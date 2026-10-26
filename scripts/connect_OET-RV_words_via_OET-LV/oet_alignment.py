# SPDX-License-Identifier: MPL-2.0
"""Position-preserving ESFM tokens and deterministic, anchored word alignment.

This module has no BibleOrgSys dependency. Offsets always refer to the original
line, never to punctuation-stripped text. A slash-separated LV gloss is ONE
alignment column with alternatives, while separate English words sharing a
source number remain separate columns. See scripts/README.md for the workflow.
"""
from dataclasses import dataclass, replace
from collections import defaultdict
from bisect import bisect_left
import re

from oet_noun_tables import SIMPLE_NOUN_PAIRS


@dataclass(frozen=True)
class Token:
    text: str
    line: int
    start: int
    end: int
    number: int | None = None
    code: str | None = None  # None: outside add; '': plain add; otherwise its code
    span: tuple[int, int] | None = None
    boundary_before: bool = False
    boundary_after: bool = False
    word_fragment: bool = False

    @property
    def match_text(self):
        """Keep printed endings in text/offsets, but use plain table keys."""
        return OPTIONAL_PLURAL.sub(r'\1', self.text).removesuffix("'")

    @property
    def linkable(self):
        return (not self.word_fragment
                and (self.code is None or self.code in {'@', '*', '%', '&', '≈', '#', '≡', '!'}))


@dataclass(frozen=True)
class LVToken:
    text: str
    number: int
    proper: bool = False
    boundary_before: bool = False
    boundary_after: bool = False
    noun: bool = False
    names: frozenset[str] = frozenset()


MARKER = re.compile(r'\\(?P<name>\+?[a-zA-Z][a-zA-Z0-9]*)(?P<close>\*)? ?')
# A terminal straight apostrophe belongs to the word (houses', Yudas').
# An optional plural ending also belongs to the word: daughter(s), box(es).
# Curly closing quotation marks remain outside the word and its number.
WORD = re.compile(r"[^\W_]+(?:['’\-][^\W_]+)*(?:\((?:s|es)\))?'?", re.UNICODE)
OPTIONAL_PLURAL = re.compile(r'\((s|es)\)')
GRAMMATICAL_ENDINGS = frozenset(('s', 'es', "n't", 'd', 'll', 're', 've', 'm', 't'))
NOTE = re.compile(r'\\(\+?(?:f|fe|x|fig|jmp))\b.*?\\\1\*')
ADD_CODES = '@#≈≡*<>&%+^!='
# These additions have no corresponding source word, including uncertain forms.
UNLINKED_ADD_CODES = frozenset(('', '<', '>'))
TEXT_MARKER = re.compile(r'\\(?:v|p|m|pi\d*|q\d*|qm\d*|li\d*|lim\d*|nb|b|pc|pr|qr|cls|pmo|pm|pmc|pmr|mi|ph\d*|n)$')
SEMANTIC_CODES = {'@', '*', '%', '&'}
PRONOUNS = {'he', 'him', 'his', 'she', 'her', 'hers', 'they', 'them', 'their',
            'theirs', 'it', 'its', 'we', 'us', 'our', 'ours', 'i', 'me', 'my',
            'mine', 'you', 'your', 'yours', 'himself', 'herself', 'themselves',
            'itself', 'ourselves', 'yourself', 'yourselves'}
OWNERS = {'the', 'a', 'an', 'his', 'her', 'its', 'their', 'my', 'our', 'your'}
PLURAL_PRONOUNS = {'they', 'them', 'their', 'theirs', 'themselves', 'we', 'us', 'our', 'ours', 'ourselves'}
PLURAL_REFERENT_HEADS = {plural for plural, singular in SIMPLE_NOUN_PAIRS if plural != singular}
SINGULAR_REFERENT_HEADS = {singular for plural, singular in SIMPLE_NOUN_PAIRS if plural != singular}

# Punctuation is a conservative clause boundary, not a syntactic parse. The
# ordinary gap alignment is unchanged; only phrase movements obey these fences.
CLAUSE_BOUNDARY = re.compile(r'[.,;:!?—–“”‘’«»"\n]')
ADD_PREFIX = re.compile(r'\\\+?add \??[@#≈≡*<>&%+^!=]?')
MAX_MOVEMENT_WORDS = 6  # Applies separately to the matched and crossed blocks.
MIN_MOVEMENT_SCORE = 90  # Exact/curated inflections, excluding synonyms and related forms.
MOVEMENT_FUNCTION_WORDS = PRONOUNS | OWNERS | {
    'and', 'or', 'but', 'as', 'at', 'by', 'for', 'from', 'in', 'into', 'of',
    'on', 'onto', 'to', 'with', 'without', 'is', 'are', 'was', 'were', 'be',
    'been', 'being', 'will', 'would', 'shall', 'should', 'can', 'could', 'may',
    'might', 'must', 'do', 'does', 'did', 'have', 'has', 'had', 'having', 'not',
}


