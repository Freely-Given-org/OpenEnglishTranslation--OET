# SPDX-License-Identifier: MPL-2.0
"""One selection boundary for every RV/LV matching rule.

Providers describe evidence; none edits ESFM. Positional alignment considers
lexical, name, number-change and phrase evidence together. Unique verse-wide
matches can recover reordered words, but cannot displace a contextual match.
Traditional aliases and explicitly repeated phrases may share a source gloss
with their original occurrence. All other competing claims abstain together.

Selection is deterministic and independent of provider enumeration order.
Existing links are immutable. Virtual anchors allow refinement to a fixed
point before the caller writes the accepted occurrences once, right to left.
"""
from collections import defaultdict
from dataclasses import dataclass, replace

from oet_alignment import (SEMANTIC_CODES, MOVEMENT_FUNCTION_WORDS, alignment_units,
                           linked_phrase_columns, phrase_edges, propose_links, same_clause)


# These nouns often supply the English head of an adjective. Even an exact
# leftover "person" elsewhere in the verse does not establish its referent.
CONTEXTUAL_HEADS = {'person', 'people', 'one', 'ones', 'thing', 'things'}


@dataclass(frozen=True)
class Candidate:
    """An atomic set of (RV occurrence, source number) assignments.

    Claims identify English LV columns, not source IDs: several English gloss
    words can legitimately translate one Hebrew/Greek word. Bindings include
    already-linked originals when a translator explicitly supplies an alias
    or repeat. That makes permitted sharing local and auditable.
    """
    bindings: tuple
    claims: frozenset
    reason: str
    priority: int = 1


def conflicts(first, second):
    """Two bundles may agree on links, but cannot lend a gloss to a new owner."""
    if len(first.bindings) == len(second.bindings) == 1:
        (a, an), (b, bn) = first.bindings[0], second.bindings[0]
        return an != bn if a == b else bool(first.claims & second.claims)
    a, b = dict(first.bindings), dict(second.bindings)
    if any(a[token] != b[token] for token in a.keys() & b.keys()):
        return True
    for column in first.claims & second.claims:
        # Sharing is licensed only when the bundles include the same original
        # occurrence, as an explicit alias/repeat does. A source number alone
        # is not evidence that two unrelated RV words refer to the same thing.
        if not any(a[t] == b[t] for t in a.keys() & b.keys()):
            return True
    return False


def select_candidates(candidates, anchors=()):
    """Resolve all providers together; ties abstain instead of choosing first.

    Contextual alignment has priority 3, explicit annotation evidence 2, and
    unique lexical recovery 1. Equal-priority conflicting bundles both wait
    for more evidence. The same policy applies on every refinement round.
    """
    accepted = list(anchors)
    selected = []
    for priority in sorted({c.priority for c in candidates}, reverse=True):
        eligible = [c for c in candidates if c.priority == priority
                    and not any(conflicts(c, old) for old in accepted)]
        winners = [c for i, c in enumerate(eligible)
                   if not any(conflicts(c, other) for j, other in enumerate(eligible) if i != j)]
        accepted.extend(winners)
        selected.extend(winners)
    return selected


class Evidence:
    """Passage-local cached scores shared by alignment and lexical recovery."""
    def __init__(self, columns, lexical_score, normalise, number_variants, directional_index=None):
        self.columns = columns
        self.lexical_score = lexical_score
        self.normalise = normalise
        self.number_variants = number_variants
        self.directional_index = directional_index or {}
        self.names = defaultdict(set)
        for col in columns:
            for spelling in (col.text, *col.text.split('/')):
                self.names[spelling].update(col.names)
        self.cache = {}
        self.word_cache = {}
        self.location_cache = {}

    def lexical(self, rv, lv):
        key = rv, lv
        if key not in self.cache:
            score = self.lexical_score(rv, lv)
            if (rv[:1].isupper() and self.normalise(rv) in self.names.get(lv, ())
                    and (score is None or score[1] < 110)):
                # Reviewed name spellings are especially useful clause anchors.
                # A generic "sons" must not displace a second named person in
                # a genealogy just because the possessive moved before it.
                score = ('proper name', 110)
            self.cache[key] = score
        return self.cache[key]

    def word(self, token, col):
        # Existing numbers/offsets do not affect lexical evidence. Cache within
        # this passage only, so virtual-anchor refinement reuses the scores.
        key = token.text, token.code, col
        if key in self.word_cache:
            return self.word_cache[key]
        scores = [self.lexical(token.text, w) for w in (col.text, *col.text.split('/'))]
        if token.code == '#' and col.noun:
            variants = self.number_variants(self.normalise(token.text))
            if any(self.normalise(w) in variants for w in col.text.split('/') if w.islower()):
                scores.append(('marked number change', 95))
        score = max((s for s in scores if s), key=lambda s: s[1], default=None)
        self.word_cache[key] = score
        return score

    def locations(self, token, number):
        key = token.text, token.code, number
        if key in self.location_cache:
            return self.location_cache[key]
        scored = [(self.word(token, col), j) for j, col in enumerate(self.columns) if col.number == number]
        best = max((s[1] for s, _ in scored if s), default=0)
        positions = frozenset(j for s, j in scored if (s[1] if s else 0) == best)
        self.location_cache[key] = positions
        return positions


