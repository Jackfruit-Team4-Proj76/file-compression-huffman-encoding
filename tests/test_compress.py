"""
Unit Tests: Huffman Compression Engine
======================================
Test Case IDs: UT-01, UT-06
Feature Owner: K C Nandan (PES2UG24AM072)
"""

import os
import tempfile
import unittest
from src.compress import (
    compress_bytes,
    compress_file,
    EmptyFileError,
    FileAccessError,
    MAGIC_HEADER,
)


class TestCompressModule(unittest.TestCase):
    """Test suite for single-file compression and boundary conditions."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_ut01_compress_bytes_structure(self) -> None:
        """UT-01: Verify compressed binary output contains magic header and valid layout."""
        sample = b"The quick brown fox jumps over the lazy dog." * 10
        compressed = compress_bytes(sample, original_name="test.txt")

        self.assertTrue(compressed.startswith(MAGIC_HEADER))
        self.assertGreater(len(compressed), len(MAGIC_HEADER) + 16)

    def test_ut01_compress_file_normal(self) -> None:
        """UT-01: Compress a physical text file on disk and verify stats."""
        test_file = os.path.join(self.temp_dir.name, "sample.txt")
        content = "Software Engineering Principles and Agile Scrum Sprints\n" * 200
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(content)

        out_file, stats = compress_file(test_file)
        self.assertTrue(os.path.exists(out_file))
        self.assertGreater(stats["original_size"], 0)
        self.assertGreater(stats["compressed_size"], 0)
        # REQ-3: For repetitive text, compressed size should be smaller
        self.assertLess(stats["compressed_size"], stats["original_size"])
        self.assertGreater(stats["ratio_percent"], 0.0)

    def test_ut06_empty_file_rejected_req4(self) -> None:
        """UT-06 / REQ-4: System must reject empty files with clear error message, not crash."""
        empty_file = os.path.join(self.temp_dir.name, "empty.txt")
        with open(empty_file, "wb") as f:
            pass  # 0 bytes

        with self.assertRaises(EmptyFileError) as ctx:
            compress_file(empty_file)

        self.assertIn("empty (0 bytes)", str(ctx.exception))
        self.assertIn("REQ-4", str(ctx.exception))

    def test_ut06_empty_bytes_rejected(self) -> None:
        """UT-06: Calling compress_bytes with b'' raises EmptyFileError."""
        with self.assertRaises(EmptyFileError):
            compress_bytes(b"")

    def test_single_character_file(self) -> None:
        """Boundary: File with all identical characters ('A'*1000)."""
        single_char_file = os.path.join(self.temp_dir.name, "monotone.txt")
        with open(single_char_file, "wb") as f:
            f.write(b"Z" * 1000)

        out_file, stats = compress_file(single_char_file)
        self.assertTrue(os.path.exists(out_file))
        self.assertLess(stats["compressed_size"], stats["original_size"])

    def test_nonexistent_file_handling(self) -> None:
        """Error handling: Non-existent file raises FileAccessError."""
        missing = os.path.join(self.temp_dir.name, "does_not_exist.txt")
        with self.assertRaises(FileAccessError):
            compress_file(missing)

    def test_self_overwrite_prevention(self) -> None:
        """Safety NFR-6.2: Output path cannot match input path."""
        target = os.path.join(self.temp_dir.name, "data.bin")
        with open(target, "wb") as f:
            f.write(b"Binary payload 1234567890")

        with self.assertRaises(FileAccessError):
            compress_file(target, target)


if __name__ == "__main__":
    unittest.main()
