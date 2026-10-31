# SPDX-License-Identifier: MPL-2.0
"""2026-10-22: validate native OSHB identities before transferring Macula data.

Both Hebrew inputs use original versification. Word numbers can differ around
ketiv/qere readings; they are not cross-source identities. Keep vowel points,
morpheme boundaries and morphology when checking a claimed OSHB ID.
"""
from collections import defaultdict
from functools import lru_cache
import logging
import re

from ot_gloss_fallbacks import normalise_hebrew as _normalise_hebrew
from word_sequence_alignment import certain_matches

normalise_hebrew = lru_cache(maxsize=32768)(_normalise_hebrew)

PART_REF = re.compile(r'([A-Z0-9]{3}_\d+:\d+)w\d+([a-z]?)$')


def compatible_morphology(first, second):
    # OSHB distinguishes the article on a preposition where Macula uses R.
    return first == second or (first, second) in (('Rd', 'R'), ('R', 'Rd'))


def same_morpheme(macula, oshb):
    """Check verse, complete pointed spelling and morphology, including ketiv."""
    source, target = PART_REF.fullmatch(macula['FGRef']), PART_REF.fullmatch(oshb['Ref'])
    return bool(source and target and source[1] == target[1]
                and source[2] == target[2]
                and macula['RowType'] == oshb['RowType'].removesuffix('K')
                and normalise_hebrew(macula['WordOrMorpheme']) == normalise_hebrew(oshb['NoCantillations'])
                and compatible_morphology(macula['Morphology'], oshb['Morphology']))


def matched_morphemes(macula_rows, oshb_rows):
    """Return source index -> target index, never reusing an OSHB occurrence.

    Validate nonempty imported IDs instead of silently replacing a bad ID with
    a nearby word. For an absent ID, accept only reciprocal unique matches in
    the same verse, with spelling, morphology and morpheme suffix agreement.
    """
    by_id, candidates = defaultdict(list), defaultdict(list)
    for n, row in enumerate(oshb_rows):
        match = PART_REF.fullmatch(row['Ref'])
        if not match:
            continue
        if row['OSHBid']:
            by_id[row['OSHBid']].append(n)
        candidates[match[1], match[2], normalise_hebrew(row['NoCantillations'])].append(n)
    proposals, claimants = {}, defaultdict(list)
    for n, row in enumerate(macula_rows):
        match = PART_REF.fullmatch(row['FGRef'])
        if not match:
            raise ValueError(f"Macula: invalid native morpheme reference {row['FGRef']!r}")
        indexes = (by_id[row['OSHBid']] if row.get('OSHBid') else
                   candidates[match[1], match[2], normalise_hebrew(row['WordOrMorpheme'])])
        compatible = [i for i in indexes if same_morpheme(row, oshb_rows[i])]
        if len(compatible) == 1:
            proposals[n] = compatible[0]
            claimants[compatible[0]].append(n)
    return {n:i for n,i in proposals.items() if len(claimants[i]) == 1}


