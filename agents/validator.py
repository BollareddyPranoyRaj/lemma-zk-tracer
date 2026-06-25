def validate_metrics(data):
    metrics = [
        "revenue",
        "ebitda",
        "yoy_growth",
        "customer_concentration",
        "legal_risks"
    ]
    for metric in metrics:
        if metric not in data:
            return False
        if "source_hash" not in data[metric]:
            return False
    return True