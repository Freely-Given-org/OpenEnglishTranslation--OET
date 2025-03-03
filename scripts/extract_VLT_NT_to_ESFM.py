#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# extract_VLT_NT_to_ESFM.py
#
# Script handling extract_VLT_NT_to_ESFM functions
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
Script extracting the initial VLT ESFM files
    directly out of the collation table and with our modifications.
Note that we don't use USFM add markers but rather the following:
    ˱I˲ for glossPre
    ˓may˒ for glossHelper, and
    \\add one\\add* for glossPost.
Puts markers around one gloss word inserted near another:
    ˱they˲_> would <_repent (after glossPre)
    ˓may˒_=> not <=_worry (after glossHelper)
    ˱to˲ the_> first <_\\add one\\add* (before glossPost)
Changes periods in morphology to middle dots

CHANGELOG:
    2023-03-22 Added word numbers to refs in
    2023-07-24 Reduce columns in SR GNT source table
    2023-08-15 Update for new collation table columns plus use of word table for lexemes
    2023-08-16 Puts punctuation markers around gloss parts in 10columns exported table
    2023-08-24 Put some untranslated articles and other words back into the gloss preceded by ¬, e.g., ¬the, ¬of_the
    2023-10-11 Fix a few more lemma transliterations (esp. concerning rough breathings)
    2023-12-14 Add in lemma table that came from CNTR and handle a few more exceptions
    2024-05-07 Make capitalization work when '-' has been changed to '¬the'
    2025-01-15 Change periods in morphology to middle dots
    2025-02-16 Change gloss helper to use ˓˒ instead of // around gloss helper (since / also used for alternative glosses)
    2025-03-03 Added /nb line after chapter numbers
