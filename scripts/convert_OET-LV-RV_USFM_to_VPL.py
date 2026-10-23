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
    2026-10-22 Use BOS source profiles for mapped metadata, passages and export/navigation.
    2026-09-21 Created from convert_OET-LV-RV_USFM_to_VREF.py
"""
from pathlib import Path
import datetime
import logging
import json
from oet_exports import export_passage, native_passages
from BibleOrgSys.Reference.BibleVersificationMappings import get_default_mapping_engine

from BibleOrgSys import BibleOrgSysGlobals
from BibleOrgSys.BibleOrgSysGlobals import vPrint, fnPrint, dPrint, BOOKLIST_66
import BibleOrgSys.Formats.USFMBible as USFMBible
from bible_organisational_system import InternalBibleEntryList
import bos_books_codes_py


LAST_MODIFIED_DATE = '2026-10-22' # by RJH
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
VREF_OutputFolderPath = project_folderpath.joinpath( 'exportedFiles/VPL1/' )

def main():
    """
    Main program to handle command line parameters and then run what they want.
    """
    BibleOrgSysGlobals.introduceProgram( __name__, PROGRAM_NAME_VERSION, LAST_MODIFIED_DATE )

    # Convert both USFM Bibles into VPL
    for VV in ('LV','RV'):
        versionAbbreviation = f'OET-{VV}'
        if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 1:
            vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"\nProcessing {versionAbbreviation}…" )

        # Ensure that our output folder exists and define our outfile file
        outputFolderpath = VREF_OutputFolderPath #.joinpath( f'{VV}/' )
        outputFolderpath.mkdir( parents=True, exist_ok=True )
        outputFilename = f'{versionAbbreviation}.vpl'
        outputFilepath = outputFolderpath.joinpath( outputFilename )

        if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 1:
            vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"Preloading '{versionAbbreviation}' USFM Bible…" )
        thisBible = USFMBible.USFMBible( OET_RV_USFM_InputFolderPath if VV=='RV' else OET_LV_USFM_InputFolderPath,
                                        givenAbbreviation=versionAbbreviation, encoding='utf-8', versification=versionAbbreviation )
        thisBible.loadBooks() # So we can iterate through them all below
        if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 2:
            vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"preloadVersion() loaded {thisBible}" )

        # Retrieve first, so a missing mapping cannot leave a truncated export.
        rows, records = [], []
        for (book,c,v,suffix), text, record in native_passages(thisBible):
            number = bos_books_codes_py.bos_book_code_to_usfm_num_str(book)
            key = f'{number.zfill(2)}{c.zfill(3)}{v.zfill(3)}{suffix or ""}'
            rows.append(f'{key}\t{text}')
            if record['combined']:
                records.append(dict(key=key, **record))
        header = f'''# language_name:        English
# closest ISO 639-3:    eng
# year_short:           {datetime.datetime.now().year}
# year_long:            {datetime.datetime.now().strftime('%Y-%m-%d')}
# title:                The Open English Translation of the Bible ({versionAbbreviation})
# URL:                  https://OET.Bible
# copyright_short:      © 2010-2026 Freely-Given.org
# copyright_long:       Copyright © 2010–2026 https://Freely-Given.org available under CC-BY-SA licence
# versification:        {versionAbbreviation} (BOS profile)
# combined_passages:    Stored once at first native address; full coverage in mapping sidecar
'''
        outputFilepath.write_text(header+'\n'.join(rows)+'\n', encoding='utf-8')
        outputFilepath.with_suffix('.vpl.mapping.json').write_text(json.dumps(dict(
            mapping_revision=get_default_mapping_engine().data_revision,
            source_profile=versionAbbreviation, target_profile=versionAbbreviation,
            combined_policy='One labelled complete passage at its first native address',
            mappings=records), ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        vPrint('Quiet', DEBUGGING_THIS_MODULE, f'Wrote {len(rows):,} passages to {outputFilepath}')
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
