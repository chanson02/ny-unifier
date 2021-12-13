import os, json
import un_util
import pandas as pd
from entry import Entry
from address import Address
from customer import Customer
from file_loader import FileLoader

"""
Unifier class to parse files
Execute instructions to load customers and data from file

Parsers:
    row - each row is one line of data
    ! if Customer cell is empty -> use previous customer
    ! if Product cell is empty -> use previous product
        | Customer1 | Product1
        | Customer2 | Product2

    int - Cells with values > 0 get assigned to column
    ! instructions.product must be array
        | Customers | Product1 | Product2       <----- Header
        | Customer1 |    0     |    5

    product_indent - Product is assigned to last customer received # Forage & Foster
    ! product cell right of customer must be null
        | Customer1 |
                        | Product 1 |
                        | Product 2 |
        | Customer2 |

    unifier - Load raw data
"""

class FileHandler:

    def __init__(self, path):
        self.entries = [] # Entries from this file
        self.file = FileLoader(path)

        if self.file.excel_file is None:
            # Could not parse file
            return

        self.merge_columns() # Merge columns as specified by the instructions
        self.parse(self.file.instructions.parser)
        return

    def __repr__(self):
        return f'{self.file.filename} FileHandler Object'

    # Merge columnns instructed
    # ex: | Address, City, State | Zip -> | Address, City, State, Zip |
    def merge_columns(self):
        merges = self.file.instructions.merge_columns
        joiners = list(merges.keys())
        if len(joiners) == 0:
            return # leave early

        for row_ndx in range(len(self.file.rows)):
            for j in joiners:
                result = []
                for merge in merges[j]:
                    if self.file.rows[row_ndx][merge] != '':
                        result.append(self.file.rows[row_ndx][merge])
                self.file.rows[row_ndx][merges[j][0]] = j.join(result)
        return

    # Handle file differently depending on layout
    def parse(self, parser):
        if parser == 'skip':
            return
        elif parser == 'unifier':
            self.parse_by_unifier()
        elif parser == 'row':
            self.parse_by_rows()
        elif parser == 'product_indent':
            self.parse_by_product_indent()
        else:
            print(f'! No parser for {self.file.filename} | {parser}')
        return

    ###############
    ### PARSERS ###

    # Each row contains full data
    # ! If missing customer -> use previous
    # ! If missing product -> use previous
    def parse_by_rows(self):
        source = self.file.filename
        previous_customer = ''
        previous_product = ['']
        for row in self.file.rows:
            customer = self.customer_from_row(row)
            products = self.products_from_row(row)
            phone = self.phone_from_row(row)
            address = self.address_from_row(row, phone)
            premise = self.premise_from_row(row)
            website = self.website_from_row(row)

            if customer == '' or customer is None:
                customer = previous_customer
            else:
                previous_customer = customer

            if products == [] or products is None:
                products = previous_product
            else:
                previous_product = products

            for prod in products:
                ent = Entry(
                    customer_name=customer,
                    product=prod,
                    address=address,
                    phone=phone,
                    premise=premise,
                    website=website,
                    source=source
                )
                self.entries.append(ent)
        return

    def parse_by_unifier(self):
        ins = self.file.instructions
        for row in self.file.rows:
            phone = self.phone_from_row(row)
            products = eval(row[ins.product])
            sources = eval(row[0])
            for ndx in range(len(products)):
                ent = Entry(
                    source = sources[ndx],
                    customer_name = self.customer_from_row(row),
                    product = products[ndx],
                    address = self.address_from_row(row, phone),
                    premise = self.premise_from_row(row),
                    website = self.website_from_row(row)
                )
                self.entries.append(ent)
        return

    def parse_by_product_indent(self):
        source = self.file.filename
        previous_customer = ''
        for row in self.file.rows:

            customer_name = self.customer_from_row(row)
            if un_util.valid_cell(customer_name):
                previous_customer = customer_name

            products = self.products_from_row(row)
            if len(products) == 0:
                continue

            for prod in products:
                ent = Entry(
                    customer_name=previous_customer,
                    product=prod,
                    source=source
                )
                self.entries.append(ent)

        return
    ###################################

    ###########################
    ### Get data from a row ###
    def customer_from_row(self, row):
        cust = row[self.file.instructions.customer]
        if not un_util.valid_cell(cust):
            return None

        if self.file.instructions.chain_address:
            return cust.split(',')[0]
        elif self.file.instructions.chain:
            # Walmart 2101
            return f'{self.file.instructions.chain} {cust}'
        return cust

    # 'Juice, Tea' -> ['Juice', 'Tea']
    def products_from_row(self, row):
        prod = self.file.instructions.product
        if prod is False:
            return None
        elif type(prod) == int:
            result = []
            if un_util.valid_cell(row[prod]):
                [result.append(p.strip()) for p in row[prod].split(', ')]
                return result
        else:
            print('file_handler: PRODUCTS_FROM_ROW NOT COMPLETE')
        return []

    def phone_from_row(self, row):
        ins = self.file.instructions.phone
        if ins is not False:
            if un_util.valid_cell(row[ins]):
                return un_util.standardize_phone(row[ins])
        return None

    def website_from_row(self, row):
        ins = self.file.instructions.website
        if ins is not False:
            if un_util.valid_cell(row[ins]):
                return row[ins]
        return None

    def premise_from_row(self, row):
        ins = self.file.instructions.premise
        if ins is not False:
            if un_util.valid_cell(row[ins]):
                return row[ins]
        return None

    def address_from_row(self, row, phone=''):
        ins = self.file.instructions.address
        address = None

        if self.file.instructions.chain_address:
            cust = row[self.file.instructions.customer]
            if un_util.valid_cell(cust):
                address = ', '.join(cust.split(',')[1:]).strip()

        elif ins is False:
            return None

        elif type(ins) == int:
            if un_util.valid_cell(row[ins]):
                address = row[ins]

        else: #type() == dict
            result = Address(phone=phone)
            if un_util.valid_cell(row[ins['address1']]) and ins['address1'] != -1:
                result.street = row[ins['address1']].strip()

            if un_util.valid_cell(row[ins['address2']]) and ins['address2'] != -1:
                adr2 = str(row[ins['address2']]).strip()
                if un_util.valid_cell(adr2):

                    if not un_util.valid_cell(result.street):
                        result.street = adr2
                    elif len(un_util.strip_letters(adr2)) == 10 and not un_util.valid_cell(result.phone):
                        # 2080 KILDAIRE FARM RD, 919-233-9483 # UNFI puts phone in address2?
                        result.phone = adr2
                    else:
                        result.street += ', ' + adr2

            if un_util.valid_cell(row[ins['city']]) and ins['city'] != -1:
                result.city = row[ins['city']]
            if un_util.valid_cell(row[ins['state']]) and ins['state'] != -1:
                result.state = row[ins['state']]
            if un_util.valid_cell(row[ins['zip']]) and ins['zip'] != -1:
                result.zip = row[ins['zip']]
            return result

        # Send address to the addressor
        if address is not None and address != '':
            result = un_util.addressor(address)
            if result is not None:
                return result
        return Address()

    ###########################

#     # Find values associated with an integer (ex: quantity)
#     # ! instructions.product must be array
#     def identify_by_int(self):
#         options = self.instructions
#         products = self.sheet.columns
#
#         for row in self.rows:
#             customer = row[options.customer]
#             phone = self.phone_from_row(row)
#             address = self.address_from_row(row, phone)
#             premise = self.premise_from_row(row)
#             website = self.website_from_row(row)
#
#             for product_column in options.product:
#                 if row[product_column].isdigit():
#                     self.add_purchase(customer, product=products[product_column], address=address, premise=premise, website=website)
#         return

if __name__ == '__main__': # Used for testing
    test1 = FileHandler('input/hella/Hella August/Craft Collective August Report.xlsx')
    test2 = FileHandler('input/hella/Hella October 2021_unifier_minimized.csv')
