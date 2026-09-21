# -*- coding: utf-8 -*-
"""
EDINET API v2 Client for live disclosure fetching and search.
"""
import urllib.request
import urllib.parse
import json
from typing import Optional, Dict, Any, List

class EdinetClient:
    BASE_URL = "https://disclosure2.edinet-fsa.go.jp/api/v2"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    def search_documents_by_date(self, date_str: str) -> Dict[str, Any]:
        """
        Fetch documents submitted on a specific date (YYYY-MM-DD).
        """
        params = {
            "date": date_str,
            "type": 2  # 2: Metadata list
        }
        if self.api_key:
            params["Subscription-Key"] = self.api_key

        url = f"{self.BASE_URL}/documents.json?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers={"User-Agent": "AntigravityFinancialApp/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=10) as res:
                if res.status == 200:
                    return json.loads(res.read().decode("utf-8"))
        except Exception as e:
            return {"status": "error", "message": str(e)}
        return {"status": "unknown"}

    def get_document_view_url(self, doc_id: str) -> str:
        """
        Returns the web viewer URL for a specific document on EDINET.
        """
        return f"https://disclosure2.edinet-fsa.go.jp/WZEK0040.aspx?{doc_id}"
