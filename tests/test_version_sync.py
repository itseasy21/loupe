from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import version_sync


@pytest.fixture(autouse=True)
def restore_paths() -> None:
    original_paths = (
        version_sync.REPO_ROOT,
        version_sync.PACKAGE_JSON,
        version_sync.PYPROJECT,
        version_sync.INIT_FILE,
        version_sync.SERVER_FILE,
    )
    try:
        yield
    finally:
        (
            version_sync.REPO_ROOT,
            version_sync.PACKAGE_JSON,
            version_sync.PYPROJECT,
            version_sync.INIT_FILE,
            version_sync.SERVER_FILE,
        ) = original_paths


@pytest.fixture
def repo_copy(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()

    (repo / "scripts").mkdir()
    (repo / "loupe" / "api").mkdir(parents=True)

    (repo / "package.json").write_text(
        json.dumps(
            {
                "name": "loupe-agent",
                "private": True,
                "version": "0.1.0",
            }
        ),
        encoding="utf-8",
    )
    (repo / "pyproject.toml").write_text(
        "[project]\nname = \"loupe-agent\"\nversion = \"0.0.1\"\n",
        encoding="utf-8",
    )
    (repo / "loupe" / "__init__.py").write_text(
        '__version__ = "0.0.1"\n',
        encoding="utf-8",
    )
    (repo / "loupe" / "api" / "server.py").write_text(
        'app = FastAPI(title="Loupe API", version=__version__)\n',
        encoding="utf-8",
    )

    return repo


def configure_paths(repo: Path) -> None:
    version_sync.REPO_ROOT = repo
    version_sync.PACKAGE_JSON = repo / "package.json"
    version_sync.PYPROJECT = repo / "pyproject.toml"
    version_sync.INIT_FILE = repo / "loupe" / "__init__.py"
    version_sync.SERVER_FILE = repo / "loupe" / "api" / "server.py"


def test_sync_updates_python_version_files(repo_copy: Path) -> None:
    configure_paths(repo_copy)

    assert version_sync.sync() == 0
    assert 'version = "0.1.0"' in version_sync.PYPROJECT.read_text(encoding="utf-8")
    assert '__version__ = "0.1.0"' in version_sync.INIT_FILE.read_text(encoding="utf-8")


def test_check_fails_when_python_versions_drift(
    repo_copy: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    configure_paths(repo_copy)

    assert version_sync.check() == 1
    assert "expected 0.1.0" in capsys.readouterr().err


def test_check_passes_when_versions_and_server_metadata_match(repo_copy: Path) -> None:
    configure_paths(repo_copy)
    version_sync.sync()

    assert version_sync.check() == 0


def test_check_tag_rejects_non_matching_tag(
    repo_copy: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    configure_paths(repo_copy)
    version_sync.sync()

    assert version_sync.check_tag("v0.2.0") == 1
    assert "does not match package version 0.1.0" in capsys.readouterr().err


def test_check_fails_when_server_does_not_expose_package_version(
    repo_copy: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    configure_paths(repo_copy)
    version_sync.sync()
    version_sync.SERVER_FILE.write_text(
        'app = FastAPI(title="Loupe API", version="0.1.0")\n',
        encoding="utf-8",
    )

    assert version_sync.check() == 1
    assert "must expose loupe.__version__" in capsys.readouterr().err
