#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# extract_OSHB_OT_to_USFM.py
#
# Script handling extract_OSHB_OT_to_USFM functions
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
Script extracting the OSHB USFM files
    directly out of the TSV table and with our modifications.
"""
from gettext import gettext as _
from typing import Dict, List, Tuple
from pathlib import Path
from csv import DictReader
from collections import defaultdict
from datetime import datetime

import BibleOrgSysGlobals
from BibleOrgSysGlobals import fnPrint, vPrint, dPrint


LAST_MODIFIED_DATE = '2022-09-28' # by RJH
SHORT_PROGRAM_NAME = "extract_glossed-OSHB_OT_to_USFM"
PROGRAM_NAME = "Extract glossed-OSHB OT USFM files"
PROGRAM_VERSION = '0.02'
PROGRAM_NAME_VERSION = f'{SHORT_PROGRAM_NAME} v{PROGRAM_VERSION}'

DEBUGGING_THIS_MODULE = True


TSV_SOURCE_TABLE_FILEPATH = Path( '../translatedTexts/glossed_OSHB/WLC_glosses.morphemes.tsv' )
OT_USFM_OUTPUT_FOLDERPATH = Path( '../sourceTexts/modified_source_glossed_OSHB_USFM/' )


state = None
class State:
    def __init__( self ) -> None:
        """
        Constructor:
        """
        self.sourceTableFilepath = TSV_SOURCE_TABLE_FILEPATH
    # end of extract_OSHB_OT_to_USFM.__init__


NEWLINE = '\n'
BACKSLASH = '\\'

NUM_EXPECTED_OSHB_COLUMNS = 14
source_tsv_rows = []
source_tsv_column_max_length_counts = {}
source_tsv_column_non_blank_counts = {}
source_tsv_column_counts = defaultdict(lambda: defaultdict(int))
source_tsv_column_headers = []


def main() -> None:
    """
    """
    BibleOrgSysGlobals.introduceProgram( __name__, PROGRAM_NAME_VERSION, LAST_MODIFIED_DATE )
    global state
    state = State()

    if loadSourceGlossTable():
        export_usfm_literal_English_gloss()
# end of extract_OSHB_OT_to_USFM.main


def loadSourceGlossTable() -> bool:
    """
    """
    global source_tsv_column_headers
    print(f"\nLoading {'UPDATED ' if 'updated' in str(state.sourceTableFilepath) else ''}source tsv file from {state.sourceTableFilepath}…")
    print(f"  Expecting {NUM_EXPECTED_OSHB_COLUMNS} columns…")
    with open(state.sourceTableFilepath, 'rt', encoding='utf-8') as tsv_file:
        tsv_lines = tsv_file.readlines()

    # Remove BOM
    if tsv_lines[0].startswith("\ufeff"):
        print("  Removing Byte Order Marker (BOM) from start of source tsv file…")
        tsv_lines[0] = tsv_lines[0][1:]

    # Get the headers before we start
    source_tsv_column_headers = [
        header for header in tsv_lines[0].strip().split('\t')
    ]  # assumes no commas in headings
    # print(f"Column headers: ({len(source_tsv_column_headers)}): {source_tsv_column_headers}")
    assert len(source_tsv_column_headers) == NUM_EXPECTED_OSHB_COLUMNS, f"Found {len(source_tsv_column_headers)} columns! (Expecting {NUM_EXPECTED_OSHB_COLUMNS})"

    # Read, check the number of columns, and summarise row contents all in one go
    dict_reader = DictReader(tsv_lines, delimiter='\t')
    unique_words = set()
    for n, row in enumerate(dict_reader):
        if len(row) != NUM_EXPECTED_OSHB_COLUMNS:
            print(f"Line {n} has {len(row)} columns instead of {NUM_EXPECTED_OSHB_COLUMNS}!!!")
        source_tsv_rows.append(row)
        unique_words.add(row['NoCantillations'])
        for key, value in row.items():
            # source_tsv_column_sets[key].add(value)
            if n==0: # We do it like this (rather than using a defaultdict(int)) so that all fields are entered into the dict in the correct order
                source_tsv_column_max_length_counts[key] = 0
                source_tsv_column_non_blank_counts[key] = 0
            if value:
                if len(value) > source_tsv_column_max_length_counts[key]:
                    source_tsv_column_max_length_counts[key] = len(value)
                source_tsv_column_non_blank_counts[key] += 1
            source_tsv_column_counts[key][value] += 1
    print(f"  Loaded {len(source_tsv_rows):,} source tsv data rows.")
    print(f"    Have {len(unique_words):,} unique Hebrew words (without cantillation marks).")

    return True
# end of extract_OSHB_OT_to_USFM.loadSourceGlossTable


def export_usfm_literal_English_gloss() -> bool:
    """
    Use the GlossOrder field to export the English gloss.
    """
    print("\nExporting USFM plain text literal English files…")
    last_BBB = last_verse_id = None
    last_chapter_number = last_verse_number = last_word_number = 0
    num_exported_files = 0
    usfm_text = ""
    for n, row in enumerate(source_tsv_rows):
        source_id = row['Ref']
        verse_id = source_id.split('-')[0]
        if verse_id != last_verse_id:
            this_verse_row_list = get_verse_rows(source_tsv_rows, n)
            last_verse_id = verse_id

        BBB = verse_id[:3]
        chapter_number = int(verse_id[4:].split(':')[0])
        verse_number = int(verse_id.split(':')[1])
        word_number = source_id.split('-')[1]
        if BBB != last_BBB:  # we've started a new book
            if usfm_text:  # write out the book
                usfm_text = usfm_text.replace('¶', '¶ ') # Looks nicer maybe
                # Fix any punctuation problems
                usfm_text = usfm_text.replace(',,',',').replace('..','.').replace(';;',';') \
                            .replace(',.','.').replace('.”.”','.”').replace('?”?”','?”')
                assert '  ' not in usfm_text
                usfm_filepath = OT_USFM_OUTPUT_FOLDERPATH.joinpath( f'{last_BBB}_gloss.usfm' )
                with open(usfm_filepath, 'wt', encoding='utf-8') as output_file:
                    output_file.write(f"{usfm_text}\n")
                num_exported_files += 1
            USFM_book_code = BibleOrgSysGlobals.loadedBibleBooksCodes.getUSFMAbbreviation( BBB )
            English_book_name = BibleOrgSysGlobals.loadedBibleBooksCodes.getEnglishName_NR( BBB )
            usfm_text = f"""\\id {USFM_book_code}