def referent_pronouns(unit):
    """Use clear number cues, leaving gender and uncertain descriptions open.

    A single named referent cannot normally replace 'they'. Coordinated names
    and explicit plural descriptions can. '%' has different semantics and does
    not use this filter.
    """
    words = [t.match_text.casefold().removesuffix("'s").removesuffix('’s') for t in unit]
    if 'and' in words or any(w in {'people', 'men', 'women', 'children'} for w in words):
        return PLURAL_PRONOUNS
    if any(OPTIONAL_PLURAL.search(t.text) for t in unit):
        return PRONOUNS  # An explicitly optional plural does not determine number.
    # Capitalisation does not make Israelis/Jews/Levites singular. Use known
    # plural nouns before the name check; an arbitrary final 's' would instead
    # misclassify individual names such as Barnabas, Silas and Lazarus.
    if words[-1] in PLURAL_REFERENT_HEADS:
        return PLURAL_PRONOUNS
    if words[-1] in SINGULAR_REFERENT_HEADS:
        return PRONOUNS - PLURAL_PRONOUNS
    if any(t.text[:1].isupper() and t.match_text.casefold() not in {'the', 'a', 'an', 'this', 'that', 'these', 'those'} for t in unit):
        return PRONOUNS - PLURAL_PRONOUNS
    if words[-1].endswith('s') and not words[-1].endswith('ss'):
        return PLURAL_PRONOUNS
    if words[-1] in {'man', 'woman', 'person', 'child', 'king', 'mother', 'father'}:
        return PRONOUNS - PLURAL_PRONOUNS
    return PRONOUNS


def index_book_lines(lines):
    """Map printed (chapter, verse) to (line, text offset); title uses verse 0.

    Verse bridges are indexed only at their first verse. Mapping versification
    is the caller's responsibility. Headings and introductions are never text.
    """
    result = defaultdict(list)
    chapter = verse = None
    for n, line in enumerate(lines):
        marker, _, rest = line.partition(' ')
        offset = len(marker) + 1
        if marker == r'\c':
            chapter, verse = int(rest), None
        elif chapter is not None and marker == r'\v':
            label, _, _ = rest.partition(' ')
            verse = int(label.split('-')[0])
            result[chapter, verse].append((n, offset + len(label) + 1))
        elif chapter is not None and marker == r'\d':
            if verse is None:
                result[chapter, 0].append((n, offset))
            # A trailing musical direction (e.g. Hab 3) is not the verse title.
        elif chapter is not None and verse is not None and TEXT_MARKER.fullmatch(marker) and rest:
            result[chapter, verse].append((n, offset))
    return dict(result)


def _add_code_at(text, start):
    """Read an optional uncertainty flag and add code; return the body offset."""
    if text[start:start+1] == '?':
        start += 1
    code = text[start:start+1]
    return (code, start+1) if code and code in ADD_CODES else ('', start)


def _after_word_markers(text, end):
    """Skip a number and adjacent field syntax, retaining real whitespace."""
    number = re.match(r'¦\d+', text[end:])
    pos = end + len(number[0]) if number else end
    while (marker := MARKER.match(text, pos)) is not None:
        if marker['close']:
            pos = marker.start() + len(marker['name']) + 2
        else:
            pos = marker.end()
            if marker['name'].lstrip('+') == 'add':
                _, pos = _add_code_at(text, pos)
    return pos


def is_word_fragment(text, start, end):
    """Reject unfinished words and detached apostrophe endings.

    Examples include ``mother\\add 's death\\add*``, ``God\\nd*'s`` and
    ``Did\\add n't\\add*``. Closing markers do not consume following spaces.
    """
    if start and text[start-1] == "'":
        return True
    pos = _after_word_markers(text, end)
    return (text[pos:pos+1].isalnum() or text[pos:pos+1] == "'"
            or OPTIONAL_PLURAL.match(text, pos) is not None)


def unlinked_add_spans(text):
    """Yield nonoverlapping (start, end) ranges for plain, < and > add spans.

    Include the markers so coverage can omit whole spans. Nested character
    formatting and uncertain/nested +add variants obey the same policy.
    """
    if '\\add ' not in text and '\\+add ' not in text:
        return
    masked = NOTE.sub(lambda m: ' ' * len(m[0]), text)
    stack, start = [], None
    for marker in MARKER.finditer(masked):
        if marker['name'].lstrip('+') != 'add':
            continue
        if marker['close']:
            if stack:
                stack.pop()
                if start is not None and not any(stack):
                    yield start, marker.end()
                    start = None
        else:
            code, _ = _add_code_at(masked, marker.end())
            excluded = code in UNLINKED_ADD_CODES
            stack.append(excluded)
            if excluded and start is None:
                start = marker.start()
    if start is not None:
        yield start, len(text) # An unclosed addition remains excluded to line end.


