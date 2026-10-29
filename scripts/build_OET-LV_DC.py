#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Reproducible, explicitly provisional DC lexical glosses (Python stdlib only).

fetch downloads checksum-pinned inputs; build is offline; check verifies outputs.
See DC/README.md for the textual basis, limitations, and editorial workflow.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
import sys
import unicodedata
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from zipfile import ZipFile

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
MANIFEST = SCRIPT_DIR / 'DC/source_manifest.json'
CACHE = ROOT / 'intermediateTexts/DC_sources'
INTERMEDIATE = ROOT / 'intermediateTexts/glossed_DC'
OUTPUT = ROOT / 'derivedTexts/auto_edited_DC_ESFM'
OVERRIDES = SCRIPT_DIR / 'DC/gloss_overrides.tsv'
RV = ROOT / 'translatedTexts/ReadersVersion'
TABLE = 'OET-LV_DC_word_table.tsv'

# Explicit source components, in a fixed order. These are NOT verse alignments to RV.
BOOKS = {
    'TOB': ('TOB', 'Tobit', [('TOB', None, None)]),
    'JDT': ('JDT', 'Judith', [('JDT', None, None)]),
    'ESG': ('ESG', 'Esther (Greek)', [('ESG', None, None)]),
    'WIS': ('WIS', 'Wisdom of Solomon', [('WIS', None, None)]),
    'SIR': ('SIR', 'Sirach', [('SIR', None, None)]),
    'BAR': ('BAR', 'Baruch', [('BAR', None, None), ('LJE', None, 6)]),
    'DAG': ('DAG', 'Daniel (Greek)', [('DAG', None, None), ('SUS', None, 13), ('BEL', None, 14)]),
    'MA1': ('1MA', '1 Maccabees', [('1MA', None, None)]),
    'MA2': ('2MA', '2 Maccabees', [('2MA', None, None)]),
    'MA3': ('3MA', '3 Maccabees', [('3MA', None, None)]),
    'MA4': ('4MA', '4 Maccabees', [('4MA', None, None)]),
    'ES1': ('1ES', '1 Esdras', [('1ES', None, None)]),
    'MAN': ('MAN', 'Prayer of Manasseh', [('MAN', None, None)]),
    'PS2': ('PS2', 'Psalm 151', [('PSA', 151, 1)]),
    # Append new books so existing DC word numbers remain stable.
    'PSS': ('PSS', 'Psalms of Solomon', []),
    'ODE': ('ODA', 'Biblical Odes', []),
}
TEI_SOURCES = {
    'PSS': ('tlg0527.tlg035.1st1K-grc1.xml', 18),
    'ODE': ('tlg0527.tlg028.1st1K-grc1.xml', 14),
}
TEI_NS = '{http://www.tei-c.org/ns/1.0}'
SOURCE_REVIEW_FIELDS = ['Ref', 'GreekWord', 'Reason', 'SourceRef', 'SourceFile']
FIELDS = ['Ref', 'GreekWord', 'Lemma', 'Morphology', 'LexiconGloss',
          'OETGlossWords', 'GlossStatus', 'GlossSource', 'Candidates',
          'SourceRef', 'SourceFile', 'Before', 'After']
WORD_RE = re.compile(r"(?:[^\W\d_]|[\u0300-\u036f])+[’ʼ᾽']?", re.UNICODE)
TAGNT_REF = re.compile(r'^[1-3]?[A-Za-z]+\.\d+\.\d+#\d+')
# These headings/colophon are encoded as \p, rather than heading markers, in
# the pinned eBible edition. They are paratext, not translated verse content.
PARAGRAPH_PARATEXT = {
    'SIR': {'ΕΓΚΡΑΤΕΙΑ ΨΥΧΗΣ.', 'ΛΟΓΟΙ ΠΑΡΑΒΟΛΩΝ.', 'ΠΑΙΔΕΙΑ ΣΤΟΜΑΤΟΣ.',
            'ΑΙΝΕΣΙΣ ΣΟΦΙΑΣ.', 'ΠΕΡΙ ΤΕΚΝΩΝ.', 'ΠΕΡΙ ʼΥΓΙΕΙΑΣ.', 'ΠΕΡΙ ΔΟΥΛΩΝ.',
            'ΠΕΡΙ ἩΓΟΥΜΕΝΩΝ.', 'ΠΑΤΕΡΩΝ ὝΜΝΟΣ.', 'ΠΡΟΣΕΥΧΗ ἸΗΣΟΥ ΥΙΟΥ ΣΕΙΡΑΧ.'},
    'ESG': {'Τέλος τῆς Ἐσθήρ.'},
}


def write_if_changed(path: Path, data: str | bytes) -> None:
    """Avoid timestamp churn; commit each completely prepared file atomically."""
    if isinstance(data, str):
        data = data.encode('utf-8')
    if path.exists() and path.read_bytes() == data:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_bytes(data)
    temporary.replace(path)


