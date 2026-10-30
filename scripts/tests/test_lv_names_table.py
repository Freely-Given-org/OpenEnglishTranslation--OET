#!/usr/bin/env -S uv run
# SPDX-License-Identifier: CC0-1.0
"""Shared LV spelling names include DC without accepting arbitrary draft glosses.

CHANGELOG:
    2026-10-30 Check DC name selection, table merging and parallel build ordering.
"""
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('oet_lv_names', SCRIPTS / 'create_OET-LV_TSV_name_table.py')
names = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(names)


class LVNamesTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.table = self.root / 'dc.tsv'
        self.output = self.root / 'names.tsv'
        for attribute, value in (
            ('OET_LV_DC_WORD_TABLE_FILEPATH', self.table),
            ('OET_LV_NAMES_TSV_OUTPUT_FILEPATH', self.output),
            ('OET_LV_OT_NAMES_SET', {('David', 'Dāvid')}),
            ('OET_LV_NT_NAMES_SET', {('David', 'Dawid')}),
            ('OET_LV_DC_NAMES_SET', set()),
        ):
            self.enterContext(patch.object(names, attribute, value))

    def write_table(self, rows):
        self.table.write_text('Ref\tOETGlossWords\tGlossStatus\n' + ''.join(
            f'TOB_1:1w{n}\t{gloss}\t{status}\n' for n, (gloss, status) in enumerate(rows, 1)), encoding='utf-8')

    def test_emitted_names_only_and_existing_mappings_survive(self):
        self.write_table([('Tōbit', 'name-transliteration'),
                          ('Tōbit', 'name-transliteration'),
                          ('Ptolemaiou', 'name-transliteration-candidate'),
                          ('Dawid', 'name-transliteration'),
                          ('Capitallised_typo', 'editorial'),
                          ('word', 'form-lexical'), ('', 'missing')])
        names.load_OET_LV_DC_names()
        names.create_OET_LV_name_table()
        self.assertEqual(self.output.read_text(), 'TraditionalName\tLVName\n'
            '\tPtolemaiou\n\tTōbit\nDavid\tDawid\nDavid\tDāvid\n')
        self.assertEqual(names.OET_LV_OT_NAMES_SET, {('David', 'Dāvid')})
        timestamp = self.output.stat().st_mtime_ns
        names.create_OET_LV_name_table()
        self.assertEqual(self.output.stat().st_mtime_ns, timestamp)
        self.write_table([('Tōbiaʸl', 'name-transliteration')])
        names.load_OET_LV_DC_names()
        names.create_OET_LV_name_table()
        self.assertIn('\tTōbiaʸl\n', self.output.read_text())
        self.assertNotIn('\tTōbit\n', self.output.read_text())

    def test_missing_or_invalid_dc_input_does_not_replace_names(self):
        self.output.write_text('previous names\n')
        with self.assertRaisesRegex(FileNotFoundError, 'make LV_DC'):
            names.load_OET_LV_DC_names()
        self.table.write_text('Wrong\tHeader\n')
        with self.assertRaisesRegex(ValueError, 'columns'):
            names.load_OET_LV_DC_names()
        for gloss in ('', '⟦Τωβίτ⟧', 'Tōbit¦3', 'Tōbit broken'):
            with self.subTest(gloss=gloss):
                self.write_table([(gloss, 'name-transliteration')])
                with self.assertRaisesRegex(ValueError, 'TOB_1:1w1'):
                    names.load_OET_LV_DC_names()
        self.assertEqual(self.output.read_text(), 'previous names\n')

    def test_parallel_make_waits_for_dc_and_refreshes_existing_names(self):
        scripts = self.root / 'scripts'
        scripts.mkdir()
        for relative in ('ScriptedOTUpdates/restoreNames.commandTable.tsv',
                         'ScriptedVLTUpdates/OTNames.commandTable.tsv',
                         'ScriptedVLTUpdates/NTNames.commandTable.tsv',
                         'create_OET-LV_TSV_name_table.py'):
            path = scripts / relative
            path.parent.mkdir(exist_ok=True)
            path.touch()
        (self.root / 'src').mkdir()
        driver = self.root / 'driver.py'
        driver.write_text('''from pathlib import Path
import sys
root = Path.cwd().parent
target = root / 'derivedTexts/OET-LV_names_table.tsv'
table = root / 'derivedTexts/dc.tsv'
if sys.argv[1] == 'build_OET-LV_DC.py':
    if sys.argv[2] == 'build':
        table.parent.mkdir(exist_ok=True)
        table.write_text((root / 'desired').read_text())
else:
    assert table.read_text() == (root / 'desired').read_text()
    target.write_text(table.read_text())
''')
        target = '../derivedTexts/OET-LV_names_table.tsv'
        for spelling in ('Tōbit', 'Tōbiaʸl'):
            (self.root / 'desired').write_text(spelling)
            result = subprocess.run(['make', '-f', str(SCRIPTS / 'makefile'), '-j4', target, 'LV_DC',
                f'UVrun={sys.executable} {driver}', f'DC_PYTHON={sys.executable} {driver}',
                f'BTRANSLIT_RUST_DIR={self.root}', f'SBE_RUST_DIR={self.root}'],
                cwd=scripts, capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual((scripts / target).read_text(), spelling)


if __name__ == '__main__':
    unittest.main()
