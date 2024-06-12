#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# extract_glossed_OSHB_OT_to_ESFM.py
#
# Script handling extract_glossed_OSHB_OT_to_ESFM functions
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
Script extracting the OSHB USFM files
    directly out of the TSV table and with our modifications.

Favors the literal glosses over the contextual ones.
"""
from gettext import gettext as _
from typing import Dict, List, Tuple
from pathlib import Path
from csv import DictReader
from collections import defaultdict
from datetime import datetime
import logging

import BibleOrgSysGlobals
from BibleOrgSysGlobals import fnPrint, vPrint, dPrint


LAST_MODIFIED_DATE = '2024-06-10' # by RJH
SHORT_PROGRAM_NAME = "extract_glossed_OSHB_OT_to_ESFM"
PROGRAM_NAME = "Extract glossed OSHB OT ESFM files"
PROGRAM_VERSION = '0.52'
PROGRAM_NAME_VERSION = f'{SHORT_PROGRAM_NAME} v{PROGRAM_VERSION}'

DEBUGGING_THIS_MODULE = False


INTERMEDIATE_FOLDER = Path( '../intermediateTexts/' )
TSV_SOURCE_MORPHEME_TABLE_FILEPATH = INTERMEDIATE_FOLDER.joinpath( 'glossed_OSHB/all_glosses.morphemes.tsv' )
TSV_SOURCE_WORD_TABLE_FILEPATH = INTERMEDIATE_FOLDER.joinpath( 'glossed_OSHB/all_glosses.words.tsv' )
OT_ESFM_OUTPUT_FOLDERPATH = INTERMEDIATE_FOLDER.joinpath( 'modified_source_glossed_OSHB_ESFM/' )

TAB = '\t'
FOOTNOTE_START = '\\f '
XREF_START = '\\x '


state = None
class State:
    def __init__( self ) -> None:
        """
        Constructor:
        """
        self.sourceMorphemeTableFilepath = TSV_SOURCE_MORPHEME_TABLE_FILEPATH
        self.sourceWordTableFilepath = TSV_SOURCE_WORD_TABLE_FILEPATH
    # end of extract_glossed_OSHB_OT_to_ESFM.__init__


NUM_EXPECTED_OSHB_MORPHEME_COLUMNS = 16
source_morpheme_tsv_rows = []
source_morpheme_tsv_column_max_length_counts = {}
source_morpheme_tsv_column_non_blank_counts = {}
source_morpheme_tsv_column_counts = defaultdict(lambda: defaultdict(int))
source_morpheme_tsv_column_headers = []

NUM_EXPECTED_OSHB_WORD_COLUMNS = 17
source_word_tsv_rows = []
source_word_tsv_column_max_length_counts = {}
source_word_tsv_column_non_blank_counts = {}
source_word_tsv_column_counts = defaultdict(lambda: defaultdict(int))
source_word_tsv_column_headers = []



def main() -> None:
    """
    """
    BibleOrgSysGlobals.introduceProgram( __name__, PROGRAM_NAME_VERSION, LAST_MODIFIED_DATE )
    global state
    state = State()

    if loadSourceMorphemeGlossTable():
        if loadSourceWordGlossTable():
            export_esfm_literal_English_gloss()

            # Delete any saved (but now obsolete) OBD Bible pickle files
            for something in INTERMEDIATE_FOLDER.iterdir():
                if something.name.endswith( '.OBD_Bible.pickle' ):
                    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"Deleting obsolete OBD Bible pickle file {something.name}…" )
                    something.unlink()

        else: print( f"\nFAILED to load words!\n" )

    else: print( f"\nFAILED to load morphemes!\n" )
# end of extract_glossed_OSHB_OT_to_ESFM.main


def loadSourceMorphemeGlossTable() -> bool:
    """
    """
    global source_morpheme_tsv_column_headers
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"\nLoading {'UPDATED ' if 'updated' in str(state.sourceMorphemeTableFilepath) else ''}source tsv file from {state.sourceMorphemeTableFilepath}…")
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  Expecting {NUM_EXPECTED_OSHB_MORPHEME_COLUMNS} columns…")
    with open(state.sourceMorphemeTableFilepath, 'rt', encoding='utf-8') as tsv_file:
        tsv_lines = tsv_file.readlines()

    # Remove any BOM
    if tsv_lines[0].startswith("\ufeff"):
        vPrint( 'Quiet', DEBUGGING_THIS_MODULE, "  Handling Byte Order Marker (BOM) at start of source morpheme tsv file…")
        tsv_lines[0] = tsv_lines[0][1:]

    # Get the headers before we start
    source_morpheme_tsv_column_header_line = tsv_lines[0].strip()
    assert source_morpheme_tsv_column_header_line == 'Ref\tOSHBid\tRowType\tStrongs\tCantillationHierarchy\tMorphology\tWordOrMorpheme\tNoCantillations\tMorphemeGloss\tContextualMorphemeGloss\tWordGloss\tContextualWordGloss\tGlossCapitalisation\tGlossPunctuation\tGlossOrder\tGlossInsert', f"{source_morpheme_tsv_column_header_line=}"
    source_morpheme_tsv_column_headers = [header for header in source_morpheme_tsv_column_header_line.split('\t')]
    # print(f"Column headers: ({len(source_morpheme_tsv_column_headers)}): {source_morpheme_tsv_column_headers}")
    assert len(source_morpheme_tsv_column_headers) == NUM_EXPECTED_OSHB_MORPHEME_COLUMNS, f"Found {len(source_morpheme_tsv_column_headers)} columns! (Expecting {NUM_EXPECTED_OSHB_MORPHEME_COLUMNS})"

    # Read, check the number of columns, and summarise row contents all in one go
    dict_reader = DictReader(tsv_lines, delimiter='\t')
    unique_words = set()
    num_morphemes, max_morphemes, morpheme_refs_list = 0, 0, []
    for n, row in enumerate(dict_reader):
        if len(row) != NUM_EXPECTED_OSHB_MORPHEME_COLUMNS:
            logging.crtical(f"Line {n} has {len(row)} columns instead of {NUM_EXPECTED_OSHB_MORPHEME_COLUMNS}!!!")
        source_morpheme_tsv_rows.append(row)
        unique_words.add(row['NoCantillations'])
        for key, value in row.items():
            # source_morpheme_tsv_column_sets[key].add(value)
            if n==0: # We do it like this (rather than using a defaultdict(int)) so that all fields are entered into the dict in the correct order
                source_morpheme_tsv_column_max_length_counts[key] = 0
                source_morpheme_tsv_column_non_blank_counts[key] = 0
            if value:
                if len(value) > source_morpheme_tsv_column_max_length_counts[key]:
                    source_morpheme_tsv_column_max_length_counts[key] = len(value)
                source_morpheme_tsv_column_non_blank_counts[key] += 1
            source_morpheme_tsv_column_counts[key][value] += 1
            if key == 'RowType':
                if value in ('seg','note','variant note','alternative note','exegesis note'):
                    continue # not of interest here
                assert value in ('m','M','mK','Am','AmK','MK','AM','AMK', 'w','wK','Aw','AwK')
                if 'm' in value:
                    if num_morphemes == 0:
                        saved_morpheme_n = n + 1 # because of header line
                    num_morphemes += 1
                elif 'M' in value:
                    assert num_morphemes > 0
                    num_morphemes += 1
                    if num_morphemes > max_morphemes:
                        max_morphemes = num_morphemes
                    if num_morphemes > 4: # Seems to be only one with five morphemes and 738 with four
                        morpheme_refs_list.append( f'''{num_morphemes}@{saved_morpheme_n}@{tsv_lines[saved_morpheme_n].split(TAB)[0][:-1]}''' ) # Get ref without morpheme letter suffix
                    num_morphemes = 0
                elif 'w' in value:
                    assert num_morphemes == 0
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  Loaded {len(source_morpheme_tsv_rows):,} source morpheme tsv data rows.")
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"    Have {len(unique_words):,} unique Hebrew words (without cantillation marks).")
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"      Max morphemes in one word = {max_morphemes} ({len(morpheme_refs_list)}) {morpheme_refs_list}")

    return len(source_morpheme_tsv_rows) > 0
# end of extract_glossed_OSHB_OT_to_ESFM.loadSourceMorphemeGlossTable


def loadSourceWordGlossTable() -> bool:
    """
    """
    global source_morpheme_tsv_column_headers
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"\nLoading {'UPDATED ' if 'updated' in str(state.sourceWordTableFilepath) else ''}source tsv file from {state.sourceWordTableFilepath}…")
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  Expecting {NUM_EXPECTED_OSHB_WORD_COLUMNS} columns…")
    with open(state.sourceWordTableFilepath, 'rt', encoding='utf-8') as tsv_file:
        tsv_lines = tsv_file.readlines()

    # Remove any BOM
    if tsv_lines[0].startswith("\ufeff"):
        vPrint( 'Quiet', DEBUGGING_THIS_MODULE, "  Handling Byte Order Marker (BOM) at start of source word tsv file…")
        tsv_lines[0] = tsv_lines[0][1:]

    # Get the headers before we start
    source_word_tsv_column_header_line = tsv_lines[0].strip()
    assert source_word_tsv_column_header_line == 'Ref\tOSHBid\tRowType\tMorphemeRowList\tStrongs\tCantillationHierarchy\tMorphology\tWord\tNoCantillations\tMorphemeGlosses\tContextualMorphemeGlosses\tWordGloss\tContextualWordGloss\tGlossCapitalisation\tGlossPunctuation\tGlossOrder\tGlossInsert', f"{source_word_tsv_column_header_line=}"
    source_word_tsv_column_headers = [header for header in source_word_tsv_column_header_line.split('\t')]
    # print(f"Column headers: ({len(source_word_tsv_column_headers)}): {source_word_tsv_column_headers}")
    assert len(source_word_tsv_column_headers) == NUM_EXPECTED_OSHB_WORD_COLUMNS, f"Found {len(source_word_tsv_column_headers)} columns! (Expecting {NUM_EXPECTED_OSHB_MORPHEME_COLUMNS})"

    # Read, check the number of columns, and summarise row contents all in one go
    dict_reader = DictReader(tsv_lines, delimiter='\t')
    unique_words = set()
    for n, row in enumerate(dict_reader):
        if len(row) != NUM_EXPECTED_OSHB_WORD_COLUMNS:
            logging.critical(f"Line {n} has {len(row)} columns instead of {NUM_EXPECTED_OSHB_WORD_COLUMNS}!!!")
        source_word_tsv_rows.append(row)
        unique_words.add(row['NoCantillations'])
        for key, value in row.items():
            # source_word_tsv_column_sets[key].add(value)
            if n==0: # We do it like this (rather than using a defaultdict(int)) so that all fields are entered into the dict in the correct order
                source_word_tsv_column_max_length_counts[key] = 0
                source_word_tsv_column_non_blank_counts[key] = 0
            if value:
                if len(value) > source_word_tsv_column_max_length_counts[key]:
                    source_word_tsv_column_max_length_counts[key] = len(value)
                source_word_tsv_column_non_blank_counts[key] += 1
            source_word_tsv_column_counts[key][value] += 1
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  Loaded {len(source_word_tsv_rows):,} source word tsv data rows.")
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"    Have {len(unique_words):,} unique Hebrew words (without cantillation marks).")

    return len(source_word_tsv_rows) > 0
# end of extract_glossed_OSHB_OT_to_ESFM.loadSourceWordGlossTable


mmmCount = wwwwCount = 0
def export_esfm_literal_English_gloss() -> bool:
    """
    Use the GlossOrder field to export the English gloss.
    """
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"\nExporting ESFM plain text literal English files to {OT_ESFM_OUTPUT_FOLDERPATH}…" )
    final_table_filename = 'OET-LV_OT_word_table.tsv' # Will be made later by associate_LV_people_places.py

    last_BBB = last_verse_id = None
    last_chapter_number = last_verse_number = last_word_number = 0
    num_exported_files = 0
    esfm_text = ""
    for n, row in enumerate(source_word_tsv_rows):
        source_id = row['Ref']
        verse_id = source_id.split('w')[0]
        if verse_id != last_verse_id:
            this_verse_row_list = get_verse_rows(source_word_tsv_rows, n)
            assert this_verse_row_list
            last_verse_id = verse_id

        BBB = verse_id[:3]
        chapter_number = int(verse_id[4:].split(':')[0])
        verse_number = int(verse_id.split(':')[1])
        # word_number = source_id.split('w')[1] if 'w' in source_id else '0'
        if BBB != last_BBB:  # we've started a new book
            if esfm_text:  # write out the book
                esfm_filepath = OT_ESFM_OUTPUT_FOLDERPATH.joinpath( f'{last_BBB}_gloss.ESFM' )
                esfm_text = esfm_text.replace('¶', '¶ ') # Looks nicer maybe
                # Fix any punctuation problems
                esfm_text = esfm_text.replace(',,',',').replace('..','.').replace(';;',';') \
                            .replace(',.','.').replace('.”.”','.”').replace('?”?”','?”')
                # if "Kasda'e" in esfm_text: logging.error( f'''Fixing "Kasda'e" from DAN in {esfm_filepath}''' )
                # esfm_text = esfm_text.replace("Kasda'e", 'Kasda’e') # Where does this come from ???
                assert '  ' not in esfm_text
                # We leave in single quotes for now, e.g., didn't (but proper typographical characters should be used for quotes)
                # assert "'" not in esfm_text, f'''Why do we have single quote in {esfm_filepath}: {esfm_text[esfm_text.index("'")-20:esfm_text.index("'")+22]}'''
                assert '"' not in esfm_text, f'''Why do we have double quote in {esfm_filepath}: {esfm_text[esfm_text.index('"')-20:esfm_text.index('"')+22]}'''
                # assert esfm_text.count('‘') == esfm_text.count('’'), f"{esfm_text.count('‘')} != {esfm_text.count('’')}"
                assert esfm_text.count('“') == esfm_text.count('”'), f"{esfm_text.count('“')} != {esfm_text.count('”')}"
                with open(esfm_filepath, 'wt', encoding='utf-8') as output_file:
                    output_file.write(f"{esfm_text}\n")
                vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Wrote {len(esfm_text)+1:,} bytes to {last_BBB}_gloss.ESFM" )
                num_exported_files += 1
            USFM_book_code = BibleOrgSysGlobals.loadedBibleBooksCodes.getUSFMAbbreviation( BBB )
            English_book_name = BibleOrgSysGlobals.loadedBibleBooksCodes.getEnglishName_NR( BBB )
            esfm_text = f"""\\id {USFM_book_code}
