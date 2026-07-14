# 台灣股市大盤每日分析報告生成器 - 設計規格書 (Design Specification)

此文件定義了台灣股市每日大盤分析報告自動化生成與雲端硬碟自動上傳系統的設計與規格。

---

## 1. 專案目標
建立一個基於 Python 的獨立自動化腳本，能於每日台股收盤後（下午 13:30 之後，建議 14:30 以便取得完整三大法人與新聞資訊）執行：
1. 獲取當日加權指數（`^TWII`）及三大權值股（台積電 `2330.TW`、鴻海 `2317.TW`、聯發科 `2454.TW`）的今日表現與 30 日歷史價量數據。
2. 抓取今日焦點財經新聞（Yahoo 股市 RSS）。
3. 繪製精美的大盤 30 日收盤價與均線（5MA, 10MA, 20MA）走勢折線圖，並搭配下方成交量柱狀圖，將圖表轉為 Base64 嵌入 HTML。
4. 渲染出一個符合現代美學的深色模式（Sleek Dark Mode）HTML 報告。
5. 使用 Google Drive API 自動上傳至使用者的雲端硬碟指定目錄下，支援首次瀏覽器 OAuth 授權與後續自動更新 Token。

---

## 2. 目錄結構

專案目錄 `d:\ai\stock-report` 的結構如下：

```text
stock-report/
├── docs/
│   └── superpowers/
│       └── specs/
│           └── 2026-07-14-taiwan-stock-report-design.md  # 本設計規格書
├── templates/
│   └── report_template.html                              # HTML 報告 Jinja2 範本
├── config.json                                           # 專案設定檔 (個股清單、雲端資料夾 ID)
├── requirements.txt                                      # Python 套件依賴清單
├── generate_report.py                                    # 主執行腳本
├── README.md                                             # 專案中文說明文件 (含 Google Drive 設定步驟)
├── client_secrets.json                                   # Google Drive API 憑證 (使用者提供)
└── token.json                                            # Google OAuth2 快取憑證 (自動生成)
```

---

## 3. 數據獲取與分析設計

### 3.1 股市數據 (`yfinance`)
*   **加權指數 (`^TWII`)**：
    *   今日開盤價、最高價、最低價、收盤價、成交量。
    *   計算今日漲跌點數（今日收盤 - 昨日收盤）與漲跌幅。
    *   獲取過去 30 個交易日的歷史收盤價與成交量。
*   **三大權值股 (`2330.TW`, `2317.TW`, `2454.TW`)**：
    *   今日收盤價、今日漲跌幅、今日成交量。

### 3.2 焦點新聞抓取 (`requests` & `BeautifulSoup`)
*   **來源**：Yahoo 股市台股焦點新聞 RSS (`https://tw.stock.yahoo.com/rss?category=tw-market`)。
*   **解析內容**：最新 5 則新聞的標題（Title）、新聞來源（Source）、發布時間（PubDate）、新聞連結（Link）。

### 3.3 技術指標計算
*   使用 pandas 計算 30 日數據的移動平均線：
    *   **5日均線 (5MA)**
    *   **10日均線 (10MA)**
    *   **20日均線 (20MA)**

---

## 4. 視覺圖表設計

### 4.1 Matplotlib 繪圖規格
*   **畫布結構**：雙子圖（Subplots）垂直排列。
    *   上方子圖：收盤價折線圖（標示今日價格、5MA、10MA、20MA 折線）。
    *   下方子圖：成交量柱狀圖（上漲日顯示淡紅色，下跌日顯示淡綠色）。
*   **風格調整**：
    *   配合 HTML 深色模式，Matplotlib 畫布背景、文字、網格線均設定為深色調（如背景為 `#1e293b`，文字為白色，網格為微透明灰）。
    *   圖表字體設定為支援中文的字體（如 `Microsoft JhengHei`），避免中文標籤亂碼。
*   **Base64 嵌入**：
    *   使用 `io.BytesIO` 將圖表儲存為 PNG 格式。
    *   將二進位數據進行 Base64 編碼，轉換為字串：`data:image/png;base64,...`。
    *   將此字串傳遞給 Jinja2 範本渲染至 HTML。

---

## 5. HTML 報告設計與美化 (CSS Rule)

HTML 報告將採用響應式、現代感的深色風格設計，具體細節如下：
*   **字型**：`Outfit`, `Noto Sans TC`, sans-serif。
*   **背景色**：`linear-gradient(135deg, #0f172a 0%, #1e293b 100%)`。
*   **卡片設計**：
    *   毛玻璃背景：`background: rgba(30, 41, 59, 0.7)`。
    *   邊框：`border: 1px solid rgba(255, 255, 255, 0.08)`。
    *   模糊濾鏡：`backdrop-filter: blur(12px)`。
    *   陰影：`box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37)`。
*   **漲跌色彩**：
    *   上漲：漸層橘紅 `#ff416c` 到 `#ff4b2b`，搭配陰影效果。
    *   下跌：漸層翠綠 `#00b09b` 到 `#96c93d`。
*   **微動畫**：
    *   個股卡片懸停：`transform: translateY(-4px)`，邊框變亮 `border-color: rgba(255, 255, 255, 0.2)`，並使用 `transition: all 0.3s ease` 確保動畫平滑。
    *   新聞連結 hover 下底線平滑滑出。

---

## 6. Google Drive API 整合設計

### 6.1 授權流程
1.  **檢查快取**：程式優先讀取根目錄下的 `token.json`。
2.  **首次授權**：若 `token.json` 不存在或無效，讀取 `client_secrets.json` 並啟動本機伺服器，自動開啟瀏覽器進行 OAuth2 登入與授權。
3.  **儲存凭证**：授權成功後，將新憑證寫入 `token.json`，方便下次自動讀取。

### 6.2 檔案上傳與更新邏輯
1.  **目標目錄**：從 `config.json` 讀取 `parent_folder_id`。如果未設定，則上傳至根目錄。
2.  **重複檔案檢查**：
    *   在 Google Drive 中搜尋該資料夾下是否已有檔案名稱為 `台股大盤分析報告_YYYY-MM-DD.html` 且 MIME 類型為 `text/html` 的檔案。
3.  **覆蓋或新建**：
    *   **已存在**：取得其 `fileId`，呼叫 `files().update` 覆蓋檔案內容。
    *   **不存在**：呼叫 `files().create` 建立新檔案。

---

## 7. 驗證與測試計畫

### 7.1 自動化測試
*   執行 `generate_report.py` 驗證資料抓取是否正常。
*   檢查本地產生的 `report_YYYY-MM-DD.html` 是否能用瀏覽器正常開啟、樣式是否跑版、圖片是否正常嵌入。
*   驗證 Google Drive API 首次授權流程及第二次執行的自動跳過授權流程。

### 7.2 手動驗證
*   確認雲端硬碟中是否確實出現該報告檔案。
*   在 Google Drive Web 介面上點兩下預覽 HTML 報告，檢查其排版與 Base64 圖片是否正常顯示。
