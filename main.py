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

with open('last_run.txt', 'r') as f:
    # last_run = float(f.read())
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

def analize_last_run(current_manager):
    unifier_io, _ = find_io_folders(current_manager.drive_container.parent.parent)
    finished_files = [f for f in unifier_io.contents if '_unifier_transformer' in f['name']]
    if len(finished_files) > 0:
        latest_run = sorted(finished_files, key=lambda f: f['createdTime'])[-1] # check drive_file datetime.fromisoformat(drive_time[:19])
        latest_run_path = dl.download_file(latest_run)
        latest_manager = ContainerManager([latest_run_path], current_manager.drive_container)
        gap_path = current_manager.generate_gap_report(latest_manager)
        new_path = current_manager.generate_new_report(latest_manager)
        dl.upload_file(gap_path, unifier_io.folder_data['id'])
        dl.upload_file(new_path, unifier_io.folder_data['id'])
        os.remove(gap_path)
        os.remove(new_path)
    else:
        return None


dl = DriveDownloader()
print('DriveDownloader Loaded')
brands = dl.root.children
files_present_queue = []
unknowns_learned_queue = []

# Find brand folder from unifier_io folder_id
def search_brands(id):
    for brand in brands:
        ids = [c.folder_data['id'] for c in brand.children]
        if id in ids:
            return brand
    return None

# Runs through each brand folder to find new files
# adds them to their respective queue
for brand in brands:
    unifier_io, brand_io = find_io_folders(brand)

    if unifier_io is None: #Initialize new brand
        dl.initialize_brand(brand)
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

# Files Present
for container in files_present_queue:
    # TO-DO: DOWNLOAD OLD FILES AND SEARCH FOR UNKNOWNS

    # Update container time for recursive search
    container.modify_time()
    unifier_io = [f for f in container.parent.parent.children if 'unifier_io' in f.path][0]
    # Download brand files
    dl.clear_storage()
    downloads = []
    print(f'Downloading {container}')
    for f in container.files:
        downloads.append(dl.download_file(f))
        print('.', end='', flush=True)
    print()

    container_manager = ContainerManager(downloads, container)
    print('Exporting files')
    known_path = container_manager.generate_knowns()

    if container_manager.unknowns():
        # Upload Unknowns file
        unknown_path = container_manager.generate_unknowns()
        upload = dl.upload_file(unknown_path, unifier_io.folder_data['id'])
        os.remove(unknown_path)
    else:
        # Upload knowns, gap, new, for_transformer
        new_known_path = known_path.replace('_unifier', '_unifier_finished')
        os.rename(known_path, new_known_path)
        upload = dl.upload_file(new_known_path, unifier_io.folder_data['id'])

        analize_last_run(container_manager)

        transformer_file = container_manager.generate_transformer()
        dl.upload_file(transformer_file, unifier_io.folder_data['id'])
        os.remove(transformer_file)
        os.remove(new_known_path)

    slack(f'uploaded {unifier_io.path}/{upload["name"]}') if SLACK else False
    print('finished', container, upload['name'])

# Unknowns Completed
for drive_file in unknowns_learned_queue:
    # Download file
    dl.clear_storage()
    print('downloading', drive_file['name'])
    csv_path = dl.download_file(drive_file)
    csv_name = csv_path.split('/')[-1].split('_complete')[0]

    # Match to existing
    unifier_id = drive_file['parents'][0]
    brand = search_brands(unifier_id)
    brand_name = brand.path.split('/')[-1]
    pending_file_path = [f'./pending/{file}' for file in os.listdir('./pending/') if brand_name in file and csv_name in file][0]

    container_folder = dl.find_folder(drive_file['parents'][0]).parent
    container_manager = ContainerManager([csv_path, pending_file_path], container_folder)

    finished_file = container_manager.generate_finished()
    transformer_file = container_manager.generate_transformer()

    #HERE

    dl.upload_file(finished_file, unifier_id)
    dl.upload_file(transformer_file, unifier_id)
    os.remove(finished_file)
    os.remove(transformer_file)
    os.remove(pending_file_path)
    slack(f'uploaded {brand.path}/unifier_io/{finished_file.split("/")[-1]}') if SLACK else False


print('Continue to record time')
pdb.set_trace()
print('done')
with open('last_run.txt', 'w') as f:
    # f.write(datetime.now(pytz.timezone('Etc/GMT+0')).isoformat())
    f.write(datetime.now().isoformat())
