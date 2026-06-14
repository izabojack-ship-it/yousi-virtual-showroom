from django.urls import path
from . import api

urlpatterns = [
    path("site/", api.api_site, name="api_site"),
    path("site/<slug:site_slug>/", api.api_site, name="api_site_slug"),
    path("zones/", api.api_zones, name="api_zones"),
    path("zones/<slug:zone_slug>/", api.api_zone_detail, name="api_zone"),
    path("products/", api.api_products, name="api_products"),
    path("products/<slug:product_slug>/", api.api_product_detail, name="api_product"),
    path("hotspots/<slug:zone_slug>/", api.api_hotspots, name="api_hotspots"),
    path("erp/demo-products/", api.api_erp_demo_products, name="api_erp_demo"),
    path("analytics/summary/", api.api_analytics_summary, name="api_analytics_summary"),
    path("pipeline/", api.api_pipeline_status, name="api_pipeline_status"),
    path("pipeline/site/<slug:site_slug>/", api.api_pipeline_status, name="api_pipeline_site"),
    path("pipeline/zone/<slug:zone_slug>/", api.api_zone_pipeline, name="api_zone_pipeline"),
    path("cad/convert-status/", api.api_cad_convert_status, name="api_cad_convert_status"),
    path("cad/convert/product/<slug:product_slug>/", api.api_cad_convert_product, name="api_cad_convert_product"),
]
