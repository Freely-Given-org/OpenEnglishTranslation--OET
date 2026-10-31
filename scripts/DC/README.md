# OET-LV deuterocanonical lexical drafts

This is a reproducible starting point for DC translation work, **not a completed
OET-LV translation**. It downloads Greek and Latin source text and English lexical data,
creates a source-linked word table, applies persistent editorial overrides, and
generates 17 draft ESFM books. LAO uses explicit OET Latin occurrence glosses.
Grammar, contextual senses, English word order,
OET terminology and names, and alignment to the RV still need editorial work.

The current draft has 124,130 source tokens: 104,460 (84.15%) have a draft
English gloss, gloss alternatives, or name transliteration; 19,670 remain visible
as `⟦SourceWord¦number⟧`. The Greek gloss improvements filled 6,445 more occurrences than the preceding
97,770-token draft; LAO adds 245 Latin occurrences, all with provisional glosses.
All earlier Greek source tokens, punctuation, references and word numbers
are unchanged. The report separates the statuses, including 4,012 Greek name
transliterations and 3,232 sets of lexical alternatives. Coverage is not a measure
of translation accuracy. In particular, `to be`, `I/we`, and `the/this/who` are
upstream dictionary aids, not inflected English renderings.

The original 14 books contained 114,896 source tokens. Psalms of Solomon
(PSS, 18 chapters, 4,830 tokens), Biblical Odes (ODE, 14 chapters, 4,159 tokens),
and Laodiceans (LAO, one chapter, 20 verses, 245 tokens) were appended,
preserving the original word numbers. Here `DC` is a project
umbrella for the explicitly listed books, not a declaration of a particular canon.

## Run it

From the repository root:

```sh
make -C scripts LV_DC
make -C scripts check_DC
```

From the `scripts/` directory, use `make LV_DC` and `make check_DC`.
`make LV_LAO` is an alias for the complete DC build, because LAO's word links
depend on the shared table's preceding rows. It also runs the DC spelling step.
`LV` (and therefore `BOTH`/`ALL`) now includes this stage. It is deliberately
separate from the current 66-book HTML, clean USFM, and VREF pipelines.
Those exporters do not yet support these draft DC word tables and source
versifications. Building DC does not edit the RV or rebuild OT/NT files.
The shared `derivedTexts/OET-LV_names_table.tsv` now includes the emitted DC
name spellings. Its make target waits for `LV_DC`, then merges OT/NT names with
`name-transliteration` and `name-transliteration-candidate` spellings from the DC
word table. These are intentional transliterations for spelling checks; candidate
identifications still require review in the DC table and `draft_gloss_review.tsv`.
DC-only rows leave `TraditionalName` empty where no mapping is supplied. Ordinary
lexical glosses and unresolved Greek are not added to the names table.
Run `make -C scripts ../derivedTexts/OET-LV_names_table.tsv` to refresh it alone
(including the prerequisite DC build), then rebuild the OBD TEST pages. Unchanged
names-table content retains its timestamp.
The RV word connector now loads available DC drafts and their independent word
table, but only links passages with an exact, explicit BOS mapping. On 2026-10-29
the BOS LV profile still lacks DC, so all DC passages are reported as unlinked;
the existing RV DC profile does not establish the LV source boundaries.

The build uses the existing NT dependency `bible-transliterations`, calling its
`transliterate_Greek` function directly. The makefile uses `scripts/.venv/bin/python`
when present, otherwise the project's existing `uv run python` setup. Override
`DC_PYTHON` with another interpreter that has that dependency if needed. Source
downloads themselves still use only the Python standard library.
The DC target also depends on the same ScriptedBibleEditor executable as OT/NT;
make builds it when necessary and passes it to the builder via `--editor`.
The direct commands below require that executable to have been built already.

```sh
# Download only missing inputs; verify every cached file against the manifest:
make -C scripts DC_sources

# Explicitly offline build/check, independent of the current working directory:
scripts/.venv/bin/python scripts/build_OET-LV_DC.py build
scripts/.venv/bin/python scripts/build_OET-LV_DC.py check
```

