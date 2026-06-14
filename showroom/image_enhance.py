"""
展間現場照片 — 科技美顏強化（明亮、乾淨、冷色科技感）

類似美顏邏輯：柔化雜訊、提亮陰影、冷色調、清晰細節，適用於工廠環景實拍。
tech_vivid：色彩鮮艷、明亮有質感，自動修復偏暗/過曝畫面。
tech_pristine：整齊明亮乾淨有序（推薦）— 均勻光感、修復不理想現場，仍保留原圖輪廓。
"""
from __future__ import annotations

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageOps, ImageStat

PRESETS = {
    "tech_clean": {
        "smooth_blend": 0.20,
        "smooth_radius": 1.0,
        "autocontrast_cutoff": 0.7,
        "brightness": 1.11,
        "contrast": 1.07,
        "color": 1.10,
        "warm_reduce": 0.93,
        "blue_boost": 1.07,
        "green_boost": 1.0,
        "haze_rgb": (238, 244, 252),
        "haze_blend": 0.07,
        "sharpness": 1.10,
        "unsharp_radius": 1.4,
        "unsharp_percent": 115,
        "vignette": 0.0,
        "gamma": 1.0,
    },
    "tech_strong": {
        "smooth_blend": 0.28,
        "smooth_radius": 1.4,
        "autocontrast_cutoff": 1.0,
        "brightness": 1.15,
        "contrast": 1.10,
        "color": 1.14,
        "warm_reduce": 0.90,
        "blue_boost": 1.10,
        "green_boost": 1.02,
        "haze_rgb": (240, 246, 255),
        "haze_blend": 0.10,
        "sharpness": 1.12,
        "unsharp_radius": 1.6,
        "unsharp_percent": 125,
        "vignette": 0.12,
        "gamma": 0.96,
    },
    "tech_cyber": {
        "smooth_blend": 0.34,
        "smooth_radius": 1.7,
        "autocontrast_cutoff": 1.2,
        "brightness": 1.20,
        "contrast": 1.16,
        "color": 1.20,
        "warm_reduce": 0.84,
        "blue_boost": 1.16,
        "green_boost": 1.05,
        "haze_rgb": (210, 235, 255),
        "haze_blend": 0.14,
        "sharpness": 1.18,
        "unsharp_radius": 2.0,
        "unsharp_percent": 150,
        "vignette": 0.32,
        "gamma": 0.90,
    },
    "tech_refined": {
        "smooth_blend": 0.14,
        "smooth_radius": 0.8,
        "autocontrast_cutoff": 0.5,
        "brightness": 1.08,
        "contrast": 1.05,
        "color": 1.06,
        "warm_reduce": 0.96,
        "blue_boost": 1.04,
        "green_boost": 1.01,
        "haze_rgb": (248, 250, 254),
        "haze_blend": 0.04,
        "sharpness": 1.14,
        "unsharp_radius": 1.2,
        "unsharp_percent": 130,
        "vignette": 0.08,
        "gamma": 0.98,
    },
    "tech_industrial": {
        "smooth_blend": 0.08,
        "smooth_radius": 0.5,
        "autocontrast_cutoff": 1.6,
        "brightness": 0.92,
        "contrast": 1.28,
        "color": 0.36,
        "warm_reduce": 0.84,
        "blue_boost": 0.95,
        "green_boost": 0.92,
        "haze_rgb": (24, 26, 30),
        "haze_blend": 0.09,
        "sharpness": 1.24,
        "unsharp_radius": 2.1,
        "unsharp_percent": 175,
        "vignette": 0.44,
        "vignette_rgb": (6, 6, 8),
        "gamma": 0.84,
        "luma_desaturate": 0.52,
        "red_preserve": 0.12,
    },
    "tech_vivid": {
        "smooth_blend": 0.18,
        "smooth_radius": 1.0,
        "autocontrast_cutoff": 0.85,
        "brightness": 1.10,
        "contrast": 1.11,
        "color": 1.20,
        "warm_reduce": 0.96,
        "blue_boost": 1.09,
        "green_boost": 1.05,
        "haze_rgb": (248, 250, 255),
        "haze_blend": 0.05,
        "sharpness": 1.16,
        "unsharp_radius": 1.5,
        "unsharp_percent": 142,
        "vignette": 0.10,
        "vignette_rgb": (10, 18, 32),
        "gamma": 0.97,
        "shadow_lift": 0.24,
        "highlight_recover": 0.16,
        "auto_exposure": True,
    },
    "tech_pristine": {
        "smooth_blend": 0.26,
        "smooth_radius": 1.25,
        "autocontrast_cutoff": 0.55,
        "brightness": 1.14,
        "contrast": 1.06,
        "color": 1.10,
        "warm_reduce": 0.93,
        "blue_boost": 1.05,
        "green_boost": 1.02,
        "haze_rgb": (252, 253, 255),
        "haze_blend": 0.09,
        "sharpness": 1.12,
        "unsharp_radius": 1.25,
        "unsharp_percent": 118,
        "vignette": 0.03,
        "vignette_rgb": (248, 250, 254),
        "gamma": 1.03,
        "shadow_lift": 0.34,
        "highlight_recover": 0.22,
        "auto_exposure": True,
        "neutral_balance": 0.40,
        "even_tones": 0.24,
        "original_blend": 0.15,
    },
    "tech_showroom": {
        "smooth_blend": 0.24,
        "smooth_radius": 1.2,
        "autocontrast_cutoff": 0.6,
        "brightness": 1.15,
        "contrast": 1.08,
        "color": 1.18,
        "warm_reduce": 0.94,
        "blue_boost": 1.07,
        "green_boost": 1.04,
        "haze_rgb": (252, 253, 255),
        "haze_blend": 0.08,
        "sharpness": 1.14,
        "unsharp_radius": 1.35,
        "unsharp_percent": 125,
        "vignette": 0.02,
        "vignette_rgb": (248, 250, 254),
        "gamma": 1.02,
        "shadow_lift": 0.30,
        "highlight_recover": 0.20,
        "auto_exposure": True,
        "neutral_balance": 0.35,
        "even_tones": 0.22,
        "original_blend": 0.12,
    },
    "tech_matterport": {
        "smooth_blend": 0.16,
        "smooth_radius": 0.9,
        "autocontrast_cutoff": 0.75,
        "brightness": 1.12,
        "contrast": 1.14,
        "color": 1.08,
        "warm_reduce": 0.90,
        "blue_boost": 1.10,
        "green_boost": 0.98,
        "haze_rgb": (235, 242, 252),
        "haze_blend": 0.06,
        "sharpness": 1.20,
        "unsharp_radius": 1.5,
        "unsharp_percent": 140,
        "vignette": 0.14,
        "vignette_rgb": (12, 22, 38),
        "gamma": 0.98,
        "shadow_lift": 0.28,
        "highlight_recover": 0.18,
        "auto_exposure": True,
        "neutral_balance": 0.42,
        "even_tones": 0.18,
        "original_blend": 0.10,
    },
    "tech_matterport_pro": {
        "smooth_blend": 0.10,
        "smooth_radius": 0.65,
        "autocontrast_cutoff": 1.1,
        "brightness": 1.18,
        "contrast": 1.24,
        "color": 1.16,
        "warm_reduce": 0.82,
        "blue_boost": 1.16,
        "green_boost": 0.94,
        "haze_rgb": (200, 220, 248),
        "haze_blend": 0.10,
        "sharpness": 1.32,
        "unsharp_radius": 2.0,
        "unsharp_percent": 175,
        "vignette": 0.24,
        "vignette_rgb": (6, 14, 30),
        "gamma": 0.92,
        "shadow_lift": 0.38,
        "highlight_recover": 0.24,
        "auto_exposure": True,
        "neutral_balance": 0.52,
        "even_tones": 0.26,
        "original_blend": 0.05,
        "metallic_sheen": 0.22,
        "cyan_accent": 0.14,
        "clarity": 0.20,
    },
    "tech_bright_white": {
        "minimal_global": True,
        "smooth_blend": 0.0,
        "smooth_radius": 0.0,
        "autocontrast_cutoff": 0.0,
        "brightness": 1.0,
        "contrast": 1.0,
        "color": 1.0,
        "warm_reduce": 1.0,
        "blue_boost": 1.0,
        "green_boost": 1.0,
        "haze_rgb": (252, 253, 255),
        "haze_blend": 0.0,
        "sharpness": 1.0,
        "unsharp_radius": 1.0,
        "unsharp_percent": 100,
        "vignette": 0.0,
        "gamma": 1.0,
        "shadow_lift": 0.0,
        "highlight_recover": 0.0,
        "auto_exposure": True,
        "neutral_balance": 0.0,
        "even_tones": 0.0,
        "original_blend": 0.0,
        "metallic_sheen": 0.0,
        "cyan_accent": 0.0,
        "clarity": 0.0,
        "bg_whiten": 0.0,
        "bg_soften": 0.48,
        "bg_whiten_floor": 94,
        "equipment_pop": 0.0,
        "equipment_depth": 0.0,
        "subject_preserve": 1.0,
        "subject_sharp_blend": 0.0,
    },
}


