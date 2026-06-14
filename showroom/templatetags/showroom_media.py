from django import template

from showroom.media_utils import resolve_file_field_url, resolve_media_url

register = template.Library()


@register.filter
def media_url(path):
    return resolve_media_url(path)


@register.filter
def file_url(field):
    return resolve_file_field_url(field)
