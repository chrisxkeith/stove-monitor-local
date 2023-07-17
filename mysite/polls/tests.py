from django.test import TestCase
from pyparticleio.ParticleCloud import ParticleCloud, _ParticleDevice
from unittest.mock import MagicMock
from dotenv import load_dotenv
import os

from polls.views import index, history, LightSensor, lightSensor

class TestLightSensor(TestCase):
    def test_elapsed_time(self):
        mockDevice = _ParticleDevice()
        mockDevice.name = "photon-07"
        
        load_dotenv("./.env")
        mockCloud = ParticleCloud(username_or_access_token=os.getenv("ACCESS_TOKEN"))
        lightSensor = LightSensor(mockCloud, mockDevice.name, "Light sensor")
        data1 = {
            "data" : "false",
            "ttl" : 1,
            "published_at" : "2023-07-17T16:38:01.560Z",
            "coreid" : "fake_core_id",
            "event_name" : "Light sensor",
        }
        lightSensor.handle_call_back(data1)
        ret = index(None)
        print(ret._container)
        ret = history(None)
        print(ret._container)