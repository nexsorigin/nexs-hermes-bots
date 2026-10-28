# Nex Hermes Bots

A reusable, local Hermes CLI automation scaffold. **The current default team consists of Support (`support`), Developer (`developer`), and QA (`qa`) agents.** This is an example team, not a required organization: other users can change the roles, number of profiles, and handoff workflow to meet their own needs, provided they keep the folder conventions and update the corresponding role names in the code and instructions.

> **Compatibility:** This setup has been tested on macOS only. Other operating systems have not been tested and may require changes to platform-specific service-management, clipboard, and installation behavior.

## Folder structure

```text
<clone-directory>/
├── bots                         # Run with: ./bots <command>
├── config.json                  # Watcher and TEAM.md profile lists
├── bin/                         # Executable Python and service scripts
│   ├── profiles.py              # Config loading and Hermes profile discovery
│   ├── sync.py                  # Mirror Hermes profiles into local folders
│   ├── setup.py                 # Initialization and SOUL.md importer
│   ├── watcher.py               # Dispatches incoming files to Hermes
│   └── …                         # Internal service launchers
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

**Folder rules for custom teams:** The repository clone directory is the project root. Runtime fixtures are stored under that project root at `fixtures/`; they are not stored in the user's home directory unless the repository itself was cloned there. Use `profiles/<profile>/soul.md` for a profile's handoff instructions, `fixtures/<profile>/` for its incoming queue, `shared/TEAM.md` for shared rules, and the project-root `config.json` for both profile lists. Profile names must match the real Hermes CLI profile names. Keep the SOUL template filenames as lowercase `soul.md` inside this project; `./bots init` imports their contents into the actual Hermes **`SOUL.md`** files at `~/.hermes/profiles/<profile>/SOUL.md` (or `$HERMES_HOME/profiles/...`). Hermes profile discovery uses `hermes profile list`.

Applications, plugins, and other work that received an explicit QA PASS are copied into `artifacts/`. There is no mandatory internal directory structure or manifest file; use clear, collision-free names and retain the matching QA evidence in the ticket workflow. Runtime artifacts are ignored by Git while `artifacts/README.md` remains tracked. A non-PASS verdict must never be promoted into this directory.

To customize the team, edit the profile lists in `config.json` and create matching `profiles/<profile>/soul.md` templates. `./bots init` creates missing configured Hermes profiles and fixture directories; `./bots sync` synchronizes only configured profiles. The watcher, guarded console, cancellation, cleanup, and log commands all derive their profile sets from the same configuration. The original handoff validation still has special behavior for Support and QA, so changing that workflow may require adjusting the role-specific checks in `bin/watcher.py`. Update filenames inside the handoff templates to match your team's workflow.

## Installation and migration

1. Back up your old `~/nexs-hermes-bots/` installation (if present), Hermes profile `SOUL.md` files, fixtures, and logs. Stop any old running services from **the old directory** using `./bots stop` before moving files.
2. Clone or place the package in any directory you choose. That clone directory becomes the project root; fixtures, logs, and submission history stay inside it. If upgrading, migrate any fixtures, shared instructions and history you want to keep. Do not simply overwrite your customized `TEAM.md` or `soul.md` templates.
3. Run:

   ```bash
   cd /path/to/nexs-hermes-bots
   ./bots init
   ```

   `init` checks that the watcher is stopped, installs the official Hermes CLI if missing, creates `.venv`, installs dependencies from `config.json` under `watcher.dependencies`, checks `hermes profile list`, creates profiles selected in `config.json`, and imports `profiles/<profile>/soul.md` into their actual Hermes `SOUL.md`. It does not install a model provider, download a model, or apply model routing. As a final best-effort readiness check, it may start an already-installed supported local model service only when the configured model is already present. When replacing existing profile instructions, it makes a timestamped backup. If the upstream Hermes installer is invoked it may perform its own setup or prompts.
4. Edit `shared/TEAM.md` for shared policies, configure its recipients and watched profiles in `config.json`, and edit the three `profiles/<profile>/soul.md` templates for role-specific handoffs. Rerun `./bots init` after changing the templates to import their updated contents (backing up existing SOUL files).
5. When ready, start services **separately** with `./bots start`. Check using `./bots status`.

**`./bots init` does not start the Hermes Gateway, watcher, project LaunchAgent, or any bot.** It can start an available local model service under the guarded readiness rules described below. The upstream Hermes installer is a third-party script and may have its own setup behavior. Profile creation and authorization may also require interaction. Manual CLI or Desktop conversations do not automatically receive the `TEAM.md` injection; it is applied by the file watcher to dispatched tasks.

`./bots start` repeats the guarded local-model-service readiness check used by init and preloads each available configured Ollama model, then verifies the watcher environment and creates it if needed before starting the Gateway. This makes a fresh clone self-contained; no manual virtual-environment setup is required. On every watcher start, existing handoff Markdown files under configured watcher profile queues are scanned as recovery candidates. Files already recorded with the same path and content hash in `submission_history.jsonl` are skipped, while unseen files created during watcher downtime are dispatched. As its final step, `./bots start` runs `./bots logs` to follow the watcher and profile logs; press Ctrl+C to stop following (the services keep running).

`./bots console` first ensures every profile in `team.profiles` has the narrow `cua:click:background` entry in its Hermes `command_allowlist`, preserving all existing entries. This lets the one-shot console turns perform background clicks even though they cannot pause for an interactive approval; foreground/focus-changing clicks and other guarded actions remain gated. Run `./bots console <profile>` (for example, `./bots console qa`) to select a listed team profile immediately, or omit the argument to display the numbered profile list. Direct launches use a profile-specific guarded tmux session, so an existing console for another profile cannot override the requested selection. The console's tmux session has mouse mode enabled so the wheel scrolls through console history instead of inserting arrow-key escape sequences at the prompt. Dragging across a Hermes response copies the selection directly to the clipboard, and every successful Hermes answer is also copied automatically after the turn finishes. Automatic copying supports `pbcopy`, `wl-copy`, `xclip`, `xsel`, and `clip.exe`. On macOS, the console verifies that `pbcopy` actually updated the GUI pasteboard and uses AppleScript as a fallback when it did not; it reports success only after the copied text is verified. This setting applies only to the guarded-console tmux session. After profile selection, the console displays that named session's most recent agent message, then sends every new message to the same persistent session. Shift+Enter adds a new line and displays a continuation prompt when the terminal reports it as a modified key, while a plain Enter submits the complete message. Terminals that send Shift+Enter as an ordinary Enter cannot be distinguished by tmux; use Option+Enter or end the line with `\` as the portable continuation fallback. Empty submissions are ignored silently. Press Esc to clear the current input without leaving that session. The same session is resumed across turns and future console launches while the profile's configured provider, model, and active Hermes `SOUL.md` remain unchanged. The session name fingerprints all three, so a model or SOUL update starts a fresh session with a newly built system prompt; returning to an earlier combination resumes its matching session. The model and SOUL fingerprint are rechecked before every turn. Type `exit;` at the profile prompt or press Ctrl+C to leave; the console does not return to profile selection after each turn. In macOS Terminal.app, open Settings → Profiles → Keyboard and either enable “Use Option as Meta key” for Option+Enter, or map Shift+Return to send Escape followed by Return so tmux receives `M-Enter`.

If your previous installation used the LaunchAgent `local.hermes.file-watcher`, stop and unload it before switching directories: the new install uses the same generic label and should not be competing with an old job pointing to the original path. The scripts do not remove the old installation automatically.

Run `./bots --help` for a short setup checklist, including model authentication and verification.

## Connect an AI model (LLM) to Hermes

Hermes needs an **inference provider** to respond to prompts. The project declares each profile's provider and model routing in `config.json`; `./bots sync` copies those declarations into Hermes's profile-scoped configuration. This synchronization only writes routing values. It never installs Homebrew packages or model providers, starts Ollama, pulls model files, or authenticates an account.

### Preferred default-team setup

Configure the default profiles with these providers:

| Profile | Role | Preferred provider |
| --- | --- | --- |
| `support` | Support | OpenAI Codex |
| `qa` | QA | Ollama through a named Hermes provider route |
| `developer` | Developer | OpenAI Codex |

The corresponding project configuration is:

```json
{
  "models": {
    "support": {
      "provider": "openai-codex",
      "model": "gpt-5.6-sol",
      "base_url": "https://chatgpt.com/backend-api/codex"
    },
    "qa": {
      "provider": "ollama",
      "model": "qwen3.5:4b",
      "base_url": "http://localhost:11434/v1"
    },
    "developer": {
      "provider": "openai-codex",
      "model": "gpt-5.6-sol",
      "base_url": "https://chatgpt.com/backend-api/codex"
    }
  }
}
```

During sync, the project registers `providers.ollama` as a named OpenAI-compatible Hermes route, using the declared `/v1` endpoint, `openai_chat` transport, and configured model as the provider default before assigning the profile's active model. Keeping both Hermes model values synchronized prevents the interactive model picker from displaying a stale provider-level selection. After writing routing for a declared profile, sync removes that profile's derived `provider_models_cache.json`; the next Hermes model picker fetches the current provider catalog instead of retaining an obsolete model. This also avoids its warning for an undefined bare `ollama` or `custom` provider. The configured model must already exist in that Ollama instance. Installing Ollama and pulling the selected model are explicit user-managed prerequisites outside this project. Change the relevant `models.<profile>.model` value if your environment uses another installed model, then run `./bots sync`. A profile omitted from `models` retains its existing Hermes model configuration and cache. Model entries may only target profiles listed by `watcher.profiles` or `team.profiles`.

During `./bots init` and `./bots start`, the Ollama readiness check reads the local model manifest without contacting or starting Ollama. It runs `brew services start ollama` only when the `ollama` executable exists, the Homebrew formula is installed, and the configured model manifest already exists. After the service becomes available, it sends Ollama an empty native generate request with `keep_alive: -1`, which preloads the configured model and keeps it in memory until `./bots stop` stops Ollama. If any prerequisite is absent—or the service or model cannot start—the command reports the skip or warning and continues. It never runs an installer or model pull. Codex is remote and has no local service to start.

`./bots stop` applies the same guarded checks in reverse. It runs `brew services stop ollama` only when Ollama, its Homebrew formula, and the configured local model are present. Missing prerequisites and shutdown failures are reported and skipped without preventing the watcher and Hermes Gateway stop routine from completing. It does not uninstall the runtime or delete any model files.

1. Make sure the Hermes CLI is available:

   ```bash
   hermes version
   ```

2. Complete provider authentication where required. For the default Codex profiles, run the model flow for each profile and complete the device-code login:

   ```bash
   hermes -p support model
   hermes -p developer model
   ```

   QA uses the configured local Ollama endpoint and normally needs no credentials. Ensure Ollama is running and the configured model is installed before starting agent work.

3. Other supported provider choices include:

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
   ./bots start
   ./bots status
   ```

