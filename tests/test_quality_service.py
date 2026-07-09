import unittest
from services.quality_service import QualityService
from repositories import sqlite_repository

class TestQualityService(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sqlite_repository.init_db()

    def setUp(self):
        self.quality_service = QualityService()
        self.quality_service.enable_llm_eval = False # 运行规则评估测试

    def test_evaluate_by_rules_high_quality(self):
        # 有来源且工具调用成功的优质回答
        res = self.quality_service.evaluate_by_rules(
            query="新生报到要准备什么？明天天气怎么样？",
            answer="材料需要录取通知书。南京天气晴朗。[演示数据]",
            sources=[{"file_name": "迎新指南.pdf", "source_text": "新生报到需准备录取通知书"}],
            tool_logs=[{"name": "get_weather_amap", "success": True, "result": {}}]
        )
        # 3 + 1 (来源) + 1 (工具成功) = 5
        self.assertEqual(res["score"], 5)
        self.assertFalse(res["is_low_quality"])

    def test_evaluate_by_rules_low_quality_policy(self):
        # 政策性提问，但无引用来源
        res = self.quality_service.evaluate_by_rules(
            query="什么时候公布高考录取分数线？",
            answer="一般在六月底左右公布吧。[演示数据]",
            sources=[],
            tool_logs=[]
        )
        # 3 - 2 (无来源回答政策) = 1
        self.assertEqual(res["score"], 1)
        self.assertTrue(res["is_low_quality"])
        self.assertTrue(any("风险" in issue for issue in res["issues"]))

    def test_evaluate_by_rules_low_satisfaction(self):
        # 用户提交点踩
        res = self.quality_service.evaluate_by_rules(
            query="图书馆开门时间",
            answer="八点开门。",
            sources=[{"file_name": "图书馆.pdf", "source_text": "早上八点开馆"}],
            tool_logs=[],
            feedback_rating="dislike"
        )
        # 3 + 1 (来源) - 2 (点踩) = 2
        self.assertEqual(res["score"], 2)
        self.assertTrue(res["is_low_quality"])

    def test_evaluate_and_save(self):
        session_id = sqlite_repository.create_chat_session("单元测试-质量")
        message_id = sqlite_repository.save_message(
            session_id=session_id,
            role="assistant",
            content="这是一条待测试的消息"
        )
        
        # 评估并保存
        eval_res = self.quality_service.evaluate_and_save(
            message_id=message_id,
            session_id=session_id,
            query="咨询奖学金",
            answer="回答奖学金政策",
            sources=[], # 无来源
            tool_logs=[]
        )
        
        # 验证数据库是否已写入，且 message 中 quality_score, is_low_quality 得到同步
        evals = sqlite_repository.list_quality_evaluations(limit=1, is_low_quality=1)
        self.assertEqual(len(evals), 1)
        self.assertEqual(evals[0]["message_id"], message_id)
        self.assertEqual(evals[0]["score"], eval_res["score"])

    def test_reevaluate_on_feedback(self):
        session_id = sqlite_repository.create_chat_session("单元测试-反馈重估")
        # 先保存一条 user 消息
        sqlite_repository.save_message(session_id=session_id, role="user", content="奖学金怎么申请？")
        # 保存一助理消息
        message_id = sqlite_repository.save_message(
            session_id=session_id,
            role="assistant",
            content="奖学金在网上申请。"
        )
        
        # 运行初始评估并保存 (政策提问无来源 => 低质量 1分)
        self.quality_service.evaluate_and_save(
            message_id=message_id,
            session_id=session_id,
            query="奖学金怎么申请？",
            answer="奖学金在网上申请。",
            sources=[],
            tool_logs=[]
        )
        
        # 用户后来点赞 (like) 反馈触发重评估
        # 初始无反馈 3 - 2 = 1分。赞反馈不改变无来源政策的扣分，所以仍然是1分。
        # 如果是优质回答原本5分，踩反馈变成 5 - 2 = 3分。
        # 我们验证 reevaluate_on_feedback 能够跑通并写入即可。
        new_eval = self.quality_service.reevaluate_on_feedback(message_id, "like")
        self.assertIsNotNone(new_eval)
        
        # 检查数据库分数是否更新
        with sqlite_repository.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM quality_evaluations WHERE message_id = ?", (message_id,))
            row = cursor.fetchone()
            self.assertIsNotNone(row)
            row_dict = dict(row)
            self.assertEqual(row_dict["score"], new_eval["score"])
