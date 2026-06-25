import hashlib

def create_hash(text):
    return hashlib.sha256(text.encode()).hexdigest()

def extract_metrics(doc_id):
    revenue_source="Revenue was $10M"
    ebitda_source="EBITDA was $6M"
    yoy_growth_source="YoY Growth was 20%"
    customer_concentration_source="Customer Concentration was 15%"
    legal_risks_source="Legal Risks were Low"
    return{
        "revenue":{
            "value": "$10M",
            "source_text": revenue_source,
            "source_hash": create_hash(revenue_source)
        },

        "ebitda": {
            "value": "$6M",
            "source_text": ebitda_source,
            "source_hash": create_hash(ebitda_source)
        },

        "yoy_growth": {
            "value": "20%",
            "source_text": yoy_growth_source,
            "source_hash": create_hash(yoy_growth_source)
        },

        "customer_concentration": {
            "value": "15%",
            "source_text": customer_concentration_source,
            "source_hash": create_hash(customer_concentration_source)
        },

        "legal_risks": {
            "value": "Low",
            "source_text": legal_risks_source,
            "source_hash": create_hash(legal_risks_source)
        }
    }