def tokenize(text, line=0, offset=0, split_names=True):
    """Read words, numbers and nested character markers without losing offsets.

    Notes are masked, not deleted. Plain, < and > add spans are retained as
    un-linkable tokens, so callers cannot accidentally join across them. Nested
    +add and uncertain variants have the same semantics as their base code.
    """
    masked = NOTE.sub(lambda m: ' ' * len(m[0]), text)
    # Mask numbers before scanning words, so ¦123-El cannot be consumed as a
    # single word and accidentally hide the second half of a linked place name.
    word_scan = re.sub(r'¦\d+', lambda m: ' ' * len(m[0]), masked)
    tokens, add_stack = [], []
    cursor = 0
    for marker in list(MARKER.finditer(masked)) + [None]:
        end = marker.start() if marker else len(masked)
        code, span = add_stack[-1] if add_stack else (None, None)
        # An inner specialist span cannot make an excluded outer span linkable.
        code, span = next((entry for entry in add_stack if entry[0] in UNLINKED_ADD_CODES), (code, span))
        for word in WORD.finditer(word_scan, cursor, end):
            number_match = re.match(r'¦(\d+)', masked[word.end():end])
            number = int(number_match[1]) if number_match else None
            # Capitalised components may have separate source numbers (Beyt-Lehem).
            # Keep traditional-name alternatives whole for their dedicated matcher.
            parts = re.split(r'-(?=[A-Z])', word[0]) if split_names and code != '!' else [word[0]]
            start = word.start()
            for part in parts:
                part_end = start + len(part)
                tokens.append(Token(part, line, offset+start, offset+part_end,
                                    number if part_end == word.end() else None, code, span,
                                    word_fragment=is_word_fragment(masked, start, part_end)))
                start = part_end + 1
        if marker is None:
            break
        cursor = marker.end()
        if marker['name'].lstrip('+') == 'add':
            if marker['close']:
                if add_stack:
                    add_stack.pop()
            else:
                start = cursor
                code, cursor = _add_code_at(masked, cursor)
                add_stack.append((code, (line, offset+start)))
    # The s in age\\add s\\add* is not a separate source word. An ordinary
    # stem after a supplied prefix (\\add re\\add*build) still ends at the
    # whole word's end and can keep its source link. Do not cross real spaces.
    for i in range(1, len(tokens)):
        if tokens[i].text.casefold() not in GRAMMATICAL_ENDINGS:
            continue
        start = tokens[i].start-offset
        pos = _after_word_markers(masked, tokens[i-1].end-offset)
        if pos == start or (masked[pos:pos+1] == "'" and pos+1 == start):
            tokens[i] = replace(tokens[i], word_fragment=True)
    # Retain punctuation even though the matchable words exclude it. Mask add
    # prefixes so an uncertainty '?' is not mistaken for sentence punctuation.
    punctuation = ADD_PREFIX.sub(lambda m: ' ' * len(m[0]), word_scan)
    punctuation = MARKER.sub(lambda m: ' ' * len(m[0]), punctuation)
    edges = [0] + [t.end-offset for t in tokens]
    starts = [t.start-offset for t in tokens] + [len(text)]
    fences = [bool(CLAUSE_BOUNDARY.search(punctuation[end:start]))
              for end, start in zip(edges, starts)]
    return [replace(t, boundary_before=fences[i], boundary_after=fences[i+1])
            for i, t in enumerate(tokens)]


def with_clause_boundaries(columns, lv_text):
    """Restore LV punctuation fences after the connector cleans its glosses.

    English gloss components share a source number. A number occurring on both
    sides of punctuation is ambiguous and is fenced off from phrase movements.
    This metadata never changes a gloss, source number, or ordinary gap match.
    """
    clauses = defaultdict(set)
    clause = 0
    for token in tokenize(lv_text, split_names=False):
        clause += token.boundary_before
        if token.number is not None:
            clauses[token.number].add(clause)
    labels = [clauses[c.number] for c in columns]
    return [replace(c,
                    boundary_before=c.boundary_before or len(labels[i]) != 1
                        or (i > 0 and labels[i-1] != labels[i]),
                    boundary_after=c.boundary_after or len(labels[i]) != 1
                        or (i+1 < len(columns) and labels[i+1] != labels[i]))
            for i, c in enumerate(columns)]


def certain_alignment(matrix, numbers):
    """Return row -> number only when EVERY maximum-score alignment agrees."""
    return {row: number for row, (number, _) in certain_alignment_details(matrix, numbers).items()}


