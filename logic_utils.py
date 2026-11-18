# FIX: Moved logic from the app.py
def get_range_for_difficulty(difficulty: str):
    """Return (low, high) inclusive range for a given difficulty."""
    if difficulty == "Easy":
        return 1, 20
    if difficulty == "Normal":
        return 1, 100
    if difficulty == "Hard":
        return 1, 50
    return 1, 100


# FIX: Moved logic from the app.py
def parse_guess(raw: str):
    """
    Parse user input into an int guess.

    Returns: (ok: bool, guess_int: int | None, error_message: str | None)
    """
    if raw is None:
        return False, None, "Enter a guess."

    if raw == "":
        return False, None, "Enter a guess."

    try:
        if "." in raw:
            value = int(float(raw))
        else:
            value = int(raw)
    except Exception:
        return False, None, "That is not a number."

    return True, value, None

# FIX: Moved logic from the app.py and removed string comparison
def check_guess(guess, secret):
    """
    Compare guess to secret and return (outcome, message).

    outcome examples: "Win", "Too High", "Too Low"
    """
    if guess == secret:
        return "Win", "🎉 Correct!"

    if guess > secret:
        return "Too High", "📉 Go LOWER!"

    return "Too Low", "📈 Go HIGHER!"


# FIX: Moved logic from the app.py
def update_score(current_score: int, outcome: str, attempt_number: int):
    """Update score based on outcome and attempt number."""
    if outcome == "Win":
        points = 100 - 10 * (attempt_number + 1)
        if points < 10:
            points = 10
        return current_score + points

    if outcome == "Too High":
        if attempt_number % 2 == 0:
            return current_score + 5
        return current_score - 5

    if outcome == "Too Low":
        return current_score - 5

    return current_score


# ---------------------------------------------------------------------------
# AI opponent
# ---------------------------------------------------------------------------
# The AI plays the same game as the user: it sees only the "Too High" /
# "Too Low" hints (never the secret) and gets one guess per round.

AI_LEVELS = ("Rookie", "Pro")


def narrow_range(low: int, high: int, guess: int, outcome: str):
    """Shrink the (low, high) search window after a guess, based on its hint."""
    if outcome == "Too Low":
        return max(low, guess + 1), high
    if outcome == "Too High":
        return low, min(high, guess - 1)
    return low, high


def ai_next_guess(low: int, high: int, level: str = "Pro", rng=None):
    """
    Pick the AI's next guess from the numbers still possible (low..high).

    - "Pro":    binary search (always the middle), the optimal strategy.
    - "Rookie": a random number from the remaining window.
    """
    if low > high:
        raise ValueError("Empty search range: low is greater than high.")

    if level == "Pro":
        return (low + high) // 2

    if rng is None:
        import random as rng  # the random module has the same randint API
    return rng.randint(low, high)


def determine_race_result(user_solved: bool, ai_solved: bool, attempts: int, attempt_limit: int):
    """
    Decide the user-vs-AI race after a full round (both have guessed `attempts` times).

    Returns:
        "tie"  - both found the number in the same round
        "user" - only the user found it (fewer tries)
        "ai"   - only the AI found it (fewer tries)
        "none" - nobody found it and the attempts ran out
        None   - race still going
    """
    if user_solved and ai_solved:
        return "tie"
    if user_solved:
        return "user"
    if ai_solved:
        return "ai"
    if attempts >= attempt_limit:
        return "none"
    return None
