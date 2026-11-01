import importlib.util
import io
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('maintenance', 'proxmox-auto-update.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class Tests(unittest.TestCase):
    def test_guests_idle_requires_success_from_every_running_guest(self):
        inventory = '[{"vmid":100,"status":"running"},{"vmid":101,"status":"stopped"}]'
        with patch.object(m.subprocess, 'check_output', side_effect=[inventory, '{"exited":1,"exitcode":0}']) as cmd:
            self.assertTrue(m.guests_idle())
            self.assertEqual(cmd.call_count, 2)
        with patch.object(m.subprocess, 'check_output', side_effect=[inventory, '{"exited":1,"exitcode":1}']):
            self.assertFalse(m.guests_idle())
        with patch.object(m.subprocess, 'check_output', side_effect=[inventory, '{"exited":0}']):
            self.assertFalse(m.guests_idle())

    def test_outside_window_stops_before_package_commands(self):
        with patch.object(m.os, 'geteuid', return_value=0), patch.object(m, 'in_window', return_value=False), patch.object(m, 'run') as run:
            with self.assertRaises(RuntimeError):
                m.main()
            run.assert_not_called()

    def test_backup_lock_contention_stops_before_package_commands(self):
        with patch.object(m.os, 'geteuid', return_value=0), patch.object(m, 'in_window', return_value=True), patch('builtins.open', return_value=io.StringIO()), patch.object(m.fcntl, 'flock', side_effect=BlockingIOError), patch.object(m, 'run') as run:
            with self.assertRaises(BlockingIOError):
                m.main()
            run.assert_not_called()

if __name__ == '__main__':
    unittest.main()
