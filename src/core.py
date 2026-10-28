"""Image convert/resize/compress core (Pillow). No Apify dependency."""
from __future__ import annotations
import io
from dataclasses import dataclass
from PIL import Image, ImageOps, UnidentifiedImageError

Image.MAX_IMAGE_PIXELS = 100_000_000  # decompression-bomb guard
FORMATS = {"jpeg": ("jpg", "image/jpeg"), "png": ("png", "image/png"), "webp": ("webp", "image/webp"),
           "avif": ("avif", "image/avif"), "gif": ("gif", "image/gif"), "tiff": ("tiff", "image/tiff")}
LOSSY = {"jpeg", "webp", "avif"}


class ConversionError(Exception):
    pass


@dataclass
class Result:
    data: bytes
    ext: str
    mime: str
    width: int
    height: int
    input: dict


def convert(raw: bytes, target: str = "webp", quality: int = 80, max_width: int | None = None,
            max_height: int | None = None, max_bytes: int | None = None, strip_metadata: bool = True,
            background: str = "#ffffff") -> Result:
    target = target.lower().replace("jpg", "jpeg")
    if target not in FORMATS:
        raise ConversionError(f"Unsupported target '{target}'. Use: {', '.join(FORMATS)}")
    if not 1 <= quality <= 100:
        raise ConversionError("quality must be 1-100")
    try:
        im = Image.open(io.BytesIO(raw)); im.load()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as e:
        raise ConversionError(f"Not a readable image: {e}")
    info = {"format": im.format, "width": im.width, "height": im.height, "mode": im.mode, "sizeBytes": len(raw)}
    im = ImageOps.exif_transpose(im)
    if max_width or max_height:
        im.thumbnail((max_width or 10**6, max_height or 10**6), Image.LANCZOS)
    if target == "jpeg" and im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA"); bg = Image.new("RGB", im.size, background); bg.paste(im, mask=im.split()[-1]); im = bg
    elif target == "jpeg" and im.mode != "RGB":
        im = im.convert("RGB")

    def encode(q: int) -> bytes:
        buf = io.BytesIO(); kw = {}
        if target in LOSSY: kw["quality"] = q
        if target == "jpeg": kw.update(optimize=True, progressive=True)
        if target == "png": kw["optimize"] = True
        if not strip_metadata and "exif" in im.info: kw["exif"] = im.info["exif"]
        im.save(buf, format=target.upper(), **kw); return buf.getvalue()

    data = encode(quality)
    if max_bytes and len(data) > max_bytes:
        if target not in LOSSY:
            raise ConversionError("maxBytes only supported for jpeg/webp/avif")
        lo, hi, best = 5, quality - 1, None  # binary search the highest quality that fits
        while lo <= hi:
            mid = (lo + hi) // 2; d = encode(mid)
            if len(d) <= max_bytes: best, lo = d, mid + 1
            else: hi = mid - 1
        if best is None:
            raise ConversionError(f"Cannot fit under {max_bytes} bytes; also set maxWidth")
        data = best
    ext, mime = FORMATS[target]
    return Result(data, ext, mime, im.width, im.height, info)
