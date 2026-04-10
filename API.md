# GeoSeer API Documentation

This document mirrors the current API contract shown on the GeoSeer API Docs page.

- Base URL: `https://geoseeer.com/api/v1`
- Interactive docs: `https://geoseeer.com/api-docs`

---

## Authentication

All requests require the `X-API-Key` header.

```http
X-API-Key: YOUR_API_KEY
```

Get your API key from the dashboard:

- `https://geoseeer.com/dashboard`

---

## Endpoint

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/analyze` | Analyze media or URL input. |

Full URL:

`https://geoseeer.com/api/v1/analyze`

---

## Request Parameters

### Required

- `X-API-Key` (header): API key.
- Input selector (body): provide exactly one of `file`, `files`, `url`, or `urls`.

### Optional

- `analysis_mode`: `fast` or `agent` (default: `fast`).
- `stream`: boolean (default: `false`). Set `true` for SSE updates.
- `user_context`: string with extra hints.

### Input Shapes

- `file`: single image or video upload.
- `files`: multiple image uploads only (up to 3 items).
- `url`: single image or video URL.
- `urls`: multiple image URLs only (up to 3 URLs).

---

## Supported Formats And Limits

### Images

- JPG
- PNG
- WebP
- HEIC

### Video

- MP4
- MOV
- WebM

### Limits

- Max media items per request: `3`
- Max upload size: `10MB`

---

## Quick Start Examples

### File Upload: Single File (Image Or Video)

```bash
curl -X POST https://geoseeer.com/api/v1/analyze \
	-H "X-API-Key: YOUR_API_KEY" \
	-F "file=@/path/to/media.jpg" \
	-F "analysis_mode=fast"
```

```python
import requests

API_KEY = "YOUR_API_KEY"

with open("media.jpg", "rb") as media_file:
		response = requests.post(
				"https://geoseeer.com/api/v1/analyze",
				headers={"X-API-Key": API_KEY},
				files={"file": media_file},
				data={"analysis_mode": "fast"}
		)

result = response.json()
print(result["locations"][0]["address"])
```

```javascript
const selectedFile = fileInput.files[0];
const formData = new FormData();
formData.append('file', selectedFile);
formData.append('analysis_mode', 'fast');

const response = await fetch('https://geoseeer.com/api/v1/analyze', {
	method: 'POST',
	headers: { 'X-API-Key': 'YOUR_API_KEY' },
	body: formData
});

const result = await response.json();
console.log(result.locations[0].address);
```

### File Upload: Multiple Images

```bash
curl -X POST https://geoseeer.com/api/v1/analyze \
	-H "X-API-Key: YOUR_API_KEY" \
	-F "files=@front.jpg" \
	-F "files=@side.jpg" \
	-F "files=@detail.jpg" \
	-F "analysis_mode=fast"
```

### URL Input: Single URL (Image Or Video)

```bash
curl -X POST https://geoseeer.com/api/v1/analyze \
	-H "X-API-Key: YOUR_API_KEY" \
	-H "Content-Type: application/json" \
	-d '{
		"url": "https://example.com/photo.jpg",
		"analysis_mode": "fast"
	}'
```

### URL Input: Multiple Image URLs

```bash
curl -X POST https://geoseeer.com/api/v1/analyze \
	-H "X-API-Key: YOUR_API_KEY" \
	-H "Content-Type: application/json" \
	-d '{
		"urls": [
			"https://example.com/front.jpg",
			"https://example.com/side.jpg",
			"https://example.com/detail.jpg"
		],
		"analysis_mode": "fast"
	}'
```

---

## Response Format

Canonical success responses include `locations` and `API_Requests_remaining`.

```json
{
	"status": "success",
	"locations": [
		{
			"latitude": 48.8584,
			"longitude": 2.2945,
			"confidence": 0.95,
			"address": "Eiffel Tower, Paris, France",
			"reasoning": "The image shows the Eiffel Tower from Trocadero gardens..."
		},
		{
			"latitude": 48.853,
			"longitude": 2.3499,
			"confidence": 0.72,
			"address": "Notre-Dame, Paris, France",
			"reasoning": "Gothic cathedral architecture and urban layout align with Notre-Dame..."
		}
	],
	"processing_time": "45.2s",
	"API_Requests_remaining": 67
}
```

### Contract Guarantees

- `locations` is the canonical success result field.
- `API_Requests_remaining` is present in success responses.
- `API_Requests_remaining` is a number.
- `processing_time` is a string with an `s` suffix.
- `status` is `"success"` for successful responses.

---

## Streaming (SSE)

Set `stream: true` to receive Server-Sent Events.

### Event Types

