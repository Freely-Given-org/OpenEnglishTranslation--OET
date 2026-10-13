"""Run with: python -m unittest discover -s scripts/tests -v"""
import itertools
from pathlib import Path
import random
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'connect_OET-RV_words_via_OET-LV'))
from oet_alignment import (LVToken, certain_alignment, certain_span_alignment, index_book_lines,
                           propose_links, tokenize, with_clause_boundaries)


def score(a, b):
    return ('exact', 100) if a.casefold() == b.casefold() else None


def links(text, lv, reverse=False):
    return [(t.text, number) for t, number, _ in propose_links(
        tokenize(text), [LVToken(w, n, w[:1].isupper()) for w, n in lv],
        score, str.casefold, reverse)]


def phrase_links(rv, lv, lexical_score=score):
    columns = [LVToken(t.text, t.number) for t in tokenize(lv) if t.number is not None]
    return [(t.text, number) for t, number, reason in propose_links(
        tokenize(rv), with_clause_boundaries(columns, lv), lexical_score, str.casefold)
        if reason == 'local phrase movement']


class PhraseAlignmentTests(unittest.TestCase):
    def test_span_ambiguity_against_exhaustive_paths(self):
        rng = random.Random(420)
        for _ in range(80):
            n, m = rng.randint(1, 4), rng.randint(2, 4)
            matrix = [[rng.choice((None, 1, 2)) for _ in range(m)] for _ in range(n)]
            numbers = [1]*m # Shared ID allows multi-column glosses.
            i, j = rng.randrange(n), rng.randrange(m-1)
            phrases = [(i, min(i+2,n), j, j+2, rng.randint(1, 4))]
            paths = []

            def visit(i, j, value, pairs):
                if i == n and j == m:
                    paths.append((value, pairs))
                    return
                if i < n: visit(i+1,j,value,pairs)
                if j < m: visit(i,j+1,value,pairs)
                if i < n and j < m and matrix[i][j] is not None:
                    visit(i+1,j+1,value+matrix[i][j],pairs | {i:numbers[j]})
                for start, end, col, stop, score_value in phrases:
                    if (start,col) == (i,j):
                        visit(end,stop,value+score_value,pairs | {r:numbers[j] for r in range(i,end)})

            visit(0,0,0,{})
            best = max(v for v,_ in paths)
            optimal = [p for v,p in paths if v == best]
            expected = {r:optimal[0][r] for r in range(n)
                        if all(r in p and p[r] == optimal[0].get(r) for p in optimal)}
            actual = {r:num for r,(num,_) in certain_span_alignment(matrix,numbers,phrases).items()}
            self.assertEqual(actual,expected)

    def test_consumes_whole_lv_phrase(self):
        # 'his' takes both columns, so a later 'him' cannot reuse the second.
        self.assertEqual(certain_span_alignment([[None,None],[None,100]], [7,7],
                                               [(0,1,0,2,110)]), {0:(7,frozenset((0,1)))})


class LocalContextTests(unittest.TestCase):
    def test_article_follows_its_linked_noun_across_a_phrase_movement(self):
        self.assertEqual(links('start¦1 after¦4 dinner¦5 the king¦3 end¦6',
            [('start',1),('the',2),('king',3),('after',4),('dinner',5),('end',6)]), [('the',2)])

    def test_possessive_reorders_within_one_source_gloss(self):
        self.assertEqual(links('start¦1 my father¦2 end¦3',
            [('start',1),('father',2),('of',2),('my',2),('end',3)]), [('my',2)])

    def test_no_context_links_through_punctuation_or_excluded_spans(self):
        lv = [('start',1),('the',2),('king',3),('after',4),('dinner',5),('end',6)]
        for rv in ('start¦1 after¦4 dinner¦5 the. king¦3 end¦6',
                   r'start¦1 after¦4 dinner¦5 \add >the\add* king¦3 end¦6',
                   r'start¦1 after¦4 dinner¦5 the \add @king¦3\add* end¦6'):
            with self.subTest(rv=rv):
                self.assertEqual(links(rv, lv), [])

    def test_context_does_not_reuse_an_occupied_gloss(self):
        self.assertEqual(links('start¦1 the¦2 after¦4 dinner¦5 the king¦3 end¦6',
            [('start',1),('the',2),('king',3),('after',4),('dinner',5),('end',6)]), [])

    def test_context_needs_an_exact_content_word(self):
        self.assertEqual(links('start¦1 after¦4 dinner¦5 the ruler¦3 end¦6',
            [('start',1),('the',2),('king',3),('after',4),('dinner',5),('end',6)]), [])


