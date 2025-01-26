from __future__ import annotations
from pydantic import BaseModel
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .season import Season


class Show(BaseModel):
    id: int | str
    title: str = ''
    seasons: Optional[List[Season]] = None

    def __str__(self):
        return f"{self.id} - {self.title}"

    def model_post_init(self, __context) -> None:
        if self.seasons:
            for season in self.seasons:
                season.show = self
