#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# apply_Clear_Macula_OT_glosses.py
#
# Script handling apply_Clear_Macula_OT_glosses functions
#
# Copyright (C) 2022-2024 Robert Hunt
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
    and filling columns with Clear.Bible low-fat glosses.
Then we use some of the flattened tree information
    to automatically reorder gloss words.

We discovered that the low-fat XML trees have the same information
    that's in the LowFat glosses TSV table
    plus a contextual gloss, so we no longer use the TSV.

(This is run AFTER convert_OSHB_XML_to_TSV.py
                and prepare_OSHB_for_glossing.py
                and convert_ClearMaculaOT_to_our_TSV.py.)

We also now convert the low-fat XML trees to an abbreviated TSV table (dropping some unnecessary columns)
    so we now use that table here instead of the XML trees directly.

OSHB morphology codes can be found at https://hb.openscriptures.org/parsing/HebrewMorphologyCodes.html.

CHANGELOG:
    2024-03-20 Create a word table as well as the morpheme table
    2024-03-27 Substitute KJB for KJV in 2000+ OSHB notes
    2024-04-26 Change 'you' to 'you_all' if morphology shows it's plural
"""
from gettext import gettext as _
# from typing import Dict, List, Tuple
from pathlib import Path
from csv import DictReader, DictWriter
from collections import defaultdict
import logging

if __name__ == '__main__':
    import sys
    sys.path.insert( 0, '../../BibleOrgSys/' )
from BibleOrgSys import BibleOrgSysGlobals
from BibleOrgSys.BibleOrgSysGlobals import vPrint, fnPrint, dPrint


LAST_MODIFIED_DATE = '2024-04-28' # by RJH
SHORT_PROGRAM_NAME = "apply_Clear_Macula_OT_glosses"
PROGRAM_NAME = "Apply Macula OT glosses"
PROGRAM_VERSION = '0.67'
PROGRAM_NAME_VERSION = f'{SHORT_PROGRAM_NAME} v{PROGRAM_VERSION}'

DEBUGGING_THIS_MODULE = False


OUR_TSV_INPUT_FILEPATH = Path( '../intermediateTexts/glossed_OSHB/our_WLC_glosses.morphemes.tsv' ) # In
LOWFAT_TSV_INPUT_FILEPATH = Path( '../intermediateTexts/Clear.Bible_lowfat_trees/ClearLowFatTrees.OT.morphemes.abbrev.tsv' ) # In, we use the smaller, abbreviated table

OUR_MORPHEME_TSV_OUTPUT_FILEPATH = Path( '../intermediateTexts/glossed_OSHB/all_glosses.morphemes.tsv' ) # Out
OUR_LEMMA_TSV_OUTPUT_FILEPATH = Path( '../intermediateTexts/glossed_OSHB/all_glosses.lemmas.tsv' ) # Out
OUR_WORD_TSV_OUTPUT_FILEPATH = Path( '../intermediateTexts/glossed_OSHB/all_glosses.words.tsv' ) # Out


state = None
class State:
    def __init__( self ) -> None:
        """
        Constructor:
        """
        self.our_TSV_input_filepath = OUR_TSV_INPUT_FILEPATH
        self.lowfat_TSV_input_folderpath = LOWFAT_TSV_INPUT_FILEPATH

        self.our_morpheme_TSV_output_filepath = OUR_MORPHEME_TSV_OUTPUT_FILEPATH
        self.our_lemma_TSV_output_filepath = OUR_LEMMA_TSV_OUTPUT_FILEPATH
        self.our_word_TSV_output_filepath = OUR_WORD_TSV_OUTPUT_FILEPATH

        self.lemma_output_fieldnames = ['Lemma', 'Glosses']

        self.WLC_rows = []
        self.lowFatRows = []
    # end of apply_Clear_Macula_OT_glosses.__init__


NUM_EXPECTED_WLC_COLUMNS = 16
WLC_tsv_column_max_length_counts = {}
WLC_tsv_column_non_blank_counts = {}
WLC_tsv_column_counts = defaultdict(lambda: defaultdict(int))
WLC_tsv_column_headers = []

NUM_EXPECTED_LOWFAT_COLUMNS = 28
LowFat_tsv_column_max_length_counts = {}
LowFat_tsv_column_non_blank_counts = {}
LowFat_tsv_column_counts = defaultdict(lambda: defaultdict(int))
LowFat_tsv_column_headers = []


def main() -> None:
    """
    """
    BibleOrgSysGlobals.introduceProgram( __name__, PROGRAM_NAME_VERSION, LAST_MODIFIED_DATE )
    global state
    state = State()

    if loadOurSourceTable():
        if loadOurLowFatTable():
            if fill_known_lowFat_English_contextual_glosses():
                if do_yalls():
                    if do_auto_reordering():
                        save_filled_morpheme_TSV_file()
                        save_lemma_TSV_file()
                        save_filled_word_TSV_file()
# end of apply_Clear_Macula_OT_glosses.main


def loadOurSourceTable() -> bool:
    """
    Loads our expanded OSHB WLC table.
    """
    global WLC_tsv_column_headers
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"\nLoading OSHB WLC tsv file from {state.our_TSV_input_filepath}…")
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  Expecting {NUM_EXPECTED_WLC_COLUMNS} columns…")
    with open(state.our_TSV_input_filepath, 'rt', encoding='utf-8') as tsv_file:
        tsv_lines = tsv_file.readlines()

    # Remove any BOM
    if tsv_lines[0].startswith("\ufeff"):
        vPrint( 'Quiet', DEBUGGING_THIS_MODULE, "  Handling Byte Order Marker (BOM) at start of WLC tsv file…")
        tsv_lines[0] = tsv_lines[0][1:]

    # Get the headers before we start
    WLC_tsv_header_line = tsv_lines[0].strip()
    assert WLC_tsv_header_line == 'Ref\tOSHBid\tRowType\tStrongs\tCantillationHierarchy\tMorphology\tWordOrMorpheme\tNoCantillations\tMorphemeGloss\tContextualMorphemeGloss\tWordGloss\tContextualWordGloss\tGlossCapitalisation\tGlossPunctuation\tGlossOrder\tGlossInsert', f"{WLC_tsv_header_line=}"
    WLC_tsv_column_headers = [header for header in WLC_tsv_header_line.split('\t')]
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
            # if row['Ref'].startswith('PSA_') and row['WordOrMorpheme'].startswith('KJV:Ps.') and row['WordOrMorpheme'].endswith('.1'):
            #     # This signals the end of a Psalm description field (past of the first verse in the original Hebrew versification)
            #     print(row)
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


def loadOurLowFatTable() -> bool:
    """
    Load the abbreviated "LowFat" TSV table.
    """
    global LowFat_tsv_column_headers
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"\nLoading our LowFat tsv file from {state.lowfat_TSV_input_folderpath}…")
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  Expecting {NUM_EXPECTED_LOWFAT_COLUMNS} columns…")
    with open(state.lowfat_TSV_input_folderpath, 'rt', encoding='utf-8') as tsv_file:
        tsv_lines = tsv_file.readlines()

    # Remove any BOM
    if tsv_lines[0].startswith("\ufeff"):
        vPrint( 'Quiet', DEBUGGING_THIS_MODULE, "  Handling Byte Order Marker (BOM) at start of LowFat tsv file…")
        tsv_lines[0] = tsv_lines[0][1:]

    # Get the headers before we start
    our_TSV_header_line = tsv_lines[0].strip()
    assert our_TSV_header_line == 'FGRef\tOSHBid\tRowType\tWordOrMorpheme\tAfter\tCompound\tWordClass\tPartOfSpeech\tPerson\tGender\tNumber\tWordType\tState\tRole\tStrongNumberX\tStrongLemma\tStem\tMorphology\tLemma\tSenseNumber\tSubjRef\tParticipantRef\tFrame\tGreek\tGreekStrong\tEnglishGloss\tContextualGloss\tNesting', f"{our_TSV_header_line=}"
    LowFat_tsv_column_headers = [header for header in our_TSV_header_line.split('\t')]
    dPrint('Info', DEBUGGING_THIS_MODULE, f"Column headers: ({len(LowFat_tsv_column_headers)}): {LowFat_tsv_column_headers}")
    assert len(LowFat_tsv_column_headers) == NUM_EXPECTED_LOWFAT_COLUMNS, f"{len(LowFat_tsv_column_headers)=} vs {NUM_EXPECTED_LOWFAT_COLUMNS=}"

    # Read, check the number of columns, and summarise row contents all in one go
    dict_reader = DictReader(tsv_lines, delimiter='\t')
    unique_morphemes, unique_words = set(), set()
    assembled_word = ''
    for n, row in enumerate(dict_reader):
        if len(row) != NUM_EXPECTED_LOWFAT_COLUMNS:
            logging.error(f"Line {n} has {len(row)} columns instead of {NUM_EXPECTED_LOWFAT_COLUMNS}!!!")
        state.lowFatRows.append(row)
        row_type = row['RowType']
        if row_type != 'm' and assembled_word:
            dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"{assembled_word=}")
            unique_words.add(assembled_word)
            assembled_word = ''
        if row_type in ('w','Aw','wK','AwK'): # w=word, A=Aramaic (rather than Hebrew), K=Ketiv
            unique_words.add(row['WordOrMorpheme'])
        elif row_type in ('m','M','Am','AM','mK','MK','AmK','AMK'): # m=morpheme, M=last morpheme in word, A=Aramaic (rather than Hebrew), K=Ketiv
            unique_morphemes.add(row['WordOrMorpheme'])
            assembled_word = f"{assembled_word}{row['WordOrMorpheme']}"
        else: vPrint( 'Quiet', DEBUGGING_THIS_MODULE, row_type); unexpected_row_type
        for key, value in row.items():
            # LowFat[key].add(value)
            if n==0: # We do it like this (rather than using a defaultdict(int)) so that all fields are entered into the dict in the correct order
                LowFat_tsv_column_max_length_counts[key] = 0
                LowFat_tsv_column_non_blank_counts[key] = 0
            if value:
                if len(value) > LowFat_tsv_column_max_length_counts[key]:
                    LowFat_tsv_column_max_length_counts[key] = len(value)
                LowFat_tsv_column_non_blank_counts[key] += 1
            LowFat_tsv_column_counts[key][value] += 1
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  Loaded {len(state.lowFatRows):,} (tsv) LowFat data rows.")
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"    Have {len(unique_words):,} unique Hebrew words.")
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"    Have {len(unique_morphemes):,} unique Hebrew morphemes.")

    return True
# end of apply_Clear_Macula_OT_glosses.loadOurLowFatTable


# def loadLowFatGlossTable() -> bool:
#     """
#     """
#     global LowFat_tsv_column_headers
#     vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"\nLoading Clear.Bible LowFat tsv file from {state.lowfat_TSV_input_folderpath}…")
#     vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  Expecting {NUM_EXPECTED_LOWFAT_COLUMNS} columns…")
#     with open(state.lowfat_TSV_input_folderpath, 'rt', encoding='utf-8') as tsv_file:
#         tsv_lines = tsv_file.readlines()

