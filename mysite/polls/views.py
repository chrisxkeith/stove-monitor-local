from django.shortcuts import render

from django.conf import settings
from django.http import HttpResponse

from string import Template

from pyparticleio.ParticleCloud import ParticleCloud
from dotenv import load_dotenv
import os
from datetime import datetime
try:
    from zoneinfo import ZoneInfo
except ImportError:
    # Just to handle older python versions on Linux, not needed unless I try GCP again
    pass # from backports.zoneinfo import ZoneInfo

import csv

import json
from urllib.request import urlopen

import time
import sys

photon_01 = "1c002c001147343438323536"
photon_02 = "300040001347343438323536"
photon_05 = "19002a001347363336383438"
photon_07 = "32002e000e47363433353735"
photon_08 = "500041000b51353432383931"
photon_09 = "1f0027001347363336383437"
photon_10 = "410027001247363335343834"
photon_14 = "28003d000147373334323233"
photon_15 = "270037000a47373336323230"
nws_core_id = "nws_core_id"

locations = {
    photon_01 : "Big Bedroom",
    photon_02 : "Small Bedroom",
    photon_05 : "Stove Temperature",
    photon_07 : "Stove Light",
    photon_08 : "Kitchen", 
    photon_09 : "FL Room",
    photon_10 : "Office",
    photon_15 : "Development",
    nws_core_id : "Forecast",
}

locations_by_name = {
    "photon-01" : "Big Bedroom",
    "photon-02" : "Small Bedroom",
    "photon-05" : "Stove Temperature",
    "photon-07" : "Stove Light",
    "photon-08" : "Kitchen", 
    "photon-09" : "FL Room",
    "photon-10" : "Office",
    "photon-15" : "Development",
    "nws_core_id" : "Forecast",
}

def log(msg):
    now = datetime.now().strftime('%Y%m%d%H%M%S')
    print(now + "\t" + msg)

def get_host():
    # Windows?
    if os.environ.get("COMPUTERNAME"):
        return os.environ["COMPUTERNAME"]
    # Linux?
    if os.environ.get("HOSTNAME"):
        return os.environ["HOSTNAME"]
    return "unknown host"

WRITE_CSVS = False # get_host() == "2018-CK-NUC"

class CsvWriter:
    def __init__(self, file_extension):
        if WRITE_CSVS:
            now = datetime.now().strftime('%Y%m%d%H%M%S')
            self.fileName = file_extension + "_" + now + ".csv"
            log("Will write to: " + os.path.realpath(self.fileName))
            self.wroteHeader = False
        else:
            log("Not writing .csv file")

    def append(self, event):
        if WRITE_CSVS:
            with open(self.fileName, "a", newline="") as csvfile:
                # format for Google Sheets
                pst = datetime.strptime(event["published_at"],
                                        "%Y-%m-%dT%H:%M:%S.%f%z").astimezone(ZoneInfo("US/Pacific"))
                event["gsheets_timestamp"] = pst.strftime("%Y-%m-%d %H:%M:%S")
                event["location"] = locations[event["coreid"]]
                theWriter = csv.DictWriter(csvfile, fieldnames = event.keys())
                if not self.wroteHeader:
                    theWriter.writeheader()
                    self.wroteHeader = True                
                theWriter.writerow(event)

eventCsvWriter = CsvWriter("events")

class ForecastGetter:
    def __init__(self):
        self.last_call_to_api = None

    def new_day(self):
        if not self.last_call_to_api:
            return True
        return datetime.now().toordinal() > self.last_call_to_api.toordinal()

    def try_to_get_forecast(self, event_func):
        try:
            if False:
                tomorrow = datetime.now().toordinal() + 1
                with urlopen("https://api.weather.gov/gridpoints/MTR/94,102/forecast/hourly") as f:
                    resp = json.load(f)
                    periods = resp["properties"]["periods"]
                    for period in periods:
                        startTimeStr = period["startTime"]
                        timeString = startTimeStr[0:22] + startTimeStr[23:]
                        startTime = datetime.strptime(timeString, "%Y-%m-%dT%H:%M:%S%z")
                        if startTime.toordinal() <= tomorrow:
                            event = {
                                "data" : period["temperature"],
                                "ttl" : 1,
                                "published_at" : startTime.strftime("%Y-%m-%dT%H:%M:%S.%f%z"),
                                "coreid" : nws_core_id,
                                "event_name" : "Temperature",
                            }
                            event_func(event)
                    self.last_call_to_api = datetime.now()
        except Exception as e:
            log("Exception: '" + str(e) + "' when trying to get forecast data. Will try again tomorrow.")
            self.last_call_to_api = datetime.now()

    def get_forecast(self):
        if self.new_day():
            self.try_to_get_forecast(eventCsvWriter.append)

