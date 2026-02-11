import pandas as pd
import re
import argparse
import sys
from collections import Counter

def parse_args():
    parser = argparse.ArgumentParser(description="AEM Dispatcher Log Analyzer")
    parser.add_argument("logfile", help="Path to dispatcher.log file")
    parser.add_argument("--metrics", choices=["errors", "traffic", "all"], default="all", help="Metrics to analyze")
    return parser.parse_args()

def parse_log_line(line):
    """
    Parses a standard Apache/Dispatcher log line.
    Example: 127.0.0.1 - - [10/Feb/2026:14:00:00 +0530] "GET /content/wknd/us/en.html HTTP/1.1" 200 1234
    """
    # Regex for Common Log Format (CLF) / Combined Log Format
    # This is a simplified regex, might need adjustment based on actual dispatcher log format
    regex = r'^(\S+) \S+ \S+ \[([\w:/]+\s[+\-]\d{4})\] "(\S+) (\S+)\s*(\S+)?" (\d{3}) (\S+)'
    match = re.match(regex, line)
    if match:
        return {
            "ip": match.group(1),
            "timestamp": match.group(2),
            "method": match.group(3),
            "path": match.group(4),
            "protocol": match.group(5),
            "status": int(match.group(6)),
            "size": match.group(7)
        }
    return None

def main():
    args = parse_args()
    
    print(f"Analyzing {args.logfile}...")
    
    data = []
    try:
        with open(args.logfile, 'r') as f:
            for line in f:
                parsed = parse_log_line(line)
                if parsed:
                    data.append(parsed)
    except FileNotFoundError:
        print(f"Error: File {args.logfile} not found.")
        sys.exit(1)

    if not data:
        print("No valid log lines found or parsed.")
        return

    df = pd.DataFrame(data)
    
    # 1. Error Hotspots (404s, 500s)
    if args.metrics in ["errors", "all"]:
        print("\n--- Error Analysis ---")
        errors = df[df['status'] >= 400]
        if not errors.empty:
            print(f"Total Errors: {len(errors)}")
            print("\nTop 404 Paths (Not Found):")
            print(errors[errors['status'] == 404]['path'].value_counts().head(5))
            
            print("\nTop 500 Paths (Server Error):")
            print(errors[errors['status'] == 500]['path'].value_counts().head(5))
        else:
            print("No errors found 🎉")

    # 2. High Traffic Paths
    if args.metrics in ["traffic", "all"]:
        print("\n--- Traffic Analysis ---")
        print("\nTop 10 Most Requested Paths:")
        print(df['path'].value_counts().head(10))
        
        print("\nTraffic by Method:")
        print(df['method'].value_counts())

if __name__ == "__main__":
    main()
