#!/usr/bin/env python3
# -\*- coding: utf-8 -\*-
# SPDX-License-Identifier: GPL-3.0-or-later
#
# convert_ClearMaculaOT_to_our_TSV.py
#
# Script handling convert_ClearMaculaOT_to_our_TSV functions
#
# Copyright (C) 2022-2025 Robert Hunt
# Author: Robert Hunt <Freely.Given.org+BOS@gmail.com>
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
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Script taking Clear.Bible Macula Hebrew and extracting and flattening the data
    into a single, large TSV file.

We also add the ID fields that were originally adapted from the OSHB id fields.

OSHB morphology codes can be found at https://hb.openscriptures.org/parsing/HebrewMorphologyCodes.html.

(This is run AFTER convert_OSHB_XML_to_TSV.py and prepare_OSHB_for_glossing.py
        and BEFORE apply_Clear_Macula_OT_glosses.py.)

CHANGELOG:
    2024-04-04 Tried using macula Hebrew TSV files instead of 'low-fat' XML but it seemed to be lacking the 'role' info
    2024-04-15 Also output Hebrew lemma table
    2025-01-07 Change literal gloss back to house from temple for 'בֵּ֖יתּל'
    2025-01-09 Switch from 'low-fat' XML with data missing for compound words, to Macula Hebrew 'nodes' XML
    2025-01-20 Remove 'of' from start of glosses which aren't 'construct'
    2025-03-14 Fix bug where '[is]' and '[was]' could wrongly end up as separate glosses
"""
from gettext import gettext as _
# from typing import Dict, List, Tuple
from pathlib import Path
from csv import DictReader, DictWriter
from collections import defaultdict
# from datetime import datetime
import re
import logging
# from pprint import pprint
from xml.etree import ElementTree
import unicodedata

if __name__ == '__main__':
    import sys
    sys.path.insert( 0, '../../BibleOrgSys/' )
from BibleOrgSys import BibleOrgSysGlobals
from BibleOrgSys.BibleOrgSysGlobals import vPrint, fnPrint, dPrint
from BibleOrgSys.OriginalLanguages import Hebrew

sys.path.append( '../../BibleTransliterations/Python/' )
from BibleTransliterations import load_transliteration_table, transliterate_Hebrew

LAST_MODIFIED_DATE = '2025-03-14' # by RJH
SHORT_PROGRAM_NAME = "convert_ClearMaculaOT_to_our_TSV"
PROGRAM_NAME = "Extract and Apply Macula OT glosses"
PROGRAM_VERSION = '0.54'
PROGRAM_NAME_VERSION = f'{SHORT_PROGRAM_NAME} v{PROGRAM_VERSION}'

DEBUGGING_THIS_MODULE = False


MACULA_HEBREW_LOWFAT_XML_INPUT_FOLDERPATH = Path( '../../Forked/macula-hebrew/WLC/lowfat/' ) # In
MACULA_HEBREW_LOWFAT_XML_INPUT_FILENAME_TEMPLATE = 'NN-Uuu-CCC-lowfat.xml' # In, e.g., 01-Gen-001-lowfat.xml
EXPECTED_MACULA_HEBREW_LOWFAT_WORD_ATTRIBUTES = ('{http://www.w3.org/XML/1998/namespace}id', 'ref',
        'mandarin', 'english', 'gloss', 'compound',
        'class','morph','pos','person','gender','number','type','state','role',
        'transliteration','unicode','after',
        'strongnumberx', 'stronglemma','greek','greekstrong',
        'lang','lemma','stem','subjref','participantref',
        'sdbh','lexdomain','sensenumber','coredomain','frame',) # 'contextualdomain',
assert len(set(EXPECTED_MACULA_HEBREW_LOWFAT_WORD_ATTRIBUTES)) == len(EXPECTED_MACULA_HEBREW_LOWFAT_WORD_ATTRIBUTES), "No duplicate attribute names"
MACULA_HEBREW_NODES_XML_INPUT_FOLDERPATH = Path( '../../Forked/macula-hebrew/WLC/nodes/' ) # In
MACULA_HEBREW_NODES_XML_INPUT_FILENAME_TEMPLATE = 'NN-Uuu-CCC.xml' # In, e.g., 01-Gen-001.xml
EXPECTED_MACULA_HEBREW_NODES_WORD_ATTRIBUTES = ('word', '{http://www.w3.org/XML/1998/namespace}id', 'ref',
        'mandarin', 'english', 'gloss', 'compound',
        'class','morph','pos','person','gender','number','type','state','role',
        'transliteration','unicode','after',
        'oshb-strongs', 'greek','GreekStrong',
        'lang','lemma','stem','SubjRef','Ref',
        'SDBH','LexDomain','sensenumber','CoreDomain','Frame',) # 'contextualdomain',
assert len(set(EXPECTED_MACULA_HEBREW_NODES_WORD_ATTRIBUTES)) == len(EXPECTED_MACULA_HEBREW_NODES_WORD_ATTRIBUTES), "No duplicate attribute names"

# MACULA_HEBREW_TSV_INPUT_FOLDERPATH = Path( '../../Forked/macula-hebrew/WLC/tsv/' ) # In
# MACULA_HEBREW_TSV_INPUT_FILENAME = 'macula-hebrew.tsv' # In
# MACULA_HEBREW_EXPECTED_COLUMN_HEADER = 'xml:id\tref\tclass\ttext\ttransliteration\tafter\tstrongnumberx\tstronglemma\tsensenumber\tgreek\tgreekstrong\tgloss\tenglish\tmandarin\tstem\tmorph\tlang\tlemma\tpos\tperson\tgender\tnumber\tstate\ttype\tlexdomain\tcontextualdomain\tcoredomain\tsdbh\textends\tframe\tsubjref\tparticipantref'
# NUM_EXPECTED_MACULA_TSV_COLUMNS = MACULA_HEBREW_EXPECTED_COLUMN_HEADER.count( '\t' ) + 1
# macula_tsv_column_max_length_counts = {}
# macula_tsv_column_non_blank_counts = {}
# macula_tsv_column_counts = defaultdict(lambda: defaultdict(int))
# macula_tsv_column_headers = []

OUR_WLC_GLOSSES_TSV_INPUT_FILEPATH = Path( '../intermediateTexts/glossed_OSHB/our_WLC_glosses.morphemes.tsv' ) # In
NUM_EXPECTED_OUR_WLC_COLUMNS = 16
WLC_tsv_column_max_length_counts = {}
WLC_tsv_column_non_blank_counts = {}
WLC_tsv_column_counts = defaultdict(lambda: defaultdict(int))
WLC_tsv_column_headers = []

MORPHEME_TSV_OUTPUT_FILEPATH = Path( '../intermediateTexts/Clear.Bible_derived_Macula_data/Clear.Bible_MaculaHebrew.OT.morphemes.tsv' ) # Out
MORPHEME_OUTPUT_FIELDNAMES = ['FGRef','OSHBid','RowType','LFRef','LFNumRef',
                    'Language','WordOrMorpheme','Unicode','Transliteration','After',
                    'Compound','WordClass','PartOfSpeech','Person','Gender','Number','WordType','State','Role','SDBH',
                    'StrongNumberX','StrongLemma','Stem','Morphology','Lemma','SenseNumber',
                    'CoreDomain','LexicalDomain',# 'ContextualDomain',
                    'SubjRef','ParticipantRef','Frame',
                    'Greek','GreekStrong',
                    'EnglishGloss','MandarinGloss','ContextualGloss',
                    'Nesting']
assert len(set(MORPHEME_OUTPUT_FIELDNAMES)) == len(MORPHEME_OUTPUT_FIELDNAMES), "No duplicate fieldnames"
assert len(MORPHEME_OUTPUT_FIELDNAMES) == 37, len(MORPHEME_OUTPUT_FIELDNAMES)

MORPHEME_SHORTENED_TSV_OUTPUT_FILEPATH = Path( '../intermediateTexts/Clear.Bible_derived_Macula_data/Clear.Bible_MaculaHebrew.OT.morphemes.abbrev.tsv' ) # Out
MORPHEME_COLUMNS_TO_REMOVE_FOR_SHORTENING = ('LFRef','LFNumRef', # Don't need their references
        'Language', # Aramaic is in already in RowType field
        'Transliteration', # We can do this on the fly (and we like our own system better anyway)
        'Unicode', # Is this just a repetition?
        'SDBH', # Resource is not open source -- no use to us
        'MandarinGloss', # Not needed for our specific task
        'CoreDomain','LexicalDomain',#'ContextualDomain', # What do all these numbers refer to?
        )
for something in MORPHEME_COLUMNS_TO_REMOVE_FOR_SHORTENING:
    assert something in MORPHEME_OUTPUT_FIELDNAMES, something
assert len(set(MORPHEME_COLUMNS_TO_REMOVE_FOR_SHORTENING)) == len(MORPHEME_COLUMNS_TO_REMOVE_FOR_SHORTENING), "No duplicate fieldnames"
assert len(MORPHEME_COLUMNS_TO_REMOVE_FOR_SHORTENING) == 9, len(MORPHEME_COLUMNS_TO_REMOVE_FOR_SHORTENING)
assert len(MORPHEME_OUTPUT_FIELDNAMES) - len(MORPHEME_COLUMNS_TO_REMOVE_FOR_SHORTENING) == 28, f"{len(MORPHEME_OUTPUT_FIELDNAMES)=} {len(MORPHEME_COLUMNS_TO_REMOVE_FOR_SHORTENING)=}"

LEMMA_TSV_OUTPUT_FILEPATH = Path( '../intermediateTexts/Clear.Bible_derived_Macula_data/Clear.Bible_MaculaHebrew.OT.lemmas.tsv' ) # Out
LEMMA_OUTPUT_FIELDNAMES = ['Lemma','Glosses']

SUFFIX_DICT = {'1':'a', '2':'b', '3':'c', '4':'d', '5':'e'} # Max of 5 morphemes in one word


state = None
class State:
    def __init__( self ) -> None:
        """
        Constructor:
        """
        self.macula_Hebrew_Lowfat_XML_input_folderpath = MACULA_HEBREW_LOWFAT_XML_INPUT_FOLDERPATH
        self.macula_Hebrew_Nodes_XML_input_folderpath = MACULA_HEBREW_NODES_XML_INPUT_FOLDERPATH
        # self.macula_TSV_input_filepath = MACULA_HEBREW_TSV_INPUT_FOLDERPATH.joinpath( MACULA_HEBREW_TSV_INPUT_FILENAME )
        self.our_TSV_input_filepath = OUR_WLC_GLOSSES_TSV_INPUT_FILEPATH
        self.morpheme_TSV_output_filepath = MORPHEME_TSV_OUTPUT_FILEPATH
        self.morpheme_shortened_TSV_output_filepath = MORPHEME_SHORTENED_TSV_OUTPUT_FILEPATH
        self.lemma_TSV_output_filepath = LEMMA_TSV_OUTPUT_FILEPATH
        self.our_WLC_rows = []
        # self.macula_rows = [] # For TSV input
        self.maculaHebrewWordsAndMorphemes = []
        self.morpheme_output_rows = []
        self.morpheme_output_fieldnames = MORPHEME_OUTPUT_FIELDNAMES
        self.lemma_formation_dict = {}
        self.lemma_output_rows = []
        self.lemma_output_fieldnames = LEMMA_OUTPUT_FIELDNAMES
        # self.lemma_index_dict = {} # Maybe we don't need this?
    # end of convert_ClearMaculaOT_to_our_TSV.State.__init__()


def main() -> None:
    """
    """
    BibleOrgSysGlobals.introduceProgram( __name__, PROGRAM_NAME_VERSION, LAST_MODIFIED_DATE )
    global state
    state = State()

    load_transliteration_table( 'Hebrew' )

    if loadOurSourceTable():
        # if loadMaculaHebrewLowFatXMLGlosses():
        if loadMaculaHebrewNodesXMLGlosses():
            if MacHeb_add_OSHB_ids(): # TSV_add_OSHB_ids()
                save_lemma_TSV_file()
                save_filled_morpheme_TSV_file()
                save_shortened_morpheme_TSV_file()
# end of convert_ClearMaculaOT_to_our_TSV.main


def loadOurSourceTable() -> bool:
    """
    """
    global WLC_tsv_column_headers
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"\nLoading our WLC tsv file from {state.our_TSV_input_filepath}…")
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  Expecting {NUM_EXPECTED_OUR_WLC_COLUMNS} columns…")
    with open(state.our_TSV_input_filepath, 'rt', encoding='utf-8') as tsv_file:
        tsv_lines = tsv_file.readlines()

    # Remove any BOM
    if tsv_lines[0].startswith("\ufeff"):
        vPrint( 'Quiet', DEBUGGING_THIS_MODULE, "  Handling Byte Order Marker (BOM) at start of our WLC tsv file…")
        tsv_lines[0] = tsv_lines[0][1:]

    # Get the headers before we start
    WLC_tsv_column_headers = [header for header in tsv_lines[0].strip().split('\t')]
    dPrint('Info', DEBUGGING_THIS_MODULE, f"Column headers: ({len(WLC_tsv_column_headers)}): {WLC_tsv_column_headers}")
    assert len(WLC_tsv_column_headers) == NUM_EXPECTED_OUR_WLC_COLUMNS

    # Read, check the number of columns, and summarise row contents all in one go
    dict_reader = DictReader(tsv_lines, delimiter='\t')
    unique_morphemes, unique_words = set(), set()
    note_count = seg_count = 0
    assembled_word = ''
    for n, row in enumerate(dict_reader):
        if len(row) != NUM_EXPECTED_OUR_WLC_COLUMNS:
            logging.error(f"Line {n} has {len(row)} columns instead of {NUM_EXPECTED_OUR_WLC_COLUMNS}!!!")
        for char in row['NoCantillations']:
            assert 'ACCENT' not in unicodedata.name(char), f"{unicodedata.name(char)=} {row['NoCantillations']=} {row=}"
        state.our_WLC_rows.append(row)
        row_type = row['RowType']
        if row_type != 'm' and assembled_word:
            # dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"{assembled_word=}")
            unique_words.add(assembled_word)
            assembled_word = ''
        if row_type == 'seg':
            seg_count += 1
        elif row_type.endswith('note'):
            note_count += 1
        elif row_type in ('w','Aw','wK','AwK'): # w=word, A=Aramaic (rather than Hebrew), K=Ketiv
            unique_words.add(row['WordOrMorpheme'])
        elif row_type in ('m','M','Am','AM','mK','MK','AmK','AMK'): # m=morpheme, M=last morpheme in word, A=Aramaic (rather than Hebrew), K=Ketiv
            unique_morphemes.add(row['WordOrMorpheme'])
            assembled_word = f"{assembled_word}{row['WordOrMorpheme']}"
        else: vPrint( 'Quiet', DEBUGGING_THIS_MODULE, row_type); unexpected_row_type
        for key, value in row.items():
            # WLC_tsv_column_sets[key].add(value)
            if n==0: # We do it like this (rather than using a defaultdict(int)) so that all fields are entered into the dict in the correct order
                WLC_tsv_column_max_length_counts[key] = 0
                WLC_tsv_column_non_blank_counts[key] = 0
            if value:
                if len(value) > WLC_tsv_column_max_length_counts[key]:
                    WLC_tsv_column_max_length_counts[key] = len(value)
                WLC_tsv_column_non_blank_counts[key] += 1
            WLC_tsv_column_counts[key][value] += 1
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  Loaded {len(state.our_WLC_rows):,} (tsv) WLC data rows.")
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"    Have {len(unique_words):,} unique Hebrew words.")
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"    Have {len(unique_morphemes):,} unique Hebrew morphemes.")
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"    Have {seg_count:,} Hebrew segment markers.")
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"    Have {note_count:,} notes.")

    return True
# end of convert_ClearMaculaOT_to_our_TSV.loadOurSourceTable


wordnumber_regex = re.compile( '[0-9]{12}' )
# def loadMaculaHebrewLowFatXMLGlosses() -> bool:
#     """
#     Reads in the Clear.Bible 'low-fat' XML chapter files
#         and then finds all <w> and <wg> entries (keeping track of their parents, e.g., other <wg>s or <sentence>)
    
