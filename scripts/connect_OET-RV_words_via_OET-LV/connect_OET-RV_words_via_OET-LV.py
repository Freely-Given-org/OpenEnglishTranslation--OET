#!/usr/bin/env -S uv run
# -\*- coding: utf-8 -\*-
# SPDX-License-Identifier: MPL-2.0
#
# connect_OET-RV_words_via_OET-LV.py
#
# Script to connect OET-RV words with OET-LV words that have word numbers.
#
# Copyright (C) 2023-2026 Robert Hunt
# Author: Robert Hunt <Freely.Given.org+OET@gmail.com>
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Every word in the OET-LV has a word number tag suffixed to it,
    which connects it back to / aligns it with the Hebrew or Greek word it is translated from.

This script attempts to deduce how some of those same words are translated in the OET-RV
    and automatically connect them with the same word number tag.
Curated specialist spans and phrases are followed by positional word/phrase
    alignment, using specialised add spans and the documented clause order.
    Context is considered before verse-wide lexical/name fallback rules commit
    additional anchors. Alignment then repeats using those new anchors.
    Shared spelling prefixes are not lexical evidence. Reviewed related forms
    and positive contraction subjects are weak positional candidates only.
    Function-word fallbacks must respect existing contextual anchors.
    Rebuild tests must start without numbers as well as with existing links:
    preserving historical links can hide links the script cannot reconstruct.
Use --dry-run and --report to evaluate changes, or --output-dir to inspect ESFM
    proposals separately. See scripts/README.md for usage, limits and validation.

It does have the potential to make wrong connections that will need to be manually fixed
        when the rest of the OET-RV words are aligned,
    but hopefully this script is relatively conservative
        so that the number of wrong alignments is not huge.

Specialised \\add spans:
    Normal character markers start with a backslash,
        but embedded character markers (often inside a '\\wj ' words-of-Jesus span)
            must have a + character after the backslash for both the opening and the closing marker,
            so all the following examples that start with '\\' can also start with '\\+'.
    '\\add ' spans must be closed by '\\add*' markers.
        '\\+add ' spans must be closed by '\\+add*' markers.
    The \\add spans below can also indicate uncertainty
        by having a ? immediately after the '\\ add ',
        i.e., before any of the specialist characters (like @*<>≡≈) if present.

    Formats are described at
        ../../../OpenEnglishTranslation-website/src/pages/Resources/Formats.astro

    Unlinked additions: plain '\\add ' spans and context-supplied '\\add <'/'\\add >' spans,
        including their uncertain '?' forms and nested '\\+add' equivalents:
        Any existing word numbers should be removed.
        No new word numbers should be added to these spans.
        Words inside these spans should not be included in word linking statistics.
        Context supplies these words; they have no corresponding OET-LV source word.
        The '\\add <' form is used when an English verb really needs a direct object.
        The '\\add >' form is used often after an article where 'the' refers to 'the one' or 'the person'.
    Pronoun referrent '\\add @' or '\\+add @' or '\\add ?@' or '\\+add ?@' spans:
        Expect the proper noun or fuller description in the OET-RV
            to match a pronoun or simpler description like 'the one' in the OET-LV.
        Known plural heads such as Israelis take precedence over capitalisation;
            individual names such as Barnabas must not be guessed plural from 's'.
    Pronoun substitution '\\add *' or '\\+add *' or '\\add ?*' or '\\+add ?*' spans:
        Expect the pronoun or simpler description in the OET-RV
            to match a proper noun or fuller description in the OET-LV.
    Added ownership '\\add &' or '\\+add &' or '\\add ?&' or '\\+add ?&' spans:
        In this case 'the hand' might become '\\add &his\\add* hand' or '\\add &that\\add* hand'.
        and 'followers' might become '\\add &his\\add* followers'.
        If there's a matching article present, then the OET-RV possessive pronoun
            can be linked to the word number of that OET-LV article.
    Elided '\\add ≡' or '\\+add ≡' or '\\add ?≡' or '\\+add ?≡' spans:
        If the original text that was implied here and then formally reinstated
            can be found earlier in the same verse or in the previous verse,
                then it can be given those matching word number(s).
        TODO: This requires an update in word number checking
            so that a lower word number (from a previous verse) can be allowed in an elided segment.
    Reworded '\\add ≈' or '\\+add ≈' or '\\add ?≈' or '\\+add ?≈' spans:
        Can be matched to OET-LV words, but more difficult expected.
    Alternate '\\add !' or '\\+add !' or '\\add ?!' or '\\+add ?!' name spans:
        Because an English Bible translation is using a mixture of Hebrew, Greek, and English names,
            we often want to display more than one form of the name to the reader.
        The OET-RV mostly puts a rough Hebrew or Greek transliteration first,
            followed by the traditional name in parentheses,
            e.g., 'Shelomo (\\add !Solomon\\add*)'
        Both forms of the name should be linked to the OET-LV name by having the same word number.

Versification: OET-RV uses English (BOS 'eng'); OET-LV uses original ('org').
    BOS maps complete RV passages before any word matching. Verse bridges stay
    together, chapter changes are followed, and Psalm titles use BOS declarations.
    Non-exact mappings and absent LV text are reported and left unlinked.
    Unused LV verses are audited too, exposing incomplete BOS split/merge data.
    All editing addresses and report chapter/verse fields use printed RV numbers.


