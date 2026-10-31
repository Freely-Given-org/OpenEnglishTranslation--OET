# SPDX-License-Identifier: MPL-2.0
"""2026-10-21: BOS passage metadata tagging without rewriting native word identifiers.

From scripts: uv run python -m unittest discover -s tests -p test_nt_theographic_mapping.py
"""
from copy import deepcopy
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import add_tags_to_NT_word_table as tagging


def entry(**values):
    return dict(people=[],places=[],peopleGroups=[],eventsDescribed=[],yearNum='',timeline='') | values


def row(reference, gloss='peace', probability='1'):
    return '\t'.join((reference,'Greek','lemma','lemma',gloss,gloss,'U',probability,'G1','N','morphology',''))


class TheographicMappingTests(unittest.TestCase):
    def setUp(self):
        self.index = {
            'JN3_1:14':entry(yearNum='90'),
            'REV_13:1':entry(yearNum='96'),
            'ACT_19:40':entry(people=['PPaul'],places=['LEphesus'],yearNum='58',timeline='First event',eventsDescribed=['Riot']),
            'ACT_19:41':entry(people=['PPaul'],places=['LEphesus'],yearNum='59',timeline='Second event',eventsDescribed=['Riot','Dismissal']),
            'CO2_13:12':entry(yearNum='60'), 'CO2_13:13':entry(yearNum='60'),
            'CO2_13:14':entry(people=['PJesus'],yearNum='61'),
            'PHP_1:16':entry(people=['PJesus']), 'PHP_1:17':entry(),
        }
        self.originalIndex = deepcopy(self.index)

    def test_split_source_uses_the_complete_target_verse(self):
        for verse,year in (('JN3_1:14','90'),('JN3_1:15','90'),('REV_12:18','96'),('REV_13:1','96')):
            with self.subTest(verse=verse):
                self.assertEqual(tagging.get_Theographic_verse_metadata(verse,self.index)['yearNums'],[year])
        self.assertEqual(self.index,self.originalIndex)

    def test_combined_source_keeps_distinct_metadata_and_removes_duplicates(self):
        data = tagging.get_Theographic_verse_metadata('ACT_19:40',self.index)
        self.assertEqual(data,dict(people=['PPaul'],places=['LEphesus'],peopleGroups=[],
            eventsDescribed=['Riot','Dismissal'],yearNums=['58','59'],timelines=['First event','Second event']))

    def test_blessing_uses_14_even_though_same_number_13_exists(self):
        self.assertEqual(tagging.get_Theographic_verse_metadata('CO2_13:13',self.index)['people'],['PJesus'])
        self.assertEqual(tagging.get_Theographic_verse_metadata('CO2_13:12',self.index)['yearNums'],['60'])

    def test_source_profile_preserves_vlt_philippians_order(self):
        self.assertEqual(tagging.get_Theographic_verse_metadata('PHP_1:16',self.index)['people'],['PJesus'])
        self.assertEqual(tagging.get_Theographic_verse_metadata('PHP_1:17',self.index)['people'],[])

    def test_missing_mapped_key_does_not_use_existing_wrong_key(self):
        del self.index['CO2_13:14']
        with self.assertRaisesRegex(ValueError,'VLT.*CO2_13:13.*KJV.*CO2_13:14.*Theographic'):
            tagging.get_Theographic_verse_metadata('CO2_13:13',self.index)

    def test_unsupported_mapping_fails_with_profile_and_native_reference(self):
        with patch.object(tagging,'WORD_TABLE_VERSIFICATION','Original'):
            with self.assertRaisesRegex(ValueError,'Original.*JN3_1:15.*KJV.*unsupported'):
                tagging.get_Theographic_verse_metadata('JN3_1:15',self.index)

    def test_association_preserves_rows_word_ids_and_every_other_column(self):
        rows = [row('JN3_1:15w1'),row('JN3_1:15w2'),row('REV_12:18w1'),
                row('ACT_19:40w1','Paul'),row('CO2_13:13w1','Jesus'),row('JN3_1:15w3',probability='')]
        state = SimpleNamespace(newTable=['header',*rows],verseIndex=self.index)
        with patch.object(tagging,'state',state), \
             patch.object(tagging,'EXPECTED_WORD_TABLE_DATA_ROW_COUNT',len(rows)), \
             patch.object(tagging.BibleOrgSysGlobals,'verbosityLevel',0), \
             patch.object(tagging,'get_Theographic_verse_metadata',wraps=tagging.get_Theographic_verse_metadata) as lookup:
            self.assertTrue(tagging.associate_Theographic_people_places())
            self.assertEqual(lookup.call_count,4)
        self.assertEqual(len(state.newTable),len(rows)+1)
        for before,after in zip(rows,state.newTable[1:]):
            self.assertEqual(before.split('\t')[:-1],after.split('\t')[:-1])
            tags = after.split('\t')[-1].split(';')
            self.assertEqual(len(tags),len(set(tags)))
        self.assertTrue(state.newTable[1].endswith('\tY90'))
        self.assertTrue(state.newTable[3].endswith('\tY96'))
        self.assertIn('PPaul;Y58;Y59;ERiot;EDismissal;TFirst_event;TSecond_event',state.newTable[4])
        self.assertTrue(state.newTable[5].endswith('\tPJesus;Y61'))
        self.assertTrue(state.newTable[6].endswith('\t')) # Unused variant still has no date tags.
        self.assertEqual(self.index,self.originalIndex)


if __name__ == '__main__':
    unittest.main()
