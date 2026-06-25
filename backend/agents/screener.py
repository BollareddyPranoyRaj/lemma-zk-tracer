"""
backend/agents/screener.py
──────────────────────────
Screener Agent: Evaluates extracted metrics against the investment mandate.
"""
from __future__ import annotations

import logging
import re
from backend.models import (
    FinancialMetrics,
    MetricEvidence,
    ScreenerMandate,
    ScreenerFlag,
    ScreenerResult,
    ScreenDecision
)

logger = logging.getLogger(__name__)


# ─── Value Parsing Helpers ────────────────────────────────────────────────────

def parse_numeric_millions(val_str: str | None) -> float | None:
    """
    Parses a money/numeric string and converts it to a float representing Millions.
    Handles: '$10.5M', '$105,000,000', '5.2 million', '12.4', etc.
    """
    if not val_str:
        return None
    
    # Remove currency symbols and formatting commas
    s = val_str.lower().replace("$", "").replace(",", "").strip()
    
    # Extract first decimal or integer pattern
    match = re.search(r"[-+]?\d*\.\d+|\d+", s)
    if not match:
        return None
    
    val = float(match.group())
    
    # Check for multiplier keywords or suffix letters
    if "billion" in s or re.search(r"\bb\b", s) or s.endswith("b"):
        val *= 1000.0  # 1 Billion = 1000 Million
    elif "million" in s or re.search(r"\bm\b", s) or s.endswith("m"):
        val *= 1.0     # Already in Millions
    elif "thousand" in s or re.search(r"\bk\b", s) or s.endswith("k"):
        val *= 0.001   # 1 Thousand = 0.001 Million
    else:
        # If no units are given, check if it looks like an absolute value
        # e.g., 105,000,000 instead of 105
        if val > 100000:
            val /= 1000000.0  # convert absolute to millions
            
    return val


def parse_percentage(val_str: str | None) -> float | None:
    """
    Parses a percentage string and returns it as a float (e.g. '15%' -> 15.0).
    """
    if not val_str:
        return None
    
    s = val_str.lower().replace("%", "").strip()
    match = re.search(r"[-+]?\d*\.\d+|\d+", s)
    if not match:
        return None
    
    val = float(match.group())
    # If the percentage was written as a fraction like 0.15 and did not have a % sign
    if val < 1.0 and "%" not in val_str:
        val *= 100.0
        
    return val


# ─── Screener Implementation ──────────────────────────────────────────────────

