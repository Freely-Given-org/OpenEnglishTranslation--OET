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
| `oet_alignment.py` | Position-preserving tokenizer, optimal alignment and bounded phrase movement. |
| `oet_candidates.py` | Shared evidence, candidate conflict resolution, aliases/repeats and in-memory convergence before writing. |
| `oet_versification.py` | BOS reference conversion, mapped text retrieval and complete passage grouping. |
| `oet_noun_tables.py` | Noun plural/singular pairs and additional verbal nouns. |
| `oet_verb_tables.py` | Verb paradigms and their permitted overlapping forms. |
| `oet_derived_word_tables.py` | Reviewed related-form families and directional contraction subjects, used only as weak positional candidates. |
| `oet_word_tables.py` | Smaller vocabulary lists, combined simple-word vocabulary and one maintained list of single-word mappings for alignment and unique recovery. |
| `oet_phrase_tables.py` | Directional RV-word/LV-phrase and LV-word/RV-phrase mappings, always with a multiword phrase on one side. |

Edit the literal tables in the relevant module; flattened collections and
reverse mappings are derived on import. Each module documents its row format
and retains the existing validation checks. The table modules do not load Bible files.

Keep entries alphabetical by the first word, ignoring case, punctuation and
diacritics. Noun pairs use the plural form; verb sets use the base present form
at the end of each tuple. Retain grammatical form order within each tuple,
numerical order in the number list. Alternatives compete on evidence and
context; their order in a table does not decide the link. Historical sections such as “additional mappings” should
be merged into the alphabetical sequence.

Maintain all single-word correspondences in `SINGLE_WORD_MAPPINGS`:

| Row | Matching rule |
| --- | --- |
| `(RV word, LV word)` | RV → LV direction. Alignment and unique lexical recovery ignore sentence case. Unique recovery counts every RV occurrence, including linked words. |
| `(word, word, 'aligned')` | Normalised, two-way matching using word positions; repeated occurrences can be matched. |
| `(RV word, LV word, 'both')` | Symmetric alignment evidence plus the explicit RV → LV permission for unique lexical recovery. |

`EQUIVALENT_LV_RV_WORDS` and `RV_SINGLE_WORDS_FROM_LV_WORDS` are generated
lookups, not separate lists to maintain. A pair used by both passes appears
once with `'both'`. Directional positional candidates score below symmetric
alternatives, exact matches and inflections; they are not reversed or expanded
transitively. `scoreRVLVWords()` supplies symmetric lexical evidence;
`scoreAlignedWords()` adds the directional candidates for alignment.
Keep directional pairs directional unless their reverse and normalised uses
have also been checked.

When investigating an unlinked word, first check whether
`scoreAlignedWords(RV_word, LV_word)` supplies evidence. For example, Matthew
23:23's `weightier` / `heavier` needed an explicit directional entry; it is not
an English inflection match. Review candidate pairs in their BOS-mapped verse,
including other occurrences and possible senses, and cite the RV reference in
the table. Unlinked words in the same gap are only suggestions for review.
Keep idioms in the phrase table and leave indistinguishable repeated sources
unresolved. A valid new pair can add anchors, remove a misleading match, or
make an old match ambiguous, so compare fresh rebuilds as well as checking
the motivating verse.

Related forms such as `destroy`/`destruction` are maintained separately in
`RELATED_WORD_GROUPS`. Their score (50) is below directional pairs (55),
symmetric equivalents (60), curated inflections (95) and exact matches (100).
Group members expand through curated noun/verb forms, never through synonym
chains. Overlapping families do not merge: `every`/`everyone` and
`every`/`everywhere` do not permit `everyone`/`everywhere`. Arbitrary shared
prefixes and spelling-ending guesses no longer produce candidates. Add an
explicit correspondence only after checking the verse and competing words.
Exact-word recovery now supplies candidates to the same selector. A complete
normalised spelling must have a mutually unique best match on both sides;
a weaker inflection does not veto an exact competing occurrence, while equally
strong occurrences abstain. Already linked occurrences still count. Shared prefixes never establish equivalence.
The former phrase-table priority integers have been removed: word and phrase
alternatives compete in the alignment graph rather than winning by table order.

The optional `OET-RV_wordPhrases_table.tsv` remains in
`translatedTexts/ReadersVersion/` and is loaded by the connector.

From the repository root, use the existing scripts environment:

