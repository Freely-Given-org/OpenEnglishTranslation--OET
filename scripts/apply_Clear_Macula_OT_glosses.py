#!/usr/bin/env python3
# -\*- coding: utf-8 -\*-
# SPDX-License-Identifier: GPL-3.0-or-later
#
# apply_Clear_Macula_OT_glosses.py
#
# Script handling apply_Clear_Macula_OT_glosses functions
#
# Copyright (C) 2022-2025 Robert Hunt
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
    and filling columns with Clear.Bible MaculaHebrew glosses.
Then we use some of the flattened tree information
    to automatically reorder gloss words.

(We previously tried using the MaculaHebrew TSV tables,
    but discovered that the XML trees have the same information
    that's in the MaculaHebrew glosses TSV table
    plus a contextual gloss, so we no longer use their TSV.
Then we had to switch from their "low-fat" XML to their "nodes" XML
    because the former has information missing for compound words.)

This is run AFTER convert_OSHB_XML_to_TSV.py
                and prepare_OSHB_for_glossing.py
                and convert_ClearMaculaOT_to_our_TSV.py.

We also now convert the MaculaHebrew XML trees to an abbreviated TSV table (dropping some unnecessary columns)
    so we now use that table here instead of the XML trees directly.

OSHB morphology codes can be found at https://hb.openscriptures.org/parsing/HebrewMorphologyCodes.html.


main() -> None
loadOurOwnSourceTable() -> bool
    Loads our expanded OSHB WLC table into state.WLC_rows list.
loadOurMaculaHebrewTable() -> bool
    Load the abbreviated "MaculaHebrew" TSV table into state.MaculaHebrewRows.
fill_known_MaculaHebrew_English_contextual_glosses() -> bool
    Because the Hebrew accents differ from our OSHB WLC text
        vs. the Clear.Bible text, we remove accents as necessary before comparing.
do_yalls() -> bool
    Go through all our OT glosses and change 'you' to 'you(pl)' if the morphology is plural
do_yahs() -> bool
    Go through all our OT glosses and change 'Yahweh' to 'yah' where appropriate
do_auto_reordering() -> bool
    Reordering OT glosses to try to put subjects before their verbs, etc.
    Does this by changing the GlossOrder fields in state.WLC_rows
        but referring to information from state.MaculaHebrewRows.
save_filled_morpheme_TSV_file() -> bool
    Save the filled TSV table with a row for each morpheme
    We do some final fixes
    This is written from state.WLC_rows.
save_lemma_TSV_file() -> bool
    Save a row for each lemma with its glosses
    This is written from state.MaculaHebrewRows.
    TODO: Why is the same code in convert_ClearMaculaOT_to_our_TSV.py???
save_filled_word_TSV_file() -> bool
    Save the TSV word table with a row for each word.
    This is written from state.WLC_rows.


CHANGELOG:
    2024-03-20 Create a word table as well as the morpheme table
    2024-03-27 Substitute KJB for KJV in 2000+ OSHB notes
    2024-04-26 Change 'you' to 'you(pl)' if morphology shows it's plural
    2024-11-12 Make sure 'יָהּ' is Yah (not Yahweh)
    2025-01-20 Fix reordering to handle Macula Hebrew new slightly different 'nodes' data (rather than the previous 'lowfat')
"""
from gettext import gettext as _
# from typing import Dict, List, Tuple
from pathlib import Path
from csv import DictReader, DictWriter
from collections import defaultdict
import logging
import unicodedata

if __name__ == '__main__':
    import sys
    sys.path.insert( 0, '../../BibleOrgSys/' )
from BibleOrgSys import BibleOrgSysGlobals
from BibleOrgSys.BibleOrgSysGlobals import vPrint, fnPrint, dPrint


LAST_MODIFIED_DATE = '2025-11-03' # by RJH
SHORT_PROGRAM_NAME = "apply_Clear_Macula_OT_glosses"
PROGRAM_NAME = "Apply Macula OT glosses"
PROGRAM_VERSION = '0.71'
PROGRAM_NAME_VERSION = f'{SHORT_PROGRAM_NAME} v{PROGRAM_VERSION}'

DEBUGGING_THIS_MODULE = False


OUR_OWN_TSV_INPUT_FILEPATH = Path( '../intermediateTexts/glossed_OSHB/our_WLC_glosses.morphemes.tsv' ) # In
OUR_MACULA_HEBREW_TSV_INPUT_FILEPATH = Path( '../intermediateTexts/Clear.Bible_derived_Macula_data/Clear.Bible_MaculaHebrew.OT.morphemes.abbrev.tsv' ) # In, we use the smaller, abbreviated table

OUR_MORPHEME_TSV_OUTPUT_FILEPATH = Path( '../intermediateTexts/glossed_OSHB/all_glosses.morphemes.tsv' ) # Out
OUR_LEMMA_TSV_OUTPUT_FILEPATH = Path( '../intermediateTexts/glossed_OSHB/all_glosses.lemmas.tsv' ) # Out
OUR_WORD_TSV_OUTPUT_FILEPATH = Path( '../intermediateTexts/glossed_OSHB/all_glosses.words.tsv' ) # Out -- will eventually be used to make the OET-LV OT ESFM files


state = None
class State:
    def __init__( self ) -> None:
        """
        Constructor:
        """
        self.our_own_TSV_input_filepath = OUR_OWN_TSV_INPUT_FILEPATH
        self.MacularHebrew_TSV_input_folderpath = OUR_MACULA_HEBREW_TSV_INPUT_FILEPATH

        self.our_morpheme_TSV_output_filepath = OUR_MORPHEME_TSV_OUTPUT_FILEPATH
        self.our_lemma_TSV_output_filepath = OUR_LEMMA_TSV_OUTPUT_FILEPATH
        self.our_word_TSV_output_filepath = OUR_WORD_TSV_OUTPUT_FILEPATH

        self.lemma_output_fieldnames = ['Lemma', 'Glosses']

        self.WLC_morpheme_rows = []
        self.MaculaHebrew_morpheme_rows = []
    # end of apply_Clear_Macula_OT_glosses.__init__


NUM_EXPECTED_WLC_COLUMNS = 16
# WLC_tsv_column_max_length_counts = {}
# WLC_tsv_column_non_blank_counts = {}
# WLC_tsv_column_counts = defaultdict(lambda: defaultdict(int))
WLC_tsv_column_headers = []

NUM_EXPECTED_MACULAR_HEBREW_COLUMNS = 28
MaculaHebrew_tsv_column_max_length_counts = {}
MaculaHebrew_tsv_column_non_blank_counts = {}
MaculaHebrew_tsv_column_counts = defaultdict(lambda: defaultdict(int))
MaculaHebrew_tsv_column_headers = []


def main() -> None:
    """
    """
    BibleOrgSysGlobals.introduceProgram( __name__, PROGRAM_NAME_VERSION, LAST_MODIFIED_DATE )
    global state
    state = State()

    if loadOurOwnSourceTable():
        if loadOurMaculaHebrewTable():
            if fill_known_MaculaHebrew_English_contextual_glosses():
                if do_yalls() and do_yahs():
                    if do_auto_reordering():
                        save_filled_morpheme_TSV_file()
                        save_lemma_TSV_file()
                        save_filled_word_TSV_file()
# end of apply_Clear_Macula_OT_glosses.main


def loadOurOwnSourceTable() -> bool:
    """
    Loads our expanded OSHB WLC table into state.WLC_rows list.
    """
    global WLC_tsv_column_headers
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"\nLoading OSHB WLC tsv file from {state.our_own_TSV_input_filepath}…")
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  Expecting {NUM_EXPECTED_WLC_COLUMNS} columns…")
    with open(state.our_own_TSV_input_filepath, 'rt', encoding='utf-8') as tsv_file:
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

        for char in row['NoCantillations']:
            assert 'ACCENT' not in unicodedata.name(char), f"{unicodedata.name(char)=} {row['NoCantillations']=} {row=}"

        state.WLC_morpheme_rows.append(row)
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
        # for key, value in row.items():
        #     # WLC_tsv_column_sets[key].add(value)
        #     if n==0: # We do it like this (rather than using a defaultdict(int)) so that all fields are entered into the dict in the correct order
        #         WLC_tsv_column_max_length_counts[key] = 0
        #         WLC_tsv_column_non_blank_counts[key] = 0
        #     if value:
        #         if len(value) > WLC_tsv_column_max_length_counts[key]:
        #             WLC_tsv_column_max_length_counts[key] = len(value)
        #         WLC_tsv_column_non_blank_counts[key] += 1
        #     WLC_tsv_column_counts[key][value] += 1
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  Loaded {len(state.WLC_morpheme_rows):,} (tsv) WLC data rows.")
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"    Have {len(unique_words):,} unique Hebrew words.")
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"    Have {len(unique_morphemes):,} unique Hebrew morphemes.")
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"    Have {seg_count:,} Hebrew segment markers.")
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"    Have {note_count:,} notes.")

    return True
# end of apply_Clear_Macula_OT_glosses.loadOurOwnSourceTable


def loadOurMaculaHebrewTable() -> bool:
    """
    Load the abbreviated "MaculaHebrew" TSV table into state.MaculaHebrewRows.
    """
    global MaculaHebrew_tsv_column_headers
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"\nLoading our MaculaHebrew tsv file from {state.MacularHebrew_TSV_input_folderpath}…")
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  Expecting {NUM_EXPECTED_MACULAR_HEBREW_COLUMNS} columns…")
    with open(state.MacularHebrew_TSV_input_folderpath, 'rt', encoding='utf-8') as tsv_file:
        tsv_lines = tsv_file.readlines()

    # Remove any BOM
    if tsv_lines[0].startswith("\ufeff"):
        vPrint( 'Quiet', DEBUGGING_THIS_MODULE, "  Handling Byte Order Marker (BOM) at start of MaculaHebrew tsv file…")
        tsv_lines[0] = tsv_lines[0][1:]

    # Get the headers before we start
    our_TSV_header_line = tsv_lines[0].strip()
    assert our_TSV_header_line == 'FGRef\tOSHBid\tRowType\tWordOrMorpheme\tAfter\tCompound\tWordClass\tPartOfSpeech\tPerson\tGender\tNumber\tWordType\tState\tRole\tStrongNumberX\tStrongLemma\tStem\tMorphology\tLemma\tSenseNumber\tSubjRef\tParticipantRef\tFrame\tGreek\tGreekStrong\tEnglishGloss\tContextualGloss\tNesting', f"{our_TSV_header_line=}"
    MaculaHebrew_tsv_column_headers = [header for header in our_TSV_header_line.split('\t')]
    dPrint('Info', DEBUGGING_THIS_MODULE, f"Column headers: ({len(MaculaHebrew_tsv_column_headers)}): {MaculaHebrew_tsv_column_headers}")
    assert len(MaculaHebrew_tsv_column_headers) == NUM_EXPECTED_MACULAR_HEBREW_COLUMNS, f"{len(MaculaHebrew_tsv_column_headers)=} vs {NUM_EXPECTED_MACULAR_HEBREW_COLUMNS=}"

    # Read, check the number of columns, and summarise row contents all in one go
    dict_reader = DictReader(tsv_lines, delimiter='\t')
    unique_morphemes, unique_words = set(), set()
    assembled_word = ''
    for n, row in enumerate(dict_reader):
        if len(row) != NUM_EXPECTED_MACULAR_HEBREW_COLUMNS:
            logging.error(f"Line {n} has {len(row)} columns instead of {NUM_EXPECTED_MACULAR_HEBREW_COLUMNS}!!!")
        for char in row['Lemma']:
            # print( f"{ord(char)=} {unicodedata.name(char)=} {char=} {unicodedata.category(char)=} {unicodedata.bidirectional(char)=} {unicodedata.combining(char)=} {unicodedata.mirrored(char)=}" )
            assert 'ACCENT' not in unicodedata.name(char), f"{unicodedata.name(char)=} {row['FGRef']} {row['WordOrMorpheme']=} {row['Lemma']=}"
        state.MaculaHebrew_morpheme_rows.append(row)
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
            # MaculaHebrew[key].add(value)
            if n==0: # We do it like this (rather than using a defaultdict(int)) so that all fields are entered into the dict in the correct order
                MaculaHebrew_tsv_column_max_length_counts[key] = 0
                MaculaHebrew_tsv_column_non_blank_counts[key] = 0
            if value:
                if len(value) > MaculaHebrew_tsv_column_max_length_counts[key]:
                    MaculaHebrew_tsv_column_max_length_counts[key] = len(value)
                MaculaHebrew_tsv_column_non_blank_counts[key] += 1
            MaculaHebrew_tsv_column_counts[key][value] += 1
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  Loaded {len(state.MaculaHebrew_morpheme_rows):,} (tsv) MaculaHebrew data rows.")
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"    Have {len(unique_words):,} unique Hebrew words.")
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"    Have {len(unique_morphemes):,} unique Hebrew morphemes.")

    return True
# end of apply_Clear_Macula_OT_glosses.loadOurMaculaHebrewTable


# def loadMaculaHebrewGlossTable() -> bool:
#     """
#     """
#     global MaculaHebrew_tsv_column_headers
#     vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"\nLoading Clear.Bible MaculaHebrew tsv file from {state.MaculaHebrew_TSV_input_folderpath}…")
#     vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  Expecting {NUM_EXPECTED_MACULAR_HEBREW_COLUMNS} columns…")
#     with open(state.MaculaHebrew_TSV_input_folderpath, 'rt', encoding='utf-8') as tsv_file:
#         tsv_lines = tsv_file.readlines()

