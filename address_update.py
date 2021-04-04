import os, json, csv, re
import pandas as pd
import pdb

"""
0 - source
1 - customer
2 - address
3 - city
4 - state
5 - zip
6 - product
7 - comment
"""

def valid_value(value):
    if value is not None and value == value:
        return True
    else:
        return False

def valid_row(row):
    if False in [valid_value(column) for column in row[:5]]:
        return False
    else:
        return True

known_file = csv.writer(open("known.csv", "r+"))
with open("address_book.json", "r") as f:
    address_book = json.load(f)

rows = pd.ExcelFile("hfactor_unknowns.xlsx").parse().values
for row in rows:
    if valid_row(row):
        known_file.writerow(row)
        address_book[str(row[1]).strip()] = {
            "address":str(row[2]).strip(),
            "city": str(row[3]).strip(),
            "state": str(row[4]).strip(),
            "zip": str(row[5]).strip()
        }

with open("address_book.json", "w") as f:
    json.dump(address_book, f, indent=2)
# os.remove("unknown.csv")
