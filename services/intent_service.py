import json
from typing import Dict, Any, Optional
from openai import OpenAI
from config import settings
from utils.logger import logger
from mapping.intent_mapper import intent_mapper

class IntentService:
    def __init__(self):
        """
        初始化意图识别服务。
        """
        self.api_key = settings.DASHSCOPE_API_KEY
        self.base_url = settings.DASHSCOPE_BASE_URL
        self.model = settings.CHAT_MODEL
        self._client = None

        # 规则匹配关键词定义
        self.rules = {
            "admission": ["招生", "录取", "分数线", "专业", "报考", "志愿", "通知书", "新生报到",
                          "高考", "填报", "提档", "调剂", "入学", "迎新", "报到", "注册入学"],
            "academic": ["选课", "考试", "成绩", "学籍", "奖学金", "助学金", "毕业", "绩点",
                         "学分", "补考", "重修", "论文", "答辩", "学位", "挂科", "休学",
                         "转专业", "退学", "课程", "教务", "学费", "缴费", "交学费"],
            "logistics": ["宿舍", "食堂", "图书馆", "校园卡", "报修", "快递", "校医院",
                          "一卡通", "热水", "洗衣", "空调", "断电", "停水", "借阅",
                          "饭卡", "挂失", "充值", "水电费", "维修"],
            "campus_life": ["社团", "活动", "校车", "校园网", "生活用品", "交通", "体育馆",
                            "运动会", "兼职", "实习", "志愿者", "迎新晚会", "文艺",
                            "比赛", "讲座", "wifi", "Wi-Fi", "健身房", "操场"],
            "weather": ["天气", "温度", "下雨", "气温", "预报", "晴", "阴", "雨", "雪"],
            "navigation": ["怎么走", "路线", "导航", "步行", "骑行", "到哪里"]
        }

        # 意图中文映射名（从映射器获取）
        self.intent_names = intent_mapper.INTENT_NAMES

    @property
    def client(self) -> OpenAI:
        if not self.api_key:
            raise ValueError("未检测到 API 密钥（DASHSCOPE_API_KEY 为空），请在 .env 文件中配置后再试。")
        if self._client is None:
            self._client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
        return self._client

    def classify_intent(self, query: str) -> Dict[str, Any]:
        """
        识别用户查询的意图。
        策略：规则优先匹配 -> 命中单一规则且大于0则返回 -> 平局或无匹配则调用大模型兜底。
        返回格式:
        {
            "intent": "academic",
            "confidence": 0.95,
            "secondary_intents": [],
            "reason": "..."
        }
        """
        if not query or not query.strip():
            return {
                "intent": "other",
                "confidence": 1.0,
                "secondary_intents": [],
                "reason": "空查询直接归为其他"
            }

        query_lower = query.lower()
        
        # 1. 规则匹配计数
        match_counts = {}
        matched_words = {}
        for category, keywords in self.rules.items():
            matched = [kw for kw in keywords if kw in query_lower]
            if matched:
                match_counts[category] = len(matched)
                matched_words[category] = matched

        # 找出命中词数最多的分类
        if match_counts:
            max_category = max(match_counts, key=match_counts.get)
            max_count = match_counts[max_category]
            
            # 判断是否是唯一的最大值 (没有平局)
            ties = [cat for cat, count in match_counts.items() if count == max_count]
            
            if len(ties) == 1:
                # 只有唯一的最大匹配分类，直接走规则
                words_str = "、".join(matched_words[max_category])
                reason = f"命中规则关键词：{words_str}"
                logger.info(f"意图识别 [规则命中]：查询 '{query}' -> {max_category} (置信度: 1.0, 原因: {reason})")
                return {
                    "intent": max_category,
                    "confidence": 1.0,
                    "secondary_intents": [],
                    "reason": reason
                }
            else:
                logger.info(f"意图识别 [规则冲突平局]：{ties}，将调用大模型兜底识别。")

        # 2. 调用大模型兜底分类
        return self._classify_by_llm(query)

    def _classify_by_llm(self, query: str) -> Dict[str, Any]:
        """
        使用大模型对用户提问做意图识别分类。
        """
        system_prompt = """你是一个专门服务校园智能客服的意图识别分类助手。
你的任务是将用户的提问（query）归类到以下 5 种主意图分类之一，并可以附带次要意图分类：
1. admission: 招生（涉及高考招生、新生录取、录取分数线、填报志愿、选专业、录取通知书寄送、新生报到点等）
2. academic: 学务（涉及教务选课、期末考试、成绩查询、绩点计算、学籍异动、毕业要求、各种奖学金和助学金评选申请等）
3. logistics: 后勤（涉及学生宿舍入住、食堂餐饮、图书馆借阅、校园一卡通挂失补办、宿舍报修、快递收发、校医院就诊等）
4. campus_life: 校园生活（涉及学生社团招新、文艺体育活动、校车时刻表、校园网办理、生活用品购置、交通出行指引、体育馆开放时间等）
5. other: 其他不属于上述分类的咨询。例如：简单的问候打招呼、聊天八卦、询问当前时间、无关校园生活的社会问题等。

【意图路由规则】
1. 意图分类仅用于统计和辅助检索，不代表最终答案范围。
2. 如果无法确定，请返回 other，不要强行分类。
3. 对复合问题不要只看第一个关键词，如果问题涉及多个领域，请返回 primary_intent（对应字段 "intent"）和 secondary_intents（次要分类列表）。

【约束条件】
1. 必须只返回一个符合 JSON 规范的字符串，不要包裹 ```json ... ``` 标记，不要带任何前缀或后缀。
2. 必须包含字段: 
   - "intent"（主意图，取值范围：admission, academic, logistics, campus_life, other）
   - "confidence"（置信度数值，介于 0.0 到 1.0 之间）
   - "secondary_intents"（次要意图列表，可包含 admission, academic, logistics, campus_life 之一，若无则返回空列表 []）
   - "reason"（中文分类的简短理由）
3. 即使问题分类不确定，也必须从这五种分类中选一个置信度相对较高的，并在 reason 里说明。
"""
        
        user_content = f"请对以下用户提问做意图分类，直接输出 JSON：\n提问：\"{query}\""

        try:
            logger.info(f"开始调用大模型进行意图分类，提问: '{query}'")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.1  # 较低温度保证分类稳定性
            )
            raw_content = response.choices[0].message.content.strip()
            
            # 清理可能包含的 Markdown JSON 标记
            if raw_content.startswith("```"):
                # 兼容格式，防止 LLM 没有听从约束
                lines = raw_content.splitlines()
                # 移除 ```json 和 ```
                clean_lines = [l for l in lines if not l.strip().startswith("```")]
                raw_content = "\n".join(clean_lines).strip()

            result = json.loads(raw_content)
            
            # 基础格式校验
            intent = result.get("intent", "other")
            if intent not in ["admission", "academic", "logistics", "campus_life", "other"]:
                logger.warning(f"大模型返回了未定义的意图类型: {intent}，回退到 other")
                result["intent"] = "other"
            
            # 置信度校验
            try:
                result["confidence"] = float(result.get("confidence", 0.0))
            except ValueError:
                result["confidence"] = 0.0

            # 兼容并提取次要意图
            sec_intents = result.get("secondary_intents", [])
            if not isinstance(sec_intents, list):
                sec_intents = [sec_intents] if sec_intents else []
            valid_sec_intents = []
            for sec in sec_intents:
                if sec in ["admission", "academic", "logistics", "campus_life", "other"] and sec != result["intent"]:
                    valid_sec_intents.append(sec)
            result["secondary_intents"] = valid_sec_intents

            if "reason" not in result:
                result["reason"] = "大模型分类生成"

            logger.info(f"意图识别 [LLM 命中]：查询 '{query}' -> {result['intent']} (置信度: {result['confidence']:.2f}, 次要意图: {result['secondary_intents']}, 原因: {result['reason']})")
            return result

        except Exception as e:
            logger.error(f"调用大模型进行意图分类失败，或 JSON 解析异常: {e}，回退到 other 意图")
            return {
                "intent": "other",
                "confidence": 0.0,
                "secondary_intents": [],
                "reason": f"大模型解析分类异常，原因: {str(e)}"
            }
