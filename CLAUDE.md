# CLAUDE.md — Rules for AI assistants working on NetArchitect

Read this file fully before any work. These rules are strict and override default behaviour.

## 0. Required reading order (every session)
1. `CLAUDE.md` (this file)
2. `idea.md` — what we are building and why
3. `implementation.md` — the phase plan; find the current phase
4. `implemented.md` — what already exists (source of truth for "done")
5. `docs/standards.md` — the ONLY allowed source for networking numbers/thresholds/RFCs
6. `docs/decisions.md` — architectural decisions already made; do not re-litigate

## 1. Git — absolute rule
- **NEVER run `git commit`, `git push`, `git tag`, `git rebase`, `git reset`, `git merge`, or create PRs.** The owner does all git operations manually.
- Read-only git (`git status`, `git diff`, `git log`) is allowed.
- Do not create or modify `.git/` or git hooks.

## 2. Anti-hallucination rules
1. **No invented facts.** Every networking number (distance limit, dB loss, power budget, PoE watts, timers, AD values) must come from `docs/standards.md`. If a needed value is missing there, STOP and ask the owner; do not guess. When added, cite the source.
2. **No invented RFC/IEEE numbers.** Only cite standards listed in `docs/standards.md`.
3. **No invented Cisco IOS syntax.** Use only commands listed in `docs/ios_reference.md`. A new command must be added there first with its exact syntax, after owner confirmation.
4. **No invented APIs/libraries.** Before using a library function, verify it exists in the installed version (read the source or run `python -c "help(...)"`). Pin versions in `requirements.txt` / `package.json`.
5. **No invented files or functions.** Before referencing a file, function, or class, open it or grep for it. Never claim something exists from memory.
6. **Never claim "done" or "tests pass" without running them.** Paste the actual command and the summary line of output.
7. **Say "I don't know" or "unverified"** instead of guessing. Mark uncertain code with `# UNVERIFIED:` and tell the owner.
8. **The LLM (OpenRouter) never decides network design.** It only converts natural language to the input JSON schema. All decisions are deterministic code.
9. Do not fabricate entries for `ai_audit_log.md`. Only record AI mistakes that really occurred, with the real buggy code.

## 3. Scope discipline
- Work only on the current phase in `implementation.md` unless the owner says otherwise.
- No features outside `idea.md`. Suggest them in chat; do not build them.
- Do not delete or rewrite working code from earlier phases without asking.
- No new dependency without stating why and checking free-tier deploy weight (Render 512 MB RAM).

## 4. Code rules
- Python 3.11+, type hints everywhere, Pydantic v2 for models.
- Core VLSM/mask math uses integer bitwise operations. Python `ipaddress` is allowed only as a **test oracle** and for input parsing/formatting.
- Always mask with `& 0xFFFFFFFF` after `~` on 32-bit values.
- Every design decision must produce a `Rationale` record (rule id, inputs, threshold, standard reference, sentence). A decision without a rationale is a bug.
- Errors are typed (see `docs/decisions.md`): never `raise Exception("...")`.
- One engine, three front-ends (web, CLI, TUI). No business logic in `api.py`, `cli.py`, `tui.py`, or React.
- No secrets in code or frontend. `OPENROUTER_API_KEY` only from env.

## 5. Testing rules
- Every new engine function ships with pytest tests in the same task.
- Boundary tests are mandatory for thresholds (exact value, value ± 1).
- Run `pytest -q` before reporting a task complete; report the real result.
- Golden files change only on purpose; say why in chat.

## 6. Documentation upkeep (mandatory after every task)
- Update `implemented.md`: what was added, files, tests, date.
- Tick the checkbox in `implementation.md`.
- If a decision was made, append it to `docs/decisions.md`.
- If a real AI bug was found and fixed, add it to `ai_audit_log.md` (see template).
- If a new standard value or IOS command is used, add it to `docs/standards.md` / `docs/ios_reference.md`.

## 7. Communication
- Report: what changed, files touched, test command + result, anything unverified.
- If a rule here blocks the task, stop and ask; do not work around it.