#     # Remove any BOM
#     if tsv_lines[0].startswith("\ufeff"):
#         vPrint( 'Quiet', DEBUGGING_THIS_MODULE, "  Handling Byte Order Marker (BOM) at start of MaculaHebrew tsv file…")
#         tsv_lines[0] = tsv_lines[0][1:]

#     # Get the headers before we start
#     tsv_header_line = tsv_lines[0].strip()
#     assert tsv_header_line == 'xx', f"{tsv_header_line=}"
#     # MaculaHebrew_tsv_column_headers = [header for header in tsv_lines[0].strip().split('\t')]
#     # dPrint('Info', DEBUGGING_THIS_MODULE, f"Column headers: ({len(MaculaHebrew_tsv_column_headers)}): {MaculaHebrew_tsv_column_headers}")
#     # assert len(MaculaHebrew_tsv_column_headers) == NUM_EXPECTED_CHERITH_COLUMNS

#     # Read, check the number of columns, and summarise row contents all in one go
#     dict_reader = DictReader(tsv_lines, fieldnames=MaculaHebrew_tsv_column_headers, delimiter='\t')
#     unique_morphemes = set()
#     for n, row in enumerate(dict_reader):
#         if len(row) != NUM_EXPECTED_MACULAR_HEBREW_COLUMNS:
#             logging.error(f"Line {n} has {len(row)} columns instead of {NUM_EXPECTED_MACULAR_HEBREW_COLUMNS}!!!")
#         state.MaculaHebrew_rows.append(row)
#         unique_morphemes.add(row['WLC_word_or_morpheme'])
#         for key, value in row.items():
#             # MaculaHebrew_tsv_column_sets[key].add(value)
#             if n==0: # We do it like this (rather than using a defaultdict(int)) so that all fields are entered into the dict in the correct order
#                 MaculaHebrew_tsv_column_max_length_counts[key] = 0
#                 MaculaHebrew_tsv_column_non_blank_counts[key] = 0
#             if value:
#                 if len(value) > MaculaHebrew_tsv_column_max_length_counts[key]:
#                     MaculaHebrew_tsv_column_max_length_counts[key] = len(value)
#                 MaculaHebrew_tsv_column_non_blank_counts[key] += 1
#             MaculaHebrew_tsv_column_counts[key][value] += 1
#     vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  Loaded {len(state.MaculaHebrew_rows):,} (tsv) MaculaHebrew data rows.")
#     vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"    Have {len(unique_morphemes):,} unique Hebrew morphemes.")

#     return False
# # end of apply_Clear_Macula_OT_glosses.loadMaculaHebrewGlossTable


