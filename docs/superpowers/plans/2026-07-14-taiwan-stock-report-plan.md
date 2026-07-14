# 台灣股市大盤每日分析報告生成器 - 實作計畫

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立一個可定時執行、具備 TDD 單元測試的 Python 系統，自動抓取今日台股大盤與權值股價量數據、焦點新聞，繪製 30 日走勢與均線圖並嵌入精美 HTML，最後透過 Google Drive API 自動上傳或覆蓋雲端報告。

**Architecture:** 
系統採用模組化設計以利單元測試。主要分為四個模組：`data_fetcher` (抓取股市與新聞數據)、`chart_generator` (繪製並將圖表轉為 Base64 嵌入)、`report_generator` (Jinja2 樣式渲染) 與 `drive_uploader` (OAuth 認證與 Drive 上傳)。主程式 `generate_report.py` 負責協調整個流程。

**Tech Stack:** Python 3.x, yfinance, pandas, matplotlib, Jinja2, BeautifulSoup4, google-api-python-client, pytest

---

## 預計異動與新建檔案清單
*   [NEW] `requirements.txt`：依賴套件管理
*   [NEW] `config.json`：設定檔
*   [NEW] `src/__init__.py`
*   [NEW] `src/data_fetcher.py`
*   [NEW] `src/chart_generator.py`
*   [NEW] `src/report_generator.py`
*   [NEW] `src/drive_uploader.py`
*   [NEW] `generate_report.py`：主進入點
*   [NEW] `templates/report_template.html`：HTML 樣式範本
*   [NEW] `tests/__init__.py`
*   [NEW] `tests/test_data_fetcher.py`
*   [NEW] `tests/test_chart_generator.py`
*   [NEW] `tests/test_report_generator.py`
*   [NEW] `README.md`

---

### Task 1: 初始化環境與配置文件 (requirements.txt, config.json)

**Files:**
*   Create: `requirements.txt`
*   Create: `config.json`

- [ ] **Step 1: 建立 requirements.txt 依賴檔**
  內容：
  ```text
  yfinance>=0.2.38
  pandas>=2.0.0
  matplotlib>=3.7.0
  beautifulsoup4>=4.12.0
  requests>=2.31.0
  Jinja2>=3.1.0
  google-api-python-client>=2.100.0
  google-auth-httplib2>=0.1.0
  google-auth-oauthlib>=1.1.0
  pytest>=8.0.0
  ```

- [ ] **Step 2: 建立 config.json 設定檔**
  預設將雲端資料夾 ID 留空（上傳至根目錄），並設定追蹤股代號。
  內容：
  ```json
  {
    "parent_folder_id": "",
    "tickers": ["2330.TW", "2317.TW", "2454.TW"],
    "market_ticker": "^TWII"
  }
  ```

- [ ] **Step 3: 建立 pytest 測試環境驗證**
  在本地安裝上述依賴套件（可以使用 pip），並執行一個簡單的 `pytest` 指令確保測試框架能正常運作。
  執行命令：`pytest --version`
  預期輸出：顯示 pytest 版本號碼。

---

### Task 2: 數據獲取與焦點新聞模組 (data_fetcher)

**Files:**
*   Create: `src/data_fetcher.py`
*   Create: `tests/test_data_fetcher.py`

- [ ] **Step 1: 撰寫數據獲取模組的測試檔**
  在 `tests/test_data_fetcher.py` 中撰寫測試。
  內容：
  ```python
  import pytest
  from src.data_fetcher import fetch_stock_data, fetch_market_news

  def test_fetch_stock_data():
      # 測試獲取加權指數與個股數據
      tickers = ["2330.TW", "2317.TW", "2454.TW"]
      market_ticker = "^TWII"
      data = fetch_stock_data(market_ticker, tickers)
      
      assert "market" in data
      assert data["market"]["ticker"] == "^TWII"
      assert "close" in data["market"]
      assert "history" in data["market"]
      assert len(data["stocks"]) == 3
      assert data["stocks"][0]["ticker"] == "2330.TW"
      assert "close" in data["stocks"][0]

  def test_fetch_market_news():
      # 測試新聞抓取是否成功解析為字典列表
      news = fetch_market_news()
      assert isinstance(news, list)
      if len(news) > 0:
          assert "title" in news[0]
          assert "link" in news[0]
          assert "source" in news[0]
  ```

- [ ] **Step 2: 執行測試並確認其失敗**
  執行命令：`pytest tests/test_data_fetcher.py`
  預期輸出：`ModuleNotFoundError: No module named 'src'`

