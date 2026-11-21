#!/usr/bin/env bash
set -euo pipefail

: "${GEOSEER_API_KEY:?Set GEOSEER_API_KEY in your environment}"
base="${GEOSEER_BASE_URL:-https://geoseeer.com/api/v1}"
url="${base%/}/analyze"

usage() {
    printf '%s\n' 'Usage: analyze.sh upload PHOTO [PHOTO ...] | stream PHOTO' >&2
    exit 2
}

case "${1:-}" in
    upload|stream) command=$1 ;;
    *) usage ;;
esac
shift
if (( $# < 1 || $# > 3 )) || [[ $command == stream && $# != 1 ]]; then
    usage
fi

field=files
if (( $# == 1 )); then
    field=file
fi
args=()
for file in "$@"; do
    if [[ ! -r $file || ! -f $file ]]; then
        printf '%s\n' 'Cannot read input file.' >&2
        exit 2
    fi
    # Quote the filename in cURL's multipart form grammar.
    file=${file//\\/\\\\}
    file=${file//\"/\\\"}
    args+=(-F "$field=@\"$file\"")
done
if [[ $command == stream ]]; then
    args+=(--no-buffer -F stream=true)
fi
send_request() {
    printf 'X-API-Key: %s\n' "$GEOSEER_API_KEY" |
        curl --disable --silent --show-error --fail --max-time 450 --connect-timeout 15 \
            --header @- "${args[@]}" "$url"
}

if [[ $command == stream ]]; then
    send_request | awk '
        { print; fflush() }
        { sub(/\r$/, "") }
        /^event: completed$/ { completed = 1 }
        END {
            if (!completed) {
                print "GeoSeer stream ended without a completed event." > "/dev/stderr"
                exit 1
            }
        }
    '
else
    send_request
fi
