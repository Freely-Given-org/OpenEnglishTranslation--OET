#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# convert_ClearMaculaOT_to_TSV.py
#
# Script handling convert_ClearMaculaOT_to_TSV functions
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
Script taking Clear.Bible low-fat trees and extracting and flattening the data
    into a single, large TSV file.

We also add the ID fields that were originally adapted from the OSHB id fields.

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


LAST_MODIFIED_DATE = '2022-10-19' # by RJH
SHORT_PROGRAM_NAME = "Convert_ClearMaculaOT_to_TSV"
PROGRAM_NAME = "Extract and Apply Macula OT glosses"
PROGRAM_VERSION = '0.31'
PROGRAM_NAME_VERSION = f'{SHORT_PROGRAM_NAME} v{PROGRAM_VERSION}'

DEBUGGING_THIS_MODULE = False


LOWFAT_XML_INPUT_FOLDERPATH = Path( '../../Forked/macula-hebrew/lowfat/' )
LOWFAT_XML_FILENAME_TEMPLATE = 'NN-Uuu-CCC-lowfat.xml' # e.g., 01-Gen-001-lowfat.xml
EXPECTED_WORD_ATTRIBUTES = ('{http://www.w3.org/XML/1998/namespace}id', 'ref',
        'mandarin', 'english', 'gloss',
        'class','morph','pos','person','gender','number','type','state',
        'transliteration','unicode','after',
        'strongnumberx', 'stronglemma','greek','greekstrong',
        'lang','lemma','stem','subjref','participantref',
        'sdbh','lexdomain','sensenumber','coredomain','contextualdomain','frame',)
assert len(set(EXPECTED_WORD_ATTRIBUTES)) == len(EXPECTED_WORD_ATTRIBUTES), "No duplicate attribute names"
TSV_INPUT_FILEPATH = Path( '../intermediateTexts/glossed_OSHB/WLC_glosses.morphemes.tsv' )
TSV_OUTPUT_FILEPATH = Path( '../intermediateTexts/Clear.Bible_lowfat_trees/ClearLowFatTrees.OT.morphemes.tsv' )
SHORTENED_TSV_OUTPUT_FILEPATH = Path( '../intermediateTexts/Clear.Bible_lowfat_trees/ClearLowFatTreesAbbrev.OT.morphemes.tsv' )
OUTPUT_FIELDNAMES = ['FGRef','OSHBid','RowType','LFRef','LFNumRef',
                    'Language','WordOrMorpheme','Unicode','Transliteration','After',
                    'WordClass','PartOfSpeech','Person','Gender','Number','WordType','State','SDBH',
                    'StrongNumberX','StrongLemma','Stem','Morphology','Lemma','SenseNumber',
                    'CoreDomain','LexicalDomain','ContextualDomain',
                    'SubjRef','ParticipantRef','Frame',
                    'Greek','GreekStrong',
                    'EnglishGloss','MandarinGloss','ContextualGloss',
                    'Nesting']
assert len(set(OUTPUT_FIELDNAMES)) == len(OUTPUT_FIELDNAMES), "No duplicate fieldnames"
assert len(OUTPUT_FIELDNAMES) == 36, len(OUTPUT_FIELDNAMES)


state = None
class State:
    def __init__( self ) -> None:
        """
        Constructor:
        """
        self.lowfat_XML_input_folderpath = LOWFAT_XML_INPUT_FOLDERPATH
        self.TSV_input_filepath = TSV_INPUT_FILEPATH
        self.TSV_output_filepath = TSV_OUTPUT_FILEPATH
        self.shortened_TSV_output_filepath = SHORTENED_TSV_OUTPUT_FILEPATH
        self.WLC_rows = []
        self.lowFatWordsAndMorphemes = []
        self.output_fieldnames = OUTPUT_FIELDNAMES
    # end of convert_ClearMaculaOT_to_TSV.State.__init__()


NUM_EXPECTED_WLC_COLUMNS = 16
WLC_tsv_column_max_length_counts = {}
WLC_tsv_column_non_blank_counts = {}
WLC_tsv_column_counts = defaultdict(lambda: defaultdict(int))
WLC_tsv_column_headers = []


