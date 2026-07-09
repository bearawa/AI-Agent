import os
import hashlib
from typing import Union
from config import settings
from utils.logger import logger

def calculate_file_hash(data: Union[str, bytes]) -> str:
    """
    计算文件内容或文件路径的 SHA-256 哈希值。
    """
    sha256 = hashlib.sha256()
    if isinstance(data, bytes):
        sha256.update(data)
    elif isinstance(data, str):
        if not os.path.exists(data):
            raise FileNotFoundError(f"找不到计算哈希的文件: {data}")
        with open(data, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
    else:
        raise TypeError("数据必须是 str (文件路径) 或 bytes (文件二进制流)")
    return sha256.hexdigest()

def is_allowed_file(file_name: str) -> bool:
    """
    校验文件名后缀是否被允许导入（仅限 pdf, docx, txt）。
    """
    _, ext = os.path.splitext(file_name.lower())
    return ext in ['.pdf', '.docx', '.txt']

def save_uploaded_file(file_name: str, file_bytes: bytes) -> str:
    """
    保存上传的文件二进制数据到 settings.UPLOAD_DIR。
    返回保存的绝对路径。
    """
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    target_path = os.path.join(settings.UPLOAD_DIR, file_name)
    
    # 避免覆盖同名但内容不同的文件。如果有重名文件，加上 hash 前缀或后缀
    if os.path.exists(target_path):
        file_hash = calculate_file_hash(file_bytes)
        base, ext = os.path.splitext(file_name)
        new_name = f"{base}_{file_hash[:8]}{ext}"
        target_path = os.path.join(settings.UPLOAD_DIR, new_name)
        logger.warning(f"文件名 {file_name} 已存在，已重命名保存为 {new_name}")
    
    with open(target_path, 'wb') as f:
        f.write(file_bytes)
    
    logger.info(f"成功保存文件到本地: {target_path}")
    return target_path
