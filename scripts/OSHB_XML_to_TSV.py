#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# OSHB_XML_to_TSV.py
#
# Script handling OSHB_XML_to_TSV functions
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
Script extracting the data out of the OSHB XML files
    and putting them into a single TSV table and also a JSON file.
"""
from gettext import gettext as _
from typing import Dict, List, Tuple
from pathlib import Path
from csv import DictWriter
from datetime import datetime
from xml.etree import ElementTree
import json
import logging

import BibleOrgSysGlobals
from BibleOrgSysGlobals import fnPrint, vPrint, dPrint


LAST_MODIFIED_DATE = '2022-09-24' # by RJH
SHORT_PROGRAM_NAME = "OSHB_XML_to_TSV"
PROGRAM_NAME = "Extract OSHB WLC XML into a TSV file"
PROGRAM_VERSION = '0.50'
PROGRAM_NAME_VERSION = f'{SHORT_PROGRAM_NAME} v{PROGRAM_VERSION}'

DEBUGGING_THIS_MODULE = True


BREAK_MORPHEMES = True
OSHB_XML_INPUT_FOLDERPATH = Path( '../../Forked/OS-morphhb/wlc/' )
OSHB_TSV_OUTPUT_FILEPATH_STRING = '../../OpenEnglishTranslation--OET/sourceTexts/rawOSHB/OSHB.original.tsv' # str so we can adjust it later
OSHB_JSON_OUTPUT_FILEPATH_STRING = '../../OpenEnglishTranslation--OET/sourceTexts/rawOSHB/OSHB.original.json'


state = None
class State:
    def __init__( self ) -> None:
        """
        Constructor:
        """
        self.OSHB_XML_input_folderpath = OSHB_XML_INPUT_FOLDERPATH
        self.sourceTableFilepath = Path( '../../CNTR-GNT/sourceExports/collation.updated.csv' )
    # end of OSHB_XML_to_TSV.__init__


NEWLINE = '\n'
BACKSLASH = '\\'


def main() -> None:
    """
    Load, refactor, check, and finally export the WLC data.
    """
    BibleOrgSysGlobals.introduceProgram( __name__, PROGRAM_NAME_VERSION, LAST_MODIFIED_DATE )
    global state
    state = State()

    if load_OSHB_XML() and adjust_data_table():
        export_table_to_files()
# end of OSHB_XML_to_TSV.main


def load_OSHB_XML() -> bool:
    """
    Loads data from the XML files for all 39 WLC OT books
    """
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"\nLoading OSHB XML files from {state.OSHB_XML_input_folderpath}…" )

    state.books_array, state.flat_array = [], []
    for BBB in BibleOrgSysGlobals.loadedBibleBooksCodes:
        if BibleOrgSysGlobals.loadedBibleBooksCodes.isOldTestament_NR( BBB ):
            nested_chapter_array = load_OSHB_XML_bookfile( BBB )
            if nested_chapter_array is None:
                logging.critical( f"load_OSHB_XML() aborted after {BBB}!" )
                return False
            state.books_array.append( nested_chapter_array )

    print(f"  Loaded {len(state.flat_array):,} total data rows{' (with breaks at morphemes)' if BREAK_MORPHEMES else ''}.")

    return True
# end of OSHB_XML_to_TSV.load_OSHB_XML


def load_OSHB_XML_bookfile( BBB:str ) -> list:
    """
    Loads data from the XML file for a single WLC OT book
    """
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Loading {BBB} OSHB XML file…" )

    nn = BibleOrgSysGlobals.loadedBibleBooksCodes.getReferenceNumber( BBB )
    assert nn < 100
    osis_book_code = BibleOrgSysGlobals.loadedBibleBooksCodes.getOSISAbbreviation( BBB )
    filename = f'{osis_book_code}.xml'

    # Adapted from https://github.com/Freely-Given-org/OS-morphhb/blob/master/morphhbXML-to-JSON.py
    tree = ElementTree.parse( state.OSHB_XML_input_folderpath.joinpath( filename ) )
    namespaces = { 'osis': 'http://www.bibletechnologies.net/2003/OSIS/namespace' }

    chapters = tree.getroot().findall('.//osis:chapter', namespaces)
    chapter_array = []
    for chapter in chapters:
        C = len(chapter_array) + 1
        assert C < 1000
        verses = chapter.findall('.//osis:verse', namespaces)
        verseArray = []
        for verse in verses:
            V = len(verseArray)+1
            assert V < 1000
            verse_element_array = []
            for j,verse_element in enumerate( verse, start=1 ):
                assert j < 100
                numeric_ref = f"{str(nn).zfill(2)}{str(C).zfill(3)}{str(V).zfill(3)}{str(j).zfill(2)}"
                readable_ref = f'{BBB}_{C}:{V}-{j}'

                if verse_element.tag == f"{{{namespaces['osis']}}}w":

                    lemma = verse_element.attrib.get('lemma')
                    n = verse_element.attrib.get('n')
                    morph = verse_element.attrib.get('morph')
                    OS_id = verse_element.attrib.get('id')
                    word = verse_element.text
                    wc, lc, mc = word.count('/'), lemma.count('/'), morph.count('/')
                    assert wc == mc, f"{readable_ref} {word=} {morph=} {lemma=}"
                    if lc != wc:
                        logger = logging.warning if lc==wc-1 else logging.critical
                        logger( f"{readable_ref} ({wc+1} parts) {word=} {morph=} ({lc+1} parts) {lemma=}" )

                    if BREAK_MORPHEMES:
                        # NOTE: There may be a different number of lemma bits --
                        #           frequently one less (for possessive pronoun at end of word)
                        max_slash_count = max( wc, lc, mc )
                        if max_slash_count == 0: # no components (separated by /)
                            verse_element_array.append([readable_ref, 'w', lemma, n, morph, OS_id, word])
                            state.flat_array.append([numeric_ref, readable_ref, 'w', lemma, n, morph, OS_id, word])
                        else: # there's multiple morphemes
                            letterDict = { 0:'a', 1:'b', 2:'c', 3:'d', 4:'e' }
                            word_bits, morph_bits, lemma_bits = word.split('/'), morph.split('/'), lemma.split('/')
                            for q in range( max_slash_count+1 ):
                                letter = letterDict[q]
                                try: word_bit = word_bits[q]
                                except IndexError: word_bit = ''
                                try: morph_bit = morph_bits[q]
                                except IndexError: morph_bit = ''
                                try: lemma_bit = lemma_bits[q]
                                except IndexError: lemma_bit = ''
                                adj_numeric_ref = f'{numeric_ref}{letter}'
                                adj_readable_ref = f'{readable_ref}{letter}'
                                adj_id = f'{OS_id}{letter}'
                                verse_element_array.append([adj_readable_ref, 'm', lemma_bit, n, morph_bit, adj_id, word_bit])
                                state.flat_array.append([adj_numeric_ref, adj_readable_ref, 'm', lemma_bit, n, morph_bit, adj_id, word_bit])
                    else: # it's simple
                        verse_element_array.append([readable_ref, 'w', lemma, n, morph, OS_id, word])
                        state.flat_array.append([numeric_ref, readable_ref, 'w', lemma, n, morph, OS_id, word])

                elif verse_element.tag == f"{{{namespaces['osis']}}}seg":
                    seg_type = verse_element.attrib.get('type')
                    verse_element_array.append([readable_ref, 'seg', seg_type, verse_element.text])
                    state.flat_array.append([numeric_ref, readable_ref, 'seg', seg_type, '','','', verse_element.text])

                elif verse_element.tag == f"{{{namespaces['osis']}}}note":
                    n = verse_element.attrib.get('n')
                    verse_element_array.append([readable_ref, 'note', n, verse_element.text])
                    state.flat_array.append([numeric_ref, readable_ref, 'note', n, verse_element.text])

                else:
                    logging.critical( f"Unknown verse element at {readable_ref}: {verse_element.tag}")
                    halt
            verseArray.append(verse_element_array)
        chapter_array.append(verseArray)

    vPrint( 'Info', DEBUGGING_THIS_MODULE, f"    Loaded {len(chapter_array):,} XML chapters." )

    return chapter_array
# end of OSHB_XML_to_TSV.load_OSHB_XML_bookfile


def adjust_data_table() -> bool:
    """
    """
    return True
# end of OSHB_XML_to_TSV.adjust_data_table


def export_table_to_files() -> bool:
    """
    Use state.flat_array to export the TSV and JSON.
    """
    OSHB_TSV_output_filepath = Path( OSHB_TSV_OUTPUT_FILEPATH_STRING.replace( '.original.', '.original.flat.morphemes.' )
                if BREAK_MORPHEMES else OSHB_TSV_OUTPUT_FILEPATH_STRING.replace( '.original.', '.original.flat.words.' ) )
    print( f"Exporting WLC table as a single flat TSV file to {OSHB_TSV_output_filepath}…" )
    fieldnames = ['FGID','Ref','Type','Strongs','n','Morphology','OSHBid','Morpheme' if BREAK_MORPHEMES else 'Word']
    with open( OSHB_TSV_output_filepath, 'wt', encoding='utf-8' ) as tsv_output_file:
        tsv_output_file.write('\ufeff') # Write BOM
        writer = DictWriter( tsv_output_file, fieldnames=fieldnames, delimiter='\t' )
        writer.writeheader()
        for row in state.flat_array:
            rowDict = {k:v for k,v in zip(fieldnames,row)}
            writer.writerow( rowDict )

    OSHB_JSON_output_filepath = Path( OSHB_JSON_OUTPUT_FILEPATH_STRING.replace( '.original.', '.original.flat.morphemes.' )
                if BREAK_MORPHEMES else OSHB_JSON_OUTPUT_FILEPATH_STRING.replace( '.original.', '.original.flat.words.' ) )
    print( f"Exporting WLC table as a single flat JSON file to {OSHB_JSON_output_filepath}…" )
    with open( OSHB_JSON_output_filepath, 'wt', encoding='utf-8' ) as json_output_file:
        json.dump( state.flat_array, json_output_file, indent=2 )
    OSHB_JSON_output_filepath = Path( OSHB_JSON_OUTPUT_FILEPATH_STRING.replace( '.original.', '.original.nested.morphemes.' )
                if BREAK_MORPHEMES else OSHB_JSON_OUTPUT_FILEPATH_STRING.replace( '.original.', '.original.nested.words.' ) )
    print( f"Exporting WLC table as a single nested book/chapter/verse JSON file to {OSHB_JSON_output_filepath}…" )
    with open( OSHB_JSON_output_filepath, 'wt', encoding='utf-8' ) as json_output_file:
        json.dump( state.books_array, json_output_file, indent=2 )

    return True
# end of OSHB_XML_to_TSV.export_table_to_files


if __name__ == '__main__':
    # from multiprocessing import freeze_support
    # freeze_support() # Multiprocessing support for frozen Windows executables

    # Configure basic Bible Organisational System (BOS) set-up
    parser = BibleOrgSysGlobals.setup( SHORT_PROGRAM_NAME, PROGRAM_VERSION, LAST_MODIFIED_DATE )
    BibleOrgSysGlobals.addStandardOptionsAndProcess( parser )

    main()

    BibleOrgSysGlobals.closedown( PROGRAM_NAME, PROGRAM_VERSION )
# end of OSHB_XML_to_TSV.py
