# Contributing to Loupe

Thanks for helping build Loupe. The project is Python-first, local-first, and optimized for a five-minute time to first trace.

## Development Setup

```bash
python -m pip install -e '.[dev]'
python -m pytest
```

## Quality Bar

Run these before opening a pull request:

```bash
python -m ruff check .
python -m mypy loupe
python -m pytest
python scripts/version_sync.py check
```

## Release Process

Loupe uses Changesets to drive version bumps, changelog updates, Git tags, GitHub Releases, and PyPI publishing for `loupe-agent`.

- Add a changeset for user-facing code changes with `npx changeset`.
- Choose the appropriate semver bump and write the release note that should appear in the changelog.
- Skip changesets for docs-only or purely internal changes that should not produce a release.
- When changesets land on `main`, GitHub opens or updates a version PR.
- Merging the version PR creates the `vX.Y.Z` GitHub Release and then calls the PyPI publish workflow for that tag.

If you change versioned metadata manually, run `python scripts/version_sync.py check` before opening the PR.

Core debugging features must stay free and local-first: recording, replay, causal tracing, CLI workflows, and local storage.
