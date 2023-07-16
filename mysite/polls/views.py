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
            [ on_time, elapsed_time ] = self.getTimeVals(
                    datetime.strptime(self.latest_on_event["published_at"],
                                      "%Y-%m-%dT%H:%M:%S.%f%z"))
            elapsed_time += " elapsed"
        return [ status, on_time, elapsed_time ]

    def getTimeVals(self, ts):
        on_time = self.getTimeString(ts)
        elapsed_time = self.getElapsedTime(ts)
        return [ on_time, elapsed_time ]

    def getTimeString(self, theDateTime):
        return theDateTime.astimezone(ZoneInfo('US/Pacific')).strftime('%I:%M %p')

    def getElapsedSeconds(self):
        if self.latest_on_event:
            return self.getElapsedSeconds(
                datetime.strptime(self.latest_on_event["published_at"],
                                  "%Y-%m-%dT%H:%M:%S.%f%z"))
        return -1

    def getElapsedTime(self, pastTime):
        elapsedSeconds = self.getElapsedSeconds(pastTime)
        mins = int(elapsedSeconds.total_seconds() / 60)
        secs = int(elapsedSeconds.total_seconds() % 60)
        return "{:0>2}:{:0>2}".format(mins, secs)

env_file_err = None
if os.path.exists("./.env"):
    load_dotenv("./.env")
    particleCloud = ParticleCloud(username_or_access_token=os.getenv("ACCESS_TOKEN"))
    lightSensor = LightSensor(particleCloud, "photon-07", "Light sensor")
    temperatureSensor = TemperatureSensor(particleCloud, "photon-05", "Temperature")
else:
    env_file_err = "Error: No file: ./.env"


def index(request):
    latest_event = "No data yet"
    on_time = ""
    elapsed_time = ""
    temperature = "No data yet"
    timeNow = ""
    red_h3tag1 = ""
    red_h3Tag2 = ""

    if env_file_err:
        status = env_file_err
    else:
        [ status, on_time, elapsed_time ] = lightSensor.getDisplayVals()
        temperature = temperatureSensor.getDisplayVals()
        now = datetime.now(ZoneInfo('US/Pacific'))
        timeNow = now.strftime("%a %d %b %Y, %I:%M%p")
        if lightSensor.getElapsedSeconds() > 45 * 60:
            red_h3tag1 = "<h3 style=\"background-color: Tomato;\">"
            red_h3Tag2 = "<h3>"

    thePage = Template("<html lang=\"en\">" + \
    "  <head>" + \
    "    <title>Stove Monitor</title>" + \
    "    <meta http-equiv=\"refresh\" content=\"5\">" + \
    "  </head>" + \
    "    <style>" + \
    "  h1 { text-align: center; }" + \
    "  h3 { text-align: center; }" + \
    "</style>" + \
    "<h3>" + \
    "    Burner indicator light<br>" + \
    "    <i><big><big>" + \
    "        $status" + \
    "        <br>" + \
    "        $on_time" + \
    "        <br>" + \
    red_h3tag1 + \
    "        $elapsed_time" + \
    red_h3Tag2 + \
    "    </big></big></i>" + \
    "</h3>" + \
    "<h3>" + \
    "    Stovetop average temperature<br>" + \
    "    <i><big><big>" + \
    "        $temperature" + \
    "    </big></big></i>" + \
    "</h3>" + \
    "<center><small>" + \
    "   $timeNow" + \
    "</small></center>" + \
    "</html>")
    return HttpResponse(thePage.substitute(status = status, on_time = on_time, 
                                           elapsed_time = elapsed_time, temperature = temperature,
                                           timeNow = timeNow))

def history(request):
    if env_file_err:
         theHistory= env_file_err
    else:
        theHistory = "lightSensor.latest_event: " + str(lightSensor.latest_event) + "<br>" + \
                    "lightSensor.latest_on_event: " + str(lightSensor.latest_on_event) + "<br>" + \
                    "temperatureSensor.latest_temperature_event: " + str(temperatureSensor.latest_temperature_event) + "<br>"        

    return HttpResponse(theHistory)