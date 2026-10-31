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
All matching rules feed one candidate-selection engine in oet_candidates.py.
    Lexical, proper-name, number-change and phrase evidence compete in the
    positional alignment graph. Unique lexical recovery, traditional aliases
    and explicit repeats propose candidates without writing any ESFM.
    Conflicting equally supported candidates abstain. Newly selected content
    anchors constrain function-word recovery; compatible joint alignments and
    atomic phrase bundles stay together. Refine to convergence, then write once at
    original occurrence offsets. Existing links remain immutable anchors.
    Shared spelling prefixes are not evidence. Rebuild tests must start without
    numbers as well as with existing links: historical anchors can hide gaps.
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
            can be identified earlier in the same mapped passage,
                each repeated word inherits its original occurrence’s number.
        Repeats outside that mapped passage are not linked automatically.
    Reworded '\\add ≈' or '\\+add ≈' or '\\add ?≈' or '\\+add ?≈' spans:
        Can be matched to OET-LV words, but more difficult expected.
    Alternate '\\add !' or '\\+add !' or '\\add ?!' or '\\+add ?!' name spans:
        Because an English Bible translation is using a mixture of Hebrew, Greek, and English names,
            we often want to display more than one form of the name to the reader.
        The OET-RV mostly puts a rough Hebrew or Greek transliteration first,
            followed by the traditional name in parentheses,
            e.g., 'Shelomo (\\add !Solomon\\add*)'
        Both forms of the name should be linked to the OET-LV name by having the same word number.

Versification: Use the explicit BOS OET-RV and OET-LV source profiles.
    BOS maps complete RV passages before any word matching. Verse bridges stay
    together, chapter changes are followed, and Psalm titles use BOS declarations.
    Non-exact mappings and absent LV text are reported and left unlinked.
    Unused LV verses are audited too, exposing incomplete BOS split/merge data.
    All editing addresses and report chapter/verse fields use printed RV numbers.


CHANGELOG:
    2026-10-29 Include DC sources, independent word tables and conservative draft metadata.
    2026-10-31 Route LAO, PSS and ODE through the DC word table.
    2026-10-22 Use BOS source profiles for mapped metadata, passages and export/navigation.
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
    2026-10-13 Consolidate remaining direct-write matchers into oet_candidates.py;
        select names and phrases with context, resolve competing claims before
        writing, and remove obsolete table priorities and per-matcher counters.

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

from oet_alignment import (LVToken, UNLINKED_ADD_CODES, index_book_lines, tokenize,
                           with_clause_boundaries, unlinked_add_spans, is_word_fragment,
                           OPTIONAL_PLURAL)
from oet_candidates import select_links
from oet_versification import audit_unmapped_lv, resolve_alignment_passages
from oet_derived_word_tables import RELATED_WORD_GROUPS, CONTRACTION_SUBJECTS
from oet_noun_tables import SIMPLE_NOUN_PAIRS, SIMPLE_NOUNS_FLAT, verbalNouns
from oet_verb_tables import SIMPLE_VERB_SETS
from oet_word_tables import SIMPLE_WORDS, EQUIVALENT_LV_RV_WORDS, RV_SINGLE_WORDS_FROM_LV_WORDS
from oet_phrase_tables import RV_SINGLE_WORDS_FROM_LV_WORD_STRINGS, LV_SINGLE_WORDS_TO_RV_WORD_STRINGS

from BibleOrgSys import BibleOrgSysGlobals
from BibleOrgSys.BibleOrgSysGlobals import vPrint, fnPrint, dPrint
from BibleOrgSys.Formats.ESFMBible import ESFMBible
import bos_books_codes_py
from bible_transliterations import transliterate_Hebrew, transliterate_Greek


LAST_MODIFIED_DATE = '2026-10-31'
SHORT_PROGRAM_NAME = "connect_OET-RV_words_via_OET-LV"
PROGRAM_NAME = "Connect OET-RV words to OET-LV word numbers"
PROGRAM_VERSION = '2.0.0'
PROGRAM_NAME_VERSION = f'{SHORT_PROGRAM_NAME} v{PROGRAM_VERSION}'

