from busybody_getter import BusybodyGetter
from xlsx_handler import Handler
import csv

# Object to keep Customers for a container organized
# Object to  generate reports on a container

#!  container_files is a list of paths
#!  container_folder is the DriveFolder of the container

"""
ContainerManager
.get_known_customers
.get_unknown_customers
.get_customers
.get_entries
.get_known_entries
.get_unknown_entries

.load_knowns(complete_file)

.generate_new_report(old_container_manager)
.generate_gap_report(old_container_manager)
.generate_unknowns()
.generate_knowns()
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
    def get_customer_rows(self, iterator):
        rows = []
        for customer in iterator:
            sources = [e['source'] for e in customer.entries]
            products = [e['product'] for e in customer.entries]
            if self.known(customer.final):
                rows += [
                    self.gen_row(customer, sources[i], customer.final, products[i])
                    for i in range(len(sources))
                ]
            else:
                rows += [self.gen_row(customer, sources, customer.final, products)]

        return rows

    # Function to convert all known chains to HEAD format
    def get_known_chain_rows(self, known=True):
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

            for struct in structs:
                if known(struct['address']) and known:
                    rows += [
                        self.gen_row(customer, struct['sources'][i], struct['address'], struct['products'][i])
                        for i in range(len(struct['sources']))
                    ]
                else:
                    row += [self.gen_row(customer, struct['sources'], struct['address'], struct['products'])]
        return rows

    # Function to generate  knowns file
    # Returns file path
    def generate_knowns(self):
        path = f"./pending/{self.drive_container.path.replace('/', '|')}.csv"
        known_file = csv.writer(open(path, 'w'))
        # rows = [HEADER] + self.get_customer_rows(self.get_known_customers())
        rows = [HEADER]
        rows += self.get_customer_rows(self.get_known_customers())
        rows += self.get_chain_rows(known=True)
        known_file.writerows(rows)
        return path

    def generate_unknowns(self):
        path = f'./tmp/{}_incomplete.csv'
