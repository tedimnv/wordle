import random
from pathlib import Path

import pytest
from PySide6.QtCore import Qt

from src.app import App, MSG_INVALID, MSG_TOO_SHORT, MSG_WIN
from src.constants import LetterResult, MAX_GUESSES, WORD_LENGTH
from src.theme import ABSENT_BG, CORRECT_BG, EMPTY_BG, KEY_BG, PRESENT_BG
from src.word_bank import WordBank


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def word_bank(tmp_path: Path) -> WordBank:
    """Tiny known word lists, seeded RNG so the answer is deterministic."""
    answers = tmp_path / "answers.txt"
    answers.write_text("crane\nslate\nproud\n")
    guesses = tmp_path / "guesses.txt"
    guesses.write_text("audio\naback\nzzzaa\n")  # zzzaa is non-alpha-ish but 5 letters
    return WordBank(answers, guesses, rng=random.Random(0))


@pytest.fixture
def app(qtbot, word_bank: WordBank) -> App:
    a = App(word_bank=word_bank, reveal_step_ms=0)
    qtbot.addWidget(a)
    return a


def _type_word(app: App, word: str) -> None:
    for letter in word:
        app.type_letter(letter)


def _all_tiles_match(app: App, row: int, color: str) -> bool:
    return all(app.board.get_background(row, c) == color for c in range(WORD_LENGTH))


# ── Bootstrap ────────────────────────────────────────────────────────────────

def test_app_starts_in_playing_state(app: App):
    assert app.state.is_active


def test_app_picks_answer_from_word_bank(app: App):
    assert app.answer in {"CRANE", "SLATE", "PROUD"}


def test_message_starts_empty(app: App):
    assert app.message == ""


# ── Full winning game ────────────────────────────────────────────────────────

def test_full_winning_game(app: App):
    _type_word(app, app.answer)
    app.submit()

    assert app.state.is_won
    assert _all_tiles_match(app, 0, CORRECT_BG)
    assert app.message == MSG_WIN


def test_win_on_last_chance(app: App):
    # 5 wrong guesses then the right one
    wrong = "CRANE" if app.answer != "CRANE" else "SLATE"
    for _ in range(5):
        _type_word(app, wrong)
        app.submit()

    assert app.state.current_row == 5
    assert app.state.is_active

    _type_word(app, app.answer)
    app.submit()
    assert app.state.is_won


# ── Full losing game ─────────────────────────────────────────────────────────

def test_full_losing_game(app: App):
    wrong = "CRANE" if app.answer != "CRANE" else "SLATE"
    for _ in range(MAX_GUESSES):
        _type_word(app, wrong)
        app.submit()

    assert app.state.is_lost
    assert app.answer in app.message


# ── Partial game flow ────────────────────────────────────────────────────────

def test_backspace_removes_last_letter(app: App):
    _type_word(app, "CHE")
    app.backspace()
    assert app.board.get_letter(0, 0) == "C"
    assert app.board.get_letter(0, 1) == "H"
    assert app.board.get_letter(0, 2) == ""


def test_type_after_backspace_uses_correct_column(app: App):
    _type_word(app, "CHE")
    app.backspace()
    app.type_letter("A")
    assert app.board.get_letter(0, 0) == "C"
    assert app.board.get_letter(0, 1) == "H"
    assert app.board.get_letter(0, 2) == "A"
    assert app.board.get_letter(0, 3) == ""


def test_typing_past_five_letters_is_ignored(app: App):
    _type_word(app, "CRANES")  # 6 letters — last one dropped
    assert "".join(app.board.get_letter(0, c) for c in range(WORD_LENGTH)) == "CRANE"
    # nothing spilled to the next row
    assert app.board.get_letter(1, 0) == ""


def test_backspace_on_empty_row_is_noop(app: App):
    app.backspace()
    assert app.board.get_letter(0, 0) == ""


# ── Submit validation ───────────────────────────────────────────────────────

def test_submit_with_too_few_letters_shows_message(app: App):
    _type_word(app, "CHE")
    app.submit()
    assert app.message == MSG_TOO_SHORT
    assert app.state.current_row == 0


def test_submit_with_unknown_word_shows_message(app: App):
    _type_word(app, "ZZZZZ")
    app.submit()
    assert app.message == MSG_INVALID
    assert app.state.current_row == 0


def test_valid_unknown_5_letter_word_is_consumed_as_guess(app: App):
    # "AUDIO" is in our guesses but not answers
    _type_word(app, "AUDIO")
    app.submit()
    assert app.state.current_row == 1
    # message clears after successful (non-winning, non-losing) submit
    assert app.message == ""


def test_message_clears_when_user_types_after_error(app: App):
    _type_word(app, "ZZZZZ")
    app.submit()
    assert app.message == MSG_INVALID
    app.backspace()
    assert app.message == ""


# ── Keyboard color updates ───────────────────────────────────────────────────

def test_keyboard_keys_update_after_guess(app: App):
    answer = app.answer
    guess = answer  # win immediately
    _type_word(app, guess)
    app.submit()
    for letter in answer:
        assert app.keyboard.get_key_background(letter) == CORRECT_BG