DEBUGGING_THIS_MODULE = False


scripts_folderpath = Path(__file__).resolve().parents[1]
project_folderpath = scripts_folderpath.parent # Find folders relative to this module
# FG_folderpath = project_folderpath.parent # Path to find parallel Freely-Given.org repos
OET_LV_ESFM_InputFolderPath = project_folderpath.joinpath( 'derivedTexts/' )
OET_LV_OT_ESFM_InputFolderPath = OET_LV_ESFM_InputFolderPath.joinpath( 'auto_edited_OT_ESFM/' )
OET_LV_NT_ESFM_InputFolderPath = OET_LV_ESFM_InputFolderPath.joinpath( 'auto_edited_VLT_ESFM/' )
OET_LV_DC_ESFM_InputFolderPath = OET_LV_ESFM_InputFolderPath.joinpath( 'auto_edited_DC_ESFM/' )
OET_RV_ESFM_FolderPath = project_folderpath.joinpath( 'translatedTexts/ReadersVersion/' )
assert OET_LV_OT_ESFM_InputFolderPath.is_dir()
assert OET_LV_NT_ESFM_InputFolderPath.is_dir()
assert OET_RV_ESFM_FolderPath.is_dir()

OET_RV_NAMES_TABLE_FILEPATH = OET_RV_ESFM_FolderPath.joinpath( 'OET-RV_names_table.tsv' )
OET_RV_NAMES_TABLE_HEADER = 'TraditionalName\tGrkName\tRVName\tExplained\tComment'
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


class State:
    """
    A place to store some of the global stuff that needs to be passed around.
    """
    def __init__(self):
        self.bookLinkAdditions = 0 # Increment only after a successful insertion.
# end of State class

state = State()


def canonicalBookCode(book):
    """Keep OET filenames separate from BOS's canonical book identities."""
    return {'DAG': 'DNG', 'ES1': 'GES', 'ES2': 'LES'}.get(book, book)


def bookSegment(book):
    book = canonicalBookCode(book)
    if bos_books_codes_py.is_old_testament_nr(book):
        return 'OT'
    if bos_books_codes_py.is_new_testament_nr(book):
        return 'NT'
    # The BOS deuterocanon category does not include every OET extra book.
    if book in {'TOB', 'JDT', 'ESG', 'WIS', 'SIR', 'BAR', 'DNG', 'MA1', 'MA2',
                'MA3', 'MA4', 'GES', 'LES', 'MAN', 'PS2', 'PSS', 'ODE', 'LAO'}:
        return 'DC'
    raise ValueError(f'No word-table segment for {book}')


def alignmentSources():
    """DC is optional in older checkouts; its presence never changes OT/NT tables."""
    return (('OT', OET_LV_OT_ESFM_InputFolderPath),
            ('DC', OET_LV_DC_ESFM_InputFolderPath),
            ('NT', OET_LV_NT_ESFM_InputFolderPath))


def bookFilename(bible, book, abbreviation):
    """Use the loader's actual filename (e.g. GES is stored as OET-RV_ES1)."""
    return getattr(bible, 'possibleFilenameDict', {}).get(book, f'{abbreviation}_{book}.ESFM')


