#!/usr/bin/env python3
# -\*- coding: utf-8 -\*-
# SPDX-License-Identifier: GPL-3.0-or-later
#
# add_tags_to_NT_word_table.py
#
# Script handling add_tags_to_NT_word_table functions
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
Adds an extra 'Tags' column to the wordTable used by the OET New Testament.
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
        which is based on the 1904 Nestle Greek New Testament)
    but which we have preprocessed into easier-to-use TSV files
        using https://github.com/Freely-Given-org/OpenEnglishTranslation--OET/blob/main/scripts/convert_ClearMaculaNT_to_TSV.py.

We use this information to update our OET word-table
    that was created by extract_VLT_NT_to_ESFM.py

CHANGELOG:
    2023-04-27 Clear table now has combined subject referents into Referents column (so now, one less column but more information)
    2024-03-08 Add OETGlossWords column and apply .tsv transforms similar to how Scripted Bible Editor does
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
from BibleTransliterations import load_transliteration_table, transliterate_Hebrew, transliterate_Greek

LAST_MODIFIED_DATE = '2024-07-02' # by RJH
SHORT_PROGRAM_NAME = "Add_wordtable_people_places_referrents"
PROGRAM_NAME = "Add People&Places tags to OET NT wordtable"
PROGRAM_VERSION = '0.34'
PROGRAM_NAME_VERSION = f'{SHORT_PROGRAM_NAME} v{PROGRAM_VERSION}'

DEBUGGING_THIS_MODULE = False


SCRIPTED_UPDATES_TABLES_INPUT_FOLDERPATH = Path( 'ScriptedVLTUpdates/' )

JSON_VERSES_DB_FILEPATH = Path( '../../Bible_speaker_identification/outsideSources/TheographicBibleData/derivedFiles/normalised_Verses.json' )
MACULA_GREEK_TSV_FILEPATH = Path( '../intermediateTexts/Clear.Bible_derived_Macula_data/Clear.Bible_MaculaGreek_LowFatTrees.NT.words.abbrev.tsv' )

WORD_TABLE_INPUT_FILEPATH = Path( '../intermediateTexts/modified_source_VLT_ESFM/OET-LV_NT_word_table.10columns.tsv' )
WORD_TABLE_OUTPUT_FILENAME = 'OET-LV_NT_word_table.tsv'
WORD_TABLE_OUTPUT_FOLDERPATH = Path( '../intermediateTexts/modified_source_VLT_ESFM/' )
WORD_TABLE_OUTPUT_FILEPATH = WORD_TABLE_OUTPUT_FOLDERPATH.joinpath( WORD_TABLE_OUTPUT_FILENAME )
EXPECTED_WORD_TABLE_DATA_ROW_COUNT = 168_247
RV_ESFM_OUTPUT_FOLDERPATH = Path( '../translatedTexts/ReadersVersion/' ) # We also copy the wordfile to this folder

TAB = '\t'


state = None
class State:
    def __init__( self ) -> None:
        """
        Constructor:
        """
        newTable = None
    # end of add_tags_to_NT_word_table.__init__


