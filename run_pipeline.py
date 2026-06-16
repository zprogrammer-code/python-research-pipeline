import os
import subprocess
import time
import functools
import logging
from datetime import datetime
from win11toast import toast

def notify(title, message):
    try:
        toast(title, message)
    except Exception as e:
        log_error(f"Toast notification failed: {e}")



# Create logs directory if it doesn't exist
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Log file name with date
log_filename = os.path.join(LOG_DIR, f"pipeline_{datetime.now().strftime('%Y-%m-%d')}.log")

logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

def log_info(msg):
    logging.info(msg)
    print(msg)

def log_error(msg):
    logging.error(msg)
    print("ERROR:", msg)

def retry(max_attempts=3, delay=5):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempts += 1
                    log_error(f"{func.__name__} failed (attempt {attempts}/{max_attempts}): {e}")
                    time.sleep(delay)
            raise Exception(f"{func.__name__} failed after {max_attempts} attempts")
        return wrapper
    return decorator

@retry(max_attempts=3, delay=5)
def run_fetcher():
    subprocess.run(["python", "fetch_sec_filings.py"], check=True)

@retry(max_attempts=3, delay=5)
def run_processor():
    subprocess.run(["python", "process_filings.py"], check=True)


# -------------------------
# PIPELINE STARTS HERE
# -------------------------

log_info("=== Pipeline Started ===")

try:
    log_info("=== Running SEC Fetcher ===")
    run_fetcher()


    log_info("=== Running Processing Layer ===")
    run_processor()


    log_info("=== Pipeline Complete ===")

    notify("Pipeline Complete", "SEC research pipeline finished successfully")


except Exception as e:
    logging.exception("Pipeline failed")

    notify("Pipeline Failed", "Check logs for details")



