# -*- coding: utf-8 -*-
import threading
import time
import urllib.request
import json
from pathlib import Path
import sys

BASE_DIR = Path(r"C:\Users\mog44\.gemini\antigravity\scratch\financial_analysis_app")
sys.path.insert(0, str(BASE_DIR))

from app import FinancialAppHandler
import socketserver

def run_test():
    test_port = 8089
    httpd = socketserver.ThreadingTCPServer(("", test_port), FinancialAppHandler)
    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()
    time.sleep(0.5)

    base_url = f"http://localhost:{test_port}"
    print(f"Server started on {base_url}")

    # 1. Test GET /
    with urllib.request.urlopen(f"{base_url}/") as res:
        assert res.status == 200
        html = res.read().decode("utf-8")
        assert "PBR" in html
        assert "PER" in html
        print(" [PASS] GET / (index.html with PBR/PER)")

    # 2. Test GET /api/companies/7203 (Toyota metrics)
    with urllib.request.urlopen(f"{base_url}/api/companies/7203") as res:
        data = json.loads(res.read().decode("utf-8"))
        m = data["metrics"]
        assert "pbr" in m
        assert "per" in m
        assert m["pbr"]["value"] > 0
        assert m["per"]["value"] > 0
        print(f" [PASS] GET /api/companies/7203 (PBR={m['pbr']['value']}倍, PER={m['per']['value']}倍)")

    # 3. Test GET /api/quiz
    with urllib.request.urlopen(f"{base_url}/api/quiz") as res:
        quiz = json.loads(res.read().decode("utf-8"))
        assert "options" in quiz
        assert len(quiz["options"]) == 3
        print(f" [PASS] GET /api/quiz (Target: {quiz['metric_name']})")

    httpd.shutdown()
    print("All HTTP integration tests with PBR & PER passed successfully!")

if __name__ == "__main__":
    run_test()
