# SPDX-License-Identifier: MPL-2.0
"""2026-10-22: native identities survive mapped, conservative word joins."""
from copy import deepcopy
from itertools import product
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from greek_word_alignment import certain_matches, mapped_word_matches, words_match
from theographic import normalise_book_codes
import add_tags_to_NT_word_table as tagging
import convert_ClearMaculaNT_to_TSV as converter
import analyze_noun_pairs_v2 as nouns


def mac(ref, word, lemma=None, referents=''):
    return dict(FGRef=ref, Word=word, Lemma=word if lemma is None else lemma, Referents=referents)


def target(ref, word, lemma=None):
    return dict(Ref=ref, Word=word, Lemma=word if lemma is None else lemma, BibTagId='ID-'+ref)


def row(ref, word, probability='1', tags=''):
    return '\t'.join((ref, word, word, word, 'gloss', 'gloss', '', probability, 'G1', 'N', 'morphology', tags))


class BookCodesTests(unittest.TestCase):
    def test_bos_keys_preserved_usfm_keys_converted_without_touching_values(self):
        source = {'__HEADERS__':[], 'EZE_1:1':{'FGid':'EZK_1:1'}, 'EZK_1:2':{},
                  'SA1_1:1':{}, 'SA1_1:2':{}, 'ISA_1:1':{}}
        before = deepcopy(source)
        result = normalise_book_codes(source)
        self.assertEqual(set(result), {'__HEADERS__','EZE_1:1','EZE_1:2','SA1_1:1','SA1_1:2','ISA_1:1'})
        self.assertIs(result['EZE_1:1'], source['EZE_1:1'])
        self.assertEqual(source, before)

    def test_collisions_unknown_codes_and_malformed_keys_raise(self):
        for source in ({'EZE_1:1':{}, 'EZK_1:1':{}}, {'ZZZ_1:1':{}}, {'1SA_1:1':{}}, {'EZE1:1':{}}):
            with self.subTest(source=source), self.assertRaises(ValueError):
                normalise_book_codes(source)


class GreekAlignmentTests(unittest.TestCase):
    def test_whole_words_and_unicode(self):
        self.assertFalse(words_match('ὁ','δέ'))
        self.assertFalse(words_match('καί','κατά'))
        self.assertFalse(words_match('ὁ','ο')) # Breathing remains significant.
        self.assertTrue(words_match('Λόγος','λόγος'))
        self.assertTrue(words_match('καὶ','καί'))
        self.assertTrue(words_match('ὑπ’', 'ὑπʼ'))

    def test_certain_matches_agrees_with_exhaustive_small_alignments(self):
        def all_alignments(matrix, i=0, j=0):
            if i == len(matrix) or j == len(matrix[0]):
                return [(0, frozenset())]
            options = all_alignments(matrix, i+1, j) + all_alignments(matrix, i, j+1)
            if matrix[i][j]:
                options += [(score+matrix[i][j], pairs | {(i,j)})
                            for score,pairs in all_alignments(matrix, i+1, j+1)]
            return options
        for values in product((None, 90, 100), repeat=6):
            matrix = [values[:3], values[3:]]
            alignments = all_alignments(matrix)
            best = max(score for score, _ in alignments)
            agreed = frozenset.intersection(*(pairs for score,pairs in alignments if score == best))
            self.assertEqual(certain_matches(matrix),dict(agreed))

    def test_shifted_sequence_not_native_word_distance(self):
        source = [mac('MAT_3:2w1','λόγος'), mac('MAT_3:2w2','γὰρ','γάρ')]
        dest = [target('MAT_3:2w1','δέ'), target('MAT_3:2w2','λόγος'), target('MAT_3:2w3','γὰρ','γάρ')]
        before = deepcopy((source,dest))
        self.assertEqual(mapped_word_matches(source,dest,'org','eng'), {0:1,1:2})
        self.assertEqual((source,dest),before)

    def test_ambiguous_repetition_stays_unlinked(self):
        source = [mac('MAT_1:1w1','καί')]
        dest = [target('MAT_1:1w1','καί'), target('MAT_1:1w2','καί')]
        self.assertEqual(mapped_word_matches(source,dest,'org','eng'),{})

    def test_weak_spelling_requires_lemma_and_conflicting_lemma_rejected(self):
        source = [mac('MAT_1:1w1','καὶ', '')]
        dest = [target('MAT_1:1w1','καί', '')]
        self.assertEqual(mapped_word_matches(source,dest,'org','eng'),{})
        source[0]['Lemma'] = dest[0]['Lemma'] = 'καί'
        self.assertEqual(mapped_word_matches(source,dest,'org','eng'),{0:0})
        dest[0]['Lemma'] = 'δέ'
        self.assertEqual(mapped_word_matches(source,dest,'org','eng'),{})

    def test_combined_acts_passage_in_both_directions(self):
        source = [mac('ACT_19:40w1','λόγος'),mac('ACT_19:40w2','ἐκκλησίαν')]
        dest = [target('ACT_19:40w1','λόγος'),target('ACT_19:41w1','ἐκκλησίαν')]
        self.assertEqual(mapped_word_matches(source,dest,'org','eng'),{0:0,1:1})
        self.assertEqual(mapped_word_matches(dest,source,'eng','org', 'Ref','FGRef'),{0:0,1:1})

    def test_philippians_mapping_finds_correct_passages(self):
        source = [mac('PHP_1:16w1','ἀγάπης'),mac('PHP_1:17w1','ἐριθείας')]
        dest = [target('PHP_1:16w1','ἐριθείας'),target('PHP_1:17w1','ἀγάπης')]
        self.assertEqual(mapped_word_matches(source,dest,'org','VLT'),{0:1,1:0})

    def test_missing_target_is_reported_not_replaced_by_nearby_verse(self):
        source = [mac('PHP_1:16w1','ἀγάπης')]
        dest = [target('PHP_1:16w1','ἀγάπης')]
        with self.assertLogs(level='WARNING'):
            self.assertEqual(mapped_word_matches(source,dest,'org','VLT'),{})

    def test_unsupported_and_duplicate_references_are_errors(self):
        source, dest = [mac('MAT_1:1w1','λόγος')], [target('MAT_1:1w1','λόγος')]
        with self.assertRaisesRegex(ValueError, 'Original.*eng.*unsupported'):
            mapped_word_matches(source,dest,'Original','eng')
        with self.assertRaisesRegex(ValueError, 'duplicate word reference'):
            mapped_word_matches(source*2,dest,'org','eng')

    def test_converter_copies_native_ids_only_and_preserves_source_fields(self):
        source = [mac('ACT_19:40w1','λόγος'),mac('ACT_19:40w2','ἐκκλησίαν')]
        dest = [target('ACT_19:40w1','λόγος'),target('ACT_19:41w1','ἐκκλησίαν')]
        source += [mac('CO2_13:12w1','ἀσπάσασθε'),mac('CO2_13:13w1','χάρις')]
        dest += [target('CO2_13:12w1','ἀσπάσασθε'),target('CO2_13:13w1','χάρις')]
        state = SimpleNamespace(lowFatWordsAndMorphemes=deepcopy(source), BibTags_rows=dest)
        with patch.object(converter,'state',state), patch.object(converter.BibleOrgSysGlobals,'verbosityLevel',0):
            self.assertTrue(converter.add_BibleTags_ids())
        for before,after,expected in zip(source,state.lowFatWordsAndMorphemes,dest):
            self.assertEqual({k:v for k,v in after.items() if k != 'BibTagId'},before)
            self.assertEqual(after['BibTagId'],expected['BibTagId'])


