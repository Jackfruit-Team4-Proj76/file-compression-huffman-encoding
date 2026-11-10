"""Huffman compression core. Imported from the existing SE mini-project."""

from src.huffman import (
    HuffmanNode,
    build_frequency_table,
    build_huffman_tree,
    generate_huffman_codes,
)
from src.compress import compress_bytes, compress_file, EmptyFileError, CompressionError
from src.decompress import (
    decompress_bytes,
    decompress_file,
    DecompressionError,
    CorruptedFileError,
)

__all__ = [
    "HuffmanNode", "build_frequency_table", "build_huffman_tree",
    "generate_huffman_codes", "compress_bytes", "compress_file",
    "EmptyFileError", "CompressionError",
    "decompress_bytes", "decompress_file", "DecompressionError", "CorruptedFileError",
]