CHANGELOG:
    2023-07-31 Added character marker checks for each RV line
    2023-08-29 Added nomina sacra (NS) for connected words in RV
    2023-09-11 Fix bug that connected the wrong (not the same) simple words
    2023-09-12 Fix bug that caused two nested /nd markers (when rerunning after numbers had been deleted)
    2023-09-28 Concatenate consecutive /nd fields
    2023-12-20 Check for unwanted trailing spaces on OET-RV lines
    2024-01-24 Check for doubled punctuation and wrong xref punctuation in OET-RV lines
    2024-01-27 Don't allow section headings to be marked with word numbers
    2024-03-25 Add OT connections
    2025-01-04 Started loading and using SBE name tables for automatic name links (not yet fully implemented for NT)
    2025-01-17 Check for bad copy/paste which might include word numbers from a different verse
    2025-02-20 Added check for /nd inside /add fields (which should never happen)
    2025-02-21 Added check for wrongly ordered combos, e.g., \\add #? instead of \\add ?#
    2025-03-07 Align OET-RV /d fields (in Psalms)
    2025-12-12 Remove "failed on" warnings for common word 'to'
    2025-12-13 Add 'fast' flag, added 'heavenly'
    2025-12-17 Add multiprocessing for converting each book (although seems no real time advantange)
    2026-02-24 Added more checking of consecutive opening and closing speech marks
    2026-04-23 Added more assert checks to catch Rust BOS faults
    2026-05-09 Switched to Rust bos_books_codes_py
    2026-05-12 Do more checking before adding NS nd markup
    2026-05-14 Switched to Rust bible_transliterations
    2026-06-11 Handle new % (changed person) \\add format
    2026-06-30 Added verb sets (but they're not fully utilised yet)
    2026-08-19 Allow ../ in lines (used in USFM jmp fields)
    2026-08-23 Added checking for doubled spaces around USFM close character marker fields
    2026-09-04 Don't add word numbers to words that are inside plain (straight) \add spans
    2026-09-25 Remove any existing word numbers from inside plain (straight) \add spans on load
    2026-09-25 Allow word numbers in the new \add !(SomeName)\add* spans
    2026-09-26 Added matchVerbSets() to connect different forms of the same verb (e.g., 'untie' to 'untying')
    2026-09-28 Use the 'Explained' decisions in OET-RV_names_table.tsv when matching proper nouns (e.g., 'Yerushalem')
    2026-09-28 Also treat plain '\\+add ...\\+add*' spans like plain '\\add ...\\add*' spans (no word numbers)
    2026-09-28 Added matchWordsInOrder() to connect words using left-to-right clause order (reversed for '⇔' verses)
    2026-09-28 Remove word numbers from inside straight '\\add'/'\\+add' spans in ALL books on every run (even 'fast'), and report it
    2026-09-28 Use the '≈' (reworded) and '#' (changed number) '\\add' span codes to connect more words (via exposeMatchedAddSpans() and matchWordsWithChangedNumbers())
    2026-09-28 Use the '@' '*' '%' '&' (pronoun/name/owner) and '≡' (repeated) codes too (via matchWordsBesideLvAnchor() and matchRepeatedWords()), and connect the OET-LV alternative names via matchNamesViaAltNames()
    2026-09-29 Connect both the OET-RV name and the traditional name in its '\\add !...\\add*' span to the same OET-LV name, including two-part names like 'John Mark' (via matchNamesViaTraditionalNames(), which replaces matchNamesViaAltNames())
    2026-09-29 Pass the exposed codes to splitExposedAddSpan() and keep exposed punctuation codes out of the word cleanup, so that the '!' code (which is also sentence punctuation) survives to be reported; add the traditional names from OET-RV_names_table.tsv to the OET-LV name spellings so that 'John' can match 'Yōannaʸs'
    2026-09-29 Stop getNameWordsBeforeSpan() at a word that belongs to another '\\add' span, so that we no longer sweep up an unrelated earlier name across e.g. the 'rebuilt' of 'from Beyt-El \\add ≈rebuilt\\add* Yeriho \\add !(Jericho)\\add*' and give it Jericho's word number
    2026-09-29 Removed the no longer productive NAME_ADJUSTMENT_TABLE
    2026-09-29 Report what percentage of the words have word numbers (via countWordsAndWordNumbers() and reportWordNumberPercentage()), for the OT, the NT and the whole Bible, or for the individual book(s) in 'fast' mode
    2026-09-30 Look up the OET-RV name spellings in the OET-LV name command tables without the
        extras that those tables carry, i.e. ignore the '\\add ...\\add*' gloss helpers and the '¦'
        word numbers, and register the last plain word of each '/' or '(' alternative as well, so that
        e.g. the OET-LV 'Farisaios¦_\add (religious leaders)\add*' can be the OET-RV 'Pharisee'
    2026-09-30 Keep a hyphenated word that isn't capitalised as the one word that the OET-RV and the
        OET-LV both use (e.g. 'empty-handed'), while still splitting a capitalised one (e.g. 'Yahweh-nissi')
    2026-09-30 Connect a short word that is exactly the same on both sides (MIN_EXACT_MATCH_WORD_LENGTH
        = 2, e.g. the OET-RV 'put' of Mark 12:1).  This used to be 3, and matchWordsInOrder() also
        used to skip the little English function words that the translators have deliberately left
        unnumbered (LITTLE_FUNCTION_WORDS, now kept only on record).  The order-preserving alignment
        and its every-alignment-agrees test turned out to be selective enough that we can now number
        the little words too, which connected 62,601 more OET-RV words across the whole Bible
        (197,116 of 933,964 = 21.1% before, 259,706 = 27.8% after)
    2026-09-30 Connect an OET-RV word to an OET-LV word that means the same thing but is a different
        word (EQUIVALENT_LV_RV_WORDS, e.g. the OET-RV 'Whenever' against the OET-LV 'wherever'), and
        let a capitalised OET-LV word take part when we have such a synonym for it
    2026-09-30 Let matchWordsInOrder() use two different OET-LV words that share one word number
        (e.g. the OET-LV 'put¦32436' and 'around¦32436' of Mark 12:1), while still skipping an OET-LV
        word that the verse gives exactly the same word and number twice
    2026-09-30 Give addNumberToRVWord() the OET-RV word as the OET-RV really spells it (via
        unSimplifyRVWord()), because it searches for that spelling, so that a capitalised OET-RV word
        such as the 'Whenever' of Mark 9:18 is no longer silently skipped
    2026-09-30 matchOurListedSimpleWords() now skips on to the next word instead of giving up on the
        whole verse when one listed word doesn't match, which is what it meant to do
    2026-09-30 Added a translator-editable table OET-RV_wordPhrases_table.tsv for OET-RV phrases of
        more than one English word that stand for just ONE OET-LV word (e.g. the OET-RV 'you all' for
        the OET-LV 'you_all', and the OET-RV 'young donkey' for the OET-LV 'colt'), and give every
        word of the OET-RV phrase that one OET-LV word number (via loadOETRVWordPhraseTable(),
        matchWordPhrases() and addNumberToRVPhrase())
    2026-09-30 addNumberToRVPhrase() only goes ahead when the phrase occurs exactly once in the
        unnumbered text of the verse, and refuses a phrase whose words already carry a different word
        number, so that a half-connected phrase (e.g. Mark 8:2 'have you all got') is finished off
        with the number that is already there
    2026-10-04 Names in the OET-RV now match via a normalised name index (normalizeNameKey +
        splitNameKey + namePartsIndex built by loadHebGrkNameTables(), and baseNameInCandidates())
        which strips diacritics/macrons/superscripts and splits 'Yəhūdāh/(Judah)' into parts,
        so e.g. the OET-RV 'Yeshua' can match the OET-LV 'Yaʸsous/(Yəhōshūˊa)'.  Also:
        - treat two-column rows of OET-RV_names_table.tsv as candidates as well (not just the 'Y' rows),
          and feed them into rvNameCandidates so that the name command tables can use them
        - treat 'YHWH' in the OET-LV as the OET-RV 'Yahweh'/'LORD' (explicitly added in
          loadHebGrkNameTables())
        - let matchIdenticalProperNouns() connect identical capitalised words in equal lists
        - let matchWordsInOrder() also match words that differ by an inflectional ending of
          up to three letters beyond the five-letter prefix (e.g. RV 'master' with LV 'masters')
        - greatly extended the contraction map in RV_SINGLE_WORDS_FROM_LV_WORD_STRINGS
    2026-10-06 Added the first OT-specific verb sets (play, provoke, slip, wean) after running the
        same OET-RV against OET-LV OT word-table (Morphology 'V...') analysis
    2026-10-06 Removed the conservative "only Messiah/Yeshua/God" nomina sacra allow-list, so that
        a genuine OET-LV nomina sacra match (e.g. the RV "God's¦" at Mrk 8:33, 9:1, 7:9, 7:13)
        now always gets its \\nd ... \\nd* (or \\+nd ... \\+nd*) markup; the CRITICAL messages are gone
    2026-10-06 Added NT noun/adjective singular/plural variant pairs to
        RV_SINGLE_WORDS_FROM_LV_WORD_STRINGS (e.g. ('fish','fishes'), ('body','bodies'),
        ('sign','signs'), ('authority','authorities') ...), which connected ~40 more OET-RV
        words in Mark.
    2026-10-10 Expanded SIMPLE_NOUN_PAIRS and SIMPLE_VERB_SETS from entire OET-RV and OET-LV
    2026-10-10 Extracted positional alignment into oet_alignment.py; indexed verses and lexical
        forms; replaced repeated-word insertion and arbitrary pronoun fallback; added previews,
        selected-book loading and JSON audits; excluded uncertain plain additions consistently.
    2026-10-11 Moved lexical tables into oet_*_tables.py modules and adjusted data paths for
        the connector's own folder under scripts/.
    2026-10-11 Added bounded phrase transpositions with strong lexical evidence and
        punctuation boundaries; preserved existing links and rejected competing moves.
    2026-10-11 Repeat matching for each book until no links are added, retaining
        in-memory edits across passes and reporting per-pass additions.
    2026-10-11 Treat < and > additions like plain additions: remove existing
        numbers and exclude them from matching and coverage, including ?/+add forms.
    2026-10-12 Audit clean rebuilds; align context before lexical fallbacks; index
        directional tables; align repeated directional words and whole phrases;
        recognise I/a, curated noun pairs and LV pronoun metadata; recover
        exact adjacent article/preposition and same-source possessive phrases.
    2026-10-12 Resolve complete eng → org passages through BOS before matching;
        remove Psalm offsets and audit unrepresented LV source verses.
        Include every paired verse's final coverage and texts in JSON reports.
    2026-10-13 Replace arbitrary prefix/ending guesses with reviewed related-form
        families in their own table module, retaining a unique full-word fallback;
        normalise LV bracketed suffixes and
        reflexive-pronoun annotations; align directional pairs without case bias
        and recognise positive contraction subjects. Count already linked forms
        when checking verse-wide lexical ambiguity; recognise capitalised plural
        referents before singular names. Remove three misleading directional pairs;
        distinguish the Israeli demonym phrase from a generic crowd of people.
        Require OT proper-noun morphology and abstain from weak semantic matches
        across overlapping reordered clauses or a preceding name's article.
        Recognise singular common-noun referents and stop traditional-name
        scans at earlier alias spans; explicitly map Shadrak and Meyshak.
        Bound function-word fallbacks by live anchors and prevent their reuse
        across overlapping reordered clauses.
"""
from gettext import gettext as _
from typing import List, Tuple, Optional
from pathlib import Path
from collections import defaultdict
import logging
import re
import multiprocessing
import unicodedata
import json
import time
from functools import lru_cache

from oet_alignment import (LVToken, SEMANTIC_CODES, UNLINKED_ADD_CODES, MOVEMENT_FUNCTION_WORDS, index_book_lines, tokenize,
                           propose_links, with_clause_boundaries, unlinked_add_spans)
from oet_versification import audit_unmapped_lv, resolve_alignment_passages
from oet_derived_word_tables import RELATED_WORD_GROUPS, CONTRACTION_SUBJECTS
from oet_noun_tables import SIMPLE_NOUN_PAIRS, SIMPLE_NOUNS_FLAT, verbalNouns
from oet_verb_tables import SIMPLE_VERB_SETS
from oet_word_tables import SIMPLE_WORDS, EQUIVALENT_LV_RV_WORDS, RV_SINGLE_WORDS_FROM_LV_WORDS
from oet_phrase_tables import RV_SINGLE_WORDS_FROM_LV_WORD_STRINGS, LV_SINGLE_WORDS_TO_RV_WORD_STRINGS

from BibleOrgSys import BibleOrgSysGlobals
from BibleOrgSys.BibleOrgSysGlobals import vPrint, fnPrint, dPrint
from BibleOrgSys.Formats.ESFMBible import ESFMBible
from bible_organisational_system import getPositiveLeadingInt
import bos_books_codes_py
from bible_transliterations import transliterate_Hebrew, transliterate_Greek


LAST_MODIFIED_DATE = '2026-10-13'
SHORT_PROGRAM_NAME = "connect_OET-RV_words_via_OET-LV"
PROGRAM_NAME = "Connect OET-RV words to OET-LV word numbers"
PROGRAM_VERSION = '1.9.0'
PROGRAM_NAME_VERSION = f'{SHORT_PROGRAM_NAME} v{PROGRAM_VERSION}'

DEBUGGING_THIS_MODULE = False


scripts_folderpath = Path(__file__).resolve().parents[1]
project_folderpath = scripts_folderpath.parent # Find folders relative to this module
# FG_folderpath = project_folderpath.parent # Path to find parallel Freely-Given.org repos
OET_LV_ESFM_InputFolderPath = project_folderpath.joinpath( 'derivedTexts/' )
OET_LV_OT_ESFM_InputFolderPath = OET_LV_ESFM_InputFolderPath.joinpath( 'auto_edited_OT_ESFM/' )
OET_LV_NT_ESFM_InputFolderPath = OET_LV_ESFM_InputFolderPath.joinpath( 'auto_edited_VLT_ESFM/' )
OET_RV_ESFM_FolderPath = project_folderpath.joinpath( 'translatedTexts/ReadersVersion/' )
assert OET_LV_OT_ESFM_InputFolderPath.is_dir()
assert OET_LV_NT_ESFM_InputFolderPath.is_dir()
assert OET_RV_ESFM_FolderPath.is_dir()

OET_RV_NAMES_TABLE_FILEPATH = OET_RV_ESFM_FolderPath.joinpath( 'OET-RV_names_table.tsv' )
OET_RV_NAMES_TABLE_HEADER = 'TraditionalName\tRVName\tExplained\tComment'
assert OET_RV_NAMES_TABLE_FILEPATH.is_file()
OET_RV_WORD_PHRASES_TABLE_FILEPATH = OET_RV_ESFM_FolderPath.joinpath( 'OET-RV_wordPhrases_table.tsv' )
OET_RV_WORD_PHRASES_TABLE_HEADER = 'LVWord\tRVWords\tEnabled\tComment'
OT_NameTable_Filepath = scripts_folderpath.joinpath( 'ScriptedOTUpdates/restoreNames.commandTable.tsv' )
NT_OT_NameTable_Filepath = scripts_folderpath.joinpath( 'ScriptedVLTUpdates/OTNames.commandTable.tsv' )
NT_NameTable_Filepath = scripts_folderpath.joinpath( 'ScriptedVLTUpdates/NTNames.commandTable.tsv' )
COMMAND_TABLE_NUM_COLUMNS = 15
COMMAND_HEADER_LINE = 'Tags	IBooks	EBooks	IMarkers	EMarkers	IRefs	ERefs	PreText	SCase	Search	PostText	RCase	Replace	Name	Comment'
assert ' ' not in COMMAND_HEADER_LINE
assert COMMAND_HEADER_LINE.count( '\t' ) == COMMAND_TABLE_NUM_COLUMNS - 1
# class EditCommand(NamedTuple):
#     tags: str           # 0
#     iBooks: list        # 1
#     eBooks: list        # 2
#     iMarkers: list      # 3
#     eMarkers: list      # 4
#     iRefs: list         # 5
#     eRefs: list         # 6
#     preText: str        # 7
#     sCase: str          # 8
#     searchText: str     # 9
#     postText: str       # 10
#     rCase: str          # 11
#     replaceText: str    # 12
#     name: str           # 13
#     comment: str        # 14


class WordNumberError(ValueError):
    pass


class State:
    """
    A place to store some of the global stuff that needs to be passed around.
    """
    def __init__(self):
        self.bookLinkAdditions = 0 # Increment only after a successful insertion.
# end of State class

state = State()


def loadAlignmentBible(folder, abbreviation, versification):
    """Avoid parsing all 66 books when --books selects a subset."""
    bible = ESFMBible(folder, givenAbbreviation=abbreviation, versification=versification)
    bible.loadAuxiliaryFiles = True
    options = BibleOrgSysGlobals.commandLineArguments
    selected = options.books
    if selected:
        bible.preload()
        bible.loadDictionaries()
        for BBB in selected:
            if BBB in bible.possibleFilenameDict:
                bible.loadBook(BBB)
        if bible.books:
            bible.lookForAuxiliaryFilenames()
            bible.doPostLoadProcessing()
    else:
        bible.loadBooks()
    return bible


# forList = []
def main():
    """
    Main program to handle command line parameters and then run what they want.
    """
    BibleOrgSysGlobals.introduceProgram( __name__, PROGRAM_NAME_VERSION, LAST_MODIFIED_DATE )

    # global genericBookList
    # genericBibleOrganisationalSystem = BibleOrganisationalSystem( 'GENERIC-KJV-ENG' )
    # genericBookList = genericBibleOrganisationalSystem.getBookList()

    # Clean only selected books in memory. Preview/output runs must not touch sources.
    state.audit = []
    state.bookReports = []
    started = time.perf_counter()
    options = BibleOrgSysGlobals.commandLineArguments
    if options.report:
        BibleOrgSysGlobals.maxProcesses = 1 # Collect a deterministic, verse-level audit.
    if options.output_dir:
        options.output_dir.mkdir(parents=True, exist_ok=True)

    rv = loadAlignmentBible(OET_RV_ESFM_FolderPath, 'OET-RV', 'eng')
    lvOT = loadAlignmentBible(OET_LV_OT_ESFM_InputFolderPath, 'OET-LV', 'org')
    lvNT = loadAlignmentBible(OET_LV_NT_ESFM_InputFolderPath, 'OET-LV', 'org')

    # Load the OT and NT word files
    state.wordTable, state.wordTableHeaderList = {}, {}
    for testament in ('OT','NT'):
        lv = lvOT if testament=='OT' else lvNT
        if not lv.books:
            continue
        BBB = next(iter(lv.books))
        input_folder_path = OET_LV_OT_ESFM_InputFolderPath if testament=='OT' else OET_LV_NT_ESFM_InputFolderPath
        lvBookObject = lv[BBB]
        wordFileName = lvBookObject.ESFMWordTableFilename
        if wordFileName:
            assert wordFileName.endswith( '.tsv' )
            if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 3:
                vPrint( 'Info', DEBUGGING_THIS_MODULE, f"  Found ESFMBible filename '{wordFileName}' for {lv.abbreviation} {BBB}" )
            if lv.ESFMWordTables[wordFileName]:
                if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 3:
                    vPrint( 'Info', DEBUGGING_THIS_MODULE, f"  Found ESFMBible loaded '{wordFileName}' word link lines: {len(lv.ESFMWordTables[wordFileName]):,}" )
            else:
                if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 3:
                    vPrint( 'Info', DEBUGGING_THIS_MODULE, f"  No word links loaded yet for '{wordFileName}'" )
            if lv.ESFMWordTables[wordFileName] is None:
                with open( input_folder_path.joinpath(wordFileName), 'rt', encoding='UTF-8' ) as wordFile:
                    lv.ESFMWordTables[wordFileName] = wordFile.read().split( '\n' )
                if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 2:
                    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  connect_OET_RV loaded {len(lv.ESFMWordTables[wordFileName]):,} total rows from {wordFileName}" )
                if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
                    dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  connect_OET_RV loaded column names were: ({len(lv.ESFMWordTables[wordFileName][0])}) {lv.ESFMWordTables[wordFileName][0]}" )
        state.wordTable[testament] = [row.split('\t') for row in lv.ESFMWordTables[wordFileName]]
        state.wordTableHeaderList[testament] = state.wordTable[testament][0]

    # Load the Hebrew and Greek name tables from TSV files
    loadOETRVNameTable()
    loadHebGrkNameTables()
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 4:
        dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"{state.nameTables=}")

    # Load the OET-RV words that are more than one word for one OET-LV word, e.g. 'you all'
    loadOETRVWordPhraseTable()

    # Display anywhere where we still have 'for' that should perhaps be 'because'
    # show_fors( lv )

    # Connect linked words in the OET-LV to the OET-RV
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 1:
        vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"\nProcessing connect words for OET OT…" )
    numWordsOT,numWordNumberedOT = connect_OET_RV( rv, lvOT, OET_LV_OT_ESFM_InputFolderPath, 'OT' ) # OT
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 1:
        vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"\nProcessing connect words for OET NT…" )
    numWordsNT,numWordNumberedNT = connect_OET_RV( rv, lvNT, OET_LV_NT_ESFM_InputFolderPath, 'NT' ) # NT

    # Selected-book runs report only the books actually processed.
    if not options.books:
        reportWordNumberPercentage( "Whole Bible", numWordsOT+numWordsNT, numWordNumberedOT+numWordNumberedNT )

    if options.report:
        options.report.parent.mkdir(parents=True, exist_ok=True)
        options.report.write_text(json.dumps({
            'seconds': round(time.perf_counter()-started, 3),
            'dry_run': options.dry_run, 'books': state.bookReports,
            'links': state.audit,
        }, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    if not options.dry_run and not options.output_dir:
        for something in OET_RV_ESFM_FolderPath.glob('*.OBD_Bible.pickle'):
            something.unlink()
# end of connect_OET-RV_words_via_OET-LV.main


def loadOETRVNameTable() -> None:
    """
    Load the translator's decisions about how proper names are spelled in the OET-RV.

    The Search column of the ScriptedBibleEditor command tables is the traditional/KJB spelling,
        which we often have to guess at when matching it to an OET-LV transliterated name
        (e.g., we blindly turn a leading 'J' into a 'Y', which gets 'Jerusalem' -> 'Yerusalem'
            instead of the 'Yerushalem' that we actually use).
    This table records the real decision, so we prefer it wherever the translator has flagged a row
        with an 'Explained' flag of 'Y'.
    Rows without that flag are just candidates, so we deliberately ignore them.
    """
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 1:
        vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  Loading decided OET-RV names from {OET_RV_NAMES_TABLE_FILEPATH}…" )
    state.rvNameTable = defaultdict( set ) # traditionalName -> set of accepted OET-RV spellings
    state.rvNameCandidates = defaultdict( set ) # traditionalName -> set of ALL known OET-RV spellings (decided or not)
    with open( OET_RV_NAMES_TABLE_FILEPATH, 'rt', encoding='utf-8' ) as namesTableFile:
        tsvLines = namesTableFile.read().rstrip().split( '\n' )
    if tsvLines[0].startswith( '\ufeff' ): tsvLines[0] = tsvLines[0][1:] # Remove any BOM
    assert tsvLines[0] == OET_RV_NAMES_TABLE_HEADER, f"Expected '{OET_RV_NAMES_TABLE_HEADER}' but found '{tsvLines[0]}' in {OET_RV_NAMES_TABLE_FILEPATH}"

    for line in tsvLines[1:]:
        fields = line.split( '\t' )
        if len(fields) < 2: continue # Some editors delete trailing columns
        traditionalName, rvName = fields[0].strip(), fields[1].strip()
        explained = fields[2].strip() if len(fields) >= 3 else ''
        if not traditionalName or not rvName: continue
        # The OET-RV uses straight apostrophes inside names, but the table uses curly ones, e.g., 'Sha’ul'
        state.rvNameCandidates[traditionalName.replace( '’', "'" )].add( rvName.replace( '’', "'" ) )
        if explained.upper() != 'Y': continue # Only the translator's decisions (not just candidates)
        state.rvNameTable[traditionalName.replace( '’', "'" )].add( rvName.replace( '’', "'" ) )
    state.rvNameTableInverse = defaultdict( set ) # OET-RV spelling -> set of traditional names for it
    for traditionalName,rvNames in state.rvNameTable.items():
        for rvName in rvNames: state.rvNameTableInverse[simplifyRVLVWord( rvName )].add( traditionalName )
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 2:
        vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"    Loaded {len(state.rvNameTable):,} decided OET-RV names covering {sum(len(v) for v in state.rvNameTable.values()):,} spellings." )
# end of connect_OET-RV_words_via_OET-LV.loadOETRVNameTable


def loadOETRVWordPhraseTable() -> None:
    """
    Load the translator's decisions about the OET-RV words that are MORE THAN ONE English word
        which together translate just ONE OET-LV word, e.g.
            the OET-LV 'you_all' (one Hebrew or Greek word, the plural 'you') which the OET-RV
                often writes as the two words 'you all' (1,281 times in the OET-RV)
            the OET-LV 'colt' which the OET-RV writes as the two words 'young donkey'
        (The other way round, i.e. several OET-LV words for one OET-RV word, is the OET-LV's own
        'first word/English gloss' convention, e.g. the OET-LV 'he/it' or 'possessions/wealth',
        and matchWordsInOrder() already lets any of those alternatives match the OET-RV word.)

    'LVWord' is the OET-LV word, spelled the way the OET-LV spells it, i.e. with an underscore
        between the parts of one word ('you_all'); a space works there too.
    'RVWords' is what the OET-RV actually uses, with a space between the words ('you all').
    Only the rows that the translator has flagged with an 'Enabled' of 'Y' are used, so that
        candidates can be listed in the table without being acted on yet (as with the names table).
    """
    state.rvWordPhrases = {} # (simplified LV words) -> (simplified RV words), e.g. ('you','all') -> ('you','all')
    if not OET_RV_WORD_PHRASES_TABLE_FILEPATH.is_file():
        logging.warning( f"Can't find the OET-RV word phrases table {OET_RV_WORD_PHRASES_TABLE_FILEPATH}, so no multi-word translations will be connected" )
        return
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 1:
        vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  Loading enabled OET-RV word phrases from {OET_RV_WORD_PHRASES_TABLE_FILEPATH}…" )
    state.rvWordPhrasesSearch = {} # (simplified RV words) -> (RV words as the OET-RV spells them)
    tsvLines = OET_RV_WORD_PHRASES_TABLE_FILEPATH.read_text( encoding='utf-8' ).rstrip().split( '\n' )
    if tsvLines[0].startswith( '﻿' ): tsvLines[0] = tsvLines[0][1:] # Remove any BOM
    assert tsvLines[0] == OET_RV_WORD_PHRASES_TABLE_HEADER, f"Expected '{OET_RV_WORD_PHRASES_TABLE_HEADER}' but found '{tsvLines[0]}' in {OET_RV_WORD_PHRASES_TABLE_FILEPATH}"

    for line in tsvLines[1:]:
        fields = line.split( '\t' )
        if len(fields) < 3: continue # Some editors delete trailing columns
        lvWordStr, rvWordsStr, enabled = fields[0].strip(), fields[1].strip(), fields[2].strip()
        if not lvWordStr or not rvWordsStr: continue
        if enabled.upper() != 'Y': continue # Only the translator's decisions (not just candidates)
        lvWords = tuple( simplifyRVLVWord( word ) for word in lvWordStr.replace( '_', ' ' ).split() )
        rvWords = tuple( rvWordsStr.split() )
        assert lvWords and all( lvWords ), f"Bad LVWord '{lvWordStr}' in {OET_RV_WORD_PHRASES_TABLE_FILEPATH}"
        if len( rvWords ) < 2:
            logging.warning( f"Skipping the OET-RV word phrases row '{lvWordStr}' -> '{rvWordsStr}', because a single OET-RV word belongs in SINGLE_WORD_MAPPINGS instead" )
            continue
        state.rvWordPhrases[ lvWords ] = tuple( simplifyRVLVWord( word ) for word in rvWords )
        state.rvWordPhrasesSearch[ tuple( simplifyRVLVWord( word ) for word in rvWords ) ] = rvWords
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 2:
        vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"    Loaded {len(state.rvWordPhrases):,} enabled OET-RV word phrases." )
# end of connect_OET-RV_words_via_OET-LV.loadOETRVWordPhraseTable

# The name command tables record a name the way the OET-LV text spells it, which means with the
#   '¦' word number, with the '\add …\add*' gloss helpers that come with it, and with the '_' that
#   joins the English glosses of the one OET-LV word, e.g. the Search 'Pharisee¦' and Replace
#   'Φαρισαῖος¦_\add party¦\add*' of the OET-RV 'Pharisees', or the Search 'Arabs¦' and Replace
#   '\add >ones¦\add*_from¦_Ἀραβία¦' of the OET-RV 'Arabs'.  A name lookup on the plain OET-LV
#   name ('Farisaios', 'Arabia') can't find such a key, so cleanNameTableField() and
#   getPlainNameKeys() below give us the plain spelling of the name as well.
NAME_GLOSS_HELPER_REGEX = re.compile( r'\\add[^*]*\\add\*' ) # e.g. the '\add party¦\add*' of 'Φαρισαῖος¦_\add party¦\add*'
WORD_NUMBER_MARKER_REGEX = re.compile( r'¦\d*' ) # e.g. '¦32660', or a bare '¦' that has lost its number
NAME_ALTERNATIVE_REGEX = re.compile( r'[/(]' ) # The '/' or '(' of an alternative spelling, e.g. 'Yəhūdāh/Judah'
# The English words that the OET-LV uses to gloss one OET-LV word, which are never the name
#   itself, e.g. the 'from' of 'from¦X_Ἀραβία¦X' or the 'tribe of' of
#   'from¦X_tribe¦X_of¦X_לֵוִי¦X'.
NAME_GLOSS_WORDS = { 'a','an','in','of','one','ones','supporters','the','tribe' }


def cleanNameTableField( name:str ) -> str:
    """
    Return a name from a name command table with the OET-LV word number marker taken off it,
        e.g. 'Pharisee¦' becomes 'Pharisee', so that it matches an OET-RV name.
    """
    return WORD_NUMBER_MARKER_REGEX.sub( '', name ).strip()
# end of connect_OET-RV_words_via_OET-LV.cleanNameTableField


def getPlainNameKeys( replaceText:str ) -> List[str]:
    """
    Return the plain word that a name command table records a name as, i.e. without the word
        number marker, the gloss helpers and the '_' joins, so that a name lookup on the OET-LV
        name itself can find it, e.g. ['Farisaios'] for 'Φαρισαῖος¦_\\add party¦\\add*' and
        ['Arabia'] for '\\add >ones¦\\add*_from¦_Ἀραβία¦'.

    We take the LAST plain word of each alternative, because that is the name itself, with the
        English glosses in front of it ('ones from Arabia', 'from tribe of Levi'), while any plain
        word that comes AFTER the name qualifies it, and so is a different name: the 'zaʸlōtaʸs' of
        'Φαρισαῖος¦_zaʸlōtaʸs¦_\\add group¦_member¦\\add*' is a Zealot, not a Pharisee.
    """
    cleaned = WORD_NUMBER_MARKER_REGEX.sub( ' ', NAME_GLOSS_HELPER_REGEX.sub( ' ', replaceText ) )
    keys = []
    for alternative in NAME_ALTERNATIVE_REGEX.split( cleaned ):
        words = [ word for word in alternative.replace( '_', ' ' ).split() if word not in NAME_GLOSS_WORDS ]
        if words: keys.append( words[-1] )
    return keys
# end of connect_OET-RV_words_via_OET-LV.getPlainNameKeys


def addPlainNameKeys( nameTableKey:str, replaceText:str, searchText:str, rvNameChoices:set ) -> None:
    """
    Save a name from a name command table under the plain OET-LV name as well as under the full
        Replace text (which has the word number marker, the gloss helpers and the '_' joins in it),
        so that both matchAdjustedProperNouns() and getLVNameSpellings() can find it when they look
        the OET-LV name up, e.g. the OET-RV 'Pharisee' against the OET-LV 'Farisaios'.
    """
    for plainName in getPlainNameKeys( replaceText ):
        state.nameTables[nameTableKey][plainName].update( rvNameChoices )
        state.nameTables[nameTableKey][plainName].add( searchText )
# end of connect_OET-RV_words_via_OET-LV.addPlainNameKeys


def loadHebGrkNameTables():
    """
    Loads three TSV files into state.nameTables

    These are the ScriptedBibleEditor command files that create the Hebrew and Greek proper names for the OET-LV.
    """
    state.nameTables = {}

    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 1:
        vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  Loading OT names from {OT_NameTable_Filepath}…" )
    state.nameTables['OT'] = defaultdict( set )
    with open( OT_NameTable_Filepath, 'rt', encoding='utf-8' ) as commandTableFile:
        line_number = 0
        for line in commandTableFile:
            line_number += 1
            line = line.rstrip( '\r\n' )
            if not line or line.startswith( '#' ): continue
            tab_count = line.count( '\t' )
            if tab_count>9 and tab_count < (COMMAND_TABLE_NUM_COLUMNS - 1): # Some editors delete trailing columns
                line += '\t' * (COMMAND_TABLE_NUM_COLUMNS - 1 - tab_count) # Add back the empty columns
                tab_count = line.count( '\t' )
            if tab_count != (COMMAND_TABLE_NUM_COLUMNS - 1):
                logging.critical( f"Skipping line {line_number} which contains {tab_count} tabs (instead of {COMMAND_TABLE_NUM_COLUMNS - 1})" )
            if line == COMMAND_HEADER_LINE:
                continue # as no need to save this

            # Get the fields and check some of them
            fields = line.split( '\t' ) # 0:Tags 1:IBooks 2:EBooks 3:IMarkers 4:EMarkers 5:IRefs 6:ERefs 7:PreText 8:SCase 9:Search 10:PostText 11:RCase 12:Replace 13:Name 14:Comment
            tags, searchText, replaceText = fields[0], fields[9], fields[12]
            # print( f"{searchText=} {replaceText=}")
            if 'H' in tags:
                searchText = cleanNameTableField( searchText ) # Take off any OET-LV word number marker, e.g. 'Chaldeans¦'
                traditionalName = searchText # Save this before we mangle it below
                if searchText.startswith( 'J' ): searchText = f'Y{searchText[1:]}' # Replace first letter J with Y
                rvNameChoices = state.rvNameTable.get( traditionalName, set() ) | state.rvNameCandidates.get( traditionalName, set() ) # What we actually call it in the OET-RV

                # newReplaceText = transliterate_Hebrew( replaceText, capitaliseHebrew=searchText[0].isupper() )
                # if newReplaceText != replaceText:
                #     # print(f" Converted Hebrew '{replaceText}' to '{newReplaceText}'")
                #     replaceText = newReplaceText
                replaceText = transliterate_Hebrew( replaceText, capitalise_hebrew=searchText[0].isupper() )
                    # NOTE: The below makes it WORSE
                    # # We replace out the special characters (from our transliteration function)
                    # .replace( 'Ā', 'A' ).replace( 'Ē', 'E' )
                    # .replace( 'Ḩ', 'H' )
                    # .replace( 'ₐ', 'a' ).replace( 'ə', 'e' )
                    # .replace( 'ā', 'a' ).replace( 'ē', 'e' ).replace( 'ī', 'i' ).replace( 'ō', 'o' ).replace( 'ū', 'u' )
                    # .replace( 'ḩ', 'h' ).replace( 'ⱪ', 'k' ).replace( 'q', 'k' ).replace( 'ʦ', 'ts' ).replace( 'ⱱ', 'v' )
                    # )
                if '/' in replaceText:
                    assert 'd' in tags, f"OT {tags=} {searchText=} {replaceText=}"
                    replaceText = replaceText.replace( '(', '' ).replace( ')', '' ) # We don't want the brackets
                    shortenedReplaceText = replaceText.split( '/' )[0]
                    # assert shortenedReplaceText not in state.nameTables['OT'], f"{tags=} {searchText=} {replaceText=} {shortenedReplaceText=}"
                    state.nameTables['OT'][shortenedReplaceText].update( rvNameChoices )
                    state.nameTables['OT'][shortenedReplaceText].add( searchText ) # We add an extra entry
                    if searchText.endswith( 'iah' ): # e.g. Azariah
                        state.nameTables['OT'][shortenedReplaceText].add( f'{searchText[:-3]}yah' ) # We add an extra entry
                    elif searchText.endswith( 'ieh' ):
                        state.nameTables['OT'][shortenedReplaceText].add( f'{searchText[:-3]}yeh' ) # We add an extra entry
                    if 'j' in searchText and 'j' not in replaceText: # e.g., Benjamin
                        state.nameTables['OT'][shortenedReplaceText].add( searchText.replace( 'j', 'y' ) ) # We add an extra entry
                    if 'ph' in searchText and 'ph' not in replaceText: # e.g., Naphtali
                        state.nameTables['OT'][shortenedReplaceText].add( searchText.replace( 'ph', 'f' ) ) # We add an extra entry
                    if 'sh' in replaceText and 'sh' not in searchText and 's' in searchText: # e.g., Yerushalem
                        # assert 's' in searchText, f"{searchText=} {replaceText=}"
                        state.nameTables['OT'][shortenedReplaceText].add( searchText.replace( 's', 'sh' ) ) # We add an extra entry
                    if 'th' in searchText and 'th' not in replaceText: # e.g., Yotham
                        state.nameTables['OT'][shortenedReplaceText].add( searchText.replace( 'th', 't' ) ) # We add an extra entry
                    if 'v' in replaceText and 'v' not in searchText and 'b' in searchText: # e.g., Argob
                        state.nameTables['OT'][shortenedReplaceText].add( searchText.replace( 'b', 'v' ) ) # We add an extra entry
                    if 'z' in searchText and 'ts' in replaceText: # e.g., Hatzor
                        state.nameTables['OT'][shortenedReplaceText].add( searchText.replace( 'z', 'ts' ) ) # We add an extra entry
                    if searchText.startswith('Z') and replaceText.startswith('Ts'): # e.g., Ziklag
                        state.nameTables['OT'][shortenedReplaceText].add( f'Ts{searchText[1:]}' ) # We add an extra entry
                # assert replaceText not in state.nameTables['OT'], f"{tags=} {searchText=} {replaceText=}"
                state.nameTables['OT'][replaceText].update( rvNameChoices )
                state.nameTables['OT'][replaceText].add( searchText )
                if searchText.endswith( 'iah' ):
                    state.nameTables['OT'][replaceText].add( f'{searchText[:-3]}yah' ) # We add an extra entry
                elif searchText.endswith( 'ieh' ):
                    state.nameTables['OT'][replaceText].add( f'{searchText[:-3]}yeh' ) # We add an extra entry
                if 'j' in searchText: # e.g., Benjamin
                    state.nameTables['OT'][replaceText].add( searchText.replace( 'j', 'y' ) ) # We add an extra entry
                if 'ph' in searchText: # e.g., Naphtali
                    state.nameTables['OT'][replaceText].add( searchText.replace( 'ph', 'f' ) ) # We add an extra entry
                if 'sh' in replaceText and 'sh' not in searchText and 's' in searchText: # e.g., Yerushalem
                    # assert 's' in searchText, f"{searchText=} {replaceText=}"
                    state.nameTables['OT'][replaceText].add( searchText.replace( 's', 'sh' ) ) # We add an extra entry
                if 'th' in searchText and 'th' not in replaceText: # e.g., Yotham
                    state.nameTables['OT'][replaceText].add( searchText.replace( 'th', 't' ) ) # We add an extra entry
                if 'v' in replaceText and 'v' not in searchText and 'b' in searchText: # e.g., Argob
                    state.nameTables['OT'][replaceText].add( searchText.replace( 'b', 'v' ) ) # We add an extra entry
                if 'z' in searchText and 'ts' in replaceText: # e.g., Hatzor
                    state.nameTables['OT'][replaceText].add( searchText.replace( 'z', 'ts' ) ) # We add an extra entry
                if searchText.startswith('Z') and replaceText.startswith('Ts'): # e.g., Ziklag
                    state.nameTables['OT'][replaceText].add( f'Ts{searchText[1:]}' ) # We add an extra entry
                addPlainNameKeys( 'OT', replaceText, searchText, rvNameChoices )
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 2:
        vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"    Loaded {len(state.nameTables['OT']):,} OT names." )
    # print( f"{state.nameTables['OT']['Mənaḩēm']=}" ); assert False, "We want to stop here"

    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 1:
        vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  Loading NT OT names from {NT_OT_NameTable_Filepath}…" )
    state.nameTables['NT_OT'] = defaultdict( set )
    with open( NT_OT_NameTable_Filepath, 'rt', encoding='utf-8' ) as commandTableFile:
        line_number = 0
        for line in commandTableFile:
            line_number += 1
            line = line.rstrip( '\r\n' )
            if not line or line.startswith( '#' ): continue
            tab_count = line.count( '\t' )
            if tab_count>9 and tab_count < (COMMAND_TABLE_NUM_COLUMNS - 1): # Some editors delete trailing columns
                line += '\t' * (COMMAND_TABLE_NUM_COLUMNS - 1 - tab_count) # Add back the empty columns
                tab_count = line.count( '\t' )
            if tab_count != (COMMAND_TABLE_NUM_COLUMNS - 1):
                logging.critical( f"Skipping line {line_number} which contains {tab_count} tabs (instead of {COMMAND_TABLE_NUM_COLUMNS - 1})" )
            if line == COMMAND_HEADER_LINE:
                continue # as no need to save this

            # Get the fields and check some of them
            fields = line.split( '\t' ) # 0:Tags 1:IBooks 2:EBooks 3:IMarkers 4:EMarkers 5:IRefs 6:ERefs 7:PreText 8:SCase 9:Search 10:PostText 11:RCase 12:Replace 13:Name 14:Comment
            tags, searchText, replaceText = fields[0], fields[9], fields[12]
            # print( f"{searchText=} {replaceText=}")
            if 'HG' in tags:
                searchText = cleanNameTableField( searchText ) # Take off any OET-LV word number marker
                traditionalName = searchText # Save this before we mangle it below
                if searchText.startswith( 'J' ): searchText = f'Y{searchText[1:]}' # Replace first letter J with Y
                rvNameChoices = state.rvNameTable.get( traditionalName, set() ) | state.rvNameCandidates.get( traditionalName, set() ) # What we actually call it in the OET-RV
                newReplaceText = transliterate_Greek( transliterate_Hebrew( replaceText, capitalise_hebrew=searchText[0].isupper() ) )
                if newReplaceText != replaceText:
                    # print(f" Converted Hebrew/Greek '{replaceText}' to '{newReplaceText}'")
                    replaceText = newReplaceText
                if '/' in replaceText:
                    assert 'd' in tags, f"OT_NT {tags=} {searchText=} {replaceText=}"
                    replaceText = replaceText.replace( '(', '' ).replace( ')', '' ) # We don't want the brackets
                    shortenedReplaceText = replaceText.split( '/' )[0]
                    # assert shortenedReplaceText not in state.nameTables['NT_OT'], f"{tags=} {searchText=} {replaceText=} {shortenedReplaceText=}"
                    state.nameTables['NT_OT'][shortenedReplaceText].update( rvNameChoices )
                    state.nameTables['NT_OT'][shortenedReplaceText].add ( searchText ) # We add an extra entry
                # assert replaceText not in state.nameTables['NT_OT'], f"{tags=} {searchText=} {replaceText=}"
                state.nameTables['NT_OT'][replaceText].update( rvNameChoices )
                state.nameTables['NT_OT'][replaceText].add( searchText )
                addPlainNameKeys( 'NT_OT', replaceText, searchText, rvNameChoices )
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 2:
        vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"    Loaded {len(state.nameTables['NT_OT']):,} NT OT names." )

    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 1:
        vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  Loading NT names from {NT_NameTable_Filepath}…" )
    state.nameTables['NT'] = defaultdict( set )
    with open( NT_NameTable_Filepath, 'rt', encoding='utf-8' ) as commandTableFile:
        line_number = 0
        for line in commandTableFile:
            line_number += 1
            line = line.rstrip( '\r\n' )
            if not line or line.startswith( '#' ): continue
            tab_count = line.count( '\t' )
            if tab_count>9 and tab_count < (COMMAND_TABLE_NUM_COLUMNS - 1): # Some editors delete trailing columns
                line += '\t' * (COMMAND_TABLE_NUM_COLUMNS - 1 - tab_count) # Add back the empty columns
                tab_count = line.count( '\t' )
            if tab_count != (COMMAND_TABLE_NUM_COLUMNS - 1):
                logging.critical( f"Skipping line {line_number} which contains {tab_count} tabs (instead of {COMMAND_TABLE_NUM_COLUMNS - 1})" )
            if line == COMMAND_HEADER_LINE:
                continue # as no need to save this

            # Get the fields and check some of them
            fields = line.split( '\t' ) # 0:Tags 1:IBooks 2:EBooks 3:IMarkers 4:EMarkers 5:IRefs 6:ERefs 7:PreText 8:SCase 9:Search 10:PostText 11:RCase 12:Replace 13:Name 14:Comment
            tags, searchText, replaceText = fields[0], fields[9], fields[12]
            # print( f"{searchText=} {replaceText=}")
            if 'G' in tags:
                searchText = cleanNameTableField( searchText ) # Take off any OET-LV word number marker, e.g. 'Pharisees¦'
                traditionalName = searchText # Save this before we mangle it below
                if searchText.startswith( 'J' ): searchText = f'Y{searchText[1:]}' # Replace first letter J with Y
                rvNameChoices = state.rvNameTable.get( traditionalName, set() ) | state.rvNameCandidates.get( traditionalName, set() ) # What we actually call it in the OET-RV
                newReplaceText = transliterate_Greek( replaceText )
                if newReplaceText != replaceText:
                    # print(f" Converted Greek '{replaceText}' to '{newReplaceText}'")
                    replaceText = newReplaceText
                if '/' in replaceText:
                    assert 'd' in tags, f"NT {tags=} {searchText=} {replaceText=}"
                    replaceText = replaceText.replace( '(', '' ).replace( ')', '' ) # We don't want the brackets
                    shortenedReplaceText = replaceText.split( '/' )[0]
                    # assert shortenedReplaceText not in state.nameTables['NT'], f"{tags=} {searchText=} {replaceText=} {shortenedReplaceText=}"
                    state.nameTables['NT'][shortenedReplaceText].update( rvNameChoices )
                    state.nameTables['NT'][shortenedReplaceText].add( searchText ) # We add an extra entry
                # assert replaceText not in state.nameTables['NT'], f"{tags=} {searchText=} {replaceText=}"
                state.nameTables['NT'][replaceText].update( rvNameChoices )
                state.nameTables['NT'][replaceText].add( searchText )
                addPlainNameKeys( 'NT', replaceText, searchText, rvNameChoices )
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 2:
        vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"    Loaded {len(state.nameTables['NT']):,} NT names." )

    # Add the divine-name forms that the LV uses directly (not produced by a Hebrew transliteration)
    state.nameTables['OT']['YHWH'].update( { 'Yahweh', 'LORD', 'Lord' } )
    # A normalised, flattened index of every name spelling known to the command tables,
    #   so that we can match an OET-LV capitalised word whose transliteration doesn't match
    #   any table key exactly (accents on/off, macrons, superscripts, slash alternatives, etc.)
    state.namePartsIndex = defaultdict( set )
    for nameTable in state.nameTables.values():
        for tableKey,rvNameCandidates in nameTable.items():
            for part in splitNameKey( tableKey ):
                normalised = normalizeNameKey( part )
                if normalised:
                    state.namePartsIndex[normalised].update( rvNameCandidates )
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 2:
        vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"    Built a normalised name index of {len(state.namePartsIndex):,} entries." )
# end of connect_OET-RV_words_via_OET-LV.loadHebGrkNameTables


_NAME_KEY_SEPARATORS = re.compile( r'[/()\[\]{}\\+_]' )
_NAME_KEY_STRIP_CHARS = " ˊ'‘’`ʹʼ¨¯´˸ـ-"

def splitNameKey( name:str ) -> List[str]:
    """Split a name key into its alternatives, e.g. 'Dawid/(Dāvid)' -> ['Dawid', 'Dāvid']."""
    return [ part for part in _NAME_KEY_SEPARATORS.split( name ) if part.strip() ]
# end of splitNameKey


def normalizeNameKey( name:str ) -> str:
    """Reduce a name to a lowercase ASCII form with no diacritics or accessorisation,
        so that e.g. 'Yəhōyāqīm' and 'YEHOIAKIM' and 'Yəhōyākīm' all look alike."""
    name = unicodedata.normalize( 'NFKD', name )
    name = ''.join( ch for ch in name if unicodedata.category( ch ) != 'Mn' )
    for ch in _NAME_KEY_STRIP_CHARS: name = name.replace( ch, '' )
    return name.lower().strip( '.,;:!?"“”‘’-' )
# end of normalizeNameKey


illegalWordLinkRegex1 = re.compile( '[0-9]¦' ) # Has digits BEFORE the broken pipe
illegalWordLinkRegex2 = re.compile( '¦[1-9][0-9]{0,5}[a-z]' ) # Has letters immediately AFTER the wordlink number
doubledND, badAddND, badNDAdd = '\\nd \\nd ', '\\add \\nd ', '\\nd*\\add*'
def connect_OET_RV( rv, lv, OET_LV_ESFM_InputFolderPath, testament:str ):
    """
    Firstly, load the OET-LV wordtable.
        Loads into state.wordTableHeaderList and state.wordTable.

    Check that any existing word numbers are in the correct verse.

    Then connect linked words in the OET-LV to the OET-RV.

    testament is either 'OT' or 'NT', and is used to label the word count summaries.

    Returns a (numWords,numWordNumbered) tuple for this testament, i.e. how many of the OET-RV
        words of the books that we processed could have a word number, and how many of them
        have one (see countWordsAndWordNumbers()), so that main() can add the two testaments
        together for a whole Bible figure.
    """
    assert testament in ('OT','NT'), f"Bad {testament=}"
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag:
        fnPrint( DEBUGGING_THIS_MODULE, f"connect_OET_RV( {rv}, {lv} {testament} )" )

    # Make a list of the books that we're going to process
    booklist_to_process = []
    selected = BibleOrgSysGlobals.commandLineArguments.books
    for BBB in lv.books:
        if selected and BBB not in selected:
            continue
        # if BBB in ('CO1',): continue # TODO: CO1_14:33 gives an issue
        booklist_to_process.append( BBB )
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 2:
        vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Created a list of {len(booklist_to_process)} OET books to process." )

    # Go through books chapters and verses
    totalWordPhraseAdds = totalSimpleListedAdds = totalProperNounAdds = totalUniqueExactMatchedAdds = totalManualMatchedAdds = totalChangedNumberAdds = totalRewordedAdds = totalSpecialistAdds = totalInOrderMatchedAdds = 0
    totalWordPhraseAddsNS = totalSimpleListedAddsNS = totalProperNounAddsNS = totalUniqueExactMatchedAddsNS = totalManualMatchedAddsNS = totalChangedNumberAddsNS = totalRewordedAddsNS = totalSpecialistAddsNS = totalInOrderMatchedAddsNS = 0 # Nomina sacra
    totalNumWords = totalNumWordNumbered = 0

    if BibleOrgSysGlobals.maxProcesses > 1 \
    and not BibleOrgSysGlobals.alreadyMultiprocessing \
    and len(booklist_to_process) > 3: # Get our subprocesses ready and waiting for work
        # Process all the books as quickly as possible
        parameters = [(BBB,lv,rv,OET_LV_ESFM_InputFolderPath) for BBB in booklist_to_process] # Can only pass a single parameter to map
        if BibleOrgSysGlobals.verbosityLevel > 1:
            vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"connect_OET_RV: Processing {len(booklist_to_process)} ESFM books using {min(BibleOrgSysGlobals.maxProcesses,len(booklist_to_process))} processes…" )
            vPrint( 'Quiet', DEBUGGING_THIS_MODULE, "  NOTE: Outputs (including error and warning messages) from loading various books may be interspersed." )
        BibleOrgSysGlobals.alreadyMultiprocessing = True
        with multiprocessing.Pool( processes=BibleOrgSysGlobals.maxProcesses ) as pool: # start worker processes
            results = pool.map( _connect_OET_RV_book_MP, parameters ) # have the pool do our loads
            assert len(results) == len(booklist_to_process)
        BibleOrgSysGlobals.alreadyMultiprocessing = False
    else: # Just single threaded
        results = [connect_OET_RV_book(BBB, lv, rv, OET_LV_ESFM_InputFolderPath)
                   for BBB in booklist_to_process]

    # Worker-local state is not shared with the parent, so carry pass counts in
    # the returned results and aggregate both execution modes in book order.
    bookPassCounts = {}
    for BBB, result in zip(booklist_to_process, results):
        bookWordPhraseAdds, bookWordPhraseAddsNS, bookSimpleListedAdds, bookSimpleListedAddsNS, bookProperNounAdds, bookProperNounAddsNS, bookUniqueExactMatchedAdds, \
            bookUniqueExactMatchedAddsNS, bookManualMatchedAdds, bookManualMatchedAddsNS, bookChangedNumberAdds, \
            bookChangedNumberAddsNS, bookSpecialistAdds, bookSpecialistAddsNS, bookInOrderMatchedAdds, \
            bookInOrderMatchedAddsNS, bookNumWords, bookNumWordNumbered, bookNumPasses = result
        bookPassCounts[BBB] = bookNumPasses
        totalWordPhraseAdds += bookWordPhraseAdds
        totalWordPhraseAddsNS += bookWordPhraseAddsNS
        totalSimpleListedAdds += bookSimpleListedAdds
        totalSimpleListedAddsNS += bookSimpleListedAddsNS
        totalProperNounAdds += bookProperNounAdds
        totalProperNounAddsNS += bookProperNounAddsNS
        totalUniqueExactMatchedAdds += bookUniqueExactMatchedAdds
        totalUniqueExactMatchedAddsNS += bookUniqueExactMatchedAddsNS
        totalManualMatchedAdds += bookManualMatchedAdds
        totalManualMatchedAddsNS += bookManualMatchedAddsNS
        totalChangedNumberAdds += bookChangedNumberAdds
        totalChangedNumberAddsNS += bookChangedNumberAddsNS
        totalSpecialistAdds += bookSpecialistAdds
        totalSpecialistAddsNS += bookSpecialistAddsNS
        totalInOrderMatchedAdds += bookInOrderMatchedAdds
        totalInOrderMatchedAddsNS += bookInOrderMatchedAddsNS
        totalNumWords += bookNumWords
        totalNumWordNumbered += bookNumWordNumbered

    if totalWordPhraseAdds or totalSimpleListedAdds or totalProperNounAdds or totalUniqueExactMatchedAdds or totalManualMatchedAdds or totalChangedNumberAdds or totalRewordedAdds or totalSpecialistAdds or totalInOrderMatchedAdds:
        if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 2:
            vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  {testament} Did total of {totalWordPhraseAdds:,} word phrase adds, {totalSimpleListedAdds:,} simple listed adds, {totalProperNounAdds:,} proper noun adds, {totalUniqueExactMatchedAdds:,} unique exact adds, {totalManualMatchedAdds:,} manual adds, {totalChangedNumberAdds:,} changed number adds, {totalRewordedAdds:,} reworded adds, {totalSpecialistAdds:,} specialist add spans and {totalInOrderMatchedAdds:,} in-order adds." )
    else: vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  {testament} No new word connections made." )
    if totalSimpleListedAddsNS or totalProperNounAddsNS or totalUniqueExactMatchedAddsNS or totalManualMatchedAddsNS or totalChangedNumberAddsNS or totalRewordedAddsNS or totalSpecialistAddsNS or totalInOrderMatchedAddsNS:
        if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 2:
            vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  {testament} Did total of {totalSimpleListedAddsNS:,} simple listed nomina sacra (NS), {totalProperNounAddsNS:,} proper noun NS, {totalUniqueExactMatchedAddsNS:,} unique exact NS, {totalManualMatchedAddsNS:,} manual NS, {totalChangedNumberAddsNS:,} changed number NS, {totalRewordedAddsNS:,} reworded NS, {totalSpecialistAddsNS:,} specialist add span NS and {totalInOrderMatchedAddsNS:,} in-order NS." )
    else: vPrint( 'Info', DEBUGGING_THIS_MODULE, f"  {testament} No new nomina sacra connections made." )
    if any(passes > 1 for passes in bookPassCounts.values()):
        details = ', '.join(f'{BBB}={passes}' for BBB, passes in bookPassCounts.items() if passes > 1)
        vPrint('Normal', DEBUGGING_THIS_MODULE,
               f"  {testament} book passes: {details}; total {sum(bookPassCounts.values()):,} book passes.")
    if not selected:
        reportWordNumberPercentage( testament, totalNumWords, totalNumWordNumbered )
    return totalNumWords, totalNumWordNumbered
# end of connect_OET-RV_words_via_OET-LV.connect_OET_RV


def _connect_OET_RV_book_MP( givenParameters ):
    """
    Multiprocessing version!
    Load the requested book if it's not already loaded (but doesn't save it as that is not safe for multiprocessing)

    Parameter is a 4-tuple containing the parameters.
    """
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag:
        fnPrint( DEBUGGING_THIS_MODULE, f"_connect_OET_RV_book_MP( {givenParameters} )" )
    return connect_OET_RV_book( *givenParameters )
# end of connect_OET-RV_words_via_OET-LV._connect_OET_RV_book_MP

def connect_OET_RV_book( BBB:str, lv, rv, OET_LV_ESFM_InputFolderPath ):
    """
    Connect one book until a complete pass inserts no more source-word numbers.

    The shared insertion function counts actual additions, independently of rule
    statistics or displayed-word coverage (which groups hyphenated components).
    It only fills unnumbered tokens, so additions are monotonic and the loop must
    finish. Preview and output-directory runs use the same in-memory loop.
    Return rule totals, final coverage, and the number of complete book passes
    (including the last pass with no additions).
    """
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag:
        fnPrint( DEBUGGING_THIS_MODULE, f"connect_OET_RV_book( {BBB} )" )
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 2:
        vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Processing connect words for OET {BBB}…" )

    # wordFileName = lv[BBB].ESFMWordTableFilename

    bookWordPhraseAdds = bookSimpleListedAdds = bookProperNounAdds = bookUniqueExactMatchedAdds = bookManualMatchedAdds = bookChangedNumberAdds = bookRewordedAdds = bookSpecialistAdds = bookInOrderMatchedAdds = 0
    bookWordPhraseAddsNS = bookSimpleListedAddsNS = bookProperNounAddsNS = bookUniqueExactMatchedAddsNS = bookManualMatchedAddsNS = bookChangedNumberAddsNS = bookRewordedAddsNS = bookSpecialistAddsNS = bookInOrderMatchedAddsNS = 0 # Nomina sacra

    lvESFMFilename = f'OET-LV_{BBB}.ESFM'
    lvESFMFilepath = OET_LV_ESFM_InputFolderPath.joinpath( lvESFMFilename )
    with open( lvESFMFilepath, 'rt', encoding='UTF-8' ) as esfmFile:
        state.lvESFMText = esfmFile.read() # We keep the original (for later comparison)
        state.lvESFMLines = state.lvESFMText.split( '\n' )
        # Do some basic checking (better to find common editing errors sooner rather than later)
        for lineNumber,line in enumerate( state.lvESFMLines, start=1 ):
            # assert not line.endswith(' '), f"Unexpected space at end in {lvESFMFilename} {lineNumber}: '{line}'" # Should be checked elsewhere -- tends to fail on OET-LV MAT line 99
            if line.endswith(' '):
                logging.warning( f"Unexpected space at end in {lvESFMFilename} {lineNumber}: '{line}'" )
            for characterMarker in BibleOrgSysGlobals.USFMCharacterMarkers:
                assert line.count( f'\\{characterMarker} ') == line.count( f'\\{characterMarker}*'), f"{characterMarker} marker mismatch in {lvESFMFilename} {lineNumber}: '{line}'"
            assert doubledND not in line, f"Double \\nd in {lvESFMFilename} {lineNumber}: '{line}'"
            assert  badAddND not in line, f"\\nd inside \\add start {lvESFMFilename} {lineNumber}: '{line}'"
            assert  badNDAdd not in line, f"\\nd inside \\add end {lvESFMFilename} {lineNumber}: '{line}'"
            assert  ' ¦' not in line, f"Word number attached to space {lvESFMFilename} {lineNumber}: '{line}'"
            if '\\x* ' in line: # this can be ok if the xref directly follows other text
                logger = logging.critical if ' \\x ' in line else logging.warning
                logger( f"Double-check space after xref in {lvESFMFilename} {lineNumber}: '{line}'" )

    rvESFMFilename = f'OET-RV_{BBB}.ESFM'
    rvESFMFilepath = OET_RV_ESFM_FolderPath.joinpath( rvESFMFilename )
    with open( rvESFMFilepath, 'rt', encoding='UTF-8' ) as esfmFile:
        state.rvESFMText = esfmFile.read() # We keep the original (for later comparison)
        state.rvESFMLines = state.rvESFMText.split( '\n' )
        state.rvLineIndex = index_book_lines(state.rvESFMLines)
        state.rvTokenCache = {}
        beforeWords, beforeLinked = countWordsAndWordNumbers(state.rvESFMLines)
        # Plain, < and > additions have no OET-LV counterpart; remove their
        # numbers before matching, including uncertain and nested +add forms.
        numUnlinkedAddSpanRemovals = removeWordNumbersInUnlinkedAddSpans( rvESFMFilename, state.rvESFMLines )
        if numUnlinkedAddSpanRemovals:
            if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 2:
                vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"    Removed a total of {numUnlinkedAddSpanRemovals:,} word number(s) from plain, < or > add spans in {rvESFMFilename}" )
        # Do some basic checking (better to find common editing errors sooner rather than later)
        for lineNumber,line in enumerate( state.rvESFMLines, start=1 ):
            assert not line.startswith(' '), f"Unexpected space at start in {rvESFMFilename} {lineNumber}: '{line}'"
            assert not line.endswith(' '), f"Unexpected space at end in {rvESFMFilename} {lineNumber}: '{line}'"
            assert '  ' not in line, f"Unexpected doubled spaces in {rvESFMFilename} {lineNumber}: '{line}'"
            assert ',,' not in line and '..' not in line.replace( '../', '' ), f"Unexpected doubled punctuation in {rvESFMFilename} {lineNumber}: '{line}'"
            assert '\\x*,' not in line and '\\x*.' not in line, f"Bad xref formatting in {rvESFMFilename} {lineNumber}: '{line}'"
            if line.count(' \\x ') < line.count('\\x '):
                assert '\\x* ' in line or line.endswith('\\x*') or '\\x*—' in line, f"Missing xref space in {rvESFMFilename} {lineNumber}: '{line}'"
            if '“ ‘' not in line:
                assert '“ ' not in line, f"Unexpected space at beginning of speech in {rvESFMFilename} {lineNumber}: '{line}'"
            assert '“‘' not in line and '‘“' not in line, f"Unexpected consecutive opeing speech marks in {rvESFMFilename} {lineNumber}: '{line}'"
            assert '’“' not in line and '“’' not in line, f"Unexpected consecutive closing speech marks in {rvESFMFilename} {lineNumber}: '{line}'"
            if '’ ”' not in line and '’\\wj* ”' not in line:
                assert ' ”' not in line, f"Unexpected space at end of speech in {rvESFMFilename} {lineNumber}: '{line}'"
            assert '≈ ' not in line, f"Unexpected space after ≈ in {rvESFMFilename} {lineNumber}: '{line}'"
            for characterMarker in BibleOrgSysGlobals.USFMCharacterMarkers:
                assert line.count( f'\\{characterMarker} ') == line.count( f'\\{characterMarker}*'), f"{characterMarker} marker mismatch in {rvESFMFilename} {lineNumber}: '{line}'"
                assert  f' \\{characterMarker}* 'not in line, f"doubled spaces around close {characterMarker} marker {rvESFMFilename} {lineNumber}: '{line}'"
            assert doubledND not in line, f"Double \\nd in {rvESFMFilename} {lineNumber}: '{line}'"
            assert  badAddND not in line, f"\\nd inside \\add start {rvESFMFilename} {lineNumber}: '{line}'"
            assert  badNDAdd not in line, f"\\nd inside \\add end {rvESFMFilename} {lineNumber}: '{line}'"
            assert  ' ¦' not in line, f"Word number attached to space {rvESFMFilename} {lineNumber}: '{line}'"
            if '\\x* ' in line: # this can be ok if the xref directly follows other text
                logger = logging.critical if ' \\x ' in line else logging.warning
                logger( f"Double-check space after xref in {rvESFMFilename} {lineNumber}: '{line}'" )

    # Only books that gain links need another pass. Retain their live lines and
    # parsed verse pairs in memory; cleanup and saving each happen just once.
    verseEntries = list(iterAlignmentVerseEntries(BBB, lv, rv))
    state.bookLinkAdditions = 0
    passLinkAdditions = []
    while True:
        beforePass = state.bookLinkAdditions
        for c, v, rvVerseEntryList, lvVerseEntryList in verseEntries:
            (numWordPhraseAdds,numWordPhraseNS), (numSimpleListedAdds,numSimpleListedAddsNS), (numProperNounAdds,numProperNounAddsNS), (numUniqueExactMatchedAdds,numUniqueExactMatchedAddsNS), (numManualMatchedAdds,numManualMatchedAddsNS), (numVerbSetAdds,numVerbSetNS), (numChangedNumberAdds,numChangedNumberNS), (numSpecialistAdds,numSpecialistNS), (numInOrderMatchedAdds,numInOrderMatchedAddsNS) \
                        = connect_OET_RV_Verse( BBB, c, v, rvVerseEntryList, lvVerseEntryList ) # updates state.rvESFMLines
            bookWordPhraseAdds += numWordPhraseAdds
            bookWordPhraseAddsNS += numWordPhraseNS
            bookSimpleListedAdds += numSimpleListedAdds + numVerbSetAdds
            bookSimpleListedAddsNS += numSimpleListedAddsNS + numVerbSetNS
            bookProperNounAdds += numProperNounAdds
            bookProperNounAddsNS += numProperNounAddsNS
            bookUniqueExactMatchedAdds += numUniqueExactMatchedAdds
            bookUniqueExactMatchedAddsNS += numUniqueExactMatchedAddsNS
            bookManualMatchedAdds += numManualMatchedAdds
            bookManualMatchedAddsNS += numManualMatchedAddsNS
            bookChangedNumberAdds += numChangedNumberAdds
            bookChangedNumberAddsNS += numChangedNumberNS
            bookSpecialistAdds += numSpecialistAdds
            bookSpecialistAddsNS += numSpecialistNS
            bookInOrderMatchedAdds += numInOrderMatchedAdds
            bookInOrderMatchedAddsNS += numInOrderMatchedAddsNS
        addedThisPass = state.bookLinkAdditions - beforePass
        passLinkAdditions.append(addedThisPass)
        vPrint( 'Normal' if addedThisPass else 'Info', DEBUGGING_THIS_MODULE,
               f"    {BBB} pass {len(passLinkAdditions)} added {addedThisPass:,} word links."
               + (" Reprocessing…" if addedThisPass else " Finished."))
        if not addedThisPass:
            break

    newESFMtext = '\n'.join( state.rvESFMLines ) \
                        .replace( '\\nd* \\nd ', ' ' ) # Concatenate consecutive nd fields
    if newESFMtext != state.rvESFMText:
        if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
            dPrint( 'Info', DEBUGGING_THIS_MODULE, f"{BBB} ESFM text has changed {len(state.rvESFMText):,} chars -> {len(newESFMtext):,} chars" )
        if BBB=='ACT': newESFMtext = newESFMtext.replace( ' 120¦', ' 12Z¦' ) # Avoid false alarm
        illegalWordLinkRegex1Match = illegalWordLinkRegex1.search( newESFMtext)
        assert not illegalWordLinkRegex1Match, f"illegalWordLinkRegex1 failed before saving {BBB} with '{newESFMtext[illegalWordLinkRegex1Match.start()-5:illegalWordLinkRegex1Match.end()+5]}'" # Don't want double-ups of wordlink numbers
        if BBB=='ACT': newESFMtext = newESFMtext.replace( ' 12Z¦', ' 120¦' ) # Avoided false alarm
        illegalWordLinkRegex2Match = illegalWordLinkRegex2.search( newESFMtext)
        assert not illegalWordLinkRegex2Match, f"illegalWordLinkRegex2 failed before saving {BBB} with '{newESFMtext[illegalWordLinkRegex2Match.start()-5:illegalWordLinkRegex2Match.end()+5]}'" # Don't want double-ups of wordlink numbers
        assert doubledND not in newESFMtext, f"doubled \\nd check failed before saving {BBB} with '{newESFMtext[newESFMtext.index(doubledND)-10:newESFMtext.index(doubledND)+35]}'"
        assert badAddND not in newESFMtext, f"\\nd in \\add start check failed before saving {BBB} with '{newESFMtext[newESFMtext.index(badAddND)-10:newESFMtext.index(badAddND)+35]}'"
        assert badNDAdd not in newESFMtext, f"\\nd in \\add end check failed before saving {BBB} with '{newESFMtext[newESFMtext.index(badNDAdd)-10:newESFMtext.index(badNDAdd)+35]}'"
        # NOTE: '*?' has to have a space before it, because \\add*? might occur at the end of a question
        for wronglyOrderedCombo in ('+?','=?','<?','>?','≡?','&?','@?',' *?','#?','%?','^?','≈?'):
            assert wronglyOrderedCombo not in newESFMtext, f"Wrongly ordered combo check failed with '{wronglyOrderedCombo}' before saving {BBB} with '{newESFMtext[newESFMtext.index(wronglyOrderedCombo)-10:newESFMtext.index(wronglyOrderedCombo)+35]}'"
        options = BibleOrgSysGlobals.commandLineArguments
        destination = options.output_dir / rvESFMFilename if options.output_dir else rvESFMFilepath
        if not options.dry_run:
            destination.write_text(newESFMtext, encoding='utf-8')
        if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 2:
            vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"    Did {bookWordPhraseAdds:,} word phrase adds, {bookSimpleListedAdds:,} simple listed adds, {bookProperNounAdds:,} proper noun adds, {bookUniqueExactMatchedAdds:,} unique exact adds, {bookManualMatchedAdds:,} manual adds, {bookChangedNumberAdds:,} changed number adds, {bookRewordedAdds:,} reworded adds, {bookSpecialistAdds:,} specialist add span adds and {bookInOrderMatchedAdds:,} in-order adds for {BBB}." )
        if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 2:
            vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"    Did {bookWordPhraseAddsNS:,} word phrase NS, {bookSimpleListedAddsNS:,} simple listed NS, {bookProperNounAddsNS:,} proper noun NS, {bookUniqueExactMatchedAddsNS:,} unique exact NS, {bookManualMatchedAddsNS:,} manual NS, {bookChangedNumberAddsNS:,} changed number NS, {bookRewordedAddsNS:,} reworded NS, {bookSpecialistAddsNS:,} specialist add span NS and {bookInOrderMatchedAddsNS:,} in-order NS for {BBB}." )
        if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 2:
            vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"      {'Previewed' if options.dry_run else 'Saved'} OET-RV {BBB} {len(newESFMtext):,} characters ({destination})" )
    else:
        # assert bookSimpleListedAdds == bookProperNounAdds == 0
        if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 3:
            vPrint( 'Info', DEBUGGING_THIS_MODULE, f"    No changes made to OET-RV {BBB}." )

    # Say how much of this book is now connected to the OET-LV.
    #   Selected-book runs report each book; full runs report testament and Bible totals
    #   in connect_OET_RV() and main().
    bookNumWords,bookNumWordNumbered = countWordsAndWordNumbers( state.rvESFMLines )
    options = BibleOrgSysGlobals.commandLineArguments
    if options.output_dir and not options.dry_run and newESFMtext == state.rvESFMText:
        (options.output_dir / rvESFMFilename).write_text(newESFMtext, encoding='utf-8')
    state.bookReports.append(dict(book=BBB, words=bookNumWords, before=beforeLinked,
                                  after=bookNumWordNumbered, added=bookNumWordNumbered-beforeLinked,
                                  removed_plain_add=numUnlinkedAddSpanRemovals, # Includes < and > additions.
                                  mapping_skipped=state.mappingSkipped,
                                  unmapped_lv=state.unmappedLV,
                                  mapped_passages=len(state.alignmentPassages),
                                  passes=len(passLinkAdditions),
                                  links_added=state.bookLinkAdditions,
                                  pass_additions=passLinkAdditions))
    if options.report:
        # Include unchanged verses, so a coverage audit does not depend on which
        # words this particular run happened to add. Use the final live RV text.
        state.bookReports[-1]['verses'] = [
            summariseVerseAlignment(BBB, c, v, lvEntries)
            for c, v, _, lvEntries in verseEntries]
    if options.books:
        reportWordNumberPercentage( f"OET-RV {BBB}", bookNumWords, bookNumWordNumbered )

    return bookWordPhraseAdds, bookWordPhraseAddsNS, bookSimpleListedAdds, bookSimpleListedAddsNS, bookProperNounAdds, bookProperNounAddsNS, bookUniqueExactMatchedAdds, \
            bookUniqueExactMatchedAddsNS, bookManualMatchedAdds, bookManualMatchedAddsNS, bookChangedNumberAdds, \
            bookChangedNumberAddsNS, bookSpecialistAdds, bookSpecialistAddsNS, bookInOrderMatchedAdds, \
            bookInOrderMatchedAddsNS, bookNumWords, bookNumWordNumbered, len(passLinkAdditions)
# end of connect_OET-RV_words_via_OET-LV.connect_OET_RV_book


def iterAlignmentVerseEntries(BBB, lv, rv):
    """Resolve mapped passages once; subsequent passes read the live RV lines.

    c/v now always identify the first *RV* verse in a matching passage. Its
    complete RV and LV reference lists are retained separately for the audit.
    """
    passages, skipped = resolve_alignment_passages(BBB, rv, lv, state.rvESFMLines)
    state.alignmentPassages = {passage.key: passage for passage in passages}
    state.rvAlignmentLines = {passage.key: passage.lines for passage in passages}
    state.mappingSkipped = skipped
    state.unmappedLV = audit_unmapped_lv(BBB, rv, lv, state.lvESFMLines, passages)
    if state.unmappedLV:
        missing = ', '.join(f'{c}:{v}{suffix or ""}' for _,c,v,suffix in
                            (gap['lv_reference'] for gap in state.unmappedLV))
        vPrint('Normal', DEBUGGING_THIS_MODULE,
               f'    WARNING: OET-LV {BBB} {missing} not represented in the RV mappings; '
               'check BOS mapping data / RV verse coverage (see unmapped_lv in --report).')
    for issue in skipped:
        refs = ', '.join(f'{b} {c}:{v}{suffix or ""}' for b,c,v,suffix in issue['rv_references'])
        diagnostics = issue.get('mapping', {}).get('diagnostics', ())
        reason = '; '.join(dict.fromkeys(d['message'] for d in diagnostics)) or issue.get('message', issue['status'])
        logging.warning(f'Skipping OET-RV {refs}: {issue["status"]}: {reason}')
    vPrint('Info', DEBUGGING_THIS_MODULE,
           f'    {BBB}: resolved {len(passages):,} RV passages (eng → org); skipped {len(skipped):,}.')
    for passage in passages:
        c, v = passage.key
        check_OET_RV_Verse(BBB, c, v, (), passage.lv_entries)
        yield c, v, (), passage.lv_entries


wordLinkRegex = re.compile('¦[1-9][0-9]{0,5}')
def check_OET_RV_Verse(BBB:str, c:int, v:int, rvEntryList, lvEntryList) -> None:
    """Require existing links to occur in the complete mapped LV passage.

    A min/max range admitted unrelated intervening IDs and did not work for
    disjoint mappings. Membership also removes the old Psalm/bridge exceptions.
    Excluded additions have already been cleaned from the live RV text.
    """
    allowed = {int(match[1:]) for entry in lvEntryList if entry.getMarker() in ('v~', 'd')
               for match in wordLinkRegex.findall(entry.getCleanText())}
    invalid = {token.number for token in getLiveRVTokens(BBB, c, v)
               if token.number is not None and token.code not in UNLINKED_ADD_CODES
               and token.number not in allowed}
    if invalid:
        raise ValueError(f'OET-RV {BBB} {c}:{v} word numbers {sorted(invalid)} '
                         'do not belong to its mapped OET-LV passage')


GLOSS_COLUMN__NUMBER = 5


def summariseVerseAlignment(BBB, c, v, lvEntries):
    """Return paired verse texts and coverage, excluding the same add spans as totals."""
    rvText = getLiveRVVerseText(BBB, c, v)
    words = getVerseTextWords(rvText)
    return dict(chapter=c, verse=v, **state.alignmentPassages[c, v].metadata(),
                words=len(words), linked=sum('¦' in w for w in words),
                rv=nonTextSpanRegex.sub('', rvText),
                lv=' '.join(e.getCleanText() for e in lvEntries if e.getMarker() in ('v~', 'd')),
                unlinked=[dict(word=t.text, code=t.code) for t in getLiveRVTokens(BBB,c,v)
                          if t.number is None and t.code not in UNLINKED_ADD_CODES])


def normaliseLVVerseText(lvText):
    """Normalise parsed LV gloss text without making pronoun annotations words."""
    # These parenthesised suffixes describe pronoun number/gender, not spelling.
    # Removing just the parentheses turned you(pl) into an unmatchable "youpl".
    lvAdjText = re.sub(r'(?<![A-Za-z])(you|your|yours|yourself|yourselves|himself|herself|itself|themselves)\((?:pl|sg|m|f|ms|fs)\)', r'\1', lvText, flags=re.IGNORECASE)
    lvAdjText = lvAdjText.replace('_',' ').replace('=',' ').replace('÷',' ') \
                .replace('˱','').replace('˲','') \
                .replace('0/','0 ').replace('1/','1 ').replace('2/','2 ').replace('3/','3 ').replace('4/','4 ').replace('5/','5 ').replace('6/','6 ').replace('7/','7 ').replace('8/','8 ').replace('9/','9 ') \
                .replace('.','').replace(',','').replace(':','').replace(';','').replace('?','').replace('!','') \
                .replace( '(', '').replace( ')', '' ) \
                .replace('   ',' ').replace('  ',' ').strip()
    if lvAdjText.startswith( '/' ): lvAdjText = lvAdjText[1:]
    return lvAdjText


def connect_OET_RV_Verse( BBB:str, c:int,v:int, rvEntryList, lvEntryList ) -> Tuple[Tuple[int,int],Tuple[int,int],Tuple[int,int],Tuple[int,int],Tuple[int,int],Tuple[int,int],Tuple[int,int],Tuple[int,int],Tuple[int,int]]:
    """
    Some undocumented documentation of the NT GlossCaps column from state.wordTable:
        ●    U – lexical entry capitalized
        ●    W – proper noun
        ●    G – reference to deity
        ●    P – paragraph boundary
        ●    S – start of sentence
        ●    D – quoted dialog
        ●    V – vocative title
        ●    B – Biblical quotation
        ●    R – other quotation
        ●    T – translated words
        ●    N – nomina sacra (our addition)

        ●    h – partial word capitalized
        ●    n – named but not proper name
        ●    b – incorporated Biblical quotation
        ●    c – continuation of quotation
        ●    e – emphasized words (scare quotes)
    The lowercase letters mark other significant places where the words are not normally capitalized.
    """
    connectRef = f'{BBB}_{c}:{v}'
    # fnPrint( DEBUGGING_THIS_MODULE, f"connect_OET_RV( {BBB} {c}:{v} {len(rvEntryList)}, {len(lvEntryList)} )" )
    # if connectRef == 'PSA_54:1':
    #     print( f"\nconnect_OET_RV( {connectRef} {len(rvEntryList)} {rvEntryList=}, {len(lvEntryList)} {lvEntryList=} )" )
    NT = bos_books_codes_py.is_new_testament_nr( BBB )
    if NT:
        assert state.wordTableHeaderList['NT'].index('VLTGlossWords')+1 == GLOSS_COLUMN__NUMBER, f"{state.wordTableHeaderList['NT'].index('VLTGlossWords')+1=} {GLOSS_COLUMN__NUMBER=} {state.wordTableHeaderList=}" # Check we have the correct column below

    lvText = ''
    for lvEntry in lvEntryList:
        lvMarker,lvRest = lvEntry.getMarker(), lvEntry.getCleanText()
        if lvMarker in ('v~', 'd'):
            lvText = f"{lvText}{' ' if lvText else ''}{lvRest.replace('+','')}"
            # lvTextSimplified = lvText.replace('¦','').replace('0','').replace('1','').replace('2','').replace('3','').replace('4','').replace('5','').replace('6','').replace('7','').replace('8','').replace('9','') \
            #                     .replace('¬','').replace('_',' ').replace('  ',' ') \
            #                     .replace('before','').replace('forget','').replace('forgive','').replace('forty','').replace('therefore','').replace('fore','') \
            #                     .replace('tolerable for','').replace('account for','').replace('prepared for','').replace('waiting for','').replace('ing for','').replace('ous for','') \
            #                     .replace('for all','').replace('for her','').replace('for him','').replace('for me','').replace('for them','').replace('for you','').replace('for us','') \
            #                     .replace('for days','').replace('for months','')
            # if lvTextSimplified.startswith( 'for ' ) or lvTextSimplified.startswith( 'For ' ) or ' for ' in lvTextSimplified or 'For ' in lvTextSimplified:
            #     print( f"FOR: {BBB}_{c}:{v}, '{lvTextSimplified.replace('for','FOR').replace('For','FOR')}'" )
            #     forList.append( f"{BBB}_{c}:{v}" )
    rvText = getLiveRVVerseText(BBB, c, v)
    if not rvText or not lvText: return (0,0), (0,0), (0,0), (0,0), (0,0), (0,0), (0,0), (0,0), (0,0)

    # ⇔ swaps clauses; words WITHIN each clause retain their left-to-right order.
    #   (e.g. Mark 3:10 '⇔and a crowd...' comes before the LV's first clause.)
    reversedOrder = rvText.lstrip().startswith( ORDER_REVERSAL_CHARACTER )
    # The exposed '\add' codes are NOT removed from this text, because splitExposedAddSpan() has
    #   to be able to see which code each exposed span has
    rvWords,rvAddSpans = getRVWordsAndAddSpans( rvText, connectRef )
    lvAdjText = normaliseLVVerseText(lvText)
    if not rvWords or not lvAdjText:
        return ((0,0),) * 9
    lvWords = lvAdjText.split()
    for rvWord in rvWords:
        assert rvWord.count('¦') <= 1 or '-' in rvWord, f"Bad {rvWord=} from {BBB} {c}:{v} {lvText=}"
    # print( f"({len(rvWords)}) {rvWords=}")
    # print( f"({len(lvWords)}) {lvWords=}")

    # Remove DOM's from word list
    #   These are capitalised, but untranslated, so remove them here (because won't ever be in RV)
    initialNumWords = len( lvWords )
    for lvIndex, lvWord in enumerate( reversed( lvWords), start=1 ):
        # print( f"  {lvIndex} {lvWord=}" )
        if lvWord.startswith( 'DOM¦' ):
            lvWords.pop( initialNumWords - lvIndex )
            # print( f"    ({len(lvWords)}) {lvWords=}")
    # print( f"({len(lvWords)}) {lvWords=}")
    assert lvWords

    # if 0: # Mostly works but a couple of exceptions
    #     badIx = None
    #     for ix,lvWord in enumerate( lvWords ):
    #         if lvWord == 'Galilaia': continue # These two bad lines are from 2 Ti NOT Galilaia TODO
    #         if lvWord == 'NOT': badIx = ix
    #         else:
    #             assert lvWord, f"{lvText=} {lvAdjText=}"
    #             assert lvWord.count( '¦' ) == 1, f"{connectRef} {lvWord=}" # Check that we haven't been retagging already tagged RV words
    #     if badIx is not None: lvWords.pop( badIx )

    # Spelling-only function-word fallbacks must respect live RV anchors. Cache
    # LV text positions once per passage; source IDs themselves are not ordered.
    lvNumberPositions = defaultdict(list)
    for position, word in enumerate(lvWords):
        if (number := getLVWordNumber(word)) is not None:
            lvNumberPositions[number].append(position)
    state.functionWordContext = (BBB, c, v), lvNumberPositions

    numWordPhraseAdds,numWordPhraseNS = matchWordPhrases( BBB, c,v, rvWords, lvWords, reversedOrder )
    numSpecialistAdds,numSpecialistNS = matchSpecialistAddSpans( BBB, c,v, rvWords, rvAddSpans, lvWords )
    # Establish context before the verse-wide fallback rules commit a synonym
    # in the wrong clause. This matters especially after deleting all numbers.
    # For example, GEN 2:5 'ground' belongs to the final 'soil', not the earlier
    # 'earth'. A unique spelling alone cannot choose between those alternatives.
    # A marked clause reversal needs lexical/name anchors to infer its rotation;
    # do not bootstrap it with an alignment in the original LV clause order.
    earlyOrderAdds,earlyOrderNS = (0,0) if reversedOrder else matchWordsInOrder(
        BBB, c,v, rvText, rvWords, lvWords, reversedOrder, lvText)
    numSimpleListedAdds,numSimpleListedNS = matchOurListedSimpleWords( BBB, c,v, rvWords, lvWords )
    numVerbSetAdds,numVerbSetNS = matchVerbSets( BBB, c,v, rvWords, lvWords )

    # Now get the uppercase words
    rvUpperWords = [rvWord for rvWord in rvWords if rvWord[0].isupper() and rvWord.split('¦',1)[0].replace("'",'').isalpha()]
    lvUpperWords = [lvWord for lvWord in lvWords if (lvWord[0].isupper() or (lvWord[0] in 'ʼˊ' and lvWord[1].isupper()))]
    # print( f"{rvText=} {lvText=}" )

    if lvUpperWords and lvText[0].isupper(): # Try to determine why the first word was capitalised
        if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
            dPrint( 'Info', DEBUGGING_THIS_MODULE, f"{lvUpperWords=} from {lvText=}")
        firstLVUpperWord, firstLVUpperNumber = lvUpperWords[0].split( '¦' )
        rowForFirstLVUpperWord = state.wordTable['NT' if NT else 'OT'][int(firstLVUpperNumber)]
        if NT:
            firstLVUpperWordCapsFlags = rowForFirstLVUpperWord[state.wordTableHeaderList['NT'].index('GlossCaps')]
            # print( f"{firstLVUpperWordCapsFlags=} from {rowForFirstLVUpperWord=}" )
            if 'G' not in firstLVUpperWordCapsFlags and 'W' not in firstLVUpperWordCapsFlags and firstLVUpperWord!='I':
                # print( f"Removing first LV Uppercase word: '{lvUpperWords[0]}' with '{firstLVUpperWordCapsFlags}'")
                lvUpperWords.pop(0) # Throw away the first word because it might just be capitalised for being at the beginning of the sentence.
        else: # OT
            firstLVUpperWordCapsFlags = rowForFirstLVUpperWord[state.wordTableHeaderList['OT'].index('GlossCapitalisation')]
            # print( f"{firstLVUpperWordCapsFlags=} from {rowForFirstLVUpperWord=}" )
            if 'S' in firstLVUpperWordCapsFlags and firstLVUpperWord!='I':
                # print( f"Removing first LV Uppercase word: '{lvUpperWords[0]}' with '{firstLVUpperWordCapsFlags}'")
                lvUpperWords.pop(0) # Throw away the first word because it might just be capitalised for being at the beginning of the sentence.
    # if rvText[0].isupper():
    #   rvUpperWords.pop(0) # Throw away the first word because it might just be capitalised for being at the beginning of the sentence.
    # print( f"({len(rvUpperWords)}) {rvUpperWords=}")
    # print( f"({len(lvUpperWords)}) {lvUpperWords=}")
    numIdenticalProperNounAdds,numIdenticalProperNounNS = matchIdenticalProperNouns( BBB, c,v, rvUpperWords, lvUpperWords ) if rvUpperWords and lvUpperWords else (0,0)
    numAdjustedProperNounAdds,numAdjustedProperNounNS = matchAdjustedProperNouns( BBB, c,v, rvUpperWords, lvUpperWords ) if rvUpperWords and lvUpperWords else (0,0)

    numUniqueExactMatchedWords,numUniqueExactMatchedWordsNS = matchUniqueExactWords( BBB, c,v, rvWords, lvWords )

    numHandmatches,numHandmatchesNS = matchWordsManually( BBB, c,v, rvWords, lvWords )

    numChangedNumberAdds,numChangedNumberNS = matchWordsWithChangedNumbers( BBB, c,v, rvWords, rvAddSpans, lvWords )

    # Refine the alignment after lexical/name rules have supplied more anchors.
    numInOrderMatches,numInOrderMatchesNS = matchWordsInOrder( BBB, c,v, rvText, rvWords, lvWords, reversedOrder, lvText )
    numInOrderMatches += earlyOrderAdds
    numInOrderMatchesNS += earlyOrderNS

    return (numWordPhraseAdds,numWordPhraseNS), \
           (numSimpleListedAdds,numSimpleListedNS), \
           (numIdenticalProperNounAdds+numAdjustedProperNounAdds,numIdenticalProperNounNS+numAdjustedProperNounNS), \
           (numUniqueExactMatchedWords,numUniqueExactMatchedWordsNS), \
           (numHandmatches,numHandmatchesNS), \
           (numVerbSetAdds,numVerbSetNS), \
           (numChangedNumberAdds,numChangedNumberNS), \
           (numSpecialistAdds,numSpecialistNS), \
           (numInOrderMatches,numInOrderMatchesNS)
# end of connect_OET-RV_words_via_OET-LV.connect_OET_RV_Verse


CNTR_ROLE_NAME_DICT = {'N':'noun', 'S':'substantive adjective', 'A':'adjective', 'E':'determiner/case-marker', 'R':'pronoun',
                  'V':'verb', 'I':'interjection', 'P':'preposition', 'D':'adverb', 'C':'conjunction', 'T':'particle'}
CNTR_MOOD_NAME_DICT = {'I':'indicative', 'M':'imperative', 'S':'subjunctive',
            'O':'optative', 'N':'infinitive', 'P':'participle', 'e':'e'}
CNTR_TENSE_NAME_DICT = {'P':'present', 'I':'imperfect', 'F':'future', 'A':'aorist', 'E':'perfect', 'L':'pluperfect', 'U':'U', 'e':'e'}
CNTR_VOICE_NAME_DICT = {'A':'active', 'M':'middle', 'P':'passive', 'p':'p', 'm':'m', 'a':'a'}
CNTR_PERSON_NAME_DICT = {'1':'1st', '2':'2nd', '3':'3rd', 'g':'g'}
CNTR_CASE_NAME_DICT = {'N':'nominative', 'G':'genitive', 'D':'dative', 'A':'accusative', 'V':'vocative', 'g':'g', 'n':'n', 'a':'a', 'd':'d', 'v':'v', 'U':'U'}
CNTR_GENDER_NAME_DICT = {'M':'masculine', 'F':'feminine', 'N':'neuter', 'm':'m', 'f':'f', 'n':'n'}
CNTR_NUMBER_NAME_DICT = {'S':'singular', 'P':'plural', 's':'s', 'p':'p'}
def matchIdenticalProperNouns( BBB:str, c:int,v:int, rvCapitalisedWordList:List[str], lvCapitalisedWordList:List[str] ) -> Tuple[int,int]:
    """
    Given a list of capitalised words from OET-RV and OET-LV,
        see if we can match any identical proper nouns

    TODO: This function can add new numbers on repeated calls,
        e.g., Acts 11:30 Barnabas and Saul are done one each call
        but could both be added at the same time?
        Jn 3:22, 4:3, 12:36,39, 21:10 Act 11:30,13:31,15:25,40,16:31,18:8
    """
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag:
        fnPrint( DEBUGGING_THIS_MODULE, f"matchIdenticalProperNouns( {BBB} {c}:{v} {rvCapitalisedWordList}, {lvCapitalisedWordList} )" )
    assert rvCapitalisedWordList and lvCapitalisedWordList

    NT = bos_books_codes_py.is_new_testament_nr( BBB )

    # But we don't want any rvWords that are already tagged
    numAdded = numNS = 0
    numRemovedRV = 0 # Extra work because we're deleting from same list that we're iterating through (a copy of)
    for rvN,rvCapitalisedWord in enumerate( rvCapitalisedWordList[:] ):
        # print( f"{BBB} {c}:{v} {rvN} {rvCapitalisedWord=} from {rvCapitalisedWordList}")
        if '¦' in rvCapitalisedWord:
            _rvCapitalisedWord, rvWordNumber = rvCapitalisedWord.split('¦')
            if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  matchIdenticalProperNouns( {BBB} {c}:{v} ) removing already tagged '{rvCapitalisedWord}' from RV list…")
            rvCapitalisedWordList.pop( rvN - numRemovedRV )
            numRemovedRV += 1
            numRemovedLV = 0 # Extra work because we're deleting from same list that we're iterating through (a copy of)
            for lvN,lvCapitalisedWord in enumerate( lvCapitalisedWordList[:] ):
                if lvCapitalisedWord.endswith( f'¦{rvWordNumber}' ):
                    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
                        dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  matchIdenticalProperNouns( {BBB} {c}:{v} ) removing already tagged '{lvCapitalisedWord}' from LV list…")
                    lvCapitalisedWordList.pop( lvN - numRemovedLV )
                    numRemovedLV += 1
    if not rvCapitalisedWordList or not lvCapitalisedWordList:
        return numAdded,numNS # nothing left to do here

    if len(rvCapitalisedWordList)==1 and len(lvCapitalisedWordList)==1:
        # A sole capitalised RV word is not necessarily the sole LV name. The
        # adjusted-name pass below handles known transliterations explicitly.
        if simplifyRVLVWord(rvCapitalisedWordList[0]) != simplifyRVLVWord(lvCapitalisedWordList[0].split('¦',1)[0]):
            return 0, 0
        assert rvCapitalisedWordList[0].replace("'",'').isalpha(), f"{rvCapitalisedWordList=}" # It might contain an apostrophe
        # print( f"{rvCapitalisedWordList=} {lvCapitalisedWordList=}" )
        assert '¦' in lvCapitalisedWordList[0], f"{lvCapitalisedWordList[0]=} from {lvCapitalisedWordList=}"
        capitalisedNoun,wordNumber,wordRow = getLVWordRow( lvCapitalisedWordList[0], 'NT' if NT else 'OT' )
        if NT:
            wordRole = wordRow[state.wordTableHeaderList['NT'].index('Role')]
            if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  '{capitalisedNoun}' {wordRole}" )
            if wordRole == 'N': # let's assume it's a proper noun
                # print( f"matchIdenticalProperNouns {BBB} {c}:{v} adding number to {rvCapitalisedWordList[0]}")
                result = addNumberToRVWord( BBB, c,v, rvCapitalisedWordList[0], wordNumber )
                if result:
                    numAdded += 1
                    if 'N' in wordRow[state.wordTableHeaderList['NT'].index('GlossCaps')]:
                        numNS += 1
        else: # OT
            glossCaps = wordRow[state.wordTableHeaderList['OT'].index('GlossCapitalisation')]
            if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  {capitalisedNoun=} {glossCaps=}" )
            if glossCaps != 'S': # start of sentence
                result = addNumberToRVWord( BBB, c,v, rvCapitalisedWordList[0], wordNumber )
                if result:
                    numAdded += 1
    else:
        # Try to connect identical spellings between the two lists
        # If the lists have the same length and structure, try to match in order
        if len(rvCapitalisedWordList) == len(lvCapitalisedWordList):
            # Try order-based matching first
            for i, rvCapitalisedWord in enumerate(rvCapitalisedWordList[:]):
                if i >= len(lvCapitalisedWordList): break
                lvCapitalisedWord = lvCapitalisedWordList[i]
                if '¦' not in lvCapitalisedWord: continue
                lvNoun = lvCapitalisedWord.split( '¦' )[0]
                if simplifyRVLVWord( lvNoun ) == simplifyRVLVWord( rvCapitalisedWord ):
                    capitalisedNoun,wordNumber,wordRow = getLVWordRow( lvCapitalisedWord, 'NT' if NT else 'OT' )
                    proceed = False
                    if NT:
                        if wordRow[state.wordTableHeaderList['NT'].index('Role')] == 'N': proceed = True
                    else:
                        if wordRow[state.wordTableHeaderList['OT'].index('GlossCapitalisation')] != 'S': proceed = True
                    if proceed:
                        result = addNumberToRVWord( BBB, c,v, rvCapitalisedWord, wordNumber )
                        if result:
                            numAdded += 1
                            if NT and 'N' in wordRow[state.wordTableHeaderList['NT'].index('GlossCaps')]:
                                numNS += 1
                            rvCapitalisedWordList.remove( rvCapitalisedWord )
                            lvCapitalisedWordList.remove( lvCapitalisedWord )
            # If still have items, fall back to cross-matching
            for rvCapitalisedWord in rvCapitalisedWordList[:]:
                for lvCapitalisedWord in lvCapitalisedWordList[:]:
                    assert '¦' in lvCapitalisedWord, f"{lvCapitalisedWordList=}"
                    lvNoun = lvCapitalisedWord.split( '¦' )[0]
                    if simplifyRVLVWord( lvNoun ) == simplifyRVLVWord( rvCapitalisedWord ):
                        capitalisedNoun,wordNumber,wordRow = getLVWordRow( lvCapitalisedWord, 'NT' if NT else 'OT' )
                        proceed = False
                        if NT:
                            if wordRow[state.wordTableHeaderList['NT'].index('Role')] == 'N': proceed = True
                        else:
                            if wordRow[state.wordTableHeaderList['OT'].index('GlossCapitalisation')] != 'S': proceed = True
                        if proceed:
                            result = addNumberToRVWord( BBB, c,v, rvCapitalisedWord, wordNumber )
                            if result:
                                numAdded += 1
                                if NT and 'N' in wordRow[state.wordTableHeaderList['NT'].index('GlossCaps')]:
                                    numNS += 1
                                rvCapitalisedWordList.remove( rvCapitalisedWord )
                                lvCapitalisedWordList.remove( lvCapitalisedWord )
                        break
        else:
            # Try to connect identical spellings between the two lists one by one (regardless of order)
            for rvCapitalisedWord in rvCapitalisedWordList[:]:
                for lvCapitalisedWord in lvCapitalisedWordList[:]:
                    assert '¦' in lvCapitalisedWord, f"{lvCapitalisedWordList=}"
                    lvNoun = lvCapitalisedWord.split( '¦' )[0]
                    if simplifyRVLVWord( lvNoun ) == simplifyRVLVWord( rvCapitalisedWord ):
                        capitalisedNoun,wordNumber,wordRow = getLVWordRow( lvCapitalisedWord, 'NT' if NT else 'OT' )
                        proceed = False
                        if NT:
                            if wordRow[state.wordTableHeaderList['NT'].index('Role')] == 'N': proceed = True
                        else:
                            if wordRow[state.wordTableHeaderList['OT'].index('GlossCapitalisation')] != 'S': proceed = True
                        if proceed:
                            result = addNumberToRVWord( BBB, c,v, rvCapitalisedWord, wordNumber )
                            if result:
                                numAdded += 1
                                if NT and 'N' in wordRow[state.wordTableHeaderList['NT'].index('GlossCaps')]:
                                    numNS += 1
                                rvCapitalisedWordList.remove( rvCapitalisedWord )
                                lvCapitalisedWordList.remove( lvCapitalisedWord )
                        break
    return numAdded,numNS
# end of connect_OET-RV_words_via_OET-LV.matchIdenticalProperNouns


def matchAdjustedProperNouns( BBB:str, c:int,v:int, rvCapitalisedWordList:List[str], lvCapitalisedWordList:List[str] ) -> Tuple[int,int]:
    """
    Given a list of capitalised words from OET-RV and OET-LV,
        see if we can match any proper nouns using the ScriptedBibleEditor name tables
    """
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag:
        fnPrint( DEBUGGING_THIS_MODULE, f"matchAdjustedProperNouns( {BBB} {c}:{v} {rvCapitalisedWordList}, {lvCapitalisedWordList} )" )
    assert rvCapitalisedWordList and lvCapitalisedWordList

    NT = bos_books_codes_py.is_new_testament_nr( BBB )

    # But we don't want any rvWords that are already tagged
    numAdded = numNS = 0
    numRemovedRV = 0 # Extra work because we're deleting from same list that we're iterating through (a copy of)
    for rvN,rvCapitalisedWord in enumerate( rvCapitalisedWordList[:] ):
        # print( f"{BBB} {c}:{v} {rvN} {rvCapitalisedWord=} from {rvCapitalisedWordList}")
        if '¦' in rvCapitalisedWord:
            _rvCapitalisedWord, rvWordNumber = rvCapitalisedWord.split('¦')
            if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  matchAdjustedProperNouns( {BBB} {c}:{v} ) removing already tagged '{rvCapitalisedWord}' from RV list…")
            rvCapitalisedWordList.pop( rvN - numRemovedRV )
            numRemovedRV += 1
            numRemovedLV = 0 # Extra work because we're deleting from same list that we're iterating through (a copy of)
            for lvN,lvCapitalisedWord in enumerate( lvCapitalisedWordList[:] ):
                if lvCapitalisedWord.endswith( f'¦{rvWordNumber}' ):
                    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
                        dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  matchAdjustedProperNouns( {BBB} {c}:{v} ) removing already tagged '{lvCapitalisedWord}' from LV list…")
                    lvCapitalisedWordList.pop( lvN - numRemovedLV )
                    numRemovedLV += 1
    if not rvCapitalisedWordList or not lvCapitalisedWordList:
        return numAdded,numNS # nothing left to do here

    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 4:
        dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"\n{BBB} {c}:{v} {rvCapitalisedWordList=} {lvCapitalisedWordList=}" )
    for lvCapitalisedWord in lvCapitalisedWordList:
        if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 4:
            dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"{lvCapitalisedWord=} from {lvCapitalisedWordList=}" )
        if '¦' not in lvCapitalisedWord:
            # TODO: Determine how/why this happened in DEU Beeroth
            logging.critical( f"Why didn't this word get a word number? {lvCapitalisedWord=} from {BBB} {c}:{v} {lvCapitalisedWordList=}" )
            continue
        assert lvCapitalisedWord.count( '¦' ) == 1, f"{BBB} {c}:{v} {lvCapitalisedWord=} from {lvCapitalisedWordList=}"
        capitalisedNoun,wordNumber,wordRow = getLVWordRow( lvCapitalisedWord, 'NT' if NT else 'OT' )

        for rvCapitalisedWord in rvCapitalisedWordList:
            if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 4:
                dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"{rvCapitalisedWord=} from {rvCapitalisedWordList=}" )
            assert rvCapitalisedWord.replace("'",'').isalpha(), f"{rvCapitalisedWordList=}" # It might contain an apostrophe
            if NT:
                wordRole = wordRow[state.wordTableHeaderList['NT'].index('Role')]
                if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 4:
                    dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"  matchAdjustedProperNouns NT '{capitalisedNoun}' {wordRole}" )
                if wordRole == 'N': # let's assume it's a proper noun
                    if baseNameInCandidates( capitalisedNoun, rvCapitalisedWord, 'NT' ) or baseNameInCandidates( capitalisedNoun, rvCapitalisedWord, 'NT_OT' ):
                        result = addNumberToRVWord( BBB, c,v, rvCapitalisedWord, wordNumber )
                        if result:
                            numAdded += 1
                            if 'N' in wordRow[state.wordTableHeaderList['NT'].index('GlossCaps')]:
                                numNS += 1
            else: # OT
                glossCaps = wordRow[state.wordTableHeaderList['OT'].index('GlossCapitalisation')]
                if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 4:
                    dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"  matchAdjustedProperNouns OT {capitalisedNoun=} {glossCaps=}" )
                if glossCaps != 'S': # start of sentence
                    if baseNameInCandidates( capitalisedNoun, rvCapitalisedWord, 'OT' ):
                        result = addNumberToRVWord( BBB, c,v, rvCapitalisedWord, wordNumber )
                        if result:
                            numAdded += 1
    return numAdded,numNS
# end of connect_OET-RV_words_via_OET-LV.matchAdjustedProperNouns


def baseNameInCandidates( capitalisedNoun:str, rvCapitalisedWord:str, nameTableKey:str ) -> bool:
    """Return True if the LV proper noun and the RV word are names recorded as
        alternatives in the command-table name lists.
    We look both names up through their normalised forms (see normalizeNameKey()),
        because the OET-LV spelling often differs from the OET-LV command-table key
        (e.g. the LV 'Dawid/(Dāvid)' against the command-table 'Dawid/(Dāwid)').
    """
    rvBase = rvCapitalisedWord
    if rvCapitalisedWord.endswith( "'s" ): rvBase = rvCapitalisedWord[:-2] # possessive
    for lvPart in splitNameKey( capitalisedNoun ):
        normalised = normalizeNameKey( lvPart )
        if not normalised: continue
        for something in state.namePartsIndex.get( normalised, () ):
            if something == rvCapitalisedWord or something == rvBase or f"{something}'s" == rvCapitalisedWord:
                if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
                    dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  Name match: LV '{lvPart}' ≈ RV '{rvCapitalisedWord}' (via '{something}' of {normalised})" )
                return True
    # Also let the unchanged (exact) spelling match, as before
    for something in state.nameTables[nameTableKey].get( capitalisedNoun, () ):
        if something == rvCapitalisedWord or something == rvBase or f"{something}'s" == rvCapitalisedWord:
            return True
    return False
# end of connect_OET-RV_words_via_OET-LV.baseNameInCandidates


@lru_cache(maxsize=1)
def getLexicalIndexes():
    """Build form -> lexical-group indexes once, instead of scanning all tables per verse."""
    nounWords = set(SIMPLE_NOUNS_FLAT) | set(verbalNouns)
    simple = defaultdict(set)
    for word in SIMPLE_WORDS:
        forms = {word} | (numberVariants(word) if word in nounWords else set())
        for form in forms:
            simple[form.lower()].add(word)
    for plural, singular in SIMPLE_NOUN_PAIRS:
        # Keep the actual curated pair (e.g. hoof/hooves), not just suffix guesses.
        simple[plural.lower()].add(singular)
        simple[singular.lower()].add(singular)
    verbs = defaultdict(set)
    for index, forms in enumerate(SIMPLE_VERB_SETS):
        for form in forms:
            verbs[form.lower()].add(index)
    return simple, verbs


def matchIndexedWords(BBB, c, v, rvWords, lvWords, formIndex):
    """Match a lexical group only if each verse contains one occurrence of it."""
    rvGroups, lvGroups = defaultdict(set), defaultdict(set)
    for i, word in enumerate(rvWords):
        # Already linked inflections still count as occurrences. Ignoring them
        # made a later pass reuse the sole LV verb for a second RV occurrence.
        for group in formIndex.get(word.split('¦', 1)[0].lower(), ()):
            rvGroups[group].add(i)
    for i, word in enumerate(lvWords):
        if getLVWordNumber(word) is not None:
            for alternative in word.split('¦', 1)[0].split('/'):
                for group in formIndex.get(alternative.lower(), ()):
                    if group in rvGroups:
                        lvGroups[group].add(i)
    added = ns = 0
    NT = bos_books_codes_py.is_new_testament_nr(BBB)
    for group in sorted(rvGroups, key=str):
        if len(rvGroups[group]) != 1 or len(lvGroups[group]) != 1:
            continue
        ri, li = next(iter(rvGroups[group])), next(iter(lvGroups[group]))
        if '¦' in rvWords[ri]:
            continue # Count linked occurrences for ambiguity, but never rewrite them.
        number = getLVWordNumber(lvWords[li])
        if addNumberToRVWord(BBB, c, v, rvWords[ri], number):
            added += 1
            if NT and 'N' in state.wordTable['NT'][number][state.wordTableHeaderList['NT'].index('GlossCaps')]: ns += 1
    return added, ns


def matchOurListedSimpleWords(BBB, c, v, rvWordList, lvWordList):
    """Use the curated simple-word and noun-number tables."""
    return matchIndexedWords(BBB, c, v, rvWordList, lvWordList, getLexicalIndexes()[0])


def matchVerbSets(BBB, c, v, rvWordList, lvWordList):
    """Use the curated verb forms, including irregular inflections."""
    return matchIndexedWords(BBB, c, v, rvWordList, lvWordList, getLexicalIndexes()[1])


def matchUniqueExactWords(BBB, c, v, rvWordList, lvWordList):
    """Recover a unique full spelling when clause order hides it from alignment.

    The old five-letter-prefix fallback also supplied useful *exact* matches
    outside the small simple-word table. Retain those, with the original
    minimum length, but require the entire spelling (ignoring case). Count
    every occurrence, including already numbered ones and LV alternatives.
    Related forms belong in positional alignment, not this verse-wide fallback.
    The index makes this linear in the verse lengths instead of repeated scans.
    """
    words = {word.split('¦', 1)[0].lower() for word in rvWordList}
    exactIndex = {word: {word} for word in words if len(word) >= 5}
    return matchIndexedWords(BBB, c, v, rvWordList, lvWordList, exactIndex)


# The English words 'I' and 'a' can align when context resolves their occurrence.
# Other one-letter fragments remain excluded.
MIN_EXACT_MATCH_WORD_LENGTH = 2


# The U+21D4 double arrow that the translator puts at the start of an OET-RV verse
#   whose clauses were translated in the opposite order to the OET-LV verse.
ORDER_REVERSAL_CHARACTER = '\u21d4'


@lru_cache(maxsize=65536)
def simplifyRVLVWord( word:str ) -> str:
    """
    Reduce an OET-RV or OET-LV word to a plain lowercase form so we can compare the two.

    We throw away edge punctuation, transliteration accents, hyphens, macrons, and the possessive 's,
        because 'Preparation' and 'preparation' are the same word to us, but
        'mother-in-law' and 'mother' are not (and 'money-changers' and 'moneychangers' are).
    """
    word = re.sub(r'\[([a-z]+)\]', r'\1', word) # LV optional suffixes: son[s], branch[es].
    word = unicodedata.normalize( 'NFD', word )
    word = ''.join( ch for ch in word if unicodedata.category( ch ) not in ('Mn', 'Lm') ) # Strip combining marks and modifier letters
    word = re.sub( r"[ʼˊʹʺʸˈ]", '', word ) # Transliteration accents
    word = re.sub( r"/.*$", '', word ) # Strip parenthetical alternatives like /(Miryām)
    word = re.sub( r"[’']s$", '', word ) # Possessives
    word = re.sub( r"[-‐‑–]", '', word ) # Hyphens, anywhere in the word
    return word.lower().strip( '.,;:!?"“”‘’()' )
# end of simplifyRVLVWord


@lru_cache(maxsize=1)
def getRelatedWordIndex():
    """Expand reviewed families through curated inflections, never through synonyms."""
    nouns, verbs = getLexicalIndexes()
    nounForms, verbForms = defaultdict(set), defaultdict(set)
    for word, groups in nouns.items():
        for group in groups: nounForms[group].add(word)
    for word, groups in verbs.items():
        for group in groups: verbForms[group].add(word)
    result = defaultdict(set)
    for index, family in enumerate(RELATED_WORD_GROUPS):
        forms = set(family)
        for word in family:
            for group in nouns.get(word, ()): forms.update(nounForms[group])
            for group in verbs.get(word, ()): forms.update(verbForms[group])
        for form in forms: result[simplifyRVLVWord(form)].add(index)
    return result


@lru_cache(maxsize=131072)
def scoreRVLVWords(rvWord: str, lvWord: str) -> Optional[Tuple[str, int]]:
    """Score lexical evidence; shared initial letters alone supply none.

    Inflections come from the curated noun/verb sets. Related forms and synonyms
    have lower weights than exact words and cannot justify phrase movements.
    Candidates still need an unambiguous anchored alignment. In particular,
    'against' is not an inflection of 'again', and 'brides' is not 'bridegroom'.
    """
    r, l = simplifyRVLVWord(rvWord), simplifyRVLVWord(lvWord)
    if r == l and (len(r) >= MIN_EXACT_MATCH_WORD_LENGTH or r in ('a', 'i')):
        return 'same word', 100
    verbs = getLexicalIndexes()[1]
    if verbs.get(r, set()) & verbs.get(l, set()): return 'curated verb forms', 95
    nouns = getLexicalIndexes()[0]
    if nouns.get(r, set()) & nouns.get(l, set()): return 'curated noun forms', 95
    if l in EQUIVALENT_LV_RV_WORDS.get(r, set()): return 'another word for the same thing', 60
    related = getRelatedWordIndex()
    if related.get(r, set()) & related.get(l, set()): return 'reviewed related forms', 50
    return None


@lru_cache(maxsize=65536)
def scoreAlignedWords(rvWord, lvWord):
    """Add one-way curated alternatives to positional matching, at lower weight.

    Ignore sentence capitalisation while preserving the RV -> LV direction. These candidates
    compete with all other words in the gap; they are not global synonyms and
    cannot justify phrase movement, which requires a score of at least 90.
    """
    lexical = scoreRVLVWords(rvWord, lvWord)
    if lexical and lexical[1] >= 55:
        return lexical
    if lvWord.casefold() in DIRECTIONAL_WORD_INDEX.get(rvWord.casefold(), ()):
        return 'directional word mapping', 55
    if CONTRACTION_SUBJECTS.get(rvWord.casefold().replace('’', "'")) == lvWord.casefold():
        return 'contraction subject', 55
    return lexical


def getUnnumberedRVWords( BBB:str, c:int, v:int ) -> set:
    """Legacy lexical matchers use a set; positional matchers retain occurrences."""
    return {simplifyRVLVWord(t.text) for t in getLiveRVTokens(BBB, c, v)
            if t.linkable and t.number is None}


def getLVWordNumber( lvWordStr:str ) -> Optional[int]:
    """
    Pull the OET-LV word number out of a word like 'wineskins¦23221'.

    We only take the leading run of digits, because the OET-LV sometimes has a gloss helper
        marker stuck to the number (e.g. 'will¦23935˒'), which would otherwise stop int().
    """
    m = re.match( r'^.*?¦(\d+)', lvWordStr )
    return int(m.group(1)) if m else None
# end of getLVWordNumber


def matchWordPhrases( BBB:str, c:int,v:int, rvWordList:List[str], lvWordList:List[str], reversedOrder:bool ) -> Tuple[int,int]:
    """
    Connect the OET-RV words that are MORE THAN ONE English word but stand for just ONE OET-LV
        word, using the pairs that the translator has listed in OET-RV_wordPhrases_table.tsv, e.g.
            the OET-RV 'you all' against the OET-LV 'you_all', the one plural 'you' word
            the OET-RV 'young donkey' against the OET-LV 'colt'
    Every word of the OET-RV phrase gets the one OET-LV word number, because that is the way the
        human translators number such a phrase (see addNumberToAddSpan() for the same convention
        on an '\add' span like Mark 5:12 '\add @the demons\add*' for the LV 'they').

    This has to run FIRST, because the little words that these phrases are made of ('you', 'all',
        'young', 'donkey') are exactly the words that we refuse to match on their own, and because
        the table records a decision that the translator has already made.
    """
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag:
        fnPrint( DEBUGGING_THIS_MODULE, f"matchWordPhrases( {BBB} {c}:{v} {reversedOrder=} {rvWordList}, {lvWordList} )" )
    if not state.rvWordPhrases: return 0,0
    assert rvWordList and lvWordList
    if reversedOrder: vPrint( 'Info', DEBUGGING_THIS_MODULE, f"  {BBB} {c}:{v} is an order-reversed verse" )

    # Where is each of our OET-LV phrases in this verse?  (The OET-LV has already had its
    #   '_' turned into a space, so the one OET-LV word 'you_all¦N_all¦N' is two lvWordList
    #   entries that share the one word number N.  We insist on that, so that we only take a
    #   phrase that really is ONE OET-LV word.)
    lvCandidates = {} # (simplified LV words) -> [ (first word index, lv word number) ]
    for lvWords in state.rvWordPhrases:
        candidates = []
        for ix in range( len( lvWordList ) - len( lvWords ) + 1 ):
            lvNumbers, isMatch = set(), True
            for offset,lvWord in enumerate( lvWords ):
                lvWordStr = lvWordList[ ix + offset ]
                lvNumber = getLVWordNumber( lvWordStr )
                lvWordSimple = simplifyRVLVWord( lvWordStr.split( '¦' )[0] )
                if lvNumber is None or lvWordSimple != lvWord:
                    isMatch = False;
                    if BBB == 'MRK' and c == 1 and v == 42 and lvWords == ('he', 'was', 'cleansed'):
                        break
                lvNumbers.add( lvNumber )
            if isMatch and len( lvNumbers ) == 1:
                lvNum = lvNumbers.pop()
                candidates.append( (ix, lvNum) )
        if candidates:
            lvCandidates[ lvWords ] = candidates
    if not lvCandidates: return 0,0

    # The OET-RV words in the simplified form that we compare in.  Note that a word which already
    #   has a word number is allowed here, because a phrase can be half connected already -- e.g.
    #   Mark 8:2 'How much bread have you all got?' has the number on the 'you' from another matcher
    #   but not yet on the 'all' -- and also because getUnnumberedRVWords()'s 'still free' words
    #   don't see through a closing marker like Mark 14:27 'you¦31031 all\wj*'.  addNumberToRVPhrase()
    #   does the real checking on the live OET-RV lines instead: it only goes ahead if the phrase
    #   occurs exactly once, and it only fills in the words that have no number yet, and only if the
    #   numbers that are already there are the ones that we want.
    rvPlainWords = [ simplifyRVLVWord( rvWordStr.split( '¦' )[0] ) for rvWordStr in rvWordList ]

    # Try the longest phrase first at each word, so that the most specific row wins
    phraseLengths = sorted( { len(rvWords) for rvWords in state.rvWordPhrases }, reverse=True )
    rvIxRange = range( len( rvWordList )-1, -1, -1 ) if reversedOrder else range( len( rvWordList ) )
    usedLvIndexes, numAdded = set(), 0
    for ix in rvIxRange:
        lvWords = None
        for length in phraseLengths:
            if ix + length > len( rvWordList ): continue
            if all( '¦' in rvWord for rvWord in rvWordList[ix:ix+length] ): continue # This phrase is already fully numbered
            rvWords = tuple( rvPlainWords[ix:ix+length] )
            lvWords = next( (key for key,value in state.rvWordPhrases.items() if value == rvWords ), None )
            if lvWords is not None: break # This is the most specific phrase that starts at this word
        if lvWords is None: continue

        # Check if this LV phrase exists in the current verse
        if lvWords not in lvCandidates:
            continue

        lvCandidatesForThisPhrase = lvCandidates[lvWords]
        if reversedOrder: lvCandidatesForThisPhrase = lvCandidatesForThisPhrase[::-1] # The OET-RV meets them in the opposite order
        for candidateIx,lvNumber in lvCandidatesForThisPhrase: # The OET-LV phrases, in the order the OET-RV meets them
            if candidateIx in usedLvIndexes: continue # This OET-LV phrase is already spoken for
            rvPhraseWords = state.rvWordPhrasesSearch[rvWords]
            phraseAdds,phraseNS = addNumberToRVPhrase( BBB, c,v, rvPhraseWords, lvNumber )
            if not phraseAdds:
                if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
                    dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  matchWordPhrases() could not use '{rvWords}' for the LV '{lvWords}¦{lvNumber}' at {BBB} {c}:{v}" )
                break # Don't keep looking, or a second OET-RV phrase would get this same OET-LV number
            if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"matchWordPhrases() is adding {lvNumber} to the {phraseAdds} RV words of '{rvWords}' from LV '{lvWords}' at {BBB} {c}:{v}" )
            usedLvIndexes.add( candidateIx )
            numAdded += phraseAdds
            break
    return numAdded,0 # None of our phrases are nomina sacra
# end of connect_OET-RV_words_via_OET-LV.matchWordPhrases


def matchWordsInOrder( BBB:str, c:int,v:int, rvVerseText:str, rvWordList:List[str], lvWordList:List[str], reversedOrder:bool, lvVerseText:Optional[str]=None ) -> Tuple[int,int]:
    """Align live occurrences between existing links, including semantic add spans.

    Alternatives share one alignment column. Existing links bound local gaps in
    LV text order. Gap matches require agreement across optimal alignments;
    short phrase movements require strong, unambiguous lexical matches across
    a nearby linked block. Original LV punctuation fences the latter operation.
    """
    testament = 'NT' if bos_books_codes_py.is_new_testament_nr(BBB) else 'OT'
    columns = []
    for word in lvWordList:
        number = getLVWordNumber(word)
        if number is None:
            continue
        plain = word.split('¦', 1)[0]
        proper = any(w[:1].isupper() for w in plain.split('/')) and lvWordIsProperNoun(state.wordTable[testament][number], testament)
        columns.append(LVToken(plain, number, proper))
    if lvVerseText is not None:
        columns = with_clause_boundaries(columns, lvVerseText)
    added = ns = 0
    while True:
        proposals = propose_links(getLiveRVTokens(BBB, c, v), columns,
                                  scoreAlignedWords, simplifyRVLVWord, reversedOrder, ALIGNED_PHRASE_INDEX)
        passAdded = 0
        # Work right to left, so recorded character offsets remain valid.
        for token, number, reason in sorted(proposals, key=lambda p: (p[0].line, p[0].start), reverse=True):
            result, resultNS = applyRVTokenLink(BBB, c, v, token, number, reason)
            passAdded += result
            ns += resultNS
        added += passAdded
        if not passAdded:
            break # Every productive pass consumes at least one unnumbered occurrence.
    return added, ns


# The '\add' code that means the translator changed the number, e.g. '\add #straps\add*'.
NUMBER_CHANGE_ADD_CODE = '#'

# The '\add' code that means the translator repeated something they had already said,
#   e.g. '\add ≡the father of\add*'.
REPEAT_ADD_CODE = '≡'

# The English number changes that we can safely undo, i.e. the ones where a '#' word like
#   'men' can only be a pluralised OET-LV 'man', and not the start of some other word.
IRREGULAR_NUMBER_CHANGES = (
    ('brother','brethren'),
    ('child','children'),
    ('foot','feet'),
    ('goose','geese'),
    ('louse','lice'),
    ('man','men'),
    ('mouse','mice'),
    ('ox','oxen'),
    ('person','people'),
    ('tooth','teeth'),
    ('woman','women'),
)
_NUMBER_CHANGE_WORDS = [ _word for _pair in IRREGULAR_NUMBER_CHANGES for _word in _pair ]
assert len( _NUMBER_CHANGE_WORDS ) == len( set( _NUMBER_CHANGE_WORDS ) ), f"Repeated word in {IRREGULAR_NUMBER_CHANGES=}" # Each word may only be in one pair, or numberVariants() would be ambiguous

# The shortest word that we will treat as an English word when we add or remove a plural 's'.
#   Three letters is safe, because the singular and plural of a three letter word can only be
#   each other (e.g. 'day'/'days', 'god'/'gods'), apart from the irregular pairs above.
MIN_NUMBER_CHANGE_WORD_LENGTH = 3

def numberVariants( word:str ) -> set:
    """
    Return the set of plain English words that 'word' would be if its number had been changed,
        e.g. numberVariants('straps') includes 'strap', and numberVariants('strap') includes 'straps'.
    We deliberately only make the changes that we are sure about, because a wrong word number
        is much worse than a missing one.  In particular, we do NOT turn 'ves' into 'fe' or 'le',
        or 'ies' into 'ie', because 'leaves' could be 'leaf' or 'loaf', and 'flies' could be
        'fly' or 'flee', so we would not know which OET-LV word the translator had in mind.
    (We do end up with some forms that aren't English words at all, e.g. 'strapses', but that
        does no harm: matchWordsWithChangedNumbers() only uses a form that is a noun of that
        exact spelling in the OET-LV verse we are working on.)
    """
    word = word.lower()
    variants = set()
    for singular,plural in IRREGULAR_NUMBER_CHANGES:
        if word == singular: variants.add( plural )
        elif word == plural: variants.add( singular )
    if len( word ) >= MIN_NUMBER_CHANGE_WORD_LENGTH:
        if word.endswith( 'ies' ): # e.g. 'families' and 'family'
            variants.add( word[:-3] + 'y' )
        if word.endswith( 'y' ) and word[-2] not in 'aeiou': # e.g. 'family' and 'families'
            variants.add( word[:-1] + 'ies' )
        if word.endswith( 'es' ) and (word[-3] in 'sxzch' or word.endswith( ('ches','shes') )):
            variants.add( word[:-2] ) # e.g. 'classes'/'class', 'watches'/'watch', 'boxes'/'box'
        if word.endswith( ('s','x','z','ch','sh') ) and not word.endswith( 'ss' ):
            variants.add( word + 'es' ) # e.g. 'class'/'classes', 'watch'/'watches'
        if word.endswith( 's' ) and not word.endswith( 'ss' ):
            variants.add( word[:-1] ) # e.g. 'straps'/'strap', 'wars'/'war'
        if not word.endswith( 's' ):
            variants.add( word + 's' ) # e.g. 'strap'/'straps', 'child'/'childs'
    return variants
# end of numberVariants


def lvWordIsNoun( lvWordRow:List[str], testament:str ) -> bool:
    """
    Return True if an OET-LV word is a noun (or a substantive adjective), because a noun is the
        only kind of word whose number the translator can have changed, e.g. RV '#straps' for the
        OET-LV 'strap', so matchWordsWithChangedNumbers() should only connect those.
    The NT word table has a 'Role' column that says 'N' for a noun, but the OT word table
        describes its nouns in the 'Morphology' column instead, e.g. 'Ncfsa' for a common
        feminine singular noun (and 'Td' for the definite article, 'C,' for a conjunction, etc.).
    """
    if testament == 'NT':
        return lvWordRow[state.wordTableHeaderList['NT'].index('Role')].strip() in ('N','S')
    morphology = lvWordRow[state.wordTableHeaderList['OT'].index('Morphology')]
    return any( part.startswith( 'N' ) for part in morphology.split( ',' ) ) # e.g. 'R,Ncfsa' is a preposition with a noun
# end of lvWordIsNoun


def matchWordsWithChangedNumbers( BBB:str, c:int,v:int, rvWordList:List[str], addSpans:List[Tuple[str,int,int]], lvWordList:List[str] ) -> Tuple[int,int]:
    """
    Connect OET-RV words that the translator marked as a changed number with a
        '\add #...' span (e.g. '\add #straps\add*'), which mostly means that we turned a
        singular OET-LV saying into a plural one.
    It works in both directions, e.g. Mark 4:29 '\add #worms\add*' against the LV 'worm', and
        1 Samuel 17:32 '\add #the king\add*' against the LV 'Saul'.

    The word inside such a span is the SAME word as the OET-LV word that it translates, only
    with the opposite number, so we can only connect it when the OET-LV word is exactly
    one of the numberVariants() of the OET-RV word, e.g. RV '#straps' against LV 'strap'.
    To stay safe, the OET-LV word has to be a noun (a noun is the only kind of word whose
    number we can change), we insist on there being exactly one such OET-LV word in the
    verse, and we also give up if any other OET-RV word in the verse is that same OET-LV
    word, because then we can't tell which OET-RV word is the one that goes with it.
    """
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag:
        fnPrint( DEBUGGING_THIS_MODULE, f"matchWordsWithChangedNumbers( {BBB} {c}:{v} {rvWordList} )" )
    assert rvWordList and lvWordList
    if not any( addCode == NUMBER_CHANGE_ADD_CODE for addCode,firstIx,lastIx in addSpans ): return 0,0

    NT = bos_books_codes_py.is_new_testament_nr( BBB )
    usedLVNumbers = set() # Skip any OET-LV word number that is used more than once in the verse (non-consecutively)
    seenLVNumbers = {} # Maps lvNumber to last index where it was seen
    for lvIx, lvWordStr in enumerate( lvWordList ):
        lvNumber = getLVWordNumber( lvWordStr )
        if lvNumber is None: continue
        if lvNumber in seenLVNumbers:
            # Only mark as used if it appears non-consecutively
            # (consecutive duplicates are parts of the same Greek word split by underscores)
            if lvIx != seenLVNumbers[lvNumber] + 1:
                usedLVNumbers.add( lvNumber )
        seenLVNumbers[lvNumber] = lvIx

    stillFree = getUnnumberedRVWords( BBB, c,v )
    numAdded = numNS = 0
    for addCode,firstIx,lastIx in addSpans:
        if addCode != NUMBER_CHANGE_ADD_CODE: continue
        for rvIx in range( firstIx, lastIx+1 ):
            rvWord = rvWordList[rvIx]
            if '¦' in rvWord: continue # Already has a word number
            plainRVWord = simplifyRVLVWord( rvWord )
            if plainRVWord not in stillFree: continue # One of the earlier matchers got there first
            if len( plainRVWord ) < MIN_NUMBER_CHANGE_WORD_LENGTH: continue
            variants = numberVariants( plainRVWord )
            if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  {BBB} {c}:{v} RV '{rvWord}' {variants=}" )

            candidateList = []
            for lvWordStr in lvWordList:
                lvNumber = getLVWordNumber( lvWordStr )
                if lvNumber is None or lvNumber in usedLVNumbers: continue
                lvWord = lvWordStr.split( '¦' )[0]
                if not lvWord.islower(): continue # Leave proper nouns to matchIdenticalProperNouns()
                plainLVWord = simplifyRVLVWord( lvWord )
                if plainLVWord not in variants: continue
                if plainLVWord == plainRVWord: continue # Same word, so the number didn't change after all
                try:
                    _lvWord,lvNumber,lvWordRow = getLVWordRow( lvWordStr, 'NT' if NT else 'OT' )
                except WordNumberError as e:
                    logging.critical( f"matchWordsWithChangedNumbers() {e} from {BBB} {c}:{v} {lvWordStr=}" )
                    continue
                if not lvWordIsNoun( lvWordRow, 'NT' if NT else 'OT' ):
                    continue # Only a noun can have its number changed (so this is not e.g. LV verb 'means')
                candidateList.append( (lvNumber,lvWord,lvWordRow) )
            if len( candidateList ) != 1:
                if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
                    dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  matchWordsWithChangedNumbers() skipping ambiguous pair {BBB} {c}:{v} RV '{rvWord}' with {len(candidateList)} OET-LV candidates" )
                continue
            lvNumber,lvWord,lvWordRow = candidateList[0]
            if any( '¦' not in otherRVWord and otherRVWord != rvWord and simplifyRVLVWord( otherRVWord ) == simplifyRVLVWord( lvWord ) for otherRVWord in rvWordList ):
                if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
                    dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  matchWordsWithChangedNumbers() skipping {BBB} {c}:{v} RV '{rvWord}' because another RV word is '{lvWord}'" )
                continue
            if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"matchWordsWithChangedNumbers() is adding {lvNumber} to RV '{rvWord}' from LV '{lvWord}' at {BBB} {c}:{v}" )
            result = addNumberToRVWord( BBB, c,v, rvWord, lvNumber )
            if result:
                numAdded += 1
                if NT and 'N' in lvWordRow[state.wordTableHeaderList['NT'].index('GlossCaps')]: numNS += 1
            else:
                logging.warning( f"Got addNumberToRVWord( {BBB} {c}:{v} '{rvWord}' {lvNumber} ) result = {result}" )

    return numAdded,numNS
# end of connect_OET-RV_words_via_OET-LV.matchWordsWithChangedNumbers


# The '\add' codes that stand in the place of a single OET-LV word, but where the English
#   word that the translator wrote is NOT a translation of that OET-LV word, so the only way
#   to find the OET-LV word is to look at the OET-LV words on either side of the span:
#     '@' – a pronoun that we changed to a name, e.g. RV '@Yeshua' for the LV 'he',
#     '%' – the person that we changed, e.g. RV '%they' for the LV '=them',
#     '*' – a name that we changed to a pronoun or a description, e.g. RV '*the priest' for the LV 'Amaziah',
#     '&' – an owner that we added, e.g. RV '&His' for the LV 'the' (the OET formats say
#           '&' replaces 'the' with a possessive like 'his').
MIN_ANCHORED_ADD_WORD_LENGTH = 2


def lvWordIsProperNoun( lvWordRow:List[str], testament:str ) -> bool:
    """
    Identify a source proper noun, not merely a capitalised English gloss.

    OT morphology marks proper nouns with Np, including prefixed words such
    as R,Np. Absence of a sentence-capitalisation flag does not establish this:
    the pronoun 'I' and many common nouns/verbs also have an empty flag.
    """
    if testament == 'NT':
        return (lvWordRow[state.wordTableHeaderList['NT'].index('Role')].strip() == 'N'
                and 'W' in lvWordRow[state.wordTableHeaderList['NT'].index('GlossCaps')])
    morphology = lvWordRow[state.wordTableHeaderList['OT'].index('Morphology')]
    return any(part.startswith('Np') for part in morphology.split(','))
# end of connect_OET-RV_words_via_OET-LV.lvWordIsProperNoun


def getRVWordNumber( rvWord:str ) -> Optional[int]:
    """
    Pull the OET-RV word number out of a word like 'wineskins¦23221'.
    """
    m = re.match( r'^.*?¦(\d+)', rvWord )
    return int(m.group(1)) if m else None
# end of connect_OET-RV_words_via_OET-LV.getRVWordNumber


def addNumberToAddSpan( BBB:str, c:int,v:int, rvWordList:List[str], firstIx:int, lastIx:int, lvNumber:int, lvWord:str, lvWordRow:List[str] ) -> Tuple[int,int]:
    """
    Give 'lvNumber' to every word of the exposed '\add' span that covers rvWordList[firstIx:lastIx+1].
    A single OET-LV word can be rendered by several English words (e.g. Mark 5:12
        '\add @the demons\add*' for the LV 'they'), and the human translators number all of
        them with the one OET-LV number, so we do the same.
    """
    NT = bos_books_codes_py.is_new_testament_nr( BBB )
    numAdded = numNS = 0
    for rvIx in range( firstIx, lastIx+1 ):
        result = addNumberToRVWord( BBB, c,v, rvWordList[rvIx], lvNumber )
        if result:
            numAdded += 1
            if NT and 'N' in lvWordRow[state.wordTableHeaderList['NT'].index('GlossCaps')]: numNS += 1
        else:
            logging.warning( f"Got addNumberToRVWord( {BBB} {c}:{v} '{rvWordList[rvIx]}' {lvNumber} ) result = {result}" )
    return numAdded,numNS
# end of connect_OET-RV_words_via_OET-LV.addNumberToAddSpan


def matchRepeatedWords( BBB:str, c:int,v:int, rvWordList:List[str], addSpans:List[Tuple[str,int,int]], lvWordList:List[str] ) -> Tuple[int,int]:
    """
    Connect the OET-RV words of a '\add ≡...' span, which means we repeated something that we
        had already said, to the OET-LV word that the repeat goes with.
    Because it is a repeat, the same words occur twice in the OET-RV verse but only ONCE in the
        OET-LV verse, so we can connect the repeated words to that single OET-LV word (e.g.
        1 Chronicles 4:19, where 'the father of' occurs twice in the OET-RV verse and only once
        in the OET-LV verse).
    We insist that the words really do occur EARLIER in the same OET-RV verse, because '≡' is
        also used to repeat something that we said in a PREVIOUS verse, and that has nothing to
        do with the OET-LV word of this verse (e.g. 1 Chronicles 16:16 and 23:29).
    """
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag:
        fnPrint( DEBUGGING_THIS_MODULE, f"matchRepeatedWords( {BBB} {c}:{v} {rvWordList} )" )
    assert rvWordList and lvWordList
    if not any( addCode == REPEAT_ADD_CODE for addCode,firstIx,lastIx in addSpans ): return 0,0

    NT = bos_books_codes_py.is_new_testament_nr( BBB )
    stillFree = getUnnumberedRVWords( BBB, c,v )
    numAdded = numNS = 0
    for addCode,firstIx,lastIx in addSpans:
        if addCode != REPEAT_ADD_CODE: continue

        if any( '¦' in rvWordList[rvIx] for rvIx in range( firstIx, lastIx+1 ) ):

            continue # Already numbered
        if any( simplifyRVLVWord( rvWordList[rvIx] ) not in stillFree for rvIx in range( firstIx, lastIx+1 ) ):

            continue # One of the earlier matchers got there first
        phrase = [ simplifyRVLVWord( rvWordList[rvIx] ) for rvIx in range( firstIx, lastIx+1 ) ]
        if not any( phrase == [ simplifyRVLVWord( rvWordList[rvIx2] ) for rvIx2 in range( rvIx, rvIx+len(phrase) ) ]
                    for rvIx in range( firstIx ) ):
            if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  matchRepeatedWords() skipping {BBB} {c}:{v} '\\add ≡{' '.join(phrase)}\\add*' because it does not occur earlier in the same verse" )
            continue # It is a repeat of something in a previous verse, so this OET-LV word is not it
        candidateNumbers = set()
        candidateWord, candidateRow = None, None
        for lvIx in range( len( lvWordList ) - len(phrase) + 1 ):
            if [ simplifyRVLVWord( lvWordList[lvIx2].split( '¦' )[0] ) for lvIx2 in range( lvIx, lvIx+len(phrase) ) ] != phrase: continue
            lvNumber = getLVWordNumber( lvWordList[lvIx] )
            if lvNumber is None: continue
            try:
                lvWord,lvNumber,lvWordRow = getLVWordRow( lvWordList[lvIx], 'NT' if NT else 'OT' )
            except WordNumberError as e:
                logging.critical( f"matchRepeatedWords() {e} from {BBB} {c}:{v} {lvWordList[lvIx]=}" )
                continue
            candidateNumbers.add( lvNumber )
            candidateWord, candidateRow = lvWord, lvWordRow
        if len( candidateNumbers ) != 1:
            if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  matchRepeatedWords() skipping {BBB} {c}:{v} '\\add ≡{' '.join(phrase)}\\add*' with {len(candidateNumbers)} OET-LV candidates" )
            continue
        lvNumber = candidateNumbers.pop()
        if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
            dPrint( 'Info', DEBUGGING_THIS_MODULE, f"matchRepeatedWords() is adding {lvNumber} to RV '{' '.join(rvWordList[firstIx:lastIx+1])}' from LV '{candidateWord}' at {BBB} {c}:{v}" )
        spanNumAdded,spanNumNS = addNumberToAddSpan( BBB, c,v, rvWordList, firstIx, lastIx, lvNumber, candidateWord, candidateRow )
        numAdded += spanNumAdded
        numNS += spanNumNS

    return numAdded,numNS
# end of connect_OET-RV_words_via_OET-LV.matchRepeatedWords


# The OET-LV gives a name in the original language AND, where we have one, its English
#   equivalent, e.g. 'Yəhūdāh/Judah' or 'Samouaʸl/(Shəmūˊel)', while the OET-RV usually uses its
#   own spelling of the name, and then puts the traditional/KJB spelling of it in a '!' '\add'
#   span right after, e.g. 'Yehudah \add !(Judah)\add*' or 'Yohan Markos \add !(John Mark)\add*'.
#   matchIdenticalProperNouns() and matchAdjustedProperNouns() can connect some of those, but not
#   the words that are inside the '!' span, and not a name that is spread over several OET-LV
#   words, so matchNamesViaTraditionalNames() below connects them.
lvAltNameRegex = re.compile( r'[/(]' )

# The '\add' code that says the span is the traditional/KJB spelling of the name that the OET-RV
#   has just spelled its own way, e.g. 'Yehudah \add !(Judah)\add*'.  A '/' in front of the name
#   ('\add !/ John Mark\add*') says that we have also changed the numbers of the words in the span.
TRADITIONAL_NAME_ADD_CODE = '!'

# The longest run of capitalised words in front of a '!' span that we treat as the OET-RV spelling
#   of the name that the span is the traditional spelling of, i.e. the 'Yohan Markos' of
#   'Yohan Markos \add !(John Mark)\add*'.  We stop at the first word that isn't capitalised.
MAX_NAME_WORDS_BEFORE_SPAN = 4

# What getTraditionalNameNumbers() found for an OET-RV word when it looked for the OET-LV name
#   that the word is another spelling of.  We don't use None/-1 for the two ambiguous answers,
#   because they mean opposite things: NO_LV_NAME means the rest of the name can tell us what
#   number this word is (e.g. the 'John' of 'Yohan¦91464 \add !(John)\add*', where the OET-LV
#   only has 'Yōannaʸs¦91464' and no 'John' word of its own), but AMBIGUOUS_LV_NAME means the
#   word is a spelling of more than one OET-LV name in the verse, so nothing can tell us.
NO_LV_NAME = None
AMBIGUOUS_LV_NAME = -1


def getLVNameSpellings( lvWord:str, nameTableKeys:tuple ) -> set:
    """
    Return all the different spellings that refer to one OET-LV name, so that we can tell which
        OET-LV word an OET-RV name is another name of.
    We use the parts of the OET-LV name itself (e.g. 'Yəhūdāh' and 'Judah' from
        'Yəhūdāh/Judah'), and the OET-RV spellings that the name tables have recorded for each of
        those parts (e.g. 'Yehudah' and 'Yihudah' — see loadHebGrkNameTables()).
    """
    spellings = { simplifyRVLVWord( lvWord ) }
    for key in lvAltNameRegex.split( lvWord ): # 'Yəhūdāh/Judah' becomes ['Yəhūdāh', 'Judah']
        key = key.strip()
        if not key: continue
        spellings.add( simplifyRVLVWord( key ) )
        for nameTableKey in nameTableKeys: # The name tables are keyed on the OET-LV spelling
            for something in state.nameTables[nameTableKey].get( key, set() ):
                spellings.add( simplifyRVLVWord( something ) )
        normalised = normalizeNameKey( key )
        if normalised: # The normalised index lets an RV word match an LV name whose transliteration differs slightly
            spellings.update( simplifyRVLVWord( something )
                              for something in state.namePartsIndex.get( normalised, () ) )
    # A name also has its traditional spelling (what the '!' '\add' span holds), which the decided
    #   OET-RV names table records against the OET-RV spellings, so add those in too.
    for spelling in tuple( spellings ):
        spellings.update( simplifyRVLVWord( traditionalName )
                          for traditionalName in state.rvNameTableInverse.get( spelling, () ) )
    return spellings
# end of connect_OET-RV_words_via_OET-LV.getLVNameSpellings


def getLvNameCandidates( lvWordList:List[str], nameTableKeys:tuple, testament:str ) -> List[Tuple[int,str,set]]:
    """
    Return the OET-LV names of a verse, each as (word number, name, all its spellings), for
        matchNamesViaTraditionalNames() to match OET-RV names against.
    We only use proper nouns (see lvWordIsProperNoun()).  We don't skip the words that share
        their number with another OET-LV word in the verse, because we match names by their
        spellings, and a number that covers two OET-LV words (e.g. Mark 1:5
        '\add >ones¦21722\add*_from¦21722_Hierousalaʸm¦21722') is still the one number of
        'Jerusalem'.
    """
    lvNameList = []
    for lvWordStr in lvWordList:
        lvNumber = getLVWordNumber( lvWordStr )
        if lvNumber is None: continue
        try:
            lvWord,lvNumber,lvWordRow = getLVWordRow( lvWordStr, testament )
        except WordNumberError as e:
            logging.critical( f"getLvNameCandidates() {e} from {lvWordStr=}" )
            continue
        if not lvWordIsProperNoun( lvWordRow, testament ): continue
        lvNameList.append( (lvNumber,lvWord,getLVNameSpellings( lvWord, nameTableKeys )) )
    return lvNameList
# end of connect_OET-RV_words_via_OET-LV.getLvNameCandidates


def getNameWordsBeforeSpan( liveWords:List[str], spanFirstIx:int, excludedWordIndexes:frozenset=frozenset() ) -> List[str]:
    """
    Return the run of capitalised words that comes immediately before a '!' '\add' span, i.e. the
        OET-RV spelling of the name that the span is the traditional spelling of,
        e.g. ['Yohan','Markos'] for 'Yohan Markos \add !(John Mark)\add*'.
    We stop at the first word that isn't capitalised (e.g. 'lived'), and we only look back a few
        words (see MAX_NAME_WORDS_BEFORE_SPAN), so that we don't sweep up an earlier name.
    'excludedWordIndexes' are the words of the other '\add' codes, which are added English rather
        than part of the OET-RV's own name.  Such a word ends the name (e.g. the 'rebuilt' of
        'from Beyt-El \add ≈rebuilt\add* Yeriho \add !(Jericho)\add*'), because the OET-RV name that
        the '!' span belongs to must be immediately next to it — otherwise we would sweep up an
        earlier, unrelated name (e.g. 'Beyt-El' here) and might give it a wrong word number.
    """
    nameWords = []
    for wordIx in reversed( range( spanFirstIx ) ):
        word = liveWords[wordIx]
        if wordIx in excludedWordIndexes: break # A word of another '\add' span, so the name isn't next to ours
        if not word or not word[0].isupper(): break # Not part of a name
        if '\\' in word: continue # One of the '\add' markers, which is not a word
        nameWords.insert( 0, word )
        if len( nameWords ) >= MAX_NAME_WORDS_BEFORE_SPAN: break
    return nameWords
# end of connect_OET-RV_words_via_OET-LV.getNameWordsBeforeSpan


def getTraditionalNameNumbers( nameWords:List[str], lvNameList:List[Tuple[int,str,set]] ) -> dict:
    """
    Return the OET-LV word number for each of the still-unnumbered OET-RV words of one name, as a
        { word: word number } dict, or an empty dict if we can't tell which OET-LV name(s) they are
        names of (a wrong word number is much worse than a missing one, so we give up rather than
        guess).
    'nameWords' are the OET-RV words of the one name, in the order that they appear in the verse,
        which is the OET-RV spelling of the name followed by the traditional spelling of it in the
        '!' span (e.g. ['Yohan','Markos','John','Mark']), and some of them may already have a word
        number that a human has checked.
    We work the numbers out like this:
        •  we look for the OET-LV name that each word is another spelling of, using
            getLvNameCandidates()
        •  if they all spell the names of the same OET-LV name, or each of them unambiguously
            spells the name of a different OET-LV word, we use those numbers (which is what puts
            the OET-LV numbers of 'John' and 'Mark' onto the 'John Mark' of
            'Yohan¦91464 Markos¦91468 \add !(John Mark)\add*' in the right order)
        •  if some of the words are spellings of no OET-LV word in the verse, and the rest are
            all the same one, then the rest tell us what number to give the others as well (this
            is what numbers the 'John' of 'Yohan \add !(John)\add*' in Mark 1:4, where the OET-LV
            has 'Yōannaʸs¦21698' and no 'John' word of its own)
        •  if neither of those works but the name already has exactly one word number, that one
            number covers the whole name, e.g. the 'Yohan¦92083 Markos \add !(John Mark)\add*'
            of Acts 13:13, where the OET-LV has just the one word that all four are names of
    """
    if not nameWords: return {}
    alreadyNumbered = { getRVWordNumber( word ) for word in nameWords if getRVWordNumber( word ) is not None }
    freeWords = [ word for word in nameWords if getRVWordNumber( word ) is None ]
    if not freeWords: return {} # Nothing to do

    # Which OET-LV name is each of our words a spelling of?
    numbers = []
    for word in freeWords:
        simpleWord = simplifyRVLVWord( word )
        candidateNumbers = { lvNumber for lvNumber,_lvName,spellings in lvNameList if simpleWord in spellings }
        if len( candidateNumbers ) == 1: numbers.append( candidateNumbers.pop() )
        elif candidateNumbers: numbers.append( AMBIGUOUS_LV_NAME )
        else: numbers.append( NO_LV_NAME )
    knownNumbers = set( number for number in numbers if number not in (NO_LV_NAME,AMBIGUOUS_LV_NAME) )

    if len( knownNumbers ) == 1 and NO_LV_NAME not in numbers: # The words are all names of the same one OET-LV name
        lvNumber = knownNumbers.pop()
        if alreadyNumbered and alreadyNumbered != { lvNumber }: return {} # The parts of the name disagree
        return dict( zip( freeWords, [lvNumber]*len(freeWords) ) )
    if not NO_LV_NAME in numbers and not AMBIGUOUS_LV_NAME in numbers:
        # Each word says which OET-LV word it is, and they are all different ones, so we can number
        #   them separately even when the name already has more than one number, e.g. the 'John Mark'
        #   of 'Yohan¦91464 Markos¦91468 \add !/ John Mark\add*' in Acts 12:12
        if alreadyNumbered and not alreadyNumbered.issubset( knownNumbers ): return {} # The parts of the name disagree
        return dict( zip( freeWords, numbers ) )
    # We can't work the name out from the OET-LV words, so fall back on the word number that the
    #   OET-RV already has somewhere in the name, if there is exactly one.
    if len( alreadyNumbered ) == 1:
        lvNumber = alreadyNumbered.pop()
        if all( number in (NO_LV_NAME,AMBIGUOUS_LV_NAME,lvNumber) for number in numbers ):
            return dict( zip( freeWords, [lvNumber]*len(freeWords) ) )
    return {}
# end of connect_OET-RV_words_via_OET-LV.getTraditionalNameNumbers


def matchNamesViaTraditionalNames( BBB:str, c:int,v:int, rvWordList:List[str], addSpans:List[Tuple[str,int,int]], lvWordList:List[str] ) -> Tuple[int,int]:
    """
    Connect an OET-RV name to the OET-LV word number of the name that it is another name of.

    The translator writes the traditional/KJB spelling of a name in a '!' '\add' span right after
        the OET-RV spelling of it, e.g. 'Yehudah \add !(Judah)\add*' against OET-LV
        'Yəhūdāh/Judah¦367711', because the OET-RV is allowed to spell names its own way.  Both
        spellings are one name, so we give them both the OET-LV word number, and a name that covers
        more than one OET-LV word, e.g. 'Yohan Markos \add !(John Mark)\add*', gets one number per
        OET-LV word, in the right order.
    (See getTraditionalNameNumbers() for how we decide which OET-LV name(s) we are looking at.)
    """
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag:
        fnPrint( DEBUGGING_THIS_MODULE, f"matchNamesViaTraditionalNames( {BBB} {c}:{v} {rvWordList} )" )
    assert rvWordList and lvWordList
    # We get the words of the '!' spans from the LIVE OET-RV text, because getCleanText() has
    #   already taken the '\add' markers off them, so we can't see which words they were.
    rvLiveText = getLiveRVVerseText( BBB, c,v )
    if not rvLiveText or not traditionalNameAddRegex.search( rvLiveText ): return 0,0 # No traditional names in this verse
    liveWords,allSpans = getRVWordsAndAddSpans( rvLiveText, f"{BBB} {c}:{v}",
                                                codesToExpose=(TRADITIONAL_NAME_ADD_CODE,),
                                                keepHyphenatedNames=True )
    # getRVWordsAndAddSpans() also reports the other '\add' codes that we didn't ask it to expose
    #   (the words of those spans are still in the text, with their code in front of them), so we
    #   must ignore those spans here, and we mustn't use their words as part of a name either.
    rvNameSpans = [ span for span in allSpans if span[0] == TRADITIONAL_NAME_ADD_CODE ]
    if not rvNameSpans: return 0,0
    # Any preceding span ends the current name, including another ! alias.
    # Otherwise "Shadrak !(Hananyah), Meyshak !(Misha'el)" can inherit
    # Shadrak's number for Meyshak through the earlier capitalised alias.
    otherSpanWords = {rvIx for _code,firstIx,lastIx in allSpans
                          for rvIx in range(firstIx, lastIx+1)}

    NT = bos_books_codes_py.is_new_testament_nr( BBB )
    testament = 'NT' if NT else 'OT'
    lvNameList = getLvNameCandidates( lvWordList, ('NT','NT_OT') if NT else ('OT',), testament ) # The OET-LV names in this verse
    stillFree = getUnnumberedRVWords( BBB, c,v )
    numAdded = numNS = 0
    for _code,firstIx,lastIx in rvNameSpans:
        # The OET-RV name, followed by the traditional name of it in the '!' span.
        #   (We keep hyphenated names as one word — e.g. '\add !(Tiglat-Pileser)\add*' — because
        #   the OET-RV numbers a name like that as a single word.)
        nameWords = [ word for word in getNameWordsBeforeSpan( liveWords, firstIx, otherSpanWords ) \
                            + liveWords[firstIx:lastIx+1]
                      if word and '\\' not in word and word[0].isupper()
                      and len( word ) >= MIN_ANCHORED_ADD_WORD_LENGTH ]
        if not nameWords: continue
        numbers = getTraditionalNameNumbers( nameWords, lvNameList )
        if not numbers:
            if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  matchNamesViaTraditionalNames() skipping {BBB} {c}:{v} {nameWords=}" )
            continue
        for rvWord,lvNumber in numbers.items():
            if simplifyRVLVWord( rvWord ) not in stillFree: continue # A matcher that ran before us got there first
            if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"matchNamesViaTraditionalNames() is adding {lvNumber} to RV '{rvWord}' at {BBB} {c}:{v}" )
            result = addNumberToRVWord( BBB, c,v, rvWord, lvNumber )
            if result:
                numAdded += 1
                if NT and 'N' in state.wordTable[testament][lvNumber][state.wordTableHeaderList[testament].index('GlossCaps')]: numNS += 1
            else:
                logging.warning( f"Got addNumberToRVWord( {BBB} {c}:{v} '{rvWord}' {lvNumber} ) result = {result}" )

    return numAdded,numNS
# end of connect_OET-RV_words_via_OET-LV.matchNamesViaTraditionalNames


def matchSpecialistAddSpans( BBB:str, c:int,v:int, rvWordList:List[str], addSpans:List[Tuple[str,int,int]], lvWordList:List[str] ) -> Tuple[int,int]:
    """
    Match same-verse elisions (≡) and traditional-name alternatives (!).
    Pronoun substitutions run later, using the live anchors created by lexical passes.
    We run these BEFORE the matchers that compare the OET-RV and OET-LV words with each other,
        because these rules use what the translator told us about the span, which is firmer
        evidence than the OET-RV and OET-LV words happening to look similar.
    """
    numAdded = numNS = 0

    for matcher in ( matchRepeatedWords, matchNamesViaTraditionalNames ):
        result,resultNS = matcher( BBB, c,v, rvWordList, addSpans, lvWordList )
        numAdded += result
        numNS += resultNS
    return numAdded,numNS
# end of connect_OET-RV_words_via_OET-LV.matchSpecialistAddSpans


def matchWordsManually( BBB:str, c:int,v:int, rvVerseWordList:List[str], lvVerseWordList:List[str] ) -> Tuple[int,int]:
    """
    """
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag:
        fnPrint( DEBUGGING_THIS_MODULE, f"matchWordsManually( {BBB} {c}:{v} {rvVerseWordList}, {lvVerseWordList} )" )
    assert rvVerseWordList and lvVerseWordList
    # if BBB=='JAM' and 'Jacob' in rvVerseWordList: print( lvVerseWordList ); assert False, "We want to stop here"

    # Firstly make matching lists of LV and RV words without the word numbers
    simpleLVWordList = []
    for lvWordStr in lvVerseWordList:
        try: lvWord, lvNumber = lvWordStr.split( '¦' )
        except ValueError:
            if lvWordStr != 'to':
                logging.critical( f"matchWordsManually failed on {lvWordStr=} from {BBB} {c}:{v} {lvVerseWordList=}" )
            lvWord = lvWordStr # One or two little mess-ups
        simpleLVWordList.append( lvWord )
    simpleRVWordList = []
    for rvWordStr in rvVerseWordList:
        try: rvWord, rvNumber = rvWordStr.split( '¦' )
        except ValueError: # Lots of RV words don't have numbers yet
            rvWord = rvWordStr
        simpleRVWordList.append( rvWord )

    numAdded = numNS = 0
    result1,result1NS = doGroup1( BBB, c, v, rvVerseWordList, lvVerseWordList, simpleLVWordList )
    numAdded += result1
    numNS += result1NS
    result2,result2NS = doGroup2( BBB, c, v, rvVerseWordList, lvVerseWordList, simpleRVWordList, simpleLVWordList )
    numAdded += result2
    numNS += result2NS

    return numAdded,numNS
# end of connect_OET-RV_words_via_OET-LV.matchWordsManually


def combineManualWordAlternatives(wordPairs, phraseRows):
    """Merge separately maintained word/phrase tables without changing priority.

    Each phrase records how many single-word alternatives for the same RV word
    precede it. Insert phrases backwards so equal priorities retain their order.
    Only alternatives for the same exact RV spelling compete with each other.
    """
    alternatives = {}
    for rvWord, lvWord in wordPairs:
        alternatives.setdefault(rvWord, []).append(lvWord)
    wordCounts = {rvWord: len(words) for rvWord, words in alternatives.items()}
    for rvWord, lvPhrase, wordsBefore in reversed(phraseRows):
        assert 0 <= wordsBefore <= wordCounts.get(rvWord, 0), f'{rvWord=} {lvPhrase=} {wordsBefore=}'
        alternatives.setdefault(rvWord, []).insert(wordsBefore, lvPhrase)
    return tuple((rvWord, lvWords) for rvWord, lvAlternatives in alternatives.items()
                 for lvWords in lvAlternatives)


MANUAL_RV_WORD_ALTERNATIVES = combineManualWordAlternatives(
    RV_SINGLE_WORDS_FROM_LV_WORDS, RV_SINGLE_WORDS_FROM_LV_WORD_STRINGS)

# Keep table priority, but visit only spellings actually present in the verse.
# Scanning thousands of unrelated alternatives dominated clean rebuilds.
MANUAL_WORD_INDEX = defaultdict(list)
for _priority, (_rvWord, _lvPhrase) in enumerate(MANUAL_RV_WORD_ALTERNATIVES):
    MANUAL_WORD_INDEX[_rvWord].append((_priority, _rvWord, _lvPhrase.split()))
DIRECTIONAL_WORD_INDEX = defaultdict(set)
for _rvWord, _lvWord in RV_SINGLE_WORDS_FROM_LV_WORDS:
    DIRECTIONAL_WORD_INDEX[_rvWord.casefold()].add(_lvWord.casefold())
ALIGNED_PHRASE_INDEX = defaultdict(list)
for _rvPhrase, _lvPhrase in (
        *((rv, lv) for rv, lv, _ in RV_SINGLE_WORDS_FROM_LV_WORD_STRINGS),
        *((rv, lv) for lv, rv in LV_SINGLE_WORDS_TO_RV_WORD_STRINGS)):
    _rvWords, _lvWords = tuple(_rvPhrase.casefold().split()), tuple(_lvPhrase.casefold().split())
    ALIGNED_PHRASE_INDEX[_rvWords[0]].append((_rvWords, _lvWords))


def doGroup1( BBB:str, c:int, v:int, rvVerseWordList:List[str], lvVerseWordList:List[str], simpleLVWordList:List[str] ) -> Tuple[int,int]:
    """Match curated one-RV-word translations only when the LV word/phrase is unique.

    In particular, 'his' cannot take the FIRST 'of him' in a verse containing
    several people. The old first-match search silently made that mistake.
    """
    NT = bos_books_codes_py.is_new_testament_nr(BBB)
    added = ns = 0
    candidates = sorted(row for word in set(rvVerseWordList)
                        if rvVerseWordList.count(word) == 1
                        for row in MANUAL_WORD_INDEX.get(word, ()))
    for _, rvWord, words in candidates:
        matches = [i for i in range(len(simpleLVWordList)-len(words)+1)
                   if simpleLVWordList[i:i+len(words)] == words]
        if len(matches) != 1:
            continue
        number = getLVWordNumber(lvVerseWordList[matches[0]])
        if number is not None and addNumberToRVWord(BBB, c, v, rvWord, number):
            added += 1
            if NT and 'N' in state.wordTable['NT'][number][state.wordTableHeaderList['NT'].index('GlossCaps')]: ns += 1
    return added, ns


def doGroup2( BBB:str, c:int, v:int, rvVerseWordList:List[str], lvVerseWordList:List[str], simpleRVWordList:List[str], simpleLVWordList:List[str] ) -> Tuple[int,int]:
    """
    This list is one LV word to many RV words
    """
    numAdded = numNS = 0
    for lvWord, rvWordStr in LV_SINGLE_WORDS_TO_RV_WORD_STRINGS:
        if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 4:
            dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"{lvWord=} {rvWordStr=}" )
        rvWords = rvWordStr.split( ' ' )
        assert len(rvWords) <= 4, rvWords # if more, we need to add searching code down below

        if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 4:
            dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"  Looking for LV '{lvWord}'" )
        lvIndexes = []
        for lvIx,thisLvWord in enumerate( simpleLVWordList ):
            if thisLvWord == lvWord:
                if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 4:
                    dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"  matchWordsManually group2 found LV '{lvWord}' in {BBB} {c}:{v}")
                lvIndexes.append( lvIx )

        if len(lvIndexes) == 1: # Only one LV word matches
            lvWordStr = lvVerseWordList[lvIndexes[0]]
            assert '¦' in lvWordStr
            lvWord, lvWordNumber = lvWordStr.split( '¦', 1 )
            lvWordNumber = getPositiveLeadingInt( lvWordNumber )
            # print( f"    here with {lvWordStr} -> '{lvWord}' and {lvWordNumber=}")

            # Now see if we have the RV word(s)
            for rvIx, thisRvWord in enumerate( simpleRVWordList ):
                matchedRvWordCount = 0
                if thisRvWord == rvWords[0]: # matched one word
                    matchedRvWordCount += 1
                    # print( f"      Matched 1/{len(rvWords)} @ {rvIx} with '{thisRvWord}' ({rvWordList[rvIx]})")
                    if matchedRvWordCount == len(rvWords): break # matched one word
                    if rvIx < len(simpleRVWordList)-1:
                        if simpleRVWordList[rvIx+1] == rvWords[1]:
                            matchedRvWordCount += 1
                            if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 4:
                                dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"        Matched 2/{len(rvWords)} @ {rvIx+1} with '{rvVerseWordList[rvIx+1]}' from '{rvWordStr}'")
                            if matchedRvWordCount == len(rvWords): break # matched two words
                            if rvIx < len(simpleRVWordList)-2:
                                if simpleRVWordList[rvIx+2] == rvWords[2]:
                                    matchedRvWordCount += 1
                                    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
                                        dPrint( 'Info', DEBUGGING_THIS_MODULE, f"          Matched 3/{len(rvWords)} @ {rvIx+2} with '{rvVerseWordList[rvIx+2]}' from '{rvWordStr}'")
                                    if matchedRvWordCount == len(rvWords): break # matched three words
                                    if rvIx < len(simpleRVWordList)-3:
                                        if simpleRVWordList[rvIx+3] == rvWords[3]:
                                            matchedRvWordCount += 1
                                            if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
                                                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"          Matched 4/{len(rvWords)} @ {rvIx+3} with '{rvVerseWordList[rvIx+3]}' from '{rvWordStr}'")
                                            if matchedRvWordCount == len(rvWords): break # matched four words
            else: # no match (no break from above/inner loop)
                continue # in the outer loop
            if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"    matchWordsManually group2 {BBB} {c}:{v} matched {lvWord=} {rvWords=}" )
            # lvWord,lvWordNumber,lvWordRow = getLVWordRow( lvWordList[lvIx] )
            if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"matchWordsManually group2 is adding a number to RV {rvWords} from '{lvWord}' at {BBB} {c}:{v} {rvIx=}")
            for rvWord in rvWords:
                result = addNumberToRVWord( BBB, c,v, rvWord, lvWordNumber )
                if result:
                    numAdded += 1
                else:
                    logging.warning( f"Got addNumberToRVWord( {BBB} {c}:{v} '{rvWord}' {lvWordNumber} ) result = {result}" )
                # why_did_we_fail
    return numAdded,numNS
# end of connect_OET-RV_words_via_OET-LV.doGroup1


def getLVWordRow( wordWithNumber:str, testament:str ) -> Tuple[str,int,List[str]]:
    """
    """
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag:
        fnPrint( DEBUGGING_THIS_MODULE, f"getLVWordRow( {wordWithNumber}, {testament} )" )
    assert '¦' in wordWithNumber
    assert testament in ('OT','NT')

    try: word,wordNumber = wordWithNumber.split( '¦' ) # Gives a ValueError if the wordNumber separator character is missing or if there's multiple
    except ValueError:
        raise WordNumberError( f"Failed to split-off OET-LV word number from {testament} {wordWithNumber=}" )
    # assert word.isalpha(), f"Non-alpha '{word}'" # not true, e.g., from 'Yaʸsous/(Yəhōshūˊa)¦21754'
    try: wordNumber = int( wordNumber )
    except ValueError:
        # A trailing gloss-helper character (e.g. ˒) is valid ESFM.
        wordNumber = getPositiveLeadingInt( wordNumber )
    assert wordNumber < len( state.wordTable[testament] )
    wordRow = state.wordTable[testament][wordNumber]
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 4:
        dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"'{word}' {wordRow}" )
    return word,wordNumber,wordRow
# end of connect_OET-RV_words_via_OET-LV.getLVWordRow


# Specialist add codes describe the translator's relationship to the source.
# Plain, < and > additions (including uncertain forms) have no source word:
# unlinked_add_spans() identifies them for cleanup and coverage consistently
# with Token.linkable. Nested \+add markers have exactly the same semantics.
ADD_SPECIAL_CHARS = '@#≈≡*<>&%?+^!='


# A '\add <code>...<text>\add*' specialist span.  The code is what the translator is telling us
#   about the span, e.g. '\add ≈because\add*' (we reworded it) or '\add #straps\add*' (we
#   changed the number).  A leading '?' means the translator is not sure about the code
#   (e.g. '\add ?≈about\add*'), and the OET-RV never puts the '?' after the code.
specialAddSpanRegex = re.compile(
    f'\\\\\\+?add (?P<code>\\?[{ADD_SPECIAL_CHARS}]|[{ADD_SPECIAL_CHARS}])(?P<text>[^\\\\]*?)\\\\\\+?add\\*' )

# Specialist span words available to lexical and formatting-aware passes.
# Plain additions and <, >, +, =, ^ are excluded from automatic connections.
# Traditional-name (!) spans have their own matching pass.
ADD_CODES_TO_EXPOSE = ( '≈', '#', '@', '*', '%', '&', '≡' )
addCloseMarkerRegex = re.compile( r'\\(?:\+)?add\*$' ) # The '\add*' or '\+add*' that closes a span
addCloseMarkerAnywhereRegex = re.compile( r'\\(?:\+)?add\*' ) # The same, but punctuation can follow it
addMarkerRegex = re.compile( r'\\(?:\+)?add\*?' ) # The '\add' or '\+add' and the '\add*' or '\+add*'
# The '\add' spans that give the traditional/KJB spelling of a name, e.g. '\add !(Judah)\add*'.
#   We can't just look for the '!' character, because a '!' can also be the punctuation at the end
#   of what somebody says, e.g. '“You are God's son!”'.
traditionalNameAddRegex = re.compile( r'\\(?:\+)?add (?:\?)?!' )

# When we expose one of the ADD_CODES_TO_EXPOSE spans above, we wrap it in these two
#   Unicode private-use characters so that the matchers can still tell where the span
#   starts and ends, now that the '\add' and '\add*' markers have gone:
#       '\add ≈because\add*'  becomes  '\uE000≈because\uE001'
# The start character is followed by the code, and the end character sits at the end of the
#   span.  They never occur in an OET-RV verse, and splitExposedAddSpan() removes them (and
#   the code) from the words before the matchers compare them, so they are just bookkeeping.
ADD_SPAN_START_CHAR = '\uE000'
ADD_SPAN_END_CHAR = '\uE001'
addSpanMarkerRegex = re.compile( f'[{ADD_SPAN_START_CHAR}{ADD_SPAN_END_CHAR}]' )

def exposeMatchedAddSpans( rvText:str, codesToExpose:tuple=ADD_CODES_TO_EXPOSE ) -> str:
    """
    Rewrite the '\add' spans of an OET-RV verse that we can use to connect words (see
        ADD_CODES_TO_EXPOSE), by dropping the '\add <code>' and '\add*' markers and marking
        where the span starts and ends, e.g.
            '\add #straps\add*' becomes '\uE000#straps\uE001'
            '\add ≈because\add*' becomes '\uE000≈because\uE001'
    Every other '\add' span is left exactly as it is, so its words stay invisible to the
        matchers (i.e. they are words that were added into the English text).
    'codesToExpose' defaults to ADD_CODES_TO_EXPOSE, but matchNamesViaTraditionalNames() passes in
        just the '!' code, so that only the words of the '!' spans get exposed.
    """
    def replacer( match ):
        code = match.group( 'code' ).lstrip('?')
        if code not in codesToExpose: return match.group( 0 )
        return f"{ADD_SPAN_START_CHAR}{code}{match.group( 'text' )}{ADD_SPAN_END_CHAR}"
    return specialAddSpanRegex.sub( replacer, rvText )
# end of exposeMatchedAddSpans



def getRVVerseLines(BBB:str, c:int, v:int):
    """Use printed RV coordinates; a mapped passage may contain several verses."""
    return getattr(state, 'rvAlignmentLines', state.rvLineIndex).get((c, v), ())


def getLiveRVTokens(BBB:str, c:int, v:int):
    """Cache tokens until a verse's lines change; offsets always describe live text."""
    entries = getRVVerseLines(BBB, c, v)
    signature = tuple(state.rvESFMLines[n] for n, _ in entries)
    key = (c, v)
    cached = state.rvTokenCache.get(key)
    if cached is None or cached[0] != signature:
        tokens = [t for n, start in entries for t in tokenize(state.rvESFMLines[n][start:], n, start)]
        state.rvTokenCache[key] = (signature, tokens)
    return state.rvTokenCache[key][1]


