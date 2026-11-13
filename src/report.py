"""
Compression Ratio Reporting & Analytics Engine
==============================================
Functional Feature Owned By: Aishwarya A (PES2UG24AM001)

Implements:
- REQ-10: Report original size, compressed size, and compression ratio.
- Calculation of space saved, duration, throughput (MB/s).
- Beautiful formatted ASCII reports for CLI and logging.
"""

from __future__ import annotations
from typing import Dict, Any, Union


def format_bytes(num_bytes: Union[int, float]) -> str:
    """
    Format byte count into human-readable representation (e.g. 1.25 MB).

    Args:
        num_bytes: Size in bytes.

    Returns:
        Formatted string with appropriate unit.
    """
    if num_bytes < 0:
        return f"-{format_bytes(-num_bytes)}"
    if num_bytes < 1024:
        return f"{num_bytes:.0f} B"
    elif num_bytes < 1024 * 1024:
        return f"{num_bytes / 1024:.2f} KB"
    elif num_bytes < 1024 * 1024 * 1024:
        return f"{num_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{num_bytes / (1024 * 1024 * 1024):.2f} GB"


def calculate_compression_metrics(
    original_size: int,
    compressed_size: int,
    duration_seconds: float = 0.0,
) -> Dict[str, Any]:
    """
    Calculate comprehensive compression metrics (REQ-10).

    Formula (per SRS Appendix A):
        Compression Ratio (%) = (1 - compressed_size / original_size) * 100

    Args:
        original_size: Uncompressed size in bytes.
        compressed_size: Compressed size in bytes.
        duration_seconds: Execution time in seconds.

    Returns:
        Dict of computed metrics.
    """
    if original_size <= 0:
        ratio = 0.0
        space_saved = 0
        factor = 1.0
    else:
        ratio = (1.0 - (compressed_size / original_size)) * 100.0
        space_saved = original_size - compressed_size
        factor = (original_size / compressed_size) if compressed_size > 0 else float("inf")

    throughput_mb_s = (
        (original_size / (1024 * 1024)) / duration_seconds
        if duration_seconds > 0
        else 0.0
    )

    return {
        "original_size_bytes": original_size,
        "compressed_size_bytes": compressed_size,
        "original_size_formatted": format_bytes(original_size),
        "compressed_size_formatted": format_bytes(compressed_size),
        "space_saved_bytes": space_saved,
        "space_saved_formatted": format_bytes(space_saved),
        "ratio_percent": round(ratio, 2),
        "compression_factor": round(factor, 2),
        "duration_seconds": round(duration_seconds, 4),
        "throughput_mb_s": round(throughput_mb_s, 2),
    }


def format_report(stats: Dict[str, Any]) -> str:
    """
    Generate a clean, structured ASCII report for CLI and console output.

    Args:
        stats: Dictionary containing compression or decompression statistics.

    Returns:
        Formatted multi-line report string.
    """
    op = stats.get("operation", "operation").upper()
    lines = [
        "",
        "============================================================",
        f"               HUFFMAN {op} REPORT",
        "============================================================",
    ]

    if "input_path" in stats:
        lines.append(f"  Input Source     : {stats['input_path']}")
    if "output_path" in stats:
        lines.append(f"  Output Artifact  : {stats['output_path']}")
    if "file_count" in stats:
        lines.append(f"  Files Processed  : {stats['file_count']}")

    lines.append("------------------------------------------------------------")

    if "original_size" in stats:
        orig = stats["original_size"]
        comp = stats.get("compressed_size", 0)
        lines.append(f"  Original Size    : {format_bytes(orig)} ({orig:,} bytes)")
        lines.append(f"  Compressed Size  : {format_bytes(comp)} ({comp:,} bytes)")

        ratio = stats.get("ratio_percent", 0.0)
        saved = stats.get("space_saved_bytes", orig - comp)
        lines.append(f"  Space Saved      : {format_bytes(saved)} ({saved:,} bytes)")
        lines.append(f"  Compression Ratio: {ratio:+.2f}%")

        if orig > 0 and comp > 0:
            lines.append(f"  Compression Factor: {orig / comp:.2f}x")

    elif "decompressed_size" in stats:
        decomp = stats["decompressed_size"]
        comp = stats.get("compressed_size", 0)
        lines.append(f"  Compressed Size  : {format_bytes(comp)} ({comp:,} bytes)")
        lines.append(f"  Restored Size    : {format_bytes(decomp)} ({decomp:,} bytes)")

    if "crc32" in stats:
        lines.append(f"  CRC32 Checksum   : 0x{stats['crc32']}")
    if "integrity_verified" in stats:
        status_str = "PASSED (Lossless Exact Match)" if stats["integrity_verified"] else "FAILED"
        lines.append(f"  Data Integrity   : {status_str}")

    if "duration_seconds" in stats:
        dur = stats["duration_seconds"]
        lines.append(f"  Processing Time  : {dur:.4f} seconds")
        orig_s = stats.get("original_size", stats.get("decompressed_size", 0))
        if dur > 0 and orig_s > 0:
            speed = (orig_s / (1024 * 1024)) / dur
            lines.append(f"  Throughput Speed : {speed:.2f} MB/s")

    lines.append("============================================================")
    lines.append("")
    return "\n".join(lines)
