#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# convert_OET-LV_to_simple_HTML.py
#
# Script to take the OET-LV NT ESFM files and convert to HTML
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
CHANGELOG:
    2023-08-07 Move MRK before MAT
    2023-08-16 Handle gloss pre/helper/post markings from updated wordtables
    2023-08-21 Add lemma pages
    2023-08-30 Add nomina sacra to word pages
"""
from gettext import gettext as _
from typing import List, Tuple, Set, Optional
from pathlib import Path
from datetime import datetime
import logging
import os
import re
from collections import defaultdict
import json

if __name__ == '__main__':
    import sys
    sys.path.insert( 0, '../../BibleOrgSys/' )
from BibleOrgSys import BibleOrgSysGlobals
from BibleOrgSys.BibleOrgSysGlobals import vPrint, fnPrint, dPrint
from BibleOrgSys.Bible import Bible
from BibleOrgSys.Reference.BibleBooksCodes import BOOKLIST_OT39, BOOKLIST_NT27
from BibleOrgSys.Reference.BibleOrganisationalSystems import BibleOrganisationalSystem
from BibleOrgSys.Misc import CompareBibles
import sys
sys.path.append( '../../BibleTransliterations/Python/' )
from BibleTransliterations import load_transliteration_table, transliterate_Greek


LAST_MODIFIED_DATE = '2023-08-30' # by RJH
SHORT_PROGRAM_NAME = "Convert_OET-LV_to_simple_HTML"
PROGRAM_NAME = "Convert OET-LV ESFM to simple HTML"
PROGRAM_VERSION = '0.74'
PROGRAM_NAME_VERSION = '{} v{}'.format( SHORT_PROGRAM_NAME, PROGRAM_VERSION )

DEBUGGING_THIS_MODULE = False


project_folderpath = Path(__file__).parent.parent # Find folders relative to this module
FG_folderpath = project_folderpath.parent # Path to find parallel Freely-Given.org repos
OET_OT_USFM_InputFolderPath = project_folderpath.joinpath( 'intermediateTexts/auto_edited_OT_USFM/' )
OET_NT_ESFM_InputFolderPath = project_folderpath.joinpath( 'intermediateTexts/auto_edited_VLT_ESFM/' )
# OET_USFM_OutputFolderPath = project_folderpath.joinpath( 'translatedTexts/LiteralVersion/' )
OET_HTML_OutputFolderPath = project_folderpath.joinpath( 'derivedTexts/simpleHTML/LiteralVersion/' )
THEOGRAPHIC_INPUT_FOLDER_PATH = FG_folderpath.joinpath( 'Bible_speaker_identification/outsideSources/TheographicBibleData/derivedFiles/' )
assert OET_OT_USFM_InputFolderPath.is_dir()
assert OET_NT_ESFM_InputFolderPath.is_dir()
# assert OET_USFM_OutputFolderPath.is_dir()
assert OET_HTML_OutputFolderPath.is_dir()
assert THEOGRAPHIC_INPUT_FOLDER_PATH.is_dir()

NEWLINE = '\n'
# EN_SPACE = ' '
EM_SPACE = ' '
NARROW_NON_BREAK_SPACE = ' '
CNTR_BOOK_ID_MAP = {
    'MAT':40, 'MRK':41, 'LUK':42, 'JHN':43, 'ACT':44,
    'ROM':45, 'CO1':46, 'CO2':47, 'GAL':48, 'EPH':49, 'PHP':50, 'COL':51, 'TH1':52, 'TH2':53, 'TI1':54, 'TI2':55, 'TIT':56, 'PHM':57,
    'HEB':58, 'JAM':58, 'PE1':60, 'PE2':61, 'JN1':62, 'JN2':63, 'JN3':64, 'JDE':65, 'REV':66}
NT_BBB_LIST = ['JHN','MRK','MAT','LUK','ACT','ROM','CO1','CO2','GAL','EPH','PHP','COL','TH1','TH2','TI1','TI2','TIT','PHM','HEB','JAM','PE1','PE2','JN1','JN2','JN3','JDE','REV']
assert len(NT_BBB_LIST) == 27
BBB_LIST = BOOKLIST_OT39 + NT_BBB_LIST
assert len(BBB_LIST) == 66
TORAH_BOOKS_CODES = ['GEN','EXO','LEV','NUM','DEU']
assert len(TORAH_BOOKS_CODES) == 5
CNTR_ROLE_NAME_DICT = {'N':'noun', 'S':'substantive adjective', 'A':'adjective', 'E':'determiner', 'R':'pronoun',
                  'V':'verb', 'I':'interjection', 'P':'preposition', 'D':'adverb', 'C':'conjunction', 'T':'particle'}
CNTR_MOOD_NAME_DICT = {'I':'indicative', 'M':'imperative', 'S':'subjunctive',
            'O':'optative', 'N':'infinitive', 'P':'participle', 'e':'e'}
CNTR_TENSE_NAME_DICT = {'P':'present', 'I':'imperfect', 'F':'future', 'A':'aorist', 'E':'perfect', 'L':'pluperfect', 'U':'U', 'e':'e'}
CNTR_VOICE_NAME_DICT = {'A':'active', 'M':'middle', 'P':'passive', 'p':'p', 'm':'m', 'a':'a'}
CNTR_PERSON_NAME_DICT = {'1':'1st', '2':'2nd', '3':'3rd', 'g':'g'}
CNTR_CASE_NAME_DICT = {'N':'nominative', 'G':'genitive', 'D':'dative', 'A':'accusative', 'V':'vocative', 'g':'g', 'n':'n', 'a':'a', 'd':'d', 'v':'v', 'U':'U'}
CNTR_GENDER_NAME_DICT = {'M':'masculine', 'F':'feminine', 'N':'neuter', 'm':'m', 'f':'f', 'n':'n'}
CNTR_NUMBER_NAME_DICT = {'S':'singular', 'P':'plural', 's':'s', 'p':'p'}


def main():
    """
    Main program to handle command line parameters and then run what they want.
    """
    BibleOrgSysGlobals.introduceProgram( __name__, PROGRAM_NAME_VERSION, LAST_MODIFIED_DATE )

    global genericBookList
    genericBibleOrganisationalSystem = BibleOrganisationalSystem( 'GENERIC-KJV-ENG' )
    genericBookList = genericBibleOrganisationalSystem.getBookList()

    # Convert files to simple HTML
    produce_HTML_files()
# end of convert_OET-LV_to_simple_HTML.main


# If you change any colours, etc., also need to adjust the Key below
BOOK_CSS_TEXT = """a { color:inherit; text-decoration:none; }

div.BibleText { }

span.upLink { font-size:1.5em; font-weight:bold; }
span.c { font-size:1.1em; color:green; }
span.cPsa { font-size:1.6em; font-weight:bold; color:green; }
span.v { vertical-align:super; font-size:0.5em; color:red; }
span.addArticle { color:grey; }
span.unusedArticle { color:lavender; }
span.addCopula { color:grey; }
span.addDirectObject { color:brown; }
span.addExtra { color:lightGreen; }
span.addOwner { color:darkOrchid; }
span.add { color:bisque; }
span.ul { color:darkGrey; }
span.dom { color:Gainsboro; }
span.schwa { font-size:0.75em; }
span.nominaSacra { font-weight:bold; }
span.nd { font-weight:bold; }
span.untr { font-size:0.8em; color:grey; text-decoration:line-through; }

p.rem { font-size:0.8em; color:grey; }
p.shortPrayer { text-align:center; }
p.mt1 { font-size:1.8em; }
p.mt2 { font-size:1.3em; }
p.LVsentence { margin-top:0.2em; margin-bottom:0.2em; }
"""

DATA_CSS_TEXT = """a { text-decoration:none; }

div.unusedOLWord { color:darkGrey; }

p.wordLine { text-indent:2em; margin-top:0.2em; margin-bottom:0.2em; font-size:0.9em; }

span.glossPre { color:lightGreen; }
span.glossHelper { color:grey; }
span.glossPost { color:brown; }

span.ul { color:darkGrey; }
"""

LV_INDEX_INTRO_HTML = """<!DOCTYPE html>
<html lang="en-US">
<head>
  <title>OET Literal Version Development</title>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="keywords" content="Bible, translation, OET, literal, version">
  <link rel="stylesheet" type="text/css" href="BibleBook.css">
