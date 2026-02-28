# GeoSeer API Documentation 🌍🔍

The GeoSeer [API](https://geoseeer.com/api-docs) allows you to integrate AI-powered image geolocation into your applications. Submit any photo and receive precise location predictions with GPS coordinates, addresses, confidence scores, and detailed reasoning.

- **Base URL**: `https://geoseeer.com/api/v1`
- **Interactive Docs**: [geoseeer.com/api-docs](https://geoseeer.com/api-docs)

---

## Table of Contents

- [Authentication](#authentication)
- [Endpoint](#endpoint)
- [Request Format](#request-format)
  - [File Upload](#option-1-file-upload-multipartform-data)
  - [Image URL](#option-2-image-url-applicationjson)
- [Streaming](#streaming-server-sent-events)
- [Response Format](#response-format)
- [Error Codes](#error-codes)
- [Rate Limits](#rate-limits)
- [Supported Formats](#supported-image-formats)
- [Code Examples](#code-examples)
- [Pricing](#pricing)
- [Contact](#contact)

---

## Authentication

All API requests require an API key passed via the `X-API-Key` header.

**Getting your API key:**

1. Create an account at [geoseeer.com](https://geoseeer.com)
2. Go to the [Dashboard](https://geoseeer.com/dashboard)
3. Copy your API key

**Header format:**

```
X-API-Key: YOUR_API_KEY
```

> ⚠️ Keep your API key secret. Do not expose it in client-side code or public repositories.

---

## Endpoint

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/analyze` | Analyze an image to determine its geographic location |

Full URL: `https://geoseeer.com/api/v1/analyze`

---

## Request Format

The analyze endpoint supports two input modes: **file upload** and **image URL**.

### Option 1: File Upload (`multipart/form-data`)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `image` | File | **Yes** | Image file (JPG, PNG, WebP, HEIC). Max 10 MB. |
| `user_context` | String | No | Optional context to improve accuracy (e.g., "European city", "taken in 2023") |
| `stream` | Boolean | No | Set `true` for real-time SSE streaming updates. Default: `false`. |

**Example:**

```bash
curl -X POST https://geoseeer.com/api/v1/analyze \
  -H "X-API-Key: YOUR_API_KEY" \
  -F "image=@photo.jpg" \
  -F "user_context=Beach photo from summer 2025"
```

### Option 2: Image URL (`application/json`)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `image_url` | String | **Yes** | Publicly accessible URL of the image |
| `user_context` | String | No | Optional context to improve accuracy |
| `stream` | Boolean | No | Set `true` for real-time SSE streaming updates. Default: `false`. |

**Example:**

```bash
curl -X POST https://geoseeer.com/api/v1/analyze \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "https://example.com/photo.jpg",
    "user_context": "European city center"
  }'
```

---

## Streaming (Server-Sent Events)

Set `stream: true` in your request to receive real-time progress updates via **Server-Sent Events (SSE)**. This is useful for showing live analysis progress in your application.

### Event Types

| Event | Description |
|-------|-------------|
| `processing` | Progress updates during analysis (includes `message`, `branch_id`, `timestamp`) |
| `branch_point` | Engine is searching multiple geographic regions in parallel |
| `branch_update` | Status change for an individual search branch |
| `completed` | Final result with location candidates array |
| `error` | An error occurred during processing |

### SSE Event Format

```
event: processing
data: {"type":"progress","message":"Analyzing visual features","branch_id":"main_llm_primary","timestamp":1737312000.123}

event: completed
data: {"type":"complete","result":{"status":"success","candidates":[{"rank":1,"coordinates":{"latitude":48.8584,"longitude":2.2945},"address":"Eiffel Tower, Paris","confidence":0.95,"branch_id":"main_llm_primary"}],"processing_time":45.2}}
```

### Python Streaming Example

```python
import requests
import sseclient  # pip install sseclient-py
import json

API_KEY = "YOUR_API_KEY"

def analyze_with_streaming(image_url):
    response = requests.post(
        "https://geoseeer.com/api/v1/analyze",
        headers={
            "X-API-Key": API_KEY,
            "Content-Type": "application/json"
        },
        json={"image_url": image_url, "stream": True},
        stream=True
    )

    client = sseclient.SSEClient(response)
    for event in client.events():
        data = json.loads(event.data)

        if event.event == "processing":
            print(f"[{data.get('branch_id', '')}] {data.get('message', '')}")
        elif event.event == "completed":
            result = data.get("result", {})
            if result.get("status") == "success":
                for loc in result.get("candidates", []):
                    coords = loc.get("coordinates", {})
                    print(f"{loc['address']} ({coords.get('latitude')}, {coords.get('longitude')})")
            return result
        elif event.event == "error":
            print(f"Error: {data.get('error')}")
```

### JavaScript Streaming Example

```javascript
async function analyzeWithStreaming(imageUrl) {
  const response = await fetch('https://geoseeer.com/api/v1/analyze', {
    method: 'POST',
    headers: {
      'X-API-Key': 'YOUR_API_KEY',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ image_url: imageUrl, stream: true })
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop();

    let eventType = 'message';
    for (const line of lines) {
      if (line.startsWith('event: ')) {
        eventType = line.slice(7);
      } else if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6));

        if (eventType === 'processing') {
          console.log(`[${data.branch_id || ''}] ${data.message || ''}`);
        } else if (eventType === 'completed') {
          const { candidates } = data.result || {};
          candidates?.forEach(loc => {
            console.log(`${loc.address} (${loc.coordinates?.latitude}, ${loc.coordinates?.longitude})`);
          });
          return data.result;
        } else if (eventType === 'error') {
          throw new Error(data.error);
        }
      }
    }
  }
}
```

---

## Response Format

### Standard (Non-Streaming) Response

Returns up to **8 location candidates**, ordered by confidence score (highest first).

```json
{
  "status": "success",
  "locations": [
    {
      "latitude": 48.8584,
      "longitude": 2.2945,
      "confidence": 0.95,
      "address": "Eiffel Tower, Paris, France",
      "reasoning": "The image shows the Eiffel Tower from Trocadéro gardens..."
    },
    {
      "latitude": 48.8530,
      "longitude": 2.3499,
      "confidence": 0.72,
      "address": "Notre-Dame, Paris, France",
      "reasoning": "Gothic cathedral architecture matches Notre-Dame..."
    }
  ],
  "processing_time": "45.2s"
}
```

### Location Object Fields

| Field | Type | Description |
|-------|------|-------------|
| `latitude` | Float | Latitude of the predicted location |
| `longitude` | Float | Longitude of the predicted location |
| `confidence` | Float | Confidence score between 0 and 1 (higher = more confident) |
| `address` | String | Human-readable address of the predicted location |
| `reasoning` | String | Detailed explanation of why this location was predicted |

### Streaming Response

When `stream: true`, the final `completed` event contains:

```json
{
  "type": "complete",
  "result": {
    "status": "success",
    "candidates": [
      {
        "rank": 1,
        "coordinates": {
          "latitude": 48.8584,
          "longitude": 2.2945
        },
        "address": "Eiffel Tower, Paris",
        "confidence": 0.95,
        "branch_id": "main_llm_primary"
      }
    ],
    "processing_time": 45.2
  }
}
```

---

## Error Codes

| HTTP Code | Meaning | Description |
|-----------|---------|-------------|
| `400` | Bad Request | Invalid request parameters (e.g., missing image, unsupported format) |
| `401` | Unauthorized | Missing or invalid API key |
| `402` | Payment Required | API credits depleted — upgrade your plan or add credits |
| `413` | Payload Too Large | Image file exceeds the 10 MB size limit |
| `429` | Too Many Requests | Rate limit exceeded — wait and retry |
| `500` | Internal Server Error | Server-side error — retry or contact support |

### Error Response Format

```json
{
  "status": "error",
  "error": "Description of what went wrong"
}
```

---

## Rate Limits

| Plan | Rate Limit | Monthly Quota |
|------|-----------|---------------|
| **Free** | 1 request/second | 10 total API calls |
| **Starter** | 1 request/second | 100 API calls/month |
| **Pro** | 1 request/second | 1,000 API calls/month |
| **Enterprise** | Custom | Custom — [enterprise.geoseeer.com](https://enterprise.geoseeer.com) |

> Starter and Pro plans support automatic overage billing at **$0.20 per additional call** beyond the monthly limit.

---

## Supported Image Formats

| Format | Supported |
|--------|-----------|
| JPEG / JPG | ✅ |
| PNG | ✅ |
| WebP | ✅ |
| HEIC | ✅ |

**Maximum file size:** 10 MB

---

## Code Examples

### Python — File Upload

```python
import requests

API_KEY = "YOUR_API_KEY"

with open("photo.jpg", "rb") as f:
    response = requests.post(
        "https://geoseeer.com/api/v1/analyze",
        headers={"X-API-Key": API_KEY},
        files={"image": f},
        data={"user_context": "Beach vacation"}
    )

result = response.json()
if result["status"] == "success":
    top_location = result["locations"][0]
    print(f"Location: {top_location['address']}")
    print(f"Confidence: {top_location['confidence']*100:.0f}%")
    print(f"Coordinates: {top_location['latitude']}, {top_location['longitude']}")
    print(f"Reasoning: {top_location['reasoning']}")
```

### Python — Image URL

```python
import requests

API_KEY = "YOUR_API_KEY"

response = requests.post(
    "https://geoseeer.com/api/v1/analyze",
    headers={
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    },
    json={
        "image_url": "https://example.com/photo.jpg",
        "user_context": "European city center"
    }
)

result = response.json()
if result["status"] == "success":
    top_location = result["locations"][0]
    print(f"Location: {top_location['address']}")
    print(f"Confidence: {top_location['confidence']*100:.0f}%")
```

### Node.js — File Upload

```javascript
const formData = new FormData();
formData.append('image', fileInput.files[0]);
formData.append('user_context', 'Beach vacation');

const response = await fetch('https://geoseeer.com/api/v1/analyze', {
  method: 'POST',
  headers: { 'X-API-Key': 'YOUR_API_KEY' },
  body: formData
});

const result = await response.json();
if (result.status === 'success') {
  const topLocation = result.locations[0];
  console.log('Location:', topLocation.address);
  console.log('Confidence:', topLocation.confidence);
  console.log('Coordinates:', topLocation.latitude, topLocation.longitude);
}
```

### Node.js — Image URL

```javascript
const response = await fetch('https://geoseeer.com/api/v1/analyze', {
  method: 'POST',
  headers: {
    'X-API-Key': 'YOUR_API_KEY',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    image_url: 'https://example.com/photo.jpg',
    user_context: 'European city center'
  })
});

const result = await response.json();
if (result.status === 'success') {
  const topLocation = result.locations[0];
  console.log('Location:', topLocation.address);
  console.log('Confidence:', topLocation.confidence);
}
```

### cURL — File Upload

```bash
curl -X POST https://geoseeer.com/api/v1/analyze \
  -H "X-API-Key: YOUR_API_KEY" \
  -F "image=@photo.jpg" \
  -F "user_context=Beach photo from summer 2025"
```

### cURL — Image URL

```bash
curl -X POST https://geoseeer.com/api/v1/analyze \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "https://example.com/photo.jpg",
    "user_context": "European city center"
  }'
```

---

## Best Practices

1. **Provide context** — Adding `user_context` (country, region, time period, source) significantly improves accuracy.
2. **Use streaming for UIs** — Set `stream: true` when building user-facing applications to show real-time progress.
3. **Handle all error codes** — Implement proper error handling, especially for `429` (rate limit) with exponential backoff.
4. **Optimize image size** — While up to 10 MB is supported, typical photos (1–3 MB) process faster without sacrificing accuracy.
5. **Respect rate limits** — Stay within 1 request/second to avoid `429` errors. For higher throughput, contact us about [Enterprise plans](https://enterprise.geoseeer.com).
6. **Secure your API key** — Never expose your key in client-side code. Use server-side proxies for browser-based applications.
7. **Check confidence scores** — Use the `confidence` field to filter or weight results programmatically.

---

## Pricing

| Plan | Monthly Price | API Calls | Overage |
|------|--------------|-----------|---------|
| Free | $0 | 10 total | — |
| Starter | $19/mo ($9/mo annual) | 100/month | $0.20/call |
| Pro | $69/mo ($29/mo annual) | 1,000/month | $0.20/call |
| Enterprise | Custom | Custom | Custom |

View full pricing at [geoseeer.com](https://geoseeer.com/#pricing).

---

## Links

- 🌐 **Website**: [geoseeer.com](https://geoseeer.com)
- 📖 **Interactive API Docs**: [geoseeer.com/api-docs](https://geoseeer.com/api-docs)
- 🔑 **Dashboard & API Keys**: [geoseeer.com/dashboard](https://geoseeer.com/dashboard)
- 🏢 **Enterprise**: [enterprise.geoseeer.com](https://enterprise.geoseeer.com)
- 📘 **Product Introduction**: [Introduction.md](Introduction.md)

---

## Contact

For API support, enterprise partnerships, or feature requests, reach out through:

- 🌐 [geoseeer.com/about](https://geoseeer.com/about)
- 𝕏 [x.com/GeoSeeer](https://x.com/GeoSeeer)
- 💼 [LinkedIn](https://www.linkedin.com/company/geoseer)

---

© 2025-2026 GeoSeer. All rights reserved.
