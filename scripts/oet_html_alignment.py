# SPDX-License-Identifier: MPL-2.0
"""Pair OET rendered sections using BOS passages; retain every native word link.

BOS maps/retrieves complete passages (including stored bridges). This module
owns only section coalescing and balanced slicing of the already-rendered HTML.
Missing text/anchors are errors, never a request to pick the next available one.
"""
from bisect import bisect_right
from functools import lru_cache
from html import escape
from pathlib import Path
import re

from BibleOrgSys.Formats.ESFMBible import ESFMBible
from BibleOrgSys.Reference.BibleVersificationMappings import get_default_mapping_engine, MappingStatus
from oet_exports import reference_label


@lru_cache(maxsize=2)
def load_lv(project, testament):
    folder = Path(project)/'derivedTexts'/('auto_edited_OT_ESFM' if testament=='OT' else 'auto_edited_VLT_ESFM')
    bible = ESFMBible(folder,givenAbbreviation='OET-LV',versification='OET-LV')
    bible.preload()
    return bible


VERSE_ID = re.compile(r'\bid="C(\d+)V(\d+)(?:-(\d+))?"')
TOKEN = re.compile(r'''<!--.*?-->|</?(?:[^<>"']|"[^"]*"|'[^']*')+>''',re.S)
VOID = {'br','hr','img','input','meta','link','wbr','area','base','col','embed','param','source','track'}


class NativeHTML:
    """Index exact native anchors and retain formatting across verse boundaries."""
    def __init__(self, book, html):
        self.book,self.html = book,html
        self.positions,self.stacks = [0],[()]
        self.anchors = {}
        stack = []
        chapter_starts = {}
        for token in TOKEN.finditer(html):
            text = token[0]
            if text.startswith('<!--'):
                continue
            match = re.match(r'<(/?)([\w]+)',text)
            if not match:
                raise ValueError(f'{book}: invalid rendered HTML token {text!r}')
            closing,tag = match.groups(); tag=tag.lower()
            if closing:
                if not stack or stack[-1][0] != tag:
                    raise ValueError(f'{book}: unbalanced HTML at {token.start()}: {text}')
                stack.pop()
            else:
                chapter = re.search(r'\bid="C(\d+)"',text)
                if chapter:
                    chapter_starts[chapter[1]] = token.start()
                verse = VERSE_ID.search(text)
                if verse:
                    c,first,last = verse.groups()
                    start = chapter_starts.get(c,token.start()) if first=='1' else token.start()
                    for v in range(int(first),int(last or first)+1):
                        ref=(book,c,str(v),None)
                        if ref in self.anchors:
                            raise ValueError(f'{book}: duplicate native HTML anchor {ref}')
                        self.anchors[ref]=start
                if tag not in VOID and not text.endswith('/>'):
                    stack.append((tag,text))
            self.positions.append(token.end()); self.stacks.append(tuple(stack))
        if stack:
            raise ValueError(f'{book}: unclosed HTML tags {stack!r}')
        self.starts = sorted(set(self.anchors.values()))
        self.ends = {p:self.starts[i+1] if i+1<len(self.starts) else len(html) for i,p in enumerate(self.starts)}

    def stack_at(self, position):
        return self.stacks[bisect_right(self.positions,position)-1]

    def slice(self, start, end):
        # Reopened containers have no duplicated anchor IDs. Inner verse/word
        # markup is copied verbatim; no word is split or identifier renumbered.
        prefix=''.join(re.sub(r'\s+id="[^"]*"','',text) for tag,text in self.stack_at(start))
        suffix=''.join(f'</{tag}>' for tag,text in reversed(self.stack_at(end)))
        return prefix+self.html[start:end]+suffix

    def select(self, refs):
        missing=[ref for ref in refs if ref not in self.anchors]
        if missing:
            raise ValueError(f'OET-LV {self.book}: mapped native anchors missing from HTML: {missing}; regenerate simple HTML')
        starts=sorted({self.anchors[ref] for ref in refs})
        ranges=[]
        for start in starts:
            end=self.ends[start]
            if ranges and ranges[-1][1]==start:
                ranges[-1]=(ranges[-1][0],end)
            else:ranges.append((start,end))
        return '\n'.join(self.slice(a,b) for a,b in ranges)


def add_title_anchors(book, html, profile='OET-RV'):
    """Attach unnumbered d headings to BOS-declared title coordinates only."""
    if book != 'PSA':return html
    pattern=re.compile(r'<p class="d">')
    def replace(match):
        next_verse=VERSE_ID.search(html,match.end())
        if next_verse is None or next_verse[2]!='1':
            raise ValueError(f'{profile} {book}: title without following verse 1')
        c=next_verse[1]
        result=get_default_mapping_engine().convert(profile,profile,[(book,c,0)])
        if result.status==MappingStatus.EXACT:
            return f'<p class="d" id="C{c}V0">'
        return match[0] # A title stored inside verse 1 is not a separate verse.
    return pattern.sub(replace,html)


