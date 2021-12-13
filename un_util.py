# NY-Unifier Utility library

import slack_send
import pandas as pd
import os, json, re
from address import Address
from busybody_getter import BusybodyGetter

XLSX_TYPE = pd.io.excel._base.ExcelFile
CSV_TYPE = pd.core.frame.DataFrame
SLACK = False # Boolean for if slack should be notified

MONTHS = {
    "january":"jan",
    "february":"feb",
    "march":"mar",
    "april":"apr",
    "may":"may",
    "june":"jun",
    "july":"jul",
    "auguest":"aug",
    "september":"sep",
    "october":"oct",
    "november":"nov",
    "december":"dec"
}

# List of customers to not report
BANNED_CUSTOMERS =[
    'total',
    'ma',
    'ri',
    'off premise',
    'on premise',
    'confidential'
]

# Sends a msg to Slack
def slack(msg):
    print('SLACK:', msg)
    return slack_send.slack(msg) if SLACK else None

def hella_codes():
    with open("extra data/hella_codes.json", "r") as f:
        hella_codes = json.load(f)
    return hella_codes

# Function to get filetypes
def filetypes():
    with open('filetypes.json', 'r') as f:
        filetypes = json.load(f)
    return filetypes

def write_filetypes(ft):
    with open('filetypes.json', 'w') as f:
        json.dump(ft, f, indent=2)
    return

# Function for user to add new filekey
def create_filekey(filename):
    print(f'\n\nNew File Discovered: {filename}')
    base, _ = os.path.splitext(filename)
    ft = filetypes()
    k = input('Name identifier for this file: ').lower()
    while k in list(ft['file_keys'].keys()):
        print('Identifier already in use')
        k = input('Name identifier for this file: ').lower()
    ft['file_keys'][k] = []
    write_filetypes(ft)
    return k

def is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

# Remove dates from string
def strip_date(string):
    base = str(string).split(' ')

    for ndx in range(len(base)):
        word = base[ndx]

        if is_int(word):
            # 04 09
            if len(word) <= 2 and int(word) <= 31 and int(word) > 0:
                base[ndx] = ''

            # 2020, 042020
            elif len(word) == 4 or len(word) == 6:
                base[ndx] = ''

        else:
            # Jan, Feb, March, April
            if word.lower() in MONTHS.values() or word.lower() in MONTHS.keys():
                base[ndx] = ''

            # 12.15
            elif len(word) == 5 and '.' in word:
                if is_int(word[:1]) and is_int(word[3:]):
                    base[ndx] = ''

            # 202004
            elif len(word) == 6 and is_int(word):
                base[ndx] = ''

            # 04-2020, 04/2020, 2020/04
            else:
                strip = word.replace('-', '').replace('/', '').replace('_', '')
                # 04-2020, 04_09_2020, 04/09/2020
                if is_int(strip) and (len(strip) + 1 == len(word) or len(strip) + 2 == len(word)):
                    base[ndx] = ''

    return ' '.join(base).strip()

# Remove unnamed columns (only at the end)
def remove_unnamed_columns(cols):
    unnamed_count = 0
    cols.append('Unnamed: ') # Always remove atleast one to prevent [:-0] error
    for c in cols[::-1]:
        if 'Unnamed: ' in str(c) or c != c:
            unnamed_count += 1
        else:
            break
    # Replace unnamed with ''
    return ['' if 'Unnamed: ' in str(c) or c != c else c for c in cols[:-unnamed_count]]

# Function to check validity of Excel cell
def valid_cell(cell):
    return cell == cell and cell != '' and cell != None

# Function to remove letters from string
def strip_letters(string):
    if string is None:
        return string
    return re.sub('[^0-9]', '', str(string))

# Function to standardize phone number 999-999-9999
def standardize_phone(phone):
    if phone is None or phone == '':
        return phone
    phone = strip_letters(phone)
    if len(phone) < 10: #is not a phone number
        return ''
    if phone[0] == '1': # remove country code
        phone = phone[1:]
    phone = phone[:10] # remove extra
    return f'{phone[:3]}-{phone[3:6]}-{phone[6:]}'

# Function to standardize address dictionary
# def empty_address():
#     return {'street': '', 'city': '', 'state': '', 'zip': '', 'phone': ''}

# Function to call the addressor from the command line
def addressor(address):
    command = f"ruby ../ny-addressor/lib/from_cmd.rb -o -a '{address}'"
    os.system(command)

    # Read from addressor, handle errors
    try:
        with open('addressor.json', 'r') as f:
            parts = json.load(f)
        os.remove('addressor.json')
    except Exception:
        return None
    if parts is None:
        return None

    # Make sure the addressor returned
    # All of the required parts
    required_keys = ['street_name', 'street_number', 'city', 'state', 'postal_code']
    keys = list(parts.keys())
    for rk in required_keys:
        if rk not in keys:
            parts[rk] = ''

    # Combine street parts together
    parts["street"] = f"{parts['street_number']} {parts['street_name']}"
    if "street_label" in keys:
        parts["street"] += f" {parts['street_label']}"
    if "street_direction" in keys:
        parts["street"] += f" {parts['street_direction']}"

    return Address(
        street = parts['street'],
        city = parts['city'],
        state = parts['state'],
        zip = parts['postal_code']
    )

# Returns the longer of two strings
def longer(string1, string2):
    if string1 is None or string1 == '':
        return string2
    elif (string2 is None or string2 == ''):
        return string1
    elif len(string1) > len(string2):
        return string1
    else:
        return string2

# Returns a new BusybodyGetter
def new_bbg():
    return BusybodyGetter()

# 'cleans' values in row from file
def clean_row(row):
    for ndx in range(len(row)):
        if row[ndx] != row[ndx]:
            row[ndx] = ''
        if row[ndx] is None:
            row[ndx] = ''
        if row[ndx] == 'None':
            row[ndx] = ''
    return [str(v) for v in row]
