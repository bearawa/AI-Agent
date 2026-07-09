# -*- coding: utf-8 -*-
"""
AIZS 知识库批量导入服务层
提供多文件导入、ZIP压缩包安全解压导入以及演示知识库一键导入功能。
"""
import os
import zipfile
import tempfile
import shutil
from typing import List, Dict, Any, Optional
from pathlib import Path
from config import settings
from utils.logger import logger
from services.rag_service import RAGService
from repositories import sqlite_repository

class BatchImportService:
    def __init__(self):
        self.rag_service = RAGService()
        
        # 预设的演示文档分类映射表
        self.demo_category_map = {
            "01_演示_图书馆服务指南.pdf": "logistics",
            "02_演示_奖助学金管理办法.pdf": "academic",
            "03_演示_本科招生咨询手册.pdf": "admission",
            "04_演示_新生报到指南.pdf": "admission",
            "05_演示_后勤与校园生活手册.pdf": "logistics",
            "06_演示_校历与重要日期.txt": "campus_life",
            "07_演示_校园常见问题.txt": "other",
            "08_演示_测试问题集.txt": "other"
        }
        
        self.category_names = {
            "general": "通用资料",
            "admission": "招生",
            "academic": "学务",
            "logistics": "后勤",
            "campus_life": "校园生活",
            "other": "其他"
        }

    def auto_detect_category(self, file_name: str, file_bytes: bytes) -> str:
        """
        根据文件名、正文前几段及关键词规则自动判断 category
        """
        file_name_lower = file_name.lower()
        
        # 1. 预设文件名映射（主要用于演示文档）
        if file_name in self.demo_category_map:
            return self.demo_category_map[file_name]
            
        # 2. 关键词规则匹配文件名
        rules = {
            "admission": ["招生", "录取", "分数线", "报考", "志愿", "入学", "迎新", "报到", "高招"],
            "academic": ["选课", "学籍", "奖学金", "助学金", "毕业", "绩点", "学分", "补考", "重修", "论文", "教务", "学费"],
            "logistics": ["宿舍", "食堂", "餐饮", "图书馆", "校园卡", "一卡通", "报修", "快递", "校医院", "水电费", "生活设施"],
            "campus_life": ["社团", "活动", "校车", "校园网", "交通", "体育馆", "运动会", "兼职", "实习", "wifi"]
        }
        
        for cat, keywords in rules.items():
            for kw in keywords:
                if kw in file_name_lower:
                    logger.info(f"自动分类：根据文件名关键词 '{kw}' 将文件 '{file_name}' 归类为 '{cat}'")
                    return cat
                    
        # 3. 如果文件名没匹配到，尝试读取文件内容前段进行文本关键词计数判断
        try:
            from services.document_service import DocumentService
            import tempfile
            _, ext = os.path.splitext(file_name)
            file_type = ext.lower().lstrip('.')
            
            if file_type in ["pdf", "docx", "txt"]:
                with tempfile.NamedTemporaryFile(suffix=f".{file_type}", delete=False) as temp_file:
                    temp_file.write(file_bytes)
                    temp_path = temp_file.name
                
                try:
                    doc_service = DocumentService()
                    chunks = doc_service.parse_document(temp_path, file_type)
                    if chunks:
                        # 拼接前 3 个切片的文本
                        sample_text = "".join([c["text"] for c in chunks[:3]]).lower()
                        # 在正文中匹配关键词
                        match_counts = {cat: 0 for cat in rules}
                        for cat, keywords in rules.items():
                            for kw in keywords:
                                if kw in sample_text:
                                    match_counts[cat] += sample_text.count(kw)
                        
                        max_cat = max(match_counts, key=match_counts.get)
                        if match_counts[max_cat] > 0:
                            logger.info(f"自动分类：根据正文关键词将文件 '{file_name}' 归类为 '{max_cat}'")
                            return max_cat
                finally:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
        except Exception as e:
            logger.warning(f"自动分类：读取正文匹配失败: {e}")
            
        # 无法判断，归为 general
        logger.info(f"自动分类：无法判断分类，文件 '{file_name}' 默认归类为 'general'")
        return "general"

    def import_single_file(self, file_bytes: bytes, file_name: str, category: str) -> Dict[str, Any]:
        """
        导入单个文件，捕获具体的业务异常并归纳状态。
        """
        if category == "auto":
            category = self.auto_detect_category(file_name, file_bytes)
            
        category_name = self.category_names.get(category, "其他")
        _, ext = os.path.splitext(file_name)
        file_type = ext.lower().lstrip('.')
        file_size = len(file_bytes)
        
        result = {
            "file_name": file_name,
            "file_type": file_type.upper(),
            "file_size": f"{file_size / 1024:.2f} KB",
            "category": category_name,
            "status": "failed",
            "chunk_count": 0,
            "error_message": None
        }

        # 检查是否为支持的文件类型
        if file_type not in ["pdf", "docx", "txt"]:
            result["error_message"] = "不支持的文件类型，仅支持 PDF, DOCX, TXT"
            return result

        try:
            doc_id = self.rag_service.import_document(
                file_name=file_name,
                file_bytes=file_bytes,
                category=category,
                category_name=category_name
            )
            # 导入成功，查询分片数
            doc = sqlite_repository.get_document(doc_id)
            result["status"] = "success"
            result["chunk_count"] = doc["chunk_count"] if doc else 0
            
        except ValueError as ve:
            # 捕获已知业务逻辑校验（重复上传、重名）
            error_str = str(ve)
            if "已在知识库中导入" in error_str or "已存在同名文档" in error_str:
                result["status"] = "skipped"
                result["error_message"] = "重复文件已被跳过"
            else:
                result["status"] = "failed"
                result["error_message"] = error_str
                
        except Exception as e:
            # 捕获其他解析/Embedding/Chroma异常
            logger.error(f"批量导入单文件 {file_name} 失败: {e}")
            result["status"] = "failed"
            result["error_message"] = f"系统错误: {str(e)}"
            
        return result

    def import_uploaded_files(self, files: List[Any], category: str) -> List[Dict[str, Any]]:
        """
        批量导入 Streamlit 上传的多个文件。
        """
        results = []
        for file in files:
            file_bytes = file.read() if hasattr(file, "read") else file.getvalue()
            file_name = file.name
            res = self.import_single_file(file_bytes, file_name, category)
            results.append(res)
        return results

    def import_zip_file(self, zip_file_bytes: bytes, category: str) -> List[Dict[str, Any]]:
        """
        批量导入 ZIP 压缩包，包含 Zip Slip 安全校验和文件名乱码解决。
        """
        results = []
        temp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(temp_dir, "upload.zip")
        
        try:
            with open(zip_path, "wb") as f:
                f.write(zip_file_bytes)
                
            with zipfile.ZipFile(zip_path, 'r') as zref:
                for member in zref.infolist():
                    # 1. 解决中文文件名乱码问题
                    try:
                        filename = member.filename.encode('cp437').decode('utf-8')
                    except (UnicodeEncodeError, UnicodeDecodeError):
                        try:
                            filename = member.filename.encode('cp437').decode('gbk')
                        except (UnicodeEncodeError, UnicodeDecodeError):
                            filename = member.filename

                    # 忽略 Mac OS X 产生的垃圾文件和隐藏文件
                    if "__MACOSX" in filename or os.path.basename(filename).startswith("."):
                        continue

                    try:
                        # 2. Zip Slip 路径安全校验
                        target_path = Path(os.path.join(temp_dir, filename)).resolve()
                        # 检查解析后的绝对路径是否位于临时目录下，防止 ../ 穿越
                        if not target_path.is_relative_to(Path(temp_dir).resolve()):
                            logger.warning(f"检测到潜在的 Zip Slip 路径穿越攻击，拦截文件: {member.filename}")
                            results.append({
                                "file_name": filename,
                                "file_type": "UNKNOWN",
                                "file_size": "0.00 KB",
                                "category": self.category_names.get(category, "其他"),
                                "status": "failed",
                                "chunk_count": 0,
                                "error_message": "安全验证失败：禁止路径穿越文件写入"
                            })
                            continue

                        # 如果是目录，直接创建并跳过文件处理
                        if member.is_dir():
                            os.makedirs(target_path, exist_ok=True)
                            continue

                        # 获取文件后缀
                        _, ext = os.path.splitext(filename)
                        ext_lower = ext.lower().lstrip('.')

                        # 不支持的文件类型，标为 skipped 且说明原因
                        if ext_lower not in ["pdf", "docx", "txt"]:
                            results.append({
                                "file_name": filename,
                                "file_type": ext_lower.upper() or "UNKNOWN",
                                "file_size": f"{member.file_size / 1024:.2f} KB",
                                "category": self.category_names.get(category, "其他"),
                                "status": "skipped",
                                "chunk_count": 0,
                                "error_message": "不支持的文件类型，已跳过"
                            })
                            continue

                        # 创建父级目录并写入解压文件
                        os.makedirs(target_path.parent, exist_ok=True)
                        with zref.open(member) as source, open(target_path, "wb") as target:
                            shutil.copyfileobj(source, target)

                        with open(target_path, "rb") as f:
                            file_data = f.read()

                        res = self.import_single_file(file_data, os.path.basename(filename), category)
                        results.append(res)
                    except Exception as member_err:
                        logger.error(f"处理压缩包内文件 {filename} 失败: {member_err}")
                        results.append({
                            "file_name": os.path.basename(filename),
                            "file_type": ext_lower.upper() if 'ext_lower' in locals() else "UNKNOWN",
                            "file_size": f"{member.file_size / 1024:.2f} KB",
                            "category": self.category_names.get(category, "其他"),
                            "status": "failed",
                            "chunk_count": 0,
                            "error_message": f"处理失败: {str(member_err)}"
                        })
                        
        except Exception as e:
            logger.error(f"解析 ZIP 文件失败: {e}")
            results.append({
                "file_name": "ZIP 压缩包",
                "file_type": "ZIP",
                "file_size": f"{len(zip_file_bytes) / 1024:.2f} KB",
                "category": self.category_names.get(category, "其他"),
                "status": "failed",
                "chunk_count": 0,
                "error_message": f"解压 ZIP 失败: {str(e)}"
            })
        finally:
            # 安全自动清理临时解压目录
            shutil.rmtree(temp_dir, ignore_errors=True)
            
        return results

    def import_demo_documents(self, category_map: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        """
        一键导入预置演示知识库。
        """
        results = []
        demo_dir = Path(settings.BASE_DIR) / "demo_documents"
        
        if not demo_dir.exists():
            logger.warning(f"未找到演示文档目录: {demo_dir}")
            return [{
                "file_name": "演示文档目录",
                "file_type": "DIR",
                "file_size": "0 KB",
                "category": "其他",
                "status": "failed",
                "chunk_count": 0,
                "error_message": "本地演示文档目录 demo_documents 不存在，无法导入。"
            }]

        cmap = category_map if category_map is not None else self.demo_category_map
        
        for item in demo_dir.iterdir():
            if item.is_file() and item.suffix.lower().lstrip('.') in ["pdf", "docx", "txt"]:
                file_name = item.name
                # 忽略说明文档
                if "README" in file_name:
                    continue
                
                category = cmap.get(file_name, "other")
                
                try:
                    with open(item, "rb") as f:
                        file_bytes = f.read()
                    
                    res = self.import_single_file(file_bytes, file_name, category)
                    results.append(res)
                except Exception as e:
                    logger.error(f"读取演示文档 {file_name} 失败: {e}")
                    results.append({
                        "file_name": file_name,
                        "file_type": item.suffix.lower().lstrip('.').upper(),
                        "file_size": f"{item.stat().st_size / 1024:.2f} KB",
                        "category": self.category_names.get(category, "其他"),
                        "status": "failed",
                        "chunk_count": 0,
                        "error_message": f"文件读取失败: {str(e)}"
                    })
                    
        return results

    def build_import_report(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        汇总批量导入的最终运行指标报表。
        """
        report = {
            "total_files": len(results),
            "success_count": 0,
            "skipped_count": 0,
            "failed_count": 0,
            "total_chunks": 0
        }
        
        for res in results:
            if res["status"] == "success":
                report["success_count"] += 1
                report["total_chunks"] += res["chunk_count"]
            elif res["status"] == "skipped":
                report["skipped_count"] += 1
            else:
                report["failed_count"] += 1
                
        return report
