#!/usr/bin/env -S uv run
# -\*- coding: utf-8 -\*-
# SPDX-FileCopyrightText: © 2023 Robert Hunt <Freely.Given.org+OET@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later
#
# create_OET-LV_TSV_name_table.py
#
# Script to create TSV table of names for OET-LV from the ScriptedBibleEditor OT & NT command tables.
#
# Copyright (C) 2025 Robert Hunt
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
Script to spell check the Open English Translation of the Bible.

CHANGELOG:
    2024-03-13 Added check for duplicated words
    2025-03-10 Added support for a few more internal USFM markers
    2025-10-10 Added support for (OET) LV & RV names tables
"""
from gettext import gettext as _
# from typing import List, Tuple, Optional
from pathlib import Path
from csv import DictReader
# import logging
import re
import os

import sys
if __name__ == '__main__':
    sys.path.insert( 0, '../../BibleOrgSys/' )
from BibleOrgSys import BibleOrgSysGlobals
from BibleOrgSys.BibleOrgSysGlobals import vPrint, fnPrint, dPrint
# from BibleOrgSys.Bible import Bible
# from BibleOrgSys.Internals.InternalBibleInternals import getLeadingInt
# from BibleOrgSys.Reference.BibleBooksCodes import BOOKLIST_OT39, BOOKLIST_NT27, BOOKLIST_66
# from BibleOrgSys.Formats.ESFMBible import ESFMBible

sys.path.insert( 0, '../../BibleTransliterations/Python/' ) # temp until submitted to PyPI
from BibleTransliterations import load_transliteration_table, transliterate_Hebrew, transliterate_Greek


LAST_MODIFIED_DATE = '2025-10-10' # by RJH
SHORT_PROGRAM_NAME = "create_OET-LV_TSV_name_table"
PROGRAM_NAME = "Make OET-LV name table"
PROGRAM_VERSION = '0.20'
PROGRAM_NAME_VERSION = f'{SHORT_PROGRAM_NAME} v{PROGRAM_VERSION}'

DEBUGGING_THIS_MODULE = False


project_folderpath = Path(__file__).parent.parent # Find folders relative to this module
FG_folderpath = project_folderpath.parent # Path to find parallel Freely-Given.org repos

OET_LV_OT_Names_Filepath = Path( 'ScriptedOTUpdates/restoreNames.commandTable.tsv' )
assert OET_LV_OT_Names_Filepath.is_file()
OET_LV_NT_FolderPath = Path( 'ScriptedVLTUpdates/' )
assert OET_LV_NT_FolderPath.is_dir()
OET_LV_NT_OT_Filepath = OET_LV_NT_FolderPath.joinpath( 'OTNames.commandTable.tsv' )
OET_LV_NT_NT_Filepath = OET_LV_NT_FolderPath.joinpath( 'NTNames.commandTable.tsv' )
assert OET_LV_NT_OT_Filepath.is_file()
assert OET_LV_NT_NT_Filepath.is_file()
EXPECTED_COMMAND_TABLE_HEADER = 'Tags	IBooks	EBooks	IMarkers	EMarkers	IRefs	ERefs	PreText	SCase	Search	PostText	RCase	Replace	Name	Comment'

OET_LV_NAMES_TSV_OUTPUT_FILEPATH = project_folderpath.joinpath( 'intermediateTexts/OET-LV_names_table.tsv' )
assert OET_LV_NAMES_TSV_OUTPUT_FILEPATH.is_file()
OET_LV_NAMES_TSV_HEADER = 'TraditionalName\tLVName'

# Globals



def main():
    """
    Main program to handle command line parameters and then run what they want.
    """
    BibleOrgSysGlobals.introduceProgram( __name__, PROGRAM_NAME_VERSION, LAST_MODIFIED_DATE )

    load_transliteration_table( 'Hebrew' )
    load_transliteration_table( 'Greek' )
    if load_OET_LV_OT_names() and load_OET_LV_NT_names():
        create_OET_LV_name_table()
# end of create_OET-LV_TSV_name_table.main


OET_LV_OT_NAMES_SET = set()
def load_OET_LV_OT_names() -> bool:
    """
    Load the names we use from the tsv names table
    """
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"Loading {OET_LV_OT_Names_Filepath}…" )
    with open( OET_LV_OT_Names_Filepath, 'rt', encoding='utf-8') as inputTSVFile:
        initialTSVLines = inputTSVFile.read().rstrip().split( '\n' )
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  {len(initialTSVLines):,} lines loaded from {OET_LV_OT_Names_Filepath.name}.\n" )

    # Remove any BOM
    if initialTSVLines[0].startswith("\ufeff"):
        vPrint( 'Normal', DEBUGGING_THIS_MODULE, "  Handling Byte Order Marker (BOM) at start of TSV file…")
        initialTSVLines[0] = initialTSVLines[0][1:]
    assert initialTSVLines[0] == EXPECTED_COMMAND_TABLE_HEADER

    dict_reader = DictReader(initialTSVLines, delimiter='\t' )
    for n, row in enumerate(dict_reader):
        if not row['Search'] or not row['Replace']: continue
        if '\\sup' in row['Replace']: continue

        lvOTName = row['Search'].replace( '¦', '' )
        hebrewName = ( row['Replace'].replace( '¦', '' )
                            .removeprefix( '\\add >ones\\add*_from_' )
                            .removeprefix( 'member_of_' )
                            .removeprefix( 'from_' )
                        )
        # print( f"{n} {lvOTName=} {hebrewName=}" )
        if '/' in hebrewName:
            hebrewName = hebrewName.split( '/' )[0]
            # print( f"   {lvOTName=} {hebrewName=}" )
        transliteratedHebrewName = transliterate_Hebrew( hebrewName, capitaliseHebrew=lvOTName[0].isupper() )
        OET_LV_OT_NAMES_SET.add( (lvOTName,transliteratedHebrewName) )

    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Loaded {len(OET_LV_OT_NAMES_SET):,} OET-LV OT name pairs." )
    # print( list(OET_LV_OT_NAMES_SET)[:10]); halt
    return True
# end of spellCheckEnglish.load_OET_LV_names


OET_LV_NT_NAMES_SET = set()
def load_OET_LV_NT_names() -> bool:
    """
    Load the names we use from the two tsv names tables
    """
    for filepath in (OET_LV_NT_OT_Filepath, OET_LV_NT_NT_Filepath):
        vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"Loading {filepath}…" )
        with open( filepath, 'rt', encoding='utf-8') as inputTSVFile:
            initialTSVLines = inputTSVFile.read().rstrip().split( '\n' )
        vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  {len(initialTSVLines):,} lines loaded from {filepath.name}.\n" )

        # Remove any BOM
        if initialTSVLines[0].startswith("\ufeff"):
            vPrint( 'Normal', DEBUGGING_THIS_MODULE, "  Handling Byte Order Marker (BOM) at start of TSV file…")
            initialTSVLines[0] = initialTSVLines[0][1:]
        assert initialTSVLines[0] == EXPECTED_COMMAND_TABLE_HEADER

        dict_reader = DictReader(initialTSVLines, delimiter='\t' )
        for n, row in enumerate(dict_reader):
            if not row['Search'] or not row['Replace']: continue
            if '\\sup' in row['Replace']: continue

            lvNTName = row['Search'].replace( '¦', '' )
            greekName = ( row['Replace'].replace( '¦', '' ).replace( '?', '' )
                            .removeprefix( '\\add >ones\\add*_from_' )
                            .removeprefix( 'supporters_of_' )
                            .removeprefix( 'member_of_' )
                            .removeprefix( 'from_' )
                            .removesuffix( '_\\add group_member\\add*' )
                            .removesuffix( '_\\add party_member\\add*' ).removesuffix( '_\\add party\\add*' )
                            .removesuffix( '_\\add sect_member\\add*' ).removesuffix( '_\\add sect\\add*' )
                        )
            # print( f"{n} {lvNTName=} {greekName=}" )
            if '/' in greekName:
                # assert greekName.count( '/' ) == 1, f"{n} {lvNTName=} {greekName=}" # Fails on Jodah
                greekName, hebrewName = greekName.split( '/' )[:2]
                hebrewName = hebrewName.lstrip('(').rstrip(')')
                # print( f"   {lvNTName=} {greekName=} {hebrewName=}" )
            else: hebrewName = None
            transliteratedGreekName = transliterate_Greek( greekName )
            OET_LV_NT_NAMES_SET.add( (lvNTName,transliteratedGreekName) )
            if hebrewName:
                transliteratedHebrewName = transliterate_Hebrew( hebrewName, capitaliseHebrew=lvNTName[0].isupper() )
                OET_LV_OT_NAMES_SET.add( (lvNTName,transliteratedHebrewName) )

    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Loaded {len(OET_LV_NT_NAMES_SET):,} OET-LV NT names." )
    # print( list(OET_LV_NT_NAMES_SET)[:10]); halt
    return True
# end of spellCheckEnglish.load_OET_RV_names


def create_OET_LV_name_table() -> bool:
    """
    """
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"Create OET-LV TSV name table…" )

    combinedSet = OET_LV_OT_NAMES_SET
    combinedSet.update( OET_LV_NT_NAMES_SET )
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Have a total of {len(combinedSet):,} OET-LV names." )

    with open( OET_LV_NAMES_TSV_OUTPUT_FILEPATH, 'wt', encoding='utf-8' ) as outputFile:
        outputFile.write( f"{OET_LV_NAMES_TSV_HEADER}\n" )
        for engName, origLanguageName in sorted( combinedSet ):
            # print( f"{engName=} {origLanguageName=}" )
            outputFile.write( f"{engName}\t{origLanguageName}\n" )

    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Wrote {len(combinedSet):,} OET-LV names to {OET_LV_NAMES_TSV_OUTPUT_FILEPATH.name}." )
    return True
# end of create_OET-LV_TSV_name_table.spellCheckOET_RV



if __name__ == '__main__':
    # Configure basic Bible Organisational System (BOS) set-up
    parser = BibleOrgSysGlobals.setup( PROGRAM_NAME, PROGRAM_VERSION )
    BibleOrgSysGlobals.addStandardOptionsAndProcess( parser, exportAvailable=False )

    main()

    BibleOrgSysGlobals.closedown( PROGRAM_NAME, PROGRAM_VERSION )
# end of create_OET-LV_TSV_name_table.py