def matched_word_groups(macula_rows, oshb_words):
    """Return target row index -> complete Macula word parts with verified IDs.

    Never join w1 to w10, consume the following word's final morpheme, or shift
    the remainder of a verse after a ketiv. Incomplete, conflicting or ambiguous
    groups remain unassigned. No qere morphology is attached to a ketiv.
    """
    groups = defaultdict(list)
    for row in macula_rows:
        match = PART_REF.fullmatch(row['FGRef'])
        if not match:
            raise ValueError(f"Macula: invalid native word reference {row['FGRef']!r}")
        word_ref = row['FGRef'][:-1] if match[2] else row['FGRef']
        groups[word_ref].append(row)
    by_id = defaultdict(list)
    for ref, parts in groups.items():
        suffixes = ''.join(PART_REF.fullmatch(r['FGRef'])[2] for r in parts)
        if not ((len(parts) == 1 and not suffixes and 'w' in parts[0]['RowType'])
                or (len(parts) > 1 and suffixes == 'abcdefghijklmnopqrstuvwxyz'[:len(parts)]
                    and all('m' in r['RowType'] for r in parts[:-1]) and 'M' in parts[-1]['RowType'])):
            logging.warning('Incomplete Macula word group %s; leaving metadata unassigned', ref)
            continue
        # OSHB word IDs have five characters; their morphemes append a..z.
        identifiers = [r['OSHBid'] for r in parts]
        word_id = identifiers[0][:5]
        expected = [word_id+s for s in suffixes] if suffixes else [word_id]
        if len(word_id) == 5 and identifiers == expected:
            by_id[word_id].append(parts)
    matches, claimed = {}, defaultdict(list)
    for n, row in enumerate(oshb_words):
        if not PART_REF.fullmatch(row['Ref']):
            continue  # Notes and separators have no word metadata.
        parts_list = by_id[row['OSHBid']]
        compatible = []
        for parts in parts_list:
            if row['Ref'].split('w')[0] != parts[0]['FGRef'].split('w')[0]:
                continue
            words = row['NoCantillations'].split(',')
            morphology = row['Morphology'].split(',')
            # LemmaRowList must continue to correspond to MorphemeRowList.
            if len(parts) != len(words) or len(parts) != len(morphology) or len(parts) != len(row['MorphemeRowList'].split(',')):
                continue
            if all(normalise_hebrew(p['WordOrMorpheme']) == normalise_hebrew(w)
                   and compatible_morphology(p['Morphology'], m)
                   for p,w,m in zip(parts, words, morphology)):
                compatible.append(parts)
        if len(compatible) == 1:
            matches[n] = compatible[0]
            claimed[compatible[0][0]['FGRef']].append(n)
    return {n:parts for n,parts in matches.items() if len(claimed[parts[0]['FGRef']]) == 1}


def align_morphemes_by_verse(macula_rows, oshb_rows):
    """Assign IDs before import using complete-word sequences in native org verses.

    Unlike an offset search, insertion/deletion alignment cannot drift into the
    next verse. Ketiv spelling/morphology is checked like every other word;
    qere substitutions require a separate explicit note policy.
    """
    def groups(rows, field):
        words = defaultdict(list)
        seen = set()
        for n, row in enumerate(rows):
            match = PART_REF.fullmatch(row[field])
            if not match:
                if field == 'Ref':
                    continue  # OSHB notes and punctuation.
                raise ValueError(f"Macula: invalid native reference {row[field]!r}")
            if row[field] in seen:
                raise ValueError(f"Duplicate native word/morpheme reference {row[field]}")
            seen.add(row[field])
            word_ref = row[field][:-1] if match[2] else row[field]
            words[word_ref].append(n)
        verses = defaultdict(list)
        for ref, indexes in words.items():
            suffixes = ''.join(PART_REF.fullmatch(rows[n][field])[2] for n in indexes)
            if ((len(indexes) == 1 and not suffixes and 'w' in rows[indexes[0]]['RowType'])
                    or (len(indexes) > 1 and suffixes == 'abcdefghijklmnopqrstuvwxyz'[:len(indexes)]
                        and all('m' in rows[n]['RowType'] for n in indexes[:-1])
                        and 'M' in rows[indexes[-1]]['RowType'])):
                verses[ref.split('w')[0]].append(indexes)
        return verses
    source, target = groups(macula_rows, 'FGRef'), groups(oshb_rows, 'Ref')
    matches = {}
    for verse, source_groups in source.items():
        target_groups = target.get(verse, [])
        matrix = [[1 if len(sg) == len(tg) and all(same_morpheme(macula_rows[s], oshb_rows[t])
                         for s,t in zip(sg,tg)) else None for tg in target_groups] for sg in source_groups]
        for s,t in certain_matches(matrix).items():
            matches.update(zip(source_groups[s],target_groups[t]))
    return matches
