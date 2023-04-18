#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# delete_OET-RV_word_numbers.py
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
Script to delete word numbers out of the OET-RV NT.
    This is usually run if the number of rows in the SR collation table has changed,
        i.e., all of the SR word numbers have moved.

Of course, it will lose any word numbers that have been manually added
    rather than by a script that can reinsert them.

TODO: A better alternative might be one that can add an offset to any word number
        that's above a certain word number.
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


LAST_MODIFIED_DATE = '2023-04-18' # by RJH
SHORT_PROGRAM_NAME = "delete_OET-RV_word_numbers"
PROGRAM_NAME = "Delete word numbers from OET-RV NT"
PROGRAM_VERSION = '0.01'
PROGRAM_NAME_VERSION = '{} v{}'.format( SHORT_PROGRAM_NAME, PROGRAM_VERSION )

DEBUGGING_THIS_MODULE = False


project_folderpath = Path(__file__).parent.parent # Find folders relative to this module
FG_folderpath = project_folderpath.parent # Path to find parallel Freely-Given.org repos
OET_RV_ESFM_FolderPath = project_folderpath.joinpath( 'translatedTexts/ReadersVersion/' )
assert OET_RV_ESFM_FolderPath.is_dir()


numberRegex = re.compile( '¦[1-9][0-9]{0,5}' ) # 1..6 digits
def main():
    """
    Main program to handle command line parameters and then run what they want.
    """
    BibleOrgSysGlobals.introduceProgram( __name__, PROGRAM_NAME_VERSION, LAST_MODIFIED_DATE )

    response = input( "Are you sure you want to delete word numbers from the OET-RV NT? ").upper()
    if not response in ( 'Y', 'YES' ): return

    totalDeletes = numChangedFiles = 0
    for BBB in BOOKLIST_NT27:
        rvESFMFilename = f'OET-RV_{BBB}.ESFM'
        rvESFMFilepath = OET_RV_ESFM_FolderPath.joinpath( rvESFMFilename )
        vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  Loading {rvESFMFilepath}…" )
        with open( rvESFMFilepath, 'rt', encoding='UTF-8' ) as esfmFile:
            rvESFMText = esfmFile.read() # We keep the original (for later comparison)
        adjText, count = numberRegex.subn( '', rvESFMText )
        if count:
            vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"   Deleted {count:,} word numbers from {BBB}." )
            with open( rvESFMFilepath, 'wt', encoding='UTF-8' ) as esfmFile:
                esfmFile.write( adjText ) # We keep the original (for later comparison)
            totalDeletes += count
            numChangedFiles += 1
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"   Deleted {totalDeletes:,} word numbers from {numChangedFiles:,} OET-RV NT files." )
# end of delete_OET-RV_word_numbers.main



if __name__ == '__main__':
    # Configure basic Bible Organisational System (BOS) set-up
    parser = BibleOrgSysGlobals.setup( PROGRAM_NAME, PROGRAM_VERSION )
    BibleOrgSysGlobals.addStandardOptionsAndProcess( parser, exportAvailable=False )

    main()

    BibleOrgSysGlobals.closedown( PROGRAM_NAME, PROGRAM_VERSION )
# end of delete_OET-RV_word_numbers.py
