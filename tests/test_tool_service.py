import unittest
import json
from services.weather_tool import get_weather
from services.calendar_tool import get_school_calendar
from services.tool_registry import call_tool, TOOL_REGISTRY
from repositories import sqlite_repository

class TestToolService(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # 确保数据库表就绪
        sqlite_repository.init_db()

    def test_get_weather(self):
        res = get_weather("南京", "明天")
        self.assertIn("南京", res["city"])
        self.assertIn("明天", res["date"])
        self.assertTrue(res["is_demo"])
        self.assertIn("演示天气数据", res["notice"])
        self.assertIn("weather_status", res)
        self.assertIn("temperature_range", res)

    def test_get_school_calendar(self):
        res = get_school_calendar("开学")
        self.assertTrue(res["is_demo"])
        self.assertIn("演示校历数据", res["notice"])
        self.assertGreaterEqual(res["matched_count"], 1)
        self.assertIn("events", res)
        self.assertTrue(any("开学" in e["event"] for e in res["events"]))

    def test_call_tool_success(self):
        session_id = sqlite_repository.create_chat_session("单元测试会话-工具")
        res = call_tool("get_weather", {"city": "苏州", "date": "今天"}, session_id=session_id)
        self.assertTrue(res["success"])
        self.assertIsNone(res["error_message"])
        self.assertIn("city", res["result"])
        
        # 检查日志是否落库
        with sqlite_repository.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tool_logs WHERE session_id = ?", (session_id,))
            rows = cursor.fetchall()
            self.assertEqual(len(rows), 1)
            row = dict(rows[0])
            self.assertEqual(row["tool_name"], "get_weather")
            self.assertEqual(row["success"], 1)

    def test_call_tool_unknown(self):
        res = call_tool("unknown_tool_xyz", {})
        self.assertFalse(res["success"])
        self.assertIn("未注册", res["error_message"])

    def test_call_tool_exception(self):
        # 传入错误的参数以引发异常类型错误或缺少必要参数
        # get_weather 需要 city 和 date，如果缺少必填，会触发 TypeError
        session_id = sqlite_repository.create_chat_session("单元测试会话-工具异常")
        res = call_tool("get_weather", {"city": "南京"}, session_id=session_id)
        self.assertFalse(res["success"])
        self.assertIsNotNone(res["error_message"])
        
        # 检查日志是否落库失败状态
        with sqlite_repository.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tool_logs WHERE session_id = ?", (session_id,))
            rows = cursor.fetchall()
            self.assertEqual(len(rows), 1)
            row = dict(rows[0])
            self.assertEqual(row["success"], 0)
            self.assertIsNotNone(row["error_message"])
