from __future__ import annotations

from src.theme import (
    KEY_BG,
    KEY_FONT_FAMILY,
    KEY_FONT_PX,
    KEY_RADIUS_PX,
    KEY_TEXT,
)


def key_style(bg: str, text: str) -> str:
    return (
        f"QPushButton {{ "
        f"background-color: {bg}; "
        f"color: {text}; "
        f"border: none; "
        f"border-radius: {KEY_RADIUS_PX}px; "
        f"font: bold {KEY_FONT_PX}px '{KEY_FONT_FAMILY}'; "
        f"}}"
    )


def action_button_style() -> str:
    return (
        f"QPushButton {{ "
        f"background-color: {KEY_BG}; "
        f"color: {KEY_TEXT}; "
        f"border: none; "
        f"border-radius: {KEY_RADIUS_PX}px; "
        f"padding: 10px 24px; "
        f"font: bold {KEY_FONT_PX}px '{KEY_FONT_FAMILY}'; "
        f"}}"
    )
