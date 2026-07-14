import pytest
from unittest.mock import MagicMock, patch, mock_open
import os

# 匯入待測試的模組與函式
from src.drive_uploader import authenticate_drive, upload_or_update_file


@patch("src.drive_uploader.os.path.exists")
@patch("src.drive_uploader.Credentials")
@patch("src.drive_uploader.build")
def test_authenticate_drive_token_exists_and_valid(
    mock_build, mock_credentials_cls, mock_exists
):
    """測試 token.json 存在且有效的情境。"""
    mock_exists.return_value = True

    # 模擬 Credentials 實例，設定為有效 (valid = True)
    mock_creds = MagicMock()
    mock_creds.valid = True
    mock_credentials_cls.from_authorized_user_file.return_value = mock_creds

    # 模擬 build 傳回的 service
    mock_service = MagicMock()
    mock_build.return_value = mock_service

    # 執行驗證
    service = authenticate_drive()

    # 斷言檢查
    mock_exists.assert_called_once_with("token.json")
    mock_credentials_cls.from_authorized_user_file.assert_called_once_with(
        "token.json", ["https://www.googleapis.com/auth/drive.file"]
    )
    mock_build.assert_called_once_with("drive", "v3", credentials=mock_creds)
    assert service == mock_service


@patch("src.drive_uploader.os.path.exists")
@patch("src.drive_uploader.Credentials")
@patch("src.drive_uploader.Request")
@patch("src.drive_uploader.build")
@patch("builtins.open", new_callable=mock_open)
def test_authenticate_drive_token_expired_refresh(
    mock_file, mock_build, mock_request_cls, mock_credentials_cls, mock_exists
):
    """測試 token.json 存在但已過期，且可以進行重新整理 (refresh) 的情境。"""
    mock_exists.return_value = True

    # 模擬已過期但含有 refresh_token 的 Credentials
    mock_creds = MagicMock()
    mock_creds.valid = False
    mock_creds.expired = True
    mock_creds.refresh_token = "some_refresh_token"
    mock_creds.to_json.return_value = '{"token": "new_dummy_token"}'
    mock_credentials_cls.from_authorized_user_file.return_value = mock_creds

    # 模擬 Request 與 build 服務
    mock_request = MagicMock()
    mock_request_cls.return_value = mock_request
    mock_service = MagicMock()
    mock_build.return_value = mock_service

    # 執行驗證
    service = authenticate_drive()

    # 斷言檢查
    mock_creds.refresh.assert_called_once_with(mock_request)
    mock_file.assert_called_once_with("token.json", "w")
    mock_file().write.assert_called_once_with('{"token": "new_dummy_token"}')
    assert service == mock_service


@patch("src.drive_uploader.os.path.exists")
@patch("src.drive_uploader.InstalledAppFlow")
@patch("src.drive_uploader.build")
@patch("builtins.open", new_callable=mock_open)
def test_authenticate_drive_no_token(
    mock_file, mock_build, mock_flow_cls, mock_exists
):
    """測試 token.json 不存在，必須啟動本地 OAuth2 流程的情境。"""
    mock_exists.return_value = False

    # 模擬 InstalledAppFlow 流程
    mock_flow = MagicMock()
    mock_creds = MagicMock()
    mock_creds.to_json.return_value = '{"token": "new_oauth_token"}'
    mock_flow.run_local_server.return_value = mock_creds
    mock_flow_cls.from_client_secrets_file.return_value = mock_flow

    # 模擬 build 服務
    mock_service = MagicMock()
    mock_build.return_value = mock_service

    # 執行驗證
    service = authenticate_drive()

    # 斷言檢查
    mock_flow_cls.from_client_secrets_file.assert_called_once_with(
        "client_secrets.json", ["https://www.googleapis.com/auth/drive.file"]
    )
    mock_flow.run_local_server.assert_called_once_with(port=0)
    mock_file.assert_called_once_with("token.json", "w")
    mock_file().write.assert_called_once_with('{"token": "new_oauth_token"}')
    assert service == mock_service


