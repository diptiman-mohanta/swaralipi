"""Reusable widgets and layout helpers."""

import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPainterPath, QPen, QPixmap, QPolygonF
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy,
                               QVBoxLayout, QWidget)

from . import style

MIN_DB = -60.0
SCALE_MARKS = [-60, -48, -36, -24, -12, -6, -3, 0]


# ================================================================ level meter
class LevelMeter(QWidget):
    """Peak meter in dBFS with a printed scale, like the one on a field recorder.
    The target speaking range (-12 to -3 dBFS) is marked on the track."""

    BAR_H = 8

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(30)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._db = MIN_DB
        self._hold = MIN_DB
        self._hold_frames = 0

    def set_peak(self, peak: float) -> None:
        db = 20 * math.log10(peak) if peak > 1e-6 else MIN_DB
        db = max(MIN_DB, min(0.0, db))
        self._db = db if db > self._db else max(db, self._db - 1.5)   # fast attack, slow fall
        if db >= self._hold:
            self._hold, self._hold_frames = db, 30
        elif self._hold_frames > 0:
            self._hold_frames -= 1
        else:
            self._hold = max(MIN_DB, self._hold - 1.0)
        self.update()

    def reset(self) -> None:
        self._db = self._hold = MIN_DB
        self.update()

    def _x(self, db: float, w: float) -> float:
        return (db - MIN_DB) / -MIN_DB * w

    def paintEvent(self, _event):
        p = QPainter(self)
        w = self.width() - 1
        h = self.BAR_H
        p.fillRect(QRectF(0, 0, w, h), QColor(style.RULE))
        # target zone underlay
        p.fillRect(QRectF(self._x(-12, w), 0, self._x(-3, w) - self._x(-12, w), h),
                   QColor(style.RULE_STRONG))
        level = self._x(self._db, w)
        color = (style.RED if self._db > -3 else style.AMBER if self._db > -12
                 else style.INK_2)
        if level > 0:
            p.fillRect(QRectF(0, 0, level, h), QColor(color))
        if self._hold > MIN_DB:
            p.fillRect(QRectF(self._x(self._hold, w) - 1, 0, 2, h), QColor(style.INK))
        # scale
        font = QFont(style.MONO)
        font.setPixelSize(10)
        p.setFont(font)
        p.setPen(QColor(style.MUTED))
        for db in SCALE_MARKS:
            x = self._x(db, w)
            p.drawLine(QPointF(x, h + 1), QPointF(x, h + 4))
            text = str(db)
            tw = p.fontMetrics().horizontalAdvance(text)
            tx = min(max(0, x - tw / 2), w - tw)
            p.drawText(QPointF(tx, h + 16), text)
        p.end()


# ================================================================ icons
def _pixmap(size: int, draw) -> QPixmap:
    ratio = 2
    pm = QPixmap(size * ratio, size * ratio)
    pm.setDevicePixelRatio(ratio)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    draw(p, size)
    p.end()
    return pm


