from __future__ import annotations
from pydantic import BaseModel
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .show import Show
    from .episode import Episode


class Season(BaseModel):
    id: int | str
    title: str
    episodes: Optional[List[Episode]] = None
    show: Show

    @property
    def number(self) -> int:
        try:
            return int(''.join(filter(str.isdigit, self.title)))
        except Exception:
            return 0
