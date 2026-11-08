"""
Unit Tests: Huffman Tree & Prefix Code Engine
=============================================
Test Case IDs: UT-01, UT-02, UT-03, UT-04
Feature Owner: K C Nandan (PES2UG24AM072)
"""

import unittest
from src.huffman import (
    HuffmanNode,
    build_frequency_table,
    build_huffman_tree,
    generate_huffman_codes,
)


class TestHuffmanModule(unittest.TestCase):
    """Test suite for HuffmanNode, tree construction, and prefix code generation."""

    def test_ut02_frequency_table_normal(self) -> None:
        """UT-02: Verify character frequency table construction from bytes."""
        data = b"abracadabra"
        table = build_frequency_table(data)

        self.assertEqual(table[ord("a")], 5)
        self.assertEqual(table[ord("b")], 2)
        self.assertEqual(table[ord("r")], 2)
        self.assertEqual(table[ord("c")], 1)
        self.assertEqual(table[ord("d")], 1)
        self.assertEqual(sum(table.values()), len(data))

    def test_ut02_frequency_table_empty(self) -> None:
        """UT-02: Frequency table for empty byte sequence should be empty dict."""
        self.assertEqual(build_frequency_table(b""), {})

    def test_ut03_huffman_node_comparison(self) -> None:
        """UT-03: HuffmanNode comparison in min-heap based on frequency."""
        n1 = HuffmanNode(byte_val=ord("A"), freq=10)
        n2 = HuffmanNode(byte_val=ord("B"), freq=20)
        self.assertTrue(n1 < n2)
        self.assertFalse(n2 < n1)

        # Equal frequency tie-breaking by byte value
        n3 = HuffmanNode(byte_val=ord("A"), freq=10)
        n4 = HuffmanNode(byte_val=ord("C"), freq=10)
        self.assertTrue(n3 < n4)

    def test_ut03_tree_construction_and_prefix_property(self) -> None:
        """UT-03: Verify tree construction and mathematical prefix-free property."""
        sample_text = b"software engineering mini project file compression tool 2026"
        table = build_frequency_table(sample_text)
        root = build_huffman_tree(table)

        self.assertIsNotNone(root)
        self.assertEqual(root.freq, len(sample_text))

        codes = generate_huffman_codes(root)
        self.assertEqual(len(codes), len(table))

        # Mathematical verification: Prefix Property
        # No valid Huffman code may be a prefix of another Huffman code
        all_codes = list(codes.values())
        for i, code1 in enumerate(all_codes):
            for j, code2 in enumerate(all_codes):
                if i != j:
                    self.assertFalse(
                        code1.startswith(code2),
                        f"Prefix property violation: '{code2}' is a prefix of '{code1}'",
                    )

        # Verify optimality: more frequent characters should have shorter or equal code length
        sorted_symbols = sorted(table.keys(), key=lambda k: table[k], reverse=True)
        most_frequent = sorted_symbols[0]
        least_frequent = sorted_symbols[-1]
        self.assertLessEqual(len(codes[most_frequent]), len(codes[least_frequent]))

    def test_ut04_single_character_tree(self) -> None:
        """UT-04: Boundary condition: input consisting of a single distinct character."""
        data = b"AAAAAAAAAA"  # 10 'A's
        table = build_frequency_table(data)
        self.assertEqual(len(table), 1)

        root = build_huffman_tree(table)
        self.assertIsNotNone(root)

        codes = generate_huffman_codes(root)
        self.assertIn(ord("A"), codes)
        self.assertEqual(codes[ord("A")], "0")


if __name__ == "__main__":
    unittest.main()
