#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# convert_ClearMaculaNT_to_TSV.py
#
# Script handling convert_ClearMaculaNT_to_TSV functions
#
# Copyright (C) 2022-2024 Robert Hunt
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
Script taking Clear.Bible low-fat NT trees and extracting and flattening the data
    into a single, large TSV file.

We also add the ID fields that were originally adapted from the BibleTags id fields.

CHANGELOG:
    2023-03-22 Shortened referent field in our output tables
               Changed some fieldnames: Referent -> Referents, Frame -> Frames better reflecting the actual data contents
    2023-04-27 Combined subject referents into Referents column (so now, one less column)
"""
from gettext import gettext as _
from typing import Dict, List, Tuple
from pathlib import Path
from csv import DictReader, DictWriter
from collections import defaultdict
import logging
from xml.etree import ElementTree

if __name__ == '__main__':
    import sys
    sys.path.insert( 0, '../../BibleOrgSys/' )
from BibleOrgSys import BibleOrgSysGlobals
from BibleOrgSys.BibleOrgSysGlobals import vPrint, fnPrint, dPrint


LAST_MODIFIED_DATE = '2024-03-19' # by RJH
SHORT_PROGRAM_NAME = "Convert_ClearMaculaNT_to_TSV"
PROGRAM_NAME = "Extract and Apply Macula OT glosses"
PROGRAM_VERSION = '0.23'
PROGRAM_NAME_VERSION = f'{SHORT_PROGRAM_NAME} v{PROGRAM_VERSION}'

DEBUGGING_THIS_MODULE = False


# LOWFAT_XML_INPUT_FOLDERPATH = Path( '../../Forked/macula-greek/Nestle1904/lowfat/' )
LOWFAT_XML_INPUT_FOLDERPATH = Path( '../../Forked/macula-greek/SBLGNT/lowfat/' )
LOWFAT_XML_FILENAME_TEMPLATE = 'NN-wwww.xml' # e.g., 01-matthew.xml, 25-3john.xml
EXPECTED_WORD_ATTRIBUTES = ('{http://www.w3.org/XML/1998/namespace}id', 'ref', 'role',
        'gloss', # 'mandarin', 'english',
        'class','morph','person','gender','number','tense','voice','mood','degree','type',#'state', # 'pos',
        'unicode','after', # 'transliteration',
        # 'strongnumberx', 'stronglemma','greek','greekstrong',
        'lemma',#'stem','subjref','participantref', # 'lang',
        'domain','frame','referent','subjref','discontinuous', # 'sdbh','lexdomain','sensenumber','coredomain','contextualdomain',
        'case','normalized','head','strong','ln',
        'note', # Added 27Apr2023
        'junction', # Added 19Mar2024
        'english','mandarin' # For SBLGNT only
        )
assert len(set(EXPECTED_WORD_ATTRIBUTES)) == len(EXPECTED_WORD_ATTRIBUTES), "No duplicate attribute names"
BIBLE_TAGS_TSV_INPUT_FILEPATH = Path( '../sourceTexts/BibleTagsOriginals/BibTags.NT.words.tsv' )
TSV_OUTPUT_FILEPATH = Path( '../intermediateTexts/Clear.Bible_lowfat_trees/ClearLowFatTrees.NT.words.tsv' )
SHORTENED_TSV_OUTPUT_FILEPATH = Path( '../intermediateTexts/Clear.Bible_lowfat_trees/ClearLowFatTreesAbbrev.NT.words.tsv' )
OUTPUT_FIELDNAMES = ['FGRef','BibTagId','LFRef','LFNumRef','Role',
                    'Word','Unicode','After',
                    'WordClass','Person','Gender','Number','Tense','Voice','Mood','Degree',
                    'WordType','Domain','Frames','Referents','Discontinuous',
                    'Morphology','Lemma','Junction',
                    'Strong',
                    'ContextualGloss',
                    'Nesting']
assert len(set(OUTPUT_FIELDNAMES)) == len(OUTPUT_FIELDNAMES), "No duplicate fieldnames"
assert len(OUTPUT_FIELDNAMES) == 27, len(OUTPUT_FIELDNAMES)


state = None
class State:
    def __init__( self ) -> None:
        """
        Constructor:
        """
        self.lowfat_XML_input_folderpath = LOWFAT_XML_INPUT_FOLDERPATH
        self.BibTags_TSV_input_filepath = BIBLE_TAGS_TSV_INPUT_FILEPATH
        self.TSV_output_filepath = TSV_OUTPUT_FILEPATH
        self.shortened_TSV_output_filepath = SHORTENED_TSV_OUTPUT_FILEPATH
        self.BibTags_rows = []
        self.lowFatWordsAndMorphemes = []
        self.output_fieldnames = OUTPUT_FIELDNAMES
    # end of convert_ClearMaculaNT_to_TSV.State.__init__()


NUM_EXPECTED_BIBLE_TAGS_COLUMNS = 7 # We expect ['Ref', 'BibTagId', 'Word', 'Lemma', 'Strong', 'Morphology', 'After']
BibTags_tsv_column_max_length_counts = {}
BibTags_tsv_column_non_blank_counts = {}
BibTags_tsv_column_counts = defaultdict(lambda: defaultdict(int))
BibTags_tsv_column_headers = []


def main() -> None:
    """
    """
    BibleOrgSysGlobals.introduceProgram( __name__, PROGRAM_NAME_VERSION, LAST_MODIFIED_DATE )
    global state
    state = State()

    if loadBibleTagsNTSourceTable():
        if loadClearLowFatGlossesXML():
            if add_BibleTags_ids():
                save_filled_TSV_file()
                save_shortened_TSV_file()
# end of convert_ClearMaculaNT_to_TSV.main


def loadBibleTagsNTSourceTable() -> bool:
    """
    """
    global BibTags_tsv_column_headers
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"\nLoading BibleTags NT tsv file from {state.BibTags_TSV_input_filepath}…")
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  Expecting {NUM_EXPECTED_BIBLE_TAGS_COLUMNS} columns…")
    with open(state.BibTags_TSV_input_filepath, 'rt', encoding='utf-8') as tsv_file:
        tsv_lines = tsv_file.readlines()

    # Remove any BOM
    if tsv_lines[0].startswith("\ufeff"):
        vPrint( 'Quiet', DEBUGGING_THIS_MODULE, "  Handling Byte Order Marker (BOM) at start of our NT tsv file…")
        tsv_lines[0] = tsv_lines[0][1:]

    # Get the headers before we start
    BibTags_tsv_column_headers = [header for header in tsv_lines[0].strip().split('\t')]
    dPrint('Info', DEBUGGING_THIS_MODULE, f"Column headers: ({len(BibTags_tsv_column_headers)}): {BibTags_tsv_column_headers}")
    assert len(BibTags_tsv_column_headers) == NUM_EXPECTED_BIBLE_TAGS_COLUMNS

    # Read, check the number of columns, and summarise row contents all in one go
    dict_reader = DictReader(tsv_lines, delimiter='\t')
    unique_words = set()
    for n, row in enumerate(dict_reader):
        # We expect ['Ref', 'BibTagId', 'Word', 'Lemma', 'Strong', 'Morphology', 'After']
        if len(row) != NUM_EXPECTED_BIBLE_TAGS_COLUMNS:
            logging.error(f"Line {n} has {len(row)} columns instead of {NUM_EXPECTED_BIBLE_TAGS_COLUMNS}!!!")
        state.BibTags_rows.append(row)
        unique_words.add(row['Word'])
        for key, value in row.items():
            # BibTags_tsv_column_sets[key].add(value)
            if n==0: # We do it like this (rather than using a defaultdict(int)) so that all fields are entered into the dict in the correct order
                BibTags_tsv_column_max_length_counts[key] = 0
                BibTags_tsv_column_non_blank_counts[key] = 0
            if value:
                if len(value) > BibTags_tsv_column_max_length_counts[key]:
                    BibTags_tsv_column_max_length_counts[key] = len(value)
                BibTags_tsv_column_non_blank_counts[key] += 1
            BibTags_tsv_column_counts[key][value] += 1
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  Loaded {len(state.BibTags_rows):,} (tsv) BibTags data rows.")
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"    Have {len(unique_words):,} unique Greek words.")

    return True
# end of convert_ClearMaculaNT_to_TSV.loadBibleTagsNTSourceTable


def loadClearLowFatGlossesXML() -> bool:
    """
    Extract glosses out of fields 
    Reorganise columns and add our extra columns
    """
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"\nLoading Clear.Bible 'low fat' NT glosses from {state.lowfat_XML_input_folderpath}/…" )
    
    # namespaces = { 'osis': 'http://www.bibletechnologies.net/2003/OSIS/namespace' }
    # namespaces = { 'xml': 'http://www.w3.org/XML/1998/namespace' }
    suffixDict = {'1':'a', '2':'b', '3':'c', '4':'d', '5':'e', '6':'f', '7':'g'} # Max of 7 morphemes in one word
    max_nesting_level = 0
    column_counts = defaultdict(lambda: defaultdict(int))
    for referenceNumber in range(40, 66+1):
        nn = referenceNumber - 39 # Want Matthew starting with 1
        BBB = BibleOrgSysGlobals.loadedBibleBooksCodes.getBBBFromReferenceNumber( referenceNumber )
        bookname = BibleOrgSysGlobals.loadedBibleBooksCodes.getEnglishName_NR( BBB )
        filename = LOWFAT_XML_FILENAME_TEMPLATE.replace( 'NN', str(nn).zfill(2) ).replace( 'wwww', bookname.lower().replace(' ','') )
        vPrint( 'Info', DEBUGGING_THIS_MODULE, f"  Loading {BBB} XML file from {filename}…")
        bookTree = ElementTree.parse( state.lowfat_XML_input_folderpath.joinpath( filename ) )

        # First make a table of parents so we can find them later
        parentMap = {child:parent for parent in bookTree.iter() for child in parent if child.tag in ('w','wg')}
        dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"  Loaded {len(parentMap):,} parent entries." )
        # print( str(parentMap)[:5000])

        # Now load all the word (w) fields for the chapter into a temporary list
        tempWordsAndMorphemes = []
        longIDs = []
        for elem in bookTree.getroot().iter():
            if elem.tag == 'w': # ignore all the others -- there's enough info in here
                for attribName in elem.attrib:
                    assert attribName in EXPECTED_WORD_ATTRIBUTES, f"loadClearLowFatGlossesXML(): unexpected {attribName=}"

                word = elem.text
                theirRef = elem.get('ref')
                # print( f"{word=} {theirRef=}" )

                longID = elem.get('{http://www.w3.org/XML/1998/namespace}id') # e.g., o010010050031 = obbcccvvvwwws
                longIDs.append( longID )
                assert longID.startswith( 'n' ) # Stands for NewTestament
                longID = longID[1:] # remove 'n' prefix
                assert len(longID) == 11
                assert longID[:].isdigit()

                role = elem.get('role')
                column_counts['role'][role] += 1

                gloss = elem.get('gloss')
                if gloss: gloss = gloss.replace( '.', '_' ) # Change to our system
                wType = elem.get('type')
                column_counts['type'][wType] += 1

                morph = elem.get('morph')
                column_counts['morph'][morph] += 1

                after = elem.get('after')
                column_counts['after'][after] += 1
                if after: assert len(after) <= 2, f"{len(after)} {after=}"

                wClass = elem.get('class')
                column_counts['class'][wClass] += 1
                person = elem.get('person')
                column_counts['person'][person] += 1
                gender = elem.get('gender')
                column_counts['gender'][gender] += 1
                number = elem.get('number')
                column_counts['number'][number] += 1
                tense = elem.get('tense')
                column_counts['tense'][tense] += 1
                voice = elem.get('voice')
                column_counts['voice'][voice] += 1
                mood = elem.get('mood')
                column_counts['mood'][mood] += 1
                degree = elem.get('degree')
                column_counts['degree'][degree] += 1
                junction = elem.get('junction')
                column_counts['junction'][junction] += 1

                discontinuous = elem.get('discontinuous')
                column_counts['discontinuous'][discontinuous] += 1

                # # Cross-checking
                # # TODO: Could do much more of this
                # if PoS=='noun': assert morph.startswith('N')
                # if morph.startswith('N'): assert PoS=='noun'

                English = elem.get('english')
                if English:
                    # if theirRef in ('MAT 15:4!18','MAT 19:9!22','MAT 21:19!30') and 
                    if English.endswith('.'): English = English[:-1]
                    assert '.' not in English, f"{theirRef} {word=} {English=}"
                    # assert English.strip() == English, f"{theirRef} '{word}' {English=}" # No leading or trailing spaces
                    English = English.strip() # for LUK 2:48!22 'ἐγὼ' English=' I'
                    English = English.replace( ' ', '_' )
                else: English = '' # Instead of None

                startElement = elem
                nestingBits = []
                while True:
                    parentElem = parentMap[startElement]
                    if parentElem.tag == 'error': # trying going one more up: parentElem.tag = parentMap[parentElem] FAILS
                        break # for now at Acts 26:12!1
                    if parentElem.tag == 'sentence': break
                    if parentElem.tag == 'error_unknown_complex_node': break # @ROM 11:22!1 got parentElem.tag='error_unknown_complex_node'
                    assert parentElem.tag == 'wg', f"@{theirRef} got {parentElem.tag=}"
                    pClass, pRole, pRule = parentElem.get('class'), parentElem.get('role'), parentElem.get('rule')
                    if not role: role = pRole # Take the first one
                    # print( f"@{theirRef} got {pClass=} {role=} {rule=}")
                    if pRole:
                        if pRule: # have both
                            nestingBits.append( f'{pRole}={pRule}' )
                        else: # only have role
                            nestingBits.append( pRole )
                    elif pRule: # have no role
                        nestingBits.append( pRule )
                    else:
                        # Fails 27Apr2023 with new updates to macula-greek lowfat
                        # assert pClass in ('compound',), f"{theirRef} has no role/rule {pClass=} {nestingBits}"
                        pass # Hopefully it doesn't matter
                    startElement = parentElem
                # print( f"@{theirRef} {nestingBits=}"); halt
                if len(nestingBits) >= max_nesting_level:
                    max_nesting_level = len(nestingBits) + 1

                # Convert pronoun referents (like 'n40001002014') to C:VwW (like '1:2w14')
                referentsStr = elem.get('referent')
                ourReferents = []
                if referentsStr:
                    if ';' in referentsStr:
                        print( f"{BBB} {longID} {word=} {gloss=} {English=} {referentsStr=}")
                    for referent in referentsStr.split( ' ' ):
                        if referent == 'n00000000000': continue # Ignore it. Why is this in MRK 10:3!5 'αὐτοῖς' referent='n00000000000'
                        # print( f"{BBB} {longID} {word=} {gloss=} {English=} {type(referent)} {referent=}")
                        assert len(referent)==12 and referent[0]=='n' and referent[1:].isdigit()
                        assert referent[1:3] == longID[:2], f"{theirRef} '{word}' {referent=}" # Don't expect referent links to point into other books
                        # referent = referent[3:] # remove 'n' prefix and predictable book number -- now down to nine digits: cccvvvwww
                        # rC, rV, rW = int(referent[3:6]), int(referent[6:9]), int(referent[9:])
                        ourReferent = f'{int(referent[3:6])}:{int(referent[6:9])}w{int(referent[9:])}' # Convert to 'C:VwW' form
                        # print( f" Got {rC=} {rV=} {rW=} so now {ourReferent=}" )
                        ourReferents.append( ourReferent )
                # Convert verb subject referents (like 'n40001002014') to C:VwW (like '1:2w14')
                subjectReferentsStr = elem.get('subjref')
                ourSubjectReferents = []
                if subjectReferentsStr:
                    if ';' in subjectReferentsStr: # there's about four of these as at 27Apr2023
                        print( f"{BBB} {longID} {word=} {gloss=} {English=} UNUSUAL {subjectReferentsStr=}")
                        subjectReferentsStr = subjectReferentsStr.replace( ';', ' ' )
                    for subjectReferent in subjectReferentsStr.split( ' ' ):
                        # print( f"{BBB} {longID} {word=} {gloss=} {English=} {type(subjectReferent)} {subjectReferent=}")
                        assert len(subjectReferent)==12 and subjectReferent[0]=='n' and subjectReferent[1:].isdigit()
                        assert subjectReferent[1:3] == longID[:2] # Don't expect referent links to point into other books
                        # referent = referent[3:] # remove 'n' prefix and predictable book number -- now down to nine digits: cccvvvwww
                        # rC, rV, rW = int(referent[3:6]), int(referent[6:9]), int(referent[9:])
                        ourSubjectReferent = f'{int(subjectReferent[3:6])}:{int(subjectReferent[6:9])}w{int(subjectReferent[9:])}' # Convert to 'C:VwW' form
                        # print( f" Got {rC=} {rV=} {rW=} so now {ourSubjectReferent=}" )
                        ourSubjectReferents.append( ourSubjectReferent )
                if ourReferents and ourSubjectReferents: # they have both!!!
                    print( f"{theirRef} Found both {ourReferents=} and {ourSubjectReferents=} for '{word}'" )
                    # assert theirRef in ('MAT 4:19!4','MAT 11:28!1'), f"{theirRef=}"
                    ourReferents = list(set(ourReferents+ourSubjectReferents)) # But this loses the order sadly
                    print( f"    From the above got {ourReferents}" )
                    # if ourReferents != ourSubjectReferents: halt
                    ourSubjectReferents = []
                if ourReferents: assert not ourSubjectReferents, f"{ourReferents=} {ourSubjectReferents=}"
                if ourSubjectReferents:
                    assert not ourReferents
                    ourReferents = ourSubjectReferents # We can combine these into one column (because we know the POS anyway)

                # Names have to match state.output_fieldnames:
                # ['FGRef','BibTagId','LFRef','LFNumRef',
                # 'Language','Word','Unicode','After',
                # 'WordClass','PartOfSpeech','Person','Gender','Number','WordType','Domain',
                # 'StrongNumberX','StrongLemma','Morphology','Lemma','SenseNumber',
                # 'CoreDomain','LexicalDomain','ContextualDomain',
                # 'ParticipantRef','Frame',
                # 'Strong',
                # 'EnglishGloss','ContextualGloss',
                # 'Nesting']
                entry = {'LFRef':theirRef, 'LFNumRef':longID, 'Word':word, 'Role':role,
                            'Unicode':elem.get('unicode'), 'After':after,
                            'WordClass':wClass, 'Person':person, 'Gender':gender, 'Number':number,
                            'Tense':tense, 'Voice':voice, 'Mood':mood, 'Degree':degree,
                            'WordType':wType, 'Domain':elem.get('domain'),
                            'Frames':elem.get('frame'), 'Referents':';'.join(ourReferents),
                            'Strong':elem.get('strong'), 'Discontinuous':discontinuous,
                            'Morphology':morph, 'Lemma':elem.get('lemma'),
                            'Junction':junction, 'ContextualGloss':gloss,
                            'Nesting':'/'.join(reversed(nestingBits)) }
                assert len(entry) == len(state.output_fieldnames)-2, f"{len(entry)=} vs {len(state.output_fieldnames)=}" # Two more fields to be added below
                tempWordsAndMorphemes.append( entry )
                if DEBUGGING_THIS_MODULE: # Check we haven't ended up with anything missing or any extra stuff at this point
                    for fieldname in entry: assert fieldname in state.output_fieldnames, f"{fieldname} missing from fieldnames"
                    for fieldname in state.output_fieldnames:
                        if fieldname not in ('FGRef','BibTagId'): assert fieldname in entry, f"{fieldname} missing from entry"

        vPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"    Got {len(tempWordsAndMorphemes):,} words/morphemes in {BBB}" )
        assert len(set(longIDs)) == len(longIDs), f"Should be no duplicates in {longIDs=}"

        # Note that because of the phrase/clause nesting, we can get the word fields in the wrong order
        #   so we sort them, before adjusting the formatting to what we're after
        # We sort by the Clear.Bible longID (2nd item in tuple, which already has the leading 'o' removed)
        sortedTempWordsAndMorphemes = sorted( tempWordsAndMorphemes, key=lambda t: t['LFNumRef'] )

        # Adjust to our references and with just the data that we need to retain
        for j,firstEntryAttempt in enumerate( sortedTempWordsAndMorphemes ):
            longID = firstEntryAttempt['LFNumRef']
            # if longID.startswith('01003009'): print(j, sixTuple)
            try: nextLongID = sortedTempWordsAndMorphemes[j+1]['LFNumRef']
            except IndexError: nextLongID = '1'
            assert nextLongID != longID, f"Should be no duplicate IDs: {j=} {longID=} {nextLongID=} {firstEntryAttempt}"
            ourRef = f"{BBB}_{firstEntryAttempt['LFRef'][4:].replace( '!', 'w')}"
            # print(f"{longID=} {nextLongID=} {mwType=} {ourRef=}")
            newExpandedDictEntry = {'FGRef':ourRef, **firstEntryAttempt}
            assert len(newExpandedDictEntry) == len(state.output_fieldnames)-1, f"{len(newExpandedDictEntry)=} vs {len(state.output_fieldnames)=}" # BibTagId field to be added below
            state.lowFatWordsAndMorphemes.append( newExpandedDictEntry )

    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  Got total of {len(state.lowFatWordsAndMorphemes):,} words/morphemes")
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
    # if 0:
    #     for n,currentEntry in enumerate(state.lowFatWordsAndMorphemes):
    #         assert len(currentEntry) == len(state.output_fieldnames)-1
    #         if n < 5 or 'THE' in currentEntry['EnglishGloss']: print(f"{n} ({len(currentEntry)}) {currentEntry}")
    return True
# end of convert_ClearMaculaNT_to_TSV.loadClearLowFatGlossesXML


def words_match( greekWord1, greekWord2, loose=True ) -> bool:
    """
    """
    if greekWord1==greekWord2: return True
    lower1, lower2 = greekWord1.lower(), greekWord2.lower()
    if lower1==lower2: return True
    if not loose: return False

    # Handle special cases, e.g., spelling differences between Nestle1904 (Clear.Bible) and unfoldingWord UGNT (BibleTags)
    for knownWord1,knownWord2 in ( ('Ἰωσίαν'.lower(), 'Ἰωσείαν'.lower()),
                                    ('Ἰωσίας'.lower(), 'Ἰωσείας'.lower()),
                                    ('παρέλαβε', 'παρέλαβεν'),
                                    ('λείαν', 'λίαν'),
                                    ):
        if lower1==knownWord1 and lower2==knownWord2:
            return True

    # Remove accents
    for charSet,simpleChar in ( ('ἀἁἂἃἄἅἆἇάὰάᾀᾁᾂᾃᾄᾅᾆᾇᾰᾱᾲᾳᾴᾶᾷἈἉἊἋἌἍἎἏΆᾈᾉᾊᾋᾌᾍᾎᾏᾸᾹᾺΆᾼ','α'),
                                ('ἐἑἒἓἔἕέὲέἘἙἚἛἜἝῈΈΈ','ε'),
                                ('ἠἡἢἣἤἥἦἧὴήᾐᾑᾒᾓᾔᾕᾖᾗῂῃῄῆῇήἨἩἪἫἬἭἮἯᾘᾙᾚᾛᾜᾝᾞᾟῊΉῌΉ','η'),
                                ('ἰἱἲἳἴἵἶἷὶίῐῑῒΐῖῗΐίϊΐίἸἹἺἻἼἽἾἿῚΊῘῙΊΪ','ι'),
                                ('ὀὁὂὃὄὅὸόόὈὉὊὋὌὍῸΌΌ','o'),
                                ('ὐὑὒὓὔὕὖὗὺύῠῡῢΰῦῧΰύϋὙὛὝὟῨῩῪΎΎΫ','υ'),
                                ('ὠὡὢὣὤὥὦὧὼώᾠᾡᾢᾣᾤᾥᾦᾧῲῳῴῶῷώὨὩὪὫὬὭὮὯᾨᾩᾪᾫᾬᾭᾮᾯῺΏῼΏ','ω'),
                                # ('ῤῥῬ','ρ'),
                                # ('῞ʹ͵΄᾽᾿῍῎῏῝῞῟῭΅`΅´῾῀῁',''),
                                ):
            for char in charSet:
                lower1 = lower1.replace(char, simpleChar)
                lower2 = lower2.replace(char, simpleChar)
    if lower1 == lower2:
        return True

    # Handle mostly similar words
    identicalStartCount = identicalEndCount = 0
    for char1,char2 in zip(greekWord1, greekWord2):
        if char1==char2:
            identicalStartCount += 1
        else: break
    for char1,char2 in zip(reversed(greekWord1), reversed(greekWord2)):
        if char1==char2:
            identicalEndCount += 1
        else: break
    # print(identicalStartCount,identicalEndCount)
    return (identicalStartCount+identicalEndCount) >= len(greekWord1) -2
# end of convert_ClearMaculaNT_to_TSV.words_match


def add_BibleTags_ids() -> bool:
    """
    The Clear.Bible data doesn't use the 5-character BibleTags id fields.

    So match the entries and add them in.
    """
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"\nMatching rows in both tables to add BibleTags ids…" )

    # We expect ['Ref', 'BibTagId', 'Word', 'Lemma', 'Strong', 'Morphology', 'After']
    BibTags_dict = {row['Ref']:(row['Word'],row['Morphology'],row['BibTagId']) for row in state.BibTags_rows} # We include the morphology for extra checking

    offset = addedCount = skippedCount = 0
    lastVerseID = None
    newLowFatWordsAndMorphemes = []
    for n,secondEntryAttempt in enumerate(state.lowFatWordsAndMorphemes):
        assert len(secondEntryAttempt) == len(state.output_fieldnames)-1
        ourID, word, morphology = secondEntryAttempt['FGRef'], secondEntryAttempt['Word'], secondEntryAttempt['Morphology']
        # print(n, ourID, word, morphology)
        verseID, wordPart = ourID.split('w')
        assert wordPart.isdigit()
        wordNumber = int( wordPart )

        if verseID != lastVerseID:
            offset = 0 # Restart at start of verse
        adjustedRowID = f'{verseID}w{wordNumber+offset}'
        try:
            foundWord, foundMorphology, foundID = BibTags_dict[adjustedRowID]
            # print("  ",foundWord, foundMorphology, foundID)
            # print(f"({len(foundWord)}) {foundWord} ({len(word)}) {word} {foundWord==word}")
            assert words_match( foundWord, word), f"ID's matched {adjustedRowID} from {ourID} and got {foundID}, but not text ({len(foundWord)}) '{foundWord}' != ({len(word)}) '{word}'"
            # Seems we can't match morphology, cf. foundMorphology='Gr,N,,,,,NFS,' vs. morphology='N-NSF'
            # print(f"{foundMorphology=} {morphology=}")
            # for mBit in morphology:
            #     assert mBit in foundMorphology, \
            #         f"ID's matched {adjustedRowID} from {ourID} and got {foundID}, but not morphology '{foundMorphology}'!='{morphology}'"
            # assert foundMorphology==morphology \
            #     or (foundMorphology=='Rd' and morphology=='R'), \
            #     f"ID's matched {adjustedRowID} from {ourID} and got {foundID}, but not morphology '{foundMorphology}'!='{morphology}'"
            # print(f"({len(secondEntryAttempt)}) {secondEntryAttempt=}")
            newMoreExpandedDictEntry = {'FGRef':ourID, 'BibTagId':foundID, **secondEntryAttempt}
            addedCount += 1
            # print(f"({len(newMoreExpandedDictEntry)}) {newMoreExpandedDictEntry=}")
            assert len(newMoreExpandedDictEntry) == len(state.output_fieldnames), f"{len(newMoreExpandedDictEntry)=} vs {len(state.output_fieldnames)=}" # BibTagId field to be added below
            newLowFatWordsAndMorphemes.append( newMoreExpandedDictEntry )
        except KeyError:
            logging.warning( f"Failed to find BibleTags id for {offset=} {ourID}: '{word}' {morphology}" )
            adjustedRowID = f'{verseID}w{wordNumber+offset}'
            try:
                foundWord, foundMorphology, foundID = BibTags_dict[adjustedRowID]
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  Got {foundID} for {offset=} {adjustedRowID}")
                assert foundWord==word, f"ID's now matched {adjustedRowID} from {ourID} and got {foundID}, but not text ({len(foundWord)}) '{foundWord}' != ({len(word)}) '{word}'"
                assert foundMorphology==morphology, f"ID's now matched {adjustedRowID} from {ourID} and got {foundID}, but not morphology '{foundMorphology}'!='{morphology}'"
                newMoreExpandedDictEntry = {'FGRef':ourID, 'BibTagId':foundID, **secondEntryAttempt}
                addedCount += 1
                assert len(newMoreExpandedDictEntry) == len(state.output_fieldnames), f"{len(newMoreExpandedDictEntry)=} vs {len(state.output_fieldnames)=}" # BibTagId field to be added below
                newLowFatWordsAndMorphemes.append( newMoreExpandedDictEntry )
            except (KeyError, AssertionError):
                logging.error( f"Failed to find BibleTags id for {offset=} {adjustedRowID} from {ourID}: '{secondEntryAttempt['Word']}'")
                newMoreExpandedDictEntry = {'FGRef':ourID, 'BibTagId':'', **secondEntryAttempt}
                assert len(newMoreExpandedDictEntry) == len(state.output_fieldnames), f"{len(newMoreExpandedDictEntry)=} vs {len(state.output_fieldnames)=}" # BibTagId field to be added below
                newLowFatWordsAndMorphemes.append( newMoreExpandedDictEntry )
        except AssertionError:
            logging.warning( f"Failed to match text for {offset=} {ourID}: '{foundWord}' vs '{word}' {foundMorphology} vs {morphology}")
            adjustedRowID = f'{verseID}w{wordNumber+offset}'
            try:
                foundWord, foundMorphology, foundID = BibTags_dict[adjustedRowID]
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  Got {foundID} for {offset=} {adjustedRowID}")
                assert foundWord==word, f"ID's now matched {adjustedRowID} from {ourID} and got {foundID}, but not text ({len(foundWord)}) '{foundWord}' != ({len(word)}) '{word}'"
                assert foundMorphology==morphology, f"ID's now matched {adjustedRowID} from {ourID} and got {foundID}, but not morphology '{foundMorphology}'!='{morphology}'"
                newMoreExpandedDictEntry = {'FGRef':ourID, 'BibTagId':foundID, **secondEntryAttempt}
                addedCount += 1
                assert len(newMoreExpandedDictEntry) == len(state.output_fieldnames), f"{len(newMoreExpandedDictEntry)=} vs {len(state.output_fieldnames)=}" # BibTagId field to be added below
                newLowFatWordsAndMorphemes.append( newMoreExpandedDictEntry )
            except (KeyError, AssertionError):
                logging.error( f"Failed to find BibleTags id for {offset=} {adjustedRowID} from {ourID}: '{secondEntryAttempt['Word']}'")
                newMoreExpandedDictEntry = {'FGRef':ourID, 'BibTagId':'', **secondEntryAttempt}
                skippedCount += 1
                assert len(newMoreExpandedDictEntry) == len(state.output_fieldnames), f"{len(newMoreExpandedDictEntry)=} vs {len(state.output_fieldnames)=}" # BibTagId field to be added below
                newLowFatWordsAndMorphemes.append( newMoreExpandedDictEntry )
        # Check we haven't ended up with anything missing or any extra stuff
        for fieldname in newLowFatWordsAndMorphemes[-1]: assert fieldname in state.output_fieldnames
        for fieldname in state.output_fieldnames: assert fieldname in newLowFatWordsAndMorphemes[-1]
        lastVerseID = verseID

    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  Added {addedCount:,} BibTags IDs" )
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  Skipped {skippedCount:,} BibTags IDs" )

    assert len(newLowFatWordsAndMorphemes) == len(state.lowFatWordsAndMorphemes)
    state.lowFatWordsAndMorphemes = newLowFatWordsAndMorphemes
    return True
# end of convert_ClearMaculaNT_to_TSV.loadClearLowFatGlossesXML


def save_filled_TSV_file() -> bool:
    """
    Save table as a single TSV file (about 25 MB).
    """
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"\nExporting filled NT Low Fat table as a single flat TSV file to {state.TSV_output_filepath}…" )

    BibleOrgSysGlobals.backupAnyExistingFile( state.TSV_output_filepath, numBackups=5 )

    # print(len(state.lowFatWordsAndMorphemes[0]), state.lowFatWordsAndMorphemes[0]);halt
    with open( state.TSV_output_filepath, 'wt', encoding='utf-8' ) as tsv_output_file:
        tsv_output_file.write('\ufeff') # Write BOM
        writer = DictWriter( tsv_output_file, fieldnames=state.output_fieldnames, delimiter='\t' )
        writer.writeheader()
        for thisTuple in state.lowFatWordsAndMorphemes:
            # print( f"{state.output_fieldnames=} {thisTuple=}" )
            assert len(thisTuple) == len(state.output_fieldnames)
            thisRow = {k:thisTuple[k] for k in state.output_fieldnames} # Make sure we have the fields in the correct output order
            # print( f"\n{thisRow=}" )
            writer.writerow( thisRow )
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  {len(state.lowFatWordsAndMorphemes):,} data rows written." )

    if 1: # Collect and print stats
        non_blank_counts, blank_counts = defaultdict(int), defaultdict(int)
        sets = defaultdict(set)
        for entry in state.lowFatWordsAndMorphemes:
            for fieldname,value in entry.items():
                if value: non_blank_counts[fieldname] += 1
                else: blank_counts[fieldname] += 1
                sets[fieldname].add( value )
        for fieldname,count in blank_counts.items():
            assert count < len(state.lowFatWordsAndMorphemes), f"Field is never filled: '{fieldname}'"
        vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"\nCounts of non-blank fields for {len(state.lowFatWordsAndMorphemes):,} rows:" )
        for fieldname,count in non_blank_counts.items():
            non_blank_count_str = 'all' if count==len(state.lowFatWordsAndMorphemes) else f'{count:,}'
            unique_count_str = 'all' if len(sets[fieldname])==len(state.lowFatWordsAndMorphemes) else f'{len(sets[fieldname]):,}'
            vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  {fieldname}: {non_blank_count_str} non-blank entries (with {unique_count_str} unique entries)" )
            assert count # Otherwise we're including a field that contains nothing!
            if len(sets[fieldname]) < 50:
                vPrint( 'Info', DEBUGGING_THIS_MODULE, f"    being: {sets[fieldname]}" )

    return True
# end of convert_ClearMaculaNT_to_TSV.save_filled_TSV_file


def save_shortened_TSV_file() -> bool:
    """
    Save table as a single TSV file
        but with a number of fields deleted or abbreviated to make it smaller.

    Of course, this makes the table less self-documenting!
    """
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"\nExporting shortened NT Low Fat table as a single flat TSV file to {state.TSV_output_filepath}…" )

    BibleOrgSysGlobals.backupAnyExistingFile( state.shortened_TSV_output_filepath, numBackups=5 )

    columnsToRemove = ('LFRef','LFNumRef', # Don't need their references
        'Unicode', # Not sure what this was anyway
        )
    shortenedFieldnameList = [fieldname for fieldname in state.output_fieldnames if fieldname not in columnsToRemove]
    # print(f"({len(state.output_fieldnames)}) {state.output_fieldnames} -> ({len(shortenedFieldnames)}) {shortenedFieldnames}")

    # print(len(state.lowFatWordsAndMorphemes[0]), state.lowFatWordsAndMorphemes[0]);halt
    with open( state.shortened_TSV_output_filepath, 'wt', encoding='utf-8' ) as tsv_output_file:
        tsv_output_file.write('\ufeff') # Write BOM
        writer = DictWriter( tsv_output_file, fieldnames=shortenedFieldnameList, delimiter='\t' )
        writer.writeheader()
        for thisEntryDict in state.lowFatWordsAndMorphemes:
            for columnName in columnsToRemove:
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
            # thisEntryDict['PartOfSpeech'] = {'noun':'n','verb':'v','preposition':'pp', 'particle':'part', 'conjunction':'cj',
            #                 'suffix':'suffix', 'adjective':'adj','pronoun':'pron','adverb':'adv'}[thisEntryDict['PartOfSpeech']]
            if thisEntryDict['Person']: # Abbreviate
                thisEntryDict['Person'] = {'first':'1','second':'2','third':'3', 'unknown: x':'?'}[thisEntryDict['Person']]
            if thisEntryDict['Gender']: # Abbreviate
                thisEntryDict['Gender'] = {'masculine':'m','feminine':'f','neuter':'n'}[thisEntryDict['Gender']]
            if thisEntryDict['Number']: # Abbreviate
                thisEntryDict['Number'] = {'singular':'s','plural':'p','dual':'d', 'unknown: x':'?'}[thisEntryDict['Number']]
            assert len(thisEntryDict) == len(state.output_fieldnames) - len(columnsToRemove)
            writer.writerow( thisEntryDict )

    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  {len(state.lowFatWordsAndMorphemes):,} shortened data rows written." )
    return True
# end of convert_ClearMaculaNT_to_TSV.save_shortened_TSV_file


if __name__ == '__main__':
    # from multiprocessing import freeze_support
    # freeze_support() # Multiprocessing support for frozen Windows executables

    # Configure basic Bible Organisational System (BOS) set-up
    parser = BibleOrgSysGlobals.setup( SHORT_PROGRAM_NAME, PROGRAM_VERSION, LAST_MODIFIED_DATE )
    BibleOrgSysGlobals.addStandardOptionsAndProcess( parser )

    main()

    BibleOrgSysGlobals.closedown( PROGRAM_NAME, PROGRAM_VERSION )
# end of convert_ClearMaculaNT_to_TSV.py
