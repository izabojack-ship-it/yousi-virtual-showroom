"""
優思國際雲端虛擬展間 — 資料模型

對應方案規劃：
- 展間站點設定（企業識別、多語系、社群連結）
- 分區導覽（形象區、設備展示區）
- 360 場景 / 平面導覽熱點
- 產品設備詳情（3D、AR、影片、型錄）
- 線上諮詢
"""
import re

from django.conf import settings
from django.db import models
from django.utils.text import slugify


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField("建立時間", auto_now_add=True)
    updated_at = models.DateTimeField("更新時間", auto_now=True)

    class Meta:
        abstract = True


class ShowroomSite(TimeStampedModel):
    """展間全域設定（單站或多品牌）"""

    name = models.CharField("展間名稱", max_length=120)
    slug = models.SlugField("代碼", unique=True, max_length=80)
    tagline = models.CharField("標語", max_length=200, blank=True)
    description = models.TextField("簡介", blank=True)
    logo = models.ImageField("Logo", upload_to="branding/", blank=True, null=True)
    hero_image = models.ImageField("首頁主視覺", upload_to="branding/", blank=True, null=True)
    primary_color = models.CharField("主色", max_length=7, default="#1a4d8c")
    accent_color = models.CharField("強調色", max_length=7, default="#e8a317")
    background_style = models.CharField(
        "背景風格",
        max_length=20,
        choices=[("light", "明亮"), ("dark", "深色"), ("gradient", "漸層")],
        default="light",
    )
    website_url = models.URLField("官網", blank=True)
    facebook_url = models.URLField("Facebook", blank=True)
    instagram_url = models.URLField("Instagram", blank=True)
    linkedin_url = models.URLField("LinkedIn", blank=True)
    youtube_url = models.URLField("YouTube", blank=True)
    line_url = models.URLField("LINE", blank=True)
    contact_email = models.EmailField("聯絡信箱", blank=True)
    contact_phone = models.CharField("聯絡電話", max_length=40, blank=True)
    inquiry_enabled = models.BooleanField("開啟線上諮詢", default=True)
    share_title = models.CharField("分享標題", max_length=120, blank=True)
    share_description = models.CharField("分享描述", max_length=300, blank=True)
    is_active = models.BooleanField("啟用", default=True)
    is_default = models.BooleanField("預設展間", default=False)

    class Meta:
        verbose_name = "展間站點"
        verbose_name_plural = "展間站點"
        ordering = ["-is_default", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name) or "showroom"
        if self.is_default:
            ShowroomSite.objects.filter(is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


class LocalizedText(TimeStampedModel):
    """多語系文字（展間文案、操作說明等）"""

    site = models.ForeignKey(ShowroomSite, on_delete=models.CASCADE, related_name="texts")
    key = models.CharField("鍵值", max_length=80)
    lang = models.CharField("語系", max_length=10, choices=[("zh-hant", "繁中"), ("en", "英文"), ("ja", "日文")])
    value = models.TextField("內容")

    class Meta:
        verbose_name = "多語系文案"
        verbose_name_plural = "多語系文案"
        unique_together = [("site", "key", "lang")]
        ordering = ["key", "lang"]

    def __str__(self):
        return f"{self.key} ({self.lang})"


class ShowroomLevel(TimeStampedModel):
    """
    展間空間層級（Level 1~3 拓撲）
    Level 1：品牌迎賓大廳
    Level 2：雙廠區樞紐（台灣廠 / 越南廠）
    Level 3：深度製程展區（管理、研發、製造、機台）
    """

    LEVEL_TYPES = [
        ("lobby", "Level 1 — 品牌迎賓大廳"),
        ("factory_hub", "Level 2 — 雙廠區樞紐"),
        ("process_deep", "Level 3 — 深度製程展區"),
    ]

    site = models.ForeignKey(ShowroomSite, on_delete=models.CASCADE, related_name="levels")
    level_number = models.PositiveSmallIntegerField(
        "層級編號", default=1, help_text="1=迎賓大廳、2=廠區樞紐、3=製程展區"
    )
    level_type = models.CharField("層級類型", max_length=20, choices=LEVEL_TYPES, default="lobby")
    slug = models.SlugField("代碼", max_length=80)
    name_zh = models.CharField("名稱（繁中）", max_length=120)
    name_en = models.CharField("名稱（英文）", max_length=120, blank=True)
    name_ja = models.CharField("名稱（日文）", max_length=120, blank=True)
    summary_zh = models.TextField("摘要（繁中）", blank=True)
    summary_en = models.TextField("摘要（英文）", blank=True)
    summary_ja = models.TextField("摘要（日文）", blank=True)
    cover_image = models.ImageField("封面圖", upload_to="levels/", blank=True, null=True)
    floor_plan_image = models.ImageField(
        "全景地圖", upload_to="levels/floorplans/", blank=True, null=True,
        help_text="展間平面導覽圖，供導覽列「當前位置」標示"
    )
    panorama_image = models.ImageField("360 全景圖", upload_to="levels/panorama/", blank=True, null=True)
    panorama_embed_url = models.URLField("外部 360 導覽連結", blank=True)
    sort_order = models.PositiveIntegerField("排序", default=0)
    is_active = models.BooleanField("啟用", default=True)
    # 預留 AI 多語系翻譯接口：後端可依 key 自動填入 name/summary 各語系欄位
    ai_translation_key = models.CharField(
        "AI 翻譯鍵值", max_length=80, blank=True,
        help_text="供未來 AI 多語系翻譯系統對應的內容鍵值"
    )

    class Meta:
        verbose_name = "展間層級"
        verbose_name_plural = "展間層級"
        unique_together = [("site", "slug")]
        ordering = ["sort_order", "level_number"]

    def __str__(self):
        return f"L{self.level_number} — {self.name_zh}"

    def localized(self, field_base, lang="zh-hant"):
        """依語系取得欄位值（預留 AI 翻譯覆寫入口）"""
        suffix = {"en": "_en", "ja": "_ja"}.get(lang, "_zh")
        return getattr(self, f"{field_base}{suffix}", "") or getattr(self, f"{field_base}_zh", "")


class FactoryPlant(TimeStampedModel):
    """
    廠區節點（Level 2 雙廠區樞紐）
    台灣廠：實地取景；越南廠：數位重構（PPT / 圖片資產）
    """

    PLANT_TYPES = [
        ("taiwan", "台灣廠（實地取景）"),
        ("vietnam", "越南廠（數位重構）"),
    ]

    site = models.ForeignKey(ShowroomSite, on_delete=models.CASCADE, related_name="plants")
    level = models.ForeignKey(
        ShowroomLevel, on_delete=models.CASCADE, related_name="plants",
        help_text="通常掛載於 Level 2 廠區樞紐"
    )
    plant_type = models.CharField("廠區類型", max_length=20, choices=PLANT_TYPES, default="taiwan")
    slug = models.SlugField("代碼", max_length=80)
    name_zh = models.CharField("名稱（繁中）", max_length=120)
    name_en = models.CharField("名稱（英文）", max_length=120, blank=True)
    name_ja = models.CharField("名稱（日文）", max_length=120, blank=True)
    description_zh = models.TextField("介紹（繁中）", blank=True)
    description_en = models.TextField("介紹（英文）", blank=True)
    description_ja = models.TextField("介紹（日文）", blank=True)
    cover_image = models.ImageField("封面圖", upload_to="plants/", blank=True, null=True)
    panorama_image = models.ImageField("360 全景圖", upload_to="plants/panorama/", blank=True, null=True)
    panorama_embed_url = models.URLField("外部 360 導覽連結", blank=True)
    asset_gallery = models.JSONField(
        "廠區資產庫", default=list, blank=True,
        help_text="越南廠 PPT 截圖、現場照片等路徑列表，供後台上傳管理"
    )
    audio_guide = models.FileField(
        "環境語音導覽", upload_to="plants/audio/", blank=True, null=True,
        help_text="廠區環境介紹音檔（MP3/M4A）"
    )
    sort_order = models.PositiveIntegerField("排序", default=0)
    is_active = models.BooleanField("啟用", default=True)
    ai_translation_key = models.CharField("AI 翻譯鍵值", max_length=80, blank=True)

    class Meta:
        verbose_name = "廠區"
        verbose_name_plural = "廠區"
        unique_together = [("site", "slug")]
        ordering = ["sort_order"]

    def __str__(self):
        return f"{self.get_plant_type_display()} — {self.name_zh}"


class Zone(TimeStampedModel):
    """展間分區（形象區、設備區、加工單元區…）"""

    ZONE_TYPES = [
        ("brand", "形象區"),
        ("equipment", "設備展示區"),
        ("process", "加工展示區"),
        ("catalog", "型錄區"),
        ("custom", "自訂區"),
    ]

    site = models.ForeignKey(ShowroomSite, on_delete=models.CASCADE, related_name="zones")
    name = models.CharField("分區名稱", max_length=100)
    slug = models.SlugField("代碼", max_length=80)
    zone_type = models.CharField("類型", max_length=20, choices=ZONE_TYPES, default="equipment")
    title_zh = models.CharField("標題（繁中）", max_length=150)
    title_en = models.CharField("標題（英文）", max_length=150, blank=True)
    title_ja = models.CharField("標題（日文）", max_length=150, blank=True)
    summary_zh = models.TextField("摘要（繁中）", blank=True)
    summary_en = models.TextField("摘要（英文）", blank=True)
    summary_ja = models.TextField("摘要（日文）", blank=True)
    cover_image = models.ImageField("封面圖", upload_to="zones/", blank=True, null=True)
    floor_plan_image = models.ImageField("平面導覽圖", upload_to="zones/", blank=True, null=True)
    panorama_image = models.ImageField("360全景圖", upload_to="zones/panorama/", blank=True, null=True)
    panorama_embed_url = models.URLField("外部360導覽連結", blank=True, help_text="如 qwhouse720 等")
    photo_gallery = models.JSONField(
        "現場照片廊", default=list, blank=True,
        help_text="分區現場照片 /media/ 路徑列表，供 AR 導覽瀏覽"
    )
    pipeline_meta = models.JSONField(
        "Pipeline 狀態", default=dict, blank=True,
        help_text="AI 強化 pipeline 處理紀錄（stage、preset、processed_at）"
    )
    audio_guide = models.FileField(
        "語音導覽", upload_to="zones/audio/", blank=True, null=True,
        help_text="分區解說音檔（MP3/M4A）"
    )
    sort_order = models.PositiveIntegerField("排序", default=0)
    is_active = models.BooleanField("啟用", default=True)

    class Meta:
        verbose_name = "展間分區"
        verbose_name_plural = "展間分區"
        unique_together = [("site", "slug")]
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.name

    def title(self, lang="zh-hant"):
        return {"en": self.title_en, "ja": self.title_ja}.get(lang) or self.title_zh


class Hotspot(TimeStampedModel):
    """導覽熱點（平面圖或全景上的可點擊位置）"""

    HOTSPOT_TYPES = [
        ("product", "產品設備"),
        ("zone", "跳轉分區"),
        ("link", "外部連結"),
        ("info", "說明資訊"),
        ("video", "播放影片"),
    ]

    zone = models.ForeignKey(Zone, on_delete=models.CASCADE, related_name="hotspots")
    label_zh = models.CharField("標籤（繁中）", max_length=100)
    label_en = models.CharField("標籤（英文）", max_length=100, blank=True)
    label_ja = models.CharField("標籤（日文）", max_length=100, blank=True)
    hotspot_type = models.CharField("類型", max_length=20, choices=HOTSPOT_TYPES, default="product")
    pos_x = models.FloatField("X 座標 (%)", default=50, help_text="0-100 百分比")
    pos_y = models.FloatField("Y 座標 (%)", default=50, help_text="0-100 百分比")
    icon = models.CharField("圖示", max_length=30, default="pin", blank=True)
    product = models.ForeignKey(
        "Product", on_delete=models.SET_NULL, null=True, blank=True, related_name="hotspots"
    )
    target_zone = models.ForeignKey(
        Zone, on_delete=models.SET_NULL, null=True, blank=True, related_name="linked_hotspots"
    )
    external_url = models.URLField("外部連結", blank=True)
    tooltip_zh = models.CharField("提示（繁中）", max_length=200, blank=True)
    sort_order = models.PositiveIntegerField("排序", default=0)
    is_active = models.BooleanField("啟用", default=True)

    class Meta:
        verbose_name = "導覽熱點"
        verbose_name_plural = "導覽熱點"
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.label_zh


class ProductCategory(TimeStampedModel):
    site = models.ForeignKey(ShowroomSite, on_delete=models.CASCADE, related_name="categories")
    name_zh = models.CharField("名稱（繁中）", max_length=100)
    name_en = models.CharField("名稱（英文）", max_length=100, blank=True)
    name_ja = models.CharField("名稱（日文）", max_length=100, blank=True)
    slug = models.SlugField("代碼", max_length=80)
    sort_order = models.PositiveIntegerField("排序", default=0)

    class Meta:
        verbose_name = "產品分類"
        verbose_name_plural = "產品分類"
        unique_together = [("site", "slug")]
        ordering = ["sort_order"]

    def __str__(self):
        return self.name_zh


class Product(TimeStampedModel):
    """關鍵零組件 / 設備（一頁式詳細介紹 + PopRealAR 3D 數位孿生）"""

    site = models.ForeignKey(ShowroomSite, on_delete=models.CASCADE, related_name="products")
    category = models.ForeignKey(
        ProductCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name="products"
    )
    zone = models.ForeignKey(Zone, on_delete=models.SET_NULL, null=True, blank=True, related_name="products")
    showroom_level = models.ForeignKey(
        ShowroomLevel, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="products", verbose_name="所屬展間層級"
    )
    factory_plant = models.ForeignKey(
        FactoryPlant, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="products", verbose_name="所屬廠區"
    )
    name_zh = models.CharField("名稱（繁中）", max_length=150)
    name_en = models.CharField("名稱（英文）", max_length=150, blank=True)
    name_ja = models.CharField("名稱（日文）", max_length=150, blank=True)
    slug = models.SlugField("代碼", max_length=100)
    model_no = models.CharField("型號", max_length=80, blank=True)
    tagline_zh = models.CharField("標語（繁中）", max_length=200, blank=True)
    tagline_en = models.CharField("標語（英文）", max_length=200, blank=True)
    tagline_ja = models.CharField("標語（日文）", max_length=200, blank=True)
    summary_zh = models.TextField("摘要（繁中）", blank=True)
    summary_en = models.TextField("摘要（英文）", blank=True)
    summary_ja = models.TextField("摘要（日文）", blank=True)
    description_zh = models.TextField("詳細說明（繁中）", blank=True)
    description_en = models.TextField("詳細說明（英文）", blank=True)
    description_ja = models.TextField("詳細說明（日文）", blank=True)
    cover_image = models.ImageField("封面圖", upload_to="products/", blank=True, null=True)
    hero_video_url = models.URLField("主影片", blank=True)
    # —— 3D 數位孿生資產（源自 12 個 IGS 原始檔精選轉換）——
    igs_file = models.FileField(
        "IGS 原始檔", upload_to="products/igs/", blank=True, null=True,
        help_text="工程原始 CAD 檔（IGS / IGES 格式）"
    )
    step_file = models.FileField(
        "STEP 原始檔", upload_to="products/step/", blank=True, null=True,
        help_text="工程原始 CAD 檔（STEP / STP 格式）"
    )
    gltf_file = models.FileField(
        "GLTF/GLB 模型檔", upload_to="products/gltf/", blank=True, null=True,
        help_text="Web 端 Three.js 載入用 GLB 檔案"
    )
    model_3d_url = models.URLField(
        "3D 模型外部連結", blank=True, help_text="GLB/Sketchfab 等備用 CDN 連結"
    )
    frame_position_image = models.ImageField(
        "車架相對定位圖", upload_to="products/frame/", blank=True, null=True,
        help_text="零組件於車架上的相對位置示意圖"
    )
    ar_popreal_url = models.URLField("PopReal AR 連結", blank=True)
    # —— PopRealAR 即時規格模擬參數上下限 ——
    default_color_hex = models.CharField(
        "預設零件色", max_length=7, default="#FFD100",
        help_text="休閒運動風高反差黃色，確保零組件不被場景吃掉"
    )
    color_options = models.JSONField(
        "可切換顏色列表", default=list, blank=True,
        help_text='例：["#FFD100","#1E4A8C","#FFFFFF","#2D2D2D"]'
    )
    scale_min = models.FloatField("縮放下限", default=0.8)
    scale_max = models.FloatField("縮放上限", default=1.2)
    scale_default = models.FloatField("預設縮放", default=1.0)
    diameter_min = models.FloatField("直徑微調下限 (mm)", default=0.0, blank=True)
    diameter_max = models.FloatField("直徑微調上限 (mm)", default=0.0, blank=True)
    diameter_default = models.FloatField("預設直徑 (mm)", default=0.0, blank=True)
    angle_cut_min = models.FloatField("切角下限 (°)", default=0.0, blank=True)
    angle_cut_max = models.FloatField("切角上限 (°)", default=0.0, blank=True)
    angle_cut_default = models.FloatField("預設切角 (°)", default=0.0, blank=True)
    joint_angle_min = models.FloatField("結合角度下限 (°)", default=0.0, blank=True)
    joint_angle_max = models.FloatField("結合角度上限 (°)", default=0.0, blank=True)
    joint_angle_default = models.FloatField("預設結合角度 (°)", default=0.0, blank=True)
    elevation_angle_min = models.FloatField("仰角下限 (°)", default=0.0, blank=True)
    elevation_angle_max = models.FloatField("仰角上限 (°)", default=0.0, blank=True)
    elevation_angle_default = models.FloatField("預設仰角 (°)", default=0.0, blank=True)
    # —— AI 多語系與教育訓練說明預留接口 ——
    ai_translation_key = models.CharField(
        "AI 翻譯鍵值", max_length=80, blank=True,
        help_text="供未來 AI 多語系翻譯批次處理的內容識別鍵"
    )
    training_notes_zh = models.TextField(
        "教育訓練說明（繁中）", blank=True,
        help_text="預留給內部教育訓練與 AI 問答系統的技術說明"
    )
    training_notes_en = models.TextField("教育訓練說明（英文）", blank=True)
    training_notes_ja = models.TextField("教育訓練說明（日文）", blank=True)
    catalog_pdf = models.FileField("型錄 PDF", upload_to="catalogs/", blank=True, null=True)
    official_url = models.URLField("官網產品頁", blank=True)
    features_zh = models.JSONField("特點列表（繁中）", default=list, blank=True)
    features_en = models.JSONField("特點列表（英文）", default=list, blank=True)
    features_ja = models.JSONField("特點列表（日文）", default=list, blank=True)
    specs = models.JSONField("規格表", default=dict, blank=True)
    has_animation = models.BooleanField("動態展示", default=False)
    animation_note_zh = models.CharField("動態說明（繁中）", max_length=300, blank=True)
    sort_order = models.PositiveIntegerField("排序", default=0)
    is_featured = models.BooleanField("精選", default=False)
    is_active = models.BooleanField("啟用", default=True)

    class Meta:
        verbose_name = "產品設備"
        verbose_name_plural = "產品設備"
        unique_together = [("site", "slug")]
        ordering = ["sort_order", "name_zh"]

    def __str__(self):
        return self.name_zh

    def name(self, lang="zh-hant"):
        return {"en": self.name_en, "ja": self.name_ja}.get(lang) or self.name_zh

    def gltf_source_url(self):
        """取得 Three.js 載入用的 GLB 路徑（優先本地上傳，其次外部連結）"""
        if self.gltf_file:
            return self.gltf_file.url
        return self.model_3d_url or ""

    def cad_source_url(self):
        """工程 CAD 下載連結（STEP 優先，其次 IGS）"""
        if self.step_file:
            return self.step_file.url
        if self.igs_file:
            return self.igs_file.url
        return ""

    def popreal_config(self):
        """組裝前端 PopRealAR 互動配置 JSON（供 detail.html Three.js 使用）"""
        colors = self.color_options or [self.default_color_hex, "#1E4A8C", "#FFFFFF"]
        gltf_url = self.gltf_source_url()
        cad_url = self.cad_source_url()
        tonnage = 0
        if self.model_no:
            m = re.search(r"(\d+)", self.model_no.replace(",", ""))
            if m:
                tonnage = int(m.group(1))
        preview_mode = "component"
        if cad_url and not gltf_url and tonnage >= 100:
            preview_mode = "die_casting"
        cad_convert_url = ""
        if cad_url and not gltf_url:
            cad_convert_url = f"/api/cad/convert/product/{self.slug}/"
        return {
            "gltf_url": gltf_url,
            "cad_url": cad_url,
            "cad_convert_url": cad_convert_url,
            "preview_mode": preview_mode,
            "machine_tonnage": tonnage,
            "model_no": self.model_no,
            "default_color": self.default_color_hex,
            "color_options": colors,
            "scale": {"min": self.scale_min, "max": self.scale_max, "default": self.scale_default},
            "diameter": {
                "min": self.diameter_min, "max": self.diameter_max, "default": self.diameter_default,
            },
            "angle_cut": {
                "min": self.angle_cut_min, "max": self.angle_cut_max, "default": self.angle_cut_default,
            },
            "joint_angle": {
                "min": self.joint_angle_min, "max": self.joint_angle_max, "default": self.joint_angle_default,
            },
            "elevation_angle": {
                "min": self.elevation_angle_min, "max": self.elevation_angle_max,
                "default": self.elevation_angle_default,
            },
            "frame_position_image": self.frame_position_image.url if self.frame_position_image else "",
            "ai_translation_key": self.ai_translation_key,
            "scene_theme": "factory",
        }


class ProductMedia(TimeStampedModel):
    """產品媒體庫（圖片、影片、動態腳本截圖）"""

    MEDIA_TYPES = [
        ("image", "圖片"),
        ("video", "影片"),
        ("gif", "動態圖"),
        ("embed", "嵌入內容"),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="media_items")
    media_type = models.CharField("類型", max_length=20, choices=MEDIA_TYPES, default="image")
    title = models.CharField("標題", max_length=120, blank=True)
    file = models.FileField("檔案", upload_to="products/media/", blank=True, null=True)
    image = models.ImageField("圖片", upload_to="products/media/", blank=True, null=True)
    video_url = models.URLField("影片網址", blank=True)
    embed_code = models.TextField("嵌入程式碼", blank=True)
    sort_order = models.PositiveIntegerField("排序", default=0)

    class Meta:
        verbose_name = "產品媒體"
        verbose_name_plural = "產品媒體"
        ordering = ["sort_order"]

    def __str__(self):
        return self.title or f"{self.product} #{self.pk}"


class BrandPoster(TimeStampedModel):
    """形象區海報 / 企業識別展示"""

    site = models.ForeignKey(ShowroomSite, on_delete=models.CASCADE, related_name="posters")
    title_zh = models.CharField("標題（繁中）", max_length=150)
    title_en = models.CharField("標題（英文）", max_length=150, blank=True)
    image = models.ImageField("海報圖", upload_to="posters/")
    link_url = models.URLField("連結", blank=True)
    sort_order = models.PositiveIntegerField("排序", default=0)
    is_active = models.BooleanField("啟用", default=True)

    class Meta:
        verbose_name = "形象海報"
        verbose_name_plural = "形象海報"
        ordering = ["sort_order"]

    def __str__(self):
        return self.title_zh


class GuideStep(TimeStampedModel):
    """操作說明指引"""

    site = models.ForeignKey(ShowroomSite, on_delete=models.CASCADE, related_name="guide_steps")
    title_zh = models.CharField("標題（繁中）", max_length=120)
    title_en = models.CharField("標題（英文）", max_length=120, blank=True)
    content_zh = models.TextField("內容（繁中）")
    content_en = models.TextField("內容（英文）", blank=True)
    icon = models.CharField("圖示", max_length=30, default="help")
    sort_order = models.PositiveIntegerField("排序", default=0)

    class Meta:
        verbose_name = "操作指引"
        verbose_name_plural = "操作指引"
        ordering = ["sort_order"]

    def __str__(self):
        return self.title_zh


class Inquiry(TimeStampedModel):
    """線上諮詢"""

    STATUS = [("new", "新詢問"), ("processing", "處理中"), ("done", "已完成")]

    site = models.ForeignKey(ShowroomSite, on_delete=models.CASCADE, related_name="inquiries")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField("姓名", max_length=80)
    company = models.CharField("公司", max_length=120, blank=True)
    email = models.EmailField("Email")
    phone = models.CharField("電話", max_length=40, blank=True)
    message = models.TextField("諮詢內容")
    status = models.CharField("狀態", max_length=20, choices=STATUS, default="new")
    ip_address = models.GenericIPAddressField("IP", blank=True, null=True)

    class Meta:
        verbose_name = "線上諮詢"
        verbose_name_plural = "線上諮詢"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} — {self.created_at:%Y-%m-%d}"


