"""Integration regressions for the connector's ESFM editing boundaries.

These tests use the project's existing BibleOrgSys dependencies, but no Bible
files are rewritten. The alignment core has separate dependency-free tests.
"""
import importlib.util
import re
from pathlib import Path
from types import SimpleNamespace
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, Mock, patch
from BibleOrgSys.Reference.BibleVersificationMappings import get_default_mapping_engine

CONNECTOR_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CONNECTOR_DIR))
spec = importlib.util.spec_from_file_location('connect_oet', CONNECTOR_DIR / 'connect_OET-RV_words_via_OET-LV.py')
connect = importlib.util.module_from_spec(spec)
spec.loader.exec_module(connect)


class BookPassTests(unittest.TestCase):
    """Exercise the complete book lifecycle, using small temporary ESFM files."""

    def setUp(self):
        self.folder = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.rv_folder = self.folder / 'rv'
        self.lv_folder = self.folder / 'lv'
        self.output = self.folder / 'output'
        for folder in (self.rv_folder, self.lv_folder, self.output):
            folder.mkdir()
        self.enterContext(patch.object(connect, 'state', connect.State()))
        self.enterContext(patch.object(connect, 'OET_RV_ESFM_FolderPath', self.rv_folder))
        self.enterContext(patch.object(connect.BibleOrgSysGlobals, 'USFMCharacterMarkers', ('add', 'nd')))
        self.enterContext(patch.object(connect, 'vPrint'))
        self.options = SimpleNamespace(books=['RUT'], report=True, dry_run=True, output_dir=None)
        self.enterContext(patch.object(connect.BibleOrgSysGlobals, 'commandLineArguments', self.options))
        connect.state.audit = []
        connect.state.bookReports = []
        connect.state.wordTable = {'OT': [[''] for _ in range(10)]}
        connect.state.wordTableHeaderList = {'OT': ['GlossCapitalisation']}
        self.rv = self.bible()
        self.lv = self.bible()
        self.matcher = self.enterContext(patch.object(connect, 'connect_OET_RV_Verse', side_effect=self.add_one_link))

    def bible(self):
        # Verse lookup is deliberately immutable, just like parsed BOS entries.
        def mapped_passage(source, refs, **kwargs):
            mapping = get_default_mapping_engine().convert('eng', 'org', refs)
            entries = [SimpleNamespace(getMarker=lambda: 'v~',
                                       getCleanText=lambda: 'bread¦1 Beth¦2 El¦3')]
            return SimpleNamespace(mapping=mapping, portions=[SimpleNamespace(
                reference=refs[0][:3], entries=entries)])
        return SimpleNamespace(
            books={},
            getMappedPassage=Mock(side_effect=mapped_passage),
        )

    def write_book(self, book='RUT', numbered=False):
        # Each part of Beth-El receives a number, but coverage counts it once.
        text = ('\\id ' + book + '\n\\c 1\n\\v 1 '
                + ('bread¦1 Beth¦2-El¦3' if numbered else 'bread Beth-El')
                + r' \add extra¦2\add*' + '\n')
        (self.rv_folder / f'OET-RV_{book}.ESFM').write_text(text, encoding='utf-8')
        (self.lv_folder / f'OET-LV_{book}.ESFM').write_text(
            f'\\id {book}\n\\c 1\n\\v 1 bread¦1 Beth¦2 El¦3\n', encoding='utf-8')
        self.rv.books[book] = self.lv.books[book] = True
        return text

    def add_one_link(self, book, c, v, rv_entries, lv_entries):
        # Simulate a matcher which needs earlier passes' anchors. Use the real
        # writer and token cache; only the candidate-selection rule is replaced.
        for token in connect.getLiveRVTokens(book, c, v):
            if token.linkable and token.number is None:
                number = {'bread': 1, 'Beth': 2, 'El': 3}[token.text]
                result = connect.applyRVTokenLink(book, c, v, token, number, 'test')
                return result
        return (0, 0)

    def test_converges_in_all_write_modes_and_counts_each_book_once(self):
        for dry_run, output_copy, report in (
            (True, False, True), (True, True, True),
            (False, True, True), (False, False, False),
        ):
            with self.subTest(dry_run=dry_run, output_copy=output_copy, report=report):
                original = self.write_book()
                self.options.dry_run = dry_run
                self.options.output_dir = self.output if output_copy else None
                self.options.report = report
                connect.state.audit.clear()
                connect.state.bookReports.clear()
                self.matcher.reset_mock()
                self.lv.getMappedPassage.reset_mock()
                with patch.object(Path, 'write_text', autospec=True, side_effect=Path.write_text) as writer:
                    counts = connect.connect_OET_RV_book('RUT', self.lv, self.rv, self.lv_folder)
                self.assertEqual(writer.call_count, 0 if dry_run else 1)
                self.assertEqual(self.matcher.call_count, 4)
                self.lv.getMappedPassage.assert_called_once_with(
                    self.rv, (('RUT', '1', '1', None),), chapterCache={})
                self.assertEqual(counts[-3:], (2, 2, 4))  # final coverage and book passes
                self.assertEqual(counts[-5:-3], (3, 0))  # additions accumulated across passes
                self.assertEqual(len(connect.state.bookReports), 1)
                summary = connect.state.bookReports[0]
                if report:
                    self.assertEqual((summary['verses'][0]['words'], summary['verses'][0]['linked']), (2,2))
                    self.assertEqual(summary['verses'][0]['unlinked'], [])
                self.assertEqual(summary['pass_additions'], [1, 1, 1, 0])
                self.assertEqual(summary['passes'], 4)
                self.assertEqual(summary['links_added'], 3)
                self.assertEqual(summary['added'], 2)
                self.assertEqual(summary['removed_plain_add'], 1)
                self.assertEqual(len(connect.state.audit), 3 if report else 0)
                expected = original.replace('bread Beth-El', 'bread¦1 Beth¦2-El¦3').replace('extra¦2', 'extra')
                self.assertEqual('\n'.join(connect.state.rvESFMLines), expected)
                self.assertEqual((self.rv_folder / 'OET-RV_RUT.ESFM').read_text(),
                                 original if dry_run or output_copy else expected)
                if not dry_run and output_copy:
                    self.assertEqual((self.output / 'OET-RV_RUT.ESFM').read_text(), expected)

    def test_cleanup_alone_does_not_trigger_another_pass(self):
        self.write_book(numbered=True)
        connect.connect_OET_RV_book('RUT', self.lv, self.rv, self.lv_folder)
        self.assertEqual(self.matcher.call_count, 1)
        self.assertEqual(connect.state.bookReports[0]['pass_additions'], [0])
        self.assertEqual(connect.state.bookReports[0]['removed_plain_add'], 1)
        self.assertEqual(connect.state.audit, [])

    def test_unchanged_book_is_not_reprocessed_when_another_book_gains_links(self):
        self.write_book('RUT')
        self.write_book('JNA', numbered=True)
        self.options.books = ['RUT', 'JNA']
        with patch.object(connect.BibleOrgSysGlobals, 'maxProcesses', 1):
            self.assertEqual(connect.connect_OET_RV(self.rv, self.lv, self.lv_folder, 'OT'), (4, 4))
        self.assertEqual([call.args[0] for call in self.matcher.call_args_list], ['RUT'] * 4 + ['JNA'])
        self.assertEqual([row['pass_additions'] for row in connect.state.bookReports], [[1, 1, 1, 0], [0]])
        self.assertEqual([row['links_added'] for row in connect.state.bookReports], [3, 0])

    def test_dc_output_keeps_filename_alias_and_declares_its_own_table(self):
        self.write_book('GES')
        for folder, abbreviation, bible in ((self.rv_folder, 'OET-RV', self.rv),
                                             (self.lv_folder, 'OET-LV', self.lv)):
            filename = f'{abbreviation}_ES1.ESFM'
            (folder / f'{abbreviation}_GES.ESFM').rename(folder / filename)
            bible.possibleFilenameDict = {'GES': filename}
        path = self.rv_folder / 'OET-RV_ES1.ESFM'
        path.write_text(path.read_text().replace('\\c 1',
            '\\rem not WORDTABLE OET-LV_OT_word_table.tsv\n\\c 1'))
        self.options.books = ['GES']
        self.options.dry_run = False
        self.options.output_dir = self.output
        original = path.read_bytes()
        connect.connect_OET_RV_book('GES', self.lv, self.rv, self.lv_folder)
        result = (self.output / 'OET-RV_ES1.ESFM').read_text()
        self.assertIn(r'\rem WORDTABLE OET-LV_DC_word_table.tsv', result)
        self.assertIn('bread¦1 Beth¦2-El¦3', result)
        self.assertEqual(path.read_bytes(), original)
        self.assertEqual(connect.state.bookReports[0]['segment'], 'DC')
        self.assertFalse((self.output / 'OET-RV_GES.ESFM').exists())


