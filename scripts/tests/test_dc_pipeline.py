"""DC source preservation, ambiguous glosses, and editorial/rebuild safeguards."""
import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'build_OET-LV_DC.py'
SPEC = importlib.util.spec_from_file_location('oet_dc_build', SCRIPT)
dc = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = dc
SPEC.loader.exec_module(dc)
HAVE_SOURCES = all((dc.CACHE / item['filename']).is_file()
                   for item in dc.load_manifest(dc.MANIFEST)['files'])


class SourceTests(unittest.TestCase):
    def test_paragraph_continuation_and_lettered_verse_are_not_lost(self):
        text = '\\id ESG\n\\c 1\n\\v 1 ἄνθρωπος.\n\\p καὶ θεός.\n\\v 1b λόγος.\n'
        verses = dc.parse_usfm(text, 'fixture.usfm')
        self.assertEqual([v.source_ref for v in verses], ['ESG_1:1', 'ESG_1:1b'])
        self.assertEqual(verses[0].text, 'ἄνθρωπος. καὶ θεός.')

    def test_known_sirach_heading_is_not_scripture(self):
        text = '\\id SIR\n\\c 1\n\\v 1 λόγος.\n\\p ΛΟΓΟΙ ΠΑΡΑΒΟΛΩΝ.\n\\v 2 σοφία.\n'
        verses = dc.parse_usfm(text, 'fixture.usfm')
        self.assertEqual([v.text for v in verses], ['λόγος.', 'σοφία.'])

    def test_duplicate_and_unsupported_markup_fail(self):
        for text in ['\\id TOB\n\\c 1\n\\v 1 λόγος\n\\v 1 θεός',
                     '\\id TOB\n\\c 1\n\\v 1 λόγος \\f + footnote\\f*',
                     '\\id TOB\n\\c 1\n\\z unknown\n\\v 1 λόγος']:
            with self.subTest(text=text), self.assertRaises(ValueError):
                dc.parse_usfm(text, 'fixture.usfm')

    def test_tokens_reconstruct_elision_combining_marks_and_punctuation(self):
        text = '“κατʼ ἐμοῦ, λόγος· οὐκ ἔστιν;”'
        tokens = list(dc.tokenise(text))
        self.assertEqual([t[0] for t in tokens], ['κατʼ', 'ἐμοῦ', 'λόγος', 'οὐκ', 'ἔστιν'])
        self.assertEqual(''.join(before + word + after for word, before, after in tokens), text)

    def test_changed_download_fails_checksum(self):
        item = dict(filename='fixture', bytes=3, sha256=hashlib.sha256(b'abc').hexdigest())
        dc.verify_data(b'abc', item)
        with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
            dc.verify_data(b'abd', item)

    def test_tsv_is_compatible_with_bos_literal_tab_reader(self):
        candidates = json.dumps([{'lemma': 'λόγος', 'gloss': '"word"'}], ensure_ascii=False)
        table = dc.tsv_text(['GreekWord', 'Candidates'], [{'GreekWord': 'λόγος', 'Candidates': candidates}])
        fields = table.splitlines()[1].split('\t')
        self.assertEqual(json.loads(fields[1])[0]['gloss'], '"word"')
        with self.assertRaises(ValueError):
            dc.tsv_text(['Gloss'], [{'Gloss': 'word\nnext row'}])

    def test_wrong_cached_file_is_never_silently_replaced(self):
        with tempfile.TemporaryDirectory() as temp:
            cache = Path(temp)
            (cache / 'fixture').write_bytes(b'bad')
            item = dict(filename='fixture', bytes=3, sha256=hashlib.sha256(b'abc').hexdigest())
            with self.assertRaises(ValueError):
                dc.sources({'files': [item]}, cache, download=True)
            self.assertEqual((cache / 'fixture').read_bytes(), b'bad')


