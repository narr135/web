import hashlib
import uuid
from pathlib import Path

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from .validators import BookFileValidator, CoverImageValidator, normalize_isbn, validate_isbn


def _unique_slug(instance, value, slug_field="slug"):
    base = slugify(value)[:220] or "item"
    slug = base
    counter = 2
    queryset = type(instance).objects.exclude(pk=instance.pk)
    while queryset.filter(**{slug_field: slug}).exists():
        slug = f"{base}-{counter}"
        counter += 1
    return slug


def _hash_field_file(field_file):
    """Return a SHA-256 checksum without consuming the uploaded file."""
    handle = field_file.file
    position = handle.tell() if hasattr(handle, "tell") else 0
    digest = hashlib.sha256()
    try:
        handle.seek(0)
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    finally:
        handle.seek(position)
    return digest.hexdigest()


def book_file_path(instance, filename):
    suffix = Path(filename).suffix.lower()
    return f"books/{uuid.uuid4().hex}{suffix}"


def book_cover_path(instance, filename):
    suffix = Path(filename).suffix.lower()
    return f"covers/{uuid.uuid4().hex}{suffix}"


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = _unique_slug(self, self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return f"{reverse('catalog:book_list')}?category={self.slug}"


class Book(models.Model):
    READABLE_FORMATS = {"pdf", "epub", "txt"}

    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=255, blank=True)
    slug = models.SlugField(max_length=280, unique=True, blank=True)
    author = models.CharField(
        max_length=255,
        help_text="Separate multiple authors with a comma or semicolon.",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="books",
    )
    isbn = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        unique=True,
        validators=[validate_isbn],
    )
    publisher = models.CharField(max_length=255, blank=True)
    published_date = models.DateField(blank=True, null=True)
    language = models.CharField(max_length=32, blank=True, default="English")
    page_count = models.PositiveIntegerField(blank=True, null=True)
    description = models.TextField(blank=True)

    cover = models.ImageField(
        upload_to=book_cover_path,
        blank=True,
        null=True,
        validators=[CoverImageValidator()],
    )
    cover_url = models.URLField(
        max_length=500,
        blank=True,
        help_text="Optional remote cover, useful for future metadata imports.",
    )

    file = models.FileField(upload_to=book_file_path, validators=[BookFileValidator()])
    original_filename = models.CharField(max_length=255, blank=True)
    file_type = models.CharField(max_length=10, blank=True, editable=False)
    file_size = models.PositiveBigIntegerField(default=0, editable=False)
    sha256 = models.CharField(max_length=64, blank=True, editable=False)
    download_count = models.PositiveIntegerField(default=0, editable=False)

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_books",
    )

    # Reserved for future Google Books / Open Library integration.
    metadata_source = models.CharField(max_length=100, blank=True)
    metadata_updated_at = models.DateTimeField(blank=True, null=True)
    external_ids = models.JSONField(default=dict, blank=True)
    raw_metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["title"]),
            models.Index(fields=["author"]),
            models.Index(fields=["file_type"]),
        ]

    def __str__(self):
        return f"{self.title} — {self.author}"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_file_name = self.file.name if self.file else None

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = _unique_slug(self, self.title)
        if self.isbn:
            self.isbn = normalize_isbn(self.isbn) or None
        else:
            self.isbn = None

        file_changed = bool(
            self.file
            and (self._state.adding or self.file.name != self._original_file_name)
        )
        if file_changed:
            self.original_filename = Path(self.file.name).name
            self.file_type = Path(self.file.name).suffix.lower().lstrip(".")
            self.file_size = self.file.size
            self.sha256 = _hash_field_file(self.file)

        super().save(*args, **kwargs)
        self._original_file_name = self.file.name if self.file else None

    def get_absolute_url(self):
        return reverse("catalog:book_detail", kwargs={"slug": self.slug})

    @property
    def is_readable(self):
        return self.file_type in self.READABLE_FORMATS

    @property
    def file_extension(self):
        return self.file_type or Path(self.file.name).suffix.lstrip(".")

    @property
    def download_filename(self):
        if self.original_filename:
            return self.original_filename
        return f"{self.slug}.{self.file_extension}"

    @property
    def content_type(self):
        return {
            "pdf": "application/pdf",
            "epub": "application/epub+zip",
            "txt": "text/plain; charset=utf-8",
        }.get(self.file_type, "application/octet-stream")
