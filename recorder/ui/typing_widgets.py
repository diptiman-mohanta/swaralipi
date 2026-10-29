"""Widgets for typing in Indian languages: phonetic text box, letter keys, typing help."""

from PySide6.QtCore import QPoint, QRect, QSize, Qt, Signal
from PySide6.QtGui import QFont, QTextCursor
from PySide6.QtWidgets import (QDialog, QGridLayout, QHBoxLayout, QLabel, QLayout, QPlainTextEdit,
                               QPushButton, QScrollArea, QSizePolicy, QVBoxLayout, QWidget)

from .. import config
from ..typing import keys as letter_keys
from ..typing import phonetic, suggest
from . import style
from .widgets import button, button_row, heading, label, rule


def font_css(language: str, size: int) -> str:
    """Stylesheet that shows text in the language's own font (falls back to IBM Plex)."""
    return f'font-family: "{config.language_font(language)}", "{style.SANS}"; font-size: {size}px;'


def apply_language(widget: QWidget, language: str, size: int) -> None:
    """Font and reading direction for a widget that shows text in `language`."""
    widget.setStyleSheet(font_css(language, size) if language != "English" else "")
    widget.setLayoutDirection(Qt.RightToLeft if config.is_rtl(language) else Qt.LeftToRight)


def _utf16_len(text: str) -> int:
    return len(text.encode("utf-16-le")) // 2


# ================================================================ phonetic text box
class PhoneticEdit(QPlainTextEdit):
    """Text box that turns English letters into the language's script as you type.

    The word being typed is kept as Latin letters ("namaste") and re-rendered on every
    key press (नमस्ते). Space, punctuation, Enter or moving the cursor ends the word.
    With suggestions on, the text shown is the best of several candidates ("pani" ->
    पानी); a number key picks another, Tab steps through them and Esc keeps exactly what
    the scheme gives.
    """

    composing = Signal(str, list, int)   # (latin letters, candidates, chosen); "" when idle
    toggle_requested = Signal()          # Ctrl+Space: switch between script and English letters

    def __init__(self, parent=None):
        super().__init__(parent)
        self.language = "English"
        self.phonetic_on = False
        self.suggest_on = True
        self._buf, self._start, self._len = "", 0, 0
        self._candidates, self._pick = [], 0
        self._internal = False
        self.cursorPositionChanged.connect(self._cursor_moved)

    # ------------------------------------------------------------ configuration
    @property
    def phonetic_available(self) -> bool:
        return phonetic.available(self.language)

    def set_language(self, language: str) -> None:
        self.commit()
        self.language = language
        apply_language(self, language, 22)
        option = self.document().defaultTextOption()
        rtl = config.is_rtl(language)
        option.setTextDirection(Qt.RightToLeft if rtl else Qt.LeftToRight)
        option.setAlignment((Qt.AlignRight if rtl else Qt.AlignLeft) | Qt.AlignAbsolute)
        self.document().setDefaultTextOption(option)
        self.phonetic_on = self.phonetic_available and self.phonetic_on

    def set_phonetic(self, on: bool) -> None:
        self.commit()
        self.phonetic_on = on and self.phonetic_available

    def _info(self) -> dict:
        return config.LANGUAGE_INFO.get(self.language, {})

    def _candidates_for(self, latin: str) -> list[str]:
        if self.suggest_on and suggest.available(self.language):
            return suggest.suggestions(self.language, latin)
        return [phonetic.scheme(self.language).transliterate(latin)]

    # ------------------------------------------------------------ composing
    def commit(self) -> None:
        """Ends the word being composed (its script text stays)."""
        if self._buf:
            self._buf, self._len = "", 0
            self._candidates, self._pick = [], 0
            self.composing.emit("", [], 0)

    def choose(self, index: int, finish: bool = True) -> None:
        """Shows candidate `index` for the word being typed (and ends the word)."""
        if self._buf and 0 <= index < len(self._candidates):
            self._pick = index
            self._show(self._candidates[index])
            if finish:
                self.commit()

    def keep_exact(self) -> None:
        """Ends the word with exactly what the scheme gives, not a suggested word."""
        if self._buf:
            exact = phonetic.scheme(self.language).transliterate(self._buf)
            self.choose(self._candidates.index(exact) if exact in self._candidates else 0)

    def _render(self) -> None:
        self._candidates = self._candidates_for(self._buf) if self._buf else []
        self._pick = 0
        self._show(self._candidates[0] if self._candidates else "")

    def _show(self, out: str) -> None:
        cur = self.textCursor()
        self._internal = True
        cur.beginEditBlock()
        cur.setPosition(self._start)
        cur.setPosition(self._start + self._len, QTextCursor.KeepAnchor)
        cur.insertText(out)
        cur.endEditBlock()
        self.setTextCursor(cur)
        self._internal = False
        self._len = _utf16_len(out)
        if self._buf:
            self.composing.emit(self._buf, self._candidates, self._pick)
        else:
            self.composing.emit("", [], 0)

    def _cursor_moved(self) -> None:
        if not self._internal and self._buf \
                and self.textCursor().position() != self._start + self._len:
            self.commit()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Space and e.modifiers() == Qt.ControlModifier:
            self.commit()
            self.toggle_requested.emit()
            return
        if not self.phonetic_on or self.isReadOnly():
            return super().keyPressEvent(e)
        if e.modifiers() & (Qt.ControlModifier | Qt.AltModifier | Qt.MetaModifier):
            self.commit()
            return super().keyPressEvent(e)
        text = e.text()
        if e.key() == Qt.Key_Backspace and self._buf:
            self._buf = self._buf[:-1]
            self._render()
            return
        if self._buf and len(self._candidates) > 1:
            if len(text) == 1 and text in "123456789" and int(text) <= len(self._candidates):
                self.choose(int(text) - 1)
                return
            if e.key() == Qt.Key_Tab:
                self.choose((self._pick + 1) % len(self._candidates), finish=False)
                return
            if e.key() == Qt.Key_Backtab:
                self.choose((self._pick - 1) % len(self._candidates), finish=False)
                return
        if self._buf and e.key() == Qt.Key_Escape:
            self.keep_exact()
            return
        if len(text) == 1 and text.isascii() and (text.isalpha() or text in "^_~"):
            if not self._buf:
                cur = self.textCursor()
                if cur.hasSelection():
                    cur.removeSelectedText()
                    self.setTextCursor(cur)
                self._start, self._len = self.textCursor().position(), 0
            self._buf += text
            self._render()
            return
        self.commit()
        if text == ".":
            self.insertPlainText(self._info().get("full_stop", "."))
            return
        if text == "|":
            before = self.toPlainText()[:self.textCursor().position()]
            if before.endswith("।"):
                self.textCursor().deletePreviousChar()
                self.insertPlainText("॥")
            else:
                self.insertPlainText("।")
            return
        super().keyPressEvent(e)

    def focusOutEvent(self, e):
        self.commit()
        super().focusOutEvent(e)

    def insert_key(self, text: str) -> None:
        """Inserts a character from the on-screen keys at the cursor."""
        self.commit()
        self.insertPlainText(text)
        self.setFocus()


