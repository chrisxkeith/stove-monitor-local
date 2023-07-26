from django.shortcuts import render

from django.conf import settings
from django.http import HttpResponse

from string import Template

from pyparticleio.ParticleCloud import ParticleCloud
from dotenv import load_dotenv
import os
from datetime import datetime
from zoneinfo import ZoneInfo

import csv

def getElapsedSeconds(theEvent):
    if theEvent:
        now = datetime.now().astimezone(ZoneInfo("US/Pacific")).timestamp()
        then = datetime.strptime(theEvent["published_at"],
                                "%Y-%m-%dT%H:%M:%S.%f%z").astimezone(ZoneInfo("US/Pacific")).timestamp()
        return int(now - then)
    return -1

class CsvWriter():
        now = datetime.now().strftime('%Y%m%d%H%M%S')
        fileName = "events_" + now + ".csv"
        def append(self, event):
            # Enable only when running locally
            if False:
                with open(self.fileName, "a", newline="") as csvfile:
                    theWriter = csv.DictWriter(csvfile, fieldnames = event.keys())
                    # format for Google Sheets
                    pst = datetime.strptime(event["published_at"],
                                            "%Y-%m-%dT%H:%M:%S.%f%z").astimezone(ZoneInfo("US/Pacific"))
                    event["published_at"] = pst.strftime("%Y-%m-%d %H:%M:%S")
                    theWriter.writerow(event)

csvWriter = CsvWriter()

class EventHandler:
    latest_event = None

    def handle_call_back(self, event_data):
        if self.latest_event:
            event_data["elapsed"] = getElapsedSeconds(self.latest_event)
        self.latest_event = event_data

class Sensor:
    eventHandler = EventHandler()

    def __init__(self, particleCloud, deviceName, eventName):
        if particleCloud:
            device = [d for d in particleCloud.devices_list if d.name == deviceName][0]
            device.subscribe(eventName, self.handle_call_back)
            try:
                device.getData("")
            except Exception as e:
                print(repr(e) + ", deviceName: " + deviceName + ", eventName: " + eventName)

    def handle_call_back(self, event_data):
        self.eventHandler.handle_call_back(event_data)

class TemperatureEventHandler(EventHandler):
    first_temperature_event = None
    total_temperature_events = 0
    latest_temperature_event = None

    def handle_call_back(self, event_data):
        super().handle_call_back(event_data)
        if self.latest_event["event_name"] == "Temperature":
            if not self.first_temperature_event:
                self.first_temperature_event = event_data
            self.total_temperature_events += 1
            if self.latest_temperature_event:
                event_data["elapsed"] = getElapsedSeconds(self.latest_temperature_event)
            self.latest_temperature_event = event_data
            csvWriter.append(event_data)

class TemperatureSensor(Sensor):
    eventHandler = TemperatureEventHandler()

    def handle_call_back(self, event_data):
        self.eventHandler.handle_call_back(event_data)

    def getDisplayVals(self):
        temperature = "No data yet"
        if (self.eventHandler.latest_temperature_event):
            temperature = str(self.eventHandler.latest_event["data"])
        return temperature

class LightEventHandler(EventHandler):
    first_light_event = None
    total_light_events = 0
    latest_on_event = None

    def handle_call_back(self, event_data):
        super().handle_call_back(event_data)
        if not self.first_light_event:
            self.first_light_event = event_data
        self.total_light_events += 1
        if self.latest_on_event:
            event_data["elapsed"] = getElapsedSeconds(self.latest_on_event)
        if self.latest_on_event is None and event_data["data"] == "true":
            self.latest_on_event = self.latest_event
        if event_data["data"] == "false":
            self.latest_on_event = None
        csvWriter.append(event_data)

