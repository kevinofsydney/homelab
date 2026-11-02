import configparser
import importlib.util
import pathlib
import subprocess
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('host_backup', 'homelab-host-config-backup.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class Tests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.mount = pathlib.Path(directory.name) / 'mount'
        patchers = [patch.object(m, 'MOUNT', self.mount), patch.object(m, 'DESTINATION', self.mount / 'host-config')]
        for patcher in patchers:
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_unmounted_destination_stops_without_creating_anything(self):
        with patch.object(m, 'require_mount', side_effect=RuntimeError('not mounted')):
            with self.assertRaises(RuntimeError):
                m.main()
        self.assertFalse(self.mount.exists())

    def test_require_mount_rejects_a_plain_directory(self):
        self.mount.mkdir()
        with patch.object(m.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, stdout='ext4\n')):
            with self.assertRaises(RuntimeError):
                m.require_mount()

    def test_failed_archive_leaves_no_partial_and_prunes_nothing(self):
        self.mount.mkdir()
        with patch.object(m, 'require_mount'), patch.object(m, 'create_archive', side_effect=lambda path: path.write_text('x')), patch.object(m, 'verify_archive', side_effect=RuntimeError('bad')), patch.object(m, 'prune') as prune:
            with self.assertRaises(RuntimeError):
                m.main()
            prune.assert_not_called()
        self.assertEqual(list(m.DESTINATION.iterdir()), [])

    def test_verified_archive_gets_its_final_name(self):
        self.mount.mkdir()
        with patch.object(m, 'require_mount'), patch.object(m, 'create_archive', side_effect=lambda path: path.write_text('x')), patch.object(m, 'verify_archive'):
            self.assertEqual(m.main(), 0)
        names = [path.name for path in m.DESTINATION.iterdir()]
        self.assertEqual(len(names), 1)
        self.assertRegex(names[0], m.ARCHIVE_NAME)

    def test_prune_keeps_newest_and_ignores_other_files(self):
        m.DESTINATION.mkdir(parents=True)
        for day in range(1, 19):
            (m.DESTINATION / f'host-config-2026-01-{day:02d}T023000.tar.gz').write_text('x')
        (m.DESTINATION / 'notes.txt').write_text('keep')
        m.prune()
        remaining = sorted(path.name for path in m.DESTINATION.iterdir())
        self.assertEqual(len(remaining), m.KEEP + 1)
        self.assertIn('notes.txt', remaining)
        self.assertNotIn('host-config-2026-01-03T023000.tar.gz', remaining)
        self.assertIn('host-config-2026-01-04T023000.tar.gz', remaining)

    def test_archive_names_the_separate_cluster_filesystem(self):
        self.assertIn('etc/pve', m.PATHS)

    def test_timer_matches_the_vm_backup_schedule(self):
        parser = configparser.ConfigParser(strict=False, interpolation=None)
        parser.optionxform = str
        parser.read('homelab-host-config-backup.timer')
        self.assertEqual(parser['Timer']['OnCalendar'], '*-*-1/3 02:30')


if __name__ == '__main__':
    unittest.main()
