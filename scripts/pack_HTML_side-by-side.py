#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# pack_HTML_side-by-side.py
#
# Script to take the OET-RV and OET-LV HTML files and display them side-by-side
#
# Copyright (C) 2022-2023 Robert Hunt
# Author: Robert Hunt <Freely.Given.org@gmail.com>
# License: See gpl-3.0.txt
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Uses the OET-RV USFM to create the headers
    then takes the pre-existing RV HTML and divides it into section chunks
    then find what verses each chunk contains
    then gets the pre-existing LV HTML and extracts those verses
    then places the related RV and LV chunks in a division
        so they'll display side-by-side.
"""
from gettext import gettext as _
from tracemalloc import start
from typing import List, Tuple, Optional
from pathlib import Path
from datetime import datetime
import logging
import re
import glob
import shutil
import os.path

if __name__ == '__main__':
    import sys
    sys.path.insert( 0, '../../BibleOrgSys/' )
from BibleOrgSys import BibleOrgSysGlobals
from BibleOrgSys.BibleOrgSysGlobals import vPrint, fnPrint, dPrint
from BibleOrgSys.Bible import Bible
from BibleOrgSys.Reference.BibleOrganisationalSystems import BibleOrganisationalSystem
from BibleOrgSys.Misc import CompareBibles


LAST_MODIFIED_DATE = '2023-03-10' # by RJH
SHORT_PROGRAM_NAME = "pack_HTML_side-by-side"
PROGRAM_NAME = "Pack RV and LV simple HTML together"
PROGRAM_VERSION = '0.40'
PROGRAM_NAME_VERSION = '{} v{}'.format( SHORT_PROGRAM_NAME, PROGRAM_VERSION )

DEBUGGING_THIS_MODULE = False


project_folderpath = Path(__file__).parent.parent # Find folders relative to this module
FG_folderpath = project_folderpath.parent # Path to find parallel Freely-Given.org repos
OET_RV_USFM_InputFolderPath = project_folderpath.joinpath( 'translatedTexts/ReadersVersion/' )
assert OET_RV_USFM_InputFolderPath.is_dir()
OET_RV_HTML_InputFolderPath = project_folderpath.joinpath( 'derivedTexts/simpleHTML/ReadersVersion/' )
assert OET_RV_HTML_InputFolderPath.is_dir()
# OET_LV_OT_USFM_InputFolderPath = project_folderpath.joinpath( 'intermediateTexts/auto_edited_OT_USFM/' )
# assert OET_LV_OT_USFM_InputFolderPath.is_dir()
# OET_LV_NT_USFM_InputFolderPath = project_folderpath.joinpath( 'intermediateTexts/auto_edited_VLT_ESFM/' )
# assert OET_LV_NT_ESFM_InputFolderPath.is_dir()
OET_LV_HTML_InputFolderPath = project_folderpath.joinpath( 'derivedTexts/simpleHTML/LiteralVersion/' )
assert OET_LV_HTML_InputFolderPath.is_dir()
OET_HTML_OutputFolderPath = project_folderpath.joinpath( 'derivedTexts/simpleHTML/SideBySide/' )
assert OET_HTML_OutputFolderPath.is_dir()

# EN_SPACE = ' '
EM_SPACE = ' '
# NARROW_NON_BREAK_SPACE = ' '
OT_BBB_LIST = ('GEN','EXO','LEV','NUM','DEU','JOS','JDG','RUT','SA1','SA2','KI1','KI2','CH1','CH2',
                'EZR','NEH','EST','JOB','PSA','PRO','ECC','SNG','ISA','JER','LAM','EZE',
                'DAN','HOS','JOL','AMO','OBA','JNA','MIC','NAH','HAB','ZEP','HAG','ZEC','MAL')
assert len(OT_BBB_LIST) == 39
# NT_BBB_LIST = ('MAT','MRK','LUK','JHN','ACT','ROM','CO1','CO2','GAL','EPH','PHP','COL','TH1','TH2','TI1','TI2','TIT','PHM','HEB','JAM','PE1','PE2','JN1','JN2','JN3','JDE','REV')
NT_BBB_LIST = ('JHN','MAT','MRK','LUK','ACT','ROM','CO1','CO2','GAL','EPH','PHP','COL','TH1','TH2','TI1','TI2','TIT','PHM','HEB','JAM','PE1','PE2','JN1','JN2','JN3','JDE','REV')
assert len(NT_BBB_LIST) == 27
BBB_LIST = OT_BBB_LIST + NT_BBB_LIST
assert len(BBB_LIST) == 66


def main():
    """
    Main program to handle command line parameters and then run what they want.
    """
    BibleOrgSysGlobals.introduceProgram( __name__, PROGRAM_NAME_VERSION, LAST_MODIFIED_DATE )

    global genericBookList
    genericBibleOrganisationalSystem = BibleOrganisationalSystem( 'GENERIC-KJV-ENG' )
    genericBookList = genericBibleOrganisationalSystem.getBookList()

    # Pack RV and LT into simple side-by-side HTML
    pack_HTML_files()
    copy_wordlink_files( OET_LV_HTML_InputFolderPath, OET_HTML_OutputFolderPath ) # The OET-LV has its words linked to the SR GNT
# end of pack_HTML_side-by-side.main


# If you change any colours, etc., may need to adjust the Key above
# . selects class, # is id
SBS_CSS_TEXT = """button#underlineButton { float:right; }

