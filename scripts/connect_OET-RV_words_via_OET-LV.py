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
In general, it attempts to match the longer words and the names / proper nouns
    in the verse first, the later tries to connect the smaller words.

It does have the potential to make wrong connections that will need to be manually fixed
        when the rest of the OET-RV words are aligned,
    but hopefully this script is relatively conservative
        so that the number of wrong alignments is not huge.

Specialised \\add spans:
    Normal character markers start with a backslash,
        but embedded character markers (often inside a '\\wj ' words-of-Jesus span)
            must have a + character after the backslash for both the opening and the closing marker,
            so all the following examples that start with '\\' can also start with '\\+'.
    '\\add ' spans must be closed by '\\add*' markers.
        '\\+add ' spans must be closed by '\\+add*' markers.
    The \\add spans below can also indicate uncertainty
        by having a ? immediately after the '\\ add ',
        i.e., before any of the specialist characters (like @*<>≡≈) if present.

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
        In this case 'the hand' might become '\\add &his\\add* hand' or '\\add &that\\add* hand'.
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
    Alternate '\\add !' or '\\+add !' or '\\add ?!' or '\\+add ?!' name spans:
        Because an English Bible translation is using a mixture of Hebrew, Greek, and English names,
            we often want to display more than one form of the name to the reader.
        The OET-RV mostly puts a rough Hebrew or Greek transliteration first,
            followed by the traditional name in parentheses,
            e.g., 'Shelomo (\\add !Solomon\\add*)'
        Both forms of the name should be linked to the OET-LV name by having the same word number.

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
    2026-10-06 Added the first OT-specific verb sets (play, provoke, slip, wean) after running the
        same OET-RV against OET-LV OT word-table (Morphology 'V...') analysis
    2026-10-06 Removed the conservative "only Messiah/Yeshua/God" nomina sacra allow-list, so that
        a genuine OET-LV nomina sacra match (e.g. the RV "God's¦" at Mrk 8:33, 9:1, 7:9, 7:13)
        now always gets its \\nd ... \\nd* (or \\+nd ... \\+nd*) markup; the CRITICAL messages are gone
    2026-10-06 Added NT noun/adjective singular/plural variant pairs to
        RV_SINGLE_WORDS_FROM_LV_WORD_STRINGS (e.g. ('fish','fishes'), ('body','bodies'),
        ('sign','signs'), ('authority','authorities') ...), which connected ~40 more OET-RV
        words in Mark.
    2026-10-10 Expanded SIMPLE_NOUN_PAIRS and SIMPLE_VERB_SETS from entire OET-RV and OET-LV
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


LAST_MODIFIED_DATE = '2026-10-10' # by RJH
SHORT_PROGRAM_NAME = "connect_OET-RV_words_via_OET-LV"
PROGRAM_NAME = "Connect OET-RV words to OET-LV word numbers"
PROGRAM_VERSION = '1.2.3'
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


