# Agent prompt: take the next step

Paste everything below the line into a new session at the repo root. It picks one step. To name one, add a line above the paste: `Take step <N>.`

---

One step of Archivum Buczkovianum. One PR, ready for a human. Never merge.

`AGENTS.md` overrides this. `docs/plan.md` §2 is the procedure. Also read §7, §4.4 when another step is open, the step's row, every AC of its story, the architecture sections and design files the row names, and only the D-numbers it cites. Read code the row says to reuse before writing any. A named step that qualifies skips §4.2 and §4.3.

**Claim, before any code.** From updated `main`: an unticked §5 step whose Needs are all ticked, with no open PR and no remote branch (`gh pr list --state open`, `git ls-remote --heads origin`). Prefer the critical path (§4.3), then the lowest wave (§4.2). A named step must pass the same three checks. If none qualifies, stop and name what blocks which step.

```bash
git switch -c <branch from the row>
git commit --allow-empty -m "<story ID or prefix>: start step <N>"
git push -u origin HEAD
gh pr create --draft --title "<story ID>: <title> (step <N>)" --body "Step <N> of docs/plan.md. In progress."
```

If the branch or PR exists, someone else claimed it: pick again. Base is `main`. Do not stack PRs.

**Build.** One failing test per AC, then the code. Stay inside the step. Commit and push when `make check` is green. If `frontend/node_modules` is missing, `npm ci` in `frontend/` first. Parallel runs share Postgres: create a database named for the step, point `DATABASE_URL` at it, then test. Do not create `test_buczkovianum` while another run holds it.

**Clean the diff once, yourself.** `git diff main...HEAD`. Do not launch the simplify skill or any subagent for this. Drop code that already exists (querysets in `archive`, page parts in `frontend/src/components/`, upload in `archive/forms.py` and `archive/uploads.py`), dead code, unused copy, extra abstraction, comments that repeat the code, and edits outside the step. Match the surrounding style. `make check` again.

**One review.** One fresh subagent, with no access to your reasoning. Give it `git diff main...HEAD`, the story, and `AGENTS.md`. Ask for correctness bugs, missed ACs, missing tests, and rule violations. Fix each finding, or note in the PR why it does not apply. Review again only if a fix changes behaviour. `make check`.

**Finish.** `git fetch && git rebase origin/main`. Keep both sides. Never hand-merge `frontend/src/api/`: take `main`'s copy and run `make api-client`. If a migration number clashes, renumber yours and fix its `dependencies`. `make check`. Tick the §5 box and write notes into later rows. Do not edit §4.1 or §4.2. `git push --force-with-lease`. Replace the PR body with: story ID and step; what changed; how to verify with `manage.py load_demo_data`; findings left unfixed, and why; new dependencies, and why; anything undone; the session attribution line, if there is one. `gh pr ready`.

**Stuck** (ambiguous story, conflict with the docs, new dependency, or a change to `docs/architecture.md`): do not guess. Leave the draft, put the question at the top of the PR body, and stop.

**Report.** PR link, step and story, what you built, what the clean pass and the review changed, and what is still open.
