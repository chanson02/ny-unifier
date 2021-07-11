import os, pickle, io
from datetime import datetime
from googleapiclient.discovery import build
from apiclient.http import MediaIoBaseDownload, MediaFileUpload
from google.oauth2.credentials import Credentials

from drive_folder import DriveFolder


class DriveDownloader:
    def __init__(self, out_path='./drive_downloaded'):
        self.out_path = out_path
        creds = Credentials.from_authorized_user_file('token.json', ['https://www.googleapis.com/auth/drive'])
        self.service = build('drive', 'v3', credentials=creds)
        # self.clear_storage()
        self.root = DriveFolder(self.service, '1ZYtG8roWBaeEdrHk0KSahAh4gPEiTOG5')

    # Function to remove previously downloaded files
    def clear_storage(self):
        files = os.listdir(self.out_path)
        for f in files:
            os.remove(os.path.join(self.out_path, f))
        return

    # Function to download
    def download_file(self, file_data):
        filename = file_data['name'].replace('/', '-')

        if file_data['mimeType'] == 'application/vnd.google-apps.spreadsheet':
            # Convert the Sheets file to XLSX file
            download_request = self.service.files().export(fileId=file_data["id"], mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            filename += '.xlsx'
        else:
            download_request = self.service.files().get_media(fileId=file_data["id"])

        path = os.path.join(self.out_path, filename)
        file_handler = io.BytesIO()
        downloader = MediaIoBaseDownload(file_handler, download_request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        with io.open(path, 'wb') as f:
            file_handler.seek(0)
            f.write(file_handler.read())
        return path

    # Function to upload
    def upload_file(self, path, parent_id):
        mime_type = 'text/csv'
        filename = path.split('|')[-1]
        media = MediaFileUpload(path, mimetype=mime_type, resumable=True)
        body = {'name': filename, 'description': 'Unifier -> Va', 'mimeType': mime_type, 'parents': [parent_id]}
        upload = self.service.files().create(body=body, media_body=media).execute()
        return upload

    # Function to setup files for new brand
    def initialize_brand(self, brand):
        mime = 'application/vnd.google-apps.folder'
        [self.service.files().create(
            body={'name': name, 'mimeType': mime, 'parents': [brand.folder_data['id']]}
        ).execute()
        for name in ['brand_io', 'unifier_io']]
        return






#id, name, mimeType, createdTime

# dl = DriveDownloader()
# root_folder_id = '1ZYtG8roWBaeEdrHk0KSahAh4gPEiTOG5'
# files = dl.root.children[0].children[1].children[0].files

# dir = './tmp/|root|burning-brothers|brand_io|March-April 2021|.csv'
# folder_id = '12KlfgSMNXqb3C8VRocTQbqxIBu8KlEuy'
