from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from typing import List, Literal, Optional


Role = Literal["liberal", "fascist", "hitler"]
WinningTeam = Literal["liberal", "fascist"]
WinningCondition = Literal["policies_enacted", "hitler_elected", "hitler_executed"]


@dataclass
class PlayerResult:
    player_id: str
    role: Role
    died: bool

    def to_dict(self) -> dict:
        return {"player_id": self.player_id, "role": self.role, "died": self.died}

    @staticmethod
    def from_dict(d: dict) -> "PlayerResult":
        return PlayerResult(player_id=d["player_id"], role=d["role"], died=d["died"])


@dataclass
class Game:
    players: List[PlayerResult]
    winning_team: WinningTeam
    winning_condition: WinningCondition
    date: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "date": self.date,
            "players": [p.to_dict() for p in self.players],
            "winning_team": self.winning_team,
            "winning_condition": self.winning_condition,
        }

    @staticmethod
    def from_dict(d: dict) -> "Game":
        return Game(
            id=d["id"],
            date=d["date"],
            players=[PlayerResult.from_dict(p) for p in d["players"]],
            winning_team=d["winning_team"],
            winning_condition=d["winning_condition"],
        )