#     # Remove any BOM
#     if tsv_lines[0].startswith("\ufeff"):
#         vPrint( 'Quiet', DEBUGGING_THIS_MODULE, "  Handling Byte Order Marker (BOM) at start of LowFat tsv file…")
#         tsv_lines[0] = tsv_lines[0][1:]

#     # Get the headers before we start
#     tsv_header_line = tsv_lines[0].strip()
#     assert tsv_header_line == 'xx', f"{tsv_header_line=}"
#     # LowFat_tsv_column_headers = [header for header in tsv_lines[0].strip().split('\t')]
#     # dPrint('Info', DEBUGGING_THIS_MODULE, f"Column headers: ({len(LowFat_tsv_column_headers)}): {LowFat_tsv_column_headers}")
#     # assert len(LowFat_tsv_column_headers) == NUM_EXPECTED_CHERITH_COLUMNS

#     # Read, check the number of columns, and summarise row contents all in one go
#     dict_reader = DictReader(tsv_lines, fieldnames=LowFat_tsv_column_headers, delimiter='\t')
#     unique_morphemes = set()
#     for n, row in enumerate(dict_reader):
#         if len(row) != NUM_EXPECTED_LOWFAT_COLUMNS:
#             logging.error(f"Line {n} has {len(row)} columns instead of {NUM_EXPECTED_LOWFAT_COLUMNS}!!!")
#         state.LowFat_rows.append(row)
#         unique_morphemes.add(row['WLC_word_or_morpheme'])
#         for key, value in row.items():
#             # LowFat_tsv_column_sets[key].add(value)
#             if n==0: # We do it like this (rather than using a defaultdict(int)) so that all fields are entered into the dict in the correct order
#                 LowFat_tsv_column_max_length_counts[key] = 0
#                 LowFat_tsv_column_non_blank_counts[key] = 0
#             if value:
#                 if len(value) > LowFat_tsv_column_max_length_counts[key]:
#                     LowFat_tsv_column_max_length_counts[key] = len(value)
#                 LowFat_tsv_column_non_blank_counts[key] += 1
#             LowFat_tsv_column_counts[key][value] += 1
#     vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  Loaded {len(state.LowFat_rows):,} (tsv) LowFat data rows.")
#     vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"    Have {len(unique_morphemes):,} unique Hebrew morphemes.")

#     return False
# # end of apply_Clear_Macula_OT_glosses.loadLowFatGlossTable


