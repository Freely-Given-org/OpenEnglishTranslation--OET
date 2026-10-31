# SPDX-License-Identifier: MPL-2.0
"""Destination-aware OET navigation. Word filenames/IDs always stay native."""
from functools import lru_cache
from html import escape, unescape
from pathlib import Path
import re
import logging

from BibleOrgSys.Reference.BibleVersificationMappings import get_default_mapping_engine, MappingStatus, VersificationMappingError
from BibleOrgSys.Reference.BibleVersificationSystems import BibleVersificationSystem


@lru_cache(maxsize=65536)
def link_targets(source, target, book, chapter, verse):
    if verse is None:
        count = BibleVersificationSystem(source).getNumVerses(book, chapter)
        refs = tuple((book,chapter,str(v),None) for v in range(1,count+1))
    else:
        refs = ((book,chapter,verse,None),)
    result = get_default_mapping_engine().convert_passage(source, target, refs)
    if result.status != MappingStatus.EXACT:
        if result.diagnostics and all(d.code == 'NO_REFERENCE_COUNTERPART' for d in result.diagnostics):
            return ()
        raise VersificationMappingError(result)
    if verse is not None:
        return result.references
    # A chapter link visits the beginning of each mapped chapter portion.
    seen, targets = set(), []
    for ref in result.references:
        if ref[:2] not in seen:
            seen.add(ref[:2]); targets.append(ref)
    return tuple(targets)


def scripture_link(source, target, book, chapter, verse, label):
    source_ref = f'{book} {chapter}' + (f':{verse}' if verse is not None else '')
    unavailable = f'reference alignment unavailable in {target}'
    try:
        targets = link_targets(source,target,book,str(chapter),str(verse) if verse is not None else None)
    except VersificationMappingError as error:
        # Preserve bad upstream dictionary citations as labelled prose, without
        # inventing a correction or breaking every person/location page.
        if source != 'KJV' or error.result.status != MappingStatus.INVALID:
            raise
        targets = ()
        unavailable = f'invalid KJV reference: {source_ref}'
        logging.warning('Theographic citation %s: %s', source_ref, error)
    links = []
    if not targets:
        links.append(escape(label) + f' ({escape(unavailable)})')
    for i,(b,c,v,s) in enumerate(targets):
        caption = label if i == 0 else f'{b} {c}:{v}{s or ""}'
        links.append(f'<a href="../{b}.html#C{c}V{v}{s or ""}" '
                     f'title="{escape(target)} {b} {c}:{v}{s or ""}">{escape(caption)}</a>')
    return (f'<span class="scriptureLink" data-source-system="{escape(source)}" '
            f'data-source-ref="{source_ref}" data-source-label="{escape(label, quote=True)}">'
            + ' / '.join(links) + '</span>')


ANNOTATED = re.compile(r'<span class="scriptureLink" data-source-system="([^"]+)" data-source-ref="(\w{3}) (\d+)(?::(\d+))?" data-source-label="([^"]*)">.*?</span>', re.S)
NATIVE = re.compile(r'<a\b[^>]*\bhref="\.\./(\w{3})\.html#C(\d+)(?:V(\d+))?"[^>]*>(.*?)</a>', re.S)


def retarget_links(html, target):
    """Copy LV word/lemma/person pages without copying their navigation system.

    Annotated Theographic links retain the original KJV coordinate, so later
    copies do not lose provenance through an intermediate merged LV passage.
    Legacy unannotated native backlinks are interpreted as OET-LV.
    """
    preserved = []
    def annotated(m):
        preserved.append(scripture_link(unescape(m[1]),target,m[2],m[3],m[4],unescape(m[5])))
        return f'@@OET_SCRIPTURE_LINK_{len(preserved)-1}@@'
    html = ANNOTATED.sub(annotated,html)
    def native(m):
        return scripture_link('OET-LV',target,m[1],m[2],m[3],unescape(re.sub('<[^>]+>','',m[4])))
    html = NATIVE.sub(native,html)
    for i,link in enumerate(preserved):
        html = html.replace(f'@@OET_SCRIPTURE_LINK_{i}@@',link)
    return html


def copy_reference_pages(source, destination, target='OET-RV'):
    count = 0
    for folder, pattern in (('W','*.html'),('Lm','*.html'),('Pe','P_*.html'),('Loc','L_*.html')):
        output = Path(destination)/folder
        output.mkdir(parents=True,exist_ok=True)
        for path in (Path(source)/folder).glob(pattern):
            (output/path.name).write_text(retarget_links(path.read_text(encoding='utf-8'),target),encoding='utf-8')
            count += 1
    return count
