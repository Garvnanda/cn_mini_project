# NetArchitect assistant initializer

Read `CLAUDE.md` in full before doing any work. Its project guardrails apply to
Codex and other assistants too; this file supplements them rather than replacing them.
Explicit owner instructions take precedence over project files.

## Start every session
1. Read `CLAUDE.md`, `idea.md`, `implementation.md`, `implemented.md`,
   `docs/standards.md`, and `docs/decisions.md` in that order.
2. Read `docs/project_audit.md` for the latest independently checked baseline.
3. Read `docs/ios_reference.md` before touching IOS generation or parsing.
4. Inspect read-only git status and the relevant source and tests before editing.
   Preserve the owner's uncommitted work.

## Evidence and scope
- Distinguish implemented, locally tested, externally validated, deferred, and absent.
  A checked box or historical test result is evidence of a claim, not current proof.
- Never claim simulator success proves Cisco IOS compatibility, real convergence,
  optical viability, encryption, or end-to-end latency under load.
- Treat `[verify]`, `?`, and `UNVERIFIED` as unresolved. Use the standards and IOS
  references as required by CLAUDE.md; do not silently invent or approve values.
- Use the append-only decision log to resolve historical conflicts: later explicitly
  superseding decisions govern. Flag other contradictions rather than guessing.
- The engine makes network decisions deterministically. NL extraction only fills
  inputs, reports assumptions, and requires user review.
- Work within the owner's current authorized scope. Broad completion requests may
  span phases; otherwise follow the current phase. Do not rewrite working features.
- Never fabricate audit-log provenance, prompts, model names, bugs, or packet traces.

## Commands, privacy, and verification
- No git mutations, commits, pushes, tags, branches, resets, merges, rebases, or PRs.
  Read-only inspection is allowed. Do not modify `.git` or hooks.
- Never print `.env` contents or API keys. Inspect configuration names or presence
  only when needed. No secrets in frontend code, reports, logs, or exports.
- No new dependencies without explaining the need and deployment cost; preserve pins.
- Run backend checks from `backend/`: `.venv/Scripts/python -m pytest -q` on Windows.
  For explicit totals use `.venv/Scripts/python -m pytest -o addopts='' -q`.
- Run frontend `npm run lint`, `npm test`, and `npm run build` after frontend changes.
- Report actual commands, working directories, totals, skips, failures, and limits.
  Never equate mocked integrations with a live service test.
- Engine changes need meaningful regression and threshold tests per CLAUDE.md.
  Regenerate golden configs only deliberately and explain why.

## Finish a task
Update `implemented.md` with real changes and checks. Update `implementation.md`
only for work actually completed; keep external acceptance tasks open until verified.
Append architectural decisions where needed. Record only genuine AI networking
mistakes in `ai_audit_log.md`. Keep `docs/project_audit.md` current when status changes.
