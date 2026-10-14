"""Regressions for lexical-table coverage and redundant definitions."""
import ast
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


CONNECTOR_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CONNECTOR_DIR))
from oet_alignment import propose_links
from oet_candidates import select_links
spec = importlib.util.spec_from_file_location('connect_word_table_tests', CONNECTOR_DIR / 'connect_OET-RV_words_via_OET-LV.py')
connect = importlib.util.module_from_spec(spec)
spec.loader.exec_module(connect)


class WordTableTests(unittest.TestCase):
    def test_unique_function_candidates_respect_live_anchors(self):
        def links(rv, lv):
            return [(t.text,n) for t,n,_ in select_links(connect.tokenize(rv),
                [connect.LVToken(w,n) for w,n in lv], connect.scoreAlignedWords,
                connect.simplifyRVLVWord, connect.numberVariants)]
        self.assertNotIn(('And',3), links('today¦1 And we have no defence that¦2 Then¦3',
                            [('today',1),('that',2),('And',3),('Then',3)]))
        self.assertNotIn(('have',3), links('today¦1 And we have no defence that¦2',
                            [('today',1),('that',2),('have',3)]))
        self.assertIn(('to',20), links('come¦30 to me¦10', [('come',30),('to',20),('me',10)]))
        for rv in ('has come¦1', 'it¦1 has come¦1', 'has come'):
            self.assertIn(('has',1), links(rv, [('it',1),('has',1),('come',1)]))
        self.assertEqual(links('at', [('in/on/at/with',1)]), [('at',1)])

    def test_function_word_cannot_reuse_a_gloss_across_reordered_anchors(self):
        self.assertEqual(self.aligned('walking¦3 power¦1 or¦2 closeness to',
            [('power',1),('or',2),('to',3),('be',3),('walking',3)]), [])

    def test_ot_proper_nouns_require_morphology_not_missing_capitalisation(self):
        with patch.object(connect.state, 'wordTableHeaderList', {'OT':['Morphology']}, create=True):
            for morphology in ('Np', 'R,Np'):
                self.assertTrue(connect.lvWordIsProperNoun([morphology], 'OT'))
            for morphology in ('Pp1cs', 'Td,Ncfsa', 'Vqp1cs', ''):
                self.assertFalse(connect.lvWordIsProperNoun([morphology], 'OT'))
    def test_prefix_collisions_cannot_create_links(self):
        # Reviewed errors found by the October 2026 whole-Bible audit. Neither
        # uniqueness nor positional certainty establishes lexical equivalence.
        for rv, lv in (
            ('against', 'again'), ('again', 'against'), ('there', 'therefore'),
            ("There's", 'Therefore'), ('conceived', 'concerning'),
            ('longed', 'longer'), ('thoughts', 'though'),
            ('everyone', 'everywhere'), ('brides', 'bridegroom'),
            ('counted', 'countryman'), ('courtyards', 'court-official'),
            ('creator', 'creatures'), ('lamps', 'lampstand'),
            ('percentage', 'perceived'), ('prove', 'proverb'),
            ('regular', 'regulation'), ('stripes', 'stripped'),
            ('terrified', 'territories'), ('threshold', 'threshed'),
            ('utterly', 'utterance'), ('commands', 'commander'),
            ('command', 'commander'),
        ):
            with self.subTest(rv=rv, lv=lv):
                self.assertIsNone(connect.scoreAlignedWords(rv, lv))
                self.assertEqual(self.aligned(rv, [(lv, 1)]), [])

    def test_reviewed_derivations_use_inflections_but_not_transitive_synonyms(self):
        self.assertEqual(connect.scoreAlignedWords('destroying', 'destruction'),
                         ('reviewed related forms', 50))
        self.assertEqual(connect.scoreRVLVWords('faithfully', 'faithfulness'),
                         ('reviewed related forms', 50))
        # Both are related to "every", but not to one another.
        self.assertIsNone(connect.scoreAlignedWords('everyone', 'everywhere'))

    def test_lv_optional_suffixes_and_pronoun_annotations(self):
        self.assertEqual(self.aligned('sons and rams', [('son[s]',1),('and',2),('ram[s]',3)]),
                         [('sons',1),('and',2),('rams',3)])
        self.assertEqual(connect.normaliseLVVerseText('yourself(m)¦1 herself(f)¦2'),
                         'yourself¦1 herself¦2')

    def test_sentence_case_does_not_reverse_directional_pairs(self):
        self.assertEqual(self.aligned("Can't", [('not',1)]), [("Can't",1)])
        self.assertIsNone(connect.scoreAlignedWords('Not', "Can't"))

    def test_reviewed_synonyms_keep_direction_and_weak_evidence(self):
        for rv, lv in (('weightier', 'heavier'), ('yeast', 'leaven'),
                       ('cavalry', 'horsemen'), ('encouragement', 'exhortation')):
            with self.subTest(rv=rv, lv=lv):
                self.assertEqual(connect.scoreAlignedWords(rv.capitalize(), lv),
                                 ('directional word mapping', 55))
                self.assertIsNone(connect.scoreAlignedWords(lv, rv))
        # No transitive expansion through synonyms, nor guesses from prefixes.
        for rv, lv in (('weightier', 'heavy'), ('weightier', 'weighed'),
                       ('yeast', 'unleavened'), ('yeast', 'bread')):
            self.assertIsNone(connect.scoreAlignedWords(rv, lv))

    def test_contractions_link_the_subject_only_with_unambiguous_context(self):
        self.assertEqual(self.aligned("You're here and you're there",
            [('you',1),('here',2),('and',3),('you',4),('there',5)]),
            [("You're",1),('here',2),('and',3),("you're",4),('there',5)])
        self.assertEqual(self.aligned("you're", [('you',1),('you',2)]), [])
        self.assertEqual(self.aligned("I'm¦1 I", [('I',1)]), [])
        self.assertIsNone(connect.scoreAlignedWords('you', "you're"))
        self.assertIsNone(connect.scoreAlignedWords("you're", 'your'))

    def aligned(self, rv, lv):
        return [(t.text, n) for t, n, _ in propose_links(connect.tokenize(rv),
            [connect.LVToken(w, n) for w, n in lv],
            connect.scoreAlignedWords, connect.simplifyRVLVWord, phrase_index=connect.ALIGNED_PHRASE_INDEX)]

    def test_repeated_possessive_phrases_have_separate_source_owners(self):
        self.assertEqual(self.aligned('his son and his daughter',
            [('of',1),('him',1),('son',2),('and',3),('of',4),('him',4),('daughter',5)]),
            [('his',1),('son',2),('and',3),('his',4),('daughter',5)])
        self.assertEqual(self.aligned('his', [('of',1),('him',2)]), [])
        self.assertEqual(self.aligned('his', [('of',1),('him',1),('of',2),('him',2)]), [])
        # Whole-phrase ownership survives saving and subsequent book passes.
        self.assertEqual(self.aligned('his¦7 him', [('of',7),('him',7)]), [])

    def test_demonym_phrase_wins_over_an_earlier_generic_people(self):
        self.assertEqual(self.aligned('Israelis why',
            [('people',1),('Men',2),('>ones',3),('from',3),
             ('Israaʸl/Yisrāʼēl',3),('why',4)]), [('Israelis',3),('why',4)])

    def test_multiword_rv_phrase_and_excluded_phrase_word(self):
        self.assertEqual(self.aligned('ran away', [('fled',7)]), [('ran',7),('away',7)])
        # The ordinary directional ran/fled link remains valid; away is excluded.
        self.assertEqual(self.aligned(r'ran \add >away\add*', [('fled',7)]), [('ran',7)])

    def test_english_one_letter_words_use_context_but_not_arbitrary_fragments(self):
        self.assertEqual(self.aligned('I saw a king', [('I',1),('saw',1),('a',2),('king',3)]),
                         [('I',1),('saw',1),('a',2),('king',3)])
        self.assertEqual(self.aligned('I', [('I',1),('I',2)]), [])
        self.assertIsNone(connect.scoreAlignedWords('x', 'x'))

    def test_directional_mappings_disambiguate_repeated_occurrences(self):
        self.assertEqual(self.aligned("can't and can't", [('not',1),('and',2),('not',3)]),
                         [("can't",1),('and',2),("can't",3)])
        self.assertIsNone(connect.scoreAlignedWords('not', "can't"))
        self.assertEqual(self.aligned("can't", [('not',1),('not',2)]), [])
        self.assertEqual(self.aligned('country', [('earth/land',1)]), [('country',1)])

    def test_curated_noun_pairs_are_used_in_alignment(self):
        self.assertEqual(connect.scoreAlignedWords('hooves', 'hoof'), ('curated noun forms',95))
        self.assertEqual(self.aligned('men and men', [('man',1),('and',2),('man',3)]),
                         [('men',1),('and',2),('men',3)])

    def test_pronoun_metadata_is_not_part_of_the_word(self):
        self.assertEqual(connect.normaliseLVVerseText(
            'You(pl)¦1=your(ms)¦2_will¦3_you(fs)¦3 yourselves(pl)¦4 region(s)¦5'),
            'You¦1 your¦2 will¦3 you¦3 yourselves¦4 regions¦5')

    def test_clause_context_selects_the_later_synonym(self):
        self.assertEqual(self.aligned('earth and ground', [('earth',1),('and',2),('soil',3)]),
                         [('earth',1),('and',2),('ground',3)])

    def test_words_and_phrases_are_kept_in_their_respective_tables(self):
        for rv, lv in connect.RV_SINGLE_WORDS_FROM_LV_WORDS:
            with self.subTest(rv=rv, lv=lv):
                self.assertEqual(len(rv.split()), 1)
                self.assertEqual(len(lv.split()), 1)
        for rv, lv in connect.RV_SINGLE_WORDS_FROM_LV_WORD_STRINGS:
            with self.subTest(rv=rv, lv=lv):
                self.assertEqual(len(rv.split()), 1)
                self.assertGreater(len(lv.split()), 1)
        for lv, rv in connect.LV_SINGLE_WORDS_TO_RV_WORD_STRINGS:
            with self.subTest(rv=rv, lv=lv):
                self.assertEqual(len(lv.split()), 1)
                self.assertGreater(len(rv.split()), 1)

    def test_immersion_verb_forms_use_the_stronger_verb_match(self):
        forms = ('immersed', 'immersing', 'immerses', 'immerse')
        for rv in forms:
            for lv in forms:
                if rv != lv:
                    with self.subTest(rv=rv, lv=lv):
                        self.assertEqual(connect.scoreRVLVWords(rv, lv), ('curated verb forms', 95))
        self.assertEqual(connect.scoreRVLVWords('immersed', 'immersion'),
                         ('another word for the same thing', 60))

    def test_needed_noun_and_positional_mappings_remain(self):
        # The simple noun matcher does not derive the irregular hoof/hooves pair.
        self.assertIn(('hooves', 'hoof'), connect.RV_SINGLE_WORDS_FROM_LV_WORDS)
        # The verse-wide noun matcher cannot distinguish these repeated sons.
        proposals = propose_links(connect.tokenize('sons and sons'),
            [connect.LVToken('son', 1), connect.LVToken('and', 2), connect.LVToken('son', 3)],
            connect.scoreRVLVWords, connect.simplifyRVLVWord)
        self.assertEqual([number for token, number, _ in proposals if token.text == 'sons'], [1, 3])
        for rv, lv in (('arms', 'hands'), ('bash', 'strike')):
            self.assertEqual(connect.scoreRVLVWords(rv, lv), ('another word for the same thing', 60))

    def test_mapping_modes_keep_the_matching_passes_distinct(self):
        # A contraction is an exact, one-way correspondence, not a general synonym.
        self.assertIn(("can't", 'not'), connect.RV_SINGLE_WORDS_FROM_LV_WORDS)
        self.assertNotIn(('not', "can't"), connect.RV_SINGLE_WORDS_FROM_LV_WORDS)
        self.assertIsNone(connect.scoreRVLVWords("can't", 'not'))
        self.assertIsNone(connect.scoreRVLVWords('not', "can't"))
        # These positional alternatives must not become verse-wide unique matches.
        self.assertNotIn(('arms', 'hands'), connect.RV_SINGLE_WORDS_FROM_LV_WORDS)
        self.assertNotIn(('hands', 'arms'), connect.RV_SINGLE_WORDS_FROM_LV_WORDS)
        for rv, lv in (('arms', 'hands'), ('hands', 'arms')):
            self.assertEqual(connect.scoreRVLVWords(rv, lv), ('another word for the same thing', 60))
        # This shared correspondence remains available to both passes.
        self.assertIn(('fishermen', 'fishers'), connect.RV_SINGLE_WORDS_FROM_LV_WORDS)
        for rv, lv in (('fishermen', 'fishers'), ('fishers', 'fishermen')):
            self.assertEqual(connect.scoreRVLVWords(rv, lv), ('another word for the same thing', 60))

    def test_positional_alternatives_do_not_gain_transitive_matches(self):
        self.assertIn('commander', connect.EQUIVALENT_LV_RV_WORDS['chief'])
        self.assertIn('high', connect.EQUIVALENT_LV_RV_WORDS['chief'])
        self.assertNotIn('high', connect.EQUIVALENT_LV_RV_WORDS['commander'])
        self.assertNotIn('commander', connect.EQUIVALENT_LV_RV_WORDS['high'])

    def test_single_word_list_has_no_duplicate_pairs(self):
        tree = ast.parse((CONNECTOR_DIR / 'oet_word_tables.py').read_text())
        node = next(node.value for node in tree.body if isinstance(node, ast.Assign)
                    and any(isinstance(target, ast.Name) and target.id == 'SINGLE_WORD_MAPPINGS'
                            for target in node.targets))
        pairs = set()
        aligned_pairs = set()
        for mapping in ast.literal_eval(node):
            rv, lv = mapping[:2]
            self.assertNotIn((rv, lv), pairs)
            pairs.add((rv, lv))
            if len(mapping) == 2:
                continue
            self.assertIn(mapping[2], ('aligned', 'both'))
            self.assertEqual(connect.simplifyRVLVWord(rv), rv)
            self.assertEqual(connect.simplifyRVLVWord(lv), lv)
            self.assertNotEqual(rv, lv)
            pair = frozenset((rv, lv))
            self.assertNotIn(pair, aligned_pairs)
            aligned_pairs.add(pair)


if __name__ == '__main__':
    unittest.main()
