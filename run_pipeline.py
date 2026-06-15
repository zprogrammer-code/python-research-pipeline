import subprocess

print("=== Running SEC Fetcher ===")
subprocess.run(["python", "fetch_sec_filings.py"])

print("\n=== Running Processing Layer ===")
subprocess.run(["python", "process_filings.py"])

print("\n=== Pipeline Complete ===")
