# HTML := $(wildcard ../derivedTexts/simpleHTML/LiteralVersion/*.html)
OT_HTML := ../derivedTexts/simpleHTML/LiteralVersion/OET-LV_GEN.html ../derivedTexts/simpleHTML/LiteralVersion/OET-LV_MAL.html
NT_HTML := ../derivedTexts/simpleHTML/LiteralVersion/OET-LV_MAT.html ../derivedTexts/simpleHTML/LiteralVersion/OET-LV_REV.html
final_OT_USFM := $(wildcard ../intermediateTexts/auto_edited_OT_USFM/*.usfm)
final_NT_USFM := $(wildcard ../intermediateTexts/auto_edited_VLT_USFM/*.usfm)
intermediate_OT_USFM := $(wildcard ../intermediateTexts/modified_source_glossed_OSHB_USFM/*.usfm)
intermediate_NT_USFM := $(wildcard ../intermediateTexts/modified_source_VLT_USFM/*.usfm)
all_OT_TSV_table := ../intermediateTexts/glossed_OSHB/all_glosses.morphemes.tsv
WLC_OT_TSV_table := ../intermediateTexts/glossed_OSHB/WLC_glosses.morphemes.tsv
Clear_Bible_OT_lowfat_TSV := ../intermediateTexts/Clear.Bible_lowfat_trees/ClearLowFatTreesAbbrev.OT.morphemes.tsv
Clear_Bible_NT_lowfat_TSV := ../intermediateTexts/Clear.Bible_lowfat_trees/ClearLowFatTreesAbbrev.NT.words.tsv
BibleTags_TSV = ../sourceTexts/BibleTagsOriginals/BibTags.OT.words.tsv ../sourceTexts/BibleTagsOriginals/BibTags.NT.words.tsv
BibleTags_OT_TSV_table = ../sourceTexts/BibleTagsOriginals/BibTags.OT.words.tsv
BibleTags_NT_TSV_table = ../sourceTexts/BibleTagsOriginals/BibTags.NT.words.tsv
short_OSHB_TSV := ../sourceTexts/rawOSHB/OSHB.original.flat.morphemes.tsv

SBE = ../../ScriptedBibleEditor/Python/ScriptedBibleEditor.py
BTranslit = ../../BibleTransliterations/Python/BibleTransliterations.py
Hebrew = ../../BibleTransliterations/sourceTables/Hebrew.tsv
Greek = ../../BibleTransliterations/sourceTables/Greek.tsv

LV: OT NT

OT: $(OT_HTML)
NT: $(NT_HTML) $(Clear_Bible_NT_lowfat_TSV)

# $(HTML): $(final_OT_USFM) $(final_NT_USFM) convert_OET-LV_to_simple_HTML.py
# 	@echo "\n\nConvert OT and NT LV USFM files to simple HTML…\n"
# 	@python convert_OET-LV_to_simple_HTML.py

$(OT_HTML): $(final_OT_USFM) convert_OET-LV_to_simple_HTML.py
	@echo "\n\nConvert OT LV USFM files to simple HTML…\n"
	@python convert_OET-LV_to_simple_HTML.py

$(NT_HTML): $(final_NT_USFM) convert_OET-LV_to_simple_HTML.py
	@echo "\n\nConvert NT LV USFM files to simple HTML…\n"
	@python convert_OET-LV_to_simple_HTML.py

$(final_OT_USFM): $(intermediate_OT_USFM) $(SBE) $(wildcard ScriptedOTUpdates/*) $(BTranslit) $(Hebrew)
	@echo "\n\nRun ScriptedBibleEditor on OT USFM files…\n"
	@python ../../ScriptedBibleEditor/Python/ScriptedBibleEditor.py ScriptedOTUpdates -qe

$(final_NT_USFM): $(intermediate_NT_USFM) $(SBE) $(wildcard ScriptedVLTUpdates/*) $(BTranslit) $(Greek) $(Hebrew)
	@echo "\n\nRun ScriptedBibleEditor on NT USFM files…\n"
	@python ../../ScriptedBibleEditor/Python/ScriptedBibleEditor.py ScriptedVLTUpdates -qe

$(intermediate_OT_USFM): $(all_OT_TSV_table) extract_OSHB_OT_to_USFM.py
	@echo "\n\nExtract OT from TSV table to USFM files…\n"
	@python extract_OSHB_OT_to_USFM.py

$(all_OT_TSV_table): $(WLC_OT_TSV_table) $(Clear_Bible_OT_lowfat_TSV) apply_Clear_Macula_OT_glosses.py
	@echo "\n\nApply glosses from Macula to OT (and reorder)…\n"
	@python apply_Clear_Macula_OT_glosses.py

$(WLC_OT_TSV_table): $(short_OSHB_TSV) prepare_OSHB_for_glossing.py WLCHebrewGlosses.txt
	@echo "\n\nExpand columns in OT TSV and add our custom glosses…\n"
	@python prepare_OSHB_for_glossing.py

$(Clear_Bible_OT_lowfat_TSV): $(wildcard ../../Forked/macula-hebrew/lowfat/*.xml) $(WLC_OT_TSV_table) convert_ClearMaculaOT_to_TSV.py
	@echo "\n\nConvert Macula Hebrew from XML files to TSV…\n"
	@python convert_ClearMaculaOT_to_TSV.py

$(Clear_Bible_NT_lowfat_TSV): $(wildcard ../../Forked/macula-greek/Nestle1904/lowfat/*.xml) $(BibleTags_NT_TSV_table) convert_ClearMaculaNT_to_TSV.py
	@echo "\n\nConvert Macula Greek from XML files to TSV…\n"
	@python convert_ClearMaculaNT_to_TSV.py

$(short_OSHB_TSV): $(wildcard ../../Forked/OS-morphhb/wlc/*.xml) convert_OSHB_XML_to_TSV.py
	@echo "\n\nConvert OSHB XML files to TSV…\n"
	@python convert_OSHB_XML_to_TSV.py

$(BibleTags_TSV): $(wildcard ../../Forked/bibletags-usfm/usfm/uhb/*.usfm) $(wildcard ../../Forked/bibletags-usfm/usfm/ugnt/*.usfm) convert_BibTags_USFM_to_TSV.py
	@echo "\n\nConvert BibleTags USFM files to TSV…\n"
	@python convert_BibTags_USFM_to_TSV.py

$(intermediate_NT_USFM): ../../CNTR-GNT/sourceExports/book.csv ../../CNTR-GNT/sourceExports/collation.updated.csv extract_VLT_NT_to_USFM.py
	@echo "\n\nExtract NT from TSV table to USFM files…\n"
	@python extract_VLT_NT_to_USFM.py

cleanBoth: cleanOT cleanNT

cleanOT:
	rm ../intermediateTexts/modified_source_glossed_OSHB_USFM/*.usfm
	rm ../intermediateTexts/glossed_OSHB/all_glosses.morphemes.tsv
	rm ../intermediateTexts/Clear.Bible_lowfat_trees/ClearLowFatTreesAbbrev.OT.morphemes.tsv
	rm ../intermediateTexts/glossed_OSHB/WLC_glosses.morphemes.tsv
	rm ../sourceTexts/rawOSHB/OSHB.original.flat.morphemes.tsv

cleanNT:
	rm ../intermediateTexts/auto_edited_VLT_USFM/*.usfm
	rm ../intermediateTexts/modified_source_VLT_USFM/*.usfm
