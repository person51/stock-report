import os
import json
from datetime import datetime
import src.data_fetcher as data_fetcher
import src.chart_generator as chart_generator
import src.report_generator as report_generator
import src.drive_uploader as drive_uploader

DEFAULT_CONFIG = {
    "market_ticker": "^TWII",
    "tickers": ["2330.TW", "2317.TW", "2454.TW"],
    "parent_folder_id": ""
}

def load_config(config_path="config.json") -> dict:
    """載入設定檔，若不存在或發生錯誤則回傳預設值。"""
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                return {
                    "market_ticker": config.get("market_ticker", DEFAULT_CONFIG["market_ticker"]),
                    "tickers": config.get("tickers", DEFAULT_CONFIG["tickers"]),
                    "parent_folder_id": config.get("parent_folder_id", DEFAULT_CONFIG["parent_folder_id"])
                }
        except Exception as e:
            print(f"讀取設定檔失敗，將使用預設值。錯誤資訊：{e}")
            return DEFAULT_CONFIG
    return DEFAULT_CONFIG

def main():
    """主執行流程，負責串接各個子模組生成大盤分析報告並上傳雲端硬碟。"""
    print("=== 開始執行台股大盤分析報告生成流程 ===")
    
    # 1. 讀取設定檔
    config = load_config()
    market_ticker = config["market_ticker"]
    tickers = config["tickers"]
    parent_folder_id = config["parent_folder_id"]
    print(f"載入設定：大盤 {market_ticker}，個股 {tickers}，雲端目錄 ID '{parent_folder_id}'")

    # 2. 獲取大盤與個股數據
    print("正在獲取市場歷史與今日數據...")
    data = data_fetcher.fetch_stock_data(market_ticker, tickers)
    
    # 3. 獲取焦點新聞
    print("正在抓取焦點新聞...")
    news = data_fetcher.fetch_market_news()

    # 4. 繪製圖表
    print("正在繪製大盤走勢與均線圖...")
    chart_base64 = chart_generator.generate_market_chart(data["market_history"])

    # 5. 套版生成 HTML
    print("正在渲染 HTML 報告...")
    html_content = report_generator.render_html_report(
        market=data["market"],
        stocks=data["stocks"],
        news=news,
        chart_base64=chart_base64
    )

    # 6. 將生成的 HTML 檔案寫入本地
    today_str = datetime.now().strftime("%Y-%m-%d")
    report_filename = f"report_{today_str}.html"
    print(f"將報告寫入本地檔案：{report_filename}")
    with open(report_filename, "w", encoding="utf-8") as f:
        f.write(html_content)

    # 7. 上傳（或覆蓋）雲端硬碟
    drive_filename = f"台股大盤分析報告_{today_str}.html"
    print(f"上傳檔案至 Google Drive，檔名：{drive_filename}")
    try:
        file_id = drive_uploader.upload_or_update_file(
            filename=drive_filename,
            filepath=report_filename,
            parent_folder_id=parent_folder_id
        )
        print(f"上傳成功！雲端檔案 ID: {file_id}")
    except Exception as e:
        print(f"上傳至雲端硬碟失敗，錯誤資訊：{e}")

if __name__ == "__main__":
    main()
