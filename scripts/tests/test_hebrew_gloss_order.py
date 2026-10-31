# SPDX-License-Identifier: MPL-2.0
"""Phrase reordering, word-table aggregation and actual ESFM rendering."""
from copy import deepcopy
from csv import DictReader
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

import apply_Clear_Macula_OT_glosses as apply
import extract_glossed_OSHB_OT_to_ESFM as export
from hebrew_gloss_order import reorder_subject_phrases

HEADERS = ('Ref OSHBid RowType Strongs CantillationHierarchy Morphology WordOrMorpheme '
           'NoCantillations MorphemeGloss ContextualMorphemeGloss WordGloss '
           'ContextualWordGloss GlossCapitalisation GlossPunctuation GlossOrder GlossInsert').split()
V = 'V-S-O/Vp2V/V2VP'
S = 'V-S-O/Np2S/'
O = 'V-S-O/Np2O/'


def fixture(specs, verse='JER_50:43'):
    """Specs are word/morpheme number, morphology, gloss and real Macula rule path."""
    oshb, macula = [], []
    for i, (number, morphology, gloss, nesting) in enumerate(specs):
        match = re.fullmatch(r'(\d+)([a-z]?)', number)
        word, suffix = match.groups()
        ref = f'{verse}w{number}'
        identifier = f'{int(word):05d}{suffix}'
        more = i + 1 < len(specs) and re.match(r'\d+', specs[i + 1][0])[0] == word
        row_type = ('m' if more else 'M') if suffix else 'w'
        row = dict.fromkeys(HEADERS, '')
        row.update(Ref=ref, OSHBid=identifier, RowType=row_type, Morphology=morphology,
                   WordOrMorpheme=number, NoCantillations=number,
                   GlossCapitalisation='S' if i == 0 else '', GlossOrder=str(10 * (i + 1)))
        row['ContextualMorphemeGloss' if suffix else 'ContextualWordGloss'] = gloss
        oshb.append(row)
        macula.append(dict(FGRef=ref, OSHBid=identifier, RowType=row_type,
                           Morphology=morphology, WordOrMorpheme=number,
                           EnglishGloss=gloss, PartOfSpeech='v' if morphology.startswith('V') else 'n',
                           Nesting=nesting))
    return oshb, macula


def jeremiah():
    # These paths and glosses reproduce the reported JER 50:43 construct chain.
    return fixture([('1', 'Vqp3ms', 'he_heard', V),
                    ('2', 'Ncmsc', 'the_king_of', S + 'NPofNP/N2NP'),
                    ('3', 'Np', 'of_Bāⱱel', S + 'NPofNP/N2NP'),
                    ('4', 'To', 'DOM', O + 'OmpNP/ObjMarker')])