</head>
<body>
  <p><a href="../">Up</a></p>
  <h1>Now obsolete! See <a href="../SideBySide/">here</a> instead.</h1>
  <!--<h1>Open English Translation Literal Version (OET-LV) Development</h1>-->
  <h2>Very preliminary in-progress still-private test version</h2>
  <h3><b>OT</b> v0.00</h3>
  <p id="Index"><a href="GEN.html">Genesis</a> &nbsp;&nbsp;<a href="EXO.html">Exodus</a> &nbsp;&nbsp;<a href="LEV.html">Leviticus</a> &nbsp;&nbsp;<a href="NUM.html">Numbers</a> &nbsp;&nbsp;<a href="DEU.html">Deuteronomy</a><br>
    <a href="JOS.html">Y<span class="schwa">ə</span>hōshū'a/Joshua</a> &nbsp;&nbsp;<a href="JDG.html">Leaders/Judges</a> &nbsp;&nbsp;<a href="RUT.html">Rūt/Ruth</a><br>
    <a href="SA1.html">Sh<span class="schwa">ə</span>mū'ēl/Samuel 1</a> &nbsp;&nbsp;<a href="SA2.html">Sh<span class="schwa">ə</span>mū'ēl/Samuel 2</a> &nbsp;&nbsp;<a href="KI1.html">Kings 1</a> &nbsp;&nbsp;<a href="KI2.html">Kings 2</a> &nbsp;&nbsp;<a href="CH1.html">Accounts/Chronicles 1</a> &nbsp;&nbsp;<a href="CH2.html">Accounts/Chronicles 2</a><br>
    <a href="EZR.html">'Ez<span class="schwa">ə</span>rā'/Ezra</a> &nbsp;&nbsp;<a href="NEH.html">N<span class="schwa">ə</span>ḩem<span class="schwa">ə</span>yāh/Nehemiah</a> &nbsp;&nbsp;<a href="EST.html">'Eş<span class="schwa">ə</span>ttēr/Esther</a><br>
    <a href="JOB.html">'Yuōv/Job</a> &nbsp;&nbsp;<a href="PSA.html">Songs/Psalms</a> &nbsp;&nbsp;<a href="PRO.html">Sayings/Proverbs</a> &nbsp;&nbsp;<a href="ECC.html">Orator/Ecclesiastes</a> &nbsp;&nbsp;<a href="SNG.html">Song of /Solomon</a><br>
    <a href="ISA.html">Y<span class="schwa">ə</span>sha'<span class="schwa">ə</span>yāh/Isaiah</a> &nbsp;&nbsp;<a href="JER.html">Yir<span class="schwa">ə</span>m<span class="schwa">ə</span>yāh/Jeremiah</a> &nbsp;&nbsp;<a href="LAM.html">Wailings/Lamentations</a> &nbsp;&nbsp;<a href="EZE.html">Y<span class="schwa">ə</span>ḩez<span class="schwa">ə</span>qē'l/Ezekiel</a><br>
    <a href="DAN.html">Dāniyyē'l/Daniel</a> &nbsp;&nbsp;<a href="HOS.html">Hōshē'a/Hosea</a> &nbsp;&nbsp;<a href="JOL.html">Yō'ēl/Joel</a> &nbsp;&nbsp;<a href="AMO.html">'Āmōʦ/Amos</a><br>
    <a href="OBA.html">'Ovad<span class="schwa">ə</span>yāh/Obadiah</a> &nbsp;&nbsp;<a href="JNA.html">Yōnāh/Jonah</a> &nbsp;&nbsp;<a href="MIC.html">Mīkāh/Micah</a> &nbsp;&nbsp;<a href="NAH.html">Naḩūm/Nahum</a><br>
    <a href="HAB.html">Ḩavaqqūq/Habakkuk</a> &nbsp;&nbsp;<a href="ZEP.html">Ts<span class="schwa">ə</span>fan<span class="schwa">ə</span>yāh/Zephaniah</a> &nbsp;&nbsp;<a href="HAG.html">Ḩaggay/Haggai</a> &nbsp;&nbsp;<a href="ZEC.html">Z<span class="schwa">ə</span>kar<span class="schwa">ə</span>yāh/Zechariah</a> &nbsp;&nbsp;<a href="MAL.html">Mal<span class="schwa">ə</span>'ākī/Malachi</a></p>
  <p>Whole <a href="OET-LV-Torah.html">Torah/Pentateuch</a>
    (long and slower to load, but useful for easy searching of multiple books, etc.)</p>
  <h3><b>NT</b> v0.01</h3>
  <p>Note that the <em>OET</em> places Yōannēs/John and Markos/Mark before Matthaios/Matthew.</p>
  <p><a href="JHN.html">Yōannēs/John</a> &nbsp;&nbsp;<a href="MRK.html">Markos/Mark</a> &nbsp;&nbsp;<a href="MAT.html">Matthaios/Matthew</a> &nbsp;&nbsp;<a href="LUK.html">Loukas/Luke</a> &nbsp;&nbsp;<a href="ACT.html">Acts</a><br>
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
  <p>Whole <a href="OET-LV-NT.html">New Testament</a>
    (long and slower to load, but useful for easy searching of multiple books, etc.)</p>
  <h2 id="Intro">Literal Version Introduction</h2>
  <h3>The Open English Translation of the Bible (OET)</h3>
      <p>This <em>Literal Version</em> (OET-LV) forms just one-half of the new, forthcoming <em>Open English Translation</em> of the Bible (OET).
        The other half is the <em>Readers' Version</em> (OET-RV) which work will resume on in 2023.
        These two versions, side-by-side, together make up the OET.</p>
      <p>So why two versions? Well, many people ask the question:
        <i>Which English Bible translation should I use?</i>
        And often the answer is that there's no single Bible translation which can meet
        all of the needs of the thoughtful reader.
        Why not? It's because we often have two related desires that we need answered:</p>
      <ol><li>What does the original (Hebrew or Greek) text actually say? and</li>
        <li>What did the original writer mean? (i.e., What should we understand from it?)</li></ol>
      <p>Our answer has always been that it's best to use <b>two</b> translations—one more <b>literal</b>
        to give a window into the actual Hebrew or Greek words, and one more <b>dynamic</b>
        that's easier for us modern readers to understand—as much to do with our
        totally different cultures as to do with our different languages.</p>
      <p>So the <em>OET</em> gives both side-by-side, and with the advantage that
        both this <em>Literal Version</em> and the <em>Readers' Version</em>
        <b>have been specifically designed to be used together</b> in this way.
        We suggest reading the <em>Readers' Version</em>, and if something stands out and you think in your mind
        “<i>Does it really say that?</i>” or “<i>Could it really mean that?</i>”,
        then flick your eyes to this <em>Literal Version</em> and see for yourself what's really there in the original texts.</p>
      <p>On the other hand if you've been reading the Bible for a few decades already,
        maybe it would be fun to work through this <em>Literal Version</em> to get fresh insight
        into what's actually written there in those original languages.
        It won't be easy reading,
        but it should be insightful as the different wording will require more concentration.</p>
  <h3 id="Goals">Goals</h3>
    <p>Put simply, the goal of the <em>Open English Translation</em> is simply to
        <b>make the Bible more accessible to this current generation</b>
        with the best of a free-and-open easy-to-understand <em>Readers' Version</em>
        alongside a faithful <em>Literal Version</em> so that you yourself can checkout what was said and what is interpreted.</p>
    <p id="LearningGoal">A secondary goal is to expose more people to some of the background of where our Bibles come from
        and how translators make decisions,
        i.e., <b>to teach</b> a little more about original manuscripts
        and to challenge a little more about translation traditions that can possibly be improved.</p>
  <h3 id="Distinctives">Distinctives</h3>
    <p>The OET has the following distinguishing points:</p>
    <ul><li>An easy-to-understand <em>Readers' Version</em> alongside a very <em>Literal Version</em></li>
    <li>A generous open license so that the <em>Open English Translation</em> can be
        freely used in any Bible app or website, or printed in your church Bible-study notes
        without even needing to request permission.</li>
    <li>This <em>Literal Version</em> has the minimum number of interpreted extras,
        so we've added basic sentence punctuation (mostly just commas and periods/fullstops).
        The New Testament has no exclamation marks, no paragraphs,
        no speech marks (even the King James Bible didn't have these), and no section headings.
        A limited number of footnotes relate mostly to the text of the source manuscripts
        that the <em>OET-LV</em> is translated from.</li>
    <li>This <em>Literal Version</em> retains the original units for all measurements
        (useful for historical and symbolic studies),
        whereas the <em>Readers' Version</em> converts them to modern units (easier to understand and visualise).</li>
    <li>This <em>Literal Version</em> retains the original figurative language
        (even if it's not a figure of speech that we are familiar with),
        whereas the <em>Readers' Version</em> converts some figures of speech to modern equivalents
        (easier to understand).</li>
    <li>Being a 21<span style="vertical-align:super;font-size:0.8em;">st</span> century translation done in an era
        when there is much more effort in general to respect speakers of other languages
        (including the languages of ethnic minorities in our own countries)
        and to pronounce their names and placenames correctly,
        the <em>OET</em> attempts to do the same for Biblical names and placenames.
        (All this is a little complex when we have both Hebrew and Greek versions of names and placenames—more below.)
        Certainly by showing a little more respect for Hebrew names,
            we hope to make this Bible translation a little more “Jew-friendly”.
        If you have difficulty following the names in this <em>Literal Version</em>,
        you can always look across to the <em>Readers' Version</em>.
        (Most English readers looking at names in the Bible all the way from <i>Jericho</i> to <i>Jesus</i>
        would have no idea that there's no <b>J</b> letter or sound in either Hebrew or Greek,
        plus there's absolutely no such name as <i>James</i> in the New Testament manuscripts—it's
        a historical accident carried through from an inconsistency by John Wycliffe—see
        <a href="https://www.biblicalarchaeology.org/daily/biblical-topics/bible-versions-and-translations/james-or-jacob-in-the-bible/">this article</a>
        for example.</li>
    <li>In addition to wanting to get names and placenames more accurate,
        we've also attempted to modernise and simplify the spelling (transliterations) of these names
        to make it easier for readers to pronounce them as they come across them,
        e.g., using <b>f</b> instead of <b>ph</b>, so <i>Epafras</i> instead of <i>Epaphras</i>.
        (Oddly, even traditional English Bible translations surprisingly
        do use <i>Felix</i> and <i>Festus</i>.)</li>
    <li>With regular words, we've tried to do the opposite,
        i.e., to use less Greek rather than more wherever possible.
        So a word like <i>baptise</i> (which is an adapted transliteration of the Greek verb),
        actually gets translated, so this example becomes <i>immerse</i>.</li>
    <li><i>Italics</i> are only used for <em>emphasis</em>, not to indicate <i>added words</i> as historically done in
        older translations due to limitations of the original printing processes.
        The <em>OET</em> fixes the problem where most modern books use <i>italics</i> for <em>emphasis</em>
        whereas older Bibles use <i>italics</i> for the words which should actually be <b>deemphasised</b>,
        i.e., the words which actually <b>aren't</b> in the original manuscripts!</li>
    <li>The English <i>Christ</i> is an adapted transliteration of the Koine Greek word <i>Kristos</i>
            used for the original Hebrew <i>Messiah</i>.
        (It's not Jesus' surname!)
        It seems to make sense to only use one word consistently
            rather than using two words for the same thing
            (just because they came from two different languages),
            so the <em>OET</em> has elected to only use <i>messiah</i>.
        However, these words actually have a meaning, just as <i>President</i> is not just a title,
            but someone who <i>presides</i> over governmental meetings.
        So going a step further, we have chosen to use the contemporary
            <b>meaning</b> of the word in this <em>Literal Version</em>.
        The original meaning is <i>one who is anointed</i> (by having a hornful of oil poured over them),
            but we use the extended meaning which is <i>one who is selected/chosen (by God)</i>.</li>
    <li>Most readers living in modern democracies
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
    <li>This <em>Literal Version</em> tries to add as little as possible
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
    <li>Most dialects of modern English don't distinguish between <i>you (singular)</i> referring to just one person,
        and <i>you (plural)</i> referring to a group of people.
        However, the original languages clearly distinguish these,
        so in order to indicate this to our readers
        this <em>Literal Version</em> uses <i>you<span class="ul">_</span>all</i> for the plural form
        (although we are aware that some modern dialects now prefer <i>yous</i>).</li>
    <li>Because this <em>Literal Version</em> so closely follows the original languages,
            it's important to remember that words often don't match one-to-one between languages.
        This is one reason why the <em>LV</em> reads strangely:
            because the translators try to avoid using different English words if we can;
            knowing that the <em>LV</em> will not be natural English.
        Again, this is because we want the <em>LV</em> to be
            a window into what's actually written in the original languages.
        For fluent English (like in the <em>Readers' Version</em>) the same Greek word
            might require several different translations when used in different contexts.
        For example, the Greek word translated <i>raise</i> in the <em>LV</em>
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
            because his hearers didn't understand until right near the end that he was going to be executed so coming back to life wasn't on their minds.
        So we, looking back in history, know that he was talking about coming back to life,
            but at the time, they were just very confused and didn't understand what he meant.
        But amazingly, as well as referring to his resurrection, <i>raising</i> also refers to his crucifixion
            as the victims on the stakes were also <i>raised</i>. (See <a href="JHN.html#C3V14">John 3:14</a>.)
        Sadly, it's not usually possible to make a translation easy to read and understand in our current times,
            without losing some of the underlying meaning or ambiguities or word-plays that were presented to the original hearers.
        That's exactly why it's good to have <em>two</em> different translations side-by-side!</small></li>
    <li>These particular pages use British spelling,
        but American spelling will also be available in the future.</li>
    <li>Our preference in most editions is to place <em>The Gospel according to John</em>
            <b>before</b> <em>Matthew</em>.
        This has a couple of advantages:
        <ol><li>The Old Testament starts with “In the beginning, god created…”
            and the New Testament starts with “In the beginning was the message…”.</li>
        <li><em>Acts</em> ends up right after the first book by its author <em>Luke</em>.</li>
        <li>It just reminds readers that the order of the “books” in the Bible
            is not set by sacred degree--only by tradition.</li>
        </ol>
        <small>(Some do complain that the traditional order of the first four gospel accounts
            represent the lion, the calf, the man, and the eagle of Rev 4:6-7
            which allegedly match with the banners (not described in the Bible) of the four divisions
            of the tribes of Israel mentioned in Numbers 2.)</small></li>
    <li>Beware of some traps interpreting this <em>Literal Version</em>.
        Because it's not designed to be used alone (but rather alongside the <em>Readers' Version</em>),
        it's <b>much more literal</b> than most other “literal versions”.
        You'll quickly notice lighter colours that mark the deemphasis of words
        that had to be added to make the English sentences even make sense.
        But there's at least two other things that aren't necessarily changed
        in the English <em>Literal Version</em>:
        <ol>
            <li>Other languages use the negative differently,
                    especially when it's doubled or tripled in the sentence.
                If you don't understand this,
                you could easily think that the original means the opposite of what the words actually appear to say.
                For example the double negative: “You are not caring about no one.” (adapted from Matthew 22:16).
                In natural, fluent English, we would have to reverse the second negative to get the expected meaning,
                    ending up with <i>anyone</i> as you'll find in the <em>Readers' Version</em>.
                But in Greek, the second negative adds emphasis rather than reversing the first negative.
                So our <em>Literal Version</em> shows you the words that are actually there
                    (in the Greek in this case).</li>
            <li>Other languages may omit (or <i>elide</i>) words which are clearly implied to the original reader,
                but which the modern English reader finds strange,
                e.g., a son may be divided against his father, and a daughter her mother.
                The elided words are “may be divided against”.</li>
        </ul>
        Always check the <em>Readers' Version</em> carefully for how it is translated into modern, idiomatic English
        before jumping to any conclusions of your own about what the original language says or doesn't say.</li>
    </ul>
  <h3 id="Key">Key to symbols and colours in the OET-LV</h3>
    <p>You will notice that this <em>Literal Version</em> looks different from most Bibles that you're used to:</p>
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
    <li><span class="addArticle">Grey</span> words indicate added articles.
        English uses <em>a</em> or <em>the</em> to indicate whether a noun
        is indefinite or definite.
        Other languages don't necessarily work the same way.
        Neither Hebrew nor Greek have a word for English “<i>a</i>”.
        If we have to add an article to make the English sound correct, we indicate this by greying it,
        e.g., <em><span class="addArticle">the</span> man</em>.
        (We use lighter colours to deemphasise added words like these rather than using <i>italics</i> like most Bibles,
        because apart from Bibles, <i>italics</i> are mostly used these days for emphasis.)</li>
    <li><span class="addCopula">Light pink</span>: A copula is a word that links a subject and its complement (or description),
        e.g., the word <i><span class="addCopula">is</span></i> in the sentence <i>The house <span class="addCopula">is</span> white.</i>
        Other languages don't necessarily work the same way and can say things like
        <i>White the house.</i>
        Added copulas are marked with this <span class="addCopula">light colour</span>.</li>
    <li><span class="addDirectObject">Light brown</span>: Certain English verbs require a direct or indirect object.
        Think of the difference between <i>He said, blah, blah</i> and <i>He told, blah, blah</i>.
        The second one feels like it requires something like <i>He told <span class="addDirectObject">him</span>, blah, blah</i>.
        Added direct and indirect objects are marked with
        a <span class="addDirectObject">light colour</span>.</li>
    <li><span class="addExtra">Light green</span>:
        In other languages it may be possible to say something
        like <i>The having<span class="ul">_</span>fallen</i>….
        In English, we must say something like
        <i>The <span class="addExtra">one</span> having<span class="ul">_</span>fallen</i>…
        or <i>The <span class="addExtra">person</span> having fallen</i>….
        If the article and verb are marked as <b>plural</b> in the source language,
            we may be able to say
            <i>The <span class="addExtra">ones</span> having<span class="ul">_</span>fallen</i>….
        If the article is marked as feminine in the source language, we may be able to say
            <i>The <span class="addExtra">female one</span> having<span class="ul">_</span>fallen</i>….
            or <i>The <span class="addExtra">woman</span> having<span class="ul">_</span>fallen</i>….
        Added words like this are marked with this <span class="addExtra">light colour</span>.</li>
    <li><span class="addOwner">Light purple</span>: If we have an original construction like <i>God spoke by son</i> (from Heb 1:2),
        in English we need to add a word like <i>God spoke by <span class="addArticle">the</span> son</i> or <i>God spoke by <span class="addOwner">his</span> son</i>.
        In the latter case (where we don't just choose an article like <i><span class="addArticle">the</span></i>),
        we mark these added words with this <span class="addOwner">light colour</span>.</li>
    <li><span class="add">Light orange</span>: Other added words not in the above categories are marked with this <span class="add">light colour</span>.</li>
    <li>All of this colouring is to be completely open by helping the reader to be able to see where the translators have chosen to
        add words to the Hebrew or Greek in order to make the English sound slightly better,
        even though this has been kept to an absolute minimum in this <em>Literal Version</em>.</li>
    <li class="intro"><span class="nominaSacra">Bold text</span>: In the earliest copies of the original Koine Greek manuscripts,
        it appears that the scribes marked a small set of words that they considered
        to refer to <span class="nominaSacra">God</span>.
        (These markings are known as <a href="https://en.wikipedia.org/wiki/Nomina_sacra"><em>nomina sacra</em></a>
        or <em>sacred names</em>.)
        Other Bible translations do not indicate these special markings,
        however in this <em>Literal Version New Testament</em> we help the reader by making
        these marked words <span class="nominaSacra">stand out</span>.</li>
    <li>Where it is determined that a group of words was either definitely or most likely
        not in the original manuscripts (autographs),
        they are omitted in the <em>OET-LV</em> without any notes.
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
        but we'll do better than our traditional Bible translations.</p>
    <p>As a general rule, even if you started to think of the letter <i>J</i> in
        Bible names like the Germans or the Dutch (the two languages closest to English)
        pronounce <i>Ja</i> (as <i>Ya</i>),
        you'd already be taking a big step towards getting Biblical names more correct.
        (This deviation is not any kind of conspiracy—simply
        an unfortunate accident of history and continuous language change.)</p>
    <p>In the New Testament, the situation is already complicated by the fact that
        Old Testament (Hebrew) names have been written as Greek-speakers would think of them.
        So English <i>Jesus</i>
        (which you now realise should be pronounced more like <i>Yesus</i>
        as there's no <i>j</i> sound in either Hebrew or Greek)
        is actually more like <i>Yaysous</i> in Greek.
        But it's likely that his “parents” (using Hebrew or the related Aramaic/Syrian language at the time)
        actually named the child something more like <i>Y<span class="schwa">ə</span>hōshū'a</i>
        (from which we get <i>Joshua</i>).
        So which name should we call him in the text?
        Because the New Testament manuscripts are written in Koine Greek,
        we have chosen to give preference to the Greek forms of the names in the New Testament.
        However, the first time a name is used, we show both forms
        like <i>Yaʸsous/(Y<span class="schwa">ə</span>hōshū'a)</i>.
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
        even though it's pronounced very much like <i>ai</i>.</p>
    <p>We use the symbol ' to mark a <a href="https://en.wikipedia.org/wiki/Glottal_stop">glottal stop</a>
        which is the sound that some UK speakers put in the middle of the word <i>butter</i> (ba'a),
        so <i>Abra'am</i> (from the Greek) is three distinct syllables—those
        two <i>a</i>'s side-by-side should not be made into a long <i>ā</i>.</p>
  <h3 id="Learning">Learning</h3>
    <p>As mentioned in our <a href="#Goals">Goals above</a>, one of
        our main goals is to <a href="#LearningGoal">educate</a> our readers about how we get our Bibles.
        Here are some of the main points:</p>
    <ul><li>Biblical names are often very mangled in English translations.
            We've already covered this extensively <a href="#Names">above</a>.</li>
        <li>The <em>Open English Translation</em> makes it possible to learn how Bible translation is done.
            This is because reading this <em>Literal Version</em> gives you a good insight into
                what's actually written in the original manuscripts.
            Then you can read the same passage in the <em>Readers' Version</em>
                or your favourite other translation,
                and you'll get a good idea of the rearranging and interpreting that
                Bible translators have to do to get good, understandable translations
                in any modern language.</li>
        <li>Some editions of the OET have the “books” in different orders
                and in different combinations.
            Remember that different Bible originals were originally written on scrolls
                and weren't combined into a <a href="https://en.wikipedia.org/wiki/Codex">book form</a> similar to
                what we're accustomed to until many centuries later.
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
            Verses don't <i>say</i> anything, and
                we shouldn't be guilty of quoting short texts out of context.</li>
    </ul>
  <h3 id="Acknowledgements">Acknowledgements</h3>
    <p>A work like this could not be done with building on the work of so many that have gone before, including:</p>
    <ul><li>The creator God who communicates with us in various ways,
        but who specifically inspired the writing of the Scriptures
        and caused them to be preserved throughout the millenia
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
        For the (mostly) Hebrew Old Testament, we are especially reliant on the team work
        of <a href="https://hb.OpenScriptures.org/">Open Scriptures</a>, given to the world under a generous open licence.
        For the Greek New Testament, we are especially reliant on the Statistical Restoration work
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
        If you're reading this and notice problems or issues,
        please do contact us by <a href="mailto:Freely.Given.org@gmail.com?subject=OET-LV Feedback">email</a>.
        Also if there's something that we didn't explain in this introduction, or didn't explain very well.
        Thanks.</p>
  <p>HTML last updated: __LAST_UPDATED__</p>
</body></html>
"""

LV_FAQ_HTML = """<!DOCTYPE html>
<html lang="en-US">
<head>
  <title>OET Literal Version Development</title>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="keywords" content="Bible, translation, OET, literal, version, FAQ">
  <link rel="stylesheet" type="text/css" href="BibleBook.css">
</head>
<body>
  <p><a href="../">Up</a></p>
  <h1>Open English Translation Literal Version (OET-LV) Development</h1>
  <h2>Frequently Asked Questions (FAQs)</h2>

  <h3 id="bold">What are the bolded words in this <em>Literal Version</em>?</h3>
  <p>As explained in the <a href="index.html#Key">Key</a>, the bold text
        indicates the use of <em>Nomina Sacra</em> on the original manuscripts.
    These are special markings and abbreviations done by the scribes,
        and in the earliest manuscripts, highlight words that are assumed to relate to God.</p>

  <h3 id="uphill">Why does this <em>Literal Version</em> have uphill and downhill everywhere?</h3>
  <p>In our culture, when we go <i>up</i> somewhere, it usually means to go north.
    (Other cultures typically use ‘up’ and ‘down’ for ‘uphill’ and ‘downhill’,
        or ‘upstream’ and ‘downstream’, etc., depending on the common modes of travel.)
    The <em>LV</em> overtranslates <i>uphill</i> and <i>downhill</i>
        in order to help our readers avoid misunderstanding the cultural cues.</p>

  <h3 id="sectionHeadings">Why are there no section headings in this <em>Literal Version</em>?</h3>
  <p>Simply because the <em>Literal Version</em> strives to closely follow
        what's in the original manuscripts, and there's no section headings
        (or even paragraph breaks or even word breaks for that matter)
        in the oldest manuscripts.<br>
    Look in the <em>Readers' Version</em> if you want section headings
        to help find your way around.</p>

  <h3 id="Feedback">Feedback</h3>
    <p>These web pages are a very preliminary preview into a work still in progress.
        The <em>OET Literal Version</em> is not yet finished, and not yet publicly released,
        but we need to have it available online for easy access for our checkers and reviewers.
    If you're reading this and have questions that aren't discussed here,
        please do contact us by <a href="mailto:Freely.Given.org@gmail.com?subject=OET-LV FAQs">email</a>.
    Also if there's something that we didn't explain in this introduction, or didn't explain very well.
    Thanks.</p>
  <p>HTML last updated: __LAST_UPDATED__</p>
</body></html>
"""
LV_FAQ_HTML = LV_FAQ_HTML.replace( "'", "’" ) # Replace apostrophes
assert "'" not in LV_FAQ_HTML
assert '--' not in LV_FAQ_HTML

DISCLAIMER_HTML = """<p>Note: This is still a very early look into the unfinished text
of the <em>Open English Translation</em> of the Bible.
Please double-check the text in advance before using in public.</p>
"""


LV_BOOK_INTRO_HTML1 = """<p>Note: This <em>Literal Version</em> is a somewhat technical translation
designed to give the English reader a window into what's actually written in the original languages.
(See the <a href="index.html#Intro">introduction</a> for more details—we
recommend that you read the introduction first if you're wanting to read and understand this <em>Literal Version</em>.)
For nice, modern, readable English you should look at the (forthcoming) <em>Readers' Version</em>.
(Between the two versions, you should also be able to get an idea about how Bible Translation
actually <a href="index.html#Learning">works</a>.
You can also compare your other favourite Bible translations with this <em>Literal Version</em>
to get more insight into how they also interpreted the original texts in crafting their translation.)</p>
"""

INTRO_PRAYER_HTML = """<p class="shortPrayer">It is our prayer that this <em>Literal Version</em> of the
<em>Open English Translation</em> of the Bible will give you fresh insight into
the words of the inspired Biblical writers.</p><!--shortPrayer-->
"""

# NOTE: BibleBook.css is created from CSS_TEXT above
START_HTML = """<!DOCTYPE html>
<html lang="en-US">
<head>
  <title>__TITLE__</title>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="keywords" content="Bible, OET, literal, version">
  <link rel="stylesheet" type="text/css" href="BibleBook.css">
</head>
<body>
"""
END_HTML = '</body></html>\n'

illegalWordLinkRegex1 = re.compile( '[0-9]¦' ) # Has digits BEFORE the broken pipe
illegalWordLinkRegex2 = re.compile( '¦[1-9][0-9]{0,5}[a-z]' ) # Has letters immediately AFTER the wordlink number
chapterRegEx = re.compile(f'''<span class="c" id="C(\\d{1,3})V1">(\\d{1,3})</span>''')
psalmRegEx = re.compile(f'''<span class="cPsa" id="C(\\d{1,3})V1">(\\d{1,3})</span>''')

whole_Torah_html = whole_NT_html = ''
genericBookList = []
word_table_filenames = set()
def produce_HTML_files() -> None:
    """
    """
    global whole_Torah_html, whole_NT_html
    fnPrint( DEBUGGING_THIS_MODULE, "produce_HTML_files()" )

    numBooksProcessed = 0
    for BBB in genericBookList: # includes intro, etc.

        # Swap book orders to put JHN before MAT
        if   BBB == 'MAT': BBB = 'JHN'
        # elif BBB == 'MRK': BBB = 'MRK'
        elif BBB == 'LUK': BBB = 'MAT'
        elif BBB == 'JHN': BBB = 'LUK'

        bookType = None
        if BibleOrgSysGlobals.loadedBibleBooksCodes.isOldTestament_NR( BBB ):
            bookType = 'OT'
        elif BibleOrgSysGlobals.loadedBibleBooksCodes.isNewTestament_NR( BBB ):
            bookType = 'NT'

        word_table = None
        if bookType:
            sourceFolderPath = OET_NT_ESFM_InputFolderPath if bookType=='NT' else OET_OT_USFM_InputFolderPath
            source_filename = f'OET-LV_{BBB}.ESFM' if 'ESFM' in str(sourceFolderPath) else f'OET-LV_{BBB}.usfm'
            source_filepath = sourceFolderPath.joinpath( source_filename )
            dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"Reading {source_filepath}…" )
            with open( source_filepath, 'rt', encoding='utf-8' ) as esfm_input_file:
                esfm_text = esfm_input_file.read()
            assert not illegalWordLinkRegex1.search( esfm_text), f"illegalWordLinkRegex1 failed when loading {BBB}" # Don't want double-ups of wordlink numbers
            assert not illegalWordLinkRegex2.search( esfm_text), f"illegalWordLinkRegex2 failed when loading {BBB}" # Don't want double-ups of wordlink numbers
            if source_filename.endswith( '.ESFM' ):
                word_table_filename = 'OET-LV_NT_word_table.tsv'
                word_table_filenames.add( word_table_filename )
                if f'\\rem WORDTABLE {word_table_filename}\n' in esfm_text:
                    if word_table is None:
                        word_table_filepath = sourceFolderPath.joinpath( word_table_filename )
                        with open( word_table_filepath, 'rt', encoding='utf-8' ) as word_table_input_file:
                            word_table = word_table_input_file.read().rstrip( '\n' ).split( '\n' ) # Remove any blank line at the end then split
                        vPrint( 'Info', DEBUGGING_THIS_MODULE, f"  Read {len(word_table):,} lines from word table at {word_table_filepath}." )
                else: logging.critical( f"Expected {BBB} word-table '{word_table_filename}' {esfm_text[:500]}" ); halt
            assert esfm_text.count('‘') == esfm_text.count('’'), f"Why do we have OET-LV_{BBB}.usfm {esfm_text.count('‘')=} and {esfm_text.count('’')=}"
            assert esfm_text.count('“') >= esfm_text.count('”'), f"Why do we have OET-LV_{BBB}.usfm {esfm_text.count('“')=} and {esfm_text.count('”')=}"
            esfm_text = esfm_text.replace( "'", "’" ) # Replace apostrophes
            assert "'" not in esfm_text, f"""Why do we have single quote in {source_filename}: {esfm_text[esfm_text.index("'")-20:esfm_text.index("'")+22]}"""
            assert '"' not in esfm_text, f"""Why do we have double quote in {source_filename}: {esfm_text[esfm_text.index('"')-20:esfm_text.index('"')+22]}"""
            assert '  ' not in esfm_text, f"""Why do we have doubled spaces in {source_filename}: {esfm_text[esfm_text.index('  ')-20:esfm_text.index('  ')+22]}"""

            book_start_html, book_html, book_end_html = convert_ESFM_to_simple_HTML( BBB, esfm_text, word_table )

            output_filename = f'{BBB}.html'
            with open( OET_HTML_OutputFolderPath.joinpath(output_filename), 'wt', encoding='utf-8' ) as html_output_file:
                html_output_file.write( f'{book_start_html}\n{book_html}\n{book_end_html}' )

            # Having saved the book file, now for better orientation within the long file (wholeTorah or wholeNT),
            #   adjust book_html to include BBB text for chapters past chapter one
            bookAbbrev = BBB.title().replace('1','-1').replace('2','-2').replace('3','-3')
            thisRegEx = psalmRegEx if BBB=='PSA' else chapterRegEx
            while True:
                for match in thisRegEx.finditer( book_html ):
                    assert match.group(1) == match.group(2)
                    # print('A',BBB,match,match.group(1),book_html[match.start():match.end()])
                    if match.group(1) != '1': # We don't adjust chapter one
                        # print('B',BBB,match,match.group(1),book_html[match.start():match.end()])
                        insert_point = match.end() - len(match.group(2)) - 7 # len('</span>')
                        book_html = f'{book_html[:insert_point]}{bookAbbrev} {book_html[insert_point:]}'
                        break # redo the search
                else: break
            if BBB in TORAH_BOOKS_CODES:
                whole_Torah_html = f'{whole_Torah_html}{book_html}'
            elif bookType == 'NT':
                whole_NT_html = f'{whole_NT_html}{book_html}'

            numBooksProcessed += 1

    if word_table_filenames:
        make_word_pages( sourceFolderPath, OET_HTML_OutputFolderPath.joinpath( 'W/'), word_table_filenames )
        make_lemma_pages( sourceFolderPath, OET_HTML_OutputFolderPath.joinpath( 'Lm/'), word_table_filenames )
        make_person_pages( OET_HTML_OutputFolderPath.joinpath( 'Pe/') )
        make_location_pages( OET_HTML_OutputFolderPath.joinpath( 'Loc/') )


    # Output CSS and index and whole NT html
    with open( OET_HTML_OutputFolderPath.joinpath('BibleBook.css'), 'wt', encoding='utf-8' ) as css_output_file:
        css_output_file.write( BOOK_CSS_TEXT )
    with open( OET_HTML_OutputFolderPath.joinpath('BibleData.css'), 'wt', encoding='utf-8' ) as css_output_file:
        css_output_file.write( DATA_CSS_TEXT )
    indexIntroHTML = LV_INDEX_INTRO_HTML.replace('   ',' ').replace('  ', ' ').replace('\n ', '\n') \
            .replace( '__LAST_UPDATED__', f"{datetime.now().strftime('%Y-%m-%d')} <small>by {PROGRAM_NAME_VERSION}</small>" )
    with open( OET_HTML_OutputFolderPath.joinpath('index.html'), 'wt', encoding='utf-8' ) as html_index_file:
        html_index_file.write( indexIntroHTML )
    faqHTML = LV_FAQ_HTML.replace('   ',' ').replace('  ', ' ').replace('\n ', '\n') \
            .replace( '__LAST_UPDATED__', f"{datetime.now().strftime('%Y-%m-%d')} <small>by {PROGRAM_NAME_VERSION}</small>" )
    with open( OET_HTML_OutputFolderPath.joinpath('FAQs.html'), 'wt', encoding='utf-8' ) as html_FAQ_file:
        html_FAQ_file.write( faqHTML )

    # Save our long book conglomerates
    with open( OET_HTML_OutputFolderPath.joinpath('OET-LV-Torah.html'), 'wt', encoding='utf-8' ) as html_output_file:
        html_output_file.write( f'{START_HTML.replace("__TITLE__","OET-LV-Torah (Preliminary)")}\n'
                                f'<p><a href="index.html">OET-LV Index</a></p>\n{whole_Torah_html}\n'
                                f'<p><a href="index.html">OET-LV Index</a></p>\n{END_HTML}' )
    with open( OET_HTML_OutputFolderPath.joinpath('OET-LV-NT.html'), 'wt', encoding='utf-8' ) as html_output_file:
        html_output_file.write( f'{START_HTML.replace("__TITLE__","OET-LV-NT (Preliminary)")}\n'
                                f'<p><a href="index.html">OET-LV Index</a></p>\n{whole_NT_html}\n'
                                f'<p><a href="index.html">OET-LV Index</a></p>\n{END_HTML}' )

    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"Finished processing {numBooksProcessed} HTML books." )
# end of convert_OET-LV_to_simple_HTML.produce_HTML_files function


def convert_ESFM_to_simple_HTML( BBB:str, usfm_text:str, word_table:Optional[List[str]] ) -> Tuple[str, str, str]:
    """
    The OET-LV contains no internal headings or paragraphs formattting at all.
    Most of the conversion from the simple ESFM to HTML is done by simply replacing character markers with HTML spans.

    The exception is the word numbers which are handled by RegEx replacements in a separate function.
    """
    fnPrint( DEBUGGING_THIS_MODULE, f"convert_ESFM_to_simple_HTML( {BBB}, ({len(usfm_text)}), ({'None' if word_table is None else len(word_table)}) )" )

    links_html_template = '<p>__PREVIOUS__OET-LV <a href="index.html#Index">Book index</a>,' \
                 ' <a href="index.html#Intro">Intro</a>, <a href="index.html#Key">Key</a>,' \
                 'and <a href="FAQs.html">FAQs</a>' \
                 f'__NEXT__<br><br>__REST__</p>'
    if BBB in BOOKLIST_OT39:
        links_html = links_html_template.replace('__REST__', 'Whole <a href="OET-LV-Torah.html">Torah/Pentateuch</a> (for easy searching of multiple books, etc.)' )

        previousBBB = BOOKLIST_OT39[BOOKLIST_OT39.index(BBB)-1] # Gives wrong value (@[-1]) for first book
        try: nextBBB = BOOKLIST_OT39[BOOKLIST_OT39.index(BBB)+1]
        except IndexError: nextBBB = NT_BBB_LIST[0] # above line fails on final book
        links_html = links_html.replace( '__PREVIOUS__', '' if BBB==NT_BBB_LIST[0]
            else f'<a href="{previousBBB}.html">Previous Book ({previousBBB})</a>{EM_SPACE}')
        links_html = links_html.replace( '__NEXT__', f'{EM_SPACE}<a href="{nextBBB}.html">Next Book ({nextBBB})</a>')
    elif BBB in NT_BBB_LIST:
        links_html = links_html_template.replace('__REST__', 'Whole <a href="OET-LV-NT.html">New Testament</a> (for easy searching of multiple books, etc.)' )

        previousBBB = BOOKLIST_OT39[-1] if BBB==NT_BBB_LIST[0] else NT_BBB_LIST[NT_BBB_LIST.index(BBB)-1] # Gives wrong value (@[-1]) for first book
        try: nextBBB = NT_BBB_LIST[NT_BBB_LIST.index(BBB)+1]
        except IndexError: pass # above line fails on final book
        links_html = links_html.replace( '__PREVIOUS__', f'<a href="{previousBBB}.html">Previous Book ({previousBBB})</a>{EM_SPACE}')
        links_html = links_html.replace( '__NEXT__', '' if BBB==NT_BBB_LIST[-1]
            else f'{EM_SPACE}<a href="{nextBBB}.html">Next Book ({nextBBB})</a>')
    else: unexpected_BBB, BBB

    C = V = '0'
    book_html = ''
    done_intro = False
    for usfm_line in usfm_text.split( '\n' ):
        if not usfm_line: continue # Ignore blank lines
        assert usfm_line.startswith( '\\' )
        usfm_line = usfm_line[1:] # Remove the leading backslash
        try: marker, rest = usfm_line.split( ' ', 1 )
        except ValueError: marker, rest = usfm_line, ''
        # print( f"{marker=} {rest=}")
        if marker in ('id','usfm','ide','h','toc2','toc3'):
            continue # We don't need to map those markers to HTML
        if marker == 'rem':
            rest = rest.replace('\\em ','<em>').replace('\\em*','</em>')
            book_html = f'{book_html}<p class="{marker}">{rest}</p>\n'
        elif marker in ('mt1','mt2'):
            if not done_intro: # Add an extra explanatory paragraph at the top
                book_html = f'{book_html}{DISCLAIMER_HTML}{LV_BOOK_INTRO_HTML1}'
                done_intro = True
            book_html = f'{book_html}<p class="{marker}">{rest}</p>\n'
        elif marker == 'toc1':
            start_html = START_HTML.replace( '__TITLE__', rest )
        elif marker == 'c':
            V = '0'
            assert rest
            assert '¦' not in rest
            C = rest
            # if C=='2': halt
            assert C.isdigit()
            if C == '1': # Add an inspirational note
                book_html = f'{book_html}{INTRO_PRAYER_HTML}<div class="BibleText">\n'
            # Note: as well as CV id's, we make sure there are simple C id's there as well
            start_c_bit = '<p class="LVsentence" id="C1">' if C=='1' else f'<a class="upLink" href="#" id="C{C}">↑</a> '
            book_html = f'''{book_html}{start_c_bit}<span class="{'cPsa' if BBB=='PSA' else 'c'}" id="C{C}V1">{C}</span>{NARROW_NON_BREAK_SPACE}'''
        elif marker == 'v':
            assert rest
            try: V, rest = rest.split( ' ', 1 )
            except ValueError: V, rest = rest, ''
            assert V.isdigit(), f"Expected a verse number digit with '{V=}' '{rest=}'"
            # Put sentences on new lines
            rest = rest.replace( '?)', 'COMBO' ) \
                        .replace( '.', '.</p>\n<p class="LVsentence">' ) \
                        .replace( '?', '?</p>\n<p class="LVsentence">' ) \
                        .replace( 'COMBO', '?)' )
            # We don't display the verse number for verse 1 (after chapter number)
            book_html = f'{book_html}{"" if book_html.endswith(">") or book_html.endswith("—") else " "}{"" if V=="1" else f"""<span class="v" id="C{C}V{V}">{V}{NARROW_NON_BREAK_SPACE}</span>"""}{rest}'
        else:
            logging.critical( f"{BBB} {C}:{V} LV has unexpected USFM marker: \\{marker}='{rest}'" )
            book_html = f'{book_html}<p>GOT UNEXPECTED{marker}={rest}</p>'
    book_html = f"{book_html}</p></div><!--BibleText-->"

    chapter_links = [f'<a title="Go to chapter" href="#C{chapter_num}">C{chapter_num}</a>' for chapter_num in range( 1, int(C)+1 )]
    chapters_html = f'<p class="chapterLinks">{EM_SPACE.join(chapter_links)}</p><!--chapterLinks-->'
    book_start_html = f'{start_html}{links_html}\n{chapters_html}'

    # Add our various spans to special text features
    book_html = book_html.replace( '\\nd ', '<span class="nominaSacra">' ).replace( '\\nd*', '</span>' ) \
                .replace( '\\sup ', '<sup>' ).replace( '\\sup*', '</sup>' ) \
                .replace( '\\untr ', '<span class="untr">' ).replace( '\\untr*', '</span>' ) # untranslated words
    book_html = book_html.replace( '\\add +', '<span class="addArticle">' ) \
                .replace( '\\add -', '<span class="unusedArticle">' ) \
                .replace( '\\add =', '<span class="addCopula">' ) \
                .replace( '\\add ~', '<span class="addDirectObject">' ) \
                .replace( '\\add >', '<span class="addExtra">' ) \
                .replace( '\\add ^', '<span class="addOwner">' ) \
                .replace( '\\add ', '<span class="add">' ) \
                .replace( '\\add*', '</span>' )
    # Make underlines grey with "ul" spans (except when already at end of a span)
    book_html = book_html.replace( '_</span>', '%%SPAN%%' ) \
                .replace( '_', '<span class="ul">_</span>' ) \
                .replace( '%%SPAN%%', '_</span>' )

    if word_table: # sort out word numbers like 'written¦21763'
        book_html = convert_tagged_ESFM_words_to_links( BBB, book_html, word_table )

    # Append "untranslated" to titles/popup-boxes for untranslated words
    # count = 0
    searchStartIndex = 0
    for _safetyCount in range( 1000 ):
        ix = book_html.find( '<span class="untr"><a title="', searchStartIndex )
        if ix == -1: break # all done
        ixEnd = book_html.index( '"><', ix+29 )
        book_html = f'{book_html[:ixEnd]} (untranslated){book_html[ixEnd:]}'
        # count += 1
        searchStartIndex = ixEnd + 5
    else: need_to_increase_loop_count_for_untranslated_words

    # Make schwas smaller
    book_html = book_html.replace( 'ə', '<span class="schwa">ə</span>' )
    if BBB in BOOKLIST_OT39: # Hebrew direct object markers (DOMs)
        book_html = book_html.replace( 'DOM', '<span class="dom">DOM</span>' ) \
                        .replace( '[was]', '<span class="addCopula">was</span>' ) \
                        .replace( '[', '<span class="add">' ) \
                        .replace( ']', '</span>' )

    # All done
    return ( book_start_html,
             book_html,
             f'{chapters_html}\n{links_html}\n{END_HTML}' )
# end of convert_OET-LV_to_simple_HTML.produce_HTML_files function


# Regexs for a single word followed by a wordnumber,
#   or 2 or 3 words joined by an underline like he_was_saying
#   (although the underline is already inside a span at this point).
# Note that single words might include a <sup></sup> span as in 'Aʸsaias/(Yəshaˊə<sup>yāh</sup>)' (but we handle that below by substitions)
# NOTE: If you are making any changes, a similar regex is in the ESFM module of BibleOrgSys
#           except this one don't handle digits (like 'feeding 5,000') because that shouldn't occur in the LV
wordRegex1 = re.compile( '([-¬A-za-zḨŌⱤḩⱪşţʦĀĒāēīōūəʸʼˊ/()]+)¦([1-9][0-9]{0,5})' ) # Max of six total digits
wordRegex2 = re.compile( '([-¬A-za-zḨŌⱤḩⱪşţʦĀĒāēīōūəʸʼˊ/()]{2,})<span class="ul">_</span>([-¬A-za-zḨŌⱤḩⱪşţʦĀĒāēīōūəʸʼˊ/()]+)¦([1-9][0-9]{0,5})' )
wordRegex3 = re.compile( '([-¬A-za-zḨŌⱤḩⱪşţʦĀĒāēīōūəʸʼˊ/()]{2,})<span class="ul">_</span>([-¬A-za-zḨŌⱤḩⱪşţʦĀĒāēīōūəʸʼˊ/()]+)<span class="ul">_</span>([-¬A-za-zḨŌⱤḩⱪşţʦĀĒāēīōūəʸʼˊ/()]+)¦([1-9][0-9]{0,5})' )
def convert_tagged_ESFM_words_to_links( BBB:str, book_html:str, word_table:List[str] ) -> str:
    """
    Handle ESFM word numbers like 'written¦21763'
        which are handled by RegEx replacements.
    """
    fnPrint( DEBUGGING_THIS_MODULE, f"convert_tagged_ESFM_words_to_links( {BBB}, ({len(book_html)}), ({len(word_table)}) )" )

    vPrint( 'Info', DEBUGGING_THIS_MODULE, f"convert_tagged_ESFM_words_to_links( {BBB}, ({len(book_html)}), ({len(word_table)}) )…" )

    # First find "compound" words like 'stood_up' or 'upper_room' or 'came_in or 'brought_up'
    #   which have a wordlink number at the end,
    #   and put the wordlink number after each individual word
    count = 0
    searchStartIndex = 0
    while True: # Look for three-word compounds like 'with_one_accord' (Acts 1:14)
        match = wordRegex3.search( book_html, searchStartIndex )
        if not match:
            break
        logging.critical( f"Shouldn't still have three-word compound {BBB} word match 1='{match.group(1)}' 2='{match.group(2)}' 3='{match.group(3)}' 4='{match.group(4)}'  all='{book_html[match.start()-5:match.end()]}'" )
        assert match.group(4).isdigit()
        book_html = f'{book_html[:match.start()]}{match.group(1)}¦{match.group(4)}<span class="ul">_</span>{match.group(2)}¦{match.group(4)}<span class="ul">_</span>{match.group(3)}¦{match.group(4)}{book_html[match.end():]}'
        searchStartIndex = match.end() + 2 # We've added at least that many characters
        count += 1
    searchStartIndex = 0
    while True: # Look for two-word compounds
        match = wordRegex2.search( book_html, searchStartIndex )
        if not match:
            break
        logging.critical( f"Shouldn't still have two-word compound {BBB} word match 1='{match.group(1)}' 2='{match.group(2)}' 3='{match.group(3)}'  all='{book_html[match.start()-5:match.end()]}'" )
        assert match.group(3).isdigit()
        book_html = f'{book_html[:match.start()]}{match.group(1)}¦{match.group(3)}<span class="ul">_</span>{match.group(2)}¦{match.group(3)}{book_html[match.end():]}'
        searchStartIndex = match.end() + 2 # We've added at least that many characters
        count += 1
    if count > 0:
        vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"    Renumbered {count:,} OET-LV {BBB} 'compound' ESFM words." )

    # Make each linked word into a html link
    #   and then put a span around it so it can have a pop-up "title"
    searchStartIndex = 0
    count = 0
    # Note that single words might include a <sup></sup> span as in 'Aʸsaias/(Yəshaˊə<sup>yāh</sup>)'
    book_html = book_html.replace( '<sup>', 'SSsupP' ).replace( '</sup>', 'ESsupP' ) # We have to temporarily make these into normal word-formation chars
    while True:
        match = wordRegex1.search( book_html, searchStartIndex )
        if not match:
            break
        # print( f"{BBB} word match 1='{match.group(1)}' 2='{match.group(2)}' all='{book_html[match.start():match.end()]}'" )
        assert match.group(2).isdigit()
        row_number = int( match.group(2) )
        try: greek = word_table[row_number].split('\t')[1]
        except IndexError:
            logging.critical( f"convert_tagged_ESFM_words_to_links( {BBB} ) index error: word='{match.group(1)}' {row_number=}/{len(word_table)} entries")
            halt
        book_html = f'{book_html[:match.start()]}<a title="{greek}" href="W/{match.group(2)}.html">{match.group(1)}</a>{book_html[match.end():]}'
        searchStartIndex = match.end() + 25 # We've added at least that many characters
        count += 1
    book_html = book_html.replace( 'SSsupP', '<sup>' ).replace( 'ESsupP', '</sup>' ) # Restores our 'hidden' HTML markup
    vPrint( 'Info', DEBUGGING_THIS_MODULE, f"  Made {count:,} OET-LV {BBB} ESFM words into live links." )

    return book_html
# end of convert_OET-LV_to_simple_HTML.convert_tagged_ESFM_words_to_links function


formUsageDict, lemmaDict = defaultdict(list), defaultdict(list)
lemmaFormsDict, formGlossesDict, lemmaGlossesDict = defaultdict(set), defaultdict(set), defaultdict(set)
def make_word_pages( inputFolderPath:Path, outputFolderPath:Path, word_table_filenames:Set[str] ) -> int:
    """
    Make pages for all the words to link to.

    Then make person and location pages.

    There's almost identical code in createOETGreekWordsPages() in OpenBibleData createWordPages.py (sadly)
    """
    global formUsageDict, lemmaDict, lemmaFormsDict, formGlossesDict, lemmaGlossesDict

    fnPrint( DEBUGGING_THIS_MODULE, f"make_word_pages( {inputFolderPath}, {outputFolderPath}, {word_table_filenames} )" )
    load_transliteration_table( 'Greek' )
    our_start_html = START_HTML.replace( 'BibleBook.css', 'BibleData.css' )

    try: os.makedirs( outputFolderPath )
    except FileExistsError: pass # it was already there

    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"Making word table pages for {word_table_filenames}…" )
    for word_table_filename in word_table_filenames:
        word_table_filepath = inputFolderPath.joinpath( word_table_filename )
        with open( word_table_filepath, 'rt', encoding='utf-8' ) as word_table_input_file:
            word_table = word_table_input_file.read().rstrip( '\n' ).split( '\n' ) # Remove any blank line at the end then split
        vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  Read {len(word_table):,} lines from word table at {word_table_filepath}." )

        columnHeaders = word_table[0]
        dPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  Word table column headers = '{columnHeaders}'" )
        assert columnHeaders == 'Ref\tGreek\tLemma\tGlossWords\tGlossCaps\tProbability\tStrongsExt\tRole\tMorphology\tTags', columnHeaders # If not, probably need to fix some stuff

        # First make a list of each place the same Greek word (and matching morphology) is used
        # TODO: The word table has Matthew at the beginning (whereas the OET places John and Mark at the beginning) so we do JHN first
        vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  Finding all uses of {len(word_table)-1:,} words in {word_table_filename}…" )
        for n, columns_string in enumerate( word_table[1:], start=1 ):
            if columns_string.startswith( 'JHN' ):
                wordRef, greek, lemma, glossWords, glossCaps,probability, extendedStrongs, roleLetter, morphology, tagsStr = columns_string.split( '\t' )
                formattedGlossWords = glossWords \
                                        .replace( '/', '<span class="glossHelper">', 1 ).replace( '/', '</span>', 1 ) \
                                        .replace( '˱', '<span class="glossPre">', 1 ).replace( '˲', '</span>', 1 ) \
                                        .replace( '‹', '<span class="glossPost">', 1 ).replace( '›', '</span>', 1 )
                if probability:
                    formKey2Tuple = (greek, None if morphology=='None' else morphology)
                    formUsageDict[formKey2Tuple].append( n )
                    lemmaDict[lemma].append( n )
                    lemmaFormsDict[lemma].add( formKey2Tuple )
                    formGlossesDict[formKey2Tuple].add( formattedGlossWords )
                    lemmaGlossesDict[lemma].add( formattedGlossWords )
            elif formUsageDict: break # Must have already finished John
        for n, columns_string in enumerate( word_table[1:], start=1 ):
            if columns_string.startswith( 'MRK' ):
                wordRef, greek, lemma, glossWords, glossCaps,probability, extendedStrongs, roleLetter, morphology, tagsStr = columns_string.split( '\t' )
                formattedGlossWords = glossWords \
                                        .replace( '/', '<span class="glossHelper">', 1 ).replace( '/', '</span>', 1 ) \
                                        .replace( '˱', '<span class="glossPre">', 1 ).replace( '˲', '</span>', 1 ) \
                                        .replace( '‹', '<span class="glossPost">', 1 ).replace( '›', '</span>', 1 )
                if probability:
                    formKey2Tuple = (greek, None if morphology=='None' else morphology)
                    formUsageDict[formKey2Tuple].append( n )
                    lemmaDict[lemma].append( n )
                    lemmaFormsDict[lemma].add( formKey2Tuple )
                    formGlossesDict[formKey2Tuple].add( formattedGlossWords )
                    lemmaGlossesDict[lemma].add( formattedGlossWords )
            elif columns_string.startswith( 'LUK' ): break # Must have already finished Mark
        for n, columns_string in enumerate( word_table[1:], start=1 ):
            if not columns_string.startswith( 'JHN' ) and not columns_string.startswith( 'MRK' ):
                wordRef, greek, lemma, glossWords, glossCaps,probability, extendedStrongs, roleLetter, morphology, tagsStr = columns_string.split( '\t' )
                formattedGlossWords = glossWords \
                                        .replace( '/', '<span class="glossHelper">', 1 ).replace( '/', '</span>', 1 ) \
                                        .replace( '˱', '<span class="glossPre">', 1 ).replace( '˲', '</span>', 1 ) \
                                        .replace( '‹', '<span class="glossPost">', 1 ).replace( '›', '</span>', 1 )
                if probability:
                    formKey2Tuple = (greek, None if morphology=='None' else morphology)
                    formUsageDict[formKey2Tuple].append( n )
                    lemmaDict[lemma].append( n )
                    lemmaFormsDict[lemma].add( formKey2Tuple )
                    formGlossesDict[formKey2Tuple].add( formattedGlossWords )
                    lemmaGlossesDict[lemma].add( formattedGlossWords )

        # Now create the individual word pages
        vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f" Making pages for {len(word_table)-1:,} words in {word_table_filename}…" )
        for n, columns_string in enumerate( word_table[1:], start=1 ):
            # print( n, columns_string )
            output_filename = f'{n}.html'
            # dPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  Got '{columns_string}' for '{output_filename}'" )
            wordRef, greek, lemma, glossWords, glossCaps,probability, extendedStrongs, roleLetter, morphology, tagsStr = columns_string.split( '\t' )
            formattedGlossWords = glossWords \
                                    .replace( '/', '<span class="glossHelper">', 1 ).replace( '/', '</span>', 1 ) \
                                    .replace( '˱', '<span class="glossPre">', 1 ).replace( '˲', '</span>', 1 ) \
                                    .replace( '‹', '<span class="glossPost">', 1 ).replace( '›', '</span>', 1 )
            if extendedStrongs == 'None': extendedStrongs = None
            if roleLetter == 'None': roleLetter = None
            if morphology == 'None': morphology = None

            BBB, CVW = wordRef.split( '_', 1 )
            C, VW = CVW.split( ':', 1 )
            V, W = VW.split( 'w', 1 )
            tidyBBB = BibleOrgSysGlobals.loadedBibleBooksCodes.tidyBBB( BBB )

            strongs = extendedStrongs[:-1] if extendedStrongs else None # drop the last digit

            roleField = ''
            if roleLetter:
                roleName = CNTR_ROLE_NAME_DICT[roleLetter]
                if roleName=='noun' and 'U' in glossCaps: # What about G?
                    roleName = 'proper noun'
                roleField = f' Word role=<b>{roleName}</b>'

            nominaSacraField = 'Marked with <b>Nomina Sacra</b>' if 'N' in glossCaps else ''

            probabilityField = f'<small>(P={probability})</small> ' if probability else ''

            moodField = tenseField = voiceField = personField = caseField = genderField = numberField = ''
            if morphology:
                assert len(morphology) == 7, f"Got {wordRef} '{greek}' morphology ({len(morphology)}) = '{morphology}'"
                mood,tense,voice,person,case,gender,number = morphology
                if mood!='.': moodField = f' mood=<b>{CNTR_MOOD_NAME_DICT[mood]}</b>'
                if tense!='.': tenseField = f' tense=<b>{CNTR_TENSE_NAME_DICT[tense]}</b>'
                if voice!='.': voiceField = f' voice=<b>{CNTR_VOICE_NAME_DICT[voice]}</b>'
                if person!='.': personField = f' person=<b>{CNTR_PERSON_NAME_DICT[person]}</b>'
                if case!='.': caseField = f' case=<b>{CNTR_CASE_NAME_DICT[case]}</b>'
                if gender!='.': genderField = f' gender=<b>{CNTR_GENDER_NAME_DICT[gender]}</b>'
                if number!='.': numberField = f' number=<b>{CNTR_NUMBER_NAME_DICT[number]}</b>' # or № ???
            translation = '<small>(no English gloss)</small>' if glossWords=='-' else f'''Typical English gloss=‘<b>{formattedGlossWords.replace('_','<span class="ul">_</span>')}</b>’'''

            # Add pointers to people, locations, etc.
            semanticExtras = nominaSacraField
            if tagsStr:
                for semanticTag in tagsStr.split( ';' ):
                    prefix, tag = semanticTag[0], semanticTag[1:]
                    # print( f"{BBB} {C}:{V} '{semanticTag}' from {tagsStr=}" )
                    if prefix == 'P':
                        semanticExtras = f'''{semanticExtras}{' ' if semanticExtras else ''}Person=<a href="../Pe/P_{tag}.html">{tag}</a>'''
                    elif prefix == 'L':
                        semanticExtras = f'''{semanticExtras}{' ' if semanticExtras else ''}Location=<a href="../Loc/L_{tag}.html">{tag}</a>'''
                    elif prefix == 'Y':
                        year = tag
                        semanticExtras = f'''{semanticExtras}{' ' if semanticExtras else ''}Year={year}{' AD' if int(year)>0 else ''}'''
                    elif prefix == 'T':
                        semanticExtras = f'''{semanticExtras}{' ' if semanticExtras else ''}TimeSeries={tag}'''
                    elif prefix == 'E':
                        semanticExtras = f'''{semanticExtras}{' ' if semanticExtras else ''}Event={tag}'''
                    elif prefix == 'G':
                        semanticExtras = f'''{semanticExtras}{' ' if semanticExtras else ''}Group={tag}'''
                    elif prefix == 'F':
                        semanticExtras = f'''{semanticExtras}{' ' if semanticExtras else ''}Referred to from <a href="{tag}.html">Word #{tag}</a>'''
                    elif prefix == 'R':
                        semanticExtras = f'''{semanticExtras}{' ' if semanticExtras else ''}Refers to <a href="{tag}.html">Word #{tag}</a>'''
                    else:
                        logging.critical( f"Unknown '{prefix}' word tag in {n}: {columns_string}")
                        unknownTag
            lemmaLink = f'<a title="View Greek root word" href="../Lm/{lemma}.html">{lemma}</a>'
            lemmaGlossesList = sorted( lemmaGlossesDict[lemma] )
            wordGlossesList = sorted( formGlossesDict[(greek,morphology)] )

            prevLink = f'<b><a href="{n-1}.html">←</a></b> ' if n>1 else ''
            nextLink = f' <b><a href="{n+1}.html">→</a></b>' if n<len(word_table) else ''
            oetLink = f'<b><a href="../{BBB}.html#C{C}V{V}">Back to OET</a></b>'
            html = f'''{'' if probability else '<div class="unusedOLWord">'}<h1>OET Wordlink #{n}{'' if probability else ' <small>(Unused Greek word variant)</small>'}</h1>
<p>{prevLink}{oetLink}{nextLink}</p>
<p><a title="View Statistical Restoration Greek page" href="https://GreekCNTR.org/collation/?{CNTR_BOOK_ID_MAP[BBB]}{C.zfill(3)}{V.zfill(3)}">SR GNT {tidyBBB} {C}:{V}</a>
 {probabilityField}<b>{greek}</b> ({transliterate_Greek(greek)}) {translation}
 Strongs=<a title="View Strongs dictionary entry" href="https://BibleHub.com/greek/{strongs}.htm">{extendedStrongs}</a> <small>Lemma={lemmaLink}</small><br>
 {roleField} Morphology=<b>{morphology}</b>:{moodField}{tenseField}{voiceField}{personField}{caseField}{genderField}{numberField}{f'<br>  {semanticExtras}' if semanticExtras else ''}</p>{'' if probability else f'{NEWLINE}</div><!--unusedOLWord-->'}'''

            if probability: # Now list all the other places where this same Greek word is used
                other_count = 0
                thisWordNumberList = formUsageDict[(greek,morphology)]
                for oN in thisWordNumberList:
                    if oN==n: continue # don't duplicate the word we're making the page for
                    oWordRef, oGreek, oLemma, oGlossWords, oGlossCaps,oProbability, oExtendedStrongs, oRoleLetter, oMorphology, oTagsStr = word_table[oN].split( '\t' )
                    oFormattedGlossWords = oGlossWords \
                                            .replace( '/', '<span class="glossHelper">', 1 ).replace( '/', '</span>', 1 ) \
                                            .replace( '˱', '<span class="glossPre">', 1 ).replace( '˲', '</span>', 1 ) \
                                            .replace( '‹', '<span class="glossPost">', 1 ).replace( '›', '</span>', 1 )
                    oBBB, oCVW = oWordRef.split( '_', 1 )
                    oC, oVW = oCVW.split( ':', 1 )
                    oV, oW = oVW.split( 'w', 1 )
                    oTidyBBB = BibleOrgSysGlobals.loadedBibleBooksCodes.tidyBBB( oBBB )
                    if other_count == 0:
                        html = f'{html}\n<h2>Other uses ({len(thisWordNumberList)-1:,}) of {greek} <small>{morphology}</small> in the NT</h2>'
                    translation = '<small>(no English gloss)</small>' if oGlossWords=='-' else f'''English gloss=‘<b>{oFormattedGlossWords.replace('_','<span class="ul">_</span>')}</b>’'''
                    html = f'{html}\n<p class="wordLine"><a href="../{oBBB}.html#C{oC}V{oV}">OET {oTidyBBB} {oC}:{oV}</a> {translation} <a href="https://GreekCNTR.org/collation/?{CNTR_BOOK_ID_MAP[oBBB]}{oC.zfill(3)}{oV.zfill(3)}">SR GNT {oTidyBBB} {oC}:{oV} word {oW}</a>'
                    other_count += 1
                    if other_count >= 120:
                        html = f'{html}\n<p class="Note">({len(thisWordNumberList)-other_count-1:,} more examples not listed)</p>'
                        break
                if len(lemmaGlossesList) > len(wordGlossesList):
                    html = f'''{html}\n<p class="lemmaGlossesSummary">The various word forms of the root word (lemma) ‘{lemmaLink}’ have {len(lemmaGlossesList):,} different glosses: ‘<b>{"</b>’, ‘<b>".join(lemmaGlossesList)}</b>’.</p>'''

            # Now put it all together
            html = f"{our_start_html.replace('__TITLE__',greek)}\n{html}\n{END_HTML}"
            with open( outputFolderPath.joinpath(output_filename), 'wt', encoding='utf-8' ) as html_output_file:
                html_output_file.write( html )
            vPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"  Wrote {len(html):,} characters to {output_filename}" )

    return len(word_table) - 1
# end of convert_OET-LV_to_simple_HTML.make_word_pages function


def make_lemma_pages( inputFolderPath:Path, outputFolderPath:Path, word_table_filenames:Set[str] ) -> int:
    """
    """
    global lemmaDict, lemmaFormsDict, lemmaGlossesDict, formUsageDict

    fnPrint( DEBUGGING_THIS_MODULE, f"make_lemma_pages( {inputFolderPath}, {outputFolderPath}, {word_table_filenames} )" )
    our_start_html = START_HTML.replace( 'BibleBook.css', 'BibleData.css' )

    try: os.makedirs( outputFolderPath )
    except FileExistsError: pass # it was already there

    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"Making lemma table pages for {word_table_filenames}…" )
    for word_table_filename in word_table_filenames:
        word_table_filepath = inputFolderPath.joinpath( word_table_filename )
        with open( word_table_filepath, 'rt', encoding='utf-8' ) as word_table_input_file:
            word_table = word_table_input_file.read().rstrip( '\n' ).split( '\n' ) # Remove any blank line at the end then split
        vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  Read {len(word_table):,} lines from word table at {word_table_filepath}." )

        columnHeaders = word_table[0]
        dPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  Word table column headers = '{columnHeaders}'" )
        assert columnHeaders == 'Ref\tGreek\tLemma\tGlossWords\tGlossCaps\tProbability\tStrongsExt\tRole\tMorphology\tTags', columnHeaders # If not, probably need to fix some stuff


    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  Making {len(lemmaDict):,} lemma pages…" )

    lemmaList = sorted( [lemma for lemma in lemmaDict] )

    # Now make a page for each Greek lemma (including the variants not used in the translation)
    for ll, lemma in enumerate( lemmaList ):
        # print( ll, lemma )
        lemmaRowsList = lemmaDict[lemma]
        lemmaFormsList = sorted( lemmaFormsDict[lemma] )
        lemmaGlossesList = sorted( lemmaGlossesDict[lemma] )
        def getFirstWordNumber(grk,morph): return formUsageDict[(grk,morph)][0]

        output_filename = f'{lemma}.html'

        prevLink = f'<b><a title="Previous lemma" href="{lemmaList[ll-1]}.html">←</a></b> ' if ll>0 else ''
        nextLink = f' <b><a title="Next lemma" href="{lemmaList[ll+1]}.html">→</a></b>' if ll<len(lemmaList)-1 else ''
        html = f'''<h1 id="Top">Greek root word (lemma) ‘{lemma}’</h1>
<p class="pNav">{prevLink}<b>{lemma}</b>{nextLink}</p>
<p class="summary">This root form (lemma) is used in {len(lemmaFormsList):,} different forms in the NT: {', '.join([f'<a title="View Greek word form" href="../W/{getFirstWordNumber(grk,morph)}.html">{grk}</a> <small>({morph[4:] if morph.startswith("....") else morph})</small>' for grk,morph in lemmaFormsList])}.</p>
<p class="summary">It is glossed in {len(lemmaGlossesList):,}{'' if len(lemmaGlossesList)==1 else ' different'} way{'' if len(lemmaGlossesList)==1 else 's'}: ‘<b>{"</b>’, ‘<b>".join(lemmaGlossesList)}</b>’.</p>
'''

        if len(lemmaRowsList) > 100: # too many to list
            maxWordsToShow = 40
            html = f'{html}\n<h2>Showing the first {maxWordsToShow} out of ({len(lemmaRowsList)-1:,}) uses of Greek root word (lemma) ‘{lemma}’ in the NT</h2>'
        else: # we can list all uses of the word
            maxWordsToShow = 100
            html = f'''{html}\n<h2>Have {len(lemmaRowsList):,} {'use' if len(lemmaRowsList)==1 else 'uses'} of Greek root word (lemma) ‘{lemma}’ in the NT</h2>'''
        for displayCounter,oN in enumerate( lemmaRowsList, start=1 ):
            oWordRef, oGreek, oLemma, oGlossWords, oGlossCaps,oProbability, oExtendedStrongs, oRoleLetter, oMorphology, oTagsStr = word_table[oN].split( '\t' )
            oFormattedGlossWords = oGlossWords \
                                    .replace( '/', '<span class="glossHelper">', 1 ).replace( '/', '</span>', 1 ) \
                                    .replace( '˱', '<span class="glossPre">', 1 ).replace( '˲', '</span>', 1 ) \
                                    .replace( '‹', '<span class="glossPost">', 1 ).replace( '›', '</span>', 1 )
            oBBB, oCVW = oWordRef.split( '_', 1 )
            oC, oVW = oCVW.split( ':', 1 )
            oV, oW = oVW.split( 'w', 1 )
            oTidyBBB = BibleOrgSysGlobals.loadedBibleBooksCodes.tidyBBB( oBBB )
            oTidyMorphology = oMorphology[4:] if oMorphology.startswith('....') else oMorphology
            # if other_count == 0:
            translation = '<small>(no English gloss here)</small>' if oGlossWords=='-' else f'''English gloss=‘<b>{oFormattedGlossWords.replace('_','<span class="ul">_</span>')}</b>’'''
            html = f'''{html}\n<p class="lemmaLine"><a title="View OET {oTidyBBB} text" href="../OET/byC/{oBBB}_C{oC}.html#C{oC}V{oV}">OET {oTidyBBB} {oC}:{oV}</a> Greek word=<b><a title="Go to word page" href="../W/{oN}.html">{oGreek}</a></b> ({transliterate_Greek(oGreek)}) <small>Morphology={oTidyMorphology}</small> {translation} <a title="Go to Statistical Restoration Greek page" href="https://GreekCNTR.org/collation/?{CNTR_BOOK_ID_MAP[oBBB]}{oC.zfill(3)}{oV.zfill(3)}">SR GNT {oTidyBBB} {oC}:{oV} word {oW}</a></p>'''
            # other_count += 1
            # if other_count >= 120:
            #     html = f'{html}\n<p class="summary">({len(thisWordNumberList)-other_count-1:,} more examples not listed)</p>'
            #     break
            if displayCounter >= maxWordsToShow: break

        # Now put it all together
        html = f"{our_start_html.replace('__TITLE__',f'Greek lemma ‘{lemma}’')}\n{html}\n{END_HTML}"
        with open( outputFolderPath.joinpath(output_filename), 'wt', encoding='utf-8' ) as html_output_file:
            html_output_file.write( html )
        vPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"  Wrote {len(html):,} characters to {output_filename}" )
# end of createOETReferencePages.make_lemma_pages


def make_person_pages( outputFolderPath:Path ) -> int:
    """
    Make pages for all the words to link to.

    There's almost identical code in createOETGreekWordsPages() in OpenBibleData createWordPages.py (sadly)
    """
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"Making person pages…" )
    our_start_html = START_HTML.replace( 'BibleBook.css', 'BibleData.css' )

    try: os.makedirs( outputFolderPath )
    except FileExistsError: pass # it was already there

    with open( THEOGRAPHIC_INPUT_FOLDER_PATH.joinpath( 'normalised_People.json' ), 'rb' ) as people_file:
        peopleDict = json.load( people_file )
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Loaded {len(peopleDict):,} person entries." )

    # Firstly, make a list of all the keys
    peopleKeys = []
    for personKey in peopleDict:
        if personKey == '__HEADERS__': continue
        if personKey == '__COLUMN_HEADERS__': continue
        peopleKeys.append( personKey )

    # Now make a page for each person
    for n,(personKey,entry) in enumerate( peopleDict.items() ):
        if personKey == '__HEADERS__': continue
        if personKey == '__COLUMN_HEADERS__': continue

        previousLink = f'''<a title="Previous person" href="P_{peopleKeys[n-3][1:]}.html">←</a>''' if n>3 else ''
        nextLink = f'''<a title="Next person" href="P_{peopleKeys[n-1][1:]}.html">→</a>''' if n<len(peopleDict)-1 else ''

        personName = entry['displayTitle']
        bornStr = f"Born: {entry['birthYear']}" if entry['birthYear'] else ''
        diedStr = f"Died: {entry['deathYear']}" if entry['deathYear'] else ''

        bodyHtml = f'''<h1>OET person: {personName.replace( "'", '’' )}</h1>
<p class="personName">{livenMD(entry['dictText'])}</p>
<p class="personGender">{entry['gender']}{f' {bornStr}' if bornStr else ''}{f' {diedStr}' if diedStr else ''}</p>'''

        # Now put it all together
        output_filename = f"{personKey[0]}_{personKey[1:]}.html"
        html = f'''{our_start_html.replace('__TITLE__',personName)}
<p>{previousLink} {nextLink}</p>
{bodyHtml}
<p class="thanks"><small>Grateful thanks to <a href="https://Viz.Bible">Viz.Bible</a> for this data.</small></p>
{END_HTML}'''
        with open( outputFolderPath.joinpath(output_filename), 'wt', encoding='utf-8' ) as html_output_file:
            html_output_file.write( html )
        vPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"  Wrote {len(bodyHtml):,} characters to {output_filename}" )
# end of convert_OET-LV_to_simple_HTML.make_person_pages function


def make_location_pages( outputFolderPath:Path ) -> int:
    """
    Make pages for all the words to link to.

    There's almost identical code in createOETGreekWordsPages() in OpenBibleData createWordPages.py (sadly)
    """
    vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"Making location pages…" )
    our_start_html = START_HTML.replace( 'BibleBook.css', 'BibleData.css' )

    try: os.makedirs( outputFolderPath )
    except FileExistsError: pass # it was already there

    with open( THEOGRAPHIC_INPUT_FOLDER_PATH.joinpath( 'normalised_Places.json' ), 'rb' ) as locations_file:
        locationsDict = json.load( locations_file )
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"  Loaded {len(locationsDict):,} location entries." )

    # Firstly, make a list of all the keys
    placeKeys = []
    for placeKey in locationsDict:
        if placeKey == '__HEADERS__': continue
        if placeKey == '__COLUMN_HEADERS__': continue
        placeKeys.append( placeKey )

    # Now make a page for each location
    for n,(placeKey,entry) in enumerate( locationsDict.items() ):
        if placeKey == '__HEADERS__': continue
        if placeKey == '__COLUMN_HEADERS__': continue

        previousLink = f'''<a title="Previous location" href="L_{placeKeys[n-3][1:]}.html">←</a>''' if n>3 else ''
        nextLink = f'''<a title="Next location" href="L_{placeKeys[n-1][1:]}.html">→</a>''' if n<len(locationsDict)-1 else ''

        placeName = entry['displayTitle']
        commentStr = f" {entry['comment']}" if entry['comment'] else ''

        bodyHtml = f'''<h1>OET location: {placeName.replace( "'", '’' )}</h1>
<p class="locationName">{livenMD(entry['dictText'])}</p>
<p class="locationType">{entry['featureType']}{f"/{entry['featureSubType']}" if entry['featureSubType'] else ''}{f' {commentStr}' if commentStr else ''}</p>
<p class="locationVersions">KJB=‘{entry['kjvName']}’ ESV=‘{entry['esvName']}’</p>'''

        # Now put it all together
        output_filename = f"{placeKey[0]}_{placeKey[1:]}.html"
        html = f'''{our_start_html.replace('__TITLE__',placeName)}
<p>{previousLink} {nextLink}</p>
{bodyHtml}
<p class="thanks"><small>Grateful thanks to <a href="https://Viz.Bible">Viz.Bible</a> for this data.</small></p>
{END_HTML}'''
        with open( outputFolderPath.joinpath(output_filename), 'wt', encoding='utf-8' ) as html_output_file:
            html_output_file.write( html )
        vPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"  Wrote {len(html):,} characters to {output_filename}" )
# end of convert_OET-LV_to_simple_HTML.make_location_pages function


mdLinkRegex = re.compile( '\\[(.+?)\\]\\((.+?)\\)' )
def livenMD( mdText:str ) -> str:
    """
    Take markdown style links like '[Gen. 35:16](/gen#Gen.35.16)'
        and convert to HTML links.
    """
    fnPrint( DEBUGGING_THIS_MODULE, f"livenMD( {mdText[:140]}… )" )

    # Firstly, try to improve the overall formatting
    mdText = mdText.replace( '\n\n', '</p><p>' ).replace( '\n', '<br>' )
    mdText = mdText.replace( "'", '’' ) # Improve apostrophes

    # Now liven links
    count = 0
    searchStartIndex = 0
    while True: # Look for links that we could maybe liven
        match = mdLinkRegex.search( mdText, searchStartIndex )
        if not match:
            break
        dPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"  {match=} {match.groups()=}" )
        readableRef, mdLinkTarget = match.group(1), match.group(2)
        mdLinkTarget = mdLinkTarget.split( '#', 1 )[1]
        if mdLinkTarget.count( '.' ) == 2: # Then it's almost certainly an OSIS B/C/V ref
            OSISBkCode, C, V = mdLinkTarget.split( '.' )
            BBB = BibleOrgSysGlobals.loadedBibleBooksCodes.getBBBFromOSISAbbreviation( OSISBkCode )
            ourLinkTarget = f'../{BBB}.html#C{C}V{V}'
        else:
            assert mdLinkTarget.count( '.' ) == 1 # Then it's almost certainly an OSIS B/C ref
            OSISBkCode, C = mdLinkTarget.split( '.' )
            BBB = BibleOrgSysGlobals.loadedBibleBooksCodes.getBBBFromOSISAbbreviation( OSISBkCode )
            ourLinkTarget = f'../{BBB}.html#C{C}'
        ourLink = f'<a href="{ourLinkTarget}">{readableRef}</a>'
        mdText = f'''{mdText[:match.start()]}{ourLink}{mdText[match.end():]}'''
        searchStartIndex = match.end() + 10 # We've added at least that many characters
        count += 1
    return mdText
# end of convert_OET-LV_to_simple_HTML.livenMD function


if __name__ == '__main__':
    # Configure basic Bible Organisational System (BOS) set-up
    parser = BibleOrgSysGlobals.setup( PROGRAM_NAME, PROGRAM_VERSION )
    BibleOrgSysGlobals.addStandardOptionsAndProcess( parser, exportAvailable=False )

    main()

    BibleOrgSysGlobals.closedown( PROGRAM_NAME, PROGRAM_VERSION )
# end of convert_OET-LV_to_simple_HTML.py