def fill_known_lowFat_English_contextual_glosses() -> bool:
    """
    Because the Hebrew accents differ from our OSHB WLC text
        vs. the Clear.Bible text, we remove accents as necessary before comparing.
    """
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, "\nFilling TSV table with Clear.Bible contextual English LowFat glosses…")

    # First make a dictionary to easily get to our WLC rows
    WLC_dict = {row['OSHBid']:n for n,row in enumerate(state.WLC_rows) if row['OSHBid'] and row['RowType'] not in ('seg','note')}
    dPrint('Info', DEBUGGING_THIS_MODULE, f"  {len(WLC_dict):,} entries in WLC dict")

    num_empty_lowfat_word_glosses = num_word_glosses_added = num_word_glosses_skipped = num_contextual_word_glosses_added = 0
    num_empty_lowfat_morpheme_glosses = num_morpheme_glosses_added = num_morpheme_glosses_skipped = num_contextual_morpheme_glosses_added = 0
    for lowFatRow in state.lowFatRows:
        if DEBUGGING_THIS_MODULE:
            print( f"{lowFatRow=}" )
            if lowFatRow['FGRef'].startswith( 'GEN_13:11' ): missing_glosses_in_GEN_13_10

        if not lowFatRow['EnglishGloss'] and not lowFatRow['ContextualGloss']:
            if 'w' in lowFatRow['RowType']:
                num_empty_lowfat_word_glosses += 1
            elif 'm' in lowFatRow['RowType'] or 'M' in lowFatRow['RowType']:
                num_empty_lowfat_morpheme_glosses += 1
            else: raise Exception("Unexpected lowfat type")
            continue

        if lowFatRow['OSHBid']:
            n = WLC_dict[lowFatRow['OSHBid']]
            guessed = False
        else:
            # dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  Skipped low fat row without OSHBid: {lowFatRow['FGRef']} '{lowFatRow['WordOrMorpheme']}'")
            n += 1 # Try the next row after the one using in the previous loop
            dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  Next row is: {state.WLC_rows[n]}")
            if state.WLC_rows[n]['NoCantillations'] != lowFatRow['WordOrMorpheme']:
                logging.critical( f"Next row guess didn't match {lowFatRow['FGRef']} '{lowFatRow['WordOrMorpheme']}' '{state.WLC_rows[n]['NoCantillations']}'" )
                continue
            guessed = True

        WLC_row = state.WLC_rows[n]
        dPrint('Info', DEBUGGING_THIS_MODULE, f"  Matched row: {WLC_row['Ref']}")

        # Not true if we just guessed above
        if not guessed:
            assert WLC_row['OSHBid'] == lowFatRow['OSHBid'], f"Should be equal: '{WLC_row['OSHBid']}' vs '{lowFatRow['OSHBid']}'"
        if WLC_row['RowType'].endswith('K'):
            pass
            # if WLC_row['RowType']!='mK' or lowFatRow['RowType']!='M': # We still have some problems, e.g., at 'JOS_24:8w1','SA1_2:3w13','SA1_7:9w6'
            #     assert WLC_row['RowType'][:-1] == lowFatRow['RowType'], f"Should be equal: '{WLC_row['RowType'][:-1]}(K)' vs '{lowFatRow['RowType']}'"
        else:
            if not guessed and WLC_row['Ref'] not in ('JER_11:15w10b','AMO_6:14w14b'): # Why ???
                assert WLC_row['RowType'] == lowFatRow['RowType'], f"Should be equal: '{WLC_row['RowType']}' vs '{lowFatRow['RowType']}'"
        if not WLC_row['WordOrMorpheme'] == lowFatRow['WordOrMorpheme']:
            dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  Should be equal: '{WLC_row['WordOrMorpheme']}' vs '{lowFatRow['WordOrMorpheme']}'" )
        dPrint( 'Info', DEBUGGING_THIS_MODULE, f"    Fully matched row: {WLC_row['Ref']}")

        if WLC_row['RowType'] in ('w','Aw','wK','AwK'):
            if lowFatRow['EnglishGloss']:
                if WLC_row['WordGloss']:
                    dPrint( 'Info', DEBUGGING_THIS_MODULE, f"    Skipping replacing {WLC_row['Ref']} word gloss '{WLC_row['WordGloss']}' with '{lowFatRow['EnglishGloss']}'" )
                    num_word_glosses_skipped += 1
                else:
                    dPrint( 'Info', DEBUGGING_THIS_MODULE, f"    Setting {WLC_row['Ref']} '{WLC_row['WordOrMorpheme']}' word gloss to '{lowFatRow['EnglishGloss']}'" )
                    WLC_row['WordGloss'] = lowFatRow['EnglishGloss']
                    num_word_glosses_added += 1
            if lowFatRow['ContextualGloss']:
                if WLC_row['ContextualWordGloss']:
                    dPrint( 'Info', DEBUGGING_THIS_MODULE, f"    Skipping replacing {WLC_row['Ref']} contextual word gloss '{WLC_row['ContextualWordGloss']}' with '{lowFatRow['ContextualGloss']}'" )
                    num_word_glosses_skipped += 1
                else:
                    dPrint( 'Info', DEBUGGING_THIS_MODULE, f"    Setting {WLC_row['Ref']} '{WLC_row['WordOrMorpheme']}' contextual word gloss to '{lowFatRow['ContextualGloss']}'" )
                    WLC_row['ContextualWordGloss'] = lowFatRow['ContextualGloss']
                    num_contextual_word_glosses_added += 1
        else: # it's a morpheme
            assert WLC_row['RowType'] in ('m','Am','mK','AmK','M','AM','MK','AMK')
            if lowFatRow['EnglishGloss']:
                if WLC_row['MorphemeGloss']:
                    dPrint( 'Info', DEBUGGING_THIS_MODULE, f"    Skipping replacing {WLC_row['Ref']} morpheme gloss '{WLC_row['ContextualMorphemeGloss']}' with '{lowFatRow['EnglishGloss']}'" )
                    num_morpheme_glosses_skipped += 1
                else:
                    dPrint( 'Info', DEBUGGING_THIS_MODULE, f"    Setting {WLC_row['Ref']} '{WLC_row['WordOrMorpheme']}' morpheme gloss to '{lowFatRow['EnglishGloss']}'" )
                    WLC_row['MorphemeGloss'] = lowFatRow['EnglishGloss']
                    num_morpheme_glosses_added += 1
            if lowFatRow['ContextualGloss']:
                if WLC_row['ContextualMorphemeGloss']:
                    dPrint( 'Info', DEBUGGING_THIS_MODULE, f"    Skipping replacing {WLC_row['Ref']} contextual morpheme gloss '{WLC_row['ContextualMorphemeGloss']}' with '{lowFatRow['ContextualGloss']}'" )
                    num_morpheme_glosses_skipped += 1
                else:
                    dPrint( 'Info', DEBUGGING_THIS_MODULE, f"    Setting {WLC_row['Ref']} '{WLC_row['WordOrMorpheme']}' contextual morpheme gloss to '{lowFatRow['ContextualGloss']}'" )
                    WLC_row['ContextualMorphemeGloss'] = lowFatRow['ContextualGloss']
                    num_contextual_morpheme_glosses_added += 1

    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Added {num_word_glosses_added:,} LowFat English word glosses." )
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Added {num_morpheme_glosses_added:,} LowFat English morpheme glosses." )
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Added {num_contextual_word_glosses_added:,} LowFat contextual English word glosses." )
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Added {num_contextual_morpheme_glosses_added:,} LowFat contextual English morpheme glosses." )
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Didn't add {num_word_glosses_skipped:,} LowFat English word glosses (because we had something already)." )
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Didn't add {num_morpheme_glosses_skipped:,} LowFat English morpheme glosses (because we had something already)." )
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Skipped {num_empty_lowfat_word_glosses:,} empty LowFat English word glosses." )
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Skipped {num_empty_lowfat_morpheme_glosses:,} empty LowFat English morpheme glosses." )
    return True
# end of apply_Clear_Macula_OT_glosses.fill_known_lowFat_English_contextual_glosses