def json_text(value) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2) + '\n'


def tsv_text(fields, rows) -> str:
    # BibleOrgSys and the existing OET word-table consumers split on literal
    # tabs; CSV quoting would corrupt quoted glosses and JSON candidate fields.
    lines = ['\t'.join(fields)]
    for row in rows:
        values = [str(row[field]) for field in fields]
        if any(any(c in value for c in '\t\r\n') for value in values):
            raise ValueError('A TSV cell contains a tab or newline')
        lines.append('\t'.join(values))
    return '\n'.join(lines) + '\n'


def load_manifest(path: Path) -> dict:
    manifest = json.loads(path.read_text(encoding='utf-8'))
    if manifest.get('schema_version') != 1:
        raise ValueError('Unsupported DC source manifest version')
    for item in manifest['files']:
        if Path(item['filename']).name != item['filename'] or not item['url'].startswith('https://'):
            raise ValueError('Unsafe source filename or non-HTTPS source URL')
    return manifest


def verify_data(data: bytes, item: dict) -> None:
    if len(data) != item['bytes'] or hashlib.sha256(data).hexdigest() != item['sha256']:
        raise ValueError(f"Source checksum mismatch: {item['filename']}. "
                         'Do not accept an upstream change without reviewing and updating the manifest.')


def sources(manifest: dict, cache: Path, download: bool = False) -> None:
    for item in manifest['files']:
        path = cache / item['filename']
        if path.exists():
            verify_data(path.read_bytes(), item)
        elif download:
            print(f"Downloading {item['filename']}…", flush=True)
            # eBible serves the documented ZIP download to browser User-Agents.
            request = urllib.request.Request(item['url'], headers={'User-Agent': 'Mozilla/5.0 (OET DC source downloader)'})
            with urllib.request.urlopen(request, timeout=60) as response:
                data = response.read(item['bytes'] + 1)
            verify_data(data, item)
            write_if_changed(path, data)
        else:
            raise ValueError(f'Missing {path}; run make -C scripts DC_sources first.')


def normalise(word: str, *, unaccented: bool = False) -> str:
    """Keep breathings and accents, except contextual grave→acute; never stem."""
    word = word.strip().replace('’', "'").replace('ʼ', "'").replace('᾽', "'")
    word = unicodedata.normalize('NFD', word.lower()).replace('\u0300', '\u0301')
    if unaccented:
        word = ''.join(c for c in word if unicodedata.category(c) != 'Mn')
    return unicodedata.normalize('NFC', word).replace('ς', 'σ')


def clean_gloss(gloss: str) -> str:
    gloss = html.unescape(re.sub(r'<[^>]+>', '', gloss)).strip()
    return re.sub(r'\s+', ' ', gloss)


@dataclass(frozen=True, order=True)
class Candidate:
    lemma: str
    gloss: str
    source: str
    morphology: str = ''


