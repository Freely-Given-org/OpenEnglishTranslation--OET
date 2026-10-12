# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023-2026 Robert Hunt
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Directional mappings involving actual multiword phrases.

RV_SINGLE_WORDS_FROM_LV_WORD_STRINGS rows are (RV word, LV phrase, words_before).
The final integer is the number of that RV word's single-word alternatives in
the derived RV_SINGLE_WORDS_FROM_LV_WORDS lookup to try before this phrase.
These are the two-column and 'both' entries in SINGLE_WORD_MAPPINGS; 'aligned'
entries do not count towards this priority. Zero means phrase first.
This preserves the existing priority when single-word and phrase alternatives
compete. Keep each RV word's phrase rows in order, with nondecreasing priorities;
review these priorities if inserting or reordering its single-word alternatives.
LV_SINGLE_WORDS_TO_RV_WORD_STRINGS rows are (LV word, RV multiword phrase).
Both tables are alphabetised by the single word in the first column, ignoring
case, punctuation and diacritics. Alternatives for the same word retain their
matching priority. The mappings are case-sensitive and directional; do not
reverse their rows.
The optional OET-RV_wordPhrases_table.tsv is still loaded by the main script.
"""

RV_SINGLE_WORDS_FROM_LV_WORD_STRINGS = (
    ('120', 'a hundred twenty', 0),
    ('anything','all things', 0),
    ('approach', 'draw near', 1), # DEU 2:19
    ('approach', 'drawn near', 1), # ISA 41:5
    ('approach', 'drew near', 1), # EXO 14:20
    ('approached', 'drew near', 1), # DEU 4:11
    ('approaches', 'draw near', 0), # LEV 22:3
    ('arrested', 'given over', 3),
    ('ascend', 'go up', 0), # PSA 24:3
    ('ascend', 'went up', 0), # EPH 4:9
    ('ascended', 'gone up', 0), # EPH 4:8
    ('ascending', 'going up', 0), # GEN 28:12
    ("can't", 'can not', 1),
    ('chief', 'chief priest', 0),
    ('collapse','passing away', 0), # Mrk 13:31
    ("couldn't", 'could not', 0),
    ('cross','pass over', 0),
    ('demon', 'unclean spirit', 0),
    ('demons', 'unclean spirits', 0),
    ('depart', 'go out', 0), # GEN 31:13
    ('departed', 'went out', 4), # GEN 47:10
    ('descend', 'come down', 0), # ISA 31:4
    ('descend', 'go down', 0), # ISA 5:14
    ('descended', 'came down', 0), # EPH 4:9
    ('descended', 'come down', 1), # EPH 4:10
    ('descended', 'went down', 2), # EXO 15:5
    ('descending', 'going down', 0), # GEN 28:12
    ("didn't", 'did not', 1),
    ('die','pass away', 0), # Mrk 13:30
    ("doesn't", 'does not', 0),
    ("don't", 'do not', 1),
    ('enter', 'go in', 0),
    ('enter', 'came in', 0), # JHN 18:28
    ('enter', 'come in', 0), # HEB 3:19
    ('enter', 'coming in', 0), # HEB 3:18
    ('entered', 'came in', 1), # JHN 13:27
    ('entered', 'come in', 1), # ACT 10:25
    ('entering', 'come in', 0), # LUK 1:28
    ('entering', 'coming in', 0), # HEB 3:11
    ('enters', 'coming in', 0), # JHN 10:1
    ('everyone','you all', 3),
    ('exited', 'went out', 0), # EST 8:15
    ('exiting', 'going out', 1), # EXO 19:1
    ('gathered','coming together', 0), # Mrk 14:53
    ("God's", 'of god', 0),
    ("God’s", 'of god', 0),
    ("hadn't", 'had not', 0),
    ("hasn't", 'has not', 0),
    ("haven't", 'have not', 0),
    ('Hear', 'give ear', 0), # PSA 78:1
    ('hear', 'give ear', 0), # PSA 77:1
    ("He'd", 'He would', 0),
    ("he'd", 'he would', 0),
    ("He'd", 'He had', 0),
    ("He'll", 'He will', 0),
    ("He'll", 'he will', 0),
    ("he'll", 'he will', 0),
    ('her', 'of her', 0),
    ('Her', 'of her', 0),
    ("Here's", 'Here is', 0),
    ("here's", 'here is', 0),
    ("He's", 'He is', 0),
    ("he's", 'he is', 0),
    ('his', 'of him', 0),
    ('His', 'of him', 0),
    ("I'd", 'I would', 0),
    ("I'll", 'I will', 0),
    ("I'm", 'I am', 0),
    ('inhabit', 'dwell in', 1), # AMO 9:14
    ("isn't", 'is not', 1),
    ('Israeli', 'of Yisrāʼēl/Israel', 0),
    ('Israelis', 'of Yisrāʼēl/Israel', 0),
    ("It'll", 'It will', 0),
    ("it'll", 'it will', 0),
    ('its', 'of it', 0),
    ('Its', 'of it', 0),
    ("It's", 'It is', 0),
    ("it's", 'it is', 0),
    ("I've", 'I have', 0),
    ('kill', 'put to death', 2), # CH2 23:7
    ('killed', 'put to death', 3), # CO2 6:9
    ('killed', 'putting to death', 3), # EZE 13:19
    ('killing', 'put to death', 1), # GEN 18:25
    ('left','came out', 0),
    ('left','set out', 0),
    ("Let's", 'Let us', 0),
    ('listen','give ear', 2),
    ('Listen', 'give ear', 3), # ACT 2:14
    ('mounted','sat down', 0),
    ("mustn't", 'must not', 0),
    ('my', 'of me', 0),
    ('My', 'of me', 0),
    ('never','no means', 0), # Mrk 13:31
    ('our', 'of us', 0),
    ('Our', 'of us', 0),
    ('rest', 'lie down', 1), # EZE 34:15
    ('rest', 'lying down', 2), # PSA 139:3
    ('Return', 'go back', 1), # GEN 44:25
    ('return', 'turn back', 6), # DEU 30:2
    ('return', 'turned back', 6), # ISA 9:13
    ('returned', 'turned back', 4), # JOS 11:10
    ('returned', 'went back', 5), # GEN 44:13
    ('returning', 'went back', 1), # SA1 6:16
    ('sacred','of meeting', 2), # tent of meeting
    ("She'll", 'She will', 0),
    ("she'll", 'she will', 0),
    ("She's", 'She is', 0),
    ("she's", 'she is', 0),
    ("shouldn't", 'should not', 1),
    ('shout', 'cry out', 1), # JER 47:2
    ('shouted', 'cried out', 2), # JHN 11:43
    ('shouted', 'crying out', 3), # ACT 12:22
    ('shouting', 'crying out', 3), # ACT 21:34
    ('sleep', 'lie down', 0), # DEU 24:13
    ('slept', 'lay down', 0), # KI1 21:27
    ('something','one message', 0),
    ('thank', 'give thanks', 0), # CH1 16:4
    ('thank', 'gives thanks', 0), # ISA 38:18
    ('thank', 'giving thanks', 0), # CO1 1:14
    ('thanked', 'give thanks', 0), # CH1 25:3
    ('thanked', 'giving thanks', 0), # ACT 28:15
    ('thanking', 'giving thanks', 0), # CH1 29:13
    ('thanks', 'giving thanks', 0), # EPH 5:20
    ('thanksgiving', 'gave thanks', 0), # NEH 11:17
    ('thanksgiving', 'give thanks', 0), # CH2 31:2
    ("That's", 'That is', 0),
    ("that's", 'that is', 0),
    ('their', 'of them', 0),
    ('Their', 'of them', 0),
    ("There's", 'There is', 0),
    ("there's", 'there is', 0),
    ("There’s", 'There is', 0),
    ("They'd", 'They would', 0),
    ("they'd", 'they would', 0),
    ("They'd", 'They had', 0),
    ("They'll", 'They will', 0),
    ("they'll", 'they will', 0),
    ("They're", 'They are', 0),
    ("they're", 'they are', 0),
    ("They've", 'They have', 0),
    ("they've", 'they have', 0),
    ('understand', 'having an ear', 0),
    ('wants', 'having an ear', 0),
    ("wasn't", 'was not', 0),
    ('waters','water supplies', 0),
    ("We'd", 'We would', 0),
    ("we'd", 'we would', 0),
    ("We'll", 'We will', 0),
    ("we'll", 'we will', 0),
    ("We're", 'We are', 0),
    ("we're", 'we are', 0),
    ("weren't", 'were not', 0),
    ("We've", 'We have', 0),
    ("we've", 'we have', 0),
    ("What's", 'What is', 0),
    ("what's", 'what is', 0),
    ("When's", 'When is', 0),
    ("when's", 'when is', 0),
    ("Where's", 'Where is', 0),
    ("where's", 'where is', 0),
    ("Who's", 'Who is', 0),
    ("who's", 'who is', 0),
    ("Why's", 'Why is', 0),
    ("why's", 'why is', 0),
    ("won't", 'will not', 1),
    ('Worship', 'bow down', 1), # CH1 16:29
    ('worship', 'bow down', 2), # CH2 7:19
    ('worship', 'bowed down', 3), # SA2 15:32
    ('worship', 'paid homage', 4), # DAN 2:46
    ('worship', 'pay homage', 4), # DAN 3:5
    ('worship', 'paying homage', 4), # DAN 3:7
    ('worshipped', 'bowed down', 2), # CH2 7:22
    ('worshipping', 'bowing down', 1), # EZE 8:16
    ("wouldn't", 'would not', 0),
    ('yelled', 'cried out', 1),
    ('yelled', 'crying out', 3), # ACT 19:28
    ('yelling', 'cried out', 1), # ACT 7:57
    ('yelling', 'crying out', 2), # ACT 19:32
    ("you'd", 'you would', 0),
    ("You'd", 'You would', 0),
    ("You'll", 'You will', 0),
    ("you'll", 'you will', 0),
    ('your', 'of you', 0),
    ('Your', 'of you', 0),
    ("you're", 'you are', 0),
    ("You're", 'You are', 0),
    ("you've", 'you have', 0),
)
assert len({(rv, lv) for rv, lv, _ in RV_SINGLE_WORDS_FROM_LV_WORD_STRINGS}) == len(RV_SINGLE_WORDS_FROM_LV_WORD_STRINGS)
_phrasePriorities = {}
for someTuple in RV_SINGLE_WORDS_FROM_LV_WORD_STRINGS:
    assert isinstance(someTuple, tuple), f'{someTuple=}'
    RVWord, LVWords, wordsBefore = someTuple
    assert len(RVWord.split()) == 1, f'Expected a single RV word: {someTuple}'
    assert len(LVWords.split()) > 1, f'Expected an LV phrase: {someTuple}'
    assert '_' not in RVWord+LVWords, f'Use spaces between phrase words: {someTuple}'
    assert isinstance(wordsBefore, int) and wordsBefore >= _phrasePriorities.get(RVWord, 0), f'{someTuple=}'
    _phrasePriorities[RVWord] = wordsBefore


LV_SINGLE_WORDS_TO_RV_WORD_STRINGS = (
    ('afar','Further back'), # Mrk 15:40
    ('all', 'many people'),
    ('and', 'and also'),
    ('anymore','any more'), # Mrk 14:63
    ('approached','came closer'), # Mrk 12:28
    ('ascent','walking uphill'),
    ('ascertained','found out'), # Mat 2:16
    ('asked','find out'), # Mrk 15:44
    ('bore','was the father of'), # Mat 1
    ('bore','the father of'), # Mat 1
    ('brothers', 'brothers and sisters'),
    ('brothers', 'fellow believers'),
    ('Brothers', 'Brothers and sisters'),
    ('Brothers', 'Fellow believers'),
    ('Brothers', 'brothers and sisters'),
    ('Brothers', 'fellow believers'),
    ('deserted', 'quiet place'),
    ('false','making up'), # Mrk 14:56
    ('first','most important'), # Mrk 12:29
    ('fishers', 'fishers of men'),
    ('fled','ran away'), # Mrk 14:52, 16:8
    ('fled','took off running'), # Mrk 14:52, 16:8
    ('food','lived on'), # Mat 3:4
    ('forgiveness', 'have been forgiven'),
    ('greater','more important'), # Mrk 12:31
    ('Higgaion', 'Meditation break'),
    ('knowing','sleep with'), # Mat 1:25
    ('known', 'found out'), # Mrk 15:45
    ('members', 'body parts'),
    ('neighbouring', 'neighbouring villages'),
    ('one', 'one man'),
    ('pinnacle','highest point'), # MAT 4:5
    ('plagues', 'deadly diseases'),
    ('pre-day','day before'), # Mrk 15:42
    ('raised','came back to life'), # Mrk 16:6
    ('raised','Get ready'), # Mat 2:20
    ('raised','packed up'), # Mat 2:21
    ('repenting','Turn from'), # Mat 3:2
    ('right','honoured position'), # Mrk 14:62
    ('risen', 'got up'),
    ('sanctuary', 'sacred tent'),
    ('scribes', 'religious teachers'),
    ('seeking', 'looking for'), # Mrk 16:6
    ('Şelāh', 'Instrumental break'), # PSA & HAB
    ('shortly', 'soon after'),
    ('son', 'son of Zebedee'),
    ('synagogue', 'Jewish meeting hall'),
    ('synagogue', 'meeting hall'),
    ('synagogues', 'Jewish meeting halls'),
    ('synagogues', 'meeting halls'),
    ('tabernacle', 'sacred tent'),
    ('this', 'just happened'),
    ('three-times','three times'), # Mrk 14:72
    ('tomb','burial chamber'), # Mrk 15:46
    ('Truly', 'May it be so'),
    ('unblemished', 'no defects'),
    ('unblemished', 'without defects'),
)
assert len(set(LV_SINGLE_WORDS_TO_RV_WORD_STRINGS)) == len(LV_SINGLE_WORDS_TO_RV_WORD_STRINGS) # No duplicate mappings
for someTuple in LV_SINGLE_WORDS_TO_RV_WORD_STRINGS:
    assert isinstance( someTuple, tuple), f"{someTuple=}"
    LVWord,RVWords = someTuple
    assert LVWord != RVWords, f"{RVWords=}"
    assert len(LVWord.split()) == 1, f'Expected a single LV word: {someTuple}'
    assert len(RVWords.split()) > 1, f'Expected an RV phrase: {someTuple}'
