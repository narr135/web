from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied


def staff_required(view_func):
    """Require an authenticated staff user, with friendly 403/redirect behaviour."""

    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if not request.user.is_staff:
            raise PermissionDenied("Staff access is required to manage the catalog.")
        return view_func(request, *args, **kwargs)

    return _wrapped
