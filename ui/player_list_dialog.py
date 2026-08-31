from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QFrame,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

import storage
from ui.avatar import avatar_label
from ui.player_tooltip import PlayerWidget
from ui.theme import GOLD, TEXT_DIM, BORDER, SURFACE


class PlayerListDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Players")
        self.setMinimumWidth(380)
        self.setMinimumHeight(420)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(12)

        title = QLabel("Players")
        title.setFont(QFont("Georgia", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"color: {GOLD};")
        root.addWidget(title)

        # Scrollable player list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._list_widget = QWidget()
        self._list_layout = QVBoxLayout(self._list_widget)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(8)
        self._list_layout.addStretch()
        scroll.setWidget(self._list_widget)
        root.addWidget(scroll, 1)

        # Add Player button at bottom
        add_btn = QPushButton("＋  Add New Player")
        add_btn.setMinimumHeight(44)
        add_btn.setFont(QFont("Georgia", 12, QFont.Weight.Bold))
        add_btn.clicked.connect(self._open_add_player)
        root.addWidget(add_btn)

        self._refresh()

    def _refresh(self):
        # Remove all items except the trailing stretch
        while self._list_layout.count() > 1:
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        players = storage.load_players()
        for player in players:
            row = self._make_row(player)
            self._list_layout.insertWidget(self._list_layout.count() - 1, row)

        if not players:
            empty = QLabel("No players yet.")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet(f"color: {TEXT_DIM};")
            self._list_layout.insertWidget(0, empty)

    def _make_row(self, player) -> QWidget:
        frame = QFrame()
        frame.setStyleSheet(
            f"QFrame {{ background: {SURFACE}; border: 1px solid {BORDER};"
            f" border-radius: 8px; padding: 4px; }}"
        )
        row = QHBoxLayout(frame)
        row.setContentsMargins(10, 6, 10, 6)
        row.setSpacing(12)

        pw = PlayerWidget(player, avatar_size=44)
        row.addWidget(pw, 1)

        edit_btn = QPushButton("✎  Edit")
        edit_btn.setMinimumWidth(90)
        edit_btn.setMinimumHeight(34)
        edit_btn.setFont(QFont("Georgia", 11))
        edit_btn.clicked.connect(lambda _, p=player: self._open_edit_player(p))
        row.addWidget(edit_btn)

        return frame

    def _open_add_player(self):
        from ui.add_player_dialog import AddPlayerDialog
        dlg = AddPlayerDialog(self)
        if dlg.exec():
            self._refresh()

    def _open_edit_player(self, player):
        from ui.add_player_dialog import AddPlayerDialog
        dlg = AddPlayerDialog(self, player=player)
        if dlg.exec():
            self._refresh()
