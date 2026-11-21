"""Analyze local media or an event. Requires requests."""

import argparse
from contextlib import ExitStack
import json
import os
from pathlib import Path
import sys

import requests


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--file", type=Path, action="append")
    inputs.add_argument("--event")
    parser.add_argument("--mode", choices=("fast", "agent"))
    parser.add_argument("--context")
    args = parser.parse_args()
    if args.event is not None and (args.mode or args.context):
        parser.error("--event supplies its own mode and context")
    if args.file and len(args.file) > 3:
        parser.error("supply at most three files")

    key = os.environ.get("GEOSEER_API_KEY")
    if not key:
        parser.error("set GEOSEER_API_KEY in your environment")
    base_url = os.environ.get("GEOSEER_BASE_URL", "https://geoseeer.com/api/v1")

    try:
        with ExitStack() as stack:
            body = {}
            if args.file:
                field = "file" if len(args.file) == 1 else "files"
                body["files"] = [
                    (field, (path.name, stack.enter_context(path.open("rb"))))
                    for path in args.file
                ]
                body["data"] = {"analysis_mode": args.mode or "fast"}
                if args.context:
                    body["data"]["user_context"] = args.context
            else:
                body["json"] = {"analysis_mode": "event", "event_text": args.event}

            with requests.post(
                f"{base_url.rstrip('/')}/analyze",
                headers={"X-API-Key": key},
                timeout=(15, 450),
                allow_redirects=False,
                **body,
            ) as response:
                if response.status_code != 200:
                    print(f"GeoSeer returned HTTP {response.status_code}.", file=sys.stderr)
                    return 1
                print(json.dumps(response.json(), indent=2))
    except requests.Timeout:
        print("GeoSeer timed out. The server may still be processing the request.", file=sys.stderr)
        return 1
    except (OSError, ValueError):
        print("Could not read the input or complete a JSON response from GeoSeer.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
