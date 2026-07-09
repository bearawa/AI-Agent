from typing import List, Dict, Any, Generator, Optional
from openai import OpenAI
from config import settings
from utils.logger import logger

class LLMService:
    def __init__(self):
        """
        初始化大语言模型服务。
        """
        self.api_key = settings.DASHSCOPE_API_KEY
        self.base_url = settings.DASHSCOPE_BASE_URL
        self.model = settings.CHAT_MODEL
        self._client = None

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

    def rewrite_query(self, history: List[Dict[str, str]], current_query: str) -> str:
        """
        将当前追问及上下文历史改写为一个独立的检索问题。
        :param history: 对话历史消息列表 [{"role": "user", "content": "..."}]，通常最多包含最近6条
        :param current_query: 用户当前输入的问题
        """
        if not history:
            return current_query

        # 构造改写 Prompt
        history_str = ""
        for msg in history:
            role_cn = "学生/家长" if msg["role"] == "user" else "客服助手"
            history_str += f"{role_cn}: {msg['content']}\n"

        prompt = f"""你是一个问答检索改写助手。你的任务是根据历史对话和最新的提问，把最新的提问改写为一个“独立的、语义完整的检索问题”。
这个检索问题将用于向量数据库检索，因此必须消除代词指代（如“它”、“他”、“那里”、“这”），并补全上下文缺失的信息。

【约束条件】
1. 如果最新的提问本身已经非常完整，不需要依赖历史对话，请【直接输出原提问】，不要做任何修改。
2. 绝对不要尝试回答提问，也无需进行任何解释，仅输出改写后的检索问题。
3. 改写后语句要通顺精炼，适合作为搜索词。

【对话历史】
{history_str}
【最新提问】
{current_query}

【改写后的检索提问】(请直接输出检索问题，不要带任何前缀或解释)："""

        try:
            logger.info(f"正在改写多轮对话问题，原提问: '{current_query}'")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个只输出改写问题、绝不解释、绝不回答问题的改写助手。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1  # 较低温度保证改写稳定性
            )
            rewritten = response.choices[0].message.content.strip()
            # 去除可能包含的引号等无用符号
            rewritten = rewritten.strip('"').strip("'")
            logger.info(f"改写完成。改写后的检索提问: '{rewritten}'")
            return rewritten
        except Exception as e:
            logger.error(f"调用 LLM 改写问题失败: {e}，将使用原始提问。")
            return current_query

    def chat_stream(
        self,
        history: List[Dict[str, str]],
        retrieved_chunks: List[Dict[str, Any]],
        current_query: str,
        intent: Optional[str] = None,
        intent_confidence: Optional[float] = None
    ) -> Generator[str, None, None]:
        """
        基于检索原文和历史对话流式生成助手回答。
        :param history: 包含最近对话历史的消息列表 [{"role": "user"|"assistant", "content": "..."}]
        :param retrieved_chunks: 向量检索出来的相关片段列表
        :param current_query: 改写前的当前用户问题
        :param intent: 用户当前意图分类的中文名称
        :param intent_confidence: 意图分类的置信度
        """
        # 1. 构建参考资料内容
        context_str = ""
        if retrieved_chunks:
            for idx, chunk in enumerate(retrieved_chunks):
                page_info = f"第 {chunk['page_number']} 页" if chunk.get('page_number') is not None else f"片段 {chunk['chunk_index']}"
                chunk_cat = chunk.get("category_name", "未分类")
                context_str += f"--- 资料来源：{chunk['file_name']} ({page_info}) | 分类：{chunk_cat} ---\n"
                context_str += f"{chunk['source_text']}\n\n"
        else:
            context_str = "（当前未检索到任何相关的参考资料）"

        # 2. 构建系统约束 Prompt
        system_prompt = """你是 AIZS｜校园智能咨询平台的智能助手。
你必须严格依据【知识库检索结果】回答用户问题。

重要规则：
1. 检索结果可能来自不同分类，分类只表示资料管理标签，不代表答案边界。
2. 回答时请优先依据与用户问题语义最相关的片段，而不是优先依据分类标签。
3. 如果多个片段内容冲突，请说明“资料之间存在不一致”，并建议以学校最新官方通知为准。
4. 如果知识库中没有足够依据，请明确说明“当前知识库未检索到相关依据”，不要编造政策、电话、日期、地点、分数线。
5. 不要因为用户问题被识别为某个意图，就忽略其他分类中更相关的资料。
6. 不要伪造来源。
7. 回答后尽量指出依据来自哪些资料（例如注明来自某个文件名或页码）。
8. 你的回答语言必须简明易懂、重点突出，适合学生和家长阅读。排版建议使用 Markdown 的分段或列表形式。
"""

        # 3. 构造传递给大模型的完整上下文列表
        messages = [{"role": "system", "content": system_prompt}]
        
        # 加上最近的历史
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})
            
        # 加上意图分类结果
        conf_val = intent_confidence if intent_confidence is not None else 0.0
        intent_info = f"intent: {intent or 'other'}\nconfidence: {conf_val:.2f}\n说明：该结果仅用于辅助理解问题，不作为限制检索范围的依据。"
            
        # 加上当前的提问以及附带的参考资料
        user_message_content = f"""【意图识别结果】
{intent_info}

【知识库检索结果】
{context_str}

【当前问题】
{current_query}"""
        messages.append({"role": "user", "content": user_message_content})

        try:
            logger.info("开始调用 LLM 流式生成回答...")
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                stream=True
            )
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
            logger.info("LLM 流式回答生成完成")
        except Exception as e:
            logger.error(f"调用 LLM 流式接口失败: {e}")
            raise RuntimeError(f"大模型响应失败: {str(e)}")