class PhraseMovementTests(unittest.TestCase):
    def test_phrase_moves_before_linked_block(self):
        self.assertEqual(phrase_links(
            'start¦1 bright lamps after¦2 dinner¦3 end¦6',
            'start¦1 after¦2 dinner¦3 bright¦4 lamps¦5 end¦6'),
            [('bright', 4), ('lamps', 5)])

    def test_phrase_moves_after_linked_block(self):
        self.assertEqual(phrase_links(
            'start¦1 after¦4 dinner¦5 bright lamps end¦6',
            'start¦1 bright¦2 lamps¦3 after¦4 dinner¦5 end¦6'),
            [('bright', 2), ('lamps', 3)])

    def test_one_unlinked_word_is_not_enough_evidence_for_a_move(self):
        self.assertEqual(phrase_links(
            'start¦1 bright¦4 lamps after¦2 dinner¦3 end¦6',
            'start¦1 after¦2 dinner¦3 bright¦4 lamps¦5 end¦6'), [])
        # An apparent 'hundred lambs' phrase must not take 'hundred' from the
        # preceding quantity 'rams, a hundred' in noun-before-number LV order.
        self.assertEqual(phrase_links(
            'start¦1 two¦5 hundred lambs¦4 end¦6',
            'start¦1 rams¦2 hundred¦3 lambs¦4 two¦5 end¦6'), [])

    def test_verse_edge_can_bound_movement(self):
        self.assertEqual(phrase_links('bright lamps after¦1 dinner¦2',
                                     'after¦1 dinner¦2 bright¦3 lamps¦4'),
                         [('bright', 3), ('lamps', 4)])

    def test_punctuation_in_either_version_blocks_movement(self):
        for punctuation in ('.', ',', ';', ':', '?', '!', '—', '“'):
            with self.subTest(punctuation=punctuation):
                self.assertEqual(phrase_links(
                    f'start¦1 bright lamps{punctuation} after¦2 dinner¦3 end¦6',
                    'start¦1 after¦2 dinner¦3 bright¦4 lamps¦5 end¦6'), [])
                self.assertEqual(phrase_links(
                    'start¦1 bright lamps after¦2 dinner¦3 end¦6',
                    f'start¦1 after¦2 dinner¦3{punctuation} bright¦4 lamps¦5 end¦6'), [])

    def test_competing_lv_phrases_are_not_resolved_by_distance(self):
        self.assertEqual(phrase_links(
            'start¦1 bright lamps after¦2 dinner¦3 end¦8',
            'start¦1 after¦2 dinner¦3 bright¦4 lamps¦5 bright¦6 lamps¦7 end¦8'), [])

    def test_competing_rv_phrases_cannot_claim_the_same_source(self):
        self.assertEqual(phrase_links(
            'start¦1 bright lamps bright lamps after¦2 dinner¦3 end¦6',
            'start¦1 after¦2 dinner¦3 bright¦4 lamps¦5 end¦6'), [])

    def test_source_owned_by_another_occurrence_is_not_reused(self):
        self.assertEqual(phrase_links(
            'start¦1 bright lamps after¦2 dinner¦3 bright¦4 lamps¦5 end¦6',
            'start¦1 after¦2 dinner¦3 bright¦4 lamps¦5 end¦6'), [])

    def test_foreign_and_conflicting_anchors_block_movement(self):
        lv = 'start¦1 after¦2 dinner¦3 bright¦4 lamps¦5 end¦6'
        for rv in ('start¦99 bright lamps after¦2 dinner¦3 end¦6',
                   'start¦1 bright lamps after¦99 dinner¦3 end¦6',
                   'start¦1 bright lamps dinner¦3 after¦2 end¦6'):
            self.assertEqual(phrase_links(rv, lv), [])

    def test_added_words_are_not_moved_or_crossed(self):
        lv = 'start¦1 after¦2 dinner¦3 bright¦4 lamps¦5 end¦6'
        for rv in (r'start¦1 \add bright lamps\add* after¦2 dinner¦3 end¦6',
                   r'start¦1 \add @bright lamps\add* after¦2 dinner¦3 end¦6',
                   r'start¦1 bright lamps \add after¦2 dinner¦3\add* end¦6'):
            self.assertEqual(phrase_links(rv, lv), [])

    def test_large_movements_are_rejected(self):
        self.assertEqual(phrase_links(
            'start¦1 bright lamps after¦2 one¦3 two¦4 three¦5 four¦6 five¦7 six¦8 end¦11',
            'start¦1 after¦2 one¦3 two¦4 three¦5 four¦6 five¦7 six¦8 bright¦9 lamps¦10 end¦11'), [])

    def test_weak_matches_and_function_words_are_insufficient(self):
        self.assertEqual(phrase_links(
            'start¦1 bright lamps after¦2 dinner¦3 end¦6',
            'start¦1 after¦2 dinner¦3 brightly¦4 lamplight¦5 end¦6',
            lambda a, b: ('weak prefix', 70) if a[:4] == b[:4] else None), [])
        self.assertEqual(phrase_links(
            'start¦1 the woman after¦2 dinner¦3 end¦6',
            'start¦1 after¦2 dinner¦3 the¦4 woman¦5 end¦6'), [])
        self.assertEqual(phrase_links(
            'start¦1 bright lamps after¦2 dinner¦3 end¦6',
            'start¦1 after¦2 dinner¦3 bright¦4 lamps¦4 end¦6'), [])

    def test_punctuation_metadata_ignores_notes_and_uncertainty_codes(self):
        tokens = tokenize(r'bright \f + \ft A note.\f* \add ?@Ruth\add* lamps.')
        self.assertFalse(any(t.boundary_before for t in tokens))
        self.assertFalse(any(t.boundary_after for t in tokens[:-1]))
        self.assertTrue(tokens[-1].boundary_after)
        columns = with_clause_boundaries([LVToken('bright',1), LVToken('lamps',2)],
                                         'bright¦1 lamps¦2. bright¦1')
        self.assertTrue(columns[0].boundary_before and columns[0].boundary_after)