def test_keyboard_tracks_best_result_across_guesses(app: App):
    # Force a controlled scenario: type the first letter of the answer
    # twice — first as a wrong guess where it lands wrong, then as the
    # correct answer. Confirm the key never downgrades.
    answer = app.answer  # e.g. "CRANE"
    other = "SLATE" if answer != "SLATE" else "PROUD"

    _type_word(app, other)
    app.submit()
    for letter, result in zip(other, app.state.guesses[0]):
        if result != LetterResult.CORRECT:
            assert app.keyboard.get_key_background(letter) != CORRECT_BG

    # Now win
    _type_word(app, answer)
    app.submit()
    for letter in answer:
        assert app.keyboard.get_key_background(letter) == CORRECT_BG


# ── New game ─────────────────────────────────────────────────────────────────

def test_new_game_resets_after_win(app: App):
    _type_word(app, app.answer)
    app.submit()
    assert app.state.is_won

    app.new_game()
    assert app.state.is_active
    assert app.state.current_row == 0
    assert app.message == ""
    for r in range(MAX_GUESSES):
        for c in range(WORD_LENGTH):
            assert app.board.get_letter(r, c) == ""
            assert app.board.get_background(r, c) == EMPTY_BG
    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        assert app.keyboard.get_key_background(letter) == KEY_BG


def test_new_game_resets_after_loss(app: App):
    wrong = "CRANE" if app.answer != "CRANE" else "SLATE"
    for _ in range(MAX_GUESSES):
        _type_word(app, wrong)
        app.submit()
    assert app.state.is_lost

    app.new_game()
    assert app.state.is_active


# ── Input blocked when game inactive ─────────────────────────────────────────

def test_input_blocked_after_win(app: App):
    _type_word(app, app.answer)
    app.submit()
    assert app.state.is_won

    app.type_letter("A")
    assert app.board.get_letter(1, 0) == ""

    app.submit()  # should be silent
    app.backspace()  # should be silent
    assert app.state.is_won


def test_input_blocked_after_loss(app: App):
    wrong = "CRANE" if app.answer != "CRANE" else "SLATE"
    for _ in range(MAX_GUESSES):
        _type_word(app, wrong)
        app.submit()
    assert app.state.is_lost

    app.type_letter("A")
    app.submit()
    app.backspace()
    assert app.state.is_lost


# ── Mouse path: on-screen keyboard wired correctly ───────────────────────────

def test_on_screen_keyboard_letter_click_types(app: App):
    app.keyboard.click_key("A")
    assert app.board.get_letter(0, 0) == "A"


def test_on_screen_keyboard_backspace_click_removes(app: App):
    app.type_letter("A")
    app.keyboard.click_backspace()
    assert app.board.get_letter(0, 0) == ""


def test_on_screen_keyboard_enter_click_submits(app: App):
    _type_word(app, app.answer)
    app.keyboard.click_enter()
    assert app.state.is_won


# ── Physical keyboard ────────────────────────────────────────────────────────

def test_physical_letter_key_types(app: App, qtbot):
    qtbot.keyClick(app, Qt.Key.Key_A)
    assert app.board.get_letter(0, 0) == "A"


def test_physical_enter_submits(app: App, qtbot):
    _type_word(app, app.answer)
    qtbot.keyClick(app, Qt.Key.Key_Return)
    assert app.state.is_won


def test_physical_backspace_removes(app: App, qtbot):
    app.type_letter("A")
    qtbot.keyClick(app, Qt.Key.Key_Backspace)
    assert app.board.get_letter(0, 0) == ""


def test_physical_non_letter_key_is_ignored(app: App, qtbot):
    qtbot.keyClick(app, Qt.Key.Key_F1)
    assert app.board.get_letter(0, 0) == ""


# ── Direct-API input guards ──────────────────────────────────────────────────

def test_type_letter_with_multichar_input_is_ignored(app: App):
    app.type_letter("AB")
    assert app.board.get_letter(0, 0) == ""


def test_type_letter_with_digit_is_ignored(app: App):
    app.type_letter("1")
    assert app.board.get_letter(0, 0) == ""


# ── Defaults ─────────────────────────────────────────────────────────────────

def test_default_word_bank_used_when_none_provided(qtbot):
    a = App(reveal_step_ms=0)
    qtbot.addWidget(a)
    assert a.answer  # something was picked
    assert len(a.answer) == WORD_LENGTH


def test_animated_typing_path(qtbot, word_bank):
    """When animations are on, typing uses the animated path."""
    a = App(word_bank=word_bank, reveal_step_ms=50)
    qtbot.addWidget(a)
    a.type_letter("A")
    assert a.board.get_letter(0, 0) == "A"
    qtbot.wait(200)  # let fade-in finish before teardown


def test_animated_backspace_path(qtbot, word_bank):
    """When animations are on, backspace fades the letter out."""
    a = App(word_bank=word_bank, reveal_step_ms=50)
    qtbot.addWidget(a)
    a.type_letter("A")
    qtbot.wait(200)
    a.backspace()
    qtbot.wait(300)
    assert a.board.get_letter(0, 0) == ""
