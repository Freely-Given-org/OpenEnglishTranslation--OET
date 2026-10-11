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
Curated lexical/name/phrase rules establish initial links. Then position-based
    matching connects remaining occurrences in gaps bounded by existing links,
    using specialised add spans and the documented clause order.
Use --dry-run and --report to evaluate changes, or --output-dir to inspect ESFM
    proposals separately. See scripts/README.md for usage, limits and validation.

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
    2026-10-10 Extracted positional alignment into oet_alignment.py; indexed verses and lexical
        forms; replaced repeated-word insertion and arbitrary pronoun fallback; added previews,
        selected-book loading and JSON audits; excluded uncertain plain additions consistently.
"""
from gettext import gettext as _
from typing import List, Tuple, Optional
from pathlib import Path
from collections import defaultdict
import logging
import re
import multiprocessing
import unicodedata
import json
import time
from functools import lru_cache

from oet_alignment import (LVToken, SEMANTIC_CODES, index_book_lines, tokenize, propose_links)

from BibleOrgSys import BibleOrgSysGlobals
from BibleOrgSys.BibleOrgSysGlobals import vPrint, fnPrint, dPrint
from BibleOrgSys.Formats.ESFMBible import ESFMBible
from bible_organisational_system import getPositiveLeadingInt, InternalBibleEntryList
import bos_books_codes_py
from bible_transliterations import transliterate_Hebrew, transliterate_Greek


LAST_MODIFIED_DATE = '2026-10-10' # by RJH
SHORT_PROGRAM_NAME = "connect_OET-RV_words_via_OET-LV"
PROGRAM_NAME = "Connect OET-RV words to OET-LV word numbers"
PROGRAM_VERSION = '1.3.0'
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
        ('landing','coming'), # Mat 3:16
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
    ('love','beloved'),('loved','beloved'), # Mat 3:17
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

    # Additional vocabulary correspondences from the 66-book RV/LV comparison.
    # Alphabetical by RV word; each reference is an unambiguous RV verse example.
    ('abandon', 'forsakes'), # PRO 15:10
    ('abandon', 'leave'), # NUM 32:15
    ('abandons', 'forsakes'), # PRO 28:13
    ('abandons', 'leaving'), # JHN 10:12
    ('abhorrent', 'abhorrence'), # ISA 66:24
    ('ability', 'power'), # PRO 3:27
    ('abode', 'dwelling'), # KI1 8:39
    ('Accept', 'receiving'), # ROM 14:1
    ('accept', 'receive'), # PRO 4:10
    ('accept', 'received'), # JHN 1:11
    ('accept', 'receiving'), # CO1 2:14
    ('accept', 'take'), # DEU 16:19
    ('accept', 'takes'), # DEU 10:17
    ('acceptable', 'acceptance'), # ISA 56:7
    ('acceptable', 'accepted'), # LEV 19:7
    ('accepted', 'acceptable'), # LUK 4:24
    ('accepted', 'acceptance'), # ISA 60:7
    ('accepted', 'received'), # ACT 8:14
    ('accepted', 'taken'), # REV 5:7
    ('accepted', 'taking'), # ACT 16:14
    ('accepting', 'receiving'), # JHN 3:11
    ('accepting', 'taking'), # MRK 7:8
    ('accepts', 'acceptable'), # ACT 10:35
    ('accident', 'inadvertence'), # NUM 35:15
    ('accidentally', 'inadvertence'), # JOS 20:3
    ('accordance', 'according'), # CH1 11:3
    ('accusation', 'accusing'), # ACT 24:2
    ('accusations', 'accuse'), # PSA 38:20
    ('accusations', 'accused'), # MAT 27:12
    ('accusations', 'accusing'), # ACT 24:13
    ('acknowledge', 'confess'), # ROM 10:9
    ('acknowledge', 'know'), # DEU 4:39
    ('acknowledge', 'recognizing'), # CO1 14:37
    ('acknowledgement', 'confessed'), # ROM 10:10
    ('acknowledging', 'confessing'), # MAT 11:25
    ('acquired', 'acquisition'), # PRO 21:6
    ('act', 'behave'), # ISA 1:4
    ('act', 'does'), # PRO 14:17
    ('act', 'work'), # PRO 21:8
    ('acted', 'did'), # HEB 11:33
    ('action', 'act'), # DAN 11:28
    ('action', 'acted'), # ISA 44:23
    ('actions', 'conduct'), # EZE 22:31
    ('actions', 'deeds'), # HOS 9:15
    ('actions', 'work'), # JN1 3:18
    ('actions', 'works'), # ROM 9:32
    ('activities', 'actions'), # CO1 12:6
    ('addition', 'besides'), # NUM 28:23
    ('addressed', 'called'), # MAT 23:7
    ('adopt', 'adoption'), # EPH 1:5
    ('adopted', 'adoption'), # ROM 9:4
    ('adulterer', 'adulteries'), # EZE 23:43
    ('adulterers', 'adultererm'), # ISA 57:3
    ('adulteress', 'adultery'), # HOS 3:1
    ('adultery', 'adulteress'), # PE2 2:14
    ('adultery', 'adulteresses'), # EZE 16:38
    ('adultery', 'adulterous'), # PRO 30:20
    ('advancing', 'progressing'), # TI2 3:9
    ('adversaries', 'foes'), # EZE 39:23
    ('advice', 'counsel'), # KI1 12:14
    ('advice', 'counsels'), # DEU 32:28
    ('advise', 'counsel'), # PRO 19:20
    ('advise', 'counselling'), # REV 3:18
    ('advise', 'counsels'), # PRO 22:20
    ('advised', 'counselled'), # JOB 26:3
    ('affirm', 'confirm'), # CO2 2:8
    ('afflict', 'strike'), # CH2 21:14
    ('afflicted', 'struck'), # CH2 26:20
    ('afraid', 'fear'), # DEU 17:13
    ('afraid', 'fears'), # KI1 1:51
    ('afterwards', 'afterward'), # HEB 12:17
    ('alienated', 'estranged'), # COL 1:21
    ('alive', 'life'), # SA1 2:6
    ('alive', 'live'), # EXO 19:13
    ('alive', 'lived'), # LUK 15:32
    ('alive', 'lives'), # SA1 20:31
    ('alive', 'living'), # ACT 25:24
    ('allied', 'alliance'), # CH2 20:37
    ('Allow', 'let'), # RUT 2:2
    ('allow', 'grant'), # PSA 140:8
    ('allow', 'let'), # EXO 21:8
    ('allow', 'permit'), # PSA 55:22
    ('allow', 'permitted'), # JDG 1:34
    ('allow', 'permitting'), # CO2 12:4
    ('allowed', 'left'), # JDG 2:23
    ('allowed', 'permitted'), # GEN 31:7
    ('allowed', 'permitting'), # LUK 6:4
    ('along', 'alongside'), # CH1 26:16
    ('amazed', 'amazement'), # LUK 4:36
    ('ambassadors', 'messengers'), # EZE 17:15
    ('ambition', 'ambitious'), # TH1 4:11
    ('ambush', 'ambusher'), # JDG 16:9
    ('ambush', 'ambushers'), # JDG 9:25
    ('ambushes', 'ambusher'), # EZR 8:31
    ('ambushes', 'ambushers'), # JER 51:12
    ('amongst', 'among'), # ACT 20:29
    ('ancestors', 'ancestral'), # ACT 24:14
    ('ancestral', 'ancestors'), # KI2 9:28
    ('ancestry', 'ancestors'), # EZR 2:59
    ('ancient', 'antiquity'), # ISA 46:10
    ('angel', 'messenger'), # EXO 32:34
    ('angels', 'messengers'), # ROM 8:38
    ('anger', 'rage'), # EST 7:10
    ('anger', 'rages'), # CO2 12:20
    ('angering', 'provoked'), # CH2 28:25
    ('angry', 'anger'), # PSA 76:7
    ('angry', 'angered'), # LUK 14:21
    ('angry', 'angering'), # ROM 10:19
    ('angry', 'angers'), # NAH 1:3
    ('angry', 'furious'), # DEU 3:26
    ('angry', 'indignant'), # ZEC 1:12
    ('angry', 'rage'), # EZE 24:8
    ('anguish', 'distress'), # PSA 107:26
    ('anguish', 'pain'), # ISA 65:14
    ('animal', 'animal[s]'), # DAN 5:21
    ('animal', 'creatures'), # DAN 8:4
    ('animal', 'livestock'), # LEV 7:26
    ('animals', 'animal[s]'), # DAN 2:38
    ('animals', 'beasts'), # CO1 15:32
    ('animals', 'creature[s]'), # PSA 50:11
    ('animals', 'creatures'), # ISA 35:9
    ('animals', 'livestock'), # EXO 12:29
    ('ankle', 'anklets'), # ISA 3:18
    ('ankle-deep', 'ankles'), # EZE 47:3
    ('Announce', 'proclaim'), # KI1 21:9
    ('announce', 'proclaiming'), # MAT 10:7
    ('announced', 'declared'), # ISA 48:14
    ('announced', 'proclaimed'), # DEU 15:2
    ('announcement', 'proclamation'), # DAN 5:29
    ('annulled', 'annulment'), # HEB 7:18
    ('anointed', 'oil'), # ZEC 4:14
    ('answer', 'respond'), # JOB 20:2
    ('answered', 'saying'), # ACT 10:30
    ('apart', 'separated'), # HEB 7:26
    ('appear', 'appearance'), # NUM 9:16
    ('appear', 'present'), # ISA 1:12
    ('appearance', 'appearing'), # TH2 2:8
    ('appeared', 'appearance'), # EZE 10:10
    ('appeared', 'presented'), # JDG 13:10
    ('appearing', 'appearance'), # SA1 28:14
    ('appearing', 'present'), # ACT 24:19
    ('appears', 'presents'), # PSA 84:7
    ('appointed', 'appointment'), # JOS 20:9
    ('appointed', 'assigned'), # KI2 8:6
    ('appointment', 'appointed'), # JOB 30:23
    ('apprentice', 'apprentice/follower'), # JHN 18:16
    ('apprentices', 'apprentice/follower'), # MAT 10:42
    ('approach', 'come'), # PSA 36:11
    ('approach', 'draw near'), # DEU 2:19
    ('approach', 'drawn near'), # ISA 41:5
    ('approach', 'drew near'), # EXO 14:20
    ('approach', 'near'), # DEU 2:19
    ('approach', 'nearing'), # HEB 7:19
    ('approached', 'coming'), # MRK 5:38
    ('approached', 'drew near'), # DEU 4:11
    ('approached', 'near'), # DEU 1:22
    ('approached', 'nearing'), # ACT 9:3
    ('approaches', 'draw near'), # LEV 22:3
    ('approaching', 'coming'), # JHN 1:47
    ('approaching', 'near'), # JHN 6:19
    ('approaching', 'nearing'), # ACT 10:9
    ('arbitrate', 'decide'), # MIC 4:3
    ('area', 'region'), # LUK 7:17
    ('areas', 'region'), # LUK 3:3
    ('arguing', 'debating'), # ACT 6:9
    ('arid', 'waterless'), # MAT 12:43
    ('armour', 'armor'), # LUK 11:22
    ('armoured', 'armours'), # CH2 26:14
    ('around', 'round'), # CH2 17:9
    ('around', 'surround'), # PSA 7:7
    ('around', 'surroundings'), # KI2 23:5
    ('arrangements', 'plans'), # EZE 42:11
    ('arrive', 'come'), # EZR 10:8
    ('arrive', 'coming'), # MAT 24:50
    ('arrived', 'come'), # ACT 21:11
    ('arrived', 'coming'), # MRK 5:15
    ('arrives', 'come'), # COL 4:10
    ('arriving', 'came'), # JDG 18:13
    ('arrogance', 'arrogant'), # PSA 31:18
    ('arrogance', 'loftiness'), # JOB 20:6
    ('arrogant', 'arrogance'), # JN1 2:16
    ('arrogant', 'proud'), # HAB 2:5
    ('arrogantly', 'pride'), # PSA 10:2
    ('ascend', 'go up'), # PSA 24:3
    ('ascend', 'went up'), # EPH 4:9
    ('ascended', 'gone up'), # EPH 4:8
    ('ascending', 'going up'), # GEN 28:12
    ('ashamed', 'shame'), # PSA 119:116
    ('ashes', 'ash[es]'), # DAN 9:3
    ('ashes', 'dust'), # KI2 23:4
    ('ask', 'enquire'), # CH2 32:31
    ('ask', 'inquiring'), # ACT 4:7
    ('ask', 'request'), # JHN 11:22
    ('ask', 'requesting'), # EPH 3:20
    ('ask', 'said'), # JER 2:8
    ('ask', 'say'), # CH1 17:6
    ('ask', 'saying'), # ACT 13:15
    ('ask', 'says'), # NUM 20:14
    ('asked', 'enquired'), # CH2 31:9
    ('asked', 'petition'), # PSA 106:15
    ('asked', 'said'), # ACT 2:37
    ('asked', 'say'), # CH1 13:12
    ('asking', 'inquiring'), # LUK 18:36
    ('asking', 'requesting'), # ACT 25:3
    ('asking', 'said'), # JDG 21:3
    ('asking', 'say'), # PRO 30:9
    ('asking', 'saying'), # ACT 22:7
    ('asks', 'enquires'), # EZE 14:10
    ('asks', 'requesting'), # MAT 7:8
    ('asks', 'said'), # JOB 35:10
    ('asks', 'says'), # ISA 40:25
    ('Assemble', 'gather'), # AMO 3:9
    ('assemble', 'assembly'), # KI2 10:20
    ('assemble', 'gather'), # DAN 11:10
    ('assemble', 'meeting'), # ISA 14:13
    ('assembled', 'assembly'), # CH1 13:4
    ('assembled', 'gathered'), # CH2 20:4
    ('assemblies', 'convocations'), # ISA 4:5
    ('assembly', 'congregation'), # KI1 12:20
    ('assessing', 'valuation'), # KI2 23:35
    ('assign', 'appoint'), # CH1 15:16
    ('assign', 'designate'), # EXO 21:13
    ('assigned', 'appointed'), # GEN 40:4
    ('assignment', 'commission'), # ROM 1:5
    ('assist', 'help'), # CH1 22:17
    ('assist', 'serve'), # NUM 3:6
    ('assistant', 'servant'), # EXO 24:13
    ('assistants', 'help'), # EZE 12:14
    ('assisted', 'helped'), # CH1 12:1
    ('associate', 'association'), # JHN 4:9
    ('associates', 'companions'), # ISA 44:11
    ('astounded', 'astonished'), # JOB 26:11
    ('astray', 'mislead'), # MIC 3:5
    ('astray', 'misleads'), # PRO 12:26
    ('astray', 'misled'), # AMO 2:4
    ('atone', 'atonement'), # EZE 43:26
    ('atonement', 'atoned'), # EXO 29:33
    ('attaches', 'binding'), # JOB 26:8
    ('attack', 'defeat'), # NUM 22:6
    ('attack', 'engage'), # ISA 7:1
    ('attack', 'fight'), # DEU 20:10
    ('attack', 'fought'), # CH2 26:6
    ('attack', 'strike'), # EZE 32:15
    ('attack', 'striking'), # LUK 22:49
    ('attacked', 'defeated'), # CH2 28:17
    ('attacked', 'engaged'), # NUM 21:1
    ('attacked', 'fighting'), # JER 34:7
    ('attacked', 'fought'), # ISA 20:1
    ('attacked', 'harassed'), # PSA 129:2
    ('attacked', 'struck'), # SA1 30:17
    ('attacker', 'attacks'), # NUM 10:9
    ('attacking', 'fighting'), # JER 34:1
    ('attacking', 'struck'), # EZE 9:7
    ('attacks', 'strike'), # EXO 21:35
    ('attempt', 'seeking'), # GAL 2:17
    ('attempted', 'sought'), # SA2 21:2
    ('attention', 'attentive'), # JOB 11:11
    ('attract', 'drawing'), # JHN 12:32
    ('attracted', 'drew'), # ACT 5:37
    ('attracts', 'draw'), # JHN 6:44
    ('authority', 'ruled'), # CH2 8:10
    ('avenge', 'avenger'), # JOS 20:5
    ('avenged', 'avenger'), # JOS 20:9
    ('avenging', 'avenger'), # NUM 35:19
    ('await', 'expecting'), # PE2 3:14
    ('await', 'waiting'), # PE2 3:13
    ('awakened', 'aroused'), # SNG 8:5
    ('awesome', 'feared'), # PSA 99:3
    ('awesomely', 'fear'), # EZE 1:18
    ('awning', 'covering'), # EZE 27:7
    ('baby', 'child'), # HEB 11:23
    ('baby', 'children'), # EXO 21:22
    ('backpack', 'knapsack'), # LUK 9:3
    ('backward', 'backwards'), # KI2 20:11
    ('baked', 'cooked'), # SA2 13:8
    ('balance', 'balancings'), # JOB 37:16
    ('bandage', 'bind'), # HOS 6:1
    ('bandage', 'bound'), # EZE 34:4
    ('bandaged', 'bound'), # ISA 1:6
    ('bandages', 'binding'), # PSA 147:3
    ('bandages', 'binds'), # JOB 5:18
    ('banner', 'signs'), # NUM 2:2
    ('banquet', 'feast'), # DAN 5:10
    ('barren', 'bare'), # JER 7:29
    ('bases', 'stands'), # KI2 25:16
    ('basin', 'laver'), # EXO 30:28
    ('basins', 'bowls'), # CH2 4:22
    ('basins', 'laver'), # KI2 16:17
    ('basins', 'lavers'), # KI1 7:43
    ('basketful', 'basket'), # AMO 8:1
    ('basketfuls', 'baskets'), # MRK 8:8
    ('battering', 'battering-ram'), # EZE 26:9
    ('battering', 'battering-rams'), # EZE 4:2
    ('battle', 'fight'), # JDG 8:1
    ('battled', 'fought'), # SA1 23:5
    ('battling', 'fighting'), # SA1 31:1
    ('beans', 'bean[s]'), # EZE 4:9
    ('bear', 'carry'), # NUM 11:14
    ('bear', 'endure'), # JER 44:22
    ('beat', 'struck'), # JNA 4:8
    ('beaten', 'struck'), # EXO 5:14
    ('beating', 'striking'), # EXO 2:11
    ('beatings', 'blows'), # PRO 20:30
    ('beauty', 'beautiful'), # SNG 2:10
    ('became', 'turned'), # ACT 9:35
    ('bedroom', 'chamber'), # CH2 22:11
    ('bedroom', 'chambers'), # SNG 1:4
    ('beg', 'imploring'), # MRK 5:7
    ('begged', 'implored'), # MRK 5:12
    ('begged', 'imploring'), # ACT 21:12
    ('begining', 'beginning'), # JER 49:34
    ('beginning', 'origins'), # EZE 16:3
    ('behave', 'act'), # DAN 12:10
    ('behave', 'acts'), # PRO 22:12
    ('behaved', 'acted'), # EZE 16:17
    ('behaviour', 'behavior'), # TIT 2:3
    ('behaviour', 'conduct'), # PE1 3:1
    ('behaviour', 'way'), # CH2 21:13
    ('behaviour', 'ways'), # EZE 18:23
    ('belief', 'believed'), # CO1 15:11
    ('believe', 'trusting'), # DEU 1:32
    ('believers', 'believed'), # ACT 4:32
    ('believers', 'believing'), # ACT 5:14
    ('bellows', 'bellow[s]'), # JER 6:29
    ('below', 'beneath'), # AMO 2:9
    ('belt', 'loincloth'), # KI2 1:8
    ('belts', 'loincloth'), # EZE 23:15
    ('beneficial', 'benefitting'), # CO1 6:12
    ('benefit', 'profit'), # JOB 22:3
    ('benefit', 'profits'), # JER 2:11
    ('bent', 'inclined'), # HOS 11:4
    ('besiege', 'siege'), # ISA 29:3
    ('besieged', 'siege'), # KI1 16:17
    ('besieged', 'surrounded'), # LAM 3:5
    ('besieging', 'siege'), # KI1 15:27
    ('bestower', 'bestows'), # ISA 23:8
    ('betrayed', 'betrayer'), # LUK 6:16
    ('betrayed', 'treacherously'), # LAM 1:2
    ('betrays', 'treacherously'), # HAB 2:5
    ('better', 'good'), # AMO 6:2
    ('Big', 'great'), # MAT 15:30
    ('big', 'great'), # ACT 17:4
    ('big', 'large'), # GAL 6:11
    ('bird', 'bird[s]'), # GEN 6:20
    ('birdie', 'bird'), # ECC 10:20
    ('birds', 'bird[s]'), # EZE 39:17
    ('birth', 'bear'), # DEU 25:6
    ('birth', 'bearing'), # LUK 1:31
    ('birth', 'bore'), # SNG 8:5
    ('birth', 'born'), # ECC 7:1
    ('birth', 'borne'), # GEN 31:43
    ('births', 'born'), # PE1 1:3
    ('bitter', 'bitterness'), # ACT 8:23
    ('bitter', 'bitternesses'), # JER 6:26
    ('bitterly', 'bitter'), # EST 4:1
    ('bitterly', 'bitterness'), # ISA 22:4
    ('bitterness', 'bitter'), # ECC 7:26
    ('black', 'blackish'), # SNG 1:6
    ('blacksmiths', 'craftsman'), # SA1 13:19
    ('blame', 'culpable'), # GEN 43:9
    ('blast', 'breathing'), # PSA 18:15
    ('blast', 'sounds'), # EXO 19:13
    ('blasts', 'sound'), # SA2 6:15
    ('blazing', 'burning'), # DAN 3:6
    ('bleeding', 'haemorrhage'), # LUK 8:43
    ('blessed', 'sanctified'), # JHN 10:36
    ('blessings', 'bless'), # DEU 21:5
    ('blew', 'blast'), # JDG 3:27
    ('block', 'stop'), # KI2 3:19
    ('blocked', 'stopped'), # CH2 32:4
    ('blocking', 'stop'), # CH2 32:3
    ('blocks', 'block[s]'), # ISA 57:14
    ('bloodshed', 'blood'), # EZE 5:17
    ('bloodshed', 'bloods'), # ISA 26:21
    ('bloodthirsty', 'bloods'), # PSA 59:2
    ('bloody', 'blood'), # HOS 6:8
    ('bloody', 'bloods'), # EXO 4:25
    ('blossom', 'bloom'), # ECC 12:5
    ('Blow', 'blast'), # JOL 2:15
    ('blow', 'blast'), # EZE 33:6
    ('blown', 'blast'), # EZE 7:14
    ('blows', 'blast'), # EZE 33:3
    ('bodies', 'corpse'), # JER 34:20
    ('bodies', 'corpse[s]'), # AMO 8:3
    ('bodies', 'corpses'), # EZE 6:5
    ('body', 'corpse'), # KI1 13:22
    ('boils', 'boil[s]'), # DEU 28:27
    ('bones', 'bone[s]'), # PRO 16:24
    ('book', 'scroll'), # DAN 12:4
    ('books', 'scrolls'), # DAN 9:2
    ('border', 'territory'), # EZE 43:12
    ('borders', 'extremities'), # JOS 17:18
    ('borders', 'territories'), # EZE 27:4
    ('borders', 'territory'), # PSA 147:14
    ('bore', 'birth'), # CH1 4:9
    ('borne', 'endure'), # PSA 55:12
    ('bother', 'troubling'), # LUK 8:49
    ('bottle', 'skin-bottle'), # PSA 56:8
    ('bought', 'purchase'), # GEN 17:12
    ('bought', 'purchased'), # ACT 7:16
    ('boundaries', 'borders'), # NUM 34:2
    ('boundaries', 'bounds'), # EXO 19:23
    ('boundary', 'border'), # EZE 47:20
    ('bounty', 'goodness'), # PSA 65:11
    ('bowls', 'troughs'), # EXO 12:34
    ('boy', 'lad'), # GEN 21:12
    ('boy', 'son'), # MAT 1:25
    ('boys', 'lads'), # GEN 25:27
    ('bracelet', 'armlet'), # SA2 1:10
    ('brag', 'boast'), # EPH 2:9
    ('branch', 'shoot'), # ISA 14:19
    ('branches', 'branch[es]'), # EZE 17:8
    ('brands', 'branding'), # ISA 3:24
    ('bread', 'bread[s]'), # KI1 14:3
    ('bread', 'food'), # EZE 16:19
    ('Break', 'tear'), # JDG 6:25
    ('break', 'tear'), # GEN 27:40
    ('break', 'violate'), # PSA 89:31
    ('breast-feeding', 'nursing'), # TH1 2:7
    ('breastfeed', 'nurse'), # KI1 3:21
    ('breastplate', 'breastpiece'), # EXO 25:7
    ('breath', 'wind'), # JOB 26:13
    ('breathe', 'breath'), # DAN 10:17
    ('breathes', 'breath'), # GEN 6:17
    ('bribery', 'bribe'), # CH2 19:7
    ('brief', 'briefly'), # ACT 24:4
    ('brief', 'little'), # JAM 4:14
    ('bright', 'shining'), # REV 15:6
    ('Bring', 'fetch'), # KI2 4:41
    ('bring', 'bear'), # KI1 1:42
    ('bring', 'carry'), # MAT 6:13
    ('bring', 'carrying'), # CH2 9:21
    ('bring', 'fetch'), # GEN 48:9
    ('bring', 'take'), # LEV 14:4
    ('bring', 'taking'), # JER 33:26
    ('bringing', 'carrying'), # KI1 10:22
    ('bringing', 'took'), # MAT 16:7
    ('broke', 'breach'), # KI2 14:13
    ('broke', 'split'), # PRO 3:20
    ('broke', 'transgressed'), # HOS 6:7
    ('broken', 'brokenness'), # ISA 65:14
    ('broken', 'torn'), # ECC 4:12
    ('broken', 'transgressed'), # JDG 2:20
    ('broken-hearted', 'broken'), # PSA 147:3
    ('brokenhearted', 'broken'), # ISA 61:1
    ('bronze', 'copper'), # EZE 22:20
    ('brother', 'countrymen'), # DEU 3:20
    ('brotherhood', 'brothers'), # AMO 1:9
    ('brought', 'carried'), # CH1 18:11
    ('brought', 'led'), # ACT 18:12
    ('brought', 'taking'), # JHN 21:13
    ('brought', 'took'), # EXO 2:10
    ('build', 'established'), # PSA 107:36
    ('build', 'rebuild'), # HAG 1:8
    ('building', 'established'), # JDG 16:29
    ('building', 'rebuilding'), # NEH 6:6
    ('building', 'rebuilt'), # NEH 6:1
    ('builds', 'makes'), # PRO 17:19
    ('built', 'made'), # KI1 6:6
    ('built', 'rebuilt'), # ZEC 1:16
    ('bulls', 'cattle'), # CH2 29:22
    ('bulls', 'ox[en]'), # CH2 4:15
    ('bundles', 'sheaves'), # RUT 2:15
    ('burden', 'load'), # GEN 49:15
    ('burial', 'tomb'), # JDG 16:31
    ('burn', 'smoke'), # EXO 29:13
    ('burnt', 'fire'), # EZE 20:31
    ('burnt', 'smoke'), # LEV 8:16
    ('bursting', 'breaking'), # EXO 9:9
    ('bury', 'hide'), # JER 13:4
    ('butter', 'curd[s]'), # JOB 29:6
    ('buttocks', 'buttock[s]'), # CH1 19:4
    ('buyer', 'buys'), # EZE 7:12
    ('calamity', 'destruction'), # JOB 6:2
    ('calamity', 'trouble'), # PRO 24:16
    ('Call', 'summon'), # JER 51:27
    ('call', 'cried'), # PSA 88:1
    ('call', 'cries'), # ISA 46:7
    ('call', 'cry'), # HOS 8:2
    ('call', 'crying'), # GAL 4:6
    ('call', 'summon'), # DEU 33:19
    ('called', 'cried'), # CH2 13:14
    ('called', 'cry'), # JOB 30:28
    ('called', 'name'), # JDG 1:23
    ('called', 'named'), # GEN 21:12
    ('called', 'summoned'), # GEN 24:58
    ('calling', 'cried'), # ACT 24:21
    ('calling', 'crying'), # GEN 4:10
    ('calls', 'cry'), # PSA 34:15
    ('calls', 'summons'), # PSA 50:4
    ('calm', 'quiet'), # EXO 14:14
    ('came', 'approached'), # ACT 12:13
    ('came', 'approaching'), # DAN 9:21
    ('came', 'arrived'), # ACT 10:33
    ('came', 'descended'), # EXO 34:5
    ('came', 'near'), # SA1 17:16
    ('came', 'returned'), # KI2 9:36
    ('came', 'went'), # DEU 2:32
    ('camels', 'camel[s]'), # KI2 8:9
    ('camp', 'encamp'), # ISA 29:3
    ('camp', 'encamped'), # JDG 6:33
    ('camped', 'encamped'), # EXO 13:20
    ('camped', 'encamping'), # SA2 23:13
    ('camping', 'encamped'), # NUM 33:11
    ('camping', 'encamping'), # EXO 18:5
    ('camps', 'encamped'), # CH1 19:7
    ('camps', 'encampments'), # NUM 31:10
    ('capable', 'able'), # ACT 20:32
    ('caps', 'capitals'), # KI1 7:19
    ('captain', 'officer'), # KI2 7:2
    ('captains', 'officials'), # KI2 11:14
    ('captivate', 'captive'), # TI2 3:6
    ('captive', 'captivity'), # DAN 11:33
    ('captives', 'captive[s]'), # CH2 28:13
    ('captives', 'captivity'), # DEU 28:41
    ('capture', 'seize'), # PSA 71:11
    ('capture', 'take'), # JOB 40:24
    ('captured', 'seized'), # KI2 18:13
    ('captured', 'taken'), # SA1 4:17
    ('captured', 'took'), # CH1 18:1
    ('capturing', 'captive'), # CO2 10:5
    ('careful', 'care'), # DEU 5:1
    ('careful', 'carefully'), # EXO 23:22
    ('carefully', 'care'), # DEU 6:3
    ('careless', 'confident'), # PRO 14:16
    ('carpenters', 'craftsmen'), # CH2 34:11
    ('carried', 'took'), # KI1 17:23
    ('carry', 'bearing'), # GAL 6:17
    ('carry', 'burden'), # NUM 4:49
    ('carry', 'take'), # JHN 5:10
    ('Carrying', 'bearing'), # JHN 19:17
    ('carrying', 'bear'), # EXO 28:29
    ('carrying', 'bearing'), # ROM 15:1
    ('case', 'cause'), # PSA 9:4
    ('cast', 'throw'), # CH2 4:17
    ('castrated', 'eunuch'), # EST 2:3
    ('castrated', 'eunuchs'), # ISA 39:7
    ('casts', 'throwing'), # MAT 9:34
    ('catch', 'took'), # LUK 5:5
    ('cattle', 'cattles'), # DEU 7:13
    ('cattle', 'herd[s]'), # GEN 47:17
    ('caught', 'captured'), # ISA 13:15
    ('caught', 'taken'), # JOS 7:15
    ('Cause', 'make'), # JER 31:7
    ('cause', 'case'), # PSA 119:154
    ('cause', 'do'), # ISA 65:25
    ('cause', 'made'), # LAM 3:45
    ('caused', 'did'), # PSA 44:2
    ('caused', 'done'), # NUM 11:11
    ('caused', 'made'), # EXO 9:12
    ('causes', 'makes'), # JOB 37:13
    ('cedar', 'cedar[s]'), # ISA 41:19
    ('Celebrate', 'observe'), # KI2 23:21
    ('celebrate', 'observe'), # DEU 16:10
    ('celebrated', 'observed'), # CH2 35:19
    ('celebrates', 'observe'), # NUM 9:14
    ('celebration', 'celebrate'), # NUM 29:12
    ('celebration', 'festivities'), # LUK 14:8
    ('celebration', 'observed'), # NEH 8:18
    ('celebrations', 'festivities'), # LUK 12:36
    ('census', 'number'), # CH1 27:23
    ('centre', 'center'), # EZE 38:12
    ('centre', 'middle'), # CH2 6:13
    ('ceremony', 'service'), # EXO 12:25
    ('certain', 'certainly'), # CO1 9:22
    ('chain', 'necklace'), # DAN 5:7
    ('chains', 'fetter[s]'), # LAM 3:7
    ('chains', 'fetters'), # NAH 3:10
    ('chamber', 'room'), # KI2 23:12
    ('chambers', 'rooms'), # EZR 8:29
    ('chance', 'opportunity'), # MRK 6:31
    ('Change', 'turn'), # PRO 1:23
    ('change', 'turn'), # EZE 13:22
    ('changed', 'turned'), # LEV 13:55
    ('changing', 'turned'), # JOB 28:5
    ('charge', 'accusation'), # JHN 18:29
    ('charge', 'appoint'), # CH1 22:12
    ('charge', 'appointed'), # EST 8:2
    ('chariot', 'chariot[s]'), # KI2 7:14
    ('chariot', 'chariotry'), # CH2 8:9
    ('charioteers', 'charioteer[s]'), # SA2 10:18
    ('chariots', 'chariot[s]'), # CH1 19:7
    ('Chase', 'pursue'), # JOS 10:19
    ('chase', 'pursue'), # DEU 28:22
    ('chase', 'pursues'), # PRO 11:19
    ('chased', 'pursue'), # MAT 5:11
    ('chased', 'pursued'), # DEU 1:44
    ('chased', 'pursuing'), # ROM 9:31
    ('chases', 'pursues'), # PRO 13:21
    ('chasing', 'pursues'), # LEV 26:17
    ('cheered', 'cheerful'), # ACT 27:36
    ('cheerful', 'cheering'), # JAM 5:13
    ('cheerfully', 'cheerfulness'), # ROM 12:8
    ('cheers', 'glad'), # JDG 9:13
    ('chest', 'box'), # EXO 25:10
    ('chest', 'breasts'), # DAN 2:32
    ('chief', 'head'), # CH2 19:11
    ('child', 'offspring'), # LEV 20:4
    ('child', 'son'), # HEB 12:6
    ('child', 'youth'), # PRO 29:15
    ('child', 'youths'), # PSA 71:5
    ('childless', 'childlessness'), # ISA 47:9
    ('children', 'child[ren]'), # JER 6:11
    ('children', 'lads'), # JOB 29:5
    ('children', 'offspring'), # GEN 48:6
    ('children', 'son'), # DEU 8:5
    ('children', 'sons'), # NUM 16:27
    ('children', 'youth'), # PRO 23:13
    ('children', 'youths'), # GEN 33:1
    ('choice', 'choicest'), # EZE 20:40
    ('circumcised', 'circumcision'), # EPH 2:11
    ('circumcision', 'circumcise'), # LUK 2:21
    ('cities', 'town'), # HAB 2:8
    ('citizens', 'citizenship'), # EPH 2:12
    ('city', 'town'), # KI1 1:41
    ('clan', 'family'), # GEN 24:41
    ('clans', 'divisions'), # JDG 5:15
    ('clapped', 'struck'), # KI2 11:12
    ('clay', 'mud'), # PSA 40:2
    ('clean', 'cleanness'), # SA2 22:21
    ('clean', 'cleanse'), # EZE 39:12
    ('clean', 'cleansed'), # ACT 10:15
    ('clean', 'cleansing'), # EZE 16:4
    ('clean', 'pure'), # NUM 31:23
    ('cleaned', 'cleansed'), # JOB 9:30
    ('clear', 'clean'), # TI1 3:9
    ('clear', 'cleansed'), # LUK 7:22
    ('clear', 'clearness'), # EZE 34:18
    ('clear', 'purity'), # EXO 24:10
    ('clearly', 'clear'), # HAB 2:2
    ('clever', 'sensible'), # PRO 14:18
    ('cliff', 'steep'), # SNG 2:14
    ('cliffs', 'steep'), # EZE 38:20
    ('climb', 'ascent'), # JER 48:5
    ('climbing', 'ascent'), # KI2 9:27
    ('cling', 'cleaving'), # DEU 30:20
    ('cloak', 'shawl'), # RUT 3:15
    ('cloak', 'skirt'), # RUT 3:9
    ('close', 'nearing'), # ACT 22:6
    ('close', 'shut'), # DEU 11:17
    ('closed', 'shut'), # ACT 21:30
    ('closed', 'shuts'), # PRO 17:28
    ('closely', 'carefully'), # KI1 3:21
    ('closer', 'approached'), # LUK 7:14
    ('closer', 'approaching'), # SA2 18:25
    ('closes', 'shuts'), # JOB 12:14
    ('cloth', 'garment'), # DEU 22:17
    ('clothed', 'dress'), # LUK 24:49
    ('clothes', 'dress'), # MRK 6:9
    ('clothes', 'garment'), # EZR 9:3
    ('clothing', 'covering'), # EXO 21:10
    ('clothing', 'garments'), # JOS 22:8
    ('clouds', 'cloud[s]'), # EZE 1:28
    ('clubs', 'staff'), # EZE 39:9
    ('clung', 'cleaved'), # KI1 11:2
    ('clusters', 'bunches'), # SA1 30:12
    ('coast', 'coastland'), # ISA 23:2
    ('coast', 'coastlands'), # GEN 10:5
    ('coastal', 'coast'), # DEU 1:7
    ('coastal', 'islands'), # EZE 27:35
    ('coastlines', 'coast'), # ISA 20:6
    ('coasts', 'islands'), # EZE 27:7
    ('cold', 'coldness'), # JOB 24:7
    ('collect', 'gather'), # NUM 19:9
    ('collected', 'gathered'), # ZEC 14:14
    ('collected', 'gathers'), # NUM 19:10
    ('colourful', 'multicoloured'), # CH1 29:2
    ('Come', 'go'), # ISA 47:1
    ('Come', 'near'), # PSA 69:18
    ('come', 'approached'), # HEB 12:18
    ('come', 'go'), # EXO 19:23
    ('come', 'going'), # REV 13:11
    ('come', 'happen'), # GEN 42:4
    ('come', 'happened'), # JER 44:23
    ('come', 'near'), # EXO 19:22
    ('come', 'nearing'), # LUK 15:1
    ('come', 'return'), # GEN 8:12
    ('come', 'went'), # JER 26:2
    ('comes', 'go'), # EZE 14:4
    ('comes', 'goes'), # JOB 41:21
    ('comes', 'going'), # MRK 7:15
    ('comes', 'happen'), # ECC 2:14
    ('comfort', 'comforter'), # LAM 1:2
    ('comfort', 'comforters'), # JOB 16:2
    ('comfort', 'consoling'), # TH1 5:14
    ('coming', 'advent'), # ACT 7:52
    ('coming', 'go'), # KI1 2:2
    ('coming', 'going'), # ISA 15:3
    ('coming', 'near'), # MAT 24:32
    ('coming', 'went'), # JER 13:20
    ('command', 'commander'), # JOS 5:14
    ('commanded', 'commander'), # CH2 17:15
    ('commander', 'leader'), # CH1 27:8
    ('commander', 'official'), # JER 51:27
    ('commanders', 'leaders'), # CH1 15:25
    ('commanders', 'officials'), # CH2 23:13
    ('commands', 'commander'), # KI2 1:11
    ('commemorate', 'recount'), # JDG 11:40
    ('commotion', 'tumult'), # ISA 33:3
    ('commotion', 'uproar'), # SA1 4:14
    ('communities', 'congregation'), # NUM 1:16
    ('community', 'congregation'), # EXO 34:31
    ('companions', 'associates'), # EZR 4:9
    ('compare', 'likening'), # LUK 7:31
    ('compared', 'comparable'), # JOB 28:19
    ('compassionate', 'compassion'), # COL 3:12
    ('compels', 'impels'), # PRO 7:21
    ('complacency', 'security'), # PRO 1:32
    ('complain', 'complaint'), # JDG 21:22
    ('complete', 'completion'), # LUK 14:28
    ('completed', 'finished'), # EZR 4:13
    ('completed', 'perfected'), # EZE 27:11
    ('Completely', 'totally'), # JER 50:26
    ('completely', 'complete'), # ACT 3:16
    ('completely', 'totally'), # DEU 2:34
    ('completion', 'completed'), # LAM 4:11
    ('compulsion', 'compulsory'), # PE1 5:2
    ('conceal', 'hide'), # JER 50:2
    ('concern', 'worry'), # CO2 11:28
    ('concerned', 'caring'), # CO1 7:21
    ('condemned', 'condemnation'), # ROM 8:1
    ('conduct', 'way'), # JOB 34:11
    ('confidence', 'security'), # PRO 3:23
    ('confidence', 'trust'), # PSA 118:8
    ('confident', 'confidence'), # CO2 5:6
    ('confident', 'secure'), # JOB 11:18
    ('confidently', 'confidence'), # CO2 11:17
    ('confirmation', 'confirm'), # ROM 15:8
    ('confirming', 'confirmation'), # PHP 1:7
    ('conflict', 'war'), # DAN 10:1
    ('confused', 'bewilderment'), # DEU 28:28
    ('confused', 'confusion'), # EXO 14:3
    ('confused', 'confusions'), # ISA 19:14
    ('confusion', 'confused'), # EXO 14:24
    ('congratulate', 'bless'), # SA2 8:10
    ('congregation', 'assemblies'), # PSA 68:26
    ('congregation', 'assembly'), # NEH 13:1
    ('connecting', 'join'), # EXO 36:18
    ('connecting', 'joined'), # EXO 36:22
    ('conqueror', 'dispossesses'), # MIC 1:15
    ('conquerors', 'conquering'), # ROM 8:37
    ('conscripted', 'selected'), # NUM 31:5
    ('consecrate', 'holy'), # EXO 29:21
    ('consecrated', 'consecration'), # LEV 21:12
    ('consecrating', 'holy'), # LEV 8:11
    ('consider', 'count'), # CO2 3:5
    ('consider', 'counting'), # ROM 6:11
    ('considered', 'reckoned'), # KI1 10:21
    ('considered', 'regarded'), # PSA 44:22
    ('considered', 'thought'), # NEH 13:13
    ('consolation', 'comfort'), # EZE 16:54
    ('conspiracy', 'conspired'), # KI2 21:24
    ('conspiring', 'conspirators'), # SA2 15:31
    ('consulted', 'counsel'), # CH2 32:3
    ('consume', 'devour'), # EZE 36:14
    ('consumed', 'ate'), # CH2 7:1
    ('containers', 'kettles'), # MRK 7:4
    ('contempt', 'abhorrence'), # DAN 12:2
    ('contempt', 'scorn'), # JOB 16:10
    ('content', 'contentment'), # CO2 9:8
    ('contentious', 'contentions'), # PRO 25:24
    ('contents', 'message'), # TH2 3:14
    ('contents', 'words/messages'), # KI2 22:11
    ('continual', 'continually'), # LEV 24:2
    ('continual', 'continuity'), # EXO 29:42
    ('continually', 'continuance'), # AMO 1:11
    ('continually', 'continuity'), # EXO 30:8
    ('continue', 'continually'), # HAB 1:17
    ('continue', 'remain'), # TI1 2:15
    ('continue', 'remaining'), # ACT 11:23
    ('continue', 'repeat'), # JDG 10:13
    ('continue', 'repeated'), # JDG 8:28
    ('continue', 'repeating'), # DEU 5:25
    ('continued', 'repeated'), # SA1 3:21
    ('continuously', 'continually'), # EZE 38:8
    ('contrary', 'contrariness'), # LEV 26:21
    ('contributed', 'contribution'), # CH1 29:6
    ('control', 'mastering'), # ROM 6:14
    ('control', 'restrain'), # GEN 45:1
    ('control', 'rules'), # PRO 16:32
    ('controlling', 'restrained'), # GEN 43:31
    ('controls', 'holding'), # CO2 5:14
    ('convenient', 'conveniently'), # MRK 14:11
    ('convulsion', 'convulsed'), # MRK 1:26
    ('convulsions', 'convulsed'), # MRK 9:26
    ('copy', 'imitating'), # JN3 1:11
    ('cornerstone', 'corner'), # ACT 4:11
    ('corpses', 'corpse[s]'), # JER 7:33
    ('correct', 'right'), # JOB 27:5
    ('corrected', 'correction'), # PRO 8:33
    ('corrupt', 'corruptly'), # DEU 4:16
    ('corrupted', 'corruptly'), # DEU 9:12
    ('counsellor', 'counselor'), # ROM 11:34
    ('counsellors', 'counsel'), # PSA 119:24
    ('count', 'enrol'), # SA2 24:4
    ('count', 'number'), # JOB 9:10
    ('counted', 'enrolled'), # NUM 1:19
    ('counted', 'mustered'), # SA1 13:15
    ('counted', 'number'), # SA2 2:15
    ('counted', 'numbered'), # ECC 1:15
    ('counting', 'number'), # NUM 1:18
    ('countries', 'earth/land'), # KI1 10:24
    ('countries', 'land'), # CH2 20:10
    ('countries', 'lands'), # DAN 9:7
    ('country', 'earth/land'), # CH2 19:3
    ('country', 'land'), # GEN 24:4
    ('country', 'nations'), # LUK 12:30
    ('country', 'territory'), # PSA 105:31
    ('countryside', 'country'), # CH1 19:9
    ('countryside', 'field[s]'), # GEN 41:48
    ('countryside', 'region'), # CH1 8:8
    ('courage', 'heart'), # DAN 11:25
    ('courageous', 'bold'), # DEU 31:6
    ('courageous', 'brave'), # CH1 28:20
    ('courageous', 'courage'), # JHN 16:33
    ('Couriers', 'runners'), # EST 3:13
    ('couriers', 'runners'), # EST 3:15
    ('courses', 'highways'), # JDG 5:20
    ('court', 'courtyard'), # EZE 43:5
    ('court', 'judgement'), # JOB 9:32
    ('court', 'lawsuit'), # PRO 25:8
    ('courtyard', 'precinct'), # CH2 6:13
    ('courtyards', 'courts'), # CH1 23:28
    ('cover', 'conceal'), # GEN 37:26
    ('cover', 'cover-up'), # PE1 2:16
    ('cover', 'whitewash'), # DEU 27:2
    ('covered', 'covered-up'), # ROM 4:7
    ('covered', 'panelled'), # KI1 7:7
    ('covered', 'roofed'), # NEH 3:15
    ('covering', 'conceals'), # PRO 28:13
    ('covetous', 'coveter'), # EPH 5:5
    ('cower', 'cringed'), # PSA 18:44
    ('cows', 'cattles'), # PSA 8:7
    ('cracks', 'clefts'), # ISA 7:19
    ('craftiest', 'crafty'), # GEN 3:1
    ('craftily', 'cunningly'), # PSA 105:25
    ('craftiness', 'crafty'), # JOB 5:13
    ('craftsmanship', 'craft'), # ACT 17:29
    ('crafty', 'craftiness'), # CO2 11:3
    ('crawling', 'creeping'), # GEN 6:7
    ('crawling', 'creeps'), # LEV 20:25
    ('created', 'made'), # ACT 4:24
    ('creator', 'created'), # COL 3:10
    ('creature', 'animal'), # REV 13:1
    ('creature', 'beast'), # DAN 7:23
    ('creatures', 'beasts'), # DAN 7:12
    ('creatures', 'creature[s]'), # GEN 1:20
    ('crevice', 'cleft'), # JDG 15:11
    ('crevices', 'clefts'), # ISA 57:5
    ('crickets', 'locust[s]'), # DEU 28:42
    ('cried', 'called'), # JDG 9:54
    ('cried', 'shouted'), # JDG 7:21
    ('cried', 'wept'), # EST 8:3
    ('crippled', 'lame'), # SA2 4:4
    ('crooked', 'bent'), # ECC 7:13
    ('crooked', 'crookedness'), # PRO 6:12
    ('crooked', 'perverse'), # PRO 8:8
    ('cross', 'pass'), # DEU 3:25
    ('crossed', 'pass'), # JOS 4:1
    ('crossed', 'passed'), # CH2 21:9
    ('crossing', 'fords'), # JDG 12:6
    ('crossing', 'pass'), # DEU 31:13
    ('cruel', 'cruelty'), # PRO 27:4
    ('cruel', 'ruthless'), # PSA 71:4
    ('cruelty', 'cruel'), # PRO 12:10
    ('crumbling', 'crumbs'), # JOS 9:12
    ('crush', 'shatter'), # DAN 7:23
    ('crush', 'smash'), # NUM 24:17
    ('crush', 'smashes'), # PSA 110:5
    ('crushed', 'pulverised'), # CH2 15:16
    ('crushed', 'shattered'), # DAN 2:45
    ('crushing', 'shattering'), # DAN 7:7
    ('cry', 'call'), # EZE 8:18
    ('cry', 'weep'), # JAM 5:1
    ('cry', 'weeping'), # LUK 7:13
    ('cry', 'wept'), # JDG 14:17
    ('crying', 'calling'), # PSA 69:3
    ('crying', 'weeping'), # JHN 20:13
    ('crying', 'wept'), # GEN 50:17
    ('crystal', 'crystalizing'), # REV 21:11
    ('crystal', 'ice'), # EZE 1:22
    ('cultivate', 'labour'), # DEU 28:39
    ('cultivate', 'work'), # GEN 2:15
    ('cunning', 'guile'), # KI2 10:19
    ('cure', 'heal'), # JER 3:22
    ('cure', 'healed'), # DEU 28:27
    ('cured', 'healing'), # CH2 21:18
    ('curse', 'oath'), # SA1 14:26
    ('curses', 'oaths'), # DEU 30:7
    ('curtaining', 'curtains'), # EXO 36:8
    ('custom', 'decree'), # CH2 35:25
    ('customs', 'ways'), # CH2 7:14
    ('cypress', 'cypress[es]'), # ISA 41:19
    ('dance', 'dancings'), # SA1 29:5
    ('dance', 'leap'), # JOB 21:11
    ('dared', 'presumed'), # NUM 14:44
    ('dark', 'night'), # JHN 13:30
    ('darken', 'dark'), # AMO 8:9
    ('darkened', 'dim'), # PSA 69:23
    ('Darkness', 'dark'), # JOB 11:17
    ('darkness', 'dark'), # LAM 3:6
    ('darkness', 'gloom'), # PSA 91:6
    ('darling', 'friend'), # SNG 1:9
    ('day', 'daytime'), # NEH 9:19
    ('daylight', 'day'), # ACT 12:18
    ('daytime', 'day'), # EZE 12:7
    ('dead', 'shades'), # JOB 26:5
    ('dead', 'slain'), # CH1 10:8
    ('dealer', 'trader'), # EZE 27:16
    ('dearest', 'lover'), # SNG 1:13
    ('dearest', 'loves'), # ISA 48:14
    ('death', 'die'), # JDG 16:16
    ('death', 'died'), # KI1 21:14
    ('death', 'dying'), # PSA 48:14
    ('deathly', 'death'), # MAT 26:38
    ('decay', 'perishable'), # PE1 1:18
    ('deceit', 'deceitfulness'), # PSA 119:118
    ('deceitful', 'deceit'), # DAN 8:25
    ('deceitful', 'deceived'), # JDG 16:15
    ('deceitfully', 'deceit'), # DAN 11:23
    ('deceitfully', 'deceitfulness'), # JER 14:14
    ('deceive', 'deceit'), # PSA 50:19
    ('deceive', 'deceitful'), # MIC 1:14
    ('deceive', 'deceitfulness'), # ZEP 3:13
    ('deceived', 'betrayed'), # LAM 1:19
    ('deceived', 'deceit'), # PRO 14:8
    ('deceived', 'deluding'), # COL 2:4
    ('deceiving', 'deceitful'), # TI1 4:1
    ('deceiving', 'deceitfulnesses'), # NUM 25:18
    ('deceptive', 'deception'), # JER 7:4
    ('deceptive', 'deceptions'), # ISA 30:10
    ('decision', 'counsel'), # EZR 10:8
    ('decision', 'judgement'), # NUM 27:21
    ('decision', 'verdict'), # DEU 17:11
    ('decisions', 'judgement'), # ISA 28:26
    ('declaration', 'proclamation'), # ROM 16:25
    ('declaration', 'utterance'), # ZEC 1:4
    ('declare', 'announce'), # MIC 3:8
    ('declare', 'recount'), # JOB 12:8
    ('declare', 'told'), # CH1 17:10
    ('declared', 'preached'), # MAT 11:5
    ('declared', 'recount'), # PSA 102:21
    ('declared', 'recounted'), # JOB 28:27
    ('declared', 'utterance'), # JER 34:5
    ('declares', 'utterance'), # ZEC 3:9
    ('decrease', 'diminish'), # EXO 5:8
    ('decreed', 'determined'), # DAN 9:27
    ('dedicate', 'consecrate'), # EXO 30:30
    ('dedicated', 'dedication'), # NUM 7:10
    ('dedicated', 'holy'), # CH1 26:20
    ('deed', 'work'), # ACT 4:9
    ('deeds', 'works'), # JAM 2:20
    ('defeated', 'overcome'), # JN1 4:4
    ('defect', 'blemish'), # LEV 21:23
    ('defence', 'defended'), # LUK 21:14
    ('defence', 'defending'), # ACT 26:24
    ('defence', 'defense'), # ACT 25:16
    ('defend', 'defense'), # PHP 1:17
    ('defend', 'plead'), # PRO 31:9
    ('defender', 'defend'), # ZEC 12:8
    ('defending', 'defense'), # PHP 1:7
    ('defiant', 'rebellious'), # PRO 7:11
    ('Defile', 'unclean'), # EZE 9:7
    ('defile', 'defilement'), # CO2 7:1
    ('defile', 'profane'), # EZE 28:7
    ('defile', 'unclean'), # EZE 22:3
    ('defiled', 'profaned'), # EZE 7:24
    ('defiled', 'unclean'), # EZE 20:26
    ('defilement', 'impurity'), # CH2 29:5
    ('defilement', 'uncleanness'), # EZE 39:24
    ('defiles', 'unclean'), # NUM 5:29
    ('defiling', 'profaning'), # ISA 56:2
    ('defying', 'rebel'), # ISA 3:8
    ('degrading', 'dishonoured'), # DEU 25:3
    ('deliberate', 'purpose'), # ROM 9:11
    ('delicacies', 'delicious'), # PRO 23:3
    ('delicious', 'delicacies'), # PRO 18:8
    ('delight', 'joy'), # ISA 32:14
    ('delight', 'pleased'), # JOB 34:9
    ('delight', 'pleasure'), # EZE 33:11
    ('delights', 'pleasure'), # PRO 11:1
    ('delivered', 'birth'), # KI2 19:3
    ('demanded', 'asked'), # PSA 137:3
    ('demanding', 'asking'), # JOB 31:30
    ('demonstrate', 'show'), # ISA 5:16
    ('demonstrated', 'showed'), # NUM 20:13
    ('demonstrating', 'demonstration'), # CO1 2:4
    ('den', 'hideout'), # LUK 19:46
    ('denigrating', 'slanderous'), # ACT 6:11
    ('depart', 'go out'), # GEN 31:13
    ('depart', 'went'), # JOB 14:20
    ('departed', 'went'), # GEN 42:26
    ('departed', 'went out'), # GEN 47:10
    ('deported', 'deportation'), # MAT 1:11
    ('deposed', 'removed'), # CH2 36:3
    ('derision', 'mockery'), # EZE 23:32
    ('descend', 'come down'), # ISA 31:4
    ('descend', 'go down'), # ISA 5:14
    ('descendant', 'descent'), # REV 22:16
    ('descendant', 'son'), # LUK 20:41
    ('descendants', 'children'), # EZE 2:4
    ('descendants', 'generation'), # ACT 8:33
    ('descendants', 'generations'), # JOS 22:28
    ('descendants', 'offspring'), # CH2 20:7
    ('descendants', 'posterity'), # DAN 11:4
    ('descendants', 'son'), # GEN 11:10
    ('descendants', 'sons'), # EZR 10:20
    ('descended', 'came down'), # EPH 4:9
    ('descended', 'come'), # EPH 4:10
    ('descended', 'come down'), # EPH 4:10
    ('descended', 'descent'), # ACT 4:6
    ('descended', 'went down'), # EXO 15:5
    ('descendent', 'descent'), # PHP 3:5
    ('descending', 'going down'), # GEN 28:12
    ('descriptions', 'describe'), # JOS 18:4
    ('desecrate', 'profane'), # EZE 23:39
    ('desecrated', 'profaned'), # EZE 25:3
    ('desert', 'abandon'), # PSA 119:8
    ('deserted', 'waste'), # EZE 6:14
    ('deserting', 'abandoned'), # SA1 8:8
    ('designer', 'skillful'), # EXO 38:23
    ('desirable', 'desirablenesses'), # SNG 5:16
    ('desirable', 'desire'), # JER 3:19
    ('desirable', 'desiring'), # LUK 15:16
    ('desolate', 'desolation'), # EZE 29:9
    ('desolate', 'desolations'), # JER 51:62
    ('desolate', 'devastate'), # EZE 30:12
    ('desolate', 'waste'), # ISA 13:9
    ('desolation', 'desolate'), # EZE 36:3
    ('despise', 'reject'), # AMO 5:21
    ('despise', 'scorn'), # CO1 16:11
    ('despise', 'scorning'), # ROM 14:3
    ('despise', 'spurn'), # DEU 31:20
    ('despise', 'spurns'), # PSA 10:3
    ('despised', 'contempt'), # PRO 12:8
    ('despised', 'rejected'), # PSA 106:24
    ('despised', 'scorned'), # MRK 9:12
    ('despised', 'spurned'), # LAM 2:6
    ('destroy', 'break'), # LAM 1:15
    ('destroy', 'consume'), # ISA 31:8
    ('destroy', 'destruction'), # DAN 11:16
    ('destroy', 'devastation'), # PSA 63:9
    ('destroy', 'kill'), # SA2 20:19
    ('destroy', 'ruin'), # ISA 13:5
    ('destroy', 'wipe'), # GEN 6:7
    ('destroy', 'wiping'), # PRO 31:3
    ('destroyed', 'break'), # JER 48:38
    ('destroyed', 'broken'), # JER 48:4
    ('destroyed', 'destruction'), # EST 8:6
    ('destroyed', 'killed'), # PSA 78:47
    ('destroyed', 'ruined'), # LAM 2:5
    ('destroyer', 'destruction'), # PE2 2:3
    ('destroying', 'kill'), # HAB 1:17
    ('destroys', 'destruction'), # PRO 18:9
    ('destroys', 'ruins'), # PRO 11:9
    ('Destruction', 'devastation'), # HAB 1:3
    ('destruction', 'brokenness'), # LAM 4:10
    ('destruction', 'destroy'), # ISA 10:7
    ('destruction', 'destroyed'), # EXO 9:15
    ('destruction', 'destroying'), # CH1 21:12
    ('destruction', 'perish'), # OBA 1:12
    ('destructive', 'destroyer'), # JER 51:1
    ('destructive', 'destroying'), # MAT 6:20
    ('destructive', 'destruction'), # EZE 9:1
    ('destructive', 'destructions'), # PRO 17:4
    ('destructive', 'disaster'), # JOB 30:12
    ('detain', 'delay'), # GEN 24:56
    ('determine', 'fixed'), # JER 33:25
    ('determined', 'predetermined'), # ROM 8:29
    ('detestable', 'abomination'), # DEU 17:4
    ('detestable', 'abominations'), # CH2 28:3
    ('devastate', 'waste'), # JER 51:2
    ('devastated', 'desolate'), # EZE 12:19
    ('devastated', 'devastation'), # JOB 30:3
    ('devastation', 'desolation'), # EZE 23:33
    ('deviate', 'depart'), # PRO 5:7
    ('devious', 'crooked'), # PRO 14:2
    ('devious', 'deviousness'), # PRO 4:24
    ('devote', 'dedicate'), # MIC 4:13
    ('devour', 'ate'), # JER 48:45
    ('devour', 'consume'), # AMO 5:6
    ('devour', 'eat'), # ZEC 9:15
    ('devoured', 'consumed'), # HOS 7:9
    ('devouring', 'consumes'), # JOL 2:5
    ('devours', 'ate'), # DEU 32:22
    ('devours', 'consumes'), # ISA 5:24
    ('did', 'acted'), # ISA 38:15
    ('did', 'made'), # CH1 14:16
    ('die', 'death'), # GEN 27:7
    ('die', 'expire'), # JOB 13:19
    ('die', 'perish'), # MAT 18:14
    ('die', 'perished'), # HEB 11:31
    ('die', 'perishing'), # ACT 13:41
    ('died', 'death'), # GEN 50:16
    ('died', 'perished'), # ACT 5:37
    ('dies', 'death'), # GEN 27:10
    ('difference', 'different'), # DAN 7:7
    ('different', 'another'), # JHN 14:16
    ('different', 'differently'), # TI1 1:3
    ('difficult', 'difficultly'), # LUK 18:24
    ('difficult', 'difficulty'), # ACT 27:7
    ('difficult', 'hard'), # DEU 1:17
    ('difficult', 'heavy'), # EZE 3:5
    ('dignified', 'dignity'), # TI1 3:4
    ('dignity', 'honour'), # PRO 31:25
    ('diligent', 'diligently'), # PRO 13:24
    ('direction', 'directed'), # CH2 12:14
    ('direction', 'way'), # DEU 1:40
    ('direction', 'ways'), # PRO 7:25
    ('directions', 'guidances'), # PRO 11:14
    ('director', 'choirmaster'), # PSA 4:0
    ('disappear', 'disappearance'), # HEB 8:13
    ('disaster', 'calamity'), # AMO 9:10
    ('disaster', 'distress'), # CH2 34:28
    ('disaster', 'harm'), # JOL 2:13
    ('disaster', 'plague'), # REV 11:6
    ('disasters', 'calamities'), # DEU 32:23
    ('disasters', 'calamity'), # ISA 45:7
    ('disasters', 'harm'), # JER 36:3
    ('disbelief', 'unbelief'), # MAT 13:58
    ('discern', 'recognize'), # JOB 34:4
    ('discerning', 'distinguish'), # KI1 3:9
    ('discerning', 'distinguishing'), # CO1 11:29
    ('discerning', 'understanding'), # KI1 3:12
    ('discipline', 'chasten'), # HOS 7:12
    ('discipline', 'correction'), # JER 17:23
    ('discipline', 'disciplinedpl'), # LEV 26:23
    ('discouraged', 'disheartened'), # EZE 13:22
    ('discover', 'find'), # EZR 4:15
    ('discovered', 'finding'), # ROM 7:21
    ('discovered', 'found'), # EZR 4:19
    ('discovered', 'learned'), # ACT 28:1
    ('discovered', 'perceived'), # NEH 13:7
    ('discussion', 'discussed'), # ACT 18:19
    ('discussions', 'discussing'), # ACT 17:17
    ('disease', 'plague'), # CH1 21:22
    ('disease', 'sickness'), # CH2 21:18
    ('diseases', 'plague'), # PSA 91:3
    ('diseases', 'plagues'), # GEN 12:17
    ('diseases', 'sickness'), # EXO 15:26
    ('disgrace', 'disgraceful'), # JDG 20:6
    ('disgrace', 'insult'), # KI2 19:3
    ('disgrace', 'reproach'), # GEN 30:23
    ('disgrace', 'shame'), # PRO 13:18
    ('disgrace', 'shamefully'), # PRO 13:5
    ('disgraceful', 'shameful'), # EPH 5:12
    ('dishes', 'pans'), # CH2 24:14
    ('dishonest', 'unjust'), # EZE 22:13
    ('dishonourable', 'dishonour'), # ROM 1:26
    ('dishonoured', 'dishonourable'), # CO1 4:10
    ('dishonoured', 'shame'), # SA1 20:34
    ('dishonouring', 'disgracing'), # CO1 11:4
    ('dishonours', 'disgracing'), # CO1 11:5
    ('dismay', 'terrified'), # ISA 13:8
    ('dismayed', 'disturbed'), # PSA 6:10
    ('dismayed', 'terrified'), # JER 23:4
    ('disobeyed', 'disobedient'), # NEH 9:26
    ('dispersed', 'dispersion'), # JAM 1:1
    ('display', 'show'), # MIC 7:15
    ('display', 'shown'), # PRO 24:10
    ('displayed', 'revealed'), # REV 3:18
    ('displayed', 'showed'), # EST 1:4
    ('dispute', 'contend'), # ECC 6:10
    ('disputes', 'dispute[s]'), # DEU 1:12
    ('disrespect', 'disregarding'), # TIT 2:15
    ('distance', 'distant'), # JOB 30:10
    ('distant', 'distance'), # DEU 28:49
    ('distant', 'distances'), # ISA 33:17
    ('distinguish', 'distinction'), # EZE 22:26
    ('distinguish', 'distinctions'), # CO1 12:10
    ('distinguish', 'separate'), # GEN 1:18
    ('distort', 'falsifying'), # CO2 4:2
    ('distress', 'trouble'), # PSA 81:7
    ('distressing', 'trouble'), # JER 16:19
    ('divided', 'cut'), # PSA 136:13
    ('divided', 'split'), # ISA 63:12
    ('divination', 'divine'), # MIC 3:11
    ('divination', 'diviner'), # JOS 13:22
    ('diviners', 'divine'), # MIC 3:7
    ('division', 'group'), # NUM 2:4
    ('division', 'groups'), # NUM 1:52
    ('divisions', 'groups'), # NUM 1:3
    ('divisions', 'troop[s]'), # CH2 26:11
    ('do', 'act'), # EZE 36:36
    ('do', 'acts'), # JOB 34:12
    ('doctor', 'physician'), # JER 8:22
    ('doctors', 'physicians'), # CH2 16:12
    ('doing', 'practicing'), # JN1 3:22
    ('dominated', 'prevailed'), # CH2 27:5
    ('donation', 'contribution'), # NUM 18:24
    ('done', 'acted'), # PSA 39:9
    ('done', 'practice'), # LUK 23:51
    ('donkey', 'colt'), # MRK 11:4
    ('donkeys', 'donkey[s]'), # JOS 6:21
    ('donkeys', 'she-asses'), # CH1 27:30
    ('door', 'entrance'), # GEN 6:16
    ('doors', 'entrances'), # EZE 42:4
    ('doorway', 'door'), # MRK 2:2
    ('doorway', 'entrance'), # KI2 4:15
    ('doorway', 'threshold'), # KI1 14:17
    ('doorways', 'threshold'), # ZEP 2:14
    ('downward', 'downwards'), # EZE 8:2
    ('dozen', 'twelve'), # MAT 26:53
    ('dreadful', 'terrible'), # DAN 7:19
    ('dreamers', 'dreaming'), # JDE 1:8
    ('dreamers', 'dreams'), # JER 27:9
    ('dress', 'clothe'), # EXO 40:14
    ('dressed', 'garment'), # PRO 7:10
    ('drink', 'drinking/feast'), # DAN 1:8
    ('drinking', 'drunkards'), # PRO 23:20
    ('drinking', 'feast'), # EST 5:6
    ('Drive', 'banish'), # PSA 5:10
    ('drive', 'banish'), # JER 24:9
    ('drive', 'dispossess'), # DEU 4:38
    ('drive', 'dispossessed'), # JDG 1:32
    ('drive', 'thrust'), # ISA 28:2
    ('driven', 'banished'), # DAN 9:7
    ('driven', 'dispossessed'), # JOS 23:9
    ('driver', 'charioteer'), # KI1 22:34
    ('drivers', 'charioteer'), # EZE 39:20
    ('driving', 'dispossess'), # JDG 2:21
    ('driving', 'dispossessed'), # NUM 32:39
    ('drop', 'drip'), # JOB 36:28
    ('drop', 'fall'), # PSA 106:26
    ('drop', 'threw'), # JOB 29:17
    ('dropped', 'fallen'), # MAT 18:26
    ('dropped', 'threw'), # CH2 24:10
    ('dropped', 'throw'), # KI2 2:16
    ('drops', 'fallen'), # JHN 12:24
    ('drove', 'dispossess'), # CH2 20:7
    ('drove', 'dispossessed'), # NUM 21:32
    ('drove', 'thrust'), # CH2 21:11
    ('drunk', 'drunkard'), # JOB 12:25
    ('drunk', 'drunken'), # ISA 51:21
    ('drunk', 'drunkenness'), # ROM 13:13
    ('drunk', 'drunkfs'), # SA1 1:13
    ('drunkard', 'drunk'), # JER 23:9
    ('drunkards', 'drink'), # PSA 69:12
    ('drunkenness', 'drinking'), # ECC 10:17
    ('drunks', 'drunkards'), # NAH 1:10
    ('dumb', 'silent'), # PE2 2:16
    ('dying', 'death'), # HEB 11:5
    ('dying', 'perish'), # JOB 29:13
    ('dying', 'perishing'), # JOB 31:19
    ('eager', 'zealous'), # TIT 2:14
    ('earnestly', 'earnestness'), # ROM 12:8
    ('earrings', 'earring[s]'), # EXO 35:22
    ('earth', 'land'), # HOS 6:3
    ('earthly', 'earth'), # ACT 4:26
    ('earthly', 'earthy'), # CO1 15:49
    ('east', 'eastward'), # DEU 3:17
    ('eastern', 'eastward'), # CH1 26:14
    ('eaten', 'consumed'), # PSA 69:9
    ('effect', 'effective'), # HEB 9:17
    ('elders', 'old'), # JDG 2:7
    ('eldest', 'firstborn'), # CH1 8:30
    ('eliminate', 'extinguish'), # EZE 32:7
    ('embarrassed', 'abashed'), # JER 15:9
    ('embers', 'coals'), # PRO 26:21
    ('emerald-looking', 'emerald'), # REV 4:3
    ('Emperor', 'king'), # EST 1:17
    ('emperor', 'king'), # EST 1:13
    ('empress', 'queen'), # EST 1:18
    ('empty-handed', 'empty'), # DEU 15:13
    ('enchanters', 'conjurers'), # DAN 5:7
    ('encountered', 'found'), # LUK 7:9
    ('encourage', 'strengthen'), # PSA 64:5
    ('encouraged', 'strengthened'), # SA1 23:16
    ('end', 'cease'), # EZE 33:28
    ('end', 'complete'), # ACT 20:24
    ('end', 'completed'), # EST 1:5
    ('end', 'finished'), # DAN 5:26
    ('end', 'last'), # ACT 13:47
    ('ended', 'last'), # PE2 2:20
    ('ending', 'extremities'), # JOS 19:14
    ('ends', 'finished'), # PSA 72:20
    ('endure', 'bear'), # CO1 10:13
    ('endure', 'endurance'), # HEB 10:36
    ('endured', 'borne'), # JOB 34:31
    ('endured', 'suffered'), # MRK 5:26
    ('enemies', 'foes'), # GEN 14:20
    ('enemy', 'foe'), # AMO 3:11
    ('engaged', 'betrothing'), # MAT 24:38
    ('engraved', 'engravings'), # EXO 28:21
    ('enjoy', 'delight'), # ISA 55:2
    ('enjoy', 'delights'), # PRO 18:2
    ('enjoyed', 'delights'), # PRO 8:30
    ('enjoying', 'delights'), # PRO 8:31
    ('enjoyment', 'pleasure'), # ECC 8:15
    ('enlarge', 'increase'), # CH1 4:10
    ('enough', 'sufficiency'), # PRO 27:27
    ('enrich', 'rich'), # PSA 65:9
    ('enriched', 'rich'), # CO2 9:11
    ('ensnare', 'snares'), # JOB 34:30
    ('enter', 'came in'), # JHN 18:28
    ('enter', 'come in'), # HEB 3:19
    ('enter', 'coming in'), # HEB 3:18
    ('entered', 'came in'), # JHN 13:27
    ('entered', 'come in'), # ACT 10:25
    ('entering', 'come in'), # LUK 1:28
    ('entering', 'coming in'), # HEB 3:11
    ('enters', 'coming in'), # JHN 10:1
    ('entice', 'deceive'), # CH2 18:20
    ('enticed', 'deceived'), # JOB 31:9
    ('enticing', 'enticements'), # LAM 2:14
    ('entirely', 'entirety'), # EXO 28:31
    ('entrance', 'gate'), # EXO 32:26
    ('enveloped', 'swallowed'), # CO2 5:4
    ('envied', 'jealous'), # GEN 30:1
    ('envious', 'jealous'), # PRO 24:1
    ('envy', 'jealous'), # PRO 3:31
    ('envying', 'jealous'), # PRO 23:17
    ('equal', 'comparable'), # JOB 28:17
    ('equipment', 'article'), # LEV 13:52
    ('equipment', 'articles'), # NUM 3:36
    ('erected', 'raised'), # ISA 23:13
    ('error', 'inadvertence'), # ECC 10:5
    ('escape', 'escapees'), # EZE 6:8
    ('escape', 'fugitives'), # OBA 1:14
    ('escaped', 'escapee'), # EZE 33:21
    ('escaped', 'escapees'), # JER 51:50
    ('escaped', 'fugitive'), # GEN 14:13
    ('escaping', 'escapees'), # JER 50:28
    ('establish', 'appoint'), # JOB 38:33
    ('established', 'appointed'), # CH1 14:2
    ('established', 'assigned'), # NEH 13:30
    ('established', 'confirmed'), # CH1 16:17
    ('established', 'make'), # PSA 8:6
    ('established', 'strengthened'), # PE2 1:12
    ('establishes', 'appointed'), # JOB 34:24
    ('establishes', 'making'), # JOB 25:2
    ('esteem', 'valued'), # ISA 53:3
    ('eternal', 'perpetuity'), # ECC 12:5
    ('eternity', 'perpetuity'), # ECC 3:11
    ('evil', 'harm'), # SA1 20:7
    ('evil', 'iniquity'), # EZE 18:30
    ('evil', 'wicked'), # EZE 20:43
    ('evil', 'wickedness'), # PSA 10:7
    ('evils', 'iniquity'), # JOB 20:27
    ('examine', 'examination'), # ACT 25:26
    ('exceeding', 'surpassing'), # EPH 1:19
    ('exceeds', 'surpassing'), # EPH 3:19
    ('excellence', 'excellent'), # CO2 4:7
    ('exhausted', 'weary'), # SA1 14:31
    ('exiles', 'exile[s]'), # EZE 11:24
    ('exited', 'went out'), # EST 8:15
    ('exiting', 'going'), # EXO 19:1
    ('exiting', 'going out'), # EXO 19:1
    ('expanded', 'enlarge'), # PSA 119:32
    ('expected', 'look'), # HAG 1:9
    ('expecting', 'awaiting'), # CO1 16:11
    ('expecting', 'wait'), # PSA 71:14
    ('experience', 'know'), # NUM 14:31
    ('experience', 'see'), # ACT 13:35
    ('experienced', 'known'), # JDG 3:1
    ('experienced', 'saw'), # ACT 13:37
    ('experienced', 'seen'), # EST 9:26
    ('explain', 'declaring'), # JHN 16:14
    ('explained', 'declared'), # ACT 15:4
    ('explore', 'spy'), # NUM 13:17
    ('explored', 'spied'), # NUM 13:21
    ('explored', 'spy'), # NUM 14:7
    ('exploring', 'spying'), # NUM 13:25
    ('Extend', 'stretch'), # EXO 10:12
    ('extended', 'stretched'), # EZE 2:9
    ('extending', 'stretched'), # MAT 12:49
    ('extension', 'prolonging'), # DAN 7:12
    ('eyelashes', 'eyelids'), # PRO 6:25
    ('face', 'cheek'), # KI1 22:24
    ('facing', 'front'), # EZE 40:45
    ('fading', 'withers'), # ISA 28:1
    ('faint', 'weary'), # SA1 14:28
    ('fainting', 'enfeebled'), # LAM 2:19
    ('faith', 'faithfulness'), # HAB 2:4
    ('faithful', 'faith'), # REV 13:10
    ('faithful', 'faithfulness'), # DEU 32:4
    ('faithful', 'faithfulnesses'), # ISA 26:2
    ('faithfully', 'faith'), # ROM 1:5
    ('faithfully', 'faithful'), # TIT 1:9
    ('faithfully', 'faithfulness'), # CH2 31:12
    ('fall', 'come'), # MAT 23:35
    ('fall', 'dropped'), # JER 50:43
    ('false', 'falsehood'), # EZE 13:8
    ('falsely', 'false'), # MAT 15:19
    ('falsely', 'falsehood'), # PSA 119:78
    ('families', 'clan'), # JDG 13:2
    ('families', 'clans'), # AMO 3:2
    ('families', 'household'), # JOB 21:21
    ('families', 'households'), # EXO 1:21
    ('family', 'clan'), # LEV 25:41
    ('family', 'clans'), # EXO 12:21
    ('family', 'house'), # CH1 7:23
    ('family', 'household'), # GEN 50:22
    ('family', 'offspring'), # EZE 17:13
    ('famished', 'hungry'), # GEN 41:55
    ('fasted', 'fastings'), # CO2 11:27
    ('fat', 'fatness'), # ISA 17:4
    ('father', 'ancestor'), # CH1 29:10
    ('fathers', 'ancestors'), # DEU 30:9
    ('Fatten', 'fat'), # ISA 6:10
    ('fattened', 'fat'), # ZEC 11:16
    ('fattened', 'fatling'), # KI1 1:9
    ('fattened', 'fatlings'), # AMO 5:22
    ('fattening', 'fat'), # SA1 2:29
    ('faults', 'faultfinder'), # JOB 40:2
    ('favour', 'favourer'), # ACT 10:34
    ('favourable', 'favour'), # PSA 69:13
    ('favourably', 'favour'), # EST 2:9
    ('favourites', 'favouritism'), # EPH 6:9
    ('fear', 'afraid'), # PSA 64:9
    ('fear', 'dread'), # JOB 33:7
    ('feared', 'afraid'), # JOS 9:24
    ('feared', 'awesome'), # HAB 1:7
    ('feathers', 'plumage'), # EZE 17:7
    ('fed', 'ate'), # DEU 32:13
    ('fed', 'eat'), # DEU 8:16
    ('feeding', 'eat'), # DEU 8:3
    ('festivals', 'feasts'), # AMO 5:21
    ('fetch', 'bring'), # KI1 22:9
    ('fever', 'feverish'), # MAT 8:14
    ('fiber', 'tow'), # JDG 16:9
    ('field', 'ground'), # ISA 1:7
    ('fierce', 'burning'), # ISA 13:9
    ('fierceness', 'burning'), # PSA 69:24
    ('fiery', 'burned'), # EPH 6:16
    ('fiery', 'burning'), # PSA 7:13
    ('fight', 'battle'), # CH2 18:31
    ('fight', 'struggle'), # EXO 21:22
    ('fight', 'war'), # JDG 11:12
    ('fighters', 'war'), # JOS 10:7
    ('fighting', 'battle'), # SA2 11:15
    ('fighting', 'struggling'), # EXO 2:13
    ('fighting', 'war'), # SA1 15:18
    ('fighting', 'warring'), # ROM 7:23
    ('fills', 'surfeits'), # JOB 9:18
    ('filth', 'filthiness'), # JAM 1:21
    ('filth', 'impure'), # LAM 1:17
    ('filthiness', 'excrement'), # PRO 30:12
    ('final', 'last'), # JAM 5:3
    ('finest', 'best'), # AMO 6:6
    ('fingers', 'digits'), # CH1 20:6
    ('finish', 'cease'), # LEV 23:32
    ('finish', 'complete'), # EXO 5:13
    ('finish', 'completed'), # RUT 2:21
    ('finished', 'ceased'), # LUK 5:4
    ('finished', 'complete'), # CH1 28:20
    ('finished', 'completed'), # EZE 5:2
    ('finished', 'end'), # PSA 9:6
    ('fire', 'burning'), # ISA 4:4
    ('fire', 'burnt'), # PSA 102:3
    ('fire-trays', 'fire-pans'), # EXO 27:3
    ('firebrands', 'firewood'), # ISA 7:4
    ('firepans', 'fire-pans'), # EXO 38:3
    ('firm', 'strong'), # DAN 9:27
    ('firstfruits', 'first-fruits'), # EZE 44:30
    ('fishers', 'fishermen'), # MAT 4:19
    ('fix', 'set'), # EZE 40:4
    ('flame', 'fire'), # JAM 3:5
    ('flaming', 'burning'), # PRO 26:18
    ('flash', 'shine'), # JOB 37:15
    ('flattery', 'flattering'), # DAN 11:32
    ('flattery', 'smooth'), # PSA 5:9
    ('flaw', 'blemish'), # DEU 32:5
    ('fleet', 'ship[s]'), # KI1 9:26
    ('fleshly', 'flesh'), # GAL 4:13
    ('flock', 'sheep'), # EXO 9:3
    ('flocks', 'flock[s]'), # CH1 4:39
    ('flocks', 'sheep'), # EXO 34:3
    ('flogged', 'floggings'), # ACT 22:24
    ('flood', 'waters'), # JOB 27:20
    ('floodwaters', 'flood'), # GEN 7:7
    ('flower', 'blossom'), # CH2 4:21
    ('flowers', 'blossom'), # JOB 14:2
    ('flowers', 'blossoms'), # EXO 25:31
    ('flowing', 'streams'), # PRO 5:15
    ('Follow', 'come'), # KI2 6:19
    ('follow', 'observe'), # DEU 5:1
    ('follow', 'pursue'), # ISA 51:1
    ('follow', 'pursuing'), # PE2 2:10
    ('followed', 'come'), # JHN 11:45
    ('follower', 'apprentices/followers'), # JHN 13:35
    ('followers', 'apprentices/followers'), # ACT 6:7
    ('followers', 'following'), # MAT 8:10
    ('following', 'coming'), # ACT 13:44
    ('following', 'pursue'), # LUK 17:23
    ('foolish', 'folly'), # PRO 14:1
    ('foolish', 'fool'), # ECC 4:13
    ('foolish', 'foolishly'), # CH2 16:9
    ('foolish', 'foolishness'), # CO1 1:21
    ('foolish', 'fools'), # ECC 7:4
    ('foolishly', 'foolishness'), # CO2 11:21
    ('Foolishness', 'folly'), # ECC 10:6
    ('foolishness', 'folly'), # ECC 2:3
    ('foolishness', 'foolish'), # CO1 1:20
    ('footrest', 'footstool'), # MAT 5:35
    ('force', 'drive'), # EXO 34:11
    ('forces', 'army'), # JOB 10:17
    ('foreign', 'foreigner'), # JER 50:37
    ('foreign', 'foreignness'), # CH2 33:15
    ('foreign', 'strange'), # JER 2:25
    ('foreigner', 'alien'), # EXO 12:45
    ('foreigner', 'foreign'), # DEU 17:15
    ('foreigner', 'foreignness'), # ISA 56:3
    ('Foreigners', 'foreignness'), # PSA 18:44
    ('foreigners', 'alien'), # NUM 35:15
    ('foreigners', 'alien[s]'), # LEV 25:6
    ('foreigners', 'aliens'), # LEV 25:23
    ('foreigners', 'foreign'), # JDG 19:12
    ('foreigners', 'foreignness'), # EXO 12:43
    ('forest', 'tree[s]'), # PSA 74:5
    ('forested', 'forest'), # JOS 17:15
    ('forever', 'ever'), # DAN 2:44
    ('forgetfulness', 'forgetting'), # PSA 88:12
    ('forgets', 'forgetful'), # JAM 1:25
    ('forgive', 'atone'), # PSA 65:3
    ('forgive', 'atonement'), # CH2 29:24
    ('forgive', 'forgiveness'), # ACT 5:31
    ('forgiven', 'atoned'), # ISA 22:14
    ('forgiven', 'atonement'), # EZE 16:63
    ('forgives', 'forgiveness'), # COL 1:14
    ('formless', 'formlessness'), # GEN 1:2
    ('forsake', 'abandon'), # DAN 11:30
    ('forsook', 'abandoned'), # JDG 10:6
    ('fortified', 'fortifications'), # CH2 11:23
    ('fortified', 'fortresses'), # NUM 13:19
    ('fortified', 'strong'), # CH2 26:9
    ('fortify', 'strengthen'), # KI1 20:22
    ('fortress', 'citadel'), # NEH 2:8
    ('fortress', 'stronghold'), # DAN 11:7
    ('fortress', 'strongholds'), # ISA 33:16
    ('fortresses', 'fortifications'), # KI2 8:12
    ('fortresses', 'strongholds'), # DAN 11:19
    ('fought', 'struggled'), # SA2 14:6
    ('fought', 'war'), # NUM 31:7
    ('found', 'knew'), # ACT 17:13
    ('found', 'known'), # ACT 9:24
    ('found', 'perceived'), # NEH 13:10
    ('found', 'proved'), # PRO 30:6
    ('found', 'saw'), # CH2 22:10
    ('found', 'seen'), # ACT 14:6
    ('foundation', 'found'), # JOS 6:26
    ('foundation', 'founded'), # EZR 3:6
    ('foundation', 'founding'), # CH2 3:3
    ('foundations', 'foundation[s]'), # EZE 13:14
    ('foundations', 'founded'), # ISA 51:13
    ('founder', 'father'), # CH1 2:50
    ('fountain', 'spring'), # PRO 5:18
    ('fountains', 'springs'), # PE2 2:17
    ('fragments', 'fragment[s]'), # ISA 30:14
    ('fragrance', 'odour'), # SNG 1:3
    ('fragrant', 'perfumed'), # SNG 3:6
    ('fragrant', 'perfumes'), # EXO 25:6
    ('frames', 'frame[s]'), # EXO 26:20
    ('frames', 'rims'), # KI1 7:35
    ('free', 'release'), # HEB 2:15
    ('fresh', 'freshly'), # GEN 8:11
    ('freshly', 'fresh'), # GEN 30:37
    ('friend', 'allies'), # PSA 55:20
    ('friend', 'companion'), # JOB 16:21
    ('friendly', 'friends'), # ACT 19:31
    ('friends', 'acquaintances'), # JOB 19:14
    ('friends', 'companions'), # JOB 16:20
    ('friends', 'friend[s]'), # PRO 19:7
    ('friendship', 'intimacy'), # JOB 29:4
    ('frighten', 'afraid'), # CH2 32:18
    ('frighten', 'dismay'), # JOB 7:14
    ('frightened', 'afraid'), # LUK 2:9
    ('frightening', 'fearful'), # LUK 21:11
    ('front', 'faces/face'), # LEV 13:41
    ('frost', 'hoar-frost'), # EXO 16:14
    ('fruitful', 'fruit'), # EZE 19:10
    ('frustrated', 'distress'), # SA2 13:2
    ('fugitive', 'escapee'), # EZE 33:22
    ('fugitives', 'fugitive[s]'), # ISA 21:14
    ('fulfil', 'pay'), # PSA 61:8
    ('fulfilled', 'fulfillment'), # ACT 21:26
    ('fulfilled', 'paid'), # PSA 65:1
    ('fulfilment', 'fulfilled'), # MAT 1:22
    ('fullness', 'fills'), # DEU 33:16
    ('furious', 'anger'), # DAN 3:13
    ('furious', 'angered'), # REV 12:17
    ('furious', 'angry'), # KI2 5:11
    ('furnace', 'crucible'), # PSA 12:6
    ('furnace', 'kiln'), # EXO 19:18
    ('further', 'advanced'), # MAT 4:21
    ('further', 'beyond'), # SA1 10:3
    ('further', 'furthermore'), # CO1 3:20
    ('fury', 'rage'), # EZE 6:12
    ('futile', 'futility'), # ISA 30:7
    ('gain', 'profit'), # CO1 15:32
    ('gaining', 'acquired'), # EZE 38:12
    ('gaining', 'acquiring'), # LUK 21:19
    ('gains', 'increased'), # PRO 11:24
    ('gap', 'breach'), # JDG 21:15
    ('garbage', 'refuse'), # LAM 3:45
    ('gateway', 'gate'), # EZE 40:3
    ('gateways', 'gates'), # EZE 40:38
    ('gather', 'assembly'), # PRO 26:26
    ('gathered', 'assembled'), # CH2 32:4
    ('gathered', 'assembly'), # DEU 31:30
    ('gathered', 'met'), # JOB 2:11
    ('gathering', 'assembly'), # JER 15:17
    ('gave', 'delivered'), # DEU 32:30
    ('gave', 'granted'), # PHP 2:9
    ('gemstones', 'stone'), # CH2 9:1
    ('gemstones', 'stone[s]'), # CH2 3:6
    ('genealogical', 'genealogy'), # HEB 7:3
    ('genealogies', 'genealogical'), # CH2 31:18
    ('generals', 'leaders'), # DAN 9:6
    ('generations', 'generation[s]'), # CH1 16:15
    ('generous', 'generosity'), # ROM 12:8
    ('gentle', 'gentleness'), # CO1 4:21
    ('gentleness', 'gentle'), # PHP 4:5
    ('genuineness', 'genuine'), # CO2 8:8
    ('gerahs', 'gerah[s]'), # EZE 45:12
    ('Get', 'become'), # ISA 29:9
    ('Get', 'take'), # CH2 35:23
    ('get', 'arrived'), # ACT 27:12
    ('get', 'become'), # ECC 7:9
    ('get', 'becoming'), # EPH 5:7
    ('get', 'fetch'), # DEU 24:19
    ('get', 'obtain'), # JAM 4:2
    ('get', 'receive'), # ACT 3:5
    ('get', 'receiving'), # JHN 3:27
    ('get', 'took'), # MAT 17:5
    ('gets', 'become'), # PRO 13:11
    ('getting', 'become'), # MRK 6:35
    ('getting', 'receiving'), # JHN 5:41
    ('getting', 'take'), # JOB 18:20
    ('girl', 'woman'), # AMO 2:7
    ('girls', 'daughters'), # GEN 28:6
    ('girls', 'women'), # NUM 31:35
    ('give', 'contribute'), # EZE 48:9
    ('give', 'deliver'), # DEU 2:31
    ('give', 'grant'), # PSA 118:25
    ('give', 'handing'), # MAT 7:10
    ('give', 'pay'), # PSA 56:12
    ('give', 'restore'), # ZEP 3:9
    ('given', 'granted'), # CO1 2:12
    ('gives', 'deliver'), # DEU 7:16
    ('gladness', 'rejoicing'), # PSA 45:15
    ('glittering', 'lightning'), # NAH 3:3
    ('gloating', 'exultation'), # HAB 3:14
    ('GLORIOUS', 'glories'), # PE1 1:11
    ('glorious', 'glories'), # PE2 2:10
    ('glorious', 'glory'), # ISA 4:2
    ('glory', 'splendour'), # EZE 31:18
    ('Go', 'pass'), # EZE 9:4
    ('go', 'depart'), # NAH 3:1
    ('go', 'pass'), # ACT 18:27
    ('go', 'passes'), # EZE 36:34
    ('go', 'passing'), # EXO 26:28
    ('go', 'run'), # SA1 20:6
    ('go', 'walk'), # DEU 6:14
    ('goads', 'goad[s]'), # SA1 13:21
    ('goat', 'he-goat'), # DAN 8:21
    ('goats', 'he-goats'), # EZR 8:35
    ('goats', 'she-goats'), # SNG 4:1
    ('god-haters', 'god-hating'), # ROM 1:30
    ('goes', 'walks'), # PSA 73:9
    ('gone', 'passed'), # DEU 27:4
    ('gone', 'passing'), # PSA 144:4
    ('good', 'goodness'), # ZEC 9:17
    ('good', 'sound'), # JOB 26:3
    ('good', 'upright'), # ECC 7:29
    ('goodness', 'good'), # CH2 6:41
    ('gorge', 'satisfy'), # EZE 32:4
    ('gorged', 'satisfied'), # REV 19:21
    ('got', 'arrived'), # ACT 9:26
    ('got', 'became'), # ACT 14:5
    ('got', 'took'), # GEN 27:15
    ('governor', 'governing'), # LUK 2:2
    ('governor', 'overseer'), # KI1 4:19
    ('governor', 'ruler'), # GEN 42:6
    ('governors', 'overseers'), # KI1 4:7
    ('grab', 'snatching'), # JHN 6:15
    ('grabbed', 'seized'), # ACT 19:29
    ('grabbed', 'took'), # JDG 15:15
    ('grabbing', 'snatching'), # MAT 11:12
    ('grabbing', 'took'), # SA1 14:32
    ('graceful', 'grace'), # PRO 1:9
    ('gracious', 'favour'), # GEN 33:11
    ('grain', 'seed'), # JOB 39:12
    ('grains', 'groats'), # LEV 2:16
    ('Grant', 'give'), # PSA 119:27
    ('grant', 'giving'), # REV 2:7
    ('granted', 'given'), # GAL 3:22
    ('grape', 'grape[s]'), # LEV 19:10
    ('grape-pickers', 'gatherers'), # OBA 1:5
    ('grapes', 'grape[s]'), # DEU 32:14
    ('grapevine', 'vine[s]'), # JOL 1:7
    ('grapevines', 'vine[s]'), # PSA 78:47
    ('grasp', 'hold'), # ECC 2:3
    ('grass', 'pasture'), # SA2 7:8
    ('grass', 'vegetation'), # JOB 5:25
    ('grassy', 'grass'), # JHN 6:10
    ('grave', 'severe'), # SNG 8:6
    ('grave', 'tomb'), # ISA 14:19
    ('graves', 'tombs'), # JHN 5:28
    ('graveyard', 'graves'), # JER 26:23
    ('Gray', 'grey'), # HOS 7:9
    ('graze', 'pasture'), # SNG 1:8
    ('graze', 'pastured'), # JOB 24:2
    ('grazing', 'pasturing'), # GEN 36:24
    ('great', 'big/large/greatfs'), # EZR 9:13
    ('great', 'greatest'), # PE2 1:4
    ('great', 'greatly'), # JER 20:15
    ('great', 'greatness'), # DEU 32:3
    ('great', 'numerous'), # AMO 5:12
    ('Greater', 'great'), # JOS 19:28
    ('greater', 'great'), # CH2 9:22
    ('greatest', 'great'), # CH1 17:8
    ('greatest', 'greater'), # CO1 13:13
    ('greatly', 'abundance'), # CH1 4:38
    ('greatness', 'great'), # EZE 38:23
    ('greed', 'greediness'), # EPH 5:3
    ('greedily', 'greediness'), # EPH 4:19
    ('green', 'greenery'), # GEN 1:30
    ('greeted', 'greetings'), # MAT 23:7
    ('grew', 'raised'), # ACT 13:1
    ('grief', 'vexation'), # PSA 10:14
    ('grinding', 'grinders'), # ECC 12:3
    ('gripping', 'hold'), # MIC 4:9
    ('groans', 'groanings'), # LAM 1:22
    ('groom', 'bridegroom'), # JER 33:11
    ('grooms', 'bridegroom'), # JER 16:9
    ('ground', 'earth'), # PSA 7:5
    ('ground', 'earth/land'), # DEU 12:16
    ('ground', 'land'), # CH2 20:24
    ('ground', 'soil'), # GEN 2:7
    ('group', 'company'), # EZE 23:46
    ('groups', 'divisions'), # CH2 35:12
    ('groves', 'trees'), # DEU 6:11
    ('growing', 'sprouting'), # EXO 10:5
    ('grown', 'arisen'), # EZE 7:11
    ('grows', 'sprouting'), # HEB 12:15
    ('grows', 'sprouts'), # PSA 90:6
    ('grumbled', 'murmured'), # DEU 1:27
    ('guarantor', 'guarantee'), # HEB 7:22
    ('Guard', 'heed'), # DEU 11:16
    ('guard', 'guard/protect'), # GEN 3:24
    ('guard', 'heed'), # MAL 2:15
    ('guard', 'keep'), # KI2 11:5
    ('guard', 'preserve'), # PRO 2:11
    ('guard', 'rearguard'), # JOS 6:9
    ('guardians', 'guarding'), # KI2 10:1
    ('guardians', 'keepers'), # EST 6:2
    ('guards', 'bodyguards'), # GEN 37:36
    ('guards', 'keep'), # ECC 12:3
    ('guards', 'keepers'), # EST 2:21
    ('guests', 'invited'), # PRO 9:18
    ('Guide', 'direct'), # PSA 119:133
    ('guide', 'direct'), # LUK 1:79
    ('guilt', 'guilty'), # HOS 5:15
    ('guilt', 'iniquity'), # HOS 5:5
    ('guilty', 'guilt'), # JHN 19:4
    ('guilty', 'guilts'), # CH2 28:10
    ('guilty', 'iniquity'), # LEV 5:1
    ('guilty', 'wicked'), # PRO 24:24
    ('hacked', 'cut'), # SA1 15:33
    ('hairstyles', 'hairs'), # PE1 3:3
    ('halfway', 'middle'), # PRO 7:9
    ('hammer', 'beat'), # ISA 2:4
    ('hammered', 'beat'), # EXO 39:3
    ('Hand', 'give'), # KI2 6:29
    ('hand', 'deliver'), # AMO 1:6
    ('hand', 'give'), # CO1 5:5
    ('hand', 'palm'), # DEU 25:12
    ('hand', 'palms'), # JOB 41:8
    ('handed', 'delivered'), # AMO 1:9
    ('handed', 'gave'), # JER 39:14
    ('handing', 'giving'), # JHN 18:5
    ('handlers', 'handled'), # JER 2:8
    ('hands', 'giving'), # CO1 15:24
    ('hands', 'palm'), # EZE 6:11
    ('hands', 'palms'), # CH2 6:12
    ('handwriting', 'hand'), # CO1 16:21
    ('happened', 'occurred'), # JDG 19:30
    ('happened', 'passed'), # CH1 29:30
    ('happy', 'blessed'), # PRO 14:21
    ('happy', 'glad'), # ISA 35:1
    ('harbour', 'harbor'), # GEN 49:13
    ('hard', 'difficult'), # GEN 18:14
    ('hard', 'difficultly'), # MAT 19:23
    ('hard', 'heavy'), # NEH 5:15
    ('hardships', 'trouble'), # GEN 41:51
    ('harps', 'lyres'), # AMO 5:23
    ('harsh', 'harshly'), # JOB 39:16
    ('harshly', 'harsh'), # GEN 42:7
    ('harshly', 'harshness'), # LEV 25:43
    ('Harvest', 'reap'), # HOS 10:12
    ('harvest', 'produce'), # JOB 31:12
    ('harvest', 'reap'), # ECC 11:4
    ('harvest', 'reaping'), # GAL 6:7
    ('harvested', 'produce'), # LEV 23:39
    ('harvested', 'reaped'), # REV 14:16
    ('harvester', 'reaper'), # AMO 9:13
    ('harvesting', 'reaping'), # LUK 19:21
    ('harvests', 'reaping'), # JHN 4:37
    ('hatches', 'brood'), # JER 17:11
    ('hate', 'hatred'), # EZE 23:29
    ('hated', 'hatred'), # DEU 9:28
    ('head', 'chief'), # CH1 23:11
    ('heads', 'chiefs'), # CH2 5:2
    ('heal', 'cure'), # LUK 7:3
    ('healed', 'clean'), # KI2 5:12
    ('health', 'healthy'), # MRK 5:34
    ('healthy', 'firm'), # ZEC 11:16
    ('healthy', 'health'), # PRO 14:30
    ('Hear', 'give ear'), # PSA 78:1
    ('Hear', 'listen'), # CH2 20:20
    ('hear', 'give ear'), # PSA 77:1
    ('hear', 'listen'), # NEH 13:27
    ('hear', 'listened'), # PSA 55:17
    ('heard', 'listened'), # CH2 30:27
    ('heart-felt', 'heart'), # ISA 59:13
    ('heaven', 'heavenly'), # PHP 2:10
    ('heaves', 'lifted'), # NAH 1:5
    ('heeds', 'keeps'), # PRO 13:18
    ('heels', 'feet'), # JDG 5:15
    ('heights', 'high'), # ECC 12:5
    ('held', 'grasped'), # SNG 3:4
    ('held', 'kept'), # ACT 12:5
    ('held', 'taken'), # EZE 6:9
    ('help', 'deliverance'), # PSA 3:2
    ('help', 'helper'), # DAN 11:45
    ('help', 'service'), # NUM 7:7
    ('helped', 'assisted'), # TI1 5:10
    ('helping', 'helpers'), # CO1 12:28
    ('herds', 'cattle'), # EXO 34:3
    ('herds', 'herd[s]'), # DEU 12:6
    ('heritage', 'inheritance'), # JOB 20:29
    ('hesitated', 'delayed'), # GEN 19:16
    ('hidden', 'concealed'), # LUK 9:45
    ('hide', 'concealing'), # GEN 18:17
    ('hiding', 'secret'), # LAM 3:10
    ('high', 'height'), # CH2 4:1
    ('high', 'height[s]'), # PSA 93:4
    ('high', 'heights'), # JOB 25:2
    ('high', 'loftiness'), # PSA 62:4
    ('high', 'lofty'), # ISA 2:14
    ('highway', 'way'), # NUM 21:22
    ('hill', 'mountains'), # KI2 2:16
    ('hills', 'mountain'), # DEU 8:7
    ('hinges', 'hinge[s]'), # PRO 26:14
    ('hit', 'struck'), # EXO 2:12
    ('hitched', 'harnessed'), # SA1 6:10
    ('hits', 'strike'), # EXO 21:18
    ('hitting', 'striking'), # EXO 2:13
    ('hold', 'restrained'), # ECC 2:10
    ('hold', 'retaining'), # HEB 10:23
    ('hold', 'taken'), # EPH 6:16
    ('holding', 'delaying'), # LUK 1:21
    ('holding', 'handles'), # AMO 2:15
    ('holiness', 'holy'), # EZE 28:22
    ('hollow', 'empty'), # JER 48:30
    ('home', 'habitation'), # JER 49:33
    ('home', 'house'), # CH2 11:4
    ('home', 'tent'), # JDG 19:9
    ('home', 'tents'), # CH2 7:10
    ('homes', 'habitation'), # JOB 5:3
    ('homes', 'house'), # DEU 7:26
    ('homes', 'household'), # PRO 12:7
    ('homes', 'households'), # NUM 16:32
    ('homes', 'houses'), # HOS 11:11
    ('homes', 'tents'), # JOS 22:6
    ('honest', 'righteousness'), # GEN 30:33
    ('honeycomb', 'honey'), # SA1 14:25
    ('honour', 'beautify'), # EZR 7:27
    ('honour', 'dignity'), # JOB 30:15
    ('honour', 'greatness'), # PSA 71:21
    ('honourable', 'honour'), # ISA 5:13
    ('honourable', 'honoured'), # ISA 3:5
    ('honourable', 'noble'), # PSA 45:9
    ('honoured', 'glory/honour'), # EST 8:16
    ('honoured', 'uplifted'), # JOB 22:8
    ('hoofbeats', 'hoof-beats'), # JDG 5:28
    ('horde', 'company'), # EZE 17:17
    ('horn', 'trumpet'), # AMO 2:2
    ('horns', 'trumpets'), # JDG 7:22
    ('horseriders', 'horsemen'), # ISA 22:6
    ('horses', 'horse[s]'), # ISA 43:17
    ('horses', 'horsemen'), # GEN 50:9
    ('horses', 'steed[s]'), # EST 8:14
    ('hostages', 'pledges'), # CH2 25:24
    ('hostility', 'enmities'), # GAL 5:20
    ('hostility', 'enmity'), # EPH 2:14
    ('hot', 'live'), # ISA 6:6
    ('house', 'habitation'), # PRO 21:20
    ('house', 'home'), # MRK 14:14
    ('house', 'household'), # GEN 12:1
    ('house-servants', 'servants'), # PE1 2:18
    ('houseful', 'house'), # NUM 22:18
    ('household', 'house'), # ACT 7:10
    ('hug', 'embraced'), # MRK 9:36
    ('hugged', 'embraced'), # LUK 15:20
    ('hugging', 'embraced'), # MRK 10:16
    ('human', 'humankind'), # DAN 8:17
    ('human', 'man'), # DAN 7:13
    ('humanity', 'humankind'), # ECC 2:3
    ('humankind', 'human'), # JAM 3:7
    ('humanly', 'humans'), # LUK 18:27
    ('Humans', 'humankind'), # PSA 62:9
    ('humans', 'humankind'), # CH2 6:18
    ('humble', 'afflict'), # LEV 16:31
    ('humbled', 'afflicted'), # JOB 30:11
    ('humbled', 'low'), # ISA 2:12
    ('humbles', 'low'), # SA1 2:7
    ('humbly', 'humble'), # PRO 6:3
    ('humbly', 'modest'), # MIC 6:8
    ('humilation', 'humiliation'), # EZR 9:5
    ('humiliate', 'humble'), # SA2 13:12
    ('humiliated', 'humbled'), # SA2 13:14
    ('hunchback', 'hunchbacked'), # LEV 21:20
    ('hungry', 'hunger'), # DEU 8:3
    ('hungry', 'hungered'), # LUK 4:2
    ('hungry', 'hungering'), # CO1 4:11
    ('hunter', 'hunted'), # PRO 12:27
    ('hurled', 'threw'), # JDG 15:17
    ('hurls', 'throw'), # JOB 27:22
    ('hurried', 'haste'), # SA1 25:34
    ('hurriedly', 'hurried'), # JOS 8:14
    ('Hurry', 'haste'), # PSA 70:5
    ('hurry', 'haste'), # PSA 71:12
    ('hurrying', 'haste'), # ISA 49:17
    ('hurting', 'bruising'), # MRK 5:5
    ('husband', 'husband/man'), # EZE 16:32
    ('husbands', 'husband/man'), # RUT 1:9
    ('hypocritical', 'hypocrisy'), # TI1 4:2
    ('idol', 'image'), # DEU 4:25
    ('idol', 'teraphim'), # SA1 19:13
    ('idolatrous', 'idolater'), # EPH 5:5
    ('idolatrous', 'pagan'), # HOS 10:5
    ('idols', 'image'), # CH2 33:15
    ('idols', 'images'), # DEU 7:5
    ('idols', 'teraphim'), # ZEC 10:2
    ('ignorant', 'ignorance'), # CO1 15:34
    ('illuminate', 'light'), # NEH 9:12
    ('imagine', 'think'), # MAT 5:17
    ('imitate', 'imitators'), # CO1 4:16
    ('imitated', 'imitators'), # TH1 1:6
    ('immersed', 'immersion'), # ACT 13:24
    ('immortal', 'immortality'), # CO1 15:53
    ('impatient', 'short'), # MIC 2:7
    ('important', 'greater'), # MRK 12:31
    ('imprison', 'imprisonment'), # KI1 22:27
    ('imprisoned', 'captive'), # ROM 7:23
    ('imprisoned', 'shut'), # JER 32:2
    ('imprisons', 'shut'), # JOB 11:10
    ('impure', 'impurity'), # EPH 4:19
    ('impure', 'unclean'), # ECC 9:2
    ('impurities', 'uncleannesses'), # EZE 36:25
    ('impurity', 'uncleanness'), # ZEC 13:2
    ('incense', 'smoke'), # CH2 34:25
    ('incinerated', 'burned'), # MAT 13:40
    ('inclined', 'inclination'), # GEN 8:21
    ('increase', 'add'), # DEU 1:11
    ('increased', 'added'), # EZE 23:14
    ('increased', 'numerous'), # HOS 10:1
    ('increasingly', 'increase'), # DAN 11:39
    ('indignant', 'indignation'), # LAM 2:6
    ('indulge', 'gratify'), # ECC 2:3
    ('infant', 'sucking'), # LAM 2:11
    ('infants', 'sucking'), # PSA 8:2
    ('inform', 'known'), # EZR 5:10
    ('informing', 'known'), # CO1 12:3
    ('inhabit', 'dwell'), # AMO 9:14
    ('inhabit', 'dwell in'), # AMO 9:14
    ('inhabit', 'inhabitant'), # EZE 7:7
    ('inhabitants', 'dwell'), # JOB 26:5
    ('inhabitants', 'inhabitant[s]'), # EXO 34:12
    ('inhabited', 'dwelling'), # EZE 36:17
    ('inhabited', 'inhabitants'), # JER 17:25
    ('inhabiting', 'dwelling'), # JDG 11:21
    ('inhabiting', 'inhabitants'), # GEN 36:20
    ('inherit', 'inheritance'), # DEU 3:28
    ('inherit', 'possess'), # EXO 32:13
    ('inherit', 'possession'), # NUM 14:24
    ('inheritance', 'inherit'), # DEU 21:16
    ('inheritance', 'inheriting'), # GAL 4:30
    ('inheritance', 'portion'), # ECC 2:21
    ('inheritance', 'possess'), # CH2 20:11
    ('inherited', 'inheritance'), # JOL 2:17
    ('inherited', 'possession'), # LEV 25:13
    ('injury', 'harm'), # EXO 21:22
    ('injustice', 'wickedness'), # HAB 1:3
    ('innards', 'entrails'), # EXO 29:13
    ('inner', 'innermost'), # CH2 4:20
    ('inner', 'within'), # CH2 29:16
    ('innermost', 'inner'), # EZE 36:26
    ('innocent', 'acquit'), # JOB 9:28
    ('innocent', 'acquitted'), # PSA 19:13
    ('innocent', 'innocence'), # SA2 15:11
    ('inquire', 'consult'), # KI2 1:3
    ('inquire', 'enquire'), # SA1 22:15
    ('inquired', 'enquired'), # SA2 5:19
    ('inquiring', 'enquires'), # SA2 16:23
    ('insanely', 'insane'), # CO2 11:23
    ('inscribed', 'engraved'), # CO2 3:7
    ('inside', 'inner'), # DEU 32:25
    ('inside', 'midst'), # DAN 7:15
    ('inside', 'within'), # CH2 3:4
    ('insides', 'inner'), # ISA 16:11
    ('insightful', 'insight'), # PRO 12:8
    ('insignificant', 'lowly'), # EZE 29:14
    ('inspect', 'visit'), # JOB 5:24
    ('instant', 'moment'), # ISA 51:4
    ('instead', 'rather'), # ROM 14:13
    ('instruct', 'teach'), # PRO 22:19
    ('instruct', 'teaching'), # CO1 2:16
    ('instructed', 'learning'), # CO1 14:31
    ('instructing', 'teach'), # SA1 12:23
    ('instruction', 'command'), # PE2 3:2
    ('instruction', 'correction'), # JOB 36:10
    ('instruction', 'discipline'), # PRO 1:2
    ('instruction', 'law'), # PSA 119:55
    ('instructions', 'command'), # GEN 49:33
    ('instructions', 'commands'), # MRK 10:19
    ('instructions', 'law'), # HOS 8:12
    ('instructions', 'laws'), # PSA 105:45
    ('instruments', 'instrument/flute'), # GEN 4:21
    ('insults', 'insult[s]'), # EZE 36:6
    ('integrity', 'blamelessness'), # PSA 84:11
    ('intend', 'think'), # DAN 7:25
    ('intercede', 'entreat'), # GEN 23:8
    ('interest', 'usury'), # NEH 5:10
    ('interior', 'middle'), # SNG 3:10
    ('intervene', 'interposed'), # ISA 59:16
    ('intervened', 'mediated'), # PSA 106:30
    ('intoxicated', 'drunk'), # REV 17:2
    ('invaded', 'attacks'), # HAB 3:16
    ('invalidate', 'annul'), # JOB 40:8
    ('invalidated', 'voided'), # CO2 9:3
    ('investigated', 'sought'), # EST 2:23
    ('investigation', 'investigated'), # JDG 6:29
    ('invite', 'calling'), # LUK 14:13
    ('invited', 'called'), # ROM 1:6
    ('jacinth', 'hyacinth'), # REV 21:20
    ('jealous', 'envious'), # PSA 106:16
    ('jealous', 'jealousy'), # ACT 13:45
    ('jealous', 'zealous'), # NUM 11:29
    ('jealously', 'jealousy'), # ROM 13:13
    ('jewels', 'corals'), # PRO 8:11
    ('job', 'business'), # ECC 1:13
    ('joined', 'united'), # ECC 9:4
    ('jostling', 'thrust'), # JOL 2:8
    ('journeys', 'journeyings'), # NUM 33:1
    ('joy', 'pleasure'), # ECC 2:2
    ('judge', 'judgement'), # DEU 17:8
    ('judge', 'justice'), # ISA 40:14
    ('judged', 'judgement'), # DAN 7:22
    ('judgement', 'judge'), # EXO 18:16
    ('judgement', 'judged'), # CO1 5:3
    ('judgement', 'judges'), # JOB 31:11
    ('judgements', 'judge'), # CH2 1:10
    ('judges', 'judgement'), # CH2 19:8
    ('judges', 'judgements'), # CH1 16:14
    ('judging', 'judgement'), # LEV 19:35
    ('jump', 'leapt'), # ACT 19:16
    ('jumps', 'leaps'), # JOB 37:1
    ('justice', 'judge'), # PRO 31:9
    ('justice', 'judgement'), # ISA 5:16
    ('justice', 'judgements'), # PSA 119:149
    ('justice', 'justify'), # ISA 5:23
    ('justice', 'right'), # JOB 27:2
    ('justice', 'uprightness'), # PSA 45:6
    ('Keep', 'preserve'), # PSA 119:107
    ('keep', 'holding'), # JHN 10:24
    ('keep', 'observe'), # PSA 119:33
    ('keep', 'observing'), # KI1 11:38
    ('keep', 'preserve'), # GEN 6:20
    ('keeper', 'kept'), # NEH 2:8
    ('keepers', 'keep'), # SNG 8:11
    ('keeps', 'preserved'), # PSA 119:50
    ('keeps', 'restrains'), # PRO 10:19
    ('kept', 'observe'), # PSA 119:22
    ('kept', 'observed'), # KI1 11:11
    ('kept', 'preserved'), # GEN 47:25
    ('kept', 'preserving'), # MRK 6:20
    ('kept', 'restrained'), # GEN 20:6
    ('kids', 'children'), # MRK 10:14
    ('kill', 'death'), # EXO 17:3
    ('kill', 'put to death'), # CH2 23:7
    ('kill', 'slays'), # JOB 20:16
    ('kill', 'stone'), # EXO 17:4
    ('kill', 'strike'), # EZE 9:5
    ('kill', 'struck'), # JER 33:5
    ('killed', 'death'), # CH2 25:27
    ('killed', 'defeated'), # JDG 1:10
    ('killed', 'put to death'), # CO2 6:9
    ('killed', 'putting to death'), # EZE 13:19
    ('killed', 'slew'), # GEN 49:6
    ('killed', 'stoned'), # HEB 12:20
    ('killed', 'struck'), # CH1 10:2
    ('killing', 'defeated'), # SA1 7:11
    ('killing', 'put to death'), # GEN 18:25
    ('killing', 'struck'), # SA1 17:57
    ('kills', 'killer'), # JOS 21:13
    ('kills', 'strike'), # SA1 17:26
    ('kills', 'strikes'), # LEV 24:18
    ('kills', 'struck'), # NUM 35:15
    ('kindness', 'loyalty'), # GEN 20:13
    ('King', 'kingdom'), # DEU 3:4
    ('king', 'kingdom'), # MAT 16:28
    ('kings', 'kingdoms'), # CH2 12:8
    ('knew', 'foreknew'), # ROM 8:29
    ('know', 'acknowledge'), # JOB 7:10
    ('knowledgable', 'knowledge'), # PRO 14:7
    ('knowledgeable', 'knowledge'), # KI1 7:14
    ('known', 'foreknown'), # PE1 1:20
    ('known', 'recognized'), # JER 28:9
    ('labour', 'birth'), # GEN 35:17
    ('labourers', 'labour'), # CH2 8:8
    ('lady', 'woman'), # MAT 15:28
    ('laid', 'put'), # EZE 11:7
    ('lamb', 'ram'), # LEV 17:3
    ('lambs', 'rams'), # GEN 30:32
    ('lampstand', 'candlestick'), # DAN 5:5
    ('land', 'earth'), # CH1 4:40
    ('land', 'ground'), # GEN 7:22
    ('land', 'nations'), # DEU 18:14
    ('land', 'soil'), # DEU 28:21
    ('larger', 'large'), # DEU 25:14
    ('last', 'finished'), # JOS 5:6
    ('lattice', 'window-lattice'), # JDG 5:28
    ('latticework', 'network'), # JER 52:23
    ('latticework', 'networks'), # CH2 4:12
    ('laughed', 'laughing-stock'), # JER 20:7
    ('laughing', 'laughter'), # JAM 4:9
    ('laughingstock', 'contempt'), # GEN 38:23
    ('laughingstock', 'laughter'), # EZE 23:32
    ('lawless', 'lawlessness'), # TH2 2:3
    ('lawlessness', 'lawless'), # PE2 2:8
    ('lawsuit', 'case'), # LAM 3:36
    ('lawsuits', 'case'), # EXO 23:6
    ('leader', 'chief'), # CH1 5:7
    ('leader', 'judge'), # JDG 2:19
    ('leader', 'overseer'), # NEH 12:42
    ('leader', 'prince'), # GEN 23:6
    ('leaders', 'chiefs'), # CH2 28:12
    ('leaders', 'judges'), # CH1 17:6
    ('leaders', 'officials'), # CH1 29:24
    ('leaders', 'princes'), # HOS 7:3
    ('leading', 'head'), # CH2 20:27
    ('learn', 'know'), # EZR 4:15
    ('learn', 'known'), # PHP 2:19
    ('learn', 'take/accept/receive'), # PRO 1:3
    ('learned', 'known'), # PSA 119:152
    ('least', 'insignificant'), # JNA 3:5
    ('least', 'little'), # NUM 11:32
    ('Leave', 'depart'), # JOB 21:14
    ('Leave', 'go'), # CH2 26:18
    ('leave', 'depart'), # JDG 16:17
    ('leave', 'departed'), # EXO 33:11
    ('leave', 'go'), # EZE 46:8
    ('leave', 'going'), # JHN 6:67
    ('leaves', 'depart'), # LUK 12:36
    ('leaves', 'departs'), # ISA 46:7
    ('leaves', 'leafage'), # ISA 1:30
    ('leaving', 'abandoning'), # JOS 24:16
    ('leaving', 'go'), # EXO 13:4
    ('leaving', 'going'), # MRK 13:1
    ('leaving', 'gone'), # KI2 20:4
    ('led', 'guided'), # DEU 32:12
    ('led', 'taken'), # PRO 24:11
    ('led', 'took'), # CH1 8:7
    ('leeks', 'leek[s]'), # NUM 11:5
    ('left', 'abandoned'), # ISA 18:6
    ('left', 'departed'), # ACT 18:1
    ('left', 'going'), # ACT 5:41
    ('left', 'gone'), # JOS 2:7
    ('left', 'remain'), # LEV 26:39
    ('left', 'remains'), # ISA 7:22
    ('left', 'went'), # ACT 10:7
    ('lengthen', 'length'), # DEU 30:20
    ('lengthen', 'long'), # KI1 3:14
    ('leprosy', 'disease'), # CH2 26:19
    ('leprosy', 'leprous'), # LUK 17:12
    ('leprous', 'leprosy'), # LUK 5:12
    ('let', 'allow'), # GEN 31:28
    ('let', 'allowed'), # ACT 16:7
    ('let', 'allowing'), # ACT 19:30
    ('let', 'permit'), # EXO 3:19
    ('let', 'permits'), # JOB 9:18
    ('liberate', 'liberty'), # ISA 61:1
    ('liberates', 'free'), # PSA 146:7
    ('life', 'alive'), # PSA 119:93
    ('life', 'lifes'), # DAN 7:12
    ('life', 'live'), # EZE 37:9
    ('life', 'lived'), # EZE 37:10
    ('life', 'living'), # CO1 6:3
    ('life', 'spirits'), # NUM 16:22
    ('lifetime', 'days'), # KI1 11:12
    ('lifetimes', 'days'), # EZE 12:25
    ('lifetimes', 'lives'), # ECC 9:3
    ('lift', 'raise'), # EZE 26:8
    ('lift', 'raising'), # MAT 12:11
    ('lifted', 'raised'), # EPH 2:6
    ('light', 'brightness'), # ISA 50:10
    ('light', 'shone'), # JOB 10:22
    ('lighter', 'lighten'), # JNA 1:5
    ('lightly', 'lightness'), # JER 3:9
    ('like', 'corresponding'), # EXO 38:18
    ('like', 'similar'), # JHN 8:55
    ('like', 'wishing'), # JHN 18:39
    ('limit', 'restrain'), # JOB 15:8
    ('linger', 'delay'), # PRO 23:30
    ('lips', 'mouth'), # EZE 33:31
    ('list', 'number'), # CH1 25:1
    ('listed', 'enrolled'), # CH1 5:17
    ('Listen', 'give ear'), # ACT 2:14
    ('Listen', 'hear'), # DEU 9:1
    ('listen', 'attentive'), # NEH 1:11
    ('listen', 'heard'), # JHN 10:8
    ('listen', 'hearing'), # ACT 4:19
    ('listen', 'heed'), # MAL 2:16
    ('listened', 'heard'), # ACT 24:24
    ('listened', 'hearing'), # ACT 15:12
    ('listener', 'listens'), # PRO 21:28
    ('listening', 'hear'), # KI1 3:11
    ('listening', 'hearing'), # ACT 10:44
    ('listening', 'heed'), # TI1 4:1
    ('listening', 'listeners'), # JAM 1:22
    ('listens', 'hearing'), # LUK 6:47
    ('listens', 'hears'), # PRO 15:31
    ('listens', 'heeds'), # PRO 15:32
    ('little', 'small'), # DAN 7:8
    ('little', 'smallsg'), # AMO 6:11
    ('little', 'young'), # JOB 21:11
    ('live', 'alive'), # ACT 7:19
    ('live', 'dwell'), # AMO 3:12
    ('live', 'dwelling'), # DEU 2:8
    ('live', 'dwells'), # ISA 20:6
    ('live', 'dwelt'), # DEU 33:28
    ('live', 'inhabitants'), # ISA 21:14
    ('live', 'life'), # ACT 11:18
    ('live', 'sojourn'), # ISA 11:6
    ('live', 'sojourns'), # EXO 12:49
    ('lived', 'dwell'), # ISA 45:18
    ('lived', 'dwelling'), # CH2 16:2
    ('lived', 'dwelt'), # JDG 11:26
    ('lived', 'inhabitants'), # CH1 4:40
    ('lived', 'life'), # EXO 6:20
    ('lived', 'sojourned'), # DEU 26:5
    ('lives', 'alive'), # EZE 13:22
    ('lives', 'dwell'), # JER 51:43
    ('lives', 'dwelling'), # ISA 33:5
    ('lives', 'dwells'), # HOS 4:3
    ('lives', 'sojourns'), # NUM 15:16
    ('livestock', 'cattle'), # DEU 11:15
    ('living', 'alive'), # DEU 5:3
    ('living', 'dwell'), # DEU 8:12
    ('living', 'dwells'), # ISA 10:24
    ('living', 'dwelt'), # SA1 12:11
    ('living', 'existence'), # GEN 7:4
    ('living', 'inhabitant'), # ZEP 3:6
    ('living', 'inhabitants'), # JER 35:17
    ('living', 'life'), # JOB 6:11
    ('living', 'sojourn'), # EXO 12:48
    ('living', 'sojourning'), # LEV 25:6
    ('living', 'sojourns'), # JOS 20:9
    ('load', 'burden'), # ISA 46:2
    ('loads', 'burdens'), # JOB 37:11
    ('loathe', 'abhor'), # PSA 119:163
    ('locked', 'secured'), # ACT 16:24
    ('locust', 'locust[s]'), # AMO 7:1
    ('locusts', 'locust[s]'), # DEU 28:38
    ('long', 'distant'), # KI2 19:25
    ('long', 'duration'), # PSA 146:2
    ('long', 'length'), # CH2 3:4
    ('long', 'prolong'), # DEU 4:26
    ('long', 'prolongs'), # ECC 7:15
    ('longed', 'longer'), # REV 18:14
    ('longings', 'desire'), # PSA 38:9
    ('Look', 'see'), # GEN 39:14
    ('look', 'considered'), # JOB 30:20
    ('look', 'search'), # MAT 10:11
    ('look', 'searching'), # JHN 5:39
    ('look', 'see'), # EZE 44:5
    ('look', 'seek'), # ACT 11:25
    ('look', 'seeking'), # ISA 41:17
    ('look', 'watch'), # PSA 68:16
    ('look', 'watching'), # MAT 26:38
    ('looked', 'appeared'), # DAN 1:15
    ('looked', 'saw'), # KI2 2:24
    ('looked', 'seeing'), # MAT 14:30
    ('looked', 'seeking'), # LUK 2:44
    ('looked', 'seen'), # HAB 3:6
    ('looking', 'seek'), # PSA 10:13
    ('lookouts', 'watchmen'), # SA1 14:16
    ('looks', 'see'), # EZE 33:3
    ('looks', 'sees'), # JOB 41:34
    ('loot', 'plunder'), # PSA 68:12
    ('looted', 'plundered'), # JER 50:37
    ('loud', 'sound'), # PSA 102:5
    ('love', 'loyalty'), # EXO 15:13
    ('lovers', 'paramours'), # EZE 23:20
    ('loves', 'beloved'), # ROM 1:7
    ('lower', 'downwards'), # EXO 39:20
    ('lower', 'low'), # PRO 25:7
    ('lowest', 'lower'), # KI1 6:6
    ('lowliest', 'insignificant'), # SA1 9:21
    ('lowly', 'small'), # GEN 19:11
    ('loyal', 'loyalty'), # KI1 8:23
    ('lying', 'deceiving'), # HOS 4:2
    ('lyres', 'harps'), # CH1 15:21
    ('made', 'caused'), # AMO 4:10
    ('made', 'established'), # LUK 1:68
    ('made', 'work'), # JOB 37:7
    ('made', 'working'), # EXO 24:10
    ('made', 'works'), # PSA 104:31
    ('madman', 'mad'), # KI2 9:11
    ('maggots', 'maggot[s]'), # JOB 7:5
    ('magic', 'magical'), # ACT 19:19
    ('majestic', 'majesty'), # ISA 30:30
    ('make', 'cause'), # EZE 26:20
    ('make', 'causes'), # ECC 10:1
    ('make', 'doing'), # JER 7:18
    ('make', 'establish'), # GEN 6:18
    ('make', 'prepare'), # ISA 40:20
    ('maker', 'made'), # ISA 17:7
    ('makes', 'caused'), # LAM 3:6
    ('makes', 'causing'), # PSA 104:14
    ('making', 'establish'), # GEN 9:9
    ('man', 'humankind'), # GEN 2:15
    ('man', 'person'), # PRO 28:2
    ('manager', 'management'), # LUK 16:2
    ('march', 'go'), # DEU 28:25
    ('marched', 'going'), # EXO 14:8
    ('marches', 'go'), # JOL 2:8
    ('marches', 'goes'), # HAB 1:6
    ('market', 'marketplace'), # MRK 7:4
    ('marketplace', 'square'), # PSA 55:11
    ('marketplaces', 'market'), # EZE 27:24
    ('marriage', 'marriable'), # CO1 7:36
    ('marsh', 'swamp'), # JOB 40:21
    ('marvellous', 'wonderful'), # PSA 119:18
    ('marvellous', 'wonders'), # JOB 9:10
    ('masons', 'wall-builders'), # KI2 22:6
    ('master', 'mastership'), # PE2 2:10
    ('masters', 'head'), # LAM 1:5
    ('masters', 'owners'), # SA2 1:6
    ('matters', 'message/thing/matter'), # EZR 10:14
    ('mauled', 'tore'), # KI2 2:24
    ('meadow', 'pastureland'), # HOS 9:13
    ('mean', 'hateful'), # TIT 3:3
    ('measured', 'measurement'), # EZE 40:21
    ('measured', 'measurements'), # EZE 40:29
    ('measuring', 'measurement'), # EZE 40:3
    ('mediate', 'mediator'), # JOB 33:23
    ('medicines', 'medications'), # JER 30:13
    ('meditate', 'meditation'), # PSA 119:99
    ('meditating', 'meditation'), # PSA 119:97
    ('medium', 'necromancer'), # LEV 20:27
    ('medium', 'necromancy'), # CH1 10:13
    ('mediums', 'necromancer'), # KI2 21:6
    ('mediums', 'necromancers'), # ISA 8:19
    ('meet', 'filling'), # PHP 4:19
    ('meet', 'saw'), # GAL 1:19
    ('meet', 'see'), # JHN 12:21
    ('meeting', 'gathered'), # JHN 11:47
    ('melons', 'watermelons'), # NUM 11:5
    ('memorial', 'remembrance'), # PSA 38:0
    ('memory', 'memorial'), # ECC 9:5
    ('memory', 'remembrance'), # DEU 32:26
    ('men', 'humankind'), # PRO 23:28
    ('men', 'people'), # CH2 9:7
    ('men', 'person'), # DAN 5:7
    ('menstruating', 'menstruation'), # EZE 18:6
    ('menstruating', 'menstruous'), # LEV 15:24
    ('mentioned', 'remembrance'), # SA1 4:18
    ('merchandise', 'trading'), # PRO 31:18
    ('merchants', 'merchant[s]'), # EZE 16:29
    ('merchants', 'trader'), # GEN 23:16
    ('merchants', 'traders'), # NAH 3:16
    ('mercy', 'compassion'), # HOS 1:6
    ('mercy', 'compassions'), # PSA 69:16
    ('mercy', 'spare'), # HAB 1:17
    ('message', 'report'), # ISA 53:1
    ('message', 'speech'), # SA2 23:2
    ('message', 'words/messages'), # AMO 1:1
    ('messages', 'speech'), # ACT 20:2
    ('messages', 'words/messages'), # EZE 2:7
    ('messengers', 'messenger-like'), # LUK 20:36
    ('met', 'encountering'), # ACT 20:14
    ('met', 'fulfilled'), # ACT 2:1
    ('met', 'gathered'), # ACT 4:27
    ('met', 'received'), # JHN 18:3
    ('metal', 'molten'), # DAN 11:8
    ('metalworker', 'metalsmith'), # JER 10:14
    ('midday', 'noons'), # GEN 43:25
    ('midday', 'noontides'), # KI1 18:26
    ('middle', 'heart'), # EZE 27:26
    ('middle', 'midst'), # ISA 5:8
    ('mighty', 'powerful/mightypl'), # GEN 6:4
    ('mighty', 'strong'), # ISA 40:26
    ('mind', 'head'), # DAN 2:28
    ('minds', 'heart'), # CH1 22:19
    ('minds', 'hearts'), # ROM 2:15
    ('mingled', 'mixed'), # PSA 106:35
    ('minister', 'ministry'), # PHP 2:30
    ('minister', 'serve'), # CH1 15:2
    ('ministered', 'serves'), # NUM 4:37
    ('ministering', 'serve'), # CH2 5:14
    ('miscarriages', 'miscarrying'), # EXO 23:26
    ('miserable', 'sufferer'), # JOB 3:20
    ('misery', 'calamity'), # GEN 44:34
    ('misery', 'trouble'), # PRO 31:7
    ('misfortune', 'disaster'), # JOB 12:5
    ('missing', 'lacked'), # CO1 1:7
    ('mistreat', 'afflict'), # EXO 22:22
    ('mistreated', 'harm'), # NUM 20:15
    ('mistreated', 'maltreat'), # ISA 49:26
    ('mistreating', 'afflicted'), # GEN 16:6
    ('Mockers', 'mockery'), # PRO 29:8
    ('mockers', 'mockeries'), # JER 51:18
    ('mockers', 'mockerpl'), # ISA 28:22
    ('modest', 'modesty'), # TI1 2:9
    ('money', 'silver'), # EST 3:11
    ('moneychangers', 'money-changers'), # JHN 2:14
    ('mount', 'mountain'), # CH2 33:15
    ('mountains', 'mountainous'), # ISA 45:2
    ('mountainsides', 'mountains'), # EZE 34:13
    ('mountaintops', 'mountains'), # ISA 42:11
    ('mounted', 'rode'), # GEN 24:61
    ('mounted', 'settings'), # EXO 35:27
    ('mourn', 'mourners'), # ISA 61:2
    ('mourned', 'wept'), # NUM 20:29
    ('mourner', 'mourning'), # EST 6:12
    ('mourning', 'lamentation'), # EZE 28:12
    ('mourning', 'mourners'), # JOB 5:11
    ('mourning', 'weep'), # ZEC 7:3
    ('mourning', 'weeping'), # GEN 50:4
    ('mouth', 'lips'), # KI2 19:28
    ('mouth', 'palate'), # EZE 3:26
    ('mouthful', 'mouth'), # PRO 20:17
    ('mouthpiece', 'mouth'), # ACT 15:7
    ('mouths', 'palate'), # JOB 29:10
    ('mouths', 'throat'), # PSA 149:6
    ('move', 'displace'), # PRO 22:28
    ('move', 'go'), # NUM 36:7
    ('moved', 'going'), # LUK 19:36
    ('moved', 'running'), # EZE 1:14
    ('moved', 'went'), # EZE 10:18
    ('mud', 'mire'), # PSA 69:2
    ('muddy', 'fouling'), # EZE 34:18
    ('multiple', 'multiplied'), # HOS 8:11
    ('multiplied', 'increase'), # JOB 29:18
    ('multiplied', 'increased'), # JOS 24:3
    ('multiply', 'increase'), # DEU 7:13
    ('murderer', 'killer'), # NUM 35:19
    ('murderer', 'murdered'), # KI2 9:31
    ('murdering', 'kill'), # DEU 22:26
    ('murderous', 'murder'), # ACT 9:1
    ('murmured', 'grumbled'), # EXO 17:3
    ('murmurings', 'grumblings'), # EXO 16:9
    ('musical', 'music'), # DAN 3:7
    ('muttering', 'grumbling'), # JHN 7:32
    ('mysteries', 'secrets'), # DAN 2:28
    ('mysterious', 'mystery'), # CO1 2:7
    ('mystery', 'secret'), # DAN 2:30
    ('naked', 'nakedness'), # EZE 16:7
    ('nakedness', 'naked'), # GEN 3:7
    ('name', 'called'), # ACT 13:9
    ('name', 'describing'), # ACT 8:33
    ('named', 'called'), # CH1 13:11
    ('narrow', 'closed'), # EZE 41:16
    ('narrowed', 'closed'), # KI1 6:4
    ('nation', 'earth/land'), # EZE 45:4
    ('nation', 'land'), # EZE 25:6
    ('nationality', 'nation'), # ACT 17:26
    ('nations', 'lands'), # CH2 12:8
    ('native', 'native-born'), # EXO 12:19
    ('natives', 'native-born'), # EXO 12:49
    ('natural', 'nature'), # ROM 11:21
    ('naturally', 'nature'), # ROM 2:14
    ('near', 'close'), # EXO 39:20
    ('nearest', 'near'), # NUM 27:11
    ('necessary', 'necessity'), # HEB 7:27
    ('necklaces', 'ornament'), # NUM 31:50
    ('negligent', 'negligence'), # EZR 4:22
    ('neighbour', 'friend'), # PRO 12:26
    ('neutralise', 'nullifying'), # TH2 2:8
    ('new', 'newness'), # ROM 6:4
    ('News', 'message'), # ACT 11:22
    ('news', 'information'), # EZE 24:26
    ('news', 'message'), # JOS 22:33
    ('news', 'new[s]'), # PSA 112:7
    ('night', 'night[s]'), # GEN 7:12
    ('night-time', 'night'), # KI2 7:12
    ('nights', 'night[s]'), # DEU 9:9
    ('nighttime', 'night'), # CH2 21:9
    ('noblemen', 'nobles'), # DAN 5:10
    ('nobles', 'honoured'), # NAH 3:10
    ('noise', 'sound'), # EZE 26:10
    ('noon', 'noontides'), # KI1 18:27
    ('north', 'northward'), # CH1 9:24
    ('north-facing', 'north'), # EZE 42:2
    ('north-facing', 'northward'), # EZE 46:19
    ('northerly', 'north'), # PRO 25:23
    ('northern', 'north'), # DAN 11:6
    ('northern', 'northerner[s]'), # JOL 2:20
    ('northern', 'northward'), # CH1 26:14
    ('northward', 'north'), # JOS 18:17
    ('nostrils', 'nose'), # JOB 27:3
    ('note', 'observe'), # PSA 107:43
    ('notice', 'regard'), # RUT 2:19
    ('noticed', 'found'), # NUM 15:32
    ('numerous', 'great'), # DEU 30:5
    ('oath', 'swear'), # HOS 4:15
    ('oath', 'swears'), # JER 51:14
    ('oath', 'swore'), # REV 10:6
    ('oath', 'sworn'), # AMO 8:7
    ('oaths', 'sworn'), # JER 5:7
    ('obedient', 'obedience'), # CO2 10:5
    ('Obey', 'listen'), # JER 38:20
    ('obey', 'listen'), # SA1 15:19
    ('obeyed', 'listened'), # JOS 22:2
    ('object', 'instrument'), # NUM 35:16
    ('obligations', 'duty'), # NUM 3:8
    ('Observe', 'keep'), # DEU 5:12
    ('observe', 'keep'), # EXO 12:25
    ('occupation', 'works'), # GEN 47:3
    ('occupied', 'taken'), # JER 40:10
    ('occupy', 'take'), # DEU 4:5
    ('ocean', 'sea'), # CH2 8:17
    ('ocean', 'seas'), # EZE 27:4
    ('oceans', 'sea'), # PSA 95:5
    ('oceans', 'seas'), # DEU 33:19
    ('offence', 'offense'), # ROM 9:33
    ('offend', 'offense'), # JN1 2:10
    ('offensive', 'offending'), # JHN 6:61
    ('offensive', 'offense'), # GAL 5:11
    ('offensive', 'offensiveness'), # JER 23:13
    ('offered', 'volunteered'), # NEH 11:2
    ('offering', 'present'), # LEV 4:23
    ('offerings', 'contribution'), # MAL 3:8
    ('offerings', 'contributions'), # NUM 18:8
    ('offerings', 'wave-offering'), # NUM 18:18
    ('officer', 'official'), # JER 51:59
    ('officers', 'officials'), # DEU 20:5
    ('official', 'officer'), # KI2 25:19
    ('officials', 'officers'), # ACT 16:35
    ('officials', 'overseers'), # CH2 8:10
    ('officials', 'princes'), # ZEP 1:8
    ('offspring', 'descendants'), # JOB 27:14
    ('older', 'aged'), # JOB 32:6
    ('older', 'old'), # EZE 16:46
    ('oldest', 'old'), # SA1 17:28
    ('olive', 'olive[s]'), # EXO 27:20
    ('olives', 'olive[s]'), # MIC 6:15
    ('onward', 'onwards'), # EZE 43:27
    ('opportunity', 'opportune'), # MRK 6:21
    ('opposes', 'oppositions'), # TI1 6:20
    ('oppress', 'afflict'), # PSA 89:22
    ('oppress', 'oppression'), # PSA 10:7
    ('oppress', 'oppressors'), # ISA 3:12
    ('oppressed', 'afflicted'), # DEU 26:6
    ('oppressed', 'crushed'), # CH2 16:10
    ('oppressed', 'oppression'), # EZE 22:7
    ('oppressed', 'oppressions'), # PRO 29:13
    ('oppressive', 'oppressor'), # JER 46:16
    ('oppressors', 'afflicted'), # ZEP 3:19
    ('oppressors', 'oppress'), # PSA 119:121
    ('oppressors', 'oppresses'), # ZEP 3:1
    ('orchards', 'grove'), # EXO 23:11
    ('orchards', 'groves'), # SA1 8:14
    ('order', 'arrange'), # JOB 33:5
    ('order', 'said'), # DAN 5:29
    ('ordered', 'decree'), # EZR 4:19
    ('ordered', 'said'), # NEH 13:9
    ('ordered', 'sayingms'), # DAN 3:19
    ('orderly', 'order'), # CO1 14:40
    ('ornaments', 'ornament[s]'), # EZE 7:20
    ('orphan', 'fatherless'), # DEU 27:19
    ('orphans', 'fatherless'), # MAL 3:5
    ('out-house', 'outhouses'), # KI2 10:27
    ('outer', 'outermost'), # EXO 26:4
    ('outnumber', 'excess'), # NUM 3:46
    ('outside', 'external'), # NEH 11:16
    ('outsider', 'stranger'), # NUM 18:4
    ('outsiders', 'outside'), # CO1 5:12
    ('outskirts', 'edge'), # SA1 14:2
    ('outskirts', 'outskirt[s]'), # NUM 22:41
    ('overcame', 'defeated'), # NUM 21:35
    ('overcome', 'defeated'), # KI2 14:12
    ('overpowers', 'overcome'), # LUK 11:22
    ('overseer', 'overseeing'), # TI1 3:1
    ('overthrows', 'subverted'), # PRO 22:12
    ('overthrows', 'subverts'), # JOB 12:19
    ('overwhelm', 'devastate'), # JOB 12:15
    ('overwhelm', 'overtake'), # ISA 35:10
    ('overwhelming', 'flood'), # PRO 27:4
    ('overwhelms', 'overpowers'), # JOB 15:24
    ('ownership', 'possession'), # DEU 28:21
    ('pagan', 'pagans'), # ACT 4:27
    ('paid', 'gave'), # CH1 21:25
    ('paid', 'give'), # DEU 22:19
    ('pain', 'anguish'), # JOB 6:10
    ('pain', 'labour-pains'), # JER 49:24
    ('pain', 'trouble'), # JDG 11:35
    ('Pains', 'labour-pains'), # HOS 13:13
    ('pains', 'pangs'), # SA1 4:19
    ('palace', 'house'), # CH2 28:7
    ('palace', 'household'), # KI1 18:3
    ('palaces', 'houses'), # MAT 11:8
    ('panic', 'dread'), # PRO 1:27
    ('panic', 'terrify'), # SA2 17:2
    ('parallel', 'corresponding'), # EZE 45:7
    ('paralysed', 'numb'), # HAB 1:4
    ('part', 'member'), # CO1 12:14
    ('part', 'members'), # CO1 12:18
    ('part', 'portion'), # ACT 8:21
    ('part', 'share'), # NEH 2:20
    ('parts', 'members'), # CO1 12:22
    ('parts', 'portions'), # JOS 18:6
    ('pass', 'go'), # NUM 36:9
    ('pass', 'goes'), # KI1 15:17
    ('pass', 'handing'), # LUK 11:12
    ('pass-over', 'passover'), # CH2 35:6
    ('pass-over', 'passovers'), # CH2 35:7
    ('passed', 'given'), # JHN 17:14
    ('passed', 'went'), # REV 9:12
    ('passing', 'passage'), # CO1 16:7
    ('passing', 'went'), # EZE 26:18
    ('passion', 'rage'), # REV 14:8
    ('past', 'beyond'), # HEB 11:11
    ('pastureland', 'pasture'), # CH1 5:16
    ('pasturelands', 'pasture'), # CH1 13:2
    ('Path', 'way'), # ACT 22:4
    ('path', 'direction'), # PRO 7:8
    ('path', 'road/course'), # JOB 3:23
    ('path', 'track'), # PSA 140:5
    ('paths', 'tracks'), # PRO 2:18
    ('paths', 'way'), # JER 3:21
    ('paths', 'ways'), # HOS 9:8
    ('patiently', 'patience'), # PE1 3:20
    ('patiently', 'patient'), # LUK 18:7
    ('pay', 'give'), # EZE 16:41
    ('pay', 'giving'), # LUK 23:2
    ('payment', 'tribute'), # EZE 27:15
    ('peace', 'peaceable'), # HEB 12:11
    ('peace', 'security'), # DAN 11:24
    ('peace', 'undisturbed'), # ZEC 1:11
    ('peace', 'welfare'), # CH1 18:10
    ('peace', 'well-being'), # MAL 2:5
    ('peace-loving', 'peaceable'), # TI1 3:3
    ('peaceable', 'peaceful'), # SA2 20:19
    ('peaceably', 'peace'), # EPH 2:15
    ('peaceful', 'peace'), # GEN 34:21
    ('peacefully', 'peace'), # EXO 18:23
    ('peacemakers', 'peacemaking'), # MAT 5:9
    ('peak', 'top'), # EZE 43:12
    ('peeled', 'stripped'), # GEN 30:38
    ('pen', 'stylus'), # JOB 19:24
    ('pens', 'folds'), # PSA 50:9
    ('People', 'men'), # JOB 24:12
    ('people', 'community'), # PSA 68:10
    ('people', 'humankind'), # JOB 28:4
    ('people', 'inhabitants'), # CH2 35:18
    ('people', 'kinspeoples'), # GEN 17:14
    ('people', 'man'), # CH1 26:8
    ('people', 'men'), # DEU 26:5
    ('people', 'souls'), # PE2 2:14
    ('peoples', 'clans'), # NAH 3:4
    ('perceive', 'observes'), # JOB 33:14
    ('perfect', 'complete'), # JOB 37:16
    ('perfect', 'perfection'), # COL 3:14
    ('perfection', 'perfect'), # CO1 13:10
    ('perfection', 'perfected'), # PHP 3:12
    ('perform', 'act'), # DEU 25:5
    ('perform', 'done'), # PSA 31:19
    ('performed', 'did'), # EZE 16:50
    ('perfume', 'nard'), # SNG 1:12
    ('perfume', 'ointment'), # ECC 7:1
    ('perfumes', 'ointment'), # CH2 16:14
    ('perfumes', 'perfumers'), # SA1 8:13
    ('perishing', 'passing'), # JOB 33:18
    ('permanently', 'permanent'), # HEB 7:24
    ('permissible', 'permitting'), # MAT 12:12
    ('permission', 'permitted'), # JHN 19:38
    ('permission', 'permitting'), # JHN 18:31
    ('perpetual', 'perpetuity'), # ISA 60:15
    ('perpetually', 'perpetuity'), # EZE 35:9
    ('persecute', 'harass'), # PSA 119:84
    ('persecuted', 'harassed'), # PSA 69:26
    ('persecuting', 'persecution'), # ISA 14:6
    ('persevering', 'perseverance'), # EPH 6:18
    ('persist', 'persistence'), # LUK 11:8
    ('persistently', 'endurance'), # ROM 2:7
    ('person', 'man'), # SA1 10:6
    ('person', 'men'), # SA2 6:20
    ('person', 'personally'), # CO1 12:11
    ('personality', 'person'), # ROM 6:6
    ('persuasive', 'persuade'), # COL 2:4
    ('persuasive', 'persuasiveness'), # PRO 16:21
    ('Perverse', 'perversities'), # PRO 16:28
    ('perverse', 'perversities'), # DEU 32:20
    ('perversely', 'perverse'), # PRO 2:12
    ('perversions', 'perverseness'), # EZE 9:9
    ('perversity', 'perverseness'), # PRO 15:4
    ('pestered', 'urged'), # JDG 16:16
    ('petition', 'prayer'), # JER 7:16
    ('physically', 'flesh'), # ROM 9:5
    ('pick', 'take'), # JHN 5:8
    ('pick', 'taken'), # LUK 5:24
    ('pick', 'taking'), # MAT 10:38
    ('picked', 'took'), # KI2 2:13
    ('picking', 'taken'), # LUK 22:19
    ('picking', 'taking'), # LUK 19:21
    ('piece', 'part'), # LUK 24:42
    ('pile', 'heap'), # RUT 3:7
    ('pile', 'heaped'), # HAB 1:10
    ('piled', 'heap'), # JOS 7:26
    ('piles', 'heaps'), # CH2 31:8
    ('pillars', 'pillar[s]'), # EXO 24:4
    ('pilots', 'sailors'), # EZE 27:8
    ('pitchers', 'jugs'), # EXO 25:29
    ('pitchfork', 'fork'), # JER 15:7
    ('pitfall', 'pit'), # LAM 3:47
    ('pitied', 'compassion'), # EZE 20:17
    ('pity', 'compassion'), # JOL 2:17
    ('Place', 'set'), # SA2 11:15
    ('place', 'lay'), # NUM 8:12
    ('place', 'put'), # DEU 31:26
    ('place', 'putting'), # MAT 12:18
    ('place', 'site'), # GEN 23:4
    ('placed', 'laying'), # ACT 8:17
    ('placed', 'put'), # CH2 17:2
    ('placed', 'set'), # DEU 26:10
    ('placed', 'setting'), # PRO 25:7
    ('places', 'put'), # ACT 9:12
    ('places', 'residence'), # HAB 3:11
    ('placing', 'laid'), # MRK 6:5
    ('Plague', 'pestilence'), # EZE 5:17
    ('plain', 'level'), # ZEC 4:7
    ('plain', 'valley'), # CH2 35:22
    ('plainly', 'plainness'), # JHN 11:14
    ('plains', 'valley'), # JDG 1:19
    ('planning', 'scheme'), # ECC 9:10
    ('plans', 'schemes'), # PSA 5:10
    ('plant', 'growth'), # EZE 16:7
    ('plant', 'plant[s]'), # GEN 1:30
    ('plant', 'set'), # ISA 41:19
    ('plant', 'shoot'), # ISA 53:2
    ('planter', 'planting'), # CO1 3:7
    ('plants', 'plant[s]'), # GEN 9:3
    ('plants', 'plantation'), # ISA 5:7
    ('plants', 'vegetation'), # EXO 10:12
    ('plaster', 'lime'), # DEU 27:2
    ('plastered', 'sealed'), # EXO 2:3
    ('plateau', 'plain'), # JOS 13:9
    ('plates', 'dishes'), # EXO 25:29
    ('plates', 'scales'), # KI1 22:34
    ('plaza', 'place'), # CH2 32:6
    ('plaza', 'places'), # PRO 5:16
    ('plazas', 'places'), # JER 5:1
    ('plea', 'supplications'), # PSA 31:22
    ('pleaded', 'implored'), # MAT 18:32
    ('pleaded', 'imploring'), # LUK 8:41
    ('pleading', 'imploring'), # LUK 8:31
    ('pleasant', 'delights'), # MIC 2:9
    ('pleasant', 'pleasantnesses'), # ISA 17:10
    ('pleasant', 'sweetness'), # PRO 16:21
    ('please', 'pleasure'), # CO1 7:33
    ('pleased', 'delighted'), # KI1 10:9
    ('pleased', 'good'), # GEN 34:18
    ('pleased', 'pleasant'), # SA2 1:23
    ('pleased', 'pleasure'), # ACT 6:5
    ('pleases', 'good'), # EZR 5:17
    ('pleases', 'pleasure'), # ROM 8:8
    ('pleasing', 'delight'), # ECC 12:10
    ('pleasing', 'pleasure'), # CO1 7:32
    ('pleasure', 'delights'), # PSA 37:23
    ('pleasure', 'pleasant'), # PRO 2:10
    ('pleasures', 'delights'), # ECC 2:8
    ('plentiful', 'plenty'), # GEN 41:29
    ('plenty', 'plentiful'), # PHP 4:18
    ('plot', 'conspiracy'), # KI2 15:15
    ('plot', 'planning'), # PSA 37:12
    ('plots', 'conspiracies'), # PSA 31:20
    ('plots', 'counsel'), # PSA 64:2
    ('plots', 'plan'), # JER 18:23
    ('plots', 'plans'), # LAM 3:60
    ('plotted', 'planned'), # EST 9:24
    ('plunder', 'booty'), # CH2 15:11
    ('plunder', 'spoil'), # EZE 25:7
    ('plundered', 'plunderers'), # KI2 17:20
    ('plundered', 'spoil'), # EZE 23:46
    ('plunge', 'dip'), # JOB 9:31
    ('polluted', 'pollutions'), # ACT 15:20
    ('poorest', 'poor'), # KI2 25:12
    ('popular', 'acceptable'), # EST 10:3
    ('porters', 'burden-bearers'), # CH2 34:13
    ('portion', 'share'), # GEN 31:14
    ('position', 'place'), # ECC 10:4
    ('positions', 'deployed'), # JDG 20:30
    ('possess', 'possession'), # DEU 2:12
    ('possession', 'possessed'), # MAT 15:22
    ('possessions', 'acquisition'), # PSA 105:21
    ('possessions', 'possessing'), # LUK 12:15
    ('possessions', 'possession[s]'), # GEN 14:11
    ('possessions', 'property'), # CH2 21:14
    ('pottery', 'potter'), # JER 18:3
    ('pounding', 'beating'), # JDG 19:22
    ('poverty', 'lack'), # PRO 14:23
    ('poverty', 'lacked'), # JER 44:18
    ('power', 'mighty'), # JOB 26:14
    ('power', 'powerful'), # CO2 10:4
    ('power', 'strength'), # CH1 29:11
    ('powerful', 'almighty'), # RUT 1:21
    ('powerful', 'great'), # CH1 11:9
    ('powerful', 'mighty'), # DAN 11:23
    ('powerful', 'power'), # ACT 19:20
    ('powerful', 'strength'), # CH2 22:9
    ('practice', 'doing'), # JAM 2:13
    ('practice', 'done'), # LUK 6:49
    ('praise', 'extol'), # PSA 63:3
    ('praise', 'glorify'), # MAT 5:16
    ('praise', 'glorifying'), # PE1 4:16
    ('praise', 'thanks'), # PSA 30:9
    ('praised', 'glorified'), # ACT 11:18
    ('praiseworthy', 'praise'), # CH1 16:35
    ('praising', 'glorifying'), # ACT 4:21
    ('prayer', 'entreated'), # GEN 25:21
    ('prayer', 'petition'), # TI1 4:5
    ('prayer', 'supplications'), # DAN 9:23
    ('prayers', 'entreat'), # ZEC 7:2
    ('prayers', 'entreated'), # CH1 5:20
    ('prayers', 'petition'), # PHP 1:19
    ('precious', 'desire'), # DAN 11:8
    ('precious', 'desires'), # LAM 2:4
    ('precious', 'preciously'), # PE1 1:7
    ('precious', 'preciousness'), # HOS 13:15
    ('pregnant', 'conceived'), # GEN 19:36
    ('preparation', 'prepared'), # CH1 29:19
    ('prepare', 'appoint'), # EZE 35:6
    ('prepare', 'arrange'), # ISA 65:11
    ('prepare', 'make'), # MAL 3:1
    ('prepared', 'arranged'), # CH2 35:10
    ('prepared', 'made'), # CH2 35:1
    ('prepared', 'preparation'), # JHN 19:14
    ('prepared', 'ready'), # LUK 22:33
    ('prescribed', 'appointed'), # CH2 30:22
    ('presence', 'front'), # EST 2:23
    ('present', 'give'), # PRO 4:9
    ('present', 'presence'), # EXO 39:36
    ('present', 'station'), # EXO 34:2
    ('presented', 'bring'), # NUM 5:9
    ('presented', 'brought'), # DAN 7:13
    ('presenter', 'present'), # LEV 1:13
    ('presenter', 'presented'), # LEV 7:18
    ('presenting', 'bringing'), # NUM 16:35
    ('presents', 'gift'), # KI2 8:9
    ('preserves', 'keeps'), # PRO 19:8
    ('pressure', 'press'), # DEU 15:3
    ('prevent', 'forbidding'), # MRK 10:14
    ('prevented', 'restrained'), # GEN 16:2
    ('previous', 'former'), # DAN 7:24
    ('price', 'money'), # CH1 21:22
    ('price', 'silver'), # GEN 23:9
    ('pride', 'exaltation'), # ISA 4:2
    ('pride', 'haughtiness'), # PSA 10:4
    ('priest', 'priesthood'), # HEB 7:24
    ('priestly', 'priesthoods'), # SA1 2:36
    ('priestly', 'priests'), # CH2 31:17
    ('priests', 'priesthood'), # EXO 29:9
    ('priests', 'priestly'), # LUK 1:9
    ('prison', 'imprisoned'), # JDG 16:21
    ('prison', 'imprisonment'), # CH2 18:26
    ('prison', 'prisoners'), # ECC 4:14
    ('prison', 'stock[s]'), # CH2 16:10
    ('prisoner', 'captive'), # KI1 8:46
    ('prisoners', 'prisoner[s]'), # ISA 10:4
    ('privately', 'quietness'), # SA2 3:27
    ('privately', 'secrecy'), # SA1 18:22
    ('problems', 'troubles'), # MAT 26:10
    ('proceed', 'go'), # DEU 1:26
    ('proclaim', 'proclaimer'), # TI1 2:7
    ('proclaim', 'proclamation'), # TIT 1:3
    ('proclaimed', 'proclamation'), # TI2 4:17
    ('prod', 'goads'), # ECC 12:11
    ('produce', 'fruits'), # LAM 4:9
    ('produce', 'products'), # GEN 43:11
    ('produce', 'raise'), # GEN 38:8
    ('produce', 'vigor/produce'), # GEN 4:12
    ('producer', 'producing'), # ROM 7:13
    ('produces', 'vigor/produce'), # JOB 31:39
    ('product', 'produce'), # PRO 18:20
    ('profited', 'wealth'), # PSA 44:12
    ('prominent', 'prominence'), # ACT 25:23
    ('promise', 'oath'), # CH1 16:16
    ('promised', 'foretold'), # GAL 3:8
    ('promised', 'words/messages'), # CH1 25:5
    ('promises', 'oath'), # SA2 21:7
    ('promises', 'oaths'), # MRK 6:26
    ('promoted', 'exalted'), # EST 5:11
    ('promoted', 'exalting'), # KI1 1:5
    ('pronounced', 'spoke'), # JER 39:5
    ('pronounced', 'spoken'), # JER 26:19
    ('property', 'money'), # EXO 21:21
    ('property', 'possession'), # EZE 46:16
    ('prophecies', 'prophesies'), # CO1 13:8
    ('prophecy', 'prophesying'), # CO1 11:4
    ('prophecy', 'prophet'), # DAN 9:24
    ('prophesied', 'prophecy'), # TI1 4:14
    ('prophesy', 'prophecy'), # CO1 13:2
    ('prophet', 'prophesied'), # MAT 15:7
    ('prophet', 'prophesying'), # JER 29:26
    ('prophet', 'seer'), # CH2 16:10
    ('prophetic', 'prophecy'), # REV 22:19
    ('prophets', 'prophetic'), # PE2 1:19
    ('prosper', 'succeed'), # DAN 8:12
    ('prosper', 'successful'), # DAN 8:25
    ('prospered', 'successful'), # CH1 29:23
    ('prosperity', 'good'), # JOB 21:13
    ('prosperity', 'peace'), # JOB 15:21
    ('prostitutes', 'prostitute[s]'), # KI1 14:24
    ('prostitution', 'prostitute'), # EZE 16:41
    ('protect', 'preserves'), # PRO 14:3
    ('protect', 'protection'), # DAN 11:1
    ('protect', 'shade'), # NUM 14:9
    ('protection', 'cover'), # PSA 5:11
    ('protection', 'sheltering'), # REV 7:15
    ('protector', 'guard/protect'), # HOS 4:10
    ('proud', 'haughty'), # ECC 7:8
    ('proud', 'pride'), # JOB 38:11
    ('proud', 'prides'), # EZE 16:56
    ('proved', 'demonstrated'), # CO2 7:11
    ('proved', 'provenness'), # CO2 8:2
    ('proven', 'provenness'), # PHP 2:22
    ('proverbs', 'byword'), # JER 24:9
    ('province', 'region'), # EZR 4:16
    ('provinces', 'province[s]'), # EST 1:1
    ('provinces', 'region'), # ACT 10:39
    ('provincial', 'province'), # NEH 11:3
    ('provincial', 'provinces'), # DAN 3:2
    ('proving', 'provenness'), # CO2 9:13
    ('provisions', 'provision[s]'), # GEN 42:25
    ('provisions', 'sustenance'), # JOS 9:14
    ('provocations', 'rebelling'), # JOB 17:2
    ('provoke', 'provocation'), # HEB 10:24
    ('provoke', 'provokers'), # JOB 12:6
    ('provoked', 'provocation'), # EZE 20:28
    ('prowl', 'walk'), # PSA 12:8
    ('prudent', 'prudence'), # PRO 8:5
    ('pruned', 'cut'), # ROM 11:22
    ('public', 'publicly'), # ACT 20:20
    ('publicly', 'public'), # COL 2:15
    ('puffed', 'swollen'), # HAB 2:4
    ('pull', 'draw'), # JOB 20:25
    ('pull', 'drew'), # JDG 3:22
    ('pull', 'pluck'), # ECC 3:2
    ('pull', 'tear'), # ISA 22:19
    ('pulled', 'drew'), # GEN 37:28
    ('pulled', 'torn'), # JOB 18:14
    ('punish', 'punishment'), # JER 48:44
    ('punished', 'punishment'), # JN1 4:18
    ('punished', 'retribution'), # PSA 91:8
    ('punishing', 'fine'), # PRO 21:11
    ('punishment', 'reprove'), # HAB 1:12
    ('purchased', 'bought'), # REV 14:4
    ('pure', 'holiness'), # EZE 39:25
    ('pure', 'unadulterated'), # PE1 2:2
    ('purge', 'remove'), # DEU 24:7
    ('purification', 'cleansing'), # EZE 43:23
    ('purification', 'purified'), # ACT 21:24
    ('purified', 'cleansed'), # CH2 29:18
    ('purified', 'purification'), # EZE 44:26
    ('purified', 'sanctified'), # ACT 20:32
    ('purify', 'cleanse'), # EZE 43:20
    ('purify', 'sanctify'), # NUM 11:18
    ('purity', 'holy'), # EZE 38:23
    ('pursuer', 'pursued'), # LAM 1:6
    ('pursuers', 'pursue'), # JER 17:18
    ('pursuers', 'pursuer[s]'), # JOS 8:20
    ('pursuit', 'pursuing'), # JDG 8:4
    ('push', 'drive'), # ISA 22:19
    ('pushed', 'drive'), # JER 46:15
    ('put', 'assigned'), # EXO 24:6
    ('put', 'laid'), # ACT 4:37
    ('put', 'laying'), # MAT 23:4
    ('put', 'set'), # CH1 16:1
    ('putting', 'laid'), # ACT 28:3
    ('puzzled', 'perplexed'), # LUK 1:29
    ('puzzled', 'perplexing'), # ACT 5:24
    ('puzzling', 'perplexing'), # LUK 24:4
    ('qualifications', 'qualified'), # CO2 3:5
    ('quarrel', 'disputed'), # GEN 26:22
    ('quarrelled', 'disputed'), # GEN 26:21
    ('quarrels', 'contentions'), # PRO 18:19
    ('quarter', 'fourth'), # REV 6:8
    ('quarters', 'room'), # NEH 3:30
    ('queen', 'queenhood'), # EST 4:14
    ('quench', 'extinguish'), # SNG 8:7
    ('question', 'ask'), # JOB 38:3
    ('questioned', 'asked'), # JER 38:27
    ('questioned', 'enquired'), # JDG 8:14
    ('questioning', 'doubted'), # ACT 11:12
    ('quick', 'quickly'), # CH2 18:8
    ('Quickly', 'quickness'), # ACT 12:7
    ('quickly', 'haste'), # JDG 13:10
    ('quickly', 'hasten'), # ISA 60:22
    ('quickly', 'hastened'), # EST 2:9
    ('quickly', 'hastens'), # PRO 19:2
    ('quickly', 'hurried'), # GEN 24:18
    ('quickly', 'hurry'), # EST 6:10
    ('quickly', 'quickness'), # LUK 18:8
    ('quickly', 'suddenness'), # CH2 29:36
    ('quiet', 'peace'), # KI2 11:20
    ('quiet', 'quietness'), # ACT 22:2
    ('quiet', 'silent'), # JDG 16:2
    ('quieten', 'silenced'), # NUM 13:30
    ('quietened', 'quiet'), # PSA 107:30
    ('quietly', 'quiet'), # HAB 3:16
    ('quietly', 'quietness'), # ECC 9:17
    ('quietly', 'secrecy'), # RUT 3:7
    ('quietness', 'security'), # PRO 17:1
    ('rabbit', 'hare'), # LEV 11:6
    ('radiates', 'radiance'), # HEB 1:3
    ('rage', 'fury'), # PRO 11:4
    ('raiding', 'marauding'), # KI1 11:24
    ('raids', 'marauding'), # KI2 13:20
    ('rainy', 'rain'), # EZE 1:28
    ('raise', 'lift'), # ISA 11:12
    ('raised', 'lifted'), # EZE 20:6
    ('raisin', 'raisin-cake'), # CH1 16:3
    ('raisin', 'raisin-cakes'), # SNG 2:5
    ('raising', 'rise'), # ISA 14:9
    ('raisins', 'raisin-cake'), # SA2 6:19
    ('ran', 'fled'), # DAN 10:7
    ('ran', 'went'), # KI1 18:35
    ('rape', 'violate'), # EST 7:8
    ('ravaged', 'desolate'), # ISA 49:17
    ('reach', 'approach'), # SA2 5:8
    ('reach', 'attain'), # EPH 4:13
    ('reach', 'near'), # JDG 19:13
    ('reached', 'grasped'), # ROM 9:30
    ('reached', 'stretched'), # PSA 18:16
    ('reached', 'touches'), # JOS 16:7
    ('ready', 'prepare'), # EZE 7:14
    ('ready', 'prepared'), # PSA 7:12
    ('realised', 'understood'), # MAT 17:13
    ('reason', 'cause'), # CO2 6:3
    ('reason', 'caused'), # EXO 9:16
    ('rebel', 'rebellion'), # JER 28:16
    ('rebelled', 'rebellion'), # HEB 3:15
    ('rebelled', 'rebellious'), # JER 4:17
    ('rebelled', 'rose'), # NUM 16:2
    ('rebelling', 'rebellion'), # ISA 1:5
    ('rebelling', 'rebellious'), # ZEP 3:1
    ('rebelling', 'rising'), # MAT 10:21
    ('rebellion', 'rebelling'), # JOS 22:16
    ('rebellion', 'transgression'), # NUM 14:18
    ('rebellion', 'transgressions'), # LEV 16:16
    ('rebellious', 'rebelled'), # KI1 13:21
    ('rebellious', 'rebellion'), # EZE 2:5
    ('rebellious', 'rebelliousness'), # SA1 20:30
    ('rebellious', 'transgression'), # PSA 107:17
    ('rebels', 'rebellious'), # HOS 9:15
    ('rebuild', 'build'), # EZR 5:2
    ('rebuild', 'built'), # PSA 102:16
    ('rebuilt', 'built'), # NUM 32:34
    ('recede', 'decreasing'), # GEN 8:5
    ('receive', 'take'), # PSA 49:15
    ('receive', 'took'), # REV 20:4
    ('received', 'obtained'), # HEB 6:15
    ('received', 'taking'), # ROM 1:27
    ('reckless', 'recklessness'), # JER 23:32
    ('reckon', 'counting'), # CO2 11:5
    ('reckoned', 'counted'), # HEB 11:19
    ('recognise', 'know'), # DEU 18:21
    ('recognise', 'known'), # ACT 13:27
    ('recognised', 'known'), # LUK 6:44
    ('recognises', 'knowing'), # NAH 1:7
    ('recognize', 'knew'), # PSA 81:5
    ('record', 'recorder'), # CH1 18:15
    ('record', 'write'), # REV 1:19
    ('recorded', 'written'), # EZR 8:34
    ('recorded', 'wrote'), # EST 9:20
    ('records', 'enrolment'), # CH1 4:33
    ('recover', 'live'), # ISA 38:21
    ('red', 'ruddy'), # SNG 5:10
    ('reddish-white', 'reddish'), # LEV 13:19
    ('redeemer', 'vindicator'), # JOB 19:25
    ('reduce', 'cut'), # KI2 10:32
    ('reeds', 'rush[es]'), # EXO 2:5
    ('reestablished', 'restored'), # KI2 14:22
    ('reflect', 'consider'), # PRO 20:25
    ('reformed', 'reformation'), # HEB 9:10
    ('refreshing', 'refreshment'), # ACT 3:20
    ('refuse', 'reject'), # ISA 7:15
    ('refused', 'rejected'), # ISA 8:6
    ('regard', 'consider'), # JOB 19:15
    ('regarded', 'considered'), # LAM 4:2
    ('regenerated', 'regeneration'), # TIT 3:5
    ('regret', 'regretful'), # MAT 21:32
    ('regretted', 'regretful'), # MAT 21:29
    ('regular', 'continuity'), # NUM 4:16
    ('regular', 'perpetual'), # DAN 8:11
    ('regulation', 'ordinance'), # LEV 5:10
    ('regulations', 'decrees'), # PSA 119:8
    ('reject', 'abandon'), # PSA 119:53
    ('reject', 'abandoned'), # PSA 119:87
    ('reject', 'spurns'), # PRO 15:5
    ('rejected', 'abandoned'), # CH2 10:8
    ('rejected', 'scorned'), # ACT 4:11
    ('rejected', 'spurned'), # DEU 32:19
    ('rejects', 'neglects'), # PRO 10:17
    ('rejoice', 'exult'), # PRO 2:14
    ('related', 'relative'), # LEV 18:12
    ('related', 'relative[s]'), # LEV 18:17
    ('relative', 'brother'), # JER 23:35
    ('relative', 'kinsman'), # KI1 16:11
    ('relative', 'relative[s]'), # LEV 25:49
    ('relatives', 'brother'), # CH1 9:17
    ('relatives', 'brothers'), # CH1 7:22
    ('relatives', 'kindred'), # JOB 19:14
    ('relatives', 'kinsmen'), # PSA 38:11
    ('relax', 'relaxation'), # CO2 2:13
    ('relaxed', 'relaxation'), # ACT 24:23
    ('relaxing', 'relaxation'), # CO2 8:13
    ('Release', 'redeem'), # PSA 26:11
    ('release', 'free'), # PSA 102:20
    ('release', 'untie/release'), # JOB 10:1
    ('released', 'free'), # JER 40:4
    ('released', 'redeemed'), # PSA 71:23
    ('released', 'untie/release'), # ISA 51:14
    ('releases', 'untie/release'), # JOB 37:3
    ('reliable', 'reliability'), # JER 2:21
    ('relied', 'depended'), # CH2 16:8
    ('relief', 'ease'), # ISA 1:24
    ('relief', 'quiet'), # PSA 94:13
    ('religious', 'religion'), # ACT 26:5
    ('rely', 'trust'), # ISA 36:15
    ('remain', 'dwell'), # SA1 1:22
    ('remain', 'leave'), # ISA 65:15
    ('remainder', 'remained'), # KI2 10:17
    ('remainder', 'remains'), # CH2 31:10
    ('remainder', 'rest'), # DAN 7:7
    ('remained', 'continuing'), # LUK 1:22
    ('remaining', 'left'), # NUM 21:35
    ('remaining', 'remainder'), # LEV 14:17
    ('remember', 'remembrance'), # LUK 22:19
    ('remembered', 'remembrance'), # DEU 25:19
    ('remembering', 'remembrance'), # TH1 1:2
    ('remembrance', 'remember'), # PSA 77:6
    ('reminder', 'memorial'), # EXO 13:9
    ('remnant', 'leave'), # EZE 6:8
    ('remnant', 'left'), # ZEC 9:7
    ('remote', 'remotest'), # JDG 19:18
    ('removal', 'removing'), # ISA 27:9
    ('remove', 'removal'), # PE1 3:21
    ('remove', 'take'), # HEB 10:11
    ('removed', 'move'), # JOB 18:4
    ('removed', 'taken'), # COL 2:14
    ('removed', 'took'), # GEN 48:12
    ('removes', 'taking'), # JHN 15:2
    ('removing', 'taken'), # MRK 15:46
    ('renewed', 'renewal'), # TIT 3:5
    ('renewing', 'renewal'), # ROM 12:2
    ('renounced', 'repudiated'), # PSA 89:39
    ('renovate', 'repair'), # CH2 24:5
    ('repair', 'renew'), # CH2 24:4
    ('repaired', 'renewed'), # CH2 15:8
    ('repay', 'repayment'), # LUK 14:12
    ('repay', 'return'), # PSA 116:12
    ('repent', 'repentance'), # ACT 5:31
    ('repent', 'repentant'), # ISA 1:27
    ('repentance', 'repent'), # JOB 42:6
    ('repented', 'sighed/regretted'), # EXO 32:14
    ('repenting', 'repentance'), # HEB 6:1
    ('replied', 'say'), # KI1 5:2
    ('replied', 'saying'), # ACT 7:2
    ('report', 'tell'), # ACT 23:18
    ('reported', 'described'), # LUK 9:10
    ('reported', 'told'), # ISA 7:2
    ('represents', 'representation'), # HEB 1:3
    ('represents', 'representative'), # PE1 3:21
    ('reputation', 'report'), # PRO 25:10
    ('request', 'asked'), # KI1 3:13
    ('request', 'petition'), # JOB 6:8
    ('requested', 'asked'), # DAN 2:16
    ('requested', 'sought'), # CH1 15:13
    ('requesting', 'asking'), # SA1 8:10
    ('requesting', 'seek'), # CH1 22:19
    ('requests', 'seek'), # DAN 9:3
    ('requirements', 'charge'), # MAL 3:14
    ('Rescue', 'deliver'), # ISA 44:17
    ('Rescue', 'save'), # PSA 31:16
    ('rescue', 'deliverance'), # ISA 59:11
    ('rescue', 'delivered'), # JDG 12:2
    ('rescue', 'delivers'), # PRO 11:4
    ('rescue', 'salvation'), # CH2 6:41
    ('rescue', 'save'), # CH2 20:9
    ('rescue', 'saved'), # ISA 63:9
    ('rescued', 'deliverance'), # PSA 144:10
    ('rescued', 'delivered'), # JDG 8:34
    ('rescued', 'salvation'), # PE1 2:2
    ('rescued', 'save'), # HAB 1:2
    ('rescued', 'saved'), # ROM 10:9
    ('rescuer', 'deliverer'), # ISA 5:29
    ('rescuer', 'rescue'), # JNA 2:10
    ('rescuer', 'rescuing'), # ROM 11:26
    ('rescuer', 'saviour'), # MAT 21:15
    ('rescues', 'delivers'), # PRO 10:2
    ('rescues', 'salvation'), # PSA 62:2
    ('rescuing', 'delivered'), # SA1 14:48
    ('rescuing', 'salvation'), # PSA 118:21
    ('rescuing', 'save'), # JER 30:10
    ('reserve', 'store'), # GEN 41:36
    ('resides', 'rests'), # PRO 14:33
    ('resist', 'stand'), # NAH 1:6
    ('resolution', 'resolved'), # JER 4:28
    ('Respect', 'fear'), # ISA 33:6
    ('respect', 'fear'), # ACT 9:31
    ('respect', 'feared'), # KI2 17:25
    ('respect', 'fearing'), # LUK 23:40
    ('respect', 'honour'), # EST 1:20
    ('respect', 'honoured'), # LAM 5:12
    ('respected', 'fear'), # GEN 31:53
    ('respected', 'feared'), # MAL 1:14
    ('respected', 'fearing'), # MRK 6:20
    ('respected', 'honour'), # CH2 17:5
    ('respected', 'honoured'), # ACT 5:34
    ('respectfully', 'respect'), # PE1 2:18
    ('Respecting', 'fear'), # PRO 14:26
    ('respecting', 'feared'), # JOB 1:9
    ('respects', 'fearing'), # PRO 13:13
    ('respond', 'answer'), # ISA 41:17
    ('responded', 'say'), # KI1 12:16
    ('responding', 'answer'), # JOB 16:3
    ('response', 'answering'), # ACT 25:9
    ('responsible', 'duty'), # NUM 3:25
    ('rest', 'lie'), # EZE 34:15
    ('rest', 'lie down'), # EZE 34:15
    ('rest', 'lying'), # PSA 139:3
    ('rest', 'lying down'), # PSA 139:3
    ('rest', 'relaxation'), # CO2 7:5
    ('rest', 'remainder'), # CH1 11:8
    ('rest', 'remained'), # JOS 17:6
    ('rest', 'stays'), # HAB 2:5
    ('rested', 'remained'), # EZR 8:32
    ('restoration', 'restoring'), # MRK 9:12
    ('restrain', 'holds'), # JOB 37:4
    ('restraint', 'restrained'), # ISA 14:6
    ('restricted', 'restrained'), # LUK 24:16
    ('result', 'outcome'), # PE1 1:9
    ('resurrected', 'resurrection'), # LUK 20:33
    ('retreat', 'turned'), # SA2 1:22
    ('retreat', 'turns'), # JOB 39:22
    ('retreated', 'turned'), # JDG 20:42
    ('Return', 'go'), # GEN 44:25
    ('Return', 'go back'), # GEN 44:25
    ('Return', 'restore'), # KI2 8:6
    ('return', 'came'), # KI1 10:22
    ('return', 'come'), # JDG 5:28
    ('return', 'repay'), # SA2 16:12
    ('return', 'restored'), # HEB 13:19
    ('return', 'turn'), # DEU 30:2
    ('return', 'turn back'), # DEU 30:2
    ('return', 'turned back'), # ISA 9:13
    ('return', 'went'), # JOS 22:6
    ('returned', 'came'), # EST 4:9
    ('returned', 'come'), # MRK 14:40
    ('returned', 'gone'), # ACT 25:9
    ('returned', 'turned'), # JOS 11:10
    ('returned', 'turned back'), # JOS 11:10
    ('returned', 'went'), # GEN 44:13
    ('returned', 'went back'), # GEN 44:13
    ('Returning', 'come'), # MAT 26:43
    ('returning', 'went'), # SA1 6:16
    ('returning', 'went back'), # SA1 6:16
    ('returns', 'come'), # CO1 11:26
    ('reveal', 'revelation'), # EPH 1:17
    ('revealed', 'divulged'), # LUK 20:37
    ('revealed', 'revelation'), # PE1 1:13
    ('reveals', 'revealer'), # DAN 2:29
    ('reveals', 'tells'), # AMO 4:13
    ('revere', 'fear'), # CH2 19:9
    ('revere', 'fearing'), # PSA 31:19
    ('revered', 'feared'), # CH1 16:25
    ('Revering', 'reverence'), # ROM 3:18
    ('reverse', 'revoke'), # ISA 43:13
    ('reverse', 'turn'), # NUM 23:20
    ('Revive', 'life'), # PSA 80:18
    ('revive', 'life'), # PSA 85:6
    ('revive', 'living'), # MAT 9:18
    ('revived', 'lived'), # JDG 15:19
    ('rewarded', 'repaid'), # SA2 22:25
    ('rewards', 'rewarder'), # HEB 11:6
    ('richer', 'wealth'), # KI1 10:23
    ('riches', 'wealth'), # PRO 11:28
    ('richest', 'fat'), # DAN 11:24
    ('rides', 'rider'), # PSA 68:4
    ('ridicule', 'laughs'), # PRO 29:9
    ('ridicule', 'mock'), # PSA 102:8
    ('ridicule', 'mocking'), # MRK 10:34
    ('riding', 'mounted'), # MAT 21:5
    ('riding', 'riders'), # ZEC 10:5
    ('right', 'good'), # DEU 1:39
    ('right', 'proper'), # PRO 25:11
    ('right', 'righteous'), # CH2 12:6
    ('right', 'righteousness'), # AMO 6:12
    ('right', 'righteousnesses'), # DAN 9:16
    ('right', 'rightly'), # JHN 8:48
    ('right', 'straight'), # MIC 3:9
    ('right', 'upright'), # PRO 21:2
    ('right', 'uprightness'), # JOB 33:23
    ('right', 'uprightnesses'), # PRO 8:6
    ('right-hand', 'right'), # REV 5:1
    ('right-handed', 'right'), # CH1 12:2
    ('righteous', 'righteousness'), # ISA 28:17
    ('righteous', 'righteousnesses'), # MIC 6:5
    ('righteously', 'righteousness'), # HEB 11:33
    ('rightful', 'righteousness'), # JOB 8:6
    ('rightly', 'righteousness'), # EZE 33:16
    ('rings', 'bands'), # EXO 38:10
    ('rip', 'torn'), # LUK 5:6
    ('ripped', 'pulled'), # JDG 16:14
    ('ripped', 'tore'), # GEN 37:34
    ('ripped', 'torn'), # JOB 16:9
    ('rise', 'arising'), # MIC 7:6
    ('rise', 'raised'), # MAT 24:7
    ('risen', 'arise'), # NUM 24:17
    ('risen', 'raises'), # MIC 2:8
    ('rises', 'arise'), # EXO 21:19
    ('road', 'highway'), # CH1 26:18
    ('road', 'path'), # JOB 24:4
    ('roads', 'highways'), # JDG 20:31
    ('roasted', 'cooked'), # CH2 35:13
    ('robbed', 'robbers'), # CO2 11:26
    ('robbed', 'taken'), # PRO 4:16
    ('robe', 'cloak'), # JNA 3:6
    ('robe', 'garment'), # SA2 13:19
    ('robe', 'skirt'), # ZEC 8:23
    ('robe', 'skirts'), # EZE 5:3
    ('robes', 'garments'), # CH2 34:22
    ('rock', 'stones'), # JOB 6:12
    ('rock-hard', 'stone'), # EZE 11:19
    ('rocks', 'cliffs'), # SA1 13:6
    ('rocks', 'stoned'), # ACT 5:26
    ('rode', 'sat'), # JHN 12:14
    ('roof', 'rafter[s]'), # ECC 10:18
    ('roofed', 'panelled'), # KI1 6:9
    ('room', 'chamber'), # JDG 16:9
    ('rooms', 'side-chambers'), # EZE 41:8
    ('rooms', 'store-rooms'), # CH1 9:26
    ('ropes', 'tent-cords'), # EXO 35:18
    ('rose', 'raised'), # SA2 23:1
    ('rotten', 'rottenness'), # JOB 13:28
    ('rowers', 'row'), # EZE 27:26
    ('royal', 'palace'), # DAN 11:45
    ('royal', 'royalty'), # DAN 1:3
    ('rubble', 'dust'), # EZE 26:12
    ('ruin', 'broken'), # PRO 18:24
    ('ruined', 'desolate'), # EZE 36:38
    ('ruined', 'waste'), # EZE 36:33
    ('ruins', 'desolate'), # HAG 1:4
    ('ruins', 'waste'), # EZE 26:20
    ('rule', 'decree'), # EXO 15:25
    ('rule', 'dominion'), # DAN 7:6
    ('rule', 'dominions'), # PSA 136:9
    ('rule', 'reign'), # DAN 8:23
    ('rule', 'reigning'), # ROM 6:12
    ('ruled', 'mastery'), # EZR 4:20
    ('ruled', 'reigned'), # CH1 18:14
    ('ruled', 'reigning'), # CH2 22:12
    ('ruler', 'leader'), # CH1 5:2
    ('ruler', 'noble'), # PRO 17:7
    ('ruler', 'prince'), # EZE 12:10
    ('ruler', 'rule'), # PSA 8:6
    ('rulers', 'princes'), # PRO 28:2
    ('rules', 'decree'), # PSA 99:7
    ('rules', 'decrees'), # PSA 119:5
    ('rules', 'regulations'), # DEU 6:20
    ('run', 'fled'), # KI1 11:23
    ('run', 'flee'), # LEV 26:17
    ('run', 'fleeing'), # CO1 6:18
    ('run', 'goes'), # LAM 3:48
    ('run', 'moved'), # JOB 32:15
    ('running', 'fled'), # MRK 16:8
    ('rural', 'regions'), # EST 9:19
    ('rush', 'haste'), # DEU 16:3
    ('rush', 'hastens'), # PRO 21:5
    ('rush', 'hurry'), # PRO 6:18
    ('rushed', 'haste'), # JOB 31:5
    ('rushing', 'hasten'), # JER 48:16
    ('rushing', 'hurries'), # PRO 7:23
    ('sacrifice', 'offering'), # KI2 3:20
    ('sacrificed', 'offered'), # PE1 2:24
    ('sacrifices', 'offering'), # CH1 21:29
    ('Sacrificing', 'offering'), # EXO 29:14
    ('safe', 'safety'), # JOB 21:9
    ('safety', 'refuge'), # JER 17:17
    ('safety', 'security'), # EZE 39:6
    ('said', 'speaking'), # ACT 23:7
    ('said', 'spoke'), # SA1 4:20
    ('said', 'spoken'), # CH2 10:15
    ('sailed', 'voyage'), # ACT 21:7
    ('sailors', 'mariners'), # EZE 27:9
    ('salvation', 'deliverance'), # JOB 13:16
    ('sanctified', 'consecrated'), # ISA 13:3
    ('sanctuary', 'holy'), # CH1 9:29
    ('sandals', 'sandal[s]'), # ISA 20:2
    ('sandals', 'shod'), # CH2 28:15
    ('sang', 'song'), # CH2 29:27
    ('sashes', 'belt'), # PRO 31:24
    ('satisfy', 'fill'), # PRO 6:30
    ('satisfy', 'satiety'), # PRO 13:25
    ('Save', 'deliver'), # PSA 22:20
    ('save', 'deliver'), # EZE 33:12
    ('save', 'delivered'), # ISA 36:19
    ('save', 'preserve'), # EZE 13:22
    ('save', 'redeemed'), # LAM 3:58
    ('save', 'redeems'), # PSA 103:4
    ('saved', 'delivered'), # EXO 14:30
    ('saved', 'redeemed'), # GAL 3:13
    ('saves', 'delivers'), # SA1 14:39
    ('saving', 'preserving'), # GEN 19:19
    ('saviour', 'deliverer'), # HOS 13:4
    ('saw', 'find'), # DEU 22:3
    ('saw', 'found'), # ACT 9:33
    ('saw', 'known'), # LUK 9:11
    ('saw', 'looked'), # REV 15:5
    ('saw', 'meet'), # JDG 15:14
    ('say', 'sayingms'), # ISA 57:14
    ('say', 'speak'), # HAB 2:1
    ('say', 'speaking'), # JHN 1:37
    ('say', 'spoke'), # JER 3:5
    ('saying', 'sayingms'), # DAN 2:20
    ('saying', 'speaking'), # CO1 9:10
    ('saying', 'spoke'), # JOB 2:13
    ('saying', 'utterances'), # PRO 4:20
    ('says', 'sayingms'), # PRO 26:18
    ('says', 'speak'), # DEU 18:19
    ('says', 'speaking'), # HEB 12:24
    ('says', 'told'), # MIC 2:11
    ('says', 'utterance'), # JER 8:13
    ('scale', 'scale[s]'), # ISA 46:6
    ('scales', 'balances'), # JOB 31:6
    ('scarlet', 'crimson'), # LAM 4:5
    ('scatter', 'disperse'), # EZE 5:10
    ('scatter', 'sprinkle'), # EZE 10:2
    ('scattered', 'dispersed'), # EZE 6:8
    ('scattered', 'sprinkled'), # CH2 34:4
    ('scent', 'odour'), # SNG 2:13
    ('scepter', 'staff'), # PSA 108:8
    ('schemes', 'plan[s]'), # JOB 18:7
    ('schemes', 'schemings'), # EPH 6:11
    ('scoff', 'derides'), # HAB 1:10
    ('scoffer', 'mocker'), # PRO 13:1
    ('scoffers', 'mockers'), # PRO 19:29
    ('scold', 'rebuke'), # LUK 17:3
    ('scold', 'rebuked'), # SA1 3:13
    ('scold', 'rebuking'), # JHN 8:46
    ('scolded', 'rebuke'), # MAT 19:13
    ('scolding', 'rebuke'), # PRO 29:15
    ('scolds', 'rebuke'), # JOB 26:11
    ('scorching', 'heat'), # ISA 11:15
    ('scorn', 'derision'), # PSA 44:13
    ('scorned', 'derision'), # PSA 79:4
    ('scorned', 'despise'), # LAM 1:8
    ('scorning', 'rejected'), # JDG 9:38
    ('scorns', 'despises'), # PRO 30:17
    ('screen', 'cover'), # EXO 40:3
    ('seams', 'leak[s]'), # EZE 27:9
    ('Search', 'seek'), # ISA 55:6
    ('search', 'sought'), # ISA 65:10
    ('searched', 'explored'), # JER 31:37
    ('searched', 'sought'), # EZE 22:30
    ('searches', 'seeking'), # MAT 7:8
    ('searches', 'seeks'), # PRO 31:13
    ('searching', 'seek'), # SA1 27:4
    ('searching', 'sought'), # SA2 17:20
    ('season', 'time'), # EZE 34:26
    ('seat', 'sit'), # KI1 21:9
    ('seat', 'throne'), # SA1 2:8
    ('seated', 'sat'), # ACT 12:21
    ('seated', 'sit'), # KI1 21:12
    ('seated', 'sitting'), # CO1 14:30
    ('secretaries', 'scribes'), # CH2 34:13
    ('secretary', 'scribe'), # KI2 25:19
    ('secretly', 'hide'), # PSA 64:5
    ('secretly', 'secrecy'), # DEU 27:15
    ('secure', 'confidence'), # JOB 18:14
    ('secure', 'securely'), # ACT 16:23
    ('secure', 'securities'), # ISA 32:18
    ('secure', 'security'), # EZE 30:9
    ('secure', 'trust'), # AMO 6:1
    ('secured', 'preserved'), # SA2 23:5
    ('securely', 'firm'), # SA2 22:34
    ('securely', 'security'), # EZE 34:28
    ('seditious', 'revolt'), # EZR 4:19
    ('seductive', 'seduction'), # EPH 4:22
    ('seductiveness', 'seduction'), # MAT 13:22
    ('see', 'finding'), # ACT 23:9
    ('see', 'know'), # EXO 2:4
    ('see', 'knowing'), # ACT 21:24
    ('see', 'look'), # EXO 1:16
    ('see', 'observe'), # JOB 34:29
    ('see', 'observing'), # JHN 6:62
    ('see', 'shown'), # KI2 8:13
    ('see', 'sight'), # JHN 9:11
    ('see', 'understanding'), # MAT 15:17
    ('seed', 'sown'), # MAT 13:18
    ('seeds', 'sowing'), # LUK 12:24
    ('seeds', 'sown'), # ISA 61:11
    ('seeing', 'known'), # GAL 2:9
    ('seeing', 'observed'), # LUK 23:48
    ('seen', 'appeared'), # SA2 22:11
    ('seen', 'found'), # REV 16:20
    ('seen', 'known'), # PSA 77:19
    ('seen', 'observing'), # JHN 9:8
    ('sees', 'looks'), # PSA 64:8
    ('sees', 'observing'), # JHN 10:12
    ('seize', 'capture'), # ACT 12:3
    ('seized', 'captured'), # KI1 9:16
    ('seized', 'took'), # SA2 10:4
    ('select', 'chosen'), # ACT 15:25
    ('select', 'take'), # EXO 12:21
    ('selected', 'chosen'), # MAT 22:14
    ('selected', 'taken'), # SA1 10:20
    ('self-centred', 'self-willed'), # TIT 1:7
    ('seller', 'sells'), # EZE 7:12
    ('sensitive', 'delicate'), # DEU 28:54
    ('sent', 'dismissals'), # EXO 18:2
    ('sentence', 'condemning'), # MRK 10:33
    ('separate', 'apart'), # CO2 6:17
    ('separated', 'apart'), # LEV 22:16
    ('separately', 'separated'), # NEH 9:2
    ('separately', 'separateness'), # KI2 15:5
    ('separation', 'consecration'), # NUM 6:4
    ('separation', 'separating'), # ISA 59:2
    ('serious', 'sober'), # PE1 4:7
    ('serpent', 'snake'), # AMO 9:3
    ('servant', 'maids'), # PRO 27:27
    ('servant', 'maidservant'), # KI1 1:17
    ('servant', 'subject'), # KI2 17:3
    ('servants', 'subjects'), # CH1 21:3
    ('serve', 'minister'), # ROM 15:16
    ('serve', 'ministering'), # LUK 1:8
    ('serve', 'service'), # EZR 6:18
    ('served', 'attended'), # ACT 13:36
    ('served', 'ministering'), # DAN 7:10
    ('served', 'service'), # ACT 20:24
    ('service', 'served'), # CO2 8:19
    ('Serving', 'service'), # CO2 9:12
    ('serving', 'service'), # CO1 16:15
    ('set', 'arranged'), # JOB 6:4
    ('set', 'determined'), # ACT 28:23
    ('set', 'prepared'), # EST 7:10
    ('set', 'put'), # EZE 30:8
    ('set', 'ready'), # ACT 23:21
    ('setting', 'arranging'), # ISA 21:5
    ('Settle', 'dwell'), # PSA 37:3
    ('settle', 'decide'), # ISA 2:4
    ('settle', 'dwell'), # GEN 35:1
    ('settle', 'encamp'), # NAH 3:17
    ('settle', 'rest'), # ISA 14:1
    ('settled', 'dwell'), # KI2 17:6
    ('settled', 'dwelling'), # JDG 10:1
    ('settled', 'encamped'), # NEH 11:30
    ('shackled', 'shackle[s]'), # PSA 105:18
    ('shade', 'shadow'), # EZE 17:23
    ('shadow', 'shade'), # SNG 2:3
    ('shadowed', 'overshadowing'), # MRK 9:7
    ('shaggy', 'hairy'), # DAN 8:21
    ('shake', 'quake'), # EZE 27:28
    ('shame', 'disgrace'), # EZE 44:13
    ('shame', 'ignominy'), # PSA 69:7
    ('shameful', 'disgraceful'), # JER 29:23
    ('shameful', 'ignominy'), # PRO 18:13
    ('shameful', 'shame'), # CO2 4:2
    ('shameful', 'shamefully'), # PRO 17:2
    ('Share', 'portion'), # ECC 11:2
    ('share', 'part'), # JOB 32:17
    ('share', 'portion'), # PSA 68:23
    ('sharp', 'sharpened'), # ISA 5:28
    ('sharper', 'sharp'), # PRO 5:4
    ('shattered', 'broke'), # KI2 18:4
    ('shearing', 'shearers'), # GEN 38:12
    ('sheep', 'flock'), # CH1 17:7
    ('sheep', 'flock[s]'), # GEN 47:17
    ('sheep', 'flocks'), # ISA 17:2
    ('sheep', 'lambs'), # JOB 31:20
    ('sheep', 'ram'), # LEV 7:23
    ('sheep', 'rams'), # LEV 22:19
    ('shekels', 'shekel[s]'), # GEN 23:15
    ('shepherds', 'sheep-tenders'), # AMO 1:1
    ('shining', 'brightness'), # JOL 2:10
    ('shock', 'appalled'), # EZE 32:10
    ('shocked', 'appalled'), # PSA 40:15
    ('shook', 'stirred'), # SA1 4:5
    ('shoot', 'shooters'), # GEN 21:16
    ('shore', 'land'), # JHN 21:8
    ('short', 'shortened'), # CO1 7:29
    ('shortage', 'famine'), # KI1 18:2
    ('shoulder', 'arm'), # DEU 18:3
    ('shoulder', 'arms'), # KI2 9:24
    ('Shout', 'call'), # ISA 58:1
    ('shout', 'cry'), # JOB 20:5
    ('shout', 'cry out'), # JER 47:2
    ('shouted', 'called'), # CH2 32:18
    ('shouted', 'cried out'), # JHN 11:43
    ('shouted', 'crying'), # ACT 12:22
    ('shouted', 'crying out'), # ACT 12:22
    ('shouting', 'cry'), # ECC 9:17
    ('shouting', 'crying'), # ACT 21:34
    ('shouting', 'crying out'), # ACT 21:34
    ('shouts', 'cry'), # JER 48:34
    ('shouts', 'shoutings'), # ZEC 4:7
    ('show', 'present'), # KI1 18:1
    ('show', 'reveal'), # ISA 49:9
    ('shown', 'revealed'), # PE1 1:12
    ('shows', 'revealed'), # CO2 3:3
    ('shut', 'closed'), # GEN 7:16
    ('sick', 'sickness'), # ISA 1:5
    ('siege', 'siege-work'), # EZE 17:17
    ('sight', 'eyes'), # AMO 9:3
    ('signal', 'standard'), # ISA 11:10
    ('signature', 'mark'), # JOB 31:35
    ('signet', 'signet-ring'), # EST 3:10
    ('silence', 'silent'), # ACT 15:12
    ('silenced', 'silent'), # JER 47:5
    ('silent', 'silence'), # JOB 11:3
    ('silently', 'silent'), # EZE 24:17
    ('silver-plated', 'silver'), # ISA 30:22
    ('similar', 'like'), # EZE 42:12
    ('simple', 'naive'), # PRO 19:25
    ('simple-minded', 'simple'), # JOB 5:2
    ('sincere', 'sincerity'), # EPH 6:5
    ('sincerely', 'sincere'), # PE2 3:1
    ('sincerely', 'sincerity'), # COL 3:22
    ('sing', 'songs'), # PSA 69:12
    ('singing', 'song'), # CH2 23:18
    ('Single', 'unmarried'), # CO1 7:32
    ('sit', 'dwell'), # MIC 4:4
    ('sits', 'dwelling'), # ZEC 1:11
    ('sits', 'dwells'), # LAM 1:3
    ('sitting', 'dwelling'), # KI2 6:1
    ('situation', 'matter'), # SA2 14:20
    ('skies', 'heaven'), # ZEC 12:1
    ('skilled', 'skill'), # CH1 28:21
    ('skilled', 'skillful'), # CH1 22:15
    ('skillfully', 'skill'), # HOS 13:2
    ('skull', 'crown'), # PSA 7:16
    ('sky', 'heavens'), # DEU 28:23
    ('slack', 'slackness'), # JER 48:10
    ('slain', 'killed'), # LAM 2:4
    ('slander', 'slanderous'), # PE2 2:11
    ('slanderer', 'slanderous'), # TI1 1:13
    ('slap', 'struck'), # JOB 16:10
    ('slapped', 'struck'), # KI1 22:24
    ('slaps', 'striking'), # LUK 6:29
    ('slaughter', 'kill'), # ZEC 11:5
    ('slaughtered', 'killed'), # GEN 34:25
    ('slaughterhouse', 'slaughter'), # ACT 8:32
    ('slave', 'maid'), # EXO 2:5
    ('slave', 'maidservant'), # GEN 16:2
    ('slave', 'maidservants'), # GEN 33:2
    ('slavery', 'servitude'), # NEH 9:17
    ('slavery', 'slaves'), # DEU 6:12
    ('slaves', 'enslaved'), # ROM 6:18
    ('slaves', 'maidservants'), # GEN 33:1
    ('sledge', 'threshing-sledge'), # ISA 41:15
    ('sledges', 'threshing-sledges'), # CH1 21:23
    ('sleep', 'lie down'), # DEU 24:13
    ('slept', 'lay down'), # KI1 21:27
    ('slingshots', 'slings'), # CH2 26:14
    ('slumped', 'sank'), # KI2 9:24
    ('small', 'fewness'), # DAN 11:23
    ('small', 'smaller'), # MAT 13:32
    ('small', 'smallsg'), # SA1 30:19
    ('smaller', 'few'), # NUM 35:8
    ('smaller', 'small'), # DEU 25:14
    ('smaller', 'smallsg'), # GEN 1:16
    ('smallest', 'small'), # SA1 9:21
    ('smallish', 'small'), # CH2 24:24
    ('smash', 'break'), # LEV 26:19
    ('smash', 'struck'), # PSA 74:6
    ('smashed', 'broke'), # KI2 23:14
    ('smashed', 'broken'), # LEV 11:35
    ('smashed', 'dashed'), # ISA 13:16
    ('smashed', 'strike'), # AMO 6:11
    ('smashing', 'break'), # JER 43:13
    ('smashing', 'breaking'), # ISA 30:13
    ('smearers', 'smear'), # JOB 13:4
    ('smell', 'odour'), # SNG 4:10
    ('smile', 'cheerful'), # JOB 9:27
    ('smooth', 'seductiveness'), # PRO 7:21
    ('smooth', 'smoothness'), # PRO 6:24
    ('smooth-skinned', 'smooth'), # ISA 18:2
    ('smoother', 'smooth'), # PRO 5:3
    ('smoothly', 'smoothnesses'), # PRO 23:31
    ('snake', 'serpent'), # EXO 7:9
    ('snakes', 'serpents'), # EXO 7:12
    ('snare-traps', 'snare'), # ISA 24:17
    ('snared', 'ensnared'), # ISA 8:15
    ('snares', 'traps'), # PSA 38:12
    ('snatched', 'seized'), # SA2 23:21
    ('sneakily', 'sneaking'), # PE2 2:1
    ('snowy', 'snow'), # CH1 11:22
    ('soil', 'ground'), # JOL 1:10
    ('soldiers', 'soldier/messenger'), # CH2 18:18
    ('soldiers', 'soldier[s]'), # KI1 20:29
    ('son', 'child'), # ECC 12:12
    ('sons', 'children'), # GEN 22:20
    ('sorcerer', 'magician'), # ACT 13:8
    ('sorcery', 'sorcerer'), # DEU 18:10
    ('sorcery', 'sorcerers'), # MAL 3:5
    ('sorry', 'compassion'), # EXO 2:6
    ('soul', 'life'), # PRO 25:13
    ('soul', 'self'), # GEN 42:21
    ('sound', 'voice'), # EZE 33:32
    ('south', 'southward'), # CH1 9:24
    ('southern', 'south'), # CH1 26:15
    ('southern', 'southward'), # EZE 48:10
    ('southward', 'south'), # JOS 12:3
    ('spacious', 'broad'), # JDG 18:10
    ('spare', 'forgive'), # GEN 18:26
    ('spared', 'compassion'), # SA2 21:7
    ('spared', 'saved'), # ROM 5:9
    ('sparing', 'compassion'), # SA1 15:9
    ('speak', 'mouth'), # EZE 29:21
    ('speak', 'words/messages'), # JOB 32:4
    ('spears', 'spear[s]'), # PSA 46:9
    ('spears', 'spearmen'), # ACT 23:23
    ('specifications', 'measurement'), # CH2 24:13
    ('specifications', 'plans'), # KI1 6:38
    ('speech', 'lips'), # PRO 19:1
    ('spend', 'pass'), # SA2 17:8
    ('spends', 'passes'), # JOB 39:28
    ('spent', 'passed'), # SA2 12:16
    ('spent', 'stayed'), # GEN 31:54
    ('spiced', 'spice'), # SNG 8:2
    ('spices', 'seasoning'), # EZE 24:10
    ('spices', 'spiced'), # PSA 75:8
    ('Spirit', 'breath/wind/spirit'), # GEN 6:3
    ('spirit', 'breath'), # JOB 26:4
    ('spirit', 'breath/wind/spirit'), # DAN 2:3
    ('spirits', 'breath/wind/spirit'), # EZR 1:5
    ('spiritual', 'spirit'), # CO1 14:2
    ('spiritual', 'spirits'), # CO1 14:12
    ('spiritual', 'spiritually'), # REV 11:8
    ('spiritually', 'spirit'), # PE1 4:6
    ('splash', 'sprinkle'), # LEV 1:5
    ('splashed', 'sprinkle'), # LEV 7:2
    ('splashed', 'sprinkled'), # LEV 8:19
    ('splashes', 'sprinkles'), # LEV 7:14
    ('splattered', 'spattered'), # ISA 63:3
    ('splendid', 'splendour'), # EZE 26:20
    ('splendour', 'adornment'), # CH2 20:21
    ('splendour', 'luster'), # PSA 89:44
    ('splendour', 'splendid'), # JOB 31:26
    ('split', 'divided'), # GEN 2:10
    ('splits', 'cleaves'), # ECC 10:9
    ('spoil', 'plunder'), # KI2 3:23
    ('spoil', 'plunders'), # HAB 2:7
    ('spoke', 'mouth'), # JOB 3:1
    ('spoke', 'words/messages'), # JER 48:27
    ('spoken', 'words/messages'), # KI1 1:7
    ('sport', 'laughter'), # PRO 10:23
    ('spot', 'place'), # PSA 55:8
    ('spread', 'opened'), # EZE 16:25
    ('spread', 'scatter'), # PRO 15:7
    ('spread', 'scattered'), # GEN 10:18
    ('springs', 'sprouts'), # HOS 10:4
    ('sprinkle', 'spatter'), # EXO 29:21
    ('squirm', 'writhing'), # JOB 15:20
    ('staff', 'rod'), # JDG 5:14
    ('stagger', 'wander'), # JOB 12:25
    ('stained', 'soiled'), # REV 3:4
    ('stairs', 'steps'), # NEH 3:15
    ('stand', 'endure'), # DAN 2:44
    ('standing', 'standing-place'), # JOS 4:3
    ('start', 'beginning'), # LUK 13:26
    ('started', 'begun'), # ACT 8:35
    ('starting', 'begun'), # LUK 24:27
    ('starts', 'begin'), # MAT 24:49
    ('stated', 'said'), # NUM 13:30
    ('stationed', 'placed'), # CH2 1:14
    ('stations', 'place'), # CH2 30:16
    ('stations', 'seating'), # CH2 9:4
    ('statue', 'image'), # DAN 2:34
    ('statute', 'regulation'), # EXO 12:14
    ('statutes', 'regulations'), # EXO 18:16
    ('Stay', 'dwell'), # KI2 25:24
    ('Stay', 'remain'), # GEN 22:5
    ('stay', 'continuing'), # TI1 4:16
    ('stay', 'delay'), # JOS 10:19
    ('stay', 'dwell'), # JDG 17:11
    ('stay', 'remain'), # CH2 25:19
    ('stay', 'remained'), # ACT 21:7
    ('stay', 'remaining'), # CO1 16:8
    ('stay', 'sojourn'), # JDG 17:9
    ('stay', 'sojourned'), # GEN 21:34
    ('stayed', 'dwell'), # PSA 139:9
    ('stayed', 'dwelt'), # GEN 25:27
    ('stayed', 'remained'), # ACT 17:14
    ('stayed', 'remaining'), # CH1 20:1
    ('stayed', 'sojourning'), # SA2 4:3
    ('staying', 'remaining'), # CH2 32:10
    ('staying', 'sojourned'), # EXO 6:4
    ('staying', 'sojourning'), # JDG 17:7
    ('stays', 'dwells'), # PSA 91:1
    ('stays', 'remaining'), # HEB 7:24
    ('stays', 'remains'), # JER 21:9
    ('steady', 'permanence'), # GEN 49:24
    ('steady', 'steadiness'), # EXO 17:12
    ('stealing', 'thefts'), # MAT 15:19
    ('steep', 'descent'), # MIC 1:4
    ('steps', 'step[s]'), # PRO 16:9
    ('stick', 'clinging'), # DAN 2:43
    ('stick', 'firewood'), # AMO 4:11
    ('stick', 'staves'), # SA1 17:43
    ('stick', 'wood'), # EZE 37:17
    ('sticks', 'cleaved'), # LAM 4:4
    ('sticks', 'clinging'), # PRO 18:24
    ('stillborn', 'miscarriage'), # ECC 6:3
    ('stingers', 'stings'), # REV 9:10
    ('stir', 'raise'), # HAB 1:6
    ('stirred', 'aroused'), # PSA 45:1
    ('stocks', 'stock[s]'), # JER 20:2
    ('stomach', 'belly'), # PRO 13:25
    ('stomachs', 'belly'), # JOB 20:15
    ('stone-workers', 'stonemasons'), # CH2 24:12
    ('stones', 'rock[s]'), # JOB 22:24
    ('stones', 'stone[s]'), # ISA 62:10
    ('stony', 'rocky'), # MAT 13:5
    ('Stop', 'cease'), # ISA 1:16
    ('stop', 'cease'), # EZE 16:41
    ('stop', 'ceasing'), # ACT 6:13
    ('stop', 'restrain'), # NUM 11:28
    ('stop', 'restrained'), # JOB 29:9
    ('stopped', 'cease'), # JDG 9:9
    ('stopped', 'ceased'), # KI1 15:21
    ('stopped', 'ceasing'), # ACT 5:42
    ('stopped', 'restrained'), # CH1 21:22
    ('stops', 'cease'), # SA1 9:5
    ('stops', 'ceased'), # PE1 4:1
    ('storage', 'stores'), # CH2 8:4
    ('store', 'deposit'), # DEU 14:28
    ('store', 'heap'), # GEN 41:35
    ('stored', 'heaped'), # GEN 41:49
    ('storehouse', 'stores'), # KI1 9:19
    ('storehouses', 'stores'), # CH1 26:15
    ('storehouses', 'supplies'), # CH2 11:11
    ('storeroom', 'store'), # MAL 3:10
    ('storeroom', 'storehouse'), # JER 38:11
    ('storerooms', 'store-room'), # NEH 13:4
    ('storerooms', 'store-rooms'), # NEH 13:9
    ('storerooms', 'stores'), # NEH 12:44
    ('storm', 'rainstorm'), # ISA 4:6
    ('storm', 'storm-tossed'), # ISA 54:11
    ('storm', 'storm-wind'), # ISA 17:13
    ('stormy', 'storm'), # PSA 148:8
    ('stragglers', 'straggling'), # DEU 25:18
    ('straight', 'straighten'), # LUK 13:11
    ('straight-talking', 'straight'), # TI2 2:15
    ('straighten', 'straight'), # ECC 7:13
    ('straightened', 'straight'), # ECC 1:15
    ('straightening', 'straight'), # SA1 13:21
    ('straightforward', 'straightforwardness'), # ISA 57:2
    ('strangers', 'sojourner'), # PSA 94:6
    ('strangers', 'sojourning'), # CH1 16:19
    ('strapped', 'girded'), # SA1 17:39
    ('straw', 'chaff'), # ISA 40:24
    ('streaked', 'striped'), # GEN 30:35
    ('stream', 'wadi'), # AMO 5:24
    ('strength', 'firmness'), # DAN 2:41
    ('strength', 'power'), # DAN 11:17
    ('strength', 'strengthened'), # ACT 9:19
    ('strength', 'strengthening'), # CH2 26:16
    ('strengthen', 'gird'), # ISA 45:5
    ('strengthen', 'strength'), # ISA 51:9
    ('strengthen', 'strong'), # EZE 30:24
    ('strengthens', 'strong'), # CH2 16:9
    ('stretch', 'spread'), # CH2 6:29
    ('stretched', 'spread'), # JOB 11:13
    ('stretched', 'spreading'), # KI1 8:7
    ('strike', 'assailant'), # JOB 36:32
    ('strike', 'attack'), # SA2 5:24
    ('strike', 'attacks'), # SA2 5:8
    ('strike', 'defeat'), # JDG 6:16
    ('strikes', 'attacks'), # CH1 11:6
    ('strikes', 'slaps'), # JOB 34:26
    ('strikes', 'smashes'), # JOB 5:18
    ('strive', 'contend'), # ROM 15:30
    ('Strong', 'mighty'), # PSA 22:12
    ('strong', 'mighty'), # PSA 19:5
    ('strong', 'strength'), # DAN 11:2
    ('strong', 'vigorous'), # GEN 30:41
    ('stronger', 'hard'), # JDG 4:24
    ('stronger', 'mighty'), # ECC 6:10
    ('stronger', 'strong'), # CH1 5:2
    ('stronghold', 'refuge'), # JDG 6:26
    ('strongholds', 'strength'), # AMO 3:11
    ('strongly', 'strong'), # EZR 10:4
    ('strongly-worded', 'strong'), # CO2 10:10
    ('strove', 'contended'), # DEU 33:8
    ('struck', 'attacked'), # CH1 4:41
    ('struck', 'defeat'), # ISA 10:26
    ('struck', 'defeated'), # CH1 4:43
    ('struck', 'fell'), # KI1 2:25
    ('struck', 'touched'), # JDG 20:41
    ('stubborn', 'hard'), # EZE 2:4
    ('stubborn', 'stubbornness'), # JER 3:17
    ('stubbornly', 'stubborn'), # ZEC 7:11
    ('stubbornly', 'stubbornness'), # JER 11:8
    ('study', 'insight'), # NEH 8:13
    ('stump', 'rootstock'), # ISA 11:1
    ('stunned', 'astonished'), # MRK 10:26
    ('stupidity', 'foolishness'), # PRO 5:23
    ('subdue', 'tame'), # MRK 5:4
    ('subdued', 'humbled'), # CH2 13:18
    ('subject', 'served'), # GEN 14:4
    ('submissively', 'submission'), # TI1 2:11
    ('submit', 'bow'), # PSA 45:11
    ('submit', 'submission'), # GAL 2:5
    ('succeed', 'prosper'), # EZE 17:15
    ('succeed', 'success'), # ECC 10:10
    ('succeed', 'successful'), # CH1 22:13
    ('succeeded', 'successful'), # CH2 7:11
    ('succeeding', 'successful'), # SA1 18:14
    ('success', 'succeed'), # JDG 18:5
    ('successes', 'successful'), # SA1 18:15
    ('successful', 'prosper'), # CH2 26:5
    ('successful', 'succeed'), # DAN 11:36
    ('successful', 'success'), # JER 5:28
    ('suckle', 'suck'), # ISA 66:12
    ('suckling', 'sucking'), # JOL 2:16
    ('sudden', 'suddenly'), # JOB 9:23
    ('suddenly', 'sudden'), # TH1 5:3
    ('suddenly', 'suddenness'), # HAB 2:7
    ('suffer', 'bear'), # NUM 14:33
    ('suffer', 'grieved'), # LAM 1:5
    ('suffer', 'sufferings'), # PE1 1:11
    ('suffered', 'sufferings'), # HEB 2:10
    ('suffering', 'pain'), # JOB 2:13
    ('sufferings', 'pains'), # JOB 9:28
    ('summit', 'top'), # SA2 15:32
    ('summoned', 'call'), # EXO 10:16
    ('summoned', 'called'), # SA1 10:17
    ('Summoning', 'calls'), # ISA 46:11
    ('supervisor', 'overseer'), # JER 20:1
    ('supervisors', 'overseers'), # CH2 34:12
    ('support', 'help'), # CH2 26:13
    ('support', 'helped'), # KI1 1:7
    ('support', 'minister'), # ROM 15:27
    ('supported', 'help'), # JOB 31:21
    ('supported', 'stand'), # CH2 11:13
    ('surging', 'swelling'), # PSA 46:3
    ('Surround', 'around'), # JER 50:29
    ('surround', 'around'), # AMO 3:11
    ('surround', 'surroundings'), # PSA 140:9
    ('surrounded', 'around'), # CH2 21:9
    ('Surrounding', 'around'), # REV 4:4
    ('surrounding', 'around'), # JOS 21:11
    ('surrounds', 'around'), # PSA 89:8
    ('survive', 'endure'), # JOL 2:11
    ('survive', 'live'), # NUM 24:23
    ('survive', 'survivor'), # JOB 20:26
    ('survived', 'survivor'), # LAM 2:22
    ('surviving', 'remains'), # KI2 19:30
    ('survivor', 'survivor[s]'), # JDG 5:13
    ('survivors', 'escaped'), # EZR 9:14
    ('survivors', 'escapees'), # JER 44:28
    ('survivors', 'survivor[s]'), # ISA 1:9
    ('sweet', 'sweetnesses'), # SNG 5:16
    ('sweeter', 'sweet'), # JDG 14:18
    ('sweetness', 'sweet'), # JDG 14:14
    ('swept', 'dragging'), # REV 12:4
    ('swifter', 'swift'), # SA2 1:23
    ('swindlers', 'swindling'), # CO1 5:10
    ('swoop', 'fly'), # ISA 11:14
    ('swordsmen', 'sword'), # JDG 20:25
    ('Take', 'bring'), # DAN 2:24
    ('take', 'accepted'), # ZEP 3:2
    ('take', 'bring'), # GEN 27:10
    ('take', 'bringing'), # MRK 13:11
    ('take', 'carry'), # KI1 18:12
    ('take', 'conduct'), # PRO 22:23
    ('take', 'consider'), # PSA 107:43
    ('take', 'remove'), # EXO 10:17
    ('take', 'snatch'), # PSA 40:14
    ('taken', 'brought'), # ACT 21:34
    ('taken', 'carry'), # MAL 2:3
    ('taken', 'consumed'), # ISA 3:14
    ('taken', 'remove'), # JOB 34:20
    ('taken', 'removed'), # DEU 26:13
    ('taken', 'seize'), # JOB 30:16
    ('Taking', 'removes'), # PRO 25:20
    ('taking', 'bringing'), # LUK 24:1
    ('taking', 'brought'), # CH2 29:21
    ('taking', 'choosing'), # SA1 20:30
    ('talk', 'preach'), # ROM 1:15
    ('talk', 'speak'), # DEU 6:7
    ('talk', 'speaking'), # EPH 5:12
    ('talked', 'speaking'), # ZEC 1:13
    ('talked', 'spoke'), # GEN 45:15
    ('talking', 'spoke'), # MAT 16:11
    ('talking', 'spoken'), # EXO 34:29
    ('tall', 'high'), # EZE 16:39
    ('taller', 'tall'), # SA1 10:23
    ('tassel', 'tassel[s]'), # NUM 15:39
    ('taste', 'palate'), # PSA 119:103
    ('tastes', 'palate'), # PRO 24:13
    ('tasty', 'delicious'), # GEN 27:17
    ('taught', 'instructed'), # PRO 31:1
    ('teach', 'instruct'), # JOB 27:11
    ('teacher', 'teaches'), # HAB 2:18
    ('teacher', 'teaching'), # TI1 3:2
    ('teaches', 'instructing'), # TIT 2:12
    ('teaching', 'instruct'), # JOB 34:32
    ('teaching', 'instruction'), # PRO 6:23
    ('tear', 'break'), # ECC 3:3
    ('tear', 'pull'), # DEU 12:3
    ('tears', 'breaks'), # PRO 29:4
    ('tears', 'tear[s]'), # KI2 20:5
    ('tears', 'weeping'), # PSA 102:9
    ('tears', 'wept'), # JHN 11:35
    ('Tell', 'proclaim'), # DEU 32:3
    ('Tell', 'said'), # ACT 12:17
    ('Tell', 'say'), # JER 7:28
    ('tell', 'proclaim'), # PE1 2:9
    ('tell', 'recount'), # JER 51:10
    ('tell', 'recounted'), # PSA 22:30
    ('tell', 'said'), # JOB 21:14
    ('tell', 'say'), # DEU 5:30
    ('tell', 'sayingms'), # DEU 20:3
    ('tell', 'says'), # PSA 10:6
    ('tell', 'speak'), # EZE 17:2
    ('tell', 'speaks'), # JOB 9:7
    ('tell', 'spoke'), # KI1 4:32
    ('telling', 'proclaiming'), # ACT 28:31
    ('telling', 'said'), # EXO 24:8
    ('telling', 'say'), # HAG 1:1
    ('telling', 'says'), # ISA 52:7
    ('telling', 'speak'), # DEU 32:45
    ('telling', 'spoke'), # CH2 32:19
    ('telling', 'spoken'), # ISA 1:20
    ('tells', 'said'), # JOB 36:10
    ('tells', 'saying'), # ACT 20:23
    ('tells', 'says'), # ISA 41:13
    ('temple', 'house'), # EZE 9:3
    ('temples', 'house'), # KI1 12:31
    ('temples', 'houses'), # JER 43:12
    ('tempt', 'temptation'), # REV 2:14
    ('tempted', 'temptation'), # LUK 11:4
    ('tempting', 'temptation'), # MAT 16:23
    ('tempting', 'temptations'), # ROM 16:17
    ('tent', 'sanctuary'), # JOS 24:26
    ('tents', 'dwellings'), # EZE 25:4
    ('terrible', 'severe'), # JER 21:5
    ('terrified', 'frightened'), # REV 11:13
    ('terrify', 'terror'), # EZE 32:32
    ('terrifying', 'terrible'), # DAN 2:31
    ('terrifying', 'terror'), # DEU 34:12
    ('terrifying', 'terrors'), # PSA 88:16
    ('territories', 'region'), # GEN 14:7
    ('territory', 'region'), # SA1 6:1
    ('terror', 'dread'), # PSA 91:5
    ('terrorized', 'terror'), # EZE 23:46
    ('terrors', 'dreads'), # JOB 15:21
    ('testified', 'warned'), # NEH 9:26
    ('testify', 'testimony'), # CO2 1:12
    ('testify', 'warn'), # AMO 3:13
    ('testimony', 'testified'), # JHN 5:33
    ('testimony', 'testifies'), # PRO 25:18
    ('testing', 'trial'), # HEB 3:8
    ('thank', 'give thanks'), # CH1 16:4
    ('thank', 'gives thanks'), # ISA 38:18
    ('thank', 'giving thanks'), # CO1 1:14
    ('thank', 'thank-offering'), # JER 17:26
    ('thank', 'thank-offerings'), # PSA 56:12
    ('thank', 'thanksgiving'), # CH2 33:16
    ('thanked', 'give thanks'), # CH1 25:3
    ('thanked', 'giving thanks'), # ACT 28:15
    ('thanked', 'thankfulness'), # CO2 8:16
    ('thankful', 'thankfulness'), # CO1 15:57
    ('thankful', 'thanks'), # ROM 16:4
    ('thankful', 'thanksgiving'), # COL 2:7
    ('thankfulness', 'thanksgiving'), # EPH 5:4
    ('thanking', 'giving thanks'), # CH1 29:13
    ('thanking', 'thanksgiving'), # PHP 4:6
    ('thanks', 'giving thanks'), # EPH 5:20
    ('thanks', 'thanksgiving'), # CO2 9:11
    ('thanks', 'thanksgivings'), # CO2 9:12
    ('thanksgiving', 'gave thanks'), # NEH 11:17
    ('thanksgiving', 'give thanks'), # CH2 31:2
    ('thanksgiving', 'thank-offering'), # AMO 4:5
    ('thanksgiving', 'thanks'), # NEH 11:17
    ('thick', 'thickness'), # CH2 4:5
    ('thicker', 'thick'), # CH2 10:10
    ('thickets', 'thicket[s]'), # JER 50:44
    ('thighs', 'loins'), # DAN 2:32
    ('Think', 'consider'), # PRO 6:6
    ('think', 'considers'), # JOB 41:32
    ('think', 'intended'), # ISA 10:7
    ('think', 'remember'), # EZE 36:31
    ('think', 'remembered'), # PSA 63:6
    ('think', 'supposing'), # CO1 10:12
    ('thinking', 'suppose'), # JHN 16:2
    ('thinking', 'thoughts'), # JOB 21:27
    ('thinks', 'considers'), # PRO 15:28
    ('thinks', 'supposing'), # CO1 3:18
    ('thirst', 'thirsty'), # JOB 24:11
    ('thirsts', 'thirsty'), # PSA 42:2
    ('thirsty', 'thirst'), # ISA 5:13
    ('thirsty', 'thirsted'), # MAT 25:35
    ('thirsty', 'thirsting'), # CO1 4:11
    ('thorn', 'thorn[s]'), # ISA 27:4
    ('Thornbushes', 'thornbush[es]'), # HOS 9:6
    ('thornbushes', 'thornbush[es]'), # JOB 31:40
    ('thornbushes', 'thorns'), # JER 4:3
    ('thorns', 'pricks'), # JOS 23:13
    ('thorns', 'thorn[s]'), # ISA 5:6
    ('thorns', 'thornbush'), # PRO 26:9
    ('thorns', 'thornbushes'), # SNG 2:2
    ('thorns', 'thorny'), # MRK 15:17
    ('thorough', 'thoroughly'), # JER 6:29
    ('thought', 'considered'), # ISA 53:4
    ('thought', 'remembered'), # EZE 16:22
    ('thought', 'supposed'), # ACT 26:9
    ('thoughts', 'plans'), # PSA 40:5
    ('threaten', 'threat'), # EPH 6:9
    ('threats', 'threatened'), # ACT 4:21
    ('three-stranded', 'threefold'), # ECC 4:12
    ('threshhold', 'threshold'), # SA1 5:4
    ('threw', 'hurled'), # JNA 1:5
    ('thrive', 'prosper'), # EZE 17:10
    ('throw', 'hurl'), # JNA 1:12
    ('thrown', 'thrust'), # ISA 49:21
    ('thunderbolts', 'thunder'), # JOB 38:25
    ('thundercloud', 'thunder'), # PSA 81:7
    ('thunderous', 'thunder'), # PSA 77:18
    ('thunderous', 'thunders'), # REV 4:5
    ('thunderstorms', 'thunder-clouds'), # ZEC 10:1
    ('Tie', 'bind'), # ISA 8:16
    ('Tie', 'bound'), # MAT 22:13
    ('tie', 'bind'), # EXO 28:28
    ('tie', 'bound'), # JDG 16:6
    ('timber', 'wood'), # HAG 1:8
    ('timber', 'woods'), # CH1 22:14
    ('tired', 'wearied'), # JHN 4:6
    ('tired', 'weary'), # ISA 43:22
    ('told', 'proclaimed'), # LAM 1:15
    ('told', 'proclaiming'), # ROM 10:14
    ('told', 'recounted'), # GEN 29:13
    ('told', 'say'), # KI1 18:31
    ('told', 'speak'), # HEB 3:5
    ('told', 'speaking'), # JNA 3:2
    ('told', 'spoke'), # ACT 7:6
    ('told', 'spoken'), # ACT 9:6
    ('tolerate', 'allowing'), # REV 2:20
    ('tolerate', 'bear'), # REV 2:2
    ('tolerate', 'stand'), # EST 3:4
    ('tomb', 'grave'), # KI2 9:28
    ('tomb', 'graves'), # CH2 16:14
    ('tombs', 'chambers'), # SA1 13:6
    ('tombs', 'graves'), # CH2 21:20
    ('tongue-shaped', 'tongue'), # JOS 7:21
    ('took', 'bring'), # EXO 12:42
    ('took', 'brought'), # ACT 17:15
    ('took', 'carried'), # SA2 5:21
    ('took', 'led'), # EZE 43:1
    ('took', 'removed'), # SA1 17:39
    ('took', 'seized'), # PSA 48:6
    ('top', 'crown'), # JER 48:45
    ('tore', 'pulled'), # CH2 34:7
    ('tormented', 'grieve'), # JOB 19:2
    ('tormented', 'terrified'), # SA1 16:14
    ('tormenting', 'terrifying'), # SA1 16:15
    ('torn', 'broken'), # NEH 1:3
    ('torn', 'plucked'), # DAN 7:4
    ('torn', 'pulled'), # CH2 33:3
    ('torn', 'split'), # JOB 26:8
    ('torrents', 'overflowings'), # JOB 14:19
    ('torture', 'torment'), # LUK 8:28
    ('toss', 'threw'), # EXO 15:7
    ('toss', 'throw'), # EXO 1:22
    ('toss', 'throwing'), # LUK 12:58
    ('toss', 'thrown'), # PSA 50:17
    ('toss', 'winnow'), # ISA 41:16
    ('tossed', 'thrown'), # ISA 34:3
    ('touch', 'reaches'), # JOB 4:5
    ('toward', 'towards'), # GEN 12:9
    ('towered', 'lofty'), # EZE 19:11
    ('town', 'cities'), # ACT 8:40
    ('towns', 'cities'), # DEU 2:37
    ('towns', 'city'), # LUK 8:1
    ('traded', 'exchanged'), # PSA 106:20
    ('trading', 'exchange'), # JOB 20:18
    ('train', 'learn'), # MIC 4:3
    ('trained', 'learned'), # JHN 7:15
    ('trample', 'tread'), # DAN 7:23
    ('trampled', 'trodden'), # ISA 63:18
    ('trampling', 'treading'), # REV 19:15
    ('transgresses', 'sin'), # LEV 4:27
    ('transgressors', 'rebels'), # DAN 8:23
    ('translate', 'interpreting'), # CO1 14:5
    ('translate', 'translation'), # CO1 12:10
    ('translating', 'interpreting'), # CO1 12:30
    ('translator', 'interpreter'), # CO1 14:28
    ('trap', 'snare'), # JER 48:44
    ('trapped', 'ensnared'), # DEU 7:25
    ('traps', 'snare'), # JER 48:43
    ('traps', 'snares'), # PRO 13:14
    ('travel', 'go'), # PSA 104:26
    ('travel', 'going'), # MAT 23:15
    ('travel', 'pass'), # DEU 2:18
    ('travel', 'went'), # CH2 15:5
    ('travelled', 'passed'), # ACT 16:6
    ('travelled', 'went'), # CH1 17:6
    ('travellers', 'walkers'), # JDG 5:6
    ('travelling', 'pass'), # JOB 21:29
    ('travelling', 'passed'), # GEN 12:6
    ('travelling', 'passing'), # ACT 18:23
    ('trays', 'fire-pans'), # EXO 37:23
    ('treacherous', 'treacheries'), # ZEP 3:4
    ('treacherous', 'treacherously'), # HAB 1:13
    ('treacherously', 'treacherous'), # JER 3:8
    ('treachery', 'deceits'), # PSA 38:12
    ('treachery', 'unfaithfulness'), # DAN 9:7
    ('treasures', 'desirable'), # LAM 1:11
    ('treasures', 'properties'), # EZR 6:8
    ('treasuries', 'storehouses'), # CH1 26:24
    ('treasuries', 'treasures'), # EZR 7:20
    ('treasury', 'treasure'), # ACT 8:27
    ('treat', 'treatment'), # CO2 13:10
    ('treaties', 'covenant'), # OBA 1:7
    ('treaty', 'covenant'), # JOS 9:15
    ('tree', 'terebinth'), # SA2 18:10
    ('tree', 'tree[s]'), # JOL 1:7
    ('trees', 'tree[s]'), # EZE 34:27
    ('tremble', 'shake'), # EZE 38:20
    ('trembling', 'shook'), # DAN 10:10
    ('tribes', 'tribe[s]'), # EXO 28:21
    ('tried', 'attempting'), # ACT 26:21
    ('tried', 'judged'), # ACT 23:6
    ('tried', 'seek'), # CH2 31:21
    ('tried', 'seeking'), # ACT 13:8
    ('tried', 'sought'), # ECC 7:28
    ('tries', 'attempt'), # JOB 4:2
    ('tries', 'seek'), # LUK 17:33
    ('triumph', 'rejoice'), # PRO 28:12
    ('triumphantly', 'triumph'), # ISA 44:23
    ('troops', 'troop[s]'), # CH2 25:9
    ('trouble', 'distress'), # LAM 1:21
    ('trouble', 'harm'), # KI2 14:10
    ('trouble', 'mischief'), # HAB 1:3
    ('troubled', 'disturbed'), # DAN 2:1
    ('troubles', 'afflicted'), # PSA 119:67
    ('troubles', 'distress'), # PSA 77:2
    ('troublesome', 'trouble'), # ISA 10:1
    ('trough', 'channel'), # GEN 24:20
    ('trough', 'manger'), # LUK 2:7
    ('true', 'genuine'), # TI1 1:2
    ('trumpet', 'horn'), # JDG 3:27
    ('Trust', 'rely'), # PSA 37:5
    ('trust', 'believed'), # PSA 78:32
    ('trust', 'believing'), # ACT 13:39
    ('trust', 'confidence'), # PRO 22:19
    ('trust', 'hope'), # ACT 24:15
    ('trust', 'hoping'), # JN3 1:2
    ('trust', 'rely'), # PSA 49:6
    ('trusted', 'believing'), # JHN 1:12
    ('trusted', 'faithfulness'), # CH1 9:26
    ('trusting', 'rely'), # KI2 18:20
    ('trusting', 'relying'), # CH2 32:10
    ('trusting', 'security'), # PRO 3:29
    ('trusts', 'confidence'), # PSA 40:4
    ('trusts', 'hope'), # JN1 3:3
    ('trusts', 'relies'), # PRO 28:25
    ('truth', 'faithfulness'), # DAN 9:13
    ('truth', 'truthful'), # EPH 4:15
    ('truthful', 'truth'), # ECC 12:10
    ('truthfully', 'truth'), # ISA 59:4
    ('try', 'examine'), # PRO 23:30
    ('try', 'seek'), # ECC 8:17
    ('try', 'seeking'), # MAT 6:32
    ('try', 'sought'), # CH2 16:12
    ('trying', 'sought'), # KI1 19:10
    ('tumours', 'tumors'), # SA1 6:11
    ('turbans', 'caps'), # DAN 3:21
    ('turbans', 'headdresses'), # ISA 3:23
    ('turmoil', 'tumult'), # PSA 65:7
    ('Turn', 'return'), # PSA 6:4
    ('turn', 'becoming'), # JHN 16:20
    ('turn', 'changed'), # EXO 7:17
    ('turn', 'repentance'), # ACT 20:21
    ('turn', 'return'), # KI1 8:33
    ('turn', 'returned'), # PSA 18:37
    ('turned', 'became'), # GEN 19:26
    ('turned', 'become'), # ISA 1:22
    ('turned', 'bent'), # EZE 17:7
    ('turned', 'changed'), # EXO 7:20
    ('turned', 'returned'), # ECC 4:1
    ('turned', 'twisted'), # RUT 3:8
    ('turning', 'repentance'), # CO2 7:9
    ('turtledove', 'turtle-dove'), # GEN 15:9
    ('twilight', 'evenings'), # EXO 29:39
    ('twisted', 'writhe'), # HAB 3:10
    ('tying', 'binding'), # ACT 22:4
    ('ulcers', 'ulcerated'), # LUK 16:20
    ('unbearably', 'unbearable'), # LUK 11:46
    ('uncertain', 'uncertainty'), # TI1 6:17
    ('unchanging', 'unchangeable'), # HEB 6:17
    ('uncircumcised', 'uncircumcision'), # ACT 11:3
    ('uncircumcision', 'uncircumcised'), # HAB 2:16
    ('unclean', 'uncleanness'), # LEV 7:20
    ('underclothes', 'undergarments'), # EZE 44:18
    ('underneath', 'beneath'), # DEU 33:27
    ('understand', 'hear'), # GEN 11:7
    ('understand', 'reading'), # LUK 10:26
    ('understanding', 'discernment'), # PRO 7:4
    ('understands', 'hearing'), # CO1 14:2
    ('understood', 'read'), # MAT 12:5
    ('underwear', 'undergarments'), # EXO 28:42
    ('undo', 'untie'), # ACT 13:25
    ('undone', 'untie/release'), # ISA 33:23
    ('unfaithful', 'unfaithfully'), # CH2 12:2
    ('unfaithful', 'unfaithfulness'), # CH2 29:19
    ('unintentionally', 'inadvertence'), # LEV 4:2
    ('united', 'joined'), # ROM 12:9
    ('unity', 'oneness'), # EPH 4:3
    ('unjust', 'unjustly'), # PE1 2:19
    ('unlace', 'untie'), # LUK 3:16
    ('unloaded', 'unharnessed'), # GEN 24:32
    ('unploughed', 'unplowed'), # JER 4:3
    ('unrighteous', 'unrighteousness'), # TH2 2:10
    ('untarnished', 'holiness'), # CH1 16:10
    ('untie', 'untie/release'), # ISA 32:20
    ('untied', 'untie/release'), # GEN 49:21
    ('uproot', 'pluck'), # KI1 14:15
    ('uprooted', 'plucked'), # EZE 19:12
    ('upward', 'upwards'), # EZE 8:2
    ('upwards', 'upward'), # JHN 11:41
    ('urge', 'exhorting'), # ACT 27:34
    ('urged', 'exhorting'), # CO1 16:12
    ('urged', 'incited'), # JDG 1:14
    ('urgent', 'urgently'), # NUM 22:37
    ('urging', 'exhorting'), # CO2 2:8
    ('useless', 'uselessly'), # MAT 15:9
    ('utensils', 'articles'), # EXO 31:9
    ('valley', 'wadi'), # CH2 20:16
    ('valleys', 'valley[s]'), # NUM 14:25
    ('valleys', 'wadis'), # KI1 18:5
    ('valuable', 'desirable'), # CH2 36:19
    ('valuable', 'valuable[s]'), # JDG 18:21
    ('valued', 'treasured'), # JOB 23:12
    ('vegetable', 'vegetable[s]'), # KI1 21:2
    ('vegetables', 'vegetable[s]'), # PRO 15:17
    ('victorious', 'strong'), # CH2 13:18
    ('victory', 'salvation'), # PSA 118:15
    ('victory', 'triumphed'), # COL 2:15
    ('victory', 'victorious'), # ZEC 9:9
    ('vigour', 'vigors'), # JOB 20:11
    ('villages', 'village[s]'), # SA1 6:18
    ('vindication', 'righteousness'), # JOL 2:23
    ('violated', 'humiliated'), # DEU 22:29
    ('violating', 'transgressing'), # CH2 24:20
    ('violence', 'fierceness'), # ISA 42:25
    ('violence', 'violent'), # DAN 11:14
    ('violence', 'violently'), # EZE 22:26
    ('Violent', 'violence'), # PRO 16:29
    ('violent', 'violence'), # GEN 6:11
    ('violent', 'violences'), # PSA 140:4
    ('violent', 'violently'), # JER 22:3
    ('violently', 'violence'), # REV 18:21
    ('virgin', 'virgin[s]'), # JDG 21:12
    ('virgin', 'virginities'), # DEU 22:14
    ('visions', 'see'), # EZE 13:9
    ('visions', 'seen'), # EZE 13:6
    ('visiting', 'visitation'), # LUK 19:44
    ('visitors', 'visiting'), # ACT 2:10
    ('voice', 'sound'), # PSA 47:1
    ('voluntarily', 'voluntary'), # CO2 8:3
    ('volunteered', 'voluntary'), # CO2 8:17
    ('wages', 'wage[s]'), # GEN 31:7
    ('wailings', 'wail'), # AMO 8:3
    ('waist', 'hips'), # EXO 28:42
    ('waist', 'loins'), # DAN 10:5
    ('waistband', 'girdle'), # EXO 28:27
    ('waistband', 'sash'), # EXO 28:4
    ('waistbands', 'sashes'), # EXO 28:40
    ('waists', 'hips'), # EZE 23:15
    ('waists', 'loins'), # EZE 44:18
    ('wait', 'delaying'), # SA2 15:28
    ('waited', 'rested'), # SA1 25:9
    ('waiting', 'delayed'), # JDG 3:26
    ('Wake', 'awake'), # PSA 7:6
    ('wake', 'awake'), # JER 51:57
    ('wake', 'awakened'), # KI2 4:31
    ('wake', 'rouse'), # GEN 49:9
    ('walk', 'advance'), # PRO 9:6
    ('walk', 'go'), # JOB 24:10
    ('walk', 'going'), # MAT 20:17
    ('walk', 'passes'), # EZE 33:28
    ('walked', 'going'), # JER 3:6
    ('walked', 'passed'), # JER 34:19
    ('walked', 'went'), # SA1 31:12
    ('walking', 'go'), # PSA 122:0
    ('walking', 'going'), # ACT 16:16
    ('walking', 'gone'), # ISA 20:3
    ('walking', 'passing'), # JHN 9:1
    ('walls', 'rampart'), # PSA 48:13
    ('wander', 'go'), # PRO 7:25
    ('wandered', 'strayed'), # JAM 5:19
    ('wandered', 'went'), # CH1 16:20
    ('wandering', 'wanderer'), # GEN 4:12
    ('want', 'desire'), # PSA 10:3
    ('want', 'desired'), # PSA 40:6
    ('want', 'seek'), # ACT 15:17
    ('want', 'seeking'), # JHN 1:38
    ('want', 'seeks'), # PRO 18:15
    ('want', 'sought'), # CH2 25:15
    ('wanted', 'desire'), # CH2 9:12
    ('wanted', 'desired'), # DAN 7:19
    ('wanted', 'desiring'), # KI1 13:33
    ('wanted', 'seeking'), # JHN 19:12
    ('wanted', 'sought'), # ZEC 6:7
    ('wants', 'desired'), # PSA 132:13
    ('wants', 'desires'), # PRO 21:1
    ('wants', 'seek'), # CH2 30:19
    ('wants', 'seeking'), # SA1 20:1
    ('wants', 'seeks'), # PRO 15:14
    ('war', 'fighting'), # SA1 28:15
    ('war', 'warfare'), # CO2 10:4
    ('warned', 'instruct'), # ISA 8:11
    ('warned', 'instructed'), # PSA 2:10
    ('warned', 'protested'), # EXO 21:29
    ('warning', 'admonishing'), # ACT 20:31
    ('warnings', 'discipline'), # JOB 33:16
    ('warriors', 'mighty'), # SA2 1:22
    ('wash', 'washer'), # ISA 7:3
    ('washed', 'bathed'), # SA2 12:20
    ('washed', 'washer'), # KI2 18:17
    ('waste', 'rot'), # EZE 4:17
    ('wasted', 'spoil'), # PRO 23:8
    ('wasteland', 'desolation'), # JOB 38:27
    ('wasteland', 'waste'), # JER 18:16
    ('wasteland', 'wastes'), # JER 51:26
    ('watch', 'looked'), # EXO 33:8
    ('watch', 'see'), # SA1 6:9
    ('watched', 'looked'), # REV 8:13
    ('watched', 'looking'), # JDG 13:19
    ('watched', 'observing'), # MRK 12:41
    ('watched', 'saw'), # SA1 6:16
    ('watchers', 'watchmen'), # JER 31:6
    ('watches', 'observing'), # JHN 6:40
    ('watchful', 'watching'), # MAT 25:13
    ('watching', 'looking'), # JDG 16:27
    ('wave', 'breakers'), # SA2 22:5
    ('way', 'direction'), # JDG 9:37
    ('way', 'journey'), # EXO 18:8
    ('way', 'manner'), # SA2 15:6
    ('way', 'path'), # PSA 44:18
    ('way', 'paths'), # PRO 9:15
    ('ways', 'path'), # PSA 119:104
    ('weak', 'feeble'), # NUM 13:18
    ('weakest', 'weak'), # JDG 6:15
    ('wealth', 'abundance'), # GEN 31:1
    ('wealth', 'opulence'), # JOB 36:19
    ('wealth', 'riches'), # LUK 8:14
    ('wealthy', 'wealth'), # CH2 17:5
    ('weapons', 'weapon[s]'), # CH2 32:5
    ('weapons', 'weaponry'), # EZE 39:9
    ('wear', 'bear'), # SA1 2:28
    ('wears', 'wearies'), # ECC 10:15
    ('weeds', 'grass'), # LUK 12:28
    ('weeds', 'plant'), # HOS 10:4
    ('weigh', 'weight'), # CH1 22:14
    ('weighed', 'weight'), # CH1 20:2
    ('weighing', 'weight'), # JOS 7:21
    ('weighs', 'weight'), # PRO 27:3
    ('weight', 'weighed'), # JER 32:10
    ('welcome', 'received'), # LUK 9:53
    ('went', 'moved'), # EZE 10:22
    ('went', 'passed'), # EST 4:17
    ('went', 'passing'), # ACT 15:41
    ('went', 'proceeded'), # ACT 12:3
    ('went', 'walking'), # GEN 18:16
    ('west', 'westward'), # CH1 9:24
    ('western', 'westward'), # EZE 48:10
    ('wheels', 'wheel[s]'), # EXO 14:25
    ('whirlwind', 'storm'), # ZEC 7:14
    ('whirlwind', 'storm-wind'), # HOS 8:7
    ('whirlwinds', 'storm-winds'), # ISA 21:1
    ('white', 'whitened'), # REV 7:14
    ('Wicked', 'wickedness'), # PRO 16:12
    ('wicked', 'evil'), # GEN 39:9
    ('wicked', 'wickedly'), # CH2 20:35
    ('wicked', 'wickedness'), # ACT 3:26
    ('wickedly', 'wickedness'), # ISA 58:6
    ('wickedness', 'evil'), # PSA 107:34
    ('wickedness', 'iniquity'), # ISA 57:17
    ('wickedness', 'sin'), # LEV 20:20
    ('wide', 'breadth'), # DEU 3:11
    ('wide', 'broad'), # CH1 4:40
    ('wide', 'spacious'), # EXO 3:8
    ('widow', 'widowhood'), # ISA 54:4
    ('widows', 'widow[s]'), # PSA 146:9
    ('widows', 'widowhood'), # SA2 20:3
    ('width', 'breadth'), # EZE 40:20
    ('wife', 'woman'), # PRO 21:9
    ('wild', 'violent'), # ISA 35:9
    ('wilderness', 'desolate'), # PSA 68:7
    ('wilderness', 'wildernesss'), # HEB 11:38
    ('willful', 'presumptuous'), # PSA 19:13
    ('willingly', 'willing'), # CO2 8:10
    ('wine-pressing', 'wine-press'), # MAT 21:33
    ('wine-pressing', 'wine-vat'), # ISA 5:2
    ('wine-pressing', 'wine-vats'), # JER 48:33
    ('wine-pressing', 'winepress'), # HOS 9:2
    ('wine-pressing', 'winepresses'), # ISA 16:10
    ('wineskin', 'skin-bottle'), # PSA 119:83
    ('wineskins', 'skin-bottles'), # JOS 9:4
    ('wisdom', 'skill'), # EZE 28:5
    ('wisdom', 'understanding'), # JOB 39:26
    ('wiser', 'wise'), # JOB 35:11
    ('wish', 'wanting'), # CO1 7:7
    ('withdraw', 'take'), # REV 6:4
    ('within', 'inner'), # HOS 5:4
    ('within', 'inward'), # GEN 25:23
    ('witness', 'see'), # DEU 28:34
    ('witnessed', 'saw'), # LUK 5:26
    ('witnessed', 'seen'), # JHN 6:14
    ('woke', 'awaking'), # MRK 4:38
    ('woke', 'awoke'), # GEN 9:24
    ('woken', 'awakened'), # EZE 7:6
    ('woman', 'wife'), # GEN 25:1
    ('women', 'wives'), # NEH 13:26
    ('wonderful', 'wonder[s]'), # PSA 88:12
    ('wonderful', 'wonders'), # CH1 16:9
    ('wondering', 'marvelling'), # LUK 1:21
    ('wonders', 'wonder[s]'), # PSA 88:10
    ('wooden', 'wood'), # HOS 4:12
    ('wooden', 'woods'), # EXO 7:19
    ('woollen', 'wool'), # EZE 34:3
    ('word', 'message'), # ECC 8:4
    ('word', 'speech'), # TIT 2:8
    ('words', 'message'), # DAN 9:12
    ('words', 'messages'), # JHN 3:34
    ('words', 'phrase'), # HEB 12:27
    ('words', 'speech'), # JOB 13:17
    ('words', 'speech/discourse'), # GEN 4:23
    ('work', 'deed[s]'), # RUT 2:12
    ('work', 'toil'), # ECC 2:24
    ('work', 'toils'), # PRO 16:26
    ('working', 'toil'), # ECC 4:9
    ('world', 'earth'), # ACT 3:25
    ('world', 'earth/land'), # CH1 16:14
    ('worldly', 'world'), # CO1 7:34
    ('worms', 'maggot'), # JOB 21:26
    ('worn', 'weary'), # JER 12:5
    ('worried', 'disturbed'), # MAT 14:26
    ('Worship', 'bow'), # CH1 16:29
    ('Worship', 'bow down'), # CH1 16:29
    ('Worship', 'serve'), # EZE 20:39
    ('worship', 'bow down'), # CH2 7:19
    ('worship', 'bowed'), # SA2 15:32
    ('worship', 'bowed down'), # SA2 15:32
    ('worship', 'homage'), # DAN 3:5
    ('worship', 'paid homage'), # DAN 2:46
    ('worship', 'pay homage'), # DAN 3:5
    ('worship', 'paying homage'), # DAN 3:7
    ('worship', 'serve'), # EXO 10:7
    ('worship', 'serving'), # HEB 12:28
    ('worshipped', 'bowed'), # JOB 1:20
    ('worshipped', 'bowed down'), # CH2 7:22
    ('worshipped', 'served'), # CH2 24:18
    ('worshipping', 'bowing'), # EZE 8:16
    ('worshipping', 'bowing down'), # EZE 8:16
    ('worth', 'price'), # PRO 31:10
    ('worth', 'valuation'), # JOB 28:13
    ('worth', 'worthy'), # LUK 7:4
    ('worthless', 'worthlessness'), # ISA 1:13
    ('worthy', 'worthily'), # PHP 1:27
    ('wounded', 'pain'), # CH1 10:3
    ('wounds', 'bruises'), # JOB 9:17
    ('wounds', 'sicknesses'), # CH2 24:25
    ('wounds', 'wound[s]'), # ISA 53:5
    ('wrapped', 'clothed'), # REV 10:1
    ('wrecked', 'broke'), # EZE 27:26
    ('writhes', 'anguish'), # ISA 13:8
    ('wrong', 'iniquity'), # DAN 9:5
    ('wrong', 'unrighteousness'), # JOB 34:10
    ('wrong', 'wicked'), # EXO 23:2
    ('wrong', 'wrongly'), # JAM 4:3
    ('wrongdoing', 'mischief'), # HAB 1:13
    ('wronged', 'subverted'), # JOB 19:6
    ('yelled', 'called'), # GEN 39:18
    ('yelled', 'crying'), # ACT 19:28
    ('yelled', 'crying out'), # ACT 19:28
    ('yelled', 'shouted'), # SA1 25:14
    ('yelling', 'cried'), # MAT 14:26
    ('yelling', 'cried out'), # ACT 7:57
    ('yelling', 'crying'), # ACT 19:32
    ('yelling', 'crying out'), # ACT 19:32
    ('yielded', 'gives'), # PSA 67:6
    ('young', 'child'), # TI1 1:18
    ('young', 'fawn'), # SNG 2:9
    ('young', 'son'), # DAN 3:25
    ('young', 'sons'), # SNG 2:3
    ('young', 'younger'), # ACT 5:6
    ('young', 'youth'), # DEU 28:50
    ('young', 'youths'), # EZE 23:8
    ('younger', 'young'), # EZE 16:46
    ('youngest', 'young'), # CH2 21:17
    ('youngest', 'younger'), # LUK 22:26
    ('youthful', 'youths'), # JER 31:19
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


def loadAlignmentBible(folder, abbreviation):
    """Avoid parsing all 66 books when --books selects a subset."""
    bible = ESFMBible(folder, givenAbbreviation=abbreviation)
    bible.loadAuxiliaryFiles = True
    options = BibleOrgSysGlobals.commandLineArguments
    selected = options.books
    if selected:
        bible.preload()
        bible.loadDictionaries()
        for BBB in selected:
            if BBB in bible.possibleFilenameDict:
                bible.loadBook(BBB)
        if bible.books:
            bible.lookForAuxiliaryFilenames()
            bible.doPostLoadProcessing()
    else:
        bible.loadBooks()
    return bible


# forList = []
def main():
    """
    Main program to handle command line parameters and then run what they want.
    """
    BibleOrgSysGlobals.introduceProgram( __name__, PROGRAM_NAME_VERSION, LAST_MODIFIED_DATE )

    # global genericBookList
    # genericBibleOrganisationalSystem = BibleOrganisationalSystem( 'GENERIC-KJV-ENG' )
    # genericBookList = genericBibleOrganisationalSystem.getBookList()

    # Clean only selected books in memory. Preview/output runs must not touch sources.
    state.audit = []
    state.bookReports = []
    started = time.perf_counter()
    options = BibleOrgSysGlobals.commandLineArguments
    if options.report:
        BibleOrgSysGlobals.maxProcesses = 1 # Collect a deterministic, verse-level audit.
    if options.output_dir:
        options.output_dir.mkdir(parents=True, exist_ok=True)

    rv = loadAlignmentBible(OET_RV_ESFM_FolderPath, 'OET-RV')
    lvOT = loadAlignmentBible(OET_LV_OT_ESFM_InputFolderPath, 'OET-LV')
    lvNT = loadAlignmentBible(OET_LV_NT_ESFM_InputFolderPath, 'OET-LV')

    # Load the OT and NT word files
    state.wordTable, state.wordTableHeaderList = {}, {}
    for testament in ('OT','NT'):
        lv = lvOT if testament=='OT' else lvNT
        if not lv.books:
            continue
        BBB = next(iter(lv.books))
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

    # Selected-book runs report only the books actually processed.
    if not options.books:
        reportWordNumberPercentage( "Whole Bible", numWordsOT+numWordsNT, numWordNumberedOT+numWordNumberedNT )

    if options.report:
        options.report.parent.mkdir(parents=True, exist_ok=True)
        options.report.write_text(json.dumps({
            'seconds': round(time.perf_counter()-started, 3),
            'dry_run': options.dry_run, 'books': state.bookReports,
            'links': state.audit,
        }, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    if not options.dry_run and not options.output_dir:
        for something in OET_RV_ESFM_FolderPath.glob('*.OBD_Bible.pickle'):
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
    selected = BibleOrgSysGlobals.commandLineArguments.books
    for BBB in lv.books:
        if selected and BBB not in selected:
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
    if not selected:
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
        state.rvLineIndex = index_book_lines(state.rvESFMLines)
        state.rvTokenCache = {}
        beforeWords, beforeLinked = countWordsAndWordNumbers(state.rvESFMLines)
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
        options = BibleOrgSysGlobals.commandLineArguments
        destination = options.output_dir / rvESFMFilename if options.output_dir else rvESFMFilepath
        if not options.dry_run:
            destination.write_text(newESFMtext, encoding='utf-8')
        if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 2:
            vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"    Did {bookWordPhraseAdds:,} word phrase adds, {bookSimpleListedAdds:,} simple listed adds, {bookProperNounAdds:,} proper noun adds, {bookFirstPartMatchedAdds:,} first part adds, {bookManualMatchedAdds:,} manual adds, {bookChangedNumberAdds:,} changed number adds, {bookRewordedAdds:,} reworded adds, {bookSpecialistAdds:,} specialist add span adds and {bookInOrderMatchedAdds:,} in-order adds for {BBB}." )
        if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 2:
            vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"    Did {bookWordPhraseAddsNS:,} word phrase NS, {bookSimpleListedAddsNS:,} simple listed NS, {bookProperNounAddsNS:,} proper noun NS, {bookFirstPartMatchedAddsNS:,} first part NS, {bookManualMatchedAddsNS:,} manual NS, {bookChangedNumberAddsNS:,} changed number NS, {bookRewordedAddsNS:,} reworded NS, {bookSpecialistAddsNS:,} specialist add span NS and {bookInOrderMatchedAddsNS:,} in-order NS for {BBB}." )
        if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 2:
            vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"      {'Previewed' if options.dry_run else 'Saved'} OET-RV {BBB} {len(newESFMtext):,} characters ({destination})" )
    else:
        # assert bookSimpleListedAdds == bookProperNounAdds == 0
        if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.verbosityLevel >= 3:
            vPrint( 'Info', DEBUGGING_THIS_MODULE, f"    No changes made to OET-RV {BBB}." )

    # Say how much of this book is now connected to the OET-LV.
    #   Selected-book runs report each book; full runs report testament and Bible totals
    #   in connect_OET_RV() and main().
    bookNumWords,bookNumWordNumbered = countWordsAndWordNumbers( state.rvESFMLines )
    options = BibleOrgSysGlobals.commandLineArguments
    if options.output_dir and not options.dry_run and newESFMtext == state.rvESFMText:
        (options.output_dir / rvESFMFilename).write_text(newESFMtext, encoding='utf-8')
    state.bookReports.append(dict(book=BBB, words=bookNumWords, before=beforeLinked,
                                  after=bookNumWordNumbered, added=bookNumWordNumbered-beforeLinked,
                                  removed_plain_add=numStraightAddSpanRemovals))
    if options.books:
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
    rvText = getLiveRVVerseText(BBB, c, v)
    if not rvText or not lvText: return (0,0), (0,0), (0,0), (0,0), (0,0), (0,0), (0,0), (0,0), (0,0)

    # ⇔ swaps clauses; words WITHIN each clause retain their left-to-right order.
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

    numWordPhraseAdds,numWordPhraseNS = matchWordPhrases( BBB, c,v, rvWords, lvWords, reversedOrder )
    numSpecialistAdds,numSpecialistNS = matchSpecialistAddSpans( BBB, c,v, rvWords, rvAddSpans, lvWords )
    numSimpleListedAdds,numSimpleListedNS = matchOurListedSimpleWords( BBB, c,v, rvWords, lvWords )
    numVerbSetAdds,numVerbSetNS = matchVerbSets( BBB, c,v, rvWords, lvWords )

    # Now get the uppercase words
    rvUpperWords = [rvWord for rvWord in rvWords if rvWord[0].isupper() and rvWord.split('¦',1)[0].replace("'",'').isalpha()]
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

    if len(rvCapitalisedWordList)==1 and len(lvCapitalisedWordList)==1:
        # A sole capitalised RV word is not necessarily the sole LV name. The
        # adjusted-name pass below handles known transliterations explicitly.
        if simplifyRVLVWord(rvCapitalisedWordList[0]) != simplifyRVLVWord(lvCapitalisedWordList[0].split('¦',1)[0]):
            return 0, 0
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


@lru_cache(maxsize=1)
def getLexicalIndexes():
    """Build form -> lexical-group indexes once, instead of scanning all tables per verse."""
    nounWords = set(SIMPLE_NOUNS_FLAT) | set(verbalNouns)
    simple = defaultdict(set)
    for word in SIMPLE_WORDS:
        forms = {word} | (numberVariants(word) if word in nounWords else set())
        for form in forms:
            simple[form.lower()].add(word)
    verbs = defaultdict(set)
    for index, forms in enumerate(SIMPLE_VERB_SETS):
        for form in forms:
            verbs[form.lower()].add(index)
    return simple, verbs


def matchIndexedWords(BBB, c, v, rvWords, lvWords, formIndex):
    """Match a lexical group only if each verse contains one occurrence of it."""
    rvGroups, lvGroups = defaultdict(set), defaultdict(set)
    for i, word in enumerate(rvWords):
        if '¦' not in word:
            for group in formIndex.get(word.lower(), ()):
                rvGroups[group].add(i)
    for i, word in enumerate(lvWords):
        if getLVWordNumber(word) is not None:
            for alternative in word.split('¦', 1)[0].split('/'):
                for group in formIndex.get(alternative.lower(), ()):
                    if group in rvGroups:
                        lvGroups[group].add(i)
    added = ns = 0
    NT = bos_books_codes_py.is_new_testament_nr(BBB)
    for group in sorted(rvGroups, key=str):
        if len(rvGroups[group]) != 1 or len(lvGroups[group]) != 1:
            continue
        ri, li = next(iter(rvGroups[group])), next(iter(lvGroups[group]))
        number = getLVWordNumber(lvWords[li])
        if addNumberToRVWord(BBB, c, v, rvWords[ri], number):
            added += 1
            if NT and 'N' in state.wordTable['NT'][number][state.wordTableHeaderList['NT'].index('GlossCaps')]: ns += 1
    return added, ns


def matchOurListedSimpleWords(BBB, c, v, rvWordList, lvWordList):
    """Use the curated simple-word and noun-number tables."""
    return matchIndexedWords(BBB, c, v, rvWordList, lvWordList, getLexicalIndexes()[0])


def matchVerbSets(BBB, c, v, rvWordList, lvWordList):
    """Use the curated verb forms, including irregular inflections."""
    return matchIndexedWords(BBB, c, v, rvWordList, lvWordList, getLexicalIndexes()[1])


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
#   unambiguous, which reduces false matches like 'protesting' vs 'prostrating'.
#   This allows inflectional matches like 'immersing'/'immersed' (6 chars) and
#   'forgiveness'/'forgiven' (6 chars).
ORDER_MATCH_PREFIX_LENGTH = 5

# One-letter words remain excluded from lexical matching; semantic % spans can
# still match 'I'. The dynamic program checks ambiguity even for short words.
MIN_EXACT_MATCH_WORD_LENGTH = 2


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


@lru_cache(maxsize=65536)
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


@lru_cache(maxsize=131072)
def scoreRVLVWords( rvWord:str, lvWord:str ) -> Optional[Tuple[str,int]]:
    """
    Score how confidently an OET-RV word and an OET-LV word are the same word.

    Returns a (description, score) tuple, or None if they are too different to connect.
    These are candidate scores, not guarantees of semantic equivalence:
        the bounded alignment supplies additional positional evidence.
            •  the same word, however short it is, allowing for a case difference, so RV
                'Preparation' matches LV 'preparation' and RV 'put' matches LV 'put'
            •  the same word once its inflectional ending is allowed for, so RV
                'wineskin' matches LV 'wineskins'
            •  a long shared opening, so RV 'money-changers' matches LV 'moneychangers'
                and RV 'immerse' matches LV 'immersing'
            •  one of the EQUIVALENT_LV_RV_WORDS pairs, so RV 'Whenever' matches LV 'wherever'
    The inherited long-prefix heuristic can confuse different words and senses.
    Agreement across optimal alignments does not itself prove semantic accuracy.
    """
    r,l = simplifyRVLVWord( rvWord ), simplifyRVLVWord( lvWord )
    if r == l and len(r) >= MIN_EXACT_MATCH_WORD_LENGTH: return ('same word', 100)
    if l in EQUIVALENT_LV_RV_WORDS.get( r, set() ): return ('another word for the same thing', 60)
    verbs = getLexicalIndexes()[1]
    if verbs.get(r, set()) & verbs.get(l, set()): return ('curated verb forms', 95)
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


def getUnnumberedRVWords( BBB:str, c:int, v:int ) -> set:
    """Legacy lexical matchers use a set; positional matchers retain occurrences."""
    return {simplifyRVLVWord(t.text) for t in getLiveRVTokens(BBB, c, v)
            if t.linkable and t.number is None}


def getLVWordNumber( lvWordStr:str ) -> Optional[int]:
    """
    Pull the OET-LV word number out of a word like 'wineskins¦23221'.

    We only take the leading run of digits, because the OET-LV sometimes has a gloss helper
        marker stuck to the number (e.g. 'will¦23935˒'), which would otherwise stop int().
    """
    m = re.match( r'^.*?¦(\d+)', lvWordStr )
    return int(m.group(1)) if m else None
# end of getLVWordNumber


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


def matchWordsInOrder( BBB:str, c:int,v:int, rvVerseText:str, rvWordList:List[str], lvWordList:List[str], reversedOrder:bool ) -> Tuple[int,int]:
    """Align live occurrences between existing links, including semantic add spans.

    Alternatives share one alignment column. Existing links bound local gaps in
    LV text order, allowing local phrase reordering. Each accepted RV occurrence
    must receive the same source number in every optimal alignment of its gap.
    """
    testament = 'NT' if bos_books_codes_py.is_new_testament_nr(BBB) else 'OT'
    columns = []
    for word in lvWordList:
        number = getLVWordNumber(word)
        if number is None:
            continue
        plain = word.split('¦', 1)[0]
        proper = any(w[:1].isupper() for w in plain.split('/')) and lvWordIsProperNoun(state.wordTable[testament][number], testament)
        columns.append(LVToken(plain, number, proper))
    added = ns = 0
    while True:
        proposals = propose_links(getLiveRVTokens(BBB, c, v), columns,
                                  scoreRVLVWords, simplifyRVLVWord, reversedOrder)
        passAdded = 0
        # Work right to left, so recorded character offsets remain valid.
        for token, number, reason in sorted(proposals, key=lambda p: (p[0].line, p[0].start), reverse=True):
            result, resultNS = applyRVTokenLink(BBB, c, v, token, number, reason)
            passAdded += result
            ns += resultNS
        added += passAdded
        if not passAdded:
            break # Every productive pass consumes at least one unnumbered occurrence.
    return added, ns


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
MIN_ANCHORED_ADD_WORD_LENGTH = 2


def lvWordIsProperNoun( lvWordRow:List[str], testament:str ) -> bool:
    """
    Return True if an OET-LV word is a proper noun, using the same test that
        matchIdenticalProperNouns() uses, so that we can tell a name from a word that just
        happens to be capitalised because it starts a sentence (e.g. LV 'Be¦1102' and 'I¦1166').
    """
    if testament == 'NT':
        return (lvWordRow[state.wordTableHeaderList['NT'].index('Role')].strip() == 'N'
                and 'W' in lvWordRow[state.wordTableHeaderList['NT'].index('GlossCaps')])
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


def getNameWordsBeforeSpan( liveWords:List[str], spanFirstIx:int, excludedWordIndexes:frozenset=frozenset() ) -> List[str]:
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
    Match same-verse elisions (≡) and traditional-name alternatives (!).
    Pronoun substitutions run later, using the live anchors created by lexical passes.
    We run these BEFORE the matchers that compare the OET-RV and OET-LV words with each other,
        because these rules use what the translator told us about the span, which is firmer
        evidence than the OET-RV and OET-LV words happening to look similar.
    """
    numAdded = numNS = 0

    for matcher in ( matchRepeatedWords, matchNamesViaTraditionalNames ):
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
    """Match curated one-RV-word translations only when the LV phrase is unique.

    In particular, 'his' cannot take the FIRST 'of him' in a verse containing
    several people. The old first-match search silently made that mistake.
    """
    NT = bos_books_codes_py.is_new_testament_nr(BBB)
    added = ns = 0
    for rvWord, lvPhrase in RV_SINGLE_WORDS_FROM_LV_WORD_STRINGS:
        if rvVerseWordList.count(rvWord) != 1:
            continue
        words = lvPhrase.split()
        matches = [i for i in range(len(simpleLVWordList)-len(words)+1)
                   if simpleLVWordList[i:i+len(words)] == words]
        if len(matches) != 1:
            continue
        number = getLVWordNumber(lvVerseWordList[matches[0]])
        if number is not None and addNumberToRVWord(BBB, c, v, rvWord, number):
            added += 1
            if NT and 'N' in state.wordTable['NT'][number][state.wordTableHeaderList['NT'].index('GlossCaps')]: ns += 1
    return added, ns


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
        # A trailing gloss-helper character (e.g. ˒) is valid ESFM.
        wordNumber = getPositiveLeadingInt( wordNumber )
    assert wordNumber < len( state.wordTable[testament] )
    wordRow = state.wordTable[testament][wordNumber]
    if (DEBUGGING_THIS_MODULE) or BibleOrgSysGlobals.debugFlag or BibleOrgSysGlobals.verbosityLevel >= 4:
        dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"'{word}' {wordRow}" )
    return word,wordNumber,wordRow
