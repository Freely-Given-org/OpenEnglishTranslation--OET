#!/usr/bin/env -S uv run
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MPL-2.0
#
# remove_word_numbers_from_added_OET-RV_words.py
#
# One-off script to remove OET-RV word numbers (e.g., word¦12345) that have
#   (wrongly) been attached to words that appear inside the plain/straight
#   \add ...\add* spans of the OET-RV ESFM files.
#
# Plain straight \add spans (without a special specification character such as
#   @ # ≈ ≡ * < > & % ? + ^ immediately after the \add) represent words that a
#   translator has ADDED into the English text for clarity.  Since such added
#   words have no OET-LV word number, any word number found inside those spans
#   is an error and should be removed.
#   Those 'added words' spans are written both as '\add ...\add*' and as
#   '\+add ...\+add*', and the two mean exactly the same thing, so we treat them
#   identically.  (Don't confuse '\+add people\+add*' with '\add +the\add*' —
#   the OET-LV uses '\add +the¦1234\add*' for an inserted article that DOES have
#   a word number.)
#
# Words inside the OTHER \add spans (e.g., \add ≈..., \add @..., \add #..., etc.)
#   are rewordings of the original words and may legitimately keep their numbers,
#   so those spans are left untouched.
#
# Copyright (C) 2026 Robert Hunt
# Author: Robert Hunt <Freely.Given.org+OET@gmail.com>
# License: See gpl-3.0.txt
#
# CHANGELOG:
#     2026-09-28 v1.0.1 Also strip numbers out of plain '\+add ...\+add*' spans, which mean
#                        the same as plain '\add ...\add*' spans
#     2026-09-28 v1.0.1 Add '!' to SPECIAL_ADD_CHARS so that '\add !(Name¦1234)\add*' spans
#                        keep their legitimate word numbers (they were being stripped before)

import re
from pathlib import Path

from BibleOrgSys import BibleOrgSysGlobals
from BibleOrgSys.BibleOrgSysGlobals import vPrint, fnPrint
from BibleOrgSys.Formats.ESFMBible import ESFM_WORD_NUMBER_REGEX


LAST_MODIFIED_DATE = '2026-09-28'
SHORT_PROGRAM_NAME = "Remove_word_numbers_from_added_OET-RV_words"
PROGRAM_NAME = "Remove word numbers from OET-RV straight \\add spans"
PROGRAM_VERSION = '1.0.1'
PROGRAM_NAME_VERSION = f'{SHORT_PROGRAM_NAME} v{PROGRAM_VERSION}'

DEBUGGING_THIS_MODULE = False

project_folderpath = Path(__file__).parent.parent
OET_RV_ESFM_FolderPath = project_folderpath.joinpath( 'translatedTexts/ReadersVersion/' )
assert OET_RV_ESFM_FolderPath.is_dir()

# The characters that, if they immediately follow a '\add ', indicate a special
#   rewording span (not a plain 'added word' span).  These spans must be left unchanged.
#   The '!' is essential: '\add !(Israel¦83035)\add*' holds a legitimate word number
#   on a bracketed proper name that was added into the English text.
SPECIAL_ADD_CHARS = '@#≈≡*<>&%?+^!'

# A straight \add span is one where the first character after the space is NOT
#   one of the special characters (nor a backslash, which would be another marker).
#   The '+' prefix of a '\+add ...\+add*' span is optional here (captured as group 1
#   for the opening marker and group 3 for the closing marker) so that both
#   spellings of the 'added words' span are matched.
straightAddSpanRegex = re.compile(
    f'(\\\\\\+?)add ([^{SPECIAL_ADD_CHARS}\\\\][^\\\\]*?)(\\\\\\+?)add\\*' )


def removeNumbersFromStraightAddText( line:str ) -> str:
    """
    Remove every OET-RV word number (e.g., 'word¦12345') that is found inside a
        straight (plain) \\add ...\\add* or \\+add ...\\+add* span in the given line.
    """
    def replacer( match ):
        return f'{match.group(1)}add {ESFM_WORD_NUMBER_REGEX.sub( "", match.group(2) )}{match.group(3)}add*'
    return straightAddSpanRegex.sub( replacer, line )
# end of removeNumbersFromStraightAddText


def main():
    """
    Main program to handle command line parameters and then do the removal.
    """
    BibleOrgSysGlobals.introduceProgram( __name__, PROGRAM_NAME_VERSION, LAST_MODIFIED_DATE )

    totalChangedLines = totalNumbersRemoved = 0
    changedFiles = 0
    for esfmFilepath in sorted( OET_RV_ESFM_FolderPath.iterdir() ):
        if esfmFilepath.suffix != '.ESFM': continue
        with open( esfmFilepath, 'rt', encoding='utf-8' ) as esfmFile:
            originalLines = esfmFile.read().split( '\n' )
        newLines = []
        numChangedLines = numNumbersRemoved = 0
        for line in originalLines:
            newLine = removeNumbersFromStraightAddText( line )
            if newLine != line:
                numChangedLines += 1
                numNumbersRemoved += line.count( '¦' ) - newLine.count( '¦' )
            newLines.append( newLine )
        if numChangedLines:
            changedFiles += 1
            totalChangedLines += numChangedLines
            totalNumbersRemoved += numNumbersRemoved
            vPrint( 'Quiet', DEBUGGING_THIS_MODULE,
                f"  {esfmFilepath.name}: changed {numChangedLines:,} lines "
                f"removing {numNumbersRemoved:,} word numbers." )
            if not BibleOrgSysGlobals.commandLineArguments.dryRun:
                with open( esfmFilepath, 'wt', encoding='utf-8' ) as esfmFile:
                    esfmFile.write( '\n'.join( newLines ) )

    vPrint( 'Normal', DEBUGGING_THIS_MODULE,
           f"\nRemoved {totalNumbersRemoved:,} OET-RV word numbers from {totalChangedLines:,} lines in {changedFiles:,} files." )
# end of remove_word_numbers_from_added_OET-RV_words.main


if __name__ == '__main__':
    parser = BibleOrgSysGlobals.setup( PROGRAM_NAME, PROGRAM_VERSION )
    parser.add_argument( '--dry-run', action='store_true', dest='dryRun', default=False,
                        help='just report what would be changed without writing any files' )
    BibleOrgSysGlobals.addStandardOptionsAndProcess( parser, exportAvailable=False )

    main()

    BibleOrgSysGlobals.closedown( PROGRAM_NAME, PROGRAM_VERSION )
# end of remove_word_numbers_from_added_OET-RV_words.py
