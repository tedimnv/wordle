from PySide6.QtGui import QPixmap

from src.constants import LetterResult
from src.theme import (
    CORRECT_BG,
    EMPTY_BG,
    EMPTY_BORDER,
    REVEALED_TEXT,
    TYPED_BORDER,
)
from src.tile import Tile, TYPE_IN_INITIAL_SCALE


def _tile(qtbot) -> Tile:
    t = Tile()
    qtbot.addWidget(t)
    return t


def _force_paint(tile: Tile) -> None:
    """Render the tile into a pixmap so paintEvent runs in tests."""
    pix = QPixmap(tile.size())
    tile.render(pix)


# ── Initial state ────────────────────────────────────────────────────────────

def test_tile_starts_empty(qtbot):
    t = _tile(qtbot)
    assert t.letter == ""
    assert t.background == EMPTY_BG
    assert t.border == EMPTY_BORDER


def test_tile_paint_runs_for_default_state(qtbot):
    t = _tile(qtbot)
    _force_paint(t)


# ── Instant API ──────────────────────────────────────────────────────────────

def test_show_letter_instant(qtbot):
    t = _tile(qtbot)
    t.show_letter("a")
    assert t.letter == "A"
    assert t.border == TYPED_BORDER


def test_reveal_instant(qtbot):
    t = _tile(qtbot)
    t.reveal(LetterResult.CORRECT)
    assert t.background == CORRECT_BG
    assert t.border == CORRECT_BG


def test_clear_resets_everything(qtbot):
    t = _tile(qtbot)
    t.show_letter("A")
    t.reveal(LetterResult.CORRECT)
    t.clear()
    assert t.letter == ""
    assert t.background == EMPTY_BG
    assert t.border == EMPTY_BORDER


# ── show_letter_animated ─────────────────────────────────────────────────────

def test_show_letter_animated_zero_duration(qtbot):
    t = _tile(qtbot)
    t.show_letter_animated("A", duration_ms=0)
    assert t.letter == "A"
    # No animation = stays at default scale/opacity
    assert t.scaleValue == 1.0
    assert t.opacityValue == 1.0


def test_show_letter_animated_starts_at_initial_values(qtbot):
    t = _tile(qtbot)
    t.show_letter_animated("A", duration_ms=80)
    assert t.letter == "A"
    # Animation starts: scale dropped to 0.8, opacity to 0
    assert t.scaleValue == TYPE_IN_INITIAL_SCALE
    assert t.opacityValue == 0.0
    qtbot.wait(200)
    # After animation: returned to defaults
    assert abs(t.scaleValue - 1.0) < 0.05
    assert abs(t.opacityValue - 1.0) < 0.05


def test_paint_runs_with_animated_transforms(qtbot):
    t = _tile(qtbot)
    t.show_letter("A")
    # Drive properties directly to non-default values
    t._set_scale(0.8)
    t._set_flip_x(0.5)
    t._set_opacity(0.5)
    _force_paint(t)


# ── flip_reveal ──────────────────────────────────────────────────────────────

def test_flip_reveal_zero_duration(qtbot):
    t = _tile(qtbot)
    done = []
    t.flip_reveal(LetterResult.CORRECT, duration_ms=0, on_done=lambda: done.append(True))
    assert t.background == CORRECT_BG
    assert done == [True]


def test_flip_reveal_zero_duration_without_callback(qtbot):
    t = _tile(qtbot)
    t.flip_reveal(LetterResult.PRESENT, duration_ms=0)
    assert t.background != EMPTY_BG


def test_flip_reveal_animated_completes(qtbot):
    t = _tile(qtbot)
    done = []
    t.flip_reveal(LetterResult.CORRECT, duration_ms=40, on_done=lambda: done.append(True))
    # Immediately after start: still empty (flip is in shrink phase)
    assert t.background == EMPTY_BG
    qtbot.wait(200)
    assert done == [True]
    assert t.background == CORRECT_BG


def test_flip_reveal_animated_without_callback(qtbot):
    t = _tile(qtbot)
    t.flip_reveal(LetterResult.PRESENT, duration_ms=40)
    qtbot.wait(200)
    assert t.background != EMPTY_BG


# ── Qt animation property accessors ──────────────────────────────────────────

def test_scale_property_setter_triggers_repaint(qtbot):
    t = _tile(qtbot)
    t._set_scale(0.5)
    assert t.scaleValue == 0.5
    _force_paint(t)


def test_flip_x_property_setter(qtbot):
    t = _tile(qtbot)
    t._set_flip_x(0.0)
    assert t.flipXValue == 0.0


def test_opacity_property_setter(qtbot):
    t = _tile(qtbot)
    t._set_opacity(0.0)
    assert t.opacityValue == 0.0


# ── Inspection helpers ───────────────────────────────────────────────────────

def test_revealed_text_color(qtbot):
    t = _tile(qtbot)
    t.reveal(LetterResult.CORRECT)
    # internal state is exposed via paintEvent; we sanity check via attribute
    assert t._text_color == REVEALED_TEXT


# ── clear_animated ───────────────────────────────────────────────────────────

def test_clear_animated_zero_duration(qtbot):
    t = _tile(qtbot)
    t.show_letter("A")
    done = []
    t.clear_animated(duration_ms=0, on_done=lambda: done.append(True))
    assert t.letter == ""
    assert t.border == EMPTY_BORDER
    assert done == [True]


def test_clear_animated_zero_duration_no_callback(qtbot):
    t = _tile(qtbot)
    t.show_letter("A")
    t.clear_animated(duration_ms=0)
    assert t.letter == ""


def test_clear_animated_completes(qtbot):
    t = _tile(qtbot)
    t.show_letter("A")
    done = []
    t.clear_animated(duration_ms=40, on_done=lambda: done.append(True))
    # Letter still rendered while animation is mid-flight
    assert t.letter == "A"
    qtbot.wait(150)
    assert done == [True]
    assert t.letter == ""
    assert t.border == EMPTY_BORDER
    assert abs(t.scaleValue - 1.0) < 0.01  # reset after finish


def test_clear_animated_without_callback(qtbot):
    t = _tile(qtbot)
    t.show_letter("A")
    t.clear_animated(duration_ms=40)
    qtbot.wait(150)
    assert t.letter == ""


# ── Animation lifecycle ──────────────────────────────────────────────────────

def test_show_letter_stops_running_animation(qtbot):
    """Typing a new letter mid-fade-in cancels the prior animation."""
    t = _tile(qtbot)
    t.show_letter_animated("A", duration_ms=100)
    # Immediately type a new letter — should cancel prior animation
    t.show_letter("B")
    # Tile is fully visible at instant state
    assert t.letter == "B"
    assert t.scaleValue == 1.0
    assert t.opacityValue == 1.0


def test_clear_stops_running_animation(qtbot):
    """Resetting (clear) cancels any in-flight animation."""
    t = _tile(qtbot)
    t.show_letter_animated("A", duration_ms=100)
    t.clear()
    assert t.letter == ""
    assert t.scaleValue == 1.0
    assert t.opacityValue == 1.0
    assert t.flipXValue == 1.0


def test_clear_animated_then_show_letter_cancels(qtbot):
    """If user types during a disappear animation, the new letter wins."""
    t = _tile(qtbot)
    t.show_letter("A")
    t.clear_animated(duration_ms=100)
    t.show_letter_animated("B", duration_ms=40)
    qtbot.wait(150)
    assert t.letter == "B"