**Important:** Model declarations contain routing settings only, never credentials or installation instructions. The project's `./bots sync` command synchronizes both profile SOUL instructions and declared model routing. Authentication, provider installation, model acquisition, subscription eligibility, API quotas, and charges remain the user's responsibility.

Official references: [Hermes Quickstart](https://hermes-agent.nousresearch.com/docs/getting-started/quickstart), [LLM and Model Providers](https://hermes-agent.nousresearch.com/docs/integrations/providers), and [Credential Management](https://hermes-agent.nousresearch.com/docs/user-guide/features/credential-pools).

## Synchronization and watcher configuration

Run `./bots sync` to synchronize the union of `watcher.profiles` and `team.profiles`. For each configured profile, local `profiles/<profile>/soul.md` is authoritative: if it exists, sync publishes its contents to the Hermes profile `SOUL.md`, backing up the previous Hermes file as `SOUL.before-sync-<timestamp>.md` whenever content differs. If a configured profile has no local `soul.md`, sync first imports its Hermes `SOUL.md` (or creates a local stub), then synchronizes it. Each profile has `meta.json` updated with `name`, `source`, and `synced_at`; custom metadata fields are preserved. `sync` does not create Hermes profiles or start services; use `./bots init` when a configured Hermes profile does not exist yet. **Review local SOUL edits before running sync, because they replace the active Hermes instructions.**

The project-root `config.json` contains both independent profile lists:

```json
{
  "watcher": {
    "profiles": ["support", "developer", "qa"],
    "dependencies": ["watchdog>=4,<7"]
  },
  "team": {
    "profiles": ["support", "developer", "qa"]
  },
  "models": {
    "support": {
      "provider": "openai-codex",
      "model": "gpt-5.6-sol",
      "base_url": "https://chatgpt.com/backend-api/codex"
    },
    "qa": {
      "provider": "ollama",
      "model": "qwen3.5:4b",
      "base_url": "http://localhost:11434/v1"
    },
    "developer": {
      "provider": "openai-codex",
      "model": "gpt-5.6-sol",
      "base_url": "https://chatgpt.com/backend-api/codex"
    }
  }
}
```

- `watcher.profiles` selects which profile fixture directories the watcher monitors. Every listed name must be a real Hermes profile with a synchronized local `profiles/<profile>/soul.md`; `default` cannot be watched. Restart the watcher after changing this list. An empty list starts the watcher without monitoring any profile queues.
- `watcher.dependencies` declares the Python packages installed into the project-local `.venv` for the watcher. `./bots init` and `./bots start` reinstall them when this list changes.
- `team.profiles` selects the guarded-console targets and which dispatched profiles receive `TEAM.md`. The shared-instruction selection is consulted on every dispatch. An empty list disables both console targets and shared-instruction injection.
- `models` maps configured profile names to their Hermes `provider`, `model`, and optional `base_url`. `./bots sync` copies only those routing values into Hermes. For `ollama`, the endpoint is required and sync also maintains the named `providers.ollama` route. It does not install providers, download models, or store credentials. Undeclared configured profiles retain their existing model settings.

Initialization, synchronization, cancellation, cleanup, and log selection use the ordered union of both lists, with duplicates removed. The `default` Hermes profile is rejected in either list so project operations cannot accidentally target it.

## Working conventions

Default handoffs follow **Support → Developer → QA ↔ Developer → Support**. The watcher monitors only the synchronized profiles listed under `watcher.profiles` in the project-root `config.json`. Core Support/Developer/QA routes retain role-specific validation. Work files can live in `fixtures/developer/<ticket>/` and are preserved by cleanup. The `clean` operation removes the entire project-root `logs/` directory along with queued handoff Markdown and submission history; it preserves source subdirectories and `artifacts/`. Services must be stopped and a `[y/N]` confirmation is required, with no as the default.

No project-specific application, platform, or local environment is assumed. Live Hermes execution should be verified in your environment.

## Full uninstall

`./bots uninstall` is destructive and requires a `[y/N]` confirmation in an interactive Terminal; no is the default. It stops the project watcher and Hermes Gateway, removes their user LaunchAgents, and runs the official `hermes uninstall --full --yes` command. A successful full uninstall removes Hermes Agent, Hermes Desktop when owned by the Hermes installer, and Hermes user data including profiles, sessions, chats, credentials, configuration, downloaded tools, plugins, caches, and logs.

The repository checkout and its local fixtures, logs, and submission history are preserved. If the Hermes CLI cannot be found, or the official full uninstall leaves a primary installation path behind, the command exits with an error instead of deleting unverified locations.