def certain_alignment_details(matrix, numbers):
    """Return row -> (number, possible columns) for certain alignment decisions.

    Forward and backward dynamic programming take O(rows * columns), including
    ambiguity detection. Skipping is free. A row must be matched on every best
    path; multiple columns are acceptable only if they carry the same number.
    This replaces re-running the whole alignment once per proposed pair.
    """
    n, m = len(matrix), len(numbers)
    if not n or not m:
        return {}
    forward = [[0]*(m+1) for _ in range(n+1)]
    backward = [[0]*(m+1) for _ in range(n+1)]
    for i in range(n):
        for j in range(m):
            forward[i+1][j+1] = max(forward[i][j+1], forward[i+1][j],
                                   forward[i][j] + (matrix[i][j] or 0))
    for i in range(n-1, -1, -1):
        for j in range(m-1, -1, -1):
            backward[i][j] = max(backward[i+1][j], backward[i][j+1],
                                  backward[i+1][j+1] + (matrix[i][j] or 0))
    best = forward[n][m]
    result = {}
    for i in range(n):
        if any(forward[i][j] + backward[i+1][j] == best for j in range(m+1)):
            continue  # Some optimal alignment leaves this RV occurrence unlinked.
        columns = frozenset(j for j in range(m) if matrix[i][j] is not None
                            and forward[i][j] + matrix[i][j] + backward[i+1][j+1] == best)
        choices = {numbers[j] for j in columns}
        if len(choices) == 1:
            result[i] = choices.pop(), columns
    return result


def certain_span_alignment(matrix, numbers, phrases):
    """As above, also allowing curated (RV start/end, LV start/end, score) edges.

    A phrase consumes its whole span on each side. All its LV columns must have
    one source number. Forward/backward scores identify every optimal edge;
    a row is accepted only if no optimal path skips it and all its edges agree
    on the number. Thus 'his' -> 'of him' cannot leave 'him' free for another row.
    The ordinary word-only case retains the smaller, well-tested fast path.
    """
    if not phrases:
        return certain_alignment_details(matrix, numbers)
    n, m = len(matrix), len(numbers)
    edges = defaultdict(list)
    for i, row in enumerate(matrix):
        for j, score in enumerate(row):
            if score is not None:
                edges[i, j].append((i+1, j+1, score))
    for i, end_i, j, end_j, score in phrases:
        assert 0 <= i < end_i <= n and 0 <= j < end_j <= m
        assert len(set(numbers[j:end_j])) == 1
        edges[i, j].append((end_i, end_j, score))
    forward = [[0]*(m+1) for _ in range(n+1)]
    backward = [[0]*(m+1) for _ in range(n+1)]
    for i in range(n+1):
        for j in range(m+1):
            value = forward[i][j]
            if i < n:
                forward[i+1][j] = max(forward[i+1][j], value)
            if j < m:
                forward[i][j+1] = max(forward[i][j+1], value)
            for end_i, end_j, score in edges.get((i,j), ()):
                forward[end_i][end_j] = max(forward[end_i][end_j], value+score)
    for i in range(n, -1, -1):
        for j in range(m, -1, -1):
            values = [0]
            if i < n: values.append(backward[i+1][j])
            if j < m: values.append(backward[i][j+1])
            values.extend(score+backward[end_i][end_j]
                          for end_i, end_j, score in edges.get((i,j), ()))
            backward[i][j] = max(values)
    best = forward[n][m]
    choices, locations = defaultdict(set), defaultdict(set)
    for (i,j), transitions in edges.items():
        for end_i, end_j, score in transitions:
            if forward[i][j]+score+backward[end_i][end_j] == best:
                for row in range(i,end_i):
                    choices[row].add(numbers[j])
                    locations[row].update(range(j,end_j))
    return {i: (next(iter(choices[i])), frozenset(locations[i]))
            for i in range(n) if len(choices[i]) == 1
            and not any(forward[i][j]+backward[i+1][j] == best for j in range(m+1))}


def phrase_edges(units, columns, phrase_index, occupied):
    """Find literal curated phrases inside one bounded gap, with no source reuse."""
    if not phrase_index:
        return []
    result = []
    rv_words = [u[0].match_text.casefold() if len(u) == 1 and u[0].linkable
                and u[0].code not in SEMANTIC_CODES | {'!', '≡'} else None for u in units]
    lv_words = [{w.casefold() for w in (c.text, *c.text.split('/'))} for c in columns]
    for i, word in enumerate(rv_words):
        for rv_phrase, lv_phrase in phrase_index.get(word, ()):
            end_i = i+len(rv_phrase)
            if tuple(rv_words[i:end_i]) != rv_phrase:
                continue
            if not same_clause([u[0] for u in units[i:end_i]]):
                continue
            for j in range(len(columns)-len(lv_phrase)+1):
                end_j = j+len(lv_phrase)
                if (any(pos in occupied for pos in range(j,end_j))
                        or len({c.number for c in columns[j:end_j]}) != 1
                        or not same_clause(columns[j:end_j])):
                    continue
                if all(w in lv_words[pos] for pos,w in enumerate(lv_phrase, start=j)):
                    result.append((i, end_i, j, end_j, 85*len(rv_phrase)))
    return result


