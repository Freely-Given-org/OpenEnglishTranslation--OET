#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# convert_OET-LV_to_simple_HTML.py
#
# Script to take the OET-LV NT USFM files and convert to HTML
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
Script to backport the ULT into empty verses of the OET-LV
    in order to give us the text of all the Bible,
    even if we haven't manually worked through it all carefully yet.

This script is designed to be able to be run over and over again,
    i.e., it should be able to update the OET-LV with more recent ULT edits.
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


LAST_MODIFIED_DATE = '2022-11-09' # by RJH
SHORT_PROGRAM_NAME = "Convert_OET-LV_to_simple_HTML"
PROGRAM_NAME = "Convert OET-LV USFM to simple HTML"
PROGRAM_VERSION = '0.38'
PROGRAM_NAME_VERSION = '{} v{}'.format( SHORT_PROGRAM_NAME, PROGRAM_VERSION )

DEBUGGING_THIS_MODULE = False


project_folderpath = Path(__file__).parent.parent # Find folders relative to this module
FG_folderpath = project_folderpath.parent # Path to find parallel Freely-Given.org repos
OET_OT_USFM_InputFolderPath = project_folderpath.joinpath( 'intermediateTexts/auto_edited_OT_USFM/' )
OET_NT_USFM_InputFolderPath = project_folderpath.joinpath( 'intermediateTexts/auto_edited_VLT_USFM/' )
# OET_USFM_OutputFolderPath = project_folderpath.joinpath( 'translatedTexts/LiteralVersion/' )
OET_HTML_OutputFolderPath = project_folderpath.joinpath( 'derivedTexts/simpleHTML/LiteralVersion/' )
assert OET_OT_USFM_InputFolderPath.is_dir()
assert OET_NT_USFM_InputFolderPath.is_dir()
# assert OET_USFM_OutputFolderPath.is_dir()
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

    # Convert files to simple HTML
    produce_HTML_files()
# end of convert_OET-LV_to_simple_HTML.main


# If you change any colours, etc., also need to adjust the Key above
CSS_TEXT = '''div.BibleText { }
span.upLink { font-size:1.5em; font-weight:bold; }
span.C { font-size:1.1em; color:green; }
span.V { vertical-align:super; font-size:0.5em; color:red; }
span.addedArticle { color:grey; }
span.addedCopula { color:pink; }
span.addedDirectObject { color:brown; }
span.addedExtra { color:lightGreen; }
span.addedOwner { color:darkOrchid; }
span.added { color:bisque; }
span.ul { color:darkGrey; }
span.dom { color:Gainsboro; }
span.schwa { font-size:0.75em; }
span.nominaSacra { font-weight:bold; }
p.rem { font-size:0.8em; color:grey; }
p.shortPrayer { text-align:center; }
p.mt1 { font-size:1.8em; }
p.mt2 { font-size:1.3em; }
p.LVsentence { margin-top:0.2em; margin-bottom:0.2em; }
'''

