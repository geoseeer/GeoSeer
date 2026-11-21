"""Exercise tool discovery and calls over the official MCP stdio transport."""

from importlib.util import find_spec
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest


HAS_MCP = find_spec("mcp") is not None

# Run the real CLI inside a child process with only outbound HTTP replaced.
MOCK_SERVER = r"""
import json
import requests
from unittest.mock import patch
from geoseeer.cli import main

def post(url, *, headers, timeout, allow_redirects, stream, **body):
    assert timeout == (15, 450)
    assert not allow_redirects and not stream
    assert url == "https://geoseeer.com/api/v1/analyze"
    key = headers["X-API-Key"]
    response = requests.Response()
    response.status_code = 200
    if key != "gsk_fixture":
        response.status_code = 401 if key == "gsk_rejected" else 402
        payload = {"error": {"message": key}}
    else:
        if "files" in body:
            assert body["data"] == {"analysis_mode": "fast", "stream": "false"}
            field, (name, stream) = body["files"][0]
            assert (field, name, stream.read()) == ("file", "clue.jpg", b"fixture-media")
        else:
            assert body["json"] == {
                "analysis_mode": "fast", "stream": False,
                "url": "https://example.test/clue.jpg", "user_context": "Coastal city",
            }
        payload = {
            "status": "success", "processing_time": "1s", "API_Requests_remaining": 5,
            "debug": {"provider_token": key},
            "locations": [{"latitude": 1, "longitude": 2, "confidence": 0.7,
                           "confidence_details": {"method": "test", "quality_score": 0.7, "debug": key},
                           "provider_token": key}],
        }
    response._content = json.dumps(payload).encode()
    response._content_consumed = True
    return response

with patch("requests.post", side_effect=post):
    raise SystemExit(main(["mcp"]))
"""


@unittest.skipUnless(HAS_MCP, "Install geoseeer[mcp] to run MCP tests")
class MCPTests(unittest.IsolatedAsyncioTestCase):
    async def call(self, arguments, key="gsk_fixture"):
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        env = {"GEOSEER_API_KEY": key}
        if "PYTHONPATH" in os.environ:
            env["PYTHONPATH"] = os.environ["PYTHONPATH"]
        parameters = StdioServerParameters(
            command=sys.executable, args=["-c", MOCK_SERVER], env=env,
        )
        # stdio_client expects a real file descriptor for subprocess stderr.
        with TemporaryDirectory() as temp:
            with (Path(temp) / "stderr").open("w+") as log:
                async with stdio_client(parameters, errlog=log) as (reader, writer):
                    async with ClientSession(
                        reader, writer, read_timeout_seconds=12,
                    ) as session:
                        await session.initialize()
                        listed = await session.list_tools()
                        self.assertEqual([tool.name for tool in listed.tools], ["geolocate_media"])
                        tool = listed.tools[0]
                        self.assertEqual(set(tool.input_schema["properties"]), {"file", "url", "context"})
                        self.assertIn("consumes", tool.description)
                        reply = await session.call_tool(tool.name, arguments)
                log.seek(0)
                self.assertNotIn("gsk_", log.read())
        self.assertNotIn("gsk_", str(reply))
        return reply

    async def test_url_returns_summary_and_public_structured_fields(self):
        reply = await self.call({"url": "https://example.test/clue.jpg", "context": "Coastal city"})
        self.assertFalse(reply.is_error)
        self.assertIn("1 location", reply.content[0].text)
        self.assertEqual(reply.structured_content, {
            "status": "success", "processing_time": "1s", "API_Requests_remaining": 5,
            "locations": [{"latitude": 1, "longitude": 2, "confidence": 0.7,
                           "confidence_details": {"method": "test", "quality_score": 0.7}}],
        })

    async def test_local_file(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "clue.jpg"
            path.write_bytes(b"fixture-media")
            reply = await self.call({"file": str(path)})
        self.assertFalse(reply.is_error)

    async def test_missing_key(self):
        reply = await self.call({"url": "https://example.test/clue.jpg"}, key="")
        self.assertTrue(reply.is_error)
        self.assertIn("GEOSEER_API_KEY", reply.content[0].text)

    async def test_rejected_key_and_exhausted_allowance(self):
        for key, message in [("gsk_rejected", "rejected"), ("gsk_exhausted", "insufficient")]:
            with self.subTest(key=key):
                reply = await self.call({"url": "https://example.test/clue.jpg"}, key=key)
                self.assertTrue(reply.is_error)
                self.assertIn(message, reply.content[0].text)

    async def test_unsupported_input(self):
        for args, message in [
            ({"file": "/tmp/invalid.txt"}, "supported format"),
            ({"file": "clue.jpg", "url": "https://example.test/clue.jpg"}, "exactly one"),
        ]:
            with self.subTest(args=args):
                reply = await self.call(args)
                self.assertTrue(reply.is_error)
                self.assertIn(message, reply.content[0].text)
