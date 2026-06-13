import pytest

from src.constants import LetterResult
from src.evaluator import Evaluator

CORRECT = LetterResult.CORRECT
PRESENT = LetterResult.PRESENT
ABSENT = LetterResult.ABSENT


# ── Happy path ────────────────────────────────────────────────────────────────

def test_all_correct():
    assert Evaluator.evaluate("CRANE", "CRANE") == [CORRECT] * 5


def test_all_absent():
    assert Evaluator.evaluate("ZZZZZ", "CRANE") == [ABSENT] * 5


def test_mix_of_all_three():
    # CHEAP vs CHASE: C=cor, H=cor, E=present, A=present, P=absent
    assert Evaluator.evaluate("CHEAP", "CHASE") == [
        CORRECT, CORRECT, PRESENT, PRESENT, ABSENT
    ]


# ── Duplicate letter edge cases ───────────────────────────────────────────────

def test_dup_speed_vs_spree():
    # S=cor, P=cor, E=present, E=correct, D=absent
    assert Evaluator.evaluate("SPEED", "SPREE") == [
        CORRECT, CORRECT, PRESENT, CORRECT, ABSENT
    ]


def test_dup_aabbb_vs_abbaa():
    # AABBB vs ABBAA:
    # pass 1: pos 0 A==A, pos 2 B==B.
    # remaining: [_, B, _, A, A]
    # pass 2: pos 1 A → present; pos 3 B → present; pos 4 B → absent (no B left)
    assert Evaluator.evaluate("AABBB", "ABBAA") == [
        CORRECT, PRESENT, CORRECT, PRESENT, ABSENT
    ]


def test_dup_abbey_vs_kebab():
    # pass 1: pos 2 B==B.
    # remaining: [K, E, _, A, B]
    # pass 2: A→present, B→present (B at pos 4), E→present, Y→absent
    assert Evaluator.evaluate("ABBEY", "KEBAB") == [
        PRESENT, PRESENT, CORRECT, PRESENT, ABSENT
    ]


def test_single_letter_in_guess_against_double_in_answer():
    # CRANE vs ERROR: pos 1 R==R correct.
    # remaining: [E, _, R, O, R]
    # pos 0 C absent; pos 2 A absent; pos 3 N absent; pos 4 E present
    assert Evaluator.evaluate("CRANE", "ERROR") == [
        ABSENT, CORRECT, ABSENT, ABSENT, PRESENT
    ]


def test_dup_speed_vs_steed():
    # Both Es match exactly in pass 1, so no PRESENT.
    assert Evaluator.evaluate("SPEED", "STEED") == [
        CORRECT, ABSENT, CORRECT, CORRECT, CORRECT
    ]


def test_dup_in_guess_single_in_answer_aligned_with_second():
    # ALPHA vs PIZZA:
    # Guess has A at positions 0 and 4. Answer has only one A — at pos 4,
    # which lines up with the SECOND A in the guess.
    # Pass 1 consumes the answer's A for the exact match at pos 4.
    # Pass 2 finds no A left, so the A at pos 0 is ABSENT (not PRESENT).
    # The P at pos 2 of guess exists at pos 0 of answer → PRESENT.
    assert Evaluator.evaluate("ALPHA", "PIZZA") == [
        ABSENT, ABSENT, PRESENT, ABSENT, CORRECT
    ]


# ── Case insensitivity ────────────────────────────────────────────────────────

def test_case_insensitive_lowercase():
    assert Evaluator.evaluate("crane", "crane") == [CORRECT] * 5


def test_case_insensitive_mixed():
    assert (
        Evaluator.evaluate("CrAnE", "cRaNe")
        == Evaluator.evaluate("CRANE", "CRANE")
    )


# ── Input validation ─────────────────────────────────────────────────────────

@pytest.mark.parametrize("bad,label", [
    ("CRAN",   "guess"),
    ("CRANES", "guess"),
    ("",       "guess"),
])
def test_guess_wrong_length_raises(bad: str, label: str):
    with pytest.raises(ValueError, match=label):
        Evaluator.evaluate(bad, "CRANE")


@pytest.mark.parametrize("bad,label", [
    ("CRAN",   "answer"),
    ("CRANES", "answer"),
])
def test_answer_wrong_length_raises(bad: str, label: str):
    with pytest.raises(ValueError, match=label):
        Evaluator.evaluate("CRANE", bad)


@pytest.mark.parametrize("bad", ["CRAN3", "CR NE"])
def test_guess_non_alpha_raises(bad: str):
    with pytest.raises(ValueError, match="guess"):
        Evaluator.evaluate(bad, "CRANE")


def test_answer_non_alpha_raises():
    with pytest.raises(ValueError, match="answer"):
        Evaluator.evaluate("CRANE", "CRAN3")