# end of connect_OET-RV_words_via_OET-LV.getLVWordRow


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
ADD_SPECIAL_CHARS = '@#≈≡*<>&%?+^!='
straightAddSpanRegex = re.compile(
    r'\\\+?add \??([^@#≈≡*<>&%?+^!=\\][^\\]*?)\\\+?add\*')


# A '\add <code>...<text>\add*' specialist span.  The code is what the translator is telling us
#   about the span, e.g. '\add ≈because\add*' (we reworded it) or '\add #straps\add*' (we
#   changed the number).  A leading '?' means the translator is not sure about the code
#   (e.g. '\add ?≈about\add*'), and the OET-RV never puts the '?' after the code.
specialAddSpanRegex = re.compile(
    f'\\\\\\+?add (?P<code>\\?[{ADD_SPECIAL_CHARS}]|[{ADD_SPECIAL_CHARS}])(?P<text>[^\\\\]*?)\\\\\\+?add\\*' )

# Specialist span words available to lexical and formatting-aware passes.
# Plain additions, +/=/< and ^ are excluded from new automatic connections.
# Traditional-name (!) spans have their own matching pass.
ADD_CODES_TO_EXPOSE = ( '≈', '#', '@', '*', '%', '&', '≡', '>' )
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
        code = match.group( 'code' ).lstrip('?')
        if code not in codesToExpose: return match.group( 0 )
        return f"{ADD_SPAN_START_CHAR}{code}{match.group( 'text' )}{ADD_SPAN_END_CHAR}"
    return specialAddSpanRegex.sub( replacer, rvText )
