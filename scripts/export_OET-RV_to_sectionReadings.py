#!/usr/bin/env -S uv run
# -\*- coding: utf-8 -\*-
# SPDX-License-Identifier: GPL-3.0-or-later
#
# convert_OET-RV_to_sectionReadings.py
#
# Script to convert OET-RV ESFM files to text files suitable for TTS processing.
#
# Copyright (C) 2026 Robert Hunt
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
Script to convert OET-RV ESFM files to text files suitable for TTS processing.


CHANGELOG:
    2026-02-24 Switched from PiperTTS to much better quality online GoogleTTS
    2026-02-26 Copy ogg files straight into Radio folder
"""
from pathlib import Path
import os, os.path
import re
import random
from time import sleep
import subprocess
import shutil
import logging

if __name__ == '__main__':
    import sys
    sys.path.insert( 0, '../../BibleOrgSys/' )
from BibleOrgSys import BibleOrgSysGlobals
from BibleOrgSys.BibleOrgSysGlobals import vPrint, fnPrint, dPrint
from BibleOrgSys.Reference.BibleBooksCodes import BOOKLIST_OT39, BOOKLIST_NT27, BOOKLIST_66, BOOKLIST_88
import BibleOrgSys.Formats.ESFMBible as ESFMBible
from BibleOrgSys.Bible import Bible
from BibleOrgSys.Internals.InternalBibleInternals import InternalBibleEntryList, getLeadingInt


LAST_MODIFIED_DATE = '2026-02-27' # by RJH
SHORT_PROGRAM_NAME = "convert_OET-RV_to_sectionReadings"
PROGRAM_NAME = "Convert OET-RV to section readings"
PROGRAM_VERSION = '0.38'
PROGRAM_NAME_VERSION = f'{SHORT_PROGRAM_NAME} v{PROGRAM_VERSION}'

DEBUGGING_THIS_MODULE = False


TEST_MODE_FLAG = False
BOOKS_TO_LOAD = ['RUT'] if TEST_MODE_FLAG else ['ALL']
MAKE_AUDIO_FILES = True # If false, only creates the text files (by section)
USE_PIPER_FLAG = False # If false, uses GoogleTTS

project_folderpath = Path(__file__).parent.parent # Find folders relative to this module
OET_RV_ESFM_FolderPath = project_folderpath.joinpath( 'translatedTexts/ReadersVersion/' )
assert OET_RV_ESFM_FolderPath.is_dir()
NORMAL_OUTPUT_FOLDER_PATH = project_folderpath.joinpath( 'derivedTexts/OET-RV_sectionReadings/' )
assert NORMAL_OUTPUT_FOLDER_PATH.is_dir()
OGG_OUTPUT_FOLDER_PATH = Path( '/mnt/SSDs/Radio/RadioData/OET/' )
assert OGG_OUTPUT_FOLDER_PATH.is_dir()

PIPER_MODEL_NAME = 'en_GB-jenny_dioco-medium'
PIPER_MODEL_PATH = f'../derivedTexts/OET-RV_sectionReadings/{PIPER_MODEL_NAME}.onnx'
assert Path(PIPER_MODEL_PATH).is_file()

"""
Core English Dialects
RegionTLD (--tld)Character / "Vibe"
New Zealand co.nz The local choice for Marton; sounds familiar and neighborly.
Australia com.au Similar to NZ but with slightly different vowel shifts.
United Kingdom co.uk Very "proper" and formal; perfect for Scripture readings.
United States com The standard "General American" default.
Canada ca Similar to the US but with distinct regional rounding of vowels.
India co.in Excellent for clarity; very precise and rhythmic enunciation.
Ireland ie Lyrical and warm; great for a "softer" segments.
South Africa co.za A unique blend of British and Dutch-influenced inflections.
Nigeria com.ng Clear, energetic, and distinct African-English rhythm."""
BBB_DICT = { # The book name to be pronounced, and then the accent TLD (if GoogleTTS is used)
        # 'GEN':('Genesis', 'com.ng'),
        # 'EXO':('Exodus', 'co.nz'),
        # 'RUT':('Ruth', 'ie'),
        # 'SA1':('first Samuel', 'co.nz'),
        # 'SA2':('second Samuel', 'co.nz'),
        # 'KI1':('first kings', 'co.nz'),
        # 'KI2':('second kings', 'co.nz'),
        # 'PSA':('Song', 'co.nz'),
        # 'JNA':('Jonah or Yonah', 'ie'),
        # 'MAT':('Matthew', 'com.au'),
        # 'MRK':('Mark', 'co.uk'),
        # 'LUK':('Luke', 'ca'),
        # 'JHN':('John or Yohan', 'co.in'),
        # 'ACT':('Acts', 'com'),
        # 'REV':('Revelation', 'co.za'),
        }
THINGS_TO_REMOVE = ( # Don't include \\add here because they get special treatment
    '\\add*','\\+add*', '\\bd ','\\bd*', '\\bk ','\\bk*', '\\em ','\\em*', '\\+em ','\\+em*', '\\it ','\\it*', '\\nd ','\\nd*', '\\+nd ','\\+nd*', '\\wj ','\\wj*',

    # After word numbers have been removed
    # TODO: Could/Should we just use a regex to delete these names?
    '(Aaron)','(Adam)'
    '(Bethlehem)',
    '(Cyrus)',
    '(Darius)',
    '(Elijah)',
    '(Gaza)','(Gomorrah)',
    '(Heb. Mitsrayim)','(Heb. Shomron)','(Hezekiah)','(Hosea)',
    '(Isaac)','(Isaiah)','(Israel)',
    '(Jacob)','(James)',
        '(Jeremiah)','(Jericho)','(Jesse)','(Jezebel)',
        '(Jonathan)','(Jordan)','(Joshua)','(Josiah)',
        '(Judah)',
    '(Manasseh)','(Moses)',
    '(Pharaoh)',
    '(Samaria)','(Simeon)','(Solomon)',
    '(Tyre)',
    '(Zion)',
)
ADD_THINGS_TO_REMOVE = ( '?≈','≈', '=', '+', '#', '*', '&', '?@','@', '≡', '<', '>', '^', '→', '?', '' )

PICKLE_FILENAME_END = '.OBD_Bible.pickle'

preloadedBible = None
sectionsLists = {}


def main():
    """
    Main program to handle command line parameters and then run what they want.
    """
    BibleOrgSysGlobals.introduceProgram( __name__, PROGRAM_NAME_VERSION, LAST_MODIFIED_DATE )

    if load_OET_RV():
        if createOETSectionLists():
            totalSectionsWritten = numBooksProcessed = 0
            for BBB in preloadedBible.books:
                if (BBB in BOOKS_TO_LOAD or BOOKS_TO_LOAD==['ALL']) \
                and BBB in BBB_DICT:
                    totalSectionsWritten += processBook( BBB )
                    numBooksProcessed += 1
                    if USE_PIPER_FLAG is False and BBB != list(BBB_DICT)[-1]: # Not the last book to process
                        vPrint( 'Normal', DEBUGGING_THIS_MODULE, "Having a rest between Bible books for gTTS bandwidth…" )
                        sleep( 1000 ) # Delay between books
            vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"Wrote {totalSectionsWritten:,} section {'file sets' if MAKE_AUDIO_FILES else 'text files'} for {numBooksProcessed} book(s): {BOOKS_TO_LOAD}." )
# end of convert_OET-RV_to_sectionReadings.main


def load_OET_RV() -> bool:
    """
    Docstring for load_OET_RV
    
    :return: Description
    :rtype: bool
    """
    global preloadedBible

    # See if a pickled version is available for a MUCH faster load time
    pickleFilename = f"OET-RV__{'_'.join(BOOKS_TO_LOAD)}{PICKLE_FILENAME_END}" \
                        if TEST_MODE_FLAG \
                        else f'OET-RV{PICKLE_FILENAME_END}'
    pickleFolderPath = OET_RV_ESFM_FolderPath if OET_RV_ESFM_FolderPath.is_dir() else OET_RV_ESFM_FolderPath.parent
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"\nLooking for {f"'{pickleFilename}'" if BibleOrgSysGlobals.verbosityLevel>1 else 'pickle'} file for ‘OET-RV’{f' in {pickleFolderPath}/' if BibleOrgSysGlobals.verbosityLevel>2 else ''} …" )
    pickleFilePath = pickleFolderPath.joinpath( pickleFilename )
    dPrint( 'Never', DEBUGGING_THIS_MODULE, f"{OET_RV_ESFM_FolderPath=} {pickleFilename=} {pickleFolderPath=} {pickleFilePath=}" )
    if pickleFilePath.is_file():
        pickleIsObsolete = False
        pickleMTime = pickleFilePath.stat().st_mtime # A large integer
        dPrint( 'Info', DEBUGGING_THIS_MODULE, f"preloadVersions found {pickleFilename=}" )
        for somePath in pickleFolderPath.iterdir():
            dPrint( 'Never', DEBUGGING_THIS_MODULE, f"{pickleFolderPath=} {somePath=} {type(somePath)=}" )
            if somePath.is_file() and not str(somePath).endswith( PICKLE_FILENAME_END ):
                fileMTime = somePath.stat().st_mtime # A large integer
                if fileMTime > pickleMTime:
                    pickleIsObsolete = True
                    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"OET-RV pickle is obsolete because {somePath.name} is more recent." )
                    break
            else:
                dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"Ignoring pickle file or folder {somePath=} {somePath.name=}")
        if not pickleIsObsolete:
            try:
                newBibleObj = BibleOrgSysGlobals.unpickleObject( pickleFilename, pickleFolderPath )
                # dPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"newObj is {newBibleObj}" )
                # dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  Loaded OET-RV {type(newBibleObj)} pickle file: {pickleFilename}." )
                vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"preloadVersions() loaded pickled {newBibleObj if BibleOrgSysGlobals.verbosityLevel>=2 else 'OET-RV'}" )
                assert 'discoveryResults' in newBibleObj.__dict__ # .discover() should have been called before it was saved
                preloadedBible = newBibleObj
                return True
            except EOFError:
                logging.critical( f"Failed to load OET-RV pickle file: Ran out of input from {pickleFilename} in {pickleFolderPath}")
                return False
    else:
        vPrint( 'Normal', DEBUGGING_THIS_MODULE, "  No pickle file for OET-RV." )
        vPrint( 'Normal', DEBUGGING_THIS_MODULE, "Preloading OET-RV ESFM Bible…" )
        thisBible = ESFMBible.ESFMBible( OET_RV_ESFM_FolderPath, givenName='Open English Translation—Readers’ Version (2030)', givenAbbreviation='OET-RV' )
        thisBible.loadAuxilliaryFiles = True
        # if versionAbbreviation in ('ULT','UST','UHB','UGNT','SR-GNT'):
        #     thisBible.uWencoded = True # TODO: Shouldn't be required ???
        if 'ALL' in BOOKS_TO_LOAD:
            thisBible.loadBooks() # So we can iterate through them all later
        else: # only load the specific books as we need them
            thisBible.preload()
            for BBB in BOOKS_TO_LOAD:
                thisBible.loadBookIfNecessary( BBB )
            thisBible.lookForAuxilliaryFilenames()

        if BOOKS_TO_LOAD != ['ALL']:
            # Remove unwanted books in this Bible
            if len(thisBible) > len(BOOKS_TO_LOAD):
                vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"Reducing {thisBible.abbreviation} {len(thisBible)} books down to {len(BOOKS_TO_LOAD)}…" )
                newBooks = {}
                for BBB,bookObject in thisBible.books.items():
                    if BBB in BOOKS_TO_LOAD:
                        newBooks[BBB] = bookObject
                thisBible.books = newBooks
            assert len(thisBible) 

        vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"\nDoing discovery for {thisBible.abbreviation} ({thisBible.name}) with {len(thisBible)} books…" )
        thisBible.discover()
        assert 'discoveryResults' in thisBible.__dict__
        preloadedBible = thisBible

        pickleFilename = f"OET-RV__{'_'.join(BOOKS_TO_LOAD)}{PICKLE_FILENAME_END}" \
                            if TEST_MODE_FLAG \
                            else f'OET-RV{PICKLE_FILENAME_END}'
        try: pickleFolderPath = OET_RV_ESFM_FolderPath if os.path.isdir( OET_RV_ESFM_FolderPath ) else Path( OET_RV_ESFM_FolderPath ).parent
        except TypeError:
                assert versionAbbreviation == 'MSB'
                pickleFolderPath = OET_RV_ESFM_FolderPath[0]
        thisBible.pickle( pickleFilename, pickleFolderPath )
        vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Saved pickle file: {pickleFilename}." )
        return True

    logging.critical( f"Failed to load OET-RV from {OET_RV_ESFM_FolderPath}" )
    return False
# end of convert_OET-RV_to_sectionReadings.load_OET_RV


def createOETSectionLists() -> bool:
    """
    Make our list of section headings
       The BibleOrgSys section index already contains a list of sections
    """
    global sectionsLists

    preloadedBible.makeSectionIndex() # These aren't made automatically

    sectionsLists = {}
    sectionsLists['OET-RV'] = {}
    for BBB in preloadedBible.books:
        if not preloadedBible[BBB]._SectionIndex: # no sections in this book, e.g., FRT
            continue

        # Now create the main sections list for this book
        bkObject = preloadedBible[BBB]
        sectionsLists['OET-RV'][BBB] = []
        for n,(startCV, sectionIndexEntry) in enumerate( bkObject._SectionIndex.items() ):
            startC,startV = startCV
            # if additionalSectionHeadingsDict: print( f"{startCV=} {startC}:{startV}" )
            endC,endV = sectionIndexEntry.getEndCV()
            # if additionalSectionHeadingsDict: print( f"End {endC}:{endV}" )
            sectionName, reasonMarker = sectionIndexEntry.getSectionNameReason()
            sectionName = ( sectionName.replace( "'", "’" ) # Replace apostrophes
                        # Remove Psalm book headings
                        .replace( 'First collection/', '' ).replace( 'Second collection/', '' ).replace( 'Third collection/', '' ).replace( 'Fourth collection/', '' ).replace( 'Fifth collection/', '' )
                        )
            sectionFilename = f'{BBB}_S{n}'
            rvVerseEntryList, rvContextList = bkObject._SectionIndex.getSectionEntriesWithContext( startCV )
            # Check that we don't have any duplicated verses in the section
            lastV = None
            for entry in rvVerseEntryList:
                marker, text = entry.getMarker(), entry.getFullText()
                # dPrint( 'Info', DEBUGGING_THIS_MODULE, ( f"createOETSectionLists {marker}={text}" )
                if marker == 'v':
                    assert text != lastV, f"OET-RV {BBB} {startCV=} {text=} {lastV=}"
                    lastV = text
            sectionsLists['OET-RV'][BBB].append( (n,startC,startV,endC,endV,sectionName,rvContextList,rvVerseEntryList,sectionFilename) )
        # Handle left-over additions
        assert len(sectionsLists['OET-RV'][BBB]) >= len(bkObject._SectionIndex), f"{BBB}: {len(sectionsLists['OET-RV'][BBB])=} {len(bkObject._SectionIndex)=}"

    return True
# end of createSectionPages.createOETSectionLists


ESFM_WORD_NUMBER_REGEX = re.compile( '¦[1-9][0-9]{0,5}' ) # 1..6 digits
def processBook( BBB:str ) -> int:
    """
    Docstring for processBook
    
    :param BBB: Description
    :type BBB: str
    :return: Description
    :rtype: int
    """
    bookFolder = NORMAL_OUTPUT_FOLDER_PATH.joinpath( f'{BBB}/' )
    try: os.makedirs( bookFolder )
    except FileExistsError: pass # they were already there
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"    Processing {BBB} into {bookFolder}…" )

    count = 0
    for n,startC,startV,endC,endV,sectionName,_contextList,verseEntryList,sectionFilename in sectionsLists['OET-RV'][BBB]:
        # if n<62: continue
        if startC == '-1': continue # Not interested in introductions
        # print( f"{n=} {startC=} {startV=} {endC=} {endV=} {sectionName=} {_contextList=} {verseEntryList=} {sectionFilename=}" )
        if endC == '?': # Then these are the OET-RV additional/alternative headings
            assert endV == '?'
            continue
        if sectionName.startswith( 'Psalms '):
            # print( f"{thisBible.abbreviation} {sectionName=}" )
            sectionName = sectionName.replace( 'Psalms', 'Song' )

        endBit = endV if endC==startC else f'{endC}:{endV}'
        reference = f'chapter {startC} verse {startV}' if endC==startC and endV==startV else f'{startC} {startV} to {endBit}' # Colon gets pronounced
        introductionString = f"{random.choice(['Now','Right now','Ok, now','Next','Coming next,','Today','Here'])} we have a " \
                        f"{'very short reading' if reference.startswith('chapter') else 'preliminary reading of a section'} " \
                        f"from the Readers Version, of the Open English Translation of the Bible, {BBB_DICT[BBB][0]} {reference}."
        headingString = f"The section heading is: {sectionName}."
        tailingString = f"That preliminary reading was from {BBB_DICT[BBB][0]} {reference}. Learn more about the ‘Open English Translation’ online at O E T dot Bible."

        verseText = ''
        for velIndex, entry in enumerate( verseEntryList ):
            marker = entry.getMarker()
            # rest = entry.getCleanText() # getText() has notes and formatting removed, but still has word numbers
            rest = entry.getAdjustedText() # getText() has notes and cross-referencing removed, but still has character formats and word numbers
            # print( f"{marker=} {rest=}" )
            if marker == 'p' and verseText:
                verseText = f'{verseText}\n\n'
            elif marker in ('v~','p~'):
                verseText = f'{verseText} {rest}' # We don't worry here about extra spaces here
        verseText = ESFM_WORD_NUMBER_REGEX.sub( '', verseText )
        for someString in THINGS_TO_REMOVE:
            verseText = verseText.replace( someString, '' ) # Leaves any surrounding spaces behind
        for someCharacters in ADD_THINGS_TO_REMOVE:
                verseText = verseText.replace( f'\\add {someCharacters}', '' ) \
                                    .replace( f'\\+add {someCharacters}', '' ) # Leaves any surrounding spaces behind
        verseText = (verseText.replace( '  ', ' ' )
                     .replace( ' ,', ',' ).replace( ' .', '.' )
                     .replace( '\n ','\n' )
                     .strip()
                    )
        # print( f"Final {BBB} {reference} verse text: {verseText}" )
        assert '\\' not in verseText, f"Backslash in final {BBB} {reference} verse text: {verseText}"
        for someCharacters in ADD_THINGS_TO_REMOVE:
            if someCharacters:
                assert f' {someCharacters}' not in verseText, f"Unexpected {someCharacters} character(s) in final {BBB} {reference} verse text: {verseText}"
        outputText = f"{introductionString}\n{headingString}\n\n\n{verseText}\n\n\n{tailingString}\n"

        print( f"      Creating text file {n}/{len(sectionsLists['OET-RV'][BBB])} {sectionFilename}.v{PROGRAM_VERSION}.txt ({startC}:{startV}–{f'{endC}:' if endC!=startC else ''}{endV})…" )
        with open( bookFolder.joinpath(f'{sectionFilename}.v{PROGRAM_VERSION}.txt'), 'wt', encoding='utf-8' ) as outputFile:
            outputFile.write( f'{outputText}\n' )

        if MAKE_AUDIO_FILES:
            if USE_PIPER_FLAG:
                OGG_filename = convertToOggWithPiper( BBB, sectionFilename )
            else:
                OGG_filename = convertToOggWithGoogle( BBB, sectionFilename, outputText )
            # Copy the Ogg file to the Radio folder
            shutil.copy2( bookFolder.joinpath( OGG_filename ), OGG_OUTPUT_FOLDER_PATH )

        count += 1

    return count
# end of convert_OET-RV_to_sectionReadings.processBook


def convertToOggWithPiper( BBB:str, sectionFilename:str ):
    """
    Convert to wav using PiperTTS and then a Vorbis (not Opus) ogg file using ffmpeg
    """
    print("        Generating speech with Piper TTS…")

    WAV_filepath = f'../derivedTexts/OET-RV_sectionReadings/{BBB}/{sectionFilename}.{PIPER_MODEL_NAME}.wav'
    OGG_filename = f'{sectionFilename}.{PIPER_MODEL_NAME}.ogg'
    OGG_filepath = f'../derivedTexts/OET-RV_sectionReadings/{BBB}/{OGG_filename}'
    MP3_filepath = f'../derivedTexts/OET-RV_sectionReadings/{BBB}/{sectionFilename}.{PIPER_MODEL_NAME}.mp3'

    # 1. Run Piper via uv
    # We use a list for arguments to handle spaces and paths safely
    piper_cmd = [
        "uv", "run", 
        "--with", "piper-tts", 
        "--with", "pathvalidate", 
        "piper", 
        "--model", PIPER_MODEL_PATH, 
        "--input_file", f'../derivedTexts/OET-RV_sectionReadings/{BBB}/{sectionFilename}.v{PROGRAM_VERSION}.txt', 
        "--output_file", WAV_filepath
    ]

    try:
        subprocess.run(piper_cmd, check=True)

        # 2. Run FFmpeg to convert WAV to OGG (Vorbis)
        # -y overwrites existing files; -q:a 5 is high quality
        # loudnorm=I=-16 targets a standard 'integrated loudness' for radio
        ffmpeg_cmd = [
            "ffmpeg", "-y", 
            "-i", WAV_filepath, 
            "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
            "-c:a", "libvorbis", 
            "-q:a", "5", 
            OGG_filepath
        ]

        print("        Normalizing to Broadcast Standards (EBU R128) & converting to Ogg Vorbis for Pygame/Radio…")
        subprocess.run(ffmpeg_cmd, check=True, capture_output=True)

        # 3. Also convert the WAV to MP3
        # -y: overwrite if exists
        # -af: audio filter (loudnorm for radio consistency)
        # -c:a: audio codec
        # -b:a: bitrate (192k is excellent for voice)
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-i", WAV_filepath,
            "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
            "-c:a", "libmp3lame",
            "-b:a", "192k",
            MP3_filepath
        ]

        try:
            print(f"        Normalizing and converting to {OGG_filepath}…")
            subprocess.run(ffmpeg_cmd, check=True, capture_output=True)
            print("Done!")
        except subprocess.CalledProcessError as e:
            print(f"FFmpeg failed: {e.stderr.decode()}")

        # 4. Cleanup intermediate WAV
        os.remove( WAV_filepath )

        print(f"        Success! Created: {OGG_filepath} (and .mp3)")

    except subprocess.CalledProcessError as e:
        print(f"Error during processing: {e}")
    except FileNotFoundError:
        print("Error: Ensure 'uv' and 'ffmpeg' are installed on your system.")

    return OGG_filename
# end of convert_OET-RV_to_sectionReadings.convertToOggWithPiper


def convertToOggWithGoogle( BBB:str, sectionFilename:str, textToSpeak:str ):
    """
    Convert to wav using GoogleTTS and then a Vorbis (not Opus) ogg file using ffmpeg
    """
    print("        Generating speech with online Google TTS…")

    accent_tld = BBB_DICT[BBB][1]

    WAV_filepath = f'../derivedTexts/OET-RV_sectionReadings/{BBB}/{sectionFilename}.en_{accent_tld}.wav'
    OGG_filename = f'{sectionFilename}.en_{accent_tld}.ogg'
    OGG_filepath = f'../derivedTexts/OET-RV_sectionReadings/{BBB}/{OGG_filename}'
    MP3_filepath = f'../derivedTexts/OET-RV_sectionReadings/{BBB}/{sectionFilename}.en_{accent_tld}.mp3'


    # 1. Generate speech with gTTS
    # Added --lang and --tld flags
    gtts_cmd = [
        "uv", "run", "--with", "gTTS", "gtts-cli",
        textToSpeak,
        "--lang", 'en',
        "--tld", accent_tld,
        "--output", MP3_filepath
    ]

    try:
        print(f"        Using online GoogleTTS via gtts-cli: fetching en ‘{accent_tld}’ audio…")
        subprocess.run(gtts_cmd, check=True)

        # 2. Convert & Normalize
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-i", MP3_filepath,
            "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
            "-c:a", "libvorbis",
            "-q:a", "5",
            OGG_filepath
        ]

        print("        Normalizing to Broadcast Standards (EBU R128) & converting to Ogg Vorbis for Pygame/Radio…")
        subprocess.run(ffmpeg_cmd, check=True, capture_output=True)

        # os.remove(f'../derivedTexts/OET-RV_sectionReadings/{BBB}/{sectionFilename}.mp3')

        print(f"        Success! Created: {MP3_filepath} and .ogg")

        sleep( 50 ) # So don't get rate limited

    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")

    return OGG_filename
# end of convert_OET-RV_to_sectionReadings.convertToOggWithGoogle


if __name__ == '__main__':
    from multiprocessing import set_start_method, freeze_support
    set_start_method('fork') # The default was changed on POSIX systems from 'fork' to 'forkserver' in Python3.14
    freeze_support() # Multiprocessing support for frozen Windows executables

    # Configure basic Bible Organisational System (BOS) set-up
    parser = BibleOrgSysGlobals.setup( PROGRAM_NAME, PROGRAM_VERSION )
    BibleOrgSysGlobals.addStandardOptionsAndProcess( parser, exportAvailable=False )

    main()

    BibleOrgSysGlobals.closedown( PROGRAM_NAME, PROGRAM_VERSION )
# end of convert_OET-RV_to_sectionReadings.py
