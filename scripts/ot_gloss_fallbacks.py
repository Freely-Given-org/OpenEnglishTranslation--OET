# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2026 Robert Hunt
"""Conservative English-gloss fallbacks shared by OT import and export.

Keep missing/technical glosses visible unless the source supplies an alternative.
Qere fallbacks require an explicit OSHB note and a unique word in the same verse;
Macula word numbers cannot be used because ketiv/qere segmentation changes them.
"""
from collections import defaultdict
import logging
import re
import unicodedata


GLOSS_FIELDS = ('ContextualWordGloss', 'WordGloss', 'ContextualMorphemeGlosses',
                'MorphemeGlosses', 'ContextualMorphemeGloss', 'MorphemeGloss')
WORD_REF = re.compile(r'(.+)w\d+$')
MACULA_WORD_REF = re.compile(r'(.+w\d+)([a-e]?)$')
QERE_NOTE = re.compile(r"^([^: ]+): \(x-qere\) '([^' ]+)'")


def usable_gloss(gloss: str) -> bool:
    """Grammatical labels and exporter placeholders are not English glosses."""
    return bool(gloss.strip(' ,_=?~')) and '(cmp)' not in gloss and 'wwww' not in gloss.lower()


def select_gloss(row: dict) -> tuple[str, str]:
    """Retain export priorities, but try English alternatives before a label.

    Repair an affected contextual morpheme from its aligned ordinary gloss,
    preserving the other contextual morphemes. Never drop an unglossed part.
    """
    cwg, wg = row['ContextualWordGloss'], row['WordGloss']
    cmg, mg = row['ContextualMorphemeGlosses'], row['MorphemeGlosses']
    if ',' in str(row['MorphemeRowList']):
        candidates = [('CWG', cwg), ('WG', wg), ('CMG', cmg), ('MG', mg)]
    else:
        candidates = ([('CWG', cwg), ('WG', wg)] if not cwg or not cwg[-1].isdigit()
                      else [('WG', wg), ('CWG', cwg)])
        candidates += [('CMG', cmg), ('MG', mg)]

    for src, gloss in candidates:
        if src == 'CMG' and not usable_gloss(gloss):
            contextual, ordinary = gloss.split(','), mg.split(',')
            if len(contextual) == len(ordinary):
                repaired = ','.join(c if usable_gloss(c) else g
                                    for c, g in zip(contextual, ordinary))
                if all(usable_gloss(part) for part in repaired.split(',')):
                    return src, repaired
        if usable_gloss(gloss):
            return src, gloss
    # Preserve evidence of missing data when there is no usable alternative.
    return next(((src, gloss) for src, gloss in candidates if gloss), ('WG', ''))


def normalise_hebrew(text: str, *, consonants: bool = False) -> str:
    """Ignore accents and morpheme separators; normally keep vowel points."""
    return ''.join(c for c in unicodedata.normalize('NFD', text)
                   if c not in ',/־\u05bd' and not '\u0591' <= c <= '\u05af'
                   and (not consonants or '\u05d0' <= c <= '\u05ea'))


def fix_known_gloss_duplication(row: dict) -> None:
    """Macula's leannoth already includes the לְ prefix (Psalm 88:1).

    Its contextual gloss is attached to the prefix, while its ordinary gloss
    is attached to the following morpheme. Combining them duplicates the word.
    This specific source correction must not collapse genuine repeated words.
    """
    if (not row['ContextualWordGloss'] and not row['WordGloss']
            and row['ContextualMorphemeGlosses'] == 'leannoth,leannoth'
            and row['NoCantillations'] == 'לְ,עַנּוֹת'):
        row['ContextualWordGloss'] = 'leannoth'


def recover_missing_word_glosses(rows: list[dict], macula_rows) -> int:
    """Fill empty single-word glosses from uniquely matched Macula words.

    Accept either the importer morpheme table or the exporter word table.
    Existing glosses, Hebrew, IDs, ordering, and variant notes are untouched.
    Multiword variants and ambiguous matches need manual review.
    """
    missing = {}
    qere_words = {}
    previous_word = None
    for row in rows:
        match = WORD_REF.fullmatch(row['Ref'])
        if match:
            previous_word = row
            if (',' not in str(row.get('MorphemeRowList', ''))
                    and not any(usable_gloss(row.get(field, '')) for field in GLOSS_FIELDS)):
                missing[row['Ref']] = row
        elif row['RowType'] == 'variant note' and previous_word is not None:
            note = row.get('Word', row.get('WordOrMorpheme', ''))
            match = QERE_NOTE.match(note)
            if (match and previous_word['Ref'].split('w')[0] == row['Ref']
                    and 'K' in previous_word['RowType']
                    and normalise_hebrew(match[1], consonants=True)
                        == normalise_hebrew(previous_word['NoCantillations'], consonants=True)):
                qere_words[previous_word['Ref']] = match[2]
        elif row['RowType'] != 'seg':
            previous_word = None
    if not missing:
        return 0

    verses = {ref.split('w')[0] for ref in missing}
    groups = defaultdict(list)
    for row in macula_rows:
        match = MACULA_WORD_REF.fullmatch(row['FGRef'])
        if match and match[1].split('w')[0] in verses:
            groups[match[1]].append((match[2], row))

    candidates = defaultdict(list)
    for ref, group in groups.items():
        # A complete word is one unsuffixed row, or consecutive a...final M rows.
        letters = ''.join(letter for letter, _ in group)
        if not ((len(group) == 1 and not letters)
                or (len(group) > 1 and letters == 'abcde'[:len(group)]
                    and 'M' in group[-1][1]['RowType'])):
            continue
        parts = [part for _, part in group]
        hebrew = normalise_hebrew(''.join(part['WordOrMorpheme'] for part in parts))
        candidates[ref.split('w')[0], hebrew].append(parts)

    recovered = 0
    for ref, row in missing.items():
        is_qere = ref in qere_words
        # A ketiv with no explicit one-word qere is not safe to substitute.
        if 'K' in row['RowType'] and not is_qere:
            continue
        hebrew = normalise_hebrew(qere_words.get(ref, row['NoCantillations']))
        matches = candidates[ref.split('w')[0], hebrew]
        if len(matches) != 1:
            continue
        parts = matches[0]
        if not is_qere and ','.join(part['Morphology'] for part in parts) != row['Morphology']:
            continue
        glosses = [part['ContextualGloss'] if usable_gloss(part['ContextualGloss'])
                   else part['EnglishGloss'] for part in parts]
        if not all(usable_gloss(gloss) for gloss in glosses):
            continue
        row['ContextualWordGloss'] = ','.join(glosses)
        ordinary = [part['EnglishGloss'] for part in parts]
        if all(usable_gloss(gloss) for gloss in ordinary):
            row['WordGloss'] = ','.join(ordinary)
        recovered += 1
        logging.info("Recovered %s gloss from Macula %s%s: %s", ref,
                     parts[0]['FGRef'], ' (OSHB qere)' if is_qere else '', row['ContextualWordGloss'])
    return recovered