def _apply_gamma(img: Image.Image, gamma: float) -> Image.Image:
    if abs(gamma - 1.0) < 0.01:
        return img
    inv = 1.0 / gamma
    table = [min(255, int((i / 255.0) ** inv * 255)) for i in range(256)]
    return img.point(lambda x, t=table: t[x])


def _apply_luma_desaturate(img: Image.Image, amount: float) -> Image.Image:
    if amount <= 0:
        return img
    gray = img.convert("L").convert("RGB")
    return Image.blend(img, gray, min(1.0, amount))


def _apply_red_preserve(img: Image.Image, strength: float) -> Image.Image:
    """保留安全標示等紅色元素，避免全幅消色後完全灰化。"""
    if strength <= 0:
        return img
    r, g, b = img.split()
    r = r.point(lambda x, s=strength: min(255, int(x * (1.0 + s) + 4)))
    return Image.merge("RGB", (r, g, b))


def _apply_vignette(img: Image.Image, strength: float, tint_rgb=(8, 18, 40)) -> Image.Image:
    if strength <= 0:
        return img
    w, h = img.size
    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    margin_x, margin_y = int(w * 0.04), int(h * 0.04)
    draw.ellipse(
        [margin_x, margin_y, w - margin_x, h - margin_y],
        fill=255,
    )
    blur = max(8, int(min(w, h) * 0.20))
    mask = mask.filter(ImageFilter.GaussianBlur(radius=blur))
    inv = ImageOps.invert(mask)
    tint = Image.new("RGB", (w, h), tint_rgb)
    overlay = Image.composite(tint, Image.new("RGB", (w, h), (0, 0, 0)), inv)
    return Image.blend(img, overlay, strength)


