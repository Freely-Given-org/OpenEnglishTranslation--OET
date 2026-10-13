# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023-2026 Robert Hunt
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Directional mappings involving actual multiword phrases.

RV_SINGLE_WORDS_FROM_LV_WORD_STRINGS rows are (RV word, LV phrase).
LV_SINGLE_WORDS_TO_RV_WORD_STRINGS rows are (LV word, RV multiword phrase).
Both tables are alphabetised by the single word in the first column, ignoring
case, punctuation and diacritics. The mappings are directional; never reverse
rows automatically. Matching ignores sentence case and compares all eligible
alternatives in one alignment graph. Table order does not choose a winner.
The old words_before priority column was removed with the direct-write matcher.
The optional OET-RV_wordPhrases_table.tsv is still loaded by the main script.
"""

RV_SINGLE_WORDS_FROM_LV_WORD_STRINGS = (
    ('120', 'a hundred twenty'),
    ('accompanied', 'went with'), # RV JDG 4:9
    ('action', 'carry out'), # RV HOS 11:9
    ('alcohol', 'strong drink'), # RV DEU 29:6 / LV DEU 29:5
    ('ambush', 'lie in wait'), # RV PSA 59:3 / LV PSA 59:4
    ('ambush', 'lay in wait'), # RV JDG 9:34
    ('ambush', 'lying in wait'), # RV JOS 8:4
    ('ambushed', 'lay in wait'), # RV LAM 4:19
    ('ambushes', 'lie in wait'), # RV DEU 19:11
    ('ambushing', 'lying in wait'), # RV SA1 24:11 / LV SA1 24:12
    ('anything','all things'),
    ('approach', 'draw near'), # DEU 2:19
    ('approach', 'drawn near'), # ISA 41:5
    ('approach', 'drew near'), # EXO 14:20
    ('approached', 'drew near'), # DEU 4:11
    ('approaches', 'draw near'), # LEV 22:3
    ('Arouse', 'Wake up'), # RV PSA 35:23
    ('arrested', 'given over'),
    ('ascend', 'go up'), # PSA 24:3
    ('ascend', 'went up'), # EPH 4:9
    ('ascended', 'gone up'), # EPH 4:8
    ('ascended', 'went up'), # RV PSA 68:18 / LV PSA 68:19
    ('ascending', 'going up'), # GEN 28:12
    ('assemble', 'set up'), # RV EXO 26:30
    ('bed', 'lie with'), # RV GEN 39:7
    ('boxwood', 'box tree[s]'), # RV ISA 41:19
    ('bulge', 'comes out'), # RV PSA 73:7
    ('calms', 'makes quiet'), # RV PRO 15:18
    ("can't", 'can not'),
    ('chased', 'go after'), # RV RUT 3:10
    ('cheerfully', 'for joy'), # RV PSA 92:4 / LV PSA 92:5
    ('chief', 'chief priest'),
    ('climb', 'go up'), # RV EXO 8:3 / LV EXO 7:28
    ('Climb', 'Go up'), # RV DEU 32:49
    ('climb', 'goes up'), # RV PRO 21:22
    ('climb', 'gone up'), # RV ACT 8:31
    ('climbed', 'went up'), # RV EXO 17:10
    ('climbed', 'gone up'), # RV MAT 14:32
    ('climbs', 'going up'), # RV JHN 10:1
    ('closed', 'stopped up'), # RV NEH 4:7 / LV NEH 4:1
    ('collapse','passing away'), # Mrk 13:31
    ('collapsed', 'fell in'), # RV LUK 6:49
    ('collected', 'piled up'), # RV EXO 8:14 / LV EXO 8:10
    ('considered', 'looked at'), # RV NUM 23:21
    ("couldn't", 'could not'),
    ('cried', 'call out'), # RV PSA 119:145
    ('cross','pass over'),
    ('cross', 'passed over'), # RV DEU 2:14
    ('Cross', 'pass over'), # RV JOS 4:5
    ('cross', 'passes over'), # RV ISA 23:2
    ('crossed', 'passing over'), # RV JDG 8:4
    ('crosses', 'passes over'), # RV EXO 30:13
    ('crossing', 'passed over'), # RV JOS 3:1
    ('crossing', 'passing over'), # RV NUM 32:7
    ('dedicated', 'given over'), # RV ACT 15:26
    ('deflect', 'turn away'), # RV PRO 29:8
    ('deliver', 'giving birth'), # RV ISA 37:3
    ('demon', 'unclean spirit'),
    ('demons', 'unclean spirits'),
    ('depart', 'go out'), # GEN 31:13
    ('departed', 'went out'), # GEN 47:10
    ('departed', 'set out'), # RV EXO 19:2
    ('descend', 'come down'), # ISA 31:4
    ('descend', 'go down'), # ISA 5:14
    ('Descend', 'come down'), # RV SNG 4:8
    ('descended', 'came down'), # EPH 4:9
    ('descended', 'come down'), # EPH 4:10
    ('descended', 'went down'), # EXO 15:5
    ('descending', 'going down'), # GEN 28:12
    ('descending', 'coming down'), # RV SA1 10:5
    ("didn't", 'did not'),
    ('die','pass away'), # Mrk 13:30
    ('disappeared', 'went away'), # RV MRK 1:42
    ('disappears', 'melting away'), # RV PSA 58:8 / LV PSA 58:9
    ('discard', 'put away'), # RV HEB 12:1
    ('discovered', 'search out'), # RV PSA 44:21 / LV PSA 44:22
    ('dismiss', 'send away'), # RV MAT 19:3
    ('dismissed', 'sent away'), # RV ACT 23:22
    ('dismissed', 'send away'), # RV MAT 14:22
    ("doesn't", 'does not'),
    ("don't", 'do not'),
    ('draw', 'bring out'), # RV EZE 21:3 / LV EZE 21:8
    ('drawn', 'brought out'), # RV EZE 21:5 / LV EZE 21:10
    ('dying', 'passing away'), # RV PRO 31:8
    ('eliminate', 'wipe out'), # RV DEU 25:19
    ('emerge', 'come out'), # RV LUK 1:22
    ('enter', 'go in'),
    ('enter', 'came in'), # JHN 18:28
    ('enter', 'come in'), # HEB 3:19
    ('enter', 'coming in'), # HEB 3:18
    ('enter', 'went in'), # RV JER 7:2
    ('enter', 'gone into'), # RV DEU 18:9
    ('entered', 'came in'), # JHN 13:27
    ('entered', 'come in'), # ACT 10:25
    ('entered', 'go into'), # RV DEU 26:1
    ('entered', 'gone in'), # RV EZE 4:14
    ('entered', 'went in'), # RV EXO 24:18
    ('entered', 'gone into'), # RV JOB 38:22
    ('entering', 'come in'), # LUK 1:28
    ('entering', 'coming in'), # HEB 3:11
    ('entering', 'go into'), # RV NUM 32:9
    ('enters', 'coming in'), # JHN 10:1
    ('enters', 'come in'), # RV JER 9:21 / LV JER 9:20
    ('enters', 'goes into'), # RV LEV 14:46
    ('erase', 'wipe out'), # RV JER 18:23
    ('erase', 'wiping out'), # RV REV 3:5
    ('erased', 'wiped out'), # RV ACT 3:19
    ('erected', 'set up'), # RV CH2 33:3
    ('escaped', 'ran away'), # RV JDG 9:21
    ('establish', 'set up'), # RV AMO 5:15
    ('everyone','you all'),
    ('exclude', 'throw out'), # RV REV 11:2
    ('execute', 'put to death'), # RV ISA 11:4
    ('exited', 'went out'), # EST 8:15
    ('exiting', 'going out'), # EXO 19:1
    ('expecting', 'waiting for'), # RV ISA 64:3 / LV ISA 64:2
    ('expels', 'throwing out'), # RV JN3 1:10
    ('fall', 'go down'), # RV HAG 2:22
    ('fall', 'coming down'), # RV REV 13:13
    ('felled', 'cut down'), # RV ISA 9:10 / LV ISA 9:9
    ('finish', 'make an end'), # RV NUM 16:45 / LV NUM 17:10
    ('flee', 'take flight'), # RV JER 50:3
    ('follow', 'coming after'), # RV ACT 19:4
    ('follow', 'Come after'), # RV MAT 4:19
    ('followed', 'going behind'), # RV GEN 32:19 / LV GEN 32:20
    ('fought', 'engaged in battle'), # RV JOS 10:29
    ('fulfill', 'carry out'), # RV DEU 8:18
    ('gathered','coming together'), # Mrk 14:53
    ("God's", 'of god'),
    ("God’s", 'of god'),
    ('grab', 'take hold of'), # RV ZEC 14:13
    ('grab', 'taking hold of'), # RV MAT 12:11
    ('grows', 'coming out'), # RV KI1 4:33 / LV KI1 5:13
    ("hadn't", 'had not'),
    ('handed', 'turned over'), # RV CH1 10:14
    ('happens', 'fall out'), # RV RUT 3:18
    ("hasn't", 'has not'),
    ("haven't", 'have not'),
    ('Hear', 'give ear'), # PSA 78:1
    ('hear', 'give ear'), # PSA 77:1
    ("He'd", 'He would'),
    ("he'd", 'he would'),
    ("He'd", 'He had'),
    ("He'll", 'He will'),
    ("He'll", 'he will'),
    ("he'll", 'he will'),
    ('her', 'of her'),
    ('Her', 'of her'),
    ("Here's", 'Here is'),
    ("here's", 'here is'),
    ("He's", 'He is'),
    ("he's", 'he is'),
    ('highest', 'Most High'), # RV PSA 83:18 / LV PSA 83:19
    ('his', 'of him'),
    ('His', 'of him'),
    ('holding', 'keeps back'), # RV PRO 21:26
    ('humble', 'bring low'), # RV DAN 4:37 / LV DAN 4:34
    ('humiliated', 'bringing low'), # RV DAN 5:19
    ("I'd", 'I would'),
    ("I'll", 'I will'),
    ("I'm", 'I am'),
    ('implement', 'carry out'), # RV JER 29:10
    ('incinerated', 'burn up'), # RV MAT 13:30
    ('inhabit', 'dwell in'), # AMO 9:14
    ('installing', 'set up'), # RV NEH 3:3
    ("isn't", 'is not'),
    ('Israeli', 'of Yisrāʼēl/Israel'),
    ('Israelis', 'of Yisrāʼēl/Israel'),
    ('Israelis', '>ones from Israaʸl/Yisrāʼēl'), # ACT 3:12: the demonym, not the earlier crowd (people).
    ('issue', 'go forth'), # RV EST 1:19
    ('issuing', 'going forth'), # RV DAN 9:25
    ("It'll", 'It will'),
    ("it'll", 'it will'),
    ('its', 'of it'),
    ('Its', 'of it'),
    ("It's", 'It is'),
    ("it's", 'it is'),
    ("I've", 'I have'),
    ('kept', 'held firm'), # RV PSA 17:5
    ('kill', 'put to death'), # CH2 23:7
    ('kill', 'cut off'), # RV EZE 21:3 / LV EZE 21:8
    ('killed', 'put to death'), # CO2 6:9
    ('killed', 'putting to death'), # EZE 13:19
    ('killing', 'put to death'), # GEN 18:25
    ('leave', 'pass on'), # RV GEN 18:5
    ('Leave', 'Go out'), # RV GEN 8:16
    ('leave', 'passed on'), # RV CH2 18:23
    ('leaves', 'goes out'), # RV PSA 41:6 / LV PSA 41:7
    ('leaves', 'go out'), # RV DEU 24:2
    ('leaves', 'goes forth'), # RV ISA 55:11
    ('leaves', 'going away'), # RV LUK 9:39
    ('leaving', 'goes out'), # RV CH2 16:1
    ('left','came out'),
    ('left','set out'),
    ("Let's", 'Let us'),
    ('lick', 'lap up'), # RV KI1 21:19
    ('licked', 'lapped up'), # RV KI1 21:19
    ('lift', 'bring up'), # RV EZE 37:12
    ('lifted', 'taken up'), # RV DAN 6:23 / LV DAN 6:24
    ('lifted', 'brought up'), # RV GEN 37:28
    ('listen','give ear'),
    ('Listen', 'give ear'), # ACT 2:14
    ('locked', 'shut up'), # RV JER 33:1
    ('lowered', 'let down'), # RV ACT 10:11
    ('lowered', 'brought down'), # RV GEN 44:11
    ('meetings', 'coming together'), # RV CO1 11:34
    ('minds', 'inner of being'), # RV PSA 62:4 / LV PSA 62:5
    ('mounted','sat down'),
    ('mounting', 'going up'), # RV GEN 31:10
    ('musicians', 'flute players'), # RV MAT 9:23
    ("mustn't", 'must not'),
    ('my', 'of me'),
    ('My', 'of me'),
    ('never','no means'), # Mrk 13:31
    ('obtained', 'took hold'), # RV CH2 7:22
    ('our', 'of us'),
    ('Our', 'of us'),
    ('produce', 'bring forth'), # RV ISA 55:10
    ('produces', 'brings forth'), # RV ISA 61:11
    ('producing', 'bringing out'), # RV HEB 6:8
    ('producing', 'brought out'), # RV NUM 14:37
    ('raged', 'in a tumult'), # RV PSA 46:6 / LV PSA 46:7
    ('raise', 'bring up'), # RV EZE 26:3
    ('raised', 'bring up'), # RV ISA 49:21
    ('raises', 'brings up'), # RV EZE 26:3
    ('refuse', 'turn away'), # RV KI1 2:16
    ('Rejoice', 'Shout for joy'), # RV PSA 33:1
    ('release', 'let go'), # RV EXO 9:28
    ('released', 'brought out'), # RV JER 20:3
    ('released', 'let go'), # RV EXO 13:17
    ('releases', 'let go'), # RV EXO 22:5 / LV EXO 22:4
    ('releasing', 'let go'), # RV JER 34:14
    ('remove', 'lift up'), # RV LEV 6:10 / LV LEV 6:3
    ('repaid', 'give back'), # RV LUK 12:59
    ('repay', 'bring back'), # RV PSA 54:5 / LV PSA 54:7
    ('repay', 'give back'), # RV LUK 7:42
    ('repay', 'giving back'), # RV MAT 18:29
    ('repaying', 'giving back'), # RV PE1 3:9
    ('repaying', 'give back'), # RV MAT 18:25
    ('reprimanded', 'gave rebuke'), # RV MRK 8:33
    ('rest', 'lie down'), # EZE 34:15
    ('rest', 'lying down'), # PSA 139:3
    ('Return', 'go back'), # GEN 44:25
    ('return', 'turn back'), # DEU 30:2
    ('return', 'turned back'), # ISA 9:13
    ('return', 'go back'), # RV GEN 43:13
    ('return', 'turning back'), # RV CH2 36:13
    ('returned', 'turned back'), # JOS 11:10
    ('returned', 'went back'), # GEN 44:13
    ('returned', 'brought back'), # RV JDG 17:4
    ('returning', 'went back'), # SA1 6:16
    ('returning', 'bring back'), # RV SA2 19:10 / LV SA2 19:11
    ('returning', 'brought back'), # RV SA2 16:8
    ('reversed', 'turn back'), # RV EZE 7:13
    ('rise', 'go up'), # RV ISA 40:31
    ('rise', 'come up'), # RV EXO 10:12
    ('rises', 'go up'), # RV JOB 20:6
    ('rising', 'went up'), # RV GEN 19:28
    ('rising', 'going up'), # RV REV 19:3
    ('rose', 'went up'), # RV ACT 10:4
    ('sacred','of meeting'), # tent of meeting
    ('safe', 'good care'), # RV SA1 22:23
    ('sank', 'went down'), # RV PSA 107:26
    ('scratched', 'made marks'), # RV SA1 21:13 / LV SA1 21:14
    ('season', 'appointed of time'), # RV HOS 2:9 / LV HOS 2:11
    ('seat', 'sat down'), # RV HEB 1:3
    ('seating', 'sit down'), # RV TH2 2:4
    ('severed', 'cut off'), # RV DEU 23:1 / LV DEU 23:2
    ("She'll", 'She will'),
    ("she'll", 'she will'),
    ("She's", 'She is'),
    ("she's", 'she is'),
    ('shortened', 'cut short'), # RV PSA 89:45 / LV PSA 89:46
    ("shouldn't", 'should not'),
    ('shout', 'cry out'), # JER 47:2
    ('shouted', 'cried out'), # JHN 11:43
    ('shouted', 'crying out'), # ACT 12:22
    ('shouting', 'crying out'), # ACT 21:34
    ('shouts', 'calling out'), # RV JER 49:21
    ('sleep', 'lie down'), # DEU 24:13
    ('slept', 'lay down'), # KI1 21:27
    ('smash', 'dash in pieces'), # RV KI2 8:12
    ('snap', 'tear apart'), # RV NAH 1:13
    ('something','one message'),
    ('start', 'take up'), # RV JER 9:18 / LV JER 9:17
    ('started', 'set out'), # RV GEN 46:1
    ('stop', 'put an end'), # RV NUM 17:5 / LV NUM 17:20
    ('Stop', 'turn back'), # RV KI2 18:14
    ('stop', 'turned back'), # RV KI1 13:33
    ('stopped', 'turned back'), # RV CH2 12:12
    ('strayed', 'turned aside'), # RV PSA 44:18 / LV PSA 44:19
    ('strip', 'laid bare'), # RV HAB 3:13
    ('summarised', 'summed up'), # RV ROM 13:9
    ('sunk', 'went down'), # RV PSA 104:8
    ('support', 'stand by'), # RV ACT 24:13
    ('surrounding', 'round about'), # RV JOL 3:11 / LV JOL 4:11
    ('thank', 'give thanks'), # CH1 16:4
    ('thank', 'gives thanks'), # ISA 38:18
    ('thank', 'giving thanks'), # CO1 1:14
    ('thanked', 'give thanks'), # CH1 25:3
    ('thanked', 'giving thanks'), # ACT 28:15
    ('thanking', 'giving thanks'), # CH1 29:13
    ('thanks', 'giving thanks'), # EPH 5:20
    ('thanksgiving', 'gave thanks'), # NEH 11:17
    ('thanksgiving', 'give thanks'), # CH2 31:2
    ("That's", 'That is'),
    ("that's", 'that is'),
    ('their', 'of them'),
    ('Their', 'of them'),
    ("There's", 'There is'),
    ("there's", 'there is'),
    ("There’s", 'There is'),
    ("They'd", 'They would'),
    ("they'd", 'they would'),
    ("They'd", 'They had'),
    ("They'll", 'They will'),
    ("they'll", 'they will'),
    ("They're", 'They are'),
    ("they're", 'they are'),
    ("They've", 'They have'),
    ("they've", 'they have'),
    ('threw', 'shook off'), # RV PSA 136:15
    ('together', 'one another'), # RV PSA 85:10 / LV PSA 85:11
    ('trim', 'cut off'), # RV JER 9:26 / LV JER 9:25
    ('turn', 'bend down'), # RV JOS 24:23
    ('understand', 'having an ear'),
    ('undressed', 'stripping off'), # RV NEH 4:23 / LV NEH 4:17
    ('wants', 'having an ear'),
    ("wasn't", 'was not'),
    ('watch', 'look on'), # RV GEN 21:16
    ('waters','water supplies'),
    ('weak', 'faints away'), # RV PSA 142:3 / LV PSA 142:4
    ("We'd", 'We would'),
    ("we'd", 'we would'),
    ("We'll", 'We will'),
    ("we'll", 'we will'),
    ("We're", 'We are'),
    ("we're", 'we are'),
    ("weren't", 'were not'),
    ("We've", 'We have'),
    ("we've", 'we have'),
    ("What's", 'What is'),
    ("what's", 'what is'),
    ("When's", 'When is'),
    ("when's", 'when is'),
    ("Where's", 'Where is'),
    ("where's", 'where is'),
    ("Who's", 'Who is'),
    ("who's", 'who is'),
    ("Why's", 'Why is'),
    ("why's", 'why is'),
    ('withdraw', 'draw back'), # RV PSA 74:11
    ("won't", 'will not'),
    ('worn-out', 'worn out'), # RV JOS 9:13
    ('Worship', 'bow down'), # CH1 16:29
    ('worship', 'bow down'), # CH2 7:19
    ('worship', 'bowed down'), # SA2 15:32
    ('worship', 'paid homage'), # DAN 2:46
    ('worship', 'pay homage'), # DAN 3:5
    ('worship', 'paying homage'), # DAN 3:7
    ('worshipped', 'bowed down'), # CH2 7:22
    ('worshipping', 'bowing down'), # EZE 8:16
    ("wouldn't", 'would not'),
    ('yelled', 'cried out'),
    ('yelled', 'crying out'), # ACT 19:28
    ('yelled', 'Crying out'), # RV ACT 22:23
    ('yelling', 'cried out'), # ACT 7:57
    ('yelling', 'crying out'), # ACT 19:32
    ("you'd", 'you would'),
    ("You'd", 'You would'),
    ("You'll", 'You will'),
    ("you'll", 'you will'),
    ('your', 'of you'),
    ('Your', 'of you'),
    ("you're", 'you are'),
    ("You're", 'You are'),
    ("you've", 'you have'),
)
assert len({(rv, lv) for rv, lv in RV_SINGLE_WORDS_FROM_LV_WORD_STRINGS}) == len(RV_SINGLE_WORDS_FROM_LV_WORD_STRINGS)
for someTuple in RV_SINGLE_WORDS_FROM_LV_WORD_STRINGS:
    assert isinstance(someTuple, tuple), f'{someTuple=}'
    RVWord, LVWords = someTuple
    assert len(RVWord.split()) == 1, f'Expected a single RV word: {someTuple}'
    assert len(LVWords.split()) > 1, f'Expected an LV phrase: {someTuple}'
    assert '_' not in RVWord+LVWords, f'Use spaces between phrase words: {someTuple}'


LV_SINGLE_WORDS_TO_RV_WORD_STRINGS = (
    ('afar','Further back'), # Mrk 15:40
    ('all', 'many people'),
    ('and', 'and also'),
    ('anymore','any more'), # Mrk 14:63
    ('approached','came closer'), # Mrk 12:28
    ('approaching', 'come near'), # RV EZE 45:4
    ('ascent','walking uphill'),
    ('ascertained','found out'), # Mat 2:16
    ('asked','find out'), # Mrk 15:44
    ('attend', 'take care'), # RV PSA 80:14 / LV PSA 80:15
    ('avenging', 'take revenge'), # RV ROM 12:19
    ('bastard', 'illegitimate child'), # RV DEU 23:2 / LV DEU 23:3
    ('before','in front of'), # Mat 4:9
    ('Beloved', 'Dear friends'), # RV JN1 2:7
    ('Beloved', 'dear friends'), # RV JN1 3:21
    ('beloved', 'Dear friends'), # RV ROM 12:19
    ('bore','was the father of'), # Mat 1
    ('bore','the father of'), # Mat 1
    ('bound', 'held captive'), # RV SNG 7:5 / LV SNG 7:6
    ('brothers', 'brothers and sisters'),
    ('brothers', 'fellow believers'),
    ('Brothers', 'Brothers and sisters'),
    ('Brothers', 'Fellow believers'),
    ('Brothers', 'brothers and sisters'),
    ('Brothers', 'fellow believers'),
    ('censer', 'incense burner'), # RV NUM 16:46 / LV NUM 17:11
    ('Consider', 'Take note'), # RV PSA 25:18
    ('Consider', 'Think about'), # RV MAT 6:26
    ('consider', 'think about'), # RV HEB 12:3
    ('delaying', 'held up'), # RV MAT 25:5
    ('delight', 'take pleasure'), # RV JER 9:24 / LV JER 9:23
    ('deserted', 'quiet place'),
    ('died', 'passed away'), # RV LUK 8:49
    ('earthenware', 'piece of fired clay'), # RV PSA 22:15 / LV PSA 22:16
    ('elders', 'older men'), # RV CH2 10:6
    ('exalted', 'lifted up'), # RV PSA 57:5 / LV PSA 57:6
    ('false','making up'), # Mrk 14:56
    ('first','most important'), # Mrk 12:29
    ('fishers', 'fishers of men'),
    ('fled','ran away'), # Mrk 14:52, 16:8
    ('fled','took off running'), # Mrk 14:52, 16:8
    ('flees', 'fly away'), # RV NAH 3:17
    ('food','lived on'), # Mat 3:4
    ('foolish', 'less sensible'), # MAT 25:8: the modifier changes the sense of 'sensible'.
    ('forgiveness', 'have been forgiven'),
    ('give', 'pass on'), # RV ACT 7:38
    ('greater','more important'), # Mrk 12:31
    ('guard/protect', 'look after'), # RV EXO 22:10 / LV EXO 22:9
    ('handmaiden', 'servant girl'), # RV LUK 1:38
    ('heavy', 'big strain'), # RV JN1 5:3
    ('Higgaion', 'Meditation break'),
    ('king', 'your majesty'), # RV DAN 4:22 / LV DAN 4:19
    ('knowing','sleep with'), # Mat 1:25
    ('known', 'found out'), # Mrk 15:45
    ('members', 'body parts'),
    ('menstruation', 'menstrual period'), # RV EZE 22:10
    ('neighbouring', 'neighbouring villages'),
    ('observes', 'take notice'), # RV JOB 35:13
    ('one', 'one man'),
    ('outcry', 'crying out'), # RV GEN 18:20
    ('overtake', 'catch up'), # RV HOS 2:7 / LV HOS 2:9
    ('overtook', 'caught up'), # RV GEN 31:25
    ('pinnacle','highest point'), # MAT 4:5
    ('plagues', 'deadly diseases'),
    ('pre-day','day before'), # Mrk 15:42
    ('raised','came back to life'), # Mrk 16:6
    ('raised','Get ready'), # Mat 2:20
    ('raised','packed up'), # Mat 2:21
    ('Remember', 'Think about'), # RV ISA 46:9
    ('remember', 'Think about'), # RV ECC 12:1
    ('remembering', 'think about'), # RV HEB 2:6
    ('repenting','Turn from'), # Mat 3:2
    ('return', 'give back'), # RV PSA 69:4 / LV PSA 69:5
    ('right','honoured position'), # Mrk 14:62
    ('risen', 'got up'),
    ('sanctuary', 'sacred tent'),
    ('scribes', 'religious teachers'),
    ('seeking', 'looking for'), # Mrk 16:6
    ('Şelāh', 'Instrumental break'), # PSA & HAB
    ('separate', 'single out'), # RV DEU 29:21 / LV DEU 29:20
    ('serving','looked after'), # Mat 4:11
    ('shortly', 'soon after'),
    ('shouting', 'call out'), # RV LUK 18:7
    ('shouting', 'cry out'), # RV ZEP 1:14
    ('signet-rings', 'signet rings'), # RV DAN 6:17 / LV DAN 6:18
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
    ('virgin', 'young woman'), # RV EXO 22:16 / LV EXO 22:15
    ('visit', 'look after'), # RV PSA 65:9 / LV PSA 65:10
    ('waiting', 'look forward'), # RV JDE 1:21
    ('waken', 'wake up'), # RV PSA 57:8 / LV PSA 57:9
)
assert len(set(LV_SINGLE_WORDS_TO_RV_WORD_STRINGS)) == len(LV_SINGLE_WORDS_TO_RV_WORD_STRINGS) # No duplicate mappings
for someTuple in LV_SINGLE_WORDS_TO_RV_WORD_STRINGS:
    assert isinstance( someTuple, tuple), f"{someTuple=}"
    LVWord,RVWords = someTuple
    assert LVWord != RVWords, f"{RVWords=}"
    assert len(LVWord.split()) == 1, f'Expected a single LV word: {someTuple}'
    assert len(RVWords.split()) > 1, f'Expected an RV phrase: {someTuple}'
