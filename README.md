# Ethos Lua VS Code template

A ready-to-use VS Code project for writing **FrSky Ethos Lua scripts**: press ▶ to deploy to the Ethos simulator or to a radio on USB, read the radio's `print()` output live, translate your script into several languages, and publish installable release zips from a git tag.

The deploy tooling is the same one large open-source Ethos suites use day to day. Only the project-specific parts were taken out.

Documentation: **[Ethos Lua Docs → VS Code project template](https://frskyrc.github.io/ethos-lua-doc/tools/vscode-template/)**

---

## 1. Install the tools (once per computer)

| Tool | Why | How |
| --- | --- | --- |
| **VS Code** | Editor and play buttons | [code.visualstudio.com](https://code.visualstudio.com/) |
| **Python 3.10+** | Runs the deploy and packaging scripts | See below |
| **VS Code extensions** | Simulator, Python, Lua | VS Code offers them when you open this folder (from `.vscode/extensions.json`): **Ethos** (`bsongis.ethos`), **Python** + **Python Debugger** (Microsoft), **Lua** (sumneko) |
| **Git** | Version control and releases | [git-scm.com](https://git-scm.com/) |

### Installing Python

- **Windows:** install from [python.org/downloads](https://www.python.org/downloads/). On the first installer screen tick **"Add python.exe to PATH"**. Check in a new terminal: `python --version`.
- **macOS:** `brew install python` (with [Homebrew](https://brew.sh/)), or the python.org installer. Check: `python3 --version`.
- **Linux:** usually already installed; otherwise `sudo apt install python3 python3-pip`.

Then in VS Code: **Ctrl+Shift+P → "Python: Select Interpreter"** and pick that Python. The play buttons run the deploy with **this** interpreter.

You do **not** need to `pip install` anything by hand: the first deploy installs what it needs (`tqdm`, `pyserial`, `hidapi`, and `pywin32` on Windows) into the selected interpreter. If you prefer to do it yourself:

```bash
python -m pip install tqdm pyserial hidapi pywin32   # pywin32: Windows only
```

> A virtual environment works too: `python -m venv .venv`, then select `.venv` as the interpreter.

## 2. Make it your project (once per project)

1. Click **Use this template** on GitHub (or clone and copy the folder).
2. Rename the starter project. In a terminal at the repository root:

   ```bash
   python .vscode/scripts/new_project.py mywidget --title "My Widget" --key com.yourname.mywidget
   ```

   This renames `src/myproject/` → `src/mywidget/` and updates every place the name is used (see [the table below](#3-what-you-change-per-project)).
3. Open the folder in VS Code and install the recommended extensions.
4. Click the Ethos simulator status-bar item (or **Ctrl+Shift+P → Ethos: Set Simulator**) and pick your radio, protocol and Ethos release. The extension downloads that simulator build.

## 3. What you change per project

Everything you edit is in this table. The scripts in `.vscode/scripts/` and `bin/` are shared tooling: **don't edit them** unless you are extending the tooling itself, so you can update them from this template later.

| File | What to change | Notes |
| --- | --- | --- |
| `src/<project>/` | **Your Lua code**: everything that goes to the radio | Deployed to `SCRIPTS:/<project>/` |
| `.vscode/deploy.json` → `tgt_name` | Your project folder name | Must match `src/<project>/` (set by `new_project.py`) |
| `src/<project>/ethos_lua_manifest.json` | `name`, `key`, `version`, `introduction` | `key` must never change after your first release |
| `src/<project>/main.lua` → `BASE` | `SCRIPTS:/<project>/` | Absolute path for files used from callbacks (set by `new_project.py`) |
| `src/<project>/widget.lua` → `key` | Widget key, **max 7 characters**, unique | Never change it after release: models refer to it |
| `i18n/<lang>.json` | Your translated strings | Add a file per language, e.g. `i18n/fr.json` |
| `.vscode/launch.json` → `inputs.deployLanguage.options` | List of your languages | Shown by **Set Deployment Language** |
| `.vscode/settings.json` → `ethos.board`, `ethos.protocol`, `ethos.release` | Your simulator | Normally set through the Ethos extension |
| `.vscode/deploy.json` → `serial_*`, `ethossuite_bin` | Only if your radio needs it | Defaults work for current FrSky radios; FrSky Suite is optional |
| `Releases.md` | Release notes per version | Used by the release workflow |
| `README.md`, `AGENTS.md` | Describe *your* project | Replace this text |

## 4. The play buttons

Open **Run and Debug** (Ctrl+Shift+D), pick a configuration from the dropdown and press ▶ (or F5).

| ▶ Configuration | What it runs | What happens |
| --- | --- | --- |
| **Deploy & Launch [SIM]** | `deploy.py --lang <lang> --step i18n`, then the Ethos extension's `ethos.start` | Mirrors `src/<project>/` into `simulators/<board>_<protocol>@<release>/scripts/<project>/`, resolves translations, starts the simulator |
| **Deploy Radio** | `deploy.py --radio ...` | Finds the radio on USB, switches it to storage mode if needed, waits for its drive, **full** safe copy, then switches the radio to serial mode so it releases USB storage and runs the new code |
| **Deploy Radio [Fast]** | `deploy.py --fileext fast --radio ...` | Same, but copies only changed files (MD5 compare) and removes deleted ones. Use this day to day |
| **Deploy Radio + Serial Debug** / **[Fast]** | `... --radio-debug` | Deploys, then streams the radio's `print()` output into the terminal until you stop it |
| **Radio: Serial Debug** | `deploy.py --radio --connect-only` | No copy: just switch to serial and stream `print()` output |
| **Simulator: Set Simulator / Open Controls / Open Telemetry** | Ethos extension commands | Pick a simulator, open the sticks/switches or telemetry panels |
| **Set Deployment Language** | `set_language.py <lang>` | Sets `ethos.deploy.language` used by every deploy |
| **Package: Build Zip [current language]** / **[all languages]** | `bin/package/build_package.py` | Builds installable zips in `dist/` (see §6) |
| **Debug Radio Connection** | `debug_connection.py` | Diagnoses USB/HID/drive detection problems |
| **Clear locks** | `deploy.py --clear-lock` | Removes a stale "deploy already running" lock after a crash |

**How it works:** VS Code only puts *launch configurations* in the Run dropdown. Each configuration here is a Python launch of an empty file (`.vscode/scripts/dummy.py`) whose `preLaunchTask` is the real work, defined in `.vscode/tasks.json`. `postDebugTask` chains the next step, for example starting the simulator after a deploy. The tasks run `deploy.py` with the interpreter you selected (`${command:python.interpreterPath}`).

**How the radio is reached:** over the radio's USB **HID** interface (the one FrSky Suite uses) to switch between storage and serial modes, finding its drive by the `*.cpuid` marker file. FrSky Suite does **not** need to be installed. Details: [Ethos Lua Docs → VS Code deployments](https://frskyrc.github.io/ethos-lua-doc/tools/vscode/).

## 5. Translations (i18n)

Write user-facing text as tags inside Lua strings:

```lua
local line = form.addLine("@i18n(widget.source)@")
```

and the text in `i18n/<lang>.json`:

```json
{ "widget": { "source": "Source" } }
```

Deploys (step `i18n`) and packages replace every `@i18n(key)@` with the text for the selected language; English is the fallback. Tags can transform text: `@i18n(widget.source):upper()@`, `@i18n(tool.print):truncate(8)@`. Run `python .vscode/scripts/resolve_i18n_tags.py --list-transforms` for all transforms. Missing keys are listed after each deploy and in `.vscode/logs/i18n-unresolved.json`.

Add a language: copy `i18n/en.json` to `i18n/fr.json`, translate it, and add `"fr"` to `inputs.deployLanguage.options` in `.vscode/launch.json`. The release workflow finds new languages automatically.

## 6. Releases

Release zips are what users install with **FrSky Suite → Lua library → Install from local .zip** (or the web simulator's **Upload a Lua plugin**). Each contains your project folder and a generated `ethos_lua_manifest.json`, one zip per language.

### Build locally

```bash
python bin/package/build_package.py --lang en                       # dist/<project>-<version>-en.zip
python bin/package/build_package.py --all-langs --artifact-version 1.2.0
```

### Publish with a git tag

1. Update `version` in `src/<project>/ethos_lua_manifest.json`.
2. Add a `# 1.2.0` section at the top of `Releases.md`.
3. Commit, then tag and push:

```bash
git tag release/1.2.0
git push origin release/1.2.0
```

The **Release** workflow builds a zip per language, validates each manifest, and publishes a GitHub release with the notes from `Releases.md`.

| Tag | GitHub release |
| --- | --- |
| `release/1.2.0` | Release |
| `release/1.2.0-rc1` | Release Candidate (pre-release) |
| `snapshot/1.2.0-dev3` | Snapshot (pre-release) |

The manifest version must be numeric `X.Y.Z`: for `1.2.0-rc1` the manifest gets `1.2.0`, and the full label is kept in `build_info.lua` inside the package. Your script can read it at load time with `loadfile("build_info.lua")`.

A tag pushed by mistake can be removed with `git push --delete origin release/1.2.0` and `git tag -d release/1.2.0`. Delete the GitHub release as well.

The **CI** workflow runs on every push and pull request: Lua syntax check of every language build (`luac5.4 -p`), manifest validation, and test zips downloadable from the run.

## 7. Repository layout

```text
src/myproject/            your script (deployed to SCRIPTS:/myproject/)
  main.lua                entry point: registers the widget and the tool
  widget.lua, tool.lua    starter widget and system tool
  lib/util.lua            shared helpers
  icon.png                system tool icon (mask: black on white)
  ethos_lua_manifest.json package name / key / version
i18n/                     en.json, de.json ... translations
bin/package/              build_package.py, validate_ethos_manifest_zip.py
.vscode/
  launch.json             ▶ play-button configurations
  tasks.json              what each one runs
  settings.json           simulator board/protocol/release, deploy language
  deploy.json             project name (tgt_name), radio serial settings
  ethos-menu.json         Ethos status-bar quick menu
  extensions.json         recommended extensions
  scripts/                shared deploy tooling (don't edit)
.github/workflows/        ci.yml, release.yml
simulators/               created by the Ethos extension (git-ignored)
dist/                     built zips (git-ignored)
```

## 8. Troubleshooting

| Problem | Fix |
| --- | --- |
| ▶ does nothing / "debugpy" error | Install the **Python** and **Python Debugger** extensions and select an interpreter |
| `Radio drive did not mount within 60s` | Radio on, USB cable plugged in, and on the radio choose the USB storage mode if it asks. Then run **Debug Radio Connection** |
| `No Ethos compatible HID device found (vendor 0x0483 not present)` | The radio isn't on USB (switched off, charge-only cable, or still re-enumerating) |
| "Another deploy is running" | Wait, or run **Clear locks** |
| Simulator shows old code | Deploys delete stale files; if you copied files by hand, delete `main.luac` and restart the simulator |
| `@i18n(...)@` text on screen | Key missing from `i18n/<lang>.json`; see the deploy output |

## License

Add your project's license here.
