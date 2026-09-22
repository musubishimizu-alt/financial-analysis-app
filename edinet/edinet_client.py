# -*- coding: utf-8 -*-
"""
EDINET API v2 Client for live disclosure fetching, document verification, and parsing.
Supports official FSA EDINET API v2 endpoints with zero external library dependencies.
Features smart date caching and batch company yuho synchronization.
"""
import os
import urllib.request
import urllib.parse
import json
import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
ENV_FILE = BASE_DIR / ".env"
CACHE_DIR = DATA_DIR / "edinet_cache"

def load_env_file():
    """
    Safely load environment variables from .env file without external dependencies.
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
        self._api_key = api_key
        if not CACHE_DIR.exists():
            try:
                CACHE_DIR.mkdir(parents=True, exist_ok=True)
            except Exception:
                pass

    @property
    def api_key(self) -> str:
        # 動的に環境変数をチェック（実行中に.envが作成された場合にも即対応）
        if self._api_key:
            return self._api_key
        key = os.environ.get("EDINET_API_KEY", "").strip()
        if not key:
            load_env_file()
            key = os.environ.get("EDINET_API_KEY", "").strip()
        return key

    def is_configured(self) -> bool:
        """Returns True if a non-empty API key is configured."""
        return bool(self.api_key and len(self.api_key) > 5)

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "User-Agent": "EDINETFinancialApp/2.0",
            "Accept": "application/json"
        }
        if self.api_key:
            headers["Ocp-Apim-Subscription-Key"] = self.api_key
        return headers

    def get_documents_by_date(self, date_str: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        Fetch documents submitted on a specific date (YYYY-MM-DD).
        Caches results locally to avoid redundant API hits.
        """
        cache_file = CACHE_DIR / f"{date_str}.json"
        if use_cache and cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

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
                    if use_cache and data.get("status") != "error":
                        try:
                            with open(cache_file, "w", encoding="utf-8") as f:
                                json.dump(data, f, ensure_ascii=False)
                        except Exception:
                            pass
                    return data
        except urllib.error.HTTPError as e:
            return {"status": "error", "code": e.code, "message": str(e)}
        except Exception as e:
            return {"status": "error", "message": str(e)}
        return {"status": "error", "message": "Unknown error"}

    def find_latest_yuho_for_company(self, code: str, edinet_code: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Finds the latest Annual Securities Report (有価証券報告書) for a given company.
        Checks key submission dates (June, March, November, August peak dates).
        """
        if not self.is_configured():
            return None

        clean_code = code.strip()[:4]
        today = datetime.date.today()
        current_year = today.year

        # 有報の集中提出日（6月下旬、3月下旬、11月下旬、8月下旬）
        dates_to_search = [
            # 6月下旬（3月決算）
            f"{current_year}-06-27", f"{current_year}-06-26", f"{current_year}-06-25",
            f"{current_year}-06-28", f"{current_year}-06-24", f"{current_year}-06-21",
            # 11月下旬（8月決算: ファストリ等）
            f"{current_year - 1}-11-28", f"{current_year - 1}-11-29", f"{current_year - 1}-11-27",
            # 3月下旬（12月決算: セグエ等）
            f"{current_year}-03-27", f"{current_year}-03-28", f"{current_year}-03-26", f"{current_year}-03-25",
            # 8月下旬（5月決算）
            f"{current_year}-08-28", f"{current_year}-08-29", f"{current_year}-08-27",
            # 9月下旬（6月決算: メルカリ等）
            f"{current_year - 1}-09-27", f"{current_year - 1}-09-26", f"{current_year - 1}-09-28",
        ]

        for date_str in dates_to_search:
            res = self.get_documents_by_date(date_str)
            if res.get("status") == "error":
                continue
            for item in res.get("results", []):
                item_sec = str(item.get("secCode", ""))[:4]
                item_edinet = item.get("edinetCode", "")
                doc_desc = item.get("docDescription", "")

                code_match = (clean_code and item_sec == clean_code) or (edinet_code and item_edinet == edinet_code)
                if code_match and "有価証券報告書" in doc_desc and "訂正" not in doc_desc:
                    doc_id = item.get("docID")
                    return {
                        "doc_id": doc_id,
                        "edinet_code": item_edinet,
                        "sec_code": item_sec,
                        "filer_name": item.get("filerName"),
                        "doc_description": doc_desc,
                        "submit_date_time": item.get("submitDateTime"),
                        "period_end": item.get("periodEnd"),
                        "view_url": self.get_document_view_url(doc_id)
                    }

        return None

    def sync_all_registered_companies(self, companies_data_file: Path) -> int:
        """
        Batch syncs official docID and view_url for all companies in companies_data.json.
        Returns the count of updated companies.
        """
        if not self.is_configured() or not companies_data_file.exists():
            return 0

        with open(companies_data_file, "r", encoding="utf-8") as f:
            companies = json.load(f)

        updated_count = 0
        for comp in companies:
            code = comp.get("code", "")
            edinet_code = comp.get("edinet_code", "")
            yuho = self.find_latest_yuho_for_company(code, edinet_code)
            if yuho:
                comp["doc_id"] = yuho["doc_id"]
                comp["edinet_url"] = yuho["view_url"]
                comp["edinet_verified"] = True
                if yuho.get("period_end"):
                    comp["submit_date_time"] = yuho.get("submit_date_time")
                updated_count += 1
                print(f"Synced {comp.get('name')}: docID={yuho['doc_id']}")

        if updated_count > 0:
            with open(companies_data_file, "w", encoding="utf-8") as f:
                json.dump(companies, f, ensure_ascii=False, indent=2)

        return updated_count

    def get_document_view_url(self, doc_id: str) -> str:
        """
        Returns the official web viewer URL for a specific document on EDINET.
        Format: https://disclosure2.edinet-fsa.go.jp/WZEK0040.aspx?{docID}
        """
        if not doc_id:
            return "https://disclosure2.edinet-fsa.go.jp/"
        return f"https://disclosure2.edinet-fsa.go.jp/WZEK0040.aspx?{doc_id}"

# Singleton instance
edinet_client = EdinetClient()
