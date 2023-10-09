from django.test import TestCase
from datetime import datetime
from zoneinfo import ZoneInfo

from polls.views import app

class TestLightSensor(TestCase):
    def do_test(self, data, expected):
        app.lightSensor.handle_call_back(data)
        ret = app.handleRequest()
        for e in expected:
            if (not e in str(ret.content)):
                 print(ret.content)
            self.assertContains(ret, e)

    def test_elapsed_time(self):
        now = datetime.now()
        more_than_an_hour_ago = datetime.fromtimestamp(now.timestamp() - (60 * 65)).astimezone(ZoneInfo("UTC"))
        self.do_test({
            "data" : "{\"on\":\"false\",\"whenSwitchedToOn\":\"\"}",
            "ttl" : 1,
            "published_at" : more_than_an_hour_ago.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "coreid" : "1c002c001147343438323536",
            "event_name" : "Light sensor",
        }, [ "Off" ])
        app.temperatureSensor.handle_call_back({
            "data" : "99",
            "ttl" : 1,
            "published_at" : more_than_an_hour_ago.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "coreid" : "1c002c001147343438323536",
            "event_name" : "Temperature",
        })
        hour_ago = datetime.fromtimestamp(now.timestamp() - (60 * 60)).astimezone(ZoneInfo("US/Pacific"))
        self.do_test({
            "data" : "{\"on\":\"true\",\"whenSwitchedToOn\":\""
                        + hour_ago.strftime("%Y-%m-%dT%H:%M:%S") 
                        + "\"}",
            "ttl" : 1,
            "published_at" : more_than_an_hour_ago.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "coreid" : "1c002c001147343438323536",
            "event_name" : "Light sensor",
        }, [ "On", "Tomato", "60:00" ])