def getLiveRVVerseText( BBB:str, c:int, v:int ) -> str:
    """Return only this verse's body text, with character markers intact."""
    return ' '.join(state.rvESFMLines[n][start:] for n, start in getRVVerseLines(BBB, c, v))


def getRVWordsAndAddSpans( rvText:str, connectRef:str, codesToExpose:tuple=ADD_CODES_TO_EXPOSE, keepHyphenatedNames:bool=False ) -> Tuple[List[str],List[Tuple[str,int,int]]]:
    """
    Return the OET-RV words of a verse, together with the exposed '\\add' specialist spans inside
        them, as a list of (code, first word index, last word index), e.g. ('@', 4, 6) for the
        three words of '\\add @the netted men\\add*'.

    'rvText' is the text of the OET-RV verse WITH the '\\add' markers still in it (see
        getLiveRVVerseText()), so we can see where each span starts and ends.  It can also be a
        text that has already lost its markers, in which case we can still see the code on the
        front of the first word of a span (e.g. '@Yeshua' for '\\add @Yeshua\\add*'), and we
        then treat the span as being that one word, which is all that the '≈' and '#' codes need.

    'keepHyphenatedNames' keeps a hyphenated capitalised name as the single word that it is in the
        OET-RV, e.g. 'Tiglat-Pileser' in '\add !(Tiglat-Pileser)\add*', because we number such a
        name as one word.  matchNamesViaTraditionalNames() needs that, but nobody else does,
        because everywhere else the parts of a hyphenated word are compared separately.
    A hyphenated word that is NOT capitalised, e.g. 'empty-handed', is the one word that the OET-RV
        and the OET-LV both use, so we keep it as one word (see simplifyRVLVWord(), which takes the
        hyphens out before it compares the two).  A capitalised one is still split into its parts,
        because there the OET-LV usually glosses the parts as separate words.
    """
    if '\\' in rvText:
        words, spans = [], []
        active = None
        for token in tokenize(rvText, split_names=not keepHyphenatedNames):
            if not token.linkable or token.code is not None and token.code not in codesToExpose:
                active = None
                continue
            word = token.text + (f'¦{token.number}' if token.number is not None else '')
            index = len(words)
            words.append(word)
            if token.code in codesToExpose:
                if active == token.span and spans:
                    code, first, _ = spans[-1]
                    spans[-1] = (code, first, index)
                else:
                    spans.append((token.code, index, index))
                active = token.span
            else:
                active = None
        return words, spans
    rvAdjText = exposeMatchedAddSpans( rvText, codesToExpose )
    # getCleanText() gives us text whose '\add' spans have lost their markers, but the text
    #   from getLiveRVVerseText() still has the markers on the spans that we didn't expose, so
    #   remove them to get the same words from both
    rvAdjText = addMarkerRegex.sub( '', rvAdjText ) \
                .replace(ORDER_REVERSAL_CHARACTER,'').replace('◘','').replace('…','') \
                .replace(' / ',' ').replace('/',' ').replace('—',' ') \
                .replace( '(', '').replace( ')', '' ) \
                .replace( '“', '' ).replace( '”', '' ).replace( '‘', '' ).replace( '’', '' )
    # Strip the sentence punctuation, but not a punctuation character that is one of the codes we
    #   were asked to expose: the '!' of a traditional-name span is punctuation AND its code, and
    #   splitExposedAddSpan() has to see it to report which span it is.
    for punctuation in ( '.', ',', ':', ';', '?', '!' ):
        if punctuation not in codesToExpose: rvAdjText = rvAdjText.replace( punctuation, '' )
    rvAdjText = rvAdjText.replace('  ',' ').strip()
    if not rvAdjText: return [],[]

    rvWords = []
    rvAddSpans = [] # The exposed '\add' specialist spans in rvWords, as (code, first word index, last word index)
    addSpanCode = addSpanStartIx = None
    for rvToken in rvAdjText.split( ' ' ):
        # Note that a token can be dropped below (a hyphenated word whose second part isn't
        #   capitalised, e.g. 'whole-heartedly'), so we have to keep track of the span markers
        #   on such a token, or we would lose the start or the end of the '\add' span it is in
        spanEvents,rvToken = splitExposedAddSpan( rvToken, codesToExpose )
        if rvToken:
            rvWordBits = rvToken.split( '-' )
            if len(rvWordBits) == 1 or keepHyphenatedNames: rvNewWords = [ rvToken ] # No hyphen, or a hyphenated name that we keep as one word
            elif rvWordBits[1] and rvWordBits[1][0].isupper(): # Hyphenated and with a capital letter, e.g., Kiriat-Arba (may even have three parts)
                rvNewWords = rvWordBits
            elif not rvToken[0].isupper(): rvNewWords = [ rvToken ] # Hyphenated but not capitalised, e.g. 'empty-handed', which is one word in the OET-RV and in the OET-LV
            else: rvNewWords = [] # A capitalised name whose second part is a word of its own, e.g. 'Yahweh-nissi', which we leave to the proper-noun matchers
        else: rvNewWords = [] # An exposed '\add' span that holds no words
        for event,code in spanEvents:
            if event == 'start':
                assert addSpanCode is None, f"Nested exposed '\\add' span at {connectRef} {rvToken=}"
                addSpanCode = code
                addSpanStartIx = len( rvWords ) # The index that the first new word (if any) will get
        rvWords.extend( rvNewWords )
        for event,code in spanEvents:
            if event == 'start': continue
            assert addSpanCode is not None, f"Unclosed exposed '\\add' span at {connectRef} {rvToken=}"
            if rvWords: rvAddSpans.append( (addSpanCode,addSpanStartIx,len( rvWords )-1) )
            addSpanCode = addSpanStartIx = None
    assert addSpanCode is None, f"Unclosed exposed '\\add' span at {connectRef}"
    return rvWords, [ addSpan for addSpan in rvAddSpans if addSpan[1] <= addSpan[2] ]
