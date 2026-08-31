from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Player:
    name: str
    avatar_path: Optional[str] = None
    avatar_crop: Optional[dict] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name,
                "avatar_path": self.avatar_path, "avatar_crop": self.avatar_crop}

    @staticmethod
    def from_dict(d: dict) -> "Player":
        return Player(id=d["id"], name=d["name"],
                      avatar_path=d.get("avatar_path"),
                      avatar_crop=d.get("avatar_crop"))