SIMPLE_NOUN_PAIRS = (# These are noun pairs (plural, singular) that are likely to match one-to-one from the OET-LV to the OET-RV
#   i.e., there's really no other word for them.
# NOTE: Some of these nouns can also be verbs -- we may need to remove those???
# 'son' causes problems
# Format: (plural_form, singular_form) -- use same form twice for uncountable/invariable nouns
# Sorted alphabetically by plural form, ignoring hyphens and transliteration marks.
    ('abhorrences', 'abhorrence'),
    ('abilities', 'ability'),
    ('abominations', 'abomination'),
    ('abortions', 'abortion'),
    ('abusers', 'abuser'),
    ('accommodations', 'accommodation'),
    ('accounts', 'account'),
    ('accusations', 'accusation'),
    ('accusers', 'accuser'),
    ('achievements', 'achievement'),
    ('acquaintances', 'acquaintance'),
    ('acres', 'acre'),
    ('actions', 'action'),
    ('activities', 'activity'),
    ('acts', 'act'),
    ('adders', 'adder'),
    ('administrators', 'administrator'),
    ('adulterers', 'adulterer'),
    ('adulteresses', 'adulteress'),
    ('adulteries', 'adultery'),
    ('adults', 'adult'),
    ('advantages', 'advantage'),
    ('adversaries', 'adversary'),
    ('adversities', 'adversity'),
    ('advisers', 'adviser'),
    ('advisors', 'advisor'),
    ('affairs', 'affair'),
    ('affections', 'affection'),
    ('afflictions', 'affliction'),
    ('agents', 'agent'),
    ('ages', 'age'),
    ('agonies', 'agony'),
    ('agreements', 'agreement'),
    ('ʼaḩīraˊmites', 'ʼaḩīraˊmite'),
    ('algums', 'algum'),
    ('aliens', 'alien'),
    ('allegories', 'allegory'),
    ('alliances', 'alliance'),
    ('allies', 'ally'),
    ('allocations', 'allocation'),
    ('allotments', 'allotment'),
    ('almonds', 'almond'),
    ('almugs', 'almug'),
    ('aloes', 'aloe'),
    ('altars', 'altar'),
    ('amalekites', 'amalekite'),
    ('ˊamālēqites', 'ˊamālēqite'),
    ('ambassadors', 'ambassador'),
    ('ambitions', 'ambition'),
    ('ambushers', 'ambusher'),
    ('ambushes', 'ambush'),
    ('ˊammōnīs', 'ˊammōnī'),
    ('ammonites', 'ammonite'),
    ('ʼamorīs', 'ʼamorī'),
    ('amorites', 'amorite'),
    ('amounts', 'amount'),
    ('ˊamrāmites', 'ˊamrāmite'),
    ('ancestors', 'ancestor'),
    ('anchors', 'anchor'),
    ('ancients', 'ancient'),
    ('angels', 'angel'),
    ('angers', 'anger'),
    ('animals', 'animal'),
    ('ankles', 'ankle'),
    ('anklets', 'anklet'),
    ('announcers', 'announcer'),
    ('answers', 'answer'),
    ('antiquities', 'antiquity'),
    ('ants', 'ant'),
    ('anxieties', 'anxiety'),
    ('apartments', 'apartment'),
    ('apostasies', 'apostasy'),
    ('apostates', 'apostate'),
    ('appearances', 'appearance'),
    ('appetites', 'appetite'),
    ('apples', 'apple'),
    ('appointments', 'appointment'),
    ('apprentices', 'apprentice'),
    ('approaches', 'approach'),
    ('aprons', 'apron'),
    ('arabians', 'arabian'),
    ('arabs', 'arab'),
    ('arameans', 'aramean'),
    ('archers', 'archer'),
    ('ardites', 'ardite'),
    ('areas', 'area'),
    ('arguments', 'argument'),
    ('arkites', 'arkite'),
    ('armies', 'army'),
    ('armlets', 'armlet'),
    ('armours', 'armour'),
    ('armrests', 'armrest'),
    ('arms', 'arm'),
    ('ʼarōdites', 'ʼarōdite'),
    ('aromas', 'aroma'),
    ('arrangements', 'arrangement'),
    ('arrows', 'arrow'),
    ('articles', 'article'),
    ('arts', 'art'),
    ('ascents', 'ascent'),
    ('ʼashbēlites', 'ʼashbēlite'),
    ('ashdodites', 'ashdodite'),
    ('ʼashdōdites', 'ʼashdōdite'),
    ('asherites', 'asherite'),
    ('ashes', 'ash'),
    ('ashkelonites', 'ashkelonite'),
    ('ashtorets', 'ashtoret'),
    ('ashurites', 'ashurite'),
    ('assarions', 'assarion'),
    ('assassinations', 'assassination'),
    ('assassins', 'assassin'),
    ('assaults', 'assault'),
    ('assemblies', 'assembly'),
    ('assistants', 'assistant'),
    ('assyrians', 'assyrian'),
    ('astrologers', 'astrologer'),
    ('athletes', 'athlete'),
    ('atonements', 'atonement'),
    ('attackers', 'attacker'),
    ('attacks', 'attack'),
    ('attendants', 'attendant'),
    ('attitudes', 'attitude'),
    ('aunts', 'aunt'),
    ('authorities', 'authority'),
    ('authors', 'author'),
    ('avvites', 'avvite'),
    ('axes', 'ax'),
    ('axes', 'axe'),
    ('axles', 'axle'),
    ('ʼāzənītes', 'ʼāzənīte'),
    ("ba'als", "ba'al"),
    ('baals', 'baal'),
    ('babblings', 'babbling'),
    ('babies', 'baby'),
    ('backgrounds', 'background'),
    ('backs', 'back'),
    ('badgers', 'badger'),
    ('baggages', 'baggage'),
    ('bags', 'bag'),
    ('bait', 'bait'),  # invariable/uncountable
    ('bakers', 'baker'),
    ('bakrites', 'bakrite'),
    ('balances', 'balance'),
    ('balancings', 'balancing'),
    ('balls', 'ball'),
    ('bandits', 'bandit'),
    ('bands', 'band'),
    ('banks', 'bank'),
    ('banners', 'banner'),
    ('banquets', 'banquet'),
    ('barbers', 'barber'),
    ('barleys', 'barley'),
    ('barns', 'barn'),
    ('barriers', 'barrier'),
    ('bars', 'bar'),
    ('bases', 'base'),
    ('basins', 'basin'),
    ('basketfuls', 'basketful'),
    ('baskets', 'basket'),
    ('baths', 'bath'),
    ('bats', 'bat'),
    ('battering-rams', 'battering-ram'),
    ('battle-cries', 'battle-cry'),
    ('battlements', 'battlement'),
    ('battles', 'battle'),
    ('beaches', 'beach'),
    ('beams', 'beam'),
    ('beans', 'bean'),
    ('beards', 'beard'),
    ('bearers', 'bearer'),
    ('bears', 'bear'),
    ('beasts', 'beast'),
    ('beatings', 'beating'),
    ('beauties', 'beauty'),
    ('bedrooms', 'bedroom'),
    ('beds', 'bed'),
    ('bəʼērōtites', 'bəʼērōtite'),
    ('bees', 'bee'),
    ('beginnings', 'beginning'),
    ('behaviours', 'behaviour'),
    ('beings', 'being'),
    ('belaites', 'belaite'),
    ('beliefs', 'belief'),
    ('believers', 'believer'),
    ('bellies', 'belly'),
    ('bellows', 'bellow'),
    ('bells', 'bell'),
    ('belongs', 'belong'),
    ('belts', 'belt'),
    ('benches', 'bench'),
    ('benefactors', 'benefactor'),
    ('benefits', 'benefit'),
    ('benyamites', 'benyamite'),
    ('bereavements', 'bereavement'),
    ('bərīˊāahites', 'bərīˊāahite'),
    ('betrayers', 'betrayer'),
    ('betrothals', 'betrothal'),
    ('birds', 'bird'),
    ('births', 'birth'),
    ('biscuits', 'biscuit'),
    ('bits', 'bit'),
    ('bitternesses', 'bitterness'),
    ('blacknesses', 'blackness'),
    ('blacksmiths', 'blacksmith'),
    ('blades', 'blade'),
    ('blankets', 'blanket'),
    ('blasphemers', 'blasphemer'),
    ('blasphemies', 'blasphemy'),
    ('blasts', 'blast'),
    ('blemishes', 'blemish'),
    ('blessings', 'blessing'),
    ('blindnesses', 'blindness'),
    ('blocks', 'block'),
    ('bloods', 'blood'),
    ('blossoms', 'blossom'),
    ('blows', 'blow'),
    ('boards', 'board'),
    ('boars', 'boar'),
    ('boastings', 'boasting'),
    ('boasts', 'boast'),
    ('boats', 'boat'),
    ('bodies', 'body'),
    ('bodyguards', 'bodyguard'),
    ('boils', 'boil'),
    ('bolts', 'bolt'),
    ('bonds', 'bond'),
    ('bones', 'bone'),
    ('books', 'book'),
    ('booths', 'booth'),
    ('borders', 'border'),
    ('bosoms', 'bosom'),
    ('bosses', 'boss'),
    ('bottles', 'bottle'),
    ('boughs', 'bough'),
    ('boundaries', 'boundary'),
    ('bowels', 'bowel'),
    ('bowls', 'bowl'),
    ('bowmen', 'bowman'),
    ('bows', 'bow'),
    ('bowstrings', 'bowstring'),
    ('boxes', 'box'),
    ('boys', 'boy'),
    ('bracelets', 'bracelet'),
    ('braids', 'braid'),
    ('branches', 'branch'),
    ('breaches', 'breach'),
    ('breads', 'bread'),
    ('breakers', 'breaker'),
    ('breaks', 'break'),
    ('breastplates', 'breastplate'),
    ('breasts', 'breast'),
    ('breaths', 'breath'),
    ('brethren', 'brother'),
    ('bribes', 'bribe'),
    ('brick-moulds', 'brick-mould'),
    ('bricks', 'brick'),
    ('bridegrooms', 'bridegroom'),
    ('brides', 'bride'),
    ('bridles', 'bridle'),
    ('briers', 'brier'),
    ('brightnesses', 'brightness'),
    ('broods', 'brood'),
    ('brooks', 'brook'),
    ('brothers', 'brother'),
    ('bruises', 'bruise'),
    ('brushwoods', 'brushwood'),
    ('brutes', 'brute'),
    ('buckets', 'bucket'),
    ('buds', 'bud'),
    ('builders', 'builder'),
    ('buildings', 'building'),
    ('bulbs', 'bulb'),
    ('bulls', 'bull'),
    ('bulrushes', 'bulrush'),
    ('bunches', 'bunch'),
    ('bundles', 'bundle'),
    ('buns', 'bun'),
    ('burden-bearers', 'burden-bearer'),
    ('burdens', 'burden'),
    ('burials', 'burial'),
    ('burners', 'burner'),
    ('burnings', 'burning'),
    ('bushes', 'bush'),
    ('buttocks', 'buttock'),
    ('buyers', 'buyer'),
    ('bywords', 'byword'),
    ('cakes', 'cake'),
    ('calamities', 'calamity'),
    ('calls', 'call'),
    ('calves', 'calf'),
    ('camels', 'camel'),
    ('camps', 'camp'),
    ('canaanites', 'canaanite'),
    ('canals', 'canal'),
    ('canopies', 'canopy'),
    ('capes', 'cape'),
    ('capitals', 'capital'),
    ('caps', 'cap'),
    ('captains', 'captain'),
    ('captives', 'captive'),
    ('captivities', 'captivity'),
    ('caravans', 'caravan'),
    ('carcasses', 'carcass'),
    ('cares', 'care'),
    ('carians', 'carian'),
    ('carmites', 'carmite'),
    ('carousings', 'carousing'),
    ('carpenters', 'carpenter'),
    ('carriers', 'carrier'),
    ('carts', 'cart'),
    ('carvings', 'carving'),
    ('cases', 'case'),
    ('cassias', 'cassia'),
    ('cauldrons', 'cauldron'),
    ('causes', 'cause'),
    ('caves', 'cave'),
    ('cedars', 'cedar'),
    ('celebrations', 'celebration'),
    ('cells', 'cell'),
    ('cemeteries', 'cemetery'),
    ('censers', 'censer'),
    ('centurions', 'centurion'),
    ('ceremonies', 'ceremony'),
    ('cessations', 'cessation'),
    ('chains', 'chain'),
    ('chairs', 'chair'),
    ('chaldeans', 'chaldean'),
    ('challenges', 'challenge'),
    ('chamberlains', 'chamberlain'),
    ('chambers', 'chamber'),
    ('chameleons', 'chameleon'),
    ('champions', 'champion'),
    ('changes', 'change'),
    ('channels', 'channel'),
    ('characters', 'character'),
    ('charges', 'charge'),
    ('charioteers', 'charioteer'),
    ('chariots', 'chariot'),
    ('charmers', 'charmer'),
    ('charms', 'charm'),
    ('cheeks', 'cheek'),
    ('cherubim', 'cherub'),
    ('cherubims', 'cherub'),
    ('cherubs', 'cherub'),
    ('chestplates', 'chestplate'),
    ('chests', 'chest'),
    ('chicks', 'chick'),
    ('chiefs', 'chief'),
    ('childbirths', 'childbirth'),
    ('children', 'child'),
    ('chins', 'chin'),
    ('chisels', 'chisel'),
    ('choices', 'choice'),
    ('choirs', 'choir'),
    ('churches', 'church'),
    ('circles', 'circle'),
    ('circuits', 'circuit'),
    ('circumcisions', 'circumcision'),
    ('circumstances', 'circumstance'),
    ('cisterns', 'cistern'),
    ('cities', 'city'),
    ('citizens', 'citizen'),
    ('claims', 'claim'),
    ('clans', 'clan'),
    ('classes', 'class'),
    ('cleansings', 'cleansing'),
    ('clefts', 'cleft'),
    ('cliffs', 'cliff'),
    ('cloaks', 'cloak'),
    ('clods', 'clod'),
    ('cloths', 'cloth'),
    ('clouds', 'cloud'),
    ('clubs', 'club'),
    ('clusters', 'cluster'),
    ('clutches', 'clutch'),
    ('coals', 'coal'),
    ('coastlands', 'coastland'),
    ('coasts', 'coast'),
    ('coats', 'coat'),
    ('cobras', 'cobra'),
    ('coins', 'coin'),
    ('collars', 'collar'),
    ('collections', 'collection'),
    ('collectors', 'collector'),
    ('colours', 'colour'),
    ('columns', 'column'),
    ('comforters', 'comforter'),
    ('comforts', 'comfort'),
    ('comings', 'coming'),
    ('commanders', 'commander'),
    ('commandments', 'commandment'),
    ('commands', 'command'),
    ('commitments', 'commitment'),
    ('commoners', 'commoner'),
    ('commotions', 'commotion'),
    ('communities', 'community'),
    ('companies', 'company'),
    ('companions', 'companion'),
    ('compassions', 'compassion'),
    ('complaints', 'complaint'),
    ('completenesses', 'completeness'),
    ('components', 'component'),
    ('compositions', 'composition'),
    ('conceits', 'conceit'),
    ('concepts', 'concept'),
    ('concerns', 'concern'),
    ('concubines', 'concubine'),
    ('conditions', 'condition'),
    ('condolences', 'condolence'),
    ('conflicts', 'conflict'),
    ('confusions', 'confusion'),
    ('connections', 'connection'),
    ('conquerors', 'conqueror'),
    ('consciences', 'conscience'),
    ('consequences', 'consequence'),
    ('considerations', 'consideration'),
    ('consolations', 'consolation'),
    ('conspiracies', 'conspiracy'),
    ('conspirators', 'conspirator'),
    ('constellations', 'constellation'),
    ('constraints', 'constraint'),
    ('constructions', 'construction'),
    ('containers', 'container'),
    ('contentions', 'contention'),
    ('contents', 'content'),
    ('contracts', 'contract'),
    ('contributions', 'contribution'),
    ('conversations', 'conversation'),
    ('converts', 'convert'),
    ('convocations', 'convocation'),
    ('convulsions', 'convulsion'),
    ('cooks', 'cook'),
    ('copies', 'copy'),
    ('corals', 'coral'),
    ('cords', 'cord'),
    ('cormorants', 'cormorant'),
    ('corners', 'corner'),
    ('corpses', 'corpse'),
    ('cors', 'cor'),
    ('costs', 'cost'),
    ('couches', 'couch'),
    ('councils', 'council'),
    ('counsellors', 'counsellor'),
    ('counsels', 'counsel'),
    ('countries', 'country'),
    ('countrymen', 'countryman'),
    ('countrysides', 'countryside'),
    ('couples', 'couple'),
    ('courses', 'course'),
    ('court-officials', 'court-official'),
    ('courts', 'court'),
    ('courtyards', 'courtyard'),
    ('cousins', 'cousin'),
    ('covenants', 'covenant'),
    ('coverings', 'covering'),
    ('coveters', 'coveter'),
    ('cowards', 'coward'),
    ('co-workers', 'co-worker'),
    ('cows', 'cow'),
    ('cracks', 'crack'),
    ('crafts', 'craft'),
    ('craftsmen', 'craftsman'),
    ('crags', 'crag'),
    ('crashings', 'crashing'),
    ('cravings', 'craving'),
    ('creators', 'creator'),
    ('creatures', 'creature'),
    ('creditors', 'creditor'),
    ('creeks', 'creek'),
    ('crevices', 'crevice'),
    ('crickets', 'cricket'),
    ('cries', 'cry'),
    ('crimes', 'crime'),
    ('criminals', 'criminal'),
    ('crops', 'crop'),
    ('cross-bars', 'cross-bar'),
    ('crossbars', 'crossbar'),
    ('crossings', 'crossing'),
    ('crowds', 'crowd'),
    ('crowns', 'crown'),
    ('crows', 'crow'),
    ('cruelties', 'cruelty'),
    ('cubits', 'cubit'),
    ('cubs', 'cub'),
    ('cucumbers', 'cucumber'),
    ('cupbearers', 'cupbearer'),
    ('cups', 'cup'),
    ('curds', 'curd'),
    ('currents', 'current'),
    ('curses', 'curse'),
    ('curtains', 'curtain'),
    ('cushion', 'cushion'),  # invariable/uncountable
    ('cushites', 'cushite'),
    ('customs', 'custom'),
    ('cuts', 'cut'),
    ('cutters', 'cutter'),
    ('cuttings', 'cutting'),
    ('cymbals', 'cymbal'),
    ('cypresses', 'cypress'),
    ('daggers', 'dagger'),
    ('dances', 'dance'),
    ('dancings', 'dancing'),
    ('dangers', 'danger'),
    ('danites', 'danite'),
    ('darknesses', 'darkness'),
    ('darts', 'dart'),
    ('dates', 'date'),
    ('daughters', 'daughter'),
    ('daughters-in-law', 'daughter-in-law'),
    ('days', 'day'),
    ('dealings', 'dealing'),
    ('deals', 'deal'),
    ('deaths', 'death'),
    ('debates', 'debate'),
    ('debtors', 'debtor'),
    ('debts', 'debt'),
    ('deceitfulnesses', 'deceitfulness'),
    ('deceits', 'deceit'),
    ('deceivers', 'deceiver'),
    ('deceptions', 'deception'),
    ('decisions', 'decision'),
    ('decks', 'deck'),
    ('declarations', 'declaration'),
    ('decorations', 'decoration'),
    ('decrees', 'decree'),
    ('deeds', 'deed'),
    ('deeps', 'deep'),
    ('deer', 'deer'),  # invariable/uncountable
    ('defects', 'defect'),
    ('defences', 'defence'),
    ('defenders', 'defender'),
    ('defenses', 'defense'),
    ('defilements', 'defilement'),
    ('delicacies', 'delicacy'),
    ('delights', 'delight'),
    ('deliverances', 'deliverance'),
    ('deliverers', 'deliverer'),
    ('demands', 'demand'),
    ('demons', 'demon'),
    ('demonstrations', 'demonstration'),
    ('dens', 'den'),
    ('departures', 'departure'),
    ('deposits', 'deposit'),
    ('depressions', 'depression'),
    ('depths', 'depth'),
    ('deputies', 'deputy'),
    ('derisions', 'derision'),
    ('descendants', 'descendant'),
    ('descendents', 'descendent'),
    ('descriptions', 'description'),
    ('deserts', 'desert'),
    ('designers', 'designer'),
    ('designs', 'design'),
    ('desirablenesses', 'desirableness'),
    ('desires', 'desire'),
    ('desolations', 'desolation'),
    ('destinies', 'destiny'),
    ('destroyers', 'destroyer'),
    ('destructions', 'destruction'),
    ('details', 'detail'),
    ('devices', 'device'),
    ('dews', 'dew'),
    ('differences', 'difference'),
    ('difficulties', 'difficulty'),
    ('dimensions', 'dimension'),
    ('dinners', 'dinner'),
    ('directions', 'direction'),
    ('disappointments', 'disappointment'),
    ('disasters', 'disaster'),
    ('disciples', 'disciple'),
    ('discussions', 'discussion'),
    ('diseases', 'disease'),
    ('dishes', 'dish'),
    ('dismissals', 'dismissal'),
    ('disorders', 'disorder'),
    ('dispersions', 'dispersion'),
    ('disputes', 'dispute'),
    ('dissensions', 'dissension'),
    ('distances', 'distance'),
    ('distinctions', 'distinction'),
    ('distresses', 'distress'),
    ('distributions', 'distribution'),
    ('districts', 'district'),
    ('disturbances', 'disturbance'),
    ('ditches', 'ditch'),
    ('divinations', 'divination'),
    ('diviners', 'diviner'),
    ('divisions', 'division'),
    ('doctors', 'doctor'),
    ('doctrines', 'doctrine'),
    ('documents', 'document'),
    ('doers', 'doer'),
    ('does', 'doe'),
    ('dogs', 'dog'),
    ('doings', 'doing'),
    ('dolphins', 'dolphin'),
    ('domains', 'domain'),
    ('dominions', 'dominion'),
    ('donations', 'donation'),
    ('donkeys', 'donkey'),
    ('doorkeepers', 'doorkeeper'),
    ('doorposts', 'doorpost'),
    ('doors', 'door'),
    ('doorways', 'doorway'),
    ('doubts', 'doubt'),
    ('doughs', 'dough'),
    ('doves', 'dove'),
    ('downpours', 'downpour'),
    ('dowries', 'dowry'),
    ('drachmas', 'drachma'),
    ('dragons', 'dragon'),
    ('drawers', 'drawer'),
    ('dreads', 'dread'),
    ('dreamers', 'dreamer'),
    ('dreams', 'dream'),
    ('dresses', 'dress'),
    ('drinks', 'drink'),
    ('drivers', 'driver'),
    ('drops', 'drop'),
    ('drosses', 'dross'),
    ('droughts', 'drought'),
    ('drums', 'drum'),
    ('drunkards', 'drunkard'),
    ('drunkennesses', 'drunkenness'),
    ('drunks', 'drunk'),
    ('dues', 'due'),
    ('dungs', 'dung'),
    ('dusts', 'dust'),
    ('duties', 'duty'),
    ('dwellers', 'dweller'),
    ('dwelling-places', 'dwelling-place'),
    ('dwellings', 'dwelling'),
    ('dyes', 'dye'),
    ('eagles', 'eagle'),
    ('earnings', 'earning'),
    ('earrings', 'earring'),
    ('ears', 'ear'),
    ('earthquakes', 'earthquake'),
    ('earths', 'earth'),
    ('edges', 'edge'),
    ('edicts', 'edict'),
    ('edomites', 'edomite'),
    ('ʼedōmites', 'ʼedōmite'),
    ('effects', 'effect'),
    ('efforts', 'effort'),
    ('efrayimites', 'efrayimite'),
    ('eggs', 'egg'),
    ('egyptians', 'egyptian'),
    ('elders', 'elder'),
    ('elephants', 'elephant'),
    ('elms', 'elm'),
    ('embalmings', 'embalming'),
    ('embroiderers', 'embroiderer'),
    ('emeralds', 'emerald'),
    ('emissions', 'emission'),
    ('emotions', 'emotion'),
    ('empires', 'empire'),
    ('encampments', 'encampment'),
    ('enchanters', 'enchanter'),
    ('enchantments', 'enchantment'),
    ('enclosures', 'enclosure'),
    ('encounters', 'encounter'),
    ('endings', 'ending'),
    ('ends', 'end'),
    ('endurances', 'endurance'),
    ('enemies', 'enemy'),
    ('engines', 'engine'),
    ('engravings', 'engraving'),
    ('enmities', 'enmity'),
    ('enterings', 'entering'),
    ('enticements', 'enticement'),
    ('entrances', 'entrance'),
    ('entreaties', 'entreaty'),
    ('envies', 'envy'),
    ('envoys', 'envoy'),
    ('epistles', 'epistle'),
    ('ˊeqrōnites', 'ˊeqrōnite'),
    ('equals', 'equal'),
    ('equipments', 'equipment'),
    ('eranites', 'eranite'),
    ('eras', 'era'),
    ('erites', 'erite'),
    ('errors', 'error'),
    ('escapees', 'escapee'),
    ('escapes', 'escape'),
    ('eshtaolites', 'eshtaolite'),
    ('ethiopians', 'ethiopian'),
    ('eunuchs', 'eunuch'),
    ('evenings', 'evening'),
    ('events', 'event'),
    ('everlastingnesses', 'everlastingness'),
    ('evictions', 'eviction'),
    ('evil-doers', 'evil-doer'),
    ('evildoers', 'evildoer'),
    ('evils', 'evil'),
    ('ewe-lambs', 'ewe-lamb'),
    ('ewes', 'ewe'),
    ('exaltations', 'exaltation'),
    ('examples', 'example'),
    ('excellences', 'excellence'),
    ('exceptions', 'exception'),
    ('excuses', 'excuse'),
    ('executioners', 'executioner'),
    ('exhortations', 'exhortation'),
    ('exiles', 'exile'),
    ('exits', 'exit'),
    ('exorcists', 'exorcist'),
    ('expanses', 'expanse'),
    ('expectations', 'expectation'),
    ('expenses', 'expense'),
    ('experiences', 'experience'),
    ('experts', 'expert'),
    ('exploits', 'exploit'),
    ('extensions', 'extension'),
    ('extortions', 'extortion'),
    ('extremities', 'extremity'),
    ('eyes', 'eye'),
    ('ʼēylōnites', 'ʼēylōnite'),
    ('ezrites', 'ezrite'),
    ('fabrics', 'fabric'),
    ('faces', 'face'),
    ('facts', 'fact'),
    ('failings', 'failing'),
    ('faith', 'faith'),  # invariable/uncountable
    ('faithfulnesses', 'faithfulness'),
    ('falcons', 'falcon'),
    ('falsehoods', 'falsehood'),
    ('families', 'family'),
    ('famines', 'famine'),
    ('farewells', 'farewell'),
    ('farmers', 'farmer'),
    ('farms', 'farm'),
    ('far-ohs', 'far-oh'),
    ('fastings', 'fasting'),
    ('fasts', 'fast'),
    ('fathers', 'father'),
    ('fatlings', 'fatling'),
    ('fatnesses', 'fatness'),
    ('fats', 'fat'),
    ('faults', 'fault'),
    ('favourites', 'favourite'),
    ('favours', 'favour'),
    ('fawns', 'fawn'),
    ('fears', 'fear'),
    ('feastings', 'feasting'),
    ('feasts', 'feast'),
    ('feathers', 'feather'),
    ('feelings', 'feeling'),
    ('fees', 'fee'),
    ('feet', 'foot'),
    ('fellow-citizens', 'fellow-citizen'),
    ('fellow-partakers', 'fellow-partaker'),
    ('fellow-prisoners', 'fellow-prisoner'),
    ('fellows', 'fellow'),
    ('fellow-slaves', 'fellow-slave'),
    ('fellow-workers', 'fellow-worker'),
    ('females', 'female'),
    ('fences', 'fence'),
    ('festivals', 'festival'),
    ('festivities', 'festivity'),
    ('fetters', 'fetter'),
    ('fevers', 'fever'),
    ('fields', 'field'),
    ('fifths', 'fifth'),
    ('fifties', 'fifty'),
    ('fights', 'fight'),
    ('figs', 'fig'),
    ('figures', 'figure'),
    ('fines', 'fine'),
    ('fingers', 'finger'),
    ('fins', 'fin'),
    ('fires', 'fire'),
    ('firs', 'fir'),
    ('firstborns', 'firstborn'),
    ('first-fruits', 'first-fruit'),
    ('fish', 'fish'),  # invariable/uncountable
    ('fishes', 'fish'),
    ('fists', 'fist'),
    ('flames', 'flame'),
    ('flanks', 'flank'),
    ('flashes', 'flash'),
    ('flatteries', 'flattery'),
    ('flaws', 'flaw'),
    ('flaxes', 'flax'),
    ('fleeces', 'fleece'),
    ('fleshes', 'flesh'),
    ('flies', 'fly'),
    ('flints', 'flint'),
    ('flocks', 'flock'),
    ('floggings', 'flogging'),
    ('floods', 'flood'),
    ('floors', 'floor'),
    ('flowers', 'flower'),
    ('flutes', 'flute'),
    ('foes', 'foe'),
    ('folds', 'fold'),
    ('follies', 'folly'),
    ('followers', 'follower'),
    ('foods', 'food'),
    ('fools', 'fool'),
    ('footprints', 'footprint'),
    ('forces', 'force'),
    ('fords', 'ford'),
    ('forefathers', 'forefather'),
    ('foreheads', 'forehead'),
    ('foreigners', 'foreigner'),
    ('foremen', 'foreman'),
    ('forerunners', 'forerunner'),
    ('foreskins', 'foreskin'),
    ('forests', 'forest'),
    ('forgivenesses', 'forgiveness'),
    ('forks', 'fork'),
    ('forms', 'form'),
    ('fornicators', 'fornicator'),
    ('fortifications', 'fortification'),
    ('fortresses', 'fortress'),
    ('forts', 'fort'),
    ('fortunes', 'fortune'),
    ('foster-fathers', 'foster-father'),
    ('foundations', 'foundation'),
    ('fountains', 'fountain'),
    ('fowlers', 'fowler'),
    ('foxes', 'fox'),
    ('fractures', 'fracture'),
    ('fragments', 'fragment'),
    ('fragrances', 'fragrance'),
    ('frames', 'frame'),
    ('frauds', 'fraud'),
    ('freedmen', 'freedman'),
    ('freedoms', 'freedom'),
    ('freemen', 'freeman'),
    ('frictions', 'friction'),
    ('friends', 'friend'),
    ('frogs', 'frog'),
    ('fronts', 'front'),
    ('fruits', 'fruit'),
    ('fugitives', 'fugitive'),
    ('funds', 'fund'),
    ('funerals', 'funeral'),
    ('furies', 'fury'),
    ('furrows', 'furrow'),
    ('futilities', 'futility'),
    ('futures', 'future'),
    ('gādīs', 'gādī'),
    ('gadites', 'gadite'),
    ('gains', 'gain'),
    ('galileans', 'galilean'),
    ('galleries', 'gallery'),
    ('gangs', 'gang'),
    ('gaps', 'gap'),
    ('gardens', 'garden'),
    ('garlands', 'garland'),
    ('garlics', 'garlic'),
    ('garments', 'garment'),
    ('garrisons', 'garrison'),
    ('gatekeepers', 'gatekeeper'),
    ('gates', 'gate'),
    ('gateways', 'gateway'),
    ('gatherers', 'gatherer'),
    ('gatherings', 'gathering'),
    ('gazelles', 'gazelle'),
    ('gazites', 'gazite'),
    ('geckos', 'gecko'),
    ('gems', 'gem'),
    ('gemstones', 'gemstone'),
    ('genealogies', 'genealogy'),
    ('generals', 'general'),
    ('generations', 'generation'),
    ('gerahs', 'gerah'),
    ('gērəshōnites', 'gērəshōnite'),
    ('gershonites', 'gershonite'),
    ('geshurites', 'geshurite'),
    ('gəshūrites', 'gəshūrite'),
    ('giants', 'giant'),
    ('gibeonites', 'gibeonite'),
    ('gifts', 'gift'),
    ('gilˊādites', 'gilˊādite'),
    ('gileadites', 'gileadite'),
    ('girgashites', 'girgashite'),
    ('girgāshiys', 'girgāshiy'),
    ('girls', 'girl'),
    ('gittites', 'gittite'),
    ('gittiys', 'gittiy'),
    ('givers', 'giver'),
    ('givings', 'giving'),
    ('giⱱlīs', 'giⱱlī'),
    ('giⱱˊōnites', 'giⱱˊōnite'),
    ('gladnesses', 'gladness'),
    ('gleams', 'gleam'),
    ('gleanings', 'gleaning'),
    ('glooms', 'gloom'),
    ('glories', 'glory'),
    ('gluttons', 'glutton'),
    ('gnats', 'gnat'),
    ('goads', 'goad'),
    ('goals', 'goal'),
    ('goats', 'goat'),
    ('goblets', 'goblet'),
    ('gods', 'god'),
    ('goings', 'going'),
    ('golds', 'gold'),
    ('goldsmiths', 'goldsmith'),
    ('goodbyes', 'goodbye'),
    ('good-for-nothings', 'good-for-nothing'),
    ('goods', 'good'),
    ('gospels', 'gospel'),
    ('gossips', 'gossip'),
    ('governments', 'government'),
    ('governors', 'governor'),
    ('grace', 'grace'),  # invariable/uncountable
    ('grains', 'grain'),
    ('granaries', 'granary'),
    ('grandsons', 'grandson'),
    ('grape-pickers', 'grape-picker'),
    ('grapes', 'grape'),
    ('grapevines', 'grapevine'),
    ('grasses', 'grass'),
    ('grasshoppers', 'grasshopper'),
    ('gratifications', 'gratification'),
    ('graves', 'grave'),
    ('greatnesses', 'greatness'),
    ('greed', 'greed'),  # invariable/uncountable
    ('greeks', 'greek'),
    ('greetings', 'greeting'),
    ('groanings', 'groaning'),
    ('grooms', 'groom'),
    ('grounds', 'ground'),
    ('groups', 'group'),
    ('groves', 'grove'),
    ('growths', 'growth'),
    ('grumblings', 'grumbling'),
    ('guarantees', 'guarantee'),
    ('guardians', 'guardian'),
    ('guards', 'guard'),
    ('guests', 'guest'),
    ('guidances', 'guidance'),
    ('guides', 'guide'),
    ('guilts', 'guilt'),
    ('gūnītes', 'gūnīte'),
    ('guts', 'gut'),
    ('guys', 'guy'),
    ('habitations', 'habitation'),
    ('habits', 'habit'),
    ('ḩaggittes', 'ḩaggitte'),
    ('hagrites', 'hagrite'),
    ('hails', 'hail'),
    ('hairs', 'hair'),
    ('half-sisters', 'half-sister'),
    ('half-tribes', 'half-tribe'),
    ('halls', 'hall'),
    ('halves', 'half'),
    ('hamlet-dwellers', 'hamlet-dweller'),
    ('hammers', 'hammer'),
    ('ḩāmūlites', 'ḩāmūlite'),
    ('handbreadths', 'handbreadth'),
    ('handfuls', 'handful'),
    ('handkerchiefs', 'handkerchief'),
    ('handles', 'handle'),
    ('handmaidens', 'handmaiden'),
    ('handmaids', 'handmaid'),
    ('hands', 'hand'),
    ('ḩₐnōkites', 'ḩₐnōkite'),
    ('happiness', 'happiness'),  # invariable/uncountable
    ('harbours', 'harbour'),
    ('hardships', 'hardship'),
    ('hares', 'hare'),
    ('harnesses', 'harness'),
    ('harpoons', 'harpoon'),
    ('harps', 'harp'),
    ('harvesters', 'harvester'),
    ('harvests', 'harvest'),
    ('haters', 'hater'),
    ('hatreds', 'hatred'),
    ('hawks', 'hawk'),
    ('headbands', 'headband'),
    ('heads', 'head'),
    ('healers', 'healer'),
    ('healings', 'healing'),
    ('healths', 'health'),
    ('heaps', 'heap'),
    ('hearers', 'hearer'),
    ('hearths', 'hearth'),
    ('hearts', 'heart'),
    ('heats', 'heat'),
    ('heavens', 'heaven'),
    ('hebrews', 'hebrew'),
    ('hedgehogs', 'hedgehog'),
    ('heels', 'heel'),
    ('ḩēferites', 'ḩēferite'),
    ('he-goats', 'he-goat'),
    ('heifers', 'heifer'),
    ('heights', 'height'),
    ('heirs', 'heir'),
    ('helekites', 'helekite'),
    ('hellaʸns', 'hellaʸn'),
    ('helmets', 'helmet'),
    ('helpers', 'helper'),
    ('helps', 'help'),
    ('herbs', 'herb'),
    ('herders', 'herder'),
    ('herds', 'herd'),
    ('herdsmen', 'herdsman'),
    ('ḩermōns', 'ḩermōn'),
    ('ḩeʦrōnites', 'ḩeʦrōnite'),
    ('ḩeⱱerites', 'ḩeⱱerite'),
    ('ḩeⱱrōnites', 'ḩeⱱrōnite'),
    ('hides', 'hide'),
    ('highways', 'highway'),
    ('hills', 'hill'),
    ('hilltops', 'hilltop'),
    ('hindrances', 'hindrance'),
    ('hinges', 'hinge'),
    ('hips', 'hip'),
    ('hissings', 'hissing'),
    ('histories', 'history'),
    ('hittites', 'hittite'),
    ('ḩittiys', 'ḩittiy'),
    ('ḩiūīs', 'ḩiūī'),
    ('hivites', 'hivite'),
    ('holes', 'hole'),
    ('holidays', 'holiday'),
    ('holies', 'holy'),
    ('holinesses', 'holiness'),
    ('hollows', 'hollow'),
    ('homelessnesses', 'homelessness'),
    ('homers', 'homer'),
    ('homes', 'home'),
    ('honey', 'honey'),  # invariable/uncountable
    ('honeycombs', 'honeycomb'),
    ('honours', 'honour'),
    ('hooks', 'hook'),
    ('hoopoes', 'hoopoe'),
    ('hooves', 'hoof'),
    ('hopes', 'hope'),
    ('hordes', 'horde'),
    ('horites', 'horite'),
    ('ḩorītes', 'ḩorīte'),
    ('hornets', 'hornet'),
    ('horns', 'horn'),
    ('horsemen', 'horseman'),
    ('horses', 'horse'),
    ('hostages', 'hostage'),
    ('hours', 'hour'),
    ('households', 'household'),
    ('houses', 'house'),
    ('house-servants', 'house-servant'),
    ('housetops', 'housetop'),
    ('humans', 'human'),
    ('humps', 'hump'),
    ('hundreds', 'hundred'),
    ('hunters', 'hunter'),
    ('huphamites', 'huphamite'),
    ('husbands', 'husband'),
    ('huts', 'hut'),
    ('hyenas', 'hyena'),
    ('hymns', 'hymn'),
    ('hypocrisies', 'hypocrisy'),
    ('hypocrites', 'hypocrite'),
    ('ideas', 'idea'),
    ('idolaters', 'idolater'),
    ('idolatries', 'idolatry'),
    ('idols', 'idol'),
    ('iezerites', 'iezerite'),
    ('ignominies', 'ignominy'),
    ('ignorances', 'ignorance'),
    ('illnesses', 'illness'),
    ('illustrations', 'illustration'),
    ('images', 'image'),
    ('imaginations', 'imagination'),
    ('imaginings', 'imagining'),
    ('immoralities', 'immorality'),
    ('immortals', 'immortal'),
    ('immunities', 'immunity'),
    ('imperfections', 'imperfection'),
    ('impieties', 'impiety'),
    ('imprisonments', 'imprisonment'),
    ('impulses', 'impulse'),
    ('impurities', 'impurity'),
    ('incenses', 'incense'),
    ('indications', 'indication'),
    ('individuals', 'individual'),
    ('infants', 'infant'),
    ('inflictions', 'infliction'),
    ('inhabitants', 'inhabitant'),
    ('inheritances', 'inheritance'),
    ('iniquities', 'iniquity'),
    ('initiatives', 'initiative'),
    ('injunctions', 'injunction'),
    ('injustices', 'injustice'),
    ('ink', 'ink'),  # invariable/uncountable
    ('inquirers', 'inquirer'),
    ('insects', 'insect'),
    ('insides', 'inside'),
    ('inspectors', 'inspector'),
    ('instructions', 'instruction'),
    ('instructors', 'instructor'),
    ('instruments', 'instrument'),
    ('insulters', 'insulter'),
    ('insults', 'insult'),
    ('insurrections', 'insurrection'),
    ('intentions', 'intention'),
    ('interests', 'interest'),
    ('interpretations', 'interpretation'),
    ('intervals', 'interval'),
    ('intrigues', 'intrigue'),
    ('invaders', 'invader'),
    ('inventions', 'invention'),
    ('inventors', 'inventor'),
    ('investments', 'investment'),
    ('invitations', 'invitation'),
    ('irons', 'iron'),
    ('islands', 'island'),
    ('israelis', 'israeli'),
    ('israelites', 'israelite'),
    ('issues', 'issue'),
    ('items', 'item'),
    ('ivories', 'ivory'),
    ('izharites', 'izharite'),
    ('jackets', 'jacket'),
    ('jahzeelites', 'jahzeelite'),
    ('jails', 'jail'),
    ('jaminites', 'jaminite'),
    ('japhletites', 'japhletite'),
    ('jars', 'jar'),
    ('jashubites', 'jashubite'),
    ('jaws', 'jaw'),
    ('jealousies', 'jealousy'),
    ('jebusites', 'jebusite'),
    ('jerahmeelites', 'jerahmeelite'),
    ('jewels', 'jewel'),
    ('jews', 'jew'),
    ('jobs', 'job'),
    ('joinings', 'joining'),
    ('joints', 'joint'),
    ('jokes', 'joke'),
    ('journeys', 'journey'),
    ('joys', 'joy'),
    ('judeans', 'judean'),
    ('judgements', 'judgement'),
    ('judges', 'judge'),
    ('jugs', 'jug'),
    ('justices', 'justice'),
    ('kadmonites', 'kadmonite'),
    ('kanaanites', 'kanaanite'),
    ('keepers', 'keeper'),
    ('kənaˊₐnīs', 'kənaˊₐnī'),
    ('kenites', 'kenite'),
    ('kenizzites', 'kenizzite'),
    ('kerethites', 'kerethite'),
    ('kettles', 'kettle'),
    ('keys', 'key'),
    ('kidneys', 'kidney'),
    ('kids', 'kid'),
    ('killers', 'killer'),
    ('killings', 'killing'),
    ('kilograms', 'kilogram'),
    ('kilometres', 'kilometre'),
    ('kilos', 'kilo'),
    ('kindnesses', 'kindness'),
    ('kinds', 'kind'),
    ('kingdoms', 'kingdom'),
    ('kings', 'king'),
    ('kinsman-redeemers', 'kinsman-redeemer'),
    ('kinsmen', 'kinsman'),
    ('kinspeoples', 'kinspeople'),
    ('kisses', 'kiss'),
    ('kites', 'kite'),
    ('knees', 'knee'),
    ('knives', 'knife'),
    ('knots', 'knot'),
    ('knowledges', 'knowledge'),
    ('kohatites', 'kohatite'),
    ('kushites', 'kushite'),
    ('kūshiys', 'kūshiy'),
    ('labourers', 'labourer'),
    ('labour-pains', 'labour-pain'),
    ('labours', 'labour'),
    ('ladders', 'ladder'),
    ('ladies', 'lady'),
    ('lads', 'lad'),
    ('lairs', 'lair'),
    ('lakes', 'lake'),
    ('lambs', 'lamb'),
    ('lamentations', 'lamentation'),
    ('lamps', 'lamp'),
    ('lampstands', 'lampstand'),
    ('lances', 'lance'),
    ('landowners', 'landowner'),
    ('lands', 'land'),
    ('languages', 'language'),
    ('laps', 'lap'),
    ('lattices', 'lattice'),
    ('lavers', 'laver'),
    ('lawbreakers', 'lawbreaker'),
    ('laws', 'law'),
    ('lawsuits', 'lawsuit'),
    ('lawyers', 'lawyer'),
    ('layers', 'layer'),
    ('lazinesses', 'laziness'),
    ('leaders', 'leader'),
    ('leaks', 'leak'),
    ('leather', 'leather'),  # invariable/uncountable
    ('leaves', 'leaf'),
    ('ledges', 'ledge'),
    ('leeks', 'leek'),
    ('left-handers', 'left-hander'),
    ('left-overs', 'left-over'),
    ('legs', 'leg'),
    ('lengths', 'length'),
    ('lentils', 'lentil'),
    ('leopards', 'leopard'),
    ('lepers', 'leper'),
    ('leptons', 'lepton'),
    ('letters', 'letter'),
    ('levels', 'level'),
    ('levites', 'levite'),
    ('lēviyyiys', 'lēviyyiy'),
    ('liars', 'liar'),
    ('libations', 'libation'),
    ('lies', 'lie'),
    ('lifestyles', 'lifestyle'),
    ('lifetimes', 'lifetime'),
    ('lightnings', 'lightning'),
    ('lights', 'light'),
    ('likenesses', 'likeness'),
    ('likes', 'like'),
    ('lilies', 'lily'),
    ('limbs', 'limb'),
    ('limits', 'limit'),
    ('linens', 'linen'),
    ('lines', 'line'),
    ('lintels', 'lintel'),
    ('lionesses', 'lioness'),
    ('lions', 'lion'),
    ('lips', 'lip'),
    ('liquids', 'liquid'),
    ('listeners', 'listener'),
    ('lists', 'list'),
    ('litres', 'litre'),
    ('litters', 'litter'),
    ('liver', 'liver'),  # invariable/uncountable
    ('lives', 'life'),
    ('livestocks', 'livestock'),
    ('liⱱnītes', 'liⱱnīte'),
    ('lizards', 'lizard'),
    ('loads', 'load'),
    ('loans', 'loan'),
    ('loaves', 'loaf'),
    ('locations', 'location'),
    ('locks', 'lock'),
    ('locusts', 'locust'),
    ('logs', 'log'),
    ('loins', 'loin'),
    ('longings', 'longing'),
    ('looks', 'look'),
    ('lords', 'lord'),
    ('losses', 'loss'),
    ('lotions', 'lotion'),
    ('lots', 'lot'),
    ('lovers', 'lover'),
    ('loves', 'love'),
    ('lowlands', 'lowland'),
    ('loyalties', 'loyalty'),
    ('luminaries', 'luminary'),
    ('lumps', 'lump'),
    ('lusts', 'lust'),
    ('lutes', 'lute'),
    ('luxuries', 'luxury'),
    ('lyings', 'lying'),
    ('lyres', 'lyre'),
    ('maacatites', 'maacatite'),
    ('maˊₐkāhites', 'maˊₐkāhite'),
    ('maˊₐkātīs', 'maˊₐkātī'),
    ('macedonians', 'macedonian'),
    ('machines', 'machine'),
    ('madmen', 'madman'),
    ('madnesses', 'madness'),
    ('maggots', 'maggot'),
    ('magicians', 'magician'),
    ('maḩlītes', 'maḩlīte'),
    ('maids', 'maid'),
    ('maidservants', 'maidservant'),
    ('majesties', 'majesty'),
    ('makers', 'maker'),
    ('mākīrites', 'mākīrite'),
    ('males', 'male'),
    ('managers', 'manager'),
    ('mānaḩatites', 'mānaḩatite'),
    ('manassites', 'manassite'),
    ('mandrakes', 'mandrake'),
    ('manifestations', 'manifestation'),
    ('manners', 'manner'),
    ('mantles', 'mantle'),
    ('mares', 'mare'),
    ('markers', 'marker'),
    ('marketplaces', 'marketplace'),
    ('markets', 'market'),
    ('marks', 'mark'),
    ('marrows', 'marrow'),
    ('marshes', 'marsh'),
    ('marvels', 'marvel'),
    ('masters', 'master'),
    ('masterships', 'mastership'),
    ('materials', 'material'),
    ('mates', 'mate'),
    ('mats', 'mat'),
    ('matters', 'matter'),
    ('mattocks', 'mattock'),
    ('meadows', 'meadow'),
    ('meals', 'meal'),
    ('mealtimes', 'mealtime'),
    ('measurements', 'measurement'),
    ('measures', 'measure'),
    ('measuring-lines', 'measuring-line'),
    ('meats', 'meat'),
    ('medes', 'mede'),
    ('medicines', 'medicine'),
    ('mediums', 'medium'),
    ('meetings', 'meeting'),
    ('melodies', 'melody'),
    ('members', 'member'),
    ('memorials', 'memorial'),
    ('men', 'man'),
    ('menstruations', 'menstruation'),
    ('mentors', 'mentor'),
    ('menuchites', 'menuchite'),
    ('merarites', 'merarite'),
    ('mərārītes', 'mərārīte'),
    ('merchandises', 'merchandise'),
    ('merchants', 'merchant'),
    ('mercies', 'mercy'),
    ('messages', 'message'),
    ('messengers', 'messenger'),
    ('messiahs', 'messiah'),
    ('metalsmiths', 'metalsmith'),
    ('metres', 'metre'),
    ('mice', 'mouse'),
    ('midianites', 'midianite'),
    ('midwives', 'midwife'),
    ('midyanites', 'midyanite'),
    ('midyānites', 'midyānite'),
    ('miles', 'mile'),
    ('milk', 'milk'),  # invariable/uncountable
    ('millions', 'million'),
    ('millstones', 'millstone'),
    ('minas', 'mina'),
    ('minds', 'mind'),
    ('mines', 'mine'),
    ('ministers', 'minister'),
    ('ministries', 'ministry'),
    ('miracles', 'miracle'),
    ('mirrors', 'mirror'),
    ('miscarriages', 'miscarriage'),
    ('miseries', 'misery'),
    ('misfortunes', 'misfortune'),
    ('mishraites', 'mishraite'),
    ('missiles', 'missile'),
    ('missionaries', 'missionary'),
    ('missions', 'mission'),
    ('mistakes', 'mistake'),
    ('mists', 'mist'),
    ('mnas', 'mna'),
    ('moabites', 'moabite'),
    ('moavites', 'moavite'),
    ('mōʼāⱱites', 'mōʼāⱱite'),
    ('mockeries', 'mockery'),
    ('mockers', 'mocker'),
    ('mockings', 'mocking'),
    ('models', 'model'),
    ('molds', 'mold'),
    ('moments', 'moment'),
    ('monsters', 'monster'),
    ('months', 'month'),
    ('monuments', 'monument'),
    ('moons', 'moon'),
    ('mornings', 'morning'),
    ('mortals', 'mortal'),
    ('mothers', 'mother'),
    ('mothers-in-law', 'mother-in-law'),
    ('moths', 'moth'),
    ('mounds', 'mound'),
    ('mountains', 'mountain'),
    ('mountings', 'mounting'),
    ('mounts', 'mount'),
    ('mourners', 'mourner'),
    ('mournings', 'mourning'),
    ('mouths', 'mouth'),
    ('mulberries', 'mulberry'),
    ('mules', 'mule'),
    ('multitudes', 'multitude'),
    ('murderers', 'murderer'),
    ('murders', 'murder'),
    ('murmurings', 'murmuring'),
    ('muscles', 'muscle'),
    ('mūshiytes', 'mūshiyte'),
    ('musicians', 'musician'),
    ('myriads', 'myriad'),
    ('mysteries', 'mystery'),
    ('naamanites', 'naamanite'),
    ('nails', 'nail'),
    ('nakednesses', 'nakedness'),
    ('names', 'name'),
    ('narratives', 'narrative'),
    ('nationalities', 'nationality'),
    ('nations', 'nation'),
    ('natives', 'native'),
    ('natures', 'nature'),
    ('nazarites', 'nazarite'),
    ('nazirites', 'nazirite'),
    ('necklaces', 'necklace'),
    ('necks', 'neck'),
    ('necromancers', 'necromancer'),
    ('needs', 'need'),
    ('neighbours', 'neighbour'),
    ('neighings', 'neighing'),
    ('nephews', 'nephew'),
    ('nests', 'nest'),
    ('nəţofātīs', 'nəţofātī'),
    ('netofatites', 'netofatite'),
    ('nets', 'net'),
    ('nettles', 'nettle'),
    ('networks', 'network'),
    ('news', 'news'),  # invariable/uncountable
    ('nights', 'night'),
    ('nipples', 'nipple'),
    ('nobles', 'noble'),
    ('nobodies', 'nobody'),
    ('noises', 'noise'),
    ('non-believers', 'non-believer'),
    ('non-gods', 'non-god'),
    ('non-jews', 'non-jew'),
    ('noons', 'noon'),
    ('noontides', 'noontide'),
    ('northerners', 'northerner'),
    ('noses', 'nose'),
    ('notes', 'note'),
    ('numbers', 'number'),
    ('nurses', 'nurse'),
    ('nuts', 'nut'),
    ('oaks', 'oak'),
    ('oars', 'oar'),
    ('oaths', 'oath'),
    ('objections', 'objection'),
    ('objects', 'object'),
    ('oblations', 'oblation'),
    ('obligations', 'obligation'),
    ('observances', 'observance'),
    ('obstacles', 'obstacle'),
    ('occasions', 'occasion'),
    ('occupations', 'occupation'),
    ('oceans', 'ocean'),
    ('odours', 'odour'),
    ('offenses', 'offense'),
    ('offerings', 'offering'),
    ('officers', 'officer'),
    ('offices', 'office'),
    ('officials', 'official'),
    ('offshoots', 'offshoot'),
    ('offspring', 'offspring'),  # invariable singular/plural
    ('offsprings', 'offspring'),
    ('oils', 'oil'),
    ('ointments', 'ointment'),
    ('olives', 'olive'),
    ('ˊomers', 'ˊomer'),
    ('openings', 'opening'),
    ('opinions', 'opinion'),
    ('opponents', 'opponent'),
    ('opportunities', 'opportunity'),
    ('oppositions', 'opposition'),
    ('oppressions', 'oppression'),
    ('oppressors', 'oppressor'),
    ('options', 'option'),
    ('oracles', 'oracle'),
    ('orchards', 'orchard'),
    ('orders', 'order'),
    ('ordinances', 'ordinance'),
    ('organs', 'organ'),
    ('origins', 'origin'),
    ('ornaments', 'ornament'),
    ('orphans', 'orphan'),
    ('ospreys', 'osprey'),
    ('ostriches', 'ostrich'),
    ('outcasts', 'outcast'),
    ('outcries', 'outcry'),
    ('outsiders', 'outsider'),
    ('outskirts', 'outskirt'),
    ('ovens', 'oven'),
    ('overflowings', 'overflowing'),
    ('overseers', 'overseer'),
    ('oversights', 'oversight'),
    ('owls', 'owl'),
    ('owners', 'owner'),
    ('oxen', 'ox'),
    ('paddocks', 'paddock'),
    ('pains', 'pain'),
    ('pairs', 'pair'),
    ('palaces', 'palace'),
    ('pallets', 'pallet'),
    ('pallūʼites', 'pallūʼite'),
    ('palms', 'palm'),
    ('panels', 'panel'),
    ('pans', 'pan'),
    ('papers', 'paper'),
    ('parables', 'parable'),
    ('pāraşns', 'pāraşn'),
    ('parents', 'parent'),
    ('partakers', 'partaker'),
    ('particulars', 'particular'),
    ('parties', 'party'),
    ('partners', 'partner'),
    ('parts', 'part'),
    ('passages', 'passage'),
    ('passers-by', 'passer-by'),
    ('passes', 'pass'),
    ('passions', 'passion'),
    ('passovers', 'passover'),
    ('pasturelands', 'pastureland'),
    ('pastures', 'pasture'),
    ('paths', 'path'),
    ('pathways', 'pathway'),
    ('patriarchs', 'patriarch'),
    ('patterns', 'pattern'),
    ('payments', 'payment'),
    ('peace', 'peace'),  # invariable/uncountable
    ('peaks', 'peak'),
    ('pearls', 'pearl'),
    ('pegs', 'peg'),
    ('pelethites', 'pelethite'),
    ('penalties', 'penalty'),
    ('pens', 'pen'),
    ('people', 'person'),
    ('peoples', 'people'),
    ('percentages', 'percentage'),
    ('pereʦites', 'pereʦite'),
    ('perfections', 'perfection'),
    ('perfumers', 'perfumer'),
    ('perfumes', 'perfume'),
    ('perils', 'peril'),
    ('periods', 'period'),
    ('pərizzīs', 'pərizzī'),
    ('perizzites', 'perizzite'),
    ('perpetuities', 'perpetuity'),
    ('persecutions', 'persecution'),
    ('persecutors', 'persecutor'),
    ('persians', 'persian'),
    ('persons', 'person'),
    ('persuasions', 'persuasion'),
    ('perversions', 'perversion'),
    ('perversities', 'perversity'),
    ('pestilences', 'pestilence'),
    ('petitions', 'petition'),
    ('phalanxes', 'phalanx'),
    ('pharaohs', 'pharaoh'),
    ('pharisees', 'pharisee'),
    ('philistines', 'philistine'),
    ('philosophers', 'philosopher'),
    ('physicians', 'physician'),
    ('pictures', 'picture'),
    ('pieces', 'piece'),
    ('pigeons', 'pigeon'),
    ('pigs', 'pig'),
    ('piles', 'pile'),
    ('pillars', 'pillar'),
    ('pilots', 'pilot'),
    ('pines', 'pine'),
    ('pinions', 'pinion'),
    ('pipes', 'pipe'),
    ('pitchers', 'pitcher'),
    ('pits', 'pit'),
    ('places', 'place'),
    ('plagues', 'plague'),
    ('plains', 'plain'),
    ('planets', 'planet'),
    ('planks', 'plank'),
    ('plans', 'plan'),
    ('plantations', 'plantation'),
    ('planters', 'planter'),
    ('plantings', 'planting'),
    ('plants', 'plant'),
    ('plates', 'plate'),
    ('players', 'player'),
    ('plazas', 'plaza'),
    ('pleas', 'plea'),
    ('pleasantnesses', 'pleasantness'),
    ('pleasures', 'pleasure'),
    ('pledges', 'pledge'),
    ('plots', 'plot'),
    ('plowmen', 'plowman'),
    ('plowshares', 'plowshare'),
    ('plunders', 'plunder'),
    ('pockets', 'pocket'),
    ('points', 'point'),
    ('poles', 'pole'),
    ('pollutions', 'pollution'),
    ('pomegranates', 'pomegranate'),
    ('pools', 'pool'),
    ('poplars', 'poplar'),
    ('populations', 'population'),
    ('porches', 'porch'),
    ('portents', 'portent'),
    ('porticos', 'portico'),
    ('portions', 'portion'),
    ('positions', 'position'),
    ('possessions', 'possession'),
    ('posts', 'post'),
    ('pots', 'pot'),
    ('potsherds', 'potsherd'),
    ('potters', 'potter'),
    ('pouches', 'pouch'),
    ('powders', 'powder'),
    ('powers', 'power'),
    ('practices', 'practice'),
    ('praises', 'praise'),
    ('prayers', 'prayer'),
    ('preachers', 'preacher'),
    ('precincts', 'precinct'),
    ('preciousnesses', 'preciousness'),
    ('precipices', 'precipice'),
    ('predecessors', 'predecessor'),
    ('preparations', 'preparation'),
    ('presents', 'present'),
    ('pretenses', 'pretense'),
    ('prices', 'price'),
    ('prides', 'pride'),
    ('priesthoods', 'priesthood'),
    ('priests', 'priest'),
    ('princes', 'prince'),
    ('principles', 'principle'),
    ('priorities', 'priority'),
    ('prisoners', 'prisoner'),
    ('prisons', 'prison'),
    ('privileges', 'privilege'),
    ('prizes', 'prize'),
    ('problems', 'problem'),
    ('procedures', 'procedure'),
    ('processions', 'procession'),
    ('proconsuls', 'proconsul'),
    ('prods', 'prod'),
    ('products', 'product'),
    ('profits', 'profit'),
    ('prohibitions', 'prohibition'),
    ('projections', 'projection'),
    ('projects', 'project'),
    ('promises', 'promise'),
    ('proofs', 'proof'),
    ('properties', 'property'),
    ('prophecies', 'prophecy'),
    ('prophets', 'prophet'),
    ('proportions', 'proportion'),
    ('proposals', 'proposal'),
    ('prosperities', 'prosperity'),
    ('prostitutes', 'prostitute'),
    ('prostitutions', 'prostitution'),
    ('protectors', 'protector'),
    ('proverbs', 'proverb'),
    ('provinces', 'province'),
    ('provisions', 'provision'),
    ('provocations', 'provocation'),
    ('psalms', 'psalm'),
    ('punishments', 'punishment'),
    ('punites', 'punite'),
    ('purifications', 'purification'),
    ('purposes', 'purpose'),
    ('purses', 'purse'),
    ('pursuers', 'pursuer'),
    ('pursuits', 'pursuit'),
    ('puthites', 'puthite'),
    ('qəhātites', 'qəhātite'),
    ('qēynīs', 'qēynī'),
    ('qoraḩites', 'qoraḩite'),
    ('quails', 'quail'),
    ('qualities', 'quality'),
    ('quantities', 'quantity'),
    ('quarrels', 'quarrel'),
    ('quarries', 'quarry'),
    ('quarters', 'quarter'),
    ('queens', 'queen'),
    ('questions', 'question'),
    ('rabbits', 'rabbit'),
    ('rackings', 'racking'),
    ('racks', 'rack'),
    ('rafters', 'rafter'),
    ('rafts', 'raft'),
    ('rages', 'rage'),
    ('rags', 'rag'),
    ('raids', 'raid'),
    ('railings', 'railing'),
    ('rains', 'rain'),
    ('raisin-cakes', 'raisin-cake'),
    ('raisins', 'raisin'),
    ('ramparts', 'rampart'),
    ('ramps', 'ramp'),
    ('rams', 'ram'),
    ('ranges', 'range'),
    ('ranks', 'rank'),
    ('ransoms', 'ransom'),
    ('rashes', 'rash'),
    ('rations', 'ration'),
    ('ravens', 'raven'),
    ('ravines', 'ravine'),
    ('rays', 'ray'),
    ('readers', 'reader'),
    ('readings', 'reading'),
    ('realities', 'reality'),
    ('realms', 'realm'),
    ('reapers', 'reaper'),
    ('reasons', 'reason'),
    ('rebels', 'rebel'),
    ('rebukes', 'rebuke'),
    ('receptacles', 'receptacle'),
    ('recommendations', 'recommendation'),
    ('recompenses', 'recompense'),
    ('recorders', 'recorder'),
    ('records', 'record'),
    ('redemptions', 'redemption'),
    ('reeds', 'reed'),
    ('references', 'reference'),
    ('refiners', 'refiner'),
    ('reflections', 'reflection'),
    ('reforms', 'reform'),
    ('refugees', 'refugee'),
    ('regions', 'region'),
    ('registers', 'register'),
    ('regrets', 'regret'),
    ('regulations', 'regulation'),
    ('reigns', 'reign'),
    ('rejoicings', 'rejoicing'),
    ('rekavites', 'rekavite'),
    ('relationships', 'relationship'),
    ('relatives', 'relative'),
    ('religions', 'religion'),
    ('reminders', 'reminder'),
    ('remissions', 'remission'),
    ('remnants', 'remnant'),
    ('repairers', 'repairer'),
    ('repairs', 'repair'),
    ('repetitions', 'repetition'),
    ('replies', 'reply'),
    ('reports', 'report'),
    ('representatives', 'representative'),
    ('reproaches', 'reproach'),
    ('reproofs', 'reproof'),
    ('reptiles', 'reptile'),
    ('reputations', 'reputation'),
    ('requests', 'request'),
    ('requirements', 'requirement'),
    ('rescuers', 'rescuer'),
    ('reservoirs', 'reservoir'),
    ('residences', 'residence'),
    ('residents', 'resident'),
    ('resolves', 'resolve'),
    ('responsibilities', 'responsibility'),
    ('rest', 'rest'),  # invariable/uncountable
    ('restlessnesses', 'restlessness'),
    ('results', 'result'),
    ('retributions', 'retribution'),
    ('rəʼūⱱēnites', 'rəʼūⱱēnite'),
    ('revelations', 'revelation'),
    ('revenues', 'revenue'),
    ('rewards', 'reward'),
    ('rhythms', 'rhythm'),
    ('ribs', 'rib'),
    ('riddles', 'riddle'),
    ('riders', 'rider'),
    ('ridges', 'ridge'),
    ('righteousnesses', 'righteousness'),
    ('rights', 'right'),
    ('rims', 'rim'),
    ('rings', 'ring'),
    ('riots', 'riot'),
    ('rituals', 'ritual'),
    ('riverbeds', 'riverbed'),
    ('rivers', 'river'),
    ('roads', 'road'),
    ('robberies', 'robbery'),
    ('robbers', 'robber'),
    ('robes', 'robe'),
    ('rocks', 'rock'),
    ('rods', 'rod'),
    ('roles', 'role'),
    ('rolls', 'roll'),
    ('romans', 'roman'),
    ('roofs', 'roof'),
    ('rooms', 'room'),
    ('roots', 'root'),
    ('ropes', 'rope'),
    ('roses', 'rose'),
    ('rows', 'row'),
    ('rubbings', 'rubbing'),
    ('rubbles', 'rubble'),
    ('rubies', 'ruby'),
    ('rudders', 'rudder'),
    ('rugs', 'rug'),
    ('ruins', 'ruin'),
    ('rulers', 'ruler'),
    ('rules', 'rule'),
    ('rulings', 'ruling'),
    ('rumblings', 'rumbling'),
    ('rumours', 'rumour'),
    ('runners', 'runner'),
    ('rushes', 'rush'),
    ('rust', 'rust'),  # invariable/uncountable
    ('sabbaths', 'sabbath'),
    ('sabeans', 'sabean'),
    ('sackcloths', 'sackcloth'),
    ('sacks', 'sack'),
    ('sacrifices', 'sacrifice'),
    ('sacrileges', 'sacrilege'),
    ('saddlebags', 'saddlebag'),
    ('saddles', 'saddle'),
    ('sadducees', 'sadducee'),
    ('sailors', 'sailor'),
    ('sails', 'sail'),
    ('sakes', 'sake'),
    ('sales', 'sale'),
    ('salvations', 'salvation'),
    ('sanctuaries', 'sanctuary'),
    ('sandals', 'sandal'),
    ('sands', 'sand'),
    ('sanhedrins', 'sanhedrin'),
    ('sapphires', 'sapphire'),
    ('saraphs', 'saraph'),
    ('sardites', 'sardite'),
    ('sashes', 'sash'),
    ('savings', 'saving'),
    ('saviours', 'saviour'),
    ('saws', 'saw'),
    ('sayings', 'saying'),
    ('scabs', 'scab'),
    ('scales', 'scale'),
    ('scarlets', 'scarlet'),
    ('scepters', 'scepter'),
    ('sceptres', 'sceptre'),
    ('schemes', 'scheme'),
    ('schemings', 'scheming'),
    ('scoffers', 'scoffer'),
    ('scorpions', 'scorpion'),
    ('scoundrels', 'scoundrel'),
    ('scourges', 'scourge'),
    ('scraps', 'scrap'),
    ('scribes', 'scribe'),
    ('scriptures', 'scripture'),
    ('scrolls', 'scroll'),
    ('seahs', 'seah'),
    ('seals', 'seal'),
    ('searchings', 'searching'),
    ('seas', 'sea'),
    ('seashores', 'seashore'),
    ('seasons', 'season'),
    ('seats', 'seat'),
    ('seconds', 'second'),
    ('secretaries', 'secretary'),
    ('secrets', 'secret'),
    ('sections', 'section'),
    ('sects', 'sect'),
    ('securities', 'security'),
    ('seductions', 'seduction'),
    ('seeds', 'seed'),
    ('seers', 'seer'),
    ('sellers', 'seller'),
    ('selves', 'self'),
    ('senses', 'sense'),
    ('sentences', 'sentence'),
    ('sentiments', 'sentiment'),
    ('sentinels', 'sentinel'),
    ('serpents', 'serpent'),
    ('servants', 'servant'),
    ('services', 'service'),
    ('sets', 'set'),
    ('settings', 'setting'),
    ('settlements', 'settlement'),
    ('sevens', 'seven'),
    ('shackles', 'shackle'),
    ('shades', 'shade'),
    ('shadows', 'shadow'),
    ('shafts', 'shaft'),
    ('shame', 'shame'),  # invariable/uncountable
    ('shapes', 'shape'),
    ('shares', 'share'),
    ('shāʼūlites', 'shāʼūlite'),
    ('shawls', 'shawl'),
    ('sheaves', 'sheaf'),
    ('shechemites', 'shechemite'),
    ('sheep', 'sheep'),  # invariable/uncountable
    ('sheepfolds', 'sheepfold'),
    ('sheets', 'sheet'),
    ('she-goats', 'she-goat'),
    ('shekels', 'shekel'),
    ('shəkemites', 'shəkemite'),
    ('shēlāhites', 'shēlāhite'),
    ('shelters', 'shelter'),
    ('shəmīdāˊites', 'shəmīdāˊite'),
    ('shepherds', 'shepherd'),
    ('shields', 'shield'),
    ('shillemites', 'shillemite'),
    ('shilōnīs', 'shilōnī'),
    ('shimeons', 'shimeon'),
    ('shimˊītes', 'shimˊīte'),
    ('shimˊōnites', 'shimˊōnite'),
    ('shimrōnites', 'shimrōnite'),
    ('ships', 'ship'),
    ('shooters', 'shooter'),
    ('shoots', 'shoot'),
    ('shores', 'shore'),
    ('shortages', 'shortage'),
    ('shoulders', 'shoulder'),
    ('shoutings', 'shouting'),
    ('shouts', 'shout'),
    ('shovels', 'shovel'),
    ('showers', 'shower'),
    ('shrines', 'shrine'),
    ('shudders', 'shudder'),
    ('shuhamites', 'shuhamite'),
    ('shumathites', 'shumathite'),
    ('shunites', 'shunite'),
    ('shuphamites', 'shuphamite'),
    ('shūtelaḩites', 'shūtelaḩite'),
    ('siblings', 'sibling'),
    ('sicknesses', 'sickness'),
    ('side-chambers', 'side-chamber'),
    ('sides', 'side'),
    ('sidonians', 'sidonian'),
    ('sieges', 'siege'),
    ('siege-works', 'siege-work'),
    ('sights', 'sight'),
    ('signet-rings', 'signet-ring'),
    ('signets', 'signet'),
    ('signposts', 'signpost'),
    ('signs', 'sign'),
    ('silvers', 'silver'),
    ('silversmiths', 'silversmith'),
    ('singers', 'singer'),
    ('sinners', 'sinner'),
    ('sins', 'sin'),
    ('sirs', 'sir'),
    ('sisters', 'sister'),
    ('sites', 'site'),
    ('situations', 'situation'),
    ('sizes', 'size'),
    ('skies', 'sky'),
    ('skills', 'skill'),
    ('skin-bottles', 'skin-bottle'),
    ('skinks', 'skink'),
    ('skins', 'skin'),
    ('skirts', 'skirt'),
    ('slabs', 'slab'),
    ('slackers', 'slacker'),
    ('slags', 'slag'),
    ('slanderers', 'slanderer'),
    ('slanders', 'slander'),
    ('slaps', 'slap'),
    ('slaughters', 'slaughter'),
    ('slaves', 'slave'),
    ('slave-wives', 'slave-wife'),
    ('sledges', 'sledge'),
    ('sleepers', 'sleeper'),
    ('slings', 'sling'),
    ('slopes', 'slope'),
    ('smoothnesses', 'smoothness'),
    ('snacks', 'snack'),
    ('snakes', 'snake'),
    ('snares', 'snare'),
    ('sneezings', 'sneezing'),
    ('societies', 'society'),
    ('sockets', 'socket'),
    ('sodomites', 'sodomite'),
    ('sojourners', 'sojourner'),
    ('sojourning-places', 'sojourning-place'),
    ('sojournings', 'sojourning'),
    ('soldiers', 'soldier'),
    ('soles', 'sole'),
    ('songs', 'song'),
    ('sons', 'son'),
    ('sons-in-law', 'son-in-law'),
    ('soothsayers', 'soothsayer'),
    ('soothsayings', 'soothsaying'),
    ('sorcerers', 'sorcerer'),
    ('sorceries', 'sorcery'),
    ('sores', 'sore'),
    ('sorrows', 'sorrow'),
    ('sorts', 'sort'),
    ('souls', 'soul'),
    ('sounds', 'sound'),
    ('sources', 'source'),
    ('sovereigns', 'sovereign'),
    ('spaces', 'space'),
    ('sparks', 'spark'),
    ('sparrows', 'sparrow'),
    ('spearmen', 'spearman'),
    ('spears', 'spear'),
    ('specks', 'speck'),
    ('speculations', 'speculation'),
    ('speeches', 'speech'),
    ('spells', 'spell'),
    ('spelts', 'spelt'),
    ('spices', 'spice'),
    ('spiders', 'spider'),
    ('spies', 'spy'),
    ('spirits', 'spirit'),
    ('spoils', 'spoil'),
    ('spokes', 'spoke'),
    ('spokesmen', 'spokesman'),
    ('spots', 'spot'),
    ('spouses', 'spouse'),
    ('spreadings', 'spreading'),
    ('springs', 'spring'),
    ('squads', 'squad'),
    ('squares', 'square'),
    ('stacks', 'stack'),
    ('stadiums', 'stadium'),
    ('staffs', 'staff'),
    ('stages', 'stage'),
    ('stains', 'stain'),
    ('stairways', 'stairway'),
    ('stakes', 'stake'),
    ('stalks', 'stalk'),
    ('stallions', 'stallion'),
    ('stalls', 'stall'),
    ('stammerings', 'stammering'),
    ('standards', 'standard'),
    ('stands', 'stand'),
    ('stars', 'star'),
    ('statements', 'statement'),
    ('states', 'state'),
    ('stations', 'station'),
    ('statues', 'statue'),
    ('statures', 'stature'),
    ('statutes', 'statute'),
    ('staves', 'staff'),
    ('steeds', 'steed'),
    ('steps', 'step'),
    ('stewards', 'steward'),
    ('sticks', 'stick'),
    ('stings', 'sting'),
    ('stocks', 'stock'),
    ('stomachs', 'stomach'),
    ('stonemasons', 'stonemason'),
    ('stones', 'stone'),
    ('storehouses', 'storehouse'),
    ('store-rooms', 'store-room'),
    ('storerooms', 'storeroom'),
    ('stores', 'store'),
    ('stories', 'story'),
    ('storks', 'stork'),
    ('storms', 'storm'),
    ('storm-winds', 'storm-wind'),
    ('straightforwardnesses', 'straightforwardness'),
    ('strains', 'strain'),
    ('strangers', 'stranger'),
    ('straps', 'strap'),
    ('straws', 'straw'),
    ('stream-beds', 'stream-bed'),
    ('streams', 'stream'),
    ('streets', 'street'),
    ('strengths', 'strength'),
    ('strifes', 'strife'),
    ('strings', 'string'),
    ('stripes', 'stripe'),
    ('strips', 'strip'),
    ('strongholds', 'stronghold'),
    ('structures', 'structure'),
    ('struggles', 'struggle'),
    ('studs', 'stud'),
    ('stumblings', 'stumbling'),
    ('stumps', 'stump'),
    ('subjects', 'subject'),
    ('substitutions', 'substitution'),
    ('subtleties', 'subtlety'),
    ('successes', 'success'),
    ('sufferings', 'suffering'),
    ('suggestions', 'suggestion'),
    ('summits', 'summit'),
    ('sums', 'sum'),
    ('sun', 'sun'),  # invariable/uncountable
    ('supervisors', 'supervisor'),
    ('suppers', 'supper'),
    ('supplications', 'supplication'),
    ('supplies', 'supply'),
    ('supporters', 'supporter'),
    ('supports', 'support'),
    ('survivors', 'survivor'),
    ('suspicions', 'suspicion'),
    ('swallows', 'swallow'),
    ('swamps', 'swamp'),
    ('swarms', 'swarm'),
    ('sweetnesses', 'sweetness'),
    ('swellings', 'swelling'),
    ('swindlers', 'swindler'),
    ('swine', 'swine'),  # invariable singular/plural
    ('swords', 'sword'),
    ('sycamores', 'sycamore'),
    ('symbols', 'symbol'),
    ('synagogues', 'synagogue'),
    ('syrians', 'syrian'),
    ('tabernacles', 'tabernacle'),
    ('tables', 'table'),
    ('tablets', 'tablet'),
    ('taḩanites', 'taḩanite'),
    ('tails', 'tail'),
    ('talantons', 'talanton'),
    ('talents', 'talent'),
    ('talks', 'talk'),
    ('tambourines', 'tambourine'),
    ('taskmasters', 'taskmaster'),
    ('tasks', 'task'),
    ('tassels', 'tassel'),
    ('taunts', 'taunt'),
    ('tax-collectors', 'tax-collector'),
    ('taxes', 'tax'),
    ('teachers', 'teacher'),
    ('teachings', 'teaching'),
    ('teams', 'team'),
    ('tears', 'tear'),
    ('teeth', 'tooth'),
    ('tekoites', 'tekoite'),
    ('tempests', 'tempest'),
    ('temples', 'temple'),
    ('temptations', 'temptation'),
    ('tenants', 'tenant'),
    ('tendons', 'tendon'),
    ('tens', 'ten'),
    ('tent-cords', 'tent-cord'),
    ('tenths', 'tenth'),
    ('tents', 'tent'),
    ('terebinths', 'terebinth'),
    ('terms', 'term'),
    ('terraces', 'terrace'),
    ('territories', 'territory'),
    ('terrors', 'terror'),
    ('testicles', 'testicle'),
    ('testimonies', 'testimony'),
    ('tēymānīs', 'tēymānī'),
    ('thank-offerings', 'thank-offering'),
    ('thanksgivings', 'thanksgiving'),
    ('theatres', 'theatre'),
    ('thefts', 'theft'),
    ('theories', 'theory'),
    ('thickets', 'thicket'),
    ('thieves', 'thief'),
    ('thighs', 'thigh'),
    ('things', 'thing'),
    ('thirds', 'third'),
    ('thistles', 'thistle'),
    ('thornbushes', 'thornbush'),
    ('thorns', 'thorn'),
    ('thoughts', 'thought'),
    ('thousands', 'thousand'),
    ('threads', 'thread'),
    ('threatenings', 'threatening'),
    ('threats', 'threat'),
    ('threshing-sledges', 'threshing-sledge'),
    ('thresholds', 'threshold'),
    ('throats', 'throat'),
    ('thrones', 'throne'),
    ('throwings', 'throwing'),
    ('thumbs', 'thumb'),
    ('thunders', 'thunder'),
    ('tiles', 'tile'),
    ('times', 'time'),
    ('tips', 'tip'),
    ('tishbites', 'tishbite'),
    ('tithes', 'tithe'),
    ('titles', 'title'),
    ('toes', 'toe'),
    ('toils', 'toil'),
    ('tokens', 'token'),
    ('tōlāˊites', 'tōlāˊite'),
    ('tombs', 'tomb'),
    ('tongues', 'tongue'),
    ('tools', 'tool'),
    ('topics', 'topic'),
    ('tops', 'top'),
    ('torches', 'torch'),
    ('torments', 'torment'),
    ('torrents', 'torrent'),
    ('tortures', 'torture'),
    ('totals', 'total'),
    ('towers', 'tower'),
    ('towns', 'town'),
    ('traces', 'trace'),
    ('tracks', 'track'),
    ('traders', 'trader'),
    ('traditions', 'tradition'),
    ('trails', 'trail'),
    ('traitors', 'traitor'),
    ('transcripts', 'transcript'),
    ('transgressions', 'transgression'),
    ('transgressors', 'transgressor'),
    ('trappings', 'trapping'),
    ('traps', 'trap'),
    ('travellers', 'traveller'),
    ('travels', 'travel'),
    ('trays', 'tray'),
    ('treacheries', 'treachery'),
    ('treaders', 'treader'),
    ('treasurers', 'treasurer'),
    ('treasures', 'treasure'),
    ('treasuries', 'treasury'),
    ('treaties', 'treaty'),
    ('treatments', 'treatment'),
    ('trees', 'tree'),
    ('tremblings', 'trembling'),
    ('trenches', 'trench'),
    ('trials', 'trial'),
    ('tribes', 'tribe'),
    ('tribulations', 'tribulation'),
    ('tributes', 'tribute'),
    ('tricks', 'trick'),
    ('trips', 'trip'),
    ('troops', 'troop'),
    ('troublemakers', 'troublemaker'),
    ('troubles', 'trouble'),
    ('troughs', 'trough'),
    ('trumpets', 'trumpet'),
    ('trunks', 'trunk'),
    ('truths', 'truth'),
    ('tubes', 'tube'),
    ('tunes', 'tune'),
    ('tunics', 'tunic'),
    ('turbans', 'turban'),
    ('turns', 'turn'),
    ('turtle-doves', 'turtle-dove'),
    ('turtledoves', 'turtledove'),
    ('tutors', 'tutor'),
    ('twigs', 'twig'),
    ('twins', 'twin'),
    ('types', 'type'),
    ('tyrants', 'tyrant'),
    ('tyrians', 'tyrian'),
    ('ulcers', 'ulcer'),
    ('unbelievers', 'unbeliever'),
    ('uncleannesses', 'uncleanness'),
    ('uncles', 'uncle'),
    ('understandings', 'understanding'),
    ('undertakings', 'undertaking'),
    ('uniforms', 'uniform'),
    ('units', 'unit'),
    ('uprightnesses', 'uprightness'),
    ('uproars', 'uproar'),
    ('upsets', 'upset'),
    ('uses', 'use'),
    ('utterances', 'utterance'),
    ('valleys', 'valley'),
    ('valuables', 'valuable'),
    ('valuations', 'valuation'),
    ('values', 'value'),
    ('vanities', 'vanity'),
    ('vapours', 'vapour'),
    ('varieties', 'variety'),
    ('vats', 'vat'),
    ('vegetables', 'vegetable'),
    ('vegetations', 'vegetation'),
    ('veils', 'veil'),
    ('vengeances', 'vengeance'),
    ('verses', 'verse'),
    ('vessels', 'vessel'),
    ('vices', 'vice'),
    ('victims', 'victim'),
    ('victories', 'victory'),
    ('victors', 'victor'),
    ('views', 'view'),
    ('vigils', 'vigil'),
    ('vigors', 'vigor'),
    ('villages', 'village'),
    ('vinedressers', 'vinedresser'),
    ('vines', 'vine'),
    ('vineyards', 'vineyard'),
    ('violences', 'violence'),
    ('vipers', 'viper'),
    ('virginities', 'virginity'),
    ('virgins', 'virgin'),
    ('virtues', 'virtue'),
    ('visions', 'vision'),
    ('visitors', 'visitor'),
    ('voices', 'voice'),
    ('voluntarinesses', 'voluntariness'),
    ('votes', 'vote'),
    ('vows', 'vow'),
    ('vultures', 'vulture'),
    ('wadis', 'wadi'),
    ('wafers', 'wafer'),
    ('wages', 'wage'),
    ('wailings', 'wailing'),
    ('wails', 'wail'),
    ('waistbands', 'waistband'),
    ('waists', 'waist'),
    ('walkways', 'walkway'),
    ('wallets', 'wallet'),
    ('walls', 'wall'),
    ('wanderers', 'wanderer'),
    ('wanderings', 'wandering'),
    ('wantonnesses', 'wantonness'),
    ('warhorses', 'warhorse'),
    ('warnings', 'warning'),
    ('warriors', 'warrior'),
    ('wars', 'war'),
    ('washbasins', 'washbasin'),
    ('washers', 'washer'),
    ('washings', 'washing'),
    ('wastelands', 'wasteland'),
    ('wastes', 'waste'),
    ('watchers', 'watcher'),
    ('watches', 'watch'),
    ('watchings', 'watching'),
    ('watchmen', 'watchman'),
    ('watchtowers', 'watchtower'),
    ('waterfalls', 'waterfall'),
    ('waterpots', 'waterpot'),
    ('waters', 'water'),
    ('wave-offerings', 'wave-offering'),
    ('waves', 'wave'),
    ('ways', 'way'),
    ('weaknesses', 'weakness'),
    ('wealths', 'wealth'),
    ('weapons', 'weapon'),
    ('weavers', 'weaver'),
    ('weavings', 'weaving'),
    ('webs', 'web'),
    ('wedges', 'wedge'),
    ('weeds', 'weed'),
    ('weeks', 'week'),
    ('weights', 'weight'),
    ('wells', 'well'),
    ('welts', 'welt'),
    ('wheats', 'wheat'),
    ('wheels', 'wheel'),
    ('whips', 'whip'),
    ('whirlwinds', 'whirlwind'),
    ('wickednesses', 'wickedness'),
    ('wicks', 'wick'),
    ('widows', 'widow'),
    ('wildernesses', 'wilderness'),
    ('willows', 'willow'),
    ('wills', 'will'),
    ('windows', 'window'),
    ('winds', 'wind'),
    ('winepresses', 'winepress'),
    ('wines', 'wine'),
    ('wineskins', 'wineskin'),
    ('wine-vats', 'wine-vat'),
    ('winged-creatures', 'winged-creature'),
    ('wings', 'wing'),
    ('wingtips', 'wingtip'),
    ('wisdoms', 'wisdom'),
    ('wishes', 'wish'),
    ('witnesses', 'witness'),
    ('wives', 'wife'),
    ('woes', 'woe'),
    ('wolves', 'wolf'),
    ('wombs', 'womb'),
    ('women', 'woman'),
    ('wonders', 'wonder'),
    ('woodcutters', 'woodcutter'),
    ('woods', 'wood'),
    ('words', 'word'),
    ('workers', 'worker'),
    ('workmen', 'workman'),
    ('works', 'work'),
    ('worlds', 'world'),
    ('worms', 'worm'),
    ('worries', 'worry'),
    ('wounds', 'wound'),
    ('wreaths', 'wreath'),
    ('wrestlings', 'wrestling'),
    ('wretches', 'wretch'),
    ('wrinkles', 'wrinkle'),
    ('wrists', 'wrist'),
    ('writers', 'writer'),
    ('writings', 'writing'),
    ('wrongs', 'wrong'),
    ('yākīnites', 'yākīnite'),
    ('yāmīnites', 'yāmīnite'),
    ('yards', 'yard'),
    ('years', 'year'),
    ('yebusites', 'yebusite'),
    ('yēʦerites', 'yēʦerite'),
    ('yevusites', 'yevusite'),
    ('yields', 'yield'),
    ('yimnāhites', 'yimnāhite'),
    ('yishvītes', 'yishvīte'),
    ('yitrites', 'yitrite'),
    ('yoke-bars', 'yoke-bar'),
    ('youths', 'youth'),
    ('yudeans', 'yudean'),
    ('zerahites', 'zerahite'),
    ('zəⱱūlūnites', 'zəⱱūlūnite'),
    ('zorathites', 'zorathite'),
    ('zorites', 'zorite'),
)
assert len(set(SIMPLE_NOUN_PAIRS)) == len(SIMPLE_NOUN_PAIRS) # Check for accidental duplicates

