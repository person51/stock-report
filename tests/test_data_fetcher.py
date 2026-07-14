import pytest
import pandas as pd
from src.data_fetcher import fetch_stock_data, fetch_market_news

def test_fetch_stock_data():
    """
    測試 fetch_stock_data 是否能正確獲取大盤及個股的今日開盤、收盤、最高、最低、成交量、漲跌額、漲跌幅，
    以及 30 天的大盤歷史數據。
    """
    market_ticker = "^TWII"
    tickers = ["2330.TW", "2317.TW", "2454.TW"]
    
    data = fetch_stock_data(market_ticker, tickers)
    
    # 驗證回傳格式包含 market, stocks, 與 market_history
    assert "market" in data
    assert "stocks" in data
    assert "market_history" in data
    
    # 驗證大盤資料欄位
    market_data = data["market"]
    assert market_data["ticker"] == "^TWII"
    required_fields = ["open", "close", "high", "low", "volume", "change", "percent_change"]
    for field in required_fields:
        assert field in market_data
        assert market_data[field] is not None
        
    # 驗證個股資料欄位
    stocks_data = data["stocks"]
    for ticker in tickers:
        assert ticker in stocks_data
        stock_data = stocks_data[ticker]
        for field in required_fields:
            assert field in stock_data
            assert stock_data[field] is not None
            
    # 驗證 30 天的大盤歷史數據
    history = data["market_history"]
    assert isinstance(history, pd.DataFrame)
    assert not history.empty
    # yfinance 歷史數據應包含 Open, High, Low, Close, Volume 等欄位
    for col in ["Open", "High", "Low", "Close", "Volume"]:
        assert col in history.columns

def test_fetch_market_news():
    """
    測試 fetch_market_news 是否能成功自 Yahoo 股市 RSS 抓取今日至少 5 則焦點新聞，
    其格式為包含標題、網址、發布時間與來源的字典清單。
    """
    news = fetch_market_news()
    
    assert isinstance(news, list)
    # 至少抓取 5 則焦點新聞
    assert len(news) >= 5
    
    for item in news[:5]:
        assert "title" in item
        assert "url" in item
        assert "published_at" in item
        assert "source" in item
        
        # 驗證內容不為空
        assert isinstance(item["title"], str) and len(item["title"]) > 0
        assert isinstance(item["url"], str) and item["url"].startswith("http")
        assert isinstance(item["published_at"], str) and len(item["published_at"]) > 0
        assert isinstance(item["source"], str) and len(item["source"]) > 0
