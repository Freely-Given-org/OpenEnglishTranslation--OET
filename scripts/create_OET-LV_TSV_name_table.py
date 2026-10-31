#!/usr/bin/env -S uv run
# -\*- coding: utf-8 -\*-
# SPDX-FileCopyrightText: © 2023 Robert Hunt <Freely.Given.org+OET@gmail.com>
# SPDX-License-Identifier: MPL-2.0
#
# create_OET-LV_TSV_name_table.py
#
# Create OET-LV names from the OT/NT command tables and DC word table.
#
# Copyright (C) 2025-2026 Robert Hunt
# Author: Robert Hunt <Freely.Given.org+OET@gmail.com>
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Create the shared OET-LV spelling-check names table.

CHANGELOG:
    2024-03-13 Added check for duplicated words
    2025-03-10 Added support for a few more internal USFM markers
    2025-10-10 Added support for (OET) LV & RV names tables
    2026-10-21 Transliterate all NT name alternatives according to their script (including both Greek forms of Obed)
    2026-10-30 Include emitted DC name transliterations and preserve unchanged output timestamps.
    2026-10-31 Report unchanged names tables without claiming that they were written.
"""
from gettext import gettext as _
# from typing import List, Tuple, Optional
from pathlib import Path
from csv import DictReader
# import logging
import re
import os

from BibleOrgSys import BibleOrgSysGlobals
from BibleOrgSys.BibleOrgSysGlobals import vPrint, fnPrint, dPrint
from bible_transliterations import transliterate_Hebrew, transliterate_Greek


LAST_MODIFIED_DATE = '2026-10-31'
SHORT_PROGRAM_NAME = "create_OET-LV_TSV_name_table"
PROGRAM_NAME = "Make OET-LV name table"
PROGRAM_VERSION = '0.23'
PROGRAM_NAME_VERSION = f'{SHORT_PROGRAM_NAME} v{PROGRAM_VERSION}'

DEBUGGING_THIS_MODULE = False


project_folderpath = Path(__file__).parent.parent # Find folders relative to this module
FG_folderpath = project_folderpath.parent # Path to find parallel Freely-Given.org repos

OET_LV_OT_Names_Filepath = Path(__file__).parent / 'ScriptedOTUpdates/restoreNames.commandTable.tsv'
assert OET_LV_OT_Names_Filepath.is_file()
OET_LV_NT_FolderPath = Path(__file__).parent / 'ScriptedVLTUpdates'
assert OET_LV_NT_FolderPath.is_dir()
OET_LV_NT_OT_Filepath = OET_LV_NT_FolderPath.joinpath( 'OTNames.commandTable.tsv' )
OET_LV_NT_NT_Filepath = OET_LV_NT_FolderPath.joinpath( 'NTNames.commandTable.tsv' )
assert OET_LV_NT_OT_Filepath.is_file()
assert OET_LV_NT_NT_Filepath.is_file()
EXPECTED_COMMAND_TABLE_HEADER = 'Tags	IBooks	EBooks	IMarkers	EMarkers	IRefs	ERefs	PreText	SCase	Search	PostText	RCase	Replace	Name	Comment'

OET_LV_NAMES_TSV_OUTPUT_FILEPATH = project_folderpath.joinpath( 'derivedTexts/OET-LV_names_table.tsv' )
OET_LV_NAMES_TSV_HEADER = 'TraditionalName\tLVName'
OET_LV_DC_WORD_TABLE_FILEPATH = project_folderpath / 'derivedTexts/auto_edited_DC_ESFM/OET-LV_DC_word_table.tsv'
DC_NAME_STATUSES = {'name-transliteration', 'name-transliteration-candidate'}

# Globals



def main():
    """
    Main program to handle command line parameters and then run what they want.
    """
    BibleOrgSysGlobals.introduceProgram( __name__, PROGRAM_NAME_VERSION, LAST_MODIFIED_DATE )

    if load_OET_LV_OT_names() and load_OET_LV_NT_names() and load_OET_LV_DC_names():
        create_OET_LV_name_table()
# end of create_OET-LV_TSV_name_table.main


OET_LV_OT_NAMES_SET = set()
def load_OET_LV_OT_names() -> bool:
    """
    Load the names we use from the tsv names table
    """
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 2:
        vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"Loading {OET_LV_OT_Names_Filepath}…" )
    with open( OET_LV_OT_Names_Filepath, 'rt', encoding='utf-8') as inputTSVFile:
        initialTSVLines = inputTSVFile.read().rstrip().split( '\n' )
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 2:
        vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  {len(initialTSVLines):,} lines loaded from {OET_LV_OT_Names_Filepath.name}.\n" )

    # Remove any BOM
    if initialTSVLines[0].startswith("\ufeff"):
        if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 2:
            vPrint( 'Normal', DEBUGGING_THIS_MODULE, "  Handling Byte Order Marker (BOM) at start of TSV file…")
        initialTSVLines[0] = initialTSVLines[0][1:]
    assert initialTSVLines[0] == EXPECTED_COMMAND_TABLE_HEADER

    dict_reader = DictReader(initialTSVLines, delimiter='\t' )
    for n, row in enumerate(dict_reader):
        # Only active Hebrew source-name rules belong in the OT names index.
        if row['Tags'].startswith('#') or 'H' not in row['Tags']: continue
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
        transliteratedHebrewName = transliterate_Hebrew( hebrewName, capitalise_hebrew=lvOTName[0].isupper() )
        OET_LV_OT_NAMES_SET.add( (lvOTName,transliteratedHebrewName) )

    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 2:
        vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Loaded {len(OET_LV_OT_NAMES_SET):,} OET-LV OT name pairs." )
    # print( list(OET_LV_OT_NAMES_SET)[:10]); assert False, "We want to stop here"
    return True
# end of spellCheckEnglish.load_OET_LV_names


OET_LV_NT_NAMES_SET = set()
def load_OET_LV_NT_names() -> bool:
    """
    Load the names we use from the two tsv names tables
    """
    for filepath in (OET_LV_NT_OT_Filepath, OET_LV_NT_NT_Filepath):
        if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 2:
            vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"Loading {filepath}…" )
        with open( filepath, 'rt', encoding='utf-8') as inputTSVFile:
            initialTSVLines = inputTSVFile.read().rstrip().split( '\n' )
        if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 2:
            vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  {len(initialTSVLines):,} lines loaded from {filepath.name}.\n" )

        # Remove any BOM
        if initialTSVLines[0].startswith("\ufeff"):
            if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 2:
                vPrint( 'Normal', DEBUGGING_THIS_MODULE, "  Handling Byte Order Marker (BOM) at start of TSV file…")
            initialTSVLines[0] = initialTSVLines[0][1:]
        assert initialTSVLines[0] == EXPECTED_COMMAND_TABLE_HEADER

        dict_reader = DictReader(initialTSVLines, delimiter='\t' )
        for n, row in enumerate(dict_reader):
            if not row['Search'] or not row['Replace']: continue
            if '\\sup' in row['Replace']: continue

            lvNTName = row['Search'].replace( '¦', '' )
            nameAlternatives = ( row['Replace'].replace( '¦', '' ).replace( '?', '' )
                            .removeprefix( '\\add >ones\\add*_from_' )
                            .removeprefix( 'supporters_of_' )
                            .removeprefix( 'member_of_' )
                            .removeprefix( 'from_' )
                            .removesuffix( '_\\add group_member\\add*' )
                            .removesuffix( '_\\add party_member\\add*' ).removesuffix( '_\\add party\\add*' )
                            .removesuffix( '_\\add sect_member\\add*' ).removesuffix( '_\\add sect\\add*' )
                        )
            # A slash can separate two Greek forms (Obed) or two Hebrew forms
            # inside parentheses (Jodah), so position does not identify language.
            for name in nameAlternatives.split( '/' ):
                name = name.lstrip('(').rstrip(')')
                if not name: continue # e.g., an unknown Hebrew form written as (?)
                if any('\u05d0' <= character <= '\u05ea' for character in name):
                    transliteratedName = transliterate_Hebrew( name, capitalise_hebrew=lvNTName[0].isupper() )
                    OET_LV_OT_NAMES_SET.add( (lvNTName,transliteratedName) )
                else:
                    transliteratedName = transliterate_Greek( name )
                    OET_LV_NT_NAMES_SET.add( (lvNTName,transliteratedName) )

    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 2:
        vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Loaded {len(OET_LV_NT_NAMES_SET):,} OET-LV NT names." )
    # print( list(OET_LV_NT_NAMES_SET)[:10]); assert False, "We want to stop here"
    return True
# end of spellCheckEnglish.load_OET_RV_names


OET_LV_DC_NAMES_SET = set()
def load_OET_LV_DC_names() -> bool:
    """Accept intentional DC transliterations, retaining candidate status in the source table.

    Read the emitted spelling rather than transliterating again or accepting every
    capitalised gloss. A blank traditional name means no mapping has been supplied.
    """
    if not OET_LV_DC_WORD_TABLE_FILEPATH.is_file():
        raise FileNotFoundError(f'Missing DC word table {OET_LV_DC_WORD_TABLE_FILEPATH}; run make LV_DC in scripts/.')
    names = set()
    with OET_LV_DC_WORD_TABLE_FILEPATH.open(encoding='utf-8-sig', newline='') as source:
        reader = DictReader(source, delimiter='\t')
        if not {'Ref', 'OETGlossWords', 'GlossStatus'} <= set(reader.fieldnames or ()):
            raise ValueError(f'Unexpected DC word-table columns in {OET_LV_DC_WORD_TABLE_FILEPATH}')
        for row in reader:
            if row['GlossStatus'] not in DC_NAME_STATUSES:
                continue
            name = row['OETGlossWords']
            if not name or any(c.isspace() or c in '¦_<>⟦⟧' for c in name) or re.search('[\u0370-\u03ff\u1f00-\u1fff]', name):
                raise ValueError(f'Invalid DC name spelling {name!r} at {row["Ref"]} in {OET_LV_DC_WORD_TABLE_FILEPATH}')
            names.add(('', name))
    OET_LV_DC_NAMES_SET.clear()
    OET_LV_DC_NAMES_SET.update(names)
    vPrint('Normal', DEBUGGING_THIS_MODULE, f'  Loaded {len(names):,} OET-LV DC name spellings.')
    return True
# end of create_OET-LV_TSV_name_table.load_OET_LV_DC_names


def create_OET_LV_name_table() -> bool:
    """
    """
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 2:
        vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"Create OET-LV TSV name table…" )

    combinedSet = OET_LV_OT_NAMES_SET | OET_LV_NT_NAMES_SET
    existingSpellings = {name for _, name in combinedSet}
    combinedSet.update(pair for pair in OET_LV_DC_NAMES_SET if pair[1] not in existingSpellings)
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 2:
        vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Have a total of {len(combinedSet):,} OET-LV names." )

    outputText = f'{OET_LV_NAMES_TSV_HEADER}\n' + ''.join(
        f'{engName}\t{origLanguageName}\n' for engName, origLanguageName in sorted(combinedSet))
    # The make target follows the always-checked DC build. Avoid timestamp churn
    # when its input checks find no change to any emitted name.
    if not OET_LV_NAMES_TSV_OUTPUT_FILEPATH.is_file() \
    or OET_LV_NAMES_TSV_OUTPUT_FILEPATH.read_text(encoding='utf-8') != outputText:
        OET_LV_NAMES_TSV_OUTPUT_FILEPATH.write_text(outputText, encoding='utf-8')
        if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 2:
            vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Wrote {len(combinedSet):,} OET-LV names to {OET_LV_NAMES_TSV_OUTPUT_FILEPATH.name}." )
    elif (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 2:
        vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  {OET_LV_NAMES_TSV_OUTPUT_FILEPATH.name} is unchanged ({len(combinedSet):,} OET-LV names); file not rewritten." )
    return True
# end of create_OET-LV_TSV_name_table.spellCheckOET_RV



if __name__ == '__main__':
    # Configure basic Bible Organisational System (BOS) set-up
    parser = BibleOrgSysGlobals.setup( PROGRAM_NAME, PROGRAM_VERSION )
    BibleOrgSysGlobals.addStandardOptionsAndProcess( parser, exportAvailable=False )

    main()

    BibleOrgSysGlobals.closedown( PROGRAM_NAME, PROGRAM_VERSION )
# end of create_OET-LV_TSV_name_table.py
