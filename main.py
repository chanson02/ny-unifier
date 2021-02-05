import os
from drive_downloader import DriveDownloader
from xlsx_handler import Handler
import pdb

unfinished = [
    "Walmart Locations.xlsx",
    "Whole Foods Top Selling stores December (2).xlsx",
    "SGWS Nationwide Individual by Store Sales Report Week Ended Dec 04-2020.xlsx",
    "SGWS Nationwide Individual by Store Sales Report Week Ended Dec 31 -2020.xlsx"
]

cwd = os.getcwd()
downloader = DriveDownloader()

quarters = downloader.child_folders(downloader.root)
# quarter = downloader.latest_file(quarters)
quarter = quarters[1] # !!! testing, Q4 2020

lists = downloader.child_folders(downloader.folder_contents(quarter)) # November/December List
downloads = []
for list in lists:
    contents = downloader.folder_contents(list)
    for item in contents:
        try:
            download = downloader.download_file(item, out_path=cwd + "/drive_downloaded/")
            downloads.append(download)
        except Exception as e:
            print("\nFailed to download", item["name"])
            print(e)
            print("\n")

for download in downloads:
    try:
        if os.path.basename(download) in unfinished:
            print(f"unfinished file type: {download}")
        else:
            file = Handler(download)
            file.write(path=cwd + "/processed/")
    except Exception as e:
        print("\n Failed to parse", download)
        print(e)
        print("\n")
