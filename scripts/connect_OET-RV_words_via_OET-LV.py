#!/usr/bin/env -S uv run
# -\*- coding: utf-8 -\*-
# SPDX-License-Identifier: MPL-2.0
#
# connect_OET-RV_words_via_OET-LV.py
#
# Script to connect OET-RV words with OET-LV words that have word numbers.
#
# Copyright (C) 2023-2026 Robert Hunt
# Author: Robert Hunt <Freely.Given.org+OET@gmail.com>
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Every word in the OET-LV has a word number tag suffixed to it,
    which connects it back to / aligns it with the Hebrew or Greek word it is translated from.

This script attempts to deduce how some of those same words are translated in the OET-RV
    and automatically connect them with the same word number tag.

It does have the potential to make wrong connections that will need to be manually fixed
        when the rest of the OET-RV words are aligned,
    but hopefully this script is relatively conservative
        so that the number of wrong alignments is not huge.

Specialised \\add spans:
    Normal character markers start with a backslash,
        but embedded character markers (often inside a '\\wj ' words-of-Jesus span)
            must have a + character after the backslash for both the opening and the closing marker.
    '\\add ' spans must be closed by '\\add*' markers.
        '\\+add ' spans must be closed by '\\+add*' markers.
    Formats are described at
        ../../OpenEnglishTranslation-website/src/pages/Resources/Formats.astro
    Pure '\\add ' or '\\+add ' or '\\add ?' or '\\+add ?' spans:
        Any existing word numbers should be removed.
        No new word numbers should be added to these spans.
        Words inside these spans should not be included in word linking statistics.
    Pronoun referrent '\\add @' or '\\+add @' or '\\add ?@' or '\\+add ?@' spans:
        Expect the proper noun or fuller description in the OET-RV
            to match a pronoun or simpler description like 'the one' in the OET-LV.
    Pronoun substitution '\\add *' or '\\+add *' or '\\add ?*' or '\\+add ?*' spans:
        Expect the pronoun or simpler description in the OET-RV
            to match a proper noun or fuller description in the OET-LV.
    Implied person or object '\\add >' or '\\+add >' or '\\add ?>' or '\\+add ?>' spans:
        As these are implied by the context and by the previous word in the sentence (often an article),
            then they should be assigned the same word number as the word that they're implied from.
    Added ownership '\\add &' or '\\+add &' or '\\add ?&' or '\\+add ?&' spans:
        In this case 'the hand' might become '\\add &his\\add* hand'.
        and 'followers' might become '\\add &his\\add* followers'.
        If there's a matching article present, then the OET-RV possessive pronoun
            can be linked to the word number of that OET-LV article.
    Elided '\\add ≡' or '\\+add ≡' or '\\add ?≡' or '\\+add ?≡' spans:
        If the original text that was implied here and then formally reinstated
            can be found earlier in the same verse or in the previous verse,
                then it can be given those matching word number(s).
        TODO: This requires an update in word number checking
            so that a lower word number (from a previous verse) can be allowed in an elided segment.
    Reworded '\\add ≈' or '\\+add ≈' or '\\add ?≈' or '\\+add ?≈' spans:
        Can be matched to OET-LV words, but more difficult expected.

