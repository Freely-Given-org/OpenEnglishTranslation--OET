# SPDX-License-Identifier: MPL-2.0
"""2026-10-22: Hebrew word identities and morpheme ownership survive variants."""
from copy import deepcopy
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from hebrew_word_alignment import matched_word_groups, matched_morphemes, align_morphemes_by_verse
import convert_ClearMaculaOT_to_our_TSV as converter
import apply_Clear_Macula_OT_glosses as glossing


def mac(ref='GEN_30:11w7', identifier='01Nsp', word='אֶת', morphology='To', kind='w', **values):
    return dict(FGRef=ref,OSHBid=identifier,WordOrMorpheme=word,Morphology=morphology,
                RowType=kind,Lemma='אֵת',Role='O',Nesting='object',EnglishGloss='DOM',ContextualGloss='DOM') | values


def oshb(ref='GEN_30:11w5', identifier='01Nsp', word='אֶת', morphology='To', kind='w', **values):
    return dict(Ref=ref,OSHBid=identifier,NoCantillations=word,Morphology=morphology,
                RowType=kind,MorphemeRowList='1',WordOrMorpheme=word,
                WordGloss='',ContextualWordGloss='',MorphemeGloss='',ContextualMorphemeGloss='') | values


class HebrewAlignmentTests(unittest.TestCase):
    def test_metadata_uses_native_id_after_qere_word_number_shift(self):
        source = [mac('GEN_30:11w6b','01tXkb','תִּקְרָא','Vqw3fs','M',Lemma='קָרָא'),mac()]
        native = [oshb()]
        before = deepcopy((source,native))
        self.assertEqual(matched_word_groups(source,native), {0:[source[1]]})
        self.assertEqual((source,native),before)

    def test_metadata_requires_pointed_spelling_morphology_verse_and_ids(self):
        for changes in (dict(OSHBid='wrong'),dict(WordOrMorpheme='אוֹת'),dict(Morphology='Np'),dict(FGRef='GEN_30:12w7')):
            with self.subTest(changes=changes):
                self.assertEqual(matched_word_groups([mac(**changes)],[oshb()]),{})

    def test_complete_morpheme_group_and_w1_w10_boundary(self):
        parts = [mac('GEN_1:1w10a','01Abca','בְּ','R','m'),mac('GEN_1:1w10b','01Abcb','רֵאשִׁית','Ncfsa','M')]
        native = [oshb('GEN_1:1w1','01Abc','בְּ,רֵאשִׁית','R,Ncfsa',MorphemeRowList='1,2')]
        self.assertEqual(matched_word_groups(parts,native),{0:parts}) # ID verifies actual ownership despite numbering.
        parts[1]['FGRef'] = 'GEN_1:1w11a' # Not the end of w10.
        with self.assertLogs(level='WARNING'):
            self.assertEqual(matched_word_groups(parts,native),{})

    def test_conflicting_or_repeated_ids_abstain(self):
        parts=[mac(),mac('GEN_30:11w8')]
        self.assertEqual(matched_word_groups(parts,[oshb()]),{})
        self.assertEqual(matched_morphemes(parts,[oshb()]),{})

    def test_missing_id_fallback_requires_reciprocal_unique_same_verse_match(self):
        source=[mac(identifier='')]
        native=[oshb()]
        self.assertEqual(matched_morphemes(source,native),{0:0})
        self.assertEqual(matched_morphemes(source,[oshb('GEN_30:12w1')]),{})
        self.assertEqual(matched_morphemes(source,native+[oshb('GEN_30:11w6',identifier='OTHER')]),{})
        self.assertEqual(matched_morphemes(source+[mac('GEN_30:11w8',identifier='')],native),{})
        # A conflicting supplied ID never triggers a spelling-based fallback.
        self.assertEqual(matched_morphemes([mac(identifier='WRONG')],native),{})

    def test_ketiv_never_bypasses_spelling_check(self):
        self.assertEqual(matched_morphemes([mac(word='בָּא',morphology='Vqrmsa')],
                                         [oshb(word='בגד',morphology='Ti',kind='wK')]),{})
        self.assertEqual(align_morphemes_by_verse([mac(word='בָּא',morphology='Vqrmsa')],
                                         [oshb(word='בגד',morphology='Ti',kind='wK')]),{})

    def test_importer_sequence_handles_insertions_and_repetitions_without_offset_guess(self):
        source=[mac('GEN_1:1w1',word='אֶת'),mac('GEN_1:1w2',word='וְ',morphology='C'),mac('GEN_1:1w3',word='אֶת')]
        native=[oshb('GEN_1:1w1',word='אֶת'),oshb('GEN_1:1w2',word='הָ',morphology='Td'),
                oshb('GEN_1:1w3',word='וְ',morphology='C'),oshb('GEN_1:1w4',word='אֶת')]
        self.assertEqual(align_morphemes_by_verse(source,native),{0:0,1:2,2:3})
        self.assertEqual(align_morphemes_by_verse(source[:1],native),{})

    def test_importer_preserves_every_native_column_and_copies_ids(self):
        source=[mac()];del source[0]['OSHBid']
        state=SimpleNamespace(maculaHebrewWordsAndMorphemes=deepcopy(source),our_WLC_rows=[oshb()])
        with patch.object(converter,'state',state),patch.object(converter.BibleOrgSysGlobals,'verbosityLevel',0):
            self.assertTrue(converter.MacHeb_add_OSHB_ids())
        self.assertEqual(state.maculaHebrewWordsAndMorphemes,[source[0] | {'OSHBid':'01Nsp'}])

    def test_gloss_import_handles_first_missing_id_and_does_not_advance_out_of_bounds(self):
        source=[mac(identifier=''),mac('GEN_30:12w1',identifier='')]
        native=[oshb()]
        state=SimpleNamespace(MaculaHebrew_morpheme_rows=source,WLC_morpheme_rows=native)
        with patch.object(glossing,'state',state),patch.object(glossing.BibleOrgSysGlobals,'verbosityLevel',0),self.assertLogs(level='WARNING'):
            self.assertTrue(glossing.fill_known_MaculaHebrew_English_contextual_glosses())
        self.assertEqual(native[0]['WordGloss'],'DOM')
        self.assertEqual(native[0]['Ref'],'GEN_30:11w5')
        self.assertEqual(native[0]['OSHBid'],'01Nsp')

if __name__ == '__main__':
    unittest.main()