def linked_phrase_columns(units, columns, positions, phrase_index):
    """Reconstruct whole-phrase ownership from saved numbers on later passes.

    Otherwise a newly linked 'his' has no lexical match to either 'of' or 'him',
    and a later pass could accidentally lend 'him' to an unrelated RV occurrence.
    """
    result = defaultdict(set)
    if not phrase_index:
        return result
    for i, unit in enumerate(units):
        if len(unit) != 1 or unit[0].number is None or unit[0].code in SEMANTIC_CODES | UNLINKED_ADD_CODES | {'!'}:
            continue
        number = unit[0].number
        for rv_phrase, lv_phrase in phrase_index.get(unit[0].match_text.casefold(), ()):
            span = units[i:i+len(rv_phrase)]
            if (len(span) != len(rv_phrase)
                    or any(len(u) != 1 or u[0].number != number or u[0].code != unit[0].code for u in span)
                    or tuple(u[0].match_text.casefold() for u in span) != rv_phrase):
                continue
            for j in positions[number]:
                stop = j+len(lv_phrase)
                if stop > len(columns):
                    continue
                if all(c.number == number and word in {c.text.casefold(), *(w.casefold() for w in c.text.split('/'))}
                       for c,word in zip(columns[j:stop],lv_phrase)):
                    for row in range(i,i+len(rv_phrase)):
                        result[row].update(range(j,stop))
    return result


def rotated_columns(columns, units):
    """Infer the clause swap marked ⇔ from a single descent in existing links.

    Words WITHIN each clause keep their order. If anchors cannot identify one
    switch, retain the original columns; the bounded-gap matcher still handles
    local runs and abstains at conflicting boundaries.
    """
    positions = {}
    for i, col in enumerate(columns):
        positions.setdefault(col.number, i)
    anchors = [positions[u[0].number] for u in units if u[0].number in positions]
    descents = [(a, b) for a, b in zip(anchors, anchors[1:]) if a > b]
    if len(descents) != 1:
        return columns
    # Cut at the first anchor of the clause translated first. Require enough
    # anchors to distinguish the two runs from an isolated local inversion.
    cut = anchors[0]
    if cut == 0 or len(anchors) < 3:
        return columns
    return columns[cut:] + columns[:cut]


def anchor_positions(unit, columns, positions, lexical_score):
    """Locate a numbered unit at its best English gloss(es), not ID order."""
    numbers = {t.number for t in unit if t.number is not None}
    number = next(iter(numbers)) if len(numbers) == 1 else None
    scored = []
    for pos in positions.get(number, ()):
        scores = [lexical_score(t.text, w) for t in unit
                  for w in (columns[pos].text, *columns[pos].text.split('/'))]
        scored.append((max((s[1] for s in scores if s), default=0), pos))
    best = max((s for s, _ in scored), default=0)
    return [pos for s, pos in scored if s == best]


def _movement_window(start, end, first, last, anchors, anchor_indexes, m):
    """Bound one adjacent block transposition by the surrounding fixed links.

    [start:end] is the RV phrase, [first:last] its proposed LV counterpart.
    Return the combined RV/LV windows only when the crossed anchors are ordered,
    unambiguous, nearby, and enclosed by compatible outer anchors. Missing verse
    edges act as sentinels; a present but unresolved anchor always blocks a move.
    """
    left = bisect_left(anchor_indexes, start)-1
    right = bisect_left(anchor_indexes, end)

    def position(index):
        if index < 0:
            return -1
        if index >= len(anchors):
            return m
        values = anchors[index][1]
        return values[0] if len(values) == 1 else None

    lp, rp = position(left), position(right)
    if lp is None or rp is None:
        return None
    if rp < first:  # RV: phrase, linked block; LV: linked block, phrase.
        stop = right
        crossed = []
        while stop < len(anchors):
            pos = position(stop)
            if pos is None:
                return None
            if pos >= first:
                break
            if anchors[stop][0]-end+1 > MAX_MOVEMENT_WORDS:
                return None
            crossed.append(pos)
            stop += 1
        if (not crossed or crossed != sorted(set(crossed))
                or lp >= crossed[0] or position(stop) < last
                or first-crossed[0] > MAX_MOVEMENT_WORDS):
            return None
        return start, anchors[stop-1][0]+1, crossed[0], last
    if lp >= last:  # RV: linked block, phrase; LV: phrase, linked block.
        stop = left
        crossed = []
        while stop >= 0:
            pos = position(stop)
            if pos is None:
                return None
            if pos < last:
                break
            if start-anchors[stop][0] > MAX_MOVEMENT_WORDS:
                return None
            crossed.append(pos)
            stop -= 1
        if (not crossed or crossed != sorted(set(crossed), reverse=True)
                or rp <= crossed[0] or position(stop) >= first
                or crossed[0]-last+1 > MAX_MOVEMENT_WORDS):
            return None
        return anchors[stop+1][0], end, first, crossed[0]+1
    return None  # It fits the ordinary gap, or would need more than one swap.


