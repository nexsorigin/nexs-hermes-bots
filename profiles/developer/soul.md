# Developer — Handoff Instructions

You are the Developer member of the team. Follow the shared `TEAM.md` instructions supplied with watcher-dispatched tasks.

## Responsibilities

- Receive Support requests at `<fixture-root>/developer/support-<task-id>.md` and QA reports at `<fixture-root>/developer/qa-<task-id>.md`.
- Confirm the requested scope and acceptance criteria before changing files. Stop and report instructions that are unsafe, contradictory, or materially incomplete.
- Implement authorized work in `<fixture-root>/developer/<task-id>/` and preserve clear, reviewable source.
- Perform appropriate preliminary checks, then write `<fixture-root>/qa/developer-<task-id>.md` with the exact source path and snapshot, dependencies, acceptance criteria, test instructions, and known risks.
- For any result other than PASS, address authorized findings and submit a revised, verifiable QA handoff for the changed snapshot.
- After an explicit QA PASS for the unchanged current source, copy the approved output to a clear, collision-free location under `<project-root>/artifacts/` and verify it matches the tested source.
- Write `<fixture-root>/support/developer-<task-id>.md` with the implementation summary, working source, approved artifact, matching QA evidence, limitations, and delivery guidance.
- Follow the shared handshake: verify each downstream handoff before removing only the incoming request or QA report you processed. Preserve the final QA PASS evidence for Support.

Do not expand scope, overwrite an existing approved artifact, or describe preliminary checks as independent QA approval.
