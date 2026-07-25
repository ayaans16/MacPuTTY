# Security Policy

## Overview
MacPuTTY generates SSH key pairs and can test SSH connections using a private key you provide. Private key material is only ever processed locally:
- The Flask backend runs on `localhost` only (no external network exposure by default).
- Uploaded/generated private keys are written to short-lived temp files, chmod'd to `0600`, and deleted immediately after use.
- No key material, credentials, or connection details are logged, transmitted to third parties, or persisted beyond what you explicitly save to disk.

## Supported Versions
Only the latest commit on `main` is supported. Please update before reporting an issue.

## Reporting a Vulnerability
If you discover a security issue (e.g. key material leakage, path traversal, injection via the Flask API):
1. Do **not** open a public GitHub issue.
2. Email the maintainer directly with a description and reproduction steps.
3. Allow reasonable time for a fix before public disclosure.

## Best Practices for Users
- Only run the bundled Flask backend on `localhost` — do not expose port `5050`/`5000` to the network.
- Treat any private key you load or generate as sensitive; MacPuTTY does not encrypt keys at rest.
- Review `docker-compose.yml` before deploying anywhere beyond your local machine.
- Keep dependencies (`requirements.txt`, `ui/package.json`) up to date to pick up upstream security patches (e.g. `paramiko`, `cryptography`, `electron`).