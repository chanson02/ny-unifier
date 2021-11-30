import pdb
import json
import traceback

class Customer:

    def __init__(self, name):
        self.name = name
        self.final = None # Final address
        # self.search_address_book()

        self.entries = []
        self.website = ''
        self.premise = ''

        self.bbg = None #BusyBodyGetter

        return

    def __repr__(self):
        return f'{self.name} Object'

    def add_entry(self, data):
        self.entries.append(data)
        return

    # # Check to see if in address book
    # def search_address_book(self):
    #     with open('address_book.json', 'r') as f:
    #         book = json.load(f)
    #     k = self.name.lower()
    #     if k in list(book.keys()):
    #         # self.final = book[k]
    #         # import pdb; pdb.set_trace()
    #         # print(f'\n\ncustomer.py:search_address_book NOT FINISHED !\ndefaulting {self}')
    #         self.final = book[k][0]
    #     return





    def execute(self, bbg):
        # print(f'Executing {self.name}')
        if self.name == 'Confidential':
            self.name = f'Confidential x{len(self.entries)}'
            self.entries = [self.entries[0]]

        self.bbg = bbg # Set the busybody getter
        if self.final is not None:
            return

        # check to see if there are different address entries
        self.set_variations()
        filename = self.entries[0]['source']
        if self.all_mergable(self.variations):
            merged = self.merge_all(self.variations)
            #send to busybody
            try:
                self.final = self.bbg.get(customer=self.name, address=merged, filename=filename)
                print('.', end='', flush=True)
            except Exception:
                self.final = merged
                print(f'\nError setting final address for {self}')
                traceback.print_exc()
                print('X', end='', flush=True)
        else: #not all mergable
            # send each variation to busybody
            #TODO: Check sources for chainfile?
            for variation in self.variations:
                variation = self.bbg.get(customer=self.name, address=variation, filename=filename)
                print(',', end='', flush=True)
            for e in self.entries:
                e['address'] = self.most_similar(e['address'], self.variations)
        return

    # Function to find different addresses within one customer
    # array
    def set_variations(self):
        uniq = []
        for entry in self.entries:
            if entry['address'] not in uniq:
                uniq.append(entry['address'])
        self.variations = uniq
        return uniq

    # Function to check if an address is empty
    # bool
    def empty_address(self, address):
        parts = list(address.values())[:-1]
        found_parts = [part for part in parts if part != '']
        if len(found_parts) == 0:
            return True
        else:
            return False

    # Function to check if all addresses can be merged
    # bool
    def all_mergable(self, addresses):
        checked_addresses = []
        for v1 in addresses:
            checked_addresses.append(v1)
            for v2 in addresses:
                if v2 not in checked_addresses:
                    if not self.mergable(v1, v2):
                        return False
        return True

    # Function to check if two addresses can be merged
    # bool
    def mergable(self, a1, a2):
        if self.empty_address(a1) or self.empty_address(a2):
            return True

        a1_parts = list(a1.values())[:-1]
        a2_parts = list(a2.values())[:-1]

        for ndx in range(len(a1_parts)):
            if a1_parts[ndx] in a2_parts[ndx] or a2_parts[ndx] in a1_parts[ndx]:
                pass
            else:
                return False

        return True

    # Function to attempt to merge all entry addresses
    def merge_all(self, variations):
        final_address = {'street': '', 'city': '', 'state': '', 'zip': '', 'phone': ''}
        for variation in variations:
            for key in list(variation.keys()):
                if len(variation[key]) > len(final_address[key]):
                    final_address[key] = variation[key]
        return final_address

    # Function to return the most similar variation
    def most_similar(self, address, variations):
        if address in variations:
            return address
        else:
            print('customer:most_similar() UNFINISHED')
            return address
