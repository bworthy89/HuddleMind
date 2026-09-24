"""Synthetic ratings tests: packed reads, backward compatibility, storage and transport."""
from dataclasses import replace
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from bridge.player_ratings import read_ratings, RATING_FIELDS
from bridge.discover_fields import packed_value
from bridge.models import PlayerRating
from bridge.snapshot_adapter import player_from_report
from bridge.test_receive_api import valid_event
from bridge.validate_event import decode_event
from bridge.test_dynasty_details import sample
from bridge.local_store import initialize_database, create_dynasty, save_observation, get_observation
from bridge.sync_event import build_observation_event, serialize_observation_event


class RatingsTests(unittest.TestCase):
    def test_reads_packed_zero_and_upper_bound_and_preserves_missing(self):
        fields = {'SpeedRating': {'type':'int','minValue':'0','maxValue':'127','offset':0,'width':7},
                  'StrengthRating': {'type':'int','minValue':'0','maxValue':'127','offset':7,'width':7}}
        result = read_ratings((127 << 18).to_bytes(4, 'big'), {'count':1,'records':0,'words':1}, fields, 0, packed_value)
        self.assertEqual(result['SpeedRating'], 0)
        self.assertEqual(result['StrengthRating'], 127)
        self.assertIsNone(result['AccelerationRating'])
        self.assertEqual(len(result), len(RATING_FIELDS))

    def test_schema_drift_and_invalid_values_fail(self):
        field={'type':'int','minValue':'0','maxValue':'127'}
        for changed in ({**field,'type':'bool'}, {**field,'maxValue':'99'}):
            with self.assertRaises(ValueError):
                read_ratings(b'', {}, {'SpeedRating':changed}, 0, lambda *args: 1)
        for value in (-1,128,True):
            with self.assertRaises(ValueError):
                read_ratings(b'', {}, {'SpeedRating':field}, 0, lambda *args: value)

    def test_adapter_supports_old_reports_and_new_ratings(self):
        record=dict(table=1,row=0,FirstName='Sample',LastName='Player',PositionLabel='QB',OverallRating=80)
        self.assertEqual(player_from_report(record).ratings, ())
        self.assertEqual(player_from_report({**record,'Ratings':{'SpeedRating':0,'StrengthRating':None}}).ratings,
                         (PlayerRating('SpeedRating',0),PlayerRating('StrengthRating',None)))
        with self.assertRaises(ValueError):
            player_from_report({**record,'Ratings':{'SpeedRating':True}})

    def test_receiver_accepts_old_and_new_without_mutating_payload(self):
        event=valid_event()
        player=event['payload']['roster']['team']['players'][0]
        player.pop('ratings',None)
        self.assertNotIn('ratings',decode_event(json.dumps(event).encode())['payload']['roster']['team']['players'][0])
        player['ratings']=[{'field':'SpeedRating','value':0},{'field':'StrengthRating','value':None}]
        self.assertEqual(decode_event(json.dumps(event).encode())['payload']['roster']['team']['players'][0]['ratings'],player['ratings'])
        for ratings in ([{'field':'OtherRating','value':1}], [{'field':'SpeedRating','value':128}],
                        [{'field':'SpeedRating','value':True}], [{'field':'SpeedRating','value':0}]*2):
            player['ratings']=ratings
            with self.assertRaises(ValueError):decode_event(json.dumps(event).encode())

    def test_storage_export_and_event_keep_ratings_and_original_observation(self):
        details=sample()
        details=replace(details,roster=replace(details.roster,save_sha256='a'*64,schema_sha256='b'*64))
        player=replace(details.roster.team.players[0],ratings=(PlayerRating('SpeedRating',91),))
        enriched=replace(details,roster=replace(details.roster,team=replace(details.roster.team,players=(player,))))
        with TemporaryDirectory() as folder:
            db=Path(folder)/'history.sqlite3';initialize_database(db);dynasty=create_dynasty(db,'Test')
            first=save_observation(db,dynasty,enriched)
            stored=get_observation(db,dynasty,first)
            decoded=decode_event(serialize_observation_event(build_observation_event(db,dynasty,first)).encode())
            self.assertEqual(decoded['payload'],stored)
            self.assertEqual(stored['roster']['team']['players'][0]['ratings'][0]['value'],91)
            self.assertEqual(save_observation(db,dynasty,details),first)
            self.assertEqual(get_observation(db,dynasty,first),stored)
