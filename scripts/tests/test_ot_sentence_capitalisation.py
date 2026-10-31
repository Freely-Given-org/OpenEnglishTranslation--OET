# SPDX-License-Identifier: MPL-2.0
"""Sentence starts must survive OSHB annotations before the English build."""
from copy import deepcopy
from csv import DictReader
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

import prepare_OSHB_for_glossing as prepare
import apply_Clear_Macula_OT_glosses as apply
import extract_glossed_OSHB_OT_to_ESFM as export
from hebrew_gloss_order import reorder_subject_phrases


def raw(ref, row_type, morphology='', text='מַה', identifier='', special=''):
    verse = int(ref.split(':')[1].split('w')[0])
    return dict(FGID=f'19052{verse:03d}01', Ref=ref, RowType=row_type,
                Special=special, Strongs='', CantillationHierarchy='',
                Morphology=morphology, OSHBid=identifier, WordOrMorpheme=text)


def word(verse=3, **changes):
    row = raw(f'PSA_52:{verse}w1', 'w', 'HTi', identifier='19Ynk')
    row.update(changes)
    return row


def note(verse=3, special=''):
    return raw(f'PSA_52:{verse}', 'note', text=f'KJV:Ps.52.{verse-2}', special=special)


def segment(kind='x-sof-pasuq', verse=2):
    return raw(f'PSA_52:{verse}', 'seg', kind, '׃')


class SentenceCapitalisationTests(unittest.TestCase):
    def prepare(self, rows):
        state = prepare.State()
        state.WLC_rows = deepcopy(rows)
        with patch.object(prepare, 'state', state), patch.object(prepare, 'vPrint'):
            self.assertTrue(prepare.create_expanded_TSV_table())
        return state.WLC_rows

    def test_psalm_52_numbering_note_does_not_consume_capital(self):
        rows = self.prepare([word(2), segment(), note(), word(), segment(verse=3)])
        self.assertEqual([r['GlossCapitalisation'] for r in rows], ['S', '', '', 'S', ''])
        self.assertEqual(rows[2]['WordOrMorpheme'], 'KJV:Ps.52.1')
        self.assertEqual([r['GlossOrder'] for r in rows], ['10', '20', '10', '20', '30'])
        self.assertEqual(rows[1]['GlossPunctuation'], '.')

    def test_sentence_flag_survives_multiple_notes_and_section_markers(self):
        rows = self.prepare([word(2), segment(), segment('x-pe'),
                             note(special='exegesis'), segment('x-samekh'),
                             note(), word(), segment(verse=3)])
        self.assertEqual([r['GlossCapitalisation'] for r in rows], ['S', '', '', '', '', '', 'S', ''])

    def test_leading_annotations_and_aramic_ketiv_words(self):
        for morphology in ('HNcmsa', 'ANcmsa'):
            with self.subTest(morphology=morphology):
                rows = self.prepare([note(), segment('x-pe', verse=3),
                                     word(Morphology=morphology, Special='K'), segment(verse=3)])
                self.assertEqual([r['GlossCapitalisation'] for r in rows], ['', '', 'S', ''])
                self.assertEqual(rows[2]['RowType'], 'AwK' if morphology.startswith('A') else 'wK')

    def test_annotations_and_verse_changes_do_not_start_sentences(self):
        # Only the existing sentence boundary (sof pasuq) sets a new flag.
        rows = self.prepare([word(2), note(2), segment('x-maqqef'),
                             segment('x-paseq'), word(), segment(verse=3)])
        self.assertEqual([r['GlossCapitalisation'] for r in rows], ['S', '', '', '', '', ''])

    def test_psalm_52_8_capital_survives_reordering_and_esfm_export(self):
        rows = self.prepare([
            note(8),
            raw('PSA_52:8w1a', 'm', 'HC', 'וְ', '19SCia'),
            raw('PSA_52:8w1b', 'm', 'Vqi3mp', 'יִרְא֖וּ', '19SCib'),
            raw('PSA_52:8w2', 'w', 'HAampa', 'צַדִּיקִ֥ים', '19cnJ'),
            segment(verse=8)])
        macula = []
        specs = [('and', 'cj', 'Cj2Cjp'),
                 ('they_will_see', 'v', 'V-S/Vp2V/V2VP'),
                 ('righteous_[people]', 'adj', 'V-S/Np2S/Adj2NP/Adj2Adjp')]
        headers = prepare.State().expanded_headers
        for row in rows:
            for field in headers:
                row.setdefault(field, '')
        for row, (gloss, pos, nesting) in zip(rows[1:4], specs):
            row['ContextualWordGloss' if row['RowType'] == 'w' else 'ContextualMorphemeGloss'] = gloss
            macula.append(dict(FGRef=row['Ref'], OSHBid=row['OSHBid'], RowType=row['RowType'],
                               WordOrMorpheme=row['WordOrMorpheme'], Morphology=row['Morphology'],
                               PartOfSpeech=pos, EnglishGloss=gloss, Nesting=nesting))
        self.assertEqual(reorder_subject_phrases(rows, macula)['VS'], 1)
        with tempfile.TemporaryDirectory() as folder:
            state = apply.State()
            state.WLC_morpheme_rows = rows
            state.our_word_TSV_output_filepath = Path(folder) / 'words.tsv'
            with patch.object(apply, 'state', state), patch.object(apply, 'WLC_tsv_column_headers', headers), patch.object(apply, 'vPrint'):
                apply.save_filled_word_TSV_file()
            with state.our_word_TSV_output_filepath.open(encoding='utf-8-sig') as f:
                words = list(DictReader(f, delimiter='\t'))
        for n, row in enumerate(words, 1):
            row['n'] = n
        with patch.multiple(export, saved_gloss='', saved_capitalisation='',
                            saved_punctuation='', just_had_insert=False):
            rendered = ' '.join(filter(None, (export.preform_row_gloss(False, row)
                       for row in sorted(words, key=lambda r: int(r['GlossOrder'])))))
            self.assertFalse(export.just_had_insert)
        rendered = re.sub(r'¦\d+', '', rendered)
        self.assertIn('Note: KJB: Ps.52.6', rendered)
        self.assertIn('And= righteous_\\add >people\\add* =they_will_see', rendered)
        self.assertNotIn('=They', rendered)


if __name__ == '__main__':
    unittest.main()