class SegmentTests(unittest.TestCase):
    def test_extra_books_and_filename_aliases_use_dc(self):
        for book in ('DAG', 'DNG', 'ES1', 'GES', 'ES2', 'LES', 'MA3', 'MA4', 'PS2', 'TOB'):
            with self.subTest(book=book):
                self.assertEqual(connect.bookSegment(book), 'DC')
        self.assertEqual(connect.bookSegment('RUT'), 'OT')
        self.assertEqual(connect.bookSegment('MRK'), 'NT')
        with self.assertRaises(ValueError):
            connect.bookSegment('FRT')

    def test_main_keeps_three_word_tables_separate_and_sums_all_segments(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            sources = [(segment, folder) for segment in ('OT', 'DC', 'NT')]
            bibles = [MagicMock() for _ in sources]
            for (segment, _), bible in zip(sources, bibles):
                filename = f'OET-LV_{segment}_word_table.tsv'
                bible.books = {dict(OT='RUT', DC='TOB', NT='MRK')[segment]: True}
                bible.__getitem__.return_value = SimpleNamespace(ESFMWordTableFilename=filename)
                bible.ESFMWordTables = {filename: [
                    'Ref\tMorphology\tGlossStatus\tOETGlossWords', f'{segment}\tN-NSM\teditorial\tbread']}
            options = SimpleNamespace(books=None, report=None, dry_run=True, output_dir=None)
            with patch.object(connect, 'state', connect.State()), \
                 patch.object(connect, 'alignmentSources', return_value=sources), \
                 patch.object(connect, 'loadAlignmentBible', side_effect=[MagicMock(), *bibles]), \
                 patch.object(connect, 'loadOETRVNameTable'), \
                 patch.object(connect, 'loadHebGrkNameTables'), \
                 patch.object(connect, 'loadOETRVWordPhraseTable'), \
                 patch.object(connect, 'connect_OET_RV', side_effect=[(10, 3), (20, 4), (30, 5)]) as run, \
                 patch.object(connect, 'reportWordNumberPercentage') as report, \
                 patch.object(connect, 'vPrint'), \
                 patch.object(connect.BibleOrgSysGlobals, 'introduceProgram'), \
                 patch.object(connect.BibleOrgSysGlobals, 'commandLineArguments', options):
                connect.main()
                self.assertEqual([call.args[-1] for call in run.call_args_list], ['OT', 'DC', 'NT'])
                self.assertEqual({key: rows[1][0] for key, rows in connect.state.wordTable.items()},
                                 {'OT': 'OT', 'DC': 'DC', 'NT': 'NT'})
                report.assert_called_once_with('Whole Bible', 60, 12)


class MatchingOrderTests(unittest.TestCase):
    def test_all_matching_goes_through_one_selection_boundary(self):
        entries = [SimpleNamespace(getMarker=lambda: 'v~', getCleanText=lambda: 'head¦1 tail¦2')]
        for reverse in (False, True):
            with self.subTest(reverse=reverse), \
                 patch.object(connect, 'getLiveRVVerseText', return_value=('⇔' if reverse else '')+'head tail'), \
                 patch.object(connect, 'matchVerseCandidates', return_value=(2,0)) as matcher:
                counts = connect.connect_OET_RV_Verse('RUT', 1, 1, entries, entries)
                matcher.assert_called_once()
                self.assertEqual(matcher.call_args.args[4], reverse)
                self.assertEqual(counts, (2,0))


class PassSummaryTests(unittest.TestCase):
    def test_testament_summaries_in_serial_and_multiprocessing_runs(self):
        for testament, books in (('OT', ['RUT', 'JNA', 'OBA', 'HAG']),
                                 ('DC', ['TOB', 'MAN', 'PS2', 'MA4']),
                                 ('NT', ['MRK', 'PHM', 'JN2', 'JN3'])):
            for processes in (1, 4):
                for passes in ((1, 3, 2, 1), (1, 1, 1, 1)):
                    with self.subTest(testament=testament, processes=processes, passes=passes):
                        results = [(0, 0, 10, 5, count) for count in passes]
                        lv = SimpleNamespace(books=dict.fromkeys(books))
                        with patch.object(connect.BibleOrgSysGlobals, 'commandLineArguments', SimpleNamespace(books=books)), \
                             patch.object(connect.BibleOrgSysGlobals, 'maxProcesses', processes), \
                             patch.object(connect.BibleOrgSysGlobals, 'alreadyMultiprocessing', False), \
                             patch.object(connect, 'connect_OET_RV_book', side_effect=results), \
                             patch.object(connect.multiprocessing, 'Pool') as pool, \
                             patch.object(connect, 'vPrint') as printer:
                            # Simulate isolated workers: nothing writes bookReports
                            # in the parent, which must use the returned counts.
                            pool.return_value.__enter__.return_value.map.return_value = results
                            self.assertEqual(connect.connect_OET_RV(None, lv, None, testament), (40, 20))
                        summaries = [call.args[2] for call in printer.call_args_list
                                     if 'book passes:' in call.args[2]]
                        expected = [] if max(passes) == 1 else [
                            f"  {testament} book passes: "
                            + ', '.join(f'{book}={count}' for book, count in zip(books, passes) if count > 1)
                            + '; total 7 book passes.']
                        self.assertEqual(summaries, expected)
                        self.assertEqual(pool.called, processes > 1)


class EditingTests(unittest.TestCase):
    def setUp(self):
        self.old_state = connect.state
        self.old_args = connect.BibleOrgSysGlobals.commandLineArguments
        self.old_markers = connect.BibleOrgSysGlobals.USFMCharacterMarkers
        connect.state = connect.State()
        connect.BibleOrgSysGlobals.commandLineArguments = SimpleNamespace(report=True)
        connect.BibleOrgSysGlobals.USFMCharacterMarkers = ('nd','wj','add','it')
        connect.state.wordTable = {'NT': [['',''] for _ in range(100)], 'OT': [['',''] for _ in range(100)]}
        connect.state.wordTableHeaderList = {'NT':['GlossCaps','Role'], 'OT':['GlossCapitalisation','Morphology']}
        connect.state.audit=[]

    def tearDown(self):
        connect.state = self.old_state
        connect.BibleOrgSysGlobals.commandLineArguments = self.old_args
        connect.BibleOrgSysGlobals.USFMCharacterMarkers = self.old_markers

    def book(self, *lines):
        connect.state.rvESFMLines=list(lines)
        connect.state.rvLineIndex=connect.index_book_lines(lines)
        connect.state.rvTokenCache={}

    def test_dc_matching_uses_its_own_table_without_ot_or_nt_metadata(self):
        connect.state.wordTableHeaderList = {'DC': ['Ref', 'Morphology', 'GlossStatus', 'OETGlossWords']}
        connect.state.wordTable = {'DC': [[], ['TOB_1:1w1', 'N-ASM', 'form-lexical', 'bread']]}
        self.book(r'\c 1', r'\v 1 bread')
        self.assertEqual(connect.matchVerseCandidates('TOB', 1, 1, ['bread¦1'], False), (1,0))
        self.assertEqual(connect.state.rvESFMLines[1], r'\v 1 bread¦1')
        self.assertEqual(connect.matchVerseCandidates('TOB', 1, 1, ['bread¦1'], False), (0,0))
        self.assertFalse(connect.lvWordIsProperNoun(connect.state.wordTable['DC'][1], 'DC'))
        for morphology, expected in [('N-NSM | N-ASM', True), ('N-NSM | V-PAM-2S', False), ('', False)]:
            with self.subTest(morphology=morphology):
                self.assertEqual(connect.lvWordIsNoun(['TOB_1:1w1', morphology, 'editorial', 'bread'], 'DC'), expected)

    def test_unresolved_dc_gloss_cannot_link_or_use_another_books_row(self):
        connect.state.wordTableHeaderList = {'DC': ['Ref', 'Morphology', 'GlossStatus', 'OETGlossWords']}
        connect.state.wordTable = {'DC': [[], ['TOB_1:1w1', '', 'ambiguous', '']]}
        self.book(r'\c 1', r'\v 1 bread')
        self.assertEqual(connect.matchVerseCandidates('TOB', 1, 1, ['bread¦1'], False), (0,0))
        connect.state.wordTable['DC'][1] = ['JDT_1:1w1', 'N-NSM', 'editorial', 'bread']
        with self.assertRaisesRegex(ValueError, 'does not belong to TOB'):
            connect.matchVerseCandidates('TOB', 1, 1, ['bread¦1'], False)

    def test_spelling_only_rejects_repeats_across_lines(self):
        self.book(r'\c 1', r'\v 1 the son', r'\q1 the father')
        token=connect.getLiveRVTokens('MRK',1,1)[2]
        self.assertEqual(connect.applyRVTokenLink('MRK',1,1,token,4,'test'), (1,0))
        self.assertEqual(connect.state.rvESFMLines[-1], r'\q1 the¦4 father')

    def test_headings_notes_and_adjacent_verses_are_untouched(self):
        self.book(r'\c 1', r'\s1 her', r'\v 1 she \f + \ft her\f*', r'\v 2 her')
        self.assertNotIn('her', [t.text for t in connect.getLiveRVTokens('MRK',1,1) if t.linkable])
        self.assertEqual(connect.state.audit, [])

    def test_no_partial_contraction_or_existing_link_changes(self):
        self.book(r'\c 1', r"\v 1 he's her¦2")
        tokens = connect.getLiveRVTokens('MRK',1,1)
        self.assertEqual([t.text for t in tokens], ["he's", 'her'])
        self.assertEqual(connect.applyRVTokenLink('MRK',1,1,tokens[1],3,'test'), (0,0))

    def test_plain_uncertain_add_is_not_linkable_or_counted(self):
        self.book(r'\c 1', r'\v 1 she \add ?her¦2\add*')
        self.assertNotIn('her', [t.text for t in connect.getLiveRVTokens('MRK',1,1) if t.linkable])
        self.assertEqual(connect.countWordsAndWordNumbers(connect.state.rvESFMLines), (1,0))
        self.assertEqual(connect.removeWordNumbersInUnlinkedAddSpans('test',connect.state.rvESFMLines),1)
        self.assertEqual(connect.state.rvESFMLines[1],r'\v 1 she \add ?her\add*')

    def test_unlinked_additions_are_cleaned_excluded_and_cannot_be_relinked(self):
        for marker in ('add', '+add'):
            for code in ('', '?', '<', '>', '?<', '?>'):
                with self.subTest(marker=marker, code=code):
                    line = (r'\v 1 she¦1 ' + f'\\{marker} {code}person¦99 '
                            + r'\+it nearby¦2\+it*' + f'\\{marker}*' + ' went¦3')
                    self.book(r'\c 1', line)
                    self.assertEqual(connect.countWordsAndWordNumbers(connect.state.rvESFMLines), (2, 2))
                    self.assertEqual(connect.removeWordNumbersInUnlinkedAddSpans('test', connect.state.rvESFMLines), 2)
                    expected = line.replace('person¦99', 'person').replace('nearby¦2', 'nearby')
                    self.assertEqual(connect.state.rvESFMLines[1], expected)
                    tokens = connect.getLiveRVTokens('MRK',1,1)
                    for token in tokens[1:3]:
                        self.assertFalse(token.linkable)
                        self.assertEqual(connect.applyRVTokenLink('MRK',1,1,token,1,'test'), (0,0))
                    self.assertEqual(connect.removeWordNumbersInUnlinkedAddSpans('test', connect.state.rvESFMLines), 0)
                    self.assertEqual(connect.state.audit, [])

    def test_excluded_outer_addition_cannot_be_overridden_by_nested_code(self):
        line = r'\v 1 she¦1 \add <the \+add @woman¦2\+add*\add* went¦3'
        self.book(r'\c 1', line)
        self.assertEqual(connect.countWordsAndWordNumbers(connect.state.rvESFMLines), (2,2))
        self.assertFalse(connect.getLiveRVTokens('MRK',1,1)[2].linkable)
        self.assertEqual(connect.removeWordNumbersInUnlinkedAddSpans('test',connect.state.rvESFMLines),1)
        self.assertEqual(connect.state.rvESFMLines[1],line.replace('woman¦2','woman'))

    def test_cleanup_preserves_other_specialist_codes(self):
        for marker in ('add', '+add'):
            for code in ('@', '*', '%', '&', '≈', '#', '≡', '!', '+', '=', '^'):
                for uncertain in ('', '?'):
                    with self.subTest(marker=marker, code=code, uncertain=uncertain):
                        line = f'\\v 1 \\{marker} {uncertain}{code}word¦2\\{marker}*'
                        self.book(r'\c 1', line)
                        self.assertEqual(connect.removeWordNumbersInUnlinkedAddSpans('test',connect.state.rvESFMLines),0)
                        self.assertEqual(connect.state.rvESFMLines[1],line)

    def test_range_check_uses_live_text_after_addition_cleanup(self):
        self.book(r'\c 1', r'\v 1 she¦1 \add >person¦99\add* went¦2')
        def entry(text):
            return SimpleNamespace(getMarker=lambda:'v~', getCleanText=lambda:text)
        rv_entries = [entry('she¦1 >person¦99 went¦2')]
        lv_entries = [entry('she¦1 went¦2')]
        connect.removeWordNumbersInUnlinkedAddSpans('test',connect.state.rvESFMLines)
        connect.check_OET_RV_Verse('RUT',1,1,rv_entries,lv_entries)
        self.book(r'\c 1', r'\v 1 she¦1 went¦99')
        with self.assertRaisesRegex(ValueError, 'do not belong to its mapped'):
            connect.check_OET_RV_Verse('RUT',1,1,rv_entries,lv_entries)

    def test_nested_nomina_sacra_and_idempotent_insertion(self):
        self.book(r'\c 1', r'\v 1 \wj God\wj*')
        connect.state.wordTable['NT'][1]=['N']
        self.assertEqual(connect.applyRVTokenLink('MRK',1,1,connect.getLiveRVTokens('MRK',1,1)[0],1,'test'), (1,1))
        self.assertEqual(connect.state.rvESFMLines[1],r'\v 1 \wj \+nd God¦1\+nd*\wj*')
        self.assertEqual(connect.applyRVTokenLink('MRK',1,1,connect.getLiveRVTokens('MRK',1,1)[0],1,'test'), (0,0))

    def test_possessive_number_follows_apostrophe_before_closing_quote(self):
        self.book(r'\c 1', "\\v 1 ‘houses'’, foundations.")
        self.assertEqual(connect.matchVerseCandidates('RUT',1,1,['houses¦1','foundations¦2'],False), (2,0))
        self.assertEqual(connect.state.rvESFMLines[1], "\\v 1 ‘houses'¦1’, foundations¦2.")
        self.assertEqual(connect.matchVerseCandidates('RUT',1,1,['houses¦1','foundations¦2'],False), (0,0))

    def test_correct_possessive_number_is_read_and_preserved(self):
        self.book(r'\c 1', "\\v 1 waters'¦1 surfaces¦2.")
        self.assertEqual([(t.text,t.number) for t in connect.getLiveRVTokens('RUT',1,1)],
                         [("waters'",1),('surfaces',2)])
        self.assertEqual(connect.matchVerseCandidates('RUT',1,1,['waters¦1','surfaces¦2'],False), (0,0))
        self.assertEqual(connect.state.rvESFMLines[1], "\\v 1 waters'¦1 surfaces¦2.")

    def test_insertion_rejects_stale_end_before_apostrophe(self):
        self.book(r'\c 1', "\\v 1 houses' foundations")
        truncated = connect.tokenize('houses', 1, 5)[0]
        self.assertEqual(connect.applyRVTokenLink('RUT',1,1,truncated,1,'test'), (0,0))
        self.assertEqual(connect.state.rvESFMLines[1], "\\v 1 houses' foundations")

    def test_insertion_rejects_apostrophe_hidden_by_formatting(self):
        for tail in (r"\add 's death\add*", r"\bd*'s sons", r"\+nd*'s children",
                     r"\add s\add*", r"\bd*s"):
            with self.subTest(tail=tail):
                line = r'\v 1 mother' + tail
                self.book(r'\c 1', line)
                truncated = connect.tokenize('mother', 1, 5)[0]
                self.assertEqual(connect.applyRVTokenLink('RUT',1,1,truncated,1,'test'), (0,0))
                self.assertEqual(connect.state.rvESFMLines[1], line)

    def test_whole_possessive_before_supplied_noun_stays_linked(self):
        self.book(r'\c 1', r"\v 1 mother's \add death\add*.")
        self.assertEqual(connect.matchVerseCandidates('RUT',1,1,['mother¦1'],False), (1,0))
        expected = r"\v 1 mother's¦1 \add death\add*."
        self.assertEqual(connect.state.rvESFMLines[1], expected)
        self.assertEqual(connect.removeWordNumbersInUnlinkedAddSpans('test',connect.state.rvESFMLines),0)
        self.assertEqual(connect.matchVerseCandidates('RUT',1,1,['mother¦1'],False), (0,0))
        self.assertEqual(connect.state.rvESFMLines[1], expected)

    def test_whole_possessive_keeps_style_and_closing_quote_outside_number(self):
        self.book(r'\c 1', r"\v 1 ‘\bd mother's\bd*’")
        self.assertEqual(connect.matchVerseCandidates('RUT',1,1,['mother¦1'],False), (1,0))
        self.assertEqual(connect.state.rvESFMLines[1], r"\v 1 ‘\bd mother's¦1\bd*’")

    def test_semantic_add_can_link_without_illegal_nested_nd(self):
        self.book(r'\c 1', r'\v 1 \add @God\add*')
        connect.state.wordTable['NT'][1]=['N']
        token=connect.getLiveRVTokens('MRK',1,1)[0]
        self.assertEqual(connect.applyRVTokenLink('MRK',1,1,token,1,'test'), (1,0))
        self.assertEqual(connect.state.rvESFMLines[1],r'\v 1 \add @God¦1\add*')

    def test_optional_plural_number_follows_complete_word(self):
        self.book(r'\c 1', r'\v 1 daughter(s).')
        self.assertEqual(connect.matchVerseCandidates('RUT',1,1,['daughter¦1'],False), (1,0))
        self.assertEqual(connect.state.rvESFMLines[1],r'\v 1 daughter(s)¦1.')
        self.assertEqual([(t.text,t.number) for t in connect.getLiveRVTokens('RUT',1,1)],
                         [('daughter(s)',1)])
        self.assertEqual(connect.matchVerseCandidates('RUT',1,1,['daughter¦1'],False), (0,0))

    def test_stale_token_cannot_insert_before_plural_ending(self):
        for ending in ('s', '(s)'):
            with self.subTest(ending=ending):
                line = r'\v 1 daughter' + ending + '.'
                self.book(r'\c 1', line)
                truncated = connect.tokenize('daughter', 1, 5)[0]
                self.assertEqual(connect.applyRVTokenLink('RUT',1,1,truncated,1,'test'), (0,0))
                self.assertEqual(connect.state.rvESFMLines[1],line)

    def test_formatted_contraction_and_plural_are_kept_as_whole_words(self):
        self.book(r'\c 1', r"\v 1 \add ≈Didn't¦1\add* the \add #ages¦2\add* end?")
        self.assertEqual([(t.text,t.number,t.code) for t in connect.getLiveRVTokens('RUT',1,1)][:3],
                         [("Didn't",1,'≈'),('the',None,None),('ages',2,'#')])
        self.assertEqual(connect.removeWordNumbersInUnlinkedAddSpans('test',connect.state.rvESFMLines),0)
        self.book(r'\c 1', r"\v 1 Did\add n't\add* I reveal myself?")
        truncated = connect.tokenize('Did', 1, 5)[0]
        self.assertEqual(connect.applyRVTokenLink('RUT',1,1,truncated,1,'test'), (0,0))

    def test_phrase_keeps_compatible_links_and_excludes_plain_add(self):
        self.book(r'\c 1', r'\v 1 you¦2 all and \add you all\add*')
        self.assertEqual(connect.matchVerseCandidates('MRK',1,1,['you¦2','all¦2'],False), (1,0))
        self.assertEqual(connect.state.rvESFMLines[1],r'\v 1 you¦2 all¦2 and \add you all\add*')
        self.assertEqual(connect.matchVerseCandidates('MRK',1,1,['you¦2','all¦2'],False), (0,0))

    def test_loyal_commitment_completes_the_source_link_once(self):
        self.book(r'\c 51', r'\v 1 because of¦2 your¦2 loyal¦2 commitment.')
        lv = ['according¦2','to¦2','of¦2','your¦2','covenant¦2','loyalty¦2']
        self.assertEqual(connect.matchVerseCandidates('PSA',51,1,lv,False), (1,0))
        self.assertEqual(connect.state.rvESFMLines[1],
                         r'\v 1 because of¦2 your¦2 loyal¦2 commitment¦2.')
        self.assertEqual(connect.matchVerseCandidates('PSA',51,1,lv,False), (0,0))

    def test_compound_name_can_be_numbered_as_a_whole(self):
        self.book(r'\c 1', r'\v 1 Tiglat-Pileser')
        token = connect.tokenize('Tiglat-Pileser', 1, 5, split_names=False)[0]
        self.assertEqual(connect.applyRVTokenLink('MRK',1,1,token,2,'test'), (1,0))
        self.assertEqual(connect.state.rvESFMLines[1],r'\v 1 Tiglat-Pileser¦2')

    def test_name_evidence_includes_hebrew_leading_modifiers_and_gentilics(self):
        self.book(r'\c 1', r'\v 1 Aharon Levites')
        connect.state.wordTableHeaderList['OT'] = ['GlossCapitalisation', 'Morphology']
        connect.state.wordTable['OT'][1] = ['', 'Np']
        connect.state.wordTable['OT'][2] = ['', 'Rd,Ngmpa']
        connect.state.nameTables = {}
        with patch.object(connect, 'getLVNameSpellings', side_effect=lambda word, keys:
                          {'aharon'} if word == 'ʼAhₐron' else {'levites'}):
            self.assertEqual(connect.matchVerseCandidates('RUT',1,1,
                ['ʼAhₐron¦1','Lēviyyiy¦2'], False), (2,0))
        self.assertEqual(connect.state.rvESFMLines[1], r'\v 1 Aharon¦1 Levites¦2')
        self.assertFalse(connect.lvWordIsProperNoun(['', 'Ngmpa'], 'OT'))

    def test_optional_phrase_table_uses_the_shared_selector(self):
        self.book(r'\c 1', r'\v 1 young donkey')
        connect.state.rvWordPhrases = {('colt',): ('young','donkey')}
        self.assertEqual(connect.matchVerseCandidates('MRK',1,1,['colt¦1'],False), (2,0))
        self.assertEqual(connect.state.rvESFMLines[1], r'\v 1 young¦1 donkey¦1')

    def test_psalm_title_separate_from_first_printed_verse(self):
        self.book(r'\c 3', r'\d title', r'\v 1 body', r'\c 4', r'\d next title', r'\v 1 next body')
        self.assertEqual(connect.getLiveRVVerseText('PSA',3,0),'title')
        self.assertEqual(connect.getLiveRVVerseText('PSA',3,1),'body')
        self.assertEqual(connect.getLiveRVVerseText('PSA',4,0),'next title')

    def test_mark_15_40_maria_is_blocked_by_the_incorrect_from_anchor(self):
        rv = (r'\add ≈Further¦36581 back¦36581\add*, there was¦36575 also¦36578 '
              r'\add a group of\add* women¦36579 observing¦36582 \add <everything\add*. '
              r'\add They\add* \add ≈included¦36583\add* Maria from¦36580 Magdala¦36589, '
              r'Maria¦36591 the¦36592 mother¦36600 of¦36594 \add ≈young¦36596\add* '
              r'Yacob¦36594 and¦36597 Yoses¦36599, and¦36601 Salome¦36602,')
        lv = ('And¦36576 were¦36575 also¦36578 women¦36579 observing¦36582 from¦36580 afar¦36581, '
              'among¦36583 whom¦36584 both¦36586 Maria/(Miryām)¦36587 the¦36588 from¦36589_Magdala¦36589, '
              'and¦36590 Maria¦36591 the¦36592 mother¦36600 of¦36594_Yakōbos/(Yaˊₐqoⱱ)¦36594 '
              'the¦36595 little¦36596 and¦36597 of¦36599_Yōsaʸs/(Yōşēf?)¦36599, and¦36601 Salōmaʸ¦36602,')
        connect.state.wordTableHeaderList['NT'] = ['GlossCaps', 'Role']
        connect.state.wordTable['NT'] = {n: ['', 'N'] for n in range(36575,36603)}
        lv_words = re.findall(r'[^\s_¦]+¦[0-9]+', lv)
        self.book(r'\c 15', r'\v 40 ' + rv)
        self.assertEqual(connect.matchVerseCandidates('MRK', 15, 40, lv_words, False, lv), (0,0))
        # The existing matcher succeeds after removing the wrong anchor; no
        # verse-specific matching rule or relaxation for repeated names is needed.
        corrected = rv.replace('from¦36580', 'from')
        self.book(r'\c 15', r'\v 40 ' + corrected)
        self.assertEqual(connect.matchVerseCandidates('MRK', 15, 40, lv_words, False, lv), (2,0))
        self.assertEqual(connect.state.rvESFMLines[1], r'\v 40 ' + corrected.replace(
            'Maria from ', 'Maria¦36587 from¦36589 '))

    def test_mark_14_72_links_both_rooster_phrases_without_changing_anchors(self):
        # Preserve the two differently ordered clauses, repeated words, and the
        # existing source numbers which originally blocked the first occurrence.
        rv = (r"Right then¦35843 the rooster crowed for¦35845 the second¦35846 time¦35846 "
              r"and Peter¦35853 remembered¦35850 \add now\add* what Yeshua had¦35879 "
              r"told¦35861 him¦35862—\add how\add* \add %he\add* would¦35876 "
              r"renounce¦35876 \add @Yeshua\add* three¦35874 times¦35874 before¦35867 "
              r"the rooster crowed—and he broke¦35879 down¦35879 \add and\add* cried¦35880.")
        lv = (r"And¦35843 immediately¦35844 for¦35845 the¦35846 second¦35846 time¦35846 "
              r"a¦35847 rooster¦35847 crowed¦35848. And¦35849 the¦35852 Petros¦35853 "
              r"was¦35850_reminded¦35850 the¦35854 message¦35856 as¦35858 Yeshua¦35864 "
              r"said¦35861 to¦35862_him¦35862, that¦35866 Before¦35867 the¦35868 "
              r"rooster¦35868 to¦35870_crow¦35870 three-times¦35874 you¦35876_will¦35876_"
              r"be¦35876_renouncing¦35876 me¦35875, and¦35877 having¦35879_broken¦35879_"
              r"down¦35879, he¦35880_was¦35880_weeping¦35880.")
        self.book(r'\c 14', r'\v 72 ' + rv)
        connect.state.wordTableHeaderList['NT'] = ['GlossCaps', 'Role']
        connect.state.wordTable['NT'] = {n: ['', ''] for n in range(35843, 35881)}
        lv_words = [f'{t.text}¦{t.number}' for t in connect.tokenize(lv)
                    if t.number is not None]
        before = connect.getLiveRVTokens('MRK',14,72)
        connect.matchVerseCandidates('MRK', 14, 72, lv_words, False, lv)
        after = connect.getLiveRVTokens('MRK',14,72)
        self.assertEqual([(t.text,t.number) for t in after if t.text in ('rooster','crowed')],
                         [('rooster',35847), ('crowed',35848),
                          ('rooster',35868), ('crowed',35870)])
        # The first 'the' must not borrow the already consumed 'the' belonging
        # to 'the second time' merely because the new phrase crosses it.
        self.assertIsNone(after[2].number)
        self.assertEqual([t.text for t in before], [t.text for t in after])
        for old, new in zip(before, after):
            if old.number is not None:
                self.assertEqual(new.number, old.number)
        self.assertEqual(connect.matchVerseCandidates('MRK', 14, 72, lv_words, False, lv), (0,0))
        # Starting with only the four rooster/crow links (as after a manual
        # edit) must not let two separate gaps both claim LV 'the¦35846'.
        occurrences = iter((35847,35848,35868,35870))
        manually_linked = re.sub(r'\b(?:rooster|crowed)\b',
                                 lambda m: f'{m[0]}¦{next(occurrences)}', rv)
        self.book(r'\c 14', r'\v 72 ' + manually_linked)
        connect.matchVerseCandidates('MRK', 14, 72, lv_words, False, lv)
        self.assertIsNone(connect.getLiveRVTokens('MRK',14,72)[2].number)

    def test_original_lv_punctuation_reaches_the_movement_matcher(self):
        self.book(r'\c 1', r'\v 1 start¦1 bright lamps after¦2 dinner¦3 end¦6')
        connect.matchVerseCandidates('MRK', 1, 1, ['start¦1','after¦2','dinner¦3','bright¦4','lamps¦5','end¦6'], False, 'start¦1 after¦2 dinner¦3. bright¦4 lamps¦5 end¦6')
        self.assertTrue(all(link['reason'] == 'unique lexical candidate' for link in connect.state.audit))


if __name__ == '__main__':
    unittest.main()
