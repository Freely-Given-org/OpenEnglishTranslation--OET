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
"""
from gettext import gettext as _
from typing import Dict, List, Tuple
from pathlib import Path
from csv import DictReader
from collections import defaultdict
from datetime import datetime

import BibleOrgSysGlobals
from BibleOrgSysGlobals import fnPrint, vPrint, dPrint


LAST_MODIFIED_DATE = '2022-09-26' # by RJH
SHORT_PROGRAM_NAME = "Prepare_OSHB_for_glossing"
PROGRAM_NAME = "Prepare OSHB for glossing"
PROGRAM_VERSION = '0.02'
PROGRAM_NAME_VERSION = f'{SHORT_PROGRAM_NAME} v{PROGRAM_VERSION}'

DEBUGGING_THIS_MODULE = True


OSHB_TSV_INPUT_FILEPATH = Path( '../sourceTexts/rawOSHB/OSHB.original.flat.morphemes.tsv' )
OUTPUT_FOLDERPATH = Path( '../translatedTexts/glossed_OSHB/' )


state = None
class State:
    def __init__( self ) -> None:
        """
        Constructor:
        """
        self.OSHB_TSV_input_filepath = OSHB_TSV_INPUT_FILEPATH
        self.outputFolderpath = OUTPUT_FOLDERPATH
    # end of prepare_OSHB_for_glossing.__init__


NEWLINE = '\n'
BACKSLASH = '\\'

NUM_EXPECTED_WLC_COLUMNS = 8
WLC_tsv_rows = []
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

    if loadWLCSourceTable():
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
        print("  Removing Byte Order Marker (BOM) from start of WLC tsv file…")
        tsv_lines[0] = tsv_lines[0][1:]

    # Get the headers before we start
    WLC_tsv_column_headers = [
        header for header in tsv_lines[0].strip().split('\t')
    ]  # assumes no commas in headings
    dPrint('Info', DEBUGGING_THIS_MODULE, f"Column headers: ({len(WLC_tsv_column_headers)}): {WLC_tsv_column_headers}")
    assert len(WLC_tsv_column_headers) == NUM_EXPECTED_WLC_COLUMNS

    # Read, check the number of columns, and summarise row contents all in one go
    dict_reader = DictReader(tsv_lines, delimiter='\t')
    unique_morphemes, unique_words = set(), set()
    note_count = seg_count = 0
    assembled_word = ''
    for n, row in enumerate(dict_reader):
        if len(row) != NUM_EXPECTED_WLC_COLUMNS:
            print(f"Line {n} has {len(row)} columns instead of {NUM_EXPECTED_WLC_COLUMNS}!!!")
        WLC_tsv_rows.append(row)
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
            unique_words.add(row['Morpheme'])
        elif row_type == 'm':
            unique_morphemes.add(row['Morpheme'])
            assembled_word = f"{assembled_word}{row['Morpheme']}"
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
    print(f"  Loaded {len(WLC_tsv_rows):,} WLC tsv data rows.")
    print(f"    Have {len(unique_words):,} unique Hebrew words.")
    print(f"    Have {len(unique_morphemes):,} unique Hebrew morphemes.")
    print(f"    Have {seg_count:,} Hebrew segment markers.")
    print(f"    Have {note_count:,} notes.")

    return True
# end of prepare_OSHB_for_glossing.loadWLCSourceTable


def save_expanded_TSV_file() -> bool:
    """
    """
    print("\nExporting expanded columns TSV file…")
    expanded_headers = ['Ref','OSHBid','Type','Strongs','n','Morphology','WordOrMorpheme','GenericGloss','ContextualGloss']
    for n, row in enumerate(WLC_tsv_rows):
        collation_id, verse_id = row['CollationID'], row['VerseID']
        assert len(collation_id) == 11 and collation_id.isdigit()
        if collation_id == '99999999999':
            this_verse_row_list = None
        else:
            assert len(verse_id) == 8 and verse_id.isdigit()
            if verse_id != last_verse_id:
                this_verse_row_list = get_verse_rows(WLC_tsv_rows, n)
                last_verse_id = verse_id

        book_number, chapter_number, verse_number, word_number \
            = int(collation_id[:2]), int(collation_id[2:5]), int(collation_id[5:8]), int(collation_id[8:])
        if book_number != last_book_number:  # we've started a new book
            if book_number != 99:
                assert book_number == last_book_number + 1
            if usfm_text:  # write out the book (including the last one)
                usfm_text = usfm_text.replace('¶', '¶ ') # Looks nicer maybe
                # Fix any punctuation problems
                usfm_text = usfm_text.replace(',,',',').replace('..','.').replace(';;',';') \
                            .replace(',.','.').replace('.”.”','.”').replace('?”?”','?”')
                assert '  ' not in usfm_text
                usfm_filepath = VLT_USFM_OUTPUT_FOLDERPATH.joinpath( f'{BOS_BOOK_ID_MAP[last_book_number]}_gloss.usfm' )
                with open(usfm_filepath, 'wt', encoding='utf-8') as output_file:
                    output_file.write(f"{usfm_text}\n")
            if book_number == 99:
                break  # all done!
            USFM_book_code = USFM_BOOK_ID_MAP[book_number]
            usfm_text = f"""\\id {USFM_book_code}