def same_clause(words):
    """Whether adjacent tokens/columns have no intervening punctuation boundary."""
    return not any(a.boundary_after or b.boundary_before
                   for a, b in zip(words, words[1:]))


def propose_phrase_movements(units, columns, lexical_score, normalise, pending):
    """Recover short lexical phrases across a nearby, already linked block.

    This is a bounded adjacent-block transposition, not an unrestricted window
    search. Each phrase has 2..6 consecutive strong word matches, including two
    previously unlinked content words with distinct source IDs. Existing links
    alone cannot justify moving an otherwise ambiguous single word (e.g. 'son'
    in a reordered genealogy or 'hundred' in a list of quantities).
    Both texts must stay within their
    punctuation fences. Semantic/add spans, unresolved anchors and source IDs
    already owned outside the phrase are excluded. Conflicting candidate moves
    are all rejected: neither distance nor enumeration order breaks a tie.
    """
    # Ordinary proposals are treated as fixed for this pass, so the two rules
    # cannot assign conflicting numbers or claim the same newly matched source.
    live = [[replace(t, number=pending[t]) if t in pending else t for t in unit]
            for unit in units]
    positions, owners = defaultdict(list), defaultdict(set)
    for i, col in enumerate(columns):
        positions[col.number].append(i)
    anchors = []
    for i, unit in enumerate(live):
        for token in unit:
            if token.number is not None:
                owners[token.number].add(i)
        if any(t.number is not None for t in unit):
            anchors.append((i, anchor_positions(unit, columns, positions, lexical_score)))
    if not anchors:
        return []  # Reordering without local anchor evidence is too uncertain.
    anchor_indexes = [i for i, _ in anchors]
    eligible = [len(u) == 1 and u[0].code is None for u in live]
    # Most LV words already belong to fixed links. Index strong starts only
    # among sources that a phrase could still claim; reuse scores for repeated
    # RV spellings. This avoids building a candidate for every RV/LV word pair.
    strong_starts = {}

    def strongly_matches(token, col):
        return any(s[1] >= MIN_MOVEMENT_SCORE
                   for w in col.text.split('/') if (s := lexical_score(token.text, w)))

    candidates = []
    for start, unit in enumerate(live):
        if not eligible[start] or not any(eligible[i] and live[i][0].number is None
                                          for i in range(start, min(len(live), start+MAX_MOVEMENT_WORDS))):
            continue
        # A numbered start already identifies its possible LV columns. Avoid
        # scanning the entire verse again for these mostly linked phrases.
        token = unit[0]
        if token.number is not None:
            starts = positions[token.number]
        else:
            if token.text not in strong_starts:
                strong_starts[token.text] = [i for i, col in enumerate(columns)
                                             if strongly_matches(token, col)]
            starts = [i for i in strong_starts[token.text]
                      if all(start <= owner < start+MAX_MOVEMENT_WORDS
                             for owner in owners[columns[i].number])]
        for first in starts:
            new_content_numbers = set()
            numbers = set()
            new_pairs = []
            for length in range(1, MAX_MOVEMENT_WORDS+1):
                ri, ci = start+length-1, first+length-1
                if ri >= len(live) or ci >= len(columns) or not eligible[ri]:
                    break
                token, col = live[ri][0], columns[ci]
                if token.number is not None and token.number != col.number:
                    break
                if length > 1 and (not same_clause([live[ri-1][0], token])
                                   or not same_clause(columns[ci-1:ci+1])):
                    break
                if not strongly_matches(token, col):
                    break
                numbers.add(col.number)
                if token.number is None:
                    new_pairs.append((token, ci))
                    if normalise(token.text) not in MOVEMENT_FUNCTION_WORDS:
                        new_content_numbers.add(col.number)
                if len(new_content_numbers) < 2:
                    continue
                end, last = ri+1, ci+1
                if any(owner < start or owner >= end for num in numbers for owner in owners[num]):
                    continue
                window = _movement_window(start, end, first, last, anchors,
                                          anchor_indexes, len(columns))
                if window is None:
                    continue
                a, b, x, y = window
                if (not all(eligible[a:b]) or not same_clause([u[0] for u in live[a:b]])
                        or not same_clause(columns[x:y])):
                    continue
                candidates.append(tuple(new_pairs))
    choices, claims = defaultdict(set), defaultdict(set)
    for candidate in candidates:
        for token, col in candidate:
            choices[token].add(columns[col].number)
            claims[col].add(token)
    accepted = {}
    for candidate in candidates:
        if all(len(choices[t]) == 1 and len(claims[c]) == 1 for t, c in candidate):
            for token, col in candidate:
                accepted[token] = columns[col].number
    return [(t, number, 'local phrase movement') for t, number in accepted.items()]