def main() -> None:
    """
    """
    BibleOrgSysGlobals.introduceProgram( __name__, PROGRAM_NAME_VERSION, LAST_MODIFIED_DATE )
    global state
    state = State()

    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"Reading existing table entries from {WORD_TABLE_INPUT_FILEPATH}…" )
    with open( WORD_TABLE_INPUT_FILEPATH, 'rt', encoding='utf-8' ) as old_table_file:
        state.oldTable = old_table_file.read().rstrip( '\n' ).split( '\n' )
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Loaded {len(state.oldTable):,} old table entries ({state.oldTable[0].count(TAB)+1} columns)." )

    expand_table_columns() # Creates state.newTable from state.oldTable

    apply_VLT_scripted_gloss_updates()

    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"Reading Theographic Bible Data json entries from {JSON_VERSES_DB_FILEPATH}…" )
    with open( JSON_VERSES_DB_FILEPATH, 'rt', encoding='utf-8' ) as json_file:
        state.verseIndex = json.load( json_file )
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Loaded {len(state.verseIndex):,} json verse entries." )

    associate_Theographic_people_places()

    tag_trinity_persons()

    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"\nReading Greek Macula tsv entries from {MACULA_GREEK_TSV_FILEPATH}…" )
    with open( MACULA_GREEK_TSV_FILEPATH, 'rt', encoding='utf-8' ) as macula_tsv_file:
        macula_tsv_lines = macula_tsv_file.readlines()
    if macula_tsv_lines[0].startswith( '\ufeff' ): # remove any BOM
        vPrint( 'Quiet', DEBUGGING_THIS_MODULE, "  Handling Byte Order Marker (BOM) at start of source tsv file…" )
        macula_tsv_lines[0] = macula_tsv_lines[0][1:]
    # Get the headers before we start
    column_line_string = macula_tsv_lines[0].rstrip( '\n' )
    # assert column_line_string == 'FGRef\tBibTagId\tRole\tWord\tAfter\tWordClass\tPerson\tGender\tNumber\tTense\tVoice\tMood\tDegree\tWordType\tDomain\tFrames\tReferents\tDiscontinuous\tMorphology\tLemma\tStrong\tContextualGloss\tNesting', f'{column_line_string=}' # otherwise we probably need to change some code
    assert column_line_string == 'FGRef\tBibTagId\tRole\tWord\tAfter\tWordClass\tPerson\tGender\tNumber\tTense\tVoice\tMood\tDegree\tWordType\tDomain\tFrames\tReferents\tDiscontinuous\tMorphology\tLemma\tJunction\tStrong\tContextualGloss\tNesting', f'{column_line_string=}' # otherwise we probably need to change some code
    # source_tsv_column_headers = [header for header in column_line_string.split('\t')]
    # # print(f"Column headers: ({len(source_tsv_column_headers)}): {source_tsv_column_headers}")
    # assert len(source_tsv_column_headers) == NUM_EXPECTED_OSHB_COLUMNS, f"Found {len(source_tsv_column_headers)} columns! (Expecting {NUM_EXPECTED_OSHB_COLUMNS})"
    # state.macula_dict_reader = DictReader(tsv_lines, delimiter='\t')
    state.macula_tsv_lines = []
    for macula_line in macula_tsv_lines:
        state.macula_tsv_lines.append( macula_line.rstrip( '\n' ).split( '\t' ) )
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Loaded {len(state.macula_tsv_lines):,} Greek Macula table entries ({column_line_string.count(TAB)+1} columns)." )

    tag_referents_from_macula_data()

    write_new_table()
# end of add_tags_to_NT_word_table.main


def expand_table_columns() -> bool:
    """
    Using state.oldTable, add the following columns and save in state.newTable:
        OETGlossWords (initialised to a copy of VLTGlossWords)
        Tags (left empty)
    """
    columnHeaders = state.oldTable[0]
    dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  Old word table column headers = '{columnHeaders}'" )
    assert columnHeaders == 'Ref\tGreekWord\tSRLemma\tGreekLemma\tVLTGlossWords\tGlossCaps\tProbability\tStrongsExt\tRole\tMorphology' # If not, probably need to fix some stuff

    state.newTable = [ f"{columnHeaders.replace(f'{TAB}VLTGlossWords{TAB}',f'{TAB}VLTGlossWords{TAB}OETGlossWords{TAB}')}{TAB}Tags" ]
    for _n, columns_string in enumerate( state.oldTable[1:], start=1 ):
        oldColumns = columns_string.split( '\t' )
        assert len(oldColumns) == 10
        newColumns = oldColumns.copy()
        newColumns.insert( 5, oldColumns[4] ) # Copy the VLTGlossWords column to the OETGlossWords column 
        newColumns.append( '' ) # Append new final Tags column
        # print( f"({len(newColumns)}) {newColumns=}" )
        assert len(newColumns) == 12, len(newColumns)
        newLine = '\t'.join( newColumns )
        assert newLine.count( '\t' ) == 11, f"{newLine.count(TAB)} {newLine=}"
        state.newTable.append( newLine )
        
    assert len(state.newTable) == EXPECTED_WORD_TABLE_DATA_ROW_COUNT+1, f"{EXPECTED_WORD_TABLE_DATA_ROW_COUNT=} {len(state.newTable)}"
    return True
