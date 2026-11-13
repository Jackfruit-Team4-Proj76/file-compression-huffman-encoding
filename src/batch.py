"""
Multi-file & Directory Batch Archiving Engine
=============================================
Functional Feature Owned By: Jashruth K A (PES2UG24AM069)

Implements:
- REQ-8: Accept a folder or list of files and compress all contained items in one operation.
- REQ-9: Preserve relative directory structure when decompressing a batch archive.
- Archive inspection tool to examine contents and metadata without extracting.
"""

from __future__ import annotations
import os
import struct
import time
import zlib
from typing import List, Tuple, Dict, Any, Optional

from src.compress import (
    compress_bytes,
    EmptyFileError,
    CompressionError,
)
from src.decompress import (
    decompress_bytes,
    CorruptedFileError,
    DecompressionError,
)

# Magic header for multi-file Huffman archives: 'H', 'U', 'F', 'Z', version 1
BATCH_MAGIC_HEADER = b"HUFZ\x01"


def collect_files(target_paths: List[str]) -> List[Tuple[str, str]]:
    """
    Scan files and directories, returning list of (absolute_path, relative_archive_path).

    Args:
        target_paths: List of file or folder paths.

    Returns:
        List of tuples: (abs_path, normalized_relative_path).
    """
    collected: List[Tuple[str, str]] = []

    for path in target_paths:
        abs_p = os.path.abspath(path)
        if not os.path.exists(abs_p):
            raise FileNotFoundError(f"Path does not exist: '{path}'")

        if os.path.isfile(abs_p):
            collected.append((abs_p, os.path.basename(abs_p)))
        elif os.path.isdir(abs_p):
            base_dir_name = os.path.basename(abs_p) or "root"
            for root, _, files in os.walk(abs_p):
                for f in sorted(files):
                    file_abs = os.path.join(root, f)
                    rel_from_root = os.path.relpath(file_abs, abs_p)
                    # Normalize to forward slashes for cross-platform portability
                    archive_rel = f"{base_dir_name}/{rel_from_root}".replace("\\", "/")
                    collected.append((file_abs, archive_rel))

    return collected


def compress_batch(
    paths: List[str],
    output_archive_path: str,
) -> Dict[str, Any]:
    """
    Compress multiple files or entire folder trees into a single .huffz archive (REQ-8).

    Format Specification:
    - 5 bytes: BATCH_MAGIC_HEADER (b'HUFZ\\x01')
    - 4 bytes: Number of files in manifest (>I)
    - For each file:
        - 2 bytes: relative path string length (>H)
        - N bytes: relative path string (UTF-8)
        - 8 bytes: uncompressed size in bytes (>Q)
        - 4 bytes: CRC32 checksum (>I)
    - Remaining bytes: Huffman-compressed payload containing all concatenated files

    Args:
        paths: List of file and/or directory paths to include.
        output_archive_path: Destination path for the .huffz archive.

    Returns:
        Summary dict containing compression statistics.

    Raises:
        EmptyFileError: If all selected files are 0 bytes or no files exist.
        CompressionError: If archiving fails.
    """
    start_time = time.perf_counter()
    file_list = collect_files(paths)

    if not file_list:
        raise EmptyFileError("No files found to compress.")

    manifest_entries: List[Tuple[str, int, int]] = []
    payload_parts: List[bytes] = []
    total_uncompressed_size = 0

    for file_abs, rel_path in file_list:
        with open(file_abs, "rb") as f:
            content = f.read()

        size = len(content)
        crc = zlib.crc32(content) & 0xFFFFFFFF
        manifest_entries.append((rel_path, size, crc))
        payload_parts.append(content)
        total_uncompressed_size += size

    concatenated_data = b"".join(payload_parts)
    if len(concatenated_data) == 0:
        raise EmptyFileError("All files in batch are empty (0 bytes). Batch compression rejected (REQ-4).")

    # Serialize manifest
    manifest_bytes = bytearray()
    manifest_bytes.extend(BATCH_MAGIC_HEADER)
    manifest_bytes.extend(struct.pack(">I", len(manifest_entries)))

    for rel_path, size, crc in manifest_entries:
        path_encoded = rel_path.encode("utf-8")
        manifest_bytes.extend(struct.pack(">H", len(path_encoded)))
        manifest_bytes.extend(path_encoded)
        manifest_bytes.extend(struct.pack(">QI", size, crc))

    # Compress the payload using Huffman engine
    compressed_payload = compress_bytes(concatenated_data, original_name="batch_payload")

    # Final archive: Manifest length prefix + Manifest + Compressed payload
    manifest_raw = bytes(manifest_bytes)
    archive_data = struct.pack(">I", len(manifest_raw)) + manifest_raw + compressed_payload

    parent_dir = os.path.dirname(output_archive_path)
    if parent_dir and not os.path.exists(parent_dir):
        os.makedirs(parent_dir, exist_ok=True)

    with open(output_archive_path, "wb") as f:
        f.write(archive_data)

    duration = time.perf_counter() - start_time
    total_compressed_size = len(archive_data)
    ratio = (
        (1.0 - (total_compressed_size / total_uncompressed_size)) * 100.0
        if total_uncompressed_size > 0
        else 0.0
    )

    return {
        "operation": "batch_compress",
        "output_path": output_archive_path,
        "file_count": len(manifest_entries),
        "files": [entry[0] for entry in manifest_entries],
        "original_size": total_uncompressed_size,
        "compressed_size": total_compressed_size,
        "ratio_percent": round(ratio, 2),
        "space_saved_bytes": total_uncompressed_size - total_compressed_size,
        "duration_seconds": round(duration, 4),
    }


