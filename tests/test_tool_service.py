import unittest
import json
from services.tool_registry import call_tool, TOOL_REGISTRY
from repositories import sqlite_repository


class TestToolService(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sqlite_repository.init_db()

    def test_registered_tools_count(self):
        """验证注册了 4 个工具"""
        self.assertEqual(len(TOOL_REGISTRY), 4)

    def test_amap_weather_registered(self):
        """高德天气工具已注册"""
        self.assertIn("get_weather_amap", TOOL_REGISTRY)

    def test_search_nearby_poi_registered(self):
        """POI 搜索工具已注册"""
        self.assertIn("search_nearby_poi", TOOL_REGISTRY)

    def test_plan_route_registered(self):
        """路线规划工具已注册"""
        self.assertIn("plan_route", TOOL_REGISTRY)

    def test_search_campus_knowledge_registered(self):
        """知识库检索工具已注册"""
        self.assertIn("search_campus_knowledge", TOOL_REGISTRY)

    def test_amap_weather_tool_schema(self):
        """高德天气工具 schema 包含必要字段"""
        schema = TOOL_REGISTRY["get_weather_amap"]["schema"]
        self.assertEqual(schema["function"]["name"], "get_weather_amap")
        self.assertIn("city", schema["function"]["parameters"]["properties"])
        self.assertIn("date", schema["function"]["parameters"]["properties"])

    def test_nearby_poi_tool_schema(self):
        """POI 搜索工具 schema 包含必要字段"""
        schema = TOOL_REGISTRY["search_nearby_poi"]["schema"]
        self.assertEqual(schema["function"]["name"], "search_nearby_poi")
        self.assertIn("keyword", schema["function"]["parameters"]["properties"])

    def test_plan_route_tool_schema(self):
        """路线规划工具 schema 包含必要字段"""
        schema = TOOL_REGISTRY["plan_route"]["schema"]
        self.assertEqual(schema["function"]["name"], "plan_route")
        self.assertIn("origin", schema["function"]["parameters"]["properties"])
        self.assertIn("destination", schema["function"]["parameters"]["properties"])

    def test_call_tool_unknown(self):
        """调用未注册工具返回失败"""
        res = call_tool("unknown_tool_xyz", {})
        self.assertFalse(res["success"])
        self.assertIn("未注册", res["error_message"])

    def test_call_tool_exception(self):
        """传入错误参数引发异常时日志正确记录"""
        session_id = sqlite_repository.create_chat_session("单元测试会话-工具异常")
        # get_weather_amap 缺少必填参数 date 会触发 TypeError
        res = call_tool("get_weather_amap", {"city": "南京"}, session_id=session_id)
        self.assertFalse(res["success"])
        self.assertIsNotNone(res["error_message"])

        with sqlite_repository.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tool_logs WHERE session_id = ?", (session_id,))
            rows = cursor.fetchall()
            self.assertEqual(len(rows), 1)
            row = dict(rows[0])
            self.assertEqual(row["tool_name"], "get_weather_amap")
            self.assertEqual(row["success"], 0)
            self.assertIsNotNone(row["error_message"])

    def test_all_tool_schemas_valid(self):
        """所有工具 schema 符合 OpenAI Function Calling 格式"""
        from services.tool_registry import get_all_tool_schemas
        schemas = get_all_tool_schemas()
        self.assertEqual(len(schemas), 4)
        for schema in schemas:
            self.assertEqual(schema["type"], "function")
            self.assertIn("function", schema)
            self.assertIn("name", schema["function"])
            self.assertIn("description", schema["function"])
            self.assertIn("parameters", schema["function"])
