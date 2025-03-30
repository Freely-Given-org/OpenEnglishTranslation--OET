#!/usr/bin/env python3
# -\*- coding: utf-8 -\*-
# SPDX-License-Identifier: GPL-3.0-or-later
#
# convert_BibTags_USFM_to_TSV.py
#
# Script handling convert_BibTags_USFM_to_TSV functions
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
Script taking BibleTags Hebrew and Greek USFM files
    (which currently come from the unfoldingWord UGNT and UHB)
    and saving each set (OT and NT) into a seven-column TSV file.
"""
from gettext import gettext as _
from typing import Dict, List, Tuple
from pathlib import Path

if __name__ == '__main__':
    import sys
    sys.path.insert( 0, '../../BibleOrgSys/' )
from BibleOrgSys import BibleOrgSysGlobals
from BibleOrgSys.BibleOrgSysGlobals import vPrint, fnPrint, dPrint


LAST_MODIFIED_DATE = '2022-10-19' # by RJH
SHORT_PROGRAM_NAME = "convert_BibTags_USFM_to_TSV"
PROGRAM_NAME = "Extract and Save BibleTags USFM as TSV"
PROGRAM_VERSION = '0.50'
PROGRAM_NAME_VERSION = f'{SHORT_PROGRAM_NAME} v{PROGRAM_VERSION}'

DEBUGGING_THIS_MODULE = False


USFM_INPUT_FOLDERPATH = Path( '../../Forked/bibletags-usfm/usfm/' )
OT_USFM_INPUT_FOLDERPATH = USFM_INPUT_FOLDERPATH.joinpath( 'uhb/' )
NT_USFM_INPUT_FOLDERPATH = USFM_INPUT_FOLDERPATH.joinpath( 'ugnt/' )
USFM_FILENAME_TEMPLATE = 'nn-UUU.usfm'
TSV_OUTPUT_FOLDERPATH = Path( '../sourceTexts/BibleTagsOriginals/' )

state = None
class State:
    def __init__( self ) -> None:
        """
        Constructor:
        """
        self.OT_USFM_input_folderpath = OT_USFM_INPUT_FOLDERPATH
        self.NT_USFM_input_folderpath = NT_USFM_INPUT_FOLDERPATH
        self.USFM_filename_template = USFM_FILENAME_TEMPLATE
        self.TSV_output_folderpath = TSV_OUTPUT_FOLDERPATH
    # end of convert_BibTags_USFM_to_TSV.State.__init__()


def main() -> None:
    """
    """
    BibleOrgSysGlobals.introduceProgram( __name__, PROGRAM_NAME_VERSION, LAST_MODIFIED_DATE )
    global state
    state = State()

    if handle_OT():
        handle_NT()
# end of convert_BibTags_USFM_to_TSV.main


def handle_OT() -> bool:
    """
    """
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"\nLoading OT USFM files from {state.OT_USFM_input_folderpath}/…")

    wordList = []
    for referenceNumber in range(1, 39+1):
        BBB = BibleOrgSysGlobals.loadedBibleBooksCodes.getBBBFromReferenceNumber( referenceNumber )
        Uuu = BibleOrgSysGlobals.loadedBibleBooksCodes.getUSFMAbbreviation( BBB )
        # bookname = BibleOrgSysGlobals.loadedBibleBooksCodes.getEnglishName_NR( BBB )
        filename = state.USFM_filename_template.replace( 'nn', str(referenceNumber).zfill(2) ).replace( 'UUU', Uuu.upper() )

        vPrint( 'Info', DEBUGGING_THIS_MODULE, f"  Loading {BBB} USFM file from {filename}…")
        with open(state.OT_USFM_input_folderpath.joinpath(filename), 'rt', encoding='utf-8') as usfm_file:
            usfm_text = usfm_file.read()

            # Remove any BOM
            if usfm_text[0].startswith("\ufeff"):
                vPrint( 'Quiet', DEBUGGING_THIS_MODULE, "  Handling Byte Order Marker (BOM) at start of our OT USFM file…")
                usfm_text[0] = usfm_text[0][1:]

            wordList += parseBook( BBB, usfm_text )

    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  Loaded {len(wordList):,} word entries in OT wordList.")

    return saveWordList( 'BibTags.OT.words.tsv', wordList )
# end of convert_BibTags_USFM_to_TSV.handle_OT


def handle_NT() -> bool:
    """
    """
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"\nLoading NT USFM files from {state.NT_USFM_input_folderpath}/…")

    wordList = []
    for referenceNumber in range(40, 66+1):
        BBB = BibleOrgSysGlobals.loadedBibleBooksCodes.getBBBFromReferenceNumber( referenceNumber )
        Uuu = BibleOrgSysGlobals.loadedBibleBooksCodes.getUSFMAbbreviation( BBB )
        # NOTE: Matthew is at #41 (not 40)
        filename = state.USFM_filename_template.replace( 'nn', str(referenceNumber+1).zfill(2) ).replace( 'UUU', Uuu.upper() )

        vPrint( 'Info', DEBUGGING_THIS_MODULE, f"  Loading {BBB} USFM file from {filename}…")
        with open(state.NT_USFM_input_folderpath.joinpath(filename), 'rt', encoding='utf-8') as usfm_file:
            usfm_text = usfm_file.read()

            # Remove any BOM
            if usfm_text[0].startswith("\ufeff"):
                vPrint( 'Quiet', DEBUGGING_THIS_MODULE, "  Handling Byte Order Marker (BOM) at start of our OT USFM file…")
                usfm_text[0] = usfm_text[0][1:]

            wordList += parseBook( BBB, usfm_text )

    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  Loaded {len(wordList):,} word entries in NT wordList.")

    return saveWordList( 'BibTags.NT.words.tsv', wordList )
# end of convert_BibTags_USFM_to_TSV.handle_NT


def parseBook( BBB:str, usfmText:str ):
    """
    """
    # We assume a line-by-line format (even though USFM itself doesn't require that)
    C, V = 0, 0
    bookWordList = []
    for usfm_line in usfmText.split('\n'):
        if not usfm_line: continue # ignore blank lines
        marker, rest = usfm_line.split(' ', 1) if ' ' in usfm_line else (usfm_line,'')
        # dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"{marker}='{rest}'")
        if marker in ('\\id','\\usfm','\\ide','\\h',
                        '\\toc1','\\toc2','\\toc3','\\mt',):
            pass # We ignore all these headers
        elif marker == '\\c':
            C, V = rest, '0'
            assert C.isdigit()
            ref = f'{BBB}_{C}:{V}'
        elif marker == '\\v':
            V = rest
            assert V.isdigit()
            ref = f'{BBB}_{C}:{V}'
        elif marker == '\\p':
            assert not rest
        elif marker == '\\w' or marker == '[\\w' or marker == '(\\w':
            bookWordList += parseWords( ref, rest )
        elif marker == '\\f':
            parseFootnote( ref, rest )
        elif marker == '\\zApparatusJson':
            parseApparatus( ref, rest )
        else: raise Exception( f"Unexpected OT marker: {marker}='{rest}'" )
    return bookWordList
# end of convert_BibTags_USFM_to_TSV.parseBook


def parseWords( ref:str, wordsText:str ):
    """
    """
    dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"  Handling {ref} word(s): {wordsText}")
    assert 1 <= wordsText.count('\\w*') <= 4
    assert wordsText.endswith('\\w*') or wordsText[-1] in ']׃פ׀ס־׆' or wordsText[-1] in ',.?!:;—)…'
    bits = wordsText.split('\\w*')
    trailingPunctuation = None
    allBits = []
    for b,bit in enumerate(bits):
        if not bit:
            assert b == len(bits) - 1 # Must be last bit
            continue
        dPrint( 'Never', DEBUGGING_THIS_MODULE, f"    Handle {ref} bit: {b} '{bit}'")
        if b==0 or '\\w' in bit:
            leadingPunctuation, word, attributeDict = parseWord( ref, bit )
            allBits.append(leadingPunctuation); allBits.append(word); allBits.append(attributeDict)
        else:
            assert b == len(bits) - 1 # Must be last bit
            assert not trailingPunctuation
            trailingPunctuation = bit
    allBits.append(trailingPunctuation)
    assert allBits[0] is None
    allBits.pop(0) # First entry is always None
    # Now allBits is set(s) of three: word, attributeDict, afterPunctuation
    resultList = []
    ix = 0
    while ix < len(allBits):
        resultList.append( (ref,allBits[ix],allBits[ix+1],allBits[ix+2]))
        ix += 3
    return resultList
# end of convert_BibTags_USFM_to_TSV.parseWords


def parseWord( ref:str, wordText:str ):
    """
    """
    dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"    Handling {ref} word: {wordText}")
    assert '\\w*' not in wordText
    if '\\w ' in wordText:
        assert wordText.count('\\w ') == 1
        assert wordText.index('\\w ') in (0,1) # Might be one preceding punctuation mark
    leadingPunctuation = None
    if wordText[0] == '־':
        leadingPunctuation, wordText = wordText[0], wordText[1:]
    if wordText.startswith('\\w '):
        wordText = wordText[2:]
    word, attributeText = wordText.split('|', 1)
    assert attributeText.endswith('"')
    attributeText = attributeText[:-1] # Remove trailing quote
    attributeBits = attributeText.split('" ') # Can't split by space coz some double words in lemma fields
    assert len(attributeBits) == 4
    attributeDict = {}
    for attributeBit in attributeBits:
        name, value = attributeBit.split('="', 1)
        assert not value.startswith('"') and not value.endswith('"'), f"{ref} {wordText=} {attributeBits=} {value=}"
        attributeDict[name.strip()] = value # Shouldn't need to strip, but handles two spaces between attributes (for 1Sam 18:9 09JUP)
    return leadingPunctuation, word, attributeDict
# end of convert_BibTags_USFM_to_TSV.parseWord


def parseFootnote( ref:str, footnoteText:str ):
    assert footnoteText.count('\\f*') == 1
    assert footnoteText.endswith('\\f*')
    footnoteText = footnoteText[:-3] # Remove end marker
    dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"    Ignoring {ref} footnote: {footnoteText}")
# end of convert_BibTags_USFM_to_TSV.parseFootnote


def parseApparatus( ref:str, apparatusJSON:str ):
    # dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"    parseApparatus {ref}: {apparatusJSON}")
    assert apparatusJSON.count('\\zApparatusJson*') == 1
    assert apparatusJSON.endswith('\\zApparatusJson*')
    apparatusJSON = apparatusJSON[:-16] # Remove end marker
    assert apparatusJSON.startswith('{"words":[') \
        and (apparatusJSON.endswith('"]}') or apparatusJSON.endswith('[]}'))
    dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"    Ignoring {ref} apparatus: {apparatusJSON}")
# end of convert_BibTags_USFM_to_TSV.parseApparatus


def saveWordList( filename:str, wordList:list) -> bool:
    """
    """
    filepath = state.TSV_output_folderpath.joinpath(filename)
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"\nSaving TSV data to {filepath}…")
    
    BibleOrgSysGlobals.backupAnyExistingFile( filepath, numBackups=5 )

    with open( filepath, 'wt', encoding='utf-8' ) as outputFile:
        outputFile.write("Ref\tBibTagId\tWord\tLemma\tStrong\tMorphology\tAfter\n")
        lastRef = None
        for ref,word,attributeDict,afterPunct in wordList:
            # print(f"{ref} {word=} {attributeDict} {afterPunct=}")
            if ref != lastRef:
                wordNumber = 1
            else: wordNumber += 1
            outputFile.write(f"{ref}w{wordNumber}\t{attributeDict['x-id']}\t{word}\t{attributeDict['lemma']}\t{attributeDict['strong']}\t{attributeDict['x-morph']}\t{afterPunct if afterPunct else ''}\n")
            lastRef = ref
    return True
# end of convert_BibTags_USFM_to_TSV.saveWordList


if __name__ == '__main__':
    # from multiprocessing import freeze_support
    # freeze_support() # Multiprocessing support for frozen Windows executables

    # Configure basic Bible Organisational System (BOS) set-up
    parser = BibleOrgSysGlobals.setup( SHORT_PROGRAM_NAME, PROGRAM_VERSION, LAST_MODIFIED_DATE )
    BibleOrgSysGlobals.addStandardOptionsAndProcess( parser )

    main()

    BibleOrgSysGlobals.closedown( PROGRAM_NAME, PROGRAM_VERSION )
# end of convert_BibTags_USFM_to_TSV.py