def main() -> None:
    """
    """
    BibleOrgSysGlobals.introduceProgram( __name__, PROGRAM_NAME_VERSION, LAST_MODIFIED_DATE )
    global state
    state = State()

    if loadOurSourceTable():
        if loadLowFatGlosses():
            if add_OSHB_ids():
                save_filled_TSV_file()
                save_shortened_TSV_file()
# end of convert_ClearMaculaOT_to_TSV.main


def loadOurSourceTable() -> bool:
    """
    """
    global WLC_tsv_column_headers
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"\nLoading our WLC tsv file from {state.TSV_input_filepath}…")
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  Expecting {NUM_EXPECTED_WLC_COLUMNS} columns…")
    with open(state.TSV_input_filepath, 'rt', encoding='utf-8') as tsv_file:
        tsv_lines = tsv_file.readlines()

    # Remove any BOM
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
        row_type = row['RowType']
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
# end of convert_ClearMaculaOT_to_TSV.loadOurSourceTable


def loadLowFatGlosses() -> bool:
    """
    Extract glosses out of fields 
    Reorganise columns and add our extra columns
    """
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"\nLoading Clear.Bible OT 'low fat' glosses from {state.lowfat_XML_input_folderpath}/…" )
    
    suffixDict = {'1':'a', '2':'b', '3':'c', '4':'d', '5':'e'} # Max of 5 morphemes in one word
    max_nesting_level = 0
    column_counts = defaultdict(lambda: defaultdict(int))
    # non_blank_counts = defaultdict(int)
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

            # First make a table of parents so we can find them later
            parentMap = {child:parent for parent in chapterTree.iter() for child in parent if child.tag in ('w','wg')}
            dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"  Loaded {len(parentMap):,} parent entries." )

            # Now load all the word (w) fields for the chapter into a temporary list
            tempWordsAndMorphemes = []
            longIDs = []
            for elem in chapterTree.getroot().iter():
                if elem.tag == 'w': # ignore all the others -- there's enough info in here
                    for attribName in elem.attrib:
                        assert attribName in EXPECTED_WORD_ATTRIBUTES, f"loadLowFatGlosses(): unexpected {attribName=}"

                    wordOrMorpheme = elem.text
                    theirRef = elem.get('ref')

                    longID = elem.get('{http://www.w3.org/XML/1998/namespace}id') # e.g., o010010050031 = obbcccvvvwwws
                    longIDs.append( longID )
                    assert longID.startswith( 'o' ) # Stands for OldTestament
                    longID = longID[1:] # remove 'o' prefix
                    if len(longID) > 12: # it's an article (vowel after preposition)
                        assert len(longID) == 13
                        assert longID.endswith( 'ה' )
                        assert longID[:-1].isdigit()
                    else:
                        assert len(longID) == 12
                        assert longID[:].isdigit()

                    gloss = elem.get('gloss')
                    if gloss: gloss = gloss.replace( '.', '_' ) # Change to our system
                    lang = elem.get('lang')
                    column_counts['lang'][lang] += 1
                    assert lang in 'HA'
                    wType = elem.get('type')
                    column_counts['type'][wType] += 1
                    wState = elem.get('state')
                    column_counts['state'][wState] += 1
                    if wState:
                        # What is 'determined' in Ezra 4:8!5, etc.
                        assert wState in ('absolute','construct','determined'), f"Found unexpected {wState=}"
                    # dPrint( 'Info', DEBUGGING_THIS_MODULE, f"    {ref} {longID} {lang} '{wordOrMorpheme}' {English=} {gloss=}")

                    stem = elem.get('stem')
                    column_counts['stem'][stem] += 1
                    morph = elem.get('morph')
                    # column_counts['morph'][morph] += 1 # There's over 700 different variations

                    senseNumber = elem.get('sensenumber')
                    column_counts['sensenumber'][senseNumber] += 1

                    after = elem.get('after')
                    column_counts['after'][after] += 1
                    if after: assert len(after) <= 2, f"{len(after)} {after=}"

                    wClass = elem.get('class')
                    column_counts['class'][wClass] += 1
                    PoS = elem.get('pos')
                    column_counts['pos'][PoS] += 1
                    person = elem.get('person')
                    column_counts['person'][person] += 1
                    gender = elem.get('gender')
                    column_counts['gender'][gender] += 1
                    number = elem.get('number')
                    column_counts['number'][number] += 1

                    # Cross-checking
                    # TODO: Could do much more of this
                    if PoS=='noun': assert morph.startswith('N')
                    if morph.startswith('N'): assert PoS=='noun'

                    English = elem.get('english')
                    if English == '.and': English = 'and' # at ISA 65:9!9
                    if English:
                        assert '.' not in English
                        assert English.strip() == English # No leading or trailing spaces
                        English = English.replace( ' ', '_' )
                    else: English = '' # Instead of None

                    startElement = elem
                    nestingBits = []
                    while True:
                        parentElem = parentMap[startElement]
                        if parentElem.tag == 'sentence': break
                        assert parentElem.tag == 'wg'
                        pClass, role, rule = parentElem.get('class'), parentElem.get('role'), parentElem.get('rule')
                        if role:
                            if rule: # have both
                                nestingBits.append( f'{role}={rule}' )
                            else: # only have role
                                nestingBits.append( role )
                        elif rule: # have no role
                            nestingBits.append( rule )
                        else:
                            assert pClass=='compound', f"{theirRef} has no role/rule {pClass=} {nestingBits}"
                        startElement = parentElem
                    if len(nestingBits) >= max_nesting_level:
                        max_nesting_level = len(nestingBits) + 1

                    # Names have to match state.output_fieldnames:
                    # ['FGRef','OSHBid','RowType','LFRef','LFNumRef',
                    # 'Language','WordOrMorpheme','Unicode','Transliteration','After',
                    # 'WordClass','PartOfSpeech','Person','Gender','Number','WordType','State','SDBH',
                    # 'StrongNumberX','StrongLemma','Stem','Morphology','Lemma','SenseNumber',
                    # 'CoreDomain','LexicalDomain','ContextualDomain',
                    # 'SubjRef','ParticipantRef','Frame',
                    # 'Greek','GreekStrong',
                    # 'EnglishGloss','MandarinGloss','ContextualGloss',
                    # 'Nesting']
                    entry = {'LFRef':theirRef, 'LFNumRef':longID, 'Language':lang, 'WordOrMorpheme':wordOrMorpheme,
                                'Unicode':elem.get('unicode'), 'Transliteration':elem.get('transliteration'), 'After':after,
                                'WordClass':wClass, 'PartOfSpeech':PoS, 'Person':person, 'Gender':gender, 'Number':number,
                                'WordType':wType, 'State':wState, 'SDBH':elem.get('sdbh'),
                                'StrongNumberX':elem.get('strongnumberx'), 'StrongLemma':elem.get('stronglemma'),
                                'Stem':stem, 'Morphology':morph, 'Lemma':elem.get('lemma'), 'SenseNumber':senseNumber,
                                'CoreDomain':elem.get('coredomain'), 'LexicalDomain':elem.get('lexdomain'), 'Frame':elem.get('frame'),
                                'SubjRef':elem.get('subjref'), 'ParticipantRef':elem.get('participantref'), 'ContextualDomain':elem.get('contextualdomain'),
                                'Greek':elem.get('greek'), 'GreekStrong':elem.get('greekstrong'),
                                'EnglishGloss':English, 'MandarinGloss':elem.get('mandarin'), 'ContextualGloss':gloss,
                                'Nesting':'/'.join(reversed(nestingBits)) }
                    assert len(entry) == len(state.output_fieldnames)-3, f"{len(entry)=} vs {len(state.output_fieldnames)=}" # Three more fields to be added below
                    # for k,v in entry.items():
                    #     if v: non_blank_counts[k] += 1
                    tempWordsAndMorphemes.append( entry )
                    # dPrint( 'Normal', DEBUGGING_THIS_MODULE, f"\n  ({len(entry)}) {entry}" ) # 28
                    # if len(tempWordsAndMorphemes) > 5: halt

            vPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"    Got {len(tempWordsAndMorphemes):,} words/morphemes in {BBB} {chapterNumber}")
            assert len(set(longIDs)) == len(longIDs), f"Should be no duplicates in {longIDs=}"

            # Note that because of the phrase/clause nesting, we can get the word fields in the wrong order
            #   so we sort them, before adjusting the formatting to what we're after
            # We sort by the Clear.Bible longID (2nd item in tuple, which already has the leading 'o' removed)
            sortedTempWordsAndMorphemes = sorted( tempWordsAndMorphemes, key=lambda t: t['LFNumRef'] )

            # Adjust to our references and with just the data that we need to retain
            for j,firstEntryAttempt in enumerate( sortedTempWordsAndMorphemes ):
                longID = firstEntryAttempt['LFNumRef']
                # if longID.startswith('01003009'): print(j, sixTuple)
                if longID.endswith( 'ה' ):  # it's an article (vowel after preposition)
                    # print(f"Got article {longID=}")
                    assert firstEntryAttempt['WordOrMorpheme'] is None # No wordOrMorpheme
                    assert firstEntryAttempt['ContextualGloss'] is None # No gloss
                    english = firstEntryAttempt['EnglishGloss']
                    wType = firstEntryAttempt['WordType']
                    assert wType == 'definite article'
                    # print(f"Got article {longID=} with '{english}' {wType=}")
                    # Add the article gloss to the previous entry
                    lastExpandedEntry = state.lowFatWordsAndMorphemes[-1] # We'll edit the last dict entry in place
                    lastExpandedEntry['EnglishGloss'] = f"{lastExpandedEntry['EnglishGloss']}_{english if english else 'THE'}" # Why wasn't the gloss there?
                    # else: print(f"{longID} There wasn't an English gloss!!!"); halt
                else: # a normal word or morpheme entry
                    try: nextLongID = sortedTempWordsAndMorphemes[j+1]['LFNumRef']
                    except IndexError: nextLongID = '1'
                    if nextLongID.endswith('ה'): # we have to skip this one
                        try: nextLongID = sortedTempWordsAndMorphemes[j+1+1]['LFNumRef']
                        except IndexError: nextLongID = '1'
                    assert nextLongID != longID, f"Should be no duplicate IDs: {j=} {longID=} {nextLongID=} {firstEntryAttempt}"
                    if nextLongID.endswith( '1' ): # current entry is end of a word
                        mwType = 'w' if longID.endswith( '1' ) else 'M'
                    else: # the above works but fails when the first morpheme of a word is (wrongly) missing
                        # print(f"{longID=} going to {nextLongID=} ")
                        assert len(nextLongID) == len(longID) == 12 # leading 'o' has already been removed
                        nextLongIDWordBit = nextLongID[:-1]
                        longIDWordBit = longID[:-1]
                        if nextLongIDWordBit == longIDWordBit: # we're still in the same word
                            mwType = 'm' # There's a following part of this word
                        else: # we going on to a new word, but the first part is missing
                            mwType = 'w' if longID.endswith( '1' ) else 'M'
                    suffix = '' if mwType=='w' else suffixDict[longID[-1]]
                    if firstEntryAttempt['Language'] == 'A': mwType = f'A{mwType}' # Assume Hebrew; mark Aramaic
                    ourRef = f"{BBB}_{firstEntryAttempt['LFRef'][4:].replace( '!', 'w')}{suffix}"
                    # print(f"{longID=} {nextLongID=} {mwType=} {ourRef=}")
                    newExpandedDictEntry = {'FGRef':ourRef, 'RowType':mwType, **firstEntryAttempt}
                    assert len(newExpandedDictEntry) == len(state.output_fieldnames)-1, f"{len(newExpandedDictEntry)=} vs {len(state.output_fieldnames)=}" # OSHBid field to be added below
                    state.lowFatWordsAndMorphemes.append( newExpandedDictEntry )

    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  Got total of {len(state.lowFatWordsAndMorphemes):,} words/morphemes")
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"      Max nesting level = {max_nesting_level}" )
    if 1:  # Just so we can turn it off and on easily
        vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"\nDetailed counts for {len(column_counts):,} fields:")
        for field_name in column_counts:
            this_set = column_counts[field_name]
            this_set_length = len(this_set)
            if this_set_length < 55:
                vPrint( 'Normal', DEBUGGING_THIS_MODULE, # Sort them with most frequent first
                    f"\n{field_name}: ({this_set_length}) {dict(sorted(this_set.items(), key=lambda x:x[1], reverse=True))}" )
            else: vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"\n{field_name} has {this_set_length:,} unique options -- display suppressed." )
    # if 0:
    #     for n,currentEntry in enumerate(state.lowFatWordsAndMorphemes):
    #         assert len(currentEntry) == len(state.output_fieldnames)-1
    #         if n < 5 or 'THE' in currentEntry['EnglishGloss']: print(f"{n} ({len(currentEntry)}) {currentEntry}")
    return True
