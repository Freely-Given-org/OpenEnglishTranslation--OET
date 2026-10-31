# SPDX-License-Identifier: MPL-2.0
"""Run from scripts with: uv run python -m unittest discover -s tests."""
from copy import deepcopy
import unittest

from ot_gloss_fallbacks import fix_known_gloss_duplication, recover_missing_word_glosses, select_gloss


def word(**changes):
    row = dict(Ref='PSA_41:3w4', RowType='K', NoCantillations='יאשר',
               Word='יאשר', Morphology='Ti', MorphemeRowList='360189',
               ContextualWordGloss='', WordGloss='',
               ContextualMorphemeGlosses='', MorphemeGlosses='')
    row.update(changes)
    return row


def qere_fixture():
    # Macula numbers the qere w5, whereas OSHB numbers the ketiv w4.
    rows = [word(), dict(Ref='PSA_41:3', RowType='variant note',
                        Word="יאשר: (x-qere) 'וְ/אֻשַּׁ֣ר': lemma=c/833 morph=HC/VPq3ms")]
    macula = [dict(FGRef='PSA_41:3w5a', RowType='m', WordOrMorpheme='וְ',
                   Morphology='C', EnglishGloss='and', ContextualGloss='and'),
              dict(FGRef='PSA_41:3w5b', RowType='M', WordOrMorpheme='אֻשַּׁ֣ר',
                   Morphology='VPq3ms', EnglishGloss='blessed',
                   ContextualGloss='he_will_be_called_blessed')]
    return rows, macula


class GlossSelectionTests(unittest.TestCase):
    def test_leannoth_is_one_whole_word(self):
        row = word(Ref='PSA_88:1w8', RowType='', NoCantillations='לְ,עַנּוֹת',
                   MorphemeRowList='372219,372220', MorphemeGlosses='to/for,leannoth',
                   ContextualMorphemeGlosses='leannoth,leannoth')
        fix_known_gloss_duplication(row)
        self.assertEqual(select_gloss(row), ('CWG', 'leannoth'))

    def test_other_repetitions_and_existing_glosses_are_preserved(self):
        for changes in (dict(ContextualMorphemeGlosses='very,very'),
                        dict(ContextualWordGloss='a_custom_gloss'),
                        dict(NoCantillations='another_word')):
            row = word(NoCantillations='לְ,עַנּוֹת', MorphemeRowList='1,2',
                       ContextualMorphemeGlosses='leannoth,leannoth')
            row.update(changes)
            before = deepcopy(row)
            fix_known_gloss_duplication(row)
            self.assertEqual(row, before)

    def test_cmp_uses_existing_word_gloss(self):
        self.assertEqual(select_gloss(word(ContextualWordGloss='(cmp)', WordGloss='that')),
                         ('WG', 'that'))

    def test_cmp_repairs_only_affected_morpheme(self):
        row = word(MorphemeRowList='1,2', ContextualMorphemeGlosses='(cmp),he_will_say',
                   MorphemeGlosses='to,say')
        self.assertEqual(select_gloss(row), ('CMG', 'to,he_will_say'))
        self.assertEqual(row['ContextualMorphemeGlosses'], '(cmp),he_will_say')

    def test_unaligned_morphemes_use_complete_word_alternative(self):
        self.assertEqual(select_gloss(word(MorphemeRowList='1,2',
                         ContextualMorphemeGlosses='and,(cmp)', MorphemeGlosses='and',
                         WordGloss='and=because')), ('WG', 'and=because'))

    def test_no_alternative_does_not_hide_missing_data(self):
        self.assertEqual(select_gloss(word()), ('WG', ''))
        self.assertEqual(select_gloss(word(ContextualWordGloss='(cmp)')), ('CWG', '(cmp)'))

    def test_placeholder_uses_other_gloss(self):
        self.assertEqual(select_gloss(word(ContextualWordGloss='wwww', WordGloss='blessed')),
                         ('WG', 'blessed'))

    def test_ordinary_priorities_and_numeric_glosses_unchanged(self):
        self.assertEqual(select_gloss(word(ContextualWordGloss='he_says', WordGloss='say')),
                         ('CWG', 'he_says'))
        self.assertEqual(select_gloss(word(ContextualWordGloss='1,000', WordGloss='thousand')),
                         ('WG', 'thousand'))
        self.assertEqual(select_gloss(word(ContextualWordGloss='1,000')), ('CWG', '1,000'))


