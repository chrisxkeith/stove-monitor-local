from django.test import TestCase

from polls.views import app

class TestLightSensor(TestCase):
    def do_test(self, data, expected):
        app.lightSensor.handle_call_back(data)
        ret = app.handleRequest()
        self.assertContains(ret, expected)

    def test_elapsed_time(self):
        self.do_test({
            "data" : "false",
            "ttl" : 1,
            "published_at" : "2023-07-17T16:38:01.560Z",
            "coreid" : "1c002c001147343438323536",
            "event_name" : "Light sensor",
        }, "Off")
        self.do_test({
            "data" : "true",
            "ttl" : 1,
            "published_at" : "2023-07-17T16:39:01.560Z",
            "coreid" : "1c002c001147343438323536",
            "event_name" : "Light sensor",
        }, "On")
        self.do_test({
            "data" : "true",
            "ttl" : 1,
            "published_at" : "2023-07-17T17:39:01.560Z",
            "coreid" : "1c002c001147343438323536",
            "event_name" : "Light sensor",
        }, "Tomato")
