import os, json, csv
from drive_downloader import DriveDownloader
from xlsx_handler import Handler
import pdb

import warnings
warnings.simplefilter("ignore") # Slicer List Extension is not supported and will be removed

cwd = os.getcwd()

def download_files():
    downloader = DriveDownloader()

    quarters = downloader.child_folders(downloader.root)
    # quarter = downloader.latest_file(quarters)
    quarter = quarters[2] # !!! testing, Q4 2020

    lists = downloader.child_folders(downloader.folder_contents(quarter)) # November/December List
    downloads = []
    for lst in lists:
        contents = downloader.folder_contents(lst)
        for item in contents:
            try:
                download = downloader.download_file(item, out_path=cwd + "/drive_downloaded/")
                downloads.append(download)
            except Exception as e:
                print("\nFailed to download", item["name"])
                print(e)
                print("\n")
    return downloads

# Open the address book
with open("address_book.json", "r") as f:
    address_book = json.load(f)

# Setup output files
known_file = csv.writer(open("known.csv", "w"))
unknown_file = csv.writer(open("unknown.csv", "w"))
known_file.writerow(["Source", "Name ID", "Customer", "Address", "City", "State", "Zip", "Product"])
unknown_file.writerow(["Source", "Name ID", "Customer", "Address", "City", "State", "Zip", "Product"])

downloads = ["drive_downloaded/Hella Direct Orders.xlsx"]
# downloads = download_files()
for download in downloads:
    file = Handler(download)
    if file.payload["source_file_type"]["identifier"] == "skip":
        print("skipping", download)
        continue
    source = file.payload["source_file_name"]
    customers = list(file.payload["customers"].keys())
    name_id = file.payload["source_file_type"]["name_id"]
    file_address_book = address_book[name_id]

    for customer in customers:
        products = file.payload["customers"][customer]
        for product in products:
            row = [source, name_id, customer, "", "", "", "", product]
            try:
                address_info = file_address_book[customer]
                row[3] = address_info["address"]
                row[4] = address_info["city"]
                row[5] = address_info["state"]
                row[6] = address_info["zip"]
                known_file.writerow(row)
            except KeyError:
                unknown_file.writerow(row)
