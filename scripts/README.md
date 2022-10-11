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
as mostly they are one-off type operations.
We are unable to offer any support for other systems.

We use the _intermediateTexts/_ folder for many of the intermediate data files.

## Old Testament

We use the Open Scriptures Hebrew Bible (OSHB) version of the
Westminster Leningrad Codex (WLC) as our Hebrew (& Aramaic) source text.

This is how we currently form the 39 Old Testament files for the OET-LV-OT:

- echo Take the OSHB WLC words, notes, and segments, and put them into a single TSV table
- ./convert_OSHB_XML_to_TSV.py # words are broken into morphemes -- nine columns -- over half-a-million lines
- echo Expand out the columns ready to add glossing information
- ./prepare_OSHB_for_glossing.py # goes from 9 to 16 columns
- echo Take the Clear.Bible LowFat trees and flatten them into a TSV file -- 32 columns -- almost half-a-million lines
- echo Also creates an abbreviated version with only xx columns
- ./convert_ClearMaculaOT_to_TSV.py -e # Gives errors due to missing particles and word numbers in low-fat trees
- ./apply_Clear_Macula_OT_glosses.py
- ./extract_OSHB_OT_to_USFM.py # TSV table ➔ USFM files
- echo Do programmed word and other substitutions to the USFM files
- ../../ScriptedBibleEditor/Python/ScriptedBibleEditor.py ScriptedVLTUpdates -qe

## New Testament

We use the glosses from the Center for New Testament Restoration (CNTR)
Verifiable Literal Translation (VLT) as our NT source text.

This is how we currently form the 27 New Testament files for the OET-LV-NT:

- echo Convert VLT glosses from still-private CNTR book and collation CSV files to NT USFM files
- ./extract_VLT_NT_to_USFM.py # TSV table ➔ USFM files
- echo Do programmed word and other substitutions to the USFM files
- ../../ScriptedBibleEditor/Python/ScriptedBibleEditor.py ScriptedOTUpdates -qe

## For both

- ./convert_OET-LV_to_simple_HTML.py # USFM files ➔ simple HTML (incl. index) files

## To Do

Although the above scripts form plain-text USFM and HTML files,
lots of linking information is lost,
i.e., the translated words/phrases are not linked to the original language words that they are translated from.
We aim to fix that as soon as we are able to design (yet another) improved Bible file format.

## Prologue

If you’re a professional Bible translator or app developer and able to help us in this endeavour, please start a conversation with us via our [Contact Page](https://Freely-Given.org/Contact.html).
