#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# backfill_OET-LV.py
#
# Script to backport the ULT OT into empty verses of the OET-LV OT
#
# Copyright (C) 2021-2022 Robert Hunt
# Author: Robert Hunt <Freely.Given.org@gmail.com>
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
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Script to backport the ULT into empty verses of the OET-LV
    in order to give us the text of all the Bible,
    even if we haven't manually worked through it all carefully yet.

This script is designed to be able to be run over and over again,
    i.e., it should be able to update the OET-LV with more recent ULT edits.

Updated Sept 2022 to not backfill the New Testament.
"""
from gettext import gettext as _
from typing import List, Tuple, Optional
from pathlib import Path
import logging
import re

if __name__ == '__main__':
    import sys
    sys.path.insert( 0, '../../BibleOrgSys/' )
from BibleOrgSys import BibleOrgSysGlobals
from BibleOrgSys.BibleOrgSysGlobals import vPrint, fnPrint, dPrint
from BibleOrgSys.Bible import Bible
from BibleOrgSys.Reference.BibleOrganisationalSystems import BibleOrganisationalSystem
from BibleOrgSys.Misc import CompareBibles


LAST_MODIFIED_DATE = '2022-09-01' # by RJH
SHORT_PROGRAM_NAME = "Backfill_OET-LV"
PROGRAM_NAME = "Backfill OET-LV from ULT"
PROGRAM_VERSION = '0.13'
PROGRAM_NAME_VERSION = '{} v{}'.format( SHORT_PROGRAM_NAME, PROGRAM_VERSION )

DEBUGGING_THIS_MODULE = False


ULTFolderPath = BibleOrgSysGlobals.DEFAULT_WRITEABLE_OUTPUT_FOLDERPATH.joinpath( 'unfoldingWordAlignedTexts/ULT_TextOnly_USFM/' )
project_folderpath = Path(__file__).parent.parent # Find folders relative to this module
OETInputFolderPath = project_folderpath.joinpath( 'translatedTexts/LiteralVersionOld/' ) # NOTE: Uses OLD ESFM files.......................XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
OETOutputFolderPath = project_folderpath.joinpath( 'derivedTexts/backFilledTexts/LiteralVersion/' )
assert ULTFolderPath.is_dir()
assert OETInputFolderPath.is_dir()
assert OETOutputFolderPath.is_dir()



loaded_ULT_BBB = None
loaded_ULT_dict = {}
def get_ULT_verse( BBB:str, C:str, V:str ) -> str:
    """
    """
    global loaded_ULT_BBB, loaded_ULT_dict
    fnPrint( DEBUGGING_THIS_MODULE, f"get_ULT_verse( {BBB}, {C}, {V} )" )

    if loaded_ULT_BBB != BBB:
        vPrint( 'Info', DEBUGGING_THIS_MODULE, f"  Loading ULT {BBB}…")
        loaded_ULT_dict = {}
        nn = BibleOrgSysGlobals.loadedBibleBooksCodes.getReferenceNumber( BBB )
        if nn > 39: nn += 1 # USFM has MAT at 41, not 40
        usfmBBB = BibleOrgSysGlobals.loadedBibleBooksCodes.getUSFMAbbreviation( BBB ).upper()
        with open( ULTFolderPath.joinpath(f'{nn:02}{usfmBBB}BibleWriter.usfm'), 'rt' ) as ULT_file:
            ULT_text = ULT_file.read()
        # haveP = False
        ultC = ultV = '0'
        for line in ULT_text.split('\n'):
            line = line.rstrip( '\r\n' )
            if line:
                # print( f"Got ULT {BBB} {ultC}:{ultV} line: '{line}'")
                if line[0] == '\\':
                    if ' ' in line: marker, rest = line[1:].split(' ', 1)
                    else: marker, rest = line[1:], ''
                else: marker, rest = None, line
                if marker == 'c':
                    ultC, ultV = rest, '0'
                    if not ultC.isdigit():
                        vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  ULT {BBB} {ultC} has non-digit chapter" )
                elif marker == 'v':
                    vLine = rest
                    ultV, text = vLine.split( ' ', 1 )
                    if not ultC.isdigit():
                        vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  ULT {BBB} {ultC}:{ultV} has non-digit verse" )
                    loaded_ULT_dict[(ultC,ultV)] = text
                elif marker == 'p':
                    haveP = True
                elif ultC!='0' and ultV!='0' and marker in ('m','q1','q2','q3','q4', 'qa', 'pi1'):
                    loaded_ULT_dict[(ultC,ultV)] += f' {rest}'
                elif BBB=='PSA' and ultC!='0' and ultV=='0' and marker in('d','qa'):
                    assert (ultC,ultV) not in loaded_ULT_dict, f"Didn't expect existing text at {BBB} {C}:{V}"
                    loaded_ULT_dict[(ultC,ultV)] = f' {rest}'
                elif rest and marker not in ('id','usfm','ide','h','toc1','toc2','toc3','mt1','mt2', 'sp'):
                    logging.critical( f"Skipped ULT {BBB} {ultC}:{ultV} line: '{line}'")
        loaded_ULT_BBB = BBB

    try: return loaded_ULT_dict[(C,V)]
    except KeyError: # presumably a versification mismatch
        if V!='0': vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"Seems ULT doesn't have {BBB} {C}:{V} -- is this a versification mismatch?")
        return ''
#end of get_ULT_verse

def adjust_ULT_verse( BBB:str, C:str, V:str, raw_text:str ) -> str:
    """
    Do some of the changes between ULT standards and the OET requirements:
        remove speech marks
    """
    fnPrint( DEBUGGING_THIS_MODULE, f"adjust_ULT_verse( {BBB} {C}:{V} {raw_text} )" )
    # print( f"{BBB} {C}:{V} {raw_text}" )

    adjusted_text = ( raw_text
        .replace( 'God', 'God=G' ).replace( 'Yahweh', 'YHWH=G' )
        .replace( 'Jesus Christ', 'Iesous=PJesus Kristos=PChrist').replace( 'Christ Jesus', 'Kristos=PChrist Iesous=PJesus')
        .replace( ' Jesus', ' Iesous=PJesus' )

        .replace( 'Abraham', 'Abraham=P' )
        .replace( 'Antipas', 'Antipas=P' )
        .replace( 'Balaam', 'Balaam=P' )
        .replace( 'Jacob', 'Jacob=P' )
        .replace( 'James', 'James=P' )
        .replace( 'John', 'Ioannes=PJohn' )
        .replace( 'Jonah', 'Jonah=P' )
        .replace( 'Lazarus', 'Lazarus=P' )
        .replace( 'Lot', 'Lot=P' )
        .replace( 'Moses', 'Moses=P' )

        .replace( 'Bethlehem', 'Bethlehem=L' )
        .replace( 'Ephesus', 'Ephesus=L' )
        .replace( 'Jerusalem', 'Ierousalem=LJerusalem' )
        .replace( 'Judea', 'Judea=L' )
        .replace( 'Patmos', 'Patmos=L' )
        .replace( 'Pergamum', 'Pergamum=L' )
        .replace( 'Philadelphia', 'Philadelphia=L' )
        .replace( 'Sardis', 'Sardis=L' )
        .replace( 'Smyrna', 'Smyrna=L' )
        .replace( 'Sodom', 'Sodom=L' )

        .replace( '12,000', 'twelve thousands' )
        )
    adjusted_text = re.sub( '([^vc])(\D)12([^\d,])', '\\1\\2twelve\\3', adjusted_text )

    # Remove speech marks
    adjusted_text = ( adjusted_text.removeprefix( '“' )
                        .replace( ', “', ': ' ).replace( '“', ': ' )
                        .replace( '”', '' ) )
    adjusted_text = adjusted_text.replace( ', "', ': ' ).replace( '"', '' )

    # Replace { } with \add markers
    adjusted_text = adjusted_text.replace( '{', '\\add ' ).replace( '}', '\\add*' )

    # Simplify some punctuation
    adjusted_text = adjusted_text.replace( '!', '.' ).replace( '?', '.' ) \
                                .replace( ';', ',' ) \
                                .replace( '—', ', ' )

    dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"{BBB} {C}:{V} {adjusted_text}" )
    return adjusted_text
# end of adjust_ULT_verse


def backfill_OET_LV( BBB:str ) -> None:
    """
    The function that actually does the work for each book.
    """
    fnPrint( DEBUGGING_THIS_MODULE, f"backfill_OET_LV( {BBB} )" )

    nn = BibleOrgSysGlobals.loadedBibleBooksCodes.getReferenceNumber( BBB )
    if nn > 39: nn += 1 # USFM has MAT at 41, not 40
    usfmBBB = BibleOrgSysGlobals.loadedBibleBooksCodes.getUSFMAbbreviation( BBB ).upper()

    # Firstly read the existing OET-LV lines
    with open( OETInputFolderPath.joinpath(f'{nn:02}{usfmBBB}OET-LV.ESFM'), 'rt' ) as OET_input_file:
        sourceLines = OET_input_file.readlines()

    # Now fill in the
    verseFillCount = 0
    outputLines = []
    C = V = '0'
    for line in sourceLines:
        line = line.rstrip()
        # print( f"Working on OET {BBB} {C}:{V} line: '{line}'")
        if line.startswith( '\\c ' ):
            C, V = line[3:], '0'
            if BBB=='PSA':
                # We prepend a special character (~) to indicate a backfilled verse
                if text := adjust_ULT_verse( BBB, C, V, get_ULT_verse( BBB, C, V ) ):
                    outputLines.append( line ) # The chapter number
                    vPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"Replacing empty OET {BBB} {C}:{V} with '{text}'")
                    line = f'\\d ~{text}' # Prepend a tilde to make it clear that this is a back-filled line
                    verseFillCount += 1
        elif line.startswith( '\\v '):
            vLine = line[3:]
            if ' ' in vLine:
                V, text = vLine.split( ' ', 1 )
            else: V, text = vLine, ''
            if not text or text[0]=='~':
                # We prepend a special character (~) to indicate a backfilled verse
                text = adjust_ULT_verse( BBB, C, V, get_ULT_verse( BBB, C, V ) )
                vPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"Replacing empty OET {BBB} {C}:{V} with '{text}'")
                line = f'\\v {V} ~{text}' # Prepend a tilde to make it clear that this is a back-filled line
                verseFillCount += 1
        outputLines.append( line )

    # Do punctuation tidy-ups and write the new ESFM file
    outputText = ( '\n'.join( outputLines )
                    .replace( '  ', ' ' )
                    .replace ( ', :', ':' ) ) # Can happen if we removed a ULT \q
    outputText = re.sub( r',\n\\v (\d{1,3}) ~: ', r':\n\\v \1 ~', outputText )

    with open( OETOutputFolderPath.joinpath(f'{nn:02}{usfmBBB}OET-LV.ESFM'), 'wt' ) as OET_output_file:
        OET_output_file.write( outputText )

    if verseFillCount: vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  Backfilled {verseFillCount:,} empty or updated {BBB} verses" )
    else: vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  {BBB} appeared to be complete and no backfilling was required  :-)" )
    return verseFillCount
# end of backfill_OET_LV


def main():
    """
    Main program to handle command line parameters and then run what they want.
    """
    BibleOrgSysGlobals.introduceProgram( __name__, PROGRAM_NAME_VERSION, LAST_MODIFIED_DATE )

    genericBibleOrganisationalSystem = BibleOrganisationalSystem( 'GENERIC-KJV-ENG' )
    genericBookList = genericBibleOrganisationalSystem.getBookList()

    numBooksProcessed = numVersesBackfilled = 0
    for BBB in genericBookList: # includes intro, etc.
        if BibleOrgSysGlobals.loadedBibleBooksCodes.isOldTestament_NR( BBB ):
        # or BibleOrgSysGlobals.loadedBibleBooksCodes.isNewTestament_NR( BBB ):
            numVersesBackfilled += backfill_OET_LV( BBB )
            numBooksProcessed += 1
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"Finished processing {numBooksProcessed} books (Backfilled {numVersesBackfilled:,} verses)" )
# end of backfill_OET-LV.main

if __name__ == '__main__':
    # Configure basic Bible Organisational System (BOS) set-up
    parser = BibleOrgSysGlobals.setup( PROGRAM_NAME, PROGRAM_VERSION )
    BibleOrgSysGlobals.addStandardOptionsAndProcess( parser, exportAvailable=False )

    main()

    BibleOrgSysGlobals.closedown( PROGRAM_NAME, PROGRAM_VERSION )
# end of backfill_OET-LV.py
