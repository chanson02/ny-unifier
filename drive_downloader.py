import os, pickle, io
from datetime import datetime
from googleapiclient.discovery import build
from apiclient.http import MediaIoBaseDownload
from google.oauth2.credentials import Credentials


class DriveDownloader:
    def __init__(self, out_path='./drive_downloaded'):
        self.out_path = out_path
        creds = Credentials.from_authorized_user_file('token.json', ['https://www.googleapis.com/auth/drive'])
        self.service = build('drive', 'v3', credentials=creds)
        self.clear_storage()

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

        file_handler = io.BytesIO()
        downloader = MediaIoBaseDownload(file_handler, download_request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        with io.open(os.path.join(out_path, filename), 'wb') as f:
            file_handler.seek(0)
            f.write(file_handler.read())


# service.drives().list().execute()
# files = service.files().list(fields='files(id, name, mimeType, createdTime)').execute()['files']
# file = files[0]

#id, name, mimeType, createdTime
