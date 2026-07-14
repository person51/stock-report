import pytest
from src.report_generator import render_html_report

def test_render_html_report():
    # 1. 模擬大盤數據
    market = {
        "index": 22000.5,
        "change": 150.3,
        "change_percent": 0.68,
        "open": 21900.0,
        "high": 22100.0,
        "low": 21850.0,
        "volume": "3,500億"
    }

    # 2. 模擬個股數據
    stocks = {
        "台積電": {
            "price": 950.0,
            "change": 10.0,
            "change_percent": 1.06,
            "open": 940.0,
            "high": 955.0,
            "low": 940.0,
            "volume": "25,000張"
        },
        "鴻海": {
            "price": 200.0,
            "change": -5.0,
            "change_percent": -2.44,
            "open": 205.0,
            "high": 206.0,
            "low": 199.0,
            "volume": "45,000張"
        },
        "聯發科": {
            "price": 1200.0,
            "change": 0.0,
            "change_percent": 0.0,
            "open": 1200.0,
            "high": 1210.0,
            "low": 1195.0,
            "volume": "3,500張"
        }
    }

    # 3. 模擬新聞數據
    news = [
        {"title": "台積電法說會展望樂觀，概念股齊揚", "source": "工商時報", "url": "https://example.com/news1"},
        {"title": "鴻海佈局電動車新進展，新車型發表", "source": "經濟日報", "url": "https://example.com/news2"}
    ]

    # 4. 模擬 Base64 圖表字串
    chart_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

    # 5. 呼叫渲染函數
    html_content = render_html_report(market, stocks, news, chart_base64)

    # 6. 斷言檢查 HTML 內容包含特定中文關鍵字與格式化數據
    assert "台股每日大盤分析報告" in html_content
    assert "22,000.50" in html_content
    assert "150.30" in html_content
    assert "+0.68%" in html_content
    assert "AI 盤勢簡評" in html_content
    assert "大盤當日走勢圖" in html_content
    assert "台積電" in html_content
    assert "950.00" in html_content
    assert "+10.00" in html_content
    assert "鴻海" in html_content
    assert "-5.00" in html_content
    assert "聯發科" in html_content
    assert "焦點財經新聞" in html_content
    assert "台積電法說會展望樂觀" in html_content
    assert "經濟日報" in html_content
    assert chart_base64 in html_content
    assert "報告生成時間" in html_content
