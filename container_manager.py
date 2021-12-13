import os
import un_util
from customer import Customer
from file_handler import FileHandler

"""
Unifier class to group multiple files into one 'container'
A container can be thought of as a directory full of files (ex: Hella October)
The ContainerManager will organize customers and products

FileHandler holds entries
Each entry is assigned to a customer

.get_all
.get_known
.get_unknown
.get_chains
.get_non_chains
"""

class ContainerManager:

    # Container path is path to a DIRECTORY
    # Each file inside the directory is run
    def __init__(self, container_path):
        self.directory = container_path
        self.customers = []
        self.output = self.export_path()

        self._load_customers()

        return

    def export_path(self):
        p = self.directory.split('/')
        p[0] = 'output'
        return '/'.join(p)

    # This function consolidates customers
    # Throughout all files in container
    def _load_customers(self):
        # Make sure each file loads with no errors
        print('Parsing files')
        file_handlers = []
        for f in os.listdir(self.directory):
            file_handlers.append(FileHandler(self.directory + '/' + f))
            print('.', end='', flush=True)
        print('')

        custs = {} # name => [Entry]
        # Point each entry to a customer
        print('Loading data from files')
        for handler in file_handlers:
            for entry in handler.entries:
                if entry.customer_name in list(custs.keys()):
                    custs[entry.customer_name].append(entry)
                else:
                    custs[entry.customer_name] = [entry]
            print('.', end='', flush=True)
        print('\n\n')

        # Add the customers to the object
        bbg = un_util.new_bbg()
        cust_names = list(custs.keys())
        print(f'Compiling {len(cust_names)} Customers')
        for k in self.remove_extra_customers(cust_names):
            c = Customer(k, custs[k], bbg=bbg)
            self.customers.append(c)
            print('.', end='', flush=True)
        bbg.close()
        print('\n\n')
        return

    def remove_extra_customers(self, names):
        result = []
        for name in names:
            if str(name).lower() not in un_util.BANNED_CUSTOMERS:
                result.append(name)
        return result

    # Looks in old manager for address data
    def load_knowns(self, old_manager):
        old_customers = old_manager.get_known() + old_manager.get_partial_known()
        old_names = [c.name.lower() for c in old_customers]

        for cust_ndx in range(len(self.customers)):
            new_customer = self.customers[cust_ndx]

            if not new_customer.known and new_customer.name.lower() in old_names:
                # If this customer is known by history
                old_customer = old_manager.search_customer(new_customer.name)

                for loc_ndx in range(len(new_customer.locations)):
                    # Check each location for presence in history
                    known_location = old_customer.search_locations(new_customer.locations[loc_ndx])
                    if known_location is not None:
                        # Update the location
                        if new_customer.locations[loc_ndx] is None:
                            self.customers[cust_ndx].locations[loc_ndx] = known_location
                        else:
                            self.customers[cust_ndx].locations[loc_ndx] = new_customer.locations[loc_ndx].merge(known_location)
                        self.customers[cust_ndx].update_known() #173
        return

    def search_customer(self, name):
        for c in self.customers:
            if c.name.lower() == name.lower():
                return c
        return None

    # Returns all customers
    def get_all(self):
        return self.customers

    # Return all known customers (+ chains)
    def get_known(self):
        result = []
        for c in self.customers:
            if c.known:
                result.append(c)
        return result

    def get_unknown(self):
        result = []
        for c in self.customers:
            if not c.known:
                result.append(c)
        return result

    def get_chains(self):
        result = []
        for c in self.customers:
            if c.is_chain:
                result.append(c)
        return result

    def get_non_chains(self):
        result = []
        for c in self.customers:
            if not c.is_chain:
                result.append(c)
        return result

    # Chains with atleast one known address
    def get_partial_known(self):
        result = []
        for c in self.get_chains():
            for loc in c.locations:
                if not loc.is_missing_parts():
                    result.append(c)
                    break
        return result
if __name__ == '__main__':
    test = ContainerManager('input/hella/Hella August')
