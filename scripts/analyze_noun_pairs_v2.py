#!/usr/bin/env python3
"""
Analyze OET-RV and OET-LV word tables to find noun pairs that occur in both
singular and plural forms in either translation.
Uses the word tables which have proper morphology/part-of-speech tagging.
"""
import re
from pathlib import Path
from collections import Counter, defaultdict

# Word table paths
NT_WORD_TABLE = Path("/srv/FreelyGiven/OpenEnglishTranslation--OET/derivedTexts/auto_edited_VLT_ESFM/OET-LV_NT_word_table.tsv")
OT_WORD_TABLE = Path("/srv/FreelyGiven/OpenEnglishTranslation--OET/derivedTexts/auto_edited_OT_ESFM/OET-LV_OT_word_table.tsv")

# OET-RV ESFM files
OET_RV_FOLDER = Path("/srv/FreelyGiven/OpenEnglishTranslation--OET/translatedTexts/ReadersVersion")

def parse_nt_word_table(filepath):
    """Parse NT word table, return dict of full native reference -> (gloss, role, morphology)"""
    words = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        header = f.readline().strip().split('\t')
        gloss_idx = header.index('OETGlossWords')
        role_idx = header.index('Role')
        morph_idx = header.index('Morphology')

        for line in f:
            parts = line.strip().split('\t')
            if len(parts) <= max(gloss_idx, role_idx, morph_idx):
                continue
            gloss = parts[gloss_idx].strip()
            role = parts[role_idx].strip()
            morph = parts[morph_idx].strip()

            # 2026-10-22: wN restarts every verse; retain the full native reference.
            ref = parts[0].strip()
            match = re.search(r'w(\d+)$', ref)
            if match:
                if ref in words:
                    raise ValueError(f'Duplicate native word reference {ref} in {filepath}')
                words[ref] = (gloss, role, morph)
    return words

def parse_ot_word_table(filepath):
    """Parse OT word table, return dict of full native reference -> (gloss, role, morphology)"""
    words = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        header = f.readline().strip().split('\t')
        gloss_idx = header.index('ContextualWordGloss')
        role_idx = header.index('Role')
        morph_idx = header.index('Morphology')

        for line in f:
            parts = line.strip().split('\t')
            if len(parts) <= max(gloss_idx, role_idx, morph_idx):
                continue
            gloss = parts[gloss_idx].strip()
            role = parts[role_idx].strip()
            morph = parts[morph_idx].strip()

            # 2026-10-22: wN restarts every verse; retain the full native reference.
            ref = parts[0].strip()
            match = re.search(r'w(\d+)$', ref)
            if match:
                if ref in words:
                    raise ValueError(f'Duplicate native word reference {ref} in {filepath}')
                words[ref] = (gloss, role, morph)
    return words

def is_noun_nt(role, morph):
    """Check if NT word is a noun."""
    return role == 'N' or morph.startswith('N')

def is_noun_ot(role, morph):
    """Check if OT word is a noun."""
    # OT morphology codes: Ncfsa, Ncmpa, Ncmsa, Ncbsa, Ncbpc, etc.
    # N = noun, c = common, f/m/b = feminine/masculine/both, s/p = singular/plural
    return role in ('S', 'O', 'P') and morph.startswith('N')

def extract_noun_number_from_morph(morph):
    """Extract number (singular/plural) from morphology code."""
    # NT: NFS, NMS, NFP, NMP, etc.
    # OT: Ncfsa, Ncmpa, Ncmsa, Ncbsa, Ncbpc, etc.
    if 'P' in morph and 'S' not in morph.split('P')[0]:
        return 'plural'
    if 'S' in morph or 's' in morph:
        return 'singular'
    return 'unknown'

