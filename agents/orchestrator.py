from extractor_agent import extract_metrics
from validator import validate_metrics
from screener_agent import screen_deal
from memo_agent import generate_memo


def process_document(doc_id):
    # Step 1: Extract metrics
    data = extract_metrics(doc_id)

    # Step 2: Validate extraction
    if not validate_metrics(data):
        return {
            "status": "FAILED",
            "reason": "hallucination_blocked"
        }

    # Step 3: Screen the deal
    screening = screen_deal(data)

    # Step 4: Generate investment memo
    memo = generate_memo(screening)

    return {
        "status": "SUCCESS",
        "memo": memo
    }


if __name__ == "__main__":
    result = process_document("doc_1")
    print(result)