def do_yalls() -> bool:
    """
    Go through all our OT glosses and change 'you' to 'you_all' if the morphology is plural
    """
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, "\nConverting to 'you_all' for plural and dual 2nd person pronouns plus marking plural/dual verbs…" )

    num_rows_changed = num_fields_changed = 0
    num_plurals = num_duals = 0
    for WLC_row_dict in state.WLC_rows:
        morphology = originalMorphology = WLC_row_dict['Morphology']
        if not morphology: continue # probably a seg or a note
        # print( f"{morphology=} from {WLC_row_dict}")
        PoS = morphology[0]
        if PoS in 'ART': # adjectives, prepositions, particles
            continue
        if morphology=='Sn':
            dPrint( 'Normal', DEBUGGING_THIS_MODULE, f"Why Sn??? Ignoring {WLC_row_dict}" ) # paragogic nun
            continue

        if PoS=='V':
            if len(morphology)==3 and morphology[-1] in 'ac':
                continue # no person marked in infinitives
            elif len(morphology)==6 and morphology[-1] in 'acd':
                morphology = morphology[:-1] # Remove the final 'state' character
        else: # not a verb
            combinedGlosses = f"{WLC_row_dict['MorphemeGloss']} {WLC_row_dict['ContextualMorphemeGloss']} {WLC_row_dict['WordGloss']} {WLC_row_dict['ContextualWordGloss']}"
            if 'you' not in combinedGlosses:
                continue
            if 'young' in combinedGlosses \
            or 'youth' in combinedGlosses \
            or '[you]' in combinedGlosses:
                continue

            if PoS=='N':
                if len(morphology)==5 and morphology[-1] in 'acd':
                    morphology = morphology[:-1] # Remove the final 'state' character
            assert PoS in 'SVPN' and morphology[-1] in 'sp', f"{WLC_row_dict=}"

        numberIndicator = morphology[-1]
        if numberIndicator == 's': continue # not interested in singulars
        assert numberIndicator in 'pd', f"{numberIndicator=} from {morphology=} from {originalMorphology=}" # plural or dual

        row_changed = False
        for fieldname in ('MorphemeGloss', 'ContextualMorphemeGloss', 'WordGloss', 'ContextualWordGloss'):
            newField = originalField = WLC_row_dict[fieldname]

            if numberIndicator == 'p': # plural
                if 'you' not in originalField or 'you_all' in originalField or 'yourselves' in originalField: continue
                if 'yourself' in newField:
                    newField = newField.replace( 'yourself', 'yourselves' )
                elif 'your' in newField:
                    newField = newField.replace( 'your(pl)', "your_all's" ) if 'your(pl)' in newField else newField.replace( 'your', "your_all's" )
                else:
                    newField = newField.replace( 'you(pl)', 'you_all' ) if 'you(pl)' in newField else newField.replace( 'you', 'you_all' )
                if morphology[0]=='V' and 'you_all' not in newField and '(pl)' not in newField:
                    newField = f'{newField}(pl)' # append a plural indicator
                num_plurals += 1

            elif numberIndicator == 'd': # dual
                if 'you' not in originalField or 'you_two' in originalField or 'yourtwoselves' in originalField: continue
                if 'yourself' in newField:
                    newField = newField.replace( 'yourself', 'yourtwoselves' )
                elif 'yourselves' in newField:
                    newField = newField.replace( 'yourselves', 'yourtwoselves' )
                elif 'your' in newField:
                    newField = newField.replace( 'your(2)', "your_two's" ) if 'your(2)' in newField else newField.replace( 'your', "your_two's" )
                else:
                    newField = newField.replace( 'you(pl)', 'you_two' ) if 'you(pl)' in newField else newField.replace( 'you', 'you_two' )
                if morphology[0]=='V' and 'you_two' not in newField and '(2)' not in newField:
                    newField = f'{newField}(2)' # append a dual indicator
                num_duals += 1

            assert newField != originalField
            WLC_row_dict[fieldname] = newField
            num_fields_changed += 1
            row_changed = True
        # dPrint( 'Info', DEBUGGING_THIS_MODULE, f"{changed} {WLC_row_dict=}")
        if row_changed: num_rows_changed += 1

    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  do_yalls() changed {num_fields_changed:,} fields in {num_rows_changed:,} table rows ({num_plurals:,} plurals and {num_duals:,} duals)." )
    return num_fields_changed > 0
# end of apply_Clear_Macula_OT_glosses.do_yalls