#     Loads all the <w> entries for the chapter into a temporary list
#         and sorts them by their numerical id, e.g., <w xml:id="o010030040011" = obbcccvvvwwws
#             but note: it can be <w xml:id="o010030060101ה" for definite article after preposition

#     Extract glosses out of fields 
#     Reorganise columns and add our extra columns
#     """
#     vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"\nLoading Clear.Bible OT 'low fat' glosses from {state.macula_Hebrew_Lowfat_XML_input_folderpath}/…" )
    
#     max_nesting_level = 0
#     column_counts = defaultdict(lambda: defaultdict(int))
#     # non_blank_counts = defaultdict(int)
#     refDict = {}
#     for referenceNumber in range(1, 39+1):
#         BBB = BibleOrgSysGlobals.loadedBibleBooksCodes.getBBBFromReferenceNumber( referenceNumber )
#         vPrint( 'Info', DEBUGGING_THIS_MODULE, f"  Loading Macula Hebrew LowFat {BBB} XML files…")
#         Uuu = BibleOrgSysGlobals.loadedBibleBooksCodes.getUSFMAbbreviation( BBB )
#         if Uuu=='Hos': Uuu = 'HOS' # Fix inconsistency in naming patterns
#         filenameTemplate = MACULA_HEBREW_LOWFAT_XML_INPUT_FILENAME_TEMPLATE.replace( 'NN', str(referenceNumber).zfill(2) ).replace( 'Uuu', Uuu )

#         for chapterNumber in range(1, 150+1):
#             filename = filenameTemplate.replace( 'CCC', str(chapterNumber).zfill(3) )
#             try:
#                 chapterTree = ElementTree.parse( state.macula_Hebrew_Lowfat_XML_input_folderpath.joinpath( filename ) )
#             except FileNotFoundError:
#                 break # gone beyond the number of chapters

#             # First make a table of parents so we can find them later
#             parentMap = {child:parent for parent in chapterTree.iter() for child in parent if child.tag in ('w','wg','c')}
#             dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"  Loaded {len(parentMap):,} parent entries." )

#             # Now load all the word (w) fields for the chapter into a temporary list
#             tempWordsAndMorphemes = []
#             longIDs = []
#             transliteratedLemmas = {}
#             for elem in chapterTree.getroot().iter():
#                 if elem.tag == 'w': # ignore all the others -- there's enough info in here
#                     for attribName in elem.attrib:
#                         assert attribName in EXPECTED_MACULA_HEBREW_LOWFAT_WORD_ATTRIBUTES, f"loadMaculaHebrewLowFatXMLGlosses(): unexpected {attribName=}"

#                     wordOrMorpheme = elem.text
#                     theirRef = elem.get('ref') # e.g., "GEN 1:1!1"
#                     # print( f"{theirRef=} {wordOrMorpheme=}" )

#                     longID = elem.get('{http://www.w3.org/XML/1998/namespace}id') # e.g., o010010050031 = obbcccvvvwwws
#                     longIDs.append( longID )
#                     assert longID.startswith( 'o' ) # Stands for OldTestament
#                     longID = longID[1:] # remove 'o' prefix
#                     if len(longID) > 12: # it's an article (vowel after preposition)
#                         assert len(longID) == 13
#                         assert longID.endswith( 'ה' )
#                         assert longID[:-1].isdigit()
#                     else:
#                         assert len(longID) == 12
#                         assert longID[:].isdigit()

#                     gloss = elem.get('gloss')
#                     if gloss:
#                         if '(et)' in gloss or '(dm)' in gloss:
#                             print( f"(et) or (dm) {theirRef=} {wordOrMorpheme=} {gloss=}" )
#                             if '(et)' in gloss and wordOrMorpheme not in ('אֵ֥ת','אֶת','אֶֽת','אֵ֚ת','אֵ֖ת','אֵ֛ת','אֵ֣ת','אֶׄתׄ','אֵת֩','אֵ֤ת','אֶ֨ת','אֵ֡ת','אֵ֧ת','אֵ֠ת','אֵ֗ת','אֵת','אֵֽת','אֶ֥ת','אֵ֝֗ת','אֵ֝ת','אֵת֮','אֶתּ'):
#                                 halt
#                             if '(dm)' in gloss and wordOrMorpheme not in ('כִּי','כִּ֣י','כִּי֩','כִּ֗י','כִּ֥י','כִּֽי','כִּ֚י','כִּ֛י','כִּ֤י','כִּ֠י','כִּ֧י','כִֽי','כִּ֡י','כִּ֖י','כִּ֞י','כִ֤י','כִ֥י','כִּ֨י','כִי','כִ֗י','כִ֔י','כִּ֭י','כִּ֘י','כִּ֝֗י','כִּ֬י','כִּ֪י','כִ֛י','כִּ֩י'):
#                                 if theirRef not in ('DAN 1:8!5','DAN 1:8!15') or wordOrMorpheme not in ('אֲשֶׁ֧ר','אֲשֶׁ֖ר'):
#                                     halt
#                         gloss = ( gloss.replace( '.', '_' ) # Change to our system
#                                     .replace( '(et)', 'DOM' ) # Change to our 'DOM' = DirectObjectMarker
#                                     .replace( '(dm)', '' if theirRef.startswith('DAN 1:8!') else 'if/because') # What is dm supposed to mean?
#                                 )
#                         assert '’' not in gloss, f"{theirRef=} {wordOrMorpheme=} {gloss=}"

#                     lang = elem.get('lang')
#                     column_counts['lang'][lang] += 1
#                     assert lang in 'HA'
#                     wordType = elem.get('type')
#                     column_counts['type'][wordType] += 1
#                     print( f"{theirRef=} {wordOrMorpheme=} {gloss=} {lang=} {wordType=}" )
#                     assert wordType in ('common','definite article','direct object marker','qatal'), f"{theirRef=} {wordOrMorpheme=} {gloss=} {lang=} {wordType=}"
#                     wordState = elem.get('state')
#                     column_counts['state'][wordState] += 1
#                     if wordState:
#                         # What is 'determined' in Ezra 4:8!5, etc.
#                         assert wordState in ('absolute','construct','determined'), f"Found unexpected {wordState=}"
#                     # dPrint( 'Info', DEBUGGING_THIS_MODULE, f"    {ref} {longID} {lang} '{wordOrMorpheme}' {English=} {gloss=}")

#                     compound = elem.get('compound')
#                     assert not compound # it seems to have gone
#                     column_counts['compound'][compound] += 1

#                     stem = elem.get('stem')
#                     column_counts['stem'][stem] += 1
#                     morph = elem.get('morph')
#                     # column_counts['morph'][morph] += 1 # There's over 700 different variations
#                     lemma = elem.get('lemma')
#                     if lemma:
#                         # I think this is a Clear.Bible error
#                         # AssertionError: unicodedata.name(char)='HEBREW ACCENT OLE' lemma='אֶ֫רֶץ' longID='010010010072'
#                         for char in lemma:
#                             if 'ACCENT' in unicodedata.name(char):
#                                 logger = logging.critical if DEBUGGING_THIS_MODULE else logging.error
#                                 logger( f"Unexpected character in LowFat lemma '{unicodedata.name(char)}' {lemma=} {longID=}" )
#                         lemma = removeHebrewCantillationMarks( lemma )
#                         for char in lemma:
#                             assert 'ACCENT' not in unicodedata.name(char), f"{unicodedata.name(char)=} {lemma=} {longID=}"
#                         transliteratedLemma = transliterate_Hebrew( lemma )
#                         # If the following fails, our lemmas aren't unique
#                         if transliteratedLemma in transliteratedLemmas:
#                             assert transliteratedLemmas[transliteratedLemma] == lemma, f"Multiple transcriptions of lemma {longID} {lemma=} {transliteratedLemma=} {transliteratedLemmas[transliteratedLemma]=}"
#                         else: transliteratedLemmas[transliteratedLemma] = lemma
#                     senseNumber = elem.get('sensenumber')
#                     column_counts['sensenumber'][senseNumber] += 1

#                     after = elem.get('after')
#                     column_counts['after'][after] += 1
#                     if after: assert len(after) <= 2, f"{len(after)} {after=}"

#                     wClass = elem.get('class')
#                     column_counts['class'][wClass] += 1
#                     PoS = elem.get('pos')
#                     column_counts['pos'][PoS] += 1
#                     person = elem.get('person')
#                     column_counts['person'][person] += 1
#                     gender = elem.get('gender')
#                     column_counts['gender'][gender] += 1
#                     number = elem.get('number')
#                     column_counts['number'][number] += 1
#                     role = elem.get('role')
#                     column_counts['role'][role] += 1

#                     # Cross-checking
#                     # TODO: Could do much more of this
#                     if PoS=='noun': assert morph.startswith('N')
#                     if morph.startswith('N'): assert PoS=='noun'

#                     English = elem.get('english')
#                     if English == '.and': English = 'and' # at ISA 65:9!9
#                     if English:
#                         assert '.' not in English
#                         assert English.strip() == English # No leading or trailing spaces
#                         English = English.replace( ' ', '_' ).replace('’s',"'s").replace('s’',"s'").replace('’t',"'t").replace('’S',"'S") # brother's sons' don't LORD'S
#                         assert '’' not in English, f"{theirRef=} {wordOrMorpheme=} {English=}"
#                     else: English = '' # Instead of None
#                     assert '(et)' not in English and '(dm)' not in English, f"{English=}"

#                     # Do some on-the-fly fixes
#                     # Note: We can't handle the logic below with our SBE tables
#                     if gloss and 'temple' in gloss:
#                         # print( f"TEMPLE gloss {theirRef=} {wordOrMorpheme=} {gloss=} {English=}" )
#                         if 'ה' in wordOrMorpheme and 'כ' in wordOrMorpheme and 'ל' in wordOrMorpheme:
#                             # 'הֵיכַל' (hēykal) is ok
#                             assert 'ב' not in wordOrMorpheme
#                             assert 'ת' not in wordOrMorpheme
#                         if 'ב' in wordOrMorpheme and 'ת' in wordOrMorpheme:
#                             print( f"Changing gloss 'temple' to 'house' for {theirRef=} {wordOrMorpheme=} {gloss=} {English=}" )
#                             assert 'כ' not in wordOrMorpheme
#                             assert 'ל' not in wordOrMorpheme
#                             gloss = gloss.replace( 'temple', 'house' )
#                             never_happens
#                     if English and 'temple' in English:
#                         # print( f"TEMPLE English {theirRef=} {wordOrMorpheme=} {gloss=} {English=}" )
#                         if 'ה' in wordOrMorpheme and 'כ' in wordOrMorpheme and 'ל' in wordOrMorpheme:
#                             # ‘הֵיכַל’ (hēykal) is ok
#                             assert 'ב' not in wordOrMorpheme
#                             assert 'ת' not in wordOrMorpheme
#                         if 'ב' in wordOrMorpheme and 'ת' in wordOrMorpheme: # probably 'בֵּית'
#                             vPrint( 'Info', DEBUGGING_THIS_MODULE, f"  Changing English 'temple' to 'house' for {theirRef=} {wordOrMorpheme=} {gloss=} {English=}" )
#                             assert 'כ' not in wordOrMorpheme
#                             assert 'ל' not in wordOrMorpheme
#                             English = English.replace( 'temple', 'house' )
#                     # if (gloss and '[is]' in gloss) or (English and '[is]' in English):
#                     #     print( f"Have '[is]' in {theirRef=} {wordOrMorpheme=} {gloss=} {English=}" )
#                     #     halt
#                     # if gloss=='[is]' or English=='[is]' \
#                     # or (gloss and gloss[0]=='[' and gloss[-1]==']' and '_' not in gloss) \
#                     # or (English and English[0]=='[' and English[-1]==']' and '_' not in English):
#                     #     halt

#                     # Get all the parent elements so we can determine the nesting
#                     startElement = elem
#                     nestingBits = []
#                     for _safetyCheck in range( 22 ): # This is the max number of expected nesting levels -- unexpectedly high
#                         parentElem = parentMap[startElement]
#                         if parentElem.tag == 'sentence': break
#                         assert parentElem.tag in ('wg','c'), f"{elem.tag=} {theirRef=} {wordOrMorpheme=} {gloss=} {English=} {parentElem.tag=}"
#                         pClass, pRole, pRule = parentElem.get('class'), parentElem.get('role'), parentElem.get('rule')
#                         if parentElem.tag == 'c':
#                             # assert not pClass and not pRole and not pRule, f"{pClass=} {pRole=} {pRule=}" # Had pRole='o' somewhere
#                             compound = True
#                         else:
#                             assert parentElem.tag == 'wg'
#                         if pRole:
#                             if pRule: # have both
#                                 nestingBits.append( f'{pRole}={pRule}' )
#                             else: # only have role
#                                 nestingBits.append( pRole )
#                         elif pRule: # have no role
#                             nestingBits.append( pRule )
#                         # else: # no role or rule attributes on parent <wg>
#                         #     # assert pClass=='compound', f"{theirRef} has no role/rule {pClass=} {nestingBits}"
#                         #     print( f"{theirRef} has no role/rule {pClass=} {nestingBits}" ) # We now have empty wg's around the words for the entire sentence (but not including the <p> with <milestone>)
#                         startElement = parentElem
#                     else: we_ran_out_of_loops
#                     if len(nestingBits) >= max_nesting_level:
#                         max_nesting_level = len(nestingBits) + 1

