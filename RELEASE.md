Fixes installation with versioned Python interpreter names.

The installer pins its hook to the Python that ran it. On macOS with Homebrew or python.org Python, that interpreter is named like `python3.14`, and beta.5's post-install check rejected it, so installation rolled back. beta.6 accepts `python3` and `python3.<minor>`; all other hook pin checks are unchanged.

To update an existing beta.5 installation, run `safe-yolo update`. Older installations without the `safe-yolo` command should rerun the installer from the README. Native hook review/trust or restart remains necessary.

Verified on Linux with Python 3.12 for Codex, Claude Code, and Cursor, including install, update, and rollback through a versioned interpreter name. macOS, Windows, and other harness installation lifecycles are not yet verified. Safe YOLO is direct-action backpressure, not a sandbox.

Checksums detect corruption; download from this publisher repository over HTTPS. The ZIP manifest records the private development source revision; the public tag records the distribution repository revision.