def inspect_archive(archive_path: str) -> Dict[str, Any]:
    """
    Read archive manifest metadata without decompressing the payload.

    Args:
        archive_path: Path to .huffz archive.

    Returns:
        Dict of archive details, entries list, sizes, and file count.
    """
    if not os.path.exists(archive_path):
        raise FileNotFoundError(f"Archive file not found: '{archive_path}'")

    with open(archive_path, "rb") as f:
        len_prefix = f.read(4)
        if len(len_prefix) < 4:
            raise CorruptedFileError("File is too small to be a batch archive (REQ-7).")

        (manifest_len,) = struct.unpack(">I", len_prefix)
        manifest_data = f.read(manifest_len)

    if not manifest_data.startswith(BATCH_MAGIC_HEADER):
        raise CorruptedFileError("Invalid archive signature: not a valid .huffz archive (REQ-7).")

    offset = len(BATCH_MAGIC_HEADER)
    (num_files,) = struct.unpack_from(">I", manifest_data, offset)
    offset += 4

    files_info = []
    total_uncompressed = 0
    for _ in range(num_files):
        (p_len,) = struct.unpack_from(">H", manifest_data, offset)
        offset += 2
        path_str = manifest_data[offset : offset + p_len].decode("utf-8", errors="replace")
        offset += p_len
        size, crc = struct.unpack_from(">QI", manifest_data, offset)
        offset += 12
        files_info.append({
            "path": path_str,
            "size": size,
            "crc32": f"{crc:08X}",
        })
        total_uncompressed += size

    total_archive_size = os.path.getsize(archive_path)

    return {
        "archive_path": archive_path,
        "file_count": num_files,
        "uncompressed_size": total_uncompressed,
        "archive_size": total_archive_size,
        "files": files_info,
    }


def decompress_batch(
    archive_path: str,
    output_dir: str,
    overwrite: bool = False,
) -> Dict[str, Any]:
    """
    Decompress a .huffz archive and restore relative folder hierarchy (REQ-8, REQ-9).

    Args:
        archive_path: Path to the .huffz archive file.
        output_dir: Base directory where files will be unpacked.
        overwrite: Whether to overwrite existing files (NFR-6.2).

    Returns:
        Summary dict of unpacked files and verification status.

    Raises:
        CorruptedFileError: If manifest or CRC32 validation fails.
    """
    start_time = time.perf_counter()
    if not os.path.exists(archive_path):
        raise FileNotFoundError(f"Archive not found: '{archive_path}'")

    with open(archive_path, "rb") as f:
        len_prefix = f.read(4)
        if len(len_prefix) < 4:
            raise CorruptedFileError("Invalid batch archive header: missing manifest length (REQ-7).")
        (manifest_len,) = struct.unpack(">I", len_prefix)
        manifest_data = f.read(manifest_len)
        payload_data = f.read()

    if not manifest_data.startswith(BATCH_MAGIC_HEADER):
        raise CorruptedFileError("Invalid archive signature: not a valid .huffz archive (REQ-7).")

    offset = len(BATCH_MAGIC_HEADER)
    (num_files,) = struct.unpack_from(">I", manifest_data, offset)
    offset += 4

    manifest: List[Tuple[str, int, int]] = []
    for _ in range(num_files):
        (p_len,) = struct.unpack_from(">H", manifest_data, offset)
        offset += 2
        path_str = manifest_data[offset : offset + p_len].decode("utf-8", errors="replace")
        offset += p_len
        size, crc = struct.unpack_from(">QI", manifest_data, offset)
        offset += 12
        manifest.append((path_str, size, crc))

    # Decompress payload
    raw_payload, _ = decompress_bytes(payload_data)

    # Extract individual files and recreate directories
    extracted_paths: List[str] = []
    payload_offset = 0

    os.makedirs(output_dir, exist_ok=True)

    for rel_path, size, expected_crc in manifest:
        file_bytes = raw_payload[payload_offset : payload_offset + size]
        payload_offset += size

        # Verify integrity (REQ-7)
        actual_crc = zlib.crc32(file_bytes) & 0xFFFFFFFF
        if actual_crc != expected_crc:
            raise CorruptedFileError(
                f"Integrity check failed for '{rel_path}'! "
                f"Expected CRC 0x{expected_crc:08X}, got 0x{actual_crc:08X}."
            )

        # Preserve relative directory structure (REQ-9)
        dest_path = os.path.join(output_dir, rel_path.replace("/", os.sep))
        parent = os.path.dirname(dest_path)
        if parent:
            os.makedirs(parent, exist_ok=True)

        if os.path.exists(dest_path) and not overwrite:
            raise FileExistsError(
                f"Target file already exists: '{dest_path}'. Pass overwrite=True to allow overwriting."
            )

        with open(dest_path, "wb") as out_f:
            out_f.write(file_bytes)

        extracted_paths.append(dest_path)

    duration = time.perf_counter() - start_time
    return {
        "operation": "batch_decompress",
        "archive_path": archive_path,
        "output_directory": output_dir,
        "files_extracted": len(extracted_paths),
        "files": extracted_paths,
        "duration_seconds": round(duration, 4),
        "integrity_verified": True,
    }
