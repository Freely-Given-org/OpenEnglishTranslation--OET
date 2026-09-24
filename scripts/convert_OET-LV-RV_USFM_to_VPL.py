#!/usr/bin/env -S uv run
# -\*- coding: utf-8 -\*-
# SPDX-FileCopyrightText: © 2024 Robert Hunt <Freely.Given.org+OET@gmail.com>
# SPDX-License-Identifier: MPL-2.0
#
# convert_OET-LV-RV_USFM_to_VPL.py
#
# Script to convert cleaned OET USFM files to VPL vref.txt files
#
# Copyright (C) 2026 Robert Hunt
# Author: Robert Hunt <Freely.Given.org+OET@gmail.com>
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Script to convert cleaned OET USFM files
    to even more cleaned verse-per-line (VPL) files.

TODO: Doesn't delete the \\rem ESFM headers yet

NOTE: This script doesn't need to remove special ESFM formatting
        because that was already removed when the USFM files were exported

Creates a VPL format for the 66 books in a single file for each of the LV and RV like:
    # language_name:        English
    # closest ISO 639-3:    eng
    # year_short:           2026
    # year_long:            2026-09-25
    # title:                The Open English Translation of the Bible (OET) Literal Version (OET-LV)
    # URL:                  https://OET.Bible
    # copyright_short:      © 2010-2026 Freely-Given.org
    # copyright_long:       Copyright © 2010–2026 https://Freely-Given.org available under CC-BY-SA licence

    01001001	The first verse of Genesis (after a tab character).
    01001002	The second verse of Genesis.
    ...

    41001001	The first verse of Matthew.
    ...
    67022021	The last verse of Revelation.

CHANGELOG:
    2026-09-21 Created from convert_OET-LV-RV_USFM_to_VREF.py
