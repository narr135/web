from datetime import date

from django import forms
from django.core.exceptions import ValidationError

from .models import Book, Category
from .validators import normalize_isbn, validate_book_file, validate_cover_image


class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = [
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
            "cover",
            "cover_url",
            "file",
        ]
        widgets = {
            "published_date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 4}),
        }
        help_texts = {
            "isbn": "Optional. Hyphens are fine — the checksum is verified.",
            "page_count": "Optional, but useful for the reader and future metadata.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["file"].required = not bool(self.instance and self.instance.pk)
        self.fields["category"].empty_label = "Choose a category"

        for name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, forms.Select):
                widget.attrs.setdefault("class", "form-select")
            else:
                widget.attrs.setdefault("class", "form-control")
            if name in {"title", "author"}:
                widget.attrs.setdefault("autofocus", "autofocus" if name == "title" else "")
            if name == "cover":
                widget.attrs.setdefault("accept", "image/jpeg,image/png,image/webp")
            if name == "file":
                widget.attrs.setdefault("accept", ".pdf,.epub,.txt")

    def clean_title(self):
        title = (self.cleaned_data.get("title") or "").strip()
        if not title:
            raise ValidationError("Enter the book title.")
        return title

    def clean_author(self):
        author = (self.cleaned_data.get("author") or "").strip()
        if not author:
            raise ValidationError("Enter at least one author.")
        if author.count(";") + author.count(",") > 10:
            raise ValidationError("That is too many authors for one field.")
        return author

    def clean_isbn(self):
        raw = self.cleaned_data.get("isbn")
        normalized = normalize_isbn(raw) or None
        if normalized:
            duplicate = Book.objects.filter(isbn=normalized).exclude(pk=self.instance.pk)
            if duplicate.exists():
                raise ValidationError("Another book already uses this ISBN.")
        return normalized

    def clean_published_date(self):
        published = self.cleaned_data.get("published_date")
        if published and published > date.today():
            raise ValidationError("The publication date cannot be in the future.")
        return published

    def clean_page_count(self):
        page_count = self.cleaned_data.get("page_count")
        if page_count is not None and page_count < 1:
            raise ValidationError("Page count must be at least 1.")
        return page_count

    def clean_description(self):
        description = self.cleaned_data.get("description") or ""
        if len(description) > 10000:
            raise ValidationError("Keep the description under 10,000 characters.")
        return description

    def clean_file(self):
        uploaded = self.cleaned_data.get("file")
        if uploaded and not (
            self.instance.pk and uploaded == self.instance.file
        ):
            validate_book_file(uploaded)
        return uploaded

    def clean_cover(self):
        uploaded = self.cleaned_data.get("cover")
        if uploaded and not (
            self.instance.pk and uploaded == self.instance.cover
        ):
            validate_cover_image(uploaded)
        return uploaded


class BookFilterForm(forms.Form):
    """Small helper used by templates to keep filter markup consistent."""

    q = forms.CharField(required=False, label="Search")
    category = forms.ChoiceField(required=False, label="Category")
    sort = forms.ChoiceField(
        required=False,
        label="Sort",
        choices=[
            ("newest", "Newest first"),
            ("title", "Title A–Z"),
            ("author", "Author A–Z"),
            ("popular", "Most downloaded"),
        ],
    )

    def __init__(self, *args, categories=None, **kwargs):
        super().__init__(*args, **kwargs)
        choices = [("", "All categories")]
        if categories is not None:
            choices += [(category.slug, category.name) for category in categories]
        self.fields["category"].choices = choices
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")
        self.fields["category"].widget.attrs["class"] = "form-select"
        self.fields["sort"].widget.attrs["class"] = "form-select"
        self.fields["q"].widget.attrs.setdefault("placeholder", "Title, author, or ISBN")
