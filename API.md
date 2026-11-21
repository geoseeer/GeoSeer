# GeoSeer External API

GeoSeer analyzes images, videos, and text-only event descriptions. Send
`POST https://geoseeer.com/api/v1/analyze` from a server or local program with
the `X-API-Key` header. Store the API key in an environment variable or secret
store and keep it out of browser code.

[OpenAPI document](openapi.json)

## Request limits and supported formats

- Submit up to three media items as clues for one analysis. The API returns
  one set of location candidates for the request.
- The application limits the entire HTTP request body to 10 MiB. Allow room
  for multipart headers and boundaries when uploading files. Each URL download
  may contain up to 10 MiB of media.
- Upload filenames must use an accepted suffix. URL downloads should return the
  exact media content type listed below. Actual media must decode successfully.

| Input | Upload suffixes | URL response content types |
| --- | --- | --- |
| Images | `jpg`, `jpeg`, `png`, `webp`, `heic`, `heif` | `image/jpeg`, `image/jpg`, `image/png`, `image/webp`, `image/heic`, `image/heif` |
| Videos | `mp4`, `mov`, `avi`, `mkv`, `webm` | `video/mp4`, `video/quicktime`, `video/x-msvideo`, `video/x-matroska`, `video/webm` |

## Analysis modes and access

| Mode | Input | Plan access |
| --- | --- | --- |
| `fast` (default) | Media | Free and paid API plans |
| `agent` | Media | Paid API plans |
| `event` | Event description | Paid API plans |

Standard per-user daily limits use a rolling 24-hour window. The default limit
is 100 calls, Starter is 500, and Pro and Enterprise are 2,000. Marketplace
subscribers use the default daily limit. Direct API keys are also limited to one
request per second and 10 requests per minute. Repeated invalid inputs can
trigger a temporary block.

## Request formats

Use one input shape per analysis. Set `analysis_mode` to select a mode. JSON
requests use a Boolean `stream`; multipart requests use the text value `true`
or `false`. Streaming defaults to `false`.

### Multipart upload

Use a single `file` part or repeat the `files` part for multiple uploads. Use
`user_context` to supply optional clues for Fast or Agent mode. Context may
contain up to 500 characters after trimming.

The upload aliases `image`, `images`, and `images[]` remain accepted. Use one
field family for interoperability with other clients. Repeated plural fields
are collected first, and singular fields are used only when the plural fields
supply no files.

### JSON URL input

Use `url` for one URL or `urls` for an array of URLs pointing to media. The
aliases `image_url` and `image_urls` remain accepted. Use `user_context` for
optional clues, subject to the same 500-character limit.

```json
{
  "analysis_mode": "fast",
  "url": "https://example.com/photo.jpg",
  "user_context": "A coastal city"
}
```

### Event input

Set `analysis_mode` to `event` and use `event_text` for the description. Event
requests reject recognized media fields. The server also accepts `text` and
then `user_context` as fallbacks for the description. The description may
contain up to 500 characters after trimming. Event mode accepts JSON or form
fields, with no file parts.

```json
{
  "analysis_mode": "event",
  "event_text": "Final held at Lusail Stadium in Qatar"
}
```

The legacy `return_debug` request flag is accepted. The public response is
described below.

## Synchronous response

With `stream=false`, a successful analysis returns HTTP `200` and JSON.

```json
{
  "status": "success",
  "locations": [
    {
      "latitude": 25.0,
      "longitude": 55.0,
      "confidence": 0.7,
      "address": "Example",
      "reasoning": "..."
    }
  ],
  "processing_time": "18.4s",
  "API_Requests_remaining": 42
}
```

Each location uses decimal degrees. `processing_time` is a duration string.
`API_Requests_remaining` is an integer, the string `"unlimited"`, or `null`
when a balance is unavailable. Marketplace synchronous responses omit this field.
Some results include `early_exit: true` and an `exit_reason` such as
`"gps_metadata"`.

The default synchronous wait deadline is 330 seconds after the analysis is
accepted. Allow additional time for upload or URL retrieval. If your connection
times out or drops, the server may still be processing the request. Repeating
the POST can start another analysis and consume another credit.

### Confidence interpretation

For verified Agent-mode locations, `confidence` is a geographic quality score.
Treat it as a ranking signal with approximate geographic meaning. It has no
calibrated probability or guaranteed radius. GPS metadata and visual-coordinate
fallbacks use their own scoring policies.

The browser result profile can include `match_strength`, `confidence_method`,
and `confidence_details`. For `geoseer_quality_v1`, the details include
`method`, `quality_score`, and `match_strength`. Current API-key Analyze
responses expose `confidence` in each location. Clients should tolerate
optional confidence metadata if present.