class LightSensor(Sensor):
    eventHandler = LightEventHandler()

    def handle_call_back(self, event_data):
        self.eventHandler.handle_call_back(event_data)

    def getDisplayVals(self):
        status = "Off"
        on_time = ""
        elapsed_time = ""
        if (self.eventHandler.latest_event):
            if self.eventHandler.latest_event["data"] == "true":
                status = "On"
        else:
            status = "No data yet"
        if self.eventHandler.latest_on_event:
            [ on_time, elapsed_time ] = self.getTimeVals(
                    datetime.strptime(self.eventHandler.latest_on_event["published_at"],
                                      "%Y-%m-%dT%H:%M:%S.%f%z"))
            elapsed_time += " elapsed"
        return [ status, on_time, elapsed_time ]

    def getTimeVals(self, ts):
        on_time = self.getTimeString(ts)
        elapsed_time = self.getElapsedTime()
        return [ on_time, elapsed_time ]

    def getTimeString(self, theDateTime):
        return theDateTime.astimezone(ZoneInfo("US/Pacific")).strftime("%I:%M %p")

    def getElapsedMySeconds(self):
        if self.eventHandler.latest_on_event:
            return getElapsedSeconds(self.eventHandler.latest_on_event)
        return -1

    def getElapsedTime(self):
        elapsedSeconds = self.getElapsedMySeconds()
        mins = int(elapsedSeconds / 60)
        secs = int(elapsedSeconds % 60)
        return "{:0>2}:{:0>2}".format(mins, secs)

class App:
    htmlHead = "<html lang=\"en\">" + \
        "  <head>" + \
        "    <title>Stove Monitor</title>" + \
        "    <meta http-equiv=\"refresh\" content=\"5\">" + \
        "  </head>"
    
    def __init__(self):
        self.env_file_err = None
        if os.path.exists("./.env"):
            particleCloud = None
            if not settings.TESTING:
                load_dotenv("./.env")
                particleCloud = ParticleCloud(username_or_access_token=os.getenv("ACCESS_TOKEN"))
            self.lightSensor = LightSensor(particleCloud, "photon-07", "Light sensor")
            self.temperatureSensor = TemperatureSensor(particleCloud, "photon-05", "Temperature")
        else:
            self.env_file_err = "Error: No file: ./.env in " + os.getcwd()
            print(self.env_file_err)

    def handleRequest(self):
        on_time = ""
        elapsed_time = ""
        temperature = "No data yet"
        timeNow = ""
        red_h3tag1 = ""
        red_h3Tag2 = ""

        if self.env_file_err:
            status = self.env_file_err
        else:
            [ status, on_time, elapsed_time ] = self.lightSensor.getDisplayVals()
            temperature = self.temperatureSensor.getDisplayVals()
            now = datetime.now(ZoneInfo("US/Pacific"))
            timeNow = now.strftime("%a %d %b %Y, %I:%M%p")
            elapsedSeconds = self.lightSensor.getElapsedMySeconds()
            if elapsedSeconds > (45 * 60):
                red_h3tag1 = "<h3 style=\"background-color: Tomato;\">"
                red_h3Tag2 = "<h3>"

        thePage = Template(self.htmlHead + \
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

    def handleHistory(self):
        if self.env_file_err:
            theHistory = self.env_file_err
        else:
            theHistory = self.htmlHead + \
                        "lightSensor.first_light_event: " + \
                            str(self.lightSensor.eventHandler.first_light_event) + "<br>" + \
                        "lightSensor.total_light_events: " + \
                            str(self.lightSensor.eventHandler.total_light_events) + "<br>" + \
                        "lightSensor.latest_event: " + \
                            str(self.lightSensor.eventHandler.latest_event) + "<br>" + \
                        "lightSensor.latest_on_event: " + \
                            str(self.lightSensor.eventHandler.latest_on_event) + "<br>" + \
                        "temperatureSensor.first_temperature_event: " + \
                            str(self.temperatureSensor.eventHandler.first_temperature_event) + "<br>"  + \
                        "temperatureSensor.total_temperature_events: " + \
                            str(self.temperatureSensor.eventHandler.total_temperature_events) + "<br>"  + \
                        "temperatureSensor.latest_temperature_event: " + \
                            str(self.temperatureSensor.eventHandler.latest_temperature_event) + "<br>"  + \
                        "</html>"
        return HttpResponse(theHistory)      

app = App()

def index(request):
    return app.handleRequest()

def history(request):
    return app.handleHistory()