# Flatten SIMPLE_NOUN_PAIRS (tuple of (plural, singular) pairs) into a flat tuple of all forms
SIMPLE_NOUNS_FLAT = tuple(form for pair in SIMPLE_NOUN_PAIRS for form in pair)
# Asserts below are not true because of invariable pairs above
#for simpleNoun in SIMPLE_NOUNS_FLAT:
#    assert SIMPLE_NOUNS_FLAT.count( simpleNoun ) == 1, f"{simpleNoun=} {SIMPLE_NOUNS_FLAT.count( simpleNoun )}"
#assert len(set(SIMPLE_NOUNS_FLAT)) == len(SIMPLE_NOUNS_FLAT) # Check for accidental duplicates in flattened form

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
    # Sorted by the base present form (last item in each set).
    ('abandoned', 'abandoning', 'abandons', 'abandon'),
    ('abducted', 'abducting', 'abducts', 'abduct'),
    ('abhorred', 'abhorring', 'abhors', 'abhor'),
    ('abided', 'abiding', 'abides', 'abode', 'abide'),
    ('abolished', 'abolishing', 'abolishes', 'abolish'),
    ('abounded', 'abounding', 'abounds', 'abound'),
    ('abstained', 'abstaining', 'abstains', 'abstain'),
    ('abused', 'abusing', 'abuses', 'abuse'),
    ('accepted', 'accepting', 'accepts', 'accept'),
    ('accommodated', 'accommodating', 'accommodates', 'accommodate'),
    ('accompanied', 'accompanying', 'accompanies', 'accompany'),
    ('accomplished', 'accomplishing', 'accomplishes', 'accomplish'),
    ('accounted', 'accounting', 'accounts', 'account'),
    ('accumulated', 'accumulating', 'accumulates', 'accumulate'),
    ('accused', 'accusing', 'accuses', 'accuse'),
    ('accustomed', 'accustoming', 'accustoms', 'accustom'),
    ('ached', 'aching', 'aches', 'ache'),
    ('achieved', 'achieving', 'achieves', 'achieve'),
    ('acknowledged', 'acknowledging', 'acknowledges', 'acknowledge'),
    ('acquainted', 'acquainting', 'acquaints', 'acquaint'),
    ('acquired', 'acquiring', 'acquires', 'acquire'),
    ('acquitted', 'acquitting', 'acquits', 'acquit'),
    ('acted', 'acting', 'acts', 'act'),
    ('actioned', 'actioning', 'actions', 'action'),
    ('adapted', 'adapting', 'adapts', 'adapt'),
    ('added', 'adding', 'adds', 'add'),
    ('addressed', 'addressing', 'addresses', 'address'),
    ('adjured', 'adjuring', 'adjures', 'adjure'),
    ('administered', 'administering', 'administers', 'administer'),
    ('admired', 'admiring', 'admires', 'admire'),
    ('admitted', 'admitting', 'admits', 'admit'),
    ('admonished', 'admonishing', 'admonishes', 'admonish'),
    ('adopted', 'adopting', 'adopts', 'adopt'),
    ('adorned', 'adorning', 'adorns', 'adorn'),
    ('advanced', 'advancing', 'advances', 'advance'),
    ('advised', 'advising', 'advises', 'advise'),
    ('affected', 'affecting', 'affects', 'affect'),
    ('affirmed', 'affirming', 'affirms', 'affirm'),
    ('afflicted', 'afflicting', 'afflicts', 'afflict'),
    ('afforded', 'affording', 'affords', 'afford'),
    ('aged', 'aging', 'ages', 'age'),
    ('agitated', 'agitating', 'agitates', 'agitate'),
    ('agreed', 'agreeing', 'agrees', 'agree'),
    ('aided', 'aiding', 'aids', 'aid'),
    ('ailed', 'ailing', 'ails', 'ail'),
    ('aimed', 'aiming', 'aims', 'aim'),
    ('alarmed', 'alarming', 'alarms', 'alarm'),
    ('aligned', 'aligning', 'aligns', 'align'),
    ('alleged', 'alleging', 'alleges', 'allege'),
    ('allocated', 'allocating', 'allocates', 'allocate'),
    ('allotted', 'allotting', 'allots', 'allot'),
    ('allowed', 'allowing', 'allows', 'allow'),
    ('allied', 'allying', 'allies', 'ally'),
    ('altered', 'altering', 'alters', 'alter'),
    ('amassed', 'amassing', 'amasses', 'amass'),
    ('amazed', 'amazing', 'amazes', 'amaze'),
    ('ambushed', 'ambushing', 'ambushes', 'ambush'),
    ('anchored', 'anchoring', 'anchors', 'anchor'),
    ('angered', 'angering', 'angers', 'anger'),
    ('annihilated', 'annihilating', 'annihilates', 'annihilate'),
    ('announced', 'announcing', 'announces', 'announce'),
    ('annoyed', 'annoying', 'annoys', 'annoy'),
    ('annulled', 'annulling', 'annuls', 'annul'),
    ('anointed', 'anointing', 'anoints', 'anoint'),
    ('answered', 'answering', 'answers', 'answer'),
    ('anticipated', 'anticipating', 'anticipates', 'anticipate'),
    ('apologised', 'apologising', 'apologises', 'apologise'),
    ('appealed', 'appealing', 'appeals', 'appeal'),
    ('appeared', 'appearing', 'appears', 'appear'),
    ('appeased', 'appeasing', 'appeases', 'appease'),
    ('applied', 'applying', 'applies', 'apply'),
    ('appointed', 'appointing', 'appoints', 'appoint'),
    ('apportioned', 'apportioning', 'apportions', 'apportion'),
    ('appreciated', 'appreciating', 'appreciates', 'appreciate'),
    ('apprehended', 'apprehending', 'apprehends', 'apprehend'),
    ('approached', 'approaching', 'approaches', 'approach'),
    ('approved', 'approving', 'approves', 'approve'),
    ('arbitrated', 'arbitrating', 'arbitrates', 'arbitrate'),
    ('argued', 'arguing', 'argues', 'argue'),
    ('arose', 'arisen', 'arising', 'arises', 'arise'),
    ('armed', 'arming', 'arms', 'arm'),
    ('aroused', 'arousing', 'arouses', 'arouse'),
    ('arranged', 'arranging', 'arranges', 'arrange'),
    ('arrayed', 'arraying', 'arrays', 'array'),
    ('arrested', 'arresting', 'arrests', 'arrest'),
    ('arrived', 'arriving', 'arrives', 'arrive'),
    ('ascended', 'ascending', 'ascends', 'ascend'),
    ('ascribed', 'ascribing', 'ascribes', 'ascribe'),
    ('asked', 'asking', 'asks', 'ask'),
    ('aspired', 'aspiring', 'aspires', 'aspire'),
    ('assailed', 'assailing', 'assails', 'assail'),
    ('assassinated', 'assassinating', 'assassinates', 'assassinate'),
    ('assaulted', 'assaulting', 'assaults', 'assault'),
    ('assembled', 'assembling', 'assembles', 'assemble'),
    ('assigned', 'assigning', 'assigns', 'assign'),
    ('assisted', 'assisting', 'assists', 'assist'),
    ('associated', 'associating', 'associates', 'associate'),
    ('assumed', 'assuming', 'assumes', 'assume'),
    ('assured', 'assuring', 'assures', 'assure'),
    ('astonished', 'astonishing', 'astonishes', 'astonish'),
    ('astounded', 'astounding', 'astounds', 'astound'),
    ('atoned', 'atoning', 'atones', 'atone'),
    ('attached', 'attaching', 'attaches', 'attach'),
    ('attacked', 'attacking', 'attacks', 'attack'),
    ('attained', 'attaining', 'attains', 'attain'),
    ('attempted', 'attempting', 'attempts', 'attempt'),
    ('attended', 'attending', 'attends', 'attend'),
    ('attested', 'attesting', 'attests', 'attest'),
    ('attracted', 'attracting', 'attracts', 'attract'),
    ('attributed', 'attributing', 'attributes', 'attribute'),
    ('authorised', 'authorising', 'authorises', 'authorized', 'authorizing', 'authorizes', 'authorize', 'authorise'),
    ('avenged', 'avenging', 'avenges', 'avenge'),
    ('avoided', 'avoiding', 'avoids', 'avoid'),
    ('awaited', 'awaiting', 'awaits', 'await'),
    ('awoke', 'awoken', 'awaking', 'awakes', 'awake'),
    ('awakened', 'awakening', 'awakens', 'awaken'),
    ('babbled', 'babbling', 'babbles', 'babble'),
    ('backed', 'backing', 'backs', 'back'),
    ('bagged', 'bagging', 'bags', 'bag'),
    ('baked', 'baking', 'bakes', 'bake'),
    ('balanced', 'balancing', 'balances', 'balance'),
    ('banned', 'banning', 'bans', 'ban'),
    ('banded', 'banding', 'bands', 'band'),
    ('bandaged', 'bandaging', 'bandages', 'bandage'),
    ('banished', 'banishing', 'banishes', 'banish'),
    ('banqueted', 'banqueting', 'banquets', 'banquet'),
    ('barred', 'barring', 'bars', 'bar'),
    ('bared', 'baring', 'bares', 'bare'),
    ('bargained', 'bargaining', 'bargains', 'bargain'),
    ('barricaded', 'barricading', 'barricades', 'barricade'),
    ('bartered', 'bartering', 'barters', 'barter'),
    ('based', 'basing', 'bases', 'base'),
    ('bashed', 'bashing', 'bashes', 'bash'),
    ('bathed', 'bathing', 'bathes', 'bathe'),
    ('battered', 'battering', 'batters', 'batter'),
    ('battled', 'battling', 'battles', 'battle'),
    ('am', 'is', 'are', 'was', 'were', 'being', 'been', 'be'),
    ('beached', 'beaching', 'beaches', 'beach'),
    ('bore', 'born', 'borne', 'bearing', 'bears', 'bear'),
    ('beaten', 'beating', 'beats', 'beat'),
    ('beautified', 'beautifying', 'beautifies', 'beautify'),
    ('became', 'becoming', 'becomes', 'become'),
    ('befell', 'befallen', 'befalling', 'befalls', 'befall'),
    ('befitted', 'befitting', 'befits', 'befit'),
    ('befriended', 'befriending', 'befriends', 'befriend'),
    ('begged', 'begging', 'begs', 'beg'),
    ('begot', 'begotten', 'begetting', 'begets', 'beget'),
    ('began', 'begun', 'beginning', 'begins', 'begin'),
    ('behaved', 'behaving', 'behaves', 'behave'),
    ('beheaded', 'beheading', 'beheads', 'behead'),
    ('belched', 'belching', 'belches', 'belch'),
    ('believed', 'believing', 'believes', 'believe'),
    ('belittled', 'belittling', 'belittles', 'belittle'),
    ('belonged', 'belonging', 'belongs', 'belong'),
    ('bent', 'bending', 'bends', 'bend'),
    ('benefited', 'benefitted', 'benefiting', 'benefitting', 'benefits', 'benefit'),
    ('bereaved', 'bereft', 'bereaving', 'bereaves', 'bereave'),
    ('besought', 'beseeched', 'beseeching', 'beseeches', 'beseech'),
    ('besieged', 'besieging', 'besieges', 'besiege'),
    ('bestowed', 'bestowing', 'bestows', 'bestow'),
    ('betrayed', 'betraying', 'betrays', 'betray'),
    ('betrothed', 'betrothing', 'betroths', 'betroth'),
    ('bewailed', 'bewailing', 'bewails', 'bewail'),
    ('bade', 'bidden', 'bidding', 'bids', 'bid'),
    ('bound', 'binding', 'binds', 'bind'),
    ('birthed', 'birthing', 'births', 'birth'),
    ('bit', 'bitten', 'biting', 'bites', 'bite'),
    ('blamed', 'blaming', 'blames', 'blame'),
    ('blanketed', 'blanketing', 'blankets', 'blanket'),
    ('blasphemed', 'blaspheming', 'blasphemes', 'blaspheme'),
    ('blasted', 'blasting', 'blasts', 'blast'),
    ('blazed', 'blazing', 'blazes', 'blaze'),
    ('bleated', 'bleating', 'bleats', 'bleat'),
    ('bled', 'bleeding', 'bleeds', 'bleed'),
    ('blemished', 'blemishing', 'blemishes', 'blemish'),
    ('blessed', 'blessing', 'blesses', 'bless'),
    ('blinded', 'blinding', 'blinds', 'blind'),
    ('blindfolded', 'blindfolding', 'blindfolds', 'blindfold'),
    ('blocked', 'blocking', 'blocks', 'block'),
    ('bloomed', 'blooming', 'blooms', 'bloom'),
    ('blossomed', 'blossoming', 'blossoms', 'blossom'),
    ('blotted', 'blotting', 'blots', 'blot'),
    ('blew', 'blown', 'blowing', 'blows', 'blow'),
    ('boarded', 'boarding', 'boards', 'board'),
    ('boasted', 'boasting', 'boasts', 'boast'),
    ('boiled', 'boiling', 'boils', 'boil'),
    ('bonded', 'bonding', 'bonds', 'bond'),
    ('bored', 'boring', 'bores', 'bore'),
    ('borrowed', 'borrowing', 'borrows', 'borrow'),
    ('bothered', 'bothering', 'bothers', 'bother'),
    ('bounced', 'bouncing', 'bounces', 'bounce'),
    ('bounded', 'bounding', 'bounds', 'bound'),
    ('bowed', 'bowing', 'bows', 'bow'),
    ('bowled', 'bowling', 'bowls', 'bowl'),
    ('boxed', 'boxing', 'boxes', 'box'),
    ('braced', 'bracing', 'braces', 'brace'),
    ('bragged', 'bragging', 'brags', 'brag'),
    ('braided', 'braiding', 'braids', 'braid'),
    ('brandished', 'brandishing', 'brandishes', 'brandish'),
    ('broke', 'broken', 'breaking', 'breaks', 'break'),
    ('breastfed', 'breastfeeding', 'breastfeeds', 'breast-fed', 'breast-feeding', 'breast-feeds', 'breast-feed', 'breastfeed'),
    ('breathed', 'breathing', 'breathes', 'breathe'),
    ('bred', 'breeding', 'breeds', 'breed'),
    ('bribed', 'bribing', 'bribes', 'bribe'),
    ('bridled', 'bridling', 'bridles', 'bridle'),
    ('briefed', 'briefing', 'briefs', 'brief'),
    ('brightened', 'brightening', 'brightens', 'brighten'),
    ('brought', 'bringing', 'brings', 'bring'),
    ('bristled', 'bristling', 'bristles', 'bristle'),
    ('bruised', 'bruising', 'bruises', 'bruise'),
    ('brushed', 'brushing', 'brushes', 'brush'),
    ('buckled', 'buckling', 'buckles', 'buckle'),
    ('budded', 'budding', 'buds', 'bud'),
    ('budgeted', 'budgeting', 'budgets', 'budget'),
    ('built', 'building', 'builds', 'build'),
    ('bulged', 'bulging', 'bulges', 'bulge'),
    ('bullied', 'bullying', 'bullies', 'bully'),
    ('burdened', 'burdening', 'burdens', 'burden'),
    ('burned', 'burnt', 'burning', 'burns', 'burn'),
    ('bursting', 'bursts', 'burst'),
    ('buried', 'burying', 'buries', 'bury'),
    ('butchered', 'butchering', 'butchers', 'butcher'),
    ('bought', 'buying', 'buys', 'buy'),
    ('calculated', 'calculating', 'calculates', 'calculate'),
    ('called', 'calling', 'calls', 'call'),
    ('calmed', 'calming', 'calms', 'calm'),
    ('calved', 'calving', 'calves', 'calve'),
    ('camped', 'camping', 'camps', 'camp'),
    ('could', 'can'),
    ('cancelled', 'cancelling', 'cancels', 'cancel'),
    ('captured', 'capturing', 'captures', 'capture'),
    ('cared', 'caring', 'cares', 'care'),
    ('caressed', 'caressing', 'caresses', 'caress'),
    ('caroused', 'carousing', 'carouses', 'carouse'),
    ('carried', 'carrying', 'carries', 'carry'),
    ('carted', 'carting', 'carts', 'cart'),
    ('carved', 'carving', 'carves', 'carve'),
    ('casting', 'casts', 'cast'),
    ('castrated', 'castrating', 'castrates', 'castrate'),
    ('caught', 'catching', 'catches', 'catch'),
    ('caused', 'causing', 'causes', 'cause'),
    ('cautioned', 'cautioning', 'cautions', 'caution'),
    ('ceased', 'ceasing', 'ceases', 'cease'),
    ('celebrated', 'celebrating', 'celebrates', 'celebrate'),
    ('chained', 'chaining', 'chains', 'chain'),
    ('challenged', 'challenging', 'challenges', 'challenge'),
    ('chanced', 'chancing', 'chances', 'chance'),
    ('changed', 'changing', 'changes', 'change'),
    ('chanted', 'chanting', 'chants', 'chant'),
    ('charged', 'charging', 'charges', 'charge'),
    ('charmed', 'charming', 'charms', 'charm'),
    ('chased', 'chasing', 'chases', 'chase'),
    ('chastened', 'chastening', 'chastens', 'chasten'),
    ('chastised', 'chastising', 'chastises', 'chastise'),
    ('cheated', 'cheating', 'cheats', 'cheat'),
    ('checked', 'checking', 'checks', 'check'),
    ('cheered', 'cheering', 'cheers', 'cheer'),
    ('cherished', 'cherishing', 'cherishes', 'cherish'),
    ('chewed', 'chewing', 'chews', 'chew'),
    ('chirped', 'chirping', 'chirps', 'chirp'),
    ('chiselled', 'chiselling', 'chisels', 'chisel'),
    ('choked', 'choking', 'chokes', 'choke'),
    ('chomped', 'chomping', 'chomps', 'chomp'),
    ('chose', 'chosen', 'choosing', 'chooses', 'choose'),
    ('chopped', 'chopping', 'chops', 'chop'),
    ('churned', 'churning', 'churns', 'churn'),
    ('circled', 'circling', 'circles', 'circle'),
    ('circumcised', 'circumcising', 'circumcises', 'circumcise'),
    ('claimed', 'claiming', 'claims', 'claim'),
    ('clamped', 'clamping', 'clamps', 'clamp'),
    ('clapped', 'clapping', 'claps', 'clap'),
    ('cleaned', 'cleaning', 'cleans', 'clean'),
    ('cleansed', 'cleansing', 'cleanses', 'cleanse'),
    ('cleared', 'clearing', 'clears', 'clear'),
    ('cleaved', 'clove', 'cleft', 'cloven', 'cleaving', 'cleaves', 'cleave'),
    ('climbed', 'climbing', 'climbs', 'climb'),
    ('clung', 'clinging', 'clings', 'cling'),
    ('clipped', 'clipping', 'clips', 'clip'),
    ('cloaked', 'cloaking', 'cloaks', 'cloak'),
    ('closed', 'closing', 'closes', 'close'),
    ('clothed', 'clad', 'clothing', 'clothes', 'clothe'),
    ('clutched', 'clutching', 'clutches', 'clutch'),
    ('collapsed', 'collapsing', 'collapses', 'collapse'),
    ('collected', 'collecting', 'collects', 'collect'),
    ('combed', 'combing', 'combs', 'comb'),
    ('combined', 'combining', 'combines', 'combine'),
    ('came', 'coming', 'comes', 'come'),
    ('comforted', 'comforting', 'comforts', 'comfort'),
    ('commanded', 'commanding', 'commands', 'command'),
    ('commandeered', 'commandeering', 'commandeers', 'commandeer'),
    ('commended', 'commending', 'commends', 'commend'),
    ('commented', 'commenting', 'comments', 'comment'),
    ('commissioned', 'commissioning', 'commissions', 'commission'),
    ('committed', 'committing', 'commits', 'commit'),
    ('communicated', 'communicating', 'communicates', 'communicate'),
    ('companied', 'companying', 'companies', 'company'),
    ('compared', 'comparing', 'compares', 'compare'),
    ('compelled', 'compelling', 'compels', 'compel'),
    ('competed', 'competing', 'competes', 'compete'),
    ('complained', 'complaining', 'complains', 'complain'),
    ('completed', 'completing', 'completes', 'complete'),
    ('complimented', 'complimenting', 'compliments', 'compliment'),
    ('complied', 'complying', 'complies', 'comply'),
    ('comprehended', 'comprehending', 'comprehends', 'comprehend'),
    ('concealed', 'concealing', 'conceals', 'conceal'),
    ('conceived', 'conceiving', 'conceives', 'conceive'),
    ('concerned', 'concerning', 'concerns', 'concern'),
    ('concluded', 'concluding', 'concludes', 'conclude'),
    ('concurred', 'concurring', 'concurs', 'concur'),
    ('condemned', 'condemning', 'condemns', 'condemn'),
    ('conducted', 'conducting', 'conducts', 'conduct'),
    ('conferred', 'conferring', 'confers', 'confer'),
    ('confessed', 'confessing', 'confesses', 'confess'),
    ('confined', 'confining', 'confines', 'confine'),
    ('confirmed', 'confirming', 'confirms', 'confirm'),
    ('confiscated', 'confiscating', 'confiscates', 'confiscate'),
    ('conformed', 'conforming', 'conforms', 'conform'),
    ('confounded', 'confounding', 'confounds', 'confound'),
    ('confronted', 'confronting', 'confronts', 'confront'),
    ('confused', 'confusing', 'confuses', 'confuse'),
    ('connected', 'connecting', 'connects', 'connect'),
    ('conquered', 'conquering', 'conquers', 'conquer'),
    ('conscripted', 'conscripting', 'conscripts', 'conscript'),
    ('consecrated', 'consecrating', 'consecrates', 'consecrate'),
    ('consented', 'consenting', 'consents', 'consent'),
    ('considered', 'considering', 'considers', 'consider'),
    ('consigned', 'consigning', 'consigns', 'consign'),
    ('consisted', 'consisting', 'consists', 'consist'),
    ('consoled', 'consoling', 'consoles', 'console'),
    ('conspired', 'conspiring', 'conspires', 'conspire'),
    ('constructed', 'constructing', 'constructs', 'construct'),
    ('consulted', 'consulting', 'consults', 'consult'),
    ('consumed', 'consuming', 'consumes', 'consume'),
    ('contacted', 'contacting', 'contacts', 'contact'),
    ('contained', 'containing', 'contains', 'contain'),
    ('contended', 'contending', 'contends', 'contend'),
    ('continued', 'continuing', 'continues', 'continue'),
    ('contracted', 'contracting', 'contracts', 'contract'),
    ('contradicted', 'contradicting', 'contradicts', 'contradict'),
    ('contributed', 'contributing', 'contributes', 'contribute'),
    ('contrived', 'contriving', 'contrives', 'contrive'),
    ('controlled', 'controlling', 'controls', 'control'),
    ('convened', 'convening', 'convenes', 'convene'),
    ('conversed', 'conversing', 'converses', 'converse'),
    ('converted', 'converting', 'converts', 'convert'),
    ('conveyed', 'conveying', 'conveys', 'convey'),
    ('convicted', 'convicting', 'convicts', 'convict'),
    ('convinced', 'convincing', 'convinces', 'convince'),
    ('convulsed', 'convulsing', 'convulses', 'convulse'),
    ('cooked', 'cooking', 'cooks', 'cook'),
    ('cooled', 'cooling', 'cools', 'cool'),
    ('cooperated', 'cooperating', 'cooperates', 'cooperate'),
    ('coped', 'coping', 'copes', 'cope'),
    ('copied', 'copying', 'copies', 'copy'),
    ('corrected', 'correcting', 'corrects', 'correct'),
    ('corresponded', 'corresponding', 'corresponds', 'correspond'),
    ('corroded', 'corroding', 'corrodes', 'corrode'),
    ('corrupted', 'corrupting', 'corrupts', 'corrupt'),
    ('costing', 'costs', 'cost'),
    ('counseled', 'counselled', 'counselling', 'counsels', 'counsel'),
    ('counted', 'counting', 'counts', 'count'),
    ('countered', 'countering', 'counters', 'counter'),
    ('coupled', 'coupling', 'couples', 'couple'),
    ('covenanted', 'covenanting', 'covenants', 'covenant'),
    ('covered', 'covering', 'covers', 'cover'),
    ('coveted', 'coveting', 'covets', 'covet'),
    ('cracked', 'cracking', 'cracks', 'crack'),
    ('crafted', 'crafting', 'crafts', 'craft'),
    ('crashed', 'crashing', 'crashes', 'crash'),
    ('craved', 'craving', 'craves', 'crave'),
    ('crawled', 'crawling', 'crawls', 'crawl'),
    ('created', 'creating', 'creates', 'create'),
    ('credited', 'crediting', 'credits', 'credit'),
    ('crept', 'creeping', 'creeps', 'creep'),
    ('cringed', 'cringing', 'cringes', 'cringe'),
    ('criticised', 'criticising', 'criticises', 'criticise'),
    ('crossed', 'crossing', 'crosses', 'cross'),
    ('crouched', 'crouching', 'crouches', 'crouch'),
    ('crowed', 'crowing', 'crows', 'crow'),
    ('crowded', 'crowding', 'crowds', 'crowd'),
    ('crowned', 'crowning', 'crowns', 'crown'),
    ('crumbled', 'crumbling', 'crumbles', 'crumble'),
    ('crushed', 'crushing', 'crushes', 'crush'),
    ('cried', 'crying', 'cries', 'cry'),
    ('cultivated', 'cultivating', 'cultivates', 'cultivate'),
    ('cupped', 'cupping', 'cups', 'cup'),
    ('curdled', 'curdling', 'curdles', 'curdle'),
    ('cured', 'curing', 'cures', 'cure'),
    ('cursed', 'cursing', 'curses', 'curse'),
    ('cutting', 'cuts', 'cut'),
    ('dabbled', 'dabbling', 'dabbles', 'dabble'),
    ('damaged', 'damaging', 'damages', 'damage'),
    ('danced', 'dancing', 'dances', 'dance'),
    ('dangled', 'dangling', 'dangles', 'dangle'),
    ('dared', 'daring', 'dares', 'dare'),
    ('darkened', 'darkening', 'darkens', 'darken'),
    ('darted', 'darting', 'darts', 'dart'),
    ('dashed', 'dashing', 'dashes', 'dash'),
    ('dawned', 'dawning', 'dawns', 'dawn'),
    ('dazed', 'dazing', 'dazes', 'daze'),
    ('dazzled', 'dazzling', 'dazzles', 'dazzle'),
    ('dealt', 'dealing', 'deals', 'deal'),
    ('debated', 'debating', 'debates', 'debate'),
    ('decayed', 'decaying', 'decays', 'decay'),
    ('deceived', 'deceiving', 'deceives', 'deceive'),
    ('decided', 'deciding', 'decides', 'decide'),
    ('decked', 'decking', 'decks', 'deck'),
    ('declared', 'declaring', 'declares', 'declare'),
    ('declined', 'declining', 'declines', 'decline'),
    ('decorated', 'decorating', 'decorates', 'decorate'),
    ('decreased', 'decreasing', 'decreases', 'decrease'),
    ('decreed', 'decreeing', 'decrees', 'decree'),
    ('dedicated', 'dedicating', 'dedicates', 'dedicate'),
    ('deeded', 'deeding', 'deeds', 'deed'),
    ('deemed', 'deeming', 'deems', 'deem'),
    ('defamed', 'defaming', 'defames', 'defame'),
    ('defeated', 'defeating', 'defeats', 'defeat'),
    ('defected', 'defecting', 'defects', 'defect'),
    ('defended', 'defending', 'defends', 'defend'),
    ('deferred', 'deferring', 'defers', 'defer'),
    ('defiled', 'defiling', 'defiles', 'defile'),
    ('defined', 'defining', 'defines', 'define'),
    ('deflected', 'deflecting', 'deflects', 'deflect'),
    ('defrauded', 'defrauding', 'defrauds', 'defraud'),
    ('defied', 'defying', 'defies', 'defy'),
    ('degraded', 'degrading', 'degrades', 'degrade'),
    ('delayed', 'delaying', 'delays', 'delay'),
    ('deliberated', 'deliberating', 'deliberates', 'deliberate'),
    ('delighted', 'delighting', 'delights', 'delight'),
    ('delivered', 'delivering', 'delivers', 'deliver'),
    ('deloused', 'delousing', 'delouses', 'delouse'),
    ('deluded', 'deluding', 'deludes', 'delude'),
    ('deluged', 'deluging', 'deluges', 'deluge'),
    ('demanded', 'demanding', 'demands', 'demand'),
    ('demeaned', 'demeaning', 'demeans', 'demean'),
    ('demolished', 'demolishing', 'demolishes', 'demolish'),
    ('demonstrated', 'demonstrating', 'demonstrates', 'demonstrate'),
    ('denounced', 'denouncing', 'denounces', 'denounce'),
    ('denied', 'denying', 'denies', 'deny'),
    ('departed', 'departing', 'departs', 'depart'),
    ('depended', 'depending', 'depends', 'depend'),
    ('deplored', 'deploring', 'deplores', 'deplore'),
    ('deployed', 'deploying', 'deploys', 'deploy'),
    ('deposed', 'deposing', 'deposes', 'depose'),
    ('deposited', 'depositing', 'deposits', 'deposit'),
    ('depressed', 'depressing', 'depresses', 'depress'),
    ('deprived', 'depriving', 'deprives', 'deprive'),
    ('derided', 'deriding', 'derides', 'deride'),
    ('descended', 'descending', 'descends', 'descend'),
    ('described', 'describing', 'describes', 'describe'),
    ('desecrated', 'desecrating', 'desecrates', 'desecrate'),
    ('deserted', 'deserting', 'deserts', 'desert'),
    ('deserved', 'deserving', 'deserves', 'deserve'),
    ('designed', 'designing', 'designs', 'design'),
    ('designated', 'designating', 'designates', 'designate'),
    ('desired', 'desiring', 'desires', 'desire'),
    ('desolated', 'desolating', 'desolates', 'desolate'),
    ('despaired', 'despairing', 'despairs', 'despair'),
    ('despised', 'despising', 'despises', 'despise'),
    ('despoiled', 'despoiling', 'despoils', 'despoil'),
    ('destroyed', 'destroying', 'destroys', 'destroy'),
    ('detailed', 'detailing', 'details', 'detail'),
    ('detained', 'detaining', 'detains', 'detain'),
    ('detected', 'detecting', 'detects', 'detect'),
    ('deteriorated', 'deteriorating', 'deteriorates', 'deteriorate'),
    ('determined', 'determining', 'determines', 'determine'),
    ('detested', 'detesting', 'detests', 'detest'),
    ('devastated', 'devastating', 'devastates', 'devastate'),
    ('developed', 'developing', 'develops', 'develop'),
    ('deviated', 'deviating', 'deviates', 'deviate'),
    ('devised', 'devising', 'devises', 'devise'),
    ('devoted', 'devoting', 'devotes', 'devote'),
    ('devoured', 'devouring', 'devours', 'devour'),
    ('died', 'dying', 'dies', 'die'),
    ('differed', 'differing', 'differs', 'differ'),
    ('dug', 'digging', 'digs', 'dig'),
    ('dimmed', 'dimming', 'dims', 'dim'),
    ('diminished', 'diminishing', 'diminishes', 'diminish'),
    ('dined', 'dining', 'dines', 'dine'),
    ('dipped', 'dipping', 'dips', 'dip'),
    ('directed', 'directing', 'directs', 'direct'),
    ('disadvantaged', 'disadvantaging', 'disadvantages', 'disadvantage'),
    ('disagreed', 'disagreeing', 'disagrees', 'disagree'),
    ('disappeared', 'disappearing', 'disappears', 'disappear'),
    ('disappointed', 'disappointing', 'disappoints', 'disappoint'),
    ('disassembled', 'disassembling', 'disassembles', 'disassemble'),
    ('disbelieved', 'disbelieving', 'disbelieves', 'disbelieve'),
    ('discarded', 'discarding', 'discards', 'discard'),
    ('discerned', 'discerning', 'discerns', 'discern'),
    ('discharged', 'discharging', 'discharges', 'discharge'),
    ('disciplined', 'disciplining', 'disciplines', 'discipline'),
    ('disclosed', 'disclosing', 'discloses', 'disclose'),
    ('disconcerted', 'disconcerting', 'disconcerts', 'disconcert'),
    ('discouraged', 'discouraging', 'discourages', 'discourage'),
    ('discovered', 'discovering', 'discovers', 'discover'),
    ('discredited', 'discrediting', 'discredits', 'discredit'),
    ('discussed', 'discussing', 'discusses', 'discuss'),
    ('disdained', 'disdaining', 'disdains', 'disdain'),
    ('disfigured', 'disfiguring', 'disfigures', 'disfigure'),
    ('disgraced', 'disgracing', 'disgraces', 'disgrace'),
    ('disguised', 'disguising', 'disguises', 'disguise'),
    ('disgusted', 'disgusting', 'disgusts', 'disgust'),
    ('dished', 'dishing', 'dishes', 'dish'),
    ('dishonoured', 'dishonouring', 'dishonours', 'dishonour'),
    ('disintegrated', 'disintegrating', 'disintegrates', 'disintegrate'),
    ('disliked', 'disliking', 'dislikes', 'dislike'),
    ('dismayed', 'dismaying', 'dismays', 'dismay'),
    ('dismembered', 'dismembering', 'dismembers', 'dismember'),
    ('dismissed', 'dismissing', 'dismisses', 'dismiss'),
    ('disobeyed', 'disobeying', 'disobeys', 'disobey'),
    ('disowned', 'disowning', 'disowns', 'disown'),
    ('dispensed', 'dispensing', 'dispenses', 'dispense'),
    ('dispersed', 'dispersing', 'disperses', 'disperse'),
    ('displaced', 'displacing', 'displaces', 'displace'),
    ('displayed', 'displaying', 'displays', 'display'),
    ('displeased', 'displeasing', 'displeases', 'displease'),
    ('disposed', 'disposing', 'disposes', 'dispose'),
    ('dispossessed', 'dispossessing', 'dispossesses', 'dispossess'),
    ('disputed', 'disputing', 'disputes', 'dispute'),
    ('disqualified', 'disqualifying', 'disqualifies', 'disqualify'),
    ('disquieted', 'disquieting', 'disquiets', 'disquiet'),
    ('disregarded', 'disregarding', 'disregards', 'disregard'),
    ('disrespected', 'disrespecting', 'disrespects', 'disrespect'),
    ('dissolved', 'dissolving', 'dissolves', 'dissolve'),
    ('distanced', 'distancing', 'distances', 'distance'),
    ('distinguished', 'distinguishing', 'distinguishes', 'distinguish'),
    ('distracted', 'distracting', 'distracts', 'distract'),
    ('distressed', 'distressing', 'distresses', 'distress'),
    ('distributed', 'distributing', 'distributes', 'distribute'),
    ('disturbed', 'disturbing', 'disturbs', 'disturb'),
    ('dived', 'dove', 'diving', 'dives', 'dive'),
    ('diverted', 'diverting', 'diverts', 'divert'),
    ('divided', 'dividing', 'divides', 'divide'),
    ('divined', 'divining', 'divines', 'divine'),
    ('divorced', 'divorcing', 'divorces', 'divorce'),
    ('divulged', 'divulging', 'divulges', 'divulge'),
    ('did', 'done', 'doing', 'does', 'do'),
    ('dominated', 'dominating', 'dominates', 'dominate'),
    ('domineered', 'domineering', 'domineers', 'domineer'),
    ('donated', 'donating', 'donates', 'donate'),
    ('doomed', 'dooming', 'dooms', 'doom'),
    ('doubled', 'doubling', 'doubles', 'double'),
    ('double-checked', 'double-checking', 'double-checks', 'double-check'),
    ('doubted', 'doubting', 'doubts', 'doubt'),
    ('dragged', 'dragging', 'drags', 'drag'),
    ('drained', 'draining', 'drains', 'drain'),
    ('drew', 'drawn', 'drawing', 'draws', 'draw'),
    ('dreaded', 'dreading', 'dreads', 'dread'),
    ('dreamed', 'dreamt', 'dreaming', 'dreams', 'dream'),
    ('drenched', 'drenching', 'drenches', 'drench'),
    ('dressed', 'dressing', 'dresses', 'dress'),
    ('drifted', 'drifting', 'drifts', 'drift'),
    ('drank', 'drunk', 'drinking', 'drinks', 'drink'),
    ('dripped', 'dripping', 'drips', 'drip'),
    ('drove', 'driven', 'driving', 'drives', 'drive'),
    ('dropped', 'dropping', 'drops', 'drop'),
    ('drowned', 'drowning', 'drowns', 'drown'),
    ('dried', 'drying', 'dries', 'dry'),
    ('dumped', 'dumping', 'dumps', 'dump'),
    ('dusted', 'dusting', 'dusts', 'dust'),
    ('dwelled', 'dwelt', 'dwelling', 'dwells', 'dwell'),
    ('dyed', 'dyeing', 'dyes', 'dye'),
    ('earned', 'earning', 'earns', 'earn'),
    ('ate', 'eaten', 'eating', 'eats', 'eat'),
    ('echoed', 'echoing', 'echoes', 'echo'),
    ('elected', 'electing', 'elects', 'elect'),
    ('elevated', 'elevating', 'elevates', 'elevate'),
    ('eliminated', 'eliminating', 'eliminates', 'eliminate'),
    ('eluded', 'eluding', 'eludes', 'elude'),
    ('emanated', 'emanating', 'emanates', 'emanate'),
    ('embalmed', 'embalming', 'embalms', 'embalm'),
    ('embarrassed', 'embarrassing', 'embarrasses', 'embarrass'),
    ('embezzled', 'embezzling', 'embezzles', 'embezzle'),
    ('embraced', 'embracing', 'embraces', 'embrace'),
    ('embroidered', 'embroidering', 'embroiders', 'embroider'),
    ('emerged', 'emerging', 'emerges', 'emerge'),
    ('employed', 'employing', 'employs', 'employ'),
    ('empowered', 'empowering', 'empowers', 'empower'),
    ('emptied', 'emptying', 'empties', 'empty'),
    ('enabled', 'enabling', 'enables', 'enable'),
    ('enacted', 'enacting', 'enacts', 'enact'),
    ('encamped', 'encamping', 'encamps', 'encamp'),
    ('encircled', 'encircling', 'encircles', 'encircle'),
    ('enclosed', 'enclosing', 'encloses', 'enclose'),
    ('encompassed', 'encompassing', 'encompasses', 'encompass'),
    ('encountered', 'encountering', 'encounters', 'encounter'),
    ('encouraged', 'encouraging', 'encourages', 'encourage'),
    ('ended', 'ending', 'ends', 'end'),
    ('endangered', 'endangering', 'endangers', 'endanger'),
    ('endeavoured', 'endeavouring', 'endeavours', 'endeavour'),
    ('endured', 'enduring', 'endures', 'endure'),
    ('enforced', 'enforcing', 'enforces', 'enforce'),
    ('engaged', 'engaging', 'engages', 'engage'),
    ('engrafted', 'engrafting', 'engrafts', 'engraft'),
    ('engraved', 'engraving', 'engraves', 'engrave'),
    ('engulfed', 'engulfing', 'engulfs', 'engulf'),
    ('enhanced', 'enhancing', 'enhances', 'enhance'),
    ('enjoyed', 'enjoying', 'enjoys', 'enjoy'),
    ('enlarged', 'enlarging', 'enlarges', 'enlarge'),
    ('enlightened', 'enlightening', 'enlightens', 'enlighten'),
    ('enquired', 'enquiring', 'enquires', 'enquire'),
    ('enriched', 'enriching', 'enriches', 'enrich'),
    ('enrolled', 'enrolling', 'enrols', 'enrolls', 'enroll', 'enrol'),
    ('enslaved', 'enslaving', 'enslaves', 'enslave'),
    ('ensnared', 'ensnaring', 'ensnares', 'ensnare'),
    ('ensued', 'ensuing', 'ensues', 'ensue'),
    ('ensured', 'ensuring', 'ensures', 'ensure'),
    ('entangled', 'entangling', 'entangles', 'entangle'),
    ('entered', 'entering', 'enters', 'enter'),
    ('entertained', 'entertaining', 'entertains', 'entertain'),
    ('enthroned', 'enthroning', 'enthrones', 'enthrone'),
    ('enticed', 'enticing', 'entices', 'entice'),
    ('entreated', 'entreating', 'entreats', 'entreat'),
    ('entrusted', 'entrusting', 'entrusts', 'entrust'),
    ('enveloped', 'enveloping', 'envelops', 'envelop'),
    ('envisioned', 'envisioning', 'envisions', 'envision'),
    ('envied', 'envying', 'envies', 'envy'),
    ('equalled', 'equalling', 'equals', 'equal'),
    ('equipped', 'equipping', 'equips', 'equip'),
    ('erased', 'erasing', 'erases', 'erase'),
    ('erected', 'erecting', 'erects', 'erect'),
    ('erred', 'erring', 'errs', 'err'),
    ('escaped', 'escaping', 'escapes', 'escape'),
    ('escorted', 'escorting', 'escorts', 'escort'),
    ('established', 'establishing', 'establishes', 'establish'),
    ('esteemed', 'esteeming', 'esteems', 'esteem'),
    ('estranged', 'estranging', 'estranges', 'estrange'),
    ('evaluated', 'evaluating', 'evaluates', 'evaluate'),
    ('evangelized', 'evangelizing', 'evangelizes', 'evangelize', 'evangelised', 'evangelising', 'evangelises', 'evangelise'),
    ('evicted', 'evicting', 'evicts', 'evict'),
    ('exacted', 'exacting', 'exacts', 'exact'),
    ('exalted', 'exalting', 'exalts', 'exalt'),
    ('examined', 'examining', 'examines', 'examine'),
    ('exasperated', 'exasperating', 'exasperates', 'exasperate'),
    ('exceeded', 'exceeding', 'exceeds', 'exceed'),
    ('excelled', 'excelling', 'excels', 'excel'),
    ('exchanged', 'exchanging', 'exchanges', 'exchange'),
    ('excited', 'exciting', 'excites', 'excite'),
    ('exclaimed', 'exclaiming', 'exclaims', 'exclaim'),
    ('excluded', 'excluding', 'excludes', 'exclude'),
    ('excused', 'excusing', 'excuses', 'excuse'),
    ('executed', 'executing', 'executes', 'execute'),
    ('exercised', 'exercising', 'exercises', 'exercise'),
    ('exerted', 'exerting', 'exerts', 'exert'),
    ('exhibited', 'exhibiting', 'exhibits', 'exhibit'),
    ('exhorted', 'exhorting', 'exhorts', 'exhort'),
    ('exiled', 'exiling', 'exiles', 'exile'),
    ('existed', 'existing', 'exists', 'exist'),
    ('exited', 'exiting', 'exits', 'exit'),
    ('expanded', 'expanding', 'expands', 'expand'),
    ('expected', 'expecting', 'expects', 'expect'),
    ('expelled', 'expelling', 'expels', 'expel'),
    ('experienced', 'experiencing', 'experiences', 'experience'),
    ('expired', 'expiring', 'expires', 'expire'),
    ('explained', 'explaining', 'explains', 'explain'),
    ('exploited', 'exploiting', 'exploits', 'exploit'),
    ('explored', 'exploring', 'explores', 'explore'),
    ('exposed', 'exposing', 'exposes', 'expose'),
    ('expressed', 'expressing', 'expresses', 'express'),
    ('extended', 'extending', 'extends', 'extend'),
    ('exterminated', 'exterminating', 'exterminates', 'exterminate'),
    ('extinguished', 'extinguishing', 'extinguishes', 'extinguish'),
    ('extolled', 'extolling', 'extols', 'extol'),
    ('extracted', 'extracting', 'extracts', 'extract'),
    ('exulted', 'exulting', 'exults', 'exult'),
    ('eyed', 'eyeing', 'eyes', 'eye'),
    ('fabricated', 'fabricating', 'fabricates', 'fabricate'),
    ('faced', 'facing', 'faces', 'face'),
    ('faded', 'fading', 'fades', 'fade'),
    ('failed', 'failing', 'fails', 'fail'),
    ('fainted', 'fainting', 'faints', 'faint'),
    ('fell', 'fallen', 'falling', 'falls', 'fall'),
    ('falsified', 'falsifying', 'falsifies', 'falsify'),
    ('faltered', 'faltering', 'falters', 'falter'),
    ('farewelled', 'farewelling', 'farewells', 'farewell'),
    ('farmed', 'farming', 'farms', 'farm'),
    ('fashioned', 'fashioning', 'fashions', 'fashion'),
    ('fasted', 'fasting', 'fasts', 'fast'),
    ('fastened', 'fastening', 'fastens', 'fasten'),
    ('fathered', 'fathering', 'fathers', 'father'),
    ('fattened', 'fattening', 'fattens', 'fatten'),
    ('favoured', 'favouring', 'favours', 'favor', 'favour'),
    ('feared', 'fearing', 'fears', 'fear'),
    ('feasted', 'feasting', 'feasts', 'feast'),
    ('fed', 'feeding', 'feeds', 'feed'),
    ('felt', 'feeling', 'feels', 'feel'),
    ('felled', 'felling', 'fells', 'fell'),
    ('fenced', 'fencing', 'fences', 'fence'),
    ('festered', 'festering', 'festers', 'fester'),
    ('fetched', 'fetching', 'fetches', 'fetch'),
    ('fettered', 'fettering', 'fetters', 'fetter'),
    ('fought', 'fighting', 'fights', 'fight'),
    ('figured', 'figuring', 'figures', 'figure'),
    ('filled', 'filling', 'fills', 'fill'),
    ('found', 'finding', 'finds', 'find'),
    ('fined', 'fining', 'fines', 'fine'),
    ('finished', 'finishing', 'finishes', 'finish'),
    ('fired', 'firing', 'fires', 'fire'),
    ('firmed', 'firming', 'firms', 'firm'),
    ('fished', 'fishing', 'fishes', 'fish'),
    ('fitted', 'fitting', 'fits', 'fit'),
    ('fixed', 'fixing', 'fixes', 'fix'),
    ('flaked', 'flaking', 'flakes', 'flake'),
    ('flamed', 'flaming', 'flames', 'flame'),
    ('flapped', 'flapping', 'flaps', 'flap'),
    ('flared', 'flaring', 'flares', 'flare'),
    ('flashed', 'flashing', 'flashes', 'flash'),
    ('flattened', 'flattening', 'flattens', 'flatten'),
    ('flattered', 'flattering', 'flatters', 'flatter'),
    ('fled', 'fleeing', 'flees', 'flee'),
    ('flicked', 'flicking', 'flicks', 'flick'),
    ('flung', 'flinging', 'flings', 'fling'),
    ('flirted', 'flirting', 'flirts', 'flirt'),
    ('floated', 'floating', 'floats', 'float'),
    ('flogged', 'flogging', 'flogs', 'flog'),
    ('flooded', 'flooding', 'floods', 'flood'),
    ('flourished', 'flourishing', 'flourishes', 'flourish'),
    ('flowed', 'flowing', 'flows', 'flow'),
    ('flowered', 'flowering', 'flowers', 'flower'),
    ('fluttered', 'fluttering', 'flutters', 'flutter'),
    ('flew', 'flown', 'flying', 'flies', 'fly'),
    ('foamed', 'foaming', 'foams', 'foam'),
    ('focused', 'focusing', 'focuses', 'focus'),
    ('folded', 'folding', 'folds', 'fold'),
    ('followed', 'following', 'follows', 'follow'),
    ('fooled', 'fooling', 'fools', 'fool'),
    ('forbore', 'forborne', 'forbearing', 'forbears', 'forbear'),
    ('forbade', 'forbidden', 'forbidding', 'forbids', 'forbid'),
    ('forced', 'forcing', 'forces', 'force'),
    ('foreknew', 'foreknown', 'foreknowing', 'foreknows', 'foreknow'),
    ('foresaw', 'foreseen', 'foreseeing', 'foresees', 'foresee'),
    ('foretold', 'foretelling', 'foretells', 'foretell'),
    ('forfeited', 'forfeiting', 'forfeits', 'forfeit'),
    ('forged', 'forging', 'forges', 'forge'),
    ('forgot', 'forgotten', 'forgetting', 'forgets', 'forget'),
    ('forgave', 'forgiven', 'forgiving', 'forgives', 'forgive'),
    ('formed', 'forming', 'forms', 'form'),
    ('fornicated', 'fornicating', 'fornicates', 'fornicate'),
    ('forsook', 'forsaken', 'forsaking', 'forsakes', 'forsake'),
    ('fortified', 'fortifying', 'fortifies', 'fortify'),
    ('forwarded', 'forwarding', 'forwards', 'forward'),
    ('fouled', 'fouling', 'fouls', 'foul'),
    ('founded', 'founding', 'founds', 'found'),
    ('freed', 'freeing', 'frees', 'free'),
    ('froze', 'frozen', 'freezing', 'freezes', 'freeze'),
    ('frequented', 'frequenting', 'frequents', 'frequent'),
    ('frighted', 'frighting', 'frights', 'fright'),
    ('frightened', 'frightening', 'frightens', 'frighten'),
    ('frustrated', 'frustrating', 'frustrates', 'frustrate'),
    ('fulfilled', 'fulfilling', 'fulfils', 'fulfills', 'fulfill', 'fulfil'),
    ('functioned', 'functioning', 'functions', 'function'),
    ('furnished', 'furnishing', 'furnishes', 'furnish'),
    ('furthered', 'furthering', 'furthers', 'further'),
    ('gained', 'gaining', 'gains', 'gain'),
    ('gaped', 'gaping', 'gapes', 'gape'),
    ('garlanded', 'garlanding', 'garlands', 'garland'),
    ('gasped', 'gasping', 'gasps', 'gasp'),
    ('gathered', 'gathering', 'gathers', 'gather'),
    ('gazed', 'gazing', 'gazes', 'gaze'),
    ('got', 'gotten', 'getting', 'gets', 'get'),
    ('gifted', 'gifting', 'gifts', 'gift'),
    ('girded', 'girding', 'girds', 'gird'),
    ('gave', 'given', 'giving', 'gives', 'give'),
    ('gladdened', 'gladdening', 'gladdens', 'gladden'),
    ('glanced', 'glancing', 'glances', 'glance'),
    ('gleamed', 'gleaming', 'gleams', 'gleam'),
    ('gleaned', 'gleaning', 'gleans', 'glean'),
    ('glided', 'gliding', 'glides', 'glide'),
    ('gloated', 'gloating', 'gloats', 'gloat'),
    ('glorified', 'glorifying', 'glorifies', 'glorify'),
    ('gloried', 'glorying', 'glories', 'glory'),
    ('glowed', 'glowing', 'glows', 'glow'),
    ('gnashed', 'gnashing', 'gnashes', 'gnash'),
    ('gnawed', 'gnawing', 'gnaws', 'gnaw'),
    ('went', 'gone', 'going', 'goes', 'go'),
    ('gored', 'goring', 'gores', 'gore'),
    ('gorged', 'gorging', 'gorges', 'gorge'),
    ('gossipping', 'gossiped', 'gossiping', 'gossips', 'gossip'),
    ('gouged', 'gouging', 'gouges', 'gouge'),
    ('governed', 'governing', 'governs', 'govern'),
    ('grabbed', 'grabbing', 'grabs', 'grab'),
    ('granted', 'granting', 'grants', 'grant'),
    ('grasped', 'grasping', 'grasps', 'grasp'),
    ('gratified', 'gratifying', 'gratifies', 'gratify'),
    ('grazed', 'grazing', 'grazes', 'graze'),
    ('greeted', 'greeting', 'greets', 'greet'),
    ('grieved', 'grieving', 'grieves', 'grieve'),
    ('ground', 'grinding', 'grinds', 'grind'),
    ('gripped', 'gripping', 'grips', 'grip'),
    ('groaned', 'groaning', 'groans', 'groan'),
    ('groped', 'groping', 'gropes', 'grope'),
    ('grounded', 'grounding', 'grounds', 'ground'),
    ('grouped', 'grouping', 'groups', 'group'),
    ('grew', 'grown', 'growing', 'grows', 'grow'),
    ('growled', 'growling', 'growls', 'growl'),
    ('grumbled', 'grumbling', 'grumbles', 'grumble'),
    ('guaranteed', 'guaranteeing', 'guarantees', 'guarantee'),
    ('guarded', 'guarding', 'guards', 'guard'),
    ('guided', 'guiding', 'guides', 'guide'),
    ('gushed', 'gushing', 'gushes', 'gush'),
    ('halted', 'halting', 'halts', 'halt'),
    ('hammered', 'hammering', 'hammers', 'hammer'),
    ('hamstrung', 'hamstringing', 'hamstrings', 'hamstring'),
    ('handed', 'handing', 'hands', 'hand'),
    ('handled', 'handling', 'handles', 'handle'),
    ('hung', 'hanged', 'hanging', 'hangs', 'hang'),
    ('happened', 'happening', 'happens', 'happen'),
    ('harassed', 'harassing', 'harasses', 'harass'),
    ('harboured', 'harbouring', 'harbours', 'harbour'),
    ('hardened', 'hardening', 'hardens', 'harden'),
    ('harmed', 'harming', 'harms', 'harm'),
    ('harnessed', 'harnessing', 'harnesses', 'harness'),
    ('harvested', 'harvesting', 'harvests', 'harvest'),
    ('hassled', 'hassling', 'hassles', 'hassle'),
    ('hastened', 'hastening', 'hastens', 'hasten'),
    ('hatched', 'hatching', 'hatches', 'hatch'),
    ('hated', 'hating', 'hates', 'hate'),
    ('hauled', 'hauling', 'hauls', 'haul'),
    ('had', 'having', 'has', 'have'),
    ('headed', 'heading', 'heads', 'head'),
    ('healed', 'healing', 'heals', 'heal'),
    ('heaped', 'heaping', 'heaps', 'heap'),
    ('heard', 'hearing', 'hears', 'hear'),
    ('heated', 'heating', 'heats', 'heat'),
    ('heaved', 'hove', 'heaving', 'heaves', 'heave'),
    ('hedged', 'hedging', 'hedges', 'hedge'),
    ('heeded', 'heeding', 'heeds', 'heed'),
    ('helped', 'helping', 'helps', 'help'),
    ('hemmed', 'hemming', 'hems', 'hem'),
    ('herded', 'herding', 'herds', 'herd'),
    ('hesitated', 'hesitating', 'hesitates', 'hesitate'),
    ('hewed', 'hewn', 'hewing', 'hews', 'hew'),
    ('hid', 'hidden', 'hiding', 'hides', 'hide'),
    ('highlighted', 'highlighting', 'highlights', 'highlight'),
    ('hindered', 'hindering', 'hinders', 'hinder'),
    ('hired', 'hiring', 'hires', 'hire'),
    ('hissed', 'hissing', 'hisses', 'hiss'),
    ('hitting', 'hits', 'hit'),
    ('hitched', 'hitching', 'hitches', 'hitch'),
    ('hoarded', 'hoarding', 'hoards', 'hoard'),
    ('hoed', 'hoeing', 'hoes', 'hoe'),
    ('held', 'holding', 'holds', 'hold'),
    ('hollowed', 'hollowing', 'hollows', 'hollow'),
    ('honoured', 'honouring', 'honours', 'honored', 'honoring', 'honors', 'honor', 'honour'),
    ('hooked', 'hooking', 'hooks', 'hook'),
    ('hopped', 'hopping', 'hops', 'hop'),
    ('hoped', 'hoping', 'hopes', 'hope'),
    ('horrified', 'horrifying', 'horrifies', 'horrify'),
    ('hosted', 'hosting', 'hosts', 'host'),
    ('hovered', 'hovering', 'hovers', 'hover'),
    ('howled', 'howling', 'howls', 'howl'),
    ('huddled', 'huddling', 'huddles', 'huddle'),
    ('hugged', 'hugging', 'hugs', 'hug'),
    ('humbled', 'humbling', 'humbles', 'humble'),
    ('humiliated', 'humiliating', 'humiliates', 'humiliate'),
    ('hungered', 'hungering', 'hungers', 'hunger'),
    ('hunted', 'hunting', 'hunts', 'hunt'),
    ('hurled', 'hurling', 'hurls', 'hurl'),
    ('hurried', 'hurrying', 'hurries', 'hurry'),
    ('hurting', 'hurts', 'hurt'),
    ('hushed', 'hushing', 'hushes', 'hush'),
    ('identified', 'identifying', 'identifies', 'identify'),
    ('idled', 'idling', 'idles', 'idle'),
    ('ignited', 'igniting', 'ignites', 'ignite'),
    ('ignored', 'ignoring', 'ignores', 'ignore'),
    ('illuminated', 'illuminating', 'illuminates', 'illuminate'),
    ('imagined', 'imagining', 'imagines', 'imagine'),
    ('imitated', 'imitating', 'imitates', 'imitate'),
    ('immersed', 'immersing', 'immerses', 'immerse'),
    ('impaled', 'impaling', 'impales', 'impale'),
    ('imparted', 'imparting', 'imparts', 'impart'),
    ('impelled', 'impelling', 'impels', 'impel'),
    ('implemented', 'implementing', 'implements', 'implement'),
    ('implored', 'imploring', 'implores', 'implore'),
    ('imported', 'importing', 'imports', 'import'),
    ('imposed', 'imposing', 'imposes', 'impose'),
    ('impoverished', 'impoverishing', 'impoverishes', 'impoverish'),
    ('impregnated', 'impregnating', 'impregnates', 'impregnate'),
    ('impressed', 'impressing', 'impresses', 'impress'),
    ('imprisoned', 'imprisoning', 'imprisons', 'imprison'),
    ('improved', 'improving', 'improves', 'improve'),
    ('imputed', 'imputing', 'imputes', 'impute'),
    ('incensed', 'incensing', 'incenses', 'incense'),
    ('incinerated', 'incinerating', 'incinerates', 'incinerate'),
    ('incited', 'inciting', 'incites', 'incite'),
    ('inclined', 'inclining', 'inclines', 'incline'),
    ('included', 'including', 'includes', 'include'),
    ('increased', 'increasing', 'increases', 'increase'),
    ('indicated', 'indicating', 'indicates', 'indicate'),
    ('indicted', 'indicting', 'indicts', 'indict'),
    ('induced', 'inducing', 'induces', 'induce'),
    ('indulged', 'indulging', 'indulges', 'indulge'),
    ('inflamed', 'inflaming', 'inflames', 'inflame'),
    ('inflicted', 'inflicting', 'inflicts', 'inflict'),
    ('influenced', 'influencing', 'influences', 'influence'),
    ('informed', 'informing', 'informs', 'inform'),
    ('infuriated', 'infuriating', 'infuriates', 'infuriate'),
    ('inhabited', 'inhabiting', 'inhabits', 'inhabit'),
    ('inherited', 'inheriting', 'inherits', 'inherit'),
    ('initiated', 'initiating', 'initiates', 'initiate'),
    ('injured', 'injuring', 'injures', 'injure'),
    ('inquired', 'inquiring', 'inquires', 'inquire'),
    ('inscribed', 'inscribing', 'inscribes', 'inscribe'),
    ('insisted', 'insisting', 'insists', 'insist'),
    ('inspected', 'inspecting', 'inspects', 'inspect'),
    ('inspired', 'inspiring', 'inspires', 'inspire'),
    ('installed', 'installing', 'installs', 'install'),
    ('instructed', 'instructing', 'instructs', 'instruct'),
    ('insulted', 'insulting', 'insults', 'insult'),
    ('integrated', 'integrating', 'integrates', 'integrate'),
    ('intended', 'intending', 'intends', 'intend'),
    ('interacted', 'interacting', 'interacts', 'interact'),
    ('interceded', 'interceding', 'intercedes', 'intercede'),
    ('intermarried', 'intermarrying', 'intermarries', 'intermarry'),
    ('internalised', 'internalising', 'internalises', 'internalise'),
    ('interpreted', 'interpreting', 'interprets', 'interpret'),
    ('interrogated', 'interrogating', 'interrogates', 'interrogate'),
    ('interrupted', 'interrupting', 'interrupts', 'interrupt'),
    ('intervened', 'intervening', 'intervenes', 'intervene'),
    ('interviewed', 'interviewing', 'interviews', 'interview'),
    ('intoxicated', 'intoxicating', 'intoxicates', 'intoxicate'),
    ('introduced', 'introducing', 'introduces', 'introduce'),
    ('invaded', 'invading', 'invades', 'invade'),
    ('invalidated', 'invalidating', 'invalidates', 'invalidate'),
    ('invented', 'inventing', 'invents', 'invent'),
    ('invested', 'investing', 'invests', 'invest'),
    ('investigated', 'investigating', 'investigates', 'investigate'),
    ('invited', 'inviting', 'invites', 'invite'),
    ('invoked', 'invoking', 'invokes', 'invoke'),
    ('involved', 'involving', 'involves', 'involve'),
    ('irritated', 'irritating', 'irritates', 'irritate'),
    ('issued', 'issuing', 'issues', 'issue'),
    ('jested', 'jesting', 'jests', 'jest'),
    ('joined', 'joining', 'joins', 'join'),
    ('joked', 'joking', 'jokes', 'joke'),
    ('jolted', 'jolting', 'jolts', 'jolt'),
    ('journeyed', 'journeying', 'journeys', 'journey'),
    ('judged', 'judging', 'judges', 'judge'),
    ('jumped', 'jumping', 'jumps', 'jump'),
    ('justified', 'justifying', 'justifies', 'justify'),
    ('kept', 'keeping', 'keeps', 'keep'),
    ('kicked', 'kicking', 'kicks', 'kick'),
    ('killed', 'killing', 'kills', 'kill'),
    ('kindled', 'kindling', 'kindles', 'kindle'),
    ('kissed', 'kissing', 'kisses', 'kiss'),
    ('kneaded', 'kneading', 'kneads', 'knead'),
    ('knelt', 'kneeled', 'kneeling', 'kneels', 'kneel'),
    ('knocked', 'knocking', 'knocks', 'knock'),
    ('knew', 'known', 'knowing', 'knows', 'know'),
    ('laboured', 'labouring', 'labours', 'labour'),
    ('lacked', 'lacking', 'lacks', 'lack'),
    ('lamented', 'lamenting', 'laments', 'lament'),
    ('landed', 'landing', 'lands', 'land'),
    ('languished', 'languishing', 'languishes', 'languish'),
    ('lapped', 'lapping', 'laps', 'lap'),
    ('lashed', 'lashing', 'lashes', 'lash'),
    ('lasted', 'lasting', 'lasts', 'last'),
    ('laughed', 'laughing', 'laughs', 'laugh'),
    ('laid', 'laying', 'lays', 'lay'),
    ('led', 'leading', 'leads', 'lead'),
    ('leaked', 'leaking', 'leaks', 'leak'),
    ('leant', 'leaned', 'leaning', 'leans', 'lean'),
    ('leapt', 'leaped', 'leaping', 'leaps', 'leap'),
    ('learnt', 'learning', 'learns', 'learned', 'learn'),
    ('left', 'leaving', 'leaves', 'leave'),
    ('leavened', 'leavening', 'leavens', 'leaven'),
    ('lent', 'lending', 'lends', 'lend'),
    ('lengthened', 'lengthening', 'lengthens', 'lengthen'),
    ('letting', 'lets', 'let'),
    ('leveling', 'levelled', 'levelling', 'levels', 'level'),
    ('levied', 'levying', 'levies', 'levy'),
    ('liberated', 'liberating', 'liberates', 'liberate'),
    ('licked', 'licking', 'licks', 'lick'),
    ('lay', 'lain', 'lying', 'lies', 'lied', 'lie'),
    ('lifted', 'lifting', 'lifts', 'lift'),
    ('lit', 'lighted', 'lighting', 'lights', 'light'),
    ('lightened', 'lightening', 'lightens', 'lighten'),
    ('liked', 'liking', 'likes', 'like'),
    ('likened', 'likening', 'likens', 'liken'),
    ('limited', 'limiting', 'limits', 'limit'),
    ('limped', 'limping', 'limps', 'limp'),
    ('lined', 'lining', 'lines', 'line'),
    ('listed', 'listing', 'lists', 'list'),
    ('listened', 'listening', 'listens', 'listen'),
    ('lived', 'living', 'lives', 'live'),
    ('loaded', 'loading', 'loads', 'load'),
    ('loafed', 'loafing', 'loafs', 'loaf'),
    ('loaned', 'loaning', 'loans', 'loan'),
    ('loathed', 'loathing', 'loathes', 'loathe'),
    ('locked', 'locking', 'locks', 'lock'),
    ('lodged', 'lodging', 'lodges', 'lodge'),
    ('longed', 'longing', 'longs', 'long'),
    ('looked', 'looking', 'looks', 'look'),
    ('loomed', 'looming', 'looms', 'loom'),
    ('loosened', 'loosening', 'loosens', 'loosen'),
    ('looted', 'looting', 'loots', 'loot'),
    ('lorded', 'lording', 'lords', 'lord'),
    ('lost', 'losing', 'loses', 'lose'),
    ('lounged', 'lounging', 'lounges', 'lounge'),
    ('loved', 'loving', 'loves', 'love'),
    ('lowed', 'lowing', 'lows', 'low'),
    ('lowered', 'lowering', 'lowers', 'lower'),
    ('lured', 'luring', 'lures', 'lure'),
    ('lurked', 'lurking', 'lurks', 'lurk'),
    ('lusted', 'lusting', 'lusts', 'lust'),
    ('magnified', 'magnifying', 'magnifies', 'magnify'),
    ('maimed', 'maiming', 'maims', 'maim'),
    ('maintained', 'maintaining', 'maintains', 'maintain'),
    ('made', 'making', 'makes', 'make'),
    ('maltreated', 'maltreating', 'maltreats', 'maltreat'),
    ('managed', 'managing', 'manages', 'manage'),
    ('manifested', 'manifesting', 'manifests', 'manifest'),
    ('manufactured', 'manufacturing', 'manufactures', 'manufacture'),
    ('mapped', 'mapping', 'maps', 'map'),
    ('marched', 'marching', 'marches', 'march'),
    ('marked', 'marking', 'marks', 'mark'),
    ('married', 'marrying', 'marries', 'marry'),
    ('marvelled', 'marvelling', 'marvels', 'marvel'),
    ('masked', 'masking', 'masks', 'mask'),
    ('masqueraded', 'masquerading', 'masquerades', 'masquerade'),
    ('mastered', 'mastering', 'masters', 'master'),
    ('matched', 'matching', 'matches', 'match'),
    ('mated', 'mating', 'mates', 'mate'),
    ('mattered', 'mattering', 'matters', 'matter'),
    ('might', 'may'),
    ('meant', 'meaning', 'means', 'mean'),
    ('measured', 'measuring', 'measures', 'measure'),
    ('meddled', 'meddling', 'meddles', 'meddle'),
    ('mediated', 'mediating', 'mediates', 'mediate'),
    ('meditated', 'meditating', 'meditates', 'meditate'),
    ('met', 'meeting', 'meets', 'meet'),
    ('melted', 'melting', 'melts', 'melt'),
    ('menaced', 'menacing', 'menaces', 'menace'),
    ('mended', 'mending', 'mends', 'mend'),
    ('mentioned', 'mentioning', 'mentions', 'mention'),
    ('merchandised', 'merchandising', 'merchandises', 'merchandise'),
    ('messed', 'messing', 'messes', 'mess'),
    ('migrated', 'migrating', 'migrates', 'migrate'),
    ('milked', 'milking', 'milks', 'milk'),
    ('milled', 'milling', 'mills', 'mill'),
    ('minded', 'minding', 'minds', 'mind'),
    ('mingled', 'mingling', 'mingles', 'mingle'),
    ('ministered', 'ministering', 'ministers', 'minister'),
    ('miscarried', 'miscarrying', 'miscarries', 'miscarry'),
    ('misled', 'misleading', 'misleads', 'mislead'),
    ('missed', 'missing', 'misses', 'miss'),
    ('mistook', 'mistaken', 'mistaking', 'mistakes', 'mistake'),
    ('mistreated', 'mistreating', 'mistreats', 'mistreat'),
    ('mixed', 'mixing', 'mixes', 'mix'),
    ('moaned', 'moaning', 'moans', 'moan'),
    ('mocked', 'mocking', 'mocks', 'mock'),
    ('moistened', 'moistening', 'moistens', 'moisten'),
    ('molested', 'molesting', 'molests', 'molest'),
    ('monitored', 'monitoring', 'monitors', 'monitor'),
    ('mothered', 'mothering', 'mothers', 'mother'),
    ('motioned', 'motioning', 'motions', 'motion'),
    ('moulded', 'moulding', 'moulds', 'molded', 'molding', 'molds', 'mold', 'mould'),
    ('mounted', 'mounting', 'mounts', 'mount'),
    ('mourned', 'mourning', 'mourns', 'mourn'),
    ('moved', 'moving', 'moves', 'move'),
    ('muddied', 'muddying', 'muddies', 'muddy'),
    ('multiplied', 'multiplying', 'multiplies', 'multiply'),
    ('murdered', 'murdering', 'murders', 'murder'),
    ('murmured', 'murmuring', 'murmurs', 'murmur'),
    ('mustered', 'mustering', 'musters', 'muster'),
    ('muttered', 'muttering', 'mutters', 'mutter'),
    ('muzzled', 'muzzling', 'muzzles', 'muzzle'),
    ('nagged', 'nagging', 'nags', 'nag'),
    ('nailed', 'nailing', 'nails', 'nail'),
    ('named', 'naming', 'names', 'name'),
    ('napped', 'napping', 'naps', 'nap'),
    ('narrowed', 'narrowing', 'narrows', 'narrow'),
    ('neared', 'nearing', 'nears', 'near'),
    ('needed', 'needing', 'needs', 'need'),
    ('neglected', 'neglecting', 'neglects', 'neglect'),
    ('negotiated', 'negotiating', 'negotiates', 'negotiate'),
    ('neighed', 'neighing', 'neighs', 'neigh'),
    ('nested', 'nesting', 'nests', 'nest'),
    ('netted', 'netting', 'nets', 'net'),
    ('nicknamed', 'nicknaming', 'nicknames', 'nickname'),
    ('nipped', 'nipping', 'nips', 'nip'),
    ('nodded', 'nodding', 'nods', 'nod'),
    ('noted', 'noting', 'notes', 'note'),
    ('noticed', 'noticing', 'notices', 'notice'),
    ('notified', 'notifying', 'notifies', 'notify'),
    ('nourished', 'nourishing', 'nourishes', 'nourish'),
    ('nullified', 'nullifying', 'nullifies', 'nullify'),
    ('numbered', 'numbering', 'numbers', 'number'),
    ('nursed', 'nursing', 'nurses', 'nurse'),
    ('nurtured', 'nurturing', 'nurtures', 'nurture'),
    ('obeyed', 'obeying', 'obeys', 'obey'),
    ('objected', 'objecting', 'objects', 'object'),
    ('obliged', 'obliging', 'obliges', 'oblige'),
    ('obscured', 'obscuring', 'obscures', 'obscure'),
    ('observed', 'observing', 'observes', 'observe'),
    ('obsessed', 'obsessing', 'obsesses', 'obsess'),
    ('obtained', 'obtaining', 'obtains', 'obtain'),
    ('occupied', 'occupying', 'occupies', 'occupy'),
    ('occurred', 'occurring', 'occurs', 'occur'),
    ('offended', 'offending', 'offends', 'offend'),
    ('offered', 'offering', 'offers', 'offer'),
    ('oozed', 'oozing', 'oozes', 'ooze'),
    ('opened', 'opening', 'opens', 'open'),
    ('opposed', 'opposing', 'opposes', 'oppose'),
    ('oppressed', 'oppressing', 'oppresses', 'oppress'),
    ('ordained', 'ordaining', 'ordains', 'ordain'),
    ('ordered', 'ordering', 'orders', 'order'),
    ('organised', 'organising', 'organises', 'organise'),
    ('originated', 'originating', 'originates', 'originate'),
    ('orphaned', 'orphaning', 'orphans', 'orphan'),
    ('outflowed', 'outflowing', 'outflows', 'outflow'),
    ('outnumbered', 'outnumbering', 'outnumbers', 'outnumber'),
    ('outraged', 'outraging', 'outrages', 'outrage'),
    ('overcame', 'overcoming', 'overcomes', 'overcome'),
    ('overextended', 'overextending', 'overextends', 'overextend'),
    ('overflowed', 'overflowing', 'overflows', 'overflow'),
    ('overhung', 'overhanging', 'overhangs', 'overhang'),
    ('overlaid', 'overlaying', 'overlays', 'overlay'),
    ('overlooked', 'overlooking', 'overlooks', 'overlook'),
    ('overnighted', 'overnighting', 'overnights', 'overnight'),
    ('overpowered', 'overpowering', 'overpowers', 'overpower'),
    ('overruled', 'overruling', 'overrules', 'overrule'),
    ('overran', 'overrunning', 'overruns', 'overrun'),
    ('oversaw', 'overseen', 'overseeing', 'oversees', 'oversee'),
    ('overshadowed', 'overshadowing', 'overshadows', 'overshadow'),
    ('overtook', 'overtaken', 'overtaking', 'overtakes', 'overtake'),
    ('overthrew', 'overthrown', 'overthrowing', 'overthrows', 'overthrow'),
    ('overturned', 'overturning', 'overturns', 'overturn'),
    ('overwhelmed', 'overwhelming', 'overwhelms', 'overwhelm'),
    ('owed', 'owing', 'owes', 'owe'),
    ('owned', 'owning', 'owns', 'own'),
    ('pacified', 'pacifying', 'pacifies', 'pacify'),
    ('packed', 'packing', 'packs', 'pack'),
    ('pained', 'paining', 'pains', 'pain'),
    ('painted', 'painting', 'paints', 'paint'),
    ('pampered', 'pampering', 'pampers', 'pamper'),
    ('panelled', 'panelling', 'panels', 'panel'),
    ('panicked', 'panicking', 'panics', 'panic'),
    ('panted', 'panting', 'pants', 'pant'),
    ('parcelled', 'parcelling', 'parcels', 'parcel'),
    ('pardoned', 'pardoning', 'pardons', 'pardon'),
    ('parted', 'parting', 'parts', 'part'),
    ('partook', 'partaken', 'partaking', 'partakes', 'partake'),
    ('participated', 'participating', 'participates', 'participate'),
    ('partied', 'partying', 'parties', 'party'),
    ('passed', 'passing', 'passes', 'pass'),
    ('pastured', 'pasturing', 'pastures', 'pasture'),
    ('patched', 'patching', 'patches', 'patch'),
    ('paved', 'paving', 'paves', 'pave'),
    ('paid', 'paying', 'pays', 'pay'),
    ('pecked', 'pecking', 'pecks', 'peck'),
    ('peeled', 'peeling', 'peels', 'peel'),
    ('peered', 'peering', 'peers', 'peer'),
    ('penetrated', 'penetrating', 'penetrates', 'penetrate'),
    ('perceived', 'perceiving', 'perceives', 'perceive'),
    ('perfected', 'perfecting', 'perfects', 'perfect'),
    ('performed', 'performing', 'performs', 'perform'),
    ('perfumed', 'perfuming', 'perfumes', 'perfume'),
    ('perished', 'perishing', 'perishes', 'perish'),
    ('permitted', 'permitting', 'permits', 'permit'),
    ('perplexed', 'perplexing', 'perplexes', 'perplex'),
    ('persecuted', 'persecuting', 'persecutes', 'persecute'),
    ('persevered', 'persevering', 'perseveres', 'persevere'),
    ('persisted', 'persisting', 'persists', 'persist'),
    ('persuaded', 'persuading', 'persuades', 'persuade'),
    ('pertained', 'pertaining', 'pertains', 'pertain'),
    ('perverted', 'perverting', 'perverts', 'pervert'),
    ('petitioned', 'petitioning', 'petitions', 'petition'),
    ('picked', 'picking', 'picks', 'pick'),
    ('pictured', 'picturing', 'pictures', 'picture'),
    ('pierced', 'piercing', 'pierces', 'pierce'),
    ('piled', 'piling', 'piles', 'pile'),
    ('pined', 'pining', 'pines', 'pine'),
    ('pitched', 'pitching', 'pitches', 'pitch'),
    ('pitied', 'pitying', 'pities', 'pity'),
    ('placated', 'placating', 'placates', 'placate'),
    ('placed', 'placing', 'places', 'place'),
    ('plagued', 'plaguing', 'plagues', 'plague'),
    ('planned', 'planning', 'plans', 'plan'),
    ('planed', 'planing', 'planes', 'plane'),
    ('planted', 'planting', 'plants', 'plant'),
    ('plastered', 'plastering', 'plasters', 'plaster'),
    ('plated', 'plating', 'plates', 'plate'),
    ('played', 'playing', 'plays', 'play'),
    ('pleaded', 'pled', 'pleading', 'pleads', 'plead'),
    ('pleased', 'pleasing', 'pleases', 'please'),
    ('pledged', 'pledging', 'pledges', 'pledge'),
    ('plotted', 'plotting', 'plots', 'plot'),
    ('ploughed', 'ploughing', 'ploughs', 'plowed', 'plowing', 'plows', 'plow', 'plough'),
    ('plucked', 'plucking', 'plucks', 'pluck'),
    ('plundered', 'plundering', 'plunders', 'plunder'),
    ('plunged', 'plunging', 'plunges', 'plunge'),
    ('pointed', 'pointing', 'points', 'point'),
    ('poisoned', 'poisoning', 'poisons', 'poison'),
    ('poked', 'poking', 'pokes', 'poke'),
    ('polished', 'polishing', 'polishes', 'polish'),
    ('polluted', 'polluting', 'pollutes', 'pollute'),
    ('pondered', 'pondering', 'ponders', 'ponder'),
    ('pooled', 'pooling', 'pools', 'pool'),
    ('positioned', 'positioning', 'positions', 'position'),
    ('possessed', 'possessing', 'possesses', 'possess'),
    ('posted', 'posting', 'posts', 'post'),
    ('pounded', 'pounding', 'pounds', 'pound'),
    ('poured', 'pouring', 'pours', 'pour'),
    ('practised', 'practising', 'practises', 'practiced', 'practicing', 'practices', 'practice', 'practise'),
    ('praised', 'praising', 'praises', 'praise'),
    ('prayed', 'praying', 'prays', 'pray'),
    ('preached', 'preaching', 'preaches', 'preach'),
    ('prearranged', 'prearranging', 'prearranges', 'prearrange'),
    ('preceded', 'preceding', 'precedes', 'precede'),
    ('predicted', 'predicting', 'predicts', 'predict'),
    ('preferred', 'preferring', 'prefers', 'prefer'),
    ('premeditated', 'premeditating', 'premeditates', 'premeditate'),
    ('prepared', 'preparing', 'prepares', 'prepare'),
    ('presented', 'presenting', 'presents', 'present'),
    ('preserved', 'preserving', 'preserves', 'preserve'),
    ('presided', 'presiding', 'presides', 'preside'),
    ('pressed', 'pressing', 'presses', 'press'),
    ('pressured', 'pressuring', 'pressures', 'pressure'),
    ('pretended', 'pretending', 'pretends', 'pretend'),
    ('prevailed', 'prevailing', 'prevails', 'prevail'),
    ('prevented', 'preventing', 'prevents', 'prevent'),
    ('preyed', 'preying', 'preys', 'prey'),
    ('priced', 'pricing', 'prices', 'price'),
    ('pricked', 'pricking', 'pricks', 'prick'),
    ('prioritised', 'prioritising', 'prioritises', 'prioritise'),
    ('proceeded', 'proceeding', 'proceeds', 'proceed'),
    ('proclaimed', 'proclaiming', 'proclaims', 'proclaim'),
    ('procured', 'procuring', 'procures', 'procure'),
    ('prodded', 'prodding', 'prods', 'prod'),
    ('produced', 'producing', 'produces', 'produce'),
    ('profaned', 'profaning', 'profanes', 'profane'),
    ('professed', 'professing', 'professes', 'profess'),
    ('profited', 'profiting', 'profits', 'profit'),
    ('progressed', 'progressing', 'progresses', 'progress'),
    ('prohibited', 'prohibiting', 'prohibits', 'prohibit'),
    ('projected', 'projecting', 'projects', 'project'),
    ('prolonged', 'prolonging', 'prolongs', 'prolong'),
    ('promised', 'promising', 'promises', 'promise'),
    ('promoted', 'promoting', 'promotes', 'promote'),
    ('prompted', 'prompting', 'prompts', 'prompt'),
    ('pronounced', 'pronouncing', 'pronounces', 'pronounce'),
    ('propped', 'propping', 'props', 'prop'),
    ('prophesied', 'prophesying', 'prophesies', 'prophesy'),
    ('prospered', 'prospering', 'prospers', 'prosper'),
    ('prostituted', 'prostituting', 'prostitutes', 'prostitute'),
    ('prostrated', 'prostrating', 'prostrates', 'prostrate'),
    ('protected', 'protecting', 'protects', 'protect'),
    ('protested', 'protesting', 'protests', 'protest'),
    ('proved', 'proven', 'proving', 'proves', 'prove'),
    ('provided', 'providing', 'provides', 'provide'),
    ('provoked', 'provoking', 'provokes', 'provoke'),
    ('prowled', 'prowling', 'prowls', 'prowl'),
    ('pruned', 'pruning', 'prunes', 'prune'),
    ('published', 'publishing', 'publishes', 'publish'),
    ('puffed', 'puffing', 'puffs', 'puff'),
    ('pulled', 'pulling', 'pulls', 'pull'),
    ('pulverised', 'pulverising', 'pulverises', 'pulverized', 'pulverizing', 'pulverizes', 'pulverize', 'pulverise'),
    ('punished', 'punishing', 'punishes', 'punish'),
    ('purchased', 'purchasing', 'purchases', 'purchase'),
    ('purged', 'purging', 'purges', 'purge'),
    ('purified', 'purifying', 'purifies', 'purify'),
    ('purposed', 'purposing', 'purposes', 'purpose'),
    ('pursed', 'pursing', 'purses', 'purse'),
    ('pursued', 'pursuing', 'pursues', 'pursue'),
    ('pushed', 'pushing', 'pushes', 'push'),
    ('putting', 'puts', 'put'),
    ('puzzled', 'puzzling', 'puzzles', 'puzzle'),
    ('quaked', 'quaking', 'quakes', 'quake'),
    ('quarantined', 'quarantining', 'quarantines', 'quarantine'),
    ('quarrelled', 'quarrelling', 'quarrels', 'quarrel'),
    ('quarried', 'quarrying', 'quarries', 'quarry'),
    ('quenched', 'quenching', 'quenches', 'quench'),
    ('queried', 'querying', 'queries', 'query'),
    ('questioned', 'questioning', 'questions', 'question'),
    ('quibbled', 'quibbling', 'quibbles', 'quibble'),
    ('quietened', 'quietening', 'quietens', 'quieten'),
    ('quitting', 'quits', 'quit'),
    ('quivered', 'quivering', 'quivers', 'quiver'),
    ('racked', 'racking', 'racks', 'rack'),
    ('radiated', 'radiating', 'radiates', 'radiate'),
    ('raged', 'raging', 'rages', 'rage'),
    ('raided', 'raiding', 'raids', 'raid'),
    ('rained', 'raining', 'rains', 'rain'),
    ('raised', 'raising', 'raises', 'raise'),
    ('rallied', 'rallying', 'rallies', 'rally'),
    ('ranged', 'ranging', 'ranges', 'range'),
    ('ransomed', 'ransoming', 'ransoms', 'ransom'),
    ('raped', 'raping', 'rapes', 'rape'),
    ('rationed', 'rationing', 'rations', 'ration'),
    ('rattled', 'rattling', 'rattles', 'rattle'),
    ('ravaged', 'ravaging', 'ravages', 'ravage'),
    ('raved', 'raving', 'raves', 'rave'),
    ('ravished', 'ravishing', 'ravishes', 'ravish'),
    ('reached', 'reaching', 'reaches', 'reach'),
    ('reacted', 'reacting', 'reacts', 'react'),
    ('reading', 'reads', 'read'),
    ('realised', 'realising', 'realises', 'realise'),
    ('reaped', 'reaping', 'reaps', 'reap'),
    ('reappeared', 'reappearing', 'reappears', 'reappear'),
    ('reared', 'rearing', 'rears', 'rear'),
    ('reasoned', 'reasoning', 'reasons', 'reason'),
    ('rebelled', 'rebelling', 'rebels', 'rebel'),
    ('rebuilt', 'rebuilding', 'rebuilds', 'rebuild'),
    ('rebuked', 'rebuking', 'rebukes', 'rebuke'),
    ('recalled', 'recalling', 'recalls', 'recall'),
    ('recaptured', 'recapturing', 'recaptures', 'recapture'),
    ('receded', 'receding', 'recedes', 'recede'),
    ('received', 'receiving', 'receives', 'receive'),
    ('recited', 'reciting', 'recites', 'recite'),
    ('reckoned', 'reckoning', 'reckons', 'reckon'),
    ('reclaimed', 'reclaiming', 'reclaims', 'reclaim'),
    ('reclined', 'reclining', 'reclines', 'recline'),
    ('recognised', 'recognising', 'recognises', 'recognized', 'recognizing', 'recognizes', 'recognize', 'recognise'),
    ('recommended', 'recommending', 'recommends', 'recommend'),
    ('reconciled', 'reconciling', 'reconciles', 'reconcile'),
    ('recorded', 'recording', 'records', 'record'),
    ('recounted', 'recounting', 'recounts', 'recount'),
    ('recovered', 'recovering', 'recovers', 'recover'),
    ('recruited', 'recruiting', 'recruits', 'recruit'),
    ('rededicated', 'rededicating', 'rededicates', 'rededicate'),
    ('redeemed', 'redeeming', 'redeems', 'redeem'),
    ('reduced', 'reducing', 'reduces', 'reduce'),
    ('reeled', 'reeling', 'reels', 'reel'),
    ('reestablished', 'reestablishing', 'reestablishes', 'reestablish'),
    ('reexamined', 'reexamining', 'reexamines', 'reexamine'),
    ('referred', 'referring', 'refers', 'refer'),
    ('refined', 'refining', 'refines', 'refine'),
    ('reflected', 'reflecting', 'reflects', 'reflect'),
    ('reformed', 'reforming', 'reforms', 'reform'),
    ('refounded', 'refounding', 'refounds', 'refound'),
    ('refrained', 'refraining', 'refrains', 'refrain'),
    ('refreshed', 'refreshing', 'refreshes', 'refresh'),
    ('refused', 'refusing', 'refuses', 'refuse'),
    ('refuted', 'refuting', 'refutes', 'refute'),
    ('regained', 'regaining', 'regains', 'regain'),
    ('regarded', 'regarding', 'regards', 'regard'),
    ('registered', 'registering', 'registers', 'register'),
    ('regretted', 'regretting', 'regrets', 'regret'),
    ('regulated', 'regulating', 'regulates', 'regulate'),
    ('reigned', 'reigning', 'reigns', 'reign'),
    ('reimbursed', 'reimbursing', 'reimburses', 'reimburse'),
    ('reinforced', 'reinforcing', 'reinforces', 'reinforce'),
    ('rejected', 'rejecting', 'rejects', 'reject'),
    ('rejoiced', 'rejoicing', 'rejoices', 'rejoice'),
    ('rekindled', 'rekindling', 'rekindles', 'rekindle'),
    ('related', 'relating', 'relates', 'relate'),
    ('relaxed', 'relaxing', 'relaxes', 'relax'),
    ('relayed', 'relaying', 'relays', 'relay'),
    ('released', 'releasing', 'releases', 'release'),
    ('releasened', 'releasening', 'releasens', 'releasen'),
    ('relented', 'relenting', 'relents', 'relent'),
    ('relieved', 'relieving', 'relieves', 'relieve'),
    ('relied', 'relying', 'relies', 'rely'),
    ('remained', 'remaining', 'remains', 'remain'),
    ('remade', 'remaking', 'remakes', 'remake'),
    ('remarried', 'remarrying', 'remarries', 'remarry'),
    ('remembered', 'remembering', 'remembers', 'remember'),
    ('reminded', 'reminding', 'reminds', 'remind'),
    ('remitted', 'remitting', 'remits', 'remit'),
    ('removed', 'removing', 'removes', 'remove'),
    ('renamed', 'renaming', 'renames', 'rename'),
    ('rendered', 'rendering', 'renders', 'render'),
    ('renewed', 'renewing', 'renews', 'renew'),
    ('renounced', 'renouncing', 'renounces', 'renounce'),
    ('rented', 'renting', 'rents', 'rent'),
    ('repaired', 'repairing', 'repairs', 'repair'),
    ('repaid', 'repaying', 'repays', 'repay'),
    ('repeated', 'repeating', 'repeats', 'repeat'),
    ('repelled', 'repelling', 'repels', 'repel'),
    ('repented', 'repenting', 'repents', 'repent'),
    ('replaced', 'replacing', 'replaces', 'replace'),
    ('replied', 'replying', 'replies', 'reply'),
    ('reported', 'reporting', 'reports', 'report'),
    ('represented', 'representing', 'represents', 'represent'),
    ('reprimanded', 'reprimanding', 'reprimands', 'reprimand'),
    ('reproached', 'reproaching', 'reproaches', 'reproach'),
    ('reproved', 'reproving', 'reproves', 'reprove'),
    ('repudiated', 'repudiating', 'repudiates', 'repudiate'),
    ('requested', 'requesting', 'requests', 'request'),
    ('required', 'requiring', 'requires', 'require'),
    ('requited', 'requiting', 'requites', 'requite'),
    ('rescued', 'rescuing', 'rescues', 'rescue'),
    ('resembled', 'resembling', 'resembles', 'resemble'),
    ('resented', 'resenting', 'resents', 'resent'),
    ('reserved', 'reserving', 'reserves', 'reserve'),
    ('resettled', 'resettling', 'resettles', 'resettle'),
    ('resided', 'residing', 'resides', 'reside'),
    ('resisted', 'resisting', 'resists', 'resist'),
    ('resolved', 'resolving', 'resolves', 'resolve'),
    ('resorted', 'resorting', 'resorts', 'resort'),
    ('resounded', 'resounding', 'resounds', 'resound'),
    ('respected', 'respecting', 'respects', 'respect'),
    ('responded', 'responding', 'responds', 'respond'),
    ('rested', 'resting', 'rests', 'rest'),
    ('restored', 'restoring', 'restores', 'restore'),
    ('restrained', 'restraining', 'restrains', 'restrain'),
    ('restricted', 'restricting', 'restricts', 'restrict'),
    ('resulted', 'resulting', 'results', 'result'),
    ('retained', 'retaining', 'retains', 'retain'),
    ('retaliated', 'retaliating', 'retaliates', 'retaliate'),
    ('retold', 'retelling', 'retells', 'retell'),
    ('retreated', 'retreating', 'retreats', 'retreat'),
    ('retrieved', 'retrieving', 'retrieves', 'retrieve'),
    ('returned', 'returning', 'returns', 'return'),
    ('revealed', 'revealing', 'reveals', 'reveal'),
    ('reveling', 'revelled', 'revelling', 'revels', 'revel'),
    ('revered', 'revering', 'reveres', 'revere'),
    ('reverenced', 'reverencing', 'reverences', 'reverence'),
    ('reversed', 'reversing', 'reverses', 'reverse'),
    ('reviled', 'reviling', 'reviles', 'revile'),
    ('revived', 'reviving', 'revives', 'revive'),
    ('revoked', 'revoking', 'revokes', 'revoke'),
    ('revolted', 'revolting', 'revolts', 'revolt'),
    ('rewarded', 'rewarding', 'rewards', 'reward'),
    ('rode', 'ridden', 'riding', 'rides', 'ride'),
    ('ridiculed', 'ridiculing', 'ridicules', 'ridicule'),
    ('rang', 'rung', 'ringing', 'rings', 'ring'),
    ('rinsed', 'rinsing', 'rinses', 'rinse'),
    ('ripped', 'ripping', 'rips', 'rip'),
    ('ripened', 'ripening', 'ripens', 'ripen'),
    ('rose', 'risen', 'rising', 'rises', 'rise'),
    ('risked', 'risking', 'risks', 'risk'),
    ('roamed', 'roaming', 'roams', 'roam'),
    ('roared', 'roaring', 'roars', 'roar'),
    ('roasted', 'roasting', 'roasts', 'roast'),
    ('robbed', 'robbing', 'robs', 'rob'),
    ('robed', 'robing', 'robes', 'robe'),
    ('rocked', 'rocking', 'rocks', 'rock'),
    ('rolled', 'rolling', 'rolls', 'roll'),
    ('roofed', 'roofing', 'roofs', 'roof'),
    ('rooted', 'rooting', 'roots', 'root'),
    ('rostered', 'rostering', 'rosters', 'roster'),
    ('rotted', 'rotting', 'rots', 'rot'),
    ('rounded', 'rounding', 'rounds', 'round'),
    ('roused', 'rousing', 'rouses', 'rouse'),
    ('roved', 'roving', 'roves', 'rove'),
    ('rowed', 'rowing', 'rows', 'row'),
    ('rubbed', 'rubbing', 'rubs', 'rub'),
    ('ruined', 'ruining', 'ruins', 'ruin'),
    ('ruled', 'ruling', 'rules', 'rule'),
    ('rumbled', 'rumbling', 'rumbles', 'rumble'),
    ('ran', 'running', 'runs', 'run'),
    ('rushed', 'rushing', 'rushes', 'rush'),
    ('sacrificed', 'sacrificing', 'sacrifices', 'sacrifice'),
    ('saddened', 'saddening', 'saddens', 'sadden'),
    ('saddled', 'saddling', 'saddles', 'saddle'),
    ('sailed', 'sailing', 'sails', 'sail'),
    ('salted', 'salting', 'salts', 'salt'),
    ('saluted', 'saluting', 'salutes', 'salute'),
    ('sanctified', 'sanctifying', 'sanctifies', 'sanctify'),
    ('sapped', 'sapping', 'saps', 'sap'),
    ('satisfied', 'satisfying', 'satisfies', 'satisfy'),
    ('saved', 'saving', 'saves', 'save'),
    ('sawed', 'sawn', 'sawing', 'saws', 'saw'),
    ('said', 'saying', 'says', 'say'),
    ('scaled', 'scaling', 'scales', 'scale'),
    ('scared', 'scaring', 'scares', 'scare'),
    ('scattered', 'scattering', 'scatters', 'scatter'),
    ('schemed', 'scheming', 'schemes', 'scheme'),
    ('scoffed', 'scoffing', 'scoffs', 'scoff'),
    ('scolded', 'scolding', 'scolds', 'scold'),
    ('scorched', 'scorching', 'scorches', 'scorch'),
    ('scorned', 'scorning', 'scorns', 'scorn'),
    ('scourged', 'scourging', 'scourges', 'scourge'),
    ('scouted', 'scouting', 'scouts', 'scout'),
    ('scraped', 'scraping', 'scrapes', 'scrape'),
    ('scratched', 'scratching', 'scratches', 'scratch'),
    ('screamed', 'screaming', 'screams', 'scream'),
    ('screened', 'screening', 'screens', 'screen'),
    ('scrutinised', 'scrutinising', 'scrutinises', 'scrutinized', 'scrutinizing', 'scrutinizes', 'scrutinize', 'scrutinise'),
    ('sealed', 'sealing', 'seals', 'seal'),
    ('searched', 'searching', 'searches', 'search'),
    ('seasoned', 'seasoning', 'seasons', 'season'),
    ('seated', 'seating', 'seats', 'seat'),
    ('secluded', 'secluding', 'secludes', 'seclude'),
    ('secreted', 'secreting', 'secretes', 'secrete'),
    ('secured', 'securing', 'secures', 'secure'),
    ('seduced', 'seducing', 'seduces', 'seduce'),
    ('saw', 'seen', 'seeing', 'sees', 'see'),
    ('seeded', 'seeding', 'seeds', 'seed'),
    ('sought', 'seeking', 'seeks', 'seek'),
    ('seemed', 'seeming', 'seems', 'seem'),
    ('seized', 'seizing', 'seizes', 'seize'),
    ('selected', 'selecting', 'selects', 'select'),
    ('sold', 'selling', 'sells', 'sell'),
    ('sent', 'sending', 'sends', 'send'),
    ('sentenced', 'sentencing', 'sentences', 'sentence'),
    ('separated', 'separating', 'separates', 'separate'),
    ('served', 'serving', 'serves', 'serve'),
    ('setting', 'sets', 'set'),
    ('settled', 'settling', 'settles', 'settle'),
    ('sewed', 'sewn', 'sewing', 'sews', 'sew'),
    ('shackled', 'shackling', 'shackles', 'shackle'),
    ('shaded', 'shading', 'shades', 'shade'),
    ('shadowed', 'shadowing', 'shadows', 'shadow'),
    ('shook', 'shaken', 'shaking', 'shakes', 'shake'),
    ('should', 'shall'),
    ('shamed', 'shaming', 'shames', 'shame'),
    ('shaped', 'shaping', 'shapes', 'shape'),
    ('shared', 'sharing', 'shares', 'share'),
    ('sharpened', 'sharpening', 'sharpens', 'sharpen'),
    ('shattered', 'shattering', 'shatters', 'shatter'),
    ('shaved', 'shaven', 'shaving', 'shaves', 'shave'),
    ('sheared', 'shorn', 'shearing', 'shears', 'shear'),
    ('sheathed', 'sheathing', 'sheathes', 'sheathe'),
    ('shedding', 'sheds', 'shed'),
    ('sheltered', 'sheltering', 'shelters', 'shelter'),
    ('shepherded', 'shepherding', 'shepherds', 'shepherd'),
    ('shielded', 'shielding', 'shields', 'shield'),
    ('shifted', 'shifting', 'shifts', 'shift'),
    ('shimmered', 'shimmering', 'shimmers', 'shimmer'),
    ('shone', 'shined', 'shining', 'shines', 'shine'),
    ('shipwrecked', 'shipwrecking', 'shipwrecks', 'shipwreck'),
    ('shivered', 'shivering', 'shivers', 'shiver'),
    ('shocked', 'shocking', 'shocks', 'shock'),
    ('shod', 'shodden', 'shoeing', 'shoes', 'shoe'),
    ('shooed', 'shooing', 'shoos', 'shoo'),
    ('shot', 'shooting', 'shoots', 'shoot'),
    ('shortened', 'shortening', 'shortens', 'shorten'),
    ('shouted', 'shouting', 'shouts', 'shout'),
    ('showed', 'shown', 'showing', 'shows', 'show'),
    ('showered', 'showering', 'showers', 'shower'),
    ('shrank', 'shrunk', 'shrinking', 'shrinks', 'shrink'),
    ('shrivelled', 'shrivelling', 'shrivels', 'shrivel'),
    ('shuddered', 'shuddering', 'shudders', 'shudder'),
    ('shuffled', 'shuffling', 'shuffles', 'shuffle'),
    ('shunned', 'shunning', 'shuns', 'shun'),
    ('shutting', 'shuts', 'shut'),
    ('shied', 'shying', 'shies', 'shy'),
    ('sickened', 'sickening', 'sickens', 'sicken'),
    ('sifted', 'sifting', 'sifts', 'sift'),
    ('sighed', 'sighing', 'sighs', 'sigh'),
    ('sighted', 'sighting', 'sights', 'sight'),
    ('signed', 'signing', 'signs', 'sign'),
    ('signalled', 'signalling', 'signals', 'signal'),
    ('signified', 'signifying', 'signifies', 'signify'),
    ('silenced', 'silencing', 'silences', 'silence'),
    ('sinned', 'sinning', 'sins', 'sin'),
    ('sang', 'sung', 'singing', 'sings', 'sing'),
    ('singled', 'singling', 'singles', 'single'),
    ('sank', 'sunk', 'sinking', 'sinks', 'sink'),
    ('sat', 'sitting', 'sits', 'sit'),
    ('skimmed', 'skimming', 'skims', 'skim'),
    ('skinned', 'skinning', 'skins', 'skin'),
    ('skipped', 'skipping', 'skips', 'skip'),
    ('slackened', 'slackening', 'slackens', 'slacken'),
    ('slandered', 'slandering', 'slanders', 'slander'),
    ('slapped', 'slapping', 'slaps', 'slap'),
    ('slashed', 'slashing', 'slashes', 'slash'),
    ('slaughtered', 'slaughtering', 'slaughters', 'slaughter'),
    ('slew', 'slain', 'slaying', 'slays', 'slayed', 'slay'),
    ('slept', 'sleeping', 'sleeps', 'sleep'),
    ('sliced', 'slicing', 'slices', 'slice'),
    ('slid', 'sliding', 'slides', 'slide'),
    ('slung', 'slinging', 'slings', 'sling'),
    ('slinked', 'slunk', 'slinking', 'slinks', 'slink'),
    ('slipped', 'slipping', 'slips', 'slip'),
    ('slitting', 'slits', 'slit'),
    ('slithered', 'slithering', 'slithers', 'slither'),
    ('sloped', 'sloping', 'slopes', 'slope'),
    ('slowed', 'slowing', 'slows', 'slow'),
    ('slumbered', 'slumbering', 'slumbers', 'slumber'),
    ('smashed', 'smashing', 'smashes', 'smash'),
    ('smeared', 'smearing', 'smears', 'smear'),
    ('smelt', 'smelled', 'smelling', 'smells', 'smell'),
    ('smelted', 'smelting', 'smelts', 'smelt'),
    ('smiled', 'smiling', 'smiles', 'smile'),
    ('smoked', 'smoking', 'smokes', 'smoke'),
    ('smoothed', 'smoothing', 'smooths', 'smooth'),
    ('smouldered', 'smouldering', 'smoulders', 'smoldering', 'smoulder'),
    ('snapped', 'snapping', 'snaps', 'snap'),
    ('snared', 'snaring', 'snares', 'snare'),
    ('snatched', 'snatching', 'snatches', 'snatch'),
    ('sneaked', 'snuck', 'sneaking', 'sneaks', 'sneak'),
    ('sneered', 'sneering', 'sneers', 'sneer'),
    ('sneezed', 'sneezing', 'sneezes', 'sneeze'),
    ('snorted', 'snorting', 'snorts', 'snort'),
    ('snowed', 'snowing', 'snows', 'snow'),
    ('snubbed', 'snubbing', 'snubs', 'snub'),
    ('soaked', 'soaking', 'soaks', 'soak'),
    ('soared', 'soaring', 'soars', 'soar'),
    ('sobbed', 'sobbing', 'sobs', 'sob'),
    ('softened', 'softening', 'softens', 'soften'),
    ('soiled', 'soiling', 'soils', 'soil'),
    ('sojourned', 'sojourning', 'sojourns', 'sojourn'),
    ('soldiered', 'soldiering', 'soldiers', 'soldier'),
    ('solved', 'solving', 'solves', 'solve'),
    ('soothed', 'soothing', 'soothes', 'soothe'),
    ('sorrowed', 'sorrowing', 'sorrows', 'sorrow'),
    ('sorted', 'sorting', 'sorts', 'sort'),
    ('sounded', 'sounding', 'sounds', 'sound'),
    ('sowed', 'sown', 'sowing', 'sows', 'sow'),
    ('spaced', 'spacing', 'spaces', 'space'),
    ('spanked', 'spanking', 'spanks', 'spank'),
    ('spared', 'sparing', 'spares', 'spare'),
    ('sparkled', 'sparkling', 'sparkles', 'sparkle'),
    ('spattered', 'spattering', 'spatters', 'spatter'),
    ('spoke', 'spoken', 'speaking', 'speaks', 'speak'),
    ('speared', 'spearing', 'spears', 'spear'),
    ('specified', 'specifying', 'specifies', 'specify'),
    ('sped', 'speeding', 'speeds', 'speed'),
    ('spent', 'spending', 'spends', 'spend'),
    ('spewed', 'spewing', 'spews', 'spew'),
    ('spilt', 'spilled', 'spilling', 'spills', 'spill'),
    ('spun', 'spinning', 'spins', 'spin'),
    ('spat', 'spitting', 'spits', 'spit'),
    ('splashed', 'splashing', 'splashes', 'splash'),
    ('splintered', 'splintering', 'splinters', 'splinter'),
    ('splitting', 'splits', 'split'),
    ('spoilt', 'spoiled', 'spoiling', 'spoils', 'spoil'),
    ('sponged', 'sponging', 'sponges', 'sponge'),
    ('sported', 'sporting', 'sports', 'sport'),
    ('spouted', 'spouting', 'spouts', 'spout'),
    ('spreading', 'spreads', 'spread'),
    ('sprang', 'sprung', 'springing', 'springs', 'spring'),
    ('sprinkled', 'sprinkling', 'sprinkles', 'sprinkle'),
    ('sprouted', 'sprouting', 'sprouts', 'sprout'),
    ('spurned', 'spurning', 'spurns', 'spurn'),
    ('spied', 'spying', 'spies', 'spy'),
    ('squeezed', 'squeezing', 'squeezes', 'squeeze'),
    ('stabbed', 'stabbing', 'stabs', 'stab'),
    ('stacked', 'stacking', 'stacks', 'stack'),
    ('staggered', 'staggering', 'staggers', 'stagger'),
    ('stained', 'staining', 'stains', 'stain'),
    ('stammered', 'stammering', 'stammers', 'stammer'),
    ('stamped', 'stamping', 'stamps', 'stamp'),
    ('stood', 'standing', 'stands', 'stand'),
    ('stared', 'staring', 'stares', 'stare'),
    ('started', 'starting', 'starts', 'start'),
    ('startled', 'startling', 'startles', 'startle'),
    ('starved', 'starving', 'starves', 'starve'),
    ('stated', 'stating', 'states', 'state'),
    ('stationed', 'stationing', 'stations', 'station'),
    ('stayed', 'staying', 'stays', 'stay'),
    ('stole', 'stolen', 'stealing', 'steals', 'steal'),
    ('steeled', 'steeling', 'steels', 'steel'),
    ('steered', 'steering', 'steers', 'steer'),
    ('stepped', 'stepping', 'steps', 'step'),
    ('stuck', 'sticking', 'sticks', 'stick'),
    ('stiffened', 'stiffening', 'stiffens', 'stiffen'),
    ('stilled', 'stilling', 'stills', 'still'),
    ('stung', 'stinging', 'stings', 'sting'),
    ('stank', 'stunk', 'stinking', 'stinks', 'stink'),
    ('stirred', 'stirring', 'stirs', 'stir'),
    ('stocked', 'stocking', 'stocks', 'stock'),
    ('stoned', 'stoning', 'stones', 'stone'),
    ('stooped', 'stooping', 'stoops', 'stoop'),
    ('stopped', 'stopping', 'stops', 'stop'),
    ('stored', 'storing', 'stores', 'store'),
    ('stormed', 'storming', 'storms', 'storm'),
    ('straightened', 'straightening', 'straightens', 'straighten'),
    ('strained', 'straining', 'strains', 'strain'),
    ('strangled', 'strangling', 'strangles', 'strangle'),
    ('strapped', 'strapping', 'straps', 'strap'),
    ('strayed', 'straying', 'strays', 'stray'),
    ('streamed', 'streaming', 'streams', 'stream'),
    ('strengthened', 'strengthening', 'strengthens', 'strengthen'),
    ('stressed', 'stressing', 'stresses', 'stress'),
    ('stretched', 'stretching', 'stretches', 'stretch'),
    ('strode', 'stridden', 'striding', 'strides', 'stride'),
    ('struck', 'stricken', 'striking', 'strikes', 'strike'),
    ('strung', 'stringing', 'strings', 'string'),
    ('stripped', 'stripping', 'strips', 'strip'),
    ('strived', 'strove', 'striven', 'striving', 'strives', 'strive'),
    ('struggled', 'struggling', 'struggles', 'struggle'),
    ('studied', 'studying', 'studies', 'study'),
    ('stuffed', 'stuffing', 'stuffs', 'stuff'),
    ('stumbled', 'stumbling', 'stumbles', 'stumble'),
    ('stunned', 'stunning', 'stuns', 'stun'),
    ('styled', 'styling', 'styles', 'style'),
    ('subdued', 'subduing', 'subdues', 'subdue'),
    ('subjected', 'subjecting', 'subjects', 'subject'),
    ('submitted', 'submitting', 'submits', 'submit'),
    ('subsided', 'subsiding', 'subsides', 'subside'),
    ('substituted', 'substituting', 'substitutes', 'substitute'),
    ('subverted', 'subverting', 'subverts', 'subvert'),
    ('succeeded', 'succeeding', 'succeeds', 'succeed'),
    ('sucked', 'sucking', 'sucks', 'suck'),
    ('suckled', 'suckling', 'suckles', 'suckle'),
    ('suffered', 'suffering', 'suffers', 'suffer'),
    ('sufficed', 'sufficing', 'suffices', 'suffice'),
    ('suggested', 'suggesting', 'suggests', 'suggest'),
    ('suited', 'suiting', 'suits', 'suit'),
    ('summed', 'summing', 'sums', 'sum'),
    ('summarised', 'summarising', 'summarises', 'summarise'),
    ('summoned', 'summoning', 'summons', 'summon'),
    ('supervised', 'supervising', 'supervises', 'supervise'),
    ('supplanted', 'supplanting', 'supplants', 'supplant'),
    ('supplied', 'supplying', 'supplies', 'supply'),
    ('supported', 'supporting', 'supports', 'support'),
    ('supposed', 'supposing', 'supposes', 'suppose'),
    ('suppressed', 'suppressing', 'suppresses', 'suppress'),
    ('surfeited', 'surfeiting', 'surfeits', 'surfeit'),
    ('surged', 'surging', 'surges', 'surge'),
    ('surpassed', 'surpassing', 'surpasses', 'surpass'),
    ('surprised', 'surprising', 'surprises', 'surprise'),
    ('surrendered', 'surrendering', 'surrenders', 'surrender'),
    ('surrounded', 'surrounding', 'surrounds', 'surround'),
    ('survived', 'surviving', 'survives', 'survive'),
    ('suspected', 'suspecting', 'suspects', 'suspect'),
    ('sustained', 'sustaining', 'sustains', 'sustain'),
    ('swaddled', 'swaddling', 'swaddles', 'swaddle'),
    ('swallowed', 'swallowing', 'swallows', 'swallow'),
    ('swamped', 'swamping', 'swamps', 'swamp'),
    ('swarmed', 'swarming', 'swarms', 'swarm'),
    ('swayed', 'swaying', 'sways', 'sway'),
    ('swore', 'sworn', 'swearing', 'swears', 'swear'),
    ('sweated', 'sweating', 'sweats', 'sweat'),
    ('swept', 'sweeping', 'sweeps', 'sweep'),
    ('swelled', 'swollen', 'swelling', 'swells', 'swell'),
    ('swam', 'swum', 'swimming', 'swims', 'swim'),
    ('swung', 'swinging', 'swings', 'swing'),
    ('swirled', 'swirling', 'swirls', 'swirl'),
    ('swooped', 'swooping', 'swoops', 'swoop'),
    ('sympathised', 'sympathising', 'sympathises', 'sympathized', 'sympathizing', 'sympathizes', 'sympathize', 'sympathise'),
    ('took', 'taken', 'taking', 'takes', 'take'),
    ('talked', 'talking', 'talks', 'talk'),
    ('tamed', 'taming', 'tames', 'tame'),
    ('targeted', 'targeting', 'targets', 'target'),
    ('tarnished', 'tarnishing', 'tarnishes', 'tarnish'),
    ('tasted', 'tasting', 'tastes', 'taste'),
    ('taunted', 'taunting', 'taunts', 'taunt'),
    ('taxed', 'taxing', 'taxes', 'tax'),
    ('taught', 'teaching', 'teaches', 'teach'),
    ('teamed', 'teaming', 'teams', 'team'),
    ('tore', 'torn', 'tearing', 'tears', 'tear'),
    ('told', 'telling', 'tells', 'tell'),
    ('tempted', 'tempting', 'tempts', 'tempt'),
    ('tended', 'tending', 'tends', 'tend'),
    ('terminated', 'terminating', 'terminates', 'terminate'),
    ('terrified', 'terrifying', 'terrifies', 'terrify'),
    ('terrorised', 'terrorising', 'terrorises', 'terrorized', 'terrorizing', 'terrorizes', 'terrorize', 'terrorise'),
    ('tested', 'testing', 'tests', 'test'),
    ('testified', 'testifying', 'testifies', 'testify'),
    ('thanked', 'thanking', 'thanks', 'thank'),
    ('thought', 'thinking', 'thinks', 'think'),
    ('thirsted', 'thirsting', 'thirsts', 'thirst'),
    ('thrashed', 'thrashing', 'thrashes', 'thrash'),
    ('threatened', 'threatening', 'threatens', 'threaten'),
    ('threshed', 'threshing', 'threshes', 'thresh'),
    ('throve', 'thriven', 'thrived', 'thriving', 'thrives', 'thrive'),
    ('thronged', 'thronging', 'throngs', 'throng'),
    ('threw', 'thrown', 'throwing', 'throws', 'throw'),
    ('thrusting', 'thrusts', 'thrust'),
    ('thundered', 'thundering', 'thunders', 'thunder'),
    ('tidied', 'tidying', 'tidies', 'tidy'),
    ('tied', 'tying', 'ties', 'tie'),
    ('tightened', 'tightening', 'tightens', 'tighten'),
    ('tilled', 'tilling', 'tills', 'till'),
    ('tinkled', 'tinkling', 'tinkles', 'tinkle'),
    ('tipped', 'tipping', 'tips', 'tip'),
    ('tired', 'tiring', 'tires', 'tire'),
    ('tithed', 'tithing', 'tithes', 'tithe'),
    ('toiled', 'toiling', 'toils', 'toil'),
    ('tolerated', 'tolerating', 'tolerates', 'tolerate'),
    ('toppled', 'toppling', 'topples', 'topple'),
    ('tormented', 'tormenting', 'torments', 'torment'),
    ('tortured', 'torturing', 'tortures', 'torture'),
    ('tossed', 'tossing', 'tosses', 'toss'),
    ('totalled', 'totalling', 'totals', 'total'),
    ('tottered', 'tottering', 'totters', 'totter'),
    ('touched', 'touching', 'touches', 'touch'),
    ('towered', 'towering', 'towers', 'tower'),
    ('traced', 'tracing', 'traces', 'trace'),
    ('tracked', 'tracking', 'tracks', 'track'),
    ('traded', 'trading', 'trades', 'trade'),
    ('trained', 'training', 'trains', 'train'),
    ('trampled', 'trampling', 'tramples', 'trample'),
    ('transferred', 'transferring', 'transfers', 'transfer'),
    ('transformed', 'transforming', 'transforms', 'transform'),
    ('transgressed', 'transgressing', 'transgresses', 'transgress'),
    ('translated', 'translating', 'translates', 'translate'),
    ('transplanted', 'transplanting', 'transplants', 'transplant'),
    ('transported', 'transporting', 'transports', 'transport'),
    ('trapped', 'trapping', 'traps', 'trap'),
    ('travailed', 'travailing', 'travails', 'travail'),
    ('travelled', 'travelling', 'travels', 'traveling', 'travel'),
    ('trod', 'trodden', 'treading', 'treads', 'tread'),
    ('treasured', 'treasuring', 'treasures', 'treasure'),
    ('treated', 'treating', 'treats', 'treat'),
    ('trembled', 'trembling', 'trembles', 'tremble'),
    ('trespassed', 'trespassing', 'trespasses', 'trespass'),
    ('tricked', 'tricking', 'tricks', 'trick'),
    ('trimmed', 'trimming', 'trims', 'trim'),
    ('tripped', 'tripping', 'trips', 'trip'),
    ('triumphed', 'triumphing', 'triumphs', 'triumph'),
    ('troubled', 'troubling', 'troubles', 'trouble'),
    ('trumpeted', 'trumpeting', 'trumpets', 'trumpet'),
    ('trusted', 'trusting', 'trusts', 'trust'),
    ('tried', 'trying', 'tries', 'try'),
    ('tucked', 'tucking', 'tucks', 'tuck'),
    ('tumbled', 'tumbling', 'tumbles', 'tumble'),
    ('tuned', 'tuning', 'tunes', 'tune'),
    ('tunnelled', 'tunnelling', 'tunnels', 'tunnel'),
    ('turned', 'turning', 'turns', 'turn'),
    ('twisted', 'twisting', 'twists', 'twist'),
    ('uncovered', 'uncovering', 'uncovers', 'uncover'),
    ('underwent', 'undergone', 'undergoing', 'undergoes', 'undergo'),
    ('understood', 'understanding', 'understands', 'understand'),
    ('undertook', 'undertaken', 'undertaking', 'undertakes', 'undertake'),
    ('undid', 'undone', 'undoing', 'undoes', 'undo'),
    ('undressed', 'undressing', 'undresses', 'undress'),
    ('unfastened', 'unfastening', 'unfastens', 'unfasten'),
    ('united', 'uniting', 'unites', 'unite'),
    ('unloaded', 'unloading', 'unloads', 'unload'),
    ('untied', 'untying', 'unties', 'untie'),
    ('updated', 'updating', 'updates', 'update'),
    ('upheld', 'upholding', 'upholds', 'uphold'),
    ('uplifted', 'uplifting', 'uplifts', 'uplift'),
    ('uprooted', 'uprooting', 'uproots', 'uproot'),
    ('upsetting', 'upsets', 'upset'),
    ('urged', 'urging', 'urges', 'urge'),
    ('used', 'using', 'uses', 'use'),
    ('uttered', 'uttering', 'utters', 'utter'),
    ('valued', 'valuing', 'values', 'value'),
    ('vanished', 'vanishing', 'vanishes', 'vanish'),
    ('varied', 'varying', 'varies', 'vary'),
    ('veiled', 'veiling', 'veils', 'veil'),
    ('vented', 'venting', 'vents', 'vent'),
    ('ventured', 'venturing', 'ventures', 'venture'),
    ('verified', 'verifying', 'verifies', 'verify'),
    ('viewed', 'viewing', 'views', 'view'),
    ('vindicated', 'vindicating', 'vindicates', 'vindicate'),
    ('violated', 'violating', 'violates', 'violate'),
    ('visited', 'visiting', 'visits', 'visit'),
    ('voided', 'voiding', 'voids', 'void'),
    ('volunteered', 'volunteering', 'volunteers', 'volunteer'),
    ('vomited', 'vomiting', 'vomits', 'vomit'),
    ('vowed', 'vowing', 'vows', 'vow'),
    ('waged', 'waging', 'wages', 'wage'),
    ('wailed', 'wailing', 'wails', 'wail'),
    ('waited', 'waiting', 'waits', 'wait'),
    ('woke', 'woken', 'waking', 'wakes', 'wake'),
    ('walked', 'walking', 'walks', 'walk'),
    ('walled', 'walling', 'walls', 'wall'),
    ('wallowed', 'wallowing', 'wallows', 'wallow'),
    ('wandered', 'wandering', 'wanders', 'wander'),
    ('wanted', 'wanting', 'wants', 'want'),
    ('warred', 'warring', 'wars', 'war'),
    ('warmed', 'warming', 'warms', 'warm'),
    ('warned', 'warning', 'warns', 'warn'),
    ('warped', 'warping', 'warps', 'warp'),
    ('washed', 'washing', 'washes', 'wash'),
    ('wasted', 'wasting', 'wastes', 'waste'),
    ('watched', 'watching', 'watches', 'watch'),
    ('watered', 'watering', 'waters', 'water'),
    ('waved', 'waving', 'waves', 'wave'),
    ('wavered', 'wavering', 'wavers', 'waver'),
    ('weakened', 'weakening', 'weakens', 'weaken'),
    ('weaned', 'weaning', 'weans', 'wean'),
    ('wore', 'worn', 'wearing', 'wears', 'wear'),
    ('wearied', 'wearying', 'wearies', 'weary'),
    ('wove', 'woven', 'weaving', 'weaves', 'weave'),
    ('wept', 'weeping', 'weeps', 'weep'),
    ('weighed', 'weighing', 'weighs', 'weigh'),
    ('weighted', 'weighting', 'weights', 'weight'),
    ('welcomed', 'welcoming', 'welcomes', 'welcome'),
    ('wetted', 'wetting', 'wets', 'wet'),
    ('whacked', 'whacking', 'whacks', 'whack'),
    ('wheeled', 'wheeling', 'wheels', 'wheel'),
    ('whipped', 'whipping', 'whips', 'whip'),
    ('whirled', 'whirling', 'whirls', 'whirl'),
    ('whispered', 'whispering', 'whispers', 'whisper'),
    ('whistled', 'whistling', 'whistles', 'whistle'),
    ('whitened', 'whitening', 'whitens', 'whiten'),
    ('whitewashed', 'whitewashing', 'whitewashes', 'whitewash'),
    ('widened', 'widening', 'widens', 'widen'),
    ('widowed', 'widowing', 'widows', 'widow'),
    ('wielded', 'wielding', 'wields', 'wield'),
    ('would', 'willed', 'willing', 'wills', 'will'),
    ('wilted', 'wilting', 'wilts', 'wilt'),
    ('won', 'winning', 'wins', 'win'),
    ('wound', 'winding', 'winds', 'wind'),
    ('winked', 'winking', 'winks', 'wink'),
    ('winnowed', 'winnowing', 'winnows', 'winnow'),
    ('wintered', 'wintering', 'winters', 'winter'),
    ('wiped', 'wiping', 'wipes', 'wipe'),
    ('wished', 'wishing', 'wishes', 'wish'),
    ('withdrew', 'withdrawn', 'withdrawing', 'withdraws', 'withdraw'),
    ('withered', 'withering', 'withers', 'wither'),
    ('withheld', 'withholding', 'withholds', 'withhold'),
    ('withstood', 'withstanding', 'withstands', 'withstand'),
    ('witnessed', 'witnessing', 'witnesses', 'witness'),
    ('wobbled', 'wobbling', 'wobbles', 'wobble'),
    ('wondered', 'wondering', 'wonders', 'wonder'),
    ('worked', 'working', 'works', 'work'),
    ('worried', 'worrying', 'worries', 'worry'),
    ('worshipped', 'worshipping', 'worshiped', 'worshiping', 'worships', 'worship'),
    ('wounded', 'wounding', 'wounds', 'wound'),
    ('wrapped', 'wrapping', 'wraps', 'wrap'),
    ('wrestled', 'wrestling', 'wrestles', 'wrestle'),
    ('wrung', 'wringing', 'wrings', 'wring'),
    ('wrote', 'written', 'writing', 'writes', 'write'),
    ('writhed', 'writhing', 'writhes', 'writhe'),
    ('wronged', 'wronging', 'wrongs', 'wrong'),
    ('yearned', 'yearning', 'yearns', 'yearn'),
    ('yelled', 'yelling', 'yells', 'yell'),
    ('yielded', 'yielding', 'yields', 'yield'),
    ('yoked', 'yoking', 'yokes', 'yoke'),
)
simpleVerbs = tuple(verb for verbSet in SIMPLE_VERB_SETS for verb in verbSet)
# Allow overlapping forms that legitimately belong to different verb paradigms (e.g., lay/lie, saw, set, spread, beat etc.)
allowed_overlaps = {'beat','become','cut','hit','hurt','lay','let','put','quit','saw','set','shut','split','spread','thrust','lying','lies','lain','sawn','sewn','shaven','spat','stridden','stricken','bore','bound','fell','found','ground','smelt','wound'}
duplicates = [x for x in simpleVerbs if simpleVerbs.count(x)>1 and x not in allowed_overlaps]
assert len(duplicates) == 0, f"Accidental duplicates in simpleVerbs: {duplicates}"
for simpleVerb in simpleVerbs: # Just a safety check in case we miss a comma and python concatenates consecutive words
    assert len(simpleVerb) <= 15, f"({len(simpleVerb)}) {simpleVerb}"

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