```sh
# Update all books using one process (recommended on a memory-limited laptop).
uv run --project scripts scripts/connect_OET-RV_words_via_OET-LV/connect_OET-RV_words_via_OET-LV.py -1

# Preview selected books without writing any ESFM files (JNA is Jonah).
uv run --project scripts scripts/connect_OET-RV_words_via_OET-LV/connect_OET-RV_words_via_OET-LV.py -1 --books RUT JNA MRK PHM --dry-run --report /tmp/oet-links.json

# Produce reviewable copies of all 66 books and an audit of proposed links.
uv run --project scripts scripts/connect_OET-RV_words_via_OET-LV/connect_OET-RV_words_via_OET-LV.py -1 --output-dir /tmp/oet-linked-books --report /tmp/oet-links.json

# Run the regression tests.
uv run --project scripts python -m unittest discover -s scripts/connect_OET-RV_words_via_OET-LV/tests -v
```

Without `--dry-run` or `--output-dir`, the script updates selected source books
in place, as before. Use `--books MRK` for Mark alone; omit `--books` to process
all books. Plain-add cleanup now applies only to selected books and takes place
in memory before matching; previews therefore do not edit unselected books or delete source
pickle files. An output directory contains ESFM proposals, not a complete
standalone build with auxiliary tables. `--report` uses one process so the
JSON can collect all books and accepted links deterministically. Normal BOS
logging/settings files may still be created during a dry run.

`-1` is the digit one, also spelled `--single`. BOS sets the process count to
one before loading the Bibles, so it disables multiprocessing in both loading
and matching. Otherwise BOS chooses its worker count from the CPU count,
without budgeting for available RAM. Even one process still holds Bible texts
and word tables; `--books` reduces the texts loaded, and omitting `--report`
avoids retaining the full verse/link audit. Run corpus comparisons sequentially
on a laptop rather than starting several single-process jobs together. Keep large
report/output directories on disk: on systems where `/tmp` is `tmpfs`, those
files consume RAM and can undo the benefit of serial processing.

### Versification and matching passages

The connector requires BOS's Bible-level versification and passage APIs. It
explicitly loads OET-RV as `eng` (English) and both LV testaments as `org`
(original). These are the conversion profiles, not the older count-only names
`KJV` or `Original`. There is no same-number fallback or manual Psalm offset.

Each printed RV verse or verse bridge is sent to `lv.getMappedPassage(rv, refs)`.
All bridge members are included: RV `1–3` retrieves all three mapped LV verses
and is matched once. Chapter boundaries are followed, e.g. RV Genesis 31:55 →
LV 32:1, Joel 2:28 → 3:1 and Malachi 4:1 → 3:19. BOS-required groups and any
shared LV storage bridges combine their RV counterparts before matching. A
discontinuous mapping fetches only its explicit destinations, in mapping order.

Pre-verse `\d` titles use verse zero where BOS declares it (Psalm 3:0 → LV
3:1). Where the English profile has no separate title address, the `\d` text
is included with printed RV verse 1, matching BOS's storage convention (e.g.
Psalm 11). Psalms 51, 52, 54 and 60 have a two-verse body offset, resolved by
BOS. Each of those RV titles maps to both LV verses 1–2, while the RV body
starts at LV verse 3.

The source-coverage audit also reports native LV verses that no RV passage
uses, with their inverse BOS mapping results in `unmapped_lv`. This matters
because a draft mapping can report `exact` yet represent only part of a verse.
The repaired BOS mappings now include the complete text for all eight passages
that the first audit found incomplete:

| RV passage | Complete LV passage |
| --- | --- |
| Numbers 26:1 | Numbers 25:19 and 26:1 |
| 1 Samuel 20:42 | 1 Samuel 20:42 and 21:1 |
| 1 Kings 22:43 | 1 Kings 22:43–44 |
| 1 Chronicles 12:4 | 1 Chronicles 12:4–5 |
| Titles of Psalms 51, 52, 54 and 60 | Verses 1–2 of each Psalm |

These complete split/merge relationships come directly from BOS. The connector
retains its unused-LV audit to detect future omissions; it does not supplement
BOS with a second, hard-coded versification table.

Non-exact mappings, missing mapped text and incomplete stored passages are
skipped with a warning and included in `mapping_skipped` in the JSON report.
An existing link must occur in the mapped LV text, rather than merely lie in
its minimum/maximum source-ID range. Cross-book destinations are currently
reported and skipped because this connector processes one book at a time.