class GlossTests(unittest.TestCase):
    def test_grave_accent_matches_but_breathings_and_acute_are_significant(self):
        self.assertEqual(dc.normalise('καὶ'), dc.normalise('καί'))
        self.assertNotEqual(dc.normalise('ἡ'), dc.normalise('ἤ'))
        self.assertNotEqual(dc.normalise('εἰ'), dc.normalise('εἷ'))

    def test_unaccented_homographs_keep_both_english_alternatives(self):
        lexicon = dc.Lexicon()
        lexicon.add('ἡ', dc.Candidate('ὁ', 'the', 'test'), form=True)
        lexicon.add('ἤ', dc.Candidate('ἤ', 'or', 'test'), form=True)
        result = lexicon.lookup('Η')
        self.assertEqual(result['GlossStatus'], 'draft-alternatives')
        self.assertEqual(result['OETGlossWords'], 'or/the')
        self.assertEqual(result['Lemma'], '')
        self.assertEqual(len(json.loads(result['Candidates'])), 2)
        self.assertEqual(lexicon.lookup('ἡ')['OETGlossWords'], 'the')

    def test_conflicting_lemmas_never_choose_most_common(self):
        lexicon = dc.Lexicon()
        lexicon.add('form', dc.Candidate('lemma1', 'one', 'test'), form=True)
        lexicon.add('form', dc.Candidate('lemma2', 'two', 'test'), form=True)
        self.assertEqual(lexicon.lookup('form')['OETGlossWords'], 'one/two')

    def test_name_requires_evidence_not_just_a_capital(self):
        lexicon = dc.Lexicon()
        self.assertEqual(lexicon.lookup('Ἄγνωστον')['GlossStatus'], 'missing')
        lexicon.add_name('Φίλος', 'Φίλος', 'name fixture')
        lexicon.add('φίλον', dc.Candidate('φίλος', 'friend', 'ordinary word'), form=True)
        self.assertEqual(lexicon.lookup('Φίλον')['OETGlossWords'], 'friend')

    def test_name_forms_use_nt_transliterator_and_preserve_evidence(self):
        lexicon = dc.Lexicon()
        lexicon.add_name('Τωβιηλ', 'Τωβιηλ', 'name fixture')
        lexicon.add_name('Ὀλοφέρνης', 'Ὀλοφέρνης', 'name fixture')
        result = lexicon.lookup('Τωβιὴλ')
        self.assertEqual(result['OETGlossWords'], 'Tōbiaʸl')
        self.assertEqual(result['OETGlossWords'], dc.greek_transliterator()('Τωβιὴλ'))
        self.assertEqual(result['GlossStatus'], 'name-transliteration')
        self.assertEqual(result['LexiconGloss'], '')
        self.assertTrue(json.loads(result['Candidates'])[0]['proper_name'])
        self.assertEqual(lexicon.lookup('Ὀλοφέρνου')['GlossStatus'], 'name-transliteration-candidate')
        self.assertEqual(lexicon.lookup('Ὀλοφέρνου')['Lemma'], '')

    def test_mixed_latin_source_error_is_not_transliterated_as_a_name(self):
        lexicon = dc.Lexicon()
        lexicon.add_name('Τωβiηλ', 'Τωβiηλ', 'bad source fixture')
        self.assertEqual(lexicon.lookup('Τωβiηλ')['GlossStatus'], 'missing')

    def test_movable_nu_requires_supported_morphology(self):
        lexicon = dc.Lexicon()
        lexicon.add('ἐποίησεν', dc.Candidate('ποιέω', 'to do/make', 'test', 'V-AAI-3S'), form=True)
        lexicon.add('πᾶσιν', dc.Candidate('πᾶς', 'all', 'test', 'A-DPM'), form=True)
        lexicon.add('μέν', dc.Candidate('μέν', 'indeed', 'test', 'PRT'), form=True)
        self.assertEqual(lexicon.lookup('ἐποίησε')['OETGlossWords'], 'to do/make')
        self.assertEqual(lexicon.lookup('πᾶσι')['GlossStatus'], 'movable-nu-candidate')
        self.assertEqual(lexicon.lookup('μέ')['GlossStatus'], 'missing')

    def test_compound_analysis_can_use_whole_word_headword_gloss(self):
        lexicon = dc.Lexicon()
        lexicon.add('μήποτε', dc.Candidate('μή', 'lest + πότε=when', 'compound'), form=True)
        lexicon.add('μήποτε', dc.Candidate('μήποτε', 'lest', 'headword'))
        result = lexicon.lookup('μήποτε')
        self.assertEqual(result['OETGlossWords'], 'lest')
        self.assertEqual(result['GlossStatus'], 'headword-fallback-candidate')
        self.assertEqual(len(json.loads(result['Candidates'])), 2)

    def test_draft_review_includes_filled_alternatives_and_names(self):
        rows = [dict(Ref='TOB_1:1w1', GreekWord='Τωβιὴλ', OETGlossWords='Tōbiaʸl', GlossStatus='name-transliteration'),
                dict(Ref='TOB_1:1w2', GreekWord='Η', OETGlossWords='or/the', GlossStatus='draft-alternatives'),
                dict(Ref='TOB_1:1w3', GreekWord='ἄγνωστον', OETGlossWords='', GlossStatus='missing')]
        self.assertEqual([r['GreekWord'] for r in dc.draft_review(rows)], ['Τωβιὴλ', 'Η'])

    def test_missing_word_remains_visible_and_linked(self):
        row = dict(OETGlossWords='', GreekWord='ἄγνωστον', Before='', After=';')
        self.assertEqual(dc.render_word(row, 12), '⟦ἄγνωστον¦12⟧?')

    def test_compound_tagnt_analysis_is_not_an_english_gloss(self):
        lexicon = dc.Lexicon()
        lexicon.add('τίνα', dc.Candidate('ἵνα', 'in order that/to + τίς=which?', 'test'), form=True)
        self.assertEqual(lexicon.lookup('τίνα')['GlossStatus'], 'unusable-gloss')
        self.assertEqual(lexicon.lookup('τίνα')['OETGlossWords'], '')

    def test_lexical_punctuation_follows_word_link(self):
        row = dict(OETGlossWords='look!', GreekWord='ἰδού', Before='', After=' ')
        self.assertEqual(dc.render_word(row, 6), 'look¦6! ')

    def test_multiword_gloss_repeats_the_correct_link(self):
        row = dict(OETGlossWords='to be', GreekWord='εἰμί', Before='', After='·')
        self.assertEqual(dc.render_word(row, 9), 'to¦9_be¦9;')


