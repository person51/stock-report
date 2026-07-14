import pytest
import pandas as pd
import numpy as np
from src.chart_generator import calculate_moving_averages, generate_market_chart

def test_calculate_moving_averages():
    """
    測試計算移動平均線 (5MA, 10MA, 20MA) 是否正確。
    """
    # 建立 30 天的模擬歷史數據
    dates = pd.date_range(start="2026-06-01", periods=30)
    # 收盤價設為從 100 開始遞增 1 的數列：100, 101, 102, ... 129
    close_prices = np.arange(100.0, 130.0)
    df = pd.DataFrame({
        "Open": close_prices,
        "High": close_prices,
        "Low": close_prices,
        "Close": close_prices,
        "Volume": np.random.randint(1000, 5000, size=30)
    }, index=dates)
    
    df_with_ma = calculate_moving_averages(df)
    
    # 檢查是否新增了 5MA, 10MA, 20MA 欄位
    assert "5MA" in df_with_ma.columns
    assert "10MA" in df_with_ma.columns
    assert "20MA" in df_with_ma.columns
    
    # 5MA：前 4 個為 NaN，第 5 個 (index 4) 開始有值
    assert pd.isna(df_with_ma["5MA"].iloc[3])
    # 第 5 個值應該是 (100+101+102+103+104)/5 = 102.0
    assert df_with_ma["5MA"].iloc[4] == 102.0
    
    # 10MA：前 9 個為 NaN，第 10 個 (index 9) 開始有值
    assert pd.isna(df_with_ma["10MA"].iloc[8])
    # 第 10 個值應該是 (100+...+109)/10 = 104.5
    assert df_with_ma["10MA"].iloc[9] == 104.5
    
    # 20MA：前 19 個為 NaN，第 20 個 (index 19) 開始有值
    assert pd.isna(df_with_ma["20MA"].iloc[18])
    # 第 20 個值應該是 (100+...+119)/20 = 109.5
    assert df_with_ma["20MA"].iloc[19] == 109.5

def test_generate_market_chart():
    """
    測試走勢圖生成函式，驗證是否能回傳正確的 Base64 圖片字串。
    """
    # 建立 30 天的模擬歷史數據
    dates = pd.date_range(start="2026-06-01", periods=30)
    close_prices = [100.0 + i + (5.0 if i % 2 == 0 else -5.0) for i in range(30)]
    df = pd.DataFrame({
        "Open": [p - 1.0 for p in close_prices],
        "High": [p + 2.0 for p in close_prices],
        "Low": [p - 2.0 for p in close_prices],
        "Close": close_prices,
        "Volume": [1000 + i * 100 for i in range(30)]
    }, index=dates)
    
    chart_base64 = generate_market_chart(df)
    
    assert isinstance(chart_base64, str)
    assert chart_base64.startswith("data:image/png;base64,")
    # Base64 字串長度應有一定大小
    assert len(chart_base64) > 100