# ================================================================ suggestions
class SuggestionBar(QWidget):
    """The word being typed and what it may mean: "pani  1 पानी  2 पनी  3 पनि". The chosen
    one is highlighted; clicking one picks it."""

    picked = Signal(int)

    HINT = "Suggestions appear as you type. Space takes the first, 1–5 picks one, Tab moves " \
           "between them, Esc keeps exactly what you typed."

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)
        self.latin = label("", "MonoMuted")
        lay.addWidget(self.latin)
        self.buttons = []
        for i in range(suggest.LIMIT):
            b = QPushButton()
            b.setObjectName("Suggestion")
            b.setCheckable(True)
            b.setFocusPolicy(Qt.NoFocus)
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _=False, n=i: self.picked.emit(n))
            b.hide()
            lay.addWidget(b)
            self.buttons.append(b)
        self.hint = label(self.HINT, "Note")
        lay.addWidget(self.hint, 1)
        lay.addStretch(0)
        self.setFixedHeight(34)
        self.language = "English"

    def set_language(self, language: str) -> None:
        self.language = language
        css = font_css(language, 17)
        for b in self.buttons:
            b.setStyleSheet(css)

    def show_candidates(self, latin: str, candidates: list, chosen: int) -> None:
        self.latin.setText(latin)
        self.latin.setVisible(bool(latin))
        self.hint.setVisible(not latin)
        numbered = len(candidates) > 1
        for i, b in enumerate(self.buttons):
            if i < len(candidates):
                b.setText(f"{i + 1}  {candidates[i]}" if numbered else candidates[i])
                b.setChecked(i == chosen)
                b.show()
            else:
                b.hide()


