import threading
import random
import string
import time
import requests
import psutil
import os
import json
from datetime import datetime

# Configs
TARGET_URL = "http://localhost:5000/search"  
# Replace with the OSINT tool's endpoint

LOG_DIR = "logs"
REPORT_DIR = "reports"
ERROR_LOG = os.path.join(LOG_DIR, "error_log.txt")
RESOURCE_LOG = os.path.join(LOG_DIR, "resource_usage.log")
REPORT_FILE = os.path.join(REPORT_DIR, "results_summary.json")

# Ensure directories exist
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)

summary = {
    "input_overload_errors": 0,
    "concurrency_errors": 0,
    "fuzz_errors": 0,
    "start_time": datetime.now().isoformat(),
    "end_time": None
}

# Utility Functions
def log_error(message):
    with open(ERROR_LOG, "a") as f:
        f.write(f"{datetime.now()} - {message}\n")

def random_query(length=50):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# Stress Tests
def test_input_overload():
    print("[*] Running input overload test...")
    for i in range(5000):  # Large number of requests
        payload = {"query": random_query(200)}
        try:
            requests.post(TARGET_URL, json=payload, timeout=5)
        except Exception as e:
            log_error(f"Input overload error at request {i}: {e}")
            summary["input_overload_errors"] += 1

def test_concurrency(threads=20):
    print(f"[*] Running concurrency test with {threads} threads...")

    def worker():
        for _ in range(500):
            payload = {"query": random_query()}
            try:
                requests.post(TARGET_URL, json=payload, timeout=5)
            except Exception as e:
                log_error(f"Concurrency error: {e}")
                summary["concurrency_errors"] += 1

    thread_list = []
    for _ in range(threads):
        t = threading.Thread(target=worker)
        t.start()
        thread_list.append(t)

    for t in thread_list:
        t.join()

def test_fuzzing():
    print("[*] Running fuzz test...")
    fuzz_inputs = ["", " ", "\n", "\x00", random_query(10000), None, 12345]
    for data in fuzz_inputs:
        try:
            requests.post(TARGET_URL, json={"query": data}, timeout=5)
        except Exception as e:
            log_error(f"Fuzz input {repr(data)} caused error: {e}")
            summary["fuzz_errors"] += 1

# Resource Monitoring
def monitor_resources(duration=60):
    print("[*] Monitoring system resources...")
    start_time = time.time()
    with open(RESOURCE_LOG, "w") as f:
        while time.time() - start_time < duration:
            cpu = psutil.cpu_percent()
            mem = psutil.virtual_memory().percent
            log_line = f"{datetime.now()} | CPU: {cpu}% | Memory: {mem}%\n"
            f.write(log_line)
            time.sleep(5)

# Main Function
if __name__ == "__main__":
    test_input_overload()
    test_concurrency()
    test_fuzzing()

    # Monitor resources for 1 minute
    monitor_resources()

    summary["end_time"] = datetime.now().isoformat()

    with open(REPORT_FILE, "w") as f:
        json.dump(summary, f, indent=4)

    print("[*] Testing complete. Check logs and reports for details.")
