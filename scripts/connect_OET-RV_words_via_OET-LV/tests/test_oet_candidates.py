"""Selection policy regressions using tiny passages, with no Bible-file writes."""
from itertools import permutations
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from oet_alignment import LVToken, tokenize
from oet_candidates import Candidate, Evidence, select_candidates, select_links, unique_word_candidates
from test_connect_oet_words import connect


class CandidateTests(unittest.TestCase):
    def links(self, rv, lv, **kwargs):
        columns = [LVToken(*c) if isinstance(c, tuple) else c for c in lv]
        return [(t.text, n) for t, n, _ in select_links(tokenize(rv), columns,
            connect.scoreAlignedWords, connect.simplifyRVLVWord, connect.numberVariants,
            phrase_index=connect.ALIGNED_PHRASE_INDEX, directional_index=connect.DIRECTIONAL_WORD_INDEX, **kwargs)]

    def test_provider_order_does_not_resolve_conflicts(self):
        a, b, c = tokenize('alpha beta gamma')
        contextual = Candidate(((a, 1),), frozenset({0}), 'context', 3)
        wrong_fallback = Candidate(((a, 2),), frozenset({1}), 'fallback')
        competing = Candidate(((b, 1),), frozenset({0}), 'fallback')
        unrelated = Candidate(((c, 3),), frozenset({2}), 'fallback')
        for candidates in permutations((contextual, wrong_fallback, competing, unrelated)):
            self.assertEqual(set(select_candidates(candidates)), {contextual, unrelated})
        first = Candidate(((a, 1),), frozenset({0}), 'provider A')
        second = Candidate(((b, 1),), frozenset({0}), 'provider B')
        self.assertEqual(select_candidates([first, second]), [])
        self.assertEqual(select_candidates([second, first]), [])

    def test_competing_phrase_is_atomic(self):
        a, b = tokenize('alpha beta')
        phrase = Candidate(((a, 1),(b, 1)), frozenset({0}), 'phrase')
        anchor = Candidate(((b, 2),), frozenset({1}), 'anchor')
        self.assertEqual(select_candidates([phrase], [anchor]), [])

    def test_saved_phrase_ownership_also_blocks_unique_recovery(self):
        self.assertEqual(self.links('his¦7 him', [('of',7),('him',7)]), [])
        self.assertEqual(self.links('you¦7 all', [('you',7),('all',7)]), [('all',7)])
        self.assertEqual(self.links('ran¦7 away', [('fled',7)]), [('away',7)])
        self.assertEqual(self.links("I'm¦7 I", [('I',7)]), [])
        self.assertEqual(self.links("I'm¦7 am I", [('I',7),('am',8)]), [('am',8)])

    def test_both_mapping_retains_directional_recovery_permission(self):
        columns = [LVToken('fishers',7)]
        evidence = Evidence(columns, connect.scoreAlignedWords, connect.simplifyRVLVWord,
                            connect.numberVariants, connect.DIRECTIONAL_WORD_INDEX)
        proposals = list(unique_word_candidates(tokenize('fishermen'), evidence))
        self.assertEqual([c.bindings[0][1] for c in proposals], [7])

    def test_mutual_uniqueness_compares_competing_occurrence_strengths(self):
        columns = [LVToken('sons',7)]
        evidence = Evidence(columns, connect.scoreAlignedWords, connect.simplifyRVLVWord,
                            connect.numberVariants, connect.DIRECTIONAL_WORD_INDEX)
        for rv in ('son sons', 'sons son'):
            candidates = list(unique_word_candidates(tokenize(rv), evidence))
            self.assertEqual([(t.text,n) for c in candidates for t,n in c.bindings], [('sons',7)])
        self.assertEqual(list(unique_word_candidates(tokenize('sons sons'), evidence)), [])

    def test_context_selects_final_soil_for_ground(self):
        self.assertEqual(self.links('earth and ground', [('earth',1),('and',2),('soil',3)]),
                         [('earth',1),('and',2),('ground',3)])

    def test_reviewed_synonyms_in_mapped_ot_and_nt_passages(self):
        # Actual mapped passages preserve source IDs, repeated occurrences and
        # saved anchors. Matthew includes the revised RV wording of 13 October.
        fixtures = json.loads(Path(__file__).with_name('synonym_passages.json').read_text())
        for passage in fixtures:
            with self.subTest(reference=passage['reference']):
                columns = [LVToken(word.split('¦', 1)[0], connect.getLVWordNumber(word))
                           for word in connect.normaliseLVVerseText(passage['lv'].replace('+', '')).split()
                           if connect.getLVWordNumber(word) is not None and not word.startswith('DOM¦')]
                columns = connect.with_clause_boundaries(columns, passage['lv'])
                expected = [tuple(link) for link in passage['expected']]
                wanted = {word.casefold() for word, _ in expected}
                wanted.update(passage.get('unresolved', ()))
                self.assertTrue(wanted, 'Every fixture must check a specific occurrence')
                actual = self.links(passage['rv'], columns)
                self.assertEqual([link for link in actual if link[0].casefold() in wanted], expected)

    def test_synonyms_do_not_resolve_indistinguishable_repeated_sources(self):
        self.assertEqual(self.links('weightier', [('heavier', 1), ('heavier', 2)]), [])
        self.assertEqual(self.links('yeast', [('leaven', 1), ('leaven', 2)]), [])
        self.assertEqual(self.links('yeast and yeast', [('leaven', 1), ('and', 2), ('leaven', 3)]),
                         [('yeast', 1), ('and', 2), ('yeast', 3)])

    def test_phrase_modifier_prevents_a_synonym_from_reversing_the_meaning(self):
        self.assertEqual(self.links('the less sensible asked the sensible',
            [('the', 1), ('foolish', 2), ('asked', 3), ('the', 4), ('prudent', 5)]),
            [('the', 1), ('less', 2), ('sensible', 2), ('asked', 3), ('the', 4), ('sensible', 5)])

    def test_new_synonyms_respect_excluded_add_spans(self):
        for marker in ('add', '+add'):
            for prefix in ('', '<', '>', '?<', '?>'):
                with self.subTest(marker=marker, prefix=prefix):
                    self.assertEqual(self.links(f'\\{marker} {prefix}weightier\\{marker}*',
                                                [('heavier', 16288)]), [])

    def test_exact_recovery_counts_linked_occurrences_and_rejects_prefixes(self):
        for rv, lv in (('there¦1 there', [('there',1)]),
                       ('there', [('there',1),('there',2)]),
                       ('walked¦1 walking', [('walk',1)])):
            self.assertEqual(self.links(rv, lv), [])
        self.assertEqual(self.links('There against', [('again',1),('there',2)]), [('There',2)])

    def test_curated_alternatives_compete_by_context_not_table_priority(self):
        # The old direct writer chose come because that row preceded draw near.
        self.assertEqual(self.links('come then approach',
            [('come',1),('then',2),('draw',3),('near',3)]), [('come',1),('then',2),('approach',3)])
        self.assertEqual(self.links('his', [('of',1),('him',1),('of',2),('him',2)]), [])
        self.assertEqual(self.links('his', [('of',1),('him',2)]), [])
        self.assertEqual(self.links('hooves and hooves', [('hoof',1),('and',2),('hoof',3)]),
                         [('hooves',1),('and',2),('hooves',3)])

    def test_repeated_name_candidates_use_occurrences(self):
        columns = [LVToken('Maria',1,names=frozenset({'maria'})), LVToken('and',2),
                   LVToken('Mariam',3,names=frozenset({'maria'}))]
        self.assertEqual(self.links('Maria and Maria', columns), [('Maria',1),('and',2),('Maria',3)])

    def test_named_anchors_resolve_a_reordered_genealogy(self):
        name = frozenset({'isaac'})
        self.assertEqual(self.links("Isaac Isaac's sons", [LVToken('Yitschaq',1,names=name),
            LVToken('sons',3), LVToken('Yitschaq',2,names=name)]),
            [('Isaac',1),("Isaac's",2),('sons',3)])
        self.assertEqual(self.links("Abraham son Isaac Isaac's sons", [
            LVToken('Abraham',1,names=frozenset({'abraham'})), LVToken('fathered',2),
            LVToken('Yitschaq',3,names=name), LVToken('sons',4), LVToken('Yitschaq',5,names=name)]),
            [('Abraham',1),('Isaac',3),("Isaac's",5),('sons',4)])

    def test_traditional_alias_cannot_borrow_an_earlier_names_number(self):
        rv = r"Shadrak¦1 \add !(Hananyah)\add*, Meyshak \add !(Misha'el)\add*"
        self.assertEqual(self.links(rv, [LVToken('Shadrach',1,names=frozenset({'shadrak'})),
                                       LVToken('Meshach',2)]), [('Hananyah',1),('Meyshak',2)])

    def test_traditional_alias_and_original_can_share_a_source(self):
        self.assertEqual(self.links(r'Yohan \add !(John)\add*',
            [LVToken('Ioannes',1,names=frozenset({'yohan','john'}))]), [('Yohan',1),('John',1)])

    def test_unknown_alias_does_not_claim_the_names_attached_conjunction(self):
        self.assertEqual(self.links(r'and¦1 Yafet¦1 \add !(Japeth)\add*',
            [LVToken('and',1), LVToken('Yāfet',1,names=frozenset({'yafet'}))]), [('Japeth',1)])

    def test_explicit_repeat_keeps_each_original_source_number(self):
        self.assertEqual(self.links(r'the¦1 father¦2 \add ≡the father\add*',
            [('the',1),('father',2)]), [('the',1),('father',2)])
        self.assertEqual(self.links(r'\add ≡the father\add*', [('the',1),('father',2)]), [])

    def test_number_change_uses_noun_metadata_and_context(self):
        self.assertEqual(self.links(r'\add #gizmos\add*', [LVToken('gizmo',1,noun=True)]), [('gizmos',1)])
        self.assertEqual(self.links(r'\add #gizmos\add*', [LVToken('gizmo',1)]), [])

    def test_excluded_additions_never_participate(self):
        for marker in ('add', '+add'):
            for code in ('', '<', '>'):
                self.assertEqual(self.links(f'\\{marker} {code}father\\{marker}*', [('father',1)]), [])

    def test_reordered_function_word_cannot_borrow_distant_source(self):
        self.assertEqual(self.links('walking¦3 power¦1 or¦2 closeness to',
            [('power',1),('or',2),('to',3),('be',3),('walking',3)]), [])

    def test_conjugated_subject_can_share_a_source_across_a_clause_adverb(self):
        def score(rv, lv):
            if rv.casefold() == lv.casefold():
                return 'same word', 100
            if (rv,lv) == ('carefully','cautiously'):
                return 'directional word mapping', 55
        result = select_links(tokenize(r'\add @Ruth\add* carefully walked'),
            [LVToken('cautiously',2),LVToken('she',1),LVToken('walked',1)],
            score, str.casefold, lambda word:set())
        self.assertEqual([(t.text,n) for t,n,_ in result], [('Ruth',1),('carefully',2),('walked',1)])

    def test_clause_swap_bootstraps_from_unique_content_words(self):
        self.assertEqual(dict(self.links('bread fish water',
            [('water',1),('bread',2),('fish',3)], reversed_clauses=True)),
            {'bread':2,'fish':3,'water':1})

    def test_running_selection_again_is_idempotent(self):
        rv = 'earth and ground'
        columns = [LVToken('earth',1),LVToken('and',2),LVToken('soil',3)]
        proposals = select_links(tokenize(rv), columns, connect.scoreAlignedWords,
                                 connect.simplifyRVLVWord, connect.numberVariants)
        for token, number, _ in sorted(proposals, key=lambda p:p[0].start, reverse=True):
            rv = rv[:token.end] + f'¦{number}' + rv[token.end:]
        self.assertEqual(self.links(rv, columns), [])

    def test_content_anchors_precede_function_word_decisions_in_real_passages(self):
        fixtures = json.loads(Path(__file__).with_name('selection_passages.json').read_text())
        for verse in fixtures:
            with self.subTest(book=verse['book'], chapter=verse['chapter'], verse=verse['verse']):
                columns = [LVToken(w.split('¦')[0], connect.getLVWordNumber(w))
                           for w in connect.normaliseLVVerseText(verse['lv']).split()
                           if connect.getLVWordNumber(w) is not None]
                columns = connect.with_clause_boundaries(columns, verse['lv'])
                links = self.links(verse['rv'], columns, reversed_clauses=verse['rv'].startswith('⇔'))
                if verse['book'] == 'RUT':
                    self.assertIn(('I',125033), links)  # "I am next after you"
                    self.assertNotIn(('I',125027), links)  # "so that I may know"
                elif verse['chapter'] == 13:
                    self.assertIn(('are',33740), links)  # "you are given"
                    self.assertNotIn(('are',33753), links)  # later "you are not"
                else:
                    self.assertIn(('was',34405), links)  # "it was sold"
                    self.assertNotIn(('was',34398), links)  # "was able"


if __name__ == '__main__':
    unittest.main()
