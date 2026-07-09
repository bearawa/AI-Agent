import os
import sys
import uuid
import json

# 将当前根目录加入 PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 解决 Windows 命令行下打印 Emoji 的编码问题
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from config import settings
from repositories import sqlite_repository
from services.agent_service import AgentService
from services.quality_service import QualityService
from services.tool_registry import TOOL_REGISTRY, call_tool

def run_scenarios():
    print("==================================================")
    print("AIZS｜校园智能咨询平台 - 挑战档场景演示脚本")
    print("演示说明：仅用于项目功能展示，展示工具及 Agent 核心逻辑。")
    print("==================================================")

    # 1. 初始化数据库
    print("\n[第一步] 初始化并升级 SQLite 数据库...")
    sqlite_repository.init_db()
    print("数据库初始化完成。")

    # 2. 检查 API Key
    if not settings.DASHSCOPE_API_KEY:
        print("\n⚠️ 警告：检测到未配置 DASHSCOPE_API_KEY 环境变量！")
        print("为了演示程序能够正常运行，我们将临时运行在测试/Mock模式下。")
        print("请在 .env 文件中填写有效的 DASHSCOPE_API_KEY 以便运行真实大模型测试。")
        # 我们可以提供部分 Mock 测试
    
    # 创建一个测试会话
    session_id = sqlite_repository.create_chat_session("演示场景测试会话")
    print(f"\n已成功创建测试会话，会话 ID: {session_id}")

    agent_service = AgentService()
    
    # 场景 1：主动澄清追问
    print("\n--------------------------------------------------")
    print("场景 1：测试主动澄清追问")
    print("用户输入：“什么时候报名？”")
    print("--------------------------------------------------")
    
    # 模拟检查澄清
    clarify_text = agent_service.check_clarification("什么时候报名？", [])
    if clarify_text:
        print(f"Agent 主动拦截成功！\n回复澄清提问：“{clarify_text}”")
    else:
        print("未触发拦截（可能由于上下文干扰或未匹配）。")

    # 场景 2：工具直接调用测试
    print("\n--------------------------------------------------")
    print("场景 2：测试 Function Calling 工具直接调用（高德 API）")
    print("我们将调用高德天气查询和周边 POI 搜索工具")
    print("--------------------------------------------------")

    print("\n1) 调用高德天气查询工具: get_weather_amap(city='南京', date='明天')")
    weather_res = call_tool("get_weather_amap", {"city": "南京", "date": "明天"}, session_id=session_id)
    print(f"执行成功: {weather_res['success']}")
    print(f"耗时: {weather_res['elapsed_ms']} ms")
    print(f"返回结果: {json.dumps(weather_res['result'], ensure_ascii=False, indent=2)}")

    print("\n2) 调用周边设施搜索工具: search_nearby_poi(keyword='医院', radius=2000)")
    poi_res = call_tool("search_nearby_poi", {"keyword": "医院", "radius": 2000}, session_id=session_id)
    print(f"执行成功: {poi_res['success']}")
    print(f"耗时: {poi_res['elapsed_ms']} ms")
    print(f"返回结果: {json.dumps(poi_res['result'], ensure_ascii=False, indent=2)}")

    # 场景 3：复合推理场景及质量评估
    print("\n--------------------------------------------------")
    print("场景 3：测试复合推理与回答质量评估运行")
    print("用户提问：“新生报到要准备什么？明天天气怎么样？”")
    print("--------------------------------------------------")
    
    # 如果没有 API KEY，则无法跑通大模型的多步推理，因此我们在此处进行分步逻辑模拟展示
    if not settings.DASHSCOPE_API_KEY:
        print("\n[Mock模式运行] 模拟 Agent 拆分与多步推理轨迹：")
        print("  - [步骤 1] 正在分析提问意图：意图分类【招生】")
        print("  - [步骤 2] 已识别复合问题：新生报到准备材料 与 明天天气")
        print("  - [步骤 3] 正在调用校园知识库检索：参数 {'query': '新生报到要准备什么'}")
        
        # 模拟检索
        rag_res = call_tool("search_campus_knowledge", {"query": "新生报到"}, session_id=session_id)
        print(f"    -> [检索结果已返回]，共匹配切片数: {rag_res['result'].get('chunks_count', 0)}")
        
        print("  - [步骤 4] 正在调用高德天气查询工具：参数 {'city': '南京', 'date': '明天'}")
        weather_res = call_tool("get_weather_amap", {"city": "南京", "date": "明天"}, session_id=session_id)
        print(f"    -> [天气结果已返回]")
        
        print("  - [步骤 5] 正在生成综合回答...")
        
        # 伪造助手应答
        mock_answer = "根据学校迎新工作安排，新生报到需准备录取通知书、身份证、近期免冠一寸照片等材料。另外，明天南京的天气状况为晴朗，温度介于 22°C 到 30°C 之间，适宜出门。祝您报到顺利！[演示数据，仅用于项目功能展示]"
        print(f"\nAgent 最终输出回答：\n{mock_answer}")
        
        # 写入一条消息以供质量评估测试
        msg_id = sqlite_repository.save_message(
            session_id=session_id,
            role="assistant",
            content=mock_answer,
            intent="admission",
            intent_name="招生",
            intent_confidence=0.9,
            intent_reason="规则模拟",
            rewritten_query="新生报到准备材料及南京天气",
            has_source=1,
            response_time_ms=300,
            agent_mode=1,
            tool_used=1
        )
        
        # 评估该回答
        quality_service = QualityService()
        quality_service.enable_llm_eval = False # 禁用，走规则
        
        eval_res = quality_service.evaluate_and_save(
            message_id=msg_id,
            session_id=session_id,
            query="新生报到要准备什么？明天天气怎么样？",
            answer=mock_answer,
            sources=rag_res["result"].get("results", []),
            tool_logs=[
                {"name": "get_weather_amap", "success": True, "result": weather_res["result"]},
                {"name": "search_campus_knowledge", "success": True, "result": rag_res["result"]}
            ]
        )
        
        print("\n回答质量评估已运行，评分结果：")
        print(f"  - 得分: {eval_res['score']} / 5")
        print(f"  - 是否低质量: {eval_res['is_low_quality']}")
        print(f"  - 检测缺陷: {eval_res['issues']}")
        print(f"  - 人工建议: {eval_res['suggestion']}")
        
    else:
        print("\n[真实大模型模式] 准备运行真实 Agent 推理...")
        try:
            # 开启流程
            flow = agent_service.handle_agent_chat_flow(session_id, "新生报到要准备什么？明天天气怎么样？")
            for chunk in flow:
                if chunk["type"] == "trace":
                    t = chunk["data"]
                    print(f"  - [步骤 {t['step_index']}] {t['step_title']}: {t['step_detail']}")
                elif chunk["type"] == "text":
                    # 流式文字
                    sys.stdout.write(chunk["data"])
                    sys.stdout.flush()
            print("\n真实推理执行完毕。数据已入库，可在管理后台查看相关审计日志。")
        except Exception as ex:
            print(f"运行真实推理时失败: {ex}")

    print("\n==================================================")
    print("演示运行结束！请使用 `streamlit run app.py` 启动完整平台进行页面体验。")
    print("==================================================")

if __name__ == "__main__":
    run_scenarios()
