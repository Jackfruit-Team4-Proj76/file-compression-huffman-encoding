"""
Integration Tests: Batch & Directory Archiving Engine
=====================================================
Test Case IDs: IT-01, IT-02
Feature Owner: Jashruth K A (PES2UG24AM069)
"""

import os
import tempfile
import unittest
from src.batch import (
    compress_batch,
    decompress_batch,
    inspect_archive,
    collect_files,
)
from src.compress import EmptyFileError


class TestBatchModule(unittest.TestCase):
    """Test suite for multi-file archiving and folder structure preservation."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_it01_compress_multiple_files(self) -> None:
        """IT-01 / REQ-8: Compress multiple independent files into a single archive."""
        f1 = os.path.join(self.temp_dir.name, "file1.txt")
        f2 = os.path.join(self.temp_dir.name, "file2.csv")
        with open(f1, "wb") as f:
            f.write(b"Content of file 1\n" * 20)
        with open(f2, "wb") as f:
            f.write(b"id,name,role\n1,alice,admin\n2,bob,user\n" * 15)

        archive_path = os.path.join(self.temp_dir.name, "multi.huffz")
        stats = compress_batch([f1, f2], archive_path)

        self.assertTrue(os.path.exists(archive_path))
        self.assertEqual(stats["file_count"], 2)
        self.assertGreater(stats["original_size"], 0)

        # Inspect archive
        info = inspect_archive(archive_path)
        self.assertEqual(info["file_count"], 2)

    def test_it02_preserve_folder_structure_req9(self) -> None:
        """IT-02 / REQ-9: Preserve nested relative folder hierarchy upon decompression."""
        root_dir = os.path.join(self.temp_dir.name, "my_project")
        sub_dir = os.path.join(root_dir, "nested", "level2")
        os.makedirs(sub_dir, exist_ok=True)

        file_a = os.path.join(root_dir, "root_file.txt")
        file_b = os.path.join(sub_dir, "deep_file.bin")

        with open(file_a, "wb") as f:
            f.write(b"Root level payload content!" * 10)
        with open(file_b, "wb") as f:
            f.write(b"\x00\x01\x02\x03\xFF\xFE\xFD" * 50)

        archive_path = os.path.join(self.temp_dir.name, "nested.huffz")
        compress_batch([root_dir], archive_path)

        # Unpack to clean directory
        unpack_dir = os.path.join(self.temp_dir.name, "restored_dir")
        stats = decompress_batch(archive_path, unpack_dir)

        self.assertEqual(stats["files_extracted"], 2)

        # Verify folder structure recreated
        expected_a = os.path.join(unpack_dir, "my_project", "root_file.txt")
        expected_b = os.path.join(unpack_dir, "my_project", "nested", "level2", "deep_file.bin")

        self.assertTrue(os.path.exists(expected_a), f"Missing: {expected_a}")
        self.assertTrue(os.path.exists(expected_b), f"Missing: {expected_b}")

        with open(expected_a, "rb") as f:
            self.assertEqual(f.read(), b"Root level payload content!" * 10)
        with open(expected_b, "rb") as f:
            self.assertEqual(f.read(), b"\x00\x01\x02\x03\xFF\xFE\xFD" * 50)

    def test_empty_folder_rejection(self) -> None:
        """Boundary: Compressing an empty folder raises EmptyFileError."""
        empty_folder = os.path.join(self.temp_dir.name, "empty_dir")
        os.makedirs(empty_folder, exist_ok=True)
        archive_path = os.path.join(self.temp_dir.name, "empty.huffz")

        with self.assertRaises(EmptyFileError):
            compress_batch([empty_folder], archive_path)


if __name__ == "__main__":
    unittest.main()
