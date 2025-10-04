#!/usr/bin/env python3
# -\*- coding: utf-8 -\*-
# SPDX-License-Identifier: GPL-3.0-or-later
#
# connect_OET-RV_words_via_OET-LV.py
#
# Script to connect OET-RV words with OET-LV words that have word numbers.
#
# Copyright (C) 2023-2025 Robert Hunt
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
Every word in the OET-LV has a word number tag suffixed to it,
    which connects it back to / aligns it with the Hebrew or Greek word it is translated from.

This script attempts to deduce how some of those same word are translated in the OET-RV
    and automatically connect them with the same word number tag.

It does have the potential to make wrong connections that will need to be manually fixed
        when the rest of the OET-RV words are aligned,
    but hopefully this script is relatively conservative
        so that the number of wrong alignments is not huge.

TODO: This script makes wrong cross-connections between different verses where versification issues apply


CHANGELOG:
    2023-07-31 Added character marker checks for each RV line
    2023-08-29 Added nomina sacra (NS) for connected words in RV
    2023-09-11 Fix bug that connected the wrong (not the same) simple words
    2023-09-12 Fix bug that caused two nested /nd markers (when rerunning after numbers had been deleted)
    2023-09-28 Concatenate consecutive /nd fields
    2023-12-20 Check for unwanted trailing spaces on OET-RV lines
    2024-01-24 Check for doubled punctuation and wrong xref punctuation in OET-RV lines
    2024-01-27 Don't allow section headings to be marked with word numbers
    2024-03-25 Add OT connections
    2025-01-04 Started loading and using SBE name tables for automatic name links (not yet fully implemented for NT)
    2025-01-17 Check for bad copy/paste which might include word numbers from a different verse
    2025-02-20 Added check for /nd inside /add fields (which should never happen)
    2025-02-21 Added check for wrongly ordered combos, e.g., \\add #? instead of \\add ?#
    2025-03-07 Align OET-RV /d fields (in Psalms)
