from __future__ import annotations
from collections import defaultdict

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QFrame, QPushButton, QSizePolicy,
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QPixmap

import storage
from ui.avatar import make_circular_pixmap
from ui.theme import GOLD, TEXT, TEXT_DIM, RED, SURFACE, CARD, BORDER


def _pct(wins: int, total: int) -> str:
    return f"{wins / total * 100:.0f}%" if total else "—"


class _SortItem(QTableWidgetItem):
    """QTableWidgetItem that sorts by a numeric key, not display text."""
    def __init__(self, display: str, sort_key):
        super().__init__(display)
        self._sort_key = sort_key

    def __lt__(self, other: QTableWidgetItem) -> bool:
        if isinstance(other, _SortItem):
            return self._sort_key < other._sort_key
        return super().__lt__(other)


class StatsWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Statistics")
        self.setMinimumSize(780, 560)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        title = QLabel("Game Statistics")
        title.setFont(QFont("Georgia", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"color: {GOLD};")
        root.addWidget(title)

        games  = storage.load_games()
        players = {p.id: p for p in storage.load_players()}

        # ── Overall scoreboard ─────────────────────────────────────────────
        total = len(games)
        lib_wins = sum(1 for g in games if g.winning_team == "liberal")
        fas_wins = sum(1 for g in games if g.winning_team == "fascist")
        policies = sum(1 for g in games if g.winning_condition == "policies_enacted")
        elected  = sum(1 for g in games if g.winning_condition == "hitler_elected")
        executed = sum(1 for g in games if g.winning_condition == "hitler_executed")

        overall_row = QHBoxLayout()
        overall_row.setSpacing(14)
        for label, value in [
            ("Total Games", str(total)),
            ("Liberal Wins", str(lib_wins)),
            ("Fascist Wins", str(fas_wins)),
            ("Policies Enacted", str(policies)),
            ("Hitler Elected", str(elected)),
            ("Hitler Executed", str(executed)),
        ]:
            overall_row.addWidget(self._score_card(label, value))
        root.addLayout(overall_row)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {BORDER};")
        root.addWidget(sep)

        # ── Per-player table ───────────────────────────────────────────────
        player_lbl = QLabel("Player Statistics")
        player_lbl.setFont(QFont("Georgia", 13, QFont.Weight.Bold))
        player_lbl.setStyleSheet(f"color: {GOLD};")
        root.addWidget(player_lbl)

        cols = ["Player", "Played", "Liberal", "Fascist", "Hitler", "Wins", "Losses", "Deaths", "Win %", "Win % Lib", "Win % Fas", "Win % Hitler"]
        self._table = QTableWidget(0, len(cols))
        self._table.setHorizontalHeaderLabels(cols)
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(1, len(cols)):
            self._table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        self._table.setSortingEnabled(True)
        self._table.horizontalHeader().setSortIndicatorShown(True)
        root.addWidget(self._table)

        self._populate_table(games, players)

        close_btn = QPushButton("Close")
        close_btn.setMaximumWidth(120)
        close_btn.clicked.connect(self.accept)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(close_btn)
        root.addLayout(btn_row)

    # ── Helpers ────────────────────────────────────────────────────────────

    def _score_card(self, label: str, value: str) -> QLabel:
        lbl = QLabel(f"<div style='text-align:center'>"
                     f"<span style='font-size:22px;font-weight:bold;color:{GOLD}'>{value}</span>"
                     f"<br/><span style='font-size:10px;color:{TEXT_DIM}'>{label}</span></div>")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(
            f"background:{CARD}; border:1px solid {BORDER}; border-radius:6px;"
            f" padding: 10px 8px;"
        )
        lbl.setMinimumWidth(90)
        lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        return lbl

    def _populate_table(self, games, players: dict) -> None:
        stats: dict[str, dict] = defaultdict(lambda: {
            "played": 0, "liberal": 0, "fascist": 0, "hitler": 0,
            "wins": 0, "losses": 0, "deaths": 0,
            "lib_wins": 0, "fas_wins": 0, "hit_wins": 0,
        })

        for game in games:
            winner = game.winning_team
            for pr in game.players:
                s = stats[pr.player_id]
                s["played"] += 1
                s[pr.role] += 1
                if pr.died:
                    s["deaths"] += 1
                # Hitler is on the fascist team
                won = (pr.role == "liberal" and winner == "liberal") or \
                      (pr.role in ("fascist", "hitler") and winner == "fascist")
                if won:
                    s["wins"] += 1
                    if pr.role == "liberal":
                        s["lib_wins"] += 1
                    elif pr.role == "fascist":
                        s["fas_wins"] += 1
                    else:
                        s["hit_wins"] += 1
                else:
                    s["losses"] += 1

        AVATAR_SIZE = 36
        self._table.setSortingEnabled(False)  # disable while populating to avoid mid-fill reorders
        self._table.setRowCount(len(stats))
        self._table.verticalHeader().setDefaultSectionSize(AVATAR_SIZE + 8)

        for row, (pid, s) in enumerate(stats.items()):
            player = players.get(pid)
            name = player.name if player else f"<unknown:{pid[:6]}>"

            # Avatar + name cell
            cell_widget = QHBoxLayout()
            cell_widget.setContentsMargins(4, 2, 4, 2)
            cell_widget.setSpacing(8)

            avatar_path = storage.resolve_avatar(player.avatar_path) if (player and player.avatar_path) else None
            px = make_circular_pixmap(avatar_path, AVATAR_SIZE)
            av_lbl = QLabel()
            av_lbl.setPixmap(px)
            av_lbl.setFixedSize(QSize(AVATAR_SIZE, AVATAR_SIZE))

            name_lbl = QLabel(name)
            name_lbl.setStyleSheet(f"color: {TEXT}; background: transparent;")

            cell_widget.addWidget(av_lbl)
            cell_widget.addWidget(name_lbl)
            cell_widget.addStretch()

            container = QFrame()
            container.setLayout(cell_widget)
            container.setStyleSheet("background: transparent; border: none;")
            # set item first so sorting works; widget overlays it for display
            self._table.setItem(row, 0, _SortItem("", name))
            self._table.setCellWidget(row, 0, container)

            numeric = [
                s["played"], s["liberal"], s["fascist"], s["hitler"],
                s["wins"], s["losses"], s["deaths"],
            ]
            pct_pairs = [
                (s["wins"],     s["played"]),
                (s["lib_wins"], s["liberal"]),
                (s["fas_wins"], s["fascist"]),
                (s["hit_wins"], s["hitler"]),
            ]
            for col, n in enumerate(numeric, start=1):
                item = _SortItem(str(n), n)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self._table.setItem(row, col, item)
            for col, (w, t) in enumerate(pct_pairs, start=1 + len(numeric)):
                key = w / t if t else -1.0
                item = _SortItem(_pct(w, t), key)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self._table.setItem(row, col, item)

        self._table.setSortingEnabled(True)
