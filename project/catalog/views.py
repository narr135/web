from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, F, Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.templatetags.static import static
from django.urls import reverse

from library.models import ReadingProgress, Shelf, ShelfItem
from library.services import get_default_shelf

from .decorators import staff_required
from .forms import BookForm
from .models import Book, Category


def _file_exists(field_file):
    if not field_file or not field_file.name:
        return False
    try:
        return field_file.storage.exists(field_file.name)
    except OSError:
        return False


def _delete_named_file(storage, name):
    if not name:
        return
    try:
        if storage.exists(name):
            storage.delete(name)
    except OSError:
        pass


def _delete_stored_file(field_file):
    if field_file and field_file.name:
        _delete_named_file(field_file.storage, field_file.name)


def _pagination_query(request):
    params = request.GET.copy()
    params.pop("page", None)
    return params.urlencode()


def home(request):
    books = Book.objects.select_related("category")[:6]
    categories = (
        Category.objects.annotate(book_count=Count("books"))
        .filter(book_count__gt=0)
        .order_by("-book_count", "name")[:8]
    )
    stats = {
        "books": Book.objects.count(),
        "categories": Category.objects.count(),
        "authors": Book.objects.values("author").distinct().count(),
    }
    continue_reading = []
    finished_count = 0
    if request.user.is_authenticated:
        continue_reading = (
            ReadingProgress.objects.filter(user=request.user)
            .select_related("book", "book__category")
            .order_by("-updated_at")[:4]
        )
        finished_count = ReadingProgress.objects.filter(
            user=request.user, percent__gte=99
        ).count()

    return render(
        request,
        "catalog/home.html",
        {
            "books": books,
            "categories": categories,
            "stats": stats,
            "continue_reading": continue_reading,
            "finished_count": finished_count,
        },
    )


def book_list(request):
    books = Book.objects.select_related("category")
    categories = Category.objects.annotate(book_count=Count("books"))

    query = (request.GET.get("q") or "").strip()[:100]
    category_slug = (request.GET.get("category") or "").strip()
    sort = request.GET.get("sort") or "newest"

    selected_category = None
    if category_slug:
        selected_category = categories.filter(slug=category_slug).first()
        if selected_category:
            books = books.filter(category=selected_category)

    if query:
        books = books.filter(
            Q(title__icontains=query)
            | Q(subtitle__icontains=query)
            | Q(author__icontains=query)
            | Q(isbn__icontains=query)
        )

    orderings = {
        "newest": ["-created_at"],
        "title": ["title", "author"],
        "author": ["author", "title"],
        "popular": ["-download_count", "title"],
    }
    books = books.order_by(*orderings.get(sort, orderings["newest"]))

    paginator = Paginator(books, 12)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "catalog/book_list.html",
        {
            "page_obj": page_obj,
            "paginator": paginator,
            "categories": categories,
            "selected_category": selected_category,
            "query": query,
            "sort": sort if sort in orderings else "newest",
            "query_string": _pagination_query(request),
            "result_count": paginator.count,
        },
    )


def book_detail(request, slug):
    book = get_object_or_404(Book.objects.select_related("category"), slug=slug)
    progress = None
    shelves = []
    shelf_ids_with_book = set()
    default_shelf = None

    if request.user.is_authenticated:
        progress = ReadingProgress.objects.filter(
            user=request.user, book=book
        ).first()
        shelves = list(
            Shelf.objects.filter(user=request.user).annotate(item_total=Count("items"))
        )
        default_shelf = get_default_shelf(request.user)
        shelf_ids_with_book = set(
            ShelfItem.objects.filter(
                book=book, shelf__user=request.user
            ).values_list("shelf_id", flat=True)
        )

    related = (
        Book.objects.filter(category=book.category)
        .exclude(pk=book.pk)
        .select_related("category")[:4]
    )

    return render(
        request,
        "catalog/book_detail.html",
        {
            "book": book,
            "progress": progress,
            "shelves": shelves,
            "shelf_ids_with_book": shelf_ids_with_book,
            "default_shelf": default_shelf,
            "related_books": related,
            "file_available": _file_exists(book.file),
        },
    )


