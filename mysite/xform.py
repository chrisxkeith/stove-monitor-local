import os
from datetime import datetime
import csv
import glob

class Xformer:
    def can_add_row(self, row):
         if row["location"] and "Stove" not in row["location"]:
             return row["data"].isnumeric()
         return False

    def get_file_names(self, prefix):
        filenames = glob.glob(prefix + "*csv")
        if len(filenames) == 0:
            thePath = "stove-monitor-local/mysite/"
            filenames = glob.glob(thePath + prefix + "*csv")
            if len(filenames) == 0:
                print("No " + prefix + " files in ./ or " + thePath)
        return filenames

    def read_multi_day_data(self, multi_day_filenames):
        columnNames = []
        temperatureRows = {}
        for f in multi_day_filenames:
            with open(f, "r", newline="") as csvfile:
                theReader = csv.DictReader(csvfile)
                columnNames = theReader.fieldnames
                for row in theReader:
                    temperatureRows[row["Hour"]] = row
        return [ columnNames, temperatureRows ]

    def read_event_data(self, temperatureRows, columnNames, event_filenames):
        for f in event_filenames:
            with open(f, "r", newline="") as csvfile:
                theReader = csv.DictReader(csvfile)
                for row in theReader:
                    if self.can_add_row(row):
                        ts = datetime.strptime(row["gsheets_timestamp"],
                               "%Y-%m-%d %H:%M:%S")
                        truncedTime =  ts.strftime("%Y-%m-%d %H:00:00")
                        temps = temperatureRows.get(truncedTime)
                        if not temps:
                            temps = {}
                            for c in columnNames:
                                temps[c] = ""
                        temps[row["location"]] = row["data"]
                        temperatureRows[truncedTime] = temps

    def write_multi_day_data(self, columnNames, temperatureRows):
        now = datetime.now().strftime('%Y%m%d%H%M%S')
        fileName = "multi_day_data_" + now + ".csv"
        print("Writing to: " + os.path.realpath(fileName))

        with open(fileName, "a", newline="") as csvfile:
            sortedTemps = dict(sorted(temperatureRows.items()))
            theFieldNames = ["Hour"]
            for c in columnNames:
                theFieldNames.append(c)
            theWriter = csv.DictWriter(csvfile, fieldnames = theFieldNames)
            theWriter.writeheader()
            for key, val in sortedTemps.items():
                row = {
                    "Hour" : key,
                }
                for c in columnNames:
                    row[c] = val[c]
                theWriter.writerow(row)

    def xform(self):
        print(os.getcwd())
        event_filenames = self.get_file_names("events_")
        multi_day_filenames = self.get_file_names("multi_day_data_")
        if len(event_filenames) == 0 and len(multi_day_filenames) == 0:
            return
        [ columnNames, temperatureRows ] = self.read_multi_day_data(multi_day_filenames)
        for f in event_filenames:
            with open(f, "r", newline="") as csvfile:
                theReader = csv.DictReader(csvfile)
                for row in theReader:
                    if self.can_add_row(row) and not row["location"] in columnNames:
                        columnNames.append(row["location"])
        self.read_event_data(temperatureRows, columnNames, event_filenames)
        self.write_multi_day_data(columnNames, temperatureRows)

xformer = Xformer()
xformer.xform()