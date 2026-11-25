from .models import Shelf


def get_default_shelf(user):
    """Return the user's default shelf, creating/repairing it when necessary."""
    shelf = Shelf.objects.filter(user=user, is_default=True).first()
    if shelf is not None:
        return shelf

    shelf = Shelf.objects.filter(user=user, name="My Shelf").first()
    if shelf is None:
        return Shelf.objects.create(user=user, name="My Shelf", is_default=True)

    if not shelf.is_default:
        shelf.is_default = True
        shelf.save(update_fields=["is_default", "updated_at"])
    return shelf