# end of exposeMatchedAddSpans



def getRVVerseLines(BBB:str, c:int, v:int):
    """Resolve the existing Psalm-title convention once, then use the book index."""
    if bos_books_codes_py.has_psalm_title(BBB, str(c)):
        v = 0 if v == 1 else v-1
    return state.rvLineIndex.get((c, v), ())


def getLiveRVTokens(BBB:str, c:int, v:int):
    """Cache tokens until a verse's lines change; offsets always describe live text."""
    entries = getRVVerseLines(BBB, c, v)
    signature = tuple(state.rvESFMLines[n] for n, _ in entries)
    key = (c, v)
    cached = state.rvTokenCache.get(key)
    if cached is None or cached[0] != signature:
        tokens = [t for n, start in entries for t in tokenize(state.rvESFMLines[n][start:], n, start)]
        state.rvTokenCache[key] = (signature, tokens)
    return state.rvTokenCache[key][1]


def getLiveRVVerseText( BBB:str, c:int, v:int ) -> str:
    """Return only this verse's body text, with character markers intact."""
    return ' '.join(state.rvESFMLines[n][start:] for n, start in getRVVerseLines(BBB, c, v))


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
    if '\\' in rvText:
        words, spans = [], []
        active = None
        for token in tokenize(rvText, split_names=not keepHyphenatedNames):
            if not token.linkable or token.code is not None and token.code not in codesToExpose:
                active = None
                continue
            word = token.text + (f'¦{token.number}' if token.number is not None else '')
            index = len(words)
            words.append(word)
            if token.code in codesToExpose:
                if active == token.span and spans:
                    code, first, _ = spans[-1]
                    spans[-1] = (code, first, index)
                else:
                    spans.append((token.code, index, index))
                active = token.span
            else:
                active = None
        return words, spans
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


