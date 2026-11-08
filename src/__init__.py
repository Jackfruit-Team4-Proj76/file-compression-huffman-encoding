"""Huffman compression core. Imported from the existing SE mini-project."""

from src.huffman import (
    HuffmanNode,
    build_frequency_table,
    build_huffman_tree,
    generate_huffman_codes,
)
from src.compress import compress_bytes, compress_file, EmptyFileError, CompressionError

__all__ = [
    "HuffmanNode", "build_frequency_table", "build_huffman_tree",
    "generate_huffman_codes", "compress_bytes", "compress_file",
    "EmptyFileError", "CompressionError",
]