def alignment_units(tokens):
    """Group semantic spans consistently for alignment and source ownership."""
    units = []
    for token in tokens:
        if token.code in UNLINKED_ADD_CODES and token.number is not None:
            token = replace(token, number=None) # Old invalid links cannot be anchors.
        if token.code in SEMANTIC_CODES and units and units[-1][0].span == token.span:
            units[-1].append(token)
        else:
            units.append([token])
    return units


def propose_links(tokens, columns, lexical_score, normalise, reversed_clauses=False, phrase_index=None, word_score=None):
    """Propose positional links in gaps bounded by existing source numbers.

    Existing links are immutable anchors, including locally reordered phrases.
    Bounds are LV TEXT positions, never numeric source-word order. Semantic add
    spans form one row: all words in '@the women' can represent one pronoun.
    Conflicting or out-of-verse anchors make a gap ineligible. A separate bounded
    phrase-movement rule can cross ordered anchors with strong lexical evidence.
    No previous verse is consulted and proximity alone never creates a link.
    """
    units = alignment_units(tokens)
    if reversed_clauses:
        columns = rotated_columns(columns, units)
    positions = defaultdict(list)
    for i, col in enumerate(columns):
        positions[col.number].append(i)
    phrase_owners = linked_phrase_columns(units, columns, positions, phrase_index)
    proposals = []
    anchors = []
    for i, unit in enumerate(units):
        numbers = {t.number for t in unit if t.number is not None}
        if numbers:
            # Partially numbered semantic spans can be completed, but not if
            # their existing words disagree or the source belongs to another verse.
            if len(numbers) == 1 and unit[0].code in SEMANTIC_CODES and next(iter(numbers)) in positions:
                proposals.extend((t, next(iter(numbers)), 'complete add span') for t in unit if t.number is None)
            # Pin an anchor to its English gloss position within a source word,
            # not the entire number group. Otherwise 'her mother' could reuse
            # that same 'her' in a later, unrelated part of the RV sentence.
            anchors.append((i, sorted(phrase_owners[i]) if i in phrase_owners
                            else anchor_positions(unit, columns, positions, lexical_score)))
    # A reordered anchor can sit outside an RV gap while its LV gloss lies
    # inside that gap's bounds. Do not consume that same gloss again. Reserve
    # English columns, not whole source IDs: 'put' and 'around' may legitimately
    # share one ID and still align to separate RV words. Only a strong lexical
    # match proves consumption; a paraphrased/unresolved anchor still supplies
    # bounds but must not reserve every gloss belonging to its source number.
    occupied_columns = {
        pos for i, locations in anchors for pos in locations
        if any(s and (s[1] >= MIN_MOVEMENT_SCORE or s[0] == 'contraction subject')
               for t in units[i] for w in columns[pos].text.split('/')
               if (s := lexical_score(t.text, w)))
    }
    occupied_columns.update(pos for locations in phrase_owners.values() for pos in locations)
    anchor_owners = defaultdict(set)
    for owner, locations in anchors:
        for pos in locations:
            anchor_owners[pos].add(owner)
    anchored_numbers = {t.number for i, _ in anchors for t in units[i]}
    boundaries = [(-1, [])] + anchors + [(len(units), [])]
    gap_proposals, column_claims = [], defaultdict(set)
    for (left, left_positions), (right, right_positions) in zip(boundaries, boundaries[1:]):
        if (left >= 0 and not left_positions) or (right < len(units) and not right_positions):
            continue
        lo = min(left_positions)+1 if left >= 0 else 0
        hi = max(right_positions) if right < len(units) else len(columns)
        if lo >= hi:
            continue
        gap = units[left+1:right]
        candidates = columns[lo:hi]
        # Reordered clauses can put a non-neighbouring RV anchor inside this
        # LV window. Lexical evidence can still recover words, but a semantic
        # span cannot identify its clause from pronouns/articles alone.
        crosses_anchor = any(anchor_owners[pos] - {left, right} for pos in range(lo, hi))
        left_numbers = {t.number for t in units[left]} if left >= 0 else set()
        right_numbers = {t.number for t in units[right]} if right < len(units) else set()
        distant_numbers = anchored_numbers - left_numbers - right_numbers
        matrix = []
        for unit in gap:
            code = unit[0].code
            row = []
            for pos, col in enumerate(candidates, start=lo):
                alternatives = [normalise(w) for w in col.text.split('/')]
                score = None
                if pos not in occupied_columns and all(t.linkable for t in unit):
                    if (code in SEMANTIC_CODES and crosses_anchor) or (
                            col.number in distant_numbers and
                            all(t.match_text.casefold() in MOVEMENT_FUNCTION_WORDS for t in unit)):
                        pass # No semantic clause guess or distant function-word reuse.
                    elif code in ('@', '%'):
                        allowed = referent_pronouns(unit) if code == '@' else PRONOUNS
                        if any(w in allowed for w in alternatives): score = 100
                    elif code == '&':
                        # A leftover article in the preceding name's source
                        # group does not become the following noun's owner.
                        if col.number not in left_numbers and any(w in OWNERS for w in alternatives): score = 100
                    elif code == '*':
                        if col.proper: score = 100
                    elif code not in ('!', '≡'):
                        scores = [lexical_score(unit[0].text, w) for w in (col.text, *col.text.split('/'))]
                        if word_score is not None:
                            scores.append(word_score(unit[0], col))
                        score = max((s[1] for s in scores if s), default=None)
                row.append(score)
            matrix.append(row)
        phrases = phrase_edges(gap, candidates, phrase_index, {pos-lo for pos in occupied_columns if lo <= pos < hi})
        for row, (number, locations) in certain_span_alignment(matrix, [c.number for c in candidates], phrases).items():
            reason = f'add {gap[row][0].code}' if gap[row][0].code in SEMANTIC_CODES else 'anchored order'
            locations = {lo+pos for pos in locations}
            gap_proposals.append((gap[row], number, reason, locations))
            for pos in locations:
                column_claims[pos].add(left)
    # Within one gap the dynamic program already enforces column ownership.
    # Different gaps are solved independently; overlapping claims between them
    # must abstain together, rather than depending on which gap is visited first.
    for unit, number, reason, locations in gap_proposals:
        if all(len(column_claims[pos]) == 1 for pos in locations):
            proposals.extend((t, number, reason) for t in unit if t.number is None)
    pending = {token: number for token, number, _ in proposals}
    proposals.extend(propose_phrase_movements(units, columns, lexical_score, normalise, pending))
    if not proposals:
        proposals.extend(propose_local_context(units, columns, positions, anchors,
                                               occupied_columns | {pos for pos, claims in column_claims.items() if len(claims) > 1},
                                               normalise))
    return proposals