"""
from gettext import gettext as _
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from csv import DictReader
from collections import defaultdict
from datetime import datetime
import logging

import BibleOrgSysGlobals
from BibleOrgSysGlobals import fnPrint, vPrint, dPrint


LAST_MODIFIED_DATE = '2025-03-03' # by RJH
SHORT_PROGRAM_NAME = "Extract_VLT_NT_to_ESFM"
PROGRAM_NAME = "Extract VLT NT ESFM files from TSV"
PROGRAM_VERSION = '0.99'
PROGRAM_NAME_VERSION = f'{SHORT_PROGRAM_NAME} v{PROGRAM_VERSION}'

DEBUGGING_THIS_MODULE = False


INTERMEDIATE_FOLDER = Path( '../intermediateTexts/' )
VLT_GLOSS_ESFM_OUTPUT_FOLDERPATH = INTERMEDIATE_FOLDER.joinpath( 'modified_source_VLT_ESFM/' ) # We copy our {BBB}_gloss.ESFM files into this folder
RV_ESFM_OUTPUT_FOLDERPATH = Path( '../translatedTexts/ReadersVersion/' ) # We also copy the wordfile to this folder

OUR_EXPORT_TABLE_FILENAME = 'OET-LV_NT_word_table.10columns.tsv' # We make this first 10-column version here (from the collation table)
EXPECTED_EXPORT_WORD_TABLE_LINE_COUNT = 168_247


state = None
class State:
    def __init__( self ) -> None:
        """
        Constructor:
        """
        self.bookTableFilepath = Path( '../../CNTR-GNT/sourceExports/book.csv' )
        self.sourceCollationTableFilepath = Path( '../../CNTR-GNT/sourceExports/collation.csv' ) # Use the latest download (symbolic link)
        # self.sourceCollationTableFilepath = Path( '../../CNTR-GNT/sourceExports/collation.updated.csv' )
        self.sourceWordTableFilepath = Path( '../../CNTR-GNT/sourceExports/word.csv' ) # Use the latest download (symbolic link)
        self.CNTRLemmaTableFilepath = Path( '../../CNTR-GNT/derivedFormats/lemmas.alphabetical.tsv' )
    # end of extract_VLT_NT_to_ESFM.__init__


USFM_BOOK_ID_MAP = {
    40: 'MAT', 41: 'MRK', 42: 'LUK', 43: 'JHN', 44: 'ACT',
    45: 'ROM', 46: '1CO', 47: '2CO', 48: 'GAL', 49: 'EPH', 50: 'PHP', 51: 'COL', 52: '1TH', 53: '2TH', 54: '1TI', 55: '2TI', 56: 'TIT', 57: 'PHM',
    58: 'HEB', 59: 'JAS', 60: '1PE', 61: '2PE', 62: '1JN', 63: '2JN', 64: '3JN', 65: 'JUD', 66: 'REV'}
BOS_BOOK_ID_MAP = {
    40: 'MAT', 41: 'MRK', 42: 'LUK', 43: 'JHN', 44: 'ACT',
    45: 'ROM', 46: 'CO1', 47: 'CO2', 48: 'GAL', 49: 'EPH', 50: 'PHP', 51: 'COL', 52: 'TH1', 53: 'TH2', 54: 'TI1', 55: 'TI2', 56: 'TIT', 57: 'PHM',
    58: 'HEB', 59: 'JAM', 60: 'PE1', 61: 'PE2', 62: 'JN1', 63: 'JN2', 64: 'JN3', 65: 'JDE', 66: 'REV', 99:None}
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

SOLO_GLOSS_INSERT_CHARACTERS = '?~@&%!' # Don't use digits or # here
    # ? is swap pre and helper,
    # ~ is put pre inside helper with underline
    # @ is put pre inside word with underline
    # & is swap word and post
    # % is swap word and other field in any row with only one other gloss field (think of swapping the two little zeroes in % symbol)
    #           e.g., ˱it˲ revealed
    #       Of course, this can be used instead of & if there's no pre and no helper.
    # ! is insert post into word with underline, e.g., gave_over them
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
# Last time we looked (2023-08-15) with 168,229 rows, 35-column header was:
# CollationID,VerseID,VariantID,Relation,Pattern,Translatable,Align,Span,Incomplete,Classic,Koine,Medieval,Probability,Historical,Capitalization,Punctuation,Role,Syntax,Morphology,Sic,LexemeID,Sense,GlossPre,GlossHelper,GlossWord,GlossPost,GlossPunctuation,GlossCapitalization,GlossOrder,GlossInsert,Reference,Notes,If,Then,Timestamp
# and table had many 'NULL' entries
# Last time we looked (2023-07-24) with 168,224 rows, 35-column header was:
# CollationID,VerseID,VariantID,Relation,Pattern,Translatable,Align,Span,Incomplete,Classic,Koine,Medieval,Probability,Historical,Capitalization,Punctuation,Role,Syntax,Morphology,Sic,LexemeID,Sense,GlossPre,GlossHelper,GlossWord,GlossPost,GlossPunctuation,GlossCapitalization,GlossOrder,GlossInsert,Reference,Notes,If,Then,Timestamp
# and table had many 'NULL' entries
# Last time we looked (2023-03-06) with 168,262 rows, 36-column header was:
# CollationID,VerseID,VariantID,Relation,Pattern,Translatable,Align,Span,Incomplete,Classic,Koine,Medieval,Probability,Historical,Capitalization,Punctuation,Role,Syntax,Morphology,Sic,Lemma,LexemeID,Sense,GlossPre,GlossHelper,GlossWord,GlossPost,GlossPunctuation,GlossCapitalization,GlossOrder,GlossInsert,Reference,Notes,If,Then,Timestamp
# and table had many 'NULL' entries
# Last time we looked (2023-03-09) with 168,263 rows, 37-column header was:
# CollationID,VerseID,VariantID,VariantID1,Relation,Pattern,Translatable,Align,Span,Incomplete,Classic,Koine,Medieval,Probability,Historical,Capitalization,Punctuation,Role,Syntax,Morphology,Sic,Lemma,LexemeID,Sense,GlossPre,GlossHelper,GlossWord,GlossPost,GlossPunctuation,GlossCapitalization,GlossOrder,GlossInsert,Reference,Notes,If,Then,Timestamp
# and table had many 'NULL' entries
# Last time we looked (2023-03-16) with 168,263 rows, 38-column header was:
# CollationID,VerseID,VariantID,VariantID1,Relation,Pattern,Translatable,Checking,Align,Span,Incomplete,Classic,Koine,Medieval,Probability,Historical,Capitalization,Punctuation,Role,Syntax,Morphology,Sic,Lemma,LexemeID,Sense,GlossPre,GlossHelper,GlossWord,GlossPost,GlossPunctuation,GlossCapitalization,GlossOrder,GlossInsert,Reference,Notes,If,Then,Timestamp
# and table had many 'NULL' entries
# Last time we looked (2023-03-17) with 168,263 rows, 37-column header was:
# CollationID,VerseID,VariantID,Relation,Pattern,Translatable,Checking,Align,Span,Incomplete,Classic,Koine,Medieval,Probability,Historical,Capitalization,Punctuation,Role,Syntax,Morphology,Sic,Lemma,LexemeID,Sense,GlossPre,GlossHelper,GlossWord,GlossPost,GlossPunctuation,GlossCapitalization,GlossOrder,GlossInsert,Reference,Notes,If,Then,Timestamp
# and table had many 'NULL' entries
collation_csv_rows = []
collation_csv_column_max_length_counts = {}
collation_csv_column_non_blank_counts = {}
collation_csv_column_counts = defaultdict(lambda: defaultdict(int))
collation_csv_column_headers = []

# 'LexemeID,Lemma,LemmaE,Template,Classic,Medieval,Role,Morphology,Attested,Irregular,Movable,Clitic'
NUM_EXPECTED_WORD_COLUMNS = 12 # and 22,385 rows # was 13 and 22,398 rows
word_csv_rows = []
word_csv_column_max_length_counts = {}
word_csv_column_non_blank_counts = {}
word_csv_column_counts = defaultdict(lambda: defaultdict(int))
word_csv_column_headers = []

NUM_EXPECTED_LEMMA_COLUMNS = 4 # and 6,416 total rows
lemma_tsv_rows = []
lemma_tsv_column_headers = []
lexemeID_CNTRLemma_dict = {}



def main() -> None:
    """
    """
    BibleOrgSysGlobals.introduceProgram( __name__, PROGRAM_NAME_VERSION, LAST_MODIFIED_DATE )
    global state
    state = State()

    if loadBookTable() and loadSourceCollationTable() and loadSourceWordTable() and loadLemmaTable():
        # export_usfm_literal_English_gloss()
        export_esfm_literal_English_gloss()

        # Delete any saved (but now obsolete) OBD Bible pickle files
        for something in INTERMEDIATE_FOLDER.iterdir():
            if something.name.endswith( '.OBD_Bible.pickle' ):
                vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"Deleting obsolete OBD Bible pickle file {something.name}…" )
                something.unlink()
# end of extract_VLT_NT_to_ESFM.main


def loadBookTable() -> bool:
    """ """
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"\nLoading book CSV file from {state.bookTableFilepath}…")
    with open(state.bookTableFilepath, 'rt', encoding='utf-8') as book_csv_file:
        book_csv_lines = book_csv_file.readlines()

    # Remove any BOM
    if book_csv_lines[0].startswith("\ufeff"):
        vPrint( 'Normal', DEBUGGING_THIS_MODULE, "  Handling Byte Order Marker (BOM) at start of book CSV file…")
        book_csv_lines[0] = book_csv_lines[0][1:]

    # Get the headers before we start
    global book_csv_column_headers
    book_csv_column_headers = [header for header in book_csv_lines[0].strip().split(",")] # assumes no commas in headings
    # vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"Column headers: ({len(collation_csv_column_headers)}): {collation_csv_column_headers}")
    assert len(book_csv_column_headers) == NUM_EXPECTED_BOOK_COLUMNS

    # Read, check the number of columns, and summarise row contents all in one go
    dict_reader = DictReader(book_csv_lines)
    for n, row in enumerate(dict_reader):
        if len(row) != NUM_EXPECTED_BOOK_COLUMNS:
            vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"Line {n} has {len(row)} columns instead of {NUM_EXPECTED_BOOK_COLUMNS}")
        # Add an adjusted title
        row['adjustedTitle'] = row['Title'].replace('Κατὰ ','').replace('Πρὸς ','')
        book_csv_rows.append(row)
        for key, value in row.items():
            if value == 'NULL':
                row[key] = value = None
            # book_csv_column_sets[key].add(value)
            book_csv_column_counts[key][value] += 1
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Loaded {len(book_csv_rows):,} book CSV data rows.")

    return True
# end of extract_VLT_NT_to_ESFM.loadBookTable


def loadSourceCollationTable() -> bool:
    """
    """
    global collation_csv_column_headers
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"\nLoading {'UPDATED ' if 'updated' in str(state.sourceCollationTableFilepath) else ''}collation CSV file from {state.sourceCollationTableFilepath}…")
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Expecting {NUM_EXPECTED_COLLATION_COLUMNS} columns…")
    with open(state.sourceCollationTableFilepath, 'rt', encoding='utf-8') as csv_file:
        csv_lines = csv_file.readlines()

    # Remove any BOM
    if csv_lines[0].startswith("\ufeff"):
        vPrint( 'Normal', DEBUGGING_THIS_MODULE, "  Handling Byte Order Marker (BOM) at start of collation CSV file…")
        csv_lines[0] = csv_lines[0][1:]

    # Get the headers before we start
    collation_csv_column_headers = [header for header in csv_lines[0].strip().split(',')] # assumes no commas in headings
    # vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"Column headers: ({len(collation_csv_column_headers)}): {collation_csv_column_headers}")
    assert len(collation_csv_column_headers) == NUM_EXPECTED_COLLATION_COLUMNS, f"{len(collation_csv_column_headers)=} {NUM_EXPECTED_COLLATION_COLUMNS=}"
    # Check that the columns we use are still there somewhere
    assert 'CollationID' in collation_csv_column_headers
    assert 'VerseID' in collation_csv_column_headers
    assert 'Classic' in collation_csv_column_headers
    assert 'Medieval' in collation_csv_column_headers
    assert 'GlossPre' in collation_csv_column_headers
    assert 'GlossHelper' in collation_csv_column_headers
    assert 'GlossWord' in collation_csv_column_headers
    assert 'GlossPost' in collation_csv_column_headers
    assert 'GlossInsert' in collation_csv_column_headers
    assert 'Morphology' in collation_csv_column_headers

    # Read, check the number of columns, and summarise row contents all in one go
    dict_reader = DictReader(csv_lines)
    unique_words = set()
    for n, row in enumerate(dict_reader):
        if len(row) != NUM_EXPECTED_COLLATION_COLUMNS:
            vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"Collation line {n} has {len(row)} columns instead of {NUM_EXPECTED_COLLATION_COLUMNS}!!!")
        row['Morphology'] = row['Morphology'].replace( '.', '·' ) # Replace period with middle dot for our use (helps to distinguish them later)
        collation_csv_rows.append(row)
        unique_words.add(row['Medieval'])
        for key, value in row.items():
            if value == 'NULL':
                row[key] = value = None
            # collation_csv_column_sets[key].add(value)
            if n==0: # We do it like this (rather than using a defaultdict(int)) so that all fields are entered into the dict in the correct order
                collation_csv_column_max_length_counts[key] = 0
                collation_csv_column_non_blank_counts[key] = 0
            if value:
                if len(value) > collation_csv_column_max_length_counts[key]:
                    collation_csv_column_max_length_counts[key] = len(value)
                collation_csv_column_non_blank_counts[key] += 1
            collation_csv_column_counts[key][value] += 1
    assert len(collation_csv_rows) == EXPECTED_EXPORT_WORD_TABLE_LINE_COUNT, f"{EXPECTED_EXPORT_WORD_TABLE_LINE_COUNT=} {len(collation_csv_rows)}"
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Loaded {len(collation_csv_rows):,} collation CSV data rows.")
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"    Have {len(unique_words):,} unique Greek words.")

    return True
# end of extract_VLT_NT_to_ESFM.loadSourceCollationTable


def loadSourceWordTable() -> bool:
    """
    """
    global word_csv_column_headers
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"\nLoading {'UPDATED ' if 'updated' in str(state.sourceWordTableFilepath) else ''}word CSV file from {state.sourceWordTableFilepath}…")
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Expecting {NUM_EXPECTED_WORD_COLUMNS} columns…")
    with open(state.sourceWordTableFilepath, 'rt', encoding='utf-8') as csv_file:
        csv_lines = csv_file.readlines()

    # Remove any BOM
    if csv_lines[0].startswith("\ufeff"):
        vPrint( 'Normal', DEBUGGING_THIS_MODULE, "  Handling Byte Order Marker (BOM) at start of word CSV file…")
        csv_lines[0] = csv_lines[0][1:]

    # Get the headers before we start
    word_csv_column_headers = [header for header in csv_lines[0].strip().split(',')] # assumes no commas in headings
    # vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"Column headers: ({len(word_csv_column_headers)}): {word_csv_column_headers}")
    assert len(word_csv_column_headers) == NUM_EXPECTED_WORD_COLUMNS, f"{len(word_csv_column_headers)=} {NUM_EXPECTED_WORD_COLUMNS=}"
    # Check that the columns we use are still there somewhere
    assert 'LexemeID' in word_csv_column_headers
    assert 'Lemma' in word_csv_column_headers
    assert 'Medieval' in word_csv_column_headers
    assert 'Morphology' in word_csv_column_headers

    # Read, check the number of columns, and summarise row contents all in one go
    dict_reader = DictReader(csv_lines)
    unique_words = set()
    for n, row in enumerate(dict_reader):
        if len(row) != NUM_EXPECTED_WORD_COLUMNS:
            vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"Word line {n} has {len(row)} columns instead of {NUM_EXPECTED_WORD_COLUMNS}!!!")
        row['Morphology'] = row['Morphology'].replace( '.', '·' ) # Replace period with middle dot for our use (helps to distinguish them later)
        word_csv_rows.append(row)
        unique_words.add(row['Medieval'])
        for key, value in row.items():
            if value == 'NULL':
                row[key] = value = None
            # word_csv_column_sets[key].add(value)
            if n==0: # We do it like this (rather than using a defaultdict(int)) so that all fields are entered into the dict in the correct order
                word_csv_column_max_length_counts[key] = 0
                word_csv_column_non_blank_counts[key] = 0
            if value:
                if len(value) > word_csv_column_max_length_counts[key]:
                    word_csv_column_max_length_counts[key] = len(value)
                word_csv_column_non_blank_counts[key] += 1
            word_csv_column_counts[key][value] += 1
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Loaded {len(word_csv_rows):,} word CSV data rows.")
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"    Have {len(unique_words):,} unique Greek words.")

    return True
# end of extract_VLT_NT_to_ESFM.loadSourceWordTable


def loadLemmaTable() -> bool:
    """ """
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"\nLoading lemma TSV file from {state.CNTRLemmaTableFilepath}…")
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Expecting {NUM_EXPECTED_LEMMA_COLUMNS} columns…")
    with open(state.CNTRLemmaTableFilepath, 'rt', encoding='utf-8') as lemma_tsv_file:
        lemma_tsv_lines = lemma_tsv_file.readlines()

    # Remove any BOM
    if lemma_tsv_lines[0].startswith("\ufeff"):
        vPrint( 'Normal', DEBUGGING_THIS_MODULE, "  Handling Byte Order Marker (BOM) at start of lemma TSV file…")
        lemma_tsv_lines[0] = lemma_tsv_lines[0][1:]

    # Get the headers before we start
    global lemma_tsv_column_headers
    lemma_tsv_column_headers = [header for header in lemma_tsv_lines[0].strip().split('\t')]
    # vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"Column headers: ({len(collation_csv_column_headers)}): {collation_csv_column_headers}")
    assert len(lemma_tsv_column_headers) == NUM_EXPECTED_LEMMA_COLUMNS, f"{lemma_tsv_column_headers=} {NUM_EXPECTED_LEMMA_COLUMNS=}"

    # Read, check the number of columns, and summarise row contents all in one go
    dict_reader = DictReader(lemma_tsv_lines, delimiter='\t')
    for n, row in enumerate(dict_reader):
        if len(row) != NUM_EXPECTED_LEMMA_COLUMNS:
            vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"Line {n} has {len(row)} columns instead of {NUM_EXPECTED_LEMMA_COLUMNS}")
        lemma_tsv_rows.append(row)

        ld_key = (row['LexemeID'],row['Lemma'])
        assert ld_key not in lexemeID_CNTRLemma_dict
        lexemeID_CNTRLemma_dict[ld_key] = row['Greek']

    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Loaded {len(lemma_tsv_rows):,} lemma TSV data rows.")

    return True
# end of extract_VLT_NT_to_ESFM.loadLemmaTable


def write_gloss_esfm_book(book_number:int, book_esfm: str) -> bool:
    """
    """
    usfm_filepath = VLT_GLOSS_ESFM_OUTPUT_FOLDERPATH.joinpath( f'{BOS_BOOK_ID_MAP[book_number]}_gloss.ESFM' )
    book_esfm = book_esfm.replace('¶', '¶ ') # Looks nicer maybe
    # Fix any punctuation problems
    if '..' in book_esfm:
        ix = book_esfm.index( '..' )
        print( f"Found periods in book {book_number}: '{book_esfm[ix-20:ix+20]}'" )
        halt
    book_esfm = book_esfm.replace(',,',',').replace('..','.').replace(';;',';') \
                .replace(',.','.').replace('.”.”','.”').replace('?”?”','?”')
    # if "another's" in book_usfm or "Lord's" in book_usfm:
    #     logging.error( f'''Fixing "another's" in {usfm_filepath}''' )
    # book_usfm = book_usfm.replace("another's", 'another’s').replace("Lord's", 'Lord’s') # Where do these come from?
    assert '  ' not in book_esfm
    # assert "'" not in book_usfm, f'''Why do we have single quote in {usfm_filepath}: {book_usfm[book_usfm.index("'")-20:book_usfm.index("'")+22]}'''
    assert '"' not in book_esfm, f'''Why do we have double quote in {usfm_filepath}: {book_esfm[book_esfm.index('"')-20:book_esfm.index('"')+22]}'''
    with open(usfm_filepath, 'wt', encoding='utf-8') as output_file:
        output_file.write(f"{book_esfm}\n")
    return True
# end of extract_VLT_NT_to_ESFM.write_gloss_esfm_book


def export_esfm_literal_English_gloss() -> bool:
    """
    Use the GlossOrder field to export the English gloss.

    Also uses the GlossInsert field to adjust word order.

    Simultaneously creates the word data table (TSV) from the collation table.
    """
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, "\nExporting ESFM plain text literal English files…" )
    last_book_number = 39 # Start here coz we only do NT
    last_chapter_number = last_verse_number = last_word_number = 0
    last_verse_id = None
    esfm_text = ''
    num_books_written = 0
    final_table_filename = 'OET-LV_NT_word_table.tsv' # Will be made later by add_tags_to_NT_word_table.py
    table_filepath = VLT_GLOSS_ESFM_OUTPUT_FOLDERPATH.joinpath( OUR_EXPORT_TABLE_FILENAME )
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Exporting ESFM auxilliary word table to {table_filepath}…" )
    next_word_number = 1 # word count includes variants
    with open(table_filepath, 'wt', encoding='utf-8') as table_output_file:
        table_output_file.write( 'Ref\tGreekWord\tSRLemma\tGreekLemma\tVLTGlossWords\tGlossCaps\tProbability\tStrongsExt\tRole\tMorphology\n' ) # Write TSV header row
        for collation_row_number, collation_row in enumerate(collation_csv_rows):
            collation_id, verse_id = collation_row['CollationID'], collation_row['VerseID']
            assert len(collation_id) == 11 and collation_id.isdigit()
            assert collation_id.startswith( verse_id )
            book_number, chapter_number, verse_number, word_number \
                = int(collation_id[:2]), int(collation_id[2:5]), int(collation_id[5:8]), int(collation_id[8:])

            # Use the original table row to put the gloss into the literal text
            # if collation_id == '99999999999':
            #     this_verse_row_list = None

            # else:
            assert len(verse_id) == 8 and verse_id.isdigit()
            if verse_id != last_verse_id:
                this_verse_row_list = get_verse_rows(collation_csv_rows, collation_row_number)
                last_verse_id = verse_id

            if book_number != last_book_number:  # we've started a new book
                if book_number != 99:
                    assert book_number == last_book_number + 1
                if esfm_text:  # write out the book (including the last one if final collation row 99999 exists)
                    assert '**' not in esfm_text
                    if write_gloss_esfm_book( last_book_number, esfm_text ):
                        num_books_written += 1
                    esfm_text = None
                if book_number == 99:
                    break  # all done!
                USFM_book_code = USFM_BOOK_ID_MAP[book_number]
                esfm_text = f"""\\id {USFM_book_code}
