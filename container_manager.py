from busybody_getter import BusybodyGetter
from xlsx_handler import Handler

# Object to keep Customers for a container organized
# Object to  generate reports on a container

#!  container_files is a list of paths
#!  container_folder is the DriveFolder of the container

"""
ContainerManager
.get_known_customers
.get_unknown_customers
.get_customers
.get_total_entries

.load_knowns(complete_file)

.generate_new_report(old_container_manager)
.generate_gap_report(old_container_manager)
.generate_unknowns()
.generate_knowns()
"""
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