class Lexicon:
    def __init__(self):
        self.forms: dict[str, set[Candidate]] = defaultdict(set)
        self.lemmas: dict[str, set[Candidate]] = defaultdict(set)
        self.bare_forms: dict[str, set[Candidate]] = defaultdict(set)
        self.bare_lemmas: dict[str, set[Candidate]] = defaultdict(set)

    def add(self, word: str, candidate: Candidate, *, form=False) -> None:
        (self.forms if form else self.lemmas)[normalise(word)].add(candidate)
        (self.bare_forms if form else self.bare_lemmas)[normalise(word, unaccented=True)].add(candidate)

    @classmethod
    def load(cls, cache: Path) -> Lexicon:
        lexicon = cls()
        count = 0
        for line in (cache / 'TBESG.txt').read_text(encoding='utf-8-sig').splitlines():
            if not re.match(r'^G\d+\t', line):
                continue
            fields = line.split('\t')
            if len(fields) < 8:
                raise ValueError('Unexpected TBESG row format')
            for lemma in fields[3].split(','):
                lemma = lemma.strip()
                if lemma:
                    lexicon.add(lemma, Candidate(lemma, clean_gloss(fields[6]), 'STEPBible TBESG'))
            count += 1
        if count < 5000:
            raise ValueError('TBESG lexicon is unexpectedly small')
        count = 0
        for name in ('TAGNT-Mat-Jhn.txt', 'TAGNT-Act-Rev.txt'):
            for line in (cache / name).read_text(encoding='utf-8-sig').splitlines():
                if not TAGNT_REF.match(line):
                    continue
                fields = line.split('\t')
                if len(fields) < 5 or '=' not in fields[4] or '=' not in fields[3]:
                    raise ValueError('Unexpected TAGNT row format')
                # Only the lexical gloss is reused. NT contextual translations and
                # semantic/person identifications do not transfer to a DC occurrence.
                greek = fields[1].split(' (', 1)[0].strip()
                words = list(WORD_RE.finditer(greek))
                if len(words) != 1:
                    continue
                lemma, gloss = fields[4].split('=', 1)
                morphology = fields[3].split('=', 1)[1]
                lexicon.add(words[0].group(), Candidate(lemma, clean_gloss(gloss), 'STEPBible TAGNT lexical gloss', morphology), form=True)
                count += 1
        if count < 130000:
            raise ValueError('TAGNT form inventory is unexpectedly small')
        text = (cache / 'GreekWordList.js').read_text(encoding='utf-8-sig')
        # Data only: never execute the downloaded JavaScript.
        data = json.loads(text.split('greekWordList = ', 1)[1].strip().removesuffix(';'))
        for entry in data.values():
            if entry.get('lemma') and entry.get('def') and normalise(entry['lemma']) not in lexicon.lemmas:
                lexicon.add(entry['lemma'], Candidate(entry['lemma'], clean_gloss(entry['def']), 'Open Scriptures Greek Word List'))
        return lexicon

    def lookup(self, word: str) -> dict:
        key = normalise(word)
        candidates = self.forms.get(key)
        method = 'form-lexical'
        if not candidates:
            candidates = self.lemmas.get(key)
            method = 'headword-lexical'
        if not candidates:
            # Missing accents, particularly all-capital openings, are common in
            # Brenton. Candidates remain marked as inference even when unique.
            bare = normalise(word, unaccented=True)
            candidates = self.bare_forms.get(bare) or self.bare_lemmas.get(bare)
            method = 'unaccented-candidate'
        if not candidates:
            return dict(Lemma='', Morphology='', LexiconGloss='', OETGlossWords='',
                        GlossStatus='missing', GlossSource='', Candidates='')
        candidates = sorted(candidates)
        pairs = {(normalise(c.lemma), c.gloss) for c in candidates}
        chosen = candidates[0]
        # TAGNT occasionally combines analyses in a single field (e.g.
        # lemma=gloss + another_lemma=gloss). Do not emit that as English.
        usable_gloss = bool(re.search('[A-Za-z]', chosen.gloss)) and not re.search(r'[=+\u0370-\u03ff\u1f00-\u1fff]', chosen.gloss)
        unambiguous = len(pairs) == 1 and usable_gloss
        gloss = chosen.gloss if unambiguous else ''
        return dict(Lemma=chosen.lemma if unambiguous else '',
                    Morphology=' | '.join(sorted({c.morphology for c in candidates if c.morphology})) if unambiguous else '',
                    LexiconGloss=gloss, OETGlossWords=gloss,
                    GlossStatus=method if unambiguous else 'ambiguous' if len(pairs) > 1 else 'unusable-gloss',
                    GlossSource='; '.join(sorted({c.source for c in candidates})),
                    Candidates=json.dumps([dict(lemma=c.lemma, gloss=c.gloss, morphology=c.morphology, source=c.source) for c in candidates], ensure_ascii=False))


@dataclass
class Verse:
    book: str
    chapter: int
    verse: str
    text: str
    source_ref: str
    source_file: str


def parse_usfm(text: str, filename: str) -> list[Verse]:
    """Read the simple pinned Brenton USFM, failing on unsupported content."""
    book = ''
    chapter = 0
    verses = []
    seen = set()
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        marker, _, value = line.partition(' ')
        if marker == '\\id':
            book = value.split()[0]
        elif marker == '\\c':
            chapter = int(value)
        elif marker == '\\v':
            label, _, content = value.partition(' ')
            if not book or not chapter or not re.fullmatch(r'\d+[a-z]?', label) or not content:
                raise ValueError(f'Malformed verse in {filename}: {line[:80]}')
            ref = f'{book}_{chapter}:{label}'
            if ref in seen:
                raise ValueError(f'Duplicate source verse: {ref}')
            seen.add(ref)
            verses.append(Verse(book, chapter, label, content.strip(), ref, filename))
        elif marker in {'\\p', '\\nb'}:
            if value:
                if value in PARAGRAPH_PARATEXT.get(book, set()):
                    continue
                if not verses or verses[-1].chapter != chapter:
                    raise ValueError(f'Paragraph text without a verse in {filename}')
                verses[-1].text += ' ' + value
        elif marker in {'\\h', '\\toc1', '\\toc2', '\\toc3', '\\mt1', '\\s1', '\\is1', '\\d'}:
            # Titles (including Psalm superscriptions) are paratext, not verses.
            continue
        elif marker.startswith('\\'):
            raise ValueError(f'Unsupported USFM marker {marker} in {filename}')
        elif verses:
            verses[-1].text += ' ' + line
        else:
            raise ValueError(f'Unexpected text before first verse in {filename}')
    if not verses:
        raise ValueError(f'No verses in {filename}')
    if any('\\' in v.text for v in verses):
        raise ValueError(f'Unsupported inline markup in {filename}')
    return verses


