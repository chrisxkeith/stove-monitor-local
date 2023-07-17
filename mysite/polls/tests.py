from django.test import TestCase
from pyparticleio.ParticleCloud import ParticleCloud, _ParticleDevice
from unittest.mock import MagicMock
from dotenv import load_dotenv
import os

from polls.views import index, LightSensor

class TestLightSensor(TestCase):
    def test_elapsed_time(self):
        mockDevice = _ParticleDevice()
        mockDevice.name = "FakePhoton"
        
        load_dotenv("./.env")
        mockCloud = ParticleCloud(username_or_access_token=os.getenv("ACCESS_TOKEN"))
        mockCloud._get_devices = MagicMock(
            return_value = [
                mockDevice
            ]
        )

        lightSensor = LightSensor(mockCloud, "FakePhoton", 'Light sensor')
        data1 = type('', (object,), {
            "data": 'false',
            "ttl" : 1,
            "published_at": '2023-07-17T16:38:01.560Z',
            "coreid" : '32002e000e47363433353735',
            "event_name": 'Light sensor',
        })()
        lightSensor.handle_call_back(data1)
        ret = index(None)
        print(ret._container)