#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# connect_OET-RV_words.py
#
# Script to take the OET-RV NT USFM files and convert to HTML
#
# Copyright (C) 2023 Robert Hunt
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
"""
from gettext import gettext as _
from tracemalloc import start
from typing import List, Tuple, Optional
from pathlib import Path
from datetime import datetime
import logging
import re

if __name__ == '__main__':
    import sys
    sys.path.insert( 0, '../../BibleOrgSys/' )
from BibleOrgSys import BibleOrgSysGlobals
from BibleOrgSys.BibleOrgSysGlobals import vPrint, fnPrint, dPrint
from BibleOrgSys.Bible import Bible
from BibleOrgSys.Internals.InternalBibleInternals import getLeadingInt
from BibleOrgSys.Reference.BibleBooksCodes import BOOKLIST_OT39, BOOKLIST_NT27, BOOKLIST_66
from BibleOrgSys.Reference.BibleOrganisationalSystems import BibleOrganisationalSystem
from BibleOrgSys.Formats.ESFMBible import ESFMBible


LAST_MODIFIED_DATE = '2023-03-16' # by RJH
SHORT_PROGRAM_NAME = "connect_OET-RV_words"
PROGRAM_NAME = "Convert OET-RV words to OET-LV word numbers"
PROGRAM_VERSION = '0.07'
PROGRAM_NAME_VERSION = '{} v{}'.format( SHORT_PROGRAM_NAME, PROGRAM_VERSION )

DEBUGGING_THIS_MODULE = False


project_folderpath = Path(__file__).parent.parent # Find folders relative to this module
FG_folderpath = project_folderpath.parent # Path to find parallel Freely-Given.org repos
OET_LV_OT_USFM_InputFolderPath = project_folderpath.joinpath( 'intermediateTexts/auto_edited_OT_USFM/' )
OET_LV_NT_ESFM_InputFolderPath = project_folderpath.joinpath( 'intermediateTexts/auto_edited_VLT_ESFM/' )
OET_RV_ESFM_FolderPath = project_folderpath.joinpath( 'translatedTexts/ReadersVersion/' )
assert OET_LV_OT_USFM_InputFolderPath.is_dir()
assert OET_LV_NT_ESFM_InputFolderPath.is_dir()
assert OET_RV_ESFM_FolderPath.is_dir()

# EN_SPACE = ' '
EM_SPACE = ' '
NARROW_NON_BREAK_SPACE = ' '
BACKSLASH = '\\'


class State:
    """
    A place to store some of the global stuff that needs to be passed around.
    """
    simpleNouns = ( # These are nouns that are likely to match one-to-one from the OET-LV to the OET-RV
                    #   i.e., there's really no other word for them.
        # NOTE: Some of these nouns can also be verbs -- we may need to remove those???
        # 'sons' causes problems
        'ambassadors','ambassador', 'ancestors','ancestor', 'angels','angel', 'ankles','ankle', 'authority',
        'birth', 'blood', 'boats','boat', 'bodies','body', 'boys','boy', 'bread', 'branches','branch', 'brothers','brother', 'bulls','bull',
        'camels','camel', 'chairs','chair', 'chariots','chariot', 'chests','chest', 'children','child',
            'cities','city', 'coats','coat', 'commands','command', 'councils','council', 'countries','country',
        'daughters','daughter', 'days','day', 'donkeys','donkey', 'doors','door', 'dreams','dream', 'dyes','dye',
        'eyes','eye',
        'faces','face', 'faith', 'farmers','farmer', 'fathers','father', 'fields','field', 'figs','fig', 'fingers','finger', 'fires','fire', 'fish', 'foot','feet',
            'friends','friend', 'fruits','fruit',
        'generations','generation', 'gifts','gift', 'girls','girl', 'goats','goat', 'gods','god', 'gold',
            'grace', 'grains','grain', 'grapes','grape', 'greed',
        'hands','hand', 'happiness', 'hearts','heart', 'heavens','heaven', 'homes','home', 'honey', 'horses','horse', 'houses','house', 'husbands','husband',
        'idols','idol', 'ink',
        'kings','king', 'kingdoms','kingdom', 'kisses','kiss',
        'languages','language', 'leaders','leader', 'letters','letter', 'life', 'lights','light', 'lions','lion', 'lips','lip', 'loaf','loaves', 'locusts','locust', 'love',
        'man','men', 'markets','market', 'mercy', 'messages','message', 'meetings','meeting', 'moon', 'mothers','mother', 'mouths','mouth',
        'names','name', 'nations','nation', 'nets','net', 'noises','noise',
        'officers','officer', 'officials','official',
        'peace', 'pens','pen', 'people', 'places','place', 'powers','power', 'prayers','prayer', 'priests','priest', 'prisons','prison', 'promises','promise'
        'rivers','river', 'roads','road', 'robes','robe', 'ropes','rope',
        'sea', 'servants','servant', 'services','service', 'shame', 'sheep', 'shepherds','shepherd',
            'signs','sign', 'silver', 'sinners','sinner', 'sins','sin', 'sisters','sister', 'sky', 'slaves','slave',
            'soldiers','soldier', 'sons', 'souls','soul', 'spirits', 'spirit',
            'stars','star', 'stones','stone', 'streets','street', 'sun', 'swords','sword',
        'tables','table', 'teachers','teacher', 'things','thing', 'thrones','throne', 'times','time', 'tombs','tomb', 'tongues','tongue', 'towns','town', 'trees','tree', 'truth',
        'vines','vine', 'visions','vision',
        'water', 'weeks','week', 'widows','widow', 'wife','wives', 'woman','women', 'words','word',
        )
    verbalNouns = ('distribution',)
    # Verbs often don't work because we use the tenses differently between OET-RV and OET-LV/Greek
    simpleVerbs = ('accepted','accepting','accepts','accept', 'asked','asking','asks','ask', 'answered','answering','answers','answer',
                   'become','became','becomes','becoming',
                        'burnt','burning','burns','burn', 'buried','burying','buries','bury',
                   'came','coming','comes','come', 'caught','catching','catches','catch',
                   'died','dying','dies','die', 'distributed','distributing','distributes','distribute',
                   'encouraged','encouraging','encourages','encourage',
                   'followed','following','follows','follow', 'forbidding','forbids','forbid',
                   'gathered','gathering','gathers','gather', 'gave','giving','gives','give', 'went','going','goes','go', 'greeted','greeting','greets','greet',
                   'harvested','harvesting','harvests','harvest', 'hated','hating','hates','hate', 'healed','healing','heals','heal', 'helped','helping','helps','help',
                   'imitated','imitating','imitates','imitate', 'immersed','immersing','immerses','immerse',
                   'knew','knowing','knows','know',
                   'learnt','learning','learns','learn', 'lived','living','lives','live', 'looked','looking','looks','look',
                   'obeyed','obeying','obeys','obey',
                   'praised','praising','praises','praise',
                   'raised','raising','raises','raise',
                        'received','receiving','receives','receive', 'recovered','recovering','recovers','recover', 'released','releasing','releases','release', 'remained','remaining','remains','remain', 'reminded','reminding','reminds','remind', 'requested','requesting','requests','request', 'respected','respecting','respects','respect',
                        'ran','running','runs','run',
                   'said','saying','says','say', 'saved','saving','saves','save',
                        'seated','seating','seats','seat', 'seduced','seducing','seduces','seduce', 'saw','seeing','seen','sees','see', 'sent','sending','sends','send', 'served','serving','serves','serve',
                        'shared','sharing','shares','share', 'shone','shining','shines','shine', 'spoke','speaking','speaks','speak',
                        'stayed','staying','stays','stay', 'supported','supporting','supports','support',
                   'took','taking','takes','take', 'talked','talking','talks','talk', 'threw','throwing','throws','throw', 'turned','turning','turns','turn',
                   'walked','walking','walks','walk', 'wanted','wanting','wants','want', 'warned','warning','warns','warn', 'watched','watching','watches','watch',
                        'withered','withering','withers','wither',
                        'wrote','writing','writes','write',
                   )
    simpleAdverbs = ('quickly', 'immediately', 'loudly', 'suddenly',)
    simpleAdjectives = ('alive', 'angry', 'bad', 'clean',
                        'dead', 'disobedient', 'entire', 'evil', 'foolish', 'godly', 'good', 'happy', 'loud', 'obedient', 'sad', 'sudden', 'whole')
    # Don't use 'one' below because it has other meanings
    simpleNumbers = ('two','three','four','five','six','seven','eight','nine',
                     'ten','eleven','twelve','thirteen','fourteen','fifteen','sixteen','seventeen','eighteen','nineteen',
                     'twenty','thirty','forty','fifty','sixty','seventy','eighty','ninety',
                     'none')
    pronouns = ('he','she','it', 'him','her','its', 'you','we','they', 'your','our','their',
                'himself','herself','itself', 'yourself','yourselves', 'ourselves', 'themselves',
                'everyone')
    # We don't expect connectors to work very well
    connectors = ('and', 'but')
    simpleWords = simpleNouns + verbalNouns + simpleVerbs + simpleAdverbs+ simpleAdjectives  + simpleNumbers + pronouns + connectors
# end of State class

state = State()


def main():
    """
    Main program to handle command line parameters and then run what they want.
    """
    BibleOrgSysGlobals.introduceProgram( __name__, PROGRAM_NAME_VERSION, LAST_MODIFIED_DATE )

    # global genericBookList
    # genericBibleOrganisationalSystem = BibleOrganisationalSystem( 'GENERIC-KJV-ENG' )
    # genericBookList = genericBibleOrganisationalSystem.getBookList()

    rv = ESFMBible( OET_RV_ESFM_FolderPath, givenAbbreviation='OET-RV' )
    rv.loadAuxilliaryFiles = True
    rv.loadBooks() # So we can iterate through them all later
    rv.lookForAuxilliaryFilenames()
    dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"{rv=}")

    lv = ESFMBible( OET_LV_NT_ESFM_InputFolderPath, givenAbbreviation='OET-LV' )
    lv.loadAuxilliaryFiles = True
    lv.loadBooks() # So we can iterate through them all later
    lv.lookForAuxilliaryFilenames()
    dPrint( 'verbose', DEBUGGING_THIS_MODULE, f"{lv=}")

    # Convert files to simple HTML
    connect_OET_RV( rv, lv )
# end of connect_OET-RV_words.main


def connect_OET_RV( rv, lv ):
    """
    """
    fnPrint( DEBUGGING_THIS_MODULE, f"connect_OET_RV( {rv}, {lv} )" )
    for BBB,bookObject in lv.books.items():
        vPrint( 'Info', DEBUGGING_THIS_MODULE, f"  Processing connect words for OET {BBB}…" )

        wordFileName = bookObject.ESFMWordTableFilename
        if wordFileName:
            assert wordFileName.endswith( '.tsv' )
            vPrint( 'Info', DEBUGGING_THIS_MODULE, f"  Found ESFMBible filename '{wordFileName}' for {lv.abbreviation} {BBB}" )
            if lv.ESFMWordTables[wordFileName]:
                vPrint( 'Info', DEBUGGING_THIS_MODULE, f"  Found ESFMBible loaded '{wordFileName}' word link lines: {len(lv.ESFMWordTables[wordFileName]):,}" )
            else:
                vPrint( 'Info', DEBUGGING_THIS_MODULE, f"  No word links loaded yet for '{wordFileName}'" )
            if lv.ESFMWordTables[wordFileName] is None:
                with open( OET_LV_NT_ESFM_InputFolderPath.joinpath(wordFileName), 'rt', encoding='UTF-8' ) as wordFile:
                    lv.ESFMWordTables[wordFileName] = wordFile.read().split( '\n' )
                vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  connect_OET_RV loaded {len(lv.ESFMWordTables[wordFileName]):,} total rows from {wordFileName}" )
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  connect_OET_RV loaded column names were: ({len(lv.ESFMWordTables[wordFileName][0])}) {lv.ESFMWordTables[wordFileName][0]}" )
        state.wordTable = lv.ESFMWordTables[wordFileName]
        state.tableHeaderList = state.wordTable[0].split( '\t' )

        rvESFMFilename = f'OET-RV_{BBB}.ESFM'
        rvESFMFilepath = OET_RV_ESFM_FolderPath.joinpath( rvESFMFilename )
        with open( rvESFMFilepath, 'rt', encoding='UTF-8' ) as esfmFile:
            state.rvESFMText = esfmFile.read() # We keep the original (for later comparison)
            state.rvESFMLines = state.rvESFMText.split( '\n' )

        numChapters = lv.getNumChapters( BBB )
        if numChapters >= 1:
            for c in range( 1, numChapters+1 ):
                vPrint( 'Info', DEBUGGING_THIS_MODULE, f"      Connecting words for {BBB} {c}…" )
                numVerses = lv.getNumVerses( BBB, c )
                if numVerses is None: # something unusual
                    logging.critical( f"connect_OET_RV: no verses found for OET-LV {BBB} {c}" )
                    continue
                for v in range( 1, numVerses+1 ):
                    try:
                        rvVerseEntryList, _rvCcontextList = rv.getContextVerseData( (BBB, str(c), str(v)) )
                        lvVerseEntryList, _lvCcontextList = lv.getContextVerseData( (BBB, str(c), str(v)) )
                    except KeyError:
                        logging.critical( f"Seems we have no {BBB} {c}:{v} -- versification issue?" )
                        continue
                    # dPrint( 'Info', DEBUGGING_THIS_MODULE, f"RV entries: ({len(rvVerseEntryList)}) {rvVerseEntryList}")
                    # dPrint( 'Info', DEBUGGING_THIS_MODULE, f"LV entries: ({len(lvVerseEntryList)}) {lvVerseEntryList}")
                    connect_OET_RV_Verse( BBB, c, v, rvVerseEntryList, lvVerseEntryList )
        else:
            dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"connect_OET_RV {BBB} has {numChapters} chapters!!!" )
            assert BBB in ('INT','FRT',)

        newESFMtext = '\n'.join( state.rvESFMLines )
        if newESFMtext != state.rvESFMText:
            dPrint( 'Info', DEBUGGING_THIS_MODULE, f"{BBB} ESFM text has changed {len(state.rvESFMText):,} -> {len(newESFMtext):,}" )
            illegalWordLinkRegex1 = re.compile( '[0-9]¦' ) # Has digits BEFORE the broken pipe
            assert not illegalWordLinkRegex1.search( newESFMtext), f"illegalWordLinkRegex1 failed before saving {BBB}" # Don't want double-ups of wordlink numbers
            illegalWordLinkRegex2 = re.compile( '¦[1-9][0-9]{0,5}[a-z]' ) # Has letters AFTER the wordlink number
            assert not illegalWordLinkRegex2.search( newESFMtext), f"illegalWordLinkRegex2 failed before saving {BBB}" # Don't want double-ups of wordlink numbers
            with open( rvESFMFilepath, 'wt', encoding='UTF-8' ) as esfmFile:
                esfmFile.write( newESFMtext )
            vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"    Saved OET-RV {BBB} {len(newESFMtext):,} bytes to {rvESFMFilepath}" )
        else:
            vPrint( 'Info', DEBUGGING_THIS_MODULE, f"    No changes made to OET-RV {BBB}." )
# end of connect_OET-RV_words.connect_OET_RV


def connect_OET_RV_Verse( BBB:str, c:int,v:int, rvEntryList, lvEntryList ):
    """
    """
    # fnPrint( DEBUGGING_THIS_MODULE, f"connect_OET_RV( {BBB} {c}:{v} {len(rvEntryList)}, {len(lvEntryList)} )" )

    rvText = ''
    for rvEntry in rvEntryList:
        rvMarker, rvRest = rvEntry.getMarker(), rvEntry.getCleanText()
        # print( f"OET-RV {BBB} {c}:{v} {rvMarker}='{rvRest}'")
        if rvMarker in ('v~','p~'):
            rvText = f"{rvText}{' ' if rvText else ''}{rvRest}"
    lvText = ''
    for lvEntry in lvEntryList:
        lvMarker,lvRest = lvEntry.getMarker(), lvEntry.getCleanText()
        if lvMarker in ('v~','p~'):
            lvText = f"{lvText}{' ' if lvText else ''}{lvRest.replace('+','')}"
    if not rvText or not lvText: return
    rvAdjText = rvText.replace('≈','').replace('…','') \
                .replace('.','').replace(',','').replace(':','').replace('?','').replace('!','').replace('—',' ') \
                .replace( '(', '').replace( ')', '' ) \
                .replace( '“', '' ).replace( '”', '' ).replace( '', '' ).replace( '’', '') \
                .replace('  ',' ').strip()
    lvAdjText = lvText.replace('_',' ') \
                .replace('.','').replace(',','').replace(':','').replace('?','').replace('!','') \
                .replace( '(', '').replace( ')', '' ) \
                .replace('  ',' ').strip()
    # print( f"({len(rvAdjText)}) {rvAdjText=}")
    # print( f"({len(lvAdjText)}) {lvAdjText=}")
    if not rvAdjText or not lvAdjText: return
    rvWords = rvAdjText.split( ' ' )
    lvWords = lvAdjText.split( ' ' )
    # print( f"({len(rvWords)}) {rvWords=}")
    # print( f"({len(lvWords)}) {lvWords=}")
    assert rvWords
    assert lvWords
    for rvWord in rvWords:
        assert rvWord, f"{rvText=} {rvAdjText=}"
        assert rvWord.count( '¦' ) <= 1 # Check that we haven't been retagging already tagged RV words
    matchSimpleWords( BBB, c,v, rvWords, lvWords )

    # Now get the uppercase words
    rvUpperWords = [rvWord for rvWord in rvWords if rvWord[0].isupper()]
    lvUpperWords = [lvWord for lvWord in lvWords if lvWord[0].isupper()]
    # print( f"'{rvText}' '{lvText}'" )
    if rvText[0].isupper(): rvUpperWords.pop(0) # Throw away the first word
    if lvText[0].isupper(): lvUpperWords.pop(0) # Throw away the first word
    # print( f"({len(rvUpperWords)}) {rvUpperWords}")
    # print( f"({len(lvUpperWords)}) {lvUpperWords}")
    if rvUpperWords and lvUpperWords:
        matchProperNouns( BBB, c,v, rvUpperWords, lvUpperWords )
# end of connect_OET-RV_words.connect_OET_RV_Verse


CNTR_ROLE_NAME_DICT = {'N':'noun', 'S':'substantive adjective', 'A':'adjective', 'E':'determiner/case-marker', 'R':'pronoun',
                  'V':'verb', 'I':'interjection', 'P':'preposition', 'D':'adverb', 'C':'conjunction', 'T':'particle'}
CNTR_MOOD_NAME_DICT = {'I':'indicative', 'M':'imperative', 'S':'subjunctive', 
            'O':'optative', 'N':'infinitive', 'P':'participle', 'e':'e'}
CNTR_TENSE_NAME_DICT = {'P':'present', 'I':'imperfect', 'F':'future', 'A':'aorist', 'E':'perfect', 'L':'pluperfect', 'U':'U', 'e':'e'}
CNTR_VOICE_NAME_DICT = {'A':'active', 'M':'middle', 'P':'passive', 'p':'p', 'm':'m', 'a':'a'}
CNTR_PERSON_NAME_DICT = {'1':'1st', '2':'2nd', '3':'3rd', 'g':'g'}
CNTR_CASE_NAME_DICT = {'N':'nominative', 'G':'genitive', 'D':'dative', 'A':'accusative', 'V':'vocative', 'g':'g', 'n':'n', 'a':'a', 'd':'d', 'v':'v', 'U':'U'}
CNTR_GENDER_NAME_DICT = {'M':'masculine', 'F':'feminine', 'N':'neuter', 'm':'m', 'f':'f', 'n':'n'}
CNTR_NUMBER_NAME_DICT = {'S':'singular', 'P':'plural', 's':'s', 'p':'p'}
def matchProperNouns( BBB:str, c:int,v:int, rvCapitalisedWordList:List[str], lvCapitalisedWordList:List[str] ):
    """
    """
    fnPrint( DEBUGGING_THIS_MODULE, f"matchProperNouns( {BBB} {c}:{v} {rvCapitalisedWordList}, {lvCapitalisedWordList} )" )
    assert rvCapitalisedWordList and lvCapitalisedWordList

    # But we don't want any rvWords that are already tagged
    for rvN,rvCapitalisedWord in enumerate( rvCapitalisedWordList[:] ):
        if '¦' in rvCapitalisedWord:
            _rvCapitalisedWord, rvWordNumber = rvCapitalisedWord.split('¦')
            dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  matchProperNouns( {BBB} {c}:{v} ) removing already tagged '{rvCapitalisedWord}' from RV list…")
            rvCapitalisedWordList.pop( rvN )
            for lvN,lvCapitalisedWord in enumerate( lvCapitalisedWordList[:] ):
                if lvCapitalisedWord.endswith( f'¦{rvWordNumber}' ):
                    dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  matchProperNouns( {BBB} {c}:{v} ) removing already tagged '{lvCapitalisedWord}' from LV list…")
                    lvCapitalisedWordList.pop( lvN )
    if not rvCapitalisedWordList or not lvCapitalisedWordList:
        return # nothing left to do here

    if len(rvCapitalisedWordList)==1 and len(lvCapitalisedWordList)==1: # easy case!
        assert rvCapitalisedWordList[0].replace("'",'').isalpha(), f"{rvCapitalisedWordList=}" # It might contain an apostrophe
        capitalisedNoun,wordNumber,wordRow = getLVWordRow( lvCapitalisedWordList[0] )
        wordRole = wordRow[state.tableHeaderList.index('Role')]
        dPrint( 'Info', DEBUGGING_THIS_MODULE, f"'{capitalisedNoun}' {wordRole}" )
        if wordRole == 'N': # let's assume it's a proper noun
            addNumberToRVWord( BBB, c,v, rvCapitalisedWordList[0], wordNumber )
    elif len(rvCapitalisedWordList) == len(lvCapitalisedWordList):
        dPrint( 'Info', DEBUGGING_THIS_MODULE, f"Lists are equal size ({len(rvCapitalisedWordList)})" )
        return
        for capitalisedNounPair in lvCapitalisedWordList:
            capitalisedNoun,wordNumber,wordRow = getLVWordRow( capitalisedNounPair )
            dPrint( 'Info', f"'{capitalisedNoun}' {wordRow}" )
            halt
    else:
        dPrint( 'Info', DEBUGGING_THIS_MODULE, f"Lists are different sizes {len(rvCapitalisedWordList)=} and {len(lvCapitalisedWordList)=}" )
        return
        for capitalisedNounPair in lvCapitalisedWordList:
            capitalisedNoun,wordNumber,wordRow = getLVWordRow( capitalisedNounPair )
            dPrint( 'Info', f"'{capitalisedNoun}' {wordRow}" )
            halt
# end of connect_OET-RV_words.matchProperNouns


def matchSimpleWords( BBB:str, c:int,v:int, rvWordList:List[str], lvWordList:List[str] ):
    """
    If the simple word (e.g., nouns) only occur once in the RV verse and once in the LV verse,
        we assume that we can match them, i.e., copy the wordlink numbers from the LV into the RV.
    """
    fnPrint( DEBUGGING_THIS_MODULE, f"matchSimpleWords( {BBB} {c}:{v} {rvWordList}, {lvWordList} )" )
    assert rvWordList and lvWordList

    for simpleNoun in state.simpleWords:
        # print( f"{simpleNoun}" )
        lvIndexList = []
        for lvN,lvWord in enumerate( lvWordList ):
            # assert lvWord.isalpha(), f"'{lvWord}'" # Might contain an apostrophe
            if f'{simpleNoun}¦' in lvWord:
                lvIndexList.append( lvN )
        if not lvIndexList: continue
        # print( f"{BBB} {c}:{v} {simpleNoun=} {lvIndexList=}" )
        rvIndexList = []
        for rvN,rvWord in enumerate( rvWordList ):
            # assert rvWord.isalpha(), f"'{rvWord}'" # Might contain an apostrophe
            if rvWord == simpleNoun:
                rvIndexList.append( rvN )
        if not rvIndexList: continue

        if len(rvIndexList) != 1 or len(lvIndexList) != 1: # then I don't think we can guarantee matching the right words
            return
        assert len(rvIndexList) == len(lvIndexList), f"{BBB} {c}:{v} {simpleNoun=} {rvIndexList=} {lvIndexList=}"

        lvNumbers = []
        for lvN in lvIndexList:
            lvNoun,lvWordNumber,lvWordRow = getLVWordRow( lvWordList[lvN] )
            lvNumbers.append( lvWordNumber )
        assert len(lvNumbers) == 1 # NOT TRUE: If there's two 'camels' in the verse, we expect both to have the same word number
        for rvN in rvIndexList:
            rvNoun = rvWordList[rvN]
            dPrint( 'Info', DEBUGGING_THIS_MODULE, f"matchSimpleWords() is adding a number to RV '{rvNoun}' at {BBB} {c}:{v} {rvN=}")
            addNumberToRVWord( BBB, c,v, rvNoun, lvWordNumber )
# end of connect_OET-RV_words.matchSimpleWords


def getLVWordRow( wordWithNumber:str ) -> Tuple[str,int,List[str]]:
    """
    """
    fnPrint( DEBUGGING_THIS_MODULE, f"getLVWordRow( {wordWithNumber} )" )

    # print( f"{wordWithNumber=}" )
    word,wordNumber = wordWithNumber.split( '¦' )
    # assert word.isalpha(), f"Non-alpha '{word}'" # not true, e.g., from 'Yaʸsous/(Yəhōshūˊa)¦21754'
    try: wordNumber = int( wordNumber )
    except ValueError:
        logging.critical( f"getLVWordRow() got non-number '{wordNumber}' from '{wordWithNumber}'" )
        wordNumber = getLeadingInt( wordNumber )
    assert wordNumber < len( state.wordTable )
    wordRow = state.wordTable[wordNumber].split( '\t' )
    dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"'{word}' {wordRow}" )
    return word,wordNumber,wordRow
# end of connect_OET-RV_words.getLVWordRow


def addNumberToRVWord( BBB:str, c:int,v:int, word:str, wordNumber:int ) -> bool:
    """
    """
    fnPrint( DEBUGGING_THIS_MODULE, f"addNumberToRVWord( {BBB} {c}:{v} '{word}' {wordNumber} )" )

    C = V = None
    found = False
    for n,line in enumerate( state.rvESFMLines[:] ): # iterate through a copy
        try: marker, rest = line.split( ' ', 1 )
        except ValueError: marker, rest = line, '' # Only a marker
        # print( f"{BBB} {C}:{V} {marker}='{rest}'" )
        if marker == '\\c': C = int(rest)
        elif marker == '\\v':
            # print( f"{BBB} {C}:{V} {marker}='{rest}'")
            Vstr, rest = rest.split( ' ', 1 )
            try: V = int(Vstr)
            except ValueError: # might be a range like 21-22
                V = int(Vstr.split('-',1)[0])
            found = C==c and V==v
        if found and f' {word} ' in rest:
            dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"addNumberToRVWord() found {BBB} {C}:{V} {marker}" )
            # assert word in rest, f"No {word=} in {rest=}"
            if rest.count( word ) > 1:
                return False
            assert rest.count( word ) == 1, f"'{word}' {rest.count(word)} '{rest}'"
            if f' {word}¦' not in rest:
                state.rvESFMLines[n] = line.replace( word, f'{word}¦{wordNumber}' )
                dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"  addNumberToRVWord() added ¦{wordNumber} to '{word}' in OET-RV {BBB} {c}:{v}" )
                return True
            else:
                logging.critical( f"addNumberToRVWord() found {BBB} {C}:{V} {marker} found ' {word}¦' already in {rest=}")
                oops
# end of connect_OET-RV_words.addNumberToRVWord


if __name__ == '__main__':
    # Configure basic Bible Organisational System (BOS) set-up
    parser = BibleOrgSysGlobals.setup( PROGRAM_NAME, PROGRAM_VERSION )
    BibleOrgSysGlobals.addStandardOptionsAndProcess( parser, exportAvailable=False )

    main()

    BibleOrgSysGlobals.closedown( PROGRAM_NAME, PROGRAM_VERSION )
# end of connect_OET-RV_words.py
