from django.conf import settings


def site(request):
    return {
        "SITE_NAME": "Libra",
        "SITE_TAGLINE": "A small library for big reading lists",
        "MAX_BOOK_UPLOAD_MB": getattr(settings, "MAX_BOOK_UPLOAD_BYTES", 0) // (1024 * 1024),
    }
