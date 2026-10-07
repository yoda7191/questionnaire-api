from collections import defaultdict
from statistics import mean

from app.scales import Scale

class AnswerValidationError(Exception):
    """Raise when answers don't fit the scale. Carries every problem found."""

    def __init__(self, errors: list[dict[str, str]]):
        super().__init__("invalid answers")
        self.errors = errors

def reverse(value: int, low: int, high: int) -> int:
    """Flip a reverse-keyed answer"""
    return low + high - value

def validate_answers(scale: Scale, answers: dict[str, int]) -> None:
    expected = {item.id for item in scale.items}
    errors = [{"item": i, "error": "missing"} for i in sorted(expected - answers.keys())]
    errors += [{"item": i, "error": "unknown item"} for i in sorted(answers.keys() - expected)]
    low, high = scale.response_min, scale.response_max
    for item_id, value in sorted(answers.items()):
        if item_id in expected and not low <= value <= high:
            errors.append({"item": item_id, "error": f"value {value} outside {low}-{high}"})
    if errors:
        raise AnswerValidationError(errors)

def score(scale: Scale, answers: dict[str, int]) -> dict[str, float]:
    """Return the mean of each subscale after reverse scoring, rounded to 2 decimals."""
    validate_answers(scale, answers)
    values: dict[str, list[int]] = defaultdict(list)
    for item in scale.items:
        value = answers[item.id]
        if item.reverse:
            value = reverse(value, scale.response_min, scale.response_max)
        values[item.subscale].append(value)
    return {name: round(mean(vs), 2) for name, vs in sorted(values.items())}