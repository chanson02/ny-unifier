import os, json, csv
import pandas as pd
import pdb

"""
0 - source
1 - name_id
2 - customer
3 - address
4 - city
5 - state
6 - zip
7 - product
"""

known_file = csv.writer(open("known.csv", "r+"))
with open("address_book.json", "r") as f:
    address_book = json.load(f)

rows = pd.read_csv("unknown.csv").values[1:]
for row in rows:
    # Add to address book
    address_book[row[1]][row[2]] = {
        "address": row[3],
        "city": row[4],
        "state": row[5],
        "zip": row[6]
    }

    # Inject into known file
    known_file.writerow(row)

with open("address_book.json", "w") as f:
    json.dump(address_book, f, indent=2)
os.remove("unknown.csv")
