# GeoSeer — AI-Powered Image Geolocation Platform 🌍🔍

[GeoSeer](https://geoseeer.com) is a professional-grade **AI geolocation intelligence platform** that pinpoints exact locations from images with state-of-the-art accuracy. Using an advanced **multi-agent workflow**, GeoSeer performs sophisticated multi-step reasoning and tool calling to deliver professional-grade results at a fraction of the cost and time.

> Upload any photo → Get precise GPS coordinates, address, and reasoning — in seconds.

---

## How It Works

1. **Upload Image** 📤 — Upload an image via the [web interface](https://geoseeer.com) or the [REST API](https://geoseeer.com/api-docs). Supports file upload (JPG, PNG, WebP, HEIC) and image URLs.
2. **AI Analysis** 🤖 — GeoSeer's multi-agent AI system examines visual clues — architectural styles, natural landmarks, vegetation patterns, street furniture, signage, satellite data, and environmental context.
3. **Location Results** 📍 — Receive up to 8 location candidates ranked by confidence, each with GPS coordinates, human-readable address, and detailed reasoning explaining the analysis.

### Architecture Overview

GeoSeer's multi-agent pipeline consists of:

- **Input Processing** — Image ingestion with metadata extraction (EXIF data, timestamps, camera info)
- **Model Estimation** — Proprietary geospatial estimation model (GS-Fast) for rapid kilometer-level predictions
- **LVLM Analysis** — Large Vision-Language Model analysis for feature extraction and scene understanding
- **Normalization & Reasoning** — Multi-step reasoning that integrates signals from all sources
- **Tool Calling** — Satellite imagery, map data, web search, and reverse image search for verification
- **Final Reasoning** — Comprehensive analysis combining all evidence into precise location candidates

---

## Features

- 🧠 **Multi-Agent AI Architecture** — Advanced multi-step reasoning with tool calling for pinpoint accuracy
- ⚡ **Dual Processing Modes** — GS-Fast (~10s, rapid estimation) and GS-Agent (~30-60s, comprehensive analysis)
- 🌐 **Global Coverage** — Geolocate photos from anywhere on Earth
- 🔒 **Privacy-First** — Images are processed in real-time and immediately discarded after analysis
- 🔌 **Developer API** — Simple REST API with streaming (SSE) support for easy integration
- 🏢 **Enterprise Ready** — Custom rate limits, dedicated support, and scalable infrastructure via [enterprise.geoseeer.com](https://enterprise.geoseeer.com)

---

## Performance Benchmarks

GeoSeer delivers **industry-leading performance** across all key metrics:

| Metric | GeoSeer | Picarta | Avg. AI Wrappers | Other |
|--------|---------|---------|------------------|-------|
| **Accuracy** | **83%** | 54% | 35% | 47% (EarthKit Agent) |
| **Cost per Query** | **$0.20** | $0.45 | $0.33 | $0.50 (Hiring Expert) |
| **Latency (Fast)** | **10s** | 13s | 17s | 44s (EarthKit Agent) |

> Benchmark: 150 diverse images (50 urban, 50 rural, 50 indoor). Success thresholds: Urban ≤1km², Rural ≤10km², Indoor ≤5km².

---

## Getting Started

### On the Web

Visit [geoseeer.com](https://geoseeer.com) — new users can get started **for free**.

1. Upload or drag & drop your image
2. Optionally add context (country, source, time period, etc.)
3. Get precise location results with confidence scores and reasoning

### Via the API

Get your API key from the [Dashboard](https://geoseeer.com/dashboard), then:

```bash
curl -X POST https://geoseeer.com/api/v1/analyze \
  -H "X-API-Key: YOUR_API_KEY" \
  -F "image=@photo.jpg" \
  -F "user_context=Beach photo from summer 2025"
```

See the full [API Documentation](https://geoseeer.com/api-docs) or our [API.md](API.md) for detailed reference.

---

## Pricing

| Plan | Price | Includes |
|------|-------|----------|
| **Free** | $0 forever | 1 search/day on web, 10 total API calls |
| **Starter** | $19/mo ($9/mo annual) | 100 searches/mo, 100 API calls/mo, priority processing |
| **Pro** | $69/mo ($29/mo annual) | Unlimited web searches, 1,000 API calls/mo |
| **Enterprise** | Custom | Custom limits, dedicated support — [enterprise.geoseeer.com](https://enterprise.geoseeer.com) |

> Starter and Pro plans: $0.20 per additional API call beyond monthly limit.

---

## Use Cases

- **OSINT & Investigations** — Verify photo locations for open-source intelligence work
- **Journalism & UGC Verification** — Authenticate user-generated content and news sources
- **Academic Research** — Study geospatial patterns, verify historical image locations
- **Supply Chain & Logistics** — Geolocate assets and shipment photos
- **AI Agent Infrastructure** — Integrate geolocation capabilities into autonomous AI systems
- **Enterprise Applications** — Build geolocation-powered features into your products

---

## About

GeoSeer is developed by **Shenzhen Ques Technology Co., Ltd.** ([quesx.com](https://quesx.com)) as part of the company's OSINT (Open-Source Intelligence) infrastructure ecosystem. Our mission is to make professional geolocation capabilities accessible to everyone — from individual investigators and researchers to AI agents and enterprise systems.

---

## Links

- 🌐 **Website**: [geoseeer.com](https://geoseeer.com)
- 📖 **API Docs**: [geoseeer.com/api-docs](https://geoseeer.com/api-docs)
- 🏢 **Enterprise**: [enterprise.geoseeer.com](https://enterprise.geoseeer.com)
- 📝 **Blog**: [geoseeer.com/blog](https://geoseeer.com/blog)
- 💼 **Careers**: [geoseeer.com/careers](https://geoseeer.com/careers)

### Social

- [X (Twitter)](https://x.com/GeoSeeer)
- [LinkedIn](https://www.linkedin.com/company/geoseer)
- [Instagram](https://www.instagram.com/geoseeer/)
- [TikTok](https://www.tiktok.com/@geoseeer)
- [YouTube](https://www.youtube.com/@geoseeer)
- [Facebook](https://www.facebook.com/profile.php?id=61583773556872)

---

## Contact

For inquiries, enterprise partnerships, or support, visit [geoseeer.com/about](https://geoseeer.com/about) or reach out through our social channels.

---

© 2025-2026 GeoSeer. All rights reserved.
