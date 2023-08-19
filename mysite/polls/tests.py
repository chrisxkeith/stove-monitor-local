from django.test import TestCase
from datetime import datetime

from polls.views import app

class TestLightSensor(TestCase):
    def do_test(self, data, expected):
        app.lightSensor.handle_call_back(data)
        ret = app.handleRequest()
        # print(ret.content)
        for e in expected:
            self.assertContains(ret, e)

    def test_elapsed_time(self):
        self.do_test({
            "data" : "false",
            "ttl" : 1,
            "published_at" : "2023-07-17T16:38:01.560Z",
            "coreid" : "1c002c001147343438323536",
            "event_name" : "Light sensor",
        }, [ "Off" ])
        self.do_test({
            "data" : "true",
            "ttl" : 1,
            "published_at" : "2023-07-17T16:39:01.560Z",
            "coreid" : "1c002c001147343438323536",
            "event_name" : "Light sensor",
        }, [ "On" ])
        self.do_test({
            "data" : "true",
            "ttl" : 1,
            "published_at" : "2023-07-17T17:39:01.560Z",
            "coreid" : "1c002c001147343438323536",
            "event_name" : "Light sensor",
        }, [ "Tomato" ])
        now = datetime.now()
        more_than_an_hour_ago = datetime.fromtimestamp(now.timestamp() - (60 * 65))
        self.do_test({
            "data" : "false",
            "ttl" : 1,
            "published_at" : more_than_an_hour_ago.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "coreid" : "1c002c001147343438323536",
            "event_name" : "Light sensor",
        }, [ "Off" ])
        hour_ago = datetime.fromtimestamp(now.timestamp() - (60 * 60))
        self.do_test({
            "data" : "true",
            "ttl" : 1,
            "published_at" : hour_ago.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "coreid" : "1c002c001147343438323536",
            "event_name" : "Light sensor",
        }, [ "On" ]) # "00:00"

