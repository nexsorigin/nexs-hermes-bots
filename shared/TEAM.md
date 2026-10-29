# Shared Team Instructions

These instructions apply to profiles listed under `team.profiles` in the project-root `config.json` when the watcher dispatches a task.

## Shared locations

- The watcher supplies the absolute project root and fixture root in every dispatched task. Do not assume where the repository was cloned.
- Incoming handoffs are stored in `<fixture-root>/<recipient>/`.
- `<project-root>/artifacts/tc-solution-add-on/` is the read-only plugin boilerplate. Solution add-ons live directly under `<project-root>/artifacts/` in folders named `tc-<solution-plugin-name>`.

## Handoff handshake

Handoff files use `<sender>-<ticket-id>.md`, where `<sender>` is the sending profile and `<ticket-id>` is preserved across the complete workflow.

1. The sender writes one self-contained handoff in the recipient's fixture directory. It must identify the sender, recipient, ticket ID, objective, relevant inputs, scope, constraints, expected output, and measurable completion criteria.
2. The sender verifies that the handoff exists, is readable, and contains no credentials or unnecessary sensitive data.
3. The recipient reads the exact incoming handoff, validates its scope, and completes only the authorized work. Missing, unsafe, or contradictory instructions must be reported instead of guessed.
4. The recipient acknowledges completion by writing and verifying the required result or downstream handoff. A chat response alone does not complete the filesystem handshake.
5. Only after the output is written and verified may the recipient remove the exact incoming handoff it processed. Never remove another ticket's files, plugins, final QA evidence, or unrelated queue entries.

If a task cannot proceed, preserve the incoming handoff and report the blocker. If a revised handoff reuses a path, its content must change; the watcher deduplicates submissions by resolved path and content hash.

## Workflow and allowed routes

| Sender | Recipient | File | Purpose |
| --- | --- | --- | --- |
| Support | Developer | `fixtures/developer/support-<ticket-id>.md` | Solution add-on request |
| Developer | QA | `fixtures/qa/developer-<ticket-id>.md` | Test request for the plugin under `artifacts/` |
| QA | Developer | `fixtures/developer/qa-<ticket-id>.md` | PASS or FAIL test result |
| Developer | Support | `fixtures/support/developer-<ticket-id>.md` | Notice of the QA-passed solution add-on |

1. Support reviews the ticket and, when a solution add-on is needed, sends a request to Developer.
2. Developer copies `artifacts/tc-solution-add-on/` to `artifacts/tc-<solution-plugin-name>/`, implements the request, and sends a test request to QA.
3. QA reviews the plugin code, tests it in Safari, and returns PASS or FAIL to Developer.
4. After a FAIL, Developer applies QA's recommendations and sends a revised test request. Repeat until QA reports PASS.
5. After PASS, Developer notifies Support of the finished solution add-on.

Support never sends anything to QA, and QA never sends anything to Support. No other routes are allowed.

No role may claim implementation, testing, approval, delivery, deployment, or production success without evidence for that exact stage. Do not modify production systems, external accounts, or unrelated files unless the task explicitly authorizes it.
