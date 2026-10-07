import pytest
from pydantic import ValidationError

from app.scales import Scale, load_scales
from app.scoring import AnswerValidationError, reverse, score, validate_answers


@pytest.mark.parametrize(
    ("value", "low", "high", "expected"),
    [(1, 1, 5, 5), (2, 1, 5, 4), (3, 1, 5, 3), (5, 1, 5, 1), (0, 0, 4, 4), (4, 0, 4, 0)],
)
def test_reverse(value, low, high, expected):
    assert reverse(value, low, high) == expected


def test_score_mixed_keyed_and_reverse_items(mini_scale):
    answers = {"e1": 4, "e2": 2, "a1": 5, "a2": 1}
    assert score(mini_scale, answers) == {"agreeableness": 5.0, "extraversion": 4.0}


def test_score_rounds_to_two_decimals():
    scale = Scale(
        id="three",
        name="Three",
        source="test",
        response_min=1,
        response_max=5,
        items=[{"id": f"i{n}", "text": "x", "subscale": "s"} for n in range(3)],
    )
    assert score(scale, {"i0": 1, "i1": 1, "i2": 2}) == {"s": 1.33}


def test_validate_reports_every_problem_at_once(mini_scale):
    answers = {"e1": 4, "a1": 7, "a2": 1, "x9": 3}  # e2 missing, x9 unknown, a1 out of range
    with pytest.raises(AnswerValidationError) as exc_info:
        validate_answers(mini_scale, answers)
    assert exc_info.value.errors == [
        {"item": "e2", "error": "missing"},
        {"item": "x9", "error": "unknown item"},
        {"item": "a1", "error": "value 7 outside 1-5"},
    ]


def test_validate_accepts_complete_answers(mini_scale):
    validate_answers(mini_scale, {"e1": 1, "e2": 5, "a1": 3, "a2": 3})


BASE = {"id": "demo", "name": "Demo", "source": "test", "response_min": 1, "response_max": 5}


def test_scale_rejects_duplicate_item_ids():
    items = [{"id": "q1", "text": "a", "subscale": "s"}, {"id": "q1", "text": "b", "subscale": "s"}]
    with pytest.raises(ValidationError, match="duplicate item ids: q1"):
        Scale(**BASE, items=items)


def test_scale_rejects_min_not_below_max():
    with pytest.raises(ValidationError, match="response_min must be less"):
        Scale(**{**BASE, "response_max": 1}, items=[{"id": "q1", "text": "a", "subscale": "s"}])


def test_scale_rejects_label_outside_range():
    with pytest.raises(ValidationError, match="outside the response range"):
        Scale(
            **BASE,
            response_labels={"6": "Too high"},
            items=[{"id": "q1", "text": "a", "subscale": "s"}],
        )


def test_load_scales_rejects_duplicate_scale_ids(tmp_path):
    body = (
        '{"id": "same", "name": "A", "source": "t", "response_min": 1, "response_max": 5,'
        ' "items": [{"id": "q1", "text": "a", "subscale": "s"}]}'
    )
    (tmp_path / "a.json").write_text(body)
    (tmp_path / "b.json").write_text(body)
    with pytest.raises(ValueError, match="duplicate scale id"):
        load_scales(tmp_path)


def test_load_scales_sets_version(mini_scale):
    assert len(mini_scale.version) == 12
