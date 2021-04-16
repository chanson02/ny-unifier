import pandas as pd
import json
import os
import re
from collections import Counter

import pdb

with open("hella_codes.json", "r") as f:
    hella_codes = json.load(f)


class Handler:
    def __init__(self, path):
        self.filename = os.path.split(path)[1]

        try:
            self.sheet = pd.ExcelFile(path).parse()
        except Exception as e:
            self.type = {"identifier":"skip", "args":["Error loading file"], "name_id":"error"}
            self.payload = self.empty_payload()
            self.payload["error"] = str(e)
            return

        self.sheet = self.strip_null(self.sheet)
        self.type = self.load_filetype()
        self.payload = self.empty_payload()
        self.parse()

    def __repr__(self):
        return f"{self.filename} file handler"

    def load_filetype(self):
        with open("filetypes.json", "r") as f:
            filetypes = json.load(f)
        file = self.known_file(filetypes)
        if not file:
            return self.register_filetype(filetypes)
        else:
            return filetypes[file]

    def known_file(self, filetypes):
        for file in list(filetypes.keys()):
            if file in self.filename:
                return file
        return False

    def register_filetype(self, filetypes):
        new_type = {}
        print(f"\n\n\nNew File Registry: {self.filename}")

        name_id = self.strip_filename()
        print(f"Name Identifier Autodetect: {name_id}")
        user_in = input("Press Enter to Continue or manually enter name name identifier (case-sensitive)\n")
        if user_in != "":
            name_id = user_in
            print(f"Name Identifier: {name_id}")
        new_type["name_id"] = name_id

        self.print_head()

        identifiers = {
            "skip":"No arguments required: press enter to continue",
            "column":"start row, customer column, product column",
            "int":"products_row, cust_column, start_row, start_column, end_column",
            "sep":"product_column, cust_column, start_row",
            "sep2":"start_row, product_column, cust_column",
            "indent":"product_column, cust_column, start_row"
        }
        keys = list(identifiers.keys())
        for index in range(len(keys)):
            print(f"{index}: {keys[index]}")
        identifier = keys[eval(input("Identify by: "))]
        new_type["identifier"] = identifier
        new_type["args"] = eval("[" + input(f"Input values (with commas)\n{identifiers[identifier]}\n") + "]")

        filetypes[name_id] = new_type
        with open("filetypes.json", "w") as f:
            json.dump(filetypes, f, indent=2)

        return new_type


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


    def is_int(self, word):
        try:
            int(word)
            return True
        except Exception:
            return False

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

    def empty_payload(self):
        return {
            "source_file_name":self.filename,
            "source_file_type":self.type,
            "customers":{}
        }

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

    def parse(self):
        args = self.type["args"]
        if self.type["identifier"] == "skip":
            return
        elif self.type["identifier"] == "column":
            self.identify_by_column(args[0], args[1], args[2])
        elif self.type["identifier"] == "int":
            self.identify_by_int(args[0], args[1], args[2], args[3], args[4])
        elif self.type["identifier"] == "sep":
            self.identify_by_sep(args[0], args[1], args[2])
        elif self.type["identifier"] == "sep2":
            self.identify_by_sep_2(args[0], args[1], args[2])
        elif self.type["identifier"] == "indent":
            self.identify_by_indent(args[0], args[1], args[2])
        else:
            raise f"No Identifier for {self.filename}"

    def add_purchase(self, customer, product):
        if customer != customer:
            return
        customer = str(customer).strip()
        if product in list(hella_codes.keys()):
            product = hella_codes[product]
        product = str(product).strip()

        if customer in self.payload["customers"]:
            self.payload["customers"][customer].append(product)
        else:
            self.payload["customers"][customer] = [product]

    # Find 1 item in each row
    def identify_by_column(self, start_index, cust_col=0, prod_col=1):
        rows = self.sheet.values[start_index:]
        for row in rows:
            customer = row[cust_col]

            try:
                products = row[prod_col]
            except IndexError:
                products = ""

            if products is not None and products == products and products != "":
                try:
                    products.split()
                except:
                    pdb.set_trace()
                for product in products.split(", "):
                    self.add_purchase(customer, product)
            else:
                self.add_purchase(customer, "")
        return

    # Find values associated with an integer (ex: quantity)
    def identify_by_int(self, products_row, cust_column, start_row, start_column, end_column):
        rows = self.sheet.values[start_row:]
        products = self.sheet.values[products_row]

        for row in rows:
            customer = None
            for column in range(end_column+1):
                item = row[column]
                if column == cust_column:
                    customer = item
                elif type(item) == int and column >= start_column:
                    self.add_purchase(customer, products[column])
        return

    # New product starts where space found
    def identify_by_sep(self, product_column, cust_column, start_row):
        # CUSTOMER
        # PRODUCT
        #
        # CUSTOMER
        # this may not be accurate ^
        rows = self.sheet.values[start_row:]
        for row in rows:
            if row[cust_column] is None or row[cust_column] != row[cust_column]:
                # This row is empty
                # Set a new product
                product = row[product_column]
            else:
                customer = row[cust_column] + " " + row[cust_column+1]
                self.add_purchase(customer, product)
        return

    def identify_by_sep_2(self, start_row, product_column, cust_column):
        rows = self.sheet.values[start_row:]
        for row in rows:
            if row[product_column] == row[product_column]:
                #there is a new product
                product = row[product_column]
            if row[cust_column] == row[cust_column]:
                customer = row[cust_column]
                self.add_purchase(customer, product)

        return

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
                self.add_purchase(customer, product)
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
    path = "/home/cooperhanson/Desktop/drive_downloaded/"
    file = "Associated Buyers 12_11_2020.xlsx"
    handler = Handler(path+file)