#                     # Names have to match state.output_fieldnames:
#                     # ['FGRef','OSHBid','RowType','LFRef','LFNumRef',
#                     # 'Language','WordOrMorpheme','Unicode','Transliteration','After',
#                     # 'WordClass','PartOfSpeech','Person','Gender','Number','WordType','State','SDBH',
#                     # 'StrongNumberX','StrongLemma','Stem','Morphology','Lemma','SenseNumber',
#                     # 'CoreDomain','LexicalDomain', # 'ContextualDomain',
#                     # 'SubjRef','ParticipantRef','Frame',
#                     # 'Greek','GreekStrong',
#                     # 'EnglishGloss','MandarinGloss','ContextualGloss',
#                     # 'Nesting']
#                     entry = {'LFRef':theirRef, 'LFNumRef':longID, 'Language':lang, 'WordOrMorpheme':wordOrMorpheme,
#                                 'Unicode':elem.get('unicode'), 'Transliteration':elem.get('transliteration'), 'After':after,
#                                 'WordClass':wClass, 'Compound':compound, 'PartOfSpeech':PoS, 'Person':person, 'Gender':gender, 'Number':number,
#                                 'WordType':wordType, 'State':wordState, 'Role':role, 'SDBH':elem.get('sdbh'),
#                                 'StrongNumberX':elem.get('strongnumberx'), 'StrongLemma':elem.get('stronglemma'),
#                                 'Stem':stem, 'Morphology':morph, 'Lemma':lemma, 'SenseNumber':senseNumber,
#                                 'CoreDomain':elem.get('coredomain'), 'LexicalDomain':elem.get('lexdomain'), 'Frame':elem.get('frame'),
#                                 'SubjRef':elem.get('subjref'), 'ParticipantRef':elem.get('participantref'), # 'ContextualDomain':elem.get('contextualdomain'),
#                                 'Greek':elem.get('greek'), 'GreekStrong':elem.get('greekstrong'),
#                                 'EnglishGloss':English, 'MandarinGloss':elem.get('mandarin'), 'ContextualGloss':gloss,
#                                 'Nesting':'/'.join(reversed(nestingBits)) }
#                     assert len(entry) == len(state.morpheme_output_fieldnames)-3, f"{len(entry)=} vs {len(state.morpheme_output_fieldnames)=}" # Three more fields to be added below
#                     # for k,v in entry.items():
#                     #     if v: non_blank_counts[k] += 1
#                     tempWordsAndMorphemes.append( entry )
#                     # dPrint( 'Normal', DEBUGGING_THIS_MODULE, f"\n  ({len(entry)}) {entry}" ) # 28
#                     # if len(tempWordsAndMorphemes) > 5: halt

#             vPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"    Got {len(tempWordsAndMorphemes):,} words/morphemes in {BBB} {chapterNumber}")
#             assert len(set(longIDs)) == len(longIDs), f"Should be no duplicates in {longIDs=}"

#             # Note that because of the phrase/clause nesting, we can get the word fields in the wrong order
#             #   so we sort them, before adjusting the formatting to what we're after
#             # We sort by the Clear.Bible longID (2nd item in tuple, which already has the leading 'o' removed)
#             sortedTempWordsAndMorphemes = sorted( tempWordsAndMorphemes, key=lambda t: t['LFNumRef'] )

#             # Adjust to our references and with just the data that we need to retain
#             # Build a ref/id dictionary as we go
#             for j,firstEntryAttempt in enumerate( sortedTempWordsAndMorphemes ):
#                 longID = firstEntryAttempt['LFNumRef']
                
#                 if longID.endswith( 'ה' ):  # it's an article (vowel after preposition)
#                     # print(f"Got article {longID=}")
#                     assert firstEntryAttempt['WordOrMorpheme'] is None # No wordOrMorpheme
#                     assert firstEntryAttempt['ContextualGloss'] is None # No gloss
#                     english = firstEntryAttempt['EnglishGloss']
#                     wordType = firstEntryAttempt['WordType']
#                     assert wordType == 'definite article'
#                     # print(f"Got article {longID=} with '{english}' {wType=}")
#                     # Add the article gloss to the previous entry
#                     lastExpandedEntry = state.maculaHebrewWordsAndMorphemes[-1] # We'll edit the last dict entry in place
#                     lastExpandedEntry['EnglishGloss'] = f"{lastExpandedEntry['EnglishGloss']}_{english if english else 'THE'}" # Why wasn't the gloss there?
#                     # else: print(f"{longID} There wasn't an English gloss!!!"); halt
#                 else: # a normal word or morpheme entry
#                     try: nextLongID = sortedTempWordsAndMorphemes[j+1]['LFNumRef']
#                     except IndexError: nextLongID = '1'
#                     if nextLongID.endswith('ה'): # we have to skip this one
#                         try: nextLongID = sortedTempWordsAndMorphemes[j+1+1]['LFNumRef']
#                         except IndexError: nextLongID = '1'
#                     assert nextLongID != longID, f"Should be no duplicate IDs: {j=} {longID=} {nextLongID=} {firstEntryAttempt}"
#                     if nextLongID.endswith( '1' ): # current entry is end of a word
#                         mwType = 'w' if longID.endswith( '1' ) else 'M'
#                     else: # the above works but fails when the first morpheme of a word is (wrongly) missing
#                         # print(f"{longID=} going to {nextLongID=} ")
#                         assert len(nextLongID) == len(longID) == 12 # leading 'o' has already been removed
#                         nextLongIDWordBit = nextLongID[:-1]
#                         longIDWordBit = longID[:-1]
#                         if nextLongIDWordBit == longIDWordBit: # we're still in the same word
#                             mwType = 'm' # There's a following part of this word
#                         else: # we going on to a new word, but the first part is missing
#                             mwType = 'w' if longID.endswith( '1' ) else 'M'
#                     suffix = '' if mwType=='w' else SUFFIX_DICT[longID[-1]]
#                     if firstEntryAttempt['Language'] == 'A': mwType = f'A{mwType}' # Assume Hebrew; mark Aramaic
#                     ourRef = f"{BBB}_{firstEntryAttempt['LFRef'][4:].replace( '!', 'w')}{suffix}"
#                     assert longID not in refDict
#                     refDict[longID] = ourRef # Create dict for next loop
#                     # print(f"{longID=} {nextLongID=} {mwType=} {ourRef=}")
#                     newExpandedDictEntry = {'FGRef':ourRef, 'RowType':mwType, **firstEntryAttempt}
#                     assert len(newExpandedDictEntry) == len(state.morpheme_output_fieldnames)-1, f"{len(newExpandedDictEntry)=} vs {len(state.morpheme_output_fieldnames)=}" # OSHBid field to be added below
#                     state.maculaHebrewWordsAndMorphemes.append( newExpandedDictEntry )
#     # if 1:
#     #     for n,currentEntry in enumerate(state.maculaHebrewWordsAndMorphemes):
#     #         print(f"{n} ({len(currentEntry)}) {currentEntry}")
#     #         if n > 10: break
#     #     halt

#     # Adjust frames to our references
#     for lfRow in state.maculaHebrewWordsAndMorphemes:
#         ourRef = lfRow['FGRef']
#         frame = lfRow['Frame'] # e.g., 'A0:010010010031; A1:010010010052;010010010072;' but we want to convert it to our word numbers
#         if frame:
#             # print( f"{ourRef} {frame=}" )
#             startIndex = 0
#             while ( match := wordnumber_regex.search(frame, startIndex) ):
#                 try: frame = f'{frame[:match.start()]}{refDict[match.group(0)]}{frame[match.end():]}'
#                 except KeyError: # Seems to be no match for the ref in the frame??? Probably because it's a pointer to a word group or something???
#                     logging.critical( f"Unable to match {ourRef} frame part: {match.group(0)}" )
#                 startIndex = match.start() + 5
#             # print( f"  {frame=}" )
#             lfRow['Frame'] = frame

#     vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  Got total of {len(state.maculaHebrewWordsAndMorphemes):,} words/morphemes")
#     vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"      Max nesting level = {max_nesting_level}" )
#     if 1:  # Just so we can turn it off and on easily
#         vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"\nDetailed counts for {len(column_counts):,} fields:")
#         for field_name in column_counts:
#             this_set = column_counts[field_name]
#             this_set_length = len(this_set)
#             if this_set_length < 55:
#                 vPrint( 'Normal', DEBUGGING_THIS_MODULE, # Sort them with most frequent first
#                     f"\n{field_name}: ({this_set_length}) {dict(sorted(this_set.items(), key=lambda x:x[1], reverse=True))}" )
#             else: vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"\n{field_name} has {this_set_length:,} unique options -- display suppressed." )
#     # if 1:
#     #     for n,currentEntry in enumerate(state.maculaHebrewWordsAndMorphemes):
#     #         assert len(currentEntry) == len(state.output_fieldnames)-1
#     #         if n < 5 or 'THE' in currentEntry['EnglishGloss']: print(f"{n} ({len(currentEntry)}) {currentEntry}")
#     #     halt
#     return True
# # end of convert_ClearMaculaOT_to_our_TSV.loadMaculaHebrewLowFatXMLGlosses