# end of add_tags_to_NT_word_table.expand_table_columns


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
def apply_VLT_scripted_gloss_updates() -> bool:
    """
    Go through the .tsv files used by Scripted Bible Editor
        and apply them to the OETGlossWords column in state.newTable
    """
    columnHeaders = state.newTable[0].split( '\t' )
    assert columnHeaders[5] == 'OETGlossWords' # If not, probably need to fix some stuff

    # Firstly we read the TOML control file
    filepath = SCRIPTED_UPDATES_TABLES_INPUT_FOLDERPATH.joinpath( 'ScriptedBibleEditor.control.toml' )
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"Loading control file: {filepath}…" )
    with open( filepath, 'rb' ) as controlFile:
        controlData = tomllib.load( controlFile )

    load_transliteration_table( 'Hebrew' )
    load_transliteration_table( 'Greek' )

    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Loading and applying transforms to {columnHeaders[5]} column…" )
    totalChangedGlosses = 0
    commandTables = {}
    for commandTableName, givenFilepath in controlData['commandTables'].items():
        if commandTableName in ('fixGlossPre','fixGlossHelpers','fixGlossPost','cleanupVLT','finalFixes'): # These ones aren't relevant
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
                        newReplaceText = transliterate_Greek( replaceText )
                        if newReplaceText != replaceText:
                            # print(f" Converted Greek '{replaceText}' to '{newReplaceText}'")
                            replaceText = newReplaceText
                        # for char in replaceText:
                        #     if 'GREEK' in unicodedata.name(char):
                        #         logging.critical(f"Have some Greek left-overs in '{replaceText}'")
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
                    for n, columns_string in enumerate( state.newTable[1:], start=1 ):
                        columnDataList = columns_string.split( '\t' )
                        assert len(columnDataList) == 12
                        bcvwRef = columnDataList[0]
                        BBB, CV = bcvwRef.split( '_' )
                        if (iBooks and BBB not in iBooks) \
                        or BBB in eBooks:
                            vPrint( 'Info', DEBUGGING_THIS_MODULE, f"  Skipping {BBB} at {bcvwRef} with {iBooks=} {eBooks=}" )
                            continue
                        C, VW = CV.split( ':' )
                        V, W = VW.split( 'w' )
                        bcvRef = f'{BBB}_{C}:{V}'
                        if (iRefs and bcvRef not in iRefs) \
                        or bcvRef in eRefs:
                            if eRefs:
                                vPrint( 'Info', DEBUGGING_THIS_MODULE, f"  Skipping {bcvRef} at {bcvwRef} with {iRefs=} {eRefs=}" )
                            continue 
                        assert C.isdigit(), f"{C=}"
                        assert V.isdigit(), f"{V=}"
                        assert W.isdigit(), f"{W=}"
                        newGloss = oldGloss = columnDataList[5]

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
                            columnDataList[5] = newGloss
                            newLine = '\t'.join( columnDataList )
                            assert newLine.count( '\t' ) == 11, f"{newLine.count(TAB)} {newLine=}"
                            state.newTable[n] = newLine
                            numChangedGlosses += 1
                            totalChangedGlosses += 1
                    if numChangedGlosses:
                        vPrint( 'Info', DEBUGGING_THIS_MODULE, f"Made {numChangedGlosses:,} '{commandTableName}' OET gloss changes from scripted tables" )
                    
            vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"    Loaded and applied {len(commandTables[commandTableName])} command{'' if len(commandTables[commandTableName])==1 else 's'} for '{commandTableName}'." )
        else: vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"      '{completeFilepath}' is not a file!" )

    if totalChangedGlosses:
        vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"Made total {totalChangedGlosses:,} OET gloss changes from scripted tables" )

    return True
# end of add_tags_to_NT_word_table.apply_VLT_scripted_gloss_updates


