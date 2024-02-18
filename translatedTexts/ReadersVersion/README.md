# Open English Translation Readers’ Version (OET-RV)

## Introduction

The OET Reader’s Version is manually translated from the OET Literal Version
which is a word-for-word translation of the original Hebrew and Greek
where the words have been minimally reordered to make sense in English.

This translation methodolgy is based on the idea that it’s easier
to try to focus on creating a draft that’s natural English
and then to fix accuracy and consistency issues later, rather than the opposite.
There are so many Bible translations in the world,
including in English,
where the grammar and expressions of the translation are much more like Hebrew or Greek styles than being natural in the language that they’re being translated into.
For instance in modern English, it's far more natural to say
‘God's kingdom’ than ‘kingdom of God’.

Currently (February 2024), over 90% of the ‘New Testament’ has been rough-drafted.

## TODO list

- Replace "whoever" with anyone
- Manually mark nomina sacra in OET-RV???
- Do a spell-check
- Consider replacing J with Y, e.g., Jacob -> Yacob, John -> Yohan
- Consider changing names still quite recognisable with only one letter difference, e.g., Lazarus -> Lazaros
- Choose one of ‘apprentices’ or ‘trainees’
- Check consistency of keyterms, e.g., how is ‘son of God’, ‘holy spirit’, ‘kingdom of the heavens’ translated everywhere?
- Compare parallel passages and choose the best renderings
- Define and check style of s1 section headings, i.e., tense, perfects, etc.
- Add "alternative" section headings for searches, e.g., \rem s1 Alternative heading
- Define and implement ‘add’ classes or probabilities (more/less certain)
- Define and implement footnote classes
- Add word numbers for all remaining OET-RV words
- Add importance index 1..5 for each verse

### ‘Add’ classes

We use USFM \add markers but need to differentiate further—probably by using an additional symbol inside the marked-up text (similarly to what we do for the OET-LV). Some possibilities are:

- cultural additions, e.g., \add Roman\add* soldier
- contextual additions, e.g., and \add after that\add* he said
- application/interpretational additions, e.g., when we reword the concept to what we think the author was trying to say, but the final words that we use are not there at all in the original.
