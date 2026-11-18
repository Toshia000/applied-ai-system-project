# Model Card: Game Glitch Investigator (Race the AI)

**What the "AI" is:** a rule-based opponent, not a trained model. In a number-guessing race it sees only the Higher/Lower hints and picks its next guess either at random inside the numbers still possible (*Rookie*) or by binary search (*Pro*). Whoever finds the secret in fewer tries wins. The logic is in `logic_utils.py` (`ai_next_guess`, `narrow_range`, `determine_race_result`).

## Limitations and Biases

- **It assumes the secret is uniformly random.** Binary search is only optimal under that assumption. The secret comes from `random.randint`, so it holds today. If the secret were ever chosen the way people pick numbers (7, 37, 50), Pro would be blind to that pattern.
- **Difficulty is tuned for the default range only.** I simulated the strategies before choosing the levels. On 1–100 Rookie needs about 7.5 tries and Pro about 5.8. On **Hard (1–50, 5 attempts)** even perfect binary search finds the number within the limit only about 61% of the time, so "nobody wins" is common there. That comes from the original attempt limits, which I did not retune.
- **Turn order slightly favors ties.** The user guesses and then the AI guesses every round, so the AI always gets its guess for the round even if the user already won it. Rounds are synchronized, so I can't call that a bias against the player, but it means the AI can never "lose" to a faster user. It can only tie or fall behind.
- **Input handling is loose.** `parse_guess` truncates decimals (`3.9` becomes `3`) and doesn't check the range, so `-5` or `500` is accepted and uses up an attempt.
- **Testing covers the logic, not the whole UI.** The 18 `pytest` tests cover parsing, hints, range narrowing, the AI strategies and race outcomes. The Streamlit flow was only smoke-tested with a throwaway headless script that I did not add to the repo, plus manual play.
- **State is session-only.** The win/loss/tie tally resets when the Streamlit session ends.

## Misuse Potential and Prevention

The stakes are low: it's a guessing game with no personal data and no external calls. The realistic risks are small:

- **Cheating.** The *Developer Debug Info* expander shows the secret. That's fine for a learning project, but with any leaderboard or shared scoring it would make results meaningless. *Prevention:* remove or gate the expander in a real deployment, keep the secret server-side only, and don't add a leaderboard without server-side validation.
- **Misrepresenting the opponent.** Calling a binary search "AI" could oversell it. *Prevention:* the docs state plainly that it is a simple rule-based strategy, and the post-game log shows every guess it made.
- **Reusing the pattern elsewhere.** A system that gives a bot the same feedback as a human is fair here, but the same setup could be used to automate guessing against something that matters, such as codes or PINs. *Prevention:* this repo has no such interface, but any real system should rate-limit and lock out repeated guessing.

## Reliability Testing: What Surprised Me

- **Random guessing was much stronger than I expected.** Rookie, which just picks randomly inside the remaining window, needs only about 4.6 tries on 1–20 versus 3.7 for binary search. Narrowing the range from hints does most of the work, so Rookie is not a pushover. I had considered a third, sloppier level that ignores hints some of the time, but dropped it to keep two clear levels.
- **A perfect AI still fails often on Hard.** I expected Pro to dominate every difficulty. With 5 attempts on 1–50 it fails about 39% of the time, so the attempt limit, not the AI, is what makes Hard hard.
- **The bugs that mattered were in the game state, not the AI.** Reading the original code showed the attempt counter started at 1 (an off-by-one against the limit), invalid input consumed an attempt, and *New Game* kept the old "won" status. All of these would have made race results wrong, so they were fixed and are covered by the headless run, which checked that invalid input doesn't count and that New Game resets the status.

## Collaboration with AI

I used Claude as a coding assistant for the whole feature. I set the goal (an AI that races the player), and the assistant read the existing code, simulated candidate strategies before choosing the levels, wrote the logic and tests, ran the app headlessly, and drafted the diagram and README sections. I reviewed what it produced and steered it.

- **Suggestion I accepted: hide the AI's guesses until the game ends.** The AI suggested this because each AI guess comes with a Higher/Lower result, so showing them live would hand the player free information about the secret. I accepted it because it keeps the race fair, and the compromise is that the full guess log appears after the game.
- **Suggestion I did not accept as written: the first "Design Decisions" draft.** The AI proposed a long section, with a paragraph of reasoning and a trade-off for every decision. I rejected it because it was too much for a README summary and buried the key points. I asked for it to be shortened, and it became six one-line bullets, each with the reason and its trade-off. It wasn't wrong, just over-written for its audience.