def do_auto_reordering() -> bool:
    """
    Reordering OT glosses to try to put subjects before their verbs, etc.
    """
    # DEBUGGING_THIS_MODULE = 99
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, "\nTrying to reorder OT glosses…" )

    # First make a dictionary to easily get to our LowFat rows
    LF_dict = {row['OSHBid']:n for n,row in enumerate(state.lowFatRows) if row['OSHBid']}
    dPrint('Quiet', DEBUGGING_THIS_MODULE, f"  {len(LF_dict):,} entries in LowFat dict")

    reorder_vn_count = reorder_von_count = reorder_vnn_count = reorder_vdn_count = 0
    last4_WLC_row = state.WLC_rows[0]
    last3_WLC_row = state.WLC_rows[1]
    last2_WLC_row = state.WLC_rows[2]
    last1_WLC_row = state.WLC_rows[3]
    for WLC_row in state.WLC_rows[4:]: # these 'rows' are dictionaries
        # if WLC_row['Ref'].startswith( 'GEN_3:12w5'):
        #     break
        
        if WLC_row['OSHBid']:
            try: n = LF_dict[WLC_row['OSHBid']]
            except KeyError:
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  Skipped LowFat row without OSHBid: {WLC_row['Ref']} {WLC_row['OSHBid']}")
                continue
        else:
            # dPrint( 'Never', DEBUGGING_THIS_MODULE, f"  Skipped WLC row without OSHBid: {WLC_row['Ref']}")
            continue

        last4_LF_row = state.lowFatRows[n-4]
        last3_LF_row = state.lowFatRows[n-3]
        last2_LF_row = state.lowFatRows[n-2]
        last1_LF_row = state.lowFatRows[n-1]
        LF_row = state.lowFatRows[n]

        dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"    {last4_LF_row['FGRef']}\t{last4_LF_row['RowType']}  {last4_LF_row['EnglishGloss']}\twC={last4_LF_row['WordClass']}\tPoS={last4_LF_row['PartOfSpeech']}\twT={last4_LF_row['WordType']}\t{last4_LF_row['Nesting']}" )
        dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"    {last3_LF_row['FGRef']}\t{last3_LF_row['RowType']}  {last3_LF_row['EnglishGloss']}\twC={last3_LF_row['WordClass']}\tPoS={last3_LF_row['PartOfSpeech']}\twT={last3_LF_row['WordType']}\t{last3_LF_row['Nesting']}" )
        dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"    {last2_LF_row['FGRef']}\t{last2_LF_row['RowType']}  {last2_LF_row['EnglishGloss']}\twC={last2_LF_row['WordClass']}\tPoS={last2_LF_row['PartOfSpeech']}\twT={last2_LF_row['WordType']}\t{last2_LF_row['Nesting']}" )
        dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"    {last1_LF_row['FGRef']}\t{last1_LF_row['RowType']}  {last1_LF_row['EnglishGloss']}\twC={last1_LF_row['WordClass']}\tPoS={last1_LF_row['PartOfSpeech']}\twT={last1_LF_row['WordType']}\t{last1_LF_row['Nesting']}" )
        dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"    {LF_row['FGRef']}\t{LF_row['RowType']}  {LF_row['EnglishGloss']}\twC={LF_row['WordClass']}\tPoS={LF_row['PartOfSpeech']}\twT={LF_row['WordType']}\t{LF_row['Nesting']}" )

        if LF_row['PartOfSpeech']=='n' and LF_row['Nesting'].split('/')[-1]=='s=n2np': # Subject is single noun
            dPrint( 'Info', DEBUGGING_THIS_MODULE, f"\n  Have a simple noun subject: {LF_row['FGRef']} {LF_row['RowType']} '{LF_row['WordClass']}' {LF_row['PartOfSpeech']} '{LF_row['EnglishGloss']}'" )

            # Look for verb followed by subject
            if ( '/' in last1_LF_row['Nesting'] and 'v-s' in last1_LF_row['Nesting'].split('/')[-2] 
            and last1_LF_row['PartOfSpeech']=='v'
            and last1_LF_row['Nesting'].split('/')[-1] == 'v=v2vp' ): # Verb is a single word
                # Possibly have a verb followed by its subject
                if last1_LF_row['EnglishGloss'] in ('be','was','there_was'):
                    continue # skip these
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"      {last1_LF_row['FGRef']}\t{last1_LF_row['RowType']}\t{last1_LF_row['EnglishGloss']}\t{last1_LF_row['WordClass']}\t{last1_LF_row['PartOfSpeech']}\t{last1_LF_row['Nesting']}" )
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"      {LF_row['FGRef']}\t{LF_row['RowType']}\t{LF_row['EnglishGloss']}\t{LF_row['WordClass']}\t{LF_row['PartOfSpeech']}\t{LF_row['Nesting']}" )
                # dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  {last_WLC_row['Ref']}\t{last_WLC_row['GlossOrder']}")
                # dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  {WLC_row['Ref']}\t{WLC_row['GlossOrder']}")
                if int(last1_WLC_row['GlossOrder']) < int(WLC_row['GlossOrder']):
                    dPrint( 'Info', DEBUGGING_THIS_MODULE, f"    Let's swap the v-s order for {WLC_row['Ref'].split('w')[0]} '{last1_WLC_row['WordGloss']}' '{WLC_row['WordGloss']}'")
                    last1_WLC_row['GlossOrder'], WLC_row['GlossOrder'] = WLC_row['GlossOrder'], last1_WLC_row['GlossOrder']
                    reorder_vn_count += 1

            # Look for verb followed by DOM and direct object then subject
            if ( last2_LF_row['WordClass']=='om' and last2_LF_row['PartOfSpeech']=='part'
                and '/' in last2_LF_row['Nesting'] and 'v-o-s' in last2_LF_row['Nesting'].split('/')[-2]
            and last3_LF_row['Nesting'].split('/')[-1] == 'v=v2vp' ): # Verb is a single word
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"      {last3_LF_row['FGRef']}\t{last3_LF_row['RowType']}\t{last3_LF_row['EnglishGloss']}\t{last3_LF_row['WordClass']}\t{last3_LF_row['PartOfSpeech']}\t{last3_LF_row['Nesting']}" )
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"      {last2_LF_row['FGRef']}\t{last2_LF_row['RowType']}\t{last2_LF_row['EnglishGloss']}\t{last2_LF_row['WordClass']}\t{last2_LF_row['PartOfSpeech']}\t{last2_LF_row['Nesting']}" )
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"      {last1_LF_row['FGRef']}\t{last1_LF_row['RowType']}\t{last1_LF_row['EnglishGloss']}\t{last1_LF_row['WordClass']}\t{last1_LF_row['PartOfSpeech']}\t{last1_LF_row['Nesting']}" )
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"      {LF_row['FGRef']}\t{LF_row['RowType']}\t{LF_row['EnglishGloss']}\t{LF_row['WordClass']}\t{LF_row['PartOfSpeech']}\t{LF_row['Nesting']}" )
                if int(last3_WLC_row['GlossOrder']) < int(last2_WLC_row['GlossOrder']) < int(last1_WLC_row['GlossOrder']) < int(WLC_row['GlossOrder']):
                    dPrint( 'Info', DEBUGGING_THIS_MODULE, f"    Let's swap the v-o-s order for {WLC_row['Ref'].split('w')[0]} '{last3_WLC_row['WordGloss']}' '{WLC_row['WordGloss']}'")
                    last3_WLC_row['GlossOrder'], last2_WLC_row['GlossOrder'], last1_WLC_row['GlossOrder'], WLC_row['GlossOrder'] = \
                        last2_WLC_row['GlossOrder'], last1_WLC_row['GlossOrder'], WLC_row['GlossOrder'], last3_WLC_row['GlossOrder']
                    reorder_von_count += 1

        elif ( LF_row['PartOfSpeech']=='n' and LF_row['Nesting'].split('/')[-1]=='s=detnp'
        and last1_LF_row['PartOfSpeech']=='part' and last1_LF_row['Nesting'].split('/')[-1]=='s=detnp' # Subject is determiner noun phrase
        and state.lowFatRows[n+1]['Nesting'].split('/')[-1]!='s=detnp'): # But not a triple one
            dPrint( 'Info', DEBUGGING_THIS_MODULE, f"\n  Have a determiner noun subject: {LF_row['FGRef']} {LF_row['RowType']} '{LF_row['WordClass']}' {LF_row['PartOfSpeech']} '{last1_LF_row['EnglishGloss']} {LF_row['EnglishGloss']}'" )

            # Look for verb followed by subject
            if ( '/' in last2_LF_row['Nesting'] and 'v-s' in last2_LF_row['Nesting'].split('/')[-2] 
            and last2_LF_row['PartOfSpeech']=='v'
            and last2_LF_row['Nesting'].split('/')[-1] == 'v=v2vp' ): # Verb is a single word
                # Possibly have a verb followed by its subject
                # if last2_LF_row['EnglishGloss'] in ('be','was','there_was'):
                #     continue # skip these
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"      {last2_LF_row['FGRef']}\t{last2_LF_row['RowType']}\t{last2_LF_row['EnglishGloss']}\t{last2_LF_row['WordClass']}\t{last2_LF_row['PartOfSpeech']}\t{last2_LF_row['Nesting']}" )
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"      {last1_LF_row['FGRef']}\t{last1_LF_row['RowType']}\t{last1_LF_row['EnglishGloss']}\t{last1_LF_row['WordClass']}\t{last1_LF_row['PartOfSpeech']}\t{last1_LF_row['Nesting']}" )
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"      {LF_row['FGRef']}\t{LF_row['RowType']}\t{LF_row['EnglishGloss']}\t{LF_row['WordClass']}\t{LF_row['PartOfSpeech']}\t{LF_row['Nesting']}" )
                if int(last2_WLC_row['GlossOrder']) < int(last1_WLC_row['GlossOrder']) < int(WLC_row['GlossOrder']):
                    dPrint( 'Info', DEBUGGING_THIS_MODULE, f"    Let's swap the v-s order for {WLC_row['Ref'].split('w')[0]} '{last2_WLC_row['WordGloss']} {last1_WLC_row['WordGloss']}' '{WLC_row['WordGloss']}'")
                    last2_WLC_row['GlossOrder'], last1_WLC_row['GlossOrder'], WLC_row['GlossOrder'] = WLC_row['GlossOrder'], last2_WLC_row['GlossOrder'], last1_WLC_row['GlossOrder']
                    reorder_vdn_count += 1

            # # Look for verb followed by DOM and direct object then subject
            # if ( last2_LF_row['WordClass']=='om' and last2_LF_row['PartOfSpeech']=='part'
            #     and '/' in last2_LF_row['Nesting'] and 'v-o-s' in last2_LF_row['Nesting'].split('/')[-2]
            # and last3_LF_row['Nesting'].split('/')[-1] == 'v=v2vp' ): # Verb is a single word
            #     dPrint( 'Info', DEBUGGING_THIS_MODULE, f"      {last3_LF_row['FGRef']}\t{last3_LF_row['RowType']}\t{last3_LF_row['EnglishGloss']}\t{last3_LF_row['WordClass']}\t{last3_LF_row['PartOfSpeech']}\t{last3_LF_row['Nesting']}" )
            #     dPrint( 'Info', DEBUGGING_THIS_MODULE, f"      {last2_LF_row['FGRef']}\t{last2_LF_row['RowType']}\t{last2_LF_row['EnglishGloss']}\t{last2_LF_row['WordClass']}\t{last2_LF_row['PartOfSpeech']}\t{last2_LF_row['Nesting']}" )
            #     dPrint( 'Info', DEBUGGING_THIS_MODULE, f"      {last1_LF_row['FGRef']}\t{last1_LF_row['RowType']}\t{last1_LF_row['EnglishGloss']}\t{last1_LF_row['WordClass']}\t{last1_LF_row['PartOfSpeech']}\t{last1_LF_row['Nesting']}" )
            #     dPrint( 'Info', DEBUGGING_THIS_MODULE, f"      {LF_row['FGRef']}\t{LF_row['RowType']}\t{LF_row['EnglishGloss']}\t{LF_row['WordClass']}\t{LF_row['PartOfSpeech']}\t{LF_row['Nesting']}" )
            #     if int(last3_WLC_row['GlossOrder']) < int(WLC_row['GlossOrder']):
            #         dPrint( 'Info', DEBUGGING_THIS_MODULE, f"    Let's swap the v-o-s order for {WLC_row['Ref'].split('w')[0]} '{last3_WLC_row['WordGloss']}' '{WLC_row['WordGloss']}'")
            #         last3_WLC_row['GlossOrder'], last2_WLC_row['GlossOrder'], last1_WLC_row['GlossOrder'], WLC_row['GlossOrder'] = \
            #             last2_WLC_row['GlossOrder'], last1_WLC_row['GlossOrder'], WLC_row['GlossOrder'], last3_WLC_row['GlossOrder']
            #         reorder_count += 1

        elif ( LF_row['PartOfSpeech']=='n' and LF_row['Nesting'].split('/')[-1]=='s=np-appos'
        and last1_LF_row['PartOfSpeech']=='n' and last1_LF_row['Nesting'].split('/')[-1]=='s=np-appos' # Subject is double noun
        and state.lowFatRows[n+1]['Nesting'].split('/')[-1]!='s=np-appos'): # But not a triple one
            dPrint( 'Info', DEBUGGING_THIS_MODULE, f"\n  Have a double noun subject: {LF_row['FGRef']} {LF_row['RowType']} '{LF_row['WordClass']}' {LF_row['PartOfSpeech']} '{last1_LF_row['EnglishGloss']} {LF_row['EnglishGloss']}'" )

            # Look for verb followed by subject
            if ( '/' in last2_LF_row['Nesting'] and 'v-s' in last2_LF_row['Nesting'].split('/')[-2] 
            and last2_LF_row['PartOfSpeech']=='v'
            and last2_LF_row['Nesting'].split('/')[-1] == 'v=v2vp' ): # Verb is a single word
                # Possibly have a verb followed by its subject
                if last2_LF_row['EnglishGloss'] in ('be','was','there_was'):
                    continue # skip these
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"      {last2_LF_row['FGRef']}\t{last2_LF_row['RowType']}\t{last2_LF_row['EnglishGloss']}\t{last2_LF_row['WordClass']}\t{last2_LF_row['PartOfSpeech']}\t{last2_LF_row['Nesting']}" )
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"      {last1_LF_row['FGRef']}\t{last1_LF_row['RowType']}\t{last1_LF_row['EnglishGloss']}\t{last1_LF_row['WordClass']}\t{last1_LF_row['PartOfSpeech']}\t{last1_LF_row['Nesting']}" )
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"      {LF_row['FGRef']}\t{LF_row['RowType']}\t{LF_row['EnglishGloss']}\t{LF_row['WordClass']}\t{LF_row['PartOfSpeech']}\t{LF_row['Nesting']}" )
                if int(last2_WLC_row['GlossOrder']) < int(last1_WLC_row['GlossOrder']) < int(WLC_row['GlossOrder']):
                    dPrint( 'Info', DEBUGGING_THIS_MODULE, f"    Let's swap the v-s order for {WLC_row['Ref'].split('w')[0]} '{last2_WLC_row['WordGloss']} {last1_WLC_row['WordGloss']}' '{WLC_row['WordGloss']}'")
                    last2_WLC_row['GlossOrder'], last1_WLC_row['GlossOrder'], WLC_row['GlossOrder'] = WLC_row['GlossOrder'], last2_WLC_row['GlossOrder'], last1_WLC_row['GlossOrder']
                    reorder_vnn_count += 1

            # # Look for verb followed by DOM and direct object then subject
            # if ( last2_LF_row['WordClass']=='om' and last2_LF_row['PartOfSpeech']=='part'
            #     and '/' in last2_LF_row['Nesting'] and 'v-o-s' in last2_LF_row['Nesting'].split('/')[-2]
            # and last3_LF_row['Nesting'].split('/')[-1] == 'v=v2vp' ): # Verb is a single word
            #     dPrint( 'Info', DEBUGGING_THIS_MODULE, f"      {last3_LF_row['FGRef']}\t{last3_LF_row['RowType']}\t{last3_LF_row['EnglishGloss']}\t{last3_LF_row['WordClass']}\t{last3_LF_row['PartOfSpeech']}\t{last3_LF_row['Nesting']}" )
            #     dPrint( 'Info', DEBUGGING_THIS_MODULE, f"      {last2_LF_row['FGRef']}\t{last2_LF_row['RowType']}\t{last2_LF_row['EnglishGloss']}\t{last2_LF_row['WordClass']}\t{last2_LF_row['PartOfSpeech']}\t{last2_LF_row['Nesting']}" )
            #     dPrint( 'Info', DEBUGGING_THIS_MODULE, f"      {last1_LF_row['FGRef']}\t{last1_LF_row['RowType']}\t{last1_LF_row['EnglishGloss']}\t{last1_LF_row['WordClass']}\t{last1_LF_row['PartOfSpeech']}\t{last1_LF_row['Nesting']}" )
            #     dPrint( 'Info', DEBUGGING_THIS_MODULE, f"      {LF_row['FGRef']}\t{LF_row['RowType']}\t{LF_row['EnglishGloss']}\t{LF_row['WordClass']}\t{LF_row['PartOfSpeech']}\t{LF_row['Nesting']}" )
            #     if int(last3_WLC_row['GlossOrder']) < int(WLC_row['GlossOrder']):
            #         dPrint( 'Info', DEBUGGING_THIS_MODULE, f"    Let's swap the v-o-s order for {WLC_row['Ref'].split('w')[0]} '{last3_WLC_row['WordGloss']}' '{WLC_row['WordGloss']}'")
            #         last3_WLC_row['GlossOrder'], last2_WLC_row['GlossOrder'], last1_WLC_row['GlossOrder'], WLC_row['GlossOrder'] = \
            #             last2_WLC_row['GlossOrder'], last1_WLC_row['GlossOrder'], WLC_row['GlossOrder'], last3_WLC_row['GlossOrder']
            #         reorder_count += 1

        last4_WLC_row = last3_WLC_row
        last3_WLC_row = last2_WLC_row
        last2_WLC_row = last1_WLC_row
        last1_WLC_row = WLC_row

    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  Reordered {reorder_vn_count+reorder_von_count+reorder_vnn_count+reorder_vdn_count:,} total sets." )
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"    Reordered {reorder_vn_count:,} single-noun v-s pairs." )
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"    Reordered {reorder_vdn_count:,} determiner-noun v-s sets." )
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"    Reordered {reorder_von_count:,} single-noun v-o-s pairs." )
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"    Reordered {reorder_vnn_count:,} double-noun v-s sets." )

    return True
