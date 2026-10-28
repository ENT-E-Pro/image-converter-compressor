"""Apify Actor: Image Converter & Compressor for AI agents (pay-per-event)."""
import asyncio, uuid
import httpx
from apify import Actor
from .core import convert, ConversionError

MAX_DOWNLOAD = 50 * 1024**2


async def fetch(url: str) -> bytes:
    async with httpx.AsyncClient(follow_redirects=True, timeout=60) as c:
        async with c.stream("GET", url) as r:
            r.raise_for_status(); buf = bytearray()
            async for ch in r.aiter_bytes(1 << 16):
                buf += ch
                if len(buf) > MAX_DOWNLOAD: raise ConversionError("Image larger than 50 MB")
            return bytes(buf)


async def main() -> None:
    async with Actor:
        inp = await Actor.get_input() or {}
        files = list(inp.get("files") or [])
        if inp.get("url"): files.append({"url": inp["url"]})
        if not files: raise ValueError("Provide 'url' or 'files'")
        opts = {k: inp.get(k) for k in ("target", "quality", "maxWidth", "maxHeight", "maxBytes", "stripMetadata")}
        kvs = await Actor.open_key_value_store()
        for item in files:
            item = item if isinstance(item, dict) else {"url": item}
            o = {**opts, **{k: v for k, v in item.items() if k != "url"}}
            row = {"sourceUrl": item["url"], "target": o.get("target") or "webp"}
            try:
                raw = await fetch(item["url"])
                r = await asyncio.to_thread(convert, raw, row["target"], int(o.get("quality") or 80), o.get("maxWidth"),
                                            o.get("maxHeight"), o.get("maxBytes"), o.get("stripMetadata", True) is not False)
                key = f"{uuid.uuid4().hex[:12]}.{r.ext}"
                await kvs.set_value(key, r.data, content_type=r.mime)
                row.update(status="ok", outputUrl=await kvs.get_public_url(key), mime=r.mime, width=r.width,
                           height=r.height, outputBytes=len(r.data), input=r.input,
                           savedPercent=round(100 * (1 - len(r.data) / r.input["sizeBytes"]), 1))
                await Actor.push_data(row)
                ch = await Actor.charge(event_name="image-converted", count=1)
                if getattr(ch, "event_charge_limit_reached", False): break
            except Exception as e:  # error rows are free
                row.update(status="error", error=str(e)[:500]); await Actor.push_data(row)