\\usfm 3.0
\\ide UTF-8
\\rem ESFM v0.6 {BOS_BOOK_ID_MAP[book_number]}
\\rem WORDTABLE {final_table_filename}
\\rem The VLT source table used to create this file is Copyright © 2022 by https://GreekCNTR.org
\\rem ESFM file created {datetime.now().strftime('%Y-%m-%d %H:%M')} by {PROGRAM_NAME_VERSION}
\\h {BOOK_NAME_MAP[book_number]}
\\toc1 {BOOK_NAME_MAP[book_number]}
\\toc2 {BOOK_NAME_MAP[book_number]}
\\toc3 {book_csv_rows[book_number-1]['eAbbreviation']}
\\mt1 {BOOK_NAME_MAP[book_number]}"""
                last_book_number = book_number
                last_chapter_number = last_verse_number = last_word_number = 0
            if chapter_number != last_chapter_number:  # we've started a new chapter
                assert chapter_number == last_chapter_number + 1
                esfm_text = f"{esfm_text}\n\\c {chapter_number}\n\\nb"
                last_chapter_number = chapter_number
                last_verse_number = last_word_number = 0
            if verse_number != last_verse_number:  # we've started a new verse
                # assert verse_number == last_verse_number + 1 # Not always true (some verses are empty)
                # vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"{chapter_number}:{last_verse_number} {verse_word_dict}")
                word_matching_dict = {}
                # Create the USFM verse text
                esfm_text = f"{esfm_text}\n\\v {verse_number}"
                for index_set in get_gloss_word_index_list(this_verse_row_list):
                    # print( f"{index_set=}" )
                    if len(index_set) == 1: # the normal and easiest case
                        # this_verse_row = this_verse_row_list[index_set[0]]
                        # greekWord = this_verse_row['Medieval']
                        preformedGloss = preform_gloss_and_word_number(this_verse_row_list, index_set[0], row_offset=collation_row_number)
                        _adjusted_lemma, preformedGloss = process_untranslated_words( this_verse_row_list[index_set[0]], preformedGloss )
                        # esfm_text += f" {preform_gloss_and_word_number(this_verse_row_list, index_set[0], row_offset=collation_row_number)}"
                        esfm_text = f"{esfm_text} {preformedGloss}"
                        assert '  ' not in esfm_text, f"ERROR: Have double spaces in esfm text: '{esfm_text[:200]} … {esfm_text[-200:]}'"
                    else: # we have multiple overlapping glosses
                        sorted_index_set = sorted(index_set) # Some things we display by Greek word order
                        # greekWord = ' '.join(this_verse_row_list[ix]['Medieval'] for ix in sorted_index_set)
                        # greekWord = f'<b style="color:orange">{greekWord}</b>'
                        preformed_word_string_bits = []
                        last_verse_row_index = last_glossWord = None
                        for this_verse_row_index in index_set:
                            # this_verse_row = this_verse_row_list[this_verse_row_index]
                            preformedGloss = preform_gloss_and_word_number(this_verse_row_list, this_verse_row_index, last_verse_row_index, last_glossWord, row_offset=collation_row_number)
                            _adjusted_lemma, preformedGloss = process_untranslated_words( this_verse_row_list[this_verse_row_index], preformedGloss )
                            if this_verse_row_list[this_verse_row_index]['GlossInsert']:
                                last_glossWord = preformedGloss
                            else:
                                preformed_word_string_bits.append(preformedGloss)
                            last_verse_row_index = this_verse_row_index
                            # last_glossInsert = last_verse_row['GlossInsert']
                        preformed_word_string = ' '.join(preformed_word_string_bits)
                        esfm_text += f" {preformed_word_string}"
                        assert '  ' not in esfm_text, f"ERROR: Have double spaces in esfm text: '{esfm_text[:200]} … {esfm_text[-200:]}'"
                last_verse_number = verse_number

            # Now write our summary table row, i.e., only some of the columns
            # NOTE: It's very easy to add more columns if necessary
            #           -- just need to remember to update the header (above) as well.
            BBB = BOS_BOOK_ID_MAP[book_number]
            ref = f'{BBB}_{chapter_number}:{verse_number}w{word_number}'

            for gloss_part_name in ('GlossPre', 'GlossHelper', 'GlossWord', 'GlossPost'):
                if collation_row[gloss_part_name]:
                    # Check because we use a space-separated list just below
                    if ' ' in collation_row[gloss_part_name]:
                        logging.critical( f"{collation_row_number} Unexpected space in {gloss_part_name} '{collation_row[gloss_part_name]}' from {collation_row}" )
            # gloss_list = [collation_row[gloss_part_name] for gloss_part_name in ('GlossPre', 'GlossHelper', 'GlossWord', 'GlossPost') if collation_row[gloss_part_name]]
            # word_list_string = ' '.join(gloss_list) # Space-separated list of English gloss words for that Greek word
            preformed_gloss_string = f"{'˱'+collation_row['GlossPre']+'˲ ' if collation_row['GlossPre'] else ''}{'˓'+collation_row['GlossHelper']+'˒ ' if collation_row['GlossHelper'] else ''}" \
                            f"{collation_row['GlossWord']}{' ‹'+collation_row['GlossPost']+'›' if collation_row['GlossPost'] else ''}"
            glossCapitalisationString = '' if collation_row['GlossCapitalization'] is None else collation_row['GlossCapitalization']
            if collation_row['Koine'].startswith( '=' ): # it's a nomina sacra
                assert 'N' not in glossCapitalisationString # already -- SR GNT doesn't currently use N -- see documentation of apply_gloss_capitalization() below
                glossCapitalisationString = f'{glossCapitalisationString}N' # We add an extra letter
            adjusted_lemma, preformed_gloss_string = process_untranslated_words( collation_row, preformed_gloss_string )
            medieval_lemma = '' if collation_row['LexemeID'] is None else find_lemma_forms(collation_row['LexemeID'], collation_row['Morphology'], collation_row['Classic'])[1]
            # medieval_lemma = '' if collation_row['LexemeID']=='99999' else lexeme_ID_lemma_dict[collation_row['LexemeID']]
            table_row = f"{ref}\t{collation_row['Medieval']}\t{adjusted_lemma}\t{medieval_lemma}\t{preformed_gloss_string}\t{glossCapitalisationString}\t{'' if collation_row['Probability'] is None else collation_row['Probability']}\t{collation_row['LexemeID']}\t{collation_row['Role']}\t{collation_row['Morphology']}"
            assert '"' not in table_row # Check in case we needed any escaping
            table_output_file.write( f'{table_row}\n' )
            # NOTE: The above code writes every table row, even for variants which aren't in the SR (but their probability column will be negative)
            # (That's probably the best all-round solution, as it's capable of covering the apparatus as well.)

    if esfm_text: # write the last book
        if write_gloss_esfm_book( last_book_number, esfm_text ):
            num_books_written += 1
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Wrote {num_books_written} books to {VLT_GLOSS_ESFM_OUTPUT_FOLDERPATH}.")

    # Now done in add_tags_to_NT_word_table.py
    # # Also use the same word file for the OET-RV
    # shutil.copy2( table_filepath, RV_ESFM_OUTPUT_FOLDERPATH.joinpath( table_filename ) )
    # vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"Also copied {table_filename} to {RV_ESFM_OUTPUT_FOLDERPATH}.")

    return True
# end of extract_VLT_NT_to_ESFM.export_esfm_literal_English_gloss


find_lemma_forms_lemma_index = {}
def find_lemma_forms(given_lexemeID:str, given_morphology:str, given_classic_word:str) -> Tuple[str,str]:
    """
    Using the word table
        and given the above two fields from the collation table,
        find the CNTR romanised lemma and the medieval form.
    """
    # print(f"find_lemma_forms( {given_lexemeID=}, {given_morphology=}, {given_classic_word=} )…")
    assert given_lexemeID.isdigit()
    assert given_morphology
    assert given_classic_word
    if not find_lemma_forms_lemma_index: # index the lemmas the first time
        # print( f"{word_csv_column_headers=}" )
        for word_row in word_csv_rows:
            # print( f"{word_row=}" )
            new_key = (word_row['LexemeID'],word_row['Morphology'],word_row['Classic'])
            assert new_key not in find_lemma_forms_lemma_index # Check for unexpected duplicates
            find_lemma_forms_lemma_index[new_key] = word_row['Lemma']
        print( f"    Created {len(find_lemma_forms_lemma_index)=:,}" )

    found_CNTR_lemma = find_lemma_forms_lemma_index[(given_lexemeID,given_morphology,given_classic_word)]
    found_medieval_lemma = lexemeID_CNTRLemma_dict[(given_lexemeID,found_CNTR_lemma)]
    # print( f"{given_lexemeID=} {given_morphology=} {given_classic_word=} --> {found_CNTR_lemma=} {found_medieval_lemma=}")
    return found_CNTR_lemma, found_medieval_lemma
# end of extract_VLT_NT_to_ESFM.find_lemma_forms


def adjust_lemma(given_lemma:str, given_Greek_word:str) -> str:
    """
    We need the actual Greek word as well
        because the rough breathing is not indicated on the given_lemma form.
    """
    # print(f"adjust_lemma({given_lemma=}, {given_Greek_word=})…")
    if not given_lemma or not given_Greek_word: return given_lemma

    adjusted_lemma = given_lemma.replace('h','ē').replace('w','ō').replace('q','th').replace('gg','ŋg').replace('y','ps').replace('c','χ') # .replace('f','ph')
    # Gloss word 'the' appears with 37 Greek words: {'τοὺς': 724, 'τὸν': 1247, 'ὁ': 1930, 'τῆς': 1006, 'τὴν': 1313,
    #       'αἱ': 130, 'τοῦ': 1720, 'ἡ': 813, 'τὸ': 1477, 'τῶν': 1158, 'τῇ': 690, 'τοῖς': 619, 'τὰ': 802, 'οἱ': 1029,
    #       'τὰς': 310, 'τῷ': 955, 'ταῖς': 177, 'τοῦς': 2, 'τόν': 4, 'τῶ': 1, 'τῆν': 1, 'τό': 5, 'τοὺ': 1, 'ἠ': 1,
    #       'τὴς': 2, 'οἳ': 4, 'του': 1, 'ἧ': 1, 'οἷ': 1, 'τὴ': 2, 'οἵ': 4, 'ᾧ': 1, 'τά': 2, 'ἥ': 3, 'τήν': 3, 'ὅ': 3, 'ἃ': 5}
    if given_lemma == 'o' \
    and given_Greek_word in ('ὁ','τοῦ','τὸ','τὸν','τῶν','τὴν','τῆς','οἱ','τῷ','τοὺς','ἡ','τῇ','τοῖς','τὰ','τὰς','αἱ','ταῖς','τοῦς','τό',
                'τόν','τῶ','τῆν','τοὺ','ἠ','τὴς','οἳ','του','ἧ','οἷ','τὴ','οἵ','ᾧ','τά','ἥ','τήν','ὅ','ἃ','αἵ'):
        adjusted_lemma = 'ho' # article
    elif given_lemma == 'os' \
    and given_Greek_word in ('ὃς','ὁ','ἃ','ἡ','οὓς','οἱ','οἳ','αἳ','ὅς','ἣ','ᾗ','ὃν','οἷς','αἱ','ὃ','ὅ','οἵ','οὖ','οὗ','οὑ'):
        adjusted_lemma = 'hos' # relative pronoun
    elif given_lemma == 'su' \
    and given_Greek_word in ('ὑμῖν','ὑμᾶς','ὑμῶν','ὑμεῖς'): # Don't want to wrongly carry across this rough breathing
        adjusted_lemma = 'su' # relative pronoun
    elif given_lemma == 'eis' \
    and given_Greek_word in ('μία','μίαν','μιᾶς','μιᾷ'):
        adjusted_lemma = 'heis' # 'one' not the preposition 'eis'
    elif given_Greek_word[0] in 'ἁἅἑἓἕἡἣἧἵὁὅὃὑὡὥὧᾧ' \
    or given_Greek_word.startswith('αἷ') \
    or given_Greek_word.startswith('εἷ') \
    or given_Greek_word.startswith('οἱ') or given_Greek_word.startswith('οἷ') \
    or given_Greek_word.startswith('οὓ') or given_Greek_word.startswith('οὗ') or given_Greek_word.startswith('οὕ') \
    or given_Greek_word.startswith('υἱ'):
        adjusted_lemma = f'h{adjusted_lemma}'
    elif given_Greek_word[0] in 'ἙἝὙ':
        adjusted_lemma = f'H{adjusted_lemma}'
    elif given_Greek_word[0] == 'ῥ' and adjusted_lemma.startswith('r'): # Don't understand ῥηθὲν,legw
        adjusted_lemma = adjusted_lemma.replace('r','rh',1)
    return adjusted_lemma
# end of adjust_lemma function


def process_untranslated_words( given_collation_row, given_preformed_gloss_string:str ) -> Tuple[str,str]:
    """
    """
    adjusted_preformed_gloss_string = given_preformed_gloss_string
    their_lemma,medieval_lemma = ('','') if given_collation_row['LexemeID'] is None else find_lemma_forms( given_collation_row['LexemeID'], given_collation_row['Morphology'], given_collation_row['Classic'] )
    adjusted_lemma = adjust_lemma( their_lemma, given_collation_row['Medieval'])
    if adjusted_preformed_gloss_string=='-' or adjusted_preformed_gloss_string.startswith( '-¦' ) or adjusted_preformed_gloss_string.startswith( '¶-¦' ): # an untranslated word from the VLT
        # NOTE: All of these new gloss strings also have to be entered into cleanupVLT.commandTable.tsv
        if adjusted_lemma == 'ho':
            # NOTE: Need to check for lowercase as well!
            # if given_collation_row['Morphology'].startswith( '····G' ): given_preformed_gloss_string = given_preformed_gloss_string.replace( '-', '¬of_the', 1 )
            # if given_collation_row['Morphology'].startswith( '····D' ): given_preformed_gloss_string = given_preformed_gloss_string.replace( '-', '¬to/from_the', 1 )
            if given_collation_row['Role'] == 'R':
                adjusted_preformed_gloss_string = adjusted_preformed_gloss_string.replace( '-', '¬which', 1 )
            else:
                adjusted_preformed_gloss_string = adjusted_preformed_gloss_string.replace( '-', '¬the', 1 )
        elif adjusted_lemma == 'hoti': adjusted_preformed_gloss_string = adjusted_preformed_gloss_string.replace( '-', '¬that', 1 )
        elif adjusted_lemma in ('ean','ei'): adjusted_preformed_gloss_string = adjusted_preformed_gloss_string.replace( '-', '¬if', 1 ) # Strongs #1437, #1487
        elif adjusted_lemma == 'an': adjusted_preformed_gloss_string = adjusted_preformed_gloss_string.replace( '-', '¬wishfully', 1 ) # Strongs #302
        elif adjusted_lemma == 'mē': adjusted_preformed_gloss_string = adjusted_preformed_gloss_string.replace( '-', '¬not/lest', 1 )
        elif adjusted_lemma == 'ē': adjusted_preformed_gloss_string = adjusted_preformed_gloss_string.replace( '-', '¬or/than', 1 ) # Strongs #2228
        elif adjusted_lemma == 'hos': adjusted_preformed_gloss_string = adjusted_preformed_gloss_string.replace( '-', '¬who/which/what/that', 1 ) # Strongs #3739
        elif adjusted_lemma == 'ou': adjusted_preformed_gloss_string = adjusted_preformed_gloss_string.replace( '-', '¬no/not', 1 ) # Strongs #3756
        elif adjusted_lemma == 'kata': adjusted_preformed_gloss_string = adjusted_preformed_gloss_string.replace( '-', '¬down/against/according_to', 1 ) # Strongs #2596
        elif adjusted_lemma == 'te': adjusted_preformed_gloss_string = adjusted_preformed_gloss_string.replace( '-', '¬and/both', 1 ) # Strongs #5037
        elif adjusted_lemma == 'ara': adjusted_preformed_gloss_string = adjusted_preformed_gloss_string.replace( '-', '¬/anxiety/', 1 ) # Strongs #687 (only occurs once)
        elif adjusted_lemma == 'mēte': adjusted_preformed_gloss_string = adjusted_preformed_gloss_string.replace( '-', '¬neither/nor', 1 ) # Strongs #3383 (only occurs once)
        else: print( f"      What is untranslated word from '{adjusted_preformed_gloss_string}' and '{adjusted_lemma}' in {given_collation_row['CollationID']} {given_collation_row['Medieval']} {adjusted_lemma} {given_collation_row['Morphology']}?" )

    # The problem is that capitalization has already been applied
    if adjusted_preformed_gloss_string != given_preformed_gloss_string:
        # Let's try capitalizing again
        _, _, adjusted_preformed_gloss_string = apply_gloss_capitalization( '', '', adjusted_preformed_gloss_string, given_collation_row['GlossCapitalization'] )
        # if '134824' in given_preformed_gloss_string: print( f"{given_preformed_gloss_string=} {given_collation_row['GlossCapitalization']=} {adjusted_preformed_gloss_string=}" ); halt

    return adjusted_lemma, adjusted_preformed_gloss_string
# end of process_untranslated_words function


def get_verse_rows(given_collation_rows: List[dict], row_index: int) -> List[list]:
    """
    row_index should be the index of the first row for the particular verse

    Returns a list of rows for the verse
    """
    # vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"get_verse_rows({row_index})")
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
# end of extract_VLT_NT_to_ESFM.get_verse_rows


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
        vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"ERROR: Verse rows for {given_verse_row_list[0]['VerseID']} have duplicate GlossOrder fields!")
        for some_row in given_verse_row_list:
            vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  {some_row['CollationID']} {some_row['VariantID']} {some_row['Align']} '{some_row['Koine']}' '{some_row['GlossWord']}' {some_row['GlossOrder']} Role={some_row['Role']} Syntax={some_row['Syntax']}")
        if stop_on_error: gloss_order_fields_for_verse_are_not_unique
# end of extract_VLT_NT_to_ESFM.check_verse_rows


def get_gloss_word_index_list(given_verse_row_list: List[dict]) -> List[List[int]]:
    """
    Goes through the verse rows in gloss word order and produces a list of lists of row indexes
        Most entries only contain one index (for one gloss word)
        If GlossInsert is set, some contain multiple indexes for the overlapping gloss words

    Returns a list of lists of relative word numbers.
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
    # vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"get_gloss_word_index_list for {verse_id} is got: ({len(base_gloss_display_order_list)}) {base_gloss_display_order_list}")

    these_words_base_display_index_list, result_list = [], []
    for n, index in enumerate( base_gloss_display_order_list ):
        these_words_base_display_index_list.append(index)
        try: gloss_insert_char = given_verse_row_list[index]['GlossInsert']
        except KeyError: gloss_insert_char = None # it's not in Alan's tables yet
        if not gloss_insert_char \
        or gloss_insert_char in SOLO_GLOSS_INSERT_CHARACTERS: # We have a word or word set to add to the result
            result_list.append(these_words_base_display_index_list)
            these_words_base_display_index_list = []
    if these_words_base_display_index_list:
        vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"Why did get_gloss_word_index_list() for {given_verse_row_list[0]['VerseID']} ({len(given_verse_row_list)} rows)"
              f" have left-over words: ({len(these_words_base_display_index_list)}) {these_words_base_display_index_list}"
              f" from glossInserts: {[row['GlossInsert'] for row in given_verse_row_list]}")
    assert not these_words_base_display_index_list # at end of loop
    # dPrint( 'Normal', DEBUGGING_THIS_MODULE, f"get_gloss_word_index_list for {verse_id} is returning: ({len(result_list)}) {result_list}"); halt
    return result_list
