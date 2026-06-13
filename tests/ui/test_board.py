import pytest

from src.board import Board
from src.constants import LetterResult, MAX_GUESSES, WORD_LENGTH
from src.theme import (
    ABSENT_BG,
    CORRECT_BG,
    EMPTY_BG,
    EMPTY_BORDER,
    PRESENT_BG,
    TYPED_BORDER,
)


def _board(qtbot) -> Board:
    b = Board()
    qtbot.addWidget(b)
    return b


# ── Construction ─────────────────────────────────────────────────────────────

def test_board_constructs_full_grid(qtbot):
    board = _board(qtbot)
    for r in range(MAX_GUESSES):
        for c in range(WORD_LENGTH):
            assert board.get_letter(r, c) == ""
            assert board.get_background(r, c) == EMPTY_BG
            assert board.get_border(r, c) == EMPTY_BORDER


# ── Typing ───────────────────────────────────────────────────────────────────

def test_set_letter_shows_letter_and_dark_border(qtbot):
    board = _board(qtbot)
    board.set_letter(0, 0, "A")
    assert board.get_letter(0, 0) == "A"
    assert board.get_border(0, 0) == TYPED_BORDER


def test_set_letter_uppercases(qtbot):
    board = _board(qtbot)
    board.set_letter(0, 0, "a")
    assert board.get_letter(0, 0) == "A"


def test_clear_letter_reverts_to_empty(qtbot):
    board = _board(qtbot)
    board.set_letter(2, 3, "X")
    board.clear_letter(2, 3)
    assert board.get_letter(2, 3) == ""
    assert board.get_border(2, 3) == EMPTY_BORDER
    assert board.get_background(2, 3) == EMPTY_BG


@pytest.mark.parametrize("row,col", [
    (-1, 0),
    (MAX_GUESSES, 0),
    (0, -1),
    (0, WORD_LENGTH),
    (0, 99),
])
def test_set_letter_out_of_bounds_is_silent_noop(qtbot, row: int, col: int):
    board = _board(qtbot)
    board.set_letter(row, col, "X")
    assert board.get_letter(0, 0) == ""


def test_clear_letter_out_of_bounds_is_silent_noop(qtbot):
    board = _board(qtbot)
    board.clear_letter(99, 99)


# ── Revealing ────────────────────────────────────────────────────────────────

def test_reveal_row_colors_each_tile(qtbot):
    board = _board(qtbot)
    for c, letter in enumerate("CHEAP"):
        board.set_letter(0, c, letter)

    results = [
        LetterResult.CORRECT,
        LetterResult.CORRECT,
        LetterResult.PRESENT,
        LetterResult.PRESENT,
        LetterResult.ABSENT,
    ]
    board.reveal_row(0, results)

    assert board.get_background(0, 0) == CORRECT_BG
    assert board.get_background(0, 1) == CORRECT_BG
    assert board.get_background(0, 2) == PRESENT_BG
    assert board.get_background(0, 3) == PRESENT_BG
    assert board.get_background(0, 4) == ABSENT_BG


def test_reveal_row_does_not_affect_other_rows(qtbot):
    board = _board(qtbot)
    results = [LetterResult.CORRECT] * WORD_LENGTH
    board.reveal_row(2, results)

    for r in (0, 1, 3, 4, 5):
        for c in range(WORD_LENGTH):
            assert board.get_background(r, c) == EMPTY_BG
            assert board.get_border(r, c) == EMPTY_BORDER


def test_reveal_row_with_wrong_result_count_raises(qtbot):
    board = _board(qtbot)
    with pytest.raises(ValueError):
        board.reveal_row(0, [LetterResult.CORRECT] * 4)


def test_reveal_row_out_of_bounds_is_silent_noop(qtbot):
    board = _board(qtbot)
    board.reveal_row(99, [LetterResult.CORRECT] * WORD_LENGTH)


# ── Reset ────────────────────────────────────────────────────────────────────

def test_reset_clears_all_tiles(qtbot):
    board = _board(qtbot)
    board.set_letter(0, 0, "A")
    board.set_letter(1, 2, "B")
    board.reveal_row(2, [LetterResult.CORRECT] * WORD_LENGTH)
    board.reset()

    for r in range(MAX_GUESSES):
        for c in range(WORD_LENGTH):
            assert board.get_letter(r, c) == ""
            assert board.get_background(r, c) == EMPTY_BG
            assert board.get_border(r, c) == EMPTY_BORDER


# ── Test helpers themselves ──────────────────────────────────────────────────

def test_get_letter_out_of_bounds_returns_empty(qtbot):
    assert _board(qtbot).get_letter(99, 99) == ""


def test_get_background_out_of_bounds_returns_empty(qtbot):
    assert _board(qtbot).get_background(99, 99) == ""


def test_get_border_out_of_bounds_returns_empty(qtbot):
    assert _board(qtbot).get_border(99, 99) == ""


# ── Animated reveal ──────────────────────────────────────────────────────────