\\usfm 3.0
\\ide UTF-8
\\rem ESFM v0.6 {BBB}
\\rem WORDTABLE {final_table_filename}
\\rem The parsed Hebrew text used to create this file is Copyright © 2019 by https://hb.openscriptures.org
\\rem Our English glosses are released CC0 by https://Freely-Given.org
\\rem ESFM file created {datetime.now().strftime('%Y-%m-%d %H:%M')} by {PROGRAM_NAME_VERSION}
\\h {English_book_name}
\\toc1 {English_book_name}
\\toc2 {English_book_name}
\\toc3 {USFM_book_code}
\\mt1 {'Songs/Psalms' if English_book_name=='Psalms' else English_book_name}"""
            last_BBB = BBB
            last_chapter_number = last_verse_number = last_word_number = 0
        if chapter_number != last_chapter_number:  # we've started a new chapter
            assert chapter_number == last_chapter_number + 1
            esfm_text = f"{esfm_text}\n\\c {chapter_number}"
            last_chapter_number = chapter_number
            last_verse_number = last_word_number = 0
        if verse_number != last_verse_number:  # we've started a new verse
            # assert verse_number == last_verse_number + 1 # Not always true (some verses are empty)
            # print(f"{chapter_number}:{last_verse_number} {verse_word_dict}")
            # Create the USFM verse text
            verse_text = ''
            last_gloss_index = -1
            for gloss_index in get_gloss_word_index_list(this_verse_row_list): # Gets the words in GlossOrder
                this_verse_row = this_verse_row_list[gloss_index]
                # HebrewWord = this_verse_row['Word']
                this_row_gloss = preform_row_gloss(gloss_index==(last_gloss_index+1), this_verse_row)
                dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"  preform_row_gloss() returned '{this_row_gloss}'" )
                if this_row_gloss:
                    verse_text = f"{verse_text}{'' if not verse_text or this_row_gloss[0] in '.,' or this_row_gloss.startswith(FOOTNOTE_START) or this_row_gloss.startswith(XREF_START) else ' '}{this_row_gloss}"
                assert '  ' not in verse_text, f"ERROR1: Have double spaces (marked ‼‼) in {verse_id} verse text: '{verse_text.replace('  ','‼‼')}'"
                last_gloss_index = gloss_index
            dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"\n{verse_id} '{verse_text}'")
            assert not verse_text.startswith(' '), f"{verse_id} '{verse_text}'"
            esfm_text = f"{esfm_text}\n\\v {verse_number} {verse_text}"
            assert '  ' not in esfm_text, f"ERROR1: Have double spaces in esfm text: '{esfm_text[:200]} … {esfm_text[-200:]}'"
            # for index_set in get_gloss_word_index_list(this_verse_row_list):
            #     print(f"{source_id} {index_set=}")
            #     if len(index_set) == 1: # single words -- the normal and easiest case
            #         this_verse_row = this_verse_row_list[index_set[0]]
            #         HebrewWord = this_verse_row['Word']
            #         this_row_gloss = preform_row_gloss(this_verse_row)
            #         if this_row_gloss:
            #             usfm_text = f'{usfm_text} {this_row_gloss}'
            #         assert '  ' not in usfm_text, f"ERROR1: Have double spaces in usfm text: '{usfm_text[:200]} … {usfm_text[-200:]}'"
            #     else: # we have multiple morphemes
            #         sorted_index_set = sorted(index_set) # Some things we display by Hebrew word order
            #         HebrewWord = '='.join(this_verse_row_list[ix]['Word'] for ix in sorted_index_set)
            #         HebrewWord = f'<b style="color:orange">{HebrewWord}</b>'
            #         preformed_word_string_bits = []
            #         last_verse_row = last_glossWord = None
            #         for ix in index_set:
            #             this_verse_row = this_verse_row_list[ix]
            #             some_result = preform_row_gloss(this_verse_row, last_verse_row, last_glossWord)
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
    if esfm_text:  # write out the last book
        esfm_text = esfm_text.replace('¶', '¶ ') # Looks nicer maybe
        # Fix any punctuation problems
        esfm_text = esfm_text.replace(',,',',').replace('..','.').replace(';;',';') \
                    .replace(',.','.').replace('.”.”','.”').replace('?”?”','?”')
        assert '  ' not in esfm_text
        # We leave in single quotes for now, e.g., didn't (but proper typographical characters should be used for quotes)
        # assert "'" not in esfm_text, f'''Why do we have single quote in {esfm_filepath}: {esfm_text[esfm_text.index("'")-20:esfm_text.index("'")+22]}'''
        assert '"' not in esfm_text, f'''Why do we have double quote in {esfm_filepath}: {esfm_text[esfm_text.index('"')-20:esfm_text.index('"')+22]}'''
        assert esfm_text.count('‘') == esfm_text.count('’'), f"{esfm_text.count('‘')} != {esfm_text.count('’')}"
        assert esfm_text.count('“') == esfm_text.count('”'), f"{esfm_text.count('“')} != {esfm_text.count('”')}"
        esfm_filepath = OT_ESFM_OUTPUT_FOLDERPATH.joinpath( f'{last_BBB}_gloss.ESFM' )
        with open(esfm_filepath, 'wt', encoding='utf-8') as output_file:
            output_file.write(f"{esfm_text}\n")
        vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Wrote {len(esfm_text)+1:,} bytes to {last_BBB}_gloss.ESFM" )
        num_exported_files += 1

    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  {num_exported_files} ESFM files exported" )
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"    {wwwwCount:,} word glosses unknown (wwww)" )
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"    {mmmCount:,} morpheme glosses unknown (mmm)" )
    return num_exported_files > 0
# end of extract_glossed_OSHB_OT_to_ESFM.export_esfm_literal_English_gloss


def get_verse_rows(given_source_rows: List[dict], row_index: int) -> List[list]:
    """
    row_index should be the index of the first row for the particular verse

    Returns a list of rows for the verse
    """
    # print(f"get_verse_rows({row_index})")
    this_verse_row_list = []
    this_verseID = given_source_rows[row_index]['Ref'].split('w')[0]
    if row_index > 0: assert not given_source_rows[row_index-1]['Ref'].startswith( this_verseID )
    for ix in range(row_index, len(given_source_rows)):
        row = given_source_rows[ix]
        row['n'] = ix+1 # Append the row number to the row dictionary
        if row['Ref'].startswith( this_verseID ): # because it has word numbers
            this_verse_row_list.append(row)
        else: # done
            break
    assert this_verse_row_list
    check_verse_rows(this_verse_row_list, stop_on_error=True)
    dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"\n{this_verseID} ({len(this_verse_row_list)}) {this_verse_row_list=}")
    return this_verse_row_list
# end of extract_glossed_OSHB_OT_to_ESFM.get_verse_rows


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
        logging.critical(f"ERROR: Verse rows for {given_verse_row_list[0]['VerseID']} have duplicate GlossOrder fields!")
        for some_row in given_verse_row_list:
            logging.error(f"  {some_row['sourceID']} {some_row['Variant']} {some_row['Align']} '{some_row['Koine']}' '{some_row['GlossWord']}' {some_row['GlossOrder']} Role={some_row['Role']} Syntax={some_row['Syntax']}")
        if stop_on_error: gloss_order_fields_for_verse_are_not_unique
# end of extract_glossed_OSHB_OT_to_ESFM.check_verse_rows


def get_gloss_word_index_list(given_verse_row_list: List[dict]) -> List[int]:
    """
    Goes through the verse rows in gloss word order and produces a list of row indexes.
    """
    # print( f"get_gloss_word_index_list( {given_verse_row_list} )")
    assert given_verse_row_list

    verse_id = given_verse_row_list[0]['Ref'].split('w')[0]

    # Make up the display order list for this new verse
    gloss_order_dict = {}
    for index,this_verse_row in enumerate(given_verse_row_list):
        assert this_verse_row['Ref'].startswith( verse_id )
        # print(f"{this_verse_row['Ref']} {this_verse_row['GlossOrder']=}")
        gloss_order_int = int(this_verse_row['GlossOrder'])
        assert gloss_order_int not in gloss_order_dict, f"ERROR: {verse_id} has multiple GlossOrder={gloss_order_int} entries!"
        gloss_order_dict[gloss_order_int] = index
    base_gloss_display_order_list = [index for (_gloss_order,index) in sorted(gloss_order_dict.items())]
    assert len(base_gloss_display_order_list) == len(given_verse_row_list)
    dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"\nget_gloss_word_index_list for {verse_id} is got: ({len(base_gloss_display_order_list)}) {base_gloss_display_order_list}")
    return base_gloss_display_order_list

    # these_words_base_display_index_list, result_list = [], []
    # for index in base_gloss_display_order_list:
    #     if 'm' in given_verse_row_list[index]['Type']:
    #         these_words_base_display_index_list.append(index)
    #     elif 'M' in given_verse_row_list[index]['Type']:
    #         these_words_base_display_index_list.append(index)
    #         result_list.append(these_words_base_display_index_list)
    #         these_words_base_display_index_list = []
    #     elif 'w' in given_verse_row_list[index]['Type']:
    #         assert not these_words_base_display_index_list
    #         result_list.append([index])
    # if these_words_base_display_index_list:
    #     print(f"Why did get_gloss_word_index_list() for {given_verse_row_list[0]['Ref']} ({len(given_verse_row_list)} rows)"
    #           f" have left-over words: ({len(these_words_base_display_index_list)}) {these_words_base_display_index_list}"
    #           f" from glossInserts: {[row['GlossInsert'] for row in given_verse_row_list]}")
    # assert not these_words_base_display_index_list # at end of loop
    # # print(f"get_gloss_word_index_list for {verse_id} is returning: ({len(result_list)}) {result_list}")
    # return result_list
# end of extract_glossed_OSHB_OT_to_ESFM.get_gloss_word_index_list


saved_gloss = saved_capitalisation = ''
just_had_insert = False
def preform_row_gloss(consecutive:bool, given_verse_row: Dict[str,str]) -> str: #, last_given_verse_row: Dict[str,str]=None, last_glossWord:str=None) -> str:
    """
    Returns the gloss to display for this row (may be nothing if we have a current GlossInsert)
        or the left-over preformatted GlossWord (if any)
    The calling function has to decide what to do with it.

    Note: because words and morphemes can be reordered,
            we might now have a word between two morphemes
            or two morphemes between another two morphemes.
    """
    # DEBUGGING_THIS_MODULE = 99
    global saved_gloss, saved_capitalisation, just_had_insert, mmmCount, wwwwCount
    dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"preform_row_gloss({given_verse_row['Ref']}.{given_verse_row['MorphemeRowList']},"
            f" mg='{given_verse_row['MorphemeGlosses']}' cmg='{given_verse_row['ContextualMorphemeGlosses']}'"
            f" wg='{given_verse_row['WordGloss']}' cwg='{given_verse_row['ContextualWordGloss']}'"
            f" {consecutive=} {saved_gloss=} {saved_capitalisation=} {just_had_insert=})…") # {last_glossWord=} 
    assert given_verse_row['GlossInsert'] == '' # None yet
    # if given_verse_row['Ref'].startswith('GEN_3:14'): halt
    
    gloss = ''
    if given_verse_row['RowType'] in ('seg','note','variant note','alternative note','exegesis note'):
        if given_verse_row['RowType'] == 'seg':
            # if given_verse_row['Morphology'] == 'x-sof-pasuq':
            #     gloss = f'{gloss}.'
            # else:
            assert given_verse_row['Morphology'] in ('x-maqqef','x-sof-pasuq','x-pe','x-paseq','x-samekh','x-reversednun'), f"Got seg '{given_verse_row['Morphology']}'"
            dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"Ignoring {given_verse_row['Morphology']} seg!" )
            saved_capitalisation = ''
        elif 'note' in given_verse_row['RowType']:
            _BBB, CV = given_verse_row['Ref'].split( '_', 1 )
            assert 'w' not in CV
            C, V = CV.split( ':', 1 )
            gloss = f"\\f + \\fr {C}:{V} \\ft {given_verse_row['RowType'][0].upper()}{given_verse_row['RowType'][1:]}: {given_verse_row['Word']}\\f*"
        # if saved_gloss:
        #     halt
        #     assert not gloss # otherwise we'd be losing it
        #     gloss = saved_gloss

    elif ',' in given_verse_row['MorphemeRowList']: # then the word consists of two or more morphemes
        gloss = given_verse_row['ContextualWordGloss'] if given_verse_row['ContextualWordGloss'] \
                    else given_verse_row['WordGloss'] if given_verse_row['WordGloss'] \
                    else given_verse_row['ContextualMorphemeGlosses'] if given_verse_row['ContextualMorphemeGlosses'] \
                    else given_verse_row['MorphemeGlosses']
        if gloss:
            gloss = gloss.replace( '_~_', '_' ) # TODO: What did these mean? Place to insert direct object, e.g, make_~_great,him ???
            gloss = gloss.replace( '==', '=' ).replace( ',?,', ',' ).replace( ',,', ',' ) # TODO: How/Why do we have these?
            gloss = gloss.replace( '!', '' ).replace( '=?', '' ).replace( '?', '' ) # e.g., on gloss for 'behold!', 'what?', 'will_you(fs)_be_drunk=?'
            # assert '.' not in gloss and '!' not in gloss, f"{given_verse_row}"
            while gloss.endswith( '~' ): gloss = gloss[:-1] # Remove any trailing tildes
            while gloss.startswith( '_' ): gloss = gloss[1:] # Remove any leading underline separators
            while gloss.startswith( ',' ): gloss = gloss[1:] # Remove any leading comma separators
            while gloss.endswith( ',' ): gloss = gloss[:-1] # Remove any trailing comma separators
            while gloss.startswith( '=' ): gloss = gloss[1:] # Remove any leading equal sign separators
        if gloss:
            assert gloss[0]!=',' and gloss[-1]!=',', f"{given_verse_row=}" # Shouldn't be at start or end of word
            assert gloss[0]!='=' and gloss[-1]!='=', f"{given_verse_row=}" # Shouldn't be at start or end of word
            assert gloss[0]!='÷' and gloss[-1]!='÷', f"{given_verse_row=}" # Shouldn't be at start or end of word
        else: # no gloss
            gloss = 'mmm' # This sequence doesn't occur in any words
            mmmCount += 1
            vPrint( 'Info', DEBUGGING_THIS_MODULE, f"{given_verse_row['Ref']}.{given_verse_row['MorphemeRowList']},"
                                        f" needs a word gloss for '{given_verse_row['Word']}'"
                                        f" (from '{given_verse_row['NoCantillations']}')" )
        if 'S' in given_verse_row['GlossCapitalisation']: # Start of Sentence
            gloss = f'{gloss[0].upper()}{gloss[1:]}'
        wn = f"¦{given_verse_row['n']}"
        gloss = f"{gloss.replace('=',f'{wn}=').replace(',',f'{wn}÷').replace('_',f'{wn}_')}{wn}" # Append the word (row) number(s) and replace comma morpheme separator

    else: # it's only a single morpheme word
        # assert not saved_gloss # NO LONGER TRUE
        wordGloss = given_verse_row['ContextualWordGloss'] if given_verse_row['ContextualWordGloss'] \
                    else given_verse_row['WordGloss']
        wordGloss = wordGloss.replace( '!', '' ).replace( '?', '' ) # e.g., on gloss for 'behold!', 'what?'
        wordGloss = wordGloss.replace( '==', '=' ).replace( ',,', ',' ) # TODO: How/Why do we have these?
        while wordGloss.startswith( '_' ): wordGloss = wordGloss[1:] # Remove any leading underline separators
        if not wordGloss:
            wordGloss = 'wwww' # Sequence doesn't occur in any English words so easy to find
            wwwwCount += 1
            vPrint( 'Info', DEBUGGING_THIS_MODULE, f"{given_verse_row['Ref']}.{given_verse_row['MorphemeRowList']},"
                                            f" needs a word gloss for '{given_verse_row['Word']}'"
                                            f" (from '{given_verse_row['NoCantillations']}')" )
        if 'S' in given_verse_row['GlossCapitalisation']:
            wordGloss = f'{wordGloss[0].upper()}{wordGloss[1:]}'
        wn = f"¦{given_verse_row['n']}"
        wordGloss = f"{wordGloss.replace('=',f'{wn}=').replace(',',f'{wn}÷').replace('_',f'{wn}_')}{wn}" # Append the word (row) number(s) and replace comma morpheme separator

        if saved_gloss: # we must have reordered glosses with a word now between morphemes
            halt
            gloss = f'{saved_gloss}= {wordGloss}'
            saved_gloss = '' # Used it
            if 'S' in saved_capitalisation:
                gloss = f'{gloss[0].upper()}{gloss[1:]}'
                saved_capitalisation = ''
            just_had_insert = True
        else: # no saved gloss -- just an ordinary word
            assert not saved_capitalisation
            gloss = wordGloss
            saved_capitalisation = given_verse_row['GlossCapitalisation']

    if gloss:
        # if saved_capitalisation: print(f"{saved_capitalisation=}")
        if 'S' in saved_capitalisation:
            # print(f"Capitalise ({saved_capitalisation}) '{gloss}'")
            gloss = f'{gloss[0].upper()}{gloss[1:]}'
            # print( f"  Now '{gloss}'")
            saved_capitalisation = ''

    # if given_verse_row['Ref'].startswith('GEN_1:4'): halt
    result = f"{gloss}{given_verse_row['GlossPunctuation']}"
    assert '!¦' not in result, f"{given_verse_row}"
    return result
# end of extract_glossed_OSHB_OT_to_ESFM.preform_row_gloss



if __name__ == '__main__':
    # from multiprocessing import freeze_support
    # freeze_support() # Multiprocessing support for frozen Windows executables

    # Configure basic Bible Organisational System (BOS) set-up
    parser = BibleOrgSysGlobals.setup( SHORT_PROGRAM_NAME, PROGRAM_VERSION, LAST_MODIFIED_DATE )
    BibleOrgSysGlobals.addStandardOptionsAndProcess( parser )

    main()

    BibleOrgSysGlobals.closedown( PROGRAM_NAME, PROGRAM_VERSION )
# end of extract_glossed_OSHB_OT_to_ESFM.py