`fetch` alone uses the network. A normal `make LV_DC` verifies the cache and only
downloads missing files, then builds offline. All output content is deterministic;
unchanged files retain their modification times. The lightweight DC target runs
the build on every invocation, so deleted outputs are restored and corrections
are always picked up, including with `make -j`. No completion stamp can hide a
missing book or word table.

### English spelling stage

[`ScriptedDCUpdates/changeFromUSSpelling.commandTable.tsv`](../ScriptedDCUpdates/changeFromUSSpelling.commandTable.tsv)
contains the DC spelling rules, initially combined from the OT and NT tables.
Its 92 explicit lower-case/initial-capital commands include `labor` → `labour`,
`honor` → `honour`, and `judgment` → `judgement`. Rules apply to `v` and `ip`
lines, including Sirach's prologue. The table is maintained separately; later
OT/NT rule changes are not automatically imported.

Every build renders the draft books into a temporary folder, then runs the real
ScriptedBibleEditor with the adjacent `ScriptedBibleEditor.control.toml` and
spelling table. The control's `input`/`output` paths refer to that staging folder,
so invoke this step through `make LV_DC` or the DC builder. The Rust editor writes
only changed books; the builder supplies originals for the other books. Temporary
filenames use BOS `DNG`/`GES`, while final repository filenames remain `DAG`/`ES1`.

The builder reads the edited ESFM back through its word links and updates
`OETGlossWords` in both word-table copies. It does not run a second replacement
implementation. Original `LexiconGloss` and `Candidates` retain the downloaded
dictionary spellings; `GlossSource` records the spelling stage on changed rows.
Only English letters within existing glosses may change. A changed Greek token,
transliterated name, word link, separator, punctuation, or verse/header structure
fails the build before final files are written. Spelling rules therefore use
literal English letter fragments with `IMarkers` set to `v,ip`; other command
features need a separate, appropriately validated editing stage.

`spelling_changes.tsv` records each changed occurrence. The first spelling build
corrected 231 glosses in 15 books; coverage and all 123,885 word numbers are
unchanged. `build_report.json` records the command-table/control hashes, editor
binary hash, and change counts. `check_DC` rejects stale spelling inputs and
checks that the edited ESFM, both word tables, and audit agree.

## Sources and attribution

Exact URLs, upstream commit IDs, byte sizes, SHA-256 digests, and attribution are
in [`source_manifest.json`](source_manifest.json). Original downloaded bytes are
kept under `intermediateTexts/DC_sources/`.

