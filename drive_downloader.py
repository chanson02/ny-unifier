import os, pickle, io
from datetime import datetime
from googleapiclient.discovery import build
from apiclient.http import MediaIoBaseDownload

class DriveDownloader:
    def __init__(self):
        root_id = "1294yduUFyoaQNU-x-Tv7dzCz0zpa0NR_"
        self.service = build('drive', 'v3', credentials=self.get_creds())
        self.root = self.folder_contents(root_id)

    def get_creds(self):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
        return creds

    def folder_contents(self, folder):
        try:
            folder_id = folder["id"]
        except TypeError:
            folder_id = folder

        results = self.service.files().list(
            pageSize=100,
            q=f"parents in '{folder_id}'",
            fields="files(id, name, createdTime, mimeType)"
        ).execute()
        return results.get('files', [])

    def child_folders(self, folder):
        items = []
        for item in folder:
            if item["mimeType"] == "application/vnd.google-apps.folder":
                items.append(item)
        return items

    def latest_file(self, folder):
        times = []
        for item in folder:
            times.append(datetime.fromisoformat(item["createdTime"][:19]))

        recent = sorted(times)[-1]
        for item in folder:
            time = datetime.fromisoformat(item["createdTime"][:19])
            if recent == time:
                return item

    def download_file(self, file, out_path="/home/cooperhanson/Desktop/drive_downloaded/"):
        filename = file["name"].replace("/", "-")
        sheet_mime = 'application/vnd.google-apps.spreadsheet'

        if file["mimeType"] == sheet_mime:
            xlsx_mime = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            request = self.service.files().export(fileId=file["id"], mimeType=xlsx_mime)
            filename += ".xlsx"
        else:
            request = self.service.files().get_media(fileId=file["id"])

        file_handler = io.BytesIO()
        downloader = MediaIoBaseDownload(file_handler, request)
        done = False
        while done is False:
            _, done = downloader.next_chunk()

        with io.open(out_path + filename, "wb") as f:
            file_handler.seek(0)
            f.write(file_handler.read())

        return out_path + filename