\\usfm 3.0
\\ide UTF-8
\\rem USFM file created {datetime.now().strftime('%Y-%m-%d %H:%M')} by {PROGRAM_NAME_VERSION}
\\rem The source table used to create this file is Copyright © 2022 by https://GreekCNTR.org
\\h {BOOK_NAME_MAP[book_number]}
\\toc1 {BOOK_NAME_MAP[book_number]}
\\toc2 {BOOK_NAME_MAP[book_number]}
\\toc3 {book_tsv_rows[book_number-1]['eAbbreviation']}
\\mt1 {BOOK_NAME_MAP[book_number]}"""
            last_book_number = book_number
            last_chapter_number = last_verse_number = last_word_number = 0
        if chapter_number != last_chapter_number:  # we've started a new chapter
            assert chapter_number == last_chapter_number + 1
            usfm_text = f"{usfm_text}\n\\c {chapter_number}"
            last_chapter_number = chapter_number
            last_verse_number = last_word_number = 0
        if verse_number != last_verse_number:  # we've started a new verse
            # assert verse_number == last_verse_number + 1 # Not always true (some verses are empty)
            # print(f"{chapter_number}:{last_verse_number} {verse_word_dict}")
            # Create the USFM verse text
            usfm_text = f"{usfm_text}\n\\v {verse_number}"
            for index_set in get_gloss_word_index_list(this_verse_row_list):
                if len(index_set) == 1: # the normal and easiest case
                    this_verse_row = this_verse_row_list[index_set[0]]
                    greekWord = this_verse_row['Medieval']
                    usfm_text += f" {preform_gloss(this_verse_row)}"
                    assert '  ' not in usfm_text, f"ERROR: Have double spaces in usfm text: '{usfm_text[:200]} … {usfm_text[-200:]}'"
                else: # we have multiple overlapping glosses
                    sorted_index_set = sorted(index_set) # Some things we display by Greek word order
                    greekWord = ' '.join(this_verse_row_list[ix]['Medieval'] for ix in sorted_index_set)
                    greekWord = f'<b style="color:orange">{greekWord}</b>'
                    preformed_word_string_bits = []
                    last_verse_row = last_glossWord = None
                    for ix in index_set:
                        this_verse_row = this_verse_row_list[ix]
                        some_result = preform_gloss(this_verse_row, last_verse_row, last_glossWord)
                        if this_verse_row['GlossInsert']:
                            last_glossWord = some_result
                        else:
                            preformed_word_string_bits.append(some_result)
                        last_verse_row = this_verse_row
                        # last_glossInsert = last_verse_row['GlossInsert']
                    preformed_word_string = ' '.join(preformed_word_string_bits)
                    usfm_text += f" {preformed_word_string}"
                    assert '  ' not in usfm_text, f"ERROR: Have double spaces in usfm text: '{usfm_text[:200]} … {usfm_text[-200:]}'"
            last_verse_number = verse_number
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