# end of apply_Clear_Macula_OT_glosses.do_auto_reordering


def save_filled_morpheme_TSV_file() -> bool:
    """
    Save the filled TSV table with a row for each morpheme

    We do some final fixes
    """
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"\nExporting filled WLC morpheme table as a single flat TSV file to {state.our_morpheme_TSV_output_filepath}…" )

    BibleOrgSysGlobals.backupAnyExistingFile( state.our_morpheme_TSV_output_filepath, numBackups=5 )

    with open( state.our_morpheme_TSV_output_filepath, 'wt', encoding='utf-8' ) as tsv_output_file:
        tsv_output_file.write('\ufeff') # Write BOM
        writer = DictWriter( tsv_output_file, fieldnames=WLC_tsv_column_headers, delimiter='\t' )
        writer.writeheader()
        for n,row_dict in enumerate( state.WLC_rows, start=1 ):
            if row_dict['RowType']=='m' and not row_dict['MorphemeGloss']:
                # if 0 and row_dict['NoCantillations'] in ('אֹתָ','אֹת'):
                if row_dict['Strongs'] == '853':
                    row_dict['MorphemeGloss'] = 'DOM'
                elif row_dict['Strongs'] == 'k':
                    row_dict['MorphemeGloss'] = 'as/like'
                elif row_dict['Strongs'] == 'l':
                    row_dict['MorphemeGloss'] = 'to/for'
                elif row_dict['Strongs'] == 'm':
                    row_dict['MorphemeGloss'] = 'from'
                elif row_dict['Strongs'] == '6440':
                    row_dict['MorphemeGloss'] = 'face/front'
                # assert row_dict['MorphemeGloss'], f"{n} {row_dict}"
            writer.writerow( row_dict )
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  {len(state.WLC_rows):,} morpheme data rows written." )

    return True