def unique_word_candidates(tokens, evidence, bound_context=True):
    """Recover mutual unique lexical matches, counting linked occurrences too.

    Related forms, pronoun substitutions and contraction subjects require
    alignment context. They cannot justify a verse-wide jump. All alternatives
    compete by evidence strength on both sides, never by row order in a
    synonym table. A weaker inflection cannot veto another occurrence's exact
    spelling, but equally strong occurrences remain ambiguous.
    """
    choices, owners, strengths = {}, defaultdict(set), {}
    for token in tokens:
        if not token.linkable or token.code in SEMANTIC_CODES | {'!', '≡'}:
            continue
        scored = [(score, j) for j, col in enumerate(evidence.columns)
                  if (score := evidence.word(token, col))
                  and (score[1] >= 90 or score[0] == 'directional word mapping'
                       or any(w.casefold() in evidence.directional_index.get(token.match_text.casefold(), ())
                              for w in (col.text, *col.text.split('/'))))]
        if not scored:
            continue
        best = max(s[1] for s, _ in scored)
        positions = frozenset(j for s, j in scored if s[1] == best)
        for j in positions:
            if best > strengths.get(j, 0):
                strengths[j] = best
                owners[j] = {token}
            elif best == strengths[j]:
                owners[j].add(token)
        choices[token] = positions
    for token, positions in choices.items():
        if token.number is not None or len({evidence.columns[j].number for j in positions}) != 1:
            continue
        if any(owners[j] != {token} for j in positions):
            continue
        number = evidence.columns[next(iter(positions))].number
        # Function words are especially prone to borrowing a verb/article from
        # a different clause. They need an ordered, unoccupied anchor window.
        if bound_context and token.match_text.casefold() in MOVEMENT_FUNCTION_WORDS | CONTEXTUAL_HEADS:
            i = tokens.index(token)
            left = next((t for t in reversed(tokens[:i]) if t.linkable and t.number is not None), None)
            right = next((t for t in tokens[i+1:] if t.linkable and t.number is not None), None)
            lo = min(evidence.locations(left, left.number), default=-1) if left else -1
            hi = max(evidence.locations(right, right.number), default=len(evidence.columns)) if right else len(evidence.columns)
            if not all(lo <= j <= hi for j in positions):
                continue
            if any(t.number == number and t not in (left, right) for t in tokens):
                continue
        yield Candidate(((token, number),), positions, 'unique lexical candidate')


