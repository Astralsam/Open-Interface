 # NOTE: i revised all of the repo and it works fine without implementing the additional dir and i compiled the code to a shorter version, thank you.



#!/usr/bin/env python3
"""
PyInstaller build script
Usage:  python3 build.py  ["Developer ID Application: …"]
"""
import os, sys, platform, subprocess, PyInstaller.__main__
from pathlib import Path
from app.version import version

APP      = "Open Interface"
DIST     = Path("dist")
RES      = Path("app/resources")
PY_FILES = list(Path("app").rglob("*.py"))

# ---------- helpers ----------
def run(cmd): subprocess.run(cmd, shell=True, check=True)
def confirm(msg):
    if input(f"{msg}  (y/n) ").lower() != "y": sys.exit("Aborted")

def zip_name():
    arch = {"arm": "-M-Series", "i386": "-Intel"}.get(platform.processor(), "")
    plat = {"Darwin": f"macOS{arch}", "Linux": "Linux", "Windows": "Windows"}[platform.system()]
    return f"{APP}-v{version}-{plat}.zip".replace(" ", "-")

def ditto_zip():
    run(f"cd {DIST} && ditto -c -k --sequesterRsrc --keepParent '{APP}.app' {zip_name()}")
def std_zip():
    run(f"cd {DIST} && zip -r9 {zip_name()} '{APP}'")

# ---------- core ----------
def pyi_args(key=None):
    """Return PyInstaller CLI list."""
    base = [
        "--clean", "--noconfirm", "--windowed",
        f"--name={APP}", f"--icon={RES}/icon.png",
        "--add-data", f"{RES}/*:resources",
        "--hidden-import", "pyautogui,appdirs,pyparsing,ttkbootstrap,openai,google_genai,google,google.genai",
        *sum([["--add-data", f"{p}:.{p.parent.relative_to('app')}"]
              for p in PY_FILES], []),
        "app/app.py"
    ]
    plat = platform.system()
    if plat == "Darwin":
        if key: base += [f"--codesign-identity={key}"]
    else:               # Linux / Windows
        base += ["--onefile"]
        if plat == "Linux":
            base += ["--hidden-import", "PIL._tkinter_finder"]
    return base

def build(key=None):
    confirm(f"Version incremented?  Current: v{version}")
    PyInstaller.__main__.run(pyi_args(key))
    if platform.system() == "Darwin" and key:
        run(f"codesign --deep --force --verbose --sign '{key}' '{DIST}/{APP}.app' --options runtime")
    zfile = zip_name()
    (ditto_zip if platform.system() == "Darwin" else std_zip)()
    if platform.system() == "Darwin" and key:
        profile = key.split("(")[0].strip()
        run(f"xcrun notarytool submit --wait --keychain-profile '{profile}' --verbose '{DIST}/{zfile}'")
        run(f"xcrun stapler staple '{DIST}/{APP}.app'")
        ditto_zip()          # re-zip stapled app

if __name__ == "__main__":
    key = sys.argv[1] if len(sys.argv) > 1 else None
    if platform.system() == "Darwin" and not key:
        confirm("Really build unsigned?")
    run("pip install -r requirements.txt")
    build(key)
