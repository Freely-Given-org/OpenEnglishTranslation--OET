# Raw OSHB source tables for Open English Translation (OET)

The source Open Scriptures Hebrew Bible (OSHB) files
were taken from [here](https://github.com/Freely-Given-org/OS-morphhb)
which is a fork of [this](https://github.com/openscriptures/morphhb).

The last conversion was done on 2022-09-25.

We would like to express our thanks to [Open Scriptures](https://github.com/openscriptures) (OS)
for their work producing the OS [Hebrew Bible](https://github.com/openscriptures/morphhb)
(a parsed version of the [public domain](https://en.wikipedia.org/wiki/Public_domain)
[WLC](https://en.wikipedia.org/wiki/Leningrad_Codex) text)
and for releasing it under an open
[Creative Commons Attribution 4.0 International](http://creativecommons.org/licenses/by/4.0/)
licence.

Note that for viewing the OSHB text and parsings, you can see the OS [website](https://hb.openscriptures.org/).

## Formats

The OSHB work is supplied as OSIS XML files.
This is not the most convenient format to work with and expand,
so we have converted the data to both TSV and JSON formats using our Python
[script](https://github.com/Freely-Given-org/OpenEnglishTranslation--OET/blob/main/scripts/OSHB_XML_to_TSV.py).

That script parses the 39 OSIS XML files and produces the whole Old Testament TSV and JSON outputs.
The script has two options -- by word or by morpheme (marked with forward slashes in the OSHB).
The versions saved here have a line for each morpheme -- some half-million lines/entries.

The TSV version has seven columns and looks like:

```code
FGID         Ref       Type Strongs n Morphology OSHBid Morpheme
0100100101a  GEN_1:1-1a  m  b      1.0  HR       01xeNa   בְּ
0100100101b  GEN_1:1-1b  m  7225   1.0  Ncfsa    01xeNb   רֵאשִׁ֖ית
0100100102   GEN_1:1-2   w  1254 a      HVqp3ms  01Nvk    בָּרָ֣א
```

so the seven columns are:

- FGID: Freely-Given 9-digit ID with optional letter suffix for morphemes --
  - two-digit book number 01..39
  - three-digit chapter number 001..150
  - three-digit verse number 001..176
  - two-digit word number 01..99
  - optional letter suffix for morpheme a..e
- Ref: the same reference data duplicated in a different form
  - [BBB](https://freely-given.org/Software/BibleOrganisationalSystem/BOSBooksCodes.html) three-character book code (followed by underline)
  - chapter number 1..150
  - verse number 1..176
  - word number 1..99
  - optional letter suffix for morpheme a..e
- Type: entry type code letter, being one of:
  - w: word
  - m: morpheme
  - seg: Hebrew segment (nothing in the n, Morphology, or OSHBid columns)
  - note: English note (in the Strongs column -- nothing in the final columns)
- Strongs number:
- n:
- Morphology: parsing information
- OSHBid: the original OSHB unique id field for reference (optional a..e letter suffix for morphemes)
- Morpheme: The actual morpheme or word

There are also two JSON formats provided for convenience -- one is a flat list of morpheme entries,
and the other a nested list of books / chapters / verses / morpheme entries.