def tei_text(element: ET.Element) -> str:
    """Extract verse text, never manuscript sigla or apparatus readings.

    Line boundaries become spaces, including adjacent <l> elements without
    whitespace in the XML. Reject unknown markup rather than lose content.
    """
    def extract(node):
        if node.tag in {TEI_NS + tag for tag in ('note', 'pb', 'lb')}:
            return ''
        if node.tag not in {TEI_NS + tag for tag in ('div', 'p', 'lg', 'l')}:
            raise ValueError(f'Unsupported TEI verse markup: {node.tag}')
        parts = [node.text or '']
        for child in node:
            parts += [extract(child), child.tail or '']
        return ''.join(parts) + (' ' if node.tag.endswith(('}l', '}p', '}lg')) else '')
    return ' '.join(extract(element).split())


def parse_swete_tei(text: str, book: str, filename: str) -> list[Verse]:
    """Read the pinned First1KGreek edition, with explicit Swete references.

    Swete IV(a)/IV(b) share chapter 4 with suffixed verse labels. Ode XIV has
    line numbers instead of verses: its 47 XML poetry lines become local segments.
    These are not Rahlfs Odes references or mappings to any RV edition.
    """
    root = ET.fromstring(text)
    editions = root.findall(f'./{TEI_NS}text/{TEI_NS}body/{TEI_NS}div')
    expected_urn = 'urn:cts:greekLit:' + filename.removesuffix('.xml')
    if len(editions) != 1 or editions[0].get('n') != expected_urn:
        raise ValueError(f'Unexpected TEI edition in {filename}')
    chapters = []
    for node in editions[0]:
        if node.tag == TEI_NS + 'div' and node.get('subtype') == 'chapter':
            chapters.append(node)
        elif node.tag not in {TEI_NS + tag for tag in ('head', 'note', 'pb')}:
            raise ValueError(f'Unexpected TEI book content in {filename}: {node.tag}')
    expected = [str(n) for n in range(1, TEI_SOURCES[book][1] + 1)]
    if book == 'ODE':
        expected[3:4] = ['iva', 'ivb']
    if [c.get('n') for c in chapters] != expected:
        raise ValueError(f'Unexpected {book} chapter sequence in {filename}')
    verses = []
    for chapter in chapters:
        if (chapter.text and chapter.text.strip()) or any(node.tail and node.tail.strip() for node in chapter):
            raise ValueError(f'Unmarked TEI chapter text in {filename}')
        source_chapter = chapter.get('n')
        suffix = source_chapter[-1] if source_chapter in ('iva', 'ivb') else ''
        target_chapter = 4 if suffix else int(source_chapter)
        if book == 'ODE' and source_chapter == '14':
            # The first <l> is the heading. XML <l> boundaries cease to agree
            # with the marginal line numbers after 35. Preserve all XML lines
            # and explicitly identify their ordinal positions, not printed refs.
            lines = []
            anchors = []
            for node in chapter:
                if node.tag == TEI_NS + 'lg':
                    for child in node:
                        if child.tag == TEI_NS + 'l':
                            lines.append(tei_text(child))
                        elif child.tag == TEI_NS + 'lb':
                            anchors.append((int(child.get('n')), len(lines)))
                        elif child.tag != TEI_NS + 'note':
                            raise ValueError('Unexpected Ode XIV line-group content')
                elif node.tag == TEI_NS + 'lb':
                    anchors.append((int(node.get('n')), len(lines)))
                elif node.tag not in {TEI_NS + tag for tag in ('head', 'note', 'pb')}:
                    raise ValueError('Unexpected Ode XIV content')
            if len(lines) != 48 or lines[0] != 'Ὕμνος ἑωθινός.':
                raise ValueError('Unexpected Ode XIV heading/line count')
            if anchors != [(n, n) for n in range(5, 36, 5)] + [(40, 42), (45, 47)]:
                raise ValueError('Ode XIV marginal line-number anchors changed')
            for number, content in enumerate(lines[1:], 1):
                verses.append(Verse(book, 14, str(number), content,
                                    f'{book}_14:xml-line{number}', filename))
            continue
        found_verse = False
        for node in chapter:
            if node.tag == TEI_NS + 'div' and node.get('subtype') == 'verse':
                found_verse = True
                label = node.get('n', '')
                content = tei_text(node)
                if not re.fullmatch(r'[1-9]\d*', label) or not content:
                    raise ValueError(f'Malformed TEI verse in {filename}')
                verses.append(Verse(book, target_chapter, label + suffix, content,
                                    f'{book}_{source_chapter}:{label}', filename))
            elif node.tag in {TEI_NS + tag for tag in ('head', 'note', 'pb')}:
                continue
            elif not found_verse and node.tag in {TEI_NS + tag for tag in ('l', 'lg', 'p')}:
                # Unnumbered superscriptions, including IV(b)'s duplicate heading.
                continue
            else:
                raise ValueError(f'Unexpected TEI chapter content in {filename}: {node.tag}')
        if not found_verse:
            raise ValueError(f'No verses in {book} chapter {source_chapter}')
    refs = [(v.chapter, v.verse) for v in verses]
    if len(set(refs)) != len(refs):
        raise ValueError(f'Duplicate TEI verse in {filename}')
    return verses


