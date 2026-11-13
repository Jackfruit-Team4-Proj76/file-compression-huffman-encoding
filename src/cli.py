"""
Command-Line Interface (CLI)
============================
Functional Feature Owned By: Aishwarya A (PES2UG24AM001)

Provides a rich command-line tool with subcommands:
- compress: Compress a single file or directory
- decompress: Decompress .huff or .huffz archive
- info: Inspect archive headers and manifest without extracting
- benchmark: Measure compression speed, ratio, and throughput
- --gui: Launch the interactive desktop Graphical User Interface
"""

from __future__ import annotations
import argparse
import os
import sys
import time

from src.compress import compress_file, EmptyFileError, CompressionError
from src.decompress import decompress_file, CorruptedFileError, DecompressionError
from src.batch import compress_batch, decompress_batch, inspect_archive
from src.report import format_report, format_bytes, calculate_compression_metrics


def handle_compress(args: argparse.Namespace) -> int:
    """Handle the compress subcommand."""
    input_path = args.input
    output_path = args.output

    if not os.path.exists(input_path):
        print(f"Error: Input path '{input_path}' does not exist.", file=sys.stderr)
        return 1

    try:
        if os.path.isdir(input_path):
            if output_path is None:
                output_path = input_path.rstrip("/\\") + ".huffz"
            print(f"Compressing directory tree '{input_path}' -> '{output_path}'...")
            stats = compress_batch([input_path], output_path)
        else:
            if output_path is None:
                output_path = input_path + ".huff"
            print(f"Compressing file '{input_path}' -> '{output_path}'...")
            _, stats = compress_file(input_path, output_path)

        print(format_report(stats))
        return 0

    except EmptyFileError as e:
        print(f"Error (REQ-4): {e}", file=sys.stderr)
        return 2
    except CompressionError as e:
        print(f"Compression Failure: {e}", file=sys.stderr)
        return 3
    except Exception as e:
        print(f"Unexpected Error: {e}", file=sys.stderr)
        return 4


def handle_decompress(args: argparse.Namespace) -> int:
    """Handle the decompress subcommand."""
    input_path = args.input
    output_path = args.output
    overwrite = args.force

    if not os.path.exists(input_path):
        print(f"Error: Archive '{input_path}' does not exist.", file=sys.stderr)
        return 1

    try:
        # Check if it's a batch archive (.huffz) or single file (.huff)
        with open(input_path, "rb") as f:
            header_sample = f.read(16)

        if b"HUFZ" in header_sample:
            dest_dir = output_path if output_path else "extracted_archive"
            print(f"Decompressing batch archive '{input_path}' -> '{dest_dir}'...")
            stats = decompress_batch(input_path, dest_dir, overwrite=overwrite)
            print(f"\nExtraction completed successfully!")
            print(f"  Archive: {stats['archive_path']}")
            print(f"  Output Directory: {stats['output_directory']}")
            print(f"  Files Restored: {stats['files_extracted']}")
            print(f"  Integrity: PASSED (All files matched CRC32)")
            print(f"  Time: {stats['duration_seconds']:.4f}s\n")
        else:
            print(f"Decompressing file '{input_path}'...")
            _, stats = decompress_file(input_path, output_path, overwrite=overwrite)
            print(format_report(stats))

        return 0

    except CorruptedFileError as e:
        print(f"Integrity Error (REQ-7): {e}", file=sys.stderr)
        return 5
    except FileExistsError as e:
        print(f"Safety Warning (NFR-6.2): {e}\nUse -f/--force to overwrite.", file=sys.stderr)
        return 6
    except Exception as e:
        print(f"Decompression Failure: {e}", file=sys.stderr)
        return 7


def handle_info(args: argparse.Namespace) -> int:
    """Handle the info subcommand to inspect archive details."""
    archive_path = args.archive
    if not os.path.exists(archive_path):
        print(f"Error: Archive '{archive_path}' does not exist.", file=sys.stderr)
        return 1

    try:
        info = inspect_archive(archive_path)
        print("\n============================================================")
        print(f"              ARCHIVE MANIFEST: {os.path.basename(archive_path)}")
        print("============================================================")
        print(f"  Archive Path     : {info['archive_path']}")
        print(f"  Archive Size     : {format_bytes(info['archive_size'])}")
        print(f"  Contained Files  : {info['file_count']}")
        print(f"  Uncompressed Size: {format_bytes(info['uncompressed_size'])}")
        ratio = (
            (1.0 - (info['archive_size'] / info['uncompressed_size'])) * 100.0
            if info['uncompressed_size'] > 0
            else 0.0
        )
        print(f"  Overall Ratio    : {ratio:+.2f}%")
        print("------------------------------------------------------------")
        print("  Files:")
        for idx, f in enumerate(info["files"], 1):
            print(f"    {idx:02d}. {f['path']} ({format_bytes(f['size'])}, CRC: 0x{f['crc32']})")
        print("============================================================\n")
        return 0
    except CorruptedFileError as e:
        print(f"Error reading archive info: {e}", file=sys.stderr)
        return 1


