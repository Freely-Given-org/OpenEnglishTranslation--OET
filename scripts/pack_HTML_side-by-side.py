#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# pack_HTML_side-by-side.py
#
# Script to take the OET-RV-LV NT USFM files and convert to HTML
#
# Copyright (C) 2022 Robert Hunt
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
Script to backport the ULT into empty verses of the OET-RV-LV
    in order to give us the text of all the Bible,
    even if we haven't manually worked through it all carefully yet.

This script is designed to be able to be run over and over again,
    i.e., it should be able to update the OET-RV-LV with more recent ULT edits.
"""
from gettext import gettext as _
from tracemalloc import start
from typing import List, Tuple, Optional
from pathlib import Path
from datetime import datetime
import logging
import re

if __name__ == '__main__':
    import sys
    sys.path.insert( 0, '../../BibleOrgSys/' )
from BibleOrgSys import BibleOrgSysGlobals
from BibleOrgSys.BibleOrgSysGlobals import vPrint, fnPrint, dPrint
from BibleOrgSys.Bible import Bible
from BibleOrgSys.Reference.BibleOrganisationalSystems import BibleOrganisationalSystem
from BibleOrgSys.Misc import CompareBibles


LAST_MODIFIED_DATE = '2022-11-01' # by RJH
SHORT_PROGRAM_NAME = "pack_HTML_side-by-side"
PROGRAM_NAME = "Pack RV and LV simple HTML together"
PROGRAM_VERSION = '0.01'
PROGRAM_NAME_VERSION = '{} v{}'.format( SHORT_PROGRAM_NAME, PROGRAM_VERSION )

DEBUGGING_THIS_MODULE = 99


project_folderpath = Path(__file__).parent.parent # Find folders relative to this module
FG_folderpath = project_folderpath.parent # Path to find parallel Freely-Given.org repos
OET_RV_USFM_InputFolderPath = project_folderpath.joinpath( 'translatedTexts/ReadersVersion/' )
assert OET_RV_USFM_InputFolderPath.is_dir()
OET_RV_HTML_InputFolderPath = project_folderpath.joinpath( 'derivedTexts/simpleHTML/ReadersVersion/' )
assert OET_RV_HTML_InputFolderPath.is_dir()
# OET_LV_OT_USFM_InputFolderPath = project_folderpath.joinpath( 'intermediateTexts/auto_edited_OT_USFM/' )
# assert OET_LV_OT_USFM_InputFolderPath.is_dir()
# OET_LV_NT_USFM_InputFolderPath = project_folderpath.joinpath( 'intermediateTexts/auto_edited_VLT_USFM/' )
# assert OET_LV_NT_USFM_InputFolderPath.is_dir()
OET_LV_HTML_InputFolderPath = project_folderpath.joinpath( 'derivedTexts/simpleHTML/LiteralVersion/' )
assert OET_LV_HTML_InputFolderPath.is_dir()
OET_HTML_OutputFolderPath = project_folderpath.joinpath( 'derivedTexts/simpleHTML/SideBySide/' )
assert OET_HTML_OutputFolderPath.is_dir()

EN_SPACE, EM_SPACE = ' ', ' '
NARROW_NON_BREAK_SPACE = ' '
OT_BBB_LIST = ('GEN','EXO','LEV','NUM','DEU','JOS','JDG','RUT','SA1','SA2','KI1','KI2','CH1','CH2',
                'EZR','NEH','EST','JOB','PSA','PRO','ECC','SNG','ISA','JER','LAM','EZE',
                'DAN','HOS','JOL','AMO','OBA','JNA','MIC','NAH','HAB','ZEP','HAG','ZEC','MAL')
assert len(OT_BBB_LIST) == 39
# NT_BBB_LIST = ('MAT','MRK','LUK','JHN','ACT','ROM','CO1','CO2','GAL','EPH','PHP','COL','TH1','TH2','TI1','TI2','TIT','PHM','HEB','JAM','PE1','PE2','JN1','JN2','JN3','JDE','REV')
NT_BBB_LIST = ('JHN','MAT','MRK','LUK','ACT','ROM','CO1','CO2','GAL','EPH','PHP','COL','TH1','TH2','TI1','TI2','TIT','PHM','HEB','JAM','PE1','PE2','JN1','JN2','JN3','JDE','REV')
assert len(NT_BBB_LIST) == 27
BBB_LIST = OT_BBB_LIST + NT_BBB_LIST
assert len(BBB_LIST) == 66
TORAH_BOOKS_CODES = ('GEN','EXO','LEV','NUM','DEU')
assert len(TORAH_BOOKS_CODES) == 5


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
# end of pack_HTML_side-by-side.main


# If you change any colours, etc., also need to adjust the Key above
CSS_TEXT = '''div.container { display:grid; column-gap:0.6em; grid-template-columns:1fr 1fr; }
div.BibleText { }
span.upLink { font-size:1.5em; font-weight:bold; }
span.C { font-size:1.1em; color:green; }
span.V { vertical-align:super; font-size:0.5em; color:red; }
span.addedArticle { color:bisque; }
span.addedCopula { color:pink; }
span.addedDirectObject { color:brown; }
span.addedExtra { color:lightGreen; }
span.addedOwner { color:darkOrchid; }
span.added { color:grey; }
span.ul { color:darkGrey; }
span.dom { color:Gainsboro; }
span.schwa { font-size:0.75em; }
span.nominaSacra { font-weight:bold; }
p.rem { font-size:0.8em; color:grey; }
p.mt1 { font-size:1.8em; }
p.mt2 { font-size:1.3em; }
div.rightBox { float:right; width:35%; border:3px solid #73AD21; padding:10px; }
p.s1 { margin-top:0.1em; margin-bottom:0; font-weight:bold; }
p.r { margin-top:0; margin-bottom:0; font-size:0.75em; }
p.p {  margin-top:0.2em; margin-bottom:0.2em; }
p.q1 { text-indent:2em; margin-top:0.2em; margin-bottom:0.2em; }
p.q2 { text-indent:4em; margin-top:0.2em; margin-bottom:0.2em; }
'''


INDEX_INTRO_HTML = '''<!DOCTYPE html>
<html lang="en-US">
<head>
  <title>OET Development</title>
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
  <p id="Index"><a href="OET-RV-LV_GEN.html">Genesis</a> &nbsp;&nbsp;<a href="OET-RV-LV_EXO.html">Exodus</a> &nbsp;&nbsp;<a href="OET-RV-LV_LEV.html">Leviticus</a> &nbsp;&nbsp;<a href="OET-RV-LV_NUM.html">Numbers</a> &nbsp;&nbsp;<a href="OET-RV-LV_DEU.html">Deuteronomy</a><br>
    <a href="OET-RV-LV_JOS.html">Y<span class="schwa">ə</span>hōshū'a/Joshua</a> &nbsp;&nbsp;<a href="OET-RV-LV_JDG.html">Leaders/Judges</a> &nbsp;&nbsp;<a href="OET-RV-LV_RUT.html">Rūt/Ruth</a><br>
    <a href="OET-RV-LV_SA1.html">Sh<span class="schwa">ə</span>mū'ēl/Samuel 1</a> &nbsp;&nbsp;<a href="OET-RV-LV_SA2.html">Sh<span class="schwa">ə</span>mū'ēl/Samuel 2</a> &nbsp;&nbsp;<a href="OET-RV-LV_KI1.html">Kings 1</a> &nbsp;&nbsp;<a href="OET-RV-LV_KI2.html">Kings 2</a> &nbsp;&nbsp;<a href="OET-RV-LV_CH1.html">Accounts/Chronicles 1</a> &nbsp;&nbsp;<a href="OET-RV-LV_CH2.html">Accounts/Chronicles 2</a><br>
    <a href="OET-RV-LV_EZR.html">'Ez<span class="schwa">ə</span>rā'/Ezra</a> &nbsp;&nbsp;<a href="OET-RV-LV_NEH.html">N<span class="schwa">ə</span>ḩem<span class="schwa">ə</span>yāh/Nehemiah</a> &nbsp;&nbsp;<a href="OET-RV-LV_EST.html">'Eş<span class="schwa">ə</span>ttēr/Esther</a><br>
    <a href="OET-RV-LV_JOB.html">'Yuōv/Job</a> &nbsp;&nbsp;<a href="OET-RV-LV_PSA.html">Songs/Psalms</a> &nbsp;&nbsp;<a href="OET-RV-LV_PRO.html">Sayings/Proverbs</a> &nbsp;&nbsp;<a href="OET-RV-LV_ECC.html">Orator/Ecclesiastes</a> &nbsp;&nbsp;<a href="OET-RV-LV_SNG.html">Song of /Solomon</a><br>
    <a href="OET-RV-LV_ISA.html">Y<span class="schwa">ə</span>sha'<span class="schwa">ə</span>yāh/Isaiah</a> &nbsp;&nbsp;<a href="OET-RV-LV_JER.html">Yir<span class="schwa">ə</span>m<span class="schwa">ə</span>yāh/Jeremiah</a> &nbsp;&nbsp;<a href="OET-RV-LV_LAM.html">Wailings/Lamentations</a> &nbsp;&nbsp;<a href="OET-RV-LV_EZE.html">Y<span class="schwa">ə</span>ḩez<span class="schwa">ə</span>qē'l/Ezekiel</a><br>
    <a href="OET-RV-LV_DAN.html">Dāniyyē'l/Daniel</a> &nbsp;&nbsp;<a href="OET-RV-LV_HOS.html">Hōshē'a/Hosea</a> &nbsp;&nbsp;<a href="OET-RV-LV_JOL.html">Yō'ēl/Joel</a> &nbsp;&nbsp;<a href="OET-RV-LV_AMO.html">'Āmōʦ/Amos</a><br>
    <a href="OET-RV-LV_OBA.html">'Ovad<span class="schwa">ə</span>yāh/Obadiah</a> &nbsp;&nbsp;<a href="OET-RV-LV_JNA.html">Yōnāh/Jonah</a> &nbsp;&nbsp;<a href="OET-RV-LV_MIC.html">Mīkāh/Micah</a> &nbsp;&nbsp;<a href="OET-RV-LV_NAH.html">Naḩūm/Nahum</a><br>
    <a href="OET-RV-LV_HAB.html">Ḩavaqqūq/Habakkuk</a> &nbsp;&nbsp;<a href="OET-RV-LV_ZEP.html">Ts<span class="schwa">ə</span>fan<span class="schwa">ə</span>yāh/Zephaniah</a> &nbsp;&nbsp;<a href="OET-RV-LV_HAG.html">Ḩaggay/Haggai</a> &nbsp;&nbsp;<a href="OET-RV-LV_ZEC.html">Z<span class="schwa">ə</span>kar<span class="schwa">ə</span>yāh/Zechariah</a> &nbsp;&nbsp;<a href="OET-RV-LV_MAL.html">Mal<span class="schwa">ə</span>'ākī/Malachi</a></p>
  <!--<p>Whole <a href="OET-RV-LV-Torah.html">Torah/Pentateuch</a>
    (long and slower to load, but useful for easy searching of multiple books, etc.)</p>-->
  <h3><b>NT</b> v0.00</h3>
  <p>Note that the <em>OET</em> places Yōannēs/John before Matthaios/Matthew.</p>
  <p><a href="OET-RV-LV_JHN.html">Yōannēs/John</a> &nbsp;&nbsp;<a href="OET-RV-LV_MAT.html">Matthaios/Matthew</a> &nbsp;&nbsp;<a href="OET-RV-LV_MRK.html">Markos/Mark</a> &nbsp;&nbsp;<a href="OET-RV-LV_LUK.html">Loukas/Luke</a> &nbsp;&nbsp;<a href="OET-RV-LV_ACT.html">Acts</a><br>
    <a href="OET-RV-LV_ROM.html">Romans</a> &nbsp;&nbsp;<a href="OET-RV-LV_CO1.html">Corinthians 1</a> &nbsp;&nbsp;<a href="OET-RV-LV_CO2.html">Corinthians 2</a><br>
    <a href="OET-RV-LV_GAL.html">Galatians</a> &nbsp;&nbsp;<a href="OET-RV-LV_EPH.html">Ephesians</a> &nbsp;&nbsp;<a href="OET-RV-LV_PHP.html">Philippians</a> &nbsp;&nbsp;<a href="OET-RV-LV_COL.html">Colossians</a><br>
    <a href="OET-RV-LV_TH1.html">Thessalonians 1</a> &nbsp;&nbsp;<a href="OET-RV-LV_TH2.html">Thessalonians 2</a> &nbsp;&nbsp;<a href="OET-RV-LV_TI1.html">Timotheos/Timothy 1</a> &nbsp;&nbsp;<a href="OET-RV-LV_TI2.html">Timotheos/Timothy 2</a> &nbsp;&nbsp;<a href="OET-RV-LV_TIT.html">Titos/Titus</a><br>
    <a href="OET-RV-LV_PHM.html">Filēmoni/Philemon</a><br>
    <a href="OET-RV-LV_HEB.html">Hebrews</a><br>
    <a href="OET-RV-LV_JAM.html">Yakōbos/James</a><br>
    <a href="OET-RV-LV_PE1.html">Petros/Peter 1</a> &nbsp;&nbsp;<a href="OET-RV-LV_PE2.html">Petros/Peter 2</a><br>
    <a href="OET-RV-LV_JN1.html">Yōannēs/John 1</a> &nbsp;&nbsp;<a href="OET-RV-LV_JN2.html">Yōannēs/John 2</a> &nbsp;&nbsp;<a href="OET-RV-LV_JN3.html">Yōannēs/John 3</a><br>
    <a href="OET-RV-LV_JDE.html">Youdas/Jude</a><br>
    <a href="OET-RV-LV_REV.html">Revelation</a></p>
  <!--<p>Whole <a href="OET-RV-LV-NT.html">New Testament</a>
    (long and slower to load, but useful for easy searching of multiple books, etc.)</p>-->
  <h2 id="Intro">Introduction</h2>
  <h3>The Open English Translation of the Bible (OET)</h3>
      <p>The <em>Readers’ Version</em> (OET-RV) and the <em>Literal Version</em> (OET-LV)
        side-by-side, together make up the OET.</p>
      <p>So why two versions? Well, many people ask the question:
        <i>Which English Bible translation should I use?</i>
        And often the answer is that there’s no single Bible translation which can meet
        all of the needs of the thoughtful reader.
        Why not? It’s because we often have two related desires that we need answered:<p>
      <ol><li>What does the original (Hebrew or Greek) text actually say? and</li>
        <li>What did the original writer mean? (i.e., What should we understand from it?)</li></ol>
      <p>Our answer has always been that it’s best to use <b>two</b> translations—one more <b>literal</b>
        to give a window into the actual Hebrew or Greek words, and one more <b>dynamic</b>
        that’s easier for us modern readers to understand—as much to do with our
        totally different cultures as to do with our different languages.</p>
      <p>So the <em>OET</em> gives both side-by-side, and with the advantage that
        both the <em>Literal Version</em> and the <em>Readers’ Version</em>
        <b>have been specifically designed to be used together</b> in this way.
        We suggest reading down the <em>Readers’ Version</em> on the left,
            and if something stands out and you think in your mind
            <i>Does it really say that?</i> or <i>Could it really mean that?</i>,
            then flick your eyes across to the <em>Literal Version</em>
            and see for yourself what’s really there in the original texts.</p>
      <p>On the other hand if you’ve been reading the Bible for a few decades already,
        maybe it would be fun to work through the <em>Literal Version</em> to get fresh insight
        into what’s actually written there in those original languages.
        It won’t be easy reading,
        but it should be insightful as the different wording will require more concentration.</p>
  <h3 id="Goals">Goals</h3>
    <p>Put simply, the goal of the <em>Open English Translation</em> is simply to
        <b>make the Bible more accessible to this current generation</b>
        with the best of a free-and-open easy-to-understand <em>Readers’ Version</em>
        alongside a faithful <em>Literal Version</em> so that you yourself can checkout what was said and what is interpreted.</p>
    <p id="LearningGoal">A secondary goal is to expose more people to some of the background of where our Bibles come from
        and how translators make decisions,
        i.e., <b>to teach</b> a little more about original manuscripts
        and to challenge a little more about translation traditions that can possibly be improved.<p>
  <h3 id="Distinctives">Distinctives</h3>
    <p>The OET has the following distinguishing points:</p>
    <ul><li>An easy-to-understand <em>Readers’ Version</em> side-by-side with a very <em>Literal Version</em></li>
    <li>A generous open license so that the <em>Open English Translation</em> can be
            freely used in any Bible app or website, or printed in your church Bible-study notes
            without even needing to request permission.</li>
    <li>The <em>Readers’ Version</em> has section headings and cross-references
            and most of the other features that help modern Bible readers.</li>
    <li>The <em>Readers’ Version</em> uses modern units for all measurements (easy to understand and visualise),
            whereas the <em>Literal Version</em> retains the ancient units (useful for historical and symbolic studies).</li>
    <li>The <em>Readers’ Version</em> uses well-known figures of speech,
            or if the original figure of speech is not readily understandable,
            explains the point that the author appears to be trying to express.
        On the other hand, the <em>Literal Version</em> retains the original figurative language
            (even if it’s not a figure of speech that we are familiar with).</li>
    <li>The <em>Readers’ Version</em> is less formal than most modern English Bible translations,
            for example, we would use contracted words like <i>we’ll</i> and <i>didn’t</i>,
            especially when it’s in direct speech.
        (Always remember that the Bible was written in the languages of the common people.)</li>
    <li>The <em>Readers’ Version</em> uses section headings
            which are very helpful to skim through when trying to locate a certain passage.
        However, you’ll quickly notice that they are formatted in such a way
            as not to break the flow of the letter or narrative.
        This is to visually help the reader to appreciate the full context
            of the part they’re reading,
            and not to ignore the connections with what came before and what follows.</li>
    <li>Being a 21<span style="vertical-align:super;font-size:0.8em;">st</span> century translation done in an era
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
        would have no idea that there’s no <b>J</b> letter or sound in either Hebrew or Greek,
        plus there’s absolutely no such name as <i>James</i> in the New Testament manuscripts!)</li>
    <li>In addition to wanting to get names and placenames more accurate,
        we’ve also attempted to modernise and simplify the spelling (transliterations) of these names
        to make it easier for readers to pronounce them as they come across them,
        e.g., using <b>f</b> instead of <b>ph</b>, so <i>Epafras</i> instead of <i>Epaphras</i>.
        (Oddly, even traditional English Bible translations surprisingly
        do use <i>Felix</i> and <i>Festus</i>.)</li>
    <li>With regular words, we’ve tried to do the opposite,
        i.e., to use less Greek rather than more wherever possible.
        So a word like <i>baptise</i> (which is an adapted transliteration of the Greek verb),
        actually gets translated, so this example becomes <i>immerse</i>.</li>
    <li><i>Italics</i> are only used for <em>emphasis</em>, not to indicate <i>added words</i> as historically done in
        older translations due to limitations of the original printing processes.
        The <em>OET</em> fixes the problem where most modern printing uses <i>italics</i> for <em>emphasis</em>
        whereas older Bibles use <i>italics</i> for the words which should actually be <b>deemphasised</b>,
        i.e., the words which actually <b>aren’t</b> in the original manuscripts!</li>
    <li>The English <i>Christ</i> is an adapted transliteration of the Koine Greek word <i>Kristos</i>
            used for the original Hebrew <i>Messiah</i>.
        (It’s not Jesus’ surname!)
        It seems to make sense to only use one word consistently
            rather than using two words for the same thing
            (just because they came from two different languages),
            so the <em>OET</em> has elected to only use <i>Messiah</i>.
        However, these words actually have a meaning, just as <i>President</i> is not just a title,
            but someone who <i>presides</i> over governmental meetings.
        So going a step further, we have chosen to use the contemporary
            <b>meaning</b> of the word in the <em>Literal Version</em>.
        The original meaning is <i>one who is anointed</i> (by pouring a hornful of oil over them),
            but we use the derived meaning which is <i>one who is selected/chosen (by God)</i>.</li>
    <li>Most readers living in modern democracies
            have never been familiar with the concept of an ancient king or <i>lord</i>
            who has the power of life and death over them.
        Thus the title <i>Lord Jesus</i> is easily said,
            yet relatively few actually live with Jesus as the lord of their thoughts and actions and daily activities.
        (Just think how many would embarrassingly rush to turn off the video they’re streaming
            if Jesus appeared in the room.)
        As a reaction to the word <i>Lord</i> seemingly becoming so cliché for many Christians,
            we use the translation <i>master</i> as a way to get readers to at least
            think a little more about what the concept might mean.
        (The word <i>boss</i> felt a little informal.)</li>
    <li>The <em>Literal Version</em> tries to add as little as possible
            that’s not actually there in the original manuscripts.
        Of course, we add spaces between words so we can read it faster,
            and we add capitals at the start of sentences as per standard, modern English,
        but we don’t capitalise words like <i>Kingdom of Heaven</i>
            or even <i>He</i> when it refers to Jesus,
            because the concept of capital and small letters didn’t even exist
            when original manuscripts like
            <a href="https://greekcntr.org/manuscripts/data/1G20001.htm">this portion</a> were written.
        (Our policy has more to do with accuracy and education
            than it does with “lack of respect” or any such thing.
        Often this goes against religious tradition of the last few centuries,
            but just because something is traditional,
            does not necessarily mean that it is correct or even helpful.)</li>
    <li>Most dialects of modern English don’t distinguish between <i>you (singular)</i> referring to just one person,
        and <i>you (plural)</i> referring to a group of people.
        However, the original languages clearly distinguish these,
        so in order to indicate this to our readers
        the <em>Literal Version</em> uses <i>you<span class="ul">_</span>all</i> for the plural form
        (although we are aware that some modern dialects now prefer <i>yous</i>).</li>
    <li>Because the <em>Literal Version</em> so closely follows the original languages,
            it’s important to remember that words often don’t match one-to-one between languages.
        This is one reason why the <em>LV</em> reads strangely:
            because we try to avoid using different English words if we can;
            knowing that the <em>LV</em> will not be natural English.
        Again, this is because we want the <em>LV</em> to be
            a window into what’s actually written in the original languages.
        For fluent English (like in the <em>Readers’ Version</em>) the same Greek word
            might require several different translations when used in different contexts.
        For example, the Greek word translated <i>raise</i> in the <em>LV</em>
            would likely require the following changes:
        <ol>
            <li>to <i>raise</i> from sitting, we’d want: <i>stand up</i></li>
            <li>to <i>raise</i> from bed, we’d want: <i>get up</i></li>
            <li>to <i>raise</i> from the grave, we’d want: <i>come back to life</i></li>
            <li>to <i>raise</i> an object, we’d want: <i>lift up</i></li>
        </ol>
        However, we would also be able to understand <i>raise</i> in each of those cases.</li>
    <li>These particular pages use British spelling,
        but American spelling will also be available in the future.</li>
    <li>Our preference in most editions is to place <em>The Gospel according to John</em>
            <b>before</b> <em>Matthew</em>.
        This has a couple of advantages:
        <ol><li>The Old Testament starts with “In the beginning, God created…”
            and the New Testament starts with “In the beginning was the Word…”.<li>
        <li><em>Acts</em> ends up right after the first book by its author <em>Luke</em>.</li>
        <li>It just reminds readers that the order of the “books” in the Bible
            is not set by sacred degree--only by tradition.</li>
        </ol>
        Some do complain that the traditional order of the first four gospel accounts
            represent the lion, the calf, the man, and the eagle of Rev 4:6-7
            which allegedly match with the banners (not described in the Bible) of the four divisions
            of the tribes of Israel mentioned in Numbers 2.</li>
    <li>Beware of some traps interpreting the <em>Literal Version</em>.
        Because it’s not designed to be used alone (but rather alongside the <em>Readers’ Version</em>)
        it’s <b>much more literal</b> than most other “literal versions”.
        You will quickly notice the deemphasis of words that had to be added
        to make the English sentences even make sense.
        But there’s at least two other things that aren’t necessarily changed
        in the English <em>Literal Version</em>:
        <ol>
            <li>Other languages use the negative differently,
                    especially when it’s doubled or tripled in the sentence.
                If you don’t understand this,
                you could easily think that the original means the opposite of what the words actually appear to say.
                For example the double negative: “You are not caring about no one.” (adapted from Matthew 22:16).
                In natural, fluent English, we would have to reverse the second negative to get the expected meaning,
                    ending up with <i>anyone</i> as you’ll find in the <em>Readers’ Version</em>.
                But in Greek, the second negative adds emphasis rather than reversing the first negative.
                So our <em>Literal Version</em> shows you the words that are actually there
                    (in the Greek in this case).</li>
            <li>Other languages may omit (or <i>elide</i>) words which are clearly implied to the original reader,
                but which the modern English reader finds strange,
                e.g., a son may be divided against his father, and a daughter her mother.
                The elided words are “may be divided against”.</li>
        </ul>
        Always check the <em>Readers’ Version</em> carefully for how it is translated into modern, idiomatic English
        before jumping to any conclusions of your own about what the original language says or doesn’t say.</li>
    </ul>
  <h3 id="Key">Key to symbols and colours in the OET-RV-LV</h3>
    <p>You will notice the the <em>Literal Version</em> looks different from most Bibles that you’re used to:</p>
    <ul><li>Underline/underscore characters: Words joined together by underlines are translated from a single original word,
        e.g., <em>he<span class="ul">_</span>is<span class="ul">_</span>walking</em>.
        Both Hebrew and Greek can express the subject as part of the verb,
        often saying in one word what takes us three.</li>
    <li>Hanging underline/underscore characters: Word groups with hanging underlines mean that to make natural English,
        we needed to insert the translation of one word into the middle of another,
        e.g., <em>not he<span class="ul">_</span>is<span class="ul">_</span>walking</em> becomes much more natural in English if
        rearranged to <em>he<span class="ul">_</span>is<span class="ul">_</span> &nbsp;not&nbsp; <span class="ul">_</span>walking</em>.
        But we can still figure out from the hanging underlines that the two parts either side of <em>not</em>
        are translated from a single original language word.</li>
    <li><span class="addedArticle">Grey</span> words indicate added articles.
        English uses <em>a</em> or <em>the</em> to indicate whether a noun
        is indefinite or definite.
        Other languages don’t necessarily work the same way.
        Neither Hebrew nor Greek have a word for English “<i>a</i>”.
        If we have to add an article to make the English sound correct, we indicate this by greying it,
        e.g., <em><span class="addedArticle">the</span> man</em>.
        (We use lighter colours to deemphasise added words like these rather than using <i>italics</i> like most Bibles,
        because apart from Bibles, <i>italics</i> are mostly used these days for emphasis.)</li>
    <li><span class="addedCopula">Light pink</span>: A copula is a word that links a subject and its complement (or description),
        e.g., the word <i><span class="addedCopula">is</span></i> in the sentence <i>The house <span class="addedCopula">is</span> white.</i>
        Other languages don’t necessarily work the same way and can say things like
        <i>White the house.</i>
        Added copulas are marked with this <span class="addedCopula">light colour</span>.</li>
    <li><span class="addedDirectObject">Light brown</span>: Certain English verbs require a direct object. Think of the difference between
        <i>He said, blah, blah</i> and <i>He told, blah, blah</i>.
        The second one feels like it requires something like <i>He told <span class="addedDirectObject">him</span>, blah, blah</i>.
        Added direct and indirect objects are marked with
        a <span class="addedDirectObject">light colour</span>.</li>
    <li><span class="addedExtra">Light green</span>:
        In other languages it may be possible to say something
        like <i>The having<span class="ul">_</span>fallen</i>….
        In English, we must say something like
        <i>The <span class="addedExtra">one</span> having<span class="ul">_</span>fallen</i>…
        or <i>The <span class="addedExtra">person</span> having fallen</i>….
        If the article and verb are marked as <b>plural</b> in the source language,
            we may be able to say
            <i>The <span class="addedExtra">ones</span> having<span class="ul">_</span>fallen</i>….
        If the article is marked as feminine in the source language, we may be able to say
            <i>The <span class="addedExtra">woman</span> having<span class="ul">_</span>fallen</i>….
        Added words like this are marked with this <span class="addedExtra">light colour</span>.</li>
    <li><span class="addedOwner">Light purple</span>: If we have an original construction like <i>God spoke by son</i> (from Heb 1:2),
        in English we need to add a word like <i>God spoke by <span class="addedArticle">the</span> son</i> or <i>God spoke by <span class="addedOwner">his</span> son</i>.
        In the latter case (where we don’t just choose an article like <i><span class="addedArticle">the</span></i>),
        we mark these added words with this <span class="addedOwner">light colour</span>.</li>
    <li><span class="added">Light orange</span>: Other added words not in the above categories are marked with this <span class="added">light colour</span>.</li>
    <li>All of this colouring is to be completely open by helping the reader to be able to see where the translators have chosen to
        add words to the Hebrew or Greek in order to make the English sound slightly better,
        even though this has been kept to an absolute minimum in the <em>Literal Version</em>.</li>
    <li><span class="nominaSacra">Bold text</span>: In the earliest copies of the original manuscripts,
        it appears that the scribes marked a small set of words that they considered
        to refer to <span class="nominaSacra">God</span>.
        (These markings are known as <a href="https://en.wikipedia.org/wiki/Nomina_sacra"><em>nomina sacra</em></a>
        or <em>sacred naming</em>.)
        Other Bible translations do not indicate these special markings,
        however in the <em>Literal Version New Testament</em> we help the reader by making
        these marked words <span class="nominaSacra">stand out</span>.</li>
    <li>Where it is determined that a group of words was either definitely or most likely
        not in the original manuscripts (autographs),
        they are omitted in the <em>OET-RV-LV</em> without any notes.
        These manuscript decisions were mostly made by the authors of the two main works that we relied on to translate
        the <em>OET</em> from—see the acknowledgements below for more details.)</li>
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
        but we’ll do better than our traditional Bible translations.</p>
    <p>As a general rule, even if you started to think of the letter <i>J</i> in
        Bible names like the Germans or the Dutch (the two languages closest to English)
        pronounce <i>Ja</i> (as <i>Ya</i>),
        you’d already be taking a big step towards getting Biblical names more correct.
        (This deviation is not any kind of conspiracy—simply
        an unfortunate accident of history and continuous language change.)<p>
    <p>In the New Testament, the situation is already complicated by the fact that
        Old Testament (Hebrew) names have been written as Greek-speakers would think of them.
        So English <i>Jesus</i>
        (which you now realise should be pronounced more like <i>Yesus</i>
        as there’s no <i>j</i> sound in either Hebrew or Greek)
        is actually more like <i>Yaysous</i> in Greek.
        But it’s likely that his “parents” (using Hebrew or the related Aramaic/Syrian language at the time)
        actually named the child something more like <i>Y<span class="schwa">ə</span>hōshū'a</i>
        (from which we get <i>Joshua</i>).
        So which name should we call him in the text?
        Because the New Testament manuscripts are written in Koine Greek,
        we have chosen to give preference to the Greek forms of the names in the New Testament.
        However, the first time a name is used, we show both forms
        like <i>Yaʸsous/(Y<span class="schwa">ə</span>hōshū'a)</i>.
        Where the name is repeated nearby, we’ll only show the Greek form like <i>Yaʸsous</i>.
        (Again, it’s an accident of history that English speakers will name a child <i>Joshua</i>,
        but would not name him <i>Jesus</i> when they’re really just the same name in different forms.
        Speakers of languages with Spanish influence don’t have that same hesitation,
        so <i>Jesus</i> is a common name in South America for example.)
    <p>Note that where Hebrew or Greek transliterations are given,
        English speakers will have the most success pronouncing these names if you
        look up the pronounciation of the five “pure” Spanish vowels in your search engine.
        Individual vowels should be pronounced in this way,
        e.g., each of the four vowels in <i>Eleazar</i>.</p>
    <p>Macrons (overlines over the vowels, like <i>ē</i> or <i>ō</i>) indicate lengthened vowels,
        so the pronounciation is the same as the Spanish vowels,
        but just prolonged.
        (If you’re wondering which syllable to put the stress/emphasis on,
            it’ll often be one of the ones with a long vowel.
        We decided not to indicate stress on the names
            or there would have been even more marks and squiggles on the letters!)</p>
    <p>The vowel <a href="https://en.wikipedia.org/wiki/Schwa">schwa</a> <i><span class="schwa">ə</span></i>
        (in names that come from Hebrew with <a href="https://en.wikipedia.org/wiki/Shva">shva</a>)
        should be regarded as a fleeting (very short and unstressed), neutral vowel
        which is the minimal vowel required to linguistically join the surrounding consonants
        e.g., in <i>Y<span class="schwa">ə</span>hūdāh</i>.</p>
    <p>Dipthongs (e.g., <i>ai</i>, <i>au</i>, <i>ei</i>, <i>oi</i>, <i>ou</i>)
        are a limited set of two vowels,
        where one vowel glides into the other,
        so even though the spelling of a dipthong is two letters,
        together they are the centre of only one syllable.
        Note that we use <i>aʸ</i> for Greek letter (eta),
        because it’s actually only one letter, not a dipthong,
        even though it’s pronounced very much like <i>ai</i>.<p>
    <p>We use the symbol ' to mark a <a href="https://en.wikipedia.org/wiki/Glottal_stop">glottal stop</a>
        which is the sound that some UK speakers put in the middle of the word <i>butter</i> (ba'a),
        so <i>Abra'am</i> (from the Greek) is three distinct syllables—those
        two <i>a</i>’s side-by-side should not be made into a long <i>ā</i>.</p>
  <h3 id="Learning">Learning</h3>
    <p>As mentioned in our <a href="#Goals">Goals above</a>, one of
        our main goals is to <a href="#LearningGoal">educate</a> our readers about how we get our Bibles.
        Here are some of the main points:</p>
    <ul><li>Biblical names are often very mangled in English translations.
            We’ve already covered this extensively <a href="#Names">above</a>.</li>
        <li>The <em>Open English Translation</em> makes it possible to learn how Bible translation is done.
            This is because reading the <em>Literal Version</em> gives you a good insight into
                what’s actually written in the original manuscripts.
            Then you can read the same passage in the <em>Readers’ Version</em>
                or your favourite other translation,
                and you’ll get a good idea of the rearranging and interpreting that
                Bible translators have to do to get good, understandable translations
                in any modern language.</li>
        <li>Some editions of the OET have the “books” in different orders
                and in different combinations.
            Remember that different Bible originals were originally written on scrolls
                and weren’t combined into a <a href="https://en.wikipedia.org/wiki/Codex">book form</a> similar to
                what we’re accustomed to until many centuries later.
            But of course, the individual scrolls could easily be placed in a different order.
            The traditional <a href="https://en.wikipedia.org/wiki/Hebrew_Bible">Hebrew Bible<a/>
            not only has what we typically refer to as the <i>Old Testament</i> “books” in a different order,
            they also have different names, are grouped into different categories,
            and are combined/separated into a different number of “books”.
            Most readers of Bibles from the West have no idea that Ezra and Nehemiah
                describe some of the latest Old Testament events as far as timelines go.</li>
        <li>Chapter and verse divisions were not in the original manuscripts and came
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
            Verses don’t <i>say</i> anything, and
                we shouldn’t be guilty of quoting short texts out of context.</li>
    </ul>
  <h3 id="Acknowledgements">Acknowledgements</h3>
    <p>A work like this could not be done with building on the work of so many that have gone before, including:</p>
    <ul><li>The creator God who communicates with us in various ways,
        but who specifically inspired the writing of the Scriptures
        and caused it to be preserved throughout the millenia
        despite the best efforts of some who tried to destroy them.</li>
    <li>Those who took the time to write down their interactions with God and his messengers,
        beginning with Moses and those before him who wrote down their experiences even though making the writing materials was so much work,
        all the way through to the disciples and others who wrote of their interactions with Yaʸsous the Messiah, and the Holy Spirit.</li>
    <li>Those who faithfully copied and carefully stored those manuscripts over the centuries
        and thus allowed the works of the original writers to be preserved for us to translate.</li>
    <li>Those who collected, preserved, photographed and digitized, and transcribed those manuscripts
        so that we could have access to them.</li>
    <li>Those who studied the variations in those copies and helped us to get the best evaluations of
        which words were most likely present in the original manuscripts (<a href="https://en.wikipedia.org/wiki/Autograph">autographs</a>).
        For the (mostly) Hebrew Old Testament, we are especially reliant on the Statistical Restoration work
        of <a href="https://hb.OpenScriptures.org/">Open Scriptures</a>, given to the world under a generous open licence.
        For the Greek New Testament, we are especially reliant on the work
        of the <a href="https://GreekCNTR.org">Center for New Testament Restoration</a>
        which is also given to the world under a generous open licence.</li>
    </ul>
  <h3 id="Status">Status</h3>
    <p>English sentences have more limitations on their word order than Greek sentences do.
        So any word-for-word Greek literal translation has to be reordered to be readable in English.
        Currently, the words in the following books (just over 50% of the NT) have been mostly reordered:
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
        If you’re reading this and notice problems or issues,
        please do contact us by <a href="mailto:Freely.Given.org@gmail.com?subject=OET-RV-LV Feedback">email</a>.
        Also, if there’s something that we didn’t explain in this introduction, or didn’t explain very well.
        Thanks.</p>
  <p>HTML last updated: __LAST_UPDATED__</p>
</body></html>
'''

RV_FAQ_HTML = '''<!DOCTYPE html>
<html lang="en-US">
<head>
  <title>OET Development</title>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="keywords" content="Bible, translation, OET, English, literal, readers, modern, FAQ, free">
  <link rel="stylesheet" type="text/css" href="BibleBook.css">
</head>
<body>
  <p><a href="../">Up</a></p>
  <h1>Open English Translation (OET) Development</h1>
  <h2>Frequently Asked Questions (FAQs)</h2>
  <h3>What are the bolded words in the <em>Literal Version</em>?</h3>
  <p>As explained in the <a href="index.html#Key">Key</a>, the bold text
  indicates the use of <em>Nomina Sacra</em> on the original manuscripts.
  These are special markings and abbreviations done by the scribes,
  and in the earliest manuscripts, highlight words that are assumed to relate to God.</p>
  <h3 id="Feedback">Feedback</h3>
    <p>These web pages are a very preliminary preview into a work still in progress.
        The <em>OET</em> is not yet finished, and not yet publicly released,
        but we need to have it available online for easy access for our checkers and reviewers.
        If you’re reading this and have questions that aren’t discussed here,
        please do contact us by <a href="mailto:Freely.Given.org@gmail.com?subject=OET FAQs">email</a>.
        Also, if there’s something that we didn’t explain in this introduction, or didn’t explain very well.
        Thanks.</p>
  <p>HTML last updated: __LAST_UPDATED__</p>
</body></html>
'''

DISCLAIMER_HTML = '''<p>Note: This is still a very early look into the unfinished text
of the <em>Open English Translation</em> of the Bible.
Please double-check the text before using in public.</p>
'''

SBS_BOOK_INTRO_HTML1 = '''<p>Note: The <em>Readers’ Version</em> on the left is a translation
into contemporary English aimed at <i>the person on the street</i> who
hasn’t necessarily been brought up with exposure to Biblical jargon and/or King James English.
It’s designed to be used alongside the <em>Literal Version</em> on the right which gives
the English reader a window into what is actually written in the original languages.
(See the <a href="index.html#Intro">introduction</a> for more details—we
recommend that you read the introduction first if you’re wanting to fully understand the <em>Literal Version</em>.)
By comparing the left and right columns, you should be able to easily get the message of the text,
while at the same time keeping an eye on what it was actually translated from.</p>
'''

INTRO_PRAYER_HTML = '''<p style="text-align:center">It is our prayer that the
<em>Open English Translation</em> of the Bible will give you clear understanding of
the messages written by the inspired Biblical writers.</p>
'''

START_HTML = '''<!DOCTYPE html>
<html lang="en-US">
<head>
  <title>__TITLE__</title>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="keywords" content="Bible, OET, translation, English, literal, readers, version, modern, free">
  <link rel="stylesheet" type="text/css" href="BibleBook.css">
</head>
<body>
'''
END_HTML = '</body></html>\n'

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

            source_RV_filename = f'OET-RV_{BBB}.html'
            source_LV_filename = f'OET-LV_{BBB}.html'
            with open( OET_RV_HTML_InputFolderPath.joinpath(source_RV_filename), 'rt', encoding='utf-8' ) as html_input_file:
                rv_html = html_input_file.read()
            with open( OET_LV_HTML_InputFolderPath.joinpath(source_LV_filename), 'rt', encoding='utf-8' ) as html_input_file:
                lv_html = html_input_file.read()

            book_start_html, book_html, book_end_html = extract_and_combine_simple_HTML( BBB, rv_usfm_text, rv_html, lv_html )

            output_filename = f'OET-RV-LV_{BBB}.html'
            with open( OET_HTML_OutputFolderPath.joinpath(output_filename), 'wt', encoding='utf-8' ) as html_output_file:
                html_output_file.write( f'{book_start_html}\n{book_html}\n{book_end_html}' )

            # # Having saved the book file, now for better orientation within the long file (wholeTorah or wholeNT),
            # #   adjust book_html to include BBB text for chapters past chapter one
            # bookAbbrev = BBB.title().replace('1','-1').replace('2','-2').replace('3','-3')
            # chapterRegEx = re.compile('<span class="C" id="C(\d{1,3})V1">(\d{1,3})</span>')
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

    # Output CSS and index and whole NT html
    with open( OET_HTML_OutputFolderPath.joinpath('BibleBook.css'), 'wt', encoding='utf-8' ) as css_output_file:
        css_output_file.write( CSS_TEXT )
    indexIntroHTML = INDEX_INTRO_HTML.replace('   ',' ').replace('  ', ' ').replace('\n ', '\n') \
            .replace( '__LAST_UPDATED__', f"{datetime.now().strftime('%Y-%m-%d')} <small>by {PROGRAM_NAME_VERSION}</small>" )
    with open( OET_HTML_OutputFolderPath.joinpath('index.html'), 'wt', encoding='utf-8' ) as html_index_file:
        html_index_file.write( indexIntroHTML )
    faqHTML = RV_FAQ_HTML.replace('   ',' ').replace('  ', ' ').replace('\n ', '\n') \
            .replace( '__LAST_UPDATED__', f"{datetime.now().strftime('%Y-%m-%d')} <small>by {PROGRAM_NAME_VERSION}</small>" )
    with open( OET_HTML_OutputFolderPath.joinpath('FAQs.html'), 'wt', encoding='utf-8' ) as html_FAQ_file:
        html_FAQ_file.write( faqHTML )
    
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


def extract_and_combine_simple_HTML( BBB:str, rvUSFM:str, rvHTML:str, lvHTML:str ) -> Tuple[str, str, str]:
    """
    We use the RV USFM to find the book name, etc.
    """
    fnPrint( DEBUGGING_THIS_MODULE, f"extract_and_combine_simple_HTML( {BBB}, ({len(rvUSFM):,}), ({len(rvHTML):,}), ({len(lvHTML):,}) )" )

    links_html_template = '<p>__PREVIOUS__OET-RV-LV <a href="index.html#Index">Book index</a>,' \
                 ' <a href="index.html#Intro">Intro</a>, <a href="index.html#Key">Key</a>,' \
                 'and <a href="FAQs.html">FAQs</a>' \
                 f'__NEXT__<br><br>__REST__</p>'
    if BBB in OT_BBB_LIST:
        links_html = links_html_template.replace('__REST__', '' ) #'Whole <a href="OET-RV-LV-Torah.html">Torah/Pentateuch</a> (for easy searching of multiple books, etc.)' )

        previousBBB = OT_BBB_LIST[OT_BBB_LIST.index(BBB)-1] # Gives wrong value (@[-1]) for first book
        try: nextBBB = OT_BBB_LIST[OT_BBB_LIST.index(BBB)+1]
        except IndexError: nextBBB = NT_BBB_LIST[0] # above line fails on final book
        links_html = links_html.replace( '__PREVIOUS__', '' if BBB==NT_BBB_LIST[0]
            else f'<a href="OET-RV-LV_{previousBBB}.html">Previous Book ({previousBBB})</a>{EM_SPACE}')
        links_html = links_html.replace( '__NEXT__', f'{EM_SPACE}<a href="OET-RV-LV_{nextBBB}.html">Next Book ({nextBBB})</a>')
    elif BBB in NT_BBB_LIST:
        links_html = links_html_template.replace('__REST__', '' ) #'Whole <a href="OET-RV-LV-NT.html">New Testament</a> (for easy searching of multiple books, etc.)' )

        previousBBB = OT_BBB_LIST[-1] if BBB==NT_BBB_LIST[0] else NT_BBB_LIST[NT_BBB_LIST.index(BBB)-1] # Gives wrong value (@[-1]) for first book
        try: nextBBB = NT_BBB_LIST[NT_BBB_LIST.index(BBB)+1]
        except IndexError: pass # above line fails on final book
        links_html = links_html.replace( '__PREVIOUS__', f'<a href="OET-RV-LV_{previousBBB}.html">Previous Book ({previousBBB})</a>{EM_SPACE}')
        links_html = links_html.replace( '__NEXT__', '' if BBB==NT_BBB_LIST[-1]
            else f'{EM_SPACE}<a href="OET-RV-LV_{nextBBB}.html">Next Book ({nextBBB})</a>')
    else: unexpected_BBB, BBB

    C = None
    done_intro = False
    book_html = ''
    for usfm_line in rvUSFM.split( '\n' ):
        if not usfm_line: continue # Ignore blank lines
        assert usfm_line.startswith( '\\' )
        usfm_line = usfm_line[1:] # Remove the leading backslash
        try: marker, rest = usfm_line.split( ' ', 1 )
        except ValueError: marker, rest = usfm_line, ''
        # print( f"{marker=} {rest=}")
        if marker in ('id','usfm','ide','h','toc2','toc3'):
            continue # We don't need to map those markers to HTML
        if marker in ('rem',):
            book_html = f'{book_html}<p class="{marker}">{rest}</p>\n'
        elif marker in ('mt1','mt2'):
            if not done_intro: # Add an extra explanatory paragraph at the top
                book_html = f'{book_html}{DISCLAIMER_HTML}{SBS_BOOK_INTRO_HTML1}'
                done_intro = True
            book_html = f'{book_html}<p class="{marker}">{rest}</p>\n'
        elif marker == 'toc1':
            start_html = START_HTML.replace( '__TITLE__', rest )
        elif marker == 'c':
            C = rest
            if C:
                if C != C.strip():
                    logging.warning( f"{BBB} C='{C}' needs cleaning")
                    C = C.strip()
                assert C.isdigit()
            if C == '1': # Add an inspirational note
                book_html = f'{book_html}{INTRO_PRAYER_HTML}\n'

    # Get the guts of the chapter/verse HTML x2
    ourRVStartMarkerIndex = rvHTML.index( '<div class="BibleText">' )
    ourRVEndMarkerIndex = rvHTML.rindex( '<p><a href="#C1">C1</a>' ) # This follows </div>
    rvMidHHTML = rvHTML[ourRVStartMarkerIndex:ourRVEndMarkerIndex]

    ourLVStartMarkerIndex = lvHTML.index( '<div class="BibleText">' )
    ourLVEndMarkerIndex = lvHTML.rindex( '<p><a href="#C1">C1</a>' ) # This follows </div>
    lvMidHHTML = lvHTML[ourLVStartMarkerIndex:ourLVEndMarkerIndex]

    # Now break the RV up by section
    rvHTMLExpandedSections = []
    for n, rvSectionHTML in enumerate( rvMidHHTML.split( '<div class="rightBox">' ) ):
        try:
            CclassIndex1 = rvSectionHTML.index( 'id="C' )
            CclassIndex2 = rvSectionHTML.index( '"', CclassIndex1+4 )
            startCV = rvSectionHTML[CclassIndex1+4:CclassIndex2]
            # if 'V' not in startCV: startCV = f'{startCV}V1'
            CclassIndex8 = rvSectionHTML.rindex( 'id="C' )
            CclassIndex9 = rvSectionHTML.index( '"', CclassIndex8+4 )
            endCV = rvSectionHTML[CclassIndex8+4:CclassIndex9]
            print( f"\n  {BBB} {n:,}: {startCV=} {endCV=}")
        except ValueError:
            print( f"  {n:,}: No Cid in {rvSectionHTML=}" )
            startCV, endCV = '', 'C1'
        rvHTMLExpandedSections.append( (startCV, endCV, rvSectionHTML) )

    # Now we need to break the LV into the same number of sections
    lvHTMLSections = []
    lastLVindex = 0
    for n, (startCV, endCV, rvSectionHTML) in enumerate( rvHTMLExpandedSections ):
        nextStartCV = rvHTMLExpandedSections[n+1][0] if n < len(rvHTMLExpandedSections)-1 else 'DONE'
        print( f"\n{BBB} {n}: {lastLVindex=} lvSectionHTML start='{lvMidHHTML[lastLVindex:lastLVindex+2000]}'\n" )
        lvSectionHTML = lvMidHHTML[lastLVindex:]
        if not startCV:
            assert n == 0
            assert lastLVindex == 0
            lastLVindex = lvSectionHTML.index( '<p class="BText" id="C1">' )
            lvHTMLSections.append( lvMidHHTML[:lastLVindex] )
        elif startCV == 'C1': # First CV section
            LVindex1 = lvSectionHTML.index( f'<p class="BText" id="C1">' )
            lvHTMLSections.append( lvMidHHTML[lastLVindex:LVindex1] )
            lastLVindex += LVindex1
            # print( f"{n}: {startCV=} '{lvSectionHTML[:LVindex1]}' then '{lvSectionHTML[LVindex1:LVindex1+60]}...'" )
            # halt
        elif n < len(rvHTMLExpandedSections)-1:
            assert n > 1
            LVindex1 = lvSectionHTML.index( f' id="{startCV}"' )
            print( f"{BBB} {n}: {startCV=} '{lvSectionHTML[:LVindex1]}' then '{lvSectionHTML[LVindex1:LVindex1+60]}...'" )
            halt
        else:
            assert n == len(rvHTMLExpandedSections)-1
            assert nextStartCV == 'DONE'
            halt

    print( f"  Got {len(rvHTMLExpandedSections)} RV section(s) and {len(lvHTMLSections)} LV section(s)")
    assert len(lvHTMLSections) == len(rvHTMLExpandedSections), f"{len(lvHTMLSections)} != {len(rvHTMLExpandedSections)}"
    if lastLVindex < len(lvMidHHTML) - 1:
        print( f"  Need to append last LV bit {len(lvMidHHTML)-lastLVindex} '{lvMidHHTML[lastLVindex:lastLVindex+40]}'")
        lvHTMLSections[-1] = f'{lvHTMLSections[-1]}{lvMidHHTML[lastLVindex:]}'

    # Now we need to remove the CV id (duplicate) fields from the LV
    Cregex, CVregex = ' id="C\d{1,3}"', ' id="C\d{1,3}V\d{1,3}"'
    lvMidHHTML = re.sub( CVregex, '', lvMidHHTML)
    lvMidHHTML = re.sub( Cregex, '', lvMidHHTML)

    book_html = f'{book_html}<div class="container">\n' \
                f'<div><h2>Readers’ Version</h2>{rvMidHHTML}</div>\n' \
                f'<div><h2>Literal Version</h2>{lvMidHHTML}</div>\n' \
                '</div>'

    chapter_links = [f'<a href="#C{chapter_num}">C{chapter_num}</a>' for chapter_num in range( 1, int(C)+1 )]
    chapter_html = f'<p>{EM_SPACE.join(chapter_links)}</p>'
    book_start_html = f'{start_html}{links_html}\n{chapter_html}'

    return ( book_start_html,
             book_html,
             f'{chapter_html}\n{links_html}\n{END_HTML}' )
# end of pack_HTML_side-by-side.pack_HTML_files()


if __name__ == '__main__':
    # Configure basic Bible Organisational System (BOS) set-up
    parser = BibleOrgSysGlobals.setup( PROGRAM_NAME, PROGRAM_VERSION )
    BibleOrgSysGlobals.addStandardOptionsAndProcess( parser, exportAvailable=False )

    main()

    BibleOrgSysGlobals.closedown( PROGRAM_NAME, PROGRAM_VERSION )
# end of pack_HTML_side-by-side.py
