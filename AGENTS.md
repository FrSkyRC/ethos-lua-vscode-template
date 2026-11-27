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

Reference: https://frskyrc.github.io/ethos-lua-doc/ (API: `/api/`, machine-readable index: `/api/api-index.json`, best practice: `/best-practice/`, site map for agents: `/llms.txt`). Check that a function exists in `api-index.json` (it lists each one's signature and the Ethos version that added it) before calling it.

Its source is [FrSkyRC/ethos-lua-doc](https://github.com/FrSkyRC/ethos-lua-doc): the pages are Markdown under `docs/` (`api/`, `best-practice/`, `guides/`, `cookbook/`, `tools/`), and complete working scripts are under `examples/cookbook/`. Clone or read it when the site is not reachable, or to copy a pattern from a working example.

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

### Testing in the Ethos simulator

Agents can boot the Ethos WASM simulator, see its screen and operate it with touch, keys and the rotary encoder, using [FrSkyRC/ethos-tools](https://github.com/FrSkyRC/ethos-tools).

- **Claude Code:** `.claude/settings.json` lists the `ethos-tools` marketplace and enables its `ethos` plugin, so Claude Code offers to install it when the folder is trusted. By hand: `/plugin marketplace add FrSkyRC/ethos-tools`, then `/plugin install ethos@ethos-tools`. (Before plugin version 0.3.0 it was `ethos-simulator`, and its skill `ethos-navigate`: a session that still has those names needs the plugin installed again.) The plugin has an MCP server, whose tools (`startSimulator`, `press`, `touch`, `screenshot`, `getLog`, `reload`, `writeFile`...) act on the simulator, and the `ethos:navigate` skill, which covers starting the simulator, the screenshot loop and the radio buttons. If neither is in the session, restart it, or read `simulation/skills/navigate/SKILL.md` from a clone of ethos-tools.
- **Other agents:** run `simulation/run_wasm.js --serve` from a clone of ethos-tools. `simulation/run_wasm.md` lists the commands (`screenshot`, `press`, `touch`, `getLog`...).
- **Deploy first** (command above), then mount `simulators/<board>_<protocol>@<release>/` as the radio's root directory (`rootDirectory` of `startSimulator`, or `--root-directory`). Don't run a second simulator on the same folder at the same time, for example the VS Code extension's.
- **Simulator build:** `startSimulator(radio, release, rootDirectory)` (or `run_wasm.js --radio X18-EU`) downloads the simulator of any radio of an Ethos release, 26.2 or newer. The Ethos VS Code extension also caches the `<BOARD>_<PROTOCOL>.js` + `.wasm` pair in `<VS Code user dir>/globalStorage/bsongis.ethos/cache`.
- **Boot dialogs:** a fresh radio folder shows *Select language*, *Storage error, default settings restored* and the *Create model* wizard; later boots can show a *Checklist warning*. Dismiss each one before any other input: menu keys are ignored while a dialog is open.
- **After a redeploy:** `reload SCRIPTS` runs `main.lua` again but keeps modules cached in `package.loaded`. `reload ALL` starts a new Lua state, without restarting the simulator; the boot dialogs show again.
- **Lua errors** appear in the output of `getLog`, not on screen. One call returns at most 200 lines, so read it after every boot and after each action that loads code.
- **Smallest screen:** check layouts on an X18 (480x320) as well as the board in `.vscode/settings.json`. A model saved by a newer Ethos build will not load on an older one, so give a second board its own folder holding only a copy of `scripts/myproject`.

### Testing on a real radio

`simulation/radio_remote.py` from ethos-tools drives a USB-connected radio with the same screenshot / `press` / `touch` loop, over the radio's serial port ([`radio_remote.md`](https://github.com/FrSkyRC/ethos-tools/blob/main/simulation/radio_remote.md)). While it serves, the plugin's MCP tools act on the radio instead of the simulator.

- **Firmware:** an Ethos 26 nightly from 2026-10-16 or later.
- **Start:** `pip install pyserial hidapi`, `python radio_remote.py mode serial`, then `python radio_remote.py --serve` (port 8766).
- **A person must accept** the connection prompt on the radio screen, and every new connection asks again. Ask the user to start the server and accept it.
- **Never send `reload ALL` to a radio:** on an X20S with 26.2.0-RC11 it restarted the radio into its bootloader, off the serial port, until it was turned off and on again. Scripts load at boot, so after `writeFile` or a deploy, ask the user to restart the radio.
- **One program on the serial port at a time:** `quit` `radio_remote.py` before `deploy.py --radio --connect-only`, and the other way round.
- **No sticks, pots or switches:** the radio may be bound to a powered model.

**Done means:** no errors in the simulator log after boot, the changed UI checked with screenshots, i18n keys present in every language, and `ci.yml`'s checks passing.

## Releases

Bump `version` in the manifest, add the `Releases.md` section, commit, then `git tag release/X.Y.Z && git push origin release/X.Y.Z` (or `release/X.Y.Z-rc1`, `snapshot/...`). The Release workflow publishes per-language zips. Don't push tags unless asked.

## Gotchas

- `ELECTRON_RUN_AS_NODE=1` (set inside VS Code) breaks `FrSky Suite.exe` CLI calls; `deploy.py` clears it, so do the same if you call Suite yourself.
- Ethos compiles `main.lua` to `main.luac` on load. Deploys remove stale files, but hand-copied files can leave old bytecode behind.
- After `--radio` (without `--radio-debug`) the deploy switches the radio to serial mode so it releases USB storage. Its drive disappears, and that's expected.
