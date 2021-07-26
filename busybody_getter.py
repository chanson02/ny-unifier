import psycopg2, re, os, json, pdb
from collections import Counter


# Class to check the Busybody database for information

class BusybodyGetter:

    def __init__(self):
        # Open connection to database
        self.conn = psycopg2.connect(host='ec2-3-231-241-17.compute-1.amazonaws.com', database='d6g73dfmsb60j0', user='doysqqcsryonfs', password='c81802d940e8b3391362ed254f31e41c20254c6a4ec26322f78334d0308a86b3')
        self.cur = self.conn.cursor()

        self.chains = self.get_chains()
        return

    def __repr__(self):
        return f"Busybody Getter"

    # Function to return all chain names known to busybody
    def get_chains(self):
        self.cur.execute('SELECT name, id FROM chains')
        result = self.cur.fetchall()
        chains = {}
        for r in result:
            chains[r[0]] = r[1]
        return chains

    # Function to search busybody for data
    def get(self, customer, address=None, filename=None):
        blank = self.missing_data(address)
        if len(blank) == 0:
            return address

        chain_file = self.is_chain(filename)
        chain_cust = self.is_chain(customer)
        chain_name = chain_file or chain_cust

        if chain_name is False:
            # Can't find anything // all info available
            return address
        # make this better !!!
        elif blank == ['phone']:
            # update only phone
            addy_search = self.partial_address_search(address, self.chains[chain_name])
            return addy_search[0] if len(addy_search) > 0 else address

        results = []

        if chain_file:
            # file is a chain, customer is either a city or a remote_id
            results += self.remote_search(customer, self.chains[chain_name])

        if chain_cust:
            # chain is in customer or is customer-- split chain and remote/city
            remote = self.parse_identifier(customer, chain_name, address)
            results += self.remote_search(remote, self.chains[chain_name])

        if address is not None:
            results += self.partial_address_search(address, self.chains[chain_name])

        return self.find_best_fit(results)

    # Function to remove misc characters from string
    def clean(self, string):
        extraneous = ['"', "'", ',', '-', '_', '.', ' ']
        for e in extraneous:
            string = string.replace(e, '')
        return string.lower().replace(' and ', '&')

    # Function to find data to look up in Busybody
    def missing_data(self, address):
        bb_keys = ['street', 'city', 'state', 'zip', 'phone']
        return bb_keys if address is None else [k for k in bb_keys if address[k] == '']

    # Function to check if string is chain
    def is_chain(self, string):
        if string is None:
            return False
        str_name = self.clean(string)
        for name in list(self.chains.keys()):
            if self.clean(name) in str_name:
                return name
        return False

    # Function to choose one final address from multiple results
    def find_best_fit(self, results):
        results = [r for r in results if r is not None]
        if len(results) == 0:
            return None
        elif len(results) == 1:
            return results[0]
        else:
            # print('UNFINISHED: find_best_fit', results)
            return results[0]

    # Function to convert Busybody entry to Unifier entry
    def result_to_dict(self, result):
        addressor = self.addressor(result[2])
        if addressor is None:
            return None
        return {
            'street': addressor['street'],
            'city': addressor['city'],
            'state': addressor['state'],
            'zip': addressor['postal_code'],
            'phone': result[3]
        }

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

    ###############################
    ### Remote Search Functions ###
    # Function to search by remote id
    def remote_search(self, identifier, chain_id):
        sql_command = f"SELECT * FROM stores WHERE chain_id='{chain_id}' AND "
        if self.contain_int(identifier) and len(identifier.split()) == 1:
            identifier = re.sub('[^0-9]', '', identifier)
            sql_command += f"remote_id='{identifier}'"
        else:
            identifier = identifier.replace("'", "''")
            sql_command += f"address ILIKE '%{identifier}%'"

        self.cur.execute(sql_command)
        results = self.cur.fetchall()
        return [self.result_to_dict(r) for r in results]

    # Function to find identifier
    def parse_identifier(self, customer, chain_name, address):
        customer = customer.lower().replace(chain_name.lower(), '').strip()
        if self.contain_int(customer):
            # remote_id
            for word in customer.split():
                if self.is_id_format(word):
                    return word.replace('#', '')
        elif len(customer) > 0:
            # customer is a city?
            return customer
        else:
            # identifier in address?
            if address['city'] != '':
                return address['city']
            elif address['street'] != '':
                return address['street']
        # Parse failed
        print('PARSE FAILED')
        return None

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

    ##############################
    ### Partial Address Search ###
    def partial_address_search(self, address, chain_id):
        # Find knowns keys
        known_keys = [k for k in list(address.keys()) if address[k] != '']
        for k in known_keys:
            address[k] = address[k].replace("'", "''")
        #Search each key
        sql_command = f"SELECT * FROM stores WHERE chain_id='{chain_id}'"
        for k in known_keys:
            if k == 'phone':
                sql_command += f" AND phone ILIKE '%{address[k]}%'"
            else:
                sql_command += f" AND address ILIKE '%{address[k]}%'"
        self.cur.execute(sql_command)
        results = self.cur.fetchall()
        return [self.result_to_dict(r) for r in results]



if __name__ == '__main__':
    customer = 'Whole Foods'
    address = {'street': '3060 excelsior blvd', 'city': 'Minneapolis', 'state': 'mn', 'zip': '55416', 'phone': ''}
    filename = ''
    bbg = BusybodyGetter()
    print(bbg.get(customer, address, filename))
    bbg.conn.close()
