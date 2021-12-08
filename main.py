from container_manager import ContainerManager
from drive_downloader import DriveDownloader
from datetime import datetime
import slack_send
import csv, os

"""
PROCEDURE:
Look for new file: done
Add knowns (from history) to new file
Post unknown file
when unknown received -> add to history
"""

HEADER = ["Source", "Customer", "Street", "City", "State", "Zip", "Phone", "Product", "Premise", "Website", "Comments"]
SLACK = False # Boolean for if slack should bbe notified
DL = DriveDownloader()
print('DriveDownloader Loaded')
BRANDS = DL.root.children

# Function to send message to slack
def slack(msg):
    print('SLACK:', msg)
    return slack_send.slack('NY-UN-L: ' + msg) if SLACK else False

# Make new empty history file
def init_history(brand):
    pth = f'tmp/{brand.folder_data["name"]}_history.csv'
    with open(pth, 'w') as f:
        writer = csv.writer(f)
        writer.writerow(HEADER)
    return DL.upload_file(pth, brand.folder_data['id'])

for brand in BRANDS:
    # io_folder = brand.children[-1]
    io_folder = [f for f in brand.children if f.folder_data['name'] == 'io'][0]

    # check for new upload
    drive_file = None
    for file in io_folder.contents:
        drive_file = file
        slack(f'{brand} found file {file["name"]}')
    # else move on
    if drive_file is None:
        continue

    # Is history not present?
        # Create empty history file -> Upload
    history = [f for f in brand.files if 'history' in f['name']]
    if len(history) == 0:
        history = init_history(brand)
    else:
        history = history[0]

    # Download file and history
    DL.clear_storage()
    run_file = DL.download_file(drive_file)
    history_file = DL.download_file(history)
    # Run through xlsx_handler
    manager = ContainerManager([run_file], brand)
    old_manager = ContainerManager([history_file], brand)
    manager.load_knowns(old_manager)
    # Delete file
    os.remove(run_file)
    os.remove(history_file)

    # upload known and unknown
    known = manager.generate_knowns()
    unknown = manager.generate_unknowns()
    dir_name = os.path.splitext(drive_file['name'])[0] + ' output'
    dir = DL.make_folder(dir_name, brand.folder_data['id'])
    k_file = manager.generate_knowns()
    uk_file = manager.generate_unknowns()
    DL.upload_file(k_file, dir['id'])
    DL.upload_file(uk_file, dir['id'])
    os.remove(k_file)
    os.remove(uk_file)
    slack(f'Uploaded {brand.path}/{dir_name}')

    # Delete drive_file
    DL.delete_file(drive_file['id'])
