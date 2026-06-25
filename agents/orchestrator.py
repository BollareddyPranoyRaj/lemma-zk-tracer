from extractor_agent import extract_metrics
from validator import validate_metrics
from screener_agent import screen_deal

def process_document(doc_id):
    data=extract_metrics(doc_id)

    if not validate_metrics(data):
        return "hallucination_blocked"
    decision = screen_deal(data)
    return decision

print(process_document("doc_1"))