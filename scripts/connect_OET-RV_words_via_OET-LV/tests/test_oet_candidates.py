"""Selection policy regressions using tiny passages, with no Bible-file writes."""
from itertools import permutations
import json
from pathlib import Path
import re
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

    def test_covenant_loyalty_phrases_complete_compatible_links(self):
        for gloss in ('loyalty', 'loyalties'):
            for phrase in ('loyal commitment', 'loyal kindness'):
                with self.subTest(gloss=gloss, phrase=phrase):
                    columns = [('covenant',7),(gloss,7)]
                    first, last = phrase.split()
                    self.assertEqual(self.links(phrase, columns), [(first,7),(last,7)])
                    self.assertEqual(self.links(f'{first}¦7 {last}', columns), [(last,7)])
        # The gloss order varies with Hebrew possessive suffixes.
        self.assertEqual(self.links('your¦7 loyal¦7 commitment',
                         [('loyalty',7),('of',7),('your',7),('covenant',7)]), [('commitment',7)])
        self.assertEqual(self.links('loyal affection', [('loyalty',7)]), [('loyal',7),('affection',7)])

    def test_covenant_loyalty_phrases_do_not_guess_or_cross_exclusions(self):
        self.assertEqual(self.links('loyal commitment', [('loyalty',7),('loyalty',8)]), [])
        self.assertEqual(self.links('loyal¦8 commitment', [('loyalty',7)]), [])
        self.assertEqual(self.links(r'loyal¦7 \add commitment\add*', [('loyalty',7)]), [])
        self.assertEqual(self.links('commitment', [('loyalty',7)]), [])
        self.assertEqual(self.links('loyal commitment', [('covenant',7)]), [])
        # Distinct literal counterparts retain their own source numbers.
        self.assertEqual(self.links('loyal faithfulness', [('loyalty',7),('faithfulness',8)]),
                         [('loyal',7),('faithfulness',8)])
        # PSA 88:11 already assigns the source to a later phrase; do not reuse it.
        self.assertEqual(self.links('loyal commitment in the grave¦2—your¦3 loyalty¦3',
                         [('grave',2),('loyalty',3),('your',3),('faithfulness',4)]), [])

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

    def test_terminal_possessive_preserves_matching_evidence(self):
        for word,lv in (("houses'",'houses'),("wives'",'wife'),("Yudas'",'Yudas'),
                        ("fishermen'",'fishers')):
            with self.subTest(word=word):
                self.assertEqual(self.links(word, [(lv,7)]), [(word,7)])
        self.assertEqual(connect.simplifyRVLVWord("houses'"), 'houses')
        self.assertEqual(connect.simplifyRVLVWord("Sha'ul"), "sha'ul")
        self.assertEqual(connect.simplifyRVLVWord("don't"), "don't")
        self.assertEqual(self.links(r"\add >houses'\add*", [('houses',7)]), [])
        self.assertEqual(self.links("houses' houses'", [('houses',7),('houses',8)]),
                         [("houses'",7),("houses'",8)])
        self.assertEqual(self.links("houses' houses'", [('houses',7)]), [])

    def test_competing_phrase_is_atomic(self):
        a, b = tokenize('alpha beta')
        phrase = Candidate(((a, 1),(b, 1)), frozenset({0}), 'phrase')
        anchor = Candidate(((b, 2),), frozenset({1}), 'anchor')
        self.assertEqual(select_candidates([phrase], [anchor]), [])

    def test_optional_plural_matches_either_form_without_choosing_between_repeats(self):
        for word, forms in (('daughter(s)', ('daughter','daughters')),
                            ('branch(es)', ('branch','branches'))):
            for lv in forms:
                with self.subTest(word=word,lv=lv):
                    self.assertEqual(self.links(word, [(lv,7)]), [(word,7)])
            self.assertEqual(self.links(word, [(forms[0],7),(forms[1],8)]), [])

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

    def test_reviewed_related_forms_in_complete_mapped_passages(self):
        fixtures = json.loads(Path(__file__).with_name('related_form_passages.json').read_text())
        for passage in fixtures:
            for fresh in (False, True):
                with self.subTest(reference=passage['reference'], fresh=fresh):
                    tokens = [token for n, line in enumerate(passage['rv_lines'])
                              for token in tokenize(re.sub(r'¦\d+', '', line) if fresh else line, n)]
                    columns = [LVToken(**{**col, 'names': frozenset(col['names'])})
                               for col in passage['columns']]
                    selected = dict((t, number) for t, number, _ in select_links(
                        tokens, columns, connect.scoreAlignedWords, connect.simplifyRVLVWord,
                        connect.numberVariants, phrase_index=connect.ALIGNED_PHRASE_INDEX,
                        directional_index=connect.DIRECTIONAL_WORD_INDEX))
                    wanted = {word for word, _ in passage['expected']}
                    expected = passage.get('expected_fresh', passage['expected']) if fresh else passage['expected']
                    self.assertEqual([(t.text, t.number or selected.get(t)) for t in tokens
                                      if t.text in wanted], [tuple(x) for x in expected])
                    self.assertFalse(any(t in selected for t in tokens if not t.linkable))

    def test_related_forms_abstain_on_ambiguous_and_already_claimed_sources(self):
        for rv, lv in (('leprosy', 'lepers'), ('deafness', 'deaf'), ('muteness', 'mute')):
            with self.subTest(rv=rv):
                self.assertEqual(self.links(rv, [(lv, 1), (lv, 2)]), [])
                self.assertEqual(self.links(f'{rv}¦1 {rv}', [(lv, 1)]), [])
                for marker in ('add', '+add'):
                    self.assertEqual(self.links(f'\\{marker} >{rv}\\{marker}*', [(lv, 1)]), [])

    def test_burial_mapping_does_not_steal_an_exact_buried_source(self):
        self.assertEqual(self.links('burial', [('bury', 1)]), [('burial', 1)])
        self.assertEqual(self.links('buried', [('burial', 1), ('buried', 2)]), [('buried', 2)])
        self.assertEqual(connect.scoreAlignedWords('buried', 'burial'), ('reviewed related forms', 50))

    def test_knowledge_family_does_not_chain_through_know(self):
        self.assertIsNotNone(connect.scoreAlignedWords('knowledge', 'known'))
        self.assertIsNotNone(connect.scoreAlignedWords('knowledgable', 'knowledge'))
        self.assertIsNone(connect.scoreAlignedWords('knowledgable', 'known'))

    def test_context_regressions_in_complete_passages(self):
        fixtures = json.loads(Path(__file__).with_name('context_passages.json').read_text())
        expected = {'PRO 14:7': {11:272943}, 'ECC 10:10': {20:281543},
                    'DEU 22:20': {4:92638},
                    'DAN 3:1': {19:357747}, 'EZR 6:3': {32:219339, 41:219344},
                    'JER 22:19': {2:313996}, 'PSA 1:1': {1:243183}}
        forbidden = {'DEU 22:20': {11:92638}, 'ROM 9:18': {9:109415, 10:109415},
                     'DAN 3:1': {15:357745, 18:357745}, 'ECC 7:5': {18:280373},
                     'NUM 19:22': {14:72519}, 'PSA 1:1': {4:243189}, 'JER 21:5': {11:313411}}
        for passage in fixtures:
            for fresh in (False, True):
                with self.subTest(reference=passage['reference'], fresh=fresh):
                    rv = re.sub(r'¦\d+', '', passage['rv']) if fresh else passage['rv']
                    tokens = tokenize(rv)
                    columns = [LVToken(**{**col, 'names': frozenset(col['names'])}) for col in passage['columns']]
                    selected = dict((t, n) for t, n, _ in select_links(tokens, columns,
                        connect.scoreAlignedWords, connect.simplifyRVLVWord, connect.numberVariants,
                        phrase_index=connect.ALIGNED_PHRASE_INDEX, directional_index=connect.DIRECTIONAL_WORD_INDEX))
                    for i, n in expected.get(passage['reference'], {}).items():
                        self.assertEqual(tokens[i].number or selected.get(tokens[i]), n)
                    if fresh and passage['reference'] == 'ROM 9:18':
                        self.assertEqual(selected.get(tokens[6]), 109412)
                    for i, n in forbidden.get(passage['reference'], {}).items():
                        self.assertNotEqual(selected.get(tokens[i]), n)
                    self.assertFalse(any(t in selected for t in tokens if not t.linkable))

    def test_generic_heads_cannot_jump_across_simultaneously_selected_anchors(self):
        for rv in ('wise¦1 \\add >person\\add* sings¦3 foolish¦4 people',
                   'wise \\add >person\\add* sings foolish people'):
            self.assertNotIn(('people',2), self.links(rv,
                [('wise',1),('man',2),('sings',3),('foolish',4)]))

    def test_article_requires_its_own_head(self):
        self.assertNotIn(('the',2), self.links('the benefits advice¦2',
            [('the',2),('counsel',2)]))
        self.assertIn(('the',1), self.links('the wise¦2', [('the',1),('wise',2)]))

    def test_auxiliary_belongs_to_its_following_predicate(self):
        columns = [('blessed',1), ('are',1), ('the',2), ('poor',3)]
        tokens = tokenize('those who are poor¦3 are blessed¦1')
        selected = dict((t, n) for t, n, _ in select_links(tokens,
            [LVToken(*col) for col in columns], connect.scoreAlignedWords,
            connect.simplifyRVLVWord, connect.numberVariants))
        self.assertNotIn(tokens[2], selected)
        self.assertIn(('are',1), self.links('are blessed¦1', columns))
        self.assertIn(('are',2), self.links('are rich¦2', [('being',2),('rich',2)]))

    def test_noun_suffix_cannot_possess_another_noun(self):
        columns = [LVToken('god',1,noun=True), LVToken('of',1,noun=True),
                   LVToken('our',1,noun=True), LVToken('and',2,noun=True),
                   LVToken('ancestors',2,noun=True)]
        self.assertNotIn(('our',1), self.links('our ancestors¦2', columns))
        self.assertIn(('our',1), self.links('our god¦1', columns))

    def test_relative_pronoun_needs_its_own_following_predicate(self):
        columns = [('sick',1),('who',2),('were',3),('healed',3)]
        self.assertNotIn(('who',2), self.links('those who were sick¦1 were healed¦3', columns))
        self.assertIn(('who',2), self.links('who were healed¦3', columns))

    def test_complete_moral_phrase_outweighs_partial_spatial_match(self):
        self.assertEqual(self.links(r"innocent \add >person\add* \add ≈does what's right\add*",
            [('righteousness',1),('blameless',2),('makes',3),('straight',3)]),
            [('innocent',2),('does',1),("what's",1),('right',1)])

    def test_remaining_ambiguities_in_complete_passages(self):
        fixtures = json.loads(Path(__file__).with_name('ambiguity_passages.json').read_text())
        for p in fixtures:
            columns = [LVToken(**{**col, 'names': frozenset(col['names'])}) for col in p['columns']]
            for version in ('before', 'after'):
                for fresh in (False, True):
                    with self.subTest(reference=p['reference'], version=version, fresh=fresh):
                        rv = re.sub(r'¦\d+', '', p[version]) if fresh else p[version]
                        tokens = tokenize(rv)
                        found = {i: t.number for i,t in enumerate(tokens) if t.number is not None}
                        added = {tokens.index(t): n for t,n,_ in select_links(tokens, columns,
                            connect.scoreAlignedWords, connect.simplifyRVLVWord, connect.numberVariants,
                            phrase_index=connect.ALIGNED_PHRASE_INDEX,
                            directional_index=connect.DIRECTIONAL_WORD_INDEX)}
                        found.update(added)
                        if fresh:
                            for i,n in p['forbidden']:
                                self.assertNotEqual(found.get(i), n)
                            for i,n in p['expected_fresh']:
                                self.assertEqual(found.get(i), n)
                        self.assertFalse(any(i in added for i,t in enumerate(tokens) if not t.linkable))

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