SIMPLE_WORDS = SIMPLE_NOUNS_FLAT + verbalNouns + simpleVerbs + simpleAdverbs+ simpleAdjectives  + simpleNumbers + pronouns + connectors
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
    ('above','over'), # Mat 2:9
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
    ('angry','enraged'), # Mat 2:16
        ('angrily','anger'), # Mrk 3:5
    ('announced','proclaiming'), ('announcing','proclaiming'),
    ('Anyone','Whoever'),('anyone','whoever'),
        ('Anyone','one'),('anyone','ones'),('anyone','one'),
    ('anything','all things'),
    ('appeared','seen'),
    ('appropriate','fitting'),
    ('area','districts'), # Mat 2:22
    ('Army','hosts'),('army','hosts'),
    ('arrest','apprehend'),
        ('arrested','apprehended'),('arrested','captured'),('arrested','laid'), # Mrk 14:49
    ('aroma','odour'),
    ('around','by'), # Mrk 14:69
    ('asked','saying'),('asked','requesting'),('asked','inquiring'), # Mrk 14:37, 15:8, Mat 2:4
    ('asleep','sleeping'), # Mrk 14:40
    ('assembly','convocation'),
    ('assure','Truly'),('assured','saying'), # Mrk 13:30, 16:^
    ('astounded','amazed'),('astounded','marvelling'), # Mrk 15:5
    ('attention','attentiveness'),
    ('avoid','pass'), # Mrk 14:35
    ('aware','knowing'), # Mrk 15:10
    ('back','stern'),
    ('base','root'),
    ('battalion','cohort'), # Mrk 15:16
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
    ('bowed','fallen'), # Mat 2:11
        ('bowing','prostrating'), # Mrk 15:19
    ('box','ark'),
    ('brightness','glory'), # Mrk 13:26
    ('bull','ox'),('bulls','oxen'),
    ('burning','fire'),
    ('But','And'),('but','And'),('But','and'),('but','and'),
    ('buyers','buying'),
    ('came','arriving'), # MAt 3:13
    ('careful','watching'), # Mrk 13:9
    ('carry','bear'), # Mat 3:11
    ('cash','money'),('cash','silver'),
    ('cease','removed'),
    ('chairs','seats'),
    ('chamber','tomb'), # Mrk 16:2
    ('charge','testimony'),('charges','testimony'), # Mrk 14:56,57
    ('chasing','pursuing'),
    ('cheerful','joy'),
    ('chest','ark'),
    ('chiselled','hewn'), # Mrk 15:46
    ('close','near'),('close','neared'), # Mrk 13:28, Mat 3:2
    ('closely','focused'), # Mrk 14:67
    ('clothes','apparel'),('clothes','garments'),
    ('collapse','passing away'), # Mrk 13:31
    ('collect','gathering'), # Mrk 13:27
    ('commander','centurion'), # Mrk 15:39
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
    ('dark','darkness'), # Mrk 15:33
    ('date','day'), # Mrk 13:32
    ('dawn','cockcrow'), # Mrk 13:35
    ('dearly','beloved'),
    ('decide','purposed'),
    ('decision','evaluate'),('decisions','judgements'),
    ('declined','not'), # Mrk 15:23
    ('defend','answering'), # Mrk 14:60
    ('definitely','Truly'), # Mrk 15:39
    ('deformed','withered'),
    ('demanded','saying'), # Mrk 15:14
    ('demolish','tearing'), # Mrk 14:58
    ('demon-possessed','unclean'),
    ('denied','disowned'),('denied','disowning'), # Mrk 14:68,70
    ('departed','gone'),('departed','withdrawn'),('departed','withdrew'), # Mat 2:9,13,14
    ('desert','ˊₐrāⱱāh'),('plain','ˊₐrāⱱāh'),
    ('deserted','desolate'),
    ('destroyed','consumed'),('destroyed','devoured'),
    ('destruction','devastation'),
    ('determine','ascertained'), # Mat 2:7
    ('die','pass away'), # Mrk 13:30
    ('died','dead'),('died','expired'), # Mrk 12:26, 15:39
    ('dies','corpse'), # Lev 19:28
    ('dinosaur','dragon'), # Rev 12:3
    ('disasters','plagues'),
    ('discouraged','dismayed'),
    ('disgrace','expose'), # Mat 1:19
    ('disown','renounce'), # Mrk 14:31
    ('distance','afar'), # Mrk 14:54
    ('divorce','send'), # Mat 1:19
    ('down','below'), # Mrk 14:66
    ('dressed','clothed'), # Mrk 16:5
    ('driving','throwing'),
    ('each','all'), # Mrk 14:23
    ('eastern','east'),
    ('eliminate','destroying'),
    ('engaged','betrothed'),
    ('ensure','order'), # Mrk 14:19
    ('entered','come'), # Mat 2:11
    ('enthusiastic','eager'), # Mrk 14:38
    ('entire','all'),
    ('entrance','door'), # Mrk 16:3
    ('everyone','all'),('everyone','people'),('everyone','one'),('everyone','you all'),
        ('Everyone','one'),
    ('everywhere','all'), # Mrk 15:33
    ('evidence','fruit'), # Mat 3:8
    ('evil','sinners'), # Mrk 14:41
    ('executed','death'), # Mrk 13:12
        ('execution','stake'),
    ('exhaled','expired'), # Mrk 15:37
    ('existence','became'),
    ('exposed','uncovered'),
    ('fellow','man'), # Mrk 14:51
    ('finally','Lastly'),('finally','last'),
    ('find','saw'), # Mrk 16:5
    ('fitting','befitting'),
    ('flames','fire'),
    ('flattered','saying'),
    ('flicked','sprinkled'),
    ('food','bread'),
    ('forced','compelling'), # Mrk 15:21
    ('forever','perpetuity'),
    ('front','before'),('front','face'), # Mrk 13:9
    ('fulfilled','accomplished'),
    ('gathered','coming together'), # Mrk 14:53
    ('get','take'), # Mrk 15:36
    ('God','god'),
    ("God's",'god'),("God's",'holy'), # Mrk 14:25, 13:11
    ('godly','devout'),('godly','righteous'),
    ('grab','apprehending'),('grab','apprehend'),('grabbed','taken'), # Mrk 14:51
    ('grapevine','vine'),('grapes','vine'), # Mrk 14:25
    ('greater','mightier'),
    ('guard','doorkeeper'),('guard','securely'), # Mrk 13:34, 14:44
    ('guide','shepherding'), # Mat 2:6
    ('guy\'s','man'), # Mrk 14:69
    ('hand','giving'),('handed','given'), # Mrk 13:11, 14:41
    ('happen','become'),('happen','becoming'),('happening','becoming'), # Mrk 13:29
    ('happy','elated'), # Mat 2:10
    ('harvests','fruit'),
    ('have','bearing'), # Mat 1:21
    ('heavenly','heavens'),('heavenly','heaven'),
    ('held','giving'), # Mrk 15:36
    ('hills','mountains'),('hill','mountain'),
    ('hilltop','high'),
    ('honest','true'),
    ('honour','glorify'),
        ('honoured','great'), # Mrk 14:45
    ('horrible','abomination'), # Mrk 13:14
    ('huge','great'),
    ('humanity','man'), # Mrk 13:26
    ('humiliated','ashamed'),
    ('hurling','many'), # Mrk 15:3
    ('hut','shelter'),
    ('immerser','immersing'),
    ('included','among'),('including','and'), # Mrk 15:40
    ('incredible','great'), # Mrk 13:26
    ('indeed','already'), # Mrk 15:44
    ('insignificant','least'), # Mat 2:6
    ('instructed','commanded'),('instructs','commanded'), # Mrk 13:34
    ('instructions','commanded'),('instructions','regulations'),
    ('insult','slander'),('insulted','dishonoured'),('insulted','slandering'),('insulting','slandering'), # Mrk 14:64, 15:29
    ('investigate','search'), # Mat 2:8
    ('Israelis','people'),
    ('item','article'),('items','article'),
    ('jealous','envy'), # Mrk 15:10
    ('jobs','work'), # Mrk 13:34
    ('judge','judgements'),
    ('kill','destroy'),
    ('King','king'),
    ('kingdoms','nations'),
    ('kingly','purple'), # Mrk 15:17
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
    ('louder','exceedingly'), # Mrk 15:14
    ('loved','beloved'),
    ('lying','lied'),
    ('mankind','humans'),
    ('many','multiply'),
    ('marry','receive'), # Mat 1:20
    ('marvelled','astonished'),
    ('means','translated'), # Mrk 15:22
    ('meat','flesh'),
    ('meeting','counsel'), # Mrk 15:1
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
    ('nearby','by'), # Mrk 15:35
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
    ('opened','divided'),('opening','door'), # Mrk 15:46
    ('other','across'),
    ('outside','out'), # Mrk 15:20
    ('over','elapsed'), # Mrk 16:1
    ('own','possession'),('owned','having'),
    ('ordered','commanded'),
    ('paralysed','paralytic'),
    ('Passover','feast'), # Mrk 15:6
    ('path','way'),('path','road'),
    ('people','humans'),('people','multitude'),('people','ones'),
    ('percent','add'),
    ('period','time'),
    ('permanent','perpetuity'),
    ('permission','requested'), ('permission','granted'), # Mrk 15:43,45
    ('picked','taken'), # Mrk 14:23
    ('placed','laid'),('placed','lying'),('placing','laying'), # Mat 3:10
    ('planet','earth'), # Mrk 13:31
    ('platform','lid'),
    ('pleasing', 'acceptable'),('pleasing','soothing'),
    ('Plenty','Many'),
    ('plus','and'),
    ('pondering','considered'), # Mat 1:20
    ('poor','humble'),
    ('population','multitude'),
    ('post','stake'), # Mrk 15:13
    ('praised','glorifying'),
    ('preaching','proclaiming'),
    ('prearranged','given'), # Mrk 14:44
    ('pregnant','womb'), # Mat 1:18
    ('presented','offered'), # Mat 2:11
    ('pressed','putting'), # Mrk 15:17
    ('priest','priest/officer'),
    ('proclamation','announcement'),('proclamation','declaration'),('proclamation','notice'),('proclamations','declarations'),
    ('produce','fruit'),
    ('promised','sworn'),
    ('pronounce','utterance'),
    ('protect','defend'),
    ('pure','holy'), ('purity','holiness'),
    ('quiet','desolate'),('quiet','silenced'),
        ('quietly','secretly'), # Mat 1:19
    ('range','various'),
    ('readers','reading'), # Mrk 13:14
    ('ready','gird'),
    ('realised','saw'),('realised','saying'),('realised','seen'), # Mrk 16:3, Mat 2:16
    ('rebuild','building'), # Mrk 15:29
    ('refused','forbidding'), # Mat 3:14
    ('region','land'),('regions','land'),
    ('release','send'), # Mrk 15:9
    ('relying','trust'),
    ('remembered','reminded'),
    ('replied','answering'), # Mrk 15:2
    ('reputation','name'),
    ('request','excusing'),('request','seek'),('requested','prayed'), # Mrk 15:6
    ('rescue','deliver'),
    ('responded','said'),('responded','saying'), # Mrk 14:30
    ('responsibilities','authority'), # Mrk 13:34
    ('return','coming'), # Mrk 13:35
    ('right','fitting'),('right','truth'), # Mrk 13:10, 12:32
    ('river','Yarden'),
    ('riverbed','wadi'),
    ('road','way'), # Mat 3:3
    ('robe','cloth'),('robe','clothes'), # Mrk 14:51,63
    ('rock','stone'),('rocks','stones'),('rocks','stone'),
        ('rockface','rock'), # Mrk 15:46
    ('roof','housetop'),('roofs','housetops'),
    ('room','place'),
    ('ropes','cords'),
    ('rubble','ruin'),
    ('rush','hasten'),
    ('sacred','holiness'),('sacred','holy'), ('sacred','of meeting'), # tent of meeting
    ('sacrificed','smoke'),
    ('saluting','greeting'), # Mrk 15:18
    ('same','again'), # Mrk 14:70
    ('sanctuary','hideout'),
    ('saw','observing'), # Mrk 16:4
    ('scared','dismayed'), ('scared','feared'),('scared','fearing'), # Mrk 16:*
    ('scoffed','mocking'),
    ('scriptures','scroll'), # Mrk 12:26
    ('search','seek'),('search','seeking'), # Mat 2:13
    ('second','another'),
    ('secured','apprehended'), # Mrk 14:46
    ('See','Behold'),
        ('Seeing','seen'), # Mat 2:10
    ('sentenced','condemned'),('sentenced','put'), # Mrk 14:55,64
    ('servants','attendants'), # Mrk 14:54
    ('settled','dwelt'), # Mat 2:@3
    ('several','many'), # Mrk 14:56
    ('shaking','trembling'), # Mrk 16:8
    ('shaved','baldness'),
    ('shed','hut'),
    ('She\'s','She'),
    ('shouted','saying'),('shouting','saying'), # Mrk 14:63, 15:29
    ('shrines','places'),
    ('shore','side'),
    ('should','let'),('should','may'), # Mrk 15:12
    ('sick','sickly'),
    ('Similarly','Likewise'),('similar','likewise'), # Mrk 14:31
    ('single','one'), # Mrk 14:37
    ('sitting','reclining'),
    ('sky','heaven'),('skies','heavens'),
    ('skin','hide'),
    #('slave','servant'), # TODO: Need to add code to prevent this substitution if BOTH words occur in the verse.
    ('small','little'),
    ('snakes','vipers'), # Mat 3:7
    ('So','And'),('So','Therefore'),
    ('soaked','filled'), # Mrk 15:36
    ('someone','anyone'),('someone','One'), # Mrk 15:36
    ('something','one message'),
    ('songs','psalms'),('songs','hymns'), # Mrk 14:26
    ('sons','boys'), # Mat 2:16
    ('sour','vinegar'), # Mrk 15:36
    ('spiced','myrrh'), # Mrk 15:23
    ('splendour','glory'),
    ('spoken','said'),('spoken','saying'),
    ('started','began'),('started','arriving'), # Mat 3:1
    ('staying','dwelling'),
    ('steeled','courage'), # Mrk 15:43
    ('stewards','managers'),
    ('stick','staff'),('stick','reed'), # Mrk 15:19,36
    ('stopped','stood'), # Mat 2:9
    ('strong','forceful'),
    ('stunned','amazed'),('stunned','amazement'), # Mrk 16:5,8
    ('Sunday','first'), # Mrk 16:2
    ('surprised','amazed'), # Mrk 16:6
    ('swindlers','robbers'),
    ('taken','carried'), # Mrk 15:1
    ('talk','spoke'), # Mrk 16:8
        ('talking','speaking'), ('talking','saying'),
    ('tarpaulin','cover'),
    ('tattoo','inscription'), # Lev 19:28
    ('teachers','scribes'),
    ('teaching','saying'), # Mrk 14:27
        ('teachings','messages'), # Mrk 13:31
    ('tell','saying'), # Mat 3:9
        ('telling','proclaimed'),('telling','saying'),('telling','speaking'),
        ('tells','say'),
    ('tent','tabernacle'),
    ('territory','land'), # Mat 2:6
    ('that','this'),('that','which'),
    ('themselves','hearts'),
    ('Then','And'),('then','And'),('then','immediately'), # Mrk 14:72
    ('thief','robber'), # Mrk 14:48
    ('think','wondered'),('think','suppose'), # Mat 3:9
    ('thinking','reasoning'),('thinking','supposing'),
    ('third','another'),
    ('thought','saying'), # Mrk 15:35
        ('thoughtful','intelligently'), # Mrk 12:34
    ('through','by'), # Mat 1:18
    ('tied','bound'),
    ('time','hour'), # Mrk 13:32
    ('tipped','overturned'),
    ('told','commanded'),('told','saying'),('told','said'), # Mrk 14:34, Mat 2:5
    ('total','all'),
        ('totally','greatly'), # Mrk 16:5
    ('town','city'),
    ('trip','travelling'), # Mrk 13:34
    ('trustworthy','faithful'),
    ('trying','seeking'), # Mrk 14:55
    ('turned','giving'), # Mrk 13:9
    ('twenty','fifth'),
    ('undesirables','sinners'),
    ('ungodly','unclean'),
    ('upset','disturbed'), # Mat 2:3
    ('upstairs','housetop'),('upstairs','upper'), # Mrk 13:15
    ('unquenchable','inextinguishable'), # Mat 3:12
    ('untarnished','holy'),
    ('urged','implored'),
    ('very','much'),('very','exceedingly'), # Mrk 12:27, 16:2
    ('wallet','purse'),
    ('wanting','seeking'), # Mat 2:20
    ('warned','spoken'), # Mrk 13:23
    ('warriors','men'),
    ('watching','observing'), # Mrk 15:47
    ('waters','water supplies'),
    ('way','how'),
    ('wealthy','rich'),
    ('wearing','clothed'), # Mrk 14:51
    ('went','came'),('went','come'), # Mrk 16:5
    ('whacking','striking'), # Mrk 15:19
    ('what','whatever'),("What's",'What'),
    ('When','And'),('When','whenever'),
    ('whipped','beat'), # Mrk 13:9
    ('whole','all'),
    ('will','are'),
    ('wishing','willing'), # Mat 1:19
    ('women','daughters'),
    ('work','service'),
    ('worried','alarmed'), # Mrk 13:7
    ('worship','bow'),('worship','prostrate'), # Mat 2:2
        ('worshipped','prostrated'), # Mat 2:11
    ('worn','girding'),
    ('wow','see'),
    ('written','inscribed'), # Mrk 15:26
    ('wrong','strayed'),('wrong','evil'), # Mrk 12:24,27, 15:14
    ('yelled','cried'),
    ('young','little'), # Mrk 15:40
        ('younger','lower'), # Mat 2:16
    ('yourselves','hearts'),

    # Words added after analysis of unmatched LV glosses
    ('missionaries','ambassadors'),
    ('chains','bonds'),
    ('forever','eternal'),
    ('miracles','signs'), ('miracles','wonders'),
    ('dear','beloved'),
    ('killed','slain'),
    ('faithfulness','loyalty'),
    ('leaders','rulers'), ('leader','ruler'),
    ('servants','slaves'),
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

    # Additional vocabulary mappings from Mark analysis (2026-10-09)
    # Non-verb mappings (verbs handled by matchVerbSets)
    ('apprentices', 'apprentices/followers'),
    ('religious', 'scribes'),
    ('lake', 'sea'),
    ('started', 'began'),
    #('heals', 'healed'), # Already in SIMPLE_VERB_TABLE
    ('happen', 'become'),
    ('enter', 'go in'),
    ('replied', 'answered'),
    ('listen', 'hear'),
    ('arrested', 'given over'),
    ('continued', 'remained'),
    ('responded', 'answered'),
    ('understand', 'know'),
    ('noticed', 'saw'),
    ('wants', 'wills'),
    ('yelled', 'cried out'),
    ('scolded', 'rebuked'),
    ('arrived', 'came'),
    ('preaching', 'proclaiming'),
    ('crowd', 'multitude'),
    #('teaching', 'teaching'),
    #('authority', 'authority'),
    #('temple', 'temple'),
    #('teacher', 'teacher'),
    ('chief', 'chief priest'),
    #('life', 'life'),
    #('time', 'time'),
    #('person', 'person'),
    #('place', 'place'),
    #('home', 'home'),
    #('house', 'house'),
    #('word', 'word'),
    #('things', 'thing'),
)
for someTuple in RV_SINGLE_WORDS_FROM_LV_WORD_STRINGS:
    assert isinstance( someTuple, tuple), f'{someTuple=}'
    RVWord, LVWords = someTuple
    assert RVWord != LVWords, f'{RVWord=}'
    assert ' ' not in RVWord
    for simpleVerbSet in SIMPLE_VERB_SETS:
        if LVWords in simpleVerbSet:
            assert RVWord not in simpleVerbSet or (RVWord,LVWords) in {('lying','lied'),('clothes','clothing'),('fish','fishes')}, f"Can simplify {RVWord=} {LVWords=}"


