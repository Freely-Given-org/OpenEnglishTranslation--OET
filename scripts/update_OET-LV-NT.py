#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# update_OET-LV-NT.py
#
# Script to backport the ULT OT into empty verses of the OET-LV OT
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

Updated Sept 2022 to not backfill the New Testament.
"""
from gettext import gettext as _
from typing import List, Tuple, Optional
from pathlib import Path
import shutil
import re

if __name__ == '__main__':
    import sys
    sys.path.insert( 0, '../../BibleOrgSys/' )
from BibleOrgSys import BibleOrgSysGlobals
from BibleOrgSys.BibleOrgSysGlobals import vPrint, fnPrint, dPrint
from BibleOrgSys.Bible import Bible
from BibleOrgSys.Reference.BibleOrganisationalSystems import BibleOrganisationalSystem
from BibleOrgSys.Misc import CompareBibles


LAST_MODIFIED_DATE = '2022-09-13' # by RJH
SHORT_PROGRAM_NAME = "Update_OET-LV-NT"
PROGRAM_NAME = "Update OET-LV New Testament"
PROGRAM_VERSION = '0.13'
PROGRAM_NAME_VERSION = '{} v{}'.format( SHORT_PROGRAM_NAME, PROGRAM_VERSION )

DEBUGGING_THIS_MODULE = False


project_folderpath = Path(__file__).parent.parent # Find folders relative to this module
FG_folderpath = project_folderpath.parent # Path to find parallel Freely-Given.org repos
OETUSFMInputFolderPath = FG_folderpath.joinpath( 'ScriptedBibleEditor/TestFiles/edited_VLT_USFM/' )
OETUSFMOutputFolderPath = project_folderpath.joinpath( 'translatedTexts/LiteralVersion/' )
OETHTMLOutputFolderPath = project_folderpath.joinpath( 'derivedTexts/simpleHTML/LiteralVersion/' )
assert OETUSFMInputFolderPath.is_dir()
assert OETUSFMOutputFolderPath.is_dir()
assert OETHTMLOutputFolderPath.is_dir()

EN_SPACE, EM_SPACE = ' ', ' '
NARROW_NON_BREAK_SPACE = ' '
BBB_LIST = ('MAT','MRK','LUK','JHN','ACT','ROM','CO1','CO2','GAL','EPH','PHP','COL','TH1','TH2','TI1','TI2','TIT','PHM','HEB','JAM','PE1','PE2','JN1','JN2','JN3','JDE','REV')
assert len(BBB_LIST) == 27

INDEX_HTML = '''<!DOCTYPE html>
<html lang="en-US">
<head>
  <title>OET Literal Version Development</title>
  <meta charset="utf-8">
  <meta http-equiv="Content-Type" content="text/html;charset=utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="keywords" content="Bible, OET, literal, version">
  <link rel="stylesheet" type="text/css" href="BibleBook.css">
</head>
<body>
  <p><a href="../">Up</a></p>
  <h1>Open English Translation Literal Version (OET-LV) Development</h1>
  <h2>Very preliminary in-progress still-private test version</h2>
  <p><a href="OET-LV_MAT.html">Matthaios/Matthew</a> &nbsp;&nbsp;<a href="OET-LV_MRK.html">Markos/Mark</a> &nbsp;&nbsp;<a href="OET-LV_LUK.html">Loukas/Luke</a> &nbsp;&nbsp;<a href="OET-LV_JHN.html">Yōannēs/John</a> &nbsp;&nbsp;<a href="OET-LV_ACT.html">Acts</a><br>
    <a href="OET-LV_ROM.html">Romans</a> &nbsp;&nbsp;<a href="OET-LV_CO1.html">Corinthians 1</a> &nbsp;&nbsp;<a href="OET-LV_CO2.html">Corinthians 2</a><br>
    <a href="OET-LV_GAL.html">Galatians</a> &nbsp;&nbsp;<a href="OET-LV_EPH.html">Ephesians</a> &nbsp;&nbsp;<a href="OET-LV_PHP.html">Philippians</a> &nbsp;&nbsp;<a href="OET-LV_COL.html">Colossians</a><br>
    <a href="OET-LV_TH1.html">Thessalonians 1</a> &nbsp;&nbsp;<a href="OET-LV_TH2.html">Thessalonians 2</a> &nbsp;&nbsp;<a href="OET-LV_TI1.html">Timotheos/Timothy 1</a> &nbsp;&nbsp;<a href="OET-LV_TI2.html">Timotheos/Timothy 2</a> &nbsp;&nbsp;<a href="OET-LV_TIT.html">Titos/Titus</a><br>
    <a href="OET-LV_PHM.html">Filēmoni/Philemon</a><br>
    <a href="OET-LV_HEB.html">Hebrews</a><br>
    <a href="OET-LV_JAM.html">Yakōbos/James</a><br>
    <a href="OET-LV_PE1.html">Petros/Peter 1</a> &nbsp;&nbsp;<a href="OET-LV_PE2.html">Petros/Peter 2</a><br>
    <a href="OET-LV_JN1.html">Yōannēs/John 1</a> &nbsp;&nbsp;<a href="OET-LV_JN2.html">Yōannēs/John 2</a> &nbsp;&nbsp;<a href="OET-LV_JN3.html">Yōannēs/John 3</a><br>
    <a href="OET-LV_JDE.html">Youdas/Jude</a><br>
    <a href="OET-LV_REV.html">Revelation</a></p>
  <p>Whole <a href="OET-LV.html">New Testament</a> (for easy searching, etc.)</p>
  <h2>Introduction</h2>
  <h3>The Open English Translation of the Bible (OET)</h3>
      <p>The <em>Literal Version</em> (OET-LV) forms just one-half of the new, forthcoming <em>Open English Translation</em> of the Bible (OET).
        The other half is the <em>Readers’ Version</em> (OET-RV) which work will resume on in 2023.
        These two versions, side-by-side, make up the OET.</p>
      <p>So why two versions? Many people ask the question: <i>Which English Bible translation should I use?</i>
        Well, often the answer is that there’s no single Bible translation which can meet all of the needs of the thoughtful reader.
        Why not? It’s because we often have two related desires that we need answered:<p>
      <ol><li>What does the original (Hebrew or Greek) text actually say? and</li>
        <li>What did the original writer mean? (i.e., What should we understand from it?)</li></ol>
      <p>Our traditional answer has always been that it’s best to use two translations—one more literal
        to give a window into the actual Hebrew or Greek words, and one more <i>dynamic</i>
        that’s easier for us modern readers to understand.</p>
      <p>So the OET gives both side-by-side, and with the advantage that
        both the <em>Literal Version</em> and the <em>Readers’ Version</em>
        <b>have been specifically designed to be used together</b> in this way.
        We suggest reading the <em>Readers’ Version</em>, and if something stands out and you think in your mind
        <i>Does it really say that?</i> or <i>Could it really mean that?</i>,
        then flick your eyes to the <em>Literal Version</em> and see for yourself what’s really there in the original texts.</p>
      <p>On the other hand if you’ve been reading the Bible for a few decades already,
        maybe it would be fun to work through the <em>Literal Version</em> to get fresh insight
        into what’s actually written there in those original languages.</p>
  <h3>Goals</h3>
    <p>Put simply, the goal of the <em>Open English Translation</em> is simply to make the Bible more accessible
        to this current generation with the best of a free-and-open easy-to-understand <em>Readers’ Version</em>
        alongside a faithful <em>Literal Version</em> so that you yourself can checkout what was said and what is interpreted.</p>
  <h3>Distinctives</h3>
    <p>The OET has the following distinguishing points:</p>
    <ul><li>An easy-to-understand <em>Readers’ Version</em> side-by-side with a very <em>Literal Version</em></li>
    <li>A generous open license so that the <em>Open English Translation</em> can be
        freely used in any Bible app or website, or printed in your church Bible-study notes
        without even needing to request permission.</li>
    <li>The <em>Literal Version</em> has the minimum number of interpreted extras,
        so we’ve added basic sentence punctuation (mostly commas and periods/fullstops).
        The New Testament has no question or exclamation marks, no paragraphs,
        no speech marks (even the King James Bible didn’t have these), and no section headings.
        A limited number of footnotes relate mostly to the text of the source manuscripts
        that the OET-LV is translated from.</li>
    <li>The <em>Literal Version</em> retains the original units for all measurements (useful for historical and symbolic studies),
        whereas the <em>Readers’ Version</em> converts them to modern units (easier to understand and visualise).</li>
    <li>The <em>Literal Version</em> retains the original figurative language (even if it’s not a figure of speech that we are familiar with),
        whereas the <em>Readers’ Version</em> converts some figures of speech to modern equivalents (easier to understand).</li>
    <li>Being a 21<span style="vertical-align:super;font-size:0.8em;">st</span> century translation done in an era
        when there is much more effort in general to respect speakers of other languages
        (including the languages of ethnic minorities in our own countries)
        and to pronounce their names and placenames correctly,
        the <em>OET</em> attempts to do the same for Biblical names and placenames.
        (This is a little complex when we have both Hebrew and Greek versions of names and placenames.
        A final strategy is yet to be decided.)
        If you have difficulty following the names in the <em>Literal Version</em>,
        you can always look across to the <em>Readers’ Version</em>.
        (Most English readers looking at names in the Bible all the way from <i>Jericho</i> to <i>Jesus</i>
        would have no idea that there’s no <b>J</b> letter or sound in either Hebrew or Greek,
        plus there’s absolutely no such name as <i>James</i> in the New Testament manuscripts!
        xxx)</li>
    <li>In addition to wanting to get names and placenames more accurate,
        we’ve also attempted to modernise the spelling (transliterations) of these names,
        e.g., using <b>f</b> instead of <b>ph</b>, so <i>Epafras</i> instead of <i>Epaphras</i>.</li>
    <li>With regular words, we’ve tried to do the opposite,
        i.e., to use less Greek rather than more wherever possible.
        So a word like <i>baptise</i> (which is an adapted transliteration of the Greek verb),
        actually gets translated, so this example becomes <i>immerse</i>.</li>
    <li><i>Italics</i> are only used for <em>emphasis</em>, not to indicate <i>added words</i> as historically done in
        older translations due to limitations of the original printing processes.
        The <em>OEM</em> fixes the problem where most modern printing uses <i>italics</i> for <em>emphasis</em>
        whereas older Bibles use <i>italics</i> for the words which should actually be <b>deemphasied</b>,
        i.e., the words which actually <b>aren’t</b> in the original manuscripts!</li>
    </ul>
  <h3>Key for the OET-LV</h3>
    <p>You will notice the the <em>Literal Version</em> looks different from most Bibles that you’re used to:
    </p>
    <ul><li>Words joined together by underlines are translated from a single original word,
        e.g., <em>he<span class="ul">_</span>is<span class="ul">_</span>walking</em>.
        Both Hebrew and Greek can express the subject as part of the verb,
        often saying in one word what takes us three.</li>
    <li>Words groups with hanging underlines mean that to make natural English,
        we needed to insert the translation of one word into the middle of another,
        e.g., <em>not he<span class="ul">_</span>is<span class="ul">_</span>walking</em> becomes much more natural in English if
        rearranged to <em>he<span class="ul">_</span>is<span class="ul">_</span> &nbsp;not&nbsp; <span class="ul">_</span>walking</em>.</li>
    <li>Grey words indicate added articles.
        English uses <em>a</em> or <em>the</em> to indicate whether a noun
        is definite or indefinite.
        Other languages don’t necessarily work the same way.
        If we have to add an article to make the English sound correct, we indicate this by greying it,
        e.g., <em><span class="addedArticle">the</span> man</em>.
        (We use lighter colours to deemphasise added words like these rather than using
        <i>italics</i> which are mostly used these days for emphasis.)</li>
    <li>A copula is a word that links a subject and its complement (or description),
        e.g., the word <i><span class="addedCopula">is</span></i> in the sentence <i>The house <span class="addedCopula">is</span> white.</i>
        Other languages don’t necessarily work the same way and can say things like
        <i>White the house.</i>
        Added copulas are marked with a <span class="addedCopula">light colour</span>.</li>
    <li>Certain English verbs require a direct object. Think of the difference between
        <i>He said, blah, blah</i> and <i>He told, blah, blah</i>.
        The second one feels like it requires something like <i>He told <span class="addedDirectObject">him</span>, blah, blah</i>.
        Added direct objects are marked with a <span class="addedDirectObject">light colour</span>.</li>
    <li>In other languages it may be possible to say something like <i>The having<span class="ul">_</span>fallen</i>.
        In English, we must say something like <i>The <span class="addedExtra">one</span> having<span class="ul">_</span>fallen</i> or <i>The <span class="addedExtra">person</span> having fallen</i>.
        If the article is marked as plural in the source language, we may be able to say <i>The <span class="addedExtra">ones</span> having<span class="ul">_</span>fallen</i>.
        If the article is marked as feminine in the source language, we may be able to say <i>The <span class="addedExtra">woman</span> having<span class="ul">_</span>fallen</i>.
        Added words like this are marked with a <span class="addedExtra">light colour</span>.</li>
    <li>If we have an original construction like <i>God spoke by son</i> (from Heb 1:2),
        in English we need to add a word like <i>God spoke by <span class="addedArticle">the</span> son</i> or <i>God spoke by <span class="addedOwner">his</span> son</i>.
        In the latter case (where we don’t just choose an article like <i><span class="addedArticle">the</span></i>),
        we mark these added words with a <span class="addedOwner">light colour</span>.</li>
    <li>Other added words not in the above categories are also marked with a <span class="added">light colour</span>.</li>
    <li>All of this colouring is to be completely open by helping the reader to be able to see where the translators have chosen to
        add words to the Hebrew or Greek in order to make the English sound slightly better,
        although this has been kept to an absolute minimum in the <em>Literal Version</em>.</li>
    <li>Where it is determined that a group of words was either definitely or most likely not in the original manuscripts (autographs),
        they are omitted in the OET-LV without any notes.
        These manuscript decisions were mostly made by the authors of the two main works that we relied on to translate
        the OET from—see the acknowledgements below for more details.)</li>
    </ul>
  <h3>Biblical names</h3>
    <p>Note that where Hebrew or Greek transliterations are given,
        Engish speakers will have the most success pronouncing these names if you
        look up the pronounciation of the five “pure” Spanish vowels in your search engine.
        Individual vowels should be pronounced in this way,
        e.g., each of the four vowels in <i>Eleazar</i>.</p>
    <p>Macrons (overlines over the vowels, like ē or ō) indicate lengthened vowels,
        so the pronounciation is the same as the Spanish vowels,
        but just prolonged.</p>
    <p>The vowel <a href="https://en.wikipedia.org/wiki/Schwa">schwa</a> <i>ə</i>
        should be regarded as a fleeting (very short and unstressed), neutral vowel
        which is the minimal vowel required to linguistically join the surrounding consonants
        e.g., in <i>Yəhūdāh</i>.</p>
    <p>Dipthongs (e.g., ai, au, ou)
        are a limited set of two vowels,
        where one vowel glides into the other,
        so even though the spelling of a dipthong is two letters,
        together they are the centre of only one syllable.<p>
    <p>We use the symbol ' to mark a <a href="https://en.wikipedia.org/wiki/Glottal_stop">glottal stop<a/>
        which is the sound that some UK speakers put in the middle of the word <i>butter</i> (ba'a),
        so <i>Abra'am</i> (from the Greek) is three distinct syllables—that's not a long a.</p>
  <h3>Acknowledgements</h3>
    <p>A work like this could not be done with building on the work of so many that have gone before, including:</p>
    <ul><li>The creator God who communicates with us in various ways,
        but who specifically inspired the writing of the Scriptures
        and caused it to be preserved throughout the millenia
        despite the best efforts of some who tried to destroy them.</li>
    <li>Those who took the time to write down their interactions with God,
        beginning with Moses and those before him who wrote down their experiences even though making the writing materials was so much work,
        all the way through to the disciples and others who wrote of their interactions with Jesus the Messiah, and the Holy Spirit.</li>
    <li>Those who faithfully copied and carefully stored those manuscripts over the centuries
        and thus allowed the works of the original writers to be preserved for us to translate.</li>
    <li>Those who collected, preserved, photographed and digitized, and transcribed those manuscripts
        so that we could have access to them.</li>
    <li>Those who studied the variations in those copies and helped us to get the best evaluations of
        which words were most likely present in the original manuscripts (<a href="https://en.wikipedia.org/wiki/Autograph">autographs</a>).
        For the (mostly) Hebrew Old Testament, we are especially reliant on the work
        of <a href="https://hb.OpenScriptures.org/">Open Scriptures</a>, given to the world under a generous open licence.
        For the Greek New Testament, we are especially reliant on the work
        of the <a href="https://GreekCNTR.org">Center for New Testament Restoration</a>
        which is also given to the world under a generous open licence.</li>
    </ul>
  <h3>Status</h3>
    <p>English sentences have more limitations on their word order than Greek sentences do.
        So any word-for-word Greek literal translation has to be reordered to be readable in English.
        Currently, the following books (just over 50% of the NT) have been reordered:
        <b>Mat, Mark, Luke, John, Acts, 1 Peter, 2 Peter, 3 John, and Jude</b>,
        leaving the following books which have not yet been reordered
        and will therefore be even harder to read in the <em>Literal Version</em>:
        Rom, 1&2 Cor, Gal, Eph, Php, Col, 1&2 Thess, 1&2 Tim, Titus, Phlm, Heb, and 1&2 John.</p>
    <p>After completing sentence reordering and fixing capitalisation and punctuation,
        we then plan to do more investigation into word concordance.
        For example, if an original language word can have multiple meanings,
        we want to indicate in the <em>OET Literal Version</em> where a
        translator has already made that interpretation.</p>
  <h3>Feedback</h3>
    <p>These web pages are a preliminary preview into a work still in progress.
        The <em>OET Literal Version</em> is not yet finished, and not yet publicly released,
        but we need to have it available online for easy access for our checkers and reviewers.
        If you are reading this, and notice problems or issues,
        please do contact us by <a href="mailto:Freely.Given.org@gmail.com?subject=OET-LV Feedback">email</a>.
        Thanks.</p>
</body></html>
'''

CSS_TEXT = '''
span.C { font-size:2em; color:green; }
span.V { vertical-align:super; font-size:0.8em; color:red; }
span.addedArticle { color:grey; }
span.addedCopula { color:pink; }
span.addedDirectObject { color:brown; }
span.addedExtra { color:lightGreen; }
span.addedOwner { color:darkOrchid; }
span.added { color:bisque; }
span.ul { color:darkGrey; }
p.rem { font-size:0.8em; color:grey; }
p.mt1 { font-size:1.8em; }
p.mt2 { font-size:1.3em; }
'''

START_HTML = '''<!DOCTYPE html>
<html lang="en-US">
<head>
  <title>__TITLE__</title>
  <meta charset="utf-8">
  <meta http-equiv="Content-Type" content="text/html;charset=utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="keywords" content="Bible, OET, literal, version">
  <link rel="stylesheet" type="text/css" href="BibleBook.css">
</head>
<body>
'''
END_HTML = '</body></html>\n'
whole_NT_html = ''

def convert_USFM_to_simple_HTML( BBB:str, usfm_text:str ) -> (str, str, str):
    fnPrint( DEBUGGING_THIS_MODULE, f"convert_USFM_to_simple_HTML( ({len(usfm_text)}) )" )

    links_html = f'<p>__PREVIOUS__<a href="index.html">OET-LV Index</a>__NEXT__{EM_SPACE}Whole <a href="OET-LV.html">New Testament</a> (for easy searching, etc.)</p>'

    previousBBB = None if BBB=='MAT' else BBB_LIST[BBB_LIST.index(BBB)-1]
    nextBBB = None if BBB=='REV' else BBB_LIST[BBB_LIST.index(BBB)+1]
    links_html = links_html.replace( '__PREVIOUS__', '' if BBB=='MAT'
        else f'<a href="OET-LV_{previousBBB}.html">Previous Book ({previousBBB})</a>{EM_SPACE}')
    links_html = links_html.replace( '__NEXT__', '' if BBB=='REV'
        else f'{EM_SPACE}<a href="OET-LV_{nextBBB}.html">Next Book ({nextBBB})</a>')
    book_start_html = f'{START_HTML}{links_html}\n'

    C = V = '0'
    book_html = ''
    for usfm_line in usfm_text.split( '\n' ):
        if not usfm_line: continue # Ignore blank lines
        assert usfm_line.startswith( '\\' )
        usfm_line = usfm_line[1:] # Remove the leading backslash
        try: marker, rest = usfm_line.split( ' ', 1 )
        except ValueError: marker, rest = usfm_line, ''
        # print( f"{marker=} {rest=}")
        if marker in ('id','usfm','ide','h','toc2','toc3'):
            continue # We don't need to map those markers to HTML
        if marker in ('rem','mt1','mt2'):
            book_html = f'{book_html}<p class="{marker}">{rest}</p>\n'
        elif marker == 'toc1':
            book_start_html = book_start_html.replace( '__TITLE__', rest )
        elif marker == 'c':
            V = '0'
            C = rest
            # if C=='2': halt
            assert C.isdigit()
            book_html = f'{book_html}<span class="C" id="C{C}V1">{C}</span>{EN_SPACE}'
        elif marker == 'v':
            try: V, rest = rest.split( ' ', 1 )
            except ValueError: V, rest = rest, ''
            assert V.isdigit(), f"Expected a verse number digit with '{V=}' '{rest=}'"
            # Put sentences on new lines
            rest = rest.replace( '?)', 'COMBO' ) \
                        .replace( '.', '.<br>\n&nbsp;&nbsp;' ) \
                        .replace( '?', '?<br>\n&nbsp;&nbsp;' ) \
                        .replace( 'COMBO', '?)' )
            # We don't display the verse number for verse 1 (after chapter number)
            book_html = f'{book_html}{"" if book_html.endswith(">") else " "}{"" if V=="1" else f"""<span class="V" id="C{C}V{V}">{V}</span>{NARROW_NON_BREAK_SPACE}"""}{rest}'
        else:
            book_html = f'{book_html}<p>GOT UNEXPECTED{marker}={rest}</p>'

    book_html = book_html.replace( '\\add +', '<span class="addedArticle">' ) \
                .replace( '\\add =', '<span class="addedCopula">' ) \
                .replace( '\\add ~', '<span class="addedDirectObject">' ) \
                .replace( '\\add >', '<span class="addedExtra">' ) \
                .replace( '\\add ^', '<span class="addedOwner">' ) \
                .replace( '\\add ', '<span class="added">' ) \
                .replace( '\\add*', '</span>' )
    book_html = book_html.replace( '_</span>', '%%SPAN%%' ) \
                .replace( '_', '<span class="ul">_</span>' ) \
                .replace( '%%SPAN%%', '_</span>' )
    return book_start_html, book_html, f'{links_html}\n{END_HTML}'


global genericBookList
def copy_in_NT_from_ScriptedBibleEditor() -> None:
    fnPrint( DEBUGGING_THIS_MODULE, "copy_in_NT_from_ScriptedBibleEditor()" )
    numFilesCopied = 0
    for BBB in genericBookList: # includes intro, etc.
        if BibleOrgSysGlobals.loadedBibleBooksCodes.isNewTestament_NR( BBB ):
            filename = f'OET-LV_{BBB}.usfm'
            vPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"  About to copy {BBB} file {filename} from {OETUSFMInputFolderPath} to {OETUSFMOutputFolderPath}")
            shutil.copy2( OETUSFMInputFolderPath.joinpath(filename), OETUSFMOutputFolderPath )
            numFilesCopied += 1
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"Finished copying {numFilesCopied} NT books\n  from {OETUSFMInputFolderPath}\n  to {OETUSFMOutputFolderPath}." )


def produce_NT_HTML_files() -> None:
    global whole_NT_html
    fnPrint( DEBUGGING_THIS_MODULE, "produce_NT_HTML_files()" )

    numBooksProcessed = 0
    for BBB in genericBookList: # includes intro, etc.
        if BibleOrgSysGlobals.loadedBibleBooksCodes.isNewTestament_NR( BBB ):
            source_filename = f'OET-LV_{BBB}.usfm'
            with open( OETUSFMOutputFolderPath.joinpath(source_filename), 'rt', encoding='utf-8' ) as usfm_input_file:
                usfm_text = usfm_input_file.read()

            book_start_html, book_html, book_end_html = convert_USFM_to_simple_HTML( BBB, usfm_text )

            output_filename = f'OET-LV_{BBB}.html'
            with open( OETHTMLOutputFolderPath.joinpath(output_filename), 'wt', encoding='utf-8' ) as html_output_file:
                html_output_file.write( f'{book_start_html}\n{book_html}\n{book_end_html}' )

            # Adjust book_html to include BBB for chapters past chapter one (for better orientation within the entire NT)
            bookAbbrev = BBB.title().replace('1','-1').replace('2','-2').replace('3','-3')
            chapterRegEx = re.compile('<span class="C" id="C(\d{1,3})V1">(\d{1,3})</span>')
            while True:
                for match in chapterRegEx.finditer( book_html ):
                    assert match.group(1) == match.group(2)
                    if match.group(1) != '1': # We don't adjust chapter one
                        # print(BBB,match,match.group(1),book_html[match.start():match.end()])
                        insert_point = match.end() - len(match.group(2)) - 7 # len('</span>')
                        book_html = f'{book_html[:insert_point]}{bookAbbrev} {book_html[insert_point:]}'
                        break # redo the search
                else: break
            whole_NT_html = f'{whole_NT_html}{book_html}'

            numBooksProcessed += 1

    # Output CSS and index and whole NT html
    with open( OETHTMLOutputFolderPath.joinpath('BibleBook.css'), 'wt', encoding='utf-8' ) as css_output_file:
        css_output_file.write( CSS_TEXT )
    with open( OETHTMLOutputFolderPath.joinpath('index.html'), 'wt', encoding='utf-8' ) as html_index_file:
        html_index_file.write( INDEX_HTML )
    with open( OETHTMLOutputFolderPath.joinpath('OET-LV.html'), 'wt', encoding='utf-8' ) as html_output_file:
        html_output_file.write( f'{START_HTML.replace("__TITLE__","OET-LV (Preliminary)")}\n'
                                f'<p><a href="index.html">OET-LV Index</a></p>\n{whole_NT_html}\n'
                                f'<p><a href="index.html">OET-LV Index</a></p>\n{END_HTML}' )

    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"Finished processing {numBooksProcessed} HTML books." )


def main():
    """
    Main program to handle command line parameters and then run what they want.
    """
    BibleOrgSysGlobals.introduceProgram( __name__, PROGRAM_NAME_VERSION, LAST_MODIFIED_DATE )

    global genericBookList
    genericBibleOrganisationalSystem = BibleOrganisationalSystem( 'GENERIC-KJV-ENG' )
    genericBookList = genericBibleOrganisationalSystem.getBookList()

    copy_in_NT_from_ScriptedBibleEditor()
    produce_NT_HTML_files()
# end of update_OET-LV-NT.main

if __name__ == '__main__':
    # Configure basic Bible Organisational System (BOS) set-up
    parser = BibleOrgSysGlobals.setup( PROGRAM_NAME, PROGRAM_VERSION )
    BibleOrgSysGlobals.addStandardOptionsAndProcess( parser, exportAvailable=False )

    main()

    BibleOrgSysGlobals.closedown( PROGRAM_NAME, PROGRAM_VERSION )
# end of update_OET-LV-NT.py
