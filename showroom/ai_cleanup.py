"""
展間現場照片 — AI 自動去雜物

優先順序：
  1. IMAGE_PROCESSOR_URL（Node image-processor 服務）
  2. REPLICATE_API_TOKEN（SDXL img2img 直接呼叫）
  3. 本機保守軟化（無 API 時 — 走道／周邊區域柔化，無法真正移除物件）
"""
from __future__ import annotations

import base64
import io
import json
import logging
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

logger = logging.getLogger(__name__)

CLEANUP_POSITIVE_PROMPT = (
    "Professional smart factory interior photograph, remove all clutter and loose objects, "
    "no electric fans, no garbage bags, no cardboard boxes, no random tools on floor, "
    "clean empty walkways and aisles, only industrial CNC machines and production equipment remain, "
    "spotless polished factory floor, organized tidy manufacturing plant, "
    "bright even lighting, vibrant clean colors, photorealistic, same camera angle and layout"
)

CLEANUP_NEGATIVE_PROMPT = (
    "electric fan, standing fan, garbage bag, trash bag, cardboard box, clutter, mess, "
    "cables on floor, random objects, workers, people, deformed machinery, "
    "blurry, low quality, watermark, cartoon, extra equipment, hallucinated machines"
)

DEFAULT_REPLICATE_VERSION = (
    "39ed52f2a78e934b3ba6e2a89fbf45c17c114af5ee346f735020d8df092ed784"
)


def get_cleanup_provider() -> str:
    if os.getenv("IMAGE_PROCESSOR_URL"):
        return "image_processor"
    if os.getenv("REPLICATE_API_TOKEN"):
        return "replicate"
    return "local_soften"


def cleanup_factory_photo(img: Image.Image, *, strength: float = 0.38) -> tuple[Image.Image, str]:
    """
    去除現場雜物，回傳 (處理後影像, 使用的 provider)。
    失敗時回傳原圖與 provider=skipped。
    """
    provider = get_cleanup_provider()
    try:
        if provider == "image_processor":
            result = _via_image_processor(img, strength)
            if result:
                return result, "image_processor"
        elif provider == "replicate":
            result = _via_replicate(img, strength)
            if result:
                return result, "replicate"
        return _local_soften_clutter(img), "local_soften"
    except Exception as exc:
        logger.warning("AI cleanup failed (%s): %s", provider, exc)
        return _local_soften_clutter(img), "local_soften_fallback"


def cleanup_image_file(src: Path, dest: Path | None = None, *, strength: float = 0.38) -> tuple[bool, str]:
    """對檔案套用去雜物，回傳 (成功與否, provider)。"""
    if not src.is_file():
        return False, "skipped"
    out = dest or src
    try:
        with Image.open(src) as img:
            if img.mode not in ("RGB", "L"):
                img = img.convert("RGB")
            cleaned, provider = cleanup_factory_photo(img, strength=strength)
            out.parent.mkdir(parents=True, exist_ok=True)
            cleaned.save(out, format="JPEG", quality=91, optimize=True)
        return True, provider
    except Exception as exc:
        logger.warning("cleanup_image_file failed for %s: %s", src, exc)
        return False, "error"


def _resize_for_api(img: Image.Image, max_width: int = 2048) -> Image.Image:
    w, h = img.size
    if w <= max_width:
        return img
    ratio = max_width / w
    return img.resize((max_width, int(h * ratio)), Image.Resampling.LANCZOS)


def _image_to_data_uri(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=88)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/jpeg;base64,{b64}"


def _download_url(url: str) -> Image.Image:
    with urllib.request.urlopen(url, timeout=120) as resp:
        data = resp.read()
    with Image.open(io.BytesIO(data)) as img:
        return img.convert("RGB")


