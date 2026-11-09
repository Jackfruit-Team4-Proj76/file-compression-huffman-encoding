"""
Huffman Decompression Engine
============================
Functional Feature Owned By: Chiranth D Nandi (PES2UG24AM048)

Implements:
- REQ-5: Reconstruct Huffman tree from compressed file's stored header.
- REQ-6: Decode compressed bitstream to produce identical byte-for-byte output.
- REQ-7: Detect and report corrupted, truncated, or invalid compressed files.
"""

from __future__ import annotations
import os
import struct
import time
import zlib
from typing import Optional, Tuple, Dict, Any, List

from src.huffman import (
    HuffmanNode,
    build_huffman_tree,
    generate_huffman_codes,
)
from src.compress import MAGIC_HEADER


class DecompressionError(Exception):
    """Base exception for decompression errors."""
    pass


class CorruptedFileError(DecompressionError):
    """Raised when header, bitstream, or checksum validation fails (REQ-7)."""
    pass


BYTE_TO_BIN = [f"{b:08b}" for b in range(256)]


def _decode_bitstream_fast(
    bitstream: bytes,
    tree_root: HuffmanNode,
    expected_size: int,
    padding: int,
) -> bytes:
    """
    Decode bitstream into original byte content using the Huffman tree (REQ-6).
    """
    if expected_size == 0:
        return b""

    # Edge case: single distinct byte
    if tree_root.is_leaf:
        return bytes([tree_root.byte_val]) * expected_size  # type: ignore[list-item]

    if tree_root.left and tree_root.left.is_leaf and tree_root.right is None:
        return bytes([tree_root.left.byte_val]) * expected_size  # type: ignore[list-item]

    # Reconstruct code lookup from tree
    codes = generate_huffman_codes(tree_root)
    code_to_byte = {code_str: byte_val for byte_val, code_str in codes.items()}
    max_code_len = max(len(c) for c in codes.values())

    # Fast bitstream expansion
    full_bits = "".join(BYTE_TO_BIN[b] for b in bitstream)
    if padding > 0:
        full_bits = full_bits[:-padding]

    decoded = bytearray()
    curr_code = ""
    get_byte = code_to_byte.get
    append = decoded.append

    for bit_char in full_bits:
        curr_code += bit_char
        b_val = get_byte(curr_code)
        if b_val is not None:
            append(b_val)
            curr_code = ""
            if len(decoded) == expected_size:
                return bytes(decoded)
        elif len(curr_code) > max_code_len:
            raise CorruptedFileError(
                "Invalid bit sequence encountered during Huffman decoding (REQ-7)."
            )

    if len(decoded) != expected_size:
        raise CorruptedFileError(
            f"Bitstream terminated prematurely: decoded {len(decoded)} bytes, "
            f"expected {expected_size} bytes (REQ-7)."
        )

    return bytes(decoded)


def decompress_bytes(compressed_data: bytes) -> Tuple[bytes, str]:
    """
    Decompress a .huff byte sequence back to its exact original form.

    Args:
        compressed_data: The complete binary content of a .huff file.

    Returns:
        Tuple of (decompressed_bytes, original_filename).

    Raises:
        CorruptedFileError: If magic bytes, header layout, or CRC32 checksum fails (REQ-7).
    """
    if len(compressed_data) < len(MAGIC_HEADER):
        raise CorruptedFileError(
            "File is too short to be a valid .huff archive (REQ-7)."
        )

    # 1. Verify Magic Bytes
    if not compressed_data.startswith(MAGIC_HEADER):
        raise CorruptedFileError(
            f"Invalid file signature. Expected {MAGIC_HEADER!r}, found {compressed_data[:5]!r} (REQ-7)."
        )

    offset = len(MAGIC_HEADER)

    # 2. Extract Original Filename
    if len(compressed_data) < offset + 2:
        raise CorruptedFileError("Truncated header: missing filename length (REQ-7).")
    (name_len,) = struct.unpack_from(">H", compressed_data, offset)
    offset += 2

    if len(compressed_data) < offset + name_len:
        raise CorruptedFileError("Truncated header: incomplete filename string (REQ-7).")
    orig_name = compressed_data[offset : offset + name_len].decode("utf-8", errors="replace")
    offset += name_len

    # 3. Extract Metadata: Original Size and Checksum
    if len(compressed_data) < offset + 12:
        raise CorruptedFileError("Truncated header: missing file size or CRC32 (REQ-7).")
    original_size, expected_crc = struct.unpack_from(">QI", compressed_data, offset)
    offset += 12

    # 4. Extract Frequency Table (REQ-5)
    if len(compressed_data) < offset + 2:
        raise CorruptedFileError("Truncated header: missing frequency table length (REQ-7).")
    (freq_entries_count,) = struct.unpack_from(">H", compressed_data, offset)
    offset += 2

    freq_table: Dict[int, int] = {}
    for _ in range(freq_entries_count):
        if len(compressed_data) < offset + 9:
            raise CorruptedFileError("Truncated header: corrupted frequency table entry (REQ-7).")
        b_val, b_freq = struct.unpack_from(">BQ", compressed_data, offset)
        freq_table[b_val] = b_freq
        offset += 9

    # 5. Extract Padding Bits
    if len(compressed_data) < offset + 1:
        raise CorruptedFileError("Truncated header: missing padding bit count (REQ-7).")
    (padding,) = struct.unpack_from(">B", compressed_data, offset)
    offset += 1

    if padding > 7:
        raise CorruptedFileError(f"Corrupted padding value: {padding} (must be 0-7) (REQ-7).")

    # 6. Reconstruct Huffman Tree (REQ-5)
    tree_root = build_huffman_tree(freq_table)
    if tree_root is None:
        raise CorruptedFileError("Failed to reconstruct Huffman tree from header frequencies (REQ-5).")

    # 7. Decode Bitstream (REQ-6)
    bitstream = compressed_data[offset:]
    decompressed_bytes = _decode_bitstream_fast(bitstream, tree_root, original_size, padding)

    # 8. Verify Data Integrity via CRC32 Checksum (REQ-7)
    actual_crc = zlib.crc32(decompressed_bytes) & 0xFFFFFFFF
    if actual_crc != expected_crc:
        raise CorruptedFileError(
            f"CRC32 Checksum verification failed! Expected 0x{expected_crc:08X}, "
            f"computed 0x{actual_crc:08X}. Data is corrupted (REQ-7)."
        )

    return decompressed_bytes, orig_name
