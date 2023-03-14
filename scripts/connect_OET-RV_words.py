#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# connect_OET-RV_words.py
#
# Script to take the OET-RV NT USFM files and convert to HTML
#
# Copyright (C) 2023 Robert Hunt
# Author: Robert Hunt <Freely.Given.org@gmail.com>
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
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
"""
from gettext import gettext as _
from tracemalloc import start
from typing import List, Tuple, Optional
from pathlib import Path
from datetime import datetime
import logging
import re

if __name__ == '__main__':
    import sys
    sys.path.insert( 0, '../../BibleOrgSys/' )
from BibleOrgSys import BibleOrgSysGlobals
from BibleOrgSys.BibleOrgSysGlobals import vPrint, fnPrint, dPrint
from BibleOrgSys.Bible import Bible
from BibleOrgSys.Reference.BibleBooksCodes import BOOKLIST_OT39, BOOKLIST_NT27, BOOKLIST_66
from BibleOrgSys.Reference.BibleOrganisationalSystems import BibleOrganisationalSystem
from BibleOrgSys.Formats.ESFMBible import ESFMBible


LAST_MODIFIED_DATE = '2023-03-14' # by RJH
SHORT_PROGRAM_NAME = "connect_OET-RV_words"
PROGRAM_NAME = "Convert OET-RV words to OET-LV word numbers"
PROGRAM_VERSION = '0.04'
PROGRAM_NAME_VERSION = '{} v{}'.format( SHORT_PROGRAM_NAME, PROGRAM_VERSION )

DEBUGGING_THIS_MODULE = False


project_folderpath = Path(__file__).parent.parent # Find folders relative to this module
FG_folderpath = project_folderpath.parent # Path to find parallel Freely-Given.org repos
OET_LV_OT_USFM_InputFolderPath = project_folderpath.joinpath( 'intermediateTexts/auto_edited_OT_USFM/' )
OET_LV_NT_ESFM_InputFolderPath = project_folderpath.joinpath( 'intermediateTexts/auto_edited_VLT_ESFM/' )
OET_RV_ESFM_FolderPath = project_folderpath.joinpath( 'translatedTexts/ReadersVersion/' )
assert OET_LV_OT_USFM_InputFolderPath.is_dir()
assert OET_LV_NT_ESFM_InputFolderPath.is_dir()
assert OET_RV_ESFM_FolderPath.is_dir()

# EN_SPACE = ' '
EM_SPACE = ' '
NARROW_NON_BREAK_SPACE = ' '
BACKSLASH = '\\'


class State:
    """
    A place to store some of the global stuff that needs to be passed around.
    """
    simpleNouns = ( # These are nouns that are likely to match one-to-one from the OET-LV to the OET-RV
                    #   i.e., there's really no other word for them.
        'boat','boats', 'camel','camels',
        'daughter', 'donkey','donkeys', 'father', 'fish', 'foot','feet', 'goat','goats',
        'hand','hands', 'honey', 'house','houses', 'lion','lions', 'locusts', 'mother', 'sea', 'sheep')
# end of State class

state = State()


def main():
    """
    Main program to handle command line parameters and then run what they want.
    """
    BibleOrgSysGlobals.introduceProgram( __name__, PROGRAM_NAME_VERSION, LAST_MODIFIED_DATE )

    # global genericBookList
    # genericBibleOrganisationalSystem = BibleOrganisationalSystem( 'GENERIC-KJV-ENG' )
    # genericBookList = genericBibleOrganisationalSystem.getBookList()

    rv = ESFMBible( OET_RV_ESFM_FolderPath, givenAbbreviation='OET-RV' )
    rv.loadAuxilliaryFiles = True
    rv.loadBooks() # So we can iterate through them all later
    rv.lookForAuxilliaryFilenames()
    dPrint( 'Normal', DEBUGGING_THIS_MODULE, f"{rv=}")

    lv = ESFMBible( OET_LV_NT_ESFM_InputFolderPath, givenAbbreviation='OET-LV' )
    lv.loadAuxilliaryFiles = True
    lv.loadBooks() # So we can iterate through them all later
    lv.lookForAuxilliaryFilenames()
    dPrint( 'Normal', DEBUGGING_THIS_MODULE, f"{lv=}")

    # Convert files to simple HTML
    connect_OET_RV( rv, lv )
# end of connect_OET-RV_words.main


def connect_OET_RV( rv, lv ):
    """
    """
    fnPrint( DEBUGGING_THIS_MODULE, f"connect_OET_RV( {rv}, {lv} )" )
    for BBB,bookObject in lv.books.items():
        vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"Processing {}" )

        wordFileName = bookObject.ESFMWordTableFilename
        if wordFileName:
            assert wordFileName.endswith( '.tsv' )
            vPrint( 'Info', DEBUGGING_THIS_MODULE, f"  Found ESFMBible filename '{wordFileName}' for {lv.abbreviation} {BBB}" )
            vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Found ESFMBible loaded word links: {lv.ESFMWordTables[wordFileName]}" )
            if lv.ESFMWordTables[wordFileName] is None:
                with open( OET_LV_NT_ESFM_InputFolderPath.joinpath(wordFileName), 'rt', encoding='UTF-8' ) as wordFile:
                    lv.ESFMWordTables[wordFileName] = wordFile.read().split( '\n' )
                vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  connect_OET_RV loaded {len(lv.ESFMWordTables[wordFileName]):,} total rows from {wordFileName}" )
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  connect_OET_RV loaded column names were: ({len(lv.ESFMWordTables[wordFileName][0])}) {lv.ESFMWordTables[wordFileName][0]}" )
        state.wordTable = lv.ESFMWordTables[wordFileName]
        state.tableHeaderList = state.wordTable[0].split( '\t' )

        rvESFMFilename = f'OET-RV_{BBB}.ESFM'
        rvESFMFilepath = OET_RV_ESFM_FolderPath.joinpath( rvESFMFilename )
        with open( rvESFMFilepath, 'rt', encoding='UTF-8' ) as esfmFile:
            state.esfmText = esfmFile.read() # We keep the original (for later comparison)
            state.esfmLines = state.esfmText.split( '\n' )

        numChapters = lv.getNumChapters( BBB )
        if numChapters >= 1:
            for c in range( 1, numChapters+1 ):
                vPrint( 'Info', DEBUGGING_THIS_MODULE, f"      Connecting words for {BBB} {c}…" )
                numVerses = lv.getNumVerses( BBB, c )
                if numVerses is None: # something unusual
                    logging.critical( f"connect_OET_RV: no verses found for OET-LV {BBB} {c}" )
                    continue
                for v in range( 1, numVerses+1 ):
                    try:
                        rvVerseEntryList, _rvCcontextList = rv.getContextVerseData( (BBB, str(c), str(v)) )
                        lvVerseEntryList, _lvCcontextList = lv.getContextVerseData( (BBB, str(c), str(v)) )
                    except KeyError:
                        logging.critical( f"Seems we have no {BBB} {c}:{v} -- versification issue?" )
                        continue
                    # dPrint( 'Info', DEBUGGING_THIS_MODULE, f"RV entries: ({len(rvVerseEntryList)}) {rvVerseEntryList}")
                    # dPrint( 'Info', DEBUGGING_THIS_MODULE, f"LV entries: ({len(lvVerseEntryList)}) {lvVerseEntryList}")
                    connect_OET_RV_Verse( BBB, c, v, rvVerseEntryList, lvVerseEntryList )
        else:
            dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"connect_OET_RV {BBB} has {numChapters} chapters!!!" )
            assert BBB in ('INT','FRT',)

        newESFMtext = '\n'.join( state.esfmLines )
        if newESFMtext != state.esfmText:
            dPrint( 'Normal', DEBUGGING_THIS_MODULE, f"{BBB} ESFM text has changed {len(state.esfmText)} -> {len(newESFMtext)}" )
            with open( rvESFMFilepath, 'wt', encoding='UTF-8' ) as esfmFile:
                esfmFile.write( newESFMtext )
            vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Saved OET-RV {BBB} {len(newESFMtext):,} bytes to {rvESFMFilepath}" )
        else:
            vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  No changes made to OET-RV {BBB}." )
# end of connect_OET-RV_words.connect_OET_RV


def connect_OET_RV_Verse( BBB:str, c:int,v:int, rvEntryList, lvEntryList ):
    """
    """
    # fnPrint( DEBUGGING_THIS_MODULE, f"connect_OET_RV( {BBB} {c}:{v} {len(rvEntryList)}, {len(lvEntryList)} )" )

    rvText = ''
    for rvEntry in rvEntryList:
        rvMarker,rvRest = rvEntry.getMarker(), rvEntry.getCleanText()
        if rvMarker in ('v~','p~'):
            rvText = f"{rvText}{' ' if rvText else ''}{rvRest}"
    lvText = ''
    for lvEntry in lvEntryList:
        lvMarker,lvRest = lvEntry.getMarker(), lvEntry.getCleanText()
        if lvMarker in ('v~','p~'):
            lvText = f"{lvText}{' ' if lvText else ''}{lvRest.replace('+','')}"
    if not rvText or not lvText: return
    rvAdjText = rvText.replace('≈','') \
                .replace('.','').replace(',','').replace(':','').replace('—',' ').strip()
    lvAdjText = lvText.replace('_',' ') \
                .replace('.','').replace(',','').replace(':','').replace('  ',' ').strip()
    # print( f"({len(rvAdjText)}) {rvAdjText=}")
    # print( f"({len(lvAdjText)}) {lvAdjText=}")
    if not rvAdjText or not lvAdjText: return
    rvWords = rvAdjText.split( ' ' )
    lvWords = lvAdjText.split( ' ' )
    # print( f"({len(rvWords)}) {rvWords=}")
    # print( f"({len(lvWords)}) {lvWords=}")
    assert rvWords
    assert lvWords
    for rvWord in rvWords:
        assert rvWord.count( '¦' ) <= 1 # Check that we haven't been retagging already tagged RV words
    matchSimpleNouns( BBB, c,v, rvWords, lvWords )

    # Now get the uppercase words
    rvUpperWords = [rvWord for rvWord in rvWords if rvWord[0].isupper()]
    lvUpperWords = [lvWord for lvWord in lvWords if lvWord[0].isupper()]
    # print( f"'{rvText}' '{lvText}'" )
    if rvText[0].isupper(): rvUpperWords.pop(0) # Throw away the first word
    if lvText[0].isupper(): lvUpperWords.pop(0) # Throw away the first word
    # print( f"({len(rvUpperWords)}) {rvUpperWords}")
    # print( f"({len(lvUpperWords)}) {lvUpperWords}")
    if rvUpperWords and lvUpperWords:
        matchProperNouns( BBB, c,v, rvUpperWords, lvUpperWords )
# end of connect_OET-RV_words.connect_OET_RV_Verse


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
def matchProperNouns( BBB:str, c:int,v:int, rvCapitalisedWordList:List[str], lvCapitalisedWordList:List[str] ):
    """
    """
    fnPrint( DEBUGGING_THIS_MODULE, f"matchProperNouns( {BBB} {c}:{v} {rvCapitalisedWordList}, {lvCapitalisedWordList} )" )
    assert rvCapitalisedWordList and lvCapitalisedWordList

    # But we don't want any rvWords that are already tagged
    for rvN,rvCapitalisedWord in enumerate( rvCapitalisedWordList[:] ):
        if '¦' in rvCapitalisedWord:
            _rvCapitalisedWord, rvWordNumber = rvCapitalisedWord.split('¦')
            dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  matchProperNouns( {BBB} {c}:{v} ) removing already tagged '{rvCapitalisedWord}' from RV list")
            rvCapitalisedWordList.pop( rvN )
            for lvN,lvCapitalisedWord in enumerate( lvCapitalisedWordList[:] ):
                if lvCapitalisedWord.endswith( f'¦{rvWordNumber}' ):
                    dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  matchProperNouns( {BBB} {c}:{v} ) removing already tagged '{lvCapitalisedWord}' from LV list")
                    lvCapitalisedWordList.pop( lvN )
    if not rvCapitalisedWordList or not lvCapitalisedWordList:
        return # nothing left to do here

    if len(rvCapitalisedWordList)==1 and len(lvCapitalisedWordList)==1: # easy case!
        assert rvCapitalisedWordList[0].replace("'",'').isalpha(), f"{rvCapitalisedWordList=}" # It might contain an apostrophe
        capitalisedNoun,wordNumber,wordRow = getLVWordRow( lvCapitalisedWordList[0] )
        wordRole = wordRow[state.tableHeaderList.index('Role')]
        dPrint( 'Info', DEBUGGING_THIS_MODULE, f"'{capitalisedNoun}' {wordRole}" )
        if wordRole == 'N': # let's assume it's a proper noun
            addNumberToRVWord( BBB, c,v, rvCapitalisedWordList[0], wordNumber )
    elif len(rvCapitalisedWordList) == len(lvCapitalisedWordList):
        dPrint( 'Info', DEBUGGING_THIS_MODULE, f"Lists are equal size ({len(rvCapitalisedWordList)})" )
        return
        for capitalisedNounPair in lvCapitalisedWordList:
            capitalisedNoun,wordNumber,wordRow = getLVWordRow( capitalisedNounPair )
            dPrint( 'Info', f"'{capitalisedNoun}' {wordRow}" )
            halt
    else:
        dPrint( 'Info', DEBUGGING_THIS_MODULE, f"Lists are different sizes {len(rvCapitalisedWordList)=} and {len(lvCapitalisedWordList)=}" )
        return
        for capitalisedNounPair in lvCapitalisedWordList:
            capitalisedNoun,wordNumber,wordRow = getLVWordRow( capitalisedNounPair )
            dPrint( 'Info', f"'{capitalisedNoun}' {wordRow}" )
            halt
# end of connect_OET-RV_words.matchProperNouns


def matchSimpleNouns( BBB:str, c:int,v:int, rvWordList:List[str], lvWordList:List[str] ):
    """
    """
    fnPrint( DEBUGGING_THIS_MODULE, f"matchSimpleNouns( {BBB} {c}:{v} {rvWordList}, {lvWordList} )" )
    assert rvWordList and lvWordList

    for simpleNoun in state.simpleNouns:
        # print( f"{simpleNoun}" )
        lvIndexList = []
        for lvN,lvWord in enumerate( lvWordList ):
            # assert lvWord.isalpha(), f"'{lvWord}'" # Might contain an apostrophe
            if f'{simpleNoun}¦' in lvWord:
                lvIndexList.append( lvN )
        if not lvIndexList: continue
        # print( f"{BBB} {c}:{v} {simpleNoun=} {lvIndexList=}" )
        rvIndexList = []
        for rvN,rvWord in enumerate( rvWordList ):
            # assert rvWord.isalpha(), f"'{rvWord}'" # Might contain an apostrophe
            if rvWord == simpleNoun:
                rvIndexList.append( rvN )
        if not rvIndexList: continue

        if len(rvIndexList) != 1 or len(lvIndexList) != 1: # then I don't think we can guarantee matching the right words
            return
        assert len(rvIndexList) == len(lvIndexList), f"{BBB} {c}:{v} {simpleNoun=} {rvIndexList=} {lvIndexList=}"

        lvNumbers = []
        for lvN in lvIndexList:
            lvNoun,lvWordNumber,lvWordRow = getLVWordRow( lvWordList[lvN] )
            lvNumbers.append( lvWordNumber )
        assert len(lvNumbers) == 1 # NOT TRUE: If there's two 'camels' in the verse, we expect both to have the same word number
        for rvN in rvIndexList:
            rvNoun = rvWordList[rvN]
            dPrint( 'Info', DEBUGGING_THIS_MODULE, f"matchSimpleNouns() is adding a number to RV '{rvNoun}' at {BBB} {c}:{v} {rvN=}")
            addNumberToRVWord( BBB, c,v, rvNoun, lvWordNumber )
# end of connect_OET-RV_words.matchSimpleNouns


def getLVWordRow( wordWithNumber:str ) -> Tuple[str,int,List[str]]:
    """
    """
    fnPrint( DEBUGGING_THIS_MODULE, f"getLVWordRow( {wordWithNumber} )" )

    word,wordNumber = wordWithNumber.split( '¦' )
    # assert word.isalpha(), f"Non-alpha '{word}'" # not true, e.g., from 'Yaʸsous/(Yəhōshūˊa)¦21754'
    wordNumber = int( wordNumber )
    wordRow = state.wordTable[wordNumber].split( '\t' )
    dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"'{word}' {wordRow}" )
    return word,wordNumber,wordRow
# end of connect_OET-RV_words.getLVWordRow


def addNumberToRVWord( BBB:str, c:int,v:int, word:str, wordNumber:int ) -> bool:
    """
    """
    fnPrint( DEBUGGING_THIS_MODULE, f"addNumberToRVWord( {BBB} {c}:{v} '{word}' {wordNumber} )" )

    C = V = None
    found = False
    for n,line in enumerate( state.esfmLines[:] ): # iterate through a copy
        try: marker, rest = line.split( ' ', 1 )
        except ValueError: marker, rest = line, '' # Only a marker
        # print( f"{marker}='{rest}'" )
        if marker == '\\c': C = int(rest)
        elif marker == '\\v':
            Vstr, rest = rest.split( ' ', 1 )
            try: V = int(Vstr)
            except ValueError: # might be a range like 21-22
                V = int(Vstr.split('-',1)[0])
            found = C==c and V==v
            if found:
                dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"addNumberToRVWord() found {BBB} {C}:{V}" )
                assert word in rest
                if rest.count( word ) > 1:
                    return False
                assert rest.count( word ) == 1, f"'{word}' {rest.count(word)} '{rest}'"
                if f'{word}¦' not in rest:
                    state.esfmLines[n] = line.replace( word, f'{word}¦{wordNumber}' )
                    dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"  addNumberToRVWord() added ¦{wordNumber} to '{word}' in OET-RV {BBB} {c}:{v}" )
                    return True
                else: oops
# end of connect_OET-RV_words.addNumberToRVWord


if __name__ == '__main__':
    # Configure basic Bible Organisational System (BOS) set-up
    parser = BibleOrgSysGlobals.setup( PROGRAM_NAME, PROGRAM_VERSION )
    BibleOrgSysGlobals.addStandardOptionsAndProcess( parser, exportAvailable=False )

    main()

    BibleOrgSysGlobals.closedown( PROGRAM_NAME, PROGRAM_VERSION )
# end of connect_OET-RV_words.py