- `processing`: progress updates.
- `branch_point`: parallel branch creation (mostly agent mode; usually absent in fast mode).
- `branch_update`: branch status update (mostly agent mode; usually absent in fast mode).
- `completed`: final result with `locations` and `API_Requests_remaining`.
- `error`: processing error.
- `cancelled`: analysis cancelled.

### SSE Example

```text
: keepalive

id: 101
event: processing
data: {"type":"progress","message":"Running fast analysis","branch_id":"Satellite Agent","last_event_id":"101"}

id: 102
event: branch_point
data: {"type":"branch_point","branch_point":{"fork_id":"candidate_search_methods","fork_label":"Candidate Search Methods","branches":[{"branch_id":"Search Agent","label":"Web Search","status":"processing"},{"branch_id":"Satellite Agent","label":"Satellite","status":"processing"}]},"last_event_id":"102"}

id: 103
event: branch_update
data: {"type":"branch_update","branch_id":"Search Agent","status":"completed","message":"Found 2 candidates","last_event_id":"103"}

id: 104
event: completed
data: {"type":"complete","result":{"status":"success","locations":[{"latitude":25.7735,"longitude":-80.2859,"address":"Miami, United States","confidence":0.6,"reasoning":"Visual clues suggest a likely match in this region."}],"processing_time":"24.9s","API_Requests_remaining":67},"last_event_id":"104"}

id: 105
event: cancelled
data: {"type":"cancelled","message":"Analysis cancelled","last_event_id":"105"}
```

### Python Streaming Example

```python
import json
import requests

API_KEY = "YOUR_API_KEY"

def analyze_with_streaming(url):
		response = requests.post(
				"https://geoseeer.com/api/v1/analyze",
				headers={
						"X-API-Key": API_KEY,
						"Content-Type": "application/json"
				},
				json={"url": url, "analysis_mode": "fast", "stream": True},
				stream=True
		)

		event_type = None
		for raw_line in response.iter_lines(decode_unicode=True):
				if not raw_line:
						continue
				if raw_line.startswith("event: "):
						event_type = raw_line[7:]
						continue
				if not raw_line.startswith("data: "):
						continue

				payload = json.loads(raw_line[6:])
				if event_type == "processing":
						print(payload.get("message", "Processing"))
				elif event_type == "completed":
						result = payload.get("result", {})
						print(result["locations"][0]["address"])
						print("Remaining:", result.get("API_Requests_remaining"))
						return result
				elif event_type == "cancelled":
						print(payload.get("message", "Analysis cancelled"))
						return None
				elif event_type == "error":
						raise RuntimeError(payload.get("error", "Streaming error"))
```

### JavaScript Streaming Example

```javascript
async function analyzeWithStreaming(fileUrl) {
	const response = await fetch('https://geoseeer.com/api/v1/analyze', {
		method: 'POST',
		headers: {
			'X-API-Key': 'YOUR_API_KEY',
			'Content-Type': 'application/json'
		},
		body: JSON.stringify({
			url: fileUrl,
			analysis_mode: 'fast',
			stream: true
		})
	});

	const reader = response.body.getReader();
	const decoder = new TextDecoder();
	let buffer = '';
	let eventType = '';

	while (true) {
		const { done, value } = await reader.read();
		if (done) break;

		buffer += decoder.decode(value, { stream: true });
		const chunks = buffer.split('\n\n');
		buffer = chunks.pop() || '';

		for (const chunk of chunks) {
			const lines = chunk.split('\n');
			let dataPayload = null;

			for (const line of lines) {
				if (line.startsWith('event: ')) {
					eventType = line.slice(7);
				}
				if (line.startsWith('data: ')) {
					dataPayload = JSON.parse(line.slice(6));
				}
			}

			if (!dataPayload) continue;

			if (eventType === 'processing') {
				console.log(dataPayload.message || 'Processing');
			} else if (eventType === 'completed') {
				const result = dataPayload.result || {};
				console.log(result.locations?.[0]?.address);
				console.log('Remaining:', result.API_Requests_remaining);
				return result;
			} else if (eventType === 'cancelled') {
				console.log(dataPayload.message || 'Analysis cancelled');
				return null;
			} else if (eventType === 'error') {
				throw new Error(dataPayload.error || 'Streaming error');
			}
		}
	}
}
```

---

## Error Codes

| HTTP Code | Label |
| --- | --- |
| `400` | Invalid request |
| `401` | Unauthorized |
| `402` | Usage limit reached |
| `413` | File too large |
| `429` | Queue full |
| `500` | Server error |

---

## Links

- Website: `https://geoseeer.com`
- API docs page: `https://geoseeer.com/api-docs`
- Dashboard: `https://geoseeer.com/dashboard`
