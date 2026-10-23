#!/usr/bin/env -S uv run
# -\*- coding: utf-8 -\*-
# SPDX-FileCopyrightText: © 2024 Robert Hunt <Freely.Given.org+OET@gmail.com>
# SPDX-License-Identifier: MPL-2.0
#
# convert_OET-LV-RV_USFM_to_VREF.py
#
# Script to convert cleaned OET USFM files to VPL vref.txt files
#
# Copyright (C) 2024-2026 Robert Hunt
# Author: Robert Hunt <Freely.Given.org+OET@gmail.com>
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Script to convert cleaned OET USFM files
    to even more cleaned VPL vref.txt files.

TODO: Doesn't delete the \\rem ESFM headers yet

NOTE: This script doesn't need to remove special ESFM formatting
        because that was already removed when the USFM files were exported


CHANGELOG:
    2026-10-22 Use BOS source profiles for mapped metadata, passages and export/navigation.
    2025-03-31 Adjust input folder
    2026-05-08 Upgraded to bos_books_codes_py
    2026-05-31 Handle (remove) Psalm/Song thematic colouring markers
"""
from pathlib import Path
import logging
import json
from oet_exports import export_passage, native_passages
from BibleOrgSys.Reference.BibleVersificationMappings import get_default_mapping_engine

from BibleOrgSys import BibleOrgSysGlobals
from BibleOrgSys.BibleOrgSysGlobals import vPrint, fnPrint, dPrint
import BibleOrgSys.Formats.USFMBible as USFMBible
from bible_organisational_system import InternalBibleEntryList
import bos_books_codes_py


LAST_MODIFIED_DATE = '2026-10-22' # by RJH
SHORT_PROGRAM_NAME = "convert_OET-LV-RV_USFM_to_VREF"
PROGRAM_NAME = "Convert OET LV & RV USFM files to VREF"
PROGRAM_VERSION = '0.12'
PROGRAM_NAME_VERSION = f'{SHORT_PROGRAM_NAME} v{PROGRAM_VERSION}'

DEBUGGING_THIS_MODULE = False


VREF_STANDARD_InputFilePath = Path(__file__).resolve().parents[3] / 'Bibles/DataSets/Reference systems/AQuA.vref.txt'

project_folderpath = Path(__file__).parent.parent # Find folders relative to this module
# FG_folderpath = project_folderpath.parent # Path to find parallel Freely-Given.org repos
cleaned_USFM_InputFolderPath = project_folderpath.joinpath( 'exportedFiles/cleanedUSFM/' )
OET_LV_USFM_InputFolderPath = cleaned_USFM_InputFolderPath.joinpath( 'LiteralVersion/' )
OET_RV_USFM_InputFolderPath = cleaned_USFM_InputFolderPath.joinpath( 'ReadersVersion/' )
VREF_OutputFolderPath = project_folderpath.joinpath( 'exportedFiles/' )
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
        if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 1:
            vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"\nProcessing OET-{VV}…" )

        versionAbbreviation = f'OET-{VV}'
        if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 1:
            vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"Preloading '{versionAbbreviation}' USFM Bible…" )
        thisBible = USFMBible.USFMBible( OET_RV_USFM_InputFolderPath if VV=='RV' else OET_LV_USFM_InputFolderPath,
                                        givenAbbreviation=versionAbbreviation, encoding='utf-8', versification=versionAbbreviation )
        thisBible.loadBooks() # So we can iterate through them all below
        if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 2:
            vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"preloadVersion() loaded {thisBible}" )

        # AQuA's canonical reference inventory uses BOS original coordinates.
        # Non-canonical books have no OET text and retain their blank slots.
        output = OET_RV_VREF_OutputFilePath if VV == 'RV' else OET_LV_VREF_OutputFilePath
        lines, records, cache = [], [], {}
        for line_number, vref in enumerate(vrefs, 1):
            usfm, cv = vref.split()
            c, v = cv.split(':')
            book = bos_books_codes_py.usfm_abbrev_to_bos_book_code(usfm)
            if book not in BibleOrgSysGlobals.BOOKLIST_66:
                lines.append('')
                continue
            text, record = export_passage(thisBible, 'org', ((book,c,v,None),), cache)
            lines.append(text)
            if record['combined'] or record['native'] != record['requested']:
                records.append(dict(line=line_number, **record))
        # Resolve every passage before replacing either export.
        output.write_text('\n'.join(lines)+'\n', encoding='utf-8')
        output.with_suffix(output.suffix+'.mapping.json').write_text(json.dumps(dict(
            mapping_revision=get_default_mapping_engine().data_revision,
            source_profile=versionAbbreviation, target_profile='org',
            reference_file=str(VREF_STANDARD_InputFilePath), line_count=len(lines),
            combined_policy='Repeat labelled complete passage in each affected slot',
            mappings=records), ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        vPrint('Quiet', DEBUGGING_THIS_MODULE, f'Wrote {len(lines):,} lines to {output}')
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
