# -*- coding: utf-8 -*-
import unittest
from unittest.mock import patch
from repositories import sqlite_repository


class TestAmapWeatherTool(unittest.TestCase):
    """高德天气工具单元测试（Mock HTTP 响应）"""

    @classmethod
    def setUpClass(cls):
        sqlite_repository.init_db()

    @patch("services.amap_tool._http_get")
    def test_get_weather_amap_today(self, mock_get):
        """测试获取今天天气 - 实时天气"""
        mock_get.return_value = {
            "status": "1", "count": "1", "infocode": "10000",
            "lives": [{"adcode": "320100", "province": "江苏", "city": "南京市",
                        "weather": "晴", "temperature": "28", "winddirection": "东南",
                        "windpower": "3", "humidity": "65", "reporttime": "2026-07-09 15:00:00"}]
        }
        from services.amap_tool import get_weather_amap
        result = get_weather_amap("南京", "今天")
        self.assertFalse(result["is_demo"])
        self.assertEqual(result["city"], "南京市")
        self.assertEqual(result["weather_status"], "晴")
        self.assertIn("temperature", result)

    @patch("services.amap_tool._http_get")
    def test_get_weather_amap_forecast(self, mock_get):
        """测试获取天气预报 - 未来日期"""
        mock_get.return_value = {
            "status": "1", "count": "1", "infocode": "10000",
            "forecasts": [{"adcode": "320100", "province": "江苏", "city": "南京市",
                           "reporttime": "2026-07-09 15:00:00",
                           "casts": [{"date": "2026-07-10", "week": "5",
                                       "dayweather": "多云", "nightweather": "阴",
                                       "daytemp": "31", "nighttemp": "23",
                                       "daywind": "东南", "nightwind": "东南",
                                       "daypower": "3", "nightpower": "2"}]}]
        }
        from services.amap_tool import get_weather_amap
        result = get_weather_amap("南京", "明天")
        self.assertFalse(result["is_demo"])
        self.assertEqual(result["weather_status"], "多云")
        self.assertIn("temperature_range", result)

    @patch("services.amap_tool._http_get")
    def test_get_weather_amap_api_error(self, mock_get):
        """测试 API 返回错误状态"""
        mock_get.return_value = {"status": "0", "infocode": "10001", "info": "INVALID_USER_KEY"}
        from services.amap_tool import get_weather_amap
        result = get_weather_amap("南京", "今天")
        self.assertIn("error", result)
        self.assertFalse(result["is_demo"])

    @patch("services.amap_tool._http_get")
    def test_get_weather_amap_network_error(self, mock_get):
        """测试网络异常时返回错误标识"""
        mock_get.side_effect = Exception("Connection timeout")
        from services.amap_tool import get_weather_amap
        result = get_weather_amap("南京", "今天")
        self.assertIn("error", result)
        self.assertTrue(result["is_demo"])


class TestAmapPOITool(unittest.TestCase):
    """高德 POI 周边搜索工具单元测试（Mock HTTP 响应）"""

    @patch("services.amap_tool._http_get")
    def test_search_nearby_poi_success(self, mock_get):
        """测试正常搜索周边 POI"""
        mock_get.return_value = {
            "status": "1", "infocode": "10000", "count": "2",
            "pois": [
                {"id": "B0FFHQWVJX", "name": "中南财经政法大学医院", "type": "综合医院",
                 "address": "南湖大道182号", "distance": "856", "tel": "027-88386001", "location": "114.3926,30.4753"},
                {"id": "B0FFG3K0JD", "name": "湖北省中医院", "type": "综合医院",
                 "address": "珞喻路856号", "distance": "1230", "tel": "027-88929300", "location": "114.3810,30.5045"}
            ]
        }
        from services.amap_tool import search_nearby_poi
        result = search_nearby_poi("医院", radius=2000, city="武汉")
        self.assertFalse(result["is_demo"])
        self.assertEqual(result["count"], 2)
        self.assertEqual(result["pois"][0]["name"], "中南财经政法大学医院")

    @patch("services.amap_tool._http_get")
    def test_search_nearby_poi_no_result(self, mock_get):
        """测试无结果返回"""
        mock_get.return_value = {"status": "1", "infocode": "10000", "count": "0", "pois": []}
        from services.amap_tool import search_nearby_poi
        result = search_nearby_poi("火星基地", radius=2000)
        self.assertFalse(result["is_demo"])
        self.assertEqual(result["count"], 0)

    @patch("services.amap_tool._http_get")
    def test_search_nearby_poi_api_error(self, mock_get):
        """测试 API 错误"""
        mock_get.return_value = {"status": "0", "infocode": "10001", "info": "INVALID_USER_KEY"}
        from services.amap_tool import search_nearby_poi
        result = search_nearby_poi("医院")
        self.assertIn("error", result)

    @patch("services.amap_tool._http_get")
    def test_search_nearby_poi_network_error(self, mock_get):
        """测试网络异常"""
        mock_get.side_effect = Exception("Timeout")
        from services.amap_tool import search_nearby_poi
        result = search_nearby_poi("银行")
        self.assertIn("error", result)
        self.assertTrue(result["is_demo"])