# end of extract_VLT_NT_to_ESFM.get_gloss_word_index_list


def preform_gloss_and_word_number(thisList:List[Dict[str,str]], given_verse_row_index:int, last_given_verse_row_index:int=None, last_glossWord:Optional[str]=None, row_offset:Optional[int]=None) -> str:
    """
    Returns the gloss to display for this row (may be nothing if we have a current GlossInsert)
        or the left-over preformatted GlossWord (if any)
    The calling function has to decide what to do with it.

    If start_row_index is given, it appends the collation row number to each word.

    Returns the preformed gloss string.
    """
    assert isinstance( thisList, list )
    assert isinstance( given_verse_row_index, int )
    if last_given_verse_row_index is not None: assert isinstance( last_given_verse_row_index, int )
    if last_glossWord is not None: assert isinstance( last_glossWord, str )
    if row_offset is not None: assert isinstance( row_offset, int )

    given_verse_row = thisList[given_verse_row_index]
    dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"preform_gloss({given_verse_row['GlossPre']}"
                        f".{given_verse_row['GlossHelper']}.{given_verse_row['GlossWord']}"
                        f".{given_verse_row['GlossPost']}, {last_glossWord=})…")
    try:
        last_given_verse_row = thisList[last_given_verse_row_index]
        last_glossInsert = last_given_verse_row['GlossInsert']
    except (TypeError, KeyError): last_glossInsert = '' # last row not given
    last_pre_punctuation = last_post_punctuation = ''
    if last_glossInsert:
        last_pre_punctuation, last_post_punctuation = separate_punctuation(last_given_verse_row['GlossPunctuation'])
        last_glossCapitalization = last_given_verse_row['GlossCapitalization']
        dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"  {last_glossInsert=}" )

    glossPre, glossHelper, glossWord, glossPost, glossPunctuation, glossCapitalization \
        = given_verse_row['GlossPre'], given_verse_row['GlossHelper'], given_verse_row['GlossWord'], given_verse_row['GlossPost'], given_verse_row['GlossPunctuation'], given_verse_row['GlossCapitalization']
    # if glossWord == '-':
    #     glossWord = '-the-' # We want to know when potential articles are just dropped (i.e., considered as pure case markers)
    # Table encoding seems to have changed
    if glossPunctuation is None: glossPunctuation = ''
    if glossCapitalization is None: glossCapitalization = ''
    if row_offset is not None:
        this_row_offset = row_offset + given_verse_row_index + 1
        # Put in the ESFM wordlink row numbers
        # NOTE: These are appended to each gloss word part, as well as to each part that's separated by an underline
        if glossPre: glossPre = f"{glossPre.replace('_',f'¦{this_row_offset}_')}¦{this_row_offset}"
        if glossHelper: glossHelper = f"{glossHelper.replace('_',f'¦{this_row_offset}_')}¦{this_row_offset}"
        assert glossWord
        glossWord = f"{glossWord.replace('_',f'¦{this_row_offset}_')}¦{this_row_offset}"
        if glossPost: glossPost = f"{glossPost.replace('_',f'¦{this_row_offset}_')}¦{this_row_offset}"

    try: glossInsert = given_verse_row['GlossInsert']
    except KeyError: glossInsert = '' # it's not in Alan's tables yet
    if given_verse_row['Koine'].startswith( '=' ): # it's a nomina sacra
        assert '\\nd' not in glossWord
        glossWord = f"\\nd {glossWord}\\nd*" # we use the USFM divine name style
    pre_punctuation, post_punctuation = separate_punctuation(glossPunctuation)
    assert '*' not in post_punctuation

    # These first ones are different cases coz they all work internally on a single row
    if glossInsert == '~' and not last_glossInsert:
        # Put GlossPre inside GlossHelper
        assert glossPre
        assert '_' in glossHelper
        glossHelper, glossPre, glossWord = apply_gloss_capitalization(glossHelper, glossPre, glossWord, glossCapitalization)
        glossHelper_bits = glossHelper.split('_', 1)
        preformed_word_string = f"{last_glossWord+' ' if last_glossWord else ''}" \
                            f"{pre_punctuation}˓{glossHelper_bits[0]}˒_˱{glossPre}˲_˓{glossHelper_bits[1]}˒_" \
                            f"{glossWord}{' '+BACKSLASH+'add '+glossPost+BACKSLASH+'add*' if glossPost else ''}{post_punctuation}"
    elif glossInsert == '@' and not last_glossInsert:
        # Put GlossPre inside GlossWord
        assert glossPre
        assert '_' in glossWord
        _, _, glossWord = apply_gloss_capitalization('', '', glossWord, glossCapitalization)
        glossWord_bits = glossWord.split('_', 1)
        preformed_word_string = f"{last_glossWord+' ' if last_glossWord else ''}" \
                                f"{pre_punctuation}{'˓'+glossHelper+'˒ ' if glossHelper else ''}" \
                                f"{glossWord_bits[0]}_ ˱{glossPre}˲ _{glossWord_bits[1]}" \
                                f"{' '+BACKSLASH+'add '+glossPost+BACKSLASH+'add*' if glossPost else ''}{post_punctuation}"
    elif glossInsert == '?' and not last_glossInsert:
        # Swap GlossPre and GlossHelper
        assert glossPre
        assert glossHelper
        # assert ' ' not in glossHelper
        glossHelper, glossPre, glossWord = apply_gloss_capitalization(glossHelper, glossPre, glossWord, glossCapitalization)
        preformed_word_string = f"{last_glossWord+' ' if last_glossWord else ''}" \
                                f"{pre_punctuation}˓{glossHelper}˒_˱{glossPre}˲_" \
                                f"{glossWord}{' '+BACKSLASH+'add '+glossPost+BACKSLASH+'add*' if glossPost else ''}{post_punctuation}"
    elif glossInsert == '&' and not last_glossInsert:
        # Swap GlossWord and GlossPost
        assert glossPost
        glossPre, glossHelper, glossWord = apply_gloss_capitalization(glossPre, glossHelper, glossWord, glossCapitalization)
        preformed_word_string = f"{last_glossWord+' ' if last_glossWord else ''}" \
                                f"{pre_punctuation}{'˱'+glossPre+'˲_' if glossPre else ''}{'˓'+glossHelper+'˒_' if glossHelper else ''}" \
                                f"\\add {glossPost}\\add* {glossWord}{post_punctuation}"
    elif glossInsert == '!' and not last_glossInsert:
        # Insert GlossPost into GlossWord
        assert glossPost
        assert '_' in glossWord
        glossPre, glossHelper, glossWord = apply_gloss_capitalization(glossPre, glossHelper, glossWord, glossCapitalization)
        glossWord_bits = glossWord.split('_', 1)
        preformed_word_string = f"{last_glossWord+' ' if last_glossWord else ''}" \
                                f"{pre_punctuation}{'˱'+glossPre+'˲_' if glossPre else ''}{'˓'+glossHelper+'˒_' if glossHelper else ''}" \
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
                                f"{pre_punctuation}{glossWord}_˓{glossHelper}˒{post_punctuation}"
        elif not glossPre and not glossHelper and glossPost:
            # Swap GlossWord and GlossPost
            glossPost, glossHelper, glossWord = apply_gloss_capitalization(glossPost, glossHelper, glossWord, glossCapitalization)
            preformed_word_string = f"{last_glossWord+' ' if last_glossWord else ''}" \
                                f"{pre_punctuation}\\add {glossPost}\\add* {glossWord}{post_punctuation}"
        else: raise Exception("bad_2_gloss_insert")

    elif last_glossInsert and last_glossInsert not in SOLO_GLOSS_INSERT_CHARACTERS and not glossInsert:
        # vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"Here with {last_pre_punctuation=} {pre_punctuation=} {last_glossWord=}")
        if last_pre_punctuation and last_glossWord.startswith(last_pre_punctuation):
            last_glossWord = last_glossWord[len(last_pre_punctuation):] # Remove the pre-punctuation off the inserted word
        if pre_punctuation != last_pre_punctuation:
            pre_punctuation = f'{last_pre_punctuation}{pre_punctuation}'
        if last_glossInsert == '<': # insert after pre
            assert last_glossWord
            assert glossPre, f"Expected glossPre after '<' at {given_verse_row_index} with {given_verse_row}"
            glossPre, _dummyHelper, last_glossWord = apply_gloss_capitalization(glossPre, '', last_glossWord, last_glossCapitalization)
            _dummyPre, glossHelper, glossWord = apply_gloss_capitalization('', glossHelper, glossWord, glossCapitalization)
            preformed_word_string = f"{pre_punctuation}˱{glossPre}˲_> {last_glossWord} <_{'˓'+glossHelper+'˒_' if glossHelper else ''}" \
                                    f"{glossWord}{' '+BACKSLASH+'add '+glossPost+BACKSLASH+'add*' if glossPost else ''}{post_punctuation}"
            last_glossWord = ''
        elif last_glossInsert == '=': # insert after helper and before word
            assert last_glossWord
            assert glossHelper, given_verse_row
            # vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"Here with {last_glossCapitalization=} {last_glossWord=} {glossCapitalization=} {glossPre=} {glossHelper=} {glossWord=}")
            glossPre, glossHelper, last_glossWord = apply_gloss_capitalization(glossPre, glossHelper, last_glossWord, last_glossCapitalization)
            _dummyPre, _dummyHelper, glossWord = apply_gloss_capitalization('', '', glossWord, glossCapitalization)
            preformed_word_string = f"{pre_punctuation}{'˱'+glossPre+'˲_' if glossPre else ''}˓{glossHelper}˒_=> " \
                                    f"{last_glossWord} <=_{glossWord}{' '+BACKSLASH+'add '+glossPost+BACKSLASH+'add*' if glossPost else ''}{post_punctuation}"
            last_glossWord = ''
        elif last_glossInsert == '-': # insert inside helper parts
            assert last_glossWord
            glossPre, glossHelper, last_glossWord = apply_gloss_capitalization(glossPre, glossHelper, last_glossWord, last_glossCapitalization)
            _dummyPre, _dummyHelper, glossWord = apply_gloss_capitalization('', '', glossWord, glossCapitalization)
            if '_' in glossHelper:
                glossHelper_bits = glossHelper.split('_', 1)
            else:
                vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Warning: Can't insert '{last_glossWord}' at underline in '{glossHelper}' at {given_verse_row['CollationID']}")
                glossHelper_bits = glossHelper, ''
            preformed_word_string = f"{pre_punctuation}{'˱'+glossPre+'˲_' if glossPre else ''}˓{glossHelper_bits[0]}˒_ {last_glossWord} _˓{glossHelper_bits[1]}˒_" \
                                    f"{glossWord}{' '+BACKSLASH+'add '+glossPost+BACKSLASH+'add*' if glossPost else ''}{post_punctuation}"
            last_glossWord = ''
        elif last_glossInsert == '_': # insert inside word parts
            assert last_glossWord
            # if glossWord.count('_') > 1:
            #     vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Warning: Inserting '{last_glossWord}' at first underline in '{glossWord}' but has {glossWord.count('_')} '_' characters")
            glossPre, glossHelper, last_glossWord = apply_gloss_capitalization(glossPre, glossHelper, last_glossWord, last_glossCapitalization)
            _dummyPre, _dummyHelper, glossWord = apply_gloss_capitalization('', '', glossWord, glossCapitalization)
            glossWord_bits = glossWord.split('_', 1)
            preformed_word_string = f"{pre_punctuation}{'˱'+glossPre+'˲_' if glossPre else ''}{'˓'+glossHelper+'˒_' if glossHelper else ''}" \
                                    f"{glossWord_bits[0]}_ {last_glossWord} _{glossWord_bits[1]}{' '+BACKSLASH+'add '+glossPost+BACKSLASH+'add*' if glossPost else ''}{post_punctuation}"
            last_glossWord = ''
        elif last_glossInsert == '>': # insert after word and before post
            assert last_glossWord
            assert glossPost
            glossPre, glossHelper, last_glossWord = apply_gloss_capitalization(glossPre, glossHelper, last_glossWord, last_glossCapitalization)
            _dummyPre, _dummyHelper, glossWord = apply_gloss_capitalization('', '', glossWord, glossCapitalization)
            preformed_word_string = f"{pre_punctuation}{'˱'+glossPre+'˲_' if glossPre else ''}{'˓'+glossHelper+'˒_' if glossHelper else ''}" \
                                    f"{glossWord}_> {last_glossWord} <_\\add {glossPost}\\add*{post_punctuation}"
            last_glossWord = ''
        else:
            vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Warning: Unexpected GlossInsert = '{last_glossInsert}' (ignored) {thisList=} {given_verse_row_index=}")
    else:
        if glossInsert and last_glossInsert and glossInsert != last_glossInsert:
            msg = f"ERROR: preform_gloss() for {given_verse_row['CollationID']} should not have {glossInsert=} but '{last_glossInsert}'"
            vPrint( 'Normal', DEBUGGING_THIS_MODULE, msg)
            last_glossWord = f'{msg} {last_glossWord}' # Also insert the error into the returned text so it gets noticed
        if not glossInsert: # (If we do have glossInsert, leave the capitalization for the next round)
            glossPre, glossHelper, glossWord = apply_gloss_capitalization(glossPre, glossHelper, glossWord, glossCapitalization)
        preformed_word_string = f"{pre_punctuation}{last_glossWord+' ' if last_glossWord else ''}{'˱'+glossPre+'˲_' if glossPre else ''}{'˓'+glossHelper+'˒_' if glossHelper else ''}" \
                            f"{glossWord}{' '+BACKSLASH+'add '+glossPost+BACKSLASH+'add*' if glossPost else ''}{post_punctuation}"
    preformed_result_string = preformed_word_string # f"{preformed_word_string}"
    assert not preformed_result_string.startswith(' '), preformed_result_string
    assert '  ' not in preformed_result_string, preformed_result_string
    # vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  returning '{preformed_result_string}'")
    return preformed_result_string