RV Jonah was returned to English numbering: the fish verse is 1:17 and the
following prayer and closing verse are 2:1–10. Translation wording is unchanged.
Matching itself never renumbers books; inputs must use the declared profiles.

Validation on 2026-10-12 rebuilt copies of all 66 unnumbered RV books, then
rebuilt NUM, SA1, KI1, CH1 and PSA after the eight BOS mapping repairs. A new
audit of all 31,055 passages confirmed that only those eight mappings changed
and that no LV verses remain unrepresented. The repaired passages gained 56
linked words; unaffected passages in those five books produced identical text.
The combined preview has 318,953 / 520,786 eligible OT words linked (61.2%) and
107,409 / 175,308 NT words (61.3%), with no skipped RV requests.
Every inserted number was checked against the raw LV text at its mapped
addresses; wording was preserved and excluded additions stayed unnumbered.
These checks establish source-passage membership, not semantic matching accuracy.
All 94 regression tests passed, including complete text retrieval and round-trip
mapping for each of the eight repaired passages. The earlier serial versus
multiprocessing check produced identical output for four books. Rerunning all
five rebuilt books with the repaired mappings added zero links in one pass.

### How matching works

1. Parse only the selected books, resolve their complete mapped passages once,
   and retain character positions, existing numbers and `add` classes for each
   word. Repeated matching passes reuse these passages and the live RV lines.
2. Build passage-local lexical, name, number-change and phrase evidence.
   `oet_candidates.select_links()` is the only matching entry point: providers
   return candidates and cannot edit ESFM. Curated name spellings participate
   in positional alignment, so repeated names can be resolved by occurrence.
   NT names with lexical-capitalisation `U` are eligible for name-table evidence
   even without `W`; Hebrew leading modifier letters and gentilic nouns also
   retain name-table evidence. Reviewed name spellings score 110, above generic
   exact matches (100), so a moved “sons” does not displace a repeated person
   in a genealogy. The metadata-only `*` substitution stays conservative.
   Verses marked `⇔` first use unique lexical/name candidates to establish
   anchors; an unnumbered reversed verse must not be forced into LV clause order.
3. Align unnumbered occurrences between existing links. The bounds use the
   **order of words in the LV text**, not the numerical order of Hebrew/Greek
   source IDs. An anchor is located at its matching English gloss within a
   multiword source group where possible. Local changes of word order therefore
   do not force the entire verse into a single monotone alignment.
   A gloss already identified by a strong existing link is reserved even if
   reordered anchors put it inside another gap. Other glosses with the same
   source number remain available (e.g. “put” and “around”).
   Semantic `@`, `%`, `*` and `&` spans abstain if another, non-neighbouring
   RV anchor lies inside their LV window: a pronoun/article alone cannot
   identify a referent across overlapping reordered clauses. An `&` span also
   cannot borrow a leftover article from the preceding name's source group.
   Ordinary function words cannot borrow a source group owned only by distant
   anchors; neighbouring words may share a multiword source gloss.
4. Accept a proposed number only when every best alignment of that gap agrees.
   Forward/backward dynamic programming computes this in O(RV words × LV words)
   per gap, instead of repeating the entire calculation for each proposed pair.
   Slash-separated gloss alternatives occupy one column. Separate English words
   with the same source number remain separate columns.
   Curated phrases are additional transitions in the same alignment graph:
   “his” can consume “of him”, and “ran away” can consume “fled”. A phrase must
   consume one complete contiguous span on each side; all its LV components
   must have the same source number. These transitions reserve every consumed
   column and obey the same all-optimal-path ambiguity check. They do not make
   individual phrase components interchangeable synonyms.
   Whole-phrase ownership is reconstructed from saved links on later passes,
   so linking “his” does not leave the “him” of “of him” available for reuse.
   Exact “I” and “a” are eligible when their occurrences are unambiguous. LV
   pronoun annotations such as `you(pl)`, `your(ms)` and `you(fs)` are stripped
   before punctuation cleanup; they must not become `youpl`, etc. Curated noun
   pairs retain irregular forms such as hoof/hooves in positional matching.
   This also covers reflexive annotations such as `yourself(m)` and optional
   LV suffixes such as `son[s]` and `branch[es]`. Positive contractions such as
   “you're” can identify the explicit LV subject “you” when alignment is
   unambiguous; the subject column is reserved on later passes. Negative
   contractions retain their separately curated mappings.
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
   Once ordinary alignment settles, a separate exact-context rule can complete
   an article/preposition next to an already linked content word when both
   texts have the same adjacent words. Possessives may move within one source
   gloss, e.g. “father of my” → “my father”. The content-word anchor must match
   exactly; punctuation, specialist spans, occupied glosses and competing
   claims block this fallback. It does not relax general phrase movement.
