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

    # 2. 獲取當前時間並格式化
    generated_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 3. 取得 templates 資料夾的絕對路徑
    current_dir = os.path.dirname(os.path.abspath(__file__))
    templates_dir = os.path.join(os.path.dirname(current_dir), "templates")

    # 4. 載入 Jinja2 模板並進行渲染
    env = Environment(loader=FileSystemLoader(templates_dir))
    template = env.get_template("report_template.html")

    html_content = template.render(
        market=market,
        stocks=stocks,
        news=news,
        chart_base64=chart_base64,
        generated_time=generated_time
    )

    return html_content
