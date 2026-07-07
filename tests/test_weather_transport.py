import unittest
from unittest.mock import Mock, patch

from weather.transport import HttpTransport, NWSApiError


class TransportErrorTests(unittest.TestCase):
    @patch("weather.transport.requests.Session.get")
    def test_problem_json_raises_api_error(self, mock_get):
        response = Mock()
        response.status_code = 403
        response.text = "Forbidden"
        response.json.return_value = {
            "type": "about:blank",
            "title": "Forbidden",
            "status": 403,
            "detail": "Missing User-Agent",
            "correlationId": "abc123",
        }
        mock_get.return_value = response

        transport = HttpTransport("TestAgent/1.0", retries=0)
        with self.assertRaises(NWSApiError) as ctx:
            transport.get_json("https://api.weather.gov/points/37.7749,-122.4194")

        self.assertEqual(ctx.exception.status_code, 403)
        self.assertIsNotNone(ctx.exception.problem)
        self.assertEqual(ctx.exception.problem.title, "Forbidden")
        self.assertEqual(ctx.exception.problem.correlation_id, "abc123")

    @patch("weather.transport.requests.Session.get")
    def test_retries_on_server_error_then_succeeds(self, mock_get):
        bad = Mock()
        bad.status_code = 500
        bad.text = "Server Error"
        bad.json.return_value = {
            "title": "Internal Server Error",
            "status": 500,
            "detail": "Temporary failure",
        }

        good = Mock()
        good.status_code = 200
        good.json.return_value = {"ok": True}

        mock_get.side_effect = [bad, good]

        transport = HttpTransport("TestAgent/1.0", retries=1)
        payload = transport.get_json("https://api.weather.gov/test")

        self.assertEqual(payload, {"ok": True})
        self.assertEqual(mock_get.call_count, 2)


if __name__ == "__main__":
    unittest.main()
