#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PACKAGE_JSON = REPO_ROOT / "package.json"
PYPROJECT = REPO_ROOT / "pyproject.toml"
INIT_FILE = REPO_ROOT / "loupe" / "__init__.py"
SERVER_FILE = REPO_ROOT / "loupe" / "api" / "server.py"
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")
PYPROJECT_VERSION_RE = re.compile(r'^(version = ")([^"]+)(")$', re.MULTILINE)
INIT_VERSION_RE = re.compile(r'^(__version__ = ")([^"]+)(")$', re.MULTILINE)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def root_version() -> str:
    data = json.loads(read_text(PACKAGE_JSON))
    version = data.get("version")
    if not isinstance(version, str) or not SEMVER_RE.match(version):
        raise SystemExit(f"Invalid version in {PACKAGE_JSON}: {version!r}")
    return version


def extract_version(path: Path, pattern: re.Pattern[str]) -> str:
    match = pattern.search(read_text(path))
    if match is None:
        raise SystemExit(f"Could not find version in {path}")
    return match.group(2)


def replace_version(path: Path, pattern: re.Pattern[str], version: str) -> bool:
    content = read_text(path)
    updated, count = pattern.subn(rf"\g<1>{version}\g<3>", content, count=1)
    if count != 1:
        raise SystemExit(f"Could not update version in {path}")
    if updated == content:
        return False
    write_text(path, updated)
    return True


def sync() -> int:
    version = root_version()
    replace_version(PYPROJECT, PYPROJECT_VERSION_RE, version)
    replace_version(INIT_FILE, INIT_VERSION_RE, version)
    print(f"Synchronized version {version}")
    return 0


def check() -> int:
    version = root_version()
    versions = {
        "package.json": version,
        "pyproject.toml": extract_version(PYPROJECT, PYPROJECT_VERSION_RE),
        "loupe/__init__.py": extract_version(INIT_FILE, INIT_VERSION_RE),
    }
    mismatches = {name: value for name, value in versions.items() if value != version}
    if mismatches:
        for name, value in mismatches.items():
            print(f"{name} has {value}, expected {version}", file=sys.stderr)
        return 1

    server_content = read_text(SERVER_FILE)
    if "FastAPI(title=\"Loupe API\", version=__version__)" not in server_content:
        message = f"{SERVER_FILE} must expose loupe.__version__ through FastAPI metadata"
        print(message, file=sys.stderr)
        return 1

    print(f"Version check passed: {version}")
    return 0


def check_tag(tag: str) -> int:
    version = root_version()
    normalized = tag[1:] if tag.startswith("v") else tag
    if normalized != version:
        print(f"Release tag {tag} does not match package version {version}", file=sys.stderr)
        return 1
    return check()


def main() -> int:
    parser = argparse.ArgumentParser(description="Synchronize Loupe release versions.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("sync")
    subparsers.add_parser("check")
    tag_parser = subparsers.add_parser("check-tag")
    tag_parser.add_argument("tag")

    args = parser.parse_args()
    if args.command == "sync":
        return sync()
    if args.command == "check":
        return check()
    return check_tag(args.tag)


if __name__ == "__main__":
    raise SystemExit(main())
