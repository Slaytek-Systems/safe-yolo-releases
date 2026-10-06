# Publish a release

The development repository stays private. This public repository contains only
the installer, guide, release verification workflow, and distributable artifacts.

1. Land and validate the development change. From a clean checkout of that exact
   merged commit, run `python3 scripts/package.py --output /path/to/this-repo/dist`.
2. Copy `scripts/download.py` to `install.py`, `docs/download-install.md` to
   `README.md`, and `DISTRIBUTION-LICENSE.txt` to `LICENSE.txt`.
3. Update `release.json` with the version, full development commit SHA, and ZIP
   SHA-256. Update `RELEASE.md` for that version. Keep previous release files.
4. Run `python3 verify.py`. Review and commit the metadata, scripts, guide,
   permission notice, and ZIP/checksum through a feature branch and pull request.
5. After landing on main, run **Publish verified Safe YOLO release** in Actions.
   The workflow checks the committed archive and installs all three supported
   harnesses in an isolated home. Only the dependent publish job receives the
   built-in repository write token. No private-source access token is needed.
6. Verify the anonymous release download, installer, and global `safe-yolo update`
   journey. Record the public release URL and both source/distribution revisions.

The workflow runs only on explicit dispatch. Publication is restricted to main.
It creates a new prerelease and never overwrites an existing tag or asset. If a
release fails verification, correct the candidate before dispatch. A published
release correction gets a new version. Stable-release promotion should be an
explicitly reviewed workflow change; this initial channel installs beta releases.

Rollback for users is `safe-yolo rollback`; retained local customizations remain
in effect. Native hook trust/restart is still the user's harness-specific step.