TODO: This script makes wrong cross-connections between different verses where versification issues apply
        but that will eventually be fixed in BibleOrgSys (not here).


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
    2025-12-12 Remove "failed on" warnings for common word 'to'
    2025-12-13 Add 'fast' flag, added 'heavenly'
    2025-12-17 Add multiprocessing for converting each book (although seems no real time advantange)
    2026-02-24 Added more checking of consecutive opening and closing speech marks
    2026-04-23 Added more assert checks to catch Rust BOS faults
    2026-05-09 Switched to Rust bos_books_codes_py
    2026-05-12 Do more checking before adding NS nd markup
    2026-05-14 Switched to Rust bible_transliterations
    2026-06-11 Handle new % (changed person) \\add format
    2026-06-30 Added verb sets (but they're not fully utilised yet)
    2026-08-19 Allow ../ in lines (used in USFM jmp fields)
    2026-08-23 Added checking for doubled spaces around USFM close character marker fields
    2026-09-04 Don't add word numbers to words that are inside plain (straight) \add spans
    2026-09-25 Remove any existing word numbers from inside plain (straight) \add spans on load
    2026-09-25 Allow word numbers in the new \add !(SomeName)\add* spans
    2026-09-26 Added matchVerbSets() to connect different forms of the same verb (e.g., 'untie' to 'untying')
    2026-09-28 Use the 'Explained' decisions in OET-RV_names_table.tsv when matching proper nouns (e.g., 'Yerushalem')
    2026-09-28 Also treat plain '\\+add ...\\+add*' spans like plain '\\add ...\\add*' spans (no word numbers)
    2026-09-28 Added matchWordsInOrder() to connect words using left-to-right clause order (reversed for '⇔' verses)
    2026-09-28 Remove word numbers from inside straight '\\add'/'\\+add' spans in ALL books on every run (even 'fast'), and report it
    2026-09-28 Use the '≈' (reworded) and '#' (changed number) '\\add' span codes to connect more words (via exposeMatchedAddSpans() and matchWordsWithChangedNumbers())
    2026-09-28 Use the '@' '*' '%' '&' (pronoun/name/owner) and '≡' (repeated) codes too (via matchWordsBesideLvAnchor() and matchRepeatedWords()), and connect the OET-LV alternative names via matchNamesViaAltNames()
    2026-09-29 Connect both the OET-RV name and the traditional name in its '\\add !...\\add*' span to the same OET-LV name, including two-part names like 'John Mark' (via matchNamesViaTraditionalNames(), which replaces matchNamesViaAltNames())
    2026-09-29 Pass the exposed codes to splitExposedAddSpan() and keep exposed punctuation codes out of the word cleanup, so that the '!' code (which is also sentence punctuation) survives to be reported; add the traditional names from OET-RV_names_table.tsv to the OET-LV name spellings so that 'John' can match 'Yōannaʸs'
    2026-09-29 Stop getNameWordsBeforeSpan() at a word that belongs to another '\\add' span, so that we no longer sweep up an unrelated earlier name across e.g. the 'rebuilt' of 'from Beyt-El \\add ≈rebuilt\\add* Yeriho \\add !(Jericho)\\add*' and give it Jericho's word number
    2026-09-29 Removed the no longer productive NAME_ADJUSTMENT_TABLE
    2026-09-29 Report what percentage of the words have word numbers (via countWordsAndWordNumbers() and reportWordNumberPercentage()), for the OT, the NT and the whole Bible, or for the individual book(s) in 'fast' mode
    2026-09-30 Look up the OET-RV name spellings in the OET-LV name command tables without the
        extras that those tables carry, i.e. ignore the '\\add ...\\add*' gloss helpers and the '¦'
        word numbers, and register the last plain word of each '/' or '(' alternative as well, so that
        e.g. the OET-LV 'Farisaios¦_\add (religious leaders)\add*' can be the OET-RV 'Pharisee'
    2026-09-30 Keep a hyphenated word that isn't capitalised as the one word that the OET-RV and the
        OET-LV both use (e.g. 'empty-handed'), while still splitting a capitalised one (e.g. 'Yahweh-nissi')
    2026-09-30 Connect a short word that is exactly the same on both sides (MIN_EXACT_MATCH_WORD_LENGTH
        = 2, e.g. the OET-RV 'put' of Mark 12:1).  This used to be 3, and matchWordsInOrder() also
        used to skip the little English function words that the translators have deliberately left
        unnumbered (LITTLE_FUNCTION_WORDS, now kept only on record).  The order-preserving alignment
        and its every-alignment-agrees test turned out to be selective enough that we can now number
        the little words too, which connected 62,601 more OET-RV words across the whole Bible
        (197,116 of 933,964 = 21.1% before, 259,706 = 27.8% after)
    2026-09-30 Connect an OET-RV word to an OET-LV word that means the same thing but is a different
        word (EQUIVALENT_LV_RV_WORDS, e.g. the OET-RV 'Whenever' against the OET-LV 'wherever'), and
        let a capitalised OET-LV word take part when we have such a synonym for it
    2026-09-30 Let matchWordsInOrder() use two different OET-LV words that share one word number
        (e.g. the OET-LV 'put¦32436' and 'around¦32436' of Mark 12:1), while still skipping an OET-LV
        word that the verse gives exactly the same word and number twice
    2026-09-30 Give addNumberToRVWord() the OET-RV word as the OET-RV really spells it (via
        unSimplifyRVWord()), because it searches for that spelling, so that a capitalised OET-RV word
        such as the 'Whenever' of Mark 9:18 is no longer silently skipped
    2026-09-30 matchOurListedSimpleWords() now skips on to the next word instead of giving up on the
        whole verse when one listed word doesn't match, which is what it meant to do
    2026-09-30 Added a translator-editable table OET-RV_wordPhrases_table.tsv for OET-RV phrases of
        more than one English word that stand for just ONE OET-LV word (e.g. the OET-RV 'you all' for
        the OET-LV 'you_all', and the OET-RV 'young donkey' for the OET-LV 'colt'), and give every
        word of the OET-RV phrase that one OET-LV word number (via loadOETRVWordPhraseTable(),
        matchWordPhrases() and addNumberToRVPhrase())
    2026-09-30 addNumberToRVPhrase() only goes ahead when the phrase occurs exactly once in the
        unnumbered text of the verse, and refuses a phrase whose words already carry a different word
        number, so that a half-connected phrase (e.g. Mark 8:2 'have you all got') is finished off
        with the number that is already there
    2026-10-04 Names in the OET-RV now match via a normalised name index (normalizeNameKey +
        splitNameKey + namePartsIndex built by loadHebGrkNameTables(), and baseNameInCandidates())
        which strips diacritics/macrons/superscripts and splits 'Yəhūdāh/(Judah)' into parts,
        so e.g. the OET-RV 'Yeshua' can match the OET-LV 'Yaʸsous/(Yəhōshūˊa)'.  Also:
        - treat two-column rows of OET-RV_names_table.tsv as candidates as well (not just the 'Y' rows),
          and feed them into rvNameCandidates so that the name command tables can use them
        - treat 'YHWH' in the OET-LV as the OET-RV 'Yahweh'/'LORD' (explicitly added in
          loadHebGrkNameTables())
        - let matchIdenticalProperNouns() connect identical capitalised words in equal lists
        - let matchWordsInOrder() also match words that differ by an inflectional ending of
          up to three letters beyond the five-letter prefix (e.g. RV 'master' with LV 'masters')
        - greatly extended the contraction map in RV_SINGLE_WORDS_FROM_LV_WORD_STRINGS
    2026-10-06 Greatly expanded SIMPLE_VERB_SETS by comparing OET-RV and OET-LV NT verses
        to find verbs where a different tense/form is used on the two sides, so that
        matchVerbSets() can connect e.g. the RV 'warm' with the LV 'warming', or the RV 'dips'
        with the LV 'dipping'
    2026-10-06 Added the first OT-specific verb sets (play, provoke, slip, wean) after running the
        same OET-RV against OET-LV OT word-table (Morphology 'V...') analysis
    2026-10-06 Removed the conservative "only Messiah/Yeshua/God" nomina sacra allow-list, so that
        a genuine OET-LV nomina sacra match (e.g. the RV "God's¦" at Mrk 8:33, 9:1, 7:9, 7:13)
        now always gets its \\nd ... \\nd* (or \\+nd ... \\+nd*) markup; the CRITICAL messages are gone
    2026-10-06 Added NT noun/adjective singular/plural variant pairs to
        RV_SINGLE_WORDS_FROM_LV_WORD_STRINGS (e.g. ('fish','fishes'), ('body','bodies'),
        ('sign','signs'), ('authority','authorities') ...), which connected ~40 more OET-RV
        words in Mark.
"""
from gettext import gettext as _
from typing import List, Tuple, Optional
from pathlib import Path
from collections import defaultdict
import logging
import re
import multiprocessing
import unicodedata

from BibleOrgSys import BibleOrgSysGlobals
from BibleOrgSys.BibleOrgSysGlobals import vPrint, fnPrint, dPrint
from BibleOrgSys.Formats.ESFMBible import ESFMBible
from bible_organisational_system import getPositiveLeadingInt, InternalBibleEntryList
import bos_books_codes_py
from bible_transliterations import transliterate_Hebrew, transliterate_Greek


LAST_MODIFIED_DATE = '2026-10-06' # by RJH
SHORT_PROGRAM_NAME = "connect_OET-RV_words_via_OET-LV"
PROGRAM_NAME = "Connect OET-RV words to OET-LV word numbers"
PROGRAM_VERSION = '1.0.3'
PROGRAM_NAME_VERSION = f'{SHORT_PROGRAM_NAME} v{PROGRAM_VERSION}'

DEBUGGING_THIS_MODULE = False


project_folderpath = Path(__file__).parent.parent # Find folders relative to this module
# FG_folderpath = project_folderpath.parent # Path to find parallel Freely-Given.org repos
OET_LV_ESFM_InputFolderPath = project_folderpath.joinpath( 'derivedTexts/' )
OET_LV_OT_ESFM_InputFolderPath = OET_LV_ESFM_InputFolderPath.joinpath( 'auto_edited_OT_ESFM/' )
OET_LV_NT_ESFM_InputFolderPath = OET_LV_ESFM_InputFolderPath.joinpath( 'auto_edited_VLT_ESFM/' )
OET_RV_ESFM_FolderPath = project_folderpath.joinpath( 'translatedTexts/ReadersVersion/' )
assert OET_LV_OT_ESFM_InputFolderPath.is_dir()
assert OET_LV_NT_ESFM_InputFolderPath.is_dir()
assert OET_RV_ESFM_FolderPath.is_dir()

OET_RV_NAMES_TABLE_FILEPATH = OET_RV_ESFM_FolderPath.joinpath( 'OET-RV_names_table.tsv' )
OET_RV_NAMES_TABLE_HEADER = 'TraditionalName\tRVName\tExplained\tComment'
assert OET_RV_NAMES_TABLE_FILEPATH.is_file()
OET_RV_WORD_PHRASES_TABLE_FILEPATH = OET_RV_ESFM_FolderPath.joinpath( 'OET-RV_wordPhrases_table.tsv' )
OET_RV_WORD_PHRASES_TABLE_HEADER = 'LVWord\tRVWords\tEnabled\tComment'
OT_NameTable_Filepath = Path( __file__ ).parent.joinpath( 'ScriptedOTUpdates/restoreNames.commandTable.tsv' )
NT_OT_NameTable_Filepath = Path( __file__ ).parent.joinpath( 'ScriptedVLTUpdates/OTNames.commandTable.tsv' )
NT_NameTable_Filepath = Path( __file__ ).parent.joinpath( 'ScriptedVLTUpdates/NTNames.commandTable.tsv' )
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
    'altars','altar',
        'ambassadors','ambassador',
        'ancestors','ancestor', 'angels','angel', 'anger', 'animals','animal', 'ankles','ankle',
        'assemblies','assembly',
        'authorities','authority', 'axes','axe',
    'babies','baby', 'badger', 'bait', 'battles','battle',
        'beds','bed', 'beginnings','beginning', 'belts','belt',
        'birds','bird', 'birth',
        'blood', 'blossoms','blossom',
        'boats','boat', 'bodies','body', 'boys','boy',
        'bread', 'breasts','breast', 'branches','branch', 'brothers','brother',
        'bulls','bull', 'burials','burial',
    'camels','camel', 'camp',
        'chairs','chair', 'chambers','chamber', 'chariots','chariot', 'chests','chest', 'children','child',
        'cities','city',
        'coats','coat', 'collectors','collector', 'commands','command', 'companions','companion',
            'cords','cord', 'corners','corner',
            'councils','council', 'courtyards','courtyard', 'courts','court', 'countries','country', 'cows','cow',
        'craftsmen','craftsman', 'crowds','crowd',
        'cushion',
    'danger', 'darkness', 'daughters','daughter', 'days','day',
        'death', 'deceivers','deceiver', 'deer', 'dens','den',
        'donkeys','donkey', 'doors','door', 'doves','dove', 'dreams','dream', 'dyes','dye',
    'eagles','eagle', 'ears','ear',
        'entrance',
        'eyes','eye',
        'exorcists','exorcist',
    'faces','face', 'faith', 'farmers','farmer', 'fathers','father',
        'fevers','fever',
        'fields','field', 'figs','fig', 'fingers','finger', 'fires','fire', 'fish',
        'flowers','flower',
        'followers','follower', 'feet','foot', 'fords','ford',
        'friends','friend', 'fruits','fruit',
    'gateways','gateway', 'gates','gate',
        'generations','generation',
        'gifts','gift', 'girls','girl',
        'goats','goat', 'gods','god', 'gold',
        'grace', 'grains','grain', 'grapes','grape', 'grass',
            'greed',
    'hairs','hair', 'handkerchiefs','handkerchief', 'hands','hand', 'happiness', 'hare', 'harvests','harvest',
        'heads','head', 'hearts','heart', 'heavens','heaven', 'hedgehogs','hedgehog',
        'hides','hide',
        'homes','home', 'honey', 'hooves','hoof', 'horsemen', 'horses','horse', 'hours','hour', 'houses','house',
        'husbands','husband',
        'hyenas','hyena',
    'idols','idol', 'incense', 'ink',
    'jails','jail', 'joy', 'judgements','judgement',
    'kidneys','kidney', 'kings','king', 'kingdoms','kingdom', 'kisses','kiss',
    'lambs','lamb', 'lands','land', 'languages','language',
        'leaders','leader', 'leather', 'letters','letter',
        'life', 'lights','light', 'lines','line', 'lions','lion', 'lips','lip', 'liver',
        'loaf','loaves', 'locusts','locust',
    'man','men', 'markets','market', 'masters','master',
        'mercy', 'messages','message', 'meetings','meeting',
        'milk',
        'moon', 'mothers','mother', 'mouths','mouth',
    'names','name', 'nations','nation',
        'neighbours','neighbour', 'nests','nest', 'nets','net', 'news',
        'nobles','noble', 'noises','noise', 'noses','nose',
    'offerings','offering', 'officers','officer', 'officials','official',
        'oil',
        'ostriches','ostrich',
        'owls','owl',
    'palms','palm',
        'peace', 'pens','pen', 'people','person',
        'pig',
        'places','place',
        'powers','power',
        'prayers','prayer',
            'priests','priest', 'princes','prince', 'prisons','prison',
            'promises','promise'
    'queens','queen',
    'rabbit', 'ravens','raven',
        'rivers','river',
        'roads','road', 'robes','robe', 'robbers','robber', 'rocks','rock', 'roofs','roof', 'rooms','room', 'ropes','rope',
        'ruins','ruin', 'rulers','ruler', 'rust',
    'sandals','sandal', 'sashes','sash',
        'scrolls','scroll',
        'sea', 'servants','servant', 'services','service',
        'shame', 'sheep', 'shepherds','shepherd', 'ships','ship', 'shores','shore', 'shrines','shrine',
        'sides','side', 'signs','sign', 'silver', 'silversmiths','silversmith', 'sinners','sinner', 'sins','sin', 'sisters','sister', 'sky', 'slaves','slave',
        'soldiers','soldier', 'sons', 'souls','soul', 'spirits','spirit',
        'stars','star', 'stones','stone', 'straps','strap', 'streams','stream', 'streets','street', 'strength', 'sun', 'swords','sword',
    'tables','table', 'taxes','tax',
        'teachers','teacher', 'temples','temple', 'tent', 'testimonies','testimony',
        'theatres','theatre', 'thieves','thief', 'things','thing', 'threats','threat', 'thrones','throne', 'thumbs','thumb',
        'times','time',
        'toes','toe', 'tombs','tomb', 'tongues','tongue', 'towers','tower', 'towns','town',
        'trees','tree', 'truth',
        'tunics','tunic', 'turban',
    'valuation', 'vines','vine', 'visions','vision',
    'waists','waist', 'walls','wall', 'wars','war', 'waters','water', 'ways','way',
        'weapons','weapon', 'weeks','week',
        'wilderness', 'widows','widow', 'wife','wives', 'windows','window', 'winds','wind',
        'woman','women', 'words','word', 'workers','worker',
    'years','year',
        'ages','age', 'chiefs','chief', 'elders','elder', 'earths','earth',
        'laws','law', 'messengers','messenger',
        'nights','night', 'prophets','prophet', 'voices','voice',
        'worlds','world', 'apprentices','apprentice',
        'rest', 'righteousness',
    # Singular/plural noun entries added 2026-10-06 (NT and OT)
    'adulteries', 'adultery', 'area', 'areas', 'armies', 'army',
    'arrow', 'arrows', 'back', 'backs', 'bank', 'banks',
    'barn', 'barns', 'beard', 'beards', 'bellies', 'belly',
    'belong', 'belongs', 'blessing', 'blessings', 'bone', 'bones',
    'border', 'borders', 'bowl', 'bowls', 'bridle', 'bridles',
    'camps', 'cart', 'carts', 'case', 'cases', 'cedar',
    'cedars', 'chain', 'chains', 'cheek', 'cheeks', 'clan',
    'clans', 'cloud', 'clouds', 'coal', 'coals', 'commander',
    'commanders', 'compassion', 'compassions', 'complaint', 'complaints', 'conscience',
    'consciences', 'contribution', 'contributions', 'corpse', 'corpses', 'creature',
    'creatures', 'curtain', 'curtains', 'cypress', 'cypresses', 'design',
    'designs', 'desire', 'desires', 'dispute', 'disputes', 'duties',
    'duty', 'edge', 'edges', 'enemies', 'enemy', 'escape',
    'escapees', 'farm', 'farms', 'fishes', 'flame', 'flames',
    'flesh', 'fleshes', 'flock', 'flocks', 'food', 'foods',
    'foundation', 'foundations', 'frame', 'frames', 'grave', 'graves',
    'grumbling', 'grumblings', 'harp', 'harps', 'heap', 'heaps',
    'horn', 'horns', 'human', 'humans', 'incenses', 'inside',
    'insides', 'instruction', 'instructions', 'island', 'islands', 'lamp',
    'lamps', 'lightning', 'lightnings', 'like', 'likes', 'livestock',
    'livestocks', 'load', 'loads', 'lust', 'lusts', 'male',
    'males', 'mark', 'marks', 'meat', 'meats', 'mile',
    'miles', 'mind', 'minds', 'month', 'months', 'moth',
    'moths', 'mound', 'mounds', 'mountain', 'mountains', 'mule',
    'mules', 'multitude', 'multitudes', 'murder', 'murders', 'neck',
    'necks', 'need', 'needs', 'oath', 'oaths', 'obligation',
    'obligations', 'pain', 'pains', 'pair', 'pairs', 'parable',
    'parables', 'part', 'parts', 'pasture', 'pastureland', 'pasturelands',
    'pastures', 'path', 'paths', 'peoples', 'persecution', 'persecutions',
    'pipe', 'pipes', 'pomegranate', 'pomegranates', 'present', 'presents',
    'rain', 'rains', 'reed', 'reeds', 'region', 'regions',
    'root', 'roots', 'rubies', 'ruby', 'rule', 'rules',
    'sack', 'sacks', 'sale', 'sales', 'scripture', 'scriptures',
    'seed', 'seeds', 'shield', 'shields', 'shoulder', 'shoulders',
    'sickness', 'sicknesses', 'skill', 'skills', 'skin', 'skins',
    'song', 'songs', 'spice', 'spices', 'staff', 'staffs',
    'step', 'steps', 'suffering', 'sufferings', 'tail', 'tails',
    'teaching', 'teachings', 'temptation', 'temptations', 'tenant', 'tenants',
    'tents', 'terror', 'terrors', 'thorn', 'thorns', 'thunder',
    'thunders', 'tool', 'tools', 'tradition', 'traditions', 'trial',
    'trials', 'tribe', 'tribes', 'trouble', 'troubles', 'twin',
    'twins', 'unbeliever', 'unbelievers', 'village', 'villages', 'wage',
    'wages', 'wave', 'waves', 'weakness', 'weaknesses', 'wildernesss',
    'will', 'wills', 'wine', 'wines', 'wineskin', 'wineskins',
    'witness', 'witnesses', 'worries', 'worry',
    )
assert len(set(SIMPLE_NOUNS)) == len(SIMPLE_NOUNS) # Check for accidental duplicates
verbalNouns = ('accusations','accusation',
               'behaviour',
               'compassion', 'confessions','confession', 'confidence',
                'deception', 'decisions','decision', 'declarations','declaration', 'dedication', 'discussions','discussion', 'distribution', 'destruction',
                'fellowship', 'forgiveness', 'fulfilment',
                'immersion', 'invasion',
                'punishment',
                'rebellion', 'repentance', 'restoration',
                'service','servitude',
                'utterances','utterance',
                )
assert len(set(verbalNouns)) == len(verbalNouns) # Check for accidental duplicates
# Verbs often don't work because we use the tenses differently between OET-RV and OET-LV/Greek
SIMPLE_VERB_SETS = (
    ('abandoned', 'abandoning', 'abandons', 'abandon'),
    ('abided', 'abiding', 'abides', 'abide'),
    ('accepted', 'accepting', 'accepts', 'accept'),
    ('acted', 'acting', 'acts', 'act'),
    ('advanced', 'advancing', 'advances', 'advance'),
    ('allowed', 'allowing', 'allows', 'allow'),
    ('anointed', 'anointing', 'anoints', 'anoint'),
    ('answered', 'answering', 'answers', 'answer'),
    ('appointed', 'appointing', 'appoints', 'appoint'),
    ('arose', 'arisen', 'arising', 'arises', 'arise'),
    ('arrested', 'arresting', 'arrests', 'arrest'),
    ('ascended', 'ascending', 'ascends', 'ascend'),
    ('asked', 'asking', 'asks', 'ask'),
    ('assembled', 'assembling', 'assembles', 'assemble'),
    ('attracted', 'attracting', 'attracts', 'attract'),
    ('attacked', 'attacking', 'attacks', 'attack'),
    ('awoke', 'awoken', 'awaking', 'awakes', 'awake'),
    ('banished', 'banishing', 'banishes', 'banish'),
    ('bore', 'born', 'borne', 'bearing', 'bears', 'bear'),
    ('beat', 'beaten', 'beating', 'beats', 'beat'),
    ('became', 'become', 'becoming', 'becomes', 'become'),
    ('began', 'begun', 'beginning', 'begins', 'begin'),
    ('behaved', 'behaving', 'behaves', 'behave'),
    ('believed', 'believing', 'believes', 'believe'),
    ('bent', 'bending', 'bends', 'bend'),
    ('bound', 'binding', 'binds', 'bind'),
    ('bit', 'bitten', 'biting', 'bites', 'bite'),
    ('blessed', 'blessing', 'blesses', 'bless'),
    ('blew', 'blown', 'blowing', 'blows', 'blow'),
    ('bought', 'buying', 'buys', 'buy'),
    ('brought', 'bringing', 'brings', 'bring'),
    ('broke', 'broken', 'breaking', 'breaks', 'break'),
    ('bred', 'breeding', 'breeds', 'breed'),
    ('built', 'building', 'builds', 'build'),
    ('burned', 'burnt', 'burning', 'burns', 'burn'),
    ('buried', 'burying', 'buries', 'bury'),
    ('called', 'calling', 'calls', 'call'),
    ('came', 'coming', 'comes', 'come'),
    ('carried', 'carrying', 'carries', 'carry'),
    ('caught', 'catching', 'catches', 'catch'),
    ('caused', 'causing', 'causes', 'cause'),
    ('chased', 'chasing', 'chases', 'chase'),
    ('chose', 'chosen', 'choosing', 'chooses', 'choose'),
    ('claimed', 'claiming', 'claims', 'claim'),
    ('clung', 'clinging', 'clings', 'cling'),
    ('closed', 'closing', 'closes', 'close'),
    ('concealed', 'concealing', 'conceals', 'conceal'),
    ('confessed', 'confessing', 'confesses', 'confess'),
    ('consumed', 'consuming', 'consumes', 'consume'),
    ('cracked', 'cracking', 'cracks', 'crack'),
    ('crept', 'creeping', 'creeps', 'creep'),
    ('cried', 'crying', 'cries', 'cry'),
    ('cringed', 'cringes', 'cringe'),
    ('crowed','crowing','crows','crow'),
    ('cursed', 'cursing', 'curses', 'curse'),
    ('cut', 'cutting', 'cuts', 'cut'),
    ('dared', 'daring', 'dares', 'dare'),
    ('dealt', 'dealing', 'deals', 'deal'),
    ('deceived', 'deceiving', 'deceives', 'deceive'),
    ('decided', 'deciding', 'decides', 'decide'),
    ('declared', 'declaring', 'declares', 'declare'),
    ('defended', 'defending', 'defends', 'defend'),
    ('delivered', 'delivering', 'delivers', 'deliver'),
    ('departed', 'departing', 'departs', 'depart'),
    ('descended', 'descending', 'descends', 'descend'),
    ('deserted', 'deserting', 'deserts', 'desert'),
    ('destroyed', 'destroying', 'destroys', 'destroy'),
    ('did', 'done', 'doing', 'does', 'do'),
    ('died', 'dying', 'dies', 'die'),
    ('dug', 'digging', 'digs', 'dig'),
    ('discussed', 'discussing', 'discusses', 'discuss'),
    ('disowned', 'disowning', 'disowns', 'disown'),
    ('distributed', 'distributing', 'distributes', 'distribute'),
    ('dived', 'dove', 'diving', 'dives', 'dive'),
    ('dragged', 'dragging', 'drags', 'drag'),
    ('drew', 'drawn', 'drawing', 'draws', 'draw'),
    ('dreamed', 'dreamt', 'dreaming', 'dreams', 'dream'),
    ('drove', 'driven', 'driving', 'drives', 'drive'),
    ('drank', 'drunk', 'drinking', 'drinks', 'drink'),
    ('dwelled', 'dwelt', 'dwelling', 'dwells', 'dwell'),
    ('ate', 'eaten', 'eating', 'eats', 'eat'),
    ('embraced', 'embracing', 'embraces', 'embrace'),
    ('encouraged', 'encouraging', 'encourages', 'encourage'),
    ('ended', 'ending', 'ends', 'end'),
    ('enslaved', 'enslaving', 'enslaves', 'enslave'),
    ('entered', 'entering', 'enters', 'enter'),
    ('equipped', 'equipping', 'equips', 'equip'),
    ('existed', 'existing', 'exists', 'exist'),
    ('extended', 'extending', 'extends', 'extend'),
    ('failed', 'failing', 'fails', 'fail'),
    ('fell', 'fallen', 'falling', 'falls', 'fall'),
    ('fed', 'feeding', 'feeds', 'feed'),
    ('feared', 'fearing', 'fears', 'fear'),
    ('felt', 'feeling', 'feels', 'feel'),
    ('fought', 'fighting', 'fights', 'fight'),
    ('filled', 'filling', 'fills', 'fill'),
    ('found', 'finding', 'finds', 'find'),
    ('fled', 'fleeing', 'flees', 'flee'),
    ('flung', 'flinging', 'flings', 'fling'),
    ('flew', 'flown', 'flying', 'flies', 'fly'),
    ('fluttered', 'fluttering', 'flutters', 'flutter'),
    ('followed', 'following', 'follows', 'follow'),
    ('forbade', 'forbidden', 'forbidding', 'forbids', 'forbid'),
    ('forced', 'forcing', 'forces', 'force'),
    ('forgot', 'forgotten', 'forgetting', 'forgets', 'forget'),
    ('forgave', 'forgiven', 'forgiving', 'forgives', 'forgive'),
    ('formed', 'forming', 'forms', 'form'),
    ('forsook', 'forsaken', 'forsaking', 'forsakes', 'forsake'),
    ('froze', 'frozen', 'freezing', 'freezes', 'freeze'),
    ('gathered', 'gathering', 'gathers', 'gather'),
    ('gave', 'given', 'giving', 'gives', 'give'),
    ('got', 'gotten', 'getting', 'gets', 'get'),
    ('went', 'gone', 'going', 'goes', 'go'),
    ('governed', 'governing', 'governs', 'govern'),
    ('greeted', 'greeting', 'greets', 'greet'),
    ('grew', 'grown', 'growing', 'grows', 'grow'),
    ('had', 'having', 'has', 'have'),
    ('hung', 'hanged', 'hanging', 'hangs', 'hang'),
    ('harvested', 'harvesting', 'harvests', 'harvest'),
    ('hated', 'hating', 'hates', 'hate'),
    ('healed', 'healing', 'heals', 'heal'),
    ('heard', 'hearing', 'hears', 'hear'),
    ('held', 'holding', 'holds', 'hold'),
    ('helped', 'helping', 'helps', 'help'),
    ('hid', 'hidden', 'hiding', 'hides', 'hide'),
    ('hit', 'hitting', 'hits', 'hit'),
    ('honoured', 'honouring', 'honours', 'honour'),
    ('horrified', 'horrifying', 'horrifies', 'horrify'),
    ('hurt', 'hurting', 'hurts', 'hurt'),
    ('imitated', 'imitating', 'imitates', 'imitate'),
    ('immersed', 'immersing', 'immerses', 'immerse'),
    ('invaded', 'invading', 'invades', 'invade'),
    ('judged', 'judging', 'judges', 'judge'),
    ('kept', 'keeping', 'keeps', 'keep'),
    ('killed', 'killing', 'kills', 'kill'),
    ('kindled', 'kindling', 'kindles', 'kindle'),
    ('kissed','kissing','kisses','kiss'),
    ('knelt', 'kneeled', 'kneeling', 'kneels', 'kneel'),
    ('knew', 'known', 'knowing', 'knows', 'know'),
    ('laid', 'laying', 'lays', 'lay'),
    ('laughed', 'laughing', 'laughs', 'laugh'),
    ('led', 'leading', 'leads', 'lead'),
    ('leant', 'leaned', 'leaning', 'leans', 'lean'),
    ('leapt', 'leaped', 'leaping', 'leaps', 'leap'),
    ('learnt', 'learning', 'learns', 'learn'),
    ('left', 'leaving', 'leaves', 'leave'),
    ('lent', 'lending', 'lends', 'lend'),
    ('let', 'letting', 'lets', 'let'),
    ('lay', 'lain', 'lying', 'lies', 'lie'),
    ('lit', 'lighted', 'lighting', 'lights', 'light'),
    ('listened', 'listening', 'listens', 'listen'),
    ('lived', 'living', 'lives', 'live'),
    ('looked', 'looking', 'looks', 'look'),
    ('lost', 'losing', 'loses', 'lose'),
    ('loved', 'loving', 'loves', 'love'),
    ('lowered', 'lowering', 'lowers', 'lower'),
    ('made', 'making', 'makes', 'make'),
    ('magnified', 'magnifying', 'magnifies', 'magnify'),
    ('married', 'marrying', 'marries', 'marry'),
    ('meant', 'meaning', 'means', 'mean'),
    ('measured', 'measuring', 'measures', 'measure'),
    ('met', 'meeting', 'meets', 'meet'),
    ('mocked', 'mocking', 'mocks', 'mock'),
    ('mourned', 'mourning', 'mourns', 'mourn'),
    ('obeyed', 'obeying', 'obeys', 'obey'),
    ('offered', 'offering', 'offers', 'offer'),
    ('opened', 'opening', 'opens', 'open'),
    ('ordered', 'ordering', 'orders', 'order'),
    ('packed', 'packing', 'packs', 'pack'),
    ('paid', 'paying', 'pays', 'pay'),
    ('passed', 'passing', 'passes', 'pass'),
    ('persuaded', 'persuading', 'persuades', 'persuade'),
    ('poured', 'pouring', 'pours', 'pour'),
    ('practiced', 'practicing', 'practices', 'practice'),
    ('praised', 'praising', 'praises', 'praise'),
    ('prayed', 'praying', 'prays', 'pray'),
    ('prevailed', 'prevailing', 'prevails', 'prevail'),
    ('promised', 'promising', 'promises', 'promise'),
    ('prophesied', 'prophesying', 'prophesies', 'prophesy'),
    ('punished', 'punishing', 'punishes', 'punish'),
    ('purchased', 'purchasing', 'purchases', 'purchase'),
    ('purified', 'purifying', 'purifies', 'purify'),
    ('put', 'putting', 'puts', 'put'),
    ('quit', 'quitting', 'quits', 'quit'),
    ('raged', 'raging', 'rages', 'rage'),
    ('raised', 'raising', 'raises', 'raise'),
    ('ran', 'running', 'runs', 'run'),
    ('rang', 'rung', 'ringing', 'rings', 'ring'),
    ('rebelled', 'rebelling', 'rebels', 'rebel'),
    ('received', 'receiving', 'receives', 'receive'),
    ('recognised', 'recognising', 'recognises', 'recognise'),
    ('recovered', 'recovering', 'recovers', 'recover'),
    ('redeemed', 'redeems', 'redeem'),
    ('reigned', 'reigning', 'reigns', 'reign'),
    ('released', 'releasing', 'releases', 'release'),
    ('relented', 'relenting', 'relents', 'relent'),
    ('relied', 'relying', 'relies', 'rely'),
    ('remained', 'remaining', 'remains', 'remain'),
    ('remembered', 'remembering', 'remembers', 'remember'),
    ('reminded', 'reminding', 'reminds', 'remind'),
    ('removed', 'removing', 'removes', 'remove'),
    ('repaid', 'repaying', 'repays', 'repay'),
    ('repented', 'repenting', 'repents', 'repent'),
    ('reported', 'reporting', 'reports', 'report'),
    ('requested', 'requesting', 'requests', 'request'),
    ('rescued', 'rescuing', 'rescues', 'rescue'),
    ('respected', 'respecting', 'respects', 'respect'),
    ('restored', 'restoring', 'restores', 'restore'),
    ('restrained', 'restraining', 'restrains', 'restrain'),
    ('revealed', 'revealing', 'reveals', 'reveal'),
    ('rode', 'ridden', 'riding', 'rides', 'ride'),
    ('rose', 'risen', 'rising', 'rises', 'rise'),
    ('ruined', 'ruining', 'ruins', 'ruin'),
    ('said', 'saying', 'says', 'say'),
    ('sailed', 'sailing', 'sails', 'sail'),
    ('sang', 'sung', 'singing', 'sings', 'sing'),
    ('sank', 'sunk', 'sinking', 'sinks', 'sink'),
    ('sat', 'sitting', 'sits', 'sit'),
    ('sawed', 'sawn', 'sawing', 'saws', 'saw'),
    ('saw', 'seen', 'seeing', 'sees', 'see'),
    ('sought', 'seeking', 'seeks', 'seek'),
    ('seated', 'seating', 'seats', 'seat'),
    ('seduced', 'seducing', 'seduces', 'seduce'),
    ('sent', 'sending', 'sends', 'send'),
    ('served', 'serving', 'serves', 'serve'),
    ('set', 'setting', 'sets', 'set'),
    ('settled', 'settling', 'settles', 'settle'),
    ('sewed', 'sewn', 'sewing', 'sews', 'sew'),
    ('shook', 'shaken', 'shaking', 'shakes', 'shake'),
    ('shared', 'sharing', 'shares', 'share'),
    ('shaved', 'shaven', 'shaving', 'shaves', 'shave'),
    ('shone', 'shined', 'shining', 'shines', 'shine'),
    ('shot', 'shooting', 'shoots', 'shoot'),
    ('showed', 'shown', 'showing', 'shows', 'show'),
    ('shrank', 'shrunk', 'shrinking', 'shrinks', 'shrink'),
    ('shut', 'shutting', 'shuts', 'shut'),
    ('signalled', 'signalling', 'signals', 'signal'),
    ('sinned', 'sinning', 'sins', 'sin'),
    ('slapped','slapping','slaps','slap'),
    ('slew', 'slain', 'slaying', 'slays', 'slay'),
    ('slept', 'sleeping', 'sleeps', 'sleep'),
    ('slid', 'sliding', 'slides', 'slide'),
    ('slung', 'slinging', 'slings', 'sling'),
    ('slinked', 'slunk', 'slinking', 'slinks', 'slink'),
    ('slaughtered', 'slaughtering', 'slaughters', 'slaughter'),
    ('smelt', 'smelled', 'smelling', 'smells', 'smell'),
    ('sold', 'selling', 'sells', 'sell'),
    ('sowed', 'sown', 'sowing', 'sows', 'sow'),
    ('spoke', 'spoken', 'speaking', 'speaks', 'speak'),
    ('sped', 'speeding', 'speeds', 'speed'),
    ('spent', 'spending', 'spends', 'spend'),
    ('spilt', 'spilled', 'spilling', 'spills', 'spill'),
    ('spun', 'spinning', 'spins', 'spin'),
    ('spat', 'spitting', 'spits', 'spit'),
    ('split', 'splitting', 'splits', 'split'),
    ('spoilt', 'spoiled', 'spoiling', 'spoils', 'spoil'),
    ('spread', 'spreading', 'spreads', 'spread'),
    ('sprang', 'sprung', 'springing', 'springs', 'spring'),
    ('stayed', 'staying', 'stays', 'stay'),
    ('stole', 'stolen', 'stealing', 'steals', 'steal'),
    ('stood', 'standing', 'stands', 'stand'),
    ('stopped', 'stopping', 'stops', 'stop'),
    ('stretched', 'stretching', 'stretches', 'stretch'),
    ('struck', 'stricken', 'striking', 'strikes', 'strike'),
    ('strung', 'stringing', 'strings', 'string'),
    ('strived', 'strove', 'striven', 'striving', 'strives', 'strive'),
    ('strode', 'stridden', 'striding', 'strides', 'stride'),
    ('stuck', 'sticking', 'sticks', 'stick'),
    ('stung', 'stinging', 'stings', 'sting'),
    ('stank', 'stunk', 'stinking', 'stinks', 'stink'),
    ('stumbled', 'stumbling', 'stumbles', 'stumble'),
    ('succeeded', 'succeeding', 'succeeds', 'succeed'),
    ('suffered', 'suffering', 'suffers', 'suffer'),
    ('summoned', 'summoning', 'summons', 'summon'),
    ('supported', 'supporting', 'supports', 'support'),
    ('swore', 'sworn', 'swearing', 'swears', 'swear'),
    ('swept', 'sweeping', 'sweeps', 'sweep'),
    ('swelled', 'swollen', 'swelling', 'swells', 'swell'),
    ('swam', 'swum', 'swimming', 'swims', 'swim'),
    ('swung', 'swinging', 'swings', 'swing'),
    ('took', 'taken', 'taking', 'takes', 'take'),
    ('talked', 'talking', 'talks', 'talk'),
    ('taught', 'teaching', 'teaches', 'teach'),
    ('tore', 'torn', 'tearing', 'tears', 'tear'),
    ('told', 'telling', 'tells', 'tell'),
    ('testified', 'testifying', 'testifies', 'testify'),
    ('thought', 'thinking', 'thinks', 'think'),
    ('threw', 'thrown', 'throwing', 'throws', 'throw'),
    ('throve', 'thriven', 'thrived', 'thriving', 'thrives', 'thrive'),
    ('thrust', 'thrusting', 'thrusts', 'thrust'),
    ('trod', 'trodden', 'treading', 'treads', 'tread'),
    ('touched', 'touching', 'touches', 'touch'),
    ('travelled', 'travelling', 'travels', 'travel'),
    ('turned', 'turning', 'turns', 'turn'),
    ('understood', 'understanding', 'understands', 'understand'),
    ('united', 'uniting', 'unites', 'unite'),
    ('untied', 'untying', 'unties', 'untie'),
    ('woke', 'woken', 'waking', 'wakes', 'wake'),
    ('wore', 'worn', 'wearing', 'wears', 'wear'),
    ('wove', 'woven', 'weaving', 'weaves', 'weave'),
    ('wailed', 'wailing', 'wails', 'wail'),
    ('walked', 'walking', 'walks', 'walk'),
    ('wanted', 'wanting', 'wants', 'want'),
    ('warned', 'warning', 'warns', 'warn'),
    ('watched', 'watching', 'watches', 'watch'),
    ('watered', 'watering', 'waters', 'water'),
    ('weakened', 'weakening', 'weakens', 'weaken'),
    ('wept', 'weeping', 'weeps', 'weep'),
    ('withdrew', 'withdrawn', 'withdrawing', 'withdraws', 'withdraw'),
    ('withered', 'withering', 'withers', 'wither'),
    ('won', 'winning', 'wins', 'win'),
    ('wound', 'winding', 'winds', 'wind'),
    ('worked', 'working', 'works', 'work'),
    ('wrapped', 'wrapping', 'wraps', 'wrap'),
    ('wrote', 'written', 'writing', 'writes', 'write'),
    ('wrung', 'wringing', 'wrings', 'wring'),
    ('yelled', 'yelling', 'yells', 'yell'),
    ('yielded', 'yielding', 'yields', 'yield'),
    ('tested', 'testing', 'tests', 'test'),
    ('tempted', 'tempting', 'tempts', 'tempt'),
    ('cleansed', 'cleansing', 'cleanses', 'cleanse'),
    ('doubted', 'doubting', 'doubts', 'doubt'),
    ('boasted', 'boasting', 'boasts', 'boast'),
    ('rejoiced', 'rejoicing', 'rejoices', 'rejoice'),
    ('returned', 'returning', 'returns', 'return'),
    ('opposed', 'opposing', 'opposes', 'oppose'),
    ('wished', 'wishing', 'wishes', 'wish'),
    ('sacrificed', 'sacrificing', 'sacrifices', 'sacrifice'),
    # Added 2026-10-06 by comparing OET-RV and OET-LV NT verses to find different verb tenses
    ('accompanied', 'accompanying', 'accompanies', 'accompany'),
    ('accused', 'accusing', 'accuses', 'accuse'),
    ('addressed', 'addressing', 'addresses', 'address'),
    ('appeared', 'appearing', 'appears', 'appear'),
    ('approached', 'approaching', 'approaches', 'approach'),
    ('approved', 'approving', 'approves', 'approve'),
    ('aspired', 'aspiring', 'aspires', 'aspire'),
    ('begged', 'begging', 'begs', 'beg'),
    ('benefited', 'benefitted', 'benefiting', 'benefitting', 'benefits', 'benefit'),
    ('blamed', 'blaming', 'blames', 'blame'),
    ('bowed', 'bowing', 'bows', 'bow'),
    ('burdened', 'burdening', 'burdens', 'burden'),
    ('castrated', 'castrating', 'castrates', 'castrate'),
    ('comforted', 'comforting', 'comforts', 'comfort'),
    ('committed', 'committing', 'commits', 'commit'),
    ('commended', 'commending', 'commends', 'commend'),
    ('contributed', 'contributing', 'contributes', 'contribute'),
    ('confirmed', 'confirming', 'confirms', 'confirm'),
    ('conformed', 'conforming', 'conforms', 'conform'),
    ('cooperated', 'cooperating', 'cooperates', 'cooperate'),
    ('described', 'describing', 'describes', 'describe'),
    ('despaired', 'despairing', 'despairs', 'despair'),
    ('detested', 'detesting', 'detests', 'detest'),
    ('dipped', 'dipping', 'dips', 'dip'),
    ('dishonoured', 'dishonouring', 'dishonours', 'dishonour'),
    ('displayed', 'displaying', 'displays', 'display'),
    ('distressed', 'distressing', 'distresses', 'distress'),
    ('divided', 'dividing', 'divides', 'divide'),
    ('escaped', 'escaping', 'escapes', 'escape'),
    ('envied', 'envying', 'envies', 'envy'),
    ('examined', 'examining', 'examines', 'examine'),
    ('explained', 'explaining', 'explains', 'explain'),
    ('fainted', 'fainting', 'faints', 'faint'),
    ('fasted', 'fasting', 'fasts', 'fast'),
    ('feasted', 'feasting', 'feasts', 'feast'),
    ('flashed', 'flashing', 'flashes', 'flash'),
    ('foamed', 'foaming', 'foams', 'foam'),
    ('fulfilled', 'fulfilling', 'fulfils', 'fulfills', 'fulfil', 'fulfill'),
    ('guarded', 'guarding', 'guards', 'guard'),
    ('happened', 'happening', 'happens', 'happen'),
    ('humbled', 'humbling', 'humbles', 'humble'),
    ('joined', 'joining', 'joins', 'join'),
    ('justified', 'justifying', 'justifies', 'justify'),
    ('knocked', 'knocking', 'knocks', 'knock'),
    ('laboured', 'labouring', 'labours', 'labour'),
    ('lifted', 'lifting', 'lifts', 'lift'),
    ('mastered', 'mastering', 'masters', 'master'),
    ('misled', 'misleading', 'misleads', 'mislead'),
    ('mistreated', 'mistreating', 'mistreats', 'mistreat'),
    ('nodded', 'nodding', 'nods', 'nod'),
    ('noticed', 'noticing', 'notices', 'notice'),
    ('obsessed', 'obsessing', 'obsesses', 'obsess'),
    ('observed', 'observing', 'observes', 'observe'),
    ('oppressed', 'oppressing', 'oppresses', 'oppress'),
    ('overcame', 'overcoming', 'overcomes', 'overcome'),
    ('perished', 'perishing', 'perishes', 'perish'),
    ('perplexed', 'perplexing', 'perplexes', 'perplex'),
    ('persecuted', 'persecuting', 'persecutes', 'persecute'),
    ('planted', 'planting', 'plants', 'plant'),
    ('plucked', 'plucking', 'plucks', 'pluck'),
    ('pondered', 'pondering', 'ponders', 'ponder'),
    ('possessed', 'possessing', 'possesses', 'possess'),
    ('prepared', 'preparing', 'prepares', 'prepare'),
    ('pretended', 'pretending', 'pretends', 'pretend'),
    ('produced', 'producing', 'produces', 'produce'),
    ('pushed', 'pushing', 'pushes', 'push'),
    ('read', 'reading', 'reads'),
    ('reaped', 'reaping', 'reaps', 'reap'),
    ('reasoned', 'reasoning', 'reasons', 'reason'),
    ('rejected', 'rejecting', 'rejects', 'reject'),
    ('rested', 'resting', 'rests', 'rest'),
    ('revered', 'revering', 'reveres', 'revere'),
    ('scorned', 'scorning', 'scorns', 'scorn'),
    ('searched', 'searching', 'searches', 'search'),
    ('shouted', 'shouting', 'shouts', 'shout'),
    ('slandered', 'slandering', 'slanders', 'slander'),
    ('snatched', 'snatching', 'snatches', 'snatch'),
    ('spared', 'sparing', 'spares', 'spare'),
    ('strained', 'straining', 'strains', 'strain'),
    ('strengthened', 'strengthening', 'strengthens', 'strengthen'),
    ('submitted', 'submitting', 'submits', 'submit'),
    ('supplied', 'supplying', 'supplies', 'supply'),
    ('supposed', 'supposing', 'supposes', 'suppose'),
    ('threshed', 'threshing', 'threshes', 'thresh'),
    ('trumpeted', 'trumpeting', 'trumpets', 'trumpet'),
    ('unloaded', 'unloading', 'unloads', 'unload'),
    ('waited', 'waiting', 'waits', 'wait'),
    ('warmed', 'warming', 'warms', 'warm'),
    ('washed', 'washing', 'washes', 'wash'),
    ('worshipped', 'worshipping', 'worshiped', 'worshiping', 'worships', 'worship'),
    # Added 2026-10-06 (OT) verbs where the OET-RV and OET-LV use a different tense/form
    ('played', 'playing', 'plays', 'play'),
    ('provoked', 'provoking', 'provokes', 'provoke'),
    ('slipped', 'slipping', 'slips', 'slip'),
    ('weaned', 'weaning', 'weans', 'wean'),
)
simpleVerbs = tuple(verb for verbSet in SIMPLE_VERB_SETS for verb in verbSet)
# Allow overlapping forms that legitimately belong to different verb paradigms (e.g., lay/lie, saw, set, spread, beat etc.)
allowed_overlaps = {'beat','become','cut','hit','hurt','lay','let','put','quit','saw','set','shut','split','spread','thrust','lying','lies','lain','sawn','sewn','shaven','spat','stridden','stricken'}
duplicates = [x for x in simpleVerbs if simpleVerbs.count(x)>1 and x not in allowed_overlaps]
assert len(duplicates) == 0, f"Accidental duplicates in simpleVerbs: {duplicates}"
for simpleVerb in simpleVerbs: # Just a safety check in case we miss a comma and python concatenates consecutive words
    assert len(simpleVerb) <= 13, f"({len(simpleVerb)}) {simpleVerb}"

simpleAdverbs = ('quickly', 'immediately', 'loudly', 'suddenly',
                 'now', 'then', 'again', 'still', 'only', 'even',
                 'indeed', 'certainly', 'perhaps',)
assert len(set(simpleAdverbs)) == len(simpleAdverbs) # Check for accidental duplicates

simpleAdjectives = ('alive', 'angry', 'bad', 'big', 'bitter',
                    'clean', 'cold',
                    'dangerous', 'dead', 'disobedient', 'entire', 'evil',
                    'female', 'foolish', 'foreign', 'friendly',
                    'godly','good', 'great',
                    'happy', 'high',
                    'impossible',
                    'large', 'little', 'local', 'long', 'loud', 'male', 'naked',
                    'obedient', 'opposite',
                    'possible',
                    'sad', 'same', 'sick', 'small', 'sudden', 'sweet',
                    'eternal', 'golden', 'heavy', 'mighty', 'new', 'old', 'precious',
                    'similar', 'spiritual', 'full', 'blind', 'blameless', 'unleavened',
                    'numerous', 'ready',
                    'whole', 'wide','wild', 'wounded')
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


RV_SINGLE_WORDS_FROM_LV_WORD_STRINGS = (
    ('120', 'a hundred twenty'),
    ('Israelis', 'of Yisrāʼēl/Israel'),('Israeli', 'of Yisrāʼēl/Israel'),
    ('Yisrael','Yisrāʼēl/Israel'),
    ('wants', 'having an ear'),('understand', 'having an ear'),

    # Greek possessive pronouns usually appear after the head noun
    ('my', 'of me'), ('your', 'of you'), ('his', 'of him'), ('her', 'of her'), ('its', 'of it'), ('our', 'of us'), ('their', 'of them'),
    ('My', 'of me'), ('Your', 'of you'), ('His', 'of him'), ('Her', 'of her'), ('Its', 'of it'), ('Our', 'of us'), ('Their', 'of them'),

    # Spelling
    ('money-changers','moneychangers'),

    # Contractions
    ("aren't",'not'),("can't",'not'),("didn't",'not'),("Don't",'not'),("don't",'not'),("isn't",'not'),("shouldn't",'not'),("won't",'not'),
    ("I'll", 'I will'),("I've", 'I have'),
    ("you're", 'you are'),("you've", 'you have'),
    ("didn't", 'did not'),("don't", 'do not'),("doesn't", 'does not'),("isn't", 'is not'),
    ("wasn't", 'was not'),("weren't", 'were not'),("haven't", 'have not'),("hasn't", 'has not'),
    ("hadn't", 'had not'),("wouldn't", 'would not'),("couldn't", 'could not'),("mustn't", 'must not'),
    ("shouldn't", 'should not'),("can't", 'can not'),("won't", 'will not'),
    ("He's", 'He is'),("he's", 'he is'),("She's", 'She is'),("she's", 'she is'),
    ("It's", 'It is'),("it's", 'it is'),("That's", 'That is'),("that's", 'that is'),
    ("There's", 'There is'),("there's", 'there is'),("There’s", 'There is'),
    ("You're", 'You are'),("We're", 'We are'),("we're", 'we are'),
    ("They're", 'They are'),("they're", 'they are'),
    ("I'm", 'I am'),("you're", 'you are'),("We're", 'We are'),
    ("He'll", 'He will'),("He'll", 'he will'),("he'll", 'he will'),("She'll", 'She will'),("she'll", 'she will'),
    ("They'll", 'They will'),("they'll", 'they will'),("You'll", 'You will'),("you'll", 'you will'),
    ("It'll", 'It will'),("it'll", 'it will'),("We'll", 'We will'),("we'll", 'we will'),
    ("They've", 'They have'),("they've", 'they have'),("We've", 'We have'),("we've", 'we have'),
    ("He'd", 'He would'),("he'd", 'he would'),("They'd", 'They would'),("they'd", 'they would'),
    ("I'd", 'I would'),("you'd", 'you would'),("You'd", 'You would'),("We'd", 'We would'),("we'd", 'we would'),
    ("Let's", 'Let us'),("What's", 'What is'),("what's", 'what is'),
    ("Who's", 'Who is'),("who's", 'who is'),("Here's", 'Here is'),("here's", 'here is'),
    ("Where's", 'Where is'),("where's", 'where is'),("When's", 'When is'),("when's", 'when is'),
    ("Why's", 'Why is'),("why's", 'why is'),
    ("He'd", 'He had'),("They'd", 'They had'),("God's", 'of god'),("God’s", 'of god'),

    # Other word number changes
    ('demons', 'unclean spirits'),('demon', 'unclean spirit'),

    # The following nominal entries handle number changes
    ('hair', 'hairs'),
    ('hooves','hoof'),

    # Prepositions
    ('at','in/on/at/with'),('in','in/on/at/with'),('on','in/on/at/with'),('with','in/on/at/with'),

    # Pronouns
    ('those','these'),

    # Adjectival/Adverbial changes
    ('golden','gold'),
    ('loudly','loud'),

    # Vocab differences / synonyms
    # RVword, LVwordOrPhrase
    ('about','concerning'),('about','of'),('about','whom'), # Mrk 12:26, 14:71
    ('accusations','testimony'), # Mrk 14:59
    ('addition','And'),
    ('advance','beforehand'),('advance','previously'), # Mrk 13:11,23
    ('afraid','feared'),('afraid','fearing'),
    ('agreed','same'), # Mrk 14:56
    ('agreeing','confirming'),
    ('agreement','covenant'),
    ('ahead','before'), # Mrk 14:28
    ('alert','watching'), # Mrk 13:34
    ('align','same'), # Mrk 14:59
    ('Also','And'),
    ('always','perpetuity'),
    ('amazed','astonished'),
    ('amazed','marvelling'),
    ('ancestors','fathers'),
    ('and', 'And'),
    ('announced','proclaiming'), ('announcing','proclaiming'),
    ('Anyone','Whoever'),('anyone','whoever'),
        ('Anyone','one'),('anyone','ones'),('anyone','one'),
    ('anything','all things'),
    ('appeared','seen'),
    ('appropriate','fitting'),
    ('Army','hosts'),('army','hosts'),
    ('arrest','apprehend'),
        ('arrested','apprehended'),('arrested','captured'),('arrested','laid'), # Mrk 14:49
    ('aroma','odour'),
    ('around','by'), # Mrk 14:69
    ('asked','saying'), # Mrk 14:37
    ('asleep','sleeping'), # Mrk 14:40
    ('assembly','convocation'),
    ('assure','Truly'), # Mrk 13:30
    ('astounded','amazed'),
    ('attention','attentiveness'),
    ('avoid','pass'), # Mrk 14:35
    ('back','stern'),
    ('battle','war'),('battles','wars'),
    ('because','for/because'),('Because','For/Because'),('because','For/Because'),
    ('because','if/because'),
    ('bedding','pallet'),
    ('believers','brothers'),
    ('biscuits','wafers'),
    ('bless','fruitful'),
    ('blowing','blast'),
    ('body','flesh'),
    ('border','edge'),
    ('both','two'),
    ('boulders','stones'),
    ('bought','redeemed'),
    ('box','ark'),
    ('brightness','glory'), # Mrk 13:26
    ('bull','ox'),('bulls','oxen'),
    ('burning','fire'),
    ('But','And'),('but','And'),('But','and'),('but','and'),
    ('buyers','buying'),
    ('careful','watching'), # Mrk 13:9
    ('cash','money'),('cash','silver'),
    ('cease','removed'),
    ('chairs','seats'),
    ('charge','testimony'),('charges','testimony'), # Mrk 14:56,57
    ('chasing','pursuing'),
    ('cheerful','joy'),
    ('chest','ark'),
    ('close','near'), # Mrk 13:28
    ('closely','focused'), # Mrk 14:67
    ('clothes','apparel'),('clothes','garments'),
    ('collapse','passing away'), # Mrk 13:31
    ('collect','gathering'), # Mrk 13:27
    ('Commander-in-chief','hosts'),
    ('commented','saying'),
    ('confused','confounded'),
    ('continued','said'),
    ('contradicted','saying'), # Mrk 14:29
    ('Countries','nation'),('countries','nation'), # Mrk 13:8
    ('cross','pass over'),
    ('could','may'),
    ('countries','nations'),('country','nation'),
    ('countryside','field'),
    ('courtyard','court'),
    ('cow','ox'),('cows','oxen'),
    ('creation','beginning'),
    ('cried','weeping'), # Mrk 14:72
    ('crowd','multitude'),
    ('date','day'), # Mrk 13:32
    ('dawn','cockcrow'), # Mrk 13:35
    ('dearly','beloved'),
    ('decide','purposed'),
    ('decision','evaluate'),('decisions','judgements'),
    ('defend','answering'), # Mrk 14:60
    ('deformed','withered'),
    ('demolish','tearing'), # Mrk 14:58
    ('demon-possessed','unclean'),
    ('denied','disowned'),('denied','disowning'), # Mrk 14:68,70
    ('desert','ˊₐrāⱱāh'),('plain','ˊₐrāⱱāh'),
    ('deserted','desolate'),
    ('destroyed','consumed'),('destroyed','devoured'),
    ('destruction','devastation'),
    ('die','pass away'), # Mrk 13:30
    ('died','dead'), # Mrk 12:26
    ('dies','corpse'), # Lev 19:28
    ('dinosaur','dragon'), # Rev 12:3
    ('disasters','plagues'),
    ('discouraged','dismayed'),
    ('disown','renounce'), # Mrk 14:31
    ('distance','afar'), # Mrk 14:54
    ('down','below'), # Mrk 14:66
    ('driving','throwing'),
    ('each','all'), # Mrk 14:23
    ('eastern','east'),
    ('eliminate','destroying'),
    ('engaged','betrothed'),
    ('ensure','order'), # Mrk 14:19
    ('enthusiastic','eager'), # Mrk 14:38
    ('entire','all'),
    ('everyone','all'),('everyone','people'),('everyone','one'),('everyone','you all'),
        ('Everyone','one'),
    ('evil','sinners'), # Mrk 14:41
    ('executed','death'), # Mrk 13:12
        ('execution','stake'),
    ('existence','became'),
    ('exposed','uncovered'),
    ('fellow','man'), # Mrk 14:51
    ('finally','Lastly'),('finally','last'),
    ('fitting','befitting'),
    ('flames','fire'),
    ('flattered','saying'),
    ('flicked','sprinkled'),
    ('food','bread'),
    ('forever','perpetuity'),
    ('front','before'),('front','face'), # Mrk 13:9
    ('fulfilled','accomplished'),
    ('gathered','coming together'), # Mrk 14:53
    ('God','god'),
    ("God's",'god'),("God's",'holy'), # Mrk 14:25, 13:11
    ('godly','devout'),('godly','righteous'),
    ('grab','apprehend'),('grabbed','taken'),
    ('grapevine','vine'),('grapes','vine'), # Mrk 14:25
    ('greater','mightier'),
    ('guard','doorkeeper'),('guard','securely'), # Mrk 13:34, 14:44
    ('guy\'s','man'), # Mrk 14:69
    ('hand','giving'),('handed','given'), # Mrk 13:11, 14:41
    ('happen','become'),('happen','becoming'),('happening','becoming'), # Mrk 13:29
    ('harvests','fruit'),
    ('heavenly','heavens'),('heavenly','heaven'),
    ('hills','mountains'),('hill','mountain'),
    ('hilltop','high'),
    ('honest','true'),
    ('honour','glorify'),
        ('honoured','great'), # Mrk 14:45
    ('horrible','abomination'), # Mrk 13:14
    ('huge','great'),
    ('humanity','man'), # Mrk 13:26
    ('humiliated','ashamed'),
    ('hut','shelter'),
    ('immerser','immersing'),
    ('including','and'),
    ('incredible','great'), # Mrk 13:26
    ('instructed','commanded'),('instructs','commanded'), # Mrk 13:34
    ('instructions','commanded'),('instructions','regulations'),
    ('insult','slander'),('insulted','dishonoured'),('insulting','slandering'), # Mrk 14:64
    ('Israelis','people'),
    ('item','article'),('items','article'),
    ('jobs','work'), # Mrk 13:34
    ('judge','judgements'),
    ('kill','destroy'),
    ('King','king'),
    ('kingdoms','nations'),
    ('knelt','falling'), # Mrk 14:35
    ('know','knowledge'),
    ('laid','spread'),
    ('lake','sea'),
    ('large','great'),
    ('land','property'), # Mrk 14:32
    ('language','tongue'),('languages','tongues'),
    ('later','after'), # Mrk 14:70
    ('left','came out'),('left','set out'),
    ('lesson','parable'), # Mrk 13:28
    ('Listen','Behold'),('listen','Behold'),('Listen','behold'),('listen','behold'),
    ('listen','give ear'),('Listen','hearing'),('listen','hear'),
    ('living','dwelling'),
    ('Look','Behold'),('look','Behold'),('Look','behold'),('look','behold'),
    ('looked','focused'), # Mrk 14:67
    ('looking','searched'),('looking','seeking'),
    ('loved','beloved'),
    ('lying','lied'),
    ('mankind','humans'),
    ('many','multiply'),
    ('marvelled','astonished'),
    ('meat','flesh'),
    ('message', 'oracle'), ('message', 'utterance'), ('message', 'word'), ('messenger', 'word'),
    ('met','known'), # Mrk 14:71
    ('metres','cubits'),
    ('mind','heart'),
    ('mister','master'),('Mister','Master'),
    ('money','reward'),
    ('mounted','sat down'),('mounted','sat'),
    ('mourn','weep'), ('mourning','wailing'),
    ('Mt','mountain'),('Mt','mount'),('Mt', 'Mount'),
    ('murdered','killed'),('murdered','killing'),
    ('must','truly'),('must','will'), # Mrk 14:70
    ('napping','sleeping'), # Mrk 13:36
    ('necessary','fitting'),
    ('needs','let'),
    ('never','no means'), # Mrk 13:31
    ('Nevertheless','nevertheless'),
    ('news','report'),
    ('non-Jews','pagans'),
    ('noticed','saw'),
    ('obey','submitting'),
    ('observe','watching'), # Mrk 13:33
    ('offered','giving'), # Mrk 14:57
    ('only','except'), # Mrk 13:32
    ('opened','divided'),
    ('other','across'),
    ('own','possession'),('owned','having'),
    ('ordered','commanded'),
    ('paralysed','paralytic'),
    ('path','way'),('path','road'),
    ('people','humans'),('people','multitude'),('people','ones'),
    ('percent','add'),
    ('permanent','perpetuity'),
    ('picked','taken'), # Mrk 14:23
    ('placed','laid'),('placing','laying'),
    ('planet','earth'), # Mrk 13:31
    ('platform','lid'),
    ('pleasing', 'acceptable'),('pleasing','soothing'),
    ('Plenty','Many'),
    ('plus','and'),
    ('poor','humble'),
    ('population','multitude'),
    ('praised','glorifying'),
    ('preaching','proclaiming'),
    ('prearranged','given'), # Mrk 14:44
    ('priest','priest/officer'),
    ('proclamation','announcement'),('proclamation','declaration'),('proclamation','notice'),('proclamations','declarations'),
    ('produce','fruit'),
    ('promised','sworn'),
    ('pronounce','utterance'),
    ('protect','defend'),
    ('pure','holy'), ('purity','holiness'),
    ('quiet','desolate'),
    ('quiet','silenced'),
    ('range','various'),
    ('readers','reading'), # Mrk 13:14
    ('ready','gird'),
    ('realised','saw'),
    ('region','land'),('regions','land'),
    ('relying','trust'),
    ('remembered','reminded'),
    ('reputation','name'),
    ('request','seek'),('requested','prayed'),
    ('rescue','deliver'),
    ('responded','said'),('responded','saying'), # Mrk 14:30
    ('responsibilities','authority'), # Mrk 13:34
    ('return','coming'), # Mrk 13:35
    ('right','fitting'),('right','truth'), # Mrk 13:10, 12:32
    ('river','Yarden'),
    ('riverbed','wadi'),
    ('robe','cloth'),('robe','clothes'), # Mrk 14:51,63
    ('rock','stone'),('rocks','stones'),('rocks','stone'),
    ('roof','housetop'),('roofs','housetops'),
    ('room','place'),
    ('ropes','cords'),
    ('rubble','ruin'),
    ('rush','hasten'),
    ('sacred','holiness'),('sacred','holy'), ('sacred','of meeting'), # tent of meeting
    ('sacrificed','smoke'),
    ('same','again'), # Mrk 14:70
    ('sanctuary','hideout'),
    ('scared','dismayed'), ('scared','feared'),
    ('scoffed','mocking'),
    ('scriptures','scroll'), # Mrk 12:26
    ('search','seek'),
    ('second','another'),
    ('secured','apprehended'), # Mrk 14:46
    ('See','Behold'),
    ('sentenced','condemned'),('sentenced','put'), # Mrk 14:55,64
    ('servants','attendants'), # Mrk 14:54
    ('several','many'), # Mrk 14:56
    ('shaved','baldness'),
    ('shed','hut'),
    ('She\'s','She'),
    ('shouted','saying'), # Mrk 14:63
    ('shrines','places'),
    ('shore','side'),
    ('should','let'),
    ('sick','sickly'),
    ('Similarly','Likewise'),('similar','likewise'), # Mrk 14:31
    ('single','one'), # Mrk 14:37
    ('sitting','reclining'),
    ('sky','heaven'),('skies','heavens'),
    ('skin','hide'),
    #('slave','servant'), # TODO: Need to add code to prevent this substitution if BOTH words occur in the verse.
    ('small','little'),
    ('So','And'),('So','Therefore'),
    ('someone','anyone'),
    ('something','one message'),
    ('songs','psalms'),('songs','hymns'), # Mrk 14:26
    ('splendour','glory'),
    ('spoken','said'),('spoken','saying'),
    ('started','began'),
    ('staying','dwelling'),
    ('stewards','managers'),
    ('strong','forceful'),
    ('swindlers','robbers'),
    ('talking','speaking'), ('talking','saying'),
    ('tarpaulin','cover'),
    ('tattoo','inscription'), # Lev 19:28
    ('teachers','scribes'),
    ('teaching','saying'), # Mrk 14:27
        ('teachings','messages'), # Mrk 13:31
    ('tell','saying'),
        ('telling','proclaimed'),('telling','saying'),('telling','speaking'),
        ('tells','say'),
    ('tent','tabernacle'),
    ('territory','land'),
    ('that','this'),('that','which'),
    ('themselves','hearts'),
    ('Then','And'),('then','And'),('then','immediately'), # Mrk 14:72
    ('thief','robber'), # Mrk 14:48
    ('thinking','reasoning'),('thinking','supposing'),
    ('third','another'),
    ('thoughtful','intelligently'), # Mrk 12:34
    ('tied','bound'),
    ('time','hour'), # Mrk 13:32
    ('tipped','overturned'),
    ('told','commanded'),('told','saying'),# Mrk 14:34
    ('total','all'),
    ('town','city'),
    ('trip','travelling'), # Mrk 13:34
    ('trustworthy','faithful'),
    ('trying','seeking'), # Mrk 14:55
    ('turned','giving'), # Mrk 13:9
    ('twenty','fifth'),
    ('undesirables','sinners'),
    ('ungodly','unclean'),
    ('upstairs','housetop'),('upstairs','upper'), # Mrk 13:15
    ('untarnished','holy'),
    ('urged','implored'),
    ('very','much'), # Mrk 12:27
    ('wallet','purse'),
    ('warned','spoken'), # Mrk 13:23
    ('warriors','men'),
    ('waters','water supplies'),
    ('way','how'),
    ('wealthy','rich'),
    ('wearing','clothed'), # Mrk 14:51
    ('went','came'),
    ('what','whatever'),("What's",'What'),
    ('When','And'),('When','whenever'),
    ('whipped','beat'), # Mrk 13:9
    ('whole','all'),
    ('will','are'),
    ('women','daughters'),
    ('work','service'),
    ('worried','alarmed'), # Mrk 13:7
    ('worship','bow'),
    ('worn','girding'),
    ('wow','see'),
    ('wrong','strayed'), # Mrk 12:24,27
    ('yelled','cried'),
    ('yourselves','hearts'),
    # Words added after analysis of unmatched LV glosses
    ('missionaries','ambassadors'), ('chains','bonds'),
    ('forever','eternal'), ('miracles','signs'), ('miracles','wonders'),
    ('dear','beloved'), ('killed','slain'), ('faithfulness','loyalty'),
    ('leaders','rulers'), ('leader','ruler'), ('servants','slaves'),
    ('nations','peoples'), ('should','ought'), ('work','labour'),
    ('encouraged','exhorting'), ('wanted','wishing'),
    ('years','year[s]'), ('year','year[s]'), ('days','day[s]'), ('day','day[s]'),
    ('cubits','cubit[s]'), ('cubit','cubit[s]'), ('reeds','reed[s]'), ('reed','reed[s]'),
    ('so','yes'), ('so','correct'), ('so','thus'),
    ('towards','toward'), ('seven','sevenfold'), ('fortified','fortification'),
    ('beautiful','beauty'), ('clothes','clothing'), ('chariots','chariotry'),
    ('time','hour'),
    # Translation differences found in OET-RV Mark chapters 1-13
    ('spoke','said'), ('spoken','said'), ('speaking','saying'), ('spoke','answering'),
    ('answered','said'), ('replied','said'),
    ('parents','mother'), ('parents','father'),
    ('buns','loaves'), ('fish','fishes'),
    ('mothers','parents'), ('fathers','parents'),
    # RVword, LVwordOrPhrase

    # Capitalisation differences (sometimes just due to a change of word order)
    ('Brothers','brothers'),
    ('Four','four'),
    ('God','god'),
    ('Master','master'),
    ('Messiah','messiah'),
    ('We\'ll','We'),('We\'ve','We'),
    ('Yahweh','master'),('Yahweh','YHWH'),('Yahweh\'s','YHWH'),

    # Additional single-word mappings from Mark analysis (2026-10-07)
    # Non-verb mappings (verbs handled by matchVerbSets)
    ('forgiven','forgiveness'),
    ('many','all'),
    ('also','and'),
    ('man','one'),
    ('soon','shortly'),
    ('fishermen','fishers'),
    ('sons','son'),
    ('regular','scribes'),
    ('just','this'),
    ('quiet','deserted'),
    ('other','neighbouring'),
    ('driving','throwing_out'),
    ('felt','having_been_feeling'),
    ('reached','having_stretched_out'),
    ('started','began'),
    ('spreading','spreading_abroad'),
    ('could','able'),
    )
for someTuple in RV_SINGLE_WORDS_FROM_LV_WORD_STRINGS:
    assert isinstance( someTuple, tuple), f"{someTuple=}"
    RVWord, LVWords = someTuple
    assert RVWord != LVWords, f"{RVWord=}"
    assert ' ' not in RVWord
    for simpleVerbSet in SIMPLE_VERB_SETS:
        if LVWords in simpleVerbSet:
            assert RVWord not in simpleVerbSet, f"Can simplify {RVWord=} {LVWords=}"


LV_SINGLE_WORDS_TO_RV_WORD_STRINGS = (
            ('brothers', 'brothers and sisters'), ('brothers', 'fellow believers'),
            ('Brothers', 'Brothers and sisters'), ('Brothers', 'Fellow believers'),
            ('Brothers', 'brothers and sisters'), ('Brothers', 'fellow believers'),

            ('Higgaion', 'Meditation break'),
            ('Şelāh', 'Instrumental break'),
            ('Truly', 'May it be so'),

            ('anymore','any more'), # Mrk 14:63
            ('approached','came closer'), # Mrk 12:28
            ('ascent','walking uphill'),
            ('false','making up'), # Mrk 14:56
            ('first','most important'), # Mrk 12:29
            ('fled','ran away'), # Mrk 14:52
            ('greater','more important'), # Mrk 12:31
            ('members', 'body parts'),
            ('plagues', 'deadly diseases'),
            ('right','honoured position'), # Mrk 14:62
            ('risen', 'got up'),
            ('sanctuary', 'sacred tent'),
            ('scribes', 'religious teachers'),
            ('seeking', 'looking for'),
            ('synagogues', 'Jewish meeting halls'), ('synagogues', 'meeting halls'),
            ('synagogue', 'Jewish meeting hall'), ('synagogue', 'meeting hall'),
            ('tabernacle', 'sacred tent'),
            ('three-times','three times'), # Mrk 14:72
            ('unblemished', 'no defects'),('unblemished', 'without defects'),

            # Additional mappings from Mark analysis (2026-10-07) - LV single word -> RV multi-word phrase
            ('forgiveness', 'have been forgiven'),
            ('all', 'many people'),
            ('and', 'and also'),
            ('one', 'one man'),
            ('shortly', 'soon after'),
            ('fishers', 'fishers of men'),
            ('son', 'son of Zebedee'),
            ('scribes', 'religious teachers'),
            ('this', 'just happened'),
            ('deserted', 'quiet place'),
            ('neighbouring', 'neighbouring villages'),
            )
for someTuple in LV_SINGLE_WORDS_TO_RV_WORD_STRINGS:
    assert isinstance( someTuple, tuple), f"{someTuple=}"
    LVWord,RVWords = someTuple
    assert LVWord != RVWords, f"{RVWords=}"
    assert ' ' not in LVWord
    assert ' ' in RVWords

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

    # First get rid of any word numbers that are wrongly inside a plain '\add'/'\+add' span.
    #   We do this before loading the OET-RV, so that everything we go on to read is the cleaned-up text.
    removeWordNumbersInStraightAddSpansInAllBooks()

    # Load the OET-RV
    rv = ESFMBible( OET_RV_ESFM_FolderPath, givenAbbreviation='OET-RV' )
    rv.loadAuxiliaryFiles = True
    rv.loadBooks() # So we can iterate through them all later
    rv.lookForAuxiliaryFilenames()
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 4:
        dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"{rv=}")

    # Load the OET-LV OT
    lvOT = ESFMBible( OET_LV_OT_ESFM_InputFolderPath, givenAbbreviation='OET-LV' )
    lvOT.loadAuxiliaryFiles = True
    lvOT.loadBooks() # So we can iterate through them all later
    lvOT.lookForAuxiliaryFilenames()
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 4:
        dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"{lvOT=}")

    # Load the OET-LV NT
    lvNT = ESFMBible( OET_LV_NT_ESFM_InputFolderPath, givenAbbreviation='OET-LV' )
    lvNT.loadAuxiliaryFiles = True
    lvNT.loadBooks() # So we can iterate through them all later
    lvNT.lookForAuxiliaryFilenames()
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 4:
        dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"{lvNT=}")

    # Load the OT and NT word files
    state.wordTable, state.wordTableHeaderList = {}, {}
    for testament in ('OT','NT'):
        lv = lvOT if testament=='OT' else lvNT
        BBB = 'GEN' if testament=='OT' else 'MAT'
        input_folder_path = OET_LV_OT_ESFM_InputFolderPath if testament=='OT' else OET_LV_NT_ESFM_InputFolderPath
        lvBookObject = lv[BBB]
        wordFileName = lvBookObject.ESFMWordTableFilename
        if wordFileName:
            assert wordFileName.endswith( '.tsv' )
            if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 3:
                vPrint( 'Info', DEBUGGING_THIS_MODULE, f"  Found ESFMBible filename '{wordFileName}' for {lv.abbreviation} {BBB}" )
            if lv.ESFMWordTables[wordFileName]:
                if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 3:
                    vPrint( 'Info', DEBUGGING_THIS_MODULE, f"  Found ESFMBible loaded '{wordFileName}' word link lines: {len(lv.ESFMWordTables[wordFileName]):,}" )
            else:
                if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 3:
                    vPrint( 'Info', DEBUGGING_THIS_MODULE, f"  No word links loaded yet for '{wordFileName}'" )
            if lv.ESFMWordTables[wordFileName] is None:
                with open( input_folder_path.joinpath(wordFileName), 'rt', encoding='UTF-8' ) as wordFile:
                    lv.ESFMWordTables[wordFileName] = wordFile.read().split( '\n' )
                if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 2:
                    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  connect_OET_RV loaded {len(lv.ESFMWordTables[wordFileName]):,} total rows from {wordFileName}" )
                if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
                    dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  connect_OET_RV loaded column names were: ({len(lv.ESFMWordTables[wordFileName][0])}) {lv.ESFMWordTables[wordFileName][0]}" )
        state.wordTable[testament] = [row.split('\t') for row in lv.ESFMWordTables[wordFileName]]
        state.wordTableHeaderList[testament] = state.wordTable[testament][0]

    # Load the Hebrew and Greek name tables from TSV files
    loadOETRVNameTable()
    loadHebGrkNameTables()
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 4:
        dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"{state.nameTables=}")

    # Load the OET-RV words that are more than one word for one OET-LV word, e.g. 'you all'
    loadOETRVWordPhraseTable()

    # Display anywhere where we still have 'for' that should perhaps be 'because'
    # show_fors( lv )

    # Connect linked words in the OET-LV to the OET-RV
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 1:
        vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"\nProcessing connect words for OET OT…" )
    numWordsOT,numWordNumberedOT = connect_OET_RV( rv, lvOT, OET_LV_OT_ESFM_InputFolderPath, 'OT' ) # OT
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 1:
        vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"\nProcessing connect words for OET NT…" )
    numWordsNT,numWordNumberedNT = connect_OET_RV( rv, lvNT, OET_LV_NT_ESFM_InputFolderPath, 'NT' ) # NT

    # In 'fast' mode we only processed MRK, so the per-book figures are all we can say
    if not BibleOrgSysGlobals.commandLineArguments.fastMode:
        reportWordNumberPercentage( "Whole Bible", numWordsOT+numWordsNT, numWordNumberedOT+numWordNumberedNT )

    # Delete any saved (but now obsolete) OBD Bible pickle files
    for something in OET_RV_ESFM_FolderPath.iterdir():
        if something.name.endswith( '.OBD_Bible.pickle' ):
            if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 2:
                vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"Deleting obsolete OBD Bible pickle file {something.name}…" )
            something.unlink()
# end of connect_OET-RV_words_via_OET-LV.main


def loadOETRVNameTable() -> None:
    """
    Load the translator's decisions about how proper names are spelled in the OET-RV.

    The Search column of the ScriptedBibleEditor command tables is the traditional/KJB spelling,
        which we often have to guess at when matching it to an OET-LV transliterated name
        (e.g., we blindly turn a leading 'J' into a 'Y', which gets 'Jerusalem' -> 'Yerusalem'
            instead of the 'Yerushalem' that we actually use).
    This table records the real decision, so we prefer it wherever the translator has flagged a row
        with an 'Explained' flag of 'Y'.
    Rows without that flag are just candidates, so we deliberately ignore them.
    """
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 1:
        vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  Loading decided OET-RV names from {OET_RV_NAMES_TABLE_FILEPATH}…" )
    state.rvNameTable = defaultdict( set ) # traditionalName -> set of accepted OET-RV spellings
    state.rvNameCandidates = defaultdict( set ) # traditionalName -> set of ALL known OET-RV spellings (decided or not)
    with open( OET_RV_NAMES_TABLE_FILEPATH, 'rt', encoding='utf-8' ) as namesTableFile:
        tsvLines = namesTableFile.read().rstrip().split( '\n' )
    if tsvLines[0].startswith( '\ufeff' ): tsvLines[0] = tsvLines[0][1:] # Remove any BOM
    assert tsvLines[0] == OET_RV_NAMES_TABLE_HEADER, f"Expected '{OET_RV_NAMES_TABLE_HEADER}' but found '{tsvLines[0]}' in {OET_RV_NAMES_TABLE_FILEPATH}"

    for line in tsvLines[1:]:
        fields = line.split( '\t' )
        if len(fields) < 2: continue # Some editors delete trailing columns
        traditionalName, rvName = fields[0].strip(), fields[1].strip()
        explained = fields[2].strip() if len(fields) >= 3 else ''
        if not traditionalName or not rvName: continue
        # The OET-RV uses straight apostrophes inside names, but the table uses curly ones, e.g., 'Sha’ul'
        state.rvNameCandidates[traditionalName.replace( '’', "'" )].add( rvName.replace( '’', "'" ) )
        if explained.upper() != 'Y': continue # Only the translator's decisions (not just candidates)
        state.rvNameTable[traditionalName.replace( '’', "'" )].add( rvName.replace( '’', "'" ) )
    state.rvNameTableInverse = defaultdict( set ) # OET-RV spelling -> set of traditional names for it
    for traditionalName,rvNames in state.rvNameTable.items():
        for rvName in rvNames: state.rvNameTableInverse[simplifyRVLVWord( rvName )].add( traditionalName )
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 2:
        vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"    Loaded {len(state.rvNameTable):,} decided OET-RV names covering {sum(len(v) for v in state.rvNameTable.values()):,} spellings." )
# end of connect_OET-RV_words_via_OET-LV.loadOETRVNameTable


def loadOETRVWordPhraseTable() -> None:
    """
    Load the translator's decisions about the OET-RV words that are MORE THAN ONE English word
        which together translate just ONE OET-LV word, e.g.
            the OET-LV 'you_all' (one Hebrew or Greek word, the plural 'you') which the OET-RV
                often writes as the two words 'you all' (1,281 times in the OET-RV)
            the OET-LV 'colt' which the OET-RV writes as the two words 'young donkey'
        (The other way round, i.e. several OET-LV words for one OET-RV word, is the OET-LV's own
        'first word/English gloss' convention, e.g. the OET-LV 'he/it' or 'possessions/wealth',
        and matchWordsInOrder() already lets any of those alternatives match the OET-RV word.)

    'LVWord' is the OET-LV word, spelled the way the OET-LV spells it, i.e. with an underscore
        between the parts of one word ('you_all'); a space works there too.
    'RVWords' is what the OET-RV actually uses, with a space between the words ('you all').
    Only the rows that the translator has flagged with an 'Enabled' of 'Y' are used, so that
        candidates can be listed in the table without being acted on yet (as with the names table).
    """
    state.rvWordPhrases = {} # (simplified LV words) -> (simplified RV words), e.g. ('you','all') -> ('you','all')
    if not OET_RV_WORD_PHRASES_TABLE_FILEPATH.is_file():
        logging.warning( f"Can't find the OET-RV word phrases table {OET_RV_WORD_PHRASES_TABLE_FILEPATH}, so no multi-word translations will be connected" )
        return
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 1:
        vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  Loading enabled OET-RV word phrases from {OET_RV_WORD_PHRASES_TABLE_FILEPATH}…" )
    state.rvWordPhrasesSearch = {} # (simplified RV words) -> (RV words as the OET-RV spells them)
    tsvLines = OET_RV_WORD_PHRASES_TABLE_FILEPATH.read_text( encoding='utf-8' ).rstrip().split( '\n' )
    if tsvLines[0].startswith( '﻿' ): tsvLines[0] = tsvLines[0][1:] # Remove any BOM
    assert tsvLines[0] == OET_RV_WORD_PHRASES_TABLE_HEADER, f"Expected '{OET_RV_WORD_PHRASES_TABLE_HEADER}' but found '{tsvLines[0]}' in {OET_RV_WORD_PHRASES_TABLE_FILEPATH}"

    for line in tsvLines[1:]:
        fields = line.split( '\t' )
        if len(fields) < 3: continue # Some editors delete trailing columns
        lvWordStr, rvWordsStr, enabled = fields[0].strip(), fields[1].strip(), fields[2].strip()
        if not lvWordStr or not rvWordsStr: continue
        if enabled.upper() != 'Y': continue # Only the translator's decisions (not just candidates)
        lvWords = tuple( simplifyRVLVWord( word ) for word in lvWordStr.replace( '_', ' ' ).split() )
        rvWords = tuple( rvWordsStr.split() )
        assert lvWords and all( lvWords ), f"Bad LVWord '{lvWordStr}' in {OET_RV_WORD_PHRASES_TABLE_FILEPATH}"
        if len( rvWords ) < 2:
            logging.warning( f"Skipping the OET-RV word phrases row '{lvWordStr}' -> '{rvWordsStr}', because a single OET-RV word belongs in EQUIVALENT_LV_RV_WORDS instead" )
            continue
        state.rvWordPhrases[ lvWords ] = tuple( simplifyRVLVWord( word ) for word in rvWords )
        state.rvWordPhrasesSearch[ tuple( simplifyRVLVWord( word ) for word in rvWords ) ] = rvWords
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 2:
        vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"    Loaded {len(state.rvWordPhrases):,} enabled OET-RV word phrases." )
# end of connect_OET-RV_words_via_OET-LV.loadOETRVWordPhraseTable

# The name command tables record a name the way the OET-LV text spells it, which means with the
#   '¦' word number, with the '\add …\add*' gloss helpers that come with it, and with the '_' that
#   joins the English glosses of the one OET-LV word, e.g. the Search 'Pharisee¦' and Replace
#   'Φαρισαῖος¦_\add party¦\add*' of the OET-RV 'Pharisees', or the Search 'Arabs¦' and Replace
#   '\add >ones¦\add*_from¦_Ἀραβία¦' of the OET-RV 'Arabs'.  A name lookup on the plain OET-LV
#   name ('Farisaios', 'Arabia') can't find such a key, so cleanNameTableField() and
#   getPlainNameKeys() below give us the plain spelling of the name as well.
NAME_GLOSS_HELPER_REGEX = re.compile( r'\\add[^*]*\\add\*' ) # e.g. the '\add party¦\add*' of 'Φαρισαῖος¦_\add party¦\add*'
WORD_NUMBER_MARKER_REGEX = re.compile( r'¦\d*' ) # e.g. '¦32660', or a bare '¦' that has lost its number
NAME_ALTERNATIVE_REGEX = re.compile( r'[/(]' ) # The '/' or '(' of an alternative spelling, e.g. 'Yəhūdāh/Judah'
# The English words that the OET-LV uses to gloss one OET-LV word, which are never the name
#   itself, e.g. the 'from' of 'from¦X_Ἀραβία¦X' or the 'tribe of' of
#   'from¦X_tribe¦X_of¦X_לֵוִי¦X'.
NAME_GLOSS_WORDS = { 'a','an','in','of','one','ones','supporters','the','tribe' }


def cleanNameTableField( name:str ) -> str:
    """
    Return a name from a name command table with the OET-LV word number marker taken off it,
        e.g. 'Pharisee¦' becomes 'Pharisee', so that it matches an OET-RV name.
    """
    return WORD_NUMBER_MARKER_REGEX.sub( '', name ).strip()
# end of connect_OET-RV_words_via_OET-LV.cleanNameTableField


def getPlainNameKeys( replaceText:str ) -> List[str]:
    """
    Return the plain word that a name command table records a name as, i.e. without the word
        number marker, the gloss helpers and the '_' joins, so that a name lookup on the OET-LV
        name itself can find it, e.g. ['Farisaios'] for 'Φαρισαῖος¦_\\add party¦\\add*' and
        ['Arabia'] for '\\add >ones¦\\add*_from¦_Ἀραβία¦'.

    We take the LAST plain word of each alternative, because that is the name itself, with the
        English glosses in front of it ('ones from Arabia', 'from tribe of Levi'), while any plain
        word that comes AFTER the name qualifies it, and so is a different name: the 'zaʸlōtaʸs' of
        'Φαρισαῖος¦_zaʸlōtaʸs¦_\\add group¦_member¦\\add*' is a Zealot, not a Pharisee.
    """
    cleaned = WORD_NUMBER_MARKER_REGEX.sub( ' ', NAME_GLOSS_HELPER_REGEX.sub( ' ', replaceText ) )
    keys = []
    for alternative in NAME_ALTERNATIVE_REGEX.split( cleaned ):
        words = [ word for word in alternative.replace( '_', ' ' ).split() if word not in NAME_GLOSS_WORDS ]
        if words: keys.append( words[-1] )
    return keys
# end of connect_OET-RV_words_via_OET-LV.getPlainNameKeys


def addPlainNameKeys( nameTableKey:str, replaceText:str, searchText:str, rvNameChoices:set ) -> None:
    """
    Save a name from a name command table under the plain OET-LV name as well as under the full
        Replace text (which has the word number marker, the gloss helpers and the '_' joins in it),
        so that both matchAdjustedProperNouns() and getLVNameSpellings() can find it when they look
        the OET-LV name up, e.g. the OET-RV 'Pharisee' against the OET-LV 'Farisaios'.
    """
    for plainName in getPlainNameKeys( replaceText ):
        state.nameTables[nameTableKey][plainName].update( rvNameChoices )
        state.nameTables[nameTableKey][plainName].add( searchText )
# end of connect_OET-RV_words_via_OET-LV.addPlainNameKeys


def loadHebGrkNameTables():
    """
    Loads three TSV files into state.nameTables

    These are the ScriptedBibleEditor command files that create the Hebrew and Greek proper names for the OET-LV.
    """
    state.nameTables = {}

    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 1:
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
                searchText = cleanNameTableField( searchText ) # Take off any OET-LV word number marker, e.g. 'Chaldeans¦'
                traditionalName = searchText # Save this before we mangle it below
                if searchText.startswith( 'J' ): searchText = f'Y{searchText[1:]}' # Replace first letter J with Y
                rvNameChoices = state.rvNameTable.get( traditionalName, set() ) | state.rvNameCandidates.get( traditionalName, set() ) # What we actually call it in the OET-RV

                # newReplaceText = transliterate_Hebrew( replaceText, capitaliseHebrew=searchText[0].isupper() )
                # if newReplaceText != replaceText:
                #     # print(f" Converted Hebrew '{replaceText}' to '{newReplaceText}'")
                #     replaceText = newReplaceText
                replaceText = transliterate_Hebrew( replaceText, capitalise_hebrew=searchText[0].isupper() )
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
                    state.nameTables['OT'][shortenedReplaceText].update( rvNameChoices )
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
                state.nameTables['OT'][replaceText].update( rvNameChoices )
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
                addPlainNameKeys( 'OT', replaceText, searchText, rvNameChoices )
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 2:
        vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"    Loaded {len(state.nameTables['OT']):,} OT names." )
    # print( f"{state.nameTables['OT']['Mənaḩēm']=}" ); assert False, "We want to stop here"

    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 1:
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
                searchText = cleanNameTableField( searchText ) # Take off any OET-LV word number marker
                traditionalName = searchText # Save this before we mangle it below
                if searchText.startswith( 'J' ): searchText = f'Y{searchText[1:]}' # Replace first letter J with Y
                rvNameChoices = state.rvNameTable.get( traditionalName, set() ) | state.rvNameCandidates.get( traditionalName, set() ) # What we actually call it in the OET-RV
                newReplaceText = transliterate_Greek( transliterate_Hebrew( replaceText, capitalise_hebrew=searchText[0].isupper() ) )
                if newReplaceText != replaceText:
                    # print(f" Converted Hebrew/Greek '{replaceText}' to '{newReplaceText}'")
                    replaceText = newReplaceText
                if '/' in replaceText:
                    assert 'd' in tags, f"OT_NT {tags=} {searchText=} {replaceText=}"
                    replaceText = replaceText.replace( '(', '' ).replace( ')', '' ) # We don't want the brackets
                    shortenedReplaceText = replaceText.split( '/' )[0]
                    # assert shortenedReplaceText not in state.nameTables['NT_OT'], f"{tags=} {searchText=} {replaceText=} {shortenedReplaceText=}"
                    state.nameTables['NT_OT'][shortenedReplaceText].update( rvNameChoices )
                    state.nameTables['NT_OT'][shortenedReplaceText].add ( searchText ) # We add an extra entry
                # assert replaceText not in state.nameTables['NT_OT'], f"{tags=} {searchText=} {replaceText=}"
                state.nameTables['NT_OT'][replaceText].update( rvNameChoices )
                state.nameTables['NT_OT'][replaceText].add( searchText )
                addPlainNameKeys( 'NT_OT', replaceText, searchText, rvNameChoices )
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 2:
        vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"    Loaded {len(state.nameTables['NT_OT']):,} NT OT names." )

    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 1:
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
                searchText = cleanNameTableField( searchText ) # Take off any OET-LV word number marker, e.g. 'Pharisees¦'
                traditionalName = searchText # Save this before we mangle it below
                if searchText.startswith( 'J' ): searchText = f'Y{searchText[1:]}' # Replace first letter J with Y
                rvNameChoices = state.rvNameTable.get( traditionalName, set() ) | state.rvNameCandidates.get( traditionalName, set() ) # What we actually call it in the OET-RV
                newReplaceText = transliterate_Greek( replaceText )
                if newReplaceText != replaceText:
                    # print(f" Converted Greek '{replaceText}' to '{newReplaceText}'")
                    replaceText = newReplaceText
                if '/' in replaceText:
                    assert 'd' in tags, f"NT {tags=} {searchText=} {replaceText=}"
                    replaceText = replaceText.replace( '(', '' ).replace( ')', '' ) # We don't want the brackets
                    shortenedReplaceText = replaceText.split( '/' )[0]
                    # assert shortenedReplaceText not in state.nameTables['NT'], f"{tags=} {searchText=} {replaceText=} {shortenedReplaceText=}"
                    state.nameTables['NT'][shortenedReplaceText].update( rvNameChoices )
                    state.nameTables['NT'][shortenedReplaceText].add( searchText ) # We add an extra entry
                # assert replaceText not in state.nameTables['NT'], f"{tags=} {searchText=} {replaceText=}"
                state.nameTables['NT'][replaceText].update( rvNameChoices )
                state.nameTables['NT'][replaceText].add( searchText )
                addPlainNameKeys( 'NT', replaceText, searchText, rvNameChoices )
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 2:
        vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"    Loaded {len(state.nameTables['NT']):,} NT names." )

    # Add the divine-name forms that the LV uses directly (not produced by a Hebrew transliteration)
    state.nameTables['OT']['YHWH'].update( { 'Yahweh', 'LORD', 'Lord' } )
    # A normalised, flattened index of every name spelling known to the command tables,
    #   so that we can match an OET-LV capitalised word whose transliteration doesn't match
    #   any table key exactly (accents on/off, macrons, superscripts, slash alternatives, etc.)
    state.namePartsIndex = defaultdict( set )
    for nameTable in state.nameTables.values():
        for tableKey,rvNameCandidates in nameTable.items():
            for part in splitNameKey( tableKey ):
                normalised = normalizeNameKey( part )
                if normalised:
                    state.namePartsIndex[normalised].update( rvNameCandidates )
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 2:
        vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"    Built a normalised name index of {len(state.namePartsIndex):,} entries." )
# end of connect_OET-RV_words_via_OET-LV.loadHebGrkNameTables


_NAME_KEY_SEPARATORS = re.compile( r'[/()\[\]{}\\+_]' )
_NAME_KEY_STRIP_CHARS = " ˊ'‘’`ʹʼ¨¯´˸ـ-"

def splitNameKey( name:str ) -> List[str]:
    """Split a name key into its alternatives, e.g. 'Dawid/(Dāvid)' -> ['Dawid', 'Dāvid']."""
    return [ part for part in _NAME_KEY_SEPARATORS.split( name ) if part.strip() ]
# end of splitNameKey


def normalizeNameKey( name:str ) -> str:
    """Reduce a name to a lowercase ASCII form with no diacritics or accessorisation,
        so that e.g. 'Yəhōyāqīm' and 'YEHOIAKIM' and 'Yəhōyākīm' all look alike."""
    name = unicodedata.normalize( 'NFKD', name )
    name = ''.join( ch for ch in name if unicodedata.category( ch ) != 'Mn' )
    for ch in _NAME_KEY_STRIP_CHARS: name = name.replace( ch, '' )
    return name.lower().strip( '.,;:!?"“”‘’-' )
# end of normalizeNameKey


illegalWordLinkRegex1 = re.compile( '[0-9]¦' ) # Has digits BEFORE the broken pipe
illegalWordLinkRegex2 = re.compile( '¦[1-9][0-9]{0,5}[a-z]' ) # Has letters immediately AFTER the wordlink number
doubledND, badAddND, badNDAdd = '\\nd \\nd ', '\\add \\nd ', '\\nd*\\add*'
def connect_OET_RV( rv, lv, OET_LV_ESFM_InputFolderPath, testament:str ):
    """
    Firstly, load the OET-LV wordtable.
        Loads into state.wordTableHeaderList and state.wordTable.

    Check that any existing word numbers are in the correct verse.

    Then connect linked words in the OET-LV to the OET-RV.

    testament is either 'OT' or 'NT', and is used to label the word count summaries.

    Returns a (numWords,numWordNumbered) tuple for this testament, i.e. how many of the OET-RV
        words of the books that we processed could have a word number, and how many of them
        have one (see countWordsAndWordNumbers()), so that main() can add the two testaments
        together for a whole Bible figure.
    """
    assert testament in ('OT','NT'), f"Bad {testament=}"
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag:
        fnPrint( DEBUGGING_THIS_MODULE, f"connect_OET_RV( {rv}, {lv} {testament} )" )

    # Make a list of the books that we're going to process
    booklist_to_process = []
    for BBB in lv.books:
        if BibleOrgSysGlobals.commandLineArguments.fastMode and BBB not in ('MRK',):
            continue
        # if BBB in ('CO1',): continue # TODO: CO1_14:33 gives an issue
        booklist_to_process.append( BBB )
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 2:
        vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Created a list of {len(booklist_to_process)} OET books to process." )

    # Go through books chapters and verses
    totalWordPhraseAdds = totalSimpleListedAdds = totalProperNounAdds = totalFirstPartMatchedAdds = totalManualMatchedAdds = totalChangedNumberAdds = totalRewordedAdds = totalSpecialistAdds = totalInOrderMatchedAdds = 0
    totalWordPhraseAddsNS = totalSimpleListedAddsNS = totalProperNounAddsNS = totalFirstPartMatchedAddsNS = totalManualMatchedAddsNS = totalChangedNumberAddsNS = totalRewordedAddsNS = totalSpecialistAddsNS = totalInOrderMatchedAddsNS = 0 # Nomina sacra
    totalNumWords = totalNumWordNumbered = 0

    if BibleOrgSysGlobals.maxProcesses > 1 \
    and not BibleOrgSysGlobals.alreadyMultiprocessing \
    and len(booklist_to_process) > 3: # Get our subprocesses ready and waiting for work
        # Process all the books as quickly as possible
        parameters = [(BBB,lv,rv,OET_LV_ESFM_InputFolderPath) for BBB in booklist_to_process] # Can only pass a single parameter to map
        if BibleOrgSysGlobals.verbosityLevel > 1:
            vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"connect_OET_RV: Processing {len(booklist_to_process)} ESFM books using {min(BibleOrgSysGlobals.maxProcesses,len(booklist_to_process))} processes…" )
            vPrint( 'Quiet', DEBUGGING_THIS_MODULE, "  NOTE: Outputs (including error and warning messages) from loading various books may be interspersed." )
        BibleOrgSysGlobals.alreadyMultiprocessing = True
        with multiprocessing.Pool( processes=BibleOrgSysGlobals.maxProcesses ) as pool: # start worker processes
            results = pool.map( _connect_OET_RV_book_MP, parameters ) # have the pool do our loads
            assert len(results) == len(booklist_to_process)
            for bookWordPhraseAdds, bookWordPhraseAddsNS, bookSimpleListedAdds, bookSimpleListedAddsNS, bookProperNounAdds, bookProperNounAddsNS, bookFirstPartMatchedAdds, \
                        bookFirstPartMatchedAddsNS, bookManualMatchedAdds, bookManualMatchedAddsNS, bookChangedNumberAdds, \
                        bookChangedNumberAddsNS, bookSpecialistAdds, bookSpecialistAddsNS, bookInOrderMatchedAdds, \
                        bookInOrderMatchedAddsNS, bookNumWords, bookNumWordNumbered in results:
                totalWordPhraseAdds += bookWordPhraseAdds
                totalWordPhraseAddsNS += bookWordPhraseAddsNS
                totalSimpleListedAdds += bookSimpleListedAdds
                totalSimpleListedAddsNS += bookSimpleListedAddsNS
                totalProperNounAdds += bookProperNounAdds
                totalProperNounAddsNS += bookProperNounAddsNS
                totalFirstPartMatchedAdds += bookFirstPartMatchedAdds
                totalFirstPartMatchedAddsNS += bookFirstPartMatchedAddsNS
                totalManualMatchedAdds += bookManualMatchedAdds
                totalManualMatchedAddsNS += bookManualMatchedAddsNS
                totalChangedNumberAdds += bookChangedNumberAdds
                totalChangedNumberAddsNS += bookChangedNumberAddsNS
                totalSpecialistAdds += bookSpecialistAdds
                totalSpecialistAddsNS += bookSpecialistAddsNS
                totalInOrderMatchedAdds += bookInOrderMatchedAdds
                totalInOrderMatchedAddsNS += bookInOrderMatchedAddsNS
                totalNumWords += bookNumWords
                totalNumWordNumbered += bookNumWordNumbered
        BibleOrgSysGlobals.alreadyMultiprocessing = False
    else: # Just single threaded
        # Process the books one by one
        for BBB in booklist_to_process:
            bookWordPhraseAdds, bookWordPhraseAddsNS, bookSimpleListedAdds, bookSimpleListedAddsNS, bookProperNounAdds, bookProperNounAddsNS, bookFirstPartMatchedAdds, \
                bookFirstPartMatchedAddsNS, bookManualMatchedAdds, bookManualMatchedAddsNS, bookChangedNumberAdds, \
                bookChangedNumberAddsNS, bookSpecialistAdds, bookSpecialistAddsNS, bookInOrderMatchedAdds, \
                bookInOrderMatchedAddsNS, bookNumWords, bookNumWordNumbered = connect_OET_RV_book( BBB, lv, rv, OET_LV_ESFM_InputFolderPath )
            totalWordPhraseAdds += bookWordPhraseAdds
            totalWordPhraseAddsNS += bookWordPhraseAddsNS
            totalSimpleListedAdds += bookSimpleListedAdds
            totalSimpleListedAddsNS += bookSimpleListedAddsNS
            totalProperNounAdds += bookProperNounAdds
            totalProperNounAddsNS += bookProperNounAddsNS
            totalFirstPartMatchedAdds += bookFirstPartMatchedAdds
            totalFirstPartMatchedAddsNS += bookFirstPartMatchedAddsNS
            totalManualMatchedAdds += bookManualMatchedAdds
            totalManualMatchedAddsNS += bookManualMatchedAddsNS
            totalChangedNumberAdds += bookChangedNumberAdds
            totalChangedNumberAddsNS += bookChangedNumberAddsNS
            totalSpecialistAdds += bookSpecialistAdds
            totalSpecialistAddsNS += bookSpecialistAddsNS
            totalInOrderMatchedAdds += bookInOrderMatchedAdds
            totalInOrderMatchedAddsNS += bookInOrderMatchedAddsNS
            totalNumWords += bookNumWords
            totalNumWordNumbered += bookNumWordNumbered

    if totalWordPhraseAdds or totalSimpleListedAdds or totalProperNounAdds or totalFirstPartMatchedAdds or totalManualMatchedAdds or totalChangedNumberAdds or totalRewordedAdds or totalSpecialistAdds or totalInOrderMatchedAdds:
        if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 2:
            vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  {testament} Did total of {totalWordPhraseAdds:,} word phrase adds, {totalSimpleListedAdds:,} simple listed adds, {totalProperNounAdds:,} proper noun adds, {totalFirstPartMatchedAdds:,} first part adds, {totalManualMatchedAdds:,} manual adds, {totalChangedNumberAdds:,} changed number adds, {totalRewordedAdds:,} reworded adds, {totalSpecialistAdds:,} specialist add spans and {totalInOrderMatchedAdds:,} in-order adds." )
    else: vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  {testament} No new word connections made." )
    if totalSimpleListedAddsNS or totalProperNounAddsNS or totalFirstPartMatchedAddsNS or totalManualMatchedAddsNS or totalChangedNumberAddsNS or totalRewordedAddsNS or totalSpecialistAddsNS or totalInOrderMatchedAddsNS:
        if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 2:
            vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  {testament} Did total of {totalSimpleListedAddsNS:,} simple listed nomina sacra (NS), {totalProperNounAddsNS:,} proper noun NS, {totalFirstPartMatchedAddsNS:,} first part NS, {totalManualMatchedAddsNS:,} manual NS, {totalChangedNumberAddsNS:,} changed number NS, {totalRewordedAddsNS:,} reworded NS, {totalSpecialistAddsNS:,} specialist add span NS and {totalInOrderMatchedAddsNS:,} in-order NS." )
    else: vPrint( 'Info', DEBUGGING_THIS_MODULE, f"  {testament} No new nomina sacra connections made." )
    if not BibleOrgSysGlobals.commandLineArguments.fastMode: # In 'fast' mode we reported the individual books instead
        reportWordNumberPercentage( testament, totalNumWords, totalNumWordNumbered )
    return totalNumWords, totalNumWordNumbered
# end of connect_OET-RV_words_via_OET-LV.connect_OET_RV


def _connect_OET_RV_book_MP( givenParameters ):
    """
    Multiprocessing version!
    Load the requested book if it's not already loaded (but doesn't save it as that is not safe for multiprocessing)

    Parameter is a 4-tuple containing the parameters.
    """
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag:
        fnPrint( DEBUGGING_THIS_MODULE, f"_connect_OET_RV_book_MP( {givenParameters} )" )
    return connect_OET_RV_book( *givenParameters )
# end of connect_OET-RV_words_via_OET-LV._connect_OET_RV_book_MP

def connect_OET_RV_book( BBB:str, lv, rv, OET_LV_ESFM_InputFolderPath ):
    """
    Firstly, load the OET-LV wordtable.
        Loads into state.wordTableHeaderList and state.wordTable.

    Check that any existing word numbers are in the correct verse.

    Then connect linked words in the OET-LV to the OET-RV.
    """
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag:
        fnPrint( DEBUGGING_THIS_MODULE, f"connect_OET_RV_book( {BBB} )" )
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 2:
        vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Processing connect words for OET {BBB}…" )

    # wordFileName = lv[BBB].ESFMWordTableFilename

    bookWordPhraseAdds = bookSimpleListedAdds = bookProperNounAdds = bookFirstPartMatchedAdds = bookManualMatchedAdds = bookChangedNumberAdds = bookRewordedAdds = bookSpecialistAdds = bookInOrderMatchedAdds = 0
    bookWordPhraseAddsNS = bookSimpleListedAddsNS = bookProperNounAddsNS = bookFirstPartMatchedAddsNS = bookManualMatchedAddsNS = bookChangedNumberAddsNS = bookRewordedAddsNS = bookSpecialistAddsNS = bookInOrderMatchedAddsNS = 0 # Nomina sacra

    lvESFMFilename = f'OET-LV_{BBB}.ESFM'
    lvESFMFilepath = OET_LV_ESFM_InputFolderPath.joinpath( lvESFMFilename )
    with open( lvESFMFilepath, 'rt', encoding='UTF-8' ) as esfmFile:
        state.lvESFMText = esfmFile.read() # We keep the original (for later comparison)
        state.lvESFMLines = state.lvESFMText.split( '\n' )
        # Do some basic checking (better to find common editing errors sooner rather than later)
        for lineNumber,line in enumerate( state.lvESFMLines, start=1 ):
            # assert not line.endswith(' '), f"Unexpected space at end in {lvESFMFilename} {lineNumber}: '{line}'" # Should be checked elsewhere -- tends to fail on OET-LV MAT line 99
            if line.endswith(' '):
                logging.warning( f"Unexpected space at end in {lvESFMFilename} {lineNumber}: '{line}'" )
            for characterMarker in BibleOrgSysGlobals.USFMCharacterMarkers:
                assert line.count( f'\\{characterMarker} ') == line.count( f'\\{characterMarker}*'), f"{characterMarker} marker mismatch in {lvESFMFilename} {lineNumber}: '{line}'"
            assert doubledND not in line, f"Double \\nd in {lvESFMFilename} {lineNumber}: '{line}'"
            assert  badAddND not in line, f"\\nd inside \\add start {lvESFMFilename} {lineNumber}: '{line}'"
            assert  badNDAdd not in line, f"\\nd inside \\add end {lvESFMFilename} {lineNumber}: '{line}'"
            assert  ' ¦' not in line, f"Word number attached to space {lvESFMFilename} {lineNumber}: '{line}'"
            if '\\x* ' in line: # this can be ok if the xref directly follows other text
                logger = logging.critical if ' \\x ' in line else logging.warning
                logger( f"Double-check space after xref in {lvESFMFilename} {lineNumber}: '{line}'" )

    rvESFMFilename = f'OET-RV_{BBB}.ESFM'
    rvESFMFilepath = OET_RV_ESFM_FolderPath.joinpath( rvESFMFilename )
    with open( rvESFMFilepath, 'rt', encoding='UTF-8' ) as esfmFile:
        state.rvESFMText = esfmFile.read() # We keep the original (for later comparison)
        state.rvESFMLines = state.rvESFMText.split( '\n' )
        # Remove any word numbers that are inside a plain (straight) \add ...\add* span,
        #   because those words were added into the English text, so they have no OET-LV word number
        numStraightAddSpanRemovals = removeWordNumbersInStraightAddSpans( rvESFMFilename, state.rvESFMLines )
        if numStraightAddSpanRemovals:
            if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 2:
                vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"    Removed a total of {numStraightAddSpanRemovals:,} word number(s) from inside straight '\\add'/'\\+add' spans in {rvESFMFilename}" )
        # Do some basic checking (better to find common editing errors sooner rather than later)
        for lineNumber,line in enumerate( state.rvESFMLines, start=1 ):
            assert not line.startswith(' '), f"Unexpected space at start in {rvESFMFilename} {lineNumber}: '{line}'"
            assert not line.endswith(' '), f"Unexpected space at end in {rvESFMFilename} {lineNumber}: '{line}'"
            assert '  ' not in line, f"Unexpected doubled spaces in {rvESFMFilename} {lineNumber}: '{line}'"
            assert ',,' not in line and '..' not in line.replace( '../', '' ), f"Unexpected doubled punctuation in {rvESFMFilename} {lineNumber}: '{line}'"
            assert '\\x*,' not in line and '\\x*.' not in line, f"Bad xref formatting in {rvESFMFilename} {lineNumber}: '{line}'"
            if line.count(' \\x ') < line.count('\\x '):
                assert '\\x* ' in line or line.endswith('\\x*') or '\\x*—' in line, f"Missing xref space in {rvESFMFilename} {lineNumber}: '{line}'"
            if '“ ‘' not in line:
                assert '“ ' not in line, f"Unexpected space at beginning of speech in {rvESFMFilename} {lineNumber}: '{line}'"
            assert '“‘' not in line and '‘“' not in line, f"Unexpected consecutive opeing speech marks in {rvESFMFilename} {lineNumber}: '{line}'"
            assert '’“' not in line and '“’' not in line, f"Unexpected consecutive closing speech marks in {rvESFMFilename} {lineNumber}: '{line}'"
            if '’ ”' not in line and '’\\wj* ”' not in line:
                assert ' ”' not in line, f"Unexpected space at end of speech in {rvESFMFilename} {lineNumber}: '{line}'"
            assert '≈ ' not in line, f"Unexpected space after ≈ in {rvESFMFilename} {lineNumber}: '{line}'"
            for characterMarker in BibleOrgSysGlobals.USFMCharacterMarkers:
                assert line.count( f'\\{characterMarker} ') == line.count( f'\\{characterMarker}*'), f"{characterMarker} marker mismatch in {rvESFMFilename} {lineNumber}: '{line}'"
                assert  f' \\{characterMarker}* 'not in line, f"doubled spaces around close {characterMarker} marker {rvESFMFilename} {lineNumber}: '{line}'"
            assert doubledND not in line, f"Double \\nd in {rvESFMFilename} {lineNumber}: '{line}'"
            assert  badAddND not in line, f"\\nd inside \\add start {rvESFMFilename} {lineNumber}: '{line}'"
            assert  badNDAdd not in line, f"\\nd inside \\add end {rvESFMFilename} {lineNumber}: '{line}'"
            assert  ' ¦' not in line, f"Word number attached to space {rvESFMFilename} {lineNumber}: '{line}'"
            if '\\x* ' in line: # this can be ok if the xref directly follows other text
                logger = logging.critical if ' \\x ' in line else logging.warning
                logger( f"Double-check space after xref in {rvESFMFilename} {lineNumber}: '{line}'" )

    numChapters = lv.getNumChapters( BBB )
    if numChapters >= 1:
        for c in range( 1, numChapters+1 ):
            C = str(c)
            if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 3:
                vPrint( 'Info', DEBUGGING_THIS_MODULE, f"      Connecting words for {BBB} {C}…" )
            numVerses = lv.getNumVerses( BBB, c )
            if numVerses is None: # something unusual
                logging.critical( f"connect_OET_RV: no verses found for OET-LV {BBB} {C}" )
                continue
            havePsalmTitles = bos_books_codes_py.has_psalm_title( BBB, C )
            rvNumVerses = rv.getNumVerses( BBB, c ) # the OET-RV follows the original-language versification
            for v in range( 1, numVerses+1 ): # Note: some Psalms have an extra verse in OET-LV (because /d is v1)
                V = str(v)
                rvV = str(v-1) if havePsalmTitles and v>1 else V
                try:
                    rvVerseEntryList, _rvCcontextList = rv.getContextVerseData( (BBB, C, rvV) )
                except KeyError:
                    # Most of these are NOT a problem, so don't cry wolf about them.  The OET-LV uses
                    #   English versification, which sometimes gives a chapter one or more verses at
                    #   the end that the original language doesn't have, and the OET-RV follows the
                    #   original.  So the OET-RV chapter simply runs out before the OET-LV one, and
                    #   there is no OET-RV text for those verses to be connected to: skipping them is
                    #   the correct thing to do.  We measured all 139 such verses across the whole
                    #   Bible and every one of them is a contiguous run at the END of its chapter,
                    #   i.e. plain truncation, with no interior gap anywhere that would suggest a
                    #   verse has been misplaced and could be causing a wrong cross-connection.
                    if rvNumVerses and int(rvV) > rvNumVerses:
                        logging.info( f"OET-RV {BBB} {c} ends at verse {rvNumVerses}, "
                                      f"but OET-LV has {numVerses}, so skipping OET-LV {c}:{v} "
                                      f"(English versification has more verses in this chapter)" )
                    else:
                        # A verse missing from the MIDDLE of the chapter, or a chapter that the OET-RV
                        #   doesn't have at all, is a real difference that somebody should look at.
                        logging.critical( f"Seems we have no OET-RV {BBB} {c}:{v} -- versification issue? "
                                          f"(the OET-RV verse we wanted is {rvV}, and this OET-RV chapter "
                                          f"has {rvNumVerses if rvNumVerses else 'no'} verse(s))" )
                    continue
                # OET-RV has /d and v1 all inside v1, but we need to separate them out to match OET-LV correctly
                if havePsalmTitles and v in (1,2):
                    adjustedRvVerseEntryList = InternalBibleEntryList()
                    for rvEntry in rvVerseEntryList:
                        rvMarker = rvEntry.getMarker()
                        if v==1 and rvMarker == 'v~': continue # don't want these
                        if v==2 and rvMarker == 'd': continue # don't want this
                        adjustedRvVerseEntryList.append( rvEntry )
                    rvVerseEntryList = adjustedRvVerseEntryList
                try:
                    lvVerseEntryList, _lvCcontextList = lv.getContextVerseData( (BBB, C, V) )
                except KeyError:
                    logging.critical( f"Seems we have no OET-LV {BBB} {c}:{v} -- versification issue?" )
                    assert False, "We want to stop here"
                    continue
                # if BBB=='PSA' and v<3: # and c in (3,23,29)
                #     dPrint( 'Normal', DEBUGGING_THIS_MODULE, f"\nRV entries for {BBB} {C}:{V}: ({len(rvVerseEntryList)}) {rvVerseEntryList}")
                #     dPrint( 'Normal', DEBUGGING_THIS_MODULE, f"LV entries for {BBB} {C}:{V}: ({len(lvVerseEntryList)}) {lvVerseEntryList}")

                check_OET_RV_Verse( BBB, c, v, rvVerseEntryList, lvVerseEntryList ) # Check that any existing word numbers are in the expected range

                (numWordPhraseAdds,numWordPhraseNS), (numSimpleListedAdds,numSimpleListedAddsNS), (numProperNounAdds,numProperNounAddsNS), (numFirstPartMatchedAdds,numFirstPartMatchedAddsNS), (numManualMatchedAdds,numManualMatchedAddsNS), (numVerbSetAdds,numVerbSetNS), (numChangedNumberAdds,numChangedNumberNS), (numSpecialistAdds,numSpecialistNS), (numInOrderMatchedAdds,numInOrderMatchedAddsNS) \
                            = connect_OET_RV_Verse( BBB, c, v, rvVerseEntryList, lvVerseEntryList ) # updates state.rvESFMLines
                bookWordPhraseAdds += numWordPhraseAdds
                bookWordPhraseAddsNS += numWordPhraseNS
                bookSimpleListedAdds += numSimpleListedAdds + numVerbSetAdds
                bookSimpleListedAddsNS += numSimpleListedAddsNS + numVerbSetNS
                bookProperNounAdds += numProperNounAdds
                bookProperNounAddsNS += numProperNounAddsNS
                bookFirstPartMatchedAdds += numFirstPartMatchedAdds
                bookFirstPartMatchedAddsNS += numFirstPartMatchedAddsNS
                bookManualMatchedAdds += numManualMatchedAdds
                bookManualMatchedAddsNS += numManualMatchedAddsNS
                bookChangedNumberAdds += numChangedNumberAdds
                bookChangedNumberAddsNS += numChangedNumberNS
                bookSpecialistAdds += numSpecialistAdds
                bookSpecialistAddsNS += numSpecialistNS
                bookInOrderMatchedAdds += numInOrderMatchedAdds
                bookInOrderMatchedAddsNS += numInOrderMatchedAddsNS
    else:
        if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 4:
            dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"connect_OET_RV {BBB} has {numChapters} chapters!!!" )
        assert BBB in ('INT','FRT',)

    newESFMtext = '\n'.join( state.rvESFMLines ) \
                        .replace( '\\nd* \\nd ', ' ' ) # Concatenate consecutive nd fields
    if newESFMtext != state.rvESFMText:
        if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
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
        for wronglyOrderedCombo in ('+?','=?','<?','>?','≡?','&?','@?',' *?','#?','%?','^?','≈?'):
            assert wronglyOrderedCombo not in newESFMtext, f"Wrongly ordered combo check failed with '{wronglyOrderedCombo}' before saving {BBB} with '{newESFMtext[newESFMtext.index(wronglyOrderedCombo)-10:newESFMtext.index(wronglyOrderedCombo)+35]}'"
        with open( rvESFMFilepath, 'wt', encoding='UTF-8' ) as esfmFile:
            esfmFile.write( newESFMtext )
        if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 2:
            vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"    Did {bookWordPhraseAdds:,} word phrase adds, {bookSimpleListedAdds:,} simple listed adds, {bookProperNounAdds:,} proper noun adds, {bookFirstPartMatchedAdds:,} first part adds, {bookManualMatchedAdds:,} manual adds, {bookChangedNumberAdds:,} changed number adds, {bookRewordedAdds:,} reworded adds, {bookSpecialistAdds:,} specialist add span adds and {bookInOrderMatchedAdds:,} in-order adds for {BBB}." )
        if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 2:
            vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"    Did {bookWordPhraseAddsNS:,} word phrase NS, {bookSimpleListedAddsNS:,} simple listed NS, {bookProperNounAddsNS:,} proper noun NS, {bookFirstPartMatchedAddsNS:,} first part NS, {bookManualMatchedAddsNS:,} manual NS, {bookChangedNumberAddsNS:,} changed number NS, {bookRewordedAddsNS:,} reworded NS, {bookSpecialistAddsNS:,} specialist add span NS and {bookInOrderMatchedAddsNS:,} in-order NS for {BBB}." )
        if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 2:
            vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"      Saved OET-RV {BBB} {len(newESFMtext):,} bytes to {rvESFMFilepath}" )
    else:
        # assert bookSimpleListedAdds == bookProperNounAdds == 0
        if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 3:
            vPrint( 'Info', DEBUGGING_THIS_MODULE, f"    No changes made to OET-RV {BBB}." )

    # Say how much of this book is now connected to the OET-LV.
    #   We only do it here in 'fast' mode, because otherwise the per-testament and per-Bible
    #   figures (printed by connect_OET_RV() and main()) say the same thing for the whole book.
    bookNumWords,bookNumWordNumbered = countWordsAndWordNumbers( state.rvESFMLines )
    if BibleOrgSysGlobals.commandLineArguments.fastMode:
        reportWordNumberPercentage( f"OET-RV {BBB}", bookNumWords, bookNumWordNumbered )

    return bookWordPhraseAdds, bookWordPhraseAddsNS, bookSimpleListedAdds, bookSimpleListedAddsNS, bookProperNounAdds, bookProperNounAddsNS, bookFirstPartMatchedAdds, \
            bookFirstPartMatchedAddsNS, bookManualMatchedAdds, bookManualMatchedAddsNS, bookChangedNumberAdds, \
            bookChangedNumberAddsNS, bookSpecialistAdds, bookSpecialistAddsNS, bookInOrderMatchedAdds, \
            bookInOrderMatchedAddsNS, bookNumWords, bookNumWordNumbered
# end of connect_OET-RV_words_via_OET-LV.connect_OET_RV_book


wordLinkRegex = re.compile( '¦[1-9][0-9]{0,5}' )
def check_OET_RV_Verse( BBB:str, c:int,v:int, rvEntryList, lvEntryList ) -> None:
    """
    If the OET-RV verse has any existing word numbers,
        check against the OET-LV verse to ensure that they're in the correct range.

    This check is specifically to catch copy and paste errors where a word number accidentally gets wrongly copied into a different verse.
    """
    # fnPrint( DEBUGGING_THIS_MODULE, f"connect_OET_RV( {BBB} {c}:{v} {len(rvEntryList)}, {len(lvEntryList)} )" )
    NT = bos_books_codes_py.is_new_testament_nr( BBB )
    if NT:
        assert state.wordTableHeaderList['NT'].index('VLTGlossWords')+1 == GLOSS_COLUMN__NUMBER, f"{state.wordTableHeaderList['NT'].index('VLTGlossWords')+1=} {GLOSS_COLUMN__NUMBER=} {state.wordTableHeaderList=}" # Check we have the correct column below

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
            elif BBB == 'PSA':
                logging.error( f"OET-RV {BBB} {c}:{v} {discovered_RV_word_number=} OUT OF RANGE IN (PSALM VERSIFICATION MISMATCH???) {minLVWordNumber=} {maxLVWordNumber=} from {discovered_OET_RV_word_numbers=}" )
            else:
                raise ValueError( f"OET-RV {BBB} {c}:{v} {discovered_RV_word_number=} OUT OF RANGE {minLVWordNumber=} {maxLVWordNumber=} from {discovered_OET_RV_word_numbers=}" )
# end of connect_OET-RV_words_via_OET-LV.check_OET_RV_Verse


GLOSS_COLUMN__NUMBER = 5
def connect_OET_RV_Verse( BBB:str, c:int,v:int, rvEntryList, lvEntryList ) -> Tuple[Tuple[int,int],Tuple[int,int],Tuple[int,int],Tuple[int,int],Tuple[int,int],Tuple[int,int],Tuple[int,int],Tuple[int,int],Tuple[int,int]]:
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
    NT = bos_books_codes_py.is_new_testament_nr( BBB )
    if NT:
        assert state.wordTableHeaderList['NT'].index('VLTGlossWords')+1 == GLOSS_COLUMN__NUMBER, f"{state.wordTableHeaderList['NT'].index('VLTGlossWords')+1=} {GLOSS_COLUMN__NUMBER=} {state.wordTableHeaderList=}" # Check we have the correct column below

    rvText = ''
    for rvEntry in rvEntryList:
        rvMarker, rvRest = rvEntry.getMarker(), rvEntry.getCleanText()
        # print( f"OET-RV {connectRef} {rvMarker}='{rvRest}'")
        if rvMarker in ('v~','d'):
            rvText = f"{rvText}{' ' if rvText else ''}{rvRest}"
    lvText = ''
    for lvEntry in lvEntryList:
        lvMarker,lvRest = lvEntry.getMarker(), lvEntry.getCleanText()
        if lvMarker == 'v~':
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
    if not rvText or not lvText: return (0,0), (0,0), (0,0), (0,0), (0,0), (0,0), (0,0), (0,0), (0,0)

    # A U+21D4 double arrow at the start of the OET-RV text means the translator did the
    #   LAST half of the OET-LV verse first, so the word order runs backwards from here on.
    #   (e.g. Mark 3:10 '⇔and a crowd...' comes before the LV's first clause.)
    reversedOrder = rvText.lstrip().startswith( ORDER_REVERSAL_CHARACTER )
    # The exposed '\add' codes are NOT removed from this text, because splitExposedAddSpan() has
    #   to be able to see which code each exposed span has
    rvWords,rvAddSpans = getRVWordsAndAddSpans( rvText, connectRef )
    lvAdjText = lvText.replace('_',' ').replace('=',' ').replace('÷',' ') \
                .replace('˱','').replace('˲','') \
                .replace('0/','0 ').replace('1/','1 ').replace('2/','2 ').replace('3/','3 ').replace('4/','4 ').replace('5/','5 ').replace('6/','6 ').replace('7/','7 ').replace('8/','8 ').replace('9/','9 ') \
                .replace('.','').replace(',','').replace(':','').replace(';','').replace('?','').replace('!','') \
                .replace( '(', '').replace( ')', '' ) \
                .replace('   ',' ').replace('  ',' ').strip()
    if lvAdjText.startswith( '/' ): lvAdjText = lvAdjText[1:]
    # print( f"({len(rvAdjText)}) {rvAdjText=}")
    # print( f"({len(lvAdjText)}) {lvAdjText=}")
    if not rvWords or not lvAdjText: return (0,0), (0,0), (0,0), (0,0), (0,0), (0,0), (0,0), (0,0), (0,0)

    lvWords = lvAdjText.split( ' ' )
    for rvWord in rvWords:
        assert rvWord.count( '¦' ) <= 1 or '-' in rvWord, f"Bad {rvWord=} from {BBB} {c}:{v} {lvText=}"
    # print( f"({len(rvWords)}) {rvWords=}")
    # print( f"({len(lvWords)}) {lvWords=}")

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

    # The '\add' markers are already gone from the OET-RV text above, so all that is left of a
    #   specialist span there is the code on the front of its first word, which we treat as a
    #   one-word span.  The text in the OET-RV file still HAS the markers, so we use that to get
    #   the real start and end of each span (which is what lets us number, say, both words of
    #   Mark 5:12 '\add @the demons\add*'), as long as it gives us the same words.
    rvLiveText = getLiveRVVerseText( BBB, c,v )
    if rvLiveText:
        liveWords,liveAddSpans = getRVWordsAndAddSpans( rvLiveText, connectRef )
        if liveWords == rvWords: rvAddSpans = liveAddSpans
        else:
            logging.warning( f"Not using the '\\add' span starts/ends of {BBB} {c}:{v} because the two OET-RV texts gave different words" )
            if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"{BBB} {c}:{v}\n  from object: {rvWords}\n  from file:   {liveWords}" )

    numWordPhraseAdds,numWordPhraseNS = matchWordPhrases( BBB, c,v, rvWords, lvWords, reversedOrder )
    numSpecialistAdds,numSpecialistNS = matchSpecialistAddSpans( BBB, c,v, rvWords, rvAddSpans, lvWords )
    numSimpleListedAdds,numSimpleListedNS = matchOurListedSimpleWords( BBB, c,v, rvWords, lvWords )
    numVerbSetAdds,numVerbSetNS = matchVerbSets( BBB, c,v, rvWords, lvWords )

    # Now get the uppercase words
    rvUpperWords = [rvWord for rvWord in rvWords if rvWord[0].isupper()]
    lvUpperWords = [lvWord for lvWord in lvWords if (lvWord[0].isupper() or (lvWord[0] in 'ʼˊ' and lvWord[1].isupper()))]
    # print( f"{rvText=} {lvText=}" )

    if lvUpperWords and lvText[0].isupper(): # Try to determine why the first word was capitalised
        if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
            dPrint( 'Info', DEBUGGING_THIS_MODULE, f"{lvUpperWords=} from {lvText=}")
        firstLVUpperWord, firstLVUpperNumber = lvUpperWords[0].split( '¦' )
        rowForFirstLVUpperWord = state.wordTable['NT' if NT else 'OT'][int(firstLVUpperNumber)]
        if NT:
            firstLVUpperWordCapsFlags = rowForFirstLVUpperWord[state.wordTableHeaderList['NT'].index('GlossCaps')]
            # print( f"{firstLVUpperWordCapsFlags=} from {rowForFirstLVUpperWord=}" )
            if 'G' not in firstLVUpperWordCapsFlags and 'W' not in firstLVUpperWordCapsFlags and firstLVUpperWord!='I':
                # print( f"Removing first LV Uppercase word: '{lvUpperWords[0]}' with '{firstLVUpperWordCapsFlags}'")
                lvUpperWords.pop(0) # Throw away the first word because it might just be capitalised for being at the beginning of the sentence.
        else: # OT
            firstLVUpperWordCapsFlags = rowForFirstLVUpperWord[state.wordTableHeaderList['OT'].index('GlossCapitalisation')]
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

    numChangedNumberAdds,numChangedNumberNS = matchWordsWithChangedNumbers( BBB, c,v, rvWords, rvAddSpans, lvWords )

    # Run this LAST, so that it can only take the words the other matchers didn't want
    numInOrderMatches,numInOrderMatchesNS = matchWordsInOrder( BBB, c,v, rvText, rvWords, lvWords, reversedOrder )

    return (numWordPhraseAdds,numWordPhraseNS), \
           (numSimpleListedAdds,numSimpleListedNS), \
           (numIdenticalProperNounAdds+numAdjustedProperNounAdds,numIdenticalProperNounNS+numAdjustedProperNounNS), \
           (numFirstPartMatchedWords,numFirstPartMatchedWordsNS), \
           (numHandmatches,numHandmatchesNS), \
           (numVerbSetAdds,numVerbSetNS), \
           (numChangedNumberAdds,numChangedNumberNS), \
           (numSpecialistAdds,numSpecialistNS), \
           (numInOrderMatches,numInOrderMatchesNS)
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
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag:
        fnPrint( DEBUGGING_THIS_MODULE, f"matchIdenticalProperNouns( {BBB} {c}:{v} {rvCapitalisedWordList}, {lvCapitalisedWordList} )" )
    assert rvCapitalisedWordList and lvCapitalisedWordList

    NT = bos_books_codes_py.is_new_testament_nr( BBB )

    # But we don't want any rvWords that are already tagged
    numAdded = numNS = 0
    numRemovedRV = 0 # Extra work because we're deleting from same list that we're iterating through (a copy of)
    for rvN,rvCapitalisedWord in enumerate( rvCapitalisedWordList[:] ):
        # print( f"{BBB} {c}:{v} {rvN} {rvCapitalisedWord=} from {rvCapitalisedWordList}")
        if '¦' in rvCapitalisedWord:
            _rvCapitalisedWord, rvWordNumber = rvCapitalisedWord.split('¦')
            if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  matchIdenticalProperNouns( {BBB} {c}:{v} ) removing already tagged '{rvCapitalisedWord}' from RV list…")
            rvCapitalisedWordList.pop( rvN - numRemovedRV )
            numRemovedRV += 1
            numRemovedLV = 0 # Extra work because we're deleting from same list that we're iterating through (a copy of)
            for lvN,lvCapitalisedWord in enumerate( lvCapitalisedWordList[:] ):
                if lvCapitalisedWord.endswith( f'¦{rvWordNumber}' ):
                    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
                        dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  matchIdenticalProperNouns( {BBB} {c}:{v} ) removing already tagged '{lvCapitalisedWord}' from LV list…")
                    lvCapitalisedWordList.pop( lvN - numRemovedLV )
                    numRemovedLV += 1
    if not rvCapitalisedWordList or not lvCapitalisedWordList:
        return numAdded,numNS # nothing left to do here

    if len(rvCapitalisedWordList)==1 and len(lvCapitalisedWordList)==1: # easy case!
        assert rvCapitalisedWordList[0].replace("'",'').isalpha(), f"{rvCapitalisedWordList=}" # It might contain an apostrophe
        # print( f"{rvCapitalisedWordList=} {lvCapitalisedWordList=}" )
        assert '¦' in lvCapitalisedWordList[0], f"{lvCapitalisedWordList[0]=} from {lvCapitalisedWordList=}"
        capitalisedNoun,wordNumber,wordRow = getLVWordRow( lvCapitalisedWordList[0], 'NT' if NT else 'OT' )
        if NT:
            wordRole = wordRow[state.wordTableHeaderList['NT'].index('Role')]
            if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  '{capitalisedNoun}' {wordRole}" )
            if wordRole == 'N': # let's assume it's a proper noun
                # print( f"matchIdenticalProperNouns {BBB} {c}:{v} adding number to {rvCapitalisedWordList[0]}")
                result = addNumberToRVWord( BBB, c,v, rvCapitalisedWordList[0], wordNumber )
                if result:
                    numAdded += 1
                    if 'N' in wordRow[state.wordTableHeaderList['NT'].index('GlossCaps')]:
                        numNS += 1
        else: # OT
            glossCaps = wordRow[state.wordTableHeaderList['OT'].index('GlossCapitalisation')]
            if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  {capitalisedNoun=} {glossCaps=}" )
            if glossCaps != 'S': # start of sentence
                result = addNumberToRVWord( BBB, c,v, rvCapitalisedWordList[0], wordNumber )
                if result:
                    numAdded += 1
    else:
        # Try to connect identical spellings between the two lists one by one (regardless of order)
        for rvCapitalisedWord in rvCapitalisedWordList[:]:
            for lvCapitalisedWord in lvCapitalisedWordList[:]:
                assert '¦' in lvCapitalisedWord, f"{lvCapitalisedWordList=}"
                lvNoun = lvCapitalisedWord.split( '¦' )[0]
                if simplifyRVLVWord( lvNoun ) == simplifyRVLVWord( rvCapitalisedWord ):
                    capitalisedNoun,wordNumber,wordRow = getLVWordRow( lvCapitalisedWord, 'NT' if NT else 'OT' )
                    proceed = False
                    if NT:
                        if wordRow[state.wordTableHeaderList['NT'].index('Role')] == 'N': proceed = True
                    else:
                        if wordRow[state.wordTableHeaderList['OT'].index('GlossCapitalisation')] != 'S': proceed = True
                    if proceed:
                        result = addNumberToRVWord( BBB, c,v, rvCapitalisedWord, wordNumber )
                        if result:
                            numAdded += 1
                            if NT and 'N' in wordRow[state.wordTableHeaderList['NT'].index('GlossCaps')]:
                                numNS += 1
                            rvCapitalisedWordList.remove( rvCapitalisedWord )
                            lvCapitalisedWordList.remove( lvCapitalisedWord )
                    break
    return numAdded,numNS
# end of connect_OET-RV_words_via_OET-LV.matchIdenticalProperNouns


def matchAdjustedProperNouns( BBB:str, c:int,v:int, rvCapitalisedWordList:List[str], lvCapitalisedWordList:List[str] ) -> Tuple[int,int]:
    """
    Given a list of capitalised words from OET-RV and OET-LV,
        see if we can match any proper nouns using the ScriptedBibleEditor name tables
    """
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag:
        fnPrint( DEBUGGING_THIS_MODULE, f"matchAdjustedProperNouns( {BBB} {c}:{v} {rvCapitalisedWordList}, {lvCapitalisedWordList} )" )
    assert rvCapitalisedWordList and lvCapitalisedWordList

    NT = bos_books_codes_py.is_new_testament_nr( BBB )

    # But we don't want any rvWords that are already tagged
    numAdded = numNS = 0
    numRemovedRV = 0 # Extra work because we're deleting from same list that we're iterating through (a copy of)
    for rvN,rvCapitalisedWord in enumerate( rvCapitalisedWordList[:] ):
        # print( f"{BBB} {c}:{v} {rvN} {rvCapitalisedWord=} from {rvCapitalisedWordList}")
        if '¦' in rvCapitalisedWord:
            _rvCapitalisedWord, rvWordNumber = rvCapitalisedWord.split('¦')
            if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  matchAdjustedProperNouns( {BBB} {c}:{v} ) removing already tagged '{rvCapitalisedWord}' from RV list…")
            rvCapitalisedWordList.pop( rvN - numRemovedRV )
            numRemovedRV += 1
            numRemovedLV = 0 # Extra work because we're deleting from same list that we're iterating through (a copy of)
            for lvN,lvCapitalisedWord in enumerate( lvCapitalisedWordList[:] ):
                if lvCapitalisedWord.endswith( f'¦{rvWordNumber}' ):
                    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
                        dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  matchAdjustedProperNouns( {BBB} {c}:{v} ) removing already tagged '{lvCapitalisedWord}' from LV list…")
                    lvCapitalisedWordList.pop( lvN - numRemovedLV )
                    numRemovedLV += 1
    if not rvCapitalisedWordList or not lvCapitalisedWordList:
        return numAdded,numNS # nothing left to do here

    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 4:
        dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"\n{BBB} {c}:{v} {rvCapitalisedWordList=} {lvCapitalisedWordList=}" )
    for lvCapitalisedWord in lvCapitalisedWordList:
        if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 4:
            dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"{lvCapitalisedWord=} from {lvCapitalisedWordList=}" )
        if '¦' not in lvCapitalisedWord:
            # TODO: Determine how/why this happened in DEU Beeroth
            logging.critical( f"Why didn't this word get a word number? {lvCapitalisedWord=} from {BBB} {c}:{v} {lvCapitalisedWordList=}" )
            continue
        assert lvCapitalisedWord.count( '¦' ) == 1, f"{BBB} {c}:{v} {lvCapitalisedWord=} from {lvCapitalisedWordList=}"
        capitalisedNoun,wordNumber,wordRow = getLVWordRow( lvCapitalisedWord, 'NT' if NT else 'OT' )

        for rvCapitalisedWord in rvCapitalisedWordList:
            if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 4:
                dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"{rvCapitalisedWord=} from {rvCapitalisedWordList=}" )
            assert rvCapitalisedWord.replace("'",'').isalpha(), f"{rvCapitalisedWordList=}" # It might contain an apostrophe
            if NT:
                wordRole = wordRow[state.wordTableHeaderList['NT'].index('Role')]
                if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 4:
                    dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"  matchAdjustedProperNouns NT '{capitalisedNoun}' {wordRole}" )
                if wordRole == 'N': # let's assume it's a proper noun
                    if baseNameInCandidates( capitalisedNoun, rvCapitalisedWord, 'NT' ) or baseNameInCandidates( capitalisedNoun, rvCapitalisedWord, 'NT_OT' ):
                        result = addNumberToRVWord( BBB, c,v, rvCapitalisedWord, wordNumber )
                        if result:
                            numAdded += 1
                        if 'N' in wordRow[state.wordTableHeaderList['NT'].index('GlossCaps')]:
                            numNS += 1
            else: # OT
                glossCaps = wordRow[state.wordTableHeaderList['OT'].index('GlossCapitalisation')]
                if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 4:
                    dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"  matchAdjustedProperNouns OT {capitalisedNoun=} {glossCaps=}" )
                if glossCaps != 'S': # start of sentence
                    if baseNameInCandidates( capitalisedNoun, rvCapitalisedWord, 'OT' ):
                        result = addNumberToRVWord( BBB, c,v, rvCapitalisedWord, wordNumber )
                        if result:
                            numAdded += 1
    return numAdded,numNS
# end of connect_OET-RV_words_via_OET-LV.matchAdjustedProperNouns


def baseNameInCandidates( capitalisedNoun:str, rvCapitalisedWord:str, nameTableKey:str ) -> bool:
    """Return True if the LV proper noun and the RV word are names recorded as
        alternatives in the command-table name lists.
    We look both names up through their normalised forms (see normalizeNameKey()),
        because the OET-LV spelling often differs from the OET-LV command-table key
        (e.g. the LV 'Dawid/(Dāvid)' against the command-table 'Dawid/(Dāwid)').
    """
    rvBase = rvCapitalisedWord
    if rvCapitalisedWord.endswith( "'s" ): rvBase = rvCapitalisedWord[:-2] # possessive
    for lvPart in splitNameKey( capitalisedNoun ):
        normalised = normalizeNameKey( lvPart )
        if not normalised: continue
        for something in state.namePartsIndex.get( normalised, () ):
            if something == rvCapitalisedWord or something == rvBase or f"{something}'s" == rvCapitalisedWord:
                if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
                    dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  Name match: LV '{lvPart}' ≈ RV '{rvCapitalisedWord}' (via '{something}' of {normalised})" )
                return True
    # Also let the unchanged (exact) spelling match, as before
    for something in state.nameTables[nameTableKey].get( capitalisedNoun, () ):
        if something == rvCapitalisedWord or something == rvBase or f"{something}'s" == rvCapitalisedWord:
            return True
    return False
# end of connect_OET-RV_words_via_OET-LV.baseNameInCandidates


def matchOurListedSimpleWords( BBB:str, c:int,v:int, rvWordList:List[str], lvWordList:List[str] ) -> Tuple[int,int]:
    """
    If the simple word (e.g., nouns) only occur once in the RV verse and once in the LV verse,
        we assume that we can match them, i.e., copy the wordlink numbers from the LV into the RV.
    """
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag:
        fnPrint( DEBUGGING_THIS_MODULE, f"matchOurListedSimpleWords( {BBB} {c}:{v} {rvWordList}, {lvWordList} )" )
    assert rvWordList and lvWordList

    NT = bos_books_codes_py.is_new_testament_nr( BBB )

    numAdded = numNS = 0
    nounWords = set(SIMPLE_NOUNS) | set(verbalNouns) # Only nouns get number-variant matching; verbs and adjectives are handled elsewhere
    for simpleNoun in SIMPLE_WORDS:
        # print( f"{simpleNoun}" )
        searchForms = (simpleNoun,)
        if simpleNoun in nounWords:
            searchForms = (simpleNoun,) + tuple(numberVariants( simpleNoun ))
        lvIndexList = []
        for lvN,lvWord in enumerate( lvWordList ):
            # assert lvWord.isalpha(), f"'{lvWord}'" # Might contain an apostrophe
            if any( f'{form}¦' in lvWord for form in searchForms ):
                lvIndexList.append( lvN )
        if not lvIndexList: continue
        # print( f"{BBB} {c}:{v} {simpleNoun=} {lvIndexList=}" )
        rvIndexList = []
        for rvN,rvWord in enumerate( rvWordList ):
            # assert rvWord.isalpha(), f"'{rvWord}'" # Might contain an apostrophe
            if rvWord == simpleNoun or ( simpleNoun in nounWords and rvWord in numberVariants( simpleNoun ) ):
                rvIndexList.append( rvN )
        if not rvIndexList: continue

        if len(rvIndexList) != 1 or len(lvIndexList) != 1: # then I don't think we can guarantee matching the right words
            # Skip just this word and carry on with the rest of SIMPLE_WORDS, because a word that
            #   occurs twice in the verse says nothing about any of the other words in it
            continue
        assert len(rvIndexList) == len(lvIndexList), f"{BBB} {c}:{v} {simpleNoun=} {rvIndexList=} {lvIndexList=}"

        lvNumbers = []
        for lvN in lvIndexList:
            assert '¦' in lvWordList[lvN], f"{lvN=} {lvWordList[lvN]=} from {lvWordList=}"
            lvNoun,lvWordNumber,lvWordRow = getLVWordRow( lvWordList[lvN], 'NT' if NT else 'OT' )
            lvNumbers.append( lvWordNumber )
        assert len(lvNumbers) == 1 # NOT TRUE: If there's two 'camels' in the verse, we expect both to have the same word number
        for rvN in rvIndexList:
            rvNoun = rvWordList[rvN]
            if rvNoun.lower() == lvNoun.lower() or ( simpleNoun in nounWords and ( lvNoun.lower() in numberVariants( rvNoun.lower() ) or rvNoun.lower() in numberVariants( lvNoun.lower() ) ) ):
                if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
                    dPrint( 'Info', DEBUGGING_THIS_MODULE, f"matchOurListedSimpleWords() from {BBB} {c}:{v} {rvN=} {lvWordNumber=} {lvNoun=} is adding a number to RV {rvNoun=}")
                result = addNumberToRVWord( BBB, c,v, rvNoun, lvWordNumber )
                if result:
                    numAdded += 1
                    if NT and 'N' in state.wordTable['NT' if NT else 'OT'][lvWordNumber][state.wordTableHeaderList['NT' if NT else 'OT'].index('GlossCaps')]:
                        numNS += 1
            # else:
            #     dPrint( 'Normal', DEBUGGING_THIS_MODULE, f"ERROR matchOurListedSimpleWords() would have connected LV '{lvNoun}' to RV '{rvNoun}' at {BBB} {c}:{v} {rvN=}")

    return numAdded,numNS
# end of connect_OET-RV_words_via_OET-LV.matchOurListedSimpleWords


def matchVerbSets( BBB:str, c:int,v:int, rvWordList:List[str], lvWordList:List[str] ) -> Tuple[int,int]:
    """
    Use SIMPLE_VERB_SETS to match different forms of the same verb.

    When a verb from a set appears once in the RV and once in the LV (in any form from the set),
        we assume that we can match them, i.e., copy the wordlink numbers from the LV into the RV.

    This handles tense changes, e.g., RV 'untie' matching LV 'untying'.
    """
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag:
        fnPrint( DEBUGGING_THIS_MODULE, f"matchVerbSets( {BBB} {c}:{v} {rvWordList}, {lvWordList} )" )
    assert rvWordList and lvWordList

    NT = bos_books_codes_py.is_new_testament_nr( BBB )

    numAdded = numNS = 0

    # For each verb set, check if any form appears in both RV and LV
    for setIndex, verbSet in enumerate(SIMPLE_VERB_SETS):
        # Find all forms of this verb set in the LV
        lvIndexes = []
        for lvN, lvWord in enumerate( lvWordList ):
            # Extract the word part (without word number)
            lvWordPart = lvWord.split('¦')[0] if '¦' in lvWord else lvWord
            if lvWordPart in verbSet:
                lvIndexes.append( lvN )

        if len(lvIndexes) != 1: continue  # Need exactly one occurrence in LV

        # Find all forms of this verb set in the RV
        rvIndexes = []
        for rvN, rvWord in enumerate( rvWordList ):
            rvWordPart = rvWord.split('¦')[0] if '¦' in rvWord else rvWord
            if rvWordPart in verbSet:
                rvIndexes.append( rvN )

        if len(rvIndexes) != 1: continue  # Need exactly one occurrence in RV

        # We have exactly one form in each - connect them
        rvWord = rvWordList[rvIndexes[0]]
        if '¦' not in rvWord:
            lvWordStr = lvWordList[lvIndexes[0]]
            assert '¦' in lvWordStr, f"{lvIndexes[0]=} {lvWordStr=} from {lvWordList=}"
            lvWord, lvWordNumber, lvWordRow = getLVWordRow( lvWordStr, 'NT' if NT else 'OT' )
            if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"matchVerbSets() is adding a number to RV '{rvWord}' from '{lvWord}' at {BBB} {c}:{v}")
            result = addNumberToRVWord( BBB, c,v, rvWord, lvWordNumber )
            if result:
                numAdded += 1
                if NT and 'N' in lvWordRow[state.wordTableHeaderList['NT' if NT else 'OT'].index('GlossCaps')]:
                    numNS += 1

    return numAdded,numNS
# end of connect_OET-RV_words_via_OET-LV.matchVerbSets


def matchWordsFirstParts( BBB:str, c:int,v:int, rvWordList:List[str], lvWordList:List[str] ) -> Tuple[int,int]:
    """
    If the longish word only occurs once in the LV word list
        and a similar starting word only occurs on in the RV word list
            we assume that we can match them, i.e., copy the wordlink numbers from the LV into the RV.

    This handles tense changes, e.g., LV despising and RV despised.
    """
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag:
        fnPrint( DEBUGGING_THIS_MODULE, f"matchWordsFirstParts( {BBB} {c}:{v} {rvWordList}, {lvWordList} )" )
    assert rvWordList and lvWordList

    NT = bos_books_codes_py.is_new_testament_nr( BBB )

    # Firstly make a matching list of LV words without the word numbers
    simpleLVWordList = []
    for lvWordStr in lvWordList:
        try: lvWord, lvNumber = lvWordStr.split( '¦' )
        except ValueError:
            if lvWordStr != 'to':
                logging.critical( f"matchWordsFirstParts failed on {lvWordStr=} from {BBB} {c}:{v} {lvWordList=}" )
            lvWord = lvWordStr # One or two little mess-ups
        simpleLVWordList.append( lvWord )

    numAdded = numNS = 0
    for lvIx,lvWord in enumerate( simpleLVWordList ):
        if len(lvWord) < 5: continue # We only process longer words
        if simpleLVWordList.count( lvWord ) != 1: continue # We can't distinguish between two usages in one verse
        if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 4:
            dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"{lvWord=} {lvNumber=}" )

        lvWordStart = lvWord[:5] # Get the first 5 letters
        if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 4:
            dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"  Looking for RV '{lvWordStart}' from LV '{lvWord}'" )
        rvIndexes = []
        for rvIx,rvWord in enumerate( rvWordList ):
            if rvWord.startswith( lvWordStart ):
                if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 4:
                    dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"  Found RV '{rvWord}' in {BBB} {c}:{v}")
                rvIndexes.append( rvIx )

        if len(rvIndexes) == 1: # Only one RV word starts with those same letters
            rvWord = rvWordList[rvIndexes[0]]
            if '¦' not in rvWord:
                assert '¦' in lvWordList[lvIx], f"{lvIx=} {lvWordList[lvIx]=} from {lvWordList=}"
                lvWord,lvWordNumber,lvWordRow = getLVWordRow( lvWordList[lvIx], 'NT' if NT else 'OT' )
                if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
                    dPrint( 'Info', DEBUGGING_THIS_MODULE, f"matchWordsFirstParts() is adding a number to RV '{rvWord}' from '{lvWord}' at {BBB} {c}:{v} {rvIx=}")
                result = addNumberToRVWord( BBB, c,v, rvWord, lvWordNumber )
                if result:
                    numAdded += 1
                    if NT and 'N' in lvWordRow[state.wordTableHeaderList['NT' if NT else 'OT'].index('GlossCaps')]:
                        numNS += 1
                else:
                    logging.warning( f"Got addNumberToRVWord( {BBB} {c}:{v} '{rvWord}' {lvWordNumber} ) result = {result}" )
                    # why_did_we_fail

    return numAdded,numNS
# end of connect_OET-RV_words_via_OET-LV.matchWordsFirstParts


# The number of matching leading characters we need before we trust an OET-RV word and an
#   OET-LV word to be the same word, e.g. RV 'money-changers' against LV 'moneychangers'.
#   Five (not seven) because we also check that the alignment is order-preserving and
#   unambiguous, which prevents false matches like 'protesting' vs 'prostrating'.
#   This allows inflectional matches like 'immersing'/'immersed' (6 chars) and
#   'forgiveness'/'forgiven' (6 chars).
ORDER_MATCH_PREFIX_LENGTH = 5

# The shortest word that matchWordsInOrder() will connect on the strength of being the SAME word,
#   which is much less than ORDER_MATCH_PREFIX_LENGTH, because an exact match is exact however
#   short it is: the OET-RV 'put' of Mark 12:1 is the OET-LV 'put¦32436' and nothing else.
#   Two letters, because matchWordsInOrder() only connects a word when every equally good
#   order-preserving alignment agrees on it (see bestMonotoneAlignmentScore()), and even the
#   one and two letter words come out safely on a full-corpus run: the RV 'the' of CO1 1:9 is the
#   LV 'the¦113151' and not any of the other 'the's of the verse.
MIN_EXACT_MATCH_WORD_LENGTH = 2

# The little English words that matchWordsInOrder() must not connect just because they are short
#   and exactly the same on both sides, because the OET-RV translators have deliberately not
#   numbered them: an OET-LV 'and¦1234' and an OET-RV 'and' tell us nothing about which of the
#   'and's of a verse is which, and a wrong word number is much worse than a missing one.
#   These are the English closed-class words, i.e. the ones that carry the grammar of a sentence
#   rather than its meaning, sorted and grouped by what they are below.  Content words are not
#   here, so the short content words do get connected, e.g. the OET-RV 'put' of Mark 12:1.
#   (The one or two letter members of these classes, e.g. 'a', 'of', 'to', 'is', 'or', don't need to
#       be here, because they are already shorter than MIN_EXACT_MATCH_WORD_LENGTH.  Longer ones
#       like 'because' and 'although' are already long enough to match on their own.)
#   This list is only consulted for the short words that MIN_EXACT_MATCH_WORD_LENGTH lets through,
#   so it can never take away a word number that the longer-word rules have already given.
#   It is now EMPTY, i.e. we no longer hold these words back.  matchWordsInOrder() only numbers a
#   word when every equally good order-preserving alignment agrees on it, and that proved strong
#   enough to number the little words safely across the whole Bible, so this list only remains as a
#   record of the words that were being held back, and of why we used to do that.  Put a word back
#   in here to hold that one word back again.
LITTLE_FUNCTION_WORDS = {
    # determiners
    'all', 'another', 'any', 'both', 'each', 'either', 'every', 'few', 'her', 'his', 'its', 'least',
    'less', 'many', 'more', 'most', 'much', 'neither', 'none', 'one', 'ones', 'other', 'others', 'our',
    'own', 'some', 'such', 'that', 'the', 'their', 'these', 'this', 'those', 'your',
    # pronouns
    'anyone', 'hers', 'herself', 'him', 'himself', 'itself', 'mine', 'myself', 'nobody', 'ours',
    'ourselves', 'she', 'someone', 'them', 'themselves', 'they', 'what', 'whatever', 'which', 'who',
    'whom', 'whose', 'you', 'yours', 'yourself', 'yourselves',
    # prepositions
    'about', 'above', 'across', 'after', 'against', 'ahead', 'along', 'among', 'around', 'atop', 'before',
    'behind', 'below', 'beside', 'besides', 'between', 'beyond', 'during', 'from', 'into', 'like',
    'near', 'off', 'onto', 'out', 'over', 'since', 'through', 'till', 'toward', 'towards', 'under',
    'until', 'unto', 'up', 'upon', 'via', 'with', 'within', 'without',
    # conjunctions
    'and', 'but', 'for', 'nor', 'than', 'though', 'unless', 'while', 'yet',
    # auxiliaries and copulas
    'are', 'been', 'being', 'can', 'cannot', 'could', 'did', 'does', 'doing', 'had', 'has', 'have',
    'may', 'might', 'must', 'ought', 'shall', 'should', 'was', 'were', 'will', 'would',
    # adverbs and particles
    'again', 'ago', 'already', 'also', 'always', 'away', 'back', 'down', 'else', 'enough', 'even',
    'ever', 'far', 'here', 'how', 'just', 'never', 'not', 'now', 'often', 'once', 'only', 'quite',
    'rather', 'still', 'then', 'there', 'thus', 'too', 'very', 'when', 'where', 'why', 'yes',
    # other little grammar words
    'let', 'lets', 'well',
}
# We keep the words above on record, but we don't hold any of them back, so matchWordsInOrder()
#   is free to number them.  This is what makes them a record only.
LITTLE_FUNCTION_WORDS_HELD_BACK = LITTLE_FUNCTION_WORDS
LITTLE_FUNCTION_WORDS = set()

def unSimplifyRVWord( rvWord:str ) -> str:
    """
    Undo simplifyRVLVWord() as far as addNumberToRVWord() needs, i.e. give back a word that
        actually appears in the OET-RV text, so it can be found there.

    We take the parts off that the OET-RV word list adds but the live text doesn't have, namely a
        leading exposed '\add' code and a trailing '\add*' close marker (which only the last word
        on a line has).  We deliberately keep the original capitalisation, because
        addNumberToRVWord() searches for the word as the OET-RV spells it, so the OET-RV
        'Whenever' of Mark 9:18 has to be looked for as 'Whenever' and not as 'whenever'.
    """
    if '\\' in rvWord: rvWord = addCloseMarkerAnywhereRegex.sub( '', rvWord )
    _addCode,rvWord = splitAddCode( rvWord )
    return rvWord
# end of unSimplifyRVWord


# The OET-RV and the OET-LV sometimes use different English words for the one OET-LV word, so we
#   let matchWordsInOrder() connect those as well, e.g. the OET-RV 'Whenever' of Mark 6:10 is the
#   OET-LV 'Wherever¦26350'.  We only put a word here when it really does mean the same thing,
#   because a synonym match is weaker evidence than the same word.
#   Each entry is { an OET-RV word: the OET-LV words that it can stand for }, and we also work it
#   the other way round, so it doesn't matter which side of a pair we list.
EQUIVALENT_LV_RV_WORDS = { # All lower case, i.e. the simplifyRVLVWord() forms
    'whenever': { 'wherever' }, # The OET-LV 'wherever' is a temporal 'whenever' in Mark 6:10, 6:56 and 9:18
    
    # NT-wide equivalences (single-word, from RV-LV analysis)
    'begins': { 'beginning' },
    'turned': { 'became' },
    'announcing': { 'proclaiming' },
    'immersed': { 'immersing', 'immersion' },
    'forgiven': { 'forgiveness' },
    'many': { 'all' },
    'went': { 'was_going', 'came', 'going' },
    'hear': { 'hearing' },
    'asked': { 'asking' },
    'dressed': { 'having_dressed', 'dressed' },
    'lived': { 'living', 'feeding' },
    'also': { 'and' },
    'man': { 'one' },
    'soon': { 'shortly' },
    'bend': { 'stoop' },
    'arrested': { 'to_be_given_over', 'given_over' },
    'promised': { 'fulfilled' },
    'turn': { 'repentance' },
    'fishermen': { 'fishers' },
    'left': { 'having_left', 'followed' },
    'sons': { 'son' },
    'leaving': { 'having_left' },
    'taught': { 'was_teaching' },
    'regular': { 'scribes' },
    'demon-possessed': { 'with an unclean spirit' },
    'yelled': { 'called' },
    'scolded': { 'gave rebuke' },
    'threw': { 'having_convulsed' },
    'cried': { 'having_called' },
    'asked': { 'debating' },
    'just': { 'this' },
    'spread': { 'came_out' },
    'brought': { 'bringing' },
    'healed': { 'healed' },
    'commanded': { 'throw_out' },
    'got': { 'having_risen_up' },
    'quiet': { 'a deserted' },
    'came': { 'searched' },
    'we': { 'we_may_be_going elsewhere into' },
    'other': { 'neighbouring' },
    'villages': { 'villages' },
    'driving': { 'throwing_out' },
    'felt': { 'having_been_feeling' },
    'reached': { 'having_stretched_out' },
    'sent': { 'sent him_forth', 'is_sending' },
    'started': { 'began to_be_proclaiming much and to_be_spreading_abroad' },
    'spreading': { 'spreading_abroad the message' },
    'could': { 'no_longer able' },
    
    # High-frequency function word variations (NT-wide)
    'that': { 'which', 'who' },
    'who': { 'whom', 'who' },
    'them': { 'those', 'them' },
    'up': { 'up' },
    'out': { 'out', 'forth' },
    'so': { 'so', 'thus' },
    'just': { 'just', 'only' },
    'like': { 'like', 'as' },
    'their': { 'their', 'theirs' },
    'when': { 'when', 'whenever' },
    'what': { 'what', 'whatever' },
    'do': { 'do', 'did', 'does' },
    'have': { 'have', 'has', 'had' },
    'one': { 'one', 'someone' },
    'some': { 'some', 'any' },
    'there': { 'there', 'here' },
    'then': { 'then', 'when' },
    'than': { 'than', 'from' },
    'into': { 'into', 'in', 'to' },
    'upon': { 'upon', 'on' },
    'unto': { 'unto', 'to' },
    'because': { 'because', 'for', 'since' },
    'although': { 'although', 'though' },
    'until': { 'until', 'till' },
    'while': { 'while', 'whilst' },
    'against': { 'against', 'towards' },
    'before': { 'before', 'ere' },
    'after': { 'after', 'later' },
    'since': { 'since', 'because' },
    'through': { 'through', 'thru' },
    'during': { 'during', 'in' },
    'without': { 'without', 'except' },
    'within': { 'within', 'in' },
    'beneath': { 'beneath', 'under' },
    'beside': { 'beside', 'by' },
    'between': { 'between', 'among' },
    'beyond': { 'beyond', 'past' },
    'around': { 'around', 'about' },
    'across': { 'across', 'over' },
    'along': { 'along', 'by' },
    'amid': { 'amid', 'among' },
    'among': { 'among', 'amidst' },
    'toward': { 'toward', 'towards' },
    'towards': { 'towards', 'toward' },
    'within': { 'within', 'inside' },
    'without': { 'without', 'outside' },
}
EQUIVALENT_LV_RV_WORDS.update( { lvWord:{rvWord} for rvWord,lvWords in EQUIVALENT_LV_RV_WORDS.items() for lvWord in lvWords } )

# The U+21D4 double arrow that the translator puts at the start of an OET-RV verse
#   whose clauses were translated in the opposite order to the OET-LV verse.
ORDER_REVERSAL_CHARACTER = '\u21d4'


def simplifyRVLVWord( word:str ) -> str:
    """
    Reduce an OET-RV or OET-LV word to a plain lowercase form so we can compare the two.

    We throw away edge punctuation, transliteration accents, hyphens and the possessive 's,
        because 'Preparation' and 'preparation' are the same word to us, but
        'mother-in-law' and 'mother' are not (and 'money-changers' and 'moneychangers' are).
    """
    word = re.sub( r"[ʼˊʹʺ]", '', word ) # Transliteration accents, e.g. LV 'Yəhōshūˊa'
    word = re.sub( r"[’']s$", '', word ) # Possessives
    word = re.sub( r"[-‐‑–]", '', word ) # Hyphens, anywhere in the word
    return word.lower().strip( '.,;:!?"“”‘’()' )
# end of simplifyRVLVWord


def scoreRVLVWords( rvWord:str, lvWord:str ) -> Optional[Tuple[str,int]]:
    """
    Score how confidently an OET-RV word and an OET-LV word are the same word.

    Returns a (description, score) tuple, or None if they are too different to connect.
    A wrong word number is much worse than a missing one, so we only score the four
        unambiguous kinds of match:
            •  the same word, however short it is, allowing for a case difference, so RV
                'Preparation' matches LV 'preparation' and RV 'put' matches LV 'put'
            •  the same word once its inflectional ending is allowed for, so RV
                'wineskin' matches LV 'wineskins'
            •  a long shared opening, so RV 'money-changers' matches LV 'moneychangers'
                and RV 'immerse' matches LV 'immersing'
            •  one of the EQUIVALENT_LV_RV_WORDS pairs, so RV 'Whenever' matches LV 'wherever'
    We deliberately do NOT score 'mother-in-law' against LV 'mother', or
        'demon-possessed' against LV 'demon', because those are different words.
    """
    r,l = simplifyRVLVWord( rvWord ), simplifyRVLVWord( lvWord )
    if r == l and len(r) >= MIN_EXACT_MATCH_WORD_LENGTH: return ('same word', 100)
    if l in EQUIVALENT_LV_RV_WORDS.get( r, set() ): return ('another word for the same thing', 60)
    if len(r) < 5 or len(l) < 3: return None
    shorter,longer = (r,l) if len(r) < len(l) else (l,r)
    if shorter == longer[:len(shorter)] and len(shorter) >= 5 \
        and len(longer)-len(shorter) <= 3: # e.g. RV 'wineskin' against LV 'wineskins'
        return ('inflectional ending', 90)
    n = 0
    while n < min( len(r), len(l) ) and r[n] == l[n]: n += 1
    if n >= ORDER_MATCH_PREFIX_LENGTH: return (f'same first {n} letters', 70)
    return None
# end of scoreRVLVWords


def bestMonotoneAlignmentScore( scoreMatrix:List[List[Optional[Tuple[str,int]]]], bannedPair=None ) -> Tuple[int,List[Tuple[int,int]]]:
    """
    Find the highest-scoring ORDER-PRESERVING alignment of two word lists.

    (An alignment may skip words, but the words it does pair up must stay in the same
        left-to-right order in both lists, because the OET-RV follows the OET-LV clause
        order through each verse.  See matchWordsInOrder().)

    'bannedPair' optionally excludes one (row, column) so we can ask
        'what would the best score be WITHOUT this pair?'

    Returns (score, [(row, column), ...]).
    """
    numRows, numCols = len(scoreMatrix), (len(scoreMatrix[0]) if scoreMatrix else 0)
    NEG = -1_000_000
    # best[i][j] is the best total for our first i rows against our first j columns
    best = [[NEG]*(numCols+1) for _ in range(numRows+1)]
    best[0][0] = 0
    for i in range(numRows+1):
        for j in range(numCols+1):
            if best[i][j] == NEG: continue
            total = best[i][j]
            if i < numRows and j < numCols: # Pair these two words
                cell = scoreMatrix[i][j]
                if cell is not None and (i,j) != bannedPair:
                    if total + cell[1] > best[i+1][j+1]:
                        best[i+1][j+1] = total + cell[1]
            if i < numRows and total > best[i+1][j]: # Skip this RV word
                best[i+1][j] = total
            if j < numCols and total > best[i][j+1]: # Skip this LV word
                best[i][j+1] = total
    # Walk back through the best path
    alignment, i, j = [], numRows, numCols
    while i > 0 or j > 0:
        if i > 0 and j > 0 and best[i][j] != best[i-1][j] and best[i][j] != best[i][j-1] \
            and scoreMatrix[i-1][j-1] is not None and (i-1,j-1) != bannedPair \
            and best[i][j] == best[i-1][j-1] + scoreMatrix[i-1][j-1][1]:
            alignment.append( (i-1, j-1) )
            i, j = i-1, j-1
        elif i > 0 and best[i][j] == best[i-1][j]:
            i -= 1
        else:
            j -= 1
    alignment.reverse()
    return best[numRows][numCols], alignment
# end of bestMonotoneAlignmentScore


def getUnnumberedRVWords( BBB:str, c:int, v:int ) -> set:
    """
    Return the set of plain words in the CURRENT OET-RV verse that don't have a word number yet,
        each in the simplified form that the matchers compare in, i.e. the form that
        simplifyRVLVWord() gives, so that a capitalised, hyphenated or possessive word is still
        recognised as the same word.

    The rvWordList that the matchers get is a snapshot taken at the start of the verse, so a
        matcher that runs after another one can't tell from it what has already been numbered.
    This reads the live OET-RV lines instead, so we can safely run after the other matchers.
    """
    havePsalmTitles = bos_books_codes_py.has_psalm_title( BBB, str(c) )
    desiredV = (v-1) if havePsalmTitles and v>1 else v
    freeWords = set()
    C = V = None
    foundChapter = foundVerse = False
    for line in state.rvESFMLines:
        try: marker, rest = line.split( ' ', 1 )
        except ValueError: marker, rest = line, ''
        if marker in ('\\s1','\\s2','\\s3','\\r','\\rem') or not rest: continue
        if marker == '\\c':
            C = int(rest)
            if C > c: break
            if C == c: foundChapter = True
        elif foundChapter and marker == '\\v':
            Vstr, rest = rest.split( ' ', 1 )
            V = int( Vstr.split('-',1)[0] )
            foundVerse = C==c and V==desiredV
        elif foundChapter and marker == '\\d':
            # Only a '\d' line before the '\v' of verse 1 belongs to verse 1 (see the long
            #   explanation in addNumberToRVWord()); the '\d' line at the end of HAB is not.
            foundVerse = C==c and desiredV==1 and V is None
        if not foundVerse: continue
        for token in rest.split():
            if '¦' in token or token.startswith( '\\' ): continue
            plainToken = simplifyRVLVWord( stripAddMarkers( token ) ) # stripAddMarkers() removes a leading '\add' code and a trailing '\add*'
            if plainToken: freeWords.add( plainToken ) # Skip a token that is only punctuation
    return freeWords
# end of getUnnumberedRVWords


def getLVWordNumber( lvWordStr:str ) -> Optional[int]:
    """
    Pull the OET-LV word number out of a word like 'wineskins¦23221'.

    We only take the leading run of digits, because the OET-LV sometimes has a gloss helper
        marker stuck to the number (e.g. 'will¦23935˒'), which would otherwise stop int().
    """
    m = re.match( r'^.*?¦(\d+)', lvWordStr )
    return int(m.group(1)) if m else None
# end of getLVWordNumber


# The words in between two words of a phrase, i.e. whitespace and any USFM markers, so that we
#   can match a phrase whose words the translator has wrapped in a '\add' span or separated with
#   e.g. '\wj' or a '\n' line marker, e.g. the 'young donkey' of '\+add ≈young donkey\+add*'.
rvPhraseSeparatorRegex = r'(?:[ ]|\\\+?[a-zA-Z0-9]+\*?)+'

def matchWordPhrases( BBB:str, c:int,v:int, rvWordList:List[str], lvWordList:List[str], reversedOrder:bool ) -> Tuple[int,int]:
    """
    Connect the OET-RV words that are MORE THAN ONE English word but stand for just ONE OET-LV
        word, using the pairs that the translator has listed in OET-RV_wordPhrases_table.tsv, e.g.
            the OET-RV 'you all' against the OET-LV 'you_all', the one plural 'you' word
            the OET-RV 'young donkey' against the OET-LV 'colt'
    Every word of the OET-RV phrase gets the one OET-LV word number, because that is the way the
        human translators number such a phrase (see addNumberToAddSpan() for the same convention
        on an '\add' span like Mark 5:12 '\add @the demons\add*' for the LV 'they').

    This has to run FIRST, because the little words that these phrases are made of ('you', 'all',
        'young', 'donkey') are exactly the words that we refuse to match on their own, and because
        the table records a decision that the translator has already made.
    """
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag:
        fnPrint( DEBUGGING_THIS_MODULE, f"matchWordPhrases( {BBB} {c}:{v} {reversedOrder=} {rvWordList}, {lvWordList} )" )
    if not state.rvWordPhrases: return 0,0
    assert rvWordList and lvWordList
    if reversedOrder: vPrint( 'Info', DEBUGGING_THIS_MODULE, f"  {BBB} {c}:{v} is an order-reversed verse" )

    # Where is each of our OET-LV phrases in this verse?  (The OET-LV has already had its
    #   '_' turned into a space, so the one OET-LV word 'you_all¦N_all¦N' is two lvWordList
    #   entries that share the one word number N.  We insist on that, so that we only take a
    #   phrase that really is ONE OET-LV word.)
    lvCandidates = {} # (simplified LV words) -> [ (first word index, lv word number) ]
    for lvWords in state.rvWordPhrases:
        candidates = []
        for ix in range( len( lvWordList ) - len( lvWords ) + 1 ):
            lvNumbers, isMatch = set(), True
            for offset,lvWord in enumerate( lvWords ):
                lvWordStr = lvWordList[ ix + offset ]
                lvNumber = getLVWordNumber( lvWordStr )
                if lvNumber is None or simplifyRVLVWord( lvWordStr.split( '¦' )[0] ) != lvWord:
                    isMatch = False; break
                lvNumbers.add( lvNumber )
            if isMatch and len( lvNumbers ) == 1: candidates.append( (ix, lvNumbers.pop()) )
        if candidates: lvCandidates[ lvWords ] = candidates
    if not lvCandidates: return 0,0

    # The OET-RV words in the simplified form that we compare in.  Note that a word which already
    #   has a word number is allowed here, because a phrase can be half connected already -- e.g.
    #   Mark 8:2 'How much bread have you all got?' has the number on the 'you' from another matcher
    #   but not yet on the 'all' -- and also because getUnnumberedRVWords()'s 'still free' words
    #   don't see through a closing marker like Mark 14:27 'you¦31031 all\wj*'.  addNumberToRVPhrase()
    #   does the real checking on the live OET-RV lines instead: it only goes ahead if the phrase
    #   occurs exactly once, and it only fills in the words that have no number yet, and only if the
    #   numbers that are already there are the ones that we want.
    rvPlainWords = [ simplifyRVLVWord( rvWordStr.split( '¦' )[0] ) for rvWordStr in rvWordList ]

    # Try the longest phrase first at each word, so that the most specific row wins
    phraseLengths = sorted( { len(rvWords) for rvWords in state.rvWordPhrases }, reverse=True )
    rvIxRange = range( len( rvWordList )-1, -1, -1 ) if reversedOrder else range( len( rvWordList ) )
    usedLvIndexes, numAdded = set(), 0
    for ix in rvIxRange:
        lvWords = None
        for length in phraseLengths:
            if ix + length > len( rvWordList ): continue
            if all( '¦' in rvWord for rvWord in rvWordList[ix:ix+length] ): continue # This phrase is already fully numbered
            rvWords = tuple( rvPlainWords[ix:ix+length] )
            lvWords = next( (key for key,value in state.rvWordPhrases.items() if value == rvWords ), None )
            if lvWords is not None: break # This is the most specific phrase that starts at this word
        if lvWords is None: continue

        lvCandidatesForThisPhrase = lvCandidates[lvWords]
        if reversedOrder: lvCandidatesForThisPhrase = lvCandidatesForThisPhrase[::-1] # The OET-RV meets them in the opposite order
        for candidateIx,lvNumber in lvCandidatesForThisPhrase: # The OET-LV phrases, in the order the OET-RV meets them
            if candidateIx in usedLvIndexes: continue # This OET-LV phrase is already spoken for
            rvPhraseWords = state.rvWordPhrasesSearch[rvWords]
            phraseAdds,phraseNS = addNumberToRVPhrase( BBB, c,v, rvPhraseWords, lvNumber )
            if not phraseAdds:
                if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
                    dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  matchWordPhrases() could not use '{rvWords}' for the LV '{lvWords}¦{lvNumber}' at {BBB} {c}:{v}" )
                break # Don't keep looking, or a second OET-RV phrase would get this same OET-LV number
            if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"matchWordPhrases() is adding {lvNumber} to the {phraseAdds} RV words of '{rvWords}' from LV '{lvWords}' at {BBB} {c}:{v}" )
            usedLvIndexes.add( candidateIx )
            numAdded += phraseAdds
            break
    return numAdded,0 # None of our phrases are nomina sacra
# end of connect_OET-RV_words_via_OET-LV.matchWordPhrases


def matchOrderedRuns( BBB:str, c:int,v:int, rvWordList:List[str], lvWordList:List[str] ) -> Tuple[int,int]:
    """
    Between two already numbered OET-RV words, the unnumbered OET-RV words and the
        corresponding OET-LV tokens with different word numbers in the same gap must form
        a one-to-one ordered mapping.  When the gap RV words and the gap LV word-groups
        line up exactly in count, we can connect the words position by position.

    The numbers are only added when (a) the RV words are all still unnumbered, (b) the gap
        on both sides has the same width, and (c) every positional pair is an exact
        match (or a pair learned from such a matching segment), otherwise we add nothing.
    """
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag:
        fnPrint( DEBUGGING_THIS_MODULE, f"matchOrderedRuns( {BBB} {c}:{v} )" )
    assert rvWordList and lvWordList
    NT = bos_books_codes_py.is_new_testament_nr( BBB )
    stillFree = getUnnumberedRVWords( BBB, c,v )

    # Parse LV tokens into a list of groups by consecutive equal LV number
    lvGroups = [] # list of dicts: { num, tokens:[...], alts:[...] }
    lastNum = None
    for lvTok in lvWordList:
        try: lvWord,lvNumber = lvTok.split( '¦', 1 )
        except ValueError:
            if lvTok != 'to':
                logging.critical( f"matchOrderedRuns failed on {lvTok=} from {BBB} {c}:{v}" )
            lvNumber = None # We treat anomalous as a splitter below
        else:
            try: lvNumber = int( lvNumber )
            except ValueError:
                lvNumber = getPositiveLeadingInt( lvNumber ) if lvNumber else None
        if lastNum != lvNumber:
            lvGroups.append( {'num': lvNumber, 'tokens': [], 'alts': set()} )
            lastNum = lvNumber
        lvGroups[-1]['tokens'].append( lvTok )
        lvWord = lvTok.split( '¦', 1 )[0].strip( '_' )
        for candidate in re.split( r'[/(]', lvWord ):
            candidate = candidate.strip( '_' )
            if candidate:
                lvGroups[-1]['alts'].add( candidate )

    numAdded = numNS = 0
    anchorIdx = []
    for ix,word in enumerate( rvWordList ):
        if '¦' in word:
            anchorIdx.append( ix )
    if len(anchorIdx)<2: return 0,0

    # collect training pairs across any safe one-to-one gap, then apply
    CANDIDATE_PAIRS = defaultdict( int )
    for pi,ni in zip( anchorIdx[:-1], anchorIdx[1:] ):
        rvGap = [w for w in rvWordList[pi+1:ni] if '¦' not in w]
        # find LV gap groups strictly between pi's number and ni's number
        try: numA = int( rvWordList[pi].split('¦',1)[1] )
        except (ValueError, IndexError): continue
        try: numB = int( rvWordList[ni].split('¦',1)[1] )
        except (ValueError, IndexError): continue
        gapGroups = [grp for grp in lvGroups if grp['num'] is not None and grp['num'] > numA and grp['num'] < numB]
        if len(rvGap) == len(gapGroups) and len(rvGap)>0:
            for rvTok, grp in zip(rvGap, gapGroups):
                for alt in grp['alts']:
                    if simplifyRVLVWord( rvTok ) == simplifyRVLVWord( alt ):
                        CANDIDATE_PAIRS[ (simplifyRVLVWord( rvTok ), simplifyRVLVWord( alt )) ] += 1

    for pi,ni in zip( anchorIdx[:-1], anchorIdx[1:] ):
        rvGap = [w for w in rvWordList[pi+1:ni] if '¦' not in w]
        try: numA = int( rvWordList[pi].split('¦',1)[1] )
        except (ValueError, IndexError): continue
        try: numB = int( rvWordList[ni].split('¦',1)[1] )
        except (ValueError, IndexError): continue
        gapGroups = [grp for grp in lvGroups if grp['num'] is not None and grp['num'] > numA and grp['num'] < numB]
        if len(rvGap) == 0 or len(gapGroups)==0 or len(rvGap) != len(gapGroups):
            continue
        if any( simplifyRVLVWord( w ) not in stillFree for w in rvGap ): continue
        allMatch = True
        for rvTok, grp in zip(rvGap, gapGroups):
            cand = [alt for alt in grp['alts'] if simplifyRVLVWord( rvTok ) == simplifyRVLVWord( alt )]
            if cand: continue
            cand2 = [alt for alt in grp['alts'] if (simplifyRVLVWord( rvTok ), simplifyRVLVWord( alt )) in CANDIDATE_PAIRS]
            if not cand2:
                allMatch = False; break
        if not allMatch: continue
        for rvTok, grp in zip(rvGap, gapGroups):
            num = int( grp['num'] )
            if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"matchOrderedRuns adding {num} to open RV gap word '{rvTok}' from gap LV {grp['tokens']} at {BBB} {c}:{v}" )
            result = addNumberToRVWord( BBB, c,v, rvTok, num )
            if result:
                numAdded += 1
                if NT and 'N' in state.wordTable['NT'][num][state.wordTableHeaderList['NT'].index('GlossCaps')]:
                    numNS += 1
    return numAdded,numNS
# end of matchOrderedRuns


ARTICLE_WORDS = ('the','a','an')
def matchArticlePrecedesLinkedNoun( BBB:str, c:int,v:int, rvWordList:List[str], lvWordList:List[str] ) -> Tuple[int,int]:
    """
    Link an unnumbered RV article ('the'/'a'/'an') when the very next RV word is already
        linked, and the OET-LV token immediately before that word carries the same article
        with a free number, e.g. RV 'the father¦34205' after earlier anchors, and LV
        'except¦34202 not/lest¦34203 the¦34204 father¦34205'.
    We require that the following noun occurs only this once in each verse, and that the
        article number hasn't already been used on another RV word.
    """
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag:
        fnPrint( DEBUGGING_THIS_MODULE, f"matchArticlePrecedesLinkedNoun( {BBB} {c}:{v} )" )
    NT = bos_books_codes_py.is_new_testament_nr( BBB )
    stillFree = getUnnumberedRVWords( BBB, c,v )
    lvWordsParsed = []
    for lvTok in lvWordList:
        try: lvWord,lvNumber = lvTok.split( '¦', 1 )
        except ValueError: continue
        try: lvNumber = int( lvNumber )
        except ValueError:
            lvNumber = getPositiveLeadingInt( lvNumber ) if lvNumber else None
        lvWordsParsed.append( (lvWord, lvNumber) )
    numAdded = numNS = 0
    rvSimpleCount = {}
    for w in rvWordList:
        sw = simplifyRVLVWord( w.split( '¦', 1 )[0] )
        if sw: rvSimpleCount[sw] = rvSimpleCount.get( sw, 0 ) + 1
    for ix in range( len( rvWordList ) - 1 ):
        rvArt = rvWordList[ix]
        if '¦' in rvArt: continue
        if simplifyRVLVWord( rvArt ) not in ARTICLE_WORDS: continue
        noun = rvWordList[ix + 1]
        if '¦' not in noun: continue
        try: nounNumber = int( noun.split( '¦', 1 )[1] )
        except (ValueError, IndexError): continue
        nounSimple = simplifyRVLVWord( noun.split( '¦', 1 )[0] )
        if not nounSimple or rvSimpleCount.get( nounSimple, 0 ) != 1: continue
        if simplifyRVLVWord( rvArt ) not in stillFree: continue
        lvNounIndexes = [ i for i,(lvW,lvN) in enumerate( lvWordsParsed ) if lvN == nounNumber ]
        if len( lvNounIndexes ) != 1: continue
        lvNounIdx = lvNounIndexes[0]
        if lvNounIdx == 0: continue
        lvPrevRaw, lvPrevNumber = lvWordsParsed[ lvNounIdx - 1 ]
        if lvPrevNumber is None or lvPrevNumber == nounNumber: continue
        lvPrevSimple = lvPrevRaw.strip( '_' )
        candidates = { simplifyRVLVWord( x ) for x in re.split( r'[/(]', lvPrevSimple ) if x }
        if simplifyRVLVWord( rvArt ) not in candidates: continue
        # Ensure LV prev article is free: no RV word already carries that number
        already = any( tok.split( '¦', 1 )[1] == str( lvPrevNumber ) for tok in rvWordList if '¦' in tok )
        if already: continue
        if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
            dPrint( 'Info', DEBUGGING_THIS_MODULE, f"matchArticlePrecedesLinkedNoun() adding {lvPrevNumber} to {rvArt} before {noun} at {BBB} {c}:{v}" )
        # Local insertion: find '{article} {noun}' on a single OT/NT line
        found = False
        for n,line in enumerate( state.rvESFMLines[:] ):
            pattern = re.escape( rvArt ) + r' |' + re.escape( noun )
            try: Mv = re.search( re.escape( rvArt ) + r'\s+' + re.escape( noun ), line)
            except IndexError: Mv = None
            if Mv is None: continue
            if isInsideStraightAddSpan( line, Mv.start() ): continue
            state.rvESFMLines[n] = re.sub( re.escape( rvArt ) + r'\s+' + re.escape( noun ), re.escape( rvArt ) + f'¦{lvPrevNumber} ' + re.escape( noun ), state.rvESFMLines[n], count=1 )
            found = True
            break
        if found:
            numAdded += 1
            # articles are never nomina sacra
    return numAdded,numNS
# end of matchArticlePrecedesLinkedNoun


def matchWordsInOrder( BBB:str, c:int,v:int, rvVerseText:str, rvWordList:List[str], lvWordList:List[str], reversedOrder:bool ) -> Tuple[int,int]:
    """
    The OET-RV follows the OET-LV clause order roughly from left to right through each verse,
        so we can use word ORDER to work out which OET-RV word goes with which OET-LV word.

    (The exception is a verse whose text starts with the U+21D4 double arrow, which means the
        OET-RV translated the LAST half of the OET-LV verse first, so for those we run the
        OET-LV words backwards.)

    This picks up the pairs that matchWordsFirstParts() has to give up on because the same
        OET-LV word occurs more than once in the verse and/or because more than one OET-RV word
        starts with the same few letters.  For example, Mark 2:22 has three OET-RV 'wineskins'
        and four OET-LV 'wineskins', so matchWordsFirstParts() cannot use any of them, but the
        order unambiguously pairs them up.

    To stay safe, we only use a pair if EVERY highest-scoring order-preserving alignment of
        the verse uses it, i.e. there is no equally good alignment that pairs something else.
    """
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag:
        fnPrint( DEBUGGING_THIS_MODULE, f"matchWordsInOrder( {BBB} {c}:{v} {reversedOrder=} {rvWordList}, {lvWordList} )" )
    assert rvWordList and lvWordList
    if reversedOrder: vPrint( 'Info', DEBUGGING_THIS_MODULE, f"  {BBB} {c}:{v} is an order-reversed verse" )

    # First try bounded order-run alignment between already-anchored words
    runNumAdded,runNumNS = matchOrderedRuns( BBB, c,v, rvWordList, lvWordList )
    # Then try the safe "article before already numbered noun" case
    artNumAdded,artNumNS = matchArticlePrecedesLinkedNoun( BBB, c,v, rvWordList, lvWordList )

    NT = bos_books_codes_py.is_new_testament_nr( BBB )
    # We skip an OET-LV word that the verse gives the same number to more than once, because such a
    #   word tells us nothing that its twin doesn't, e.g. LV 'been¦1544, have¦1544'.  We do NOT skip
    #   a number that two DIFFERENT OET-LV words share, because which of the two a pair belongs to
    #   is then decided by the word itself: the OET-RV 'put' of Mark 12:1 is the OET-LV 'put¦32436'
    #   and not the 'around¦32436' that shares its number.
    lvWordCount = {}
    for lvWordStr in lvWordList:
        lvNumber = getLVWordNumber( lvWordStr )
        if lvNumber is None: continue
        key = ( lvWordStr.split( '¦' )[0], lvNumber )
        lvWordCount[key] = lvWordCount.get( key, 0 ) + 1
    repeatedLVWords = { key for key,count in lvWordCount.items() if count > 1 }

    # Build our OET-RV rows.  We only handle plain words that are still unnumbered, and we
    #   skip nomina sacra, because matchIdenticalProperNouns() and addNumberToRVWord() do those.
    stillFree = getUnnumberedRVWords( BBB, c,v )
    rvRows = []
    for ix,rvWordStr in enumerate( rvWordList ):
        if '¦' in rvWordStr: continue # Already has a word number
        plainWord = simplifyRVLVWord( rvWordStr )
        if len(plainWord) < MIN_EXACT_MATCH_WORD_LENGTH: continue # Too short to match on safely
        if len(plainWord) < ORDER_MATCH_PREFIX_LENGTH and plainWord in LITTLE_FUNCTION_WORDS:
            continue # A little English function word, which the OET-RV has deliberately not numbered
        if plainWord not in stillFree: continue # One of the earlier matchers got there first
        # We score the plain (simplified) word, but we have to give addNumberToRVWord() the word
        #   as the OET-RV really spells it, because that is what it searches the OET-RV text for.
        rvRows.append( (ix, plainWord, unSimplifyRVWord( rvWordStr ) ) )
    if not rvRows: return 0,0

    # Build our OET-LV columns, running them backwards for an order-reversed verse.
    #   A '/' means the OET-LV offers alternative spellings/glosses (e.g. 'because/for',
    #   'apprentices/followers'), so we let any of them count as a match.
    lvIndexList = list( range( len(lvWordList) ) )
    if reversedOrder: lvIndexList = lvIndexList[::-1]
    lvCols = []
    for ix in lvIndexList:
        lvWordStr = lvWordList[ix]
        lvNumber = getLVWordNumber( lvWordStr )
        if lvNumber is None: continue
        lvWord = lvWordStr.split( '¦' )[0]
        if (lvWord,lvNumber) in repeatedLVWords: continue
        for alternative in lvWord.split( '/' ):
            if not alternative.islower() and simplifyRVLVWord( alternative ) not in EQUIVALENT_LV_RV_WORDS:
                # Allow short/common capitalised words (e.g. 'But', 'And', 'So') that are
                #   capitalised only because a verse begins with them, while still leaving
                #   proper nouns to the proper noun matchers.
                try:
                    lvWordRow = state.wordTable['NT' if NT else 'OT'][lvNumber]
                    lvRole = lvWordRow[state.wordTableHeaderList['NT' if NT else 'OT'].index('Role')].strip()
                except Exception:
                    lvRole = '?'
                if lvRole == 'N':
                    continue # Leave proper nouns alone
                if lvRole not in ('C','D','P','T','E','I','V','A'):
                    continue # Unknown part of speech; play it safe
            if NT and 'N' in state.wordTable['NT'][lvNumber][state.wordTableHeaderList['NT'].index('GlossCaps')]:
                continue # Leave nomina sacra alone
            lvCols.append( (ix, alternative, lvNumber) )
    if not lvCols: return runNumAdded + artNumAdded, runNumNS + artNumNS

    # Score every RV word against every LV word
    scoreMatrix = [ [ None ]*len(lvCols) for _ in rvRows ]
    for rowIx,(rvIx,rvWord,rvSearchWord) in enumerate( rvRows ):
        for colIx,(lvIx,lvWord,lvNumber) in enumerate( lvCols ):
            cell = scoreRVLVWords( rvWord, lvWord )
            if cell: scoreMatrix[rowIx][colIx] = cell

    bestScore, alignment = bestMonotoneAlignmentScore( scoreMatrix )
    if not alignment: return 0,0

    numAdded = numNS = 0
    for rowIx,colIx in alignment:
        rvIx,rvWord,rvSearchWord = rvRows[rowIx]
        lvIx,lvWord,lvNumber = lvCols[colIx]
        # Only trust this pair if the best alignment would be WORSE without it
        scoreWithoutPair, _ = bestMonotoneAlignmentScore( scoreMatrix, bannedPair=(rowIx,colIx) )
        if scoreWithoutPair >= bestScore:
            if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  matchWordsInOrder() skipping ambiguous pair {BBB} {c}:{v} RV '{rvWord}' LV '{lvWord}¦{lvNumber}'" )
            continue
        why = scoreMatrix[rowIx][colIx][0]
        if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
            dPrint( 'Info', DEBUGGING_THIS_MODULE, f"matchWordsInOrder() is adding {lvNumber} to RV '{rvWord}' from LV '{lvWord}' ({why}) at {BBB} {c}:{v}" )
        result = addNumberToRVWord( BBB, c,v, rvSearchWord, lvNumber )
        if result:
            numAdded += 1
        else:
            logging.warning( f"Got addNumberToRVWord( {BBB} {c}:{v} '{rvWord}' {lvNumber} ) result = {result}" )

    numAdded = numAdded + runNumAdded
    numNS = numNS + runNumNS + artNumNS
    numAdded = numAdded + artNumAdded
    return numAdded,numNS
# end of connect_OET-RV_words_via_OET-LV.matchWordsInOrder


# The '\add' code that means the translator changed the number, e.g. '\add #straps\add*'.
NUMBER_CHANGE_ADD_CODE = '#'

# The '\add' code that means the translator repeated something they had already said,
#   e.g. '\add ≡the father of\add*'.
REPEAT_ADD_CODE = '≡'

# The English number changes that we can safely undo, i.e. the ones where a '#' word like
#   'men' can only be a pluralised OET-LV 'man', and not the start of some other word.
IRREGULAR_NUMBER_CHANGES = ( ('man','men'), ('woman','women'), ('person','people'),
    ('child','children'), ('foot','feet'), ('tooth','teeth'), ('goose','geese'),
    ('mouse','mice'), ('louse','lice'), ('ox','oxen'), ('brother','brethren') )
_NUMBER_CHANGE_WORDS = [ _word for _pair in IRREGULAR_NUMBER_CHANGES for _word in _pair ]
assert len( _NUMBER_CHANGE_WORDS ) == len( set( _NUMBER_CHANGE_WORDS ) ), f"Repeated word in {IRREGULAR_NUMBER_CHANGES=}" # Each word may only be in one pair, or numberVariants() would be ambiguous

# The shortest word that we will treat as an English word when we add or remove a plural 's'.
#   Three letters is safe, because the singular and plural of a three letter word can only be
#   each other (e.g. 'day'/'days', 'god'/'gods'), apart from the irregular pairs above.
MIN_NUMBER_CHANGE_WORD_LENGTH = 3

def numberVariants( word:str ) -> set:
    """
    Return the set of plain English words that 'word' would be if its number had been changed,
        e.g. numberVariants('straps') includes 'strap', and numberVariants('strap') includes 'straps'.
    We deliberately only make the changes that we are sure about, because a wrong word number
        is much worse than a missing one.  In particular, we do NOT turn 'ves' into 'fe' or 'le',
        or 'ies' into 'ie', because 'leaves' could be 'leaf' or 'loaf', and 'flies' could be
        'fly' or 'flee', so we would not know which OET-LV word the translator had in mind.
    (We do end up with some forms that aren't English words at all, e.g. 'strapses', but that
        does no harm: matchWordsWithChangedNumbers() only uses a form that is a noun of that
        exact spelling in the OET-LV verse we are working on.)
    """
    word = word.lower()
    variants = set()
    for singular,plural in IRREGULAR_NUMBER_CHANGES:
        if word == singular: variants.add( plural )
        elif word == plural: variants.add( singular )
    if len( word ) >= MIN_NUMBER_CHANGE_WORD_LENGTH:
        if word.endswith( 'ies' ): # e.g. 'families' and 'family'
            variants.add( word[:-3] + 'y' )
        if word.endswith( 'y' ) and word[-2] not in 'aeiou': # e.g. 'family' and 'families'
            variants.add( word[:-1] + 'ies' )
        if word.endswith( 'es' ) and (word[-3] in 'sxzch' or word.endswith( ('ches','shes') )):
            variants.add( word[:-2] ) # e.g. 'classes'/'class', 'watches'/'watch', 'boxes'/'box'
        if word.endswith( ('s','x','z','ch','sh') ) and not word.endswith( 'ss' ):
            variants.add( word + 'es' ) # e.g. 'class'/'classes', 'watch'/'watches'
        if word.endswith( 's' ) and not word.endswith( 'ss' ):
            variants.add( word[:-1] ) # e.g. 'straps'/'strap', 'wars'/'war'
        if not word.endswith( 's' ):
            variants.add( word + 's' ) # e.g. 'strap'/'straps', 'child'/'childs'
    return variants
# end of numberVariants


def lvWordIsNoun( lvWordRow:List[str], testament:str ) -> bool:
    """
    Return True if an OET-LV word is a noun (or a substantive adjective), because a noun is the
        only kind of word whose number the translator can have changed, e.g. RV '#straps' for the
        OET-LV 'strap', so matchWordsWithChangedNumbers() should only connect those.
    The NT word table has a 'Role' column that says 'N' for a noun, but the OT word table
        describes its nouns in the 'Morphology' column instead, e.g. 'Ncfsa' for a common
        feminine singular noun (and 'Td' for the definite article, 'C,' for a conjunction, etc.).
    """
    if testament == 'NT':
        return lvWordRow[state.wordTableHeaderList['NT'].index('Role')].strip() in ('N','S')
    morphology = lvWordRow[state.wordTableHeaderList['OT'].index('Morphology')]
    return any( part.startswith( 'N' ) for part in morphology.split( ',' ) ) # e.g. 'R,Ncfsa' is a preposition with a noun
# end of lvWordIsNoun


def matchWordsWithChangedNumbers( BBB:str, c:int,v:int, rvWordList:List[str], addSpans:List[Tuple[str,int,int]], lvWordList:List[str] ) -> Tuple[int,int]:
    """
    Connect OET-RV words that the translator marked as a changed number with a
        '\add #...' span (e.g. '\add #straps\add*'), which mostly means that we turned a
        singular OET-LV saying into a plural one.
    It works in both directions, e.g. Mark 4:29 '\add #worms\add*' against the LV 'worm', and
        1 Samuel 17:32 '\add #the king\add*' against the LV 'Saul'.

    The word inside such a span is the SAME word as the OET-LV word that it translates, only
    with the opposite number, so we can only connect it when the OET-LV word is exactly
    one of the numberVariants() of the OET-RV word, e.g. RV '#straps' against LV 'strap'.
    To stay safe, the OET-LV word has to be a noun (a noun is the only kind of word whose
    number we can change), we insist on there being exactly one such OET-LV word in the
    verse, and we also give up if any other OET-RV word in the verse is that same OET-LV
    word, because then we can't tell which OET-RV word is the one that goes with it.
    """
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag:
        fnPrint( DEBUGGING_THIS_MODULE, f"matchWordsWithChangedNumbers( {BBB} {c}:{v} {rvWordList} )" )
    assert rvWordList and lvWordList
    if not any( addCode == NUMBER_CHANGE_ADD_CODE for addCode,firstIx,lastIx in addSpans ): return 0,0

    NT = bos_books_codes_py.is_new_testament_nr( BBB )
    usedLVNumbers = set() # Skip any OET-LV word number that is used more than once in the verse
    seenLVNumbers = set()
    for lvWordStr in lvWordList:
        lvNumber = getLVWordNumber( lvWordStr )
        if lvNumber is None: continue
        if lvNumber in seenLVNumbers: usedLVNumbers.add( lvNumber ) # e.g. LV 'been¦1544, have¦1544'
        seenLVNumbers.add( lvNumber )

    stillFree = getUnnumberedRVWords( BBB, c,v )
    numAdded = numNS = 0
    for addCode,firstIx,lastIx in addSpans:
        if addCode != NUMBER_CHANGE_ADD_CODE: continue
        for rvIx in range( firstIx, lastIx+1 ):
            rvWord = rvWordList[rvIx]
            if '¦' in rvWord: continue # Already has a word number
            plainRVWord = simplifyRVLVWord( rvWord )
            if plainRVWord not in stillFree: continue # One of the earlier matchers got there first
            if len( plainRVWord ) < MIN_NUMBER_CHANGE_WORD_LENGTH: continue
            variants = numberVariants( plainRVWord )
            if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  {BBB} {c}:{v} RV '{rvWord}' {variants=}" )

            candidateList = []
            for lvWordStr in lvWordList:
                lvNumber = getLVWordNumber( lvWordStr )
                if lvNumber is None or lvNumber in usedLVNumbers: continue
                lvWord = lvWordStr.split( '¦' )[0]
                if not lvWord.islower(): continue # Leave proper nouns to matchIdenticalProperNouns()
                plainLVWord = simplifyRVLVWord( lvWord )
                if plainLVWord not in variants: continue
                if plainLVWord == plainRVWord: continue # Same word, so the number didn't change after all
                try:
                    _lvWord,lvNumber,lvWordRow = getLVWordRow( lvWordStr, 'NT' if NT else 'OT' )
                except WordNumberError as e:
                    logging.critical( f"matchWordsWithChangedNumbers() {e} from {BBB} {c}:{v} {lvWordStr=}" )
                    continue
                if not lvWordIsNoun( lvWordRow, 'NT' if NT else 'OT' ):
                    continue # Only a noun can have its number changed (so this is not e.g. LV verb 'means')
                candidateList.append( (lvNumber,lvWord,lvWordRow) )
            if len( candidateList ) != 1:
                if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
                    dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  matchWordsWithChangedNumbers() skipping ambiguous pair {BBB} {c}:{v} RV '{rvWord}' with {len(candidateList)} OET-LV candidates" )
                continue
            lvNumber,lvWord,lvWordRow = candidateList[0]
            if any( '¦' not in otherRVWord and otherRVWord != rvWord and simplifyRVLVWord( otherRVWord ) == simplifyRVLVWord( lvWord ) for otherRVWord in rvWordList ):
                if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
                    dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  matchWordsWithChangedNumbers() skipping {BBB} {c}:{v} RV '{rvWord}' because another RV word is '{lvWord}'" )
                continue
            if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"matchWordsWithChangedNumbers() is adding {lvNumber} to RV '{rvWord}' from LV '{lvWord}' at {BBB} {c}:{v}" )
            result = addNumberToRVWord( BBB, c,v, rvWord, lvNumber )
            if result:
                numAdded += 1
                if NT and 'N' in lvWordRow[state.wordTableHeaderList['NT'].index('GlossCaps')]: numNS += 1
            else:
                logging.warning( f"Got addNumberToRVWord( {BBB} {c}:{v} '{rvWord}' {lvNumber} ) result = {result}" )

    return numAdded,numNS
# end of connect_OET-RV_words_via_OET-LV.matchWordsWithChangedNumbers


# The '\add' codes that stand in the place of a single OET-LV word, but where the English
#   word that the translator wrote is NOT a translation of that OET-LV word, so the only way
#   to find the OET-LV word is to look at the OET-LV words on either side of the span:
#     '@' – a pronoun that we changed to a name, e.g. RV '@Yeshua' for the LV 'he',
#     '%' – the person that we changed, e.g. RV '%they' for the LV '=them',
#     '*' – a name that we changed to a pronoun or a description, e.g. RV '*the priest' for the LV 'Amaziah',
#     '&' – an owner that we added, e.g. RV '&His' for the LV 'the' (the OET formats say
#           '&' replaces 'the' with a possessive like 'his').
# Every one of those words has to go with a particular KIND of OET-LV word, which is what
#   the ANCHOR_ADD_CODE_TESTS below check before we accept a connection.
# The '<', '>' and '+' and '=' codes are deliberately NOT here: '<add' and '>add' are English
#   that the translator added (a direct object, an implied person or object) and we have no
#   reliable way to tell which OET-LV word, if any, they stand in for.
ANCHOR_ADD_CODE_TESTS = { '@','%','*','&' }

# The OET-LV words that the '@' and '%' codes can stand in for, i.e. the person pronouns.
#   We include the possessives ('his', 'their', ...) because a name can stand in for a
#   possessive too (e.g. 2 Samuel 21:20 '\add @Maccabeus\add*' for the LV 'his feet').
#   We deliberately leave out the ambiguous combinations ('he/it', 'he/she', 'they/them', ...)
#   which the OET-LV uses when it is not sure which word it means.
PERSON_PRONOUN_WORDS = { 'he','him','his','she','her','hers','they','them','their','theirs',
                         'himself','herself','themselves','we','us','our','i','me','my' }
# The OET-LV words that the '&' code can stand in for, i.e. an article or a possessive.
OWNER_LV_WORDS = { 'the','a','an','his','her','its','their','my','our','your','yours','theirs','who','whom','whose' }
MIN_ANCHORED_ADD_WORD_LENGTH = 2


def lvWordIsProperNoun( lvWordRow:List[str], testament:str ) -> bool:
    """
    Return True if an OET-LV word is a proper noun, using the same test that
        matchIdenticalProperNouns() uses, so that we can tell a name from a word that just
        happens to be capitalised because it starts a sentence (e.g. LV 'Be¦1102' and 'I¦1166').
    """
    if testament == 'NT':
        return lvWordRow[state.wordTableHeaderList['NT'].index('Role')].strip() == 'N'
    glossCapitalisation = lvWordRow[state.wordTableHeaderList['OT'].index('GlossCapitalisation')]
    return 'S' not in glossCapitalisation # 'S' means it is only capitalised because it starts a sentence
# end of connect_OET-RV_words_via_OET-LV.lvWordIsProperNoun


def getRVWordNumber( rvWord:str ) -> Optional[int]:
    """
    Pull the OET-RV word number out of a word like 'wineskins¦23221'.
    """
    m = re.match( r'^.*?¦(\d+)', rvWord )
    return int(m.group(1)) if m else None
# end of connect_OET-RV_words_via_OET-LV.getRVWordNumber


def addNumberToAddSpan( BBB:str, c:int,v:int, rvWordList:List[str], firstIx:int, lastIx:int, lvNumber:int, lvWord:str, lvWordRow:List[str] ) -> Tuple[int,int]:
    """
    Give 'lvNumber' to every word of the exposed '\add' span that covers rvWordList[firstIx:lastIx+1].
    A single OET-LV word can be rendered by several English words (e.g. Mark 5:12
        '\add @the demons\add*' for the LV 'they'), and the human translators number all of
        them with the one OET-LV number, so we do the same.
    """
    NT = bos_books_codes_py.is_new_testament_nr( BBB )
    numAdded = numNS = 0
    for rvIx in range( firstIx, lastIx+1 ):
        result = addNumberToRVWord( BBB, c,v, rvWordList[rvIx], lvNumber )
        if result:
            numAdded += 1
            if NT and 'N' in lvWordRow[state.wordTableHeaderList['NT'].index('GlossCaps')]: numNS += 1
        else:
            logging.warning( f"Got addNumberToRVWord( {BBB} {c}:{v} '{rvWordList[rvIx]}' {lvNumber} ) result = {result}" )
    return numAdded,numNS
# end of connect_OET-RV_words_via_OET-LV.addNumberToAddSpan


def matchWordsBesideLvAnchor( BBB:str, c:int,v:int, rvWordList:List[str], addSpans:List[Tuple[str,int,int]], lvWordList:List[str] ) -> Tuple[int,int]:
    """
    Connect the OET-RV words of a '@', '%', '*' or '&' '\add' span to the OET-LV word that they
        stand in front of, which is the OET-LV word NEXT to the OET-LV word that the OET-RV word
        before (or after) the span is connected to.
    For example, in Mark 1:16 the OET-RV 'Simon¦27817 ... \add @the netted men\add* came in' is
        numbered against the OET-LV 'Simon¦27817 ˊēth¦27818 the¦27819 ˢaccâbîm¦27820', so the
        numbered OET-RV word before the '@' span gives us the OET-LV word number 27819, and the
        OET-LV word after that one ('ˢaccâbîm¦27820') is what the span is standing in front of.
    We only use an OET-RV word as the anchor if it is a plain word or a one-word span, because a
        longer '≈' or '#' span can stand for more than one OET-LV word, in which case the OET-LV
        word next to it would not be the one that the span is next to.
    We also insist that the OET-LV word we land on is the kind of word that the code needs (see
        ANCHOR_ADD_CODE_TESTS and lvWordIsProperNoun()) and that the before and after anchors
        don't disagree, so a missing or misleading anchor can't produce a wrong word number.
    """
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag:
        fnPrint( DEBUGGING_THIS_MODULE, f"matchWordsBesideLvAnchor( {BBB} {c}:{v} {rvWordList} )" )
    assert rvWordList and lvWordList
    if not any( addCode in ANCHOR_ADD_CODE_TESTS for addCode,firstIx,lastIx in addSpans ): return 0,0

    NT = bos_books_codes_py.is_new_testament_nr( BBB )
    usedLVNumbers = set() # Skip any OET-LV word number that is used more than once in the verse
    seenLVNumbers = set()
    for lvWordStr in lvWordList:
        lvNumber = getLVWordNumber( lvWordStr )
        if lvNumber is None: continue
        if lvNumber in seenLVNumbers: usedLVNumbers.add( lvNumber ) # e.g. LV 'been¦1544, have¦1544'
        seenLVNumbers.add( lvNumber )

    # The span that each word is inside of, so we can tell a plain word from a reworded one
    spanAtIx = {}
    for addCode,firstIx,lastIx in addSpans:
        for rvIx in range( firstIx, lastIx+1 ): spanAtIx[rvIx] = (addCode,firstIx,lastIx)

    stillFree = getUnnumberedRVWords( BBB, c,v )
    numAdded = numNS = 0
    for addCode,firstIx,lastIx in addSpans:
        if addCode not in ANCHOR_ADD_CODE_TESTS: continue
        if any( '¦' in rvWordList[rvIx] for rvIx in range( firstIx, lastIx+1 ) ): continue # Already numbered
        if any( simplifyRVLVWord( rvWordList[rvIx] ) not in stillFree for rvIx in range( firstIx, lastIx+1 ) ):
            continue # One of the earlier matchers got there first
        candidateList = []
        for rvDirection in ( -1, 1 ): # Look at the numbered OET-RV word before the span, then the one after
            rvIx = firstIx - 1 if rvDirection == -1 else lastIx + 1
            while 0 <= rvIx < len( rvWordList ):
                span = spanAtIx.get( rvIx )
                if span is None: break # A plain OET-RV word
                if span[1] == span[2]: break # A one-word span, which stands for one OET-LV word
                rvIx += rvDirection # Skip over a longer span, which can stand for several OET-LV words
            if not ( 0 <= rvIx < len( rvWordList ) ): continue
            anchorNumber = getRVWordNumber( rvWordList[rvIx] )
            if anchorNumber is None: continue
            anchorLVIndexes = [ lvIx for lvIx,lvWordStr in enumerate( lvWordList ) if getLVWordNumber( lvWordStr ) == anchorNumber ]
            if len( anchorLVIndexes ) != 1: continue # The OET-LV word number covers more than one OET-LV word
            # The anchor is on the left of the span, so the OET-LV word we want is on its right, and vice versa
            candidateIx = anchorLVIndexes[0] - rvDirection
            if not ( 0 <= candidateIx < len( lvWordList ) ): continue
            lvWordStr = lvWordList[candidateIx]
            lvNumber = getLVWordNumber( lvWordStr )
            if lvNumber is None or lvNumber == anchorNumber or lvNumber in usedLVNumbers: continue
            try:
                lvWord,lvNumber,lvWordRow = getLVWordRow( lvWordStr, 'NT' if NT else 'OT' )
            except WordNumberError as e:
                logging.critical( f"matchWordsBesideLvAnchor() {e} from {BBB} {c}:{v} {lvWordStr=}" )
                continue
            if addCode in ( '@', '%' ):
                if simplifyRVLVWord( lvWord ) not in PERSON_PRONOUN_WORDS: continue
            elif addCode == '&':
                if simplifyRVLVWord( lvWord ) not in OWNER_LV_WORDS: continue
            elif addCode == '*':
                if not lvWordIsProperNoun( lvWordRow, 'NT' if NT else 'OT' ): continue
            if len( simplifyRVLVWord( lvWord ) ) < MIN_ANCHORED_ADD_WORD_LENGTH: continue
            candidateList.append( (lvNumber,lvWord,lvWordRow) )
        candidateNumbers = { candidate[0] for candidate in candidateList }
        if len( candidateNumbers ) != 1:
            if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  matchWordsBesideLvAnchor() skipping {BBB} {c}:{v} '\\add {addCode}{' '.join(rvWordList[firstIx:lastIx+1])}\\add*' with {len(candidateNumbers)} OET-LV candidates" )
            continue
        lvNumber,lvWord,lvWordRow = candidateList[0]
        if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
            dPrint( 'Info', DEBUGGING_THIS_MODULE, f"matchWordsBesideLvAnchor() is adding {lvNumber} to RV '{' '.join(rvWordList[firstIx:lastIx+1])}' from LV '{lvWord}' at {BBB} {c}:{v}" )
        spanNumAdded,spanNumNS = addNumberToAddSpan( BBB, c,v, rvWordList, firstIx, lastIx, lvNumber, lvWord, lvWordRow )
        numAdded += spanNumAdded
        numNS += spanNumNS

    return numAdded,numNS
# end of connect_OET-RV_words_via_OET-LV.matchWordsBesideLvAnchor


def matchRepeatedWords( BBB:str, c:int,v:int, rvWordList:List[str], addSpans:List[Tuple[str,int,int]], lvWordList:List[str] ) -> Tuple[int,int]:
    """
    Connect the OET-RV words of a '\add ≡...' span, which means we repeated something that we
        had already said, to the OET-LV word that the repeat goes with.
    Because it is a repeat, the same words occur twice in the OET-RV verse but only ONCE in the
        OET-LV verse, so we can connect the repeated words to that single OET-LV word (e.g.
        1 Chronicles 4:19, where 'the father of' occurs twice in the OET-RV verse and only once
        in the OET-LV verse).
    We insist that the words really do occur EARLIER in the same OET-RV verse, because '≡' is
        also used to repeat something that we said in a PREVIOUS verse, and that has nothing to
        do with the OET-LV word of this verse (e.g. 1 Chronicles 16:16 and 23:29).
    """
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag:
        fnPrint( DEBUGGING_THIS_MODULE, f"matchRepeatedWords( {BBB} {c}:{v} {rvWordList} )" )
    assert rvWordList and lvWordList
    if not any( addCode == REPEAT_ADD_CODE for addCode,firstIx,lastIx in addSpans ): return 0,0

    NT = bos_books_codes_py.is_new_testament_nr( BBB )
    stillFree = getUnnumberedRVWords( BBB, c,v )
    numAdded = numNS = 0
    for addCode,firstIx,lastIx in addSpans:
        if addCode != REPEAT_ADD_CODE: continue
        if any( '¦' in rvWordList[rvIx] for rvIx in range( firstIx, lastIx+1 ) ): continue # Already numbered
        if any( simplifyRVLVWord( rvWordList[rvIx] ) not in stillFree for rvIx in range( firstIx, lastIx+1 ) ):
            continue # One of the earlier matchers got there first
        phrase = [ simplifyRVLVWord( rvWordList[rvIx] ) for rvIx in range( firstIx, lastIx+1 ) ]
        if not any( phrase == [ simplifyRVLVWord( rvWordList[rvIx2] ) for rvIx2 in range( rvIx, rvIx+len(phrase) ) ]
                    for rvIx in range( firstIx ) ):
            if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  matchRepeatedWords() skipping {BBB} {c}:{v} '\\add ≡{' '.join(phrase)}\\add*' because it does not occur earlier in the same verse" )
            continue # It is a repeat of something in a previous verse, so this OET-LV word is not it
        candidateNumbers = set()
        candidateWord, candidateRow = None, None
        for lvIx in range( len( lvWordList ) - len(phrase) + 1 ):
            if [ simplifyRVLVWord( lvWordList[lvIx2].split( '¦' )[0] ) for lvIx2 in range( lvIx, lvIx+len(phrase) ) ] != phrase: continue
            lvNumber = getLVWordNumber( lvWordList[lvIx] )
            if lvNumber is None: continue
            try:
                lvWord,lvNumber,lvWordRow = getLVWordRow( lvWordList[lvIx], 'NT' if NT else 'OT' )
            except WordNumberError as e:
                logging.critical( f"matchRepeatedWords() {e} from {BBB} {c}:{v} {lvWordList[lvIx]=}" )
                continue
            candidateNumbers.add( lvNumber )
            candidateWord, candidateRow = lvWord, lvWordRow
        if len( candidateNumbers ) != 1:
            if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  matchRepeatedWords() skipping {BBB} {c}:{v} '\\add ≡{' '.join(phrase)}\\add*' with {len(candidateNumbers)} OET-LV candidates" )
            continue
        lvNumber = candidateNumbers.pop()
        if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
            dPrint( 'Info', DEBUGGING_THIS_MODULE, f"matchRepeatedWords() is adding {lvNumber} to RV '{' '.join(rvWordList[firstIx:lastIx+1])}' from LV '{candidateWord}' at {BBB} {c}:{v}" )
        spanNumAdded,spanNumNS = addNumberToAddSpan( BBB, c,v, rvWordList, firstIx, lastIx, lvNumber, candidateWord, candidateRow )
        numAdded += spanNumAdded
        numNS += spanNumNS

    return numAdded,numNS
# end of connect_OET-RV_words_via_OET-LV.matchRepeatedWords


# The OET-LV gives a name in the original language AND, where we have one, its English
#   equivalent, e.g. 'Yəhūdāh/Judah' or 'Samouaʸl/(Shəmūˊel)', while the OET-RV usually uses its
#   own spelling of the name, and then puts the traditional/KJB spelling of it in a '!' '\add'
#   span right after, e.g. 'Yehudah \add !(Judah)\add*' or 'Yohan Markos \add !(John Mark)\add*'.
#   matchIdenticalProperNouns() and matchAdjustedProperNouns() can connect some of those, but not
#   the words that are inside the '!' span, and not a name that is spread over several OET-LV
#   words, so matchNamesViaTraditionalNames() below connects them.
lvAltNameRegex = re.compile( r'[/(]' )

# The '\add' code that says the span is the traditional/KJB spelling of the name that the OET-RV
#   has just spelled its own way, e.g. 'Yehudah \add !(Judah)\add*'.  A '/' in front of the name
#   ('\add !/ John Mark\add*') says that we have also changed the numbers of the words in the span.
TRADITIONAL_NAME_ADD_CODE = '!'

# The longest run of capitalised words in front of a '!' span that we treat as the OET-RV spelling
#   of the name that the span is the traditional spelling of, i.e. the 'Yohan Markos' of
#   'Yohan Markos \add !(John Mark)\add*'.  We stop at the first word that isn't capitalised.
MAX_NAME_WORDS_BEFORE_SPAN = 4

# What getTraditionalNameNumbers() found for an OET-RV word when it looked for the OET-LV name
#   that the word is another spelling of.  We don't use None/-1 for the two ambiguous answers,
#   because they mean opposite things: NO_LV_NAME means the rest of the name can tell us what
#   number this word is (e.g. the 'John' of 'Yohan¦91464 \add !(John)\add*', where the OET-LV
#   only has 'Yōannaʸs¦91464' and no 'John' word of its own), but AMBIGUOUS_LV_NAME means the
#   word is a spelling of more than one OET-LV name in the verse, so nothing can tell us.
NO_LV_NAME = None
AMBIGUOUS_LV_NAME = -1


def getLVNameSpellings( lvWord:str, nameTableKeys:tuple ) -> set:
    """
    Return all the different spellings that refer to one OET-LV name, so that we can tell which
        OET-LV word an OET-RV name is another name of.
    We use the parts of the OET-LV name itself (e.g. 'Yəhūdāh' and 'Judah' from
        'Yəhūdāh/Judah'), and the OET-RV spellings that the name tables have recorded for each of
        those parts (e.g. 'Yehudah' and 'Yihudah' — see loadHebGrkNameTables()).
    """
    spellings = { simplifyRVLVWord( lvWord ) }
    for key in lvAltNameRegex.split( lvWord ): # 'Yəhūdāh/Judah' becomes ['Yəhūdāh', 'Judah']
        key = key.strip()
        if not key: continue
        spellings.add( simplifyRVLVWord( key ) )
        for nameTableKey in nameTableKeys: # The name tables are keyed on the OET-LV spelling
            for something in state.nameTables[nameTableKey].get( key, set() ):
                spellings.add( simplifyRVLVWord( something ) )
        normalised = normalizeNameKey( key )
        if normalised: # The normalised index lets an RV word match an LV name whose transliteration differs slightly
            spellings.update( simplifyRVLVWord( something )
                              for something in state.namePartsIndex.get( normalised, () ) )
    # A name also has its traditional spelling (what the '!' '\add' span holds), which the decided
    #   OET-RV names table records against the OET-RV spellings, so add those in too.
    for spelling in tuple( spellings ):
        spellings.update( simplifyRVLVWord( traditionalName )
                          for traditionalName in state.rvNameTableInverse.get( spelling, () ) )
    return spellings
# end of connect_OET-RV_words_via_OET-LV.getLVNameSpellings


def getLvNameCandidates( lvWordList:List[str], nameTableKeys:tuple, testament:str ) -> List[Tuple[int,str,set]]:
    """
    Return the OET-LV names of a verse, each as (word number, name, all its spellings), for
        matchNamesViaTraditionalNames() to match OET-RV names against.
    We only use proper nouns (see lvWordIsProperNoun()).  We don't skip the words that share
        their number with another OET-LV word in the verse, because we match names by their
        spellings, and a number that covers two OET-LV words (e.g. Mark 1:5
        '\add >ones¦21722\add*_from¦21722_Hierousalaʸm¦21722') is still the one number of
        'Jerusalem'.
    """
    lvNameList = []
    for lvWordStr in lvWordList:
        lvNumber = getLVWordNumber( lvWordStr )
        if lvNumber is None: continue
        try:
            lvWord,lvNumber,lvWordRow = getLVWordRow( lvWordStr, testament )
        except WordNumberError as e:
            logging.critical( f"getLvNameCandidates() {e} from {lvWordStr=}" )
            continue
        if not lvWordIsProperNoun( lvWordRow, testament ): continue
        lvNameList.append( (lvNumber,lvWord,getLVNameSpellings( lvWord, nameTableKeys )) )
    return lvNameList
# end of connect_OET-RV_words_via_OET-LV.getLvNameCandidates


def getNameWordsBeforeSpan( liveWords:List[str], spanFirstIx:int, excludedWordIndexes:set=set() ) -> List[str]:
    """
    Return the run of capitalised words that comes immediately before a '!' '\add' span, i.e. the
        OET-RV spelling of the name that the span is the traditional spelling of,
        e.g. ['Yohan','Markos'] for 'Yohan Markos \add !(John Mark)\add*'.
    We stop at the first word that isn't capitalised (e.g. 'lived'), and we only look back a few
        words (see MAX_NAME_WORDS_BEFORE_SPAN), so that we don't sweep up an earlier name.
    'excludedWordIndexes' are the words of the other '\add' codes, which are added English rather
        than part of the OET-RV's own name.  Such a word ends the name (e.g. the 'rebuilt' of
        'from Beyt-El \add ≈rebuilt\add* Yeriho \add !(Jericho)\add*'), because the OET-RV name that
        the '!' span belongs to must be immediately next to it — otherwise we would sweep up an
        earlier, unrelated name (e.g. 'Beyt-El' here) and might give it a wrong word number.
    """
    nameWords = []
    for wordIx in reversed( range( spanFirstIx ) ):
        word = liveWords[wordIx]
        if wordIx in excludedWordIndexes: break # A word of another '\add' span, so the name isn't next to ours
        if not word or not word[0].isupper(): break # Not part of a name
        if '\\' in word: continue # One of the '\add' markers, which is not a word
        nameWords.insert( 0, word )
        if len( nameWords ) >= MAX_NAME_WORDS_BEFORE_SPAN: break
    return nameWords
# end of connect_OET-RV_words_via_OET-LV.getNameWordsBeforeSpan


def getTraditionalNameNumbers( nameWords:List[str], lvNameList:List[Tuple[int,str,set]] ) -> dict:
    """
    Return the OET-LV word number for each of the still-unnumbered OET-RV words of one name, as a
        { word: word number } dict, or an empty dict if we can't tell which OET-LV name(s) they are
        names of (a wrong word number is much worse than a missing one, so we give up rather than
        guess).
    'nameWords' are the OET-RV words of the one name, in the order that they appear in the verse,
        which is the OET-RV spelling of the name followed by the traditional spelling of it in the
        '!' span (e.g. ['Yohan','Markos','John','Mark']), and some of them may already have a word
        number that a human has checked.
    We work the numbers out like this:
        •  we look for the OET-LV name that each word is another spelling of, using
            getLvNameCandidates()
        •  if they all spell the names of the same OET-LV name, or each of them unambiguously
            spells the name of a different OET-LV word, we use those numbers (which is what puts
            the OET-LV numbers of 'John' and 'Mark' onto the 'John Mark' of
            'Yohan¦91464 Markos¦91468 \add !(John Mark)\add*' in the right order)
        •  if some of the words are spellings of no OET-LV word in the verse, and the rest are
            all the same one, then the rest tell us what number to give the others as well (this
            is what numbers the 'John' of 'Yohan \add !(John)\add*' in Mark 1:4, where the OET-LV
            has 'Yōannaʸs¦21698' and no 'John' word of its own)
        •  if neither of those works but the name already has exactly one word number, that one
            number covers the whole name, e.g. the 'Yohan¦92083 Markos \add !(John Mark)\add*'
            of Acts 13:13, where the OET-LV has just the one word that all four are names of
    """
    if not nameWords: return {}
    alreadyNumbered = { getRVWordNumber( word ) for word in nameWords if getRVWordNumber( word ) is not None }
    freeWords = [ word for word in nameWords if getRVWordNumber( word ) is None ]
    if not freeWords: return {} # Nothing to do

    # Which OET-LV name is each of our words a spelling of?
    numbers = []
    for word in freeWords:
        simpleWord = simplifyRVLVWord( word )
        candidateNumbers = { lvNumber for lvNumber,_lvName,spellings in lvNameList if simpleWord in spellings }
        if len( candidateNumbers ) == 1: numbers.append( candidateNumbers.pop() )
        elif candidateNumbers: numbers.append( AMBIGUOUS_LV_NAME )
        else: numbers.append( NO_LV_NAME )
    knownNumbers = set( number for number in numbers if number not in (NO_LV_NAME,AMBIGUOUS_LV_NAME) )

    if len( knownNumbers ) == 1 and NO_LV_NAME not in numbers: # The words are all names of the same one OET-LV name
        lvNumber = knownNumbers.pop()
        if alreadyNumbered and alreadyNumbered != { lvNumber }: return {} # The parts of the name disagree
        return dict( zip( freeWords, [lvNumber]*len(freeWords) ) )
    if not NO_LV_NAME in numbers and not AMBIGUOUS_LV_NAME in numbers:
        # Each word says which OET-LV word it is, and they are all different ones, so we can number
        #   them separately even when the name already has more than one number, e.g. the 'John Mark'
        #   of 'Yohan¦91464 Markos¦91468 \add !/ John Mark\add*' in Acts 12:12
        if alreadyNumbered and not alreadyNumbered.issubset( knownNumbers ): return {} # The parts of the name disagree
        return dict( zip( freeWords, numbers ) )
    # We can't work the name out from the OET-LV words, so fall back on the word number that the
    #   OET-RV already has somewhere in the name, if there is exactly one.
    if len( alreadyNumbered ) == 1:
        lvNumber = alreadyNumbered.pop()
        if all( number in (NO_LV_NAME,AMBIGUOUS_LV_NAME,lvNumber) for number in numbers ):
            return dict( zip( freeWords, [lvNumber]*len(freeWords) ) )
    return {}
# end of connect_OET-RV_words_via_OET-LV.getTraditionalNameNumbers


def matchNamesViaTraditionalNames( BBB:str, c:int,v:int, rvWordList:List[str], addSpans:List[Tuple[str,int,int]], lvWordList:List[str] ) -> Tuple[int,int]:
    """
    Connect an OET-RV name to the OET-LV word number of the name that it is another name of.

    The translator writes the traditional/KJB spelling of a name in a '!' '\add' span right after
        the OET-RV spelling of it, e.g. 'Yehudah \add !(Judah)\add*' against OET-LV
        'Yəhūdāh/Judah¦367711', because the OET-RV is allowed to spell names its own way.  Both
        spellings are one name, so we give them both the OET-LV word number, and a name that covers
        more than one OET-LV word, e.g. 'Yohan Markos \add !(John Mark)\add*', gets one number per
        OET-LV word, in the right order.
    (See getTraditionalNameNumbers() for how we decide which OET-LV name(s) we are looking at.)
    """
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag:
        fnPrint( DEBUGGING_THIS_MODULE, f"matchNamesViaTraditionalNames( {BBB} {c}:{v} {rvWordList} )" )
    assert rvWordList and lvWordList
    # We get the words of the '!' spans from the LIVE OET-RV text, because getCleanText() has
    #   already taken the '\add' markers off them, so we can't see which words they were.
    rvLiveText = getLiveRVVerseText( BBB, c,v )
    if not rvLiveText or not traditionalNameAddRegex.search( rvLiveText ): return 0,0 # No traditional names in this verse
    liveWords,allSpans = getRVWordsAndAddSpans( rvLiveText, f"{BBB} {c}:{v}",
                                                codesToExpose=(TRADITIONAL_NAME_ADD_CODE,),
                                                keepHyphenatedNames=True )
    # getRVWordsAndAddSpans() also reports the other '\add' codes that we didn't ask it to expose
    #   (the words of those spans are still in the text, with their code in front of them), so we
    #   must ignore those spans here, and we mustn't use their words as part of a name either.
    rvNameSpans = [ span for span in allSpans if span[0] == TRADITIONAL_NAME_ADD_CODE ]
    if not rvNameSpans: return 0,0
    otherSpanWords = set( rvIx for code,firstIx,lastIx in allSpans if code != TRADITIONAL_NAME_ADD_CODE
                          for rvIx in range( firstIx, lastIx+1 ) )

    NT = bos_books_codes_py.is_new_testament_nr( BBB )
    testament = 'NT' if NT else 'OT'
    lvNameList = getLvNameCandidates( lvWordList, ('NT','NT_OT') if NT else ('OT',), testament ) # The OET-LV names in this verse
    stillFree = getUnnumberedRVWords( BBB, c,v ) # So we don't fight with the matchers that ran before us
    numAdded = numNS = 0
    for _code,firstIx,lastIx in rvNameSpans:
        # The OET-RV name, followed by the traditional name of it in the '!' span.
        #   (We keep hyphenated names as one word — e.g. '\add !(Tiglat-Pileser)\add*' — because
        #   the OET-RV numbers a name like that as a single word.)
        nameWords = [ word for word in getNameWordsBeforeSpan( liveWords, firstIx, otherSpanWords ) \
                            + liveWords[firstIx:lastIx+1]
                      if word and '\\' not in word and word[0].isupper()
                      and len( word ) >= MIN_ANCHORED_ADD_WORD_LENGTH ]
        if not nameWords: continue
        numbers = getTraditionalNameNumbers( nameWords, lvNameList )
        if not numbers:
            if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  matchNamesViaTraditionalNames() skipping {BBB} {c}:{v} {nameWords=}" )
            continue
        for rvWord,lvNumber in numbers.items():
            if simplifyRVLVWord( rvWord ) not in stillFree: continue # A matcher that ran before us got there first
            if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"matchNamesViaTraditionalNames() is adding {lvNumber} to RV '{rvWord}' at {BBB} {c}:{v}" )
            result = addNumberToRVWord( BBB, c,v, rvWord, lvNumber )
            if result:
                numAdded += 1
                if NT and 'N' in state.wordTable[testament][lvNumber][state.wordTableHeaderList[testament].index('GlossCaps')]: numNS += 1
            else:
                logging.warning( f"Got addNumberToRVWord( {BBB} {c}:{v} '{rvWord}' {lvNumber} ) result = {result}" )

    return numAdded,numNS
# end of connect_OET-RV_words_via_OET-LV.matchNamesViaTraditionalNames


def matchSpecialistAddSpans( BBB:str, c:int,v:int, rvWordList:List[str], addSpans:List[Tuple[str,int,int]], lvWordList:List[str] ) -> Tuple[int,int]:
    """
    Run the matchers that use the meaning of a specialist '\add' code to find the OET-LV word
        that the words of the span stand in front of, i.e. the '@', '*', '%', '&' and '≡' codes.
    We run these BEFORE the matchers that compare the OET-RV and OET-LV words with each other,
        because these rules use what the translator told us about the span, which is firmer
        evidence than the OET-RV and OET-LV words happening to look similar.
    """
    numAdded = numNS = 0
    for matcher in ( matchWordsBesideLvAnchor, matchRepeatedWords, matchNamesViaTraditionalNames ):
        result,resultNS = matcher( BBB, c,v, rvWordList, addSpans, lvWordList )
        numAdded += result
        numNS += resultNS
    return numAdded,numNS
# end of connect_OET-RV_words_via_OET-LV.matchSpecialistAddSpans


def matchWordsManually( BBB:str, c:int,v:int, rvVerseWordList:List[str], lvVerseWordList:List[str] ) -> Tuple[int,int]:
    """
    """
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag:
        fnPrint( DEBUGGING_THIS_MODULE, f"matchWordsManually( {BBB} {c}:{v} {rvVerseWordList}, {lvVerseWordList} )" )
    assert rvVerseWordList and lvVerseWordList
    # if BBB=='JAM' and 'Jacob' in rvVerseWordList: print( lvVerseWordList ); assert False, "We want to stop here"

    # Firstly make matching lists of LV and RV words without the word numbers
    simpleLVWordList = []
    for lvWordStr in lvVerseWordList:
        try: lvWord, lvNumber = lvWordStr.split( '¦' )
        except ValueError:
            if lvWordStr != 'to':
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
    #     assert False, "We want to stop here"
    NT = bos_books_codes_py.is_new_testament_nr( BBB )

    numAdded = numNS = 0
    for rvWord, lvWordStr in RV_SINGLE_WORDS_FROM_LV_WORD_STRINGS:
        if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 4:
            dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"{rvWord=} {lvWordStr=}" )
        lvWords = lvWordStr.split( ' ' )
        assert len(lvWords) <= 3, lvWords # if more, we need to add searching code down below

        if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 4:
            dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"  Looking for RV '{rvWord}'" )
        rvIndexes = []
        for rvIx,thisRvWord in enumerate( rvVerseWordList ):
            if thisRvWord == rvWord:
                if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 4:
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
                if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
                    dPrint( 'Info', DEBUGGING_THIS_MODULE, f"matchWordsManually group1 {BBB} {c}:{v} matched {rvWord=} {lvWords=}" )
                assert '¦' in lvVerseWordList[lvIx], f"{lvIx=} {lvVerseWordList[lvIx]=} from {lvVerseWordList=}"
                lvWord,lvWordNumber,lvWordRow = getLVWordRow( lvVerseWordList[lvIx], 'NT' if NT else 'OT' )
                if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
                    dPrint( 'Info', DEBUGGING_THIS_MODULE, f"matchWordsManually group1 is adding a number to RV '{rvWord}' from '{lvWord}' at {BBB} {c}:{v} {lvIx=}")
                result = addNumberToRVWord( BBB, c,v, rvWord, lvWordNumber )
                if result:
                    numAdded += 1
                    if NT and 'N' in lvWordRow[state.wordTableHeaderList['NT' if NT else 'OT'].index('GlossCaps')]:
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
    for lvWord, rvWordStr in LV_SINGLE_WORDS_TO_RV_WORD_STRINGS:
        if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 4:
            dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"{lvWord=} {rvWordStr=}" )
        rvWords = rvWordStr.split( ' ' )
        assert len(rvWords) <= 4, rvWords # if more, we need to add searching code down below

        if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 4:
            dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"  Looking for LV '{lvWord}'" )
        lvIndexes = []
        for lvIx,thisLvWord in enumerate( simpleLVWordList ):
            if thisLvWord == lvWord:
                if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 4:
                    dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"  matchWordsManually group2 found LV '{lvWord}' in {BBB} {c}:{v}")
                lvIndexes.append( lvIx )

        if len(lvIndexes) == 1: # Only one LV word matches
            lvWordStr = lvVerseWordList[lvIndexes[0]]
            assert '¦' in lvWordStr
            lvWord, lvWordNumber = lvWordStr.split( '¦', 1 )
            lvWordNumber = getPositiveLeadingInt( lvWordNumber )
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
                            if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 4:
                                dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"        Matched 2/{len(rvWords)} @ {rvIx+1} with '{rvVerseWordList[rvIx+1]}' from '{rvWordStr}'")
                            if matchedRvWordCount == len(rvWords): break # matched two words
                            if rvIx < len(simpleRVWordList)-2:
                                if simpleRVWordList[rvIx+2] == rvWords[2]:
                                    matchedRvWordCount += 1
                                    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
                                        dPrint( 'Info', DEBUGGING_THIS_MODULE, f"          Matched 3/{len(rvWords)} @ {rvIx+2} with '{rvVerseWordList[rvIx+2]}' from '{rvWordStr}'")
                                    if matchedRvWordCount == len(rvWords): break # matched three words
                                    if rvIx < len(simpleRVWordList)-3:
                                        if simpleRVWordList[rvIx+3] == rvWords[3]:
                                            matchedRvWordCount += 1
                                            if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
                                                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"          Matched 4/{len(rvWords)} @ {rvIx+3} with '{rvVerseWordList[rvIx+3]}' from '{rvWordStr}'")
                                            if matchedRvWordCount == len(rvWords): break # matched four words
            else: # no match (no break from above/inner loop)
                continue # in the outer loop
            if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
                dPrint( 'Info', DEBUGGING_THIS_MODULE, f"    matchWordsManually group2 {BBB} {c}:{v} matched {lvWord=} {rvWords=}" )
            # lvWord,lvWordNumber,lvWordRow = getLVWordRow( lvWordList[lvIx] )
            if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
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


def getLVWordRow( wordWithNumber:str, testament:str ) -> Tuple[str,int,List[str]]:
    """
    """
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag:
        fnPrint( DEBUGGING_THIS_MODULE, f"getLVWordRow( {wordWithNumber}, {testament} )" )
    assert '¦' in wordWithNumber
    assert testament in ('OT','NT')

    try: word,wordNumber = wordWithNumber.split( '¦' ) # Gives a ValueError if the wordNumber separator character is missing or if there's multiple
    except ValueError:
        raise WordNumberError( f"Failed to split-off OET-LV word number from {testament} {wordWithNumber=}" )
    # assert word.isalpha(), f"Non-alpha '{word}'" # not true, e.g., from 'Yaʸsous/(Yəhōshūˊa)¦21754'
    try: wordNumber = int( wordNumber )
    except ValueError:
        logging.critical( f"getLVWordRow() got non-number '{wordNumber}' from '{wordWithNumber}'" )
        wordNumber = getPositiveLeadingInt( wordNumber )
    assert wordNumber < len( state.wordTable[testament] )
    wordRow = state.wordTable[testament][wordNumber]
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 4:
        dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"'{word}' {wordRow}" )
    return word,wordNumber,wordRow
# end of connect_OET-RV_words_via_OET-LV.getLVWordRow


ndStartMarker, ndEndMarker = '\\nd ', '\\nd*'

# The characters that, if they immediately follow a '\add ', indicate a special
#   rewording span (e.g., \add ≈..., \add @..., \add #..., \add !(Name)...).  Words inside those
#   special spans may keep their OET-LV word numbers.  But words inside a PLAIN
#   straight '\add ...\add*' span are words that have been ADDED into the English
#   text by the translator, so by definition they have no OET-LV word number and
#   must never be given one.
#   The 'added words' spans are written both as '\add ...\add*' and as '\+add ...\+add*',
#   and the two mean exactly the same thing, so we treat them identically.
#   (Don't confuse '\+add people\+add*' with '\add +the\add*' — the 'OET-LV' uses
#   '\add +the¦1234\add*' for an inserted article that DOES have a word number.)
ADD_SPECIAL_CHARS = '@#≈≡*<>&%?+^!'
straightAddSpanRegex = re.compile(
    f'\\\\\\+?add ([^{ADD_SPECIAL_CHARS}\\\\][^\\\\]*?)\\\\\\+?add\\*' ) # A plain '\add ...\add*' or '\+add ...\+add*' span

# A '\add <code>...<text>\add*' specialist span.  The code is what the translator is telling us
#   about the span, e.g. '\add ≈because\add*' (we reworded it) or '\add #straps\add*' (we
#   changed the number).  A leading '?' means the translator is not sure about the code
#   (e.g. '\add ?≈about\add*'), and the OET-RV never puts the '?' after the code.
specialAddSpanRegex = re.compile(
    f'\\\\\\+?add (?P<code>\\?[{ADD_SPECIAL_CHARS}]|[{ADD_SPECIAL_CHARS}])(?P<text>[^\\\\]*?)\\\\\\+?add\\*' )

# The '\add' codes that tell us how the words in the span relate to the OET-LV, so we can
#   connect them: '\add ≈because\add*' is still a translation of an OET-LV word, just in
#   different English words, and '\add #straps\add*' is the same word as an OET-LV word with
#   the opposite number.  (The '≈' code gets removed again by the normal word clean-up, the
#   '#' code is kept so that matchWordsWithChangedNumbers() knows what the word is.)
#   The '@' '*' '%' '&' and '≡' codes are also exposed, because the words in those spans
#   still stand for an OET-LV word, we just have to look for it next to the span rather than
#   in the words of the span itself (see matchWordsBesideLvAnchor() and matchRepeatedWords()).
#   We do NOT expose the other codes, because the words in those spans are NOT translations
#   of a single OET-LV word:
#     '+' and '=' and '<' and '>' are English that the translator added (an article,
#           a copula, a direct object, an implied person or object), so there is
#           no OET-LV word for them
#     '!' is the traditional/KJB spelling of the name that the OET-RV has just spelled its own
#           way, and it goes with an OET-LV name that is right next to it, so those words are
#           connected by matchNamesViaTraditionalNames() instead
#     '^' is the opposite of the OET-LV, and '?' means the translator is not even sure
#           about the code
ADD_CODES_TO_EXPOSE = ( '≈', '#', '@', '*', '%', '&', '≡', '<', '>' )
addCloseMarkerRegex = re.compile( r'\\(?:\+)?add\*$' ) # The '\add*' or '\+add*' that closes a span
addCloseMarkerAnywhereRegex = re.compile( r'\\(?:\+)?add\*' ) # The same, but punctuation can follow it
addMarkerRegex = re.compile( r'\\(?:\+)?add\*?' ) # The '\add' or '\+add' and the '\add*' or '\+add*'
# The '\add' spans that give the traditional/KJB spelling of a name, e.g. '\add !(Judah)\add*'.
#   We can't just look for the '!' character, because a '!' can also be the punctuation at the end
#   of what somebody says, e.g. '“You are God's son!”'.
traditionalNameAddRegex = re.compile( r'\\(?:\+)?add (?:\?)?!' )

# When we expose one of the ADD_CODES_TO_EXPOSE spans above, we wrap it in these two
#   Unicode private-use characters so that the matchers can still tell where the span
#   starts and ends, now that the '\add' and '\add*' markers have gone:
#       '\add ≈because\add*'  becomes  '\uE000≈because\uE001'
# The start character is followed by the code, and the end character sits at the end of the
#   span.  They never occur in an OET-RV verse, and splitExposedAddSpan() removes them (and
#   the code) from the words before the matchers compare them, so they are just bookkeeping.
ADD_SPAN_START_CHAR = '\uE000'
ADD_SPAN_END_CHAR = '\uE001'
addSpanMarkerRegex = re.compile( f'[{ADD_SPAN_START_CHAR}{ADD_SPAN_END_CHAR}]' )

def exposeMatchedAddSpans( rvText:str, codesToExpose:tuple=ADD_CODES_TO_EXPOSE ) -> str:
    """
    Rewrite the '\add' spans of an OET-RV verse that we can use to connect words (see
        ADD_CODES_TO_EXPOSE), by dropping the '\add <code>' and '\add*' markers and marking
        where the span starts and ends, e.g.
            '\add #straps\add*' becomes '\uE000#straps\uE001'
            '\add ≈because\add*' becomes '\uE000≈because\uE001'
    Every other '\add' span is left exactly as it is, so its words stay invisible to the
        matchers (i.e. they are words that were added into the English text).
    'codesToExpose' defaults to ADD_CODES_TO_EXPOSE, but matchNamesViaTraditionalNames() passes in
        just the '!' code, so that only the words of the '!' spans get exposed.
    """
    def replacer( match ):
        code = match.group( 'code' )
        if code not in codesToExpose: return match.group( 0 )
        return f"{ADD_SPAN_START_CHAR}{code}{match.group( 'text' )}{ADD_SPAN_END_CHAR}"
    return specialAddSpanRegex.sub( replacer, rvText )
# end of exposeMatchedAddSpans



def splitAddCode( word:str ) -> Tuple[str,str]:
    """
    Split a leading exposed '\add' code off the front of an OET-RV word,
        e.g. '#straps' becomes ('#', 'straps').
    This is for words taken from the LIVE OET-RV text (see getUnnumberedRVWords()), where the
        code is still sitting in front of the word; the words that come from
        exposeMatchedAddSpans() carry ADD_SPAN_START_CHAR/ADD_SPAN_END_CHAR instead.
    """
    if word and word[0] in ADD_CODES_TO_EXPOSE:
        return word[0], word[1:]
    return '', word
# end of splitAddCode


def getLiveRVVerseText( BBB:str, c:int, v:int ) -> str:
    """
    Return the CURRENT text of an OET-RV verse out of state.rvESFMLines, i.e. the text of all
        its verse and '\\d' lines joined together, EXACTLY as the file has it, so the '\\add'
        markers are still in it.
    We need that because the OET-RV object (see connect_OET_RV_Verse()) has already thrown the
        '\\add' markers away, which means we can no longer tell where a '\\add' specialist span
        starts and ends from that text.
    Returns '' if we can't find the verse.
    """
    havePsalmTitles = bos_books_codes_py.has_psalm_title( BBB, str(c) )
    desiredV = (v-1) if havePsalmTitles and v>1 else v
    verseText = ''
    C = V = None
    foundChapter = foundVerse = False
    for line in state.rvESFMLines:
        try: marker, rest = line.split( ' ', 1 )
        except ValueError: marker, rest = line, ''
        if marker in ('\\s1','\\s2','\\s3','\\r','\\rem') or not rest: continue
        if marker == '\\c':
            C = int(rest)
            if C > c: break
            if C == c: foundChapter = True
        elif foundChapter and marker == '\\v':
            Vstr, rest = rest.split( ' ', 1 ) # Drop the verse number
            V = int( Vstr.split('-',1)[0] )
            foundVerse = C==c and V==desiredV
        elif foundChapter and marker == '\\d':
            # Only a '\d' line before the '\v' of verse 1 belongs to verse 1 (see the long
            #   explanation in addNumberToRVWord()); the '\d' line at the end of HAB is not.
            foundVerse = C==c and desiredV==1 and V is None
        if not foundVerse: continue
        verseText = f"{verseText}{' ' if verseText else ''}{rest}"
    return verseText.strip()
# end of connect_OET-RV_words_via_OET-LV.getLiveRVVerseText


def getRVWordsAndAddSpans( rvText:str, connectRef:str, codesToExpose:tuple=ADD_CODES_TO_EXPOSE, keepHyphenatedNames:bool=False ) -> Tuple[List[str],List[Tuple[str,int,int]]]:
    """
    Return the OET-RV words of a verse, together with the exposed '\\add' specialist spans inside
        them, as a list of (code, first word index, last word index), e.g. ('@', 4, 6) for the
        three words of '\\add @the netted men\\add*'.

    'rvText' is the text of the OET-RV verse WITH the '\\add' markers still in it (see
        getLiveRVVerseText()), so we can see where each span starts and ends.  It can also be a
        text that has already lost its markers, in which case we can still see the code on the
        front of the first word of a span (e.g. '@Yeshua' for '\\add @Yeshua\\add*'), and we
        then treat the span as being that one word, which is all that the '≈' and '#' codes need.

    'keepHyphenatedNames' keeps a hyphenated capitalised name as the single word that it is in the
        OET-RV, e.g. 'Tiglat-Pileser' in '\add !(Tiglat-Pileser)\add*', because we number such a
        name as one word.  matchNamesViaTraditionalNames() needs that, but nobody else does,
        because everywhere else the parts of a hyphenated word are compared separately.
    A hyphenated word that is NOT capitalised, e.g. 'empty-handed', is the one word that the OET-RV
        and the OET-LV both use, so we keep it as one word (see simplifyRVLVWord(), which takes the
        hyphens out before it compares the two).  A capitalised one is still split into its parts,
        because there the OET-LV usually glosses the parts as separate words.
    """
    rvAdjText = exposeMatchedAddSpans( rvText, codesToExpose )
    # getCleanText() gives us text whose '\add' spans have lost their markers, but the text
    #   from getLiveRVVerseText() still has the markers on the spans that we didn't expose, so
    #   remove them to get the same words from both
    rvAdjText = addMarkerRegex.sub( '', rvAdjText ) \
                .replace(ORDER_REVERSAL_CHARACTER,'').replace('◘','').replace('…','') \
                .replace(' / ',' ').replace('/',' ').replace('—',' ') \
                .replace( '(', '').replace( ')', '' ) \
                .replace( '“', '' ).replace( '”', '' ).replace( '‘', '' ).replace( '’', '' )
    # Strip the sentence punctuation, but not a punctuation character that is one of the codes we
    #   were asked to expose: the '!' of a traditional-name span is punctuation AND its code, and
    #   splitExposedAddSpan() has to see it to report which span it is.
    for punctuation in ( '.', ',', ':', ';', '?', '!' ):
        if punctuation not in codesToExpose: rvAdjText = rvAdjText.replace( punctuation, '' )
    rvAdjText = rvAdjText.replace('  ',' ').strip()
    if not rvAdjText: return [],[]

    rvWords = []
    rvAddSpans = [] # The exposed '\add' specialist spans in rvWords, as (code, first word index, last word index)
    addSpanCode = addSpanStartIx = None
    for rvToken in rvAdjText.split( ' ' ):
        # Note that a token can be dropped below (a hyphenated word whose second part isn't
        #   capitalised, e.g. 'whole-heartedly'), so we have to keep track of the span markers
        #   on such a token, or we would lose the start or the end of the '\add' span it is in
        spanEvents,rvToken = splitExposedAddSpan( rvToken, codesToExpose )
        if rvToken:
            rvWordBits = rvToken.split( '-' )
            if len(rvWordBits) == 1 or keepHyphenatedNames: rvNewWords = [ rvToken ] # No hyphen, or a hyphenated name that we keep as one word
            elif rvWordBits[1] and rvWordBits[1][0].isupper(): # Hyphenated and with a capital letter, e.g., Kiriat-Arba (may even have three parts)
                rvNewWords = rvWordBits
            elif not rvToken[0].isupper(): rvNewWords = [ rvToken ] # Hyphenated but not capitalised, e.g. 'empty-handed', which is one word in the OET-RV and in the OET-LV
            else: rvNewWords = [] # A capitalised name whose second part is a word of its own, e.g. 'Yahweh-nissi', which we leave to the proper-noun matchers
        else: rvNewWords = [] # An exposed '\add' span that holds no words
        for event,code in spanEvents:
            if event == 'start':
                assert addSpanCode is None, f"Nested exposed '\\add' span at {connectRef} {rvToken=}"
                addSpanCode = code
                addSpanStartIx = len( rvWords ) # The index that the first new word (if any) will get
        rvWords.extend( rvNewWords )
        for event,code in spanEvents:
            if event == 'start': continue
            assert addSpanCode is not None, f"Unclosed exposed '\\add' span at {connectRef} {rvToken=}"
            if rvWords: rvAddSpans.append( (addSpanCode,addSpanStartIx,len( rvWords )-1) )
            addSpanCode = addSpanStartIx = None
    assert addSpanCode is None, f"Unclosed exposed '\\add' span at {connectRef}"
    return rvWords, [ addSpan for addSpan in rvAddSpans if addSpan[1] <= addSpan[2] ]
# end of connect_OET-RV_words_via_OET-LV.getRVWordsAndAddSpans


def splitExposedAddSpan( token:str, codesToExpose:tuple=ADD_CODES_TO_EXPOSE ) -> Tuple[List[Tuple[str,str]],str]:
    """
    Pull the exposed '\add' span markers off a token that came from exposeMatchedAddSpans(),
        e.g. '\uE000#straps' becomes ([('start','#'),('end','')], 'straps') and 'demons\uE001'
        becomes ([('end','')], 'demons').
    'token' must be a single word, so a word can only be the start or the end of a span (or
        both, if the span holds a single word), but it could still be the end of one span and
        the start of the next, so we return the events in the order that they appear in the
        word.
    A token that has no span markers but does start with one of the ADD_CODES_TO_EXPOSE codes
        (e.g. '#straps' or '@Yeshua') is a span of one word that lost its '\add' markers, and we
        return it as such, so that the caller doesn't have to treat those two cases differently.
    'codesToExpose' is the same tuple that exposeMatchedAddSpans() was given, so that we can
        recognise a code that it exposed but that isn't one of the usual ones (e.g. the '!' of
        matchNamesViaTraditionalNames()).
    """
    if ADD_SPAN_START_CHAR not in token and ADD_SPAN_END_CHAR not in token:
        if token[0:1] in ADD_CODES_TO_EXPOSE:
            return [ ('start',token[0]), ('end','') ], token[1:]
        return [], token
    events = []
    bits = []
    pos = 0
    for marker in addSpanMarkerRegex.finditer( token ):
        bits.append( token[pos:marker.start()] )
        pos = marker.end()
        if marker.group( 0 ) == ADD_SPAN_START_CHAR:
            # The '\add' code follows the start marker, but only if it is still there
            #   (the '≈' code used to be removed by the normal word clean-up, and an
            #   exposed span that holds no words has no code at all)
            code = token[pos:pos+1] if token[pos:pos+1] in codesToExpose else ''
            events.append( ('start',code) )
            if code: pos += 1
        else:
            events.append( ('end','') )
    bits.append( token[pos:] )
    return events, ''.join( bits )
# end of splitExposedAddSpan


def stripAddMarkers( token:str ) -> str:
    """
    Reduce one token of the live OET-RV verse text to a plain word, by removing a leading
        exposed '\add' code and a trailing '\add*' close marker, e.g. '#straps' becomes
        'straps' and 'forgiven\add*' becomes 'forgiven'.
    The close marker doesn't have to be at the very end of the token, because punctuation can
        follow it, e.g. '!(Mary)\add*,' becomes 'Mary'.
    """
    if '\\' in token: token = addCloseMarkerAnywhereRegex.sub( '', token )
    _addCode,token = splitAddCode( token )
    return simplifyRVLVWord( token )
# end of stripAddMarkers


def isInsideStraightAddSpan( line:str, index:int ) -> bool:
    """
    Return True if the character at 'index' in 'line' falls inside a PLAIN straight
        '\\add ...\\add*' or '\\+add ...\\+add*' span (either 'added words' or a bracketed
        translation that was added into the English text).
    """
    return any( match.start() < index < match.end()
                for match in straightAddSpanRegex.finditer( line ) )
# end of isInsideStraightAddSpan


ndStartMarkerRegex = re.compile( r'\\\+?nd ' ) # A nomina sacra open marker, e.g. '\nd ' or '\+nd '
ndEndMarkerRegex = re.compile( r'\\\+?nd\*' ) # A nomina sacra close marker, e.g. '\nd*' or '\+nd*'

def isInsideNominaSacraSpan( line:str, index:int ) -> bool:
    """
    Return True if the character at 'index' in 'line' is inside a nomina sacra
        '\\nd ...\\nd*' span that has already been opened before 'index'.

    We count the open and the close markers that come before 'index' rather than matching
        '\\nd ...\\nd*' spans with a single regex, because we cannot pair the markers up with a
        regex once they are nested, and nesting them is exactly the fault that this function
        exists to detect: an earlier run could insert a '\\nd ...\\nd*' span around a word that
        was already the first word of one, giving 'son¦113159 \\nd \\nd Yeshua¦113161\\nd*'.
    """
    numOpens = len( ndStartMarkerRegex.findall( line[:index] ))
    numCloses = len( ndEndMarkerRegex.findall( line[:index] ))
    return numOpens > numCloses
# end of isInsideNominaSacraSpan


def removeWordNumbersInStraightAddSpans( filename:str, lines:List[str] ) -> int:
    """
    Remove any word numbers (¦nnnnn) that are inside a PLAIN straight '\\add ...\\add*'
        or '\\+add ...\\+add*' span.

    Words inside such a span were ADDED into the English text by the translator,
        so by definition they have no OET-LV word number.
    addNumberToRVWord() now refuses to give them one,
        but any that were inserted before that check was added still need to be cleaned up.

    'lines' is modified in place.
    Returns the number of word numbers that were removed.
    """
    numRemoved = 0
    for n,line in enumerate( lines ):
        if '¦' not in line: continue # Fast path for the many lines that have no word numbers at all
        spanMatches = [spanMatch for spanMatch in straightAddSpanRegex.finditer( line )
                            if '¦' in spanMatch.group(1)]
        if not spanMatches: continue

        numLineRemoved = 0
        newLineBits, lastIndex = [], 0
        for spanMatch in spanMatches:
            cleanedSpanText, numSpanRemovals = wordLinkRegex.subn( '', spanMatch.group(1) ) # The span text without any word numbers
            assert numSpanRemovals, f"Failed to remove a word number from a straight \\add span in {filename} line {n+1}: '{line[spanMatch.start():spanMatch.end()]}'"
            assert cleanedSpanText.strip(), f"Removing the word number(s) would leave an empty straight \\add span in {filename} line {n+1}: '{line[spanMatch.start():spanMatch.end()]}'" # This shouldn't happen, but we don't want to silently create a broken field
            numLineRemoved += numSpanRemovals
            newLineBits.append( line[lastIndex:spanMatch.start(1)] ) # Everything up to the text inside the \add span
            newLineBits.append( cleanedSpanText ) # The text inside the \add span, with the word numbers removed
            lastIndex = spanMatch.end(1)
        newLineBits.append( line[lastIndex:] ) # The rest of the line (including the closing \add*)

        numRemoved += numLineRemoved
        if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 2:
            vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"    Removed {numLineRemoved:,} word number(s) from inside a straight '\\add'/'\\+add' span in {filename} line {n+1}: '{line[max(0,spanMatches[0].start()-10):spanMatches[-1].end()+10]}'" )
        lines[n] = ''.join( newLineBits )
    return numRemoved
# end of removeWordNumbersInStraightAddSpans


def removeWordNumbersInStraightAddSpansInAllBooks( ) -> int:
    """
    Remove any word numbers inside a plain '\\add ...\\add*' or '\\+add ...\\+add*' span
        from EVERY OET-RV book, not just the books that are about to get new connections.

    Words inside such a span were added into the English text by the translator,
        so by definition they have no OET-LV word number, and a leftover one is simply wrong.
    We do this for all books (even in 'fast' mode, which only connects MRK) because this is
        a data cleanup rather than a new connection, and a wrong number stays wrong
        wherever we leave it.

    Prints a message saying what it did, so it is obvious if it changed anything.
    Returns the total number of word numbers that were removed.
    """
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 1:
        vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"\nRemoving any word numbers from inside plain '\\add'/'\\+add' spans in all OET-RV books…" )
    numBooksChanged = 0
    numTotalRemoved = 0
    for rvESFMFilepath in sorted( OET_RV_ESFM_FolderPath.glob( 'OET-RV_*.ESFM' ) ):
        with open( rvESFMFilepath, 'rt', encoding='UTF-8' ) as esfmFile:
            oldText = esfmFile.read()
        lines = oldText.split( '\n' )
        numRemoved = removeWordNumbersInStraightAddSpans( rvESFMFilepath.name, lines )
        if not numRemoved: continue
        newText = '\n'.join( lines )
        assert newText != oldText, f"removeWordNumbersInStraightAddSpans said it removed {numRemoved} word number(s) from {rvESFMFilepath.name} but the text is unchanged"
        for line in lines: # Just to be sure we didn't leave any behind
            assert not any( '¦' in spanMatch.group(1) for spanMatch in straightAddSpanRegex.finditer( line ) ), \
                f"Still a word number inside a straight \\add span in {rvESFMFilepath.name}: '{line}'"
        with open( rvESFMFilepath, 'wt', encoding='UTF-8' ) as esfmFile:
            esfmFile.write( newText )
        numBooksChanged += 1
        numTotalRemoved += numRemoved
        if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 2:
            vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"    Removed {numRemoved:,} word number(s) from inside plain '\\add'/'\\+add' spans in {rvESFMFilepath.name} and saved it." )
    if numTotalRemoved:
        if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 2:
            vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Removed a total of {numTotalRemoved:,} wrongly-placed word number(s) from inside plain '\\add'/'\\+add' spans in {numBooksChanged:,} OET-RV book(s)." )
    else:
        if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 2:
            vPrint( 'Normal', DEBUGGING_THIS_MODULE, "  No word numbers inside plain '\\add'/'\\+add' spans needed removing." )
    return numTotalRemoved
# end of removeWordNumbersInStraightAddSpansInAllBooks


# The OET-RV lines that hold something other than translated Bible text, so their words can never
#   have a word number: section headings, the translator's heading comments, the titles of the
#   poetry sections, the speaker of a saying, and the letters of an acrostic poem.
nonTextLineMarkers = ( '\\s1','\\s2','\\s3','\\s4','\\r','\\rem','\\mr','\\ms1','\\ms2','\\sp','\\sr','\\qa' )
# The OET-RV spans that hold something other than translated Bible text, so their words can never
#   have a word number: the translator's notes ('\f ...\f*', including the '\fr'/'\ft' sub-parts),
#   the cross-references ('\x ...\x*'), and the file and image links ('\jmp ...\jmp*', '\fig ...\fig*').
nonTextSpanRegex = re.compile( r'\\(f[a-z]*|x|jmp|fig)\b.*?\\\1\*' )
# The OET-RV characters that run two words together (e.g. 'Satan¦29058—you're¦29061'),
#   or that are not a word at all, so that we get the same words that
#   getRVWordsAndAddSpans() gets when it matches the OET-RV against the OET-LV
rvWordSeparatorChars = ( ORDER_REVERSAL_CHARACTER, '◘', '…', '—', '/', '(', ')' )
# Any other USFM marker that is left in an OET-RV verse, e.g. '\nd ' or '\wj' or '\+add*'
#   (The '+/add*' variants are the continued-character markers, which the OET-RV uses for the
#    nomina sacra and for the added-words spans.)
usfmMarkerRegex = re.compile( r'\\\+?[a-zA-Z0-9]+\*?' )

def stripUSFMMarker( match ) -> str:
    """
    Replacement function for usfmMarkerRegex: take a USFM marker out of an OET-RV verse.

    We leave a space behind if the marker was stuck onto the end of the word in front of it
        (e.g. 'God¦123\\+nd*' or 'first\\wj*second'), so that we don't run those two words together.
    A marker that is stuck onto the front of the next word (e.g. '\\add*brothers') just goes,
        because there is nothing in front of it to run it together with.
    """
    return ' ' if match.start() and not match.string[match.start()-1].isspace() else ''
# end of stripUSFMMarker

def getVerseTextWords( verseText:str ) -> List[str]:
    """
    Split the text of an OET-RV verse into the words that could have an OET-LV word number.

    We throw away the words that can never have one, so that they are left out of the word
        number percentages (see countWordsAndWordNumbers()):
            the translator's notes, the cross-references and the file/image links, because they
                are not translations of the Hebrew or Greek at all
            the words inside a PLAIN straight '\\add ...\\add*' span, because they were ADDED into
                the English text by the translator, so they have no OET-LV word to be numbered
    (The words of the other '\\add' spans, e.g. '\\add ≈because\\add*', DO get word numbers,
        because they are still translations of an OET-LV word, so we keep them here.)
    The word numbers themselves are left attached to their words, so the caller can count them.
    """
    text = nonTextSpanRegex.sub( ' ', verseText ) # The notes, the cross-references and the links
        # NOTE: These have to go first, because a note can be inside a straight '\add' span
    text = straightAddSpanRegex.sub( ' ', text ) # The words that were ADDED into the English text
    for separatorChar in rvWordSeparatorChars:
        text = text.replace( separatorChar, ' ' ) # The characters that run two words together
    text = usfmMarkerRegex.sub( stripUSFMMarker, text ).strip() # The markers that are left
    return [ word for word in text.split() if any(char.isalnum() for char in word) ] # Ignore stray punctuation
# end of getVerseTextWords


def countWordsAndWordNumbers( rvESFMLines:List[str] ) -> Tuple[int,int]:
    """
    Count the words of an OET-RV book that could have a word number, and how many of them have one.

    We only count the text of the verses (including their poetry lines, and the '\\d' lines of
        Psalms), because that is the only text that gets connected to the OET-LV.
    The words that can never have a word number are left out of BOTH figures
        (see getVerseTextWords()), so that the percentage says how much of the OET-RV that we
        have actually connected to the OET-LV.

    Returns a (numWords,numWordNumbered) tuple.
    """
    numWords = numWordNumbered = 0
    foundVerse = False
    for line in rvESFMLines:
        try: marker, rest = line.split( ' ', 1 )
        except ValueError: marker, rest = line, '' # Only a marker
        if not rest or marker in nonTextLineMarkers: continue
        if marker == '\\c': foundVerse = False # A new chapter, so any verse of the last one is finished
        elif marker == '\\v':
            _verseNumber,_separator,rest = rest.partition( ' ' ) # Drop the verse number
            foundVerse = True
        elif marker == '\\d': foundVerse = True # The Psalms titles, which belong to verse 1
        if not foundVerse: continue # Not the text of a verse, e.g. the book introduction
        verseWords = getVerseTextWords( rest )
        numWords += len( verseWords )
        numWordNumbered += sum( 1 for verseWord in verseWords if '¦' in verseWord )
    return numWords, numWordNumbered
# end of countWordsAndWordNumbers


def reportWordNumberPercentage( description:str, numWords:int, numWordNumbered:int ) -> None:
    """
    Say what percentage of the words of 'description' (e.g. 'OT' or 'Whole Bible') have a word number.
    """
    if not numWords:
        if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 2:
            vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  No words found for {description}." )
        return
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 2:
        vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  {description} has word numbers on {numWordNumbered:,} of {numWords:,} words ({numWordNumbered*100/numWords:.1f}%)." )
# end of reportWordNumberPercentage


def maskFootnoteSpans( line:str ) -> str:
    """
    Replace the contents of any '\\f ...\\f*' footnote span with spaces,
        while keeping the line the same length so that character offsets stay valid.
    This lets us search for words inside the verse text without matching
        identical wording that happens to sit in a footnote (e.g. 'first')."""
    bits = []
    i = 0
    while True:
        start = line.find( '\\f ', i )
        if start < 0: break
        end = line.find( '\\f*', start )
        if end < 0:
            logging.warning( f"Unterminated \\f footnote span in: '{line}'" )
            break
        end += len( '\\f*' )
        bits.append( line[i:start] )
        bits.append( ' ' * (end - start) )
        i = end
    bits.append( line[i:] )
    return ''.join( bits )
# end of maskFootnoteSpans


def addNumberToRVWord( BBB:str, c:int,v:int, word:str, wordNumber:int ) -> bool | None:
    """
    Go through the RV USFM for BBBB and find the lines for c:v (which comes from Original/OET-LV verse numbering)

    Then try to find the word in the line.

    If there's only one word that it can be,
        then append the word number
        and also surround it with a nomina sacra span if necessary
    """
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag:
        fnPrint( DEBUGGING_THIS_MODULE, f"addNumberToRVWord( {BBB} {c}:{v} '{word}' {wordNumber} )" )
    assert isinstance( wordNumber, int )
    assert '¦' not in word
    # if BBB=='MAT' and v==1: print( word )

    NT = bos_books_codes_py.is_new_testament_nr( BBB )
    havePsalmTitles = bos_books_codes_py.has_psalm_title( BBB, str(c) )
    desiredV = (v-1) if havePsalmTitles and v>1 else v

    if NT:
        if wordNumber in (119_194,142_216,149_264,149_303,149_665,149_715,149_739,149_829,149_847,150_387):
            return None # TODO: 1Cor 14:33, Heb 1:6, 1 Pet 2:19,21, 3:15,16,18,21, 4:1 (nd gets put inside add field).................................................................................
    else:
        if wordNumber in (252_390,): return None # TODO: PSA 54:1 (v1 gets put into d field).................................................................................

    C = V = None
    foundChapter = foundVerse = False
    for n,line in enumerate( state.rvESFMLines[:] ): # iterate through a copy
        try: marker, rest = line.split( ' ', 1 )
        except ValueError: marker, rest = line, '' # Only a marker
        if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 4:
            dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"addNumberToRVWord A searching {BBB} {C}:{V} {marker}='{rest}'" )
        if marker in ('\\s1','\\s2','\\s3','\\r','\\rem') or not rest:
            continue # Skip these fields (so we don't add word numbers to headings, etc.)
        if marker == '\\c':
            C = int(rest)
            if C > c: return False # Gone too far
            if C == c: foundChapter = True
        elif foundChapter and marker == '\\v':
            if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 4:
                dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"addNumberToRVWord B searching {BBB} {C}:{V} {marker}='{rest}'")
            Vstr, rest = rest.split( ' ', 1 )
            try: V = int(Vstr)
            except ValueError: # might be a range like 21-22
                V = int(Vstr.split('-',1)[0])
            foundVerse = C==c and V==desiredV
        elif foundChapter and marker == '\\d':
            if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 4:
                dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"addNumberToRVWord D searching {BBB} {C}:{V} {marker}='{rest}'")
            assert havePsalmTitles or BBB=='HAB', f"addNumberToRVWord( {BBB} {c}:{v} {word=} {havePsalmTitles=} {marker=} {rest=}"
            # A '\d' line is only the title of verse 1 if it comes BEFORE the '\v' of verse 1, which
            #   is where the Psalm titles sit.  We must check V is still None, because a '\d' line
            #   anywhere else in the chapter is not part of verse 1 at all.  HAB is the case in
            #   point: its single '\d' line (the musical direction for the book) sits AFTER 3:19, so
            #   without this check we claimed it for HAB 3:1 and numbered a word in it with a word
            #   number from 3:1, because 3:1 happens to have more than one 'the' for us to choose
            #   between, so we carried on looking and found a line with exactly one.
            foundVerse = C==c and desiredV==1 and V is None
        if foundVerse:
            searchLine = maskFootnoteSpans( line )
            allWordMatches = [match for match in re.finditer( f'\\b{word}\\b', searchLine )] # Matches of the word standing alone
            if len(allWordMatches) == 1:
                match = allWordMatches[0]
                if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
                    dPrint( 'Info', DEBUGGING_THIS_MODULE, type(allWordMatches), type(match), match )
                assert match.group(0) == word
                if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
                    dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  Found {word=} {line=}" )
                if isInsideStraightAddSpan( line, match.start() ): # the word was ADDED into the English text
                    logger = logging.critical if DEBUGGING_THIS_MODULE else logging.error
                    logger( f"Refusing to add a word number to the ADDED OET-RV word '{word}' in {BBB} {C}:{V} (inside straight \\add or \\+add span) from '{line[match.start()-5:match.end()+5]}'" )
                    # already_numbered_error
                    return False
                wordRow = state.wordTable['NT' if NT else 'OT'][wordNumber]
                if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
                    dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  Found {word=} {line=} {wordRow=}" )
                # TODO: Why do we often get the wrong row (in the NT at least)
                # if BBB=='ROM' and not word[0].isupper(): # No, this fails too often
                #     assert word in str(wordRow), f"{BBB} {c}:{v} Can't find {word=} ({wordNumber=}) in {wordRow=}"
                addNominaSacra = False
                if NT and 'N' in wordRow[state.wordTableHeaderList['NT'].index('GlossCaps')]: # Check that the RV doesn't already have it marked (with /nd)
                                      #   (This can happen after word numbers are deleted.)
                    # print( f"{word=} {wordNumber=} index={state.wordTableHeaderList['NT'].index('GlossCaps')} {wordRow[state.wordTableHeaderList['NT'].index('GlossCaps')]=} {wordRow=}" )
                    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
                        dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  Have NS on {word=} {line[match.start()-6:match.start()]=} {line[match.end():match.end()+6]=} {line=}" )
                    if (match.end()==len(line) or not line[match.end()]=='¦') \
                    and not line[match.end():match.end()+4] == '\\nd*' \
                    and not line[match.end():match.end()+5] == '\\+nd*' \
                    and not isInsideNominaSacraSpan( line, match.start() ):
                        addNominaSacra = True
                        if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
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
                    elif addNominaSacra and line[match.end():].lstrip( ' ' ).startswith( ('\\add*','\\+add*') ): # we're inside a \add field
                        #   Note that the '\add*' can be right up against the word (e.g. '\add @God\add*'),
                        #   so we have to allow for there not being a space before it
                        logger = logging.critical if DEBUGGING_THIS_MODULE else logging.error
                        logger( f"Tried to append nomina sacra inside added word(s) {BBB} {C}:{V} {marker} '{line[match.start():match.end()]}' (from '{line[match.start():match.end()+5]}') -> '{word}¦{wordNumber}'" )
                        # nd_inside_add_error
                        return False
                    else: # seems all ok
                        state.rvESFMLines[n] = f'''{line[:match.start()]}{ndStartMarker if addNominaSacra else ''}{word}¦{wordNumber}{ndEndMarker if addNominaSacra else ''}{line[match.end():]}'''
                        # print( f"{word=} {line=}" )
                        if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
                            dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  addNumberToRVWord() added ¦{wordNumber}{' and nomina sacra' if addNominaSacra else ''} to '{word}' in OET-RV {BBB} {c}:{v}" )
                        return True
                except IndexError: # if the word is at the END OF THE LINE
                    assert line.endswith( word )
                    state.rvESFMLines[n] = f'''{line[:-len(word)]}{ndStartMarker if addNominaSacra else ''}{word}¦{wordNumber}{ndEndMarker if addNominaSacra else ''}'''
                    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
                        dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  addNumberToRVWord() added ¦{wordNumber}{' and nomina sacra' if addNominaSacra else ''} to final '{word}' in OET-RV {BBB} {c}:{v}" )
                    return True
            else:
                if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
                    dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  addNumberToRVWord {BBB} {c}:{v} '{word}' found {len(allWordMatches)=}" )
# end of connect_OET-RV_words_via_OET-LV.addNumberToRVWord


def addNumberToRVPhrase( BBB:str, c:int,v:int, rvPhraseWords:List[str], lvNumber:int ) -> Tuple[int,int]:
    """
    Give 'lvNumber' to every word of the OET-RV phrase 'rvPhraseWords', wherever that phrase is in
        the verse, e.g. both words of the 'young donkey' that the OET-RV uses for the OET-LV 'colt'.

    addNumberToRVWord() can only number a word that occurs ONCE in the verse, which almost never
        works for the little words that these phrases are made of: Mark 6:10 has both the 'you' of
        'you all' and the 'you' of "you're", so neither 'you' can be found on its own.  So this
        looks for the whole PHRASE instead, and only goes ahead if the phrase occurs exactly once
        in the unnumbered text of the verse (a verse that uses the phrase twice could be using the
        two occurrences for two different OET-LV words, and we can't tell which is which without
        an alignment).  A word of the phrase that already has a word number keeps it, so that a
        repeat of the same phrase elsewhere in the verse is not counted as a second candidate, and
        so that a phrase that one of the other matchers has half connected can be finished off --
        but only if the number that is already there is the one that we want to give the phrase.

    Returns the number of word numbers added, and the number of nomina sacra added (always 0,
        because none of the words that we put phrases together from are nomina sacra).
    """
    assert isinstance( lvNumber, int )
    assert len( rvPhraseWords ) > 1, f"addNumberToRVPhrase needs more than one OET-RV word, not {rvPhraseWords=}"
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag:
        fnPrint( DEBUGGING_THIS_MODULE, f"addNumberToRVPhrase( {BBB} {c}:{v} {rvPhraseWords} {lvNumber} )" )
    havePsalmTitles = bos_books_codes_py.has_psalm_title( BBB, str(c) )
    desiredV = (v-1) if havePsalmTitles and v>1 else v

    # Build a regex that matches the words of the phrase in order, with any whitespace and USFM
    #   markers allowed in between, and with an already existing word number allowed after a word
    phraseRegexBits = []
    for ix,word in enumerate( rvPhraseWords ):
        if phraseRegexBits: phraseRegexBits.append( rvPhraseSeparatorRegex )
        phraseRegexBits.append( rf'\b(?P<word{ix}>{re.escape(word)})\b(?:¦\d+)?' )
    phraseRegex = re.compile( ''.join( phraseRegexBits ), re.IGNORECASE )

    C = V = None
    foundChapter = foundVerse = False
    occurrences = [] # The (line number, match) of each place in this verse where the phrase is still unnumbered
    for n,line in enumerate( state.rvESFMLines[:] ): # iterate through a copy
        try: marker, rest = line.split( ' ', 1 )
        except ValueError: marker, rest = line, '' # Only a marker
        if marker in ('\\s1','\\s2','\\s3','\\r','\\rem') or not rest: continue
        if marker == '\\c':
            C = int(rest)
            if C > c: break
            if C == c: foundChapter = True
        elif foundChapter and marker == '\\v':
            Vstr, rest = rest.split( ' ', 1 )
            try: V = int(Vstr)
            except ValueError: V = int(Vstr.split('-',1)[0]) # It can be a range like 21-22
            foundVerse = C==c and V==desiredV
        elif foundChapter and marker == '\\d':
            # Only a '\d' line before the '\v' of verse 1 belongs to verse 1 (see the long
            #   explanation in addNumberToRVWord()); the '\d' line at the end of HAB is not.
            foundVerse = C==c and desiredV==1 and V is None
        if not foundVerse: continue
        # Blank out the notes, the cross-references and the links, because the translator's
        #   notes often quote the OET-RV text, but keep the length the same so that the
        #   match.start() indexes below still point at the right characters of the real line
        searchLine = nonTextSpanRegex.sub( lambda match: ' '*( match.end() - match.start() ), line )
        for match in phraseRegex.finditer( searchLine ):
            rvSpans = [ match.span( f'word{ix}' ) for ix in range(len(rvPhraseWords)) ] # The (start,end) of each word of the phrase
            if all( rvEnd < len(line) and line[rvEnd] == '¦' for rvStart,rvEnd in rvSpans ):
                continue # This occurrence already has all of its word numbers
            occurrences.append( (n,match) )

    if len( occurrences ) != 1:
        # Zero means the OET-RV really doesn't use the phrase here, and more than one means we
        #   can't tell which occurrence stands for this OET-LV word without an alignment
        if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
            dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  addNumberToRVPhrase() found the phrase '{rvPhraseWords}' {len( occurrences ):,} times in the unnumbered text of OET-RV {BBB} {c}:{v}, not exactly once" )
        return 0,0

    n,match = occurrences[0]
    line = state.rvESFMLines[n] # Get this again, in case a previous call has changed the line
    rvSpans = [ match.span( f'word{ix}' ) for ix in range(len(rvPhraseWords)) ]
    # A word of the phrase that one of the other matchers has already numbered has to carry the
    #   same number that we are about to give the rest of the phrase, or we have no idea which
    #   OET-LV word that other matcher had in mind
    for rvStart,rvEnd in rvSpans:
        if rvEnd >= len(line) or line[rvEnd] != '¦': continue # This word is unnumbered
        existingNumber = int( re.match( r'¦(\d+)', line[rvEnd:] ).group(1) )
        if existingNumber != lvNumber:
            logger = logging.critical if DEBUGGING_THIS_MODULE else logging.error
            logger( f"Refusing to add the OET-LV word number {lvNumber} to the OET-RV phrase '{' '.join(rvPhraseWords)}' in {BBB} {c}:{v}, because the word '{line[rvStart:rvEnd]}' is already numbered {existingNumber}" )
            return 0,0
    if any( isInsideStraightAddSpan( line, rvStart ) for rvStart,rvEnd in rvSpans ):
        # These words are inside a plain '\add' span, which removeWordNumbersInStraightAddSpans()
        #   deliberately leaves unnumbered, so a number here would just be stripped out again
        logger = logging.critical if DEBUGGING_THIS_MODULE else logging.error
        logger( f"Refusing to add a word number to the ADDED OET-RV phrase '{' '.join(rvPhraseWords)}' in {BBB} {c}:{v} (inside straight \\add or \\+add span)" )
        return 0,0

    # Add the numbers from the end of the line backwards, so that the earlier indexes
    #   stay valid as we go
    numAdded = 0
    for rvStart,rvEnd in reversed( rvSpans ):
        if rvEnd < len(state.rvESFMLines[n]) and state.rvESFMLines[n][rvEnd] == '¦': continue # This word already has a word number
        state.rvESFMLines[n] = f'{state.rvESFMLines[n][:rvEnd]}¦{lvNumber}{state.rvESFMLines[n][rvEnd:]}'
        numAdded += 1
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
        dPrint( 'Info', DEBUGGING_THIS_MODULE, f"  addNumberToRVPhrase() added ¦{lvNumber} to {numAdded} word(s) of '{rvPhraseWords}' in OET-RV {BBB} {c}:{v}" )
    return numAdded,0
# end of connect_OET-RV_words_via_OET-LV.addNumberToRVPhrase


if __name__ == '__main__':
    multiprocessing.set_start_method('fork') # The default was changed on POSIX systems from 'fork' to 'forkserver' in Python3.14
    multiprocessing.freeze_support() # Multiprocessing support for frozen Windows executables

    # Configure basic Bible Organisational System (BOS) set-up
    parser = BibleOrgSysGlobals.setup( PROGRAM_NAME, PROGRAM_VERSION )
    parser.add_argument("-f", "--fast", action="store_true", dest="fastMode", default=False, help="only work on unfinished books")
    BibleOrgSysGlobals.addStandardOptionsAndProcess( parser, exportAvailable=False )

    main()

    BibleOrgSysGlobals.closedown( PROGRAM_NAME, PROGRAM_VERSION )
# end of connect_OET-RV_words_via_OET-LV.py