def loadAlignmentBible(folder, abbreviation, versification):
    """Avoid parsing every book when --books selects a subset."""
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

    rv = loadAlignmentBible(OET_RV_ESFM_FolderPath, 'OET-RV', 'OET-RV')
    sources = [(segment, folder, loadAlignmentBible(folder, 'OET-LV', 'OET-LV'))
               for segment, folder in alignmentSources() if folder.is_dir()]

    # Word numbers are independent row indices within each segment's table.
    state.wordTable, state.wordTableHeaderList = {}, {}
    for testament, input_folder_path, lv in sources:
        if not lv.books:
            continue
        BBB = next(iter(lv.books))
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
        if testament == 'DC':
            required = {'Ref', 'Morphology', 'GlossStatus', 'OETGlossWords'}
            if not required <= set(state.wordTableHeaderList[testament]):
                raise ValueError(f'DC word table is missing columns: {required - set(state.wordTableHeaderList[testament])}')

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
    totalWords = totalLinked = dcLinked = 0
    for testament, folder, lv in sources:
        vPrint('Quiet', DEBUGGING_THIS_MODULE, f'\nProcessing connect words for OET {testament}…')
        words, linked = connect_OET_RV(rv, lv, folder, testament)
        totalWords += words
        totalLinked += linked
        if testament == 'DC':
            dcLinked = linked # Returned counts also work with multiprocessing.

    # Selected-book runs report only the books actually processed.
    if not options.books:
        reportWordNumberPercentage('Whole Bible', totalWords, totalLinked)

    # Keep linked DC output self-contained, including output-directory previews.
    if not options.dry_run and dcLinked:
        destination = options.output_dir or OET_RV_ESFM_FolderPath
        table = 'OET-LV_DC_word_table.tsv'
        data = (OET_LV_DC_ESFM_InputFolderPath / table).read_bytes()
        target = destination / table
        if not target.exists() or target.read_bytes() != data:
            target.write_bytes(data)

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
        if len(fields) < 3: continue # Some editors delete trailing columns
        traditionalName, rvName = fields[0].strip(), fields[2].strip()
        explained = fields[3].strip() if len(fields) >= 4 else ''
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
        and the candidate engine lets those alternatives match the OET-RV word.)

    'LVWord' is the OET-LV word, spelled the way the OET-LV spells it, i.e. with an underscore
        between the parts of one word ('you_all'); a space works there too.
    'RVWords' is what the OET-RV actually uses, with a space between the words ('you all').
    Only the rows that the translator has flagged with an 'Enabled' of 'Y' are used, so that
        candidates can be listed in the table without being acted on yet (as with the names table).
    """
    state.rvWordPhrases = {} # (simplified LV words) -> (simplified RV words), e.g. ('you','all') -> ('you','all')
    if not OET_RV_WORD_PHRASES_TABLE_FILEPATH.is_file():
        logging.warning( f"Can't find the OET-RV word phrases table {OET_RV_WORD_PHRASES_TABLE_FILEPATH}, so only the maintained Python phrase tables will be used" )
        return
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 1:
        vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  Loading enabled OET-RV word phrases from {OET_RV_WORD_PHRASES_TABLE_FILEPATH}…" )
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
        so that getLVNameSpellings() can find it when it looks
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

    testament is 'OT', 'DC' or 'NT', and labels the word count summaries.

    Returns a (numWords,numWordNumbered) tuple for this testament, i.e. how many of the OET-RV
        words of the books that we processed could have a word number, and how many of them
        have one (see countWordsAndWordNumbers()), so that main() can add the segments
        together for a whole Bible figure.
    """
    assert testament in ('OT','DC','NT'), f"Bad {testament=}"
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag:
        fnPrint( DEBUGGING_THIS_MODULE, f"connect_OET_RV( {rv}, {lv} {testament} )" )

    # Make a list of the books that we're going to process
    booklist_to_process = []
    selected = BibleOrgSysGlobals.commandLineArguments.books
    for BBB in lv.books:
        if selected and BBB not in selected:
            continue
        if rv is not None and BBB not in rv.books:
            logging.warning(f'Skipping OET-LV {BBB}: no corresponding RV book')
            continue
        # if BBB in ('CO1',): continue # TODO: CO1_14:33 gives an issue
        booklist_to_process.append( BBB )
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 2:
        vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Created a list of {len(booklist_to_process)} OET books to process." )

    totalAdds = totalNS = totalNumWords = totalNumWordNumbered = 0

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
        bookAdds, bookNS, bookNumWords, bookNumWordNumbered, bookNumPasses = result
        bookPassCounts[BBB] = bookNumPasses
        totalAdds += bookAdds
        totalNS += bookNS
        totalNumWords += bookNumWords
        totalNumWordNumbered += bookNumWordNumbered

    vPrint('Normal', DEBUGGING_THIS_MODULE,
           f"  {testament} candidate selection added {totalAdds:,} word links ({totalNS:,} new nomina sacra).")
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
    Adapt the four book arguments to Pool.map's single-argument interface.

    Each worker owns its live RV lines and writes only its assigned book.
    Pass totals return to the parent; detailed JSON reporting uses one process.
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
    Return insertion/nomina-sacra totals, coverage, and complete book passes
    (including the last pass with no additions).
    """
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag:
        fnPrint( DEBUGGING_THIS_MODULE, f"connect_OET_RV_book( {BBB} )" )
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 2:
        vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Processing connect words for OET {BBB}…" )

    # wordFileName = lv[BBB].ESFMWordTableFilename

    bookAdds = bookNS = 0

    lvESFMFilename = bookFilename(lv, BBB, 'OET-LV')
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

    rvESFMFilename = bookFilename(rv, BBB, 'OET-RV')
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
            added, ns = connect_OET_RV_Verse(BBB, c, v, rvVerseEntryList, lvVerseEntryList)
            bookAdds += added
            bookNS += ns
        addedThisPass = state.bookLinkAdditions - beforePass
        passLinkAdditions.append(addedThisPass)
        vPrint( 'Normal' if addedThisPass else 'Info', DEBUGGING_THIS_MODULE,
               f"    {BBB} pass {len(passLinkAdditions)} added {addedThisPass:,} word links."
               + (" Reprocessing…" if addedThisPass else " Finished."))
        if not addedThisPass:
            break

    newESFMtext = '\n'.join( state.rvESFMLines ) \
                        .replace( '\\nd* \\nd ', ' ' ) # Concatenate consecutive nd fields
    if bookSegment(BBB) == 'DC' and (bookAdds or beforeLinked):
        declaration = r'\rem WORDTABLE OET-LV_DC_word_table.tsv'
        if re.search(r'^\\rem (?:not )?WORDTABLE .*$', newESFMtext, re.MULTILINE):
            newESFMtext = re.sub(r'^\\rem (?:not )?WORDTABLE .*$', lambda m: declaration,
                                newESFMtext, flags=re.MULTILINE)
        else:
            first, separator, rest = newESFMtext.partition('\n')
            newESFMtext = first + '\n' + declaration + separator + rest
            for item in getattr(state, 'audit', ()):
                if item['book'] == BBB:
                    item['line'] += 1 # The new header precedes every verse.
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
        vPrint('Normal', DEBUGGING_THIS_MODULE,
               f"    Candidate selection added {bookAdds:,} word links ({bookNS:,} new nomina sacra) for {BBB}.")
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
    state.bookReports.append(dict(book=BBB, segment=bookSegment(BBB), filename=rvESFMFilename,
                                  words=bookNumWords, before=beforeLinked,
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

    return bookAdds, bookNS, bookNumWords, bookNumWordNumbered, len(passLinkAdditions)
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
                            (gap['lv_reference'] for gap in state.unmappedLV[:20]))
        if len(state.unmappedLV) > 20:
            missing += f', … ({len(state.unmappedLV):,} total)'
        vPrint('Normal', DEBUGGING_THIS_MODULE,
               f'    WARNING: OET-LV {BBB} {missing} not represented in the RV mappings; '
               'check BOS mapping data / RV verse coverage (see unmapped_lv in --report).')
    for issue in skipped[:20]:
        refs = ', '.join(f'{b} {c}:{v}{suffix or ""}' for b,c,v,suffix in issue['rv_references'])
        diagnostics = issue.get('mapping', {}).get('diagnostics', ())
        reason = '; '.join(dict.fromkeys(d['message'] for d in diagnostics)) or issue.get('message', issue['status'])
        logging.warning(f'Skipping OET-RV {refs}: {issue["status"]}: {reason}')
    if len(skipped) > 20:
        logging.warning(f'OET-RV {BBB}: {len(skipped):,} passages skipped; first 20 shown. Full details are retained in --report.')
    if bookSegment(BBB) == 'DC' and not passages:
        vPrint('Normal', DEBUGGING_THIS_MODULE,
               f'    {BBB}: no exact OET-RV → OET-LV passage mappings; no DC word connections made.')
    vPrint('Info', DEBUGGING_THIS_MODULE,
           f'    {BBB}: resolved {len(passages):,} RV passages (OET-RV → OET-LV); skipped {len(skipped):,}.')
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


def connect_OET_RV_Verse(BBB:str, c:int, v:int, rvEntryList, lvEntryList) -> Tuple[int,int]:
    """Build the mapped LV passage and select all links before editing the RV.

    BOS supplies LV entries in original versification for this English RV
    passage. Live RV lines retain add markers and occurrence offsets, unlike
    parsed clean text. Return inserted word-link and nomina-sacra counts.
    """
    lvText = ' '.join(entry.getCleanText().replace('+', '') for entry in lvEntryList
                      if entry.getMarker() in ('v~', 'd'))
    rvText = getLiveRVVerseText(BBB, c, v)
    if not rvText or not lvText:
        return 0, 0
    lvWords = [word for word in normaliseLVVerseText(lvText).split()
               if not word.startswith('DOM¦')]
    if not lvWords:
        return 0, 0
    return matchVerseCandidates(BBB, c, v, lvWords,
                                rvText.lstrip().startswith(ORDER_REVERSAL_CHARACTER), lvText)


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
    word = OPTIONAL_PLURAL.sub(r'\1', word) # RV optional plurals: daughter(s), box(es).
    word = unicodedata.normalize( 'NFD', word )
    word = ''.join( ch for ch in word if unicodedata.category( ch ) not in ('Mn', 'Lm') ) # Strip combining marks and modifier letters
    word = re.sub( r"[ʼˊʹʺʸˈ]", '', word ) # Transliteration accents
    word = re.sub( r"/.*$", '', word ) # Strip parenthetical alternatives like /(Miryām)
    word = word.removesuffix("'") # Plural possessives and names ending in s.
    word = re.sub( r"[’']s$", '', word ) # Singular possessives
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
        if OPTIONAL_PLURAL.search(rvWord):
            return 'optional plural', 95 # Do not prefer plural over its curated singular form.
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
    rvWord = rvWord.removesuffix("'")
    lexical = scoreRVLVWords(rvWord, lvWord)
    if lexical and lexical[1] >= 55:
        return lexical
    rvWord = OPTIONAL_PLURAL.sub(r'\1', rvWord)
    if lvWord.casefold() in DIRECTIONAL_WORD_INDEX.get(rvWord.casefold(), ()):
        return 'directional word mapping', 55
    if CONTRACTION_SUBJECTS.get(rvWord.casefold().replace('’', "'")) == lvWord.casefold():
        return 'contraction subject', 55
    return lexical


def getLVWordNumber( lvWordStr:str ) -> Optional[int]:
    """
    Pull the OET-LV word number out of a word like 'wineskins¦23221'.

    We only take the leading run of digits, because the OET-LV sometimes has a gloss helper
        marker stuck to the number (e.g. 'will¦23935˒'), which would otherwise stop int().
    """
    m = re.match( r'^.*?¦(\d+)', lvWordStr )
    return int(m.group(1)) if m else None
# end of getLVWordNumber


def matchVerseCandidates( BBB:str, c:int,v:int, lvWordList:List[str], reversedOrder:bool, lvVerseText:Optional[str]=None ) -> Tuple[int,int]:
    """Adapt BOS metadata to the pure selector, then write accepted occurrences.

    Alternatives share one alignment column. Existing links bound local gaps in
    LV text order. Gap matches require agreement across optimal alignments;
    short phrase movements require strong, unambiguous lexical matches across
    a nearby linked block. Original LV punctuation fences the latter operation.
    """
    testament = bookSegment(BBB)
    columns = []
    for word in lvWordList:
        number = getLVWordNumber(word)
        if number is None:
            continue
        plain = word.split('¦', 1)[0]
        row = state.wordTable[testament][number]
        if testament == 'DC':
            header = state.wordTableHeaderList['DC']
            if canonicalBookCode(row[header.index('Ref')].split('_', 1)[0]) != canonicalBookCode(BBB):
                raise ValueError(f'DC word {number} does not belong to {BBB}')
            if row[header.index('GlossStatus')] in {'missing', 'ambiguous', 'unusable-gloss'} \
                    or not row[header.index('OETGlossWords')]:
                # Retain its position as an unmatchable column; omitting it
                # would join words that are not adjacent in the source text.
                columns.append(LVToken(f'⟦DC:{number}⟧', number))
                continue
        # Hebrew transliterations can start with a modifier letter (ʼAhₐron,
        # ˊĒsāv). Inspect their first ordinary letter, not character zero.
        capitalised = any(next((ch for ch in w if ch.isalpha() and unicodedata.category(ch) != 'Lm'), '').isupper()
                          for w in plain.split('/'))
        proper = capitalised and lvWordIsProperNoun(row, testament)
        # Name-table evidence also covers NT nouns with U but no W, and OT
        # gentilics (Ng), e.g. Lēviyyiy/Levites. Metadata-only '*' substitutions
        # retain the stricter proper-noun test; tables justify these spellings.
        nameEligible = capitalised and lvWordIsNoun(row, testament)
        names = (frozenset(getLVNameSpellings(plain, ('NT','NT_OT') if testament in ('NT','DC') else ('OT',)))
                 if nameEligible and hasattr(state, 'nameTables') else frozenset())
        columns.append(LVToken(plain, number, proper, noun=lvWordIsNoun(row, testament), names=names))
    if lvVerseText is not None:
        columns = with_clause_boundaries(columns, lvVerseText)
    # Optional project-specific phrases enter the same candidate graph as the
    # maintained phrase tables, with no separate first-writer priority.
    phraseIndex = ALIGNED_PHRASE_INDEX
    if getattr(state, 'rvWordPhrases', None):
        phraseIndex = {word: list(rows) for word, rows in ALIGNED_PHRASE_INDEX.items()}
        for lvPhrase, rvPhrase in state.rvWordPhrases.items():
            rvPhrase, lvPhrase = tuple(rvPhrase), tuple(lvPhrase)
            phraseIndex.setdefault(rvPhrase[0], []).append((rvPhrase, lvPhrase))
    proposals = select_links(getLiveRVTokens(BBB, c, v), columns,
                             scoreAlignedWords, simplifyRVLVWord, numberVariants,
                             reversedOrder, phraseIndex, DIRECTIONAL_WORD_INDEX)
    added = ns = 0
    for token, number, reason in sorted(proposals, key=lambda p: (p[0].line, p[0].start), reverse=True):
        result, resultNS = applyRVTokenLink(BBB, c, v, token, number, reason)
        added += result
        ns += resultNS
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
        does no harm: number-change evidence only uses a form that is a noun of that
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
        OET-LV 'strap', so number-change evidence only connects those.
    The NT word table has a 'Role' column that says 'N' for a noun, but the OT word table
        describes its nouns in the 'Morphology' column instead, e.g. 'Ncfsa' for a common
        feminine singular noun (and 'Td' for the definite article, 'C,' for a conjunction, etc.).
    """
    if testament == 'NT':
        return lvWordRow[state.wordTableHeaderList['NT'].index('Role')].strip() in ('N','S')
    if testament == 'DC':
        morphology = lvWordRow[state.wordTableHeaderList['DC'].index('Morphology')]
        # TAGNT candidates use a different scheme from both OT and NT tables.
        # Only unanimous noun analyses justify number-change/name evidence.
        return bool(morphology) and all(part.strip().startswith('N-') for part in morphology.split('|'))
    morphology = lvWordRow[state.wordTableHeaderList['OT'].index('Morphology')]
    return any( part.startswith( 'N' ) for part in morphology.split( ',' ) ) # e.g. 'R,Ncfsa' is a preposition with a noun
