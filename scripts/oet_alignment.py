# SPDX-License-Identifier: MPL-2.0
"""Position-preserving ESFM tokens and deterministic, anchored word alignment.

This module has no BibleOrgSys dependency. Offsets always refer to the original
line, never to punctuation-stripped text. A slash-separated LV gloss is ONE
alignment column with alternatives, while separate English words sharing a
source number remain separate columns. See scripts/README.md for the workflow.
"""
from dataclasses import dataclass
from collections import defaultdict
import re


@dataclass(frozen=True)
class Token:
    text: str
    line: int
    start: int
    end: int
    number: int | None = None
    code: str | None = None  # None: outside add; '': plain add; otherwise its code
    span: tuple[int, int] | None = None

    @property
    def linkable(self):
        return self.code is None or self.code in {'@', '*', '%', '&', '>', '≈', '#', '≡', '!'}


@dataclass(frozen=True)
class LVToken:
    text: str
    number: int
    proper: bool = False


MARKER = re.compile(r'\\(?P<name>\+?[a-zA-Z][a-zA-Z0-9]*)(?P<close>\*)? ?')
WORD = re.compile(r"[^\W_]+(?:['’\-][^\W_]+)*", re.UNICODE)
NOTE = re.compile(r'\\(\+?(?:f|fe|x|fig|jmp))\b.*?\\\1\*')
ADD_CODES = '@#≈≡*<>&%+^!='
TEXT_MARKER = re.compile(r'\\(?:v|p|m|pi\d*|q\d*|qm\d*|li\d*|lim\d*|nb|b|pc|pr|qr|cls|pmo|pm|pmc|pmr|mi|ph\d*|n)$')
SEMANTIC_CODES = {'@', '*', '%', '&', '>'}
PRONOUNS = {'he', 'him', 'his', 'she', 'her', 'hers', 'they', 'them', 'their',
            'theirs', 'it', 'its', 'we', 'us', 'our', 'ours', 'i', 'me', 'my',
            'mine', 'you', 'your', 'yours', 'himself', 'herself', 'themselves',
            'itself', 'ourselves', 'yourself', 'yourselves'}
OWNERS = {'the', 'a', 'an', 'his', 'her', 'its', 'their', 'my', 'our', 'your'}
PLURAL_PRONOUNS = {'they', 'them', 'their', 'theirs', 'themselves', 'we', 'us', 'our', 'ours', 'ourselves'}


def referent_pronouns(unit):
    """Use clear number cues, leaving gender and uncertain descriptions open.

    A single named referent cannot normally replace 'they'. Coordinated names
    and explicit plural descriptions can. '%' has different semantics and does
    not use this filter.
    """
    words = [t.text.casefold().removesuffix("'s").removesuffix('’s') for t in unit]
    if 'and' in words or any(w in {'people', 'men', 'women', 'children'} for w in words):
        return PLURAL_PRONOUNS
    if any(t.text[:1].isupper() and t.text.casefold() not in {'the', 'a', 'an', 'this', 'that', 'these', 'those'} for t in unit):
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


def tokenize(text, line=0, offset=0, split_names=True):
    """Read words, numbers and nested character markers without losing offsets.

    Notes are masked, not deleted. Plain and uncertain plain add spans are
    retained as un-linkable tokens, so callers cannot accidentally join across
    them. Nested +add and ?@ variants have the same semantics as their base code.
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
                                    number if part_end == word.end() else None, code, span))
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
                if masked[cursor:cursor+1] == '?':
                    cursor += 1
                code = masked[cursor:cursor+1]
                if code and code in ADD_CODES:
                    cursor += 1
                else:
                    code = ''
                add_stack.append((code, (line, offset+start)))
    return tokens


def certain_alignment(matrix, numbers):
    """Return row -> number only when EVERY maximum-score alignment agrees.

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
        choices = {numbers[j] for j in range(m) if matrix[i][j] is not None
                   and forward[i][j] + matrix[i][j] + backward[i+1][j+1] == best}
        if len(choices) == 1:
            result[i] = choices.pop()
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


