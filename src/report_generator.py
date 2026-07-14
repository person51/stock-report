import os
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

def render_html_report(market: dict, stocks: dict, news: list, chart_base64: str) -> str:
    """
    使用 Jinja2 渲染台股每日大盤分析報告的 HTML 檔案。

    Args:
        market (dict): 大盤數據字典。
        stocks (dict): 個股數據字典。
        news (list): 新聞字典清單。
        chart_base64 (str): 大盤走勢圖的 Base64 字串。

    Returns:
        str: 渲染後的 HTML 內容字串。
    """
    # 1. 確保 chart_base64 具有 data URL 格式，以利 HTML 顯示
    if not chart_base64.startswith("data:"):
        chart_base64 = f"data:image/png;base64,{chart_base64}"
 
    # 2. 轉換與適配大盤數據以符合 HTML 範本規格
    adapted_market = market.copy()
    adapted_market["index"] = market.get("close", market.get("index", 0.0))
    adapted_market["change_percent"] = market.get("percent_change", market.get("change_percent", 0.0))
 
    # 3. 轉換與適配個股數據（將代碼轉為中文，並加上欄位別名）
    name_map = {"2330.TW": "台積電", "2317.TW": "鴻海", "2454.TW": "聯發科"}
    adapted_stocks = {}
    for ticker, info in stocks.items():
        adapted_info = info.copy()
        adapted_info["price"] = info.get("close", info.get("price", 0.0))
        adapted_info["change_percent"] = info.get("percent_change", info.get("change_percent", 0.0))
        
        name = name_map.get(ticker, ticker)
        adapted_stocks[name] = adapted_info
 
    # 4. 獲取當前時間並格式化
    generated_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
 
    # 5. 取得 templates 資料夾的絕對路徑
    current_dir = os.path.dirname(os.path.abspath(__file__))
    templates_dir = os.path.join(os.path.dirname(current_dir), "templates")
 
    # 6. 載入 Jinja2 模板並進行渲染
    env = Environment(loader=FileSystemLoader(templates_dir))
    template = env.get_template("report_template.html")
 
    html_content = template.render(
        market=adapted_market,
        stocks=adapted_stocks,
        news=news,
        chart_base64=chart_base64,
        generated_time=generated_time
    )

    return html_content
