
# Object for comparing instructions from filetypes.json

class Instructions:

    def __init__(self):
        self.header_id = None
        self.identifier = 'skip'

        self.start_row = False
        self.merge_columns = {} #Dictionary {joiner: [columns]}
        self.chain = False

        # Location data
        self.phone = False
        self.website = False
        self.premise = False
        self.product = False
        self.address = False
        self.chain_address = False # combine chain and address

        self.customer = False
        return

    def __repr__(self):
        if self.header_id:
            msg = f'Instruction #{self.header_id} Object'
        else:
            msg = 'uninitialized Instructions object'
        return msg

    ####################
    ### USER PROMPTS ###
    def ask_instructions(self, header_id):
        self.header_id = header_id

        print("Enter a 1/0 for yes/no")
        if self.ask("Skip file? "):
            return

        self.start_row = int(input("What row does the data start? "))
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
        self.ask_identifier()

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

    def ask_identifier(self):
        identifiers = ['column', 'int', 'sep', 'indent', 'unifier']
        for index in range(len(identifiers)):
            print(f"{index}: {identifiers[index]}")
        self.identifier = identifiers[int(input('Identify by: '))]
        return
    ############################################

    # Convert these options to JSON
    def jsonify(self):
        instructions = {
            'identifier': self.identifier,
            'start_row': self.start_row,
            'merge': self.merge_columns,
            'chain': self.chain,
            'phone': self.phone,
            'website': self.website,
            'premise': self.premise,
            'product': self.product,
            'address': self.address,
            'chain_address': self.chain_address,
            'customer': self.customer
        }
        return instructions

    # Load JSON into memory
    def load_from_json(self, json):
        self.identifier = json['identifier']
        self.start_row = json['start_row']
        self.merge_columns = json['merge']
        self.chain = json['chain']
        self.phone = json['phone']
        self.website = json['website']
        self.premise = json['premise']
        self.product = json['product']
        self.address = json['address']
        self.chain_address = json['chain_address']
        self.customer = json['customer']
        return self
