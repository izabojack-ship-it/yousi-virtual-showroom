from django.contrib import admin
from django.utils.html import format_html
from .models import (
    AnalyticsEvent,
    BrandPoster,
    ErpConnection,
    ErpSyncLog,
    FactoryPlant,
    GuideStep,
    Hotspot,
    Inquiry,
    LocalizedText,
    MemberProfile,
    Product,
    ProductCategory,
    ProductMedia,
    ShowroomLevel,
    ShowroomSite,
    Zone,
)


def _img_preview(fieldfile, max_h=60):
    if fieldfile:
        return format_html('<img src="{}" style="max-height:{}px;border-radius:6px;" />', fieldfile.url, max_h)
    return "-"


class FactoryPlantInline(admin.TabularInline):
    model = FactoryPlant
    extra = 1
    fields = ("name_zh", "plant_type", "cover_image", "panorama_embed_url", "sort_order", "is_active")


@admin.register(ShowroomLevel)
class ShowroomLevelAdmin(admin.ModelAdmin):
    list_display = ("name_zh", "level_number", "level_type", "site", "cover_preview", "sort_order", "is_active")
    list_filter = ("site", "level_type", "is_active")
    prepopulated_fields = {"slug": ("name_zh",)}
    inlines = [FactoryPlantInline]
    fieldsets = (
        ("基本", {"fields": ("site", "level_number", "level_type", "slug", "name_zh", "name_en", "name_ja", "sort_order", "is_active")}),
        ("文案", {"fields": ("summary_zh", "summary_en", "summary_ja", "ai_translation_key")}),
        ("導覽媒體", {
            "fields": ("cover_image", "floor_plan_image", "panorama_image", "panorama_embed_url"),
            "description": "上傳全景地圖供導覽列「當前位置」標示；Level 2 可掛載台灣廠 / 越南廠",
        }),
    )

    @admin.display(description="封面")
    def cover_preview(self, obj):
        return _img_preview(obj.cover_image, 40)


@admin.register(FactoryPlant)
class FactoryPlantAdmin(admin.ModelAdmin):
    list_display = ("name_zh", "plant_type", "level", "site", "cover_preview", "sort_order", "is_active")
    list_filter = ("site", "plant_type", "is_active")
    prepopulated_fields = {"slug": ("name_zh",)}
    fieldsets = (
        ("基本", {"fields": ("site", "level", "plant_type", "slug", "name_zh", "name_en", "name_ja", "sort_order", "is_active")}),
        ("文案", {"fields": ("description_zh", "description_en", "description_ja", "ai_translation_key")}),
        ("廠區媒體", {
            "fields": ("cover_image", "panorama_image", "panorama_embed_url", "asset_gallery"),
            "description": "越南廠可上傳 PPT 截圖路徑至 asset_gallery JSON 陣列",
        }),
    )

    @admin.display(description="封面")
    def cover_preview(self, obj):
        return _img_preview(obj.cover_image, 40)


class HotspotInline(admin.TabularInline):
    model = Hotspot
    fk_name = "zone"
    extra = 1
    fields = ("label_zh", "hotspot_type", "pos_x", "pos_y", "product", "target_zone", "sort_order", "is_active")


class ProductMediaInline(admin.TabularInline):
    model = ProductMedia
    extra = 1
    fields = ("media_type", "title", "image", "video_url", "sort_order")


@admin.register(ShowroomSite)
class ShowroomSiteAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "logo_preview", "is_default", "is_active", "updated_at")
    list_filter = ("is_active", "is_default")
    prepopulated_fields = {"slug": ("name",)}
    fieldsets = (
        ("基本", {"fields": ("name", "slug", "tagline", "description", "is_active", "is_default")}),
        ("品牌視覺", {
            "fields": ("logo", "hero_image", "primary_color", "accent_color", "background_style"),
            "description": "上傳 Logo 與主視覺，並設定企業識別色彩（例：#1a4d8c）",
        }),
        ("聯絡與社群", {"fields": (
            "website_url", "facebook_url", "instagram_url", "linkedin_url",
            "youtube_url", "line_url", "contact_email", "contact_phone", "inquiry_enabled",
        )}),
        ("分享", {"fields": ("share_title", "share_description")}),
    )

    @admin.display(description="Logo")
    def logo_preview(self, obj):
        return _img_preview(obj.logo, 36)


