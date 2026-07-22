import unittest
from utils.display_utils import (
    safe_text,
    format_percent,
    format_confidence,
    format_ms,
    format_score,
    format_bool_status,
    truncate_text,
    safe_json_preview
)

class TestDisplayUtils(unittest.TestCase):
    def test_safe_text(self):
        self.assertEqual(safe_text("hello"), "hello")
        self.assertEqual(safe_text("  hello  "), "hello")
        self.assertEqual(safe_text(123), "123")
        self.assertEqual(safe_text(None), "暂无")
        self.assertEqual(safe_text(""), "暂无")
        self.assertEqual(safe_text("   "), "暂无")
        self.assertEqual(safe_text(None, default="N/A"), "N/A")

    def test_format_percent(self):
        self.assertEqual(format_percent(0.85), "85.0%")
        self.assertEqual(format_percent(1.0), "100.0%")
        self.assertEqual(format_percent(0.0), "0.0%")
        self.assertEqual(format_percent("0.5"), "50.0%")
        self.assertEqual(format_percent(None), "暂无")
        self.assertEqual(format_percent("invalid"), "暂无")
        self.assertEqual(format_percent(None, default="N/A"), "N/A")
        self.assertEqual(format_percent("invalid", default="N/A"), "N/A")

    def test_format_confidence(self):
        self.assertEqual(format_confidence(0.95), "95.0%")
        self.assertEqual(format_confidence(None), "暂无")

    def test_format_ms(self):
        self.assertEqual(format_ms(123), "123 ms")
        self.assertEqual(format_ms(123.45), "123 ms")
        self.assertEqual(format_ms("456"), "456 ms")
        self.assertEqual(format_ms(None), "暂无")
        self.assertEqual(format_ms("invalid"), "暂无")
        self.assertEqual(format_ms(None, default="N/A"), "N/A")

    def test_format_score(self):
        self.assertEqual(format_score(4), "4 / 5")
        self.assertEqual(format_score(4.5), "4 / 5")
        self.assertEqual(format_score("3"), "3 / 5")
        self.assertEqual(format_score(4, total=10), "4 / 10")
        self.assertEqual(format_score(None), "暂无")
        self.assertEqual(format_score("invalid"), "暂无")
        self.assertEqual(format_score(None, default="N/A"), "N/A")

    def test_format_bool_status(self):
        self.assertEqual(format_bool_status(True), "是")
        self.assertEqual(format_bool_status(False), "否")
        self.assertEqual(format_bool_status(1), "是")
        self.assertEqual(format_bool_status(0), "否")
        self.assertEqual(format_bool_status("1"), "是")
        self.assertEqual(format_bool_status("0"), "否")
        self.assertEqual(format_bool_status(True, true_text="Yes", false_text="No"), "Yes")
        self.assertEqual(format_bool_status(False, true_text="Yes", false_text="No"), "No")
        self.assertEqual(format_bool_status(None), "暂无")
        self.assertEqual(format_bool_status("invalid"), "暂无")
        self.assertEqual(format_bool_status(None, default="N/A"), "N/A")

    def test_truncate_text(self):
        self.assertEqual(truncate_text("hello"), "hello")
        self.assertEqual(truncate_text("hello world", max_length=5), "hello...")
        self.assertEqual(truncate_text("hello", max_length=10), "hello")
        self.assertEqual(truncate_text(None), "")
        self.assertEqual(truncate_text(12345, max_length=3), "123...")

    def test_safe_json_preview(self):
        self.assertEqual(safe_json_preview({"a": 1}), '{"a": 1}')
        self.assertEqual(safe_json_preview([1, 2, 3]), "[1, 2, 3]")
        self.assertEqual(safe_json_preview(None), "")
        self.assertEqual(safe_json_preview("hello"), "hello")

        long_dict = {"key": "value" * 20}
        preview = safe_json_preview(long_dict, max_length=20)
        self.assertTrue(preview.endswith("..."))
        self.assertEqual(len(preview), 23) # 20 + len("...")

if __name__ == '__main__':
    unittest.main()