# end of convert_ClearMaculaOT_to_TSV.loadLowFatGlosses


def removeCantillationMarks( text:str, removeMetegOrSiluq=False ):
    """
    Return the text with cantillation marks removed.
    """
    #dPrint( 'Quiet', DEBUGGING_THIS_MODULE, "removeCantillationMarks( {!r}, {} )".format( text, removeMetegOrSiluq ) )
    h = Hebrew.Hebrew( text )
    return h.removeCantillationMarks( removeMetegOrSiluq=removeMetegOrSiluq )
# end of apply_Clear_Macula_OT_glosses.removeCantillationMarks


def add_OSHB_ids() -> bool:
    """
    The Clear.Bible data doesn't use the 5-character OSHB id fields
        (which we augment to 6-characters).

    So match the entries and add them in.
    """
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, "\nMatching rows in both tables to add OSHB ids…" )

    WLC_dict = {row['Ref']:(row['RowType'].endswith('K'),row['NoCantillations'],row['Morphology'],row['OSHBid']) for row in state.WLC_rows} # We include the morphology for extra checking
    # print()
    # testVerseRef = 'GEN_22:7'
    # for row in state.WLC_rows:
    #     if row['Ref'].startswith( testVerseRef ):
    #         print( f"{row['Ref']}\t{row['OSHBid']}\t{row['RowType']}\t'{row['WordOrMorpheme']}'\t {row['Morphology']}" )
    # print()

    offset = 0
    lastVerseID = None
    newLowFatWordsAndMorphemes = []
    for n,secondEntryAttempt in enumerate(state.lowFatWordsAndMorphemes):
        assert len(secondEntryAttempt) == len(state.output_fieldnames)-1
        ourID, wordOrMorpheme, morphology = secondEntryAttempt['FGRef'], removeCantillationMarks(secondEntryAttempt['WordOrMorpheme'], removeMetegOrSiluq=True), secondEntryAttempt['Morphology']
        verseID, wordPart = ourID.split('w')
        if wordPart.isdigit():
            wordNumber,suffix = int( wordPart ), ''
        else:
            wordNumber,suffix = int( wordPart[:-1] ), wordPart[-1]
        # if ourID.startswith( testVerseRef ):
        #     print( f"{ourID}, '{wordOrMorpheme}' {morphology}" ) # '{rowTuple30[-1]}'

        if verseID != lastVerseID:
            offset = 0 # Restart at start of verse
        adjustedRowID = f'{verseID}w{wordNumber+offset}{suffix}'
        try:
            foundKetivFlag, foundWordOrMorpheme, foundMorphology, foundID = WLC_dict[adjustedRowID]
            assert foundWordOrMorpheme==wordOrMorpheme, f"ID's matched {adjustedRowID} from {ourID} and got {foundID}, but not text ({len(foundWordOrMorpheme)}) '{foundWordOrMorpheme}' != ({len(wordOrMorpheme)}) '{wordOrMorpheme}'"
            assert foundMorphology==morphology \
                or (foundMorphology=='Rd' and morphology=='R'), \
                f"ID's matched {adjustedRowID} from {ourID} and got {foundID}, but not morphology '{foundMorphology}'!='{morphology}'"
            # print(f"({len(secondEntryAttempt)}) {secondEntryAttempt=}")
            newMoreExpandedDictEntry = {'FGRef':ourID, 'OSHBid':foundID, **secondEntryAttempt}
            # print(f"({len(newMoreExpandedDictEntry)}) {newMoreExpandedDictEntry=}")
            assert len(newMoreExpandedDictEntry) == len(state.output_fieldnames), f"{len(newMoreExpandedDictEntry)=} vs {len(state.output_fieldnames)=}" # OSHBid field to be added below
            newLowFatWordsAndMorphemes.append( newMoreExpandedDictEntry )
        except KeyError:
            logging.warning( f"Failed to find OSHB id for {offset=} {ourID}: '{wordOrMorpheme}' {morphology}" )
            assert 'w' in ourID
            if suffix in ('','a'):
                offset -= 1
            adjustedRowID = f'{verseID}w{wordNumber+offset}{suffix}'
            try:
                foundKetivFlag, foundWordOrMorpheme, foundMorphology, foundID = WLC_dict[adjustedRowID]
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  Got {foundID} for {offset=} {foundKetivFlag=} {adjustedRowID}")
                if not foundKetivFlag: # Doesn't always work on Ketivs
                    assert foundWordOrMorpheme==wordOrMorpheme, f"ID's now matched {adjustedRowID} from {ourID} and got {foundID}, but not text ({len(foundWordOrMorpheme)}) '{foundWordOrMorpheme}' != ({len(wordOrMorpheme)}) '{wordOrMorpheme}'"
                    assert foundMorphology==morphology, f"ID's now matched {adjustedRowID} from {ourID} and got {foundID}, but not morphology '{foundMorphology}'!='{morphology}'"
                newMoreExpandedDictEntry = {'FGRef':ourID, 'OSHBid':foundID, **secondEntryAttempt}
                assert len(newMoreExpandedDictEntry) == len(state.output_fieldnames), f"{len(newMoreExpandedDictEntry)=} vs {len(state.output_fieldnames)=}" # OSHBid field to be added below
                newLowFatWordsAndMorphemes.append( newMoreExpandedDictEntry )
            except (KeyError, AssertionError):
                logging.error( f"Failed to find OSHB id for {offset=} {adjustedRowID} from {ourID}: '{secondEntryAttempt['WordOrMorpheme']}'")
                newMoreExpandedDictEntry = {'FGRef':ourID, 'OSHBid':'', **secondEntryAttempt}
                assert len(newMoreExpandedDictEntry) == len(state.output_fieldnames), f"{len(newMoreExpandedDictEntry)=} vs {len(state.output_fieldnames)=}" # OSHBid field to be added below
                newLowFatWordsAndMorphemes.append( newMoreExpandedDictEntry )
        except AssertionError:
            logging.warning( f"Failed to match text or morphology for {offset=} {ourID}: '{foundWordOrMorpheme}' vs '{wordOrMorpheme}' {foundMorphology} vs {morphology}")
            assert 'w' in ourID
            if suffix in ('','a'):
                offset -= 1
            adjustedRowID = f'{verseID}w{wordNumber+offset}{suffix}'
            try:
                foundKetivFlag, foundWordOrMorpheme, foundMorphology, foundID = WLC_dict[adjustedRowID]
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  Got {foundID} for {offset=} {foundKetivFlag=} {adjustedRowID}")
                if not foundKetivFlag: # Doesn't always work on Ketivs
                    assert foundWordOrMorpheme==wordOrMorpheme, f"ID's now matched {adjustedRowID} from {ourID} and got {foundID}, but not text ({len(foundWordOrMorpheme)}) '{foundWordOrMorpheme}' != ({len(wordOrMorpheme)}) '{wordOrMorpheme}'"
                    assert foundMorphology==morphology, f"ID's now matched {adjustedRowID} from {ourID} and got {foundID}, but not morphology '{foundMorphology}'!='{morphology}'"
                newMoreExpandedDictEntry = {'FGRef':ourID, 'OSHBid':foundID, **secondEntryAttempt}
                assert len(newMoreExpandedDictEntry) == len(state.output_fieldnames), f"{len(newMoreExpandedDictEntry)=} vs {len(state.output_fieldnames)=}" # OSHBid field to be added below
                newLowFatWordsAndMorphemes.append( newMoreExpandedDictEntry )
            except (KeyError, AssertionError):
                logging.error( f"Failed to find OSHB id for {offset=} {adjustedRowID} from {ourID}: '{secondEntryAttempt['WordOrMorpheme']}'")
                newMoreExpandedDictEntry = {'FGRef':ourID, 'OSHBid':'', **secondEntryAttempt}
                assert len(newMoreExpandedDictEntry) == len(state.output_fieldnames), f"{len(newMoreExpandedDictEntry)=} vs {len(state.output_fieldnames)=}" # OSHBid field to be added below
                newLowFatWordsAndMorphemes.append( newMoreExpandedDictEntry )
        # Check we haven't ended up with anything missing or any extra stuff
        for fieldname in newLowFatWordsAndMorphemes[-1]: assert fieldname in state.output_fieldnames
        for fieldname in state.output_fieldnames: assert fieldname in newLowFatWordsAndMorphemes[-1]
        lastVerseID = verseID

    assert len(newLowFatWordsAndMorphemes) == len(state.lowFatWordsAndMorphemes)
    state.lowFatWordsAndMorphemes = newLowFatWordsAndMorphemes

    return True