@admin.register(Zone)
class ZoneAdmin(admin.ModelAdmin):
    list_display = ("name", "site", "zone_type", "cover_preview", "sort_order", "is_active")
    list_filter = ("site", "zone_type", "is_active")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [HotspotInline]
    fieldsets = (
        ("基本", {"fields": ("site", "name", "slug", "zone_type", "sort_order", "is_active")}),
        ("文案", {"fields": ("title_zh", "title_en", "title_ja", "summary_zh", "summary_en", "summary_ja")}),
        ("導覽媒體", {
            "fields": ("cover_image", "floor_plan_image", "panorama_image", "panorama_embed_url"),
            "description": "上傳平面導覽圖供熱點定位；360 可上傳全景圖或填入外部嵌入連結（如 qwhouse720）",
        }),
    )

    @admin.display(description="封面")
    def cover_preview(self, obj):
        return _img_preview(obj.cover_image, 40)


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ("name_zh", "site", "sort_order")
    list_filter = ("site",)
    prepopulated_fields = {"slug": ("name_zh",)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name_zh", "model_no", "cover_preview", "site", "showroom_level", "factory_plant", "is_featured", "is_active")
    list_filter = ("site", "showroom_level", "factory_plant", "zone", "is_featured", "is_active")
    search_fields = ("name_zh", "name_en", "model_no", "slug", "ai_translation_key")
    prepopulated_fields = {"slug": ("name_zh",)}
    inlines = [ProductMediaInline]
    fieldsets = (
        ("基本", {
            "fields": (
                "site", "category", "zone", "showroom_level", "factory_plant",
                "name_zh", "name_en", "name_ja", "slug", "model_no",
                "sort_order", "is_featured", "is_active",
            ),
        }),
        ("文案", {"fields": ("tagline_zh", "tagline_en", "tagline_ja", "summary_zh", "summary_en", "summary_ja", "description_zh", "description_en", "description_ja")}),
        ("3D 數位孿生資產", {
            "fields": (
                "step_file", "igs_file", "gltf_file", "model_3d_url", "frame_position_image",
                "ar_popreal_url", "cover_image", "hero_video_url", "catalog_pdf", "official_url",
            ),
            "description": "上傳 STEP / IGS 原始檔與 GLB 模型；GLB 供 Web 3D 預覽，STEP 供工程下載",
        }),
        ("PopRealAR 規格模擬參數", {
            "fields": (
                "default_color_hex", "color_options",
                "scale_min", "scale_max", "scale_default",
                "diameter_min", "diameter_max", "diameter_default",
                "angle_cut_min", "angle_cut_max", "angle_cut_default",
                "joint_angle_min", "joint_angle_max", "joint_angle_default",
                "elevation_angle_min", "elevation_angle_max", "elevation_angle_default",
            ),
            "description": "設定滑桿微調上下限，前端 Three.js 即時渲染",
        }),
        ("特點與規格", {"fields": ("features_zh", "features_en", "features_ja", "specs")}),
        ("動態展示", {"fields": ("has_animation", "animation_note_zh")}),
        ("AI 多語系與教育訓練（預留接口）", {
            "fields": ("ai_translation_key", "training_notes_zh", "training_notes_en", "training_notes_ja"),
            "description": "供未來 AI 翻譯批次處理與內部教育訓練問答系統串接",
        }),
    )

    @admin.display(description="圖片")
    def cover_preview(self, obj):
        return _img_preview(obj.cover_image, 40)


@admin.register(Hotspot)
class HotspotAdmin(admin.ModelAdmin):
    list_display = ("label_zh", "zone", "hotspot_type", "pos_x", "pos_y", "is_active")
    list_filter = ("zone__site", "hotspot_type")


@admin.register(BrandPoster)
class BrandPosterAdmin(admin.ModelAdmin):
    list_display = ("title_zh", "site", "image_preview", "sort_order", "is_active")
    list_filter = ("site",)

    @admin.display(description="海報")
    def image_preview(self, obj):
        return _img_preview(obj.image, 50)


@admin.register(GuideStep)
class GuideStepAdmin(admin.ModelAdmin):
    list_display = ("title_zh", "site", "sort_order")
    list_filter = ("site",)


@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = ("name", "company", "email", "site", "status", "created_at")
    list_filter = ("site", "status")
    readonly_fields = ("created_at", "updated_at", "ip_address")
    actions = ["mark_processing", "mark_done"]

    @admin.action(description="標記為處理中")
    def mark_processing(self, request, queryset):
        queryset.update(status="processing")

    @admin.action(description="標記為已完成")
    def mark_done(self, request, queryset):
        queryset.update(status="done")


@admin.register(MemberProfile)
class MemberProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "company", "phone", "is_verified", "last_login_ip", "created_at")
    list_filter = ("is_verified",)
    search_fields = ("user__username", "user__email", "company")


@admin.register(AnalyticsEvent)
class AnalyticsEventAdmin(admin.ModelAdmin):
    list_display = ("event_type", "path", "product", "ip_address", "created_at")
    list_filter = ("event_type", "site")
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "created_at"


class ErpSyncLogInline(admin.TabularInline):
    model = ErpSyncLog
    extra = 0
    readonly_fields = ("status", "created_count", "updated_count", "skipped_count", "message", "created_at")
    can_delete = False


@admin.register(ErpConnection)
class ErpConnectionAdmin(admin.ModelAdmin):
    list_display = ("site", "name", "is_active", "auto_sync", "last_sync_at", "last_sync_status")
    list_filter = ("is_active", "auto_sync")
    inlines = [ErpSyncLogInline]
    actions = ["run_sync_now"]

    @admin.action(description="立即同步 ERP 產品")
    def run_sync_now(self, request, queryset):
        from .erp_sync import sync_products
        for conn in queryset:
            sync_products(conn)
        self.message_user(request, f"已觸發 {queryset.count()} 筆 ERP 同步")


@admin.register(ErpSyncLog)
class ErpSyncLogAdmin(admin.ModelAdmin):
    list_display = ("connection", "status", "created_count", "updated_count", "created_at")
    list_filter = ("status",)


@admin.register(LocalizedText)
class LocalizedTextAdmin(admin.ModelAdmin):
    list_display = ("key", "lang", "site")
    list_filter = ("site", "lang")


@admin.register(ProductMedia)
class ProductMediaAdmin(admin.ModelAdmin):
    list_display = ("product", "media_type", "title", "sort_order")


# 自訂 Admin 首頁連結
admin.site.site_header = "優思國際 — 雲端虛擬展間管理"
admin.site.site_title = "展間管理"
admin.site.index_title = "內容管理 · 請至「分析儀表板」查看數據"