# end of apply_Clear_Macula_OT_glosses.save_filled_morpheme_TSV_file


def save_lemma_TSV_file() -> bool:
    """
    Save a row for each lemma with its glosses

    TODO: Why is the same code in convert_ClearMaculaOT_to_our_TSV.py???
    """
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"\nCreating and exporting OT lemma table from Low Fat table as a single flat TSV file to {state.our_lemma_TSV_output_filepath}…" )


    # Firstly, let's create the lemma table
    state.lemma_formation_dict = defaultdict(set)
    num_missing_lemmas = 0
    morphemes_with_missing_lemmas = set()
    for thisRowDict in state.lowFatRows:
        # print( f"{thisRowDict=}" )
        fgRef, wordOrMorpheme, lemma, gloss = thisRowDict['FGRef'], thisRowDict['WordOrMorpheme'], thisRowDict['Lemma'], thisRowDict['EnglishGloss']
        # assert ',' not in gloss, thisRow # Check our separator's not in the data -- fails on "1,000"
        assert ';' not in gloss
        if lemma:
            if gloss:
                state.lemma_formation_dict[lemma].add( gloss )
        else: # no lemma
            if fgRef.startswith( 'GEN_1:'):
                print( f"Why do we have no lemma for {fgRef} {wordOrMorpheme=}?" )
            morphemes_with_missing_lemmas.add( wordOrMorpheme )
            num_missing_lemmas += 1
    print( f"{num_missing_lemmas:,} morphemes with no lemmas => {len(morphemes_with_missing_lemmas):,} unique morphemes_with_missing_lemmas={sorted(morphemes_with_missing_lemmas)}")
    print( f"Extracted {len(state.lemma_formation_dict):,} Hebrew lemmas from {len(state.lowFatRows):,} morphemes" )
    # print( f"{state.lemma_formation_dict=}" )
    
    # Preprocess it in the sorted order
    new_dict = {}
    # state.lemma_index_dict = {}
    for n, hebrew_lemma in enumerate( sorted( state.lemma_formation_dict ), start=1 ):
        new_dict[hebrew_lemma] = ';'.join( sorted( state.lemma_formation_dict[hebrew_lemma], key=str.casefold ) )
        # state.lemma_index_dict[hebrew_lemma] = n
    state.lemma_formation_dict = new_dict
    # print( f"{state.lemma_formation_dict=}" )
    # print( f"{state.lemma_index_dict=}" )


    BibleOrgSysGlobals.backupAnyExistingFile( state.our_lemma_TSV_output_filepath, numBackups=5 )

    non_blank_counts = defaultdict(int)
    sets = defaultdict(set)
    with open( state.our_lemma_TSV_output_filepath, 'wt', encoding='utf-8' ) as tsv_output_file:
        tsv_output_file.write('\ufeff') # Write BOM
        writer = DictWriter( tsv_output_file, fieldnames=state.lemma_output_fieldnames, delimiter='\t' )
        writer.writeheader()
        for lemma,glosses in state.lemma_formation_dict.items():
            thisEntryDict = {}
            thisEntryDict['Lemma'] = lemma
            thisEntryDict['Glosses'] = glosses
            assert len(thisEntryDict) == len(state.lemma_output_fieldnames)
            writer.writerow( thisEntryDict )
            for fieldname,value in thisEntryDict.items():
                if value: non_blank_counts[fieldname] += 1
                sets[fieldname].add( value )
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  {len(state.lemma_formation_dict):,} lemma ({len(state.lemma_output_fieldnames)} fields) data rows written to {state.our_lemma_TSV_output_filepath}." )

    # if 1: # Print stats
    #     vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"\nCounts of non-blank fields for {len(state.lemma_formation_dict):,} rows:" )
    #     for fieldname,count in non_blank_counts.items():
    #         non_blank_count_str = 'all' if count==len(state.lemma_formation_dict) else f'{count:,}'
    #         unique_count_str = 'all' if len(sets[fieldname])==len(state.lemma_formation_dict) else f'{len(sets[fieldname]):,}'
    #         vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  {fieldname}: {non_blank_count_str} non-blank entries (with {unique_count_str} unique entries)" )
    #         assert count # Otherwise we're including a field that contains nothing!
    #         if len(sets[fieldname]) < 50:
    #             vPrint( 'Info', DEBUGGING_THIS_MODULE, f"    being: {sets[fieldname]}" )

    return True
# end of apply_Clear_Macula_OT_glosses.save_lemma_TSV_file


