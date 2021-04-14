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
    name = str(name)
    if name.isdigit():
        return ""
    while name[-1].isdigit() or name[-1] == "#" or name[-1] == ":":
        name = name[:-1]
    return re.sub(' +', ' ', os.path.splitext(name.lower())[0]
        .replace("'", "")
        .replace("liquors", "").replace("liquor", "")
        .replace("and", "&")
        .replace("wine & spirits", "").replace("wine & sp", "")
        .strip())

def is_chain(name):

    if "FRED MEYER" in str(name):
        return name[15:].lower()
    elif "TOTAL WINE" in str(name):
        return re.sub("[^0-9]", "", name)
    elif "Nutty Gourmet" in str(name):
        # Run it as a walmart
        cur.execute("SELECT id FROM chains WHERE name='Walmart'")
        return cur.fetchall()[0][0]

    for chain in chains:
        if chain["name"].lower() in str(name).lower():
            return chain["id"]
    return False

# False or address_object
def is_known(customer):
    customer = str(customer).lower()
    for key in list(address_book.keys()):
        saved_customer = key.lower()
        if saved_customer == customer or saved_customer == re.sub(' +', ' ', customer):
            return address_book[key]
    if customer == "DAMON":
        pdb.set_trace()
    return False

def is_address(string):
    string = str(string)
    sep_comma = string.split(", ")
    sep_space = [sep for sep in string.split(" ") if sep != '']
    try:
        return (sep_space[0].replace("-", "").isdigit() or sep_comma[1][0:2].isdigit()) and (sep_space[-1].isdigit() or sep_space[-1].lower() == "usa") and len(sep_comma) > 1
    except IndexError:
        pass
    if "-" in sep_space[-1]:
        # phone number
        return is_address(" ".join(sep_space[:-1]))
    return False

def addressor(address):
    # Call the addressor from the command line
    command = f"ruby ../ny-addressor/lib/from_cmd.rb -o -a '{address}'"
    os.system(command)

    try:
        with open("addressor.json", "r") as f:
            parts = json.load(f)
        os.remove("addressor.json")
    except:
        print("Failed to address", address)
        return address

    if parts is None:
        return address

    # Make sure it has all required parts
    required_keys = ["street_name", "street_number", "city", "state", "postal_code"]
    keys = list(parts.keys())
    for rk in required_keys:
        if rk not in keys:
            parts[rk] = ""

    # Combine the 4 street parts into one
    parts["street"] = f"{parts['street_number']} {parts['street_name']}"
    if "street_label" in keys:
        parts["street"] += f" {parts['street_label']}"
    if "street_direction" in keys:
        parts["street"] += f" {parts['street_direction']}"

    return parts

def write_addressor(source, store, address, products):
    parts = addressor(address)
    if type(parts) == dict:
        known_file.writerow([source, store, parts["street"], parts["city"], parts["state"], parts["postal_code"], products])
    else:
        known_file.writerow([source, store, parts, "", "", "", products])

def write_address(source, customer, products):
    if is_address(customer):
        # The customer already is an address
        # Check to see if the chain is in the address
        sep_comma = customer.split(",")
        potential_address = ",".join(sep_comma[1:])
        if is_chain(sep_comma[0]) and is_address(potential_address):
            store = sep_comma[0]
            customer = potential_address
        else:
            store = " ".join([word for word in source.split(" ") if not word[0].isdigit()])
        write_addressor(source, strip_name(store), customer, products)
    else:
        if not customer.isdigit():
            customer = customer.lstrip(digits).strip()
        customer_info = is_known(customer)
        if customer_info:
            # known file
            known_file.writerow([source, customer, customer_info["address"], customer_info["city"], customer_info["state"], customer_info["zip"], products])
        else:
            # unknown file
            unknown_file.writerow([source, customer, "", "", "", "", products])








# Open known and unknown files
known_file = csv.writer(open("known.csv", "w"))
unknown_file = csv.writer(open("unknown.csv", "w"))
header = ["Source", "Customer", "Address", "City", "State", "Zip", "Products", "Comments"]
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

    chain_id = is_chain(source)
    if chain_id is False:
        # The file does not represent a chain
        for customer in customers:
            customer = str(customer)
            products = ", ".join(file.payload["customers"][customer])
            chain_id = is_chain(customer)
            if chain_id is False:
                # Location is not a chain
                write_address(source, customer, products)

            else:
                ## TEMPORARY
                if "FRED MEYER" in customer:
                    with open("./temp/fred_meyer.json", "r") as f:
                        fred_meyers = json.load(f)
                    for fred_meyer in fred_meyers:
                        if chain_id in str(fred_meyer["address"]).lower():
                            known_file.writerow([source, customer, fred_meyer["address"], fred_meyer["city"], fred_meyer["state"], fred_meyer["zip"], products])
                            continue
                    continue
                if "TOTAL WINE" in customer:
                    with open("./temp/tw.json", "r") as f:
                        tws = json.load(f)
                    try:
                        data = tws[chain_id]
                        known_file.writerow([source, customer, data["address"], data["city"], data["state"], data["zip"], products])
                    except:
                        write_address(source, customer, products)
                    continue

                # Location is a chain
                remote_id = re.sub("[^0-9]", "", customer).lstrip("0")
                cur.execute(f"SELECT address FROM stores WHERE chain_id='{chain_id}' AND remote_id='{remote_id}'")
                results = cur.fetchall()
                if len(results) > 0:
                    # Address found
                    address = results[0][0]
                    write_addressor(source, customer, address, products)
                else:
                    # Address not found
                    # Pass back to address book
                    write_address(source, customer, products)


    # chaind_id is True
    else:
        if chain_id == 42:
            # Whole Foods
            for store in customers:
                products = ", ".join(file.payload["customers"][store])
                cur.execute(f"SELECT address FROM stores WHERE chain_id='{chain_id}' and LOWER(address) LIKE '%{store.lower()}%'")
                results = cur.fetchall()
                if len(results) > 0:
                    address = results[0][0]
                    write_addressor(source, "Whole Foods", address, products)
                    # parts = addressor(address)
                    # known_file.writerow([source, store, address, "", "", "", products])
                else:
                    write_address(source, "Whole Foods " + store, products)

        elif str(customers[0]).isdigit():
            # The file represents a chain and has numeric id's
            for remote_id in customers:
                cur.execute(f"SELECT name FROM chains WHERE id='{chain_id}'")
                customer = cur.fetchone()[0] + " " + remote_id
                products = ", ".join(file.payload["customers"][remote_id])
                cur.execute(f"SELECT address FROM stores WHERE remote_id='{remote_id}' and chain_id='{chain_id}'")
                results = cur.fetchall()
                if len(results) > 0:
                    # Address found
                    address = results[0][0]
                    write_addressor(source, customer, address, products)
                else:
                    # Address not found
                    # Pass it back to the address book
                    write_address(source, customer, products)
        else:
            print("chain data not found", customers, source)
            print("THIS DOES NOTHING")

conn.close()
print("Done", counter)
