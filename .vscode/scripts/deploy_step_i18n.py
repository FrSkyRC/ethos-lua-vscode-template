#!/usr/bin/env python
import os
import sys
import argparse
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Resolve @i18n(...)@ tags for a given output dir + language."
    )
    parser.add_argument("--out-dir", required=True, help="Deployed project folder (scripts/<tgt_name>).")
    parser.add_argument("--lang", default="en", help="Language code, e.g. en, fr, de.")
    parser.add_argument(
        "--git-src",
        help="Workspace root; if omitted, will be inferred from this script location.",
    )
    args = parser.parse_args()

    out_dir = os.path.abspath(args.out_dir)
    lang = args.lang

    if args.git_src:
        git_src = os.path.abspath(args.git_src)
    else:
        # Assume this script is: <git_src>/.vscode/scripts/deploy_step_i18n.py
        git_src = str(Path(__file__).resolve().parents[2])

    # Translation files live in <repo>/i18n/<lang>.json (not deployed). A project
    # may also ship them inside src/<project>/i18n/. Missing language -> English.
    candidates = [
        os.path.join(out_dir, "i18n", f"{lang}.json"),
        os.path.join(git_src, "i18n", f"{lang}.json"),
        os.path.join(git_src, "i18n", "en.json"),
    ]
    json_path = next((p for p in candidates if os.path.isfile(p)), None)
    if not json_path:
        print(f"[I18N] Skipping: no {lang}.json or en.json in {os.path.join(git_src, 'i18n')}")
        return 0
    if not json_path.endswith(f"{lang}.json"):
        print(f"[I18N] {lang}.json not found; using English")

    resolver = os.path.join(git_src, ".vscode", "scripts", "resolve_i18n_tags.py")
    if not os.path.isfile(resolver):
        print(f"[I18N] Skipping: resolver not found at {resolver}")
        return 0

    # Unresolved keys are recorded here (and the file removed when there are
    # none) so AGENTS.md can point coding agents at the last deploy's result.
    report = os.path.join(git_src, ".vscode", "logs", "i18n-unresolved.json")

    print(f"[I18N] Resolving @i18n(...)@ tags (lang={lang})...")
    subprocess.run(
        [sys.executable, resolver, "--json", json_path, "--root", out_dir, "--report", report],
        check=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