def loadMaculaHebrewNodesXMLGlosses() -> bool:
    """
    Reads in the Clear.Bible 'nodes' XML chapter files
        and then finds all inner <Node> entries (keeping track of their parents, e.g., other <Node>s or <Sentence>)
    
    Loads all the inner <Node> entries for the chapter into a temporary list
        and sorts them by their numerical id, e.g., <Node n="o010030040011" = obbcccvvvwwws
            but note: it can be <Node n="o010030060101ה" for definite article after preposition

    Extract glosses out of fields 
    Reorganise columns and add our extra columns
    """
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"\nLoading Clear.Bible OT 'nodes' glosses from {state.macula_Hebrew_Nodes_XML_input_folderpath}/…" )
    
    max_nesting_level = 0
    column_counts = defaultdict(lambda: defaultdict(int))
    # non_blank_counts = defaultdict(int)
    refDict = {}
    for referenceNumber in range(1, 39+1):
        BBB = BibleOrgSysGlobals.loadedBibleBooksCodes.getBBBFromReferenceNumber( referenceNumber )
        vPrint( 'Info', DEBUGGING_THIS_MODULE, f"  Loading Macula Hebrew Nodes {BBB} XML files…")
        Uuu = BibleOrgSysGlobals.loadedBibleBooksCodes.getUSFMAbbreviation( BBB )
        if Uuu=='Hos': Uuu = 'HOS' # Fix inconsistency in naming patterns
        filenameTemplate = MACULA_HEBREW_NODES_XML_INPUT_FILENAME_TEMPLATE.replace( 'NN', str(referenceNumber).zfill(2) ).replace( 'Uuu', Uuu )

        for chapterNumber in range(1, 150+1):
            filename = filenameTemplate.replace( 'CCC', str(chapterNumber).zfill(3) )
            try:
                chapterTree = ElementTree.parse( state.macula_Hebrew_Nodes_XML_input_folderpath.joinpath( filename ) )
            except FileNotFoundError:
                break # gone beyond the number of chapters

            # First make a table of parents so we can find them later
            parentMap = {child:parent for parent in chapterTree.iter() for child in parent if child.tag in ('m','c','Node')}
            dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"  Loaded {len(parentMap):,} parent entries." )

            # Now load all the morpheme (m) fields for the chapter into a temporary list
            tempWordsAndMorphemes = []
            longIDs = []
            transliteratedLemmas = {}
            lastGloss = lastEnglish = None
            for elem in chapterTree.getroot().iter():
                # print( f"{elem=}" )
                if elem.tag == 'm': # ignore all the others -- there's enough info in here
                    for attribName in elem.attrib:
                        assert attribName in EXPECTED_MACULA_HEBREW_NODES_WORD_ATTRIBUTES, f"loadMaculaHebrewNodeXMLGlosses(): unexpected {attribName=}"

                    wordOrMorpheme = elem.text
                    theirRef = elem.get('word') # e.g., "GEN 1:1!1"
                    # print( f"{theirRef=} {wordOrMorpheme=}" )

                    longID = elem.get('{http://www.w3.org/XML/1998/namespace}id') # e.g., o010010050031 = obbcccvvvwwws
                    longIDs.append( longID )
                    assert longID.startswith( 'o' ) # Stands for OldTestament
                    longID = longID[1:] # remove 'o' prefix
                    if len(longID) > 12: # it's an article (vowel after preposition)
                        assert len(longID) == 13
                        assert longID.endswith( 'ה' )
                        assert longID[:-1].isdigit()
                    else:
                        assert len(longID) == 12
                        assert longID[:].isdigit()

                    gloss = elem.get('gloss')
                    if gloss:
                        if '(et)' in gloss or '(dm)' in gloss:
                            # print( f"(et) or (dm) {theirRef=} {wordOrMorpheme=} {gloss=}" )
                            if '(et)' in gloss and wordOrMorpheme not in ('אֵ֥ת','אֶת','אֶֽת','אֵ֚ת','אֵ֖ת','אֵ֛ת','אֵ֣ת','אֶׄתׄ','אֵת֩','אֵ֤ת','אֶ֨ת','אֵ֡ת','אֵ֧ת','אֵ֠ת','אֵ֗ת','אֵת','אֵֽת','אֶ֥ת','אֵ֝֗ת','אֵ֝ת','אֵת֮','אֶתּ'):
                                halt
                            if '(dm)' in gloss and wordOrMorpheme not in ('כִּי','כִּ֣י','כִּי֩','כִּ֗י','כִּ֥י','כִּֽי','כִּ֚י','כִּ֛י','כִּ֤י','כִּ֠י','כִּ֧י','כִֽי','כִּ֡י','כִּ֖י','כִּ֞י','כִ֤י','כִ֥י','כִּ֨י','כִי','כִ֗י','כִ֔י','כִּ֭י','כִּ֘י','כִּ֝֗י','כִּ֬י','כִּ֪י','כִ֛י','כִּ֩י'):
                                if theirRef not in ('DAN 1:8!5','DAN 1:8!15') or wordOrMorpheme not in ('אֲשֶׁ֧ר','אֲשֶׁ֖ר'):
                                    halt
                        gloss = ( gloss.replace( '.', '_' ) # Change to our system
                                    .replace( '(et)', 'DOM' ) # Change to our 'DOM' = DirectObjectMarker
                                    .replace( '(dm)', '' if theirRef.startswith('DAN 1:8!') else 'if/because') # What is dm supposed to mean?
                                )
                        assert '’' not in gloss, f"{theirRef=} {wordOrMorpheme=} {gloss=}"

                    lang = elem.get('lang')
                    column_counts['lang'][lang] += 1
                    assert lang in 'HA'
                    wordType = elem.get('type')
                    column_counts['type'][wordType] += 1
                    # if wordType:
                    #     print( f"{theirRef=} {wordOrMorpheme=} {gloss=} {lang=} {wordType=}" )
                    #     assert wordType in ('adjective','cardinal number','common','definite article','direct object marker','jussive','ordinal number','participle active','pronominal','qatal','relative','wayyiqtol','yiqtol'), \
                    #                         f"{theirRef=} {wordOrMorpheme=} {gloss=} {lang=} {wordType=}"
                    wordState = elem.get('state')
                    column_counts['state'][wordState] += 1
                    if wordState:
                        # What is 'determined' in Ezra 4:8!5, etc.
                        assert wordState in ('absolute','construct','determined'), f"Found unexpected {wordState=}"
                    # dPrint( 'Info', DEBUGGING_THIS_MODULE, f"    {ref} {longID} {lang} '{wordOrMorpheme}' {English=} {gloss=}")

                    compound = elem.get('compound')
                    assert not compound # it seems to have gone
                    column_counts['compound'][compound] += 1

                    stem = elem.get('stem')
                    column_counts['stem'][stem] += 1
                    morph = elem.get('morph')
                    # column_counts['morph'][morph] += 1 # There's over 700 different variations
                    lemma = elem.get('lemma')
                    if lemma:
                        # I think this is a Clear.Bible systematic error
                        # AssertionError: unicodedata.name(char)='HEBREW ACCENT OLE' lemma='אֶ֫רֶץ' longID='010010010072'
                        for char in lemma:
                            if 'ACCENT' in unicodedata.name(char):
                                logger = logging.critical if DEBUGGING_THIS_MODULE else logging.error
                                logger( f"Unexpected character in Nodes lemma '{unicodedata.name(char)}' {lemma=} {longID=}" )
                        lemma = removeHebrewCantillationMarks( lemma )
                        for char in lemma:
                            assert 'ACCENT' not in unicodedata.name(char), f"{unicodedata.name(char)=} {lemma=} {longID=}"
                        transliteratedLemma = transliterate_Hebrew( lemma )
                        # If the following fails, our lemmas aren't unique
                        if transliteratedLemma in transliteratedLemmas:
                            assert transliteratedLemmas[transliteratedLemma] == lemma, f"Multiple transcriptions of lemma {longID} {lemma=} {transliteratedLemma=} {transliteratedLemmas[transliteratedLemma]=}"
                        else: transliteratedLemmas[transliteratedLemma] = lemma
                    senseNumber = elem.get('SenseNumber')
                    column_counts['sensenumber'][senseNumber] += 1

                    after = elem.get('after')
                    column_counts['after'][after] += 1
                    if after: assert len(after) <= 2, f"{len(after)} {after=}"

                    wClass = elem.get('class')
                    column_counts['class'][wClass] += 1
                    PoS = elem.get('pos')
                    column_counts['pos'][PoS] += 1
                    person = elem.get('person')
                    column_counts['person'][person] += 1
                    gender = elem.get('gender')
                    column_counts['gender'][gender] += 1
                    number = elem.get('number')
                    column_counts['number'][number] += 1
                    role = elem.get('role')
                    column_counts['role'][role] += 1

                    # Cross-checking
                    # TODO: Could do much more of this
                    if PoS=='noun': assert morph.startswith('N')
                    if morph.startswith('N'): assert PoS=='noun'

                    English, Mandarin = elem.get('english'), elem.get('mandarin')
                    if English == '.and': English = 'and' # at ISA 65:9!9
                    if English:
                        assert '.' not in English
                        assert English.strip() == English # No leading or trailing spaces
                        English = English.replace( ' ', '_' ).replace('’s',"'s").replace('s’',"s'").replace('’t',"'t").replace('’S',"'S") # brother's sons' don't LORD'S
                        assert '’' not in English, f"{theirRef=} {wordOrMorpheme=} {English=}"
                    else: English = '' # Instead of None
                    assert '(et)' not in English and '(dm)' not in English, f"{English=}"

                    # None of these are actually expected to be there (but they're filled from higher level elements, i.e., parent elements)
                    greekWord, greekStrong = elem.get('Greek'), elem.get('GreekStrong')
                    frame, subjRef, participantRef = elem.get('Frame'), elem.get('SubjRef'), elem.get('Ref')

                    # Do some on-the-fly fixes
                    # Note: We can't handle the logic below with our SBE tables
                    if gloss:
                        if 'temple' in gloss:
                            # print( f"{theirRef=} {wordOrMorpheme=} {gloss=} {English=}" )
                            if 'ה' in wordOrMorpheme and 'כ' in wordOrMorpheme and 'ל' in wordOrMorpheme:
                                # 'הֵיכַל' (hēykal) is ok
                                assert 'ב' not in wordOrMorpheme
                                assert 'ת' not in wordOrMorpheme
                            if 'ב' in wordOrMorpheme and 'ת' in wordOrMorpheme:
                                print( f"Changing gloss 'temple' to 'house' for {theirRef=} {wordOrMorpheme=} {gloss=} {English=}" )
                                assert 'כ' not in wordOrMorpheme
                                assert 'ל' not in wordOrMorpheme
                                gloss = gloss.replace( 'temple', 'house' )
                                never_happens
                        # Place genitive 'of' at the end of the construct form, not at the beginning of the absolute form
                        # NOTE: THIS ISN'T NECESSARILY CORRECT if the (following) absolute word is a possessive pronoun, e.g., house_of their
                        #           but we can fix it again later when we do reordering
                        if wordState == 'construct' and not gloss.endswith( 'of' ):
                            # print( f"{theirRef=} {wordOrMorpheme=} {wordType=} {wordState=} {gloss=} {English=}")
                            gloss = f'{gloss}_of'
                        elif wordState == 'absolute' and gloss.startswith ( 'of_' ):
                            # print( f"{theirRef=} {wordOrMorpheme=} {wordType=} {wordState=} {gloss=} {English=}")
                            # assert gloss.startswith( 'off' ) or gloss.startswith( 'of_' )
                            # if gloss.startswith( 'of_' ):
                            gloss = gloss[3:]
                    if English:
                        if 'temple' in English:
                            # print( f"{theirRef=} {wordOrMorpheme=} {gloss=} {English=}" )
                            if 'ה' in wordOrMorpheme and 'כ' in wordOrMorpheme and 'ל' in wordOrMorpheme:
                                # ‘הֵיכַל’ (hēykal) is ok
                                assert 'ב' not in wordOrMorpheme
                                assert 'ת' not in wordOrMorpheme
                            if 'ב' in wordOrMorpheme and 'ת' in wordOrMorpheme: # probably 'בֵּית'
                                vPrint( 'Info', DEBUGGING_THIS_MODULE, f"  Changing English 'temple' to 'house' for {theirRef=} {wordOrMorpheme=} {gloss=} {English=}" )
                                assert 'כ' not in wordOrMorpheme
                                assert 'ל' not in wordOrMorpheme
                                English = English.replace( 'temple', 'house' )
                        # Place genitive 'of' at the end of the construct form, not at the beginning of the absolute form
                        # NOTE: THIS ISN'T NECESSARILY CORRECT if the (following) absolute word is a possessive pronoun, e.g., house_of their
                        #           but we can fix it again later when we do reordering
                        if wordState == 'construct' and not English.endswith( 'of' ):
                            # print( f"{theirRef=} {wordOrMorpheme=} {wordType=} {wordState=} {gloss=} {English=}")
                            English = f'{English}_of'
                        elif wordState == 'absolute' and English.startswith ( 'of_' ):
                            # print( f"{theirRef=} {wordOrMorpheme=} {wordType=} {wordState=} {gloss=} {English=}")
                            # assert English.startswith( 'off' ) or English.startswith( 'of_' )
                            # if English.startswith( 'of_' ):
                            English = English[3:]

                    # Get all the parent elements so we can determine the nesting
                    startElement = elem
                    unicodeField, strongNumberX = elem.get('Unicode'), elem.get('StrongNumberX')
                    assert unicodeField is None and strongNumberX is None, f"{theirRef} {unicodeField=} {strongNumberX}"
                    nestingBits = []
                    for _safetyCheck in range( 31 ): # This is the max number of expected nesting levels -- unexpectedly high
                        parentElem = parentMap[startElement]
                        # print( f"  {_safetyCheck}: {parentElem=} {parentElem.attrib=}" )
                        if parentElem.tag == 'Tree': break
                        assert parentElem.tag in ('c','Node','Tree'), f"{elem.tag=} {theirRef=} {wordOrMorpheme=} {gloss=} {English=} {parentElem.tag=}"
                        pClass, pRole, pRule = parentElem.get('class'), parentElem.get('role'), parentElem.get('Rule')
                        # print( f"   {pClass=} {pRole=} {pRule=}")
                        if parentElem.tag == 'c':
                            # assert not pClass and not pRole and not pRule, f"{pClass=} {pRole=} {pRule=}" # Had pRole='o' somewhere
                            compound = True
                            if theirRef not in ('1KI 4:8!3','1KI 4:8!4', # glosses Ben- Hur
                                                '2KI 12:21!8','2KI 12:21!9', # glosses Beth- Millo
                                                'NEH 12:39!5','NEH 12:39!6', # glosses [the]_gate 'of_(the)_Jeshanah'
                                                'PSA 102:4!7','PSA 102:4!8', # glosses a_hearth
                                                'SNG 6:12!7','SNG 6:12!8', # glosses nadib
                                                'ISA 2:20!16','ISA 2:20!17', # glosses of_moles
                                                ):
                                assert not gloss, f"{theirRef} {gloss=} {English=} {Mandarin=}"
                            assert not English and not Mandarin, f"{theirRef} {gloss=} {English=} {Mandarin=}"
                            gloss, English, Mandarin = parentElem.get('gloss'), parentElem.get('english'), parentElem.get('mandarin')

                            # Here's we do some magic to split the compound glosses if possible
                            # print( f"  SPLITA {theirRef} {gloss=} {English=}")
                            for compoundWord,compoundReplacement in (
                                            ('toanger', 'to_anger'), # Seems to be a systematic error in the Macula Hebrew data

                                            ('Abednego', 'Abed-nego'), ('Abiezrite', 'Abi-ezrite'), ('Asahel', 'Asah-el'),
                                            ('Bathsheba', 'Bath-sheba'), ('Beersheba', 'Beer-sheba'), ('Bethel', 'Beth-el'), ('Bethlehem', 'Beth-lehem'),
                                            ('Dizahab', 'Di-zahab'),
                                            ('Ebenezer', 'Eben-ezer'), ('Esarhaddon', 'Esar-haddon'),
                                            ('Heliopolis', 'Beth-Shemesh'), ('Hephzibah', 'Hephzi-bah'),
                                            ('Ichabod', 'I-chabod'), ('Immanuel', 'Immanu-el'),
                                            ('Malchishua', 'Malchi-shua'), ('Melchizedek', 'Melchi-zedek'), ('Mephibosheth', 'Mephi-bosheth'), ('Mesopotamia', 'Aram-Naharyim'), ('Mezahab', 'Me-zahab'),
                                            ('Nebuzaradan', 'Nebuzar-adan'),
                                            ('Pedahzur', 'Pedah-zur'), ('Potiphera', 'Poti-phera'),
                                            ('Sarsechim', 'Sar-sechim'), ('Sarsekim', 'Sar-sekim'),
                                            ('Zurishaddai', 'Zuri-shaddai'),
                                            
                                            ('Aram of ', 'Aram_of.'),('Arameans of ', 'Arameans_of.'),
                                            ('house of ', 'house_of.'),
                                            ('the Rock of ', 'the_Rock_of.'),
                                            ('the son of ', 'the_son_of.'),('the.son.of', 'the_son_of'),('son of ', 'son_of.'),('son.of', 'son_of'),
                                            ('spring of ', 'spring_of.'),
                                            ('stone of ', 'stone_of.'),('the.stone.of.', 'the_stone_of.'),
                                            ('the.threshing.floor.of', 'the_threshing_floor_of'),('threshing floor of ', 'threshing_floor_of.'),
                                            ('[was].in.the.valley.of.', '[was]_in_the_valley_of.'), ('Valley of ', 'Valley_of.'),('valley of ', 'valley_of.'),('the.valley.of.', 'the_valley_of.'),('the.Valley.of.', 'the_Valley_of.'),
                                            ('well of ', 'well_of.'),('of.the.Well.of.', 'of_the_Well_of.'),
                                            ('wine press of ', 'winepress_of.'),

                                            ('and.Kephar.(the).Ammonah', 'and_Kephar.(the)_Ammonah'),
                                            ('Baal of Peor', 'Baal_of.Peor'),
                                            ('[is].', '[is]_'),('[was].', '[was]_'),
                                            ('[was.at].Beth.Eked.of.the.Shepherds', '[was_at]_Beth.Eked_of.the_Shepherds'),
                                            ('Hamath the great', 'Hamath.the_great'),
                                            ('Kir of Moab', 'Kir_of.Moab'),
                                            ('Ramah of the Negeb', 'Ramah_of.the_Negeb'),('Ramoth of the Negev', 'Ramoth_of.the_Negev'),
                                            ('.[Ben].Hinnom', '_[Ben].Hinnom'),('.Ben.Hinnom', '_Ben.Hinnom'),
                                                ('in.[the].Valley.of.Salt', 'in_[the]_Valley_of.Salt'),
                                            ('of Beth', 'of_Beth'),('of.Beth', 'of_Beth'),('of-Beth', 'of_Beth'),
                                            ('of.Col-', 'of_Col-'),
                                            ('Abel of_Beth-maacah', 'Abel.of.Beth.maacah'), # SA2_20:15 not ideal
                                            ('of.the.tower.of.Shechem', 'of_the_tower_of.Shechem'),
                                            ('Zela ~ Haeleph', 'Zela.Haeleph'),
                                            ):
                                if gloss: gloss = gloss.replace( compoundWord, compoundReplacement )
                                if English: English = English.replace( compoundWord, compoundReplacement )
                            if English.lower().startswith('tower of '): English = f"{English[:8]}.{English[9:]}"
                            # print( f"  SPLITB {theirRef} {gloss=} {English=}")
                            if gloss:
                                if '-' in gloss:
                                    # gloss = gloss.replace( 'of.', 'of_' ) # This seems to be a common one
                                    gloss = gloss.replace( '.', '_' ) # but also '[is].Beth-
                                    # assert '.' not in gloss, f"COMPOUND WILL LOSE GLOSS DOT in {ourRef=} {theirRef=} {gloss=} {English=}"
                                    glossParts = gloss.split( '-' )
                                    if len(glossParts) == 2:
                                        if lastGloss == f'{glossParts[0]}-': # Assume this is now the second part
                                            gloss = f'-{glossParts[1]}'
                                            # print( f"    Changed-B to {gloss=}" )
                                        else: # Assume that this is the first part
                                            gloss = f'{glossParts[0]}-'
                                            # print( f"    Changed-A to {gloss=}" )
                                    elif len(glossParts) == 4:
                                        if lastGloss == f'{glossParts[0]}-': # Assume this is now the second part
                                            gloss = f'-{glossParts[1]}-'
                                            # print( f"    Changed-B to {gloss=}" )
                                        elif lastGloss == f'-{glossParts[1]}-': # Assume this is now the third part
                                            gloss = f'-{glossParts[2]}-'
                                            # print( f"    Changed-B to {gloss=}" )
                                        elif lastGloss == f'-{glossParts[2]}-': # Assume this is now the fourth part
                                            gloss = f'-{glossParts[3]}'
                                            # print( f"    Changed-B to {gloss=}" )
                                        else: # Assume that this is the first part
                                            gloss = f'{glossParts[0]}-'
                                            # print( f"    Changed-A to {gloss=}" )
                                    else: print( f"    TOO MANY HYPHENS in {ourRef} compound {gloss=}" )
                                elif '.' in gloss:
                                    glossParts = gloss.split( '.' )
                                    if len(glossParts) == 2:
                                        if lastGloss == glossParts[0]: # Assume this is now the second part
                                            gloss = glossParts[1]
                                            # print( f"    Changed.B to {gloss=}" )
                                        else: # Assume that this is the first part
                                            gloss = glossParts[0]
                                            # print( f"    Changed.A to {gloss=}" )
                                    elif len(glossParts) == 3:
                                        if lastGloss == glossParts[0]: # Assume this is now the second part
                                            gloss = glossParts[1]
                                            # print( f"    Changed.B to {gloss=}" )
                                        elif lastGloss == glossParts[1]: # Assume this is now the third part
                                            gloss = glossParts[2]
                                            # print( f"    Changed.C to {gloss=}" )
                                        else: # Assume that this is the first part
                                            gloss = glossParts[0]
                                            # print( f"    Changed.A to {gloss=}" )
                                    else: print( f"    TOO MANY PERIODS in {ourRef} compound {gloss=}" )
                                else: print( f"    NO DIVIDERS in {ourRef} compound {gloss=}" )
                            if English:
                                if '-' in English:
                                    English = English.replace( '.', '_' ) # e.g., valley_of.Iphtah-
                                    # assert '.' not in English, f"COMPOUND WILL LOSE ENGLISH DOT in {ourRef=} {theirRef=} {gloss=} {English=}"
                                    englishParts = English.split( '-' )
                                    if len(englishParts) == 2:
                                        if lastEnglish == f'{englishParts[0]}-': # Assume this is now the second part
                                            English = f'-{englishParts[1]}'
                                            # print( f"    Changed-B to {English=}" )
                                            if gloss == 'Beth': print( f"Deleting BETH {ourRef=} {theirRef=} {glossParts=} {englishParts=} {lastGloss=} {lastEnglish=}" )
                                        else: # Assume that this is the first part
                                            English = f'{englishParts[0]}-'
                                            # print( f"    Changed-A to {English=}" )
                                    elif len(englishParts) == 3:
                                        if lastEnglish == f'{englishParts[0]}-': # Assume this is now the second part
                                            English = f'-{englishParts[1]}-'
                                            # print( f"    Changed-B to {English=}" )
                                        elif lastEnglish == f'-{englishParts[1]}-': # Assume this is now the third part
                                            English = f'-{englishParts[2]}'
                                            # print( f"    Changed-C to {English=}" )
                                        else: # Assume that this is the first part
                                            English = f'{englishParts[0]}-'
                                            # print( f"    Changed-A to {English=}" )
                                    elif len(englishParts) == 4:
                                        if lastEnglish == f'{englishParts[0]}-': # Assume this is now the second part
                                            English = f'-{englishParts[1]}-'
                                            # print( f"    Changed-B to {English=}" )
                                        elif lastEnglish == f'-{englishParts[1]}-': # Assume this is now the third part
                                            English = f'-{englishParts[2]}'
                                            # print( f"    Changed-C to {English=}" )
                                        elif lastEnglish == f'-{englishParts[2]}-': # Assume this is now the fourth part
                                            English = f'-{englishParts[3]}'
                                            # print( f"    Changed-D to {English=}" )
                                        else: # Assume that this is the first part
                                            English = f'{englishParts[0]}-'
                                            # print( f"    Changed-A to {English=}" )
                                    else: print( f"    TOO MANY HYPHENS in {ourRef} compound {English=}" )
                                elif '.' in English:
                                    englishParts = English.split( '.' )
                                    if len(englishParts) == 2:
                                        if lastEnglish == englishParts[0]: # Assume this is now the second part
                                            English = englishParts[1]
                                            # print( f"    Changed.B to {English=}" )
                                            if gloss == 'Beth': print( f"Deleting BETH {ourRef=} {theirRef=} {glossParts=} {englishParts=} {lastGloss=} {lastEnglish=}" ); halt
                                        else: # Assume that this is the first part
                                            English = englishParts[0]
                                            # print( f"    Changed.A to {English=}" )
                                    elif len(englishParts) == 3:
                                        if lastEnglish == englishParts[0]: # Assume this is now the second part
                                            English = englishParts[1]
                                            # print( f"    Changed.B to {English=}" )
                                        elif lastEnglish == englishParts[1]: # Assume this is now the third part
                                            English = englishParts[2]
                                            # print( f"    Changed.C to {English=}" )
                                        else: # Assume that this is the first part
                                            English = englishParts[0]
                                            # print( f"    Changed.A to {English=}" )
                                    elif len(englishParts) == 4: # Abel of Beth Maacah
                                        if lastEnglish == englishParts[0]: # Assume this is now the second part
                                            English = englishParts[1]
                                            # print( f"    Changed.B to {English=}" )
                                        elif lastEnglish == englishParts[1]: # Assume this is now the third part
                                            English = englishParts[2]
                                            # print( f"    Changed.C to {English=}" )
                                        elif lastEnglish == englishParts[2]: # Assume this is now the fourth part
                                            English = englishParts[3]
                                            # print( f"    Changed.D to {English=}" )
                                        else: # Assume that this is the first part
                                            English = englishParts[0]
                                            # print( f"    Changed.A to {English=}" )
                                    else: print( f"{ourRef=} {theirRef=} {glossParts=} {englishParts=} {lastGloss=} {lastEnglish=}" ); halt
                                elif ' ' in English:
                                    englishParts = English.split( ' ' )
                                    if len(englishParts) == 2:
                                        if lastEnglish == englishParts[0]: # Assume this is now the second part
                                            English = englishParts[1]
                                            # print( f"    Changed B to {English=}" )
                                            if gloss == 'Beth': print( f"Deleting BETH {ourRef=} {theirRef=} {glossParts=} {englishParts=} {lastGloss=} {lastEnglish=}" ); halt
                                        else: # Assume that this is the first part
                                            English = englishParts[0]
                                            # print( f"    Changed A to {English=}" )
                                    else: print( f"    TOO MANY SPACES in {ourRef} compound {English=}" )
                                else: print( f"    NO DIVIDERS in {ourRef} compound {English=}" )
                        else:
                            assert parentElem.tag == 'Node'
                            if parentElem.get('Cat'):
                                # print( f"{theirRef} {PoS=} {wClass=} {parentElem.get('Cat')=}")
                                if not wClass:
                                    wClass = parentElem.get('Cat') # One level above the 'm'
                                elif not role \
                                or (len(role)>1 and len(parentElem.get('Cat'))==1):
                                    role = parentElem.get('Cat') # Next level higher now (at least)
                            if not senseNumber:
                                senseNumber = parentElem.get('SenseNumber')
                            if not greekWord:
                                greekWord = parentElem.get('Greek')
                            if not greekStrong:
                                greekStrong = parentElem.get('GreekStrong')
                            if not frame:
                                frame = parentElem.get('Frame')
                            if not subjRef:
                                subjRef = parentElem.get('SubjRef')
                            if not participantRef:
                                participantRef = parentElem.get('Ref')
                            if parentElem.get('Unicode'):
                                assert not unicodeField
                                unicodeField = parentElem.get('Unicode')
                            if parentElem.get('StrongNumberX'):
                                assert not strongNumberX
                                strongNumberX = parentElem.get('StrongNumberX')
                        if pRole:
                            if pRule: # have both
                                nestingBits.append( f'{pRole}={pRule}' )
                            else: # only have role
                                nestingBits.append( pRole )
                        elif pRule: # have no role
                            nestingBits.append( pRule )
                        # else: # no role or rule attributes on parent <wg>
                        #     # assert pClass=='compound', f"{theirRef} has no role/rule {pClass=} {nestingBits}"
                        #     print( f"{theirRef} has no role/rule {pClass=} {nestingBits}" ) # We now have empty wg's around the words for the entire sentence (but not including the <p> with <milestone>)
                        # print( f"    {nestingBits=}")
                        startElement = parentElem
                    else: we_ran_out_of_loops
                    if len(nestingBits) >= max_nesting_level:
                        max_nesting_level = len(nestingBits) + 1

                    if gloss: assert '.' not in gloss, print( f"Warning: REMAINING DOT IN GLOSS {ourRef=} {theirRef=} {gloss=} {English=}" )
                    # if gloss and '.' in gloss: print( f"Warning: REMAINING DOT IN GLOSS {ourRef=} {theirRef=} {gloss=} {English=}" )
                    if English: assert '.' not in English, print( f"Warning: REMAINING DOT IN ENGLISH {ourRef=} {theirRef=} {gloss=} {English=}" )
                    # if English and '.' in English: print( f"Warning: REMAINING DOT IN ENGLISH {ourRef=} {theirRef=} {gloss=} {English=}" )

                    # if (gloss and '[is]' in gloss) or (English and '[is]' in English):
                    #     print( f"   Have '[is]' in {theirRef=} {wordOrMorpheme=} {gloss=} {English=}" )
                    if gloss in ('[is]','[was]') or English in ('[is]','[was]') \
                    or (gloss and gloss[0]=='[' and gloss[-1]==']' and '_' not in gloss) \
                    or (English and English[0]=='[' and English[-1]==']' and '_' not in English):
                        print( f"   Have potential problem in {theirRef=} {wordOrMorpheme=} {gloss=} {English=}" )
                        halt

                    # Names have to match state.output_fieldnames:
                    # ['FGRef','OSHBid','RowType','LFRef','LFNumRef',
                    # 'Language','WordOrMorpheme','Unicode','Transliteration','After',
                    # 'WordClass','PartOfSpeech','Person','Gender','Number','WordType','State','SDBH',
                    # 'StrongNumberX','StrongLemma','Stem','Morphology','Lemma','SenseNumber',
                    # 'CoreDomain','LexicalDomain', # 'ContextualDomain',
                    # 'SubjRef','ParticipantRef','Frame',
                    # 'Greek','GreekStrong',
                    # 'EnglishGloss','MandarinGloss','ContextualGloss',
                    # 'Nesting']
                    entry = {'LFRef':theirRef, 'LFNumRef':longID, 'Language':lang, 'WordOrMorpheme':wordOrMorpheme,
                                'Unicode':unicodeField, 'Transliteration':elem.get('transliteration'), 'After':after,
                                'WordClass':wClass, 'Compound':compound, 'PartOfSpeech':PoS, 'Person':person, 'Gender':gender, 'Number':number,
                                'WordType':wordType, 'State':wordState, 'Role':role, 'SDBH':elem.get('SDBH'),
                                'StrongNumberX':strongNumberX,
                                'StrongLemma':lemma, # Where do these come from -- are they duplicates in the lowfat??? elem.get('stronglemma'),
                                'Stem':stem, 'Morphology':morph, 'Lemma':lemma, 'SenseNumber':senseNumber,
                                'CoreDomain':elem.get('CoreDomain'), 'LexicalDomain':elem.get('LexDomain'), 'Frame':frame,
                                'SubjRef':subjRef, 'ParticipantRef':participantRef, # 'ContextualDomain':elem.get('contextualdomain'),
                                'Greek':greekWord, 'GreekStrong':greekStrong,
                                'EnglishGloss':English, 'MandarinGloss':Mandarin, 'ContextualGloss':gloss,
                                'Nesting':'/'.join(reversed(nestingBits)) }
                    assert len(entry) == len(state.morpheme_output_fieldnames)-3, f"{len(entry)=} vs {len(state.morpheme_output_fieldnames)=}" # Three more fields to be added below
                    # for k,v in entry.items():
                    #     if v: non_blank_counts[k] += 1
                    tempWordsAndMorphemes.append( entry )
                    # dPrint( 'Normal', DEBUGGING_THIS_MODULE, f"\n  ({len(entry)}) {entry}" ) # 28
                    # if len(tempWordsAndMorphemes) > 5: halt
                    lastGloss, lastEnglish = gloss, English

            vPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"    Got {len(tempWordsAndMorphemes):,} words/morphemes in {BBB} {chapterNumber}")
            assert len(set(longIDs)) == len(longIDs), f"Should be no duplicates in {longIDs=}"

            # Note that because of the phrase/clause nesting, we can get the word fields in the wrong order
            #   so we sort them, before adjusting the formatting to what we're after
            # We sort by the Clear.Bible longID (2nd item in tuple, which already has the leading 'o' removed)
            sortedTempWordsAndMorphemes = sorted( tempWordsAndMorphemes, key=lambda t: t['LFNumRef'] )

            # Adjust to our references and with just the data that we need to retain
            # Build a ref/id dictionary as we go
            for j,firstEntryAttempt in enumerate( sortedTempWordsAndMorphemes ):
                longID = firstEntryAttempt['LFNumRef']
                
                if longID.endswith( 'ה' ):  # it's an article (vowel after preposition)
                    # print(f"Got article {longID=}")
                    assert firstEntryAttempt['WordOrMorpheme'] is None # No wordOrMorpheme
                    assert firstEntryAttempt['ContextualGloss'] is None # No gloss
                    english = firstEntryAttempt['EnglishGloss']
                    wordType = firstEntryAttempt['WordType']
                    assert wordType == 'definite article'
                    # print(f"Got article {longID=} with '{english}' {wType=}")
                    # Add the article gloss to the previous entry
                    lastExpandedEntry = state.maculaHebrewWordsAndMorphemes[-1] # We'll edit the last dict entry in place
                    lastExpandedEntry['EnglishGloss'] = f"{lastExpandedEntry['EnglishGloss']}_{english if english else 'THE'}" # Why wasn't the gloss there?
                    # else: print(f"{longID} There wasn't an English gloss!!!"); halt
                else: # a normal word or morpheme entry
                    try: nextLongID = sortedTempWordsAndMorphemes[j+1]['LFNumRef']
                    except IndexError: nextLongID = '1'
                    if nextLongID.endswith('ה'): # we have to skip this one
                        try: nextLongID = sortedTempWordsAndMorphemes[j+1+1]['LFNumRef']
                        except IndexError: nextLongID = '1'
                    assert nextLongID != longID, f"Should be no duplicate IDs: {j=} {longID=} {nextLongID=} {firstEntryAttempt}"
                    if nextLongID.endswith( '1' ): # current entry is end of a word
                        mwType = 'w' if longID.endswith( '1' ) else 'M'
                    else: # the above works but fails when the first morpheme of a word is (wrongly) missing
                        # print(f"{longID=} going to {nextLongID=} ")
                        assert len(nextLongID) == len(longID) == 12 # leading 'o' has already been removed
                        nextLongIDWordBit = nextLongID[:-1]
                        longIDWordBit = longID[:-1]
                        if nextLongIDWordBit == longIDWordBit: # we're still in the same word
                            mwType = 'm' # There's a following part of this word
                        else: # we going on to a new word, but the first part is missing
                            mwType = 'w' if longID.endswith( '1' ) else 'M'
                    suffix = '' if mwType=='w' else SUFFIX_DICT[longID[-1]]
                    if firstEntryAttempt['Language'] == 'A': mwType = f'A{mwType}' # Assume Hebrew; mark Aramaic
                    ourRef = f"{BBB}_{firstEntryAttempt['LFRef'][4:].replace( '!', 'w')}{suffix}"
                    assert longID not in refDict
                    refDict[longID] = ourRef # Create dict for next loop
                    # print(f"{longID=} {nextLongID=} {mwType=} {ourRef=}")
                    newExpandedDictEntry = {'FGRef':ourRef, 'RowType':mwType, **firstEntryAttempt}
                    assert len(newExpandedDictEntry) == len(state.morpheme_output_fieldnames)-1, f"{len(newExpandedDictEntry)=} vs {len(state.morpheme_output_fieldnames)=}" # OSHBid field to be added below
                    state.maculaHebrewWordsAndMorphemes.append( newExpandedDictEntry )
    # if 1:
    #     for n,currentEntry in enumerate(state.maculaHebrewWordsAndMorphemes):
    #         print(f"{n} ({len(currentEntry)}) {currentEntry}")
    #         if n > 10: break
    #     halt

    # Adjust frames to our references
    for lfRow in state.maculaHebrewWordsAndMorphemes:
        ourRef = lfRow['FGRef']
        frame = lfRow['Frame'] # e.g., 'A0:010010010031; A1:010010010052;010010010072;' but we want to convert it to our word numbers
        if frame:
            # print( f"{ourRef} {frame=}" )
            startIndex = 0
            while ( match := wordnumber_regex.search(frame, startIndex) ):
                try: frame = f'{frame[:match.start()]}{refDict[match.group(0)]}{frame[match.end():]}'
                except KeyError: # Seems to be no match for the ref in the frame??? Probably because it's a pointer to a word group or something???
                    logging.critical( f"Unable to match {ourRef} frame part: {match.group(0)}" )
                startIndex = match.start() + 5
            # print( f"  {frame=}" )
            lfRow['Frame'] = frame

    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  Got total of {len(state.maculaHebrewWordsAndMorphemes):,} words/morphemes")
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"      Max nesting level = {max_nesting_level}" )
    if 1:  # Just so we can turn it off and on easily
        vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"\nDetailed counts for {len(column_counts):,} fields:")
        for field_name in column_counts:
            this_set = column_counts[field_name]
            this_set_length = len(this_set)
            if this_set_length < 55:
                vPrint( 'Normal', DEBUGGING_THIS_MODULE, # Sort them with most frequent first
                    f"\n{field_name}: ({this_set_length}) {dict(sorted(this_set.items(), key=lambda x:x[1], reverse=True))}" )
            else: vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"\n{field_name} has {this_set_length:,} unique options -- display suppressed." )
    # if 1:
    #     for n,currentEntry in enumerate(state.maculaHebrewWordsAndMorphemes):
    #         assert len(currentEntry) == len(state.output_fieldnames)-1
    #         if n < 5 or 'THE' in currentEntry['EnglishGloss']: print(f"{n} ({len(currentEntry)}) {currentEntry}")
    # halt
    return True
