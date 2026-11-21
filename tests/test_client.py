import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import requests

from geoseeer import APIError, GeoSeer, GeoSeerError


def response(body, *, status=200, content_type="application/json"):
    result = requests.Response()
    result.status_code = status
    result.headers["Content-Type"] = content_type
    result.raw = io.BytesIO(body)
    return result


class GeoSeerTests(unittest.TestCase):
    def setUp(self):
        environment = patch.dict(os.environ, {"GEOSEER_API_KEY": "test-key"}, clear=True)
        environment.start()
        self.addCleanup(environment.stop)
        sender = patch.object(requests.Session, "send")
        self.send = sender.start()
        self.addCleanup(sender.stop)
        self.send.return_value = response(b'{"status":"success","locations":[]}')
        self.client = GeoSeer()

    def test_single_url_uses_hosted_api_and_environment_key(self):
        result = self.client.analyze(urls="https://example.com/photo.jpg", context="A coast")
        request = self.send.call_args.args[0]
        self.assertEqual(request.method, "POST")
        self.assertEqual(request.url, "https://geoseeer.com/api/v1/analyze")
        self.assertEqual(request.headers["X-API-Key"], "test-key")
        self.assertFalse(self.send.call_args.kwargs["allow_redirects"])
        self.assertEqual(json.loads(request.body), {
            "analysis_mode": "fast",
            "stream": False,
            "url": "https://example.com/photo.jpg",
            "user_context": "A coast",
        })
        self.assertEqual(result, {"status": "success", "locations": []})

    def test_event_uses_json_without_media_fields(self):
        client = GeoSeer("explicit-key", base_url="https://example.com/api/v1/")
        client.analyze(event_text="An event at Lusail Stadium")
        request = self.send.call_args.args[0]
        self.assertEqual(request.url, "https://example.com/api/v1/analyze")
        self.assertEqual(request.headers["X-API-Key"], "explicit-key")
        self.assertEqual(json.loads(request.body), {
            "analysis_mode": "event",
            "stream": False,
            "event_text": "An event at Lusail Stadium",
        })

    def test_multiple_uploads_repeat_files_field(self):
        with tempfile.TemporaryDirectory() as folder:
            front = Path(folder) / "front.jpg"
            side = Path(folder) / "side.png"
            front.write_bytes(b"front image bytes")
            side.write_bytes(b"side image bytes")
            self.client.analyze(files=[front, str(side)], mode="agent")
        request = self.send.call_args.args[0]
        self.assertTrue(request.headers["Content-Type"].startswith("multipart/form-data;"))
        self.assertEqual(request.body.count(b'name="files"'), 2)
        self.assertIn(b'filename="front.jpg"', request.body)
        self.assertIn(b"front image bytes", request.body)
        self.assertIn(b'filename="side.png"', request.body)
        self.assertIn(b"side image bytes", request.body)
        self.assertIn(b'name="stream"\r\n\r\nfalse\r\n', request.body)

    def test_invalid_input_does_not_send_a_request(self):
        for arguments in (
            {},
            {"urls": []},
            {"files": ["a"] * 4},
            {"urls": "u", "files": "f"},
            {"event_text": "e", "mode": "fast"},
        ):
            with self.subTest(arguments=arguments), self.assertRaises(ValueError):
                self.client.analyze(**arguments)
        self.send.assert_not_called()

    def test_json_http_error_preserves_details_and_retry_header(self):
        self.send.return_value = response(
            b'{"error":{"code":"rate_limited","message":"Slow down","details":{"retry_after_seconds":3}}}',
            status=429,
        )
        self.send.return_value.headers["Retry-After"] = "3"
        with self.assertRaisesRegex(APIError, "Slow down") as exc:
            self.client.analyze(urls="https://example.com/photo.jpg")
        self.assertEqual(exc.exception.status_code, 429)
        self.assertEqual(exc.exception.code, "rate_limited")
        self.assertEqual(exc.exception.details, {"retry_after_seconds": 3})
        self.assertEqual(exc.exception.retry_after, "3")
        self.send.assert_called_once()

    def test_stream_handles_keepalives_and_multiline_events(self):
        first_data_line = b'data: {"type":"progress",\r'
        # Put the first data line's CR and LF in separate read chunks.
        comment = b":" + b" " * (509 - len(first_data_line)) + b"\r\n"
        self.assertEqual(len(comment + first_data_line), 512)
        self.send.return_value = response(
            comment + first_data_line + '\ndata: "message":"Zürich"}\r\n\r\nevent: completed\n'
            'data: {"type":"complete","result":{"locations":[]}}\n\n'.encode(),
            content_type="text/event-stream; charset=utf-8",
        )
        with self.client.stream(urls=["https://example.com/a.jpg", "https://example.com/b.jpg"]) as events:
            self.assertEqual(list(events), [
                {"type": "progress", "message": "Zürich"},
                {"type": "complete", "result": {"locations": []}},
            ])
        request = self.send.call_args.args[0]
        self.assertTrue(self.send.call_args.kwargs["stream"])
        self.assertEqual(json.loads(request.body), {
            "analysis_mode": "fast",
            "stream": True,
            "urls": ["https://example.com/a.jpg", "https://example.com/b.jpg"],
        })
        self.assertTrue(self.send.return_value.raw.closed)

    def test_stream_reports_premature_end(self):
        self.send.return_value = response(b'data: {"type":"progress"}\n\n', content_type="text/event-stream")
        with patch.object(self.send.return_value, "close", wraps=self.send.return_value.close) as close:
            with self.client.stream(event_text="An event") as events:
                self.assertEqual(next(events), {"type": "progress"})
                with self.assertRaisesRegex(GeoSeerError, "before a terminal event"):
                    next(events)
        close.assert_called_once()

    def test_stream_exposes_terminal_api_error(self):
        event = {"type": "error", "error_code": "invalid_request", "message": "Analysis failed"}
        self.send.return_value = response(
            f"data: {json.dumps(event)}\n\n".encode(), content_type="text/event-stream",
        )
        with self.client.stream(event_text="An event") as events:
            self.assertEqual(list(events), [event])