# end of connect_OET-RV_words_via_OET-LV.getRVWordsAndAddSpans


def splitExposedAddSpan( token:str, codesToExpose:tuple=ADD_CODES_TO_EXPOSE ) -> Tuple[List[Tuple[str,str]],str]:
    """
    Pull the exposed '\add' span markers off a token that came from exposeMatchedAddSpans(),
        e.g. '\uE000#straps' becomes ([('start','#'),('end','')], 'straps') and 'demons\uE001'
        becomes ([('end','')], 'demons').
    'token' must be a single word, so a word can only be the start or the end of a span (or
        both, if the span holds a single word), but it could still be the end of one span and
        the start of the next, so we return the events in the order that they appear in the
        word.
    A token that has no span markers but does start with one of the ADD_CODES_TO_EXPOSE codes
        (e.g. '#straps' or '@Yeshua') is a span of one word that lost its '\add' markers, and we
        return it as such, so that the caller doesn't have to treat those two cases differently.
    'codesToExpose' is the same tuple that exposeMatchedAddSpans() was given, so that we can
        recognise a code that it exposed but that isn't one of the usual ones (e.g. the '!' of
        matchNamesViaTraditionalNames()).
    """
    if ADD_SPAN_START_CHAR not in token and ADD_SPAN_END_CHAR not in token:
        if token[0:1] in ADD_CODES_TO_EXPOSE:
            return [ ('start',token[0]), ('end','') ], token[1:]
        return [], token
    events = []
    bits = []
    pos = 0
    for marker in addSpanMarkerRegex.finditer( token ):
        bits.append( token[pos:marker.start()] )
        pos = marker.end()
        if marker.group( 0 ) == ADD_SPAN_START_CHAR:
            # The '\add' code follows the start marker, but only if it is still there
            #   (the '≈' code used to be removed by the normal word clean-up, and an
            #   exposed span that holds no words has no code at all)
            code = token[pos:pos+1] if token[pos:pos+1] in codesToExpose else ''
            events.append( ('start',code) )
            if code: pos += 1
        else:
            events.append( ('end','') )
    bits.append( token[pos:] )
    return events, ''.join( bits )
