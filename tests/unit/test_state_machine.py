import pytest

from src.constants import LetterResult, MAX_GUESSES, WORD_LENGTH
from src.state_machine import GameState, InvalidStateError, StateMachine

WIN = [LetterResult.CORRECT] * WORD_LENGTH
MISS = [LetterResult.ABSENT] * WORD_LENGTH
PARTIAL = [
    LetterResult.CORRECT, LetterResult.PRESENT,
    LetterResult.ABSENT, LetterResult.ABSENT, LetterResult.ABSENT,
]


def _started() -> StateMachine:
    sm = StateMachine()
    sm.start_game()
    return sm


def _lost() -> StateMachine:
    sm = _started()
    for _ in range(MAX_GUESSES):
        sm.submit_guess(MISS)
    return sm


def _won() -> StateMachine:
    sm = _started()
    sm.submit_guess(WIN)
    return sm


# ── Initial state ────────────────────────────────────────────────────────────

def test_starts_in_idle():
    assert StateMachine().state == GameState.IDLE


def test_current_row_starts_at_zero():
    assert StateMachine().current_row == 0


def test_guesses_starts_empty():
    assert StateMachine().guesses == []


# ── Tell-don't-ask predicates ────────────────────────────────────────────────

def test_predicates_in_idle():
    sm = StateMachine()
    assert not sm.is_active
    assert not sm.is_finished
    assert not sm.is_won
    assert not sm.is_lost


def test_predicates_in_playing():
    sm = _started()
    assert sm.is_active
    assert not sm.is_finished
    assert not sm.is_won
    assert not sm.is_lost


def test_predicates_in_won():
    sm = _won()
    assert not sm.is_active
    assert sm.is_finished
    assert sm.is_won
    assert not sm.is_lost


def test_predicates_in_lost():
    sm = _lost()
    assert not sm.is_active
    assert sm.is_finished
    assert not sm.is_won
    assert sm.is_lost


# ── Valid transitions ────────────────────────────────────────────────────────

def test_start_game_from_idle_moves_to_playing():
    sm = _started()
    assert sm.state == GameState.PLAYING


def test_submit_guess_non_winning_stays_playing():
    sm = _started()
    sm.submit_guess(MISS)
    assert sm.state == GameState.PLAYING


def test_submit_guess_increments_row():
    sm = _started()
    sm.submit_guess(MISS)
    assert sm.current_row == 1
    sm.submit_guess(MISS)
    assert sm.current_row == 2


def test_submit_guess_stores_result():
    sm = _started()
    sm.submit_guess(PARTIAL)
    assert sm.guesses == [PARTIAL]


def test_submit_guess_all_correct_moves_to_won():
    sm = _won()
    assert sm.state == GameState.WON


def test_submit_guess_on_row_six_without_winning_moves_to_lost():
    sm = _lost()
    assert sm.state == GameState.LOST


def test_reset_from_won_returns_to_idle():
    sm = _won()
    sm.reset()
    assert sm.state == GameState.IDLE
    assert sm.current_row == 0
    assert sm.guesses == []


def test_reset_from_lost_returns_to_idle():
    sm = _lost()
    sm.reset()
    assert sm.state == GameState.IDLE
    assert sm.current_row == 0
    assert sm.guesses == []


def test_reset_from_idle_is_no_op():
    sm = StateMachine()
    sm.reset()
    assert sm.state == GameState.IDLE


def test_reset_from_playing_returns_to_idle():
    sm = _started()
    sm.submit_guess(MISS)
    sm.reset()
    assert sm.state == GameState.IDLE
    assert sm.current_row == 0


# ── Invalid transitions ──────────────────────────────────────────────────────

def test_submit_guess_in_idle_raises():
    with pytest.raises(InvalidStateError):
        StateMachine().submit_guess(MISS)


def test_submit_guess_in_won_raises():
    with pytest.raises(InvalidStateError):
        _won().submit_guess(MISS)


def test_submit_guess_in_lost_raises():
    with pytest.raises(InvalidStateError):
        _lost().submit_guess(MISS)


def test_start_game_in_playing_raises():
    with pytest.raises(InvalidStateError):
        _started().start_game()


def test_start_game_in_won_raises():
    with pytest.raises(InvalidStateError):
        _won().start_game()


def test_start_game_in_lost_raises():
    with pytest.raises(InvalidStateError):
        _lost().start_game()


# ── Input validation ─────────────────────────────────────────────────────────

@pytest.mark.parametrize("bad", [
    [LetterResult.ABSENT] * 4,
    [LetterResult.ABSENT] * 6,
])
def test_submit_guess_with_wrong_length_raises(bad: list):
    with pytest.raises(ValueError):
        _started().submit_guess(bad)


def test_submit_guess_with_non_list_raises():
    with pytest.raises(ValueError):
        _started().submit_guess("absent")  # type: ignore[arg-type]


# ── Boundary conditions ──────────────────────────────────────────────────────

def test_lost_only_triggers_at_exactly_six_guesses():
    sm = _started()
    for _ in range(5):
        sm.submit_guess(MISS)
    assert sm.state == GameState.PLAYING
    sm.submit_guess(MISS)
    assert sm.state == GameState.LOST
    assert sm.current_row == 6


def test_win_on_first_try():
    sm = _won()
    assert sm.current_row == 1


def test_win_on_last_chance_does_not_lose():
    sm = _started()
    for _ in range(5):
        sm.submit_guess(MISS)
    sm.submit_guess(WIN)
    assert sm.state == GameState.WON
    assert sm.current_row == 6


# ── Encapsulation ────────────────────────────────────────────────────────────

def test_guesses_returns_copy_not_internal_list():
    sm = _started()
    sm.submit_guess(PARTIAL)
    sm.guesses.append([LetterResult.ABSENT] * 5)
    assert sm.guesses == [PARTIAL]


def test_guesses_inner_lists_are_copies():
    sm = _started()
    sm.submit_guess(PARTIAL)
    sm.guesses[0][0] = LetterResult.ABSENT
    assert sm.guesses[0][0] == LetterResult.CORRECT


def test_submit_guess_copies_result_list():
    sm = _started()
    result = list(PARTIAL)
    sm.submit_guess(result)
    result[0] = LetterResult.ABSENT
    assert sm.guesses[0][0] == LetterResult.CORRECT


# ── Full game scenarios ──────────────────────────────────────────────────────

def test_full_game_play_again_after_win():
    sm = _won()
    sm.reset()
    sm.start_game()
    assert sm.is_active
    assert sm.current_row == 0
    assert sm.guesses == []


def test_full_game_play_again_after_loss():
    sm = _lost()
    sm.reset()
    sm.start_game()
    assert sm.is_active