# end of convert_ClearMaculaOT_to_TSV.add_OSHB_ids


def save_filled_TSV_file() -> bool:
    """
    Save table as a single TSV file (about 94 MB).
    """
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"\nExporting filled OT Low Fat table as a single flat TSV file to {state.TSV_output_filepath}…" )

    BibleOrgSysGlobals.backupAnyExistingFile( state.TSV_output_filepath, numBackups=5 )

    # print(len(state.lowFatWordsAndMorphemes[0]), state.lowFatWordsAndMorphemes[0]);halt
    with open( state.TSV_output_filepath, 'wt', encoding='utf-8' ) as tsv_output_file:
        tsv_output_file.write('\ufeff') # Write BOM
        writer = DictWriter( tsv_output_file, fieldnames=state.output_fieldnames, delimiter='\t' )
        writer.writeheader()
        for thisTuple in state.lowFatWordsAndMorphemes:
            thisRow = {k:v for k,v in zip(state.output_fieldnames, thisTuple, strict=True)}
            writer.writerow( thisRow )
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  {len(state.lowFatWordsAndMorphemes):,} data rows written ({len(state.output_fieldnames)} fields)." )

    if 1: # Collect and print stats
        non_blank_counts, blank_counts = defaultdict(int), defaultdict(int)
        sets = defaultdict(set)
        for entry in state.lowFatWordsAndMorphemes:
            for fieldname,value in entry.items():
                if value: non_blank_counts[fieldname] += 1
                else: blank_counts[fieldname] += 1
                sets[fieldname].add( value )
        for fieldname,count in blank_counts.items():
            assert count < len(state.lowFatWordsAndMorphemes), f"Field is never filled: '{fieldname}'"
        vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"\nCounts of non-blank fields for {len(state.lowFatWordsAndMorphemes):,} rows:" )
        for fieldname,count in non_blank_counts.items():
            non_blank_count_str = 'all' if count==len(state.lowFatWordsAndMorphemes) else f'{count:,}'
            unique_count_str = 'all' if len(sets[fieldname])==len(state.lowFatWordsAndMorphemes) else f'{len(sets[fieldname]):,}'
            vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  {fieldname}: {non_blank_count_str} non-blank entries (with {unique_count_str} unique entries)" )
            assert count # Otherwise we're including a field that contains nothing!
            if len(sets[fieldname]) < 50:
                vPrint( 'Info', DEBUGGING_THIS_MODULE, f"    being: {sets[fieldname]}" )

    return True