def handle_benchmark(args: argparse.Namespace) -> int:
    """Benchmark compression and decompression on a target file."""
    input_path = args.input
    if not os.path.exists(input_path):
        print(f"Error: Target file '{input_path}' does not exist.", file=sys.stderr)
        return 1

    temp_compressed = input_path + ".bench.huff"
    temp_restored = input_path + ".bench.restored"

    try:
        print(f"Benchmarking Huffman Compression Engine on: '{input_path}'...")
        file_size = os.path.getsize(input_path)
        print(f"Input File Size: {format_bytes(file_size)} ({file_size:,} bytes)")

        # 1. Compress
        t0 = time.perf_counter()
        _, comp_stats = compress_file(input_path, temp_compressed)
        t_comp = time.perf_counter() - t0

        # 2. Decompress
        t1 = time.perf_counter()
        _, decomp_stats = decompress_file(temp_compressed, temp_restored, overwrite=True)
        t_decomp = time.perf_counter() - t1

        # 3. Verify Lossless Equality
        with open(input_path, "rb") as f1, open(temp_restored, "rb") as f2:
            exact_match = (f1.read() == f2.read())

        print("\n============================================================")
        print("                 BENCHMARK PERFORMANCE RESULTS")
        print("============================================================")
        print(f"  Original Size      : {format_bytes(file_size)}")
        print(f"  Compressed Size    : {format_bytes(comp_stats['compressed_size'])}")
        print(f"  Compression Ratio  : {comp_stats['ratio_percent']:+.2f}%")
        print(f"  Space Saved        : {format_bytes(comp_stats['space_saved_bytes'])}")
        print("------------------------------------------------------------")
        print(f"  Compression Time   : {t_comp:.4f} s ({(file_size/1024/1024)/t_comp:.2f} MB/s)")
        print(f"  Decompression Time : {t_decomp:.4f} s ({(file_size/1024/1024)/t_decomp:.2f} MB/s)")
        print(f"  Total Roundtrip    : {t_comp + t_decomp:.4f} s")
        print(f"  Byte-for-Byte Match: {'PASS (100% Lossless)' if exact_match else 'FAIL'}")
        
        # Check against NFR-6.1 performance requirement
        is_under_5s = (t_comp + t_decomp) < 5.0
        print(f"  REQ-6.1 Compliance : {'PASS (< 5s SLA)' if is_under_5s else 'WARNING (> 5s)'}")
        print("============================================================\n")
        return 0

    finally:
        if os.path.exists(temp_compressed):
            os.remove(temp_compressed)
        if os.path.exists(temp_restored):
            os.remove(temp_restored)


def main(argv: list[str] | None = None) -> int:
    """Main entry point for the command-line tool."""
    parser = argparse.ArgumentParser(
        prog="huffzip",
        description="Lossless File & Directory Compression Tool using Huffman Coding (Project ID 76)",
    )
    parser.add_argument("--gui", action="store_true", help="Launch the Graphical User Interface (GUI)")

    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Compress subcommand
    comp_parser = subparsers.add_parser("compress", aliases=["c"], help="Compress a file or directory")
    comp_parser.add_argument("input", help="Path to input file or directory")
    comp_parser.add_argument("-o", "--output", help="Destination path for compressed archive")
    comp_parser.set_defaults(func=handle_compress)

    # Decompress subcommand
    decomp_parser = subparsers.add_parser("decompress", aliases=["d", "x"], help="Decompress a .huff or .huffz archive")
    decomp_parser.add_argument("input", help="Path to .huff or .huffz archive")
    decomp_parser.add_argument("-o", "--output", help="Destination file or output directory")
    decomp_parser.add_argument("-f", "--force", action="store_true", help="Overwrite existing files (NFR-6.2)")
    decomp_parser.set_defaults(func=handle_decompress)

    # Info subcommand
    info_parser = subparsers.add_parser("info", aliases=["i"], help="Display metadata of a .huffz archive")
    info_parser.add_argument("archive", help="Path to .huffz archive")
    info_parser.set_defaults(func=handle_info)

    # Benchmark subcommand
    bench_parser = subparsers.add_parser("benchmark", aliases=["b"], help="Benchmark compression and decompression speed")
    bench_parser.add_argument("input", help="Path to input file to benchmark")
    bench_parser.set_defaults(func=handle_benchmark)

    args = parser.parse_args(argv)

    if args.gui or args.command is None:
        try:
            from src.gui import launch_gui
            launch_gui()
            return 0
        except ImportError as e:
            if args.gui:
                print(f"Error launching GUI: {e}", file=sys.stderr)
                return 1
            parser.print_help()
            return 0

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