6. Resolve proposals at one selection boundary. Contextual alignment takes
   precedence over explicit alias/repeat evidence and unique lexical recovery.
   Conflicting candidates at the same priority abstain together, independent of
   provider enumeration order. Claims identify English LV columns rather than
   whole source IDs. Only an explicit alias/repeat bundle may share a consumed
   gloss with its original occurrence. Candidate bundles are atomic.
7. Check provisional function words against the content-word anchors selected
   in the same round, while preserving the graph’s joint positional decisions.
   A function word cannot borrow a source group owned only in another
   punctuation-bounded clause. A conjugated subject may share its verb’s source
   number across an intervening adverb in the same clause. Unique recovery also
   checks the new bounds; in a `⇔` clause swap it
   waits for lexical/name anchors to stabilise. Keep phrase bundles atomic. Refine
   temporary anchors until no more candidates are accepted, then insert links
   once, from right to left, at their original positions. Existing links stay
   unchanged. This prevents “are” in Mark 13:11's “you are given” from taking
   the later “you are not” while “given” is still becoming an anchor.
8. Retain the book-level convergence check and pass summaries. Parsed passages
   are reused, excluded additions are cleaned once, and only the final book is
   saved. A book that gains nothing takes one pass; productive books receive a
   final verification pass. Preview and output-copy modes use the same selector.
   Each productive selection round fills an unnumbered occurrence, so both
   loops terminate without an arbitrary pass limit.

The specialist classes are handled as follows:

| Class | Treatment |
| --- | --- |
| Plain `add`, `<`, or `>` (including uncertain `?` forms) | These have no corresponding source word: exclude from matching and coverage, and remove old numbers. |
| `@` | Align a whole referent phrase with an LV pronoun; recognise curated singular/plural noun heads before testing for capitalised names. Thus “the land” is singular and Israelis/Jews are plural. |
| `%` | Align changed-person wording with an LV pronoun. |
| `*` | Align a substituted pronoun/phrase with an identified LV proper noun. OT sources require an `Np` morphology component; an empty capitalisation flag does not make “I” a name. Broader descriptions still need more work. |
| `&` | Match an LV article or possessive in the bounded gap. |
| `≈`, `#` | Allow lexical, curated synonym and inflection matches; do not equate arbitrary paraphrases by position alone. |
| `≡` | Repeat an already identified earlier phrase in this passage, preserving each word’s own source number; no previous-verse borrowing or assigning the first number to the entire phrase. |
| `!` | Propose an atomic traditional-name alias bundle including its adjacent original name. |
| `+`, `=`, `^` | No new automatic positional links. These need more specific grammatical or semantic evidence. |

Nested `\+add` and uncertain specialist codes such as `?@` retain the base
class's meaning. Notes, cross-references, headings and marker names cannot
become matchable words. Nomina sacra use `+nd` inside another character field;
no new `nd` is inserted inside an `add` span.
Each `!` alias belongs only to the immediately preceding name. Earlier `!`
spans stop the backward name scan, just as other added spans do; a numbered
Shadrak/Hananyah cannot lend its number to Meyshak/Misha’el later in the list.

A leading `⇔` means a **clause swap**, not a reversal of individual words.
The aligner can rotate the LV sequence when existing anchors expose one clear
switch between two runs. Otherwise it retains local anchored gaps and skips
conflicting bounds. This is deliberately incomplete clause segmentation.
The smaller phrase-movement rule retains punctuation separately from the
cleaned glosses and logs accepted links as `local phrase movement`. Punctuation
is a conservative boundary estimate, not a grammatical parser: it can reject
valid movements around commas and cannot identify every unpunctuated clause.
Synonym and related-form scores are too weak for this rule; existing
exact, curated verb-form and inflection scores qualify.

