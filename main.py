import os, json, csv, psycopg2, re, pdb
from drive_downloader import DriveDownloader
from xlsx_handler import Handler
from string import digits

import warnings
warnings.simplefilter("ignore") # Slider List Extension is not supported and will be removed

counter = 0 #for debugging

#Open connection to database
conn = psycopg2.connect(host='ec2-3-231-241-17.compute-1.amazonaws.com', database='d6g73dfmsb60j0', user='doysqqcsryonfs', password='c81802d940e8b3391362ed254f31e41c20254c6a4ec26322f78334d0308a86b3')
cur = conn.cursor()

# Open known and unknown files
known_file = csv.writer(open("known.csv", "w"))
unknown_file = csv.writer(open("unknown.csv", "w"))
header = ["Source", "Customer", "Street", "City", "State", "Zip", "Phone", "Products", "Comments"]
known_file.writerow(header)
unknown_file.writerow(header)

chains = load_chains()
downloads = ["drive_downloaded/UNFI Q4 2020 .xlsx"]
downloads = [f"drive_downloaded/{file}" for file in os.listdir("drive_downloaded/") if file != ".gitkeep"]
# downloads = download_files()

for download in downloads:
    file = Handler(download)
    if file.payload["source_file_type"]["identifier"] == "skip":
        continue

    source = file.payload["source_file_name"]
    customers = list(file.payload["customers"].keys())

conn.close()
print("Done", counter)