class MissingGlossRecoveryTests(unittest.TestCase):
    def test_explicit_qere_with_different_word_number(self):
        rows, macula = qere_fixture()
        before = deepcopy(rows)
        self.assertEqual(recover_missing_word_glosses(rows, iter(macula)), 1)
        self.assertEqual(rows[0]['ContextualWordGloss'], 'and,he_will_be_called_blessed')
        self.assertEqual(rows[0]['WordGloss'], 'and,blessed')
        for key in before[0].keys() - {'WordGloss', 'ContextualWordGloss'}:
            self.assertEqual(rows[0][key], before[0][key])
        self.assertEqual(rows[1], before[1])
        self.assertEqual(recover_missing_word_glosses(rows, macula), 0)

    def test_importer_morpheme_table_also_supported(self):
        rows, macula = qere_fixture()
        rows[0]['RowType'] = 'wK'
        del rows[0]['MorphemeRowList']
        for row in rows:
            row['WordOrMorpheme'] = row.pop('Word')
        self.assertEqual(recover_missing_word_glosses(rows, macula), 1)

    def test_existing_gloss_is_preserved(self):
        rows, macula = qere_fixture()
        rows[0]['WordGloss'] = 'blessed'
        before = deepcopy(rows)
        self.assertEqual(recover_missing_word_glosses(rows, macula), 0)
        self.assertEqual(rows, before)

    def test_no_guess_for_omitted_multiword_or_wrong_ketiv(self):
        for note in ("יאשר: (x-qere)", "יאשר אחר: (x-qere) 'וְ/אֻשַּׁ֣ר'",
                     "יאשר: (x-qere) 'וְ אֻשַּׁ֣ר'", "אחר: (x-qere) 'וְ/אֻשַּׁ֣ר'"):
            with self.subTest(note=note):
                rows, macula = qere_fixture()
                rows[1]['Word'] = note
                before = deepcopy(rows)
                self.assertEqual(recover_missing_word_glosses(rows, macula), 0)
                self.assertEqual(rows, before)

    def test_ambiguous_cross_verse_incomplete_or_unglossed_matches_rejected(self):
        for case in ('ambiguous', 'other verse', 'incomplete', 'missing gloss'):
            with self.subTest(case=case):
                rows, macula = qere_fixture()
                if case == 'ambiguous':
                    macula += [dict(r, FGRef=r['FGRef'].replace('w5', 'w6')) for r in macula]
                elif case == 'other verse':
                    for r in macula:
                        r['FGRef'] = r['FGRef'].replace('41:3', '41:4')
                elif case == 'incomplete':
                    macula.pop()
                else:
                    macula[1]['ContextualGloss'] = macula[1]['EnglishGloss'] = ''
                self.assertEqual(recover_missing_word_glosses(rows, macula), 0)

    def test_exact_word_match_requires_same_vowels_and_morphology(self):
        macula = [dict(FGRef='LEV_11:42w21', RowType='w', WordOrMorpheme='שֶׁקֶץ',
                       Morphology='Ncmsa', EnglishGloss='detestable_thing', ContextualGloss='')]
        for text, morphology, expected in (('שֶׁ֥קֶץ', 'Ncmsa', 1),
                                            ('שָׁקֶץ', 'Ncmsa', 0),
                                            ('שֶׁקֶץ', 'Ncfsa', 0)):
            with self.subTest(text=text, morphology=morphology):
                rows = [word(Ref='LEV_11:42w21', RowType='', NoCantillations=text, Morphology=morphology)]
                self.assertEqual(recover_missing_word_glosses(rows, macula), expected)


if __name__ == '__main__':
    unittest.main()