class SweteTests(unittest.TestCase):
    def fixture(self):
        chapters = ''.join(f'<div subtype="chapter" n="{n}"><head>Title</head>'
                           '<l>Superscription</l><div subtype="verse" n="1">'
                           '<l>λόγος<note>not scripture</note> θεός</l>'
                           '<l>καί.</l></div></div>' for n in range(1, 19))
        return ('<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body>'
                '<div n="urn:cts:greekLit:tlg0527.tlg035.1st1K-grc1">'
                + chapters + '</div></body></text></TEI>')

    def test_verse_extraction_excludes_notes_and_keeps_line_boundaries(self):
        node = ET.fromstring('<div xmlns="http://www.tei-c.org/ns/1.0">'
                             '<l>ἔστιν <note>variant <note>nested</note></note>θεός</l>'
                             '<pb n="5"/><l>καὶ<lb/> λόγος.</l></div>')
        self.assertEqual(dc.tei_text(node), 'ἔστιν θεός καὶ λόγος.')

    def test_unknown_verse_markup_fails_instead_of_omitting_words(self):
        node = ET.fromstring('<div xmlns="http://www.tei-c.org/ns/1.0"><app>λόγος</app></div>')
        with self.assertRaisesRegex(ValueError, 'Unsupported TEI'):
            dc.tei_text(node)

    def test_pss_parser_keeps_references_and_excludes_superscriptions(self):
        filename = dc.TEI_SOURCES['PSS'][0]
        verses = dc.parse_swete_tei(self.fixture(), 'PSS', filename)
        self.assertEqual(len(verses), 18)
        self.assertEqual(verses[-1], dc.Verse('PSS', 18, '1', 'λόγος θεός καί.', 'PSS_18:1', filename))

    def test_wrong_edition_missing_chapter_and_unmarked_text_fail(self):
        text = self.fixture()
        for damaged in [text.replace('tlg035', 'tlg028'),
                        text.replace('chapter" n="18', 'chapter" n="19'),
                        text.replace('</head>', '</head>lost text', 1),
                        text.replace('<l>καί.</l></div>', '<l>καί.</l></div><l>lost text</l>', 1)]:
            with self.subTest(text=damaged[:100]), self.assertRaises(ValueError):
                dc.parse_swete_tei(damaged, 'PSS', dc.TEI_SOURCES['PSS'][0])

    def test_duplicate_verse_fails(self):
        text = self.fixture().replace('<l>καί.</l></div>',
                '<l>καί.</l></div><div subtype="verse" n="1"><l>θεός</l></div>', 1)
        with self.assertRaisesRegex(ValueError, 'Duplicate TEI verse'):
            dc.parse_swete_tei(text, 'PSS', dc.TEI_SOURCES['PSS'][0])

    def test_visible_ocr_error_is_preserved_and_flagged(self):
        verses = {'PSS': [dc.Verse('PSS', 1, '1', 'ΕBOΗΣA θεός', 'PSS_1:1', 'fixture.xml')]}
        rows = dc.make_rows(verses, dc.Lexicon(), {})
        self.assertEqual(rows[0]['GreekWord'], 'ΕBOΗΣA')
        review = dc.source_review(rows)
        self.assertEqual(len(review), 1)
        self.assertEqual(review[0]['Ref'], 'PSS_1:1w1')
        self.assertIn('ΕBOΗΣA¦1', dc.render_word(rows[0], 1))