def _apply_shadow_lift(img: Image.Image, amount: float) -> Image.Image:
    """提亮陰影區，修復現場偏暗畫面。"""
    if amount <= 0:
        return img
    lum = img.convert("L")
    mask = lum.point(lambda x, a=amount: min(255, int((255 - x) * a * 1.1)))
    lifted = ImageEnhance.Brightness(img).enhance(1.18)
    lifted = ImageEnhance.Color(lifted).enhance(1.04)
    return Image.composite(lifted, img, mask)


def _apply_highlight_recover(img: Image.Image, amount: float) -> Image.Image:
    """柔化過曝高光，避免白場死白。"""
    if amount <= 0:
        return img
    lum = img.convert("L")
    mask = lum.point(lambda x, a=amount: min(255, int(max(0, x - 198) * a * 4.5)))
    softened = ImageEnhance.Brightness(img).enhance(0.90)
    softened = ImageEnhance.Contrast(softened).enhance(0.96)
    return Image.composite(softened, img, mask)


def _apply_auto_exposure(img: Image.Image, enabled: bool) -> Image.Image:
    """依整體亮度自動微調曝光。"""
    if not enabled:
        return img
    lum = img.convert("L")
    hist = lum.histogram()
    total = sum(hist) or 1
    mean = sum(i * c for i, c in enumerate(hist)) / total
    if mean < 95:
        img = ImageEnhance.Brightness(img).enhance(1.08 + (95 - mean) / 400)
    elif mean > 175:
        img = ImageEnhance.Brightness(img).enhance(0.94 - (mean - 175) / 500)
    return img


def _apply_neutral_balance(img: Image.Image, strength: float) -> Image.Image:
    """灰世界白平衡 — 減少偏黃/偏綠，讓現場看起來更乾淨一致。"""
    if strength <= 0:
        return img
    stat = ImageStat.Stat(img)
    avgs = stat.mean[:3]
    gray = sum(avgs) / 3.0
    if gray < 1:
        return img
    r, g, b = img.split()
    scales = [gray / max(a, 1.0) for a in avgs]

    def _shift(ch, scale, s=strength):
        return ch.point(lambda x, sc=scale, st=s: min(255, int(x * (1 - st) + x * sc * st)))

    return Image.merge("RGB", (
        _shift(r, scales[0]),
        _shift(g, scales[1]),
        _shift(b, scales[2]),
    ))


