#!/usr/bin/env python3
"""Rename the template's starter project ("myproject") to your own name.

Usage (from the repository root):
    python .vscode/scripts/new_project.py mywidget
    python .vscode/scripts/new_project.py mywidget --key com.yourname.mywidget --title "My Widget"

What it changes:
  * src/myproject/            -> src/<name>/           (the folder deployed to SCRIPTS:/<name>/)
  * .vscode/deploy.json       "tgt_name"               (what deploy.py copies)
  * SCRIPTS:/myproject/ paths in src/<name>/*.lua      (absolute paths used from callbacks)
  * ethos_lua_manifest.json   folder / key / name      (installable zip metadata)
  * widget key in widget.lua; display name in i18n/en.json (project.name)
  * "[myproject]" log prefix in lib/util.lua
  * README.md / AGENTS.md mentions of src/myproject

<name>: letters, digits, '_' or '-', max 32 chars (it becomes a folder on the radio).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OLD = "myproject"


def replace_in(path: Path, pairs: list[tuple[str, str]]) -> None:
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    new = text
    for a, b in pairs:
        new = new.replace(a, b)
    if new != text:
        path.write_text(new, encoding="utf-8")
        print(f"  updated {path.relative_to(ROOT).as_posix()}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("name", help="new project / folder name, e.g. mywidget")
    ap.add_argument("--key", help="manifest key, e.g. com.yourname.mywidget (default com.example.<name>)")
    ap.add_argument("--title", help='display name, e.g. "My Widget" (default: name)')
    ap.add_argument("--widget-key", help="widget key, max 7 chars (default: first 7 chars of name)")
    args = ap.parse_args()

    name = args.name
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,31}", name):
        sys.exit("name must be letters/digits/_/- (max 32), starting with a letter or digit")
    src_old, src_new = ROOT / "src" / OLD, ROOT / "src" / name
    if not src_old.is_dir():
        sys.exit(f"{src_old} not found - already renamed?")
    if src_new.exists():
        sys.exit(f"{src_new} already exists")
    title = args.title or name
    key = args.key or f"com.example.{name}"
    wkey = (args.widget_key or re.sub(r"[^A-Za-z0-9]", "", name))[:7] or "widget"

    src_old.rename(src_new)
    print(f"  renamed src/{OLD} -> src/{name}")

    cfg_path = ROOT / ".vscode" / "deploy.json"
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    cfg["tgt_name"] = name
    cfg_path.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
    print("  updated .vscode/deploy.json")

    man_path = src_new / "ethos_lua_manifest.json"
    if man_path.exists():
        man = json.loads(man_path.read_text(encoding="utf-8"))
        man.update({"folder": name, "key": key, "name": title})
        man_path.write_text(json.dumps(man, indent=2) + "\n", encoding="utf-8")
        print(f"  updated src/{name}/ethos_lua_manifest.json")

    for lua in src_new.rglob("*.lua"):
        replace_in(lua, [
            (f"SCRIPTS:/{OLD}/", f"SCRIPTS:/{name}/"),
            (f"[{OLD}]", f"[{name}]"),
            ('key = "myproj"', f'key = "{wkey}"'),
            (f"-- {OLD}:", f"-- {name}:"),
        ])
    # display name lives in the English translations (project.name)
    en = ROOT / "i18n" / "en.json"
    if en.exists():
        data = json.loads(en.read_text(encoding="utf-8"))
        data.setdefault("project", {})["name"] = title
        en.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print("  updated i18n/en.json (project.name)")

    for doc in ("README.md", "AGENTS.md"):
        replace_in(ROOT / doc, [(f"src/{OLD}", f"src/{name}"), (f"SCRIPTS:/{OLD}/", f"SCRIPTS:/{name}/"), (f"[{OLD}]", f"[{name}]")])

    print(f"\nDone. Your script deploys to SCRIPTS:/{name}/ (widget key '{wkey}').")
    return 0


if __name__ == "__main__":
    sys.exit(main())