forecastGetter = ForecastGetter()

class EventHandler:
    latest_event = None

    def handle_call_back(self, event_data):
        self.latest_event = event_data

class Sensor:
    eventHandler = EventHandler()

    def getData(self):
        try:
            ret = self.device.getData("")
            log("device.getData() return value) = " + repr(ret) + \
                ", deviceName: " + self.deviceName + ", eventName: " + self.eventName + \
                ", " + locations_by_name[self.deviceName])
        except Exception as e:
            log(repr(e) + ", getData() failed, deviceName: " + \
                self.deviceName + ", eventName: " + self.eventName + \
                ", " + locations_by_name[self.deviceName])

    def __init__(self, particleCloud, deviceName, eventName):
        self.deviceName = deviceName
        self.eventName = eventName
        device = None
        if particleCloud:
            try:
                device = [d for d in particleCloud.devices_list if d.name == deviceName][0]
            except IndexError as e:
                log(repr(e) + ", No device named, " + deviceName + ", eventName: " + eventName + \
                ", " + locations_by_name[deviceName])
                return
            device.subscribe(eventName, self.handle_call_back)
        self.device = device

    def handle_call_back(self, event_data):
        self.eventHandler.handle_call_back(event_data)

# For 'circular' reference
class AbstractApp():
    def check_devices(self):
        pass

app = AbstractApp()

class TemperatureEventHandler(EventHandler):
    first_temperature_event = None
    total_temperature_events = 0
    latest_temperature_event = None

    def handle_call_back(self, event_data):
        super().handle_call_back(event_data)
        if not self.first_temperature_event:
            self.first_temperature_event = event_data
        self.total_temperature_events += 1
        self.latest_temperature_event = event_data
        eventCsvWriter.append(event_data)

class TemperatureSensor(Sensor):
    eventHandler = TemperatureEventHandler()

    def handle_call_back(self, event_data):
        self.eventHandler.handle_call_back(event_data)
        forecastGetter.get_forecast()
        app.check_devices()

    def getDisplayVals(self):
        temperature = "No data yet"
        if (self.eventHandler.latest_temperature_event):
            temperature = str(self.eventHandler.latest_event["data"])
        return temperature

class LightEventHandler(EventHandler):
    light_event = None
    def handle_call_back(self, event_data):
        super().handle_call_back(event_data)
        self.light_event = json.loads(event_data["data"])

    def getValsForDisplay(self):
        status = "No data yet"
        on_time = None
        elapsed_seconds = None
        if (self.light_event):
            if self.light_event["on"] == "true":
                status = "On"
                on_time = datetime.strptime(self.light_event["whenSwitchedToOn"],
                                        "%Y-%m-%dT%H:%M:%S")
                now = datetime.now().astimezone(ZoneInfo("US/Pacific")).timestamp()
                elapsed_seconds = now - on_time.timestamp()
            else:
                status = "Off"
        return [ status, on_time, elapsed_seconds ]

class LightSensor(Sensor):
    eventHandler = LightEventHandler()

    def handle_call_back(self, event_data):
        self.eventHandler.handle_call_back(event_data)

    def getDisplayVals(self):
        [ status, on_time, elapsed_seconds ] = self.eventHandler.getValsForDisplay()
        elapsed_display = ""
        if elapsed_seconds:
            mins = int(elapsed_seconds / 60)
            secs = int(elapsed_seconds % 60)
            hours = int(mins / 60)
            mins = int(mins % 60)
            elapsed_display = "Elapsed: {:0>2}:{:0>2}:{:0>2}".format(hours, mins, secs)
        time_turned_on = ""
        if on_time:
            time_turned_on = on_time.astimezone(ZoneInfo("US/Pacific")).strftime("%I:%M %p")
        return [ status, time_turned_on, elapsed_display ]

    def getElapsedSeconds(self):
        [ status, on_time, elapsed_seconds ] = self.eventHandler.getValsForDisplay()
        return elapsed_seconds

