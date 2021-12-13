
"""
Unifier class to load any format file into memory properly
Remembers headers, searches multiple sheets for a known header
Upon unidentified header, prompt user for action

__init__(path)                  - path to file
self.rows         :[String]     - All the rows from this file (after the header)
self.filename     :String       - Name of file from path
self.instructions :Instructions - instructions for parser for this header

"""

import os, json
import un_util
import pandas as pd
from instructions import Instructions

class FileLoader:

    def __init__(self, path):
        self.file_key = None
        self.rows = [] # set in _load_filetype
        self.instructions = None


        self.filename = os.path.split(path)[1]

        self.excel_file = self._load_file(path)
        if self.excel_file is None:
            return

        header_id = self._load_file_type() # sets rows
        self.instructions = Instructions(iden=header_id)


        return

    def __repr__(self):
        return f'{self.filename} FileLoader Object'

    # Bring file into memory
    def _load_file(self, path):
        file_ext = self.filename.split('.')[-1]
        if file_ext in ['xlsx', 'xls', 'xlsm']:
            return pd.ExcelFile(path)
        elif file_ext == 'csv':
            return pd.read_csv(path)
        else:
            print(file_ext, 'not supported')
            return None

    # Determine how to parse file
    def _load_file_type(self):
        filetypes = un_util.filetypes()
        keys = [k for k in list(filetypes['file_keys'].keys()) if k in self.filename.lower()]
        if len(keys) == 0:
            # Need to create new key
            self.file_key = un_util.create_filekey(self.filename)
            filetypes = un_util.filetypes()
        else:
            self.file_key = keys[0]

        known_headers = filetypes['file_keys'][self.file_key] # [row0, row1, row2, ...]
        file_headers = self.file_headers() # {sheet_num: [row0, row1, ...]}
        raw_headers = []
        [[raw_headers.append(row) for row in values] for values in list(file_headers.values())]
        header = self.find_common_header(known_headers, raw_headers)

        # No header was found
        if header is None:
            # Initialize a new one
            header = self.init_header()
            # Update known headers
            filetypes = un_util.filetypes()
            known_headers = filetypes['file_keys'][self.file_key]

        # Find sheet and row number (to remove everything before it)
        sheet_num = self.search_sheets(sheets=file_headers, row=header['value'])
        row_offset = row_num = file_headers[sheet_num].index(header['value'])
        if type(self.excel_file) == un_util.XLSX_TYPE:
            self.rows = self.excel_file.parse(self.excel_file.sheet_names[sheet_num]).values[row_offset:]
        else:
            self.rows = self.excel_file.values[row_offset:]

        self.rows = [r.tolist() for r in self.rows]
        return header['id']

    # Get the first n rows from each sheet of file
    # {sheet_num: [row0, row1, ...]}
    def file_headers(self, rows=20):
        result = {}
        if type(self.excel_file) == un_util.XLSX_TYPE:
            names = self.excel_file.sheet_names
            for ndx in range(len(names)):
                sheet = self.excel_file.parse(names[ndx])
                result[ndx] = [sheet.columns.tolist()]
                result[ndx] += [row.tolist() for row in sheet.values[:rows - 1]]
        else:
            result[0] = [self.excel_file.columns.tolist()]
            result[0] += [row.tolist() for row in self.excel_file.values[:rows - 1]]

        pages = list(result.keys())
        for p in pages:
            result[p] = [un_util.remove_unnamed_columns(r) for r in result[p]]
            result[p] = [[un_util.strip_date(row) for row in r] for r in result[p]]
        return result

    # Return header saved in unifier
    def find_common_header(self, known, unknown):
        for k in known:
            if k['value'] in unknown:
                return k
        return None

    # Searches each sheet for a header
    def search_sheets(self, sheets, row):
        values = list(sheets.values())
        for ndx in range(len(values)):
            if row in values[ndx]:
                return ndx
        return None

    # Add new header to filetypes
    def init_header(self):
        # Ask about which sheet to use
        parsed = self.excel_file
        if type(self.excel_file) == un_util.XLSX_TYPE:
            sheets = self.excel_file.sheet_names
            if len(sheets) == 1:
                sheet_num = 0
            else:
                for ndx in range(len(sheets)):
                    print(f'{ndx}: {sheets[ndx]}')
                sheet_num = eval(input('Which sheet to use? '))
            parsed = self.excel_file.parse(sheets[sheet_num])

        # Ask about which header to use
        value = parsed.columns.tolist()
        value = un_util.remove_unnamed_columns(value)
        value = [un_util.strip_date(v) for v in value]
        print(self.filename, 'Header found', value)
        if eval(input('Use this header? ')) != 1:
            header_found = 0
            while header_found != 1:
                # Keep looping until correct header found
                usr_in = eval(input('Row to use as header: '))
                value = parsed.values[usr_in].tolist()
                value = un_util.remove_unnamed_columns(value)
                value = [un_util.strip_date(v) for v in value]
                print(value)
                header_found = eval(input('Is this the correct header to use?: '))

        ins = Instructions(value=value)
        ins.save(self.file_key)
        return {'id': ins.id, 'value': value}

if __name__ == '__main__':
    fl = FileLoader('input/hella/Hella August/Craft Collective August Report.xlsx')
