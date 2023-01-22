import csv
from data import DataStore

ds = DataStore()

with open("data/init.csv", "r", encoding="utf-8") as csvfile:
    csvreader = csv.reader(csvfile)
    for row in csvreader:
        ds.createSummoner(*row)