# end of convert_ClearMaculaOT_to_TSV.save_filled_TSV_file


def save_shortened_TSV_file() -> bool:
    """
    Save table as a single TSV file
        but with a number of fields deleted or abbreviated to make it smaller.

    Of course, this makes the table less self-documenting!
    """
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"\nExporting shortened OT Low Fat table as a single flat TSV file to {state.TSV_output_filepath}…" )

    BibleOrgSysGlobals.backupAnyExistingFile( state.shortened_TSV_output_filepath, numBackups=5 )

    columnsToRemove = ('LFRef','LFNumRef', # Don't need their references
        'Language', # Aramaic is in already in RowType field
        'Unicode', # Not sure what this was anyway
        'Transliteration', # We can do this on the fly
        'SDBH', # Resource is not open source -- no use to us
        'MandarinGloss', # Not needed for our specific task
        'CoreDomain','LexicalDomain','ContextualDomain', # What do all these numbers refer to?
        )
    shortenedFieldnameList = [fieldname for fieldname in state.output_fieldnames if fieldname not in columnsToRemove]
    # print(f"({len(state.output_fieldnames)}) {state.output_fieldnames} -> ({len(shortenedFieldnames)}) {shortenedFieldnames}")

    # print(len(state.lowFatWordsAndMorphemes[0]), state.lowFatWordsAndMorphemes[0]);halt
    non_blank_counts = defaultdict(int)
    sets = defaultdict(set)
    with open( state.shortened_TSV_output_filepath, 'wt', encoding='utf-8' ) as tsv_output_file:
        tsv_output_file.write('\ufeff') # Write BOM
        writer = DictWriter( tsv_output_file, fieldnames=shortenedFieldnameList, delimiter='\t' )
        writer.writeheader()
        for thisEntryDict in state.lowFatWordsAndMorphemes:
            for columnName in columnsToRemove:
                del thisEntryDict[columnName]
            # Abbreviate wordy fields -- they can always be reconstituted later
            # Try to use the same abbreviations as already used in other fields
            try: thisEntryDict['WordType'] = {'common':'com', 'pronominal':'pron', 'proper':'PN', 'definite article':'def',
                            'direct object marker':'DOM', 'adjective':'adj', 'negative':'neg', 'imperative':'imp',
                            'cardinal number':'cardinal', 'ordinal number':'ordinal', 'interjection':'ij',
                            'unknown: x':'?' }[thisEntryDict['WordType']]
            except KeyError: pass # The above set is not complete -- there's several others (plus None) that we leave unchanged
            try: thisEntryDict['WordClass'] = {'noun':'n','verb':'v','prep':'pp', 'particle':'part'}[thisEntryDict['WordClass']]
            except KeyError: pass # The above set is not complete -- there's several others that we leave unchanged
            thisEntryDict['PartOfSpeech'] = {'noun':'n','verb':'v','preposition':'pp', 'particle':'part', 'conjunction':'cj',
                            'suffix':'suffix', 'adjective':'adj','pronoun':'pron','adverb':'adv'}[thisEntryDict['PartOfSpeech']]
            if thisEntryDict['Person']: # Abbreviate
                thisEntryDict['Person'] = {'first':'1','second':'2','third':'3', 'unknown: x':'?'}[thisEntryDict['Person']]
            if thisEntryDict['Gender']: # Abbreviate
                thisEntryDict['Gender'] = {'masculine':'m','feminine':'f','common':'c', 'both':'b', 'unknown: x':'?'}[thisEntryDict['Gender']]
            if thisEntryDict['Number']: # Abbreviate
                thisEntryDict['Number'] = {'singular':'s','plural':'p','dual':'d', 'unknown: x':'?'}[thisEntryDict['Number']]
            if thisEntryDict['State']: # Abbreviate
                thisEntryDict['State'] = {'absolute':'a','construct':'c','determined':'d'}[thisEntryDict['State']]
            assert len(thisEntryDict) == len(state.output_fieldnames) - len(columnsToRemove)
            writer.writerow( thisEntryDict )
            for fieldname,value in thisEntryDict.items():
                if value: non_blank_counts[fieldname] += 1
                sets[fieldname].add( value )
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  {len(state.lowFatWordsAndMorphemes):,} shortened ({len(state.output_fieldnames)} - {len(columnsToRemove)} = {len(thisEntryDict)} fields) data rows written." )

    if 1: # Print stats
        vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"\nCounts of non-blank fields for {len(state.lowFatWordsAndMorphemes):,} rows:" )
        for fieldname,count in non_blank_counts.items():
            non_blank_count_str = 'all' if count==len(state.lowFatWordsAndMorphemes) else f'{count:,}'
            unique_count_str = 'all' if len(sets[fieldname])==len(state.lowFatWordsAndMorphemes) else f'{len(sets[fieldname]):,}'
            vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  {fieldname}: {non_blank_count_str} non-blank entries (with {unique_count_str} unique entries)" )
            assert count # Otherwise we're including a field that contains nothing!
            if len(sets[fieldname]) < 50:
                vPrint( 'Info', DEBUGGING_THIS_MODULE, f"    being: {sets[fieldname]}" )

    return True
# end of convert_ClearMaculaOT_to_TSV.save_shortened_TSV_file


if __name__ == '__main__':
    # from multiprocessing import freeze_support
    # freeze_support() # Multiprocessing support for frozen Windows executables

    # Configure basic Bible Organisational System (BOS) set-up
    parser = BibleOrgSysGlobals.setup( SHORT_PROGRAM_NAME, PROGRAM_VERSION, LAST_MODIFIED_DATE )
    BibleOrgSysGlobals.addStandardOptionsAndProcess( parser )

    main()

    BibleOrgSysGlobals.closedown( PROGRAM_NAME, PROGRAM_VERSION )
# end of convert_ClearMaculaOT_to_TSV.py