class App(AbstractApp):
    htmlHead = "<html lang=\"en\">" + \
        "  <head>" + \
        "    <title>Stove Monitor</title>" + \
        "    <meta http-equiv=\"refresh\" content=\"5\">" + \
        "  </head>"
    
    forecast_events = []
    last_call_to_getData = None
    getting_data = False

    def __init__(self):
        self.env_file_err = None
        if os.path.exists("./.env"):
            particleCloud = None
            if not settings.TESTING:
                load_dotenv("./.env")
                particleCloud = ParticleCloud(username_or_access_token=os.getenv("ACCESS_TOKEN"))
            self.lightSensor = LightSensor(particleCloud, "photon-07", "Light sensor")
            self.temperatureSensor = TemperatureSensor(particleCloud, "photon-05", "Temperature")
            self.thermistorSensors = []
            # for photonName in [ "photon-01", "photon-02", "photon-08", "photon-09", "photon-10", "photon-15", ]: 
            #    self.thermistorSensors.append(TemperatureSensor(particleCloud, photonName, "Temperature"))
            self.get_data()
        else:
            self.env_file_err = "Error: No file: ./.env in " + os.getcwd()
            log(self.env_file_err)

    def get_data(self):
        self.lightSensor.getData()
        time.sleep(2) # Give this server time to respond to the first event (?)
        self.temperatureSensor.getData()
        for t in self.thermistorSensors:
            time.sleep(2)
            t.getData()
        self.last_call_to_getData = datetime.now()

    def check_devices(self):
        if not self.last_call_to_getData:
            return
        if datetime.now().toordinal() <= self.last_call_to_getData.toordinal():
            return
        if self.getting_data:
            return
        self.getting_data = True
        self.get_data()
        self.getting_data = False

    def handleRequest(self, showDev):
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
            if showDev:
                status = status + " (dev is disabled!)"
            temperature = self.temperatureSensor.getDisplayVals()
            now = datetime.now(ZoneInfo("US/Pacific"))
            timeNow = now.strftime("%a %d %b %Y, %I:%M:%S %p %Z")
            elapsedSeconds = self.lightSensor.getElapsedSeconds()
            if elapsedSeconds and elapsedSeconds > (45 * 60):
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
            lightSensor = self.lightSensor
            theHistory = self.htmlHead + \
                        "(Production) lightSensor.latest_event: " + \
                            str(lightSensor.eventHandler.latest_event) + "<br>" + \
                        "temperatureSensor.first_temperature_event: " + \
                            str(self.temperatureSensor.eventHandler.first_temperature_event) + "<br>"  + \
                        "temperatureSensor.total_temperature_events: " + \
                            str(self.temperatureSensor.eventHandler.total_temperature_events) + "<br>"  + \
                        "temperatureSensor.latest_temperature_event: " + \
                            str(self.temperatureSensor.eventHandler.latest_temperature_event) + "<br>"  + \
                        "</html>"
        return HttpResponse(theHistory)

    def forecast_data(self, event_data):
        self.forecast_events.append(event_data)

    def showForecast(self):
        if self.env_file_err:
            theforecast = self.env_file_err
        else:
            self.forecast_events = []
            forecastGetter.try_to_get_forecast(self.forecast_data)
            theStr = "forecast disabled"
            if len(self.forecast_events) > 0:
                for e in self.forecast_events:
                    theStr += str(e) + "<br>"
            theforecast = self.htmlHead + \
                        theStr + \
                        "</html>"
        return HttpResponse(theforecast) 

app = App()

def index(request):
    return app.handleRequest(False)

def dev(request):
    return app.handleRequest(True)

def history(request):
    return app.handleHistory()

def forecast(request):
    return app.showForecast()