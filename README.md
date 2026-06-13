# wordle

# "Wordle" word-guessing game

## Project description

Implementation of the word-guessing game "Wordle".
The player tries to uncover a hidden 5-letter word against the computer using a graphical (Qt) interface.
The game follows the rules of the original Wordle: a fixed-length hidden answer, up to six attempts, per-letter feedback after every guess, and an on-screen keyboard that tracks what has already been learned.

Important!
The game accepts input in three ways:
- If the player uses the physical keyboard, letter keys type into the active row, Enter submits the guess and Backspace deletes the last letter.
- If the player uses the mouse, the on-screen QWERTY keyboard provides the same functionality through clickable keys (including ENTER and ⌫).
- The player can also freely combine both — for example, typing letters on the physical keyboard and clicking ENTER on the on-screen keyboard (or vice versa) — and the game will behave identically.

## Game rules

1. Word structure:
    - The game uses 5-letter English words.
    - The answer is picked at random from a curated pool of possible answers (~2,300 words).
    - Any guess submitted by the player must exist in the accepted-guesses list (~10,600 words).

2. Start of the game:
    - The computer picks a random hidden 5-letter word as the answer.
    - The player is given an empty 6×5 grid and the on-screen keyboard.

3. Turns:
    - The player types a 5-letter word and submits it with Enter.
    - If the word is too short, the game shows "Not enough letters" and nothing else happens.
    - If the word is not in the accepted list, the game shows "Not in word list" and nothing else happens.
    - Otherwise the guess is accepted, evaluated, and the tiles flip to reveal the result.

4. Coloring of letters:
    - GREEN — the letter is in the answer and in the correct position.
    - YELLOW — the letter is in the answer but in a different position.
    - GREY — the letter is not in the answer at all.
    - Duplicate letters are handled the same way as in the original Wordle: each letter in the answer can only "satisfy" one tile, so two of the same letter in a guess will not both turn yellow if the answer only contains one.

5. End of the game:
    - The player wins as soon as a guess turns fully green and the game shows "You won!".
    - The player loses if all six guesses are used without finding the answer, in which case the answer is revealed.
    - At any time the "New Game" button starts a fresh round with a new hidden word.

## Technologies

- Programming language: Python 3.9+
- Required to start the game: The user must have Python 3.9 or newer and `pip` available, and is expected to create a virtual environment before installing the project.
- Libraries:
    PySide6 — official Qt for Python bindings, used for the entire GUI (window, board, keyboard, animations).
    pytest — test runner for the unit and UI test suites.
    pytest-qt — fixtures for driving Qt widgets in tests (key events, signals, waiting).
    pytest-cov — coverage reporting for the test suite.

## Structure

- src/app.py:
The main QMainWindow of the application and the entry point of the game. It wires the WordBank, StateMachine, Evaluator, Board and Keyboard together, handles physical key events, manages the typing/submission/animation flow, and exposes the "New Game" action.

- src/state_machine.py:
Defines the game states (IDLE, PLAYING, WON, LOST) and the transitions between them. It records every submitted guess, advances the current row, and decides when the game has been won (all letters correct) or lost (six guesses used).

- src/evaluator.py:
Pure logic for scoring a guess against an answer. Implements the two-pass Wordle algorithm: first mark exact (CORRECT) matches, then mark misplaced (PRESENT) matches against the remaining letters, leaving the rest as ABSENT. Returns a list of LetterResult values.

- src/word_bank.py:
Loads and manages the two word lists. `answers.txt` is the pool the computer picks from; `guesses.txt` is the extra pool of words the player is allowed to type. Provides `get_answer()` (random pick) and `is_valid(word)` (membership check) and validates the format of every loaded word.

- src/constants.py:
Defines the shared game-wide constants — WORD_LENGTH (5), MAX_GUESSES (6) — and the LetterResult enum (CORRECT, PRESENT, ABSENT) used throughout the codebase.

- src/board.py:
The 6×5 tile grid widget. Pure presentation — it has no game logic. Exposes a tell-only API (`set_letter`, `clear_letter`, `reveal_row_animated`, `reset`) and orchestrates the staggered flip animation when a row is revealed.

- src/tile.py:
A single letter tile widget. Renders the letter, background and border, and provides the typing-in "pop" animation as well as the flip animation used when revealing a guess result.

- src/keyboard.py:
The on-screen QWERTY keyboard. Emits letter, Enter and Backspace events back to the App, and updates the color of each key based on the best result that letter has had so far (CORRECT > PRESENT > ABSENT).

- src/theme.py:
Centralizes the visual identity of the game — tile and key colors, borders, text colors, sizing constants, and the mapping from LetterResult to background color.

- src/styles.py:
Builds the Qt stylesheet strings for the on-screen keys and action buttons (New Game), using the values defined in `theme.py`.

- data/answers.txt:
The pool of possible hidden answers (~2,300 words). The computer picks the answer for each round randomly from this file.

- data/guesses.txt:
The full set of words the player is allowed to submit as a guess (~10,600 words). A guess that is not present in either this file or `answers.txt` is rejected as "Not in word list".

- tests/unit/:
Pure-logic tests that do not require Qt — covers the Evaluator (all coloring edge cases including duplicate letters), the StateMachine (every transition and every invalid-state guard) and the WordBank (file parsing, validation, randomness, and real word-list smoke tests).

- tests/ui/:
Qt widget and integration tests driven with pytest-qt — covers the Tile, Board and Keyboard widgets directly, plus end-to-end integration tests that simulate full games through the App using real key events.

- doc/plan.md:
The step-by-step build plan for the project, with coverage targets per layer and an explicit list of edge cases tested at every step.

- doc/project.md:
The decisions log — records the architectural choices made during development (component split, framework choice, testing strategy) and the reasoning behind them.
