#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# count_completed_OET-RV_verses.py
#
# Script to connect OET-RV words with OET-LV words that have word numbers.
#
# Copyright (C) 2023-2024 Robert Hunt
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
Every word in the OET-LV has a word number tag suffixed to it,
    which connects it back to / aligns it with the Greek word it is translated from.

This script attempts to deduce how some of those same word are translated in the OET-RV
    and automatically connect them with the same word number tag.

It does have the potential to make wrong connections that will need to be manually fixed
        when the rest of the OET-RV words are aligned,
    but hopefully this script is relatively conservative
        so that the number of wrong alignments is not huge.
"""
from gettext import gettext as _
from typing import List, Tuple, Optional
from pathlib import Path
# from datetime import datetime
# import logging
# import re
import glob
import os.path

if __name__ == '__main__':
    import sys
    sys.path.insert( 0, '../../BibleOrgSys/' )
from BibleOrgSys import BibleOrgSysGlobals
from BibleOrgSys.BibleOrgSysGlobals import vPrint, fnPrint, dPrint
from BibleOrgSys.Bible import Bible
from BibleOrgSys.Internals.InternalBibleInternals import getLeadingInt
from BibleOrgSys.Reference.BibleBooksCodes import BOOKLIST_OT39, BOOKLIST_NT27, BOOKLIST_66
from BibleOrgSys.Reference.BibleOrganisationalSystems import BibleOrganisationalSystem
from BibleOrgSys.Reference.BibleVersificationSystems import BibleVersificationSystem #, BibleVersificationSystems
from BibleOrgSys.Formats.ESFMBible import ESFMBible


LAST_MODIFIED_DATE = '2024-05-13' # by RJH
SHORT_PROGRAM_NAME = "count_completed_OET-RV_verses"
PROGRAM_NAME = "Count completed OET-RV verses"
PROGRAM_VERSION = '0.22'
PROGRAM_NAME_VERSION = '{} v{}'.format( SHORT_PROGRAM_NAME, PROGRAM_VERSION )

DEBUGGING_THIS_MODULE = False


project_folderpath = Path(__file__).parent.parent # Find folders relative to this module
OET_RV_ESFM_InputFolderPath = project_folderpath.joinpath( 'translatedTexts/ReadersVersion/' )
assert OET_RV_ESFM_InputFolderPath.is_dir()

# EN_SPACE = ' '
EM_SPACE = ' '
NARROW_NON_BREAK_SPACE = ' '
BACKSLASH = '\\'


class State:
    """
    A place to store some of the global stuff that needs to be passed around.
    """
    # bvss = BibleVersificationSystems().loadData() # Doesn't reload the XML unnecessarily :)
    # vPrint( 'Quiet', DEBUGGING_THIS_MODULE, bvss ) # Just print a summary
    # vPrint( 'Quiet', DEBUGGING_THIS_MODULE, _("Available system names are: {}").format( bvss.getAvailableVersificationSystemNames() ) )

    vPrint( 'Info', DEBUGGING_THIS_MODULE, "Using 'Original' versification…" )
    # versificationSystem = bvss.getVersificationSystem( 'Original' )
    versificationSystem = BibleVersificationSystem( 'Original' )
# end of State class

state = State()


def main():
    """
    Main program to handle command line parameters and then run what they want.
    """
    BibleOrgSysGlobals.introduceProgram( __name__, PROGRAM_NAME_VERSION, LAST_MODIFIED_DATE )

    finishedOTVerses = finishedNTVerses = finishedVerses = 0
    finishedOTChapters = finishedNTChapters = finishedChapters = 0
    totalOTVerses = totalNTVerses = totalVerses = 0
    totalOTChapters = totalNTChapters = totalChapters = 0

    # Do OT first
    for filename in glob.glob( os.path.join( OET_RV_ESFM_InputFolderPath, 'OET-RV_???.ESFM' ) ):
        BBB = filename[-8:-5]
        if BBB in BOOKLIST_OT39:
            totalBookChapters = state.versificationSystem.getNumChapters( BBB )
            totalOTChapters += totalBookChapters
            totalChapters += totalBookChapters
            totalBookVerses = state.versificationSystem.getTotalNumVerses( BBB )
            totalOTVerses += totalBookVerses
            totalVerses += totalBookVerses
            with open( OET_RV_ESFM_InputFolderPath.joinpath( filename ), 'rt', encoding='utf-8' ) as ESFMFile:
                ESFMText = ESFMFile.read()
            unfinishedCount = ESFMText.count( '◙' )
            finishedVerseCount = totalBookVerses - min( unfinishedCount, totalBookVerses )
            finishedOTVerses += finishedVerseCount
            finishedVerses += finishedVerseCount
            finishedPercentage = finishedVerseCount * 100 // totalBookVerses
            approxFinishedChapters = (finishedPercentage * totalBookChapters + 50) // 100
            finishedOTChapters += approxFinishedChapters
            finishedChapters += approxFinishedChapters
            if unfinishedCount:
                vPrint( 'Info' if finishedVerseCount==0 else 'Normal', DEBUGGING_THIS_MODULE, f"  OET-RV OT {BBB} has {finishedVerseCount:,}/{totalBookVerses:,} = {finishedPercentage}% verses finished (approx. {approxFinishedChapters}/{totalBookChapters} chapters finished)." )
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"OET-RV OT has {finishedOTVerses:,}/{totalOTVerses:,} verses finished = {finishedOTVerses*100//totalOTVerses}%. (Approx {finishedOTChapters:,}/{totalOTChapters:,} = {finishedOTChapters*100//totalOTChapters}% chapters.)\n" )

    # Now do NT
    for filename in glob.glob( os.path.join( OET_RV_ESFM_InputFolderPath, 'OET-RV_???.ESFM' ) ):
        BBB = filename[-8:-5]
        if BBB in BOOKLIST_NT27:
            totalBookChapters = state.versificationSystem.getNumChapters( BBB )
            totalNTChapters += totalBookChapters
            totalChapters += totalBookChapters
            totalBookVerses = state.versificationSystem.getTotalNumVerses( BBB )
            totalNTVerses += totalBookVerses
            totalVerses += totalBookVerses
            with open( OET_RV_ESFM_InputFolderPath.joinpath( filename ), 'rt', encoding='utf-8' ) as ESFMFile:
                ESFMText = ESFMFile.read()
            unfinishedCount = ESFMText.count( '◙' )
            finishedVerseCount = totalBookVerses - min( unfinishedCount, totalBookVerses )
            finishedNTVerses += finishedVerseCount
            finishedVerses += finishedVerseCount
            finishedPercentage = finishedVerseCount * 100 // totalBookVerses
            approxFinishedChapters = (finishedPercentage * totalBookChapters + 50) // 100
            finishedNTChapters += approxFinishedChapters
            finishedChapters += approxFinishedChapters
            if unfinishedCount:
                vPrint( 'Info' if finishedVerseCount==0 else 'Normal', DEBUGGING_THIS_MODULE, f"  OET-RV NT {BBB} has {finishedVerseCount:,}/{totalBookVerses:,} = {finishedPercentage}% verses finished (approx. {approxFinishedChapters}/{totalBookChapters} chapters finished)." )
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"OET-RV NT has {finishedNTVerses:,}/{totalNTVerses:,} verses finished = {finishedNTVerses*100//totalNTVerses}%. (Approx {finishedNTChapters:,}/{totalNTChapters:,} = {finishedNTChapters*100//totalNTChapters}% chapters.)\n" )

    # Now do whole Bible
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"OET-RV has {finishedVerses:,}/{totalVerses:,} verses finished = {finishedVerses*100/totalVerses:.1f}%. (Approx {finishedChapters:,}/{totalChapters:,} = {finishedChapters*100//totalChapters}% chapters.)\n" )
# end of count_completed_OET-RV_verses.main


if __name__ == '__main__':
    # Configure basic Bible Organisational System (BOS) set-up
    parser = BibleOrgSysGlobals.setup( PROGRAM_NAME, PROGRAM_VERSION )
    BibleOrgSysGlobals.addStandardOptionsAndProcess( parser, exportAvailable=False )

    main()

    BibleOrgSysGlobals.closedown( PROGRAM_NAME, PROGRAM_VERSION )
# end of count_completed_OET-RV_verses.py