Unique lexical candidates count already linked forms when testing
uniqueness. Otherwise a second pass could reuse the sole LV occurrence for
another RV inflection of the same word. Existing linked occurrences count as
evidence but are never passed back to the insertion function.
Unique function-word recovery cannot borrow a source group owned only elsewhere.
It also respects the nearest live anchors in LV
text order. Neighbouring words may share a source group, articles/prepositions
may move around content words, and verse-wide uniqueness can still establish
initial anchors. Acts 19:40–41's
“And … have no defence” must not borrow “And having said” from the dismissal
sentence after the quotation.

### 13 October 2026 synonym review

Matthew 23:23's `weightier` had no lexical evidence for LV `heavier`.
It now links to **16288**. A scan of all 66 books' 31,055 mapped passages
identified **75 missing directional word pairs** suitable for this batch,
including `yeast` / `leaven`, `cavalry` / `horsemen`, `container` / `vessel`,
`godliness` / `devoutness`, and `encouragement` / `exhortation`.
The [pair ledger](connect_OET-RV_words_via_OET-LV/audits/2026-10-13-synonym-pairs.tsv)
records reviewed examples, discovery references and resulting direct links.

A whole-phrase entry maps Matthew 25:8's `less sensible` to `foolish` (**17708**),
preventing the new `sensible` / `prudent` pair from selecting **17710**, which
belongs to the other women. Two otherwise plausible pairs were withheld:
`disobeyed` / `sinned` exposes wrong possessive links in Jeremiah 3:25, and
`innocent` / `blameless` makes Proverbs 11:5's `right` select `makes_straight`
instead of `righteousness`. These need a separate alignment fix. This change
adds vocabulary and tests without changing candidate selection.

The controlled **fresh rebuild** uses the same frozen blank RV snapshot and
unchanged LV data as the v2.0 audit below; it isolates table changes from
concurrent RV edits. All output remains in preview copies.

| Corpus | Before these entries | After these entries | Net linked words |
| --- | ---: | ---: | ---: |
| OT | 319,035 | 319,354 | +319 |
| NT | 106,443 | 106,720 | +277 |
| Bible | 425,478 | 426,074 | +596 |

Overall coverage changes from **61.1544%** to
**61.2401%** of 695,744 eligible displayed RV words.
The [link-change ledger](connect_OET-RV_words_via_OET-LV/audits/2026-10-13-synonym-link-changes.tsv)
records 649 added tags, 53 removed tags and
13 reassignments. Tag counts can differ from displayed-word
counts, e.g. hyphenated names. New anchors can remove questionable links or
leave previously linked words ambiguous; coverage is not measured semantic
accuracy, and the table does not force unresolved repeated occurrences.

All **130 tests** pass, including 13 mapped-passage fixtures, excluded-addition
checks, repeated-source ambiguity and the phrase-modifier regression.
The 66-book validation confirms unchanged wording and denominators, no IDs
outside mapped LV passages, no numbered excluded additions, and no skipped
versification mappings. Runs used `-1` and at most four selected books at a
time; peak process RSS was **966.1 MiB**. The
[summary](connect_OET-RV_words_via_OET-LV/audits/2026-10-13-synonym-summary.json)
contains per-book counts, hashes and the withheld cases. Raw comparisons are
in the ignored SSD directories `.cache/oet-synonyms-20261013/` and
`.cache/oet-candidate-engine-20261013/fresh-synonyms*`.

### 13 October 2026 v2.0 candidate-engine audit

The consolidation was compared with the user's frozen **428,428 / 695,744
(61.58%)** rebuild. Both runs below process all 66 books and 31,055 mapped
passages. The fresh run starts without numbers; the incremental run retains
that baseline's existing links. All output is in separate copies. Concurrent
RV formatting edits, mostly `\add ≈So`, were preserved in the working tree
and were not mixed into this comparison.

| Corpus | Frozen v1.9 baseline | Fresh v2.0 rebuild | Incremental v2.0 |
| --- | ---: | ---: | ---: |
| OT | 321,423 (61.73%) | 319,035 (61.27%) | 326,798 (62.76%) |
| NT | 107,005 (61.12%) | 106,443 (60.80%) | 108,767 (62.13%) |
| Bible | 428,428 (61.58%) | 425,478 (61.15%) | 435,565 (62.60%) |

The fresh rebuild changes coverage by **-2,950**
displayed words; the incremental run adds **7,137**.
These are coverage measurements, not measured semantic accuracy. The new
selection order corrects some links and loses some valid links: Amos 2:4's
“Yahweh's” and the second “Yitshak's” in 1 Chronicles 1:34 use the correct
occurrences, while Amos 1:8's “will” before “die” remains unlinked. Historical
anchors explain why an incremental result cannot stand in for a rebuild test.
The [review ledger](connect_OET-RV_words_via_OET-LV/audits/2026-10-13-candidate-engine-review.tsv)
records these examples as preview results, not edits applied to RV sources.

