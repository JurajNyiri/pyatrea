import unittest
from unittest.mock import Mock, patch

from pyatrea import Atrea


class OneShotCommandTests(unittest.TestCase):
    def setUp(self):
        self.atrea = Atrea("192.0.2.1", code="12345")

    @patch("pyatrea.requests.get")
    def test_executes_without_changing_command_queue(self, request_get):
        request_get.return_value = Mock(status_code=200, text="OK")
        self.atrea.commands["H10708"] = "00020"

        self.assertTrue(self.atrea.executeOneShotCommand("C12345", 1))

        url = request_get.call_args.args[0]
        self.assertIn("/config/xml.cgi?auth=12345&", url)
        self.assertTrue(url.endswith("&C1234500001"))
        self.assertEqual({"H10708": "00020"}, self.atrea.commands)

    @patch("pyatrea.requests.get")
    def test_reauthenticates_and_retries_once(self, request_get):
        request_get.side_effect = [
            Mock(status_code=200, text="HTTP: 403 Forbidden"),
            Mock(status_code=200, content=b"<root>54321</root>"),
            Mock(status_code=200, text="OK"),
        ]

        self.assertTrue(self.atrea.executeOneShotCommand("C54321"))

        self.assertEqual("54321", self.atrea.code)
        self.assertEqual(3, request_get.call_count)
        retry_url = request_get.call_args.args[0]
        self.assertIn("auth=54321", retry_url)
        self.assertTrue(retry_url.endswith("&C5432100001"))

    @patch("pyatrea.requests.get")
    def test_returns_false_when_retry_is_rejected(self, request_get):
        request_get.side_effect = [
            Mock(status_code=200, text="HTTP: 403 Forbidden"),
            Mock(status_code=200, content=b"<root>54321</root>"),
            Mock(status_code=200, text="HTTP: 403 Forbidden"),
        ]

        self.assertFalse(self.atrea.executeOneShotCommand("C54321"))

    def test_rejects_invalid_registers_and_values(self):
        for register, value in (
            ("C1234", 1),
            ("C123456", 1),
            ("C12&45", 1),
            ("C12345", -1),
            ("C12345", 65536),
            ("C12345", "1"),
        ):
            with self.subTest(register=register, value=value):
                self.assertFalse(
                    self.atrea.executeOneShotCommand(register, value)
                )


if __name__ == "__main__":
    unittest.main()
