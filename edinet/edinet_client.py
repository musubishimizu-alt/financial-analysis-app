# -*- coding: utf-8 -*-
"""
EDINET API v2 Client for live disclosure fetching, document verification, and parsing.
Supports official FSA EDINET API v2 endpoints with zero external library dependencies.
"""
import os
import urllib.request
import urllib.parse
import json
import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

BASE_DIR = Path(__file__).parent.parent
ENV_FILE = BASE_DIR / ".env"

def load_env_file():
    """
    Safely load environment variables from .env file without external dependencies (e.g. python-dotenv).
    """
    if ENV_FILE.exists():
        try:
            with open(ENV_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip("'\"")
                        if k and not os.environ.get(k):
                            os.environ[k] = v
        except Exception as e:
            print(f"Warning: Could not parse .env file: {e}")

load_env_file()

class EdinetClient:
    """
    Client for Financial Services Agency (FSA) EDINET API v2.
    Base URL: https://disclosure2.edinet-fsa.go.jp/api/v2
    """
    BASE_URL = "https://disclosure2.edinet-fsa.go.jp/api/v2"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("EDINET_API_KEY", "").strip()

    def is_configured(self) -> bool:
        """Returns True if a non-empty API key is configured."""
        return bool(self.api_key)

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "User-Agent": "EDINETFinancialApp/2.0",
            "Accept": "application/json"
        }
        if self.api_key:
            headers["Ocp-Apim-Subscription-Key"] = self.api_key
        return headers

    def get_documents_by_date(self, date_str: str) -> Dict[str, Any]:
        """
        Fetch documents submitted on a specific date (YYYY-MM-DD).
        type=2: Metadata list of submitted documents.
        """
        params = {
            "date": date_str,
            "type": 2
        }
        if self.api_key:
            params["Subscription-Key"] = self.api_key

        url = f"{self.BASE_URL}/documents.json?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers=self._get_headers())
        try:
            with urllib.request.urlopen(req, timeout=12) as res:
                if res.status == 200:
                    data = json.loads(res.read().decode("utf-8"))
                    return data
        except urllib.error.HTTPError as e:
            return {"status": "error", "code": e.code, "message": str(e)}
        except Exception as e:
            return {"status": "error", "message": str(e)}
        return {"status": "error", "message": "Unknown error"}

    def find_latest_yuho_for_company(self, code: str, edinet_code: Optional[str] = None, target_dates: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """
        Finds the latest Annual Securities Report (有価証券報告書) for a given company code or EDINET code.
        If target_dates is provided, it searches those specific dates; otherwise checks common filing dates.
        """
        if not self.is_configured():
            return None

        # Clean code
        clean_code = code.strip()
        # 証券コード4桁の場合は前方一致用
        sec_prefix = clean_code[:4]

        # 探索する日付リスト（通常、有報の提出集中日: 6月下旬、11月下旬、3月下旬、8月下旬）
        if not target_dates:
            today = datetime.date.today()
            # 直近の決算発表・提出ピーク日を複数サンプリング
            current_year = today.year
            candidate_dates = [
                f"{current_year}-06-27", f"{current_year}-06-26", f"{current_year}-06-25",
                f"{current_year}-06-24", f"{current_year}-06-28",
                f"{current_year - 1}-11-28", f"{current_year - 1}-11-29", f"{current_year - 1}-11-27",
                f"{current_year}-03-27", f"{current_year}-03-28", f"{current_year}-03-26",
            ]
            target_dates = candidate_dates

        for date_str in target_dates:
            res = self.get_documents_by_date(date_str)
            if res.get("status") == "error":
                continue
            results = res.get("results", [])
            for item in results:
                # 提出者チェック
                item_sec = str(item.get("secCode", ""))[:4]
                item_edinet = item.get("edinetCode", "")
                doc_desc = item.get("docDescription", "")

                code_match = (sec_prefix and item_sec == sec_prefix) or (edinet_code and item_edinet == edinet_code)
                if code_match and "有価証券報告書" in doc_desc and "訂正" not in doc_desc:
                    return {
                        "doc_id": item.get("docID"),
                        "edinet_code": item_edinet,
                        "sec_code": item_sec,
                        "filer_name": item.get("filerName"),
                        "doc_description": doc_desc,
                        "submit_date_time": item.get("submitDateTime"),
                        "period_end": item.get("periodEnd"),
                        "view_url": self.get_document_view_url(item.get("docID"))
                    }

        return None

    def get_document_view_url(self, doc_id: str) -> str:
        """
        Returns the official web viewer URL for a specific document on EDINET.
        """
        if not doc_id:
            return "https://disclosure2.edinet-fsa.go.jp/"
        return f"https://disclosure2.edinet-fsa.go.jp/WZEK0040.aspx?{doc_id}"

# Singleton instance
edinet_client = EdinetClient()
