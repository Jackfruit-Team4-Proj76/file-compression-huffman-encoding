"""
Unit Tests: Command-Line Interface (CLI)
========================================
Test Case ID: IT-04
Feature Owner: Aishwarya A (PES2UG24AM001)
Contributor: K C Nandan (PES2UG24AM072)
"""

import os
import tempfile
import unittest
from unittest.mock import patch
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

    def test_cli_compress_default_output(self) -> None:
        """IT-04: CLI compress file with default .huff output path."""
        src = os.path.join(self.temp_dir.name, "default_test.txt")
        with open(src, "wb") as f:
            f.write(b"Default output test data content" * 10)
        ret = main(["compress", src])
        self.assertEqual(ret, 0)
        self.assertTrue(os.path.exists(src + ".huff"))

    def test_cli_compress_empty_file(self) -> None:
        """IT-04: CLI compress empty file returns code 2 (REQ-4)."""
        empty = os.path.join(self.temp_dir.name, "empty.txt")
        open(empty, "wb").close()
        ret = main(["compress", empty])
        self.assertEqual(ret, 2)

    def test_cli_compress_directory_default_output(self) -> None:
        """IT-04: CLI compress directory with default .huffz output path."""
        dir_path = os.path.join(self.temp_dir.name, "test_dir")
        os.makedirs(dir_path)
        with open(os.path.join(dir_path, "sample.txt"), "wb") as f:
            f.write(b"Directory compression test file")
        ret = main(["compress", dir_path])
        self.assertEqual(ret, 0)
        self.assertTrue(os.path.exists(dir_path + ".huffz"))

    def test_cli_decompress_directory_archive(self) -> None:
        """IT-04: CLI decompress .huffz batch directory archive."""
        dir_path = os.path.join(self.temp_dir.name, "dir_for_huffz")
        os.makedirs(dir_path)
        with open(os.path.join(dir_path, "a.txt"), "wb") as f:
            f.write(b"File A in huffz archive")
        huffz_path = os.path.join(self.temp_dir.name, "out.huffz")
        main(["compress", dir_path, "-o", huffz_path])

        dest = os.path.join(self.temp_dir.name, "extracted")
        ret = main(["decompress", huffz_path, "-o", dest])
        self.assertEqual(ret, 0)
        self.assertTrue(os.path.exists(dest))

    def test_cli_decompress_missing_file(self) -> None:
        """IT-04: CLI decompress missing file returns code 1."""
        ret = main(["decompress", os.path.join(self.temp_dir.name, "missing.huff")])
        self.assertEqual(ret, 1)

    def test_cli_decompress_existing_file_without_force(self) -> None:
        """IT-04: CLI decompress over existing file without force returns code 6 (NFR-6.2)."""
        src = os.path.join(self.temp_dir.name, "safety.txt")
        with open(src, "wb") as f:
            f.write(b"Safety file overwrite test" * 10)
        huff = os.path.join(self.temp_dir.name, "safety.txt.huff")
        main(["compress", src, "-o", huff])
        ret = main(["decompress", huff, "-o", src])
        self.assertEqual(ret, 6)

    def test_cli_decompress_corrupted_file(self) -> None:
        """IT-04: CLI decompress corrupted archive returns code 5."""
        bad_file = os.path.join(self.temp_dir.name, "corrupt.huff")
        with open(bad_file, "wb") as f:
            f.write(b"NOT_A_VALID_HUFFMAN_ARCHIVE_HEADER")
        ret = main(["decompress", bad_file])
        self.assertEqual(ret, 5)

    def test_cli_info_missing_file(self) -> None:
        """IT-04: CLI info missing archive returns code 1."""
        ret = main(["info", os.path.join(self.temp_dir.name, "nonexistent.huffz")])
        self.assertEqual(ret, 1)

    def test_cli_benchmark_missing_file(self) -> None:
        """IT-04: CLI benchmark missing file returns code 1."""
        ret = main(["benchmark", os.path.join(self.temp_dir.name, "missing_bench.txt")])
        self.assertEqual(ret, 1)

    def test_cli_no_args_launches_gui_mock(self) -> None:
        """IT-04: Running CLI with no arguments launches GUI without blocking."""
        with patch("src.gui.launch_gui"):
            ret = main([])
            self.assertEqual(ret, 0)


if __name__ == "__main__":
    unittest.main()
