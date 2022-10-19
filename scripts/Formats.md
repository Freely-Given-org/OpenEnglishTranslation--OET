# Format summaries

## Old Testament

### OSHB TSV

../sourceTexts/rawOSHB/OSHB.original.flat.morphemes.tsv

Nine columns:

- FGGID: OSHB 10-digit bbcccvvvww id plus our a/b/c/d/e suffix
- Ref: Our ref, e.g., GEN_1_1_w1a
- Type: m, w, seg, note (morpheme, word, segment/punctuation, note)
- Special: K for Ketiv
- Strongs: e.g., 8064 or b
- CantillationHierarchy: e.g., 1.1.1 (or note type)
- Morphology: e.g., HVqp3ms (or segment type)
- OSHBid: e.g., 01xeNab (includes our suffix for morphemes, none for segs or notes)
- WordOrMorpheme: (Hebrew text) or note text or segment punctuation

### Clear.Bible low fat tree TSV

../intermediateTexts/Clear.Bible_lowfat_trees/ClearLowFatTrees.OT.morphemes.tsv

Created from Clear.Bible Macula Hebrew low fat trees XML files.

Thirty-two columns:

- FGRef: Our ref, e.g., GEN_1_1_w1a
- OSHBid: e.g., 01xeNab (includes our suffix for morphemes)
- Type: m (morpheme) or M (final morpheme) or w (word)
- LFRef: Their reference, e.g., GEN 1:1!1 (repeated for each morpheme)
- LFNumRef: Their 12-digit bbcccvvvwwwm reference, e.g., 010010010011 (repeated for each morpheme)
- Language: H or A
- WordOrMorpheme: Hebrew
- Unicode: Hebrew???
- Transliteration:
- After: space or punctuation to go after word
- StrongNumberX:
- StrongLemma:
- Stem:
- Morphology:
- Lemma:
- LexicalDomain:
- SenseNumber:
- WordClass:
- PartOfSpeech:
- Person:
- Gender:
- Number:
- WordType:
- State:
- Domain:
- SDBH:
- Greek:
- GreekStrong:
- EnglishGloss: Cherith English gloss
- MandarinGloss: Cherith Mandarin gloss
- ContextualGloss:
- Nesting: flattened role/tree structure below sentence, e.g., pp-v-s-o/o=npanp/ompnp/detnp

### Abbreviated Clear.Bible low fat tree TSV

../intermediateTexts/Clear.Bible_lowfat_trees/ClearLowFatTreesAbbrev.OT.morphemes.tsv

Created from Clear.Bible Macula Hebrew low fat trees XML files.

We shorten some of the fields,
e.g., WordType field 'direct object marker' to 'DOM' and PartOfSpeech 'noun' to 'n',
and drop some other fields completely to make the TSV file that we use smaller.

Twenty-five columns:

- FGRef: Our ref, e.g., GEN_1_1_w1a
- OSHBid: e.g., 01xeNab (includes our suffix for morphemes)
- Type: m (morpheme) or M (final morpheme) or w (word)
- WordOrMorpheme: Hebrew word or morpheme
- After: space or punctuation to go after word
- StrongNumberX:
- StrongLemma:
- Stem:
- Morphology:
- Lemma:
- LexicalDomain:
- SenseNumber:
- WordClass:
- PartOfSpeech:
- Person:
- Gender:
- Number:
- WordType:
- State:
- Domain:
- Greek:
- GreekStrong:
- EnglishGloss:
- ContextualGloss:
- Nesting: flattened role/tree structure below sentence, e.g., pp-v-s-o/o=npanp/ompnp/detnp

### Glossed OSHB TSV

./intermediateTexts/glossed_OSHB/WLC_glosses.morphemes.tsv

Sixteen columns:

- Ref: Our ref, e.g., GEN_1_1_w1a
- OSHBid: e.g., 01xeNab (includes our suffix for morphemes, none for segs or notes)
- Type: m (morpheme) or M (final morpheme) or w (word), A prefix for Aramaic, K suffix for Ketiv
- Strongs: e.g., 8064 or b
- CantillationHierarchy: e.g., 1.1.1 (or note type)
- Morphology: e.g., HVqp3ms (or segment type)
- WordOrMorpheme: (Hebrew text) or note text or segment punctuation
- NoCantillations: Hebrew text with cantillation marks removed
- MorphemeGloss: for m or M types
- ContextualMorphemeGloss: for m or M types
- WordGloss: for w types
- ContextualWordGloss: for M or W types
- GlossCapitalisation: S for start of sentence
- GlossPunctuation: post-punctuation (but not spaces)
- GlossOrder: number giving relative order for English glosses (but not used here yet)
- GlossInsert (not used yet)

## New Testament

### Book table

Book table: book.csv

../../CNTR-GNT/sourceExports/book.csv

Six columns:

- BookID: 1..66
- Testament: O or N
- Title: Hebrew or Greek title
- eTitle: English title
- eAbbreviation: English abbreviation, e.g., "Is."
- eAuthor English author name, e.g., "Moses", "Solomon, et. al.", "Unknown"

### Word table

Collation table: collation.csv

../../CNTR-GNT/sourceExports/collation.updated.csv

Includes rows for all variants.

Thirty-five columns:

- CollationID: CNTR 11-digit bbcccvvvwww id
- Variant:
- VariantI:
- Dependence:
- VariantType:
- Align:
- Span:
- Incomplete:
- Classic:
- Koine:
- Medieval:
- Probability:
- Historical:
- Capitalization: codes for capitalising Greek words
- Punctuation: combined pre-word and post-word punctuation characters
- Role:
- Syntax:
- Morphology:
- Sic:
- Lemma:
- LexemeID:
- Sense:
- GlossPre: English helper words
- GlossHelper: English helper words like "was"
- GlossWord: main English gloss
- GlossPost: e.g., elided words
- GlossPunctuation:
- GlossCapitalization: codes for capitalising gloss words
- GlossOrder:
- GlossInsert: single-character code
- Reference:
- Notes:
- If:
- Then:
- VerseID: 8-digit verse bbcccvvv ID (same as start of CollationID)