LV_SINGLE_WORDS_TO_RV_WORD_STRINGS = (
            ('brothers', 'brothers and sisters'), ('brothers', 'fellow believers'),
            ('Brothers', 'Brothers and sisters'), ('Brothers', 'Fellow believers'),
            ('Brothers', 'brothers and sisters'), ('Brothers', 'fellow believers'),

            ('Higgaion', 'Meditation break'),
            ('Şelāh', 'Instrumental break'),
            ('Truly', 'May it be so'),

            ('afar','Further back'), # Mrk 15:40
            ('anymore','any more'), # Mrk 14:63
            ('approached','came closer'), # Mrk 12:28
            ('ascent','walking uphill'),
            ('ascertained','found out'), # Mat 2:16
            ('asked','find out'), # Mrk 15:44
            ('bore','was the father of'),('bore','the father of'), # Mat 1
            ('pre-day','day before'), # Mrk 15:42
            ('false','making up'), # Mrk 14:56
            ('first','most important'), # Mrk 12:29
            ('fled','ran away'),('fled','took off running'), # Mrk 14:52, 16:8
            ('food','lived on'), # Mat 3:4
            ('greater','more important'), # Mrk 12:31
            ('members', 'body parts'),
            ('knowing','sleep with'), # Mat 1:25
            ('known', 'found out'), # Mrk 15:45
            ('plagues', 'deadly diseases'),
            ('raised','came back to life'), # Mrk 16:6
                ('raised','Get ready'), # Mat 2:20
                ('raised','packed up'), # Mat 2:21
            ('repenting','Turn from'), # Mat 3:2
            ('right','honoured position'), # Mrk 14:62
            ('risen', 'got up'),
            ('sanctuary', 'sacred tent'),
            ('scribes', 'religious teachers'),
            ('seeking', 'looking for'), # Mrk 16:6
            ('synagogues', 'Jewish meeting halls'), ('synagogues', 'meeting halls'),
            ('synagogue', 'Jewish meeting hall'), ('synagogue', 'meeting hall'),
            ('tabernacle', 'sacred tent'),
            ('three-times','three times'), # Mrk 14:72
            ('tomb','burial chamber'), # Mrk 15:46
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

            # Reverse mappings for vocabulary from Mark analysis (2026-10-09)
            #('apprentices/followers', 'apprentices'),
            #('scribes', 'religious'),
            #('sea', 'lake'),
            #('began', 'started'),
            #('healed', 'heals'),
            #('become', 'happen'),
            #('go in', 'enter'),
            #('answered', 'replied'),
            #('hear', 'listen'),
            #('given over', 'arrested'),
            #('remained', 'continued'),
            #('know', 'understand'),
            #('saw', 'noticed'),
            #('wills', 'wants'),
            #('cried out', 'yelled'),
            #('rebuked', 'scolded'),
            #('came', 'arrived'),
            #('proclaiming', 'preaching'),
            #('multitude', 'crowd'),
            #('chief priest', 'chief'),

            # Reverse mappings for vocabulary from Mark analysis (2026-10-09)
            #('apprentices/followers', 'apprentices'),
            #('scribes', 'religious'),
            #('sea', 'lake'),
            #('began', 'started'),
            #('healed', 'heals'),
            #('become', 'happen'),
            #('go in', 'enter'),
            #('answered', 'replied'),
            #('hear', 'listen'),
            #('given over', 'arrested'),
            #('remained', 'continued'),
            #('know', 'understand'),
            #('saw', 'noticed'),
            #('wills', 'wants'),
            #('cried out', 'yelled'),
            #('rebuked', 'scolded'),
            #('came', 'arrived'),
            #('proclaiming', 'preaching'),
            #('multitude', 'crowd'),
            #('chief priest', 'chief'),

            # Reverse mappings for vocabulary from Mark analysis (2026-10-09)
            #('apprentices/followers', 'apprentices'),
            #('scribes', 'religious'),
            #('sea', 'lake'),
            #('began', 'started'),
            #('healed', 'heals'),
            #('become', 'happen'),
            #('go in', 'enter'),
            #('answered', 'replied'),
            #('hear', 'listen'),
            #('given over', 'arrested'),
            #('remained', 'continued'),
            #('know', 'understand'),
            #('saw', 'noticed'),
            #('wills', 'wants'),
            #('cried out', 'yelled'),
            #('rebuked', 'scolded'),
            #('came', 'arrived'),
            #('proclaiming', 'preaching'),
            #('multitude', 'crowd'),
            #('chief priest', 'chief'),

            # Reverse mappings for vocabulary from Mark analysis (2026-10-09)
            #('apprentices/followers', 'apprentices'),
            #('scribes', 'religious'),
            #('sea', 'lake'),
            #('began', 'started'),
            #('healed', 'heals'),
            #('become', 'happen'),
            #('go in', 'enter'),
            #('answered', 'replied'),
            #('hear', 'listen'),
            #('given over', 'arrested'),
            #('remained', 'continued'),
            #('know', 'understand'),
            #('saw', 'noticed'),
            #('wills', 'wants'),
            #('cried out', 'yelled'),
            #('rebuked', 'scolded'),
            #('came', 'arrived'),
            #('proclaiming', 'preaching'),
            #('multitude', 'crowd'),
            #('chief priest', 'chief')
    )