class OverrideTests(unittest.TestCase):
    def setUp(self):
        self.lexicon = dc.Lexicon()
        self.lexicon.add('λόγος', dc.Candidate('λόγος', 'word', 'test'))
        self.verses = {'TOB': [dc.Verse('TOB', 1, '1', 'λόγος λόγος', 'TOB_1:1', 'fixture')]}

    def test_occurrence_override_takes_precedence_over_form(self):
        overrides = {('*', dc.normalise('λόγος')): {'Gloss': 'message', 'Note': 'form'},
                     ('TOB_1:1w2', 'λόγος'): {'Gloss': 'account', 'Note': 'context'}}
        rows = dc.make_rows(self.verses, self.lexicon, overrides)
        self.assertEqual([r['OETGlossWords'] for r in rows], ['message', 'account'])
        self.assertEqual(rows[1]['LexiconGloss'], 'word')

    def test_changed_source_word_or_ref_is_a_stale_override(self):
        for key in [('TOB_1:1w2', 'θεός'), ('TOB_1:2w1', 'λόγος')]:
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'stale overrides'):
                dc.make_rows(self.verses, self.lexicon, {key: {'Gloss': 'account', 'Note': 'context'}})

    def test_override_rejects_esfm_injection_and_duplicate_rows(self):
        header = 'Ref\tGreekWord\tGloss\tNote\n'
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'overrides.tsv'
            for body in ['*\tλόγος\tword¦999\tbad\n',
                         '*\tλόγος\tword\tnote\n*\tλόγος\tmessage\tnote\n']:
                path.write_text(header + body)
                with self.subTest(body=body), self.assertRaises(ValueError):
                    dc.read_overrides(path)