def fill_known_MaculaHebrew_English_contextual_glosses() -> bool:
    """
    Because the Hebrew accents differ from our OSHB WLC text
        vs. the Clear.Bible text, we remove accents as necessary before comparing.
    """
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, "\nFilling TSV table with Clear.Bible contextual English MaculaHebrew glosses…" )

    # First make a dictionary to easily get to our WLC rows
    WLC_dict = {row['OSHBid']:n for n,row in enumerate(state.WLC_morpheme_rows) if row['OSHBid'] and row['RowType'] not in ('seg','note')}
    dPrint('Info', DEBUGGING_THIS_MODULE, f"  {len(WLC_dict):,} entries in WLC dict")

    num_empty_MaculaHebrew_word_glosses = num_word_glosses_added = num_word_glosses_skipped = num_contextual_word_glosses_added = 0
    num_empty_MaculaHebrew_morpheme_glosses = num_morpheme_glosses_added = num_morpheme_glosses_skipped = num_contextual_morpheme_glosses_added = 0
    for MaculaHebrewRow in state.MaculaHebrew_morpheme_rows:
        if DEBUGGING_THIS_MODULE:
            print( f"{MaculaHebrewRow=}" )
            # if MaculaHebrewRow['FGRef'].startswith( 'GEN_13:11' ): missing_glosses_in_GEN_13_10

        # Do a fix
        if MaculaHebrewRow['WordOrMorpheme'] == 'כִּי':
            # print( f"{MaculaHebrewRow=}" )
            assert 'DOM' not in MaculaHebrewRow['EnglishGloss'].upper()
            if 'DOM' in MaculaHebrewRow['ContextualGloss'].upper():
                print( f"{MaculaHebrewRow['ContextualGloss']=}" )
                halt # Shouldn't happen now
                MaculaHebrewRow['ContextualGloss'] = MaculaHebrewRow['ContextualGloss'].replace( 'DOM_', '' ).replace( 'DOM', '' )
                assert 'DOM' not in MaculaHebrewRow['ContextualGloss'].upper()

        if not MaculaHebrewRow['EnglishGloss'] and not MaculaHebrewRow['ContextualGloss']:
            if 'w' in MaculaHebrewRow['RowType']:
                num_empty_MaculaHebrew_word_glosses += 1
            elif 'm' in MaculaHebrewRow['RowType'] or 'M' in MaculaHebrewRow['RowType']:
                num_empty_MaculaHebrew_morpheme_glosses += 1
            else: raise Exception("Unexpected MaculaHebrew type")
            continue

        if MaculaHebrewRow['OSHBid']:
            n = WLC_dict[MaculaHebrewRow['OSHBid']]
            guessed = False
        else:
            # dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  Skipped low fat row without OSHBid: {MaculaHebrewRow['FGRef']} '{MaculaHebrewRow['WordOrMorpheme']}'")
            n += 1 # Try the next row after the one using in the previous loop
            dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  Next row is: {state.WLC_morpheme_rows[n]}")
            if state.WLC_morpheme_rows[n]['NoCantillations'] != MaculaHebrewRow['WordOrMorpheme']:
                logging.critical( f"Next row guess didn't match {MaculaHebrewRow['FGRef']} '{MaculaHebrewRow['WordOrMorpheme']}' '{state.WLC_morpheme_rows[n]['NoCantillations']}'" )
                continue
            guessed = True

        WLC_morpheme_row = state.WLC_morpheme_rows[n]
        dPrint('Info', DEBUGGING_THIS_MODULE, f"  Matched row: {WLC_morpheme_row['Ref']}")

        # Not true if we just guessed above
        if not guessed:
            assert WLC_morpheme_row['OSHBid'] == MaculaHebrewRow['OSHBid'], f"Should be equal: '{WLC_morpheme_row['OSHBid']}' vs '{MaculaHebrewRow['OSHBid']}'"
        if WLC_morpheme_row['RowType'].endswith('K'):
            pass
            # if WLC_morpheme_row['RowType']!='mK' or MaculaHebrewRow['RowType']!='M': # We still have some problems, e.g., at 'JOS_24:8w1','SA1_2:3w13','SA1_7:9w6'
            #     assert WLC_morpheme_row['RowType'][:-1] == MaculaHebrewRow['RowType'], f"Should be equal: '{WLC_morpheme_row['RowType'][:-1]}(K)' vs '{MaculaHebrewRow['RowType']}'"
        else:
            if not guessed and WLC_morpheme_row['Ref'] not in ('JER_11:15w10b','AMO_6:14w14b'): # Why ???
                assert WLC_morpheme_row['RowType'] == MaculaHebrewRow['RowType'], f"Should be equal: '{WLC_morpheme_row['RowType']}' vs '{MaculaHebrewRow['RowType']}'"
        if not WLC_morpheme_row['WordOrMorpheme'] == MaculaHebrewRow['WordOrMorpheme']:
            dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  Should be equal: '{WLC_morpheme_row['WordOrMorpheme']}' vs '{MaculaHebrewRow['WordOrMorpheme']}'" )
        dPrint( 'Info', DEBUGGING_THIS_MODULE, f"    Fully matched row: {WLC_morpheme_row['Ref']}")

        if WLC_morpheme_row['RowType'] in ('w','Aw','wK','AwK'):
            if MaculaHebrewRow['EnglishGloss']:
                if WLC_morpheme_row['WordGloss']:
                    dPrint( 'Info', DEBUGGING_THIS_MODULE, f"    Skipping replacing {WLC_morpheme_row['Ref']} word gloss '{WLC_morpheme_row['WordGloss']}' with '{MaculaHebrewRow['EnglishGloss']}'" )
                    num_word_glosses_skipped += 1
                else:
                    dPrint( 'Info', DEBUGGING_THIS_MODULE, f"    Setting {WLC_morpheme_row['Ref']} '{WLC_morpheme_row['WordOrMorpheme']}' word gloss to '{MaculaHebrewRow['EnglishGloss']}'" )
                    WLC_morpheme_row['WordGloss'] = MaculaHebrewRow['EnglishGloss']
                    num_word_glosses_added += 1
            if MaculaHebrewRow['ContextualGloss']:
                if WLC_morpheme_row['ContextualWordGloss']:
                    dPrint( 'Info', DEBUGGING_THIS_MODULE, f"    Skipping replacing {WLC_morpheme_row['Ref']} contextual word gloss '{WLC_morpheme_row['ContextualWordGloss']}' with '{MaculaHebrewRow['ContextualGloss']}'" )
                    num_word_glosses_skipped += 1
                else:
                    dPrint( 'Info', DEBUGGING_THIS_MODULE, f"    Setting {WLC_morpheme_row['Ref']} '{WLC_morpheme_row['WordOrMorpheme']}' contextual word gloss to '{MaculaHebrewRow['ContextualGloss']}'" )
                    WLC_morpheme_row['ContextualWordGloss'] = MaculaHebrewRow['ContextualGloss']
                    num_contextual_word_glosses_added += 1
        else: # it's a morpheme
            assert WLC_morpheme_row['RowType'] in ('m','Am','mK','AmK','M','AM','MK','AMK')
            if MaculaHebrewRow['EnglishGloss']:
                if WLC_morpheme_row['MorphemeGloss']:
                    dPrint( 'Info', DEBUGGING_THIS_MODULE, f"    Skipping replacing {WLC_morpheme_row['Ref']} morpheme gloss '{WLC_morpheme_row['ContextualMorphemeGloss']}' with '{MaculaHebrewRow['EnglishGloss']}'" )
                    num_morpheme_glosses_skipped += 1
                else:
                    dPrint( 'Info', DEBUGGING_THIS_MODULE, f"    Setting {WLC_morpheme_row['Ref']} '{WLC_morpheme_row['WordOrMorpheme']}' morpheme gloss to '{MaculaHebrewRow['EnglishGloss']}'" )
                    WLC_morpheme_row['MorphemeGloss'] = MaculaHebrewRow['EnglishGloss']
                    num_morpheme_glosses_added += 1
            if MaculaHebrewRow['ContextualGloss']:
                if WLC_morpheme_row['ContextualMorphemeGloss']:
                    dPrint( 'Info', DEBUGGING_THIS_MODULE, f"    Skipping replacing {WLC_morpheme_row['Ref']} contextual morpheme gloss '{WLC_morpheme_row['ContextualMorphemeGloss']}' with '{MaculaHebrewRow['ContextualGloss']}'" )
                    num_morpheme_glosses_skipped += 1
                else:
                    dPrint( 'Info', DEBUGGING_THIS_MODULE, f"    Setting {WLC_morpheme_row['Ref']} '{WLC_morpheme_row['WordOrMorpheme']}' contextual morpheme gloss to '{MaculaHebrewRow['ContextualGloss']}'" )
                    WLC_morpheme_row['ContextualMorphemeGloss'] = MaculaHebrewRow['ContextualGloss']
                    num_contextual_morpheme_glosses_added += 1
        if (WLC_morpheme_row['WordGloss'] and '[is]' in WLC_morpheme_row['WordGloss']) or (WLC_morpheme_row['ContextualWordGloss'] and '[is]' in WLC_morpheme_row['ContextualWordGloss']):
            print( f"Have '[is]' in {WLC_morpheme_row['Ref']=} {WLC_morpheme_row['WordOrMorpheme']=} {WLC_morpheme_row['WordGloss']=} {WLC_morpheme_row['ContextualWordGloss']=}" )
        if WLC_morpheme_row['WordGloss']=='[is]' or WLC_morpheme_row['ContextualWordGloss']=='[is]' \
        or (WLC_morpheme_row['WordGloss'] and WLC_morpheme_row['WordGloss'][0]=='[' and WLC_morpheme_row['WordGloss'][-1]==']' and '_' not in WLC_morpheme_row['WordGloss']) \
        or (WLC_morpheme_row['ContextualWordGloss'] and WLC_morpheme_row['ContextualWordGloss'][0]=='[' and WLC_morpheme_row['ContextualWordGloss'][-1]==']' and '_' not in WLC_morpheme_row['ContextualWordGloss']):
            halt

    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Added {num_word_glosses_added:,} MaculaHebrew English word glosses." )
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Added {num_morpheme_glosses_added:,} MaculaHebrew English morpheme glosses." )
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Added {num_contextual_word_glosses_added:,} MaculaHebrew contextual English word glosses." )
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Added {num_contextual_morpheme_glosses_added:,} MaculaHebrew contextual English morpheme glosses." )
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Didn't add {num_word_glosses_skipped:,} MaculaHebrew English word glosses (because we had something already)." )
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Didn't add {num_morpheme_glosses_skipped:,} MaculaHebrew English morpheme glosses (because we had something already)." )
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Skipped {num_empty_MaculaHebrew_word_glosses:,} empty MaculaHebrew English word glosses." )
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Skipped {num_empty_MaculaHebrew_morpheme_glosses:,} empty MaculaHebrew English morpheme glosses." )
    assert num_word_glosses_added > 80_000 # otherwise something stopped working
    assert num_morpheme_glosses_added > 210_000 # otherwise something stopped working
    assert num_contextual_word_glosses_added > 150_000 # otherwise something stopped working
    assert num_contextual_morpheme_glosses_added > 20 # otherwise something stopped working
    return num_word_glosses_added > 0
