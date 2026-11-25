"""Template helpers for cache-safe static asset URLs."""

import os

from django import template
from django.contrib.staticfiles import finders
from django.templatetags.static import static

register = template.Library()


@register.simple_tag
def static_v(path):
    """Return the static URL with a version derived from the file's mtime.

    Browsers may keep using a previously cached stylesheet or script even when
    the development server serves a newer file. Adding the modification time as
    a query string makes every edit a new URL, so the browser is forced to fetch
    the current asset. Falls back to the plain static URL if the file is not
    found (for example when serving collected assets).
    """
    url = static(path)
    absolute_path = finders.find(path)
    if not absolute_path:
        return url
    try:
        version = os.stat(absolute_path).st_mtime_ns
    except OSError:
        return url
    separator = "&" if "?" in url else "?"
    return f"{url}{separator}v={version}"