class AlignmentTests(unittest.TestCase):
    def test_repeated_words_have_positions(self):
        self.assertEqual(links('the son¦2 and the father¦5',
                              [('the',1),('son',2),('and',3),('the',4),('father',5)]),
                         [('the',1),('and',3),('the',4)])

    def test_ambiguous_occurrence_is_left_unlinked(self):
        self.assertEqual(links('her', [('her',1),('her',2)]), [])
        self.assertEqual(links('her her', [('her',1)]), [])

    def test_same_number_alternatives_are_not_ambiguous(self):
        self.assertEqual(links('her', [('her',1),('her',1)]), [('her',1)])
        self.assertEqual(links('because for', [('because/for',1)]), [])

    def test_multiple_gloss_words_can_share_number(self):
        self.assertEqual(links('put around', [('put',2),('around',2)]), [('put',2),('around',2)])

    def test_referent_span_and_pronoun_alternatives(self):
        self.assertEqual(links(r'\add @Ruth\add* went¦3',
                              [('she/it',2),('went',3)]), [('Ruth',2)])
        self.assertEqual(links(r'\wj \+add ?@the women\+add* went¦3\wj*',
                              [('they',2),('went',3)]), [('the',2),('women',2)])

    def test_referent_uses_local_anchors_not_first_pronoun(self):
        self.assertEqual(links(r'he¦1 said¦2 \add @Ruth\add* went¦4',
                              [('he',1),('said',2),('she',3),('went',4)]), [('Ruth',3)])
        self.assertEqual(links(r'\add @Ruth\add*', [('he',1),('she',2)]), [])

    def test_semantic_codes(self):
        self.assertEqual(links(r'\add *she\add* went¦2', [('Ruth',1),('went',2)]), [('she',1)])
        self.assertEqual(links(r'\add &his\add* hand¦2', [('the',1),('hand',2)]), [('his',1)])
        self.assertEqual(links(r'\add %he\add* went¦2', [('I',1),('went',2)]), [('he',1)])

    def test_partial_span_and_conflict(self):
        self.assertEqual(links(r'\add @the¦1 women\add*', [('they',1)]), [('women',1)])
        self.assertEqual(links(r'\add @the¦1 women¦2 workers\add*', [('they',1),('them',2)]), [])

    def test_plain_add_and_uncertain_plain_add_are_excluded(self):
        for marker in ('', '?', '+', '=', '<', '>', '^'):
            self.assertEqual(links(r'\add '+marker+r'her\add*', [('her',1)]), [])

    def test_notes_and_character_markers_preserve_offsets(self):
        text = r'\wj she \f + \ft she\f* \+add ?@Ruth\+add* said¦2\wj*'
        tokens = tokenize(text, line=7, offset=10)
        self.assertEqual([t.text for t in tokens], ['she','Ruth','said'])
        self.assertEqual([text[t.start-10:t.end-10] for t in tokens], ['she','Ruth','said'])
        self.assertEqual(tokens[-1].number, 2)
        self.assertEqual(tokens[1].code, '@')

    def test_contractions_and_hyphens(self):
        self.assertEqual([t.text for t in tokenize("he's empty-handed Beyt-Lehem")],
                         ["he's", 'empty-handed', 'Beyt', 'Lehem'])
        tokens = tokenize('Beyt¦123-El¦124')
        self.assertEqual([(t.text, t.number) for t in tokens], [('Beyt',123),('El',124)])

    def test_context_additions_never_link_or_constrain_surrounding_words(self):
        for marker in ('add', '+add'):
            for code in ('<', '>', '?<', '?>'):
                with self.subTest(marker=marker, code=code):
                    span = f'\\{marker} {code}person\\{marker}*'
                    self.assertEqual(links('one¦2 ' + span, [('one',2),('person',3)]), [])
                    self.assertEqual(links('one ' + span, [('one',2)]), [('one',2)])
                    # Even a stale out-of-verse number in an excluded span is
                    # ignored; the cleanup will remove it when processing a book.
                    self.assertEqual(links('one ' + span.replace('person', 'person¦999') + ' went',
                                           [('one',2),('went',3)]), [('one',2),('went',3)])

    def test_anchor_gloss_is_not_reused_in_the_next_gap(self):
        self.assertEqual(links('her¦1 mother¦1 her', [('her',1),('mother',1)]), [])

    def test_reordered_anchor_gloss_is_not_reused_in_another_gap(self):
        self.assertEqual(links('start¦1 the lamp¦4 after¦2 the¦3 end¦5',
                              [('start',1),('after',2),('the',3),('lamp',4),('end',5)]), [])
        # Reserving one gloss must still leave other glosses with the same ID.
        self.assertEqual(links('put¦2 around end¦3',
                              [('put',2),('around',2),('end',3)]), [('around',2)])

    def test_independent_gaps_cannot_claim_the_same_lv_gloss(self):
        self.assertEqual(links('start¦1 bright lamp¦4 after¦2 bright second¦3 end¦5',
                              [('start',1),('after',2),('bright',3),('second',3),('lamp',4),('end',5)]), [])
        # Different columns with a shared source ID can still match two words
        # in the same gap, without being mistaken for a duplicated claim.
        self.assertEqual(links('her her', [('her',1),('her',1)]), [('her',1),('her',1)])

    def test_named_referent_does_not_take_plural_subject(self):
        self.assertEqual(links(r'\add @Yairos\add* house¦2', [('they',1),('house',2)]), [])

    def test_semantic_span_cannot_borrow_from_a_reordered_occupied_clause(self):
        self.assertEqual(links(r'know¦5 mysteries¦7 said¦3 \add @Yeshua\add* but¦9',
            [('he',1),('said',3),('it',4),('given',4),('know',5),('the',6),('mysteries',7),('but',9)]), [])
        self.assertEqual(links(r'said¦2 \add @Baruk\add* I¦4 built¦3',
            [('him',1),('said',2),('I',3),('built',3),('I',4)]), [])

    def test_owner_cannot_reuse_an_article_from_the_preceding_name(self):
        self.assertEqual(links(r'Salonika¦1 \add &his\add* grace¦2',
            [('of',1),('the',1),('ones',1),('from',1),('Thessalonica',1),('grace',2)]), [])

    def test_singular_common_referent_does_not_take_plural_pronoun(self):
        self.assertEqual(links(r'enter¦1 \add @the land\add* and¦3',
            [('enter',1),('they',2),('and',3)]), [])

    def test_capitalised_plural_referents_are_not_singular_names(self):
        for group in ('Israelis', 'Jews', 'Levites', 'Egyptians', 'Philistines', 'Babylonians'):
            self.assertEqual(links(r'\add @' + group + r'\add* left¦3',
                [('I',1),('them',2),('left',3)]), [(group,2)])
            self.assertEqual(links(r'\add @' + group + r'\add* left¦3',
                [('he',1),('left',3)]), [])
        for name in ('Barnabas', 'Silas', 'Lazarus'):
            self.assertEqual(links(r'\add @' + name + r'\add* left¦3',
                [('he',1),('them',2),('left',3)]), [(name,1)])

    def test_lv_text_order_is_not_source_number_order(self):
        self.assertEqual(links('son¦30 and father¦10', [('son',30),('and',20),('father',10)]), [('and',20)])

    def test_crossing_or_foreign_anchors_block_gap(self):
        self.assertEqual(links('father¦3 and son¦1', [('son',1),('and',2),('father',3)]), [])
        self.assertEqual(links('son¦99 and father¦3', [('son',1),('and',2),('father',3)]), [])

    def test_clause_swap_preserves_internal_order(self):
        lv=[('as',1),('commanded',2),('the',3),('girls',4),('did',5)]
        self.assertEqual(links('the girls¦4 did¦5 as commanded¦2', lv, True), [('as',1)])
        # Without enough anchors, keep safe local gaps instead of reversing words.
        self.assertEqual(links('girls¦4 did as commanded¦2', lv, True), [])

    def test_chapter_titles_bridges_and_headings(self):
        lines=[r'\ip intro',r'\c 1',r'\d title',r'\v 1 first',r'\q1 more',
               r'\s1 heading',r'\v 2-3 bridge',r'\c 2',r'\d next title',r'\v 1 next',r'\d trailing']
        index=index_book_lines(lines)
        self.assertEqual(index[(1,0)], [(2,3)])
        self.assertEqual(index[(1,1)], [(3,5),(4,4)])
        self.assertEqual(index[(1,2)], [(6,7)])
        self.assertEqual(index[(2,0)], [(8,3)])
        self.assertEqual(index[(2,1)], [(9,5)])
        self.assertNotIn((1,3), index)

    def test_dynamic_program_against_exhaustive_alignments(self):
        rng=random.Random(4821)
        for n,m in itertools.product(range(1,5),repeat=2):
            for _ in range(25):
                matrix=[[rng.choice([None, 2, 3]) for _ in range(m)] for _ in range(n)]
                numbers=[rng.randrange(1,4) for _ in range(m)]
                paths=[]
                def enumerate_paths(i,j,pairs,total):
                    paths.append((total,dict(pairs)))
                    for r in range(i,n):
                        for c in range(j,m):
                            if matrix[r][c] is not None:
                                enumerate_paths(r+1,c+1,pairs+[(r,numbers[c])],total+matrix[r][c])
                enumerate_paths(0,0,[],0)
                best=max(p[0] for p in paths)
                optimal=[p[1] for p in paths if p[0]==best]
                expected={i:optimal[0][i] for i in range(n)
                          if all(i in p and p[i]==optimal[0].get(i) for p in optimal)}
                self.assertEqual(certain_alignment(matrix,numbers), expected)


if __name__ == '__main__':
    unittest.main()
