# Image Converter & Compressor for AI Agents

[![Run on Apify](https://apify.com/ext/run-on-apify.png)](https://apify.com/ent-e/image-converter-compressor)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**Convert to WebP** or AVIF, compress to a target file size, resize, and strip EXIF/GPS metadata from any image URL, in one API call, running as an [Apify Actor](https://apify.com/ent-e/image-converter-compressor) at $1 per 1,000 images. Nothing to install, no server to run.

This repository contains the Actor's source code, tests and example inputs. The hosted version is on the Apify Store:

**▶ [Run it on Apify](https://apify.com/ent-e/image-converter-compressor)**

## What it does

You send a public image URL (or a batch of them) and choose a format. The Actor converts, resizes and compresses each image with Pillow, stores the result in the run's key-value store, and returns one row per image with a download link (`outputUrl`), the final dimensions, the output size and the percentage saved.

- **Formats out:** `webp` (default), `avif`, `jpeg`, `png`, `gif`, `tiff`
- **Formats in:** JPEG, PNG, WebP, AVIF, GIF (first frame), TIFF, BMP and more
- **Compress to a target size:** set `maxBytes` and quality is lowered automatically until the image fits (JPEG, WebP, AVIF)
- **Resize:** cap the size with `maxWidth` and/or `maxHeight` (never upscales)
- **Privacy:** EXIF and GPS metadata are removed by default (`stripMetadata: true`)
- **Handled for you:** EXIF auto-rotation, and transparency is flattened for JPEG output
- **Failed images are free:** a bad URL or unreadable file comes back as a `status: "error"` row and the run continues

## Quick start

You need an Apify account and an API token (Apify Console → Settings → API & Integrations). Keep the token in an environment variable, never in code:

```bash
export APIFY_TOKEN=<your-apify-token>
```

### curl (run synchronously and get dataset items)

```bash
curl -X POST "https://api.apify.com/v2/acts/ent-e~image-converter-compressor/run-sync-get-dataset-items" \
  -H "Authorization: Bearer $APIFY_TOKEN" \
  -H "Content-Type: application/json" \
  -d @examples/convert-to-webp.json
```

Synchronous calls wait up to 5 minutes. For very large batches, start an asynchronous run (`POST /v2/acts/ent-e~image-converter-compressor/runs`) and read the dataset when it finishes.

### Python (`pip install apify-client`)

```python
import os
from apify_client import ApifyClient

client = ApifyClient(os.environ["APIFY_TOKEN"])
run = client.actor("ent-e/image-converter-compressor").call(
    run_input={
        "url": "https://download.samplelib.com/png/sample-boat-400x300.png",
        "target": "webp",
        "maxBytes": 20000,
    }
)
for item in client.dataset(run["defaultDatasetId"]).iterate_items():
    print(item["status"], item.get("outputUrl"), item.get("savedPercent"), item.get("error"))
```

### JavaScript / Node.js (`npm install apify-client`)

```js
import { ApifyClient } from 'apify-client';

const client = new ApifyClient({ token: process.env.APIFY_TOKEN });
const run = await client.actor('ent-e/image-converter-compressor').call({
    url: 'https://download.samplelib.com/png/sample-boat-400x300.png',
    target: 'avif',
    maxWidth: 200,
});
const { items } = await client.dataset(run.defaultDatasetId).listItems();
for (const item of items) console.log(item.status, item.outputUrl ?? item.error);
```

### MCP (Claude, Cursor and other MCP clients)

```json
{
  "mcpServers": {
    "apify": { "url": "https://mcp.apify.com?tools=ent-e/image-converter-compressor" }
  }
}
```

### n8n / Make / Zapier

Use the official Apify integration ("Run an Actor and get dataset" in n8n, "Run an Actor" + "Get Dataset Items" in Make, "Run Actor and Fetch Results" in Zapier), select `ent-e/image-converter-compressor`, paste an input from [`examples/`](examples/) and map each item's `outputUrl` into the next step. In n8n you can pass a URL from a previous node, e.g. `"url": "{{ $json.imageUrl }}"`.

**Ready-made templates:** importable n8n workflows and Make blueprints for this Actor are in [ENT-E-Pro/automation-templates](https://github.com/ENT-E-Pro/automation-templates).

## Example inputs

See [`examples/`](examples/):

| File | What it does |
|---|---|
| [`convert-to-webp.json`](examples/convert-to-webp.json) | PNG → WebP at quality 80 |
| [`convert-to-avif.json`](examples/convert-to-avif.json) | PNG → AVIF |
| [`compress-to-target-size.json`](examples/compress-to-target-size.json) | JPEG under a byte budget, metadata stripped |
| [`resize-max-200.json`](examples/resize-max-200.json) | Fit inside a 200 × 200 box as WebP |
| [`batch-bulk-compress.json`](examples/batch-bulk-compress.json) | Batch with shared defaults and per-file overrides |

## Input

| Field | Type | Default | Description |
|---|---|---|---|
| `url` | string | – | Public URL of one image (max 50 MB, 100 megapixels). |
| `files` | array | – | Batch of images; each item can override any setting below. Plain URL strings also work. |
| `target` | string | `webp` | `webp`, `avif`, `jpeg`, `png`, `gif`, `tiff`. |
| `quality` | integer | `80` | 1–100 for JPEG, WebP and AVIF. With `maxBytes`, the starting quality. |
| `maxWidth` | integer | – | Maximum width in pixels. |
| `maxHeight` | integer | – | Maximum height in pixels. |
| `maxBytes` | integer | – | Target maximum file size in bytes (min 1000). JPEG, WebP, AVIF. |
| `stripMetadata` | boolean | `true` | Remove EXIF/GPS metadata. |

The full schema is in [`.actor/input_schema.json`](.actor/input_schema.json).

## Output

One dataset row per input image:

```json
{
  "sourceUrl": "https://example.com/images/hero.png",
  "target": "webp",
  "status": "ok",
  "outputUrl": "https://api.apify.com/v2/key-value-stores/<storeId>/records/<key>.webp",
  "mime": "image/webp",
  "width": 1200,
  "height": 675,
  "outputBytes": 98304,
  "input": { "format": "PNG", "width": 2400, "height": 1350, "mode": "RGBA", "sizeBytes": 528310 },
  "savedPercent": 81.4
}
```

A failed image returns `sourceUrl`, `target`, `status: "error"` and `error`, and is not charged.

## Pricing (pay per event on Apify)

| Event | Price |
|---|---|
| Image converted (per successful image) | **$0.001** ($1 per 1,000 images) |
| Actor start (per run, per GB of memory) | $0.00005 |

Same price for every format, quality and size; failed images are free. Examples: 1,000 images = $1.00; a 10,000-SKU catalog to WebP = $10.00. See the [Store page](https://apify.com/ent-e/image-converter-compressor) for current pricing.

## Development

Requires Python 3.13.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt pytest
.venv/bin/python -m pytest -q tests
```

Local run with the Apify SDK: put your input in `storage/key_value_stores/default/INPUT.json`, then:

```bash
CRAWLEE_STORAGE_DIR=./storage .venv/bin/python -m src
```

Project layout:

```
.actor/        Actor definition, input/output/dataset schemas, pay-per-event config
src/           Actor entrypoint (main.py) and Pillow conversion logic (core.py)
tests/         Unit tests for conversion, resizing and target-size compression
examples/      Sample input JSON
Dockerfile     Apify Python base image
```

## Also from ENT-E

[Media Converter for AI Agents (FFmpeg)](https://apify.com/ent-e/media-converter-ffmpeg) ([source](https://github.com/ENT-E-Pro/media-converter-ffmpeg)): MP3, Whisper-ready 16 kHz WAV, MP4, GIF and thumbnails from any media URL, at $5 per 1,000 files plus $0.002 per output minute.

## License

[MIT](LICENSE) © ENT-E. Only process images you have the rights to.