class MemberProfile(TimeStampedModel):
    """展間會員（經銷商 / 客戶帳號）"""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="member_profile")
    company = models.CharField("公司", max_length=120, blank=True)
    phone = models.CharField("電話", max_length=40, blank=True)
    job_title = models.CharField("職稱", max_length=80, blank=True)
    country = models.CharField("國家/地區", max_length=60, blank=True, default="Taiwan")
    is_verified = models.BooleanField("已驗證", default=False)
    last_login_ip = models.GenericIPAddressField("最後登入 IP", blank=True, null=True)

    class Meta:
        verbose_name = "展間會員"
        verbose_name_plural = "展間會員"

    def __str__(self):
        return self.user.get_username()


class AnalyticsEvent(TimeStampedModel):
    """瀏覽與互動追蹤"""

    EVENT_TYPES = [
        ("page_view", "頁面瀏覽"),
        ("product_view", "產品瀏覽"),
        ("zone_view", "分區瀏覽"),
        ("inquiry", "諮詢送出"),
        ("share", "分享"),
        ("ar_click", "AR 點擊"),
        ("login", "會員登入"),
    ]

    site = models.ForeignKey(ShowroomSite, on_delete=models.CASCADE, related_name="analytics_events", null=True, blank=True)
    event_type = models.CharField("事件類型", max_length=20, choices=EVENT_TYPES)
    path = models.CharField("路徑", max_length=300, blank=True)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    zone = models.ForeignKey(Zone, on_delete=models.SET_NULL, null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField("IP", blank=True, null=True)
    user_agent = models.CharField("User-Agent", max_length=300, blank=True)
    referer = models.CharField("來源", max_length=300, blank=True)
    meta = models.JSONField("附加資料", default=dict, blank=True)

    class Meta:
        verbose_name = "分析事件"
        verbose_name_plural = "分析事件"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["event_type", "created_at"]),
            models.Index(fields=["site", "created_at"]),
        ]

    def __str__(self):
        return f"{self.event_type} @ {self.path or '-'}"