def propose_links(tokens, columns, lexical_score, normalise, reversed_clauses=False):
    """Propose positional links in gaps bounded by existing source numbers.

    Existing links are immutable anchors, including locally reordered phrases.
    Bounds are LV TEXT positions, never numeric source-word order. Semantic add
    spans form one row: all words in '@the women' can represent one pronoun.
    Conflicting or out-of-verse anchors make a gap ineligible. No previous verse
    is consulted and neither equal gap size nor proximity alone creates a link.
    """
    units = []
    for token in tokens:
        if token.code in SEMANTIC_CODES and units and units[-1][0].span == token.span:
            units[-1].append(token)
        else:
            units.append([token])
    if reversed_clauses:
        columns = rotated_columns(columns, units)
    positions = defaultdict(list)
    for i, col in enumerate(columns):
        positions[col.number].append(i)
    proposals = []
    anchors = []
    for i, unit in enumerate(units):
        numbers = {t.number for t in unit if t.number is not None}
        if numbers:
            # Partially numbered semantic spans can be completed, but not if
            # their existing words disagree or the source belongs to another verse.
            if len(numbers) == 1 and unit[0].code in SEMANTIC_CODES and next(iter(numbers)) in positions:
                proposals.extend((t, next(iter(numbers)), 'complete add span') for t in unit if t.number is None)
            number = next(iter(numbers)) if len(numbers) == 1 else None
            # Pin an anchor to its English gloss position within a source word,
            # not the entire number group. Otherwise 'her mother' could reuse
            # that same 'her' in a later, unrelated part of the RV sentence.
            scored = []
            for pos in positions.get(number, ()):
                scores = [lexical_score(t.text, w) for t in unit
                          for w in columns[pos].text.split('/')]
                scored.append((max((s[1] for s in scores if s), default=0), pos))
            best = max((s for s, _ in scored), default=0)
            anchor_positions = [pos for s, pos in scored if s == best]
            anchors.append((i, anchor_positions))
    boundaries = [(-1, [])] + anchors + [(len(units), [])]
    for (left, left_positions), (right, right_positions) in zip(boundaries, boundaries[1:]):
        if (left >= 0 and not left_positions) or (right < len(units) and not right_positions):
            continue
        lo = min(left_positions)+1 if left >= 0 else 0
        hi = max(right_positions) if right < len(units) else len(columns)
        if lo >= hi:
            continue
        gap = units[left+1:right]
        candidates = columns[lo:hi]
        matrix = []
        for unit in gap:
            code = unit[0].code
            row = []
            for col in candidates:
                alternatives = [normalise(w) for w in col.text.split('/')]
                score = None
                if all(t.linkable for t in unit):
                    if code in ('@', '%'):
                        allowed = referent_pronouns(unit) if code == '@' else PRONOUNS
                        if any(w in allowed for w in alternatives): score = 100
                    elif code == '&':
                        if any(w in OWNERS for w in alternatives): score = 100
                    elif code == '*':
                        if col.proper: score = 100
                    elif code not in ('!', '>'):
                        scores = [lexical_score(unit[0].text, w) for w in col.text.split('/')]
                        score = max((s[1] for s in scores if s), default=None)
                row.append(score)
            matrix.append(row)
        for row, number in certain_alignment(matrix, [c.number for c in candidates]).items():
            reason = f'add {gap[row][0].code}' if gap[row][0].code in SEMANTIC_CODES else 'anchored order'
            proposals.extend((token, number, reason) for token in gap[row] if token.number is None)
    # An explicitly implied person/object belongs to the immediately preceding
    # translated word ("one >person"), including a link just found in this pass.
    pending = {token: number for token, number, _ in proposals}
    for i, unit in enumerate(units):
        if i == 0 or unit[0].code != '>':
            continue
        previous = units[i-1][-1]
        number = previous.number or pending.get(previous)
        if previous.linkable and number in positions and all(t.number in (None, number) for t in unit):
            proposals.extend((t, number, 'implied add >') for t in unit if t.number is None and t not in pending)
    return proposals