class ReorderingTests(unittest.TestCase):
    def render(self, rows):
        with tempfile.TemporaryDirectory() as folder:
            state = apply.State()
            state.WLC_morpheme_rows = rows
            state.our_word_TSV_output_filepath = Path(folder) / 'words.tsv'
            with patch.object(apply, 'state', state), patch.object(apply, 'WLC_tsv_column_headers', HEADERS), patch.object(apply, 'vPrint'):
                apply.save_filled_word_TSV_file()
            with state.our_word_TSV_output_filepath.open(encoding='utf-8-sig') as f:
                words = list(DictReader(f, delimiter='\t'))
        export.saved_gloss = export.saved_capitalisation = export.saved_punctuation = ''
        export.just_had_insert = False
        for n, word in enumerate(words, 1):
            word['n'] = n
        rendered = [export.preform_row_gloss(False, word) for word in sorted(words, key=lambda w: int(w['GlossOrder']))]
        self.assertFalse(export.just_had_insert)
        self.assertEqual(export.saved_gloss, '')
        return re.sub(r'¦\d+', '', ' '.join(filter(None, rendered))), words

    def test_jeremiah_construct_chain_and_sentence_capital(self):
        rows, macula = jeremiah()
        before = deepcopy(rows)
        self.assertEqual(reorder_subject_phrases(rows, macula)['VS'], 1)
        text, _ = self.render(rows)
        self.assertEqual(text, 'The_king_of of_Bāⱱel he_heard DOM')
        self.assertEqual(rows[0]['GlossCapitalisation'], '')
        self.assertEqual(rows[1]['GlossCapitalisation'], 'S')
        for old, new in zip(before, rows):
            for key in old.keys() - {'GlossOrder', 'GlossCapitalisation'}:
                self.assertEqual(old[key], new[key])
        self.assertEqual(sorted(r['GlossOrder'] for r in rows), sorted(r['GlossOrder'] for r in before))
        again = deepcopy(rows)
        self.assertFalse(reorder_subject_phrases(rows, macula))
        self.assertEqual(rows, again)

    def test_long_phrase_articles_modifiers_and_embedded_clause(self):
        rows, macula = fixture([('1', 'Vqp3ms', 'he_heard', V),
            ('2a', 'Td', 'the', S + 'DetNP'), ('2b', 'Ncmsc', 'king', S + 'DetNP/N2NP'),
            ('3', 'Np', 'of_Bāⱱel', S + 'NPofNP/N2NP'),
            ('4', 'Aamsa', 'great', S + 'NpaAdj/Adj2Adjp'),
            ('5', 'Vqp3ms', 'who_ruled', S + 'NpRel/relCL/Vp2V/V2VP'),
            ('6', 'To', 'DOM', O + 'OmpNP/ObjMarker')])
        self.assertEqual(reorder_subject_phrases(rows, macula)['multiword_subjects'], 1)
        text, _ = self.render(rows)
        self.assertEqual(text, 'The÷king of_Bāⱱel great who_ruled he_heard DOM')

    def test_prefixed_verb_buffers_whole_np_including_suffixes(self):
        rows, macula = fixture([('1a', 'C', 'and', 'Cj2Cjp'), ('1b', 'Vqw3ms', 'he_said', V),
            ('2', 'Ncmsc', 'the_king_of', S + 'NPofNP/N2NP'),
            ('3', 'Np', 'of_Bāⱱel', S + 'NPofNP/N2NP'),
            ('4a', 'Ncmsc', 'servant', S + 'Np-Appos/NPofNP/N2NP'),
            ('4b', 'Sp3ms', 'his', S + 'Np-Appos/NPofNP/Pron2NP')])
        self.assertEqual(reorder_subject_phrases(rows, macula)['VS'], 1)
        text, words = self.render(rows)
        self.assertEqual(text, 'And= the_king_of Bāⱱel servant÷his =he_said')
        self.assertEqual([w['GlossInsert'] for w in words], ['', '_', '_', '_'])
        self.assertEqual(rows[0]['GlossCapitalisation'], 'S')
        self.assertFalse(reorder_subject_phrases(rows, macula))

    def test_vos_keeps_object_phrase_after_verb(self):
        rows, macula = fixture([('1', 'Vqp3ms', 'he_saw', 'V-O-S/Vp2V/V2VP'),
            ('2', 'To', 'DOM', 'V-O-S/Np2O/OmpNP/ObjMarker'),
            ('3a', 'Td', 'the', 'V-O-S/Np2O/OmpNP/DetNP'),
            ('3b', 'Ncmpa', 'people', 'V-O-S/Np2O/OmpNP/DetNP/N2NP'),
            ('4', 'Ncmsc', 'the_king', 'V-O-S/Np2S/NPofNP/N2NP'),
            ('5', 'Np', 'of_Bāⱱel', 'V-O-S/Np2S/NPofNP/N2NP')])
        self.assertEqual(reorder_subject_phrases(rows, macula)['VOS'], 1)
        self.assertEqual(self.render(rows)[0], 'The_king of_Bāⱱel he_saw DOM the÷people')

    def test_non_sentence_capitals_and_earlier_sentence_start(self):
        rows, macula = jeremiah()
        rows[0]['GlossCapitalisation'] = 'SD'
        rows[1]['GlossCapitalisation'] = 'N'
        reorder_subject_phrases(rows, macula)
        self.assertEqual(rows[0]['GlossCapitalisation'], 'D')
        self.assertEqual(rows[1]['GlossCapitalisation'], 'NS')
        rows, macula = fixture([('1', 'R', 'in_beginning', 'PP-V-S-O/Pp2PP/PrepNp/P2PP'),
            ('2', 'Vqp3ms', 'he_created', 'PP-V-S-O/Vp2V/V2VP'),
            ('3', 'Ncmpa', 'Elohim', 'PP-V-S-O/Np2S/N2NP')], verse='GEN_1:1')
        reorder_subject_phrases(rows, macula)
        self.assertEqual(self.render(rows)[0], 'In_beginning Elohim he_created')

    def test_repeated_clause_paths_do_not_merge_subjects(self):
        rows, macula = fixture([('1', 'Vqp3ms', 'he_heard', V),
            ('2', 'Ncmsa', 'king', S + 'N2NP'), ('3', 'Vqp3ms', 'he_said', V),
            ('4', 'Ncmsa', 'servant', S + 'N2NP')])
        self.assertEqual(reorder_subject_phrases(rows, macula)['VS'], 2)
        self.assertEqual(self.render(rows)[0], 'King he_heard servant he_said')

    def test_two_verb_prefixes_and_mixed_gloss_separators(self):
        rows, macula = fixture([('1a', 'C', 'and', 'Cj2Cjp'),
            ('1b', 'R', 'when', 'PrepCL/P2PP'), ('1c', 'Vqp3ms', 'he_came', V),
            ('2', 'Ncmsa', 'the_king', S + 'N2NP')])
        rows[2]['ContextualWordGloss'] = 'and=when,he_came'
        self.assertEqual(reorder_subject_phrases(rows, macula)['VS'], 1)
        self.assertEqual(self.render(rows)[0], 'And=when= the_king =he_came')

    def test_bracketed_sentence_start_preserves_repairs_and_markup(self):
        rows, macula = jeremiah()
        rows[1]['ContextualWordGloss'] = '[the]_king_of'
        reorder_subject_phrases(rows, macula)
        self.assertTrue(self.render(rows)[0].startswith('\\add +The\\add*_king_of'))
        # The renderer repairs this existing source gloss before capitalising.
        rows, _ = fixture([('1a', 'R', '[will', 'P2PP'),
                           ('1b', 'Ncmsa', 'in_the_month', 'N2NP')])
        self.assertTrue(self.render(rows)[0].startswith('\\add +Will\\add*'))

    def test_maqaf_and_shifted_word_numbers_use_verified_identities(self):
        rows, macula = jeremiah()
        for row in rows:
            row['Ref'] = re.sub(r'w(\d+)', lambda m: f'w{int(m[1])+1}', row['Ref'])
        marker = dict.fromkeys(HEADERS, '')
        marker.update(Ref='JER_50:43', RowType='seg', Morphology='x-maqqef', GlossOrder='25')
        rows.insert(2, marker)
        self.assertEqual(reorder_subject_phrases(rows, macula)['VS'], 1)
        self.assertEqual(self.render(rows)[0], 'The_king_of of_Bāⱱel he_heard DOM')

    def test_silent_interrogative_prefix_is_not_an_insertion_host(self):
        rows, macula = fixture([('1a', 'Ti', '?', 'V-S-O/Int'),
            ('1b', 'Vqrmsa', 'seeing', V), ('2', 'Pp2ms', 'you', S + 'Pron2NP')])
        before = deepcopy(rows)
        self.assertFalse(reorder_subject_phrases(rows, macula))
        self.assertEqual(rows, before)

    def test_unsafe_or_unsupported_spans_are_unchanged(self):
        for case in ('missing member', 'wrong identity', 'different clause', 'object',
                     'different verse', 'partial word', 'manual order', 'existing insert', 'copula', 'note'):
            with self.subTest(case=case):
                rows, macula = jeremiah()
                if case == 'missing member':
                    macula[2]['OSHBid'] = 'other'
                elif case == 'wrong identity':
                    macula[1]['WordOrMorpheme'] = 'different'
                elif case == 'different clause':
                    macula[1]['Nesting'] = 'Other/' + macula[1]['Nesting']
                elif case == 'object':
                    for m in macula[1:3]: m['Nesting'] = m['Nesting'].replace('Np2S', 'Np2O')
                elif case == 'different verse':
                    for m in macula[2:]: m['FGRef'] = m['FGRef'].replace('50:43', '50:44')
                    for r in rows[2:]: r['Ref'] = r['Ref'].replace('50:43', '50:44')
                elif case == 'partial word':
                    macula[2].update(FGRef='JER_50:43w3a', RowType='m')
                    rows[2].update(Ref='JER_50:43w3a', RowType='m')
                elif case == 'manual order':
                    rows[0]['GlossOrder'], rows[1]['GlossOrder'] = rows[1]['GlossOrder'], rows[0]['GlossOrder']
                elif case == 'existing insert':
                    rows[1]['GlossInsert'] = '_'
                elif case == 'copula':
                    macula[0]['EnglishGloss'] = 'there_was'
                else:
                    note = dict.fromkeys(HEADERS, '')
                    note.update(Ref='JER_50:43', RowType='variant note', GlossOrder='15')
                    rows.insert(1, note)
                before = deepcopy(rows)
                self.assertFalse(reorder_subject_phrases(rows, macula))
                self.assertEqual(rows, before)

    def test_empty_and_tiny_inputs(self):
        self.assertFalse(reorder_subject_phrases([], []))
        rows, macula = jeremiah()
        self.assertFalse(reorder_subject_phrases(rows[:1], macula[:1]))


if __name__ == '__main__':
    unittest.main()
