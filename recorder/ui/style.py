"""Visual system: tokens, fonts and the application stylesheet.

Direction: a field recorder, not a web dashboard. Warm paper background, near-black
ink, hairline rules instead of boxed cards. Red is reserved for recording; green and
amber appear only on quality-check results. IBM Plex Sans for text, IBM Plex Mono for
IDs and measured values.
"""

from pathlib import Path

from PySide6.QtGui import QColor, QFontDatabase, QPalette

UI_DIR = Path(__file__).parent
FONTS_DIR = UI_DIR / "fonts"
CHECK_ICON = (UI_DIR / "icons" / "check.svg").as_posix()
CHEVRON_ICON = (UI_DIR / "icons" / "chevron-down.svg").as_posix()

# ---------------------------------------------------------------- colour tokens
PAPER = "#f4f3ee"
FIELD = "#fdfdfb"
INK = "#1c1b18"
INK_2 = "#45423b"
MUTED = "#7a776d"
RULE = "#dcd9cf"
RULE_STRONG = "#b9b5a8"
HOVER = "#eae8e0"
RED = "#c0392b"
GREEN = "#2e7a48"
AMBER = "#9a6200"

# ---------------------------------------------------------------- type tokens (px)
SANS = "IBM Plex Sans"
MONO = "IBM Plex Mono"
FALLBACK = '"Segoe UI", "Helvetica Neue", Arial, sans-serif'
BODY = 14
SMALL = 12
SECTION = 15
TITLE = 28
DISPLAY = 38
PROMPT = 24
READOUT = 30


def load_fonts() -> None:
    for f in FONTS_DIR.glob("*.ttf"):
        QFontDatabase.addApplicationFont(str(f))


def light_palette() -> QPalette:
    """Fixed light palette so Windows dark mode cannot leak into popups and dialogs."""
    p = QPalette()
    roles = {
        QPalette.Window: PAPER, QPalette.WindowText: INK, QPalette.Base: FIELD,
        QPalette.AlternateBase: HOVER, QPalette.Text: INK, QPalette.Button: PAPER,
        QPalette.ButtonText: INK, QPalette.Highlight: HOVER, QPalette.HighlightedText: INK,
        QPalette.ToolTipBase: INK, QPalette.ToolTipText: PAPER, QPalette.PlaceholderText: MUTED,
        QPalette.Light: FIELD, QPalette.Mid: RULE, QPalette.Dark: RULE_STRONG,
    }
    for role, color in roles.items():
        p.setColor(role, QColor(color))
    for role in (QPalette.Text, QPalette.WindowText, QPalette.ButtonText):
        p.setColor(QPalette.Disabled, role, QColor(MUTED))
    return p


