# Huffman File Compression Tool

Software Engineering Mini-Project - Project ID 76.

## Current scope

This project implements lossless file compression and decompression using Huffman coding.
Current capabilities:
- Character and byte frequency counting
- Min-heap Huffman tree construction and prefix code generation
- Single-file compression into custom `.huff` archives with stored header metadata
- Lossless decompression reconstructing original files byte-for-byte (REQ-5, REQ-6)
- Checksum-based integrity verification using CRC32 to detect corrupted or tampered files (REQ-7)
- Protection against accidental overwrite (NFR-6.2)
- Comprehensive test suite covering core algorithms and edge cases (18 tests passing)

Folder archiving, ratio reporting, CLI, and GUI are scheduled for subsequent stages.

## Run locally

Requires Python 3.10 or newer. Runtime uses only the Python standard library.

```powershell
# Run the test suite (18 unit tests)
python -m unittest discover -s tests -v

# Example compression and decompression usage
python -c "from src.compress import compress_file; from src.decompress import decompress_file; arch, _ = compress_file('sample.txt'); print(decompress_file(arch))"
```

## Planned component integration

| Integration order | Component coordinator | Scope | Status |
| --- | --- | --- | --- |
| 1 | Jashruth K A | Huffman core and compression | Merged |
| 2 | Chiranth D Nandi | Decompression and integrity validation | Completed (18 tests pass) |
| 3 | Aishwarya A | Multi-file and folder archiving | Pending |
| 4 | K C Nandan | Reporting, CLI, GUI, and final integration | Pending |

## Source and provenance

The core implementation and tests in this initial import are reused from the
existing `se-mini-project` workspace. Original source ownership comments and the
MIT license are retained. Each contributor records their respective functional
features, fixes, reviews, and test verification on their assigned branches.
