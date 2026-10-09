# Agent guide

This is an **FrSky Ethos Lua** project built from the Ethos Lua VS Code template. Read this before changing code. Replace the "About this project" section with a description of your script.

## About this project

`src/myproject/`: starter widget + system tool. *(Describe your script here: what it shows or does, which radios and Ethos versions it targets.)*

## Where things are, and what may be edited

| Path | Edit? | What |
| --- | --- | --- |
| `src/myproject/**` | **Yes** | The Lua that runs on the radio. Deployed to `SCRIPTS:/myproject/` |
| `i18n/<lang>.json` | **Yes** | Translations for `@i18n(key)@` tags. Keep every language's keys in step with `en.json` |
| `src/myproject/ethos_lua_manifest.json` | Yes (version, introduction) | Never change `key` after a release |
| `Releases.md` | Yes | Add a `# <version>` section before tagging a release |
| `.vscode/deploy.json`, `.vscode/settings.json`, `.vscode/launch.json` inputs | Only when asked | Project name, simulator, language list |
| `.vscode/scripts/**`, `bin/package/**`, `.github/**` | **No** (shared tooling) | Change only when the task is about the tooling itself |
| `simulators/`, `dist/`, `.vscode/logs/` | Never commit | Generated |

## Ethos Lua rules (must follow)

Reference: https://frskyrc.github.io/ethos-lua-doc/ (API: `/api/`, machine-readable index: `/api/api-index.json`, best practice: `/best-practice/`).

- **Hot paths** (`wakeup`, `paint`, event handlers): no per-call table, closure or string allocation; call `lcd.invalidate()` only when something visible changed; compare values at display precision.
- **Paths:** relative paths only resolve while `main.lua` loads. Any file access from a callback uses `SCRIPTS:/myproject/...` (see `BASE` in `main.lua`).
- **Nil-check** `system.getSource`, `model.createSensor`, `lcd.loadBitmap`/`loadMask`, dialog handles, `io.open`.
- **Guard newer APIs** (`if system.getSources then ... end`) for older firmware.
- **Release resources** (bitmaps, caches, file handles, dialogs) in a tool's `close()`.
- Widget keys are max 7 characters and must never change after a release.
- **User-facing text** goes through `@i18n(key)@` tags, with the key added to **every** `i18n/*.json`. Never hard-code display strings.
- System tool icons are masks: black shapes on white (dark pixels are drawn).
- Prefix `print()` output with `[myproject]` (see `lib/util.lua`).

## Build, deploy, test

| Goal | Command (from repo root) |
| --- | --- |
| Deploy to simulator | `python .vscode/scripts/deploy.py --lang en --step i18n` |
| Deploy to USB radio (fast) | `python .vscode/scripts/deploy.py --fileext fast --radio --lang en --step i18n` |
| Stream radio `print()` output | `python .vscode/scripts/deploy.py --radio --connect-only` (runs until stopped) |
| Build installable zips | `python bin/package/build_package.py --all-langs` |
| Validate a zip | `python bin/package/validate_ethos_manifest_zip.py dist/<zip>` |
| Lua syntax check | Build zips, unzip, `luac5.4 -p` every `.lua` (as `.github/workflows/ci.yml` does) |

Simulator deploys go to `simulators/<board>_<protocol>@<release>/scripts/myproject/` (board/protocol/release from `.vscode/settings.json`).

**Testing in the simulator without VS Code:** use [FrSkyRC/ethos-tools](https://github.com/FrSkyRC/ethos-tools). The Claude Code plugin is `ethos-simulator@ethos-tools` (already enabled in `.claude/settings.json`), or run `simulation/run_wasm.js --serve --root-directory simulators/<board>_<protocol>@<release>` directly. Lua errors appear in `node run_wasm.js log`, not on screen. A fresh radio folder shows *Select language → Storage error → Model wizard* dialogs first.

**Done means:** no errors in the simulator log after boot, the changed UI checked with screenshots, i18n keys present in every language, and `ci.yml`'s checks passing.

## Releases

Bump `version` in the manifest, add the `Releases.md` section, commit, then `git tag release/X.Y.Z && git push origin release/X.Y.Z` (or `release/X.Y.Z-rc1`, `snapshot/...`). The Release workflow publishes per-language zips. Don't push tags unless asked.

## Gotchas

- `ELECTRON_RUN_AS_NODE=1` (set inside VS Code) breaks `FrSky Suite.exe` CLI calls; `deploy.py` clears it, so do the same if you call Suite yourself.
- Ethos compiles `main.lua` to `main.luac` on load. Deploys remove stale files, but hand-copied files can leave old bytecode behind.
- After `--radio` (without `--radio-debug`) the deploy switches the radio to serial mode so it releases USB storage. Its drive disappears, and that's expected.
