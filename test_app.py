# -*- coding: utf-8 -*-
import json
import unittest
from pathlib import Path
import sys

BASE_DIR = Path(r"C:\Users\mog44\.gemini\antigravity\scratch\financial_analysis_app")
sys.path.insert(0, str(BASE_DIR))

from financial_calculator import calculate_metrics, generate_quiz

class TestFinancialApp(unittest.TestCase):
    def setUp(self):
        data_path = BASE_DIR / "data" / "companies_data.json"
        self.assertTrue(data_path.exists(), "companies_data.json must exist")
        with open(data_path, "r", encoding="utf-8") as f:
            self.companies = json.load(f)
        self.assertGreater(len(self.companies), 0)

    def test_company_data_integrity(self):
        for c in self.companies:
            self.assertIn("name", c)
            self.assertIn("code", c)
            self.assertIn("financial_raw", c)
            raw = c["financial_raw"]
            self.assertGreater(raw["revenue"], 0)
            self.assertGreater(raw["total_assets"], 0)
            self.assertGreater(raw["stock_price"], 0, f"{c['name']} must have stock_price")
            self.assertGreater(raw["eps"], 0, f"{c['name']} must have eps")
            self.assertGreater(raw["bps"], 0, f"{c['name']} must have bps")

    def test_metrics_calculation(self):
        expected_keys = ["equity_ratio", "roe", "roic", "pbr", "per", "roa", "operating_margin"]
        for c in self.companies:
            metrics = calculate_metrics(c)
            for key in expected_keys:
                self.assertIn(key, metrics, f"Metric {key} missing in {c['name']}")
                m = metrics[key]
                self.assertIn("value", m)
                self.assertIn("formula_definition", m)
                self.assertIn("formula_applied", m)
                self.assertIn("items_used", m)
                self.assertGreater(len(m["items_used"]), 0)

    def test_quiz_generation(self):
        for _ in range(15):
            quiz = generate_quiz(self.companies)
            self.assertIn("options", quiz)
            self.assertEqual(len(quiz["options"]), 3)
            self.assertIn(quiz["correct_option"], quiz["options"])
            self.assertIn("hint_items", quiz)
            self.assertIn("explanation", quiz)

if __name__ == "__main__":
    unittest.main()
