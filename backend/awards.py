from __future__ import annotations
import math
from datetime import datetime
from typing import Dict, Iterable, List

from models.game import Game

INITIAL_ELO = 1500
ELO_SCALE = 400
ELO_K_FACTOR = 64
MIN_GAMES_FOR_RATE_AWARDS = 5

# (key, stat, direction, needs_min_games). Titles/descriptions live in the frontend.
AWARD_RULES = [
    ("most_games", "games", "max", False),
    ("least_games", "games", "min", False),
    ("most_wins", "wins", "max", False),
    ("highest_win_pct", "win_pct", "max", True),
    ("lowest_win_pct", "win_pct", "min", True),
    ("highest_elo", "elo", "max", True),
    ("lowest_elo", "elo", "min", True),
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


def _sort_key(game: Game, index: int):
    try:
        t = datetime.fromisoformat(game.date.replace("Z", "+00:00")).timestamp()
    except (ValueError, AttributeError):
        t = math.inf
    return (t, game.id or "", index)


def _won(role: str, winning_team: str) -> bool:
    return (role == "liberal" and winning_team == "liberal") or (
        role in ("fascist", "hitler") and winning_team == "fascist"
    )


def compute_elo(games: Iterable[Game]) -> Dict[str, float]:
    ordered = [g for _, g in sorted(((_sort_key(g, i), g) for i, g in enumerate(games)), key=lambda x: x[0])]
    ratings: Dict[str, float] = {}
    for game in ordered:
        lib, fas, seen = [], [], set()
        for r in game.players:
            if r.player_id in seen:
                continue
            if r.role == "liberal":
                lib.append(r.player_id)
            elif r.role in ("fascist", "hitler"):
                fas.append(r.player_id)
            else:
                continue
            seen.add(r.player_id)
            ratings.setdefault(r.player_id, INITIAL_ELO)
        if not lib or not fas or game.winning_team not in ("liberal", "fascist"):
            continue
        lib_r = sum(ratings[p] for p in lib) / len(lib)
        fas_r = sum(ratings[p] for p in fas) / len(fas)
        expected = 1 / (1 + 10 ** ((fas_r - lib_r) / ELO_SCALE))
        surprise = (1 if game.winning_team == "liberal" else 0) - expected
        n = len(lib) + len(fas)
        for p in lib:
            ratings[p] += ELO_K_FACTOR * surprise * len(fas) / n
        for p in fas:
            ratings[p] -= ELO_K_FACTOR * surprise * len(lib) / n
    return ratings


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

    elo = compute_elo(games)
    for pid, s in stats.items():
        s["win_pct"] = s["wins"] / s["games"] * 100 if s["games"] else 0
        s["elo"] = elo.get(pid, INITIAL_ELO)
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
