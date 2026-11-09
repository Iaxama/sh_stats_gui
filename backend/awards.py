from __future__ import annotations
import math
from typing import Dict, List

from models.game import Game

MIN_GAMES_FOR_RATE_AWARDS = 5

# (key, stat, direction, needs_min_games). Titles/descriptions live in the frontend.
AWARD_RULES = [
    ("most_games", "games", "max", False),
    ("most_wins", "wins", "max", False),
    ("highest_win_pct", "win_pct", "max", True),
    ("lowest_win_pct", "win_pct", "min", True),
    ("most_deaths", "deaths", "max", False),
    ("most_snipes", "snipes", "max", False),
    ("most_liberal_games", "lib_games", "max", False),
    ("most_liberal_wins", "lib_wins", "max", False),
    ("most_fascist_games", "fas_games", "max", False),
    ("most_fascist_wins", "fas_wins", "max", False),
    ("most_hitler_games", "hit_games", "max", False),
    ("most_hitler_wins", "hit_wins", "max", False),
    ("most_dumbo", "dumbo", "max", False),
    ("most_dictator", "dictator", "max", False),
]


def _won(role: str, winning_team: str) -> bool:
    return (role == "liberal" and winning_team == "liberal") or (
        role in ("fascist", "hitler") and winning_team == "fascist"
    )


def compute_player_stats(games: List[Game]) -> Dict[str, dict]:
    stats: Dict[str, dict] = {}

    def row(pid: str) -> dict:
        return stats.setdefault(pid, {
            "games": 0, "wins": 0, "deaths": 0, "snipes": 0, "dumbo": 0, "dictator": 0,
            "lib_games": 0, "lib_wins": 0, "fas_games": 0, "fas_wins": 0,
            "hit_games": 0, "hit_wins": 0,
        })

    for game in games:
        roles = {r.player_id: r.role for r in game.players}
        if game.sniper_id and game.sniper_id in roles:
            row(game.sniper_id)["snipes"] += 1
        chooser_role = roles.get(game.hitler_chooser_id) if game.hitler_chooser_id else None
        if chooser_role == "liberal":
            row(game.hitler_chooser_id)["dumbo"] += 1
        elif chooser_role == "fascist":
            row(game.hitler_chooser_id)["dictator"] += 1
        for r in game.players:
            s = row(r.player_id)
            won = _won(r.role, game.winning_team)
            s["games"] += 1
            s["wins"] += won
            s["deaths"] += bool(r.died)
            prefix = {"liberal": "lib", "fascist": "fas", "hitler": "hit"}.get(r.role)
            if prefix:
                s[f"{prefix}_games"] += 1
                s[f"{prefix}_wins"] += won

    for pid, s in stats.items():
        s["win_pct"] = s["wins"] / s["games"] * 100 if s["games"] else 0
    return stats


def compute_awards(games: List[Game]) -> List[dict]:
    """Return one entry per award: {key, value, winners: [player_id, ...]} (ties included)."""
    stats = compute_player_stats(games)
    awards = []
    for key, stat, direction, needs_min in AWARD_RULES:
        pool = {
            pid: s[stat] for pid, s in stats.items()
            if s["games"] > 0 and (not needs_min or s["games"] >= MIN_GAMES_FOR_RATE_AWARDS)
        }
        if not pool:
            continue
        best = max(pool.values()) if direction == "max" else min(pool.values())
        if direction == "max" and best <= 0:
            continue
        winners = sorted(pid for pid, v in pool.items() if math.isclose(v, best, abs_tol=1e-9))
        awards.append({"key": key, "value": round(best, 2), "winners": winners})
    return awards