def reader(request, slug):
    book = get_object_or_404(Book.objects.select_related("category"), slug=slug)
    if not book.is_readable:
        messages.error(request, "This format can only be downloaded, not read in the browser.")
        return redirect(book)
    if not _file_exists(book.file):
        messages.error(request, "The book file is missing. Please contact the librarian.")
        return redirect(book)

    progress = None
    if request.user.is_authenticated:
        progress = ReadingProgress.objects.filter(
            user=request.user, book=book
        ).first()

    reader_config = {
        "bookId": book.pk,
        "format": book.file_type,
        "fileUrl": reverse("catalog:book_file", kwargs={"slug": book.slug}),
        "progressUrl": reverse("save_progress", kwargs={"book_id": book.pk}),
        "isAuthenticated": request.user.is_authenticated,
        "title": book.title,
        "author": book.author,
        "initialLocator": progress.locator if progress else {},
        "initialPercent": progress.percent if progress else 0,
        "pdfLibUrl": request.build_absolute_uri(static("vendor/pdfjs/pdf.min.mjs")),
        "pdfWorkerUrl": request.build_absolute_uri(static("vendor/pdfjs/pdf.worker.min.mjs")),
        "pdfStandardFontsUrl": request.build_absolute_uri(static("vendor/pdfjs/standard_fonts/")),
    }

    return render(
        request,
        "catalog/reader.html",
        {
            "book": book,
            "reader_config": reader_config,
            "progress": progress,
        },
    )


def book_file(request, slug):
    book = get_object_or_404(Book, slug=slug)
    if not book.is_readable:
        raise Http404("This book format cannot be displayed in the browser.")
    if not _file_exists(book.file):
        raise Http404("The book file is missing.")

    response = FileResponse(
        book.file.open("rb"),
        content_type=book.content_type,
        as_attachment=False,
        filename=f"{book.slug}.{book.file_extension}",
    )
    response["Cache-Control"] = "private, max-age=0, must-revalidate"
    response["X-Content-Type-Options"] = "nosniff"
    return response


def book_download(request, slug):
    book = get_object_or_404(Book, slug=slug)
    if not _file_exists(book.file):
        messages.error(request, "The book file is missing. Please contact the librarian.")
        return redirect(book)

    Book.objects.filter(pk=book.pk).update(download_count=F("download_count") + 1)
    response = FileResponse(
        book.file.open("rb"),
        content_type="application/octet-stream",
        as_attachment=True,
        filename=book.download_filename,
    )
    response["X-Content-Type-Options"] = "nosniff"
    return response


@staff_required
def manage_dashboard(request):
    context = {
        "book_count": Book.objects.count(),
        "category_count": Category.objects.count(),
        "recent_books": Book.objects.select_related("category")[:8],
        "missing_files": [
            book
            for book in Book.objects.all()[:50]
            if not _file_exists(book.file)
        ],
    }
    return render(request, "catalog/manage/dashboard.html", context)


@staff_required
def manage_book_list(request):
    books = Book.objects.select_related("category", "uploaded_by")
    query = (request.GET.get("q") or "").strip()[:100]
    if query:
        books = books.filter(
            Q(title__icontains=query)
            | Q(author__icontains=query)
            | Q(isbn__icontains=query)
        )
    paginator = Paginator(books, 20)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(
        request,
        "catalog/manage/book_list.html",
        {
            "page_obj": page_obj,
            "query": query,
            "query_string": _pagination_query(request),
        },
    )


@staff_required
def manage_book_create(request):
    if request.method == "POST":
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            book = form.save(commit=False)
            book.uploaded_by = request.user
            book.save()
            messages.success(request, f"“{book.title}” was added to the catalog.")
            return redirect("catalog:manage_book_list")
        messages.error(request, "Please fix the highlighted fields and try again.")
    else:
        form = BookForm()

    return render(
        request,
        "catalog/manage/book_form.html",
        {"form": form, "book": None, "is_create": True},
    )


@staff_required
def manage_book_edit(request, slug):
    book = get_object_or_404(Book, slug=slug)
    old_file = book.file.name if book.file else None
    old_cover = book.cover.name if book.cover else None

    if request.method == "POST":
        form = BookForm(request.POST, request.FILES, instance=book)
        if form.is_valid():
            saved = form.save()
            if old_file and old_file != saved.file.name:
                _delete_named_file(saved.file.storage, old_file)
            if old_cover and old_cover != saved.cover.name:
                _delete_named_file(saved.cover.storage, old_cover)
            messages.success(request, f"“{saved.title}” was updated.")
            return redirect("catalog:manage_book_list")
        messages.error(request, "Please fix the highlighted fields and try again.")
    else:
        form = BookForm(instance=book)

    return render(
        request,
        "catalog/manage/book_form.html",
        {"form": form, "book": book, "is_create": False},
    )


@staff_required
def manage_book_delete(request, slug):
    book = get_object_or_404(Book, slug=slug)
    if request.method == "POST":
        title = book.title
        book.delete()
        messages.success(request, f"“{title}” was deleted from the catalog.")
        return redirect("catalog:manage_book_list")
    return render(
        request,
        "catalog/manage/book_confirm_delete.html",
        {"book": book},
    )