# end of extract_VLT_NT_to_ESFM.preform_gloss


def separate_punctuation(given_punctuation:str) -> Tuple[str,str]:
    """
    Take a combination punctuation string and converts it into pre and post punctuation characters.
    """
    # fnPrint( DEBUGGING_THIS_MODULE, f"separate_punctuation({given_punctuation})" )
    pre_punctuation = post_punctuation = ''
    if given_punctuation:
        assert 'None' not in given_punctuation and 'NULL' not in given_punctuation, f"{given_punctuation=}"
        if given_punctuation not in ('.”’”','[[',']]',):
            for char in given_punctuation:
                if given_punctuation.count(char) > 1:
                    logging.warning( f"Have duplicated '{char}' punctuation character(s) in '{given_punctuation}'." )
        improved_given_punctuation = given_punctuation \
                                        .replace(',,',',').replace('..','.').replace('”“','”')
        if improved_given_punctuation not in ('.”’”','[[',']]',):
            for char in improved_given_punctuation:
                if improved_given_punctuation.count(char) > 1:
                    logging.critical( f"Still have duplicated '{char}' punctuation character(s) in '{improved_given_punctuation}'." )

        temporary_copied_punctuation = improved_given_punctuation
        while temporary_copied_punctuation:
            if temporary_copied_punctuation[0] in PRE_WORD_PUNCTUATION_LIST:
                pre_punctuation += temporary_copied_punctuation[0]
                temporary_copied_punctuation = temporary_copied_punctuation[1:]
            elif temporary_copied_punctuation[-1] in ENGLISH_POST_WORD_PUNCTUATION_LIST_STRING:
                post_punctuation = f'{temporary_copied_punctuation[-1]}{post_punctuation}'
                temporary_copied_punctuation = temporary_copied_punctuation[:-1]
            else:
                vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"ERROR: punctuation character(s) '{temporary_copied_punctuation}' is not handled yet! ({given_punctuation=})")
                if __name__ == "__main__": stop_right_here
                break
        if __name__ == "__main__": # don't want this to fail when in the gloss editor
            assert f'{pre_punctuation}{post_punctuation}' == improved_given_punctuation
    return pre_punctuation, post_punctuation
