# -*- coding: utf-8 -*-
"""
Financial metrics calculation and quiz generation engine.
Includes: 自己資本比率, ROE, ROIC, ROA, 売上高営業利益率, PBR, PER
"""
import random
from typing import Dict, Any, List

def calculate_metrics(company: Dict[str, Any]) -> Dict[str, Any]:
    raw = company["financial_raw"]
    sources = company["source_locations"]

    rev = raw["revenue"]
    op_inc = raw["operating_income"]
    net_inc = raw["net_income"]
    assets = raw["total_assets"]
    equity = raw["equity"]
    debt = raw.get("interest_bearing_debt", 0)
    tax_rate = raw.get("tax_rate", 0.306)

    # 1. 自己資本比率 (Equity Ratio)
    equity_ratio = (equity / assets * 100) if assets else 0.0
    equity_ratio_eval = "優良 (50%以上)" if equity_ratio >= 50 else ("健全 (40%以上)" if equity_ratio >= 40 else "注意 (40%未満)")

    # 2. ROE (自己資本利益率)
    roe = (net_inc / equity * 100) if equity else 0.0
    roe_eval = "非常に高い (15%以上)" if roe >= 15 else ("高水準 (8%〜15%)" if roe >= 8 else "標準的/改善余地 (8%未満)")

    # 3. ROA (総資産利益率)
    roa = (net_inc / assets * 100) if assets else 0.0
    roa_eval = "高収益 (10%以上)" if roa >= 10 else ("良好 (5%〜10%)" if roa >= 5 else "標準的 (5%未満)")

    # 4. ROIC (投下資本利益率)
    nopat = op_inc * (1 - tax_rate)
    invested_capital = debt + equity
    roic = (nopat / invested_capital * 100) if invested_capital else 0.0
    roic_eval = "資本コストを大幅に超過 (10%以上)" if roic >= 10 else ("価値創造圏 (7%〜10%)" if roic >= 7 else "資本効率改善余地 (7%未満)")

    # 5. 売上高営業利益率 (Operating Margin)
    op_margin = (op_inc / rev * 100) if rev else 0.0
    op_margin_eval = "超高収益 (20%以上)" if op_margin >= 20 else ("高収益 (10%〜20%)" if op_margin >= 10 else ("良好 (5%〜10%)" if op_margin >= 5 else "薄利 (5%未満)"))

    # 6. PBR (株価純資産倍率 - Price Book-value Ratio)
    stock_price = raw.get("stock_price", 0)
    bps = raw.get("bps", 0)
    pbr = (stock_price / bps) if (stock_price and bps) else 0.0
    if pbr < 1.0:
        pbr_eval = "解散価値割れ (1.0倍未満・割安/改善要請対象)"
    elif pbr < 2.0:
        pbr_eval = "市場標準水準 (1.0〜2.0倍)"
    elif pbr < 5.0:
        pbr_eval = "高評価・ブランド価値大 (2.0〜5.0倍)"
    else:
        pbr_eval = "超高評価・市場期待極めて大 (5.0倍以上)"

    # 7. PER (株価収益率 - Price Earnings Ratio)
    eps = raw.get("eps", 0)
    per = (stock_price / eps) if (stock_price and eps) else 0.0
    if per < 15.0:
        per_eval = "割安水準 (15倍未満)"
    elif per < 25.0:
        per_eval = "市場平均水準 (15〜25倍)"
    elif per < 40.0:
        per_eval = "高成長期待 (25〜40倍)"
    else:
        per_eval = "超高成長期待 / プレミアム評価 (40倍以上)"

    metrics = {
        "equity_ratio": {
            "name": "自己資本比率 (Equity Ratio)",
            "key": "equity_ratio",
            "value": round(equity_ratio, 1),
            "unit": "%",
            "formula_definition": "自己資本 ÷ 総資産 × 100 (%)",
            "formula_applied": f"({equity:,} 百万円 ÷ {assets:,} 百万円) × 100 = {equity_ratio:.1f}%",
            "evaluation": equity_ratio_eval,
            "description": "総資産のうち返済不要な自己資本が占める割合。企業の財務健全性や中長期的な倒産リスク耐性を示します（一般に40%以上で健全）。",
            "items_used": [
                {
                    "item_name": sources["equity"]["item_name"],
                    "value": f"{equity:,} 百万円",
                    "location": sources["equity"]["section"],
                    "page": sources["equity"]["page"]
                },
                {
                    "item_name": sources["total_assets"]["item_name"],
                    "value": f"{assets:,} 百万円",
                    "location": sources["total_assets"]["section"],
                    "page": sources["total_assets"]["page"]
                }
            ]
        },
        "roe": {
            "name": "ROE (自己資本利益率 - Return on Equity)",
            "key": "roe",
            "value": round(roe, 1),
            "unit": "%",
            "formula_definition": "当期純利益 ÷ 自己資本 × 100 (%)",
            "formula_applied": f"({net_inc:,} 百万円 ÷ {equity:,} 百万円) × 100 = {roe:.1f}%",
            "evaluation": roe_eval,
            "description": "株主から集めた資金（自己資本）を使ってどれだけ効率的に利益を生み出したかを示す指標。投資家が最も重視する指標の一つで、伊藤レポートでは8%以上が推奨水準とされています。",
            "items_used": [
                {
                    "item_name": sources["net_income"]["item_name"],
                    "value": f"{net_inc:,} 百万円",
                    "location": sources["net_income"]["section"],
                    "page": sources["net_income"]["page"]
                },
                {
                    "item_name": sources["equity"]["item_name"],
                    "value": f"{equity:,} 百万円",
                    "location": sources["equity"]["section"],
                    "page": sources["equity"]["page"]
                }
            ]
        },
        "roic": {
            "name": "ROIC (投下資本利益率 - Return on Invested Capital)",
            "key": "roic",
            "value": round(roic, 1),
            "unit": "%",
            "formula_definition": "税引後営業利益 (NOPAT) ÷ 投下資本 (有利子負債 + 自己資本) × 100 (%)",
            "formula_applied": f"(営業利益 {op_inc:,} × (1 - {tax_rate}) = {int(nopat):,} 百万円 ÷ 投下資本: {invested_capital:,} 百万円) × 100 = {roic:.1f}%",
            "evaluation": roic_eval,
            "description": "調達した資本（株主資本＋有利子負債）を本業に投じてどれだけ効率的に税引後利益を稼ぎ出したかを示します。資本コスト（WACC）を上回ることで企業価値を創出します。",
            "items_used": [
                {
                    "item_name": sources["operating_income"]["item_name"] + " (および実効税率30.6%)",
                    "value": f"{op_inc:,} 百万円 (NOPAT: {int(nopat):,} 百万円)",
                    "location": sources["operating_income"]["section"],
                    "page": sources["operating_income"]["page"]
                },
                {
                    "item_name": sources["interest_bearing_debt"]["item_name"] + " ＋ " + sources["equity"]["item_name"],
                    "value": f"投下資本合計: {invested_capital:,} 百万円 (有利子負債: {debt:,} 百万円, 自己資本: {equity:,} 百万円)",
                    "location": sources["interest_bearing_debt"]["section"] + " / " + sources["equity"]["section"],
                    "page": sources["interest_bearing_debt"]["page"] + " / " + sources["equity"]["page"]
                }
            ]
        },
        "pbr": {
            "name": "PBR (株価純資産倍率 - Price Book-value Ratio)",
            "key": "pbr",
            "value": round(pbr, 2),
            "unit": "倍",
            "formula_definition": "株価 ÷ 1株当たり純資産額 (BPS)",
            "formula_applied": f"{stock_price:,} 円 ÷ {bps:,.2f} 円 = {pbr:.2f}倍",
            "evaluation": pbr_eval,
            "description": "現在の株価が企業の1株当たり純資産（解散価値）の何倍まで買われているかを示す指標。1倍を下回ると解散価値割れとみなされ、東証による資本コスト改善要請（PBR1倍超え改革）の最重要指標となっています。",
            "items_used": [
                {
                    "item_name": sources["stock_price"]["item_name"],
                    "value": f"{stock_price:,} 円",
                    "location": sources["stock_price"]["section"],
                    "page": sources["stock_price"]["page"]
                },
                {
                    "item_name": sources["bps"]["item_name"],
                    "value": f"{bps:,.2f} 円",
                    "location": sources["bps"]["section"],
                    "page": sources["bps"]["page"]
                }
            ]
        },
        "per": {
            "name": "PER (株価収益率 - Price Earnings Ratio)",
            "key": "per",
            "value": round(per, 1),
            "unit": "倍",
            "formula_definition": "株価 ÷ 1株当たり当期純利益 (EPS)",
            "formula_applied": f"{stock_price:,} 円 ÷ {eps:,.2f} 円 = {per:.1f}倍",
            "evaluation": per_eval,
            "description": "株価が1株当たり当期純利益の何倍まで買われているかを示す指標。現在の利益水準で投資資金を何年で回収できるかを表し、企業の将来成長性への期待度や割安度を測る代表格です（日本市場平均は約15倍）。",
            "items_used": [
                {
                    "item_name": sources["stock_price"]["item_name"],
                    "value": f"{stock_price:,} 円",
                    "location": sources["stock_price"]["section"],
                    "page": sources["stock_price"]["page"]
                },
                {
                    "item_name": sources["eps"]["item_name"],
                    "value": f"{eps:,.2f} 円",
                    "location": sources["eps"]["section"],
                    "page": sources["eps"]["page"]
                }
            ]
        },
        "roa": {
            "name": "ROA (総資産利益率 - Return on Assets)",
            "key": "roa",
            "value": round(roa, 1),
            "unit": "%",
            "formula_definition": "当期純利益 ÷ 総資産 × 100 (%)",
            "formula_applied": f"({net_inc:,} 百万円 ÷ {assets:,} 百万円) × 100 = {roa:.1f}%",
            "evaluation": roa_eval,
            "description": "負債を含めた会社全体の保有資産を使ってどれだけ効率よく利益を生み出せたかを示す指標です。会社の総合的な資産活用効率を表します（一般に5%以上で良好）。",
            "items_used": [
                {
                    "item_name": sources["net_income"]["item_name"],
                    "value": f"{net_inc:,} 百万円",
                    "location": sources["net_income"]["section"],
                    "page": sources["net_income"]["page"]
                },
                {
                    "item_name": sources["total_assets"]["item_name"],
                    "value": f"{assets:,} 百万円",
                    "location": sources["total_assets"]["section"],
                    "page": sources["total_assets"]["page"]
                }
            ]
        },
        "operating_margin": {
            "name": "売上高営業利益率 (Operating Margin)",
            "key": "operating_margin",
            "value": round(op_margin, 1),
            "unit": "%",
            "formula_definition": "営業利益 ÷ 売上収益（売上高） × 100 (%)",
            "formula_applied": f"({op_inc:,} 百万円 ÷ {rev:,} 百万円) × 100 = {op_margin:.1f}%",
            "evaluation": op_margin_eval,
            "description": "売上高に対して本業の営業活動でどれだけ利益を残せたかを示す収益性指標。ビジネスモデルの競争優位性や製品・サービスの付加価値の高さを反映します。",
            "items_used": [
                {
                    "item_name": sources["operating_income"]["item_name"],
                    "value": f"{op_inc:,} 百万円",
                    "location": sources["operating_income"]["section"],
                    "page": sources["operating_income"]["page"]
                },
                {
                    "item_name": sources["revenue"]["item_name"],
                    "value": f"{rev:,} 百万円",
                    "location": sources["revenue"]["section"],
                    "page": sources["revenue"]["page"]
                }
            ]
        }
    }
    return metrics

