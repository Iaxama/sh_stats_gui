from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from ui.theme import GOLD, TEXT, RED, BG


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Secret Hitler — Stats Tracker")
        self.setMinimumSize(520, 420)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(40, 30, 40, 30)
        root.setSpacing(0)

        # ── Header ────────────────────────────────────────────────────────
        title = QLabel("SECRET HITLER")
        title_font = QFont("Georgia", 32, QFont.Weight.Bold)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"color: {GOLD}; letter-spacing: 6px; background: transparent;")

        subtitle = QLabel("Stats Tracker")
        sub_font = QFont("Georgia", 13)
        sub_font.setItalic(True)
        subtitle.setFont(sub_font)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet(f"color: {TEXT}; background: transparent; margin-bottom: 6px;")

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {RED}; margin: 12px 0 28px 0;")

        root.addWidget(title)
        root.addWidget(subtitle)
        root.addWidget(sep)

        # ── Buttons ───────────────────────────────────────────────────────
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(16)

        self.btn_add_game   = self._big_button("⚔  Add Game Results")
        self.btn_players    = self._big_button("👤  Players")
        self.btn_history    = self._big_button("📖  Game History")
        self.btn_stats      = self._big_button("📜  View Statistics")

        for btn in (self.btn_add_game, self.btn_players, self.btn_history, self.btn_stats):
            btn_layout.addWidget(btn)

        root.addLayout(btn_layout)
        root.addStretch()

        # ── Wire buttons ──────────────────────────────────────────────────
        self.btn_add_game.clicked.connect(self._open_add_game)
        self.btn_players.clicked.connect(self._open_players)
        self.btn_history.clicked.connect(self._open_history)
        self.btn_stats.clicked.connect(self._open_stats)

    def _big_button(self, text: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setMinimumHeight(52)
        btn.setFont(QFont("Georgia", 14, QFont.Weight.Bold))
        return btn

    def _open_add_game(self):
        from ui.add_game_dialog import AddGameDialog
        dlg = AddGameDialog(self)
        dlg.exec()

    def _open_players(self):
        from ui.player_list_dialog import PlayerListDialog
        dlg = PlayerListDialog(self)
        dlg.exec()

    def _open_history(self):
        from ui.game_history_dialog import GameHistoryDialog
        dlg = GameHistoryDialog(self)
        dlg.exec()

    def _open_stats(self):
        from ui.stats_window import StatsWindow
        win = StatsWindow(self)
        win.exec()