# end of extract_VLT_NT_to_ESFM.separate_punctuation


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
    def capitalize_it( something:str ) -> str:
        if something[0] == '¶':
            assert something[1] != ' ', f"{something=}"
            if something[1] == '¬':
                something = f'¶¬{something[2].upper()}{something[3:]}' # Those are WORD punctuation characters
                # print( f"{something=}"); halt
            else:
                something = f'¶{something[1].upper()}{something[2:]}' # Those are WORD punctuation characters
                # print( f"{gloss_word=}"); halt
        elif something[0] == '¬':
            something = f'¬{something[1].upper()}{something[2:]}' # Those are WORD punctuation characters
            # print( f"{gloss_word=}"); halt
        else:
            something = f'{something[0].upper()}{something[1:]}' # Those are WORD punctuation characters
        assert '¬the' not in something
        return something

    if gloss_capitalization:
        if gloss_capitalization.lower() != gloss_capitalization: # there's some UPPERCASE values
            # NOTE: We can't use the title() function here for capitalising or else words like 'you_all' become 'You_All'
            if 'G' in gloss_capitalization or 'U' in gloss_capitalization or 'W' in gloss_capitalization:
                gloss_word = capitalize_it( gloss_word )
            if ('P' in gloss_capitalization or 'S' in gloss_capitalization # new paragraph or sentence
            or 'B' in gloss_capitalization # new Biblical quotation
            or 'D' in gloss_capitalization # new dialog
            or 'T' in gloss_capitalization # translated words
            or 'R' in gloss_capitalization): # other quotation, e.g., writing on board over cross
                if gloss_pre: gloss_pre = capitalize_it( gloss_pre )
                elif gloss_helper: gloss_helper = capitalize_it( gloss_helper )
                else: gloss_word = capitalize_it( gloss_word )

    # assert '134824' not in  gloss_pre and '134824' not in gloss_helper and '134824' not in gloss_word, f"{gloss_pre=} {gloss_helper=} {gloss_word=} {gloss_capitalization=}"
    return gloss_pre, gloss_helper, gloss_word
# end of extract_VLT_NT_to_ESFM.apply_gloss_capitalization



if __name__ == '__main__':
    # from multiprocessing import freeze_support
    # freeze_support() # Multiprocessing support for frozen Windows executables

    # Configure basic Bible Organisational System (BOS) set-up
    parser = BibleOrgSysGlobals.setup( SHORT_PROGRAM_NAME, PROGRAM_VERSION, LAST_MODIFIED_DATE )
    BibleOrgSysGlobals.addStandardOptionsAndProcess( parser )

    main()

    BibleOrgSysGlobals.closedown( PROGRAM_NAME, PROGRAM_VERSION )
# end of extract_VLT_NT_to_ESFM.py