def _via_image_processor(img: Image.Image, strength: float) -> Image.Image | None:
    processor = os.getenv("IMAGE_PROCESSOR_URL", "").rstrip("/")
    if not processor:
        return None

    from django.conf import settings

    # 暫存供 Node 服務以公開 URL 讀取（開發環境）
    tmp_dir = Path(settings.MEDIA_ROOT) / "_cleanup_tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    tmp_path = tmp_dir / f"cleanup_{int(time.time() * 1000)}.jpg"
    api_img = _resize_for_api(img)
    api_img.save(tmp_path, format="JPEG", quality=88)

    base = os.getenv("SHOWROOM_PUBLIC_BASE_URL", "http://127.0.0.1:9000").rstrip("/")
    rel = tmp_path.relative_to(settings.MEDIA_ROOT).as_posix()
    public_url = f"{base}/media/{rel}"

    payload = json.dumps({
        "imageUrl": public_url,
        "provider": os.getenv("IMAGE_PROCESSOR_PROVIDER", "replicate"),
        "strength": strength,
        "removeClutter": True,
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{processor}/api/v1/process/url",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            data = json.loads(resp.read().decode())
            if data.get("success") and data.get("enhancedImageUrl"):
                result = _download_url(data["enhancedImageUrl"])
                tmp_path.unlink(missing_ok=True)
                return result
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        logger.warning("IMAGE_PROCESSOR_URL failed: %s", exc)
    tmp_path.unlink(missing_ok=True)
    return None


def _replicate_create_prediction(token: str, version: str, input_data: dict) -> dict:
    headers = {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json",
    }
    body = json.dumps({"version": version, "input": input_data}).encode("utf-8")
    req = urllib.request.Request(
        "https://api.replicate.com/v1/predictions",
        data=body,
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode())


def _replicate_poll_prediction(token: str, prediction_id: str, timeout: int = 300) -> dict:
    headers = {"Authorization": f"Token {token}"}
    deadline = time.time() + timeout
    while time.time() < deadline:
        req = urllib.request.Request(
            f"https://api.replicate.com/v1/predictions/{prediction_id}",
            headers=headers,
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode())
        status = data.get("status")
        if status == "succeeded":
            return data
        if status in ("failed", "canceled"):
            raise RuntimeError(data.get("error", f"prediction {status}"))
        time.sleep(2)
    raise TimeoutError(f"Replicate prediction {prediction_id} timed out")


def _extract_replicate_output(output) -> str:
    if isinstance(output, str):
        return output
    if isinstance(output, list) and output:
        return str(output[0])
    raise RuntimeError("Unexpected Replicate output shape")


def _via_replicate(img: Image.Image, strength: float) -> Image.Image | None:
    token = os.getenv("REPLICATE_API_TOKEN")
    if not token:
        return None

    model_env = os.getenv("REPLICATE_MODEL", "")
    version = model_env.split(":")[-1] if ":" in model_env else DEFAULT_REPLICATE_VERSION

    api_img = _resize_for_api(img)
    input_data = {
        "image": _image_to_data_uri(api_img),
        "prompt": CLEANUP_POSITIVE_PROMPT,
        "negative_prompt": CLEANUP_NEGATIVE_PROMPT,
        "prompt_strength": strength,
        "num_inference_steps": 28,
        "guidance_scale": 7.5,
        "scheduler": "K_EULER",
        "refine": "no_refiner",
    }

    pred = _replicate_create_prediction(token, version, input_data)
    result = _replicate_poll_prediction(token, pred["id"])
    url = _extract_replicate_output(result.get("output"))
    cleaned = _download_url(url)

    # 若 API 有縮圖，放大回原尺寸
    if cleaned.size != img.size:
        cleaned = cleaned.resize(img.size, Image.Resampling.LANCZOS)
    return cleaned


def _local_soften_clutter(img: Image.Image) -> Image.Image:
    """
    無 API 時的保守本機處理：
    走道（下方）與周邊區域柔化，降低雜物視覺干擾，保留中央機台清晰。
    """
    img = img.convert("RGB")
    w, h = img.size
    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)

    # 走道／地面區域 — 較強清理
    draw.rectangle([0, int(h * 0.62), w, h], fill=220)
    # 左右周邊
    draw.rectangle([0, 0, int(w * 0.12), h], fill=160)
    draw.rectangle([int(w * 0.88), 0, w, h], fill=160)
    # 上方背景
    draw.rectangle([0, 0, w, int(h * 0.18)], fill=120)

    mask = mask.filter(ImageFilter.GaussianBlur(radius=max(12, int(min(w, h) * 0.03))))

    softened = img.filter(ImageFilter.GaussianBlur(radius=2.2))
    softened = ImageEnhance.Brightness(softened).enhance(1.04)
    median = img.filter(ImageFilter.MedianFilter(size=5))
    blended_soft = Image.blend(softened, median, 0.35)

    return Image.composite(blended_soft, img, mask)
