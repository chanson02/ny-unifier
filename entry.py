# Unifier class for representing each 'row' in a xlsx file

class Entry:

    def __init__(
        self, customer_name, product=None, address=None,
        phone=None, premise=None, website=None, source=None
    ):
        self.customer_name = customer_name
        self.product = product
        self.address = address # address.py Object
        self.phone = phone
        self.premise = premise
        self.website = website
        self.source = source
        return

    def __repr__(self):
        return f'{self.customer_name} Entry Object from {self.source}' # | {self.to_dict()}'

    def to_dict(self):
        return {
            'product': self.product,
            'phone': self.phone,
            'premise': self.premise,
            'website': self.website,
            'address': self.address
        }

    def print(self):
        print(self.customer_name, self.product, self.phone, self.premise, self.website, self.source)
        self.address.print()
        return

    def get_address(self):
        result = un_util.empty_address()

        return result

    def equals(self, entry):
        result = (
            self.customer_name.lower() == entry.customer_name.lower() and
            str(self.product).lower() == str(entry.product).lower()
        )
        if self.address is None:
            if entry.address is None:
                return result
            else:
                return result and self.address.equals(entry.address)
