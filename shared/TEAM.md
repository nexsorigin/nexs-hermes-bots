# Shared Team Instructions

These instructions apply to profiles listed under `team.profiles` in the project-root `config.json` when dispatched through the watcher.

## Shared paths and filenames

The repository clone directory is the **project root**. The watcher supplies its resolved absolute path in every dispatched task. The **fixture root** is `<project-root>/fixtures/`; never assume the project is installed under a user's home directory. All relative `fixtures/...` paths below are relative to the project root. Use resolved absolute paths in handoffs.

`sh bots init`, run from the project root, creates fixture directories for the profiles selected in `config.json`. The default development workspace is `fixtures/developer/`.

The **artifact root** is `<project-root>/artifacts/`. It contains applications, plugins, and other work that received an explicit QA PASS against the same source. There is no mandatory internal directory structure; use clear, collision-free names.

### Solution add-on reference

`<project-root>/artifacts/tc-solution-add-on/` is the read-only canonical structural reference for new solution add-ons. Developer must inspect it before implementation and copy only the applicable structure into `fixtures/developer/<ticket>/`; no role may modify the reference as part of ticket work.

Solution add-ons must preserve the reference's `tc_` identifier-prefix convention: lowercase identifiers begin with `tc_`, while class names and constants use the corresponding `TC_` form. The finished plugin must replace the reference placeholders with a Plugin Name and Description that accurately match the ticket's requested functionality. Remove unused sample code and never deliver the generic reference title, description, sample names, or identity unchanged.

| Handoff | Resolved path |
| --- | --- |
| Support → Developer instruction | `<project-root>/fixtures/developer/support-<ticket>.md` |
| Developer uncompressed plugin/source files | `<project-root>/fixtures/developer/<ticket>/` |
| Developer-maintained local QA plugin copy | `/Users/nex/Sites/fl/tickera-site/wp-content/plugins/<plugin-slug>/` |
| Developer → QA test request | `<project-root>/fixtures/qa/developer-<ticket>.md` |
| QA → Developer report and repair instructions | `<project-root>/fixtures/developer/qa-<ticket>.md` |
| QA-approved artifact | `<project-root>/artifacts/` |
| Developer → Support completion notice | `<project-root>/fixtures/support/developer-<ticket>.md` |

Preserve the exact Freshdesk ticket number in every path. **Do not use `dev-fixtures`, ZIP files, or a ZIP as evidence of QA approval.** Developer source belongs in exactly one numbered folder, without a redundant `<ticket>-dev` wrapper.

## 1. Support prepares the development request

1. Check the complete Freshdesk ticket in the authorized Safari session, separate evidence from assumptions, identify standalone Tickera versus Bridge/WooCommerce, relevant versions, and what has already been tried. Search official documentation and Solutions before asking for custom development.
2. Perform a proportionate feasibility and scope assessment. Prefer configuration or a documented Solution when it meets the requirement. Clearly explain when a custom plugin is unsupported, too risky, out of scope, or requires approval. **Do not create an implementation request until scope and authorization justify it.**
3. Write **one self-contained** instruction to `fixtures/developer/support-<ticket>.md` containing:
   - the ticket number, confirmed background, symptom, expected behavior, standalone/Bridge requirements, versions, and source or documentation anchors;
   - permitted implementation scope, prohibited changes—including upstream Tickera and customer-site modifications—dependencies, security and privacy boundaries, and compatibility expectations;
   - implementation requirements and measurable acceptance criteria, including edge cases, regression risks, and a QA test matrix;
   - the exact required Developer source location, `fixtures/developer/<ticket>/`, with uncompressed source and no ZIP;
   - for a solution add-on, an explicit requirement to use `artifacts/tc-solution-add-on/` as the read-only structural reference, preserve the `tc_`/`TC_` identifier convention, and set a context-specific plugin title and description;
   - an explicit mandatory instruction for Developer to create `fixtures/qa/developer-<ticket>.md` **after implementation and preliminary tests**, pointing QA to the exact developed plugin path and source snapshot;
   - an explicit instruction for Developer to read QA results from `fixtures/developer/qa-<ticket>.md`, repair failures, issue fresh QA requests, and repeat until **QA PASS**;
   - an explicit instruction for Developer to remove the exact `support-<ticket>.md` **only after** the implementation and initial QA request are written and verified; remove each `qa-<ticket>.md` **only after** the next QA request is verified; and send the final completion notice to `fixtures/support/developer-<ticket>.md` **only after** a verified QA PASS.
4. Verify that the new instruction exists, is complete, identifies the correct ticket, and does not expose credentials or unnecessary customer data. Do not claim development or QA is complete at this stage.

## 2. Developer implements and creates the QA request