def alias_candidates(tokens, evidence):
    """Link a traditional ! spelling with its immediately preceding name.

    Numbered originals can identify otherwise unknown traditional spellings.
    Other add spans and punctuation stop the backward name scan. Ambiguous
    names never borrow an arbitrary earlier person's number.
    """
    spans = defaultdict(list)
    for i, token in enumerate(tokens):
        if token.code == '!':
            spans[token.span].append(i)
    for indexes in spans.values():
        before = []
        for token in reversed(tokens[max(0, indexes[0]-4):indexes[0]]):
            if token.code is not None or not token.text[:1].isupper() or token.boundary_after:
                break
            before.insert(0, token)
            if token.boundary_before:
                break
        aliases = [tokens[i] for i in indexes if tokens[i].text[:1].isupper()]
        group = before + aliases
        if not before or not aliases or all(t.number is not None for t in group):
            continue
        choices = {}
        for t in group:
            numbers = {col.number for col in evidence.columns if evidence.normalise(t.text) in col.names}
            choices[t] = {t.number} if t.number is not None else numbers
        known = {next(iter(ns)) for ns in choices.values() if len(ns) == 1}
        existing = {t.number for t in group if t.number is not None}
        if len(existing) == 1 and known <= existing:
            # The original explicitly licenses an unrecognised alias. It must
            # itself belong to a proper-name column in this mapped passage.
            number = next(iter(existing))
            if not any(col.number == number and col.names for col in evidence.columns):
                continue
            choices = {t: {number} if not ns or number in ns else ns for t, ns in choices.items()}
        if any(len(ns) != 1 for ns in choices.values()):
            continue
        bindings = tuple((t, next(iter(ns))) for t, ns in choices.items())
        # An unfamiliar traditional spelling still denotes the name, not an
        # attached "and/from/of" gloss sharing that Hebrew/Greek source ID.
        # Otherwise a correctly linked conjunction blocks its own name's alias.
        claims = frozenset(j for t, n in bindings for j in evidence.locations(t, n)
                           if evidence.columns[j].names)
        yield Candidate(bindings, claims, 'traditional name alias', 2)


def phrase_candidates(units, evidence, phrase_index):
    """Propose whole curated phrases, including partially linked occurrences.

    The positional graph handles ordinary phrase alignment. These candidates
    recover a unique reordered phrase or complete a compatible saved phrase;
    all ambiguous alternatives are passed to the shared conflict resolver.
    """
    for i, end_i, j, end_j, _ in phrase_edges(units, evidence.columns, phrase_index, set()):
        number = evidence.columns[j].number
        tokens = [t for unit in units[i:end_i] for t in unit]
        if all(t.number is not None for t in tokens) or any(t.number not in (None, number) for t in tokens):
            continue
        yield Candidate(tuple((t, number) for t in tokens), frozenset(range(j,end_j)),
                        'curated phrase', 2 if any(t.number is not None for t in tokens) else 1)


def existing_claims(units, evidence, phrase_index):
    """Expose saved whole-phrase and proven gloss ownership to every provider.

    Contraction subjects reserve their explicit pronoun even though their score
    is weaker than an exact match. Use the alignment graph's same ownership rule.
    """
    positions = defaultdict(list)
    for j, col in enumerate(evidence.columns):
        positions[col.number].append(j)
    owners = linked_phrase_columns(units, evidence.columns, positions, phrase_index)
    for row, unit in enumerate(units):
        for t in unit:
            if not t.linkable or t.number is None:
                continue
            if row in owners:
                yield Candidate(((t,t.number),), frozenset(owners[row]), 'saved phrase', 4)
            elif t.code not in SEMANTIC_CODES | {'!', '≡'} and any(
                    (score := evidence.word(t, col))
                    and (score[1] >= 90 or score[0] == 'contraction subject')
                    for col in evidence.columns if col.number == t.number):
                yield Candidate(((t,t.number),), evidence.locations(t, t.number), 'existing link', 4)


def repeat_candidates(tokens, evidence):
    """Repeat only an identifiable earlier phrase in this mapped passage.

    Preserve each original word's number; a repeated multiword expression may
    translate several source words and must not inherit just the first one.
    """
    spans = defaultdict(list)
    for i, token in enumerate(tokens):
        if token.code == '≡':
            spans[token.span].append(i)
    for indexes in spans.values():
        phrase = [tokens[i] for i in indexes]
        if all(t.number is not None for t in phrase):
            continue
        words = [evidence.normalise(t.text) for t in phrase]
        originals = [tokens[i:i+len(phrase)] for i in range(indexes[0]-len(phrase)+1)
                     if all(t.linkable and t.number is not None and t.code != '≡' for t in tokens[i:i+len(phrase)])
                     and [evidence.normalise(t.text) for t in tokens[i:i+len(phrase)]] == words]
        if not originals or len({tuple(t.number for t in original) for original in originals}) != 1:
            continue
        original = originals[-1]
        if any(t.number is not None and t.number != o.number for t, o in zip(phrase, original)):
            continue
        bindings = tuple((t, t.number) for t in original) + tuple((t, o.number) for t, o in zip(phrase, original))
        claims = frozenset(j for t in original for j in evidence.locations(t, t.number))
        if claims:
            yield Candidate(bindings, claims, 'explicit same-verse repeat', 2)


