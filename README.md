# GeoSeer — AI-Powered Image Geolocation Platform 🌍🔍

[GeoSeer](https://geoseeer.com) is a professional-grade **AI geolocation intelligence platform** for image geolocation, broader visual geolocation workflows, and real-world event analysis. It pinpoints exact locations from images with state-of-the-art accuracy, and also supports image sets, short video analysis, and text-only event searches. Using an advanced **agentic workflow with fast, agent, and event modes**, GeoSeer combines rapid estimation with sophisticated multi-step reasoning and tool calling to deliver professional-grade results at a fraction of the cost and time.

> Upload a photo, image set, or short video, or enter an event description → Get precise GPS coordinates, address, and reasoning.

---

## How It Works

1. **Submit Input** 📤 — Upload an image via the [web interface](https://geoseeer.com) or the [REST API](https://geoseeer.com/api-docs). GeoSeer supports single-image, multi-image, video, image URL, and text-based event analysis on the web.
2. **AI Analysis** 🤖 — GeoSeer's agentic analysis system examines visual clues — architectural styles, natural landmarks, vegetation patterns, street furniture, signage, satellite data, environmental context, and event-specific context when using Event mode.
3. **Location Results** 📍 — Receive up to 8 location candidates ranked by confidence, each with GPS coordinates, human-readable address, and detailed reasoning explaining the analysis.

### Architecture Overview

GeoSeer's agentic pipeline consists of three complementary analysis paths:

- **Fast Mode (GS-Fast)** — Proprietary geospatial estimation for rapid kilometer-level predictions
- **Agent Mode (GS-Agent)** — Multi-step reasoning and tool calling for more comprehensive pinpointing
- **Event Mode (GS-Event)** — Text-first event investigation for real-world incident and event-location searches

Shared system components include:

- **Input Processing** — Visual media ingestion with metadata extraction (EXIF data, timestamps, camera info)
- **Model Estimation** — Proprietary geospatial estimation model used by GS-Fast and as a signal source for deeper analysis
- **LVLM Analysis** — Large Vision-Language Model analysis for feature extraction and scene understanding
- **Normalization & Reasoning** — Multi-step reasoning that integrates signals from all sources
- **Tool Calling** — Satellite imagery, map data, web search, and reverse image search for verification
- **Final Reasoning** — Comprehensive analysis combining all evidence into precise location candidates

---

## Features

- 🧠 **Agentic AI Architecture** — Advanced multi-step reasoning with tool calling for pinpoint accuracy
- ⚡ **Three Processing Modes** — GS-Fast (~10s, rapid estimation), GS-Agent (~30-60s, comprehensive analysis), and GS-Event (~50-150s depending on search complexity)
- 🌐 **Global Coverage** — Geolocate photos, image sets, and video from anywhere on Earth
- 📝 **Event Search Support** — Run text-only event geolocation searches without requiring file upload
- 🔒 **Privacy-First** — Uploaded media is processed in real-time and immediately discarded after analysis
- 🔌 **Developer API** — Simple REST API with streaming (SSE) support for easy integration
- 🏢 **Enterprise Ready** — Custom rate limits, white-label API access, and self-host support via [enterprise.geoseeer.com](https://enterprise.geoseeer.com)

---

## Performance Benchmarks

The results below summarize a fixed evaluation protocol covering geolocation accuracy, billed cost per completed query, and end-to-end response latency.

| Metric | GeoSeer | Picarta | Avg. AI Wrappers | Other |
|--------|---------|---------|------------------|-------|
| **Accuracy (@1 km)** | **83%** | 54% | 35% | 47% (EarthKit Agent) |
| **Cost per Query** | **$0.20** | $0.90 | $0.50 | $1.50 (Hiring Expert) |
| **Latency (Fast, p50)** | **10s** | 13s | 17s | 44s (EarthKit Agent) |

> Benchmark scope: Accuracy results use 150 held-out images across 50 urban, 50 rural, and 50 indoor scenes with verified coordinates. Cost results reflect public self-serve pricing in May 2026 for one image per request. Latency results reflect warm requests from a US East client with concurrency fixed at 1.
>
> Reporting notes: Accuracy is reported at 1 km and supported by additional distance-error analysis. Latency is reported as p50 response time, with p95 tracked in the full methodology. Products without public access or reproducible request conditions are excluded.

---

## Getting Started

### On the Web

Visit [geoseeer.com](https://geoseeer.com) — new users can get started **for free**.

1. Upload or drag & drop your image or video, or enter an event description
2. Choose Fast mode for quick estimation, Agent mode for deeper analysis, or Event mode for text-only event investigation
3. Optionally add context (country, source, time period, etc.)
4. Get precise location results with confidence scores and reasoning

### Via the API

Get your API key from the [Dashboard](https://geoseeer.com/dashboard), then send either a media-analysis request or a text-only event-analysis request:

```bash
curl -X POST https://geoseeer.com/api/v1/analyze \
  -H "X-API-Key: YOUR_API_KEY" \
  -F "file=@photo.jpg" \
  -F "analysis_mode=fast" \
  -F "user_context=Beach photo from summer 2025"
```

See the full [API Documentation](https://geoseeer.com/api-docs) or our [API.md](API.md) for detailed reference.

---

## Pricing

| Plan | Price | Includes |
|------|-------|----------|
| **Free** | $0 forever | Fast Mode access, 1 search/day on web, 10 total API calls |
| **Starter** | $19/mo ($9/mo annual) | All analysis modes, 100 searches/mo, 100 API calls/mo, priority processing |
| **Pro** | $69/mo ($29/mo annual) | Everything in Starter, unlimited web searches, 1,000 API calls/mo, white-label API access |
| **Enterprise** | Custom | Custom limits, white-label API access, self-host support — [enterprise.geoseeer.com](https://enterprise.geoseeer.com) |

> Starter and Pro plans: $0.20 per additional call beyond monthly limit.

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