# end of lvWordIsNoun


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
    if testament == 'DC':
        return False # Draft metadata has no contextual proper-name classification.
    morphology = lvWordRow[state.wordTableHeaderList['OT'].index('Morphology')]
    return any(part.startswith('Np') for part in morphology.split(','))
# end of connect_OET-RV_words_via_OET-LV.lvWordIsProperNoun


lvAltNameRegex = re.compile(r'[/(]')


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


DIRECTIONAL_WORD_INDEX = defaultdict(set)
for _rvWord, _lvWord in RV_SINGLE_WORDS_FROM_LV_WORDS:
    DIRECTIONAL_WORD_INDEX[_rvWord.casefold()].add(_lvWord.casefold())
ALIGNED_PHRASE_INDEX = defaultdict(list)
for _rvPhrase, _lvPhrase in (
        *((rv, lv) for rv, lv in RV_SINGLE_WORDS_FROM_LV_WORD_STRINGS),
        *((rv, lv) for lv, rv in LV_SINGLE_WORDS_TO_RV_WORD_STRINGS)):
    _rvWords, _lvWords = tuple(_rvPhrase.casefold().split()), tuple(_lvPhrase.casefold().split())
    ALIGNED_PHRASE_INDEX[_rvWords[0]].append((_rvWords, _lvWords))


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
#   the positional tokenizer sees when it matches RV against LV
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
    if (line[token.start:token.end] != token.text or line[token.end:token.end+1] == '¦'
            or is_word_fragment(line, token.start, token.end)):
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