def _apply_even_tones(img: Image.Image, amount: float) -> Image.Image:
    """均勻中間調，讓畫面光感更整齊有序。"""
    if amount <= 0:
        return img
    lut = []
    for i in range(256):
        x = i / 255.0
        lift = amount * (0.28 * x * (1.0 - x) + 0.06)
        y = min(1.0, max(0.0, x + lift - amount * 0.04 * (x - 0.5) ** 2))
        lut.append(int(y * 255))
    return img.point(lambda i, t=lut: t[i])


def _apply_metallic_sheen(img: Image.Image, strength: float) -> Image.Image:
    """高光區域疊加冷色金屬反光。"""
    if strength <= 0:
        return img
    lum = img.convert("L")
    mask = lum.point(lambda x, s=strength: min(255, int(max(0, x - 145) * s * 2.2)))
    sheen = Image.new("RGB", img.size, (180, 210, 245))
    bright = ImageEnhance.Brightness(sheen).enhance(1.15)
    return Image.composite(bright, img, mask)


def _apply_cyan_accent(img: Image.Image, strength: float) -> Image.Image:
    """中間調注入青色科技光感。"""
    if strength <= 0:
        return img
    lum = img.convert("L")
    mask = lum.point(lambda x, s=strength: min(255, int(s * 255 * (1.0 - abs(x - 128) / 128.0) * 0.55)))
    accent = Image.new("RGB", img.size, (0, 220, 255))
    return Image.composite(accent, img, mask)


def _apply_clarity(img: Image.Image, amount: float) -> Image.Image:
    """局部對比清晰度 — 強化材質細節。"""
    if amount <= 0:
        return img
    radius = 1.2 + amount * 1.5
    percent = int(100 + amount * 280)
    sharp = img.filter(ImageFilter.UnsharpMask(radius=radius, percent=percent, threshold=1))
    return Image.blend(img, sharp, min(0.72, amount * 2.8))


def _apply_background_whiten(
    img: Image.Image,
    strength: float,
    lum_floor: int = 90,
    white_rgb=(252, 253, 255),
) -> Image.Image:
    """亮區且低彩度（牆面、地面、天花板）推向亮白，保留設備本體色彩。"""
    if strength <= 0:
        return img
    lum = img.convert("L")
    r, g, b = img.split()
    max_c = ImageChops.lighter(ImageChops.lighter(r, g), b)
    min_c = ImageChops.darker(ImageChops.darker(r, g), b)
    spread = ImageChops.subtract(max_c, min_c)

    lum_mask = lum.point(lambda x, f=lum_floor: max(0, min(255, int((x - f) * 2.4))))
    sat_mask = spread.point(lambda x: max(0, min(255, 255 - int(x * 3.2))))
    combined = ImageChops.multiply(lum_mask, sat_mask)
    combined = combined.point(lambda x, s=strength: min(255, int(x * s)))

    white = Image.new("RGB", img.size, white_rgb)
    return Image.composite(white, img, combined)


def _apply_equipment_pop(img: Image.Image, strength: float) -> Image.Image:
    """暗部設備略增飽和與對比，避免被白底沖淡。"""
    if strength <= 0:
        return img
    lum = img.convert("L")
    mask = lum.point(lambda x, s=strength: min(255, int(max(0, 175 - x) * s * 2.2)))
    vivid = ImageEnhance.Color(img).enhance(1.0 + strength * 0.65)
    vivid = ImageEnhance.Contrast(vivid).enhance(1.0 + strength * 0.12)
    return Image.composite(vivid, img, mask)


def _equipment_subject_mask(img: Image.Image, strength: float) -> Image.Image:
    """設備遮罩：暗部機台 + 有色彩的中間調。"""
    lum = img.convert("L")
    r, g, b = img.split()
    max_c = ImageChops.lighter(ImageChops.lighter(r, g), b)
    min_c = ImageChops.darker(ImageChops.darker(r, g), b)
    spread = ImageChops.subtract(max_c, min_c)

    dark = lum.point(lambda x, s=strength: min(255, int(max(0, 195 - x) * s * 2.1)))
    mid = lum.point(lambda x, s=strength: min(255, int(max(0, min(x, 215) - 38) * s * 1.3)))
    color = spread.point(lambda x, s=strength: min(255, int(max(28, x) * s * 1.4)))
    mid_color = ImageChops.multiply(mid, color)
    combined = ImageChops.lighter(dark, mid_color)
    return combined.point(lambda x: min(255, x))