def load_verses(cache: Path) -> dict[str, list[Verse]]:
    result = {}
    with ZipFile(cache / 'grcbrent_usfm.zip') as archive:
        source_books = {}
        for name in archive.namelist():
            match = re.fullmatch(r'\d+-(\w{3})grcbrent\.usfm', name)
            if match:
                source_books[match[1]] = name
        for book, (_, _, components) in BOOKS.items():
            if book in TEI_SOURCES:
                continue
            result[book] = []
            for source_book, only_chapter, target_chapter in components:
                name = source_books[source_book]
                for v in parse_usfm(archive.read(name).decode('utf-8-sig'), name):
                    if only_chapter is not None and v.chapter != only_chapter:
                        continue
                    chapter, label = target_chapter or v.chapter, v.verse
                    if book == 'SIR' and v.chapter == 1:
                        # eBible places the prologue at 1:1–1g and actual 1:1 at 1h.
                        # Preserve the prologue separately, with explicit source refs.
                        if label in ('1', '1a', '1b', '1c', '1d', '1e', '1f', '1g'):
                            chapter = 0
                            label = str(1 if label == '1' else ord(label[1]) - ord('a') + 2)
                        elif label == '1h':
                            label = '1'
                    result[book].append(Verse(book, chapter, label, v.text, v.source_ref, name))
            refs = [(v.chapter, v.verse) for v in result[book]]
            if not refs or len(set(refs)) != len(refs):
                raise ValueError(f'Missing or duplicate target verses in {book}')
    for book, (filename, _) in TEI_SOURCES.items():
        result[book] = parse_swete_tei((cache / filename).read_text(encoding='utf-8'), book, filename)
    return result


def tokenise(text: str):
    matches = list(WORD_RE.finditer(text))
    if not matches:
        raise ValueError('Verse has no words')
    for i, match in enumerate(matches):
        before = text[:match.start()] if i == 0 else ''
        after = text[match.end():matches[i + 1].start() if i + 1 < len(matches) else len(text)]
        yield match.group(), before, after


def read_overrides(path: Path) -> dict:
    overrides = {}
    with path.open(encoding='utf-8-sig', newline='') as source:
        reader = csv.DictReader(source, delimiter='\t', quoting=csv.QUOTE_NONE)
        if reader.fieldnames != ['Ref', 'GreekWord', 'Gloss', 'Note']:
            raise ValueError(f'Unexpected override columns in {path}')
        for row in reader:
            if None in row or any(value is None for value in row.values()):
                raise ValueError('Malformed override row')
            if not row['GreekWord'] or not row['Gloss'].strip() or not row['Note'].strip():
                raise ValueError('Overrides need GreekWord, Gloss, and an editorial Note')
            if any(c in row['Gloss'] for c in '\\¦\t\n\r'):
                raise ValueError('Use plain text glosses; ESFM markers and word numbers are generated')
            key = (row['Ref'], row['GreekWord'] if row['Ref'] != '*' else normalise(row['GreekWord']))
            if key in overrides:
                raise ValueError(f'Duplicate override: {key}')
            overrides[key] = row
    return overrides


def make_rows(verses: dict, lexicon: Lexicon, overrides: dict) -> list[dict]:
    rows = []
    used = set()
    for book_verses in verses.values():
        for verse in book_verses:
            for index, (word, before, after) in enumerate(tokenise(verse.text), 1):
                ref = f'{verse.book}_{verse.chapter}:{verse.verse}w{index}'
                row = dict(Ref=ref, GreekWord=word, **lexicon.lookup(word),
                           SourceRef=verse.source_ref, SourceFile=verse.source_file, Before=before, After=after)
                # Apply a global form override, then a more specific occurrence.
                for key in [('*', normalise(word)), (ref, word)]:
                    if key in overrides:
                        row.update(OETGlossWords=overrides[key]['Gloss'].strip(), GlossStatus='editorial',
                                   GlossSource='OET override: ' + overrides[key]['Note'])
                        used.add(key)
                rows.append(row)
    unused = set(overrides) - used
    if unused:
        raise ValueError(f'Unused/stale overrides (including changed Greek source words): {sorted(unused)[:10]}')
    return rows


