"""
Integration & End-to-End Test Suite
===================================
Test Case IDs: IT-03, IT-05, IT-06
Feature Owner: Jashruth K A (PES2UG24AM069)
"""

import os
import tempfile
import time
import unittest
from src.compress import compress_file, compress_bytes
from src.decompress import decompress_file, decompress_bytes


class TestIntegration(unittest.TestCase):
    """End-to-end integration and multi-format validation."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_it03_all_256_byte_values_roundtrip(self) -> None:
        """IT-03: Verify lossless compression across all 256 distinct byte values (0-255)."""
        all_bytes = bytes(range(256)) * 100
        compressed = compress_bytes(all_bytes, "full_spectrum.bin")
        restored, name = decompress_bytes(compressed)

        self.assertEqual(restored, all_bytes)
        self.assertEqual(name, "full_spectrum.bin")

    def test_it03_binary_simulated_image(self) -> None:
        """IT-03: Binary simulated image file with PNG signature and high-entropy byte patterns."""
        png_signature = b"\x89PNG\r\n\x1a\n"
        simulated_data = png_signature + (os.urandom(500) * 10)

        file_path = os.path.join(self.temp_dir.name, "image.png")
        with open(file_path, "wb") as f:
            f.write(simulated_data)

        arch_path, _ = compress_file(file_path)
        restored_path = os.path.join(self.temp_dir.name, "restored.png")
        decompress_file(arch_path, restored_path)

        with open(restored_path, "rb") as f:
            self.assertEqual(f.read(), simulated_data)

    def test_it06_performance_under_5_seconds_nfr61(self) -> None:
        """IT-06 / NFR-6.1: Verify 1MB-2MB test file roundtrips well within performance SLA."""
        # 1.5 MB test payload
        pattern = b"PES University UE24CS341A Software Engineering Project 76 Huffman Compression\n"
        large_data = pattern * ((1_500_000 // len(pattern)) + 1)

        test_file = os.path.join(self.temp_dir.name, "perf_test.txt")
        with open(test_file, "wb") as f:
            f.write(large_data)

        t0 = time.perf_counter()
        arch_path, c_stats = compress_file(test_file)
        restored_path = os.path.join(self.temp_dir.name, "perf_restored.txt")
        _, d_stats = decompress_file(arch_path, restored_path)
        total_time = time.perf_counter() - t0

        # Lossless check
        self.assertEqual(os.path.getsize(restored_path), len(large_data))
        with open(restored_path, "rb") as f:
            self.assertEqual(f.read(), large_data)

        # Performance constraint: roundtrip should complete comfortably within 5 seconds
        self.assertLess(
            total_time,
            5.0,
            f"Performance SLA breached: roundtrip took {total_time:.2f}s (must be < 5.0s)",
        )
        self.assertGreater(c_stats["ratio_percent"], 30.0)


if __name__ == "__main__":
    unittest.main()
