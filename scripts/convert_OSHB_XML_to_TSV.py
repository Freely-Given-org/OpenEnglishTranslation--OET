#!/usr/bin/env python3
# -\*- coding: utf-8 -\*-
# SPDX-License-Identifier: GPL-3.0-or-later
#
# convert_OSHB_XML_to_TSV.py
#
# Script handling convert_OSHB_XML_to_TSV function
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
Script extracting the data out of the OSHB XML files
    and putting them into a single TSV table and also a JSON file.

(This is run BEFORE prepare_OSHB_for_glossing.py.)

OSHB morphology codes can be found at https://hb.openscriptures.org/parsing/HebrewMorphologyCodes.html.

CHANGELOG:
    2025-01-15 Fix the single note that contains an exclamation mark ('KJV:1Kgs.22.43!b')
    2025-06-26 Fix the notes that contain a superfluous trailing space.
"""
from gettext import gettext as _
# from typing import Dict, List, Tuple
from pathlib import Path
from csv import DictWriter
from xml.etree import ElementTree
import json
import logging

import BibleOrgSysGlobals
from BibleOrgSysGlobals import fnPrint, vPrint, dPrint


LAST_MODIFIED_DATE = '2025-06-26' # by RJH
SHORT_PROGRAM_NAME = "Convert_OSHB_XML_to_TSV"
PROGRAM_NAME = "Convert OSHB WLC OT XML into TSV/JSON files"
PROGRAM_VERSION = '0.60'
PROGRAM_NAME_VERSION = f'{SHORT_PROGRAM_NAME} v{PROGRAM_VERSION}'

DEBUGGING_THIS_MODULE = False


BREAK_MORPHEMES = True
OSHB_XML_INPUT_FOLDERPATH = Path( '../../Forked/OS-morphhb/wlc/' )
OSHB_TSV_OUTPUT_FILEPATH_STRING = '../../OpenEnglishTranslation--OET/sourceTexts/rawOSHB/OSHB.parsedOriginal.tsv' # str so we can adjust it later
OSHB_JSON_OUTPUT_FILEPATH_STRING = '../../OpenEnglishTranslation--OET/sourceTexts/rawOSHB/OSHB.parsedOriginal.json'

OUTPUT_FIELDNAMES = ['FGID','Ref','RowType','Special','Strongs','CantillationHierarchy','Morphology','OSHBid','WordOrMorpheme' if BREAK_MORPHEMES else 'Word']
OUTPUT_FIELDNAMES_COUNT = len( OUTPUT_FIELDNAMES )


state = None
class State:
    def __init__( self ) -> None:
        """
        Constructor:
        """
        self.OSHB_XML_input_folderpath = OSHB_XML_INPUT_FOLDERPATH
        self.sourceTableFilepath = Path( '../../CNTR-GNT/sourceExports/collation.updated.csv' )
        self.numKetivs = 0
    # end of convert_OSHB_XML_to_TSV.State.__init__


def main() -> None:
    """
    Load, refactor, check, and finally export the WLC data.
    """
    BibleOrgSysGlobals.introduceProgram( __name__, PROGRAM_NAME_VERSION, LAST_MODIFIED_DATE )
    global state
    state = State()

    if load_OSHB_XML() and adjust_data_table():
        export_table_to_files()
# end of convert_OSHB_XML_to_TSV.main


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

    vPrint( 'Quiet',  DEBUGGING_THIS_MODULE, f"  Loaded {len(state.flat_array):,} total data rows{' (with breaks at morphemes)' if BREAK_MORPHEMES else ''}.")
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"    Found {state.numKetivs:,} total KETIV words used." )

    return True
# end of convert_OSHB_XML_to_TSV.load_OSHB_XML


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

    chapter_array, id_list = [], []
    chapters = tree.getroot().findall('.//osis:chapter', namespaces)
    for chapter in chapters:
        C = len(chapter_array) + 1
        assert C < 1000
        verses = chapter.findall('.//osis:verse', namespaces)
        verseArray = []
        for verse in verses:
            V = len(verseArray)+1
            assert V < 1000
            verse_element_array = []
            word_number = 1
            for j,verse_element in enumerate( verse, start=1 ):
                assert j < 100

                if verse_element.tag == f"{{{namespaces['osis']}}}w":

                    numeric_ref = f"{str(nn).zfill(2)}{str(C).zfill(3)}{str(V).zfill(3)}{str(word_number).zfill(2)}"
                    readable_ref = f'{BBB}_{C}:{V}w{word_number}'

                    lemma = verse_element.attrib.get('lemma')
                    n = verse_element.attrib.get('n') # See https://github.com/openscriptures/morphhb/issues/46
                    morph = verse_element.attrib.get('morph')
                    assert morph[0] in 'HA' # Must be Hebrew or Aramaic
                    OS_id = verse_element.attrib.get('id')
                    wType = verse_element.attrib.get('type')
                    if wType:
                        assert wType == 'x-ketiv', f"Found {wType=}"
                        state.numKetivs += 1
                    ketiv = 'K' if wType else ''
                    word = verse_element.text

                    if OS_id:
                        assert int(OS_id[:2]) == nn # id field should start with 2-digit book number
                        id_list.append( OS_id ) # we'll check later for duplicates

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
                            verse_element_array.append([readable_ref, 'w', ketiv, lemma, n, morph, OS_id, word])
                            state.flat_array.append([numeric_ref, readable_ref, 'w', ketiv, lemma, n, morph, OS_id, word])
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
                                verse_element_array.append([adj_readable_ref, 'm', ketiv, lemma_bit, n, morph_bit, adj_id, word_bit])
                                entry = [adj_numeric_ref, adj_readable_ref, 'm', ketiv, lemma_bit, n, morph_bit, adj_id, word_bit]
                                assert len(entry) == OUTPUT_FIELDNAMES_COUNT, f"Entry should have {OUTPUT_FIELDNAMES_COUNT} fields, not {len(entry)}: {entry}"
                                state.flat_array.append( entry )
                    else: # it's simple
                        verse_element_array.append([readable_ref, 'w', ketiv, lemma, n, morph, OS_id, word])
                        entry = (numeric_ref, readable_ref, 'w', ketiv, lemma, n, morph, OS_id, word)
                        assert len(entry) == OUTPUT_FIELDNAMES_COUNT, f"Entry should have {OUTPUT_FIELDNAMES_COUNT} fields, not {len(entry)}: {entry}"
                        state.flat_array.append( entry )
                    word_number += 1
                    

                elif verse_element.tag == f"{{{namespaces['osis']}}}seg":
                    numeric_ref = f"{str(nn).zfill(2)}{str(C).zfill(3)}{str(V).zfill(3)}"
                    readable_ref = f'{BBB}_{C}:{V}'

                    seg_type = verse_element.attrib.get('type')
                    verse_element_array.append([readable_ref, 'seg', seg_type, verse_element.text])
                    entry = [numeric_ref, readable_ref, 'seg', '','','', seg_type, '', verse_element.text]
                    assert len(entry) == OUTPUT_FIELDNAMES_COUNT, f"Entry should have {OUTPUT_FIELDNAMES_COUNT} fields, not {len(entry)}: {entry}"
                    state.flat_array.append( entry )

                elif verse_element.tag == f"{{{namespaces['osis']}}}note":
                    numeric_ref = f"{str(nn).zfill(2)}{str(C).zfill(3)}{str(V).zfill(3)}"
                    readable_ref = f'{BBB}_{C}:{V}'

                    n = verse_element.attrib.get('n')
                    noteType = verse_element.attrib.get('type')
                    noteText = verse_element.text
                    # if readable_ref=='JER_48:44':
                    #     noteText = noteText.strip() # Need to strip multiline note
                    #     # NOTE: This doesn't work! We had to edit Jer.xml in Forked/OS-morphhb/wlc/
                    #     while '  ' in noteText: noteText = noteText.replace( '  ', ' ' )
                    #     print( f"{readable_ref} {noteText=}" )
                    vPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"    Got note: {readable_ref} {n=} {noteType=} {noteText=}" )
                    if noteType in ('variant','alternative','exegesis'):
                        if noteType in ('variant','alternative'):
                            assert not noteText
                            noteText = '' # it probably was None
                        for noteChild in verse_element:
                            if noteChild.tag == f"{{{namespaces['osis']}}}catchWord":
                                for attrib,value in noteChild.items():
                                    print(attrib,value); halt # Should be no attributes
                                noteText = f"{noteText}{' ' if noteText else ''}{noteChild.text}:"
                                assert 'None' not in noteText, f"BAD note: {readable_ref} {n=} {noteType=} {noteText=}"
                            elif noteChild.tag == f"{{{namespaces['osis']}}}rdg":
                                for attrib,value in noteChild.items():
                                    if attrib == 'type':
                                        noteText = f"{noteText}{' ' if noteText else ''}({value})"
                                        assert 'None' not in noteText, f"BAD note: {readable_ref} {n=} {noteType=} {noteText=}"
                                    else: print(attrib,value); halt # Should be no attributes
                                for rdgChild in noteChild:
                                    if rdgChild.tag == f"{{{namespaces['osis']}}}w":
                                        noteText = f"{noteText}{' ' if noteText and noteText[-1] not in '׀־' else ''}'{rdgChild.text}':"
                                        assert 'None' not in noteText, f"BAD note: {readable_ref} {n=} {noteType=} {noteText=}"
                                        for attrib,value in rdgChild.items():
                                            noteText = f"{noteText}{' ' if noteText else ''}{attrib}={value}"
                                            assert 'None' not in noteText, f"BAD note: {readable_ref} {n=} {noteType=} {noteText=}"
                                    elif rdgChild.tag == f"{{{namespaces['osis']}}}seg":
                                        assert rdgChild.get('type') in ('x-maqqef','x-paseq'), f"Seg is {rdgChild.get('type')} {rdgChild.text=}"
                                        noteText = f"{noteText}{rdgChild.text}"
                                        assert 'None' not in noteText, f"BAD note: {readable_ref} {n=} {noteType=} {noteText=}"
                                    else: print(rdgChild); halt
                                    if rdgChild.text:
                                        noteText = f"{noteText}{' ' if noteText else ''}{rdgChild.text}"
                                        assert 'None' not in noteText, f"BAD note: {readable_ref} {n=} {noteType=} {noteText=}"
                                if noteChild.text:
                                    noteText = f"{noteText}{noteChild.text}"
                                    assert 'None' not in noteText, f"BAD note: {readable_ref} {n=} {noteType=} {noteText=}"
                            else: print(noteChild); halt
                        # if readable_ref=='JER_48:44':
                        #     noteText = noteText.strip() # Need to strip multiline note
                        #     # NOTE: This doesn't work! We had to edit Jer.xml in Forked/OS-morphhb/wlc/
                        #     while '  ' in noteText: noteText = noteText.replace( '  ', ' ' )
                        #     print( f"{readable_ref} {noteText=}" )
                        vPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"    Now note: {readable_ref} {n=} {noteType=} {noteText=}" )
                        assert '  ' not in noteText and noteText.strip()==noteText
                        # if readable_ref=='JER_49:25': halt # Next note afterwards
                    else: # not 'variant'
                        assert noteText
                        for attrib,value in verse_element.items():
                            assert attrib in ('n',), f"Unhandled {attrib}='{value}'"

                    assert 'None' not in noteText, f"BAD note: {readable_ref} {n=} {noteType=} {noteText=}"
                    if readable_ref == 'KI1_22:44': noteText = noteText.replace( '!', '' ) # 'KJV:1Kgs.22.43!b'
                    assert '!' not in noteText, f"BAD note: {readable_ref} {n=} {noteType=} {noteText=}"
                    verse_element_array.append([readable_ref, 'note', n, noteType, noteText])
                    entry = [numeric_ref, readable_ref, 'note', noteType,'', n, '','', noteText.rstrip()] # TODO: Why is there a trailing space???
                    assert len(entry) == OUTPUT_FIELDNAMES_COUNT, f"Entry should have {OUTPUT_FIELDNAMES_COUNT} fields, not {len(entry)}: {entry}"
                    state.flat_array.append( entry )

                else:
                    logging.critical( f"Unknown verse element at {readable_ref}: {verse_element.tag}")
                    halt
            verseArray.append(verse_element_array)
        chapter_array.append(verseArray)
        assert len(set(id_list)) == len(id_list) # i.e., no duplicate IDs within book

    vPrint( 'Info', DEBUGGING_THIS_MODULE, f"    Loaded {len(chapter_array):,} XML chapters." )

    return chapter_array
# end of convert_OSHB_XML_to_TSV.load_OSHB_XML_bookfile


def adjust_data_table() -> bool:
    """
    """
    # Check all fields for superfluous leading/trailing spaces
    for row in state.flat_array:
        # print( f"  {row=}")
        assert isinstance( row, list )
        for columnNumber,field in enumerate( row ):
            if field: assert field.strip() == field, f"{columnNumber=} {field=} from {row=}"
            if field and field.strip() != field:
                row[columnNumber] = field.strip()
        # print( f"  {row=}")
        # if 'Often this notation indicates a typographical error in BHS' in str(row): halt # Gen 1:12

    return True
# end of convert_OSHB_XML_to_TSV.adjust_data_table


def export_table_to_files() -> bool:
    """
    Use state.flat_array to export the TSV and JSON.
    """
    OSHB_TSV_output_filepath = Path( OSHB_TSV_OUTPUT_FILEPATH_STRING.replace( '.parsedOriginal.', '.parsedOriginal.flat.morphemes.' )
                if BREAK_MORPHEMES else OSHB_TSV_OUTPUT_FILEPATH_STRING.replace( '.parsedOriginal.', '.parsedOriginal.flat.words.' ) )
    print( f"Exporting WLC table as a single flat TSV file ({OUTPUT_FIELDNAMES_COUNT} columns) to {OSHB_TSV_output_filepath}…" )
    with open( OSHB_TSV_output_filepath, 'wt', encoding='utf-8' ) as tsv_output_file:
        tsv_output_file.write('\ufeff') # Write BOM
        writer = DictWriter( tsv_output_file, fieldnames=OUTPUT_FIELDNAMES, delimiter='\t' )
        writer.writeheader()
        for row in state.flat_array:
            rowDict = {k:v for k,v in zip(OUTPUT_FIELDNAMES,row)}
            writer.writerow( rowDict )

    OSHB_JSON_output_filepath = Path( OSHB_JSON_OUTPUT_FILEPATH_STRING.replace( '.parsedOriginal.', '.parsedOriginal.flat.morphemes.' )
                if BREAK_MORPHEMES else OSHB_JSON_OUTPUT_FILEPATH_STRING.replace( '.parsedOriginal.', '.parsedOriginal.flat.words.' ) )
    print( f"Exporting WLC table as a single flat JSON file to {OSHB_JSON_output_filepath}…" )
    with open( OSHB_JSON_output_filepath, 'wt', encoding='utf-8' ) as json_output_file:
        json.dump( state.flat_array, json_output_file, indent=2 )
    OSHB_JSON_output_filepath = Path( OSHB_JSON_OUTPUT_FILEPATH_STRING.replace( '.parsedOriginal.', '.parsedOriginal.nested.morphemes.' )
                if BREAK_MORPHEMES else OSHB_JSON_OUTPUT_FILEPATH_STRING.replace( '.parsedOriginal.', '.parsedOriginal.nested.words.' ) )
    print( f"Exporting WLC table as a single nested book/chapter/verse JSON file to {OSHB_JSON_output_filepath}…" )
    with open( OSHB_JSON_output_filepath, 'wt', encoding='utf-8' ) as json_output_file:
        json.dump( state.books_array, json_output_file, indent=2 )

    return True
# end of convert_OSHB_XML_to_TSV.export_table_to_files


if __name__ == '__main__':
    # from multiprocessing import freeze_support
    # freeze_support() # Multiprocessing support for frozen Windows executables

    # Configure basic Bible Organisational System (BOS) set-up
    parser = BibleOrgSysGlobals.setup( SHORT_PROGRAM_NAME, PROGRAM_VERSION, LAST_MODIFIED_DATE )
    BibleOrgSysGlobals.addStandardOptionsAndProcess( parser )

    main()

    BibleOrgSysGlobals.closedown( PROGRAM_NAME, PROGRAM_VERSION )
# end of convert_OSHB_XML_to_TSV.py