def save_filled_word_TSV_file() -> bool:
    """
    Save the TSV table with a row for each word
    """
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"\nExporting filled WLC word table as a single flat TSV file to {state.our_word_TSV_output_filepath}…" )

    BibleOrgSysGlobals.backupAnyExistingFile( state.our_word_TSV_output_filepath, numBackups=5 )

    # Firstly adjust the column headers
    WLC_tsv_header_line = '\t'.join( WLC_tsv_column_headers )
    word_tsv_column_header_line = ( WLC_tsv_header_line.replace( '\tRowType\t', '\tRowType\tMorphemeRowList\t') # Add column
                                                .replace( 'WordOrMorpheme', 'Word' ) # rename this column
                                                # .replace( '\tMorphemeGloss', '' ) # delete this column
                                                # .replace( '\tContextualMorphemeGloss', '' ) # delete this column
                                                .replace( 'MorphemeGloss', 'MorphemeGlosses' ) # rename these two columns
                                )
    assert word_tsv_column_header_line == 'Ref\tOSHBid\tRowType\tMorphemeRowList\tStrongs\tCantillationHierarchy\tMorphology\tWord\tNoCantillations\tMorphemeGlosses\tContextualMorphemeGlosses\tWordGloss\tContextualWordGloss\tGlossCapitalisation\tGlossPunctuation\tGlossOrder\tGlossInsert', f"{word_tsv_column_header_line=}"
    word_tsv_column_headers = word_tsv_column_header_line.split( '\t' )
    assert len(word_tsv_column_headers) == len(WLC_tsv_column_headers)+1 == 17, f"{len(word_tsv_column_headers)=} {len(WLC_tsv_column_headers)=}"
    
    with open( state.our_word_TSV_output_filepath, 'wt', encoding='utf-8' ) as tsv_output_file:
        tsv_output_file.write('\ufeff') # Write BOM
        writer = DictWriter( tsv_output_file, fieldnames=word_tsv_column_headers, delimiter='\t' )
        writer.writeheader()

        num_data_rows_written = 0
        morpheme_row_list, morpheme_strongs_list, morpheme_morphology_list, morpheme_list, morpheme_noCantillations_list, morpheme_glosses_list, contextual_morpheme_glosses_list = [], [], [], [], [], [], []
        morpheme_gloss_capitalisation = ''
        ref = OSHB_id = morpheme_cantillation_hierarchy = morpheme_gloss_order = None
        for n,original_column_dict in enumerate( state.WLC_rows, start=1 ):
            # print( f"{n} {original_column_dict}" )
            if 'w' in original_column_dict['RowType']:
                for column_name in ('MorphemeGloss','ContextualMorphemeGloss','GlossPunctuation','GlossInsert'):
                    assert not original_column_dict[column_name], f"{n} {column_name=} {original_column_dict[column_name]=}"
                word_entry = {}
                for new_header in word_tsv_column_headers:
                    word_entry[new_header] = original_column_dict['RowType'].replace('w','') if new_header=='RowType' \
                                            else n if new_header=='MorphemeRowList' \
                                            else original_column_dict['WordOrMorpheme' if new_header=='Word'
                                                                       else 'MorphemeGloss' if new_header=='MorphemeGlosses'
                                                                       else 'ContextualMorphemeGloss' if new_header=='ContextualMorphemeGlosses'
                                                                       else new_header]
                # print( f"{n} {original_column_dict=} {word_entry=}")
                writer.writerow( word_entry )
                num_data_rows_written += 1
            elif 'm' in original_column_dict['RowType']:
                if ref is None:
                    assert original_column_dict['Ref'][-1] in 'abcde'
                    ref = original_column_dict['Ref'][:-1] # Remove the lowercase letter suffix
                    assert len(ref) >= 9
                else:
                    assert ref == original_column_dict['Ref'][:-1]
                if OSHB_id is None:
                    assert original_column_dict['OSHBid'][-1] in 'abcde'
                    OSHB_id = original_column_dict['OSHBid'][:-1] # Remove the lowercase letter suffix
                    assert len(OSHB_id) == 5
                else:
                    assert OSHB_id == original_column_dict['OSHBid'][:-1]
                morpheme_row_list.append( str(n) )
                for column_name in ('Strongs','Morphology','WordOrMorpheme','NoCantillations','MorphemeGloss','ContextualMorphemeGloss'):
                    assert ',' not in original_column_dict[column_name], f"{n} {column_name=} {original_column_dict[column_name]=}"
                morpheme_strongs_list.append( original_column_dict['Strongs'] )
                morpheme_morphology_list.append( original_column_dict['Morphology'] )
                morpheme_list.append( original_column_dict['WordOrMorpheme'] )
                morpheme_noCantillations_list.append( original_column_dict['NoCantillations'] )
                morpheme_glosses_list.append( original_column_dict['MorphemeGloss'] )
                # assert morpheme_glosses_list[0], f"{ref} {morpheme_glosses_list=} will end up starting with a comma separator"
                contextual_morpheme_glosses_list.append( original_column_dict['ContextualMorphemeGloss'] )
                if morpheme_cantillation_hierarchy is None:
                    morpheme_cantillation_hierarchy = original_column_dict['CantillationHierarchy']
                else:
                    assert morpheme_cantillation_hierarchy == original_column_dict['CantillationHierarchy']
                for column_name in ('WordGloss','ContextualWordGloss','GlossPunctuation','GlossInsert'):
                    assert not original_column_dict[column_name], f"{n} {column_name=} {original_column_dict[column_name]=}"
                if original_column_dict['GlossCapitalisation']:
                    assert not morpheme_gloss_capitalisation
                    morpheme_gloss_capitalisation = original_column_dict['GlossCapitalisation']
                if morpheme_gloss_order is None:
                    morpheme_gloss_order = original_column_dict['GlossOrder'] # We take the first one and ignore the rest
            elif 'M' in original_column_dict['RowType']: # the final morpheme in the word
                assert ref == original_column_dict['Ref'][:-1]
                assert OSHB_id == original_column_dict['OSHBid'][:-1]
                morpheme_row_list.append( str(n) )
                for column_name in ('Strongs','Morphology','WordOrMorpheme','NoCantillations','MorphemeGloss','ContextualMorphemeGloss'):
                    assert ',' not in original_column_dict[column_name], f"{n} {column_name=} {original_column_dict[column_name]=}"
                morpheme_strongs_list.append( original_column_dict['Strongs'] )
                morpheme_morphology_list.append( original_column_dict['Morphology'] )
                morpheme_list.append( original_column_dict['WordOrMorpheme'] )
                morpheme_noCantillations_list.append( original_column_dict['NoCantillations'] )
                morpheme_glosses_list.append( original_column_dict['MorphemeGloss'] )
                if not any(morpheme_glosses_list): morpheme_glosses_list = [] # Don't want to end up with just a comma separator there
                contextual_morpheme_glosses_list.append( original_column_dict['ContextualMorphemeGloss'] )
                assert morpheme_cantillation_hierarchy == original_column_dict['CantillationHierarchy']
                for column_name in ('GlossCapitalisation','GlossPunctuation','GlossInsert'):
                    assert not original_column_dict[column_name], f"{n} {column_name=} {original_column_dict[column_name]=}"
                word_entry = {}
                for new_header in word_tsv_column_headers:
                    word_entry[new_header] = ( ref if new_header=='Ref'
                                        else OSHB_id if new_header=='OSHBid'
                                        else original_column_dict['RowType'].replace('M','') if new_header=='RowType'
                                        else ','.join(morpheme_row_list) if new_header=='MorphemeRowList'
                                        else ','.join(morpheme_strongs_list) if new_header=='Strongs'
                                        else ','.join(morpheme_morphology_list) if new_header=='Morphology'
                                        else ','.join(morpheme_list) if new_header=='Word'
                                        else ','.join(morpheme_noCantillations_list) if new_header=='NoCantillations'
                                        else ','.join(morpheme_glosses_list) if new_header=='MorphemeGlosses'
                                        else (','.join(contextual_morpheme_glosses_list) if any(contextual_morpheme_glosses_list) else '') if new_header=='ContextualMorphemeGlosses' # Don't just put commas in if all empty strings
                                        else morpheme_gloss_capitalisation if new_header=='GlossCapitalisation'
                                        else morpheme_gloss_order if new_header=='GlossOrder'
                                        else original_column_dict['WordOrMorpheme' if new_header=='Word' else new_header]
                                        )
                # print( f"{n} {original_column_dict=} {word_entry=}")
                writer.writerow( word_entry )
                num_data_rows_written += 1
                morpheme_row_list, morpheme_strongs_list, morpheme_morphology_list, morpheme_list, morpheme_noCantillations_list, morpheme_glosses_list, contextual_morpheme_glosses_list = [], [], [], [], [], [], []
                morpheme_gloss_capitalisation = ''
                ref = OSHB_id = morpheme_cantillation_hierarchy = morpheme_gloss_order = None
            elif original_column_dict['RowType'] in ('seg','note','variant note','alternative note','exegesis note'):
                assert not original_column_dict['OSHBid']
                # print( f"{n}: {original_column_dict}" )
                word_entry = {}
                for new_header in word_tsv_column_headers:
                    word_entry[new_header] = ( n if new_header=='MorphemeRowList'
                                            else original_column_dict['WordOrMorpheme'].replace('KJV:','KJB: ') if new_header=='Word'
                                            else original_column_dict['MorphemeGloss' if new_header=='MorphemeGlosses'
                                                                    else 'ContextualMorphemeGloss' if new_header=='ContextualMorphemeGlosses'
                                                                    else new_header]
                                            )
                writer.writerow( word_entry )
                num_data_rows_written += 1
            else: halt

    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  {num_data_rows_written:,} word data rows written." )

    return True
# end of apply_Clear_Macula_OT_glosses.save_filled_word_TSV_file


if __name__ == '__main__':
    # from multiprocessing import freeze_support
    # freeze_support() # Multiprocessing support for frozen Windows executables

    # Configure basic Bible Organisational System (BOS) set-up
    parser = BibleOrgSysGlobals.setup( SHORT_PROGRAM_NAME, PROGRAM_VERSION, LAST_MODIFIED_DATE )
    BibleOrgSysGlobals.addStandardOptionsAndProcess( parser )

    main()

    BibleOrgSysGlobals.closedown( PROGRAM_NAME, PROGRAM_VERSION )
# end of apply_Clear_Macula_OT_glosses.py