- [ ] **Step 3: 實作 `src/data_fetcher.py`**
  內容：
  ```python
  import yfinance as yf
  import requests
  from bs4 import BeautifulSoup
  import pandas as pd

  def fetch_stock_data(market_ticker: str, tickers: list) -> dict:
      result = {"market": {}, "stocks": []}
      
      # 1. 抓取大盤數據 (30個交易日)
      m_ticker = yf.Ticker(market_ticker)
      m_hist = m_ticker.history(period="45d") # 抓多一點確保扣除假日有30天
      if len(m_hist) >= 30:
          m_hist = m_hist.tail(30)
      
      # 計算今日收盤與昨日收盤
      today_close = m_hist['Close'].iloc[-1]
      prev_close = m_hist['Close'].iloc[-2]
      change = today_close - prev_close
      change_pct = (change / prev_close) * 100
      
      # 計算均線
      m_hist['5MA'] = m_hist['Close'].rolling(window=5).mean()
      m_hist['10MA'] = m_hist['Close'].rolling(window=10).mean()
      m_hist['20MA'] = m_hist['Close'].rolling(window=20).mean()
      
      result["market"] = {
          "ticker": market_ticker,
          "name": "加權指數",
          "close": round(today_close, 2),
          "open": round(m_hist['Open'].iloc[-1], 2),
          "high": round(m_hist['High'].iloc[-1], 2),
          "low": round(m_hist['Low'].iloc[-1], 2),
          "volume": int(m_hist['Volume'].iloc[-1]),
          "change": round(change, 2),
          "change_pct": round(change_pct, 2),
          "history": m_hist.to_dict(orient="index") # 用於傳給繪圖模組
      }
      
      # 2. 抓取個股數據
      name_map = {"2330.TW": "台積電", "2317.TW": "鴻海", "2454.TW": "聯發科"}
      for ticker in tickers:
          t = yf.Ticker(ticker)
          hist = t.history(period="2d")
          if len(hist) >= 2:
              t_close = hist['Close'].iloc[-1]
              p_close = hist['Close'].iloc[-2]
              t_change = t_close - p_close
              t_change_pct = (t_change / p_close) * 100
              
              result["stocks"].append({
                  "ticker": ticker,
                  "name": name_map.get(ticker, ticker),
                  "close": round(t_close, 2),
                  "open": round(hist['Open'].iloc[-1], 2),
                  "high": round(hist['High'].iloc[-1], 2),
                  "low": round(hist['Low'].iloc[-1], 2),
                  "volume": int(hist['Volume'].iloc[-1]),
                  "change": round(t_change, 2),
                  "change_pct": round(t_change_pct, 2)
              })
      
      return result

  def fetch_market_news() -> list:
      # 抓取 Yahoo 股市台股 RSS
      url = "https://tw.stock.yahoo.com/rss?category=tw-market"
      headers = {"User-Agent": "Mozilla/5.0"}
      news_list = []
      try:
          resp = requests.get(url, headers=headers, timeout=10)
          if resp.status_code == 200:
              soup = BeautifulSoup(resp.content, "xml")
              items = soup.find_all("item")
              for item in items[:5]: # 抓最新 5 條
                  title = item.find("title").text if item.find("title") else "無標題"
                  link = item.find("link").text if item.find("link") else "#"
                  pub_date = item.find("pubDate").text if item.find("pubDate") else ""
                  source = "Yahoo股市"
                  news_list.append({
                      "title": title,
                      "link": link,
                      "pub_date": pub_date,
                      "source": source
                  })
      except Exception as e:
          print(f"抓取新聞時發生錯誤: {e}")
      return news_list
  ```

- [ ] **Step 4: 執行測試並確認其通過**
  執行命令：`pytest tests/test_data_fetcher.py -v`
  預期輸出：`test_fetch_stock_data PASSED`, `test_fetch_market_news PASSED`

---

### Task 3: 走勢圖與均線圖繪製模組 (chart_generator)

**Files:**
*   Create: `src/chart_generator.py`
*   Create: `tests/test_chart_generator.py`

- [ ] **Step 1: 撰寫圖表繪製模組的測試檔**
  內容：
  ```python
  import pytest
  import pandas as pd
  from src.chart_generator import generate_market_chart

  def test_generate_market_chart():
      # 模擬 30 天的大盤歷史數據
      date_range = pd.date_range(end="2026-07-14", periods=30)
      mock_history = {}
      for i, date in enumerate(date_range):
          mock_history[date] = {
              "Close": 20000.0 + (i * 10),
              "Volume": 300000000 + (i * 100000),
              "5MA": 20000.0 + (i * 10),
              "10MA": 20000.0 + (i * 10),
              "20MA": 20000.0 + (i * 10)
          }
      
      base64_str = generate_market_chart(mock_history)
      assert isinstance(base64_str, str)
      assert base64_str.startswith("data:image/png;base64,")
  ```