LV_INDEX_INTRO_HTML = '''<!DOCTYPE html>
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
  <p>Note that the <em>OET</em> places Yōannēs/John before Matthaios/Matthew.</p>
  <p><a href="JHN.html">Yōannēs/John</a> &nbsp;&nbsp;<a href="MAT.html">Matthaios/Matthew</a> &nbsp;&nbsp;<a href="MRK.html">Markos/Mark</a> &nbsp;&nbsp;<a href="LUK.html">Loukas/Luke</a> &nbsp;&nbsp;<a href="ACT.html">Acts</a><br>
    <a href="ROM.html">Romans</a> &nbsp;&nbsp;<a href="CO1.html">Corinthians 1</a> &nbsp;&nbsp;<a href="CO2.html">Corinthians 2</a><br>
    <a href="GAL.html">Galatians</a> &nbsp;&nbsp;<a href="EPH.html">Ephesians</a> &nbsp;&nbsp;<a href="PHP.html">Philippians</a> &nbsp;&nbsp;<a href="COL.html">Colossians</a><br>
    <a href="TH1.html">Thessalonians 1</a> &nbsp;&nbsp;<a href="TH2.html">Thessalonians 2</a> &nbsp;&nbsp;<a href="TI1.html">Timotheos/Timothy 1</a> &nbsp;&nbsp;<a href="TI2.html">Timotheos/Timothy 2</a> &nbsp;&nbsp;<a href="TIT.html">Titos/Titus</a><br>
    <a href="PHM.html">Filēmoni/Philemon</a><br>
    <a href="HEB.html">Hebrews</a><br>
    <a href="JAM.html">Yakōbos/James</a><br>
    <a href="PE1.html">Petros/Peter 1</a> &nbsp;&nbsp;<a href="PE2.html">Petros/Peter 2</a><br>
    <a href="JN1.html">Yōannēs/John 1</a> &nbsp;&nbsp;<a href="JN2.html">Yōannēs/John 2</a> &nbsp;&nbsp;<a href="JN3.html">Yōannēs/John 3</a><br>
    <a href="JDE.html">Youdas/Jude</a><br>
    <a href="REV.html">Revelation</a></p>
  <p>Whole <a href="OET-LV-NT.html">New Testament</a>
    (long and slower to load, but useful for easy searching of multiple books, etc.)</p>
  <h2 id="Intro">Literal Version Introduction</h2>
  <h3>The Open English Translation of the Bible (OET)</h3>
      <p>This <em>Literal Version</em> (OET-LV) forms just one-half of the new, forthcoming <em>Open English Translation</em> of the Bible (OET).
        The other half is the <em>Readers’ Version</em> (OET-RV) which work will resume on in 2023.
        These two versions, side-by-side, together make up the OET.</p>
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
        both this <em>Literal Version</em> and the <em>Readers’ Version</em>
        <b>have been specifically designed to be used together</b> in this way.
        We suggest reading the <em>Readers’ Version</em>, and if something stands out and you think in your mind
        <i>Does it really say that?</i> or <i>Could it really mean that?</i>,
        then flick your eyes to this <em>Literal Version</em> and see for yourself what’s really there in the original texts.</p>
      <p>On the other hand if you’ve been reading the Bible for a few decades already,
        maybe it would be fun to work through this <em>Literal Version</em> to get fresh insight
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
    <li>This <em>Literal Version</em> has the minimum number of interpreted extras,
        so we’ve added basic sentence punctuation (mostly just commas and periods/fullstops).
        The New Testament has no exclamation marks, no paragraphs,
        no speech marks (even the King James Bible didn’t have these), and no section headings.
        A limited number of footnotes relate mostly to the text of the source manuscripts
        that the <em>OET-LV</em> is translated from.</li>
    <li>This <em>Literal Version</em> retains the original units for all measurements
        (useful for historical and symbolic studies),
        whereas the <em>Readers’ Version</em> converts them to modern units (easier to understand and visualise).</li>
    <li>This <em>Literal Version</em> retains the original figurative language
        (even if it’s not a figure of speech that we are familiar with),
        whereas the <em>Readers’ Version</em> converts some figures of speech to modern equivalents
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
        you can always look across to the <em>Readers’ Version</em>.
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
            <b>meaning</b> of the word in this <em>Literal Version</em>.
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
    <li>This <em>Literal Version</em> tries to add as little as possible
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
        this <em>Literal Version</em> uses <i>you<span class="ul">_</span>all</i> for the plural form
        (although we are aware that some modern dialects now prefer <i>yous</i>).</li>
    <li>Because this <em>Literal Version</em> so closely follows the original languages,
            it’s important to remember that words often don’t match one-to-one between languages.
        This is one reason why the <em>LV</em> reads strangely:
            because the translators try to avoid using different English words if we can;
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
        However, we would also be able to understand <i>raise</i> in each of those cases.
        In addition, sometimes there’s a play on words in the Greek,
            where <i>raise</i> can intentional mean two or more of the above simultaneously!</li>
    <li>These particular pages use British spelling,
        but American spelling will also be available in the future.</li>
    <li>Our preference in most editions is to place <em>The Gospel according to John</em>
            <b>before</b> <em>Matthew</em>.
        This has a couple of advantages:
        <ol><li>The Old Testament starts with “In the beginning, god created…”
            and the New Testament starts with “In the beginning was the message…”.<li>
        <li><em>Acts</em> ends up right after the first book by its author <em>Luke</em>.</li>
        <li>It just reminds readers that the order of the “books” in the Bible
            is not set by sacred degree--only by tradition.</li>
        </ol>
        Some do complain that the traditional order of the first four gospel accounts
            represent the lion, the calf, the man, and the eagle of Rev 4:6-7
            which allegedly match with the banners (not described in the Bible) of the four divisions
            of the tribes of Israel mentioned in Numbers 2.</li>
    <li>Beware of some traps interpreting this <em>Literal Version</em>.
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
  <h3 id="Key">Key to symbols and colours in the OET-LV</h3>
    <p>You will notice that this <em>Literal Version</em> looks different from most Bibles that you’re used to:</p>
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
        even though this has been kept to an absolute minimum in this <em>Literal Version</em>.</li>
    <li><span class="nominaSacra">Bold text</span>: In the earliest copies of the original manuscripts,
        it appears that the scribes marked a small set of words that they considered
        to refer to <span class="nominaSacra">God</span>.
        (These markings are known as <a href="https://en.wikipedia.org/wiki/Nomina_sacra"><em>nomina sacra</em></a>
        or <em>sacred naming</em>.)
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
            This is because reading this <em>Literal Version</em> gives you a good insight into
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
        please do contact us by <a href="mailto:Freely.Given.org@gmail.com?subject=OET-LV Feedback">email</a>.
        Also if there’s something that we didn’t explain in this introduction, or didn’t explain very well.
        Thanks.</p>
  <p>HTML last updated: __LAST_UPDATED__</p>
</body></html>
'''