# end of splitExposedAddSpan


def isInsideUnlinkedAddSpan(line:str, index:int) -> bool:
    """Whether an offset is inside a plain, < or > addition, including +add/? forms."""
    return any(start < index < end for start, end in unlinked_add_spans(line))


ndStartMarkerRegex = re.compile( r'\\\+?nd ' ) # A nomina sacra open marker, e.g. '\nd ' or '\+nd '
ndEndMarkerRegex = re.compile( r'\\\+?nd\*' ) # A nomina sacra close marker, e.g. '\nd*' or '\+nd*'

def isInsideNominaSacraSpan( line:str, index:int ) -> bool:
    """
    Return True if the character at 'index' in 'line' is inside a nomina sacra
        '\\nd ...\\nd*' span that has already been opened before 'index'.

    We count the open and the close markers that come before 'index' rather than matching
        '\\nd ...\\nd*' spans with a single regex, because we cannot pair the markers up with a
        regex once they are nested, and nesting them is exactly the fault that this function
        exists to detect: an earlier run could insert a '\\nd ...\\nd*' span around a word that
        was already the first word of one, giving 'son¦113159 \\nd \\nd Yeshua¦113161\\nd*'.
    """
    numOpens = len( ndStartMarkerRegex.findall( line[:index] ))
    numCloses = len( ndEndMarkerRegex.findall( line[:index] ))
    return numOpens > numCloses
