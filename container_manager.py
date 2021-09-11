from busybody_getter import BusybodyGetter
from xlsx_handler import Handler
import pandas as pd
import csv

# Object to keep Customers for a container organized
# Object to  generate reports on a container

#!  container_files is a list of paths
#!  container_folder is the DriveFolder of the container/

"""
ContainerManager
.get_all() [] - returns known, unknown, customers and chains
.get_known_customers []
.get_unknown_customers []
.get_customers []
.get_entries(customers) []
.unknowns bool

.load_knowns(complete_file)

.generate_new_report(old_container_manager)
.generate_gap_report(old_container_manager)
.generate_unknowns()
.generate_knowns()
.generate_transformer()
"""

HEADER = ["Source", "Customer", "Street", "City", "State", "Zip", "Phone", "Product", "Premise", "Website", "Comments"]
#           0           1           2       3       4       5       6           7           8           9

class ContainerManager:
    def __init__(self, container_files, drive_container):
        self.files = container_files
        self.drive_container = drive_container
        self.bbg = BusybodyGetter()
        self.customers = [] #customers && chains

        print(f'Parsing {len(self.files)} files')
        for f in self.files:
            Handler(f, self.customers)
            print('.', end='', flush=True)
        print()

        print(f'Consulting Busybody on {len(self.customers)} customers')
        [c.execute(self.bbg) for c in self.customers]
        self.bbg.conn.close()
        print()

        return

    def get_all(self):
        result = []
        result += self.get_customers()
        result += self.get_chains()
        return result

    def get_customers(self):
        result = []
        for customer in self.customers:
            if customer.final:
                result.append(customer)
        return result

    def get_chains(self):
        result = []
        for customer in self.customers:
            if not customer.final:
                result.append(customer)
        return result

    def get_known_customers(self):
        result = []
        for customer in self.get_customers():
            if self.known(customer.final):
                result.append(customer)
        return result

    def get_unknown_customers(self):
        result = []
        for customer in self.get_customers():
            if not self.known(customer.final):
                result.append(customer)
        return result

    # Function to check if all address data found
    def known(self, address):
        rk = ['street', 'city', 'state', 'zip']
        missing = [k for k in rk if address[k] == '']
        return True if len(missing) == 0 else False

    # function to check if unknowns are needed to be generated
    def unknowns(self):
        if self.get_unknown_customers():
            return True
        if self.get_chain_rows(known=False):
            return True
        return False

    # Customer group: self.customers, self.get_customers(), self.known_customers()
    def get_entries(self, customer_group):
        result = []
        for customer in customer_group:
            result += customer.entries
        return result

    # Function to convert entry to HEADER format
    def gen_row(self, customer, source, address, product):
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

    # Function to convert all iterator into HEAD format
    # Iterator can be either known or unknown  customers
    # minimize will condense products and sources
    def get_customer_rows(self, iterator, minimize=False):
        rows = []
        for customer in iterator:
            sources = [e['source'] for e in customer.entries]
            products = [e['product'] for e in customer.entries]
            # if self.known(customer.final):
            if not minimize:
                rows += [
                    self.gen_row(customer, sources[i], customer.final, products[i])
                    for i in range(len(sources))
                ]
            else:
                rows += [self.gen_row(customer, sources, customer.final, products)]

        return rows

    # Function to convert all known chains to HEAD format
    # Minimize will condense products and sources
    def get_chain_rows(self, known=True, minimize=False):
        rows = []
        for customer in self.get_chains():
            structs = []
            for variation in customer.variations:
                structs.append({
                    'address': variation,
                    'sources': [],
                    'products': []
                })

            for entry in customer.entries:
                # Fill each struct with sources and products
                struct = [s for s in structs if s['address'] == entry['address']][0]
                struct['sources'].append(entry['source'])
                struct['products'].append(entry['product'])
            structs = remove_structs(known, structs)

            for struct in structs:
                if minimize:
                    rows += [self.gen_row(customer, struct['sources'], struct['address'], struct['products'])]
                else:
                    rows += [
                        self.gen_row(customer, struct['sources'][i], struct['address'], struct['products'][i])
                        for i in range(len(struct['sources']))
                    ]
        return rows

    # Function to remove unwanted structs
    # only want known or unknown?
    def remove_structs(known, structs):
        result = []
        for struct in structs:
            if known and self.known(struct['address']):
                result.append(struct)
            else:
                result.append(struct)
        return result


    # Function to generate  knowns file
    # Returns file path
    def generate_knowns(self):
        path = f"./pending/{self.drive_container.path.replace('/', '|')}_unifier.csv"
        known_file = csv.writer(open(path, 'w'))
        # rows = [HEADER] + self.get_customer_rows(self.get_known_customers())
        rows = [HEADER]
        rows += self.get_customer_rows(self.get_known_customers(), minimize=False)
        rows += self.get_chain_rows(known=True, minimize=False)
        known_file.writerows(rows)
        return path

    def generate_unknowns(self):
        path = f"./tmp/{self.drive_container.path.replace('/', '|')}_unifier_incomplete.csv"
        unknown_file = csv.writer(open(path, 'w'))
        rows = [HEADER]
        rows += self.get_customer_rows(self.get_unknown_customers(), minimize=True)
        rows += self.get_chain_rows(known=False, minimize=True)
        unknown_file.writerows(rows)
        return path

    def generate_finished(self):
        path = f"./tmp/{self.drive_container.path.replace('/', '|')}_unifier_finished.csv"
        finished_file = csv.writer(open(path, 'w'))
        rows = [HEADER]
        rows += self.get_customer_rows(self.get_known_customers(), minimize=False)
        rows += self.get_chain_rows(known=True, minimize=False)
        rows += self.get_customer_rows(self.get_unknown_customers(), minimize=False)
        rows += self.get_chain_rows(known=False, minimize=False)
        finished_file.writerows(rows)
        return path

    def generate_transformer(self):
        path = f"./tmp/{self.drive_container.path.replace('/', '|')}_unifier_transformer.csv"
        transformer_file = csv.writer(open(path, 'w'))
        rows = [HEADER]
        rows += self.get_customer_rows(self.get_known_customers(), minimize=True)
        rows += self.get_chain_rows(known=True, minimize=True)
        rows += self.get_customer_rows(self.get_unknown_customers(), minimize=True)
        rows += self.get_chain_rows(known=False, minimize=True)
        transformer_file.writerows(rows)
        return path

    # Function to clean data from a parsed file
    def clean(self, row):
        row = [str(v) for v in row]
        for i in range(len(row)):
            if row[i] == 'nan':
                row[i] = ''
            row[i] = row[i].strip()
        return row

    def generate_new_report(self, old_container):
        current_customers = [c.name for c in self.get_all()]
        old_customers = [c.name for c in old_container.get_all()]

        path = f"./tmp/{self.drive_container.path.replace('/', '|')}_unifier_new.csv"
        gap_file = csv.writer(open(path, 'w'))
        rows = [HEADER]
        for customer in current_customers:
            if customer not in old_customers:
                rows.append([customer])
        gap_file.writerows(rows)
        return path

    def generate_gap_report(self, old_container):
        current_customers = [c.name for c in self.get_all()]
        old_customers = [c.name for c in old_container.get_all()]

        path = f"./tmp/{self.drive_container.path.replace('/', '|')}_unifier_gap.csv"
        gap_file = csv.writer(open(path, 'w'))
        rows = [HEADER]
        for customer in old_customers:
            if customer not in current_customers:
                rows.append([customer])
        gap_file.writerows(rows)
        return path