STYLESHEET = f"""
* {{
    font-family: "{SANS}", {FALLBACK};
    font-size: {BODY}px;
    color: {INK};
}}
QMainWindow, QDialog, QStackedWidget, QStackedWidget > QWidget, QScrollArea,
QScrollArea > QWidget > QWidget, QMessageBox {{
    background: {PAPER};
}}
QScrollArea {{ border: none; }}
QToolTip {{ background: {INK}; color: {PAPER}; border: none; padding: 4px 6px; }}

/* ---- type ---- */
QLabel#Display {{ font-size: {DISPLAY}px; font-weight: 600; }}
QLabel#Title {{ font-size: {TITLE}px; font-weight: 600; }}
QLabel#Lede {{ font-size: 15px; color: {INK_2}; }}
QLabel#Section {{ font-size: {SECTION}px; font-weight: 600; }}
QLabel#Note, QLabel#Hint {{ font-size: {SMALL}px; color: {MUTED}; }}
QLabel#Muted {{ color: {MUTED}; }}
QLabel#Warning {{ font-size: {SMALL}px; color: {AMBER}; }}
QLabel#Mono {{ font-family: "{MONO}", Consolas, monospace; }}
QLabel#MonoMuted {{ font-family: "{MONO}", Consolas, monospace; color: {MUTED};
                    font-size: {SMALL}px; }}
QLabel#SpeakerId {{ font-family: "{MONO}", Consolas, monospace; font-size: 15px;
                    font-weight: 500; }}
QLabel#Readout {{ font-family: "{MONO}", Consolas, monospace; font-size: {READOUT}px;
                  font-weight: 500; }}
QLabel#Figure {{ font-family: "{MONO}", Consolas, monospace; font-size: 15px;
                 font-weight: 500; }}
QLabel#Prompt {{ font-size: {PROMPT}px; line-height: 140%; }}
QLabel#AppName {{ font-weight: 600; }}
QLabel#Step {{ color: {MUTED}; }}
QLabel#StepDone {{ color: {INK_2}; }}
QLabel#StepCurrent {{ color: {INK}; font-weight: 600; }}

QFrame#Rule {{ background: {RULE}; border: none; }}
QWidget#TopBar {{ background: {PAPER}; }}

/* ---- buttons ---- */
QPushButton {{
    background: transparent; border: 1px solid {RULE_STRONG}; border-radius: 4px;
    padding: 7px 16px; min-height: 20px; font-weight: 500;
}}
QPushButton:hover {{ background: {HOVER}; }}
QPushButton:pressed {{ background: {RULE}; }}
QPushButton:disabled {{ color: #aeaa9e; border-color: {RULE}; }}
QPushButton#Primary {{ background: {INK}; color: {PAPER}; border: 1px solid {INK}; }}
QPushButton#Primary:hover {{ background: #000000; }}
QPushButton#Primary:disabled {{ background: #c9c6bc; border-color: #c9c6bc; color: {PAPER}; }}
QPushButton#Record {{ background: {RED}; color: white; border: 1px solid {RED}; }}
QPushButton#Record:hover {{ background: #a93226; }}
QPushButton#Record:disabled {{ background: #e3b9b3; border-color: #e3b9b3; color: white; }}
QPushButton#Quiet {{ border: none; padding: 7px 0; color: {INK_2}; text-decoration: underline; }}
QPushButton#Quiet:hover {{ color: {INK}; background: transparent; }}
QPushButton#Quiet:disabled {{ color: #b9b5a8; }}
QPushButton#Option {{
    text-align: left; border: none; border-top: 1px solid {RULE}; border-radius: 0;
    padding: 18px 12px;
}}
QPushButton#Option:hover {{ background: {HOVER}; }}
QLabel#OptionTitle {{ font-size: 17px; font-weight: 600; background: transparent; }}
QLabel#OptionText {{ color: {INK_2}; background: transparent; }}

/* ---- inputs ---- */
QLineEdit, QComboBox, QPlainTextEdit, QTextBrowser {{
    background: {FIELD}; border: 1px solid {RULE_STRONG}; border-radius: 3px;
    padding: 6px 8px; selection-background-color: {INK}; selection-color: {PAPER};
}}
QLineEdit:focus, QComboBox:focus, QPlainTextEdit:focus {{ border: 1px solid {INK}; }}
QLineEdit[invalid="true"], QComboBox[invalid="true"] {{ border: 1px solid {RED}; }}
QComboBox::drop-down {{ border: none; width: 26px; }}
QComboBox::down-arrow {{ image: url({CHEVRON_ICON}); width: 12px; height: 12px; }}
QComboBox QAbstractItemView {{
    background: {FIELD}; border: 1px solid {RULE_STRONG}; outline: none;
    selection-background-color: {HOVER}; selection-color: {INK};
}}
QComboBox QAbstractItemView::item {{ min-height: 26px; padding: 0 6px; }}

QPlainTextEdit#Transcript {{ font-size: 20px; padding: 10px 12px; }}
QTextBrowser#Document {{
    background: transparent; border: none; border-top: 1px solid {RULE};
    border-bottom: 1px solid {RULE}; padding: 0;
}}

/* ---- checkboxes ---- */
QCheckBox {{ spacing: 10px; }}
QCheckBox::indicator {{
    width: 16px; height: 16px; border: 1px solid {INK_2}; border-radius: 2px;
    background: {FIELD};
}}
QCheckBox::indicator:checked {{
    background: {INK}; border-color: {INK}; image: url({CHECK_ICON});
}}

/* ---- lists ---- */
/* Type-ahead suggestions (QCompleter) open in their own popup window, outside the combo box. */
QListView {{
    background: {FIELD}; color: {INK}; border: 1px solid {RULE_STRONG}; outline: none;
    selection-background-color: {HOVER}; selection-color: {INK};
}}
QListView::item {{ min-height: 26px; padding: 0 6px; }}
QListWidget {{ background: transparent; border: none; outline: none; }}
QListWidget::item {{ border-bottom: 1px solid {RULE}; padding: 7px 2px; }}
QListWidget::item:selected {{ background: {HOVER}; color: {INK}; }}
QListWidget::item:hover {{ background: {HOVER}; }}

/* ---- scrollbars ---- */
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 0; }}
QScrollBar::handle:vertical {{ background: {RULE_STRONG}; border-radius: 4px; min-height: 30px;
                               margin: 2px; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 0; }}
QScrollBar::handle:horizontal {{ background: {RULE_STRONG}; border-radius: 4px; margin: 2px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}
"""
