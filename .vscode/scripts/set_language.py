#!/usr/bin/env python3
"""Set the language used by deploys (VS Code setting "ethos.deploy.language").

Called by the "Set Deployment Language" launch configuration with the language
picked from the list (built from i18n/*.json would be ideal, but VS Code pick
lists are static: keep "inputs" in launch.json in sync with your i18n/ folder).
"""
import json
import sys
from pathlib import Path

lang = sys.argv[1] if len(sys.argv) > 1 else "en"
root = Path(__file__).resolve().parents[2]
if not (root / "i18n" / f"{lang}.json").exists():
    print(f"warning: i18n/{lang}.json does not exist yet; deploys will fall back to English")
settings_path = root / ".vscode" / "settings.json"
settings = json.loads(settings_path.read_text(encoding="utf-8")) if settings_path.exists() else {}
settings["ethos.deploy.language"] = lang
settings_path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
print("Deployment language set to:", lang)
