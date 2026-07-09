import re
from typing import List

class ChineseTextSplitter:
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 100):
        """
        初始化中文语义切分器。
        :param chunk_size: 每个切片的大致目标字数 (默认 500 字符)
        :param chunk_overlap: 相邻切片的重叠字符数 (默认 100 字符)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_text(self, text: str) -> List[str]:
        """
        根据标点符号和分段，将中文文本切分为语义连贯的切片。
        """
        if not text or not text.strip():
            return []

        # 按句末标点或换行进行粗切分，(?<=[...]) 保留分隔符
        # 匹配：。 ！？ ； 换行符
        sentences = re.split(r'(?<=[。！？；\n])', text)
        sentences = [s for s in sentences if s]  # 去除空字符串

        chunks = []
        current_chunk = []
        current_length = 0

        for sentence in sentences:
            sentence_len = len(sentence)
            # 如果单句本身就很长，超过了目标 chunk_size
            if sentence_len >= self.chunk_size:
                # 先把之前累积的 chunk 导出
                if current_chunk:
                    chunks.append("".join(current_chunk).strip())
                    current_chunk = []
                    current_length = 0
                # 然后把当前长句强行按硬截断切片
                start = 0
                while start < sentence_len:
                    end = start + self.chunk_size
                    chunks.append(sentence[start:end].strip())
                    # 步长为 chunk_size - chunk_overlap
                    start += (self.chunk_size - self.chunk_overlap)
                continue

            # 正常合并逻辑
            if current_length + sentence_len <= self.chunk_size:
                current_chunk.append(sentence)
                current_length += sentence_len
            else:
                # 导出当前累积的文本
                if current_chunk:
                    chunks.append("".join(current_chunk).strip())
                
                # 计算需要重叠回退的句子
                overlap_chunk = []
                overlap_len = 0
                # 从 current_chunk 尾部开始往前数，直到累积长度达到 chunk_overlap
                for s in reversed(current_chunk):
                    if overlap_len + len(s) <= self.chunk_overlap:
                        overlap_chunk.insert(0, s)
                        overlap_len += len(s)
                    else:
                        # 至少留一句，避免没有 overlap
                        if not overlap_chunk:
                            overlap_chunk.insert(0, s)
                            overlap_len += len(s)
                        break
                
                current_chunk = overlap_chunk + [sentence]
                current_length = sum(len(s) for s in current_chunk)

        # 导出最后一组
        if current_chunk:
            chunks.append("".join(current_chunk).strip())

        # 过滤掉极短的碎片 chunk（比如只有换行符或空格的块）
        chunks = [c for c in chunks if len(c.strip()) > 5]
        return chunks
