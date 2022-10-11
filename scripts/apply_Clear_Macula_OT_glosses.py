#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# apply_Clear_Macula_OT_glosses.py
#
# Script handling apply_Clear_Macula_OT_glosses functions
#
# Copyright (C) 2022 Robert Hunt
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
Script taking our expanded OSHB morpheme table (TSV)
    and filling columns with Clear.Bible low-fat and/or Cherith glosses.

(This is run AFTER convert_OSHB_XML_to_TSV.py
    and then AFTER prepare_OSHB_for_glossing.py.)

OSHB morphology codes can be found at https://hb.openscriptures.org/parsing/HebrewMorphologyCodes.html.
"""
from gettext import gettext as _
from typing import Dict, List, Tuple
from pathlib import Path
from csv import DictReader, DictWriter
from collections import defaultdict
from datetime import datetime
import logging
from pprint import pprint
from xml.etree import ElementTree

if __name__ == '__main__':
    import sys
    sys.path.insert( 0, '../../BibleOrgSys/' )
from BibleOrgSys import BibleOrgSysGlobals
from BibleOrgSys.BibleOrgSysGlobals import vPrint, fnPrint, dPrint
from BibleOrgSys.OriginalLanguages import Hebrew
# from BibleOrgSys.OriginalLanguages import HebrewWLCBible


LAST_MODIFIED_DATE = '2022-10-11' # by RJH
SHORT_PROGRAM_NAME = "apply_Clear_Macula_OT_glosses"
PROGRAM_NAME = "Extract and Apply Macula OT glosses"
PROGRAM_VERSION = '0.42'
PROGRAM_NAME_VERSION = f'{SHORT_PROGRAM_NAME} v{PROGRAM_VERSION}'

DEBUGGING_THIS_MODULE = False


TSV_INPUT_OUTPUT_FILEPATH = Path( '../intermediateTexts/glossed_OSHB/WLC_glosses.morphemes.tsv' )
CHERITH_TSV_INPUT_FILEPATH = Path( '../../Forked/macula-hebrew/sources/Cherith/glosses/wlc-gloss.tsv' )
LOWFAT_XML_INPUT_FOLDERPATH = Path( '../../Forked/macula-hebrew/lowfat/' )
LOWFAT_XML_FILENAME_TEMPLATE = 'NN-Uuu-CCC-lowfat.xml' # e.g., 01-Gen-001-lowfat.xml


state = None
class State:
    def __init__( self ) -> None:
        """
        Constructor:
        """
        self.TSV_input_output_filepath = TSV_INPUT_OUTPUT_FILEPATH
        self.Cherith_TSV_input_filepath = CHERITH_TSV_INPUT_FILEPATH
        self.lowfat_XML_input_folderpath = LOWFAT_XML_INPUT_FOLDERPATH
        self.WLC_rows = []
        self.Cherith_rows = []
        self.lowFatWordsAndMorphemeTuples = []
    # end of apply_Clear_Macula_OT_glosses.__init__


NUM_EXPECTED_WLC_COLUMNS = 16
WLC_tsv_column_max_length_counts = {}
WLC_tsv_column_non_blank_counts = {}
WLC_tsv_column_counts = defaultdict(lambda: defaultdict(int))
WLC_tsv_column_headers = []

NUM_EXPECTED_CHERITH_COLUMNS = 4 # e.g., 010010010012    רֵאשִׁית   beginning       起初
Cherith_tsv_column_max_length_counts = {}
Cherith_tsv_column_non_blank_counts = {}
Cherith_tsv_column_counts = defaultdict(lambda: defaultdict(int))
Cherith_tsv_column_headers = ['numID','WLC_word_or_morpheme','English_gloss','Chinese_gloss'] # Has no headers in the file


def main() -> None:
    """
    """
    BibleOrgSysGlobals.introduceProgram( __name__, PROGRAM_NAME_VERSION, LAST_MODIFIED_DATE )
    global state
    state = State()

    if loadOurSourceTable():
        if loadLowFatGlosses():
            # if loadCherithGlossTable() and prepass_on_Cherith_rows() and compareSomeGlosses(): # Yes, English in lowFat matches Cherith glosses
                if fill_known_lowFat_English_contextual_glosses():
                # if fill_known_Cherith_English_contextual_glosses(): # these are inferior
                    save_filled_TSV_file()
# end of apply_Clear_Macula_OT_glosses.main


def loadOurSourceTable() -> bool:
    """
    """
    global WLC_tsv_column_headers
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"\nLoading our WLC tsv file from {state.TSV_input_output_filepath}…")
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  Expecting {NUM_EXPECTED_WLC_COLUMNS} columns…")
    with open(state.TSV_input_output_filepath, 'rt', encoding='utf-8') as tsv_file:
        tsv_lines = tsv_file.readlines()

    # Remove BOM
    if tsv_lines[0].startswith("\ufeff"):
        vPrint( 'Quiet', DEBUGGING_THIS_MODULE, "  Handling Byte Order Marker (BOM) at start of our WLC tsv file…")
        tsv_lines[0] = tsv_lines[0][1:]

    # Get the headers before we start
    WLC_tsv_column_headers = [header for header in tsv_lines[0].strip().split('\t')]
    dPrint('Info', DEBUGGING_THIS_MODULE, f"Column headers: ({len(WLC_tsv_column_headers)}): {WLC_tsv_column_headers}")
    assert len(WLC_tsv_column_headers) == NUM_EXPECTED_WLC_COLUMNS

    # Read, check the number of columns, and summarise row contents all in one go
    dict_reader = DictReader(tsv_lines, delimiter='\t')
    unique_morphemes, unique_words = set(), set()
    note_count = seg_count = 0
    assembled_word = ''
    for n, row in enumerate(dict_reader):
        if len(row) != NUM_EXPECTED_WLC_COLUMNS:
            logging.error(f"Line {n} has {len(row)} columns instead of {NUM_EXPECTED_WLC_COLUMNS}!!!")
        state.WLC_rows.append(row)
        row_type = row['Type']
        if row_type != 'm' and assembled_word:
            dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"{assembled_word=}")
            unique_words.add(assembled_word)
            assembled_word = ''
        if row_type == 'seg':
            seg_count += 1
        elif row_type.endswith('note'):
            note_count += 1
        elif row_type in ('w','Aw','wK','AwK'): # w=word, A=Aramaic (rather than Hebrew), K=Ketiv
            unique_words.add(row['WordOrMorpheme'])
        elif row_type in ('m','M','Am','AM','mK','MK','AmK','AMK'): # m=morpheme, M=last morpheme in word, A=Aramaic (rather than Hebrew), K=Ketiv
            unique_morphemes.add(row['WordOrMorpheme'])
            assembled_word = f"{assembled_word}{row['WordOrMorpheme']}"
        else: vPrint( 'Quiet', DEBUGGING_THIS_MODULE, row_type); unexpected_row_type
        for key, value in row.items():
            # WLC_tsv_column_sets[key].add(value)
            if n==0: # We do it like this (rather than using a defaultdict(int)) so that all fields are entered into the dict in the correct order
                WLC_tsv_column_max_length_counts[key] = 0
                WLC_tsv_column_non_blank_counts[key] = 0
            if value:
                if len(value) > WLC_tsv_column_max_length_counts[key]:
                    WLC_tsv_column_max_length_counts[key] = len(value)
                WLC_tsv_column_non_blank_counts[key] += 1
            WLC_tsv_column_counts[key][value] += 1
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  Loaded {len(state.WLC_rows):,} (tsv) WLC data rows.")
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"    Have {len(unique_words):,} unique Hebrew words.")
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"    Have {len(unique_morphemes):,} unique Hebrew morphemes.")
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"    Have {seg_count:,} Hebrew segment markers.")
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"    Have {note_count:,} notes.")

    return True
# end of apply_Clear_Macula_OT_glosses.loadOurSourceTable


def removeCantillationMarks( text:str, removeMetegOrSiluq=False ):
    """
    Return the text with cantillation marks removed.
    """
    #dPrint( 'Quiet', DEBUGGING_THIS_MODULE, "removeCantillationMarks( {!r}, {} )".format( text, removeMetegOrSiluq ) )
    h = Hebrew.Hebrew( text )
    return h.removeCantillationMarks( removeMetegOrSiluq=removeMetegOrSiluq )
# end of apply_Clear_Macula_OT_glosses.removeCantillationMarks


def loadCherithGlossTable() -> bool:
    """
    Load the four-column "Cherith" TSV table.
    """
    global Cherith_tsv_column_headers
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"\nLoading Clear.Bible Cherith tsv file from {state.Cherith_TSV_input_filepath}…")
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  Expecting {NUM_EXPECTED_CHERITH_COLUMNS} columns…")
    with open(state.Cherith_TSV_input_filepath, 'rt', encoding='utf-8') as tsv_file:
        tsv_lines = tsv_file.readlines()

    # Remove BOM
    if tsv_lines[0].startswith("\ufeff"):
        vPrint( 'Quiet', DEBUGGING_THIS_MODULE, "  Handling Byte Order Marker (BOM) at start of Cherith tsv file…")
        tsv_lines[0] = tsv_lines[0][1:]

    # # Get the headers before we start
    # Cherith_tsv_column_headers = [header for header in tsv_lines[0].strip().split('\t')]
    # dPrint('Info', DEBUGGING_THIS_MODULE, f"Column headers: ({len(Cherith_tsv_column_headers)}): {Cherith_tsv_column_headers}")
    # assert len(Cherith_tsv_column_headers) == NUM_EXPECTED_CHERITH_COLUMNS

    # Read, check the number of columns, and summarise row contents all in one go
    dict_reader = DictReader(tsv_lines, fieldnames=Cherith_tsv_column_headers, delimiter='\t')
    unique_morphemes = set()
    for n, row in enumerate(dict_reader):
        if len(row) != NUM_EXPECTED_CHERITH_COLUMNS:
            logging.error(f"Line {n} has {len(row)} columns instead of {NUM_EXPECTED_CHERITH_COLUMNS}!!!")
        state.Cherith_rows.append(row)
        unique_morphemes.add(row['WLC_word_or_morpheme'])
        for key, value in row.items():
            # Cherith_tsv_column_sets[key].add(value)
            if n==0: # We do it like this (rather than using a defaultdict(int)) so that all fields are entered into the dict in the correct order
                Cherith_tsv_column_max_length_counts[key] = 0
                Cherith_tsv_column_non_blank_counts[key] = 0
            if value:
                if len(value) > Cherith_tsv_column_max_length_counts[key]:
                    Cherith_tsv_column_max_length_counts[key] = len(value)
                Cherith_tsv_column_non_blank_counts[key] += 1
            Cherith_tsv_column_counts[key][value] += 1
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  Loaded {len(state.Cherith_rows):,} (tsv) Cherith data rows.")
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"    Have {len(unique_morphemes):,} unique Hebrew morphemes.")

    return True
# end of apply_Clear_Macula_OT_glosses.loadCherithGlossTable


def prepass_on_Cherith_rows() -> bool:
    """
    For prepositional suffixes with a vowel,
        Cherith put the preposition on one row,
        and then the article on the next row (with Hebrew column empty).
    We want to combine those two rows.
    """
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"\nPreprocessing TSV table with Clear.Bible {len(state.Cherith_rows):,} rows…" )

    lastCherithRow = None
    deleteList = []
    prepositionSet, articleSet = set(), set()
    for n,CherithRow in enumerate( state.Cherith_rows ):
        if ' ' in CherithRow['English_gloss']:
            assert CherithRow['English_gloss'].strip() # Check that it's not ONLY whitespace
            vPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"  Replacing space in {CherithRow['numID']} gloss '{CherithRow['English_gloss']}'" )
            CherithRow['English_gloss'] = CherithRow['English_gloss'].strip().replace( ' ', '_' )
        if not CherithRow['WLC_word_or_morpheme']:
            assert lastCherithRow
            # vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"Deleting '{CherithRow['English_gloss']}' row after '{lastCherithRow['WLC_word_or_morpheme']}' '{lastCherithRow['English_gloss']}' {CherithRow['numID']}" )
            if CherithRow['English_gloss']:
                # assert lastCherithRow['English_gloss'] in ('in','at','to','for','on','of','over','with','as','among','by','into','upon','from','so',
                #                             'through','against','such','like','alike','about','according to','same','during','whether','until','concerning','both','also',
                #                             'just as','in exchange for','because of','within','throughout','belongs to','as well as','belonging to','up to',
                #                             'such ~ as','as ~ as','had','has','each','or','') # These last ones were more unexpected
                # assert CherithRow['English_gloss'] in ('the','a','an','this','that','these','those','such','each','their','his','your')
                prepositionSet.add( lastCherithRow['English_gloss'] )
                articleSet.add( CherithRow['English_gloss'] )
                lastCherithRow['English_gloss'] = f"{lastCherithRow['English_gloss']}_{CherithRow['English_gloss']}"
            deleteList.append(n)
        lastCherithRow = CherithRow
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"({len(prepositionSet):,}) {prepositionSet=}\n({len(articleSet):,}) {articleSet=}" )

    for n in reversed( deleteList ):
        del state.Cherith_rows[n]

    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  Preprocessing returning with TSV table with Clear.Bible {len(state.Cherith_rows):,} rows")
    return True
# end of apply_Clear_Macula_OT_glosses.prepass_on_Cherith_rows


def loadLowFatGlosses() -> bool:
    """
    Extract glosses out of fields 
    Reorganise columns and add our extra columns
    """
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"\nLoading Clear.Bible 'low fat' glosses from {state.lowfat_XML_input_folderpath}/…" )
    
    # namespaces = { 'osis': 'http://www.bibletechnologies.net/2003/OSIS/namespace' }
    # namespaces = { 'xml': 'http://www.w3.org/XML/1998/namespace' }
    suffixDict = {'1':'a', '2':'b', '3':'c', '4':'d', '5':'e'} # Max of 5 morphemes in one word
    for referenceNumber in range(1, 39+1):
        BBB = BibleOrgSysGlobals.loadedBibleBooksCodes.getBBBFromReferenceNumber( referenceNumber )
        vPrint( 'Info', DEBUGGING_THIS_MODULE, f"  Loading {BBB} XML files…")
        Uuu = BibleOrgSysGlobals.loadedBibleBooksCodes.getUSFMAbbreviation( BBB )
        if Uuu=='Hos': Uuu = 'HOS' # Fix inconsistency in naming patterns
        filenameTemplate = LOWFAT_XML_FILENAME_TEMPLATE.replace( 'NN', str(referenceNumber).zfill(2) ).replace( 'Uuu', Uuu )


        for chapterNumber in range(1, 150+1):
            filename = filenameTemplate.replace( 'CCC', str(chapterNumber).zfill(3) )
            try:
                chapterTree = ElementTree.parse( state.lowfat_XML_input_folderpath.joinpath( filename ) )
            except FileNotFoundError:
                break # gone beyond the number of chapters

            # First load all the word (w) fields for the chapter into a temporary list
            tempWordsAndMorphemes = []
            longIDs = []
            for elem in chapterTree.getroot().iter():
                if elem.tag == 'w': # ignore all the others -- there's enough info in here
                    wordOrMorpheme = elem.text
                    theirRef = elem.get('ref')
                    longID = elem.get('{http://www.w3.org/XML/1998/namespace}id') # e.g., o010010050031 = obbcccvvvwwws
                    longIDs.append( longID )
                    English = elem.get('english')
                    gloss = elem.get('gloss')
                    if gloss: gloss = gloss.replace( '.', '_' ) # Change to our system
                    lang = elem.get('lang')
                    assert lang in 'HA'
                    # dPrint( 'Info', DEBUGGING_THIS_MODULE, f"    {ref} {longID} {lang} '{wordOrMorpheme}' {English=} {gloss=}")
                    if English == '.and': English = 'and' # at ISA 65:9!9
                    if English:
                        assert '.' not in English
                        assert English.strip() == English # No leading or trailing spaces
                        English = English.replace( ' ', '_' )
                    else: English = '' # Instead of None
                    assert longID.startswith( 'o' ) # What does this stand for
                    longID = longID[1:] # remove 'o' prefix
                    if len(longID) > 12: # it's an article (vowel after preposition)
                        assert len(longID) == 13
                        assert longID.endswith( 'ה' )
                        assert longID[:-1].isdigit()
                    else:
                        assert len(longID) == 12
                        assert longID[:].isdigit()
                    tempWordsAndMorphemes.append( (theirRef,longID,wordOrMorpheme,lang,English,gloss) )
            vPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"    Got {len(tempWordsAndMorphemes):,} words/morphemes in {BBB} {chapterNumber}")
            assert len(set(longIDs)) == len(longIDs), f"Should be no duplicates in {longIDs=}"

            # Note that because of the phrase/clause nesting, we can get the word fields in the wrong order
            #   so we sort them, before adjusting the formatting to what we're after
            # We sort by the Clear.Bible longID (2nd item in tuple, which already has the leading 'o' removed)
            sortedTempWordsAndMorphemes = sorted( tempWordsAndMorphemes, key=lambda t: t[1] )

            # Adjust to our references and with just the data that we need to retain
            # We reduce from six entries: theirRef, longID, wordOrMorpheme, lang, English, gloss
            #   to five: ourRef, type, wordOrMorpheme, English, gloss
            for j,sixTuple in enumerate( sortedTempWordsAndMorphemes ):
                longID = sixTuple[1]
                # if longID.startswith('01003009'): print(j, sixTuple)
                if longID.endswith( 'ה' ):  # it's an article (vowel after preposition)
                    # print(f"Got article {longID=}")
                    assert sixTuple[2] is None # No wordOrMorpheme
                    assert sixTuple[5] is None # No gloss
                    if sixTuple[4]: # English
                        lastFiveTuple = state.lowFatWordsAndMorphemeTuples.pop()
                        # Add the article gloss to the previous entry
                        newFiveTuple = lastFiveTuple[0],lastFiveTuple[1],lastFiveTuple[2],f'{lastFiveTuple[3]}_{sixTuple[4]}',lastFiveTuple[4]
                        assert len(newFiveTuple) == len(lastFiveTuple) == 5
                        state.lowFatWordsAndMorphemeTuples.append( newFiveTuple ) # Put edited entry back on
                else: # a normal word or morpheme entry
                    try: nextLongID = sortedTempWordsAndMorphemes[j+1][1]
                    except IndexError: nextLongID = '1'
                    assert nextLongID != longID, f"Should be no duplicate IDs: {j=} {longID=} {nextLongID=} {sixTuple}"
                    if nextLongID.endswith( '1' ): # current entry is end of a word
                        mwType = 'w' if longID.endswith( '1' ) else 'M'
                    else: mwType = 'm' # There's a following part of this word
                    suffix = '' if mwType=='w' else suffixDict[longID[-1]]
                    if sixTuple[3] == 'A': mwType = f'A{mwType}' # Assume Hebrew; mark Aramaic
                    ourRef = f"{BBB}_{sixTuple[0][4:].replace( '!', 'w')}{suffix}"
                    # print(f"{longID=} {nextLongID=} {mwType=} {ourRef=}")
                    state.lowFatWordsAndMorphemeTuples.append( (ourRef,mwType,sixTuple[2],sixTuple[4],sixTuple[5]) )

    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  Got total of {len(state.lowFatWordsAndMorphemeTuples):,} words/morphemes")
    return True
# end of apply_Clear_Macula_OT_glosses.loadLowFatGlosses


def compareSomeGlosses() -> bool:
    """
    Reorganise columns and add our extra columns
    """
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"\nComparing some loaded Clear.Bible 'Cherith' and 'low fat' glosses…" )

    NUM_TO_DISPLAY = 10
    for CherithRow in state.Cherith_rows[:NUM_TO_DISPLAY]:
        vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"{CherithRow}")
    for fiveTuple in state.lowFatWordsAndMorphemeTuples[:NUM_TO_DISPLAY]:
        vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"{fiveTuple}")

    for CherithRow,fiveTuple in zip( state.Cherith_rows, state.lowFatWordsAndMorphemeTuples ):
        lowFatEnglish = fiveTuple[3] if fiveTuple[3] else ''
        if CherithRow['English_gloss'] != lowFatEnglish:
            vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"Got mismatch at {CherithRow} {fiveTuple}" )
            break

    return True
# end of apply_Clear_Macula_OT_glosses.compareSomeGlosses
    

def fill_known_lowFat_English_contextual_glosses() -> bool:
    """
    Because the Hebrew accents differ from our OSHB WLC text
        vs. the Clear.Bible text, we remove accents as necessary before comparing.
    """
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, "\nPrefilling TSV table with Clear.Bible contextual English lowFat glosses…")

    num_empty_word_glosses = num_word_glosses_added = num_word_glosses_skipped = 0
    num_empty_morpheme_glosses = num_morpheme_glosses_added = num_morpheme_glosses_skipped = 0
    missing_low_fat_references, ketiv_references = [], []
    our_index = num_consecutive_mismatches = 0
    current_verse_reference = last_verse_reference = None
    ketiv_count = 0
    for theirRef,theirType,theirWordOrMorpheme,theirEnglish,theirGloss in state.lowFatWordsAndMorphemeTuples:
        dPrint( 'Info', DEBUGGING_THIS_MODULE, f"\n  {theirRef} {theirType} '{theirWordOrMorpheme}' {theirEnglish=} {theirGloss=}" )

        if theirRef.startswith('EZE_42:9'): # This verse is a mess
            our_index += 1
            continue

        useGloss = theirGloss if theirGloss else theirEnglish
        useGloss = useGloss.replace('(dm)','DOM').replace('(et)','DOM') # Tidy up some inconsistences
        if not useGloss:
            if ourRow['Type'] in ('w','Aw','wK','AwK'):
                vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"    Have no lowfat word gloss for {ourRow['Ref']} '{ourRow['WordOrMorpheme']}' gloss '{ourRow['ContextualWordGloss']}'" )
                num_empty_word_glosses += 1
            else:
                vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"    Have no lowfat morpheme gloss for {ourRow['Ref']} '{ourRow['WordOrMorpheme']}' gloss '{ourRow['ContextualMorphemeGloss']}' {ourRow['ContextualWordGloss']=}" )
                num_empty_morpheme_glosses += 1
            our_index += 1
            continue
        current_verse_reference = theirRef.split('w')[0] if 'w' in theirRef else theirRef
        if current_verse_reference != last_verse_reference:
            ketiv_count = 0
            last_verse_reference = current_verse_reference

        for increment in (0,1,2,3,4,5,6,7,8, -1,-2,-3,-4,-5,-6, 0): # ends with 0 again so 'else' messages below make sense
            ourRow = state.WLC_rows[our_index+increment]
            while ourRow['Type']=='seg' or ourRow['Type'].endswith('note'):
                increment += 1
                ourRow = state.WLC_rows[our_index+increment]
            if ourRow['Type'][-1]=='K' and increment==1:
                ketiv_count += 1
                if ketiv_count == 1:
                    ketiv_references.append( ourRow['Ref'] )
            if theirRef in ('SA2_22:8w2a', 'KI1_6:6w3a', 'JER_8:7w9a') \
            and increment > 4: # special case
                continue # Avoid a mismatch

            theirVerseRef, theirWordNumberBit = theirRef.split('w')
            ourVerseRef, ourWordNumberBit = ourRow['Ref'].split('w')
            if ourVerseRef != theirVerseRef: # nothing further to do here -- we're into a different verse
                continue

            if theirWordNumberBit.isdigit(): their_suffix_bit = ''
            else: theirWordNumberBit, their_suffix_bit = theirWordNumberBit[:-1], theirWordNumberBit[-1] # they have a letter suffix
            if ourWordNumberBit.isdigit(): our_suffix_bit = ''
            else: ourWordNumberBit, our_suffix_bit = ourWordNumberBit[:-1], ourWordNumberBit[-1] # we have a letter suffix

            # Try to match the reference and the Hebrew and use the gloss if we can
            if ( ourRow['Ref']==theirRef # then complete match
            or ( abs(int(theirWordNumberBit)-int(ourWordNumberBit))<5) # and their_suffix_bit==our_suffix_bit)
            ):
                dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"  Ref Match!" )
                if ourRow['WordOrMorpheme'] == theirWordOrMorpheme:
                    dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"  WordOrMorpheme Match!" )
                    if ourRow['Type'] in ('w','Aw'):
                        if ourRow['ContextualWordGloss']:
                            if ourRow['ContextualWordGloss'] == useGloss:
                                vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"    Already have {ourRow['Ref']} word gloss '{useGloss}'" )
                            else:
                                vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"    Skipping replacing {ourRow['Ref']} word gloss '{ourRow['ContextualWordGloss']}' with '{useGloss}'" )
                            num_word_glosses_skipped += 1
                        else:
                            vPrint( 'Info', DEBUGGING_THIS_MODULE, f"    Setting {ourRow['Ref']} '{ourRow['WordOrMorpheme']}' word gloss to '{useGloss}'" )
                            ourRow['ContextualWordGloss'] = useGloss
                            num_word_glosses_added += 1
                    else: # it's a morpheme
                        if ourRow['ContextualMorphemeGloss']:
                            if ourRow['ContextualMorphemeGloss'] == useGloss:
                                vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"    Already have {ourRow['Ref']} morpheme gloss '{useGloss}'" )
                            else:
                                vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"    Skipping replacing {ourRow['Ref']} morpheme gloss '{ourRow['ContextualMorphemeGloss']}' with '{useGloss}'" )
                            num_morpheme_glosses_skipped += 1
                        else:
                            vPrint( 'Info', DEBUGGING_THIS_MODULE, f"    Setting {ourRow['Ref']} '{ourRow['WordOrMorpheme']}' morpheme gloss to '{useGloss}'" )
                            ourRow['ContextualMorphemeGloss'] = useGloss
                            num_morpheme_glosses_added += 1
                    our_index += increment + 1 # Used it
                    num_consecutive_mismatches = 0
                    try: missing_low_fat_references.remove( ourRow['Ref'] ) # Since we (eventually) matched it
                    except ValueError: pass # it might not be in there
                    break # from _num_tries
                else:
                    dPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"    {our_index} {our_index+increment} {ourRow['Ref']} {ourRow['Type']} '{ourRow['WordOrMorpheme']}' '{ourRow['MorphemeGloss'] or ourRow['WordGloss']}'" )
                    dPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"    WordOrMorpheme Mismatch!!! ({increment=} {num_consecutive_mismatches=})" )
            else: 
                dPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"    Temp ref Mismatch!!! ({increment=} {num_consecutive_mismatches=})" )
                dPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"    {our_index} {our_index+increment} {ourRow['Ref']} {ourRow['Type']} '{ourRow['WordOrMorpheme']}' '{ourRow['MorphemeGloss'] or ourRow['WordGloss']}'" )
                if not (theirRef.startswith( 'GEN_8:17') or theirRef.startswith( 'GEN_13:3') ):
                    missing_low_fat_references.append( ourRow['Ref'] )
        else:
            num_consecutive_mismatches += 1
            dPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  Ref Mismatch!!! ({num_consecutive_mismatches=})" )
            dPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  {our_index} {ourRow['Ref']} {ourRow['Type']} '{ourRow['WordOrMorpheme']}' '{ourRow['MorphemeGloss'] or ourRow['WordGloss']}'" )
            missing_low_fat_references.append( ourRow['Ref'] )
            vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  Is {ourRow['Ref']=} missing from their lowfat data before {theirRef=}???" )
            our_index += 1 # Try skipping our entry to make up for their missing entry

        if num_consecutive_mismatches > 10:
            print( "TOO MANY CONSECUTIVE MISMATCHES" )
            break

    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"\n  Added {num_word_glosses_added:,} low fat contextual English word glosses." )
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Added {num_morpheme_glosses_added:,} low fat contextual English morpheme glosses." )
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Didn't add {num_word_glosses_skipped:,} low fat English word glosses (because we had something already)." )
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Didn't add {num_morpheme_glosses_skipped:,} low fat English morpheme glosses (because we had something already)." )
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Skipped {num_empty_word_glosses:,} empty low fat English word glosses." )
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Skipped {num_empty_morpheme_glosses:,} empty low fat English morpheme glosses." )
    missing_low_fat_references_set = sorted( set(missing_low_fat_references), key=lambda r: f'{str(BibleOrgSysGlobals.loadedBibleBooksCodes.getReferenceNumber(r[:3])).zfill(2)}{r[3:]}' )
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"\n  Low fat data seems to be missing {len(missing_low_fat_references_set):,} unique Hebrew morphemes/words" )
    vPrint( 'Info', DEBUGGING_THIS_MODULE, f"    {missing_low_fat_references_set}" )
    ketiv_references_set = sorted( set(ketiv_references), key=lambda r: f'{str(BibleOrgSysGlobals.loadedBibleBooksCodes.getReferenceNumber(r[:3])).zfill(2)}{r[3:]}' )
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Low fat data miscounts words at {len(ketiv_references_set):,} ketivs." )
    vPrint( 'Info', DEBUGGING_THIS_MODULE, f"    {ketiv_references_set}" )
    return True
# end of apply_Clear_Macula_OT_glosses.fill_known_lowFat_English_contextual_glosses


def fill_known_Cherith_English_contextual_glosses() -> bool:
    """
    Because the Hebrew accents differ from our OSHB WLC text
        vs. the Clear.Bible text, we remove accents as necessary before comparing.
    """
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, "\nPrefilling TSV table with Clear.Bible contextual English Cherith glosses…")

    suffixDict = {1:'a', 2:'b', 3:'c', 4:'d'} # Converts Clear digits to our letter suffixes
    num_empty_word_glosses = num_word_glosses_added = num_word_glosses_skipped = num_word_cantillation_marks_differ = 0
    num_empty_morpheme_glosses = num_morpheme_glosses_added = num_morpheme_glosses_skipped = num_morpheme_cantillation_marks_differ = 0
    our_index = our_word_count_offset = 0
    skipToNextVerse = False
    for CherithRow in state.Cherith_rows:
        if skipToNextVerse:
            if int(CherithRow['numID'][5:8]) == CherithVerseNum:
                vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"Skipping Cherith past v{CherithVerseNum} with {CherithRow['numID']}")
                continue
        if CherithRow['English_gloss']:
            # vPrint( 'Quiet', DEBUGGING_THIS_MODULE, row)
            numericID = CherithRow['numID'] # bbcccvvvwwwm
            assert len(numericID) == 12
            if numericID == '010080170151': # Cherith word 14 is missing for some odd reason
                our_word_count_offset -= 1
            CherithBookNum, CherithChapterNum, CherithVerseNum, CherithWordNum, CherithMorphemeNum = int(numericID[:2]), int(numericID[2:5]), int(numericID[5:8]), int(numericID[8:11]), int(numericID[-1])
            BBB = BibleOrgSysGlobals.loadedBibleBooksCodes.getBBBFromReferenceNumber( CherithBookNum )
            convertedCherithVerseID = f'{BBB}_{CherithChapterNum}:{CherithVerseNum}'
            convertedCherithWordID = f'{convertedCherithVerseID}w{CherithWordNum}'
            fullConvertedCherithID = f'{convertedCherithWordID}{suffixDict[CherithMorphemeNum]}'
            vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"\n  Got Cherith {convertedCherithVerseID=} {convertedCherithWordID=} {fullConvertedCherithID=}")
            adjusted_Cherith_word_or_morpheme = CherithRow['WLC_word_or_morpheme'][:-1] if CherithRow['WLC_word_or_morpheme'].endswith('־') \
                            else CherithRow['WLC_word_or_morpheme'][:-2] if CherithRow['WLC_word_or_morpheme'].endswith(' ׀') \
                                else CherithRow['WLC_word_or_morpheme']

            if skipToNextVerse: # Now skip our table ahead
                for increment in range( 30 ):
                    ourRow = state.WLC_rows[our_index+increment]
                    verseNum = ourRow['Ref'].split(':')[1]
                    if 'w' in verseNum: verseNum = verseNum.split('w')[0]
                    if int(verseNum) == CherithVerseNum:
                        vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"Skipped our table past {increment} rows!" )
                        break
                else: vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"Skip to next verse went wrong after skipping {increment} rows!!!!" )
                our_index += increment
                skipToNextVerse = False

            # See if we can match the morpheme with our own table
            # segNoteCount = 0
            ourLastVerseID = None
            for increment in range( 10 ):
                ourRow = state.WLC_rows[our_index+increment]
                if 'w' in ourRow['Ref']:
                    ourVerseID, ourWordNumberBits = ourRow['Ref'].split('w')
                else:
                    assert ourRow['Type']=='seg' or ourRow['Type'].endswith('note')
                    ourVerseID, ourWordNumberBits = ourRow['Ref'], '0'
                if ourLastVerseID and ourVerseID != ourLastVerseID:
                    if our_word_count_offset: vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"RESET our_word_count_offset from {our_word_count_offset} to 0")
                    our_word_count_offset = 0
                # vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"    {ourVerseID=} {ourLastVerseID=} {our_word_count_offset=} @ {ourRow['Ref']} with {ourRow['Type']} '{ourRow['WordOrMorpheme']}'" )
                ourWordNumber = int( ourWordNumberBits.replace('a','').replace('b','').replace('c','').replace('d','') ) - our_word_count_offset
                # vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"    Now checking {our_index=} {increment=} {ourRow['Ref']} {ourVerseID=} {ourWordNumber=} '{ourRow['WordOrMorpheme']}' with Cherith {fullConvertedCherithID} '{adjusted_Cherith_word_or_morpheme}'" )
                if ourRow['Ref'].startswith( convertedCherithVerseID ): # we're in the right verse
                    # vPrint( 'Quiet', DEBUGGING_THIS_MODULE, "    In right verse")
                    if ( ourRow['Type'] in ('m','M','w','Am','AM','Aw')
                    and ourRow['WordOrMorpheme']
                    and ( (ourRow['Ref']==convertedCherithWordID and CherithMorphemeNum==1) # We have no suffix so it's a whole word match
                    or ourRow['Ref']==fullConvertedCherithID  # It's a suffix match
                    or ourWordNumber == CherithWordNum ) ): # It's a word number match only
                        # vPrint( 'Quiet', DEBUGGING_THIS_MODULE, "    Looking good!")
                        our_index += increment + 1 # Stay roughly in step with the other table
                        assert ourRow['WordOrMorpheme'] not in '׃־', f"It's {ourRow['Type']} with ({len(ourRow['WordOrMorpheme'])}) '{ourRow['WordOrMorpheme']}' in ({len('׃־')}) '{'׃־'}'"
                        if ourRow['WordOrMorpheme'] == adjusted_Cherith_word_or_morpheme:
                            # vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"    Matched {ourRow=} with {CherithRow=}")
                            if ourRow['Type'] in ('w','Aw'):
                                if ourRow['ContextualWordGloss']:
                                    dPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"    Skipping replacing {ourRow['Ref']} word gloss '{ourRow['ContextualWordGloss']}' with '{CherithRow['English_gloss']}'" )
                                    num_word_glosses_skipped += 1
                                else:
                                    dPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"    Setting {ourRow['Ref']} '{ourRow['WordOrMorpheme']}' word gloss to '{CherithRow['English_gloss']}'" )
                                    ourRow['ContextualWordGloss'] = CherithRow['English_gloss']
                                    num_word_glosses_added += 1
                            else: # it's a morpheme
                                if ourRow['ContextualMorphemeGloss']:
                                    dPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"    Skipping replacing {ourRow['Ref']} morpheme gloss '{ourRow['ContextualMorphemeGloss']}' with '{CherithRow['English_gloss']}'" )
                                    num_morpheme_glosses_skipped += 1
                                else:
                                    dPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"    Setting {ourRow['Ref']} '{ourRow['WordOrMorpheme']}' morpheme gloss to '{CherithRow['English_gloss']}'" )
                                    ourRow['ContextualMorphemeGloss'] = CherithRow['English_gloss']
                                    num_morpheme_glosses_added += 1
                        elif ourRow['NoCantillations'] == removeCantillationMarks( adjusted_Cherith_word_or_morpheme, removeMetegOrSiluq=True ):
                            # vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"    Matched {ourRow=} with {CherithRow=}")
                            if ourRow['Type'] in ('w','Aw'):
                                num_word_cantillation_marks_differ += 1
                                if ourRow['ContextualWordGloss']:
                                    dPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"    Skipping replacing {ourRow['Ref']} word gloss '{ourRow['ContextualWordGloss']}' with '{CherithRow['English_gloss']}'" )
                                    num_word_glosses_skipped += 1
                                else:
                                    dPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"    Setting {ourRow['Ref']} '{ourRow['WordOrMorpheme']}' word gloss to '{CherithRow['English_gloss']}'" )
                                    ourRow['ContextualWordGloss'] = CherithRow['English_gloss']
                                    num_word_glosses_added += 1
                            else: # it's a morpheme
                                num_morpheme_cantillation_marks_differ += 1
                                if ourRow['ContextualMorphemeGloss']:
                                    dPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"    Skipping replacing {ourRow['Ref']} morpheme gloss '{ourRow['ContextualMorphemeGloss']}' with '{CherithRow['English_gloss']}'" )
                                    num_morpheme_glosses_skipped += 1
                                else:
                                    dPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"    Setting {ourRow['Ref']} '{ourRow['WordOrMorpheme']}' morpheme gloss to '{CherithRow['English_gloss']}'" )
                                    ourRow['ContextualMorphemeGloss'] = CherithRow['English_gloss']
                                    num_morpheme_glosses_added += 1
                        else:
                            dPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"    Why didn't our {ourRow['Ref']} ({len(ourRow['WordOrMorpheme'])}) '{ourRow['WordOrMorpheme']}' match {fullConvertedCherithID} ({len(adjusted_Cherith_word_or_morpheme)}) {adjusted_Cherith_word_or_morpheme=} ???" )
                            BibleOrgSysGlobals.printUnicodeInfo( ourRow['WordOrMorpheme'], f"OSHB text for {ourRow['Ref']}" )
                            BibleOrgSysGlobals.printUnicodeInfo( CherithRow['WLC_word_or_morpheme'], f"Cherith text for {CherithRow['numID']}" )
                            if ' ' in adjusted_Cherith_word_or_morpheme: # There's two Hebrew words in there
                                our_index += adjusted_Cherith_word_or_morpheme.count( ' ' ) # Try to compensate
                                our_word_count_offset += adjusted_Cherith_word_or_morpheme.count( ' ' ) # Try to compensate
                        break
                    elif ourRow['Type']!='seg' and not ourRow['Type'].endswith('note'):
                        vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"    NO MATCH!!!! {ourRow['Ref']} {ourRow['Type']} '{ourRow['WordOrMorpheme']}' {ourWordNumber=} {CherithWordNum=}" )
                ourLastVerseID = ourVerseID
            else:
                logging.critical(f"Why didn't we get a table match: {fullConvertedCherithID} {our_index=}")
                skipToNextVerse = True
        else: # no English_gloss found
            vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  No Cherith gloss available for {fullConvertedCherithID} '{adjusted_Cherith_word_or_morpheme}'")
            our_index += 1 # Advance our index anyway
            num_empty_word_glosses += 1

    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"\n  Added {num_word_glosses_added:,} Cherith contextual English word glosses." )
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Added {num_morpheme_glosses_added:,} Cherith contextual English morpheme glosses." )
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Didn't add {num_word_glosses_skipped:,} Cherith English word glosses (because we had something already)." )
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Didn't add {num_morpheme_glosses_skipped:,} Cherith English morpheme glosses (because we had something already)." )
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Skipped {num_empty_word_glosses:,} empty Cherith English word glosses." )
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Skipped {num_empty_morpheme_glosses:,} empty Cherith English morpheme glosses." )
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Noted {num_word_cantillation_marks_differ:,} Hebrew words have different cantillation marks." )
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Noted {num_morpheme_cantillation_marks_differ:,} Hebrew morphemes have different cantillation marks." )
    return True
# end of apply_Clear_Macula_OT_glosses.fill_known_Cherith_English_contextual_glosses


def save_filled_TSV_file() -> bool:
    """
    Reorganise columns and add our extra columns
    """
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"\nExporting filled WLC table as a single flat TSV file to {state.TSV_input_output_filepath}…" )

    BibleOrgSysGlobals.backupAnyExistingFile( state.TSV_input_output_filepath, numBackups=5 )

    with open( state.TSV_input_output_filepath, 'wt', encoding='utf-8' ) as tsv_output_file:
        tsv_output_file.write('\ufeff') # Write BOM
        writer = DictWriter( tsv_output_file, fieldnames=WLC_tsv_column_headers, delimiter='\t' )
        writer.writeheader()
        writer.writerows( state.WLC_rows )
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  {len(state.WLC_rows):,} data rows written." )

    return True
# end of apply_Clear_Macula_OT_glosses.save_filled_TSV_file


if __name__ == '__main__':
    # from multiprocessing import freeze_support
    # freeze_support() # Multiprocessing support for frozen Windows executables

    # Configure basic Bible Organisational System (BOS) set-up
    parser = BibleOrgSysGlobals.setup( SHORT_PROGRAM_NAME, PROGRAM_VERSION, LAST_MODIFIED_DATE )
    BibleOrgSysGlobals.addStandardOptionsAndProcess( parser )

    main()

    BibleOrgSysGlobals.closedown( PROGRAM_NAME, PROGRAM_VERSION )
# end of apply_Clear_Macula_OT_glosses.py
