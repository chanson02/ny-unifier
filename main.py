import os, json, csv
from drive_downloader import DriveDownloader
from xlsx_handler import Handler
import pdb

import warnings
warnings.simplefilter("ignore") # Slicer List Extension is not supported and will be removed

cwd = os.getcwd()


######################
### DOWNLOAD FILES ###
######################
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



downloads = ["drive_downloaded/" + file for file in os.listdir('drive_downloaded/') if file!=".gitkeep"]
# downloads = ["drive_downloaded/Hella Direct Orders.xlsx"]
for i in range(len(downloads)):
    download = downloads[i]
    file = Handler(download)
    dir = file.write(path=cwd + "/xlsx_extract/")
    downloads[i] = dir

for download in downloads:
    addresses = {}
    # Open file and address book
    with open(download, "r") as f:
        payload = json.load(f)
    name_id = payload["source_file_type"]["name_id"]
    if name_id == "error":
        continue
    with open("address_book.json", "r") as f:
        customers = json.load(f)[name_id]

    # Check to see if customer has address
    if len(customers.keys()) > 0:
        known_customers = list(customers.keys())
    else:
        known_customers = []
    unknown_customers = []
    for customer in list(payload["customers"].keys()):

        if customer in known_customers:
            # Replace known customers
            addresses[customers[customer]] = payload["customers"][customer]
        else:
            # Save unknown customers
            unknown_customers.append(customer)
            addresses[customer] = payload["customers"][customer]

    payload["customers"] = addresses
    with open(download, "w") as f:
        json.dump(payload, f, indent=2)

    # Make CSV file for unknown customers
    if len(unknown_customers) > 0:
        writer = csv.writer(open(download.replace("xlsx_extract", "unknowns").replace("json", "csv"), "w"))
        writer.writerow(["Customer", "Address"])
        for customer in unknown_customers:
            writer.writerow([customer])

print("Done")
