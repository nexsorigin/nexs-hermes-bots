# Shared Team Instructions

These instructions apply to profiles listed under `team.profiles` in the project-root `config.json` when the watcher dispatches a task.

## Shared locations

- The watcher supplies the absolute project root and fixture root in every dispatched task. Do not assume where the repository was cloned.
- Incoming handoffs are stored in `<fixture-root>/<recipient>/`.
- Working files belong in a clearly named task directory under the responsible profile's fixture directory.
- Approved final outputs may be copied to `<project-root>/artifacts/`. Do not treat the presence of a file there as approval without matching QA evidence.

## Handoff handshake

Handoff files use `<sender>-<task-id>.md`, where `<sender>` is the sending profile and `<task-id>` is preserved across the complete workflow.

1. The sender writes one self-contained handoff in the recipient's fixture directory. It must identify the sender, recipient, task ID, objective, relevant inputs, permitted scope, constraints, expected output, and measurable completion criteria.
2. The sender verifies that the handoff exists, is readable, and contains no credentials or unnecessary sensitive data.
3. The recipient reads the exact incoming handoff, validates its scope, and completes only the authorized work. Missing, unsafe, or contradictory instructions must be reported instead of guessed.
4. The recipient acknowledges completion by writing and verifying the required result or downstream handoff. A chat response alone does not complete the filesystem handshake.
5. Only after the acknowledged output is safely written and verified may the recipient remove the exact incoming handoff it processed. Never remove another task's files, working source, final evidence, or unrelated queue entries.

If a task cannot proceed, preserve the incoming handoff and report the blocker. If a revised handoff reuses a path, its content must change; the watcher deduplicates submissions by resolved path and content hash.

## Default workflow

1. Support sends an implementation request to Developer.
2. Developer implements the authorized request and sends the exact source snapshot to QA.
3. QA independently reports PASS, PASS WITH ISSUES, FAIL, BLOCKED, or NOT TESTED to Developer.
4. Developer and QA repeat the handoff cycle until the current source receives an explicit PASS or the task is blocked.
5. After PASS, Developer copies the verified output to `artifacts/` and sends Support a completion handoff with the matching source and QA evidence.

No role may claim implementation, testing, approval, delivery, deployment, or production success without evidence for that exact stage. Do not modify production systems, external accounts, or unrelated files unless the task explicitly authorizes it.
