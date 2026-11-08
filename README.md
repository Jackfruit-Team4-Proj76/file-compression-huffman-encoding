# Huffman File Compression Tool

Software Engineering Mini-Project - Project ID 76.

## Current scope

This first component contains byte frequency counting, min-heap Huffman tree
construction, prefix-code generation, single-file compression, and unit tests.
It writes custom `.huff` archives; these are not standard ZIP files.
Some inputs, especially already compressed files, become larger because of
archive metadata. Decompression, folder archiving, reporting, CLI, and GUI are
not included in this stage.

## Run locally

Requires Python 3.10 or newer. Runtime uses only the Python standard library.

```powershell
python -m unittest discover -s tests -v
python -c "from src.compress import compress_file; print(compress_file('sample.txt'))"
```

The compression command requires an existing, nonempty `sample.txt` and creates
`sample.txt.huff`. Do not use an existing important file as the output path.

## Planned component integration

| Integration order | Component coordinator | Scope |
| --- | --- | --- |
| 1 | Jashruth K A | Huffman core and compression |
| 2 | Chiranth D Nandi | Decompression and integrity validation |
| 3 | Aishwarya A | Multi-file and folder archiving |
| 4 | K C Nandan | Reporting, CLI, GUI, and final integration |

These are integration responsibilities, not evidence of original authorship.

## Source and provenance

The core implementation and tests in this initial import are reused from the
existing `se-mini-project` workspace. Original source ownership comments and the
MIT license are retained. This repository's initial commit records the import
and standalone package setup, not newly implemented work by four contributors.
Future implementation, fixes, reviews, and test results should be recorded as
actual work using each contributor's own account.