class ScreenerAgent:
    """
    Evaluates FinancialMetrics against a ScreenerMandate.
    Computes passing status for individual gates and compiles the ScreenerResult.
    """

    def screen(self, metrics: FinancialMetrics, mandate: ScreenerMandate) -> ScreenerResult:
        flags: list[ScreenerFlag] = []
        
        passed_count = 0
        failed_count = 0
        na_count = 0

        # ── 1. Revenue Gate ───────────────────────────────────────────────────
        rev_evidence = metrics.revenue
        rev_val = parse_numeric_millions(rev_evidence.value if rev_evidence else None)
        if rev_val is None:
            na_count += 1
            flags.append(ScreenerFlag(
                gate="Revenue",
                passed=False,
                required=f">= ${mandate.min_revenue_m}M",
                actual=None,
                reason="Metric missing or could not be parsed."
            ))
        else:
            passed = rev_val >= mandate.min_revenue_m
            if passed:
                passed_count += 1
            else:
                failed_count += 1
            flags.append(ScreenerFlag(
                gate="Revenue",
                passed=passed,
                required=f">= ${mandate.min_revenue_m}M",
                actual=f"${rev_val:.2f}M",
                reason=f"Revenue of ${rev_val:.2f}M " + ("meets" if passed else "fails to meet") + f" the minimum requirement of ${mandate.min_revenue_m}M."
            ))

        # ── 2. EBITDA Gate ────────────────────────────────────────────────────
        eb_evidence = metrics.ebitda
        eb_val = parse_numeric_millions(eb_evidence.value if eb_evidence else None)
        if eb_val is None:
            na_count += 1
            flags.append(ScreenerFlag(
                gate="EBITDA",
                passed=False,
                required=f">= ${mandate.min_ebitda_m}M",
                actual=None,
                reason="Metric missing or could not be parsed."
            ))
        else:
            passed = eb_val >= mandate.min_ebitda_m
            if passed:
                passed_count += 1
            else:
                failed_count += 1
            flags.append(ScreenerFlag(
                gate="EBITDA",
                passed=passed,
                required=f">= ${mandate.min_ebitda_m}M",
                actual=f"${eb_val:.2f}M",
                reason=f"EBITDA of ${eb_val:.2f}M " + ("meets" if passed else "fails to meet") + f" the minimum requirement of ${mandate.min_ebitda_m}M."
            ))

        # ── 3. EBITDA Margin Gate ─────────────────────────────────────────────
        margin_evidence = metrics.ebitda_margin
        margin_val = parse_percentage(margin_evidence.value if margin_evidence else None)
        if margin_val is None:
            na_count += 1
            flags.append(ScreenerFlag(
                gate="EBITDA Margin",
                passed=False,
                required=f">= {mandate.min_ebitda_margin_pct}%",
                actual=None,
                reason="Metric missing or could not be parsed."
            ))
        else:
            passed = margin_val >= mandate.min_ebitda_margin_pct
            if passed:
                passed_count += 1
            else:
                failed_count += 1
            flags.append(ScreenerFlag(
                gate="EBITDA Margin",
                passed=passed,
                required=f">= {mandate.min_ebitda_margin_pct}%",
                actual=f"{margin_val:.1f}%",
                reason=f"EBITDA Margin of {margin_val:.1f}% " + ("meets" if passed else "fails to meet") + f" the minimum requirement of {mandate.min_ebitda_margin_pct}%."
            ))

        # ── 4. YoY Revenue Growth Gate ────────────────────────────────────────
        growth_evidence = metrics.yoy_growth
        growth_val = parse_percentage(growth_evidence.value if growth_evidence else None)
        if growth_val is None:
            na_count += 1
            flags.append(ScreenerFlag(
                gate="YoY Growth",
                passed=False,
                required=f">= {mandate.min_yoy_growth_pct}%",
                actual=None,
                reason="Metric missing or could not be parsed."
            ))
        else:
            passed = growth_val >= mandate.min_yoy_growth_pct
            if passed:
                passed_count += 1
            else:
                failed_count += 1
            flags.append(ScreenerFlag(
                gate="YoY Growth",
                passed=passed,
                required=f">= {mandate.min_yoy_growth_pct}%",
                actual=f"{growth_val:.1f}%",
                reason=f"YoY Growth of {growth_val:.1f}% " + ("meets" if passed else "fails to meet") + f" the minimum requirement of {mandate.min_yoy_growth_pct}%."
            ))

        # ── 5. Customer Concentration Gate ────────────────────────────────────
        conc_evidence = metrics.customer_concentration
        conc_val = parse_percentage(conc_evidence.value if conc_evidence else None)
        if conc_val is None:
            na_count += 1
            flags.append(ScreenerFlag(
                gate="Customer Concentration",
                passed=False,
                required=f"<= {mandate.max_customer_concentration_pct}%",
                actual=None,
                reason="Metric missing or could not be parsed."
            ))
        else:
            # Note: lower concentration is better
            passed = conc_val <= mandate.max_customer_concentration_pct
            if passed:
                passed_count += 1
            else:
                failed_count += 1
            flags.append(ScreenerFlag(
                gate="Customer Concentration",
                passed=passed,
                required=f"<= {mandate.max_customer_concentration_pct}%",
                actual=f"{conc_val:.1f}%",
                reason=f"Customer concentration of {conc_val:.1f}% " + ("is within" if passed else "exceeds") + f" the maximum allowance of {mandate.max_customer_concentration_pct}%."
            ))

        # ── 6. Legal Risks Gate ───────────────────────────────────────────────
        risk_evidence = metrics.legal_risks
        risk_val = (risk_evidence.value if risk_evidence else None)
        allowed_risks_lower = [r.lower() for r in mandate.allowed_legal_risk_levels]
        if risk_val is None:
            na_count += 1
            flags.append(ScreenerFlag(
                gate="Legal Risks",
                passed=False,
                required="in [" + ", ".join(mandate.allowed_legal_risk_levels) + "]",
                actual=None,
                reason="Metric missing or could not be parsed."
            ))
        else:
            passed = risk_val.strip().lower() in allowed_risks_lower
            if passed:
                passed_count += 1
            else:
                failed_count += 1
            flags.append(ScreenerFlag(
                gate="Legal Risks",
                passed=passed,
                required="in [" + ", ".join(mandate.allowed_legal_risk_levels) + "]",
                actual=risk_val,
                reason=f"Legal risk level '{risk_val}' " + ("is acceptable" if passed else "is unacceptable") + f" under the mandate allowed levels: {mandate.allowed_legal_risk_levels}."
            ))

        # ── Determine Overall Decision ───────────────────────────────────────
        # Criteria:
        # - Any explicit failure (passed=False and actual is not None) -> NO_GO
        # - Any missing critical data (passed=False and actual is None) and no explicit failures -> INSUFFICIENT_DATA
        # - All gates pass -> GO
        
        has_failed_gate = False
        has_missing_gate = False

        for f in flags:
            if not f.passed:
                if f.actual is None:
                    has_missing_gate = True
                else:
                    has_failed_gate = True

        if has_failed_gate:
            decision = ScreenDecision.NO_GO
        elif has_missing_gate:
            decision = ScreenDecision.INSUFFICIENT_DATA
        else:
            decision = ScreenDecision.GO

        logger.info("Screening finished with decision=%s (passed=%d, failed=%d, na=%d)", 
                    decision, passed_count, failed_count, na_count)

        return ScreenerResult(
            decision=decision,
            flags=flags,
            passed_count=passed_count,
            failed_count=failed_count,
            na_count=na_count
        )
