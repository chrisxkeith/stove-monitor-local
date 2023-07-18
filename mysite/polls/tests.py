from django.test import TestCase

from polls.views import App

class TestLightSensor(TestCase):
    def test_elapsed_time(self):
        data1 = {
            "data" : "false",
            "ttl" : 1,
            "published_at" : "2023-07-17T16:38:01.560Z",
            "coreid" : "fake_core_id",
            "event_name" : "Light sensor",
        }