def _background_mask(img: Image.Image, strength: float = 1.0) -> Image.Image:
    """背景遮罩（設備遮罩的反相，邊緣柔化）。"""
    subject = _equipment_subject_mask(img, strength)
    bg = subject.point(lambda x: max(0, 255 - x))
    return bg.filter(ImageFilter.GaussianBlur(radius=2.8))


def _apply_background_soften(
    img: Image.Image,
    strength: float,
    lum_floor: int = 90,
    white_rgb=(252, 253, 255),
    reference: Image.Image | None = None,
) -> Image.Image:
    """背景淡化：降飽和、略提亮、偏亮白，設備區不處理。"""
    if strength <= 0:
        return img
    ref = reference or img
    bg = _background_mask(ref, 1.0)
    lum = ref.convert("L")
    r, g, b = img.split()
    max_c = ImageChops.lighter(ImageChops.lighter(r, g), b)
    min_c = ImageChops.darker(ImageChops.darker(r, g), b)
    spread = ImageChops.subtract(max_c, min_c)
    lum_boost = lum.point(lambda x, f=lum_floor: max(0, min(255, int((x - f) * 1.6))))
    bg = ImageChops.multiply(bg, lum_boost)
    bg = ImageChops.multiply(
        bg,
        spread.point(lambda x: max(0, min(255, 255 - int(x * 2.8)))),
    )
    bg = bg.point(lambda x, s=strength: min(255, int(x * s)))

    gray = img.convert("L").convert("RGB")
    faded = Image.blend(img, gray, 0.38)
    faded = ImageEnhance.Brightness(faded).enhance(1.08)
    white = Image.new("RGB", img.size, white_rgb)
    softened = Image.blend(faded, white, 0.22)
    return Image.composite(softened, img, bg)


def _apply_natural_subject_preserve(
    processed: Image.Image,
    original: Image.Image,
    preserve: float,
    sharp_blend: float = 0.45,
) -> Image.Image:
    """設備區還原原圖像素；preserve≥0.99 時 100% 使用原圖。"""
    if preserve <= 0:
        return processed
    mask = _equipment_subject_mask(original, 1.0)
    mask = mask.point(lambda x, p=preserve: min(255, int(x * p)))
    mask = mask.filter(ImageFilter.GaussianBlur(radius=0.45))

    if preserve >= 0.99:
        subject = original.copy()
    else:
        sharp = original.filter(
            ImageFilter.UnsharpMask(radius=1.2, percent=140, threshold=1),
        )
        sharp = ImageEnhance.Sharpness(sharp).enhance(1.12)
        subject = Image.blend(original, sharp, min(0.65, sharp_blend))
    return Image.composite(subject, processed, mask)


def _apply_equipment_depth(img: Image.Image, strength: float) -> Image.Image:
    """舊版立體強化（非 tech_bright_white 預設使用）。"""
    if strength <= 0:
        return img
    mask = _equipment_subject_mask(img, strength)
    vivid = ImageEnhance.Color(img).enhance(1.0 + strength * 0.5)
    punch = ImageEnhance.Contrast(vivid).enhance(1.0 + strength * 0.2)
    return Image.composite(punch, img, mask)