## Streaming response

Set `stream=true` to request `text/event-stream` over the same authenticated
POST. Errors detected before stream setup return an HTTP error response. Once
the stream starts, inspect its events for the outcome. The stream deadline is
300 seconds from connection setup.

Each event uses SSE framing with one JSON object in the `data` field.
Numbered events repeat the sequence ID as a string in `last_event_id`.
Keepalive comments have no JSON body. The external POST provides no reconnect
or replay endpoint.

```text
id: 1
event: processing
data: {"type":"progress","message":"Starting fast analysis","last_event_id":"1"}
```

| SSE event | JSON payload |
| --- | --- |
| `processing` | `type: "progress"`, `message`, and optional progress metadata. The queued messages include “Starting <mode> analysis” and “Waiting for an available analysis slot.” |
| `branch_point` | `type: "branch_point"` and branch metadata when emitted. |
| `branch_update` | `type: "branch_update"` and branch metadata, including a normalized `status`. |
| `completed` | `type: "complete"` and `result` containing the public result object. |
| `error` | `type: "error"`, `error`, and `message`. A failed analysis includes `error_code`. A stream deadline includes `timeout_seconds`. |
| `cancelled` | `type: "cancelled"`, `message`, and `error_code`. |

Treat a stream that closes without `completed` as having no successful result.
The browser stream uses a separate profile with `candidates` and a `failed`
event for failed or cancelled analyses.

## Errors and credits

Application errors normally use the following JSON envelope. Proxies may send
their own response body.

```json
{
  "success": false,
  "error": {
    "code": "invalid_field_value",
    "message": "Invalid analysis_mode. Allowed values: agent, fast, event"
  }
}
```

| HTTP status | Error code and meaning |
| --- | --- |
| `400` | `missing_required_field` or `invalid_field_value` for bad input, including unsupported media formats and oversized URL downloads. `event_invalid_input` denotes an invalid event. A failed analysis generally uses `invalid_request`. |
| `401` | `missing_credentials` or `invalid_credentials` for missing or invalid API keys. |
| `402` | `insufficient_api_credits` signals an exhausted allowance. `error.details` may include credit totals. |
| `403` | `free_plan_fast_mode_only` denotes a mode the free plan cannot use. |
| `413` | An oversized HTTP request can be rejected with this status. A body-parser failure caught inside Analyze may instead return `500`. |
| `429` | `rate_limited` denotes a request limit or full analysis queue. Request-limit responses include `Retry-After` in seconds and `error.details.retry_after_seconds`. Queue-full responses may omit these. |
| `500` | `internal_server_error` for an unexpected request or processing error. |
| `503` | `service_unavailable` when analysis state is temporarily unavailable. |
| `504` | `service_unavailable` when a synchronous analysis times out. |

An accepted direct API analysis holds a credit until the outcome is known. A
successful analysis charges the hold. Failed or cancelled work releases the
hold through the normal credit lifecycle. Agent image rejection or a completed
search without a usable location is a failed analysis (`400` for synchronous
calls, `error` for external SSE). Those outcomes do not consume a successful
analysis credit. Marketplace billing is handled by the marketplace.

## Processing storage and sharing

Submitted media is held in temporary local files during processing. Analysis
cleanup attempts to remove those files when work ends. When image search needs
temporarily hosted imagery, cleanup attempts to delete the transformed copy
after the search. Maximum retention periods for processing media and result
records have not been verified. Saving or sharing a result is a separate action
that persists result data and may include original media references. Analyze
does not publish a share.

## Executable examples

Set `GEOSEER_API_KEY` in your shell. Use your own local media or a direct media
URL you can submit to GeoSeer. The scripts accept `GEOSEER_BASE_URL` when testing
against another compatible environment.

[cURL](examples/external_api/analyze.sh) · [Python](examples/external_api/analyze.py) · [Node.js](examples/external_api/analyze.mjs)

From the repository root:

```bash
# Single upload and a multi-image analysis with cURL
examples/external_api/analyze.sh upload ./photo.jpg
examples/external_api/analyze.sh upload ./front.jpg ./side.jpg

# Stream progress and inspect the terminal event
examples/external_api/analyze.sh stream ./photo.jpg

# Upload or analyze an event in Python (requires requests)
python3 examples/external_api/analyze.py --file ./photo.jpg
python3 examples/external_api/analyze.py --event 'Final held at Lusail Stadium in Qatar'

# Analyze a direct media URL with Node.js 22+
node examples/external_api/analyze.mjs 'https://example.com/photo.jpg'
```

Replace the example URL with a reachable file. Event-mode calls require a paid
API plan.
