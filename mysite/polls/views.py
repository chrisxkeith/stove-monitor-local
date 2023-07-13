from django.shortcuts import render

from django.http import HttpResponse

from string import Template

from pyparticleio.ParticleCloud import ParticleCloud
from dotenv import load_dotenv
import os
from datetime import datetime
from zoneinfo import ZoneInfo

class Sensor:
    latest_event = None

    def __init__(self, particleCloud, deviceName, eventName):
        device = [d for d in particleCloud.devices_list if d.name == deviceName][0]
        device.subscribe(eventName, self.handle_call_back)
        try:
            device.getData("")
        except Exception as e:
            print(repr(e) + ", deviceName: " + deviceName + ", eventName: " + eventName)

    def handle_call_back(self, event_data):
        self.latest_event = event_data

class TemperatureSensor(Sensor):
    latest_temperature_event = None

    def handle_call_back(self, event_data):
        super().handle_call_back(event_data)
        if self.latest_event["event_name"] == "Temperature":
            self.latest_temperature_event = event_data

    def getDisplayVals(self):
        temperature = "No data yet"
        if (self.latest_temperature_event):
            temperature = str(self.latest_event["data"])
        return temperature

class LightSensor(Sensor):
    latest_on_event = None

    def handle_call_back(self, event_data):
        super().handle_call_back(event_data)
        if self.latest_on_event is None and event_data["data"] == "true":
            self.latest_on_event = self.latest_event
        if event_data["data"] == "false":
            self.latest_on_event = None

    def getDisplayVals(self):
        status = "Off"
        on_time = ""
        elapsed_time = ""
        if (self.latest_event):
            if self.latest_event["data"] == 'true':
                status = "On"
        else:
            status = "No data yet"
        if self.latest_on_event:
            [ on_time, elapsed_time ] = getTimeVals(datetime.strptime(self.latest_on_event["published_at"], "%Y-%m-%dT%H:%M:%S.%f%z"))
            elapsed_time += " elapsed"
        return [ status, on_time, elapsed_time ]
    
env_file_err = None
if os.path.exists("./.env"):
    load_dotenv("./.env")
    particleCloud = ParticleCloud(username_or_access_token=os.getenv("ACCESS_TOKEN"))
    lightSensor = LightSensor(particleCloud, "photon-07", "Light sensor")
    temperatureSensor = TemperatureSensor(particleCloud, "photon-05", "Temperature")
else:
    env_file_err = "No file: ./.env"

def getTimeString(theDateTime):
    return theDateTime.astimezone(ZoneInfo('US/Pacific')).strftime('%I:%M %p')

def getElapsedTime(pastTime):
    now = datetime.now(ZoneInfo('US/Pacific'))
    elapsedSeconds = now - pastTime
    mins = int(elapsedSeconds.total_seconds() / 60)
    secs = int(elapsedSeconds.total_seconds() % 60)
    return "{:0>2}:{:0>2}".format(mins, secs)

def getTimeVals(ts):
    on_time = getTimeString(ts)
    elapsed_time = getElapsedTime(ts)
    return [ on_time, elapsed_time]

latest_event = "No data yet"
on_time = ""
elapsed_time = ""
temperature = "No data yet"

if env_file_err:
    status = env_file_err
else:
    [ status, on_time, elapsed_time ] = lightSensor.getDisplayVals()
    temperature = temperatureSensor.getDisplayVals()

def index(request):
    thePage = Template("    <style>" + \
    "  h1 { text-align: center; }" + \
    "  h3 { text-align: center; }" + \
    "</style>" + \
    "<h3>" + \
    "    Burner indicator light<br>" + \
    "    <i><big><big>" + \
    "        $latest_event" + \
    "        <br>" + \
    "        $on_time" + \
    "        <br>" + \
    "        $elapsed_time" + \
    "    </big></big></i>" + \
    "</h3>" + \
    "<h3>" + \
    "    Stovetop average temperature<br>" + \
    "    <i><big><big>" + \
    "        $temperature" + \
    "    </big></big></i>" + \
    "</h3>")
    return HttpResponse(thePage.substitute(latest_event = latest_event, on_time = on_time, 
                                           elapsed_time = elapsed_time, temperature = temperature))
