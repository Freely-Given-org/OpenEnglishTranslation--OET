#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# prepare_OSHB_for_glossing.py
#
# Script handling prepare_OSHB_for_glossing functions
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
Script taking our OSHB morpheme table (TSV)
    and adding columns for glossing.

(This is run AFTER convert_OSHB_XML_to_TSV.py
    and BEFPRE extract_Clear_Cherith_glosses.py.)

OSHB morphology codes can be found at https://hb.openscriptures.org/parsing/HebrewMorphologyCodes.html.
"""
from gettext import gettext as _
from typing import Dict, List, Tuple
from pathlib import Path
from csv import DictReader, DictWriter
from collections import defaultdict
from datetime import datetime
import logging
import ast
from pprint import pprint

if __name__ == '__main__':
    import sys
    sys.path.insert( 0, '../../BibleOrgSys/' )
from BibleOrgSys import BibleOrgSysGlobals
from BibleOrgSys.BibleOrgSysGlobals import vPrint, fnPrint, dPrint
from BibleOrgSys.OriginalLanguages import Hebrew
# from BibleOrgSys.OriginalLanguages import HebrewWLCBible


LAST_MODIFIED_DATE = '2022-10-05' # by RJH
SHORT_PROGRAM_NAME = "Prepare_OSHB_for_glossing"
PROGRAM_NAME = "Prepare OSHB for glossing"
PROGRAM_VERSION = '0.40'
PROGRAM_NAME_VERSION = f'{SHORT_PROGRAM_NAME} v{PROGRAM_VERSION}'

DEBUGGING_THIS_MODULE = True


OSHB_TSV_INPUT_FILEPATH = Path( '../sourceTexts/rawOSHB/OSHB.original.flat.morphemes.tsv' )
PREDONE_GLOSSES_FILEPATH = Path( 'WLCHebrewGlosses.txt' )
TSV_OUTPUT_FILEPATH = Path( '../intermediateTexts/glossed_OSHB/WLC_glosses.morphemes.tsv' )


state = None
class State:
    def __init__( self ) -> None:
        """
        Constructor:
        """
        self.OSHB_TSV_input_filepath = OSHB_TSV_INPUT_FILEPATH
        self.TSV_output_filepath = TSV_OUTPUT_FILEPATH
        self.WLC_rows = []
        self.expanded_headers = ['Ref','OSHBid','Type','Strongs','CantillationHierarchy','Morphology','WordOrMorpheme','NoCantillations',
                                            'MorphemeGloss','ContextualMorphemeGloss', 'WordGloss','ContextualWordGloss',
                                            'GlossCapitalisation','GlossPunctuation','GlossOrder']
    # end of prepare_OSHB_for_glossing.__init__


NUM_EXPECTED_WLC_COLUMNS = 9
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

    if loadWLCSourceTable() and create_expanded_TSV_table() and prefill_known_glosses():
        save_expanded_TSV_file()
# end of prepare_OSHB_for_glossing.main


def loadWLCSourceTable() -> bool:
    """
    """
    global WLC_tsv_column_headers
    print(f"\nLoading WLC tsv file from {state.OSHB_TSV_input_filepath}…")
    print(f"  Expecting {NUM_EXPECTED_WLC_COLUMNS} columns…")
    with open(state.OSHB_TSV_input_filepath, 'rt', encoding='utf-8') as tsv_file:
        tsv_lines = tsv_file.readlines()

    # Remove BOM
    if tsv_lines[0].startswith("\ufeff"):
        print("  Handling Byte Order Marker (BOM) at start of WLC tsv file…")
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
        elif row_type == 'note':
            note_count += 1
        elif row_type == 'w':
            unique_words.add(row['WordOrMorpheme'])
        elif row_type == 'm':
            unique_morphemes.add(row['WordOrMorpheme'])
            assembled_word = f"{assembled_word}{row['WordOrMorpheme']}"
        else: unexpected_row_type
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
    print(f"  Loaded {len(state.WLC_rows):,} (tsv) WLC data rows.")
    print(f"    Have {len(unique_words):,} unique Hebrew words.")
    print(f"    Have {len(unique_morphemes):,} unique Hebrew morphemes.")
    print(f"    Have {seg_count:,} Hebrew segment markers.")
    print(f"    Have {note_count:,} notes.")

    return True
# end of prepare_OSHB_for_glossing.loadWLCSourceTable


def removeCantillationMarks( text:str, removeMetegOrSiluq=False ):
    """
    Return the text with cantillation marks removed.
    """
    #dPrint( 'Quiet', DEBUGGING_THIS_MODULE, "removeCantillationMarks( {!r}, {} )".format( text, removeMetegOrSiluq ) )
    h = Hebrew.Hebrew( text )
    return h.removeCantillationMarks( removeMetegOrSiluq=removeMetegOrSiluq )
# end of prepare_OSHB_for_glossing.removeCantillationMarks


def create_expanded_TSV_table() -> bool:
    """
    Reorganise columns and add our extra columns

    Also mark the last morpheme in a word-set with M (instead of m)
    """
    print( f"\nCreating expanded TSV table with {len(state.expanded_headers)} columns…" )
    new_rows = []
    last_OSIS_base_id, last_row = '', []
    last_V = 0
    glossCapitalisation = 'S' # First word is start of sentence
    for row in state.WLC_rows:
        V = int(row['FGID'][5:8])
        if V != last_V:
            glossOrderInt = 10
            last_V = V
        else: glossOrderInt += 10
        OSIS_base_id = row['OSHBid'][:5]
        new_type = row['Type']
        if new_type in ('seg','note'): language_code = ''
        new_morphology = row['Morphology']
        if OSIS_base_id != last_OSIS_base_id: # it's the start of a new word (or set of morphemes)
            if last_row:
                if last_row['Type'] == 'm': # we just finished that set of Hebrew morphemes
                    last_row['Type'] = 'M' # Leave a marker for the last morpheme in a set
                elif last_row['Type'] == 'mK': # we just finished that set of Hebrew morphemes
                    last_row['Type'] = 'MK' # Leave a marker for the last morpheme in a set
                elif last_row['Type'] == 'Am': # we just finished that set of Aramaic morphemes
                    last_row['Type'] = 'AM' # Leave a marker for the last morpheme in a set
                elif last_row['Type'] == 'AmK': # we just finished that set of Aramaic morphemes
                    last_row['Type'] = 'AMK' # Leave a marker for the last morpheme in a set
            if row['Type'] in 'wm': # word or morpheme
                assert row['Morphology'].startswith('H') or row['Morphology'].startswith('A') # Hebrew or Aramaic
                language_code, new_morphology = row['Morphology'][0], row['Morphology'][1:]
                # print(f"  Got {language_code=} {new_morphology=} ")
        if language_code and language_code != 'H':
            assert language_code == 'A'
            assert row['Type'] in 'mw', f"Got {row['FGID']} {language_code=} with {row['Type']=} {row['Morphology']=}"
            new_type = f'{language_code}{new_type}'
        if row['Special']:
            if row['Type'] in 'wm':
                assert row['Special'] == 'K', f"Got {row['FGID']} Ketiv {row['Special']=}"
                new_type = f'{new_type}K'
            else:
                assert row['Type'] == 'note'
                assert row['Special'] in ('variant','alternative','exegesis'), f"Got {row['FGID']} note {row['Special']=}"
                new_type = f"{row['Special']} {new_type}"
        newRowDict = { 'Ref': row['Ref'], 'OSHBid': row['OSHBid'], 'Type': new_type,
                        'Strongs': row['Strongs'], 'CantillationHierarchy': row['CantillationHierarchy'], 'Morphology': new_morphology,
                        'WordOrMorpheme': row['WordOrMorpheme'],
                        'NoCantillations': removeCantillationMarks(row['WordOrMorpheme'], removeMetegOrSiluq=True),
                        'GlossCapitalisation': glossCapitalisation,
                        'GlossOrder': str(glossOrderInt), }
        new_rows.append( newRowDict )
        glossCapitalisation = 'S' if new_morphology=='x-sof-pasuq' else ''
        last_OSIS_base_id, last_row = OSIS_base_id, newRowDict

    # A little check
    last_row = None
    for row in new_rows:
        if row['Type']=='seg' or row['Type'].endswith( 'note' ):
            assert 'm' not in last_row['Type'], f"Expected 'M' in\n{last_row}\nbefore\n{row}"
        last_row = row
    state.WLC_rows = new_rows
    return True
# end of prepare_OSHB_for_glossing.create_expanded_TSV_table


def prefill_known_glosses() -> bool:
    """
    """
    print("  Prefilling TSV table with previously known glosses…")

    print(f"    Loading previously done glosses from {PREDONE_GLOSSES_FILEPATH}…")
    wordGlossDict = {}
    morphemeGlossDict = defaultdict(set)
    wordsSpecificGlossesDict, refsSpecificGlossesDict = {}, {}
    with open( PREDONE_GLOSSES_FILEPATH, 'rt', encoding='utf-8' ) as predone_file:
        for line in predone_file:
            bits = line.rstrip('\n').split( '  ' )
            assert len(bits) == 4
            _referencesList = ast.literal_eval( bits[0] )
            thisWordSpecificGlossesDict = ast.literal_eval( bits[1] )
            genericGloss, word = bits[2], bits[3]
            # print(f"{referencesList=} {wordSpecificGlossesDict=} {genericGloss=} {word=}")
            assert word.count('=') == genericGloss.count('=')
            if '=' in word:
                for wordBit, genericGlossBit in zip( word.split('='), genericGloss.split('=') ):
                    for genericGlossBitBit in genericGlossBit.split('/'):
                        morphemeGlossDict[wordBit].add(genericGlossBitBit)
                assert word not in wordGlossDict
                wordGlossDict[word] = genericGloss
            else:
                assert word not in wordGlossDict
                wordGlossDict[word] = genericGloss
            if thisWordSpecificGlossesDict:
                # print(f"{referencesList=} {wordSpecificGlossesDict=} {genericGloss=} {word=}")
                assert len(thisWordSpecificGlossesDict) == 1 # Only one reference entry
                for ref_4tuple,specificGloss in thisWordSpecificGlossesDict.items(): # only loops once so we use final values
                    assert len(ref_4tuple) == 4
                    ourRef = f'{ref_4tuple[0]}_{ref_4tuple[1]}:{ref_4tuple[2]}w{ref_4tuple[3]}'
                assert word not in wordsSpecificGlossesDict
                wordsSpecificGlossesDict[word] = (ourRef, specificGloss)
                assert ourRef not in refsSpecificGlossesDict
                refsSpecificGlossesDict[ourRef] = (word, specificGloss)
    # pprint(wordsSpecificGlossesDict)
    # pprint(refsSpecificGlossesDict)
    assert len(wordsSpecificGlossesDict) == len(refsSpecificGlossesDict)

    print(f"    Applying {len(wordGlossDict):,} word and {len(morphemeGlossDict):,} morpheme glosses and {len(refsSpecificGlossesDict):,} specific glosses…")
    numAppliedWordGlosses = numAppliedMorphemeGlosses = numAppliedSpecificGlosses = numManualMorphemeGlosses = 0
    combinedMorphemes = ''
    verseSegNoteCount = 0
    lastVerseRef = ''
    for row in state.WLC_rows: # Alters these rows in place
        thisBaseRef = row['Ref'] if row['Ref'][-1].isdigit() else row['Ref'][:-1] # drop morpheme suffix letter
        if 'w' in thisBaseRef: # There's a word number
            thisVerseRef, wordNumber = thisBaseRef.split('w')
            wordNumberInt = int(wordNumber)
        if thisVerseRef != lastVerseRef:
            verseSegNoteCount = 0

        wordOrMorpheme = row['NoCantillations']
        if row['Type'] in ('w','Aw','wK','AwK'): # A is Aramaic, w is (single-morpheme) word, K is Ketiv
            try:
                row['WordGloss'] = wordGlossDict[wordOrMorpheme]
                numAppliedWordGlosses += 1
            except KeyError: pass
        elif row['Type'] in ('m','M','Am','AM','mK','MK','AmK','AMK'): # A is Aramaic, m is morpheme, M is last morpheme in word, K is Ketiv
            if row['Strongs'] == 'b': # manual override for bet
                # print( f" {row['Ref']} '{wordOrMorpheme}' Strongs={row['Strongs']} n={row['CantillationHierarchy']} morph={row['Morphology']}" )
                # if row['CantillationHierarchy']: assert row['CantillationHierarchy'] == '1.0' # Fails: some a blank, some 1.0, some 1.2, etc.
                # assert row['Morphology'] in ('R','Rd','HR') # is this an error: DEU_11:4-18a Strongs=b n=1.0 morph=HR ?
                row['MorphemeGloss'] = 'in/on/at/with'
                numManualMorphemeGlosses += 1
            elif row['Strongs'] == 'c': # manual override for conjunction
                # print( f" {row['Ref']} '{wordOrMorpheme}' Strongs={row['Strongs']} n={row['CantillationHierarchy']} morph={row['Morphology']}" )
                # assert row['Morphology'] in ('C','HC') # is this an error: LEV_15:13-17a Strongs=c n=0 morph=HC ?
                row['MorphemeGloss'] = 'and'
                numManualMorphemeGlosses += 1
            elif row['Strongs'] == 'd': # manual override for determiner
                # print( f" {row['Ref']} '{wordOrMorpheme}' Strongs={row['Strongs']} n={row['CantillationHierarchy']} morph={row['Morphology']}" )
                # assert row['Morphology'] in ('Td','Ti','HTd') # is this an error: NUM_13:29-17a Strongs=d n=0 morph=HTd ?
                row['MorphemeGloss'] = 'the'
                numManualMorphemeGlosses += 1
            else: # general case
                try:
                    row['MorphemeGloss'] = '/'.join(morphemeGlossDict[wordOrMorpheme])
                    numAppliedMorphemeGlosses += 1
                except KeyError: print("skip morpheme")
            combinedMorphemes = f"{combinedMorphemes}{'=' if combinedMorphemes else ''}{wordOrMorpheme}"
            if row['Type'] in ('M','AM','MK','AMK'): # A is Aramaic, M is last morpheme in word, K is Ketiv
                # print( f" {row['Ref']} final morpheme='{wordOrMorpheme}' word='{combinedMorphemes}'" )
                try:
                    row['WordGloss'] = wordGlossDict[combinedMorphemes] # Contains = signs
                    numAppliedWordGlosses += 1
                except KeyError: pass
        else:
            assert row['Type']=='seg' or row['Type'].endswith('note'), f"{row['Ref']} got {row['Type']=}"
            verseSegNoteCount += 1

        # Allow for the fact that the old interlineariser counted segs and notes as words (but we don't now)
        # print(f"{thisBaseRef=} {thisVerseRef=} {wordNumberInt=} {row['Type']=} {verseSegNoteCount=}")
        adjBaseRef = f'{thisVerseRef}w{wordNumberInt+verseSegNoteCount}'
        # print(f"{adjBaseRef=}")
        if adjBaseRef in refsSpecificGlossesDict:
            specificWord, specificGloss = refsSpecificGlossesDict[adjBaseRef]
            if 'w' in row['Type']:
                # print( f"{row['Ref']=} {thisBaseRef=} {row['Type']} {specificWord=} {wordOrMorpheme=} {specificGloss=}" )
                assert specificWord == wordOrMorpheme
                row['ContextualWordGloss'] = specificGloss
                numAppliedSpecificGlosses += 1
            elif 'M' in row['Type']:
                # print( f"{row['Ref']=} {thisBaseRef=} {row['Type']} {specificWord=} {combinedMorphemes=} {specificGloss=}" )
                assert specificWord == combinedMorphemes
                row['ContextualWordGloss'] = specificGloss
                numAppliedSpecificGlosses += 1
        if row['Type'] in ('M','AM','MK','AMK'): # A is Aramaic, M is last morpheme in word, K is Ketiv
            combinedMorphemes = '' # reset
        lastVerseRef = thisVerseRef

    print(f"      Applied {numAppliedWordGlosses:,} word and {numAppliedMorphemeGlosses:,} morpheme glosses\n"
          f"        with {numManualMorphemeGlosses:,} manual morphome glosses and {numAppliedSpecificGlosses:,} specific glosses…")

    return True
# end of prepare_OSHB_for_glossing.prefill_known_glosses


def save_expanded_TSV_file() -> bool:
    """
    Reorganise columns and add our extra columns
    """
    print( f"Exporting adjusted WLC table as a single flat TSV file to {state.TSV_output_filepath}…" )
    with open( state.TSV_output_filepath, 'wt', encoding='utf-8' ) as tsv_output_file:
        tsv_output_file.write('\ufeff') # Write BOM
        writer = DictWriter( tsv_output_file, fieldnames=state.expanded_headers, delimiter='\t' )
        writer.writeheader()
        writer.writerows( state.WLC_rows )
    print( f"  {len(state.WLC_rows):,} data rows written." )

    return True
# end of prepare_OSHB_for_glossing.save_expanded_TSV_file


if __name__ == '__main__':
    # from multiprocessing import freeze_support
    # freeze_support() # Multiprocessing support for frozen Windows executables

    # Configure basic Bible Organisational System (BOS) set-up
    parser = BibleOrgSysGlobals.setup( SHORT_PROGRAM_NAME, PROGRAM_VERSION, LAST_MODIFIED_DATE )
    BibleOrgSysGlobals.addStandardOptionsAndProcess( parser )

    main()

    BibleOrgSysGlobals.closedown( PROGRAM_NAME, PROGRAM_VERSION )
# end of prepare_OSHB_for_glossing.py