div.container { display:grid; column-gap:0.6em; grid-template-columns:0.85fr 1.15fr; }
div.BibleText { }
div.rightBox { float:right; width:35%; border:3px solid #73AD21; padding:0.2em; }

span.upLink { font-size:1.5em; font-weight:bold; }
span.c { font-size:1.1em; color:green; }
span.cPsa { font-size:1.6em; font-weight:bold; color:green; }
span.v { vertical-align:super; font-size:0.5em; color:red; }
span.cv { vertical-align:super; font-size:0.8em; color:orange; }
span.addedArticle { color:bisque; }
span.addedCopula { color:pink; }
span.addedDirectObject { color:brown; }
span.addedExtra { color:lightGreen; }
span.addedOwner { color:darkOrchid; }
span.added { color:grey; }
span.RVadded { color:dimGrey; }
span.ul { color:darkGrey; }
span.dom { color:Gainsboro; }
span.schwa { font-size:0.75em; }
span.nominaSacra { font-weight:bold; }
span.bk { font-style:italic; }
span.fn { vertical-align: super; font-size:0.7em; color:green; }
span.xref { vertical-align: super; font-size:0.7em; color:blue; }

p.h { font-weight:bold; }
p.rem { font-size:0.8em; color:grey; }
p.shortPrayer { text-align:center; }
p.mt1 { text-align:center; font-size:1.8em; }
p.mt2 { text-align:center; font-size:1.3em; }
p.s1 { margin-top:0.1em; margin-bottom:0; font-weight:bold; }
p.r { margin-top:0; margin-bottom:0; font-size:0.75em; }
p.LVsentence { margin-top:0.2em; margin-bottom:0.2em; }
p.p { text-indent:0.5em; margin-top:0.2em; margin-bottom:0.2em; }
p.q1 { margin-left:1em; margin-top:0.2em; margin-bottom:0.2em; }
p.q2 { margin-left:2em; margin-top:0.2em; margin-bottom:0.2em; }
/* p.m {  } */

a { text-decoration: none; }

/* Book intro (OET-RV only) */
li.intro { margin-top:0.5em; margin-bottom:0.5em; }
p.is1 { font-weight:bold; font-size:1.3em; }
p.is2 { font-weight:bold; }
p.iot { font-weight:bold; }
p.io1 { text-indent:2em; margin-top:0.2em; margin-bottom:0.2em; }
span.ior { font-weight:bold; } /* font-style:italic; */
"""

SBS_JS = """
function hide_show_underlines() {
    console.log('hide_show_underlines()');
    ul_classes = ['ul', 'dom'];
    // ul_colours = ['darkGrey'];
    let btn = document.getElementById('underlineButton');
    if (btn.textContent == 'Hide underlines') {
        console.log('It was hide');
        for (let cl of ul_classes) {
            console.log(`  Hiding ${cl}`);
            let underlines = document.getElementsByClassName(cl);
            for (let i=0; i<underlines.length; i++) {
                if (cl == 'ul') underlines[i].style.color = 'white';
                // else underlines[i].style.visibility = 'hidden';
                else underlines[i].style.display = 'none';
                }
        }
        btn.textContent = 'Show underlines';
    } else {
        console.log('It was show');
        for (let cl of ul_classes) {
            console.log(`  Hiding ${cl}`);
            let underlines = document.getElementsByClassName(cl);
            for (let i=0; i<underlines.length; i++) {
                if (cl == 'ul') underlines[i].style.color = 'darkGrey';
                // else underlines[i].style.visibility = 'visible';
                else underlines[i].style.display = 'revert';
                }
        }
        btn.textContent = 'Hide underlines';
    }
}"""


SBS_BUTTONS_HTML = """<div class="buttons">
    <button type="button" id="underlineButton" onclick="hide_show_underlines()">Hide underlines</button>
</div><!--buttons-->"""

SBS_INDEX_INTRO_HTML = """<!DOCTYPE html>
<html lang="en-US">
<head>
  <title>OET Development Introduction</title>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="keywords" content="Bible, translation, OET, open, English, literal, readers, modern, free">
  <link rel="stylesheet" type="text/css" href="BibleBook.css">
</head>
<body>
  <p><a href="../">Up</a></p>
  <h1>Open English Translation (OET) Development</h1>
  <h2>Very preliminary in-progress still-private test version</h2>
  <h3><b>OT</b> v0.00</h3>
  <p id="Index"><a href="GEN.html">Genesis</a> &nbsp;&nbsp;<a href="EXO.html">Exodus</a> &nbsp;&nbsp;<a href="LEV.html">Leviticus</a> &nbsp;&nbsp;<a href="NUM.html">Numbers</a> &nbsp;&nbsp;<a href="DEU.html">Deuteronomy</a><br>
    <a href="JOS.html">Y<span class="schwa">ə</span>hōshūʼa/Joshua</a> &nbsp;&nbsp;<a href="JDG.html">Leaders/Judges</a> &nbsp;&nbsp;<a href="RUT.html">Rūt/Ruth</a><br>
    <a href="SA1.html">Sh<span class="schwa">ə</span>mūʼēl/Samuel 1</a> &nbsp;&nbsp;<a href="SA2.html">Sh<span class="schwa">ə</span>mūʼēl/Samuel 2</a> &nbsp;&nbsp;<a href="KI1.html">Kings 1</a> &nbsp;&nbsp;<a href="KI2.html">Kings 2</a> &nbsp;&nbsp;<a href="CH1.html">Accounts/Chronicles 1</a> &nbsp;&nbsp;<a href="CH2.html">Accounts/Chronicles 2</a><br>
    <a href="EZR.html">ʼEz<span class="schwa">ə</span>rāʼ/Ezra</a> &nbsp;&nbsp;<a href="NEH.html">N<span class="schwa">ə</span>ḩem<span class="schwa">ə</span>yāh/Nehemiah</a> &nbsp;&nbsp;<a href="EST.html">ʼEş<span class="schwa">ə</span>ttēr/Esther</a><br>
    <a href="JOB.html">ʼYuōv/Job</a> &nbsp;&nbsp;<a href="PSA_index.html">Songs/Psalms</a> &nbsp;&nbsp;<a href="PRO.html">Sayings/Proverbs</a> &nbsp;&nbsp;<a href="ECC.html">Orator/Ecclesiastes</a> &nbsp;&nbsp;<a href="SNG.html">Song of /Solomon</a><br>
    <a href="ISA.html">Y<span class="schwa">ə</span>shaʼ<span class="schwa">ə</span>yāh/Isaiah</a> &nbsp;&nbsp;<a href="JER.html">Yir<span class="schwa">ə</span>m<span class="schwa">ə</span>yāh/Jeremiah</a> &nbsp;&nbsp;<a href="LAM.html">Wailings/Lamentations</a> &nbsp;&nbsp;<a href="EZE.html">Y<span class="schwa">ə</span>ḩez<span class="schwa">ə</span>qēʼl/Ezekiel</a><br>
    <a href="DAN.html">Dāniyyēʼl/Daniel</a> &nbsp;&nbsp;<a href="HOS.html">Hōshēʼa/Hosea</a> &nbsp;&nbsp;<a href="JOL.html">Yōʼēl/Joel</a> &nbsp;&nbsp;<a href="AMO.html">ʼĀmōʦ/Amos</a><br>
    <a href="OBA.html">ʼOvad<span class="schwa">ə</span>yāh/Obadiah</a> &nbsp;&nbsp;<a href="JNA.html">Yōnāh/Jonah</a> &nbsp;&nbsp;<a href="MIC.html">Mīkāh/Micah</a> &nbsp;&nbsp;<a href="NAH.html">Naḩūm/Nahum</a><br>
    <a href="HAB.html">Ḩavaqqūq/Habakkuk</a> &nbsp;&nbsp;<a href="ZEP.html">Ts<span class="schwa">ə</span>fan<span class="schwa">ə</span>yāh/Zephaniah</a> &nbsp;&nbsp;<a href="HAG.html">Ḩaggay/Haggai</a> &nbsp;&nbsp;<a href="ZEC.html">Z<span class="schwa">ə</span>kar<span class="schwa">ə</span>yāh/Zechariah</a> &nbsp;&nbsp;<a href="MAL.html">Mal<span class="schwa">ə</span>ʼākī/Malachi</a></p>
  <!--<p>Whole <a href="OET-RV-LV-Torah.html">Torah/Pentateuch</a>
    (long and slower to load, but useful for easy searching of multiple books, etc.)</p>-->
  <h3><b>NT</b> v0.01</h3>
  <p>Note that the <em>OET</em> places Yōannēs/John before Matthaios/Matthew.</p>
  <p><a href="JHN.html">Yōannēs/John</a> &nbsp;&nbsp;<a href="MAT.html">Matthaios/Matthew</a> &nbsp;&nbsp;<a href="MRK.html">Markos/Mark</a> &nbsp;&nbsp;<a href="LUK.html">Loukas/Luke</a> &nbsp;&nbsp;<a href="ACT.html">Acts</a><br>
    <a href="ROM.html">Romans</a> &nbsp;&nbsp;<a href="CO1.html">Corinthians 1</a> &nbsp;&nbsp;<a href="CO2.html">Corinthians 2</a><br>
    <a href="GAL.html">Galatians</a> &nbsp;&nbsp;<a href="EPH.html">Ephesians</a> &nbsp;&nbsp;<a href="PHP.html">Philippians</a> &nbsp;&nbsp;<a href="COL.html">Colossians</a><br>
    <a href="TH1.html">Thessalonians 1</a> &nbsp;&nbsp;<a href="TH2.html">Thessalonians 2</a> &nbsp;&nbsp;<a href="TI1.html">Timotheos/Timothy 1</a> &nbsp;&nbsp;<a href="TI2.html">Timotheos/Timothy 2</a> &nbsp;&nbsp;<a href="TIT.html">Titos/Titus</a><br>
    <a href="PHM.html">Filēmoni/Philemon</a><br>
    <a href="HEB.html">Hebrews</a><br>
    <a href="JAM.html">Yakōbos/Jacob/James</a><br>
    <a href="PE1.html">Petros/Peter 1</a> &nbsp;&nbsp;<a href="PE2.html">Petros/Peter 2</a><br>
    <a href="JN1.html">Yōannēs/John 1</a> &nbsp;&nbsp;<a href="JN2.html">Yōannēs/John 2</a> &nbsp;&nbsp;<a href="JN3.html">Yōannēs/John 3</a><br>
    <a href="JDE.html">Youdas/Jude</a><br>
    <a href="REV.html">Revelation</a></p>
  <!--<p>Whole <a href="OET-RV-LV-NT.html">New Testament</a>
    (long and slower to load, but useful for easy searching of multiple books, etc.)</p>-->
  <p>See also the <a href="FAQs.html">FAQs</a> and the <a href="Glossary.html">Glossary</a>.</p>
  <h2 id="Intro">Introduction</h2>
  <h3>The Open English Translation of the Bible (OET)</h3>
      <p>The <em>Readers' Version</em> (OET-RV) and the <em>Literal Version</em> (OET-LV)
        side-by-side, together make up the OET.</p>
      <p>So why two versions? Well, many people ask the question:
        <i>Which English Bible translation should I use?</i>
        And often the answer is that there's no single Bible translation which can meet
        all of the needs of the thoughtful reader.
        Why not? It's because we often have two related desires that we need answered:<p>
      <ol><li class="intro">What does the original (Hebrew or Greek) text actually say? and</li>
        <li class="intro">What did the original writer mean? (i.e., What should we understand from it?)</li></ol>
      <p>Our answer has always been that it's best to use <b>two</b> translations—one more <b>literal</b>
        to give a window into the actual Hebrew or Greek words, and one more <b>dynamic</b>
        that's easier for us modern readers to understand—as much to do with our
        totally different cultures as to do with our different languages.</p>
      <p>So the <em>OET</em> gives both side-by-side, and with the advantage that
        both the <em>Readers' Version</em> and the <em>Literal Version</em>
        <b>have been specifically designed to be used together</b> in this way.
        We suggest reading down the <em>Readers' Version</em> on the left,
            and if something stands out and you think in your mind
            “<i>Does it really say that?</i>” or “<i>Could it really mean that?</i>”,
            then flick your eyes across to the <em>Literal Version</em>
            and see for yourself what's really there in the original texts.</p>
      <p>On the other hand if you've been reading the Bible for a few decades already,
        maybe it would be fun to work through the <em>Literal Version</em> to get fresh insight
        into what's actually written there in those original languages.
        It won't be easy reading,
        but it should be insightful as the different wording will require more concentration.</p>
  <h3 id="Goals">Goals and intended audience</h3>
    <p>The OET has the following goals:</p>
    <ul><li class="intro" id="Goal">The primary goal of the <em>Open English Translation</em>
        is <b>to make the Bible more accessible to this current generation</b>
        with the best of a free-and-open easy-to-understand <em>Readers' Version</em>
        alongside a faithful <em>Literal Version</em> so that readers themselves can checkout what was said and what is interpreted.</li>
    <li class="intro">Part of the motivation comes from our work on the street and door-to-door
            where we worked hard to explain the Good News about Jesus
            to people without any church background.
        The <em>Readers' Version</em> strives to replace jargon and terminology that's only
            heard at church with words and phrases that should be understood by modern English speakers.</li>
    <li class="intro" id="LearningGoal">A further goal is to expose more people to some of the background of where our Bibles come from
        and how translators make decisions,
        i.e., <b>to teach</b> a little more about original manuscripts
        and to challenge a little more about English translation traditions
        (some going back to the 1500's)
        that can possibly be improved.</li>
    <li class="intro">Finally, we also want a translation that can be read by Christians with
        many years of Bible reading experience,
        but who might benefit by reading the accounts in slightly different words
        that make it fresh and interesting,
        and hopefully it will provoke deeper thought into what the original
        speakers or writers likely meant.</li>
    </ul>
  <h3 id="Distinctives">Distinctives</h3>
    <p>The OET has the following distinguishing points:</p>
    <ul><li class="intro">An easy-to-understand <em>Readers' Version</em> alongside a very <em>Literal Version</em></li>
    <li class="intro">A generous open license so that the <em>Open English Translation</em> can be
            freely used in any Bible app or website, or printed in your church Bible-study notes
            without even needing to request permission.</li>
    <li class="intro">The <em>Readers' Version</em> speaks like people around you.
        Because the history and legacy of English Bibles now goes back for hundreds of years,
            many things have been carried over that readers don't even realise.
        For example, we all smile at Yoda saying, “Strong is the force.”
        That's because naturally we would say, “The force is strong.”
        So think about “<a href="https://biblehub.com/parallel/lamentations/3-23.htm">Great is your faithfulness.</a>”
        (At least Miles Coverdale improved it in 1535 if you look carefully.)
        But our aim isn't at all to criticise those who came before (because we very-much build on their shoulders)—we
            just want our readers to be able to share the Good News of Jesus the Messiah
            with others, without them thinking that Christians speak like dinosaurs (or Yoda)!</li>
    <li class="intro">The <em>Readers' Version</em> has section headings and cross-references
            and most of the other features that help modern Bible readers.</li>
    <li class="intro">The <em>Readers' Version</em> uses modern units for all measurements (easy to understand and visualise),
            whereas the <em>Literal Version</em> retains the ancient units (useful for historical and symbolic studies).</li>
    <li class="intro">The <em>Readers' Version</em> uses well-known figures of speech,
            or if the original figure of speech is not readily understandable,
            explains the point that the author appears to be trying to express.
        On the other hand, the <em>Literal Version</em> retains the original figurative language
            (even if it's not a figure of speech that we are familiar with).</li>
    <li class="intro"><i>Up</i> and <i>down</i> in the original languages (and thus in the <em>Literal Version</em>)
            refer to <i>uphill</i> and <i>downhill</i>.
        However, in the <em>Readers' Version</em>, <i>up</i> and <i>down</i> are used to refer
            to <i>north</i> and <i>south</i> respectively as per our modern norm.</li>
    <li class="intro">The <em>Readers' Version</em> is less formal than most modern English Bible translations,
            for example, we would use contracted words like <i>we'll</i> and <i>didn't</i>,
            especially when it's in direct speech.
        (Always remember that the Bible was written in the languages of the common people.)</li>
    <li class="intro" id="sectionHeadings">The <em>Readers' Version</em> uses section headings
            which are very helpful to skim through when trying to locate a certain passage.
        However, you'll quickly notice that they are formatted in such a way
            as not to break the flow of the letter or narrative.
        This is to visually help the reader to appreciate the full context
            of the part they're reading,
            and not to ignore the connections with what came before and what follows.<br>
        We've also tried to focus our section headings on principles that are being taught,
            rather than just focusing on the events happening at the time.<br>
        We'll also be providing a list of these section headings that you can quickly skim through
            (and we hope to include extra, alternative headings).</li>
    <li class="intro">Being a 21<span style="vertical-align:super;font-size:0.8em;">st</span> century translation done in an era
        when there is much more effort in general to respect speakers of other languages
        (including the languages of ethnic minorities in our own countries)
        and to pronounce their names and placenames correctly,
        the <em>OET</em> attempts to do the same for Biblical names and placenames.
        (All this is a little complex when we have both Hebrew and Greek versions of names and placenames—more below.)
        Certainly by showing a little more respect for Hebrew names,
            we hope to make this Bible translation a little more “Jew-friendly”.
        If you have difficulty following the names in the <em>Literal Version</em>,
        you can always look across to the <em>Literal Version</em>.
        (Most English readers looking at names in the Bible all the way from <i>Jericho</i> to <i>Jesus</i>
        would have no idea that there's no <b>J</b> letter or sound in either Hebrew or Greek,
        plus there's absolutely no such name as <i>James</i> in the New Testament manuscripts—it's
        a historical accident carried through from an inconsistency by John Wycliffe—see
        <a href="https://www.biblicalarchaeology.org/daily/biblical-topics/bible-versions-and-translations/james-or-jacob-in-the-bible/">this article</a>
        for example.</li>
    <li class="intro">In addition to wanting to get names and placenames more accurate,
        we've also attempted to modernise and simplify the spelling (transliterations) of these names
        to make it easier for readers to pronounce them as they come across them,
        e.g., using <b>f</b> instead of <b>ph</b>, so <i>Epafras</i> instead of <i>Epaphras</i>.
        (Oddly, even traditional English Bible translations surprisingly
        do use <i>Felix</i> and <i>Festus</i>.)</li>
    <li class="intro">With regular words, we've tried to do the opposite,
        i.e., to use less Greek rather than more wherever possible.
        So a word like <i>baptise</i> (which is an adapted transliteration of the Greek verb),
        actually gets translated, so this example becomes <i>immerse</i>.</li>
    <li class="intro"><i>Italics</i> are only used for <em>emphasis</em>, not to indicate <i>added words</i> as historically done in
        older translations due to limitations of the original printing processes.
        The <em>OET</em> fixes the problem where most modern printing uses <i>italics</i> for <em>emphasis</em>
        whereas older Bibles use <i>italics</i> for the words which should actually be <b>deemphasised</b>,
        i.e., the words which actually <b>aren't</b> in the original manuscripts!</li>
    <li class="intro">The English <i>Christ</i> is an adapted transliteration of the Koine Greek word <i>Kristos</i>
            used for the original Hebrew <i>Messiah</i>.
        (It's not Jesus' surname!)
        It seems to make sense to only use one word consistently
            rather than using two words for the same thing
            (just because they came from two different languages),
            so the <em>OET</em> has elected to only use <i>Messiah</i>.
        However, these words actually have a meaning, just as <i>President</i> is not just a title,
            but someone who <i>presides</i> over governmental meetings.
        So going a step further, we have chosen to use the contemporary
            <b>meaning</b> of the word in the <em>Literal Version</em>.
        The original meaning is <i>one who is anointed</i> (by pouring a hornful of oil over them),
            but we use the extended meaning which is <i>one who is selected/chosen (by God)</i>.</li>
    <li class="intro">Most readers living in modern democracies
            have never been familiar with the concept of an ancient king or <i>lord</i>
            who has the power of life and death over them.
        Thus the title <i>Lord Jesus</i> is easily said,
            yet relatively few actually live with Jesus as the lord of their thoughts and actions and daily activities.
        (Just think how many would embarrassingly rush to turn off the video they're streaming
            if Jesus appeared in the room.)
        As a reaction to the word <i>Lord</i> seemingly becoming so cliché for many Christians,
            we use the translation <i>master</i> as a way to get readers to at least
            think a little more about what the concept might mean.
        (The word <i>boss</i> felt a little informal.)</li>
    <li class="intro">The <em>Literal Version</em> tries to add as little as possible
            that's not actually there in the original manuscripts.
        Of course, we add spaces between words so we can read it faster,
            and we add capitals at the start of sentences as per standard, modern English,
        but we don't capitalise words like <i>Kingdom of Heaven</i>
            or even <i>He</i> when it refers to Jesus,
            because the concept of capital and small letters didn't even exist
            when original manuscripts like
            <a href="https://greekcntr.org/manuscripts/data/1G20001.htm">this portion</a> were written.
        (Our policy has more to do with accuracy and education
            than it does with “lack of respect” or any such thing.
        Often this goes against religious tradition of the last few centuries,
            but just because something is traditional,
            does not necessarily mean that it is correct or even helpful.)</li>
    <li class="intro">Most dialects of modern English don't distinguish between <i>you (singular)</i> referring to just one person,
        and <i>you (plural)</i> referring to a group of people.
        However, the original languages clearly distinguish these,
        so in order to indicate this to our readers
        the <em>Literal Version</em> uses <i>you<span class="ul">_</span>all</i> for the plural form
        (although we are aware that some modern dialects now prefer <i>yous</i>).</li>
    <li class="intro">Because the <em>Literal Version</em> so closely follows the original languages,
            it's important to remember that words often don't match one-to-one between languages.
        This is one reason why the <em>OET-LV</em> reads strangely:
            because we try to avoid using different English words if we can;
            knowing that the <em>OET-LV</em> will not be natural English.
        Again, this is because we want the <em>OET-LV</em> to be
            a window into what's actually written in the original languages.
        For fluent English (like in the <em>Readers' Version</em>) the same Greek word
            might require several different translations when used in different contexts.
        For example, the Greek word translated <i>raise</i> in the <em>OET-LV</em>
            would likely require the following changes:
        <ol>
            <li>to <i>raise</i> from sitting, we'd want: <i>stand up</i></li>
            <li>to <i>raise</i> from bed, we'd want: <i>get up</i></li>
            <li>to <i>raise</i> from the grave, we'd want: <i>come back to life</i></li>
            <li>to <i>raise</i> an object, we'd want: <i>lift up</i></li>
            <li>to <i>raise</i> a person, we'd often want: <i>exalt</i> or <i>praise</i></li>
        </ol>
        <small>Alert readers might be aware that there's a play on words here in the gospels.
        When Jesus talked about himself <i>being raised up</i>, it was deliberately ambiguous
            because his hearers didn't understand until right near the end that he was going to be executed.
        So we, looking back in history, know that he was talking about coming back to life,
            but at the time, they were just very confused and didn't understand what he meant.
        But amazingly, as well as referring to his resurrection, <i>raising</i> also refers to his crucifixion
            as the victims on the stakes were also <i>raised</i>. (See <a href="JHN.html#C3V14">John 3:14</a>.)
        Sadly, it's not usually possible to make a translation easy to read and understand in our current times,
            without losing some of the underlying meaning or ambiguities or word-plays that were presented to the original hearers.
        That's exactly why it's good to have <em>two</em> different translations side-by-side!</small></li>
    <li class="intro">These particular pages use British spelling,
        but American spelling will also be available in the future.</li>
    <li class="intro">Our preference in most editions is to place <em>The Gospel according to John</em>
            <b>before</b> <em>Matthew</em>.
        This has a couple of advantages:
        <ol><li class="intro">The Old Testament starts with “In the beginning, Elohim created…”
            and the New Testament starts with “In the beginning was the Messenger…”.</li>
        <li class="intro"><em>Acts</em> ends up right after the first book by its author <em>Luke</em>.</li>
        <li class="intro">It just reminds readers that the order of the “books” in the Bible
            is not set by sacred degree—only by tradition.</li>
        </ol>
        Some do complain that the traditional order of the first four gospel accounts
            represent the lion, the calf, the man, and the eagle of Rev 4:6-7
            which allegedly match with the banners (not described in the Bible) of the four divisions
            of the tribes of Israel mentioned in Numbers 2.</li>
    <li class="intro">Beware of some traps interpreting the <em>Literal Version</em>.
        Because it's not designed to be used alone (but rather alongside the <em>Readers' Version</em>)
        it's <b>much more literal</b> than most other “literal versions”.
        You'll quickly notice lighter colours that mark the deemphasis of words
        that had to be added to make the English sentences even make sense.
        But there's at least two other things that aren't necessarily changed
        in the English <em>Literal Version</em>:
        <ol>
            <li class="intro">Other languages use the negative differently,
                    especially when it's doubled or tripled in the sentence.
                If you don't understand this,
                you could easily think that the original means the opposite of what the words actually appear to say.
                For example the double negative:
                    “You are<span class="ul">_</span> not <span class="ul">_</span>caring<span class="ul">_</span>about
                    no one.” (adapted from Matthew 22:16).
                In natural, fluent English, we would have to reverse the second negative to get the expected meaning,
                    ending up with <i>anyone</i> as you'll find in the <em>Readers' Version</em>.
                But in Greek, the second negative adds emphasis rather than reversing the first negative.
                So our <em>Literal Version</em> shows you the words that are actually there
                    (in the Greek in this case).</li>
            <li class="intro">Other languages may omit (or <i>elide</i>) words which are clearly implied to the original reader,
                but which the modern English reader finds strange,
                e.g., a son may be divided against his father, and a daughter her mother.
                The elided words are “may be divided against”.</li>
        </ol>
        Always check the <em>Readers' Version</em> carefully for how it is translated into modern, idiomatic English
        before jumping to any conclusions of your own about what the original language
        or the <em>Literal Version</em> says or doesn't say.</li>
    </ul>
  <h3 id="Key">Key to symbols and colours in the OET</h3>
    <p>You will notice the the <em>Literal Version</em> looks different from most Bibles that you're used to:</p>
    <ul><li class="intro">Underline/underscore characters: Words joined together by underlines are translated from a single original word,
        e.g., <em>he<span class="ul">_</span>is<span class="ul">_</span>walking</em>.
        Both Hebrew and Greek can express the subject as part of the verb,
        often saying in one word what takes us three.</li>
    <li class="intro">Hanging underline/underscore characters: Word groups with hanging underlines mean that to make natural English,
        we needed to insert the translation of one word into the middle of another,
        e.g., <em>not he<span class="ul">_</span>is<span class="ul">_</span>walking</em> becomes much more natural in English if
        rearranged to <em>he<span class="ul">_</span>is<span class="ul">_</span> &nbsp;not&nbsp; <span class="ul">_</span>walking</em>.
        But we can still figure out from the hanging underlines that the two parts either side of <em>not</em>
        are translated from a single original language word.</li>
    <li class="intro"><span class="addedArticle">Grey</span> words indicate added articles.
        English uses <em>a</em> or <em>the</em> to indicate whether a noun
        is indefinite or definite.
        Other languages don't necessarily work the same way.
        Neither Hebrew nor Greek have a word for English “<i>a</i>”.
        If we have to add an article to make the English sound correct, we indicate this by greying it,
        e.g., <em><span class="addedArticle">the</span> man</em>.
        (We use lighter colours to deemphasise added words like these rather than using <i>italics</i> like most Bibles,
        because apart from Bibles, <i>italics</i> are mostly used these days for emphasis.)</li>
    <li class="intro"><span class="addedCopula">Light pink</span>: A copula is a word that links a subject and its complement (or description),
        e.g., the word <i><span class="addedCopula">is</span></i> in the sentence <i>The house <span class="addedCopula">is</span> white.</i>
        Other languages don't necessarily work the same way and can say things like
        <i>White the house.</i>
        Added copulas are marked with this <span class="addedCopula">light colour</span>.</li>
    <li><span class="addedDirectObject">Light brown</span>: Certain English verbs require a direct or indirect object.
        Think of the difference between <i>He said, blah, blah</i> and <i>He told, blah, blah</i>.
        The second one feels like it requires something like <i>He told <span class="addedDirectObject">him</span>, blah, blah</i>.
        Added direct and indirect objects are marked with
        a <span class="addedDirectObject">light colour</span>.</li>
    <li class="intro"><span class="addedExtra">Light green</span>:
        In other languages it may be possible to say something
        like <i>The having<span class="ul">_</span>fallen</i>….
        In English, we must say something like
        <i>The <span class="addedExtra">one</span> having<span class="ul">_</span>fallen</i>…
        or <i>The <span class="addedExtra">person</span> having fallen</i>….
        If the article and verb are marked as <b>plural</b> in the source language,
            we may be able to say
            <i>The <span class="addedExtra">ones</span> having<span class="ul">_</span>fallen</i>….
        If the article is marked as feminine in the source language, we may be able to say
            <i>The <span class="addedExtra">female one</span> having<span class="ul">_</span>fallen</i>….
            or <i>The <span class="addedExtra">woman</span> having<span class="ul">_</span>fallen</i>….
        Added words like this are marked with this <span class="addedExtra">light colour</span>.</li>
    <li class="intro"><span class="addedOwner">Light purple</span>: If we have an original construction like <i>God spoke by son</i> (from Heb 1:2),
        in English we need to add a word like <i>God spoke by <span class="addedArticle">the</span> son</i> or <i>God spoke by <span class="addedOwner">his</span> son</i>.
        In the latter case (where we don't just choose an article like <i><span class="addedArticle">the</span></i>),
        we mark these added words with this <span class="addedOwner">light colour</span>.</li>
    <li class="intro"><span class="added">Light orange</span>: Other added words not in the above categories are marked with this <span class="added">light colour</span>.</li>
    <li class="intro">All of this colouring is to be completely open by helping the reader to be able to see where the translators have chosen to
        add words to the Hebrew or Greek in order to make the English sound slightly better,
        even though this has been kept to an absolute minimum in the <em>Literal Version</em>.</li>
    <li class="intro"><span class="nominaSacra">Bold text</span>: In the earliest copies of the original Koine Greek manuscripts,
        it appears that the scribes marked a small set of words that they considered
        to refer to <span class="nominaSacra">God</span>.
        (These markings are known as <a href="https://en.wikipedia.org/wiki/Nomina_sacra"><em>nomina sacra</em></a>
        or <em>sacred names</em>.)
        Other Bible translations do not indicate these special markings,
        however in the <em>Literal Version New Testament</em> we help the reader by making
        these marked words <span class="nominaSacra">stand out</span>.</li>
    </ul>
    <p>You will notice the the <em>Readers' Version</em> also looks different from most Bibles that you're used to:</p>
    <ul><li class="intro">Sometimes the <em>Readers' Version</em> adds words
            that definitely aren't in the original text, but are included to help
            our readers understand what was probably being meant.
        We put these words in a <span class="RVadded">lighter colour</span>
            in order to be completely transparent about our translation decisions.
        We also do this to encourage our readers to actually actively think about what
            the original authors were trying to express to their listeners/readers.</li>
    <li class="intro">Where it is determined that a group of words was either definitely or most likely
        not in the original manuscripts (autographs),
        they are omitted in the <em>OET</em> without any notes
        but a <b>≈</b> symbol is inserted to show that the decision was intentional and not just an accidental omission.
        These manuscript decisions were mostly made by the authors of the two main works that we relied on to translate
        the <em>OET</em> from—see the acknowledgements below for more details.)</li>
    <li>You might also find more information in the <a href="FAQs.html">FAQs</a>
        and/or in the <a href="Glossary.html">Glossary</a>.</li>
    </ul>
  <h3 id="Names">Biblical names</h3>
    <p>As mentioned above, the <em>OET Literal Version</em> goes out of its way
        to help English speakers to be able to pronounce Biblical names more correctly.
        Because our English Bible traditions have often come from Hebrew through Koine Greek
        through Latin with Germanic influence into modern English,
        what we consider as Biblical names are sometimes quite far from reality.
        Since most of us prefer it when people pronounce our names correctly,
        we have made our best attempt at showing the same respect to Biblical characters.
        Of course different languages have different sets of sounds
        and also pronounciations have changed over the millenia
        (think how much our languages have changed in the last few <em>decades</em>)
        so we will never get perfect pronounciations,
        but we'll do better than our traditional Bible translations.</p>
    <p>As a general rule, even if you started to think of the letter <i>J</i> in
        Bible names like the Germans or the Dutch (the two languages closest to English)
        pronounce <i>Ja</i> (as <i>Ya</i>),
        you'd already be taking a big step towards getting Biblical names more correct.
        (This deviation is not any kind of conspiracy—simply
        an unfortunate accident of history and continuous language change.)<p>
    <p>In the New Testament, the situation is already complicated by the fact that
        Old Testament (Hebrew) names have been written as Greek-speakers would think of them.
        So English <i>Jesus</i>
        (which you now realise should be pronounced more like <i>Yesus</i>
        as there's no <i>j</i> sound in either Hebrew or Greek)
        is actually more like <i>Yaysous</i> in Greek.
        But it's likely that his “parents” (using Hebrew or the related Aramaic/Syrian language at the time)
        actually named the child something more like <i>Y<span class="schwa">ə</span>hōshūʼa</i>
        (from which we get <i>Joshua</i>).
        So which name should we call him in the text?
        Because the New Testament manuscripts are written in Koine Greek,
        we have chosen to give preference to the Greek forms of the names in the New Testament.
        However, the first time a name is used, we show both forms
        like <i>Yaʸsous/(Y<span class="schwa">ə</span>hōshūʼa)</i>.
        Where the name is repeated nearby, we'll only show the Greek form like <i>Yaʸsous</i>.
        (Again, it's an accident of history that English speakers will name a child <i>Joshua</i>,
        but would not name him <i>Jesus</i> when they're really just the same name in different forms.
        Speakers of languages with Spanish influence don't have that same hesitation,
        so <i>Jesus</i> is a common name in South America for example.)
    <p>Note that where Hebrew or Greek transliterations are given,
        English speakers will have the most success pronouncing these names if you
        look up the pronounciation of the five “pure” Spanish vowels in your search engine.
        Individual vowels should be pronounced in this way,
        e.g., each of the four vowels in <i>Eleazar</i>.</p>
    <p>Macrons (overlines over the vowels, like <i>ē</i> or <i>ō</i>) indicate lengthened vowels,
        so the pronounciation is the same as the Spanish vowels,
        but just prolonged.
        (If you're wondering which syllable to put the stress/emphasis on,
            it'll often be one of the ones with a long vowel.
        We decided not to indicate stress on the names
            or there would have been even more marks and squiggles on the letters!)</p>
    <p>The vowel <a href="https://en.wikipedia.org/wiki/Schwa">schwa</a> <i><span class="schwa">ə</span></i>
        (in names that come from Hebrew with <a href="https://en.wikipedia.org/wiki/Shva">shva</a>)
        should be regarded as a fleeting (very short and unstressed), neutral vowel
        which is the minimal vowel required to linguistically join the surrounding consonants
        e.g., in <i>Y<span class="schwa">ə</span>hūdāh</i> (Judah).</p>
    <p>Dipthongs (e.g., <i>ai</i>, <i>au</i>, <i>ei</i>, <i>oi</i>, <i>ou</i>)
        are a limited set of two vowels,
        where one vowel glides into the other,
        so even though the spelling of a dipthong is two letters,
        together they are the centre of only one syllable.
        Note that we use <i>aʸ</i> for Greek letter (eta),
        because it's actually only one letter, not a dipthong,
        even though it's pronounced very much like <i>ai</i>.<p>
    <p>We use the symbol ʼ to mark a <a href="https://en.wikipedia.org/wiki/Glottal_stop">glottal stop</a>
        which is the sound that some UK speakers put in the middle of the word <i>butter</i> (baʼa),
        so <i>Abraʼam</i> (from the Greek) is three distinct syllables—those
        two <i>a</i>'s side-by-side should not be made into a long <i>ā</i>.</p>
  <h3 id="Language">Language and words</h3>
    <p>As mentioned in our <a href="#Goals">Goals above</a>, two of
            our goals relate to the kind of language that the Bible is translated into.
        Here are some of the changes:</p>
    <ul><li class="intro" id="genitives">It's common in the original Biblical languages
            for possessive pronouns to follow the head noun,
            i.e., phrases like ‘the house of Zechariah’,
            or even ‘the house of the father of me’.
        Of course, we have shorter ways of saying those in modern English.
        But consider ‘the kingdom of God’ or ‘the son of man’.
        Could there be more up-to-date ways to express terms like this?
        Certainly we've become so accustomed to phrases like those in the church context
            that we forget that others don't talk like that.
        But that doesn't mean that God wouldn't want us to have the scriptures
            in the language that we actually speak.</li>
    </ul>
  <h3 id="Learning">Learning</h3>
    <p>As mentioned in our <a href="#Goals">Goals above</a>, one of
        our main goals is to <a href="#LearningGoal">educate</a> our readers about how we get our Bibles.
        Here are some of the main points:</p>
    <ul><li class="intro" id="chaptersAndVerses">Biblical names are often very mangled in English translations.
            We've already covered this extensively <a href="#Names">above</a>.</li>
        <li class="intro">The <em>Open English Translation</em> makes it possible to learn how Bible translation is done.
            This is because reading the <em>Literal Version</em> gives you a good insight into
                what's actually written in the original manuscripts.
            Then you can read the same passage in the <em>Readers' Version</em>
                or your favourite other translation,
                and you'll get a good idea of the rearranging and interpreting that
                Bible translators have to do to get good, understandable translations
                in any modern language.</li>
        <li class="intro">Some editions of the OET have the “books” in different orders
                and in different combinations.
            Remember that different Bible originals were originally written on scrolls
                and weren't combined into a <a href="https://en.wikipedia.org/wiki/Codex">book form</a> similar to
                what we're accustomed to until many centuries later.
            But of course, the individual scrolls could easily be placed in a different order.
            The traditional <a href="https://en.wikipedia.org/wiki/Hebrew_Bible">Hebrew Bible</a>
            not only has what we typically refer to as the <i>Old Testament</i> “books” in a different order,
            they also have different names, are grouped into different categories,
            and are combined/separated into a different number of “books”.
            Most readers of Bibles from the West have no idea that Ezra and Nehemiah
                describe some of the latest Old Testament events as far as timelines go.</li>
        <li class="intro">Chapter and verse divisions were not in the original manuscripts and came
                <a href="https://en.wikipedia.org/wiki/Chapters_and_verses_of_the_Bible">many centuries later</a>.
            We have deliberately tried to make chapter and verse markers as small as we can,
                as we actively discourage our readers to get into bad habits like
                reading “a chapter a day” or quoting “a verse”,
                as chapter and verse breaks are not always in the most sensible places.
            We teach that chapter and verse numbers are good ways to locate
                (or in computer terminology to “index”) a passage,
                but should not be thought of as “containers” of words.
            For example, instead of saying,
                “The verse at <a href="https://biblehub.com/1_corinthians/3-21.htm">1 Corinthians 3:21</a>
                says that all things are ours.”,
            consider saying something more like,
                “As Paul wrote in his first letter to those at the church in Corinth
                and which we can read starting at chapter 3, verse 21…”
            You see, those words in verse 21 stop right in the middle of sentence.
            Verses don't <i>say</i> anything, and
                we shouldn't be guilty of quoting short texts out of context.</li>
    </ul>
  <h3 id="Acknowledgements">Acknowledgements</h3>
    <p>A work like this could not be done with building on the work of so many that have gone before, including:</p>
    <ul><li class="intro">The creator God who communicates with us in various ways,
        but who specifically inspired the writing of the Scriptures
        and caused them to be preserved throughout the millenia
        despite the best efforts of some who tried to destroy them.</li>
    <li class="intro">Those who took the time to write down their interactions with God and his messengers,
        beginning with Moses and those before him who wrote down their experiences even though making the writing materials was so much work,
        all the way through to the disciples and others who wrote of their interactions with Yaʸsous the Messiah, and the Holy Spirit.</li>
    <li class="intro">Those who faithfully copied and carefully stored those manuscripts over the centuries
        and thus allowed the works of the original writers to be preserved for us to translate.</li>
    <li class="intro">Those who collected, preserved, photographed and digitized, and transcribed those manuscripts
        so that we could have access to them.</li>
    <li class="intro">Those who studied the variations in those copies and helped us to get the best evaluations of
        which words were most likely present in the original manuscripts (<a href="https://en.wikipedia.org/wiki/Autograph">autographs</a>).
        For the (mostly) Hebrew Old Testament, we are especially reliant on the team work
        of <a href="https://hb.OpenScriptures.org/">Open Scriptures</a>, given to the world under a generous open licence.
        For the Greek New Testament, we are especially reliant on the Statistical Restoration work
        of the <a href="https://GreekCNTR.org">Center for New Testament Restoration</a>
        which is also given to the world under a generous open licence.</li>
    </ul>
  <h3 id="Status">Status</h3>
    <p>English sentences have more limitations on their word order than Greek sentences do.
        So any word-for-word Greek literal translation has to be reordered to be readable in English.
        Currently, the words in the following <em>Literal Version</em> books (just over 50% of the NT) have been mostly reordered:
        <b>Mat, Mark, Luke, John, Acts, 1 Peter, 2 Peter, 3 John, and Jude</b>,
        leaving the following books which have not yet been reordered at all
        and will therefore be even harder to read in this preliminary <em>Literal Version</em>:
        Rom, 1&2 Cor, Gal, Eph, Php, Col, 1&2 Thess, 1&2 Tim, Titus, Phlm, Heb, and 1&2 John.</p>
    <p>After completing sentence reordering and fixing capitalisation and punctuation,
        we then plan to do more investigation into word concordance.
        For example, if an original language word can have multiple meanings,
        we want to indicate in the <em>OET Literal Version</em> where a
        translator has already made that interpretation.</p>
  <h3 id="Feedback">Feedback</h3>
    <p>These web pages are a very preliminary preview into a work still in progress.
        The <em>OET Literal Version</em> is not yet finished, and not yet publicly released,
        but we need to have it available online for easy access for our checkers and reviewers.
        If you're reading this and notice problems or issues,
        please do contact us by <a href="mailto:Freely.Given.org@gmail.com?subject=OET SBS Feedback">email</a>.
        Also if there's something that we didn't explain in this introduction, or didn't explain very well.
        Thanks.</p>
  <p>See also the <a href="FAQs.html">FAQs</a> and the <a href="Glossary.html">Glossary</a>.</p>
  <p>HTML last updated: __LAST_UPDATED__</p>
</body></html>
"""
assert SBS_INDEX_INTRO_HTML.count('‘') == SBS_INDEX_INTRO_HTML.count('’'), f"Why do we have {SBS_INDEX_INTRO_HTML.count('‘')=} and {SBS_INDEX_INTRO_HTML.count('’')=}"
assert SBS_INDEX_INTRO_HTML.count('“') == SBS_INDEX_INTRO_HTML.count('”'), f"Why do we have {SBS_INDEX_INTRO_HTML.count('“')=} and {SBS_INDEX_INTRO_HTML.count('”')=}"
SBS_INDEX_INTRO_HTML = SBS_INDEX_INTRO_HTML.replace( "'", "’" ) # Replace hyphens
assert "'" not in SBS_INDEX_INTRO_HTML

SBS_FAQ_HTML = """<!DOCTYPE html>
<html lang="en-US">
<head>
  <title>OET Development FAQs</title>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="keywords" content="Bible, open, translation, OET, English, literal, readers, modern, FAQ, free">
  <link rel="stylesheet" type="text/css" href="BibleBook.css">
</head>
<body>
  <p><a href="../">Up</a></p>
  <h1>Open English Translation (OET) Development</h1>
  <h2>Frequently Asked Questions (FAQs)</h2>

  <h3 id="sectionHeadings">Why are section headings in boxes in the <em>Readers' Version</em>?</h3>
  <p>As explained in the <a href="index.html#sectionHeadings">Introduction</a>,
        many other English Bible translations break the text and put section headings right across the column.
    This can tend to encourage the reader to read the text in unnatural chunks
        that were never divided by the author.
    The <em>OET</em> on the other hand wants to educate readers that the narratives
        and prophecies and letters, etc., were written as contiguous documents.
    Hence our section headings are designed help the modern reader,
        yet not to break the flow of the text any more than necessary.</p>

  <h3 id="paraphrase">Is the <em>Readers' Version</em> a paraphrase?</h3>
  <p>Well, it's close, in fact you could debate all day about
        what is a modern, fluent translation and what is a paraphrase.
    The short answer is that we don't regard the <em>OET-RV</em> as a paraphrase,
        but rather as a modern English translation.
    Our goal with the <em>OET-RV</em> is to take both the words and cultural background
        of the original authors, and express the meaning in the modern language of our generation.
    We've tried to avoid <i>Bible jargon</i> (words that you'd only hear in church),
        and to think carefully about how we might explain it on the street.
    So we've done the hard work for you to make the Bible accessible
        and understandable to the average person.
    And always remember that the <em>OET</em> provides a <em>Literal Version</em>
        that's intended be referred to alongside the <em>Readers' Version</em>
        if you'd really like a word-for-word rendering of the Hebrew or Greek.
    (Having both side-by-side does mean that we were able to break away from ancient/traditional Bible wording
        and think carefully about how we say things these days.)</p>

  <h3 id="informal">Why does the <em>Readers' Version</em> seem so informal?</h3>
  <p>Oh, that probably means that you're already accustomed to more traditional Bible translations
        that sometimes propogate decisions made in the 1500s by William Tyndale,
        or even back in the 1300s by John Wycliffe.
    Now those early English translators did many things very well,
        and we're not here to criticise more modern English translations either,
        but nevertheless it's a sad fact that established traditions
        can make it hard for anyone to make improvements.
    For example, most Christians don't even blink at the title often printed on Bible covers: “God's Word”.
        That's because in Christian circles, ‘word’ often means ‘statement’, ‘account’, or ‘message’.
        Only someone on the street might wonder which ‘word’ it means.
        (Generally these days, a ‘word’ is something on a page like this one.)
    It's because we've become so accustomed to this unusual or quaint (or archaic?) use of language
        that a Bible that actually uses natural English sounds so ‘informal’ to many readers.</p>

  <h3 id="bias">Is the <em>Open English Translation</em> theologically biased?</h3>
  <p>Ha, we don't think so, but if you find any slip-ups,
        please do contact us.
    Certainly we will have lost some readers by replacing ‘baptism’ (transliterated from the Greek word)
        with ‘immersion’, but that's primarily a translation decision
        to use the regular meaning of the word rather than to put Greek into our English.
    We certainly don't have any intentional theological agenda in creating the <em>OET</em>
        other than trying to use as little as possible of the language and terms
        that you would only hear in church circles
        and which don't correspond with how other people would normally talk in the 2020s.<br>
    In other words, the <em>OET</em> is aimed at sharing the Good News
        with non-churched people without having to speak ‘Church English’ (or <i>jargon</i>) to them.
    A side-effect is to express the message of the Biblical texts with fresh phrasing
        that's different from many traditional English translations
        and thus encourage (or maybe even, <i>shock</i>) regular Bible readers
        into seriously thinking about what the original writers were trying to communicate.</p>

  <h3 id="bold">What are the bolded words in the <em>Literal Version</em>?</h3>
  <p>As explained in the <a href="index.html#Key">Key</a>, the bold text
          indicates the use of <em>Nomina Sacra</em> on the original manuscripts.
    These are special markings and abbreviations done by the scribes,
        and in the earliest manuscripts, highlight words that are assumed to relate to God.</p>

  <h3 id="uphill">Why does the <em>Literal Version</em> have uphill and downhill everywhere?</h3>
  <p>In our culture, when we go <i>up</i> somewhere, it usually means to go north.
    (Other cultures typically use ‘up’ and ‘down’ for ‘uphill’ and ‘downhill’,
        or ‘upstream’ and ‘downstream’, etc., depending on the common modes of travel.)
    The <em>LV</em> overtranslates <i>uphill</i> and <i>downhill</i>
        in order to help our readers avoid misunderstanding the cultural cues.</p>
  <p>And just a bonus tip: Most modern maps of our countries or of the world
        have north at the top.
    However, most maps from Biblical times had the east at the top!
    (This actually makes quite a bit of sense as we're all rapidly hurtling
        towards the east as our planet spins us.)</p>

  <h3 id="baptise">Why is the word <i>baptise</i> missing from the <em>OET</em>?</h3>
  <p>Ha, the short answer is that <i>baptise</i> is a Greek word
        and the “ET” in <em>OET</em> stands for <b>English Translation</b>
        (so we try to use English words, not Greek ones).</p>
  <p>The long answer is that the word <i>baptise</i> is not a translation
        of the Greek word βαπτίζω (baptizo), but just a transliteration.
    In other words, it was an invented English word
        that Bible readers have gotten used to in their jargon,
        but which isn't used outside of religious contexts.
    However, the Koine Greek word means “to dip, dunk, immerse, or sink”
        (but certainly doesn't mean “to sprinkle”).
    So the <em>Open English Translation</em> is one of the
        <a href="https://biblehub.com/parallel/matthew/3-11.htm">very few</a>
        to actually translate the word.</p>

  <h3 id="chapterCount">How many chapters are there in the Bible?</h3>
  <p>Well, it depends on which Bible you're asking about,
        but the <em>OET</em> has <b>929</b> chapters in the “Old Testament” and
        <b>260</b> in the “New Testament”, so a total of <b>1,189</b> chapters.</p>
  <p>And if you're wondering, the <em>OET</em> has over <b>23,000</b> verses in the “Old Testament” and
        very close to <b>8,000</b> in the “New Testament”, so a total of over <b>31,000</b> verses.
    <small>(It's hard to count exact numbers of verses in a modern Bible translation,
        because some verse numbers are still there but don't match any text in the older original texts,
        so don't actually have any content in the translation.)</small></p>
  <p><a href="index.html#chaptersAndVerses">Note</a> that the <em>OET</em>
        tries to downplay the use of chapters and verses
        as chapters are artificial and sometimes quite unnatural breaks in the flow of the text,
        and verse breaks are sometimes even worse—often plonked right in the middle of a sentence.</p>

  <h3 id="similar">Which other translations are the closest to the <em>OET</em>?</h3>
  <p>Any English Bible translation which contains <i>Literal</i> in its name
        is probably close to the <em>OET-LV</em>.
    However, the <em>OET-LV</em> is probably more literal in a sense
        because most other <i>Literal</i> translations are designed to be easy to read.
        whereas the <em>OET-LV</em> is mostly designed as a reference tool for readers of the <em>OET-RV</em>.</p>
  <p>The <i>Contemporary English Version (CEV)</i> and then the <i>New Living Translation (NLT)</i>
        are probably the closest to the <em>OET-RV</em>.
        But the <em>OET-LV</em> goes out of its way to remove church jargon more than
            most other contemporary English Bible translations.</p>

  <h3 id="uW">Are the <em>OET-LV</em> and <em>OET-RV</em> replicating what uW is doing with the <em>ULT</em> and <em>UST</em>?</h3>
  <p>No, not at all.</p>
    <ol><li class="intro">The <a href="https://door43.org/u/unfoldingWord/en_ult/">unfoldingWord Literal Text</a>
            is not as literal as the <em>OET Literal Version</em>.
        The <em>ULT</em> is designed to be translated by those who don't have English as their first language,
            whereas the <em>OET-LV</em> is quite a technical translation aimed at well-educated, native English speakers.</li>
    <li class="intro">The <a href="https://door43.org/u/unfoldingWord/en_ust/">unfoldingWord Simplified Text</a>
            is again designed for Bible translators don't have English as their first language.
        The <em>UST</em> is a specialist translation tool that removes all figures of speech and passive constructions
            in order to help Bible translators access the meaning to translate into their languages.
        On the contrary, the <em>OET Readers' Version</em> is aimed at the average 2020's English speaker on the street
            (and certainly contains passive constructions and figures of speech).</li>
    </ol>

  <h3 id="qualifications">Don't Bible translations have to be done by seminary professors?</h3>
  <p>It's certainly true that many people these days think that any respectable Bible translation
        must be done by Bible college or seminary or university professors
        with advanced degrees in Biblical languages and
        with decades of teaching experience in those institutions.
    Well, you already have a wide choice of English Bible translations that would fit that description
        but one of the main distinctives and benefits of the <em>Open English Translation</em>
        is that it's <b>not</b> done by those kinds of people—
        rather the rendering of the text is done by those who have worked on the street
        and in public schools and in prison and have expertise at
        explaining the teaching of our saviour
        to many people who have never heard this good news before.</p>
  <p>That's not to criticize or show any disrespect to those learned people
        who write Bible dictionaries and Bible commentaries
        and work on the committees of Bible translation projects.
    It's just that we need them to carefully check our work
        and offer corrections and improvements,
        but the <em>OET</em> speaks quite a different dialect of English than them.</p>

  <h3 id="committee">Isn't a large committee needed to create a Bible translation?</h3>
  <p>John Wycliffe (1300s) and William Tyndale (1500s) were primarily responsible
        for two of the earliest English New Testament translations,
        along with Martin Luther (1500s) who translated the Bible into
        what became ‘standard German’.
    It may also be noted that the most powerful figures in the churches at that time
        generally (and sometimes violently) resisted having the scriptures
        translated into the ‘vulgar’ (ordinary) languages of the less-educated people.
    (You can find other examples of Bible translations mostly associated with a
        single translator <a href="https://en.wikipedia.org/wiki/Bible_translations#Reformation_and_Early_Modern_period">here</a>.)</p>
  <p>After that time, many Bible translations were done in major world languages
        by men such as William Carey (India, 1800s) and many others.</p>
  <p>In more recent times, you might be familiar with the J.B.Phillips (mid-1900s)
        and Kenneth Taylor (Living Bible, 1971) as well as many others.</p>
  <p>The <em>Open English Translation</em> <b>follows a long history of
        individuals taking the initiative to translate the Bible</b>
        into a particular segment of the languages they worked in.</p>

  <h3 id="Feedback">Feedback</h3>
    <p>These web pages are a very preliminary preview into a work still in progress.
        The <em>OET</em> is not yet finished, and not yet publicly released,
        but we need to have it available online for easy access for our checkers and reviewers.
    If you're reading this and have questions that aren't discussed here,
        please do contact us by <a href="mailto:Freely.Given.org@gmail.com?subject=OET FAQs">email</a>.
    Also if there's something that we didn't explain in these FAQs, or didn't explain very well.
    Thanks.</p>
  <p>See also the <a href="index.html#Intro">Introduction</a> and the <a href="Glossary.html">Glossary</a>.</p>
  <p>HTML last updated: __LAST_UPDATED__</p>
</body></html>
"""
assert SBS_FAQ_HTML.count('‘') == SBS_FAQ_HTML.count('’')
assert SBS_FAQ_HTML.count('“') == SBS_FAQ_HTML.count('”')
SBS_FAQ_HTML = SBS_FAQ_HTML.replace( "'", "’" ) # Replace hyphens
assert "'" not in SBS_FAQ_HTML
assert '--' not in SBS_FAQ_HTML

SBS_GLOSSARY_HTML = """<!DOCTYPE html>
<html lang="en-US">
<head>
  <title>OET Development Glossary</title>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="keywords" content="Bible, open, translation, OET, English, literal, readers, modern, glossary, free">
  <link rel="stylesheet" type="text/css" href="BibleBook.css">
</head>
<body>
  <p><a href="../">Up</a></p>
  <h1>Open English Translation (OET) Development</h1>
  <h2>Glossary</h2>
  <p>This page contains words which need further explanations.
    <br><br></p>

  <h3 id="genitive">of</h3>
  <p>This little explanation is placed at the top (out of alphabetical order),
        because it's quite a wide issue that affects quite a bit
        of the way that the <em>OET</em> phrases things.</p>
  <p>First a little explanation:
    In the New Testament Greek there's a grammatical construction
        (called the <i>genitive</i>, and it's marked with suffixes on the words involved)
        that allows the source or possessor of a noun to be expressed,
        e.g., to say the ‘the house of God’ or ‘the right_hand of_him’ or
        ‘the God of_the fathers of_us’.
    Note that the source or possessor typically <b>follows</b> the head noun in Greek.
    (You will see these kinds of expressions a lot in the <em>OET LV</em>
        because the Literal Version intentionally tries to follow
        each word of the Koine Greek very closely.)</p>
  <p>Note also that <i>of</i> phrases can be ambiguous,
        such as ‘the love of God’
        (which would require clues from the surrounding context to know
        if it's talking about <b>someone's love for God</b> or
        <b>the love that God has</b> for someone or something).</p>
  <p>You should also note that in regular, modern English as spoken in the public arena,
        we tend to put possessives <b>before</b> the head noun,
        so taking the above examples we might get ‘God's house’, ‘his right hand’,
        and ‘the God of our fathers’ (or even ‘our fathers' God’).</p>
  <p>However, because of the ways that both Bible translation and English itself
        have evolved over the centuries,
        our Bibles tend to have lots of literal phrases that might
        sound unnatural to newcomers, but long-time Bible readers
        have become so accustomed to them that we tend to fail to even notice
        their unnatural and/or archaic nature.</p>
  <p>The following extracts are all taken from
        <a href="https://BibleHub.com/niv/mark/1.htm">Mark 1</a> out of the
        <a href="https://BibleHub.com/niv/version.htm">NIV Bible</a>
        that was first translated in 1973, and then revised in 1978, 1984,
        and, more recently, in 2011:</p>
  <ul>
    <li>1:1 Son <b>of</b> God (cf. the more natural: God's Son)</li>
    <li>1:14 the good news <b>of</b> God (cf. the good news about/from God???)</li>
    <li>1:15 the kingdom <b>of</b> God (cf. God's kingdom)</li>
    <li>1:16 the Sea <b>of</b> Galilee (cf. the Galilee Sea, or Lake Galilee)</li>
    <li>1:19 son <b>of</b> Zebedee (cf. Zebedee's son)</li>
    <li>1:22 the teachers <b>of</b> the law (cf. the law teachers)</li>
    <li>1:24 Jesus <b>of</b> Nazareth (cf. Jesus from Nazareth)</li>
    <li>1:24 the Holy One <b>of</b> God (cf. God's Holy One, or the Holy One from God???)</li>
    <li>1:28 the whole region <b>of</b> Galilee (cf. whole Galilee region)</li>
    <li>1:29 the home <b>of</b> Simon and Andrew (cf. Andrew and Simon's home)</li>
  </ul>
  <p>The aim here is not to criticise the NIV,
        and certainly if you compared Mark 1 with the KJV
        you'd find many more examples there that have been made more natural in the NIV.
    Rather <b>we're just trying to explain why the <em>OET RV</em> might
        sound quite informal</b> or even ‘colloquial’ to you—<b>it's because
        we've made an effort to translate the Bible into our own language
        that we speak every day</b>—not the quaint sounding language
        of the literal Greek or six-hundred year old English.</p>
  <p>And if you didn't read our <a href="index.html#Intro">introduction</a> yet,
        <b>the reason that we've wanted to translate the Bible into
        our own modern English is that we want to make it easier for
        you to share it with others</b>.</p>

  <p><br>
    The remainder of these glossary words are listed in English alphabetical order…
    <br><br></p>

  <h3 id="angel">angel, messenger</h3>
  <p>The Greek word translated ‘angel’ really means a <i>messenger</i> or <i>delegate</i>.
        In fact, ‘angel’ is a transliteration of the Greek, not a translation.
        The translators have to decide from the context if it's referring to a human
        or to a supernatural being (typically dressed in shining white).
        Sometimes (e.g., <a href="https://BibleHub.com/parallel/revelation/1-20.htm">Rev 1:20</a>)
        we don't really know which of the two is meant.</p>

  <h3 id="apostle">ambassador, apostle, missionary</h3>
  <p><i>Missionary</i> (literally <i>sent-out one</i>) would be the natural translation
        of the Greek word (<a href="https://biblehub.com/greek/652.htm">ἀπόστολος</a>),
        but that's not always what it's used for in the “New Testament”.
    Sometimes it's used as a synonym for the close disciples when they were sent out
        (e.g., see <a href="MRK.html#C6V30">Mark 6:30</a>).
    Other times it seems to be used for church authorities,
        and it's often used for that today,
        although not generally used at all outside of church language.</p>

  <h3 id="believe">believe, believe in, trust</h3>
  <p>If you ‘believe’ someone, it usually means that you consider
        that what they just said wasn't a lie.
    But if you ‘believe <b>in</b>’ someone, that's different—it's often to do with capability,
        i.e., usually that they're able to do what they're about to embark on,
            e.g., believing in a child that's learning to drive,
            or an engineer trying to solve a difficult problem.</p>
  <p>So what do the New Testament writers mean when they write
        about ‘believing in Jesus’?
    In most cases, they're talking about ‘believing that Jesus is the messiah’,
        or in other words,
            ‘believing that Jesus is authentically sent from heaven and doing God's work’.
    This can be clearly seen when <a href="JHN.html#C11V27">Martha responds</a>
        to Jesus' statement about
        those who ‘believe in me’.</p>
  <p>Because belief in a coming messiah is not a basic staple of our modern culture,
        sometimes we need to help our readers know what was at stake
        as people of those times either rejected or ‘believed in’ Jesus.</p>

  <h3 id="disciple">apprentice, disciple, follower</h3>
  <p>While it is true that the word <i>disciple</i>
        (<a href="https://biblehub.com/greek/3101.htm">μαθητής</a>)
        can probably be understood by most modern readers,
        it's the concept more than the word that people aren't really familiar with these days.
    Some do indeed go to the East and place themselves under the teaching of various <i>guru</i>s,
        but we wouldn't usually use the term <i>disciple</i> for an intern in a church.
    The term is complicated when it's used in the Bible for thousands of Jesus followers,
        and then used for the selected twelve close followers, and sometimes for other size groups in-between.
    So the <em>Readers' Version</em> has elected to use <i>followers</i> most of the time,
        and the word <i>apprentices</i> or <i>trainees</i> (still to be decided)
        for the twelve who stuck more closely with Jesus.
    At least modern readers understand the work of an apprentice who works for the master tradesman
        who takes responsibility for their work,
        even if much of the actual teaching is done away at a block course in an institution these days.</p>

  <h3 id="father">father, ancestor</h3>
  <p>In the biblical languages and cultures, they often used the term for ‘father’
        to refer to any of their male ancestors.
        Thus Abraham was considered the ‘father’ of the Jews.
    We can use the term to mean ‘founder’ in English, e.g., ‘the father of jazz’,
        but don't usually use it for ancestors.</p>

  <h3 id="glory">glory, glorify</h3>
  <p>It's not common to hear on the street about someone being ‘glorified’
        and also difficult to find a single <a href="https://www.thesaurus.com/browse/glorify">synonym</a>
        that captures the original meaning.
    This leaves us with three main choices:</p>
  <ol><li>Use the traditional word that's not really understood by young English speakers,</li>
    <li>Use a longer phrase that tries to capture the full meaning of the word,</li>
    <li>Choose one synonym that will be understood, albeit inadequately expressing the full meaning.</li>
  </ol>
  <p>Sadly (because we ourselves recognise that it's not ideal),
        we'll often choose the latter compromise in the <em>Readers' Version</em>.</p>

  <h3 id="holy">holy</h3>
  <p>Oh, what does the word ‘holy’ mean
        to the average person in the 2020s?
    On the street, we mostly hear it used as part of an exclamation
        (often along with a word for excrement or other profanity)!</p>
  <p>To the more serious reader, ‘holy’ seems to be associated with
        purity, perfection, and sinlessness, and even with a halo.
    So the ‘holy apostles’ (typical translation found in
        <a href="https://biblehub.com/parallel/ephesians/3-5.htm">Eph. 3:5</a>) weren't
        necessarily any more perfect or sinless than us—in fact it's quite misleading
    because that is NOT the root meaning of the Greek word which is closer to
        ‘different’, ‘separated’, or ‘set aside for a special purpose’.
  <p>Is there a better word, perhaps a <a href="https://www.thesaurus.com/browse/holy">synonym</a>
        that we could use that would convey the right meaning?
    (We want to avoid misconceptions that have lead to concepts like ‘Saints’ in
        the Roman church.
    It's so easy to wrongly think that somehow those now deceased were
        somehow more pure or sinless than us.)</p>
  <p>Some of the words used in the Readers' Version include:
        ‘dedicated (ones)’, and ‘pure’.</p>

  <h3 id="holySpirit">holy spirit</h3>
  <p><small>Please be sure to read about ‘<a href="#holy">holy</a>’ above first.</small></p>
  <p>We notice that the term ‘Holy Spirit’ is almost used like a name,
        with users often not really considering the meaning of the term,
        and possibly not even able to define it well in their own words.</p>
  <p>Because of the mismatch of cultures, the <em>Readers' Version</em>
        has made the decision to downplay the word ‘holy’,
        often referring to ‘God's spirit’
        or using ‘pure’ in other contexts.
    We acknowledge that many will find this inadequate,
        but we feel that words that have lost their cultural meaning
        are also inadequate, so there's no ideal solution.</p>

  <h3 id="lord">lord, master</h3>
  <p>In our modern, Western culture,
        we don't really have the ancient concept of our lives being
        very much in the hands of our king or lord or master or boss or owner.
    In general, our boss only has power over us for certain hours of the week,
        and no person in our mostly
        <a href="https://duckduckgo.com/?q=egalitarian+meaning&ia=definition">egalitarian</a>
        culture considers anyone else to be their ‘master’.</p>
  <p>On the other hand, in churches you will hear a lot of talk about ‘the Lord’,
        but we suspect that it's mostly only jargon or cliche
        because few of us can imagine a single person (or deity)
        in a position of the power of life or death over us.</p>
  <p>Because of this mismatch of cultures, the <em>OET</em>
        has made the decision not to use the word ‘lord’ or ‘Lord’,
        and chosen the word ‘master’, while not ideal,
        to at least provoke more thought
        about what the Biblical concept might mean.
    (‘Boss’ was rejected as being too informal.)
    Sometimes too, we will simply use ‘God’ or his name ‘Yahweh’
        where it seems to fit better.
    Remember that the Jewish people traditionally also say the word ‘Lord’
        as a substitute for Yahweh, the name of God, in the Hebrew scriptures
        (although that's not a Biblical command—in fact
        it seems to make God's revelation of his name rather pointless).</p>

  <h3 id="name">name</h3>
  <p>In ancient days, if a group of horse riders turned up at your house and said,
        “We've come to arrest you in the name of King Henry!”,
        they meant that they have come with the <i>authority</i> of the king.
    The name ‘Henry’ has no particular power in its syllables.
    And of course, the person that we refer to as ‘Jesus’ was <b>never ever</b>
        referred to by those particular syllables when he walked on this earth.
    So too, sometimes when we read about <i>the name of Jesus</i>,
        it might not only be referring to his actual name
        (which likely differed depending on whether it was a Jew or a Roman or a Greek speaking),
        but also referring to his <i>authority</i>,
        for example his authority over demons.
    Thus when praying for healing, it's not necessarily productive to shout
        “in the name of Jesus” over and over
        (not least because that was never his actual name).
    What if the traffic officer shouted, “Prime-minister, prime-minister” over and over again
        in order to convince you that they have authority
        from the government to issue you a speeding ticket?
    No, you muffle your response because you know that the authority to issue tickets or instant fines
        is part of their job description.
    Perhaps it might be more helpful to consider how you would pray if you were employed by Jesus
        and believed that in your job description,
        he has given you his authority to command these certain things.</p>
  <p>P.S. Look in the <em>Literal Version</em> to see how to more properly
        pronounce the names of Biblical characters.</p>

  <h3 id="priest">priest</h3>
  <p>It's important that you don't picture a Roman Catholic or an Anglican or an Orthodox priest
        as you read the Bible.
     Remember that most of the priests mentioned in the Bible are Jewish priests,
        and had their own unique set of traditions.</p>

  <h3 id="word">word</h3>
  <p>John's gospel account typically <a href="https://biblehub.com/parallel/john/1-1.htm">starts with</a>
        “In the beginning was the Word…” but which word was it? “Tree?” “Apple?” “Snake?”
    Of course it's not talking about the normal meaning of the word <i>word</i>,
        but a religious use of the word as it later refers to Jesus the Messiah.
    But Jesus isn't a word like the words on this page, but it refers to something totally different.
    In fact, the meaning of Greek
        <a href="https://biblehub.com/greek/3056.htm">λόγος</a> (‘logos’—but not the plural of logo),
        more likely refers to a speech, message, statement, or account
        and very rarely refers to a single word.
    In other words, it would be extremely rare for modern speaker to use the word <i>word</i>
        to describe a message:
        “The president read out a long word at the stadium opening ceremony.” Never!
    So the <em>OET</em> breaks tradition and
        tries to give a <b>modern</b> translation of what the Bible writers wrote.</p>

  <h3 id="Feedback">Feedback</h3>
    <p>These web pages are a very preliminary preview into a work still in progress.
        The <em>OET</em> is not yet finished, and not yet publicly released,
        but we need to have it available online for easy access for our checkers and reviewers.
        If you're reading this and have questions that aren't discussed here,
        please do contact us by <a href="mailto:Freely.Given.org@gmail.com?subject=OET Glossary">email</a>.
        Also if there's something that we didn't explain in this glossary, or didn't explain very well.
        Thanks.</p>
  <p>See also the <a href="index.html#Intro">Introduction</a> and the <a href="FAQs.html">FAQs</a>.</p>
  <p>HTML last updated: __LAST_UPDATED__</p>
</body></html>
"""
assert SBS_GLOSSARY_HTML.count('‘') == SBS_GLOSSARY_HTML.count('’'), f"Why do we have {SBS_GLOSSARY_HTML.count('‘')=} and {SBS_GLOSSARY_HTML.count('’')=}"
assert SBS_GLOSSARY_HTML.count('“') == SBS_GLOSSARY_HTML.count('”'), f"Why do we have {SBS_GLOSSARY_HTML.count('“')=} and {SBS_GLOSSARY_HTML.count('”')=}"
SBS_GLOSSARY_HTML = SBS_GLOSSARY_HTML.replace( "'", "’" ) # Replace hyphens
assert "'" not in SBS_GLOSSARY_HTML
assert '--' not in SBS_GLOSSARY_HTML

SBS_NOTES_HTML = """<!DOCTYPE html>
<html lang="en-US">
<head>
  <title>OET Development Notes</title>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="keywords" content="Bible, open, translation, OET, English, literal, readers, modern, notes, outstanding, free">
  <link rel="stylesheet" type="text/css" href="BibleBook.css">
</head>
<body>
  <p><a href="../">Up</a></p>
  <h1>Open English Translation (OET) Development</h1>
  <h2>Notes</h2>
  <p>This page contains a list of various issues that need further work
        and/or consistency checking.</p>

  <h3 id="believeIn">believe in me</h3>
  <p>Need to check for consistency.</p>

  <h3 id="age">will not die to the age</h3>
  <p>Need to check for consistency—‘to the age’
    just seems to be just omitted in most translations.</p>

  <h3 id="Jesus">Jesus vs Yeshua</h3>
  <p>Need to decide.</p>

  <p>HTML last updated: __LAST_UPDATED__</p>
</body></html>
"""
assert "'" not in SBS_NOTES_HTML
assert '--' not in SBS_NOTES_HTML

RV_CHECKING_HTML = """<!DOCTYPE html>
<html lang="en-US">
<head>
  <title>OET Checking Instructions</title>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="keywords" content="Bible, open, translation, OET, English, readers, modern, check, test, free">
  <link rel="stylesheet" type="text/css" href="BibleBook.css">
</head>
<body>
  <p><a href="../">Up</a></p>
  <h1>Open English Translation (OET) Checking Instructions</h1>
  <h2>Checking the <em>Readers' Version</em></h2>

  <p>If you've been asked to help with checking the <em>OET RV</em>,
        this is how we suggest you work.
    Please note that we suggest that you read the <em>OET RV</em>
        on a wider screen, like a laptop or tablet (not a phone).
    We will use the book of Mark as an example below.</p>

  <p>Please note also that when you submit any corrections or suggestions for the <em>OET</em>
        those comments and any changes that result from them
        become the property of Freely-Given.org.
    (If you would like your name added to the list of contributors to the <em>OET</em>,
        we're happy to do this and you should contact us for further details.)</p>

  <h3>Set up</h3>
  <ol>
  <li>The starting page is
        <a href="https://Freely-Given.org/OET/SideBySide/MRK.html">https://Freely-Given.org/OET/SideBySide/MRK.html</a>.
        For other books, the three UPPERCASE characters have to be changed, e.g., JDE for Jude</li>
  <li>You can always access the book index at
        <a href="https://Freely-Given.org/OET/SideBySide/index.html#Index">https://Freely-Given.org/OET/SideBySide/index.html#Index</a></li>
  <li>You can also jump directly to specific chapters by appending <b>#C4</b> or similar
        to the book address like the Mark one above, getting
        <a href="https://Freely-Given.org/OET/SideBySide/MRK#C4.html">https://Freely-Given.org/OET/SideBySide/MRK.html#C4</a></li>
  <li>You can also jump directly to specific verses by appending <b>#C12V7</b> or similar
        to the book address like the Mark one above, getting
        <a href="https://Freely-Given.org/OET/SideBySide/MRK#C12V7.html">https://Freely-Given.org/OET/SideBySide/MRK.html#C12V7</a></li>
  <li>The above views give the introduction to the book (and some other bits &amp; pieces)
        then when it gets to the Bible text, it displays the <em>Readers' Version</em>
        on the left and the <em>Literal Version</em> on the right</li>
  <li>You may want to print the book you are checking and then you can just circle errors
        and write down your suggestions directly.
        (Ask us if you need technical help doing that, and/or compensation for your costs.)</li>
  <li>The <em>RV</em> has section headings which are enclosed in boxes on the right of the text
        in such a way that they don't interrupt the flow of the text</li>
  <li>You should read the introduction at
        <a href="https://Freely-Given.org/OET/SideBySide/index.html#Intro">https://Freely-Given.org/OET/SideBySide/index.html#Intro</a>
        to get a good understanding of the goals of the <em>OET</em>.</li>
  <li>We recommend that you look at the parallel Bible verse view on BibleHub at
        <a href="https://BibleHub.com/parallel/mark/1-1.htm">https://BibleHub.com/parallel/mark/1-1.htm</a>
        (and of course you can navigate from there to where you are working)</li>
  <li>You can see the interlinear version of the Greek source text of the New Testament on the bottom lines of
        <a href="https://GreekCNTR.org/collation/">https://GreekCNTR.org/collation/</a>.
        (The blue Strong's dictionary numbers there can be clicked to give some definitions of the Greek words.)</li>
  </ol>

  <h3>Things to look out for</h3>
  <p>It wouldn't hurt to re-read this section each day before starting a checking session
        (to remind yourself what we're looking for).</p>
  <ol>
  <li><b>Whole section</b>: Read the whole text of the <em>RV</em> down to the next section heading.
            Check if
    <ul>
    <li>It reads fluently and naturally?</li>
    <li>Any typos or missing words?</li>
    <li>Did it have any words that you don't normally use?
            (We're trying to avoid as much ‘churchy’ language as possible.)</li>
    <li>Is there any sentence that you think you could say more clearly or more naturally
            than what's there?</li>
    </ul></li>
  <li><b>Section headings</b>: After finishing a section, go back up to the section heading and
    <ul>
    <li>See if the heading is a good summary of the main point of the section?</li>
    <li>Look at the start of the section and see if there's a natural break from the previous section
            (i.e., that this current section starts in the best place)?</li>
    <li>Do you think that the section should have been divided into two (or more) sections?</li>
    </ul></li>
  <li><b>Verse content</b>:
    <ul>
    <li>Check that all phrases are present in each verse,
            e.g., if the verse in the <em>Literal Version</em> or in other versions
            says that something happened at a certain time,
            then the <em>RV</em> should usually also mention a time</li>
    <li>Check that all the adjectives are present, e.g., if the <em>LV</em> says
            it's a <i>great storm</i>, then the <em>RV</em> should have <i><b>big</b> storm</i>
            or <i><b>bad</b> storm</i> or use a single word that covers both like
            <i>typhoon</i> or <i>tornado</i> or something</li>
    <li>Does the <em>RV</em> seem to be saying something different from every other version?</li>
    </ul></li>
  <li><b>Key Terms</b>: These are important words that repeat in a Bible,
        like <i>God</i>, <i>Jesus</i>, <i>Holy Spirit</i>, <i>sin/sinner</i>,
        <i>save/salvation</i>, <i>redeem/redemption</i>, <i>heaven</i>, etc.
    <ul>
    <li>Did you notice anywhere where a particular Key Term was translated differently before?</li>
    <li>Is that Key Term rendered well? Can you think of a better way of saying it?</li>
    </ul></li>
  <li><b>Theology</b>: Check that the <em>RV</em> is not accidentally
            teaching something that you think it shouldn't.
        (Once there was a printed Bible nicknamed <a href="https://en.wikipedia.org/wiki/Wicked_Bible">The Wicked Bible</a>
            because it accidentally missed typesetting the <i>not</i>
            in <i>Thou shalt not commit adultery.</i>)</li>
  <li><b>Literal Version</b>: The <em>LV</em> is not manually translated like the <em>RV</em>,
        but instead it's translated from the Hebrew (OT)
        and Greek (NT) by a series of computer programs.
        However, the words are reordered manually, e.g., <i>going he is now</i>
        should be reordered to <i>he is now going</i> or <i>he is going now</i>.
        If you notice words that should be reordered, please inform us.
        However, not all of the NT has been reordered yet
        (so far only Mark is completed), so please check first
        before spending a lot of time on checking this.</li>
  </ol>

  <h3 id="Notes">Notes</h3>
  <ol>
    <li><b>RV and LV</b>: Generally the <em>RV</em> should represent
        every important word that's in the <em>LV</em> except for the following:
        <ul><li>A pronoun (like ‘he’) might be changed to the person's name in the <em>RV</em>
                at the start of a new section, or if it's helpful
                to remind the readers or to clarify who it's referring to</li>
        <li>A name might be changed to a pronoun in the <em>RV</em> if it seems
                unnecessary or unnatural in English to repeat the name again so soon</li>
        <li>A phrase might be omitted in the <em>RV</em> if it was already mentioned previously,
                and would seem unnatural or bad style in English
                to repeat that information again so soon.</li>
        <li>When the <em>RV</em> guesses at some information that's not mentioned
                in the <em>LV</em> and could possibly be wrong,
                then we try to mark it in grey in the <em>RV</em> as something added.
            However, if we think it's obvious what was implied
                (and thus very unlikely to be wrong),
                we don't always grey the text in that case.</li>
        </ul></li>
  </ol>

  <h3 id="Feedback">Feedback</h3>
    <p>The <em>OET</em> is not yet finalised, and not yet publicly released,
        but it's online here for easy access for our checkers and reviewers.
    If you have corrections and suggestions,
        please do contact us by <a href="mailto:Freely.Given.org@gmail.com?subject=OET RV Checking">email</a>.
    Also if there's something that we didn't explain in these notes, or didn't explain very well.
    Thanks.</p>
    <p>Please don't be offended if we choose not to take your suggestion.</p>
  <p>See also the <a href="index.html#Intro">Introduction</a>, the <a href="FAQs.html">FAQs</a>, and the <a href="Glossary.html">Glossary</a>.</p>
  <p>HTML last updated: __LAST_UPDATED__</p>
</body></html>
"""
assert RV_CHECKING_HTML.count('‘') == RV_CHECKING_HTML.count('’')
assert RV_CHECKING_HTML.count('“') == RV_CHECKING_HTML.count('”')
RV_CHECKING_HTML = RV_CHECKING_HTML.replace( "'", "’" ) # Replace hyphens
assert "'" not in RV_CHECKING_HTML
assert '--' not in RV_CHECKING_HTML

SBS_DISCLAIMER_HTML = """<p id="Disclaimer">Note: This is still a very early look into the unfinished text of the <em>Open English Translation</em> of the Bible.
Please double-check the text in advance before using in public.
Some things (like capitalisation of ‘him’ referring to Jesus or ‘father’ referring to God)
    in the <em>RV</em> haven't been decided yet so we're still testing both ways.</p>
"""
assert SBS_DISCLAIMER_HTML.count('‘') == SBS_DISCLAIMER_HTML.count('’')
assert SBS_DISCLAIMER_HTML.count('“') == SBS_DISCLAIMER_HTML.count('”')
SBS_DISCLAIMER_HTML = SBS_DISCLAIMER_HTML.replace( "'", "’" ) # Replace hyphens
assert "'" not in SBS_DISCLAIMER_HTML
assert '--' not in SBS_DISCLAIMER_HTML

SBS_BOOK_INTRO_HTML1 = """<p>Note: The <em>Readers' Version</em> on the left is a translation
into contemporary English aimed at <i>the person on the street</i> who
hasn't necessarily been brought up with exposure to Biblical jargon and/or 500-year old English.
It's designed to be used alongside the <em>Literal Version</em> on the right which gives
the English reader a window into what's actually written in the original languages.
(See the <a href="index.html#Intro">introduction</a> for more details—we
recommend that you read the introduction first if you're wanting to fully understand the <em>Literal Version</em>.)
By comparing the left and right columns, you should be able to easily get the message of the text,
while at the same time keeping an eye on what it was actually translated from.</p>
<p>Note that <span class="RVadded">greyed words</span> in the <em>RV</em> are words that the translators
consider were most probably in the mind of the writer, but as none of us can double-check
with the original speakers or writers, the reader is free to disagree.
They are clearly marked because we've tried to be as honest and transparent as possible.</p>
<p>The <span class="added">lighter coloured words</span> in the <em>LV</em> are words which
aren't needed in the grammar of the original languages but are required or implied in English.
You can read the <a href="index.html#Key">Key</a> to learn more about them.
The underlines in the <em>LV</em> show when one original language word needs to be translated into two or more English words.
(Just hide them with the button if you don't need that information and find it distracting.)
Also, the majority of sentences in the <em>LV</em> don't have the words
put into a sensible English order yet.
(This should be completed by the end of 2023.)</p>
"""
assert SBS_BOOK_INTRO_HTML1.count('‘') == SBS_BOOK_INTRO_HTML1.count('’'), f"Why do we have {SBS_BOOK_INTRO_HTML1.count('‘')=} and {SBS_BOOK_INTRO_HTML1.count('’')=}"
assert SBS_BOOK_INTRO_HTML1.count('“') == SBS_BOOK_INTRO_HTML1.count('”'), f"Why do we have {SBS_BOOK_INTRO_HTML1.count('“')=} and {SBS_BOOK_INTRO_HTML1.count('”')=}"
SBS_BOOK_INTRO_HTML1 = SBS_BOOK_INTRO_HTML1.replace( "'", "’" ) # Replace hyphens
assert "'" not in SBS_BOOK_INTRO_HTML1
assert '--' not in SBS_BOOK_INTRO_HTML1

SBS_NOMINA_SACRA_HTML = """<p>The <span class="nominaSacra">bold words</span>
in the <em>LV New Testament</em> are
<a href="https://BibleQuestions.info/2020/01/25/what-are-nomina-sacra/">words</a>
that the original writers or copyists
marked to indicate that they considered them to refer to God.
<small>(Sadly, this information is not displayed in most Bible translations,
especially since it seems to clearly confirm that the earliest writers/copyists
considered both Jesus and the Holy Spirit to be God.)</small></p>
"""
assert "'" not in SBS_NOMINA_SACRA_HTML
assert '--' not in SBS_NOMINA_SACRA_HTML

SBS_INTRO_PRAYER_HTML = """<p class="shortPrayer">It is our prayer that the
<em>Open English Translation</em> of the Bible will give you a clear understanding of
the accounts and messages written by the God-inspired Biblical writers.</p>
"""
assert "'" not in SBS_INTRO_PRAYER_HTML
assert '--' not in SBS_INTRO_PRAYER_HTML

SBS_START_HTML = """<!DOCTYPE html>
<html lang="en-US">
<head>
  <title>__TITLE__</title>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="keywords" content="Bible, OET, translation, English, literal, readers, version, modern, free, open">
  <link rel="stylesheet" type="text/css" href="BibleBook.css">
  <script src="content.js"></script>
</head>
<body>
"""
END_HTML = '</body></html>\n'
assert "'" not in SBS_START_HTML and "'" not in END_HTML
assert '--' not in SBS_START_HTML and '--' not in END_HTML

BACK_FORTH_LINKS_HTML_TEMPLATE = '<p>' \
     '__PREVIOUS__OET <a href="index.html#Index">Book index</a>,' \
     ' <a href="index.html#Intro">Intro</a>, and <a href="index.html#Key">Key</a>__NEXT__' \
    f'{EM_SPACE}<a href="FAQs.html">FAQs</a>' \
    f'{EM_SPACE}<a href="Glossary.html">Glossary</a>' \
     '<br><br>__REST__</p>'

TWO_COLUMN_START_HTML = f"""<p>See also the <a href="FAQs.html">FAQs</a> and the <a href="Glossary.html">Glossary</a>.</p>
<div class="container">
<span> </span>
{SBS_BUTTONS_HTML}
<h2>Readers' Version</h2>
<h2>Literal Version</h2>"""
assert TWO_COLUMN_START_HTML.count('‘') == TWO_COLUMN_START_HTML.count('’'), f"Why do we have {TWO_COLUMN_START_HTML.count('‘')=} and {TWO_COLUMN_START_HTML.count('’')=}"
assert TWO_COLUMN_START_HTML.count('“') == TWO_COLUMN_START_HTML.count('”'), f"Why do we have {TWO_COLUMN_START_HTML.count('“')=} and {TWO_COLUMN_START_HTML.count('”')=}"
TWO_COLUMN_START_HTML = TWO_COLUMN_START_HTML.replace( "'", "’" ) # Replace hyphens
assert "'" not in TWO_COLUMN_START_HTML

SBS_PSALM_INDEX_HTML = """<!DOCTYPE html>
<html lang="en-US">
<head>
  <title>Songs (Psalms)</title>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="keywords" content="Bible, open, translation, OET, English, literal, readers, modern, psalms, songs, outstanding, free">
  <link rel="stylesheet" type="text/css" href="BibleBook.css">
</head>
<body>
  <p><a href="../">Up</a></p>
  <h1>Open English Translation (OET) Development</h1>
  <h2>Songs (Psalms)</h2>

  __PSALMS_INDEX_MIDDLE__

  <p>HTML last updated: __LAST_UPDATED__</p>
</body></html>
"""
assert "'" not in SBS_PSALM_INDEX_HTML
assert '--' not in SBS_PSALM_INDEX_HTML


genericBookList = []
def pack_HTML_files() -> None:
    """
    """
    fnPrint( DEBUGGING_THIS_MODULE, "pack_HTML_files()" )

    numBooksProcessed = 0
    for BBB in genericBookList: # includes intro, etc.

        # Swap book orders to put JHN before MAT
        if   BBB == 'MAT': BBB = 'JHN'
        elif BBB == 'MRK': BBB = 'MAT'
        elif BBB == 'LUK': BBB = 'MRK'
        elif BBB == 'JHN': BBB = 'LUK'

        bookType = None
        if BibleOrgSysGlobals.loadedBibleBooksCodes.isOldTestament_NR( BBB ):
            bookType = 'OT'
        elif BibleOrgSysGlobals.loadedBibleBooksCodes.isNewTestament_NR( BBB ):
            bookType = 'NT'

        if bookType:
            source_ESFM_filename = f'OET-RV_{BBB}.ESFM'
            with open( OET_RV_USFM_InputFolderPath.joinpath(source_ESFM_filename), 'rt', encoding='utf-8' ) as usfm_input_file:
                rv_usfm_text = usfm_input_file.read()

            source_RV_filename = f'{BBB}.html'
            source_LV_filename = f'{BBB}.html'
            with open( OET_RV_HTML_InputFolderPath.joinpath(source_RV_filename), 'rt', encoding='utf-8' ) as html_input_file:
                rv_html = html_input_file.read()
            with open( OET_LV_HTML_InputFolderPath.joinpath(source_LV_filename), 'rt', encoding='utf-8' ) as html_input_file:
                lv_html = html_input_file.read()

            book_start_html, book_html, book_end_html = extract_and_combine_simple_HTML( BBB, rv_usfm_text, rv_html, lv_html )

            output_filename = f'{BBB}.html'
            with open( OET_HTML_OutputFolderPath.joinpath(output_filename), 'wt', encoding='utf-8' ) as html_output_file:
                html_output_file.write( f'{book_start_html}\n{book_html}\n{book_end_html}' )

            # We also save individual Psalms
            if BBB == 'PSA':
                handle_Psalms( book_start_html, book_html, book_end_html )

            # # Having saved the book file, now for better orientation within the long file (wholeTorah or wholeNT),
            # #   adjust book_html to include BBB text for chapters past chapter one
            # bookAbbrev = BBB.title().replace('1','-1').replace('2','-2').replace('3','-3')
            # chapterRegEx = re.compile(f'''<span class="{'cPsa' if BBB=='PSA' else 'c'}" id="C(\d{1,3})V1">(\d{1,3})</span>''')
            # while True:
            #     for match in chapterRegEx.finditer( book_html ):
            #         assert match.group(1) == match.group(2)
            #         # print('A',BBB,match,match.group(1),book_html[match.start():match.end()])
            #         if match.group(1) != '1': # We don't adjust chapter one
            #             # print('B',BBB,match,match.group(1),book_html[match.start():match.end()])
            #             insert_point = match.end() - len(match.group(2)) - 7 # len('</span>')
            #             book_html = f'{book_html[:insert_point]}{bookAbbrev} {book_html[insert_point:]}'
            #             break # redo the search
            #     else: break
            # if BBB in TORAH_BOOKS_CODES:
            #     whole_Torah_html = f'{whole_Torah_html}{book_html}'
            # elif bookType == 'NT':
            #     whole_NT_html = f'{whole_NT_html}{book_html}'

            numBooksProcessed += 1

    # Output CSS, JS, index, FAQs, glossary, and notes html
    assert "'" not in SBS_CSS_TEXT
    with open( OET_HTML_OutputFolderPath.joinpath('BibleBook.css'), 'wt', encoding='utf-8' ) as css_output_file:
        css_output_file.write( SBS_CSS_TEXT )
    with open( OET_HTML_OutputFolderPath.joinpath('content.js'), 'wt', encoding='utf-8' ) as js_output_file:
        js_output_file.write( SBS_JS )

    indexIntroHTML = SBS_INDEX_INTRO_HTML.replace('   ',' ').replace('  ', ' ').replace('\n ', '\n') \
            .replace( '__LAST_UPDATED__', f"{datetime.now().strftime('%Y-%m-%d')} <small>by {PROGRAM_NAME_VERSION}</small>" )
    assert "'" not in indexIntroHTML
    with open( OET_HTML_OutputFolderPath.joinpath('index.html'), 'wt', encoding='utf-8' ) as html_index_file:
        html_index_file.write( indexIntroHTML )

    faqHTML = SBS_FAQ_HTML.replace('   ',' ').replace('  ', ' ').replace('\n ', '\n') \
            .replace( '__LAST_UPDATED__', f"{datetime.now().strftime('%Y-%m-%d')} <small>by {PROGRAM_NAME_VERSION}</small>" )
    assert "'" not in faqHTML and '--' not in faqHTML
    with open( OET_HTML_OutputFolderPath.joinpath('FAQs.html'), 'wt', encoding='utf-8' ) as html_FAQ_file:
        html_FAQ_file.write( faqHTML )

    glossaryHTML = SBS_GLOSSARY_HTML.replace('   ',' ').replace('  ', ' ').replace('\n ', '\n') \
            .replace( '__LAST_UPDATED__', f"{datetime.now().strftime('%Y-%m-%d')} <small>by {PROGRAM_NAME_VERSION}</small>" )
    assert "'" not in glossaryHTML and '--' not in glossaryHTML
    with open( OET_HTML_OutputFolderPath.joinpath('Glossary.html'), 'wt', encoding='utf-8' ) as html_glossary_file:
        html_glossary_file.write( glossaryHTML )

    notesHTML = SBS_NOTES_HTML.replace('   ',' ').replace('  ', ' ').replace('\n ', '\n') \
            .replace( '__LAST_UPDATED__', f"{datetime.now().strftime('%Y-%m-%d')} <small>by {PROGRAM_NAME_VERSION}</small>" )
    assert "'" not in notesHTML and '--' not in notesHTML
    with open( OET_HTML_OutputFolderPath.joinpath('Notes.html'), 'wt', encoding='utf-8' ) as html_notes_file:
        html_notes_file.write( notesHTML )

    checkingHTML = RV_CHECKING_HTML.replace('   ',' ').replace('  ', ' ').replace('\n ', '\n') \
            .replace( '__LAST_UPDATED__', f"{datetime.now().strftime('%Y-%m-%d')} <small>by {PROGRAM_NAME_VERSION}</small>" )
    assert "'" not in checkingHTML and '--' not in checkingHTML
    with open( OET_HTML_OutputFolderPath.joinpath('Checking.html'), 'wt', encoding='utf-8' ) as html_checking_file:
        html_checking_file.write( checkingHTML )

    # # Save our long book conglomerates
    # with open( OET_HTML_OutputFolderPath.joinpath('OET-RV-LV-Torah.html'), 'wt', encoding='utf-8' ) as html_output_file:
    #     html_output_file.write( f'{START_HTML.replace("__TITLE__","OET-RV-LV-Torah (Preliminary)")}\n'
    #                             f'<p><a href="index.html">OET-RV-LV Index</a></p>\n{whole_Torah_html}\n'
    #                             f'<p><a href="index.html">OET-RV-LV Index</a></p>\n{END_HTML}' )
    # with open( OET_HTML_OutputFolderPath.joinpath('OET-RV-LV-NT.html'), 'wt', encoding='utf-8' ) as html_output_file:
    #     html_output_file.write( f'{START_HTML.replace("__TITLE__","OET-RV-LV-NT (Preliminary)")}\n'
    #                             f'<p><a href="index.html">OET-RV-LV Index</a></p>\n{whole_NT_html}\n'
    #                             f'<p><a href="index.html">OET-RV-LV Index</a></p>\n{END_HTML}' )

    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"Finished processing {numBooksProcessed} HTML books." )
# end of pack_HTML_side-by-side.pack_HTML_files()


def extract_and_combine_simple_HTML( BBB:str, rvUSFM:str, rvHTML:str, lvHTML:str ) -> Tuple[str, str, str]:
    """
    We use the RV USFM to find the book name, etc.
        Also we use the intro from the RV HTML.
    """
    fnPrint( DEBUGGING_THIS_MODULE, f"extract_and_combine_simple_HTML( {BBB}, ({len(rvUSFM):,}), ({len(rvHTML):,}), ({len(lvHTML):,}) )" )

    if BBB in OT_BBB_LIST:
        links_html = BACK_FORTH_LINKS_HTML_TEMPLATE.replace('__REST__', '' ) #'Whole <a href="OET-RV-LV-Torah.html">Torah/Pentateuch</a> (for easy searching of multiple books, etc.)' )

        previousBBB = OT_BBB_LIST[OT_BBB_LIST.index(BBB)-1] # Gives wrong value (@[-1]) for first book
        try: nextBBB = OT_BBB_LIST[OT_BBB_LIST.index(BBB)+1]
        except IndexError: nextBBB = NT_BBB_LIST[0] # above line fails on final book
        links_html = links_html.replace( '__PREVIOUS__', '' if BBB==NT_BBB_LIST[0]
            else f'<a href="{previousBBB}.html">Previous Book ({previousBBB})</a>{EM_SPACE}')
        links_html = links_html.replace( '__NEXT__', f'{EM_SPACE}<a href="{nextBBB}.html">Next Book ({nextBBB})</a>')
    elif BBB in NT_BBB_LIST:
        links_html = BACK_FORTH_LINKS_HTML_TEMPLATE.replace('__REST__', '' ) #'Whole <a href="OET-RV-LV-NT.html">New Testament</a> (for easy searching of multiple books, etc.)' )

        previousBBB = OT_BBB_LIST[-1] if BBB==NT_BBB_LIST[0] else NT_BBB_LIST[NT_BBB_LIST.index(BBB)-1] # Gives wrong value (@[-1]) for first book
        try: nextBBB = NT_BBB_LIST[NT_BBB_LIST.index(BBB)+1]
        except IndexError: pass # above line fails on final book
        links_html = links_html.replace( '__PREVIOUS__', f'<a href="{previousBBB}.html">Previous Book ({previousBBB})</a>{EM_SPACE}')
        links_html = links_html.replace( '__NEXT__', '' if BBB==NT_BBB_LIST[-1]
            else f'{EM_SPACE}<a href="{nextBBB}.html">Next Book ({nextBBB})</a>')
    else: raise Exception( f"unexpected_BBB '{BBB}'" )

    # Create the introduction at the top of the book
    C, V = None, '0'
    done_intro = startedChapters = False
    book_html = ''
    book_h_field = None
    section1_headers = []
    for usfm_line in rvUSFM.split( '\n' ):
        if not usfm_line: continue # Ignore blank lines
        assert usfm_line.startswith( '\\' )
        usfm_line = usfm_line[1:] # Remove the leading backslash
        try: marker, rest = usfm_line.split( ' ', 1 )
        except ValueError: marker, rest = usfm_line, ''
        # dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"{marker=} {rest=}")
        if marker in ('id','usfm','ide','h','toc2','toc3'):
            if marker == 'h': book_h_field = rest
            continue # We don't need to map those markers to HTML
        if marker in ('rem',):
            if not startedChapters:
                book_html = f'{book_html}<p class="{marker}">{rest}</p>\n'
        elif marker in ('mt1','mt2'):
            if not done_intro: # Add an extra explanatory paragraph at the top
                book_html = f'{book_html}{SBS_DISCLAIMER_HTML}{SBS_BOOK_INTRO_HTML1}'
                if BBB in NT_BBB_LIST:
                    book_html = f'{book_html}{SBS_NOMINA_SACRA_HTML}'
                done_intro = True
            book_html = f'{book_html}<p class="{marker}">{rest}</p>\n'
        elif marker == 'toc1':
            start_html = SBS_START_HTML.replace( '__TITLE__', rest )
        elif marker == 'c':
            C, V = rest, '0'
            if C:
                if C != C.strip():
                    logging.warning( f"{BBB} C='{C}' needs cleaning")
                    C = C.strip()
                assert C.isdigit()
            if C == '1': # Add an inspirational note
                book_html = f'{book_html}{SBS_INTRO_PRAYER_HTML}'
                startedChapters = True
        elif marker == 'v':
            try: V, rest = rest.split( ' ', 1 )
            except ValueError: V, rest = rest, ''
            if '-' in V: # for a verse range
                V = V.split( '-', 1 )[0]
        elif marker == 's1':
            # print( f"{BBB} {C} {V} '{rest}'" )
            section1_headers.append( (C,str(int(V)+1),rest) ) # We assume it will be the next verse -- right most of the time

    # Get the intro of the RV chapter/verse HTML and append it
    ourRVStartMarkerIndex = rvHTML.index( '<div class="bookIntro">' )
    ourRVEndMarkerIndex = rvHTML.rindex( '</div><!--bookIntro-->' )
    rvIntroHTML = rvHTML[ourRVStartMarkerIndex:ourRVEndMarkerIndex+22]
    book_html = f'{book_html}{rvIntroHTML}\n'

    # Get the guts of the RV chapter/verse HTML
    ourRVStartMarkerIndex = rvHTML.index( '<div class="BibleText">' )
    ourRVEndMarkerIndex = rvHTML.rindex( '<p class="chapterLinks"><a href="#C1">C1</a>' ) # This follows </div>
    rvMidHHTML = rvHTML[ourRVStartMarkerIndex:ourRVEndMarkerIndex]

    # Get the guts of the LV chapter/verse HTML
    ourLVStartMarkerIndex = lvHTML.index( '<div class="BibleText">' )
    ourLVEndMarkerIndex = lvHTML.rindex( '<p class="chapterLinks"><a href="#C1">C1</a>' ) # This follows </div>
    lvMidHHTML = lvHTML[ourLVStartMarkerIndex:ourLVEndMarkerIndex]

    # Now break the RV up by section
    rvHTMLExpandedSections = []
    for n, rvSectionHTML in enumerate( rvMidHHTML.split( '<div class="rightBox">' ) ):
        try:
            CclassIndex1 = rvSectionHTML.index( 'id="C' )
            CclassIndex2 = rvSectionHTML.index( '"', CclassIndex1+4 )
            rvStartCV = rvSectionHTML[CclassIndex1+4:CclassIndex2]
            CclassIndex8 = rvSectionHTML.rindex( 'id="C' )
            CclassIndex9 = rvSectionHTML.index( '"', CclassIndex8+4 )
            rvEndCV = rvSectionHTML[CclassIndex8+4:CclassIndex9]
            # dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"\n  {BBB} {n:,}: {startCV=} {endCV=}")
        except ValueError:
            # dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"  {n:,}: No Cid in {rvSectionHTML=}" )
            rvStartCV, rvEndCV = '', 'C1'
        if n == 0:
            rvSectionHTML = rvSectionHTML.replace( '<div class="BibleText">', '' )
        # else: # actually only for the last one
        rvSectionHTML = rvSectionHTML.replace( '</div><!--BibleText-->', '' )
        if '</div><!--rightBox-->' in rvSectionHTML:
            rvSectionHTML = f'<div class="rightBox">{rvSectionHTML}'
        assert rvSectionHTML.count('<div ')+rvSectionHTML.count('<div>') == rvSectionHTML.count('</div'), f"{BBB} {n} RV {rvStartCV} {rvEndCV} {rvSectionHTML.count('<div ')}+{rvSectionHTML.count('<div>')}={rvSectionHTML.count('<div ')+rvSectionHTML.count('<div>')} != {rvSectionHTML.count('</div')} '{rvSectionHTML}'"
        assert rvSectionHTML.count('<p ')+rvSectionHTML.count('<p>') == rvSectionHTML.count('</p'), f"{BBB} {n} RV {rvStartCV} {rvEndCV} {rvSectionHTML.count('<p ')}+{rvSectionHTML.count('<p>')}={rvSectionHTML.count('<p ')+rvSectionHTML.count('<p>')} != {rvSectionHTML.count('</p')} '{rvSectionHTML}'"
        rvHTMLExpandedSections.append( (rvStartCV, rvEndCV, rvSectionHTML) )

    # Now we need to break the LV into the same number of sections
    lvHTMLSections = []
    lastLVindex = 0
    hadVersificationErrors = False
    for n, (rvStartCV, rvEndCV, rvSectionHTML) in enumerate( rvHTMLExpandedSections ):
        nextStartCV = rvHTMLExpandedSections[n+1][0] if n < len(rvHTMLExpandedSections)-1 else 'DONE'
        dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"\n{BBB} {n}/{len(rvHTMLExpandedSections)}: {rvStartCV=} {rvEndCV=} {nextStartCV=} {lastLVindex=} lvSectionHTML='{lvMidHHTML[lastLVindex:lastLVindex+60]}...'" )
        lvSectionHTML = lvMidHHTML[lastLVindex:]
        if not rvStartCV:
            # assert n == 0 ??? No longer true now we have book introductions
            # assert lastLVindex == 0 ??? No longer true now we have book introductions
            LVindex1 = lvSectionHTML.index( '<p class="LVsentence" id="C1">' )
            section = lvSectionHTML[:LVindex1]
            dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"  {n}: {LVindex1=} '{lvSectionHTML[:LVindex1]}' then '{section[:60]}...{section[-30:]}'" )
            if section == '<div class="BibleText">\n': section = ''
            # if BBB == 'MRK': dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"A ({len(section):,}) '{section}'" ); halt
            lastLVindex = LVindex1
        elif rvStartCV == 'C1': # First CV section
            LVindex1 = lvSectionHTML.index( f'<p class="LVsentence" id="C1">' )
            if nextStartCV == 'DONE':
                section = lvSectionHTML[LVindex1:]
                dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"  {n}: {LVindex1=} remaining chars '{lvSectionHTML[:LVindex1]}' then '{lvSectionHTML[LVindex1:LVindex1+60]}...'" )
                # if BBB == 'MRK': dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"B1 ({len(section):,}) '{section}'" ); halt
            else:
                LVindex9 = lvSectionHTML.index( f' id="{nextStartCV}"', LVindex1+24 )
                # Find our way back to the start of the HTML marker
                for x in range( 30 ):
                    LVindex8 = LVindex9 - x
                    if lvSectionHTML[LVindex8] == '<':
                        break
                else:
                    dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"{lvSectionHTML[LVindex8-50:LVindex8+50]}")
                    not_far_enough
                section = lvSectionHTML[LVindex1:LVindex8].removesuffix( '\n<p class="LVsentence">' )
                dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"  {n}: {LVindex1=} {LVindex8-LVindex1} chars '{lvSectionHTML[:LVindex1]}' then '{lvSectionHTML[LVindex1:LVindex1+60]}...'" )
                # if BBB == 'MRK': dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"B2 ({len(section):,}) '{section}'" ); halt
            lastLVindex += LVindex1
            # halt
        else:
            assert n > 0
            try: LVindex2 = lvSectionHTML.index( f' id="{rvStartCV}"' )
            except ValueError:
                logging.critical( f"{BBB} Unable to find '{rvStartCV}' in LV -- probable versification error" )
                hadVersificationErrors = True
                LVindex2 = lvSectionHTML.index( f' id="C' ) # Just find any suitable place -- we won't have the correct chunk
            # Find our way back to the start of the HTML marker
            for x in range( 30 ):
                LVindex1 = LVindex2 - x
                if lvSectionHTML[LVindex1] == '<':
                    break
            else: not_far_enough
            if nextStartCV == 'DONE':
                section = lvSectionHTML[LVindex1:]
                assert section.startswith('<'), section[:10]
                dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"  {n}: {LVindex1=} remaining chars '{lvSectionHTML[:LVindex1]}' then '{lvSectionHTML[LVindex1:LVindex1+60]}...'" )
                # if BBB == 'MRK': dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"C1 ({len(section):,}) '{section}'" ); halt
            else: # in the middle
                try: LVindex9 = lvSectionHTML.index( f' id="{nextStartCV}"', LVindex2+6 )
                except ValueError:
                    logging.error( f"{BBB} {rvStartCV} Unable to find '{nextStartCV}' in LV -- probable versification error" )
                    hadVersificationErrors = True
                    LVindex9 = lvSectionHTML.index( f' id="C', LVindex2+8 ) # Just find any suitable place
                # Find our way back to the start of the HTML marker
                for x in range( 30 ):
                    LVindex8 = LVindex9 - x
                    if lvSectionHTML[LVindex8] == '<':
                        break
                else: not_far_enough
                section = lvSectionHTML[LVindex1:LVindex8]
                assert section.startswith('<'), section[:10]
                dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"  {n}: {LVindex1=} {LVindex8=} {LVindex8-LVindex1} chars '{lvSectionHTML[LVindex1:LVindex1+40]}' then '{lvSectionHTML[LVindex8:LVindex8+60]}...'" )
                # if BBB == 'MRK': dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"C2 ({len(section):,}) '{section}'" ); halt
            lastLVindex += LVindex1
            # halt
        section = section.removesuffix( '\n' ).removesuffix( '</div><!--BibleText-->' ).removesuffix( '<p class="LVsentence">' ).removesuffix( '\n' )
        if section.startswith( '<a class="upLink" ' ) or section.startswith( '<span class="v" ' ):
            section = f'<p class="LVsentence">{section}'
        assert section.count('<div ')+section.count('<div>') == section.count('</div'), f"{BBB} {n} LV {rvStartCV} {rvEndCV} {section.count('<div ')}+{section.count('<div>')}={section.count('<div ')+section.count('<div>')} != {section.count('</div')} '{section}'"
# NEXT LINE TEMPORARILY DISABLED
        if section.count('<p ')+section.count('<p>') != section.count('</p'):
            logging.error( f"{BBB} {n} LV {rvStartCV} {rvEndCV} has mismatching <p> openers: {section.count('<p ')}+{section.count('<p>')}={section.count('<p ')+section.count('<p>')} != {section.count('</p')}\n        '{section}'" )
        # assert section.count('<p ')+section.count('<p>') == section.count('</p'), f"{BBB} {n} LV {startCV} {endCV} {section.count('<p ')}+{section.count('<p>')}={section.count('<p ')+section.count('<p>')} != {section.count('</p')} '{section}'"
        lvHTMLSections.append( section )

    dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"  Got {len(rvHTMLExpandedSections)} RV section(s) and {len(lvHTMLSections)} LV section(s)")
    assert len(lvHTMLSections) == len(rvHTMLExpandedSections), f"{len(lvHTMLSections)} != {len(rvHTMLExpandedSections)}"
    # if lastLVindex < len(lvMidHHTML) - 1:
    #     newSection = lvMidHHTML[lastLVindex:]
    #     dPrint( 'Normal', DEBUGGING_THIS_MODULE, f"\n  Need to append last LV bit {len(lvMidHHTML)-lastLVindex:,} chars '{lvMidHHTML[lastLVindex:lastLVindex+40]}'")
    #     lvHTMLSections[-1] = f'{lvHTMLSections[-1]}{newSection}'
    #     # halt

    book_html = f'{book_html}\n{TWO_COLUMN_START_HTML}\n'

    # Now add each segment to the HTML
    q = 0
    for (_startCV,_endCV,rv),lv in zip( rvHTMLExpandedSections, lvHTMLSections, strict=True ):
        if DEBUGGING_THIS_MODULE and BBB == 'MRK':
            nextStartCV = rvHTMLExpandedSections[q+1][0] if q < len(rvHTMLExpandedSections)-1 else 'DONE'
            with open( OET_HTML_OutputFolderPath.joinpath(f'{BBB}-RV-{q}.html'), 'wt', encoding='utf-8' ) as html_output_file:
                html_output_file.write( f'<!DOCTYPE html><html lang="en-US"><head><title>RV {BBB} {q}</title></head><body>\n' \
                                        f'<p>{_startCV} to {_endCV} (next {nextStartCV})</p>\n{rv}</body></html>' )
            with open( OET_HTML_OutputFolderPath.joinpath(f'{BBB}-LV-{q}.html'), 'wt', encoding='utf-8' ) as html_output_file:
                html_output_file.write( f'<!DOCTYPE html><html lang="en-US"><head><title>LV {BBB} {q}</title></head><body>\n' \
                                        f'<p>{_startCV} to {_endCV} (next {nextStartCV})</p>\n{lv}</body></html>' )
        # Before we make the page, we need to remove the CV id (duplicate) fields from the LV
        Cregex, CVregex = ' id="C\\d{1,3}"', ' id="C\\d{1,3}V\\d{1,3}"'
        lv = re.sub( CVregex, '', lv)
        lv = re.sub( Cregex, '', lv)
        if DEBUGGING_THIS_MODULE:
            rv = f'{rv}<hr style="height:2px;border-width:0;color:gray;background-color:red">'
            lv = f'{lv}<hr style="height:2px;border-width:0;color:gray;background-color:orange">'
            book_html = f'{book_html}<div class="chunkRV"><p>{q}</p>{rv}</div><!--chunkRV-->\n<div class="chunkLV"><p>{q}</p>{lv}</div><!--chunkLV-->\n'
            q += 1
        else:
            book_html = f'{book_html}<div class="chunkRV">{rv}</div><!--chunkRV-->\n<div class="chunkLV">{lv}</div><!--chunkLV-->\n'
    book_html = f'{book_html}\n</div><!--container-->\n'


    usfm_header_html = f'<p class="h">{book_h_field} quick links (Skip down to <a href="#Disclaimer">book intro</a> or <a href="#C1">start of text</a>)</p>'
    chapter_links = [f'<a href="#C{chapter_num}">C{chapter_num}</a>' for chapter_num in range( 1, int(C)+1 ) ]
    chapter_html = f'<p class="chapterLinks">{EM_SPACE.join(chapter_links)}</p><!--chapterLinks-->'
    section_heading_links = [f'{heading} <a href="#C{c}V{v}">{c}:{v}</a>' for c,v,heading in section1_headers ]
    section_heading_html = f'<p class="sectionHeadingLinks">{"<br>".join(section_heading_links)}</p><!--sectionHeadingLinks-->'
    book_start_html = f'{start_html}{links_html}\n{usfm_header_html}\n{chapter_html}\n{section_heading_html}'

    return ( book_start_html,
             book_html,
             f'<h3>Quick links</h3>\n{chapter_html}\n{section_heading_html}\n{links_html}\n{END_HTML}' )
# end of pack_HTML_side-by-side.extract_and_combine_simple_HTML()


def handle_Psalms( psa_start_html:str, psa_html:str, psa_end_html:str ) -> bool:
    """
    This code is a bit fragile coz it depends on the exact formatting.
    """
    fnPrint( DEBUGGING_THIS_MODULE, f"handle_Psalms( ({len(psa_start_html):,}), ({len(psa_html):,}), ({len(psa_end_html):,}) )" )

    ITEM_NAME = 'Item'

    # print(psa_start_html); halt
    bodyIx = psa_start_html.index('<body>')
    chapterLinksIx = psa_start_html.index('<p class="chapterLinks">')
    psa_book_links_html = psa_start_html[bodyIx+6:chapterLinksIx]
    psa_chapter_links_html = psa_start_html[chapterLinksIx:].replace( 'href="#C', 'href="PSA_' ).replace( '">C', '.html">C' )
    # print(psa_top_links_html); halt

    # print(psa_html); halt
    SEARCH_CHUNK = '<span class="cPsa" id="C' # Near the start of the RV chunk
    psa_html_bits = psa_html.split( SEARCH_CHUNK )
    assert len(psa_html_bits) == 151, len(psa_html_bits)

    # print(psa_html_bits[0]); halt
    endIntroIx = psa_html_bits[0].index( '<!--bookIntro-->' )
    psa_intro_html = psa_html_bits[0][:endIntroIx+16]

    for c in range( 1, 150+1):
        start_html = SBS_START_HTML.replace( '__TITLE__', f"Song (Psalm) {c}" )
        back_forth_links = BACK_FORTH_LINKS_HTML_TEMPLATE \
            .replace( '__PREVIOUS__', f'<a href="JOB.html">Previous Book (JOB)</a>__PREVIOUS__{EM_SPACE}' ) \
            .replace( '__PREVIOUS__', '' if c==1 else f'{EM_SPACE}<a href="PSA_{c-1}.html">PSA {c-1}</a>' ) \
            .replace( '__NEXT__', f'{EM_SPACE}__NEXT__<a href="PRO.html">Next Book (PRO)</a>' ) \
            .replace( '__NEXT__', '' if c==150 else f'<a href="PSA_{c+1}.html">PSA {c+1}</a>{EM_SPACE}' ) \
            .replace( '__REST__', '')
        psalmHTML = f'{start_html}{back_forth_links}\n<h1>Song (Psalm) {c}</h1>\n' \
                    f'{SBS_DISCLAIMER_HTML}\n{SBS_BOOK_INTRO_HTML1}'
        chunkEndIx = psa_html_bits[c-1].rindex( '<!--chunkLV-->' )
        leftover_HTML = psa_html_bits[c-1][chunkEndIx+14:]
        # print(leftover_HTML); halt
        chunkEndIx = psa_html_bits[c].rindex( '<!--chunkLV-->' )
        main_PSA_HTML = psa_html_bits[c][:chunkEndIx+14]
        # print(main_PSA_HTML); halt
        psalmHTML = f'{psalmHTML}{TWO_COLUMN_START_HTML}{leftover_HTML}{SEARCH_CHUNK}' \
                    f'{main_PSA_HTML}\n</div><!--container-->\n{back_forth_links}\n{END_HTML}'
        assert "'" not in psalmHTML
        with open( OET_HTML_OutputFolderPath.joinpath(f'PSA_{c}.html'), 'wt', encoding='utf-8' ) as html_psalm_file:
            html_psalm_file.write( psalmHTML )

    psaBooksHTML = ''
    for bookname, startC, endC in (('Book 1', 1, 41), ('Book 2', 42, 72), ('Book 3', 73, 89), ('Book 4', 90, 106), ('Book 5', 107, 150)):
        psaBookHTMLrefs = f"{EM_SPACE}".join( [f'<a href="PSA_{c}.html">{ITEM_NAME} {c}</a>' for c in range( startC, endC+1 )] )
        psaBooksHTML += f"<h2>{bookname}: {ITEM_NAME}s {startC}–{endC}</h2>\n<p>{psaBookHTMLrefs}</p>\n"
    psalmsIndexHTML = SBS_PSALM_INDEX_HTML.replace('   ',' ').replace('  ', ' ').replace('\n ', '\n') \
            .replace( '__PSALMS_INDEX_MIDDLE__', f"{psa_book_links_html}{psa_intro_html}{psaBooksHTML}{psa_book_links_html}" ) \
            .replace( '__LAST_UPDATED__', f"{datetime.now().strftime('%Y-%m-%d')} <small>by {PROGRAM_NAME_VERSION}</small>" )
    assert "'" not in psalmsIndexHTML
    with open( OET_HTML_OutputFolderPath.joinpath('PSA_index.html'), 'wt', encoding='utf-8' ) as html_index_file:
        html_index_file.write( psalmsIndexHTML )

    return True
# end of pack_HTML_side-by-side.handle_Psalms()


def copy_wordlink_files( sourceFolder:Path, destinationFolder:Path ) -> bool:
    """
    Copy the SB_nnnnn.html wordlink HMTL files across.
        (There's around 168,262 of these.)
    """
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"Copying OET-LV word-link HTML files from {sourceFolder}…")
    copyCount = 0
    for filename in glob.glob( os.path.join( sourceFolder, 'SB_*.html' ) ):
        shutil.copy( filename, destinationFolder ) # Want the time to be updated or else "make" doesn't function correctly
        # shutil.copy2( filename, destinationFolder ) # copy2 copies the file attributes as well (e.g., creation date/time)
        copyCount += 1
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Copied {copyCount:,} OET-LV word-link HTML files to {destinationFolder}.")
# end of pack_HTML_side-by-side.handle_Psalms()


if __name__ == '__main__':
    # Configure basic Bible Organisational System (BOS) set-up
    parser = BibleOrgSysGlobals.setup( PROGRAM_NAME, PROGRAM_VERSION )
    BibleOrgSysGlobals.addStandardOptionsAndProcess( parser, exportAvailable=False )

    main()

    BibleOrgSysGlobals.closedown( PROGRAM_NAME, PROGRAM_VERSION )
# end of pack_HTML_side-by-side.py
