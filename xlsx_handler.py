import pandas as pd
import json
import uuid
import os
import re
from customer import Customer
from collections import Counter

import instructions

import pdb

with open("extra data/hella_codes.json", "r") as f:
    hella_codes = json.load(f)

XLSX_TYPE = pd.io.excel._base.ExcelFile
CSV_TYPE = pd.core.frame.DataFrame

class Handler:
    def __init__(self, path, customers=[]):
        self.filename = os.path.split(path)[1]
        self.customers = customers

        file_ext = self.filename.split('.')[-1]
        if  file_ext in ['xlsx', 'xls', 'xlsm']:
            self.excel_file = pd.ExcelFile(path)
        elif file_ext == 'csv':
            self.excel_file = pd.read_csv(path)
        else:
            print(file_ext, 'not supported', end='', flush=True)
            return

        self.load_filetype() # sets self.sheet and self.instructions

        self.load_rows() #sets self.rows
        self.parse()
        return

    def __repr__(self):
        return f"{self.filename} file handler"

    # Function to check history
        # have we used this file before?
        # do we need to register this file?
    def load_filetype(self):
        with open("filetypes.json", "r") as f:
            filetypes = json.load(f)

        # search for filename in filetypes
        file_key = self.search_file_key(filetypes)
        if file_key is None:
            # File key is not registered
            file_key, filetypes = self.register_filetype(filetypes)

        matching_header = self.find_matching_header(filetypes['file_keys'][file_key])
        if matching_header is None:
            # Register a filetype
            _, filetypes = self.register_filetype(filetypes, file_key)
            matching_header = self.find_matching_header(filetypes['file_keys'][file_key])

        self.sheet = self.select_sheet(matching_header)
        self.instructions = self.select_instructions(matching_header, filetypes)
        return

    # Function to search for filename in filetypes.json
    def search_file_key(self, filetypes):
        keys = filetypes['file_keys'].keys()
        for k in keys:
            if k in self.filename:
                return k
        return None

    def find_matching_header(self, file_data):
        file_headers = self.get_file_headers()
        file_headers = [[self.strip_date(header) for header in headers] for headers in file_headers]
        for index in range(len(file_data)):
            header_value = file_data[index]['header_value']
            if header_value in file_headers:
                return file_data[index]
        return None

    def get_file_headers(self):
        if type(self.excel_file) != XLSX_TYPE:
            return [self.remove_unnamed_columns(self.excel_file.columns.tolist())]
        return [self.remove_unnamed_columns(self.excel_file.parse(sheet).columns.tolist())
        for sheet in self.excel_file.sheet_names]

    def select_sheet(self, header):
        if type(self.excel_file) != XLSX_TYPE:
            return self.excel_file
        sheet_count = len(self.excel_file.sheet_names)
        for sheet in self.excel_file.sheet_names:
            sheet = self.excel_file.parse(sheet)
            h = self.remove_unnamed_columns(sheet.columns.tolist())
            h = [self.strip_date(v) for v in  h]
            if h == header['header_value']:
                return sheet
        return None

    def select_instructions(self, header_data, filetypes):
        i = instructions.Instructions()
        i.load_from_json(filetypes['headers'][str(header_data['header_id'])])
        return i

    # Function to stringify all NULL values and repalce 'nan' with ''
    def load_rows(self):
        self.rows = self.sheet.values[self.instructions.start_row:].tolist()
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
        merges = self.instructions.merge_columns
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
    def register_filetype(self, filetypes, file_key=None):
        print(f'\nNew Filetype discovered!  |  {self.filename}')
        if file_key is None:
            file_key = self.ask_file_key()
            filetypes['file_keys'][file_key] = []

        # Find the header(s)
        sheet_number = self.ask_sheet()
        if sheet_number is not None:
            sheet = self.excel_file.parse(self.excel_file.sheet_names[sheet_number])
        else:
            sheet = self.excel_file

        header_value = self.remove_unnamed_columns(sheet.columns.tolist())
        header_value = [self.strip_date(v) for v in header_value]
        self.print_header(header_value)

        if input("Does this header exist? ") == '1':
            header_id = input('  header_id: ')
        else:
            header_id = str(len(list(filetypes['headers'].keys())))

            instruct = instructions.Instructions()
            instruct.ask_instructions(header_id)
            filetypes['headers'][header_id] = instruct.jsonify()

        filetypes['file_keys'][file_key].append({'header_id': header_id, 'header_value': header_value})

        with open('filetypes.json', 'w') as f:
            json.dump(filetypes, f, indent=2)
        return file_key, filetypes

    def ask_file_key(self):
        print(f'\n\nNew File Registry: {self.filename}')
        base, _ = os.path.splitext(self.filename)
        file_key = self.strip_date(base)
        print(f'Name Identifier Autodetect: {file_key}')
        user_in = input("Press Enter to Continue or manually enter name identifier (case-sensitive)\n")
        if user_in != "":
            file_key = user_in
            print(f"Name Identifier: {file_key}")
        return file_key


    # must know which sheet to get header from when registering
    def ask_sheet(self):
        if type(self.excel_file) != XLSX_TYPE:
            return None
        sheet_count = len(self.excel_file.sheet_names)
        if sheet_count == 1:
            return 0

        print("Which sheet would you like to use?")
        for sheet_i in range(sheet_count):
            print(f"{sheet_i}: {self.excel_file.sheet_names[sheet_i]}")

        return eval(input('Sheet number: '))

    # Function to get rid of unnamed columns
    def remove_unnamed_columns(self, cols):
        unnamed_count = 0
        for c in cols[::-1]:
            if 'Unnamed: ' in c:
                unnamed_count += 1
            else:
                break
        if unnamed_count > 0:
            return cols[:-unnamed_count]
        else:
            return cols

    # Function to check if a string can be an integer
    def is_int(self, s):
        if len(s) == 0:
            return False
        try:
            int(s)
            return True
        except ValueError:
            return False


    # Function to try automatically remove dates from filenames
    def strip_date(self, string):
        base = str(string).split(" ")

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
                if self.is_int(word[:1]) and self.is_int(word[3:]):
                    base[index] = ""

            # 04-2020, 202004, 042020, 04/2020, 2020/04
            elif (len(word) == 7 or len(word) == 6) and (self.is_int(word.replace('/', '')) or self.is_int(word.replace('-', ''))):
                # if self.is_int(word[0:1]) and self.is_int(word[3:]):
                base[index] = ""

            # 04_09_2020 | 04-09-2020 | 04/09/2020
            elif len(word) == 10:
                if self.is_int(word[0:1]) and self.is_int(word[3:4]) and self.is_int(word[6:]):
                    base[index] = ""

        base = " ".join(base)
        if base == '':
            return base
        while base[-1] == " " or base[-1] == "-":
            base = base[:-1]

        return base

    # function to display just the first few rows
    def print_head(self, row_count=5):
        print("\n")
        rows = self.sheet.values[:row_count]

        col_count = len(rows[0])
        row_line = "-1"
        for index in range(col_count):
            row_line += f'  {index:>8}'
        print(row_line)

        for row_index in range(len(rows)):
            new_line = f' {row_index}'
            row = rows[row_index]
            for column in row:
                new_line += f'  {str(column)[:8]:>8}'
            print(new_line)
        print("\n")

    def print_header(self, columns):
        print('\n')
        col_count = len(columns)
        count_line = ''
        for index in range(col_count):
            count_line += f'  {index:>8}  '
        print(count_line)

        header_line = ''
        for column in columns:
            header_line += f'  {str(column)[:10]:>10}'
        print(header_line)
        return

    # handle file differently depending on layout
    def parse(self):
        identifier = self.instructions.identifier
        if identifier == "skip":
            return
        elif identifier == "column":
            self.identify_by_column()
        elif identifier == "int":
            self.identify_by_int()
        # elif identifier == "sep":
        #     self.identify_by_sep()
        # elif identifier == "indent":
        #     self.identify_by_indent()
        else:
            print(f"No Identifier for {self.filename} | {identifier}")

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
    def products_from_row(self, row):
        prod = self.instructions.product
        if prod is False:
            return ['']
        elif type(prod) == int:
            result = []
            [result.append(p.strip()) for p in row[prod].split(', ')]
            return result
        else:
            print('products_from_row not complete')
            return ['']

    # Function to return phone number from row
    def phone_from_row(self, row):
        if self.instructions.phone is not False:
            if self.valid_cell(row[self.instructions.phone]):
                return self.standardize_phone(row[self.instructions.phone])
        return ''

    # Function to return website from row
    def website_from_row(self, row):
        col = self.instructions.website
        if col is not False:
            if self.valid_cell(row[col]):
                return row[col]
        return ""

    # Function to return address from row
    def address_from_row(self, row, phone=''):
        address = {"street": "", "city": "", "state": "", "zip": "", "phone": phone}
        addr_data = self.instructions.address

        if type(addr_data) == int:
            full_address = re.sub(' +', ' ', row[addr_data].strip())
            parts = self.addressor(full_address)
            if parts is None:
                address['street'] = full_address
            else:
                address['street'] = parts['street']
                address['city'] = parts['city']
                address['state'] = parts['state']
                address['zip'] = parts['postal_code']

        elif type(addr_data) == dict:
            if self.valid_cell(row[addr_data['address1']]) and addr_data['address1'] != -1:
                address['street'] = row[addr_data['address1']]
            if self.valid_cell(row[addr_data['address2']]) and addr_data['address2'] != -1:
                address['street'] += ', ' + row[addr_data['address2']]
            if self.valid_cell(row[addr_data['city']]) and addr_data['city'] != -1:
                address['city'] = row[addr_data['city']]
            if self.valid_cell(row[addr_data['state']]) and addr_data['state'] != -1:
                address['state'] = row[addr_data['state']]
            if self.valid_cell(row[addr_data['zip']]) and addr_data['zip'] != -1:
                address['zip'] = row[addr_data['zip']]

        return address

    def premise_from_row(self, row):
        col = self.instructions.premise
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
            'source': self.filename,
            'address': address,
            'product': product,
        }
        customer.add_entry(entry_data)
        customer.website = website if customer.website == '' and website != '' else customer.website
        customer.premise = premise if customer.premise == '' and premise != '' else customer.premise

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
        options = self.instructions
        for row in self.rows:

            if options.chain_address:
                # Remove chain from address
                target_col = row[options.customer]
                if target_col == '':
                    continue
                data = target_col.split(',')
                customer = data[0] # chain name
                row[options.customer] = (','.join(data[1:])).strip() # put address back
            else:
                if options.chain:
                    customer = f'{options.chain} {row[options.customer]}'
                else:
                    customer = row[options.customer]

            if options.phone == options.address:
                # Remove phone from address
                target_col = row[options.phone].strip()
                if target_col == '':
                    continue
                data = target_col.split(' ')
                phone = data[-1]
                row[options.address] = ' '.join(data[:-1]).strip()
            else:
                phone = self.phone_from_row(row)

            address = self.address_from_row(row, phone)
            products = self.products_from_row(row)
            premise = self.premise_from_row(row)
            website = self.website_from_row(row)

            for product in products:
                self.add_purchase(customer, product=product, address=address, premise=premise, website=website)
        return

    # Find values associated with an integer (ex: quantity)
    # ! instructions.product must be array
    def identify_by_int(self):
        options = self.instructions
        products = self.sheet.columns

        for row in self.rows:
            customer = row[options.customer]
            phone = self.phone_from_row(row)
            address = self.address_from_row(row, phone)
            premise = self.premise_from_row(row)
            website = self.website_from_row(row)

            for product_column in options.product:
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