def render_word(row: dict, number: int) -> str:
    unresolved = not row['OETGlossWords']
    gloss = row['OETGlossWords'] or row['GreekWord']
    if any(c in gloss for c in '\\¦\t\n\r'):
        raise ValueError(f"Unsafe gloss at {row['Ref']}")
    # The existing ESFM convention repeats the word link on each English component.
    components = []
    for part in re.split(r'[ _]+', gloss):
        if part:
            match = re.fullmatch(r'(.*?)([.!?:;]*)', part)
            components.append(f'{match[1]}¦{number}{match[2]}')
    gloss = '_'.join(components)
    if unresolved:
        gloss = '⟦' + gloss + '⟧'
    punct = lambda s: s.replace('·', ';').replace('·', ';').replace(';', '?')
    # Ordinary ASCII semicolon in a Greek source is also a question mark.
    before = punct(row['Before'].replace(';', '?'))
    after = punct(row['After'].replace(';', '?'))
    return before + gloss + after


def render_books(verses: dict, rows: list[dict]) -> dict[str, str]:
    by_verse = defaultdict(list)
    for number, row in enumerate(rows, 1):
        by_verse[row['Ref'].rsplit('w', 1)[0]].append((number, row))
    rendered = {}
    for book, book_verses in verses.items():
        usfm, title, _ = BOOKS[book]
        source = ('H. B. Swete, volume III (1905); Open Greek and Latin / First1KGreek, CC BY-SA 4.0.'
                  if book in TEI_SOURCES else 'Brenton Greek Septuagint (eBible.org), Public Domain.')
        lines = [f'\\id {usfm} - OET-LV DC lexical draft', '\\usfm 3.0', '\\ide UTF-8',
                 f'\\rem ESFM v0.6 {book}', f'\\rem WORDTABLE {TABLE}',
                 '\\rem DRAFT: automatic dictionary glosses in Greek order; grammar and context are unreviewed.',
                 '\\rem Unresolved words are enclosed in ⟦ ⟧. These files are not publication-ready translations.',
                 '\\rem Source: ' + source,
                 '\\rem Glosses/forms: STEPBible.org (Tyndale House Cambridge), CC BY 4.0;',
                 '\\rem additional headword definitions: Open Scriptures Septuagint Project, CC BY 4.0.',
                 '\\rem Changes: lexical lookup, source-based book assembly, OET editorial overrides, ESFM conversion.',
                 '\\rem Source verse labels are retained except documented book assembly and Sirach prologue handling.',
                 '\\rem No verse or word alignment to OET-RV is asserted. See build_report.json and scripts/DC/README.md.',
                 f'\\h {title}', f'\\toc1 {title}', f'\\toc2 {title}', f'\\toc3 {book}', f'\\mt1 {title}']
        if book in TEI_SOURCES:
            lines[13:13] = [
                '\\rem Digitisation: Harvard College Library; Digital Divide Data. See scripts/DC/source_manifest.json for the pinned XML.',
                '\\rem Source transcription needs review; OCR errors are preserved, not silently corrected.',
            ]
        if book == 'ODE':
            lines[13:13] = [
                '\\rem Swete Odes order: IV(a)/IV(b) are chapter 4 with a/b verse suffixes.',
                '\\rem Chapter 14 uses XML hymn lines 1-47 as local verse segments. This is not Rahlfs numbering.',
            ]
        chapter = None
        for v in book_verses:
            if chapter != v.chapter:
                chapter = v.chapter
                if chapter == 0:
                    lines.append("\\is1 Translator's prologue (draft glosses)")
                else:
                    lines += [f'\\c {chapter}', '\\p']
                    if book == 'PS2':
                        lines.insert(-1, '\\cp 151')
            rendered_words = ''.join(render_word(row, n) for n, row in by_verse[f'{book}_{v.chapter}:{v.verse}'])
            lines.append(('\\ip ' if chapter == 0 else f'\\v {v.verse} ') + rendered_words)
        rendered[book] = '\n'.join(lines) + '\n'
    return rendered


def audit_rv(verses: dict, rv_dir: Path) -> list[dict]:
    """Label inventory only. Equal labels must never imply equivalent content."""
    differences = []
    for book, items in verses.items():
        source_refs = {f'{v.chapter}:{v.verse}' for v in items if v.chapter}
        path = rv_dir / f'OET-RV_{book}.ESFM'
        if not path.is_file():
            differences.append(dict(Book=book, Ref='', Status='RV file unavailable'))
            continue
        chapter = None
        rv_refs = set()
        for line in path.read_text(encoding='utf-8-sig').splitlines():
            if line.startswith('\\c '):
                chapter = line.split()[1]
            elif line.startswith('\\v '):
                rv_refs.add(f'{chapter}:{line.split()[1]}')
        for ref in sorted(source_refs - rv_refs):
            differences.append(dict(Book=book, Ref=ref, Status='source label only; alignment required'))
        for ref in sorted(rv_refs - source_refs):
            differences.append(dict(Book=book, Ref=ref, Status='RV label only; alignment required'))
    return differences


