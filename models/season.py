from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Season:
    number: int
    start_date: str
    scheduled_end: str
    end_date: Optional[str] = None
    awards: Optional[List[dict]] = None
    name: str = ""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self) -> None:
        if not self.name:
            self.name = f"Season {self.number}"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "number": self.number,
            "name": self.name,
            "start_date": self.start_date,
            "scheduled_end": self.scheduled_end,
            "end_date": self.end_date,
            "awards": self.awards,
        }

    @staticmethod
    def from_dict(d: dict) -> "Season":
        return Season(
            id=d["id"],
            number=d["number"],
            name=d.get("name", ""),
            start_date=d["start_date"],
            scheduled_end=d["scheduled_end"],
            end_date=d.get("end_date"),
            awards=d.get("awards"),
        )
