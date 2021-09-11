import os, json, csv, psycopg2, re, pdb, time, requests
from container_manager import ContainerManager
from drive_downloader import DriveDownloader
from busybody_getter import BusybodyGetter
from xlsx_handler import Handler
from secret import slack_webhook
from customer import Customer
from string import digits
import pandas as pd

from datetime import datetime

import warnings
warnings.simplefilter("ignore") # Slider List Extension is not supported and will be removed

SLACK = False #Boolean for if slack should be notified
DL = DriveDownloader()
print('DriveDownloader Loaded')
BRANDS = DL.root.children

with open('last_run.txt', 'r') as f:
    last_run = datetime.fromisoformat(f.read())

# Function to send message to slack
def slack(msg):
    headers = {'Content-Type': 'application/json'}
    data = json.dumps({'text': msg})
    response = requests.post(slack_webhook, data=data, headers=headers)
    return response

# Function to see if a file life is newer than a threshold
def new(drive_time):
    file_life = datetime.utcnow() - datetime.fromisoformat(drive_time[:19])
    thresh = datetime.now() - last_run
    if file_life < thresh:
        return True
    else:
        return False

# Function to find important subdirectories from brand directory
def find_io_folders(container_folder):
    try:
        unifier_io = [f for f in container_folder.children if 'unifier_io' in f.path][0]
        brand_io = [f for f in container_folder.children if 'brand_io' in f.path][0]
        return unifier_io, brand_io
    except IndexError:
        # No children means new brand
        return None, None

# Finds transformer files and sorts by date
def find_finished_files(brand_folder):
    unifier_io, _ = find_io_folders(brand_folder)
    finished_files = [f for f in unifier_io.contents if '_unifier_transformer' in f['name']]
    if len(finished_files) == 0:
        return []
    else:
        return sorted(finished_files, key=lambda f: f['createdTime'])

def analize_last_run(current_manager):
    finished_files = find_finished_files(current_manager.drive_container.parent.parent)
    if finished_files:
        latest_run = finished_files[-1] # datetime.fromisoformat(drive_time[:19])
        latest_run_path = DL.download_file(latest_run)
        latest_manager = ContainerManager([latest_run_path], current_manager.drive_container, True)
        gap_path = current_manager.generate_gap_report(latest_manager)
        new_path = current_manager.generate_new_report(latest_manager)
        DL.upload_file(gap_path, unifier_io.folder_data['id'])
        DL.upload_file(new_path, unifier_io.folder_data['id'])
        os.remove(gap_path)
        os.remove(new_path)
    else:
        return None

files_present_queue = []
unknowns_learned_queue = []

# Find brand folder from unifier_io folder_id
def search_brands(id):
    for brand in BRANDS:
        ids = [c.folder_data['id'] for c in brand.children]
        if id in ids:
            return brand
    return None

def download_files(files):
    downloads = []
    for f in files:
        downloads.append(DL.download_file(f))
        print('.', end='', flush=True)
    print()
    return downloads

# Runs through each brand folder to find new files
# adds them to their respective queue
for brand in BRANDS:
    unifier_io, brand_io = find_io_folders(brand)

    if unifier_io is None: #Initialize new brand
        DL.initialize_brand(brand)
        slack(f'Initializing {brand.folder_data["name"]}') if SLACK else False
        continue

    [ # Get new container folders
        files_present_queue.append(container)
        for container in brand_io.children
        if new(container.folder_data['createdTime'])
    ]
    [ # Get new complete files
        unknowns_learned_queue.append(file)
        for file in unifier_io.files
        if new(file['createdTime']) and '_complete' in file['name']
    ]
print('New files flagged')

#####################
### Files Present ###
for container in files_present_queue:
    brand = container.parent.parent
    container.modify_time() # Update container time for recursive search
    unifier_io, _ = find_io_folders(brand)
    # Download brand files
    DL.clear_storage()
    print(f'Downloading {len(container.files)} {container} files from {brand}')
    current_downloads = download_files(container.files)

    # Download old files to get missing info
    old_transformer_files = find_finished_files(brand)
    print(f'Downloading {len(old_transformer_files)} old files from {brand}')
    previous_downloads = download_files(old_transformer_files)
    previous_manager = ContainerManager(previous_downloads, container, True)

    container_manager = ContainerManager(downloads, container)
    print('Exporting files')
    known_path = container_manager.generate_knowns()

    if container_manager.unknowns():
        # Upload Unknowns file
        unknown_path = container_manager.generate_unknowns()
        upload = DL.upload_file(unknown_path, unifier_io.folder_data['id'])
        os.remove(unknown_path)
    else:
        # Upload knowns, gap, new, for_transformer
        new_known_path = known_path.replace('_unifier', '_unifier_finished')
        os.rename(known_path, new_known_path)
        upload = DL.upload_file(new_known_path, unifier_io.folder_data['id'])

        analize_last_run(container_manager)

        transformer_file = container_manager.generate_transformer()
        DL.upload_file(transformer_file, unifier_io.folder_data['id'])
        os.remove(transformer_file)
        os.remove(new_known_path)

    slack(f'uploaded {unifier_io.path}/{upload["name"]}') if SLACK else False
    print('finished', container, upload['name'])


##########################
### Unknowns Completed ###
for drive_file in unknowns_learned_queue:
    # Download file
    DL.clear_storage()
    print('downloading', drive_file['name'])
    csv_path = DL.download_file(drive_file)
    csv_name = csv_path.split('/')[-1].split('_complete')[0]

    # Match to existing
    unifier_id = drive_file['parents'][0]
    brand = search_brands(unifier_id)
    brand_name = brand.path.split('/')[-1]
    pending_file_path = [f'./pending/{file}' for file in os.listdir('./pending/') if brand_name in file and csv_name in file][0]

    container_folder = DL.find_folder(drive_file['parents'][0]).parent
    container_manager = ContainerManager([csv_path, pending_file_path], container_folder, True)

    finished_file = container_manager.generate_finished()
    transformer_file = container_manager.generate_transformer()

    analize_last_run(container_folder)

    DL.upload_file(finished_file, unifier_id)
    DL.upload_file(transformer_file, unifier_id)
    os.remove(finished_file)
    os.remove(transformer_file)
    os.remove(pending_file_path)
    slack(f'uploaded {brand.path}/unifier_io/{finished_file.split("/")[-1]}') if SLACK else False


print('Continue to record time')
pdb.set_trace()
print('done')
with open('last_run.txt', 'w') as f:
    f.write(datetime.now().isoformat())