LV_FAQ_HTML = '''<!DOCTYPE html>
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
  <h3>What are the bolded words in the text?</h3>
  <p>As explained in the <a href="index.html#Key">Key</a>, the bold text
  indicates the use of <em>Nomina Sacra</em> on the original manuscripts.
  These are special markings and abbreviations done by the scribes,
  and in the earliest manuscripts, highlight words that are assumed to relate to God.</p>
  <h3 id="Feedback">Feedback</h3>
    <p>These web pages are a very preliminary preview into a work still in progress.
        The <em>OET Literal Version</em> is not yet finished, and not yet publicly released,
        but we need to have it available online for easy access for our checkers and reviewers.
        If you’re reading this and have questions that aren’t discussed here,
        please do contact us by <a href="mailto:Freely.Given.org@gmail.com?subject=OET-LV FAQs">email</a>.
        Also if there’s something that we didn’t explain in this introduction, or didn’t explain very well.
        Thanks.</p>
  <p>HTML last updated: __LAST_UPDATED__</p>
</body></html>
'''

DISCLAIMER_HTML = '''<p>Note: This is still a very early look into the unfinished text
of the <em>Open English Translation</em> of the Bible.
Please double-check the text before using in public.</p>
'''


LV_BOOK_INTRO_HTML1 = '''<p>Note: This <em>Literal Version</em> is a somewhat technical translation
designed to give the English reader a window into what’s actually written in the original languages.
(See the <a href="index.html#Intro">introduction</a> for more details—we
recommend that you read the introduction first if you’re wanting to read and understand this <em>Literal Version</em>.)
For nice, modern, readable English you should look at the (forthcoming) <em>Readers’ Version</em>.
(Between the two versions, you should also be able to get an idea about how Bible Translation
actually <a href="index.html#Learning">works</a>.
You can also compare your other favourite Bible translations with this <em>Literal Version</em>
to get more insight into how they also interpreted the original texts in crafting their translation.)</p>
'''

INTRO_PRAYER_HTML = '''<p class="shortPrayer">It is our prayer that this <em>Literal Version</em> of the
<em>Open English Translation</em> of the Bible will give you fresh insight into
the words of the inspired Biblical writers.</p><!--shortPrayer-->
'''

START_HTML = '''<!DOCTYPE html>
<html lang="en-US">
<head>
  <title>__TITLE__</title>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="keywords" content="Bible, OET, literal, version">
  <link rel="stylesheet" type="text/css" href="BibleBook.css">
</head>
<body>
'''
END_HTML = '</body></html>\n'