for someTuple in LV_SINGLE_WORDS_TO_RV_WORD_STRINGS:
    assert isinstance( someTuple, tuple), f"{someTuple=}"
    LVWord,RVWords = someTuple
    assert LVWord != RVWords, f"{RVWords=}"
    assert ' ' not in LVWord, f"Unexpected space in {LVWord=}"
    assert ' ' in RVWords, f'Expected a space in {RVWords=}'

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
        # Try to connect identical spellings between the two lists
        # If the lists have the same length and structure, try to match in order
        if len(rvCapitalisedWordList) == len(lvCapitalisedWordList):
            # Try order-based matching first
            for i, rvCapitalisedWord in enumerate(rvCapitalisedWordList[:]):
                if i >= len(lvCapitalisedWordList): break
                lvCapitalisedWord = lvCapitalisedWordList[i]
                if '¦' not in lvCapitalisedWord: continue
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
            # If still have items, fall back to cross-matching
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
    nounWords = set(SIMPLE_NOUNS_FLAT) | set(verbalNouns) # Only nouns get number-variant matching; verbs and adjectives are handled elsewhere
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

    # Name variations from NT (RV name -> LV name)
    'jordan': { 'yarden' },

    # Per-book custom equivalences
    # Gospel/Acts narrative style
    'gospel_equivalences': {
        'said': { 'spoke', 'told', 'declared' },
        'asked': { 'inquired', 'questioned' },
        'answered': { 'replied', 'responded' },
        'went': { 'journeyed', 'traveled', 'departed' },
        'came': { 'arrived', 'approached' },
        'saw': { 'beheld', 'observed' },
        'heard': { 'listened' },
        'did': { 'performed', 'accomplished' },
        'made': { 'created', 'formed' },
        'gave': { 'bestowed', 'granted' },
        'took': { 'received', 'accepted' },
        'found': { 'discovered', 'met' },
        'knew': { 'understood', 'recognized' },
        'believed': { 'trusted', 'had faith' },
        'followed': { 'accompanied', 'went after' },
        'left': { 'departed', 'abandoned' },
        'stayed': { 'remained', 'dwelt' },
        'entered': { 'went into', 'came into' },
        'went out': { 'exited', 'departed' },
        'turned': { 'returned', 'converted' },
        'rose': { 'arose', 'stood up' },
        'fell': { 'collapsed', 'dropped' },
        'sat': { 'seated', 'rested' },
        'stood': { 'rose', 'stood up' },
        'walked': { 'journeyed', 'traveled' },
        'ran': { 'hurried', 'fled' },
        'slept': { 'rested', 'lay down' },
        'awoke': { 'woke up', 'rose' },
        'ate': { 'dined', 'feasted' },
        'drank': { 'imbibed' },
        'prayed': { 'petitioned', 'supplicated' },
        'blessed': { 'consecrated', 'sanctified' },
        'healed': { 'cured', 'restored' },
        'taught': { 'instructed', 'discipled' },
        'preached': { 'proclaimed', 'heralded' },
        'baptized': { 'immersed', 'washed' },
        'cast out': { 'exorcised', 'drove out' },
        'forgave': { 'pardoned', 'remitted' },
        'judged': { 'condemned', 'evaluated' },
        'condemned': { 'sentenced', 'damned' },
        'crucified': { 'executed', 'hanged' },
        'rose again': { 'was resurrected', 'lived again' },
        'ascended': { 'went up', 'was taken up' },
        'descended': { 'came down', 'went down' },
        'appeared': { 'manifested', 'showed himself' },
        'vanished': { 'disappeared', 'became invisible' },
    },

    # Epistle style (Pauline and general)
    'epistle_equivalences': {
        'therefore': { 'wherefore', 'consequently', 'so then' },
        'however': { 'nevertheless', 'yet', 'but' },
        'moreover': { 'furthermore', 'besides', 'also' },
        'nevertheless': { 'notwithstanding', 'however' },
        'accordingly': { 'consequently', 'therefore' },
        'thus': { 'so', 'in this way' },
        'hence': { 'therefore', 'consequently' },
        'since': { 'because', 'forasmuch as' },
        'whereas': { 'although', 'while' },
        'inasmuch as': { 'since', 'because' },
        'inasmuch': { 'to the degree that', 'as' },
        'whereby': { 'by which', 'through which' },
        'wherefore': { 'therefore', 'why' },
        'whence': { 'from where', 'from which' },
        'whereupon': { 'upon which', 'after which' },
        'hereby': { 'by this', 'through this' },
        'herein': { 'in this', 'here in' },
        'thereof': { 'of it', 'of that' },
        'therein': { 'in it', 'in that' },
        'wherewith': { 'with which', 'by which' },
        'whereof': { 'of which', 'of what' },
        'whereunto': { 'to which', 'to what' },
        'behold': { 'lo', 'see', 'observe' },
        'lo': { 'behold', 'see' },
        'verily': { 'truly', 'amen', 'certainly' },
        'amen': { 'verily', 'truly', 'so be it' },
        'selah': { 'pause', 'reflect' },
        'albeit': { 'although', 'though' },
        'notwithstanding': { 'nevertheless', 'despite' },
        'whereas': { 'although', 'since' },
        'wheresoever': { 'wherever', 'whenever' },
        'whithersoever': { 'wherever', 'where' },
        'whosoever': { 'whoever', 'anyone who' },
        'whatsoever': { 'whatever', 'anything that' },
        'whichever': { 'which ever', 'any which' },
        'whereto': { 'to which', 'to what' },
        'wherefrom': { 'from which', 'from where' },
        'whereinto': { 'into which', 'into what' },
        'whereof': { 'of which', 'of what' },
        'whereby': { 'by which', 'through which' },
        'wherewith': { 'with which', 'by which' },
        'whereon': { 'on which', 'upon which' },
        'whereunder': { 'under which', 'beneath which' },
        'whereover': { 'over which', 'above which' },
        'wherethrough': { 'through which', 'by means of which' },
        'wherebetween': { 'between which', 'among which' },
        'whereamong': { 'among which', 'in the midst of which' },
        'whereamidst': { 'amidst which', 'in the midst of which' },
        'whereagainst': { 'against which', 'opposed to which' },
        'wherebefore': { 'before which', 'prior to which' },
        'whereafter': { 'after which', 'subsequent to which' },
        'whereabove': { 'above which', 'higher than which' },
        'wherebelow': { 'below which', 'lower than which' },
        'wherebeyond': { 'beyond which', 'past which' },
        'wherearound': { 'around which', 'about which' },
        'whereacross': { 'across which', 'over which' },
        'wherealong': { 'along which', 'by which' },
        'whereamid': { 'amid which', 'in the midst of which' },
        'whereamongst': { 'amongst which', 'among which' },
        'wherebetwixt': { 'between which', 'betwixt which' },
        'wherefrom': { 'from which', 'from where' },
        'whereagainst': { 'against which', 'in opposition to which' },
        'wherebefore': { 'before which', 'prior to which' },
        'whereafter': { 'after which', 'following which' },
        'whereabove': { 'above which', 'higher than which' },
        'wherebelow': { 'below which', 'beneath which' },
        'wherebeyond': { 'beyond which', 'further than which' },
        'wherearound': { 'around which', 'about which' },
        'whereacross': { 'across which', 'over which' },
        'wherealong': { 'along which', 'by which' },
        'whereamid': { 'amid which', 'in the midst of which' },
        'whereamongst': { 'amongst which', 'among which' },
        'wherebetwixt': { 'between which', 'betwixt which' },
    },

    # High-frequency function word variations (NT-wide)
    'that': { 'which', 'who' },
    'zebedee': { 'zebedaios' },
    'bartholomew': { 'bartholomaios' },
    'matthew': { 'matthaios' },
    'thaddeus': { 'thaddaios' },
    'jairus': { 'yaeiros' },
    'bartimaeus': { 'bartimaios' },
    'jericho': { 'yeriho' },
    'bethphage': { 'beyt-fagey' },
    'pilate': { 'pilatos' },
    'peter': { 'petros' },
    'andrew': { 'andreas' },
    'zebedaios': { 'zebedee' },
    'jairus': { 'yairos' },
    'james': { 'iakovos' },
    'bartimaeus': { 'bartimaios' },
    'jericho': { 'yeriho' },
    'bethphage': { 'beyt-fagey' },
    'pilate': { 'pilatos' },
    'peter': { 'petros' },
    'andrew': { 'andreas' },
    'philip': { 'filippos' },
    'barnabas': { 'barnabas' },
    'silas': { 'silas' },
    'timothy': { 'timotheos' },
    'titus': { 'titos' },
    'luke': { 'loukas' },
    'mark': { 'markos' },
    'john': { 'ioannes' },
    'paul': { 'paulos' },
    'simon': { 'simon' },
    'thomas': { 'thomas' },
    'judas': { 'ioudas' },
    'herod': { 'herodes' },
    'caiaphas': { 'kaiaphas' },
    'annas': { 'annas' },
    'gamaliel': { 'gamaliel' },
    'stephen': { 'stephanos' },
    'philip': { 'filippos' },
    'prochorus': { 'prochoros' },
    'nicanor': { 'nikanor' },
    'timon': { 'timon' },
    'parmenas': { 'parmenas' },
    'nicolas': { 'nikolaos' },
    'stephen': { 'stephanos' },
    'saul': { 'saulos' },
    'barnabas': { 'barnabas' },
    'john_mark': { 'ioannes_markos' },
    'aquila': { 'akylas' },
    'priscilla': { 'priskilla' },
    'apollos': { 'apollos' },
    'agabus': { 'agabos' },
    'philip_evangelist': { 'filippos' },
    'cornelius': { 'kornelios' },
    'peter': { 'petros' },
    'john': { 'ioannes' },
    'james': { 'iakovos' },
    'andrew': { 'andreas' },
    'philip': { 'filippos' },
    'bartholomew': { 'bartholomaios' },
    'thomas': { 'thomas' },
    'matthew': { 'matthaios' },
    'james_alphaeus': { 'iakovos_alphaios' },
    'thaddaeus': { 'thaddaios' },
    'simon_zealot': { 'simon_zelotes' },
    'judas_iscariot': { 'ioudas_iskariotes' },
    'matthias': { 'matthias' },
    'joseph_barsabbas': { 'iosepos_barsabbas' },
    'justus': { 'ioustos' },
    'stephen': { 'stephanos' },
    'philip': { 'filippos' },
    'prochorus': { 'prochoros' },
    'nicanor': { 'nikanor' },
    'timon': { 'timon' },
    'parmenas': { 'parmenas' },
    'nicolas': { 'nikolaos' },
    'stephen': { 'stephanos' },
    'saul': { 'saulos' },
    'barnabas': { 'barnabas' },
    'john_mark': { 'ioannes_markos' },
    'aquila': { 'akylas' },
    'priscilla': { 'priskilla' },
    'apollos': { 'apollos' },
    'agabus': { 'agabos' },
    'philip': { 'filippos' },
    'cornelius': { 'kornelios' },
    'peter': { 'petros' },
    'john': { 'ioannes' },
    'james': { 'iakovos' },
    'andrew': { 'andreas' },
    'philip': { 'filippos' },
    'bartholomew': { 'bartholomaios' },
    'thomas': { 'thomas' },
    'matthew': { 'matthaios' },
    'james_alphaeus': { 'iakovos_alphaios' },
    'thaddaeus': { 'thaddaios' },
    'simon_zealot': { 'simon_zelotes' },
    'judas_iscariot': { 'ioudas_iskariotes' },
    'matthias': { 'matthias' },
    'joseph_barsabbas': { 'iosepos_barsabbas' },
    'justus': { 'ioustos' },

    # Group/people names from NTNames table
    'jews': { 'youdaions', 'ioudaion', 'ioudaions' },
    'jew': { 'youdaion', 'ioudaion' },
    'gentiles': { 'ethne', 'ethnesin' },
    'samaritans': { 'samareitai', 'samareitasin' },
    'pharisees': { 'pharisaios', 'pharisaiousin' },
    'sadducees': { 'saddoukaios', 'saddoukaiousin' },
    'herodians': { 'herodianoi', 'herodianousin' },
    'scribes': { 'grammateus', 'grammateusin' },
    'lawyers': { 'nomikos', 'nomikousin' },
    'priests': { 'hiereus', 'hiereusin' },
    'levites': { 'leuites', 'leuitesin' },
    'disciples': { 'mathetes', 'mathetesin' },
    'apostles': { 'apostolos', 'apostolousin' },
    'prophets': { 'prophetes', 'prophetesin' },
    'elders': { 'presbyteros', 'presbyterousin' },
    'rulers': { 'archon', 'archontesin' },
    'crowds': { 'ochlos', 'ochlousin' },
    'multitudes': { 'ochlos', 'ochlousin' },
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

    We throw away edge punctuation, transliteration accents, hyphens, macrons, and the possessive 's,
        because 'Preparation' and 'preparation' are the same word to us, but
        'mother-in-law' and 'mother' are not (and 'money-changers' and 'moneychangers' are).
    """
    word = unicodedata.normalize( 'NFD', word )
    word = ''.join( ch for ch in word if unicodedata.category( ch ) not in ('Mn', 'Lm') ) # Strip combining marks and modifier letters
    word = re.sub( r"[ʼˊʹʺʸˈ]", '', word ) # Transliteration accents
    word = re.sub( r"/.*$", '', word ) # Strip parenthetical alternatives like /(Miryām)
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


def buildSegments( words:List[str], segmentLength:int=2 ) -> List[List[str]]:
    """
    Build overlapping segments of given length from a word list.
    E.g. for ['the', 'chief', 'priests'] with length 2: [['the','chief'], ['chief','priests']]
    """
    if len(words) < segmentLength:
        return [words]
    return [words[i:i+segmentLength] for i in range(len(words) - segmentLength + 1)]


def scoreSegments( rvSeg:List[str], lvSeg:List[str], rvWord:str, lvWord:str, bookType:str='narrative' ) -> Optional[Tuple[str,int]]:
    """
    Score two segments (lists of simplified words).
    Returns (why, score) or None if no match.
    """
    if len(rvSeg) != len(lvSeg):
        return None
    # Score each word pair in the segment
    totalScore = 0
    for rvW, lvW in zip(rvSeg, lvSeg):
        cell = scoreRVLVWords( rvW, lvW )
        if cell is None:
            return None
        totalScore += cell[1]
    # Average score per word
    avgScore = totalScore // len(rvSeg)
    return ('segment', avgScore)


def bestSegmentAlignmentScore( rvSegments:List[List[str]], lvSegments:List[List[str]],
                                rvWords:List[str], lvWords:List[str], bookType:str='narrative' ) -> Tuple[int,List[Tuple[int,int]]]:
    """
    Find the best order-preserving alignment using segment-level scoring.
    """
    numRows, numCols = len(rvSegments), len(lvSegments)
    NEG = -1_000_000
    best = [[NEG]*(numCols+1) for _ in range(numRows+1)]
    best[0][0] = 0
    # For backtracking, store which segment was matched
    prev = [[None]*(numCols+1) for _ in range(numRows+1)]

    for i in range(numRows+1):
        for j in range(numCols+1):
            if best[i][j] == NEG: continue
            total = best[i][j]
            if i < numRows and j < numCols:
                cell = scoreSegments( rvSegments[i], lvSegments[j], rvWords[i] if i < len(rvWords) else '', lvWords[j] if j < len(lvWords) else '', bookType )
                if cell is not None:
                    if total + cell[1] > best[i+1][j+1]:
                        best[i+1][j+1] = total + cell[1]
                        prev[i+1][j+1] = ('match', i, j)
            if i < numRows and total > best[i+1][j]:
                best[i+1][j] = total
                prev[i+1][j] = ('skip_rv', i, j)
            if j < numCols and total > best[i][j+1]:
                best[i][j+1] = total
                prev[i][j+1] = ('skip_lv', i, j)

    # Backtrack
    alignment, i, j = [], numRows, numCols
    while i > 0 or j > 0:
        if prev[i][j] is None:
            if i > 0 and j > 0 and best[i][j] == best[i-1][j-1]:
                i, j = i-1, j-1
            elif i > 0 and best[i][j] == best[i-1][j]:
                i -= 1
            else:
                j -= 1
        else:
            action, pi, pj = prev[i][j]
            if action == 'match':
                alignment.append( (pi, pj) )
            i, j = pi, pj
    alignment.reverse()
    return best[numRows][numCols], alignment


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
                lvWordSimple = simplifyRVLVWord( lvWordStr.split( '¦' )[0] )
                if lvNumber is None or lvWordSimple != lvWord:
                    isMatch = False;
                    if BBB == 'MRK' and c == 1 and v == 42 and lvWords == ('he', 'was', 'cleansed'):
                        break
                lvNumbers.add( lvNumber )
            if isMatch and len( lvNumbers ) == 1:
                lvNum = lvNumbers.pop()
                candidates.append( (ix, lvNum) )
        if candidates:
            lvCandidates[ lvWords ] = candidates
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

        # Check if this LV phrase exists in the current verse
        if lvWords not in lvCandidates:
            continue

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


def alignGap( rvGap:List[str], gapGroups:List[dict], CANDIDATE_PAIRS:dict, stillFree:set ) -> List[Tuple[str,int]]:
    """
    Find a monotone alignment between RV gap words and LV gap groups.
    Returns list of (rvWord, lvNumber) pairs.
    """
    if not rvGap or not gapGroups:
        return []
    rvPlain = [ simplifyRVLVWord(w) for w in rvGap ]
    # Build LV alternatives for each group
    lvAlts = []
    lvNumbers = []
    for grp in gapGroups:
        alts = [ simplifyRVLVWord(a) for a in grp['alts'] ]
        lvAlts.append( alts )
        lvNumbers.append( grp['num'] )

    # Score matrix for monotone alignment
    n, m = len(rvPlain), len(lvAlts)
    scoreMatrix = [ [ None ]*m for _ in range(n) ]
    for i,rvW in enumerate(rvPlain):
        for j in range(m):
            if lvNumbers[j] is None: continue
            # Check if any alternative matches
            for alt in lvAlts[j]:
                if simplifyRVLVWord(rvW) == alt:
                    scoreMatrix[i][j] = ('exact', 100)
                    break
                elif (rvW, alt) in CANDIDATE_PAIRS:
                    scoreMatrix[i][j] = ('learned', 50)
                    break
    # Find best monotone alignment
    bestScore, alignment = bestMonotoneAlignmentScore( scoreMatrix )
    if not alignment or bestScore <= 0:
        return []
    # Verify each pair is still free
    pairs = []
    for i,j in alignment:
        rvWord = rvGap[i]
        lvNumber = lvNumbers[j]
        if simplifyRVLVWord(rvWord) in stillFree:
            pairs.append( (rvWord, lvNumber) )
    return pairs


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

        # Try exact gap size matching first (original logic)
        if len(rvGap) > 0 and len(gapGroups) > 0 and len(rvGap) == len(gapGroups):
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
        # Try partial gap alignment when sizes don't match exactly
        elif len(rvGap) > 0 and len(gapGroups) > 0:
            if any( simplifyRVLVWord( w ) not in stillFree for w in rvGap ): continue
            gapPairs = alignGap( rvGap, gapGroups, CANDIDATE_PAIRS, stillFree )
            for rvWord, lvNumber in gapPairs:
                if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 3:
                    dPrint( 'Info', DEBUGGING_THIS_MODULE, f"matchOrderedRuns adding {lvNumber} to open RV gap word '{rvWord}' from aligned gap at {BBB} {c}:{v}" )
                result = addNumberToRVWord( BBB, c,v, rvWord, lvNumber )
                if result:
                    numAdded += 1
                    if NT and 'N' in state.wordTable['NT'][lvNumber][state.wordTableHeaderList['NT'].index('GlossCaps')]:
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
        # Find all LV indexes with this noun number
        lvNounIndexes = [ i for i,(lvW,lvN) in enumerate( lvWordsParsed ) if lvN == nounNumber ]
        if not lvNounIndexes: continue
        # Group consecutive indexes with the same number (they form a single LV word with underscores)
        # We only need the FIRST index of each consecutive group
        groupedIndexes = []
        for idx in lvNounIndexes:
            if not groupedIndexes or idx != groupedIndexes[-1] + 1:
                groupedIndexes.append( idx )
        # For each group, check the word immediately before it
        for lvNounIdx in groupedIndexes:
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

    # Enhance word-level scoring with segment context for high-frequency words
    rvPlainWords = [ rvWord for _,rvWord,_ in rvRows ]
    lvPlainWords = [ lvWord for _,lvWord,_ in lvCols ]

    # Build bigram context maps for context-aware scoring
    rvBigrams = {}
    for i in range(len(rvPlainWords)-1):
        bigram = (rvPlainWords[i], rvPlainWords[i+1])
        rvBigrams[i] = bigram
        rvBigrams[i+1] = (rvPlainWords[i], rvPlainWords[i+1])

    lvBigrams = {}
    for i in range(len(lvPlainWords)-1):
        bigram = (lvPlainWords[i], lvPlainWords[i+1])
        lvBigrams[i] = bigram
        lvBigrams[i+1] = (lvPlainWords[i], lvPlainWords[i+1])

    # Re-score with bigram context boost for high-frequency words
    boostCount = 0
    for rowIx,(rvIx,rvWord,rvSearchWord) in enumerate( rvRows ):
        for colIx,(lvIx,lvWord,lvNumber) in enumerate( lvCols ):
            if scoreMatrix[rowIx][colIx] is not None:
                why, baseScore = scoreMatrix[rowIx][colIx]
                # Boost score if bigram context matches
                rvBigram = rvBigrams.get(rowIx)
                lvBigram = lvBigrams.get(colIx)
                if rvBigram and lvBigram:
                    contextMatch = sum(1 for a,b in zip(rvBigram, lvBigram) if simplifyRVLVWord(a) == simplifyRVLVWord(b))
                    if contextMatch >= 1: # At least one word in context matches
                        scoreMatrix[rowIx][colIx] = (why, baseScore + 10) # Context boost
                        boostCount += 1
    if BBB == 'MRK' and c == 15 and v == 6:
        pass
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
        why = scoreMatrix[rowIx][colIx][0] if scoreMatrix[rowIx][colIx] else 'segment'
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
    usedLVNumbers = set() # Skip any OET-LV word number that is used more than once in the verse (non-consecutively)
    seenLVNumbers = {} # Maps lvNumber to last index where it was seen
    for lvIx, lvWordStr in enumerate( lvWordList ):
        lvNumber = getLVWordNumber( lvWordStr )
        if lvNumber is None: continue
        if lvNumber in seenLVNumbers:
            # Only mark as used if it appears non-consecutively
            # (consecutive duplicates are parts of the same Greek word split by underscores)
            if lvIx != seenLVNumbers[lvNumber] + 1:
                usedLVNumbers.add( lvNumber )
        seenLVNumbers[lvNumber] = lvIx

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

    has_anchor = any( addCode in ANCHOR_ADD_CODE_TESTS for addCode,firstIx,lastIx in addSpans )
    if not has_anchor: return 0,0

    NT = bos_books_codes_py.is_new_testament_nr( BBB )
    usedLVNumbers = set() # Skip any OET-LV word number that is used more than once in the verse (non-consecutively)
    seenLVNumbers = {} # Maps lvNumber to last index where it was seen
    for lvIx, lvWordStr in enumerate( lvWordList ):
        lvNumber = getLVWordNumber( lvWordStr )
        if lvNumber is None: continue
        if lvNumber in seenLVNumbers:
            # Only mark as used if it appears non-consecutively
            # (consecutive duplicates are parts of the same Greek word split by underscores)
            if lvIx != seenLVNumbers[lvNumber] + 1:
                usedLVNumbers.add( lvNumber )
        seenLVNumbers[lvNumber] = lvIx

    # The span that each word is inside of, so we can tell a plain word from a reworded one
    spanAtIx = {}
    for addCode,firstIx,lastIx in addSpans:
        for rvIx in range( firstIx, lastIx+1 ): spanAtIx[rvIx] = (addCode,firstIx,lastIx)

    stillFree = getUnnumberedRVWords( BBB, c,v )

    numAdded = numNS = 0
    for addCode,firstIx,lastIx in addSpans:
        if addCode not in ANCHOR_ADD_CODE_TESTS: continue

        if any( '¦' in rvWordList[rvIx] for rvIx in range( firstIx, lastIx+1 ) ):

            continue # Already numbered

        if any( '¦' in rvWordList[rvIx] for rvIx in range( firstIx, lastIx+1 ) ):

            continue # Already numbered
        still_free_check = any( simplifyRVLVWord( rvWordList[rvIx] ) not in stillFree for rvIx in range( firstIx, lastIx+1 ) )

        if still_free_check:

            continue # One of the earlier matchers got there first

        candidateList = []

        for rvDirection in ( -1, 1 ): # Look at the numbered OET-RV word before the span, then the one after
            rvIx = firstIx - 1 if rvDirection == -1 else lastIx + 1

            while 0 <= rvIx < len( rvWordList ):
                span = spanAtIx.get( rvIx )
                if span is None:

                    break # A plain OET-RV word
                if span[1] == span[2]:

                    break # A one-word span, which stands for one OET-LV word

                rvIx += rvDirection # Skip over a longer span, which can stand for several OET-LV words
            if not ( 0 <= rvIx < len( rvWordList ) ):

                continue
            anchorNumber = getRVWordNumber( rvWordList[rvIx] )

            if anchorNumber is None: continue
            # Group consecutive LV indexes with the same number (they form a single LV word split by underscores)
            rawAnchorLVIndexes = [ lvIx for lvIx,lvWordStr in enumerate( lvWordList ) if getLVWordNumber( lvWordStr ) == anchorNumber ]
            # Group consecutive indexes
            anchorLVIndexes = []
            for idx in rawAnchorLVIndexes:
                if not anchorLVIndexes or idx != anchorLVIndexes[-1] + 1:
                    anchorLVIndexes.append( idx )

            if len( anchorLVIndexes ) != 1:

                continue # The OET-LV word number covers more than one distinct OET-LV word
            # For a group of consecutive LV words with the same number, we need to look
            # at the word AFTER the group (rvDirection=-1, anchor before span) or
            # BEFORE the group (rvDirection=1, anchor after span)
            if rvDirection == -1:
                # Anchor is before span, we want the word AFTER the anchor group
                candidateIx = anchorLVIndexes[-1] + 1
            else:
                # Anchor is after span, we want the word BEFORE the anchor group
                candidateIx = anchorLVIndexes[0] - 1
            if not ( 0 <= candidateIx < len( lvWordList ) ): continue
            # Skip any remaining words with the same anchor number
            while 0 <= candidateIx < len( lvWordList ):
                lvWordStr = lvWordList[candidateIx]
                lvNumber = getLVWordNumber( lvWordStr )
                if lvNumber is not None and lvNumber != anchorNumber:
                    break
                candidateIx += 1 if rvDirection == -1 else -1
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


        # Fallback for @ spans: if anchor-based approach failed, try matching to free LV pronouns directly
        if not candidateList and addCode == '@':



            # Find free LV pronouns in this verse
            freeLVPronouns = []
            for lvWordStr in lvWordList:
                lvNumber = getLVWordNumber( lvWordStr )
                if lvNumber is None or lvNumber in usedLVNumbers: continue
                lvWord = lvWordStr.split( '¦' )[0]
                simplified = simplifyRVLVWord( lvWord )

                if simplified in PERSON_PRONOUN_WORDS:
                    try:
                        _lvWord, lvNumber, lvWordRow = getLVWordRow( lvWordStr, 'NT' if NT else 'OT' )
                    except WordNumberError as e:
                        logging.critical( f"matchWordsBesideLvAnchor() fallback {e} from {BBB} {c}:{v} {lvWordStr=}" )
                        continue
                    freeLVPronouns.append( (lvNumber, lvWord, lvWordRow) )

            if len( freeLVPronouns ) == 1:
                candidateList = freeLVPronouns
            elif len( freeLVPronouns ) > 1:
                # Multiple free pronouns - for now just take the first one
                # TODO: Could add smarter matching based on proximity or span content
                candidateList = [freeLVPronouns[0]]
            elif addCode == '@' and not candidateList:
                # Cross-verse anaphora resolution for @Yeshua spans
                # Check if this span contains "Yeshua" (or "Jesus")
                spanWords = [ simplifyRVLVWord( rvWordList[i] ) for i in range( firstIx, lastIx+1 ) ]
                if any( w in ('yeshua','jesus') for w in spanWords ):
                    # Look back in recent verses for a connected @Yeshua
                    for lookbackV in range( v-1, max(0, v-10), -1 ):
                        prevResult = findRecentYeshuaConnection( BBB, c, lookbackV )
                        if prevResult:
                            prevLvNumber, prevLvWord, prevLvWordRow = prevResult
                            # Verify the previous connection was to a masculine pronoun
                            if simplifyRVLVWord( prevLvWord ) in ('he','him','his'):
                                candidateList = [(prevLvNumber, prevLvWord, prevLvWordRow)]
                                break
                    if not candidateList:
                        # Default to masculine pronouns for Yeshua
                        for lvWordStr in lvWordList:
                            lvNumber = getLVWordNumber( lvWordStr )
                            if lvNumber is None or lvNumber in usedLVNumbers: continue
                            lvWord = lvWordStr.split( '¦' )[0]
                            if simplifyRVLVWord( lvWord ) in ('he','him','his'):
                                try:
                                    _lvWord, lvNumber, lvWordRow = getLVWordRow( lvWordStr, 'NT' if NT else 'OT' )
                                except WordNumberError as e:
                                    continue
                                candidateList = [(lvNumber, lvWord, lvWordRow)]
                                break

        # Recompute candidateNumbers after potential fallback
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

        if any( '¦' in rvWordList[rvIx] for rvIx in range( firstIx, lastIx+1 ) ):

            continue # Already numbered
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
    stillFree = getUnnumberedRVWords( BBB, c,v )
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
