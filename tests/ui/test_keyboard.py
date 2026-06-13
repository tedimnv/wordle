import pytest

from src.constants import LetterResult
from src.keyboard import BACKSPACE_LABEL, ENTER_LABEL, Keyboard
from src.theme import ABSENT_BG, CORRECT_BG, KEY_BG, PRESENT_BG

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def _kb(qtbot, **callbacks) -> Keyboard:
    k = Keyboard(**callbacks)
    qtbot.addWidget(k)
    return k


# ── Initial state ────────────────────────────────────────────────────────────

def test_all_letter_keys_present(qtbot):
    kb = _kb(qtbot)
    for letter in ALPHABET:
        assert kb.has_letter_key(letter)


def test_enter_and_backspace_keys_present(qtbot):
    kb = _kb(qtbot)
    kb.click_enter()
    kb.click_backspace()


def test_all_keys_start_with_default_background(qtbot):
    kb = _kb(qtbot)
    for letter in ALPHABET:
        assert kb.get_key_background(letter) == KEY_BG


# ── update_key — color ───────────────────────────────────────────────────────

@pytest.mark.parametrize("result,expected_bg", [
    (LetterResult.CORRECT, CORRECT_BG),
    (LetterResult.PRESENT, PRESENT_BG),
    (LetterResult.ABSENT, ABSENT_BG),
])
def test_update_key_sets_background(qtbot, result, expected_bg):
    kb = _kb(qtbot)
    kb.update_key("A", result)
    assert kb.get_key_background("A") == expected_bg


def test_update_key_is_case_insensitive(qtbot):
    kb = _kb(qtbot)
    kb.update_key("a", LetterResult.CORRECT)
    assert kb.get_key_background("A") == CORRECT_BG


def test_update_key_unknown_letter_is_noop(qtbot):
    kb = _kb(qtbot)
    kb.update_key("1", LetterResult.CORRECT)


# ── No-downgrade rule ────────────────────────────────────────────────────────

def test_correct_does_not_downgrade_to_present(qtbot):
    kb = _kb(qtbot)
    kb.update_key("A", LetterResult.CORRECT)
    kb.update_key("A", LetterResult.PRESENT)
    assert kb.get_key_background("A") == CORRECT_BG


def test_correct_does_not_downgrade_to_absent(qtbot):
    kb = _kb(qtbot)
    kb.update_key("A", LetterResult.CORRECT)
    kb.update_key("A", LetterResult.ABSENT)
    assert kb.get_key_background("A") == CORRECT_BG


def test_present_does_not_downgrade_to_absent(qtbot):
    kb = _kb(qtbot)
    kb.update_key("A", LetterResult.PRESENT)
    kb.update_key("A", LetterResult.ABSENT)
    assert kb.get_key_background("A") == PRESENT_BG


def test_absent_upgrades_to_present(qtbot):
    kb = _kb(qtbot)
    kb.update_key("A", LetterResult.ABSENT)
    kb.update_key("A", LetterResult.PRESENT)
    assert kb.get_key_background("A") == PRESENT_BG


def test_absent_upgrades_to_correct(qtbot):
    kb = _kb(qtbot)
    kb.update_key("A", LetterResult.ABSENT)
    kb.update_key("A", LetterResult.CORRECT)
    assert kb.get_key_background("A") == CORRECT_BG


def test_present_upgrades_to_correct(qtbot):
    kb = _kb(qtbot)
    kb.update_key("A", LetterResult.PRESENT)
    kb.update_key("A", LetterResult.CORRECT)
    assert kb.get_key_background("A") == CORRECT_BG


def test_same_state_is_idempotent(qtbot):
    kb = _kb(qtbot)
    kb.update_key("A", LetterResult.PRESENT)
    kb.update_key("A", LetterResult.PRESENT)
    assert kb.get_key_background("A") == PRESENT_BG


# ── Click callbacks ──────────────────────────────────────────────────────────

def test_clicking_letter_fires_callback_with_letter(qtbot):
    seen = []
    kb = _kb(qtbot, on_letter=seen.append)
    kb.click_key("Q")
    assert seen == ["Q"]


def test_clicking_unknown_letter_does_not_fire(qtbot):
    seen = []
    kb = _kb(qtbot, on_letter=seen.append)
    kb.click_key("1")
    assert seen == []


def test_clicking_enter_fires_callback(qtbot):
    seen = []
    kb = _kb(qtbot, on_enter=lambda: seen.append("enter"))
    kb.click_enter()
    assert seen == ["enter"]


def test_clicking_backspace_fires_callback(qtbot):
    seen = []
    kb = _kb(qtbot, on_backspace=lambda: seen.append("back"))
    kb.click_backspace()
    assert seen == ["back"]


def test_default_callbacks_do_nothing(qtbot):
    kb = _kb(qtbot)
    kb.click_key("A")
    kb.click_enter()
    kb.click_backspace()


# ── Reset ────────────────────────────────────────────────────────────────────

def test_reset_clears_all_key_colors(qtbot):
    kb = _kb(qtbot)
    for letter in "QWERTY":
        kb.update_key(letter, LetterResult.CORRECT)
    for letter in "ASDFGH":
        kb.update_key(letter, LetterResult.PRESENT)
    for letter in "ZXCVBN":
        kb.update_key(letter, LetterResult.ABSENT)

    kb.reset()

    for letter in ALPHABET:
        assert kb.get_key_background(letter) == KEY_BG


def test_reset_allows_new_state_to_take_effect(qtbot):
    kb = _kb(qtbot)
    kb.update_key("A", LetterResult.CORRECT)
    kb.reset()
    kb.update_key("A", LetterResult.ABSENT)
    assert kb.get_key_background("A") == ABSENT_BG


# ── Test helpers themselves ──────────────────────────────────────────────────

def test_get_key_background_unknown_letter_returns_empty(qtbot):
    kb = _kb(qtbot)
    assert kb.get_key_background("1") == ""


def test_labels_are_what_we_expect():
    assert ENTER_LABEL == "ENTER"
    assert BACKSPACE_LABEL == "⌫"
