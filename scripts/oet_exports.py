# SPDX-License-Identifier: MPL-2.0
"""OET plain-text export policy; BOS owns mapping and scripture retrieval.

VREF keeps one output line per input reference. An indivisible passage is
repeated, explicitly labelled, at each affected coordinate. The JSON sidecar
records requested/native coverage. Native VPL emits stored bridges once at
their first address, with the same label and full coverage in the sidecar.
Neither exporter changes source entries or word identifiers.
"""
from BibleOrgSys.Internals.InternalBiblePassages import passageReferencesFromEntries
from BibleOrgSys.BibleOrgSysGlobals import BOOKLIST_66


def reference_label(refs):
    """Compress only consecutive native addresses; never hide disjoint gaps."""
    runs = []
    for b,c,v,s in refs:
        if runs and not s and runs[-1][3] is None and runs[-1][:2] == (b,c) and int(v) == int(runs[-1][4])+1:
            runs[-1] = (*runs[-1][:4],v)
        else:
            runs.append((b,c,v,s,v))
    return ', '.join(f'{b} {c}:' + (f'{v}{s or ""}' if v==last else f'{v}-{last}')
                     for b,c,v,s,last in runs)


def render_entries(verseData, VV, BBB):
    verseText, firstWord = '', False
    for entry in verseData:
        marker, cleanText = entry.getMarker(), entry.getOriginalText()
        if cleanText and VV=='RV' and BBB=='PSA' and '\\z' in cleanText: # Psalm/Song colouring markers
            cleanText = cleanText.replace( '\\zr ', '' ).replace( '\\z1 ', '' ).replace( '\\z2 ', '' ).replace( '\\z3 ', '' ).replace( '\\z4 ', '' ) \
                        .replace( '\\zrhilite ', '' ).replace( '\\z1hilite ', '' ).replace( '\\z2hilite ', '' ).replace( '\\z3hilite ', '' ).replace( '\\z4hilite ', '' ) \
                        .replace( '\\zrhilite*', '' ).replace( '\\z1hilite*', '' ).replace( '\\z2hilite*', '' ).replace( '\\z3hilite*', '' ).replace( '\\z4hilite*', '' )
        if marker[0] == '¬': pass # Ignore end markers
        elif marker == 'c': pass # Ignore
        elif marker == 'c~': pass # Ignore text after chapter marker
        elif marker == 'c#': pass # Ignore print chapter number
        elif marker == 'cl': pass # Ignore cl markers AFTER the '\c 1' marker (the text for the individual chapter/psalm heading)
        elif marker == 'v=': pass # Ignore the verse number (not to be printed) that the next field(s) (usually a section heading) logically belong together with
        elif marker == 'd': verseText += '¦' + cleanText + '¦'
        elif marker in ('list',): pass
        elif marker in ('rem',): pass
        elif marker in ('ms1','mr','sr'): pass
        elif marker in ('s1','s2','s3','s4','r'): pass
        elif marker in ('b','nb'): pass
        elif marker in ('sp','qa'): pass
        elif marker == 'p': verseText = f'{verseText}¶ {cleanText}'
        elif marker == 'q1': verseText += '₁ ' + cleanText
        elif marker == 'q2': verseText += '₂ ' + cleanText
        elif marker == 'q3': verseText += '₃ ' + cleanText
        elif marker == 'q4': verseText += '₄ ' + cleanText
        elif marker == 'm': verseText += '§ ' + cleanText
        elif marker == 'mi': verseText = f'{verseText}{cleanText}'
        elif marker == 'pi1': verseText = f'{verseText}{cleanText}'
        elif marker == 'li1': verseText = f'{verseText}{cleanText}'
        elif marker == 'li2': verseText = f'{verseText}{cleanText}'
        elif marker == 'v': firstWord = True # Ignore
        elif marker == 'v~': verseText = f'{verseText}{cleanText}'
        elif marker == 'vw':
            verseText = f"{verseText}{'' if firstWord else ' '}{cleanText}"
            firstWord = False
        else: raise ValueError(f"Unknown export marker {marker!r}: {cleanText!r}")
        verseText = verseText.replace( '\\add ', '{' ).replace( '\\add*', '}' )
    return verseText.strip()


def export_passage(bible, source_profile, refs, cache=None):
    passage = bible.getMappedPassage(source_profile, refs, chapterCache=cache, expandGroups=True)
    text = ' '.join(filter(None, (render_entries(p.entries, bible.abbreviation[-2:], p.reference[0])
                                  for p in passage.portions)))
    coverage = passage.mapping.source_references
    combined = len(coverage) > 1 and (len(refs) == 1 or len(passage.portions) < len(coverage))
    if combined:
        text = f'[Combined passage: {source_profile if isinstance(source_profile,str) else source_profile.abbreviation} {reference_label(coverage)}] {text}'
    record = dict(requested=passage.mapping.requested_references or refs,
                  source_coverage=coverage, native=passage.native_references, combined=combined)
    return text, record


def native_passages(bible):
    """Yield stored native passages once, including declared Psalm titles."""
    cache, seen = {}, set()
    for book in BOOKLIST_66:
        count = bible.getNumChapters(book)
        if count is None:
            raise ValueError(f'{bible.abbreviation}: missing export book {book}')
        for chapter in range(1,count+1):
            entries, _ = bible.getContextVerseData((book,str(chapter)))
            refs = passageReferencesFromEntries((book,str(chapter)), entries, bible)
            for ref in refs:
                if ref in seen:
                    continue
                text, record = export_passage(bible, bible, (ref,), cache)
                seen.update(record['native'])
                yield ref,text,record
