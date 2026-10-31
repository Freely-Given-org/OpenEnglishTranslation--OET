# SPDX-License-Identifier: MPL-2.0
"""Reorder complete Macula subject phrases through verified OSHB identities.

Nesting contains rule paths, not unique tree IDs. Match adjacent constituents
of the same clause, within one verse; never collect all rows with a shared
path. Keep complete Hebrew words together, including articles and suffixes.
Only GlossOrder, sentence capitalisation (S), and GlossInsert are changed.
"""
from collections import Counter
from itertools import groupby

from hebrew_word_alignment import PART_REF, matched_morphemes


def _word_ref(row):
    ref = row['FGRef']
    match = PART_REF.fullmatch(ref)
    return ref[:-1] if match and match[2] else ref


def _word_spans(rows):
    """Index complete words; incomplete morpheme groups cannot be moved."""
    spans = {}
    for _, items in groupby(enumerate(rows), lambda item: _word_ref(item[1])):
        group = list(items)
        parts = [r for _, r in group]
        suffixes = ''.join(PART_REF.fullmatch(r['FGRef'])[2] for r in parts)
        if ((len(parts) == 1 and not suffixes and 'w' in parts[0]['RowType'])
                or (len(parts) > 1 and suffixes == 'abcdefghijklmnopqrstuvwxyz'[:len(parts)]
                    and all('m' in r['RowType'] for r in parts[:-1])
                    and 'M' in parts[-1]['RowType'])):
            span = (group[0][0], group[-1][0] + 1)
            spans.update((i, span) for i, _ in group)
    return spans


def reorder_subject_phrases(oshb_rows, macula_rows):
    """Mutate gloss metadata in place and return counts by VS/VOS pattern.

    Use Np2S at the predicate's clause depth, so construct chains, determiners,
    appositions, coordinated nouns and embedded modifiers travel as a unit.
    Leave missing/ambiguous alignments, partial words, copulas, existing manual
    orders/inserts and non-adjacent clause constituents alone.

    For a prefixed verb, subjects sort before the whole verb word and each subject
    word gets GlossInsert='_'. The ESFM exporter places that buffered phrase
    between the verb's prefix and stem, preserving e.g. 'And ... he_said'.
    """
    matches = matched_morphemes(macula_rows, oshb_rows)
    spans = _word_spans(macula_rows)
    counts = Counter()
    for v, verb in enumerate(macula_rows):
        path = tuple(verb['Nesting'].split('/'))
        if (verb['PartOfSpeech'] != 'v' or len(path) < 3
                or path[-2:] != ('Vp2V', 'V2VP')
                or verb['EnglishGloss'] in ('be', 'was', 'there_was')):
            continue
        roles = path[-3].split('=')[-1].split('-')
        if roles.count('V') != 1:
            continue
        following = roles[roles.index('V') + 1:]
        if following[:1] == ['S']:
            pattern = 'VS'
        elif following[:2] == ['O', 'S']:
            pattern = 'VOS'
        else:
            continue
        if v not in spans or spans[v][1] != v + 1:
            continue  # A verb with a suffix is not a simple V2VP word.
        start, _ = spans[v]
        # The supported insertion point is immediately before the verb stem.
        if v - start > 2:
            continue
        clause = path[:-2]
        verse = verb['FGRef'].split('w')[0]

        def end_of_phrase(begin, rule):
            prefix = clause + (rule,)
            end = begin
            while end < len(macula_rows):
                row = macula_rows[end]
                if tuple(row['Nesting'].split('/'))[:len(prefix)] != prefix:
                    break
                if row['FGRef'].split('w')[0] != verse:
                    # Do not move a truncated phrase across a verse boundary.
                    return None
                end += 1
            if (end == begin or begin not in spans or end - 1 not in spans
                    or spans[begin][0] != begin or spans[end - 1][1] != end):
                return None
            return end

        subject_start = v + 1
        if pattern == 'VOS':
            subject_start = end_of_phrase(subject_start, 'Np2O')
            if subject_start is None:
                continue
        end = end_of_phrase(subject_start, 'Np2S')
        if end is None or any(i not in matches or i not in spans for i in range(start, end)):
            continue
        target_indexes = [matches[i] for i in range(start, end)]
        if target_indexes != sorted(target_indexes):
            continue
        # Maqqef separators have no English output. Other gaps (including
        # unmatched ketiv/qere words and notes) make the proposed move unsafe.
        selected = set(target_indexes)
        if any(i not in selected and not (oshb_rows[i]['RowType'] == 'seg'
                   and oshb_rows[i]['Morphology'] == 'x-maqqef'
                   and not oshb_rows[i]['GlossPunctuation'])
               for i in range(target_indexes[0], target_indexes[-1] + 1)):
            continue
        rows = [oshb_rows[i] for i in target_indexes]
        if any(r['Ref'].split('w')[0] != verse for r in rows):
            continue
        if any(not (r['ContextualMorphemeGloss'] or r['MorphemeGloss']).strip(' ,_=?~')
               for r in rows[:v - start]):
            # E.g. an interrogative prefix glossed only '?' disappears during
            # export, leaving no visible morpheme boundary for an insertion.
            continue
        orders = [r['GlossOrder'] for r in rows]
        numbers = [int(order) for order in orders]
        if (numbers != sorted(set(numbers)) or any(r['GlossInsert'] for r in rows)
                or any('S' in r['GlossCapitalisation'] for r in rows[v - start + 1:])):
            continue
        subjects = [oshb_rows[matches[i]] for i in range(subject_start, end)]
        before_subject = [oshb_rows[matches[i]] for i in range(start, subject_start)]
        for row, order in zip(subjects + before_subject, orders):
            row['GlossOrder'] = order
        if start < v:
            for i in range(subject_start, end):
                if spans[i][0] == i:
                    oshb_rows[matches[i]]['GlossInsert'] = '_'
        else:
            # S belongs to the sentence position; other flags and intrinsic
            # capitals (God, Bāⱱel, I, etc.) belong to their original word.
            first = before_subject[0]
            if 'S' in first['GlossCapitalisation']:
                first['GlossCapitalisation'] = first['GlossCapitalisation'].replace('S', '')
                subjects[0]['GlossCapitalisation'] += 'S'
        counts[pattern] += 1
        if len({_word_ref(macula_rows[i]) for i in range(subject_start, end)}) > 1:
            counts['multiword_subjects'] += 1
    return counts
