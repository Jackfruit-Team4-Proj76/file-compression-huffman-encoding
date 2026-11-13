"""
Unit Tests: Command-Line Interface (CLI)
========================================
Test Case ID: IT-04
Feature Owner: Aishwarya A (PES2UG24AM001)
"""

import os
import tempfile
import unittest
from src.cli import main


class TestCLI(unittest.TestCase):
    """Test suite for CLI arguments, subcommands, and exit statuses."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_cli_compress_and_decompress(self) -> None:
        """IT-04: End-to-end CLI command execution for compress and decompress."""
        src_path = os.path.join(self.temp_dir.name, "cli_test.txt")
        with open(src_path, "wb") as f:
            f.write(b"CLI compression testing string data 12345!" * 20)

        out_huff = os.path.join(self.temp_dir.name, "cli_test.txt.huff")
        restored = os.path.join(self.temp_dir.name, "cli_restored.txt")

        # Compress via CLI
        ret_c = main(["compress", src_path, "-o", out_huff])
        self.assertEqual(ret_c, 0)
        self.assertTrue(os.path.exists(out_huff))

        # Decompress via CLI
        ret_d = main(["decompress", out_huff, "-o", restored, "--force"])
        self.assertEqual(ret_d, 0)
        self.assertTrue(os.path.exists(restored))

        with open(restored, "rb") as f:
            self.assertEqual(f.read(), b"CLI compression testing string data 12345!" * 20)

    def test_cli_missing_input_file(self) -> None:
        """IT-04: CLI returns non-zero error code for missing input file."""
        ret = main(["compress", os.path.join(self.temp_dir.name, "nonexistent.txt")])
        self.assertNotEqual(ret, 0)

    def test_cli_benchmark_subcommand(self) -> None:
        """IT-04: CLI benchmark subcommand runs and outputs metrics."""
        sample_path = os.path.join(self.temp_dir.name, "bench_sample.txt")
        with open(sample_path, "wb") as f:
            f.write(b"Benchmark input payload repetitive pattern ABCDEFGHIJKLMNOPQRSTUVWXYZ\n" * 50)

        ret = main(["benchmark", sample_path])
        self.assertEqual(ret, 0)

    def test_cli_info_subcommand(self) -> None:
        """IT-04: CLI info subcommand inspects batch archive manifest."""
        sample_dir = os.path.join(self.temp_dir.name, "sample_folder")
        os.makedirs(sample_dir, exist_ok=True)
        with open(os.path.join(sample_dir, "f1.txt"), "wb") as f:
            f.write(b"Hello from nested batch file 1!")

        archive_path = os.path.join(self.temp_dir.name, "sample.huffz")
        ret_c = main(["compress", sample_dir, "-o", archive_path])
        self.assertEqual(ret_c, 0)

        ret_info = main(["info", archive_path])
        self.assertEqual(ret_info, 0)


if __name__ == "__main__":
    unittest.main()
