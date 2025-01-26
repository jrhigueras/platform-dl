from __future__ import annotations
from pydantic import BaseModel, field_validator
from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .season import Season


class Episode(BaseModel):
    id: int | str
    title: str
    description: Optional[str] = None
    url: str | None
    number: int
    season: Season
    download_url: Optional[str] = None

    @field_validator('number', mode='before')
    @staticmethod
    def validate_number(v: Any) -> int:
        if isinstance(v, str):
            try:
                return int(v)
            except Exception:
                return 0
        return v

    def model_post_init(self, __context) -> None:
        if self.number == 0:
            try:
                self.number = int(''.join(filter(str.isdigit, self.title)))
            except Exception:
                self.number = 0
