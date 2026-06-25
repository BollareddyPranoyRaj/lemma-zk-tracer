def generate_memo(screening):
    return {
        "company": "Apple Inc.",
        "decision": screening["decision"],
        "score": screening["score"],
        "summary": screening["summary"],
        "reasons": screening["reasons"],
        "metrics": screening["metrics"]
    }