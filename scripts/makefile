# OET makfile
#
# Last updated: 2023-03-06 by RJH
#

#=== Folder and file declarations =======================

LV_HTML := $(wildcard ../derivedTexts/simpleHTML/LiteralVersion/*.html)
RV_HTML := $(wildcard ../derivedTexts/simpleHTML/ReadersVersion/*.html)
RV_ESFM := $(wildcard ../translatedTexts/ReadersVersion/*.ESFM)
final_LV_OT_USFM := $(wildcard ../intermediateTexts/auto_edited_OT_USFM/*.usfm)
final_LV_NT_ESFM := $(wildcard ../intermediateTexts/auto_edited_VLT_ESFM/*.ESFM)
intermediate_LV_OT_USFM := $(wildcard ../intermediateTexts/modified_source_glossed_OSHB_USFM/*.usfm)
intermediate_LV_NT_ESFM := $(wildcard ../intermediateTexts/modified_source_VLT_ESFM/*.ESFM)
all_OT_TSV_table := ../intermediateTexts/glossed_OSHB/all_glosses.morphemes.tsv
WLC_OT_TSV_table := ../intermediateTexts/glossed_OSHB/WLC_glosses.morphemes.tsv
Clear_Bible_OT_lowfat_TSV := ../intermediateTexts/Clear.Bible_lowfat_trees/ClearLowFatTreesAbbrev.OT.morphemes.tsv
Clear_Bible_NT_lowfat_TSV := ../intermediateTexts/Clear.Bible_lowfat_trees/ClearLowFatTreesAbbrev.NT.words.tsv
BibleTags_TSV = ../sourceTexts/BibleTagsOriginals/BibTags.OT.words.tsv ../sourceTexts/BibleTagsOriginals/BibTags.NT.words.tsv
BibleTags_OT_TSV_table = ../sourceTexts/BibleTagsOriginals/BibTags.OT.words.tsv
BibleTags_NT_TSV_table = ../sourceTexts/BibleTagsOriginals/BibTags.NT.words.tsv
short_OSHB_TSV := ../sourceTexts/rawOSHB/OSHB.original.flat.morphemes.tsv

#=== Script declarations =======================

Python := python3.12
SBE := ../../ScriptedBibleEditor/Python/ScriptedBibleEditor.py
BTranslit := ../../BibleTransliterations/Python/BibleTransliterations.py
Hebrew := ../../BibleTransliterations/sourceTables/Hebrew.tsv
Greek := ../../BibleTransliterations/sourceTables/Greek.tsv

#=== Top-level/Main stuff =======================

ALL: BOTH SideBySide
BOTH: LV RV
LV: LV_OT LV_NT

LV_OT: $(LV_OT_HTML)
LV_NT: $(LV_NT_HTML) $(Clear_Bible_NT_lowfat_TSV)
RV: $(RV_HTML)

#=== LV stuff =======================

$(LV_HTML): $(final_LV_OT_USFM)  $(final_LV_NT_ESFM) convert_OET-LV_to_simple_HTML.py
	@echo "\n\nConvert OET LV USFM files to simple HTML…\n"
	@$(Python) convert_OET-LV_to_simple_HTML.py

$(final_LV_OT_USFM): $(intermediate_LV_OT_USFM) $(SBE) $(wildcard ScriptedOTUpdates/*) $(BTranslit) $(Hebrew)
	@echo "\n\nRun ScriptedBibleEditor on OT USFM files…\n"
	@$(Python) $(SBE) ScriptedOTUpdates -qe

$(final_LV_NT_ESFM): $(intermediate_LV_NT_ESFM) $(SBE) $(wildcard ScriptedVLTUpdates/*) $(BTranslit) $(Greek) $(Hebrew)
	@echo "\n\nRun ScriptedBibleEditor on NT ESFM files…\n"
	@$(Python) $(SBE) ScriptedVLTUpdates -qe

$(intermediate_LV_OT_USFM): $(all_OT_TSV_table) extract_OSHB_OT_to_USFM.py
	@echo "\n\nExtract OT from TSV table to USFM files…\n"
	@$(Python) extract_OSHB_OT_to_USFM.py -e

$(all_OT_TSV_table): $(WLC_OT_TSV_table) $(Clear_Bible_OT_lowfat_TSV) apply_Clear_Macula_OT_glosses.py
	@echo "\n\nApply glosses from Macula to OT (and reorder)…\n"
	@$(Python) apply_Clear_Macula_OT_glosses.py

$(WLC_OT_TSV_table): $(short_OSHB_TSV) prepare_OSHB_for_glossing.py WLCHebrewGlosses.txt
	@echo "\n\nExpand columns in OT TSV and add our custom glosses…\n"
	@$(Python) prepare_OSHB_for_glossing.py

$(Clear_Bible_OT_lowfat_TSV): $(wildcard ../../Forked/macula-hebrew/lowfat/*.xml) $(WLC_OT_TSV_table) convert_ClearMaculaOT_to_TSV.py
	@echo "\n\nConvert Macula Hebrew from XML files to TSV…\n"
	@$(Python) convert_ClearMaculaOT_to_TSV.py

$(Clear_Bible_NT_lowfat_TSV): $(wildcard ../../Forked/macula-greek/Nestle1904/lowfat/*.xml) $(BibleTags_NT_TSV_table) convert_ClearMaculaNT_to_TSV.py
	@echo "\n\nConvert Macula Greek from XML files to TSV…\n"
	@$(Python) convert_ClearMaculaNT_to_TSV.py

$(short_OSHB_TSV): $(wildcard ../../Forked/OS-morphhb/wlc/*.xml) convert_OSHB_XML_to_TSV.py
	@echo "\n\nConvert OSHB XML files to TSV…\n"
	@$(Python) convert_OSHB_XML_to_TSV.py

$(BibleTags_TSV): $(wildcard ../../Forked/bibletags-usfm/usfm/uhb/*.usfm) $(wildcard ../../Forked/bibletags-usfm/usfm/ugnt/*.usfm) convert_BibTags_USFM_to_TSV.py
	@echo "\n\nConvert BibleTags USFM files to TSV…\n"
	@$(Python) convert_BibTags_USFM_to_TSV.py

$(intermediate_LV_NT_ESFM): ../../CNTR-GNT/sourceExports/book.csv ../../CNTR-GNT/sourceExports/collation.updated.csv extract_VLT_NT_to_ESFM.py
	@echo "\n\nExtract NT from TSV table to ESFM files…\n"
	@$(Python) extract_VLT_NT_to_ESFM.py -e

#=== RV stuff =======================

$(RV_HTML): $(RV_ESFM) connect_OET-RV_words.py convert_OET-RV_to_simple_HTML.py
	@echo "\n\nConnect OET-RV words to OET-LV word numbers…\n"
	@$(Python) connect_OET-RV_words.py
	@echo "\n\nConvert OET RV USFM files to simple HTML…\n"
	@$(Python) convert_OET-RV_to_simple_HTML.py

#=== Side-by-side stuff =======================

SideBySide: $(LV_HTML) $(RV_HTML) pack_HTML_side-by-side.py
	@echo "\n\nPack LV and RV HTML files side-by-side…\n"
	@$(Python) pack_HTML_side-by-side.py


#=== Clean up stuff =======================

clean: clean_LT clean_RT
clean_LT: clean_LT_OT cleanLT_NT

clean_LT_OT:
	rm ../intermediateTexts/modified_source_glossed_OSHB_USFM/*.usfm
	rm ../intermediateTexts/glossed_OSHB/all_glosses.morphemes.tsv
	rm ../intermediateTexts/Clear.Bible_lowfat_trees/ClearLowFatTreesAbbrev.OT.morphemes.tsv
	rm ../intermediateTexts/glossed_OSHB/WLC_glosses.morphemes.tsv
	rm ../sourceTexts/rawOSHB/OSHB.original.flat.morphemes.tsv

clean_LT_NT:
	rm ../intermediateTexts/auto_edited_VLT_ESFM/*.ESFM
	rm ../intermediateTexts/modified_source_VLT_ESFM/*.ESFM

clean_RT:
	@echo "Nothing to clean for RT yet"