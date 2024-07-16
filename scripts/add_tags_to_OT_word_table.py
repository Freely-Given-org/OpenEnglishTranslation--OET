#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# add_tags_to_OT_word_table.py
#
# Script handling add_tags_to_OT_word_table functions
#
# Copyright (C) 2023-2024 Robert Hunt
# Author: Robert Hunt <Freely.Given.org+BOS@gmail.com>
# License: See gpl-3.0.txt
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Adds an extra 'Tags' column to the wordTable used by the OET Old Testament.
This contains tags (separated by ';') including:
    Pname       Person name
    Lname       Location name
    Yyear       Year (digits, can be negative = BC)
    Eevent      Event
    Ttimeline   Timeline entry
    Rreferent   Pronoun referent(s)

We currently take the person, location, year, event, and timeline tags
    from our normalised version of the Theographic Bible Data
    (see https://github.com/Freely-Given-org/Bible_speaker_identification/tree/main/outsideSources/TheographicBibleData).

We determine pronoun referents from the Clear.Bible "lowfat" xml files
    (see https://github.com/Freely-Given-org/macula-greek/tree/main/Nestle1904/lowfat
        which is based on the 1904 Nestle Hebrew New Testament)
    but which we have preprocessed into easier-to-use TSV files
        using https://github.com/Freely-Given-org/OpenEnglishTranslation--OET/blob/main/scripts/convert_ClearMaculaNT_to_TSV.py.

We use this information to update our OET word-table
    that was created by extract_glossed_OSHB_OT_to_ESFM.py

CHANGELOG:
"""
from gettext import gettext as _
from typing import Dict, List, Tuple, NamedTuple, Optional
from pathlib import Path
import json
import tomllib
import logging
import shutil
import os
import unicodedata
import re

import BibleOrgSysGlobals
from BibleOrgSysGlobals import fnPrint, vPrint, dPrint

import sys
sys.path.insert( 0, '../../BibleTransliterations/Python/' ) # temp until submitted to PyPI
from BibleTransliterations import load_transliteration_table, transliterate_Hebrew #, transliterate_Greek

LAST_MODIFIED_DATE = '2024-07-02' # by RJH
SHORT_PROGRAM_NAME = "Add_wordtable_people_places_referrents"
PROGRAM_NAME = "Add People&Places tags to OET OT wordtable"
PROGRAM_VERSION = '0.13'
PROGRAM_NAME_VERSION = f'{SHORT_PROGRAM_NAME} v{PROGRAM_VERSION}'

DEBUGGING_THIS_MODULE = False


SCRIPTED_UPDATES_TABLES_INPUT_FOLDERPATH = Path( 'ScriptedOTUpdates/' ) # The control files folder for Scripted Bible Editor

JSON_VERSES_DB_INPUT_FILEPATH = Path( '../../Bible_speaker_identification/outsideSources/TheographicBibleData/derivedFiles/normalised_Verses.json' ) # In
MACULA_HEBREW_TSV_INPUT_FILEPATH = Path( '../intermediateTexts/Clear.Bible_lowfat_trees/ClearLowFatTrees.OT.morphemes.abbrev.tsv' ) # In

LEMMA_TABLE_INPUT_FILEPATH = Path( '../intermediateTexts/glossed_OSHB/all_glosses.lemmas.tsv' ) # In
MORPHEME_TABLE_INPUT_FILEPATH = Path( '../intermediateTexts/glossed_OSHB/all_glosses.morphemes.tsv' ) # In
WORD_TABLE_INPUT_FILEPATH = Path( '../intermediateTexts/glossed_OSHB/all_glosses.words.tsv' ) # In
WORD_TABLE_OUTPUT_FILENAME = 'OET-LV_OT_word_table.tsv' # Out
WORD_TABLE_OUTPUT_FOLDERPATH = Path( '../intermediateTexts/modified_source_glossed_OSHB_ESFM/' ) # Out
WORD_TABLE_OUTPUT_FILEPATH = WORD_TABLE_OUTPUT_FOLDERPATH.joinpath( WORD_TABLE_OUTPUT_FILENAME ) # Out
RV_ESFM_OUTPUT_FOLDERPATH = Path( '../translatedTexts/ReadersVersion/' ) # Out (we copy the outputted wordfile to this folder)

TAB = '\t'


state = None
class State:
    def __init__( self ) -> None:
        """
        Constructor:
        """
        newWordTable = None
    # end of add_tags_to_OT_word_table.__init__


def main() -> None:
    """
    """
    BibleOrgSysGlobals.introduceProgram( __name__, PROGRAM_NAME_VERSION, LAST_MODIFIED_DATE )
    global state
    state = State()

    # Read the existing lemma table
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"Reading existing lemma table entries from {LEMMA_TABLE_INPUT_FILEPATH}…" )
    with open( LEMMA_TABLE_INPUT_FILEPATH, 'rt', encoding='utf-8' ) as old_table_file:
        file_data = old_table_file.read()
        if file_data.startswith( '\ufeff' ): # remove any BOM
            vPrint( 'Quiet', DEBUGGING_THIS_MODULE, "  Handling Byte Order Marker (BOM) at start of source lemma table tsv file…" )
            file_data = file_data[1:]
        state.lemmaTable = file_data.rstrip( '\n' ).split( '\n' )
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Loaded {len(state.lemmaTable):,} existing lemma table entries ({state.lemmaTable[0].count(TAB)+1} columns)." )

    # Read the existing morpheme table
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"Reading existing morpheme table entries from {MORPHEME_TABLE_INPUT_FILEPATH}…" )
    with open( MORPHEME_TABLE_INPUT_FILEPATH, 'rt', encoding='utf-8' ) as old_table_file:
        file_data = old_table_file.read()
        if file_data.startswith( '\ufeff' ): # remove any BOM
            vPrint( 'Quiet', DEBUGGING_THIS_MODULE, "  Handling Byte Order Marker (BOM) at start of source morpheme table tsv file…" )
            file_data = file_data[1:]
        state.morphemeTable = file_data.rstrip( '\n' ).split( '\n' )
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Loaded {len(state.morphemeTable):,} existing morpheme table entries ({state.morphemeTable[0].count(TAB)+1} columns)." )

    # Read our old word table
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"Reading existing word table entries from {WORD_TABLE_INPUT_FILEPATH}…" )
    with open( WORD_TABLE_INPUT_FILEPATH, 'rt', encoding='utf-8' ) as old_table_file:
        file_data = old_table_file.read()
        if file_data.startswith( '\ufeff' ): # remove any BOM
            vPrint( 'Quiet', DEBUGGING_THIS_MODULE, "  Handling Byte Order Marker (BOM) at start of source word table tsv file…" )
            file_data = file_data[1:]
        state.oldWordTable = file_data.rstrip( '\n' ).split( '\n' )
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Loaded {len(state.oldWordTable):,} old word table entries ({state.oldWordTable[0].count(TAB)+1} columns)." )

    expand_table_columns() # Creates state.newWordTable from state.oldWordTable

    if not DEBUGGING_THIS_MODULE: apply_OT_scripted_gloss_updates()

    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"Reading Theographic Bible Data json entries from {JSON_VERSES_DB_INPUT_FILEPATH}…" )
    with open( JSON_VERSES_DB_INPUT_FILEPATH, 'rt', encoding='utf-8' ) as json_file:
        state.verseIndex = json.load( json_file )
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Loaded {len(state.verseIndex):,} json verse entries." )

    associate_Theographic_people_places()

    tag_trinity_persons()

    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"\nReading Hebrew Macula tsv entries from {MACULA_HEBREW_TSV_INPUT_FILEPATH}…" )
    with open( MACULA_HEBREW_TSV_INPUT_FILEPATH, 'rt', encoding='utf-8' ) as macula_tsv_file:
        macula_tsv_lines = macula_tsv_file.readlines()
    if macula_tsv_lines[0].startswith( '\ufeff' ): # remove any BOM
        vPrint( 'Quiet', DEBUGGING_THIS_MODULE, "  Handling Byte Order Marker (BOM) at start of source tsv file…" )
        macula_tsv_lines[0] = macula_tsv_lines[0][1:]
    # Get the headers before we start
    column_line_string = macula_tsv_lines[0].rstrip( '\n' )
    # print( f"{column_line_string=}")
    assert column_line_string == 'FGRef\tOSHBid\tRowType\tWordOrMorpheme\tAfter\tCompound\tWordClass\tPartOfSpeech\tPerson\tGender\tNumber\tWordType\tState\tRole\tStrongNumberX\tStrongLemma\tStem\tMorphology\tLemma\tSenseNumber\tSubjRef\tParticipantRef\tFrame\tGreek\tGreekStrong\tEnglishGloss\tContextualGloss\tNesting', f'{column_line_string=}' # otherwise we probably need to change some code
    state.macula_tsv_lines = []
    for macula_line in macula_tsv_lines:
        state.macula_tsv_lines.append( macula_line.rstrip( '\n' ).split( '\t' ) )
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Loaded {len(state.macula_tsv_lines):,} Hebrew Macula table entries ({column_line_string.count(TAB)+1} columns)." )

    # tag_referents_from_macula_data() # No 'referents' data in Macula Hebrew yet

    fill_extra_columns_and_remove_some() # Role and Nesting
    write_new_table()
# end of add_tags_to_OT_word_table.main


def expand_table_columns() -> bool:
    """
    Using state.oldWordTable, add the following empty columns and save in state.newWordTable:
        LemmaRowList
        Role
        Nesting
        Tags
    """
    assert len(state.oldWordTable) < 382_000, f"{len(state.oldWordTable)=}"
    columnHeaders = state.oldWordTable[0]
    dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  Old word table column headers = '{columnHeaders!r}'" )
    assert columnHeaders == 'Ref\tOSHBid\tRowType\tMorphemeRowList\tStrongs\tCantillationHierarchy\tMorphology\tWord\tNoCantillations\tMorphemeGlosses\tContextualMorphemeGlosses\tWordGloss\tContextualWordGloss\tGlossCapitalisation\tGlossPunctuation\tGlossOrder\tGlossInsert' # If not, probably need to fix some stuff

    # We'll insert a LemmaRowList column and at the end, append Role, Nesting, and Tags columns
    state.newWordTable = [ f"{columnHeaders.replace(f'{TAB}MorphemeRowList{TAB}',f'{TAB}MorphemeRowList{TAB}LemmaRowList{TAB}')}{TAB}Role{TAB}Nesting{TAB}Tags" ]
    assert state.newWordTable[0].count( '\t' ) == 20, f"{state.newWordTable[0].count(TAB)} {state.newWordTable[0]=}"
    for _n, columns_string in enumerate( state.oldWordTable[1:], start=1 ):
        oldColumns = columns_string.split( '\t' )
        assert len(oldColumns) == 17
        newColumns:List[str] = oldColumns.copy()
        # assert columnHeaders.split('\t')[5] == 'CantillationHierarchy' # If not, probably need to fix some stuff
        # assert columnHeaders.split('\t')[1] == 'OSHBid' # If not, probably need to fix some stuff
        # del newColumns[5] # Remove CantillationHierarchy
        # del newColumns[1] # Remove OSHBid
        newColumns.insert( 4, '' ) # Insert empty LemmaRowList column
        newColumns.append(''); newColumns.append(''); newColumns.append('') # Append new final three columns
        # print( f"({len(newColumns)}) {newColumns=}" )
        assert len(newColumns) == 21, len(newColumns)
        newLine = '\t'.join( newColumns )
        assert newLine.count( '\t' ) == 20, f"{newLine.count(TAB)} {newLine=}"
        state.newWordTable.append( newLine )
        
    assert 381_000 < len(state.newWordTable) < 382_000, f"{len(state.newWordTable)=}"
    return True
# end of add_tags_to_OT_word_table.expand_table_columns


COMMAND_TABLE_NUM_COLUMNS = 15
COMMAND_HEADER_LINE = 'Tags	IBooks	EBooks	IMarkers	EMarkers	IRefs	ERefs	PreText	SCase	Search	PostText	RCase	Replace	Name	Comment'
assert ' ' not in COMMAND_HEADER_LINE
assert COMMAND_HEADER_LINE.count( '\t' ) == COMMAND_TABLE_NUM_COLUMNS - 1
class EditCommand(NamedTuple):
    tags: str           # 0
    iBooks: list        # 1
    eBooks: list        # 2
    iMarkers: list      # 3
    eMarkers: list      # 4
    iRefs: list         # 5
    eRefs: list         # 6
    preText: str        # 7
    sCase: str          # 8
    searchText: str     # 9
    postText: str       # 10
    rCase: str          # 11
    replaceText: str    # 12
    name: str           # 13
    comment: str        # 14
def apply_OT_scripted_gloss_updates() -> bool:
    """
    Go through the .tsv files used by Scripted Bible Editor
        and apply them to the WordGloss column in state.newWordTable
    """
    assert 381_000 < len(state.newWordTable) < 382_000, f"{len(state.newWordTable)=}"

    # 0    1       2        3                4             5        6                      7           8     9                10               11                         12         13                   14                   15                16          17          18     19       20
    # Ref\tOSHBid\tRowType\tMorphemeRowList\tLemmaRowList\tStrongs\tCantillationHierarchy\tMorphology\tWord\tNoCantillations\tMorphemeGlosses\tContextualMorphemeGlosses\tWordGloss\tContextualWordGloss\tGlossCapitalisation\tGlossPunctuation\tGlossOrder\tGlossInsert\tRole\tNesting\tTags
    columnHeaders = state.newWordTable[0].split( '\t' )
    assert columnHeaders[0] == 'Ref' # If not, probably need to fix some stuff below
    assert columnHeaders[2] == 'RowType' # If not, probably need to fix some stuff below
    # assert columnHeaders[10] == 'MorphemeGlosses' # If not, probably need to fix some stuff below
    # assert columnHeaders[11] == 'ContextualMorphemeGlosses' # If not, probably need to fix some stuff below
    assert columnHeaders[12] == 'WordGloss' # If not, probably need to fix some stuff below
    # assert columnHeaders[13] == 'ContextualWordGloss' # If not, probably need to fix some stuff below

    # Firstly we read the TOML control file
    filepath = SCRIPTED_UPDATES_TABLES_INPUT_FOLDERPATH.joinpath( 'ScriptedBibleEditor.control.toml' )
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"Loading control file: {filepath}…" )
    with open( filepath, 'rb' ) as controlFile:
        controlData = tomllib.load( controlFile )

    load_transliteration_table( 'Hebrew' )

    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Loading and applying transforms to {columnHeaders[12]} column…" )
    totalChangedGlosses = 0
    commandTables = {}
    for commandTableName, givenFilepath in controlData['commandTables'].items():
        if 0 and commandTableName in ('fixGlossPre','fixGlossHelpers','fixGlossPost','cleanupVLT','finalFixes'): # These ones aren't relevant
            vPrint( 'Info', DEBUGGING_THIS_MODULE, f" Completely ignoring command table file: {commandTableName}" )
            continue
        completeFilepath = SCRIPTED_UPDATES_TABLES_INPUT_FOLDERPATH.joinpath( givenFilepath )
        if os.path.isfile(completeFilepath):
            vPrint( 'Info', DEBUGGING_THIS_MODULE, f"  Loading command table file: {completeFilepath}…" )
            assert commandTableName not in commandTables
            commandTables[commandTableName] = []
            with open( completeFilepath, 'rt', encoding='utf-8' ) as commandTableFile:
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
                    iBooks, eBooks = fields[1].split(',') if fields[1] else [], fields[2].split(',') if fields[2] else []
                    iMarkers, eMarkers = fields[3].split(',') if fields[3] else [], fields[4].split(',') if fields[4] else []
                    iRefs, eRefs = fields[5].split(',') if fields[5] else [], fields[6].split(',') if fields[6] else []
                    for iBook in iBooks:
                        assert iBook in BibleOrgSysGlobals.loadedBibleBooksCodes, iBook
                    for eBook in eBooks:
                        assert eBook in BibleOrgSysGlobals.loadedBibleBooksCodes, eBook
                    for iRef in iRefs:
                        assert iRef.count('_')==1 and iRef.count(':')==1, iRef
                        iRefBits = iRef.split('_')
                        assert iRefBits[0] in BibleOrgSysGlobals.loadedBibleBooksCodes, iRef
                        iRefC, iRefV = iRefBits[1].split(':')
                        assert iRefC[0].isdigit() and iRefV[0].isdigit(), iRef
                    for eRef in eRefs:
                        assert eRef.count('_')==1 and eRef.count(':')==1, eRef
                        eRefBits = eRef.split('_')
                        assert eRefBits[0] in BibleOrgSysGlobals.loadedBibleBooksCodes, eRef
                        eRefC, eRefV = eRefBits[1].split(':')
                        assert eRefC[0].isdigit() and eRefV[0].isdigit(), eRef
                    # print( f"From '{name}' ({givenFilepath}) have {searchText=} {replaceText=} {tags=}" )

                    # Adjust and save the fields
                    if 'H' in tags:
                        newReplaceText = transliterate_Hebrew( replaceText, capitaliseHebrew=searchText[0].isupper() )
                        if newReplaceText != replaceText:
                            # print(f" Converted Hebrew '{replaceText}' to '{newReplaceText}'")
                            replaceText = newReplaceText
                        # for char in replaceText:
                        #     if 'HEBREW' in unicodedata.name(char):
                        #         logging.critical(f"Have some Hebrew left-overs in '{replaceText}'")
                        #         break
                        tags = tags.replace( 'H', '' ) # Don't need this tag any longer
                    if 'G' in tags:
                        Oh_we_need_Greek
                        newReplaceText = transliterate_Greek( replaceText )
                        if newReplaceText != replaceText:
                            # print(f" Converted Hebrew '{replaceText}' to '{newReplaceText}'")
                            replaceText = newReplaceText
                        # for char in replaceText:
                        #     if 'GREEK' in unicodedata.name(char):
                        #         logging.critical(f"Have some Hebrew left-overs in '{replaceText}'")
                        #         break
                        tags = tags.replace( 'G', '' ) # Don't need this tag any longer

                    # Our glosses have no word numbers yet, so remove those markers
                    replaceText = replaceText.replace( '¦', '' )
                    searchText = searchText.replace( '¦', '' )
                    editCommand = EditCommand( tags,
                            iBooks, eBooks, iMarkers, eMarkers, iRefs, eRefs,
                            fields[7], fields[8], searchText, fields[10], fields[11],
                            replaceText, fields[13], fields[14] )
                    commandTables[commandTableName].append( editCommand )

                    # We only have the actual scripture words (no headers, headings, or cross-references, etc.) so
                    try: eMarkers.remove( 'id' )  # } No need for these because we don't have any of this stuff
                    except ValueError: pass # There wasn't one
                    try: eMarkers.remove( 'h' )  # } No need for these because we don't have any of this stuff
                    except ValueError: pass # There wasn't one
                    try: eMarkers.remove( 'toc1' )  # } No need for these because we don't have any of these
                    except ValueError: pass # There wasn't one
                    try: eMarkers.remove( 'toc2' )  # } No need for these because we don't have any of these
                    except ValueError: pass # There wasn't one
                    try: eMarkers.remove( 'toc3' )  # } No need for these because we don't have any of these
                    except ValueError: pass # There wasn't one
                    try: eMarkers.remove( 'mt1' )  # } No need for these because we don't have any of these
                    except ValueError: pass # There wasn't one
                    try: eMarkers.remove( 'rem' )  # } No need for these because we don't have any of this stuff
                    except ValueError: pass # There wasn't one
                    tags = tags.replace( 'd', '' ) # No use for 'distance' tag
                    tags = tags.replace( 'c', '' ) # Can't even remember what this tag is from finalFixes 'JtB's announcement'
                    
                    # We're going to do the changes to the entire word table right here!
                    vPrint( 'Info', DEBUGGING_THIS_MODULE, f"Applying {commandTableName}: {tags=} {iBooks=} {eBooks=} {iMarkers=} {eMarkers=} {iRefs=} {eRefs=} {editCommand.preText=} {editCommand.sCase=} {searchText=} {editCommand.postText=} {editCommand.rCase=} {replaceText=} {editCommand.name=} {editCommand.comment}" )
                    if iMarkers or eMarkers:
                        print( f"  Unable to apply '{commandTableName}' {iMarkers=} or {eMarkers=}" )
                        halt

                    if 'w' in tags: # whole words
                        myRegexSearchString = f'\\b{searchText}\\b'
                        compiledSearchRegex = re.compile( myRegexSearchString )

                    numChangedGlosses = 0
                    for n, columns_string in enumerate( state.newWordTable[1:], start=1 ):
                        columnDataList = columns_string.split( '\t' )
                        assert len(columnDataList) == 21
                        bcvwRef = columnDataList[0]
                        BBB, CV = bcvwRef.split( '_' )
                        if (iBooks and BBB not in iBooks) \
                        or BBB in eBooks:
                            vPrint( 'Info', DEBUGGING_THIS_MODULE, f"  Skipping {BBB} at {bcvwRef} with {iBooks=} {eBooks=}" )
                            continue
                        C, VW = CV.split( ':' )
                        try: V, W = VW.split( 'w' )
                        except ValueError:
                            # print( columnDataList)
                            assert columnDataList[2] in ('seg','note','variant note','alternative note','exegesis note')
                            continue
                        bcvRef = f'{BBB}_{C}:{V}'
                        if (iRefs and bcvRef not in iRefs) \
                        or bcvRef in eRefs:
                            if eRefs:
                                vPrint( 'Info', DEBUGGING_THIS_MODULE, f"  Skipping {bcvRef} at {bcvwRef} with {iRefs=} {eRefs=}" )
                            continue 
                        assert C.isdigit(), f"{C=}"
                        assert V.isdigit(), f"{V=}"
                        assert W.isdigit(), f"{W=}"
                        newGloss = oldGloss = columnDataList[12]

                        if not tags:
                            newGloss = newGloss.replace( searchText, replaceText )
                        elif tags == 'l': # loop
                            for _safetyCount in range( 10_000 ): # Prevent infinite loops
                                if searchText in newGloss:
                                    newGloss = newGloss.replace( searchText, replaceText )
                                else: break
                        elif tags == 'w': # whole words -- we use regex here
                            searchStartIndex = numReplacements = 0
                            while True:
                                # print( f"  Searching '{newGloss}' for {compiledSearchRegex.pattern=}")
                                match = compiledSearchRegex.search( newGloss, searchStartIndex )
                                if not match:
                                    break
                                # print( f"    {searchStartIndex}/{len(newGloss)} {numReplacements=} {match=}" )
                                # print( f"    guts='{newGloss[match.start()-10:match.end()+10]}'" )
                                newGloss = f'{newGloss[:match.start()]}{replaceText}{newGloss[match.end():]}'
                                # print( f"    {newGloss=}")
                                searchStartIndex = match.start() + len(replaceText)
                                numReplacements += 1
                        else:
                            vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  Ignored {commandTableName} '{editCommand.name}' {editCommand.comment} {tags=}" )
                            halt

                        if newGloss != oldGloss:
                            columnDataList[12] = newGloss
                            newLine = '\t'.join( columnDataList )
                            assert newLine.count( '\t' ) == 20, f"{newLine.count(TAB)} {newLine=}"
                            state.newWordTable[n] = newLine
                            numChangedGlosses += 1
                            totalChangedGlosses += 1
                    if numChangedGlosses:
                        vPrint( 'Info', DEBUGGING_THIS_MODULE, f"Made {numChangedGlosses:,} '{commandTableName}' OET gloss changes from scripted tables" )
                    
            vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"    Loaded and applied {len(commandTables[commandTableName])} command{'' if len(commandTables[commandTableName])==1 else 's'} for '{commandTableName}'." )
        else: vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"      '{completeFilepath}' is not a file!" )

    if totalChangedGlosses:
        vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"Made total {totalChangedGlosses:,} OET gloss changes from scripted tables" )

    assert 381_000 < len(state.newWordTable) < 382_000, f"{len(state.newWordTable)=}"
    return True
# end of add_tags_to_OT_word_table.apply_OT_scripted_gloss_updates


def associate_Theographic_people_places() -> bool:
    """
    Using the Theographic Bible Data, tag Hebrew word lines in our table
        with keys for people, places, etc.
    """
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, "\nAssociating Hebrew words with json keys…" )
    assert 381_000 < len(state.newWordTable) < 382_000, f"{len(state.newWordTable)=}"

    numAddedPeople = numAddedPeopleGroups = numAddedLocations = numAddedEvents = numAddedYears = numAddedTimelines = 0
    lastVerseRef = None
    for n, columns_string in enumerate( state.newWordTable[1:], start=1 ):
        wordRef, _OSHBid, rowType, _morphemeRowList, _lemmaRowList, _strongs, _cantillationHierarchy, _morphology, _word, noCantillations, morphemeGlosses, contextualMorphemeGlosses, wordGloss, contextualWordGloss, glossCaps, _glossPunctuation, _glossOrder, _glossInsert, _role, _nesting, _tags = columns_string.split( '\t' )
        if rowType in ('seg','note','variant note','alternative note','exegesis note'):
            assert columns_string.count( '\t' ) == 20, f"{columns_string.count(TAB)} {columns_string=}"
            # state.newWordTable.append( columns_string )
            lastVerseRef = verseRef
            continue
        tags:List[str] = []
        verseRef = wordRef.split('w')[0]
        newVerse = verseRef != lastVerseRef
        # print( f"{wordRef=} {verseRef} {lastVerseRef=} {newVerse=}" )
        try: verseLinkEntry = state.verseIndex[verseRef]
        except KeyError: # versification difference ???
            logging.critical( f"Versification error: Unable to find {verseRef} in Theographic json" )
            assert columns_string.count( '\t' ) == 20, f"{columns_string.count(TAB)} {columns_string=}"
            # state.newWordTable.append( columns_string )
            lastVerseRef = verseRef
            continue

        gloss = contextualWordGloss if contextualWordGloss \
                else wordGloss if wordGloss \
                else contextualMorphemeGlosses if contextualMorphemeGlosses \
                else morphemeGlosses

        if gloss and gloss[0].isupper():
        # if 'U' in glossCaps: # or 'G' in glossCaps: ???
            dPrint( 'Never', DEBUGGING_THIS_MODULE, f"{wordRef} {verseLinkEntry=}" )
            if verseLinkEntry['people']:
                dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"Need to add people: {n} {wordRef} '{noCantillations}' {glossCaps} '{gloss}' {verseLinkEntry['people']}")
                assert isinstance( verseLinkEntry['people'], list )
                for personID in verseLinkEntry['people']:
                    assert personID[0] == 'P' and ' ' not in personID and ';' not in personID
                    personName = personID[1:] # First prefix letter is P for person
                    while personName[-1].isdigit(): # it has a suffix
                        personName = personName[:-1] # Drop the final digit
                    if personName in gloss:
                        tags.append( personID )
                        dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  Added '{personID}' to {wordRef} for '{gloss}'")
                        numAddedPeople += 1
                    else:
                        for thgName,oetName in (('Israel','Jacob'),('Pharez','Perez'),('Zerah','Zara'),('Tamar','Thamar'),('Hezron','Esrom'),('Ram','Aram'),('Amminadab','Aminadab'),('Nahshon','Naasson'),
                                            ('Jehoshaphat','Josaphat'),('Jehoram','Joram'),('Uzziah','Ozias'),('Jotham','Joatham'),('Ahaz','Achaz'),
                                            ('Jehoiachin','Jechonias'),('Shealtiel','Salathiel'),('Zerubbabel','Zorobabel'),('Sadoc','Zadok')):
                            if personName==thgName and oetName in gloss:
                                tags.append( personID )
                                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  Added '{personID}' to {wordRef} for '{gloss}'")
                                numAddedPeople += 1
                                break
            if verseLinkEntry['places']:
                dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"Need to add places: {n} {wordRef} '{noCantillations}' {glossCaps} '{gloss}' {verseLinkEntry['places']}")
                assert isinstance( verseLinkEntry['places'], list )
                for placeID in verseLinkEntry['places']:
                    assert placeID[0] == 'L'
                    placeName = placeID[1:] # First prefix letter is L for location
                    while placeName[-1].isdigit(): # it has a suffix
                        placeName = placeName[:-1] # Drop the final digit
                    if placeName in gloss:
                        assert ' ' not in placeID and ';' not in placeID
                        tags.append( placeID )
                        dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  Added '{placeID}' to {wordRef} for '{gloss}'")
                        numAddedLocations += 1
        if newVerse:
            newVerse = False
            # These ones we can link to the first (included) word in the verse
            if verseLinkEntry['peopleGroups']:
                dPrint( 'Normal', DEBUGGING_THIS_MODULE, f"Could add people groups: {n} {wordRef} '{noCantillations}' {glossCaps} '{gloss}' {verseLinkEntry['peopleGroups']}")
                assert isinstance( verseLinkEntry['peopleGroups'], list )
                for pgID in verseLinkEntry['peopleGroups']:
                    # personName = pgID[1:] # First prefix letter is P for person
                    # while personName[-1].isdigit(): # it has a suffix
                    #     personName = personName[:-1] # Drop the final digit
                    assert ' ' not in pgID and ';' not in pgID
                    tag = f"G{pgID.replace(' ','_')}"
                    tags.append( tag )
                    dPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Added '{tag}' to {wordRef}")
                    numAddedPeopleGroups += 1
            if verseLinkEntry['yearNum']:
                dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"Could add year number: {n} {wordRef} '{noCantillations}' {glossCaps} '{gloss}' {verseLinkEntry['yearNum']}")
                assert isinstance( verseLinkEntry['yearNum'], str )
                tag = f"Y{verseLinkEntry['yearNum']}"
                assert ' ' not in tag and ';' not in tag
                tags.append( tag )
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  Added '{tag}' to {wordRef}")
                numAddedYears += 1
            if verseLinkEntry['eventsDescribed']:
                dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"Could add events: {n} {wordRef} '{noCantillations}' {glossCaps} '{gloss}' {verseLinkEntry['eventsDescribed']}")
                assert isinstance( verseLinkEntry['eventsDescribed'], list )
                for eventID in verseLinkEntry['eventsDescribed']:
                    # personName = personID[1:] # First prefix letter is P for person
                    # while personName[-1].isdigit(): # it has a suffix
                    #     personName = personName[:-1] # Drop the final digit
                    tag = f"E{eventID.replace(' ','_')}"
                    assert ' ' not in tag and ';' not in tag
                    tags.append( tag )
                    dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  Added '{tag}' to {wordRef}")
                    numAddedEvents += 1
            if verseLinkEntry['timeline']:
                dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"Could add timeline: {n} {wordRef} '{noCantillations}' {glossCaps} '{gloss}' {verseLinkEntry['timeline']}")
                assert isinstance( verseLinkEntry['timeline'], str )
                tag = f"T{verseLinkEntry['timeline'].replace(' ','_')}"
                assert ' ' not in tag and ';' not in tag
                tags.append( tag )
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  Added '{tag}' to {wordRef}")
                numAddedTimelines += 1

        # Put the new column in the table
        # print( f"{n=} {columns_string=} {tags=}" )
        assert columns_string.endswith( '\t' ) # because the newly created tags column was empty
        newLine = f"{columns_string}{';'.join(tags)}"
        assert newLine.count( '\t' ) == 20, f"{newLine.count(TAB)} {newLine=}"
        state.newWordTable[n] = newLine
        # print( f"  {state.newWordTable[n]=}")
        lastVerseRef = verseRef

    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"{numAddedPeople=:,} {numAddedPeopleGroups=:,} {numAddedLocations=:,} {numAddedEvents=:,} {numAddedYears=:,} {numAddedTimelines=:,}" )
    assert 381_000 < len(state.newWordTable) < 382_000, f"{len(state.newWordTable)=}"
    return True
# end of add_tags_to_OT_word_table.associate_Theographic_people_places


TAG_COLUMN_NUMBER = 20
def tag_trinity_persons() -> bool:
    """
    """
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, "\nTagging trinity persons in our table…" )
    assert 381_000 < len(state.newWordTable) < 382_000, f"{len(state.newWordTable)=}"

    # 0    1       2        3                4             5        6                      7           8     9                10               11                         12         13                   14                   15                16          17          18     19       20
    # Ref\tOSHBid\tRowType\tMorphemeRowList\tLemmaRowList\tStrongs\tCantillationHierarchy\tMorphology\tWord\tNoCantillations\tMorphemeGlosses\tContextualMorphemeGlosses\tWordGloss\tContextualWordGloss\tGlossCapitalisation\tGlossPunctuation\tGlossOrder\tGlossInsert\tRole\tNesting\tTags
    columnHeaders = state.newWordTable[0].split( '\t' )
    assert columnHeaders[TAG_COLUMN_NUMBER] == 'Tags' # Check our index value

    numAddedGod = numAddedHolySpirit = 0
    for n,rowStr in enumerate( state.newWordTable[1:], start=1 ):
        rowFields = rowStr.split( '\t' )
        wordRef, _OSHBid, rowType, _morphemeRowList, _lemmaRowList, _strongs, _cantillationHierarchy, _morphology, _word, noCantillations, morphemeGlosses, contextualMorphemeGlosses, wordGloss, contextualWordGloss, glossCaps, _glossPunctuation, _glossOrder, _glossInsert, _role, _nesting, tags = rowFields

        gloss = contextualWordGloss if contextualWordGloss \
                else wordGloss if wordGloss \
                else contextualMorphemeGlosses if contextualMorphemeGlosses \
                else morphemeGlosses
        
        tagList = tags.split( ';' ) if tags else []

        madeChanges = False

        # We rely on the SR capitalisation for these matches, e.g., difference between father/Father, son/Son, holy/Holy, spirit/Spirit
        # Any of these have the potential for a false tag, e.g., if Father or Holy was capitalised at the start of a sentence in the SR
        #   If it's a problem, we have the Caps column that we could also look at
        if ('God' in gloss or 'Father' in gloss) and 'PGod' not in tagList:
            tagList.append( 'PGod' )
            numAddedGod += 1
            madeChanges = True
        if 'Spirit' in gloss and 'PHoly_Spirit' not in tagList:
            tagList.append( 'PHoly_Spirit' )
            numAddedHolySpirit += 1
            madeChanges = True

        if madeChanges:
            rowFields[TAG_COLUMN_NUMBER] = ';'.join( tagList )
            newLine = '\t'.join( rowFields )
            assert newLine.count( '\t' ) == 20, f"{newLine.count(TAB)} {newLine=}"
            state.newWordTable[n] = newLine

    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  {numAddedGod=:,} {numAddedHolySpirit=:,} Total added={numAddedGod+numAddedHolySpirit:,}" )
    return True
# end of add_tags_to_OT_word_table.tag_trinity_persons


def tag_referents_from_macula_data() -> bool:
    """
    Using the Referent field from the Clear.Bible Macula Hebrew data
        (already loaded from a TSV file preprocessed by our convert_ClearMaculaOT_to_our_TSV.py)
        add referent tags to our existing table.

    Note that we are using the UHB
        and Clear used the OSHB,
        so some matches won't fit.
    """
    # global DEBUGGING_THIS_MODULE
    # DEBUGGING_THIS_MODULE = 99
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, "\nAssociating Macula referents with our table entries…" )
    assert 381_000 < len(state.newWordTable) < 382_000, f"{len(state.newWordTable)=}"

    # First make a book index into our table (for greater search efficiency down below)
    lastBBB = None
    ourBBBIndex = {}
    for p,ourRowStr in enumerate( state.newWordTable[1:], start=1 ):
        BBB = ourRowStr[:3]
        if BBB != lastBBB:
            if lastBBB is not None:
                ourBBBIndex[lastBBB] = (startIndex,p)
            startIndex = p
            lastBBB = BBB
    ourBBBIndex[BBB] = (startIndex,p)

    # 0      1       2        3               4       5        6          7             8       9       10      11        12     13    14             15           16    17          18     19           20       21              22     23     24           25            26               27
    # FGRef\tOSHBid\tRowType\tWordOrMorpheme\tAfter\tCompound\tWordClass\tPartOfSpeech\tPerson\tGender\tNumber\tWordType\tState\tRole\tStrongNumberX\tStrongLemma\tStem\tMorphology\tLemma\tSenseNumber\tSubjRef\tParticipantRef\tFrame\tGreek\tGreekStrong\tEnglishGloss\tContextualGloss\tNesting
    assert state.macula_tsv_lines[0][0] == 'FGRef' # Check our index value of 0
    assert state.macula_tsv_lines[0][3] == 'WordOrMorpheme' # Check our index value of 3
    assert state.macula_tsv_lines[0][6] == 'WordClass' # Check our index value of 6
    assert state.macula_tsv_lines[0][16] == 'Referents' # Check our index value of 16

    totalAdds = totalReferencePairAdds = totalPersonAdds = totalLocationAdds = numUnmatched = 0
    lastBBB = None
    for n,maculaRowList in enumerate( state.macula_tsv_lines[1:], start=1 ):
        BBB = maculaRowList[0][:3]
        if BBB != lastBBB:
            vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Processing {BBB}…")
            bookStartIndex,bookEndIndex = ourBBBIndex[BBB]
            lastBBB = BBB
        # if n > 110: break
        # if totalAdds > 5: break

        if maculaRowList[16]:
            # dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"{n} ({type(maculaRowList)}) {maculaRowList}" )
            referentIDs = maculaRowList[16].split( ';' )
            referentWordID, referentGreek = maculaRowList[0], maculaRowList[3]
            dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"  {referentWordID} ({maculaRowList[6]}) '{referentGreek}' ({len(referentIDs)}) {referentIDs}")
            for referentID in referentIDs:
                fullReferentID = f'{maculaRowList[0][:4]}{referentID}' # Add the bookcode in
                dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"    Need to find {fullReferentID}")

                # So do we need to search backwards or forwards?
                referentC, referentV, referentW = int(referentWordID[4:].split(':')[0]), int(referentWordID[4:].split(':')[-1].split('w')[0]), int(referentWordID[4:].split('w')[-1])
                referredC, referredV, referredW = int(referentID.split(':')[0]), int(referentID.split(':')[-1].split('w')[0]), int(referentID.split('w')[-1])
                searchAmount = '-C' if referredC<referentC else '+C' if referredC>referentC else None
                if searchAmount is None: searchAmount = '-V' if referredV<referentV else '+V' if referredV>referentV else None
                if searchAmount is None: searchAmount = '-W' if referredW<referentW else '+W' if referredW>referentW else None
                if searchAmount is None:
                    logging.critical( f"Are we linking to ourselves??? Failed going from {referentWordID} ({referentC},{referentV},{referentW}) to {referentID} ({referredC},{referredV},{referredW})" )
                    continue
                assert searchAmount is not None, f"Failed going from {referentWordID} ({referentC},{referentV},{referentW}) to {referentID} ({referredC},{referredV},{referredW})"
                offsetAmount = (abs(referentC-referredC)+1)*50*40 if searchAmount[1]=='C' else (abs(referentV-referredV)+1)*40 if searchAmount[1]=='V' else 30
                if searchAmount[0]=='-': offsetAmount = -offsetAmount; step = -1
                else: step = 1
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"    Got {searchAmount=} going from {referentWordID} ({referentC},{referentV},{referentW}) to {referentID} ({referredC},{referredV},{referredW}) so {offsetAmount=} and {step=}")
                # Firstly we also have to find the referred word in the macula table
                # Usually it's before the referent, but can be after, e.g., "and you, Bethlehem"
                for m in range( n, n+offsetAmount, step ):
                    # print( f"      {m} {state.macula_tsv_lines[m]}")
                    if state.macula_tsv_lines[m][0] == fullReferentID:
                        # print( f"      Found {m} {state.macula_tsv_lines[m]}")
                        break
                else:
                    dPrint( 'Normal', DEBUGGING_THIS_MODULE, f"    Got {searchAmount=} going from {referentWordID} ({referentC},{referentV},{referentW}) to {referentID} ({referredC},{referredV},{referredW}) so {offsetAmount=} and {step=}")
                    logging.critical( f"<<<< @{referentWordID} can't find {fullReferentID} '{referentGreek}' >>>>" )
                referredWordID, referrednoCantillations = state.macula_tsv_lines[m][0], state.macula_tsv_lines[m][3]
                # We expect that the referredWordID is BEFORE the referentWordID
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"    {referentWordID=} {referentGreek=} {referredWordID=} {referrednoCantillations=}")

                # Find the parts of our table for this verse / verses
                referentVerseID, referredVerseID = referentWordID.split('w')[0], referredWordID.split('w')[0]
                ourReferentVerseRowIndices, ourReferredVerseRowIndices = [], []
                for p,ourRowStr in enumerate( state.newWordTable[bookStartIndex:bookEndIndex], start=bookStartIndex ):
                    if ourRowStr.startswith( f'{referredVerseID}w' ):
                        # print( f"  to REFERRED {p} {ourRowStr}" )
                        ourReferredVerseRowIndices.append( p )
                    if ourRowStr.startswith( f'{referentVerseID}w' ):
                        # print( f"  fr REFERENT {p} {ourRowStr}" )
                        ourReferentVerseRowIndices.append( p )

                # First try to find our referent Hebrew word
                possibleReferentRowIndices = []
                for p in ourReferentVerseRowIndices:
                    rowItems = state.newWordTable[p].split( '\t' )
                    if rowItems[1] == referentGreek:
                        # print( f"  REFERENT {p} {rowItems}" )
                        possibleReferentRowIndices.append( p )
                dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"    Found {len(possibleReferentRowIndices)}/{len(ourReferentVerseRowIndices)} referent verse row(s) that might match {referentWordID} '{referentGreek}'")

                # Now try to find the referred Hebrew word
                possibleReferredRowIndices = []
                for p in ourReferredVerseRowIndices:
                    rowItems = state.newWordTable[p].split( '\t' )
                    if rowItems[1] == referrednoCantillations:
                        # print( f"  REFERRED {p} {rowItems}" )
                        possibleReferredRowIndices.append( p )
                dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"    Found {len(possibleReferredRowIndices)}/{len(ourReferredVerseRowIndices)} referred verse row(s) that might match {referentWordID} '{referrednoCantillations}'")
                
                if not possibleReferredRowIndices: # have a second attempt
                    for p in ourReferredVerseRowIndices:
                        rowItems = state.newWordTable[p].split( '\t' )
                        if rowItems[1][:3] == referrednoCantillations[:3]: # Last letters might be different?
                            # print( f"  REFERRED {p} {rowItems}" )
                            possibleReferredRowIndices.append( p )
                        # else: print( f"{rowItems[1][:4]} != {referrednoCantillations[:4]}")
                    dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"    Loosely found {len(possibleReferredRowIndices)} referred verse row(s) that might match {referentWordID} '{referrednoCantillations}'")

                def appendNewTags( ixReferent:int, ixReferred:int ):
                    """
                    We establish a referred (R) and from (F) link for referents marked in Macula

                    Also, if there's a person or location link in the referred word, we copy that back to the referent word.

                    However, our word numbers vary (because our GNT is different, plus we include unused/variant words in our word count)
                        so we have to fix up the word number as well.
                        UPDATED: We now put the row number instead

                    Uses many global variables as well as a declared nonlocal ones.
                    """
                    nonlocal totalReferencePairAdds, totalPersonAdds, totalLocationAdds, totalAdds
                    fnPrint( DEBUGGING_THIS_MODULE, f"appendNewTags( {ixReferent=}, {ixReferred=} )" )

                    referrentRowIndex = possibleReferentRowIndices[ixReferent]
                    referredRowIndex = possibleReferredRowIndices[ixReferred]
                    existingReferentRowStr = state.newWordTable[referrentRowIndex]
                    existingReferredRowStr = state.newWordTable[referredRowIndex]

                    existingReferentRowFields = existingReferentRowStr.split( '\t' )
                    existingReferredRowFields = existingReferredRowStr.split( '\t' )

                    existingReferentRowTags = existingReferentRowFields[TAG_COLUMN_NUMBER].split( ';' ) if existingReferentRowFields[TAG_COLUMN_NUMBER] else []
                    existingReferredRowTags = existingReferredRowFields[TAG_COLUMN_NUMBER].split( ';' ) if existingReferredRowFields[TAG_COLUMN_NUMBER] else []

                    # We decided that the row number is a better link
                    # elReferentWordID = existingReferentRowFields[0][4:] # } We drop the BBB_ because referent/referred pairs
                    # elReferredWordID = existingReferredRowFields[0][4:] # }   only occur within the same book
                    # existingReferentRowTags.append( f'R{elReferredWordID}' )
                    # existingReferredRowTags.append( f'F{elReferentWordID}' )

                    existingReferentRowTags.append( f'R{referredRowIndex}' )
                    existingReferredRowTags.append( f'F{referrentRowIndex}' )

                    totalReferencePairAdds += 1

                    for referredTag in existingReferredRowTags:
                        if referredTag.startswith( 'P' ): # Found a person tag
                            # Add the person tag to our referent line
                            existingReferentRowTags.append( referredTag )
                            totalPersonAdds += 1
                            totalAdds += 1
                        elif referredTag.startswith( 'L' ): # Found a location tag
                            # Add the person tag to our referent line
                            existingReferentRowTags.append( referredTag )
                            totalLocationAdds += 1
                            totalAdds += 1
                    # dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"    Added {numAdded} tag(s) so now {existingReferentRowTags}" )
                    existingReferentRowFields[TAG_COLUMN_NUMBER] = ';'.join( existingReferentRowTags )
                    newLine = '\t'.join( existingReferentRowFields )
                    assert newLine.count( '\t' ) == 11, f"{newLine.count(TAB)} {newLine=}"
                    state.newWordTable[possibleReferentRowIndices[ixReferent]] = newLine
                    existingReferredRowFields[TAG_COLUMN_NUMBER] = ';'.join( existingReferredRowTags )
                    newLine = '\t'.join( existingReferredRowFields )
                    assert newLine.count( '\t' ) == 11, f"{newLine.count(TAB)} {newLine=}"
                    state.newWordTable[possibleReferredRowIndices[ixReferred]] = newLine
                # end of appendNewTags function

                if not possibleReferentRowIndices:
                    dPrint( 'Info', DEBUGGING_THIS_MODULE, f"    <<< Unable to find referent {referentVerseID} '{referentGreek}' in {len(possibleReferentRowIndices)} rows >>>")
                    for p in ourReferentVerseRowIndices:
                        dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"       {state.newWordTable[p].split( TAB )}" )
                elif not possibleReferredRowIndices:
                    dPrint( 'Info', DEBUGGING_THIS_MODULE, f"    <<< Unable to find referred {referredVerseID} '{referrednoCantillations}' in {len(possibleReferredRowIndices)} rows >>>")
                    for p in ourReferredVerseRowIndices:
                        dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"       {state.newWordTable[p].split( TAB )}" )

                elif len(possibleReferentRowIndices)==1 and len(possibleReferredRowIndices)==1: # This is the easiest case
                    appendNewTags( ixReferent=0, ixReferred=0 )
                elif len(possibleReferredRowIndices) == 1: # we know where we're going
                    assert len(possibleReferentRowIndices) > 1 # but don't know where we're coming from (yet)
                    referentWordNumber = int( referentWordID.split('w')[-1] )
                    possibleWordNumbers = []
                    for p in possibleReferentRowIndices:
                        dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"       {state.newWordTable[p].split( TAB )}" )
                        possibleWordNumbers.append( int( state.newWordTable[p].split(TAB)[0].split('w')[-1] ) )
                    wordNumberDistances = [abs(referentWordNumber-possibleWordNumber) for possibleWordNumber in possibleWordNumbers]
                    minWordNumberDistance = min( wordNumberDistances )
                    dPrint( 'Info', DEBUGGING_THIS_MODULE, f"      Have {referentWordNumber=} and {possibleWordNumbers=} giving {wordNumberDistances=} with {minWordNumberDistance=}")
                    if wordNumberDistances.count( minWordNumberDistance ) == 1: # only one has this minimum distance
                        appendNewTags( ixReferent=wordNumberDistances.index( minWordNumberDistance ), ixReferred=0 )
                elif len(possibleReferentRowIndices) == 1: # we know where we're coming from
                    assert len(possibleReferredRowIndices) > 1 # but don't know where we're going to (yet)
                    referredWordNumber = int( referredWordID.split('w')[-1] )
                    possibleWordNumbers = []
                    for p in possibleReferredRowIndices:
                        dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"       {state.newWordTable[p].split( TAB )}" )
                        possibleWordNumbers.append( int( state.newWordTable[p].split(TAB)[0].split('w')[-1] ) )
                    wordNumberDistances = [abs(referredWordNumber-possibleWordNumber) for possibleWordNumber in possibleWordNumbers]
                    minWordNumberDistance = min( wordNumberDistances )
                    dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"      Have {referredWordNumber=} and {possibleWordNumbers=} giving {wordNumberDistances=} with {minWordNumberDistance=}")
                    if wordNumberDistances.count( minWordNumberDistance ) == 1: # only one has this minimum distance
                        appendNewTags( ixReferent=0, ixReferred=wordNumberDistances.index( minWordNumberDistance ) )
                else:
                    assert len(possibleReferentRowIndices)>1 and len(possibleReferredRowIndices)>1 # both!
                    # if len(possibleReferentRowIndices) != 1:
                    #     for p in possibleReferentRowIndices:
                    #         print( f"       {state.newWordTable[p].split( TAB )}" )
                    # if len(possibleReferredRowIndices) != 1:
                    #     for p in possibleReferredRowIndices:
                    #         print( f"       {state.newWordTable[p].split( TAB )}" )
                    referentWordNumber = int( referentWordID.split('w')[-1] )
                    possibleWordNumbers = []
                    for p in possibleReferentRowIndices:
                        dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"       {state.newWordTable[p].split( TAB )}" )
                        possibleWordNumbers.append( int( state.newWordTable[p].split(TAB)[0].split('w')[-1] ) )
                    wordNumberDistances = [abs(referentWordNumber-possibleWordNumber) for possibleWordNumber in possibleWordNumbers]
                    minWordNumberDistance = min( wordNumberDistances )
                    dPrint( 'Info', DEBUGGING_THIS_MODULE, f"      Have {referentWordNumber=} and {possibleWordNumbers=} giving {wordNumberDistances=} with {minWordNumberDistance=}")
                    if wordNumberDistances.count( minWordNumberDistance ) == 1: # only one has this minimum distance
                        ixReferent = wordNumberDistances.index( minWordNumberDistance )

                    referredWordNumber = int( referredWordID.split('w')[-1] )
                    possibleWordNumbers = []
                    for p in possibleReferredRowIndices:
                        dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"       {state.newWordTable[p].split( TAB )}" )
                        possibleWordNumbers.append( int( state.newWordTable[p].split(TAB)[0].split('w')[-1] ) )
                    wordNumberDistances = [abs(referredWordNumber-possibleWordNumber) for possibleWordNumber in possibleWordNumbers]
                    minWordNumberDistance = min( wordNumberDistances )
                    dPrint( 'Info', DEBUGGING_THIS_MODULE, f"      Have {referredWordNumber=} and {possibleWordNumbers=} giving {wordNumberDistances=} with {minWordNumberDistance=}")
                    if wordNumberDistances.count( minWordNumberDistance ) == 1: # only one has this minimum distance
                        ixReferred = wordNumberDistances.index( minWordNumberDistance )

                    try: # will fail if both ixReferent and ixReferred are not declared
                        appendNewTags( ixReferent, ixReferred )
                    except UnboundLocalError:
                        logging.critical( f"Unable to find a referent and a referrer row for {referentWordID=} {referentGreek=} {referredWordID=} {referrednoCantillations=}" )
                        numUnmatched += 1
                    # Make them both undefined again
                    try: del ixReferent
                    except UnboundLocalError: pass
                    try: del ixReferred 
                    except UnboundLocalError: pass

    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"Added {totalPersonAdds:,} referred person tags")
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"Added {totalLocationAdds:,} referred location tags")
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"Added {totalAdds:,} total referred person/location tags")
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"Added {totalReferencePairAdds:,} total back/forth referrent tag pairs")
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"Skipped {numUnmatched:,} referrent tag pairs (probably GNT differences)")
    return True
# end of add_tags_to_OT_word_table.tag_referents_from_macula_data


def fill_extra_columns_and_remove_some() -> bool:
    """
    Fill the new TSV table (already with an extra Tags column)
        filling in the Role and Nesting columns from the Macula Hebrew data

    Problem is first table is organised by word,
        and second table is organised by morpheme.

    Finally, we remove the OSHBid and CantillationHierarchy columns from our table
    """
    # DEBUGGING_THIS_MODULE = 99
    assert 381_000 < len(state.newWordTable) < 382_000, f"{len(state.newWordTable)=}"

    # 0    1       2        3                4             5        6                      7           8     9                10               11                         12         13                   14                   15                16          17          18     19       20
    # Ref\tOSHBid\tRowType\tMorphemeRowList\tLemmaRowList\tStrongs\tCantillationHierarchy\tMorphology\tWord\tNoCantillations\tMorphemeGlosses\tContextualMorphemeGlosses\tWordGloss\tContextualWordGloss\tGlossCapitalisation\tGlossPunctuation\tGlossOrder\tGlossInsert\tRole\tNesting\tTags
    ourHeaderColumns = state.newWordTable[0].split( '\t' )
    assert ourHeaderColumns[1] == 'OSHBid' # If not, we need to make changes below -- we delete this column
    assert ourHeaderColumns[2] == 'RowType' # If not, we need to make changes below
    assert ourHeaderColumns[3] == 'MorphemeRowList' # If not, we need to make changes below
    assert ourHeaderColumns[4] == 'LemmaRowList' # If not, we need to make changes below -- we fill this column
    assert ourHeaderColumns[6] == 'CantillationHierarchy' # If not, we need to make changes below -- we delete this column
    assert ourHeaderColumns[18] == 'Role' # If not, we need to make changes below -- we fill this column
    assert ourHeaderColumns[19] == 'Nesting' # If not, we need to make changes below -- we fill this column
    # 0      1       2        3               4       5        6          7             8       9       10      11        12     13    14             15           16    17          18     19           20       21              22     23     24           25            26               27
    # FGRef\tOSHBid\tRowType\tWordOrMorpheme\tAfter\tCompound\tWordClass\tPartOfSpeech\tPerson\tGender\tNumber\tWordType\tState\tRole\tStrongNumberX\tStrongLemma\tStem\tMorphology\tLemma\tSenseNumber\tSubjRef\tParticipantRef\tFrame\tGreek\tGreekStrong\tEnglishGloss\tContextualGloss\tNesting
    theirHeaderColumns = state.macula_tsv_lines[0] # Already in a list
    assert theirHeaderColumns[2] == 'RowType' # If not, we need to make changes below
    assert theirHeaderColumns[13] == 'Role' # If not, we need to make changes below
    assert theirHeaderColumns[18] == 'Lemma' # If not, we need to make changes below
    assert theirHeaderColumns[27] == 'Nesting' # If not, we need to make changes below

    # First build a dictionary to lemma row numbers
    state.lemmaDict = {}
    for n,lemmaStr in enumerate( state.lemmaTable[1:], start=1 ):
        lemma, _glosses = lemmaStr.split('\t')
        # print( f"{n} {lemma=} {_glosses=}")
        state.lemmaDict[lemma] = str(n)
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"Loaded {len(state.lemmaDict):,} lemma index entries into state.lemmaDict." )

    # Fill in the role and nesting columns
    mIx = 1 # Macula index
    numConsecutiveMismatches = 0
    for ix, ourLine in enumerate( state.newWordTable[1:], start=1 ):
        lemmaList, lemmaRowList = [], []
        for dummyRange in range( 4 ):
            if dummyRange > 0: dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"{dummyRange=}" )
            if mIx >= len(state.macula_tsv_lines):
                dPrint( 'Normal', DEBUGGING_THIS_MODULE, f"RanA out of Macula lines at {ix}/{len(state.newWordTable)} {ourLine}" )
                break # no more macula lines
            theirMaculaColumns = state.macula_tsv_lines[mIx] # Already in a list
            # print( f"\n{ix}: {ourLine}\n{mIx}: {theirLine}")
            assert ourLine.count( '\t' ) == 20, f"{ourLine.count(TAB)} {ourLine=}"
            ourColumns = ourLine.split( '\t' )
            assert len(theirMaculaColumns) == 28, f"{len(theirMaculaColumns)} {theirMaculaColumns=}"

            if ourColumns[2] in ('seg','note','variant note','alternative note','exegesis note'):
                numConsecutiveMismatches = 0
                dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"Skipping our {ourColumns[0]} {ourColumns[2]}")
                break # from inner dummy loop because we were successful
            elif theirMaculaColumns[0] == ourColumns[0]: # then it's a word
                numConsecutiveMismatches = 0
                dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"Matched word {ourColumns[0]}=={theirMaculaColumns[0]} {theirMaculaColumns[1]} {ourColumns[1]} {theirMaculaColumns[2]} {ourColumns[2]} R='{theirMaculaColumns[13]}' N='{theirMaculaColumns[27]}'")
                assert 'w' in theirMaculaColumns[2] # Might be 'Aw'
                ourColumns[18], ourColumns[19] = theirMaculaColumns[13], theirMaculaColumns[27]
                theirMaculaLemma = theirMaculaColumns[18]
                # print( f"{ourColumns[0]} {theirMaculaColumns[0]} {theirMaculaLemma=}" )
                lemmaList.append( theirMaculaLemma )
                if theirMaculaLemma:
                    try: lemmaRowList.append( state.lemmaDict[theirMaculaLemma] ) # Save the lemma row number(s)
                    except KeyError: lemmaRowList.append( '<<<MISSING-A1>>>' )
                else: lemmaRowList.append( '<<<MISSING-B1>>>' )
                mIx += 1
                break # from inner dummy loop because we were successful
            elif theirMaculaColumns[0].startswith( ourColumns[0] ): # then theirs is a morpheme that's part of our word
                numConsecutiveMismatches = 0
                role = nesting = ''
                while 'm' in theirMaculaColumns[2]:
                    dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"Matched morpheme {ourColumns[0]} in {theirMaculaColumns[0]} {theirMaculaColumns[1]} {ourColumns[1]} {theirMaculaColumns[2]} {ourColumns[2]} R='{theirMaculaColumns[13]}' N='{theirMaculaColumns[27]}'")
                    assert not role or theirMaculaColumns[13]==role or ourColumns[0].startswith( 'ECC_4:10' ) # TODO: dunno why ???
                    # assert nesting is None or theirLine[27] == nesting
                    # Above failed on
                    #   morpheme GEN_1:2w1a 01LN3a  m 13,14,15 R='' N='cj2cjp'
                    #   morpheme GEN_1:2w1b 01LN3b  m 13,14,15 R='' N='cj2cjp/s-v-o/s=detnp'
                    role, nesting = theirMaculaColumns[13], theirMaculaColumns[27]
                    theirMaculaLemma = theirMaculaColumns[18]
                    # print( f"{ourColumns[0]} {theirMaculaColumns[0]} {theirMaculaLemma=}" )
                    lemmaList.append( theirMaculaLemma )
                    if theirMaculaLemma:
                        try: lemmaRowList.append( state.lemmaDict[theirMaculaLemma] ) # Save the lemma row number(s)
                        except KeyError: lemmaRowList.append( '<<<MISSING-A2>>>' )
                    else: lemmaRowList.append( '<<<MISSING-B2>>>' )
                    mIx += 1
                    theirMaculaColumns = state.macula_tsv_lines[mIx] # Already in a list
                dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"Matched Morpheme {ourColumns[0]} in {theirMaculaColumns[0]} {theirMaculaColumns[1]} {ourColumns[1]} {theirMaculaColumns[2]} {ourColumns[2]} R='{theirMaculaColumns[13]}' N='{theirMaculaColumns[27]}'")
                assert 'M' in theirMaculaColumns[2] # Might be 'AM'
                if theirMaculaColumns[13] != role:
                    role = f'{role}{theirMaculaColumns[13]}' # Append the different role onto the end
                # assert theirLine[27] == nesting
                # Above failed on
                #   morpheme GEN_1:1w6a 01k5Pa  m 8,9 R='' N='pp-v-s-o/o=npanp/cj2cjp'
                #   Morpheme GEN_1:1w6b 01k5Pb  M 8,9 R='' N='pp-v-s-o/o=npanp/cj2cjp/ompnp'
                ourColumns[18], ourColumns[19] = role, nesting
                theirMaculaLemma = theirMaculaColumns[18]
                # print( f"{ourColumns[0]} {theirMaculaColumns[0]} {theirMaculaLemma=}" )
                lemmaList.append( theirMaculaLemma )
                if theirMaculaLemma:
                    try: lemmaRowList.append( state.lemmaDict[theirMaculaLemma] ) # Save the lemma row number(s)
                    except KeyError: lemmaRowList.append( '<<<MISSING-A3>>>' )
                else: lemmaRowList.append( '<<<MISSING-B3>>>' )
                mIx += 1
                break # from inner dummy loop because we were successful
            else:
                numConsecutiveMismatches += 1
                if numConsecutiveMismatches > 25:
                    # logging.critical( f"Aborted around {ourColumns[0]} {theirMaculaColumns[0]}")
                    break # Gen 39:9 after w7 missing has about 25 rows
                ourBBB, ourCVW = ourColumns[0].split( '_', 1 )
                theirMaculaBBB, theirMaculaCVW = theirMaculaColumns[0].split( '_', 1 )
                less = more = False
                # assert ourBBB == theirMaculaBBB, f"{ourBBB=} {theirMaculaBBB=} {lastBBB=}"
                if ourBBB != theirMaculaBBB:
                    if ourBBB != lastBBB: more = True
                    else: halt
                if not more or less:
                    ourC, ourVW = ourCVW.split( ':', 1 )
                    theirMaculaC, theirVW = theirMaculaCVW.split( ':', 1 )
                    less = int(ourC) < int(theirMaculaC)
                    more = int(ourC) > int(theirMaculaC)
                if not more or less:
                    ourV, ourW = ourVW.split( 'w', 1 )
                    theirMaculaV, theirMaculaW = theirVW.split( 'w', 1 )
                    less = int(ourV) < int(theirMaculaV)
                    more = int(ourV) > int(theirMaculaV)
                if not more or less:
                    ourWint = int(ourW)
                    try: theirMaculaWint = int(theirMaculaW)
                    except ValueError: theirMaculaWint = int(theirMaculaW[:-1]) # Remove suffix
                    less = ourWint < theirMaculaWint
                    more = ourWint > theirMaculaWint
                # NOTE: Can also happen with versification issues
                # We currently get as far as DEU_22:16
                if less: #ourColumns[0] < theirMaculaColumns[0]: # string comparison
                    logging.critical( f"Missing word in Macula Hebrew??? {ourC}:{ourV}w{ourW}<{theirMaculaC}:{theirMaculaV}w{theirMaculaW} {dummyRange=} {numConsecutiveMismatches=}\n We have a mismatch ({numConsecutiveMismatches}) with \n  {ix}: {ourLine}\n  {mIx}: {theirMaculaColumns}")
                    break # from inner dummy loop (which uses mIx but we haven't changed it)
                elif more: # it might be the opposite
                    logging.critical( f"Extra word in Macula Hebrew??? {ourC}:{ourV}w{ourW}>{theirMaculaC}:{theirMaculaV}w{theirMaculaW} {dummyRange=} {numConsecutiveMismatches=}\n We have a mismatch ({numConsecutiveMismatches}) with \n  {ix}: {ourLine}\n  {mIx}: {theirMaculaColumns}")
                    mIx += 1 # Advance 'their' row
                else:
                    print( f"Neither more nor less {ourC}:{ourV}w{ourW} vs {theirMaculaC}:{theirMaculaV}w{theirMaculaW} {dummyRange=} {numConsecutiveMismatches=}" )
            lastBBB = ourBBB
        if lemmaRowList:
            # print( lemmaRowList )
            ourColumns[4] = ','.join( lemmaRowList )
            if ourColumns[4].count(',') != ourColumns[3].count(','):
                logging.critical( f"LemmaRowList count doesn't match MorphemeRowList count at {ourColumns[0]} {lemmaList=} {ourColumns[3]=} {ourColumns[4]=}" )
        state.newWordTable[ix] = '\t'.join( ourColumns )
        if mIx >= len(state.macula_tsv_lines):
            dPrint( 'Normal', DEBUGGING_THIS_MODULE, f"RanB out of Macula lines at {ix}/{len(state.newWordTable)} {ourLine}" )
            break # no more macula lines
        if numConsecutiveMismatches > 25: # Gen 39:9 after w7 missing has about 25 rows
            logging.critical( f"Aborted around {ourColumns[0]} {theirMaculaColumns[0]}")
            halt
            break # from outer loop

    # Remove the OSHBid and CantillationHierarchy columns
    assert 381_000 < len(state.newWordTable) < 382_000, f"{len(state.newWordTable)=}"
    state.newWordTable[0] = state.newWordTable[0].replace(f'{TAB}OSHBid{TAB}',f'{TAB}').replace(f'{TAB}CantillationHierarchy{TAB}',f'{TAB}')
    for ix, ourLine in enumerate( state.newWordTable[1:], start=1 ):
        assert ourLine.count( '\t' ) == 20, f"{ourLine.count(TAB)} {ourLine=}"
        ourColumns = ourLine.split( '\t' )
        del ourColumns[6] # CantillationHierarchy
        del ourColumns[1] # OSHBid
        state.newWordTable[ix] = '\t'.join( ourColumns )
    assert 381_000 < len(state.newWordTable) < 382_000, f"{len(state.newWordTable)=}"

    return True
# end of add_tags_to_OT_word_table.write_new_table


def write_new_table() -> bool:
    """
    Write the new TSV table (already with an extra Tags column)
        using the data in state.newWordTable
    """
    assert 381_000 < len(state.newWordTable) < 382_000, f"{len(state.newWordTable)=}"
    
    with open( WORD_TABLE_OUTPUT_FILEPATH, 'wt', encoding='utf-8' ) as new_table_output_file:
        for line in state.newWordTable:
            assert line.count( '\t' ) == 18, f"{line.count(TAB)} {line=}"
            new_table_output_file.write( f'{line}\n' )
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"Wrote {len(state.newWordTable):,} lines to {WORD_TABLE_OUTPUT_FILEPATH} ({state.newWordTable[0].count(TAB)+1} columns).")
    
    # Also use the same word file for the OET-RV
    shutil.copy2( WORD_TABLE_OUTPUT_FILEPATH, RV_ESFM_OUTPUT_FOLDERPATH.joinpath( WORD_TABLE_OUTPUT_FILENAME ) )
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"Also copied {WORD_TABLE_OUTPUT_FILENAME} to {RV_ESFM_OUTPUT_FOLDERPATH}.")

    return True
# end of add_tags_to_OT_word_table.write_new_table



if __name__ == '__main__':
    # from multiprocessing import freeze_support
    # freeze_support() # Multiprocessing support for frozen Windows executables

    # Configure basic Bible Organisational System (BOS) set-up
    parser = BibleOrgSysGlobals.setup( SHORT_PROGRAM_NAME, PROGRAM_VERSION, LAST_MODIFIED_DATE )
    BibleOrgSysGlobals.addStandardOptionsAndProcess( parser )

    main()

    BibleOrgSysGlobals.closedown( PROGRAM_NAME, PROGRAM_VERSION )
# end of add_tags_to_OT_word_table.py