def get_english_nouns_from_word_table(words_dict, is_nt=True):
    """Extract English nouns with their numbers from word table."""
    nouns = defaultdict(lambda: {'singular': set(), 'plural': set()})

    for word_num, (gloss, role, morph) in words_dict.items():
        if is_nt:
            if not is_noun_nt(role, morph):
                continue
            number = extract_noun_number_from_morph(morph)
        else:
            if not is_noun_ot(role, morph):
                continue
            number = extract_noun_number_from_morph(morph)

        # Clean gloss - remove markup
        clean_gloss = re.sub(r'[¦_˱˲/\\]', ' ', gloss)
        clean_gloss = re.sub(r'\b(the|a|an|of|in|for|to|from|with|by|on|at)\b', '', clean_gloss)
        clean_gloss = re.sub(r'\s+', ' ', clean_gloss).strip()

        # Skip if gloss is empty or just punctuation/markers
        if not clean_gloss or clean_gloss in ('', 'the', 'a', 'an'):
            continue

        # Get the base word (last word in gloss typically)
        gloss_words = clean_gloss.split()
        if not gloss_words:
            continue
        base_word = gloss_words[-1].lower().strip("'\".,;:!?()[]{}")

        if not base_word or len(base_word) < 2:
            continue

        if number == 'singular':
            nouns[base_word]['singular'].add(base_word)
        elif number == 'plural':
            nouns[base_word]['plural'].add(base_word)

    return nouns

def extract_rv_nouns():
    """Extract nouns from OET-RV ESFM files."""
    rv_nouns = Counter()
    word_pattern = re.compile(r'\b([A-Za-z][A-Za-z\-\']*)¦\d+\b')

    for filepath in OET_RV_FOLDER.glob("*.ESFM"):
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip().startswith('\\v '):
                    continue
                # Extract words with numbers
                matches = word_pattern.findall(line)
                for word in matches:
                    rv_nouns[word.lower()] += 1
    return rv_nouns

