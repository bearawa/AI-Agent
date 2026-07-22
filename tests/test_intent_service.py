import sys
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.append(str(Path(__file__).resolve().parent.parent))

from services.intent_service import IntentService


class TestIntentService(unittest.TestCase):
    def setUp(self):
        self.intent_service = IntentService()

    def test_rule_based_matching_admission(self):
        # 1. 测试招生规则
        res = self.intent_service.classify_intent("请问今年录取分数线是多少？")
        self.assertEqual(res["intent"], "admission")
        self.assertEqual(res["confidence"], 1.0)
        self.assertIn("分数线", res["reason"])

    def test_rule_based_matching_academic(self):
        # 2. 测试学务规则
        res = self.intent_service.classify_intent("怎么申请我的绩点和奖学金？")
        self.assertEqual(res["intent"], "academic")
        self.assertEqual(res["confidence"], 1.0)
        self.assertIn("绩点", res["reason"])

    def test_rule_based_matching_logistics(self):
        # 3. 测试后勤规则
        res = self.intent_service.classify_intent("我宿舍的校园卡丢了，能报修吗")
        # 宿舍(logistics), 校园卡(logistics), 报修(logistics) => 全是后勤
        res = self.intent_service.classify_intent("请问去哪里可以补办校园卡？")
        self.assertEqual(res["intent"], "logistics")
        self.assertEqual(res["confidence"], 1.0)
        self.assertIn("校园卡", res["reason"])

    def test_rule_based_matching_campus_life(self):
        # 4. 测试校园生活规则
        res = self.intent_service.classify_intent("这周末有哪些社团活动可以参加？")
        self.assertEqual(res["intent"], "campus_life")
        self.assertEqual(res["confidence"], 1.0)
        self.assertIn("社团", res["reason"])

    @patch("openai.resources.chat.completions.Completions.create")
    def test_llm_based_matching_other(self, mock_create):
        # 1. 模拟 LLM 返回正常的 JSON
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = '{"intent": "other", "confidence": 0.90, "reason": "打招呼内容，非校园咨询"}'
        mock_response.choices = [mock_choice]
        mock_create.return_value = mock_response

        # 2. 调用分类（无关键词命中，将触发大模型）
        res = self.intent_service.classify_intent("你好啊！")

        # 3. 断言
        self.assertEqual(res["intent"], "other")
        self.assertEqual(res["confidence"], 0.90)
        self.assertIn("打招呼内容", res["reason"])

    @patch("openai.resources.chat.completions.Completions.create")
    def test_llm_json_malformed_fallback(self, mock_create):
        # 1. 模拟大模型返回了损坏的 JSON 格式
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = "这里是损坏的JSON，根本不是合法的 json 字符串"
        mock_response.choices = [mock_choice]
        mock_create.return_value = mock_response

        # 2. 调用分类，理应优雅捕获并回退至 other
        res = self.intent_service.classify_intent("你好呀，今天过得怎么样？")

        # 3. 断言
        self.assertEqual(res["intent"], "other")
        self.assertEqual(res["confidence"], 0.0)
        self.assertIn("大模型解析分类异常", res["reason"])

    @patch("openai.resources.chat.completions.Completions.create")
    def test_rule_conflict_tie_breaker(self, mock_create):
        # 1. 模拟平局时大模型返回
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = '{"intent": "academic", "confidence": 0.85, "reason": "虽然提到宿舍和学籍，但主要是问怎么转学籍，属于学务"}'
        mock_response.choices = [mock_choice]
        mock_create.return_value = mock_response

        # 2. “学籍”(academic) 和 “宿舍”(logistics) 冲突平局，触发大模型
        res = self.intent_service.classify_intent("因为宿舍问题想改学籍")

        # 3. 断言
        self.assertEqual(res["intent"], "academic")
        self.assertEqual(res["confidence"], 0.85)


if __name__ == "__main__":
    unittest.main()
