"""Verify the committed release and exercise installation before publication."""

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parent


def verify() -> tuple[Path, str]:
    metadata = json.loads((ROOT / 'release.json').read_text())
    version = metadata['version']
    if not re.fullmatch(r'3\.[0-9]+\.[0-9]+(?:-[A-Za-z0-9.]+)?', version):
        raise ValueError('Invalid release version')
    if not re.fullmatch('[0-9a-f]{40}', metadata['source_commit']):
        raise ValueError('Invalid source revision')
    archive = ROOT / 'dist' / f'safe-yolo-{version}.zip'
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    if digest != metadata['sha256']:
        raise ValueError('ZIP does not match the reviewed release metadata')
    if archive.with_suffix('.zip.sha256').read_text() != f'{digest}  {archive.name}\n':
        raise ValueError('Checksum sidecar mismatch')
    with zipfile.ZipFile(archive) as bundle:
        entries = bundle.infolist()
        if len(entries) > 1000 or sum(item.file_size for item in entries) > 16 * 1024 * 1024:
            raise ValueError('Archive limits exceeded')
        names = set()
        payload = {}
        for entry in entries:
            path = PurePosixPath(entry.filename)
            if (path.is_absolute() or '..' in path.parts or '\\' in entry.filename
                    or len(path.parts) < 2 or path.parts[0] != f'safe-yolo-{version}'
                    or entry.filename in names or stat.S_ISLNK(entry.external_attr >> 16)):
                raise ValueError('Unsafe archive entry')
            names.add(entry.filename)
            payload[str(PurePosixPath(*path.parts[1:]))] = bundle.read(entry)
        manifest = json.loads(payload.pop('distribution.json'))
        if (manifest['schema_version'] != 1 or manifest['version'] != version
                or manifest['source_commit'] != metadata['source_commit']):
            raise ValueError('Source provenance mismatch')
        if {name: hashlib.sha256(data).hexdigest() for name, data in payload.items()} != manifest['files']:
            raise ValueError('Payload verification failed')
        if payload['VERSION'].decode().strip() != version:
            raise ValueError('Runtime version mismatch')
        if payload['scripts/download.py'] != (ROOT / 'install.py').read_bytes():
            raise ValueError('Public installer differs from the reviewed release')
        if payload['DISTRIBUTION-LICENSE.txt'] != (ROOT / 'LICENSE.txt').read_bytes():
            raise ValueError('Distribution permission mismatch')
    return archive, version


def acceptance(archive: Path) -> None:
    with tempfile.TemporaryDirectory(prefix='safe-yolo-publish-check-') as temporary:
        root = Path(temporary)
        with zipfile.ZipFile(archive) as bundle:
            bundle.extractall(root / 'extracted')
        source = next((root / 'extracted').iterdir())
        user = root / 'user'
        for directory in ('.codex', '.claude', '.cursor'):
            (user / directory).mkdir(parents=True)
        (user / '.codex/config.toml').write_text(
            'approval_policy = "never"\nsandbox_mode = "danger-full-access"\n[features]\nhooks = true\n')
        (user / '.claude/settings.json').write_text('{"theme": "dark"}\n')
        environment = {key: value for key, value in os.environ.items()
                       if key not in {'CODEX_HOME', 'CLAUDE_CONFIG_DIR', 'PYTHONPATH'}}
        def run(args):
            result = subprocess.run(args, cwd=root, env=environment, capture_output=True, text=True, check=True)
            return json.loads(result.stdout)
        result = run([sys.executable, str(source / 'safe-yolo'), '--home', str(user / '.safe-yolo'),
                      '--user-home', str(user), 'install'])
        if {item['harness'] for item in result['reports']} != {'codex', 'claude-code', 'cursor'}:
            raise ValueError('Expected three installed harnesses')
        source.rename(root / 'moved-download')
        launcher = str(user / '.local/bin/safe-yolo')
        if not run([launcher, 'doctor'])['healthy']:
            raise ValueError('Global doctor failed')
        run([launcher, 'update', '--source', str(root / 'moved-download')])
        run([launcher, 'uninstall'])
        if (user / '.codex/hooks.json').exists() or (user / '.cursor/hooks.json').exists():
            raise ValueError('Uninstall left an active integration')
        if (user / '.claude/settings.json').read_text() != '{"theme": "dark"}\n':
            raise ValueError('Uninstall changed unrelated settings')


if __name__ == '__main__':
    archive, version = verify()
    acceptance(archive)
    print(f'PROVEN: {version} archive integrity, three-harness install, global doctor, same-version update, uninstall')