class ReferentTests(unittest.TestCase):
    def state(self, source, rows):
        header = list(source[0])
        return SimpleNamespace(macula_tsv_lines=[header,*[[r[k] for k in header] for r in source]],
            newTable=['Ref\tGreekWord\tSRLemma\tGreekLemma\tVLTGlossWords\tOETGlossWords\tGlossCaps\tProbability\tStrongsExt\tRole\tMorphology\tTags',*rows])

    def apply(self, state):
        with patch.object(tagging,'state',state), patch.object(tagging.BibleOrgSysGlobals,'verbosityLevel',0):
            self.assertTrue(tagging.tag_referents_from_macula_data())

    def test_mapped_edges_use_original_rows_skip_variants_include_final_row_and_deduplicate(self):
        source = [mac('PHP_1:16w1','ἀγάπης',referents='1:17w1;1:17w1'),mac('PHP_1:17w1','ἐριθείας')]
        rows = [row('PHP_1:16w1','ἐριθείας',tags='PPaul'), row('PHP_1:17w1','ἀγάπης',probability=''),
                row('PHP_1:17w2','ἀγάπης')]
        state = self.state(source, rows)
        self.apply(state)
        self.assertEqual(state.newTable[1].split('\t')[-1], 'PPaul;F3')
        self.assertEqual(state.newTable[2].split('\t')[-1], '')
        self.assertEqual(state.newTable[3].split('\t')[-1], 'R1;PPaul')
        for before,after in zip(rows,state.newTable[1:]):
            self.assertEqual(before.split('\t')[:-1],after.split('\t')[:-1])
        once = list(state.newTable)
        self.apply(state)
        self.assertEqual(state.newTable,once)

    def test_missing_native_endpoint_raises_before_mutating_table(self):
        state = self.state([mac('MAT_1:1w1','λόγος',referents='1:1w2')],[row('MAT_1:1w1','λόγος')])
        before = deepcopy(state.newTable)
        with self.assertRaisesRegex(ValueError,'MAT_1:1w1.*missing target MAT_1:1w2'):
            self.apply(state)
        self.assertEqual(state.newTable,before)

    def test_ambiguous_endpoint_leaves_both_sides_unlinked(self):
        state = self.state([mac('MAT_1:1w1','λόγος',referents='1:1w2'),mac('MAT_1:1w2','καί')],
                           [row('MAT_1:1w1','λόγος'),row('MAT_1:1w2','καί'),row('MAT_1:1w3','καί')])
        before = list(state.newTable)
        self.apply(state)
        self.assertEqual(state.newTable,before)


class NounReaderTests(unittest.TestCase):
    def test_word_one_in_different_verses_is_not_overwritten(self):
        with TemporaryDirectory() as folder:
            path = Path(folder)/'words.tsv'
            for parse,gloss in ((nouns.parse_nt_word_table,'OETGlossWords'),(nouns.parse_ot_word_table,'ContextualWordGloss')):
                path.write_text(f'Ref\t{gloss}\tRole\tMorphology\nMAT_1:1w1\tman\tN\tNMS\nMAT_1:2w1\tmen\tN\tNMP\n')
                self.assertEqual(set(parse(path)),{'MAT_1:1w1','MAT_1:2w1'})

if __name__ == '__main__':
    unittest.main()