def applyRVTokenLink(BBB, c, v, token, number, reason):
    """Insert at an exact source position without changing existing links or text."""
    line = state.rvESFMLines[token.line]
    if not token.linkable or token.number is not None:
        return 0, 0
    if line[token.start:token.end] != token.text or line[token.end:token.end+1] == '¦':
        return 0, 0  # A caller supplied a stale position.
    NT = bos_books_codes_py.is_new_testament_nr(BBB)
    addNS = (NT and 'N' in state.wordTable['NT'][number][state.wordTableHeaderList['NT'].index('GlossCaps')]
             and token.code is None and not isInsideNominaSacraSpan(line, token.start))
    # Nested character fields (e.g. words of Jesus) need +nd, never a second bare nd.
    nested = False
    if addNS:
        opens = re.findall(r'\\(\+?[a-zA-Z]+)(\*| )', line[:token.start])
        stack = []
        for marker, close in opens:
            if close == '*':
                if stack and stack[-1] == marker: stack.pop()
            elif marker.lstrip('+') in BibleOrgSysGlobals.USFMCharacterMarkers:
                stack.append(marker)
        nested = bool(stack)
    startND, endND = ('\\+nd ', '\\+nd*') if nested else ('\\nd ', '\\nd*')
    replacement = f'{startND if addNS else ""}{token.text}¦{number}{endND if addNS else ""}'
    state.rvESFMLines[token.line] = line[:token.start] + replacement + line[token.end:]
    if BibleOrgSysGlobals.commandLineArguments.report:
        state.audit.append(dict(book=BBB, chapter=c, verse=v, line=token.line+1,
                                word=token.text, number=number, reason=reason))
    return 1, int(bool(addNS))


