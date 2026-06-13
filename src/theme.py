from __future__ import annotations

from src.constants import LetterResult

# ── Tile backgrounds ─────────────────────────────────────────────────────────
EMPTY_BG = "#ffffff"
CORRECT_BG = "#6aaa64"
PRESENT_BG = "#c9b458"
ABSENT_BG = "#787c7e"

# ── Borders ──────────────────────────────────────────────────────────────────
EMPTY_BORDER = "#d3d6da"
TYPED_BORDER = "#878a8c"

# ── Text ─────────────────────────────────────────────────────────────────────
EMPTY_TEXT = "#1a1a1b"
REVEALED_TEXT = "#ffffff"

# ── Mapping ──────────────────────────────────────────────────────────────────
RESULT_BG: dict[LetterResult, str] = {
    LetterResult.CORRECT: CORRECT_BG,
    LetterResult.PRESENT: PRESENT_BG,
    LetterResult.ABSENT: ABSENT_BG,
}

# ── Tile geometry ────────────────────────────────────────────────────────────
TILE_SIZE_PX = 62
TILE_GAP_PX = 5
TILE_BORDER_PX = 2
TILE_FONT_FAMILY = "Helvetica Neue"
TILE_FONT_PX = 26

# ── Keyboard ─────────────────────────────────────────────────────────────────
KEY_BG = "#d3d6da"
KEY_TEXT = "#1a1a1b"
KEY_FONT_FAMILY = "Helvetica Neue"
KEY_FONT_PX = 13
KEY_WIDTH_PX = 44
KEY_WIDE_WIDTH_PX = 70
KEY_HEIGHT_PX = 56
KEY_RADIUS_PX = 4
KEY_ROW_SPACING_PX = 6
KEY_GAP_PX = 4
