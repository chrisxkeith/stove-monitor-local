from django.test import TestCase

from polls.views import index, history, LightEventHandler

class TestLightSensor(TestCase):
    def test_elapsed_time(self):
        lightEventHandler = LightEventHandler()
        data1 = {
            "data" : "false",
            "ttl" : 1,
            "published_at" : "2023-07-17T16:38:01.560Z",
            "coreid" : "fake_core_id",
            "event_name" : "Light sensor",
        }
        lightEventHandler.handle_call_back(data1)
        # ret = index(None)
        # print(ret._container)
        ret = history(None)
        print(str(ret._container).replace("<br>", "\n"))
