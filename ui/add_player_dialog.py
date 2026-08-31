from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QSizePolicy,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

import storage
from ui.avatar import avatar_label, make_circular_pixmap
from ui.theme import GOLD, TEXT_DIM, RED, BORDER


class AddPlayerDialog(QDialog):
    def __init__(self, parent=None, player=None):
        super().__init__(parent)
        self._player = player  # None = add mode, Player = edit mode
        self._avatar_src: str | None = None   # relative path (already in assets)
        self._avatar_crop: dict | None = None
        is_edit = player is not None
        self.setWindowTitle("Edit Player" if is_edit else "Add New Player")
        self.setMinimumWidth(340)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        # Title
        title = QLabel("Edit Player" if is_edit else "Register Player")
        title.setFont(QFont("Georgia", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"color: {GOLD};")
        layout.addWidget(title)

        # Avatar preview
        initial_path = storage.resolve_avatar(player.avatar_path) if (player and player.avatar_path) else None
        initial_crop = player.avatar_crop if player else None
        self._avatar_lbl = avatar_label(initial_path, 96, initial_crop)
        self._avatar_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar_row = QHBoxLayout()
        avatar_row.addStretch()
        avatar_row.addWidget(self._avatar_lbl)
        avatar_row.addStretch()
        layout.addLayout(avatar_row)

        # Upload button
        upload_btn = QPushButton("Upload Photo")
        upload_btn.setMaximumWidth(160)
        upload_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        up_row = QHBoxLayout()
        up_row.addStretch()
        up_row.addWidget(upload_btn)
        up_row.addStretch()
        layout.addLayout(up_row)
        upload_btn.clicked.connect(self._pick_image)

        # Name field
        name_lbl = QLabel("Player Name")
        name_lbl.setStyleSheet(f"color: {GOLD}; font-weight: bold;")
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("Enter name…")
        if player:
            self._name_edit.setText(player.name)
        layout.addWidget(name_lbl)
        layout.addWidget(self._name_edit)

        # Error label
        self._error_lbl = QLabel("")
        self._error_lbl.setStyleSheet(f"color: {RED};")
        self._error_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._error_lbl)

        # Buttons
        btn_row = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        self._save_btn = QPushButton("Save Changes" if player else "Save Player")
        self._save_btn.clicked.connect(self._save)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(self._save_btn)
        layout.addLayout(btn_row)

    def _pick_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Profile Picture", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif *.webp)"
        )
        if not path:
            return
        from ui.crop_dialog import CropDialog
        dlg = CropDialog(path, self)
        if not dlg.exec():
            return
        # copy original to assets immediately so params stay valid
        rel_path = storage.copy_avatar(path)
        self._avatar_src = rel_path
        self._avatar_crop = dlg.crop_params()
        abs_path = storage.resolve_avatar(rel_path)
        self._avatar_lbl.setPixmap(make_circular_pixmap(abs_path, 96, self._avatar_crop))

    def _save(self):
        name = self._name_edit.text().strip()
        if not name:
            self._error_lbl.setText("Name cannot be empty.")
            return

        players = storage.load_players()

        if self._player is None:
            # Add mode: name must be unique
            if any(p.name.lower() == name.lower() for p in players):
                self._error_lbl.setText("A player with that name already exists.")
                return
            from models.player import Player
            players.append(Player(name=name, avatar_path=self._avatar_src,
                                  avatar_crop=self._avatar_crop))
        else:
            # Edit mode: update matching player by id
            if any(p.name.lower() == name.lower() and p.id != self._player.id for p in players):
                self._error_lbl.setText("A player with that name already exists.")
                return
            for p in players:
                if p.id == self._player.id:
                    p.name = name
                    if self._avatar_src:
                        p.avatar_path = self._avatar_src
                        p.avatar_crop = self._avatar_crop
                    break

        storage.save_players(players)
        self.accept()