def get_singular(plural):
    """Get the singular form of a plural noun."""
    plural = plural.lower()

    # Irregular plurals
    irregular = {
        'men': 'man', 'women': 'woman', 'children': 'child', 'people': 'person',
        'feet': 'foot', 'teeth': 'tooth', 'geese': 'goose', 'mice': 'mouse',
        'lice': 'louse', 'oxen': 'ox', 'brethren': 'brother',
        'sheep': 'sheep', 'deer': 'deer', 'fish': 'fish', 'species': 'species',
        'offspring': 'offspring', 'aircraft': 'aircraft', 'craft': 'craft',
        'brothers': 'brother', 'sisters': 'sister', 'fathers': 'father',
        'mothers': 'mother', 'daughters': 'daughter', 'sons': 'son',
        'husbands': 'husband', 'wives': 'wife', 'widows': 'widow',
        'angels': 'angel', 'demons': 'demon', 'spirits': 'spirit',
        'disciples': 'disciple', 'apostles': 'apostle', 'prophets': 'prophet',
        'priests': 'priest', 'kings': 'king', 'queens': 'queen',
        'cities': 'city', 'towns': 'town', 'villages': 'village',
        'houses': 'house', 'homes': 'home', 'temples': 'temple',
        'synagogues': 'synagogue', 'churches': 'church',
        'nations': 'nation', 'peoples': 'people', 'tribes': 'tribe',
        'families': 'family', 'children': 'child',
        'years': 'year', 'days': 'day', 'months': 'month', 'weeks': 'week',
        'hours': 'hour', 'minutes': 'minute', 'seconds': 'second',
        'hands': 'hand', 'feet': 'foot', 'eyes': 'eye', 'ears': 'ear',
        'mouths': 'mouth', 'hearts': 'heart', 'minds': 'mind',
        'heads': 'head', 'faces': 'face', 'voices': 'voice',
        'words': 'word', 'names': 'name', 'books': 'book',
        'laws': 'law', 'commands': 'command', 'rules': 'rule',
        'signs': 'sign', 'wonders': 'wonder', 'miracles': 'miracle',
        'gifts': 'gift', 'blessings': 'blessing', 'curses': 'curse',
        'prayers': 'prayer', 'songs': 'song', 'psalms': 'psalm',
        'covenants': 'covenant', 'promises': 'promise', 'vows': 'vow',
        'offerings': 'offering', 'sacrifices': 'sacrifice',
        'altars': 'altar', 'sanctuaries': 'sanctuary', 'tabernacles': 'tabernacle',
        'courts': 'court', 'gates': 'gate', 'doors': 'door', 'walls': 'wall',
        'towers': 'tower', 'pillars': 'pillar', 'stones': 'stone',
        'trees': 'tree', 'fruits': 'fruit', 'seeds': 'seed',
        'grains': 'grain', 'breads': 'bread', 'loaves': 'loaf',
        'fishes': 'fish', 'birds': 'bird', 'beasts': 'beast',
        'cattle': 'cattle', 'sheep': 'sheep', 'goats': 'goat',
        'oxen': 'ox', 'donkeys': 'donkey', 'camels': 'camel',
        'horses': 'horse', 'mules': 'mule', 'chariots': 'chariot',
        'ships': 'ship', 'boats': 'boat', 'nets': 'net',
        'swords': 'sword', 'spears': 'spear', 'shields': 'shield',
        'armies': 'army', 'soldiers': 'soldier', 'warriors': 'warrior',
        'captains': 'captain', 'commanders': 'commander', 'officers': 'officer',
        'guards': 'guard', 'watchmen': 'watchman', 'gatekeepers': 'gatekeeper',
        'servants': 'servant', 'slaves': 'slave', 'masters': 'master',
        'lords': 'lord', 'ladies': 'lady', 'princes': 'prince',
        'princesses': 'princess', 'officials': 'official', 'rulers': 'ruler',
        'judges': 'judge', 'elders': 'elder', 'leaders': 'leader',
        'teachers': 'teacher', 'scribes': 'scribe', 'lawyers': 'lawyer',
        'doctors': 'doctor', 'healers': 'healer', 'physicians': 'physician',
        'shepherds': 'shepherd', 'farmers': 'farmer', 'fishers': 'fisher',
        'builders': 'builder', 'craftsmen': 'craftsman', 'workers': 'worker',
        'merchants': 'merchant', 'traders': 'trader', 'buyers': 'buyer',
        'sellers': 'seller', 'rich': 'rich', 'poor': 'poor',
        'widows': 'widow', 'orphans': 'orphan', 'strangers': 'stranger',
        'foreigners': 'foreigner', 'aliens': 'alien', 'sojourners': 'sojourner',
        'enemies': 'enemy', 'friends': 'friend', 'neighbors': 'neighbour',
        'brothers': 'brother', 'sisters': 'sister', 'relatives': 'relative',
        'ancestors': 'ancestor', 'descendants': 'descendant', 'generations': 'generation',
        'fathers': 'father', 'mothers': 'mother', 'parents': 'parent',
        'sons': 'son', 'daughters': 'daughter', 'children': 'child',
        'wives': 'wife', 'husbands': 'husband', 'spouses': 'spouse',
    }
    if plural in irregular:
        return irregular[plural]

    # Regular patterns
    if plural.endswith('ies') and len(plural) > 3:
        return plural[:-3] + 'y'
    elif plural.endswith('es') and len(plural) > 2:
        if plural.endswith(('ches', 'shes', 'xes', 'zes', 'ses')):
            return plural[:-2]
        elif plural.endswith('oes'):
            return plural[:-2]
        else:
            return plural[:-1]
    elif plural.endswith('s') and len(plural) > 1 and not plural.endswith('ss'):
        return plural[:-1]

    return None