# end of isInsideNominaSacraSpan


def removeWordNumbersInUnlinkedAddSpans(filename:str, lines:List[str]) -> int:
    """Remove source numbers from plain, < and > additions in place.

    These words have no source-word counterpart. Nested character fields and
    uncertain codes do not change that rule. Preserve wording and all markers.
    Return the number of individual source-number suffixes removed.
    """
    numRemoved = 0
    for n, line in enumerate(lines):
        if '¦' not in line:
            continue
        numLineRemoved = 0
        for start, end in reversed(list(unlinked_add_spans(line))):
            cleaned, removed = wordLinkRegex.subn('', line[start:end])
            line = line[:start] + cleaned + line[end:]
            numLineRemoved += removed
        if numLineRemoved:
            vPrint('Normal', DEBUGGING_THIS_MODULE,
                   f"    Removed {numLineRemoved:,} word number(s) from plain, < or > add spans in {filename} line {n+1}.")
            lines[n] = line
            numRemoved += numLineRemoved
    return numRemoved
# end of removeWordNumbersInUnlinkedAddSpans


# The OET-RV lines that hold something other than translated Bible text, so their words can never
#   have a word number: section headings, the translator's heading comments, the titles of the
#   poetry sections, the speaker of a saying, and the letters of an acrostic poem.
nonTextLineMarkers = ( '\\s1','\\s2','\\s3','\\s4','\\r','\\rem','\\mr','\\ms1','\\ms2','\\sp','\\sr','\\qa' )
# The OET-RV spans that hold something other than translated Bible text, so their words can never
#   have a word number: the translator's notes ('\f ...\f*', including the '\fr'/'\ft' sub-parts),
#   the cross-references ('\x ...\x*'), and the file and image links ('\jmp ...\jmp*', '\fig ...\fig*').
nonTextSpanRegex = re.compile( r'\\(f[a-z]*|x|jmp|fig)\b.*?\\\1\*' )
# The OET-RV characters that run two words together (e.g. 'Satan¦29058—you're¦29061'),
#   or that are not a word at all, so that we get the same words that
#   getRVWordsAndAddSpans() gets when it matches the OET-RV against the OET-LV
rvWordSeparatorChars = ( ORDER_REVERSAL_CHARACTER, '◘', '…', '—', '/', '(', ')' )
# Any other USFM marker that is left in an OET-RV verse, e.g. '\nd ' or '\wj' or '\+add*'
#   (The '+/add*' variants are the continued-character markers, which the OET-RV uses for the
#    nomina sacra and for the added-words spans.)
usfmMarkerRegex = re.compile( r'\\\+?[a-zA-Z0-9]+\*?' )