def align_sections(book, rv_html, lv_html, lv_bible):
    """Return (RV HTML, LV HTML) pairs, coalescing sections sharing whole text."""
    rv_html=add_title_anchors(book,rv_html)
    # Strip the common outer wrapper; every output chunk is balanced itself.
    def body(html):
        return html.removeprefix('<div class="BibleText">').removesuffix('\n').removesuffix('</div><!--BibleText-->').strip()
    rv_html,lv_html=body(rv_html),body(lv_html)
    rv_index,lv_index=NativeHTML(book,rv_html),NativeHTML(book,lv_html)
    cuts=[0]+[m.start() for m in re.finditer('<div class="rightS1Box">',rv_html) if m.start()>0]+[len(rv_html)]
    if book == 'PSA':
        # Individual Psalm exports need chapter boundaries even when the RV
        # has no new section heading there. Titles belong to their own Psalm.
        first_by_chapter = {}
        for ref,pos in rv_index.anchors.items():
            first_by_chapter.setdefault(ref[1],pos)
        for c,pos in first_by_chapter.items():
            previous_cut=max(cut for cut in cuts if cut<=pos)
            if any(previous_cut<=p<pos for p in rv_index.anchors.values()):
                cuts.append(pos)
        cuts=sorted(set(cuts))
    groups=[(a,b) for a,b in zip(cuts,cuts[1:])]
    cache={}
    while True:
        owners={ref:i for i,(a,b) in enumerate(groups) for ref,pos in rv_index.anchors.items() if a<=pos<b}
        passages=[]; merge_range=None; target_owners={}
        for i,(a,b) in enumerate(groups):
            refs=tuple(ref for ref,pos in rv_index.anchors.items() if a<=pos<b)
            if not refs:
                passages.append(None);continue
            passage=lv_bible.getMappedPassage('OET-RV',refs,expandGroups=True,allowAbsent=True,chapterCache=cache)
            passages.append(passage)
            missing=set(passage.mapping.source_references)-owners.keys()
            if missing:
                raise ValueError(f'OET-RV {book}: mapped passage requires absent HTML addresses {missing}')
            required={i}|{owners[ref] for ref in passage.mapping.source_references}
            for ref in passage.native_references:
                if ref in target_owners:required.add(target_owners[ref])
                target_owners[ref]=i
            if len(required)>1:
                merge_range=min(required),max(required);break
        if merge_range is None:break
        first,last=merge_range
        groups[first:last+1]=[(groups[first][0],groups[last][1])]
    result=[];used=set()
    for (a,b),passage in zip(groups,passages,strict=True):
        rv=rv_index.slice(a,b)
        if passage is None:
            result.append((rv,''));continue
        native=passage.native_references;used.update(native)
        lv=lv_index.select(native)
        refs=passage.mapping.source_references
        if tuple(refs)!=tuple(native) and native:
            label = (f'Corresponding passage: OET-RV {reference_label(refs)}; '
                     f'OET-LV {reference_label(native)}. Complete verses are shown together.')
            lv = '<p class="verseAlignment">'+escape(label)+'</p>'+lv
        if passage.absent_source_references:
            absence = reference_label(passage.absent_source_references)
            lv = f'<p class="verseAlignment">No OET-LV counterpart for OET-RV {escape(absence)}.</p>' + lv
        result.append((rv,lv))
    missing=set(lv_index.anchors)-used
    if missing:
        raise ValueError(f'OET-LV {book}: rendered verses left unpaired: {sorted(missing)}')
    return result


def render_editorial_brackets(html):
    """Render paired editorial brackets; leave source typos visible as text.

    An unmatched ] must not become a closing span. Ignore attribute contents,
    which may contain punctuation and markup used only as tooltip text.
    """
    stack, pairs = [], {}
    position = 0
    for token in list(TOKEN.finditer(html)) + [None]:
        end = token.start() if token else len(html)
        for match in re.finditer(r'[\[\]]',html[position:end]):
            offset = position+match.start()
            if match[0]=='[':stack.append(offset)
            elif stack:
                start=stack.pop();pairs[start]='<span class="add">';pairs[offset]='</span>'
        position=token.end() if token else end
    if not pairs:return html
    result=[];position=0
    for offset,replacement in sorted(pairs.items()):
        result.extend((html[position:offset],replacement));position=offset+1
    return ''.join(result)+html[position:]