def enhance_showroom_photo(img: Image.Image, preset: str = "tech_clean") -> Image.Image:
    """將一般現場照強化為明亮乾淨的科技感環景基底"""
    cfg = PRESETS.get(preset, PRESETS["tech_clean"])
    img = img.convert("RGB")
    original = img.copy()

    if cfg.get("minimal_global"):
        img = original.copy()
        if cfg.get("auto_exposure"):
            img = _apply_auto_exposure(img, True)
        bg_soften = cfg.get("bg_soften", 0.0)
        if bg_soften:
            img = _apply_background_soften(
                img,
                bg_soften,
                lum_floor=int(cfg.get("bg_whiten_floor", 90)),
                reference=original,
            )
        subject_preserve = cfg.get("subject_preserve", 0.0)
        if subject_preserve:
            img = _apply_natural_subject_preserve(
                img,
                original,
                subject_preserve,
                sharp_blend=float(cfg.get("subject_sharp_blend", 0.45)),
            )
        return img

    smooth = img.filter(ImageFilter.GaussianBlur(radius=cfg["smooth_radius"]))
    img = Image.blend(img, smooth, cfg["smooth_blend"])

    img = ImageOps.autocontrast(img, cutoff=cfg["autocontrast_cutoff"])
    img = _apply_gamma(img, cfg.get("gamma", 1.0))
    img = ImageEnhance.Brightness(img).enhance(cfg["brightness"])
    img = ImageEnhance.Contrast(img).enhance(cfg["contrast"])

    shadow = cfg.get("shadow_lift", 0.0)
    if shadow:
        img = _apply_shadow_lift(img, shadow)
    highlight = cfg.get("highlight_recover", 0.0)
    if highlight:
        img = _apply_highlight_recover(img, highlight)
    if cfg.get("auto_exposure"):
        img = _apply_auto_exposure(img, True)

    neutral = cfg.get("neutral_balance", 0.0)
    if neutral:
        img = _apply_neutral_balance(img, neutral)

    even = cfg.get("even_tones", 0.0)
    if even:
        img = _apply_even_tones(img, even)

    r, g, b = img.split()
    wr = cfg["warm_reduce"]
    bb = cfg["blue_boost"]
    gb = cfg.get("green_boost", 1.0)
    r = r.point(lambda x, w=wr: min(255, int(x * w + 4)))
    g = g.point(lambda x, boost=gb: min(255, int(x * boost + 8)))
    b = b.point(lambda x, boost=bb: min(255, int(x * boost + 16)))
    img = Image.merge("RGB", (r, g, b))

    img = ImageEnhance.Color(img).enhance(cfg["color"])

    luma = cfg.get("luma_desaturate", 0.0)
    if luma:
        img = _apply_luma_desaturate(img, luma)

    red_keep = cfg.get("red_preserve", 0.0)
    if red_keep:
        img = _apply_red_preserve(img, red_keep)

    img = img.filter(
        ImageFilter.UnsharpMask(
            radius=cfg["unsharp_radius"],
            percent=cfg["unsharp_percent"],
            threshold=2,
        )
    )
    img = ImageEnhance.Sharpness(img).enhance(cfg["sharpness"])

    metallic = cfg.get("metallic_sheen", 0.0)
    if metallic:
        img = _apply_metallic_sheen(img, metallic)

    cyan = cfg.get("cyan_accent", 0.0)
    if cyan:
        img = _apply_cyan_accent(img, cyan)

    clarity = cfg.get("clarity", 0.0)
    if clarity:
        img = _apply_clarity(img, clarity)

    bg_whiten = cfg.get("bg_whiten", 0.0)
    if bg_whiten:
        img = _apply_background_whiten(
            img,
            bg_whiten,
            lum_floor=int(cfg.get("bg_whiten_floor", 90)),
        )

    bg_soften = cfg.get("bg_soften", 0.0)
    if bg_soften:
        img = _apply_background_soften(
            img,
            bg_soften,
            lum_floor=int(cfg.get("bg_whiten_floor", 90)),
        )

    equip_pop = cfg.get("equipment_pop", 0.0)
    if equip_pop:
        img = _apply_equipment_pop(img, equip_pop)

    equip_depth = cfg.get("equipment_depth", 0.0)
    if equip_depth:
        img = _apply_equipment_depth(img, equip_depth)

    subject_preserve = cfg.get("subject_preserve", 0.0)
    if subject_preserve:
        img = _apply_natural_subject_preserve(
            img,
            original,
            subject_preserve,
            sharp_blend=float(cfg.get("subject_sharp_blend", 0.45)),
        )

    haze = Image.new("RGB", img.size, cfg["haze_rgb"])
    img = Image.blend(img, haze, cfg["haze_blend"])

    img = _apply_vignette(
        img,
        cfg.get("vignette", 0.0),
        tint_rgb=cfg.get("vignette_rgb", (8, 18, 40)),
    )

    blend = cfg.get("original_blend", 0.0)
    if blend:
        img = Image.blend(img, original, min(0.35, blend))

    return img