def _shape(name: str, color: str):
    c = QColor(color)

    def draw(p: QPainter, s: int):
        if name == "record":
            p.setPen(Qt.NoPen)
            p.setBrush(c)
            p.drawEllipse(QRectF(s * 0.2, s * 0.2, s * 0.6, s * 0.6))
        elif name == "stop":
            p.setPen(Qt.NoPen)
            p.setBrush(c)
            p.drawRect(QRectF(s * 0.24, s * 0.24, s * 0.52, s * 0.52))
        elif name == "play":
            p.setPen(Qt.NoPen)
            p.setBrush(c)
            p.drawPolygon(QPolygonF([QPointF(s * 0.28, s * 0.18), QPointF(s * 0.82, s * 0.5),
                                     QPointF(s * 0.28, s * 0.82)]))
        elif name == "check":
            pen = QPen(c, s * 0.13, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            p.setPen(pen)
            path = QPainterPath(QPointF(s * 0.2, s * 0.53))
            path.lineTo(s * 0.42, s * 0.74)
            path.lineTo(s * 0.8, s * 0.28)
            p.drawPath(path)
        elif name == "dot":
            p.setPen(Qt.NoPen)
            p.setBrush(c)
            p.drawEllipse(QRectF(s * 0.32, s * 0.32, s * 0.36, s * 0.36))
    return draw


def icon(name: str, color: str, disabled_color: str | None = None, size: int = 16) -> QIcon:
    ic = QIcon(_pixmap(size, _shape(name, color)))
    if disabled_color:
        ic.addPixmap(_pixmap(size, _shape(name, disabled_color)), QIcon.Disabled)
    return ic


# ================================================================ layout helpers
class WrapLabel(QLabel):
    """Word-wrapped label that reserves the height its text needs at its actual width.
    (Qt layouts otherwise size wrapped labels for a single line and clip the rest.)"""

    def __init__(self, text: str = ""):
        super().__init__(text)
        self.setWordWrap(True)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        h = self.heightForWidth(self.width())
        if h > 0 and h != self.minimumHeight():
            self.setMinimumHeight(h)


def label(text: str, name: str = "", wrap: bool = False) -> QLabel:
    lbl = WrapLabel(text) if wrap else QLabel(text)
    if name:
        lbl.setObjectName(name)
    return lbl


def rule(vertical: bool = False) -> QFrame:
    f = QFrame()
    f.setObjectName("Rule")
    if vertical:
        f.setFixedWidth(1)
    else:
        f.setFixedHeight(1)
    return f


def heading(title: str, lede: str = "") -> QWidget:
    """Page title with an optional one-paragraph lede."""
    w = QWidget()
    lay = QVBoxLayout(w)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(6)
    lay.addWidget(label(title, "Title"))
    if lede:
        lbl = label(lede, "Lede", wrap=True)
        lbl.setMaximumWidth(720)
        lay.addWidget(lbl)
    return w


def section(title: str, note: str = "") -> QWidget:
    w = QWidget()
    lay = QVBoxLayout(w)
    lay.setContentsMargins(0, 0, 0, 4)
    lay.setSpacing(2)
    lay.addWidget(label(title, "Section"))
    if note:
        lay.addWidget(label(note, "Note", wrap=True))
    return w


def button(text: str, kind: str = "", icon_name: str = "") -> QPushButton:
    b = QPushButton(text)
    if kind:
        b.setObjectName(kind)
    b.setCursor(Qt.PointingHandCursor)
    if icon_name:
        fg = {"Primary": style.PAPER, "Record": "#ffffff"}.get(kind, style.INK)
        b.setIcon(icon(icon_name, fg, disabled_color="#ffffff" if kind else "#b9b5a8"))
    return b


def button_row(*widgets, stretch_first=True) -> QHBoxLayout:
    """None in the argument list inserts a stretch."""
    row = QHBoxLayout()
    row.setSpacing(10)
    if stretch_first:
        row.addStretch(1)
    for w in widgets:
        if w is None:
            row.addStretch(1)
        elif isinstance(w, QWidget):
            row.addWidget(w)
        else:
            row.addLayout(w)
    return row


def set_invalid(widget: QWidget, invalid: bool) -> None:
    widget.setProperty("invalid", "true" if invalid else "false")
    widget.style().unpolish(widget)
    widget.style().polish(widget)


class OptionButton(QPushButton):
    """A full-width choice row: bold title over one line of explanation."""

    def __init__(self, title: str, text: str):
        super().__init__()
        self.setObjectName("Option")
        self.setCursor(Qt.PointingHandCursor)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 18, 12, 18)
        lay.setSpacing(4)
        for t, name in ((title, "OptionTitle"), (text, "OptionText")):
            lbl = label(t, name, wrap=True)
            lbl.setAttribute(Qt.WA_TransparentForMouseEvents)
            lay.addWidget(lbl)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        h = self.layout().totalHeightForWidth(self.width())
        if h > 0 and h != self.minimumHeight():
            self.setMinimumHeight(h)


class StepBar(QWidget):
    """App name on the left, the five steps of a session on the right."""

    STEPS = ["Mode", "Audio", "Consent", "Speaker", "Record"]

    def __init__(self, app_name: str):
        super().__init__()
        self.setObjectName("TopBar")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        row = QHBoxLayout()
        row.setContentsMargins(48, 14, 48, 14)
        row.setSpacing(22)
        row.addWidget(label(app_name, "AppName"))
        row.addStretch(1)
        self.labels = []
        for i, name in enumerate(self.STEPS, start=1):
            lbl = label(f"{i}  {name}", "Step")
            self.labels.append(lbl)
            row.addWidget(lbl)
        outer.addLayout(row)
        outer.addWidget(rule())

    def set_step(self, current: int) -> None:
        for i, lbl in enumerate(self.labels):
            name = "StepCurrent" if i == current else "StepDone" if i < current else "Step"
            lbl.setObjectName(name)
            lbl.style().unpolish(lbl)
            lbl.style().polish(lbl)
