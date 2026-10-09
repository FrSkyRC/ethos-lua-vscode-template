#!/usr/bin/env python3
"""Example deploy step: a template for your own build steps.

deploy.py runs optional "steps" after copying src/<tgt_name>/ to the target
and before (for radio deploys) the files are written to the radio. Ask for a
step with `--step <name>` in .vscode/tasks.json; deploy.py then runs
.vscode/scripts/deploy_step_<name>.py like this:

    python deploy_step_<name>.py --out-dir OUT --lang LANG --git-src REPO_ROOT

  --out-dir  the deployed copy of your project (e.g. simulators/X20S_FCC@nightly26/scripts/myproject,
             or a local staging folder for radio deploys, so edits are fast and safe)
  --lang     value of --lang / the "ethos.deploy.language" setting
  --git-src  repository root

Edit files under --out-dir only, never under src/. A non-zero exit code is
reported as a failed step; the deploy itself continues.

Typical uses in real projects: generating a translation table for the chosen
language, building a sound pack, stamping a version/build date into a file,
copying simulator-only fixtures (e.g. simulated telemetry definitions) to the
simulator folder, or stripping debug-only files from radio builds.

This example writes the git commit and build time to build_info.lua, so the
script can show which build is on the radio:

    local info = loadfile("build_info.lua")   -- at load time, in main.lua
    info = info and info() or {}

To use it, add to the deploy task's "args" in .vscode/tasks.json:
    "--step", "example"
"""

import argparse
import datetime as dt
import subprocess
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True, help="deployed project folder (scripts/<tgt_name>)")
    ap.add_argument("--lang", default="en")
    ap.add_argument("--git-src", default=str(Path(__file__).resolve().parents[2]))
    args = ap.parse_args()

    out = Path(args.out_dir)
    try:
        commit = subprocess.run(["git", "-C", args.git_src, "rev-parse", "--short", "HEAD"],
                                capture_output=True, text=True, timeout=10).stdout.strip() or "unknown"
    except Exception:
        commit = "unknown"
    stamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M")

    (out / "build_info.lua").write_text(
        f'return {{ commit = "{commit}", built = "{stamp}", lang = "{args.lang}" }}\n', encoding="utf-8")
    print(f"[STEP example] wrote build_info.lua (commit {commit}, {stamp})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