# end of convert_ClearMaculaOT_to_our_TSV.loadMaculaHebrewNodesXMLGlosses


# def loadMaculaHebrewTSVTable() -> bool:
#     """
#     Reads in the Clear.Bible macula-hebrew TSV file
    
#     """
#     vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"\nLoading Macula OT TSV file from {state.macula_TSV_input_filepath}/…" )
    
#     global macula_tsv_column_headers
#     vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"\nLoading Macula Hebrew tsv file from {state.macula_TSV_input_filepath}…")
#     vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  Expecting {NUM_EXPECTED_MACULA_TSV_COLUMNS} columns…")
#     with open(state.macula_TSV_input_filepath, 'rt', encoding='utf-8') as tsv_file:
#         tsv_lines = tsv_file.readlines()

#     # Remove any BOM
#     if tsv_lines[0].startswith("\ufeff"):
#         vPrint( 'Quiet', DEBUGGING_THIS_MODULE, "  Handling Byte Order Marker (BOM) at start of Macula Hebrew tsv file…")
#         tsv_lines[0] = tsv_lines[0][1:]

#     # Get the headers before we start
#     macula_tsv_column_headers = [header for header in tsv_lines[0].strip().split('\t')]
#     dPrint('Info', DEBUGGING_THIS_MODULE, f"Column headers: ({len(macula_tsv_column_headers)}): {macula_tsv_column_headers}")
#     assert len(macula_tsv_column_headers) == NUM_EXPECTED_MACULA_TSV_COLUMNS