- [ ] **Step 2: 執行測試並確認其失敗**
  執行命令：`pytest tests/test_chart_generator.py`
  預期輸出：`ModuleNotFoundError: No module named 'src.chart_generator'`

- [ ] **Step 3: 實作 `src/chart_generator.py`**
  內容：
  ```python
  import io
  import base64
  import matplotlib.pyplot as plt
  import matplotlib.dates as mdates
  import pandas as pd

  # 設定支援中文字型，防止亂碼
  plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'DejaVu Sans', 'Arial Unicode MS']
  plt.rcParams['axes.unicode_minus'] = False

  def generate_market_chart(history_dict: dict) -> str:
      # 將字典轉回 DataFrame，按日期排序
      df = pd.DataFrame.from_dict(history_dict, orient="index")
      df.index = pd.to_datetime(df.index)
      df = df.sort_index()

      # 設定畫布為深色風格
      fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6), sharex=True, 
                                     gridspec_kw={'height_ratios': [3, 1]})
      
      fig.patch.set_facecolor('#1e293b') # 外背景色
      ax1.set_facecolor('#1e293b') # 內背景色
      ax2.set_facecolor('#1e293b')

      # 1. 繪製收盤價與均線 (5MA, 10MA, 20MA)
      ax1.plot(df.index, df['Close'], label="收盤價", color="#38bdf8", linewidth=2.5)
      if '5MA' in df.columns:
          ax1.plot(df.index, df['5MA'], label="5MA", color="#f43f5e", linestyle="--", linewidth=1.2)
      if '10MA' in df.columns:
          ax1.plot(df.index, df['10MA'], label="10MA", color="#fbbf24", linestyle="--", linewidth=1.2)
      if '20MA' in df.columns:
          ax1.plot(df.index, df['20MA'], label="20MA", color="#34d399", linestyle="--", linewidth=1.2)

      ax1.set_title("台灣加權指數 30日走勢與移動平均線", color="#ffffff", fontsize=14, pad=15)
      ax1.legend(loc="upper left", facecolor="#0f172a", edgecolor="none", labelcolor="#ffffff")
      ax1.grid(True, color="#334155", linestyle=":", alpha=0.6)
      ax1.tick_params(colors="#94a3b8")
      ax1.spines['bottom'].set_color('#334155')
      ax1.spines['top'].set_color('none')
      ax1.spines['left'].set_color('#334155')
      ax1.spines['right'].set_color('none')

      # 2. 繪製成交量柱狀圖
      # 計算今日相較昨日的漲跌，用以著色
      colors = []
      for i in range(len(df)):
          if i == 0:
              colors.append("#ef4444") # 預設紅色 (漲)
          else:
              if df['Close'].iloc[i] >= df['Close'].iloc[i-1]:
                  colors.append("#ef4444") # 漲為紅 (台股習慣)
              else:
                  colors.append("#22c55e") # 跌為綠
                  
      # 將成交量單位改為億元或張數，這裡用張數/1000 (千股/手) 或純數值，大盤成交量 yfinance 單位通常是股
      # 為了圖表易讀，大盤量除以 100,000,000 (億股/張)
      volume_in_billion = df['Volume'] / 1e8
      ax2.bar(df.index, volume_in_billion, color=colors, alpha=0.8, width=0.6)
      ax2.set_ylabel("成交量 (億)", color="#94a3b8", fontsize=10)
      ax2.grid(True, color="#334155", linestyle=":", alpha=0.6)
      ax2.tick_params(colors="#94a3b8")
      ax2.spines['bottom'].set_color('#334155')
      ax2.spines['top'].set_color('none')
      ax2.spines['left'].set_color('#334155')
      ax2.spines['right'].set_color('none')

      # 格式化日期軸
      plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
      plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=3))
      plt.gcf().autofmt_xdate()

      plt.tight_layout()
      
      # 轉為 Base64 字串
      buf = io.BytesIO()
      plt.savefig(buf, format='png', dpi=120, facecolor=fig.get_facecolor(), edgecolor='none')
      plt.close(fig)
      
      buf.seek(0)
      img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
      return f"data:image/png;base64,{img_base64}"
  ```