# ================================================================ letter keys
class FlowLayout(QLayout):
    """Lays widgets out left to right, wrapping onto new rows."""

    def __init__(self, parent=None, spacing: int = 4):
        super().__init__(parent)
        self._items = []
        self.setSpacing(spacing)
        self.setContentsMargins(0, 0, 0, 0)

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, i):
        return self._items[i] if 0 <= i < len(self._items) else None

    def takeAt(self, i):
        return self._items.pop(i) if 0 <= i < len(self._items) else None

    def expandingDirections(self):
        return Qt.Orientations(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._do_layout(QRect(0, 0, width, 0), test=True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, test=False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        return size

    def _do_layout(self, rect, test):
        x, y, line_h = rect.x(), rect.y(), 0
        gap = self.spacing()
        for item in self._items:
            w = item.sizeHint()
            if x + w.width() > rect.right() + 1 and line_h > 0:
                x, y, line_h = rect.x(), y + line_h + gap, 0
            if not test:
                item.setGeometry(QRect(QPoint(x, y), w))
            x += w.width() + gap
            line_h = max(line_h, w.height())
        return y + line_h - rect.y()


class LetterKeys(QWidget):
    """Clickable letters of a language's script, grouped (vowels, vowel signs, ...)."""

    key_pressed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._lay = QVBoxLayout(self)
        self._lay.setContentsMargins(0, 4, 0, 4)
        self._lay.setSpacing(6)
        self.language = ""

    def set_language(self, language: str) -> None:
        if language == self.language:
            return
        self.language = language
        while self._lay.count():
            item = self._lay.takeAt(0)
            old = item.widget()
            if old:   # detach now; deleteLater alone leaves old keys visible until idle
                old.hide()
                old.setParent(None)
                old.deleteLater()
        css = font_css(language, 17)
        for title, keys in letter_keys.key_groups(language):
            self._lay.addWidget(label(title, "Note"))
            holder = QWidget()
            flow = FlowLayout(holder)
            for ch, shown in keys:
                b = QPushButton(shown)
                b.setObjectName("Key")
                b.setStyleSheet(css)
                b.setFocusPolicy(Qt.NoFocus)
                b.setCursor(Qt.PointingHandCursor)
                b.setToolTip(ch)
                b.clicked.connect(lambda _=False, c=ch: self.key_pressed.emit(c))
                flow.addWidget(b)
            holder.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
            self._lay.addWidget(holder)


class LetterKeysPanel(QScrollArea):
    """Scrollable container so a long alphabet never pushes the record buttons away."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.keys = LetterKeys()
        self.setWidget(self.keys)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setFixedHeight(190)
        self.setObjectName("KeysPanel")


# ================================================================ typing help
class TypingHelpDialog(QDialog):
    def __init__(self, parent, language: str):
        super().__init__(parent)
        native = config.LANGUAGE_INFO[language]["native"]
        scheme = phonetic.scheme(language)
        small, small_shows, big, big_shows = scheme.case_example()
        self.setWindowTitle(f"Typing {language} with English letters")
        self.resize(760, 680)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(32, 28, 32, 24)
        outer.setSpacing(12)
        outer.addWidget(heading(f"Typing {language} with English letters",
                                f"Type how a word sounds and it appears in {native}. Small "
                                "and capital letters mean different sounds, for example "
                                f"{small} ({small_shows}) and {big} ({big_shows}). Press space "
                                "to finish a word."))
        body = QWidget()
        grid = QGridLayout(body)
        grid.setContentsMargins(0, 0, 8, 0)
        grid.setHorizontalSpacing(24)
        grid.setVerticalSpacing(6)
        row = 0
        css = font_css(language, 17)
        mono = QFont(style.MONO)
        mono.setPixelSize(14)
        per_row = {"Vowels": 3, "Consonants": 3, "Marks": 3, "Examples": 2}
        width = 2 * max(per_row.values())
        for title, items in scheme.cheat_sheet():
            if row:
                grid.addWidget(rule(), row, 0, 1, width)
                row += 1
            grid.addWidget(label(title, "Section"), row, 0, 1, width)
            row += 1
            cols = per_row.get(title, 1)
            for n, (latin, script) in enumerate(items):
                key = QLabel(latin)
                key.setFont(mono)
                key.setTextInteractionFlags(Qt.TextSelectableByMouse)
                value = QLabel(script)
                value.setStyleSheet(css)
                col = 2 * (n % cols)
                grid.addWidget(key, row, col)
                grid.addWidget(value, row, col + 1, 1, 1 if cols > 1 else width - 1)
                if n % cols == cols - 1 or n == len(items) - 1:
                    row += 1
        for c in range(1, width, 2):
            grid.setColumnStretch(c, 1)
        area = QScrollArea()
        area.setWidgetResizable(True)
        area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        area.setWidget(body)
        outer.addWidget(area, 1)
        close = button("Close", "Primary")
        close.clicked.connect(self.accept)
        outer.addLayout(button_row(close))
