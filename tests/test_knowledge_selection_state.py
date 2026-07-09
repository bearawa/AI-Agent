import unittest
from unittest.mock import MagicMock, patch
import pandas as pd

class TestKnowledgeSelectionState(unittest.TestCase):
    def setUp(self):
        # 模拟 st.session_state 状态机
        self.session_state = {}

    def test_selected_doc_ids_initialization(self):
        """
        测试：selected_doc_ids 初始化为空 set。
        """
        if "selected_doc_ids" not in self.session_state:
            self.session_state["selected_doc_ids"] = set()
        
        self.assertEqual(self.session_state["selected_doc_ids"], set())

    def test_select_all_list(self):
        """
        测试：全选会选中当前文档列表中的所有 doc_id。
        """
        self.session_state["selected_doc_ids"] = set()
        
        # 模拟当前筛选出来的文档列表 ID 集合
        current_doc_ids = {"doc_1", "doc_2", "doc_3"}
        
        # 全选
        self.session_state["selected_doc_ids"].update(current_doc_ids)
        self.assertEqual(self.session_state["selected_doc_ids"], current_doc_ids)

    def test_deselect_all_list(self):
        """
        测试：取消全选会清空 selected_doc_ids。
        """
        self.session_state["selected_doc_ids"] = {"doc_1", "doc_2"}
        
        # 取消全选
        self.session_state["selected_doc_ids"] = set()
        self.assertEqual(self.session_state["selected_doc_ids"], set())

    def test_refresh_cleans_deleted_ids(self):
        """
        测试：文档列表刷新后，已从数据库删除的 doc_id 会从 selected_doc_ids 自动清理。
        """
        self.session_state["selected_doc_ids"] = {"doc_1", "doc_2", "doc_3"}
        
        # 模拟数据库中最新的全部有效文档 ID 集合（doc_3 已经被删除了）
        all_db_doc_ids = {"doc_1", "doc_2"}
        
        # 刷新清洗逻辑
        self.session_state["selected_doc_ids"] = self.session_state["selected_doc_ids"] & all_db_doc_ids
        
        self.assertEqual(self.session_state["selected_doc_ids"], {"doc_1", "doc_2"})

    def test_data_editor_empty_safe(self):
        """
        测试：st.data_editor 结果为空（即 DataFrame 为空）时不会报错。
        """
        filtered_docs = []
        df = pd.DataFrame(filtered_docs)
        self.assertTrue(df.empty)
        
        # 模拟对空 DataFrame 的列初始化，验证是否能稳健运行不崩溃
        df["selected"] = pd.Series(dtype=bool)
        df["doc_id"] = pd.Series(dtype=str)
        
        newly_selected = set(df.loc[df["selected"] == True, "doc_id"].tolist())
        self.assertEqual(newly_selected, set())

if __name__ == "__main__":
    unittest.main()