@patch("src.drive_uploader.authenticate_drive")
@patch("src.drive_uploader.MediaFileUpload")
def test_upload_or_update_file_exists_overwrite(mock_media_file, mock_auth):
    """測試上傳檔案時，雲端硬碟已存在同名檔案，應執行覆蓋更新 (update)。"""
    mock_service = MagicMock()
    mock_auth.return_value = mock_service

    # 模擬 list().execute() 傳回包含一個同名檔案的列表
    mock_list_execute = MagicMock()
    mock_list_execute.execute.return_value = {
        "files": [{"id": "existing_file_id_123", "name": "test_report.html"}]
    }
    mock_service.files.return_value.list.return_value = mock_list_execute

    # 模擬 update().execute() 傳回更新後的檔案資訊
    mock_update_execute = MagicMock()
    mock_update_execute.execute.return_value = {"id": "existing_file_id_123"}
    mock_service.files.return_value.update.return_value = mock_update_execute

    # 模擬 MediaFileUpload 實例
    mock_media = MagicMock()
    mock_media_file.return_value = mock_media

    # 執行驗證
    file_id = upload_or_update_file(
        "test_report.html", "dummy_path/test_report.html", "parent_folder_id_789"
    )

    # 斷言檢查搜尋 API 參數
    expected_q = "name = 'test_report.html' and 'parent_folder_id_789' in parents and trashed = false"
    mock_service.files.return_value.list.assert_called_once_with(
        q=expected_q, spaces="drive", fields="files(id, name)"
    )

    # 斷言檢查 MediaFileUpload 初始化
    mock_media_file.assert_called_once_with(
        "dummy_path/test_report.html", mimetype="text/html"
    )

    # 斷言檢查 update 呼叫
    mock_service.files.return_value.update.assert_called_once_with(
        fileId="existing_file_id_123", media_body=mock_media
    )

    assert file_id == "existing_file_id_123"


@patch("src.drive_uploader.authenticate_drive")
@patch("src.drive_uploader.MediaFileUpload")
def test_upload_or_update_file_not_exists_create(mock_media_file, mock_auth):
    """測試上傳檔案時，雲端硬碟中無此同名檔案，應執行新建檔案 (create)。"""
    mock_service = MagicMock()
    mock_auth.return_value = mock_service

    # 模擬 list().execute() 傳回空列表
    mock_list_execute = MagicMock()
    mock_list_execute.execute.return_value = {"files": []}
    mock_service.files.return_value.list.return_value = mock_list_execute

    # 模擬 create().execute() 傳回新建立檔案的 ID
    mock_create_execute = MagicMock()
    mock_create_execute.execute.return_value = {"id": "new_file_id_456"}
    mock_service.files.return_value.create.return_value = mock_create_execute

    # 模擬 MediaFileUpload 實例
    mock_media = MagicMock()
    mock_media_file.return_value = mock_media

    # 執行驗證
    file_id = upload_or_update_file(
        "test_report.html", "dummy_path/test_report.html", "parent_folder_id_789"
    )

    # 斷言檢查搜尋 API 參數
    expected_q = "name = 'test_report.html' and 'parent_folder_id_789' in parents and trashed = false"
    mock_service.files.return_value.list.assert_called_once_with(
        q=expected_q, spaces="drive", fields="files(id, name)"
    )

    # 斷言檢查 MediaFileUpload 初始化
    mock_media_file.assert_called_once_with(
        "dummy_path/test_report.html", mimetype="text/html"
    )

    # 斷言檢查 create 呼叫
    expected_metadata = {
        "name": "test_report.html",
        "parents": ["parent_folder_id_789"],
    }
    mock_service.files.return_value.create.assert_called_once_with(
        body=expected_metadata, media_body=mock_media, fields="id"
    )

    assert file_id == "new_file_id_456"