def stripUSFMMarker( match ) -> str:
    """
    Replacement function for usfmMarkerRegex: take a USFM marker out of an OET-RV verse.

    We leave a space behind if the marker was stuck onto the end of the word in front of it
        (e.g. 'God¦123\\+nd*' or 'first\\wj*second'), so that we don't run those two words together.
    A marker that is stuck onto the front of the next word (e.g. '\\add*brothers') just goes,
        because there is nothing in front of it to run it together with.
    """
    return ' ' if match.start() and not match.string[match.start()-1].isspace() else ''
# end of stripUSFMMarker

def getVerseTextWords( verseText:str ) -> List[str]:
    """
    Split the text of an OET-RV verse into the words that could have an OET-LV word number.

    We throw away the words that can never have one, so that they are left out of the word
        number percentages (see countWordsAndWordNumbers()):
            the translator's notes, the cross-references and the file/image links, because they
                are not translations of the Hebrew or Greek at all
            plain, < and > additions (including ?/+add forms), because they have
                no corresponding OET-LV word to be numbered
    (The words of the other '\\add' spans, e.g. '\\add ≈because\\add*', DO get word numbers,
        because they are still translations of an OET-LV word, so we keep them here.)
    The word numbers themselves are left attached to their words, so the caller can count them.
    """
    text = nonTextSpanRegex.sub( ' ', verseText ) # The notes, the cross-references and the links
        # NOTE: These have to go first, because a note can be inside an add span.
    for start, end in reversed(list(unlinked_add_spans(text))):
        text = text[:start] + ' ' + text[end:] # Additions with no source-word counterpart
    for separatorChar in rvWordSeparatorChars:
        text = text.replace( separatorChar, ' ' ) # The characters that run two words together
    text = usfmMarkerRegex.sub( stripUSFMMarker, text ).strip() # The markers that are left
    return [ word for word in text.split() if any(char.isalnum() for char in word) ] # Ignore stray punctuation
