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
    ('accompanied', 'went with', 0), # RV JDG 4:9
    ('action', 'carry out', 2), # RV HOS 11:9
    ('alcohol', 'strong drink', 0), # RV DEU 29:6 / LV DEU 29:5
    ('ambush', 'lie in wait', 2), # RV PSA 59:3 / LV PSA 59:4
    ('ambush', 'lay in wait', 2), # RV JDG 9:34
    ('ambush', 'lying in wait', 2), # RV JOS 8:4
    ('ambushed', 'lay in wait', 0), # RV LAM 4:19
    ('ambushes', 'lie in wait', 2), # RV DEU 19:11
    ('ambushing', 'lying in wait', 0), # RV SA1 24:11 / LV SA1 24:12
    ('anything','all things', 0),
    ('approach', 'draw near', 1), # DEU 2:19
    ('approach', 'drawn near', 1), # ISA 41:5
    ('approach', 'drew near', 1), # EXO 14:20
    ('approached', 'drew near', 1), # DEU 4:11
    ('approaches', 'draw near', 0), # LEV 22:3
    ('Arouse', 'Wake up', 0), # RV PSA 35:23
    ('arrested', 'given over', 3),
    ('ascend', 'go up', 0), # PSA 24:3
    ('ascend', 'went up', 0), # EPH 4:9
    ('ascended', 'gone up', 0), # EPH 4:8
    ('ascended', 'went up', 0), # RV PSA 68:18 / LV PSA 68:19
    ('ascending', 'going up', 0), # GEN 28:12
    ('assemble', 'set up', 3), # RV EXO 26:30
    ('bed', 'lie with', 0), # RV GEN 39:7
    ('boxwood', 'box tree[s]', 0), # RV ISA 41:19
    ('bulge', 'comes out', 0), # RV PSA 73:7
    ('calms', 'makes quiet', 0), # RV PRO 15:18
    ("can't", 'can not', 1),
    ('chased', 'go after', 3), # RV RUT 3:10
    ('cheerfully', 'for joy', 1), # RV PSA 92:4 / LV PSA 92:5
    ('chief', 'chief priest', 0),
    ('climb', 'go up', 1), # RV EXO 8:3 / LV EXO 7:28
    ('Climb', 'Go up', 0), # RV DEU 32:49
    ('climb', 'goes up', 1), # RV PRO 21:22
    ('climb', 'gone up', 1), # RV ACT 8:31
    ('climbed', 'went up', 0), # RV EXO 17:10
    ('climbed', 'gone up', 0), # RV MAT 14:32
    ('climbs', 'going up', 0), # RV JHN 10:1
    ('closed', 'stopped up', 2), # RV NEH 4:7 / LV NEH 4:1
    ('collapse','passing away', 0), # Mrk 13:31
    ('collapsed', 'fell in', 0), # RV LUK 6:49
    ('collected', 'piled up', 2), # RV EXO 8:14 / LV EXO 8:10
    ('considered', 'looked at', 4), # RV NUM 23:21
    ("couldn't", 'could not', 0),
    ('cried', 'call out', 4), # RV PSA 119:145
    ('cross','pass over', 0),
    ('cross', 'passed over', 1), # RV DEU 2:14
    ('Cross', 'pass over', 0), # RV JOS 4:5
    ('cross', 'passes over', 1), # RV ISA 23:2
    ('crossed', 'passing over', 2), # RV JDG 8:4
    ('crosses', 'passes over', 0), # RV EXO 30:13
    ('crossing', 'passed over', 2), # RV JOS 3:1
    ('crossing', 'passing over', 2), # RV NUM 32:7
    ('dedicated', 'given over', 3), # RV ACT 15:26
    ('deflect', 'turn away', 0), # RV PRO 29:8
    ('deliver', 'giving birth', 0), # RV ISA 37:3
    ('demon', 'unclean spirit', 0),
    ('demons', 'unclean spirits', 0),
    ('depart', 'go out', 0), # GEN 31:13
    ('departed', 'went out', 4), # GEN 47:10
    ('departed', 'set out', 4), # RV EXO 19:2
    ('descend', 'come down', 0), # ISA 31:4
    ('descend', 'go down', 0), # ISA 5:14
    ('Descend', 'come down', 0), # RV SNG 4:8
    ('descended', 'came down', 0), # EPH 4:9
    ('descended', 'come down', 1), # EPH 4:10
    ('descended', 'went down', 2), # EXO 15:5
    ('descending', 'going down', 0), # GEN 28:12
    ('descending', 'coming down', 0), # RV SA1 10:5
    ("didn't", 'did not', 1),
    ('die','pass away', 0), # Mrk 13:30
    ('disappeared', 'went away', 0), # RV MRK 1:42
    ('disappears', 'melting away', 0), # RV PSA 58:8 / LV PSA 58:9
    ('discard', 'put away', 0), # RV HEB 12:1
    ('discovered', 'search out', 5), # RV PSA 44:21 / LV PSA 44:22
    ('dismiss', 'send away', 0), # RV MAT 19:3
    ('dismissed', 'sent away', 0), # RV ACT 23:22
    ('dismissed', 'send away', 0), # RV MAT 14:22
    ("doesn't", 'does not', 0),
    ("don't", 'do not', 1),
    ('draw', 'bring out', 1), # RV EZE 21:3 / LV EZE 21:8
    ('drawn', 'brought out', 0), # RV EZE 21:5 / LV EZE 21:10
    ('dying', 'passing away', 4), # RV PRO 31:8
    ('eliminate', 'wipe out', 2), # RV DEU 25:19
    ('emerge', 'come out', 0), # RV LUK 1:22
    ('enter', 'go in', 0),
    ('enter', 'came in', 0), # JHN 18:28
    ('enter', 'come in', 0), # HEB 3:19
    ('enter', 'coming in', 0), # HEB 3:18
    ('enter', 'went in', 0), # RV JER 7:2
    ('enter', 'gone into', 0), # RV DEU 18:9
    ('entered', 'came in', 1), # JHN 13:27
    ('entered', 'come in', 1), # ACT 10:25
    ('entered', 'go into', 1), # RV DEU 26:1
    ('entered', 'gone in', 1), # RV EZE 4:14
    ('entered', 'went in', 1), # RV EXO 24:18
    ('entered', 'gone into', 1), # RV JOB 38:22
    ('entering', 'come in', 0), # LUK 1:28
    ('entering', 'coming in', 0), # HEB 3:11
    ('entering', 'go into', 0), # RV NUM 32:9
    ('enters', 'coming in', 0), # JHN 10:1
    ('enters', 'come in', 0), # RV JER 9:21 / LV JER 9:20
    ('enters', 'goes into', 0), # RV LEV 14:46
    ('erase', 'wipe out', 0), # RV JER 18:23
    ('erase', 'wiping out', 0), # RV REV 3:5
    ('erased', 'wiped out', 0), # RV ACT 3:19
    ('erected', 'set up', 1), # RV CH2 33:3
    ('escaped', 'ran away', 3), # RV JDG 9:21
    ('establish', 'set up', 1), # RV AMO 5:15
    ('everyone','you all', 3),
    ('exclude', 'throw out', 0), # RV REV 11:2
    ('execute', 'put to death', 0), # RV ISA 11:4
    ('exited', 'went out', 0), # EST 8:15
    ('exiting', 'going out', 1), # EXO 19:1
    ('expecting', 'waiting for', 2), # RV ISA 64:3 / LV ISA 64:2
    ('expels', 'throwing out', 0), # RV JN3 1:10
    ('fall', 'go down', 2), # RV HAG 2:22
    ('fall', 'coming down', 2), # RV REV 13:13
    ('felled', 'cut down', 0), # RV ISA 9:10 / LV ISA 9:9
    ('finish', 'make an end', 3), # RV NUM 16:45 / LV NUM 17:10
    ('flee', 'take flight', 0), # RV JER 50:3
    ('follow', 'coming after', 4), # RV ACT 19:4
    ('follow', 'Come after', 4), # RV MAT 4:19
    ('followed', 'going behind', 3), # RV GEN 32:19 / LV GEN 32:20
    ('fought', 'engaged in battle', 2), # RV JOS 10:29
    ('fulfill', 'carry out', 0), # RV DEU 8:18
    ('gathered','coming together', 0), # Mrk 14:53
    ("God's", 'of god', 0),
    ("God’s", 'of god', 0),
    ('grab', 'take hold of', 3), # RV ZEC 14:13
    ('grab', 'taking hold of', 3), # RV MAT 12:11
    ('grows', 'coming out', 2), # RV KI1 4:33 / LV KI1 5:13
    ("hadn't", 'had not', 0),
    ('handed', 'turned over', 3), # RV CH1 10:14
    ('happens', 'fall out', 0), # RV RUT 3:18
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
    ('highest', 'Most High', 0), # RV PSA 83:18 / LV PSA 83:19
    ('his', 'of him', 0),
    ('His', 'of him', 0),
    ('holding', 'keeps back', 2), # RV PRO 21:26
    ('humble', 'bring low', 2), # RV DAN 4:37 / LV DAN 4:34
    ('humiliated', 'bringing low', 2), # RV DAN 5:19
    ("I'd", 'I would', 0),
    ("I'll", 'I will', 0),
    ("I'm", 'I am', 0),
    ('implement', 'carry out', 0), # RV JER 29:10
    ('incinerated', 'burn up', 1), # RV MAT 13:30
    ('inhabit', 'dwell in', 1), # AMO 9:14
    ('installing', 'set up', 0), # RV NEH 3:3
    ("isn't", 'is not', 1),
    ('Israeli', 'of Yisrāʼēl/Israel', 0),
    ('Israelis', 'of Yisrāʼēl/Israel', 0),
    ('Israelis', '>ones from Israaʸl/Yisrāʼēl', 0), # ACT 3:12: the demonym, not the earlier crowd (people).
    ('issue', 'go forth', 0), # RV EST 1:19
    ('issuing', 'going forth', 0), # RV DAN 9:25
    ("It'll", 'It will', 0),
    ("it'll", 'it will', 0),
    ('its', 'of it', 0),
    ('Its', 'of it', 0),
    ("It's", 'It is', 0),
    ("it's", 'it is', 0),
    ("I've", 'I have', 0),
    ('kept', 'held firm', 5), # RV PSA 17:5
    ('kill', 'put to death', 2), # CH2 23:7
    ('kill', 'cut off', 6), # RV EZE 21:3 / LV EZE 21:8
    ('killed', 'put to death', 3), # CO2 6:9
    ('killed', 'putting to death', 3), # EZE 13:19
    ('killing', 'put to death', 1), # GEN 18:25
    ('leave', 'pass on', 5), # RV GEN 18:5
    ('Leave', 'Go out', 2), # RV GEN 8:16
    ('leave', 'passed on', 5), # RV CH2 18:23
    ('leaves', 'goes out', 4), # RV PSA 41:6 / LV PSA 41:7
    ('leaves', 'go out', 4), # RV DEU 24:2
    ('leaves', 'goes forth', 4), # RV ISA 55:11
    ('leaves', 'going away', 4), # RV LUK 9:39
    ('leaving', 'goes out', 4), # RV CH2 16:1
    ('left','came out', 0),
    ('left','set out', 0),
    ("Let's", 'Let us', 0),
    ('lick', 'lap up', 0), # RV KI1 21:19
    ('licked', 'lapped up', 0), # RV KI1 21:19
    ('lift', 'bring up', 2), # RV EZE 37:12
    ('lifted', 'taken up', 1), # RV DAN 6:23 / LV DAN 6:24
    ('lifted', 'brought up', 1), # RV GEN 37:28
    ('listen','give ear', 2),
    ('Listen', 'give ear', 3), # ACT 2:14
    ('locked', 'shut up', 1), # RV JER 33:1
    ('lowered', 'let down', 0), # RV ACT 10:11
    ('lowered', 'brought down', 0), # RV GEN 44:11
    ('meetings', 'coming together', 0), # RV CO1 11:34
    ('minds', 'inner of being', 2), # RV PSA 62:4 / LV PSA 62:5
    ('mounted','sat down', 0),
    ('mounting', 'going up', 0), # RV GEN 31:10
    ('musicians', 'flute players', 0), # RV MAT 9:23
    ("mustn't", 'must not', 0),
    ('my', 'of me', 0),
    ('My', 'of me', 0),
    ('never','no means', 0), # Mrk 13:31
    ('obtained', 'took hold', 0), # RV CH2 7:22
    ('our', 'of us', 0),
    ('Our', 'of us', 0),
    ('produce', 'bring forth', 5), # RV ISA 55:10
    ('produces', 'brings forth', 1), # RV ISA 61:11
    ('producing', 'bringing out', 0), # RV HEB 6:8
    ('producing', 'brought out', 0), # RV NUM 14:37
    ('raged', 'in a tumult', 0), # RV PSA 46:6 / LV PSA 46:7
    ('raise', 'bring up', 2), # RV EZE 26:3
    ('raised', 'bring up', 2), # RV ISA 49:21
    ('raises', 'brings up', 0), # RV EZE 26:3
    ('refuse', 'turn away', 1), # RV KI1 2:16
    ('Rejoice', 'Shout for joy', 0), # RV PSA 33:1
    ('release', 'let go', 3), # RV EXO 9:28
    ('released', 'brought out', 3), # RV JER 20:3
    ('released', 'let go', 3), # RV EXO 13:17
    ('releases', 'let go', 1), # RV EXO 22:5 / LV EXO 22:4
    ('releasing', 'let go', 0), # RV JER 34:14
    ('remove', 'lift up', 2), # RV LEV 6:10 / LV LEV 6:3
    ('repaid', 'give back', 0), # RV LUK 12:59
    ('repay', 'bring back', 2), # RV PSA 54:5 / LV PSA 54:7
    ('repay', 'give back', 2), # RV LUK 7:42
    ('repay', 'giving back', 2), # RV MAT 18:29
    ('repaying', 'giving back', 0), # RV PE1 3:9
    ('repaying', 'give back', 0), # RV MAT 18:25
    ('reprimanded', 'gave rebuke', 0), # RV MRK 8:33
    ('rest', 'lie down', 1), # EZE 34:15
    ('rest', 'lying down', 2), # PSA 139:3
    ('Return', 'go back', 1), # GEN 44:25
    ('return', 'turn back', 6), # DEU 30:2
    ('return', 'turned back', 6), # ISA 9:13
    ('return', 'go back', 7), # RV GEN 43:13
    ('return', 'turning back', 7), # RV CH2 36:13
    ('returned', 'turned back', 4), # JOS 11:10
    ('returned', 'went back', 5), # GEN 44:13
    ('returned', 'brought back', 5), # RV JDG 17:4
    ('returning', 'went back', 1), # SA1 6:16
    ('returning', 'bring back', 1), # RV SA2 19:10 / LV SA2 19:11
    ('returning', 'brought back', 1), # RV SA2 16:8
    ('reversed', 'turn back', 0), # RV EZE 7:13
    ('rise', 'go up', 3), # RV ISA 40:31
    ('rise', 'come up', 3), # RV EXO 10:12
    ('rises', 'go up', 1), # RV JOB 20:6
    ('rising', 'went up', 0), # RV GEN 19:28
    ('rising', 'going up', 0), # RV REV 19:3
    ('rose', 'went up', 1), # RV ACT 10:4
    ('sacred','of meeting', 2), # tent of meeting
    ('safe', 'good care', 2), # RV SA1 22:23
    ('sank', 'went down', 0), # RV PSA 107:26
    ('scratched', 'made marks', 0), # RV SA1 21:13 / LV SA1 21:14
    ('season', 'appointed of time', 1), # RV HOS 2:9 / LV HOS 2:11
    ('seat', 'sat down', 2), # RV HEB 1:3
    ('seating', 'sit down', 0), # RV TH2 2:4
    ('severed', 'cut off', 0), # RV DEU 23:1 / LV DEU 23:2
    ("She'll", 'She will', 0),
    ("she'll", 'she will', 0),
    ("She's", 'She is', 0),
    ("she's", 'she is', 0),
    ('shortened', 'cut short', 0), # RV PSA 89:45 / LV PSA 89:46
    ("shouldn't", 'should not', 1),
    ('shout', 'cry out', 1), # JER 47:2
    ('shouted', 'cried out', 2), # JHN 11:43
    ('shouted', 'crying out', 3), # ACT 12:22
    ('shouting', 'crying out', 3), # ACT 21:34
    ('shouts', 'calling out', 2), # RV JER 49:21
    ('sleep', 'lie down', 0), # DEU 24:13
    ('slept', 'lay down', 0), # KI1 21:27
    ('smash', 'dash in pieces', 2), # RV KI2 8:12
    ('snap', 'tear apart', 0), # RV NAH 1:13
    ('something','one message', 0),
    ('start', 'take up', 1), # RV JER 9:18 / LV JER 9:17
    ('started', 'set out', 4), # RV GEN 46:1
    ('stop', 'put an end', 4), # RV NUM 17:5 / LV NUM 17:20
    ('Stop', 'turn back', 1), # RV KI2 18:14
    ('stop', 'turned back', 4), # RV KI1 13:33
    ('stopped', 'turned back', 5), # RV CH2 12:12
    ('strayed', 'turned aside', 1), # RV PSA 44:18 / LV PSA 44:19
    ('strip', 'laid bare', 0), # RV HAB 3:13
    ('summarised', 'summed up', 0), # RV ROM 13:9
    ('sunk', 'went down', 1), # RV PSA 104:8
    ('support', 'stand by', 3), # RV ACT 24:13
    ('surrounding', 'round about', 1), # RV JOL 3:11 / LV JOL 4:11
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
    ('threw', 'shook off', 1), # RV PSA 136:15
    ('together', 'one another', 0), # RV PSA 85:10 / LV PSA 85:11
    ('trim', 'cut off', 0), # RV JER 9:26 / LV JER 9:25
    ('turn', 'bend down', 6), # RV JOS 24:23
    ('understand', 'having an ear', 0),
    ('undressed', 'stripping off', 0), # RV NEH 4:23 / LV NEH 4:17
    ('wants', 'having an ear', 0),
    ("wasn't", 'was not', 0),
    ('watch', 'look on', 3), # RV GEN 21:16
    ('waters','water supplies', 0),
    ('weak', 'faints away', 2), # RV PSA 142:3 / LV PSA 142:4
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
    ('withdraw', 'draw back', 1), # RV PSA 74:11
    ("won't", 'will not', 1),
    ('worn-out', 'worn out', 0), # RV JOS 9:13
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
    ('yelled', 'Crying out', 4), # RV ACT 22:23
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
