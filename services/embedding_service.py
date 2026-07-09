from typing import List
from openai import OpenAI
from config import settings
from utils.logger import logger

class EmbeddingService:
    def __init__(self):
        """
        初始化 Embedding 服务。
        """
        self.api_key = settings.DASHSCOPE_API_KEY
        self.base_url = settings.DASHSCOPE_BASE_URL
        self.model = settings.EMBEDDING_MODEL
        
        # 延迟校验，只有在需要调用时才抛错，防止服务启动时直接崩溃
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

    def get_embedding(self, text: str) -> List[float]:
        """
        为单条文本生成向量。
        """
        if not text or not text.strip():
            raise ValueError("输入文本不能为空")

        try:
            logger.debug(f"正在为文本生成向量 (模型: {self.model}): {text[:20]}...")
            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )
            embedding = response.data[0].embedding
            return embedding
        except Exception as e:
            logger.error(f"调用 Embedding 接口生成向量失败: {e}")
            raise RuntimeError(f"Embedding 服务调用失败: {str(e)}")

    def get_embeddings_batch(self, texts: List[str], batch_size: int = 10) -> List[List[float]]:
        """
        批量为文本列表生成向量。
        DashScope Embedding API 限制每批最多 10 条，因此自动分批发送。
        """
        if not texts:
            return []
        
        # 过滤可能存在的空字符串
        valid_texts = [t if t.strip() else " " for t in texts]

        all_embeddings = []
        total = len(valid_texts)
        
        try:
            for start in range(0, total, batch_size):
                end = min(start + batch_size, total)
                batch = valid_texts[start:end]
                batch_num = start // batch_size + 1
                total_batches = (total + batch_size - 1) // batch_size
                logger.info(f"正在批量生成向量，第 {batch_num}/{total_batches} 批 ({len(batch)} 条文本)...")
                
                response = self.client.embeddings.create(
                    model=self.model,
                    input=batch
                )
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)
            
            logger.info(f"批量生成向量完成，共 {len(all_embeddings)} 条")
            return all_embeddings
        except Exception as e:
            logger.error(f"批量调用 Embedding 接口生成向量失败: {e}")
            raise RuntimeError(f"批量 Embedding 服务调用失败: {str(e)}")