def test_reveal_row_animated_step_zero_is_synchronous(qtbot):
    board = _board(qtbot)
    done = []
    results = [LetterResult.CORRECT] * WORD_LENGTH
    board.reveal_row_animated(0, results, step_ms=0, on_done=lambda: done.append(True))
    for c in range(WORD_LENGTH):
        assert board.get_background(0, c) == CORRECT_BG
    assert done == [True]


def test_reveal_row_animated_step_zero_no_callback(qtbot):
    board = _board(qtbot)
    board.reveal_row_animated(0, [LetterResult.CORRECT] * WORD_LENGTH, step_ms=0)
    assert board.get_background(0, 0) == CORRECT_BG


def test_reveal_row_animated_flip_completes_without_callback(qtbot):
    board = _board(qtbot)
    board.reveal_row_animated(
        0, [LetterResult.CORRECT] * WORD_LENGTH, step_ms=10, flip_ms=20
    )
    qtbot.wait(400)
    for c in range(WORD_LENGTH):
        assert board.get_background(0, c) == CORRECT_BG


def test_reveal_row_animated_invokes_on_done(qtbot):
    board = _board(qtbot)
    done = []
    board.reveal_row_animated(
        0, [LetterResult.CORRECT] * WORD_LENGTH,
        step_ms=10, flip_ms=20,
        on_done=lambda: done.append(True),
    )
    qtbot.wait(400)
    assert done == [True]
    for c in range(WORD_LENGTH):
        assert board.get_background(0, c) == CORRECT_BG


def test_reveal_row_animated_does_not_color_immediately(qtbot):
    """With a flip animation, color is applied at the flip midpoint, not at t=0."""
    board = _board(qtbot)
    board.reveal_row_animated(
        0, [LetterResult.CORRECT] * WORD_LENGTH, step_ms=200, flip_ms=200
    )
    # Right after start: first tile is still shrinking; color not yet swapped.
    assert board.get_background(0, 0) == EMPTY_BG
    qtbot.wait(1500)  # let everything finish before teardown


def test_reveal_row_animated_out_of_bounds_is_noop(qtbot):
    board = _board(qtbot)
    board.reveal_row_animated(99, [LetterResult.CORRECT] * WORD_LENGTH, step_ms=0)


def test_reveal_row_animated_wrong_result_count_raises(qtbot):
    board = _board(qtbot)
    with pytest.raises(ValueError):
        board.reveal_row_animated(0, [LetterResult.CORRECT] * 4, step_ms=0)


# ── set_letter_animated ──────────────────────────────────────────────────────

def test_set_letter_animated_zero_duration_is_synchronous(qtbot):
    board = _board(qtbot)
    board.set_letter_animated(0, 0, "A", duration_ms=0)
    assert board.get_letter(0, 0) == "A"
    assert board.get_border(0, 0) == TYPED_BORDER


def test_set_letter_animated_positive_duration_sets_letter_immediately(qtbot):
    board = _board(qtbot)
    board.set_letter_animated(0, 0, "A", duration_ms=50)
    assert board.get_letter(0, 0) == "A"
    qtbot.wait(150)  # let the fade-in animation finish before teardown


def test_set_letter_animated_out_of_bounds_is_noop(qtbot):
    board = _board(qtbot)
    board.set_letter_animated(99, 99, "X", duration_ms=0)
    assert board.get_letter(0, 0) == ""


# ── clear_letter_animated ────────────────────────────────────────────────────

def test_clear_letter_animated_zero_duration(qtbot):
    board = _board(qtbot)
    board.set_letter(0, 0, "A")
    board.clear_letter_animated(0, 0, duration_ms=0)
    assert board.get_letter(0, 0) == ""


def test_clear_letter_animated_completes(qtbot):
    board = _board(qtbot)
    board.set_letter(0, 0, "A")
    board.clear_letter_animated(0, 0, duration_ms=40)
    qtbot.wait(150)
    assert board.get_letter(0, 0) == ""


def test_clear_letter_animated_out_of_bounds_is_noop(qtbot):
    board = _board(qtbot)
    board.clear_letter_animated(99, 99, duration_ms=0)


# ── reset cancels pending reveal scheduling ──────────────────────────────────

def test_reset_cancels_pending_reveal_timers(qtbot):
    board = _board(qtbot)
    results = [LetterResult.CORRECT] * WORD_LENGTH
    # Schedule a slow reveal so several timers are pending
    board.reveal_row_animated(0, results, step_ms=400, flip_ms=40)
    # Reset before later tiles' timers fire
    qtbot.wait(50)
    board.reset()
    qtbot.wait(2000)  # well past when stale timers would have fired
    # No tile should have ended up colored
    for c in range(WORD_LENGTH):
        assert board.get_background(0, c) == EMPTY_BG


# ── flip reveal (via animated row) ───────────────────────────────────────────

def test_reveal_row_animated_default_flip_duration(qtbot):
    board = _board(qtbot)
    done = []
    results = [LetterResult.CORRECT] * WORD_LENGTH
    board.reveal_row_animated(
        0, results, step_ms=20, flip_ms=40,
        on_done=lambda: done.append(True),
    )
    qtbot.wait(500)
    assert done == [True]
