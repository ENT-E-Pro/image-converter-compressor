import io, pytest
from PIL import Image
from src.core import convert, ConversionError, FORMATS

def img(fmt="PNG", size=(800, 600), mode="RGBA"):
    im = Image.effect_noise(size, 60).convert(mode); b = io.BytesIO(); im.save(b, fmt); return b.getvalue()

@pytest.mark.parametrize("t", list(FORMATS))
def test_targets(t):
    r = convert(img(), t); assert Image.open(io.BytesIO(r.data)).format.lower().replace("jpg","jpeg") in (t, "jpeg" if t=="jpeg" else t)

def test_resize_keeps_aspect():
    r = convert(img(), "webp", max_width=400); assert (r.width, r.height) == (400, 300)

def test_max_bytes():
    r = convert(img(mode="RGB"), "jpeg", quality=95, max_bytes=40000); assert len(r.data) <= 40000

def test_max_bytes_impossible():
    with pytest.raises(ConversionError): convert(img(mode="RGB"), "jpeg", max_bytes=1000)

def test_rgba_to_jpeg_flattens():
    assert Image.open(io.BytesIO(convert(img(), "jpg").data)).mode == "RGB"

def test_strips_exif():
    im = Image.new("RGB", (50, 50)); ex = im.getexif(); ex[0x010F] = "Cam"; b = io.BytesIO(); im.save(b, "JPEG", exif=ex)
    assert not Image.open(io.BytesIO(convert(b.getvalue(), "jpeg").data)).getexif()

def test_garbage():
    with pytest.raises(ConversionError): convert(b"not an image", "png")

def test_bad_target_and_quality():
    with pytest.raises(ConversionError): convert(img(), "bmpx")
    with pytest.raises(ConversionError): convert(img(), "webp", quality=0)