- [ ] **Step 4: 執行測試並確認其通過**
  執行命令：`pytest tests/test_chart_generator.py -v`
  預期輸出：`test_generate_market_chart PASSED`

---

### Task 4: HTML 範本與報告生成模組 (report_generator)

**Files:**
*   Create: `templates/report_template.html`
*   Create: `src/report_generator.py`
*   Create: `tests/test_report_generator.py`

- [ ] **Step 1: 建立 HTML Jinja2 範本檔 (`templates/report_template.html`)**
  設計深色模式、毛玻璃效果、紅綠漸層樣式的網頁。
  內容：
  ```html
  <!DOCTYPE html>
  <html lang="zh-TW">
  <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>台股每日大盤分析報告 - {{ date }}</title>
      <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Noto+Sans+TC:wght@300;400;700&display=swap" rel="stylesheet">
      <style>
          :root {
              --bg-gradient: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
              --card-bg: rgba(30, 41, 59, 0.7);
              --card-border: 1px solid rgba(255, 255, 255, 0.08);
              --text-primary: #f8fafc;
              --text-secondary: #94a3b8;
              --up-color: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%);
              --down-color: linear-gradient(135deg, #00b09b 0%, #96c93d 100%);
          }
          * {
              box-sizing: border-box;
              margin: 0;
              padding: 0;
          }
          body {
              font-family: 'Outfit', 'Noto Sans TC', sans-serif;
              background: var(--bg-gradient);
              color: var(--text-primary);
              min-height: 100vh;
              padding: 2rem 1rem;
              line-height: 1.6;
          }
          .container {
              max-width: 1100px;
              margin: 0 auto;
          }
          header {
              text-align: center;
              margin-bottom: 2rem;
          }
          h1 {
              font-size: 2.5rem;
              font-weight: 800;
              background: linear-gradient(to right, #38bdf8, #818cf8);
              -webkit-background-clip: text;
              -webkit-text-fill-color: transparent;
              margin-bottom: 0.5rem;
          }
          .time-badge {
              display: inline-block;
              background: rgba(255, 255, 255, 0.05);
              padding: 0.4rem 1rem;
              border-radius: 50px;
              font-size: 0.85rem;
              color: var(--text-secondary);
              border: 1px solid rgba(255, 255, 255, 0.05);
          }
          .grid-2 {
              display: grid;
              grid-template-columns: 1fr;
              gap: 1.5rem;
              margin-bottom: 1.5rem;
          }
          @media (min-width: 768px) {
              .grid-2 {
                  grid-template-columns: 1.2fr 0.8fr;
              }
          }
          .card {
              background: var(--card-bg);
              border: var(--card-border);
              backdrop-filter: blur(12px);
              -webkit-backdrop-filter: blur(12px);
              border-radius: 16px;
              padding: 1.5rem;
              box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2);
              transition: all 0.3s ease;
          }
          .card:hover {
              transform: translateY(-4px);
              border-color: rgba(255, 255, 255, 0.15);
              box-shadow: 0 12px 40px 0 rgba(0, 0, 0, 0.3);
          }
          .market-hero {
              display: flex;
              flex-direction: column;
              justify-content: space-between;
          }
          .market-title {
              font-size: 1.2rem;
              color: var(--text-secondary);
              font-weight: 600;
          }
          .market-value {
              font-size: 3.5rem;
              font-weight: 800;
              margin: 0.5rem 0;
          }
          .badge {
              display: inline-block;
              padding: 0.3rem 0.8rem;
              border-radius: 8px;
              font-weight: 700;
              color: #ffffff;
              font-size: 1.1rem;
          }
          .badge-up {
              background: var(--up-color);
              box-shadow: 0 4px 15px rgba(255, 65, 108, 0.3);
          }
          .badge-down {
              background: var(--down-color);
              box-shadow: 0 4px 15px rgba(0, 176, 155, 0.3);
          }
          .market-details {
              display: grid;
              grid-template-columns: repeat(2, 1fr);
              gap: 1rem;
              margin-top: 1.5rem;
              border-top: 1px solid rgba(255, 255, 255, 0.05);
              padding-top: 1rem;
          }
          .detail-item {
              display: flex;
              flex-direction: column;
          }
          .detail-label {
              font-size: 0.8rem;
              color: var(--text-secondary);
          }
          .detail-val {
              font-size: 1.1rem;
              font-weight: 600;
          }
          .chart-container img {
              width: 100%;
              height: auto;
              border-radius: 8px;
              display: block;
          }
          .stocks-grid {
              display: grid;
              grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
              gap: 1.5rem;
              margin-bottom: 1.5rem;
          }
          .stock-card {
              display: flex;
              justify-content: space-between;
              align-items: center;
          }
          .stock-info h3 {
              font-size: 1.3rem;
              font-weight: 700;
          }
          .stock-info span {
              font-size: 0.85rem;
              color: var(--text-secondary);
          }
          .stock-price-block {
              text-align: right;
          }
          .stock-price {
              font-size: 1.4rem;
              font-weight: 700;
          }
          .stock-pct {
              font-size: 0.9rem;
              font-weight: 600;
          }
          .text-up {
              color: #ff4b2b;
          }
          .text-down {
              color: #00b09b;
          }
          .news-section h2 {
              font-size: 1.4rem;
              margin-bottom: 1rem;
              border-left: 4px solid #38bdf8;
              padding-left: 0.5rem;
          }
          .news-list {
              display: flex;
              flex-direction: column;
              gap: 1rem;
          }
          .news-item {
              display: block;
              text-decoration: none;
              color: inherit;
              padding: 1rem;
              border-radius: 8px;
              background: rgba(255, 255, 255, 0.02);
              border: 1px solid rgba(255, 255, 255, 0.03);
              transition: all 0.2s ease;
          }
          .news-item:hover {
              background: rgba(255, 255, 255, 0.05);
              border-color: rgba(255, 255, 255, 0.1);
              transform: translateX(4px);
          }
          .news-title {
              font-weight: 600;
              font-size: 1.05rem;
              margin-bottom: 0.25rem;
              color: #e2e8f0;
          }
          .news-meta {
              font-size: 0.8rem;
              color: var(--text-secondary);
              display: flex;
              gap: 1rem;
          }
          footer {
              text-align: center;
              margin-top: 3rem;
              font-size: 0.8rem;
              color: var(--text-secondary);
              border-top: 1px solid rgba(255, 255, 255, 0.05);
              padding-top: 1.5rem;
          }
      </style>
  </head>
  <body>
      <div class="container">
          <header>
              <h1>台灣股市每日大盤分析報告</h1>
              <div class="time-badge">報告生成時間：{{ timestamp }}</div>
          </header>

          <div class="grid-2">
              <!-- 大盤焦點卡片 -->
              <div class="card market-hero">
                  <div>
                      <div class="market-title">加權指數 (^TWII)</div>
                      <div class="market-value">{{ market.close }}</div>
                      <div class="badge {% if market.change >= 0 %}badge-up{% else %}badge-down{% endif %}">
                          {% if market.change >= 0 %}+{% endif %}{{ market.change }} ({% if market.change >= 0 %}+{% endif %}{{ market.change_pct }}%)
                      </div>
                  </div>
                  <div class="market-details">
                      <div class="detail-item">
                          <span class="detail-label">今日開盤</span>
                          <span class="detail-val">{{ market.open }}</span>
                      </div>
                      <div class="detail-item">
                          <span class="detail-label">今日成交量 (億)</span>
                          <span class="detail-val">{{ (market.volume / 100000000) | round(2) }}</span>
                      </div>
                      <div class="detail-item">
                          <span class="detail-label">今日最高</span>
                          <span class="detail-val">{{ market.high }}</span>
                      </div>
                      <div class="detail-item">
                          <span class="detail-label">今日最低</span>
                          <span class="detail-val">{{ market.low }}</span>
                      </div>
                  </div>
              </div>

              <!-- AI 大盤簡評 -->
              <div class="card" style="display: flex; flex-direction: column; justify-content: center;">
                  <h3 style="font-size: 1.2rem; margin-bottom: 0.8rem; color: #38bdf8;">今日盤勢 AI 簡評</h3>
                  <p style="color: #cbd5e1; font-size: 0.95rem;">
                      今日加權指數收在 {{ market.close }} 點，相較於昨日{% if market.change >= 0 %}上漲 {{ market.change }} 點{% else %}下跌 {{ abs(market.change) }} 點{% endif %}。
                      {% if market.change_pct >= 1.0 %}
                      今日市場多頭氣勢強勁，大盤大幅走高。
                      {% elif market.change_pct > 0 %}
                      今日呈現小幅震盪收紅，多方仍佔上風。
                      {% elif market.change_pct <= -1.0 %}
                      今日空方賣壓沉重，大盤跌幅較深，需注意下方支撐。
                      {% else %}
                      今日呈現小幅拉回盤整，多空雙方呈膠著態勢。
                      {% endif %}
                      主要權值股中，台積電收在 {{ stocks[0].close }} 元（{{ stocks[0].change_pct }}%）、鴻海收在 {{ stocks[1].close }} 元（{{ stocks[1].change_pct }}%）、聯發科收在 {{ stocks[2].close }} 元（{{ stocks[2].change_pct }}%），三大權值股今日表現引領盤勢動向。
                  </p>
              </div>
          </div>

          <!-- 30 日走勢圖卡片 -->
          <div class="card chart-container" style="margin-bottom: 1.5rem;">
              <img src="{{ chart_base64 }}" alt="大盤走勢圖">
          </div>

          <!-- 權值股表現 -->
          <div class="stocks-grid">
              {% for stock in stocks %}
              <div class="card stock-card">
                  <div class="stock-info">
                      <h3>{{ stock.name }}</h3>
                      <span>{{ stock.ticker }}</span>
                  </div>
                  <div class="stock-price-block">
                      <div class="stock-price">{{ stock.close }}</div>
                      <div class="stock-pct {% if stock.change >= 0 %}text-up{% else %}text-down{% endif %}">
                          {% if stock.change >= 0 %}+{% endif %}{{ stock.change_pct }}%
                      </div>
                  </div>
              </div>
              {% endfor %}
          </div>

          <!-- 今日焦點新聞 -->
          <div class="card news-section">
              <h2>今日焦點財經新聞</h2>
              <div class="news-list">
                  {% for item in news %}
                  <a href="{{ item.link }}" target="_blank" class="news-item">
                      <div class="news-title">{{ item.title }}</div>
                      <div class="news-meta">
                          <span>來源：{{ item.source }}</span>
                          <span>時間：{{ item.pub_date }}</span>
                      </div>
                  </a>
                  {% endfor %}
              </div>
          </div>

          <footer>
              <p>資料來源：Yahoo Finance 及公開新聞 RSS。報告僅供參考，不構成任何投資建議。</p>
              <p>© 2026 台股每日大盤分析報告生成器</p>
          </footer>
      </div>
  </body>
  </html>
  ```

