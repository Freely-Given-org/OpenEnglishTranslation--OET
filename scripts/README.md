# OpenEnglishTranslation (OET) Scripts

The **_Open English Translation_ of the Bible (OET)** -- a unique, completely free and open-licensed new modern-English Bible translation

The _OET Literal Version_ (OET-LV) is a new creative work,
yet it also depends on the work of others.
We are very grateful for those who have worked on the original Hebrew/Aramaic
and Greek texts, and made their work available to us online
in convenient digital forms and under open licenses.
As well as the original texts themselves,
we have also relied on the parsing and English glossing of those original texts
in order to speed up our own work
in producing a unique, specialised Literal Version
(actually a family of Literal Versions with different options available)
that is designed from the start to be used alongside
our forthcoming _Readers’ Version_ (OET-RV).

The source data used as the basis of the OET-LV
is formed by scripted manipulation of various of those original language source texts.
(This is different from the work of other organisations which have
formed literal versions by taking open-licensed English translations such as the ASV,
and then manually editing them to make them more literal.)
We apply certain transforms to those source texts to form them
into a style more suited to our uses and priorities.
We then manually craft specific transforms
(applied with our [ScriptedBibleEditor](https://github.com/Freely-Given-org/ScriptedBibleEditor))
to edit these intermediate files into the OET-LV.

One reason for scripting most of the editing work is that our source texts
are still being edited themselves as we start this work.
This scripted means that we can rebuild our intermediate files
whenever a new version of the source texts is released.
As those works firm up by more community checking and use and become more stable,
we expect these intermediate files to also stabilise
and then our scripted editing will become basically obsolete
and our manual crafting/editing will become more important (and more efficient).

This scripting starts with a mix of CSV and XML files,
creates TSV files and then USFM files,
before converting them for display as simple HTML files.
As of October 2022, everything is in flux and changing often
but with an expectation of having v0.5 of the OET-LV
available for external review around mid-2023.

## Setup

The OET is developed in full public view on [GitHub](https://github.com/Freely-Given-org/OpenEnglishTranslation--OET).
But we also have our own software projects that we use,
as well as maintaining forks of data that we use for this OET work in a _Forked_ subfolder.
If you want to replicate this work (most people wouldn’t need/want to bother),
you’ll need to checkout the following repos side-by-side
on your system:

- [OET](https://github.com/Freely-Given-org/OpenEnglishTranslation--OET)
- [BibleOrgSys](https://github.com/Freely-Given-org/BibleOrgSys)
- [ScriptedBibleEditor](https://github.com/Freely-Given-org/ScriptedBibleEditor)
- And in _Forked/_ subfolder:
  - [Open Scriptures Hebrew Bible](https://github.com/Freely-Given-org/OS-morphhb)
  - [Clear.Bible Macula Hebrew](https://github.com/Freely-Given-org/macula-hebrew)

All of our scripts are developed and run on an Ubuntu Linux computer.
For very simple scripts we use Bash and use the .sh suffix for filenames.
For most scripts, we use up-to-date Python versions (v3.10 as of Oct 2022)
as we find Python code much more understandable and maintainable
when we return to it and try to understand it again after a few months.
We make no attempt at all to optimise these scripts for efficiency or memory use
or to use multiple threads or cores
as they are mostly one-off type operations.
We are unable to offer any support for other systems.

We use the _intermediateTexts/_ folder for many of the intermediate data files.

## Makefile

Much of the flow creating the draft Literal Version texts can be found
in the __makefile__.

## Old Testament

We use the Open Scriptures Hebrew Bible (OSHB) version of the
Westminster Leningrad Codex (WLC) as our Hebrew (& Aramaic) source text.

This is how we currently form the 39 Old Testament files for the OET-LV-OT:

- echo Take the OSHB WLC words, notes, and segments, and put them into a single TSV table
- ./convert_OSHB_XML_to_TSV.py # words are broken into morphemes -- nine columns -- over half-a-million lines
- echo Expand out the columns ready to add glossing information
- ./prepare_OSHB_for_glossing.py # goes from 9 to 16 columns
- echo Take the Clear.Bible LowFat trees and flatten them into a TSV file -- 32 columns -- almost half-a-million lines
- echo   Also creates an abbreviated version with only 25 columns
- ./convert_ClearMaculaOT_to_TSV.py -e # Gives errors due to currently missing particles and word numbers in low-fat trees
- ./apply_Clear_Macula_OT_glosses.py # Also does some automatic reordering, e.g., verb-subject to subject-verb
- ./extract_OSHB_OT_to_USFM.py # TSV table ➔ USFM files
- echo Do programmed word and other substitutions to the USFM files
- ../../ScriptedBibleEditor/Python/ScriptedBibleEditor.py ScriptedOTUpdates -qe

## New Testament

We use the glosses from the Center for New Testament Restoration (CNTR)
Verifiable Literal Translation (VLT) as our NT source text.

This is how we currently form the 27 New Testament files for the OET-LV-NT:

- ./convert_BibTags_USFM_to_TSV # We use the ID fields from BibleTags for the NT
- echo Convert VLT glosses from still-private CNTR book and collation CSV files to NT USFM files
- ./extract_VLT_NT_to_USFM.py # TSV table ➔ USFM files
- echo Do programmed word and other substitutions to the USFM files
- ../../ScriptedBibleEditor/Python/ScriptedBibleEditor.py ScriptedVLTUpdates -qe

## For both

- ./convert_OET-LV_to_simple_HTML.py # USFM files ➔ simple HTML (incl. index) files

## To Do

Although the above scripts form plain-text USFM and HTML files,
lots of linking information is lost,
i.e., the translated words/phrases are not linked to the original language words that they are translated from.
We aim to fix that as soon as we are able to design (yet another) improved Bible file format.

## Prologue

If you’re a professional Bible translator or app developer and able to help us in this endeavour, please start a conversation with us via our [Contact Page](https://Freely-Given.org/Contact.html).

## Connecting OET-RV words to OET-LV word numbers

The `connect_OET-RV_words_via_OET-LV/` folder contains the connector and its
supporting modules. The connector copies existing OET-LV source-word numbers
onto corresponding OET-RV words without changing the translation wording.

| File in the connector folder | Responsibility |
| --- | --- |
| `connect_OET-RV_words_via_OET-LV.py` | Command-line options, Bible loading, matching passes, ESFM edits and reports. |
| `oet_alignment.py` | Position-preserving tokenizer and alignment algorithm. |
| `oet_noun_tables.py` | Noun plural/singular pairs and additional verbal nouns. |
| `oet_verb_tables.py` | Verb paradigms and their permitted overlapping forms. |
| `oet_word_tables.py` | Smaller vocabulary lists, combined simple-word vocabulary, positional equivalences and directional single-word pairs. |
| `oet_phrase_tables.py` | Directional RV-word/LV-phrase and LV-word/RV-phrase mappings, always with a multiword phrase on one side. |

Edit the literal tables in the relevant module; flattened collections and
reverse mappings are derived on import. Each module documents its row format
and retains the existing validation checks. These modules do not load Bible files.

Keep entries alphabetical by the first word, ignoring case, punctuation and
diacritics. Noun pairs use the plural form; verb sets use the base present form
at the end of each tuple. Retain grammatical form order within each tuple,
numerical order in the number list, and matching priority among alternatives
for the same word. Historical sections such as “additional mappings” should
be merged into the alphabetical sequence.

Directional single-word pairs remain case-sensitive and are not automatically
reversed. The final integer in each RV-word/LV-phrase row says how many
single-word alternatives for that RV word precede the phrase. This preserves
matching priority across the two files; review it when inserting or reordering
that RV word's single-word alternatives.

The optional `OET-RV_wordPhrases_table.tsv` remains in
`translatedTexts/ReadersVersion/` and is loaded by the connector.

From the repository root, use the existing scripts environment:

```sh
# Preview selected books without writing any ESFM files (JNA is Jonah).
uv run --project scripts scripts/connect_OET-RV_words_via_OET-LV/connect_OET-RV_words_via_OET-LV.py --books RUT JNA MRK PHM --dry-run --report /tmp/oet-links.json

# Produce reviewable copies of all 66 books and an audit of proposed links.
uv run --project scripts scripts/connect_OET-RV_words_via_OET-LV/connect_OET-RV_words_via_OET-LV.py --output-dir /tmp/oet-linked-books --report /tmp/oet-links.json

# Run the regression tests.
uv run --project scripts python -m unittest discover -s scripts/tests -v
```

Without `--dry-run` or `--output-dir`, the script updates selected source books
in place, as before. Use `--books MRK` for Mark alone; omit `--books` to process
all books. Plain-add cleanup now applies only to selected books and takes place
in memory before matching; previews therefore do not edit unselected books or delete source
pickle files. An output directory contains ESFM proposals, not a complete
standalone build with auxiliary tables. `--report` uses one process so the
JSON can collect all books and accepted links deterministically. Normal BOS
logging/settings files may still be created during a dry run.

### How matching works

1. Parse only the selected books, index their verse lines once, and retain
   character positions, existing numbers and `add` classes for each word.
2. Apply curated lexical, verb, name and phrase mappings. Reverse indexes avoid
   scanning every noun and verb set for every verse. Spelling-only insertion
   requires a unique full word across the entire verse, including poetry lines.
3. Align unnumbered occurrences between existing links. The bounds use the
   **order of words in the LV text**, not the numerical order of Hebrew/Greek
   source IDs. An anchor is located at its matching English gloss within a
   multiword source group where possible. Local changes of word order therefore
   do not force the entire verse into a single monotone alignment.
   A gloss already identified by a strong existing link is reserved even if
   reordered anchors put it inside another gap. Other glosses with the same
   source number remain available (e.g. “put” and “around”).
4. Accept a proposed number only when every best alignment of that gap agrees.
   Forward/backward dynamic programming computes this in O(RV words × LV words)
   per gap, instead of repeating the entire calculation for each proposed pair.
   Slash-separated gloss alternatives occupy one column. Separate English words
   with the same source number remain separate columns.
   Retain the supporting columns until all gaps have been checked. If two
   independent gaps claim the same LV column, reject the competing proposals
   together rather than letting gap order decide which occurrence gets it.
5. Recover short phrase movements across a nearby linked block using the
   separate `propose_phrase_movements()` rule. It requires 2–6 consecutive
   strong lexical matches, including at least two previously unlinked content
   words with distinct source numbers. Existing neighbouring links cannot
   justify moving a lone ambiguous word. The crossed block is limited to six
   words in each text. Both texts must stay within punctuation boundaries;
   added spans are excluded. Outer
   anchors must agree, source words already linked outside the phrase cannot
   be borrowed, and competing destinations or competing RV occurrences cause
   rejection. This handles “rooster crowed for the second time” against “for
   the second time a rooster crowed” without a verse-specific rule.
6. Insert links by source position, from right to left. This permits several
   occurrences of `the`, `her`, etc. to receive distinct numbers. Repeat the
   positional pass until it cannot add another link. Previously numbered words
   remain untouched, apart from the documented plain-add cleanup.

The specialist classes are handled as follows:

| Class | Treatment |
| --- | --- |
| Plain `add`, or `?` without a specialist class | Exclude from matching and coverage; remove old numbers. |
| `@` | Align a whole referent phrase with an LV pronoun; use clear singular/plural cues where available. |
| `%` | Align changed-person wording with an LV pronoun. |
| `*` | Align a substituted pronoun/phrase with an identified LV proper noun. Broader descriptions still need more work. |
| `&` | Match an LV article or possessive in the bounded gap. |
| `>` | Share the immediately preceding translated word's number, if available in this verse. |
| `≈`, `#` | Allow lexical, curated synonym and inflection matches; do not equate arbitrary paraphrases by position alone. |
| `≡` | Allow repeated-word matching within the same verse; no previous-verse number borrowing. |
| `!` | Use the traditional-name matcher. |
| `+`, `=`, `<`, `^` | No new automatic positional links. These need more specific grammatical or semantic evidence. |

Nested `\+add` and uncertain specialist codes such as `?@` retain the base
class's meaning. Notes, cross-references, headings and marker names cannot
become matchable words. Nomina sacra use `+nd` inside another character field;
no new `nd` is inserted inside an `add` span.

A leading `⇔` means a **clause swap**, not a reversal of individual words.
The aligner can rotate the LV sequence when existing anchors expose one clear
switch between two runs. Otherwise it retains local anchored gaps and skips
conflicting bounds. This is deliberately incomplete clause segmentation.
The smaller phrase-movement rule retains punctuation separately from the
cleaned glosses and logs accepted links as `local phrase movement`. Punctuation
is a conservative boundary estimate, not a grammatical parser: it can reject
valid movements around commas and cannot identify every unpunctuated clause.
Synonym-only and shared-prefix scores are too weak for this rule; existing
exact, curated verb-form and inflection scores qualify.

### Evaluation and remaining work

The October 2026 evaluation used the existing numbers as its starting point.
The old script made no new links in Ruth, Mark or Philemon on rerun. The revised
full-corpus preview increased coverage from about **46.4% to 56.2%** (roughly
68,289 additional numbered words) in approximately 90 seconds on the local
machine, including loading and JSON reporting. These are **coverage figures,
not measured alignment accuracy**; run the commands above for current figures.
The original selected-book run took about 414 seconds and still loaded all
books; the revised small-book previews took a few seconds. Those timings include
startup and depend on filesystem caching and logging, so they are not an
isolated algorithm benchmark.

The JSON reports per-book eligible words, before/after counts, net added words,
plain-add removals and individual accepted links with verse, line, spelling,
source number and matching rule. Individual link counts can differ from the
coverage delta because separately numbered hyphenated components are counted
as one displayed word by the established coverage counter.

All 46 regression tests pass. Tests cover repeated words, alternative glosses sharing a number, semantic spans,
ambiguous pronouns, local reordering, clause swaps, notes, contractions, nested
formatting, verse bridges, Psalm titles, and preservation of existing links.
The ambiguity calculation is also compared with exhaustive enumeration on 400
small score matrices. A second script run can still discover additional links
through legacy lexical/name passes after the new anchors become available.
Phrase-movement regressions cover both directions, the repeated phrases in
Mark 14:72 (including partially/manual-linked starting states), preservation
of existing numbers, idempotence, punctuation fences, conflicts between gaps,
ambiguous/reused source words, weak evidence and overlong movements.

### Further restructuring

The tables, positional representation and alignment engine now have separate
responsibilities. Gap alignment and bounded phrase movement share anchor
resolution, check competing source claims, and return proposals to the same
position-based writer. Mark 14:72
is a regression fixture, not a condition in the matching code.

The older lexical/name passes still edit the verse as they run, which makes
their order significant. Before adding broader semantic or paraphrase rules,
the next structural improvement should make those passes emit candidates with
RV spans, LV source groups, evidence and provenance. One shared selection stage
could then resolve conflicts before a single write stage. A hand-checked verse
set should measure precision separately from coverage during that migration.

Known limitations remain: existing incorrect links can constrain later matches;
versification mismatches are still delegated to BibleOrgSys; broad synonym and
prefix rules can confuse senses; complex multiword paraphrases and multi-source
phrases need a richer alignment representation. The optional
`OET-RV_wordPhrases_table.tsv` is absent from this checkout, so that particular
curated phrase pass has no entries (the script's older phrase tables still run).

The next useful step is a manually checked, stratified sample of verses and
**precision/recall by matching rule**, including narrative, poetry, epistles,
`⇔` and the different `add` classes. Then extend phrase mappings from those
examples. A semantic model could propose difficult clause/phrase correspondences
into the same review report, with deterministic source-number and formatting
checks before applying them. Optimising the percentage alone would encourage
incorrect links, especially where earlier automatic numbers are already wrong.

### Reviewed removals during this cleanup

In addition to 22 numbers inside uncertain plain `add ?…` spans, ten clearly
misassigned numbers were removed from Mark. The translation wording was retained.

| Verse | Removed number(s) | Reason |
| --- | --- | --- |
| 1:45 | `@Yeshua¦22584` | 22584 is the healed man's subject pronoun; the later pronoun for Yeshua is 22596. |
| 2:15 | `@Levi's¦22959` | 22959 is the person reclining, not the house's owner (22964). |
| 2:15 | `his¦22964` before “followers” | The followers' possessive is 22977, not the earlier house-owner pronoun. |
| 2:15 | `sitting¦22956` | The tax collectors and sinners reclining use 22971; 22956 belongs to the earlier subject. |
| 3:4 | `Is¦23450` | 23450 is “he is saying”; “Is it permitting” is 23455. |
| 5:38 | `@Yeshua¦25976` | 25976 is plural “they are coming”; the subject of observing belongs to 25986. |
| 8:22 | `@the¦28762 people¦28762` | 28762 is the object “him”, not the people bringing (28757). |
| 8:22 | `@Yeshua¦28762` after “to” | This earlier object is “bring to him” (28758), not the later “implore him” (28762). |
| 14:12 | `@Yeshua's¦34549` | 34549 is “they were sacrificing”; the apprentices' possessive is 34554. |
