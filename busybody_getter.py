import psycopg2, re, os, json, pdb
from collections import Counter


# Class to check the Busybody database for information

class BusybodyGetter:

    def __init__(self, handler):
        self.handler = handler

        # Open connection to database
        self.conn = psycopg2.connect(host='ec2-3-231-241-17.compute-1.amazonaws.com', database='d6g73dfmsb60j0', user='doysqqcsryonfs', password='c81802d940e8b3391362ed254f31e41c20254c6a4ec26322f78334d0308a86b3')
        self.cur = self.conn.cursor()

        self.chains = self.get_chains()

        chain_name = self.is_chain(self.handler.payload['source_file']['name'])
        if chain_name is not False:
            # file is a chain
            self.update_file(chain_name)
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
        return string.lower().replace(' and ', '&')

    # Function to identify if an integer is in a string
    def contain_int(self, string):
        for char in string:
            if char.isdigit():
                return True
        return False

    # Function to identify if a word might be an ID
    def is_id_format(self, string):
        #, #12 returns TRUE
        # 17th returns FALSE
        if string[-2:] == 'st' or string[-2:] == 'nd' or string[-2:] == 'rd' or string[-2:] == 'th':
            return False
        if string[0] == '(' and string[-1] == ')':
            return False
        return True

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

    def is_chain(self, string):
        str_name = self.clean(string)
        for name in list(self.chains.keys()):
            if self.clean(name) in str_name:
                return name
                # return self.chains[name]

        return False

    # Function to look for a chain in each row
    def update_rows(self):
        customers = self.handler.payload['customers']

        for customer in customers:
            chain = self.is_chain(customer)
            if chain is False:
                continue

            # Scrape busybody for chain data
            self.update_row(customer, chain)

        return

    # Function to look up each entry against a chain
    def update_file(self, chain):
        customers = self.handler.payload['customers']

        for customer in list(customers.keys()):
            self.update_row(customer, chain, chain_file=True)

    def update_row(self, customer, chain_name, chain_file=False):
        # remove chain from customer (if in there)
        blank = self.missing_data(customer)
        remote_id = self.find_remote_id(customer, chain_name)
        chain_id = self.chains[chain_name]

        # Skip if all information already exists
        if len(blank) == 0 or customer is None:
            return

        # Check if only missing phone
        elif blank == ['phone']:
            self.update_phone(customer, chain_name)
            return

        # Use partial address to find the rest of the information
        elif self.partial_address(blank):
            if self.partial_search(customer, chain_id):
                return

        # Search by remote_id
        if remote_id is not None:
            print('remote_id search does nothing right now')

        # Search by city
        else:
            self.cur.execute(f"SELECT * FROM stores WHERE chain_id={chain_id} AND address ILIKE '%{customer}%'")
            results = self.cur.fetchall()
            if len(results) == 0:
                return

            entry = self.best_fit(customer, results)
            if entry is None:
                return

            self.update_customer(customer, entry)

        return

    # Function to only find phone number of customer
    # (address already known)
    def update_phone(self, customer, chain):
        address = self.handler.payload['customers'][customer]['address']

        sql_command = 'SELECT phone FROM stores WHERE '
        sql_command += f"chain_id={self.chains[chain]} "
        sql_command += f"AND address ILIKE '%{address['street'].split()[0]}%' " # Just search for the same street number
        sql_command += f"AND address ILIKE '%{address['city']}%' "
        sql_command += f"AND address ILIKE '%{address['state']}%' " # TO-DO: Standardize the state?
        sql_command += f"AND address ILIKE '%{address['zip']}%'"
        self.cur.execute(sql_command)
        results = self.cur.fetchall()
        if len(results) == 0:
            #TO-DO: print('flag and check!')
            return

        address['phone'] = results[0][0]

        return

    # Function to extract remote id out of customer name
    # Whole Foods #12 - return 12
    # 17th Street - return None
    def find_remote_id(self, customer, chain_name):
        # Find chain id and name
        # chain_name = self.is_chain(self.handler.payload['source_file']['name'])
        chain_id = self.chains[chain_name]

        # Remove chain from name
        no_chain_name = self.clean(customer).replace(chain_name, "")

        # Find potential matches for ID's
        potential_ids = []
        for word in customer.split()[::-1]:
            if word in no_chain_name and self.contain_int(word) and self.is_id_format(word):
                potential_ids.append(word)

        # Find which potential id to return
        if len(potential_ids) == 0:
            return None
        elif len(potential_ids) == 1:
            return re.sub('[^0-9]', '', potential_ids[0])
        else:
            for p_id in potential_ids:
                if '#' in p_id:
                    return re.sub('[^0-9]', '', p_id)
            return re.sub('[^0-9]', '', potential_ids[0])

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

    # Function to find best matching location based off partial address
    def partial_search(self, customer, chain_id):
        # find known keys
        # search each key
        # append results to array/
        # find most repeated entry
        data = self.handler.payload['customers'][customer]['address']
        known_keys = []
        for k in list(data.keys()):
            if data[k] != '':
                known_keys.append(k)

        entries = []
        for k in known_keys:
            if k == 'phone':
                self.cur.execute(f"SELECT * FROM stores WHERE chain_id='{chain_id}' AND phone ILIKE '%{data[k]}%'")
            else:
                self.cur.execute(f"SELECT * FROM stores WHERE chain_id='{chain_id}' AND address ILIKE '%{data[k]}%'")

            for r in self.cur.fetchall():
                entries.append(r)

        if len(entries) == 0:
            print('partial search failed')
            return False
        self.update_customer(customer, Counter(entries).most_common()[0][0])
        return True


if __name__ == '__main__':
    from xlsx_handler import Handler
    file = Handler('XLSX examples/whole_foods.xlsx')
    t = BusybodyGetter(file)
