"""Command-line interface for the GeoSeer Analyze API."""

import argparse
import json
import sys
from collections.abc import Sequence
from importlib.metadata import version

from requests.exceptions import RequestException

from .client import GeoSeer, GeoSeerError


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return a process exit status."""
    parser = argparse.ArgumentParser(prog="geoseeer", description="GeoSeer geolocation API CLI.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {version('geoseeer')}")
    commands = parser.add_subparsers(required=True)
    analyze = commands.add_parser(
        "analyze",
        help="Analyze media or an event description.",
        description="Analyze media or an event description. Set GEOSEER_API_KEY before running.",
    )
    inputs = analyze.add_mutually_exclusive_group(required=True)
    inputs.add_argument(
        "--file", dest="files", metavar="PATH", action="append",
        help="Local media file. Repeat up to three times.",
    )
    inputs.add_argument(
        "--url", dest="urls", metavar="URL", action="append",
        help="Direct media URL. Repeat up to three times.",
    )
    inputs.add_argument("--event-text", metavar="DESCRIPTION", help="Text description for Event mode.")
    analyze.add_argument("--mode", choices=("fast", "agent"), help="Media analysis mode (default: fast).")
    analyze.add_argument("--context", help="Optional context for media analysis.")
    analyze.add_argument("--stream", action="store_true", help="Print each streamed event as one line of JSON.")
    args = parser.parse_args(argv)

    if args.event_text is not None and (args.mode is not None or args.context is not None):
        analyze.error("--mode and --context are only available with --file or --url.")

    options = {
        "files": args.files,
        "urls": args.urls,
        "event_text": args.event_text,
        "mode": args.mode,
        "context": args.context,
    }
    try:
        client = GeoSeer()
        if args.stream:
            with client.stream(**options) as events:
                for event in events:
                    print(json.dumps(event), flush=True)
                    if event.get("type") in ("error", "cancelled"):
                        message = event.get("message") or event.get("error") or event["type"]
                        print(f"geoseeer: {message}", file=sys.stderr)
                        return 1
        else:
            print(json.dumps(client.analyze(**options), indent=2), flush=True)
    except ValueError as exc:
        analyze.error(str(exc))
    except (GeoSeerError, RequestException, OSError) as exc:
        print(f"geoseeer: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("geoseeer: interrupted", file=sys.stderr)
        return 130
    return 0
