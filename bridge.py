"""Verify the one-time, byte-identical beta.7 migration release."""
import hashlib
from pathlib import Path
import urllib.request

from verify import acceptance

VERSION = '3.0.0-beta.7'
SHA256 = '1a4024b923b1bafc92003c108997fc0ff828ec289e0ac376b8c81e69276a13de'
URL = f'https://github.com/Slaytek-Systems/safe-yolo/releases/download/v{VERSION}/safe-yolo-{VERSION}.zip'


def prepare(directory: Path) -> Path:
    with urllib.request.urlopen(URL, timeout=30) as response:
        payload = response.read(16 * 1024 * 1024 + 1)
    if hashlib.sha256(payload).hexdigest() != SHA256:
        raise ValueError('Bridge differs from the reviewed canonical release')
    directory.mkdir(parents=True, exist_ok=True)
    archive = directory / f'safe-yolo-{VERSION}.zip'
    archive.write_bytes(payload)
    archive.with_suffix('.zip.sha256').write_text(f'{SHA256}  {archive.name}\n')
    acceptance(archive)
    return archive


if __name__ == '__main__':
    print(prepare(Path('/tmp/safe-yolo-final-bridge')))
