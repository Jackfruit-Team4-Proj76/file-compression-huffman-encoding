"""
Unit Tests: Huffman Decompression Engine
========================================
Test Case IDs: UT-05, UT-07, UT-08
Feature Owner: Chiranth D Nandi (PES2UG24AM048)
"""

import os
import tempfile
import unittest
from src.compress import compress_bytes
from src.decompress import (
    decompress_bytes,
    CorruptedFileError,
)


class TestDecompressModule(unittest.TestCase):
    """Test suite for decompression, lossless reconstruction, and corruption detection."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_ut05_roundtrip_lossless_text(self) -> None:
        """UT-05 / REQ-6: Decompress .huff back to exact original byte-for-byte content."""
        original_data = (
            b"Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
            b"Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua."
        )
        compressed = compress_bytes(original_data, original_name="lorem.txt")
        decompressed, name = decompress_bytes(compressed)

        self.assertEqual(decompressed, original_data)
        self.assertEqual(name, "lorem.txt")


if __name__ == "__main__":
    unittest.main()