class TestAmapRouteTool(unittest.TestCase):
    """高德路线规划工具单元测试（Mock HTTP 响应）"""

    @patch("services.amap_tool._http_get")
    def test_plan_route_walking_success(self, mock_get):
        """测试步行路线规划 - 正常场景（校园地点通过 location_mapper 解析）"""
        # location_mapper 已内置"教学楼"和"图书馆"坐标，只需 mock 路线规划 API
        mock_get.return_value = {
            "status": "1",
            "route": {"origin": "114.3926,30.4753", "destination": "114.3935,30.4762",
                      "paths": [{"distance": "820", "duration": "600",
                                 "steps": [
                                     {"instruction": "沿学府路向东步行300米", "road": "学府路", "distance": "300", "duration": "200"},
                                     {"instruction": "右转进入图书馆南路步行520米", "road": "图书馆南路", "distance": "520", "duration": "400"}
                                 ]}]}
        }
        from services.amap_tool import plan_route
        result = plan_route("教学楼", "图书馆", mode="walking")
        self.assertFalse(result["is_demo"])
        self.assertEqual(result["mode"], "walking")
        self.assertEqual(result["distance"], "820")
        self.assertEqual(result["duration"], "600")
        self.assertGreater(len(result["steps"]), 0)

    @patch("services.amap_tool._http_get")
    def test_plan_route_with_coords(self, mock_get):
        """测试直接使用坐标输入"""
        mock_get.return_value = {
            "status": "1",
            "route": {"origin": "118.7749,32.0562", "destination": "118.7810,32.0545",
                      "paths": [{"distance": "500", "duration": "360", "steps": [
                          {"instruction": "向东步行500米", "road": "主路", "distance": "500", "duration": "360"}
                      ]}]}
        }
        from services.amap_tool import plan_route
        result = plan_route("118.7749,32.0562", "118.7810,32.0545", mode="walking")
        self.assertFalse(result["is_demo"])
        self.assertEqual(result["distance"], "500")
        # 不应调用地理编码
        mock_get.assert_called_once()

    @patch("services.amap_tool._http_get")
    def test_plan_route_geocode_failure(self, mock_get):
        """测试地理编码失败场景"""
        mock_get.return_value = {"status": "0", "info": "NO_RESULTS"}
        from services.amap_tool import plan_route
        result = plan_route("火星", "月球")
        self.assertIn("error", result)
        self.assertFalse(result["is_demo"])

    @patch("services.amap_tool._http_get")
    def test_plan_route_network_error(self, mock_get):
        """测试网络异常 - 路线规划 API 超时"""
        mock_get.side_effect = Exception("Timeout")
        from services.amap_tool import plan_route
        result = plan_route("教学楼", "食堂")
        self.assertIn("error", result)
        self.assertIn("Timeout", result["error"])

    def test_plan_route_no_api_key(self):
        """测试无 API Key 时返回提示"""
        from services.amap_tool import plan_route
        with patch("services.amap_tool.settings") as mock_settings:
            mock_settings.AMAP_API_KEY = ""
            result = plan_route("教学楼", "食堂")
            self.assertIn("error", result)
            self.assertTrue(result["is_demo"])


class TestAmapGeocode(unittest.TestCase):
    """地理编码内部函数测试"""

    @patch("services.amap_tool._http_get")
    def test_geocode_success(self, mock_get):
        """测试地理编码成功"""
        mock_get.return_value = {"status": "1", "geocodes": [{"location": "118.7749,32.0562"}]}
        from services.amap_tool import _geocode
        result = _geocode("新街口")
        self.assertEqual(result, "118.7749,32.0562")

    @patch("services.amap_tool._http_get")
    def test_geocode_failure(self, mock_get):
        """测试地理编码失败"""
        mock_get.return_value = {"status": "1", "geocodes": []}
        from services.amap_tool import _geocode
        result = _geocode("不存在的地址")
        self.assertIsNone(result)


class TestAmapHelpers(unittest.TestCase):
    """辅助函数测试"""

    def test_resolve_adcode_known(self):
        from services.amap_tool import _resolve_adcode
        self.assertEqual(_resolve_adcode("南京"), "320100")
        self.assertEqual(_resolve_adcode("北京"), "110000")

    def test_resolve_adcode_unknown(self):
        from services.amap_tool import _resolve_adcode
        self.assertEqual(_resolve_adcode("小城市"), "小城市")

    def test_is_today_query(self):
        from services.amap_tool import _is_today_query
        self.assertTrue(_is_today_query("今天"))
        self.assertTrue(_is_today_query("今日"))
        self.assertFalse(_is_today_query("明天"))
        self.assertFalse(_is_today_query("后天"))
