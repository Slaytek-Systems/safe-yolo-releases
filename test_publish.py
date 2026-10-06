import json
from pathlib import Path
import unittest
from unittest.mock import patch

from publish import publish

REVISION = 'a' * 40
TAG = 'v3.0.0-beta.5'
REF = {'ref': f'refs/tags/{TAG}', 'object': {'type': 'commit', 'sha': REVISION}}


class PublishTests(unittest.TestCase):
    def setUp(self):
        self.environment = patch.dict('os.environ', {
            'GH_REPO': 'Slaytek-Systems/safe-yolo-releases', 'GITHUB_SHA': REVISION})
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.verification = patch('publish.verify', return_value=(Path('/tmp/release.zip'), TAG[1:]))
        self.verification.start()
        self.addCleanup(self.verification.stop)

    @patch('publish.subprocess.run')
    @patch('publish.subprocess.check_output')
    def test_mismatched_existing_tag_never_publishes(self, read, run):
        other = {**REF, 'object': {'type': 'commit', 'sha': 'b' * 40}}
        read.return_value = json.dumps([other])
        with self.assertRaisesRegex(ValueError, 'does not match'):
            publish()
        run.assert_not_called()

    @patch('publish.subprocess.run')
    @patch('publish.subprocess.check_output')
    def test_new_tag_is_pinned_and_verified_before_release(self, read, run):
        read.side_effect = [json.dumps([]), json.dumps(REF), json.dumps(REF)]
        publish()
        creation, release = [call.args[0] for call in run.call_args_list]
        self.assertIn(f'sha={REVISION}', creation)
        self.assertIn(f'ref=refs/tags/{TAG}', creation)
        self.assertEqual(['gh', 'release', 'create', TAG], release[:4])
        self.assertIn('--verify-tag', release)

    @patch('publish.subprocess.run')
    @patch('publish.subprocess.check_output')
    def test_matching_existing_tag_is_not_overwritten(self, read, run):
        read.side_effect = [json.dumps([REF]), json.dumps(REF), json.dumps(REF)]
        publish()
        self.assertEqual(1, run.call_count)
        self.assertEqual(['gh', 'release', 'create'], run.call_args.args[0][:3])

    @patch('publish.subprocess.run')
    @patch('publish.subprocess.check_output')
    def test_tag_moved_before_publication_stops_release(self, read, run):
        other = {**REF, 'object': {'type': 'commit', 'sha': 'b' * 40}}
        read.side_effect = [json.dumps([REF]), json.dumps(other)]
        with self.assertRaisesRegex(ValueError, 'changed before'):
            publish()
        run.assert_not_called()
