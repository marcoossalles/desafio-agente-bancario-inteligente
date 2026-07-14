import pytest

from app.services.score_service import ScoreService


class CustomerRepositoryStub:
    pass


def test_score_is_limited_to_valid_range():
    service = ScoreService(CustomerRepositoryStub())

    assert service.calculate_score(100_000, "formal", 0, 0, False) == 1000
    assert service.calculate_score(0, "desempregado", 10_000, 8, True) == 0


def test_score_uses_expenses_plus_one_formula_from_challenge():
    service = ScoreService(CustomerRepositoryStub())

    score = service.calculate_score(1000, "formal", 99, 0, False)

    assert score == 800


def test_score_rejects_invalid_interview_data():
    service = ScoreService(CustomerRepositoryStub())

    with pytest.raises(ValueError, match="dependentes"):
        service.calculate_score(1000, "formal", 500, -1, False)