#     # Read, check the number of columns, and summarise row contents all in one go
#     dict_reader = DictReader(tsv_lines, delimiter='\t')
#     unique_morphemes, unique_words = set(), set()
#     note_count = seg_count = 0
#     assembled_word = ''
#     for n, row in enumerate(dict_reader):
#         if len(row) != NUM_EXPECTED_MACULA_TSV_COLUMNS:
#             logging.error(f"Line {n} has {len(row)} columns instead of {NUM_EXPECTED_MACULA_TSV_COLUMNS}!!!")
#         state.macula_rows.append(row)
#         for key, value in row.items():
#             # macula_tsv_column_sets[key].add(value)
#             if n==0: # We do it like this (rather than using a defaultdict(int)) so that all fields are entered into the dict in the correct order
#                 macula_tsv_column_max_length_counts[key] = 0
#                 macula_tsv_column_non_blank_counts[key] = 0
#             if value:
#                 if len(value) > macula_tsv_column_max_length_counts[key]:
#                     macula_tsv_column_max_length_counts[key] = len(value)
#                 macula_tsv_column_non_blank_counts[key] += 1
#             macula_tsv_column_counts[key][value] += 1
#     vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  Loaded {len(state.macula_rows):,} (tsv) Macula Hebrew data rows.")
#     vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"    Have {len(unique_words):,} unique Hebrew words.")
#     vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"    Have {len(unique_morphemes):,} unique Hebrew morphemes.")
#     vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"    Have {seg_count:,} Hebrew segment markers.")
#     vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"    Have {note_count:,} notes.")

#     return True
# # end of convert_ClearMaculaOT_to_our_TSV.loadMaculaHebrewTSVTable


def removeHebrewCantillationMarks( text:str, removeMetegOrSiluq=False ) -> str:
    """
    Return the text with cantillation marks removed.
    """
    #dPrint( 'Quiet', DEBUGGING_THIS_MODULE, "removeHebrewCantillationMarks( {!r}, {} )".format( text, removeMetegOrSiluq ) )
    h = Hebrew.Hebrew( text )
    return h.removeCantillationMarks( removeMetegOrSiluq=removeMetegOrSiluq )
# end of apply_Clear_Macula_OT_glosses.removeHebrewCantillationMarks


# def TSV_add_OSHB_ids() -> bool:
#     """
#     The Clear.Bible data doesn't use the 5-character OSHB id fields
#         (which we augment to 6-characters).

#     So match the entries and add them in.
#     """
#     vPrint( 'Quiet', DEBUGGING_THIS_MODULE, "\nMatching rows in both tables to add OSHB ids for TSV…" )

#     our_WLC_dict = {row['Ref']:(row['RowType'].endswith('K'),row['NoCantillations'],row['Morphology'],row['OSHBid']) for row in state.our_WLC_rows} # We include the morphology for extra checking
#     # if DEBUGGING_THIS_MODULE:
#     #     testVerseRef = 'GEN_3:5'
#     #     print( "\nOur WLC rows:" )
#     #     print( " Ref\t\tOSHBid\tRowType\tWrd/Mrph\tMorph\tMorphemeGloss\tContextualMG\tWordGloss\tContextualWG" )
#     #     for ourRow in state.our_WLC_rows:
#     #         if ourRow['Ref'].startswith( testVerseRef ):
#     #             print( f" {ourRow['Ref']}\t{ourRow['OSHBid'] if ourRow['OSHBid'] else '     '}\t {ourRow['RowType']}\t'{ourRow['WordOrMorpheme']}'\t\t{ourRow['Morphology']}\t{ourRow['MorphemeGloss'] if ourRow['MorphemeGloss'] else '~     '}\t{ourRow['ContextualMorphemeGloss'] if ourRow['ContextualMorphemeGloss'] else '~     '}\t{ourRow['WordGloss'] if ourRow['WordGloss'] else '~     '}\t{ourRow['ContextualWordGloss'] if ourRow['ContextualWordGloss'] else '~'}" )
#     #     print()

#     offset = 0
#     lastVerseID = None
#     longIDs = []
#     newRows = []
#     for rr,maculaRow in enumerate(state.macula_rows):
#         assert len(maculaRow) == NUM_EXPECTED_MACULA_TSV_COLUMNS
#         print( f"({len(maculaRow)}) {maculaRow}" )
#         nextMaculaRow = state.macula_rows[rr+1]

#         BBB = BibleOrgSysGlobals.loadedBibleBooksCodes.getBBBFromReferenceNumber( maculaRow['xml:id'][1:3] )

#         theirRef = maculaRow['ref']
#         wordOrMorpheme = removeHebrewCantillationMarks(maculaRow['text'], removeMetegOrSiluq=True)
#         morphology = maculaRow['morph']
#         print( f"{BBB} {theirRef=} {wordOrMorpheme=} {morphology=}" )

#         longID = maculaRow['xml:id'] # e.g., o010010050031 = obbcccvvvwwws
#         longIDs.append( longID )
#         assert longID.startswith( 'o' ) # Stands for OldTestament
#         longID = longID[1:] # remove 'o' prefix
#         if len(longID) > 12: # it's an article (vowel after preposition)
#             assert len(longID) == 13
#             assert longID.endswith( 'ה' )
#             assert longID[:-1].isdigit()
#         else:
#             assert len(longID) == 12
#             assert longID[:].isdigit()

#         nextLongID = nextMaculaRow['xml:id']
#         assert nextLongID.startswith( 'o' ) # Stands for OldTestament
#         nextLongID = nextLongID[1:] # remove 'o' prefix
#         if nextLongID.endswith('ה'): # we have to skip this one
#             try: nextLongID = state.macula_rows[rr+1+1]['LFNumRef']
#             except IndexError: nextLongID = '1'
#         assert nextLongID != longID, f"Should be no duplicate IDs: {j=} {longID=} {nextLongID=} {firstEntryAttempt}"
#         if nextLongID.endswith( '1' ): # current entry is end of a word
#             mwType = 'w' if longID.endswith( '1' ) else 'M'
#         else: # the above works but fails when the first morpheme of a word is (wrongly) missing
#             # print(f"{longID=} going to {nextLongID=} ")
#             assert len(nextLongID) == len(longID) == 12 # leading 'o' has already been removed
#             nextLongIDWordBit = nextLongID[:-1]
#             longIDWordBit = longID[:-1]
#             if nextLongIDWordBit == longIDWordBit: # we're still in the same word
#                 mwType = 'm' # There's a following part of this word
#             else: # we going on to a new word, but the first part is missing
#                 mwType = 'w' if longID.endswith( '1' ) else 'M'

#         suffix = '' if mwType=='w' else SUFFIX_DICT[longID[-1]]
#         if maculaRow['lang'] == 'A': mwType = f'A{mwType}' # Assume Hebrew; mark Aramaic
#         ourRef = f"{BBB}_{maculaRow['ref'][4:].replace( '!', 'w')}{suffix}"

#         gloss1 = maculaRow['gloss']
#         glossE = maculaRow['english']
#         print( f"{gloss1=} {glossE=}" )
#         if gloss1 and glossE: why_both
#         gloss = glossE if glossE else gloss1
#         if gloss:
#             gloss = gloss.replace( '.', '_' ) # Change to our system
#             assert '’' not in gloss, f"{theirRef=} {wordOrMorpheme=} {gloss=}"

#         # newExpandedDictEntry = {'FGRef':ourRef, 'RowType':mwType, **maculaRow}

#         verseID, wordPart = ourRef.split('w')
#         if wordPart.isdigit():
#             wordNumber,suffix = int( wordPart ), ''
#         else:
#             wordNumber,suffix = int( wordPart[:-1] ), wordPart[-1]
#         # if DEBUGGING_THIS_MODULE:
#         #     if ourRef.startswith( testVerseRef ):
#         #         print( f"{ourRef=}, '{wordOrMorpheme=}' {morphology=}" ) # '{rowTuple30[-1]}'

