# Nex Hermes Bots

A reusable, local Hermes CLI automation scaffold. **The current default team consists of Support (`support`), Developer (`developer`), and QA (`qa`) agents.** This is an example team, not a required organization: other users can change the roles, number of profiles, and handoff workflow to meet their own needs, provided they keep the folder conventions and update the corresponding role names in the code and instructions.

## Folder structure

```text
<clone-directory>/
├── bots                         # Run with: sh bots <command>
├── config.json                  # Watcher and TEAM.md profile lists
├── bin/                         # Executable Python and service scripts
│   ├── profiles.py              # Config loading and Hermes profile discovery
│   ├── sync.py                  # Mirror Hermes profiles into local folders
│   ├── setup.py                 # Initialization and SOUL.md importer
│   ├── watcher.py               # Dispatches incoming files to Hermes
│   ├── run.sh
│   ├── install.sh
│   ├── stop.sh
│   └── uninstall.sh
├── profiles/                    # Editable handoff-only SOUL templates
│   ├── support/
│   │   ├── soul.md
│   │   └── meta.json
│   ├── developer/{soul.md,meta.json}
│   ├── qa/{soul.md,meta.json}
│   └── <other-profile>/{soul.md,meta.json} # Added by sync
├── shared/
│   └── TEAM.md                  # Common instructions
├── fixtures/                    # Incoming queue and working files
│   ├── support/
│   ├── developer/
│   └── qa/
├── artifacts/                   # Applications, plugins, and other QA-PASS work
├── logs/
└── submission_history.jsonl
```

**Folder rules for custom teams:** The repository clone directory is the project root. Runtime fixtures are stored under that project root at `fixtures/`; they are not stored in the user's home directory unless the repository itself was cloned there. Use `profiles/<profile>/soul.md` for a profile's handoff instructions, `fixtures/<profile>/` for its incoming queue, `shared/TEAM.md` for shared rules, and the project-root `config.json` for both profile lists. Profile names must match the real Hermes CLI profile names. Keep the SOUL template filenames as lowercase `soul.md` inside this project; `sh bots init` imports their contents into the actual Hermes **`SOUL.md`** files at `~/.hermes/profiles/<profile>/SOUL.md` (or `$HERMES_HOME/profiles/...`). Hermes profile discovery uses `hermes profile list`.

Applications, plugins, and other work that received an explicit QA PASS are copied into `artifacts/`. There is no mandatory internal directory structure or manifest file; use clear, collision-free names and retain the matching QA evidence in the ticket workflow. Runtime artifacts are ignored by Git while `artifacts/README.md` remains tracked. A non-PASS verdict must never be promoted into this directory.

To customize the team, edit the profile lists in `config.json` and create matching `profiles/<profile>/soul.md` templates. `sh bots init` creates missing configured Hermes profiles and fixture directories; `sh bots sync` synchronizes only configured profiles. The watcher, guarded console, cancellation, cleanup, and log commands all derive their profile sets from the same configuration. The original handoff validation still has special behavior for Support and QA, so changing that workflow may require adjusting the role-specific checks in `bin/watcher.py`. Update filenames inside the handoff templates to match your team's workflow.

## Installation and migration

1. Back up your old `~/hermes-file-watcher/` installation (if present), Hermes profile `SOUL.md` files, fixtures, and logs. Stop any old running services from **the old directory** using `sh bots stop` before moving files.
2. Clone or place the package in any directory you choose. That clone directory becomes the project root; fixtures, logs, and submission history stay inside it. If upgrading, migrate any fixtures, shared instructions and history you want to keep. Do not simply overwrite your customized `TEAM.md` or `soul.md` templates.
3. Run:

   ```bash
   cd /path/to/nexs-hermes-bots
   sh bots init
   ```

   `init` checks that the watcher is stopped, installs the official Hermes CLI if missing, creates `.venv`, installs dependencies from `config.json` under `watcher.dependencies`, checks `hermes profile list`, creates profiles selected in `config.json`, and imports `profiles/<profile>/soul.md` into their actual Hermes `SOUL.md`. When replacing existing profile instructions, it makes a timestamped backup. If the upstream Hermes installer is invoked it may perform its own setup or prompts.