class CachedSourceTests(unittest.TestCase):
    @unittest.skipUnless(HAVE_SOURCES, 'downloaded lexical source integration check')
    def test_real_names_and_article_default(self):
        lexicon = dc.Lexicon.load(dc.CACHE)
        verses = {'TOB': [dc.Verse('TOB', 1, '1', 'Τωβὶτ τοῦ Τωβιὴλ Νινευή', 'TOB_1:1', 'fixture')]}
        article_override = {k: v for k, v in dc.read_overrides(dc.OVERRIDES).items() if k[1] == dc.normalise('τοῦ')}
        rows = dc.make_rows(verses, lexicon, article_override)
        self.assertEqual([r['OETGlossWords'] for r in rows], ['Tōbit', 'of_the', 'Tōbiaʸl', 'Nineuaʸ'])
        self.assertEqual(rows[1]['GlossStatus'], 'editorial')
        self.assertGreater(len(json.loads(rows[1]['Candidates'])), 1)
        self.assertEqual(dc.render_word(rows[1], 4), 'of¦4_the¦4 ')
        for word in ['Ναβουχοδονόσορ', 'Ἐσθὴρ', 'Μαρδοχαῖος', 'Ἰουδὶθ']:
            self.assertTrue(lexicon.lookup(word)['GlossStatus'].startswith('name-transliteration'), word)
        for word, gloss in [('ὡς', 'which/how'), ('Ὡς', 'which/how'), ('στέφανον', 'crown')]:
            self.assertEqual(lexicon.lookup(word)['OETGlossWords'], gloss)

    @unittest.skipUnless(HAVE_SOURCES, 'downloaded source integration check')
    def test_real_book_assembly_and_sirach_prologue(self):
        dc.sources(dc.load_manifest(dc.MANIFEST), dc.CACHE)
        verses = dc.load_verses(dc.CACHE)
        self.assertEqual(set(verses), set(dc.BOOKS))
        self.assertNotIn('ES2', verses)
        baruch6 = [v for v in verses['BAR'] if v.chapter == 6]
        self.assertEqual(len(baruch6), 73)
        self.assertEqual(baruch6[0].source_ref, 'LJE_1:1')
        self.assertEqual({v.chapter for v in verses['DAG']}, set(range(1, 15)))
        self.assertEqual(verses['PS2'][0].source_ref, 'PSA_151:1')
        self.assertEqual(len(verses['PS2']), 7)
        prologue = [v for v in verses['SIR'] if v.chapter == 0]
        self.assertEqual(len(prologue), 8)
        first = next(v for v in verses['SIR'] if v.chapter == 1 and v.verse == '1')
        self.assertEqual(first.source_ref, 'SIR_1:1h')
        self.assertTrue(first.text.startswith('ΠΑΣΑ σοφία'))

    @unittest.skipUnless(HAVE_SOURCES, 'downloaded Swete source integration check')
    def test_swete_chapters_word_counts_and_unusual_references(self):
        verses = dc.load_verses(dc.CACHE)
        self.assertEqual(list(verses)[-2:], ['PSS', 'ODE'])
        self.assertEqual({v.chapter for v in verses['PSS']}, set(range(1, 19)))
        self.assertEqual({v.chapter for v in verses['ODE']}, set(range(1, 15)))
        self.assertEqual(len(verses['PSS']), 332)
        self.assertEqual(len(verses['ODE']), 275)
        for book, count in [('PSS', 4830), ('ODE', 4159)]:
            self.assertEqual(sum(len(list(dc.tokenise(v.text))) for v in verses[book]), count)
        fourth = [v for v in verses['ODE'] if v.chapter == 4]
        self.assertEqual([v.verse for v in fourth],
                         [f'{n}a' for n in range(1, 10)] + [f'{n}b' for n in range(9, 21)])
        self.assertEqual(fourth[8].source_ref, 'ODE_iva:9')
        self.assertEqual(fourth[9].source_ref, 'ODE_ivb:9')
        last = [v for v in verses['ODE'] if v.chapter == 14]
        self.assertEqual(len(last), 47)
        self.assertEqual(last[0].text, 'Δόξα ἐν ὑψίστοις θεῷ,')
        self.assertEqual(last[-1].source_ref, 'ODE_14:xml-line47')
        self.assertEqual(last[-1].text, 'παράτεινον τὸ ἔλεός σου τοῖς γινώσκουσίν σε.')
        tenth = [v.verse for v in verses['ODE'] if v.chapter == 10]
        self.assertEqual(tenth[17:23], ['68', '71', '72', '69', '70', '73'])

    @unittest.skipUnless(HAVE_SOURCES, 'downloaded Swete source integration check')
    def test_ode_xiv_cannot_be_silently_truncated(self):
        filename = dc.TEI_SOURCES['ODE'][0]
        text = (dc.CACHE / filename).read_text(encoding='utf-8')
        for damaged in [text.replace('<l>παράτεινον τὸ ἔλεός σου τοῖς γινώσκουσίν σε.</l>', ''),
                        text.replace('<lb n="45"/>', '<lb n="44"/>')]:
            self.assertNotEqual(text, damaged)
            with self.assertRaisesRegex(ValueError, 'Ode XIV'):
                dc.parse_swete_tei(damaged, 'ODE', filename)

    def test_unchanged_writes_preserve_mtime(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'file.txt'
            dc.write_if_changed(path, 'original')
            before = path.stat().st_mtime_ns
            dc.write_if_changed(path, 'original')
            self.assertEqual(path.stat().st_mtime_ns, before)


if __name__ == '__main__':
    unittest.main()