| Input | Published terms | Use in this pipeline |
| --- | --- | --- |
| [Brenton Greek Septuagint, eBible.org](https://ebible.org/grcbrent/) | [Public domain](https://ebible.org/grcbrent/copyright.htm) | Greek source text, punctuation, and source verse labels; source files dated 2026-04-08 |
| [Open Greek and Latin / First1KGreek](https://github.com/OpenGreekAndLatin/First1KGreek/tree/ed91552c52530c8f5a3ddf2dd767e899372a804c/data/tlg0527) | CC BY-SA 4.0, as specified in each XML header; Harvard College Library and Digital Divide Data | PSS and ODE: transcription of H. B. Swete, *The Old Testament in Greek*, volume III (1905); original TEI files retain attribution, apparatus and source-scan links |
| [STEPBible TBESG and TAGNT](https://github.com/STEPBible/STEPBible-Data) | CC BY 4.0; STEPBible.org, based on work at Tyndale House Cambridge | English dictionary glosses; attested NT surface forms, lemma candidates and possible morphology |
| [Open Scriptures Greek Word List](https://github.com/openscriptures/GreekResources) | CC BY 4.0; credit the Open Scriptures Septuagint Project | Additional headword definitions, spelling aliases, and proper-name recognition |
| [J. B. Lightfoot, *St. Paul's Epistles to the Colossians and Philemon* (1875)](https://www.gutenberg.org/ebooks/50857) | Public domain; digitised by Project Gutenberg, KD Weeks, Colin Bell and the Online Distributed Proofreading Team | LAO Latin text on printed pp. 353–355; no reconstructed Greek is used |
| [M. R. James, *The Apocryphal New Testament* (1924), Laodiceans](https://en.wikisource.org/wiki/The_Apocryphal_New_Testament_(1924)/Epistles/The_Epistle_to_the_Laodiceans) | Public domain; [status notice](https://en.wikisource.org/wiki/The_Apocryphal_New_Testament_(1924)); Wikisource chapter revision 11900163 | English adaptation base for the manually maintained RV LAO file; not a source of automatic Latin glosses |

Changes to those data consist of lexical matching, book assembly below,
normalisation for lookup, OET overrides, and conversion into TSV/ESFM. For Swete,
TEI notes, page markers and superscriptions are excluded from verse text; poetry
lines are joined with spaces, and special ODE references are handled below. The source
word table preserves the source Greek spelling. Attribution appears in every
ESFM header, the report, and this document. Source README and lexical documentation
are included in the download cache. OET's existing text and script licences remain
as documented in the repository root.

Git tracks the small Brenton ZIP snapshot and both LAO HTML snapshots because
their download URLs can return changed bytes over time (including page furniture
around a fixed Wikisource revision). The other cache files are ignored and can be recovered from their
pinned GitHub commits. A changed or damaged file fails checksum verification;
the downloader never silently accepts an upstream update. To adopt new sources,
review the source change, update URLs/sizes/digests in the manifest, replace the
corresponding cached input, rebuild, and inspect the word/reference differences.

### Other sources investigated

[Eliran Wong's Rahlfs dataset](https://github.com/eliranwong/LXX-Rahlfs-1935)
includes much more extensive word-level information and glosses, but its README
specifies CC BY-NC-SA 4.0 and a CATSS user declaration. It is not an input to this
pipeline. Its terms differ from the OET's existing open redistribution terms.

[OpenScriptorium's lxx-morph](https://github.com/OpenScriptorium/lxx-morph)
publishes new morphology as CC BY 4.0, but its README describes its transcription
as derived from an Eliran Wong public-domain edition. That provenance needs
clarification alongside the source repository's stated restrictions before
adopting it as an OET input. Its [release announcement](https://openscriptorium.org/posts/free-lxx-morphology)
also calls for specialist verification. It is not downloaded into the build cache
or used for the generated texts.

The [Eliran Wong Swete repository](https://github.com/eliranwong/LXX-Swete-1930)
is not an input. PSS and ODE instead use the independently published First1KGreek
transcription, under CC BY-SA 4.0, matching the OET text licence. No restricted
Rahlfs/CATSS annotation data are used or copied.

## Books and source references

| OET book | Source component |
| --- | --- |
| TOB, JDT, ESG, WIS, SIR | Corresponding Greek book |
| BAR | BAR 1–5, followed by LJE 1 as BAR 6 |
| DAG | DAG 1–12, SUS 1 as DAG 13, BEL 1 as DAG 14 |
| MA1, MA2, MA3, MA4 | 1MA, 2MA, 3MA, 4MA |
| ES1 | 1ES |
| MAN | MAN |
| PS2 | PSA 151 as PS2 1, with `\cp 151` |
| PSS | First1KGreek `tlg0527.tlg035.1st1K-grc1.xml`, Swete's 18 Psalms of Solomon; USFM `PSS` |
| ODE | First1KGreek `tlg0527.tlg028.1st1K-grc1.xml`, Swete's Odes I–XIV; USFM `ODA` |
| LAO | Lightfoot (1875), Latin text, pp. 353–355; one chapter and 20 OET verses; USFM/BOS `LAO` |
| ES2 | No output; requires a different source/glossing route |

### Latin Laodiceans and its RV adaptation

LAO is the apocryphal *Letter to the Laodiceans*, written in Paul's name. Its
surviving textual witnesses are Latin and medieval translations. Whether it was
originally composed in Greek is uncertain; Lightfoot's Greek retroversion is
not an ancient Greek witness. See [Philip L. Tite's NASSCAL entry](https://www.nasscal.com/e-clavis-christian-apocrypha/epistle-to-the-laodiceans/).

The builder extracts only the eight Latin main-text paragraphs beneath
`AD LAODICENSES.` in `Lightfoot-1875.html`, excluding the apparatus, page numbers
and Greek retroversion. It preserves spelling, punctuation, and the bracketed
editorial supplement `[reliquum]` in verse 13. The HTML's visibly broken
`#<sup>13</sup>al_13#` verse-link markup is repaired during extraction; it is not
Latin text. Source bytes remain unchanged in the cache.

Lightfoot prints `et erit vobis pax.` at the end of verse 16 without a separate
17 marker. OET 16 ends at `retinete;`, and OET 17 contains that final clause,
matching James's 20-verse numbering. `SourceRef` records `LAO_1:16a` and
`LAO_1:16b` for those two halves of printed 16. The combined text reconstructs
Lightfoot 16 without adding or dropping words. No extra greeting from another
manuscript is inserted as verse 17.

[`LAO_latin_glosses.tsv`](LAO_latin_glosses.tsv) contains all 245 occurrence
glosses, keyed by exact reference and Latin spelling. These are original,
AI-assisted OET draft glosses, **not downloaded or human-approved annotations**.
They need human editorial review, especially the difficult syntax in verse 5.
The builder rejects missing, changed, extra, duplicate, or malformed gloss
entries, so a source change cannot silently reuse another word's gloss.
Its Greek lookup/transliterator never processes these Latin tokens.
Explicit name equivalents follow existing OET NT spellings (Paulos, Yaʸsous,
Laodikeia and Kolossai); these are editorial choices, not Latin transliterations.

LAO appends DC word numbers **123886–124130**. Each row has status
`latin-editorial-draft` and an editorial provenance note. `Lemma`, `Morphology`
and `LexiconGloss` are blank and `Candidates` is empty, because no annotated
Latin lexicon has been adopted. All these draft glosses appear in the review
report. Latin semicolons remain semicolons. The same ScriptedBibleEditor stage
and word-table synchronisation apply to LAO as to the Greek books.

To name the mixed-language data honestly while preserving column positions,
the output table/review column `GreekWord` is now `SourceWord`, and
`source_verses.tsv` uses `SourceText` instead of `GreekText`. Existing Greek row
data and links are unchanged. The report schema is now 2 and each book records
`source_language` (`grc` or `lat`); the report also hashes the Latin gloss file.
The Greek-only override and name-alias input tables retain their `GreekWord`
headers. Consumers should look up columns by header. The RV connector and
shared names-table loader do not require the renamed column.

The editable [OET-RV LAO file](../../translatedTexts/ReadersVersion/OET-RV_LAO.ESFM)
adapts James's public-domain English into current English, with OET terminology,
name explanations, paragraphs, an introduction, and headings. Verse 5 has a
footnote acknowledging its uncertain meaning. The source snapshot is retained
as `James-1924-LAO.html`; its underlying translation is public domain (James
died in 1936), and the adaptation follows the repository's OET text licence.
The file identifies its AI-assisted draft origin. Edit it directly: the LV
make chain never regenerates or overwrites RV prose. No automatic RV word
alignment is asserted or fabricated by this addition.

### Swete PSS and ODE references and source quality

The BOS identities are **PSS** (18 chapters) and **ODE** (14 chapters). The
chapter counts establish book identity only. These files preserve Swete's
arrangement and the transcription's verse labels, which must not be treated as
Rahlfs or other editions' verse mappings. There are no corresponding RV files.
The label audit records their absence separately from verse-label differences.

Swete's Odes run: Moses in Exodus (1), Moses in Deuteronomy (2), Hannah (3),
Isaiah (4a: Isaiah 5; 4b: Isaiah 26), Jonah (5), Habakkuk (6), Hezekiah (7),
Manasseh (8), Azariah (9), the three young men (10), Mary (11), Simeon (12),
Zechariah (13), and the morning hymn (14). This is **Biblical Odes**, not Odes of
Solomon. The builder keeps all of the following distinctions:

- XML chapters `iva` and `ivb` become ODE chapter 4 with labels `1a`–`9a` and
  `9b`–`20b`. `SourceRef` retains `ODE_iva:...` or `ODE_ivb:...`.
- Chapter 14 has no XML verse divisions. Its 47 poetry lines after the heading
  become local segments `14:1`–`14:47`, with source references
  `ODE_14:xml-line1`–`ODE_14:xml-line47`. These identify XML line ordinals, not
  conventional verses. The marginal numbers agree through 35, but marginal
  40 precedes XML line 42 and marginal 45 precedes XML line 47. No text is dropped
  to force those numbers to agree.
- Other source labels and their order remain unchanged, including ODE 10's
  sequence `68, 71, 72, 69, 70, 73` and the transcription's absent divisions at
  ODE 7:15 and 13:74. The builder does not silently invent missing divisions.
- Superscriptions and critical/marginal notes remain in the source XML, outside
  the glossed verse text. TEI notes embedded within a verse are excluded too.

The transcription contains visible OCR mistakes, including mixed Latin/Greek
tokens, misspellings and broken words. These are preserved rather than corrected
by guessing. `source_text_review.tsv` flags seven tokens containing Latin letters;
this is a narrow diagnostic, **not a complete list of transcription errors**.
The source needs proofreading against Swete before publication. Checksum and
reconstruction tests establish faithful processing of the downloaded XML, not
the accuracy of that transcription or of its verse divisions.

### Brenton assembly

For Sirach, eBible encodes the translator's prologue as 1:1 through 1:1g and the
actual first verse as 1:1h. The draft emits the prologue as introduction paragraphs
before chapter 1, gives those words internal `SIR_0:1` through `SIR_0:8` references,
and maps source 1:1h to SIR 1:1. Every word retains its original `SourceRef`.

Source verse suffixes such as ESG 1:1b are preserved. They are not silently
collapsed into an RV verse. This is a Brenton-based Greek witness, including for
Daniel; it is not a claim to reproduce every reading of WEBBE or of Rahlfs.
Differences between witnesses and verse divisions remain editorial decisions.
The initial 14 books have 268 source/RV verse-label differences. The report is an
inventory of unequal labels only: **equal labels do not prove equal content**.
Do not use a simple chapter/verse join to attach these word numbers to the RV.

Paragraph continuations are retained within their source verse. Source book and
section headings, Psalm superscriptions, and the explicit Sirach headings/Esther
colophon encoded as paragraph text are paratext, not included in the glossed
verse text. Their original text remains in the unmodified archive. The exceptional
paragraph strings are listed explicitly in `PARAGRAPH_PARATEXT` in the builder.

English **2 Esdras** (OET `ES2`, often Latin **4 Esdras**) must not be substituted
with the Septuagint's **Esdras B**, which is Ezra–Nehemiah. The Brenton archive
does not contain the requested book. The public-domain eBible Clementine Vulgate
download listing also omits that appendix. Selecting and checking a complete
Latin or other surviving witness, its verse numbering (including the extended
chapter 7), and suitable lexical data is a separate outstanding task. No English
WEBBE text is relabelled as an original-language source.

## Gloss selection

1. Look up the accented surface form in TAGNT, including its explicit single-word
   spelling variants. Reuse its **dictionary gloss**, not an NT verse's contextual
   translation. Candidate morphology and source spellings remain reviewable.
2. If there is no exact form, try omission of movable nu in supported attested
   verb/dative-plural forms, then a dictionary headword (TBESG, supplemented by
   Open Scriptures and its explicit spelling aliases). Movable-nu matches are
   labelled `movable-nu-candidate`.
3. Otherwise try unaccented forms/headwords, marked `unaccented-candidate`.
4. Recognise names using proper-name lemmas/flags and Open Scriptures `Np`
   entries, including entries with **no English definition**. Additional reviewed
   spellings are in [`proper_name_aliases.tsv`](proper_name_aliases.tsv). Names
   use the same installed `bible_transliterations.transliterate_Greek` function as
   the NT. For example, Τωβιὴλ becomes `Tōbiaʸl` and Νινευή becomes `Nineuaʸ`.
5. Limited inflections of recognised name headwords may supply additional
   **name candidates**, labelled `name-transliteration-candidate`. They require
   source capitalisation and cannot displace ordinary lexical evidence. Even
   direct name recognition requires a capitalised source form: capitals alone
   are insufficient, and lower-case common lemmas such as ὡς must not become
   names merely because an unaccented dictionary name resembles them.
6. When several English lexical aids are possible, emit slash-separated
   alternatives (`draft-alternatives`) and preserve every candidate. No frequency
   vote selects a contextual sense. For lower-case source words with both name
   and common-word analyses, prefer the common-word glosses, explicitly marked
   `common-word-candidate`. Compound Greek analysis strings are never printed as
   English; a whole-word headword gloss can supply a `headword-fallback-candidate`.
7. Apply global form overrides, followed by occurrence-specific overrides.

Matching normalises Unicode, case, final sigma, apostrophe variants, and the
contextual grave/acute alternation. Accents and breathings remain significant in
exact lookups. NT morphology describes the **attested NT form**, not an annotated
DC occurrence. Inferred name endings do not establish contextual morphology or
person identity. Name output transliterates the **source form**, retaining Greek
case endings; canonical OET name selection and Hebrew restoration remain editorial
work. The report records the installed transliterator version and implementation
hash, along with the name-alias and editorial-override hashes.

The earlier build skipped proper names without definitions and rejected all
conflicting lexical candidates. Those restrictions caused many avoidable Greek
placeholders. The current build fills those cases without presenting a guessed
sense as settled. Remaining placeholders largely need broader Greek inflection
coverage or source-spelling review; this is not a complete LXX morphological
analyser. A name recognition/inflection candidate can still be wrong in context;
all such output is listed for review, and corrections belong in the override file.

The source's spelling errors are preserved and exposed, e.g. MAN 1:1
`παντοκράτωπ`. They should be investigated against an edition, not fixed by
approximate spelling matches. The retained `SourceWord`, `Before`, and `After`
columns reconstruct each parsed source verse exactly. For Greek, ESFM punctuation converts
Greek middle stops to semicolons and question marks to English question marks.

## Editorial workflow and outputs

- `derivedTexts/auto_edited_DC_ESFM/OET-LV_*.ESFM`: 17 lexical/editorial drafts.
- `derivedTexts/auto_edited_DC_ESFM/OET-LV_DC_word_table.tsv`: linked word table;
  the same table is under `intermediateTexts/glossed_DC/`.
- `derivedTexts/auto_edited_DC_ESFM/build_report.json`: coverage per book,
  status counts, source/editor provenance, spelling changes, and unsupported-book explanation.
- `intermediateTexts/glossed_DC/source_verses.tsv`: assembled Greek and Latin verses with
  original source references and filenames.
- `intermediateTexts/glossed_DC/unresolved_words.tsv`: every occurrence still
  lacking a usable English gloss or recognised name, including available candidates.
- `intermediateTexts/glossed_DC/review_by_frequency.tsv`: unresolved forms ordered
  by frequency, with first-occurrence references.
- `intermediateTexts/glossed_DC/draft_gloss_review.tsv`: filled gloss alternatives,
  inferred matches, all name transliterations and Latin draft glosses, grouped by form/gloss/status
  with frequency and first occurrence. Full evidence is in the word table.
- `intermediateTexts/glossed_DC/rv_verse_label_differences.tsv`: labels requiring
  investigation before RV alignment.
- `intermediateTexts/glossed_DC/source_text_review.tsv`: Greek source tokens containing
  Latin letters, requiring inspection of the printed edition.
- `intermediateTexts/glossed_DC/spelling_changes.tsv`: reference, source word,
  and English gloss before/after ScriptedBibleEditor.

For Greek, edit [`gloss_overrides.tsv`](gloss_overrides.tsv), not a generated file. It has
four tab-separated columns: `Ref`, `GreekWord`, `Gloss`, and `Note`.

- `Ref` can be a word reference such as `TOB_1:1w1`, with the **exact** source
  `GreekWord`, or `*` to apply to every occurrence of that normalised Greek form.
- `Gloss` is plain English text; spaces or underscores join English components
  belonging to one source word. Do not include ESFM markers or word numbers.
- `Note` records the reason/evidence for the editorial decision.
- An occurrence override takes precedence over a global form override.
- Duplicate, stale, unmatched, or malformed overrides fail the build before
  output is written. An upstream Greek word change cannot silently shift an
  occurrence correction onto another word.

`LexiconGloss` retains the selected upstream dictionary aid;
`OETGlossWords` contains the effective output; `GlossSource` and `GlossStatus`
identify overrides and automatic matching. `Candidates` preserves alternatives.
The default for `τοῦ` is now **`of_the`**, as requested, covering 1,982 occurrences.
The exceptional TAGNT pronoun analysis remains in `Candidates`; occurrence
corrections can handle contextual exceptions. The earlier `Τωβίτ` → `Tobit`
override has been removed so the name follows the NT Greek transliterator
(`Tōbit`) alongside the other names.

The review also corrected common words which resemble names: Βάλλων in SIR 22:20
is `throwing`, not a form of Βαλλα; the DC forms of τύραννος are `tyrant`/`tyrants`,
not the NT person Tyrannus. These persistent editorial defaults demonstrate how
to correct recognition without modifying generated files. No source spelling
is changed by an override.

Each `¦number` points to a 1-based data row in the **DC** table, excluding its
header. It is independent of OT and NT word tables. A multiword English gloss
repeats its link on each component, matching existing OET ESFM conventions.
Rebuild the complete fixed book sequence together. A source update can renumber
downstream words; never retain old links against a rebuilt table.

The checks verify input hashes, source reconstruction, word-reference uniqueness
and sequence, original source references, ESFM/table agreement, every word link,
and report freshness (including name aliases, the installed transliterator,
the Latin occurrence glosses, the spelling table/control, and ScriptedBibleEditor).
Unit tests cover name/common-word collisions, movable nu, English alternatives,
NT name spellings, ambiguous homographs, paragraph content,
lettered verses, the real book assembly, prologue handling, TEI apparatus exclusion,
PSS/ODE chapter inventories, Ode XIV completeness, checksums, and override
failure cases. Spelling tests run the actual editor on all 16 BOS book codes,
Sirach's prologue and unchanged books, and reject broken links/structure,
changes to Greek/names, unsafe control paths, malformed rules and editor failure.
They verify the conversion machinery, not translation accuracy.
The installed BibleOrgSys loader was also checked against all 16 books and the
complete 123,885-word auxiliary table, including PSS 18:14, ODE 4:9a/9b and ODE
14:47. All 42 conversion tests pass. The connector uses canonical BOS identities
(`DNG`/`GES`) internally while preserving the repository's `DAG`/`ES1` filenames,
and keeps lettered LV labels distinct in its audit. General DC export support
will need to account for these book identities and source boundaries as well.

The next substantial improvements are an openly reusable, validated LXX
lemmatisation/morphology source, contextual glossing and inflection, an ES2
witness, and explicit edition/versification mappings before publication or RV
word alignment.
