import os, json, csv, psycopg2, re, pdb
from drive_downloader import DriveDownloader
from busybody_getter import BusybodyGetter
from xlsx_handler import Handler
from string import digits

import warnings
warnings.simplefilter("ignore") # Slider List Extension is not supported and will be removed

# Open known and unknown files
known_file = csv.writer(open("known_v2.csv", "w"))
unknown_file = csv.writer(open("unknown_v2.csv", "w"))
header = ["Source", "Customer", "Street", "City", "State", "Zip", "Phone", "Product", "Premise", "Website", "Comments"]
#           0           1           2       3       4       5       6           7           8           9
known_file.writerow(header)
unknown_file.writerow(header)

# Function to check if all information has been found
def known(customer):
    if type(customer) == str:
        # look in the address book
        pass
    elif type(customer) == dict:
        required_keys = ["street", "city", "state", "zip"]
        result = [False for rk in required_keys if customer["address"][rk] == ""]
        if False not in result:
            return True
    else:
        return False


downloads = ["XLSX examples/column_full_address.xlsx",
            "XLSX examples/column_phone_sep.xlsx",
            "XLSX examples/column_dzip_dphone_chainaddress.xlsx",
            "XLSX examples/phone_address.xlsx",
            "XLSX examples/int_iden.xlsx",
            "XLSX examples/multipage_file.xlsx",
            "XLSX examples/sep1.xlsx",
            "XLSX examples/sep2_no_state.xlsx"]

# downloads = [f"drive_downloaded/{file}" for file in os.listdir("drive_downloaded/") if file != ".gitkeep"]
for download in downloads:

    # Parse XLSX file with Handler
    file = Handler(download)
    source_info = file.payload["source_file"]
    customers_info = file.payload["customers"]
    if source_info["identifier"] == "skip":
        print(source_info["name"], "was skipped")
        continue

    # Check with Busybody
    BusybodyGetter(file)

    # Check Address Book

    # Write to known/unknown file
    source = source_info['name']
    customers = list(customers_info.keys())

    for name in customers:
        customer = customers_info[name]
        parts = customer["address"]
        if len(customer["products"]) == 0:
            customer["products"] = [""]

        for product in customer["products"]:
            row = [source, name, parts["street"], parts["city"], parts["state"], parts["zip"], parts["phone"], product, customer["premise"], customer["website"]]
            if known(customer):
                known_file.writerow(row)
            else:
                unknown_file.writerow(row)

print("Done")