def select_links(tokens, columns, lexical_score, normalise, number_variants,
                 reversed_clauses=False, phrase_index=None, directional_index=None):
    """Return accepted links using original offsets, with no text mutation.

    All providers see the same snapshot each round. Accepted links become
    virtual anchors for the next round; each productive round consumes at
    least one unnumbered occurrence. Working storage is bounded by one passage.
    """
    originals = {(t.line, t.start): t for t in tokens}
    live = list(tokens)
    evidence = Evidence(columns, lexical_score, normalise, number_variants, directional_index)
    result = {}
    while True:
        indexes = {t: i for i, t in enumerate(live)}
        units = alignment_units(live)
        candidates = list(unique_word_candidates(live, evidence))
        candidates.extend(phrase_candidates(units, evidence, phrase_index))
        candidates.extend(alias_candidates(live, evidence))
        candidates.extend(repeat_candidates(live, evidence))
        anchors = list(existing_claims(units, evidence, phrase_index))
        # A marked clause swap needs lexical/name anchors before its rotation
        # can be inferred. Never bootstrap it by assuming the original order.
        anchored = [t for t in live if t.linkable and t.number is not None]
        if not reversed_clauses or len(anchored) >= 3:
            proposals = propose_links(live, columns, evidence.lexical, normalise,
                                      reversed_clauses, phrase_index, evidence.word)
            if proposals:
                # Keep adjacent words assigned to one source atomic. This
                # includes phrases such as "you all" and whole semantic spans.
                groups = []
                for t, n, reason in sorted(proposals, key=lambda p: (p[0].line, p[0].start)):
                    if groups and groups[-1][-1][1] == n and indexes[t] == live.index(groups[-1][-1][0])+1:
                        groups[-1].append((t, n, reason))
                    else:
                        groups.append([(t, n, reason)])
                candidates.extend(Candidate(tuple((t,n) for t,n,_ in group),
                    frozenset(j for t,n,_ in group for j in evidence.locations(t,n)),
                    group[0][2], 3) for group in groups)
        # The alignment solver has already checked ownership of saved anchors
        # per English column. Passing its whole bundle through a second coarse
        # ownership check would incorrectly reject other glosses of that word.
        # Include unique lexical witnesses outside the current anchor window
        # for vetoes only. If "was" is stranded by reordered "true", that still
        # does not license the later "been" to take its exact LV "was".
        strong = [candidate for candidate in unique_word_candidates(live, evidence, bound_context=False)
                  if all((score := evidence.word(t, columns[j])) and score[1] >= 90
                          for t, _ in candidate.bindings for j in candidate.claims)]
        whole_phrases = select_candidates([c for c in candidates if c.reason == 'curated phrase'], anchors)
        clause_fences = []
        if not reversed_clauses:
            for candidate in strong:
                token, _ = candidate.bindings[0]
                if (token.match_text.casefold() in {'and', 'but', 'or'} and token.boundary_before
                        and all(columns[j].boundary_before for j in candidate.claims)):
                    clause_fences.append((indexes[token], candidate.claims))
        def respects_stronger_evidence(candidate):
            for token, number in candidate.bindings:
                positions = evidence.locations(token, number)
                for boundary, fence in clause_fences:
                    if ((indexes[token] < boundary and min(positions) > max(fence))
                            or (indexes[token] > boundary and max(positions) < min(fence))):
                        return False
                if token.code in SEMANTIC_CODES:
                    continue
                score = max((s[1] for j in evidence.locations(token, number)
                             if (s := evidence.word(token, columns[j]))), default=0)
                if score < 90 and any(token in dict(phrase.bindings)
                                     and dict(phrase.bindings)[token] != number for phrase in whole_phrases):
                    # The meaning of a reviewed whole expression outweighs a
                    # weak match of one word ("does what's right" is moral
                    # righteousness, not an adjacent "makes straight").
                    return False
                for alternative in strong:
                    other, other_number = alternative.bindings[0]
                    if token == other and score < 90 and number != other_number:
                        return False
                    if (score < 90 and number != other_number
                            and other.match_text.casefold() in {'is', 'are', 'was', 'were', 'be', 'been'}
                            and indexes[other] == indexes[token]-1
                            and same_clause([other, token])):
                        # Let the stronger anchor settle before a weaker edge
                        # changes the order of the gap around it.
                        if max(positions) < min(alternative.claims):
                            return False
                    # A different occurrence's exact word is stronger evidence
                    # than this auxiliary's inflection ("was true ... been").
                    if token != other and candidate.claims & alternative.claims:
                        best = max(evidence.word(other, columns[j])[1] for j in alternative.claims)
                        if score < best:
                            return False
            return True
        contextual = [c for c in candidates if c.priority == 3 and respects_stronger_evidence(c)]
        proposed = {t: n for candidate in contextual for t, n in candidate.bindings}
        def complete_repeated_alternative(candidate):
            for token, number in candidate.bindings:
                if token.code in SEMANTIC_CODES:
                    continue
                score = max((s[1] for j in evidence.locations(token, number)
                             if (s := evidence.word(token, columns[j]))), default=0)
                if score >= 90:
                    continue
                copies = [t for t in live if t.linkable and t.match_text.casefold() == token.match_text.casefold()]
                alternatives = {col.number for col in columns if evidence.word(token, col)}
                if len(copies) > 1 and len(alternatives) > 1 and any(
                        t.number is None and t not in proposed for t in copies):
                    i = indexes[token]
                    # An immediately aligned neighbour still identifies local
                    # phrases such as "from glory to glory", even if a third
                    # occurrence elsewhere in the verse remains unresolved.
                    if not any(0 <= i+step < len(live) and live[i+step].number is not None
                               and same_clause(live[min(i,i+step):max(i,i+step)+1])
                               and any(j+step in evidence.locations(live[i+step], live[i+step].number)
                                       for j in evidence.locations(token, number))
                               for step in (-1, 1)):
                        return False
            return True
        # A partial ordered path is insufficient for repeated weak alternatives
        # in reordered phrases: the second "metres" must not take the first
        # "cubits" while the first "metres" has no match at all.
        contextual = [candidate for candidate in contextual if complete_repeated_alternative(candidate)]
        selected = contextual + select_candidates([c for c in candidates if c.priority != 3], anchors + contextual)
        # Validate function words against the content anchors selected in THIS
        # round too. Keep a compatible joint alignment intact: discarding all
        # function proposals would throw away its all-optimal-path evidence.
        # A provisional "are" must not take a later exact "are" while its own
        # "given" is simultaneously becoming an anchor in an earlier clause.
        content = [c for c in selected if any(t.number is None
                   and t.code not in SEMANTIC_CODES
                   and t.match_text.casefold() not in MOVEMENT_FUNCTION_WORDS
                   for t, _ in c.bindings)]
        if content:
            fixed = {i: t.number for i, t in enumerate(live) if t.linkable and t.number is not None}
            fixed.update((indexes[t], n) for c in content for t, n in c.bindings)
            def fits_content(candidate):
                generic_head = any(t.match_text.casefold() in CONTEXTUAL_HEADS for t, _ in candidate.bindings)
                if (candidate in content and not generic_head) or candidate.reason in {
                        'curated phrase', 'traditional name alias', 'explicit same-verse repeat'}:
                    return True
                rows = [indexes[t] for t, _ in candidate.bindings]
                left = max((i for i in fixed if i < min(rows)), default=None)
                right = min((i for i in fixed if i > max(rows)), default=None)
                neighbours = {fixed[i] for i in (left, right) if i is not None}
                distant = set(fixed.values()) - neighbours
                for token, number in candidate.bindings:
                    if number in distant and not any(
                            owner_number == number and same_clause(live[min(indexes[token],owner):max(indexes[token],owner)+1])
                            for owner, owner_number in fixed.items()):
                        return False
                if candidate.priority == 3 and not generic_head:
                    return True  # Preserve the graph's joint positional evidence.
                if reversed_clauses:
                    return False  # Stabilise lexical/name anchors before recovery.
                lo = min(evidence.locations(live[left], fixed[left]), default=-1) if left is not None else -1
                hi = max(evidence.locations(live[right], fixed[right]), default=len(columns)) if right is not None else len(columns)
                return any(lo <= j <= hi for j in candidate.claims)
            selected = [c for c in selected if fits_content(c)]
        # A copula inside an LV content gloss needs its following RV predicate.
        # This also prevents a measurement's "was" from borrowing another
        # measurement's "+was_cubits".
        # An article/possessive belongs to its own adjacent head, not any
        # surviving article inside a large alignment gap. In "the benefits ...
        # advice", LV "the counsel" cannot supply "the benefits". A following
        # content anchor also disambiguates "its foundations" from "its height".
        assigned = {t: t.number for t in live if t.linkable and t.number is not None}
        assigned.update((t, n) for candidate in selected for t, n in candidate.bindings)
        def has_head(candidate):
            if candidate.reason in {'curated phrase', 'traditional name alias', 'explicit same-verse repeat'}:
                return True
            for token, number in candidate.bindings:
                if token.code is None and token.match_text.casefold() == 'who':
                    head = next((t for t in live[indexes[token]+1:]
                                 if t.linkable and t.match_text.casefold() not in MOVEMENT_FUNCTION_WORDS), None)
                    if head is not None and head in assigned:
                        # A later relative clause's "who" cannot supply the
                        # English expansion of an earlier adjective/participle.
                        predicates = [next((col for col in columns[j+1:]
                                            if col.text.casefold() not in MOVEMENT_FUNCTION_WORDS), None)
                                      for j in evidence.locations(token, number)]
                        if not any(col is not None and col.number == assigned[head] for col in predicates):
                            return False
                if (token.code not in SEMANTIC_CODES
                        and token.match_text.casefold() in {'and', 'or', 'but'}
                        and any(col.number == number and col.noun
                                and col.text.casefold() not in MOVEMENT_FUNCTION_WORDS for col in columns)
                        and any(n == number and t.match_text.casefold() not in MOVEMENT_FUNCTION_WORDS
                                for t, n in assigned.items())):
                    head = next((t for t in live[indexes[token]+1:] if t.linkable
                                 and t.match_text.casefold() not in MOVEMENT_FUNCTION_WORDS), None)
                    if head is None or assigned.get(head) != number:
                        return False
                if (token.code not in SEMANTIC_CODES
                        and token.match_text.casefold() in {'is', 'are', 'was', 'were', 'be', 'been', 'being'}
                        and any(col.number == number and col.text.casefold() not in MOVEMENT_FUNCTION_WORDS
                                for col in columns)):
                    # An auxiliary inside a source gloss belongs to that
                    # predicate, not a nearby relative phrase: "who are poor
                    # are blessed" must not lend blessed's "are" to poor.
                    head = next((t for t in live[indexes[token]+1:]
                                 if t.match_text.casefold() not in MOVEMENT_FUNCTION_WORDS), None)
                    if (head is None or assigned.get(head) != number
                            or not same_clause(live[indexes[token]:indexes[head]+1])):
                        return False
                if token.code is not None or token.match_text.casefold() not in {
                        'the', 'a', 'an', 'its', 'my', 'your', 'his', 'her', 'our', 'their'}:
                    continue
                if not (any(n == number and t.match_text.casefold() not in MOVEMENT_FUNCTION_WORDS
                            for t, n in assigned.items())
                        or (token.match_text.casefold() in {'its', 'my', 'your', 'his', 'her', 'our', 'their'}
                            and any(col.number == number and col.noun for col in columns))):
                    continue  # No competing head has been established yet.
                following = live[indexes[token]+1:]
                head = next((t for t in following if t.linkable), None)
                if head is None or not same_clause(live[indexes[token]:indexes[head]+1]):
                    return False
                if head not in assigned:
                    return False
                if assigned[head] == number:
                    continue
                if (token.match_text.casefold() in {'its', 'my', 'your', 'his', 'her', 'our', 'their'}
                        and any(col.number == number and col.noun for col in columns)):
                    return False  # A noun's suffix cannot possess the next noun.
                if not any(0 < k-j <= 3
                           and all(col.text.casefold() in MOVEMENT_FUNCTION_WORDS for col in columns[j+1:k])
                           for j in evidence.locations(token, number)
                           for k in evidence.locations(head, assigned[head])):
                    return False
            return True
        selected = [candidate for candidate in selected if has_head(candidate)]
        additions = {}
        for candidate in sorted(selected, key=lambda c: (-c.priority, c.reason,
                                tuple((t.line,t.start,n) for t,n in c.bindings))):
            for t, number in candidate.bindings:
                if t.number is None and (t.line, t.start) not in additions:
                    additions[t.line, t.start] = number
                    original = originals[t.line, t.start]
                    result[t.line, t.start] = original, number, candidate.reason
        if not additions:
            return [result[key] for key in sorted(result)]
        live = [replace(t, number=additions[t.line, t.start]) if (t.line, t.start) in additions else t for t in live]
