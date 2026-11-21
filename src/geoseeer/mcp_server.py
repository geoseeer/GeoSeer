"""Local stdio adapter for the GeoSeer client."""

from importlib.metadata import version
import os
from pathlib import Path
from typing import Annotated
from urllib.parse import urlsplit

from mcp.server import MCPServer
from mcp.types import CallToolResult, TextContent, ToolAnnotations
from pydantic import Field
from requests import RequestException, Timeout

from .client import APIError, GeoSeer, GeoSeerError


MEDIA_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif", ".mp4", ".mov", ".avi", ".mkv", ".webm"}
RESULT_FIELDS = ("status", "processing_time", "API_Requests_remaining", "early_exit", "exit_reason")
LOCATION_FIELDS = ("latitude", "longitude", "confidence", "address", "reasoning",
                   "confidence_method", "match_strength")
API_ERROR_MESSAGES = {
    400: "GeoSeer rejected the input or could not find a location.",
    401: "GeoSeer rejected the API key.",
    402: "The account has insufficient API credits.",
    403: "The API key does not have access to this analysis.",
    413: "The server rejected the upload size.",
    429: "GeoSeer is rate limiting requests.",
}
CONFIDENCE_FIELDS = ("method", "quality_score", "match_strength")


def _error(message: str) -> CallToolResult:
    return CallToolResult(content=[TextContent(type="text", text=message)], is_error=True)


def _public_location(location: dict) -> dict:
    public = {key: location[key] for key in LOCATION_FIELDS if key in location}
    details = location.get("confidence_details")
    if isinstance(details, dict):
        public["confidence_details"] = {key: details[key] for key in CONFIDENCE_FIELDS if key in details}
    return public


server = MCPServer("GeoSeer", version=version("geoseeer"), website_url="https://geoseeer.com", log_level="WARNING")


@server.tool(
    annotations=ToolAnnotations(read_only_hint=False, destructive_hint=False,
                                idempotent_hint=False, open_world_hint=True),
)
def geolocate_media(
    file: Annotated[str | None, Field(description="Local path to a supported image or video.")] = None,
    url: Annotated[str | None, Field(description="Direct HTTP or HTTPS URL of an image or video.")] = None,
    context: Annotated[str | None, Field(description="Optional location clues, up to 500 characters.")] = None,
) -> CallToolResult:
    """Estimate where an image or short video was taken using GeoSeer Fast mode.

    Give exactly one local file or direct media URL. Use media the user has
    authorized for upload. Local media, URLs, and optional context are sent
    to GeoSeer. A successful analysis consumes the user's API allowance.
    Confidence ranks candidate locations and is not a probability.
    """
    if (file is None) == (url is None):
        return _error("Provide exactly one local file or media URL.")

    if file is not None:
        path = Path(file)
        try:
            if path.suffix.lower() not in MEDIA_SUFFIXES or not path.is_file():
                return _error("Provide a readable local image or video in a supported format.")
            if path.stat().st_size >= 10 * 1024 * 1024:
                return _error("Choose a file smaller than 10 MiB to allow for multipart overhead.")
        except (OSError, ValueError):
            return _error("Could not read the local media file.")
    else:
        try:
            parsed = urlsplit(url)
            valid = (parsed.scheme in {"http", "https"} and parsed.hostname
                     and parsed.username is None and not any(c.isspace() for c in url))
        except ValueError:
            valid = False
        if not valid:
            return _error("Provide a valid direct HTTP or HTTPS media URL.")

    if context is not None and len(context.strip()) > 500:
        return _error("Context must be at most 500 characters.")

    key = os.getenv("GEOSEER_API_KEY", "").strip()
    if not key:
        return _error("Set GEOSEER_API_KEY in the MCP server environment.")

    try:
        result = GeoSeer(api_key=key, base_url="https://geoseeer.com/api/v1").analyze(
            files=file, urls=url, context=context, mode="fast",
        )
    except APIError as exc:
        message = API_ERROR_MESSAGES.get(exc.status_code, f"GeoSeer returned HTTP {exc.status_code}.")
        retry_after = exc.retry_after or ""
        if exc.status_code == 429 and retry_after.isascii() and retry_after.isdecimal() and len(retry_after) <= 10:
            message += f" Retry after {retry_after} seconds."
        return _error(message)
    except Timeout:
        return _error("The request timed out. GeoSeer may still be processing it.")
    except RequestException:
        return _error("The connection failed. GeoSeer may still be processing the request.")
    except (OSError, ValueError):
        return _error("Could not read the local media or submit the input.")
    except GeoSeerError:
        return _error("GeoSeer returned an invalid analysis response.")

    locations = result.get("locations")
    if result.get("status") != "success" or not isinstance(locations, list) or any(
        not isinstance(location, dict) for location in locations
    ):
        return _error("GeoSeer returned an invalid location result.")
    public = {key: result[key] for key in RESULT_FIELDS if key in result}
    public["locations"] = [_public_location(location) for location in locations]
    return CallToolResult(
        content=[TextContent(type="text", text=f"GeoSeer returned {len(locations)} location candidate(s).")],
        structured_content=public,
    )


def run() -> None:
    server.run(transport="stdio")