#         if verseID != lastVerseID:
#             offset = 0 # Restart at start of verse
#         adjustedRowID = f'{verseID}w{wordNumber+offset}{suffix}'
#         try:
#             foundKetivFlag, foundWordOrMorpheme, foundMorphology, foundID = our_WLC_dict[adjustedRowID]
#             assert foundWordOrMorpheme==wordOrMorpheme, f"ID's matched {adjustedRowID} from {ourRef} and got {foundID}, but not text ({len(foundWordOrMorpheme)}) '{foundWordOrMorpheme}' != ({len(wordOrMorpheme)}) '{wordOrMorpheme}'"
#             assert foundMorphology==morphology \
#                 or (foundMorphology=='Rd' and morphology=='R'), \
#                 f"ID's matched {adjustedRowID} from {ourRef} and got {foundID}, but not morphology '{foundMorphology}'!='{morphology}'"
#             # print(f"({len(secondEntryAttempt)}) {secondEntryAttempt=}")
#             newExpandedDictEntry = {'FGRef':ourRef, 'OSHBid':foundID, 'RowType':mwType}
#             # print(f"({len(newMoreExpandedDictEntry)}) {newMoreExpandedDictEntry=}")
#             # assert len(newMoreExpandedDictEntry) == len(state.output_fieldnames), f"{len(newMoreExpandedDictEntry)=} vs {len(state.output_fieldnames)=}" # OSHBid field to be added below
#             # newRows.append( newMoreExpandedDictEntry )
#         except KeyError:
#             logging.warning( f"Failed to find OSHB id for {offset=} {ourRef}: '{wordOrMorpheme}' {morphology}" )
#             assert 'w' in ourRef
#             if suffix in ('','a'):
#                 offset -= 1
#             adjustedRowID = f'{verseID}w{wordNumber+offset}{suffix}'
#             try:
#                 foundKetivFlag, foundWordOrMorpheme, foundMorphology, foundID = our_WLC_dict[adjustedRowID]
#                 dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  Got {foundID} for {offset=} {foundKetivFlag=} {adjustedRowID}")
#                 if not foundKetivFlag: # Doesn't always work on Ketivs
#                     assert foundWordOrMorpheme==wordOrMorpheme, f"ID's now matched {adjustedRowID} from {ourRef} and got {foundID}, but not text ({len(foundWordOrMorpheme)}) '{foundWordOrMorpheme}' != ({len(wordOrMorpheme)}) '{wordOrMorpheme}'"
#                     assert foundMorphology==morphology, f"ID's now matched {adjustedRowID} from {ourRef} and got {foundID}, but not morphology '{foundMorphology}'!='{morphology}'"
#                 newExpandedDictEntry = {'FGRef':ourRef, 'OSHBid':foundID, 'RowType':mwType}
#                 # assert len(newMoreExpandedDictEntry) == len(state.output_fieldnames), f"{len(newMoreExpandedDictEntry)=} vs {len(state.output_fieldnames)=}" # OSHBid field to be added below
#                 # newRows.append( newMoreExpandedDictEntry )
#             except (KeyError, AssertionError):
#                 logging.error( f"Failed to find OSHB id for {offset=} {adjustedRowID} from {ourRef}: '{maculaRow['WordOrMorpheme']}'")
#                 newExpandedDictEntry = {'FGRef':ourRef, 'OSHBid':'', 'RowType':mwType}
#                 # assert len(newMoreExpandedDictEntry) == len(state.output_fieldnames), f"{len(newMoreExpandedDictEntry)=} vs {len(state.output_fieldnames)=}" # OSHBid field to be added below
#                 # newRows.append( newMoreExpandedDictEntry )
#                 if DEBUGGING_THIS_MODULE:
#                     print( f"{rr} {state.macula_rows[rr]}" )
#                     print( f"{rr+1} {state.macula_rows[rr+1]}" )
#                     print( f"{rr+2} {state.macula_rows[rr+2]}" )
#                     print( f"{rr+3} {state.macula_rows[rr+3]}" )
#                     haltA
#         except AssertionError:
#             logging.warning( f"Failed to match text or morphology for {offset=} {ourRef}: '{foundWordOrMorpheme}' vs '{wordOrMorpheme}' {foundMorphology} vs {morphology}")
#             assert 'w' in ourRef
#             if suffix in ('','a'):
#                 offset -= 1
#             adjustedRowID = f'{verseID}w{wordNumber+offset}{suffix}'
#             try:
#                 foundKetivFlag, foundWordOrMorpheme, foundMorphology, foundID = our_WLC_dict[adjustedRowID]
#                 dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  Got {foundID} for {offset=} {foundKetivFlag=} {adjustedRowID}")
#                 if not foundKetivFlag: # Doesn't always work on Ketivs
#                     assert foundWordOrMorpheme==wordOrMorpheme, f"ID's now matched {adjustedRowID} from {ourRef} and got {foundID}, but not text ({len(foundWordOrMorpheme)}) '{foundWordOrMorpheme}' != ({len(wordOrMorpheme)}) '{wordOrMorpheme}'"
#                     assert foundMorphology==morphology, f"ID's now matched {adjustedRowID} from {ourRef} and got {foundID}, but not morphology '{foundMorphology}'!='{morphology}'"
#                 newExpandedDictEntry = {'FGRef':ourRef, 'OSHBid':foundID, 'RowType':mwType}
#                 # assert len(newMoreExpandedDictEntry) == len(state.output_fieldnames), f"{len(newMoreExpandedDictEntry)=} vs {len(state.output_fieldnames)=}" # OSHBid field to be added below
#                 # newRows.append( newMoreExpandedDictEntry )
#             except (KeyError, AssertionError):
#                 logging.error( f"Failed to find OSHB id for {offset=} {adjustedRowID} from {ourRef}: '{maculaRow['WordOrMorpheme']}'")
#                 newExpandedDictEntry = {'FGRef':ourRef, 'OSHBid':'', 'RowType':mwType}
#                 # assert len(newMoreExpandedDictEntry) == len(state.output_fieldnames), f"{len(newMoreExpandedDictEntry)=} vs {len(state.output_fieldnames)=}" # OSHBid field to be added below
#                 # newRows.append( newMoreExpandedDictEntry )
#                 if DEBUGGING_THIS_MODULE:
#                     haltB

#         # Fill out the rest of the entry
#         entryRemainder = {'LFRef':theirRef, 'LFNumRef':longID, 'Language':maculaRow['lang'], 'WordOrMorpheme':wordOrMorpheme,
#                         'Transliteration':maculaRow['transliteration'], 'After':maculaRow['after'],
#                         'WordClass':maculaRow['class'], 'PartOfSpeech':maculaRow['pos'], 'Person':maculaRow['person'], 'Gender':maculaRow['gender'], 'Number':maculaRow['number'],
#                         # 'WordType':maculaRow['wType'], 'State':maculaRow['wState'], 'Role':maculaRow['role'],
#                         'SDBH':maculaRow['sdbh'],
#                         'StrongNumberX':maculaRow['strongnumberx'], 'StrongLemma':maculaRow['stronglemma'],
#                         'Stem':maculaRow['stem'], 'Morphology':maculaRow['morph'], 'Lemma':maculaRow['lemma'], 'SenseNumber':maculaRow['senseNumber'],
#                         'CoreDomain':maculaRow['coredomain'], 'LexicalDomain':maculaRow['lexdomain'], 'Frame':maculaRow['frame'],
#                         'SubjRef':maculaRow['subjref'], 'ParticipantRef':maculaRow['participantref'], # 'ContextualDomain':elem.get('contextualdomain'),
#                         'Greek':maculaRow['greek'], 'GreekStrong':maculaRow['greekstrong'],
#                         'EnglishGloss':maculaRow['english'], 'MandarinGloss':maculaRow['mandarin'], 'ContextualGloss':gloss,
#                         # 'Nesting':'/'.join(reversed(nestingBits))
#                         }
#         newExpandedDictEntry += entryRemainder

#         # Check we haven't ended up with anything missing or any extra stuff
#         for fieldname in newExpandedDictEntry: assert fieldname in state.output_fieldnames
#         for fieldname in state.output_fieldnames: assert fieldname in newExpandedDictEntry
#         assert len(maculaRow) == len(state.output_fieldnames)-1, f"{len(maculaRow)=} ({len(state.output_fieldnames)}) {state.output_fieldnames}"
#         newRows.append( newExpandedDictEntry )
#         lastVerseID = verseID

#     assert len(newRows) == len(state.lowFatWordsAndMorphemes)
#     assert len(set(longIDs)) == len(longIDs), f"Should be no duplicates in {longIDs=}"
#     state.output_rows = newRows

#     return True
# # end of convert_ClearMaculaOT_to_our_TSV.TSV_add_OSHB_ids


def MacHeb_add_OSHB_ids() -> bool:
    """
    The Clear.Bible data doesn't use the 5-character OSHB id fields
        (which we augment to 6-characters).

    So match the entries and add them in.
    """
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, "\nMatching rows in both tables to add OSHB ids for LF…" )

    our_WLC_dict = {row['Ref']:(row['RowType'].endswith('K'),row['NoCantillations'],row['Morphology'],row['OSHBid']) for row in state.our_WLC_rows} # We include the morphology for extra checking
    if DEBUGGING_THIS_MODULE:
        testVerseRef = 'GEN_26:33'
        print( "\nOur WLC rows:" )
        print( " Ref\t\tOSHBid\tRowType\tWrd/Mrph\tMorph\tMorphemeGloss\tContextualMG\tWordGloss\tContextualWG" )
        for row in state.our_WLC_rows:
            if row['Ref'].startswith( testVerseRef ):
                print( f" {row['Ref']}\t{row['OSHBid'] if row['OSHBid'] else '     '}\t {row['RowType']}\t'{row['WordOrMorpheme']}'\t\t{row['Morphology']}\t{row['MorphemeGloss'] if row['MorphemeGloss'] else '~     '}\t{row['ContextualMorphemeGloss'] if row['ContextualMorphemeGloss'] else '~     '}\t{row['WordGloss'] if row['WordGloss'] else '~     '}\t{row['ContextualWordGloss'] if row['ContextualWordGloss'] else '~'}" )
        print()

    offset = 0
    lastVerseID = None
    newLowFatWordsAndMorphemes = []
    for _n,secondEntryAttempt in enumerate(state.maculaHebrewWordsAndMorphemes):
        assert len(secondEntryAttempt) == len(state.morpheme_output_fieldnames)-1
        ourID, wordOrMorpheme, morphology = secondEntryAttempt['FGRef'], removeHebrewCantillationMarks(secondEntryAttempt['WordOrMorpheme'], removeMetegOrSiluq=True), secondEntryAttempt['Morphology']
        verseID, wordPart = ourID.split('w')
        if wordPart.isdigit():
            wordNumber,suffix = int( wordPart ), ''
        else:
            wordNumber,suffix = int( wordPart[:-1] ), wordPart[-1]
        if DEBUGGING_THIS_MODULE:
            if ourID.startswith( testVerseRef ):
                print( f"{ourID=}, '{wordOrMorpheme=}' {morphology=}" ) # '{rowTuple30[-1]}'

        if verseID != lastVerseID:
            offset = 0 # Restart at start of verse
        adjustedRowID = f'{verseID}w{wordNumber+offset}{suffix}'
        try:
            foundKetivFlag, foundWordOrMorpheme, foundMorphology, foundID = our_WLC_dict[adjustedRowID]
            assert foundWordOrMorpheme==wordOrMorpheme, f"ID's matched {adjustedRowID} from {ourID} and got {foundID}, but not text ({len(foundWordOrMorpheme)}) '{foundWordOrMorpheme}' != ({len(wordOrMorpheme)}) '{wordOrMorpheme}'"
            assert foundMorphology==morphology \
                or (foundMorphology=='Rd' and morphology=='R'), \
                f"ID's matched {adjustedRowID} from {ourID} and got {foundID}, but not morphology '{foundMorphology}'!='{morphology}'"
            # print(f"({len(secondEntryAttempt)}) {secondEntryAttempt=}")
            newMoreExpandedDictEntry = {'FGRef':ourID, 'OSHBid':foundID, **secondEntryAttempt}
            # print(f"({len(newMoreExpandedDictEntry)}) {newMoreExpandedDictEntry=}")
            assert len(newMoreExpandedDictEntry) == len(state.morpheme_output_fieldnames), f"{len(newMoreExpandedDictEntry)=} vs {len(state.morpheme_output_fieldnames)=}" # OSHBid field to be added below
            newLowFatWordsAndMorphemes.append( newMoreExpandedDictEntry )
        except KeyError:
            logging.warning( f"Failed to find OSHB id for {offset=} {ourID}: '{wordOrMorpheme}' {morphology}" )
            assert 'w' in ourID
            if suffix in ('','a'):
                offset -= 1
            adjustedRowID = f'{verseID}w{wordNumber+offset}{suffix}'
            try:
                foundKetivFlag, foundWordOrMorpheme, foundMorphology, foundID = our_WLC_dict[adjustedRowID]
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  Got {foundID} for {offset=} {foundKetivFlag=} {adjustedRowID}")
                if not foundKetivFlag: # Doesn't always work on Ketivs
                    assert foundWordOrMorpheme==wordOrMorpheme, f"ID's now matched {adjustedRowID} from {ourID} and got {foundID}, but not text ({len(foundWordOrMorpheme)}) '{foundWordOrMorpheme}' != ({len(wordOrMorpheme)}) '{wordOrMorpheme}'"
                    assert foundMorphology==morphology, f"ID's now matched {adjustedRowID} from {ourID} and got {foundID}, but not morphology '{foundMorphology}'!='{morphology}'"
                newMoreExpandedDictEntry = {'FGRef':ourID, 'OSHBid':foundID, **secondEntryAttempt}
                assert len(newMoreExpandedDictEntry) == len(state.morpheme_output_fieldnames), f"{len(newMoreExpandedDictEntry)=} vs {len(state.morpheme_output_fieldnames)=}" # OSHBid field to be added below
                newLowFatWordsAndMorphemes.append( newMoreExpandedDictEntry )
            except (KeyError, AssertionError):
                logging.error( f"Failed to find OSHB id for {offset=} {adjustedRowID} from {ourID}: '{secondEntryAttempt['WordOrMorpheme']}'")
                newMoreExpandedDictEntry = {'FGRef':ourID, 'OSHBid':'', **secondEntryAttempt}
                assert len(newMoreExpandedDictEntry) == len(state.morpheme_output_fieldnames), f"{len(newMoreExpandedDictEntry)=} vs {len(state.morpheme_output_fieldnames)=}" # OSHBid field to be added below
                newLowFatWordsAndMorphemes.append( newMoreExpandedDictEntry )
                if DEBUGGING_THIS_MODULE:
                    print( f"{_n} {state.maculaHebrewWordsAndMorphemes[_n]}" )
                    print( f"{_n+1} {state.maculaHebrewWordsAndMorphemes[_n+1]}" )
                    print( f"{_n+2} {state.maculaHebrewWordsAndMorphemes[_n+2]}" )
                    print( f"{_n+3} {state.maculaHebrewWordsAndMorphemes[_n+3]}" )
                    haltA
        except AssertionError:
            logging.warning( f"Failed to match text or morphology for {offset=} {ourID}: '{foundWordOrMorpheme}' vs '{wordOrMorpheme}' {foundMorphology} vs {morphology}")
            assert 'w' in ourID
            if suffix in ('','a'):
                offset -= 1
            adjustedRowID = f'{verseID}w{wordNumber+offset}{suffix}'
            try:
                foundKetivFlag, foundWordOrMorpheme, foundMorphology, foundID = our_WLC_dict[adjustedRowID]
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  Got {foundID} for {offset=} {foundKetivFlag=} {adjustedRowID}")
                if not foundKetivFlag: # Doesn't always work on Ketivs
                    assert foundWordOrMorpheme==wordOrMorpheme, f"ID's now matched {adjustedRowID} from {ourID} and got {foundID}, but not text ({len(foundWordOrMorpheme)}) '{foundWordOrMorpheme}' != ({len(wordOrMorpheme)}) '{wordOrMorpheme}'"
                    assert foundMorphology==morphology, f"ID's now matched {adjustedRowID} from {ourID} and got {foundID}, but not morphology '{foundMorphology}'!='{morphology}'"
                newMoreExpandedDictEntry = {'FGRef':ourID, 'OSHBid':foundID, **secondEntryAttempt}
                assert len(newMoreExpandedDictEntry) == len(state.morpheme_output_fieldnames), f"{len(newMoreExpandedDictEntry)=} vs {len(state.morpheme_output_fieldnames)=}" # OSHBid field to be added below
                newLowFatWordsAndMorphemes.append( newMoreExpandedDictEntry )
            except (KeyError, AssertionError):
                logging.error( f"Failed to find OSHB id for {offset=} {adjustedRowID} from {ourID}: '{secondEntryAttempt['WordOrMorpheme']}'")
                newMoreExpandedDictEntry = {'FGRef':ourID, 'OSHBid':'', **secondEntryAttempt}
                assert len(newMoreExpandedDictEntry) == len(state.morpheme_output_fieldnames), f"{len(newMoreExpandedDictEntry)=} vs {len(state.morpheme_output_fieldnames)=}" # OSHBid field to be added below
                newLowFatWordsAndMorphemes.append( newMoreExpandedDictEntry )
                if DEBUGGING_THIS_MODULE:
                    haltB
        # Check we haven't ended up with anything missing or any extra stuff
        for fieldname in newLowFatWordsAndMorphemes[-1]: assert fieldname in state.morpheme_output_fieldnames
        for fieldname in state.morpheme_output_fieldnames: assert fieldname in newLowFatWordsAndMorphemes[-1]
        lastVerseID = verseID

    assert len(newLowFatWordsAndMorphemes) == len(state.maculaHebrewWordsAndMorphemes)
    state.maculaHebrewWordsAndMorphemes = newLowFatWordsAndMorphemes

    return True
