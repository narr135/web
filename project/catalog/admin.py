from django.contrib import admin
from django.db.models import Count
from django.urls import reverse
from django.utils.html import format_html

from .models import Book, Category

admin.site.site_header = "Libra administration"
admin.site.site_title = "Libra admin"
admin.site.index_title = "Library catalog"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "book_count", "created_at")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at",)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(total_books=Count("books"))

    @admin.display(description="Books", ordering="total_books")
    def book_count(self, obj):
        return obj.total_books


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "author",
        "category",
        "file_type",
        "download_count",
        "created_at",
    )
    list_filter = ("category", "file_type", "language")
    search_fields = ("title", "author", "isbn", "publisher")
    readonly_fields = (
        "slug",
        "file_type",
        "file_size",
        "sha256",
        "download_count",
        "original_filename",
        "uploaded_by",
        "created_at",
        "updated_at",
        "metadata_updated_at",
        "file_link",
    )
    fieldsets = (
        (
            "Book",
            {
                "fields": (
                    "title",
                    "subtitle",
                    "author",
                    "category",
                    "isbn",
                    "publisher",
                    "published_date",
                    "language",
                    "page_count",
                    "description",
                )
            },
        ),
        (
            "Files",
            {
                "fields": (
                    "file",
                    "file_link",
                    "original_filename",
                    "file_type",
                    "file_size",
                    "sha256",
                    "cover",
                    "cover_url",
                )
            },
        ),
        (
            "Library data",
            {
                "fields": (
                    "slug",
                    "download_count",
                    "uploaded_by",
                    "created_at",
                    "updated_at",
                )
            },
        ),
        (
            "Metadata (reserved for future imports)",
            {
                "classes": ("collapse",),
                "fields": (
                    "metadata_source",
                    "metadata_updated_at",
                    "external_ids",
                    "raw_metadata",
                ),
            },
        ),
    )

    @admin.display(description="Current file")
    def file_link(self, obj):
        if not obj or not obj.pk or not obj.file:
            return "—"
        url = reverse("catalog:book_file", kwargs={"slug": obj.slug})
        return format_html('<a href="{}" target="_blank">Open / preview</a>', url)

    def save_model(self, request, obj, form, change):
        if not obj.uploaded_by_id:
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)
