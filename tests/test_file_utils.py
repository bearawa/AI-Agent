import unittest
import os
import hashlib
import tempfile
from utils.file_utils import calculate_file_hash

class TestFileUtils(unittest.TestCase):

    def test_calculate_file_hash_with_bytes(self):
        data = b"Hello, World!"
        expected_hash = hashlib.sha256(data).hexdigest()
        actual_hash = calculate_file_hash(data)
        self.assertEqual(expected_hash, actual_hash)

    def test_calculate_file_hash_with_file_path(self):
        data = b"Hello, World!"
        expected_hash = hashlib.sha256(data).hexdigest()

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(data)
            temp_file_path = temp_file.name

        try:
            actual_hash = calculate_file_hash(temp_file_path)
            self.assertEqual(expected_hash, actual_hash)
        finally:
            os.remove(temp_file_path)

    def test_calculate_file_hash_file_not_found(self):
        non_existent_path = "non_existent_file.txt"
        with self.assertRaises(FileNotFoundError) as context:
            calculate_file_hash(non_existent_path)
        self.assertIn("找不到计算哈希的文件", str(context.exception))

    def test_calculate_file_hash_invalid_type(self):
        invalid_types = [123, None, ["list"], {"dict": "value"}]
        for invalid_type in invalid_types:
            with self.subTest(invalid_type=invalid_type):
                with self.assertRaises(TypeError) as context:
                    calculate_file_hash(invalid_type)
                self.assertEqual("数据必须是 str (文件路径) 或 bytes (文件二进制流)", str(context.exception))

if __name__ == '__main__':
    unittest.main()
