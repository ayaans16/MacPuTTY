# Contributing to MacPuTTY

Thanks for your interest in contributing! MacPuTTY is a small Electron + Flask app, so contributions generally touch one of two layers: the Python backend (core/) or the Electron UI (ui/).

## Project layout

- `core/` — Flask backend
  - `app.py` — Flask routes
  - `key_pair_gen.py` — RSA/ECDSA/ED25519 key generation
  - `load_existing_key.py` — parsing uploaded private keys
  - `comment.py` — editing a public key's comment
  - `ssh_config_visualizer.py` — parses ~/.ssh/config for the Key Usage tab
  - `paths.py` — resolves bundled resources (config.conf, ssh/) in dev vs. packaged builds
- `ui/` — Electron app (index.html, renderer.js, main.js, preload.js, styles.css)
- `ssh/` — standalone SSH connection-test script, dynamically loaded by core/app.py
- `scripts/` — build tooling (PyInstaller backend build for the .dmg)
- `docs/` — project notebook/guide
- `config.conf` — HOCON config: where keys live (directory.path) and RSA bit size (key_size.rsa)

## Development setup

The backend runs in Docker; the UI runs natively via Electron.
```bash
    make build   # docker compose up --build -d, then cd ui && npm install && npm start
    make health  # sanity-check the backend container is up and healthy
```
The Electron UI talks to the backend over HTTP at `http://localhost:5050` (hardcoded in ui/renderer.js). If you change backend routes, the UI is the only consumer to update.

## Building the standalone .dmg
```bash
    make dist   # builds the PyInstaller backend, then runs electron-builder
```
This produces dist/MacPuTTY-<version>-arm64.dmg. Note config.conf is bundled as a read-only default in this build — it's not live-editable like the Docker-mounted version, so changes to config.conf require rebuilding.

## Making changes

- Backend changes: add routes in core/app.py, keep business logic in a separate flat module (following the existing `key_pair_gen.py` / `comment.py` / `ssh_config_visualizer.py` pattern) rather than piling logic into `app.py` directly.
- UI changes: follow the existing tab pattern (Key Generator / Test Connection / Key Usage) — each tab is a `<main class="window">` block toggled via the shared tab-switch logic in `renderer.js`.
- Never write directly to a user's real `~/.ssh` during testing; use a scratch directory and point `config.conf`'s directory.path at it.
- Keep Docker (`docker-compose.yml`, `Dockerfile`) and the .dmg packaging path (scripts/build-backend.sh, ui/main.js's spawn logic) both working — they're two independent ways to run the same backend, and a change to one shouldn't silently break the other.

## Pull requests

- Keep PRs focused — one feature or fix at a time.
- Test both distribution paths if you touch `core/` or `ui/main.js`: `make build` (Docker/dev) and, if relevant, `make dist` (packaged .dmg).
- Update README.md's roadmap/feature list if you add or change user-facing functionality.

## License

By contributing, you agree your contributions will be licensed under this project's GPLv3 license (see LICENSE.md).