# end of apply_Clear_Macula_OT_glosses.fill_known_MaculaHebrew_English_contextual_glosses


def do_yalls() -> bool:
    """
    Go through all our OT glosses and change 'you' to 'you(pl)' if the morphology is plural
    """
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, "\nConverting to 'you(pl)' for plural and dual 2nd person pronouns plus marking plural/dual verbs…" )

    num_rows_changed = num_fields_changed = 0
    num_plurals = num_duals = 0
    for WLC_row_dict in state.WLC_morpheme_rows:
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
                if 'you' not in originalField or 'you(pl)' in originalField or 'yourselves' in originalField: continue
                if 'yourself' in newField:
                    newField = newField.replace( 'yourself', 'yourselves' )
                elif 'your' in newField and 'your(pl)' not in newField:
                    # newField = newField.replace( 'your(pl)', "your_all's" ) if 'your(pl)' in newField else newField.replace( 'your', "your_all's" )
                    newField = newField.replace( 'your', "your(pl)" )
                elif 'your(pl)' not in newField:
                    # newField = newField.replace( 'you(pl)', 'you(pl)' ) if 'you(pl)' in newField else newField.replace( 'you', 'you(pl)' )
                    newField = newField.replace( 'you', 'you(pl)' )
                if morphology[0]=='V' and 'you(pl)' not in newField and '(pl)' not in newField:
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

            # assert newField != originalField, f"{originalField=}" # Not true when we use 'you(pl)'
            if newField != originalField:
                WLC_row_dict[fieldname] = newField
                num_fields_changed += 1
                row_changed = True
        # dPrint( 'Info', DEBUGGING_THIS_MODULE, f"{changed} {WLC_row_dict=}")
        if row_changed: num_rows_changed += 1

    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  do_yalls() changed {num_fields_changed:,} fields in {num_rows_changed:,} table rows ({num_plurals:,} plurals and {num_duals:,} duals)." )
    # assert num_fields_changed > 4_700 # otherwise something stopped working (for 'you_all')
    assert num_fields_changed > 4_200 # otherwise something stopped working (for 'you(pl)')
    # assert num_rows_changed > 4_100 # otherwise something stopped working (for 'you_all')
    assert num_rows_changed > 4_000 # otherwise something stopped working (for 'you(pl)')
    # assert num_plurals > 4_700 # otherwise something stopped working (for 'you_all')
    assert num_plurals > 4_200 # otherwise something stopped working (for 'you(pl)')
    # assert num_duals > 0 # otherwise something stopped working -- TODO: maybe there aren't any???
    return num_fields_changed > 0
# end of apply_Clear_Macula_OT_glosses.do_yalls


def do_yahs() -> bool:
    """
    Go through all our OT glosses and change 'Yahweh' to 'yah' where appropriate
    """
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, "\nFixing Hebrew 'yah's…" )

    num_rows_changed = 0
    for WLC_row_dict in state.WLC_morpheme_rows:
        if WLC_row_dict['NoCantillations'] == 'יָהּ':
            dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"    {WLC_row_dict['Ref']} {WLC_row_dict['RowType']} MG='{WLC_row_dict['MorphemeGloss']}' CMG='{WLC_row_dict['ContextualMorphemeGloss']}' WG='{WLC_row_dict['WordGloss']}' CWG='{WLC_row_dict['ContextualWordGloss']}'" )
            assert WLC_row_dict['MorphemeGloss'] in ('','LORD')
            assert not WLC_row_dict['ContextualMorphemeGloss']
            assert WLC_row_dict['WordGloss'] in ('Yah','')
            if WLC_row_dict['RowType'] in ('m','M'):
                WLC_row_dict['MorphemeGloss'] = WLC_row_dict['ContextualMorphemeGloss'] = 'Yah'
            else:
                assert not WLC_row_dict['MorphemeGloss'] and not WLC_row_dict['ContextualMorphemeGloss']
            WLC_row_dict['WordGloss'] = 'Yah'
            WLC_row_dict['ContextualWordGloss'] = 'Yah' if not WLC_row_dict['ContextualWordGloss'] else WLC_row_dict['ContextualWordGloss'].replace( 'Yahweh', 'Yah' )
            assert WLC_row_dict['ContextualWordGloss'] == 'Yah' or ('Yah' in WLC_row_dict['ContextualWordGloss'] and not 'Yahweh' in WLC_row_dict['ContextualWordGloss'])
            dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"              MG='{WLC_row_dict['MorphemeGloss']}' CMG='{WLC_row_dict['ContextualMorphemeGloss']}' WG='{WLC_row_dict['WordGloss']}' CWG='{WLC_row_dict['ContextualWordGloss']}'" )
            num_rows_changed += 1

    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  do_yahs() changed four fields in {num_rows_changed:,} table rows." )
    assert num_rows_changed > 40 # otherwise something stopped working
    return num_rows_changed > 0
# end of apply_Clear_Macula_OT_glosses.do_yahs


