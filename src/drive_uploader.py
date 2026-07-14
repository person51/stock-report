import os.path
import mimetypes
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# 定義存取權限範圍 (Scope)
SCOPES = ["https://www.googleapis.com/auth/drive.file"]


def authenticate_drive():
    """驗證並建立 Google Drive API 服務實例。

    檢查本地是否存在 token.json 快取檔案。若無或無效，
    則讀取 client_secrets.json 啟動本地 OAuth2 認證，並重新快取 Token。

    Returns:
        googleapiclient.discovery.Resource: Google Drive 服務實例。
    """
    creds = None
    # 檢查快取的 token.json 是否存在
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    # 若 credentials 不存在或無效
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # 讀取本地 client_secrets.json 啟動 OAuth 流程
            flow = InstalledAppFlow.from_client_secrets_file(
                "client_secrets.json", SCOPES
            )
            creds = flow.run_local_server(port=0)

        # 將新的 credentials 快取至 token.json
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    # 建立並傳回 Drive 服務實例
    service = build("drive", "v3", credentials=creds)
    return service


def upload_or_update_file(filename, filepath, parent_folder_id):
    """上傳檔案至 Google Drive，若雲端已存在同名檔案則覆蓋更新。

    於雲端硬碟指定資料夾內搜尋是否有同名檔案，若有則進行 overwrite，
    若無則建立新檔案，最後回傳該檔案的雲端 fileId。

    Args:
        filename (str): 雲端硬碟目標檔名。
        filepath (str): 本地欲上傳檔案之路徑。
        parent_folder_id (str): Google Drive 目標父資料夾 ID。

    Returns:
        str: 雲端檔案的唯一 fileId。
    """
    service = authenticate_drive()

    # 搜尋同檔名且在指定父資料夾下的未刪除檔案
    if parent_folder_id:
        q = f"name = '{filename}' and '{parent_folder_id}' in parents and trashed = false"
    else:
        q = f"name = '{filename}' and 'root' in parents and trashed = false"

    # 執行搜尋 API
    results = (
        service.files()
        .list(q=q, spaces="drive", fields="files(id, name)")
        .execute()
    )
    files = results.get("files", [])

    # 自動判斷檔案的 mimetype
    mimetype, _ = mimetypes.guess_type(filepath)
    if not mimetype:
        mimetype = "application/octet-stream"

    # 建立媒體上傳對象
    media = MediaFileUpload(filepath, mimetype=mimetype)

    if files:
        # 同名檔案已存在，進行覆蓋更新
        file_id = files[0]["id"]
        service.files().update(fileId=file_id, media_body=media).execute()
    else:
        # 同名檔案不存在，建立新檔案
        file_metadata = {"name": filename}
        if parent_folder_id:
            file_metadata["parents"] = [parent_folder_id]

        created_file = (
            service.files()
            .create(body=file_metadata, media_body=media, fields="id")
            .execute()
        )
        file_id = created_file.get("id")

    return file_id
