#!/usr/bin/env -S uv run
# -\*- coding: utf-8 -\*-
# SPDX-FileCopyrightText: © 2023 Robert Hunt <Freely.Given.org+OET@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later
#
# spell_check.py
#
# Script to spell check either the OET-RV or OET-LV.
#
# Copyright (C) 2023-2026 Robert Hunt
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
    2025-10-10 Added support for loading (OET) LV & RV names tables; change to check entire Bible (so no books missed)
    2026-02-13 Seems above names tables were never used
    2026-03-24 Added Hebrew alphabet
    2026-04-16 Handle names with apostrophes in them better
"""
from gettext import gettext as _
# from typing import List, Tuple, Optional
from pathlib import Path
from csv import DictReader
# import logging
import re
import os

# if __name__ == '__main__':
#     import sys
#     sys.path.insert( 0, '../../BibleOrgSys/' )
from BibleOrgSys import BibleOrgSysGlobals
from BibleOrgSys.BibleOrgSysGlobals import vPrint, fnPrint, dPrint


LAST_MODIFIED_DATE = '2026-05-26' # by RJH
SHORT_PROGRAM_NAME = "spell_check"
PROGRAM_NAME = "OET Spell Check"
PROGRAM_VERSION = '0.30'
PROGRAM_NAME_VERSION = f'{SHORT_PROGRAM_NAME} v{PROGRAM_VERSION}'

DEBUGGING_THIS_MODULE = False


project_folderpath = Path(__file__).parent.parent # Find folders relative to this module
FG_folderpath = project_folderpath.parent # Path to find parallel Freely-Given.org repos
OET_LV_ESFM_FolderPath = project_folderpath.joinpath( 'derivedTexts/auto_edited_VLT_ESFM/' )
assert OET_LV_ESFM_FolderPath.is_dir()
OET_RV_ESFM_FolderPath = project_folderpath.joinpath( 'translatedTexts/ReadersVersion/' )
assert OET_RV_ESFM_FolderPath.is_dir()

OET_LV_NAMES_TSV_FILEPATH = project_folderpath.joinpath( 'derivedTexts/OET-LV_names_table.tsv' )
assert OET_LV_NAMES_TSV_FILEPATH.is_file()
EXPECTED_OET_LV_NAMES_TSV_HEADER = 'TraditionalName\tLVName'
OET_RV_NAMES_TSV_FILEPATH = project_folderpath.joinpath( 'translatedTexts/ReadersVersion/OET-RV_names_table.tsv' )
assert OET_RV_NAMES_TSV_FILEPATH.is_file()
EXPECTED_OET_RV_NAMES_TSV_HEADER = 'TraditionalName\tRVName\tExplained\tComment'

TED_Dict_folderpath = Path( '../../../Documents/RobH123/TED_Dict/sourceDicts/')
assert TED_Dict_folderpath.is_dir()


# Globals
# Prepopulate the word set with our exceptions
BIBLE_WORD_SET = set(['3.0','UTF','ESFM','v0.6','Freely-Given.org',
                      'OET','WORDTABLE','LV_OT_word_table.tsv','LV_NT_word_table.tsv',
                      'b','c','d','e',
                      's1','s2','s3','s4','r','+','LXX','Grk',
                      'nomina','Nomina','sacra',
                      'Deutercanon','Deuterocanonicals',

                      'href="https', # Website refererences
                      '\\jmp', '_', '_\\em*about', '_\\em*all', '_\\em*caring\\em',
                      'wpmu2.azurewebsites.net', 'www.GotQuestions.org', 'www.biblicalarchaeology.org', 'www.billmounce.com', 'www.sil.org','textandcanon.org',
                      'armstronginstitute.org','bibleDifferences.net','bibleandtech.blogspot.com','bibledifferences.net','biblestudyresources','commentary.html','judas%E2%80%99','tongue%E2%80%9D', 'Yeshua%E2%80%99',
                      'mounce', 'openenglishbible', 'scrollandscreen.com', 'UASVBible.org', 'given.org', 'GitHub.com', 'GreekCNTR.org', # Websites
                      '%E2%80%9Cdivided','%E2%80%9Cjew%E2%80%9D','v=66013018'

                    #   'Abimelek','Abshalom','Ahimelek','Amatsyah','Ayyalon','Azaryah',
                    #   'Benyamin','Benyamite','Benyamites', 'Beyt',
                    #   'Efraim','Efron','Elifaz','Eliyyah','Esaw',
                    #   'Far\'oh','Finehas',
                    #   'Goliat',
                    #   'Hizkiyyah','Hofni',
                    #   'Isayah','Ishma\'el','Iyyov',
                    #   'Kayin',
                    #   'Lavan','Lakish','Layish',
                    #   'Malaki','Manashsheh',
                    #     'Metushalah',
                    #     'Mikal','Milkah','Mitspah','Mitsrayim',
                    #     'Mordekai','Mosheh',
                    #   'Natan',
                    #   'Potifar',
                    #   'Sha\'ul',
                    #     'Shekem','Shelomoh','Shemu\'el',
                    #     'Shimshon',
                    #     'Shomron',
                    #     'Shushan',
                    #   'Tsidon','Tsiklag','Tsiyyon',
                    #   'Uriyyah','Uzziyyah'
                    #   'Yacob',
                    #         'Yael',
                    #         'Yafet','Yafo',
                    #         'Yair',
                    #         'Yakob',
                    #         'Yared',
                    #     'Yehoshafat','Yehoshua','Yehu','Yehud','Yericho','Yerushalem','Yeshayah','Yesous','Yesse','Yetro',
                    #     'Yhn',
                    #     'Yishay',
                    #     'Yisra\'el','Yisrael', # CHOOSE ONE!!!
                    #     'Yitshak',
                    #     'Yoab','Yoav',
                    #     'Yohan','Yohan-the-Immerser','Yoel','Yoktan','Yonah','Yonatan','Yoppa','Yordan','Yosef','Yoshua','Yotam',
                    #     'Yudah','Yudas','Yude','Yudea','Yudean','Yudeans',
                    #   'Zekaryah','Zofar',

                      'black-grained','building-stone',
                      'efod','emerald-looking',
                      'false-teachers','finely-ground','finely-spun',
                      'house-servants',
                      'law-breaker',
                      'non',
                      'pass-over',
                      'tent-making',

                      'nlt',

                      'v2','v3','v4','v5','v6','v8','v9','v13','v14','v15','v16','v19','v26','v27',
                      'GEN','EXO','LEV','NUM','DEU','JOS','JDG','RUT','SA1','SA2','KI1','KI2','CH1','CH2','EZR','NEH','EST',
                        'JOB','PSA','PRO','ECC','SNG','ISA','JER','LAM','EZE','DAN','HOS','JOL','AMO','OBA','JNA','MIC','NAH','HAB','ZEP','HAG','ZEC','MAL',
                      'JDT', 'MA1','MA2','MA3','MA4', 'MAN', 'TOB',
                      'MAT','MRK','LUK','JHN','ACT','ROM','CO1','CO2','GAL','EPH','PHP','COL','TH1','TH2','TI1','TI2','TIT',
                        'PHM','HEB','JAM','PE1','PE2','JN1','JN2','JN3','JDE','REV',
                      'Gen','Exo','Lev','Num','Deu','Chr','Rut','Psa','Prv','Hos','Zech','Mal',
                        'Mrk','Luk','Lk','Jhn','Jn','Act','Gal','Eph','Php','Col','Heb','Phm','Rev',

                      'ABADDON', 'ASKING', 'ABOUT', 'AM', 'AN', 'AND',
                      'B.C', 'BE', 'BEEN', 'BOY', 'BUT',
                      'CAME', 'CHECK', 'CONSISTENCY',
                      'DELIVERANCE', 'DIAGRAM', 'DOES', 'DOUBLE',
                      'ENDING', 'EYES',
                      'FAIL', 'FIVE', 'FOR', 'FORMAT', 'FOUR',
                      'GAVE','GLORIFIED', 'GLORIOUS', 'GLORY', 'GOSPEL',
                      'HAVING', 'HE', 'HOLY',
                      'IN', 'IS',
                      'LITERAL', 'LIVE', 'LONGER', 'LORD',
                      'MARK', 'MEAN', 'MEANING', 'MONTH', 'MOON', 'MORE',
                      'NEED', 'NEEDS', 'NOT',
                      'OF', 'OLD', 'ONE', 'OR',
                      'PATHS', 'POETIC', 'POINT', 'PRODUCTS',
                      'QUOTES',
                      'RAHAB', 'REJECT', 'RIGHTEOUS',
                      'SALVATION', 'SECTION', 'SEVEN', 'SHOULD', 'SIX', 'STUD', 'SURE',
                      'TENTATIVELY', 'THAT', 'THE', 'THIS', 'THREE', 'THRONE', 'TO', 'TOO', 'TWO',
                      'VANISHING', 'VISIT',
                      'WHAT', "WHAT'S", 'WHO', 'WORD', 'WORK', "Why've",
                      'YOUNG',

                      'א','ב','ג','ד','ה','ו','ז','ח','ט','י','כ'
                      'ל','מ','נ','ס','ע','פ','צ','ק','ר','ש','ת',
                    ])
BAD_WORD_SET = set()
BAD_WORD_LIST = []



def main():
    """
    Main program to handle command line parameters and then run what they want.
    """
    BibleOrgSysGlobals.introduceProgram( __name__, PROGRAM_NAME_VERSION, LAST_MODIFIED_DATE )

    if load_dict_sources() and load_OET_RV_names():
        spellCheck_OET_RV()

    if BAD_WORD_SET:
        vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"Found {len(BAD_WORD_SET):,} different bad words: {sorted(BAD_WORD_SET)}" )
    if BAD_WORD_LIST:
        vPrint( 'Info', DEBUGGING_THIS_MODULE, f"Found {len(BAD_WORD_LIST):,} total bad words: {BAD_WORD_LIST}" )
# end of spell_check.main


OET_LV_NAMES_SET = set()
def load_OET_LV_names() -> bool:
    """
    Load the names we use from the tsv names table
    """
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"Loading {OET_LV_NAMES_TSV_FILEPATH}…" )
    with open( OET_LV_NAMES_TSV_FILEPATH, 'rt', encoding='utf-8') as inputTSVFile:
        initialTSVLines = inputTSVFile.read().rstrip().split( '\n' )
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  {len(initialTSVLines):,} lines loaded from {OET_LV_NAMES_TSV_FILEPATH.name}." )

    # Remove any BOM
    if initialTSVLines[0].startswith("\ufeff"):
        vPrint( 'Normal', DEBUGGING_THIS_MODULE, "  Handling Byte Order Marker (BOM) at start of TSV file…")
        initialTSVLines[0] = initialTSVLines[0][1:]
    assert initialTSVLines[0] == EXPECTED_OET_LV_NAMES_TSV_HEADER

    # crossTestamentQuotes_tsv_rows = []
    dict_reader = DictReader(initialTSVLines, delimiter='\t' )
    for n, row in enumerate(dict_reader):
        lvName = row['LVName']
        OET_LV_NAMES_SET.add( lvName )
        if '-' in lvName: # Break up names like Beer-Sheva (as we split them below)
            for rvNameBit in lvName.split( '-' ):
                OET_LV_NAMES_SET.add( rvNameBit )


    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Loaded {len(OET_LV_NAMES_SET):,} OET-LV names." )
    # print( list(OET_LV_NAMES_SET)[:10]); halt
    return True
# end of spellCheckEnglish.load_OET_LV_names


OET_RV_NAMES_SET = set()
def load_OET_RV_names() -> bool:
    """
    Load the names we use from the tsv names table
    """
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"Loading {OET_RV_NAMES_TSV_FILEPATH}…" )
    with open( OET_RV_NAMES_TSV_FILEPATH, 'rt', encoding='utf-8') as inputTSVFile:
        initialTSVLines = inputTSVFile.read().rstrip().replace( '’', "'" ).split( '\n' ) # Change apostrophe back to simple one
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  {len(initialTSVLines):,} lines loaded from {OET_RV_NAMES_TSV_FILEPATH.name}." )

    # Remove any BOM
    if initialTSVLines[0].startswith("\ufeff"):
        vPrint( 'Normal', DEBUGGING_THIS_MODULE, "  Handling Byte Order Marker (BOM) at start of TSV file…")
        initialTSVLines[0] = initialTSVLines[0][1:]
    assert initialTSVLines[0] == EXPECTED_OET_RV_NAMES_TSV_HEADER

    # crossTestamentQuotes_tsv_rows = []
    dict_reader = DictReader(initialTSVLines, delimiter='\t' )
    for n, row in enumerate(dict_reader):
        rvName = row['RVName']
        OET_RV_NAMES_SET.add( rvName )
        if '-' in rvName: # Break up names like Beer-Sheva (as we split them below)
            for rvNameBit in rvName.split( '-' ):
                OET_RV_NAMES_SET.add( rvNameBit )


    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Loaded {len(OET_RV_NAMES_SET):,} OET-RV names." )
    # print( list(OET_RV_NAMES_SET)[:10]); halt
    return True
# end of spellCheckEnglish.load_OET_RV_names


def load_dict_sources() -> bool:
    """
    Load the words from the SIL Toolbox source files.
    """
    global BIBLE_WORD_SET
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"Load English and Bible words from source dictionaries in {TED_Dict_folderpath}…" )

    for dictFilename in ('EnglishDict.db','BibleDict.db'):
        dictFilepath = TED_Dict_folderpath.joinpath( dictFilename )
        with open( dictFilepath, 'rt', encoding='utf-8' ) as dictSourceFile:
            dictText = dictSourceFile.read()
        dictWords = dictText.split( '\n\\wd ')
        # print( f"{dictWords[0]=} {dictWords[1]=} {dictWords[2]=} {dictWords[-1]=}"); halt
        for entryStr in dictWords[1:]:
            entryLines = entryStr.rstrip().split( '\n' )
            # print( f"{entryLines=}")
            word = entryLines[0].rstrip()
            if '*' in word:
                word, subscript = word.split( '*', 1 )
                assert subscript.isdigit()
            assert entryLines[1].startswith( '\\lg ')
            language = entryLines[1][4:]
            mispelling = False
            for entryLine in entryLines[2:]:
                if entryLine.startswith( '\\ms '):
                    mispelling = True
                    break
            if language != 'AME' and not mispelling:
                BIBLE_WORD_SET.add( word )
        # for line in dictSourceFile:
        #     line = line.rstrip( '\n' )
        #     if line.startswith( '\\wd '):
        #         word = line[4:]
        #         if '*' in word:
        #             word, subscript = word.split( '*', 1 )
        #             assert subscript.isdigit()
        #         BIBLE_WORD_SET.add( word )

    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Loaded {len(BIBLE_WORD_SET):,} English and Bible words." )
    # print( BIBLE_WORD_LIST[:10]); halt
    return True
# end of spell_check.load_dict_sources


def spellCheck_OET_RV() -> bool:
    """
    """
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"\nSpell check selected OET-RV files…" )

    numCheckedFiles = 0
    for filename in sorted( os.listdir( OET_RV_ESFM_FolderPath ) ):
        # Expect filenames like 'OET-RV_PHM.ESFM'
        if not filename.endswith( '.ESFM' ): continue
        assert filename.startswith( 'OET-RV_' )
        BBB = filename[7:10]

        filepath = OET_RV_ESFM_FolderPath.joinpath( filename )
        spellCheckFile( BBB, filepath, OET_RV_NAMES_SET )
        numCheckedFiles += 1

    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Checked {numCheckedFiles:,} OET-RV files." )
    return True
# end of spell_check.spellCheckOET_RV

def spellCheckFile( BBB:str, filepath:str|Path, nameSet:set[str] ) -> bool:
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Checking spelling of {filepath}…" )

    with open( filepath, 'rt', encoding='utf-8' ) as checkFile:
        C = V = '0'
        for line in checkFile:
            line = line.rstrip( '\n' )
            if not line:
                assert BBB in ('FRT','INT'), f"{BBB} has a blank line in it!"
                continue
            if line.startswith( '\\' ):
                line = line[1:]
            else:
                assert BBB in ('INT',), f"Found {BBB} line that doesn't begin with a backslash: {line=}"
            try: marker, rest = line.split( ' ', 1 )
            except ValueError: marker, rest = line, None # No space in the line
            if marker in ('id','toc3'): # We don't spell-check these lines
                continue
            elif marker == 'rem' and rest.startswith( '/s1 '):
                continue # Don't check headings from other versions
            elif marker == 'c':
                C, V = rest, '0'
                continue
            elif marker == 'v':
                V, rest = rest.split( ' ', 1 )
            if rest:
                if rest.startswith( '⇔' ): rest = rest[1:] # Delete 'reordered verse' marker
                spellCheckESFMText( rest, f'{BBB} {C}:{V} \\{marker}', nameSet )
    return True
# end of spell_check.spellCheckFile


USFM_CLOSED_FIELDS_TO_COMPLETELY_REMOVE = ('x','fig')
def spellCheckESFMText( text:str, location:str, nameSet:set[str] ) -> bool:
    """
    """
    # vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Checking spelling of {location} '{text}'…" )

    adjText = text
    for fieldName in USFM_CLOSED_FIELDS_TO_COMPLETELY_REMOVE:
        regex = re.compile( f'\\\\{fieldName} .+?\\\\{fieldName}\\*')
        adjText, numSubs = regex.subn( '', adjText )
        assert f'\\{fieldName}' not in adjText or ('\\f ' in adjText and '\\xt ' in adjText), f"{fieldName=} {adjText=}"

    lastLastWord = lastWord = ''

    for addChar in ('≈','+','>','<','@','*','#','≡'):
        adjText = adjText.replace( f'\\add ?{addChar}', '' ).replace( f'\\add {addChar}', '' )
    for charMarker in ('add','+add','em','+em','nd','+nd','sc','wj','+wj','bd','+bd','it','+it','bdit','+bdit','tl',
                        'ior','bk','+bk','sig','sup','qs',
                        '+wh',
                        'f +','ft','fqa','fq','fl', # We intentionally omit 'fr' Why???
                        'x +','xt', # We intentionally omit 'xo' Why???
                        'jmp',
                        ):
        adjText = adjText.replace( f'\\{charMarker} ', '' ).replace( f'\\{charMarker}*', '' )
    adjText =  ( adjText.replace( '—', ' ' ) # Treat em-dashes as spaces
                    .replace( '-', ' ' ) # Treat hyphens as spaces, i.e., split compound words (both good and bad like 'non-combatant')
                    .replace( '/', ' ' ) # Treat forward slash as spaces (sometimes used to separate alternate words like 'dew/rain')
                    # .replace( '\\f ', ' \\f ' ).replace( '\\x ', ' \\x ' )
                    .replace( '\\fr ', ' ###' ).replace( '\\xo ', ' ###' )
                    .replace( '\\x*', ' ' ).replace( '\\f*', ' ' )
                    .replace( '\\fig*', ' ' )
                    # .replace( '\\add*', '' ) # Removed above
                    # .replace( '\\jmp ', ' \\jmp ' ) # Removed above
                    .replace( '…', ' ' ).replace( '◙', ' ' ).replace( '◘', ' ' )
                    .replace( '  ', ' ' )
                    )
    adjWords = adjText.split( ' ' )
    for ww,word in enumerate( adjWords ):
        try: nextWord = adjWords[ww+1]
        except IndexError: nextWord = '' # at end

        if word.startswith( '###' ): continue # it's an fr or xo field
        for _x in range( 3 ):
            # We can have nested things, especially at the end of a sentence
            #   e.g., 'my¦141837 heart¦141839 in \+add the\+add* \+nd messiah¦141841\+nd*.\sig*'
            while word.startswith('‘') or word.startswith('“') \
            or word.startswith('(')  or word.startswith('['):
                word = word[1:]
            # for charMarker in ('add','+add','em','+em','nd','+nd','sc','wj','+wj','bd','it','+it','bdit','tl',
            #                     'ior','bk','sig','sup','qs',
            #                     'f','ft', # We intentionally omit 'fr'
            #                     'x','xt'): # We intentionally omit 'xo'
            #     if word == f'\\{charMarker}': # These are the character fields that we use in the OET
            #         word = None
            #         break
            #     while word.endswith('.') or word.endswith(',') \
            #     or word.endswith('’') or word.endswith('”') \
            #     or word.endswith('?') or word.endswith('!') \
            #     or word.endswith(':') or word.endswith(';') \
            #     or word.endswith(')') or word.endswith(']') \
            #     or word.endswith('…'): 
            #         word = word[:-1]
            #     if word.endswith( f'\\{charMarker}*' ):
            #         word = word[:-len(charMarker)-2]
            while word.endswith('.') or word.endswith(',') \
            or word.endswith('’') or word.endswith('”') \
            or word.endswith('?') or word.endswith('!') \
            or word.endswith(':') or word.endswith(';') \
            or word.endswith(')') or word.endswith(']') \
            or word.endswith('…'): 
                word = word[:-1]
            if not word: break

            # Remove \add markers
            if word[0] == '?': # This one can precede the others
                word = word[1:]
            if word[0] in '+<=>#@*^&≈?≡→':
                word = word[1:]
            if not word: break

            # Get rid of possessives (using straight apostrophe ')
            if word.endswith("'"): word = word[:-1]
            elif word.endswith("'s"): word = word[:-2]
        if not word: continue
        if '¦' in word:
            assert word.count( '¦' ) == 1, f"{word=} @ {location}"
            word, number = word.split( '¦', 1 )
            assert number.isdigit(), f"'{word}¦{number}' @ {location}\n\nfrom '{adjText}'\n\nfrom '{text}'"
        # Get rid of possessives (using straight apostrophe ')
        if word.endswith("'"): word = word[:-1]
        elif word.endswith("'s"): word = word[:-2]
        if not word: continue
        if word[0].isdigit(): continue # Probably a ior or fr or xo reference
        if word.startswith( 'http' ): continue # URL
        if word not in BIBLE_WORD_SET \
        and f'{word[0].lower()}{word[1:]}' not in BIBLE_WORD_SET \
        and word not in nameSet:
            print( f'''    Suspect {word=} @ {location} with "{lastLastWord} {lastWord} {word} {nextWord}"''' )
            BAD_WORD_SET.add( word )
            BAD_WORD_LIST.append( (word,location) )
        if word == lastWord and word not in ('had','that'):
            print( f'''    Possible duplicated {word=} @ {location} with "{lastLastWord} {lastWord} {word} {nextWord}"''' )
            dupWord = f'{word} {word}'
            BAD_WORD_SET.add( dupWord )
            BAD_WORD_LIST.append( (dupWord,location) )
        lastLastWord = lastWord
        lastWord = word

    return True
# end of spell_check.spellCheckESFMText



if __name__ == '__main__':
    # Configure basic Bible Organisational System (BOS) set-up
    parser = BibleOrgSysGlobals.setup( PROGRAM_NAME, PROGRAM_VERSION )
    BibleOrgSysGlobals.addStandardOptionsAndProcess( parser, exportAvailable=False )

    main()

    BibleOrgSysGlobals.closedown( PROGRAM_NAME, PROGRAM_VERSION )
# end of spell_check.py