# end of convert_ClearMaculaOT_to_our_TSV.MacHeb_add_OSHB_ids


def save_filled_morpheme_TSV_file() -> bool:
    """
    Save table as a single TSV file (about 94 MB).
    """
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"\nExporting filled OT Low Fat table as a single flat TSV file to {state.morpheme_TSV_output_filepath}…" )

    BibleOrgSysGlobals.backupAnyExistingFile( state.morpheme_TSV_output_filepath, numBackups=5 )

    # print(len(state.lowFatWordsAndMorphemes[0]), state.lowFatWordsAndMorphemes[0]);halt
    with open( state.morpheme_TSV_output_filepath, 'wt', encoding='utf-8' ) as tsv_output_file:
        tsv_output_file.write('\ufeff') # Write BOM
        writer = DictWriter( tsv_output_file, fieldnames=state.morpheme_output_fieldnames, delimiter='\t' )
        writer.writeheader()
        for thisTuple in state.maculaHebrewWordsAndMorphemes:
            thisRow = {k:thisTuple[k] for k in state.morpheme_output_fieldnames}
            # print( f"{state.output_fieldnames=} {thisTuple=} {thisRow=}" )
            writer.writerow( thisRow )
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  {len(state.maculaHebrewWordsAndMorphemes):,} data rows written ({len(state.morpheme_output_fieldnames)} fields) to {state.morpheme_TSV_output_filepath}." )

    if 1: # Collect and print stats
        non_blank_counts, blank_counts = defaultdict(int), defaultdict(int)
        sets = defaultdict(set)
        for entry in state.maculaHebrewWordsAndMorphemes:
            for fieldname,value in entry.items():
                if value: non_blank_counts[fieldname] += 1
                else: blank_counts[fieldname] += 1
                sets[fieldname].add( value )
        for fieldname,count in blank_counts.items():
            assert count < len(state.maculaHebrewWordsAndMorphemes), f"save_filled_morpheme_TSV_file: '{fieldname}' field is never filled"
        vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"\nCounts of non-blank fields for {len(state.maculaHebrewWordsAndMorphemes):,} rows:" )
        for fieldname,count in non_blank_counts.items():
            non_blank_count_str = 'all' if count==len(state.maculaHebrewWordsAndMorphemes) else f'{count:,}'
            unique_count_str = 'all' if len(sets[fieldname])==len(state.maculaHebrewWordsAndMorphemes) else f'{len(sets[fieldname]):,}'
            vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  {fieldname}: {non_blank_count_str} non-blank entries (with {unique_count_str} unique entries)" )
            assert count # Otherwise we're including a field that contains nothing!
            if len(sets[fieldname]) < 50:
                vPrint( 'Info', DEBUGGING_THIS_MODULE, f"    being: {sets[fieldname]}" )

    return True
# end of convert_ClearMaculaOT_to_our_TSV.save_filled_morpheme_TSV_file


def save_shortened_morpheme_TSV_file() -> bool:
    """
    Save table as a single TSV file
        but with a number of fields deleted or abbreviated to make it smaller.

    Of course, this makes the table less self-documenting!
    """
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"\nExporting shortened OT Low Fat table as a single flat TSV file to {state.morpheme_TSV_output_filepath}…" )

    BibleOrgSysGlobals.backupAnyExistingFile( state.morpheme_shortened_TSV_output_filepath, numBackups=5 )

    shortenedFieldnameList = [fieldname for fieldname in state.morpheme_output_fieldnames if fieldname not in MORPHEME_COLUMNS_TO_REMOVE_FOR_SHORTENING]
    # FGRef	OSHBid	RowType	WordOrMorpheme	After	Compound	WordClass	PartOfSpeech	Person	Gender	Number	WordType	State	Role	StrongNumberX	StrongLemma	Stem	Morphology	Lemma	SenseNumber	SubjRef	ParticipantRef	Frame	Greek	GreekStrong	EnglishGloss	ContextualGloss	Nesting
    # print(f"({len(state.output_fieldnames)}) {state.output_fieldnames} -> ({len(shortenedFieldnames)}) {shortenedFieldnames}")

    # print(len(state.lowFatWordsAndMorphemes[0]), state.lowFatWordsAndMorphemes[0]);halt
    non_blank_counts = defaultdict(int)
    sets = defaultdict(set)
    with open( state.morpheme_shortened_TSV_output_filepath, 'wt', encoding='utf-8' ) as tsv_output_file:
        tsv_output_file.write('\ufeff') # Write BOM
        writer = DictWriter( tsv_output_file, fieldnames=shortenedFieldnameList, delimiter='\t' )
        writer.writeheader()
        for thisEntryDict in state.maculaHebrewWordsAndMorphemes:
            for columnName in MORPHEME_COLUMNS_TO_REMOVE_FOR_SHORTENING:
                del thisEntryDict[columnName]
            # Abbreviate wordy fields -- they can always be reconstituted later
            # Try to use the same abbreviations as already used in other fields
            try: thisEntryDict['WordType'] = {'common':'com', 'pronominal':'pron', 'proper':'PN', 'definite article':'def',
                            'direct object marker':'DOM', 'adjective':'adj', 'negative':'neg', 'imperative':'imp',
                            'cardinal number':'cardinal', 'ordinal number':'ordinal', 'interjection':'ij',
                            'unknown: x':'?' }[thisEntryDict['WordType']]
            except KeyError: pass # The above set is not complete -- there's several others (plus None) that we leave unchanged
            try: thisEntryDict['WordClass'] = {'noun':'n','verb':'v','prep':'pp', 'particle':'part'}[thisEntryDict['WordClass']]
            except KeyError: pass # The above set is not complete -- there's several others that we leave unchanged
            thisEntryDict['PartOfSpeech'] = {'noun':'n','verb':'v','preposition':'pp', 'particle':'part', 'conjunction':'cj',
                            'suffix':'suffix', 'adjective':'adj','pronoun':'pron','adverb':'adv'}[thisEntryDict['PartOfSpeech']]
            if thisEntryDict['Person']: # Abbreviate
                thisEntryDict['Person'] = {'first':'1','second':'2','third':'3', 'unknown: x':'?'}[thisEntryDict['Person']]
            if thisEntryDict['Gender']: # Abbreviate
                thisEntryDict['Gender'] = {'masculine':'m','feminine':'f','common':'c', 'both':'b', 'unknown: x':'?'}[thisEntryDict['Gender']]
            if thisEntryDict['Number']: # Abbreviate
                thisEntryDict['Number'] = {'singular':'s','plural':'p','dual':'d', 'unknown: x':'?'}[thisEntryDict['Number']]
            if thisEntryDict['State']: # Abbreviate
                thisEntryDict['State'] = {'absolute':'a','construct':'c','determined':'d'}[thisEntryDict['State']]
            assert len(thisEntryDict) == len(state.morpheme_output_fieldnames) - len(MORPHEME_COLUMNS_TO_REMOVE_FOR_SHORTENING)
            writer.writerow( thisEntryDict )
            for fieldname,value in thisEntryDict.items():
                if value: non_blank_counts[fieldname] += 1
                sets[fieldname].add( value )
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  {len(state.maculaHebrewWordsAndMorphemes):,} shortened ({len(state.morpheme_output_fieldnames)} - {len(MORPHEME_COLUMNS_TO_REMOVE_FOR_SHORTENING)} = {len(thisEntryDict)} fields) data rows written to {state.morpheme_shortened_TSV_output_filepath}." )

    if 1: # Print stats
        vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"\nCounts of non-blank fields for {len(state.maculaHebrewWordsAndMorphemes):,} rows:" )
        for fieldname,count in non_blank_counts.items():
            non_blank_count_str = 'all' if count==len(state.maculaHebrewWordsAndMorphemes) else f'{count:,}'
            unique_count_str = 'all' if len(sets[fieldname])==len(state.maculaHebrewWordsAndMorphemes) else f'{len(sets[fieldname]):,}'
            vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  {fieldname}: {non_blank_count_str} non-blank entries (with {unique_count_str} unique entries)" )
            assert count # Otherwise we're including a field that contains nothing!
            if len(sets[fieldname]) < 50:
                vPrint( 'Info', DEBUGGING_THIS_MODULE, f"    being: {sets[fieldname]}" )

    return True
# end of convert_ClearMaculaOT_to_our_TSV.save_shortened_morpheme_TSV_file


def save_lemma_TSV_file() -> bool:
    """
    Create the lemma table from the Macula Hebrew morpheme table.

    Save table as a single TSV file

    TODO: Why is the same code in apply_Clear_Macula_OT_glosses.py???
    """
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"\nCreating and exporting OT lemma table from Macula Hebrew as a single flat TSV file to {state.lemma_TSV_output_filepath}…" )


    # Firstly, let's create the lemma table
    state.lemma_formation_dict = defaultdict(set)
    num_missing_lemmas = 0
    morphemes_with_missing_lemmas = set()
    for thisTuple in state.maculaHebrewWordsAndMorphemes:
        thisRow = {k:thisTuple[k] for k in state.morpheme_output_fieldnames}
        # print( f"{thisRow=}" )
        fgRef, wordOrMorpheme, lemma, gloss = thisRow['FGRef'], thisRow['WordOrMorpheme'], thisRow['Lemma'], thisRow['EnglishGloss']
        # assert ',' not in gloss, thisRow # Check our separator's not in the data -- fails on "1,000"
        assert gloss is not None and ';' not in gloss, f"{thisRow=}"
        if lemma:
            if gloss:
                state.lemma_formation_dict[lemma].add( gloss )
        else: # no lemma
            if fgRef.startswith( 'GEN_1:'):
                print( f"Why do we have no lemma for {fgRef} {wordOrMorpheme=}?" )
            morphemes_with_missing_lemmas.add( wordOrMorpheme )
            num_missing_lemmas += 1
    print( f"{num_missing_lemmas:,} morphemes with no lemmas => {len(morphemes_with_missing_lemmas):,} unique morphemes_with_missing_lemmas={sorted(morphemes_with_missing_lemmas)}")
    print( f"Extracted {len(state.lemma_formation_dict):,} Hebrew lemmas from {len(state.maculaHebrewWordsAndMorphemes):,} morphemes" )
    # print( f"{state.lemma_formation_dict=}" )
    
    # Preprocess it in the sorted order
    new_dict = {}
    # state.lemma_index_dict = {}
    for n, hebrew_lemma in enumerate( sorted( state.lemma_formation_dict ), start=1 ):
        new_dict[hebrew_lemma] = ';'.join( sorted( state.lemma_formation_dict[hebrew_lemma], key=str.casefold ) )
        # state.lemma_index_dict[hebrew_lemma] = n
    state.lemma_formation_dict = new_dict
    # print( f"{state.lemma_formation_dict=}" )
    # print( f"{state.lemma_index_dict=}" )


    BibleOrgSysGlobals.backupAnyExistingFile( state.lemma_TSV_output_filepath, numBackups=5 )

    non_blank_counts = defaultdict(int)
    sets = defaultdict(set)
    with open( state.lemma_TSV_output_filepath, 'wt', encoding='utf-8' ) as tsv_output_file:
        tsv_output_file.write('\ufeff') # Write BOM
        writer = DictWriter( tsv_output_file, fieldnames=state.lemma_output_fieldnames, delimiter='\t' )
        writer.writeheader()
        for lemma,glosses in state.lemma_formation_dict.items():
            thisEntryDict = {}
            thisEntryDict['Lemma'] = lemma
            thisEntryDict['Glosses'] = glosses
            assert len(thisEntryDict) == len(state.lemma_output_fieldnames)
            writer.writerow( thisEntryDict )
            for fieldname,value in thisEntryDict.items():
                if value: non_blank_counts[fieldname] += 1
                sets[fieldname].add( value )
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  {len(state.lemma_formation_dict):,} lemma ({len(state.lemma_output_fieldnames)} fields) data rows written to {state.lemma_TSV_output_filepath}." )

    # if 1: # Print stats
    #     vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"\nCounts of non-blank fields for {len(state.lemma_formation_dict):,} rows:" )
    #     for fieldname,count in non_blank_counts.items():
    #         non_blank_count_str = 'all' if count==len(state.lemma_formation_dict) else f'{count:,}'
    #         unique_count_str = 'all' if len(sets[fieldname])==len(state.lemma_formation_dict) else f'{len(sets[fieldname]):,}'
    #         vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  {fieldname}: {non_blank_count_str} non-blank entries (with {unique_count_str} unique entries)" )
    #         assert count # Otherwise we're including a field that contains nothing!
    #         if len(sets[fieldname]) < 50:
    #             vPrint( 'Info', DEBUGGING_THIS_MODULE, f"    being: {sets[fieldname]}" )

    return True
# end of convert_ClearMaculaOT_to_our_TSV.save_lemma_TSV_file


if __name__ == '__main__':
    # from multiprocessing import freeze_support
    # freeze_support() # Multiprocessing support for frozen Windows executables

    # Configure basic Bible Organisational System (BOS) set-up
    parser = BibleOrgSysGlobals.setup( SHORT_PROGRAM_NAME, PROGRAM_VERSION, LAST_MODIFIED_DATE )
    BibleOrgSysGlobals.addStandardOptionsAndProcess( parser )

    main()

    BibleOrgSysGlobals.closedown( PROGRAM_NAME, PROGRAM_VERSION )
# end of convert_ClearMaculaOT_to_our_TSV.py
