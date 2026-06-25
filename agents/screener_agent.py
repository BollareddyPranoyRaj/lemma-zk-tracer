import subprocess
import json
import re


def screen_deal(data):
    revenue = data["revenue"]["value"]
    ebitda = data["ebitda"]["value"]
    yoy_growth = data["yoy_growth"]["value"]
    customer = data["customer_concentration"]["value"]
    legal = data["legal_risks"]["value"]

    prompt = f"""Revenue: {revenue}
EBITDA: {ebitda}
YoY Growth: {yoy_growth}
Customer Concentration: {customer}
Legal Risks: {legal}
"""

    result = subprocess.run(
        [
            "lemma",
            "agents",
            "run",
            "investment_analyst",
            prompt,
        ],
        capture_output=True,
        text=True,
    )

    output = result.stdout
    print(output)

    match = re.search(r'"output"\s*:\s*(\{.*\})\s*\}\s*\}\s*COMPLETED', output, re.DOTALL)
    if not match:
        raise ValueError("Could not extract JSON output from Lemma response")

    screening = json.loads(match.group(1))

    normalized = {}
    for key, value in screening.items():
        if isinstance(value, list):
            value = [item.replace("</item>", "").strip() for item in value]
        normalized[key.strip()] = value

    return {
        "decision": normalized.get("decision"),
        "summary": normalized.get("summary"),
        "confidence": normalized.get("confidence"),
        "strengths": normalized.get("strengths", []),
        "risks": normalized.get("risks", []),
        "score": round(normalized.get("confidence", 0) * 100),
        "reasons": normalized.get("strengths", []) + normalized.get("risks", []),
        "metrics": {
            "revenue": revenue,
            "ebitda": ebitda,
            "customer_concentration": customer,
            "legal_risks": legal,
        },
    }