def do_auto_reordering() -> bool:
    """
    Reordering OT glosses to try to put subjects before their verbs, etc.
    Does this by changing the GlossOrder fields in state.WLC_rows
        but referring to information from state.MaculaHebrewRows.
    """
    DEBUGGING_THIS_MODULE = 99
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, "\nTrying to reorder WLC OT glosses…" )

    # First make a dictionary to easily get to our MaculaHebrew rows
    MaculaHebrew_morpheme_row_dict = {row['OSHBid']:n for n,row in enumerate(state.MaculaHebrew_morpheme_rows) if row['OSHBid']}
    dPrint('Quiet', DEBUGGING_THIS_MODULE, f"  {len(MaculaHebrew_morpheme_row_dict):,} entries in MaculaHebrew dict")

    reorder_vn_count = reorder_von_count = reorder_vnn_count = reorder_vdn_count = 0
    last4_WLC_morpheme_row = state.WLC_morpheme_rows[0] # in
    last3_WLC_morpheme_row = state.WLC_morpheme_rows[1] # beginning
    last2_WLC_morpheme_row = state.WLC_morpheme_rows[2] # he_created
    last1_WLC_morpheme_row = state.WLC_morpheme_rows[3] # Elohim
    # Manually put subject Elohim before he_created before we start the loop from the next morpheme
    last2_WLC_morpheme_row['GlossOrder'], last1_WLC_morpheme_row['GlossOrder'] = last1_WLC_morpheme_row['GlossOrder'], last2_WLC_morpheme_row['GlossOrder']
    print( f"{last4_WLC_morpheme_row=}\n{last3_WLC_morpheme_row=}\n{last2_WLC_morpheme_row=}\n{last1_WLC_morpheme_row=}" )

    for this__WLC_morpheme_row in state.WLC_morpheme_rows[4:]: # these 'rows' are dictionaries
        print( f"\n{this__WLC_morpheme_row=}" )
        # if WLC_morpheme_row['Ref'].startswith( 'GEN_30:1w1'):
        #     print( "Stopping there" ); break
        
        if this__WLC_morpheme_row['OSHBid']:
            try: MH_index = MaculaHebrew_morpheme_row_dict[this__WLC_morpheme_row['OSHBid']]
            except KeyError:
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  Skipped MaculaHebrew row without OSHBid: {this__WLC_morpheme_row['Ref']} {this__WLC_morpheme_row['OSHBid']}")
                last4_WLC_morpheme_row = last3_WLC_morpheme_row
                last3_WLC_morpheme_row = last2_WLC_morpheme_row
                last2_WLC_morpheme_row = last1_WLC_morpheme_row
                last1_WLC_morpheme_row = this__WLC_morpheme_row
                continue
        else:
            dPrint( 'Never', DEBUGGING_THIS_MODULE, f"  Skipped WLC row without OSHBid: {this__WLC_morpheme_row['Ref']}")
            assert this__WLC_morpheme_row['RowType']=='seg' or 'note' in this__WLC_morpheme_row['RowType']
            last4_WLC_morpheme_row = last3_WLC_morpheme_row
            last3_WLC_morpheme_row = last2_WLC_morpheme_row
            last2_WLC_morpheme_row = last1_WLC_morpheme_row
            last1_WLC_morpheme_row = this__WLC_morpheme_row
            continue

        last4_MaculaHebrew_morpheme_row = state.MaculaHebrew_morpheme_rows[MH_index-4]
        last3_MaculaHebrew_morpheme_row = state.MaculaHebrew_morpheme_rows[MH_index-3]
        last2_MaculaHebrew_morpheme_row = state.MaculaHebrew_morpheme_rows[MH_index-2]
        last1_MaculaHebrew_morpheme_row = state.MaculaHebrew_morpheme_rows[MH_index-1]
        MaculaHebrew_morpheme_row = state.MaculaHebrew_morpheme_rows[MH_index]

        dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"    lastMH4 {last4_MaculaHebrew_morpheme_row['FGRef']}\t{last4_MaculaHebrew_morpheme_row['RowType']}  {last4_MaculaHebrew_morpheme_row['EnglishGloss']}\twC={last4_MaculaHebrew_morpheme_row['WordClass']}\tPoS={last4_MaculaHebrew_morpheme_row['PartOfSpeech']}\twT={last4_MaculaHebrew_morpheme_row['WordType']}\t{last4_MaculaHebrew_morpheme_row['Nesting']}" )
        dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"    lastMH3 {last3_MaculaHebrew_morpheme_row['FGRef']}\t{last3_MaculaHebrew_morpheme_row['RowType']}  {last3_MaculaHebrew_morpheme_row['EnglishGloss']}\twC={last3_MaculaHebrew_morpheme_row['WordClass']}\tPoS={last3_MaculaHebrew_morpheme_row['PartOfSpeech']}\twT={last3_MaculaHebrew_morpheme_row['WordType']}\t{last3_MaculaHebrew_morpheme_row['Nesting']}" )
        dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"    lastMH2 {last2_MaculaHebrew_morpheme_row['FGRef']}\t{last2_MaculaHebrew_morpheme_row['RowType']}  {last2_MaculaHebrew_morpheme_row['EnglishGloss']}\twC={last2_MaculaHebrew_morpheme_row['WordClass']}\tPoS={last2_MaculaHebrew_morpheme_row['PartOfSpeech']}\twT={last2_MaculaHebrew_morpheme_row['WordType']}\t{last2_MaculaHebrew_morpheme_row['Nesting']}" )
        dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"    lastMH1 {last1_MaculaHebrew_morpheme_row['FGRef']}\t{last1_MaculaHebrew_morpheme_row['RowType']}  {last1_MaculaHebrew_morpheme_row['EnglishGloss']}\twC={last1_MaculaHebrew_morpheme_row['WordClass']}\tPoS={last1_MaculaHebrew_morpheme_row['PartOfSpeech']}\twT={last1_MaculaHebrew_morpheme_row['WordType']}\t{last1_MaculaHebrew_morpheme_row['Nesting']}" )
        dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"    M_H_Row {MaculaHebrew_morpheme_row['FGRef']}\t{MaculaHebrew_morpheme_row['RowType']}  {MaculaHebrew_morpheme_row['EnglishGloss']}\twC={MaculaHebrew_morpheme_row['WordClass']}\tPoS={MaculaHebrew_morpheme_row['PartOfSpeech']}\twT={MaculaHebrew_morpheme_row['WordType']}\t{MaculaHebrew_morpheme_row['Nesting']}" )

        if MaculaHebrew_morpheme_row['PartOfSpeech']=='n' and MaculaHebrew_morpheme_row['Nesting'].split('/')[-1]=='N2NP': # Subject is single noun
            dPrint( 'Info', DEBUGGING_THIS_MODULE, f"\n  Have a simple noun subject: {MaculaHebrew_morpheme_row['FGRef']} {MaculaHebrew_morpheme_row['RowType']} '{MaculaHebrew_morpheme_row['WordClass']}' {MaculaHebrew_morpheme_row['PartOfSpeech']} '{MaculaHebrew_morpheme_row['EnglishGloss']}'" )

            # Look for verb followed by subject
            if ( '/' in last1_MaculaHebrew_morpheme_row['Nesting'] and 'V-S' in last1_MaculaHebrew_morpheme_row['Nesting'].split('/')[0] 
            and last1_MaculaHebrew_morpheme_row['PartOfSpeech']=='v'
            and last1_MaculaHebrew_morpheme_row['Nesting'].split('/')[-1] == 'V2VP' ): # Verb is a single word
                # Possibly have a verb followed by its subject (first one is Gen 1:3 'and=he_said Elohim')
                if last1_MaculaHebrew_morpheme_row['EnglishGloss'] in ('be','was','there_was'):
                    continue # skip these
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"      {last1_MaculaHebrew_morpheme_row['FGRef']}\t{last1_MaculaHebrew_morpheme_row['RowType']}\t{last1_MaculaHebrew_morpheme_row['EnglishGloss']}\t{last1_MaculaHebrew_morpheme_row['WordClass']}\t{last1_MaculaHebrew_morpheme_row['PartOfSpeech']}\t{last1_MaculaHebrew_morpheme_row['Nesting']}" )
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"      {MaculaHebrew_morpheme_row['FGRef']}\t{MaculaHebrew_morpheme_row['RowType']}\t{MaculaHebrew_morpheme_row['EnglishGloss']}\t{MaculaHebrew_morpheme_row['WordClass']}\t{MaculaHebrew_morpheme_row['PartOfSpeech']}\t{MaculaHebrew_morpheme_row['Nesting']}" )
                # dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  {last1_WLC_morpheme_row['Ref']}\t{last1_WLC_morpheme_row['GlossOrder']}")
                # dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  {WLC_morpheme_row['Ref']}\t{WLC_morpheme_row['GlossOrder']}")
                if int(last1_WLC_morpheme_row['GlossOrder']) < int(this__WLC_morpheme_row['GlossOrder']):
                    print( f"{last2_WLC_morpheme_row=}\n{last1_WLC_morpheme_row=}\n{this__WLC_morpheme_row=}" )
                    if 'w' in last1_WLC_morpheme_row['RowType']: # a word -- can be 'w', 'wK', 'Aw'
                        dPrint( 'Info', DEBUGGING_THIS_MODULE, f"    Let's swap the v-s order for this word {this__WLC_morpheme_row['Ref'].split('w')[0]} '{last1_WLC_morpheme_row['WordGloss']}' '{this__WLC_morpheme_row['WordGloss']}'")
                        last1_WLC_morpheme_row['GlossOrder'], this__WLC_morpheme_row['GlossOrder'] = this__WLC_morpheme_row['GlossOrder'], last1_WLC_morpheme_row['GlossOrder']
                        reorder_vn_count += 1
                    elif 'M' in last1_WLC_morpheme_row['RowType'] and 'm' in last2_WLC_morpheme_row['RowType'] and 'm' not in last3_WLC_morpheme_row['RowType']: # a final morpheme preceded by another morpheme
                        # it's more complicated because it has to go into the middle of two morphemes so we have to use GlossInsert
                        dPrint( 'Info', DEBUGGING_THIS_MODULE, f"    Let's swap the v-s order for these two morphemes {this__WLC_morpheme_row['Ref'].split('w')[0]} '{last2_WLC_morpheme_row['WordGloss']}' '{last1_WLC_morpheme_row['WordGloss']}' '{this__WLC_morpheme_row['WordGloss']}'")
                        last2_WLC_morpheme_row['GlossOrder'], last1_WLC_morpheme_row['GlossOrder'], this__WLC_morpheme_row['GlossOrder'] = last1_WLC_morpheme_row['GlossOrder'], this__WLC_morpheme_row['GlossOrder'], last2_WLC_morpheme_row['GlossOrder']
                        this__WLC_morpheme_row['GlossInsert'] = '_'
                        reorder_vn_count += 1
                    elif 'M' in last1_WLC_morpheme_row['RowType'] and 'm' in last2_WLC_morpheme_row['RowType'] and 'm' in last3_WLC_morpheme_row['RowType'] and 'm' not in last4_WLC_morpheme_row['RowType']: # a final morpheme preceded by another two morphemes
                        # it's more complicated because it has to go into the middle of three morphemes so we have to use GlossInsert
                        dPrint( 'Info', DEBUGGING_THIS_MODULE, f"    Let's swap the v-s order for these three morphemes {this__WLC_morpheme_row['Ref'].split('w')[0]} '{last3_WLC_morpheme_row['WordGloss']}' '{last2_WLC_morpheme_row['WordGloss']}' '{last1_WLC_morpheme_row['WordGloss']}' '{this__WLC_morpheme_row['WordGloss']}'")
                        last3_WLC_morpheme_row['GlossOrder'], last2_WLC_morpheme_row['GlossOrder'], last1_WLC_morpheme_row['GlossOrder'], this__WLC_morpheme_row['GlossOrder'] = last2_WLC_morpheme_row['GlossOrder'], last1_WLC_morpheme_row['GlossOrder'], this__WLC_morpheme_row['GlossOrder'], last3_WLC_morpheme_row['GlossOrder']
                        this__WLC_morpheme_row['GlossInsert'] = '_'
                        reorder_vn_count += 1 # Num 5:22, Josh 8:2, 2Ch 12:7
                    else:
                        dPrint( 'Info', DEBUGGING_THIS_MODULE, f"{last2_WLC_morpheme_row['Ref']} rT={last2_WLC_morpheme_row['RowType']} wOrM={last2_WLC_morpheme_row['WordOrMorpheme']} mG={last2_WLC_morpheme_row['MorphemeGloss']}")
                        dPrint( 'Info', DEBUGGING_THIS_MODULE, f"{last1_WLC_morpheme_row['Ref']} rT={last1_WLC_morpheme_row['RowType']} wOrM={last1_WLC_morpheme_row['WordOrMorpheme']} mG={last1_WLC_morpheme_row['MorphemeGloss']}")
                        dPrint( 'Info', DEBUGGING_THIS_MODULE, f"{this__WLC_morpheme_row['Ref']} rT={this__WLC_morpheme_row['RowType']} wOrM={this__WLC_morpheme_row['WordOrMorpheme']} mG={this__WLC_morpheme_row['MorphemeGloss']}")
                        print( "Seems we can't put subject before verb!!!" )
                        # halt # Jer 6:29
                    if this__WLC_morpheme_row['Ref'].startswith( 'JOS_8:2w' ): halt

            # Look for verb followed by DOM and direct object then subject
            if ( last2_MaculaHebrew_morpheme_row['WordClass']=='om' and last2_MaculaHebrew_morpheme_row['PartOfSpeech']=='part'
                and '/' in last2_MaculaHebrew_morpheme_row['Nesting'] and 'V-O-S' in last2_MaculaHebrew_morpheme_row['Nesting'].split('/')[0]
            and last3_MaculaHebrew_morpheme_row['Nesting'].split('/')[-1] == 'V2VP' ): # Verb is a single word
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"      {last3_MaculaHebrew_morpheme_row['FGRef']}\t{last3_MaculaHebrew_morpheme_row['RowType']}\t{last3_MaculaHebrew_morpheme_row['EnglishGloss']}\t{last3_MaculaHebrew_morpheme_row['WordClass']}\t{last3_MaculaHebrew_morpheme_row['PartOfSpeech']}\t{last3_MaculaHebrew_morpheme_row['Nesting']}" )
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"      {last2_MaculaHebrew_morpheme_row['FGRef']}\t{last2_MaculaHebrew_morpheme_row['RowType']}\t{last2_MaculaHebrew_morpheme_row['EnglishGloss']}\t{last2_MaculaHebrew_morpheme_row['WordClass']}\t{last2_MaculaHebrew_morpheme_row['PartOfSpeech']}\t{last2_MaculaHebrew_morpheme_row['Nesting']}" )
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"      {last1_MaculaHebrew_morpheme_row['FGRef']}\t{last1_MaculaHebrew_morpheme_row['RowType']}\t{last1_MaculaHebrew_morpheme_row['EnglishGloss']}\t{last1_MaculaHebrew_morpheme_row['WordClass']}\t{last1_MaculaHebrew_morpheme_row['PartOfSpeech']}\t{last1_MaculaHebrew_morpheme_row['Nesting']}" )
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"      {MaculaHebrew_morpheme_row['FGRef']}\t{MaculaHebrew_morpheme_row['RowType']}\t{MaculaHebrew_morpheme_row['EnglishGloss']}\t{MaculaHebrew_morpheme_row['WordClass']}\t{MaculaHebrew_morpheme_row['PartOfSpeech']}\t{MaculaHebrew_morpheme_row['Nesting']}" )
                if int(last3_WLC_morpheme_row['GlossOrder']) < int(last2_WLC_morpheme_row['GlossOrder']) < int(last1_WLC_morpheme_row['GlossOrder']) < int(this__WLC_morpheme_row['GlossOrder']):
                    dPrint( 'Info', DEBUGGING_THIS_MODULE, f"    Let's swap the v-o-s order for {this__WLC_morpheme_row['Ref'].split('w')[0]} '{last3_WLC_morpheme_row['WordGloss']}' '{this__WLC_morpheme_row['WordGloss']}'")
                    last3_WLC_morpheme_row['GlossOrder'], last2_WLC_morpheme_row['GlossOrder'], last1_WLC_morpheme_row['GlossOrder'], this__WLC_morpheme_row['GlossOrder'] = \
                        last2_WLC_morpheme_row['GlossOrder'], last1_WLC_morpheme_row['GlossOrder'], this__WLC_morpheme_row['GlossOrder'], last3_WLC_morpheme_row['GlossOrder']
                    reorder_von_count += 1
                    if this__WLC_morpheme_row['Ref'].startswith( 'JOS_8:2w' ): halt

        elif ( MaculaHebrew_morpheme_row['PartOfSpeech']=='n' and MaculaHebrew_morpheme_row['Nesting'].split('/')[-1] in ('N2NP','DetNP')
        and last1_MaculaHebrew_morpheme_row['WordClass']=='art' and 'DetNP' in last1_MaculaHebrew_morpheme_row['Nesting'] # Subject is determiner noun phrase
        and 'DetNP' not in state.MaculaHebrew_morpheme_rows[MH_index+1]['Nesting'] ): # But not a triple one
            everywhere
            dPrint( 'Info', DEBUGGING_THIS_MODULE, f"\n  Have a determiner noun subject: {MaculaHebrew_morpheme_row['FGRef']} {MaculaHebrew_morpheme_row['RowType']} '{MaculaHebrew_morpheme_row['WordClass']}' {MaculaHebrew_morpheme_row['PartOfSpeech']} '{last1_MaculaHebrew_morpheme_row['EnglishGloss']} {MaculaHebrew_morpheme_row['EnglishGloss']}'" )

            # Look for verb followed by subject
            if ( '/' in last2_MaculaHebrew_morpheme_row['Nesting'] and 'V-S' in last2_MaculaHebrew_morpheme_row['Nesting'].split('/')[0] 
            and last2_MaculaHebrew_morpheme_row['PartOfSpeech']=='v'
            and last2_MaculaHebrew_morpheme_row['Nesting'].split('/')[-1] == 'V2VP' ): # Verb is a single word
                again
                # Possibly have a verb followed by its subject
                # if last2_MaculaHebrew_row['EnglishGloss'] in ('be','was','there_was'):
                #     continue # skip these
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"      {last2_MaculaHebrew_morpheme_row['FGRef']}\t{last2_MaculaHebrew_morpheme_row['RowType']}\t{last2_MaculaHebrew_morpheme_row['EnglishGloss']}\t{last2_MaculaHebrew_morpheme_row['WordClass']}\t{last2_MaculaHebrew_morpheme_row['PartOfSpeech']}\t{last2_MaculaHebrew_morpheme_row['Nesting']}" )
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"      {last1_MaculaHebrew_morpheme_row['FGRef']}\t{last1_MaculaHebrew_morpheme_row['RowType']}\t{last1_MaculaHebrew_morpheme_row['EnglishGloss']}\t{last1_MaculaHebrew_morpheme_row['WordClass']}\t{last1_MaculaHebrew_morpheme_row['PartOfSpeech']}\t{last1_MaculaHebrew_morpheme_row['Nesting']}" )
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"      {MaculaHebrew_morpheme_row['FGRef']}\t{MaculaHebrew_morpheme_row['RowType']}\t{MaculaHebrew_morpheme_row['EnglishGloss']}\t{MaculaHebrew_morpheme_row['WordClass']}\t{MaculaHebrew_morpheme_row['PartOfSpeech']}\t{MaculaHebrew_morpheme_row['Nesting']}" )
                if int(last2_WLC_morpheme_row['GlossOrder']) < int(last1_WLC_morpheme_row['GlossOrder']) < int(this__WLC_morpheme_row['GlossOrder']):
                    dPrint( 'Info', DEBUGGING_THIS_MODULE, f"    Let's swap the v-s order for {this__WLC_morpheme_row['Ref'].split('w')[0]} '{last2_WLC_morpheme_row['WordGloss']} {last1_WLC_morpheme_row['WordGloss']}' '{this__WLC_morpheme_row['WordGloss']}'")
                    last2_WLC_morpheme_row['GlossOrder'], last1_WLC_morpheme_row['GlossOrder'], this__WLC_morpheme_row['GlossOrder'] = this__WLC_morpheme_row['GlossOrder'], last2_WLC_morpheme_row['GlossOrder'], last1_WLC_morpheme_row['GlossOrder']
                    reorder_vdn_count += 1

            # # Look for verb followed by DOM and direct object then subject
            # if ( last2_MaculaHebrew_row['WordClass']=='om' and last2_MaculaHebrew_row['PartOfSpeech']=='part'
            #     and '/' in last2_MaculaHebrew_row['Nesting'] and 'v-o-s' in last2_MaculaHebrew_row['Nesting'].split('/')[-2]
            # and last3_MaculaHebrew_row['Nesting'].split('/')[-1] == 'v=v2vp' ): # Verb is a single word
            #     dPrint( 'Info', DEBUGGING_THIS_MODULE, f"      {last3_MaculaHebrew_row['FGRef']}\t{last3_MaculaHebrew_row['RowType']}\t{last3_MaculaHebrew_row['EnglishGloss']}\t{last3_MaculaHebrew_row['WordClass']}\t{last3_MaculaHebrew_row['PartOfSpeech']}\t{last3_MaculaHebrew_row['Nesting']}" )
            #     dPrint( 'Info', DEBUGGING_THIS_MODULE, f"      {last2_MaculaHebrew_row['FGRef']}\t{last2_MaculaHebrew_row['RowType']}\t{last2_MaculaHebrew_row['EnglishGloss']}\t{last2_MaculaHebrew_row['WordClass']}\t{last2_MaculaHebrew_row['PartOfSpeech']}\t{last2_MaculaHebrew_row['Nesting']}" )
            #     dPrint( 'Info', DEBUGGING_THIS_MODULE, f"      {last1_MaculaHebrew_row['FGRef']}\t{last1_MaculaHebrew_row['RowType']}\t{last1_MaculaHebrew_row['EnglishGloss']}\t{last1_MaculaHebrew_row['WordClass']}\t{last1_MaculaHebrew_row['PartOfSpeech']}\t{last1_MaculaHebrew_row['Nesting']}" )
            #     dPrint( 'Info', DEBUGGING_THIS_MODULE, f"      {MaculaHebrew_row['FGRef']}\t{MaculaHebrew_row['RowType']}\t{MaculaHebrew_row['EnglishGloss']}\t{MaculaHebrew_row['WordClass']}\t{MaculaHebrew_row['PartOfSpeech']}\t{MaculaHebrew_row['Nesting']}" )
            #     if int(last3_WLC_row['GlossOrder']) < int(WLC_morpheme_row['GlossOrder']):
            #         dPrint( 'Info', DEBUGGING_THIS_MODULE, f"    Let's swap the v-o-s order for {WLC_morpheme_row['Ref'].split('w')[0]} '{last3_WLC_row['WordGloss']}' '{WLC_morpheme_row['WordGloss']}'")
            #         last3_WLC_row['GlossOrder'], last2_WLC_row['GlossOrder'], last1_WLC_row['GlossOrder'], WLC_morpheme_row['GlossOrder'] = \
            #             last2_WLC_row['GlossOrder'], last1_WLC_row['GlossOrder'], WLC_morpheme_row['GlossOrder'], last3_WLC_row['GlossOrder']
            #         reorder_count += 1

        elif ( MaculaHebrew_morpheme_row['PartOfSpeech']=='n' and 'Np-Appos' in MaculaHebrew_morpheme_row['Nesting']
        and last1_MaculaHebrew_morpheme_row['PartOfSpeech']=='n' and 'Np-Appos' in last1_MaculaHebrew_morpheme_row['Nesting'] # Subject is double noun
        and 'Np-Appos' not in state.MaculaHebrew_morpheme_rows[MH_index+1]['Nesting'] ): # But not a triple one
            dPrint( 'Info', DEBUGGING_THIS_MODULE, f"\n  Have a double noun subject: {MaculaHebrew_morpheme_row['FGRef']} {MaculaHebrew_morpheme_row['RowType']} '{MaculaHebrew_morpheme_row['WordClass']}' {MaculaHebrew_morpheme_row['PartOfSpeech']} '{last1_MaculaHebrew_morpheme_row['EnglishGloss']} {MaculaHebrew_morpheme_row['EnglishGloss']}'" )

            # Look for verb followed by subject
            if ( '/' in last2_MaculaHebrew_morpheme_row['Nesting'] and 'V-S' in last2_MaculaHebrew_morpheme_row['Nesting'].split('/')[0] 
            and last2_MaculaHebrew_morpheme_row['PartOfSpeech']=='v'
            and last2_MaculaHebrew_morpheme_row['Nesting'].split('/')[-1] == 'V2VP' ): # Verb is a single word
                # Possibly have a verb followed by its subject
                doubleN_VS
                if last2_MaculaHebrew_morpheme_row['EnglishGloss'] in ('be','was','there_was'):
                    continue # skip these
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"      {last2_MaculaHebrew_morpheme_row['FGRef']}\t{last2_MaculaHebrew_morpheme_row['RowType']}\t{last2_MaculaHebrew_morpheme_row['EnglishGloss']}\t{last2_MaculaHebrew_morpheme_row['WordClass']}\t{last2_MaculaHebrew_morpheme_row['PartOfSpeech']}\t{last2_MaculaHebrew_morpheme_row['Nesting']}" )
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"      {last1_MaculaHebrew_morpheme_row['FGRef']}\t{last1_MaculaHebrew_morpheme_row['RowType']}\t{last1_MaculaHebrew_morpheme_row['EnglishGloss']}\t{last1_MaculaHebrew_morpheme_row['WordClass']}\t{last1_MaculaHebrew_morpheme_row['PartOfSpeech']}\t{last1_MaculaHebrew_morpheme_row['Nesting']}" )
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"      {MaculaHebrew_morpheme_row['FGRef']}\t{MaculaHebrew_morpheme_row['RowType']}\t{MaculaHebrew_morpheme_row['EnglishGloss']}\t{MaculaHebrew_morpheme_row['WordClass']}\t{MaculaHebrew_morpheme_row['PartOfSpeech']}\t{MaculaHebrew_morpheme_row['Nesting']}" )
                if int(last2_WLC_morpheme_row['GlossOrder']) < int(last1_WLC_morpheme_row['GlossOrder']) < int(this__WLC_morpheme_row['GlossOrder']):
                    dPrint( 'Info', DEBUGGING_THIS_MODULE, f"    Let's swap the v-s order for {this__WLC_morpheme_row['Ref'].split('w')[0]} '{last2_WLC_morpheme_row['WordGloss']} {last1_WLC_morpheme_row['WordGloss']}' '{this__WLC_morpheme_row['WordGloss']}'")
                    last2_WLC_morpheme_row['GlossOrder'], last1_WLC_morpheme_row['GlossOrder'], this__WLC_morpheme_row['GlossOrder'] = this__WLC_morpheme_row['GlossOrder'], last2_WLC_morpheme_row['GlossOrder'], last1_WLC_morpheme_row['GlossOrder']
                    reorder_vnn_count += 1

            # # Look for verb followed by DOM and direct object then subject
            # if ( last2_MaculaHebrew_row['WordClass']=='om' and last2_MaculaHebrew_row['PartOfSpeech']=='part'
            #     and '/' in last2_MaculaHebrew_row['Nesting'] and 'v-o-s' in last2_MaculaHebrew_row['Nesting'].split('/')[-2]
            # and last3_MaculaHebrew_row['Nesting'].split('/')[-1] == 'v=v2vp' ): # Verb is a single word
            #     dPrint( 'Info', DEBUGGING_THIS_MODULE, f"      {last3_MaculaHebrew_row['FGRef']}\t{last3_MaculaHebrew_row['RowType']}\t{last3_MaculaHebrew_row['EnglishGloss']}\t{last3_MaculaHebrew_row['WordClass']}\t{last3_MaculaHebrew_row['PartOfSpeech']}\t{last3_MaculaHebrew_row['Nesting']}" )
            #     dPrint( 'Info', DEBUGGING_THIS_MODULE, f"      {last2_MaculaHebrew_row['FGRef']}\t{last2_MaculaHebrew_row['RowType']}\t{last2_MaculaHebrew_row['EnglishGloss']}\t{last2_MaculaHebrew_row['WordClass']}\t{last2_MaculaHebrew_row['PartOfSpeech']}\t{last2_MaculaHebrew_row['Nesting']}" )
            #     dPrint( 'Info', DEBUGGING_THIS_MODULE, f"      {last1_MaculaHebrew_row['FGRef']}\t{last1_MaculaHebrew_row['RowType']}\t{last1_MaculaHebrew_row['EnglishGloss']}\t{last1_MaculaHebrew_row['WordClass']}\t{last1_MaculaHebrew_row['PartOfSpeech']}\t{last1_MaculaHebrew_row['Nesting']}" )
            #     dPrint( 'Info', DEBUGGING_THIS_MODULE, f"      {MaculaHebrew_row['FGRef']}\t{MaculaHebrew_row['RowType']}\t{MaculaHebrew_row['EnglishGloss']}\t{MaculaHebrew_row['WordClass']}\t{MaculaHebrew_row['PartOfSpeech']}\t{MaculaHebrew_row['Nesting']}" )
            #     if int(last3_WLC_row['GlossOrder']) < int(WLC_morpheme_row['GlossOrder']):
            #         dPrint( 'Info', DEBUGGING_THIS_MODULE, f"    Let's swap the v-o-s order for {WLC_morpheme_row['Ref'].split('w')[0]} '{last3_WLC_row['WordGloss']}' '{WLC_morpheme_row['WordGloss']}'")
            #         last3_WLC_row['GlossOrder'], last2_WLC_row['GlossOrder'], last1_WLC_row['GlossOrder'], WLC_morpheme_row['GlossOrder'] = \
            #             last2_WLC_row['GlossOrder'], last1_WLC_row['GlossOrder'], WLC_morpheme_row['GlossOrder'], last3_WLC_row['GlossOrder']
            #         reorder_count += 1

        # Processing at end of each loop
        last4_WLC_morpheme_row = last3_WLC_morpheme_row
        last3_WLC_morpheme_row = last2_WLC_morpheme_row
        last2_WLC_morpheme_row = last1_WLC_morpheme_row
        last1_WLC_morpheme_row = this__WLC_morpheme_row

    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"    Reordered {reorder_vn_count:,} single-noun v-s pairs." )
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"    Reordered {reorder_vdn_count:,} determiner-noun v-s sets." )
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"    Reordered {reorder_von_count:,} single-noun v-o-s pairs." )
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"    Reordered {reorder_vnn_count:,} double-noun v-s sets." )
    assert reorder_vn_count > 7_000 # Otherwise something has gone wrong
    # assert reorder_vdn_count > 0 # Otherwise something isn't working
    assert reorder_von_count > 60 # Otherwise something has gone wrong
    # assert reorder_vnn_count > 0 # Otherwise something isn't working
    total_count = reorder_vn_count + reorder_von_count + reorder_vnn_count + reorder_vdn_count
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  Reordered {total_count:,} total sets." )

    return True
