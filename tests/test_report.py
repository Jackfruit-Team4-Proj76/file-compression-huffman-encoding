"""
Unit Tests: Compression Ratio Reporting & Analytics
===================================================
Test Case IDs: UT-09, UT-10
Feature Owner: Aishwarya A (PES2UG24AM001)
"""

import unittest
from src.report import (
    calculate_compression_metrics,
    format_bytes,
    format_report,
)


class TestReportModule(unittest.TestCase):
    """Test suite for metrics calculation, byte formatting, and report layouts."""

    def test_ut09_compression_ratio_formula(self) -> None:
        """UT-09 / REQ-10: Verify compression ratio formula: (1 - comp/orig) * 100."""
        original = 1000
        compressed = 400
        metrics = calculate_compression_metrics(original, compressed, duration_seconds=0.1)

        # Expected ratio: (1 - 400/1000) * 100 = 60.0%
        self.assertEqual(metrics["ratio_percent"], 60.0)
        self.assertEqual(metrics["space_saved_bytes"], 600)
        self.assertEqual(metrics["compression_factor"], 2.5)

    def test_ut09_zero_original_size_safety(self) -> None:
        """UT-09: Division-by-zero protection when original size is 0."""
        metrics = calculate_compression_metrics(0, 0)
        self.assertEqual(metrics["ratio_percent"], 0.0)
        self.assertEqual(metrics["space_saved_bytes"], 0)

    def test_ut10_byte_formatting_units(self) -> None:
        """UT-10: Verify human-readable byte unit string representations."""
        self.assertEqual(format_bytes(500), "500 B")
        self.assertEqual(format_bytes(1024), "1.00 KB")
        self.assertEqual(format_bytes(1024 * 1024 * 2.5), "2.50 MB")
        self.assertEqual(format_bytes(1024 * 1024 * 1024 * 1.5), "1.50 GB")

    def test_format_report_ascii_structure(self) -> None:
        """Verify ASCII report includes headers, ratios, and checksums."""
        stats = {
            "operation": "compress",
            "input_path": "sample.txt",
            "output_path": "sample.txt.huff",
            "original_size": 2048,
            "compressed_size": 1024,
            "ratio_percent": 50.0,
            "crc32": "ABCD1234",
            "duration_seconds": 0.05,
        }
        report_str = format_report(stats)
        self.assertIn("HUFFMAN COMPRESS REPORT", report_str)
        self.assertIn("Compression Ratio: +50.00%", report_str)
        self.assertIn("0xABCD1234", report_str)


if __name__ == "__main__":
    unittest.main()
