import csv, copy, un_util
from address import Address
"""
Unifier Library used for generating the reports
Outputs to slack when reports are made
"""

HEADER = ["Source", "Customer", "Street", "City", "State", "Zip", "Phone", "Product", "Premise", "Website", "Comments"]
#           0           1           2       3       4       5       6           7           8           9

# Puts the entry into csv friendly header format
def gen_row(customer, entry):
    if entry.address is None:
        entry.address = Address()
    entry.address.format() # Format address for exporting
    row =  [
        entry.source,
        customer.name,
        entry.address.street,
        entry.address.city,
        entry.address.state,
        entry.address.zip,
        entry.address.phone,
        entry.product,
        customer.premise,
        customer.website
    ]
    return un_util.clean_row(row)

# Reports EVERYTHING --Not just knowns
def make_final_report(manager):
    customers = manager.get_all()
    rows = [HEADER]
    for customer in customers:
        for entry in customer.entries:
            if customer.is_chain:
                # Customer is a chain
                entry.address = customer.find_location_from_entry(entry) # Overwrite entry address with busybody address
                rows += [gen_row(customer, entry)]

            else:
                # Customer is not a chain
                entry.address = customer.locations[0] # Overwrite entry address with busybody address
                rows += [gen_row(customer, entry)]

    opath = manager.export_path() + '_unifier_report.csv'
    write_csv(rows, opath)
    return opath

# Same as final_report but minimized
def make_history_report(manager):
    customers = manager.get_all()
    rows = [HEADER]
    for customer in customers:
        for loc_ndx in range(len(customer.locations)):
            entries = customer.loc_to_ent[loc_ndx]
            new_ent = copy.copy(entries[0])
            new_ent.address = customer.locations[loc_ndx]
            new_ent.source = [e.source for e in entries]
            new_ent.product = [e.product for e in entries]
            rows += [gen_row(customer, new_ent)]

    opath = manager.export_path() + '_unifier_history.csv'
    write_csv(rows, opath)
    return opath

# Reports unknowns ONLY
def make_unknown_report(manager):
    customers = manager.get_unknown()
    rows = [HEADER]
    for customer in customers:
        for loc_ndx in range(len(customer.locations)):
            if customer.locations[loc_ndx] is None or customer.locations[loc_ndx].is_missing_parts():
                entries = customer.loc_to_ent[loc_ndx]
                new_ent = copy.copy(entries[0])
                new_ent.address = customer.locations[loc_ndx]
                new_ent.source = [e.source for e in entries]
                new_ent.product = [e.product for e in entries]
                rows += [gen_row(customer, new_ent)]

    opath = manager.export_path() + '_unifier_unknown.csv'
    write_csv(rows, opath)
    un_util.slack(f'{manager.directory}: {len(customers)}/{len(manager.get_all())} unknown customers')
    return opath


def make_new_report(new_manager, old_manager):
    new_customers = new_manager.get_all()
    rows = [HEADER]
    new_count = 0

    for customer in new_customers:
        if old_manager.search_customer(customer.name) is None:
            new_count += 1
            for entry in customer.entries:
                if customer.is_chain:
                    # Customer is a chain
                    entry.address = customer.find_location_from_entry(entry) # Overwrite entry address with busybody address
                    rows += [gen_row(customer, entry)]

                else:
                    # Customer is not a chain
                    entry.address = customer.locations[0] # Overwrite entry address with busybody address
                    rows += [gen_row(customer, entry)]

    opath = new_manager.export_path() + '_unifier_new.csv'
    write_csv(rows, opath)
    un_util.slack(f'{new_manager.directory} vs {old_manager.directory}: {new_count}/{len(new_customers)} new customers')
    return opath

def make_gap_report(new_manager, old_manager):
    old_customers = old_manager.get_all()
    rows = [HEADER]
    gap_count = 0

    for customer in old_customers:
        if new_manager.search_customer(customer.name) is None:
            gap_count += 1
            for entry in customer.entries:
                if customer.is_chain:
                    # Customer is a chain
                    entry.address = customer.find_location_from_entry(entry) # Overwrite entry address with busybody address
                    rows += [gen_row(customer, entry)]

                else:
                    # Customer is not a chain
                    entry.address = customer.locations[0] # Overwrite entry address with busybody address
                    rows += [gen_row(customer, entry)]


    opath = new_manager.export_path() + '_unifier_gap.csv'
    write_csv(rows, opath)
    un_util.slack(f'{new_manager.directory} vs {old_manager.directory}: {gap_count}/{len(old_customers)} gap customers')
    return opath

def write_csv(rows, path):
    with open(path, 'w') as f:
        wr = csv.writer(f)
        wr.writerows(rows)
    return
