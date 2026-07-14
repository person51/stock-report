import base64
import io
import matplotlib
# 使用非互動式後端，避免在無 GUI 環境下報錯
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np

def calculate_moving_averages(market_history: pd.DataFrame) -> pd.DataFrame:
    """
    計算大盤歷史數據的 5MA、10MA、20MA。
    
    Args:
        market_history: 包含 'Close' 欄位的大盤歷史數據 DataFrame。
        
    Returns:
        pd.DataFrame: 新增 5MA、10MA、20MA 欄位後的 DataFrame。
    """
    df = market_history.copy()
    df['5MA'] = df['Close'].rolling(window=5).mean()
    df['10MA'] = df['Close'].rolling(window=10).mean()
    df['20MA'] = df['Close'].rolling(window=20).mean()
    return df

def generate_market_chart(market_history: pd.DataFrame) -> str:
    """
    生成大盤走勢與均線圖，並回傳 Base64 字串。
    
    Args:
        market_history: 大盤歷史數據 DataFrame。
        
    Returns:
        str: 格式為 'data:image/png;base64,...' 的 Base64 字串。
    """
    # 1. 計算均線
    df = calculate_moving_averages(market_history)
    
    # 2. 設定中文字型與外觀
    plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'Heiti TC', 'DejaVu Sans', 'sans-serif']
    plt.rcParams['axes.unicode_minus'] = False
    
    # 3. 建立畫布與子圖 (ax1 為收盤/均線，ax2 為成交量)
    fig, (ax1, ax2) = plt.subplots(
        nrows=2, 
        ncols=1, 
        sharex=True, 
        gridspec_kw={'height_ratios': [3, 1]}, 
        figsize=(10, 6),
        facecolor='#0f172a' # 外圍背景色 (slate-900)
    )
    
    # 設定子圖內部背景色 (slate-800)
    ax1.set_facecolor('#1e293b')
    ax2.set_facecolor('#1e293b')
    
    # 4. 繪製上方子圖 (收盤價與均線)
    # 收盤折線 (藍色)
    ax1.plot(df.index, df['Close'], label='收盤價', color='#60a5fa', linewidth=2)
    # 收盤價下方漸層填充 (避免 Y 軸被填滿到 0，以 0.99 * min_price 為底)
    min_close = df['Close'].min()
    ax1.fill_between(df.index, df['Close'], min_close * 0.99, color='#60a5fa', alpha=0.1)
    
    # 均線
    ax1.plot(df.index, df['5MA'], label='5MA', color='#fbbf24', linewidth=1.2)
    ax1.plot(df.index, df['10MA'], label='10MA', color='#f472b6', linewidth=1.2)
    ax1.plot(df.index, df['20MA'], label='20MA', color='#34d399', linewidth=1.2)
    
    # 設定 ax1 的標題與樣式
    ax1.set_title('大盤走勢與均線圖 (30日)', color='#f8fafc', fontsize=14, fontweight='bold', pad=12)
    ax1.tick_params(axis='y', colors='#94a3b8')
    ax1.grid(True, color='#334155', linestyle='--', alpha=0.5)
    ax1.legend(facecolor='#1e293b', edgecolor='#334155', labelcolor='#e2e8f0')
    
    # 5. 繪製下方子圖 (成交量)
    # 計算收盤價與前一日的差值，以判定漲跌著色
    close_diff = df['Close'].diff()
    if len(df) > 0:
        # 第一天無前一日，改與當日開盤價比
        first_diff = df['Close'].iloc[0] - df['Open'].iloc[0]
        close_diff = close_diff.fillna(first_diff)
        
    colors = np.where(close_diff >= 0, '#ef4444', '#22c55e')
    
    # 繪製成交量柱狀圖 (為了解決 DateIndex 的寬度問題，設定合理寬度，通常以天為單位的 width=0.6 即可)
    ax2.bar(df.index, df['Volume'], color=colors, width=0.6, label='成交量')
    
    # 設定 ax2 的樣式
    ax2.tick_params(axis='y', colors='#94a3b8')
    ax2.grid(True, color='#334155', linestyle='--', alpha=0.5)
    ax2.set_ylabel('成交量', color='#94a3b8')
    
    # 6. 格式化 X 軸 (日期)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
    ax2.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax2.tick_params(axis='x', colors='#94a3b8', rotation=15)
    
    # 調整佈局
    plt.tight_layout()
    
    # 7. 轉換成 Base64 字串
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100, facecolor=fig.get_facecolor(), edgecolor='none')
    buf.seek(0)
    image_base64 = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()
    plt.close(fig)
    
    return f"data:image/png;base64,{image_base64}"