whole_Torah_html = whole_NT_html = ''
genericBookList = []
def produce_HTML_files() -> None:
    """
    """
    global whole_Torah_html, whole_NT_html
    fnPrint( DEBUGGING_THIS_MODULE, "produce_HTML_files()" )

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
            source_filename = f'OET-LV_{BBB}.usfm'
            sourceFolderpath = OET_NT_USFM_InputFolderPath if bookType=='NT' else OET_OT_USFM_InputFolderPath
            with open( sourceFolderpath.joinpath(source_filename), 'rt', encoding='utf-8' ) as usfm_input_file:
                usfm_text = usfm_input_file.read()
            assert "'" not in usfm_text, f'''Why do we have single quote in {source_filename}: {usfm_text[usfm_text.index("'")-20:usfm_text.index("'")+22]}'''
            assert '"' not in usfm_text, f'''Why do we have double quote in {source_filename}: {usfm_text[usfm_text.index('"')-20:usfm_text.index('"')+22]}'''

            book_start_html, book_html, book_end_html = convert_USFM_to_simple_HTML( BBB, usfm_text )

            output_filename = f'{BBB}.html'
            with open( OET_HTML_OutputFolderPath.joinpath(output_filename), 'wt', encoding='utf-8' ) as html_output_file:
                html_output_file.write( f'{book_start_html}\n{book_html}\n{book_end_html}' )

            # Having saved the book file, now for better orientation within the long file (wholeTorah or wholeNT),
            #   adjust book_html to include BBB text for chapters past chapter one
            bookAbbrev = BBB.title().replace('1','-1').replace('2','-2').replace('3','-3')
            chapterRegEx = re.compile('<span class="C" id="C(\d{1,3})V1">(\d{1,3})</span>')
            while True:
                for match in chapterRegEx.finditer( book_html ):
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

    # Output CSS and index and whole NT html
    with open( OET_HTML_OutputFolderPath.joinpath('BibleBook.css'), 'wt', encoding='utf-8' ) as css_output_file:
        css_output_file.write( CSS_TEXT )
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
# end of convert_OET-LV_to_simple_HTML.convert_USFM_to_simple_HTML function