4. Edit `shared/TEAM.md` for shared policies, configure its recipients and watched profiles in `config.json`, and edit the three `profiles/<profile>/soul.md` templates for role-specific handoffs. Rerun `sh bots init` after changing the templates to import their updated contents (backing up existing SOUL files).
5. When ready, start services **separately** with `sh bots start`. Check using `sh bots status`.

**`sh bots init` does not explicitly start the gateway, watcher, LaunchAgent, or any bot.** The upstream Hermes installer is a third-party script and may have its own setup behavior. Profile creation and authorization may also require interaction. Manual CLI or Desktop conversations do not automatically receive the `TEAM.md` injection; it is applied by the file watcher to dispatched tasks.

`sh bots start` also verifies the watcher environment and creates it if needed before starting the Gateway. This makes a fresh clone self-contained; no manual virtual-environment setup is required. On every watcher start, existing handoff Markdown files under configured watcher profile queues are scanned as recovery candidates. Files already recorded with the same path and content hash in `submission_history.jsonl` are skipped, while unseen files created during watcher downtime are dispatched.

`sh bots console` displays a numbered list containing only profiles from `team.profiles`. Select one by number or exact name, then every message is sent to that profile's persistent named session. The same session is resumed across turns and future console launches. Type `exit;` at the profile prompt or press Ctrl+C to leave; the console does not return to profile selection after each turn.

If your previous installation used the LaunchAgent `local.hermes.file-watcher`, stop and unload it before switching directories: the new install uses the same generic label and should not be competing with an old job pointing to the original path. The scripts do not remove the old installation automatically.

Run `sh bots --help` for a short setup checklist, including model authentication and verification.

## Connect an AI model (LLM) to Hermes

Hermes needs an **inference provider** to respond to prompts. Set this up **after** `sh bots init` and **before** starting the bots. This step is interactive and intentionally **not** performed by `sh bots init`: each user chooses their own model, provider, account, and billing arrangements.

1. Make sure the Hermes CLI is available:

   ```bash
   hermes version
   ```

2. Open Hermes's interactive model/provider selector:

   ```bash
   hermes model
   ```

3. Choose a provider and complete its authentication steps. Common choices include:

   | Provider | Connection method |
   | --- | --- |
   | **OpenAI Codex (ChatGPT subscription)** | Select **ChatGPT or Codex Subscription** in `hermes model`, then complete the device-code OAuth sign-in. This uses supported Codex models; it is **not** an OpenAI API key. |
   | **Nous Portal** | Select Nous in `hermes model` and sign in, or run `hermes setup --portal` for its guided setup. A Nous subscription may be required. |
   | **Anthropic / Claude** | Use `hermes model` and choose a supported login or API-key option. Anthropic OAuth access has specific plan/extra-usage requirements; an API key is a separately billed alternative. |
   | **OpenRouter** | Add an OpenRouter API key to `~/.hermes/.env`, then choose a suitable model in `hermes model`. |
   | **Google Gemini** | Put `GOOGLE_API_KEY` (or `GEMINI_API_KEY`) in `~/.hermes/.env` and configure the provider/model. A Gemini consumer subscription does not itself provide Hermes API access. |
   | **Local/custom LLM** | Select **Custom endpoint** or **LM Studio** in `hermes model` and supply your server's endpoint and model details. |

   For an API-key provider, follow the provider's own key and billing instructions. For example, place an OpenRouter key in the local Hermes environment file (create it if needed):

   ```dotenv
   OPENROUTER_API_KEY=your_key_here
   ```

   Save that entry in `~/.hermes/.env` **on your own machine**, not in this project's `shared/`, `profiles/`, or `fixtures/` folders. Never commit `.env`, API keys, or OAuth credentials to source control or put them in `TEAM.md`/`soul.md`.

4. Check the configured credentials and test the model in an interactive conversation:

   ```bash
   hermes auth list
   hermes
   ```

   At the Hermes chat prompt, send a simple test such as **“Reply with: connected”**. Confirm you receive a model-generated response, then exit the chat using its on-screen instructions.

