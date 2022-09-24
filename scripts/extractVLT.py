#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# extractVLT.py
#
# Script handling extractVLT functions
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
Script extracting the VLT USFM files
    directly out of the collation table and with our modifications.
Note that we don't use USFM add markers but rather the following:
    ˱I˲ for glossPre
    /may/ for glossHelper, and
    \\add one\\add* for glossPost.
Puts markers around one gloss word inserted near another:
    ˱they˲_> would <_repent (after glossPre)
    /may/_=> not <=_worry (after glossHelper)
    ˱to˲ the_> first <_\\add one\\add* (before glossPost)
"""
from gettext import gettext as _
from typing import Dict, List, Tuple
from pathlib import Path
from csv import DictReader
from collections import defaultdict
from datetime import datetime

import BibleOrgSysGlobals
from BibleOrgSysGlobals import fnPrint, vPrint, dPrint


LAST_MODIFIED_DATE = '2022-09-24' # by RJH
SHORT_PROGRAM_NAME = "extractVLT"
PROGRAM_NAME = "Extract VLT USFM files"
PROGRAM_VERSION = '0.50'
PROGRAM_NAME_VERSION = f'{SHORT_PROGRAM_NAME} v{PROGRAM_VERSION}'

DEBUGGING_THIS_MODULE = True


VLT_USFM_OUTPUT_FOLDERPATH = Path( '../sourceTexts/modified_source_VLT_USFM/' )


state = None
class State:
    def __init__( self ) -> None:
        """
        Constructor:
        """
        self.bookTableFilepath = Path( '../../CNTR-GNT/sourceExports/book.csv' )
        self.sourceTableFilepath = Path( '../../CNTR-GNT/sourceExports/collation.updated.csv' )
    # end of extractVLT.__init__


USFM_BOOK_ID_MAP = {
    40: 'MAT', 41: 'MRK', 42: 'LUK', 43: 'JHN', 44: 'ACT',
    45: 'ROM', 46: '1CO', 47: '2CO', 48: 'GAL', 49: 'EPH', 50: 'PHP', 51: 'COL', 52: '1TH', 53: '2TH', 54: '1TI', 55: '2TI', 56: 'TIT', 57: 'PHM',
    58: 'HEB', 59: 'JAS', 60: '1PE', 61: '2PE', 62: '1JN', 63: '2JN', 64: '3JN', 65: 'JUD', 66: 'REV'}
BOS_BOOK_ID_MAP = {
    40: 'MAT', 41: 'MRK', 42: 'LUK', 43: 'JHN', 44: 'ACT',
    45: 'ROM', 46: 'CO1', 47: 'CO2', 48: 'GAL', 49: 'EPH', 50: 'PHP', 51: 'COL', 52: 'TH1', 53: 'TH2', 54: 'TI1', 55: 'TI2', 56: 'TIT', 57: 'PHM',
    58: 'HEB', 59: 'JAM', 60: 'PE1', 61: 'PE2', 62: 'JN1', 63: 'JN2', 64: 'JN3', 65: 'JDE', 66: 'REV'}
BOOK_NAME_MAP = {
    40: 'Matthew',    41: 'Mark',    42: 'Luke',    43: 'John',    44: 'Acts',
    45: 'Romans',    46: '1 Corinthians',    47: '2 Corinthians',    48: 'Galatians',    49: 'Ephesians',    50: 'Philippians',    51: 'Colossians',
    52: '1 Thessalonians',    53: '2 Thessalonians',    54: '1 Timothy',    55: '2 Timothy',    56: 'Titus',    57: 'Philemon',
    58: 'Hebrews',
    59: 'James',    60: '1 Peter',    61: '2 Peter',    62: '1 John',    63: '2 John',    64: '3 John',    65: 'Jude',
    66: 'Revelation'}
NEWLINE = '\n'
BACKSLASH = '\\'

PRE_WORD_PUNCTUATION_LIST = '[(¶“‘'
ENGLISH_POST_WORD_PUNCTUATION_LIST_STRING = ',.?:;!”’–)…]' # Includes English question mark. Which list should en-dash be in??? -- I think is the right place

SOLO_GLOSS_INSERT_CHARACTERS = '~?&%!' # Don't use digits or # here
    # ? is swap pre and helper,
    # ~ is put pre inside helper with underline
    # & is swap word and post
    # % is swap word and other field in any row with only one other gloss field (think of swapping the two little zeroes in % symbol)
    # ! is insert post into gloss with underline, e.g., gave_over them
COMBINATION_GLOSS_INSERT_CHARACTERS = '<-=_>' # Don't use digits or # here
    # < insert after pre
    # - insert inside helper parts
    # = insert after helper
    # _ insert inside word parts
    # > insert after word and before post
ALLOWED_GLOSS_INSERT_CHARACTERS = f'{SOLO_GLOSS_INSERT_CHARACTERS}{COMBINATION_GLOSS_INSERT_CHARACTERS}'

NUM_EXPECTED_BOOK_COLUMNS = 6
book_csv_rows = []
book_csv_column_counts = defaultdict(lambda: defaultdict(int))
book_csv_column_headers = []


NUM_EXPECTED_COLLATION_COLUMNS = 35
collation_csv_rows = []
collation_csv_column_max_length_counts = {}
collation_csv_column_non_blank_counts = {}
collation_csv_column_counts = defaultdict(lambda: defaultdict(int))
collation_csv_column_headers = []


def main() -> None:
    """
    """
    BibleOrgSysGlobals.introduceProgram( __name__, PROGRAM_NAME_VERSION, LAST_MODIFIED_DATE )
    global state
    state = State()

    if loadBookTable() and loadSourceCollationTable():
        export_usfm_literal_English_gloss()
# end of extractVLT.main


def loadBookTable() -> bool:
    """ """
    print(f"\nLoading book CSV file from {state.bookTableFilepath}…")
    with open(state.bookTableFilepath, 'rt', encoding='utf-8') as book_csv_file:
        book_csv_lines = book_csv_file.readlines()

    # Remove BOM
    if book_csv_lines[0].startswith("\ufeff"):
        print("  Removing Byte Order Marker (BOM) from start of book CSV file…")
        book_csv_lines[0] = book_csv_lines[0][1:]

    # Get the headers before we start
    global book_csv_column_headers
    book_csv_column_headers = [
        header for header in book_csv_lines[0].strip().split(",")
    ]  # assumes no commas in headings
    # print(f"Column headers: ({len(collation_csv_column_headers)}): {collation_csv_column_headers}")
    assert len(book_csv_column_headers) == NUM_EXPECTED_BOOK_COLUMNS

    # Read, check the number of columns, and summarise row contents all in one go
    dict_reader = DictReader(book_csv_lines)
    for n, row in enumerate(dict_reader):
        if len(row) != NUM_EXPECTED_BOOK_COLUMNS:
            print(f"Line {n} has {len(row)} columns instead of {NUM_EXPECTED_BOOK_COLUMNS}")
        # Add an adjusted title
        row['adjustedTitle'] = row['Title'].replace('Κατὰ ','').replace('Πρὸς ','')
        book_csv_rows.append(row)
        for key, value in row.items():
            # book_csv_column_sets[key].add(value)
            book_csv_column_counts[key][value] += 1
    print(f"  Loaded {len(book_csv_rows):,} book CSV data rows.")

    return True
# end of extractVLT.loadBookTable


def loadSourceCollationTable() -> bool:
    """
    """
    global collation_csv_column_headers
    print(f"\nLoading {'UPDATED ' if 'updated' in str(state.sourceTableFilepath) else ''}collation CSV file from {state.sourceTableFilepath}…")
    print(f"  Expecting {NUM_EXPECTED_COLLATION_COLUMNS} columns…")
    with open(state.sourceTableFilepath, 'rt', encoding='utf-8') as csv_file:
        csv_lines = csv_file.readlines()

    # Remove BOM
    if csv_lines[0].startswith("\ufeff"):
        print("  Removing Byte Order Marker (BOM) from start of collation CSV file…")
        csv_lines[0] = csv_lines[0][1:]

    # Get the headers before we start
    collation_csv_column_headers = [
        header for header in csv_lines[0].strip().split(",")
    ]  # assumes no commas in headings
    # print(f"Column headers: ({len(collation_csv_column_headers)}): {collation_csv_column_headers}")
    assert len(collation_csv_column_headers) == NUM_EXPECTED_COLLATION_COLUMNS

    # Read, check the number of columns, and summarise row contents all in one go
    dict_reader = DictReader(csv_lines)
    unique_words = set()
    for n, row in enumerate(dict_reader):
        if len(row) != NUM_EXPECTED_COLLATION_COLUMNS:
            print(f"Line {n} has {len(row)} columns instead of {NUM_EXPECTED_COLLATION_COLUMNS}!!!")
        collation_csv_rows.append(row)
        unique_words.add(row['Medieval'])
        for key, value in row.items():
            # collation_csv_column_sets[key].add(value)
            if n==0: # We do it like this (rather than using a defaultdict(int)) so that all fields are entered into the dict in the correct order
                collation_csv_column_max_length_counts[key] = 0
                collation_csv_column_non_blank_counts[key] = 0
            if value:
                if len(value) > collation_csv_column_max_length_counts[key]:
                    collation_csv_column_max_length_counts[key] = len(value)
                collation_csv_column_non_blank_counts[key] += 1
            collation_csv_column_counts[key][value] += 1
    print(f"  Loaded {len(collation_csv_rows):,} collation CSV data rows.")
    print(f"    Have {len(unique_words):,} unique Greek words.")

    return True
# end of extractVLT.loadSourceCollationTable


def export_usfm_literal_English_gloss() -> bool:
    """
    Use the GlossOrder field to export the English gloss.

    Also uses the GlossInsert field to adjust word order.
    """
    print("\nExporting USFM plain text literal English files…")
    last_book_number = 39 # Start here coz we only do NT
    last_chapter_number = last_verse_number = last_word_number = 0
    last_verse_id = None
    usfm_text = ""
    for n, row in enumerate(collation_csv_rows):
        collation_id, verse_id = row['CollationID'], row['VerseID']
        assert len(collation_id) == 11 and collation_id.isdigit()
        if collation_id == '99999999999':
            this_verse_row_list = None
        else:
            assert len(verse_id) == 8 and verse_id.isdigit()
            if verse_id != last_verse_id:
                this_verse_row_list = get_verse_rows(collation_csv_rows, n)
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
\\toc3 {book_csv_rows[book_number-1]['eAbbreviation']}
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
# end of extractVLT.export_usfm_literal_English_gloss


def get_verse_rows(given_collation_rows: List[dict], row_index: int) -> List[list]:
    """
    row_index should be the index of the first row for the particular verse

    Returns a list of rows for the verse
    """
    # print(f"get_verse_rows({row_index})")
    this_verse_row_list = []
    this_verseID = given_collation_rows[row_index]['VerseID']
    if row_index > 0: assert given_collation_rows[row_index-1]['VerseID'] != this_verseID
    for ix in range(row_index, len(given_collation_rows)):
        row = given_collation_rows[ix]
        if row['VerseID'] == this_verseID:
            this_verse_row_list.append(row)
        else: # done
            break
    check_verse_rows(this_verse_row_list, stop_on_error=True)
    return this_verse_row_list
# end of extractVLT.get_verse_rows


def check_verse_rows(given_verse_row_list: List[dict], stop_on_error:bool=False) -> None:
    """
    Given a set of verse rows, check that all GlossOrder fields are unique if they exist
    """
    gloss_order_set = set()
    for row in given_verse_row_list:
        if not row['GlossOrder']: # We don't have values yet
            return
        gloss_order_set.add(row['GlossOrder'])
    if len(gloss_order_set) < len(given_verse_row_list):
        print(f"ERROR: Verse rows for {given_verse_row_list[0]['VerseID']} have duplicate GlossOrder fields!")
        for some_row in given_verse_row_list:
            print(f"  {some_row['CollationID']} {some_row['Variant']} {some_row['Align']} '{some_row['Koine']}' '{some_row['GlossWord']}' {some_row['GlossOrder']} Role={some_row['Role']} Syntax={some_row['Syntax']}")
        if stop_on_error: gloss_order_fields_for_verse_are_not_unique
# end of extractVLT.check_verse_rows


def get_gloss_word_index_list(given_verse_row_list: List[dict]) -> List[List[int]]:
    """
    Goes through the verse rows in gloss word order and produces a list of lists of row indexes
        Most entries only contain one index (for one gloss word)
        If GlossInsert is set, some contain multiple indexes for the overlapping gloss words
    """
    verse_id = given_verse_row_list[0]['VerseID']

    # Make up the display order list for this new verse
    gloss_order_dict = {}
    for index,this_verse_row in enumerate(given_verse_row_list):
        if this_verse_row['Probability'] and not this_verse_row['CollationID'].endswith('000'): # it's in the text and not word zero
            try: gloss_order_int = int(this_verse_row['GlossOrder'])
            except ValueError: gloss_order_int = int(this_verse_row['CollationID'][8:]) # Use the word number if no GlossOrder field yet
            assert gloss_order_int not in gloss_order_dict, f"ERROR: {verse_id} has multiple GlossOrder={gloss_order_int} entries!"
            gloss_order_dict[gloss_order_int] = index
    base_gloss_display_order_list = [index for (_gloss_order,index) in sorted(gloss_order_dict.items())]
    # print(f"get_gloss_word_index_list for {verse_id} is got: ({len(base_gloss_display_order_list)}) {base_gloss_display_order_list}")


    these_words_base_display_index_list, result_list = [], []
    for index in base_gloss_display_order_list:
        these_words_base_display_index_list.append(index)
        try: gloss_insert_char = given_verse_row_list[index]['GlossInsert']
        except KeyError: gloss_insert_char = None # it's not in Alan's tables yet
        if not gloss_insert_char \
        or gloss_insert_char in SOLO_GLOSS_INSERT_CHARACTERS: # We have a word or word set to add to the result
            result_list.append(these_words_base_display_index_list)
            these_words_base_display_index_list = []
    if these_words_base_display_index_list:
        print(f"Why did get_gloss_word_index_list() for {given_verse_row_list[0]['VerseID']} ({len(given_verse_row_list)} rows)"
              f" have left-over words: ({len(these_words_base_display_index_list)}) {these_words_base_display_index_list}"
              f" from glossInserts: {[row['GlossInsert'] for row in given_verse_row_list]}")
    assert not these_words_base_display_index_list # at end of loop
    # print(f"get_gloss_word_index_list for {verse_id} is returning: ({len(result_list)}) {result_list}")
    return result_list
# end of extractVLT.get_gloss_word_index_list


def preform_gloss(given_verse_row: Dict[str,str], last_given_verse_row: Dict[str,str]=None, last_glossWord:str=None) -> str:
    """
    Returns the gloss to display for this row (may be nothing if we have a current GlossInsert)
        or the left-over preformatted GlossWord (if any)
    The calling function has to decide what to do with it.
    """
    # print(f"preform_gloss({given_verse_row['GlossPre']}.{given_verse_row['GlossHelper']}.{given_verse_row['GlossWord']}.{given_verse_row['GlossPost']}, {last_glossInsert=}, {last_glossWord=})…")
    try: last_glossInsert = last_given_verse_row['GlossInsert']
    except (TypeError, KeyError): last_glossInsert = '' # last row not given or GlossInsert is not in Alan's tables yet
    last_pre_punctuation = last_post_punctuation = ''
    if last_glossInsert:
        last_pre_punctuation, last_post_punctuation = separate_punctuation(last_given_verse_row['GlossPunctuation'])
        last_glossCapitalization = last_given_verse_row['GlossCapitalization']

    glossPre, glossHelper, glossWord, glossPost, glossPunctuation, glossCapitalization \
        = given_verse_row['GlossPre'], given_verse_row['GlossHelper'], given_verse_row['GlossWord'], given_verse_row['GlossPost'], given_verse_row['GlossPunctuation'], given_verse_row['GlossCapitalization']
    try: glossInsert = given_verse_row['GlossInsert']
    except KeyError: glossInsert = '' # it's not in Alan's tables yet
    if given_verse_row['Koine'].startswith( '=' ): # it's a nomina sacra
        glossWord = f"\\nd {glossWord}\\nd*" # we use the USFM divine name style
    pre_punctuation, post_punctuation = separate_punctuation(glossPunctuation)

    # These first ones are different cases coz they all work internally on a single row
    if glossInsert == '~' and not last_glossInsert:
        # Put GlossPre inside GlossHelper
        assert glossPre
        assert '_' in glossHelper
        glossHelper, glossPre, glossWord = apply_gloss_capitalization(glossHelper, glossPre, glossWord, glossCapitalization)
        glossHelper_bits = glossHelper.split('_', 1)
        preformed_word_string = f"{last_glossWord+' ' if last_glossWord else ''}" \
                                f"{pre_punctuation}/{glossHelper_bits[0]}_˱{glossPre}˲_/{glossHelper_bits[1]}_" \
                                f"{glossWord}{' '+BACKSLASH+'add '+glossPost+BACKSLASH+'add*' if glossPost else ''}{post_punctuation}"
    elif glossInsert == '?' and not last_glossInsert:
        # Swap GlossPre and GlossHelper
        assert glossPre
        assert glossHelper
        # assert ' ' not in glossHelper
        glossHelper, glossPre, glossWord = apply_gloss_capitalization(glossHelper, glossPre, glossWord, glossCapitalization)
        preformed_word_string = f"{last_glossWord+' ' if last_glossWord else ''}" \
                                f"{pre_punctuation}/{glossHelper}/_˱{glossPre}˲_" \
                                f"{glossWord}{' '+BACKSLASH+'add '+glossPost+BACKSLASH+'add*' if glossPost else ''}{post_punctuation}"
    elif glossInsert == '&' and not last_glossInsert:
        # Swap GlossWord and GlossPost
        assert glossPost
        glossPre, glossHelper, glossWord = apply_gloss_capitalization(glossPre, glossHelper, glossWord, glossCapitalization)
        preformed_word_string = f"{last_glossWord+' ' if last_glossWord else ''}" \
                                f"{pre_punctuation}{'˱'+glossPre+'˲_' if glossPre else ''}{'/'+glossHelper+'/_' if glossHelper else ''}" \
                                f"\\add {glossPost}\\add* {glossWord}{post_punctuation}"
    elif glossInsert == '!' and not last_glossInsert:
        # Insert GlossPost into GlossWord
        assert glossPost
        assert '_' in glossWord
        glossPre, glossHelper, glossWord = apply_gloss_capitalization(glossPre, glossHelper, glossWord, glossCapitalization)
        glossWord_bits = glossWord.split('_', 1)
        preformed_word_string = f"{last_glossWord+' ' if last_glossWord else ''}" \
                                f"{pre_punctuation}{'˱'+glossPre+'˲_' if glossPre else ''}{'/'+glossHelper+'/_' if glossHelper else ''}" \
                                f"{glossWord_bits[0]}_ \\add {glossPost}\\add* _{glossWord_bits[1]}{post_punctuation}"
    elif glossInsert == '%' and not last_glossInsert: # Swap two gloss fields
        if glossPre and not glossHelper and not glossPost:
            # Swap GlossPre and GlossWord
            _dummyPre, glossHelper, glossWord = apply_gloss_capitalization('', glossHelper, glossWord, glossCapitalization)
            preformed_word_string = f"{last_glossWord+' ' if last_glossWord else ''}" \
                                f"{pre_punctuation}{glossWord}_˱{glossPre}˲{post_punctuation}"
        elif not glossPre and glossHelper and not glossPost:
            # Swap GlossHelper and GlossWord
            glossPre, _dummyHelper, glossWord = apply_gloss_capitalization(glossPre, '', glossWord, glossCapitalization)
            preformed_word_string = f"{last_glossWord+' ' if last_glossWord else ''}" \
                                f"{pre_punctuation}{glossWord}_/{glossHelper}/{post_punctuation}"
        elif not glossPre and not glossHelper and glossPost:
            # Swap GlossWord and GlossPost
            glossPost, glossHelper, glossWord = apply_gloss_capitalization(glossPost, glossHelper, glossWord, glossCapitalization)
            preformed_word_string = f"{last_glossWord+' ' if last_glossWord else ''}" \
                                f"{pre_punctuation}\\add {glossPost}\\add* {glossWord}{post_punctuation}"
        else: bad_2_gloss_insert

    elif last_glossInsert and last_glossInsert not in SOLO_GLOSS_INSERT_CHARACTERS and not glossInsert:
        # print(f"Here with {last_pre_punctuation=} {pre_punctuation=} {last_glossWord=}")
        if last_pre_punctuation and last_glossWord.startswith(last_pre_punctuation):
            last_glossWord = last_glossWord[len(last_pre_punctuation):] # Remove the pre-punctuation off the inserted word
        if pre_punctuation != last_pre_punctuation:
            pre_punctuation = f'{last_pre_punctuation}{pre_punctuation}'
        if last_glossInsert == '<': # insert after pre
            assert last_glossWord
            assert glossPre
            glossPre, _dummyHelper, last_glossWord = apply_gloss_capitalization(glossPre, '', last_glossWord, last_glossCapitalization)
            _dummyPre, glossHelper, glossWord = apply_gloss_capitalization('', glossHelper, glossWord, glossCapitalization)
            preformed_word_string = f"{pre_punctuation}˱{glossPre}˲_> {last_glossWord} <_{'/'+glossHelper+'/_' if glossHelper else ''}" \
                                    f"{glossWord}{' '+BACKSLASH+'add '+glossPost+BACKSLASH+'add*' if glossPost else ''}{post_punctuation}"
            last_glossWord = ''
        elif last_glossInsert == '=': # insert after helper and before word
            assert last_glossWord
            assert glossHelper
            # print(f"Here with {last_glossCapitalization=} {last_glossWord=} {glossCapitalization=} {glossPre=} {glossHelper=} {glossWord=}")
            glossPre, glossHelper, last_glossWord = apply_gloss_capitalization(glossPre, glossHelper, last_glossWord, last_glossCapitalization)
            _dummyPre, _dummyHelper, glossWord = apply_gloss_capitalization('', '', glossWord, glossCapitalization)
            preformed_word_string = f"{pre_punctuation}{'˱'+glossPre+'˲_' if glossPre else ''}/{glossHelper}/_=> " \
                                    f"{last_glossWord} <=_{glossWord}{' '+BACKSLASH+'add '+glossPost+BACKSLASH+'add*' if glossPost else ''}{post_punctuation}"
            last_glossWord = ''
        elif last_glossInsert == '-': # insert inside helper parts
            assert last_glossWord
            glossPre, glossHelper, last_glossWord = apply_gloss_capitalization(glossPre, glossHelper, last_glossWord, last_glossCapitalization)
            _dummyPre, _dummyHelper, glossWord = apply_gloss_capitalization('', '', glossWord, glossCapitalization)
            if '_' in glossHelper:
                glossHelper_bits = glossHelper.split('_', 1)
            else:
                print(f"  Warning: Can't insert '{last_glossWord}' at underline in '{glossHelper}' at {given_verse_row['CollationID']}")
                glossHelper_bits = glossHelper, ''
            preformed_word_string = f"{pre_punctuation}{'˱'+glossPre+'˲_' if glossPre else ''}/{glossHelper_bits[0]}_ {last_glossWord} _{glossHelper_bits[1]}/_" \
                                    f"{glossWord}{' '+BACKSLASH+'add '+glossPost+BACKSLASH+'add*' if glossPost else ''}{post_punctuation}"
            last_glossWord = ''
        elif last_glossInsert == '_': # insert inside word parts
            assert last_glossWord
            # if glossWord.count('_') > 1:
            #     print(f"  Warning: Inserting '{last_glossWord}' at first underline in '{glossWord}' but has {glossWord.count('_')} '_' characters")
            glossPre, glossHelper, last_glossWord = apply_gloss_capitalization(glossPre, glossHelper, last_glossWord, last_glossCapitalization)
            _dummyPre, _dummyHelper, glossWord = apply_gloss_capitalization('', '', glossWord, glossCapitalization)
            glossWord_bits = glossWord.split('_', 1)
            preformed_word_string = f"{pre_punctuation}{'˱'+glossPre+'˲_' if glossPre else ''}{'/'+glossHelper+'/_' if glossHelper else ''}" \
                                    f"{glossWord_bits[0]}_ {last_glossWord} _{glossWord_bits[1]}{' '+BACKSLASH+'add '+glossPost+BACKSLASH+'add*' if glossPost else ''}{post_punctuation}"
            last_glossWord = ''
        elif last_glossInsert == '>': # insert after word and before post
            assert last_glossWord
            assert glossPost
            glossPre, glossHelper, last_glossWord = apply_gloss_capitalization(glossPre, glossHelper, last_glossWord, last_glossCapitalization)
            _dummyPre, _dummyHelper, glossWord = apply_gloss_capitalization('', '', glossWord, glossCapitalization)
            preformed_word_string = f"{pre_punctuation}{'˱'+glossPre+'˲_' if glossPre else ''}{'/'+glossHelper+'/_' if glossHelper else ''}" \
                                    f"{glossWord}_> {last_glossWord} <_\\add {glossPost}\\add*{post_punctuation}"
            last_glossWord = ''
        else:
            print(f"  Warning: Unexpected GlossInsert = '{last_glossInsert}' (ignored)")
    else:
        if glossInsert and last_glossInsert and glossInsert != last_glossInsert:
            msg = f"ERROR: preform_gloss() for {given_verse_row['CollationID']} should not have {glossInsert=} but '{last_glossInsert}'"
            print(msg)
            last_glossWord = f'{msg} {last_glossWord}' # Also insert the error into the returned text so it gets noticed
        if not glossInsert: # (If we do have glossInsert, leave the capitalization for the next round)
            glossPre, glossHelper, glossWord = apply_gloss_capitalization(glossPre, glossHelper, glossWord, glossCapitalization)
        preformed_word_string = f"{pre_punctuation}{last_glossWord+' ' if last_glossWord else ''}{'˱'+glossPre+'˲_' if glossPre else ''}{'/'+glossHelper+'/_' if glossHelper else ''}" \
                                f"{glossWord}{' '+BACKSLASH+'add '+glossPost+BACKSLASH+'add*' if glossPost else ''}{post_punctuation}"
    preformed_result_string = f"{preformed_word_string}"
    assert not preformed_result_string.startswith(' '), preformed_result_string
    assert '  ' not in preformed_result_string, preformed_result_string
    # print(f"  returning '{preformed_result_string}'")
    return preformed_result_string
# end of extractVLT.preform_gloss


def separate_punctuation(given_punctuation:str) -> Tuple[str,str]:
    """
    Take a combination punctuation string and converts it into pre and post punctuation characters.
    """
    # fnPrint( DEBUGGING_THIS_MODULE, f"separate_punctuation({given_punctuation})" )
    pre_punctuation = post_punctuation = ''
    if given_punctuation not in ('.”’”','[[',']]',):
        for char in given_punctuation:
            if given_punctuation.count(char) > 1:
                print(f"  WARNING: have duplicated '{char}' punctuation character(s) in '{given_punctuation}'.")
    improved_given_punctuation = given_punctuation \
                                    .replace(',,',',').replace('..','.').replace('”“','”')
    temporary_copied_punctuation = improved_given_punctuation
    while temporary_copied_punctuation:
        if temporary_copied_punctuation[0] in PRE_WORD_PUNCTUATION_LIST:
            pre_punctuation += temporary_copied_punctuation[0]
            temporary_copied_punctuation = temporary_copied_punctuation[1:]
        elif temporary_copied_punctuation[-1] in ENGLISH_POST_WORD_PUNCTUATION_LIST_STRING:
            post_punctuation = f'{temporary_copied_punctuation[-1]}{post_punctuation}'
            temporary_copied_punctuation = temporary_copied_punctuation[:-1]
        else:
            print(f"ERROR: punctuation character(s) '{temporary_copied_punctuation}' is not handled yet!")
            if __name__ == "__main__": stop_right_here
            break
    if __name__ == "__main__": # don't want this to fail when in the gloss editor
        assert f'{pre_punctuation}{post_punctuation}' == improved_given_punctuation
    return pre_punctuation, post_punctuation
# end of extractVLT.separate_punctuation


def apply_gloss_capitalization(gloss_pre:str, gloss_helper:str, gloss_word:str, gloss_capitalization) -> Tuple[str,str,str]:
    """
    Some undocumented documentation:
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

        ●    h – partial word capitalized
        ●    n – named but not proper name
        ●    b – incorporated Biblical quotation
        ●    c – continuation of quotation
        ●    e – emphasized words (scare quotes)
    The lowercase letters mark other significant places where the words are not normally capitalized.
    """
    if gloss_capitalization.lower() != gloss_capitalization: # there's some UPPERCASE values
        # NOTE: We can't use the title() function here for capitalising or else words like 'you_all' become 'You_All'
        if 'G' in gloss_capitalization or 'U' in gloss_capitalization or 'W' in gloss_capitalization:
            gloss_word = f'{gloss_word[0].upper()}{gloss_word[1:]}' # Those are WORD punctuation characters
        if ('P' in gloss_capitalization or 'S' in gloss_capitalization # new paragraph or sentence
        or 'D' in gloss_capitalization): # new dialog
            if gloss_pre: gloss_pre = f'{gloss_pre[0].upper()}{gloss_pre[1:]}'
            elif gloss_helper: gloss_helper = f'{gloss_helper[0].upper()}{gloss_helper[1:]}'
            else: gloss_word = f'{gloss_word[0].upper()}{gloss_word[1:]}'
    return gloss_pre, gloss_helper, gloss_word
# end of extractVLT.apply_gloss_capitalization



if __name__ == '__main__':
    # from multiprocessing import freeze_support
    # freeze_support() # Multiprocessing support for frozen Windows executables

    # Configure basic Bible Organisational System (BOS) set-up
    parser = BibleOrgSysGlobals.setup( SHORT_PROGRAM_NAME, PROGRAM_VERSION, LAST_MODIFIED_DATE )
    BibleOrgSysGlobals.addStandardOptionsAndProcess( parser )

    main()

    BibleOrgSysGlobals.closedown( PROGRAM_NAME, PROGRAM_VERSION )
# end of extractVLT.py
