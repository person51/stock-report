# 台股大盤及權值股價量分析自動化報告系統

這是一個全自動化的台股市場分析工具。系統每日會自動下載今日台股大盤及三大權值股的即時價量數據、繪製 30 日走勢與均線圖、抓取 Yahoo 焦點新聞，並將其渲染為精美的毛玻璃風格 (Glassmorphism) HTML 報表後，自動上傳至 Google 雲端硬碟進行歸檔與備份。

---

## 目錄
- [1. 專案介紹](#1-專案介紹)
- [2. 安裝指引](#2-安裝指引)
- [3. Google 雲端硬碟 API 設定指引（最重要）](#3-google-雲端硬碟-api-設定指引最重要)
- [4. 專案自訂設定 (config.json)](#4-專案自訂設定-configjson)
- [5. Windows 定時自動排程教學](#5-windows-定時自動排程教學)

---

## 1. 專案介紹

本專案旨在提供一個輕量且美觀的台股每日盤後分析自動化方案。主要核心流程包含：
1. **數據獲取**：獲取今日台股大盤（預設為加權指數 `^TWII`）及三大權值股（預設為台積電 `2330.TW`、鴻海 `2317.TW`、聯發科 `2454.TW`）的最新即時價量與歷史數據。
2. **走勢繪製**：繪製包含 30 日收盤價走勢與 5 日/20 日移動平均線 (MA) 的分析圖表，並將圖表以 Base64 格式安全內嵌至報告中，不產生多餘的本地圖片碎片。
3. **新聞抓取**：抓取 Yahoo 財經的最新焦點新聞，掌握今日市場熱點與重大消息。
4. **報表渲染**：採用現代感十足的 **Glassmorphism (毛玻璃微光風格)** 設計範本，將數據與新聞渲染成精美的單頁式 HTML 互動報表。
5. **雲端硬碟備份**：透過 Google Drive API 自動將報表上傳至指定的雲端資料夾，若偵測到同名檔案（同日期）則會自動執行覆蓋更新，確保雲端檔案最新且不重複。

---

## 2. 安裝指引

請確保您的系統已安裝 **Python 3.8** 或以上版本。請依照以下步驟完成環境設定：

1. 開啟終端機（如命令提示字元 CMD 或 PowerShell）。
2. 切換至本專案的根目錄：
   ```bash
   cd /d "d:\ai\stock-report"
   ```
3. 執行以下指令以安裝專案所需的第三方套件：
   ```bash
   pip install -r requirements.txt
   ```

> [!NOTE]
> `requirements.txt` 中包含 `yfinance`（獲取股價數據）、`pandas`（數據處理）、`matplotlib`（繪製圖表）、`beautifulsoup4` 與 `requests`（新聞抓取）、`Jinja2`（HTML 模板渲染）以及 `google-api-python-client` 相關套件（雲端硬碟 API 串接）。

---

## 3. Google 雲端硬碟 API 設定指引（最重要）

為了讓系統能夠自動將報表上傳至 Google 雲端硬碟，您需要建立一個 Google Cloud 專案並下載憑證。請依照以下步驟一步步完成設定：

### 步驟 1：前往 Google Cloud Console 並建立專案
1. 開啟瀏覽器，前往 [Google Cloud Console](https://console.cloud.google.com/)。
2. 登入您的 Google 帳號。
3. 點選頁面左上角的專案選擇下拉選單，並點選右上角的「**新增專案 (New Project)**」。
4. 輸入專案名稱（例如：`Stock-Report-Automation`），然後點選「**建立 (Create)**」。

### 步驟 2：啟用 Google Drive API
1. 確保控制台當前選取的專案是您剛剛建立的專案。
2. 在頂端搜尋列中輸入「**Google Drive API**」並進行搜尋。
3. 在搜尋結果中點選「Google Drive API」。
4. 點選「**啟用 (Enable)**」按鈕。

### 步驟 3：設定 OAuth 同意畫面 (OAuth Consent Screen)
1. 在左側導覽選單中，點選「**OAuth 同意畫面 (OAuth consent screen)**」。
2. 使用者類型 (User Type) 選擇「**外部 (External)**」，然後點選「**建立 (Create)**」。
3. 填寫基本應用程式資訊（僅需填寫必要欄位）：
   - **應用程式名稱 (App name)**：例如 `Stock Report Uploader`。
   - **使用者支援電子郵件 (User support email)**：選擇您的 Google 信箱。
   - **開發人員聯絡資訊 (Developer contact information)**：輸入您的電子郵件信箱。
4. 點選「**儲存並繼續 (Save and Continue)**」。
5. **重要（測試使用者設定）**：
   - 繼續點選「儲存並繼續」直到進入「**測試使用者 (Test users)**」頁面。
   - 點選「**+ ADD USERS (新增使用者)**」。
   - **必須輸入您用來進行授權與登入的 Google 帳號（即您自己的 Google 信箱）**。若未加入，稍後登入授權時會出現權限阻擋錯誤。
   - 輸入後點選「新增」，再點選「**儲存並繼續**」回到資訊主頁。

### 步驟 4：建立「電腦版應用程式 (Desktop App)」憑證
1. 在左側導覽選單中，點選「**憑證 (Credentials)**」。
2. 點選頁面頂部的「**+ 建立憑證 (+ CREATE CREDENTIALS)**」，並選擇「**OAuth 用戶端識別碼 (OAuth client ID)**」。
3. 應用程式類型 (Application type) 選擇「**電腦版應用程式 (Desktop App)**」。
4. 名稱 (Name) 可以使用預設值或自訂（例如 `Stock Report Desktop Client`）。
5. 點選「**建立 (Create)**」。

### 步驟 5：下載憑證並重新命名
1. 建立成功後，會彈出顯示「OAuth 用戶端已建立」的對話框。
2. 點選「**下載 JSON (Download JSON)**」圖示，將檔案下載至您的電腦。
3. 將該 JSON 檔案重新命名為 **`client_secrets.json`**（注意副檔名必須是 `.json`）。
4. 將 `client_secrets.json` 複製並放入本專案的**根目錄**下（即與 `generate_report.py` 同一層級）。

### 步驟 6：首次執行與一次性登入授權
1. 在專案根目錄下，手動執行以下指令以啟動程式：
   ```bash
   python generate_report.py
   ```
2. 由於是首次執行，系統會偵測到無 Token，並**自動在您的預設瀏覽器中開啟 Google OAuth 登入頁面**。
3. 請選擇您在「步驟 3」中加入的**測試 Google 帳號**進行登入。
4. 瀏覽器可能會顯示「Google 尚未驗證此應用程式 (Google hasn’t verified this app)」的安全性警告。
5. 點選「**進階 (Advanced)**」，接著點選「**前往「Stock Report Uploader」（不安全）(Go to Stock Report Uploader (unsafe))**」。
6. 勾選授予該應用程式存取您 Google 雲端硬碟特定檔案的權限，然後點選「**繼續 (Continue)**」。
7. 授權完成後，瀏覽器會顯示「The authentication flow has completed. You may close this window.」代表驗證成功，即可關閉瀏覽器網頁。
8. 此時，專案根目錄下會自動生成一個加密的快取憑證檔案 **`token.json`**。
9. 往後執行此腳本時，系統會自動讀取 `token.json` 進行靜態靜默驗證，**不再需要開啟瀏覽器進行手動登入**，達成了完全自動化的背景運作。

---

## 4. 專案自訂設定 (`config.json`)

您可以透過編輯專案根目錄下的 [config.json](file:///d:/ai/stock-report/config.json) 檔案來變更分析的個股標的與雲端硬碟歸檔位置。

設定檔格式如下：
```json
{
  "parent_folder_id": "",
  "tickers": ["2330.TW", "2317.TW", "2454.TW"],
  "market_ticker": "^TWII"
}
```

### 設定參數說明
- **`market_ticker`**：大盤指數代碼。預設為台灣加權指數 `^TWII`。
- **`tickers`**：分析與追蹤的個股代碼清單。您可以依需求增減，代碼格式必須與 Yahoo Finance 一致（例如台股個股需加上 `.TW` 後綴，如台積電為 `2330.TW`、鴻海為 `2317.TW`、聯發科為 `2454.TW`）。
- **`parent_folder_id`**：Google 雲端硬碟目標資料夾的唯一識別碼。
  - **如何取得資料夾 ID**：
    1. 開啟您的 Google 雲端硬碟網頁版。
    2. 進入您想要用來存放歷史報告的特定資料夾（如果沒有，請先新建一個）。
    3. 查看瀏覽器的網址列，網址的最後一段字串即為該資料夾的 ID。
       - 例如網址為：`https://drive.google.com/drive/folders/1aBcDeFgHiJkLmNoPqRsTuVwXyZ`
       - 則資料夾 ID 即為：`1aBcDeFgHiJkLmNoPqRsTuVwXyZ`
    4. 將該 ID 複製並貼入 `parent_folder_id` 欄位中。
  - **注意**：如果此欄位保持為空字串 `""`，產生的報告預設會直接上傳至您 Google 雲端硬碟的根目錄。

---

## 5. Windows 定時自動排程教學

為了讓報告在每日台股收盤後（例如下午 14:30）自動產生並上傳，我們可以使用 Windows 內建的「工作排程器」進行排程設定。

### 步驟 1：建立排程啟動批次檔 (`run_report.bat`)
由於 Windows 工作排程器在背景執行 Python 腳本時常會因為環境變數或工作路徑不正確而失敗，最穩妥的做法是建立一個批次檔：
1. 在專案根目錄下新建一個文字檔案，命名為 `run_report.bat`。
2. 以文字編輯器打開它，並寫入以下內容：
   ```bat
   @echo off
   cd /d "d:\ai\stock-report"
   python generate_report.py
   ```
   *（如果您的 Python 是安裝在虛擬環境中，請將 `python` 替換為您虛擬環境下 `Scripts\python.exe` 的完整路徑，例如 `"d:\ai\stock-report\venv\Scripts\python.exe"`）*
3. 儲存並關閉檔案。您可以雙擊執行該批次檔以測試是否能正常產生報告並上傳。

### 步驟 2：設定 Windows 工作排程器 (Task Scheduler)
1. 同時按下鍵盤 `Win + R` 鍵，輸入 `taskschd.msc` 並按下 Enter 鍵，開啟「工作排程器」。
2. 在右側的「動作」窗格中，點選「**建立基本工作... (Create Basic Task...)**」。
3. **名稱與描述**：
   - 輸入工作名稱：`Daily Stock Report AutoRun`。
   - 描述：每日下午 14:30 自動分析台股數據並備份至雲端。
   - 點選「下一步」。
4. **工作觸發程序**：
   - 選擇「**每日 (Daily)**」，點選「下一步」。
   - 設定開始時間與週期：將時間設定為每日下午的 **14:30:00**（即 14:30）。
   - 點選「下一步」。
5. **動作**：
   - 選擇「**啟動程式 (Start a program)**」，點選「下一步」。
6. **啟動程式參數設定**：
   - **程式或指令碼 (Program/script)**：點選「瀏覽」，選擇您剛剛建立的批次檔路徑（例如：`d:\ai\stock-report\run_report.bat`）。
   - **開始位置 (選填) (Start in)**：輸入專案的根目錄 `d:\ai\stock-report`（**重要：請注意此欄位不要加雙引號**）。
   - 點選「下一步」。
7. 確認所有設定無誤後，點選「**完成 (Finish)**」。
8. **驗證與測試**：
   - 在工作排程器中找到剛建立的 `Daily Stock Report AutoRun`。
   - 在其上點選滑鼠右鍵，選擇「**執行 (Run)**」。
   - 確認是否會彈出命令提示字元視窗，並且專案目錄下會產生新的報告，且雲端硬碟也成功收到更新的檔案。
