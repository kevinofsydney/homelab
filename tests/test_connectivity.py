"""Probe behavior without opening network sockets."""
import importlib.util
from pathlib import Path
import ssl
import unittest
from unittest.mock import MagicMock, patch

spec = importlib.util.spec_from_file_location(
    "connectivity", Path(__file__).resolve().parents[1] / "scripts/check-connectivity.py"
)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


class ConnectivityTests(unittest.TestCase):
    def test_tcp_success_closes_connection(self):
        with patch.object(probe.socket, "create_connection") as connect:
            self.assertEqual(probe.tcp_probe("host", 8006, 2)["status"], "reachable")
            connect.assert_called_once_with(("host", 8006), timeout=2)
            connect.return_value.__exit__.assert_called_once()

    def test_tcp_failure_is_not_success(self):
        with patch.object(probe.socket, "create_connection", side_effect=TimeoutError):
            self.assertEqual(probe.tcp_probe("host", 8006, 2)["status"], "failed")

    def test_tls_rejects_untrusted_certificate(self):
        context = MagicMock()
        context.wrap_socket.side_effect = ssl.SSLCertVerificationError("untrusted")
        with patch.object(probe.ssl, "create_default_context", return_value=context), patch.object(
            probe.socket, "create_connection"
        ):
            self.assertEqual(probe.tls_probe("host", 8006, 2)["status"], "failed")
            context.wrap_socket.assert_called_once()

    def test_tls_uses_trusted_ca_and_hostname(self):
        with patch.object(probe.ssl, "create_default_context") as create, patch.object(
            probe.socket, "create_connection"
        ):
            self.assertEqual(probe.tls_probe("host", 8006, 2, "ca.pem")["status"], "verified")
            create.assert_called_once_with(cafile="ca.pem")
            self.assertEqual(create.return_value.wrap_socket.call_args.kwargs["server_hostname"], "host")
