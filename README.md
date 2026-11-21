# GeoSeer AI image geolocation — geoseeer.com 🌍🔍

[GeoSeer](https://geoseeer.com) analyzes images, multiple image clues, videos, and real-world event descriptions to suggest locations and explain the clues behind them. **Fast** provides rapid estimation, **Agent** uses tools and multi-step reasoning for a more extensive search, and **Event** investigates locations from text descriptions.

> Upload a photo, image set, or video, or enter an event description → Review location candidates with coordinates, addresses, and reasoning.

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
- ⚡ **Three Processing Modes** — Fast for rapid estimation, Agent for a more extensive search, and Event for text-only investigation. Fast measured 10 seconds at API p50 in the October 14, 2026 tests; timing varies with input, load, and network conditions
- 🌐 **Global Coverage** — Geolocate photos, image sets, and video from anywhere on Earth
- 📝 **Event Search Support** — Run text-only event geolocation searches without requiring file upload
- 🔒 **Processing & Sharing** — Media is stored temporarily during analysis, and cleanup attempts to remove processing files afterward. Saving or sharing a result can retain result data and associated media separately
- 🔌 **Developer API** — Simple REST API with streaming (SSE) support for easy integration
- 🏢 **Enterprise Ready** — Custom rate limits, white-label API access, and self-host support via [enterprise.geoseeer.com](https://enterprise.geoseeer.com)

---

## Performance Benchmarks

Updated **November 16, 2026**. Accuracy uses IM2GPS3k, and costs use entry monthly consumer plans with fixed search allowances, falling back to entry prepaid credits when no such plan exists. See the [full results, sources, and methodology](https://geoseeer.com/benchmarks).

| Provider | IM2GPS3k accuracy @ 1 km | Latency | Reference paid cost / search |
|----------|-------------------------|---------|----------------------------------|
| **GeoSeer** | [**67%**](https://geoseeer.com/benchmarks#accuracy), Agent | **10s**, Fast · GeoSeer API p50 | [**$0.19**](https://geoseeer.com/#pricing), Starter $19/month / 100 web searches |
| GeoAxis | — No published IM2GPS3k result | 35s, Global Search Low · GeoAxis API | [$0.90](https://geoaxis.ai/pricing), prepaid credits, minimum $10 purchase |
| Oceanir | [22.52%](https://oceanir.ai/geoestimation), Manta Geo-Estimation | — API not tested | [$1.00](https://oceanir.ai/pricing), Starter $10/month / 10 Orca Max detailed analyses |
| Picarta | [44.8%](https://picarta.ai/picarta-v2), V2.1 | 12s, standard image search · Picarta API | [$0.60](https://picarta.ai/pricing), $59.90/month / 100 searches, rounded |
| GeoInfer | [50%](https://docs.geoinfer.com/faq), Global | [1s](https://geoinfer.com/en), published inference reference | [$0.10](https://geoinfer.com/en/pricing), $4.99 / 50 global predictions, rounded |

> Accuracy: GeoSeer tested the full [IM2GPS3k benchmark](https://github.com/lugiavn/revisiting-im2gps) itself; competitor figures are linked vendor-published results from separate evaluations. Model versions, training data, prediction-selection rules, and experimental conditions can differ. Oceanir's accuracy result describes Manta, which requires organizational access; its displayed cost covers public Orca Max analysis.
>
> Latency: GeoSeer tested its own, GeoAxis's, and Picarta's APIs. The p50 values retain the October 14, 2026 test snapshot and selected modes. GeoInfer's displayed 1s represents its advertised sub-second inference, rather than a GeoSeer-measured API p50. Oceanir's API has not been timed. GeoAxis now [advertises](https://geoaxis.ai/) approximately 5s for Instant and 20s for Low; these are separate provider-reported production timings.
>
> Cost: Apply the same rule to all providers: use the entry monthly consumer plan with a fixed search allowance; otherwise use the entry prepaid pack or published credit rate. Divide price by included complete searches, assuming full utilization before allowance or credit expiry. GeoSeer's denominator is its 100 web searches; its separate API allowance is not added. [GeoAxis](https://geoaxis.ai/pricing) and [GeoInfer](https://geoinfer.com/en/pricing) advertise unlimited consumer subscriptions, whose effective per-search costs depend on actual usage, so the table uses their prepaid rates. GeoInfer [uses one credit per global prediction](https://docs.geoinfer.com/faq). Higher tiers and larger packs are separate: [Oceanir Pro](https://oceanir.ai/pricing) includes 300 detailed analyses for $29/month (about $0.10 each at full utilization). Free allowances, trials, promotions, annual billing, and negotiated enterprise rates are excluded. Commercial API pricing can differ from these consumer search references.

Providers were selected for their popularity, strong geolocation accuracy, and public availability at the comparison date. Access-restricted services such as [GeoSpy (now Raven)](https://graylark.com/raven/faq) and broader enterprise platforms such as [Palantir Foundry](https://www.palantir.com/platforms/foundry/) fall outside this product comparison. Individual model access is identified in the methodology.

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
| **Starter** | $19/month; or $9/month billed annually | All analysis modes, 100 searches/mo, 100 API calls/mo, priority processing |
| **Pro** | $69/month; or $29/month billed annually | Everything in Starter, unlimited web searches, 1,000 API calls/mo, white-label API access |
| **Enterprise** | Custom | Custom limits, white-label API access, self-host support — [enterprise.geoseeer.com](https://enterprise.geoseeer.com) |

> Eligible paid plans can purchase additional web-search or API credits from the dashboard at $0.20 per credit, sold in packs of five.

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
