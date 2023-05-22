#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# OET-LV-RV_ESFM_to_USFM.py
#
# Script to delete word numbers out of the OET-RV NT.
#
# Copyright (C) 2023 Robert Hunt
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
Script to convert OET ESFM files with word numbers back to simple USFM files.

TODO: Doesn't delete the \rem ESFM headers yet
"""
from gettext import gettext as _
from tracemalloc import start
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
from BibleOrgSys.Internals.InternalBibleInternals import getLeadingInt
from BibleOrgSys.Reference.BibleBooksCodes import BOOKLIST_OT39, BOOKLIST_NT27, BOOKLIST_66
from BibleOrgSys.Reference.BibleOrganisationalSystems import BibleOrganisationalSystem
from BibleOrgSys.Formats.ESFMBible import ESFMBible


LAST_MODIFIED_DATE = '2023-05-20' # by RJH
SHORT_PROGRAM_NAME = "OET-LV-RV_ESFM_to_USFM"
PROGRAM_NAME = "Convert OET LV & RV ESFM files to USFM"
PROGRAM_VERSION = '0.04'
PROGRAM_NAME_VERSION = '{} v{}'.format( SHORT_PROGRAM_NAME, PROGRAM_VERSION )

DEBUGGING_THIS_MODULE = False


project_folderpath = Path(__file__).parent.parent # Find folders relative to this module
# FG_folderpath = project_folderpath.parent # Path to find parallel Freely-Given.org repos
OET_LV_ESFM_FolderPath = project_folderpath.joinpath( 'intermediateTexts/auto_edited_VLT_ESFM/' )
OET_RV_ESFM_FolderPath = project_folderpath.joinpath( 'translatedTexts/ReadersVersion/' )
assert OET_LV_ESFM_FolderPath.is_dir() and OET_RV_ESFM_FolderPath.is_dir()
OET_LV_USFM_OutputFolderPath = project_folderpath.joinpath( 'derivedTexts/LiteralVersion_derivedUSFM/' )
OET_RV_USFM_OutputFolderPath = project_folderpath.joinpath( 'derivedTexts/ReadersVersion_derivedUSFM/' )
assert OET_LV_USFM_OutputFolderPath.is_dir() and OET_RV_USFM_OutputFolderPath.is_dir()


ESFMWordNumberRegex = re.compile( '¦[1-9][0-9]{0,5}' ) # 1..6 digits
def main():
    """
    Main program to handle command line parameters and then run what they want.
    """
    BibleOrgSysGlobals.introduceProgram( __name__, PROGRAM_NAME_VERSION, LAST_MODIFIED_DATE )

    for VV in ('LV','RV'):
        vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"Processing {VV} files…" )
        totalWordDeletes = totalESBs = numChangedFiles = 0
        for BBB in BOOKLIST_NT27:
            vvInputFolderpath = OET_LV_ESFM_FolderPath if VV=='LV' else OET_RV_ESFM_FolderPath
            vvESFMFilename = f'OET-{VV}_{BBB}.ESFM'
            vvESFMFilepath = vvInputFolderpath.joinpath( vvESFMFilename )
            vvOutputFolderpath = OET_LV_USFM_OutputFolderPath if VV=='LV' else OET_RV_USFM_OutputFolderPath
            Uuu = BibleOrgSysGlobals.loadedBibleBooksCodes.getUSFMAbbreviation( BBB )
            vvUSFMFilename = f'OET-{VV}_{Uuu}.USFM'
            vvUSFMFilepath = vvOutputFolderpath.joinpath( vvUSFMFilename )
            vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  Loading {vvESFMFilepath}…" )
            with open( vvESFMFilepath, 'rt', encoding='UTF-8' ) as esfmFile:
                vvESFMText = esfmFile.read() # We keep the original (for later comparison)
            adjText, wordDeleteCount = ESFMWordNumberRegex.subn( '', vvESFMText )
            esbCount = 0
            if VV == 'LV': # remove LV specialised version of USFM \\add fields
                adjText = adjText.replace( '\\add +', '\\add ' ) \
                                .replace( '\\add -', '\\add ' ) \
                                .replace( '\\add =', '\\add ' ) \
                                .replace( '\\add ~', '\\add ' ) \
                                .replace( '\\add >', '\\add ' ) \
                                .replace( '\\add ^', '\\add ' )
                adjText = adjText.replace( '\\add -\\add*', '' ) # Remove those added hyphens
            elif VV == 'RV': # Turn section headings into USFM Extended Study Content sidebars
                # See https://ubsicap.github.io/usfm/master/notes_study/sidebars.html
                inESB = False
                # newLines = []
                # for line in adjText.split( '\n' ):
                #     if line.startswith( '\\s1 ' ):
                #         assert not inESB
                #         newLines.append( '\\esb \\cat s1\\cat*' )
                #         newLines.append( line )
                #         inESB = True
                #         esbCount += 1
                #     elif not line.startswith( '\\r ' ):
                #         if inESB:
                #             newLines.append( '\\esbe' )
                #             inESB = False
                #         newLines.append( line )
                #     else:
                #         newLines.append( line )
                # assert not inESB
                # adjText = '\n'.join( newLines )
            if wordDeleteCount or esbCount or adjText!=vvESFMText:
                if esbCount:
                    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"      Added {esbCount:,} sidebar markers to {BBB} (for OET-RV section headings)." )
                vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"      Deleted {wordDeleteCount:,} word numbers from {BBB}." )
                vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"    Writing {vvUSFMFilepath}…" )
                with open( vvUSFMFilepath, 'wt', encoding='UTF-8' ) as usfmFile:
                    usfmFile.write( adjText ) # We keep the original (for later comparison)
                totalWordDeletes += wordDeleteCount
                totalESBs += esbCount
                numChangedFiles += 1
        if totalESBs:
            vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f" Added {totalESBs:,} total sidebar markers." )
        vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f" Deleted {totalWordDeletes:,} word numbers from {numChangedFiles:,} OET-{VV} NT files." )
# end of OET-LV-RV_ESFM_to_USFM.main



if __name__ == '__main__':
    # Configure basic Bible Organisational System (BOS) set-up
    parser = BibleOrgSysGlobals.setup( PROGRAM_NAME, PROGRAM_VERSION )
    BibleOrgSysGlobals.addStandardOptionsAndProcess( parser, exportAvailable=False )

    main()

    BibleOrgSysGlobals.closedown( PROGRAM_NAME, PROGRAM_VERSION )
# end of OET-LV-RV_ESFM_to_USFM.py