def associate_Theographic_people_places() -> bool:
    """
    Using the Theographic Bible Data, tag Greek word lines in our table
        with keys for people, places, etc.
    """
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, "\nAssociating Greek words with json keys…" )

    # columnHeaders = state.oldTable[0]
    # dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  Old word table column headers = '{columnHeaders}'" )
    # assert columnHeaders == 'Ref\tGreekWord\tSRLemma\tGreekLemma\tVLTGlossWords\tGlossCaps\tProbability\tStrongsExt\tRole\tMorphology' # If not, probably need to fix some stuff

    numAddedPeople = numAddedPeopleGroups = numAddedLocations = numAddedEvents = numAddedYears = numAddedTimelines = 0
    lastVerseRef = None
    for n, columns_string in enumerate( state.newTable[1:], start=1 ):
        wordRef, greekWord, _srLemma, _greekLemma, VLTglossWords, OETGlossWords, glossCaps,probability, _extendedStrongs, _roleLetter, _morphology, _tags = columns_string.split( '\t' )
        tags:List[str] = []
        verseRef = wordRef.split('w')[0]
        newVerse = verseRef != lastVerseRef
        # print( f"{wordRef=} {verseRef} {lastVerseRef=} {newVerse=}" )
        try: verseLinkEntry = state.verseIndex[verseRef]
        except KeyError: # versification difference ???
            logging.critical( f"Versification error: Unable to find {verseRef} in Theographic json" )
            assert columns_string.count( '\t' ) == 11, f"{columns_string.count(TAB)} {columns_string=}"
            # print( f"{n} {columns_string=}" ); halt
            # state.newTable.append( columns_string ) # What was I trying to do here? (These duplicate rows get appended to the end)
            lastVerseRef = verseRef
            continue
        assert not verseLinkEntry['peopleGroups'] # Why is this true??? Ah, because only has a handful of OT references!!!

        if 'U' in glossCaps: # or 'G' in glossCaps: ???
            dPrint( 'Never', DEBUGGING_THIS_MODULE, f"{wordRef} {verseLinkEntry=}" )
            if verseLinkEntry['people']:
                dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"Need to add people: {n} {wordRef} ({probability}) '{greekWord}' {glossCaps} '{VLTglossWords}' {verseLinkEntry['people']}")
                assert isinstance( verseLinkEntry['people'], list )
                for personID in verseLinkEntry['people']:
                    assert personID[0] == 'P' and ' ' not in personID and ';' not in personID
                    personName = personID[1:] # First prefix letter is P for person
                    while personName[-1].isdigit(): # it has a suffix
                        personName = personName[:-1] # Drop the final digit
                    if personName in VLTglossWords:
                        tags.append( personID )
                        dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  Added '{personID}' to {wordRef} for '{VLTglossWords}'")
                        numAddedPeople += 1
                    else:
                        for thgName,srName in (('Israel','Jacob'),('Pharez','Perez'),('Zerah','Zara'),('Tamar','Thamar'),('Hezron','Esrom'),('Ram','Aram'),('Amminadab','Aminadab'),('Nahshon','Naasson'),
                                               ('Jehoshaphat','Josaphat'),('Jehoram','Joram'),('Uzziah','Ozias'),('Jotham','Joatham'),('Ahaz','Achaz'),
                                               ('Jehoiachin','Jechonias'),('Shealtiel','Salathiel'),('Zerubbabel','Zorobabel'),('Sadoc','Zadok')):
                            if personName==thgName and srName in VLTglossWords:
                                tags.append( personID )
                                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  Added '{personID}' to {wordRef} for '{VLTglossWords}'")
                                numAddedPeople += 1
                                break
            if verseLinkEntry['places']:
                dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"Need to add places: {n} {wordRef} ({probability}) '{greekWord}' {glossCaps} '{VLTglossWords}' {verseLinkEntry['places']}")
                assert isinstance( verseLinkEntry['places'], list )
                for placeID in verseLinkEntry['places']:
                    assert placeID[0] == 'L'
                    placeName = placeID[1:] # First prefix letter is L for location
                    while placeName[-1].isdigit(): # it has a suffix
                        placeName = placeName[:-1] # Drop the final digit
                    if placeName in VLTglossWords:
                        assert ' ' not in placeID and ';' not in placeID
                        tags.append( placeID )
                        dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  Added '{placeID}' to {wordRef} for '{VLTglossWords}'")
                        numAddedLocations += 1
        if probability and newVerse:
            newVerse = False
            # These ones we can link to the first (included) word in the verse
            if verseLinkEntry['peopleGroups']:
                halt
                # dPrint( 'Normal', DEBUGGING_THIS_MODULE, f"Could add people groups: {n} {ref} ({probability}) '{greek}' {glossCaps} '{glossWords}' {verseLinkEntry['peopleGroups']}")
                # assert isinstance( verseLinkEntry['peopleGroups'], list )
                # for pgID in verseLinkEntry['peopleGroups']:
                #     # personName = pgID[1:] # First prefix letter is P for person
                #     # while personName[-1].isdigit(): # it has a suffix
                #     #     personName = personName[:-1] # Drop the final digit
                #     assert ' ' not in pgID and ';' not in pgID
                #     links.append( pgID )
                #     dPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Added '{pgID}' to {ref}")
                #     halt
            if verseLinkEntry['yearNum']:
                dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"Could add year number: {n} {wordRef} ({probability}) '{greekWord}' {glossCaps} '{VLTglossWords}' {verseLinkEntry['yearNum']}")
                assert isinstance( verseLinkEntry['yearNum'], str )
                tag = f"Y{verseLinkEntry['yearNum']}"
                assert ' ' not in tag and ';' not in tag
                tags.append( tag )
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  Added '{tag}' to {wordRef}")
                numAddedYears += 1
            if verseLinkEntry['eventsDescribed']:
                dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"Could add events: {n} {wordRef} ({probability}) '{greekWord}' {glossCaps} '{VLTglossWords}' {verseLinkEntry['eventsDescribed']}")
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
                dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"Could add timeline: {n} {wordRef} ({probability}) '{greekWord}' {glossCaps} '{VLTglossWords}' {verseLinkEntry['timeline']}")
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
        assert newLine.count( '\t' ) == 11, f"{newLine.count(TAB)} {newLine=}"
        state.newTable[n] = newLine
        # print( f"  {state.newTable[n]=}")
        lastVerseRef = verseRef

    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"{numAddedPeople=:,} {numAddedPeopleGroups=:,} {numAddedLocations=:,} {numAddedEvents=:,} {numAddedYears=:,} {numAddedTimelines=:,}" )

    assert len(state.newTable) == EXPECTED_WORD_TABLE_DATA_ROW_COUNT+1, f"{EXPECTED_WORD_TABLE_DATA_ROW_COUNT=} {len(state.newTable)}"
    return True
