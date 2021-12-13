import re
import secret
import un_util
import psycopg2
from address import Address
from collections import Counter

"""
Unifier Class to check Busybody database for missing information
"""

class BusybodyGetter:

    def __init__(self):
        # Open connection to db
        self.conn = psycopg2.connect(host=secret.db_login['host'], database=secret.db_login['database'], user=secret.db_login['user'], password=secret.db_login['password'])
        self.cur = self.conn.cursor()
        self.chains = self.get_chains()
        return

    def __repr__(self):
        return 'BusybodyGetter Object'

    def close(self):
        self.conn.close()
        return

    # Returns all chains
    # {name => id}
    def get_chains(self):
        self.cur.execute('SELECT name, id FROM chains')
        result = self.cur.fetchall()
        chains = {}
        for r in result:
            chains[r[0].replace('!', '')] = r[1]
        return chains

    # ! Does not always return bool
    def is_chain(self, string):
        if string is None:
            return False
        elif 'WF-NE' in string: # Make this apply to all aliases?
            string = string.replace('WF-NE', 'Whole Foods')

        string = self.clean(string)
        for name in list(self.chains.keys()):
            if self.clean(name) in string:
                return name
        return False

    # Function to remove misc characters from string
    def clean(self, string):
        extraneous = ['"', "'", ',', '-', '_', '.', ' ']
        for e in extraneous:
            string = string.replace(e, '')
        return string.lower().replace(' and ', '&')

    # Call busybody to find data
    def get(self, address, customer=None, filename=None):
        results = []
        # Pre check
        if address is not None and not address.is_missing_parts(include_phone=True):
            return address

        chain_file = self.is_chain(filename)
        chain_cust = self.is_chain(customer)
        chain_name = chain_file or chain_cust

        if chain_name is False:
            # Can't find any information on this address
            return address

        elif address is not None and not address.is_missing_parts(include_phone=False):
            # Only missing phone !
            try:
                address.phone = self.partial_address_search(address, self.chains[chain_name])[0][3] # 0th result, 3rd position = phone
            except IndexError:
                pass
            return address


        if chain_file:
            # file is a chain, customer is either a city or a remote_id
            results += self.remote_search(customer, self.chains[chain_name])

        if chain_cust:
            # chain is in customer or is customer-- split chain and remote/city
            remote = self.parse_identifier(customer, chain_name, address)
            if remote is not None:
                results += self.remote_search(remote, self.chains[chain_name])

        if address is not None and not address.is_empty():
            results += self.partial_address_search(address, self.chains[chain_name])

        if len(results) == 0:
            return address

        # return Address() object from busybody result
        result = Counter(results).most_common()[0][0]
        return self.address_object(result)

    # Converts database entry -> Address() object
    def address_object(self, db_ent):
        raw_addy = db_ent[2]
        result = un_util.addressor(raw_addy)
        if result is None:
            # Failed to addressor this
            result = Address(street=raw_addy)
        result.phone = db_ent[3]
        return result

    ###############################
    ### Remote Search Functions ###
    # Function to search by remote id
    def remote_search(self, identifier, chain_id):
        sql_command = f"SELECT * FROM stores WHERE chain_id='{chain_id}' AND "
        if self.contain_int(identifier) and len(identifier.split()) == 1: # One number ex: 13
            identifier = un_util.strip_letters(identifier)
            sql_command += f"remote_id='{identifier}'"
        else:
            identifier = identifier.replace("'", "''")
            sql_command += f"address ILIKE '%{identifier}%'"

        self.cur.execute(sql_command)
        result = self.cur.fetchall()
        return result

    # Function to find identifier
    def parse_identifier(self, customer, chain_name, address):
        customer = customer.lower().replace(chain_name.lower(), '').strip()
        if self.contain_int(customer):
            # remote_id
            for word in customer.split():
                if self.is_id_format(word):
                    return un_util.strip_letters(word)
        elif len(customer) > 0:
            # customer is a city?
            return customer
        else:
            # identifier in address?
            if address.street is not None and address.street != '':
                return address.street
            if address.city is not None and address.city != '':
                return address.city
        # Parse failed // didn't find anything
        return None

    # Function to identify if an integer is in a string
    def contain_int(self, string):
        if string is None:
            return False
        for char in string:
            if char.isdigit():
                return True
        return False

    # Function to identify if a word might be an ID
    def is_id_format(self, string):
        #, #12 returns TRUE
        # 17th returns FALSE
        if not self.contain_int(string):
            return False
        if string[-2:] == 'st' or string[-2:] == 'nd' or string[-2:] == 'rd' or string[-2:] == 'th':
            return False
        if string[0] == '(' and string[-1] == ')':
            return False
        return True

    ##############################
    ### Partial Address Search ###
    def partial_address_search(self, address, chain_id):
        sql_command = f"SELECT * FROM stores WHERE chain_id='{chain_id}'"

        potential_results = []

        if address.street is not None and address.street != '':
            t = address.street.replace("'", "''")
            cmd = sql_command + f" AND address ILIKE '%{t}%'"
            self.cur.execute(cmd)
            potential_results += self.cur.fetchall()
        if address.city is not None and address.city != '':
            t = address.city.replace("'", "''")
            cmd = sql_command + f" AND address ILIKE '%{t}%'"
            self.cur.execute(cmd)
            potential_results += self.cur.fetchall()
        if address.state is not None and address.state != '':
            t = address.state.replace("'", "''")
            cmd = sql_command + f" AND address ILIKE '%{t}%'"
            self.cur.execute(cmd)
            potential_results += self.cur.fetchall()
        if address.zip is not None and address.zip != '':
            t = str(address.zip).replace("'", "''")
            cmd = sql_command + f" AND address ILIKE '%{t}%'"
            self.cur.execute(cmd)
            potential_results += self.cur.fetchall()
        if address.phone is not None and address.phone != '':
            t = str(address.phone).replace("'", "''")
            cmd = sql_command + f" AND phone ILIKE '%{t}%'"
            self.cur.execute(cmd)
            potential_results += self.cur.fetchall()

        # Select the most common potential result
        if len(potential_results) == 0:
            return []
        return Counter(potential_results).most_common()[0]


if __name__ == '__main__':
    bbg = BusybodyGetter()
    customer = 'Whole Foods'
    address = Address('3060 excelsior blvd', None, 'mn', '55416')
    filename = ''
    bbg.get(address, customer, filename).print()
    # bbg.close()
