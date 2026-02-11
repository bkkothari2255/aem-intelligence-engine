import unittest
from unittest.mock import patch, mock_open
import sys
import os
import pandas as pd
from io import StringIO

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.analysis.log_analyzer import parse_log_line, main

class TestLogAnalyzer(unittest.TestCase):

    def test_parse_log_line_valid(self):
        line = '127.0.0.1 - - [10/Feb/2026:14:00:00 +0530] "GET /content/wknd/us/en.html HTTP/1.1" 200 1234'
        parsed = parse_log_line(line)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed['ip'], '127.0.0.1')
        self.assertEqual(parsed['timestamp'], '10/Feb/2026:14:00:00 +0530')
        self.assertEqual(parsed['method'], 'GET')
        self.assertEqual(parsed['path'], '/content/wknd/us/en.html')
        self.assertEqual(parsed['status'], 200)

    def test_parse_log_line_invalid(self):
        line = 'Invalid Log Line'
        parsed = parse_log_line(line)
        self.assertIsNone(parsed)

    @patch('sys.stdout', new_callable=StringIO)
    def test_main_analysis(self, mock_stdout):
        # Mock file content
        log_content = """127.0.0.1 - - [10/Feb/2026:14:00:00 +0530] "GET /content/page1.html HTTP/1.1" 200 100
127.0.0.1 - - [10/Feb/2026:14:01:00 +0530] "GET /content/page2.html HTTP/1.1" 404 100
127.0.0.1 - - [10/Feb/2026:14:02:00 +0530] "GET /content/page2.html HTTP/1.1" 404 100
127.0.0.1 - - [10/Feb/2026:14:03:00 +0530] "POST /bin/submit HTTP/1.1" 500 100"""
        
        with patch('builtins.open', mock_open(read_data=log_content)):
            with patch('argparse.ArgumentParser.parse_args') as mock_args:
                mock_args.return_value.logfile = 'dummy.log'
                mock_args.return_value.metrics = 'all'
                
                main()
                
        output = mock_stdout.getvalue()
        
        # Verify output contains analysis
        self.assertIn("Total Errors: 3", output) # 2 404s + 1 500
        self.assertIn("/content/page2.html", output)
        self.assertIn("Top 404 Paths", output)
        self.assertIn("Top 500 Paths", output)

if __name__ == '__main__':
    unittest.main()