if __name__ == '__main__':
    multiprocessing.set_start_method('fork') # The default was changed on POSIX systems from 'fork' to 'forkserver' in Python3.14
    multiprocessing.freeze_support() # Multiprocessing support for frozen Windows executables

    # Configure basic Bible Organisational System (BOS) set-up
    parser = BibleOrgSysGlobals.setup( PROGRAM_NAME, PROGRAM_VERSION )
    parser.add_argument('--books', nargs='+', metavar='BBB', help='process only these OT/DC/NT codes (e.g. RUT TOB MRK; DAG/ES1/ES2 filename aliases are accepted)')
    parser.add_argument('--dry-run', action='store_true', help='compute links and coverage without writing ESFM files')
    parser.add_argument('--output-dir', type=Path, help='write proposed ESFM books here instead of replacing source books')
    parser.add_argument('--report', type=Path, help='write coverage and proposed positional/lexical links as JSON (single process)')
    BibleOrgSysGlobals.addStandardOptionsAndProcess( parser, exportAvailable=False )

    options = BibleOrgSysGlobals.commandLineArguments
    if options.books:
        options.books = list(dict.fromkeys(canonicalBookCode(book) for book in options.books))
        available = {canonicalBookCode(p.stem.removeprefix('OET-LV_'))
                     for _, folder in alignmentSources() for p in folder.glob('OET-LV_*.ESFM')}
        invalid = set(options.books) - available
        if invalid: parser.error(f'No OET-LV source file for book code(s): {", ".join(sorted(invalid))}')
    if options.output_dir and options.output_dir.resolve() == OET_RV_ESFM_FolderPath.resolve():
        parser.error('--output-dir must differ from the source folder')
    main()

    BibleOrgSysGlobals.closedown( PROGRAM_NAME, PROGRAM_VERSION )
# end of connect_OET-RV_words_via_OET-LV.py