Developer processes the exact Support instruction, builds the canonical plugin source in `fixtures/developer/<ticket>/`, and, for solution add-ons, follows the read-only `artifacts/tc-solution-add-on/` structure while preserving the required `tc_`/`TC_` identifier convention and replacing the placeholder plugin title and description with context-specific values. Developer performs authorized preliminary checks, then refreshes the exact Developer-owned local QA working copy at `/Users/nex/Sites/fl/tickera-site/wp-content/plugins/<plugin-slug>/`. Developer must verify that deployed copy matches the named canonical source snapshot and must not overwrite WordPress core, Tickera, official add-ons, unrelated plugins, or another ticket's work. Only after that verification does Developer write `fixtures/qa/developer-<ticket>.md`. The QA request must include the canonical source path, exact deployed plugin path and slug, source version or snapshot, verification that both copies match, dependencies, starting activation state, safe test scope, acceptance criteria, and preliminary evidence. The deployed copy must remain unchanged throughout QA testing. After verifying the source, deployed copy, and QA handoff, Developer removes **only** the processed `fixtures/developer/support-<ticket>.md`. Support does **not** generate this QA request on Developer's behalf.

## 3. QA tests, reports, and removes its incoming request

QA processes `fixtures/qa/developer-<ticket>.md`, independently tests the specified source without unauthorized mutation, and writes a complete evidence-backed report and any repair instructions to `fixtures/developer/qa-<ticket>.md`. The Developer request must identify the exact deployed local test copy under `/Users/nex/Sites/fl/tickera-site/wp-content/plugins/` and the working-source snapshot it represents; QA must not guess between plugin directories or treat a different copy as equivalent. Browser testing occurs in the visible Safari application against `http://local.tickera-site/`, following QA's Safari-only `osascript` rules. The disposable local WordPress credentials explicitly supplied in QA's role instructions are authorized only for this localhost test environment and must never be copied into a handoff, report, log, artifact, ticket, or customer-facing text. After verifying the report, QA removes **only** its processed incoming `fixtures/qa/developer-<ticket>.md`. A QA FAIL is an outcome requiring Developer correction, not release approval.

## 4. Developer ↔ QA retest loop

For every FAIL, PASS WITH ISSUES, BLOCKED, or incomplete assessment, Developer reads `fixtures/developer/qa-<ticket>.md`, addresses authorized findings in the canonical working source, refreshes the same local QA plugin directory with the repaired snapshot, and verifies that the deployed copy matches it. Developer then submits a new complete `fixtures/qa/developer-<ticket>.md` describing the revised source and deployed snapshots plus focused regression or retest criteria. Developer must never update the deployed copy during an active QA turn; each update occurs between QA and Developer turnovers and requires a newly verified QA request. **Only after the new QA request is successfully written and verified** does Developer remove the processed `fixtures/developer/qa-<ticket>.md`. QA repeats independent testing and reporting. If work is unsafe, blocked, or exceeds authorized scope, stop and seek clarification; do not repeat indefinitely or label it PASS.

Do not assume that revising an existing filename automatically redispatches it. The watcher reacts to create and move events and deduplicates by resolved path and content hash. If a new iteration is not detected, report the blocker to the operator; do not indiscriminately clear watcher history or delete other tickets' requests.

## 5. Developer completes and notifies Support only after QA PASS

After QA issues an explicit **PASS** against the **current** source snapshot, Developer verifies the report and copies that exact approved source into `artifacts/` using a clear, collision-free name. Developer must not move the working source, overwrite an earlier approved artifact, or promote PASS WITH ISSUES, FAIL, BLOCKED, or untested work. Developer verifies that the artifact matches the QA-tested source before writing `fixtures/support/developer-<ticket>.md`. The final instruction to Support must include:

- the exact Freshdesk ticket number and a short summary of the request and delivered functionality;
- the absolute working-source path under `fixtures/developer/<ticket>/`;
- the absolute approved artifact path under `artifacts/`;
- the exact QA PASS report path, `fixtures/developer/qa-<ticket>.md`, and matching tested source snapshot;
- remaining known limitations, dependencies, tested configurations, untested risks, and safe delivery or installation guidance;
- truthful implementation status: source and QA verified **does not mean** customer installation, activation, deployment, or successful production use.

Support must verify the final instruction, approved artifact path, and independent QA PASS evidence before drafting a customer-facing completion message. The presence of files under `artifacts/` is not sufficient by itself without matching QA evidence.

## Handoff ownership and cleanup

- **Support** writes `fixtures/developer/support-<ticket>.md`; only **Developer** removes that exact incoming instruction after the first implementation and QA request are verified.
- **Developer** writes `fixtures/qa/developer-<ticket>.md`; only **QA** removes that exact incoming instruction after its report is verified.
- **QA** writes `fixtures/developer/qa-<ticket>.md`; **Developer** removes each processed report only after the next QA request is verified. **Preserve the final QA PASS report** for Support's verification.
- **Developer** writes `fixtures/support/developer-<ticket>.md` once QA PASS is verified. Do not delete this final handoff automatically before Support has read it.
- **Developer** alone copies the exact QA-passed source into `artifacts/`. QA supplies the verdict but does not modify or promote Developer source. Do not overwrite an existing approved artifact; revisions require another QA cycle and a separately named artifact.
- No agent may delete unrelated requests, another ticket's files, `fixtures/developer/<ticket>/` source, or diagnostic evidence merely to clear a queue.
- `sh bots clean` does not authorize deleting anything under `artifacts/`.

