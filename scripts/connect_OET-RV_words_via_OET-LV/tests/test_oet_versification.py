"""Real BOS mapping/retrieval fixtures; no project Bible files are rewritten."""
import logging
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import bos_books_codes_py

from BibleOrgSys.Formats.USFMBible import USFMBible
from BibleOrgSys.Reference import BibleVersification as bv
from BibleOrgSys.Reference.BibleVersificationMappings import VersificationMappingEngine, get_default_mapping_engine
from test_connect_oet_words import connect
from oet_versification import audit_unmapped_lv, resolve_alignment_passages


class VersificationTests(unittest.TestCase):
    def setUp(self):
        self.folder = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.count = 0
        self.addCleanup(logging.disable, logging.root.manager.disable)
        logging.disable(logging.CRITICAL)
        self.enterContext(patch.object(connect, 'state', connect.State()))

    def bible(self, BBB, text, profile):
        self.count += 1
        folder = self.folder / str(self.count)
        folder.mkdir()
        usfm = bos_books_codes_py.bos_book_code_to_usfm_abbrev(BBB).upper()
        (folder / f'{usfm}.usfm').write_text(f'\\id {usfm}\n\\h {BBB}\n{text}\n')
        bible = USFMBible(folder, versification=profile)
        bible.load()
        return bible

    def resolve(self, BBB, rv_text, lv_text):
        rv = self.bible(BBB, rv_text, 'eng')
        lv = self.bible(BBB, lv_text, 'org')
        lines = rv_text.splitlines()
        passages, skipped = resolve_alignment_passages(BBB, rv, lv, lines)
        connect.state.rvESFMLines = lines
        connect.state.rvLineIndex = connect.index_book_lines(lines)
        connect.state.rvAlignmentLines = {p.key: p.lines for p in passages}
        connect.state.rvTokenCache = {}
        return passages, skipped

    def text(self, passage):
        return ' '.join(e.getCleanText() for e in passage.lv_entries if e.getMarker() in ('v~', 'd'))

    def test_genesis_chapter_boundary_uses_rv_coordinates(self):
        passages, skipped = self.resolve('GEN', '\\c 31\n\\v 54 Feast\n\\v 55 Farewell\n\\c 32\n\\v 1 Journey',
            '\\c 31\n\\v 54 Feast¦54\n\\c 32\n\\v 1 Farewell¦55\n\\v 2 Journey¦56')
        self.assertEqual(skipped, [])
        self.assertEqual([p.key for p in passages], [(31,54),(31,55),(32,1)])
        self.assertEqual([p.lv_references for p in passages], [
            (('GEN','31','54',None),), (('GEN','32','1',None),), (('GEN','32','2',None),)])
        self.assertEqual(self.text(passages[1]), 'Farewell¦55')
        self.assertEqual(connect.getLiveRVVerseText('GEN',31,55), 'Farewell')
        token = connect.getLiveRVTokens('GEN',31,55)[0]
        with patch.object(connect.BibleOrgSysGlobals, 'commandLineArguments', type('Options', (), {'report': False})()):
            self.assertEqual(connect.applyRVTokenLink('GEN',31,55,token,55,'test'), (1,0))
        self.assertEqual(connect.state.rvESFMLines[2], r'\v 55 Farewell¦55')
        self.assertEqual(connect.state.rvESFMLines[-1], r'\v 1 Journey')

    def test_chapters_present_only_on_one_side(self):
        for BBB, rc, rv, lc, lv in [('MAL',4,1,3,19),('JOL',2,28,3,1),('JOL',3,1,4,1),('JNA',1,17,2,1)]:
            with self.subTest(book=BBB, chapter=rc):
                passages, skipped = self.resolve(BBB, f'\\c {rc}\n\\v {rv} word', f'\\c {lc}\n\\v {lv} word¦7')
                self.assertEqual(skipped, [])
                self.assertEqual(passages[0].lv_references, ((BBB,str(lc),str(lv),None),))
                self.assertEqual(self.text(passages[0]), 'word¦7')

    def test_psalm_separate_title_and_two_verse_offset(self):
        passages, skipped = self.resolve('PSA', '\\c 3\n\\d David\n\\v 1 enemies\n\\c 51\n\\d Natan\n\\v 1 mercy',
            '\\c 3\n\\v 1 David¦1\n\\v 2 enemies¦2\n\\c 51\n\\v 1 director¦3\n\\v 2 Natan¦4\n\\v 3 mercy¦5')
        self.assertEqual(skipped, [])
        self.assertEqual([self.text(p) for p in passages], ['David¦1','enemies¦2','director¦3 Natan¦4','mercy¦5'])
        self.assertEqual(connect.getLiveRVVerseText('PSA',3,0), 'David')
        self.assertEqual(connect.getLiveRVVerseText('PSA',3,1), 'enemies')
        # The complete title spans two original verses; the body still starts
        # at org 51:3. Both title verses must be retrieved exactly once.
        self.assertEqual(passages[2].lv_references, (('PSA','51','1',None), ('PSA','51','2',None)))

    def test_all_eight_repaired_mappings_retrieve_complete_text(self):
        cases = [
            ('NUM',26,1,((25,19),(26,1))),
            ('SA1',20,42,((20,42),(21,1))),
            ('KI1',22,43,((22,43),(22,44))),
            ('CH1',12,4,((12,4),(12,5))),
            *(('PSA',c,0,((c,1),(c,2))) for c in (51,52,54,60)),
        ]
        for BBB, c, v, targets in cases:
            with self.subTest(book=BBB, chapter=c, verse=v):
                rv_text = f'\\c {c}\n' + (f'\\v {v} ' if v else '\\d ') + 'first second'
                lv_lines, previous_chapter = [], None
                for n, ((chapter, verse), word) in enumerate(zip(targets, ('first','second')), 1):
                    if chapter != previous_chapter:
                        lv_lines.append(f'\\c {chapter}')
                    lv_lines.append(f'\\v {verse} {word}¦{n}')
                    previous_chapter = chapter
                lv_text = '\n'.join(lv_lines)
                passages, skipped = self.resolve(BBB, rv_text, lv_text)
                self.assertEqual(skipped, [])
                self.assertEqual(len(passages), 1)
                self.assertEqual(self.text(passages[0]), 'first¦1 second¦2')
                expected = tuple((BBB,str(chapter),str(verse),None) for chapter,verse in targets)
                self.assertEqual(passages[0].lv_references, expected)
                inverse = get_default_mapping_engine().convert('org','eng',expected)
                self.assertEqual(inverse.status, 'exact')
                self.assertEqual(inverse.references, ((BBB,str(c),str(v),None),))

    def test_title_inside_verse_one_is_one_matching_unit(self):
        passages, skipped = self.resolve('PSA', '\\c 11\n\\d David\n\\v 1 refuge\n\\q1 bird\n\\v 2 bow',
            '\\c 11\n\\v 1 David¦1 refuge¦2 bird¦3\n\\v 2 bow¦4')
        self.assertEqual(skipped, [])
        self.assertEqual([p.key for p in passages], [(11,1),(11,2)])
        self.assertEqual(passages[0].rv_references, (('PSA','11','1',None),))
        self.assertEqual(connect.getLiveRVVerseText('PSA',11,1), 'David refuge bird')
        self.assertEqual(len(connect.getLiveRVTokens('PSA',11,1)), 3)

    def test_rv_bridge_retrieves_each_lv_verse_once(self):
        passages, skipped = self.resolve('GEN', '\\c 1\n\\v 1-3 first second third\n\\v 4 fourth',
            '\\c 1\n\\v 1 first¦1\n\\v 2 second¦2\n\\v 3 third¦3\n\\v 4 fourth¦4')
        self.assertEqual(skipped, [])
        self.assertEqual(len(passages), 2)
        self.assertEqual(self.text(passages[0]), 'first¦1 second¦2 third¦3')
        self.assertEqual(len(passages[0].lv_references), 3)
        self.assertEqual(len(connect.getLiveRVTokens('GEN',1,1)), 3)

    def test_lv_bridge_merges_its_rv_counterparts(self):
        passages, skipped = self.resolve('GEN', '\\c 1\n\\v 1 first\n\\v 2 second\n\\v 3 third',
            '\\c 1\n\\v 1-2 first¦1 second¦2\n\\v 3 third¦3')
        self.assertEqual(skipped, [])
        self.assertEqual(len(passages), 2)
        self.assertEqual(self.text(passages[0]), 'first¦1 second¦2')
        self.assertEqual(len(passages[0].rv_references), 2)
        self.assertEqual(connect.getLiveRVVerseText('GEN',1,1), 'first second')

    def test_incomplete_lv_bridge_does_not_expose_unrelated_text(self):
        passages, skipped = self.resolve('GEN', '\\c 1\n\\v 1 first', '\\c 1\n\\v 1-2 first¦1 second¦2')
        self.assertEqual(passages, [])
        self.assertEqual(skipped[0]['status'], 'incomplete_lv_storage')

    def test_missing_mapped_text_never_uses_same_number(self):
        passages, skipped = self.resolve('GEN', '\\c 32\n\\v 1 requested', '\\c 32\n\\v 1 wrong¦1')
        self.assertEqual(passages, [])
        self.assertEqual(skipped[0]['status'], 'missing_lv_text')
        self.assertEqual(skipped[0]['missing_reference'], ('GEN','32','2'))

    def custom(self, eng, counts):
        engine = VersificationMappingEngine({'maxVerses': {'GEN': counts}}, {
            'eng': eng, 'org': {'maxVerses': {'GEN': counts}, 'identityBooks': {'GEN':'GEN'}}})
        return patch.object(bv, 'get_default_mapping_engine', return_value=engine)

    def test_explicit_mapping_group_is_requested_together(self):
        with self.custom({'maxVerses': {'GEN':[2]},
                          'groupMappings': [{'source':'GEN 1:1-2', 'target':'GEN 1:1'}]}, [1]):
            passages, skipped = self.resolve('GEN', '\\c 1\n\\v 1 first\n\\v 2 second', '\\c 1\n\\v 1 first¦1 second¦2')
        self.assertEqual(skipped, [])
        self.assertEqual(len(passages), 1)
        self.assertEqual(len(passages[0].rv_references), 2)
        self.assertEqual(self.text(passages[0]), 'first¦1 second¦2')

    def test_split_mapping_retains_all_destinations(self):
        with self.custom({'maxVerses': {'GEN':[1]},
                          'groupMappings': [{'source':'GEN 1:1', 'target':'GEN 1:1-2'}]}, [2]):
            passages, skipped = self.resolve('GEN', '\\c 1\n\\v 1 first second', '\\c 1\n\\v 1 first¦1\n\\v 2 second¦2')
        self.assertEqual(skipped, [])
        self.assertEqual(self.text(passages[0]), 'first¦1 second¦2')

    def test_disjoint_reordered_mapping_does_not_include_middle_verse(self):
        with self.custom({'maxVerses': {'GEN':[2]},
                          'mappedVerses': {'GEN 1:1':'GEN 1:3', 'GEN 1:2':'GEN 1:1'}}, [3]):
            passages, skipped = self.resolve('GEN', '\\c 1\n\\v 1-2 third first',
                '\\c 1\n\\v 1 first¦1\n\\v 2 unrelated¦2\n\\v 3 third¦3')
        self.assertEqual(skipped, [])
        self.assertEqual(self.text(passages[0]), 'third¦3 first¦1')
        connect.state.rvESFMLines[1] += ' unrelated¦2'
        with self.assertRaisesRegex(ValueError, 'do not belong to its mapped'):
            connect.check_OET_RV_Verse('GEN',1,1,(),passages[0].lv_entries)

    def test_non_exact_mappings_are_reported_without_text(self):
        # An incomplete group and a quarantined unequal upstream range both
        # prevent retrieval, even if a plausible same-number verse exists.
        for definition, status in [
            ({'groupMappings': [{'source':'GEN 1:1-2', 'target':'GEN 1:1'}]}, 'partial'),
            ({'mappedVerses': {'GEN 1:1':'GEN 1:1-2'}}, 'unsupported'),
            ({'mappedVerses': {'GEN 1:1':'GEN 1:1', 'GEN 1:1-2':'GEN 1:2-3'}}, 'ambiguous'),
        ]:
            with self.subTest(status=status), self.custom({'maxVerses': {'GEN':[3]}, **definition}, [3]):
                passages, skipped = self.resolve('GEN', '\\c 1\n\\v 1 word', '\\c 1\n\\v 1 word¦1')
                self.assertEqual(passages, [])
                self.assertEqual(skipped[0]['status'], status)

    def test_unused_lv_audit_exposes_an_incomplete_exact_mapping(self):
        # Retain coverage of the audit with deliberately incomplete fixture
        # data, independent of repairs to the bundled BOS mapping profiles.
        with self.custom({'maxVerses': {'GEN':[1]}, 'mappedVerses': {'GEN 1:1':'GEN 1:2'}}, [2]):
            rv = self.bible('GEN', '\\c 1\n\\v 1 first second', 'eng')
            lv_text = '\\c 1\n\\v 1 first¦1\n\\v 2 second¦2'
            lv = self.bible('GEN', lv_text, 'org')
            passages, skipped = resolve_alignment_passages('GEN', rv, lv, ['\\c 1', '\\v 1 first second'])
            self.assertEqual(skipped, [])
            gaps = audit_unmapped_lv('GEN', rv, lv, lv_text.splitlines(), passages)
        self.assertEqual([g['lv_reference'] for g in gaps], [('GEN','1','1',None)])
        self.assertEqual(gaps[0]['mapping']['status'], 'unsupported')
        self.assertEqual(gaps[0]['mapping']['diagnostics'][0]['code'], 'NO_MAPPING')


if __name__ == '__main__':
    unittest.main()