def addNumberToRVWord( BBB:str, c:int,v:int, word:str, wordNumber:int ) -> bool:
    """Legacy spelling-only match: require a unique full word in the whole verse.

    Positional alignment calls applyRVTokenLink directly for repeated words.
    Never match inside a contraction, a footnote, a heading or a plain add span.
    Semantic substitutions are reserved for the position-based matcher.
    """
    assert isinstance(wordNumber, int) and '¦' not in word
    matches = [t for t in getLiveRVTokens(BBB, c, v) if t.text == word and t.linkable
               and t.code not in SEMANTIC_CODES]
    if not matches and '-' in word:
        # Traditional-name mappings can intentionally number a whole compound
        # name; ordinary alignment can also number its components separately.
        matches = [t for n, start in getRVVerseLines(BBB, c, v)
                   for t in tokenize(state.rvESFMLines[n][start:], n, start, split_names=False)
                   if t.text == word and t.linkable and t.code not in SEMANTIC_CODES]
    if len(matches) != 1:
        return False
    return bool(applyRVTokenLink(BBB, c, v, matches[0], wordNumber, 'lexical/name rule')[0])


def addNumberToRVPhrase( BBB:str, c:int,v:int, rvPhraseWords:List[str], lvNumber:int ) -> Tuple[int,int]:
    """Complete one occurrence of a curated phrase, retaining compatible existing links.

    Token positions allow repeated component words and nested formatting. A
    conflicting number or an added word anywhere in the phrase blocks it.
    """
    words = [word.casefold() for word in rvPhraseWords]
    tokens = getLiveRVTokens(BBB, c, v)
    occurrences = []
    for i in range(len(tokens)-len(words)+1):
        span = tokens[i:i+len(words)]
        if [t.text.casefold() for t in span] != words:
            continue
        if not all(t.linkable and t.code not in SEMANTIC_CODES for t in span):
            continue
        if any(t.number is not None and t.number != lvNumber for t in span):
            continue
        if any(t.number is None for t in span):
            occurrences.append(span)
    if len(occurrences) != 1:
        return 0, 0
    added = ns = 0
    for token in reversed(occurrences[0]):
        result, resultNS = applyRVTokenLink(BBB, c, v, token, lvNumber, 'curated phrase')
        added += result
        ns += resultNS
    return added, ns


