import unittest
from unittest.mock import patch, MagicMock, mock_open, call
import os
import sys
import pandas as pd
from datetime import datetime
import importlib

# 確保 src 目錄在 python path 中
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

class TestIntegration(unittest.TestCase):
    @patch("os.path.exists")
    @patch("generate_report.open", new_callable=mock_open, read_data='{"market_ticker": "^TWII", "tickers": ["2330.TW"], "parent_folder_id": "test_folder_id"}')
    @patch("src.data_fetcher.fetch_stock_data")
    @patch("src.data_fetcher.fetch_market_news")
    @patch("src.chart_generator.generate_market_chart")
    @patch("src.report_generator.render_html_report")
    @patch("src.drive_uploader.upload_or_update_file")
    def test_integration_flow_with_config(self, mock_upload, mock_render, mock_chart, mock_news, mock_fetch, mock_file, mock_exists):
        """測試當 config.json 存在時，按順序執行完整流程"""
        # 設定 os.path.exists
        mock_exists.side_effect = lambda path: True if "config.json" in str(path) else False

        # 設定 mock 返回值
        mock_fetch.return_value = {
            "market": {"ticker": "^TWII", "close": 20000.0},
            "stocks": {"2330.TW": {"close": 800.0}},
            "market_history": pd.DataFrame()
        }
        mock_news.return_value = [{"title": "News 1", "url": "http://example.com"}]
        mock_chart.return_value = "data:image/png;base64,mock_base64"
        mock_render.return_value = "<html>Mock Report</html>"
        mock_upload.return_value = "mock_file_id"

        # 為了驗證呼叫順序，使用 attach_mock 將 mock 物件綁定到 manager
        manager = MagicMock()
        manager.attach_mock(mock_exists, 'exists')
        manager.attach_mock(mock_file, 'open')
        manager.attach_mock(mock_fetch, 'fetch_stock_data')
        manager.attach_mock(mock_news, 'fetch_market_news')
        manager.attach_mock(mock_chart, 'generate_market_chart')
        manager.attach_mock(mock_render, 'render_html_report')
        manager.attach_mock(mock_upload, 'upload_or_update_file')

        # 執行主程式的 main()
        import generate_report
        importlib.reload(generate_report)
        generate_report.main()

        # 驗證步驟的先後順序
        calls = manager.mock_calls
        
        # 從 calls 中挑出我們關心的呼叫來比對順序
        relevant_calls = []
        for c in calls:
            name = c[0]
            if name in ["fetch_stock_data", "fetch_market_news", "generate_market_chart", "render_html_report", "upload_or_update_file"]:
                relevant_calls.append(name)
            elif name == "open":
                args = c[1]
                if args and any(x in str(args[0]) for x in ["config.json", "report_"]):
                    relevant_calls.append(f"open_{args[0]}")
        
        expected_flow = [
            "fetch_stock_data",
            "fetch_market_news",
            "generate_market_chart",
            "render_html_report",
            "upload_or_update_file"
        ]
        
        # 檢查主要函數是否有被呼叫，且順序正確
        func_indices = []
        for f in expected_flow:
            self.assertIn(f, relevant_calls, f"主要函數 {f} 未被呼叫")
            func_indices.append(relevant_calls.index(f))
            
        self.assertEqual(func_indices, sorted(func_indices), "主要函數呼叫順序不正確")
        
        # 檢查 config.json 讀取是否在 fetch_stock_data 之前
        config_open_index = -1
        for i, call_name in enumerate(relevant_calls):
            if "config.json" in call_name:
                config_open_index = i
                break
        
        fetch_index = relevant_calls.index("fetch_stock_data")
        self.assertTrue(config_open_index != -1, "沒有讀取 config.json")
        self.assertTrue(config_open_index < fetch_index, "讀取 config.json 必須在 fetch_stock_data 之前")
        
        # 檢查寫入 report_... 是否在 render_html_report 之後，且在 upload_or_update_file 之前
        report_open_index = -1
        for i, call_name in enumerate(relevant_calls):
            if "report_" in call_name:
                report_open_index = i
                break
        
        render_index = relevant_calls.index("render_html_report")
        upload_index = relevant_calls.index("upload_or_update_file")
        self.assertTrue(report_open_index != -1, "沒有寫入本地 HTML 報告")
        self.assertTrue(render_index < report_open_index < upload_index, "寫入本地報告必須在渲染之後且上傳之前")

        # 驗證傳給 fetch_stock_data 的參數是來自於 config.json
        mock_fetch.assert_called_once_with("^TWII", ["2330.TW"])
        
        # 驗證上傳檔名與 parent_folder_id (相容位置參數與關鍵字參數)
        today_str = datetime.now().strftime("%Y-%m-%d")
        expected_upload_filename = f"台股大盤分析報告_{today_str}.html"
        mock_upload.assert_called_once()
        args, kwargs = mock_upload.call_args
        
        filename = kwargs.get("filename") if "filename" in kwargs else (args[0] if len(args) > 0 else None)
        parent_folder_id = kwargs.get("parent_folder_id") if "parent_folder_id" in kwargs else (args[2] if len(args) > 2 else None)
        
        self.assertEqual(filename, expected_upload_filename)
        self.assertEqual(parent_folder_id, "test_folder_id")


    @patch("os.path.exists")
    @patch("generate_report.open", new_callable=mock_open)
    @patch("src.data_fetcher.fetch_stock_data")
    @patch("src.data_fetcher.fetch_market_news")
    @patch("src.chart_generator.generate_market_chart")
    @patch("src.report_generator.render_html_report")
    @patch("src.drive_uploader.upload_or_update_file")
    def test_integration_flow_without_config(self, mock_upload, mock_render, mock_chart, mock_news, mock_fetch, mock_file, mock_exists):
        """測試當 config.json 不存在時，使用預設值執行完整流程"""
        # 設定 os.path.exists 回傳 False
        mock_exists.return_value = False

        # 設定 mock 返回值
        mock_fetch.return_value = {
            "market": {"ticker": "^TWII", "close": 20000.0},
            "stocks": {"2330.TW": {"close": 800.0}},
            "market_history": pd.DataFrame()
        }
        mock_news.return_value = [{"title": "News 1", "url": "http://example.com"}]
        mock_chart.return_value = "data:image/png;base64,mock_base64"
        mock_render.return_value = "<html>Mock Report</html>"
        mock_upload.return_value = "mock_file_id"

        # 執行主程式的 main()
        import generate_report
        importlib.reload(generate_report)
        generate_report.main()

        # 驗證 fetch_stock_data 使用了預設值
        mock_fetch.assert_called_once_with("^TWII", ["2330.TW", "2317.TW", "2454.TW"])
        
        # 驗證上傳檔名與 parent_folder_id 為預設值
        today_str = datetime.now().strftime("%Y-%m-%d")
        expected_upload_filename = f"台股大盤分析報告_{today_str}.html"
        mock_upload.assert_called_once()
        args, kwargs = mock_upload.call_args
        
        filename = kwargs.get("filename") if "filename" in kwargs else (args[0] if len(args) > 0 else None)
        parent_folder_id = kwargs.get("parent_folder_id") if "parent_folder_id" in kwargs else (args[2] if len(args) > 2 else None)
        
        self.assertEqual(filename, expected_upload_filename)
        self.assertTrue(parent_folder_id == "" or parent_folder_id is None)

if __name__ == "__main__":
    unittest.main()
