import json

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count, Max
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from catalog.models import Book

from .forms import RegistrationForm, ShelfForm
from .models import ReadingProgress, Shelf, ShelfItem
from .services import get_default_shelf


def register(request):
    if request.user.is_authenticated:
        return redirect("library:dashboard")

    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            get_default_shelf(user)
            messages.success(
                request,
                "Your account is ready. Your first shelf has been created for you.",
            )
            return redirect("library:dashboard")
        messages.error(request, "Please fix the highlighted fields and try again.")
    else:
        form = RegistrationForm()

    return render(request, "registration/register.html", {"form": form})


@login_required
def dashboard(request):
    get_default_shelf(request.user)
    shelves = (
        Shelf.objects.filter(user=request.user)
        .annotate(item_total=Count("items"))
        .order_by("-is_default", "name")
    )
    continue_reading = (
        ReadingProgress.objects.filter(user=request.user)
        .select_related("book", "book__category")
        .order_by("-updated_at")[:6]
    )
    stats = {
        "shelves": shelves.count(),
        "shelved_books": ShelfItem.objects.filter(shelf__user=request.user).count(),
        "started": ReadingProgress.objects.filter(user=request.user).count(),
        "finished": ReadingProgress.objects.filter(
            user=request.user, percent__gte=99
        ).count(),
    }
    return render(
        request,
        "library/dashboard.html",
        {
            "shelves": shelves,
            "continue_reading": continue_reading,
            "stats": stats,
        },
    )


@login_required
def shelf_create(request):
    get_default_shelf(request.user)
    if request.method == "POST":
        form = ShelfForm(request.POST, user=request.user)
        if form.is_valid():
            if Shelf.objects.filter(user=request.user).count() >= 20:
                form.add_error(None, "You can keep at most 20 shelves.")
            else:
                shelf = Shelf.objects.create(
                    user=request.user,
                    name=form.cleaned_data["name"],
                )
                messages.success(request, f"Shelf “{shelf.name}” created.")
                return redirect("library:shelf_detail", pk=shelf.pk)
        if form.errors:
            messages.error(request, "Please fix the highlighted fields and try again.")
    else:
        form = ShelfForm(user=request.user)

    return render(request, "library/shelf_form.html", {"form": form, "is_create": True})


def _owned_shelf(request, pk):
    return get_object_or_404(Shelf, pk=pk, user=request.user)


@login_required
def shelf_detail(request, pk):
    shelf = _owned_shelf(request, pk)
    items = list(
        shelf.items.select_related("book", "book__category").order_by("position", "id")
    )
    progress_by_book = {
        progress.book_id: progress
        for progress in ReadingProgress.objects.filter(
            user=request.user,
            book_id__in=[item.book_id for item in items],
        )
    }
    rows = [
        {"item": item, "progress": progress_by_book.get(item.book_id)}
        for item in items
    ]
    return render(
        request,
        "library/shelf_detail.html",
        {"shelf": shelf, "rows": rows},
    )


@login_required
def shelf_edit(request, pk):
    shelf = _owned_shelf(request, pk)
    if request.method == "POST":
        form = ShelfForm(request.POST, user=request.user, instance=shelf)
        if form.is_valid():
            shelf.name = form.cleaned_data["name"]
            shelf.save()
            messages.success(request, "Shelf renamed.")
            return redirect("library:shelf_detail", pk=shelf.pk)
        messages.error(request, "Please fix the highlighted fields and try again.")
    else:
        form = ShelfForm(user=request.user, instance=shelf)

    return render(
        request,
        "library/shelf_form.html",
        {"form": form, "shelf": shelf, "is_create": False},
    )


@login_required
def shelf_delete(request, pk):
    shelf = _owned_shelf(request, pk)
    if shelf.is_default:
        messages.error(request, "Your default shelf cannot be deleted.")
        return redirect("library:shelf_detail", pk=shelf.pk)

    if request.method == "POST":
        name = shelf.name
        shelf.delete()
        messages.success(request, f"Shelf “{name}” deleted. The books are still in the catalog.")
        return redirect("library:dashboard")

    return render(request, "library/shelf_confirm_delete.html", {"shelf": shelf})


@login_required
@require_POST
def shelf_add_book(request, pk=None):
    book = get_object_or_404(Book, pk=request.POST.get("book_id"))
    if pk:
        shelf = _owned_shelf(request, pk)
    else:
        shelf_id = request.POST.get("shelf_id")
        shelf = (
            get_object_or_404(Shelf, pk=shelf_id, user=request.user)
            if shelf_id
            else get_default_shelf(request.user)
        )

    max_position = shelf.items.aggregate(Max("position"))["position__max"] or 0
    _, created = ShelfItem.objects.get_or_create(
        shelf=shelf,
        book=book,
        defaults={"position": max_position + 1},
    )
    if created:
        messages.success(request, f"“{book.title}” added to {shelf.name}.")
    else:
        messages.info(request, f"“{book.title}” is already on {shelf.name}.")
    return redirect(book)


@login_required
@require_POST
def shelf_remove_book(request, pk):
    item = get_object_or_404(
        ShelfItem,
        pk=pk,
        shelf__user=request.user,
    )
    shelf = item.shelf
    title = item.book.title
    item.delete()
    messages.success(request, f"“{title}” removed from {shelf.name}.")
    return redirect("library:shelf_detail", pk=shelf.pk)


@login_required
@require_POST
def shelf_reorder(request, pk):
    shelf = _owned_shelf(request, pk)
    try:
        payload = json.loads(request.body.decode("utf-8"))
        order = payload.get("order")
        if not isinstance(order, list) or not all(
            isinstance(value, int) for value in order
        ):
            raise ValueError
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
        return JsonResponse({"error": "Invalid ordering payload."}, status=400)

    items = list(shelf.items.all())
    item_ids = {item.pk for item in items}
    if set(order) != item_ids or len(order) != len(item_ids):
        return JsonResponse(
            {"error": "The ordering must include every book on this shelf exactly once."},
            status=400,
        )

    by_id = {item.pk: item for item in items}
    with transaction.atomic():
        for position, item_id in enumerate(order, start=1):
            by_id[item_id].position = position
        ShelfItem.objects.bulk_update(items, ["position"])

    return JsonResponse({"saved": True, "count": len(order)})


def _validate_locator(locator):
    if not isinstance(locator, dict):
        return None
    if len(locator) > 12:
        return None
    try:
        serialized = json.dumps(locator, ensure_ascii=False)
    except (TypeError, ValueError):
        return None
    if len(serialized.encode("utf-8")) > 4096:
        return None
    return locator


@login_required
@require_POST
def save_progress(request, book_id):
    book = get_object_or_404(Book, pk=book_id)
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return JsonResponse({"error": "Invalid JSON body."}, status=400)

    locator = _validate_locator(payload.get("locator"))
    if locator is None:
        return JsonResponse({"error": "Invalid reading position."}, status=400)

    try:
        percent = float(payload.get("percent", 0))
    except (TypeError, ValueError):
        return JsonResponse({"error": "Percent must be a number."}, status=400)
    if not 0 <= percent <= 100:
        return JsonResponse({"error": "Percent must be between 0 and 100."}, status=400)

    progress, _ = ReadingProgress.objects.update_or_create(
        user=request.user,
        book=book,
        defaults={"locator": locator, "percent": round(percent, 2)},
    )
    return JsonResponse(
        {
            "saved": True,
            "percent": progress.percent,
            "updatedAt": progress.updated_at.isoformat(),
        }
    )