class ErpConnection(TimeStampedModel):
    """ERP 連線設定"""

    site = models.OneToOneField(ShowroomSite, on_delete=models.CASCADE, related_name="erp_connection")
    name = models.CharField("連線名稱", max_length=80, default="ERP")
    api_base_url = models.URLField("API 基礎網址", help_text="例：https://erp.example.com/api")
    api_key = models.CharField("API Key", max_length=200, blank=True)
    products_endpoint = models.CharField("產品同步端點", max_length=200, default="/products")
    auth_header = models.CharField("認證 Header 名稱", max_length=60, default="Authorization")
    auth_prefix = models.CharField("認證前綴", max_length=20, default="Bearer")
    is_active = models.BooleanField("啟用", default=False)
    auto_sync = models.BooleanField("自動同步", default=False)
    sync_interval_hours = models.PositiveIntegerField("同步間隔（小時）", default=24)
    last_sync_at = models.DateTimeField("上次同步", blank=True, null=True)
    last_sync_status = models.CharField("上次狀態", max_length=20, blank=True)
    last_sync_message = models.TextField("上次訊息", blank=True)
    field_mapping = models.JSONField(
        "欄位對應",
        default=dict,
        blank=True,
        help_text='例：{"name_zh":"item_name","model_no":"item_code","summary_zh":"description"}',
    )

    class Meta:
        verbose_name = "ERP 連線"
        verbose_name_plural = "ERP 連線"

    def __str__(self):
        return f"{self.site.name} — {self.name}"


class ErpSyncLog(TimeStampedModel):
    """ERP 同步紀錄"""

    connection = models.ForeignKey(ErpConnection, on_delete=models.CASCADE, related_name="sync_logs")
    status = models.CharField("狀態", max_length=20, choices=[("ok", "成功"), ("error", "失敗")])
    created_count = models.PositiveIntegerField("新增", default=0)
    updated_count = models.PositiveIntegerField("更新", default=0)
    skipped_count = models.PositiveIntegerField("略過", default=0)
    message = models.TextField("訊息", blank=True)

    class Meta:
        verbose_name = "ERP 同步紀錄"
        verbose_name_plural = "ERP 同步紀錄"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.connection} — {self.status} ({self.created_at:%Y-%m-%d %H:%M})"