All **125 regression tests** passed. Both corpus runs preserve translation
wording and eligible-word denominators, leave excluded additions unnumbered,
and have zero skipped mappings or numbers outside the mapped LV passage.
Every book reaches a zero-addition pass. The detailed
[comparison summary](connect_OET-RV_words_via_OET-LV/audits/2026-10-13-candidate-engine-summary.json)
contains per-book counts, pass totals, regression examples and input/output
hashes. Raw reports and snapshots are kept in the ignored SSD directory
`.cache/oet-candidate-engine-20261013/`.

Runs used `-1` sequentially in four-book groups, with peak process RSS of
**774 MiB**.
This measures the batches, not an unbatched all-book invocation. The pure
candidate engine imports without BibleOrgSys; BOS remains responsible for
loading and versification through the main adapter.

### 13 October 2026 v1.9 accuracy and coverage audit

This pass checked all 66 canonical books and all 31,055 mapped passages using
BOS English → original versification. Recurring error patterns and proposed
new links were also inspected manually; this is not a claim that every link
has received a human semantic review.

| Corpus | Starting snapshot | Reviewed existing links + v1.9 | Rebuilt without any numbers |
| --- | ---: | ---: | ---: |
| OT | 321,425 / 520,681 (61.73%) | 326,720 (62.75%) | 321,423 (61.73%) |
| NT | 107,946 / 175,063 (61.66%) | 109,136 (62.34%) | 107,005 (61.12%) |
| Bible | 429,371 / 695,744 (61.71%) | 435,856 (62.65%) | 428,428 (61.58%) |

The applied result gains **6,485 linked displayed words net**.
It removes or reassigns 71 individually reviewed incorrect links;
none of those old assignments reappears in the applied result. The
[correction ledger](connect_OET-RV_words_via_OET-LV/audits/2026-10-13-corrections.tsv)
records each word, old number, replacement (if any) and reason. The
[added-link ledger](connect_OET-RV_words_via_OET-LV/audits/2026-10-13-added-links.tsv)
and [audit summary](connect_OET-RV_words_via_OET-LV/audits/2026-10-13-summary.json)
record automatic additions, per-book results, passes and source/output hashes.

Four assignments required explicit human correction: Acts 3:12's “man” refers
to the healed man, and 1 Samuel 20:2's “telling”, “So” and “would” belong to
later clauses. The previously unnumbered “it” in “Far from it” was also linked
to that complete LV expression. These decisions are recorded separately in the
summary. They are not verse-specific exceptions in the matching code.

The eligible-word denominators are unchanged: plain, `<` and `>` additions,
including uncertain and nested `\+add` forms, remain unnumbered and excluded.
Every resulting number belongs to its mapped LV passage. Translation wording
is unchanged. The existing combined text at Acts 19:40 is now labelled
`40-41`, so BOS can include the dismissal sentence in the complete mapping;
there are zero skipped RV passages and zero unrepresented LV verses.

Validation passed **110 regression tests**. A normal serial rerun over the
validated result added zero links, with one pass per book. Existing regressions
for Matthew 4:6's arms/hands, both rooster/crowed occurrences in Mark 14:72,
and both Marias in Mark 15:40 remain covered by the corpus checks/tests.

These percentages measure coverage, not accuracy. The clean rebuild is an
independent check, not the applied output: it does not retain the manual
assignments or useful historical anchors. Checking function-word ownership and auxiliary bounds
also deliberately rejects some former verse-wide guesses. Known incorrect
referent matches and recreated reviewed errors in the clean rebuild are
listed in the summary; some still need human correction. Removing every
number and rerunning does not reproduce the reviewed result exactly.

### Evaluation and remaining work

The 12 October 2026 audit compared both a clean rebuild and an incremental run
against the same starting RV snapshot (before concurrent edits to Matthew 4:9–11). Plain, `<` and `>` additions, including uncertain and
nested `\+add` forms, were excluded from both coverage counts throughout.