# end of add_tags_to_NT_word_table.associate_Theographic_people_places


GLOSS_COLUMN_NUMBER = 4
TAG_COLUMN_NUMBER = 11
def tag_trinity_persons() -> bool:
    """
    Some undocumented documentation of the GlossCaps column:
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
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, "\nTagging trinity persons in our table…" )

    # Expect column headers 'Ref\tGreekWord\tSRLemma\tGreekLemma\tVLTGlossWords\tOETGlossWords\tGlossCaps\tProbability\tStrongsExt\tRole\tMorphology\tTags'
    columnHeaders = state.newTable[0].split( '\t' )
    assert columnHeaders[GLOSS_COLUMN_NUMBER] == 'VLTGlossWords' # Check our index value of 4
    assert columnHeaders[TAG_COLUMN_NUMBER] == 'Tags' # Check our index value of 10

    numAddedGod = numAddedJesus = numAddedHolySpirit = 0
    for n,rowStr in enumerate( state.newTable[1:], start=1 ):
        rowFields = rowStr.split( '\t' )
        srGlossWords = rowFields[GLOSS_COLUMN_NUMBER]
        tagList = rowFields[TAG_COLUMN_NUMBER].split( ';' ) if rowFields[TAG_COLUMN_NUMBER] else []

        madeChanges = False

        # We rely on the SR capitalisation for these matches, e.g., difference between father/Father, son/Son, holy/Holy, spirit/Spirit
        # Any of these have the potential for a false tag, e.g., if Father or Holy was capitalised at the start of a sentence in the SR
        #   If it's a problem, we have the Caps column that we could also look at
        if ('God' in srGlossWords or 'Father' in srGlossWords) and 'PGod' not in tagList:
            tagList.append( 'PGod' )
            numAddedGod += 1
            madeChanges = True
        if ('Messiah' in srGlossWords or 'Christ' in srGlossWords or 'Son' in srGlossWords) and 'PJesus' not in tagList:
            tagList.append( 'PJesus' )
            numAddedJesus += 1
            madeChanges = True
        if ('Holy' in srGlossWords or 'Spirit' in srGlossWords) and 'PHoly_Spirit' not in tagList:
            tagList.append( 'PHoly_Spirit' )
            numAddedHolySpirit += 1
            madeChanges = True

        if madeChanges:
            rowFields[TAG_COLUMN_NUMBER] = ';'.join( tagList )
            newLine = '\t'.join( rowFields )
            assert newLine.count( '\t' ) == 11, f"{newLine.count(TAB)} {newLine=}"
            state.newTable[n] = newLine

    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  {numAddedGod=:,} {numAddedJesus=:,} {numAddedHolySpirit=:,} Total added={numAddedGod+numAddedJesus+numAddedHolySpirit:,}" )
    return True
# end of add_tags_to_NT_word_table.tag_trinity_persons


def tag_referents_from_macula_data() -> bool:
    """
    Using the Referent field from the Clear.Bible Macula Greek data
        (already loaded from a TSV file preprocessed by our convert_ClearMaculaNT_to_TSV.py)
        add referent tags to our existing table.

    Note that we are using the SR-GNT
        and Clear used the Nestle 1904,
        so some matches won't fit.

    Note also that our table includes variant words (unused in the SR-GNT),
        so we have to also take account of that.
    """
    # global DEBUGGING_THIS_MODULE
    # DEBUGGING_THIS_MODULE = 99
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, "\nAssociating Macula referents with our table entries…" )

    # First make a book index into our table (for greater search efficiency down below)
    lastBBB = None
    ourBBBIndex = {}
    for p,ourRowStr in enumerate( state.newTable[1:], start=1 ):
        BBB = ourRowStr[:3]
        if BBB != lastBBB:
            if lastBBB is not None:
                ourBBBIndex[lastBBB] = (startIndex,p)
            startIndex = p
            lastBBB = BBB
    ourBBBIndex[BBB] = (startIndex,p)

    assert state.macula_tsv_lines[0][0] == 'FGRef' # Check our index value of 0
    assert state.macula_tsv_lines[0][3] == 'Word' # Check our index value of 3
    assert state.macula_tsv_lines[0][5] == 'WordClass' # Check our index value of 5
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
            dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"  {referentWordID} ({maculaRowList[5]}) '{referentGreek}' ({len(referentIDs)}) {referentIDs}")
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
                referredWordID, referredGreekWord = state.macula_tsv_lines[m][0], state.macula_tsv_lines[m][3]
                # We expect that the referredWordID is BEFORE the referentWordID
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"    {referentWordID=} {referentGreek=} {referredWordID=} {referredGreekWord=}")

                # Find the parts of our table for this verse / verses
                referentVerseID, referredVerseID = referentWordID.split('w')[0], referredWordID.split('w')[0]
                ourReferentVerseRowIndices, ourReferredVerseRowIndices = [], []
                for p,ourRowStr in enumerate( state.newTable[bookStartIndex:bookEndIndex], start=bookStartIndex ):
                    if ourRowStr.startswith( f'{referredVerseID}w' ):
                        # print( f"  to REFERRED {p} {ourRowStr}" )
                        ourReferredVerseRowIndices.append( p )
                    if ourRowStr.startswith( f'{referentVerseID}w' ):
                        # print( f"  fr REFERENT {p} {ourRowStr}" )
                        ourReferentVerseRowIndices.append( p )

                # First try to find our referent Greek word
                possibleReferentRowIndices = []
                for p in ourReferentVerseRowIndices:
                    rowItems = state.newTable[p].split( '\t' )
                    if rowItems[1] == referentGreek:
                        # print( f"  REFERENT {p} {rowItems}" )
                        possibleReferentRowIndices.append( p )
                dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"    Found {len(possibleReferentRowIndices)}/{len(ourReferentVerseRowIndices)} referent verse row(s) that might match {referentWordID} '{referentGreek}'")

                # Now try to find the referred Greek word
                possibleReferredRowIndices = []
                for p in ourReferredVerseRowIndices:
                    rowItems = state.newTable[p].split( '\t' )
                    if rowItems[1] == referredGreekWord:
                        # print( f"  REFERRED {p} {rowItems}" )
                        possibleReferredRowIndices.append( p )
                dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"    Found {len(possibleReferredRowIndices)}/{len(ourReferredVerseRowIndices)} referred verse row(s) that might match {referentWordID} '{referredGreekWord}'")
                
                if not possibleReferredRowIndices: # have a second attempt
                    for p in ourReferredVerseRowIndices:
                        rowItems = state.newTable[p].split( '\t' )
                        if rowItems[1][:3] == referredGreekWord[:3]: # Last letters might be different?
                            # print( f"  REFERRED {p} {rowItems}" )
                            possibleReferredRowIndices.append( p )
                        # else: print( f"{rowItems[1][:4]} != {referredGreekWord[:4]}")
                    dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"    Loosely found {len(possibleReferredRowIndices)} referred verse row(s) that might match {referentWordID} '{referredGreekWord}'")

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
                    existingReferentRowStr = state.newTable[referrentRowIndex]
                    existingReferredRowStr = state.newTable[referredRowIndex]

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
                    state.newTable[possibleReferentRowIndices[ixReferent]] = newLine
                    existingReferredRowFields[TAG_COLUMN_NUMBER] = ';'.join( existingReferredRowTags )
                    newLine = '\t'.join( existingReferredRowFields )
                    assert newLine.count( '\t' ) == 11, f"{newLine.count(TAB)} {newLine=}"
                    state.newTable[possibleReferredRowIndices[ixReferred]] = newLine
                # end of appendNewTags function

                if not possibleReferentRowIndices:
                    dPrint( 'Info', DEBUGGING_THIS_MODULE, f"    <<< Unable to find referent {referentVerseID} '{referentGreek}' in {len(possibleReferentRowIndices)} rows >>>")
                    for p in ourReferentVerseRowIndices:
                        dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"       {state.newTable[p].split( TAB )}" )
                elif not possibleReferredRowIndices:
                    dPrint( 'Info', DEBUGGING_THIS_MODULE, f"    <<< Unable to find referred {referredVerseID} '{referredGreekWord}' in {len(possibleReferredRowIndices)} rows >>>")
                    for p in ourReferredVerseRowIndices:
                        dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"       {state.newTable[p].split( TAB )}" )

                elif len(possibleReferentRowIndices)==1 and len(possibleReferredRowIndices)==1: # This is the easiest case
                    appendNewTags( ixReferent=0, ixReferred=0 )
                elif len(possibleReferredRowIndices) == 1: # we know where we're going
                    assert len(possibleReferentRowIndices) > 1 # but don't know where we're coming from (yet)
                    referentWordNumber = int( referentWordID.split('w')[-1] )
                    possibleWordNumbers = []
                    for p in possibleReferentRowIndices:
                        dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"       {state.newTable[p].split( TAB )}" )
                        possibleWordNumbers.append( int( state.newTable[p].split(TAB)[0].split('w')[-1] ) )
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
                        dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"       {state.newTable[p].split( TAB )}" )
                        possibleWordNumbers.append( int( state.newTable[p].split(TAB)[0].split('w')[-1] ) )
                    wordNumberDistances = [abs(referredWordNumber-possibleWordNumber) for possibleWordNumber in possibleWordNumbers]
                    minWordNumberDistance = min( wordNumberDistances )
                    dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"      Have {referredWordNumber=} and {possibleWordNumbers=} giving {wordNumberDistances=} with {minWordNumberDistance=}")
                    if wordNumberDistances.count( minWordNumberDistance ) == 1: # only one has this minimum distance
                        appendNewTags( ixReferent=0, ixReferred=wordNumberDistances.index( minWordNumberDistance ) )
                else:
                    assert len(possibleReferentRowIndices)>1 and len(possibleReferredRowIndices)>1 # both!
                    # if len(possibleReferentRowIndices) != 1:
                    #     for p in possibleReferentRowIndices:
                    #         print( f"       {state.newTable[p].split( TAB )}" )
                    # if len(possibleReferredRowIndices) != 1:
                    #     for p in possibleReferredRowIndices:
                    #         print( f"       {state.newTable[p].split( TAB )}" )
                    referentWordNumber = int( referentWordID.split('w')[-1] )
                    possibleWordNumbers = []
                    for p in possibleReferentRowIndices:
                        dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"       {state.newTable[p].split( TAB )}" )
                        possibleWordNumbers.append( int( state.newTable[p].split(TAB)[0].split('w')[-1] ) )
                    wordNumberDistances = [abs(referentWordNumber-possibleWordNumber) for possibleWordNumber in possibleWordNumbers]
                    minWordNumberDistance = min( wordNumberDistances )
                    dPrint( 'Info', DEBUGGING_THIS_MODULE, f"      Have {referentWordNumber=} and {possibleWordNumbers=} giving {wordNumberDistances=} with {minWordNumberDistance=}")
                    if wordNumberDistances.count( minWordNumberDistance ) == 1: # only one has this minimum distance
                        ixReferent = wordNumberDistances.index( minWordNumberDistance )

                    referredWordNumber = int( referredWordID.split('w')[-1] )
                    possibleWordNumbers = []
                    for p in possibleReferredRowIndices:
                        dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"       {state.newTable[p].split( TAB )}" )
                        possibleWordNumbers.append( int( state.newTable[p].split(TAB)[0].split('w')[-1] ) )
                    wordNumberDistances = [abs(referredWordNumber-possibleWordNumber) for possibleWordNumber in possibleWordNumbers]
                    minWordNumberDistance = min( wordNumberDistances )
                    dPrint( 'Info', DEBUGGING_THIS_MODULE, f"      Have {referredWordNumber=} and {possibleWordNumbers=} giving {wordNumberDistances=} with {minWordNumberDistance=}")
                    if wordNumberDistances.count( minWordNumberDistance ) == 1: # only one has this minimum distance
                        ixReferred = wordNumberDistances.index( minWordNumberDistance )

                    try: # will fail if both ixReferent and ixReferred are not declared
                        appendNewTags( ixReferent, ixReferred )
                    except UnboundLocalError:
                        logging.critical( f"Unable to find a referent and a referrer row for {referentWordID=} {referentGreek=} {referredWordID=} {referredGreekWord=}" )
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
# end of add_tags_to_NT_word_table.tag_referents_from_macula_data


def write_new_table() -> bool:
    """
    Write the new TSV table (with an extra Tags column)
        using the data in state.newTable.
    """
    assert len(state.newTable) == EXPECTED_WORD_TABLE_DATA_ROW_COUNT+1, f"{EXPECTED_WORD_TABLE_DATA_ROW_COUNT=} {len(state.newTable)}"
    
    with open( WORD_TABLE_OUTPUT_FILEPATH, 'wt', encoding='utf-8' ) as new_table_output_file:
        for line in state.newTable:
            assert line.count( '\t' ) == 11, f"{line.count(TAB)} {line=}"
            new_table_output_file.write( f'{line}\n' )
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"Wrote {len(state.newTable):,} lines to {WORD_TABLE_OUTPUT_FILEPATH} ({state.newTable[0].count(TAB)+1} columns).")

    # Also use the same word file for the OET-RV
    shutil.copy2( WORD_TABLE_OUTPUT_FILEPATH, RV_ESFM_OUTPUT_FOLDERPATH.joinpath( WORD_TABLE_OUTPUT_FILENAME ) )
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"Also copied {WORD_TABLE_OUTPUT_FILENAME} to {RV_ESFM_OUTPUT_FOLDERPATH}.")

    return True
# end of add_tags_to_NT_word_table.write_new_table



if __name__ == '__main__':
    # from multiprocessing import freeze_support
    # freeze_support() # Multiprocessing support for frozen Windows executables

    # Configure basic Bible Organisational System (BOS) set-up
    parser = BibleOrgSysGlobals.setup( SHORT_PROGRAM_NAME, PROGRAM_VERSION, LAST_MODIFIED_DATE )
    BibleOrgSysGlobals.addStandardOptionsAndProcess( parser )

    main()

    BibleOrgSysGlobals.closedown( PROGRAM_NAME, PROGRAM_VERSION )
# end of add_tags_to_NT_word_table.py
