"""Publish only when the lightweight release tag matches the reviewed checkout."""

import json
import os
import re
import subprocess

from verify import ROOT, verify


def publish() -> None:
    archive, version = verify()
    repository = os.environ['GH_REPO']
    revision = os.environ['GITHUB_SHA']
    if repository != 'Slaytek-Systems/safe-yolo-releases' or not re.fullmatch('[0-9a-f]{40}', revision):
        raise ValueError('Unexpected publication repository or revision')
    tag = f'v{version}'
    ref = f'refs/tags/{tag}'
    prefix = f'repos/{repository}/git'
    existing = json.loads(subprocess.check_output(['gh', 'api', f'{prefix}/matching-refs/tags/{tag}'], text=True))
    matches = [item for item in existing if item['ref'] == ref]
    if matches:
        if (len(matches) != 1 or matches[0]['object']['type'] != 'commit'
                or matches[0]['object']['sha'] != revision):
            raise ValueError('Existing release tag does not match this reviewed commit')
    else:
        subprocess.run(['gh', 'api', '--method', 'POST', f'{prefix}/refs',
                        '--raw-field', f'ref={ref}', '--raw-field', f'sha={revision}'],
                       check=True, stdout=subprocess.DEVNULL)
    observed = json.loads(subprocess.check_output(['gh', 'api', f'{prefix}/ref/tags/{tag}'], text=True))
    if observed['object']['type'] != 'commit' or observed['object']['sha'] != revision:
        raise ValueError('Release tag changed before publication')
    subprocess.run(['gh', 'release', 'create', tag, str(archive), str(archive.with_suffix('.zip.sha256')),
                    '--verify-tag', '--prerelease', '--title', f'Safe YOLO {tag}',
                    '--notes-file', str(ROOT / 'RELEASE.md')], check=True)
    observed = json.loads(subprocess.check_output(['gh', 'api', f'{prefix}/ref/tags/{tag}'], text=True))
    if observed['object']['type'] != 'commit' or observed['object']['sha'] != revision:
        raise ValueError('Published tag no longer matches the reviewed commit')


if __name__ == '__main__':
    publish()
