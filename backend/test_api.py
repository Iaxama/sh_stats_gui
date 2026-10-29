import json
import os
import shutil
import tempfile

import pytest

import storage


@pytest.fixture()
def client(monkeypatch):
    tmp = tempfile.mkdtemp()
    monkeypatch.setattr(storage, "DATA_DIR", tmp)
    monkeypatch.setattr(storage, "AVATARS_DIR", os.path.join(tmp, "assets", "avatars"))
    monkeypatch.setattr(storage, "PLAYERS_FILE", os.path.join(tmp, "players.json"))
    monkeypatch.setattr(storage, "GAMES_FILE", os.path.join(tmp, "games.json"))
    monkeypatch.setattr(storage, "SEASONS_FILE", os.path.join(tmp, "seasons.json"))
    from backend.app import create_app
    yield create_app().test_client()
    shutil.rmtree(tmp)


def _game(ids, win="fascist", cond="hitler_elected", **extra):
    roles = ["liberal", "liberal", "liberal", "fascist", "hitler"]
    return {"players": [{"player_id": i, "role": r, "died": False} for i, r in zip(ids, roles)],
            "winning_team": win, "winning_condition": cond, **extra}


def test_season_lifecycle(client):
    ids = [client.post("/api/players", json={"name": f"p{i}"}).get_json()["id"] for i in range(5)]
    assert client.post("/api/games", json=_game(ids)).status_code == 400
    assert client.post("/api/games", json=_game(ids, hitler_chooser_id=ids[4])).status_code == 400
    r = client.post("/api/games", json=_game(ids, hitler_chooser_id=ids[0]))
    assert r.status_code == 201
    seasons = client.get("/api/seasons").get_json()
    assert len(seasons) == 1 and r.get_json()["season_id"] == seasons[0]["id"]

    seasons = client.post("/api/seasons", json={"retire_ids": [ids[1]]}).get_json()
    assert [s["number"] for s in seasons] == [1, 2]
    assert seasons[0]["end_date"] and seasons[1]["end_date"] is None
    keys = {a["key"]: a for a in seasons[0]["awards"]}
    assert keys["most_dumbo"]["winners"] == [ids[0]]
    assert "highest_elo" not in keys  # below 5 games
    retired = [p["id"] for p in client.get("/api/players").get_json() if p["retired"]]
    assert retired == [ids[1]]
    g2 = client.post("/api/games", json=_game(ids, win="liberal", cond="policies_enacted")).get_json()
    assert g2["season_id"] == seasons[1]["id"]


def test_season_end_for():
    from datetime import datetime, timezone
    assert storage.season_end_for(datetime(2026, 11, 1, tzinfo=timezone.utc)).isoformat().startswith("2027-01-31")
    assert storage.season_end_for(datetime(2026, 10, 21, tzinfo=timezone.utc), 1).isoformat().startswith("2026-10-31")
