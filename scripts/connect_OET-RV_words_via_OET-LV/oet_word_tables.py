# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023-2026 Robert Hunt
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Simple vocabulary and single-word mappings for RV/LV matching.

SIMPLE_WORDS combines the noun and verb tables with the smaller lists below.
SINGLE_WORD_MAPPINGS is the one maintained list of single-word correspondences:
    (RV word, LV word) preserves direction; selection ignores sentence case.
    (word, word, 'aligned') supports normalised, bidirectional positional matching.
    (RV word, LV word, 'both') permits both symmetric alignment and directional recovery.
The positional pass can distinguish repeated occurrences of directional pairs,
at a lower score than identical words, inflections and symmetric alternatives.
Verse-wide lexical recovery requires mutually unique matches. Do not make directional
pairs symmetric or expand them transitively.

Rows are alphabetised by the first word, ignoring case, punctuation and
diacritics. All alternatives compete on evidence and context, not row order.
The two working lookups EQUIVALENT_LV_RV_WORDS and RV_SINGLE_WORDS_FROM_LV_WORDS
are derived from this list; edit SINGLE_WORD_MAPPINGS, not those lookups.
These modules contain data and validation only, with no Bible loading.

Review new pairs in mapped passages, including repeated occurrences and other
senses of each word. A missing entry (e.g. weightier -> heavier, MAT 23:23) is
different from an unresolved alignment: adding vocabulary must not force a
choice between indistinguishable source occurrences. Co-occurrence alone is
not evidence of equivalence, and idioms belong in the phrase table.
"""

from oet_noun_tables import SIMPLE_NOUNS_FLAT, verbalNouns
from oet_verb_tables import SIMPLE_VERB_SETS, simpleVerbs

simpleAdverbs = (
    'again', 'certainly', 'even', 'immediately', 'indeed',
    'loudly', 'now', 'only', 'perhaps', 'quickly',
    'still', 'suddenly', 'then',
)
assert len(set(simpleAdverbs)) == len(simpleAdverbs) # Check for accidental duplicates

simpleAdjectives = (
    'alive', 'angry', 'bad', 'big', 'bitter',
    'blameless', 'blind', 'clean', 'cold', 'dangerous',
    'dead', 'disobedient', 'entire', 'eternal', 'evil',
    'female', 'foolish', 'foreign', 'friendly', 'full',
    'godly', 'golden', 'good', 'great', 'happy',
    'heavy', 'high', 'impossible', 'large', 'little',
    'local', 'long', 'loud', 'male', 'mighty',
    'naked', 'new', 'numerous', 'obedient', 'old',
    'opposite', 'possible', 'precious', 'ready', 'sad',
    'same', 'sick', 'similar', 'small', 'spiritual',
    'sudden', 'sweet', 'unleavened', 'whole', 'wide',
    'wild', 'wounded',
)
assert len(set(simpleAdjectives)) == len(simpleAdjectives) # Check for accidental duplicates

# Numbers retain numerical order, followed by the non-numeric alternative 'none'.
# Don't use 'one' below because it has other meanings.
simpleNumbers = ('two','three','four','five','six','seven','eight','nine',
                    'ten','eleven','twelve','thirteen','fourteen','fifteen','sixteen','seventeen','eighteen','nineteen',
                    'twenty','thirty','forty','fifty','sixty','seventy','eighty','ninety',
                    'none')
assert len(set(simpleNumbers)) == len(simpleNumbers) # Check for accidental duplicates

pronouns = (
    'everyone', 'he', 'her', 'herself', 'him',
    'himself', 'it', 'its', 'itself', 'our',
    'ourselves', 'she', 'their', 'themselves', 'they',
    'we', 'you', 'your', 'yourself', 'yourselves',
)
assert len(set(pronouns)) == len(pronouns) # Check for accidental duplicates

# We don't expect connectors to work very well
connectors = (
    'and', 'but',
)
assert len(set(connectors)) == len(connectors) # Check for accidental duplicates

# Parts of speech can overlap; the matcher needs each spelling only once.
SIMPLE_WORDS = tuple(dict.fromkeys(
    SIMPLE_NOUNS_FLAT + verbalNouns + simpleVerbs + simpleAdverbs + simpleAdjectives
    + simpleNumbers + pronouns + connectors
))


# Single-word correspondences, alphabetised by the first word.
# Two-column rows keep their RV -> LV direction.
# 'aligned' adds only the positional match; 'both' also keeps the unique match.
# Multiword alternatives and their insertion priorities live in oet_phrase_tables.py.
SINGLE_WORD_MAPPINGS = (
    ('abandon', 'forsakes'), # PRO 15:10
    ('abandon', 'leave'), # NUM 32:15
    ('abandoned', 'desolated'), # RV EZE 36:36
    ('abandoned', 'rejected'), # RV PSA 60:1 / LV PSA 60:3
    ('abandons', 'forsakes'), # PRO 28:13
    ('abandons', 'leaving'), # JHN 10:12
    ('abhorrent', 'abhorrence'), # ISA 66:24
    ('ability', 'power'), # PRO 3:27
    ('abode', 'dwelling'), # KI1 8:39
    ('about','concerning'), # Mrk 12:26, 14:71
    ('about','of'), # Mrk 12:26, 14:71
    ('about','whom'), # Mrk 12:26, 14:71
    ('above','over'), # Mat 2:9
    ('Accept', 'receiving'), # ROM 14:1
    ('accept', 'receive'), # PRO 4:10
    ('accept', 'received'), # JHN 1:11
    ('accept', 'receiving'), # CO1 2:14
    ('accept', 'take'), # DEU 16:19
    ('accept', 'takes'), # DEU 10:17
    ('Accept', 'take'), # RV GEN 23:13
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
    ('accusations','testimony'), # Mrk 14:59
    ('accusations', 'accuse'), # PSA 38:20
    ('accusations', 'accused'), # MAT 27:12
    ('accusations', 'accusing'), # ACT 24:13
    ('achieve', 'attained'), # RV ROM 9:31
    ('acknowledge', 'confess'), # ROM 10:9
    ('acknowledge', 'know'), # DEU 4:39
    ('acknowledge', 'recognizing'), # CO1 14:37
    ('acknowledgement', 'confessed'), # ROM 10:10
    ('acknowledging', 'confessing'), # MAT 11:25
    ('acquired', 'acquisition'), # PRO 21:6
    ('across', 'over', 'aligned'),
    ('act', 'behave'), # ISA 1:4
    ('act', 'does'), # PRO 14:17
    ('act', 'work'), # PRO 21:8
    ('acted', 'did'), # HEB 11:33
    ('action', 'act'), # DAN 11:28
    ('action', 'acted'), # ISA 44:23
    ('actioned', 'fulfilling'), # RV LUK 9:31
    ('actions', 'conduct'), # EZE 22:31
    ('actions', 'deeds'), # HOS 9:15
    ('actions', 'work'), # JN1 3:18
    ('actions', 'works'), # ROM 9:32
    ('actions', 'practices'), # RV EZE 21:24 / LV EZE 21:29
    ('activities', 'actions'), # CO1 12:6
    ('addition','And'),
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
    ('advance','beforehand'), # Mrk 13:11,23
    ('advance','previously'), # Mrk 13:11,23
    ('advancing', 'progressing'), # TI2 3:9
    ('advantage', 'profit'), # RV PSA 30:9 / LV PSA 30:10
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
    ('afraid','feared'),
    ('afraid','fearing'),
    ('afraid', 'fear'), # DEU 17:13
    ('afraid', 'fears'), # KI1 1:51
    ('afraid', 'fearful'), # MRK 4:40 (reviewed 2026-10-13)
    ('afterwards', 'afterward'), # HEB 12:17
    ('agabus', 'agabos', 'aligned'),
    ('against', 'towards', 'aligned'),
    ('age', 'years'), # RV DAN 5:31 / LV DAN 6:1
    ('age', 'year[s]'), # RV CH2 24:15
    ('agony', 'tormented'), # RV REV 12:2
    ('agreed','same'), # Mrk 14:56
    ('agreeing','confirming'),
    ('agreeing', 'consenting'), # ACT 8:1 (reviewed 2026-10-13)
    ('agreement','covenant'),
    ('agrees', 'consenting'), # CO1 7:12 (reviewed 2026-10-13)
    ('ahead','before'), # Mrk 14:28
    ('alert','watching'), # Mrk 13:34
    ('alienated', 'estranged'), # COL 1:21
    ('align','same'), # Mrk 14:59
    ('alive', 'life'), # SA1 2:6
    ('alive', 'live'), # EXO 19:13
    ('alive', 'lived'), # LUK 15:32
    ('alive', 'lives'), # SA1 20:31
    ('alive', 'living'), # ACT 25:24
    ('all', 'every', 'aligned'), # MAT 4:5
    ('allegiance', 'loyalty'), # RV JNA 2:8 / LV JNA 2:9
    ('allied', 'alliance'), # CH2 20:37
    ('allotted', 'lot'), # RV CH1 6:54 / LV CH1 6:39
    ('Allow', 'let'), # RUT 2:2
    ('allow', 'grant'), # PSA 140:8
    ('allow', 'let'), # EXO 21:8
    ('allow', 'permit'), # PSA 55:22
    ('allow', 'permitted'), # JDG 1:34
    ('allow', 'permitting'), # CO2 12:4
    ('allowable', 'permitting', 'aligned'), # LUK 6:9
    ('allowed', 'left'), # JDG 2:23
    ('allowed', 'permitted'), # GEN 31:7
    ('allowed', 'permitting'), # LUK 6:4
    ('allowed', 'let'), # RV CH2 36:23
    ('all-powerful', 'almighty'), # RV CO2 6:18
    ('alone', 'solitary'), # RV PSA 25:16
    ('along', 'alongside'), # CH1 26:16
    ('along', 'by', 'aligned'),
    ('Also','And'),
    ('also','and', 'both'),
    ('although', 'though', 'aligned'),
    ('always','perpetuity'),
    ('always', 'continually'), # CH1 23:31 (reviewed 2026-10-13)
    ('amassed', 'gathered'), # RV CH2 24:11
    ('amazed','astonished'),
    ('amazed','marvelling'),
    ('amazed', 'amazement'), # LUK 4:36
    ('amazed', 'marvelled'), # ACT 7:31 (reviewed 2026-10-13)
    ('amazing', 'awesome'), # RV ISA 64:3 / LV ISA 64:2
    ('ambassadors', 'messengers'), # EZE 17:15
    ('ambition', 'ambitious'), # TH1 4:11
    ('ambush', 'ambusher'), # JDG 16:9
    ('ambush', 'ambushers'), # JDG 9:25
    ('ambushes', 'ambusher'), # EZR 8:31
    ('ambushes', 'ambushers'), # JER 51:12
    ('amid', 'among', 'aligned'),
    ('among', 'amidst', 'aligned'),
    ('among', 'midst'), # RV MIC 5:13 / LV MIC 5:12
    ('amongst', 'among'), # ACT 20:29
    ('ancestors','fathers'),
    ('ancestors', 'ancestral'), # ACT 24:14
    ('ancestral', 'ancestors'), # KI2 9:28
    ('ancestry', 'ancestors'), # EZR 2:59
    ('ancient', 'antiquity'), # ISA 46:10
    ('andrew', 'andreas', 'aligned'),
    ('angel', 'messenger'), # EXO 32:34
    ('angels', 'messengers'), # ROM 8:38
    ('anger', 'rage'), # EST 7:10
    ('anger', 'rages'), # CO2 12:20
    ('anger', 'fury'), # HEB 10:27 (reviewed 2026-10-13)
    ('angering', 'provoked'), # CH2 28:25
    ('angrily','anger'), # Mrk 3:5
    ('angry','enraged'), # Mat 2:16
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
    ('Announce', 'Declare'), # RV JER 46:14
    ('announced','proclaiming'),
    ('announced', 'declared'), # ISA 48:14
    ('announced', 'proclaimed'), # DEU 15:2
    ('announcement', 'proclamation'), # DAN 5:29
    ('announcing','proclaiming', 'both'),
    ('annulled', 'annulment'), # HEB 7:18
    ('anointed', 'oil'), # ZEC 4:14
    ('answer', 'respond'), # JOB 20:2
    ('answered','said'),
    ('answered', 'saying'), # ACT 10:30
    ('answered', 'replying'), # RV DAN 6:12 / LV DAN 6:13
    ('Anyone','Whoever'),
    ('anyone','whoever'),
    ('Anyone','one'),
    ('anyone','ones'),
    ('anyone','one'),
    ('apart', 'separated'), # HEB 7:26
    ('apostles', 'apostolos', 'aligned'),
    ('apostles', 'apostolousin', 'aligned'),
    ('appear', 'appearance'), # NUM 9:16
    ('appear', 'present'), # ISA 1:12
    ('appearance', 'appearing'), # TH2 2:8
    ('appeared','seen'),
    ('appeared', 'appearance'), # EZE 10:10
    ('appeared', 'presented'), # JDG 13:10
    ('appearing', 'appearance'), # SA1 28:14
    ('appearing', 'present'), # ACT 24:19
    ('appears', 'presents'), # PSA 84:7
    ('appointed', 'appointment'), # JOS 20:9
    ('appointed', 'assigned'), # KI2 8:6
    ('appointment', 'appointed'), # JOB 30:23
    ('apprentice', 'apprentice/follower'), # JHN 18:16
    ('apprentices', 'apprentices/followers'),
    ('apprentices', 'apprentice/follower'), # MAT 10:42
    ('approach', 'come'), # PSA 36:11
    ('approach', 'near'), # DEU 2:19
    ('approach', 'nearing'), # HEB 7:19
    ('approached', 'coming'), # MRK 5:38
    ('approached', 'near'), # DEU 1:22
    ('approached', 'nearing'), # ACT 9:3
    ('approaching', 'coming'), # JHN 1:47
    ('approaching', 'near'), # JHN 6:19
    ('approaching', 'nearing'), # ACT 10:9
    ('appropriate','fitting'),
    ('apron', 'ephod', 'aligned'), # EXO 25:7
    ('aquila', 'akylas', 'aligned'),
    ('arbitrate', 'decide'), # MIC 4:3
    ('area','districts'), # Mat 2:22
    ('area', 'region'), # LUK 7:17
    ('area', 'country'), # RV MRK 5:14
    ('area', 'regions'), # RV MAT 15:22
    ('areas', 'region'), # LUK 3:3
    ("aren't",'not'),
    ('argue', 'contended'), # RV JOB 33:13
    ('arguing', 'debating'), # ACT 6:9
    ('arid', 'waterless'), # MAT 12:43
    ('arm', 'hand', 'aligned'), # EXO 14:16
    ('armour', 'armor'), # LUK 11:22
    ('armoured', 'armours'), # CH2 26:14
    ('arms', 'hands', 'aligned'), # MAT 4:6
    ('Army','hosts'),
    ('army','hosts'),
    ('aroma','odour'),
    ('around','by'), # Mrk 14:69
    ('around', 'round'), # CH2 17:9
    ('around', 'surround'), # PSA 7:7
    ('around', 'surroundings'), # KI2 23:5
    ('around', 'about', 'aligned'),
    ('arrangements', 'plans'), # EZE 42:11
    ('arrest','apprehend'),
    ('arrested','apprehended'), # Mrk 14:49
    ('arrested','captured'), # Mrk 14:49
    ('arrested','laid'), # Mrk 14:49
    ('arrive', 'come'), # EZR 10:8
    ('arrive', 'coming'), # MAT 24:50
    ('arrived', 'came'),
    ('arrived', 'come'), # ACT 21:11
    ('arrived', 'coming'), # MRK 5:15
    ('arrives', 'come'), # COL 4:10
    ('arriving', 'came'), # JDG 18:13
    ('arriving', 'come'), # RV ACT 19:1
    ('arrogance', 'arrogant'), # PSA 31:18
    ('arrogance', 'loftiness'), # JOB 20:6
    ('Arrogance', 'Haughtiness'), # RV PRO 21:4
    ('arrogant', 'arrogance'), # JN1 2:16
    ('arrogant', 'proud'), # HAB 2:5
    ('arrogant', 'haughty', 'aligned'), # EZE 16:50
    ('arrogantly', 'pride'), # PSA 10:2
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
    ('ask', 'enquired'), # RV EZE 21:21 / LV EZE 21:26
    ('asked','saying'), # Mrk 14:37, 15:8, Mat 2:4
    ('asked','requesting'), # Mrk 14:37, 15:8, Mat 2:4
    ('asked','inquiring'), # Mrk 14:37, 15:8, Mat 2:4
    ('asked', 'enquired'), # CH2 31:9
    ('asked', 'petition'), # PSA 106:15
    ('asked', 'said'), # ACT 2:37
    ('asked', 'say'), # CH1 13:12
    ('asked', 'debating', 'aligned'),
    ('asking', 'inquiring'), # LUK 18:36
    ('asking', 'requesting'), # ACT 25:3
    ('asking', 'said'), # JDG 21:3
    ('asking', 'say'), # PRO 30:9
    ('asking', 'saying'), # ACT 22:7
    ('asks', 'enquires'), # EZE 14:10
    ('asks', 'requesting'), # MAT 7:8
    ('asks', 'said'), # JOB 35:10
    ('asks', 'says'), # ISA 40:25
    ('asleep','sleeping'), # Mrk 14:40
    ('assault', 'assailed'), # RV PSA 17:9
    ('Assemble', 'gather'), # AMO 3:9
    ('assemble', 'assembly'), # KI2 10:20
    ('assemble', 'gather'), # DAN 11:10
    ('assemble', 'meeting'), # ISA 14:13
    ('assembled', 'assembly'), # CH1 13:4
    ('assembled', 'gathered'), # CH2 20:4
    ('assemblies', 'convocations'), # ISA 4:5
    ('assembly','convocation'),
    ('assembly', 'congregation'), # KI1 12:20
    ('assessing', 'valuation'), # KI2 23:35
    ('assign', 'appoint'), # CH1 15:16
    ('assign', 'designate'), # EXO 21:13
    ('assigned', 'appointed'), # GEN 40:4
    ('assigned', 'allotted'), # RV CO1 7:17
    ('assignment', 'commission'), # ROM 1:5
    ('assist', 'help'), # CH1 22:17
    ('assist', 'serve'), # NUM 3:6
    ('assistant', 'servant'), # EXO 24:13
    ('assistants', 'help'), # EZE 12:14
    ('assisted', 'helped'), # CH1 12:1
    ('associate', 'association'), # JHN 4:9
    ('associates', 'companions'), # ISA 44:11
    ('assure','Truly'), # Mrk 13:30, 16:^
    ('assured','saying'), # Mrk 13:30, 16:^
    ('astonished', 'marvelled'), # ACT 10:45 (reviewed 2026-10-13)
    ('astounded','amazed'), # Mrk 15:5
    ('astounded','marvelling'), # Mrk 15:5
    ('astounded', 'astonished'), # JOB 26:11
    ('astray', 'mislead'), # MIC 3:5
    ('astray', 'misleads'), # PRO 12:26
    ('astray', 'misled'), # AMO 2:4
    ('at','in/on/at/with'),
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
    ('attacking', 'trampled'), # RV PSA 56:1 / LV PSA 56:2
    ('attacks', 'strike'), # EXO 21:35
    ('attempt', 'seeking'), # GAL 2:17
    ('attempted', 'sought'), # SA2 21:2
    ('attempted', 'seeking'), # RV MAT 21:46
    ('attending', 'serving'), # RV KI1 1:15
    ('attention','attentiveness'),
    ('attention', 'attentive'), # JOB 11:11
    ('attract', 'drawing'), # JHN 12:32
    ('attracted', 'drew'), # ACT 5:37
    ('attracts', 'draw'), # JHN 6:44
    ('authority', 'ruled'), # CH2 8:10
    ('avenge', 'avenger'), # JOS 20:5
    ('avenged', 'avenger'), # JOS 20:9
    ('avenging', 'avenger'), # NUM 35:19
    ('avoid','pass'), # Mrk 14:35
    ('await', 'expecting'), # PE2 3:14
    ('await', 'waiting'), # PE2 3:13
    ('awakened', 'aroused'), # SNG 8:5
    ('aware','knowing'), # Mrk 15:10
    ('aware', 'know'), # RV PSA 46:10 / LV PSA 46:11
    ('awe', 'fear'), # RV PSA 5:7 / LV PSA 5:8
    ('awe-inspiring', 'awesome'), # RV DAN 9:4
    ('awesome', 'feared'), # PSA 99:3
    ('awesomely', 'fear'), # EZE 1:18
    ('awning', 'covering'), # EZE 27:7
    ('baby', 'child'), # HEB 11:23
    ('baby', 'children'), # EXO 21:22
    ('back','stern'),
    ('backpack', 'knapsack'), # LUK 9:3
    ('backward', 'backwards'), # KI2 20:11
    ('bad', 'badness'), # RV JER 29:17
    ('baked', 'cooked'), # SA2 13:8
    ('balance', 'balancings'), # JOB 37:16
    ('band', 'fetter'), # RV DAN 4:15 / LV DAN 4:12
    ('band', 'company'), # RV PSA 22:16 / LV PSA 22:17
    ('bandage', 'bind'), # HOS 6:1
    ('bandage', 'bound'), # EZE 34:4
    ('bandaged', 'bound'), # ISA 1:6
    ('bandages', 'binding'), # PSA 147:3
    ('bandages', 'binds'), # JOB 5:18
    ('banner', 'signs'), # NUM 2:2
    ('banner', 'standard', 'aligned'), # ISA 11:12
    ('banquet', 'feast'), # DAN 5:10
    ('bare', 'naked'), # RV CO1 15:37
    ('barren', 'bare'), # JER 7:29
    ('bartholomew', 'bartholomaios', 'aligned'),
    ('bartimaeus', 'bartimaios', 'aligned'),
    ('base','root'),
    ('bases', 'stands'), # KI2 25:16
    ('bash', 'strike', 'aligned'), # MAT 4:6
    ('basin', 'laver'), # EXO 30:28
    ('basins', 'bowls'), # CH2 4:22
    ('basins', 'laver'), # KI2 16:17
    ('basins', 'lavers'), # KI1 7:43
    ('basketful', 'basket'), # AMO 8:1
    ('basketfuls', 'baskets'), # MRK 8:8
    ('battalion','cohort'), # Mrk 15:16
    ('battering', 'battering-ram'), # EZE 26:9
    ('battering', 'battering-rams'), # EZE 4:2
    ('battle','war'),
    ('battle', 'fight'), # JDG 8:1
    ('battled', 'fought'), # SA1 23:5
    ('battlefield', 'field'), # RV JDG 5:18
    ('battles','wars'),
    ('battling', 'fighting'), # SA1 31:1
    ('beach', 'shore'), # ACT 21:5 (reviewed 2026-10-13)
    ('beans', 'bean[s]'), # EZE 4:9
    ('bear', 'carry'), # NUM 11:14
    ('bear', 'endure'), # JER 44:22
    ('bear', 'carried'), # RV LAM 5:7
    ('beat', 'struck'), # JNA 4:8
    ('beaten', 'struck'), # EXO 5:14
    ('beating', 'striking'), # EXO 2:11
    ('beatings', 'blows'), # PRO 20:30
    ('beautiful','beauty'),
    ('beautiful', 'splendour'), # RV ISA 64:11 / LV ISA 64:10
    ('beauty', 'beautiful'), # SNG 2:10
    ('beauty', 'grace'), # RV JOB 41:12 / LV JOB 41:4
    ('became', 'turned'), # ACT 9:35
    ('because','for/because'),
    ('Because','For/Because'),
    ('because','For/Because'),
    ('because','if/because'),
    ('because', 'for', 'aligned'),
    ('because', 'since', 'aligned'),
    ('bedding','pallet'),
    ('bedroom', 'chamber'), # CH2 22:11
    ('bedroom', 'chambers'), # SNG 1:4
    ('before', 'ere', 'aligned'),
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
    ('believers','brothers'),
    ('believers', 'believed'), # ACT 4:32
    ('believers', 'believing'), # ACT 5:14
    ('bellows', 'bellow[s]'), # JER 6:29
    ('below', 'beneath'), # AMO 2:9
    ('belt', 'loincloth'), # KI2 1:8
    ('belts', 'loincloth'), # EZE 23:15
    ('bend', 'stoop', 'aligned'),
    ('bend', 'stretches'), # RV PSA 18:34 / LV PSA 18:35
    ('beneath', 'under', 'aligned'),
    ('beneficial', 'benefitting'), # CO1 6:12
    ('benefit', 'profit'), # JOB 22:3
    ('benefit', 'profits'), # JER 2:11
    ('benefit', 'Profit'), # RV REV 3:15
    ('bent', 'inclined'), # HOS 11:4
    ('beside', 'by', 'aligned'),
    ('besiege', 'siege'), # ISA 29:3
    ('besieged', 'siege'), # KI1 16:17
    ('besieged', 'surrounded'), # LAM 3:5
    ('besieging', 'siege'), # KI1 15:27
    ('best', 'choicest', 'aligned'), # DEU 33:21
    ('bestower', 'bestows'), # ISA 23:8
    ('betrayed', 'betrayer'), # LUK 6:16
    ('betrayed', 'treacherously'), # LAM 1:2
    ('betrays', 'treacherously'), # HAB 2:5
    ('better', 'good'), # AMO 6:2
    ('better', 'improving'), # RV LUK 17:2
    ('between', 'among', 'aligned'),
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
    ('biscuits','wafers'),
    ('bitter', 'bitterness'), # ACT 8:23
    ('bitter', 'bitternesses'), # JER 6:26
    ('bitterly', 'bitter'), # EST 4:1
    ('bitterly', 'bitterness'), # ISA 22:4
    ('bitterness', 'bitter'), # ECC 7:26
    ('black', 'blackish'), # SNG 1:6
    ('blacksmiths', 'craftsman'), # SA1 13:19
    ('blame', 'culpable'), # GEN 43:9
    ('blanketed', 'covered'), # RV HAB 3:3
    ('blast', 'breathing'), # PSA 18:15
    ('blast', 'sounds'), # EXO 19:13
    ('blast', 'blow'), # RV JOS 6:5
    ('blasts', 'sound'), # SA2 6:15
    ('blazing', 'burning'), # DAN 3:6
    ('bleeding', 'haemorrhage'), # LUK 8:43
    ('bless','fruitful'),
    ('blessed', 'sanctified'), # JHN 10:36
    ('blessings', 'bless'), # DEU 21:5
    ('blew', 'blast'), # JDG 3:27
    ('block', 'stop'), # KI2 3:19
    ('blocked', 'stopped'), # CH2 32:4
    ('blocking', 'stop'), # CH2 32:3
    ('blocks', 'block[s]'), # ISA 57:14
    ('blocks', 'shuts'), # RV PSA 58:4 / LV PSA 58:5
    ('bloodshed', 'blood'), # EZE 5:17
    ('bloodshed', 'bloods'), # ISA 26:21
    ('bloodthirsty', 'bloods'), # PSA 59:2
    ('bloody', 'blood'), # HOS 6:8
    ('bloody', 'bloods'), # EXO 4:25
    ('blossom', 'bloom'), # ECC 12:5
    ('blotted', 'wiped'), # RV PSA 69:28 / LV PSA 69:29
    ('Blow', 'blast'), # JOL 2:15
    ('blow', 'blast'), # EZE 33:6
    ('blowing','blast'),
    ('blown', 'blast'), # EZE 7:14
    ('blows', 'blast'), # EZE 33:3
    ('boast', 'bragging'), # RV CO1 13:4
    ('bodies', 'corpse'), # JER 34:20
    ('bodies', 'corpse[s]'), # AMO 8:3
    ('bodies', 'corpses'), # EZE 6:5
    ('body','flesh'),
    ('body', 'corpse'), # KI1 13:22
    ('boiling', 'cooking'), # RV JOB 41:20 / LV JOB 41:12
    ('boils', 'boil[s]'), # DEU 28:27
    ('bones', 'bone[s]'), # PRO 16:24
    ('book', 'scroll'), # DAN 12:4
    ('books', 'scrolls'), # DAN 9:2
    ('border','edge'),
    ('border', 'territory'), # EZE 43:12
    ('borders', 'extremities'), # JOS 17:18
    ('borders', 'territories'), # EZE 27:4
    ('borders', 'territory'), # PSA 147:14
    ('bore', 'birth'), # CH1 4:9
    ('borne', 'endure'), # PSA 55:12
    ('both','two'),
    ('bother', 'troubling'), # LUK 8:49
    ('bottle', 'skin-bottle'), # PSA 56:8
    ('bought','redeemed'),
    ('bought', 'purchase'), # GEN 17:12
    ('bought', 'purchased'), # ACT 7:16
    ('boulders','stones'),
    ('boundaries', 'borders'), # NUM 34:2
    ('boundaries', 'bounds'), # EXO 19:23
    ('boundary', 'border'), # EZE 47:20
    ('bounty', 'goodness'), # PSA 65:11
    ('bowed','fallen'), # Mat 2:11
    ('bowing','prostrating'), # Mrk 15:19
    ('bowls', 'troughs'), # EXO 12:34
    ('box','ark'),
    ('boy', 'lad'), # GEN 21:12
    ('boy', 'son'), # MAT 1:25
    ('boys', 'lads'), # GEN 25:27
    ('bracelet', 'armlet'), # SA2 1:10
    ('brag', 'boast'), # EPH 2:9
    ('brag', 'boasting'), # RV TH1 2:19
    ('branch', 'shoot'), # ISA 14:19
    ('branches', 'branch[es]'), # EZE 17:8
    ('brands', 'branding'), # ISA 3:24
    ('bread', 'bread[s]'), # KI1 14:3
    ('bread', 'food'), # EZE 16:19
    ('bread', 'wheat'), # RV PSA 81:16 / LV PSA 81:17
    ('breadrolls', 'loaves'), # LUK 9:13 (reviewed 2026-10-13)
    ('Break', 'tear'), # JDG 6:25
    ('break', 'tear'), # GEN 27:40
    ('break', 'violate'), # PSA 89:31
    ('breaks', 'breaches'), # RV AMO 4:3
    ('breastfed', 'nursed'), # RV SA1 1:23
    ('breastfeed', 'nurse'), # KI1 3:21
    ('breastfeed', 'nursed'), # RV GEN 21:7
    ('breast-feeding', 'nursing'), # TH1 2:7
    ('breast-feeding', 'sucking'), # RV LAM 4:4
    ('breastplate', 'breastpiece'), # EXO 25:7
    ('breath', 'wind'), # JOB 26:13
    ('breathe', 'breath'), # DAN 10:17
    ('breathes', 'breath'), # GEN 6:17
    ('bribery', 'bribe'), # CH2 19:7
    ('brief', 'briefly'), # ACT 24:4
    ('brief', 'little'), # JAM 4:14
    ('bright', 'shining'), # REV 15:6
    ('brightness','glory'), # Mrk 13:26
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
    ('broken', 'crushed'), # RV PSA 51:8 / LV PSA 51:10
    ('broken-hearted', 'broken'), # PSA 147:3
    ('brokenhearted', 'broken'), # ISA 61:1
    ('bronze', 'copper'), # EZE 22:20
    ('brother', 'countrymen'), # DEU 3:20
    ('brotherhood', 'brothers'), # AMO 1:9
    ('brothers', 'countrymen'), # RV NEH 10:29 / LV NEH 10:30
    ('brought', 'carried'), # CH1 18:11
    ('brought', 'led'), # ACT 18:12
    ('brought', 'taking'), # JHN 21:13
    ('brought', 'took'), # EXO 2:10
    ('buds', 'bulbs'), # EXO 25:31 (reviewed 2026-10-13)
    ('build', 'established'), # PSA 107:36
    ('build', 'rebuild'), # HAG 1:8
    ('build', 'make'), # RV DEU 16:21
    ('building', 'established'), # JDG 16:29
    ('building', 'rebuilding'), # NEH 6:6
    ('building', 'rebuilt'), # NEH 6:1
    ('builds', 'makes'), # PRO 17:19
    ('built', 'made'), # KI1 6:6
    ('built', 'rebuilt'), # ZEC 1:16
    ('bull','ox'),
    ('bulls','oxen'),
    ('bulls', 'cattle'), # CH2 29:22
    ('bulls', 'ox[en]'), # CH2 4:15
    ('bundles', 'sheaves'), # RUT 2:15
    ('buns','loaves'),
    ('burden', 'load'), # GEN 49:15
    ('burial', 'tomb'), # JDG 16:31
    ('burial', 'burying'), # RV JHN 19:40
    ('burn', 'smoke'), # EXO 29:13
    ('burning','fire'),
    ('burnt', 'fire'), # EZE 20:31
    ('burnt', 'smoke'), # LEV 8:16
    ('bursting', 'breaking'), # EXO 9:9
    ('bury', 'hide'), # JER 13:4
    ('But','And'),
    ('but','And'),
    ('But','and'),
    ('but','and'),
    ('butter', 'curd[s]'), # JOB 29:6
    ('buttocks', 'buttock[s]'), # CH1 19:4
    ('buyer', 'buys'), # EZE 7:12
    ('buyers','buying'),
    ('caiaphas', 'kaiaphas', 'aligned'),
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
    ('called', 'crying'), # RV MAT 9:27
    ('calling', 'cried'), # ACT 24:21
    ('calling', 'crying'), # GEN 4:10
    ('calls', 'cry'), # PSA 34:15
    ('calls', 'summons'), # PSA 50:4
    ('calm', 'quiet'), # EXO 14:14
    ('came','arriving'), # MAt 3:13
    ('came', 'approached'), # ACT 12:13
    ('came', 'approaching'), # DAN 9:21
    ('came', 'arrived'), # ACT 10:33
    ('came', 'descended'), # EXO 34:5
    ('came', 'near'), # SA1 17:16
    ('came', 'returned'), # KI2 9:36
    ('came', 'went'), # DEU 2:32
    ('came', 'searched', 'aligned'),
    ('camels', 'camel[s]'), # KI2 8:9
    ('camp', 'encamp'), # ISA 29:3
    ('camp', 'encamped'), # JDG 6:33
    ('camp', 'encampments'), # RV EZE 25:4
    ('camped', 'encamped'), # EXO 13:20
    ('camped', 'encamping'), # SA2 23:13
    ('camping', 'encamped'), # NUM 33:11
    ('camping', 'encamping'), # EXO 18:5
    ('camps', 'encamped'), # CH1 19:7
    ('camps', 'encampments'), # NUM 31:10
    ("can't",'not'),
    ('capable', 'able'), # ACT 20:32
    ('caps', 'capitals'), # KI1 7:19
    ('captain', 'officer'), # KI2 7:2
    ('captains', 'officials'), # KI2 11:14
    ('captains', 'chiefs'), # RV CH1 12:20 / LV CH1 12:21
    ('captivate', 'captive'), # TI2 3:6
    ('captive', 'captivity'), # DAN 11:33
    ('captives', 'captive[s]'), # CH2 28:13
    ('captives', 'captivity'), # DEU 28:41
    ('capture', 'seize'), # PSA 71:11
    ('capture', 'take'), # JOB 40:24
    ('captured', 'seized'), # KI2 18:13
    ('captured', 'taken'), # SA1 4:17
    ('captured', 'took'), # CH1 18:1
    ('captured', 'caught'), # RV JER 6:11
    ('capturing', 'captive'), # CO2 10:5
    ('careful','watching'), # Mrk 13:9
    ('careful', 'care'), # DEU 5:1
    ('careful', 'carefully'), # EXO 23:22
    ('carefully', 'care'), # DEU 6:3
    ('careless', 'confident'), # PRO 14:16
    ('carpenters', 'craftsmen'), # CH2 34:11
    ('carried', 'took'), # KI1 17:23
    ('carry','bear'), # Mat 3:11
    ('carry', 'bearing'), # GAL 6:17
    ('carry', 'burden'), # NUM 4:49
    ('carry', 'take'), # JHN 5:10
    ('carry', 'borne'), # RV EZE 32:24
    ('Carrying', 'bearing'), # JHN 19:17
    ('carrying', 'bear'), # EXO 28:29
    ('carrying', 'bearing'), # ROM 15:1
    ('case', 'cause'), # PSA 9:4
    ('cash','money'),
    ('cash','silver'),
    ('cast', 'throw'), # CH2 4:17
    ('castrated', 'eunuch'), # EST 2:3
    ('castrated', 'eunuchs'), # ISA 39:7
    ('casts', 'throwing'), # MAT 9:34
    ('catch', 'took'), # LUK 5:5
    ('cattle', 'cattles'), # DEU 7:13
    ('cattle', 'herd[s]'), # GEN 47:17
    ('cattle', 'ox[en]'), # RV GEN 32:5 / LV GEN 32:6
    ('cattle', 'livestock'), # CH2 14:15 (reviewed 2026-10-13)
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
    ('cavalry', 'horsemen'), # ISA 31:1 (reviewed 2026-10-13)
    ('cease','removed'),
    ('cedar', 'cedar[s]'), # ISA 41:19
    ('Celebrate', 'observe'), # KI2 23:21
    ('celebrate', 'observe'), # DEU 16:10
    ('celebrate', 'rejoice', 'aligned'), # DEU 26:11
    ('celebrated', 'observed'), # CH2 35:19
    ('celebrates', 'observe'), # NUM 9:14
    ('celebration', 'celebrate'), # NUM 29:12
    ('celebration', 'festivities'), # LUK 14:8
    ('celebration', 'observed'), # NEH 8:18
    ('celebration', 'festival'), # EZE 45:23 (reviewed 2026-10-13)
    ('celebrations', 'festivities'), # LUK 12:36
    ('census', 'number'), # CH1 27:23
    ('centre', 'center'), # EZE 38:12
    ('centre', 'middle'), # CH2 6:13
    ('ceremony', 'service'), # EXO 12:25
    ('certain', 'certainly'), # CO1 9:22
    ('certainly', 'surely', 'aligned'), # EXO 21:15
    ('chain', 'necklace'), # DAN 5:7
    ('chains','bonds'),
    ('chains', 'fetter[s]'), # LAM 3:7
    ('chains', 'fetters'), # NAH 3:10
    ('chairs','seats'),
    ('chamber','tomb'), # Mrk 16:2
    ('chamber', 'room'), # KI2 23:12
    ('chambers', 'rooms'), # EZR 8:29
    ('chance', 'opportunity'), # MRK 6:31
    ('Change', 'turn'), # PRO 1:23
    ('change', 'turn'), # EZE 13:22
    ('change', 'exchange'), # RV HOS 4:7
    ('changed', 'turned'), # LEV 13:55
    ('changing', 'turned'), # JOB 28:5
    ('charge','testimony'), # Mrk 14:56,57
    ('charge', 'accusation'), # JHN 18:29
    ('charge', 'appoint'), # CH1 22:12
    ('charge', 'appointed'), # EST 8:2
    ('charges','testimony'), # Mrk 14:56,57
    ('chariot', 'chariot[s]'), # KI2 7:14
    ('chariot', 'chariotry'), # CH2 8:9
    ('charioteers', 'charioteer[s]'), # SA2 10:18
    ('chariots','chariotry'),
    ('chariots', 'chariot[s]'), # CH1 19:7
    ('Chase', 'pursue'), # JOS 10:19
    ('chase', 'pursue'), # DEU 28:22
    ('chase', 'pursues'), # PRO 11:19
    ('chase', 'pursuit'), # RV SA2 2:27
    ('chased', 'pursue'), # MAT 5:11
    ('chased', 'pursued'), # DEU 1:44
    ('chased', 'pursuing'), # ROM 9:31
    ('chases', 'pursues'), # PRO 13:21
    ('chasing','pursuing'),
    ('chasing', 'pursues'), # LEV 26:17
    ('cheek', 'jaw'), # RV PSA 3:7 / LV PSA 3:8
    ('cheered', 'cheerful'), # ACT 27:36
    ('cheerful','joy'),
    ('cheerful', 'cheering'), # JAM 5:13
    ('cheerfully', 'cheerfulness'), # ROM 12:8
    ('cheers', 'glad'), # JDG 9:13
    ('cherished', 'treasured'), # RV EZE 7:22
    ('chest','ark'),
    ('chest', 'box'), # EXO 25:10
    ('chest', 'breasts'), # DAN 2:32
    ('chest', 'heart'), # RV JOB 41:24 / LV JOB 41:16
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
    ('chiselled','hewn'), # Mrk 15:46
    ('choice', 'choicest'), # EZE 20:40
    ('chooses', 'taking'), # RV GEN 27:46
    ('chosen', 'found'), # RV PSA 89:20 / LV PSA 89:21
    ('church', 'assembly'), # CO1 4:17 (reviewed 2026-10-13)
    ('circumcised', 'circumcision'), # EPH 2:11
    ('circumcision', 'circumcise'), # LUK 2:21
    ('cities', 'town'), # HAB 2:8
    ('citizens', 'citizenship'), # EPH 2:12
    ('city', 'town'), # KI1 1:41
    ('claiming', 'take'), # RV MAT 5:40
    ('clan', 'family'), # GEN 24:41
    ('clan', 'tribes'), # RV NUM 25:15
    ('clans', 'divisions'), # JDG 5:15
    ('clapped', 'struck'), # KI2 11:12
    ('clay', 'mud'), # PSA 40:2
    ('clay', 'earthenware'), # JER 32:14 (reviewed 2026-10-13)
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
    ('cleared', 'vindicated'), # RV GEN 20:16
    ('clearly', 'clear'), # HAB 2:2
    ('clever', 'sensible'), # PRO 14:18
    ('cliff', 'steep'), # SNG 2:14
    ('cliffs', 'steep'), # EZE 38:20
    ('climb', 'ascent'), # JER 48:5
    ('climbing', 'ascent'), # KI2 9:27
    ('cling', 'cleaving'), # DEU 30:20
    ('cling', 'joined'), # RV JOB 41:17 / LV JOB 41:9
    ('cloak', 'shawl'), # RUT 3:15
    ('cloak', 'skirt'), # RUT 3:9
    ('close','near'), # Mrk 13:28, Mat 3:2
    ('close','neared'), # Mrk 13:28, Mat 3:2
    ('close', 'nearing'), # ACT 22:6
    ('close', 'shut'), # DEU 11:17
    ('close', 'beside'), # RV NEH 4:12 / LV NEH 4:6
    ('closed', 'shut'), # ACT 21:30
    ('closed', 'shuts'), # PRO 17:28
    ('closely','focused'), # Mrk 14:67
    ('closely', 'carefully'), # KI1 3:21
    ('closer', 'approached'), # LUK 7:14
    ('closer', 'approaching'), # SA2 18:25
    ('closes', 'shuts'), # JOB 12:14
    ('cloth', 'garment'), # DEU 22:17
    ('clothed', 'dress'), # LUK 24:49
    ('clothes','apparel'),
    ('clothes','garments'),
    ('clothes', 'dress'), # MRK 6:9
    ('clothes', 'garment'), # EZR 9:3
    ('clothing', 'covering'), # EXO 21:10
    ('clothing', 'garments'), # JOS 22:8
    ('clothing', 'garment'), # RV EXO 22:9 / LV EXO 22:8
    ('clouds', 'cloud[s]'), # EZE 1:28
    ('clubs', 'staff'), # EZE 39:9
    ('clung', 'cleaved'), # KI1 11:2
    ('clusters', 'bunches'), # SA1 30:12
    ('clutch', 'hand'), # RV PSA 22:20 / LV PSA 22:21
    ('coast', 'coastland'), # ISA 23:2
    ('coast', 'coastlands'), # GEN 10:5
    ('coastal', 'coast'), # DEU 1:7
    ('coastal', 'islands'), # EZE 27:35
    ('coastlines', 'coast'), # ISA 20:6
    ('coasts', 'islands'), # EZE 27:7
    ('coat', 'garment'), # PRO 20:16 (reviewed 2026-10-13)
    ('cold', 'coldness'), # JOB 24:7
    ('collapsed', 'fell'), # HEB 11:30 (reviewed 2026-10-13)
    ('collect','gathering'), # Mrk 13:27
    ('collect', 'gather'), # NUM 19:9
    ('collect', 'gathers'), # RV JER 9:22 / LV JER 9:21
    ('collect', 'Gather'), # RV JHN 6:12
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
    ('comes', 'turns'), # RV NAH 2:8 / LV NAH 2:9
    ('comfort', 'comforter'), # LAM 1:2
    ('comfort', 'comforters'), # JOB 16:2
    ('comfort', 'consoling'), # TH1 5:14
    ('comfort', 'consolation'), # RV CO1 14:3
    ('comforts', 'consolations'), # RV JOB 15:11
    ('coming', 'advent'), # ACT 7:52
    ('coming', 'go'), # KI1 2:2
    ('coming', 'going'), # ISA 15:3
    ('coming', 'near'), # MAT 24:32
    ('coming', 'went'), # JER 13:20
    ('command','speak'), # Mat 4:3
    ('commanded', 'commander'), # CH2 17:15
    ('commander','centurion'), # Mrk 15:39
    ('commander', 'leader'), # CH1 27:8
    ('commander', 'official'), # JER 51:27
    ('commander', 'chief', 'aligned'), # JDG 11:8
    ('Commander-in-chief','hosts'),
    ('commanders', 'leaders'), # CH1 15:25
    ('commanders', 'officials'), # CH2 23:13
    ('commemorate', 'recount'), # JDG 11:40
    ('commented','saying'),
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
    ('complete', 'total'), # RV MAL 4:6 / LV MAL 3:24
    ('completed', 'finished'), # EZR 4:13
    ('completed', 'perfected'), # EZE 27:11
    ('Completely', 'totally'), # JER 50:26
    ('completely', 'complete'), # ACT 3:16
    ('completely', 'totally'), # DEU 2:34
    ('completely', 'whole'), # RV PSA 51:19 / LV PSA 51:21
    ('completion', 'completed'), # LAM 4:11
    ('component', 'part'), # RV EPH 4:16
    ('compulsion', 'compulsory'), # PE1 5:2
    ('conceal', 'hide'), # JER 50:2
    ('concern', 'worry'), # CO2 11:28
    ('concerned', 'caring'), # CO1 7:21
    ('conclusion', 'end'), # RV ECC 12:13
    ('condemned', 'condemnation'), # ROM 8:1
    ('conduct', 'way'), # JOB 34:11
    ('confidence', 'security'), # PRO 3:23
    ('confidence', 'trust'), # PSA 118:8
    ('confident', 'confidence'), # CO2 5:6
    ('confident', 'secure'), # JOB 11:18
    ('confidently', 'confidence'), # CO2 11:17
    ('confined', 'bound'), # RV ACT 24:27
    ('confirmation', 'confirm'), # ROM 15:8
    ('confirming', 'confirmation'), # PHP 1:7
    ('conflict', 'war'), # DAN 10:1
    ('confused','confounded'),
    ('confused', 'bewilderment'), # DEU 28:28
    ('confused', 'confusion'), # EXO 14:3
    ('confused', 'confusions'), # ISA 19:14
    ('confusion', 'confused'), # EXO 14:24
    ('congratulate', 'bless'), # SA2 8:10
    ('congregation', 'assemblies'), # PSA 68:26
    ('congregation', 'assembly'), # NEH 13:1
    ('connecting', 'join'), # EXO 36:18
    ('connecting', 'joined'), # EXO 36:22
    ('conquered', 'captured'), # RV JER 50:46
    ('conquered', 'subdued'), # RV SA2 8:11
    ('conquered', 'overcame'), # REV 3:21 (reviewed 2026-10-13)
    ('conqueror', 'dispossesses'), # MIC 1:15
    ('conquerors', 'conquering'), # ROM 8:37
    ('conscripted', 'selected'), # NUM 31:5
    ('consecrate', 'holy'), # EXO 29:21
    ('consecrated', 'consecration'), # LEV 21:12
    ('consecrating', 'holy'), # LEV 8:11
    ('consider', 'count'), # CO2 3:5
    ('consider', 'counting'), # ROM 6:11
    ('consider', 'counted'), # RV ROM 2:26
    ('Consider', 'See'), # RV JN1 3:1
    ('Consider', 'seeing'), # RV CO1 10:18
    ('considered', 'reckoned'), # KI1 10:21
    ('considered', 'regarded'), # PSA 44:22
    ('considered', 'thought'), # NEH 13:13
    ('considered', 'counted'), # RV ROM 4:9
    ('consistently', 'persistently'), # RV JER 9:4 / LV JER 9:3
    ('consolation', 'comfort'), # EZE 16:54
    ('conspiracy', 'conspired'), # KI2 21:24
    ('conspiring', 'conspirators'), # SA2 15:31
    ('constructed', 'made'), # RV ECC 2:6
    ('consulted', 'counsel'), # CH2 32:3
    ('consume', 'devour'), # EZE 36:14
    ('consume', 'eat'), # RV DEU 14:26
    ('consumed', 'ate'), # CH2 7:1
    ('container', 'vessel'), # JER 48:11 (reviewed 2026-10-13)
    ('containers', 'kettles'), # MRK 7:4
    ('containers', 'vessels'), # CO2 4:7 (reviewed 2026-10-13)
    ('contempt', 'abhorrence'), # DAN 12:2
    ('contempt', 'scorn'), # JOB 16:10
    ('contempt', 'mockery'), # RV PSA 44:13 / LV PSA 44:14
    ('content', 'contentment'), # CO2 9:8
    ('contentious', 'contentions'), # PRO 25:24
    ('contents', 'message'), # TH2 3:14
    ('contents', 'words/messages'), # KI2 22:11
    ('continual', 'continually'), # LEV 24:2
    ('continual', 'continuity'), # EXO 29:42
    ('continually', 'continuance'), # AMO 1:11
    ('continually', 'continuity'), # EXO 30:8
    ('continually', 'always'), # COL 1:3 (reviewed 2026-10-13)
    ('continue', 'continually'), # HAB 1:17
    ('continue', 'remain'), # TI1 2:15
    ('continue', 'remaining'), # ACT 11:23
    ('continue', 'repeat'), # JDG 10:13
    ('continue', 'repeated'), # JDG 8:28
    ('continue', 'repeating'), # DEU 5:25
    ('continued','said'),
    ('continued', 'remained'),
    ('continued', 'repeated'), # SA1 3:21
    ('continuously', 'continually'), # EZE 38:8
    ('contradicted','saying'), # Mrk 14:29
    ('contrary', 'contrariness'), # LEV 26:21
    ('contributed', 'contribution'), # CH1 29:6
    ('contributed', 'giving'), # RV NEH 12:47
    ('control', 'mastering'), # ROM 6:14
    ('control', 'restrain'), # GEN 45:1
    ('control', 'rules'), # PRO 16:32
    ('control', 'mastered'), # RV CO1 6:12
    ('controlling', 'restrained'), # GEN 43:31
    ('controls', 'holding'), # CO2 5:14
    ('convenient', 'conveniently'), # MRK 14:11
    ('convulsion', 'convulsed'), # MRK 1:26
    ('convulsions', 'convulsed'), # MRK 9:26
    ('cook', 'prepare'), # RV GEN 27:4
    ('cooked', 'made'), # RV LEV 7:9
    ('copy', 'imitating'), # JN3 1:11
    ('cornelius', 'kornelios', 'aligned'),
    ('cornerstone', 'corner'), # ACT 4:11
    ('corpses', 'corpse[s]'), # JER 7:33
    ('correct', 'right'), # JOB 27:5
    ('corrected', 'correction'), # PRO 8:33
    ('corrupt', 'corruptly'), # DEU 4:16
    ('corrupt', 'crooked'), # RV ACT 2:40
    ('corrupted', 'corruptly'), # DEU 9:12
    ('could','may'),
    ('could','able'),
    ('counsellor', 'counselor'), # ROM 11:34
    ('counsellors', 'counsel'), # PSA 119:24
    ('count', 'enrol'), # SA2 24:4
    ('count', 'number'), # JOB 9:10
    ('count', 'numbers'), # RV PSA 71:15
    ('counted', 'enrolled'), # NUM 1:19
    ('counted', 'mustered'), # SA1 13:15
    ('counted', 'number'), # SA2 2:15
    ('counted', 'numbered'), # ECC 1:15
    ('counting', 'number'), # NUM 1:18
    ('Countries','nation'), # Mrk 13:8
    ('countries','nation'), # Mrk 13:8
    ('countries','nations'),
    ('countries', 'earth/land'), # KI1 10:24
    ('countries', 'land'), # CH2 20:10
    ('countries', 'lands'), # DAN 9:7
    ('country','nation'),
    ('country', 'earth/land'), # CH2 19:3
    ('country', 'land'), # GEN 24:4
    ('country', 'nations'), # LUK 12:30
    ('country', 'territory'), # PSA 105:31
    ('country', 'Land'), # RV ISA 1:7
    ("country's", 'earth/land'), # RV EZE 7:27
    ('countryside','field'),
    ('countryside', 'country'), # CH1 19:9
    ('countryside', 'field[s]'), # GEN 41:48
    ('countryside', 'region'), # CH1 8:8
    ('counts', 'reckons'), # RV PSA 32:2
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
    ('court', 'tribunal'), # RV CO2 5:10
    ('courtyard','court'),
    ('courtyard', 'precinct'), # CH2 6:13
    ('courtyards', 'courts'), # CH1 23:28
    ('cover', 'conceal'), # GEN 37:26
    ('cover', 'cover-up'), # PE1 2:16
    ('cover', 'whitewash'), # DEU 27:2
    ('covered', 'covered-up'), # ROM 4:7
    ('covered', 'panelled'), # KI1 7:7
    ('covered', 'roofed'), # NEH 3:15
    ('covered', 'wrapped'), # RV PSA 89:45 / LV PSA 89:46
    ('covering', 'conceals'), # PRO 28:13
    ('covers', 'Coverings'), # RV PRO 7:16
    ('covetous', 'coveter'), # EPH 5:5
    ('cow','ox'),
    ('cow', 'oxen'), # RV DAN 4:33 / LV DAN 4:30
    ('cowardly', 'fearful'), # RV REV 21:8
    ('cower', 'cringed'), # PSA 18:44
    ('cower', 'cringe'), # RV PSA 66:3
    ('cows','oxen'),
    ('cows', 'cattles'), # PSA 8:7
    ('cows', 'ox[en]'), # RV JOB 42:12
    ('crack', 'cleft'), # RV JER 13:4
    ('cracked', 'breaking'), # RV EZE 21:6 / LV EZE 21:11
    ('cracks', 'clefts'), # ISA 7:19
    ('craftiest', 'crafty'), # GEN 3:1
    ('craftily', 'cunningly'), # PSA 105:25
    ('craftiness', 'crafty'), # JOB 5:13
    ('crafts', 'workmanship'), # RV EXO 31:5
    ('craftsmanship', 'craft'), # ACT 17:29
    ('craftsmanship', 'workmanship'), # RV EXO 31:3
    ('crafty', 'craftiness'), # CO2 11:3
    ('crawling', 'creeping'), # GEN 6:7
    ('crawling', 'creeps'), # LEV 20:25
    ('created', 'made'), # ACT 4:24
    ('creation','beginning'),
    ('creation', 'foundation', 'aligned'), # EPH 1:4
    ('creator', 'created'), # COL 3:10
    ('creature', 'animal'), # REV 13:1
    ('creature', 'beast'), # DAN 7:23
    ('creatures', 'beasts'), # DAN 7:12
    ('creatures', 'creature[s]'), # GEN 1:20
    ('creek', 'brook'), # RV SA2 17:20
    ('crevice', 'cleft'), # JDG 15:11
    ('crevices', 'clefts'), # ISA 57:5
    ('crickets', 'locust[s]'), # DEU 28:42
    ('cried','weeping'), # Mrk 14:72
    ('cried', 'called'), # JDG 9:54
    ('cried', 'shouted'), # JDG 7:21
    ('cried', 'wept'), # EST 8:3
    ('crippled', 'lame'), # SA2 4:4
    ('crooked', 'bent'), # ECC 7:13
    ('crooked', 'crookedness'), # PRO 6:12
    ('crooked', 'perverse'), # PRO 8:8
    ('crop', 'craw'), # RV LEV 1:16
    ('cross', 'pass'), # DEU 3:25
    ('crossbars', 'bars'), # EXO 26:26 (reviewed 2026-10-13)
    ('crossed', 'pass'), # JOS 4:1
    ('crossed', 'passed'), # CH2 21:9
    ('crossing', 'fords'), # JDG 12:6
    ('crossing', 'pass'), # DEU 31:13
    ('crowd','multitude'),
    ('crowds', 'ochlos', 'aligned'),
    ('crowds', 'ochlousin', 'aligned'),
    ('cruel', 'cruelty'), # PRO 27:4
    ('cruel', 'ruthless'), # PSA 71:4
    ('cruelty', 'cruel'), # PRO 12:10
    ('crumbling', 'crumbs'), # JOS 9:12
    ('crush', 'shatter'), # DAN 7:23
    ('crush', 'smash'), # NUM 24:17
    ('crush', 'smashes'), # PSA 110:5
    ('Crush', 'smash'), # RV DEU 33:11
    ('crush', 'tramples'), # RV PSA 57:3 / LV PSA 57:4
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
    ('cubit','cubit[s]'),
    ('cubits','cubit[s]'),
    ('cultivate', 'labour'), # DEU 28:39
    ('cultivate', 'work'), # GEN 2:15
    ('cunning', 'guile'), # KI2 10:19
    ('cure', 'heal'), # JER 3:22
    ('cure', 'healed'), # DEU 28:27
    ('cured', 'healing'), # CH2 21:18
    ('curse', 'oath'), # SA1 14:26
    ('curses', 'oaths'), # DEU 30:7
    ('curses', 'oath'), # RV DEU 29:20 / LV DEU 29:19
    ('curtaining', 'curtains'), # EXO 36:8
    ('custom', 'decree'), # CH2 35:25
    ('customs', 'ways'), # CH2 7:14
    ('customs', 'tradition'), # RV MRK 7:9
    ('cypress', 'cypress[es]'), # ISA 41:19
    ('cypress', 'firs'), # RV CH2 2:8 / LV CH2 2:7
    ('damage', 'harm'), # RV PSA 74:3
    ('dance', 'dancings'), # SA1 29:5
    ('dance', 'leap'), # JOB 21:11
    ('dared', 'presumed'), # NUM 14:44
    ('dark','darkness'), # Mrk 15:33
    ('dark', 'night'), # JHN 13:30
    ('darken', 'dark'), # AMO 8:9
    ('darkened', 'dim'), # PSA 69:23
    ('Darkness', 'dark'), # JOB 11:17
    ('darkness', 'dark'), # LAM 3:6
    ('darkness', 'gloom'), # PSA 91:6
    ('darling', 'friend'), # SNG 1:9
    ('date','day'), # Mrk 13:32
    ('dawn','cockcrow'), # Mrk 13:35
    ('dawn', 'morning'), # RV PSA 46:5 / LV PSA 46:6
    ('day','day[s]'),
    ('day', 'daytime'), # NEH 9:19
    ('daylight', 'day'), # ACT 12:18
    ('days','day[s]'),
    ('daytime', 'day'), # EZE 12:7
    ('dead', 'shades'), # JOB 26:5
    ('dead', 'slain'), # CH1 10:8
    ('dealer', 'trader'), # EZE 27:16
    ('dear','beloved'),
    ('dearest', 'lover'), # SNG 1:13
    ('dearest', 'loves'), # ISA 48:14
    ('dearly','beloved'),
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
    ('decide','purposed'),
    ('decided', 'planning'), # RV DAN 6:3 / LV DAN 6:4
    ('decision','evaluate'),
    ('decision', 'counsel'), # EZR 10:8
    ('decision', 'judgement'), # NUM 27:21
    ('decision', 'verdict'), # DEU 17:11
    ('decisions','judgements'),
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
    ('declined','not'), # Mrk 15:23
    ('decorate', 'beautify'), # RV ISA 60:7
    ('decrease', 'diminish'), # EXO 5:8
    ('decreed', 'determined'), # DAN 9:27
    ('dedicate', 'consecrate'), # EXO 30:30
    ('dedicated', 'dedication'), # NUM 7:10
    ('dedicated', 'holy'), # CH1 26:20
    ('dedicated', 'consecrated'), # RV CH1 26:27
    ('deed', 'work'), # ACT 4:9
    ('deeds', 'works'), # JAM 2:20
    ('defeated', 'overcome'), # JN1 4:4
    ('defect', 'blemish'), # LEV 21:23
    ('defects', 'blemish'), # RV LEV 22:21
    ('defence', 'defended'), # LUK 21:14
    ('defence', 'defending'), # ACT 26:24
    ('defence', 'defense'), # ACT 25:16
    ('defend','answering'), # Mrk 14:60
    ('defend', 'defense'), # PHP 1:17
    ('defend', 'plead'), # PRO 31:9
    ('defender', 'defend'), # ZEC 12:8
    ('defending', 'defense'), # PHP 1:7
    ('defiant', 'rebellious'), # PRO 7:11
    ('deficient', 'lacking'), # RV DAN 5:27
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
    ('definitely','Truly'), # Mrk 15:39
    ('deformed','withered'),
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
    ('delivered', 'rescued'), # RV NEH 9:28
    ('demanded','saying'), # Mrk 15:14
    ('demanded', 'asked'), # PSA 137:3
    ('demanding', 'asking'), # JOB 31:30
    ('demolish','tearing'), # Mrk 14:58
    ('demolish', 'destroy'), # RV MIC 5:10 / LV MIC 5:9
    ('demon-possessed','unclean'),
    ('demonstrate', 'show'), # ISA 5:16
    ('demonstrated', 'showed'), # NUM 20:13
    ('demonstrating', 'demonstration'), # CO1 2:4
    ('den', 'hideout'), # LUK 19:46
    ('denied','disowned'), # Mrk 14:68,70
    ('denied','disowning'), # Mrk 14:68,70
    ('denigrating', 'slanderous'), # ACT 6:11
    ('depart', 'went'), # JOB 14:20
    ('departed','gone'), # Mat 2:9,13,14
    ('departed','withdrawn'), # Mat 2:9,13,14
    ('departed','withdrew'), # Mat 2:9,13,14
    ('departed', 'went'), # GEN 42:26
    ('deported', 'deportation'), # MAT 1:11
    ('deposed', 'removed'), # CH2 36:3
    ('depraved', 'perverted'), # RV MAT 17:17
    ('depths', 'deeps'), # ISA 63:13 (reviewed 2026-10-13)
    ('derision', 'mockery'), # EZE 23:32
    ('descend', 'falls'), # RV PRO 17:20
    ('descendant', 'descent'), # REV 22:16
    ('descendant', 'son'), # LUK 20:41
    ('descendants', 'children'), # EZE 2:4
    ('descendants', 'generation'), # ACT 8:33
    ('descendants', 'generations'), # JOS 22:28
    ('descendants', 'offspring'), # CH2 20:7
    ('descendants', 'posterity'), # DAN 11:4
    ('descendants', 'son'), # GEN 11:10
    ('descendants', 'sons'), # EZR 10:20
    ('descended', 'come'), # EPH 4:10
    ('descended', 'descent'), # ACT 4:6
    ('descendent', 'descent'), # PHP 3:5
    ('descriptions', 'describe'), # JOS 18:4
    ('desecrate', 'profane'), # EZE 23:39
    ('desecrated', 'profaned'), # EZE 25:3
    ('desert','ˊₐrāⱱāh'),
    ('desert', 'abandon'), # PSA 119:8
    ('deserted','desolate'),
    ('deserted', 'waste'), # EZE 6:14
    ('deserted', 'abandoned'), # RV ISA 6:12
    ('deserting', 'abandoned'), # SA1 8:8
    ('designer', 'skillful'), # EXO 38:23
    ('desirable', 'desirablenesses'), # SNG 5:16
    ('desirable', 'desire'), # JER 3:19
    ('desirable', 'desiring'), # LUK 15:16
    ('desire', 'hoping'), # RV CO2 13:9
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
    ('destroy', 'annihilate'), # RV PSA 83:4 / LV PSA 83:5
    ('destroyed','consumed'),
    ('destroyed','devoured'),
    ('destroyed', 'break'), # JER 48:38
    ('destroyed', 'broken'), # JER 48:4
    ('destroyed', 'destruction'), # EST 8:6
    ('destroyed', 'killed'), # PSA 78:47
    ('destroyed', 'ruined'), # LAM 2:5
    ('destroyed', 'ruins'), # RV MAL 1:4
    ('destroyer', 'destruction'), # PE2 2:3
    ('destroying', 'kill'), # HAB 1:17
    ('destroying', 'ruining'), # RV SA1 6:5
    ('destroys', 'destruction'), # PRO 18:9
    ('destroys', 'ruins'), # PRO 11:9
    ('destruction','devastation'),
    ('Destruction', 'devastation'), # HAB 1:3
    ('destruction', 'brokenness'), # LAM 4:10
    ('destruction', 'destroy'), # ISA 10:7
    ('destruction', 'destroyed'), # EXO 9:15
    ('destruction', 'destroying'), # CH1 21:12
    ('destruction', 'perish'), # OBA 1:12
    ('destruction', 'ruin'), # PRO 10:14 (reviewed 2026-10-13)
    ('destructive', 'destroyer'), # JER 51:1
    ('destructive', 'destroying'), # MAT 6:20
    ('destructive', 'destruction'), # EZE 9:1
    ('destructive', 'destructions'), # PRO 17:4
    ('destructive', 'disaster'), # JOB 30:12
    ('detain', 'delay'), # GEN 24:56
    ('determine','ascertained'), # Mat 2:7
    ('determine', 'fixed'), # JER 33:25
    ('determine', 'see'), # RV ZEC 2:2 / LV ZEC 2:6
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
    ("didn't",'not'),
    ('die', 'death'), # GEN 27:7
    ('die', 'expire'), # JOB 13:19
    ('die', 'perish'), # MAT 18:14
    ('die', 'perished'), # HEB 11:31
    ('die', 'perishing'), # ACT 13:41
    ('died','dead'), # Mrk 12:26, 15:39
    ('died','expired'), # Mrk 12:26, 15:39
    ('died', 'death'), # GEN 50:16
    ('died', 'perished'), # ACT 5:37
    ('dies','corpse'), # Lev 19:28
    ('dies', 'death'), # GEN 27:10
    ('difference', 'different'), # DAN 7:7
    ('different', 'another'), # JHN 14:16
    ('different', 'differently'), # TI1 1:3
    ('difficult', 'difficultly'), # LUK 18:24
    ('difficult', 'difficulty'), # ACT 27:7
    ('difficult', 'hard'), # DEU 1:17
    ('difficult', 'heavy'), # EZE 3:5
    ('difficulties', 'trouble'), # RV SA1 26:24
    ('dignified', 'dignity'), # TI1 3:4
    ('dignity', 'honour'), # PRO 31:25
    ('diligent', 'diligently'), # PRO 13:24
    ('dinner', 'supper'), # CO1 11:20 (reviewed 2026-10-13)
    ('dinners', 'suppers'), # LUK 20:46 (reviewed 2026-10-13)
    ('dinosaur','dragon'), # Rev 12:3
    ('directed', 'led'), # RV PRO 4:11
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
    ('disaster', 'calamities'), # RV PSA 78:49
    ('disasters','plagues'),
    ('disasters', 'calamities'), # DEU 32:23
    ('disasters', 'calamity'), # ISA 45:7
    ('disasters', 'harm'), # JER 36:3
    ('disbelief', 'unbelief'), # MAT 13:58
    ('discern', 'recognize'), # JOB 34:4
    ('discerning', 'distinguish'), # KI1 3:9
    ('discerning', 'distinguishing'), # CO1 11:29
    ('discerning', 'understanding'), # KI1 3:12
    ('disciples', 'mathetes', 'aligned'),
    ('disciples', 'mathetesin', 'aligned'),
    ('discipline', 'chasten'), # HOS 7:12
    ('discipline', 'correction'), # JER 17:23
    ('discipline', 'disciplinedpl'), # LEV 26:23
    ('discouraged','dismayed'),
    ('discouraged', 'disheartened'), # EZE 13:22
    ('discover', 'find'), # EZR 4:15
    ('discover', 'found'), # RV ROM 4:1
    ('discovered', 'finding'), # ROM 7:21
    ('discovered', 'found'), # EZR 4:19
    ('discovered', 'learned'), # ACT 28:1
    ('discovered', 'perceived'), # NEH 13:7
    ('discovered', 'find'), # RV PSA 36:2 / LV PSA 36:3
    ('discussion', 'discussed'), # ACT 18:19
    ('discussions', 'discussing'), # ACT 17:17
    ('disdain', 'scorn'), # RV EZE 36:5
    ('disease', 'plague'), # CH1 21:22
    ('disease', 'sickness'), # CH2 21:18
    ('disease', 'pestilence'), # CH2 7:13 (reviewed 2026-10-13)
    ('diseases', 'plague'), # PSA 91:3
    ('diseases', 'plagues'), # GEN 12:17
    ('diseases', 'sickness'), # EXO 15:26
    ('disgrace','expose'), # Mat 1:19
    ('disgrace', 'disgraceful'), # JDG 20:6
    ('disgrace', 'insult'), # KI2 19:3
    ('disgrace', 'reproach'), # GEN 30:23
    ('disgrace', 'shame'), # PRO 13:18
    ('disgrace', 'shamefully'), # PRO 13:5
    ('disgrace', 'dishonour'), # RV CO1 11:14
    ('disgrace', 'ignomini[es]'), # RV MIC 2:6
    ('disgraced', 'ignominy'), # RV JER 51:51
    ('disgraceful', 'shameful'), # EPH 5:12
    ('dishes', 'pans'), # CH2 24:14
    ('dishonest', 'unjust'), # EZE 22:13
    ('dishonour', 'violate'), # RV NUM 30:2 / LV NUM 30:3
    ('dishonourable', 'dishonour'), # ROM 1:26
    ('dishonoured', 'dishonourable'), # CO1 4:10
    ('dishonoured', 'shame'), # SA1 20:34
    ('dishonouring', 'disgracing'), # CO1 11:4
    ('dishonours', 'disgracing'), # CO1 11:5
    ('dismay', 'terrified'), # ISA 13:8
    ('dismayed', 'disturbed'), # PSA 6:10
    ('dismayed', 'terrified'), # JER 23:4
    ('disobedience', 'transgression', 'aligned'), # ISA 53:8
    ('disobeyed', 'disobedient'), # NEH 9:26
    ('disown','renounce'), # Mrk 14:31
    ('dispersed', 'dispersion'), # JAM 1:1
    ('display', 'show'), # MIC 7:15
    ('display', 'shown'), # PRO 24:10
    ('displayed', 'revealed'), # REV 3:18
    ('displayed', 'showed'), # EST 1:4
    ('dispute', 'contend'), # ECC 6:10
    ('disputes', 'dispute[s]'), # DEU 1:12
    ('disrespect', 'disregarding'), # TIT 2:15
    ('dissolve', 'melted'), # RV ISA 64:7 / LV ISA 64:6
    ('distance','afar'), # Mrk 14:54
    ('distance', 'distant'), # JOB 30:10
    ('distant', 'distance'), # DEU 28:49
    ('distant', 'distances'), # ISA 33:17
    ('distinguish', 'distinction'), # EZE 22:26
    ('distinguish', 'distinctions'), # CO1 12:10
    ('distinguish', 'separate'), # GEN 1:18
    ('distinguished', 'separate'), # RV NUM 8:14
    ('distort', 'falsifying'), # CO2 4:2
    ('distress', 'trouble'), # PSA 81:7
    ('distressed', 'disturbed'), # RV PSA 6:3 / LV PSA 6:4
    ('distressing', 'trouble'), # JER 16:19
    ('divide', 'distribute'), # RV PSA 22:18 / LV PSA 22:19
    ('divided', 'cut'), # PSA 136:13
    ('divided', 'split'), # ISA 63:12
    ('divination', 'divine'), # MIC 3:11
    ('divination', 'diviner'), # JOS 13:22
    ('diviners', 'divine'), # MIC 3:7
    ('diviners', 'soothsayers'), # ISA 19:3 (reviewed 2026-10-13)
    ('division', 'group'), # NUM 2:4
    ('division', 'groups'), # NUM 1:52
    ('divisions', 'groups'), # NUM 1:3
    ('divisions', 'troop[s]'), # CH2 26:11
    ('divorce','send'), # Mat 1:19
    ('do', 'act'), # EZE 36:36
    ('do', 'acts'), # JOB 34:12
    ('doctor', 'physician'), # JER 8:22
    ('doctor', 'Physician'), # RV LUK 4:23
    ('doctors', 'physicians'), # CH2 16:12
    ('doing', 'practicing'), # JN1 3:22
    ('dominate', 'rule'), # RV EZE 29:15
    ('dominated', 'prevailed'), # CH2 27:5
    ('dominion', 'rule'), # RV PSA 72:8
    ('donation', 'contribution'), # NUM 18:24
    ('donations', 'contributions'), # RV NUM 18:19
    ('done', 'acted'), # PSA 39:9
    ('done', 'practice'), # LUK 23:51
    ('done', 'made'), # RV PSA 40:5 / LV PSA 40:6
    ('done', 'works'), # RV PSA 46:8 / LV PSA 46:9
    ('donkey', 'colt'), # MRK 11:4
    ('donkeys', 'donkey[s]'), # JOS 6:21
    ('donkeys', 'she-asses'), # CH1 27:30
    ("Don't",'not'),
    ("don't",'not'),
    ('door', 'entrance'), # GEN 6:16
    ('doors', 'entrances'), # EZE 42:4
    ('doors', 'doorways'), # RV SNG 7:13 / LV SNG 7:14
    ('doors', 'gates'), # RV CH2 14:7 / LV CH2 14:6
    ('doorway', 'door'), # MRK 2:2
    ('doorway', 'entrance'), # KI2 4:15
    ('doorway', 'threshold'), # KI1 14:17
    ('doorways', 'threshold'), # ZEP 2:14
    ('double', 'twofold'), # RV EXO 22:7 / LV EXO 22:6
    ('down','below'), # Mrk 14:66
    ('downfall', 'fall'), # RV PSA 5:10 / LV PSA 5:11
    ('downward', 'downwards'), # EZE 8:2
    ('dozen', 'twelve'), # MAT 26:53
    ('draw', 'lot'), # RV JOS 19:32
    ('dreadful', 'terrible'), # DAN 7:19
    ('dreamers', 'dreaming'), # JDE 1:8
    ('dreamers', 'dreams'), # JER 27:9
    ('dress', 'clothe'), # EXO 40:14
    ('dress', 'clothed'), # RV JOB 40:10
    ('dressed','clothed'), # Mrk 16:5
    ('dressed', 'garment'), # PRO 7:10
    ('dressed', 'clothes'), # RV DAN 3:21
    ('dressed', 'girded'), # RV PSA 30:11 / LV PSA 30:12
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
    ('drives', 'pushing'), # RV PSA 35:5
    ('driving','throwing'),
    ('driving', 'dispossess'), # JDG 2:21
    ('driving', 'dispossessed'), # NUM 32:39
    ('drop', 'drip'), # JOB 36:28
    ('drop', 'fall'), # PSA 106:26
    ('drop', 'threw'), # JOB 29:17
    ('drop', 'fell'), # RV JAM 1:11
    ('dropped', 'fallen'), # MAT 18:26
    ('dropped', 'threw'), # CH2 24:10
    ('dropped', 'throw'), # KI2 2:16
    ('droppings', 'dungs'), # RV KI2 6:25
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
    ('during', 'in', 'aligned'),
    ('dust', 'debris'), # RV NEH 4:2 / LV NEH 3:34
    ('dying', 'death'), # HEB 11:5
    ('dying', 'perish'), # JOB 29:13
    ('dying', 'perishing'), # JOB 31:19
    ('dying', 'perishes'), # RV ECC 7:15
    ('each','all'), # Mrk 14:23
    ('eager', 'zealous'), # TIT 2:14
    ('earnestly', 'earnestness'), # ROM 12:8
    ('earrings', 'earring[s]'), # EXO 35:22
    ('earth', 'land'), # HOS 6:3
    ('earth', 'ground'), # RV LAM 2:2
    ('earthly', 'earth'), # ACT 4:26
    ('earthly', 'earthy'), # CO1 15:49
    ('east', 'eastward'), # DEU 3:17
    ('eastern','east'),
    ('eastern', 'eastward'), # CH1 26:14
    ('eat', 'consume'), # RV DEU 28:38
    ('eaten', 'consumed'), # PSA 69:9
    ('eaten', 'food'), # RV PSA 44:11 / LV PSA 44:12
    ('eats', 'feeding'), # RV ISA 44:20
    ('effect', 'effective'), # HEB 9:17
    ('elderly', 'old'), # RV JOL 2:28 / LV JOL 3:1
    ('elders', 'old'), # JDG 2:7
    ('elders', 'presbyteros', 'aligned'),
    ('elders', 'presbyterousin', 'aligned'),
    ('eldest', 'firstborn'), # CH1 8:30
    ('eliminate','destroying'),
    ('eliminate', 'extinguish'), # EZE 32:7
    ('eliminate', 'destroy'), # CH2 12:12 (reviewed 2026-10-13)
    ('embarrassed', 'abashed'), # JER 15:9
    ('embers', 'coals'), # PRO 26:21
    ('emerald-looking', 'emerald'), # REV 4:3
    ('Emperor', 'king'), # EST 1:17
    ('emperor', 'king'), # EST 1:13
    ('empowered', 'power'), # RV ECC 5:19 / LV ECC 5:18
    ('empress', 'queen'), # EST 1:18
    ('empty-handed', 'empty'), # DEU 15:13
    ('enchanters', 'conjurers'), # DAN 5:7
    ('encircled', 'surrounded'), # RV JDG 16:2
    ('encountered', 'found'), # LUK 7:9
    ('encourage', 'strengthen'), # PSA 64:5
    ('encourage', 'comforters'), # RV PSA 69:20 / LV PSA 69:21
    ('encouraged','exhorting'),
    ('encouraged', 'strengthened'), # SA1 23:16
    ('encouragement', 'exhortation'), # ACT 9:31 (reviewed 2026-10-13)
    ('encouraging', 'exhorting'), # CO2 5:20 (reviewed 2026-10-13)
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
    ('enemies', 'foe'), # RV ZEC 8:10
    ('enemy', 'foe'), # AMO 3:11
    ("enemy's", 'foe'), # RV PSA 107:2
    ('engaged','betrothed'),
    ('engaged', 'betrothing'), # MAT 24:38
    ('engaged', 'betroth'), # RV DEU 28:30
    ('engraved', 'engravings'), # EXO 28:21
    ('enjoy', 'delight'), # ISA 55:2
    ('enjoy', 'delights'), # PRO 18:2
    ('enjoy', 'loving'), # RV PE1 3:10
    ('enjoyed', 'delights'), # PRO 8:30
    ('enjoying', 'delights'), # PRO 8:31
    ('enjoyment', 'pleasure'), # ECC 8:15
    ('enlarge', 'increase'), # CH1 4:10
    ('enough', 'sufficiency'), # PRO 27:27
    ('enrich', 'rich'), # PSA 65:9
    ('enriched', 'rich'), # CO2 9:11
    ('ensnare', 'snares'), # JOB 34:30
    ('ensure','order'), # Mrk 14:19
    ('ensure', 'see'), # RV JER 51:61
    ('entered','come'), # Mat 2:11
    ('enthusiastic','eager'), # Mrk 14:38
    ('entice', 'deceive'), # CH2 18:20
    ('entice', 'persuade'), # RV HOS 2:14 / LV HOS 2:16
    ('enticed', 'deceived'), # JOB 31:9
    ('enticing', 'enticements'), # LAM 2:14
    ('entire','all'),
    ('entire', 'whole', 'aligned'), # EPH 2:21
    ('entirely', 'entirety'), # EXO 28:31
    ('entrance','door'), # Mrk 16:3
    ('entrance', 'gate'), # EXO 32:26
    ('entrance', 'opening', 'aligned'), # EXO 33:8
    ('entry', 'entrance'), # RV PE2 1:11
    ('entryway', 'entrance'), # RV EZE 41:17
    ('enveloped', 'swallowed'), # CO2 5:4
    ('envied', 'jealous'), # GEN 30:1
    ('envious', 'jealous'), # PRO 24:1
    ('envision', 'see'), # RV ZEC 10:2
    ('envy', 'jealous'), # PRO 3:31
    ('envying', 'jealous'), # PRO 23:17
    ('equal', 'comparable'), # JOB 28:17
    ('equipment', 'article'), # LEV 13:52
    ('equipment', 'articles'), # NUM 3:36
    ('erect', 'upright'), # RV LEV 26:13
    ('erected', 'raised'), # ISA 23:13
    ('error', 'inadvertence'), # ECC 10:5
    ('escape', 'escapees'), # EZE 6:8
    ('escape', 'fugitives'), # OBA 1:14
    ('escape', 'flight'), # RV MAT 24:20
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
    ('established', 'installed'), # RV PRO 8:23
    ('established', 'gave'), # RV EZE 20:12
    ('establishes', 'appointed'), # JOB 34:24
    ('establishes', 'making'), # JOB 25:2
    ('esteem', 'valued'), # ISA 53:3
    ('eternal', 'perpetuity'), # ECC 12:5
    ('eternity', 'perpetuity'), # ECC 3:11
    ('everyone','all'),
    ('everyone','people'),
    ('everyone','one'),
    ('Everyone','one'),
    ('everywhere','all'), # Mrk 15:33
    ('evidence','fruit'), # Mat 3:8
    ('evidence', 'signs'), # RV PSA 65:8 / LV PSA 65:9
    ('evil','sinners'), # Mrk 14:41
    ('evil', 'harm'), # SA1 20:7
    ('evil', 'iniquity'), # EZE 18:30
    ('evil', 'wicked'), # EZE 20:43
    ('evil', 'wickedness'), # PSA 10:7
    ('evils', 'iniquity'), # JOB 20:27
    ('examine', 'examination'), # ACT 25:26
    ('examine', 'see'), # RV LEV 13:15
    ('examines', 'test'), # RV PSA 7:9 / LV PSA 7:10
    ('examines', 'tests'), # RV PSA 11:5
    ('exceeding', 'surpassing'), # EPH 1:19
    ('exceeds', 'surpassing'), # EPH 3:19
    ('excellence', 'excellent'), # CO2 4:7
    ('execute', 'kill'), # JHN 18:31 (reviewed 2026-10-13)
    ('executed','death'), # Mrk 13:12
    ('execution','stake'),
    ('exempt', 'free'), # RV SA1 17:25
    ('exhaled','expired'), # Mrk 15:37
    ('exhausted', 'weary'), # SA1 14:31
    ('exiles', 'exile[s]'), # EZE 11:24
    ('existence','became'),
    ('exiting', 'going'), # EXO 19:1
    ('expand', 'enlarge'), # RV EXO 34:24
    ('expanded', 'enlarge'), # PSA 119:32
    ('expectation', 'hope'), # CO2 3:12 (reviewed 2026-10-13)
    ('expected', 'look'), # HAG 1:9
    ('expecting', 'awaiting'), # CO1 16:11
    ('expecting', 'wait'), # PSA 71:14
    ('experience', 'know'), # NUM 14:31
    ('experience', 'see'), # ACT 13:35
    ('experienced', 'known'), # JDG 3:1
    ('experienced', 'saw'), # ACT 13:37
    ('experienced', 'seen'), # EST 9:26
    ('experienced', 'knowing'), # RV CO2 8:9
    ('experienced', 'knew'), # RV KI1 9:27
    ('experiencing', 'know'), # RV NUM 14:34
    ('explain', 'declaring'), # JHN 16:14
    ('explained', 'declared'), # ACT 15:4
    ('explore', 'spy'), # NUM 13:17
    ('explored', 'spied'), # NUM 13:21
    ('explored', 'spy'), # NUM 14:7
    ('explored', 'searched'), # RV ECC 2:3
    ('exploring', 'spying'), # NUM 13:25
    ('expose', 'exhibit'), # RV HOS 2:3 / LV HOS 2:5
    ('expose', 'uncover'), # RV DEU 22:30 / LV DEU 23:1
    ('expose', 'uncovered'), # RV EXO 20:26
    ('expose', 'revealing'), # RV CO1 4:5
    ('exposed','uncovered'),
    ('express', 'declare'), # RV PSA 51:15 / LV PSA 51:17
    ('expression', 'face'), # RV JOB 9:27
    ('Extend', 'stretch'), # EXO 10:12
    ('extended', 'stretched'), # EZE 2:9
    ('extending', 'stretched'), # MAT 12:49
    ('extension', 'prolonging'), # DAN 7:12
    ('extent', 'measure'), # RV PSA 39:4 / LV PSA 39:5
    ('extortion', 'oppression'), # RV ECC 5:8 / LV ECC 5:7
    ('extremely', 'exceedingly'), # LUK 18:23 (reviewed 2026-10-13)
    ('eyelashes', 'eyelids'), # PRO 6:25
    ('Ezrahite', 'Ezrachite'), # RV KI1 4:31 / LV KI1 5:11
    ('face', 'cheek'), # KI1 22:24
    ('facing', 'front'), # EZE 40:45
    ('fading', 'withers'), # ISA 28:1
    ('fails', 'abandoned'), # RV PSA 40:12 / LV PSA 40:13
    ('faint', 'weary'), # SA1 14:28
    ('fainting', 'enfeebled'), # LAM 2:19
    ('fairness', 'righteousness'), # RV ISA 9:7 / LV ISA 9:6
    ('faith', 'faithfulness'), # HAB 2:4
    ('faithful', 'faith'), # REV 13:10
    ('faithful', 'faithfulness'), # DEU 32:4
    ('faithful', 'faithfulnesses'), # ISA 26:2
    ('faithfully', 'faith'), # ROM 1:5
    ('faithfully', 'faithful'), # TIT 1:9
    ('faithfully', 'faithfulness'), # CH2 31:12
    ('faithfulness','loyalty'),
    ('fall', 'come'), # MAT 23:35
    ('fall', 'dropped'), # JER 50:43
    ('false', 'falsehood'), # EZE 13:8
    ('falsely', 'false'), # MAT 15:19
    ('falsely', 'falsehood'), # PSA 119:78
    ('falter', 'stumble'), # RV MRK 9:42
    ('fame', 'memorial'), # RV HOS 14:7 / LV HOS 14:8
    ('familiar', 'acquainted', 'aligned'), # ISA 53:3
    ('families', 'clan'), # JDG 13:2
    ('families', 'clans'), # AMO 3:2
    ('families', 'household'), # JOB 21:21
    ('families', 'households'), # EXO 1:21
    ('families', 'houses'), # RV PSA 49:11 / LV PSA 49:12
    ('family', 'clan'), # LEV 25:41
    ('family', 'clans'), # EXO 12:21
    ('family', 'house'), # CH1 7:23
    ('family', 'household'), # GEN 50:22
    ('family', 'offspring'), # EZE 17:13
    ("family's", 'household'), # RV CH1 10:6
    ('famished', 'hungry'), # GEN 41:55
    ('famous', 'great'), # RV MIC 5:4 / LV MIC 5:3
    ('fasted', 'fastings'), # CO2 11:27
    ('fat', 'fatness'), # ISA 17:4
    ('father', 'ancestor', 'both'), # CH1 29:10; positional: CH1 2:55
    ('fathers','parents'),
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
    ('Fearfulness', 'fear'), # RV PSA 55:5 / LV PSA 55:6
    ('fearsome', 'awesome'), # RV NEH 4:14 / LV NEH 4:8
    ('feathers', 'plumage'), # EZE 17:7
    ('fed', 'ate'), # DEU 32:13
    ('fed', 'eat'), # DEU 8:16
    ('feed', 'eat'), # RV HOS 4:8
    ('feed', 'grazes'), # RV PSA 80:13 / LV PSA 80:14
    ('feeding', 'eat'), # DEU 8:3
    ('fellow','man'), # Mrk 14:51
    ('festival', 'feast'), # JHN 6:4 (reviewed 2026-10-13)
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
    ('figures', 'images'), # RV EZE 7:20
    ('filled', 'satisfied'), # RV HAB 2:16
    ('filled', 'surfeited'), # RV PSA 88:3 / LV PSA 88:4
    ('fills', 'surfeits'), # JOB 9:18
    ('filth', 'filthiness'), # JAM 1:21
    ('filth', 'impure'), # LAM 1:17
    ('filthiness', 'excrement'), # PRO 30:12
    ('final', 'last'), # JAM 5:3
    ('finally','Lastly'),
    ('finally','last'),
    ('find','saw'), # Mrk 16:5
    ('fine', 'pure'), # RV PSA 19:10 / LV PSA 19:11
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
    ('firebrands', 'firewood'), # ISA 7:4
    ('firepans', 'fire-pans'), # EXO 38:3
    ('fire-trays', 'fire-pans'), # EXO 27:3
    ('firewood', 'woods', 'aligned'), # CH1 21:23
    ('firm', 'strong'), # DAN 9:27
    ('firstfruits', 'first-fruits'), # EZE 44:30
    ('fishermen','fishers', 'both'),
    ('fishers', 'fishermen'), # MAT 4:19
    ('fissures', 'fractures'), # RV PSA 60:2 / LV PSA 60:4
    ('fitting','befitting'),
    ('fix', 'set'), # EZE 40:4
    ('flame', 'fire'), # JAM 3:5
    ('flames','fire'),
    ('flaming', 'burning'), # PRO 26:18
    ('flash', 'shine'), # JOB 37:15
    ('flat', 'unleavened', 'aligned'), # DEU 16:8
    ('flattered','saying'),
    ('flattery', 'flattering'), # DAN 11:32
    ('flattery', 'smooth'), # PSA 5:9
    ('flaw', 'blemish'), # DEU 32:5
    ('fleet', 'ship[s]'), # KI1 9:26
    ('fleshly', 'flesh'), # GAL 4:13
    ('flicked','sprinkled'),
    ('flock', 'sheep'), # EXO 9:3
    ('flocks', 'flock[s]'), # CH1 4:39
    ('flocks', 'sheep'), # EXO 34:3
    ('flogged', 'floggings'), # ACT 22:24
    ('flood', 'waters'), # JOB 27:20
    ('flood', 'river'), # RV JNA 2:3 / LV JNA 2:4
    ('floods', 'overflowing'), # RV CH1 12:15 / LV CH1 12:16
    ('floodwaters', 'flood'), # GEN 7:7
    ('flour', 'doughs'), # RV NEH 10:37 / LV NEH 10:38
    ('flourish', 'thrive'), # RV ZEC 9:17
    ('flower', 'blossom'), # CH2 4:21
    ('flowers', 'blossom'), # JOB 14:2
    ('flowers', 'blossoms'), # EXO 25:31
    ('flowing', 'streams'), # PRO 5:15
    ('fog', 'mist'), # RV ACT 13:11
    ('Follow', 'come'), # KI2 6:19
    ('follow', 'observe'), # DEU 5:1
    ('follow', 'pursue'), # ISA 51:1
    ('follow', 'pursuing'), # PE2 2:10
    ('follow', 'walk'), # RV HOS 14:9 / LV HOS 14:10
    ('followed', 'come'), # JHN 11:45
    ('followed', 'pursued'), # RV SA1 23:25
    ('followed', 'pursuing'), # RV LUK 1:6
    ('follower', 'apprentices/followers'), # JHN 13:35
    ('followers', 'apprentices/followers'), # ACT 6:7
    ('followers', 'following'), # MAT 8:10
    ('following', 'coming'), # ACT 13:44
    ('following', 'pursue'), # LUK 17:23
    ('following', 'next'), # RV CH1 29:21
    ('food','bread'),
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
    ('footsteps', 'footprints'), # RV PSA 89:51 / LV PSA 89:52
    ('force', 'drive'), # EXO 34:11
    ('forced','compelling'), # Mrk 15:21
    ('forces', 'army'), # JOB 10:17
    ('forces', 'drives'), # RV JOB 20:15
    ('foreign', 'foreigner'), # JER 50:37
    ('foreign', 'foreignness'), # CH2 33:15
    ('foreign', 'strange'), # JER 2:25
    ('foreign', 'strangers'), # RV JOL 3:17 / LV JOL 4:17
    ('foreigner', 'alien'), # EXO 12:45
    ('foreigner', 'foreign'), # DEU 17:15
    ('foreigner', 'foreignness'), # ISA 56:3
    ('foreigner', 'sojourner', 'aligned'), # DEU 27:19
    ('Foreigners', 'foreignness'), # PSA 18:44
    ('foreigners', 'alien'), # NUM 35:15
    ('foreigners', 'alien[s]'), # LEV 25:6
    ('foreigners', 'aliens'), # LEV 25:23
    ('foreigners', 'foreign'), # JDG 19:12
    ('foreigners', 'foreignness'), # EXO 12:43
    ('foreigners', 'sojourner', 'aligned'), # DEU 16:14; EZE 11:9
    ('foreigners', 'strangers', 'aligned'), # DEU 16:14; EZE 11:9
    ('forest', 'tree[s]'), # PSA 74:5
    ('forested', 'forest'), # JOS 17:15
    ('forever','perpetuity'),
    ('forever','eternal'),
    ('forever', 'ever'), # DAN 2:44
    ('forgetfulness', 'forgetting'), # PSA 88:12
    ('forgets', 'forgetful'), # JAM 1:25
    ('forgive', 'atone'), # PSA 65:3
    ('forgive', 'atonement'), # CH2 29:24
    ('forgive', 'forgiveness'), # ACT 5:31
    ('forgiven','forgiveness', 'both'),
    ('forgiven', 'atoned'), # ISA 22:14
    ('forgiven', 'atonement'), # EZE 16:63
    ('forgives', 'forgiveness'), # COL 1:14
    ('formed', 'made'), # RV JHN 2:15
    ('formless', 'formlessness'), # GEN 1:2
    ('forsake', 'abandon'), # DAN 11:30
    ('forsaken', 'abandoned'), # RV JER 15:6
    ('forsook', 'abandoned'), # JDG 10:6
    ('fortified','fortification'),
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
    ('fragrance', 'aroma'), # RV JHN 12:3
    ('fragrant', 'perfumed'), # SNG 3:6
    ('fragrant', 'perfumes'), # EXO 25:6
    ('frames', 'frame[s]'), # EXO 26:20
    ('frames', 'rims'), # KI1 7:35
    ('free', 'release'), # HEB 2:15
    ('freely', 'voluntariness'), # RV HOS 14:4 / LV HOS 14:5
    ('freeze', 'frost'), # RV ZEC 14:6
    ('fresh', 'freshly'), # GEN 8:11
    ('fresh', 'sweet'), # RV JAM 3:12
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
    ('frightened', 'terrified'), # RV DAN 8:17
    ('frightening', 'fearful'), # LUK 21:11
    ('front','before'), # Mrk 13:9
    ('front','face'), # Mrk 13:9
    ('front', 'faces/face'), # LEV 13:41
    ('frost', 'hoar-frost'), # EXO 16:14
    ('fruitful', 'fruit'), # EZE 19:10
    ('frustrated', 'distress'), # SA2 13:2
    ('fugitive', 'escapee'), # EZE 33:22
    ('fugitives', 'fugitive[s]'), # ISA 21:14
    ('fulfil', 'pay'), # PSA 61:8
    ('fulfilled','accomplished'),
    ('fulfilled', 'fulfillment'), # ACT 21:26
    ('fulfilled', 'paid'), # PSA 65:1
    ('fulfilled', 'filled'), # RV ECC 6:7
    ('fulfilment', 'fulfilled'), # MAT 1:22
    ('fullness', 'fills'), # DEU 33:16
    ('furious', 'anger'), # DAN 3:13
    ('furious', 'angered'), # REV 12:17
    ('furious', 'angry'), # KI2 5:11
    ('furious', 'enraged'), # RV DAN 8:7
    ('furnace', 'crucible'), # PSA 12:6
    ('furnace', 'kiln'), # EXO 19:18
    ('furnace', 'oven'), # RV MAL 4:1 / LV MAL 3:19
    ('further', 'advanced'), # MAT 4:21
    ('further', 'beyond'), # SA1 10:3
    ('further', 'furthermore'), # CO1 3:20
    ('further', 'farther'), # RV LUK 24:28
    ('fury', 'rage'), # EZE 6:12
    ('fury', 'anger'), # EZE 22:21 (reviewed 2026-10-13)
    ('futile', 'futility'), # ISA 30:7
    ('future', 'later'), # RV PSA 102:18 / LV PSA 102:19
    ('gain', 'profit'), # CO1 15:32
    ('gain', 'benefit'), # RV JDE 1:16
    ('gained', 'made'), # RV LUK 19:18
    ('gaining', 'acquired'), # EZE 38:12
    ('gaining', 'acquiring'), # LUK 21:19
    ('gains', 'increased'), # PRO 11:24
    ('gap', 'breach'), # JDG 21:15
    ('garbage', 'refuse'), # LAM 3:45
    ('garland', 'wreath'), # RV PRO 1:9
    ('gasp', 'panted'), # RV JER 15:9
    ('gatekeeper', 'doorkeeper'), # RV JHN 10:3
    ('gateway', 'gate'), # EZE 40:3
    ('gateway', 'door'), # RV HOS 2:15 / LV HOS 2:17
    ('gateways', 'gates'), # EZE 40:38
    ('gather', 'assembly'), # PRO 26:26
    ('Gather', 'Assemble'), # RV GEN 49:2
    ('gathered', 'assembled'), # CH2 32:4
    ('gathered', 'assembly'), # DEU 31:30
    ('gathered', 'met'), # JOB 2:11
    ('gathering', 'assembly'), # JER 15:17
    ('gatherings', 'assembly'), # RV PSA 26:5
    ('gave', 'delivered'), # DEU 32:30
    ('gave', 'granted'), # PHP 2:9
    ('gemstones', 'stone'), # CH2 9:1
    ('gemstones', 'stone[s]'), # CH2 3:6
    ('genealogical', 'genealogy'), # HEB 7:3
    ('genealogies', 'genealogical'), # CH2 31:18
    ('generals', 'leaders'), # DAN 9:6
    ('generations', 'generation[s]'), # CH1 16:15
    ('generosity', 'grace'), # ROM 5:21 (reviewed 2026-10-13)
    ('generous', 'generosity'), # ROM 12:8
    ('generously', 'abundantly'), # RV PSA 65:10 / LV PSA 65:11
    ('gentiles', 'ethne', 'aligned'),
    ('gentiles', 'ethnesin', 'aligned'),
    ('gentle', 'gentleness'), # CO1 4:21
    ('gentleness', 'gentle'), # PHP 4:5
    ('genuine', 'true'), # RV CO2 6:8
    ('genuineness', 'genuine'), # CO2 8:8
    ('gerahs', 'gerah[s]'), # EZE 45:12
    ('get','take'), # Mrk 15:36
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
    ('Get', 'Take'), # RV JER 36:2
    ('Get', 'Receive'), # RV LUK 16:7
    ('get', 'received'), # RV MAT 13:56
    ('gets', 'become'), # PRO 13:11
    ('gets', 'comes'), # RV EXO 1:19
    ('getting', 'become'), # MRK 6:35
    ('getting', 'receiving'), # JHN 5:41
    ('getting', 'take'), # JOB 18:20
    ('gift', 'given'), # RV MAT 19:11
    ('girl', 'woman'), # AMO 2:7
    ('girls', 'daughters'), # GEN 28:6
    ('girls', 'women'), # NUM 31:35
    ('girls', 'daughter'), # RV EXO 1:22
    ('give', 'contribute'), # EZE 48:9
    ('give', 'deliver'), # DEU 2:31
    ('give', 'grant'), # PSA 118:25
    ('give', 'handing'), # MAT 7:10
    ('give', 'pay'), # PSA 56:12
    ('give', 'restore'), # ZEP 3:9
    ('given', 'granted'), # CO1 2:12
    ('given', 'gift'), # RV MRK 7:11
    ('gives', 'deliver'), # DEU 7:16
    ('glad', 'rejoice'), # RV ZEC 2:10 / LV ZEC 2:14
    ('gladness', 'rejoicing'), # PSA 45:15
    ('gladness', 'joy'), # RV PSA 45:7 / LV PSA 45:8
    ('glided', 'swooped'), # RV PSA 18:10 / LV PSA 18:11
    ('glittering', 'lightning'), # NAH 3:3
    ('gloat', 'rejoice'), # RV PSA 38:16 / LV PSA 38:17
    ('gloating', 'exultation'), # HAB 3:14
    ('GLORIOUS', 'glories'), # PE1 1:11
    ('glorious', 'glories'), # PE2 2:10
    ('glorious', 'glory'), # ISA 4:2
    ('glory', 'splendour'), # EZE 31:18
    ('glory', 'honour'), # RV DAN 4:30 / LV DAN 4:27
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
    ('godlessness', 'ungodliness'), # RV TI2 2:16
    ('godliness', 'devoutness'), # PE2 1:3 (reviewed 2026-10-13)
    ('godly','devout'),
    ('godly','righteous'),
    ("God's",'god'), # Mrk 14:25, 13:11
    ("God's",'holy'), # Mrk 14:25, 13:11
    ('goes', 'walks'), # PSA 73:9
    ('goes', 'turns'), # RV JOB 24:18
    ('golden','gold'),
    ('gone', 'passed'), # DEU 27:4
    ('gone', 'passing'), # PSA 144:4
    ('gone', 'perishing'), # RV JAM 4:14
    ('good', 'goodness'), # ZEC 9:17
    ('good', 'sound'), # JOB 26:3
    ('good', 'upright'), # ECC 7:29
    ('good', 'Goodness'), # RV PSA 119:66
    ('goodness', 'good'), # CH2 6:41
    ('gorge', 'satisfy'), # EZE 32:4
    ('gorged', 'satisfied'), # REV 19:21
    ('got', 'arrived'), # ACT 9:26
    ('got', 'became'), # ACT 14:5
    ('got', 'took'), # GEN 27:15
    ('government', 'dominion'), # RV ISA 9:6 / LV ISA 9:5
    ('governor', 'governing'), # LUK 2:2
    ('governor', 'overseer'), # KI1 4:19
    ('governor', 'ruler'), # GEN 42:6
    ('governors', 'overseers'), # KI1 4:7
    ('grab','apprehending'), # Mrk 14:51
    ('grab','apprehend'), # Mrk 14:51
    ('grab', 'snatching'), # JHN 6:15
    ('grabbed','taken'), # Mrk 14:51
    ('grabbed', 'seized'), # ACT 19:29
    ('grabbed', 'took'), # JDG 15:15
    ('grabbing', 'snatching'), # MAT 11:12
    ('grabbing', 'took'), # SA1 14:32
    ('graceful', 'grace'), # PRO 1:9
    ('gracious', 'favour'), # GEN 33:11
    ('grain', 'seed'), # JOB 39:12
    ('grains', 'groats'), # LEV 2:16
    ('grandchildren', 'sons'), # RV GEN 31:55 / LV GEN 32:1
    ('Grant', 'give'), # PSA 119:27
    ('grant', 'giving'), # REV 2:7
    ('grant', 'fulfill'), # RV PSA 20:5 / LV PSA 20:6
    ('grant', 'give'), # RV PSA 21:6 / LV PSA 21:7
    ('granted', 'given'), # GAL 3:22
    ('grape', 'grape[s]'), # LEV 19:10
    ('grape-pickers', 'gatherers'), # OBA 1:5
    ('grapes','vine'), # Mrk 14:25
    ('grapes', 'grape[s]'), # DEU 32:14
    ('grapevine','vine'), # Mrk 14:25
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
    ('greater','mightier'),
    ('Greater', 'great'), # JOS 19:28
    ('greater', 'great'), # CH2 9:22
    ('greatest', 'great'), # CH1 17:8
    ('greatest', 'greater'), # CO1 13:13
    ('greatly', 'abundance'), # CH1 4:38
    ('greatness', 'great'), # EZE 38:23
    ('greatness', 'glory'), # CO2 3:18 (reviewed 2026-10-13)
    ('greed', 'greediness'), # EPH 5:3
    ('greedily', 'greediness'), # EPH 4:19
    ('green', 'greenery'), # GEN 1:30
    ('greeted', 'greetings'), # MAT 23:7
    ('grew', 'raised'), # ACT 13:1
    ('grief', 'vexation'), # PSA 10:14
    ('grief', 'sorrow'), # RV PSA 13:2 / LV PSA 13:3
    ('grief', 'mourning'), # REV 18:7 (reviewed 2026-10-13)
    ('grieving', 'mourning'), # RV REV 21:4
    ('grinding', 'grinders'), # ECC 12:3
    ('gripping', 'hold'), # MIC 4:9
    ('groans', 'groanings'), # LAM 1:22
    ('groom', 'bridegroom'), # JER 33:11
    ('grooms', 'bridegroom'), # JER 16:9
    ("groom's", 'bridegroom'), # RV MAT 25:6
    ('ground', 'earth'), # PSA 7:5
    ('ground', 'earth/land'), # DEU 12:16
    ('ground', 'land'), # CH2 20:24
    ('ground', 'soil'), # GEN 2:7
    ('group', 'company'), # EZE 23:46
    ('group', 'crowd'), # RV DAN 6:6 / LV DAN 6:7
    ('group', 'assembly'), # RV JER 9:2 / LV JER 9:1
    ('groups', 'divisions'), # CH2 35:12
    ('groves', 'trees'), # DEU 6:11
    ('growing', 'sprouting'), # EXO 10:5
    ('grown', 'arisen'), # EZE 7:11
    ('grows', 'sprouting'), # HEB 12:15
    ('grows', 'sprouts'), # PSA 90:6
    ('grumbled', 'murmured'), # DEU 1:27
    ('guarantee', 'surety'), # PRO 11:15 (reviewed 2026-10-13)
    ('guarantor', 'guarantee'), # HEB 7:22
    ('guard','doorkeeper'), # Mrk 13:34, 14:44
    ('guard','securely'), # Mrk 13:34, 14:44
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
    ('guards', 'bodyguard'), # RV SA1 22:14
    ('guests', 'invited'), # PRO 9:18
    ('guide','shepherding'), # Mat 2:6
    ('Guide', 'direct'), # PSA 119:133
    ('guide', 'direct'), # LUK 1:79
    ('guides', 'leads'), # RV PSA 25:9
    ('guilt', 'guilty'), # HOS 5:15
    ('guilt', 'iniquity'), # HOS 5:5
    ('guilty', 'guilt'), # JHN 19:4
    ('guilty', 'guilts'), # CH2 28:10
    ('guilty', 'iniquity'), # LEV 5:1
    ('guilty', 'wicked'), # PRO 24:24
    ('guy\'s','man'), # Mrk 14:69
    ('hacked', 'cut'), # SA1 15:33
    ('hairstyles', 'hairs'), # PE1 3:3
    ('halfway', 'middle'), # PRO 7:9
    ('hammer', 'beat'), # ISA 2:4
    ('hammered', 'beat'), # EXO 39:3
    ('hand','giving'), # Mrk 13:11, 14:41
    ('Hand', 'give'), # KI2 6:29
    ('hand', 'deliver'), # AMO 1:6
    ('hand', 'give'), # CO1 5:5
    ('hand', 'palm'), # DEU 25:12
    ('hand', 'palms'), # JOB 41:8
    ('handed','given'), # Mrk 13:11, 14:41
    ('handed', 'delivered'), # AMO 1:9
    ('handed', 'gave'), # JER 39:14
    ('handing', 'giving'), # JHN 18:5
    ('handlers', 'handled'), # JER 2:8
    ('hands', 'giving'), # CO1 15:24
    ('hands', 'palm'), # EZE 6:11
    ('hands', 'palms'), # CH2 6:12
    ('handwriting', 'hand'), # CO1 16:21
    ('happen','become'), # Mrk 13:29
    ('happen','becoming'), # Mrk 13:29
    ('happened', 'occurred'), # JDG 19:30
    ('happened', 'passed'), # CH1 29:30
    ('happening','becoming'), # Mrk 13:29
    ('happily', 'joy', 'aligned'), # ISA 52:8
    ('happiness', 'gladness'), # EST 8:16 (reviewed 2026-10-13)
    ('happy','elated'), # Mat 2:10
    ('happy', 'blessed'), # PRO 14:21
    ('happy', 'glad'), # ISA 35:1
    ('happy', 'rejoices'), # RV ISA 64:5 / LV ISA 64:4
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
    ('harvesters', 'reaper'), # RV JER 9:22 / LV JER 9:21
    ('harvesting', 'reaping'), # LUK 19:21
    ('harvests','fruit'),
    ('harvests', 'reaping'), # JHN 4:37
    ('hastening', 'hurrying'), # RV PE2 3:12
    ('hatches', 'brood'), # JER 17:11
    ('hate', 'hatred'), # EZE 23:29
    ('hated', 'hatred'), # DEU 9:28
    ('have','bearing'), # Mat 1:21
    ('head', 'chief'), # CH1 23:11
    ('heads', 'chiefs'), # CH2 5:2
    ('heads', 'ears', 'aligned'), # GEN 41:22
    ('heal', 'cure'), # LUK 7:3
    ('healed', 'clean'), # KI2 5:12
    ('health', 'healthy'), # MRK 5:34
    ('healthy', 'firm'), # ZEC 11:16
    ('healthy', 'health'), # PRO 14:30
    ('Hear', 'listen'), # CH2 20:20
    ('hear', 'listen'), # NEH 13:27
    ('hear', 'listened'), # PSA 55:17
    ('hear', 'listens'), # RV JOB 31:35
    ('heard', 'listened'), # CH2 30:27
    ('hearing', 'sound'), # RV PSA 44:16 / LV PSA 44:17
    ('heart', 'bosom'), # RV PSA 89:50 / LV PSA 89:51
    ('heart-felt', 'heart'), # ISA 59:13
    ('heaven', 'heavenly'), # PHP 2:10
    ('heavenly','heavens'),
    ('heavenly','heaven'),
    ('heavens', 'cloud[s]'), # RV PSA 89:6 / LV PSA 89:7
    ('heaves', 'lifted'), # NAH 1:5
    ('heavy', 'thick'), # RV PSA 18:9 / LV PSA 18:10
    ('heeds', 'keeps'), # PRO 13:18
    ('heels', 'feet'), # JDG 5:15
    ('heights', 'high'), # ECC 12:5
    ('held','giving'), # Mrk 15:36
    ('held', 'grasped'), # SNG 3:4
    ('held', 'kept'), # ACT 12:5
    ('held', 'taken'), # EZE 6:9
    ('help', 'deliverance'), # PSA 3:2
    ('help', 'helper'), # DAN 11:45
    ('help', 'service'), # NUM 7:7
    ('helped', 'assisted'), # TI1 5:10
    ('helped', 'rescued'), # RV PSA 81:7 / LV PSA 81:8
    ('helper', 'help'), # RV PSA 44:26 / LV PSA 44:27
    ('helping', 'helpers'), # CO1 12:28
    ('herds', 'cattle'), # EXO 34:3
    ('herds', 'herd[s]'), # DEU 12:6
    ('heritage', 'inheritance'), # JOB 20:29
    ('herod', 'herodes', 'aligned'),
    ('herodians', 'herodianoi', 'aligned'),
    ('herodians', 'herodianousin', 'aligned'),
    ('hesitated', 'delayed'), # GEN 19:16
    ('hid', 'covered'), # RV PSA 32:5
    ('hidden', 'concealed'), # LUK 9:45
    ('hide', 'concealing'), # GEN 18:17
    ('hiding', 'secret'), # LAM 3:10
    ('high', 'height'), # CH2 4:1
    ('high', 'height[s]'), # PSA 93:4
    ('high', 'heights'), # JOB 25:2
    ('high', 'loftiness'), # PSA 62:4
    ('high', 'lofty'), # ISA 2:14
    ('high', 'chief', 'aligned'), # HEB 4:15
    ('highway', 'way'), # NUM 21:22
    ('hill','mountain'),
    ('hill', 'mountains'), # KI2 2:16
    ('hills','mountains'),
    ('hills', 'mountain'), # DEU 8:7
    ('hilltop','high'),
    ('hinges', 'hinge[s]'), # PRO 26:14
    ('history', 'accounts'), # RV GEN 2:4
    ('hit', 'struck'), # EXO 2:12
    ('hit', 'shot'), # RV CH2 35:23
    ('hitched', 'harnessed'), # SA1 6:10
    ('hits', 'strike'), # EXO 21:18
    ('hitting', 'striking'), # EXO 2:13
    ('hoarded', 'kept'), # RV ECC 5:13 / LV ECC 5:12
    ('hold', 'restrained'), # ECC 2:10
    ('hold', 'retaining'), # HEB 10:23
    ('hold', 'taken'), # EPH 6:16
    ('hold', 'contain'), # RV JER 2:13
    ('holding', 'delaying'), # LUK 1:21
    ('holding', 'handles'), # AMO 2:15
    ('holiness', 'holy'), # EZE 28:22
    ('hollow', 'empty'), # JER 48:30
    ('home', 'habitation'), # JER 49:33
    ('home', 'house'), # CH2 11:4
    ('home', 'tent'), # JDG 19:9
    ('home', 'tents'), # CH2 7:10
    ('home', 'place'), # RV SA2 19:39 / LV SA2 19:40
    ('homes', 'habitation'), # JOB 5:3
    ('homes', 'house'), # DEU 7:26
    ('homes', 'household'), # PRO 12:7
    ('homes', 'households'), # NUM 16:32
    ('homes', 'houses'), # HOS 11:11
    ('homes', 'tents'), # JOS 22:6
    ('homes', 'Houses'), # RV JOB 21:9
    ('homes', 'dwellings'), # RV LUK 16:9
    ('honest','true'),
    ('honest', 'righteousness'), # GEN 30:33
    ('honestly', 'truly'), # JHN 1:51 (reviewed 2026-10-13)
    ('honeycomb', 'honey'), # SA1 14:25
    ('honour','glorify'),
    ('honour', 'beautify'), # EZR 7:27
    ('honour', 'dignity'), # JOB 30:15
    ('honour', 'greatness'), # PSA 71:21
    ('honour', 'fear'), # RV PSA 40:3 / LV PSA 40:4
    ('honour', 'fearing'), # RV PSA 60:4 / LV PSA 60:6
    ('honour', 'glory'), # ACT 12:23 (reviewed 2026-10-13)
    ('honourable', 'honour'), # ISA 5:13
    ('honourable', 'honoured'), # ISA 3:5
    ('honourable', 'noble'), # PSA 45:9
    ('honoured','great'), # Mrk 14:45
    ('honoured', 'glory/honour'), # EST 8:16
    ('honoured', 'uplifted'), # JOB 22:8
    ('honoured', 'exalted'), # RV PSA 108:5 / LV PSA 108:6
    ('hoofbeats', 'hoof-beats'), # JDG 5:28
    ('hooks', 'knives'), # RV JOL 3:10 / LV JOL 4:10
    ('hooves','hoof'), # Not covered by the noun matcher's numberVariants().
    ('hope', 'wait'), # RV PSA 69:6 / LV PSA 69:7
    ('hoping', 'desiring'), # RV LUK 16:21
    ('horde', 'company'), # EZE 17:17
    ('horn', 'trumpet'), # AMO 2:2
    ('horns', 'trumpets'), # JDG 7:22
    ('horrible','abomination'), # Mrk 13:14
    ('horseriders', 'horsemen'), # ISA 22:6
    ('horses', 'horse[s]'), # ISA 43:17
    ('horses', 'horsemen'), # GEN 50:9
    ('horses', 'steed[s]'), # EST 8:14
    ('host', 'innkeeper'), # RV LUK 10:35
    ('hostages', 'pledges'), # CH2 25:24
    ('hostility', 'enmities'), # GAL 5:20
    ('hostility', 'enmity'), # EPH 2:14
    ('hostility', 'animosity'), # HOS 9:7 (reviewed 2026-10-13)
    ('hot', 'live'), # ISA 6:6
    ('house', 'habitation'), # PRO 21:20
    ('house', 'home'), # MRK 14:14
    ('house', 'household'), # GEN 12:1
    ('houseful', 'house'), # NUM 22:18
    ('household', 'house'), # ACT 7:10
    ('house-servants', 'servants'), # PE1 2:18
    ('however', 'nevertheless'), # CH2 30:11 (reviewed 2026-10-13)
    ('hug', 'embraced'), # MRK 9:36
    ('huge','great'),
    ('hugged', 'embraced'), # LUK 15:20
    ('hugging', 'embraced'), # MRK 10:16
    ('human', 'humankind'), # DAN 8:17
    ('human', 'man'), # DAN 7:13
    ('humanity','man'), # Mrk 13:26
    ('humanity', 'humankind'), # ECC 2:3
    ('humanity', 'Man'), # RV JHN 1:51
    ("humanity's", 'humankind'), # RV PSA 89:47 / LV PSA 89:48
    ('humankind', 'human'), # JAM 3:7
    ('humankind', 'mankind'), # RV JHN 1:4
    ('humanly', 'humans'), # LUK 18:27
    ('Humans', 'humankind'), # PSA 62:9
    ('humans', 'humankind'), # CH2 6:18
    ('humans', 'man'), # RV CH2 14:11 / LV CH2 14:10
    ('humble', 'afflict'), # LEV 16:31
    ('humble', 'lowly'), # RV JOB 5:11
    ('humbled', 'afflicted'), # JOB 30:11
    ('humbled', 'low'), # ISA 2:12
    ('humbles', 'low'), # SA1 2:7
    ('humbly', 'humble'), # PRO 6:3
    ('humbly', 'modest'), # MIC 6:8
    ('humilation', 'humiliation'), # EZR 9:5
    ('humiliate', 'humble'), # SA2 13:12
    ('humiliated','ashamed'),
    ('humiliated', 'humbled'), # SA2 13:14
    ('humiliating', 'humbled'), # RV SA2 13:22
    ('hunchback', 'hunchbacked'), # LEV 21:20
    ('hungry', 'hunger'), # DEU 8:3
    ('hungry', 'hungered'), # LUK 4:2
    ('hungry', 'hungering'), # CO1 4:11
    ('hunter', 'hunted'), # PRO 12:27
    ('hurled', 'threw'), # JDG 15:17
    ('hurling','many'), # Mrk 15:3
    ('hurls', 'throw'), # JOB 27:22
    ('hurried', 'haste'), # SA1 25:34
    ('hurried', 'rushed'), # RV SA2 19:17 / LV SA2 19:18
    ('hurriedly', 'hurried'), # JOS 8:14
    ('Hurry', 'haste'), # PSA 70:5
    ('hurry', 'haste'), # PSA 71:12
    ('hurry', 'hasten'), # RV JER 9:18 / LV JER 9:17
    ('hurry', 'hastened'), # RV JOS 10:13
    ('hurrying', 'haste'), # ISA 49:17
    ('hurt', 'harmed'), # RV DAN 6:22 / LV DAN 6:23
    ('hurting', 'bruising'), # MRK 5:5
    ('hurting', 'harm'), # RV PSA 40:14 / LV PSA 40:15
    ('husband', 'husband/man'), # EZE 16:32
    ('husbands', 'husband/man'), # RUT 1:9
    ('hut','shelter'),
    ('hypocritical', 'hypocrisy'), # TI1 4:2
    ('idol', 'image'), # DEU 4:25
    ('idol', 'teraphim'), # SA1 19:13
    ('idolatrous', 'idolater'), # EPH 5:5
    ('idolatrous', 'pagan'), # HOS 10:5
    ('idols', 'image'), # CH2 33:15
    ('idols', 'images'), # DEU 7:5
    ('idols', 'teraphim'), # ZEC 10:2
    ('ignorant', 'ignorance'), # CO1 15:34
    ('ignored', 'neglected'), # RV JOB 20:19
    ('illuminate', 'light'), # NEH 9:12
    ('illuminating', 'light'), # RV REV 18:23
    ('imagine', 'think'), # MAT 5:17
    ('imitate', 'imitators'), # CO1 4:16
    ('imitated', 'imitators'), # TH1 1:6
    ('immersed', 'immersion', 'both'), # ACT 13:24
    ('immerser','immersing'),
    ('immortal', 'immortality'), # CO1 15:53
    ('impartiality', 'uprightness'), # RV PSA 67:4 / LV PSA 67:5
    ('impatient', 'short'), # MIC 2:7
    ('important', 'greater'), # MRK 12:31
    ('imprison', 'imprisonment'), # KI1 22:27
    ('imprisoned', 'captive'), # ROM 7:23
    ('imprisoned', 'shut'), # JER 32:2
    ('imprisoned', 'confined'), # RV KI2 17:4
    ('imprisonment', 'bonds'), # ACT 23:29 (reviewed 2026-10-13)
    ('imprisons', 'shut'), # JOB 11:10
    ('impure', 'impurity'), # EPH 4:19
    ('impure', 'unclean'), # ECC 9:2
    ('impurities', 'uncleannesses'), # EZE 36:25
    ('impurity', 'uncleanness'), # ZEC 13:2
    ('in','in/on/at/with'),
    ('incense', 'smoke'), # CH2 34:25
    ('incinerated', 'burned'), # MAT 13:40
    ('incinerator', 'furnace'), # MAT 13:42 (reviewed 2026-10-13)
    ('inclined', 'inclination'), # GEN 8:21
    ('included','among'), # Mrk 15:40
    ('including','and'), # Mrk 15:40
    ('increase', 'add'), # DEU 1:11
    ('increased', 'added'), # EZE 23:14
    ('increased', 'numerous'), # HOS 10:1
    ('increasingly', 'increase'), # DAN 11:39
    ('incredible','great'), # Mrk 13:26
    ('indeed','already'), # Mrk 15:44
    ('indicating', 'signifying'), # JHN 12:33 (reviewed 2026-10-13)
    ('indignant', 'indignation'), # LAM 2:6
    ('individual', 'person'), # RV JOB 34:29
    ('indulge', 'gratify'), # ECC 2:3
    ('infant', 'sucking'), # LAM 2:11
    ('infants', 'sucking'), # PSA 8:2
    ('inform', 'known'), # EZR 5:10
    ('informed', 'told', 'aligned'), # KI1 20:17
    ('informing', 'known'), # CO1 12:3
    ('inhabit', 'dwell'), # AMO 9:14
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
    ('injured', 'maimed'), # RV EXO 22:10 / LV EXO 22:9
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
    ('inscribed', 'write'), # RV NUM 17:2 / LV NUM 17:17
    ('inside', 'inner'), # DEU 32:25
    ('inside', 'midst'), # DAN 7:15
    ('inside', 'within', 'both'), # CH2 3:4
    ('insides', 'inner'), # ISA 16:11
    ('insightful', 'insight'), # PRO 12:8
    ('insignificant','least'), # Mat 2:6
    ('insignificant', 'lowly'), # EZE 29:14
    ('inspect', 'visit'), # JOB 5:24
    ('inspecting', 'examining'), # NEH 2:13 (reviewed 2026-10-13)
    ('instant', 'moment'), # ISA 51:4
    ('instead', 'rather'), # ROM 14:13
    ('instruct', 'teach'), # PRO 22:19
    ('instruct', 'teaching'), # CO1 2:16
    ('instruct', 'teaches'), # RV PSA 25:12
    ('instructed','commanded'), # Mrk 13:34
    ('instructed', 'learning'), # CO1 14:31
    ('instructing', 'teach'), # SA1 12:23
    ('instruction', 'command'), # PE2 3:2
    ('instruction', 'correction'), # JOB 36:10
    ('instruction', 'discipline'), # PRO 1:2
    ('instruction', 'law'), # PSA 119:55
    ('instructions','commanded'),
    ('instructions','regulations'),
    ('instructions', 'command'), # GEN 49:33
    ('instructions', 'commands'), # MRK 10:19
    ('instructions', 'law'), # HOS 8:12
    ('instructions', 'laws'), # PSA 105:45
    ('instructs','commanded'), # Mrk 13:34
    ('instruments', 'instrument/flute'), # GEN 4:21
    ('insult','slander'), # Mrk 14:64, 15:29
    ('insult', 'reviles'), # RV PSA 44:16 / LV PSA 44:17
    ('insulted','dishonoured'), # Mrk 14:64, 15:29
    ('insulted','slandering'), # Mrk 14:64, 15:29
    ('insulting','slandering'), # Mrk 14:64, 15:29
    ('insults', 'insult[s]'), # EZE 36:6
    ('integrity', 'blamelessness'), # PSA 84:11
    ('intend', 'think'), # DAN 7:25
    ('intensity', 'strength'), # RV PSA 90:11
    ('intercede', 'entreat'), # GEN 23:8
    ('interest', 'usury'), # NEH 5:10
    ('interior', 'middle'), # SNG 3:10
    ('interior', 'inner'), # RV EZE 42:15
    ('intervene', 'interposed'), # ISA 59:16
    ('intervened', 'mediated'), # PSA 106:30
    ('into', 'in', 'aligned'),
    ('into', 'to', 'aligned'),
    ('intoxicated', 'drunk'), # REV 17:2
    ('invaded', 'attacks'), # HAB 3:16
    ('invalidate', 'annul'), # JOB 40:8
    ('invalidated', 'voided'), # CO2 9:3
    ('invested', 'put'), # RV MAT 25:27
    ('investigate','search'), # Mat 2:8
    ('investigated', 'sought'), # EST 2:23
    ('investigation', 'investigated'), # JDG 6:29
    ('invite', 'calling'), # LUK 14:13
    ('invited', 'called'), # ROM 1:6
    ('invited', 'receiving'), # RV JDG 19:15
    ("isn't",'not'),
    ('isolated', 'separated'), # RV PRO 19:4
    ('Israeli', 'Yisrāʼēl/Israel'), # RV SA1 24:2 / LV SA1 24:3
    ('Israelis','people'),
    ('Israelis', 'Yisrāʼēl/Israel'), # RV HOS 1:10 / LV HOS 2:1
    ('issues', 'questions'), # ACT 25:19 (reviewed 2026-10-13)
    ('item','article'),
    ('items','article'),
    ('items', 'articles'), # CH2 9:24 (reviewed 2026-10-13)
    ('jacinth', 'hyacinth'), # REV 21:20
    ('jairus', 'yairos', 'aligned'),
    ('james', 'iakovos', 'aligned'),
    ('jars', 'waterpots'), # JHN 2:6 (reviewed 2026-10-13)
    ('jealous','envy'), # Mrk 15:10
    ('jealous', 'envious'), # PSA 106:16
    ('jealous', 'jealousy'), # ACT 13:45
    ('jealous', 'zealous'), # NUM 11:29
    ('jealously', 'jealousy'), # ROM 13:13
    ('jericho', 'yeriho', 'aligned'),
    ('jew', 'ioudaion', 'aligned'),
    ('jew', 'youdaion', 'aligned'),
    ('jewellery', 'jewelry'), # RV HOS 2:13 / LV HOS 2:15
    ('jewels', 'corals'), # PRO 8:11
    ('jews', 'ioudaion', 'aligned'),
    ('jews', 'ioudaions', 'aligned'),
    ('jews', 'youdaions', 'aligned'),
    ('job', 'business'), # ECC 1:13
    ('jobs','work'), # Mrk 13:34
    ('john', 'ioannes', 'aligned'),
    ('join', 'united'), # RV GEN 49:6
    ('joined', 'united'), # ECC 9:4
    ('joking', 'jesting'), # RV PRO 26:18,PRO 26:19
    ('joking', 'jests'), # RV GEN 19:14
    ('jordan', 'yarden', 'aligned'),
    ('jostling', 'thrust'), # JOL 2:8
    ('journeys', 'journeyings'), # NUM 33:1
    ('joy', 'pleasure'), # ECC 2:2
    ('judas', 'ioudas', 'aligned'),
    ('judge','judgements'),
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
    ('just','this'),
    ('just', 'only', 'aligned'),
    ('justice', 'judge'), # PRO 31:9
    ('justice', 'judgement'), # ISA 5:16
    ('justice', 'judgements'), # PSA 119:149
    ('justice', 'justify'), # ISA 5:23
    ('justice', 'right'), # JOB 27:2
    ('justice', 'uprightness'), # PSA 45:6
    ('justus', 'ioustos', 'aligned'),
    ('Keep', 'preserve'), # PSA 119:107
    ('keep', 'holding'), # JHN 10:24
    ('keep', 'observe'), # PSA 119:33
    ('keep', 'observing'), # KI1 11:38
    ('keep', 'preserve'), # GEN 6:20
    ('Keep', 'Restrain'), # RV JER 2:25
    ('Keep', 'restrain'), # RV PRO 1:15
    ('keep', 'restrain'), # RV JER 31:16
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
    ('kill','destroy'),
    ('kill', 'death'), # EXO 17:3
    ('kill', 'slays'), # JOB 20:16
    ('kill', 'stone'), # EXO 17:4
    ('kill', 'strike'), # EZE 9:5
    ('kill', 'struck'), # JER 33:5
    ('killed','slain'),
    ('killed', 'death'), # CH2 25:27
    ('killed', 'defeated'), # JDG 1:10
    ('killed', 'slew'), # GEN 49:6
    ('killed', 'stoned'), # HEB 12:20
    ('killed', 'struck'), # CH1 10:2
    ('killing', 'defeated'), # SA1 7:11
    ('killing', 'struck'), # SA1 17:57
    ('kills', 'killer'), # JOS 21:13
    ('kills', 'strike'), # SA1 17:26
    ('kills', 'strikes'), # LEV 24:18
    ('kills', 'struck'), # NUM 35:15
    ('Kimham', 'Kimhan'), # RV SA2 19:40 / LV SA2 19:41
    ('kindness', 'loyalty'), # GEN 20:13
    ('King', 'kingdom'), # DEU 3:4
    ('king', 'kingdom'), # MAT 16:28
    ('king', 'royalty'), # RV PSA 22:28 / LV PSA 22:29
    ('kingdoms','nations'), # MAT 4:8
    ('kingdoms','countries'), # MAT 4:8
    ('kingly','purple'), # Mrk 15:17
    ('kings', 'kingdoms'), # CH2 12:8
    ('knelt','falling'), # Mrk 14:35
    ('knelt', 'fell', 'aligned'), # LUK 8:28
    ('knew', 'foreknew'), # ROM 8:29
    ('knocked', 'pushed'), # RV PSA 36:12 / LV PSA 36:13
    ('know','knowledge'),
    ('know', 'acknowledge'), # JOB 7:10
    ('knowledgable', 'knowledge'), # PRO 14:7
    ('knowledgeable', 'knowledge'), # KI1 7:14
    ('known', 'foreknown'), # PE1 1:20
    ('known', 'recognized'), # JER 28:9
    ('known', 'designated'), # RV CH1 12:31 / LV CH1 12:32
    ('labour', 'birth'), # GEN 35:17
    ('labour', 'toil'), # RV DEU 26:7
    ('labourers', 'labour'), # CH2 8:8
    ('labours', 'toils'), # RV HOS 12:8 / LV HOS 12:9
    ('lacking', 'missing'), # RV KI1 4:27 / LV KI1 5:7
    ('lady', 'woman'), # MAT 15:28
    ('laid','spread'),
    ('laid', 'put'), # EZE 11:7
    ('laid', 'set'), # RV DAN 6:17 / LV DAN 6:18
    ('laid', 'placed'), # RV KI1 13:30
    ('lake','sea'),
    ('lamb', 'ram'), # LEV 17:3
    ('lambs', 'rams'), # GEN 30:32
    ('lampstand', 'candlestick'), # DAN 5:5
    ('land','property'), # Mrk 14:32
    ('land', 'earth'), # CH1 4:40
    ('land', 'ground'), # GEN 7:22
    ('land', 'nations'), # DEU 18:14
    ('land', 'soil'), # DEU 28:21
    ('landing','coming'), # Mat 3:16
    ('language','tongue'),
    ('languages','tongues'),
    ('large','great'),
    ('Large', 'great'), # RV LUK 14:25
    ('larger', 'large'), # DEU 25:14
    ('last', 'finished'), # JOS 5:6
    ('later','after', 'both'), # Mrk 14:70
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
    ('lawyers', 'nomikos', 'aligned'),
    ('lawyers', 'nomikousin', 'aligned'),
    ('lay', 'put'), # RV PSA 84:3 / LV PSA 84:4
    ('lay', 'set'), # RV PSA 38:12 / LV PSA 38:13
    ('lazy', 'idle'), # TIT 1:12 (reviewed 2026-10-13)
    ('leader','ruler'),
    ('leader', 'chief'), # CH1 5:7
    ('leader', 'judge'), # JDG 2:19
    ('leader', 'overseer'), # NEH 12:42
    ('leader', 'prince'), # GEN 23:6
    ('leaders','rulers'),
    ('leaders', 'chiefs'), # CH2 28:12
    ('leaders', 'judges'), # CH1 17:6
    ('leaders', 'officials'), # CH1 29:24
    ('leaders', 'princes'), # HOS 7:3
    ('leaders', 'elders'), # RV SA2 19:11 / LV SA2 19:12
    ('leading', 'head'), # CH2 20:27
    ('learn', 'know'), # EZR 4:15
    ('learn', 'known'), # PHP 2:19
    ('learn', 'take/accept/receive'), # PRO 1:3
    ('learn', 'see'), # RV JOS 2:1
    ('learned', 'known'), # PSA 119:152
    ('leash', 'cord'), # RV JOB 41:2 / LV JOB 40:26
    ('least', 'insignificant'), # JNA 3:5
    ('least', 'little'), # NUM 11:32
    ('leather', 'hide'), # LEV 13:48 (reviewed 2026-10-13)
    ('Leave', 'depart'), # JOB 21:14
    ('Leave', 'go'), # CH2 26:18
    ('leave', 'depart'), # JDG 16:17
    ('leave', 'departed'), # EXO 33:11
    ('leave', 'go'), # EZE 46:8
    ('leave', 'going'), # JHN 6:67
    ('leave', 'departs'), # RV PSA 55:11 / LV PSA 55:12
    ('leaves', 'depart'), # LUK 12:36
    ('leaves', 'departs'), # ISA 46:7
    ('leaves', 'leafage'), # ISA 1:30
    ('leaves', 'foliage'), # RV DAN 4:12 / LV DAN 4:9
    ('leaving', 'abandoning'), # JOS 24:16
    ('leaving', 'go'), # EXO 13:4
    ('leaving', 'going'), # MRK 13:1
    ('leaving', 'gone'), # KI2 20:4
    ('led', 'guided'), # DEU 32:12
    ('led', 'taken'), # PRO 24:11
    ('led', 'took'), # CH1 8:7
    ('led', 'judged', 'aligned'), # JDG 10:2
    ('leeks', 'leek[s]'), # NUM 11:5
    ('left', 'abandoned'), # ISA 18:6
    ('left', 'departed'), # ACT 18:1
    ('left', 'going'), # ACT 5:41
    ('left', 'gone'), # JOS 2:7
    ('left', 'remain'), # LEV 26:39
    ('left', 'remains'), # ISA 7:22
    ('left', 'went'), # ACT 10:7
    ('left', 'followed', 'aligned'),
    ('legs', 'loins'), # RV PSA 69:23 / LV PSA 69:24
    ('lengthen', 'length'), # DEU 30:20
    ('lengthen', 'long'), # KI1 3:14
    ('leprosy', 'disease'), # CH2 26:19
    ('leprosy', 'leprous'), # LUK 17:12
    ('leprous', 'leprosy'), # LUK 5:12
    ('lesson','parable'), # Mrk 13:28
    ('let', 'allow'), # GEN 31:28
    ('let', 'allowed'), # ACT 16:7
    ('let', 'allowing'), # ACT 19:30
    ('let', 'permit'), # EXO 3:19
    ('let', 'permits'), # JOB 9:18
    ('Let', 'Allow'), # RV JHN 12:7
    ('let', 'Allow'), # RV MRK 10:14
    ('levites', 'leuites', 'aligned'),
    ('levites', 'leuitesin', 'aligned'),
    ('liberate', 'liberty'), # ISA 61:1
    ('liberates', 'free'), # PSA 146:7
    ('lice', 'gnats'), # RV EXO 8:16 / LV EXO 8:12
    ('lies', 'falsehood', 'aligned'), # DAN 11:27
    ('life', 'alive'), # PSA 119:93
    ('life', 'lifes'), # DAN 7:12
    ('life', 'live'), # EZE 37:9
    ('life', 'lived'), # EZE 37:10
    ('life', 'living'), # CO1 6:3
    ('life', 'spirits'), # NUM 16:22
    ('life', 'lifespan'), # RV JOB 11:17
    ('lifetime', 'days'), # KI1 11:12
    ('lifetime', 'life'), # RV PSA 30:5 / LV PSA 30:6
    ('lifetime', 'lifespan'), # RV MAT 6:27
    ('lifetimes', 'days'), # EZE 12:25
    ('lifetimes', 'lives'), # ECC 9:3
    ('lift', 'raise'), # EZE 26:8
    ('lift', 'raising'), # MAT 12:11
    ('lifted', 'raised'), # EPH 2:6
    ('light', 'brightness'), # ISA 50:10
    ('light', 'shone'), # JOB 10:22
    ('light', 'kindle', 'aligned'), # AMO 1:14
    ('light', 'lightness'), # RV CO2 1:17
    ('light', 'enlightening'), # RV PSA 19:8 / LV PSA 19:9
    ('lighter', 'lighten'), # JNA 1:5
    ('lightly', 'lightness'), # JER 3:9
    ('like', 'corresponding'), # EXO 38:18
    ('like', 'similar'), # JHN 8:55
    ('like', 'wishing'), # JHN 18:39
    ('like', 'as', 'aligned'),
    ('like', 'Similar'), # RV MAT 13:33
    ('like', 'equal'), # RV PSA 143:7
    ('likes', 'delights'), # RV PSA 22:8 / LV PSA 22:9
    ('likes', 'pleasure'), # RV ECC 5:4 / LV ECC 5:3
    ('limit', 'restrain'), # JOB 15:8
    ('linger', 'delay'), # PRO 23:30
    ('lips', 'mouth'), # EZE 33:31
    ('list', 'number'), # CH1 25:1
    ('listed', 'enrolled'), # CH1 5:17
    ('Listen','Behold'),
    ('listen','Behold'),
    ('Listen','behold'),
    ('listen','behold'),
    ('Listen','hearing'),
    ('listen','hear'),
    ('Listen', 'hear'), # DEU 9:1
    ('listen', 'attentive'), # NEH 1:11
    ('listen', 'heard'), # JHN 10:8
    ('listen', 'hearing'), # ACT 4:19
    ('listen', 'heed'), # MAL 2:16
    ('Listen', 'Hear'), # RV JAM 2:5
    ('listen', 'Hear'), # RV PSA 27:7
    ('listened', 'heard'), # ACT 24:24
    ('listened', 'hearing'), # ACT 15:12
    ('listener', 'listens'), # PRO 21:28
    ('listening', 'hear'), # KI1 3:11
    ('listening', 'hearing'), # ACT 10:44
    ('listening', 'heed'), # TI1 4:1
    ('listening', 'listeners'), # JAM 1:22
    ('listening', 'heard'), # RV ECC 12:13
    ('listens', 'hearing'), # LUK 6:47
    ('listens', 'hears'), # PRO 15:31
    ('listens', 'heeds'), # PRO 15:32
    ('listens', 'heard'), # RV LUK 6:49
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
    ('Live', 'dwell'), # RV JER 40:9
    ('lived', 'dwell'), # ISA 45:18
    ('lived', 'dwelling'), # CH2 16:2
    ('lived', 'dwelt'), # JDG 11:26
    ('lived', 'inhabitants'), # CH1 4:40
    ('lived', 'life'), # EXO 6:20
    ('lived', 'sojourned'), # DEU 26:5
    ('lived', 'feeding', 'aligned'),
    ('lives', 'alive'), # EZE 13:22
    ('lives', 'dwell'), # JER 51:43
    ('lives', 'dwelling'), # ISA 33:5
    ('lives', 'dwells'), # HOS 4:3
    ('lives', 'sojourns'), # NUM 15:16
    ('livestock', 'cattle'), # DEU 11:15
    ('living','dwelling'),
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
    ('loads', 'burden'), # RV NEH 4:17 / LV NEH 4:11
    ('loan', 'lend'), # RV EXO 22:25 / LV EXO 22:24
    ('loathe', 'abhor'), # PSA 119:163
    ('locked', 'secured'), # ACT 16:24
    ('locust', 'locust[s]'), # AMO 7:1
    ('locusts', 'locust[s]'), # DEU 28:38
    ('long', 'distant'), # KI2 19:25
    ('long', 'duration'), # PSA 146:2
    ('long', 'length'), # CH2 3:4
    ('long', 'prolong'), # DEU 4:26
    ('long', 'prolongs'), # ECC 7:15
    ('longings', 'desire'), # PSA 38:9
    ('Look','Behold'),
    ('look','Behold'),
    ('Look','behold'),
    ('look','behold'),
    ('Look', 'see'), # GEN 39:14
    ('look', 'considered'), # JOB 30:20
    ('look', 'search'), # MAT 10:11
    ('look', 'searching'), # JHN 5:39
    ('look', 'see'), # EZE 44:5
    ('look', 'seek'), # ACT 11:25
    ('look', 'seeking'), # ISA 41:17
    ('look', 'watch'), # PSA 68:16
    ('look', 'watching'), # MAT 26:38
    ('look', 'BEHOLD/LO/SEE'), # RV ECC 2:11
    ('Look', 'BEHOLD/LO/SEE'), # RV CH2 20:11
    ('look', 'appear'), # RV GAL 6:12
    ('look', 'seen'), # RV ISA 58:3
    ('Look', 'See'), # RV GAL 6:11
    ('look', 'appearing'), # RV MAT 23:27
    ('looked','focused'), # Mrk 14:67
    ('looked', 'appeared'), # DAN 1:15
    ('looked', 'saw'), # KI2 2:24
    ('looked', 'seeing'), # MAT 14:30
    ('looked', 'seeking'), # LUK 2:44
    ('looked', 'seen'), # HAB 3:6
    ('looking','searched'),
    ('looking','seeking'),
    ('looking', 'seek'), # PSA 10:13
    ('looking', 'seeing'), # RV DAN 4:13 / LV DAN 4:10
    ('lookouts', 'watchmen'), # SA1 14:16
    ('looks', 'see'), # EZE 33:3
    ('looks', 'sees'), # JOB 41:34
    ('looks', 'saw'), # RV EZE 28:18
    ('looks', 'face/front'), # RV EZE 3:9
    ('loose', 'free'), # RV JDG 16:20
    ('loose', 'untie/release'), # RV LEV 10:6
    ('loot', 'plunder'), # PSA 68:12
    ('looted', 'plundered'), # JER 50:37
    ('looted', 'plunder'), # RV ZEC 2:9 / LV ZEC 2:13
    ('lotion', 'ointment'), # JHN 12:5 (reviewed 2026-10-13)
    ('lots', 'plentiful'), # RV DAN 4:12 / LV DAN 4:9
    ('loud', 'sound'), # PSA 102:5
    ('louder','exceedingly'), # Mrk 15:14
    ('loudly','loud'),
    ('love','beloved'), # Mat 3:17
    ('love', 'loyalty'), # EXO 15:13
    ('loved','beloved'), # Mat 3:17
    ('lovers', 'paramours'), # EZE 23:20
    ('loves', 'beloved'), # ROM 1:7
    ('lower', 'downwards'), # EXO 39:20
    ('lower', 'low'), # PRO 25:7
    ('lowest', 'lower'), # KI1 6:6
    ('lowliest', 'insignificant'), # SA1 9:21
    ('lowly', 'small'), # GEN 19:11
    ('loyal', 'loyalty'), # KI1 8:23
    ('luke', 'loukas', 'aligned'),
    ('lying', 'deceiving'), # HOS 4:2
    ('lyres', 'harps'), # CH1 15:21
    ('made', 'caused'), # AMO 4:10
    ('made', 'established'), # LUK 1:68
    ('made', 'work'), # JOB 37:7
    ('made', 'working'), # EXO 24:10
    ('made', 'works'), # PSA 104:31
    ('made', 'form'), # RV PSA 103:14
    ('made', 'formed'), # RV ISA 54:17
    ('made-up', 'fabricated'), # RV PE2 2:3
    ('madman', 'mad'), # KI2 9:11
    ('maggots', 'maggot[s]'), # JOB 7:5
    ('magic', 'magical'), # ACT 19:19
    ('magic', 'enchantments'), # RV EXO 8:7 / LV EXO 8:3
    ('maintaining', 'holding'), # RV TI1 1:19
    ('majestic', 'majesty'), # ISA 30:30
    ('make', 'cause'), # EZE 26:20
    ('make', 'causes'), # ECC 10:1
    ('make', 'doing'), # JER 7:18
    ('make', 'establish'), # GEN 6:18
    ('make', 'prepare'), # ISA 40:20
    ('maker', 'made'), # ISA 17:7
    ('makes', 'caused'), # LAM 3:6
    ('makes', 'causing'), # PSA 104:14
    ('makes', 'causes'), # RV PSA 29:9
    ('making', 'establish'), # GEN 9:9
    ('man','one', 'both'),
    ('man', 'humankind'), # GEN 2:15
    ('man', 'person'), # PRO 28:2
    ('man', 'human'), # RV ACT 10:26
    ('manager', 'management'), # LUK 16:2
    ('mankind','humans'),
    ('mankind', 'humankind'), # DAN 4:32 (reviewed 2026-10-13)
    ("man's", 'human'), # RV PE2 2:16
    ('many','multiply'),
    ('many','all', 'both'), # MAT 4:5
    ('march', 'go'), # DEU 28:25
    ('march', 'going'), # RV NAH 2:5 / LV NAH 2:6
    ('march', 'tread'), # RV MIC 5:5 / LV MIC 5:4
    ('marched', 'going'), # EXO 14:8
    ('marches', 'go'), # JOL 2:8
    ('marches', 'goes'), # HAB 1:6
    ('mark', 'markos', 'aligned'),
    ('market', 'marketplace'), # MRK 7:4
    ('marketplace', 'square'), # PSA 55:11
    ('marketplaces', 'market'), # EZE 27:24
    ('marriage', 'marriable'), # CO1 7:36
    ('marry','receive'), # Mat 1:20
    ('marsh', 'swamp'), # JOB 40:21
    ('marvelled','astonished'),
    ('marvellous', 'wonderful'), # PSA 119:18
    ('marvellous', 'wonders'), # JOB 9:10
    ('masons', 'wall-builders'), # KI2 22:6
    ('master', 'mastership'), # PE2 2:10
    ('masters', 'head'), # LAM 1:5
    ('masters', 'owners'), # SA2 1:6
    ('material', 'stuff'), # RV EXO 28:31
    ('matters', 'message/thing/matter'), # EZR 10:14
    ('matthew', 'matthaios', 'aligned'),
    ('mauled', 'tore'), # KI2 2:24
    ('maybe', 'perhaps'), # ISA 47:12 (reviewed 2026-10-13)
    ('meadow', 'pastureland'), # HOS 9:13
    ('mean', 'hateful'), # TIT 3:3
    ('means','translated'), # Mrk 15:22
    ('measured', 'measurement'), # EZE 40:21
    ('measured', 'measurements'), # EZE 40:29
    ('measuring', 'measurement'), # EZE 40:3
    ('meat','flesh'),
    ('mediate', 'mediator'), # JOB 33:23
    ('medicines', 'medications'), # JER 30:13
    ('meditate', 'meditation'), # PSA 119:99
    ('meditate', 'contemplate'), # RV PSA 27:4
    ('meditating', 'meditation'), # PSA 119:97
    ('medium', 'necromancer'), # LEV 20:27
    ('medium', 'necromancy'), # CH1 10:13
    ('mediums', 'necromancer'), # KI2 21:6
    ('mediums', 'necromancers'), # ISA 8:19
    ('meet', 'filling'), # PHP 4:19
    ('meet', 'saw'), # GAL 1:19
    ('meet', 'see'), # JHN 12:21
    ('meeting','counsel'), # Mrk 15:1
    ('meeting', 'gathered'), # JHN 11:47
    ('melons', 'watermelons'), # NUM 11:5
    ('memorial', 'remembrance'), # PSA 38:0
    ('memory', 'memorial'), # ECC 9:5
    ('memory', 'remembrance'), # DEU 32:26
    ('men', 'humankind'), # PRO 23:28
    ('men', 'people'), # CH2 9:7
    ('men', 'person'), # DAN 5:7
    ("men's", 'humankind'), # RV GEN 6:2
    ('menstruating', 'menstruation'), # EZE 18:6
    ('menstruating', 'menstruous'), # LEV 15:24
    ('mentioned', 'remembrance'), # SA1 4:18
    ('mentioned', 'named'), # RV ISA 14:20
    ('merchandise', 'trading'), # PRO 31:18
    ('merchants', 'merchant[s]'), # EZE 16:29
    ('merchants', 'trader'), # GEN 23:16
    ('merchants', 'traders'), # NAH 3:16
    ('mercy', 'compassion'), # HOS 1:6
    ('mercy', 'compassions'), # PSA 69:16
    ('mercy', 'spare'), # HAB 1:17
    ('message', 'oracle'),
    ('message', 'utterance'),
    ('message', 'word'),
    ('message', 'report'), # ISA 53:1
    ('message', 'speech'), # SA2 23:2
    ('message', 'words/messages'), # AMO 1:1
    ('messages', 'speech'), # ACT 20:2
    ('messages', 'words/messages'), # EZE 2:7
    ('messenger', 'word'),
    ('messengers', 'messenger-like'), # LUK 20:36
    ('met','known'), # Mrk 14:71
    ('met', 'encountering'), # ACT 20:14
    ('met', 'fulfilled'), # ACT 2:1
    ('met', 'gathered'), # ACT 4:27
    ('met', 'received'), # JHN 18:3
    ('metal', 'molten'), # DAN 11:8
    ('metalworker', 'metalsmith'), # JER 10:14
    ('metres','cubits'),
    ('Meyshak', 'Meshach'), # DAN 2:49: named separately from Shadrak.
    ('midday', 'noons'), # GEN 43:25
    ('midday', 'noontides'), # KI1 18:26
    ('middle', 'heart'), # EZE 27:26
    ('middle', 'midst'), # ISA 5:8
    ('mighty', 'powerful/mightypl'), # GEN 6:4
    ('mighty', 'strong'), # ISA 40:26
    ('mind','heart'),
    ('mind', 'head'), # DAN 2:28
    ('minds', 'heart'), # CH1 22:19
    ('minds', 'hearts'), # ROM 2:15
    ('mingled', 'mixed'), # PSA 106:35
    ('minister', 'ministry'), # PHP 2:30
    ('minister', 'serve'), # CH1 15:2
    ('ministered', 'serves'), # NUM 4:37
    ('ministering', 'serve'), # CH2 5:14
    ('ministry', 'service'), # CO2 5:18 (reviewed 2026-10-13)
    ('minor', 'small'), # RV SA2 7:19
    ('miracle', 'sign', 'aligned'), # CH2 32:31
    ('miracles','signs'),
    ('miracles','wonders'),
    ('miracles', 'deed[s]'), # RV PSA 44:1 / LV PSA 44:2
    ('mirth', 'joy'), # RV HOS 2:11 / LV HOS 2:13
    ('miscarriages', 'miscarrying'), # EXO 23:26
    ('miserable', 'sufferer'), # JOB 3:20
    ('misery', 'calamity'), # GEN 44:34
    ('misery', 'trouble'), # PRO 31:7
    ('misfortune', 'disaster'), # JOB 12:5
    ('missing', 'lacked'), # CO1 1:7
    ('missionaries','ambassadors'),
    ('missionary', 'ambassador', 'aligned'), # CO1 9:1
    ('mist', 'clouds'), # RV JER 51:16
    ('mistakes', 'error'), # RV JOB 4:18
    ('mister','master'),
    ('Mister','Master'),
    ('mistreat', 'afflict'), # EXO 22:22
    ('mistreat', 'maltreat'), # RV DEU 23:16 / LV DEU 23:17
    ('mistreated', 'harm'), # NUM 20:15
    ('mistreated', 'maltreat'), # ISA 49:26
    ('mistreating', 'afflicted'), # GEN 16:6
    ('moan', 'groaning'), # RV JAM 5:9
    ('moan', 'murmur'), # RV PSA 55:17 / LV PSA 55:18
    ('mocked', 'contempt'), # RV NEH 4:4 / LV NEH 3:36
    ('Mockers', 'mockery'), # PRO 29:8
    ('mockers', 'mockeries'), # JER 51:18
    ('mockers', 'mockerpl'), # ISA 28:22
    ('modest', 'modesty'), # TI1 2:9
    ('money','reward'),
    ('money', 'silver'), # EST 3:11
    ('money-changers','moneychangers'),
    ('moneychangers', 'money-changers'), # JHN 2:14
    ('morning', 'dawn'), # RV AMO 4:13
    ('mothers','parents'),
    ('mount', 'mountain'), # CH2 33:15
    ('mount', 'rise'), # RV EZE 38:18
    ('mountains', 'mountainous'), # ISA 45:2
    ('mountainsides', 'mountains'), # EZE 34:13
    ('mountaintops', 'mountains'), # ISA 42:11
    ('mounted','sat'),
    ('mounted', 'rode'), # GEN 24:61
    ('mounted', 'settings'), # EXO 35:27
    ('mourn','weep'),
    ('mourn', 'mourners'), # ISA 61:2
    ('mourned', 'wept'), # NUM 20:29
    ('mourner', 'mourning'), # EST 6:12
    ('mourning','wailing'),
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
    ('moved', 'travelled'), # RV MAT 21:33
    ('moves', 'displaces'), # RV DEU 27:17
    ('Mt','mountain'),
    ('Mt','mount'),
    ('Mt', 'Mount'),
    ('mud', 'mire'), # PSA 69:2
    ('muddy', 'fouling'), # EZE 34:18
    ('multiple', 'multiplied'), # HOS 8:11
    ('multiplied', 'increase'), # JOB 29:18
    ('multiplied', 'increased'), # JOS 24:3
    ('multiplies', 'increases'), # RV HOS 12:1 / LV HOS 12:2
    ('multiply', 'increase'), # DEU 7:13
    ('multitudes', 'ochlos', 'aligned'),
    ('multitudes', 'ochlousin', 'aligned'),
    ('murdered','killed'),
    ('murdered','killing'),
    ('murderer', 'killer'), # NUM 35:19
    ('murderer', 'murdered'), # KI2 9:31
    ('murdering', 'kill'), # DEU 22:26
    ('murderous', 'murder'), # ACT 9:1
    ('murmured', 'grumbled'), # EXO 17:3
    ('murmurings', 'grumblings'), # EXO 16:9
    ('music', 'song'), # RV CH1 6:32 / LV CH1 6:17
    ('musical', 'music'), # DAN 3:7
    ('must','truly'), # Mrk 14:70
    ('must','will'), # Mrk 14:70
    ('mute', 'dumb'), # RV PSA 38:13 / LV PSA 38:14
    ('muttering', 'grumbling'), # JHN 7:32
    ('mysteries', 'secrets'), # DAN 2:28
    ('mysterious', 'mystery'), # CO1 2:7
    ('mystery', 'secret'), # DAN 2:30
    ('naked', 'nakedness'), # EZE 16:7
    ('nakedness', 'naked'), # GEN 3:7
    ('name', 'called'), # ACT 13:9
    ('name', 'describing'), # ACT 8:33
    ('named', 'called'), # CH1 13:11
    ('napping','sleeping'), # Mrk 13:36
    ('narrow', 'closed'), # EZE 41:16
    ('narrowed', 'closed'), # KI1 6:4
    ('nation', 'earth/land'), # EZE 45:4
    ('nation', 'land'), # EZE 25:6
    ('nationality', 'nation'), # ACT 17:26
    ('nations','peoples'),
    ('nations', 'lands'), # CH2 12:8
    ('native', 'native-born'), # EXO 12:19
    ('natives', 'native-born'), # EXO 12:49
    ('natural', 'nature'), # ROM 11:21
    ('naturally', 'nature'), # ROM 2:14
    ('nauseous', 'loathsome'), # RV NUM 11:20
    ('near', 'close'), # EXO 39:20
    ('near', 'Close'), # RV EXO 25:27
    ('nearby','by'), # Mrk 15:35
    ('nearby', 'near'), # RV DEU 13:7 / LV DEU 13:8
    ('nearest', 'near'), # NUM 27:11
    ('necessary','fitting'),
    ('necessary', 'necessity'), # HEB 7:27
    ('necklaces', 'ornament'), # NUM 31:50
    ('needs','let'),
    ('neglected', 'abandoned'), # RV DEU 29:25 / LV DEU 29:24
    ('negligent', 'negligence'), # EZR 4:22
    ('neighbour', 'friend'), # PRO 12:26
    ('neutralise', 'nullifying'), # TH2 2:8
    ('new', 'newness'), # ROM 6:4
    ('news','report'),
    ('News', 'message'), # ACT 11:22
    ('news', 'information'), # EZE 24:26
    ('news', 'message'), # JOS 22:33
    ('news', 'new[s]'), # PSA 112:7
    ('News', 'words/messages'), # RV PRO 18:8
    ('nicanor', 'nikanor', 'aligned'),
    ('nicknamed', 'called'), # ACT 1:23 (reviewed 2026-10-13)
    ('nicolas', 'nikolaos', 'aligned'),
    ('night', 'night[s]'), # GEN 7:12
    ('nights', 'night[s]'), # DEU 9:9
    ('night-time', 'night'), # KI2 7:12
    ('nighttime', 'night'), # CH2 21:9
    ('noblemen', 'nobles'), # DAN 5:10
    ('nobles', 'honoured'), # NAH 3:10
    ('noise', 'sound'), # EZE 26:10
    ('non-Jews','pagans'),
    ('noon', 'noontides'), # KI1 18:27
    ('north', 'northward'), # CH1 9:24
    ('northerly', 'north'), # PRO 25:23
    ('northern', 'north'), # DAN 11:6
    ('northern', 'northerner[s]'), # JOL 2:20
    ('northern', 'northward'), # CH1 26:14
    ('north-facing', 'north'), # EZE 42:2
    ('north-facing', 'northward'), # EZE 46:19
    ('northward', 'north'), # JOS 18:17
    ('nostrils', 'nose'), # JOB 27:3
    ('note', 'observe'), # PSA 107:43
    ('notice', 'regard'), # RUT 2:19
    ('Notice', 'observing'), # RV HEB 7:4
    ('notice', 'see'), # RV PSA 64:5 / LV PSA 64:6
    ('noticed','saw'),
    ('noticed', 'found'), # NUM 15:32
    ('noticed', 'seen', 'aligned'), # ACT 7:24
    ('nullified', 'broken'), # RV NUM 30:12 / LV NUM 30:13
    ('number', 'count'), # RV JOB 38:37
    ('numerous', 'great'), # DEU 30:5
    ('nursed', 'sucking'), # RV SNG 8:1
    ('oath', 'swear'), # HOS 4:15
    ('oath', 'swears'), # JER 51:14
    ('oath', 'swore'), # REV 10:6
    ('oath', 'sworn'), # AMO 8:7
    ('oaths', 'sworn'), # JER 5:7
    ('obedience', 'righteousness'), # RV PSA 7:8 / LV PSA 7:9
    ('obedient', 'obedience'), # CO2 10:5
    ('obey','submitting'),
    ('Obey', 'listen'), # JER 38:20
    ('obey', 'listen'), # SA1 15:19
    ('obey', 'observe'), # RV CH2 14:4 / LV CH2 14:3
    ('obey', 'yielded'), # RV PSA 81:11 / LV PSA 81:12
    ('obeyed', 'listened'), # JOS 22:2
    ('obeying', 'righteousness'), # RV PSA 4:5 / LV PSA 4:6
    ('object', 'instrument'), # NUM 35:16
    ('obligations', 'duty'), # NUM 3:8
    ('observe','watching'), # Mrk 13:33
    ('Observe', 'keep'), # DEU 5:12
    ('observe', 'keep'), # EXO 12:25
    ('Observe', 'Watch'), # RV PSA 37:37
    ('occupation', 'works'), # GEN 47:3
    ('occupied', 'taken'), # JER 40:10
    ('occupied', 'busy'), # RV ECC 3:10
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
    ('offered','giving'), # Mrk 14:57
    ('offered', 'volunteered'), # NEH 11:2
    ('offering', 'present'), # LEV 4:23
    ('offerings', 'contribution'), # MAL 3:8
    ('offerings', 'contributions'), # NUM 18:8
    ('offerings', 'wave-offering'), # NUM 18:18
    ('officer', 'official'), # JER 51:59
    ('officers', 'officials'), # DEU 20:5
    ('officers', 'nobles'), # RV NAH 2:5 / LV NAH 2:6
    ('official', 'officer'), # KI2 25:19
    ('officials', 'officers'), # ACT 16:35
    ('officials', 'overseers'), # CH2 8:10
    ('officials', 'princes'), # ZEP 1:8
    ('offspring', 'descendants'), # JOB 27:14
    ('older', 'aged'), # JOB 32:6
    ('older', 'old'), # EZE 16:46
    ('older', 'elder'), # RV LUK 15:25
    ('oldest', 'old'), # SA1 17:28
    ('oldest', 'firstborn', 'aligned'), # CH1 3:15
    ('olive', 'olive[s]'), # EXO 27:20
    ('olives', 'olive[s]'), # MIC 6:15
    ('on','in/on/at/with'),
    ('one', 'someone', 'aligned'),
    ('only','except'), # Mrk 13:32
    ('onward', 'onwards'), # EZE 43:27
    ('opened','divided'), # Mrk 15:46
    ('opening','door'), # Mrk 15:46
    ('opening', 'mouth'), # RV DAN 6:17 / LV DAN 6:18
    ('opportunity', 'opportune'), # MRK 6:21
    ('oppose', 'fight'), # RV JER 1:19
    ('opposes', 'oppositions'), # TI1 6:20
    ('opposite', 'reversed'), # RV EST 9:1
    ('oppress', 'afflict'), # PSA 89:22
    ('oppress', 'oppression'), # PSA 10:7
    ('oppress', 'oppressors'), # ISA 3:12
    ('oppressed', 'afflicted'), # DEU 26:6
    ('oppressed', 'crushed'), # CH2 16:10
    ('oppressed', 'oppression'), # EZE 22:7
    ('oppressed', 'oppressions'), # PRO 29:13
    ('oppressed', 'persecuted'), # RV DEU 30:7
    ('oppressive', 'oppressor'), # JER 46:16
    ('oppressors', 'afflicted'), # ZEP 3:19
    ('oppressors', 'oppress'), # PSA 119:121
    ('oppressors', 'oppresses'), # ZEP 3:1
    ('orchards', 'grove'), # EXO 23:11
    ('orchards', 'groves'), # SA1 8:14
    ('order', 'arrange'), # JOB 33:5
    ('order', 'said'), # DAN 5:29
    ('ordered','commanded'),
    ('ordered', 'decree'), # EZR 4:19
    ('ordered', 'said'), # NEH 13:9
    ('ordered', 'sayingms'), # DAN 3:19
    ('orderly', 'order'), # CO1 14:40
    ('ordination', 'installation', 'aligned'), # LEV 8:22
    ('ornaments', 'ornament[s]'), # EZE 7:20
    ('orphan', 'fatherless'), # DEU 27:19
    ('orphans', 'fatherless'), # MAL 3:5
    ('other','across'),
    ('other','neighbouring', 'both'),
    ('out', 'forth', 'aligned'),
    ('outer', 'outermost'), # EXO 26:4
    ('out-house', 'outhouses'), # KI2 10:27
    ('outnumber', 'excess'), # NUM 3:46
    ('outside','out'), # Mrk 15:20
    ('outside', 'external'), # NEH 11:16
    ('outsider', 'stranger'), # NUM 18:4
    ('outsiders', 'outside'), # CO1 5:12
    ('outskirts', 'edge'), # SA1 14:2
    ('outskirts', 'outskirt[s]'), # NUM 22:41
    ('outstanding', 'great'), # RV CH2 1:8
    ('over','elapsed'), # Mrk 16:1
    ('overcame', 'defeated'), # NUM 21:35
    ('overcome', 'defeated'), # KI2 14:12
    ('overflow', 'flood'), # RV PSA 32:6
    ('overpower', 'overcoming'), # RV REV 11:7
    ('overpowers', 'overcome'), # LUK 11:22
    ('overseer', 'overseeing'), # TI1 3:1
    ('overthrows', 'subverted'), # PRO 22:12
    ('overthrows', 'subverts'), # JOB 12:19
    ('overwhelm', 'devastate'), # JOB 12:15
    ('overwhelm', 'overtake'), # ISA 35:10
    ('overwhelmed', 'covered'), # RV PSA 44:15 / LV PSA 44:16
    ('overwhelming', 'flood'), # PRO 27:4
    ('overwhelms', 'overpowers'), # JOB 15:24
    ('own','possession'),
    ('owned','having'),
    ('owned', 'possessing'), # RV ACT 4:37
    ('owner', 'master'), # RV EXO 22:8 / LV EXO 22:7
    ('ownership', 'possession'), # DEU 28:21
    ('owns', 'possessing'), # RV LUK 12:44
    ('pagan', 'pagans'), # ACT 4:27
    ('paid', 'gave'), # CH1 21:25
    ('paid', 'give'), # DEU 22:19
    ('paid', 'given'), # RV EZR 6:4
    ('pain', 'anguish'), # JOB 6:10
    ('pain', 'labour-pains'), # JER 49:24
    ('pain', 'trouble'), # JDG 11:35
    ('Pains', 'labour-pains'), # HOS 13:13
    ('pains', 'pangs'), # SA1 4:19
    ('pairs', 'twins'), # RV SNG 4:2
    ('palace', 'house'), # CH2 28:7
    ('palace', 'household'), # KI1 18:3
    ('palaces', 'houses'), # MAT 11:8
    ('panic', 'dread'), # PRO 1:27
    ('panic', 'terrify'), # SA2 17:2
    ('Panic', 'Terror'), # RV LAM 3:47
    ('pans', 'censers'), # RV NUM 16:38 / LV NUM 17:3
    ('parables', 'allegory'), # RV JHN 16:29
    ('parallel', 'corresponding'), # EZE 45:7
    ('paralysed','paralytic'),
    ('paralysed', 'numb'), # HAB 1:4
    ('parents','mother'),
    ('parents','father'),
    ('part', 'member'), # CO1 12:14
    ('part', 'members'), # CO1 12:18
    ('part', 'portion'), # ACT 8:21
    ('part', 'share'), # NEH 2:20
    ('parts', 'members'), # CO1 12:22
    ('parts', 'portions'), # JOS 18:6
    ('pass', 'go'), # NUM 36:9
    ('pass', 'goes'), # KI1 15:17
    ('pass', 'handing'), # LUK 11:12
    ('passed', 'given'), # JHN 17:14
    ('passed', 'went'), # REV 9:12
    ('passing', 'passage'), # CO1 16:7
    ('passing', 'went'), # EZE 26:18
    ('passion', 'rage'), # REV 14:8
    ('Passover','feast'), # Mrk 15:6
    ('pass-over', 'passover'), # CH2 35:6
    ('pass-over', 'passovers'), # CH2 35:7
    ('past', 'beyond', 'both'), # HEB 11:11
    ('pastureland', 'pasture'), # CH1 5:16
    ('pasturelands', 'pasture'), # CH1 13:2
    ('path','way'),
    ('path','road'),
    ('Path', 'way'), # ACT 22:4
    ('path', 'direction'), # PRO 7:8
    ('path', 'road/course'), # JOB 3:23
    ('path', 'track'), # PSA 140:5
    ('paths', 'tracks'), # PRO 2:18
    ('paths', 'way'), # JER 3:21
    ('paths', 'ways'), # HOS 9:8
    ('patiently', 'patience'), # PE1 3:20
    ('patiently', 'patient'), # LUK 18:7
    ('paul', 'paulos', 'aligned'),
    ('pay', 'give'), # EZE 16:41
    ('pay', 'giving'), # LUK 23:2
    ('payment', 'tribute'), # EZE 27:15
    ('peace', 'peaceable'), # HEB 12:11
    ('peace', 'security'), # DAN 11:24
    ('peace', 'undisturbed'), # ZEC 1:11
    ('peace', 'welfare'), # CH1 18:10
    ('peace', 'well-being'), # MAL 2:5
    ('peaceable', 'peaceful'), # SA2 20:19
    ('peaceably', 'peace'), # EPH 2:15
    ('peaceful', 'peace'), # GEN 34:21
    ('peacefully', 'peace'), # EXO 18:23
    ('peace-loving', 'peaceable'), # TI1 3:3
    ('peacemakers', 'peacemaking'), # MAT 5:9
    ('peak', 'top'), # EZE 43:12
    ('peeled', 'stripped'), # GEN 30:38
    ('pen', 'stylus'), # JOB 19:24
    ('pens', 'folds'), # PSA 50:9
    ('people','humans'),
    ('people','multitude'),
    ('people','ones'),
    ('People', 'men'), # JOB 24:12
    ('people', 'community'), # PSA 68:10
    ('people', 'humankind'), # JOB 28:4
    ('people', 'inhabitants'), # CH2 35:18
    ('people', 'kinspeoples'), # GEN 17:14
    ('people', 'man'), # CH1 26:8
    ('people', 'men'), # DEU 26:5
    ('people', 'souls'), # PE2 2:14
    ('people', 'congregation'), # RV NUM 16:46 / LV NUM 17:11
    ('people', 'flesh'), # RV PSA 56:4 / LV PSA 56:5
    ('people', 'servants'), # RV PSA 69:36 / LV PSA 69:37
    ('peoples', 'clans'), # NAH 3:4
    ('peoples', 'flesh'), # RV JOL 2:28 / LV JOL 3:1
    ('perceive', 'observes'), # JOB 33:14
    ('percent','add'),
    ('perfect', 'complete'), # JOB 37:16
    ('perfect', 'perfection'), # COL 3:14
    ('perfect', 'blameless'), # RV PSA 19:13 / LV PSA 19:14
    ('perfection', 'perfect'), # CO1 13:10
    ('perfection', 'perfected'), # PHP 3:12
    ('perform', 'act'), # DEU 25:5
    ('perform', 'done'), # PSA 31:19
    ('performed', 'did'), # EZE 16:50
    ('perfume', 'nard'), # SNG 1:12
    ('perfume', 'ointment'), # ECC 7:1
    ('perfumes', 'ointment'), # CH2 16:14
    ('perfumes', 'perfumers'), # SA1 8:13
    ('period','time'),
    ('periods', 'times'), # RV DAN 4:16 / LV DAN 4:13
    ('perished', 'destroyed'), # RV PSA 83:10 / LV PSA 83:11
    ('perishing', 'passing'), # JOB 33:18
    ('permanent','perpetuity'),
    ('permanently', 'permanent'), # HEB 7:24
    ('permissible', 'permitting'), # MAT 12:12
    ('permission','requested'), # Mrk 15:43,45
    ('permission','granted'), # Mrk 15:43,45
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
    ('person', 'soul'), # RV ROM 2:9
    ('person', 'humankind'), # RV ECC 5:19 / LV ECC 5:18
    ('personality', 'person'), # ROM 6:6
    ('persuasive', 'persuade'), # COL 2:4
    ('persuasive', 'persuasiveness'), # PRO 16:21
    ('Perverse', 'perversities'), # PRO 16:28
    ('perverse', 'perversities'), # DEU 32:20
    ('perversely', 'perverse'), # PRO 2:12
    ('perversions', 'perverseness'), # EZE 9:9
    ('perversity', 'perverseness'), # PRO 15:4
    ('pestered', 'urged'), # JDG 16:16
    ('pet', 'bird'), # RV JOB 41:5 / LV JOB 40:29
    ('peter', 'petros', 'aligned'),
    ('petition', 'prayer'), # JER 7:16
    ('Petor', 'Pethor'), # RV DEU 23:4 / LV DEU 23:5
    ('pharisees', 'pharisaios', 'aligned'),
    ('pharisees', 'pharisaiousin', 'aligned'),
    ('philip', 'filippos', 'aligned'),
    ('physically', 'flesh'), # ROM 9:5
    ('pick', 'take'), # JHN 5:8
    ('pick', 'taken'), # LUK 5:24
    ('pick', 'taking'), # MAT 10:38
    ('pick', 'plucked'), # RV PSA 80:12 / LV PSA 80:13
    ('pick', 'pluck'), # RV JOB 30:4
    ('picked','taken'), # Mrk 14:23
    ('picked', 'took'), # KI2 2:13
    ('picking', 'taken'), # LUK 22:19
    ('picking', 'taking'), # LUK 19:21
    ('piece', 'part'), # LUK 24:42
    ('pilate', 'pilatos', 'aligned'),
    ('pile', 'heap'), # RUT 3:7
    ('pile', 'heaped'), # HAB 1:10
    ('pile', 'place'), # RV LEV 6:10 / LV LEV 6:3
    ('piled', 'heap'), # JOS 7:26
    ('piles', 'heaps'), # CH2 31:8
    ('pillars', 'pillar[s]'), # EXO 24:4
    ('pilots', 'sailors'), # EZE 27:8
    ('pitchers', 'jugs'), # EXO 25:29
    ('pitchfork', 'fork'), # JER 15:7
    ('pitfall', 'pit'), # LAM 3:47
    ('pitied', 'compassion'), # EZE 20:17
    ('pitiless', 'ruthless'), # RV PSA 54:3 / LV PSA 54:5
    ('pity', 'compassion'), # JOL 2:17
    ('pity', 'compassions'), # RV PSA 106:46
    ('Place', 'set'), # SA2 11:15
    ('place', 'lay'), # NUM 8:12
    ('place', 'put'), # DEU 31:26
    ('place', 'putting'), # MAT 12:18
    ('place', 'site'), # GEN 23:4
    ('place', 'set'), # RV PSA 89:25 / LV PSA 89:26
    ('place', 'Set'), # RV PSA 141:3
    ('place', 'property'), # RV JHN 4:5
    ('place', 'earth/land'), # RV CH2 14:6 / LV CH2 14:5
    ('place', 'habitation'), # RV JER 9:11 / LV JER 9:10
    ('placed','laid'), # Mat 3:10
    ('placed','lying'), # Mat 3:10
    ('placed', 'laying'), # ACT 8:17
    ('placed', 'put'), # CH2 17:2
    ('placed', 'set'), # DEU 26:10
    ('placed', 'setting'), # PRO 25:7
    ('places', 'put'), # ACT 9:12
    ('places', 'residence'), # HAB 3:11
    ('places', 'puts'), # RV JOB 19:8
    ('placing','laying'), # Mat 3:10
    ('placing', 'laid'), # MRK 6:5
    ('Plague', 'pestilence'), # EZE 5:17
    ('plain','ˊₐrāⱱāh'),
    ('plain', 'level'), # ZEC 4:7
    ('plain', 'valley'), # CH2 35:22
    ('plainly', 'plainness'), # JHN 11:14
    ('plains', 'valley'), # JDG 1:19
    ('planet','earth'), # Mrk 13:31
    ('planning', 'scheme'), # ECC 9:10
    ('plans', 'schemes'), # PSA 5:10
    ('plant', 'growth'), # EZE 16:7
    ('plant', 'plant[s]'), # GEN 1:30
    ('plant', 'set'), # ISA 41:19
    ('plant', 'shoot'), # ISA 53:2
    ('planted', 'sown'), # MAT 13:24 (reviewed 2026-10-13)
    ('planter', 'planting'), # CO1 3:7
    ('plants', 'plant[s]'), # GEN 9:3
    ('plants', 'plantation'), # ISA 5:7
    ('plants', 'vegetation'), # EXO 10:12
    ('plaster', 'lime'), # DEU 27:2
    ('plastered', 'sealed'), # EXO 2:3
    ('plateau', 'plain'), # JOS 13:9
    ('plates', 'dishes'), # EXO 25:29
    ('plates', 'scales'), # KI1 22:34
    ('platform','lid'),
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
    ('pleased', 'delight'), # RV PSA 41:11 / LV PSA 41:12
    ('pleased', 'delights'), # RV NUM 14:8
    ('pleases', 'good'), # EZR 5:17
    ('pleases', 'pleasure'), # ROM 8:8
    ('pleasing', 'acceptable'),
    ('pleasing','soothing'),
    ('pleasing', 'delight'), # ECC 12:10
    ('pleasing', 'pleasure'), # CO1 7:32
    ('pleasure', 'delights'), # PSA 37:23
    ('pleasure', 'pleasant'), # PRO 2:10
    ('pleasure', 'favour'), # RV PSA 51:18 / LV PSA 51:20
    ('pleasures', 'delights'), # ECC 2:8
    ('plentiful', 'plenty'), # GEN 41:29
    ('Plenty','Many'),
    ('plenty', 'plentiful'), # PHP 4:18
    ('plot', 'conspiracy'), # KI2 15:15
    ('plot', 'planning'), # PSA 37:12
    ('plot', 'scheme'), # RV PSA 21:11 / LV PSA 21:12
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
    ('plus','and'),
    ('pointless', 'futilities'), # RV ECC 5:7 / LV ECC 5:6
    ('poison', 'venom'), # RV PSA 140:3 / LV PSA 140:4
    ('polluted', 'pollutions'), # ACT 15:20
    ('pondering','considered'), # Mat 1:20
    ('poor','humble'),
    ('poor', 'needy'), # RV PSA 69:33 / LV PSA 69:34
    ('poorest', 'poor'), # KI2 25:12
    ('popular', 'acceptable'), # EST 10:3
    ('population','multitude'),
    ('porters', 'burden-bearers'), # CH2 34:13
    ('porters', 'burden-bearer[s]'), # RV CH2 2:2 / LV CH2 2:1
    ('portion', 'share'), # GEN 31:14
    ('position', 'place'), # ECC 10:4
    ('position', 'office'), # RV GEN 41:13
    ('positions', 'deployed'), # JDG 20:30
    ('possess', 'possession'), # DEU 2:12
    ('possession', 'possessed'), # MAT 15:22
    ('possessions', 'acquisition'), # PSA 105:21
    ('possessions', 'possessing'), # LUK 12:15
    ('possessions', 'possession[s]'), # GEN 14:11
    ('possessions', 'property'), # CH2 21:14
    ('post','stake'), # Mrk 15:13
    ('potter', 'formed'), # RV ISA 64:8 / LV ISA 64:7
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
    ('praise', 'boast'), # RV PSA 34:2 / LV PSA 34:3
    ('praise', 'thanksgiving'), # RV PSA 42:4 / LV PSA 42:5
    ('praised','glorifying'),
    ('praised', 'glorified'), # ACT 11:18
    ('praiseworthy', 'praise'), # CH1 16:35
    ('praising', 'glorifying'), # ACT 4:21
    ('prayer', 'entreated'), # GEN 25:21
    ('prayer', 'petition'), # TI1 4:5
    ('prayer', 'supplications'), # DAN 9:23
    ('prayers', 'entreat'), # ZEC 7:2
    ('prayers', 'entreated'), # CH1 5:20
    ('prayers', 'petition'), # PHP 1:19
    ('preaching','proclaiming'),
    ('prearranged','given'), # Mrk 14:44
    ('precious', 'desire'), # DAN 11:8
    ('precious', 'desires'), # LAM 2:4
    ('precious', 'preciously'), # PE1 1:7
    ('precious', 'preciousness'), # HOS 13:15
    ('prefects', 'officials'), # RV NEH 4:14 / LV NEH 4:8
    ('pregnant','womb'), # Mat 1:18
    ('pregnant', 'conceived'), # GEN 19:36
    ('preparation', 'prepared'), # CH1 29:19
    ('prepare', 'appoint'), # EZE 35:6
    ('prepare', 'arrange'), # ISA 65:11
    ('prepare', 'make'), # MAL 3:1
    ('Prepare', 'consecrate'), # RV JOL 3:9 / LV JOL 4:9
    ('prepared', 'arranged'), # CH2 35:10
    ('prepared', 'made'), # CH2 35:1
    ('prepared', 'preparation'), # JHN 19:14
    ('prepared', 'ready'), # LUK 22:33
    ('prescribed', 'appointed'), # CH2 30:22
    ('presence', 'front'), # EST 2:23
    ('present', 'give'), # PRO 4:9
    ('present', 'presence'), # EXO 39:36
    ('present', 'station'), # EXO 34:2
    ('presented','offered'), # Mat 2:11
    ('presented', 'bring'), # NUM 5:9
    ('presented', 'brought'), # DAN 7:13
    ('presenter', 'present'), # LEV 1:13
    ('presenter', 'presented'), # LEV 7:18
    ('presenting', 'bringing'), # NUM 16:35
    ('presents', 'gift'), # KI2 8:9
    ('preserved', 'kept'), # RV HOS 12:13 / LV HOS 12:14
    ('preserves', 'keeps'), # PRO 19:8
    ('pressed','putting'), # Mrk 15:17
    ('pressure', 'press'), # DEU 15:3
    ('prevent', 'forbidding'), # MRK 10:14
    ('prevented', 'restrained'), # GEN 16:2
    ('previous', 'former'), # DAN 7:24
    ('price', 'money'), # CH1 21:22
    ('price', 'silver'), # GEN 23:9
    ('pride', 'exaltation'), # ISA 4:2
    ('pride', 'haughtiness'), # PSA 10:4
    ('priest','priest/officer'),
    ('priest', 'priesthood'), # HEB 7:24
    ('priestly', 'priesthoods'), # SA1 2:36
    ('priestly', 'priests'), # CH2 31:17
    ('priests', 'priesthood'), # EXO 29:9
    ('priests', 'priestly'), # LUK 1:9
    ('priests', 'hiereus', 'aligned'),
    ('priests', 'hiereusin', 'aligned'),
    ('princes', 'rulers'), # RV PSA 76:12 / LV PSA 76:13
    ('princess', 'daughter'), # RV PSA 45:12 / LV PSA 45:13
    ('principles', 'precepts', 'aligned'), # PSA 119:93
    ('priscilla', 'priskilla', 'aligned'),
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
    ('prochorus', 'prochoros', 'aligned'),
    ('proclaim', 'proclaimer'), # TI1 2:7
    ('proclaim', 'proclamation'), # TIT 1:3
    ('proclaimed', 'proclamation'), # TI2 4:17
    ('proclaimed', 'recounted'), # RV PSA 88:11 / LV PSA 88:12
    ('proclamation','announcement'),
    ('proclamation','declaration'),
    ('proclamation','notice'),
    ('proclamations','declarations'),
    ('prod', 'goads'), # ECC 12:11
    ('produce','fruit'),
    ('produce', 'fruits'), # LAM 4:9
    ('produce', 'products'), # GEN 43:11
    ('produce', 'raise'), # GEN 38:8
    ('produce', 'vigor/produce'), # GEN 4:12
    ('producer', 'producing'), # ROM 7:13
    ('produces', 'vigor/produce'), # JOB 31:39
    ('product', 'produce'), # PRO 18:20
    ('profit', 'gain'), # RV EXO 18:21
    ('profited', 'wealth'), # PSA 44:12
    ('prominent', 'prominence'), # ACT 25:23
    ('promise', 'oath'), # CH1 16:16
    ('promised','sworn'),
    ('promised', 'foretold'), # GAL 3:8
    ('promised', 'words/messages'), # CH1 25:5
    ('promised', 'fulfilled', 'aligned'), # ACT 2:30: promised / swore
    ('promised', 'swore', 'aligned'), # ACT 2:30: promised / swore
    ('promises', 'oath'), # SA2 21:7
    ('promises', 'oaths'), # MRK 6:26
    ('promises', 'vows'), # RV PSA 61:5 / LV PSA 61:6
    ('promoted', 'exalted'), # EST 5:11
    ('promoted', 'exalting'), # KI1 1:5
    ('pronounce','utterance'),
    ('pronounced', 'spoke'), # JER 39:5
    ('pronounced', 'spoken'), # JER 26:19
    ('property', 'money'), # EXO 21:21
    ('property', 'possession'), # EZE 46:16
    ('prophecies', 'prophesies'), # CO1 13:8
    ('prophecies', 'divination'), # RV EZE 12:24
    ('prophecy', 'prophesying'), # CO1 11:4
    ('prophecy', 'prophet'), # DAN 9:24
    ('prophesied', 'prophecy'), # TI1 4:14
    ('prophesy', 'prophecy'), # CO1 13:2
    ('prophet', 'prophesied'), # MAT 15:7
    ('prophet', 'prophesying'), # JER 29:26
    ('prophet', 'seer'), # CH2 16:10
    ('prophet', 'prophesier'), # RV MIC 2:11
    ('prophetic', 'prophecy'), # REV 22:19
    ('prophets', 'prophetic'), # PE2 1:19
    ('prophets', 'prophetes', 'aligned'),
    ('prophets', 'prophetesin', 'aligned'),
    ('prosper', 'succeed'), # DAN 8:12
    ('prosper', 'successful'), # DAN 8:25
    ('prospered', 'successful'), # CH1 29:23
    ('prospering', 'flourishing'), # RV DAN 4:4 / LV DAN 4:1
    ('prosperity', 'good'), # JOB 21:13
    ('prosperity', 'peace'), # JOB 15:21
    ('prostitutes', 'prostitute[s]'), # KI1 14:24
    ('prostitution', 'prostitute'), # EZE 16:41
    ('protect','defend'),
    ('protect', 'preserves'), # PRO 14:3
    ('protect', 'protection'), # DAN 11:1
    ('protect', 'shade'), # NUM 14:9
    ('protection', 'cover'), # PSA 5:11
    ('protection', 'sheltering'), # REV 7:15
    ('protection', 'refuge'), # RV PSA 46:1 / LV PSA 46:2
    ('protector', 'guard/protect'), # HOS 4:10
    ('protector', 'judge'), # RV PSA 68:5 / LV PSA 68:6
    ('proud', 'haughty'), # ECC 7:8
    ('proud', 'pride'), # JOB 38:11
    ('proud', 'prides'), # EZE 16:56
    ('proved', 'demonstrated'), # CO2 7:11
    ('proved', 'provenness'), # CO2 8:2
    ('proven', 'provenness'), # PHP 2:22
    ('proverbs', 'byword'), # JER 24:9
    ('provide', 'supply'), # RV SA2 19:33 / LV SA2 19:34
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
    ('pull', 'dragged'), # RV DEU 21:3
    ('pulled', 'drew'), # GEN 37:28
    ('pulled', 'torn'), # JOB 18:14
    ('pulling', 'drags'), # RV PSA 10:9
    ('punish', 'punishment'), # JER 48:44
    ('punish', 'visit'), # RV JER 9:9 / LV JER 9:8
    ('punished', 'punishment'), # JN1 4:18
    ('punished', 'retribution'), # PSA 91:8
    ('punishing', 'fine'), # PRO 21:11
    ('punishment', 'reprove'), # HAB 1:12
    ('purchased', 'bought'), # REV 14:4
    ('pure','holy'),
    ('pure', 'holiness'), # EZE 39:25
    ('pure', 'unadulterated'), # PE1 2:2
    ('purest', 'pure'), # RV PSA 21:3 / LV PSA 21:4
    ('purge', 'remove'), # DEU 24:7
    ('purification', 'cleansing'), # EZE 43:23
    ('purification', 'purified'), # ACT 21:24
    ('purified', 'cleansed'), # CH2 29:18
    ('purified', 'purification'), # EZE 44:26
    ('purified', 'sanctified'), # ACT 20:32
    ('purify', 'cleanse'), # EZE 43:20
    ('purify', 'sanctify'), # NUM 11:18
    ('Purify', 'Sanctify'), # RV JHN 17:17
    ('purity','holiness'),
    ('purity', 'holy'), # EZE 38:23
    ('pursuer', 'pursued'), # LAM 1:6
    ('pursuers', 'pursue'), # JER 17:18
    ('pursuers', 'pursuer[s]'), # JOS 8:20
    ('pursuers', 'harass'), # RV PSA 142:6 / LV PSA 142:7
    ('pursuit', 'pursuing'), # JDG 8:4
    ('push', 'drive'), # ISA 22:19
    ('pushed', 'drive'), # JER 46:15
    ('put', 'assigned'), # EXO 24:6
    ('put', 'laid'), # ACT 4:37
    ('put', 'laying'), # MAT 23:4
    ('put', 'set'), # CH1 16:1
    ('put', 'lay'), # RV EXO 29:10
    ('put', 'placed'), # RV EXO 33:4
    ('put', 'placing'), # RV JDG 6:37
    ('puts', 'place'), # RV ISA 30:32
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
    ('queen', 'queen-consort'), # RV PSA 45:9 / LV PSA 45:10
    ('quench', 'extinguish'), # SNG 8:7
    ('quench', 'extinguishes'), # RV AMO 5:6
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
    ('quiet','desolate'),
    ('quiet','silenced'),
    ('quiet','deserted'),
    ('quiet', 'peace'), # KI2 11:20
    ('quiet', 'quietness'), # ACT 22:2
    ('quiet', 'silent'), # JDG 16:2
    ('quiet', 'hush'), # RV JDG 3:19
    ('quieten', 'silenced'), # NUM 13:30
    ('quietened', 'quiet'), # PSA 107:30
    ('quietly','secretly'), # Mat 1:19
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
    ('raise', 'lifted'), # RV EZE 31:14
    ('raised', 'lifted'), # EZE 20:6
    ('raised', 'rise'), # RV ACT 10:41
    ('raisin', 'raisin-cake'), # CH1 16:3
    ('raisin', 'raisin-cakes'), # SNG 2:5
    ('raising', 'rise'), # ISA 14:9
    ('raisins', 'raisin-cake'), # SA2 6:19
    ('ran', 'fled'), # DAN 10:7
    ('ran', 'went'), # KI1 18:35
    ('range','various'),
    ('rape', 'violate'), # EST 7:8
    ('rattling', 'shaking'), # RV JOB 41:29 / LV JOB 41:21
    ('ravaged', 'desolate'), # ISA 49:17
    ('reach', 'approach'), # SA2 5:8
    ('reach', 'attain'), # EPH 4:13
    ('reach', 'near'), # JDG 19:13
    ('reached', 'grasped'), # ROM 9:30
    ('reached', 'stretched'), # PSA 18:16
    ('reached', 'touches'), # JOS 16:7
    ('reached', 'come'), # RV PSA 69:1 / LV PSA 69:2
    ('reaches', 'stretch'), # RV DEU 25:11
    ('readers','reading'), # Mrk 13:14
    ('ready','gird'),
    ('ready', 'prepare'), # EZE 7:14
    ('ready', 'prepared'), # PSA 7:12
    ('ready', 'preparing'), # RV MAT 11:10
    ('ready', 'Prepare'), # RV LUK 17:8
    ('realise', 'knew', 'aligned'), # JHN 8:27
    ('realise', 'know'), # RV DEU 29:6 / LV DEU 29:5
    ('realise', 'knowing'), # RV ECC 5:1 / LV ECC 4:17
    ('realised','saw'), # Mrk 16:3, Mat 2:16
    ('realised','saying'), # Mrk 16:3, Mat 2:16
    ('realised','seen'), # Mrk 16:3, Mat 2:16
    ('realised', 'understood'), # MAT 17:13
    ('realised', 'knew', 'aligned'), # CH1 14:2
    ('reason', 'cause'), # CO2 6:3
    ('reason', 'caused'), # EXO 9:16
    ('reason', 'understanding'), # RV DAN 4:34 / LV DAN 4:31
    ('reasons', 'cause'), # RV TIT 1:13
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
    ('rebellion', 'insurrection'), # RV LUK 23:25
    ('rebellious', 'rebelled'), # KI1 13:21
    ('rebellious', 'rebellion'), # EZE 2:5
    ('rebellious', 'rebelliousness'), # SA1 20:30
    ('rebellious', 'transgression'), # PSA 107:17
    ('rebels', 'rebellious'), # HOS 9:15
    ('rebuild','building'), # Mrk 15:29
    ('rebuild', 'build'), # EZR 5:2
    ('rebuild', 'built'), # PSA 102:16
    ('rebuilt', 'built'), # NUM 32:34
    ('rebuke', 'reproach'), # RV PSA 69:9 / LV PSA 69:10
    ('rebukes', 'reproaches'), # RV PSA 69:9 / LV PSA 69:10
    ('recalled', 'remembered'), # RV ISA 63:11
    ('recede', 'decreasing'), # GEN 8:5
    ('receive', 'take'), # PSA 49:15
    ('receive', 'took'), # REV 20:4
    ('receive', 'obtain'), # RV TI2 2:10
    ('received', 'obtained'), # HEB 6:15
    ('received', 'taking'), # ROM 1:27
    ('received', 'accepted'), # RV CH1 12:18 / LV CH1 12:19
    ('receives', 'obtains'), # RV PRO 12:2
    ('reckless', 'recklessness'), # JER 23:32
    ('reckon', 'counting'), # CO2 11:5
    ('reckoned', 'counted'), # HEB 11:19
    ('recognise', 'know'), # DEU 18:21
    ('recognise', 'known'), # ACT 13:27
    ('recognise', 'knew'), # RV MAT 17:12
    ('recognised', 'known'), # LUK 6:44
    ('recognises', 'knowing'), # NAH 1:7
    ('recognize', 'knew'), # PSA 81:5
    ('recommended', 'commend'), # RV ECC 8:15
    ('record', 'recorder'), # CH1 18:15
    ('record', 'write'), # REV 1:19
    ('record', 'book'), # RV EST 9:32
    ('recorded', 'written'), # EZR 8:34
    ('recorded', 'wrote'), # EST 9:20
    ('records', 'enrolment'), # CH1 4:33
    ('recover', 'live'), # ISA 38:21
    ('red', 'ruddy'), # SNG 5:10
    ('red', 'crimson'), # RV CH2 2:7 / LV CH2 2:6
    ('red', 'reddened'), # RV JOB 16:16
    ('red', 'redness'), # RV ISA 63:2
    ('reddish-white', 'reddish'), # LEV 13:19
    ('redeemer', 'vindicator'), # JOB 19:25
    ('reduce', 'cut'), # KI2 10:32
    ('reed','reed[s]'),
    ('reeds','reed[s]'),
    ('reeds', 'rush[es]'), # EXO 2:5
    ('reeds', 'bulrush'), # RV ISA 9:14 / LV ISA 9:13
    ('reestablish', 'restore'), # RV SA2 8:3
    ('reestablished', 'restored'), # KI2 14:22
    ('reflect', 'consider'), # PRO 20:25
    ('reformed', 'reformation'), # HEB 9:10
    ('refreshing', 'refreshment'), # ACT 3:20
    ('refuse', 'reject'), # ISA 7:15
    ('refused','forbidding'), # Mat 3:14
    ('refused', 'rejected'), # ISA 8:6
    ('regard', 'consider'), # JOB 19:15
    ('regarded', 'considered'), # LAM 4:2
    ('regenerated', 'regeneration'), # TIT 3:5
    ('region','land'),
    ('regions','land'),
    ('regions', 'parts'), # RV ACT 19:1
    ('regions', 'territories'), # RV JOL 3:4 / LV JOL 4:4
    ('regret', 'regretful'), # MAT 21:32
    ('regretted', 'regretful'), # MAT 21:29
    ('regular','scribes', 'both'),
    ('regular', 'continuity'), # NUM 4:16
    ('regular', 'perpetual'), # DAN 8:11
    ('regulation', 'ordinance'), # LEV 5:10
    ('regulations', 'decrees'), # PSA 119:8
    ('regulations', 'ordinance'), # RV CH1 23:31
    ('reign', 'throne'), # RV PSA 45:6 / LV PSA 45:7
    ('reject', 'abandon'), # PSA 119:53
    ('reject', 'abandoned'), # PSA 119:87
    ('reject', 'spurns'), # PRO 15:5
    ('rejected', 'abandoned'), # CH2 10:8
    ('rejected', 'scorned'), # ACT 4:11
    ('rejected', 'spurned'), # DEU 32:19
    ('rejects', 'neglects'), # PRO 10:17
    ('rejoice', 'exult'), # PRO 2:14
    ('rejoicing', 'joy'), # RV NEH 12:27
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
    ('release','send'), # Mrk 15:9
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
    ('religious', 'scribes'),
    ('religious', 'religion'), # ACT 26:5
    ('rely', 'trust'), # ISA 36:15
    ('relying','trust'),
    ('remain', 'dwell'), # SA1 1:22
    ('remain', 'leave'), # ISA 65:15
    ('remainder', 'remained'), # KI2 10:17
    ('remainder', 'remains'), # CH2 31:10
    ('remainder', 'rest'), # DAN 7:7
    ('remained', 'continuing'), # LUK 1:22
    ('remained', 'delayed'), # RV GEN 32:4 / LV GEN 32:5
    ('remaining', 'left'), # NUM 21:35
    ('remaining', 'remainder'), # LEV 14:17
    ('remaining', 'rest'), # RV CH1 19:11
    ('remains', 'keep'), # RV NUM 30:4 / LV NUM 30:5
    ('remember', 'remembrance'), # LUK 22:19
    ('remembered','reminded'),
    ('remembered', 'remembrance'), # DEU 25:19
    ('remembering', 'remembrance'), # TH1 1:2
    ('remembrance', 'remember'), # PSA 77:6
    ('reminder', 'memorial'), # EXO 13:9
    ('reminder', 'sign'), # RV NUM 16:38 / LV NUM 17:3
    ('reminder', 'remembrance'), # PE2 1:13 (reviewed 2026-10-13)
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
    ('renders', 'gives'), # RV PSA 82:1
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
    ('replace', 'substitute'), # RV ISA 9:10 / LV ISA 9:9
    ('replied','answering'), # Mrk 15:2
    ('replied','said'),
    ('replied', 'answered'),
    ('replied', 'say'), # KI1 5:2
    ('replied', 'saying'), # ACT 7:2
    ('report', 'tell'), # ACT 23:18
    ('reported', 'described'), # LUK 9:10
    ('reported', 'told'), # ISA 7:2
    ('represents', 'representation'), # HEB 1:3
    ('represents', 'representative'), # PE1 3:21
    ('reputation','name'),
    ('reputation', 'report'), # PRO 25:10
    ('request','excusing'), # Mrk 15:6
    ('request','seek'), # Mrk 15:6
    ('request', 'asked'), # KI1 3:13
    ('request', 'petition'), # JOB 6:8
    ('request', 'asking'), # RV LUK 16:27
    ('requested','prayed'), # Mrk 15:6
    ('requested', 'asked'), # DAN 2:16
    ('requested', 'sought'), # CH1 15:13
    ('requesting', 'asking'), # SA1 8:10
    ('requesting', 'seek'), # CH1 22:19
    ('requests', 'seek'), # DAN 9:3
    ('requirements', 'charge'), # MAL 3:14
    ('rescue','deliver'),
    ('Rescue', 'deliver'), # ISA 44:17
    ('Rescue', 'save'), # PSA 31:16
    ('rescue', 'deliverance'), # ISA 59:11
    ('rescue', 'delivered'), # JDG 12:2
    ('rescue', 'delivers'), # PRO 11:4
    ('rescue', 'salvation'), # CH2 6:41
    ('rescue', 'save'), # CH2 20:9
    ('rescue', 'saved'), # ISA 63:9
    ('rescue', 'delivering'), # RV DAN 8:7
    ('Rescue', 'Deliver'), # RV PRO 24:11
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
    ('rescuing', 'delivering'), # RV JDG 6:36
    ('reserve', 'store'), # GEN 41:36
    ('residence', 'tabernacle', 'aligned'), # EXO 25:9
    ('residence', 'dwelling'), # RV JER 9:6 / LV JER 9:5
    ('residents', 'inhabitants', 'aligned'), # ISA 10:31
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
    ('respond', 'answering'), # RV MAT 25:44
    ('respond', 'answered'), # RV MAT 27:14
    ('responded','said'), # Mrk 14:30
    ('responded','saying'), # Mrk 14:30
    ('responded', 'answered'),
    ('responded', 'say'), # KI1 12:16
    ('responded', 'replying'), # RV DAN 6:16 / LV DAN 6:17
    ('responded', 'answering'), # RV LUK 14:3
    ('responded', 'Answered'), # RV JHN 18:8
    ('responding', 'answer'), # JOB 16:3
    ('response', 'answering'), # ACT 25:9
    ('responsibilities','authority'), # Mrk 13:34
    ('responsible', 'duty'), # NUM 3:25
    ('rest', 'lie'), # EZE 34:15
    ('rest', 'lying'), # PSA 139:3
    ('rest', 'relaxation'), # CO2 7:5
    ('rest', 'remainder'), # CH1 11:8
    ('rest', 'remained'), # JOS 17:6
    ('rest', 'stays'), # HAB 2:5
    ('rested', 'remained'), # EZR 8:32
    ('restoration', 'restoring'), # MRK 9:12
    ('restrain', 'holds'), # JOB 37:4
    ('restrained', 'bound'), # RV KI2 25:7
    ('restraint', 'restrained'), # ISA 14:6
    ('restricted', 'restrained'), # LUK 24:16
    ('result', 'outcome'), # PE1 1:9
    ('resurrected', 'resurrection'), # LUK 20:33
    ('retreat', 'turned'), # SA2 1:22
    ('retreat', 'turns'), # JOB 39:22
    ('retreated', 'turned'), # JDG 20:42
    ('return','coming'), # Mrk 13:35
    ('Return', 'go'), # GEN 44:25
    ('Return', 'restore'), # KI2 8:6
    ('return', 'came'), # KI1 10:22
    ('return', 'come'), # JDG 5:28
    ('return', 'repay'), # SA2 16:12
    ('return', 'restored'), # HEB 13:19
    ('return', 'turn'), # DEU 30:2
    ('return', 'went'), # JOS 22:6
    ('returned', 'came'), # EST 4:9
    ('returned', 'come'), # MRK 14:40
    ('returned', 'gone'), # ACT 25:9
    ('returned', 'turned'), # JOS 11:10
    ('returned', 'went'), # GEN 44:13
    ('Returning', 'come'), # MAT 26:43
    ('returning', 'went'), # SA1 6:16
    ('returns', 'come'), # CO1 11:26
    ('reveal', 'revelation'), # EPH 1:17
    ('reveal', 'show'), # RV ISA 30:30
    ('reveal', 'shows'), # RV JOB 11:11
    ('revealed', 'divulged'), # LUK 20:37
    ('revealed', 'revelation'), # PE1 1:13
    ('revealed', 'uncovered'), # RV EZE 16:57
    ('revealing', 'uncovered'), # RV EZE 21:24 / LV EZE 21:29
    ('reveals', 'revealer'), # DAN 2:29
    ('reveals', 'tells'), # AMO 4:13
    ('reveals', 'uncovering'), # RV PRO 20:19
    ('reveals', 'declares'), # RV PSA 19:2 / LV PSA 19:3
    ('revere', 'fear'), # CH2 19:9
    ('revere', 'fearing'), # PSA 31:19
    ('revered', 'feared'), # CH1 16:25
    ('reverence', 'fearing'), # RV ROM 11:20
    ('Revering', 'reverence'), # ROM 3:18
    ('reverse', 'revoke'), # ISA 43:13
    ('reverse', 'turn'), # NUM 23:20
    ('Revive', 'life'), # PSA 80:18
    ('revive', 'life'), # PSA 85:6
    ('revive', 'living'), # MAT 9:18
    ('revived', 'lived'), # JDG 15:19
    ('reward', 'wage[s]'), # RV PRO 10:16
    ('reward', 'repay'), # RV DEU 32:6
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
    ('right','fitting'), # Mrk 13:10, 12:32
    ('right','truth'), # Mrk 13:10, 12:32
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
    ('righteous', 'righteousness'), # ISA 28:17
    ('righteous', 'righteousnesses'), # MIC 6:5
    ('righteously', 'righteousness'), # HEB 11:33
    ('rightful', 'righteousness'), # JOB 8:6
    ('right-hand', 'right'), # REV 5:1
    ('right-handed', 'right'), # CH1 12:2
    ('rightly', 'righteousness'), # EZE 33:16
    ('rings', 'bands'), # EXO 38:10
    ('rip', 'torn'), # LUK 5:6
    ('ripped', 'pulled'), # JDG 16:14
    ('ripped', 'tore'), # GEN 37:34
    ('ripped', 'torn'), # JOB 16:9
    ('rise', 'arising'), # MIC 7:6
    ('rise', 'raised'), # MAT 24:7
    ('rise', 'arise'), # RV PSA 88:10 / LV PSA 88:11
    ('risen', 'arise'), # NUM 24:17
    ('risen', 'raises'), # MIC 2:8
    ('rises', 'arise'), # EXO 21:19
    ('river','Yarden'),
    ('riverbed','wadi'),
    ('road','way'), # Mat 3:3
    ('road', 'highway'), # CH1 26:18
    ('road', 'path'), # JOB 24:4
    ('roads', 'highways'), # JDG 20:31
    ('roam', 'roving'), # RV ZEC 4:10
    ('Roam', 'rove'), # RV JER 5:1
    ('roamed', 'walked/wandered'), # RV EZE 19:6
    ('roasted', 'cooked'), # CH2 35:13
    ('robbed', 'robbers'), # CO2 11:26
    ('robbed', 'taken'), # PRO 4:16
    ('robe','cloth'), # Mrk 14:51,63
    ('robe','clothes'), # Mrk 14:51,63
    ('robe', 'cloak'), # JNA 3:6
    ('robe', 'garment'), # SA2 13:19
    ('robe', 'skirt'), # ZEC 8:23
    ('robe', 'skirts'), # EZE 5:3
    ('robes', 'garments'), # CH2 34:22
    ('robes', 'tunics'), # RV NEH 7:72 / LV NEH 7:71
    ('rock','stone'),
    ('rock', 'stones'), # JOB 6:12
    ('rockface','rock'), # Mrk 15:46
    ('rock-hard', 'stone'), # EZE 11:19
    ('rocks','stones'),
    ('rocks','stone'),
    ('rocks', 'cliffs'), # SA1 13:6
    ('rocks', 'stoned'), # ACT 5:26
    ('rode', 'sat'), # JHN 12:14
    ('roof','housetop'),
    ('roof', 'rafter[s]'), # ECC 10:18
    ('roofed', 'panelled'), # KI1 6:9
    ('roofs','housetops'),
    ('room','place'),
    ('room', 'chamber'), # JDG 16:9
    ('rooms', 'side-chambers'), # EZE 41:8
    ('rooms', 'store-rooms'), # CH1 9:26
    ('ropes','cords'),
    ('ropes', 'tent-cords'), # EXO 35:18
    ('rose', 'raised'), # SA2 23:1
    ('rotten', 'rottenness'), # JOB 13:28
    ('rowers', 'row'), # EZE 27:26
    ('royal', 'palace'), # DAN 11:45
    ('royal', 'royalty'), # DAN 1:3
    ('rubble','ruin'),
    ('rubble', 'dust'), # EZE 26:12
    ('rubble', 'debris'), # RV NEH 4:10 / LV NEH 4:4
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
    ('rule', 'ruler'), # RV MIC 5:2 / LV MIC 5:1
    ('rule', 'rulers'), # RV HOS 7:7
    ('rule', 'reigned'), # RV KI1 12:17
    ('ruled', 'mastery'), # EZR 4:20
    ('ruled', 'reigned'), # CH1 18:14
    ('ruled', 'reigning'), # CH2 22:12
    ('ruler', 'leader'), # CH1 5:2
    ('ruler', 'noble'), # PRO 17:7
    ('ruler', 'prince'), # EZE 12:10
    ('ruler', 'rule'), # PSA 8:6
    ('ruler', 'ruling'), # RV GEN 45:26
    ('rulers', 'princes'), # PRO 28:2
    ('rulers', 'archon', 'aligned'),
    ('rulers', 'archontesin', 'aligned'),
    ('rules', 'decree'), # PSA 99:7
    ('rules', 'decrees'), # PSA 119:5
    ('rules', 'regulations'), # DEU 6:20
    ('rules', 'dominion'), # RV PSA 103:22
    ('ruling', 'reigned'), # RV CH2 10:17
    ('run', 'fled'), # KI1 11:23
    ('run', 'flee'), # LEV 26:17
    ('run', 'fleeing'), # CO1 6:18
    ('run', 'goes'), # LAM 3:48
    ('run', 'moved'), # JOB 32:15
    ('running', 'fled'), # MRK 16:8
    ('rural', 'regions'), # EST 9:19
    ('rush','hasten'),
    ('rush', 'haste'), # DEU 16:3
    ('rush', 'hastens'), # PRO 21:5
    ('rush', 'hurry'), # PRO 6:18
    ('rush', 'hastening'), # RV PRO 28:22
    ('rushed', 'haste'), # JOB 31:5
    ('rushing', 'hasten'), # JER 48:16
    ('rushing', 'hurries'), # PRO 7:23
    ('sacred','holiness'), # tent of meeting
    ('sacred','holy'), # tent of meeting
    ('sacrifice', 'offering'), # KI2 3:20
    ('sacrificed','smoke'),
    ('sacrificed', 'offered'), # PE1 2:24
    ('sacrifices', 'offering'), # CH1 21:29
    ('Sacrificing', 'offering'), # EXO 29:14
    ('sadducees', 'saddoukaios', 'aligned'),
    ('sadducees', 'saddoukaiousin', 'aligned'),
    ('sadness', 'gloominess'), # RV JAM 4:9
    ('safe', 'safety'), # JOB 21:9
    ('safe', 'secure'), # RV PHP 3:1
    ('safety', 'refuge'), # JER 17:17
    ('safety', 'security'), # EZE 39:6
    ('said', 'speaking'), # ACT 23:7
    ('said', 'spoke'), # SA1 4:20
    ('said', 'spoken'), # CH2 10:15
    ('sailed', 'voyage'), # ACT 21:7
    ('sailors', 'mariners'), # EZE 27:9
    ('saliva', 'spittle'), # RV SA1 21:13 / LV SA1 21:14
    ('salty', 'salt'), # RV JAM 3:12
    ('saluting','greeting'), # Mrk 15:18
    ('salvation', 'deliverance'), # JOB 13:16
    ('samaritans', 'samareitai', 'aligned'),
    ('samaritans', 'samareitasin', 'aligned'),
    ('same','again'), # Mrk 14:70
    ('sanctified', 'consecrated'), # ISA 13:3
    ('sanctuary','hideout'),
    ('sanctuary', 'holy'), # CH1 9:29
    ('sandals', 'sandal[s]'), # ISA 20:2
    ('sandals', 'shod'), # CH2 28:15
    ('sang', 'song'), # CH2 29:27
    ('sanity', 'understanding'), # RV DAN 4:36 / LV DAN 4:33
    ('sashes', 'belt'), # PRO 31:24
    ('satisfy', 'fill'), # PRO 6:30
    ('satisfy', 'satiety'), # PRO 13:25
    ('saul', 'saulos', 'aligned'),
    ('Save', 'deliver'), # PSA 22:20
    ('save', 'deliver'), # EZE 33:12
    ('save', 'delivered'), # ISA 36:19
    ('save', 'preserve'), # EZE 13:22
    ('save', 'redeemed'), # LAM 3:58
    ('save', 'redeems'), # PSA 103:4
    ('Save', 'preserve'), # RV PSA 64:1 / LV PSA 64:2
    ('save', 'delivering'), # RV SA1 19:11
    ('saved', 'delivered'), # EXO 14:30
    ('saved', 'redeemed'), # GAL 3:13
    ('saved', 'rescued'), # RV PSA 18:19 / LV PSA 18:20
    ('saves', 'delivers'), # SA1 14:39
    ('saves', 'delivering'), # RV PRO 14:25
    ('saving', 'preserving'), # GEN 19:19
    ('saviour', 'deliverer'), # HOS 13:4
    ('saw','observing'), # Mrk 16:4
    ('saw', 'find'), # DEU 22:3
    ('saw', 'found'), # ACT 9:33
    ('saw', 'known'), # LUK 9:11
    ('saw', 'looked'), # REV 15:5
    ('saw', 'meet'), # JDG 15:14
    ('saw', 'considered'), # RV ECC 4:4
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
    ('scared','dismayed'), # Mrk 16:*
    ('scared','feared'), # Mrk 16:*
    ('scared','fearing'), # Mrk 16:*
    ('scared', 'afraid', 'aligned'), # EXO 3:6
    ('scared', 'frightened'), # RV LUK 24:5
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
    ('scoffed','mocking'),
    ('scoffer', 'mocker'), # PRO 13:1
    ('scoffers', 'mockers'), # PRO 19:29
    ('scold', 'rebuke'), # LUK 17:3
    ('scold', 'rebuked'), # SA1 3:13
    ('scold', 'rebuking'), # JHN 8:46
    ('scolded', 'rebuked'),
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
    ('scribes', 'grammateus', 'aligned'),
    ('scribes', 'grammateusin', 'aligned'),
    ('scriptures','scroll'), # Mrk 12:26
    ('seams', 'leak[s]'), # EZE 27:9
    ('search','seek'), # Mat 2:13
    ('search','seeking'), # Mat 2:13
    ('Search', 'seek'), # ISA 55:6
    ('search', 'sought'), # ISA 65:10
    ('Search', 'Seek'), # RV ZEP 2:3
    ('searched', 'explored'), # JER 31:37
    ('searched', 'sought'), # EZE 22:30
    ('searches', 'seeking'), # MAT 7:8
    ('searches', 'seeks'), # PRO 31:13
    ('searching', 'seek'), # SA1 27:4
    ('searching', 'sought'), # SA2 17:20
    ('searching', 'seeking'), # RV JHN 7:11
    ('seashore', 'sea'), # RV HOS 1:10 / LV HOS 2:1
    ('season', 'time'), # EZE 34:26
    ('seat', 'sit'), # KI1 21:9
    ('seat', 'throne'), # SA1 2:8
    ('seated', 'sat'), # ACT 12:21
    ('seated', 'sit'), # KI1 21:12
    ('seated', 'sitting'), # CO1 14:30
    ('second','another'),
    ('secretaries', 'scribes'), # CH2 34:13
    ('secretary', 'scribe'), # KI2 25:19
    ('secretly', 'hide'), # PSA 64:5
    ('secretly', 'secrecy'), # DEU 27:15
    ('secrets', 'hidden'), # RV DEU 29:29 / LV DEU 29:28
    ('secure', 'confidence'), # JOB 18:14
    ('secure', 'securely'), # ACT 16:23
    ('secure', 'securities'), # ISA 32:18
    ('secure', 'security'), # EZE 30:9
    ('secure', 'trust'), # AMO 6:1
    ('secured','apprehended'), # Mrk 14:46
    ('secured', 'preserved'), # SA2 23:5
    ('securely', 'firm'), # SA2 22:34
    ('securely', 'security'), # EZE 34:28
    ('seditious', 'revolt'), # EZR 4:19
    ('seductive', 'seduction'), # EPH 4:22
    ('seductiveness', 'seduction'), # MAT 13:22
    ('See','Behold'),
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
    ('seem', 'appear'), # RV EZE 16:52
    ('seen', 'appeared'), # SA2 22:11
    ('seen', 'found'), # REV 16:20
    ('seen', 'known'), # PSA 77:19
    ('seen', 'observing'), # JHN 9:8
    ('seen', 'looked'), # RV PSA 54:7 / LV PSA 54:9
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
    ('semen', 'seed'), # RV LEV 15:16
    ('send', 'bring'), # RV JOL 3:11 / LV JOL 4:11
    ('sensible', 'prudent'), # MAT 25:2 (reviewed 2026-10-13)
    ('sensitive', 'delicate'), # DEU 28:54
    ('sent', 'dismissals'), # EXO 18:2
    ('sent', 'stretched'), # RV PSA 80:11 / LV PSA 80:12
    ('sentence', 'condemning'), # MRK 10:33
    ('sentenced','condemned'), # Mrk 14:55,64
    ('sentenced','put'), # Mrk 14:55,64
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
    ('servant', 'slave', 'aligned'), # CH1 2:34
    ('servants','attendants'), # Mrk 14:54
    ('servants','slaves'),
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
    ('set', 'laid'), # RV JER 50:24
    ('set', 'placed'), # RV GEN 28:12
    ('setting', 'arranging'), # ISA 21:5
    ('Settle', 'dwell'), # PSA 37:3
    ('settle', 'decide'), # ISA 2:4
    ('settle', 'dwell'), # GEN 35:1
    ('settle', 'encamp'), # NAH 3:17
    ('settle', 'rest'), # ISA 14:1
    ('settle', 'sink'), # RV AMO 8:8
    ('settled','dwelt'), # Mat 2:@3
    ('settled', 'dwell'), # KI2 17:6
    ('settled', 'dwelling'), # JDG 10:1
    ('settled', 'encamped'), # NEH 11:30
    ('settlements', 'villages'), # RV GEN 25:16
    ('seven','sevenfold'),
    ('several','many'), # Mrk 14:56
    ('shackled', 'shackle[s]'), # PSA 105:18
    ('shackles', 'fetters'), # RV JDG 16:21
    ('shade', 'shadow'), # EZE 17:23
    ('shadow', 'shade'), # SNG 2:3
    ('shadowed', 'overshadowing'), # MRK 9:7
    ('Shadrak', 'Shadrach'), # DAN 2:49
    ('shaggy', 'hairy'), # DAN 8:21
    ('shake', 'quake'), # EZE 27:28
    ('shaking','trembling'), # Mrk 16:8
    ('shame', 'disgrace'), # EZE 44:13
    ('shame', 'ignominy'), # PSA 69:7
    ('shameful', 'disgraceful'), # JER 29:23
    ('shameful', 'ignominy'), # PRO 18:13
    ('shameful', 'shame'), # CO2 4:2
    ('shameful', 'shamefully'), # PRO 17:2
    ('shaming', 'ignominy'), # RV PSA 4:2 / LV PSA 4:3
    ('shapes', 'form'), # RV EZE 8:10
    ('Share', 'portion'), # ECC 11:2
    ('share', 'part'), # JOB 32:17
    ('share', 'portion'), # PSA 68:23
    ('sharp', 'sharpened'), # ISA 5:28
    ('sharper', 'sharp'), # PRO 5:4
    ('shattered', 'broke'), # KI2 18:4
    ('shattered', 'broken'), # RV LEV 6:28 / LV LEV 6:21
    ('shaved','baldness'),
    ('shearing', 'shearers'), # GEN 38:12
    ('shed','hut'),
    ('sheep', 'flock'), # CH1 17:7
    ('sheep', 'flock[s]'), # GEN 47:17
    ('sheep', 'flocks'), # ISA 17:2
    ('sheep', 'lambs'), # JOB 31:20
    ('sheep', 'ram'), # LEV 7:23
    ('sheep', 'rams'), # LEV 22:19
    ('shekels', 'shekel[s]'), # GEN 23:15
    ('shelter', 'refuge'), # RV PSA 64:10 / LV PSA 64:11
    ('shelters', 'tents', 'aligned'), # LUK 9:33
    ('shepherds', 'sheep-tenders'), # AMO 1:1
    ('She\'s','She'),
    ('shine', 'radiance'), # RV MRK 13:24
    ('shining', 'brightness'), # JOL 2:10
    ('shock', 'appalled'), # EZE 32:10
    ('shocked', 'appalled'), # PSA 40:15
    ('shook', 'stirred'), # SA1 4:5
    ('shoot', 'shooters'), # GEN 21:16
    ('shore','side'),
    ('shore', 'land'), # JHN 21:8
    ('short', 'shortened'), # CO1 7:29
    ('shortage', 'famine'), # KI1 18:2
    ('should','let'), # Mrk 15:12
    ('should','may'), # Mrk 15:12
    ('should','ought'),
    ('shoulder', 'arm'), # DEU 18:3
    ('shoulder', 'arms'), # KI2 9:24
    ("shouldn't",'not'),
    ('Shout', 'call'), # ISA 58:1
    ('shout', 'cry'), # JOB 20:5
    ('shouted','saying'), # Mrk 14:63, 15:29
    ('shouted', 'called'), # CH2 32:18
    ('shouted', 'crying'), # ACT 12:22
    ('shouting','saying'), # Mrk 14:63, 15:29
    ('shouting', 'cry'), # ECC 9:17
    ('shouting', 'crying'), # ACT 21:34
    ('shouts', 'cry'), # JER 48:34
    ('shouts', 'shoutings'), # ZEC 4:7
    ('show', 'present'), # KI1 18:1
    ('show', 'reveal'), # ISA 49:9
    ('show', 'displaying'), # RV TIT 3:2
    ('show', 'testifying'), # RV JHN 5:36
    ('show', 'demonstrating'), # RV GAL 2:18
    ('shown', 'revealed'), # PE1 1:12
    ('shows', 'revealed'), # CO2 3:3
    ('shows', 'display'), # RV TH2 1:5
    ('shrines','places'),
    ('shrivelled', 'withered'), # RV JNA 4:7
    ('shut', 'closed'), # GEN 7:16
    ('siblings', 'brothers', 'aligned'), # JOS 2:18
    ('sick','sickly'),
    ('sick', 'sickness'), # ISA 1:5
    ('side', 'thigh'), # RV PSA 45:3 / LV PSA 45:4
    ('siege', 'siege-work'), # EZE 17:17
    ('sight', 'eyes'), # AMO 9:3
    ('signal', 'standard'), # ISA 11:10
    ('signature', 'mark'), # JOB 31:35
    ('signet', 'signet-ring'), # EST 3:10
    ('silence', 'silent'), # ACT 15:12
    ('silence', 'hush'), # RV AMO 8:3
    ('silenced', 'silent'), # JER 47:5
    ('silent', 'silence'), # JOB 11:3
    ('silent', 'dumb'), # RV EZE 24:27
    ('silent', 'quiet'), # LUK 14:4 (reviewed 2026-10-13)
    ('silently', 'silent'), # EZE 24:17
    ('silver-plated', 'silver'), # ISA 30:22
    ('similar','likewise'), # Mrk 14:31
    ('similar', 'like'), # EZE 42:12
    ('Similarly','Likewise'), # Mrk 14:31
    ('simple', 'naive'), # PRO 19:25
    ('simple-minded', 'simple'), # JOB 5:2
    ('sincere', 'sincerity'), # EPH 6:5
    ('sincerely', 'sincere'), # PE2 3:1
    ('sincerely', 'sincerity'), # COL 3:22
    ('sing', 'songs'), # PSA 69:12
    ('singing', 'song'), # CH2 23:18
    ('single','one'), # Mrk 14:37
    ('Single', 'unmarried'), # CO1 7:32
    ('sinning', 'transgressed'), # RV EZE 2:3
    ('sins', 'guilts'), # RV PSA 69:5 / LV PSA 69:6
    ('sit', 'dwell'), # MIC 4:4
    ('sits', 'dwelling'), # ZEC 1:11
    ('sits', 'dwells'), # LAM 1:3
    ('sitting','reclining'),
    ('sitting', 'dwelling'), # KI2 6:1
    ('sitting', 'seated'), # RV LUK 10:39
    ('situation', 'matter'), # SA2 14:20
    ('skies','heavens'),
    ('skies', 'heaven'), # ZEC 12:1
    ('skilled', 'skill'), # CH1 28:21
    ('skilled', 'skillful'), # CH1 22:15
    ('skillfully', 'skill'), # HOS 13:2
    ('skin','hide'),
    ('skins', 'hides'), # RV LEV 16:27
    ('skull', 'crown'), # PSA 7:16
    ('sky','heaven'),
    ('sky', 'heavens'), # DEU 28:23
    ('slack', 'slackness'), # JER 48:10
    ('slain', 'killed'), # LAM 2:4
    ('slander', 'slanderous'), # PE2 2:11
    ('slander', 'defamed'), # RV CO1 4:13
    ('slanderer', 'slanderous'), # TI1 1:13
    ('slap', 'struck'), # JOB 16:10
    ('slapped', 'struck'), # KI1 22:24
    ('slaps', 'striking'), # LUK 6:29
    ('slaughter', 'kill'), # ZEC 11:5
    ('slaughtered', 'killed'), # GEN 34:25
    ('slaughtered', 'slain', 'aligned'), # DEU 32:42
    ('slaughterhouse', 'slaughter'), # ACT 8:32
    ('slave', 'maid'), # EXO 2:5
    ('slave', 'maidservant'), # GEN 16:2
    ('slave', 'maidservants'), # GEN 33:2
    ('slavery', 'servitude'), # NEH 9:17
    ('slavery', 'slaves'), # DEU 6:12
    ('slaves', 'enslaved'), # ROM 6:18
    ('slaves', 'maidservants'), # GEN 33:1
    ('slaves', 'servant[s]'), # RV GEN 32:5 / LV GEN 32:6
    ('sledge', 'threshing-sledge'), # ISA 41:15
    ('sledges', 'threshing-sledges'), # CH1 21:23
    ('sleeps', 'lie'), # RV EXO 22:16 / LV EXO 22:15
    ('slingshots', 'slings'), # CH2 26:14
    ('slumped', 'sank'), # KI2 9:24
    ('small','little'),
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
    ('smashed', 'crushed'), # RV MIC 1:7
    ('smashing', 'break'), # JER 43:13
    ('smashing', 'breaking'), # ISA 30:13
    ('smearers', 'smear'), # JOB 13:4
    ('smell', 'odour'), # SNG 4:10
    ('smile', 'cheerful'), # JOB 9:27
    ('smooth', 'seductiveness'), # PRO 7:21
    ('smooth', 'smoothness'), # PRO 6:24
    ('smoother', 'smooth'), # PRO 5:3
    ('smoothly', 'smoothnesses'), # PRO 23:31
    ('smooth-skinned', 'smooth'), # ISA 18:2
    ('snake', 'serpent'), # EXO 7:9
    ('snakes','vipers'), # Mat 3:7
    ('snakes', 'serpents'), # EXO 7:12
    ('snared', 'ensnared'), # ISA 8:15
    ('snares', 'traps'), # PSA 38:12
    ('snare-traps', 'snare'), # ISA 24:17
    ('snatched', 'seized'), # SA2 23:21
    ('sneakily', 'sneaking'), # PE2 2:1
    ('snowy', 'snow'), # CH1 11:22
    ('So','And'),
    ('So','Therefore'),
    ('so','yes'),
    ('so','correct'),
    ('so','thus', 'both'),
    ('soaked','filled'), # Mrk 15:36
    ('softer', 'soft'), # RV PSA 55:21 / LV PSA 55:22
    ('soil', 'ground'), # JOL 1:10
    ('soldiers', 'soldier/messenger'), # CH2 18:18
    ('soldiers', 'soldier[s]'), # KI1 20:29
    ('soldiers', 'troop[s]'), # RV MIC 5:1 / LV MIC 4:14
    ('some', 'any', 'aligned'),
    ('someone','anyone'), # Mrk 15:36
    ('someone','One'), # Mrk 15:36
    ('son', 'child'), # ECC 12:12
    ('song', 'poem'), # RV PSA 52:0 / LV PSA 52:1,PSA 52:2
    ('songs','psalms'), # Mrk 14:26
    ('songs','hymns'), # Mrk 14:26
    ('sons','boys'), # Mat 2:16
    ('sons', 'children'), # GEN 22:20
    ('sons', 'son', 'aligned'), # Still needed by positional alignment when the noun repeats.
    ('soon','shortly', 'both'),
    ('soon', 'quickly'), # JHN 13:27 (reviewed 2026-10-13)
    ('sorcerer', 'magician'), # ACT 13:8
    ('sorcerers', 'magicians/soothsayers'), # RV GEN 41:24
    ('sorcery', 'sorcerer'), # DEU 18:10
    ('sorcery', 'sorcerers'), # MAL 3:5
    ('sorry', 'compassion'), # EXO 2:6
    ('soul', 'life'), # PRO 25:13
    ('soul', 'self'), # GEN 42:21
    ('sound', 'voice'), # EZE 33:32
    ('sounds', 'voices'), # RV REV 16:18
    ('sour','vinegar'), # Mrk 15:36
    ('source', 'root'), # RV REV 22:16
    ('south', 'southward'), # CH1 9:24
    ('south', 'Southward'), # RV JOS 17:10
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
    ('speak', 'uttered'), # RV JER 23:31
    ('speak', 'announce'), # RV GEN 32:5 / LV GEN 32:6
    ('speaking','saying'),
    ('spears', 'spear[s]'), # PSA 46:9
    ('spears', 'spearmen'), # ACT 23:23
    ('specifications', 'measurement'), # CH2 24:13
    ('specifications', 'plans'), # KI1 6:38
    ('speech', 'lips'), # PRO 19:1
    ('spell', 'enchantment'), # RV NUM 23:23
    ('spend', 'pass'), # SA2 17:8
    ('spends', 'passes'), # JOB 39:28
    ('spent', 'passed'), # SA2 12:16
    ('spent', 'stayed'), # GEN 31:54
    ('spiced','myrrh'), # Mrk 15:23
    ('spiced', 'spice'), # SNG 8:2
    ('spiced', 'mixed'), # RV SNG 7:2 / LV SNG 7:3
    ('spices', 'seasoning'), # EZE 24:10
    ('spices', 'spiced'), # PSA 75:8
    ('Spirit', 'breath/wind/spirit'), # GEN 6:3
    ('spirit', 'breath'), # JOB 26:4
    ('spirit', 'breath/wind/spirit'), # DAN 2:3
    ('spirit', 'heart'), # RV KI2 5:26
    ('spirits', 'breath/wind/spirit'), # EZR 1:5
    ('spiritual', 'spirit'), # CO1 14:2
    ('spiritual', 'spirits'), # CO1 14:12
    ('spiritual', 'spiritually'), # REV 11:8
    ('spiritually', 'spirit'), # PE1 4:6
    ('spit', 'spittle'), # RV JOB 30:10
    ('splash', 'sprinkle'), # LEV 1:5
    ('splashed', 'sprinkle'), # LEV 7:2
    ('splashed', 'sprinkled'), # LEV 8:19
    ('splashes', 'sprinkles'), # LEV 7:14
    ('splattered', 'spattered'), # ISA 63:3
    ('splendid', 'splendour'), # EZE 26:20
    ('splendid', 'glorious'), # RV PSA 45:13 / LV PSA 45:14
    ('splendour','glory'),
    ('splendour', 'adornment'), # CH2 20:21
    ('splendour', 'luster'), # PSA 89:44
    ('splendour', 'splendid'), # JOB 31:26
    ('split', 'divided'), # GEN 2:10
    ('splits', 'cleaves'), # ECC 10:9
    ('spoil', 'plunder'), # KI2 3:23
    ('spoil', 'plunders'), # HAB 2:7
    ('spoke','said'),
    ('spoke','answering'),
    ('spoke', 'mouth'), # JOB 3:1
    ('spoke', 'words/messages'), # JER 48:27
    ('spoken','said'),
    ('spoken','saying'),
    ('spoken', 'words/messages'), # KI1 1:7
    ('sport', 'laughter'), # PRO 10:23
    ('spot', 'place'), # PSA 55:8
    ('spread', 'opened'), # EZE 16:25
    ('spread', 'scatter'), # PRO 15:7
    ('spread', 'scattered'), # GEN 10:18
    ('springs', 'sprouts'), # HOS 10:4
    ('sprinkle', 'spatter'), # EXO 29:21
    ('sprinkled', 'scattered'), # RV EXO 32:20
    ('squirm', 'writhing'), # JOB 15:20
    ('staff', 'rod'), # JDG 5:14
    ('stagger', 'wander'), # JOB 12:25
    ('stained', 'soiled'), # REV 3:4
    ('stained', 'defiled'), # RV ISA 63:3
    ('stairs', 'steps'), # NEH 3:15
    ('stalks', 'stubble'), # RV MAL 4:1 / LV MAL 3:19
    ('stand', 'endure'), # DAN 2:44
    ('standing', 'standing-place'), # JOS 4:3
    ('start', 'beginning'), # LUK 13:26
    ('started','began'), # Mat 3:1
    ('started','arriving'), # Mat 3:1
    ('started', 'begun'), # ACT 8:35
    ('started', 'kindled'), # RV EXO 22:6 / LV EXO 22:5
    ('starting', 'begun'), # LUK 24:27
    ('starts', 'begin'), # MAT 24:49
    ('starve', 'hunger'), # RV EXO 16:3
    ('stated', 'said'), # NUM 13:30
    ('stated', 'told'), # RV SA1 24:18 / LV SA1 24:19
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
    ('stay', 'remains'), # RV JOB 14:2
    ('stay', 'lodge'), # RV PSA 55:7 / LV PSA 55:8
    ('stayed', 'dwell'), # PSA 139:9
    ('stayed', 'dwelt'), # GEN 25:27
    ('stayed', 'remained'), # ACT 17:14
    ('stayed', 'remaining'), # CH1 20:1
    ('stayed', 'sojourning'), # SA2 4:3
    ('stayed', 'detain'), # RV JDG 13:16
    ('staying','dwelling'),
    ('staying', 'remaining'), # CH2 32:10
    ('staying', 'sojourned'), # EXO 6:4
    ('staying', 'sojourning'), # JDG 17:7
    ('stays', 'dwells'), # PSA 91:1
    ('stays', 'remaining'), # HEB 7:24
    ('stays', 'remains'), # JER 21:9
    ('steady', 'permanence'), # GEN 49:24
    ('steady', 'steadiness'), # EXO 17:12
    ('stealing', 'thefts'), # MAT 15:19
    ('steeled','courage'), # Mrk 15:43
    ('steep', 'descent'), # MIC 1:4
    ('stephen', 'stephanos', 'aligned'),
    ('steps', 'step[s]'), # PRO 16:9
    ('steps', 'heels'), # RV PSA 56:6 / LV PSA 56:7
    ('stewards','managers'),
    ('stick','staff'), # Mrk 15:19,36
    ('stick','reed'), # Mrk 15:19,36
    ('stick', 'clinging'), # DAN 2:43
    ('stick', 'firewood'), # AMO 4:11
    ('stick', 'staves'), # SA1 17:43
    ('stick', 'wood'), # EZE 37:17
    ('stick', 'cleave'), # RV PSA 137:6
    ('sticks', 'cleaved'), # LAM 4:4
    ('sticks', 'clinging'), # PRO 18:24
    ('sticks', 'cling'), # RV PSA 22:15 / LV PSA 22:16
    ('stillborn', 'miscarriage'), # ECC 6:3
    ('stingers', 'stings'), # REV 9:10
    ('stir', 'raise'), # HAB 1:6
    ('stir', 'arouse'), # SNG 2:7 (reviewed 2026-10-13)
    ('stirred', 'aroused'), # PSA 45:1
    ('stock', 'livestock'), # RV KI1 18:5
    ('stocks', 'stock[s]'), # JER 20:2
    ('stomach', 'belly'), # PRO 13:25
    ('stomachs', 'belly'), # JOB 20:15
    ('stones', 'rock[s]'), # JOB 22:24
    ('stones', 'stone[s]'), # ISA 62:10
    ('stone-workers', 'stonemasons'), # CH2 24:12
    ('stony', 'rocky'), # MAT 13:5
    ('Stop', 'cease'), # ISA 1:16
    ('stop', 'cease'), # EZE 16:41
    ('stop', 'ceasing'), # ACT 6:13
    ('stop', 'restrain'), # NUM 11:28
    ('stop', 'restrained'), # JOB 29:9
    ('stopped','stood'), # Mat 2:9
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
    ('straighten', 'straight'), # ECC 7:13
    ('straightened', 'straight'), # ECC 1:15
    ('straightening', 'straight'), # SA1 13:21
    ('straightforward', 'straightforwardness'), # ISA 57:2
    ('straight-talking', 'straight'), # TI2 2:15
    ('strangers', 'sojourner'), # PSA 94:6
    ('strangers', 'sojourning'), # CH1 16:19
    ('strapped', 'girded'), # SA1 17:39
    ('straw', 'chaff'), # ISA 40:24
    ('strayed', 'wander'), # RV EZE 34:6
    ('streaked', 'striped'), # GEN 30:35
    ('stream', 'wadi'), # AMO 5:24
    ('streams', 'rivers'), # RV EXO 8:5 / LV EXO 8:1
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
    ('strides', 'step[s]'), # RV SA2 22:37
    ('strike', 'assailant'), # JOB 36:32
    ('strike', 'attack'), # SA2 5:24
    ('strike', 'attacks'), # SA2 5:8
    ('strike', 'defeat'), # JDG 6:16
    ('strikes', 'attacks'), # CH1 11:6
    ('strikes', 'slaps'), # JOB 34:26
    ('strikes', 'smashes'), # JOB 5:18
    ('strive', 'contend'), # ROM 15:30
    ('strong','forceful'),
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
    ('stunned','amazed'), # Mrk 16:5,8
    ('stunned','amazement'), # Mrk 16:5,8
    ('stunned', 'astonished'), # MRK 10:26
    ('stupid', 'foolish'), # LUK 11:40 (reviewed 2026-10-13)
    ('stupidity', 'foolishness'), # PRO 5:23
    ('subdue', 'tame'), # MRK 5:4
    ('subdued', 'humbled'), # CH2 13:18
    ('subject', 'served'), # GEN 14:4
    ('submissively', 'submission'), # TI1 2:11
    ('submit', 'bow'), # PSA 45:11
    ('submit', 'submission'), # GAL 2:5
    ('Submit', 'subjected'), # RV PE1 2:13
    ('submit', 'subjected'), # RV CO1 16:16
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
    ('suffer', 'bearing'), # RV JER 15:15
    ('suffered', 'sufferings'), # HEB 2:10
    ('suffered', 'borne'), # RV PSA 88:15 / LV PSA 88:16
    ('suffering', 'pain'), # JOB 2:13
    ('suffering', 'affliction', 'aligned'), # LAM 1:7
    ('suffering', 'distressed'), # RV LUK 16:25
    ('sufferings', 'pains'), # JOB 9:28
    ('summit', 'top'), # SA2 15:32
    ('summoned', 'call'), # EXO 10:16
    ('summoned', 'called'), # SA1 10:17
    ('summoned', 'mustered'), # RV EZE 38:8
    ('Summoning', 'calls'), # ISA 46:11
    ('Sunday','first'), # Mrk 16:2
    ('sunk', 'dropped'), # RV JOB 29:22
    ('sunlight', 'sun'), # RV PSA 58:8 / LV PSA 58:9
    ('sunshine', 'sun'), # RV DEU 33:14
    ('supervisor', 'overseer'), # JER 20:1
    ('supervisors', 'overseers'), # CH2 34:12
    ('supplied', 'giving'), # RV KI1 5:10 / LV KI1 5:24
    ('support', 'help'), # CH2 26:13
    ('support', 'helped'), # KI1 1:7
    ('support', 'minister'), # ROM 15:27
    ('supported', 'help'), # JOB 31:21
    ('supported', 'stand'), # CH2 11:13
    ('supports', 'sustain'), # RV PSA 54:4 / LV PSA 54:6
    ('supports', 'sustaining'), # RV PSA 37:17
    ('surging', 'swelling'), # PSA 46:3
    ('surprised','amazed'), # Mrk 16:6
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
    ('sustain', 'confirming'), # RV CO1 1:8
    ('sweet', 'sweetnesses'), # SNG 5:16
    ('sweeter', 'sweet'), # JDG 14:18
    ('sweetness', 'sweet'), # JDG 14:14
    ('swept', 'dragging'), # REV 12:4
    ('swifter', 'swift'), # SA2 1:23
    ('swindlers','robbers'),
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
    ('taken','carried'), # Mrk 15:1, Mat 4:1
    ('taken','brought'), # Mrk 15:1, Mat 4:1
    ('taken', 'carry'), # MAL 2:3
    ('taken', 'consumed'), # ISA 3:14
    ('taken', 'remove'), # JOB 34:20
    ('taken', 'removed'), # DEU 26:13
    ('taken', 'seize'), # JOB 30:16
    ('Taking', 'removes'), # PRO 25:20
    ('taking', 'bringing'), # LUK 24:1
    ('taking', 'brought'), # CH2 29:21
    ('taking', 'choosing'), # SA1 20:30
    ('talk','spoke'), # Mrk 16:8
    ('talk', 'preach'), # ROM 1:15
    ('talk', 'speak'), # DEU 6:7
    ('talk', 'speaking'), # EPH 5:12
    ('Talk', 'speak'), # RV EXO 14:15
    ('talk', 'spoken'), # RV SA1 9:21
    ('talked', 'speaking'), # ZEC 1:13
    ('talked', 'spoke'), # GEN 45:15
    ('talked', 'spoken'), # RV JER 38:25
    ('talking','speaking'),
    ('talking','saying'),
    ('talking', 'spoke'), # MAT 16:11
    ('talking', 'spoken'), # EXO 34:29
    ('talking', 'speak'), # RV ECC 1:8
    ('tall', 'high'), # EZE 16:39
    ('taller', 'tall'), # SA1 10:23
    ('tarpaulin','cover'),
    ('tassel', 'tassel[s]'), # NUM 15:39
    ('taste', 'palate'), # PSA 119:103
    ('tastes', 'palate'), # PRO 24:13
    ('tasty', 'delicious'), # GEN 27:17
    ('tattoo','inscription'), # Lev 19:28
    ('taught', 'instructed'), # PRO 31:1
    ('taunts', 'mock'), # RV PSA 22:7 / LV PSA 22:8
    ('teach', 'instruct'), # JOB 27:11
    ('teacher', 'teaches'), # HAB 2:18
    ('teacher', 'teaching'), # TI1 3:2
    ('teachers','scribes'),
    ('teaches', 'instructing'), # TIT 2:12
    ('teaches', 'instructed'), # RV PSA 16:7
    ('teaching','saying'), # Mrk 14:27
    ('teaching', 'instruct'), # JOB 34:32
    ('teaching', 'instruction'), # PRO 6:23
    ('teachings','messages'), # Mrk 13:31
    ('tear', 'break'), # ECC 3:3
    ('tear', 'pull'), # DEU 12:3
    ('tears', 'breaks'), # PRO 29:4
    ('tears', 'tear[s]'), # KI2 20:5
    ('tears', 'weeping'), # PSA 102:9
    ('tears', 'wept'), # JHN 11:35
    ('tell','saying'), # Mat 3:9
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
    ('Tell', 'recount'), # RV JOL 1:3
    ('tell', 'announce'), # JOB 1:15 (reviewed 2026-10-13)
    ('telling','proclaimed'),
    ('telling','saying'),
    ('telling','speaking'),
    ('telling', 'proclaiming'), # ACT 28:31
    ('telling', 'said'), # EXO 24:8
    ('telling', 'say'), # HAG 1:1
    ('telling', 'says'), # ISA 52:7
    ('telling', 'speak'), # DEU 32:45
    ('telling', 'spoke'), # CH2 32:19
    ('telling', 'spoken'), # ISA 1:20
    ('telling', 'recounting'), # RV KI2 8:5
    ('tells','say'),
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
    ('tent','tabernacle'),
    ('tent', 'sanctuary'), # JOS 24:26
    ('tent', 'covering'), # RV PSA 18:11 / LV PSA 18:12
    ('tents', 'dwellings'), # EZE 25:4
    ('terrible', 'severe'), # JER 21:5
    ('terrified', 'frightened'), # REV 11:13
    ('terrified', 'alarmed'), # RV DAN 4:5 / LV DAN 4:2
    ('terrify', 'terror'), # EZE 32:32
    ('terrifying', 'terrible'), # DAN 2:31
    ('terrifying', 'terror'), # DEU 34:12
    ('terrifying', 'terrors'), # PSA 88:16
    ('terrifying', 'feared'), # RV PSA 47:2 / LV PSA 47:3
    ('territories', 'region'), # GEN 14:7
    ('territory','land'), # Mat 2:6
    ('territory', 'region'), # SA1 6:1
    ('terror', 'dread'), # PSA 91:5
    ('terrorized', 'terror'), # EZE 23:46
    ('terrors', 'dreads'), # JOB 15:21
    ('testified', 'warned'), # NEH 9:26
    ('testified', 'attested'), # RV HEB 7:8
    ('testify', 'testimony'), # CO2 1:12
    ('testify', 'warn'), # AMO 3:13
    ('testimony', 'testified'), # JHN 5:33
    ('testimony', 'testifies'), # PRO 25:18
    ('testing', 'trial'), # HEB 3:8
    ('thaddaeus', 'thaddaios', 'aligned'),
    ('thaddeus', 'thaddaios', 'aligned'),
    ('than', 'from', 'aligned'),
    ('thank', 'thank-offering'), # JER 17:26
    ('thank', 'thank-offerings'), # PSA 56:12
    ('thank', 'thanksgiving'), # CH2 33:16
    ('thanked', 'thankfulness'), # CO2 8:16
    ('thankful', 'thankfulness'), # CO1 15:57
    ('thankful', 'thanks'), # ROM 16:4
    ('thankful', 'thanksgiving'), # COL 2:7
    ('thankfulness', 'thanksgiving'), # EPH 5:4
    ('thanking', 'thanksgiving'), # PHP 4:6
    ('thanks', 'thanksgiving'), # CO2 9:11
    ('thanks', 'thanksgivings'), # CO2 9:12
    ('thanksgiving', 'thank-offering'), # AMO 4:5
    ('thanksgiving', 'thanks'), # NEH 11:17
    ('that','this'),
    ('that','which', 'both'),
    ('that', 'who', 'aligned'),
    ('theft', 'robbery'), # RV LEV 6:2 / LV LEV 5:21
    ('their', 'theirs', 'aligned'),
    ('them', 'those', 'aligned'),
    ('themselves','hearts'),
    ('Then','And'), # Mrk 14:72
    ('then','And'), # Mrk 14:72
    ('then','immediately'), # Mrk 14:72
    ('then', 'when', 'aligned'),
    ('there', 'here', 'aligned'),
    ('thick', 'thickness'), # CH2 4:5
    ('thicker', 'thick'), # CH2 10:10
    ('thickets', 'thicket[s]'), # JER 50:44
    ('thief','robber'), # Mrk 14:48
    ('thighs', 'loins'), # DAN 2:32
    ('thin', 'lean'), # RV EZE 34:20
    ('think','wondered'), # Mat 3:9
    ('think','suppose'), # Mat 3:9
    ('Think', 'consider'), # PRO 6:6
    ('think', 'considers'), # JOB 41:32
    ('think', 'intended'), # ISA 10:7
    ('think', 'remember'), # EZE 36:31
    ('think', 'remembered'), # PSA 63:6
    ('think', 'supposing'), # CO1 10:12
    ('think', 'believing'), # RV ROM 14:2
    ('thinking','reasoning'),
    ('thinking','supposing'),
    ('thinking', 'suppose'), # JHN 16:2
    ('thinking', 'thoughts'), # JOB 21:27
    ('thinks', 'considers'), # PRO 15:28
    ('thinks', 'supposing'), # CO1 3:18
    ('third','another'),
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
    ('those','these'),
    ('thought','saying'), # Mrk 15:35
    ('thought', 'considered'), # ISA 53:4
    ('thought', 'remembered'), # EZE 16:22
    ('thought', 'supposed'), # ACT 26:9
    ('thought', 'supposing'), # RV JHN 13:29
    ('thoughtful','intelligently'), # Mrk 12:34
    ('thoughts', 'plans'), # PSA 40:5
    ('threaten', 'threat'), # EPH 6:9
    ('threats', 'threatened'), # ACT 4:21
    ('three-stranded', 'threefold'), # ECC 4:12
    ('threshhold', 'threshold'), # SA1 5:4
    ('threw', 'hurled'), # JNA 1:5
    ('thrive', 'prosper'), # EZE 17:10
    ('through','by'), # Mat 1:18
    ('through', 'thru', 'aligned'),
    ('throw', 'hurl'), # JNA 1:12
    ('thrown', 'thrust'), # ISA 49:21
    ('thrown', 'hurled'), # RV PRO 16:33
    ('thunderbolts', 'thunder'), # JOB 38:25
    ('thundercloud', 'thunder'), # PSA 81:7
    ('thunderous', 'thunder'), # PSA 77:18
    ('thunderous', 'thunders'), # REV 4:5
    ('thunderstorms', 'thunder-clouds'), # ZEC 10:1
    ('Tie', 'bind'), # ISA 8:16
    ('Tie', 'bound'), # MAT 22:13
    ('tie', 'bind'), # EXO 28:28
    ('tie', 'bound'), # JDG 16:6
    ('tied','bound'),
    ('ties', 'bind'), # RV MRK 3:27
    ('timber', 'wood'), # HAG 1:8
    ('timber', 'woods'), # CH1 22:14
    ('time','hour'), # Mrk 13:32
    ('time', 'days'), # RV KI1 22:46 / LV KI1 22:47
    ('time', 'day'), # RV ZEC 2:11 / LV ZEC 2:15
    ('timothy', 'timotheos', 'aligned'),
    ('tipped','overturned'),
    ('tired', 'wearied'), # JHN 4:6
    ('tired', 'weary'), # ISA 43:22
    ('titus', 'titos', 'aligned'),
    ('told','commanded'), # Mrk 14:34, Mat 2:5
    ('told','saying'), # Mrk 14:34, Mat 2:5
    ('told','said'), # Mrk 14:34, Mat 2:5
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
    ('top', 'height'), # RV DAN 4:11 / LV DAN 4:8
    ('top', 'covering'), # RV GEN 8:13
    ('tops', 'crown'), # RV DEU 28:35
    ('tops', 'height[s]'), # RV ISA 37:24
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
    ('total','all'),
    ('totally','greatly'), # Mrk 16:5
    ('touch', 'reaches'), # JOB 4:5
    ('toward', 'towards', 'both'), # GEN 12:9
    ('towards','toward'),
    ('towered', 'lofty'), # EZE 19:11
    ('town','city'),
    ('town', 'cities'), # ACT 8:40
    ('towns', 'cities'), # DEU 2:37
    ('towns', 'city'), # LUK 8:1
    ('traded', 'exchanged'), # PSA 106:20
    ('traded', 'bartered'), # RV LUK 19:15
    ('trading', 'exchange'), # JOB 20:18
    ('trading', 'merchandising'), # RV JAM 4:13
    ('traditions', 'customs'), # RV ACT 6:14
    ('train', 'learn'), # MIC 4:3
    ('trained', 'learned'), # JHN 7:15
    ('trample', 'tread'), # DAN 7:23
    ('trample', 'treads'), # RV JER 51:33
    ('trampled', 'trodden'), # ISA 63:18
    ('trampling', 'treading'), # REV 19:15
    ('transgresses', 'sin'), # LEV 4:27
    ('transgressors', 'rebels'), # DAN 8:23
    ('translate', 'interpreting'), # CO1 14:5
    ('translate', 'translation'), # CO1 12:10
    ('translating', 'interpreting'), # CO1 12:30
    ('translator', 'interpreter'), # CO1 14:28
    ('transplanted', 'planted'), # RV PSA 80:8 / LV PSA 80:9
    ('trap', 'snare'), # JER 48:44
    ('trapped', 'ensnared'), # DEU 7:25
    ('trapping', 'snare'), # RV DEU 7:16
    ('traps', 'snare'), # JER 48:43
    ('traps', 'snares'), # PRO 13:14
    ('travel', 'go'), # PSA 104:26
    ('travel', 'going'), # MAT 23:15
    ('travel', 'pass'), # DEU 2:18
    ('travel', 'went'), # CH2 15:5
    ('travel', 'gone'), # RV ACT 23:23
    ('travelled', 'passed'), # ACT 16:6
    ('travelled', 'went'), # CH1 17:6
    ('travelled', 'gone'), # RV MAT 28:16
    ('travelled', 'journeyed'), # RV ISA 57:9
    ('travellers', 'walkers'), # JDG 5:6
    ('travelling', 'pass'), # JOB 21:29
    ('travelling', 'passed'), # GEN 12:6
    ('travelling', 'passing'), # ACT 18:23
    ('travelling', 'journeying'), # RV ACT 22:6
    ('trays', 'fire-pans'), # EXO 37:23
    ('treacherous', 'treacheries'), # ZEP 3:4
    ('treacherous', 'treacherously'), # HAB 1:13
    ('treacherously', 'treacherous'), # JER 3:8
    ('treachery', 'deceits'), # PSA 38:12
    ('treachery', 'unfaithfulness'), # DAN 9:7
    ('tread', 'trampling'), # RV ISA 7:25
    ('treason', 'treachery'), # RV KI2 9:23
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
    ('trembled', 'quaked'), # RV PSA 68:8 / LV PSA 68:9
    ('trembling', 'shook'), # DAN 10:10
    ('trial', 'tested'), # RV DAN 1:14
    ('tribes', 'tribe[s]'), # EXO 28:21
    ('tried', 'attempting'), # ACT 26:21
    ('tried', 'judged'), # ACT 23:6
    ('tried', 'seek'), # CH2 31:21
    ('tried', 'seeking'), # ACT 13:8
    ('tried', 'sought'), # ECC 7:28
    ('tries', 'attempt'), # JOB 4:2
    ('tries', 'seek'), # LUK 17:33
    ('trip','travelling'), # Mrk 13:34
    ('trips', 'travelled'), # RV LUK 20:9
    ('triumph', 'rejoice'), # PRO 28:12
    ('triumphantly', 'triumph'), # ISA 44:23
    ('troops', 'troop[s]'), # CH2 25:9
    ('trouble', 'distress'), # LAM 1:21
    ('trouble', 'harm'), # KI2 14:10
    ('trouble', 'mischief'), # HAB 1:3
    ('troubled', 'disturbed'), # DAN 2:1
    ('troubles', 'afflicted'), # PSA 119:67
    ('troubles', 'distress'), # PSA 77:2
    ('troubles', 'tribulation'), # JHN 16:33 (reviewed 2026-10-13)
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
    ('trust', 'relies'), # RV EZE 33:13
    ('trust', 'hoped'), # RV EPH 1:12
    ('trusted', 'believing'), # JHN 1:12
    ('trusted', 'faithfulness'), # CH1 9:26
    ('trusting', 'rely'), # KI2 18:20
    ('trusting', 'relying'), # CH2 32:10
    ('trusting', 'security'), # PRO 3:29
    ('trusts', 'confidence'), # PSA 40:4
    ('trusts', 'hope'), # JN1 3:3
    ('trusts', 'relies'), # PRO 28:25
    ('trusts', 'believing'), # RV JHN 7:38
    ('trustworthy','faithful'),
    ('truth', 'faithfulness'), # DAN 9:13
    ('truth', 'truthful'), # EPH 4:15
    ('truthful', 'truth'), # ECC 12:10
    ('truthful', 'true'), # RV JHN 7:28
    ('truthfully', 'truth'), # ISA 59:4
    ('truthfulness', 'faithfulness'), # RV PSA 89:2 / LV PSA 89:3
    ('try', 'examine'), # PRO 23:30
    ('try', 'seek'), # ECC 8:17
    ('try', 'seeking'), # MAT 6:32
    ('try', 'sought'), # CH2 16:12
    ('trying','seeking'), # Mrk 14:55
    ('trying', 'sought'), # KI1 19:10
    ('Tsevoim', 'Tsəⱱoʼīm/Zeboiim'), # RV DEU 29:23 / LV DEU 29:22
    ('Tsivyah', 'Zibiah'), # RV KI2 12:1 / LV KI2 12:2
    ('Tsovah', 'Tsōⱱāh/Zobah'), # RV PSA 60:0 / LV PSA 60:1,PSA 60:2
    ('tumours', 'tumors'), # SA1 6:11
    ('turbans', 'caps'), # DAN 3:21
    ('turbans', 'headdresses'), # ISA 3:23
    ('turmoil', 'tumult'), # PSA 65:7
    ('turmoil', 'agitation'), # RV JOB 20:2
    ('Turn', 'return'), # PSA 6:4
    ('turn', 'becoming'), # JHN 16:20
    ('turn', 'changed'), # EXO 7:17
    ('turn', 'repentance', 'both'), # ACT 20:21
    ('turn', 'return'), # KI1 8:33
    ('turn', 'returned'), # PSA 18:37
    ('turn', 'become'), # RV MAT 4:3
    ('turned','giving'), # Mrk 13:9
    ('turned', 'became', 'both'), # GEN 19:26
    ('turned', 'become'), # ISA 1:22
    ('turned', 'bent'), # EZE 17:7
    ('turned', 'changed'), # EXO 7:20
    ('turned', 'returned'), # ECC 4:1
    ('turned', 'twisted'), # RUT 3:8
    ('turning', 'repentance'), # CO2 7:9
    ('turns', 'become'), # RV EXO 7:9
    ('turtledove', 'turtle-dove'), # GEN 15:9
    ('twenty','fifth'),
    ('twilight', 'evenings'), # EXO 29:39
    ('twisted', 'writhe'), # HAB 3:10
    ('twisting', 'perverting'), # RV ACT 13:10
    ('tying', 'binding'), # ACT 22:4
    ('tying', 'binds'), # RV PSA 129:7
    ('ulcers', 'ulcerated'), # LUK 16:20
    ('unbearably', 'unbearable'), # LUK 11:46
    ('uncertain', 'uncertainty'), # TI1 6:17
    ('unchanging', 'unchangeable'), # HEB 6:17
    ('uncircumcised', 'uncircumcision'), # ACT 11:3
    ('uncircumcision', 'uncircumcised'), # HAB 2:16
    ('unclean', 'uncleanness'), # LEV 7:20
    ('underclothes', 'undergarments'), # EZE 44:18
    ('underneath', 'beneath'), # DEU 33:27
    ('understand', 'know'),
    ('understand', 'hear'), # GEN 11:7
    ('understand', 'reading'), # LUK 10:26
    ('understanding', 'discernment'), # PRO 7:4
    ('understands', 'hearing'), # CO1 14:2
    ('understood', 'read'), # MAT 12:5
    ('underwear', 'undergarments'), # EXO 28:42
    ('undesirables','sinners'),
    ('undo', 'untie'), # ACT 13:25
    ('undone', 'untie/release'), # ISA 33:23
    ('unfaithful', 'unfaithfully'), # CH2 12:2
    ('unfaithful', 'unfaithfulness'), # CH2 29:19
    ('ungodly','unclean'),
    ('unimportant', 'insignificant'), # RV PSA 119:141
    ('uninhabited', 'desolate'), # MAT 23:38 (reviewed 2026-10-13)
    ('unintentionally', 'inadvertence'), # LEV 4:2
    ('united', 'joined'), # ROM 12:9
    ('unity', 'oneness'), # EPH 4:3
    ('unjust', 'unjustly'), # PE1 2:19
    ('unlace', 'untie'), # LUK 3:16
    ('unloaded', 'unharnessed'), # GEN 24:32
    ('unploughed', 'unplowed'), # JER 4:3
    ('unquenchable','inextinguishable'), # Mat 3:12
    ('unrighteous', 'unrighteousness'), # TH2 2:10
    ('untarnished','holy'),
    ('untarnished', 'holiness'), # CH1 16:10
    ('untie', 'untie/release'), # ISA 32:20
    ('untied', 'untie/release'), # GEN 49:21
    ('untied', 'unfastened'), # RV ACT 27:40
    ('until', 'till', 'aligned'),
    ('unto', 'to', 'aligned'),
    ('unwavering', 'steadfast'), # RV PSA 51:10 / LV PSA 51:12
    ('upon', 'on', 'aligned'),
    ('uprising', 'insurrection'), # RV LUK 23:19
    ('uproot', 'pluck'), # KI1 14:15
    ('uprooted', 'plucked'), # EZE 19:12
    ('upset','disturbed'), # Mat 2:3
    ('upstairs','housetop'), # Mrk 13:15
    ('upstairs','upper'), # Mrk 13:15
    ('upward', 'upwards'), # EZE 8:2
    ('upwards', 'upward'), # JHN 11:41
    ('urge', 'exhorting'), # ACT 27:34
    ('urged','implored'),
    ('urged', 'exhorting'), # CO1 16:12
    ('urged', 'incited'), # JDG 1:14
    ('urgent', 'urgently'), # NUM 22:37
    ('urging', 'exhorting'), # CO2 2:8
    ('useless', 'uselessly'), # MAT 15:9
    ('utensils', 'articles'), # EXO 31:9
    ('utensils', 'vessels', 'aligned'), # EXO 37:16
    ('valid', 'true'), # JHN 5:31 (reviewed 2026-10-13)
    ('valley', 'wadi'), # CH2 20:16
    ('valleys', 'valley[s]'), # NUM 14:25
    ('valleys', 'wadis'), # KI1 18:5
    ('valuable', 'desirable'), # CH2 36:19
    ('valuable', 'valuable[s]'), # JDG 18:21
    ('valued', 'treasured'), # JOB 23:12
    ('vegetable', 'vegetable[s]'), # KI1 21:2
    ('vegetables', 'vegetable[s]'), # PRO 15:17
    ('very','much'), # Mrk 12:27, 16:2
    ('very','exceedingly'), # Mrk 12:27, 16:2
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
    ('violence', 'strife'), # RV PSA 31:20 / LV PSA 31:21
    ('Violent', 'violence'), # PRO 16:29
    ('violent', 'violence'), # GEN 6:11
    ('violent', 'violences'), # PSA 140:4
    ('violent', 'violently'), # JER 22:3
    ('violently', 'violence'), # REV 18:21
    ('virgin', 'virgin[s]'), # JDG 21:12
    ('virgin', 'virginities'), # DEU 22:14
    ('visible', 'sight'), # RV DAN 4:20 / LV DAN 4:17
    ('visions', 'see'), # EZE 13:9
    ('visions', 'seen'), # EZE 13:6
    ('visiting', 'visitation'), # LUK 19:44
    ('visitors', 'visiting'), # ACT 2:10
    ('voice', 'sound'), # PSA 47:1
    ('voices', 'sound'), # RV KI2 7:10
    ('voluntarily', 'voluntary'), # CO2 8:3
    ('volunteered', 'voluntary'), # CO2 8:17
    ('wages', 'wage[s]'), # GEN 31:7
    ('wages', 'reward'), # RV ROM 4:4
    ('wailing', 'lamentation'), # RV ACT 8:2
    ('wailings', 'wail'), # AMO 8:3
    ('waist', 'hips'), # EXO 28:42
    ('waist', 'loins'), # DAN 10:5
    ('waistband', 'girdle'), # EXO 28:27
    ('waistband', 'sash'), # EXO 28:4
    ('waistbands', 'sashes'), # EXO 28:40
    ('waists', 'hips'), # EZE 23:15
    ('waists', 'loins'), # EZE 44:18
    ('wait', 'delaying'), # SA2 15:28
    ('wait', 'awaiting'), # RV ACT 1:4
    ('waited', 'rested'), # SA1 25:9
    ('waited', 'delay'), # RV JDG 19:8
    ('waiting', 'delayed'), # JDG 3:26
    ('waiting', 'awaiting'), # RV ACT 17:16
    ('waiting', 'expecting'), # RV PE2 3:12
    ('Wake', 'awake'), # PSA 7:6
    ('wake', 'awake'), # JER 51:57
    ('wake', 'awakened'), # KI2 4:31
    ('wake', 'rouse'), # GEN 49:9
    ('wake', 'awaken'), # RV JHN 11:11
    ('wake', 'awoke'), # RV PSA 139:18
    ('Wake', 'Awake'), # RV JOL 1:5
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
    ('wall', 'rampart'), # RV KI1 21:23
    ('wallet','purse'),
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
    ('want', 'desires'), # RV PSA 140:8 / LV PSA 140:9
    ('want', 'wishing'), # RV JDE 1:5
    ('wanted','wishing'),
    ('wanted', 'desire'), # CH2 9:12
    ('wanted', 'desired'), # DAN 7:19
    ('wanted', 'desiring'), # KI1 13:33
    ('wanted', 'seeking'), # JHN 19:12
    ('wanted', 'sought'), # ZEC 6:7
    ('wanting','seeking'), # Mat 2:20
    ('wanting', 'desires'), # RV SA2 3:21
    ('wants', 'wills'),
    ('wants', 'desired'), # PSA 132:13
    ('wants', 'desires'), # PRO 21:1
    ('wants', 'seek'), # CH2 30:19
    ('wants', 'seeking'), # SA1 20:1
    ('wants', 'seeks'), # PRO 15:14
    ('wants', 'desire'), # RV DEU 18:6
    ('wants', 'wishing'), # RV MAT 11:27
    ('war', 'fighting'), # SA1 28:15
    ('war', 'warfare'), # CO2 10:4
    ('warfare', 'war'), # RV KI1 5:3 / LV KI1 5:17
    ('warned','spoken'), # Mrk 13:23
    ('warned', 'instruct'), # ISA 8:11
    ('warned', 'instructed'), # PSA 2:10
    ('warned', 'protested'), # EXO 21:29
    ('warning', 'admonishing'), # ACT 20:31
    ('warnings', 'discipline'), # JOB 33:16
    ('warnings', 'admonition'), # RV TIT 3:10
    ('warrior', 'mighty'), # RV JER 9:23 / LV JER 9:22
    ('warriors','men'),
    ('warriors', 'mighty'), # SA2 1:22
    ('wash', 'washer'), # ISA 7:3
    ('washbasin', 'laver', 'aligned'), # EXO 30:18
    ('washed', 'bathed'), # SA2 12:20
    ('washed', 'washer'), # KI2 18:17
    ('waste', 'rot'), # EZE 4:17
    ('wasted', 'spoil'), # PRO 23:8
    ('wasteland', 'desolation'), # JOB 38:27
    ('wasteland', 'waste'), # JER 18:16
    ('wasteland', 'wastes'), # JER 51:26
    ('watch', 'looked'), # EXO 33:8
    ('watch', 'see'), # SA1 6:9
    ('Watch', 'See'), # RV HAB 1:5
    ('watch', 'seen'), # RV PSA 74:9
    ('watched', 'looked'), # REV 8:13
    ('watched', 'looking'), # JDG 13:19
    ('watched', 'observing'), # MRK 12:41
    ('watched', 'saw'), # SA1 6:16
    ('watched', 'seeing'), # RV ACT 8:6
    ('watchers', 'watchmen'), # JER 31:6
    ('watches', 'observing'), # JHN 6:40
    ('watchful', 'watching'), # MAT 25:13
    ('watching','observing'), # Mrk 15:47
    ('watching', 'looking'), # JDG 16:27
    ('wave', 'breakers'), # SA2 22:5
    ('wave', 'brandish'), # RV ISA 11:15
    ('way','how'),
    ('way', 'direction'), # JDG 9:37
    ('way', 'journey'), # EXO 18:8
    ('way', 'manner'), # SA2 15:6
    ('way', 'path'), # PSA 44:18
    ('way', 'paths'), # PRO 9:15
    ('ways', 'path'), # PSA 119:104
    ('ways', 'paths'), # RV PSA 17:4
    ('waywardness', 'apostasy'), # RV HOS 14:4 / LV HOS 14:5
    ('weak', 'feeble'), # NUM 13:18
    ('weak', 'poor'), # RV PSA 41:1 / LV PSA 41:2
    ('weakest', 'weak'), # JDG 6:15
    ('wealth', 'abundance'), # GEN 31:1
    ('wealth', 'opulence'), # JOB 36:19
    ('wealth', 'riches'), # LUK 8:14
    ('wealth', 'rich[es]'), # RV PSA 52:7 / LV PSA 52:9
    ("wealth's", 'riches'), # RV MAT 13:22
    ('wealthy','rich'),
    ('wealthy', 'wealth'), # CH2 17:5
    ('weapons', 'weapon[s]'), # CH2 32:5
    ('weapons', 'weaponry'), # EZE 39:9
    ('wear', 'bear'), # SA1 2:28
    ('wearing','clothed'), # Mrk 14:51
    ('wears', 'wearies'), # ECC 10:15
    ('weeds', 'grass'), # LUK 12:28
    ('weeds', 'plant'), # HOS 10:4
    ('weep', 'bewail'), # RV JER 9:1 / LV JER 8:23
    ('weigh', 'weight'), # CH1 22:14
    ('weighed', 'weight'), # CH1 20:2
    ('weighing', 'weight'), # JOS 7:21
    ('weighs', 'weight'), # PRO 27:3
    ('weight', 'weighed'), # JER 32:10
    ('weightier', 'heavier'), # MAT 23:23 (reviewed 2026-10-13)
    ('welcome', 'received'), # LUK 9:53
    ('We\'ll','We'),
    ('went','came', 'both'), # Mrk 16:5
    ('went','come'), # Mrk 16:5
    ('went', 'moved'), # EZE 10:22
    ('went', 'passed'), # EST 4:17
    ('went', 'passing'), # ACT 15:41
    ('went', 'proceeded'), # ACT 12:3
    ('went', 'walking'), # GEN 18:16
    ('went', 'belonged'), # RV CH1 5:2
    ('went', 'passes'), # RV JOS 18:19
    ('went', 'coming'), # RV SA2 19:41 / LV SA2 19:42
    ('west', 'westward'), # CH1 9:24
    ('western', 'westward'), # EZE 48:10
    ('We\'ve','We'),
    ('whacking','striking'), # Mrk 15:19
    ('what','whatever', 'both'),
    ("What's",'What'),
    ('wheels', 'wheel[s]'), # EXO 14:25
    ('When','And'),
    ('When','whenever'),
    ('when', 'whenever', 'aligned'),
    ('whenever', 'wherever', 'aligned'), # The OET-LV 'wherever' is a temporal 'whenever' in Mark 6:10, 6:56 and 9:18
    ('while', 'whilst', 'aligned'),
    ('whipped','beat'), # Mrk 13:9
    ('whirlwind', 'storm'), # ZEC 7:14
    ('whirlwind', 'storm-wind'), # HOS 8:7
    ('whirlwinds', 'storm-winds'), # ISA 21:1
    ('white', 'whitened'), # REV 7:14
    ('white', 'grey'), # RV JOB 41:32 / LV JOB 41:24
    ('who', 'whom', 'aligned'),
    ('whole','all'),
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
    ('wild', 'untamed'), # RV TI2 3:3
    ('wilderness', 'desolate'), # PSA 68:7
    ('wilderness', 'wildernesss'), # HEB 11:38
    ('will','are'),
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
    ('wishing','willing'), # Mat 1:19
    ('with','in/on/at/with'),
    ('withdraw', 'take'), # REV 6:4
    ('within', 'inner'), # HOS 5:4
    ('within', 'inward'), # GEN 25:23
    ('within', 'midst'), # RV ZEC 2:4 / LV ZEC 2:8
    ('without', 'outside', 'aligned'),
    ('witness', 'see'), # DEU 28:34
    ('witnessed', 'saw'), # LUK 5:26
    ('witnessed', 'seen'), # JHN 6:14
    ('woke', 'awaking'), # MRK 4:38
    ('woke', 'awoke'), # GEN 9:24
    ('woke', 'awoken'), # RV ACT 16:27
    ('woken', 'awakened'), # EZE 7:6
    ('woman', 'wife'), # GEN 25:1
    ('womb', 'belly'), # RV PSA 22:9 / LV PSA 22:10
    ('women','daughters'),
    ('women', 'wives'), # NEH 13:26
    ('wonderful', 'wonder[s]'), # PSA 88:12
    ('wonderful', 'wonders'), # CH1 16:9
    ('wondering', 'marvelling'), # LUK 1:21
    ('wonders', 'wonder[s]'), # PSA 88:10
    ("won't",'not'),
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
    ('words', 'voice'), # RV PSA 81:11 / LV PSA 81:12
    ('words', 'reproach'), # RV NEH 4:4 / LV NEH 3:36
    ('words', 'utterance'), # RV PSA 89:34 / LV PSA 89:35
    ('wore', 'clothing'), # RV PSA 35:13
    ('work','service'),
    ('work','labour'),
    ('work', 'deed[s]'), # RUT 2:12
    ('work', 'toil'), # ECC 2:24
    ('work', 'toils'), # PRO 16:26
    ('worked', 'served'), # RV HOS 12:12 / LV HOS 12:13
    ('worked', 'laboured'), # JHN 4:38 (reviewed 2026-10-13)
    ('workers', 'doers'), # RV KI2 12:15 / LV KI2 12:16
    ('workers', 'doer[s]'), # RV NEH 2:16
    ('working', 'toil'), # ECC 4:9
    ('working', 'labouring'), # CO1 4:12 (reviewed 2026-10-13)
    ('workmanship', 'work'), # RV MIC 5:13 / LV MIC 5:12
    ('world', 'earth'), # ACT 3:25
    ('world', 'earth/land'), # CH1 16:14
    ('world', 'creation'), # RV HEB 9:11
    ('worldly', 'world'), # CO1 7:34
    ("world's", 'earth'), # RV ISA 40:23
    ("world's", 'earth/land'), # RV EZE 39:18
    ('worms', 'maggot'), # JOB 21:26
    ('worn','girding'),
    ('worn', 'weary'), # JER 12:5
    ('worried','alarmed'), # Mrk 13:7
    ('worried', 'disturbed'), # MAT 14:26
    ('worship','bow'), # Mat 2:2
    ('worship','prostrate'), # Mat 2:2
    ('Worship', 'bow'), # CH1 16:29
    ('Worship', 'serve'), # EZE 20:39
    ('worship', 'bowed'), # SA2 15:32
    ('worship', 'homage'), # DAN 3:5
    ('worship', 'serve'), # EXO 10:7
    ('worship', 'serving'), # HEB 12:28
    ('worshipped','prostrated'), # Mat 2:11
    ('worshipped', 'bowed'), # JOB 1:20
    ('worshipped', 'served'), # CH2 24:18
    ('worshipping', 'bowing'), # EZE 8:16
    ('worth', 'price'), # PRO 31:10
    ('worth', 'valuation'), # JOB 28:13
    ('worth', 'worthy'), # LUK 7:4
    ('worthless', 'worthlessness'), # ISA 1:13
    ('worthy', 'worthily'), # PHP 1:27
    ('wounded', 'pain'), # CH1 10:3
    ('wounds', 'bruises'), # JOB 9:17
    ('wounds', 'sicknesses'), # CH2 24:25
    ('wounds', 'wound[s]'), # ISA 53:5
    ('Wounds', 'bruises'), # RV PRO 27:6
    ('wow','see'),
    ('wrapped', 'clothed'), # REV 10:1
    ('wrecked', 'broke'), # EZE 27:26
    ('writhes', 'anguish'), # ISA 13:8
    ('written','inscribed'), # Mrk 15:26
    ('wrong','strayed'), # Mrk 12:24,27, 15:14
    ('wrong','evil'), # Mrk 12:24,27, 15:14
    ('wrong', 'iniquity'), # DAN 9:5
    ('wrong', 'unrighteousness'), # JOB 34:10
    ('wrong', 'wicked'), # EXO 23:2
    ('wrong', 'wrongly'), # JAM 4:3
    ('wrong', 'amiss'), # RV LUK 23:41
    ('wrongdoing', 'mischief'), # HAB 1:13
    ('wronged', 'subverted'), # JOB 19:6
    ('Yacob', 'Yaˊₐqoⱱ/Jacob'), # RV GEN 32:18 / LV GEN 32:19
    ('Yahweh','master'),
    ('Yahweh','YHWH'),
    ('Yahweh\'s','YHWH'),
    ('Yakob', 'Yaˊₐqoⱱ/Jacob'), # RV PSA 22:23 / LV PSA 22:24
    ('year','year[s]'),
    ('years','year[s]'),
    ('yeast', 'leaven'), # CO1 5:6 (reviewed 2026-10-13)
    ('Yehoram', 'Yəhōrām/Jehoram'), # RV KI2 12:18 / LV KI2 12:19
    ('Yehozabad', 'Yəhōzāⱱād/Jehozabad'), # RV KI2 12:21 / LV KI2 12:22
    ('Yehudah', 'Yəhūdāh/Judah'), # RV JOL 3:8 / LV JOL 4:8
    ('Yehudah', 'Yəhūdāh/Yihudah'), # RV HOS 11:12 / LV HOS 12:1
    ('yelled','cried'),
    ('yelled', 'called', 'both'), # GEN 39:18
    ('yelled', 'crying'), # ACT 19:28
    ('yelled', 'shouted'), # SA1 25:14
    ('yelling', 'cried'), # MAT 14:26
    ('yelling', 'crying'), # ACT 19:32
    ('Yerushalem', 'Yərūshālam/Jerusalem'), # RV JOL 2:32 / LV JOL 3:5
    ('yielded', 'gives'), # PSA 67:6
    ('Yisrael','Yisrāʼēl/Israel'),
    ('Yitshak', 'Yiʦḩāq/Isaac'), # RV GEN 32:9 / LV GEN 32:10
    ('Yoav', 'Yōʼāⱱ/Joab'), # RV PSA 60:0 / LV PSA 60:1,PSA 60:2
    ('Yordan', 'Yardēn/Jordan'), # RV GEN 32:10 / LV GEN 32:11
    ('young','little'), # Mrk 15:40
    ('young', 'child'), # TI1 1:18
    ('young', 'fawn'), # SNG 2:9
    ('young', 'son'), # DAN 3:25
    ('young', 'sons'), # SNG 2:3
    ('young', 'younger'), # ACT 5:6
    ('young', 'youth'), # DEU 28:50
    ('young', 'youths'), # EZE 23:8
    ('younger','lower'), # Mat 2:16
    ('younger', 'young'), # EZE 16:46
    ('youngest', 'young'), # CH2 21:17
    ('youngest', 'younger'), # LUK 22:26
    ('yourselves','hearts'),
    ('youthful', 'youths'), # JER 31:19
    ('zebedaios', 'zebedee', 'aligned'),
)

# Derived lookups for the two matching passes; do not maintain entries here.
# Add only the listed positional pairs and their reverses, never transitive pairs.
EQUIVALENT_LV_RV_WORDS = {}
_uniqueWordPairs = []
_seenWordPairs = set()
_seenAlignedPairs = set()
for mapping in SINGLE_WORD_MAPPINGS:
    assert isinstance(mapping, tuple) and len(mapping) in (2, 3), f'{mapping=}'
    rvWord, lvWord = mapping[:2]
    mode = mapping[2] if len(mapping) == 3 else 'unique'
    assert mode in ('unique', 'aligned', 'both'), f'Unknown matching mode: {mapping}'
    assert len(rvWord.split()) == len(lvWord.split()) == 1, f'Expected single words: {mapping}'
    assert '_' not in rvWord+lvWord, f'Unexpected phrase separator: {mapping}'
    assert rvWord.lower() != lvWord.lower(), f'Redundant identity mapping: {mapping}'
    assert (rvWord, lvWord) not in _seenWordPairs, f'Duplicate mapping: {mapping}'
    _seenWordPairs.add((rvWord, lvWord))
    for verbSet in SIMPLE_VERB_SETS:
        if lvWord.lower() in verbSet:
            assert rvWord.lower() not in verbSet, f'Already covered by verb forms: {mapping}'
    if mode in ('aligned', 'both'):
        for word in (rvWord, lvWord):
            assert word == word.lower() and not any(c in word for c in ' _=÷'), f'Expected a lower-case single word: {word}'
        pair = frozenset((rvWord, lvWord))
        assert pair not in _seenAlignedPairs, f'Duplicate bidirectional mapping: {mapping}'
        _seenAlignedPairs.add(pair)
        EQUIVALENT_LV_RV_WORDS.setdefault(rvWord, set()).add(lvWord)
        EQUIVALENT_LV_RV_WORDS.setdefault(lvWord, set()).add(rvWord)
    if mode in ('unique', 'both'):
        _uniqueWordPairs.append((rvWord, lvWord))
RV_SINGLE_WORDS_FROM_LV_WORDS = tuple(_uniqueWordPairs)
