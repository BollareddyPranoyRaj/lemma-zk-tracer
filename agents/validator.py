def validate_metrics(data):
    metrics = [
        "revenue",
        "ebitda",
        "yoy_growth",
        "customer_concentration",
        "legal_risks",
    ]

    errors = []

    for metric in metrics:
        if metric not in data:
            errors.append(f"Missing metric: {metric}")
            continue

        item = data[metric]

        if not isinstance(item, dict):
            errors.append(f"{metric} must be an object")
            continue

        for field in ("value", "source_text", "source_hash"):
            if field not in item:
                errors.append(f"{metric}: missing {field}")

        if item.get("value") is not None:
            source_text = item.get("source_text")
            if not isinstance(source_text, str) or not source_text.strip():
                errors.append(
                    f"{metric}: source_text required when value is present"
                )

    return {
        "valid": len(errors) == 0,
        "errors": errors,
    }