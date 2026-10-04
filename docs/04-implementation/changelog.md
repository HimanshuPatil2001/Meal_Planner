# Changelog

## 2026-10-04 — housekeeping

- Added `.gitignore` covering `__pycache__/`, `*.py[cod]`, `.venv/` and `.env`.
- Removed committed bytecode (`__pycache__/*.pyc`) from version control.

### Why
Compiled artefacts were being tracked, which pollutes diffs and can cause stale-bytecode
bugs. The file stays on disk; it is simply no longer tracked.