def convert_USFM_to_simple_HTML( BBB:str, usfm_text:str ) -> Tuple[str, str, str]:
    fnPrint( DEBUGGING_THIS_MODULE, f"convert_USFM_to_simple_HTML( {BBB}, ({len(usfm_text)}) )" )

    links_html_template = '<p>__PREVIOUS__OET-LV <a href="index.html#Index">Book index</a>,' \
                 ' <a href="index.html#Intro">Intro</a>, <a href="index.html#Key">Key</a>,' \
                 'and <a href="FAQs.html">FAQs</a>' \
                 f'__NEXT__<br><br>__REST__</p>'
    if BBB in OT_BBB_LIST:
        links_html = links_html_template.replace('__REST__', 'Whole <a href="OET-LV-Torah.html">Torah/Pentateuch</a> (for easy searching of multiple books, etc.)' )

        previousBBB = OT_BBB_LIST[OT_BBB_LIST.index(BBB)-1] # Gives wrong value (@[-1]) for first book
        try: nextBBB = OT_BBB_LIST[OT_BBB_LIST.index(BBB)+1]
        except IndexError: nextBBB = NT_BBB_LIST[0] # above line fails on final book
        links_html = links_html.replace( '__PREVIOUS__', '' if BBB==NT_BBB_LIST[0]
            else f'<a href="{previousBBB}.html">Previous Book ({previousBBB})</a>{EM_SPACE}')
        links_html = links_html.replace( '__NEXT__', f'{EM_SPACE}<a href="{nextBBB}.html">Next Book ({nextBBB})</a>')
    elif BBB in NT_BBB_LIST:
        links_html = links_html_template.replace('__REST__', 'Whole <a href="OET-LV-NT.html">New Testament</a> (for easy searching of multiple books, etc.)' )

        previousBBB = OT_BBB_LIST[-1] if BBB==NT_BBB_LIST[0] else NT_BBB_LIST[NT_BBB_LIST.index(BBB)-1] # Gives wrong value (@[-1]) for first book
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
        if marker in ('rem',):
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
            C = rest
            # if C=='2': halt
            assert C.isdigit()
            if C == '1': # Add an inspirational note
                book_html = f'{book_html}{INTRO_PRAYER_HTML}<div class="BibleText">\n'
            # Note: as well as CV id's, we make sure there are simple C id's there as well
            start_c_bit = '<p class="LVsentence" id="C1">' if C=='1' else f'<a class="upLink" href="#" id="C{C}">↑</a> '
            book_html = f'{book_html}{start_c_bit}<span class="C" id="C{C}V1">{C}</span>{EN_SPACE}'
        elif marker == 'v':
            try: V, rest = rest.split( ' ', 1 )
            except ValueError: V, rest = rest, ''
            assert V.isdigit(), f"Expected a verse number digit with '{V=}' '{rest=}'"
            # Put sentences on new lines
            rest = rest.replace( '?)', 'COMBO' ) \
                        .replace( '.', '.</p>\n<p class="LVsentence">' ) \
                        .replace( '?', '?</p>\n<p class="LVsentence">' ) \
                        .replace( 'COMBO', '?)' )
            # We don't display the verse number for verse 1 (after chapter number)
            book_html = f'{book_html}{"" if book_html.endswith(">") else " "}{"" if V=="1" else f"""<span class="V" id="C{C}V{V}">{V}{NARROW_NON_BREAK_SPACE}</span>"""}{rest}'
        else:
            logging.error( f"{BBB} {C}:{V} LV has unexpected USFM marker: \\{marker}='{rest}'" )
            book_html = f'{book_html}<p>GOT UNEXPECTED{marker}={rest}</p>'
    book_html = f"{book_html}</p></div><!--BibleText-->"

    chapter_links = [f'<a href="#C{chapter_num}">C{chapter_num}</a>' for chapter_num in range( 1, int(C)+1 )]
    chapter_html = f'<p class="chapterLinks">{EM_SPACE.join(chapter_links)}</p><!--chapterLinks-->'
    book_start_html = f'{start_html}{links_html}\n{chapter_html}'

    book_html = book_html.replace( '\\nd ', '<span class="nominaSacra">' ) \
                .replace( '\\nd*', '</span>' )
    book_html = book_html.replace( '\\add +', '<span class="addedArticle">' ) \
                .replace( '\\add =', '<span class="addedCopula">' ) \
                .replace( '\\add ~', '<span class="addedDirectObject">' ) \
                .replace( '\\add >', '<span class="addedExtra">' ) \
                .replace( '\\add ^', '<span class="addedOwner">' ) \
                .replace( '\\add ', '<span class="added">' ) \
                .replace( '\\add*', '</span>' )
    # Make underlines grey with "ul" spans (except when already at end of a span)
    book_html = book_html.replace( '_</span>', '%%SPAN%%' ) \
                .replace( '_', '<span class="ul">_</span>' ) \
                .replace( '%%SPAN%%', '_</span>' )
    # Make schwas smaller
    book_html = book_html.replace( 'ə', '<span class="schwa">ə</span>' )
    if BBB in OT_BBB_LIST: # Hebrew direct object markers (DOMs)
        book_html = book_html.replace( 'DOM', '<span class="dom">DOM</span>' ) \
                        .replace( '[was]', '<span class="addedCopula">was</span>' ) \
                        .replace( '[', '<span class="added">' ) \
                        .replace( ']', '</span>' )
    return ( book_start_html,
             book_html,
             f'{chapter_html}\n{links_html}\n{END_HTML}' )
# end of convert_OET-LV_to_simple_HTML.produce_HTML_files()


if __name__ == '__main__':
    # Configure basic Bible Organisational System (BOS) set-up
    parser = BibleOrgSysGlobals.setup( PROGRAM_NAME, PROGRAM_VERSION )
    BibleOrgSysGlobals.addStandardOptionsAndProcess( parser, exportAvailable=False )

    main()

    BibleOrgSysGlobals.closedown( PROGRAM_NAME, PROGRAM_VERSION )
# end of convert_OET-LV_to_simple_HTML.py