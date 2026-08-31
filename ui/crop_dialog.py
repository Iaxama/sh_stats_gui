from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QSlider, QLabel, QSizePolicy,
)
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import (
    QFont, QPixmap, QPainter, QPainterPath, QColor, QBrush, QPen,
)

from ui.theme import GOLD, TEXT_DIM, BG, SURFACE, BORDER


_PREVIEW = 300   # size of the crop canvas in pixels
_CIRCLE_R = 140  # radius of the crop circle


class _CropCanvas(QPushButton):
    """Interactive widget: drag to pan, zoom via external slider."""

    def __init__(self, pixmap: QPixmap, parent=None):
        super().__init__(parent)
        self.setFixedSize(_PREVIEW, _PREVIEW)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setStyleSheet("border: none; background: transparent;")

        self._source = pixmap
        self._zoom = 1.0
        # offset = top-left corner of the (scaled) image relative to widget origin
        self._offset = QPoint(0, 0)
        self._drag_start: QPoint | None = None
        self._offset_at_drag = QPoint(0, 0)
        self._fit()

    # ── public ────────────────────────────────────────────────────────────
    def set_zoom(self, value: int) -> None:
        """value 100–400 maps to zoom 1.0–4.0."""
        self._zoom = value / 100.0
        self._clamp()
        self.update()

    # ── internals ────────────────────────────────────────────────────────
    def _fit(self):
        """Initial zoom so the image fills the circle."""
        w, h = self._source.width(), self._source.height()
        min_dim = min(w, h)
        self._zoom = (2 * _CIRCLE_R) / min_dim if min_dim else 1.0
        self._center()

    def _scaled_size(self):
        return (
            int(self._source.width()  * self._zoom),
            int(self._source.height() * self._zoom),
        )

    def _center(self):
        sw, sh = self._scaled_size()
        self._offset = QPoint((_PREVIEW - sw) // 2, (_PREVIEW - sh) // 2)
        self._clamp()

    def _clamp(self):
        sw, sh = self._scaled_size()
        cx = _PREVIEW // 2
        cy = _PREVIEW // 2
        # ensure circle area is always covered
        max_x = cx - _CIRCLE_R
        min_x = cx + _CIRCLE_R - sw
        max_y = cy - _CIRCLE_R
        min_y = cy + _CIRCLE_R - sh
        x = max(min_x, min(max_x, self._offset.x()))
        y = max(min_y, min(max_y, self._offset.y()))
        self._offset = QPoint(x, y)

    # ── events ────────────────────────────────────────────────────────────
    def mousePressEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:
            self._drag_start = ev.pos()
            self._offset_at_drag = QPoint(self._offset)
            self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseMoveEvent(self, ev):
        if self._drag_start is not None:
            delta = ev.pos() - self._drag_start
            self._offset = self._offset_at_drag + delta
            self._clamp()
            self.update()

    def mouseReleaseEvent(self, ev):
        self._drag_start = None
        self.setCursor(Qt.CursorShape.OpenHandCursor)

    def paintEvent(self, _ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        # draw image
        sw, sh = self._scaled_size()
        p.drawPixmap(self._offset.x(), self._offset.y(),
                     self._source.scaled(sw, sh,
                                         Qt.AspectRatioMode.IgnoreAspectRatio,
                                         Qt.TransformationMode.SmoothTransformation))

        # dim outside circle
        cx = _PREVIEW / 2
        cy = _PREVIEW / 2
        outer = QPainterPath()
        outer.addRect(0, 0, _PREVIEW, _PREVIEW)
        inner = QPainterPath()
        inner.addEllipse(cx - _CIRCLE_R, cy - _CIRCLE_R, _CIRCLE_R * 2, _CIRCLE_R * 2)
        mask = outer - inner
        p.fillPath(mask, QColor(0, 0, 0, 160))

        # circle border
        p.setPen(QPen(QColor(BORDER), 2))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(int(cx - _CIRCLE_R), int(cy - _CIRCLE_R),
                      _CIRCLE_R * 2, _CIRCLE_R * 2)
        p.end()


class CropDialog(QDialog):
    def __init__(self, image_path: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Crop Photo")
        self.setFixedSize(360, 460)
        self._params: dict | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(12)

        hint = QLabel("Drag to reposition · use slider to zoom")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px;")
        root.addWidget(hint)

        src = QPixmap(image_path)
        self._canvas = _CropCanvas(src)
        canvas_row = QHBoxLayout()
        canvas_row.addStretch()
        canvas_row.addWidget(self._canvas)
        canvas_row.addStretch()
        root.addLayout(canvas_row)

        # Zoom slider — minimum = fitted zoom so circle is always filled
        zoom_lbl = QLabel("Zoom")
        zoom_lbl.setStyleSheet(f"color: {GOLD}; font-weight: bold;")
        zoom_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._slider = QSlider(Qt.Orientation.Horizontal)
        fit_val = max(10, int(self._canvas._zoom * 100))
        self._slider.setRange(fit_val, fit_val * 4)
        self._slider.setValue(fit_val)
        self._slider.valueChanged.connect(self._canvas.set_zoom)
        root.addWidget(zoom_lbl)
        root.addWidget(self._slider)

        # Buttons
        btn_row = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        ok_btn = QPushButton("Use Photo")
        ok_btn.setFont(QFont("Georgia", 12, QFont.Weight.Bold))
        ok_btn.clicked.connect(self._accept)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(ok_btn)
        root.addLayout(btn_row)

    def _accept(self):
        c = self._canvas
        self._params = {
            "zoom":         c._zoom,
            "offset_x":     c._offset.x(),
            "offset_y":     c._offset.y(),
            "preview_size": _PREVIEW,
            "circle_r":     _CIRCLE_R,
        }
        self.accept()

    def crop_params(self) -> dict | None:
        return self._params
