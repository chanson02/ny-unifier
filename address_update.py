import os, json, csv
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

def valid(value):
    if value is not None and value == value:
        return True
    else:
        return False

known_file = csv.writer(open("known.csv", "r+"))
with open("address_book.json", "r") as f:
    address_book = json.load(f)

# rows = pd.read_csv("unknown.csv").values[1:]
rows = pd.ExcelFile("Ryan.F_Missing Information.xlsx").parse().values[1:]
for row in rows:
    if False not in [valid(column) for column in row[:-1]]:
        print("This got called")
        # Add to address book
        address_book[str(row[1])] = {
            "address": str(row[2]),
            "city": str(row[3]),
            "state": str(row[4]),
            "zip": str(row[5])
        }

        # Inject into known file
        known_file.writerow(row)

with open("address_book.json", "w") as f:
    json.dump(address_book, f, indent=2)
# os.remove("unknown.csv")
