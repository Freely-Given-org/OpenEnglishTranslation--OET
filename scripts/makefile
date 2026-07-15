# OET makefile
#
# Last updated: 2026-05-15 by RJH
#
# CHANGELOG:
#	2025-12-08 Copy OET LV OT & NT word tables into BSB and MSB folders
#	2026-02-20 Produce OET-RV sections and automated TTS files for radio production
#	2026-03-06 Separated derivedFiles folder out with some now in furtherDerivedFiles
#   2026-07-13 Removed absolute filepaths (for word-table copies) to work on laptop
#

#=== Folder and file declarations =======================

# Source of truth for which books have been translated (these are not cleaned)
RV_ESFM_SOURCE := $(wildcard ../translatedTexts/ReadersVersion/OET-RV_???.ESFM)
BOOKS := $(patsubst ../translatedTexts/ReadersVersion/OET-RV_%.ESFM,%,$(RV_ESFM_SOURCE))

# Standard book codes for Literal Version
ESFM_OT_BOOKS := GEN EXO LEV NUM DEU JOS JDG RUT SA1 SA2 KI1 KI2 CH1 CH2 EZR NEH EST JOB PSA PRO ECC SNG ISA JER LAM EZE DAN HOS JOL AMO OBA JNA MIC NAH HAB ZEP HAG ZEC MAL
ESFM_NT_BOOKS := MAT MRK LUK JHN ACT ROM CO1 CO2 GAL EPH PHP COL TH1 TH2 TI1 TI2 TIT PHM HEB JAM PE1 PE2 JN1 JN2 JN3 JDE REV
ESFM_LV_BOOKS := $(ESFM_OT_BOOKS) $(ESFM_NT_BOOKS)

# USFM book codes mapping (generated from bos_books_codes_py)
USFM_OT_BOOKS := Gen Exo Lev Num Deu Jos Jdg Rut 1Sa 2Sa 1Ki 2Ki 1Ch 2Ch Ezr Neh Est Job Psa Pro Ecc Sng Isa Jer Lam Ezk Dan Hos Jol Amo Oba Jon Mic Nah Hab Zep Hag Zec Mal
USFM_NT_BOOKS := Mat Mar Luk Jhn Act Rom 1Co 2Co Gal Eph Php Col 1Th 2Th 1Ti 2Ti Tit Phn Heb Jas 1Pe 2Pe 1Jn 2Jn 3Jn Jud Rev
USFM_LV_BOOKS := $(USFM_OT_BOOKS) $(USFM_NT_BOOKS)
USFM_RV_BOOKS := Act Amo Bar 1Ch 2Ch 1Co 2Co Col Dag Dan Deu Ecc Eph Es1 Es2 Esg Est Exo Ezk Ezr Frt Gal Gen Hab Hag Heb Hos Int Isa Jas Jud Jdg Jdt Jer Jhn 1Jn 2Jn 3Jn Jon Job Jol Jos 1Ki 2Ki Lam Lev Lul 1Ma 2Ma 3Ma 4Ma Mal Man Mat Mic Mar Nah Neh Num Oba 1Pe 2Pe Phm Php Pro Ps2 Psa Rev Rom Rut 1Sa 2Sa Sir Sng 1Th 2Th 1Ti 2Ti Tit Tob Wis Zec Zep

derived_audio_sections := ../exportedFiles/OET-RV_sectionReadings/MRK/MRK_S2.ogg
derived_VREFs := ../exportedFiles/OET-RV.vref.txt ../exportedFiles/OET-LV.vref.txt
derived_USFM := $(patsubst %,../exportedFiles/cleanedUSFM/ReadersVersion/OET-RV_%.USFM,$(USFM_RV_BOOKS)) \
                $(patsubst %,../exportedFiles/cleanedUSFM/LiteralVersion/OET-LV_%.USFM,$(USFM_LV_BOOKS))