def generate_quiz(companies: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate a 3-choice quiz from random company and random metric.
    Includes equity_ratio, roe, roic, roa, operating_margin, pbr, per
    """
    company = random.choice(companies)
    metrics = calculate_metrics(company)
    
    metric_keys = ["equity_ratio", "roe", "roic", "roa", "operating_margin", "pbr", "per"]
    target_key = random.choice(metric_keys)
    target_metric = metrics[target_key]
    correct_value = target_metric["value"]
    unit = target_metric["unit"]

    # Generate 2 plausible distractors
    distractors = set()
    if unit == "倍":
        if target_key == "pbr":
            offsets = [-0.45, 0.65, -0.8, 1.2]
            for off in offsets:
                val = round(max(0.4, correct_value + off), 2)
                if val != correct_value:
                    distractors.add(val)
        else: # per
            offsets = [-5.2, 7.8, -9.4, 12.5]
            for off in offsets:
                val = round(max(3.0, correct_value + off), 1)
                if val != correct_value:
                    distractors.add(val)
    else: # %
        offsets = [random.choice([-1, 1]) * random.uniform(2.5, 6.0), random.choice([-1, 1]) * random.uniform(6.5, 12.0)]
        for off in offsets:
            val = round(max(0.5, correct_value + off), 1)
            if val != correct_value:
                distractors.add(val)

    while len(distractors) < 2:
        val = round(max(0.4, correct_value + random.choice([-1, 1]) * random.uniform(1.5, 5.0)), 2 if unit == "倍" and target_key == "pbr" else 1)
        if val != correct_value:
            distractors.add(val)

    options = [correct_value] + list(distractors)[:2]
    random.shuffle(options)

    question_text = f"【{company['name']}（コード: {company['code']}）】の最新有価証券報告書（{company['fiscal_period']}）の情報をもとに、以下の指標を計算してください。"

    return {
        "company_id": company["id"],
        "company_name": company["name"],
        "code": company["code"],
        "fiscal_period": company["fiscal_period"],
        "metric_key": target_key,
        "metric_name": target_metric["name"],
        "question_title": f"Q. 【{company['short_name']}】の「{target_metric['name']}」として正しいものはどれ？",
        "question_lead": question_text,
        "hint_items": target_metric["items_used"],
        "options": [f"{opt}{unit}" for opt in options],
        "correct_option": f"{correct_value}{unit}",
        "correct_value": correct_value,
        "unit": unit,
        "explanation": {
            "formula_definition": target_metric["formula_definition"],
            "formula_applied": target_metric["formula_applied"],
            "description": target_metric["description"],
            "evaluation": target_metric["evaluation"],
            "source_details": target_metric["items_used"],
            "edinet_url": company.get("edinet_url", "https://disclosure2.edinet-fsa.go.jp/"), "edinet_code": company.get("edinet_code", ""), "disclosure_url": company.get("disclosure_url", "")
        }
    }
