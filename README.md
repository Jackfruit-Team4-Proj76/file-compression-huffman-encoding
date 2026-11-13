# Huffman File Compression Tool

Software Engineering Mini-Project — Project ID 76 (Jackfruit-Team4).

## Current Scope

This project implements a complete, lossless file and directory compression toolkit using Huffman coding.
Current capabilities:
- **Core Algorithm:** Character and byte frequency counting, min-heap Huffman tree construction, and variable-length prefix code generation (REQ-1 to REQ-4).
- **Single-File Compression:** Compression into custom `.huff` binary archives storing magic bytes, uncompressed length, frequency table header, padding bits, and CRC32 checksum.
- **Lossless Decompression:** Bitstream decoding reconstructing original files byte-for-byte (REQ-5, REQ-6).
- **Integrity Validation:** Checksum-based integrity verification using CRC32 to detect file corruption or bit tampering (REQ-7).
- **Safety Guards:** Accidental file overwrite prevention (NFR-6.2) requiring explicit `-f/--force` flags.
- **Folder & Batch Archiving:** Multi-file and directory recursive archiving into `.huffz` archive containers preserving relative directory hierarchies (REQ-8, REQ-9).
- **Analytics & Reporting:** Comprehensive compression metrics reporting (ratio %, factor, space saved, processing duration, throughput speed in MB/s) and ASCII summary layouts (REQ-10).
- **Command-Line Interface (CLI):** Full CLI (`huffzip`) featuring subcommands for `compress`, `decompress`, `info`, and `benchmark` (IT-04).
- **Desktop Graphical User Interface (GUI):** Responsive desktop Tkinter interface with four tabs: Single File Compression, File Decompression, Batch / Directory Archiving, and Live Statistics & Archive Inspector.
- **Packaging & CI/CD:** PEP 517/621 packaging (`pyproject.toml`, `setup.py`) and automated GitHub Actions CI testing on Python 3.12 with branch coverage reporting.
- **Verification:** Comprehensive unit and integration test suite (44 tests passing, 86% branch coverage).

## Run Locally

Requires Python 3.10 or newer. Runtime uses only the Python standard library.

```bash
# Run the test suite (44 unit & integration tests)
python -m unittest discover -s tests -v

# Run tests with branch coverage reporting
python -m coverage run --branch -m unittest discover -s tests -v
python -m coverage report -m

# Launch the Graphical User Interface (GUI)
python -m src.gui

# CLI usage examples
python -m src.cli --help
python -m src.cli compress sample.txt -o sample.txt.huff
python -m src.cli decompress sample.txt.huff -o restored.txt --force
python -m src.cli compress my_folder/ -o my_folder.huffz
python -m src.cli info my_folder.huffz
python -m src.cli benchmark sample.txt
```

## Planned Component Integration

| Integration Order | Component Coordinator | Scope | Status |
|:---:|---|---|:---:|
| 1 | Jashruth K A | Huffman core and compression | Merged |
| 2 | Chiranth D Nandi | Decompression and integrity validation | Completed (18 tests pass) |
| 3 | Aishwarya A | Multi-file and folder archiving | Completed (21 tests pass) |
| 4 | K C Nandan | Reporting, CLI, GUI, packaging & CI integration | Completed (44 tests pass, 86% coverage) |

## Source and Provenance

The core implementation and tests in this project are developed in staged integration milestones. Original source ownership comments and the MIT license are retained. Each contributor records their respective functional features, fixes, reviews, and test verification on their assigned commits and tickets.
