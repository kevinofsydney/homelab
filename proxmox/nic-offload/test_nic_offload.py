import configparser
import importlib.util
import json
import pathlib
import subprocess
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('nic_offload', 'homelab-nic-offload.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

ALL_ON = {'tso': 'on', 'gso': 'on', 'gro': 'on'}
ALL_OFF = {'tso': 'off', 'gso': 'off', 'gro': 'off'}
ETHTOOL_K = """Features for nic0:
tcp-segmentation-offload: on
\ttx-tcp-segmentation: on
generic-segmentation-offload: off
generic-receive-offload: on [fixed]
"""


def unit(name):
    parser = configparser.ConfigParser(strict=False, interpolation=None)
    parser.optionxform = str
    parser.read(name)
    return parser


class Tests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        patcher = patch.object(m, 'BASELINE', pathlib.Path(directory.name) / 'state' / 'baseline.json')
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_current_settings_parses_feature_values(self):
        with patch.object(m.subprocess, 'check_output', return_value=ETHTOOL_K):
            self.assertEqual(m.current_settings(), {'tso': 'on', 'gso': 'off', 'gro': 'on'})

    def test_current_settings_rejects_a_missing_feature(self):
        with patch.object(m.subprocess, 'check_output', return_value='tcp-segmentation-offload: on\n'):
            with self.assertRaises(RuntimeError):
                m.current_settings()

    def test_wrong_driver_changes_nothing(self):
        with patch.object(m.subprocess, 'check_output', return_value='driver: igc\n'), patch.object(m, 'run') as run:
            with self.assertRaises(RuntimeError):
                m.arm()
            run.assert_not_called()
        self.assertFalse(m.BASELINE.exists())

    def test_arm_records_baseline_and_checks_rollback_before_the_candidate(self):
        calls = []
        with patch.object(m, 'require_expected_nic'), patch.object(m, 'current_settings', return_value=ALL_ON), patch.object(m, 'run', side_effect=lambda *a: calls.append(a)), patch.object(m, 'succeeds', side_effect=lambda *a: calls.append(a) or True):
            m.arm()
        self.assertEqual(json.loads(m.BASELINE.read_text()), ALL_ON)
        timer = calls.index(('systemctl', 'enable', '--now', m.ROLLBACK_TIMER))
        enabled = calls.index(('systemctl', 'is-enabled', '--quiet', m.ROLLBACK_TIMER))
        candidate = calls.index(('systemctl', 'enable', m.SERVICE))
        self.assertLess(timer, enabled)
        self.assertLess(enabled, candidate)

    def test_arm_stops_when_rollback_timer_is_not_active(self):
        with patch.object(m, 'require_expected_nic'), patch.object(m, 'current_settings', return_value=ALL_ON), patch.object(m, 'run') as run, patch.object(m, 'succeeds', return_value=False):
            with self.assertRaises(RuntimeError):
                m.arm()
        self.assertNotIn(unittest.mock.call('systemctl', 'enable', m.SERVICE), run.call_args_list)

    def test_repeated_arm_keeps_the_first_baseline(self):
        m.BASELINE.parent.mkdir(parents=True)
        m.BASELINE.write_text(json.dumps(ALL_ON))
        with patch.object(m, 'current_settings', return_value=ALL_OFF):
            m.record_baseline()
        self.assertEqual(json.loads(m.BASELINE.read_text()), ALL_ON)

    def test_rollback_restores_the_recorded_baseline_not_a_fixed_value(self):
        m.BASELINE.parent.mkdir(parents=True)
        m.BASELINE.write_text(json.dumps({'tso': 'off', 'gso': 'on', 'gro': 'on'}))
        with patch.object(m, 'require_expected_nic'), patch.object(m, 'current_settings', return_value=ALL_ON), patch.object(m, 'run') as run:
            self.assertEqual(m.rollback(), 0)
        run.assert_any_call('ethtool', '-K', 'nic0', 'tso', 'off', 'gso', 'on', 'gro', 'on')
        run.assert_any_call('systemctl', 'disable', m.SERVICE)
        self.assertFalse(m.BASELINE.exists())

    def test_failed_restore_still_disables_candidate_and_keeps_baseline(self):
        m.BASELINE.parent.mkdir(parents=True)
        m.BASELINE.write_text(json.dumps(ALL_ON))

        def fail_ethtool(*args):
            if args[0] == 'ethtool':
                raise subprocess.CalledProcessError(1, args)

        with patch.object(m, 'require_expected_nic'), patch.object(m, 'run', side_effect=fail_ethtool) as run:
            self.assertEqual(m.rollback(), 1)
        run.assert_any_call('systemctl', 'disable', m.SERVICE)
        run.assert_any_call('systemctl', 'disable', '--now', m.ROLLBACK_TIMER)
        self.assertTrue(m.BASELINE.exists())

    def test_ack_refuses_to_cancel_rollback_when_candidate_is_not_applied(self):
        with patch.object(m, 'current_settings', return_value=ALL_ON), patch.object(m, 'succeeds', return_value=True), patch.object(m, 'run') as run:
            with self.assertRaises(RuntimeError):
                m.acknowledge()
            run.assert_not_called()

    def test_ack_cancels_only_the_rollback(self):
        with patch.object(m, 'current_settings', return_value=ALL_OFF), patch.object(m, 'succeeds', return_value=True), patch.object(m, 'run') as run:
            m.acknowledge()
        run.assert_called_once_with('systemctl', 'disable', '--now', m.ROLLBACK_TIMER)

    def test_check_changes_nothing(self):
        with patch.object(m, 'require_expected_nic'), patch.object(m, 'current_settings', return_value=ALL_ON), patch.object(m, 'succeeds', return_value=False), patch.object(m, 'run') as run:
            self.assertEqual(m.check(), 0)
            run.assert_not_called()

    def test_rollback_timer_survives_reboot(self):
        timer = unit('homelab-nic-offload-rollback.timer')
        self.assertEqual(timer['Install']['WantedBy'], 'timers.target')
        self.assertIn('OnActiveSec', timer['Timer'])
        # OnBootSec would fire at once when armed on a host that has been up longer than the delay.
        self.assertNotIn('OnBootSec', timer['Timer'])

    def test_candidate_runs_before_networking_and_after_the_device(self):
        service = unit('homelab-nic-offload.service')['Unit']
        self.assertIn('networking.service', service['Before'])
        self.assertIn('sys-subsystem-net-devices-nic0.device', service['After'])


if __name__ == '__main__':
    unittest.main()
