import os
from datetime import datetime
import csv
import glob

class Xformer:
     def can_add_row(self, row):
         if row["location"] and "Stove" not in row["location"]:
             return row["data"].isnumeric()
         return False
         
     def xform(self):
        print(os.getcwd())
        filenames = glob.glob("events_*csv")
        if len(filenames) == 0:
            filenames = glob.glob("**/events_*csv")
            if len(filenames) == 0:
                print("no files!")
                return
        columnNames = { "" }
        for f in filenames:
            with open(f, "r", newline="") as csvfile:
                theReader = csv.DictReader(csvfile)
                for row in theReader:
                    if self.can_add_row(row):
                        columnNames.add(row["location"])
        columnNames.remove("")
        temperatureRows = {}
        for f in filenames:
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

xformer = Xformer()
xformer.xform()