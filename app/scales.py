import hashlib
from pathlib import Path
from typing import Self

from pydantic import BaseModel, Field, model_validator

class Item(BaseModel):
    id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    subscale: str = Field(min_length=1)
    reverse: bool = False

class Scale(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$")
    name: str
    description: str = ""
    source: str
    instructions: str = ""
    response_min: int
    response_max: int
    response_labels: dict[str, str] = {}
    items: list[Item] = Field(min_length=1)
    version: str = ""

    @model_validator(mode="after")
    def check_consistency(self) -> Self:
        ids = [item.id for item in self.items]
        duplicates = sorted({i for i in ids if ids.count(i) > 1})
        if duplicates:
            raise ValueError(f"duplicate item ids: {', '.join(duplicates)}")
        if self.response_min >= self.response_max:
            raise ValueError("response_min must be less than response_max")
        for key in self.response_labels:
            if not (key.isdigit() and self.response_min <= int(key) <= self.response_max):
                raise ValueError(f"label key {key!r} os outside the response range")
        return self

    @property
    def subscales(self) -> list[str]:
        return sorted({item.subscale for item in self.items})

def load_scales(directory: Path) -> dict[str, Scale]:
    """Load and validate every *.json scale file in a directory."""
    scales: dict[str, Scale] = {}
    for path in sorted(Path(directory).glob("*.json")):
        raw = path.read_text(encoding="utf-8")
        try:
            scale = Scale.model_validate_json(raw)
        except ValueError as e:
            raise ValueError(f"invalid scale file {path.name}: {e}") from e
        if scale.id in scales:
            raise ValueError(f"duplicate scale id {scale.id!r} in {path.name}")
        scale.version = hashlib.sha256(raw.encode()).hexdigest()[:12]
        scales[scale.id] = scale
    return scales