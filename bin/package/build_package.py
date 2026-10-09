#!/usr/bin/env python3
"""Build an installable Ethos Lua package (.zip) for one language.

The zip is what FrSky Suite's Lua library ("Install from local .zip") and the
web simulator ("Upload a Lua plugin") install: the project folder plus a
generated ethos_lua_manifest.json at the zip root.

Steps:
  1. copy src/<tgt_name>/ to a temp staging folder
  2. resolve @i18n(key)@ tags with i18n/<lang>.json (English fallback)
  3. write build_info.lua (version, language, commit, build time)
  4. generate ethos_lua_manifest.json from src/<tgt_name>/ethos_lua_manifest.json
     (name, key, folder, introduction) + version + file list + release notes
  5. zip it as <tgt_name>-<version>-<lang>.zip

Usage:
  python bin/package/build_package.py --lang en
  python bin/package/build_package.py --lang de --artifact-version 1.2.0 --release-notes-file Notes.md
  python bin/package/build_package.py --all-langs --artifact-version 1.2.0-rc1

Versions: the manifest needs numeric X.Y.Z. A tag such as 1.2.0-rc1 or a
snapshot name is kept in build_info.lua, and the manifest falls back to the
numeric part (or to the version in src/<tgt_name>/ethos_lua_manifest.json).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

REPO = Path(__file__).resolve().parents[2]
MANIFEST = "ethos_lua_manifest.json"
VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")
LEADING_VERSION_RE = re.compile(r"^(\d+\.\d+\.\d+)")
KEY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
FOLDER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


def project_name() -> str:
    cfg = json.loads((REPO / ".vscode" / "deploy.json").read_text(encoding="utf-8"))
    return cfg["tgt_name"]


def languages() -> list[str]:
    return sorted(p.stem for p in (REPO / "i18n").glob("*.json")) or ["en"]


def git_commit() -> str:
    try:
        return subprocess.run(["git", "-C", str(REPO), "rev-parse", "--short", "HEAD"],
                              capture_output=True, text=True, timeout=10).stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def resolve_i18n(stage: Path, lang: str) -> None:
    src = REPO / "i18n" / f"{lang}.json"
    if not src.exists():
        src = REPO / "i18n" / "en.json"
    if not src.exists():
        print("[package] no i18n/*.json; skipping @i18n tag resolution")
        return
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
    subprocess.run([sys.executable, str(REPO / ".vscode" / "scripts" / "resolve_i18n_tags.py"),
                    "--json", str(src), "--root", str(stage)], check=True, env=env)


def build(lang: str, artifact_version: str | None, notes_file: str | None, out_dir: Path) -> Path:
    tgt = project_name()
    src = REPO / "src" / tgt
    if not src.is_dir():
        sys.exit(f"source folder not found: {src} (check tgt_name in .vscode/deploy.json)")
    base = json.loads((src / MANIFEST).read_text(encoding="utf-8")) if (src / MANIFEST).exists() else {}
    base_version = base.get("version", "0.1.0")
    label = artifact_version or base_version
    m = LEADING_VERSION_RE.match(label)
    manifest_version = label if VERSION_RE.match(label) else (m.group(1) if m else base_version)

    folder = base.get("folder", tgt)
    key = base.get("key", f"com.example.{tgt}")
    name = base.get("name", tgt)
    if not FOLDER_RE.fullmatch(folder) or not KEY_RE.fullmatch(key) or not VERSION_RE.fullmatch(manifest_version):
        sys.exit(f"invalid manifest values: folder={folder!r} key={key!r} version={manifest_version!r}")

    with tempfile.TemporaryDirectory(prefix=f"{tgt}-package-") as tmp:
        root = Path(tmp)
        stage = root / folder
        shutil.copytree(src, stage, ignore=shutil.ignore_patterns(MANIFEST, "*.luac", "__pycache__", ".DS_Store"))
        resolve_i18n(stage, lang)

        (stage / "build_info.lua").write_text(
            f'return {{ version = "{label}", lang = "{lang}", commit = "{git_commit()}", '
            f'built = "{dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M")}Z" }}\n',
            encoding="utf-8")

        files = sorted(p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file())
        if not any(f.endswith(("/main.lua", "/main.luac")) for f in files):
            sys.exit("package must contain main.lua or main.luac")
        manifest = {
            "manifestVersion": 1,
            "name": name,
            "key": key,
            "version": manifest_version,
            "folder": folder,
            "files": [f"{folder}/**"],
        }
        if base.get("introduction"):
            manifest["introduction"] = base["introduction"]
        if notes_file and Path(notes_file).exists():
            content = Path(notes_file).read_text(encoding="utf-8").strip()[:32000]
            if content:
                manifest["releaseNotes"] = {"format": "markdown", "content": content}
        elif base.get("releaseNotes"):
            manifest["releaseNotes"] = base["releaseNotes"]
        (root / MANIFEST).write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

        out_dir.mkdir(parents=True, exist_ok=True)
        zip_path = out_dir / f"{tgt}-{label}-{lang}.zip"
        with ZipFile(zip_path, "w", compression=ZIP_DEFLATED, compresslevel=9) as z:
            for p in sorted(root.rglob("*")):
                if p.is_file():
                    z.write(p, p.relative_to(root).as_posix())
    print(f"[package] {zip_path.name}: manifest version {manifest_version}, {len(files)} files")
    return zip_path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    lang = ap.add_mutually_exclusive_group(required=True)
    lang.add_argument("--lang", help="language to package, e.g. en")
    lang.add_argument("--all-langs", action="store_true", help="one zip per i18n/<lang>.json")
    ap.add_argument("--artifact-version", help="e.g. 1.2.0, 1.2.0-rc1 or a snapshot name (default: manifest version)")
    ap.add_argument("--release-notes-file", help="Markdown file embedded as the manifest releaseNotes")
    ap.add_argument("--output-dir", default=str(REPO / "dist"))
    ap.add_argument("--list-langs", action="store_true", help=argparse.SUPPRESS)
    args = ap.parse_args()

    out = Path(args.output_dir)
    for lg in (languages() if args.all_langs else [args.lang]):
        build(lg, args.artifact_version, args.release_notes_file, out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
