"""
Huffman Tree & Prefix Code Engine
==================================
Functional Feature Owned By: K C Nandan (PES2UG24AM072)

Implements:
- REQ-1: Frequency table generation from input byte data.
- REQ-2: Huffman tree construction using a min-heap priority queue.
- Prefix-code generation with deterministic canonical-like tie breaking.
- Edge case handling for single-character payloads.
"""

from __future__ import annotations
import heapq
from collections import Counter
from typing import Optional, Dict


class HuffmanNode:
    """
    Node in the Huffman coding tree.

    Attributes:
        byte_val: Integer byte value (0-255), or None for internal nodes.
        freq: Frequency count of the byte(s).
        left: Left child (representing bit '0').
        right: Right child (representing bit '1').
        order: Monotonic sequence ID used for deterministic tie-breaking in heap.
    """

    _sequence_counter: int = 0

    def __init__(
        self,
        byte_val: Optional[int] = None,
        freq: int = 0,
        left: Optional[HuffmanNode] = None,
        right: Optional[HuffmanNode] = None,
    ) -> None:
        self.byte_val = byte_val
        self.freq = freq
        self.left = left
        self.right = right
        HuffmanNode._sequence_counter += 1
        self.order = HuffmanNode._sequence_counter

    @property
    def is_leaf(self) -> bool:
        """Return True if this node is a leaf (contains a byte value)."""
        return self.left is None and self.right is None

    def __lt__(self, other: HuffmanNode) -> bool:
        """
        Compare nodes for min-heap ordering.
        First compares frequency. If equal, compares lowest byte value,
        then sequence counter for fully deterministic ordering.
        """
        if not isinstance(other, HuffmanNode):
            return NotImplemented
        if self.freq != other.freq:
            return self.freq < other.freq
        
        # Tie-break by byte value if available
        s_byte = self.byte_val if self.byte_val is not None else 256
        o_byte = other.byte_val if other.byte_val is not None else 256
        if s_byte != o_byte:
            return s_byte < o_byte

        return self.order < other.order

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, HuffmanNode):
            return False
        return (
            self.byte_val == other.byte_val
            and self.freq == other.freq
            and self.left == other.left
            and self.right == other.right
        )

    def __repr__(self) -> str:
        if self.is_leaf:
            return f"HuffmanLeaf(byte={self.byte_val}, freq={self.freq})"
        return f"HuffmanInternal(freq={self.freq})"


def build_frequency_table(data: bytes) -> Dict[int, int]:
    """
    Build a byte-frequency table from input byte data (REQ-1).

    Args:
        data: Raw input bytes.

    Returns:
        Dict mapping integer byte value (0-255) to its occurrence count.
    """
    if not data:
        return {}
    return dict(Counter(data))


def build_huffman_tree(freq_table: Dict[int, int]) -> Optional[HuffmanNode]:
    """
    Construct a Huffman tree from a frequency table using a min-heap (REQ-2).

    Args:
        freq_table: Mapping of byte values (0-255) to frequencies.

    Returns:
        Root HuffmanNode of the tree, or None if the table is empty.
    """
    if not freq_table:
        return None

    # Reset sequence counter to ensure reproducible tree structures across tests
    HuffmanNode._sequence_counter = 0

    heap: list[HuffmanNode] = []
    # Sort keys for consistent initial insertion
    for byte_val in sorted(freq_table.keys()):
        heapq.heappush(heap, HuffmanNode(byte_val=byte_val, freq=freq_table[byte_val]))

    # Edge case: Payload has only 1 distinct byte value
    if len(heap) == 1:
        single_leaf = heapq.heappop(heap)
        root = HuffmanNode(
            byte_val=None,
            freq=single_leaf.freq,
            left=single_leaf,
            right=None,
        )
        return root

    # Repeatedly combine the two lowest-frequency subtrees
    while len(heap) > 1:
        left = heapq.heappop(heap)
        right = heapq.heappop(heap)
        parent = HuffmanNode(
            byte_val=None,
            freq=left.freq + right.freq,
            left=left,
            right=right,
        )
        heapq.heappush(heap, parent)

    return heap[0]


def generate_huffman_codes(root: Optional[HuffmanNode]) -> Dict[int, str]:
    """
    Generate prefix-code bitstrings for all leaves in the Huffman tree.

    Args:
        root: Root HuffmanNode of the tree.

    Returns:
        Dict mapping byte value (0-255) to its prefix code string (e.g., '011').
    """
    if root is None:
        return {}

    codes: Dict[int, str] = {}

    def _traverse(node: HuffmanNode, current_code: str) -> None:
        if node.is_leaf:
            # If the tree has only 1 symbol, current_code may be empty
            codes[node.byte_val] = current_code if current_code else "0"  # type: ignore[index]
            return

        if node.left is not None:
            _traverse(node.left, current_code + "0")
        if node.right is not None:
            _traverse(node.right, current_code + "1")

    _traverse(root, "")
    return codes