sideBySide_HTML := $(patsubst %,../exportedFiles/simpleHTML/SideBySide/%.html,$(BOOKS))
LV_OT_HTML := $(patsubst %,../exportedFiles/simpleHTML/LiteralVersion/%.html,$(ESFM_OT_BOOKS))
LV_NT_HTML := $(patsubst %,../exportedFiles/simpleHTML/LiteralVersion/%.html,$(ESFM_NT_BOOKS))
RV_HTML := $(patsubst %,../exportedFiles/simpleHTML/ReadersVersion/%.html,$(BOOKS))

RV_ESFM := $(RV_ESFM_SOURCE)
final_LV_OT_ESFM := $(patsubst %,../derivedTexts/auto_edited_OT_ESFM/OET-LV_%.ESFM,$(ESFM_OT_BOOKS))
final_LV_NT_ESFM := $(patsubst %,../derivedTexts/auto_edited_VLT_ESFM/OET-LV_%.ESFM,$(ESFM_NT_BOOKS))

LV_names_TSV_table := ../derivedTexts/OET-LV_names_table.tsv
LV_ESFM := $(final_LV_OT_ESFM) $(final_LV_NT_ESFM)
intermediate_LV_OT_ESFM := $(patsubst %,../intermediateTexts/modified_source_glossed_OSHB_ESFM/%_gloss.ESFM,$(ESFM_OT_BOOKS))
intermediate_LV_NT_ESFM := $(patsubst %,../intermediateTexts/modified_source_VLT_ESFM/%_gloss.ESFM,$(ESFM_NT_BOOKS))
final_RV_OT_word_tables = ../translatedTexts/ReadersVersion/OET-LV_OT_morpheme_table.tsv ../translatedTexts/ReadersVersion/OET-LV_OT_lemma_table.tsv
final_LV_OT_word_tables = ../derivedTexts/auto_edited_OT_ESFM/OET-LV_OT_word_table.tsv ../derivedTexts/auto_edited_OT_ESFM/OET-LV_OT_morpheme_table.tsv ../derivedTexts/auto_edited_OT_ESFM/OET-LV_OT_lemma_table.tsv
expanded_OT_TSV_tables := ../intermediateTexts/modified_source_glossed_OSHB_ESFM/OET-LV_OT_word_table.tsv ../intermediateTexts/modified_source_glossed_OSHB_ESFM/OET-LV_OT_morpheme_table.tsv ../intermediateTexts/modified_source_glossed_OSHB_ESFM/OET-LV_OT_lemma_table.tsv
initial_OT_TSV_tables := ../intermediateTexts/glossed_OSHB/all_glosses.words.tsv ../intermediateTexts/glossed_OSHB/all_glosses.morphemes.tsv ../intermediateTexts/glossed_OSHB/all_glosses.lemmas.tsv
expanded_NT_wordtable = ../intermediateTexts/modified_source_VLT_ESFM/OET-LV_NT_word_table.tsv
original_NT_wordtable = ../intermediateTexts/modified_source_VLT_ESFM/OET-LV_NT_word_table.10columns.tsv

CNTR_lemma_table = ../../CNTR-GNT/derivedFormats/lemmas.alphabetical.tsv
CNTR_book_table = ../../CNTR-GNT/sourceExports/book.csv
CNTR_collation_table = ../../CNTR-GNT/sourceExports/collation.csv
CNTR_word_table = ../../CNTR-GNT/sourceExports/word.csv
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

# python3_13 := python3.13
# python3_14 := python3.14
# python3_15 := ~/Downloads/Python-3.15.0a1/python
# Python := $(python3_14)
UVrun := uv run


# For Rust, define the paths (to ensure that we have the latest release file)
SBE_RUST_DIR := ../../ScriptedBibleEditor/Rust/scripted_bible_editor
SBE_RUST_BIN := $(SBE_RUST_DIR)/target/release/scripted_bible_editor

# Rule to build the Rust binary if sources have changed
$(SBE_RUST_BIN): $(shell find $(SBE_RUST_DIR)/src -type f) $(SBE_RUST_DIR)/Cargo.toml
	cd $(SBE_RUST_DIR) && cargo build --release

# Choose ONE of the following
# SBE := ../../ScriptedBibleEditor/Python/ScriptedBibleEditor.py
SBE := $(SBE_RUST_BIN)