\\usfm 3.0
\\ide UTF-8
\\rem USFM file created {datetime.now().strftime('%Y-%m-%d %H:%M')} by {PROGRAM_NAME_VERSION}
\\rem The parsed Hebrew text used to create this file is Copyright © 2019 by https://hb.openscriptures.org
\\rem The English glosses are released CC0 by https://Freely-Given.org
\\h {English_book_name}
\\toc1 {English_book_name}
\\toc2 {English_book_name}
\\toc3 {USFM_book_code}
\\mt1 {English_book_name}"""
            last_BBB = BBB
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
            for gloss_index in get_gloss_word_index_list(this_verse_row_list):
                this_verse_row = this_verse_row_list[gloss_index]
                HebrewWordOrMorpheme = this_verse_row['WordOrMorpheme']
                this_row_gloss = preform_gloss(this_verse_row)
                if this_row_gloss:
                    usfm_text = f'{usfm_text} {this_row_gloss}'
                assert '  ' not in usfm_text, f"ERROR1: Have double spaces in usfm text: '{usfm_text[:200]} … {usfm_text[-200:]}'"
            # for index_set in get_gloss_word_index_list(this_verse_row_list):
            #     print(f"{source_id} {index_set=}")
            #     if len(index_set) == 1: # single words -- the normal and easiest case
            #         this_verse_row = this_verse_row_list[index_set[0]]
            #         HebrewWordOrMorpheme = this_verse_row['WordOrMorpheme']
            #         this_row_gloss = preform_gloss(this_verse_row)
            #         if this_row_gloss:
            #             usfm_text = f'{usfm_text} {this_row_gloss}'
            #         assert '  ' not in usfm_text, f"ERROR1: Have double spaces in usfm text: '{usfm_text[:200]} … {usfm_text[-200:]}'"
            #     else: # we have multiple morphemes
            #         sorted_index_set = sorted(index_set) # Some things we display by Hebrew word order
            #         HebrewWordOrMorpheme = '='.join(this_verse_row_list[ix]['WordOrMorpheme'] for ix in sorted_index_set)
            #         HebrewWordOrMorpheme = f'<b style="color:orange">{HebrewWordOrMorpheme}</b>'
            #         preformed_word_string_bits = []
            #         last_verse_row = last_glossWord = None
            #         for ix in index_set:
            #             this_verse_row = this_verse_row_list[ix]
            #             some_result = preform_gloss(this_verse_row, last_verse_row, last_glossWord)
            #             # if this_verse_row['GlossInsert']:
            #             #     last_glossWord = some_result
            #             # else:
            #             preformed_word_string_bits.append(some_result)
            #             last_verse_row = this_verse_row
            #             # last_glossInsert = last_verse_row['GlossInsert']
            #         preformed_word_string = 'Z'.join(preformed_word_string_bits)
            #         usfm_text = f'{usfm_text} {preformed_word_string}'
            #         assert '  ' not in usfm_text, f"ERROR2: Have double spaces in usfm text: '{usfm_text[:200]} … {usfm_text[-200:]}'"
            last_verse_number = verse_number
    if usfm_text:  # write out the book
        usfm_text = usfm_text.replace('¶', '¶ ') # Looks nicer maybe
        # Fix any punctuation problems
        usfm_text = usfm_text.replace(',,',',').replace('..','.').replace(';;',';') \
                    .replace(',.','.').replace('.”.”','.”').replace('?”?”','?”')
        assert '  ' not in usfm_text
        usfm_filepath = OT_USFM_OUTPUT_FOLDERPATH.joinpath( f'{last_BBB}_gloss.usfm' )
        with open(usfm_filepath, 'wt', encoding='utf-8') as output_file:
            output_file.write(f"{usfm_text}\n")
        num_exported_files += 1

    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  {num_exported_files} USFM files exported" )
    return num_exported_files > 0
# end of extract_OSHB_OT_to_USFM.export_usfm_literal_English_gloss


def get_verse_rows(given_source_rows: List[dict], row_index: int) -> List[list]:
    """
    row_index should be the index of the first row for the particular verse

    Returns a list of rows for the verse
    """
    # print(f"get_verse_rows({row_index})")
    this_verse_row_list = []
    this_verseID = given_source_rows[row_index]['Ref'].split('-')[0]
    if row_index > 0: assert not given_source_rows[row_index-1]['Ref'].startswith( this_verseID )
    for ix in range(row_index, len(given_source_rows)):
        row = given_source_rows[ix]
        if row['Ref'].startswith( this_verseID ):
            this_verse_row_list.append(row)
        else: # done
            break
    check_verse_rows(this_verse_row_list, stop_on_error=True)
    return this_verse_row_list
# end of extract_OSHB_OT_to_USFM.get_verse_rows


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
            print(f"  {some_row['sourceID']} {some_row['Variant']} {some_row['Align']} '{some_row['Koine']}' '{some_row['GlossWord']}' {some_row['GlossOrder']} Role={some_row['Role']} Syntax={some_row['Syntax']}")
        if stop_on_error: gloss_order_fields_for_verse_are_not_unique
# end of extract_OSHB_OT_to_USFM.check_verse_rows


def get_gloss_word_index_list(given_verse_row_list: List[dict]) -> List[List[int]]:
    """
    Goes through the verse rows in gloss word order and produces a list of lists of row indexes
        Most entries only contain one index (for one gloss word)
    """
    verse_id = given_verse_row_list[0]['Ref'].split('-')[0]

    # Make up the display order list for this new verse
    gloss_order_dict = {}
    for index,this_verse_row in enumerate(given_verse_row_list):
        assert this_verse_row['Ref'].startswith( verse_id )
        gloss_order_int = int(this_verse_row['GlossOrder'])
        assert gloss_order_int not in gloss_order_dict, f"ERROR: {verse_id} has multiple GlossOrder={gloss_order_int} entries!"
        gloss_order_dict[gloss_order_int] = index
    base_gloss_display_order_list = [index for (_gloss_order,index) in sorted(gloss_order_dict.items())]
    assert len(base_gloss_display_order_list) == len(given_verse_row_list)
    # print(f"get_gloss_word_index_list for {verse_id} is got: ({len(base_gloss_display_order_list)}) {base_gloss_display_order_list}")
    return base_gloss_display_order_list

    these_words_base_display_index_list, result_list = [], []
    for index in base_gloss_display_order_list:
        if 'm' in given_verse_row_list[index]['Type']:
            these_words_base_display_index_list.append(index)
        elif 'M' in given_verse_row_list[index]['Type']:
            these_words_base_display_index_list.append(index)
            result_list.append(these_words_base_display_index_list)
            these_words_base_display_index_list = []
        elif 'w' in given_verse_row_list[index]['Type']:
            assert not these_words_base_display_index_list
            result_list.append([index])
    if these_words_base_display_index_list:
        print(f"Why did get_gloss_word_index_list() for {given_verse_row_list[0]['Ref']} ({len(given_verse_row_list)} rows)"
              f" have left-over words: ({len(these_words_base_display_index_list)}) {these_words_base_display_index_list}"
              f" from glossInserts: {[row['GlossInsert'] for row in given_verse_row_list]}")
    assert not these_words_base_display_index_list # at end of loop
    # print(f"get_gloss_word_index_list for {verse_id} is returning: ({len(result_list)}) {result_list}")
    return result_list
# end of extract_OSHB_OT_to_USFM.get_gloss_word_index_list


saved_gloss = ''
def preform_gloss(given_verse_row: Dict[str,str], last_given_verse_row: Dict[str,str]=None, last_glossWord:str=None) -> str:
    """
    Returns the gloss to display for this row (may be nothing if we have a current GlossInsert)
        or the left-over preformatted GlossWord (if any)
    The calling function has to decide what to do with it.
    """
    global saved_gloss
    # print(f"preform_gloss({given_verse_row['Ref']}.{given_verse_row['Type']}, mg='{given_verse_row['MorphemeGloss']}' wg='{given_verse_row['WordGloss']}' cg='{given_verse_row['ContextualGloss']}' {saved_gloss=}, {last_glossWord=})…")
    gloss = ''
    if 'm' in given_verse_row['Type']:
        gloss = given_verse_row['ContextualGloss'] if given_verse_row['ContextualGloss'] \
                    else given_verse_row['MorphemeGloss']
        if not gloss: gloss = 'mmm' # Sequence doesn't occur in any words
        saved_gloss = f"{saved_gloss}{'=' if saved_gloss else ''}{gloss}"
        return ''
    elif 'M' in given_verse_row['Type']:
        if given_verse_row['ContextualGloss']:
            gloss = given_verse_row['ContextualGloss']
            saved_gloss = '' # Ignore it
        elif given_verse_row['WordGloss']:
            gloss = given_verse_row['WordGloss']
            saved_gloss = '' # Ignore it
        elif given_verse_row['MorphemeGloss']:
            gloss = f"{saved_gloss}={given_verse_row['MorphemeGloss']}"
            saved_gloss = '' # Used it
        if not gloss: # Sequence doesn't occur in any words
            gloss = f'{saved_gloss}=mmm'
            saved_gloss = '' # Used it
        assert not saved_gloss
    elif 'w' in given_verse_row['Type']:
        assert not saved_gloss
        gloss = given_verse_row['ContextualGloss'] if given_verse_row['ContextualGloss'] \
                    else given_verse_row['WordGloss']
        if not gloss: gloss = 'wwww' # Sequence doesn't occur in any English words so easy to find

    if gloss:
        if 'S' in given_verse_row['GlossCapitalisation']:
            gloss = f'{gloss[0].upper()}{gloss[1:]}'

    return f"{gloss}{given_verse_row['GlossPunctuation']}"
# end of extract_OSHB_OT_to_USFM.preform_gloss


# def apply_gloss_capitalization(gloss_pre:str, gloss_helper:str, gloss_word:str, gloss_capitalization) -> Tuple[str,str,str]:
#     """
#     Some undocumented documentation:
#         ●    U – lexical entry capitalized
#         ●    W – proper noun
#         ●    G – reference to deity
#         ●    P – paragraph boundary
#         ●    S – start of sentence
#         ●    D – quoted dialog
#         ●    V – vocative title
#         ●    B – Biblical quotation
#         ●    R – other quotation
#         ●    T – translated words

