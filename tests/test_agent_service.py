import unittest
from services.agent_service import AgentService
from repositories import sqlite_repository

class TestAgentService(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sqlite_repository.init_db()

    def setUp(self):
        self.agent_service = AgentService()

    def test_check_clarification_no_context(self):
        # 模糊提问，且无上下文
        reply = self.agent_service.check_clarification("什么时候报名？", [])
        self.assertIsNotNone(reply)
        self.assertIn("请问您咨询的是本科招生报名、研究生报名", reply)
        
        reply2 = self.agent_service.check_clarification("怎么缴费？", [])
        self.assertIsNotNone(reply2)
        self.assertIn("请问您咨询的是学费缴纳、校园一卡通充值", reply2)

    def test_check_clarification_with_context(self):
        # 模糊提问，但有上下文提及了招生相关
        history = [
            {"role": "user", "content": "我想咨询一下关于高考招生的问题"},
            {"role": "assistant", "content": "好的，本校本科生招生工作一般在每年6月中下旬开始。"}
        ]
        reply = self.agent_service.check_clarification("什么时候报名？", history)
        # 命中上下文关键词，应该不拦截（即返回 None，走普通 RAG 或 Agent 处理）
        self.assertIsNone(reply)

    def test_agent_trace_logging(self):
        session_id = sqlite_repository.create_chat_session("单元测试-Agent轨迹")
        # 模拟记录 Agent 轨迹
        trace_id = sqlite_repository.save_agent_trace(
            session_id=session_id,
            message_id="msg-test-123",
            step_index=1,
            step_type="test",
            step_title="已识别复合问题",
            step_detail="测试轨迹步骤详情描述"
        )
        self.assertIsNotNone(trace_id)
        self.assertNotEqual(trace_id, "")
        
        # 提取轨迹
        traces = sqlite_repository.get_agent_traces(session_id, "msg-test-123")
        self.assertEqual(len(traces), 1)
        self.assertEqual(traces[0]["step_title"], "已识别复合问题")
        self.assertEqual(traces[0]["step_type"], "test")
