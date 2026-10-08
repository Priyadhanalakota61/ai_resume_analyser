from app.scoring import calculate_match_score


def test_score_counts_each_requirement_equally():
    requirements = [
        {"status": "matched"},
        {"status": "not_found"},
        {"status": "matched"},
    ]

    assert calculate_match_score(requirements) == 67


def test_score_is_not_calculated_without_requirements():
    assert calculate_match_score([]) is None


def test_score_is_zero_when_no_requirement_has_resume_evidence():
    requirements = [
        {"status": "not_found"},
        {"status": "not_found"},
    ]

    assert calculate_match_score(requirements) == 0


def test_score_is_100_when_all_requirements_have_resume_evidence():
    requirements = [
        {"status": "matched"},
        {"status": "matched"},
    ]

    assert calculate_match_score(requirements) == 100
