# SPDX-License-Identifier: MPL-2.0
"""2026-10-22: conservative associations between the OET pipeline's Greek tables.

BOS owns passage conversion. These functions align native table occurrences;
they never change references, word IDs, or row order. Repeated words need
agreement across every optimal sequence alignment, not nearby word numbers.
"""
from collections import defaultdict
from functools import lru_cache
import logging
import re
import unicodedata

from word_sequence_alignment import certain_matches

from BibleOrgSys.Reference.BibleVersificationMappings import get_default_mapping_engine, MappingStatus

WORD_REF = re.compile(r'([A-Z0-9]{3})_(\d+):(\d+)w\d+$')
STRESS = frozenset(('\u0300', '\u0301', '\u0342'))
# Reviewed source spelling variants, not general edit-distance permissions.
SPELLING_PAIRS = (('Ἰωσίαν', 'Ἰωσείαν'), ('Ἰωσίας', 'Ἰωσείας'),
                  ('παρέλαβε', 'παρέλαβεν'), ('λείαν', 'λίαν'))


@lru_cache(maxsize=32768)
def canonical_greek(word):
    return unicodedata.normalize('NFC', word).lower()


@lru_cache(maxsize=32768)
def normalise_greek(word):
    """Ignore stress/case/elision typography; keep breathing and iota subscript."""
    return ''.join(c for c in unicodedata.normalize('NFD', word.lower()) if c not in STRESS
                   ).replace('ς', 'σ').replace('’', "'").replace('ʼ', "'").rstrip("'")


NORMALISED_SPELLING_PAIRS = frozenset(frozenset((normalise_greek(x), normalise_greek(y)))
                                     for x, y in SPELLING_PAIRS)

def words_match(first, second, loose=True):
    if canonical_greek(first) == canonical_greek(second):
        return bool(first)
    if not loose:
        return False
    a, b = normalise_greek(first), normalise_greek(second)
    return bool(a and b) and (a == b or frozenset((a, b)) in NORMALISED_SPELLING_PAIRS)



def lexical_score(source, target):
    word1, word2 = source.get('Word', source.get('GreekWord', '')), target.get('Word', target.get('GreekWord', ''))
    lemma1, lemma2 = source.get('Lemma', source.get('GreekLemma', '')), target.get('Lemma', target.get('GreekLemma', ''))
    same_lemma = bool(lemma1 and lemma2 and words_match(lemma1, lemma2))
    if lemma1 and lemma2 and not same_lemma:
        return None
    if canonical_greek(word1) == canonical_greek(word2) and word1:
        return 100
    # A weakened spelling needs independent lexical evidence. No prefix guesses.
    if same_lemma and words_match(word1, word2):
        return 90
    return None


def mapped_word_matches(source_rows, target_rows, source_system, target_system,
                        source_ref='FGRef', target_ref='Ref'):
    """Map complete passages and return original row indexes for certain pairs.

    Absent target verses can be textual omissions; report and leave those
    passages unresolved. Unsupported mappings and duplicate IDs are errors.
    Combined source groups are aligned once, including when target storage
    covers several source verses. Native word-number suffixes are never mapped.
    """
    def index(rows, field, system):
        verses, words = defaultdict(list), set()
        for i, row in enumerate(rows):
            word_ref = row[field]
            match = WORD_REF.fullmatch(word_ref)
            if not match or word_ref in words:
                raise ValueError(f'{system}: invalid or duplicate word reference {word_ref!r}')
            words.add(word_ref)
            verses[(*match.groups(), None)].append(i)
        return verses
    source = index(source_rows, source_ref, source_system)
    target = index(target_rows, target_ref, target_system)
    engine = get_default_mapping_engine()
    result, seen, claimed = {}, set(), set()
    for ref in source:
        mapping = engine.convert_passage(source_system, target_system, (ref,))
        if mapping.status != MappingStatus.EXACT:
            raise ValueError(f'Greek word alignment {source_system} -> {target_system} '
                             f'at {ref}: {mapping.status.value}; {mapping.diagnostics}')
        source_refs = mapping.source_references or (ref,)
        group = frozenset(source_refs)
        if group in seen:
            continue
        seen.add(group)
        if any(r not in source for r in source_refs) or any(r not in target for r in mapping.references):
            logging.warning('Greek word alignment %s -> %s: missing passage words for %s -> %s',
                            source_system, target_system, source_refs, mapping.references)
            continue
        si = [i for r in source_refs for i in source[r]]
        ti = [i for r in mapping.references for i in target[r]]
        matrix = [[lexical_score(source_rows[i], target_rows[j]) for j in ti] for i in si]
        for i, j in certain_matches(matrix).items():
            if ti[j] in claimed:
                raise ValueError(f'Greek word alignment: target {target_rows[ti[j]][target_ref]} claimed by different passages')
            result[si[i]] = ti[j]
            claimed.add(ti[j])
    return result
