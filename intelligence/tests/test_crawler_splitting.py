import unittest
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.crawler.crawler import splitter, CHUNK_SIZE, CHUNK_OVERLAP
from langchain_text_splitters import RecursiveCharacterTextSplitter

class TestCrawlerSplitting(unittest.TestCase):

    def test_splitter_configuration(self):
        self.assertIsInstance(splitter, RecursiveCharacterTextSplitter)
        # Note: In newer langchain versions, these might be private or named differently, 
        # but commonly they are accessible properties.
        # If accessing implementation details is flaky, we verify behavior.
        # But let's check attributes if possible.
        self.assertEqual(getattr(splitter, '_chunk_size', splitter._chunk_size), 650)
        self.assertEqual(getattr(splitter, '_chunk_overlap', splitter._chunk_overlap), 65)

    def test_splitting_behavior(self):
        text = "A" * 1000 # String of 1000 characters
        chunks = splitter.split_text(text)
        
        self.assertTrue(len(chunks) > 1)
        # First chunk should be 650
        self.assertEqual(len(chunks[0]), 650)
        # Overlap check is trickier on simple string, but length constraints hold

    def test_splitting_with_separator(self):
        # Create text with explicit separators
        text = "Paragraph 1. " * 50 + "\n\n" + "Paragraph 2. " * 50
        chunks = splitter.split_text(text)
        
        for chunk in chunks:
            self.assertTrue(len(chunk) <= 650)

if __name__ == '__main__':
    unittest.main()