def source_review(rows: list[dict]) -> list[dict]:
    """Flag visible transcription problems without guessing a corrected word."""
    return [dict(Ref=r['Ref'], GreekWord=r['GreekWord'],
                 Reason='Latin letter in Greek source token; inspect the printed edition',
                 SourceRef=r['SourceRef'], SourceFile=r['SourceFile'])
            for r in rows if re.search('[A-Za-z]', r['GreekWord'])]


def build(args) -> None:
    manifest = load_manifest(args.manifest)
    sources(manifest, args.cache)
    verses = load_verses(args.cache)
    rows = make_rows(verses, Lexicon.load(args.cache), read_overrides(args.overrides))
    rendered = render_books(verses, rows)
    differences = audit_rv(verses, args.rv_dir)
    per_book = {}
    for book in BOOKS:
        selected = [r for r in rows if r['Ref'].startswith(book + '_')]
        glossed = sum(bool(r['OETGlossWords']) for r in selected)
        per_book[book] = dict(words=len(selected), glossed=glossed, unresolved=len(selected) - glossed,
                              lexical_coverage_percent=round(100 * glossed / len(selected), 2),
                              statuses=dict(Counter(r['GlossStatus'] for r in selected)),
                              chapters=len({v.chapter for v in verses[book] if v.chapter}),
                              verse_segments=sum(v.chapter != 0 for v in verses[book]),
                              prologue_segments=sum(v.chapter == 0 for v in verses[book]))
    report = dict(schema_version=1, status='lexical draft; not a completed translation',
                  source_manifest_sha256=hashlib.sha256(args.manifest.read_bytes()).hexdigest(),
                  overrides_sha256=hashlib.sha256(args.overrides.read_bytes()).hexdigest(),
                  books=per_book, words=len(rows), glossed=sum(bool(r['OETGlossWords']) for r in rows),
                  unsupported_books={'ES2': 'No complete Greek source in Brenton. English 2 Esdras (Latin 4 Esdras) needs a separately selected witness and glossing pipeline; LXX Esdras B is Ezra-Nehemiah, not this book.'},
                  rv_label_differences=len(differences),
                  source_review_tokens=len(source_review(rows)),
                  limitations=['Lexical glosses do not supply inflection, syntax, or contextual sense.',
                               'TAGNT form analyses are candidates transferred from NT forms, not DC morphology annotations.',
                               'Unaccented matches are explicitly marked candidates, not verified lemmatisation.',
                               'Brenton source spelling and verse labels are not silently corrected.',
                               'PSS/ODE use an unreviewed Swete/First1KGreek transcription, with visible OCR errors retained.',
                               'ODE keeps Swete order: IV(a)/IV(b) use chapter 4 with a/b suffixes; XIV uses 47 XML lines as local verse segments, not Rahlfs references or printed line numbers.',
                               'Equal RV/source verse labels do not prove content alignment.',
                               'Word numbers are 1-based data rows, excluding the header, and rebuild with the complete fixed book order.'],
                  source_files=manifest['files'])
    table = tsv_text(FIELDS, rows)
    unresolved = [dict(Ref=r['Ref'], GreekWord=r['GreekWord'], Status=r['GlossStatus'], Candidates=r['Candidates']) for r in rows if not r['OETGlossWords']]
    frequency = Counter((r['GreekWord'], r['GlossStatus']) for r in rows if not r['OETGlossWords'])
    first_refs = {}
    for r in unresolved:
        first_refs.setdefault((r['GreekWord'], r['Status']), r['Ref'])
    review = [dict(GreekWord=word, Status=status, Occurrences=count, FirstRef=first_refs[(word, status)])
              for (word, status), count in frequency.most_common()]
    # All source parsing, rendering, and override validation precedes any writes.
    write_if_changed(args.intermediate / TABLE, table)
    write_if_changed(args.output / TABLE, table)
    for book, content in rendered.items():
        write_if_changed(args.output / f'OET-LV_{book}.ESFM', content)
    write_if_changed(args.output / 'build_report.json', json_text(report))
    write_if_changed(args.intermediate / 'unresolved_words.tsv', tsv_text(['Ref', 'GreekWord', 'Status', 'Candidates'], unresolved))
    write_if_changed(args.intermediate / 'review_by_frequency.tsv', tsv_text(['GreekWord', 'Status', 'Occurrences', 'FirstRef'], review))
    write_if_changed(args.intermediate / 'rv_verse_label_differences.tsv', tsv_text(['Book', 'Ref', 'Status'], differences))
    write_if_changed(args.intermediate / 'source_text_review.tsv', tsv_text(SOURCE_REVIEW_FIELDS, source_review(rows)))
    source_rows = [dict(Ref=f'{v.book}_{v.chapter}:{v.verse}', SourceRef=v.source_ref,
                        SourceFile=v.source_file, GreekText=v.text)
                   for items in verses.values() for v in items]
    write_if_changed(args.intermediate / 'source_verses.tsv', tsv_text(['Ref', 'SourceRef', 'SourceFile', 'GreekText'], source_rows))
    check(args)
    for book, summary in per_book.items():
        print(f"{book}: {summary['glossed']:,}/{summary['words']:,} words have draft lexical glosses ({summary['lexical_coverage_percent']}%)")
    print('ES2: no output; requires a separately selected source witness and glossing pipeline.')