def get_plural(singular):
    """Get the plural form of a singular noun."""
    singular = singular.lower()

    # Irregular plurals
    irregular = {
        'man': 'men', 'woman': 'women', 'child': 'children', 'person': 'people',
        'foot': 'feet', 'tooth': 'teeth', 'goose': 'geese', 'mouse': 'mice',
        'louse': 'lice', 'ox': 'oxen', 'brother': 'brethren',
        'sheep': 'sheep', 'deer': 'deer', 'fish': 'fish', 'species': 'species',
        'offspring': 'offspring', 'aircraft': 'aircraft', 'craft': 'craft',
        'brother': 'brothers', 'sister': 'sisters', 'father': 'fathers',
        'mother': 'mothers', 'daughter': 'daughters', 'son': 'sons',
        'husband': 'husbands', 'wife': 'wives', 'widow': 'widows',
        'angel': 'angels', 'demon': 'demons', 'spirit': 'spirits',
        'disciple': 'disciples', 'apostle': 'apostles', 'prophet': 'prophets',
        'priest': 'priests', 'king': 'kings', 'queen': 'queens',
        'city': 'cities', 'town': 'towns', 'village': 'villages',
        'house': 'houses', 'home': 'homes', 'temple': 'temples',
        'synagogue': 'synagogues', 'church': 'churches',
        'nation': 'nations', 'people': 'peoples', 'tribe': 'tribes',
        'family': 'families',
        'year': 'years', 'day': 'days', 'month': 'months', 'week': 'weeks',
        'hour': 'hours', 'minute': 'minutes', 'second': 'seconds',
        'hand': 'hands', 'eye': 'eyes', 'ear': 'ears',
        'mouth': 'mouths', 'heart': 'hearts', 'mind': 'minds',
        'head': 'heads', 'face': 'faces', 'voice': 'voices',
        'word': 'words', 'name': 'names', 'book': 'books',
        'law': 'laws', 'command': 'commands', 'rule': 'rules',
        'sign': 'signs', 'wonder': 'wonders', 'miracle': 'miracles',
        'gift': 'gifts', 'blessing': 'blessings', 'curse': 'curses',
        'prayer': 'prayers', 'song': 'songs', 'psalm': 'psalms',
        'covenant': 'covenants', 'promise': 'promises', 'vow': 'vows',
        'offering': 'offerings', 'sacrifice': 'sacrifices',
        'altar': 'altars', 'sanctuary': 'sanctuaries', 'tabernacle': 'tabernacles',
        'court': 'courts', 'gate': 'gates', 'door': 'doors', 'wall': 'walls',
        'tower': 'towers', 'pillar': 'pillars', 'stone': 'stones',
        'tree': 'trees', 'fruit': 'fruits', 'seed': 'seeds',
        'grain': 'grains', 'loaf': 'loaves',
        'bird': 'birds', 'beast': 'beasts',
        'goat': 'goats', 'donkey': 'donkeys', 'camel': 'camels',
        'horse': 'horses', 'mule': 'mules', 'chariot': 'chariots',
        'ship': 'ships', 'boat': 'boats', 'net': 'nets',
        'sword': 'swords', 'spear': 'spears', 'shield': 'shields',
        'army': 'armies', 'soldier': 'soldiers', 'warrior': 'warriors',
        'captain': 'captains', 'commander': 'commanders', 'officer': 'officers',
        'guard': 'guards', 'watchman': 'watchmen', 'gatekeeper': 'gatekeepers',
        'servant': 'servants', 'slave': 'slaves', 'master': 'masters',
        'lord': 'lords', 'lady': 'ladies', 'prince': 'princes',
        'princess': 'princesses', 'official': 'officials', 'ruler': 'rulers',
        'judge': 'judges', 'elder': 'elders', 'leader': 'leaders',
        'teacher': 'teachers', 'scribe': 'scribes', 'lawyer': 'lawyers',
        'doctor': 'doctors', 'healer': 'healers', 'physician': 'physicians',
        'shepherd': 'shepherds', 'farmer': 'farmers', 'fisher': 'fishers',
        'builder': 'builders', 'craftsman': 'craftsmen', 'worker': 'workers',
        'merchant': 'merchants', 'trader': 'traders', 'buyer': 'buyers',
        'seller': 'sellers', 'widow': 'widows', 'orphan': 'orphans',
        'stranger': 'strangers', 'foreigner': 'foreigners', 'alien': 'aliens',
        'sojourner': 'sojourners', 'enemy': 'enemies', 'friend': 'friends',
        'neighbour': 'neighbours', 'relative': 'relatives',
        'ancestor': 'ancestors', 'descendant': 'descendants', 'generation': 'generations',
        'parent': 'parents', 'spouse': 'spouses',
    }
    if singular in irregular:
        return irregular[singular]

    # Regular patterns
    if singular.endswith('y') and len(singular) > 1 and singular[-2] not in 'aeiou':
        return singular[:-1] + 'ies'
    elif singular.endswith(('ch', 'sh', 's', 'x', 'z')):
        return singular + 'es'
    elif singular.endswith('o') and len(singular) > 1:
        return singular + 'es'
    else:
        return singular + 's'

