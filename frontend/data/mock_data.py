mock_data = {
    "company": "ABC Technologies Pvt Ltd",
    "sector": "Healthcare",

    "decision": "GO",
    "confidence": 94,

    "metrics": {
        "Revenue": "$230M",
        "EBITDA": "$48M",
        "Growth": "18%",
        "Industry": "Healthcare",
        "Risk": "Low"
    },

    "verification": {
        "Revenue": {
            "page": 14,
            "hash": "8ab93fd7a29ef113",
            "source": "Revenue increased to $230 Million in FY24.",
            "verified": True
        },

        "EBITDA": {
            "page": 18,
            "hash": "7fd12abce99a721",
            "source": "EBITDA reached $48 Million.",
            "verified": True
        },

        "Growth": {
            "page": 20,
            "hash": "",
            "source": "",
            "verified": False
        }
    },

    "executive_summary": """
ABC Technologies has demonstrated strong financial performance with
consistent revenue growth and healthy EBITDA margins.

The company operates in the Healthcare sector with low operational
risk and stable year-over-year growth.

Based on the extracted financial metrics and verification results,
the AI recommends proceeding with the investment opportunity.
"""
}