def check(args) -> None:
    sources(load_manifest(args.manifest), args.cache)
    with (args.output / TABLE).open(encoding='utf-8', newline='') as source:
        reader = csv.DictReader(source, delimiter='\t', quoting=csv.QUOTE_NONE)
        if reader.fieldnames != FIELDS:
            raise ValueError('Unexpected DC word table columns')
        rows = list(reader)
    refs = [r['Ref'] for r in rows]
    if len(refs) != len(set(refs)):
        raise ValueError('Duplicate DC word references')
    # Independently reconstruct every source verse, including all punctuation.
    by_verse = defaultdict(list)
    for row in rows:
        by_verse[row['Ref'].rsplit('w', 1)[0]].append(row)
    verses = load_verses(args.cache)
    expected_refs = set()
    for items in verses.values():
        for verse in items:
            key = f'{verse.book}_{verse.chapter}:{verse.verse}'
            expected_refs.add(key)
            selected = by_verse[key]
            if ''.join(r['Before'] + r['GreekWord'] + r['After'] for r in selected) != verse.text:
                raise ValueError(f'Source reconstruction failed: {key}')
            if [r['Ref'] for r in selected] != [f'{key}w{i}' for i in range(1, len(selected) + 1)]:
                raise ValueError(f'Non-sequential word references: {key}')
            if any(r['SourceRef'] != verse.source_ref or r['SourceFile'] != verse.source_file for r in selected):
                raise ValueError(f'Incorrect source provenance: {key}')
    if set(by_verse) != expected_refs:
        raise ValueError('Extra or missing verses in word table')
    for book, expected in render_books(verses, rows).items():
        text = (args.output / f'OET-LV_{book}.ESFM').read_text(encoding='utf-8')
        if text != expected:
            raise ValueError(f'ESFM does not match word table: {book}; save edits in gloss_overrides.tsv')
        actual = {int(n) for n in re.findall(r'¦(\d+)', text)}
        wanted = {i for i, r in enumerate(rows, 1) if r['Ref'].startswith(book + '_')}
        if actual != wanted:
            raise ValueError(f'Missing or incorrect ESFM word links: {book}')
    report = json.loads((args.output / 'build_report.json').read_text(encoding='utf-8'))
    if report['words'] != len(rows) or report['glossed'] != sum(bool(r['OETGlossWords']) for r in rows):
        raise ValueError('Coverage report does not match word table')
    if set(report['books']) != set(verses) or any(
            report['books'][book]['chapters'] != len({v.chapter for v in items if v.chapter})
            for book, items in verses.items()):
        raise ValueError('Book/chapter inventory does not match source texts')
    if report['source_review_tokens'] != len(source_review(rows)):
        raise ValueError('Source transcription review count does not match word table')
    if (args.intermediate / 'source_text_review.tsv').read_text(encoding='utf-8') != tsv_text(SOURCE_REVIEW_FIELDS, source_review(rows)):
        raise ValueError('Source transcription review does not match word table')
    if report['source_manifest_sha256'] != hashlib.sha256(args.manifest.read_bytes()).hexdigest() or report['overrides_sha256'] != hashlib.sha256(args.overrides.read_bytes()).hexdigest():
        raise ValueError('Outputs are stale: sources or overrides changed; rebuild LV_DC')
    print(f'Checked {len(BOOKS)} DC ESFM files, {len(rows):,} source words, and all word-table links.')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['fetch', 'build', 'check'])
    for name, default in [('manifest', MANIFEST), ('cache', CACHE), ('intermediate', INTERMEDIATE),
                          ('output', OUTPUT), ('overrides', OVERRIDES), ('rv-dir', RV)]:
        parser.add_argument('--' + name, type=Path, default=default)
    args = parser.parse_args()
    try:
        if args.command == 'fetch':
            sources(load_manifest(args.manifest), args.cache, download=True)
            print('All pinned DC source files are present and verified.')
        else:
            (build if args.command == 'build' else check)(args)
    except (ValueError, OSError, KeyError, ET.ParseError) as error:
        print(f'DC build failed: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
