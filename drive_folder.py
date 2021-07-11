class DriveFolder:

    def __init__(self, service, folder_data, parent=None):
        self.service = service
        self.folder_data = self.set_folder_data(folder_data)
        self.parent = parent
        self.path = self.set_path()
        self.files = []
        self.children = []

        self.contents = self.get_contents()
        self.sep_contents()
        return

    def __repr__(self):
        return f'{self.folder_data["name"]} Folder'

    # Makes fake data for root
    def set_folder_data(self, folder_data):
        if type(folder_data) == str:
            return {'name': 'root', 'id': folder_data, 'mimeType': 'application/vnd.google-apps.folder', 'createdTime': 0}
        else:
            return folder_data

    # Function to set path string
    def set_path(self):
        if self.parent is None:
            return f'/{self.folder_data["name"]}'
        else:
            return f'{self.parent.path}/{self.folder_data["name"]}'

    # Function to return items in folder
    def get_contents(self):
        return self.service.files().list(
            q=f"parents in '{self.folder_data['id']}'",
            fields='files(id, name, createdTime, mimeType, parents)'
        ).execute()['files']

    # Function to populate children and files arrays
    def sep_contents(self):
        for content in self.contents:
            if content['mimeType'] == 'application/vnd.google-apps.folder':
                folder = DriveFolder(self.service, content, self)
                self.children.append(folder)
            else:
                self.files.append(content)
