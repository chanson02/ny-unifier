import os, json
import pandas as pd
import pdb

unknowns = os.listdir("unknowns/")
for unknown in unknowns:
    rows = pd.read_csv("unknowns/" + unknown).values

    if rows[0][1] != rows[0][1]:
        # This has not been filled out yet
        continue

    # Open the original file and the address book
    with open("xlsx_extract/" + unknown.replace("csv", "json"), "r") as f:
        file_payload = json.load(f)
    name_id = file_payload["source_file_type"]["name_id"]
    with open("address_book.json", "r") as f:
        address_book = json.load(f)
    customers = address_book[name_id]

    # Append to the address book
    for row in rows:
        if row[1] == row[1] and row[1] != "" and row[1] is not None:
            customers[row[0]] = row[1]
        else:
            print(f"Warning: Missing address for {row[0]} - {unknown}")
    address_book[name_id] = customers
    with open("address_book.json", "w") as f:
        json.dump(address_book, f, indent=2)

    # Overwrite old xlsx_extract
    file_customers = list(file_payload["customers"].keys())
    known_customers = list(customers.keys())
    addresses = {}
    for customer_name in file_customers:
        if customer_name in known_customers:
            addresses[customers[customer_name]] = file_payload["customers"][customer_name]
        else:
            addresses[customer_name] = file_payload["customers"][customer_name]
    file_payload["customers"] = addresses
    with open("xlsx_extract/" + unknown.replace("csv", "json"), "w") as f:
        json.dump(file_payload, f, indent=2)

    # Remove completed file
    os.remove("unknowns/" + unknown)
