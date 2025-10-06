"""
Huffman Coding Algorithm Implementation
Provides encoding, decoding, and tree visualization for Huffman coding
"""

import heapq
from collections import defaultdict, Counter
import json


class HuffmanNode:
    """Node class for Huffman Tree"""
    def __init__(self, char, freq):
        self.char = char
        self.freq = freq
        self.left = None
        self.right = None
    
    def __lt__(self, other):
        return self.freq < other.freq
    
    def __eq__(self, other):
        return self.freq == other.freq


class HuffmanCoding:
    """Huffman Coding implementation for compression and decompression"""
    
    def __init__(self):
        self.heap = []
        self.codes = {}
        self.reverse_codes = {}
        self.root = None
    
    def build_frequency_dict(self, text):
        """Build frequency dictionary from text"""
        return dict(Counter(text))
    
    def build_heap(self, frequency):
        """Build min heap from frequency dictionary"""
        for char, freq in frequency.items():
            node = HuffmanNode(char, freq)
            heapq.heappush(self.heap, node)
    
    def build_tree(self):
        """Build Huffman tree from heap"""
        while len(self.heap) > 1:
            node1 = heapq.heappop(self.heap)
            node2 = heapq.heappop(self.heap)
            
            merged = HuffmanNode(None, node1.freq + node2.freq)
            merged.left = node1
            merged.right = node2
            
            heapq.heappush(self.heap, merged)
        
        self.root = self.heap[0]
        return self.root
    
    def build_codes_helper(self, node, current_code):
        """Helper function to build codes recursively"""
        if node is None:
            return
        
        if node.char is not None:
            self.codes[node.char] = current_code
            self.reverse_codes[current_code] = node.char
            return
        
        self.build_codes_helper(node.left, current_code + "0")
        self.build_codes_helper(node.right, current_code + "1")
    
    def build_codes(self):
        """Build Huffman codes from tree"""
        if self.root is None:
            return
        
        # Special case: single character
        if self.root.char is not None:
            self.codes[self.root.char] = "0"
            self.reverse_codes["0"] = self.root.char
            return
        
        self.build_codes_helper(self.root, "")
    
    def encode_text(self, text):
        """Encode text using Huffman codes"""
        encoded = ""
        for char in text:
            encoded += self.codes.get(char, "")
        return encoded
    
    def decode_text(self, encoded_text):
        """Decode text using Huffman codes"""
        decoded = ""
        current_code = ""
        
        for bit in encoded_text:
            current_code += bit
            if current_code in self.reverse_codes:
                decoded += self.reverse_codes[current_code]
                current_code = ""
        
        return decoded
    
    def compress(self, text):
        """Complete compression pipeline"""
        if not text:
            return "", {}, None
        
        # Build frequency dictionary
        frequency = self.build_frequency_dict(text)
        
        # Build heap and tree
        self.build_heap(frequency)
        self.build_tree()
        
        # Build codes
        self.build_codes()
        
        # Encode text
        encoded_text = self.encode_text(text)
        
        return encoded_text, self.codes, self.root
    
    def get_tree_structure(self, node=None, level=0):
        """Get tree structure for visualization"""
        if node is None:
            node = self.root
        
        if node is None:
            return []
        
        tree_data = []
        
        # Create node data
        node_data = {
            'char': node.char if node.char else 'Internal',
            'freq': node.freq,
            'level': level,
            'is_leaf': node.char is not None
        }
        
        tree_data.append(node_data)
        
        # Recursively get children
        if node.left:
            tree_data.extend(self.get_tree_structure(node.left, level + 1))
        if node.right:
            tree_data.extend(self.get_tree_structure(node.right, level + 1))
        
        return tree_data
    
    def get_tree_json(self, node=None):
        """Get tree structure as JSON for D3.js visualization"""
        if node is None:
            node = self.root
        
        if node is None:
            return None
        
        tree_dict = {
            'name': f"{node.char if node.char else '●'}\n({node.freq})",
            'char': node.char,
            'freq': node.freq,
            'is_leaf': node.char is not None
        }
        
        children = []
        if node.left:
            left_child = self.get_tree_json(node.left)
            if left_child:
                left_child['edge_label'] = '0'
                children.append(left_child)
        
        if node.right:
            right_child = self.get_tree_json(node.right)
            if right_child:
                right_child['edge_label'] = '1'
                children.append(right_child)
        
        if children:
            tree_dict['children'] = children
        
        return tree_dict


def compress_file_content(content):
    """Compress file content using Huffman coding"""
    huffman = HuffmanCoding()
    
    if isinstance(content, bytes):
        # Convert bytes to string representation
        content_str = ''.join(chr(b) for b in content)
    else:
        content_str = content
    
    encoded, codes, root = huffman.compress(content_str)
    
    # Convert encoded string to bytes
    # Pad to make it byte-aligned
    padding = 8 - len(encoded) % 8
    encoded += '0' * padding
    
    # Convert binary string to bytes
    compressed_bytes = bytearray()
    for i in range(0, len(encoded), 8):
        byte = encoded[i:i+8]
        compressed_bytes.append(int(byte, 2))
    
    # Store metadata
    metadata = {
        'codes': codes,
        'padding': padding,
        'original_size': len(content_str)
    }
    
    return bytes(compressed_bytes), metadata


def decompress_file_content(compressed_bytes, metadata):
    """Decompress file content using Huffman coding"""
    # Convert bytes back to binary string
    binary_str = ''.join(format(byte, '08b') for byte in compressed_bytes)
    
    # Remove padding
    binary_str = binary_str[:-metadata['padding']]
    
    # Decode using reverse codes
    huffman = HuffmanCoding()
    huffman.reverse_codes = {v: k for k, v in metadata['codes'].items()}
    
    decoded = huffman.decode_text(binary_str)
    
    return decoded