if __name__ == '__main__':
    multiprocessing.set_start_method('fork') # The default was changed on POSIX systems from 'fork' to 'forkserver' in Python3.14
    multiprocessing.freeze_support() # Multiprocessing support for frozen Windows executables

    # Configure basic Bible Organisational System (BOS) set-up
    parser = BibleOrgSysGlobals.setup( PROGRAM_NAME, PROGRAM_VERSION )
    parser.add_argument('--books', nargs='+', metavar='BBB', help='process only these BOS book codes (e.g. RUT MRK)')
    parser.add_argument('--dry-run', action='store_true', help='compute links and coverage without writing ESFM files')
    parser.add_argument('--output-dir', type=Path, help='write proposed ESFM books here instead of replacing source books')
    parser.add_argument('--report', type=Path, help='write coverage and proposed positional/lexical links as JSON (single process)')
    BibleOrgSysGlobals.addStandardOptionsAndProcess( parser, exportAvailable=False )

    options = BibleOrgSysGlobals.commandLineArguments
    if options.books:
        invalid = set(options.books) - {p.stem.removeprefix('OET-LV_') for folder in (OET_LV_OT_ESFM_InputFolderPath, OET_LV_NT_ESFM_InputFolderPath) for p in folder.glob('OET-LV_*.ESFM')}
        if invalid: parser.error(f'Unknown book code(s): {", ".join(sorted(invalid))}')
    if options.output_dir and options.output_dir.resolve() == OET_RV_ESFM_FolderPath.resolve():
        parser.error('--output-dir must differ from the source folder')
    main()

    BibleOrgSysGlobals.closedown( PROGRAM_NAME, PROGRAM_VERSION )
# end of connect_OET-RV_words_via_OET-LV.py
