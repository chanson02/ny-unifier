import un_util

"""
Unifier class to hold an address
"""

class Address:

    def __init__(self, street=None, city=None, state=None, zip=None, phone=None):
        self.street = street
        self.city = city
        self.state = state
        self.zip = zip
        self.phone = phone
        return

    def print(self):
        print(f'{self.street}, {self.city}, {self.state}, {self.zip} - {self.phone}')

    # Function to format street for exporting
    def format(self):
        self.clean_street()
        self.phone = un_util.standardize_phone(self.phone)
        return

    # Misc functionality for certain files
    def clean_street(self):
        sep = str(self.street).split()
        if len(sep) > 0 and sep[0].lower() == 'c/o':
            #C/O MANAGER, 108 HEKILI STREET, STE 103
            self.street = ','.join(self.street.split(',')[1:]).strip()

        sep = str(self.street).split(',')
        if len(sep) > 0 and sep[0].lower() == 'c/o':
            # C/O, 2610 E 29TH AVE
            self.street = ','.join(self.street.split(',')[1:]).strip()

        return

    def is_empty(self):
        return (
            (self.street is None or self.street == '') and
            (self.city is None or self.city == '') and
            (self.state is None or self.state == '') and
            (self.zip is None or self.zip == '')
        )

    def is_missing_parts(self, include_phone=False):
        if include_phone and (self.phone is None or self.phone == ''):
            return True

        return (
            (self.street is None or self.street == '') or
            (self.city is None or self.city == '') or
            (self.state is None or self.state == '') or
            (self.zip is None or self.state == '')
        )

    def is_missing_phone(self):
        return self.phone is None or self.phone == ''

    def equals(self, address):
        return (
            str(self.street).lower() == str(address.street).lower() and
            str(self.city).lower() == str(address.city).lower() and
            str(self.state).lower() == str(address.state).lower() and
            str(self.zip).lower() == str(address.zip).lower() and
            str(self.phone).lower() == str(address.phone).lower()
        )

    def overlays(self, address):
        if address is None or address.is_empty():
            return True
        return (
            str(address.street).lower() in str(self.street).lower() and
            str(address.city).lower() in str(self.city).lower() and
            str(address.state).lower() in str(self.state).lower() and
            str(address.zip).lower() in str(self.zip)
        )

    # Can this address be merged?
    def mergable(self, address):
        if self.is_empty() or address.is_empty():
            return True
        return (
            (str(self.street).lower() in str(address.street).lower() or str(address.street).lower() in str(self.street).lower()) and
            (str(self.city).lower() in str(address.city).lower() or str(address.city).lower() in str(self.city).lower()) and
            (str(self.state).lower() in str(address.state).lower() or str(address.state).lower() in str(self.state).lower()) and
            (str(self.zip).lower() in str(address.zip).lower() or str(address.zip).lower() in str(self.zip).lower())
        )

    # Merge these two addresses
    # Returns a new address (these addresses combined)
    def merge(self, address):
        if not self.mergable(address):
            return None

        result = Address()

        result.street = un_util.longer(self.street, address.street)
        result.city   = un_util.longer(self.city, address.city)
        result.state  = un_util.longer(self.state, address.state)
        result.zip    = un_util.longer(str(self.zip), str(address.zip))
        result.phone  = un_util.longer(str(self.phone), str(address.phone))

        return result
