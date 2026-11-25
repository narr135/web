import io
import tempfile
import zipfile
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .forms import BookForm
from .models import Book, Category

User = get_user_model()
TEST_MEDIA_ROOT = tempfile.mkdtemp(prefix="libra-test-media-")

PDF_BYTES = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF\n"


def epub_bytes():
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("mimetype", "application/epub+zip")
        archive.writestr(
            "META-INF/container.xml",
            '<?xml version="1.0"?><container version="1.0"></container>',
        )
    return buffer.getvalue()


def make_book(**overrides):
    category = overrides.pop("category", None) or Category.objects.get_or_create(
        name="Fiction"
    )[0]
    data = {
        "title": "Test Book",
        "author": "Test Author",
        "category": category,
        "language": "English",
        "file": SimpleUploadedFile(
            "test-book.pdf", PDF_BYTES, content_type="application/pdf"
        ),
    }
    data.update(overrides)
    return Book.objects.create(**data)


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class BookModelTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Fiction")

    def test_slug_and_file_metadata_are_generated(self):
        book = make_book(category=self.category)
        self.assertEqual(book.slug, "test-book")
        self.assertEqual(book.file_type, "pdf")
        self.assertEqual(book.original_filename, "test-book.pdf")
        self.assertGreater(book.file_size, 0)
        self.assertEqual(len(book.sha256), 64)
        self.assertTrue(book.is_readable)

    def test_duplicate_titles_receive_unique_slugs(self):
        first = make_book(category=self.category)
        second = make_book(category=self.category)
        self.assertEqual(first.slug, "test-book")
        self.assertEqual(second.slug, "test-book-2")

    def test_blank_isbn_is_stored_as_null(self):
        book = make_book(category=self.category, isbn="")
        self.assertIsNone(book.isbn)

    def test_isbn_is_normalized(self):
        book = make_book(category=self.category, isbn="978-0-14-143951-8")
        self.assertEqual(book.isbn, "9780141439518")

    def test_delete_signal_removes_files(self):
        book = make_book(category=self.category)
        storage = book.file.storage
        name = book.file.name
        self.assertTrue(storage.exists(name))
        with self.captureOnCommitCallbacks(execute=True):
            book.delete()
        self.assertFalse(storage.exists(name))


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class BookFormTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Fiction")

    def base_data(self, **overrides):
        data = {
            "title": "A New Book",
            "subtitle": "",
            "author": "A. Writer",
            "category": self.category.pk,
            "isbn": "",
            "publisher": "",
            "published_date": "",
            "language": "English",
            "page_count": "",
            "description": "",
            "cover_url": "",
        }
        data.update(overrides)
        return data

    def test_valid_txt_upload(self):
        form = BookForm(
            data=self.base_data(),
            files={
                "file": SimpleUploadedFile(
                    "novel.txt", b"Once upon a time.\n", content_type="text/plain"
                )
            },
        )
        self.assertTrue(form.is_valid(), form.errors)
        book = form.save()
        self.assertEqual(book.file_type, "txt")

    def test_author_is_required(self):
        form = BookForm(
            data=self.base_data(author="   "),
            files={"file": SimpleUploadedFile("a.pdf", PDF_BYTES)},
        )
        self.assertFalse(form.is_valid())
        self.assertIn("author", form.errors)

    def test_invalid_pdf_content_is_rejected(self):
        form = BookForm(
            data=self.base_data(),
            files={"file": SimpleUploadedFile("fake.pdf", b"not really a pdf")},
        )
        self.assertFalse(form.is_valid())
        self.assertIn("file", form.errors)

    def test_invalid_epub_content_is_rejected(self):
        form = BookForm(
            data=self.base_data(),
            files={"file": SimpleUploadedFile("fake.epub", b"PK not an epub")},
        )
        self.assertFalse(form.is_valid())
        self.assertIn("file", form.errors)

    def test_valid_epub_content_is_accepted(self):
        form = BookForm(
            data=self.base_data(),
            files={"file": SimpleUploadedFile("real.epub", epub_bytes())},
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_invalid_isbn_checksum_is_rejected(self):
        form = BookForm(
            data=self.base_data(isbn="9780141439519"),
            files={"file": SimpleUploadedFile("a.pdf", PDF_BYTES)},
        )
        self.assertFalse(form.is_valid())
        self.assertIn("isbn", form.errors)

    def test_duplicate_isbn_is_rejected(self):
        make_book(category=self.category, isbn="9780141439518")
        form = BookForm(
            data=self.base_data(isbn="978-0-14-143951-8"),
            files={"file": SimpleUploadedFile("a.txt", b"hello")},
        )
        self.assertFalse(form.is_valid())
        self.assertIn("isbn", form.errors)

    def test_future_publication_date_is_rejected(self):
        form = BookForm(
            data=self.base_data(published_date="2999-01-01"),
            files={"file": SimpleUploadedFile("a.pdf", PDF_BYTES)},
        )
        self.assertFalse(form.is_valid())
        self.assertIn("published_date", form.errors)

    @override_settings(MAX_BOOK_UPLOAD_BYTES=10)
    def test_oversized_file_is_rejected(self):
        form = BookForm(
            data=self.base_data(),
            files={"file": SimpleUploadedFile("a.pdf", PDF_BYTES + b"x" * 20)},
        )
        self.assertFalse(form.is_valid())
        self.assertIn("file", form.errors)

    def test_edit_without_new_file_is_valid(self):
        book = make_book(category=self.category)
        form = BookForm(
            data=self.base_data(
                title="Renamed",
                author=book.author,
                isbn="",
                language=book.language,
            ),
            instance=book,
        )
        self.assertTrue(form.is_valid(), form.errors)
        saved = form.save()
        self.assertEqual(saved.title, "Renamed")
        self.assertEqual(saved.pk, book.pk)


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class CatalogViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(name="Fiction")
        cls.staff = User.objects.create_user(
            username="staff", password="staffpass123", is_staff=True
        )
        cls.reader = User.objects.create_user(
            username="reader", password="readerpass123"
        )
        cls.other = User.objects.create_user(
            username="other", password="otherpass123"
        )
        cls.book = make_book(
            category=cls.category,
            title="Alice in Testing",
            author="Test Carroll",
        )

    def test_home_and_catalog_are_public(self):
        self.assertEqual(self.client.get(reverse("catalog:home")).status_code, 200)
        self.assertEqual(self.client.get(reverse("catalog:book_list")).status_code, 200)

    def test_search_finds_title_and_author(self):
        response = self.client.get(reverse("catalog:book_list"), {"q": "Alice"})
        self.assertContains(response, "Alice in Testing")
        response = self.client.get(reverse("catalog:book_list"), {"q": "Carroll"})
        self.assertContains(response, "Alice in Testing")

    def test_category_filter(self):
        response = self.client.get(
            reverse("catalog:book_list"), {"category": self.category.slug}
        )
        self.assertContains(response, "Alice in Testing")

    def test_guest_cannot_open_manage(self):
        response = self.client.get(reverse("catalog:manage_book_list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_member_cannot_open_manage(self):
        self.client.login(username="reader", password="readerpass123")
        response = self.client.get(reverse("catalog:manage_book_list"))
        self.assertEqual(response.status_code, 403)

    def test_staff_can_open_manage(self):
        self.client.login(username="staff", password="staffpass123")
        response = self.client.get(reverse("catalog:manage_book_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Alice in Testing")

    def test_staff_can_create_book(self):
        self.client.login(username="staff", password="staffpass123")
        response = self.client.post(
            reverse("catalog:manage_book_create"),
            {
                "title": "Created Book",
                "subtitle": "",
                "author": "Created Author",
                "category": self.category.pk,
                "isbn": "",
                "publisher": "Libra Press",
                "published_date": "",
                "language": "English",
                "page_count": "10",
                "description": "A test.",
                "cover_url": "",
                "file": SimpleUploadedFile(
                    "created.txt", b"Created text.", content_type="text/plain"
                ),
            },
        )
        self.assertRedirects(response, reverse("catalog:manage_book_list"))
        self.assertTrue(Book.objects.filter(title="Created Book").exists())

    def test_staff_create_with_bad_file_shows_error(self):
        self.client.login(username="staff", password="staffpass123")
        before = Book.objects.count()
        response = self.client.post(
            reverse("catalog:manage_book_create"),
            {
                "title": "Bad Book",
                "author": "Bad Author",
                "category": self.category.pk,
                "language": "English",
                "file": SimpleUploadedFile("bad.pdf", b"not a pdf"),
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "does not look like a valid PDF")
        self.assertEqual(Book.objects.count(), before)

    def test_staff_can_edit_and_delete_book(self):
        self.client.login(username="staff", password="staffpass123")
        response = self.client.post(
            reverse("catalog:manage_book_edit", kwargs={"slug": self.book.slug}),
            {
                "title": "Edited Title",
                "subtitle": "",
                "author": self.book.author,
                "category": self.category.pk,
                "isbn": "",
                "publisher": "",
                "published_date": "",
                "language": "English",
                "page_count": "",
                "description": "",
                "cover_url": "",
            },
        )
        self.assertRedirects(response, reverse("catalog:manage_book_list"))
        self.book.refresh_from_db()
        self.assertEqual(self.book.title, "Edited Title")

        storage = self.book.file.storage
        stored_name = self.book.file.name
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                reverse(
                    "catalog:manage_book_delete",
                    kwargs={"slug": self.book.slug},
                )
            )
        self.assertRedirects(response, reverse("catalog:manage_book_list"))
        self.assertFalse(Book.objects.filter(pk=self.book.pk).exists())
        self.assertFalse(storage.exists(stored_name))

    def test_download_increments_counter_and_uses_attachment(self):
        url = reverse("catalog:book_download", kwargs={"slug": self.book.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("attachment", response["Content-Disposition"])
        b"".join(response.streaming_content)
        self.book.refresh_from_db()
        self.assertEqual(self.book.download_count, 1)

    def test_file_endpoint_is_inline_with_correct_content_type(self):
        url = reverse("catalog:book_file", kwargs={"slug": self.book.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn("inline", response["Content-Disposition"])
        b"".join(response.streaming_content)

    def test_reader_page_includes_configuration(self):
        url = reverse("catalog:reader", kwargs={"slug": self.book.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "reader-config")
        self.assertContains(response, "reader.js")

    def test_missing_file_is_handled(self):
        book = make_book(category=self.category, title="Missing File")
        Book.objects.filter(pk=book.pk).update(file="books/does-not-exist.pdf")
        response = self.client.get(
            reverse("catalog:book_file", kwargs={"slug": book.slug})
        )
        self.assertEqual(response.status_code, 404)
        response = self.client.get(
            reverse("catalog:book_download", kwargs={"slug": book.slug})
        )
        self.assertEqual(response.status_code, 302)


class StaticAssetVersionTests(TestCase):
    def test_app_assets_include_a_cache_busting_version(self):
        response = self.client.get(reverse("catalog:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "/static/css/app.css?v=")
        self.assertContains(response, "/static/js/theme.js?v=")
