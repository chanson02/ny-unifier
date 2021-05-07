import psycopg2, re, os, json, pdb


# Class to check the Busybody database for information

class BusybodyGetter:

    def __init__(self, handler):
        self.handler = handler

        # Open connection to database
        self.conn = psycopg2.connect(host='ec2-3-231-241-17.compute-1.amazonaws.com', database='d6g73dfmsb60j0', user='doysqqcsryonfs', password='c81802d940e8b3391362ed254f31e41c20254c6a4ec26322f78334d0308a86b3')
        self.cur = self.conn.cursor()

        self.chains = self.get_chains()

        chain_id = self.file_is_chain()
        if chain_id is not False:
            # file is a chain
            self.update_file(chain_id)
        else:
            self.update_rows()

        self.conn.close()

    def __repr__(self):
        return f"Busybody Getter for {self.handler}"

    # Function to remove characters from string
    def clean(self, string):
        extraneous = ['"', "'", ',', '-', '_', '.', ' ']
        for e in extraneous:
            string = string.replace(e, '')
        return string.lower()

    # Function to return all chain names known to busybody
    def get_chains(self):
        self.cur.execute('SELECT name, id FROM chains')
        result = self.cur.fetchall()
        chains = {}
        for r in result:
            chains[r[0]] = r[1]
        return chains

    # Function to find data to look up in Busybody
    def missing_data(self, customer):
        bb_keys = ['street', 'city', 'state', 'zip', 'phone']
        address = self.handler.payload['customers'][customer]['address']
        return [k for k in bb_keys if address[k] == '']

    # Check if address can be partially searched
    def partial_address(self, missing_keys):
        if 'street' not in missing_keys or 'city' not in missing_keys or 'state' not in missing_keys or 'zip' not in missing_keys:
            return True
        return False

    # Function to update self.handler.payload with Busybody data
    def update_customer(self, customer, entry):
        parts = self.addressor(entry[2])
        if parts is None:
            return

        address = self.handler.payload['customers'][customer]['address']
        address['street'] = parts['street']
        address['city'] = parts['city']
        address['state'] = parts['state']
        address['zip'] = parts['postal_code']
        address['phone'] = entry[3]

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
        try:
            if "street_label" in keys:
                parts["street"] += f" {parts['street_label']}"
        except:
            pass
        try:
            if "street_direction" in keys:
                parts["street"] += f" {parts['street_label']}"
        except:
            pass

        return parts

    def file_is_chain(self):
        filename = self.clean(self.handler.payload['source_file']['name'])
        for name in list(self.chains.keys()):
            if self.clean(name) in filename:
                return self.chains[name]

        return False

    def update_rows(self):
        pass

    def update_file(self, chain_id):
        customers = self.handler.payload['customers']

        for customer in list(customers.keys()):
            blank = self.missing_data(customer)

            # Skip if all information already exists
            if len(blank) == 0 or customer is None:
                continue

            if blank == ['phone']:
                # If phone is the only missing key
                print('this does nothing right now')
                continue

            if self.partial_address(blank):
                # Use partial address to find the rest of the address
                print('this also does nothing right now')
                pass
            else:
                # Find by customer
                # MAKE A FUNCTION TO DETECT REMOTE ID
                remote_id = re.sub('[^0-9]', '', customer)
                if len(remote_id) == 0:
                    # Customer is a city
                    self.cur.execute(f"SELECT * FROM stores WHERE chain_id=42 AND address ILIKE '%{customer}%'")
                    results = self.cur.fetchall()
                    if len(results) == 0:
                        continue

                    entry = self.best_fit(customer, results)
                    if entry is None:
                        continue

                    self.update_customer(customer, entry)

                else:
                    #Customer is a remote_id
                    print('this does nothing right now x3', remote_id)
                    pass

    # Function to find the best matching location returned by busybody
    def best_fit(self, customer, results, by='city'):
        parsed_addresses = []
        for r in results:
            nyaddr = self.addressor(r[2])
            if nyaddr is not None:
                parsed_addresses.append(nyaddr)

        possible = []
        for pa in parsed_addresses:
            if pa[by] == customer.lower():
                possible.append(pa)

        if len(possible) > 0:
            for r in results:
                if possible[0]['orig'] == r[2]:
                    return r
        return None



if __name__ == '__main__':
    from xlsx_handler import Handler
    file = Handler('XLSX examples/whole_foods.xlsx')
    t = BusybodyGetter(file)