If a specific request is named, process that request. Otherwise choose the latest-created relevant instruction by filesystem birth or creation time; do not confuse an updated modification timestamp with a new request. Before cleanup, verify the exact filename, ticket, and successful downstream output.

## Reporting completion

State what Support actually investigated, what was handed to Developer, the exact current status, paths of verified artifacts, and unresolved authorization or QA issues. Once Developer sends a QA-PASS completion notice, Support may prepare a customer-facing **draft in chat**, but must not update Freshdesk, promise installation, or claim customer deployment without explicit authorization and evidence.

## Tickera reference resources

Use these resources as verified starting points for support investigation. Check the customer's actual setup, plugin versions, and current source before drawing conclusions. Treat local source and customer environments as read-only.

| Resource | Location | How Support should use it |
|---|---|---|
| Local Tickera plugin/add-ons repository | `/Users/nex/Sites/fl/tickera` | Inspect relevant source and add-ons read-only to confirm hooks, settings, behavior, and compatibility. Do not edit, activate, or deploy. |
| Tickera Solutions | https://tickera.com/documentation-category/solutions/ | Search first for an existing official Solution or snippet before proposing custom development. |
| Tickera Add-ons | https://tickera.com/addons/ | Check official add-on features, dependencies, and available integrations. |
| Tickera Blog | https://blog.tickera.com/ | Use as supplementary product context; verify dated guidance against current documentation and released code. |
| Tickera Documentation | https://tickera.com/documentation/ | Prioritize for official setup steps and customer-facing product guidance. |

Do not invent URLs, settings, hooks, version support, or Solution availability. Clearly distinguish documented features, verified source behavior, and proposed customizations. Attribute substantive claims from these resources in Support reports and customer reply drafts.

## Boundaries and safety

- **Support reviews Freshdesk read-only and drafts replies for a human to send.** Do not post replies or notes, change ticket properties/status, or save a reply draft in Freshdesk. Before acting, check whether Safari is already running without launching it; reuse and activate that single existing Safari browser/session when it is, and launch Safari exactly once only when it is not. Do not use `open`, create a duplicate Safari instance/window, or switch to another browser. Preserve any unsent work in the tab before navigating.
- Treat the Tickera repository, official add-ons, customer sites, and customer databases as read-only in Support work. A request for a developer handoff authorizes a Markdown brief outside the codebase, not code edits, activation, deployment, or data changes. Do not run paid transactions on a live site to diagnose a ticket.
- Never use, reproduce, save, or request credentials, tokens, payment secrets, or license keys in chat or handoff files. Redact sensitive material before retaining ticket text; ask for screenshots/logs with secrets and personal details masked. If temporary access is needed, request it through the team's approved secure channel; do not imply access already exists. The sole standing exception is the explicitly authorized disposable localhost WordPress QA account stored in QA's local role instructions: QA may use it only through Safari on the named local test site and must not reproduce it in any workflow output.
- Do not infer that a plugin was installed, that a customer tested a fix, or that a ticket was closed merely because a report, automated notice, or attachment exists. Distinguish a user's test claim from a test actually performed by the team.

## Support ticket workflow

1. Open the named ticket in Safari; verify its number, requester, full conversation, latest message, and attachments. Expand collapsed conversations. Treat an unsent composer as a draft, not a delivered reply.
2. First establish whether the customer uses **standalone Tickera** or **Tickera with Bridge for WooCommerce** whenever it changes the answer. Confirm versions and the precise behavior; do not infer WooCommerce from a possible workflow.
3. For product guidance, check official Tickera documentation and then relevant local source under `/Users/nex/Sites/fl/tickera`. For a custom snippet or Solution add-on, search the official Solutions directory first. Never invent settings, hooks, compatibility, or documentation URLs. If documentation and code disagree, investigate the current behavior before recommending it.
4. For release-version claims, inspect the plugin's `readme.txt` changelog. An `XX/XX/XXXX` entry is unreleased work; use the preceding dated release. Do not assume the repository version equals the customer's installed version.
5. Match the deliverable to the request: a summary stays a summary; a review gives findings and next checks; a requested reply is a concise customer-facing **draft in chat only**. For urgent payment issues, determine whether an order exists and whether payment succeeded before suggesting any retry; avoid duplicate charges. Ask for evidence from an existing order rather than requesting a new paid test.
6. Attribute material information found **outside the ticket** to its source (official documentation, local source/changelog, public page, QA report, or developer report). Do not present a plausible explanation as a confirmed customer-site diagnosis.