"""
from pathlib import Path
import datetime
import logging

from BibleOrgSys import BibleOrgSysGlobals
from BibleOrgSys.BibleOrgSysGlobals import vPrint, fnPrint, dPrint, BOOKLIST_66
import BibleOrgSys.Formats.USFMBible as USFMBible
from bible_organisational_system import InternalBibleEntryList
import bos_books_codes_py


LAST_MODIFIED_DATE = '2026-09-23' # by RJH
SHORT_PROGRAM_NAME = "convert_OET-LV-RV_USFM_to_VPL"
PROGRAM_NAME = "Convert OET LV & RV USFM files to Verse-per-line format"
PROGRAM_VERSION = '0.15'
PROGRAM_NAME_VERSION = f'{SHORT_PROGRAM_NAME} v{PROGRAM_VERSION}'

DEBUGGING_THIS_MODULE = False


project_folderpath = Path(__file__).parent.parent # Find folders relative to this module
# FG_folderpath = project_folderpath.parent # Path to find parallel Freely-Given.org repos
cleaned_USFM_InputFolderPath = project_folderpath.joinpath( 'exportedFiles/cleanedUSFM/' )
OET_LV_USFM_InputFolderPath = cleaned_USFM_InputFolderPath.joinpath( 'LiteralVersion/' )
OET_RV_USFM_InputFolderPath = cleaned_USFM_InputFolderPath.joinpath( 'ReadersVersion/' )
assert cleaned_USFM_InputFolderPath.is_dir() and OET_LV_USFM_InputFolderPath.is_dir() and OET_RV_USFM_InputFolderPath.is_dir()
VREF_OutputFolderPath = project_folderpath.joinpath( 'exportedFiles/VPL1/' )

def main():
    """
    Main program to handle command line parameters and then run what they want.
    """
    BibleOrgSysGlobals.introduceProgram( __name__, PROGRAM_NAME_VERSION, LAST_MODIFIED_DATE )

    # Convert both USFM Bibles into VPL
    for VV in ('LV','RV'):
        versionAbbreviation = f'OET-{VV}'
        vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"\nProcessing {versionAbbreviation}…" )

        # Ensure that our output folder exists and define our outfile file
        outputFolderpath = VREF_OutputFolderPath #.joinpath( f'{VV}/' )
        outputFolderpath.mkdir( parents=True, exist_ok=True )
        outputFilename = f'{versionAbbreviation}.vpl'
        outputFilepath = outputFolderpath.joinpath( outputFilename )

        vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"Preloading '{versionAbbreviation}' USFM Bible…" )
        thisBible = USFMBible.USFMBible( OET_RV_USFM_InputFolderPath if VV=='RV' else OET_LV_USFM_InputFolderPath,
                                        givenAbbreviation=versionAbbreviation, encoding='utf-8' )
        thisBible.loadBooks() # So we can iterate through them all below
        vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"preloadVersion() loaded {thisBible}" )

        totalLinesWritten = blankLinesWritten = verseLinesWritten = versificationErrorCount = 0
        with open( outputFilepath, 'wt', encoding='utf-8' ) as vplOutputFile:
            vplOutputFile.write( f'''# language_name:        English
# closest ISO 639-3:    eng
# year_short:           {datetime.datetime.now().year}
# year_long:            {datetime.datetime.now().strftime('%Y-%m-%d')}
# title:                The Open English Translation of the Bible (OET) {'Literal Version (OET-LV)' if VV=='LV' else 'Readers’ Version (OET-RV)'}
# URL:                  https://OET.Bible
# copyright_short:      © 2010-2026 Freely-Given.org
# copyright_long:       Copyright © 2010–2026 https://Freely-Given.org available under CC-BY-SA licence
''')
            totalLinesWritten += 8

            for BBB in BOOKLIST_66:
                n = bos_books_codes_py.bos_book_code_to_usfm_num_str( BBB )

                vplOutputFile.write( '\n' )
                blankLinesWritten += 1
                totalLinesWritten += 1

                numChapters = thisBible.getNumChapters( BBB )
                for c in range( 1, numChapters+1 ):
                    C = str(c)
                    numVerses = thisBible.getNumVerses( BBB, c )
                    for v in range( 1, numVerses+1 ):
                        V = str(v)

                        bcvRef = (BBB, C, V)
                        try: result = thisBible.getContextVerseData( bcvRef )
                        except KeyError:
                            logging.error( f"Probable versification error with {bcvRef=}" )
                            vplOutputFile.write( '\n' )
                            versificationErrorCount += 1
                            totalLinesWritten += 1
                            continue
                        if result is None:
                            if BBB not in ('TOB','JDT','ESG','WIS','SIR','BAR','LJE','PAZ','SUS','BEL','MA1','MA2','MA3','MA4','GES','LES','MAN','PS2','ODE','PSS','EZA','JUB','ENO'):
                                print( f"Unable to fetch {bcvRef=}" )
                                continue
                        verseData, _context = result
                        #dPrint( 'Quiet', DEBUGGING_THIS_MODULE, "gVT", self.name, BCVReference, verseData )
                        assert isinstance( verseData, InternalBibleEntryList )
                        #if BibleOrgSysGlobals.debugFlag: assert 1 <= len(verseData) <= 5
                        verseText, firstWord = '', False
                        for entry in verseData:
                            marker, cleanText = entry.getMarker(), entry.getOriginalText()
                            if cleanText and VV=='RV' and BBB=='PSA' and '\\z' in cleanText: # Psalm/Song colouring markers
                                cleanText = cleanText.replace( '\\zr ', '' ).replace( '\\z1 ', '' ).replace( '\\z2 ', '' ).replace( '\\z3 ', '' ).replace( '\\z4 ', '' ) \
                                            .replace( '\\zrhilite ', '' ).replace( '\\z1hilite ', '' ).replace( '\\z2hilite ', '' ).replace( '\\z3hilite ', '' ).replace( '\\z4hilite ', '' ) \
                                            .replace( '\\zrhilite*', '' ).replace( '\\z1hilite*', '' ).replace( '\\z2hilite*', '' ).replace( '\\z3hilite*', '' ).replace( '\\z4hilite*', '' )
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
                            elif marker in ('s1','s2','s3','s4','r'): pass
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
                            elif marker == 'vw':
                                verseText = f"{verseText}{'' if firstWord else ' '}{cleanText}"
                                firstWord = False
                            else: logging.critical( f"InternalBible.getVerseText Unknown marker '{marker}'='{cleanText}'" )
                            verseText = verseText.replace( '\\add ', '{' ).replace( '\\add*', '}' )

                        ref = f'{n.zfill(2)}{C.zfill(3)}{V.zfill(3)}'
                        vplOutputFile.write( f'{ref}\t{verseText}\n' )
                        verseLinesWritten += 1
                        totalLinesWritten += 1
        vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"Wrote {totalLinesWritten:,} lines to OET-{VV} file ({verseLinesWritten:,} verses, {versificationErrorCount:,} versification problems, {blankLinesWritten:,} blank)." )
# end of convert_OET-LV-RV_USFM_to_VPL.main



if __name__ == '__main__':
    from multiprocessing import set_start_method, freeze_support
    set_start_method('fork') # The default was changed on POSIX systems from 'fork' to 'forkserver' in Python3.14
    freeze_support() # Multiprocessing support for frozen Windows executables

    # Configure basic Bible Organisational System (BOS) set-up
    parser = BibleOrgSysGlobals.setup( PROGRAM_NAME, PROGRAM_VERSION )
    BibleOrgSysGlobals.addStandardOptionsAndProcess( parser, exportAvailable=False )

    main()

    BibleOrgSysGlobals.closedown( PROGRAM_NAME, PROGRAM_VERSION )
# end of convert_OET-LV-RV_USFM_to_VPL.py