# end of getVerseTextWords


def countWordsAndWordNumbers( rvESFMLines:List[str] ) -> Tuple[int,int]:
    """
    Count the words of an OET-RV book that could have a word number, and how many of them have one.

    We only count the text of the verses (including their poetry lines, and the '\\d' lines of
        Psalms), because that is the only text that gets connected to the OET-LV.
    The words that can never have a word number are left out of BOTH figures
        (see getVerseTextWords()), so that the percentage says how much of the OET-RV that we
        have actually connected to the OET-LV.

    Returns a (numWords,numWordNumbered) tuple.
    """
    numWords = numWordNumbered = 0
    foundVerse = False
    for line in rvESFMLines:
        try: marker, rest = line.split( ' ', 1 )
        except ValueError: marker, rest = line, '' # Only a marker
        if not rest or marker in nonTextLineMarkers: continue
        if marker == '\\c': foundVerse = False # A new chapter, so any verse of the last one is finished
        elif marker == '\\v':
            _verseNumber,_separator,rest = rest.partition( ' ' ) # Drop the verse number
            foundVerse = True
        elif marker == '\\d': foundVerse = True # Scriptural titles, whether separate or part of verse 1
        if not foundVerse: continue # Not the text of a verse, e.g. the book introduction
        verseWords = getVerseTextWords( rest )
        numWords += len( verseWords )
        numWordNumbered += sum( 1 for verseWord in verseWords if '¦' in verseWord )
    return numWords, numWordNumbered
# end of countWordsAndWordNumbers


def reportWordNumberPercentage( description:str, numWords:int, numWordNumbered:int ) -> None:
    """
    Say what percentage of the words of 'description' (e.g. 'OT' or 'Whole Bible') have a word number.
    """
    if not numWords:
        if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 2:
            vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  No words found for {description}." )
        return
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 2:
        vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  {description} has word numbers on {numWordNumbered:,} of {numWords:,} words ({numWordNumbered*100/numWords:.1f}%)." )
# end of reportWordNumberPercentage


def applyRVTokenLink(BBB, c, v, token, number, reason):
    """Insert at an exact source position without changing existing links or text."""
    line = state.rvESFMLines[token.line]
    if not token.linkable or token.number is not None:
        return 0, 0
    if line[token.start:token.end] != token.text or line[token.end:token.end+1] == '¦':
        return 0, 0  # A caller supplied a stale position.
    NT = bos_books_codes_py.is_new_testament_nr(BBB)
    addNS = (NT and 'N' in state.wordTable['NT'][number][state.wordTableHeaderList['NT'].index('GlossCaps')]
             and token.code is None and not isInsideNominaSacraSpan(line, token.start))
    # Nested character fields (e.g. words of Jesus) need +nd, never a second bare nd.
    nested = False
    if addNS:
        opens = re.findall(r'\\(\+?[a-zA-Z]+)(\*| )', line[:token.start])
        stack = []
        for marker, close in opens:
            if close == '*':
                if stack and stack[-1] == marker: stack.pop()
            elif marker.lstrip('+') in BibleOrgSysGlobals.USFMCharacterMarkers:
                stack.append(marker)
        nested = bool(stack)
    startND, endND = ('\\+nd ', '\\+nd*') if nested else ('\\nd ', '\\nd*')
    replacement = f'{startND if addNS else ""}{token.text}¦{number}{endND if addNS else ""}'
    state.rvESFMLines[token.line] = line[:token.start] + replacement + line[token.end:]
    state.bookLinkAdditions += 1
    if BibleOrgSysGlobals.commandLineArguments.report:
        state.audit.append(dict(book=BBB, chapter=c, verse=v, line=token.line+1,
                                word=token.text, number=number, reason=reason))
    return 1, int(bool(addNS))


# Function words need the positional/phrase matcher even when their spelling is
# unique. For example, ACT 19:40-41 "And ... have no defence" must not borrow
# "And having said" from the dismissal sentence after the quotation.
CONTEXT_ONLY_WORDS = MOVEMENT_FUNCTION_WORDS
AUXILIARY_WORDS = {'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
                   'have', 'has', 'had', 'having', 'do', 'does', 'did',
                   'will', 'would', 'shall', 'should', 'can', 'could', 'may', 'might', 'must'}


def functionWordFitsAnchors(tokens, token, number, positions):
    """Reject a weak spelling match that contradicts established passage order.

    Neighbouring source groups are inclusive: an auxiliary can share its verb's
    number, including a multiword translation. A source group owned only
    elsewhere cannot be borrowed. Auxiliaries also stay within neighbour bounds;
    ordinary articles/prepositions can change position around a content word.
    With no anchors yet, the caller's verse-wide uniqueness check still applies.
    """
    if number not in positions:
        return False
    index = tokens.index(token)
    left = next((t for t in reversed(tokens[:index]) if t.number in positions), None)
    right = next((t for t in tokens[index+1:] if t.number in positions), None)
    neighbours = {t.number for t in (left, right) if t is not None}
    if number not in neighbours and any(t.number == number for t in tokens if t != token):
        return False
    if token.text.casefold() not in AUXILIARY_WORDS:
        return True
    lo = min(positions[left.number]) if left else -1
    hi = max(positions[right.number]) if right else float('inf')
    return any(lo <= position <= hi for position in positions[number])


def addNumberToRVWord( BBB:str, c:int,v:int, word:str, wordNumber:int ) -> bool:
    """Legacy spelling-only match: require a unique full word in the whole verse.

    Positional alignment calls applyRVTokenLink directly for repeated words.
    Never match inside a contraction, a footnote, a heading, or a plain, < or > addition.
    Semantic substitutions require positional matching. Function-word fallbacks
    may not contradict existing anchors or reuse a distant source group.
    """
    assert isinstance(wordNumber, int) and '¦' not in word
    tokens = getLiveRVTokens(BBB, c, v)
    matches = [t for t in tokens if t.text == word and t.linkable
               and t.code not in SEMANTIC_CODES]
    if not matches and '-' in word:
        # Traditional-name mappings can intentionally number a whole compound
        # name; ordinary alignment can also number its components separately.
        matches = [t for n, start in getRVVerseLines(BBB, c, v)
                   for t in tokenize(state.rvESFMLines[n][start:], n, start, split_names=False)
                   if t.text == word and t.linkable and t.code not in SEMANTIC_CODES]
    if len(matches) != 1:
        return False
    if word.casefold() in CONTEXT_ONLY_WORDS:
        context = getattr(state, 'functionWordContext', None)
        if context is None or context[0] != (BBB, c, v):
            return False
        if not functionWordFitsAnchors(tokens, matches[0], wordNumber, context[1]):
            return False
    return bool(applyRVTokenLink(BBB, c, v, matches[0], wordNumber, 'lexical/name rule')[0])


def addNumberToRVPhrase( BBB:str, c:int,v:int, rvPhraseWords:List[str], lvNumber:int ) -> Tuple[int,int]:
    """Complete one occurrence of a curated phrase, retaining compatible existing links.

    Token positions allow repeated component words and nested formatting. A
    conflicting number or an added word anywhere in the phrase blocks it.
    """
    words = [word.casefold() for word in rvPhraseWords]
    tokens = getLiveRVTokens(BBB, c, v)
    occurrences = []
    for i in range(len(tokens)-len(words)+1):
        span = tokens[i:i+len(words)]
        if [t.text.casefold() for t in span] != words:
            continue
        if not all(t.linkable and t.code not in SEMANTIC_CODES for t in span):
            continue
        if any(t.number is not None and t.number != lvNumber for t in span):
            continue
        if any(t.number is None for t in span):
            occurrences.append(span)
    if len(occurrences) != 1:
        return 0, 0
    added = ns = 0
    for token in reversed(occurrences[0]):
        result, resultNS = applyRVTokenLink(BBB, c, v, token, lvNumber, 'curated phrase')
        added += result
        ns += resultNS
    return added, ns


if __name__ == '__main__':
    multiprocessing.set_start_method('fork') # The default was changed on POSIX systems from 'fork' to 'forkserver' in Python3.14
    multiprocessing.freeze_support() # Multiprocessing support for frozen Windows executables

    # Configure basic Bible Organisational System (BOS) set-up
    parser = BibleOrgSysGlobals.setup( PROGRAM_NAME, PROGRAM_VERSION )
    parser.add_argument('--books', nargs='+', metavar='BBB', help='process only these BOS book codes (e.g. RUT MRK)')
    parser.add_argument('--dry-run', action='store_true', help='compute links and coverage without writing ESFM files')
    parser.add_argument('--output-dir', type=Path, help='write proposed ESFM books here instead of replacing source books')
    parser.add_argument('--report', type=Path, help='write coverage and proposed positional/lexical links as JSON (single process)')
    BibleOrgSysGlobals.addStandardOptionsAndProcess( parser, exportAvailable=False )

    options = BibleOrgSysGlobals.commandLineArguments
    if options.books:
        invalid = set(options.books) - {p.stem.removeprefix('OET-LV_') for folder in (OET_LV_OT_ESFM_InputFolderPath, OET_LV_NT_ESFM_InputFolderPath) for p in folder.glob('OET-LV_*.ESFM')}
        if invalid: parser.error(f'Unknown book code(s): {", ".join(sorted(invalid))}')
    if options.output_dir and options.output_dir.resolve() == OET_RV_ESFM_FolderPath.resolve():
        parser.error('--output-dir must differ from the source folder')
    main()

    BibleOrgSysGlobals.closedown( PROGRAM_NAME, PROGRAM_VERSION )
# end of connect_OET-RV_words_via_OET-LV.py
