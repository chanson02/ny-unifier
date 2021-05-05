import psycopg2, re


# Class to check the Busybody database for information

class BusybodyGetter:

    def __init__(self, handler):
        self.handler = handler

        # Open connection to database
        self.conn = psycopg2.connect(host='ec2-3-231-241-17.compute-1.amazonaws.com', database='d6g73dfmsb60j0', user='doysqqcsryonfs', password='c81802d940e8b3391362ed254f31e41c20254c6a4ec26322f78334d0308a86b3')
        self.cur = self.conn.cursor()

        self.chains = self.get_chains()

        self.execute()

        self.conn.close()

    def __repr__(self):
        return f"Busybody Getter for {self.handler}"

    def clean(self, string):
        extraneous = ['"', "'", ',', '-', '_', '.', ' ']
        for e in extraneous:
            string = string.replace(e, '')
        return string.lower()

    def get_chains(self):
        self.cur.execute('SELECT name, id FROM chains')
        result = self.cur.fetchall()
        chains = {}
        for r in result:
            chains[r[0]] = r[1]
        return chains

    def execute(self):
        # check if the whole file is a chain
        remote_id = self.file_is_chain()
        if remote_id is not False:
            # file is a chain
            print("not false")

        # check each entry for busybody

    def file_is_chain(self):
        filename = self.clean(self.handler.payload['source_file']['name'])
        for name in list(self.chains.keys()):
            if self.clean(name) in filename:
                return self.chains[name]

        return False



if __name__ == '__main__':
    from xlsx_handler import Handler
    file = Handler('XLSX examples/whole_foods.xlsx')
    t = BusybodyGetter(file)
