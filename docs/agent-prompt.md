# Agent prompt: take the next step

Paste everything below the line into a new agent session started at the repo root. It works for any step: the agent picks one itself.
To give the agent a specific step, add one line at the top: `Take step <N>.`

---

You are implementing one step of the v1 delivery plan of Archivum Buczkovianum. Your work ends as one pull request, ready for a human to review. You never merge it.

## 1. Read

1. `AGENTS.md`: the rules. They override anything below.
2. `docs/plan.md`: sections 2 (how we work), 3 (decisions), 4 (order and dependencies) and 7 (reminders).

## 2. Pick a step

1. `git switch main && git pull`.
2. List what others already took: `gh pr list --state open` (drafts count) and `git ls-remote --heads origin`.
3. Pick a step from `docs/plan.md` section 5 that:
   - is not ticked;
   - has every step in its "Needs" ticked;
   - has no open PR and no remote branch.

   Prefer the critical path (section 4.3), then the lowest wave (4.2). If you were given a step, check those three conditions for it.
4. If no step qualifies, stop. Report which steps are blocked and on what. Do not start anything.

## 3. Claim it

Do this before writing any code, so parallel agents see the step is taken.

```bash
git switch -c <branch from the step's row>
git commit --allow-empty -m "<story ID or prefix>: start step <N>"
git push -u origin HEAD
gh pr create --draft --title "<story ID>: <title> (step <N>)" --body "Step <N> of docs/plan.md. In progress."
```

If the push or the PR fails because the branch exists, someone claimed the step first. Go back to section 2 and pick another.

## 4. Understand it

Read the step's row in full, its story in `docs/user-stories.md` (every AC), the architecture sections it touches and the design files it names. Read the decisions (D-numbers) the row cites. Check `docs/plan.md` section 4.4 for files you share with steps running in parallel.

Find the code you are told to reuse and read it before writing your own. If the story is ambiguous, conflicts with the docs, needs a new dependency or a change to `docs/architecture.md`, go to section 9.

## 5. Build it

- Test first: for each AC, a failing test named after it (`test_us_ra_07_ac4_...`), then the code that passes it.
- Stay inside the step. No refactoring, renaming or reformatting outside it.
- Commit in small steps and push as you go.
- `make check` must pass.

## 6. Simplify

Run the `/simplify` skill on your branch's diff and apply what it finds. If the skill is not available, go through the diff yourself:

- Did you write something that already exists? Shared querysets live in `archive`, page parts in `frontend/src/components/`, the upload in `archive/forms.py` and `archive/uploads.py`. Use those.
- Remove dead code, unused copy, needless abstraction, comments that repeat the code, and any change outside the step.
- Match the surrounding code: its naming, its idioms, its comment density.

Run `make check` again.

## 7. Review

Run the `/code-review` skill at `high` effort on your branch against `main`. For each finding, fix it or note in the PR why it does not apply. If the skill is not available, start a fresh subagent with no access to your reasoning. Give it the diff (`git diff main...HEAD`), the story and `AGENTS.md`, and ask it for correctness bugs, missed ACs, missing tests and rule violations.

Re-run the review after fixing anything non-trivial. Then run `make check` again.

## 8. Finish the PR

1. Rebase: `git fetch && git rebase origin/main`. Resolve conflicts by keeping both sides. Never hand-merge `frontend/src/api/`: take `main`'s copy and run `make api-client`. If a migration number clashes, renumber yours and fix its `dependencies`. Run `make check`.
2. In `docs/plan.md`, tick the step's box in section 5 and write notes for later steps into their rows. Do not edit sections 4.1 or 4.2; a human refreshes them.
3. Run `make api-client` if the API changed, and commit migrations if models changed.
4. `git push --force-with-lease`.
5. Replace the PR description with:
   - the story ID and the step number;
   - what changed;
   - how to verify it by hand (with `manage.py load_demo_data`);
   - the review findings you did not fix, and why;
   - new dependencies, with a justification;
   - anything left undone.

   End it with the attribution line from your session's instructions, if there is one.
6. `gh pr ready`. Never merge.

## 9. When you are stuck

Do not guess. Leave the PR as a draft, put the question at the top of its description, and stop. Your report says what you need answered.

## 10. Report

End with: the PR link, the step and story, what you built, how review and simplification changed it, and anything left open.
