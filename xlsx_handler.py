import pandas as pd
import json
import uuid
import os
import re
from customer import Customer
from collections import Counter

import pdb

with open("extra data/hella_codes.json", "r") as f:
    hella_codes = json.load(f)


class Handler:
    def __init__(self, path, customers=[]):
        self.filename = os.path.split(path)[1]
        self.customers = customers

        file_ext = self.filename.split('.')[-1]
        if  file_ext in ['xlsx', 'xls']:
            self.excel_file = pd.ExcelFile(path)
        elif file_ext == 'csv':
            self.excel_file = pd.read_csv(path)
        else:
            print(file_ext, 'not supported')
            return

        self.payload = self.empty_payload()
        self.load_filetype()

        try:
            self.set_sheet()
        except Exception as e:
            print("There was an error", e)
            return

        # self.sheet = self.strip_null(self.sheet) #this is making things MORE complicated
        self.load_rows()
        self.parse()

    def __repr__(self):
        return f"{self.filename} file handler"

    # Sheet is a dataframe object
    def set_sheet(self):
        if type(self.excel_file) == pd.core.frame.DataFrame:
            self.sheet = self.excel_file
        else:
            self.sheet = self.excel_file.parse(self.excel_file.sheet_names[self.payload['source_file']['options']['sheet']])
        return

    # Function to prepare an empty payload to be populated
    def empty_payload(self):
        return {
            "source_file": {
                "name": self.filename,
                "identifier": "skip",
                "options": {
                    "sheet": 0,
                    "start_row": 0,
                    "merge": {},
                    "chain": False,
                    "phone": False,
                    "website": False,
                    "product": False,
                    "products": False,
                    "address_data": False,
                    "chain+address": False,
                    "premise": False,
                    "customer_column": 0,
                    "unique_instruction": False
                }
            },
            "customers": {}
        }

    # Function to remove extraneous data from the spreadsheet
    def strip_null(self, dataframe):
        dataframe.drop_duplicates(inplace=True) # Remove duplicate rows
        dataframe.dropna(how='all', axis=1, inplace=True) # Remove empty columns
        dataframe.reset_index(drop=True, inplace=True)

        # Drop header rows with repeating data
        rows = dataframe.values
        for index in range(len(rows)):
            row = rows[index]
            c = Counter(row)
            if c.most_common()[0][1] > len(row) / 2:
                dataframe.drop(index=index, inplace=True)
            else:
                break
        dataframe.reset_index(drop=True, inplace=True)
        return dataframe

    # Function to check history
        # have we used this file before?
        # do we need to register this file?
    def load_filetype(self):
        with open("filetypes.json", "r") as f:
            filetypes = json.load(f)
        file = self.known_file(filetypes)
        if not file:
            self.register_filetype(filetypes)
        else:
            self.payload["source_file"] = filetypes[file]
            self.payload["source_file"]["name"] = self.filename

    # checks history for this file
    def known_file(self, filetypes):
        for file in list(filetypes.keys()):
            if file in self.filename:
                return file
        return False

    # Function to stringify all NULL values and repalce 'nan' with ''
    def load_rows(self):
        options = self.payload["source_file"]["options"]
        self.rows = self.sheet.values[options["start_row"]:]
        for i_row in range(len(self.rows)):
            self.rows[i_row] = [str(v).strip() for v in self.rows[i_row]]
            for i_val in range(len(self.rows[i_row])):
                if self.rows[i_row][i_val] == 'nan':
                    self.rows[i_row][i_val] = ''
                if self.rows[i_row][i_val][-2:] == ".0":
                    self.rows[i_row][i_val] = self.rows[i_row][i_val][:-2]

        self.merge_columns()
        return

    # Function to merge columns
    # ex: | Address, City, State | Zip
    def merge_columns(self):
        merges = self.payload["source_file"]["options"]["merge"]
        joiners = list(merges.keys())
        if len(joiners) == 0:
            return

        for i_row in range(len(self.rows)):
            for j in joiners:
                result = []
                for merge in merges[j]:
                    if self.rows[i_row][merge] != '':
                        result.append(self.rows[i_row][merge])
                self.rows[i_row][merges[j][0]] = j.join(result)

        return

    # save this file in history
    def register_filetype(self, filetypes):
        new_type = {}
        print(f"\n\n\nNew File Registry: {self.filename}")

        # name_id is the file key used for searching history
        name_id = self.strip_filename()
        print(f"Name Identifier Autodetect: {name_id}")
        user_in = input("Press Enter to Continue or manually enter name identifier (case-sensitive)\n")
        if user_in != "":
            name_id = user_in
            print(f"Name Identifier: {name_id}")
        new_type["name_id"] = name_id

        self.payload['source_file']['options']['sheet'] = self.select_sheet()
        self.set_sheet()
        self.print_head()
        self.set_options()

        identifiers = ["column", "int", "sep", "indent"]
        for index in range(len(identifiers)):
            print(f"{index}: {identifiers[index]}")
        self.payload["source_file"]["identifier"] = identifiers[int(input("Identify by: "))]

        filetypes[name_id] = self.payload["source_file"]
        with open("filetypes.json", "w") as f:
            json.dump(filetypes, f, indent=2)

        return

    # Function to check if a string can be an integer
    def is_int(self, s):
        try:
            int(s)
            return True
        except ValueError:
            return False


    # Function to try automatically remove dates from filenames
    def strip_filename(self):
        base, ext = os.path.splitext(self.filename)
        base = base.split(" ")

        months = {
            "january":"jan",
            "february":"feb",
            "march":"mar",
            "april":"apr",
            "may":"may",
            "june":"jun",
            "july":"jul",
            "auguest":"aug",
            "september":"sep",
            "october":"oct",
            "november":"nov",
            "december":"dec"
        }

        for index in range(len(base)):
            word = base[index]

            # 04 09 2020
            if (len(word) == 2 or len(word) == 4) and self.is_int(word):
                base[index] = ""

            # Dec
            elif len(word) == 3 and word.lower() in months.values():
                base[index] = ""

            # December
            elif word.lower() in months.keys():
                base[index] = ""

            # 12.15
            elif len(word) == 5:
                if self.is_int(word[0:1]) and self.is_int(word[3:]):
                    base[index] = ""

            # 04-2020
            elif len(word) == 7:
                if self.is_int(word[0:1]) and self.is_int(word[3:]):
                    base[index] = ""

            # 04_09_2020 | 04-09-2020 | 04/09/2020
            elif len(word) == 10:
                if self.is_int(word[0:1]) and self.is_int(word[3:4]) and self.is_int(word[6:]):
                    base[index] = ""

        base = " ".join(base)
        while base[-1] == " " or base[-1] == "-":
            base = base[:-1]

        return base

    def select_sheet(self):
        if type(self.excel_file) == pd.core.frame.DataFrame:
            return None
        sheet_count = len(self.excel_file.sheet_names)
        if sheet_count == 1:
            return 0

        print("Which sheet would you like to use?")
        for sheet_i in range(sheet_count):
            print(f"{sheet_i}: {self.excel_file.sheet_names[sheet_i]}")

        return eval(input('Sheet number: '))

    # function to display just the first few rows
    def print_head(self, row_count=5):
        print("\n")
        rows = self.sheet.values[:row_count]

        col_count = len(rows[0])
        row_line = "-1"
        for index in range(col_count):
            row_line += f'  {index:>8}'
        print(row_line)

        for row_index in range(row_count):
            new_line = f' {row_index}'
            row = rows[row_index]
            for column in row:
                new_line += f'  {str(column)[:8]:>8}'
            print(new_line)
        print("\n")

    # Function to ask user to input data used for collection
    def set_options(self):
        print("Enter a 1/0 for yes/no")
        if input("Skip file? ") == "1":
            return

        self.payload["source_file"]["options"]["start_row"] = int(input("What row does the data start? "))

        if input("Do any columns need to be merged? ") == "1":
            for i in range(eval(input("  How many merges? "))):
                joiner = input('  Character to combine columns: ')
                merge = eval(input('  Array of columns: '))
                if joiner in list(self.payload["source_file"]["options"]["merge"].keys()):
                    self.payload["source_file"]["options"]["merge"][joiner].append(merge)
                else:
                    self.payload["source_file"]["options"]["merge"][joiner] = [merge]

        if input("Does this file represent a chain? ") == "1":
            self.payload["source_file"]["options"]["chain"] = True

        if input("Does this file contain phone numbers? ") == "1":
            self.payload["source_file"]["options"]["phone"] = int(input("  Phone Column: "))

        if input("Does this file contain websites? ") == "1":
            self.payload["source_file"]["options"]["website"] = int(input("  Webbsite Column: "))

        if input("Does this file contain products? ") == "1":
            if input("  Do the products span multiple columns? ") == "1":
                self.payload["source_file"]["options"]["products"] = eval(input("  Product rows- enter like this '[5,6,7]' "))
            else:
                self.payload["source_file"]["options"]["product"] = int(input("  Product column: "))

        if input("Does this contain premise data? ") == "1":
            self.payload["source_file"]["options"]["premise"] = int(input("  Premise column: "))

        if input("Does this file contain addresses? ") == "1":
            if input("Does this file seperate addresses? ") == "1":
                print("(Input -1 for empty address column)")
                self.payload["source_file"]["options"]["address_data"] = {}
                self.payload["source_file"]["options"]["address_data"]["address1"] = int(input("  Address 1 column: "))
                self.payload["source_file"]["options"]["address_data"]["address2"] = int(input("  Address 2 column: "))
                self.payload["source_file"]["options"]["address_data"]["city"] = int(input("  City column: "))
                self.payload["source_file"]["options"]["address_data"]["state"] = int(input("  State column: "))
                self.payload["source_file"]["options"]["address_data"]["zip"] = int(input("  Zip column: "))
            else:
                if input("Does this file combine chain and addresses? ") == "1":
                    self.payload["source_file"]["options"]["chain+address"] = True
                self.payload["source_file"]["options"]["address_data"] = int(input("  Address column: "))

        if self.payload["source_file"]["options"]["chain+address"]:
            self.payload["source_file"]["options"]["customer_column"] = self.payload["source_file"]["options"]["address_data"]
        else:
            self.payload["source_file"]["options"]["customer_column"] = int(input("Customer column: "))

        return

    # handle file differently depending on layout
    def parse(self):
        identifier = self.payload["source_file"]["identifier"]
        if identifier == "skip":
            return
        elif identifier == "column":
            self.identify_by_column()
        elif identifier == "int":
            self.identify_by_int()
        elif identifier == "sep":
            self.identify_by_sep()
        elif identifier == "indent":
            self.identify_by_indent()
        else:
            raise f"No Identifier for {self.filename} | {identifier}"

    # Function to check validity of cell
    def valid_cell(self, cell):
        return cell == cell and cell != "" and cell != None

    # Function to standardize phone number 999-999-9999
    def standardize_phone(self, data):
        data = re.sub('[^0-9]', '', data)
        if len(data) < 10:
            return ""
        if data[0] == "1":
            data = data[1:]
        data = data[:10]
        return f"{data[:3]}-{data[3:6]}-{data[6:]}"


    # Function to return array of products
    # Cell example: Juice, Tea -> ['Juice', 'Tea']
    def products_from_row(self, row, product_column):
        if product_column is False:
            return [""]
        else:
            result = []
            [result.append(p.strip()) for p in row[product_column].split(",")]
            return result

    # Function to return phone number from row
    def phone_from_row(self, row, phone_column):
        if phone_column is not False:
            if self.valid_cell(row[phone_column]):
                return self.standardize_phone(row[phone_column])
        return ""

    # Function to return website from row
    def website_from_row(self, row, website_column):
        if website_column is not False:
            if self.valid_cell(row[website_column]):
                return row[website_column]
        return ""

    # Function to return address from row
    def address_from_row(self, row, address_data, phone=''):
        address = {"street": "", "city": "", "state": "", "zip": "", "phone": phone}
        if type(address_data) == int:
            full_address = re.sub(' +', ' ', row[address_data].strip())
            parts = self.addressor(full_address)
            if parts is None:
                # addressor error?
                # bad input?
                address["street"] = full_address
                return address
            address["street"] = parts["street"]
            address["city"] = parts["city"]
            address["state"] = parts["state"]
            address["zip"] = parts["postal_code"]

        # If the address is seperated for us
        elif type(address_data) == dict:
            if self.valid_cell(row[address_data["address1"]]) and address_data["address1"] != -1:
                address["street"] = row[address_data["address1"]]
            if self.valid_cell(row[address_data["address2"]]) and address_data["address2"] != -1:
                address["street"] += ", " + row[address_data["address2"]]
            if self.valid_cell(row[address_data["city"]]) and address_data["city"] != -1:
                address["city"] = row[address_data["city"]]
            if self.valid_cell(row[address_data["state"]]) and address_data["state"] != -1:
                address["state"] = row[address_data["state"]].split(', ')[-1] #sometimes 'city' | 'city, state'
            if self.valid_cell(row[address_data["zip"]]) and address_data["zip"] != -1:
                address["zip"] = row[address_data["zip"]]

        return address

    def premise_from_row(self, row, col):
        if col is False:
            return ""
        else:
            return row[col]

    # Call the addressor from the command line
    def addressor(self, address):
        command = f"ruby ../ny-addressor/lib/from_cmd.rb -o -a '{address}'"
        os.system(command)

        try:
            with open("addressor.json", "r") as f:
                parts = json.load(f)
            os.remove("addressor.json")
        except Exception:
            return None
        if parts is None:
            return None

        # Make sure it has all required parts
        required_keys = ["street_name", "street_number", "city", "state", "postal_code"]
        keys = list(parts.keys())
        for rk in required_keys:
            if rk not in keys:
                parts[rk] = ""

        # Combine street parts together
        parts["street"] = f"{parts['street_number']} {parts['street_name']}"
        if "street_label" in keys:
            parts["street"] += f" {parts['street_label']}"
        if "street_direction" in keys:
            parts["street"] += f" {parts['street_direction']}"

        return parts


    # Function to map purchases to customers
    def add_purchase(self, customer_name, product='', address='', premise='', website=''):
        # Return early if null
        if not self.valid_cell(customer_name) or product.lower() == 'total':
            return

        # Check for hella
        if product in list(hella_codes.keys()):
            product = hella_codes[product]

        # Standardize
        product = str(product).strip()
        customer_name = re.sub(' +', ' ', str(customer_name).strip())
        customer = self.search_customers(customer_name)

        # Update customer information
        entry_data = {
            'source': self.payload['source_file']['name'],
            'address': address,
            'product': product,
        }
        customer.add_entry(entry_data)
        customer.website = website if customer.website == '' and website != '' else False
        customer.premise = premise if customer.premise == '' and premise != '' else False

        return

    def search_customers(self, name):
        for cust in self.customers:
            if name == cust.name:
                return cust
        new_cust = Customer(name)
        self.customers.append(new_cust)
        return new_cust

    # Customer and Product in each row
    def identify_by_column(self):
        options = self.payload["source_file"]["options"]
        for row in self.rows:

            # Remove chain from address if exists
            if options["chain+address"]:
                target_col = row[options["customer_column"]]
                if target_col == "":
                    continue
                data = target_col.split(",")
                customer = data[0]
                row[options["customer_column"]] = (",".join(data[1:])).strip()
            else:
                customer = row[options["customer_column"]]
            # Remove phone from address if exists
            if options["phone"] == options["address_data"] and options['phone']:
                target_col = row[options["phone"]].strip()
                if target_col == "":
                    continue
                data = target_col.split(' ')
                phone = data[-1]
                row[options["address_data"]] = ' '.join(data[:-1]).strip()
            else:
                phone = self.phone_from_row(row, options["phone"])
            address = self.address_from_row(row, options["address_data"], phone)
            products = self.products_from_row(row, options["product"])
            premise = self.premise_from_row(row, options["premise"])
            website = self.website_from_row(row, options["website"])

            for product in products:
                self.add_purchase(customer, product=product, address=address, premise=premise, website=website)
        return

    # Find values associated with an integer (ex: quantity)
    # def identify_by_int(self, products_row, cust_column, start_row, start_column, end_column):
    def identify_by_int(self):
        options = self.payload["source_file"]["options"]
        products = self.sheet.columns

        for row in self.rows:
            customer = row[options["customer_column"]]
            phone = self.phone_from_row(row, options["phone"])
            address = self.address_from_row(row, options["address_data"], phone)
            premise = self.premise_from_row(row, options["premise"])
            website = self.website_from_row(row, options["website"])

            for product_column in options["products"]:
                if row[product_column].isdigit():
                    self.add_purchase(customer, product=products[product_column], address=address, premise=premise, website=website)
        return

    # New product starts where space found
    def identify_by_sep(self):
        # if product_col is not a number: set new product
        options = self.payload['source_file']['options']
        product = ""

        for row in self.rows:
            # Set new product
            product_cell = self.products_from_row(row, options['product'])
            if not product_cell[0].isdigit() and product_cell[0] != "":
                product = product_cell[0]

            # Add purchase to current product (if there is a customer in this row)
            customer = row[options["customer_column"]]
            if customer == '':
                continue
            address = self.address_from_row(row, options['address_data'])
            self.add_purchase(customer, product=product, address=address)

        return

    # DOES NOT FUNCTION !!!
    def identify_by_indent(self, product_column, cust_column, start_row):
        # CUSTOMER
            # PRODUCT
        # CUSTOMER
        rows = self.sheet.values[start_row:]
        for row in rows:
            if not (row[cust_column] is None or row[cust_column] != row[cust_column]):
                # There is a customer
                customer = row[cust_column]
            elif not (row[product_column] is None or row[product_column] != row[product_column]):
                product = row[product_column]
                self.add_purchase(customer, product=product)
        return


    def write(self, path=None, filename=None):
        if path is None:
            path = "/home/cooperhanson/Desktop/"
        if filename is None:
            path += f"{self.filename.replace('.', '_')}.json"

        with open(path, "w") as f:
            json.dump(self.payload, f, indent=2)

        return path





if __name__ == "__main__":
    path = "/home/chanson/Documents/Projects/NearestYou/ny-unifier/XLSX examples/"
    file = "column_full_address.xlsx"
    file = "column_phone_sep.xlsx"
    file = "column_dzip_dphone_chainaddress.xlsx"
    handler = Handler(path+file)
    customer_data = handler.payload["customers"]
    customers = list(handler.payload["customers"].keys())