- [ ] **Step 2: 撰寫報告生成模組的測試檔**
  在 `tests/test_report_generator.py` 中。
  內容：
  ```python
  import pytest
  import os
  from src.report_generator import render_html_report

  def test_render_html_report():
      market_data = {
          "close": 21000.0, "open": 20900.0, "high": 21100.0, "low": 20850.0,
          "volume": 35000000000, "change": 150.0, "change_pct": 0.72
      }
      stocks_data = [
          {"name": "台積電", "ticker": "2330.TW", "close": 900.0, "change_pct": 1.1},
          {"name": "鴻海", "ticker": "2317.TW", "close": 200.0, "change_pct": -0.5},
          {"name": "聯發科", "ticker": "2454.TW", "close": 1200.0, "change_pct": 0.0}
      ]
      news_data = [
          {"title": "台股焦點新聞測試", "link": "http://example.com", "pub_date": "2026-07-14", "source": "測試"}
      ]
      chart_base64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="

      # 測試渲染
      html_content = render_html_report(market_data, stocks_data, news_data, chart_base64)
      
      assert "台灣股市每日大盤分析報告" in html_content
      assert "21000.0" in html_content
      assert "台積電" in html_content
      assert "台股焦點新聞測試" in html_content
  ```

- [ ] **Step 3: 執行測試並確認其失敗**
  執行命令：`pytest tests/test_report_generator.py`
  預期輸出：`ModuleNotFoundError: No module named 'src.report_generator'`