"""
from gettext import gettext as _
from typing import List, Tuple, Optional
from pathlib import Path
from collections import defaultdict
import logging
import re

if __name__ == '__main__':
    import sys
    sys.path.insert( 0, '../../BibleOrgSys/' )
from BibleOrgSys import BibleOrgSysGlobals
from BibleOrgSys.BibleOrgSysGlobals import vPrint, fnPrint, dPrint
from BibleOrgSys.Internals.InternalBibleInternals import getLeadingInt, InternalBibleEntryList
# from BibleOrgSys.Reference.BibleOrganisationalSystems import BibleOrganisationalSystem
from BibleOrgSys.Formats.ESFMBible import ESFMBible

import sys
sys.path.insert( 0, '../../BibleTransliterations/Python/' ) # temp until submitted to PyPI
from BibleTransliterations import load_transliteration_table, transliterate_Hebrew, transliterate_Greek


LAST_MODIFIED_DATE = '2025-10-04' # by RJH
SHORT_PROGRAM_NAME = "connect_OET-RV_words_via_OET-LV"
PROGRAM_NAME = "Connect OET-RV words to OET-LV word numbers"
PROGRAM_VERSION = '0.79'
PROGRAM_NAME_VERSION = '{} v{}'.format( SHORT_PROGRAM_NAME, PROGRAM_VERSION )

DEBUGGING_THIS_MODULE = False


project_folderpath = Path(__file__).parent.parent # Find folders relative to this module
# FG_folderpath = project_folderpath.parent # Path to find parallel Freely-Given.org repos
OET_LV_ESFM_InputFolderPath = project_folderpath.joinpath( 'intermediateTexts/' )
OET_LV_OT_ESFM_InputFolderPath = OET_LV_ESFM_InputFolderPath.joinpath( 'auto_edited_OT_ESFM/' )
OET_LV_NT_ESFM_InputFolderPath = OET_LV_ESFM_InputFolderPath.joinpath( 'auto_edited_VLT_ESFM/' )
OET_RV_ESFM_FolderPath = project_folderpath.joinpath( 'translatedTexts/ReadersVersion/' )
assert OET_LV_OT_ESFM_InputFolderPath.is_dir()
assert OET_LV_NT_ESFM_InputFolderPath.is_dir()
assert OET_RV_ESFM_FolderPath.is_dir()

OT_NameTable_Filepath = Path( 'ScriptedOTUpdates/restoreNames.commandTable.tsv' )
NT_OT_NameTable_Filepath = Path( 'ScriptedVLTUpdates/OTNames.commandTable.tsv' )
NT_NameTable_Filepath = Path( 'ScriptedVLTUpdates/NTNames.commandTable.tsv' )
COMMAND_TABLE_NUM_COLUMNS = 15
COMMAND_HEADER_LINE = 'Tags	IBooks	EBooks	IMarkers	EMarkers	IRefs	ERefs	PreText	SCase	Search	PostText	RCase	Replace	Name	Comment'
assert ' ' not in COMMAND_HEADER_LINE
assert COMMAND_HEADER_LINE.count( '\t' ) == COMMAND_TABLE_NUM_COLUMNS - 1
# class EditCommand(NamedTuple):
#     tags: str           # 0
#     iBooks: list        # 1
#     eBooks: list        # 2
#     iMarkers: list      # 3
#     eMarkers: list      # 4
#     iRefs: list         # 5
#     eRefs: list         # 6
#     preText: str        # 7
#     sCase: str          # 8
#     searchText: str     # 9
#     postText: str       # 10
#     rCase: str          # 11
#     replaceText: str    # 12
#     name: str           # 13
#     comment: str        # 14


SIMPLE_NOUNS = ( # These are nouns that are likely to match one-to-one from the OET-LV to the OET-RV
                #   i.e., there's really no other word for them.
    # NOTE: Some of these nouns can also be verbs -- we may need to remove those???
    # 'son' causes problems
    'ambassadors','ambassador', 'ancestors','ancestor', 'angels','angel', 'anger', 'ankles','ankle',
        'assemblies','assembly',
        'authorities','authority', 'axes','axe',
    'beginnings','beginning', 'belts','belt',
        'birth', 'blood', 'boats','boat', 'bodies','body', 'boys','boy', 'bread', 'branches','branch', 'brothers','brother',
        'bulls','bull', 'burials','burial',
    'camels','camel', 'chairs','chair', 'chambers','chamber', 'chariots','chariot', 'chests','chest', 'children','child',
        'cities','city', 'coats','coat', 'collectors','collector', 'commands','command', 'compassion', 'councils','council', 'courtyards','courtyard', 'courts','court', 'countries','country',
        'craftsmen','craftsman', 'crowds','crowd',
    'danger', 'darkness', 'daughters','daughter', 'days','day',
        'death', 'deceivers','deceiver',
        'donkeys','donkey', 'doors','door', 'doves','dove', 'dreams','dream', 'dyes','dye',
    'ears','ear', 'eyes','eye', 'exorcists','exorcist',
    'faces','face', 'faith', 'farmers','farmer', 'fathers','father',
        'fevers','fever',
        'fields','field', 'figs','fig', 'fingers','finger', 'fires','fire', 'fish', 'foot','feet',
        'followers','follower',
        'friends','friend', 'fruits','fruit',
    'gateways','gateway', 'gates','gate', 'generations','generation', 'gifts','gift', 'girls','girl', 'goats','goat', 'gods','god', 'gold',
        'grace', 'grains','grain', 'grapes','grape', 'greed',
    'handkerchiefs','handkerchief', 'hands','hand', 'happiness', 'hearts','heart', 'heavens','heaven', 'homes','home', 'honey', 'horses','horse', 'hours','hour', 'houses','house', 'husbands','husband',
    'idols','idol', 'ink',
    'jails','jail', 'joy', 'judgements','judgement',
    'kings','king', 'kingdoms','kingdom', 'kisses','kiss',
    'languages','language', 'leaders','leader', 'leather', 'letters','letter', 'life', 'lights','light', 'lions','lion', 'lips','lip', 'loaf','loaves', 'locusts','locust',
    'man','men', 'markets','market', 'masters','master',
        'mercy', 'messages','message', 'meetings','meeting', 'moon', 'mothers','mother', 'mouths','mouth',
    'names','name', 'nations','nation', 'nets','net', 'news', 'noises','noise',
    'officers','officer', 'officials','official',
    'peace', 'pens','pen', 'people','person', 'places','place', 'powers','power', 'prayers','prayer', 'priests','priest', 'prisons','prison', 'promises','promise'
    'rivers','river', 'roads','road', 'robes','robe', 'rocks','rock', 'roofs','roof', 'rooms','room', 'ropes','rope', 'rulers','ruler',
    'sandals','sandal', 'sea',
        'scrolls','scroll',
        'servants','servant', 'services','service', 'shame', 'sheep', 'shepherds','shepherd', 'ships','ship',
        'signs','sign', 'silver', 'silversmiths','silversmith', 'sinners','sinner', 'sins','sin', 'sisters','sister', 'sky', 'slaves','slave',
        'soldiers','soldier', 'sons', 'souls','soul', 'spirits','spirit',
        'stars','star', 'stones','stone', 'streets','street', 'sun', 'swords','sword',
    'tables','table', 'taxes','tax',
        'teachers','teacher', 'temples','temple', 'testimonies','testimony',
        'theatres','theatre', 'things','thing', 'thrones','throne',
        'times','time', 'tombs','tomb', 'tongues','tongue', 'towns','town', 'trees','tree', 'truth',
    'vines','vine', 'visions','vision',
    'waists','waist', 'waters','water', 'ways','way',
        'weeks','week', 'wilderness', 'widows','widow', 'wife','wives', 'windows','window', 'winds','wind', 'woman','women', 'words','word', 'workers','worker',
    'years','year',
    )
assert len(set(SIMPLE_NOUNS)) == len(SIMPLE_NOUNS) # Check for accidental duplicates
verbalNouns = ('confession', 'confidence',
                'deception', 'dedication', 'discussion', 'distribution',
                'fellowship', 'forgiveness', 'fulfilment',
                'immersion', 'repentance')
assert len(set(verbalNouns)) == len(verbalNouns) # Check for accidental duplicates
# Verbs often don't work because we use the tenses differently between OET-RV and OET-LV/Greek
simpleVerbs = ('accepted','accepting','accepts','accept',
                    'answered','answering','answers','answer',
                    'arrested','arresting','arrests','arrest',
                    'asked','asking','asks','ask', 'assembled','assembling','assembles','assemble',
                    'attracted','attracting','attracts','attract', 'attacked','attacking','attacks','attack',
                'become','became','becomes','becoming', 'believed','believing','believes','believe',
                    'brought','bringing','brings','bring',
                    'burnt','burning','burns','burn', 'buried','burying','buries','bury',
                'came','coming','comes','come', 'caught','catching','catches','catch',
                    'chose','choosing','chooses','choose',
                    'confessed','confessing','confesses','confess',
                    'cried','crying','cries','cry',
                'deceived','deceiving','deceives','deceive', 'defended','defending','defends','defend', 'departed','departing','departs','depart',
                    'died','dying','dies','die', 'discussed','discussing','discusses','discuss', 'disowned','disowning','disowns','disown', 'distributed','distributing','distributes','distribute',
                    'drunk','drinking','drinks','drink',
                'ate','eating','eats','eat', 'embraced','embracing','embraces','embrace',
                    'encouraged','encouraging','encourages','encourage', 'ended','ending','ends','end',
                    'existed','existing','exists','exist', 'extended','extending','extends','extend',
                'feared','fearing','fears','fear',
                    'filled','filling','fills','fill',
                    'followed','following','follows','follow', 'forbidding','forbids','forbid', 'forgave','forgiven','forgiving','forgives','forgive',
                'gathered','gathering','gathers','gather', 'gave','giving','gives','give', 'went','going','goes','go', 'greeted','greeting','greets','greet',
                'harvested','harvesting','harvests','harvest', 'hated','hating','hates','hate',
                    'healed','healing','heals','heal', 'helped','helping','helps','help', 'heard','hearing','hears','hear',
                    'honoured','honouring','honours','honour',
                'imitated','imitating','imitates','imitate', 'immersed','immersing','immerses','immerse',
                'judged','judging','judges','judge',
                'kept','keeping','keeps','keep', 'killed','killing','kills','kill', 'knew','known','knowing','knows','know',
                'learnt','learning','learns','learn',
                    'listened','listening','listens','listen', 'lived','living','lives','live', 'looked','looking','looks','look', 'loved','loving','loves','love',
                'magnified','magnifying','magnifies','magnify',
                'obeyed','obeying','obeys','obey',
                'passed','passing','passes','pass', 'persuaded','persuading','persuades','persuade',
                    'practiced','practicing','practices','practice', 'praised','praising','praises','praise', 'promised','promising','promises','promise',
                    'purified','purifying','purifies','purify',
                'raged','raging','rages','rage', 'raised','raising','raises','raise',
                    'received','receiving','receives','receive', 'recognised','recognising','recognises','recognise', 'recovered','recovering','recovers','recover',
                        'released','releasing','releases','release',
                        'remained','remaining','remains','remain', 'reminded','reminding','reminds','remind', 'removed','removing','removes','remove',
                        'reported','reporting','reports','report',
                        'requested','requesting','requests','request',
                        'respected','respecting','respects','respect', 'restrained','restraining','restrains','restrain',
                    'ran','running','runs','run',
                'sailed','sailing','sails','sail', 'said','saying','says','say', 'saved','saving','saves','save',
                    'seated','seating','seats','seat', 'seduced','seducing','seduces','seduce', 'saw','seeing','seen','sees','see', 'sent','sending','sends','send', 'served','serving','serves','serve',
                    'shook','shaken','shaking','shakes','shake', 'shared','sharing','shares','share', 'shone','shining','shines','shine',
                    'sat','sitting','sits','sit',
                    'spoke','spoken','speaking','speaks','speak',
                    'stayed','staying','stays','stay',
                    'summoned','summoning','summons','summon', 'supported','supporting','supports','support',
                'took','taking','takes','take', 'talked','talking','talks','talk',
                    'testified','testifying','testifies','testify',
                    'thought','thinking','thinks','think', 'threw','throwing','throws','throw',
                    'touched','touching','touches','touch',
                    'travelled','travelling','travels','travel', 'turned','turning','turns','turn',
                'united','uniting','unites','unite', 'untied','untying','unties','untie'
                'walked','walking','walks','walk', 'wanted','wanting','wants','want', 'warned','warning','warns','warn', 'watched','watching','watches','watch',
                    'withdrew','withdrawing','withdraws','withdraw', 'withered','withering','withers','wither',
                    'wrote','written','writing','writes','write',
                'yelled','yelling','yells','yell',
                )
assert len(set(simpleVerbs)) == len(simpleVerbs), [x for x in simpleVerbs if simpleVerbs.count(x)>1 ] # Check for accidental duplicates
simpleAdverbs = ('quickly', 'immediately', 'loudly', 'suddenly',)
assert len(set(simpleAdverbs)) == len(simpleAdverbs) # Check for accidental duplicates
simpleAdjectives = ('alive', 'angry', 'bad', 'big', 'bitter',
                    'clean', 'cold',
                    'dangerous', 'dead', 'disobedient', 'entire', 'evil',
                    'female', 'foolish', 'foreign', 'friendly', 'godly', 'good',
                    'happy', 'high',
                    'impossible',
                    'large', 'little', 'local', 'long', 'loud', 'male', 'naked',
                    'obedient', 'opposite', 'possible', 'sad', 'same', 'sick', 'small', 'sudden', 'sweet',
                    'whole', 'wide', 'wounded')
assert len(set(simpleAdjectives)) == len(simpleAdjectives) # Check for accidental duplicates
# Don't use 'one' below because it has other meanings
simpleNumbers = ('two','three','four','five','six','seven','eight','nine',
                    'ten','eleven','twelve','thirteen','fourteen','fifteen','sixteen','seventeen','eighteen','nineteen',
                    'twenty','thirty','forty','fifty','sixty','seventy','eighty','ninety',
                    'none')
assert len(set(simpleNumbers)) == len(simpleNumbers) # Check for accidental duplicates
pronouns = ('he','she','it', 'him','her','its', 'you','we','they', 'your','our','their',
            'himself','herself','itself', 'yourself','yourselves', 'ourselves', 'themselves',
            'everyone')
assert len(set(pronouns)) == len(pronouns) # Check for accidental duplicates
# We don't expect connectors to work very well
connectors = ('and', 'but')
assert len(set(connectors)) == len(connectors) # Check for accidental duplicates
SIMPLE_WORDS = SIMPLE_NOUNS + verbalNouns + simpleVerbs + simpleAdverbs+ simpleAdjectives  + simpleNumbers + pronouns + connectors
# assert len(set(simpleWords)) == len(simpleWords) # Check for accidental duplicates -- but may be overlaps, e.g., love is a verb and a noun


RV_WORDS_FROM_LV_WORD_STRINGS = (
    ('120', 'a hundred twenty'),
    ('Israelis', 'of Yisrāʼēl/Israel'),
    ('wants', 'having an ear'),('understand', 'having an ear'),
    # Greek possessive pronouns usually appear after the head noun
    ('my', 'of me'), ('your', 'of you'), ('his', 'of him'), ('her', 'of her'), ('its', 'of it'), ('our', 'of us'), ('their', 'of them'),
    ('My', 'of me'), ('Your', 'of you'), ('His', 'of him'), ('Her', 'of her'), ('Its', 'of it'), ('Our', 'of us'), ('Their', 'of them'),
    # Contractions
    ("you're", 'you are'),
    # Other word number changes
    ('demons', 'unclean spirits'),('demon', 'unclean spirit'),
    # The following nominal entries handle number changes
    ('hair', 'hairs'),
    # The following verbal entries handle tense changes
    ('bend', 'bent'),
    ('calling', 'called'),
    ('gave', 'given'),
    ('hear', 'hearing'),
    ('prayed', 'praying'),
    ('pleasing', 'acceptable'),
    ('requested', 'requesting'),
    # Vocab differences / synonyms
    ('afraid','feared'),
    ('agreeing','confirming'),
    ('amazed','astonished'),
    ('amazed','marvelling'),
    ('ancestors','fathers'),
    ('announced','proclaiming'), ('announcing','proclaiming'),
    ('Anyone','one'),('anyone','one'),
    ('appeared','seen'),
    ('appropriate','fitting'),
    ('army-commander','hosts'),
    ('arrested','captured'),('arrested','laid'),
    ('astounded','amazed'),
    ('because','for/because'),('Because','For/Because'),('because','For/Because'),
    ('bedding','pallet'),
    ('believers','brothers'),
    ('body','flesh'),
    ('boulders','stones'),
    ('box','ark'),
    ('but','But'),
    ('But','And'),
    ('carrying','carried'),
    ('chasing','pursuing'),
    ('cheerful','joy'),
    ('chest','ark'),
    ('clothes','apparel'),
    ('confused','confounded'),
    ('countries','nations'),('country','nation'),
    ('countryside','field'),
    ('courtyard','court'),
    ('creation','beginning'),
    ('crowd','multitude'),
    ('decide','purposed'),
    ('deformed','withered'),
    # ('demon','unclean'),('demons','spirits'),
    ('demon-possessed','unclean'),
    ('deserted','desolate'),
    ('dinosaur','dragon'), # Rev 12:3
    ('driving','throwing'),
    ('entire','all'),
    ('everyone','people'), ('Everyone','one'),('everyone','one'),
    ('execution','stake'),
    ('existence','became'),
    ('fitting','befitting'),
    ('forgive','forgiving'),
    ('fulfilled','accomplished'),
    ('godly','devout'),
    ('grapevine','vine'),
    ('honour','glorify'),
    ('huge','great'),
    ('instructed','commanded'),
    ('insulting','slandering'),
    ('kill','destroy'),
    ('know','knowledge'),
    ('knowing','known'),
    ('lake','sea'),
    ('languages','tongues'),
    ('left','came out'),
    ('listen','give ear'),('listen','hear'),
    ('Listen','Behold'),('Look','Behold'),
    ('living','dwelling'),
    ('looking','searched'),
    ('looking','seeking'),
    ('loudly','loud'),
    ('lowered','lowering'),
    ('lying','lied'),
    ('mankind','humans'),
    ('mister','master'),('Mister','Master'),
    ('message', 'word'), ('messenger', 'word'),
    ('metres','cubits'),
    ('mind','heart'),
    ('money','reward'),
    ('Mount','mountain'),
    ('necessary','fitting'),
    ('needs','let'),
    ('news','report'),
    ('non-Jews','pagans'),
    ('obey','submitting'),
    ('paralysed','paralytic'),
    ('path','way'),
    ('people','multitude'),
    ('platform','lid'),
    ('poor','humble'),
    ('praised','glorifying'),
    ('preaching','proclaiming'),
    ('pure','holy'), ('purity','holiness'),
    ('quiet','desolate'),
    ('quiet','silenced'),
    ('range','various'),
    ('requested','prayed'),
    ('responded','said'),
    ('rock','stone'),('rocks','stones'),
    ('room','place'),
    ('sacred','holy'),
    ('scared','feared'),
    ('scoffed','mocking'),
    ('See','Behold'),
    ('should','let'),
    ('sick','sickly'),
    ('Similarly','Likewise'),
    ('sitting','reclining'),
    ('skies','heavens'),
    ('small','little'),
    ('So','And'),('So','Therefore'),
    ('songs','psalms'),
    ('spoken','said'),
    ('staying','dwelling'),
    ('strong','forceful'),
    ('talking','speaking'), ('talking','saying'),
    ('tarpaulin','cover'),
    ('taught','teaching'),
    ('teachers','scribes'),
    ('themselves','hearts'),
    ('Then','And'),
    ('thinking','reasoning'),
    ('thinking','supposing'),
    ('undesirables','sinners'),
    ('ungodly','unclean'),
    ('upstairs','upper'),
    ('untarnished','holy'),
    ('urged','implored'),
    ('walk','walking'),
    ('wallet','purse'),
    ('wealthy','rich'),
    ('went','came'),
    ("What's",'What'),
    ('work','service'),
    ('wow','see'),
    ('wrote','written'),
    ('yelled','cried'),
    ('yourselves','hearts'),
    # Capitalisation differences (sometimes just due to a change of word order)
    ('Brothers','brothers'),
    ('Four','four'),
    ('God','god'),
    ('Master','master'),
    ('Messiah','messiah'),('messiah','messiah'),
    ("We've",'We'),
    ('Yahweh','master'),('Yahweh','YHWH'),
    # Names including places (parentheses have already been deleted from the OET-LV at this stage)
    # NOTE: No longer required because we load the TSV source tables themselves (rather than having to duplicate all this info)
    # ('Abijah','Abia'),('Abijah','Abia/ʼAvīāh'),
    # ('Abimelek', 'ʼAⱱīmelek'),
    # ('Abraham','Abraʼam'),('Abraham','Abraʼam/ʼAvrāhām'),
    # ('Abshalom', 'ʼAⱱīshālōm'),
    # ('Adam','Adam'),('Adam','Adam/ʼĀdām'),
    # ('Aharon', 'ʼAhₐron'),
    # ('Aksah', 'ʼAchsah'),
    # ('Amalekites', 'ˊAmālēqites'),
    # ('Aminadab','Aminadab'),('Amon','Aminadab/ˊAmmiynādāⱱ'),
    # ('Amon','Amōs'),('Amon','Amōs/ʼĀmōʦ'),
    # ('Ammonites', 'ˊAmmōn'),
    # ('Aram','Aram'),('Aram','Aram/Rām'),
    # ('Asa','Asaf'),('Asa','Asaf/ʼĀşāf'),
    # ('Babylon', 'Babulōn'),('Babylon', 'Babulōn/Bāvel'),
    # ('Bethany', 'Baʸthania'),
    # ('Bethlehem', 'Baʸthleʼem'),('Bethlehem', 'Baʸthleʼem/Bēyt-leḩem'),
    # ('Beyt', 'Bēyt'),
    # ('Boaz', 'Boʼoz'),('Boaz', 'Boʼoz/Boˊaz'),
    # ('Caesarea', 'Kaisareia'),
    # ('Canaan', 'Kinaˊan'),
    # ('Capernaum', 'Kafarnaʼoum'),
    # ('Cappadocia', 'Kappadokia'),
    # ('Dan', 'Dān'),
    # ('David','Dawid'),('David','Dawid/Dāvid'),('David','Dāvid'),
    # ('Delilah', 'Dilīlāh'),
    # ('Demetrius', 'Daʸmaʸtrios'), ('Diotrephes', 'Diotrefaʸs'),
    # ('Dorcas', 'The_Gazelle/Dorkas'),
    # ('Efraim', 'ʼEfrayim'), # Should be long a
    # ('Egypt','Aiguptos'),('Egypt','Aiguptos/Miʦrayim'),('Egypt', 'Miʦrayim/Egypt'),
    # ('Ephesus', 'Efesos'),
    # ('Esaw', 'ˊĒsāv'),
    # ('Eve','Eua'),('Eve','Eua/Ḩavvāh'),
    # ("Far'oh", 'Farˊoh'),
    # ('Gad', 'Gād'),
    # ('Gaius', 'Gaios'),
    # ('Galilee', 'Galilaia'),('Galilee', 'Galilaia/Gālīl'),
    # ('Gideon', 'Gidˊōn'),('Gideon', 'Jerub-Baˊal'),
    # ('Gilead', 'Gilˊād'),
    # ('Gileadite', 'Gilˊādite'),
    # ('Gilgal', 'Gilgāl'),
    # ('God', 'ʼElohīm'),
    # ("Herod's", 'Haʸrōdaʸs'),('Herod', 'Haʸrōdaʸs'),
    # ('Hezron', 'Hesrōm'),('Hezron', 'Hesrōm/Ḩeʦrōn'),
    # ('Idumea', 'Idoumaia'),
    # ('Immanuel', 'Emmanouaʸl'),('Immanuel', 'Emmanouaʸl/ˊImmānūʼēl'),
    # ('Isaac', 'Isaʼak'),('Isaac', 'Isaʼak/Yiʦḩāq'),
    # ('Isayah', 'Aʸsaias'),('Isayah', 'Aʸsaias/Yəshaˊyāh'),
    # ('Israel', 'Yisrāʼēl/Israel'),('Israel', 'Yisrāʼēl'),
    # ('Issachar', 'Yissākār'),
    # ('Iyyov', 'ʼIuōv'),
    # ('Yacob', 'Yakōbos'),('Yacob', 'Yakōbos/Yaˊₐqoⱱ'), ('Yacob', 'Yakōb'),('Yacob', 'Yakōb/Yaˊₐqoⱱ'),("Yacob's", 'Yakōb'),("Yacob's", 'Yakōb/Yaˊₐqoⱱ'),
    # ('Yarobam', 'Yārāⱱəˊām'),('Yarobam', 'Yārāⱱəˊām/Jeroboam'),
    # ('Yehoshapat', 'Yōsafat'),('Yehoshapat', 'Yōsafat/Yəhōshāfāţ'),
    # ('Yerusalem', 'Hierousalaʸm'),('Yerusalem', 'Hierousalaʸm/Yərūshālayim'),
    # ('Yiftah', 'Yiftāḩ'),
    # ('Jesse', 'Yessai'),('Jesse', 'Yessai/Yishay'),
    # ('Jew', 'Youdaios'),
    # ('Jews', 'Youdaiōns'),
    # ('Josiah', 'Yōsias'),('Josiah', 'Yōsias/Yʼoshiyyāh'),
    # ('Judah', 'Youda'),('Judah', 'Youda/Yəhūdāh'),
    # ('Judas', 'Youdas'),
    # ('Justus', 'Youstos'),
    # ('Lazarus', 'Lazaros'),
    # ('Lebanon', 'Ləⱱānōn'),
    # ('Levi', 'Leui'),('Levi', 'Leui/Lēvī'),('Levi','Lēvīh'),
    # ('Lydda', 'Ludda'),('Lydda', 'Ludda/Lod'),
    # ('Macedonia', 'Makedonia'),
    # ('Manasseh', 'Manassaʸs'),('Manasseh', 'Manassaʸs/Mənashsheh'),('Menashsheh', 'Mənashsheh'),
    # ('Manoah', 'Mānōaḩ'),('Manoah’s', 'Mānōaḩ'),
    # ('Maria', 'Maria'),('Maria', 'Maria/Miryām'),
    # ('Media', 'Maʸdia'),
    # ('Micah', 'Mīkāhū'),('Micah', 'Mīkāh'),
    # ('Midian', 'Midyān'),
    # ('Mitsrayim', 'Miʦrayim/Egypt'),
    ('Mt', 'Mount'),
    # ('Nahshon', 'Naʼassōn'),('Nahshon', 'Naʼassōn/Naḩshōn'),
    # ('Nazareth', 'Nazaret'),
    # ('Obed', 'Yōbaʸd'),('Obed', 'Yōbaʸd/Ōbaʸd/ˊŌvēd'),
    # ('Paul', 'Paulos'),
    # ('Perez', 'Fares'),('Perez', 'Fares/Fereʦ'),
    # ('Pharisee', 'Farisaios'),
    # ('Philadelphia', 'Filadelfeia'),
    # ('Philistines', 'Fəlishəttiy'),
    # ('Pontus', 'Pontos'),
    # ('Potifar', 'Fōţīfar'),
    # ('Reuben', 'Rəʼūⱱēn'),
    # ('Rehoboam', 'Ɽoboam'),('Rehoboam', 'Ɽoboam/Rəḩavəˊām'),
    # ('Ruth', 'Ɽouth'),('Ruth', 'Ɽouth/Rūt'),
    # ('Sadducees', 'Saddoukaios'),
    # ('Salmon', 'Salmōn'),('Salmon', 'Salmōn/Salmōn'),
    # ('Samaria', 'Samareia'),('Samaria', 'Samareia/Shomrōn'),
    # ('Sapphira', 'Sapfeiraʸ'),
    # ('Sardis', 'Sardeis'),
    # ('Sha\'ul', 'Shāʼūl'), ('Saul', 'Saulos'),
    # ('Shekem', 'Shəkem'),
    # ('Shimshon', 'Shimshōn'),
    # ('Sidon', 'Sidōn'),('Sidon', 'Sidōn/Tsīdōn'),
    # ('Silas', 'Silouanos'),
    # ('Simeon', 'Shimˊōn'),
    # ('Simon', 'Simōn'),
    # ('Smyrna', 'Smurna'),
    # ('Solomon', 'Solomōn'),('Solomon', 'Solomōn/Shəlomih'),('Solomon', 'Shəlomoh'),
    # ('Tabitha', 'Tabaʸtha'),
    # ('Tamar', 'Thamar'),('Tamar', 'Thamar/Tāmār'),
    # ('Tarsus', 'Tarsos'),
    # ('Theophilus', 'Theofilos'),
    # ('Thessalonica', 'Thessalonikaʸ'),
    # ('Thyatira', 'Thuateira'),
    # ('Timothy', 'Timotheos'),
    # ('Tola', 'Tōlāˊ'),
    # ('Tsiklag', 'Ziklag'),('Tsiklag', 'Tsiqlag/Ziklag'),
    # ('Tyre', 'Turos'),('Tyre', 'Turos/Tsor'),
    # ('Uzziah', 'Ozias'),('Uzziah', 'Ozias/ˊUzziyyāh'),
    # ('Yacob', 'Yaˊaqov'),
    # ('Yehudah', 'Yəhūdāh'),
    # ('Yericho', 'Yərīḩō'),
    # ('Yeshua', 'Yaʸsous'),('Yeshua', 'Yaʸsous/Yəhōshūˊa'), ("Yeshua's", 'Yaʸsous'),("Yeshua's", 'Yaʸsous/Yəhōshūˊa'),
    # ('Yito', 'Yitrō'),
    # ('Yoav', 'Yōʼāⱱ'),('Yoav', 'Yōʼāⱱ/Joab'),
    # ('Yohan', 'Yōannaʸs'),
    # ('Yoppa', 'Yoppaʸ'),
    # ('Yordan', 'Yardēn'),('Yordan', 'Yordanaʸs'),('Yordan', 'Yordanaʸs/Yardēn'),
    # ('Yosef', 'Yōsaʸf'),('Yosef', 'Yōsaʸf/Yōşēf'),('Yosef', 'Yōşēf'),
    # ('Yudea', 'Youdaia'),
    # ("Zebedee's", 'Zebedaios'),
    # ('Zerah', 'Zara'),('Zerah', 'Zara/Zeraḩ'),
    ("aren't",'not'),("can't",'not'),("didn't",'not'),("don't",'not'),("isn't",'not'),("shouldn't",'not'),("won't",'not'),
    )



class WordNumberError(ValueError):
    pass


class State:
    """
    A place to store some of the global stuff that needs to be passed around.
    """
# end of State class

state = State()


# forList = []
def main():
    """
    Main program to handle command line parameters and then run what they want.
    """
    BibleOrgSysGlobals.introduceProgram( __name__, PROGRAM_NAME_VERSION, LAST_MODIFIED_DATE )

    # global genericBookList
    # genericBibleOrganisationalSystem = BibleOrganisationalSystem( 'GENERIC-KJV-ENG' )
    # genericBookList = genericBibleOrganisationalSystem.getBookList()

    # Load the OET-RV
    rv = ESFMBible( OET_RV_ESFM_FolderPath, givenAbbreviation='OET-RV' )
    rv.loadAuxilliaryFiles = True
    rv.loadBooks() # So we can iterate through them all later
    rv.lookForAuxilliaryFilenames()
    dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"{rv=}")

    # Load the OET-LV OT
    lvOT = ESFMBible( OET_LV_OT_ESFM_InputFolderPath, givenAbbreviation='OET-LV' )
    lvOT.loadAuxilliaryFiles = True
    lvOT.loadBooks() # So we can iterate through them all later
    lvOT.lookForAuxilliaryFilenames()
    dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"{lvOT=}")

    # Load the OET-LV NT
    lvNT = ESFMBible( OET_LV_NT_ESFM_InputFolderPath, givenAbbreviation='OET-LV' )
    lvNT.loadAuxilliaryFiles = True
    lvNT.loadBooks() # So we can iterate through them all later
    lvNT.lookForAuxilliaryFilenames()
    dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"{lvNT=}")

    # Load the Hebrew and Greek name tables from TSV files
    load_transliteration_table( 'Hebrew' )
    load_transliteration_table( 'Greek' )
    loadHebGrkNameTables()
    dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"{state.nameTables=}")

    # Display anywhere where we still have 'for' that should perhaps be 'because'
    # show_fors( lv )

    # Connect linked words in the OET-LV to the OET-RV
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"\nProcessing connect words for OET OT…" )
    connect_OET_RV( rv, lvOT, OET_LV_OT_ESFM_InputFolderPath ) # OT
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"\nProcessing connect words for OET NT…" )
    connect_OET_RV( rv, lvNT, OET_LV_NT_ESFM_InputFolderPath ) # NT

    # Delete any saved (but now obsolete) OBD Bible pickle files
    for something in OET_RV_ESFM_FolderPath.iterdir():
        if something.name.endswith( '.OBD_Bible.pickle' ):
            vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"Deleting obsolete OBD Bible pickle file {something.name}…" )
            something.unlink()
# end of connect_OET-RV_words_via_OET-LV.main


NAME_ADJUSTMENT_TABLE = { # Where we change too far from the accepted KJB word
    'Menashsheh':'Manasseh',
    'Shomron':'Samaria',
    'Yudah':'Yehudah',
    }
def loadHebGrkNameTables():
    """
    Loads three TSV files into state.nameTables

    These are the ScriptedBibleEditor command files that create the Hebrew and Greek proper names for the OET-LV.
    """
    state.nameTables = {}

    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  Loading OT names from {OT_NameTable_Filepath}…" )
    state.nameTables['OT'] = defaultdict( set )
    with open( OT_NameTable_Filepath, 'rt', encoding='utf-8' ) as commandTableFile:
        line_number = 0
        for line in commandTableFile:
            line_number += 1
            line = line.rstrip( '\r\n' )
            if not line or line.startswith( '#' ): continue
            tab_count = line.count( '\t' )
            if tab_count>9 and tab_count < (COMMAND_TABLE_NUM_COLUMNS - 1): # Some editors delete trailing columns
                line += '\t' * (COMMAND_TABLE_NUM_COLUMNS - 1 - tab_count) # Add back the empty columns
                tab_count = line.count( '\t' )
            if tab_count != (COMMAND_TABLE_NUM_COLUMNS - 1):
                logging.critical( f"Skipping line {line_number} which contains {tab_count} tabs (instead of {COMMAND_TABLE_NUM_COLUMNS - 1})" )
            if line == COMMAND_HEADER_LINE:
                continue # as no need to save this

            # Get the fields and check some of them
            fields = line.split( '\t' ) # 0:Tags 1:IBooks 2:EBooks 3:IMarkers 4:EMarkers 5:IRefs 6:ERefs 7:PreText 8:SCase 9:Search 10:PostText 11:RCase 12:Replace 13:Name 14:Comment
            tags, searchText, replaceText = fields[0], fields[9], fields[12]
            # print( f"{searchText=} {replaceText=}")
            if 'H' in tags:
                if searchText.startswith( 'J' ): searchText = f'Y{searchText[1:]}' # Replace first letter J with Y
                try: searchText = NAME_ADJUSTMENT_TABLE[searchText] # Do transforms
                except KeyError: pass

                # newReplaceText = transliterate_Hebrew( replaceText, capitaliseHebrew=searchText[0].isupper() )
                # if newReplaceText != replaceText:
                #     # print(f" Converted Hebrew '{replaceText}' to '{newReplaceText}'")
                #     replaceText = newReplaceText
                replaceText = transliterate_Hebrew( replaceText, capitaliseHebrew=searchText[0].isupper() )
                    # NOTE: The below makes it WORSE
                    # # We replace out the special characters (from our transliteration function)
                    # .replace( 'Ā', 'A' ).replace( 'Ē', 'E' )
                    # .replace( 'Ḩ', 'H' )
                    # .replace( 'ₐ', 'a' ).replace( 'ə', 'e' )
                    # .replace( 'ā', 'a' ).replace( 'ē', 'e' ).replace( 'ī', 'i' ).replace( 'ō', 'o' ).replace( 'ū', 'u' )
                    # .replace( 'ḩ', 'h' ).replace( 'ⱪ', 'k' ).replace( 'q', 'k' ).replace( 'ʦ', 'ts' ).replace( 'ⱱ', 'v' )
                    # )
                if '/' in replaceText:
                    assert 'd' in tags, f"OT {tags=} {searchText=} {replaceText=}"
                    replaceText = replaceText.replace( '(', '' ).replace( ')', '' ) # We don't want the brackets
                    shortenedReplaceText = replaceText.split( '/' )[0]
                    # assert shortenedReplaceText not in state.nameTables['OT'], f"{tags=} {searchText=} {replaceText=} {shortenedReplaceText=}"
                    state.nameTables['OT'][shortenedReplaceText].add( searchText ) # We add an extra entry
                    if searchText.endswith( 'iah' ): # e.g. Azariah
                        state.nameTables['OT'][shortenedReplaceText].add( f'{searchText[:-3]}yah' ) # We add an extra entry
                    elif searchText.endswith( 'ieh' ):
                        state.nameTables['OT'][shortenedReplaceText].add( f'{searchText[:-3]}yeh' ) # We add an extra entry
                    if 'j' in searchText and 'j' not in replaceText: # e.g., Benjamin
                        state.nameTables['OT'][shortenedReplaceText].add( searchText.replace( 'j', 'y' ) ) # We add an extra entry
                    if 'ph' in searchText and 'ph' not in replaceText: # e.g., Naphtali
                        state.nameTables['OT'][shortenedReplaceText].add( searchText.replace( 'ph', 'f' ) ) # We add an extra entry
                    if 'sh' in replaceText and 'sh' not in searchText and 's' in searchText: # e.g., Yerushalem
                        # assert 's' in searchText, f"{searchText=} {replaceText=}"
                        state.nameTables['OT'][shortenedReplaceText].add( searchText.replace( 's', 'sh' ) ) # We add an extra entry
                    if 'th' in searchText and 'th' not in replaceText: # e.g., Yotham
                        state.nameTables['OT'][shortenedReplaceText].add( searchText.replace( 'th', 't' ) ) # We add an extra entry
                    if 'v' in replaceText and 'v' not in searchText and 'b' in searchText: # e.g., Argob
                        state.nameTables['OT'][shortenedReplaceText].add( searchText.replace( 'b', 'v' ) ) # We add an extra entry
                    if 'z' in searchText and 'ts' in replaceText: # e.g., Hatzor
                        state.nameTables['OT'][shortenedReplaceText].add( searchText.replace( 'z', 'ts' ) ) # We add an extra entry
                    if searchText.startswith('Z') and replaceText.startswith('Ts'): # e.g., Ziklag
                        state.nameTables['OT'][shortenedReplaceText].add( f'Ts{searchText[1:]}' ) # We add an extra entry
                # assert replaceText not in state.nameTables['OT'], f"{tags=} {searchText=} {replaceText=}"
                state.nameTables['OT'][replaceText].add( searchText )
                if searchText.endswith( 'iah' ):
                    state.nameTables['OT'][replaceText].add( f'{searchText[:-3]}yah' ) # We add an extra entry
                elif searchText.endswith( 'ieh' ):
                    state.nameTables['OT'][replaceText].add( f'{searchText[:-3]}yeh' ) # We add an extra entry
                if 'j' in searchText: # e.g., Benjamin
                    state.nameTables['OT'][replaceText].add( searchText.replace( 'j', 'y' ) ) # We add an extra entry
                if 'ph' in searchText: # e.g., Naphtali
                    state.nameTables['OT'][replaceText].add( searchText.replace( 'ph', 'f' ) ) # We add an extra entry
                if 'sh' in replaceText and 'sh' not in searchText and 's' in searchText: # e.g., Yerushalem
                    # assert 's' in searchText, f"{searchText=} {replaceText=}"
                    state.nameTables['OT'][replaceText].add( searchText.replace( 's', 'sh' ) ) # We add an extra entry
                if 'th' in searchText and 'th' not in replaceText: # e.g., Yotham
                    state.nameTables['OT'][replaceText].add( searchText.replace( 'th', 't' ) ) # We add an extra entry
                if 'v' in replaceText and 'v' not in searchText and 'b' in searchText: # e.g., Argob
                    state.nameTables['OT'][replaceText].add( searchText.replace( 'b', 'v' ) ) # We add an extra entry
                if 'z' in searchText and 'ts' in replaceText: # e.g., Hatzor
                    state.nameTables['OT'][replaceText].add( searchText.replace( 'z', 'ts' ) ) # We add an extra entry
                if searchText.startswith('Z') and replaceText.startswith('Ts'): # e.g., Ziklag
                    state.nameTables['OT'][replaceText].add( f'Ts{searchText[1:]}' ) # We add an extra entry
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"    Loaded {len(state.nameTables['OT']):,} OT names." )
    # print( f"{state.nameTables['OT']['Mənaḩēm']=}" ); halt

    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  Loading NT OT names from {NT_OT_NameTable_Filepath}…" )
    state.nameTables['NT_OT'] = defaultdict( set )
    with open( NT_OT_NameTable_Filepath, 'rt', encoding='utf-8' ) as commandTableFile:
        line_number = 0
        for line in commandTableFile:
            line_number += 1
            line = line.rstrip( '\r\n' )
            if not line or line.startswith( '#' ): continue
            tab_count = line.count( '\t' )
            if tab_count>9 and tab_count < (COMMAND_TABLE_NUM_COLUMNS - 1): # Some editors delete trailing columns
                line += '\t' * (COMMAND_TABLE_NUM_COLUMNS - 1 - tab_count) # Add back the empty columns
                tab_count = line.count( '\t' )
            if tab_count != (COMMAND_TABLE_NUM_COLUMNS - 1):
                logging.critical( f"Skipping line {line_number} which contains {tab_count} tabs (instead of {COMMAND_TABLE_NUM_COLUMNS - 1})" )
            if line == COMMAND_HEADER_LINE:
                continue # as no need to save this

            # Get the fields and check some of them
            fields = line.split( '\t' ) # 0:Tags 1:IBooks 2:EBooks 3:IMarkers 4:EMarkers 5:IRefs 6:ERefs 7:PreText 8:SCase 9:Search 10:PostText 11:RCase 12:Replace 13:Name 14:Comment
            tags, searchText, replaceText = fields[0], fields[9], fields[12]
            # print( f"{searchText=} {replaceText=}")
            if 'HG' in tags:
                if searchText.startswith( 'J' ): searchText = f'Y{searchText[1:]}' # Replace first letter J with Y
                newReplaceText = transliterate_Greek( transliterate_Hebrew( replaceText, capitaliseHebrew=searchText[0].isupper() ) )
                if newReplaceText != replaceText:
                    # print(f" Converted Hebrew/Greek '{replaceText}' to '{newReplaceText}'")
                    replaceText = newReplaceText
                if '/' in replaceText:
                    assert 'd' in tags, f"OT_NT {tags=} {searchText=} {replaceText=}"
                    replaceText = replaceText.replace( '(', '' ).replace( ')', '' ) # We don't want the brackets
                    shortenedReplaceText = replaceText.split( '/' )[0]
                    # assert shortenedReplaceText not in state.nameTables['NT_OT'], f"{tags=} {searchText=} {replaceText=} {shortenedReplaceText=}"
                    state.nameTables['NT_OT'][shortenedReplaceText].add ( searchText ) # We add an extra entry
                # assert replaceText not in state.nameTables['NT_OT'], f"{tags=} {searchText=} {replaceText=}"
                state.nameTables['NT_OT'][replaceText].add( searchText )
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"    Loaded {len(state.nameTables['NT_OT']):,} NT OT names." )

    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  Loading NT names from {NT_NameTable_Filepath}…" )
    state.nameTables['NT'] = defaultdict( set )
    with open( NT_NameTable_Filepath, 'rt', encoding='utf-8' ) as commandTableFile:
        line_number = 0
        for line in commandTableFile:
            line_number += 1
            line = line.rstrip( '\r\n' )
            if not line or line.startswith( '#' ): continue
            tab_count = line.count( '\t' )
            if tab_count>9 and tab_count < (COMMAND_TABLE_NUM_COLUMNS - 1): # Some editors delete trailing columns
                line += '\t' * (COMMAND_TABLE_NUM_COLUMNS - 1 - tab_count) # Add back the empty columns
                tab_count = line.count( '\t' )
            if tab_count != (COMMAND_TABLE_NUM_COLUMNS - 1):
                logging.critical( f"Skipping line {line_number} which contains {tab_count} tabs (instead of {COMMAND_TABLE_NUM_COLUMNS - 1})" )
            if line == COMMAND_HEADER_LINE:
                continue # as no need to save this

            # Get the fields and check some of them
            fields = line.split( '\t' ) # 0:Tags 1:IBooks 2:EBooks 3:IMarkers 4:EMarkers 5:IRefs 6:ERefs 7:PreText 8:SCase 9:Search 10:PostText 11:RCase 12:Replace 13:Name 14:Comment
            tags, searchText, replaceText = fields[0], fields[9], fields[12]
            # print( f"{searchText=} {replaceText=}")
            if 'G' in tags:
                if searchText.startswith( 'J' ): searchText = f'Y{searchText[1:]}' # Replace first letter J with Y
                newReplaceText = transliterate_Greek( replaceText )
                if newReplaceText != replaceText:
                    # print(f" Converted Greek '{replaceText}' to '{newReplaceText}'")
                    replaceText = newReplaceText
                if '/' in replaceText:
                    assert 'd' in tags, f"NT {tags=} {searchText=} {replaceText=}"
                    replaceText = replaceText.replace( '(', '' ).replace( ')', '' ) # We don't want the brackets
                    shortenedReplaceText = replaceText.split( '/' )[0]
                    # assert shortenedReplaceText not in state.nameTables['NT'], f"{tags=} {searchText=} {replaceText=} {shortenedReplaceText=}"
                    state.nameTables['NT'][shortenedReplaceText].add( searchText ) # We add an extra entry
                # assert replaceText not in state.nameTables['NT'], f"{tags=} {searchText=} {replaceText=}"
                state.nameTables['NT'][replaceText].add( searchText )
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"    Loaded {len(state.nameTables['NT']):,} NT names." )
# end of connect_OET-RV_words_via_OET-LV.loadHebGrkNameTables


illegalWordLinkRegex1 = re.compile( '[0-9]¦' ) # Has digits BEFORE the broken pipe
illegalWordLinkRegex2 = re.compile( '¦[1-9][0-9]{0,5}[a-z]' ) # Has letters immediately AFTER the wordlink number
doubledND, badAddND, badNDAdd = '\\nd \\nd ', '\\add \\nd ', '\\nd*\\add*'
def connect_OET_RV( rv, lv, OET_LV_ESFM_InputFolderPath ):
    """
    Firstly, load the OET-LV wordtable.
        Loads into state.wordTableHeaderList and state.wordTable.

    Check that any existing word numbers are in the correct verse.

    Then connect linked words in the OET-LV to the OET-RV.
    """
    fnPrint( DEBUGGING_THIS_MODULE, f"connect_OET_RV( {rv}, {lv} )" )

    # Go through books chapters and verses
    totalSimpleListedAdds = totalProperNounAdds = totalFirstPartMatchedAdds = totalManualMatchedAdds = 0
    totalSimpleListedAddsNS = totalProperNounAddsNS = totalFirstPartMatchedAddsNS = totalManualMatchedAddsNS = 0 # Nomina sacra
    for BBB,lvBookObject in lv.books.items():
        if BBB not in ('CH1','PRO',): continue
        vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Processing connect words for OET {BBB}…" )

        bookSimpleListedAdds = bookProperNounAdds = bookFirstPartMatchedAdds = bookManualMatchedAdds = 0
        bookSimpleListedAddsNS = bookProperNounAddsNS = bookFirstPartMatchedAddsNS = bookManualMatchedAddsNS = 0 # Nomina sacra
        wordFileName = lvBookObject.ESFMWordTableFilename
        if wordFileName:
            assert wordFileName.endswith( '.tsv' )
            vPrint( 'Info', DEBUGGING_THIS_MODULE, f"  Found ESFMBible filename '{wordFileName}' for {lv.abbreviation} {BBB}" )
            if lv.ESFMWordTables[wordFileName]:
                vPrint( 'Info', DEBUGGING_THIS_MODULE, f"  Found ESFMBible loaded '{wordFileName}' word link lines: {len(lv.ESFMWordTables[wordFileName]):,}" )
            else:
                vPrint( 'Info', DEBUGGING_THIS_MODULE, f"  No word links loaded yet for '{wordFileName}'" )
            if lv.ESFMWordTables[wordFileName] is None:
                with open( OET_LV_ESFM_InputFolderPath.joinpath(wordFileName), 'rt', encoding='UTF-8' ) as wordFile:
                    lv.ESFMWordTables[wordFileName] = wordFile.read().split( '\n' )
                vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  connect_OET_RV loaded {len(lv.ESFMWordTables[wordFileName]):,} total rows from {wordFileName}" )
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  connect_OET_RV loaded column names were: ({len(lv.ESFMWordTables[wordFileName][0])}) {lv.ESFMWordTables[wordFileName][0]}" )
        state.wordTable = [row.split('\t') for row in lv.ESFMWordTables[wordFileName]]
        state.wordTableHeaderList = state.wordTable[0]

        lvESFMFilename = f'OET-LV_{BBB}.ESFM'
        lvESFMFilepath = OET_LV_ESFM_InputFolderPath.joinpath( lvESFMFilename )
        with open( lvESFMFilepath, 'rt', encoding='UTF-8' ) as esfmFile:
            state.lvESFMText = esfmFile.read() # We keep the original (for later comparison)
            state.lvESFMLines = state.lvESFMText.split( '\n' )
            # Do some basic checking (better to find common editing errors sooner rather than later)
            for lineNumber,line in enumerate( state.lvESFMLines, start=1 ):
                # assert not line.endswith(' '), f"Unexpected space at end in {lvESFMFilename} {lineNumber}: '{line}'"
                if line.endswith(' '):
                    logging.warning( f"Unexpected space at end in {lvESFMFilename} {lineNumber}: '{line}'" )
                for characterMarker in BibleOrgSysGlobals.USFMCharacterMarkers:
                    assert line.count( f'\\{characterMarker} ') == line.count( f'\\{characterMarker}*'), f"{characterMarker} marker mismatch in {lvESFMFilename} {lineNumber}: '{line}'"
                assert doubledND not in line, f"Double \\nd in {lvESFMFilename} {lineNumber}: '{line}'"
                assert  badAddND not in line, f"\\nd inside \\add start {lvESFMFilename} {lineNumber}: '{line}'"
                assert  badNDAdd not in line, f"\\nd inside \\add end {lvESFMFilename} {lineNumber}: '{line}'"
                if '\\x* ' in line: # this can be ok if the xref directly follows other text
                    logger = logging.critical if ' \\x ' in line else logging.warning
                    logger( f"Double-check space after xref in {lvESFMFilename} {lineNumber}: '{line}'" )

        rvESFMFilename = f'OET-RV_{BBB}.ESFM'
        rvESFMFilepath = OET_RV_ESFM_FolderPath.joinpath( rvESFMFilename )
        with open( rvESFMFilepath, 'rt', encoding='UTF-8' ) as esfmFile:
            state.rvESFMText = esfmFile.read() # We keep the original (for later comparison)
            state.rvESFMLines = state.rvESFMText.split( '\n' )
            # Do some basic checking (better to find common editing errors sooner rather than later)
            for lineNumber,line in enumerate( state.rvESFMLines, start=1 ):
                assert not line.startswith(' '), f"Unexpected space at start in {rvESFMFilename} {lineNumber}: '{line}'"
                assert not line.endswith(' '), f"Unexpected space at end in {rvESFMFilename} {lineNumber}: '{line}'"
                assert '  ' not in line, f"Unexpected doubled spaces in {rvESFMFilename} {lineNumber}: '{line}'"
                assert ',,' not in line and '..' not in line, f"Unexpected doubled punctuation in {rvESFMFilename} {lineNumber}: '{line}'"
                assert '\\x*,' not in line and '\\x*.' not in line, f"Bad xref formatting in {rvESFMFilename} {lineNumber}: '{line}'"
                if line.count(' \\x ') < line.count('\\x '):
                    assert '\\x* ' in line or line.endswith('\\x*') or '\\x*—' in line, f"Missing xref space in {rvESFMFilename} {lineNumber}: '{line}'"
                assert '“ ' not in line, f"Unexpected space at beginning of speech in {rvESFMFilename} {lineNumber}: '{line}'"
                assert '’“' not in line, f"Unexpected consecutive speech marks in {rvESFMFilename} {lineNumber}: '{line}'"
                assert '“’' not in line, f"Unexpected consecutive speech marks in {rvESFMFilename} {lineNumber}: '{line}'"
                if '’ ”' not in line and '’\\wj* ”' not in line:
                    assert ' ”' not in line, f"Unexpected space at end of speech in {rvESFMFilename} {lineNumber}: '{line}'"
                assert '≈ ' not in line, f"Unexpected space after ≈ in {rvESFMFilename} {lineNumber}: '{line}'"
                for characterMarker in BibleOrgSysGlobals.USFMCharacterMarkers:
                    assert line.count( f'\\{characterMarker} ') == line.count( f'\\{characterMarker}*'), f"{characterMarker} marker mismatch in {rvESFMFilename} {lineNumber}: '{line}'"
                assert doubledND not in line, f"Double \\nd in {rvESFMFilename} {lineNumber}: '{line}'"
                assert  badAddND not in line, f"\\nd inside \\add start {rvESFMFilename} {lineNumber}: '{line}'"
                assert  badNDAdd not in line, f"\\nd inside \\add end {rvESFMFilename} {lineNumber}: '{line}'"
                if '\\x* ' in line: # this can be ok if the xref directly follows other text
                    logger = logging.critical if ' \\x ' in line else logging.warning
                    logger( f"Double-check space after xref in {rvESFMFilename} {lineNumber}: '{line}'" )

        numChapters = lv.getNumChapters( BBB )
        if numChapters >= 1:
            for c in range( 1, numChapters+1 ):
                C = str(c)
                vPrint( 'Info', DEBUGGING_THIS_MODULE, f"      Connecting words for {BBB} {C}…" )
                numVerses = lv.getNumVerses( BBB, c )
                if numVerses is None: # something unusual
                    logging.critical( f"connect_OET_RV: no verses found for OET-LV {BBB} {C}" )
                    continue
                havePsalmTitles = BibleOrgSysGlobals.loadedBibleBooksCodes.hasPsalmTitle( BBB, C )
                for v in range( 1, numVerses+1 ): # Note: some Psalms have an extra verse in OET-LV (because /d is v1)
                    V = str(v)
                    try:
                        rvVerseEntryList, _rvCcontextList = rv.getContextVerseData( (BBB, C, str(v-1) if havePsalmTitles and v>1 else V) )
                    except KeyError:
                        logging.critical( f"Seems we have no OET-RV {BBB} {c}:{v} -- versification issue?" )
                        continue
                    # OET-RV has /d and v1 all inside v1, but we need to separate them out to match OET-LV correctly
                    if havePsalmTitles and v in (1,2):
                        adjustedRvVerseEntryList = InternalBibleEntryList()
                        for rvEntry in rvVerseEntryList:
                            rvMarker = rvEntry.getMarker()
                            if v==1 and rvMarker in ('v~','p~'): continue # don't want these
                            if v==2 and rvMarker == 'd': continue # don't want this
                            adjustedRvVerseEntryList.append( rvEntry )
                        rvVerseEntryList = adjustedRvVerseEntryList
                    try:
                        lvVerseEntryList, _lvCcontextList = lv.getContextVerseData( (BBB, C, V) )
                    except KeyError:
                        logging.critical( f"Seems we have no OET-LV {BBB} {c}:{v} -- versification issue?" )
                        halt
                        continue
                    # if BBB=='PSA' and v<3: # and c in (3,23,29)
                    #     dPrint( 'Normal', DEBUGGING_THIS_MODULE, f"\nRV entries for {BBB} {C}:{V}: ({len(rvVerseEntryList)}) {rvVerseEntryList}")
                    #     dPrint( 'Normal', DEBUGGING_THIS_MODULE, f"LV entries for {BBB} {C}:{V}: ({len(lvVerseEntryList)}) {lvVerseEntryList}")

                    check_OET_RV_Verse( BBB, c, v, rvVerseEntryList, lvVerseEntryList ) # Check that any existing word numbers are in the expected range

                    (numSimpleListedAdds,numSimpleListedAddsNS), (numProperNounAdds,numProperNounAddsNS), (numFirstPartMatchedAdds,numFirstPartMatchedAddsNS), (numManualMatchedAdds,numManualMatchedAddsNS) \
                                = connect_OET_RV_Verse( BBB, c, v, rvVerseEntryList, lvVerseEntryList ) # updates state.rvESFMLines
                    bookSimpleListedAdds += numSimpleListedAdds
                    bookSimpleListedAddsNS += numSimpleListedAddsNS
                    bookProperNounAdds += numProperNounAdds
                    bookProperNounAddsNS += numProperNounAddsNS
                    bookFirstPartMatchedAdds += numFirstPartMatchedAdds
                    bookFirstPartMatchedAddsNS += numFirstPartMatchedAddsNS
                    bookManualMatchedAdds += numManualMatchedAdds
                    bookManualMatchedAddsNS += numManualMatchedAddsNS
        else:
            dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"connect_OET_RV {BBB} has {numChapters} chapters!!!" )
            assert BBB in ('INT','FRT',)

        newESFMtext = '\n'.join( state.rvESFMLines ) \
                          .replace( '\\nd* \\nd ', ' ' ) # Concatenate consecutive nd fields
        if newESFMtext != state.rvESFMText:
            dPrint( 'Info', DEBUGGING_THIS_MODULE, f"{BBB} ESFM text has changed {len(state.rvESFMText):,} chars -> {len(newESFMtext):,} chars" )
            if BBB=='ACT': newESFMtext = newESFMtext.replace( ' 120¦', ' 12Z¦' ) # Avoid false alarm
            illegalWordLinkRegex1Match = illegalWordLinkRegex1.search( newESFMtext)
            assert not illegalWordLinkRegex1Match, f"illegalWordLinkRegex1 failed before saving {BBB} with '{newESFMtext[illegalWordLinkRegex1Match.start()-5:illegalWordLinkRegex1Match.end()+5]}'" # Don't want double-ups of wordlink numbers
            if BBB=='ACT': newESFMtext = newESFMtext.replace( ' 12Z¦', ' 120¦' ) # Avoided false alarm
            illegalWordLinkRegex2Match = illegalWordLinkRegex2.search( newESFMtext)
            assert not illegalWordLinkRegex2Match, f"illegalWordLinkRegex2 failed before saving {BBB} with '{newESFMtext[illegalWordLinkRegex2Match.start()-5:illegalWordLinkRegex2Match.end()+5]}'" # Don't want double-ups of wordlink numbers
            assert doubledND not in newESFMtext, f"doubled \\nd check failed before saving {BBB} with '{newESFMtext[newESFMtext.index(doubledND)-10:newESFMtext.index(doubledND)+35]}'"
            assert badAddND not in newESFMtext, f"\\nd in \\add start check failed before saving {BBB} with '{newESFMtext[newESFMtext.index(badAddND)-10:newESFMtext.index(badAddND)+35]}'"
            assert badNDAdd not in newESFMtext, f"\\nd in \\add end check failed before saving {BBB} with '{newESFMtext[newESFMtext.index(badNDAdd)-10:newESFMtext.index(badNDAdd)+35]}'"
            # NOTE: '*?' has to have a space before it, because \\add*? might occur at the end of a question
            for wronglyOrderedCombo in ('+?','=?','<?','>?','≡?','&?','@?',' *?','#?','^?','≈?'):
                assert wronglyOrderedCombo not in newESFMtext, f"Wrongly ordered combo check failed with '{wronglyOrderedCombo}' before saving {BBB} with '{newESFMtext[newESFMtext.index(wronglyOrderedCombo)-10:newESFMtext.index(wronglyOrderedCombo)+35]}'"
            with open( rvESFMFilepath, 'wt', encoding='UTF-8' ) as esfmFile:
                esfmFile.write( newESFMtext )
            vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"    Did {bookSimpleListedAdds:,} simple listed adds, {bookProperNounAdds:,} proper noun adds, {bookFirstPartMatchedAdds:,} first part adds and {bookManualMatchedAdds:,} manual adds for {BBB}." )
            vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"    Did {bookSimpleListedAddsNS:,} simple listed NS, {bookProperNounAddsNS:,} proper noun NS, {bookFirstPartMatchedAddsNS:,} first part NS and {bookManualMatchedAddsNS:,} manual NS for {BBB}." )
            vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"      Saved OET-RV {BBB} {len(newESFMtext):,} bytes to {rvESFMFilepath}" )
        else:
            # assert bookSimpleListedAdds == bookProperNounAdds == 0
            vPrint( 'Info', DEBUGGING_THIS_MODULE, f"    No changes made to OET-RV {BBB}." )
        totalSimpleListedAdds += bookSimpleListedAdds
        totalSimpleListedAddsNS += bookSimpleListedAddsNS
        totalProperNounAdds += bookProperNounAdds
        totalProperNounAddsNS += bookProperNounAddsNS
        totalFirstPartMatchedAdds += bookFirstPartMatchedAdds
        totalFirstPartMatchedAddsNS += bookFirstPartMatchedAddsNS
        totalManualMatchedAdds += bookManualMatchedAdds
        totalManualMatchedAddsNS += bookManualMatchedAddsNS

    if totalSimpleListedAdds or totalProperNounAdds or totalFirstPartMatchedAdds or totalManualMatchedAdds:
        vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Did total of {totalSimpleListedAdds:,} simple listed adds, {totalProperNounAdds:,} proper noun adds, {totalFirstPartMatchedAdds:,} first part adds and {totalManualMatchedAdds:,} manual adds." )
    else: vPrint( 'Normal', DEBUGGING_THIS_MODULE, "  No new word connections made." )
    if totalSimpleListedAddsNS or totalProperNounAddsNS or totalFirstPartMatchedAddsNS or totalManualMatchedAddsNS:
        vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Did total of {totalSimpleListedAddsNS:,} simple listed nomina sacra (NS), {totalProperNounAddsNS:,} proper noun NS, {totalFirstPartMatchedAddsNS:,} first part NS and {totalManualMatchedAddsNS:,} manual NS." )
    else: vPrint( 'Info', DEBUGGING_THIS_MODULE, "  No new nomina sacra connections made." )
# end of connect_OET-RV_words_via_OET-LV.connect_OET_RV


wordLinkRegex = re.compile( '¦[1-9][0-9]{0,5}' )
def check_OET_RV_Verse( BBB:str, c:int,v:int, rvEntryList, lvEntryList ) -> None:
    """
    If the OET-RV verse has any existing word numbers,
        check against the OET-LV verse to ensure that they're in the correct range.

    This check is specifically to catch copy and paste errors where a word number accidentally gets wrongly copied into a different verse.
    """
    # fnPrint( DEBUGGING_THIS_MODULE, f"connect_OET_RV( {BBB} {c}:{v} {len(rvEntryList)}, {len(lvEntryList)} )" )
    NT = BibleOrgSysGlobals.loadedBibleBooksCodes.isNewTestament_NR( BBB )
    if NT:
        assert state.wordTableHeaderList.index('VLTGlossWords')+1 == GLOSS_COLUMN__NUMBER, f"{state.wordTableHeaderList.index('VLTGlossWords')+1=} {GLOSS_COLUMN__NUMBER=} {state.wordTableHeaderList=}" # Check we have the correct column below

    discovered_OET_RV_word_numbers = []
    haveVerseRange = False
    for rvEntry in rvEntryList:
        rvMarker, rvRest = rvEntry.getMarker(), rvEntry.getCleanText()
        if rvMarker == 'v' and '-' in rvRest: haveVerseRange = True
        # print( f"Check OET-RV {BBB} {c}:{v} {rvMarker}='{rvRest}'")
        startIndex = 0
        while True:
            wordLinkRegexMatch = wordLinkRegex.search( rvRest, startIndex )
            if not wordLinkRegexMatch: break
            # print( f"Check OET-RV {BBB} {c}:{v} {rvMarker}='{rvRest}' {wordLinkRegexMatch.group()=}" )
            discovered_OET_RV_word_numbers.append( int( wordLinkRegexMatch.group()[1:]) )
            startIndex = wordLinkRegexMatch.end() + 1
    if not discovered_OET_RV_word_numbers:
        return # nothing to see here
    # print( f"Check OET-RV {BBB} {c}:{v} {discovered_OET_RV_word_numbers=}" )

    minLVWordNumber, maxLVWordNumber = 999_9999, 0
    for lvEntry in lvEntryList:
        lvMarker,lvRest = lvEntry.getMarker(), lvEntry.getCleanText()
        # print( f"Check OET-LV {BBB} {c}:{v} {lvMarker}='{lvRest}'")
        startIndex = 0
        while True:
            wordLinkRegexMatch = wordLinkRegex.search( lvRest, startIndex )
            if not wordLinkRegexMatch: break
            # print( f"Check OET-LV {BBB} {c}:{v} {lvMarker}='{lvRest}' {wordLinkRegexMatch.group()=}" )
            wordNumber = int( wordLinkRegexMatch.group()[1:])
            if wordNumber < minLVWordNumber: minLVWordNumber = wordNumber
            if wordNumber > maxLVWordNumber: maxLVWordNumber = wordNumber
            startIndex = wordLinkRegexMatch.end() + 1
    # print( f"Check OET-RV {BBB} {c}:{v} {minLVWordNumber=} {maxLVWordNumber=}" )

    for discovered_RV_word_number in discovered_OET_RV_word_numbers:
        if discovered_RV_word_number < minLVWordNumber or discovered_RV_word_number > maxLVWordNumber:
            if haveVerseRange:
                logging.warning( f"OET-RV {BBB} {c}:{v} {discovered_OET_RV_word_numbers=} HAS VERSE RANGE {minLVWordNumber=} {maxLVWordNumber=}" )
            else:
                raise ValueError( f"OET-RV {BBB} {c}:{v} {discovered_RV_word_number=} OUT OF RANGE {minLVWordNumber=} {maxLVWordNumber=} from {discovered_OET_RV_word_numbers=}" )
# end of connect_OET-RV_words_via_OET-LV.check_OET_RV_Verse


GLOSS_COLUMN__NUMBER = 5
def connect_OET_RV_Verse( BBB:str, c:int,v:int, rvEntryList, lvEntryList ) -> Tuple[Tuple[int,int],Tuple[int,int],Tuple[int,int],Tuple[int,int]]:
    """
    Some undocumented documentation of the NT GlossCaps column from state.wordTable:
        ●    U – lexical entry capitalized
        ●    W – proper noun
        ●    G – reference to deity
        ●    P – paragraph boundary
        ●    S – start of sentence
        ●    D – quoted dialog
        ●    V – vocative title
        ●    B – Biblical quotation
        ●    R – other quotation
        ●    T – translated words
        ●    N – nomina sacra (our addition)

        ●    h – partial word capitalized
        ●    n – named but not proper name
        ●    b – incorporated Biblical quotation
        ●    c – continuation of quotation
        ●    e – emphasized words (scare quotes)
    The lowercase letters mark other significant places where the words are not normally capitalized.
    """
    connectRef = f'{BBB}_{c}:{v}'
    # fnPrint( DEBUGGING_THIS_MODULE, f"connect_OET_RV( {BBB} {c}:{v} {len(rvEntryList)}, {len(lvEntryList)} )" )
    # if connectRef == 'PSA_54:1':
    #     print( f"\nconnect_OET_RV( {connectRef} {len(rvEntryList)} {rvEntryList=}, {len(lvEntryList)} {lvEntryList=} )" )
    NT = BibleOrgSysGlobals.loadedBibleBooksCodes.isNewTestament_NR( BBB )
    if NT:
        assert state.wordTableHeaderList.index('VLTGlossWords')+1 == GLOSS_COLUMN__NUMBER, f"{state.wordTableHeaderList.index('VLTGlossWords')+1=} {GLOSS_COLUMN__NUMBER=} {state.wordTableHeaderList=}" # Check we have the correct column below

    rvText = ''
    for rvEntry in rvEntryList:
        rvMarker, rvRest = rvEntry.getMarker(), rvEntry.getCleanText()
        # print( f"OET-RV {connectRef} {rvMarker}='{rvRest}'")
        if rvMarker in ('v~','p~','d'):
            rvText = f"{rvText}{' ' if rvText else ''}{rvRest}"
    lvText = ''
    for lvEntry in lvEntryList:
        lvMarker,lvRest = lvEntry.getMarker(), lvEntry.getCleanText()
        if lvMarker in ('v~','p~'):
            lvText = f"{lvText}{' ' if lvText else ''}{lvRest.replace('+','')}"
            # lvTextSimplified = lvText.replace('¦','').replace('0','').replace('1','').replace('2','').replace('3','').replace('4','').replace('5','').replace('6','').replace('7','').replace('8','').replace('9','') \
            #                     .replace('¬','').replace('_',' ').replace('  ',' ') \
            #                     .replace('before','').replace('forget','').replace('forgive','').replace('forty','').replace('therefore','').replace('fore','') \
            #                     .replace('tolerable for','').replace('account for','').replace('prepared for','').replace('waiting for','').replace('ing for','').replace('ous for','') \
            #                     .replace('for all','').replace('for her','').replace('for him','').replace('for me','').replace('for them','').replace('for you','').replace('for us','') \
            #                     .replace('for days','').replace('for months','')
            # if lvTextSimplified.startswith( 'for ' ) or lvTextSimplified.startswith( 'For ' ) or ' for ' in lvTextSimplified or 'For ' in lvTextSimplified:
            #     print( f"FOR: {BBB}_{c}:{v}, '{lvTextSimplified.replace('for','FOR').replace('For','FOR')}'" )
            #     forList.append( f"{BBB}_{c}:{v}" )
    if not rvText or not lvText: return (0,0), (0,0), (0,0), (0,0)

    rvAdjText = rvText.replace('◘','').replace('≈','').replace('…','') \
                .replace('.','').replace(',','').replace(':','').replace(';','').replace('?','').replace('!','') \
                .replace('/',' ').replace('—',' ') \
                .replace( '(', '').replace( ')', '' ) \
                .replace( '“', '' ).replace( '”', '' ).replace( '‘', '' ).replace( '’', '') \
                .replace('  ',' ').strip()
    lvAdjText = lvText.replace('_',' ').replace('=',' ').replace('÷',' ') \
                .replace('˱','').replace('˲','') \
                .replace('0/','0 ').replace('1/','1 ').replace('2/','2 ').replace('3/','3 ').replace('4/','4 ').replace('5/','5 ').replace('6/','6 ').replace('7/','7 ').replace('8/','8 ').replace('9/','9 ') \
                .replace('.','').replace(',','').replace(':','').replace(';','').replace('?','').replace('!','') \
                .replace( '(', '').replace( ')', '' ) \
                .replace('   ',' ').replace('  ',' ').strip()
    if lvAdjText.startswith( '/' ): lvAdjText = lvAdjText[1:]
    # print( f"({len(rvAdjText)}) {rvAdjText=}")
    # print( f"({len(lvAdjText)}) {lvAdjText=}")
    if not rvAdjText or not lvAdjText: return (0,0), (0,0), (0,0), (0,0)

    lvWords = lvAdjText.split( ' ' )
    rvWords1 = rvAdjText.split( ' ' )
    # print( f"({len(rvWords)}) {rvWords=}")
    # print( f"({len(lvWords)}) {lvWords=}")
    # if BBB=='PSA' and c in (3,23,29) and v<3: print( f"{connectRef} {lvWords=} {rvWords1=}" )

    # Remove DOM's from word list
    #   These are capitalised, but untranslated, so remove them here (because won't ever be in RV)
    initialNumWords = len( lvWords )
    for lvIndex, lvWord in enumerate( reversed( lvWords), start=1 ):
        # print( f"  {lvIndex} {lvWord=}" )
        if lvWord.startswith( 'DOM¦' ):
            lvWords.pop( initialNumWords - lvIndex )
            # print( f"    ({len(lvWords)}) {lvWords=}")
    # print( f"({len(lvWords)}) {lvWords=}")
    assert lvWords

    # if 0: # Mostly works but a couple of exceptions
    #     badIx = None
    #     for ix,lvWord in enumerate( lvWords ):
    #         if lvWord == 'Galilaia': continue # These two bad lines are from 2 Ti NOT Galilaia TODO
    #         if lvWord == 'NOT': badIx = ix
    #         else:
    #             assert lvWord, f"{lvText=} {lvAdjText=}"
    #             assert lvWord.count( '¦' ) == 1, f"{connectRef} {lvWord=}" # Check that we haven't been retagging already tagged RV words
    #     if badIx is not None: lvWords.pop( badIx )

    assert rvWords1
    rvWords = []
    for rvWord in rvWords1:
        assert rvWord, f"{connectRef} {rvText=} {rvAdjText=}"
        rvWordBits = rvWord.split( '-' )
        if len(rvWordBits) == 1: # No hyphen
            assert rvWord.count( '¦' ) <= 1, f"{connectRef} {rvWord=} {rvText=} {rvAdjText=}" # Check that we haven't been retagging already tagged RV words
            rvWords.append( rvWord )
        elif rvWordBits[1][0].isupper(): # Hyphenated and with a capital letter, e.g., Kiriat-Arba (may even have three parts)
            for rvWordBit in rvWordBits:
                assert rvWordBit.count( '¦' ) <= 1, f"{connectRef} {rvWordBit=} {rvText=} {rvAdjText=}" # Check that we haven't been retagging already tagged RV words
                rvWords.append( rvWordBit )

    numSimpleListedAdds,numSimpleListedNS = matchOurListedSimpleWords( BBB, c,v, rvWords, lvWords )

    # Now get the uppercase words
    rvUpperWords = [rvWord for rvWord in rvWords if rvWord[0].isupper()]
    lvUpperWords = [lvWord for lvWord in lvWords if (lvWord[0].isupper() or (lvWord[0] in 'ʼˊ' and lvWord[1].isupper()))]
    # print( f"{rvText=} {lvText=}" )

    if lvUpperWords and lvText[0].isupper(): # Try to determine why the first word was capitalised
        dPrint( 'Info', DEBUGGING_THIS_MODULE, f"{lvUpperWords=} from {lvText=}")
        firstLVUpperWord, firstLVUpperNumber = lvUpperWords[0].split( '¦' )
        rowForFirstLVUpperWord = state.wordTable[int(firstLVUpperNumber)]
        if NT:
            firstLVUpperWordCapsFlags = rowForFirstLVUpperWord[state.wordTableHeaderList.index('GlossCaps')]
            # print( f"{firstLVUpperWordCapsFlags=} from {rowForFirstLVUpperWord=}" )
            if 'G' not in firstLVUpperWordCapsFlags and 'W' not in firstLVUpperWordCapsFlags and firstLVUpperWord!='I':
                # print( f"Removing first LV Uppercase word: '{lvUpperWords[0]}' with '{firstLVUpperWordCapsFlags}'")
                lvUpperWords.pop(0) # Throw away the first word because it might just be capitalised for being at the beginning of the sentence.
        else: # OT
            firstLVUpperWordCapsFlags = rowForFirstLVUpperWord[state.wordTableHeaderList.index('GlossCapitalisation')]
            # print( f"{firstLVUpperWordCapsFlags=} from {rowForFirstLVUpperWord=}" )
            if 'S' in firstLVUpperWordCapsFlags and firstLVUpperWord!='I':
                # print( f"Removing first LV Uppercase word: '{lvUpperWords[0]}' with '{firstLVUpperWordCapsFlags}'")
                lvUpperWords.pop(0) # Throw away the first word because it might just be capitalised for being at the beginning of the sentence.
    # if rvText[0].isupper():
    #   rvUpperWords.pop(0) # Throw away the first word because it might just be capitalised for being at the beginning of the sentence.
    # print( f"({len(rvUpperWords)}) {rvUpperWords=}")
    # print( f"({len(lvUpperWords)}) {lvUpperWords=}")
    numIdenticalProperNounAdds,numIdenticalProperNounNS = matchIdenticalProperNouns( BBB, c,v, rvUpperWords, lvUpperWords ) if rvUpperWords and lvUpperWords else (0,0)
    numAdjustedProperNounAdds,numAdjustedProperNounNS = matchAdjustedProperNouns( BBB, c,v, rvUpperWords, lvUpperWords ) if rvUpperWords and lvUpperWords else (0,0)

    numFirstPartMatchedWords,numFirstPartMatchedWordsNS = matchWordsFirstParts( BBB, c,v, rvWords, lvWords )

    numHandmatches,numHandmatchesNS = matchWordsManually( BBB, c,v, rvWords, lvWords )

    return (numSimpleListedAdds,numSimpleListedNS), \
           (numIdenticalProperNounAdds+numAdjustedProperNounAdds,numIdenticalProperNounNS+numAdjustedProperNounNS), \
           (numFirstPartMatchedWords,numFirstPartMatchedWordsNS), \
           (numHandmatches,numHandmatchesNS)
# end of connect_OET-RV_words_via_OET-LV.connect_OET_RV_Verse


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
def matchIdenticalProperNouns( BBB:str, c:int,v:int, rvCapitalisedWordList:List[str], lvCapitalisedWordList:List[str] ) -> Tuple[int,int]:
    """
    Given a list of capitalised words from OET-RV and OET-LV,
        see if we can match any identical proper nouns

    TODO: This function can add new numbers on repeated calls,
        e.g., Acts 11:30 Barnabas and Saul are done one each call
        but could both be added at the same time?
        Jn 3:22, 4:3, 12:36,39, 21:10 Act 11:30,13:31,15:25,40,16:31,18:8
    """
    fnPrint( DEBUGGING_THIS_MODULE, f"matchIdenticalProperNouns( {BBB} {c}:{v} {rvCapitalisedWordList}, {lvCapitalisedWordList} )" )
    assert rvCapitalisedWordList and lvCapitalisedWordList

    NT = BibleOrgSysGlobals.loadedBibleBooksCodes.isNewTestament_NR( BBB )

    # But we don't want any rvWords that are already tagged
    numAdded = numNS = 0
    numRemovedRV = 0 # Extra work because we're deleting from same list that we're iterating through (a copy of)
    for rvN,rvCapitalisedWord in enumerate( rvCapitalisedWordList[:] ):
        # print( f"{BBB} {c}:{v} {rvN} {rvCapitalisedWord=} from {rvCapitalisedWordList}")
        if '¦' in rvCapitalisedWord:
            _rvCapitalisedWord, rvWordNumber = rvCapitalisedWord.split('¦')
            dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  matchIdenticalProperNouns( {BBB} {c}:{v} ) removing already tagged '{rvCapitalisedWord}' from RV list…")
            rvCapitalisedWordList.pop( rvN - numRemovedRV )
            numRemovedRV += 1
            numRemovedLV = 0 # Extra work because we're deleting from same list that we're iterating through (a copy of)
            for lvN,lvCapitalisedWord in enumerate( lvCapitalisedWordList[:] ):
                if lvCapitalisedWord.endswith( f'¦{rvWordNumber}' ):
                    dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  matchIdenticalProperNouns( {BBB} {c}:{v} ) removing already tagged '{lvCapitalisedWord}' from LV list…")
                    lvCapitalisedWordList.pop( lvN - numRemovedLV )
                    numRemovedLV += 1
    if not rvCapitalisedWordList or not lvCapitalisedWordList:
        return numAdded,numNS # nothing left to do here

    if len(rvCapitalisedWordList)==1 and len(lvCapitalisedWordList)==1: # easy case!
        assert rvCapitalisedWordList[0].replace("'",'').isalpha(), f"{rvCapitalisedWordList=}" # It might contain an apostrophe
        # print( f"{rvCapitalisedWordList=} {lvCapitalisedWordList=}" )
        assert '¦' in lvCapitalisedWordList[0], f"{lvCapitalisedWordList[0]=} from {lvCapitalisedWordList=}"
        capitalisedNoun,wordNumber,wordRow = getLVWordRow( lvCapitalisedWordList[0] )
        if NT:
            wordRole = wordRow[state.wordTableHeaderList.index('Role')]
            dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  '{capitalisedNoun}' {wordRole}" )
            if wordRole == 'N': # let's assume it's a proper noun
                # print( f"matchIdenticalProperNouns {BBB} {c}:{v} adding number to {rvCapitalisedWordList[0]}")
                result = addNumberToRVWord( BBB, c,v, rvCapitalisedWordList[0], wordNumber )
                if result:
                    numAdded += 1
                    if 'N' in wordRow[state.wordTableHeaderList.index('GlossCaps')]:
                        numNS += 1
        else: # OT
            glossCaps = wordRow[state.wordTableHeaderList.index('GlossCapitalisation')]
            dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  {capitalisedNoun=} {glossCaps=}" )
            if glossCaps != 'S': # start of sentence
                result = addNumberToRVWord( BBB, c,v, rvCapitalisedWordList[0], wordNumber )
                if result:
                    numAdded += 1
    elif len(rvCapitalisedWordList) == len(lvCapitalisedWordList):
        dPrint( 'Info', DEBUGGING_THIS_MODULE, f"matchIdenticalProperNouns() lists are equal size ({len(rvCapitalisedWordList)})" )
        return numAdded,numNS
        # for capitalisedNounPair in capitalisedNounPair:
        #     assert '¦' in capitalisedNounPair, f"{capitalisedNounPair=} from {capitalisedNounPair=}"
        #     capitalisedNoun,wordNumber,wordRow = getLVWordRow( capitalisedNounPair )
        #     dPrint( 'Info', f"'{capitalisedNoun}' {wordRow}" )
        #     halt
    else:
        dPrint( 'Info', DEBUGGING_THIS_MODULE, f"matchIdenticalProperNouns() lists are different sizes {len(rvCapitalisedWordList)=} and {len(lvCapitalisedWordList)=}" )
        # for capitalisedNounPair in lvCapitalisedWordList:
        #     capitalisedNoun,wordNumber,wordRow = getLVWordRow( capitalisedNounPair )
        #     dPrint( 'Info', DEBUGGING_THIS_MODULE, f"'{capitalisedNoun}' {wordRow}" )
        #     halt
    return numAdded,numNS
# end of connect_OET-RV_words_via_OET-LV.matchIdenticalProperNouns


def matchAdjustedProperNouns( BBB:str, c:int,v:int, rvCapitalisedWordList:List[str], lvCapitalisedWordList:List[str] ) -> Tuple[int,int]:
    """
    Given a list of capitalised words from OET-RV and OET-LV,
        see if we can match any proper nouns using the ScriptedBibleEditor name tables
    """
    fnPrint( DEBUGGING_THIS_MODULE, f"matchAdjustedProperNouns( {BBB} {c}:{v} {rvCapitalisedWordList}, {lvCapitalisedWordList} )" )
    assert rvCapitalisedWordList and lvCapitalisedWordList

    NT = BibleOrgSysGlobals.loadedBibleBooksCodes.isNewTestament_NR( BBB )

    # But we don't want any rvWords that are already tagged
    numAdded = numNS = 0
    numRemovedRV = 0 # Extra work because we're deleting from same list that we're iterating through (a copy of)
    for rvN,rvCapitalisedWord in enumerate( rvCapitalisedWordList[:] ):
        # print( f"{BBB} {c}:{v} {rvN} {rvCapitalisedWord=} from {rvCapitalisedWordList}")
        if '¦' in rvCapitalisedWord:
            _rvCapitalisedWord, rvWordNumber = rvCapitalisedWord.split('¦')
            dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  matchAdjustedProperNouns( {BBB} {c}:{v} ) removing already tagged '{rvCapitalisedWord}' from RV list…")
            rvCapitalisedWordList.pop( rvN - numRemovedRV )
            numRemovedRV += 1
            numRemovedLV = 0 # Extra work because we're deleting from same list that we're iterating through (a copy of)
            for lvN,lvCapitalisedWord in enumerate( lvCapitalisedWordList[:] ):
                if lvCapitalisedWord.endswith( f'¦{rvWordNumber}' ):
                    dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  matchAdjustedProperNouns( {BBB} {c}:{v} ) removing already tagged '{lvCapitalisedWord}' from LV list…")
                    lvCapitalisedWordList.pop( lvN - numRemovedLV )
                    numRemovedLV += 1
    if not rvCapitalisedWordList or not lvCapitalisedWordList:
        return numAdded,numNS # nothing left to do here

    dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"\n{BBB} {c}:{v} {rvCapitalisedWordList=} {lvCapitalisedWordList=}" )
    for lvCapitalisedWord in lvCapitalisedWordList:
        dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"{lvCapitalisedWord=} from {lvCapitalisedWordList=}" )
        assert '¦' in lvCapitalisedWord, f"{BBB} {c}:{v} {lvCapitalisedWord=} from {lvCapitalisedWordList=}"
        capitalisedNoun,wordNumber,wordRow = getLVWordRow( lvCapitalisedWord )

        for rvCapitalisedWord in rvCapitalisedWordList:
            dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"{rvCapitalisedWord=} from {rvCapitalisedWordList=}" )
            assert rvCapitalisedWord.replace("'",'').isalpha(), f"{rvCapitalisedWordList=}" # It might contain an apostrophe
            if NT:
                wordRole = wordRow[state.wordTableHeaderList.index('Role')]
                dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"  matchAdjustedProperNouns NT '{capitalisedNoun}' {wordRole}" )
                if wordRole == 'N': # let's assume it's a proper noun
                    if capitalisedNoun in state.nameTables['NT']:
                        dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"  {BBB} {c}:{v} {capitalisedNoun=} {state.nameTables['NT'][capitalisedNoun]=}")
                        for something in state.nameTables['NT'][capitalisedNoun]:
                            dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"    {capitalisedNoun=} {something=} from {state.nameTables['NT'][capitalisedNoun]=}")
                            if something == rvCapitalisedWord:
                                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"matchAdjustedProperNouns {BBB} {c}:{v} adding number to NT {rvCapitalisedWord}")
                                result = addNumberToRVWord( BBB, c,v, rvCapitalisedWord, wordNumber )
                                if result:
                                    numAdded += 1
                                if 'N' in wordRow[state.wordTableHeaderList.index('GlossCaps')]:
                                    numNS += 1
                                break
                    elif capitalisedNoun in state.nameTables['NT_OT']:
                        dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"  {BBB} {c}:{v} {capitalisedNoun=} {state.nameTables['NT_OT'][capitalisedNoun]=}")
                        for something in state.nameTables['NT_OT'][capitalisedNoun]:
                            dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"    {capitalisedNoun=} {something=} from {state.nameTables['NT_OT'][capitalisedNoun]=}")
                            if something == rvCapitalisedWord:
                                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"matchAdjustedProperNouns {BBB} {c}:{v} adding number to NT {rvCapitalisedWord}")
                                result = addNumberToRVWord( BBB, c,v, rvCapitalisedWord, wordNumber )
                                if result:
                                    numAdded += 1
                                if 'N' in wordRow[state.wordTableHeaderList.index('GlossCaps')]:
                                    numNS += 1
                                break
            else: # OT
                glossCaps = wordRow[state.wordTableHeaderList.index('GlossCapitalisation')]
                dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"  matchAdjustedProperNouns OT {capitalisedNoun=} {glossCaps=}" )
                if glossCaps != 'S': # start of sentence
                    if capitalisedNoun in state.nameTables['OT']:
                        dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"  {BBB} {c}:{v} {capitalisedNoun=} {state.nameTables['OT'][capitalisedNoun]=}")
                        for something in state.nameTables['OT'][capitalisedNoun]:
                            dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"    {capitalisedNoun=} {something=} from {state.nameTables['OT'][capitalisedNoun]=}")
                            if something == rvCapitalisedWord:
                                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"matchAdjustedProperNouns {BBB} {c}:{v} adding number to OT {rvCapitalisedWord}")
                                result = addNumberToRVWord( BBB, c,v, rvCapitalisedWord, wordNumber )
                                if result:
                                    numAdded += 1
                                break
                            elif f"{something}'s" == rvCapitalisedWord:
                                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"matchAdjustedProperNouns {BBB} {c}:{v} adding number to possessive OT {rvCapitalisedWord}")
                                result = addNumberToRVWord( BBB, c,v, rvCapitalisedWord, wordNumber )
                                if result:
                                    numAdded += 1
                                break
                    # elif rvCapitalisedWord.endswith( "'s" ) and capitalisedNoun[:-2] in state.nameTables['OT']:
                    #     dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"  {BBB} {c}:{v} {capitalisedNoun=} {state.nameTables['OT'][capitalisedNoun[:-2]]=}")
                    #     for something in state.nameTables['OT'][capitalisedNoun[:-2]]:
                    #         dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"    {capitalisedNoun=} {something=} from {state.nameTables['OT'][capitalisedNoun[:-2]]=}")
                    #         if f"{something}'s" == rvCapitalisedWord:
                    #             dPrint( 'Info', DEBUGGING_THIS_MODULE, f"matchAdjustedProperNouns {BBB} {c}:{v} adding number to OT {rvCapitalisedWord}")
                    #             result = addNumberToRVWord( BBB, c,v, rvCapitalisedWord, wordNumber )
                    #             if result:
                    #                 numAdded += 1
                    #             halt
                    #             break
    # if BBB=='KI2' and c==17 and v==1:
    #     print( f"{rvCapitalisedWordList=} {lvCapitalisedWordList=}" )
    #     halt
    return numAdded,numNS
# end of connect_OET-RV_words_via_OET-LV.matchAdjustedProperNouns


def matchOurListedSimpleWords( BBB:str, c:int,v:int, rvWordList:List[str], lvWordList:List[str] ) -> Tuple[int,int]:
    """
    If the simple word (e.g., nouns) only occur once in the RV verse and once in the LV verse,
        we assume that we can match them, i.e., copy the wordlink numbers from the LV into the RV.
    """
    fnPrint( DEBUGGING_THIS_MODULE, f"matchOurListedSimpleWords( {BBB} {c}:{v} {rvWordList}, {lvWordList} )" )
    assert rvWordList and lvWordList

    NT = BibleOrgSysGlobals.loadedBibleBooksCodes.isNewTestament_NR( BBB )

    numAdded = numNS = 0
    for simpleNoun in SIMPLE_WORDS:
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
            return numAdded,numNS
        assert len(rvIndexList) == len(lvIndexList), f"{BBB} {c}:{v} {simpleNoun=} {rvIndexList=} {lvIndexList=}"

        lvNumbers = []
        for lvN in lvIndexList:
            assert '¦' in lvWordList[lvN], f"{lvN=} {lvWordList[lvN]=} from {lvWordList=}"
            lvNoun,lvWordNumber,lvWordRow = getLVWordRow( lvWordList[lvN] )
            lvNumbers.append( lvWordNumber )
        assert len(lvNumbers) == 1 # NOT TRUE: If there's two 'camels' in the verse, we expect both to have the same word number
        for rvN in rvIndexList:
            rvNoun = rvWordList[rvN]
            if rvNoun.lower() == lvNoun.lower():
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"matchOurListedSimpleWords() is adding a number to RV '{rvNoun}' at {BBB} {c}:{v} {rvN=}")
                result = addNumberToRVWord( BBB, c,v, rvNoun, lvWordNumber )
                if result:
                    numAdded += 1
                    if NT and 'N' in state.wordTable[lvWordNumber][state.wordTableHeaderList.index('GlossCaps')]:
                        numNS += 1
            # else:
            #     dPrint( 'Normal', DEBUGGING_THIS_MODULE, f"ERROR matchOurListedSimpleWords() would have connected LV '{lvNoun}' to RV '{rvNoun}' at {BBB} {c}:{v} {rvN=}")

    return numAdded,numNS
# end of connect_OET-RV_words_via_OET-LV.matchOurListedSimpleWords


def matchWordsFirstParts( BBB:str, c:int,v:int, rvWordList:List[str], lvWordList:List[str] ) -> Tuple[int,int]:
    """
    If the longish word only occurs once in the LV word list
        and a similar starting word only occurs on in the RV word list
            we assume that we can match them, i.e., copy the wordlink numbers from the LV into the RV.

    This handles tense changes, e.g., LV despising and RV despised.
    """
    fnPrint( DEBUGGING_THIS_MODULE, f"matchWordsFirstParts( {BBB} {c}:{v} {rvWordList}, {lvWordList} )" )
    assert rvWordList and lvWordList

    NT = BibleOrgSysGlobals.loadedBibleBooksCodes.isNewTestament_NR( BBB )

    # Firstly make a matching list of LV words without the word numbers
    simpleLVWordList = []
    for lvWordStr in lvWordList:
        try: lvWord, lvNumber = lvWordStr.split( '¦' )
        except ValueError:
            logging.critical( f"matchWordsFirstParts failed on {lvWordStr=} from {BBB} {c}:{v} {lvWordList=}" )
            lvWord = lvWordStr # One or two little mess-ups
        simpleLVWordList.append( lvWord )

    numAdded = numNS = 0
    for lvIx,lvWord in enumerate( simpleLVWordList ):
        if len(lvWord) < 5: continue # We only process longer words
        if simpleLVWordList.count( lvWord ) != 1: continue # We can't distinguish between two usages in one verse
        dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"{lvWord=} {lvNumber=}" )

        lvWordStart = lvWord[:5] # Get the first 5 letters
        dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"  Looking for RV '{lvWordStart}' from LV '{lvWord}'" )
        rvIndexes = []
        for rvIx,rvWord in enumerate( rvWordList ):
            if rvWord.startswith( lvWordStart ):
                dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"  Found RV '{rvWord}' in {BBB} {c}:{v}")
                rvIndexes.append( rvIx )

        if len(rvIndexes) == 1: # Only one RV word starts with those same letters
            rvWord = rvWordList[rvIndexes[0]]
            if '¦' not in rvWord:
                assert '¦' in lvWordList[lvIx], f"{lvIx=} {lvWordList[lvIx]=} from {lvWordList=}"
                lvWord,lvWordNumber,lvWordRow = getLVWordRow( lvWordList[lvIx] )
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"matchWordsFirstParts() is adding a number to RV '{rvWord}' from '{lvWord}' at {BBB} {c}:{v} {rvIx=}")
                result = addNumberToRVWord( BBB, c,v, rvWord, lvWordNumber )
                if result:
                    numAdded += 1
                    if NT and 'N' in lvWordRow[state.wordTableHeaderList.index('GlossCaps')]:
                        numNS += 1
                else:
                    logging.warning( f"Got addNumberToRVWord( {BBB} {c}:{v} '{rvWord}' {lvWordNumber} ) result = {result}" )
                    # why_did_we_fail

    return numAdded,numNS
# end of connect_OET-RV_words_via_OET-LV.matchWordsFirstParts


def matchWordsManually( BBB:str, c:int,v:int, rvVerseWordList:List[str], lvVerseWordList:List[str] ) -> Tuple[int,int]:
    """
    """
    fnPrint( DEBUGGING_THIS_MODULE, f"matchWordsManually( {BBB} {c}:{v} {rvVerseWordList}, {lvVerseWordList} )" )
    assert rvVerseWordList and lvVerseWordList
    # if BBB=='JAM' and 'Jacob' in rvVerseWordList: print( lvVerseWordList ); halt

    # Firstly make matching lists of LV and RV words without the word numbers
    simpleLVWordList = []
    for lvWordStr in lvVerseWordList:
        try: lvWord, lvNumber = lvWordStr.split( '¦' )
        except ValueError:
            logging.critical( f"matchWordsManually failed on {lvWordStr=} from {BBB} {c}:{v} {lvVerseWordList=}" )
            lvWord = lvWordStr # One or two little mess-ups
        simpleLVWordList.append( lvWord )
    simpleRVWordList = []
    for rvWordStr in rvVerseWordList:
        try: rvWord, rvNumber = rvWordStr.split( '¦' )
        except ValueError: # Lots of RV words don't have numbers yet
            rvWord = rvWordStr
        simpleRVWordList.append( rvWord )

    numAdded = numNS = 0
    result1,result1NS = doGroup1( BBB, c, v, rvVerseWordList, lvVerseWordList, simpleLVWordList )
    numAdded += result1
    numNS += result1NS
    result2,result2NS = doGroup2( BBB, c, v, rvVerseWordList, lvVerseWordList, simpleRVWordList, simpleLVWordList )
    numAdded += result2
    numNS += result2NS

    return numAdded,numNS
# end of connect_OET-RV_words_via_OET-LV.matchWordsManually


def doGroup1( BBB:str, c:int, v:int, rvVerseWordList:List[str], lvVerseWordList:List[str], simpleLVWordList:List[str] ) -> Tuple[int,int]:
    """
    This list is 1 RV from 1 or many LV
    Match things like RV 'your' with LV 'of you'
    """
    # if BBB=='KI2' and c==15 and v==28:
    #     print( f"doGroup1( {BBB} {c}:{v} {rvVerseWordList=} {lvVerseWordList=} {simpleLVWordList=} )")
    #     halt
    NT = BibleOrgSysGlobals.loadedBibleBooksCodes.isNewTestament_NR( BBB )

    numAdded = numNS = 0
    for rvWord, lvWordStr in RV_WORDS_FROM_LV_WORD_STRINGS:
        dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"{rvWord=} {lvWordStr=}" )
        lvWords = lvWordStr.split( ' ' )
        assert len(lvWords) <= 3, lvWords # if more, we need to add searching code down below

        dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"  Looking for RV '{rvWord}'" )
        rvIndexes = []
        for rvIx,thisRvWord in enumerate( rvVerseWordList ):
            if thisRvWord == rvWord:
                dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"  matchWordsManually group1 found RV '{rvWord}' in {BBB} {c}:{v}")
                rvIndexes.append( rvIx )

        if len(rvIndexes) == 1: # Only one RV word matches
            rvWord = rvVerseWordList[rvIndexes[0]]
            if '¦' not in rvWord:
                # Now see if we have the LV word(s)
                for lvIx, thisLvWord in enumerate( simpleLVWordList ):
                    matchedLvWordCount = 0
                    if thisLvWord == lvWords[0]: # matched one word
                        matchedLvWordCount += 1
                        if matchedLvWordCount == len(lvWords): break
                        if lvIx < len(simpleLVWordList)-1:
                            if simpleLVWordList[lvIx+1] == lvWords[1]:
                                matchedLvWordCount += 1
                                if matchedLvWordCount == len(lvWords): break
                                if lvIx < len(simpleLVWordList)-2:
                                    if simpleLVWordList[lvIx+2] == lvWords[2]:
                                        matchedLvWordCount += 1
                                        if matchedLvWordCount == len(lvWords): break
                else: # no match (no break from above/inner loop)
                    continue # in the outer loop
                assert matchedLvWordCount == len(lvWords)
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"matchWordsManually group1 {BBB} {c}:{v} matched {rvWord=} {lvWords=}" )
                assert '¦' in lvVerseWordList[lvIx], f"{lvIx=} {lvVerseWordList[lvIx]=} from {lvVerseWordList=}"
                lvWord,lvWordNumber,lvWordRow = getLVWordRow( lvVerseWordList[lvIx] )
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"matchWordsManually group1 is adding a number to RV '{rvWord}' from '{lvWord}' at {BBB} {c}:{v} {lvIx=}")
                result = addNumberToRVWord( BBB, c,v, rvWord, lvWordNumber )
                if result:
                    numAdded += 1
                    if NT and 'N' in lvWordRow[state.wordTableHeaderList.index('GlossCaps')]:
                        numNS += 1
                else:
                    logging.warning( f"Got addNumberToRVWord( {BBB} {c}:{v} '{rvWord}' {lvWordNumber} ) result = {result}" )
                    # why_did_we_fail
    return numAdded,numNS
# end of connect_OET-RV_words_via_OET-LV.doGroup1


def doGroup2( BBB:str, c:int, v:int, rvVerseWordList:List[str], lvVerseWordList:List[str], simpleRVWordList:List[str], simpleLVWordList:List[str] ) -> Tuple[int,int]:
    """
    This list is one LV word to many RV words
    """
    numAdded = numNS = 0
    for lvWord, rvWordStr  in (
            ('brothers', 'brothers and sisters'), ('brothers', 'fellow believers'),
            ('Brothers', 'Brothers and sisters'), ('Brothers', 'Fellow believers'),
            ('Brothers', 'brothers and sisters'), ('Brothers', 'fellow believers'),

            ('Higgaion', 'Meditation break'),
            ('Şelāh', 'Instrumental break'),
            ('Truly', 'May it be so'),

            ('ascent','walking uphill'),
            ('members', 'body parts'),
            ('risen', 'got up'),
            ('sanctuary', 'sacred tent'),
            ('scribes', 'religious teachers'),
            ('seeking', 'looking for'),
            ('synagogues', 'Jewish meeting halls'), ('synagogues', 'meeting halls'),
            ('synagogue', 'Jewish meeting hall'), ('synagogue', 'meeting hall'),
            ('tabernacle', 'sacred tent'),
            ):
        dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"{lvWord=} {rvWordStr=}" )
        rvWords = rvWordStr.split( ' ' )
        assert len(rvWords) <= 4, rvWords # if more, we need to add searching code down below

        dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"  Looking for LV '{lvWord}'" )
        lvIndexes = []
        for lvIx,thisLvWord in enumerate( simpleLVWordList ):
            if thisLvWord == lvWord:
                dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"  matchWordsManually group2 found LV '{lvWord}' in {BBB} {c}:{v}")
                lvIndexes.append( lvIx )

        if len(lvIndexes) == 1: # Only one LV word matches
            lvWordStr = lvVerseWordList[lvIndexes[0]]
            assert '¦' in lvWordStr
            lvWord, lvWordNumber = lvWordStr.split( '¦' )
            lvWordNumber = int( lvWordNumber )
            # print( f"    here with {lvWordStr} -> '{lvWord}' and {lvWordNumber=}")

            # Now see if we have the RV word(s)
            for rvIx, thisRvWord in enumerate( simpleRVWordList ):
                matchedRvWordCount = 0
                if thisRvWord == rvWords[0]: # matched one word
                    matchedRvWordCount += 1
                    # print( f"      Matched 1/{len(rvWords)} @ {rvIx} with '{thisRvWord}' ({rvWordList[rvIx]})")
                    if matchedRvWordCount == len(rvWords): break # matched one word
                    if rvIx < len(simpleRVWordList)-1:
                        if simpleRVWordList[rvIx+1] == rvWords[1]:
                            matchedRvWordCount += 1
                            dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"        Matched 2/{len(rvWords)} @ {rvIx+1} with '{rvVerseWordList[rvIx+1]}' from '{rvWordStr}'")
                            if matchedRvWordCount == len(rvWords): break # matched two words
                            if rvIx < len(simpleRVWordList)-2:
                                if simpleRVWordList[rvIx+2] == rvWords[2]:
                                    matchedRvWordCount += 1
                                    dPrint( 'Info', DEBUGGING_THIS_MODULE, f"          Matched 3/{len(rvWords)} @ {rvIx+2} with '{rvVerseWordList[rvIx+2]}' from '{rvWordStr}'")
                                    if matchedRvWordCount == len(rvWords): break # matched three words
                                    if rvIx < len(simpleRVWordList)-3:
                                        if simpleRVWordList[rvIx+3] == rvWords[3]:
                                            matchedRvWordCount += 1
                                            dPrint( 'Info', DEBUGGING_THIS_MODULE, f"          Matched 4/{len(rvWords)} @ {rvIx+3} with '{rvVerseWordList[rvIx+3]}' from '{rvWordStr}'")
                                            if matchedRvWordCount == len(rvWords): break # matched four words
            else: # no match (no break from above/inner loop)
                continue # in the outer loop
            dPrint( 'Info', DEBUGGING_THIS_MODULE, f"    matchWordsManually group2 {BBB} {c}:{v} matched {lvWord=} {rvWords=}" )
            # lvWord,lvWordNumber,lvWordRow = getLVWordRow( lvWordList[lvIx] )
            dPrint( 'Info', DEBUGGING_THIS_MODULE, f"matchWordsManually group2 is adding a number to RV {rvWords} from '{lvWord}' at {BBB} {c}:{v} {rvIx=}")
            for rvWord in rvWords:
                result = addNumberToRVWord( BBB, c,v, rvWord, lvWordNumber )
                if result:
                    numAdded += 1
                else:
                    logging.warning( f"Got addNumberToRVWord( {BBB} {c}:{v} '{rvWord}' {lvWordNumber} ) result = {result}" )
                # why_did_we_fail
    return numAdded,numNS
# end of connect_OET-RV_words_via_OET-LV.doGroup1


def getLVWordRow( wordWithNumber:str ) -> Tuple[str,int,List[str]]:
    """
    """
    fnPrint( DEBUGGING_THIS_MODULE, f"getLVWordRow( {wordWithNumber} )" )
    assert '¦' in wordWithNumber

    try: word,wordNumber = wordWithNumber.split( '¦' ) # Gives a ValueError if the wordNumber separator character is missing
    except ValueError:
        raise WordNumberError( f"Failed to split-off word number from {wordWithNumber=}" )
    # assert word.isalpha(), f"Non-alpha '{word}'" # not true, e.g., from 'Yaʸsous/(Yəhōshūˊa)¦21754'
    try: wordNumber = int( wordNumber )
    except ValueError:
        logging.critical( f"getLVWordRow() got non-number '{wordNumber}' from '{wordWithNumber}'" )
        wordNumber = getLeadingInt( wordNumber )
    assert wordNumber < len( state.wordTable )
    wordRow = state.wordTable[wordNumber]
    dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"'{word}' {wordRow}" )
    return word,wordNumber,wordRow
# end of connect_OET-RV_words_via_OET-LV.getLVWordRow


ndStartMarker, ndEndMarker = '\\nd ', '\\nd*'
def addNumberToRVWord( BBB:str, c:int,v:int, word:str, wordNumber:int ) -> bool | None:
    """
    Go through the RV USFM for BBBB and find the lines for c:v (which comes from Original/OET-LV verse numbering)

    Then try to find the word in the line.

    If there's only one word that it can be,
        then append the word number
        and also surround it with a nomina sacra span if necessary
    """
    fnPrint( DEBUGGING_THIS_MODULE, f"addNumberToRVWord( {BBB} {c}:{v} '{word}' {wordNumber} )" )
    assert isinstance( wordNumber, int )
    assert '¦' not in word
    if BBB=='MAT' and v==1: print( word )

    NT = BibleOrgSysGlobals.loadedBibleBooksCodes.isNewTestament_NR( BBB )
    havePsalmTitles = BibleOrgSysGlobals.loadedBibleBooksCodes.hasPsalmTitle( BBB, str(c) )
    desiredV = (v-1) if havePsalmTitles and v>1 else v

    if NT:
        if wordNumber in (143_176,143_692,149_461,150_257): return None # Temp HEB 1:6, 1 Pet (nd gets put inside add field).................................................................................
    else:
        if wordNumber in (252_390,): return None # Temp PSA 54:1 (v1 gets put into d field).................................................................................

    C = V = None
    foundChapter = foundVerse = False
    for n,line in enumerate( state.rvESFMLines[:] ): # iterate through a copy
        try: marker, rest = line.split( ' ', 1 )
        except ValueError: marker, rest = line, '' # Only a marker
        dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"addNumberToRVWord A searching {BBB} {C}:{V} {marker}='{rest}'" )
        if marker in ('\\s1','\\s2','\\s3','\\r','\\rem') or not rest:
            continue # Skip these fields (so we don't add word numbers to headings, etc.)
        if marker == '\\c':
            C = int(rest)
            if C > c: return False # Gone too far
            if C == c: foundChapter = True
        elif foundChapter and marker == '\\v':
            dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"addNumberToRVWord B searching {BBB} {C}:{V} {marker}='{rest}'")
            Vstr, rest = rest.split( ' ', 1 )
            try: V = int(Vstr)
            except ValueError: # might be a range like 21-22
                V = int(Vstr.split('-',1)[0])
            foundVerse = C==c and V==desiredV
        elif foundChapter and marker == '\\d':
            dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"addNumberToRVWord D searching {BBB} {C}:{V} {marker}='{rest}'")
            assert havePsalmTitles or BBB=='HAB', f"addNumberToRVWord( {BBB} {c}:{v} {word=} {havePsalmTitles=} {marker=} {rest=}"
            foundVerse = C==c and desiredV==1
        if foundVerse:
            wholeWordRegexStr = f'\\b{word}\\b'
            allWordMatches = [match for match in re.finditer( wholeWordRegexStr, line )]
            if len(allWordMatches) == 1:
                match = allWordMatches[0]
                dPrint( 'Info', DEBUGGING_THIS_MODULE, type(allWordMatches), type(match), match )
                assert match.group(0) == word
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  Found {word=} {line=}" )
                wordRow = state.wordTable[wordNumber]
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  Found {word=} {line=} {wordRow=}" )
                addNominaSacra = False
                if NT and 'N' in wordRow[state.wordTableHeaderList.index('GlossCaps')]: # Check that the RV doesn't already have it marked (with /nd)
                                      #   (This can happen after word numbers are deleted.)
                    dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"  Have NS on {word=} {line[match.start()-6:match.start()]=} {line[match.end():match.end()+6]=} {line=}" )
                    if (match.end()==len(line) or not line[match.end()]=='¦') \
                    and not line[match.end():match.end()+4] == '\\nd*' \
                    and not line[match.end():match.end()+5] == '\\+nd*':
                        addNominaSacra = True
                        dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  Adding NS on {word=} {line[match.start()-6:match.start()]=} {line[match.end():match.end()+6]=} {line=}" )

                try:
                    if line[match.end()] == '¦': # next character after word
                        logging.warning( f"Tried to append second number to {BBB} {C}:{V} {marker} '{line[match.start():match.end()]}' -> '{word}¦{wordNumber}'" )
                        # already_numbered_error
                        return False
                    elif line[match.end()] == "'": # next character after abbreviated word(s) like "they're"
                        logger = logging.critical if DEBUGGING_THIS_MODULE else logging.error
                        logger( f"Tried to append number inside abbreviated word(s) {BBB} {C}:{V} {marker} '{line[match.start():match.end()]}' (from '{line[match.start():match.end()+5]}') -> '{word}¦{wordNumber}'" )
                        # abbreviated_word_error
                        return False
                    elif addNominaSacra and line[match.end():].startswith( ' \\add*'): # we're inside a \\add field
                        logger = logging.critical if DEBUGGING_THIS_MODULE else logging.error
                        logger( f"Tried to append nomina sacra inside added word(s) {BBB} {C}:{V} {marker} '{line[match.start():match.end()]}' (from '{line[match.start():match.end()+5]}') -> '{word}¦{wordNumber}'" )
                        # nd_inside_add_error
                        return False
                    else: # seems all ok
                        state.rvESFMLines[n] = f'''{line[:match.start()]}{ndStartMarker if addNominaSacra else ''}{word}¦{wordNumber}{ndEndMarker if addNominaSacra else ''}{line[match.end():]}'''
                        # print( f"{word=} {line=}" )
                        dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  addNumberToRVWord() added ¦{wordNumber}{' and nomina sacra' if addNominaSacra else ''} to '{word}' in OET-RV {BBB} {c}:{v}" )
                        return True
                except IndexError: # if the word is at the END OF THE LINE
                    assert line.endswith( word )
                    state.rvESFMLines[n] = f'''{line[:-len(word)]}{ndStartMarker if addNominaSacra else ''}{word}¦{wordNumber}{ndEndMarker if addNominaSacra else ''}'''
                    dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  addNumberToRVWord() added ¦{wordNumber}{' and nomina sacra' if addNominaSacra else ''} to final '{word}' in OET-RV {BBB} {c}:{v}" )
                    return True
            else:
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  addNumberToRVWord {BBB} {c}:{v} '{word}' found {len(allWordMatches)=}" )
# end of connect_OET-RV_words_via_OET-LV.addNumberToRVWord


if __name__ == '__main__':
    # Configure basic Bible Organisational System (BOS) set-up
    parser = BibleOrgSysGlobals.setup( PROGRAM_NAME, PROGRAM_VERSION )
    BibleOrgSysGlobals.addStandardOptionsAndProcess( parser, exportAvailable=False )

    main()

    BibleOrgSysGlobals.closedown( PROGRAM_NAME, PROGRAM_VERSION )
# end of connect_OET-RV_words_via_OET-LV.py
