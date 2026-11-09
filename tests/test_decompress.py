"""
Unit Tests: Huffman Decompression Engine
========================================
Test Case IDs: UT-05, UT-07, UT-08
Feature Owner: Chiranth D Nandi (PES2UG24AM048)
"""

import os
import tempfile
import unittest
from src.compress import compress_bytes, compress_file
from src.decompress import (
    decompress_bytes,
    decompress_file,
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

    def test_ut05_decompress_file_restoration(self) -> None:
        """UT-05: Decompress physical file on disk and verify content fidelity."""
        test_file = os.path.join(self.temp_dir.name, "doc.txt")
        content = b"Unit testing verification with Huffman coding 2026!"
        with open(test_file, "wb") as f:
            f.write(content)

        archive_path, _ = compress_file(test_file)
        restored_file = os.path.join(self.temp_dir.name, "restored.txt")
        out_path, stats = decompress_file(archive_path, restored_file)

        self.assertTrue(os.path.exists(restored_file))
        with open(restored_file, "rb") as f:
            self.assertEqual(f.read(), content)
        self.assertTrue(stats["integrity_verified"])

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

    def test_safety_prevent_unintended_overwrite(self) -> None:
        """Safety NFR-6.2: Refuse to overwrite existing file unless overwrite=True."""
        src_file = os.path.join(self.temp_dir.name, "source.txt")
        with open(src_file, "wb") as f:
            f.write(b"Initial content")
        arch, _ = compress_file(src_file)

        dest_file = os.path.join(self.temp_dir.name, "existing.txt")
        with open(dest_file, "wb") as f:
            f.write(b"Do not clobber me!")

        with self.assertRaises(FileExistsError):
            decompress_file(arch, dest_file, overwrite=False)

        # Should succeed with overwrite=True
        decompress_file(arch, dest_file, overwrite=True)
        with open(dest_file, "rb") as f:
            self.assertEqual(f.read(), b"Initial content")


if __name__ == "__main__":
    unittest.main()