- [ ] **Step 4: 實作 `src/report_generator.py`**
  內容：
  ```python
  import os
  from jinja2 import Environment, FileSystemLoader
  from datetime import datetime

  def render_html_report(market: dict, stocks: list, news: list, chart_base64: str) -> str:
      # 設定 templates 目錄
      template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
      env = Environment(loader=FileSystemLoader(template_dir))
      template = env.get_template('report_template.html')
      
      now = datetime.now()
      timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")
      date_str = now.strftime("%Y-%m-%d")
      
      rendered = template.render(
          date=date_str,
          timestamp=timestamp_str,
          market=market,
          stocks=stocks,
          news=news,
          chart_base64=chart_base64,
          abs=abs # 將 abs 函數傳入範本以方便使用
      )
      return rendered
  ```

- [ ] **Step 5: 執行測試並確認其通過**
  執行命令：`pytest tests/test_report_generator.py -v`
  預期輸出：`test_report_generator.py PASSED`

---

### Task 5: Google Drive API 雲端硬碟上傳模組 (drive_uploader)

**Files:**
*   Create: `src/drive_uploader.py`

- [ ] **Step 1: 實作 `src/drive_uploader.py`**
  因為 Google 驗證涉及瀏覽器跳轉與本地憑證檔案，我們採用實用導向的實作。
  內容：
  ```python
  import os
  from google.oauth2.credentials import Credentials
  from google_auth_oauthlib.flow import InstalledAppFlow
  from google.auth.transport.requests import Request
  from googleapiclient.discovery import build
  from googleapiclient.http import MediaFileUpload

  # 宣告 API 權限範圍 (唯讀 + 寫入/建立/修改檔案)
  SCOPES = ['https://www.googleapis.com/auth/drive.file']

  def authenticate_drive() -> Credentials:
      creds = None
      # 檢查是否已存在授權 Token 檔案
      if os.path.exists('token.json'):
          creds = Credentials.from_authorized_user_file('token.json', SCOPES)
      
      # 若憑證無效或不存在，進行 OAuth 授權流程
      if not creds or not creds.valid:
          if creds and creds.expired and creds.refresh_token:
              try:
                  creds.refresh(Request())
              except Exception:
                  creds = None
          
          if not creds:
              if not os.path.exists('client_secrets.json'):
                  raise FileNotFoundError(
                      "未找到 client_secrets.json 檔案！\n"
                      "請依照 README.md 中的說明下載您的 Google OAuth 憑證並放入專案根目錄中。"
                  )
              flow = InstalledAppFlow.from_client_secrets_file('client_secrets.json', SCOPES)
              creds = flow.run_local_server(port=0)
              
          # 儲存最新的授權 Token 供下次使用
          with open('token.json', 'w') as token:
              token.write(creds.to_json())
              
      return creds

  def upload_or_update_file(filename: str, filepath: str, parent_folder_id: str = "") -> str:
      creds = authenticate_drive()
      service = build('drive', 'v3', credentials=creds)
      
      # 1. 搜尋是否有同名的舊報告檔案
      query = f"name = '{filename}' and trashed = false"
      if parent_folder_id:
          query += f" and '{parent_folder_id}' in parents"
      else:
          query += " and 'root' in parents"
          
      response = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
      files = response.get('files', [])
      
      media = MediaFileUpload(filepath, mimetype='text/html')
      
      if files:
          # 若檔案已存在，使用 update (覆蓋內容)
          file_id = files[0]['id']
          print(f"偵測到雲端中已存在同名檔案 [ID: {file_id}]，正在覆蓋更新...")
          updated_file = service.files().update(
              fileId=file_id,
              media_body=media,
              fields='id'
          ).execute()
          return updated_file.get('id')
      else:
          # 若檔案不存在，建立新檔案
          print(f"雲端中無重複檔案，正在上傳新檔案...")
          file_metadata = {'name': filename}
          if parent_folder_id:
              file_metadata['parents'] = [parent_folder_id]
              
          new_file = service.files().create(
              body=file_metadata,
              media_body=media,
              fields='id'
          ).execute()
          return new_file.get('id')
  ```

