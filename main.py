import os, json, csv, psycopg2, re, pdb, time, requests
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

header = ["Source", "Customer", "Street", "City", "State", "Zip", "Phone", "Product", "Premise", "Website", "Comments"]
#           0           1           2       3       4       5       6           7           8           9

SLACK = True #Boolean for if slack should be notified

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

# Function to check if all address data is found
def known(address):
    rk = ['street', 'city', 'state', 'zip']
    missing = [k for k in rk if address[k] == '']
    return True if len(missing) == 0 else False

# function to generate row
def gen_row(customer, source, address, product):
    return [
        source,
        customer.name,
        address['street'],
        address['city'],
        address['state'],
        address['zip'],
        address['phone'],
        product,
        customer.premise,
        customer.website
    ]

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


for brand in brands:
    try:
        unifier_io = [f for f in brand.children if 'unifier_io' in f.path][0]
        brand_io = [f for f in brand.children if 'brand_io' in f.path][0]
    except IndexError:
        # No children means new brand
        dl.initialize_brand(brand)
        slack(f'Initializing {brand.folder_data["name"]}') if SLACK else False
        continue

    # Check to see if there is new files
    for container in brand_io.children:
        if new(container.folder_data['createdTime']):
            files_present_queue.append(container)

    for file in unifier_io.files:
        if new(file['createdTime']) and '_complete.csv' in file['name']:
            unknowns_learned_queue.append(file)
print('New files flagged')


# Files Present
for container in files_present_queue:
    # Download brand files
    dl.clear_storage()
    [dl.download_file(f) for f in container.files]
    downloads = [f"drive_downloaded/{file}" for file in os.listdir("drive_downloaded/") if file != ".gitkeep"]
    print('Downloaded', container)

    # Setup known and unknown files
    path = container.path.replace('/', '|')
    unknown_path = f'./tmp/{path}_incomplete.csv'
    known_file = csv.writer(open(f'./pending/{path}.csv', 'w'))
    unknown_file = csv.writer(open(unknown_path, 'w'))
    known_file.writerow(header)
    unknown_file.writerow(header)

    # Get customer data by parsing XLSX
    print('Parsing files')
    customers = []
    for download in downloads:
        print('.', end='', flush=True)
        Handler(download, customers)

    print('\nConsulting Busybody')
    bbg = BusybodyGetter()
    # Merge addresses to find best data
    [c.execute(bbg) for c in customers]
    bbg.conn.close()

    print('\nWriting files')
    # Write to csv files
    for customer in customers:
        if customer.final:
            sources = [e['source'] for e in customer.entries]
            products = [e['product'] for e in customer.entries]
            if known(customer.final):
                rows = [gen_row(customer, sources[i], customer.final, products[i]) for i in range(len(sources))]
                known_file.writerows(rows)
            else:
                row = gen_row(customer, sources, customer.final, products)
                unknown_file.writerow(row)
        else:
            #different address for each entry
            for entry in customer.entries:
                row = gen_row(customer, entry['source'], entry['address'], entry['product'])
                if known(entry['address']):
                    known_file.writerow(row)
                else:
                    unknown_file.writerow(row)

    # Upload and delete unknown file
    unifier_io = [f for f in container.parent.parent.children if 'unifier_io' in f.path][0]
    upload = dl.upload_file(unknown_path, unifier_io.folder_data['id'])
    slack(f'uploaded {unifier_io.path}/{upload["name"]}') if SLACK else False
    os.remove(unknown_path)
    print('finished', container)

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
    slack(f'uploaded {brand.path}/unifier_io/{complete_file_path.split("/")[-1]}') if SLACK else False


print('Continue to record time')
pdb.set_trace()
print('done')
with open('last_run.txt', 'w') as f:
    # f.write(datetime.now(pytz.timezone('Etc/GMT+0')).isoformat())
    f.write(datetime.now().isoformat())
