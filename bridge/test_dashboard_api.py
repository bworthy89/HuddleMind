from copy import deepcopy
from io import BytesIO
import json
from pathlib import Path
import tempfile
import unittest
from uuid import uuid4
from bridge.hosted_receiver import create_app
from bridge.receiver_store import store_event
from bridge.test_receive_api import valid_event


class DashboardTests(unittest.TestCase):
    def setUp(self):
        folder=tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.path=Path(folder.name)/'receiver.sqlite3'
        self.event=valid_event()
        self.upload='u'*40
        self.read='r'*40
        self.app=create_app(self.path,self.upload,'owner',[self.event['dynasty_id']],read_token=self.read)

    def request(self, token, route='/v1/dashboard', method='GET'):
        env=dict(PATH_INFO=route,REQUEST_METHOD=method,HTTP_AUTHORIZATION='Bearer '+token)
        env['wsgi.input']=BytesIO()
        result=[]
        body=b''.join(self.app(env,lambda status,headers:result.append(status)))
        return int(result[0].split()[0]),json.loads(body)

    def test_read_upload_credentials_are_not_interchangeable(self):
        self.assertEqual(self.request(self.upload)[0],401)
        self.assertEqual(self.request(self.read,'/v1/observations','POST')[0],401)
        self.assertEqual(self.request(self.read,method='POST')[0],405)
        self.assertEqual(self.request('')[0],401)

    def test_latest_capture_wins_over_late_arrival_and_other_owners(self):
        newer=deepcopy(self.event);newer['observed_at']='2026-09-23T20:00:00+00:00'
        store_event(self.path,'owner',newer)
        older=deepcopy(newer);older['event_id']=str(uuid4());older['observed_at']='2026-09-22T20:00:00+00:00'
        store_event(self.path,'owner',older)
        other=deepcopy(newer);other['event_id']=str(uuid4());other['observed_at']='2026-09-24T20:00:00+00:00'
        store_event(self.path,'other-owner',other)
        forbidden=deepcopy(other);forbidden['dynasty_id']=str(uuid4())
        store_event(self.path,'owner',forbidden)
        status,data=self.request(self.read)
        self.assertEqual(status,200)
        self.assertEqual(len(data['dynasties']),1)
        self.assertEqual(data['dynasties'][0]['snapshot']['event_id'],newer['event_id'])

    def test_empty_dynasty_is_explicit(self):
        self.assertIsNone(self.request(self.read)[1]['dynasties'][0]['snapshot'])

    def test_read_token_cannot_equal_upload_token(self):
        with self.assertRaises(ValueError):
            create_app(self.path,self.upload,'owner',[self.event['dynasty_id']],read_token=self.upload)