# end of apply_Clear_Macula_OT_glosses.do_auto_reordering


def save_filled_morpheme_TSV_file() -> bool:
    """
    Save the filled TSV table with a row for each morpheme
    This is written from state.WLC_rows.

    We do some final fixes
    """
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"\nExporting filled WLC morpheme table as a single flat TSV file to {state.our_morpheme_TSV_output_filepath}…" )

    BibleOrgSysGlobals.backupAnyExistingFile( state.our_morpheme_TSV_output_filepath, numBackups=5 )

    with open( state.our_morpheme_TSV_output_filepath, 'wt', encoding='utf-8' ) as tsv_output_file:
        tsv_output_file.write('\ufeff') # Write BOM
        writer = DictWriter( tsv_output_file, fieldnames=WLC_tsv_column_headers, delimiter='\t' )
        writer.writeheader()
        for n,row_dict in enumerate( state.WLC_morpheme_rows, start=1 ):
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
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  {len(state.WLC_morpheme_rows):,} morpheme data rows written." )

    return True
# end of apply_Clear_Macula_OT_glosses.save_filled_morpheme_TSV_file


def save_lemma_TSV_file() -> bool:
    """
    Save a row for each lemma with its glosses
    This is written from state.MaculaHebrewRows.

    TODO: Why is the same code in convert_ClearMaculaOT_to_our_TSV.py???
    """
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"\nCreating and exporting OT lemma table from Low Fat table as a single flat TSV file to {state.our_lemma_TSV_output_filepath}…" )


    # Firstly, let's create the lemma table
    state.lemma_formation_dict = defaultdict(set)
    num_missing_lemmas = 0
    morphemes_with_missing_lemmas = set()
    for thisRowDict in state.MaculaHebrew_morpheme_rows:
        # print( f"{thisRowDict=}" )
        fgRef, wordOrMorpheme, lemma, gloss = thisRowDict['FGRef'], thisRowDict['WordOrMorpheme'], thisRowDict['Lemma'], thisRowDict['EnglishGloss']
        # assert ',' not in gloss, thisRow # Check our separator's not in the data -- fails on "1,000"
        assert ';' not in gloss
        if lemma:
            for char in lemma:
                # print( f"{ord(char)=} {unicodedata.name(char)=} {char=} {unicodedata.category(char)=} {unicodedata.bidirectional(char)=} {unicodedata.combining(char)=} {unicodedata.mirrored(char)=}" )
                assert 'ACCENT' not in unicodedata.name(char), f"{unicodedata.name(char)=} {fgRef} {wordOrMorpheme=} {lemma=} {gloss=}"
            if gloss:
                # assert lemma not in state.lemma_formation_dict, f"DUPLICATE {lemma=}" # Maybe not correct: we're just collecting all possible glosses for that lemma???
                state.lemma_formation_dict[lemma].add( gloss )
        else: # no lemma
            if fgRef.startswith( 'GEN_1:'):
                print( f"Why do we have no lemma for {fgRef} {wordOrMorpheme=}?" )
            morphemes_with_missing_lemmas.add( wordOrMorpheme )
            num_missing_lemmas += 1
    print( f"{num_missing_lemmas:,} morphemes with no lemmas => {len(morphemes_with_missing_lemmas):,} unique morphemes_with_missing_lemmas={sorted(morphemes_with_missing_lemmas)}")
    print( f"Extracted {len(state.lemma_formation_dict):,} Hebrew lemmas from {len(state.MaculaHebrew_morpheme_rows):,} morphemes" )
    # print( f"{state.lemma_formation_dict=}" )
    
    # Preprocess it in the sorted order
    new_dict = {}
    # state.lemma_index_dict = {}
    for n, hebrew_lemma in enumerate( sorted( state.lemma_formation_dict ), start=1 ):
        for char in hebrew_lemma:
            # print( f"{ord(char)=} {unicodedata.name(char)=} {char=} {unicodedata.category(char)=} {unicodedata.bidirectional(char)=} {unicodedata.combining(char)=} {unicodedata.mirrored(char)=}" )
            assert 'ACCENT' not in unicodedata.name(char), f"{unicodedata.name(char)=} {hebrew_lemma=} {state.lemma_formation_dict[hebrew_lemma]=}"
        assert hebrew_lemma not in new_dict, f"DUPLICATE {hebrew_lemma=}"
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
            for char in lemma:
                # print( f"{ord(char)=} {unicodedata.name(char)=} {char=} {unicodedata.category(char)=} {unicodedata.bidirectional(char)=} {unicodedata.combining(char)=} {unicodedata.mirrored(char)=}" )
                assert 'ACCENT' not in unicodedata.name(char), f"{unicodedata.name(char)=} {lemma=} {glosses=}"
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
    Save the TSV word table with a row for each word.
    This is written from state.WLC_rows.
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
    
    current_verse_ref = None
    verse_gloss_order_list = []
    with open( state.our_word_TSV_output_filepath, 'wt', encoding='utf-8' ) as tsv_output_file:
        tsv_output_file.write('\ufeff') # Write BOM
        writer = DictWriter( tsv_output_file, fieldnames=word_tsv_column_headers, delimiter='\t' )
        writer.writeheader()

        num_data_rows_written = 0
        morpheme_row_list, morpheme_strongs_list, morpheme_morphology_list, morpheme_list, morpheme_noCantillations_list, morpheme_glosses_list, contextual_morpheme_glosses_list = [], [], [], [], [], [], []
        morpheme_gloss_capitalisation = ''
        ref = OSHB_id = morpheme_cantillation_hierarchy = morpheme_gloss_order = None
        for n,original_column_dict in enumerate( state.WLC_morpheme_rows, start=1 ):
            # print( f"{n} {original_column_dict}" )
            if 'w' in original_column_dict['RowType']:
                for column_name in ('MorphemeGloss','ContextualMorphemeGloss','GlossPunctuation'):
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
                verse_ref = word_entry['Ref'].split('w')[0]
                if verse_ref != current_verse_ref:
                    verse_gloss_order_list = [word_entry['GlossOrder']]
                    current_verse_ref = verse_ref
                else:
                    assert word_entry['GlossOrder'] not in verse_gloss_order_list, f"Duplicate {word_entry['GlossOrder']=} in {word_entry=}"
                    verse_gloss_order_list.append( word_entry['GlossOrder'] )
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
                for column_name in ('WordGloss','ContextualWordGloss','GlossPunctuation'):
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
                verse_ref = word_entry['Ref'].split('w')[0]
                if verse_ref != current_verse_ref:
                    verse_gloss_order_list = [word_entry['GlossOrder']]
                    current_verse_ref = verse_ref
                else:
                    assert word_entry['GlossOrder'] not in verse_gloss_order_list, f"Duplicate {word_entry['GlossOrder']=} in {word_entry=}"
                    verse_gloss_order_list.append( word_entry['GlossOrder'] )
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
                verse_ref = word_entry['Ref'].split('w')[0]
                if verse_ref != current_verse_ref:
                    verse_gloss_order_list = [word_entry['GlossOrder']]
                    current_verse_ref = verse_ref
                else:
                    assert word_entry['GlossOrder'] not in verse_gloss_order_list, f"Duplicate {word_entry['GlossOrder']=} in {word_entry=}"
                    verse_gloss_order_list.append( word_entry['GlossOrder'] )
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