---

### Task 6: 主執行腳本與入口串接 (generate_report.py)

**Files:**
*   Create: `generate_report.py`

- [ ] **Step 1: 實作主程序 `generate_report.py`**
  內容：
  ```python
  import os
  import json
  from datetime import datetime
  from src.data_fetcher import fetch_stock_data, fetch_market_news
  from src.chart_generator import generate_market_chart
  from src.report_generator import render_html_report
  from src.drive_uploader import upload_or_update_file

  def main():
      print("===== 開始執行台灣股市每日大盤分析報告生成程序 =====")
      
      # 1. 讀取設定檔
      config_path = "config.json"
      parent_folder_id = ""
      tickers = ["2330.TW", "2317.TW", "2454.TW"]
      market_ticker = "^TWII"
      
      if os.path.exists(config_path):
          try:
              with open(config_path, "r", encoding="utf-8") as f:
                  config = json.load(f)
                  parent_folder_id = config.get("parent_folder_id", "")
                  tickers = config.get("tickers", tickers)
                  market_ticker = config.get("market_ticker", market_ticker)
          except Exception as e:
              print(f"讀取 config.json 失敗，將使用預設設定。錯誤: {e}")
              
      # 2. 獲取數據
      print("正在獲取股市價量與歷史數據...")
      stock_data = fetch_stock_data(market_ticker, tickers)
      
      print("正在獲取今日財經焦點新聞...")
      news_data = fetch_market_news()
      
      # 3. 繪製圖表
      print("正在繪製大盤走勢與均線圖表...")
      chart_base64 = generate_market_chart(stock_data["market"]["history"])
      
      # 4. 產生報告 HTML
      print("正在渲染精美 HTML 報告...")
      html_content = render_html_report(
          stock_data["market"],
          stock_data["stocks"],
          news_data,
          chart_base64
      )
      
      # 儲存到本地
      date_str = datetime.now().strftime("%Y-%m-%d")
      local_filename = f"report_{date_str}.html"
      with open(local_filename, "w", encoding="utf-8") as f:
          f.write(html_content)
      print(f"報告已成功產生於本地：{os.path.abspath(local_filename)}")
      
      # 5. 上傳雲端硬碟
      print("準備將報告上傳至 Google 雲端硬碟...")
      drive_filename = f"台股大盤分析報告_{date_str}.html"
      try:
          file_id = upload_or_update_file(drive_filename, local_filename, parent_folder_id)
          print(f"上傳成功！雲端檔案 ID: {file_id}")
          print("===== 生成與上傳程序已全部完成 =====")
      except FileNotFoundError as fnf:
          print(f"\n[提示] {fnf}")
          print("報告已儲存於本地，您可以手動上傳。若要啟用自動上傳，請設定 client_secrets.json。")
      except Exception as e:
          print(f"\n[錯誤] 上傳雲端硬碟失敗: {e}")
          print("報告已儲存於本地，您可以手動上傳。")

  if __name__ == "__main__":
      main()
  ```