| Corpus | Before this fix | Clean rebuild, v1.7 | Earlier preserved-link snapshot |
| --- | ---: | ---: | ---: |
| OT | 259,663 / 520,470 (49.9%) | 302,622 (58.1%) | 300,456 (57.7%) |
| NT | 95,870 / 175,151 (54.7%) | 106,634 (60.9%) | 104,428 (59.6%) |

The clean rebuild adds **53,723 numbered displayed words** over the user's
rebuild, reaching 409,256 / 695,621 (58.8%). Preserving the starting numbers and
only adding links reaches 381,830 (54.9%): existing incorrect anchors can still
block better correspondences. These are coverage measurements, not a measured
accuracy rate. No historical numbers were restored as supposed ground truth.

No consolidation loss was found in the 184 symmetric pairs, 5,207 directional
word pairs, noun pairs or verb groups. The relative priorities of all 5,393
earlier word/phrase alternatives were also preserved. The audit examined all
30,879 nonempty paired verse units automatically, with focused inspection of
failures and representative additions. Those historical measurements predate
the BOS versification integration above and used the old verse pairing. JSON
reports now include mapped references as well as paired texts for review.

An isolated comparison of the old and indexed directional lookup over 997
verses produced the same 2,040 attempted links: 7.1 seconds versus 0.3 seconds.
This measures that lookup only, not the complete application. Full-corpus
validation included fresh and existing-number inputs and separate checks of
the 29 marked clause reversals. All 7,705 unmarked verses in those seven books
were identical in the reversal-specific reruns.

The initial evaluation used the existing numbers as its starting point,
which hid gaps in reconstructing those links after deletion.
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
unlinked-add removals and individual accepted links with verse, line, spelling,
source number and matching rule. Individual link counts can differ from the
coverage delta because separately numbered hyphenated components are counted
as one displayed word by the established coverage counter.
Each book's `verses` list covers every mapped passage, including unchanged ones:
chapter/verse, eligible words, linked words, final RV text without notes, LV
text, and remaining unlinked tokens with their add codes. `chapter`/`verse`
identify the first printed RV address in the matching unit (zero for a separate
title); `rv_references` and `lv_references` give all the corresponding BOS
four-tuples. `mapping` retains BOS status, provenance, diagnostics and data/policy
versions. Per-book `mapped_passages`, `mapping_skipped` and `unmapped_lv` make
both unsuccessful RV requests and unused LV source verses visible.
Individual links use the same RV passage address and an exact source line.
The `unlinked` list uses tokenizer
components, whereas coverage retains the displayed-word convention.
The existing `removed_plain_add` field now counts removals from plain, `<` and
`>` additions together, including their uncertain and nested `\+add` forms.
Each book also reports `links_added` (actual insertions), `pass_additions`
(insertions in each pass, ending in zero), and `passes` (including that final
zero-addition pass). Coverage counts each book once, with candidate-selected additions accumulated
across its passes. Individual JSON link entries retain their selection reason.
If any book in a testament needs more than one pass, normal console output
also includes a single summary for that testament, listing books processed
more than once and the total across all processed books,
e.g. `OT book passes: RUT=3, JNA=2; total 5 book passes.`
These counts include the final zero-addition pass and work with multiprocessing
and `--books`; a testament whose books all finish in one pass has no such line.

Regression tests cover repeated words, alternative glosses sharing a number, semantic spans,
ambiguous pronouns, local reordering, clause swaps, notes, contractions, nested
formatting, verse bridges, Psalm titles, and preservation of existing links.
The ambiguity calculation is also compared with exhaustive enumeration on 400
small word-score matrices and 80 phrase-transition graphs. Book-loop regressions check convergence, cleanup-only books,
all writing/preview modes, audit entries, and accumulated counts without counting
a book's coverage more than once.
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

All lexical, name, specialist and phrase rules now supply candidates to the
shared selection engine. No matching rule edits the verse before selection.
Multiword candidates use span transitions and atomic bundles; saved whole-phrase
ownership also constrains unique lexical recovery. The remaining work is better
lexical/semantic evidence and validation, rather than another direct-write pass.
A manually checked verse set should measure precision separately from coverage.

Known limitations remain: existing incorrect links can constrain later matches;
BOS's remaining unsupported mappings are skipped; synonym and related-form
tables can still confuse senses; complex multiword paraphrases and multi-source
phrases need a richer alignment representation. The optional
`OET-RV_wordPhrases_table.tsv` is absent from this checkout, so that particular
optional source contributes no entries (the maintained Python phrase tables still contribute candidates).

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
