"""Read-only checks for the portable AI CLI installer."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/install-ai-cli.sh'


@unittest.skipUnless(shutil.which('node'), 'Node.js is needed for the read-only check')
class InstallerCheckTests(unittest.TestCase):
    def fixture(self, root):
        home = Path(root)
        bindir = home / 'mock-bin'
        bindir.mkdir()
        identity = bindir / 'id'
        identity.write_text('#!/bin/sh\necho coder\n')
        identity.chmod(0o755)
        tools = home / '.local/ai-tools'
        node = tools / 'node/bin/node'
        node.parent.mkdir(parents=True)
        node.symlink_to(shutil.which('node'))
        version = subprocess.check_output([str(node), '--version'], text=True).strip().removeprefix('v')
        for name, pkg_version in [('@openai/codex', '0.164.0'), ('@opencode/cli', '2.1.4'), ('@deepseek-ai/dsh', '0.2.1-rc.2')]:
            path = tools / 'npm/node_modules' / name
            path.mkdir(parents=True)
            (path / 'package.json').write_text(json.dumps({'version': pkg_version}))
        binaries = tools / 'npm/node_modules/.bin'
        binaries.mkdir()
        for name in ('codex', 'opencode', 'dsh'):
            item = binaries / name
            item.write_text('#!/bin/sh\nexit 0\n')
            item.chmod(0o755)
        env = dict(os.environ, HOME=str(home), PATH=str(bindir) + os.pathsep + os.environ['PATH'],
                   NODE_TARBALL_URL=f'https://nodejs.org/dist/v{version}/node-v{version}-linux-x64.tar.xz',
                   NODE_SHA256='0' * 64, CODEX_VERSION='0.164.0', OPENCODE_VERSION='2.1.4',
                   DSH_VERSION='0.2.1-rc.2', DSH_SHA512='0' * 128)
        return tools, env

    def test_matching_install_is_read_only(self):
        with tempfile.TemporaryDirectory() as directory:
            tools, env = self.fixture(directory)
            before = sorted(str(p.relative_to(tools)) for p in tools.rglob('*'))
            result = subprocess.run(['bash', str(SCRIPT), '--check'], env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('no changes made', result.stdout)
            self.assertEqual(before, sorted(str(p.relative_to(tools)) for p in tools.rglob('*')))

    def test_incorrect_or_missing_dsh_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            tools, env = self.fixture(directory)
            package = tools / 'npm/node_modules/@deepseek-ai/dsh/package.json'
            package.write_text('{"version":"0.0.0"}')
            result = subprocess.run(['bash', str(SCRIPT), '--check'], env=env, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            package.unlink()
            result = subprocess.run(['bash', str(SCRIPT), '--check'], env=env, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)

    def test_invalid_digest_is_rejected_before_download(self):
        with tempfile.TemporaryDirectory() as directory:
            _, env = self.fixture(directory)
            env['DSH_SHA512'] = 'bad'
            result = subprocess.run(['bash', str(SCRIPT)], env=env, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('Invalid DeepSeek Harness SHA512', result.stderr)
            self.assertFalse((Path(directory) / '.local/ai-tools/download').exists())


if __name__ == '__main__':
    unittest.main()
