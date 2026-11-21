import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from importlib.metadata import version
from pathlib import Path
from unittest.mock import patch

import requests

from geoseeer.cli import main

from test_client import response


class CLITests(unittest.TestCase):
    def setUp(self):
        environment = patch.dict(os.environ, {"GEOSEER_API_KEY": "test-key"}, clear=True)
        environment.start()
        self.addCleanup(environment.stop)
        sender = patch.object(requests.Session, "send")
        self.send = sender.start()
        self.addCleanup(sender.stop)
        self.send.return_value = response(b'{"status":"success","locations":[]}')

    def run_cli(self, *args):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            try:
                status = main(args)
            except SystemExit as exc:
                status = exc.code
        return status, stdout.getvalue(), stderr.getvalue()

    def test_help_and_version_without_api_key(self):
        del os.environ["GEOSEER_API_KEY"]
        status, stdout, stderr = self.run_cli("--version")
        self.assertEqual((status, stdout, stderr), (0, f"geoseeer {version('geoseeer')}\n", ""))
        status, stdout, stderr = self.run_cli("analyze", "--help")
        self.assertEqual(status, 0)
        self.assertIn("GEOSEER_API_KEY", stdout)
        self.assertEqual(stderr, "")
        self.send.assert_not_called()

    def test_multiple_urls_with_media_options(self):
        os.environ["GEOSEER_BASE_URL"] = "https://example.com/api/v1/"
        urls = ["https://example.com/a.jpg", "https://example.com/b.jpg"]
        status, stdout, stderr = self.run_cli(
            "analyze", "--url", urls[0], "--url", urls[1], "--mode", "agent", "--context", "A coast",
        )
        self.assertEqual(status, 0)
        self.assertEqual(json.loads(stdout), {"status": "success", "locations": []})
        self.assertEqual(stderr, "")
        request = self.send.call_args.args[0]
        self.assertEqual(request.url, "https://example.com/api/v1/analyze")
        self.assertEqual(request.headers["X-API-Key"], "test-key")
        self.assertEqual(json.loads(request.body), {
            "analysis_mode": "agent", "stream": False, "urls": urls, "user_context": "A coast",
        })

    def test_multiple_files_default_to_fast_mode(self):
        with tempfile.TemporaryDirectory() as folder:
            first = Path(folder) / "front view.jpg"
            second = Path(folder) / "side.png"
            first.write_bytes(b"front image bytes")
            second.write_bytes(b"side image bytes")
            status, stdout, stderr = self.run_cli("analyze", "--file", str(first), "--file", str(second))
        self.assertEqual(status, 0)
        self.assertEqual(stderr, "")
        self.assertEqual(json.loads(stdout)["status"], "success")
        body = self.send.call_args.args[0].body
        self.assertEqual(body.count(b'name="files"'), 2)
        self.assertIn(b'filename="front view.jpg"', body)
        self.assertIn(b'filename="side.png"', body)
        self.assertIn(b'name="analysis_mode"\r\n\r\nfast\r\n', body)

    def test_event_stream_prints_ndjson(self):
        events = [
            {"type": "progress", "message": "Searching Zürich"},
            {"type": "complete", "result": {"locations": []}},
        ]
        self.send.return_value = response(
            b"".join(f"data: {json.dumps(event)}\n\n".encode() for event in events),
            content_type="text/event-stream",
        )
        status, stdout, stderr = self.run_cli("analyze", "--event-text", "An event in Zürich", "--stream")
        self.assertEqual(status, 0)
        self.assertEqual([json.loads(line) for line in stdout.splitlines()], events)
        self.assertEqual(stderr, "")
        self.assertEqual(json.loads(self.send.call_args.args[0].body), {
            "analysis_mode": "event", "stream": True, "event_text": "An event in Zürich",
        })
        self.assertTrue(self.send.return_value.raw.closed)

    def test_terminal_stream_errors_remain_in_json_output(self):
        for event_type in ("error", "cancelled"):
            with self.subTest(event_type=event_type):
                event = {"type": event_type, "message": "Analysis failed"}
                self.send.return_value = response(
                    f"data: {json.dumps(event)}\n\n".encode(), content_type="text/event-stream",
                )
                status, stdout, stderr = self.run_cli("analyze", "--url", "https://example.com/a.jpg", "--stream")
                self.assertEqual(status, 1)
                self.assertEqual(json.loads(stdout), event)
                self.assertIn("Analysis failed", stderr)
                self.assertTrue(self.send.return_value.raw.closed)

    def test_usage_errors_do_not_send_a_request(self):
        for args, message in (
            (("analyze",), "required"),
            (("analyze", "--file", "photo.jpg", "--url", "https://example.com/a.jpg"), "not allowed"),
            (("analyze", "--event-text", "e", "--mode", "fast"), "only available"),
            (("analyze", "--event-text", "e", "--context", "extra"), "only available"),
            (("analyze", "--file", "photo.jpg", "--mode", "event"), "invalid choice"),
            (("analyze", *("--url", "https://example.com/a.jpg") * 4), "one to three URLs"),
        ):
            with self.subTest(args=args):
                status, stdout, stderr = self.run_cli(*args)
                self.assertEqual((status, stdout), (2, ""))
                self.assertIn(message, stderr)
        self.send.assert_not_called()

    def test_missing_api_key(self):
        del os.environ["GEOSEER_API_KEY"]
        status, stdout, stderr = self.run_cli("analyze", "--event-text", "An event")
        self.assertEqual((status, stdout), (2, ""))
        self.assertIn("GEOSEER_API_KEY", stderr)
        self.send.assert_not_called()

    def test_file_failure(self):
        with tempfile.TemporaryDirectory() as folder:
            status, stdout, stderr = self.run_cli("analyze", "--file", str(Path(folder) / "missing.jpg"))
        self.assertEqual((status, stdout), (1, ""))
        self.assertIn("missing.jpg", stderr)
        self.send.assert_not_called()

    def test_request_failures(self):
        self.send.return_value = response(b'{"error":{"message":"Slow down"}}', status=429)
        args = ("analyze", "--url", "https://example.com/a.jpg")
        status, stdout, stderr = self.run_cli(*args)
        self.assertEqual((status, stdout), (1, ""))
        self.assertIn("Slow down", stderr)

        self.send.side_effect = requests.ConnectionError("Connection refused")
        status, stdout, stderr = self.run_cli(*args)
        self.assertEqual((status, stdout), (1, ""))
        self.assertIn("Connection refused", stderr)
