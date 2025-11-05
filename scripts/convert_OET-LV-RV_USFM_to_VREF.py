#!/usr/bin/env python3
# -\*- coding: utf-8 -\*-
# SPDX-FileCopyrightText: © 2024 Robert Hunt <Freely.Given.org+OET@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later
#
# convert_OET-LV-RV_USFM_to_VREF.py
#
# Script to convert cleaned OET USFM files to VPL vref.txt files
#
# Copyright (C) 2024-2025 Robert Hunt
# Author: Robert Hunt <Freely.Given.org+OET@gmail.com>
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
Script to convert cleaned OET USFM files
    to even more cleaned VPL vref.txt files.

TODO: Doesn't delete the \rem ESFM headers yet


CHANGELOG:
    2025-03-31 Adjust input folder
"""
from pathlib import Path
import logging

if __name__ == '__main__':
    import sys
    sys.path.insert( 0, '../../BibleOrgSys/' )
from BibleOrgSys import BibleOrgSysGlobals
from BibleOrgSys.BibleOrgSysGlobals import vPrint, fnPrint, dPrint
from BibleOrgSys.Internals.InternalBibleInternals import InternalBibleEntryList
import BibleOrgSys.Formats.USFMBible as USFMBible


LAST_MODIFIED_DATE = '2025-11-04' # by RJH
SHORT_PROGRAM_NAME = "convert_OET-LV-RV_USFM_to_VREF"
PROGRAM_NAME = "Convert OET LV & RV USFM files to VREF"
PROGRAM_VERSION = '0.03'
PROGRAM_NAME_VERSION = f'{SHORT_PROGRAM_NAME} v{PROGRAM_VERSION}'

DEBUGGING_THIS_MODULE = False


VREF_STANDARD_InputFilePath = Path( '../../../Bibles/DataSets/Reference systems/AQuA.vref.txt' )
assert VREF_STANDARD_InputFilePath.is_file()

project_folderpath = Path(__file__).parent.parent # Find folders relative to this module
# FG_folderpath = project_folderpath.parent # Path to find parallel Freely-Given.org repos
cleaned_USFM_InputFolderPath = project_folderpath.joinpath( 'derivedTexts/cleanedUSFM/' )
OET_LV_USFM_InputFolderPath = cleaned_USFM_InputFolderPath.joinpath( 'LiteralVersion/' )
OET_RV_USFM_InputFolderPath = cleaned_USFM_InputFolderPath.joinpath( 'ReadersVersion/' )
assert cleaned_USFM_InputFolderPath.is_dir() and OET_LV_USFM_InputFolderPath.is_dir() and OET_RV_USFM_InputFolderPath.is_dir()
VREF_OutputFolderPath = project_folderpath.joinpath( 'derivedTexts/' )
assert VREF_OutputFolderPath.is_dir()
OET_LV_VREF_OutputFilePath = VREF_OutputFolderPath.joinpath( 'OET-LV.vref.txt' )
OET_RV_VREF_OutputFilePath = VREF_OutputFolderPath.joinpath( 'OET-RV.vref.txt' )

def main():
    """
    Main program to handle command line parameters and then run what they want.
    """
    BibleOrgSysGlobals.introduceProgram( __name__, PROGRAM_NAME_VERSION, LAST_MODIFIED_DATE )

    # Load the vref reference file
    # It contains 41,899 USFM references starting with 'GEN 1:1' and ending with 'ENO 42:16'
    with open( VREF_STANDARD_InputFilePath, 'rt', encoding='UTF-8' ) as vrefsFile:
        vrefs = vrefsFile.read().rstrip().split( '\n' )
        assert len(vrefs) == 41_899, f"{len(vrefs)=}"

    # Now convert both USFM Bibles into VPL
    for VV in ('LV','RV'):
        vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"\nProcessing OET-{VV}…" )

        versionAbbreviation = f'OET-{VV}'
        vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"Preloading '{versionAbbreviation}' USFM Bible…" )
        thisBible = USFMBible.USFMBible( OET_RV_USFM_InputFolderPath if VV=='RV' else OET_LV_USFM_InputFolderPath,
                                        givenAbbreviation=versionAbbreviation, encoding='utf-8' )
        thisBible.loadBooks() # So we can iterate through them all below
        vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"preloadVersion() loaded {thisBible}" )

        totalLinesWritten = blankLinesWritten = verseLinesWritten = versificationErrorCount = 0
        with open( OET_RV_VREF_OutputFilePath if VV=='RV' else OET_LV_VREF_OutputFilePath, 'wt', encoding='utf-8' ) as vrefOutputFile:
            for vref in vrefs:
                # print( f"{vref=}" )
                UUU, CV = vref.split( ' ' )
                C,V = CV.split( ':' )
                BBB = BibleOrgSysGlobals.loadedBibleBooksCodes.getBBBFromUSFMAbbreviation( UUU )
                # print( f"{vref=} {UUU=} {BBB=} {C=} {V=}" )

                bcvRef = (BBB, C, V)
                try: result = thisBible.getContextVerseData( bcvRef )
                except KeyError:
                    logging.error( f"Probable versification error with {bcvRef=}" )
                    vrefOutputFile.write( '\n' )
                    versificationErrorCount += 1
                    totalLinesWritten += 1
                    continue
                if result is None:
                    if BBB not in ('TOB','JDT','ESG','WIS','SIR','BAR','LJE','PAZ','SUS','BEL','MA1','MA2','MA3','MA4','GES','LES','MAN','PS2','ODE','PSS','EZA','JUB','ENO'):
                        print( f"Unable to fetch {bcvRef=}" )
                    vrefOutputFile.write( '\n' )
                    blankLinesWritten += 1
                    totalLinesWritten += 1
                    continue
                verseData, _context = result
                #dPrint( 'Quiet', DEBUGGING_THIS_MODULE, "gVT", self.name, BCVReference, verseData )
                assert isinstance( verseData, InternalBibleEntryList )
                #if BibleOrgSysGlobals.debugFlag: assert 1 <= len(verseData) <= 5
                verseText, firstWord = '', False
                for entry in verseData:
                    marker, cleanText = entry.getMarker(), entry.getOriginalText()
                    if marker[0] == '¬': pass # Ignore end markers
                    elif marker == 'c': pass # Ignore
                    elif marker == 'c~': pass # Ignore text after chapter marker
                    elif marker == 'c#': pass # Ignore print chapter number
                    elif marker == 'cl': pass # Ignore cl markers AFTER the '\c 1' marker (the text for the individual chapter/psalm heading)
                    elif marker == 'v=': pass # Ignore the verse number (not to be printed) that the next field(s) (usually a section heading) logically belong together with
                    elif marker == 'd': verseText += '¦' + cleanText + '¦'
                    elif marker in ('list',): pass
                    elif marker in ('rem',): pass
                    elif marker in ('ms1','mr','sr'): pass
                    elif marker in ('s1','s2','s3','r'): pass
                    elif marker in ('b','nb'): pass
                    elif marker in ('sp','qa'): pass
                    elif marker == 'p': verseText = f'{verseText}¶ {cleanText}'
                    elif marker == 'q1': verseText += '₁ ' + cleanText
                    elif marker == 'q2': verseText += '₂ ' + cleanText
                    elif marker == 'q3': verseText += '₃ ' + cleanText
                    elif marker == 'q4': verseText += '₄ ' + cleanText
                    elif marker == 'm': verseText += '§ ' + cleanText
                    elif marker == 'mi': verseText = f'{verseText}{cleanText}'
                    elif marker == 'pi1': verseText = f'{verseText}{cleanText}'
                    elif marker == 'li1': verseText = f'{verseText}{cleanText}'
                    elif marker == 'li2': verseText = f'{verseText}{cleanText}'
                    elif marker == 'v': firstWord = True # Ignore
                    elif marker == 'v~': verseText = f'{verseText}{cleanText}'
                    elif marker == 'p~': verseText = f'{verseText}{cleanText}'
                    elif marker == 'vw':
                        verseText = f"{verseText}{'' if firstWord else ' '}{cleanText}"
                        firstWord = False
                    else: logging.critical( f"InternalBible.getVerseText Unknown marker '{marker}'='{cleanText}'" )
                vrefOutputFile.write( f'{verseText}\n' )
                verseLinesWritten += 1
                totalLinesWritten += 1
        vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"Wrote {totalLinesWritten:,} lines to OET-{VV} file ({verseLinesWritten:,} verses, {versificationErrorCount:,} versification problems, {blankLinesWritten:,} blank)." )
# end of convert_OET-LV-RV_USFM_to_VREF.main



if __name__ == '__main__':
    from multiprocessing import set_start_method, freeze_support
    set_start_method('fork') # The default was changed on POSIX systems from 'fork' to 'forkserver' in Python3.14
    freeze_support() # Multiprocessing support for frozen Windows executables

    # Configure basic Bible Organisational System (BOS) set-up
    parser = BibleOrgSysGlobals.setup( PROGRAM_NAME, PROGRAM_VERSION )
    BibleOrgSysGlobals.addStandardOptionsAndProcess( parser, exportAvailable=False )

    main()

    BibleOrgSysGlobals.closedown( PROGRAM_NAME, PROGRAM_VERSION )
# end of convert_OET-LV-RV_USFM_to_VREF.py
