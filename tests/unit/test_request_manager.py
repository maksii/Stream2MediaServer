import unittest
from unittest.mock import patch

from curl_cffi.requests.exceptions import HTTPError

from stream2mediaserver.config import config
from stream2mediaserver.processors.request_manager import RequestManager


class FakeResponse:
    def __init__(self, status_code=200, headers=None):
        self.status_code = status_code
        self.headers = headers or {}
        self.ok = status_code < 400
        self.content = b""
        self.url = "https://example.test"

    def raise_for_status(self):
        if not self.ok:
            raise HTTPError(f"{self.status_code} error")


class RequestManagerRetryTests(unittest.TestCase):
    def setUp(self):
        # Throttling would make these tests sleep for real seconds.
        self._delay = config.provider_config.request_delay_seconds
        self._retries = config.provider_config.max_retries
        config.provider_config.request_delay_seconds = 0

    def tearDown(self):
        config.provider_config.request_delay_seconds = self._delay
        config.provider_config.max_retries = self._retries

    def _run(self, responses):
        """Drive RequestManager.get over a scripted list of responses/exceptions."""
        calls = []
        waits = []

        def fake_request(method, url, **kwargs):
            calls.append(kwargs.get("headers", {}))
            result = responses[len(calls) - 1]
            if isinstance(result, Exception):
                raise result
            return result

        with patch.object(RequestManager._session, "request", fake_request), patch(
            "stream2mediaserver.processors.request_manager.time.sleep", waits.append
        ):
            response = RequestManager.get("https://example.test")
        return response, calls, waits

    def test_retries_429_then_succeeds(self):
        ok = FakeResponse(200)
        response, calls, waits = self._run([FakeResponse(429), ok])
        self.assertIs(response, ok)
        self.assertEqual(len(calls), 2)

    def test_honours_retry_after_header(self):
        _, _, waits = self._run(
            [FakeResponse(429, {"Retry-After": "7"}), FakeResponse(200)]
        )
        self.assertEqual(waits, [7.0])

    def test_retry_wait_is_capped(self):
        _, _, waits = self._run(
            [FakeResponse(503, {"Retry-After": "9999"}), FakeResponse(200)]
        )
        self.assertEqual(waits, [RequestManager.MAX_RETRY_WAIT])

    def test_gives_up_after_max_retries(self):
        config.provider_config.max_retries = 3
        response, calls, _ = self._run([FakeResponse(429)] * 3)
        self.assertIsNone(response)
        self.assertEqual(len(calls), 3)

    def test_sends_browser_user_agent(self):
        _, calls, _ = self._run([FakeResponse(200)])
        self.assertIn("Chrome", calls[0]["User-Agent"])

    def test_does_not_retry_client_errors(self):
        response, calls, _ = self._run([FakeResponse(404)])
        self.assertIsNone(response)
        self.assertEqual(len(calls), 1)


if __name__ == "__main__":
    unittest.main()
