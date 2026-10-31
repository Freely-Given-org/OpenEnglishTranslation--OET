# SPDX-License-Identifier: MPL-2.0
"""2026-10-22: mapped exports/navigation and complete HTML passages."""
import collections
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch
import bos_books_codes_py
from BibleOrgSys import BibleOrgSysGlobals
from BibleOrgSys.Formats.USFMBible import USFMBible
from oet_exports import export_passage,native_passages
from oet_html_alignment import align_sections,NativeHTML,render_editorial_brackets
from oet_html_links import scripture_link,retarget_links
from theographic import mapped_verse_metadata


def ref(b,c,v):return b,str(c),str(v),None

def metadata(person,year=''):
    return dict(people=[person] if person else [],peopleGroups=[],places=[],eventsDescribed=[],yearNum=year,timeline='')


class MappingTests(unittest.TestCase):
    def setUp(self):
        BibleOrgSysGlobals.preloadCommonData()
        self.folder=Path(self.enterContext(tempfile.TemporaryDirectory()))

    def bible(self,book,text,profile='OET-LV'):
        usfm=bos_books_codes_py.bos_book_code_to_usfm_abbrev(book).upper()
        (self.folder/(book+'.usfm')).write_text(f'\\id {usfm}\n{text}\n')
        bible=USFMBible(self.folder,givenAbbreviation=profile,versification=profile);bible.load()
        return bible

    def test_ot_metadata_chapter_shift_title_group_and_missing_data(self):
        index={'MAL_4:1':metadata('PTest','-400'),'PSA_51:1':metadata('PDavid')}
        self.assertEqual(mapped_verse_metadata('MAL_3:19',index,'org')['people'],['PTest'])
        for v in (1,2):self.assertEqual(mapped_verse_metadata(f'PSA_51:{v}',index,'org')['people'],[])
        self.assertEqual(mapped_verse_metadata('PSA_51:3',index,'org')['people'],['PDavid'])
        with self.assertRaisesRegex(ValueError,'org.*MAL_3:20.*KJV.*MAL_4:2'):
            mapped_verse_metadata('MAL_3:20',index,'org')
        # A many-to-one annotation join retains each year/person, in order.
        data={'CO2_13:12':metadata('PFirst','1'),'CO2_13:13':metadata('PSecond','2')}
        self.assertEqual(mapped_verse_metadata('CO2_13:12',data,'OET-LV')['yearNums'],['1','2'])

    def test_vref_mapping_and_native_bridge_export(self):
        bible=self.bible('MAL','\\c 3\n\\v 19 fire¦123\n\\v 20 sun¦456')
        text,record=export_passage(bible,'KJV',(ref('MAL',4,1),))
        self.assertIn('fire¦123',text);self.assertNotIn('sun',text)
        self.assertEqual(record['native'],(ref('MAL',3,19),))
        bible=self.bible('ACT','\\c 19\n\\v 40 speech¦10 dismissal¦11')
        for v in (40,41):
            text,record=export_passage(bible,'OET-RV',(ref('ACT',19,v),))
            self.assertIn('Combined passage:',text)
            self.assertIn('speech¦10 dismissal¦11',text)
            self.assertEqual(record['source_coverage'],(ref('ACT',19,40),ref('ACT',19,41)))
        bible=self.bible('MAT','\\c 1\n\\v 1-2 joined¦999\n\\v 3 next¦1000')
        with patch('oet_exports.BOOKLIST_66',['MAT']):rows=list(native_passages(bible))
        self.assertEqual(len(rows),2)
        self.assertIn('Combined passage:',rows[0][1])
        self.assertEqual(rows[0][2]['native'],(ref('MAT',1,1),ref('MAT',1,2)))

    def test_destination_links_and_original_provenance_survive_copy(self):
        native='<a href="../ACT.html#C19V40">Acts 19:40</a><a href="123.html">word</a>'
        result=retarget_links(native,'OET-RV')
        self.assertIn('../ACT.html#C19V40',result);self.assertIn('../ACT.html#C19V41',result)
        self.assertIn('href="123.html"',result)
        original=scripture_link('KJV','OET-LV','MAL','4','1','Malachi 4:1')
        self.assertIn('../MAL.html#C3V19',original)
        copied=retarget_links(original,'OET-RV')
        self.assertIn('../MAL.html#C4V1',copied)
        self.assertIn('data-source-system="KJV"',copied)
        self.assertNotIn('C3V19',copied)
        chapter=scripture_link('KJV','OET-LV','MAL','4',None,'Malachi 4')
        self.assertIn('C3V19',chapter)
        self.assertIn('invalid KJV reference',scripture_link('KJV','OET-LV','JHN','15','44','John 15:44'))

    def test_html_shared_passages_merge_and_words_are_never_duplicated(self):
        bible=self.bible('ACT','\\c 19\n\\v 40 speech¦10 dismissal¦11')
        rv='<div class="BibleText"><div class="rightS1Box"><p>Speech</p></div><p><span id="C19V40">40</span>speech</p><div class="rightS1Box"><p>Dismissal</p></div><p><span id="C19V41">41</span>dismissal</p></div><!--BibleText-->'
        lv='<div class="BibleText"><p><span id="C19V40">40</span><a href="W/10.html">speech</a> <a href="W/11.html">dismissal</a></p></div><!--BibleText-->'
        pairs=align_sections('ACT',rv,lv,bible)
        self.assertEqual(len(pairs),1)
        self.assertEqual(pairs[0][1].count('href="W/10.html"'),1)
        self.assertEqual(pairs[0][1].count('href="W/11.html"'),1)
        self.assertIn('Complete verses are shown together',pairs[0][1])
        NativeHTML('ACT',pairs[0][0]);NativeHTML('ACT',pairs[0][1])
        with self.assertRaisesRegex(ValueError,'mapped native anchors missing'):
            align_sections('ACT',rv,lv.replace('C19V40','C19V39'),bible)

    def test_html_title_and_balanced_slices_with_quoted_markup(self):
        bible=self.bible('PSA','\\c 3\n\\v 1 title¦1\n\\v 2 text¦2')
        rv='<div class="BibleText"><p class="d">title</p><div class="rightS1Box"><p>Section</p></div><p><span id="C3V1">1</span>text</p></div><!--BibleText-->'
        lv='<div class="BibleText"><p id="C3"><span id="C3V1">1</span><a href="W/1.html">title</a> <span id="C3V2">2</span><a title="<em>note</em>" href="W/2.html">text</a></p></div><!--BibleText-->'
        pairs=align_sections('PSA',rv,lv,bible)
        self.assertEqual(len(pairs),2)
        self.assertIn('W/1.html',pairs[0][1]);self.assertNotIn('W/2.html',pairs[0][1])
        self.assertIn('W/2.html',pairs[1][1])
        for rv,lv in pairs:NativeHTML('PSA',rv);NativeHTML('PSA',lv)

    def test_reviewed_absence_preserves_remaining_passage_but_default_stays_strict(self):
        from BibleOrgSys.Reference.BibleVersificationMappings import VersificationMappingError,MappingStatus
        bible=self.bible('NEH','\\c 7\n\\v 67 singers¦11\n\\v 68 camels¦22')
        refs=(ref('NEH',7,67),ref('NEH',7,68),ref('NEH',7,69))
        with self.assertRaises(VersificationMappingError):
            bible.getMappedPassage('OET-RV',refs,expandGroups=True)
        passage=bible.getMappedPassage('OET-RV',refs,expandGroups=True,allowAbsent=True)
        self.assertEqual(passage.mapping.status,MappingStatus.PARTIAL)
        self.assertEqual(passage.absent_source_references,(ref('NEH',7,68),))
        self.assertEqual(passage.native_references,(ref('NEH',7,67),ref('NEH',7,68)))
        self.assertEqual(passage.mapping.requested_references,refs)
        self.assertIn('camels¦22',' '.join(e.getCleanText() for p in passage.portions for e in p.entries))
        with self.assertRaises(VersificationMappingError):
            bible.getMappedPassage('not-a-profile',refs,allowAbsent=True)
        self.assertIn('alignment unavailable',scripture_link('KJV','OET-LV','NEH','7','68','Neh 7:68'))

    def test_ot_tagger_keeps_native_columns_including_leading_note_rows(self):
        import add_tags_to_OT_word_table as tagging
        from types import SimpleNamespace
        class SmallFixture(list):
            def __len__(self):return 381001 # The production whole-table size guard.
        note=['MAL_3:19w0','','note']+['']*18
        word=['MAL_3:19w7','NativeID','w']+['']*18
        word[13]='Test'
        rows=SmallFixture(['header','\t'.join(note),'\t'.join(word)])
        before=list(rows)
        with patch.object(tagging,'state',SimpleNamespace(newWordTable=rows,verseIndex={'MAL_4:1':metadata('PTest','-400')})):
            tagging.associate_Theographic_people_places()
        self.assertEqual(rows[1],before[1])
        self.assertEqual(rows[2].split('\t')[:20],before[2].split('\t')[:20])
        self.assertIn('PTest',rows[2].split('\t')[-1]);self.assertIn('Y-400',rows[2].split('\t')[-1])

    def test_orphan_editorial_bracket_stays_visible_without_malformed_markup(self):
        text='<p>[<a href="W/1.html">who</a>] <a href="W/2.html">tear[s]</a> ]</p>'
        rendered=render_editorial_brackets(text)
        NativeHTML('MAL',rendered)
        self.assertIn(' ]</p>',rendered)
        self.assertEqual(rendered.count('href="W/'),2)


if __name__=='__main__':unittest.main()
