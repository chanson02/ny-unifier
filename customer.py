import un_util

# Unifier class to hold customer data
class Customer:
    def __init__(self, name, entries, bbg=None):
        self.known = False # all locations are known

        self.is_chain = False
        self.locations = []
        self.loc_to_ent = {} # {location_ndx => [Entry]}

        self.name = name
        self.entries = entries

        self.website = self.get_website()
        self.premise = self.get_premise()

        if bbg is None:
            bbg = un_util.new_bbg()

        # Compile addresses, is it a chain?
        self._remove_duplicate_entries()
        self._set_locations()

        if len(self.locations) == 0:
            # No location data found?
            return
        elif len(self.locations) == 1:
            # One location! <3
            # Send to busybody
            self.locations[0] = bbg.get(
                customer=self.name,
                address=self.locations[0],
                filename=self.entries[0].source
            )

        else:
            # multiple locations, represents chain?
            self.is_chain = True
            self.known = True
            for ndx in range(len(self.locations)):
                self.locations[ndx] = bbg.get(
                    customer=self.name,
                    address=self.locations[ndx]
                )

        self.update_known()
        return

    def __repr__(self):
        return f'{self.name} Customer Object'

    # Sets the known property
    # Call this whenever updating location
    def update_known(self):
        for loc in self.locations:
            if loc is None or loc.is_missing_parts():
                self.known = False
                return
        self.known = True
        return

    # Remove entries with the same address and product
    def _remove_duplicate_entries(self):
        result = []

        for ent in self.entries:
            if not self.in_list(ent, result):
                result.append(ent)

        self.entries = result
        return

    def in_list(self, obj, list):
        for item in list:
            if item.equals(obj):
                return True
        return False

    # Find different addresses within the same customer
    def _set_locations(self):
        for entry in self.entries:
            is_uniq = True

            for ndx in range(len(self.locations)):
                if self.locations[ndx] is None:
                    if None in self.locations:
                        is_uniq = False

                elif self.locations[ndx].mergable(entry.address):
                    self.locations[ndx] = self.locations[ndx].merge(entry.address)
                    is_uniq = False
                    self.loc_to_ent[ndx].append(entry)

            if is_uniq:
                self.loc_to_ent[len(self.locations)] = [entry]
                self.locations.append(entry.address)
        return

    def get_website(self):
        for ent in self.entries:
            if ent.website is not None:
                return ent.website
        return None


    def get_premise(self):
        for ent in self.entries:
            if ent.premise is not None:
                return ent.premise
        return None

    # Returns the location index
    # That matches an entry
    def find_location_from_entry(self, ent):
        for ndx in list(self.loc_to_ent.keys()):
            if ent in self.loc_to_ent[ndx]:
                return self.locations[ndx]
        return None

    # Search for a location that overlays given address
    def search_locations(self, address):
        for loc in self.locations:
            if loc.overlays(address):
                return loc
        return None
