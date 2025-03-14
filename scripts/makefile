# OET makefile
#
# Last updated: 2025-03-08 by RJH
#

#=== Folder and file declarations =======================

# LV_HTML := $(wildcard ../derivedTexts/simpleHTML/LiteralVersion/*.html)
derived_VREFs := ../derivedTexts/OET-RV.vref.txt ../derivedTexts/OET-LV.vref.txt
derived_USFM := $(wildcard ../derivedTexts/cleanedUSFM/ReadersVersion/*.USFM) $(wildcard ../derivedTexts/cleanedUSFM/LiteralVersion/*.USFM)
sideBySide_HTML := $(wildcard ../derivedTexts/simpleHTML/SideBySide/???.html)
LV_OT_HTML := ../derivedTexts/simpleHTML/LiteralVersion/GEN.html ../derivedTexts/simpleHTML/LiteralVersion/MAL.html
LV_NT_HTML := ../derivedTexts/simpleHTML/LiteralVersion/MAT.html ../derivedTexts/simpleHTML/LiteralVersion/REV.html
RV_HTML := $(wildcard ../derivedTexts/simpleHTML/ReadersVersion/*.html)
RV_ESFM := $(wildcard ../translatedTexts/ReadersVersion/*.ESFM)
# final_LV_OT_USFM := $(wildcard ../intermediateTexts/auto_edited_OT_USFM/*.usfm)
final_LV_OT_ESFM := $(wildcard ../intermediateTexts/auto_edited_OT_ESFM/*.ESFM)
final_LV_NT_ESFM := $(wildcard ../intermediateTexts/auto_edited_VLT_ESFM/OET-LV_???.ESFM)
LV_ESFM := $(final_LV_OT_ESFM) $(final_LV_NT_ESFM)
# intermediate_LV_OT_USFM := $(wildcard ../intermediateTexts/modified_source_glossed_OSHB_USFM/*.usfm)
intermediate_LV_OT_ESFM := $(wildcard ../intermediateTexts/modified_source_glossed_OSHB_ESFM/???_gloss.ESFM)
intermediate_LV_NT_ESFM := $(wildcard ../intermediateTexts/modified_source_VLT_ESFM/???_gloss.ESFM)
final_RV_OT_word_tables = ../translatedTexts/ReadersVersion/OET-LV_OT_morpheme_table.tsv ../translatedTexts/ReadersVersion/OET-LV_OT_lemma_table.tsv
final_LV_OT_word_tables = ../intermediateTexts/auto_edited_OT_ESFM/OET-LV_OT_word_table.tsv ../intermediateTexts/auto_edited_OT_ESFM/OET-LV_OT_morpheme_table.tsv ../intermediateTexts/auto_edited_OT_ESFM/OET-LV_OT_lemma_table.tsv
expanded_OT_TSV_tables := ../intermediateTexts/modified_source_glossed_OSHB_ESFM/OET-LV_OT_word_table.tsv ../intermediateTexts/modified_source_glossed_OSHB_ESFM/OET-LV_OT_morpheme_table.tsv ../intermediateTexts/modified_source_glossed_OSHB_ESFM/OET-LV_OT_lemma_table.tsv
initial_OT_TSV_tables := ../intermediateTexts/glossed_OSHB/all_glosses.words.tsv ../intermediateTexts/glossed_OSHB/all_glosses.morphemes.tsv ../intermediateTexts/glossed_OSHB/all_glosses.lemmas.tsv
expanded_NT_wordtable = ../intermediateTexts/modified_source_VLT_ESFM/OET-LV_NT_word_table.tsv
original_NT_wordtable = ../intermediateTexts/modified_source_VLT_ESFM/OET-LV_NT_word_table.10columns.tsv
CNTR_lemma_table = ../../CNTR-GNT/derivedFormats/lemmas.alphabetical.tsv
CNTR_book_table = ../../CNTR-GNT/sourceExports/book.csv
CNTR_collation_table = ../../CNTR-GNT/sourceExports/collation.csv
WLC_OT_TSV_table := ../intermediateTexts/glossed_OSHB/our_WLC_glosses.morphemes.tsv
Clear_Bible_MaculaHebrew_OT_TSV := ../intermediateTexts/Clear.Bible_derived_Macula_data/Clear.Bible_MaculaHebrew.OT.morphemes.abbrev.tsv ../intermediateTexts/Clear.Bible_derived_Macula_data/Clear.Bible_MaculaHebrew.OT.lemmas.tsv
Clear_Bible_NT_lowfat_TSV := ../intermediateTexts/Clear.Bible_derived_Macula_data/Clear.Bible_MaculaGreek_LowFatTrees.NT.words.abbrev.tsv
Clear_Bible_OT_lowfat_XML := $(wildcard ../../Forked/macula-hebrew/WLC/lowfat/*.xml)
Clear_Bible_NT_lowfat_XML := $(wildcard ../../Forked/macula-greek/Nestle1904/lowfat/*.xml)
WLC_XML := $(wildcard ../../Forked/OS-morphhb/wlc/*.xml)
BibleTags_TSV = ../sourceTexts/BibleTagsOriginals/BibTags.OT.words.tsv ../sourceTexts/BibleTagsOriginals/BibTags.NT.words.tsv
BibleTags_OT_TSV_table = ../sourceTexts/BibleTagsOriginals/BibTags.OT.words.tsv
BibleTags_NT_TSV_table = ../sourceTexts/BibleTagsOriginals/BibTags.NT.words.tsv
BibleTags_OT_USFM := $(wildcard ../../Forked/bibletags-usfm/usfm/uhb/*.usfm)
BibleTags_NT_USFM := $(wildcard ../../Forked/bibletags-usfm/usfm/ugnt/*.usfm)
short_OSHB_TSV := ../sourceTexts/rawOSHB/OSHB.parsedOriginal.flat.morphemes.tsv

#=== Script declarations =======================

python3_12 := python3.12
python3_13 := python3.13
# python3_14 := ~/Downloads/Python-3.14.0a1/python
Python := $(python3_13)

SBE := ../../ScriptedBibleEditor/Python/ScriptedBibleEditor.py
BTranslit := ../../BibleTransliterations/Python/BibleTransliterations.py
HebrewTranslit := ../../BibleTransliterations/sourceTables/Hebrew.tsv
GreekTranslit := ../../BibleTransliterations/sourceTables/Greek.tsv
scripted_OT_updates := $(wildcard ScriptedOTUpdates/*)
scripted_NT_updates := $(wildcard ScriptedVLTUpdates/*)

#=== Top-level/Main stuff =======================

ALL: BOTH $(sideBySide_HTML) $(derived_USFM) $(derived_VREFs)
BOTH: LV RV
LV: LV_OT LV_NT

LV_OT: $(LV_OT_HTML)
LV_NT: $(LV_NT_HTML) $(Clear_Bible_NT_lowfat_TSV)
RV: $(RV_HTML)

#=== LV stuff =======================


# $(LV_HTML): $(LV_OT_HTML) $(LV_NT_HTML)
$(LV_OT_HTML) $(LV_NT_HTML): $(final_LV_OT_ESFM)  $(final_LV_NT_ESFM) convert_OET-LV_to_simple_HTML.py $(expanded_NT_wordtable)
	@echo "\n\nConvert OET LV ESFM files to simple HTML…\n"
	@$(Python) convert_OET-LV_to_simple_HTML.py

# $(final_LV_OT_USFM): $(intermediate_LV_OT_USFM) $(SBE) $(scripted_OT_updates) $(BTranslit) $(HebrewTranslit)
# 	@echo "\n\nRun ScriptedBibleEditor on OT USFM files…\n"
# 	@$(Python) $(SBE) ScriptedOTUpdates -qe

# Had $(final_LV_OT_ESFM) here before
../intermediateTexts/auto_edited_OT_ESFM/OET-LV_MAL.ESFM: $(intermediate_LV_OT_ESFM) $(SBE) $(scripted_OT_updates) $(BTranslit) $(HebrewTranslit)
	@echo "\n\nRun ScriptedBibleEditor on OT ESFM files…\n"
	@$(Python) $(SBE) ScriptedOTUpdates -qe
	#@echo "\n\nCopying OT word and morpheme tables from modified_source_glossed_OSHB_ESFM/ to auto_edited_OT_ESFM/…\n"
	#@cp ../intermediateTexts/modified_source_glossed_OSHB_ESFM/OET-LV_OT_word_table.tsv ../intermediateTexts/auto_edited_OT_ESFM/OET-LV_OT_word_table.tsv
	#@cp ../intermediateTexts/modified_source_glossed_OSHB_ESFM/OET-LV_OT_morpheme_table.tsv ../intermediateTexts/auto_edited_OT_ESFM/OET-LV_OT_morpheme_table.tsv
	#@cp ../intermediateTexts/modified_source_glossed_OSHB_ESFM/OET-LV_OT_lemma_table.tsv ../intermediateTexts/auto_edited_OT_ESFM/OET-LV_OT_lemma_table.tsv
	# Does SBE automatically do some of the above copying steps??? Well, it certainly wouldn't do both

$(final_LV_OT_word_tables): $(expanded_OT_TSV_tables)
	@echo "\n\nCopying OT word and morpheme tables from modified_source_glossed_OSHB_ESFM/ to auto_edited_OT_ESFM/…\n"
	@cp ../intermediateTexts/modified_source_glossed_OSHB_ESFM/OET-LV_OT_word_table.tsv ../intermediateTexts/auto_edited_OT_ESFM/OET-LV_OT_word_table.tsv
	@cp ../intermediateTexts/modified_source_glossed_OSHB_ESFM/OET-LV_OT_morpheme_table.tsv ../intermediateTexts/auto_edited_OT_ESFM/OET-LV_OT_morpheme_table.tsv
	@cp ../intermediateTexts/modified_source_glossed_OSHB_ESFM/OET-LV_OT_lemma_table.tsv ../intermediateTexts/auto_edited_OT_ESFM/OET-LV_OT_lemma_table.tsv
	# Does SBE automatically do some of the above copying steps??? Well, it certainly wouldn't do both

$(final_LV_NT_ESFM): $(intermediate_LV_NT_ESFM) $(SBE) $(scripted_NT_updates) $(BTranslit) $(GreekTranslit) $(HebrewTranslit) $(expanded_NT_wordtable)
	@echo "\n\nRun ScriptedBibleEditor on NT ESFM files…\n"
	@$(Python) $(SBE) ScriptedVLTUpdates -qe

../intermediateTexts/modified_source_glossed_OSHB_ESFM/OET-LV_OT_word_table.tsv: $(initial_OT_TSV_tables) $(Clear_Bible_MaculaHebrew_OT_TSV) $(scripted_OT_updates) add_tags_to_OT_word_table.py $(BTranslit) $(HebrewTranslit)
	@echo "\n\nAdd people/places/referent tags to OET OT word table…\n"
	@$(Python) add_tags_to_OT_word_table.py -e
	@echo "\n\nCopying and renaming OT morpheme and lemma tables from glossed_OSHB/ to modified_source_glossed_OSHB_ESFM/…\n"
	@cp ../intermediateTexts/glossed_OSHB/all_glosses.morphemes.tsv ../intermediateTexts/modified_source_glossed_OSHB_ESFM/OET-LV_OT_morpheme_table.tsv
	@cp ../intermediateTexts/glossed_OSHB/all_glosses.lemmas.tsv ../intermediateTexts/modified_source_glossed_OSHB_ESFM/OET-LV_OT_lemma_table.tsv

$(intermediate_LV_OT_ESFM): $(expanded_OT_TSV_tables) extract_glossed_OSHB_OT_to_ESFM.py
	@echo "\n\nExtract OT from TSV table to ESFM files…\n"
	@$(Python) extract_glossed_OSHB_OT_to_ESFM.py -e

$(initial_OT_TSV_tables): $(WLC_OT_TSV_table) $(Clear_Bible_MaculaHebrew_OT_TSV) apply_Clear_Macula_OT_glosses.py
	@echo "\n\nApply glosses from Macula Hebrew to OT (and reorder)…\n"
	@$(Python) apply_Clear_Macula_OT_glosses.py
	# @echo "\n\nCopying and renaming OT word and morpheme tables from glossed_OSHB/ to modified_source_glossed_OSHB_ESFM/…\n"
	# @cp ../intermediateTexts/glossed_OSHB/all_glosses.words.tsv ../intermediateTexts/modified_source_glossed_OSHB_ESFM/OET-LV_OT_word_table.tsv
	# @cp ../intermediateTexts/glossed_OSHB/all_glosses.morphemes.tsv ../intermediateTexts/modified_source_glossed_OSHB_ESFM/OET-LV_OT_morpheme_table.tsv

$(WLC_OT_TSV_table): $(short_OSHB_TSV) prepare_OSHB_for_glossing.py ourWLCHebrewGlosses.txt
	@echo "\n\nExpand columns in OT TSV and add our custom glosses…\n"
	@$(Python) prepare_OSHB_for_glossing.py

$(Clear_Bible_MaculaHebrew_OT_TSV): $(Clear_Bible_OT_lowfat_XML) $(WLC_OT_TSV_table) convert_ClearMaculaOT_to_our_TSV.py
	@echo "\n\nConvert Macula Hebrew from XML files to TSV…\n"
	@$(Python) convert_ClearMaculaOT_to_our_TSV.py

$(Clear_Bible_NT_lowfat_TSV): $(Clear_Bible_NT_lowfat_XML) $(BibleTags_NT_TSV_table) convert_ClearMaculaNT_to_TSV.py
	@echo "\n\nConvert Macula Greek from XML files to TSV…\n"
	@$(Python) convert_ClearMaculaNT_to_TSV.py

$(short_OSHB_TSV): $(WLC_XML) convert_OSHB_XML_to_TSV.py
	@echo "\n\nConvert OSHB XML files to TSV…\n"
	@$(Python) convert_OSHB_XML_to_TSV.py

$(BibleTags_TSV): $(BibleTags_OT_USFM) $(BibleTags_NT_USFM) convert_BibTags_USFM_to_TSV.py
	@echo "\n\nConvert BibleTags USFM files to TSV…\n"
	@$(Python) convert_BibTags_USFM_to_TSV.py

$(intermediate_LV_NT_ESFM) $(original_NT_wordtable): $(CNTR_book_table) $(CNTR_collation_table) $(CNTR_lemma_table) extract_VLT_NT_to_ESFM.py
	@echo "\n\nExtract NT from TSV table to the various {BBB}_gloss.ESFM files…\n"
	@$(Python) extract_VLT_NT_to_ESFM.py -e

$(expanded_NT_wordtable): $(original_NT_wordtable) $(Clear_Bible_NT_lowfat_TSV) $(scripted_NT_updates) add_tags_to_NT_word_table.py $(BTranslit) $(HebrewTranslit) $(GreekTranslit)
	@echo "\n\nAdd people/places/referent tags to OET NT word table…\n"
	@$(Python) add_tags_to_NT_word_table.py -e

#=== RV stuff =======================

$(final_RV_OT_word_tables): $(final_LV_OT_word_tables)
	@echo "\n\nCopying OT morpheme and lemma tables from auto_edited_OT_ESFM/ to ReadersVersion/…\n"
	@cp ../intermediateTexts/auto_edited_OT_ESFM/OET-LV_OT_morpheme_table.tsv ../translatedTexts/ReadersVersion/OET-LV_OT_morpheme_table.tsv
	@cp ../intermediateTexts/auto_edited_OT_ESFM/OET-LV_OT_lemma_table.tsv ../translatedTexts/ReadersVersion/OET-LV_OT_lemma_table.tsv

$(RV_HTML): $(LV_ESFM) $(RV_ESFM) connect_OET-RV_words_via_OET-LV.py convert_OET-RV_to_simple_HTML.py $(expanded_NT_wordtable) $(final_RV_OT_word_tables) $(BTranslit) $(GreekTranslit)
	@echo "\n\nConnect OET-RV words to OET-LV word numbers…\n"
	@$(Python) connect_OET-RV_words_via_OET-LV.py
	@echo "\n\nConvert OET RV ESFM files to simple HTML…\n"
	@$(Python) convert_OET-RV_to_simple_HTML.py

#=== Side-by-side stuff =======================

$(sideBySide_HTML): $(LV_OT_HTML) $(LV_NT_HTML) $(RV_HTML) pack_HTML_side-by-side.py
	@echo "\n\nPack LV and RV HTML files side-by-side…\n"
	@$(Python) pack_HTML_side-by-side.py

#=== Format conversions =======================

$(derived_USFM): $(LV_ESFM) $(RV_ESFM) convert_OET-LV-RV_ESFM_to_USFM.py
	@echo "\n\nCreate clean USFM files…\n"
	@$(Python) convert_OET-LV-RV_ESFM_to_USFM.py

$(derived_VREFs): $(LV_ESFM) $(RV_ESFM) convert_OET-LV-RV_USFM_to_VREF.py
	@echo "\n\nCreate VREF.txt files from USFM…\n"
	@$(Python) convert_OET-LV-RV_USFM_to_VREF.py
	@echo "\n\nFinally, just count our progress…\n"
	@$(Python) count_completed_OET-RV_verses.py
	@$(Python) --version


#=== Partial stuff =======================


.PHONY: check
check: $(LV_ESFM) $(RV_ESFM) connect_OET-RV_words_via_OET-LV.py $(expanded_NT_wordtable) $(final_RV_OT_word_tables) $(BTranslit) $(GreekTranslit)
	@echo "\n\nConnect OET-RV words to OET-LV word numbers…\n"
	@$(Python) connect_OET-RV_words_via_OET-LV.py
	@echo "\n\nFinally, just count our progress…\n"
	@$(Python) count_completed_OET-RV_verses.py
	@$(Python) --version


#=== Clean up stuff =======================

.PHONY: clean
clean: clean_LT clean_RT
.PHONY: clean_LT
clean_LT: clean_LT_OT cleanLT_NT

.PHONY: clean_LT_OT
clean_LT_OT:
	rm ../intermediateTexts/modified_source_glossed_OSHB_USFM/*.usfm
	rm ../intermediateTexts/modified_source_glossed_OSHB_ESFM/*.ESFM
	rm ../intermediateTexts/glossed_OSHB/all_glosses.morphemes.tsv ../intermediateTexts/glossed_OSHB/lemmas.tsv
	rm ../intermediateTexts/Clear.Bible_derived_Macula_data/Clear.Bible_MaculaHebrew.OT.morphemes.abbrev.tsv
	rm ../intermediateTexts/glossed_OSHB/our_WLC_glosses.morphemes.tsv
	rm ../sourceTexts/rawOSHB/OSHB.parsedOriginal.flat.morphemes.tsv

.PHONY: clean_LT_NT
clean_LT_NT:
	rm ../intermediateTexts/auto_edited_VLT_ESFM/*.ESFM
	rm ../intermediateTexts/modified_source_VLT_ESFM/*.ESFM

.PHONY: clean_RT
clean_RT:
	@echo "Nothing to clean for RT yet"