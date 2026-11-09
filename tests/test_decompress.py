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

    def test_ut07_invalid_magic_header(self) -> None:
        """UT-07 / REQ-7: Reject file with invalid magic bytes."""
        bad_data = b"NOT_A_HUFF_FILE_HEADER"
        with self.assertRaises(CorruptedFileError) as ctx:
            decompress_bytes(bad_data)
        self.assertIn("Invalid file signature", str(ctx.exception))

    def test_ut07_truncated_archive(self) -> None:
        """UT-07 / REQ-7: Reject truncated file (too short for header)."""
        too_short = b"HUF"
        with self.assertRaises(CorruptedFileError):
            decompress_bytes(too_short)

    def test_ut08_tampered_payload_crc_mismatch(self) -> None:
        """UT-08 / REQ-7: Detect tampering in bitstream via CRC32 validation failure."""
        original_data = b"Sensitive information that must not be corrupted!" * 5
        compressed = bytearray(compress_bytes(original_data, original_name="test.txt"))

        # Tamper with the last byte of the bitstream
        compressed[-1] ^= 0xFF

        with self.assertRaises(CorruptedFileError) as ctx:
            decompress_bytes(bytes(compressed))

        self.assertTrue(
            "CRC32 Checksum verification failed" in str(ctx.exception)
            or "Bitstream terminated" in str(ctx.exception)
            or "Invalid bitstream" in str(ctx.exception)
        )


if __name__ == "__main__":
    unittest.main()
