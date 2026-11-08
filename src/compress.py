"""
Huffman Compression Engine
==========================
Functional Feature Owned By: K C Nandan (PES2UG24AM072)

Implements:
- REQ-3: Generate compressed output file whose size is smaller for non-trivial inputs.
- REQ-4: Reject empty files with a clear, descriptive error message rather than crashing.
- Custom binary format (.huff) with embedded frequency table, CRC32, and metadata.
- Optimized bit-packing engine supporting all arbitrary binary and text formats.
"""

from __future__ import annotations
import os
import struct
import time
import zlib
from typing import Optional, Tuple, Dict, Any

from src.huffman import (
    build_frequency_table,
    build_huffman_tree,
    generate_huffman_codes,
)


# Magic identifier for single-file Huffman archive: 'H', 'U', 'F', 'F', version 1
MAGIC_HEADER = b"HUFF\x01"


class CompressionError(Exception):
    """Base exception for compression failures."""
    pass


class EmptyFileError(CompressionError):
    """Raised when an empty (0 byte) file is passed for compression (REQ-4)."""
    pass


class FileAccessError(CompressionError):
    """Raised when input or output file paths cannot be accessed."""
    pass


def encode_bitstream(data: bytes, codes: Dict[int, str]) -> Tuple[bytes, int]:
    """
    Encode raw bytes into a packed bitstream using precomputed Huffman codes.

    Args:
        data: Input bytes to encode.
        codes: Dict mapping byte values (0-255) to bitstrings (e.g. '011').

    Returns:
        Tuple of (packed_bytes, padding_bits_count).
    """
    if not data:
        return b"", 0

    code_map = {b: codes[b] for b in codes}
    bit_str = "".join(code_map[b] for b in data)

    padding = (8 - (len(bit_str) % 8)) % 8
    if padding > 0:
        bit_str += "0" * padding

    # Convert bit_str into bytes in 64K-bit chunks
    CHUNK_SIZE = 65536  # 64K bits = 8KB bytes, multiple of 8
    output_parts = []
    for i in range(0, len(bit_str), CHUNK_SIZE):
        chunk = bit_str[i : i + CHUNK_SIZE]
        num_bytes = len(chunk) // 8
        n = int(chunk, 2)
        output_parts.append(n.to_bytes(num_bytes, byteorder="big"))

    return b"".join(output_parts), padding


def compress_bytes(data: bytes, original_name: str = "") -> bytes:
    """
    Compress raw bytes into the .huff binary format.

    Header Layout:
    - 5 bytes: Magic Header (b'HUFF\\x01')
    - 2 bytes: Original file name length (>H)
    - N bytes: Original file name (UTF-8 encoded)
    - 8 bytes: Original uncompressed size in bytes (>Q)
    - 4 bytes: CRC32 checksum of original bytes (>I)
    - 2 bytes: Frequency table distinct entries count (>H, 1-256)
    - For each distinct byte:
        - 1 byte: byte value (B)
        - 8 bytes: frequency count (>Q)
    - 1 byte: Padding bit count (B, 0-7)
    - Remaining bytes: Packed Huffman bitstream

    Args:
        data: Raw uncompressed bytes.
        original_name: Optional original file name to preserve.

    Returns:
        Complete compressed binary bytes.

    Raises:
        EmptyFileError: If input data is empty (0 bytes) (REQ-4).
    """
    if not data or len(data) == 0:
        raise EmptyFileError(
            "Input data is empty (0 bytes). Huffman compression requires at least one byte of data."
        )

    # 1. Frequency Table & Huffman Tree
    freq_table = build_frequency_table(data)
    tree_root = build_huffman_tree(freq_table)
    codes = generate_huffman_codes(tree_root)

    # 2. Checksum & Size
    original_size = len(data)
    checksum = zlib.crc32(data) & 0xFFFFFFFF

    # 3. Encode Bitstream
    bitstream, padding = encode_bitstream(data, codes)

    # 4. Construct Binary Header
    name_bytes = original_name.encode("utf-8")
    header_parts = [
        MAGIC_HEADER,
        struct.pack(">H", len(name_bytes)),
        name_bytes,
        struct.pack(">Q", original_size),
        struct.pack(">I", checksum),
        struct.pack(">H", len(freq_table)),
    ]

    for byte_val in sorted(freq_table.keys()):
        header_parts.append(struct.pack(">BQ", byte_val, freq_table[byte_val]))

    header_parts.append(struct.pack(">B", padding))

    return b"".join(header_parts) + bitstream


def compress_file(
    input_path: str,
    output_path: Optional[str] = None,
) -> Tuple[str, Dict[str, Any]]:
    """
    Compress an individual file using Huffman coding.

    Args:
        input_path: Path to the uncompressed input file.
        output_path: Optional destination path. Defaults to '<input_path>.huff'.

    Returns:
        Tuple of (output_file_path, stats_dict).

    Raises:
        EmptyFileError: If the input file is 0 bytes (REQ-4).
        FileAccessError: If the input file does not exist or cannot be read.
    """
    if not os.path.exists(input_path):
        raise FileAccessError(f"Input file not found: '{input_path}'")

    if not os.path.isfile(input_path):
        raise FileAccessError(f"Input path is not a regular file: '{input_path}'")

    file_size = os.path.getsize(input_path)
    if file_size == 0:
        raise EmptyFileError(
            f"Input file '{input_path}' is empty (0 bytes). Compression rejected per REQ-4."
        )

    if output_path is None:
        output_path = input_path + ".huff"

    # Safety: Avoid self-overwrite (NFR-6.2)
    if os.path.abspath(input_path) == os.path.abspath(output_path):
        raise FileAccessError("Output path cannot be identical to the input path.")

    # Read data and track performance
    start_time = time.perf_counter()
    with open(input_path, "rb") as f:
        raw_data = f.read()

    file_basename = os.path.basename(input_path)
    compressed_bytes = compress_bytes(raw_data, original_name=file_basename)

    # Ensure parent output directory exists
    parent_dir = os.path.dirname(output_path)
    if parent_dir and not os.path.exists(parent_dir):
        os.makedirs(parent_dir, exist_ok=True)

    with open(output_path, "wb") as f:
        f.write(compressed_bytes)

    duration = time.perf_counter() - start_time
    compressed_size = len(compressed_bytes)

    # Calculate compression ratio: (1 - compressed_size / original_size) * 100
    ratio = (1.0 - (compressed_size / file_size)) * 100.0 if file_size > 0 else 0.0

    stats = {
        "operation": "compress",
        "input_path": input_path,
        "output_path": output_path,
        "original_size": file_size,
        "compressed_size": compressed_size,
        "ratio_percent": round(ratio, 2),
        "space_saved_bytes": file_size - compressed_size,
        "duration_seconds": round(duration, 4),
        "crc32": f"{zlib.crc32(raw_data) & 0xFFFFFFFF:08X}",
    }

    return output_path, stats