#         ●    h – partial word capitalized
#         ●    n – named but not proper name
#         ●    b – incorporated Biblical quotation
#         ●    c – continuation of quotation
#         ●    e – emphasized words (scare quotes)
#     The lowercase letters mark other significant places where the words are not normally capitalized.
#     """
#     if gloss_capitalization.lower() != gloss_capitalization: # there's some UPPERCASE values
#         # NOTE: We can't use the title() function here for capitalising or else words like 'you_all' become 'You_All'
#         if 'G' in gloss_capitalization or 'U' in gloss_capitalization or 'W' in gloss_capitalization:
#             gloss_word = f'{gloss_word[0].upper()}{gloss_word[1:]}' # Those are WORD punctuation characters
#         if ('P' in gloss_capitalization or 'S' in gloss_capitalization # new paragraph or sentence
#         or 'D' in gloss_capitalization): # new dialog
#             if gloss_pre: gloss_pre = f'{gloss_pre[0].upper()}{gloss_pre[1:]}'
#             elif gloss_helper: gloss_helper = f'{gloss_helper[0].upper()}{gloss_helper[1:]}'
#             else: gloss_word = f'{gloss_word[0].upper()}{gloss_word[1:]}'
#     return gloss_pre, gloss_helper, gloss_word
# # end of extract_OSHB_OT_to_USFM.apply_gloss_capitalization



if __name__ == '__main__':
    # from multiprocessing import freeze_support
    # freeze_support() # Multiprocessing support for frozen Windows executables

    # Configure basic Bible Organisational System (BOS) set-up
    parser = BibleOrgSysGlobals.setup( SHORT_PROGRAM_NAME, PROGRAM_VERSION, LAST_MODIFIED_DATE )
    BibleOrgSysGlobals.addStandardOptionsAndProcess( parser )

    main()

    BibleOrgSysGlobals.closedown( PROGRAM_NAME, PROGRAM_VERSION )
# end of extract_OSHB_OT_to_USFM.py
