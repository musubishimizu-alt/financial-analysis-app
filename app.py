# -*- coding: utf-8 -*-
"""
Financial Analysis & Quiz Web Application Server.
Uses standard library http.server for zero-dependency portability and high performance.
"""
import http.server
import socketserver
import json
import urllib.parse
from pathlib import Path
from typing import Dict, Any, List
import os

from financial_calculator import calculate_metrics, generate_quiz
from financial_scraper import search_company_candidates, fetch_company_financials
from edinet.edinet_client import edinet_client

PORT = int(os.environ.get("PORT", 8000))
BASE_DIR = Path(__file__).parent
DATA_FILE = BASE_DIR / "data" / "companies_data.json"
STATIC_DIR = BASE_DIR / "static"

# Load companies data in-memory
companies_cache: List[Dict[str, Any]] = []

def load_data():
    global companies_cache
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            companies_cache = json.load(f)
    else:
        companies_cache = []

load_data()

class FinancialAppHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # 1. API: List / Search Companies
        if path == "/api/companies":
            q = query.get("q", [""])[0].strip().lower()
            sector = query.get("sector", [""])[0].strip()

            results = []
            for c in companies_cache:
                if sector and c.get("sector") != sector:
                    continue
                if q:
                    match = (
                        q in c["name"].lower() or
                        q in c["short_name"].lower() or
                        q in c["code"].lower() or
                        q in c.get("kana", "").lower() or
                        q in c.get("english_name", "").lower()
                    )
                    if not match:
                        continue
                results.append(c)

            formatted = [{
                "id": c["id"],
                "code": c["code"],
                "name": c["name"],
                "short_name": c["short_name"],
                "sector": c["sector"],
                "fiscal_period": c["fiscal_period"],
                "standard": c["standard"],
                "edinet_code": c["edinet_code"]
            } for c in results]
            self.send_json_response(formatted)
            return

        # 2. API: Search Candidates from JPX Master (for adding new company)
        if path == "/api/companies/search_candidates":
            q = query.get("q", [""])[0].strip()
            candidates = search_company_candidates(q)
            existing_codes = {c["code"] for c in companies_cache}
            for cand in candidates:
                cand["is_registered"] = (cand["code"] in existing_codes)
            self.send_json_response(candidates)
            return

        # 3. API: Fetch Financials for specified stock code
        if path == "/api/companies/fetch_financials":
            code = query.get("code", [""])[0].strip()
            if not code:
                self.send_json_response({"error": "Stock code is required"}, status=400)
                return
            try:
                data = fetch_company_financials(code)
                self.send_json_response(data)
            except Exception as e:
                self.send_json_response({"error": f"Failed to fetch financials: {str(e)}"}, status=500)
            return

        # 4. API: Company Details & Calculated Metrics
        if path.startswith("/api/companies/"):
            comp_id = path.replace("/api/companies/", "").strip("/")
            company = next((c for c in companies_cache if c["id"] == comp_id or c["code"] == comp_id), None)
            if not company:
                self.send_json_response({"error": "Company not found"}, status=404)
                return

            metrics = calculate_metrics(company)
            response_data = {
                "company": {
                    "id": company["id"],
                    "code": company["code"],
                    "name": company["name"],
                    "short_name": company["short_name"],
                    "english_name": company.get("english_name", ""),
                    "sector": company["sector"],
                    "fiscal_period": company["fiscal_period"],
                    "standard": company["standard"],
                    "edinet_code": company["edinet_code"],
                    "doc_id": company.get("doc_id", ""),
                    "edinet_url": company["edinet_url"],
                    "description": company.get("description", ""),
                    "financial_raw": company["financial_raw"],
                    "source_locations": company["source_locations"]
                },
                "metrics": metrics
            }
            self.send_json_response(response_data)
            return

        # 5. API: Generate Quiz
        if path == "/api/quiz":
            if not companies_cache:
                self.send_json_response({"error": "No companies loaded"}, status=500)
                return
            quiz_data = generate_quiz(companies_cache)
            self.send_json_response(quiz_data)
            return

        # 6. API: Stats & Sectors
        if path == "/api/meta":
            sectors = sorted(list({c["sector"] for c in companies_cache}))
            self.send_json_response({
                "company_count": len(companies_cache),
                "sectors": sectors,
                "edinet_api_active": edinet_client.is_configured(),
                "supported_metrics": [
                    {"key": "equity_ratio", "name": "自己資本比率", "lead": "財務健全性の最重要指標"},
                    {"key": "roe", "name": "ROE（自己資本利益率）", "lead": "株主目線での資本効率"},
                    {"key": "roic", "name": "ROIC（投下資本利益率）", "lead": "本業の稼ぐ力＆資本コスト"},
                    {"key": "pbr", "name": "PBR（株価純資産倍率）", "lead": "解散価値対比の割安度・東証改革"},
                    {"key": "per", "name": "PER（株価収益率）", "lead": "利益対比の割安度・市場期待度"},
                    {"key": "roa", "name": "ROA（総資産利益率）", "lead": "総資産の総合的運用効率"},
                    {"key": "operating_margin", "name": "売上高営業利益率", "lead": "事業の高収益性・競争優位"}
                ]
            })
            return

        # Fallback to static files
        if path == "/":
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # 1. Check Quiz Answer
        if path == "/api/quiz/check":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            try:
                data = json.loads(body)
            except Exception:
                self.send_json_response({"error": "Invalid JSON"}, status=400)
                return

            user_choice = data.get("selected_option")
            correct_choice = data.get("correct_option")
            is_correct = (user_choice == correct_choice)

            self.send_json_response({
                "is_correct": is_correct,
                "selected_option": user_choice,
                "correct_option": correct_choice
            })
            return

        # 2. Add New Company
        if path == "/api/companies/add":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            try:
                new_company = json.loads(body)
            except Exception:
                self.send_json_response({"error": "Invalid JSON format"}, status=400)
                return

            code = str(new_company.get("code", "")).strip()
            if not code:
                self.send_json_response({"error": "Stock code is required"}, status=400)
                return

            global companies_cache
            existing_idx = next((i for i, c in enumerate(companies_cache) if c["code"] == code), None)
            if existing_idx is not None:
                companies_cache[existing_idx] = new_company
            else:
                companies_cache.append(new_company)

            # Persist to JSON file
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(companies_cache, f, ensure_ascii=False, indent=2)

            self.send_json_response({
                "success": True,
                "message": f"「{new_company.get('name', code)}」を有報分析対象に登録しました！",
                "company_id": new_company.get("id", code),
                "code": code
            })
            return

        self.send_json_response({"error": "Not Found"}, status=404)

    def send_json_response(self, data: Any, status: int = 200):
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

def run_server():
    server_address = ("", PORT)
    with socketserver.ThreadingTCPServer(server_address, FinancialAppHandler) as httpd:
        edinet_status = "ENABLED (金融庁公式API連携中)" if edinet_client.is_configured() else "FALLBACK (公開Webデータ連携)"
        print(f"===========================================================")
        print(f" Financial Analysis & Quiz App is running!")
        print(f" URL: http://localhost:{PORT}")
        print(f" Loaded {len(companies_cache)} companies from EDINET reports.")
        print(f" EDINET API v2: {edinet_status}")
        print(f" Supported: 自己資本比率, ROE, ROIC, PBR, PER, ROA, 営業利益率")
        print(f" Press Ctrl+C to stop.")
        print(f"===========================================================")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")

if __name__ == "__main__":
    run_server()
