def calculate_match_score(requirements: list[dict]) -> int | None:
    if not requirements:
        return None

    matched = sum(item["status"] == "matched" for item in requirements)
    return round(matched / len(requirements) * 100)