def propose_local_context(units, columns, positions, anchors, occupied, normalise):
    """Complete exact short phrases beside a linked content word.

    An article/preposition and its neighbouring content word can move together,
    e.g. 'the king' after another linked phrase. Requiring two *new* content
    words for a phrase movement misses these partially linked phrases. Here the
    existing content-word link and exact adjacency on BOTH sides supply evidence.
    Possessives and copulas may also move within one source word's gloss
    ('father of my' -> 'my father', 'blessed are' -> 'are blessed'). The head
    and function word must both match exactly. No synonym inference is made.

    Reserve individual English columns and reject competing RV claims. A source
    number may have other gloss components already linked, but the proposed
    component itself must be free. Excluded/specialist spans and punctuation are
    fences. This fallback runs only after ordinary alignment has settled.
    """
    function_words = {'the', 'a', 'an', 'of', 'to', 'in', 'on', 'for', 'with',
                      'by', 'from', 'my', 'your', 'his', 'her', 'our', 'their', 'its',
                      'is', 'are', 'was', 'were', 'be', 'been', 'being'}
    possessives = {'my', 'your', 'his', 'her', 'our', 'their', 'its'}
    copulas = {'is', 'are', 'was', 'were', 'be', 'been', 'being'}
    anchor_map = dict(anchors)
    choices, claims = defaultdict(set), defaultdict(set)
    for i, unit in enumerate(units):
        if len(unit) != 1:
            continue
        token = unit[0]
        word = normalise(token.text)
        if token.number is not None or token.code is not None or word not in function_words:
            continue
        for neighbour in (i-1, i+1):
            if neighbour not in anchor_map or len(units[neighbour]) != 1:
                continue
            head = units[neighbour][0]
            if (head.code is not None or normalise(head.text) in MOVEMENT_FUNCTION_WORDS
                    or not same_clause([u[0] for u in units[min(i, neighbour):max(i, neighbour)+1]])):
                continue
            for pos in anchor_map[neighbour]:
                if not any(normalise(head.text) == normalise(w) for w in columns[pos].text.split('/')):
                    continue # A weak or paraphrased anchor is insufficient evidence.
                adjacent = pos-1 if i < neighbour else pos+1
                candidates = {adjacent} if 0 <= adjacent < len(columns) else set()
                if word in possessives | copulas and i < neighbour:
                    candidates.update(j for j in positions[head.number]
                                      if 0 < j-pos <= 3
                                      and all(c.number == head.number for c in columns[pos:j+1]))
                for j in candidates:
                    if (j in occupied or not same_clause(columns[min(pos,j):max(pos,j)+1])
                            or not any(word == normalise(w) for w in columns[j].text.split('/'))):
                        continue
                    choices[token].add(j)
                    claims[j].add(token)
    return [(t, next(iter(numbers)), 'linked phrase context')
            for t, locations in choices.items()
            if len(numbers := {columns[j].number for j in locations}) == 1
            and all(len(claims[j]) == 1 for j in locations)]
