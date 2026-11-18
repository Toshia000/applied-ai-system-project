import random

import pytest

from logic_utils import (
    ai_next_guess,
    check_guess,
    determine_race_result,
    narrow_range,
)

def test_winning_guess():
    # If the secret is 50 and guess is 50, it should be a win
    outcome, message = check_guess(50, 50)
    assert outcome == "Win"
    assert message == "🎉 Correct!"

def test_guess_too_high():
    # If secret is 50 and guess is 60, the player should be told to go lower
    outcome, message = check_guess(60, 50)
    assert outcome == "Too High"
    assert message == "📉 Go LOWER!"

def test_guess_too_low():
    # If secret is 50 and guess is 40, the player should be told to go higher
    outcome, message = check_guess(40, 50)
    assert outcome == "Too Low"
    assert message == "📈 Go HIGHER!"

def test_numeric_not_lexicographic_comparison():
    # 9 < 10 numerically, even though "9" > "10" as strings
    outcome, message = check_guess(9, 10)
    assert outcome == "Too Low"
    assert message == "📈 Go HIGHER!"


# --- AI opponent ---

def test_narrow_range_too_low_raises_lower_bound():
    assert narrow_range(1, 100, 40, "Too Low") == (41, 100)


def test_narrow_range_too_high_lowers_upper_bound():
    assert narrow_range(1, 100, 60, "Too High") == (1, 59)


def test_narrow_range_win_leaves_range_unchanged():
    assert narrow_range(1, 100, 50, "Win") == (1, 100)


def test_pro_ai_guesses_the_middle():
    assert ai_next_guess(1, 100, "Pro") == 50


def test_rookie_ai_guess_stays_inside_range():
    rng = random.Random(0)
    for _ in range(200):
        assert 30 <= ai_next_guess(30, 35, "Rookie", rng) <= 35


def test_ai_with_empty_range_raises():
    with pytest.raises(ValueError):
        ai_next_guess(10, 9, "Pro")


@pytest.mark.parametrize("level", ["Rookie", "Pro"])
def test_ai_always_finds_the_secret_given_unlimited_tries(level):
    rng = random.Random(1)
    for secret in range(1, 101):
        low, high = 1, 100
        for _ in range(101):
            guess = ai_next_guess(low, high, level, rng)
            outcome, _ = check_guess(guess, secret)
            if outcome == "Win":
                break
            low, high = narrow_range(low, high, guess, outcome)
        else:
            pytest.fail(f"{level} AI never found {secret}")


def test_pro_ai_needs_at_most_seven_tries_for_1_to_100():
    for secret in range(1, 101):
        low, high, tries = 1, 100, 0
        while True:
            tries += 1
            guess = ai_next_guess(low, high, "Pro")
            outcome, _ = check_guess(guess, secret)
            if outcome == "Win":
                break
            low, high = narrow_range(low, high, guess, outcome)
        assert tries <= 7


# --- Race result ---

def test_race_user_wins_when_only_user_solved():
    assert determine_race_result(True, False, attempts=3, attempt_limit=8) == "user"


def test_race_ai_wins_when_only_ai_solved():
    assert determine_race_result(False, True, attempts=4, attempt_limit=8) == "ai"


def test_race_tie_when_both_solved_same_round():
    assert determine_race_result(True, True, attempts=5, attempt_limit=8) == "tie"


def test_race_continues_while_nobody_solved_and_attempts_remain():
    assert determine_race_result(False, False, attempts=3, attempt_limit=8) is None


def test_race_ends_with_no_winner_when_attempts_run_out():
    assert determine_race_result(False, False, attempts=8, attempt_limit=8) == "none"