---

### Task 7: 撰寫專案說明文件 (README.md)

**Files:**
*   Create: `README.md`

- [ ] **Step 1: 建立繁體中文 README.md 指南**
  詳細說明如何啟用 Google Drive API 下載憑證，以及如何執行與排程化。
  內容：
  ```markdown
  # 台股每日大盤分析報告自動生成與雲端上傳器

  此專案是一個 Python 自動化工具，專門在每日收盤後自動抓取台股大盤與主要權值股的價量數據、焦點新聞，產生美輪美奐的深色科技風 HTML 報告，並直接上傳（或更新覆蓋）至 Google 雲端硬碟。

  ## 🛠️ 安裝說明

  1.  **安裝 Python 依賴套件**：
      ```bash
      pip install -r requirements.txt
      ```

  2.  **設定 Google 雲端硬碟上傳憑證 (第一次設定需時 3 分鐘)**：
      *   前往 [Google Cloud Console](https://console.cloud.google.com/)。
      *   建立一個新專案（例如 `stock-report-uploader`）。
      *   在左側選單選擇 **API 和服務** > **庫**，搜尋並啟用 **Google Drive API**。
      *   選擇 **OAuth 同意畫面**，將 User Type 設為 **外部 (External)**，填寫必填欄位，並將您自己的 Google 帳號新增為 **測試使用者 (Test Users)**。
      *   選擇 **憑證 (Credentials)** > **建立憑證** > **OAuth 用戶端 ID**。
      *   應用程式類型選擇 **電腦版應用程式 (Desktop App)**，並點選建立。
      *   在憑證列表中，點選下載按鈕下載 JSON 檔案，重新命名為 `client_secrets.json`，並放入此專案的根目錄下。

  ## 🚀 執行與使用

  *   **手動執行**：
      ```bash
      python generate_report.py
      ```
      *首次執行時會自動開啟您的瀏覽器要求進行 Google 授權，點選同意後會在根目錄生成 `token.json`，之後執行便不再需要重新授權。*

  *   **自訂設定**：
      您可以編輯 `config.json`：
      *   `parent_folder_id`：輸入您 Google 雲端硬碟中某個特定資料夾的 ID（從網址列的最後一段取得），報告將會上傳至該資料夾中。若留空則上傳至根目錄。
      *   `tickers`：可自由增減追蹤的台股個股代碼（例如 `"2317.TW"`, `"2454.TW"`, `"2330.TW"`）。

  *   **每日自動定時排程執行 (Windows 範例)**：
      *   開啟「工作排程器 (Task Scheduler)」。
      *   新增工作，設定触发器為每日的下午 14:30。
      *   操作設定為「啟動程式」，設定為執行您的 Python 執行路徑（如 `python.exe`），並於引數填入 `generate_report.py` 的絕對路徑。
  ```