5. Once the model works, start the project services explicitly:

   ```bash
   cd /path/to/nexs-hermes-bots
   sh bots start
   sh bots status
   ```

**Important:** Creating configured profiles does not by itself connect an LLM. The project's `sh bots sync` command synchronizes profile SOUL instructions, **not** LLM credentials. Depending on the Hermes configuration, profiles may use the installation's selected provider/model; check each profile's effective configuration if it behaves differently. Authentication, subscription eligibility, API quotas, and charges depend on the selected provider.

Official references: [Hermes Quickstart](https://hermes-agent.nousresearch.com/docs/getting-started/quickstart), [LLM and Model Providers](https://hermes-agent.nousresearch.com/docs/integrations/providers), and [Credential Management](https://hermes-agent.nousresearch.com/docs/user-guide/features/credential-pools).

## Synchronization and watcher configuration

Run `sh bots sync` to synchronize the union of `watcher.profiles` and `team.profiles`. For each configured profile, local `profiles/<profile>/soul.md` is authoritative: if it exists, sync publishes its contents to the Hermes profile `SOUL.md`, backing up the previous Hermes file as `SOUL.before-sync-<timestamp>.md` whenever content differs. If a configured profile has no local `soul.md`, sync first imports its Hermes `SOUL.md` (or creates a local stub), then synchronizes it. Each profile has `meta.json` updated with `name`, `source`, and `synced_at`; custom metadata fields are preserved. `sync` does not create Hermes profiles or start services; use `sh bots init` when a configured Hermes profile does not exist yet. **Review local SOUL edits before running sync, because they replace the active Hermes instructions.**

The project-root `config.json` contains both independent profile lists:

```json
{
  "watcher": {
    "profiles": ["support", "developer", "qa"],
    "dependencies": ["watchdog>=4,<7"]
  },
  "team": {
    "profiles": ["support", "developer", "qa"]
  }
}
```

- `watcher.profiles` selects which profile fixture directories the watcher monitors. Every listed name must be a real Hermes profile with a synchronized local `profiles/<profile>/soul.md`; `default` cannot be watched. Restart the watcher after changing this list. An empty list starts the watcher without monitoring any profile queues.
- `watcher.dependencies` declares the Python packages installed into the project-local `.venv` for the watcher. `sh bots init` and `sh bots start` reinstall them when this list changes.
- `team.profiles` selects the guarded-console targets and which dispatched profiles receive `TEAM.md`. The shared-instruction selection is consulted on every dispatch. An empty list disables both console targets and shared-instruction injection.

Initialization, synchronization, cancellation, cleanup, and log selection use the ordered union of both lists, with duplicates removed. The `default` Hermes profile is rejected in either list so project operations cannot accidentally target it.

## Working conventions

Default handoffs follow **Support → Developer → QA ↔ Developer → Support**. The watcher monitors only the synchronized profiles listed under `watcher.profiles` in the project-root `config.json`. Core Support/Developer/QA routes retain role-specific validation. Work files can live in `fixtures/developer/<ticket>/` and are preserved by cleanup. The `clean` operation removes the entire project-root `logs/` directory along with queued handoff Markdown and submission history; it preserves source subdirectories and `artifacts/`. Services must be stopped and a `[y/N]` confirmation is required, with no as the default.

No project-specific application, platform, or local environment is assumed. Live Hermes execution should be verified in your environment.

## Full uninstall

`sh bots uninstall` is destructive and requires a `[y/N]` confirmation in an interactive Terminal; no is the default. It stops the project watcher and Hermes Gateway, removes their user LaunchAgents, and runs the official `hermes uninstall --full --yes` command. A successful full uninstall removes Hermes Agent, Hermes Desktop when owned by the Hermes installer, and Hermes user data including profiles, sessions, chats, credentials, configuration, downloaded tools, plugins, caches, and logs.

The repository checkout and its local fixtures, logs, and submission history are preserved. If the Hermes CLI cannot be found, or the official full uninstall leaves a primary installation path behind, the command exits with an error instead of deleting unverified locations.
