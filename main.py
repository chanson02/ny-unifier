import os, json, csv, psycopg2, re, pdb, time, requests
from drive_downloader import DriveDownloader
from busybody_getter import BusybodyGetter
from xlsx_handler import Handler
from string import digits
import pandas as pd

from datetime import datetime

import warnings
warnings.simplefilter("ignore") # Slider List Extension is not supported and will be removed

header = ["Source", "Customer", "Street", "City", "State", "Zip", "Phone", "Product", "Premise", "Website", "Comments"]
#           0           1           2       3       4       5       6           7           8           9

SLACK = False #Boolean for if slack should be notified

with open('last_run.txt', 'r') as f:
    # last_run = float(f.read())
    last_run = datetime.fromisoformat(f.read())

# Function to send message to slack
def slack(msg):
    slack_webhook = 'https://hooks.slack.com/services/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'
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

# Function to check if all information has been found
def known(customer):
    if type(customer) == str:
        # look in the address book
        print('known customer does nothing right now')
        return False
    elif type(customer) == dict:
        required_keys = ["street", "city", "state", "zip"]
        result = [False for rk in required_keys if customer["address"][rk] == ""]
        if False not in result:
            return True
        else:
            return False
    else:
        return False

# Function to 'merge' csv files
def append_csv(to, frm): #from -> to
    update_file = csv.writer(open(to, 'a'))
    rows = pd.read_csv(frm).values
    for row in rows:
        row = [str(v) if str(v) != 'nan' else '' for v in row]
        for product in row[7].split(', '):
            row[7] = product
            update_file.writerow(row)
    return


dl = DriveDownloader()
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


for brand in brands:
    try:
        unifier_io = [f for f in brand.children if 'unifier_io' in f.path][0]
        brand_io = [f for f in brand.children if 'brand_io' in f.path][0]
    except IndexError:
        # No children means new brand
        dl.initialize_brand(brand)
        continue

    # Check to see if there is new files
    for container in brand_io.children:
        if new(container.folder_data['createdTime']):
            files_present_queue.append(container)

    for file in unifier_io.files:
        if new(file['createdTime']) and '_complete.csv' in file['name']:
            unknowns_learned_queue.append(file)

# Files Present
for container in files_present_queue:
    # Download brand files
    dl.clear_storage()
    [dl.download_file(f) for f in container.files]
    downloads = [f"drive_downloaded/{file}" for file in os.listdir("drive_downloaded/") if file != ".gitkeep"]

    # Setup known and unknown files
    path = container.path.replace('/', '|')
    unknown_path = f'./tmp/{path}_incomplete.csv'
    known_file = csv.writer(open(f'./pending/{path}.csv', 'w'))
    unknown_file = csv.writer(open(unknown_path, 'w'))
    known_file.writerow(header)
    unknown_file.writerow(header)

    # Process downloaded files
    for download in downloads:
        # Parse XLSX file with Handler
        file = Handler(download)
        print('parsed', file)
        source_info = file.payload['source_file']
        customer_info = file.payload['customers']
        if source_info['identifier'] == 'skip':
            print(source_info['name'], 'was skipped')
            continue

        # Check with Busybody
        BusybodyGetter(file) # Updates Haldner object
        print('bodied', file)

        # Check Address Book
        pass

        # Writer to known/unknown file
        source = source_info['name']
        customers = list(customer_info.keys())
        for name in customers:
            customer = customer_info[name]
            parts = customer['address']
            if len(customer['products']) == 0:
                customer['products'] = ['']

            row = [source, name, parts["street"], parts["city"], parts["state"], parts["zip"], parts["phone"], ', '.join(customer['products']), customer["premise"], customer["website"]]
            if known(customer):
                for product in customer['products']:
                    row[7] = product
                    known_file.writerow(row)
            else:
                unknown_file.writerow(row)

    # Upload and delete unknown file
    unifier_io = [f for f in container.parent.parent.children if 'unifier_io' in f.path][0]
    upload = dl.upload_file(unknown_path, unifier_io.folder_data['id'])
    slack(f'uploaded {unifier_io.path}/{upload["name"]}') if SLACK else False
    os.remove(unknown_path)

# Unknowns Completed
for drive_file in unknowns_learned_queue:
    # Download file
    dl.clear_storage()
    csv_path = dl.download_file(drive_file)
    csv_name = csv_path.split('/')[-1].split('_complete.csv')[0]

    # Match to existing
    unifier_id = drive_file['parents'][0]
    brand = search_brands(unifier_id)
    brand_name = brand.path.split('/')[-1]
    pending_file_path = [f'./pending/{file}' for file in os.listdir('./pending/') if brand_name in file and csv_name in file][0]

    # Fill out missing info
    append_csv(pending_file_path, csv_path)

    # Upload as '_finished.csv'
    complete_file_path = pending_file_path.replace('.csv', '_finished.csv')
    os.rename(pending_file_path, complete_file_path)
    dl.upload_file(complete_file_path, unifier_id)

    # Delete local file
    os.remove(complete_file_path)



print('done')
with open('last_run.txt', 'w') as f:
    # f.write(datetime.now(pytz.timezone('Etc/GMT+0')).isoformat())
    f.write(datetime.now().isoformat())
