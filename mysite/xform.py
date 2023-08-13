import os
from datetime import datetime
import csv
import glob

class Xformer:
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
                    if row["location"] and "Stove" not in row["location"]:
                        columnNames.add(row["location"])
        columnNames.remove("")
        temperatureRows = {}
        for f in filenames:
            with open(f, "r", newline="") as csvfile:
                theReader = csv.DictReader(csvfile)
                for row in theReader:
                    if row["location"] and "Stove" not in row["location"]:
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
            theFn = ["gsheets_timestamp"]
            for c in columnNames:
                theFn.append(c)
            theWriter = csv.DictWriter(csvfile, fieldnames = theFn)
            theWriter.writeheader()
            for key, val in temperatureRows.items():
                row = {
                    "gsheets_timestamp" : key,
                }
                for c in columnNames:
                    row[c] = val[c]
                theWriter.writerow(row)

xformer = Xformer()
xformer.xform()