def main():
    print("Parsing NT word table...")
    nt_words = parse_nt_word_table(NT_WORD_TABLE)
    print(f"  Found {len(nt_words)} NT words")

    print("Parsing OT word table...")
    ot_words = parse_ot_word_table(OT_WORD_TABLE)
    print(f"  Found {len(ot_words)} OT words")

    print("Extracting nouns from word tables...")
    nt_nouns = get_english_nouns_from_word_table(nt_words, is_nt=True)
    ot_nouns = get_english_nouns_from_word_table(ot_words, is_nt=False)

    # Combine LV nouns
    lv_nouns = defaultdict(lambda: {'singular': set(), 'plural': set()})
    for word, forms in nt_nouns.items():
        lv_nouns[word]['singular'].update(forms['singular'])
        lv_nouns[word]['plural'].update(forms['plural'])
    for word, forms in ot_nouns.items():
        lv_nouns[word]['singular'].update(forms['singular'])
        lv_nouns[word]['plural'].update(forms['plural'])

    print(f"  Found {len(lv_nouns)} unique LV noun bases")

    print("Extracting nouns from OET-RV...")
    rv_nouns = extract_rv_nouns()
    print(f"  Found {len(rv_nouns)} unique RV words with numbers")

    # Find pairs in LV
    lv_pairs = set()
    for base, forms in lv_nouns.items():
        for sing in forms['singular']:
            for plur in forms['plural']:
                if sing != plur:
                    lv_pairs.add((sing, plur))

    # Also check for base words that have both singular and plural in their forms
    for base in lv_nouns:
        singulars = lv_nouns[base]['singular']
        plurals = lv_nouns[base]['plural']
        for s in singulars:
            for p in plurals:
                lv_pairs.add((s, p))

    # Find pairs in RV
    rv_pairs = set()
    rv_words_set = set(rv_nouns.keys())
    for word in rv_words_set:
        singular = get_singular(word)
        if singular and singular in rv_words_set:
            rv_pairs.add((singular, word))
        plural = get_plural(word)
        if plural and plural in rv_words_set:
            rv_pairs.add((word, plural))

    # Combine pairs from both translations
    all_pairs = lv_pairs | rv_pairs

    # Filter to only include pairs where both forms are reasonably common nouns
    # and not proper nouns (capitalized)
    filtered_pairs = []
    for sing, plur in all_pairs:
        if sing[0].isupper() or plur[0].isupper():
            continue
        # Skip very short words
        if len(sing) < 2 or len(plur) < 2:
            continue
        filtered_pairs.append((sing, plur))

    # Sort alphabetically by singular form
    sorted_pairs = sorted(set(filtered_pairs), key=lambda x: x[0])

    print(f"\nFound {len(sorted_pairs)} noun pairs (singular, plural):")
    for singular, plural in sorted_pairs:
        print(f"    ('{plural}', '{singular}'),")

    return sorted_pairs

if __name__ == '__main__':
    main()
