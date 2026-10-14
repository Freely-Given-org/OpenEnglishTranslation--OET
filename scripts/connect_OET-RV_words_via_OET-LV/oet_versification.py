# SPDX-License-Identifier: MPL-2.0
"""Resolve complete RV (eng) passages to LV (org) text through BibleOrgSys.

The matcher writes using *printed RV* addresses and character offsets. BOS
alone converts scripture addresses. A stored RV bridge is one matching unit;
complete mapping groups and shared LV bridges are coalesced before matching.
Non-exact mappings or missing text never fall back to same-number verses.
"""
from dataclasses import asdict, dataclass
import re

from BibleOrgSys.Internals.InternalBiblePassages import passageReferencesFromEntries
from BibleOrgSys.Reference.BibleVersificationMappings import MappingResult, MappingStatus, VersificationMappingError
from oet_alignment import index_book_lines


@dataclass
class AlignmentPassage:
    key: tuple[int, int]  # First printed RV address (0 denotes a separate title).
    lines: tuple[tuple[int, int], ...]
    rv_references: tuple
    lv_references: tuple
    lv_entries: list
    mapping: MappingResult

    def metadata(self):
        return dict(rv_references=self.rv_references, lv_references=self.lv_references,
                    mapping=asdict(self.mapping))


def _indexed_references(BBB, lines, index):
    """Expand stored numeric labels without manufacturing missing verses."""
    references = {}
    for (c, v), locations in index.items():
        label = lines[locations[0][0]].split(' ', 2)[1] if v else '0'
        if not re.fullmatch(r'\d+(?:-\d+)?', label):
            raise ValueError(f'Unsupported verse label {BBB} {c}:{label}')
        end = int(label.split('-')[-1])
        if end < v:
            raise ValueError(f'Reversed verse bridge {BBB} {c}:{label}')
        references[c, v] = tuple((BBB, str(c), str(n), None) for n in range(v, end+1))
    return references


def audit_unmapped_lv(BBB, rv, lv, lv_lines, passages):
    """Expose source text omitted even when every RV mapping reports exact.

    A draft mapping can return only one part of a split/merged verse. Audit
    native LV storage as well as requested RV references so this is visible.
    An inverse result is diagnostic only; it never expands a matching passage.
    """
    used = {ref for passage in passages for ref in passage.lv_references}
    native = _indexed_references(BBB, lv_lines, index_book_lines(lv_lines))
    return [dict(lv_reference=ref,
                 mapping=asdict(rv.convertReferencesFromVersification(lv, (ref,))))
            for refs in native.values() for ref in refs if ref not in used]


def resolve_alignment_passages(BBB, rv, lv, lines):
    """Return (passages, skipped) in RV text order, without editing either Bible.

    A pre-verse ``d`` field belongs to verse 1 when BOS does not declare a
    separate title address in the RV profile (e.g. Psalm 11). Otherwise it is
    its own verse-zero passage (e.g. Psalm 3). This is a storage distinction,
    not a guessed Psalm offset. Mapping and retrieval are cached per book and
    reused across all matching passes; no chapter cache survives this call.

    Group expansion is permitted only by BOS's explicit incomplete-group
    diagnostics, exact inverse mappings of stored LV bridges, or shared LV
    storage. Every expanded group is converted again as a complete request.
    """
    index = index_book_lines(lines)
    references = _indexed_references(BBB, lines, index)

    for c, v in tuple(index):
        if v != 0 or (c, 1) not in index:
            continue
        result = rv.convertReferencesToVersification(lv, references[c, 0])
        if result.diagnostics and all(d.code == 'UNDECLARED_TITLE' and d.system == result.source_system
                                      for d in result.diagnostics):
            index[c, 1] = index.pop((c, 0)) + index[c, 1]
            del references[c, 0]

    # Components only grow, so resolution terminates even for cyclic bridges.
    keys = sorted(index, key=lambda k: index[k][0][0])
    parent = {k: k for k in keys}
    owners = {ref: key for key in keys for ref in references[key]}
    cache, chapter_cache = {}, {}

    def root(key):
        while parent[key] != key:
            parent[key] = parent[parent[key]]
            key = parent[key]
        return key

    def merge(key, required):
        if not required or any(ref not in owners for ref in required):
            return False
        other_roots = {root(owners[ref]) for ref in required} - {root(key)}
        for other in other_roots:
            parent[other] = root(key)
        return bool(other_roots)

    while True:
        groups = {}
        for key in keys:
            groups.setdefault(root(key), []).append(key)
        changed, passages, skipped, target_owners = False, [], [], {}
        for group in groups.values():
            key = group[0]
            refs = tuple(dict.fromkeys(ref for member in group for ref in references[member]))
            locations = tuple(sorted({location for member in group for location in index[member]}))
            if refs not in cache:
                try:
                    cache[refs] = lv.getMappedPassage(rv, refs, chapterCache=chapter_cache)
                except (VersificationMappingError, KeyError) as error:
                    cache[refs] = error
            mapped = cache[refs]
            if isinstance(mapped, VersificationMappingError):
                result = mapped.result
                if result.status == MappingStatus.PARTIAL and result.diagnostics and all(
                        d.system == result.source_system and d.code in {
                            'INCOMPLETE_MAPPING_GROUP', 'INCOMPLETE_MERGED_VERSE'} for d in result.diagnostics):
                    required = tuple(ref for d in result.diagnostics for ref in d.references)
                    if merge(key, required):
                        changed = True
                        continue
                skipped.append(dict(rv_references=refs, status=result.status.value,
                                    mapping=asdict(result)))
                continue
            if isinstance(mapped, KeyError):
                skipped.append(dict(rv_references=refs, status='missing_lv_text',
                                    missing_reference=getattr(mapped, 'reference', None), message=str(mapped)))
                continue
            result = mapped.mapping
            if any(ref[0] != BBB for ref in result.references):
                skipped.append(dict(rv_references=refs, status='cross_book_mapping', mapping=asdict(result)))
                continue

            # Retrieval can return an entire stored LV bridge for a singleton
            # address. Include its RV counterparts before exposing that text.
            stored_refs = tuple(dict.fromkeys(ref for portion in mapped.portions
                for ref in passageReferencesFromEntries(portion.reference, portion.entries, lv)))
            if set(stored_refs) - set(result.references):
                inverse = rv.convertReferencesFromVersification(lv, stored_refs)
                if inverse.status == MappingStatus.EXACT and set(refs) <= set(inverse.references) \
                        and merge(key, inverse.references):
                    changed = True
                    continue
                skipped.append(dict(rv_references=refs, status='incomplete_lv_storage',
                                    lv_stored_references=stored_refs, mapping=asdict(result)))
                continue
            for ref in result.references:
                if ref in target_owners and root(target_owners[ref]) != root(key):
                    changed |= merge(key, references[target_owners[ref]])
                target_owners[ref] = key
            passages.append(AlignmentPassage(key, locations, refs, result.references,
                [entry for portion in mapped.portions for entry in portion.entries], result))
        if not changed:
            return passages, skipped
