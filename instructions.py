
# Object for comparing instructions from filetypes.json
import un_util

class Instructions:

    def __init__(self, iden=None, value=[]):

        # Instruction Data
        self.parser = 'skip'
        self.merge_columns = {}
        self.chain = False
        self.chain_address = False # Combine chain and address

        # Customer Data
        self.phone = False
        self.website = False
        self.premise = False
        self.customer = False

        # Location Data
        self.address = False # can be int or dict
        self.product = False # can be int or array

        self.id = iden
        self.value = value

        if self.id is None:
            # See if value already has an ID
            self.id = self.search_all_values(value)

            if self.id is None:
                # See if instructions belong to another header
                self.ask_instructions()
                self.id = self.search_all_instructions()
                # MUST CALL SAVE METHOD EXTERNALLY
            return

        else:
            # Load instructions
            self.load()

    def __repr__(self):
        if self.id is None:
            return 'Uninitialized Instructions object'
        else:
            return f'Instructions for header-id #{self.id} Object'

    def print_instructions(self):
        print(self.jsonify())

    # Load an id from the JSON
    def load(self):
        filetypes = un_util.filetypes()
        ins = filetypes['headers'][str(self.id)]
        self.parser = ins['parser']
        self.merge_columns = ins['merge']
        self.chain = ins['chain']
        self.phone = ins['phone']
        self.website = ins['website']
        self.premise = ins['premise']
        self.product = ins['product']
        self.chain_address = ins['chain_address']
        self.address = ins['address']
        self.customer = ins['customer']
        return

    # Converts these options to json
    def jsonify(self):
        return {
            'parser': self.parser,
            'merge': self.merge_columns,
            'chain': self.chain,
            'phone': self.phone,
            'website': self.website,
            'premise': self.premise,
            'product': self.product,
            'chain_address': self.chain_address,
            'address': self.address,
            'customer': self.customer
        }

    def save(self, file_key):
        filetypes = un_util.filetypes()

        # Save header instructions
        if self.id is None:
            header_count = len(list(filetypes['headers'].keys()))
            self.id = header_count + 1
            filetypes['headers'][self.id] = self.jsonify()

        # Point header to instructions
        filetypes['file_keys'][file_key].append({
            'id': self.id,
            'value': self.value
        })

        # Save to disk
        un_util.write_filetypes(filetypes)
        return


    # Search every header in the filetypes
    # Returns id
    def search_all_values(self, value):
        filetypes = un_util.filetypes()
        file_keys = list(filetypes['file_keys'].keys())
        for key in file_keys:
            file_headers = filetypes['file_keys'][key]
            for header in file_headers:
                if value == header['value']:
                    return header['id']
        return None

    # Search all instructions
    # Returns id
    def search_all_instructions(self):
        ins = self.jsonify()
        filetypes = un_util.filetypes()
        header_ids = list(filetypes['headers'].keys())
        for iden in header_ids:
            if filetypes['headers'][iden] == ins:
                return int(iden)
        return None

    # Easily view head
    def print_header(self):
        col_count = len(self.value)
        count_line = ''  # 1       2       3
        header_line = '' # row0    row1    row2

        for ndx in range(col_count):
            count_line += f'  {ndx:>8}  '
        for col in self.value:
            header_line += f'  {str(col)[:10]:>10}'

        print('\n')
        print(count_line)
        print(header_line)
        return

    ####################
    ### USER PROMPTS ###
    def ask_instructions(self):
        self.print_header()

        print("Enter a 1/0 for yes/no")
        if self.ask("Skip file? "):
            return

        self.ask_merge_columns()

        if self.ask('Does this file represent a chain? '):
            self.chain = input("   Chain  name: ")

        if self.ask('Does this file contain phone numbers? '):
            self.phone = int(input("  Phone column: "))

        if self.ask('Does this file contain websites?  '):
            self.website = int(input("  Website Column: "))

        if self.ask('Does this file contain premise data? '):
            self.premise = int(input("  Premise Column: "))

        if self.ask('Does this file contain products? '):
            print('   *for multiple products input [x,y,z]')
            self.product = eval(input('  Product row: '))

        self.ask_address_data()
        self.customer = int(input("Customer column: "))
        self.ask_parser()

        return

    # Function to ask yes/no # QUESTION:
    def ask(self, prompt):
        user_input = input(prompt)
        if user_input == "1":
            return True
        else:
            return False

    def ask_merge_columns(self):
        if not self.ask('Do any columns need to be merged? '):
            return

        for i in range(eval(input("  How many merges? "))):
            joiner = input('  Character to combine columns: ')
            merge = eval(input('  Array of columns: '))

            if joiner in list(self.merge_columns.keys()):
                self.merge_columns[joiner].append(merge)
            else:
                self.merge_columns[joiner] = merge
        return

    def ask_address_data(self):
        if not self.ask('Does this file contain addresses? '):
            return

        if self.ask('  Does this file seperate address data? '):
            address_data = {}
            keys = ['address1', 'address2', 'city', 'state', 'zip']
            print('    Input -1 for empty address column')
            for k in keys:
                address_data[k] = int(input(f"    {k} column: "))
            self.address = address_data
        else:
            if self.ask('  Does this file combine chain and addresses? '):
                self.chain_address = True
            self.address = int(input("  Address column: "))
        return

    def ask_parser(self):
        parsers = ['row', 'int', 'sep', 'product_indent', 'unifier']
        for index in range(len(parsers)):
            print(f"{index}: {parsers[index]}")
        self.parser = parsers[int(input('Parse by: '))]
        return
