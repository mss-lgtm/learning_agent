#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TikTok Publisher - Build Script
Simple Python build script that works on any system
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run(cmd, check=True):
    """Run a command"""
    print(f"  Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"  ERROR: {result.stderr}")
        return False
    return True

def main():
    print("=" * 50)
    print("TikTok Publisher - Build Script")
    print("=" * 50)
    print()

    # Get project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)

    # Step 1: Check Python
    print("[1/5] Checking Python...")
    print(f"  Python {sys.version}")
    print("  OK")
    print()

    # Step 2: Install dependencies
    print("[2/5] Installing dependencies...")
    if not run(f'"{sys.executable}" -m pip install -r requirements.txt -q'):
        print("  Failed to install dependencies")
        return 1
    print("  OK")
    print()

    # Step 3: Create icon
    print("[3/5] Creating icon...")
    if not Path("assets").exists():
        Path("assets").mkdir()
    if not run(f'"{sys.executable}" create_icon.py'):
        print("  Warning: Icon creation failed, continuing...")
    else:
        print("  OK")
    print()

    # Step 4: Clean old builds
    print("[4/5] Cleaning old builds...")
    for dir_name in ["build"]:
        if Path(dir_name).exists():
            try:
                shutil.rmtree(dir_name)
                print(f"  Removed {dir_name}/")
            except Exception as e:
                print(f"  Warning: Could not remove {dir_name}: {e}")

    # Try to remove dist, but handle permission errors
    if Path("dist").exists():
        try:
            shutil.rmtree("dist")
            print("  Removed dist/")
        except PermissionError:
            print("  Warning: dist/ is in use, will overwrite files")
        except Exception as e:
            print(f"  Warning: Could not remove dist: {e}")
    print("  OK")
    print()

    # Step 5: Build with PyInstaller
    print("[5/5] Building with PyInstaller...")
    pyinstaller_cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--noconsole",
        "--name", "TikTokPublisherWeb",
        "--icon", "assets/icon.ico",
        "--add-data", "web/templates;web/templates",
        "--add-data", "web/static;web/static",
        "--hidden-import", "selenium.webdriver.chrome.webdriver",
        "--hidden-import", "selenium.webdriver.chrome.service",
        "--hidden-import", "selenium.webdriver.chrome.options",
        "--hidden-import", "selenium.webdriver.common.service",
        "--hidden-import", "selenium.webdriver.common.options",
        "--hidden-import", "selenium.webdriver.remote.webdriver",
        "--hidden-import", "selenium.webdriver.remote.error_handler",
        "--hidden-import", "selenium.webdriver.remote.command",
        "--hidden-import", "selenium.webdriver.remote.connection",
        "--hidden-import", "selenium.webdriver.common.by",
        "--hidden-import", "selenium.webdriver.common.keys",
        "--hidden-import", "selenium.webdriver.support.ui",
        "--hidden-import", "selenium.webdriver.support.expected_conditions",
        "--hidden-import", "selenium.common.exceptions",
        "--hidden-import", "urllib3",
        "--hidden-import", "urllib3.connectionpool",
        "run_web.py"
    ]

    result = subprocess.run(pyinstaller_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ERROR: {result.stderr}")
        return 1
    print("  OK")
    print()

    # Copy web resources
    print("Copying web resources...")
    dist_web = Path("dist/web")
    dist_web.mkdir(exist_ok=True)

    if Path("web/templates").exists():
        shutil.copytree("web/templates", dist_web / "templates", dirs_exist_ok=True)
    if Path("web/static").exists():
        shutil.copytree("web/static", dist_web / "static", dirs_exist_ok=True)
    if Path("assets/icon.ico").exists():
        shutil.copy("assets/icon.ico", "dist/")
    print("  OK")
    print()

    # Success
    print("=" * 50)
    print("BUILD SUCCESS!")
    print()
    print("Output files:")
    print(f"  - dist/TikTokPublisherWeb.exe")
    print(f"  - dist/web/ (web resources)")
    print()
    print("To create installer:")
    print("  Run installer/install_simple.bat (as Admin)")
    print("=" * 50)

    # Open dist folder
    try:
        os.startfile("dist")
    except:
        pass

    return 0

if __name__ == "__main__":
    sys.exit(main())