# Choose ONE of the following
# BTranslit := ../../BibleTransliterations/Python/BibleTransliterations.py
BTranslit := ../../BibleTransliterations/Rust/src/lib.rs

HebrewTranslit := ../../BibleTransliterations/sourceTables/Hebrew.tsv
GreekTranslit := ../../BibleTransliterations/sourceTables/Greek.tsv

scripted_OT_updates := $(wildcard ScriptedOTUpdates/*)
scripted_NT_updates := $(wildcard ScriptedVLTUpdates/*)

sideBySide_sentinel := ../exportedFiles/simpleHTML/SideBySide/.sentinel
RV_word_tables_sentinel := ../translatedTexts/ReadersVersion/.word_tables_sentinel

#=== Top-level/Main stuff =======================

ALL: BOTH $(sideBySide_HTML) $(derived_USFM) $(derived_VREFs)
BOTH: LV RV
LV: LV_OT LV_NT $(LV_names_TSV_table)

LV_OT: $(LV_OT_HTML)
LV_NT: $(LV_NT_HTML) $(Clear_Bible_NT_lowfat_TSV)
RV: $(RV_HTML)

#=== LV stuff =======================

$(LV_names_TSV_table): ScriptedOTUpdates/restoreNames.commandTable.tsv ScriptedVLTUpdates/OTNames.commandTable.tsv ScriptedVLTUpdates/NTNames.commandTable.tsv create_OET-LV_TSV_name_table.py
	@echo "\n\nCreate OET-LV TSV names table from command tables…\n"
	@$(UVrun) create_OET-LV_TSV_name_table.py

LV_HTML_sentinel := ../exportedFiles/simpleHTML/LiteralVersion/.html_sentinel

$(LV_HTML_sentinel): $(final_LV_OT_ESFM) $(final_LV_NT_ESFM) convert_OET-LV_to_simple_HTML.py $(expanded_NT_wordtable)
	@echo "\n\nConvert OET LV ESFM files to simple HTML…\n"
	@$(UVrun) convert_OET-LV_to_simple_HTML.py
	@touch $@

$(LV_OT_HTML) $(LV_NT_HTML): $(LV_HTML_sentinel)

# $(final_LV_OT_USFM): $(intermediate_LV_OT_USFM) $(SBE) $(scripted_OT_updates) $(BTranslit) $(HebrewTranslit)
# 	@echo "\n\nRun ScriptedBibleEditor on OT USFM files…\n"
# 	@$(SBE) ScriptedOTUpdates -qe

# Had $(final_LV_OT_ESFM) here before
LV_OT_ESFM_sentinel := ../derivedTexts/auto_edited_OT_ESFM/.sentinel
$(LV_OT_ESFM_sentinel): $(intermediate_LV_OT_ESFM) $(SBE) $(scripted_OT_updates) $(BTranslit) $(HebrewTranslit)
	@echo "\n\nRun ScriptedBibleEditor on OT ESFM files…\n"
	@$(SBE) ScriptedOTUpdates -qe
	@touch $@

$(final_LV_OT_ESFM): $(LV_OT_ESFM_sentinel)

LV_OT_word_tables_sentinel := ../derivedTexts/auto_edited_OT_ESFM/.word_tables_sentinel
$(LV_OT_word_tables_sentinel): $(expanded_OT_TSV_tables)
	@echo "\n\nCopying OT word and morpheme tables from modified_source_glossed_OSHB_ESFM/ to auto_edited_OT_ESFM/…\n"
	@cp -a ../intermediateTexts/modified_source_glossed_OSHB_ESFM/OET-LV_OT_word_table.tsv ../derivedTexts/auto_edited_OT_ESFM/OET-LV_OT_word_table.tsv
	@cp -a ../intermediateTexts/modified_source_glossed_OSHB_ESFM/OET-LV_OT_morpheme_table.tsv ../derivedTexts/auto_edited_OT_ESFM/OET-LV_OT_morpheme_table.tsv
	@cp -a ../intermediateTexts/modified_source_glossed_OSHB_ESFM/OET-LV_OT_lemma_table.tsv ../derivedTexts/auto_edited_OT_ESFM/OET-LV_OT_lemma_table.tsv
	@touch $@

$(final_LV_OT_word_tables): $(LV_OT_word_tables_sentinel)

LV_NT_ESFM_sentinel := ../derivedTexts/auto_edited_VLT_ESFM/.sentinel
$(LV_NT_ESFM_sentinel): $(intermediate_LV_NT_ESFM) $(SBE) $(scripted_NT_updates) $(BTranslit) $(GreekTranslit) $(HebrewTranslit) $(expanded_NT_wordtable)
	@echo "\n\nRun ScriptedBibleEditor on NT ESFM files…\n"
	@$(SBE) ScriptedVLTUpdates -qe
	@touch $@

$(final_LV_NT_ESFM): $(LV_NT_ESFM_sentinel)

../intermediateTexts/modified_source_glossed_OSHB_ESFM/OET-LV_OT_word_table.tsv: $(initial_OT_TSV_tables) $(Clear_Bible_MaculaHebrew_OT_TSV) $(scripted_OT_updates) add_tags_to_OT_word_table.py $(BTranslit) $(HebrewTranslit)
	@echo "\n\nAdd people/places/referent tags to OET OT word table…\n"
	@$(UVrun) add_tags_to_OT_word_table.py -e
	@echo "\n\nCopying and renaming OT morpheme and lemma tables from glossed_OSHB/ to modified_source_glossed_OSHB_ESFM/…\n"
	@cp -a ../intermediateTexts/glossed_OSHB/all_glosses.morphemes.tsv ../intermediateTexts/modified_source_glossed_OSHB_ESFM/OET-LV_OT_morpheme_table.tsv
	@cp -a ../intermediateTexts/glossed_OSHB/all_glosses.lemmas.tsv ../intermediateTexts/modified_source_glossed_OSHB_ESFM/OET-LV_OT_lemma_table.tsv

$(intermediate_LV_OT_ESFM): $(expanded_OT_TSV_tables) extract_glossed_OSHB_OT_to_ESFM.py
	@echo "\n\nExtract OT from TSV table to ESFM files…\n"
	@$(UVrun) extract_glossed_OSHB_OT_to_ESFM.py -e

$(initial_OT_TSV_tables): $(WLC_OT_TSV_table) $(Clear_Bible_MaculaHebrew_OT_TSV) apply_Clear_Macula_OT_glosses.py
	@echo "\n\nApply glosses from Macula Hebrew to OT (and reorder)…\n"
	@$(UVrun) apply_Clear_Macula_OT_glosses.py
	# @echo "\n\nCopying and renaming OT word and morpheme tables from glossed_OSHB/ to modified_source_glossed_OSHB_ESFM/…\n"
	# @cp -a ../intermediateTexts/glossed_OSHB/all_glosses.words.tsv ../intermediateTexts/modified_source_glossed_OSHB_ESFM/OET-LV_OT_word_table.tsv
	# @cp -a ../intermediateTexts/glossed_OSHB/all_glosses.morphemes.tsv ../intermediateTexts/modified_source_glossed_OSHB_ESFM/OET-LV_OT_morpheme_table.tsv

$(WLC_OT_TSV_table): $(short_OSHB_TSV) prepare_OSHB_for_glossing.py ourWLCHebrewGlosses.txt
	@echo "\n\nExpand columns in OT TSV and add our custom glosses…\n"
	@$(UVrun) prepare_OSHB_for_glossing.py

$(Clear_Bible_MaculaHebrew_OT_TSV): $(Clear_Bible_OT_lowfat_XML) $(WLC_OT_TSV_table) convert_ClearMaculaOT_to_our_TSV.py
	@echo "\n\nConvert Macula Hebrew from XML files to TSV…\n"
	@$(UVrun) convert_ClearMaculaOT_to_our_TSV.py

$(Clear_Bible_NT_lowfat_TSV): $(Clear_Bible_NT_lowfat_XML) $(BibleTags_NT_TSV_table) convert_ClearMaculaNT_to_TSV.py
	@echo "\n\nConvert Macula Greek from XML files to TSV…\n"
	@$(UVrun) convert_ClearMaculaNT_to_TSV.py

$(short_OSHB_TSV): $(WLC_XML) convert_OSHB_XML_to_TSV.py
	@echo "\n\nConvert OSHB XML files to TSV…\n"
	@$(UVrun) convert_OSHB_XML_to_TSV.py

$(BibleTags_TSV): $(BibleTags_OT_USFM) $(BibleTags_NT_USFM) convert_BibTags_USFM_to_TSV.py
	@echo "\n\nConvert BibleTags USFM files to TSV…\n"
	@$(UVrun) convert_BibTags_USFM_to_TSV.py

$(intermediate_LV_NT_ESFM) $(original_NT_wordtable): $(CNTR_book_table) $(CNTR_collation_table) $(CNTR_word_table) $(CNTR_lemma_table) extract_VLT_NT_to_ESFM.py
	@echo "\n\nExtract NT from TSV table to the various {BBB}_gloss.ESFM files…\n"
	@$(UVrun) extract_VLT_NT_to_ESFM.py -e

$(expanded_NT_wordtable): $(original_NT_wordtable) $(Clear_Bible_NT_lowfat_TSV) $(scripted_NT_updates) add_tags_to_NT_word_table.py $(BTranslit) $(HebrewTranslit) $(GreekTranslit)
	@echo "\n\nAdd people/places/referent tags to OET NT word table…\n"
	@$(UVrun) add_tags_to_NT_word_table.py -e
	@echo "\n\nCopying final OET NT word table to OET-RV and BSB/MSB folders…\n"
	@cp -a $(expanded_NT_wordtable) ../translatedTexts/ReadersVersion/
	@cp -a $(expanded_NT_wordtable) ../../OpenBibleData/copiedBibles/English/Berean.Bible/BSB/
	@cp -a $(expanded_NT_wordtable) ../../OpenBibleData/copiedBibles/English/Berean.Bible/MSB/

#=== RV stuff =======================

$(RV_word_tables_sentinel): $(final_LV_OT_word_tables)
	@echo "\n\nCopying OT morpheme and lemma tables from auto_edited_OT_ESFM/ to ReadersVersion/…\n"
	@cp -a ../derivedTexts/auto_edited_OT_ESFM/OET-LV_OT_morpheme_table.tsv ../translatedTexts/ReadersVersion/OET-LV_OT_morpheme_table.tsv
	@cp -a ../derivedTexts/auto_edited_OT_ESFM/OET-LV_OT_lemma_table.tsv ../translatedTexts/ReadersVersion/OET-LV_OT_lemma_table.tsv
	@echo "\n\nCopying final OET OT word table to BSB & MSB folders…\n"
	@cp -a ../translatedTexts/ReadersVersion/OET-LV_OT_word_table.tsv ../../OpenBibleData/copiedBibles/English/Berean.Bible/BSB/
	@cp -a ../translatedTexts/ReadersVersion/OET-LV_OT_word_table.tsv ../../OpenBibleData/copiedBibles/English/Berean.Bible/MSB/
	@touch $@

$(final_RV_OT_word_tables): $(RV_word_tables_sentinel)

RV_sentinel := ../translatedTexts/ReadersVersion/.connected_sentinel
RV_HTML_sentinel := ../exportedFiles/simpleHTML/ReadersVersion/.html_sentinel

$(RV_sentinel): $(LV_ESFM) $(RV_ESFM) connect_OET-RV_words_via_OET-LV.py $(expanded_NT_wordtable) $(final_RV_OT_word_tables) $(BTranslit) $(GreekTranslit)
	@echo "\n\nConnect OET-RV words to OET-LV word numbers (in full mode)…\n"
	@$(UVrun) connect_OET-RV_words_via_OET-LV.py
	@touch $@

$(RV_HTML_sentinel): $(RV_sentinel) convert_OET-RV_to_simple_HTML.py $(expanded_NT_wordtable) $(final_RV_OT_word_tables) $(BTranslit) $(GreekTranslit)
	@echo "\n\nConvert OET RV ESFM files to simple HTML…\n"
	@$(UVrun) convert_OET-RV_to_simple_HTML.py
	@touch $@

$(RV_HTML): $(RV_HTML_sentinel)

#=== Side-by-side stuff =======================

$(sideBySide_sentinel): $(LV_OT_HTML) $(LV_NT_HTML) $(RV_HTML) pack_HTML_side-by-side.py
	@echo "\n\nPack LV and RV HTML files side-by-side…\n"
	@$(UVrun) pack_HTML_side-by-side.py
	@touch $@

$(sideBySide_HTML): $(sideBySide_sentinel)

#=== Format conversions =======================

USFM_sentinel := ../exportedFiles/cleanedUSFM/.sentinel

$(USFM_sentinel): $(LV_ESFM) $(RV_ESFM) convert_OET-LV-RV_ESFM_to_USFM.py
	@echo "\n\nCreate clean USFM files…\n"
	@$(UVrun) convert_OET-LV-RV_ESFM_to_USFM.py
	@touch $@

$(derived_USFM): $(USFM_sentinel)

VREF_sentinel := ../exportedFiles/.vref_sentinel

$(VREF_sentinel): $(LV_ESFM) $(RV_ESFM) convert_OET-LV-RV_USFM_to_VREF.py
	@echo "\n\nCreate VREF.txt files from USFM…\n"
	@$(UVrun) convert_OET-LV-RV_USFM_to_VREF.py
	@echo "\n\nFinally, just count our progress…\n"
	@$(UVrun) count_completed_OET-RV_verses.py
	@touch $@

$(derived_VREFs): $(VREF_sentinel)

$(derived_audio_sections): $(RV_ESFM) export_OET-RV_to_sectionReadings.py
	@echo "\n\nCreate section readings from OET-RV…\n"
	@$(UVrun) export_OET-RV_to_sectionReadings.py


#=== Partial stuff =======================

.PHONY: check
check: $(LV_ESFM) $(RV_ESFM) connect_OET-RV_words_via_OET-LV.py $(expanded_NT_wordtable) $(final_RV_OT_word_tables) $(BTranslit) $(GreekTranslit)
	@echo "\n\nConnect OET-RV words to OET-LV word numbers (in fast mode)…\n"
	@$(UVrun) connect_OET-RV_words_via_OET-LV.py --fast
	@echo "\n\nFinally, just count our progress…\n"
	@$(UVrun) count_completed_OET-RV_verses.py


.PHONY: audio
audio: $(derived_audio_sections)
	@echo "\n\nFinally, just count our progress…\n"
	@$(UVrun) count_completed_OET-RV_verses.py


#=== Clean up stuff =======================

.PHONY: clean
clean: clean_LV clean_RV
.PHONY: clean_LV
clean_LT: clean_LV_OT clean_LV_NT

.PHONY: clean_LV_OT
clean_LT_OT:
	@echo "Clean OET LV OT intermediate texts"
	rm -f ../intermediateTexts/modified_source_glossed_OSHB_USFM/*.usfm
	rm -f ../intermediateTexts/modified_source_glossed_OSHB_ESFM/*.ESFM
	rm -f ../intermediateTexts/glossed_OSHB/all_glosses.morphemes.tsv ../intermediateTexts/glossed_OSHB/lemmas.tsv
	rm -f ../intermediateTexts/Clear.Bible_derived_Macula_data/Clear.Bible_MaculaHebrew.OT.morphemes.abbrev.tsv
	rm -f ../intermediateTexts/glossed_OSHB/our_WLC_glosses.morphemes.tsv
	rm -f ../sourceTexts/rawOSHB/OSHB.parsedOriginal.flat.morphemes.tsv

.PHONY: clean_LV_NT
clean_LV_NT:
	@echo "Clean OET LV NT intermediate and derived texts"
	rm -f ../derivedTexts/auto_edited_VLT_ESFM/*.ESFM
	rm -f ../intermediateTexts/modified_source_VLT_ESFM/*.ESFM

.PHONY: clean_RV
clean_RV:
	@echo "Nothing to clean for OET RV"
