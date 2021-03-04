import os, json, csv, psycopg2, re
from drive_downloader import DriveDownloader
from xlsx_handler import Handler

import warnings
warnings.simplefilter("ignore") # Slider List Extension is not supported and will be removed

#Open connection to database
conn = psycopg2.connect(host='ec2-3-231-241-17.compute-1.amazonaws.com', database='d6g73dfmsb60j0', user='doysqqcsryonfs', password='c81802d940e8b3391362ed254f31e41c20254c6a4ec26322f78334d0308a86b3')
cur = conn.cursor()

# Open address_book
with open("address_book.json", "r") as f:
    address_book = json.load(f)

def download_files():
    downloader = DriveDownloader()
    quarters = downloader.child_folders(downloader.root)
    quarter = quarters[2] # Q4 2020 // downloader.latest_file(quarters)

    lists = downloader.child_folders(downloader.folder_contents(quarter))
    downloads = []
    for lst in lists:
        contents = downloader.folder_contents(lst)
        for item in contents:
            try:
                download = downloader.download_file(item, out_path="./drive_downloaded/")
                downloads.append(download)
            except Exception as e:
                print("\nFailed to download", item["name"])
                print(e)
                print("\n")

    return downloads

def load_chains():
    cur.execute("SELECT ID, name FROM chains")
    results = cur.fetchall()

    chains = []
    for result in results:
        chains.append({"name":result[1], "id":result[0]})
    return chains

def strip_name(name):
    while name[-1].isdigit() or name[-1] == "#":
        name = name[:-1]
    return re.sub(' +', ' ', name.lower()
        .replace("'", "")
        .replace("liquors", "").replace("liquor", "")
        .replace("and", "&")
        .replace("wine & spirits", "").replace("wine & sp", "")
        .strip())

def is_chain(name):
    for chain in chains:
        if chain["name"].lower() in str(name).lower():
            return chain["id"]
    return False

# False or address_object
def is_known(customer):
    for saved_customer in list(address_book.keys()):
        if saved_customer.lower() == str(customer).lower():
            return address_book[saved_customer]
    return False

def write_address(source, customer, products):
    customer_info = is_known(customer)
    if customer_info is False:
        # unknown file
        unknown_file.writerow([source, customer, "", "", "", "", products])
    else:
        # known file
        known_file.writerow([source, customer, customer_info["address"], customer_info["city"], customer_info["state"], customer_info["zip"], products])

# Open known and unknown files
known_file = csv.writer(open("known.csv", "w"))
unknown_file = csv.writer(open("unknown.csv", "w"))
header = ["Source", "Customer", "Address", "City", "State", "Zip", "Products", "Comments"]
known_file.writerow(header)
unknown_file.writerow(header)

chains = load_chains()
# downloads = ["drive_downloaded/Baldor YOY - New accounts, November 2020.xlsx", "drive_downloaded/Ruby Wine Account List.xlsx", "drive_downloaded/Associated Buyers Dec 2020.xlsx", "drive_downloaded/Associated Buyers 12_11_2020.xlsx"]
downloads = [f"drive_downloaded/{file}" for file in os.listdir("drive_downloaded/") if file != ".gitkeep"]
# downloads = download_files()
for download in downloads:
    file = Handler(download)
    if file.payload["source_file_type"]["identifier"] == "skip":
        continue

    source = file.payload["source_file_name"]
    customers = list(file.payload["customers"].keys())

    chain_id = is_chain(source)
    if chain_id is False:
        # The file does not represent a chain
        for customer in customers:
            products = ", ".join(file.payload["customers"][customer])
            chain_id = is_chain(customer)
            if chain_id is False:
                # Location is not a chain
                write_address(source, customer, products)

            else:
                # Location is a chain
                remote_id = re.sub("[^0-9]", "", customer).lstrip("0")
                cur.execute(f"SELECT address FROM stores WHERE chain_id='{chain_id}' and remote_id='{remote_id}'")
                results = cur.fetchall()
                if len(results) > 0:
                    # Address found
                    address = results[0][0]
                    known_file.writerow([source, customer, address, "", "", "", products])
                else:
                    # Address not found
                    # Pass back to address book
                    write_address(source, customer, products)


    else:
        if chain_id == 42:
            # Whole Foods
            for store in customers:
                products = ", ".join(file.payload["customers"][store])
                cur.execute(f"SELECT address FROM stores WHERE chain_id='{chain_id}' and LOWER(address) LIKE '%{store.lower()}%'")
                results = cur.fetchall()
                if len(results) > 0:
                    address = results[0][0]
                    known_file.writerow([source, store, address, "", "", "", products])
                else:
                    write_address(source, store, products)

        elif str(customers[0]).isdigit():
            # The file represents a chain and has numeric id's
            for remote_id in customers:
                products = ", ".join(file.payload["customers"][remote_id])
                cur.execute(f"SELECT address FROM stores WHERE remote_id='{remote_id}' and chain_id='{chain_id}'")
                results = cur.fetchall()
                if len(results) > 0:
                    # Address found
                    address = results[0][0]
                    known_file.writerow([source, remote_id, address, "", "", "", products])
                else:
                    # Address not found
                    # Pass it back to the address book
                    write_address(source, customer, products)
        else:
            print("chain data not found", customers)
            print("THIS DOES NOTHING")

conn.close()
