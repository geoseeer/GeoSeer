"""Client for GeoSeer's external Analyze endpoint."""

import json
import os
from collections.abc import Iterator, Sequence
from contextlib import ExitStack, contextmanager
from pathlib import Path
from typing import Any, Literal

import requests

FilePath = str | os.PathLike[str]
MediaMode = Literal["fast", "agent"]


class GeoSeerError(Exception):
    """The API returned an error or an invalid response."""


class APIError(GeoSeerError):
    """An unsuccessful HTTP response from GeoSeer."""

    def __init__(self, response: requests.Response) -> None:
        self.status_code = response.status_code
        self.retry_after = response.headers.get("Retry-After")
        try:
            body = response.json()
        except ValueError:
            body = None
        error = body.get("error") if isinstance(body, dict) else None
        if not isinstance(error, dict):
            error = {}
        self.code = error.get("code")
        self.details = error.get("details")
        message = error.get("message") or f"GeoSeer returned HTTP {self.status_code}."
        super().__init__(message)


class GeoSeer:
    """Analyze local media, direct media URLs, or text using the GeoSeer API."""

    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str | None = None,
        timeout: float | tuple[float, float] = (15, 450),
    ) -> None:
        self._api_key = api_key if api_key is not None else os.getenv("GEOSEER_API_KEY")
        if not self._api_key:
            raise ValueError("Provide api_key or set GEOSEER_API_KEY.")
        self._base_url = base_url or os.getenv("GEOSEER_BASE_URL") or "https://geoseeer.com/api/v1"
        self._timeout = timeout

    def analyze(
        self,
        *,
        files: FilePath | Sequence[FilePath] | None = None,
        urls: str | Sequence[str] | None = None,
        event_text: str | None = None,
        mode: MediaMode | None = None,
        context: str | None = None,
    ) -> dict[str, Any]:
        """Return the JSON result for exactly one kind of input."""
        with self._post(files, urls, event_text, mode, context, stream=False) as response:
            try:
                result = response.json()
            except ValueError as exc:
                raise GeoSeerError("GeoSeer returned invalid JSON.") from exc
            if not isinstance(result, dict):
                raise GeoSeerError("GeoSeer returned an unexpected JSON result.")
            return result

    @contextmanager
    def stream(
        self,
        *,
        files: FilePath | Sequence[FilePath] | None = None,
        urls: str | Sequence[str] | None = None,
        event_text: str | None = None,
        mode: MediaMode | None = None,
        context: str | None = None,
    ) -> Iterator[Iterator[dict[str, Any]]]:
        """Open a stream of decoded events. Use the result in a with block."""
        with self._post(files, urls, event_text, mode, context, stream=True) as response:
            content_type = response.headers.get("Content-Type", "").partition(";")[0]
            if content_type.strip().lower() != "text/event-stream":
                raise GeoSeerError("GeoSeer did not return an event stream.")
            yield self._events(response)

    def _post(
        self,
        files: FilePath | Sequence[FilePath] | None,
        urls: str | Sequence[str] | None,
        event_text: str | None,
        mode: MediaMode | None,
        context: str | None,
        *,
        stream: bool,
    ) -> requests.Response:
        if sum(value is not None for value in (files, urls, event_text)) != 1:
            raise ValueError("Provide exactly one of files, urls, and event_text.")
        if event_text is not None and (mode is not None or context is not None):
            raise ValueError("event_text supplies its own mode and context.")
        if mode not in (None, "fast", "agent"):
            raise ValueError("Media mode must be fast or agent.")

        fields: dict[str, Any] = {
            "analysis_mode": "event" if event_text is not None else mode or "fast",
            "stream": stream,
        }
        if context is not None:
            fields["user_context"] = context

        with ExitStack() as inputs:
            if files is not None:
                paths = [files] if isinstance(files, (str, os.PathLike)) else list(files)
                if not 1 <= len(paths) <= 3:
                    raise ValueError("Provide one to three files.")
                field_name = "file" if len(paths) == 1 else "files"
                uploads = []
                for filename in paths:
                    path = Path(filename)
                    file = inputs.enter_context(path.open("rb"))
                    uploads.append((field_name, (path.name, file)))
                fields["stream"] = "true" if stream else "false"
                body = {"files": uploads, "data": fields}
            else:
                if urls is not None:
                    media_urls = [urls] if isinstance(urls, str) else list(urls)
                    if not 1 <= len(media_urls) <= 3:
                        raise ValueError("Provide one to three URLs.")
                    if len(media_urls) == 1:
                        fields["url"] = media_urls[0]
                    else:
                        fields["urls"] = media_urls
                else:
                    fields["event_text"] = event_text
                body = {"json": fields}

            response = requests.post(
                f"{self._base_url.rstrip('/')}/analyze",
                headers={"X-API-Key": self._api_key},
                timeout=self._timeout,
                allow_redirects=False,
                stream=stream,
                **body,
            )

        if response.status_code != 200:
            with response:
                raise APIError(response)
        return response

    @staticmethod
    def _events(response: requests.Response) -> Iterator[dict[str, Any]]:
        pending = b""
        data_lines: list[bytes] = []
        for chunk in response.iter_content(chunk_size=512):
            lines = (pending + chunk).split(b"\n")
            pending = lines.pop()
            for line in lines:
                line = line.removesuffix(b"\r")
                if line.startswith(b"data:"):
                    data_lines.append(line[5:].removeprefix(b" "))
                if line or not data_lines:
                    continue
                try:
                    event = json.loads(b"\n".join(data_lines).decode("utf-8"))
                except ValueError as exc:
                    raise GeoSeerError("GeoSeer returned an invalid stream event.") from exc
                if not isinstance(event, dict):
                    raise GeoSeerError("GeoSeer returned an unexpected stream event.")
                data_lines.clear()
                terminal = event.get("type") in ("complete", "error", "cancelled")
                yield event
                if terminal:
                    return
        raise GeoSeerError("The GeoSeer stream closed before a terminal event.")
