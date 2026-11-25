import json
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from catalog.models import Book, Category
from library.models import ReadingProgress, Shelf, ShelfItem
from library.services import get_default_shelf

User = get_user_model()
TEST_MEDIA_ROOT = tempfile.mkdtemp(prefix="libra-library-test-media-")

PDF_BYTES = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF\n"


def make_book(title="Shelf Book", **overrides):
    category = overrides.pop("category", None) or Category.objects.get_or_create(
        name="Fiction"
    )[0]
    data = {
        "title": title,
        "author": "Test Author",
        "category": category,
        "language": "English",
        "file": SimpleUploadedFile(
            f"{title.lower().replace(' ', '-')}.pdf",
            PDF_BYTES,
            content_type="application/pdf",
        ),
    }
    data.update(overrides)
    return Book.objects.create(**data)


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class DefaultShelfTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="reader", password="secret12345")

    def test_default_shelf_is_created_once(self):
        first = get_default_shelf(self.user)
        second = get_default_shelf(self.user)
        self.assertEqual(first.pk, second.pk)
        self.assertTrue(first.is_default)
        self.assertEqual(Shelf.objects.filter(user=self.user).count(), 1)

    def test_existing_named_shelf_is_promoted(self):
        shelf = Shelf.objects.create(user=self.user, name="My Shelf")
        promoted = get_default_shelf(self.user)
        self.assertEqual(promoted.pk, shelf.pk)
        shelf.refresh_from_db()
        self.assertTrue(shelf.is_default)

    def test_default_shelf_is_per_user(self):
        other = User.objects.create_user(username="other", password="secret12345")
        mine = get_default_shelf(self.user)
        theirs = get_default_shelf(other)
        self.assertNotEqual(mine.pk, theirs.pk)
        self.assertEqual(mine.user, self.user)
        self.assertEqual(theirs.user, other)


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class RegistrationTests(TestCase):
    def test_registration_creates_account_and_default_shelf(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "newreader",
                "email": "new@example.com",
                "password1": "a-strong-password-9",
                "password2": "a-strong-password-9",
            },
        )
        self.assertRedirects(response, reverse("library:dashboard"))
        user = User.objects.get(username="newreader")
        self.assertEqual(user.email, "new@example.com")
        self.assertTrue(Shelf.objects.filter(user=user, is_default=True).exists())
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

    def test_registration_rejects_mismatched_passwords(self):
        before = User.objects.count()
        response = self.client.post(
            reverse("register"),
            {
                "username": "newreader",
                "email": "",
                "password1": "a-strong-password-9",
                "password2": "different-password-9",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.count(), before)
        self.assertIn("password2", response.context["form"].errors)

    def test_duplicate_username_is_rejected(self):
        User.objects.create_user(username="taken", password="secret12345")
        response = self.client.post(
            reverse("register"),
            {
                "username": "taken",
                "email": "",
                "password1": "a-strong-password-9",
                "password2": "a-strong-password-9",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.filter(username="taken").count(), 1)

    def test_logged_in_user_is_redirected_away_from_register(self):
        self.client.force_login(
            User.objects.create_user(username="reader", password="secret12345")
        )
        response = self.client.get(reverse("register"))
        self.assertRedirects(response, reverse("library:dashboard"))


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class ShelfViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="reader", password="secret12345")
        self.other = User.objects.create_user(username="other", password="secret12345")
        self.book = make_book()
        self.client.force_login(self.user)

    def test_dashboard_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("library:dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_dashboard_creates_default_shelf_and_lists_books(self):
        shelf = get_default_shelf(self.user)
        shelf.items.create(book=self.book, position=1)
        response = self.client.get(reverse("library:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "My Shelf")
        self.assertContains(response, "1 book on this shelf")

        detail = self.client.get(
            reverse("library:shelf_detail", kwargs={"pk": shelf.pk})
        )
        self.assertContains(detail, "Shelf Book")

    def test_shelf_create(self):
        response = self.client.post(
            reverse("library:shelf_create"), {"name": "Weekend reading"}
        )
        shelf = Shelf.objects.get(user=self.user, name="Weekend reading")
        self.assertRedirects(response, reverse("library:shelf_detail", kwargs={"pk": shelf.pk}))
        self.assertFalse(shelf.is_default)

    def test_shelf_create_rejects_duplicate_name(self):
        Shelf.objects.create(user=self.user, name="Weekend reading")
        response = self.client.post(
            reverse("library:shelf_create"), {"name": "weekend reading"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "already have a shelf")
        self.assertEqual(Shelf.objects.filter(user=self.user).count(), 2)

    def test_shelf_create_rejects_blank_name(self):
        response = self.client.post(reverse("library:shelf_create"), {"name": "   "})
        self.assertEqual(response.status_code, 200)
        self.assertIn("name", response.context["form"].errors)
        self.assertEqual(Shelf.objects.filter(user=self.user).count(), 1)

    def test_shelf_create_enforces_limit(self):
        for index in range(19):
            Shelf.objects.create(user=self.user, name=f"Shelf {index}")
        self.assertEqual(Shelf.objects.filter(user=self.user).count(), 19)
        # Creating the default shelf brings the user to 20, which is still allowed.
        response = self.client.post(reverse("library:shelf_create"), {"name": "One more"})
        self.assertContains(response, "at most 20 shelves")
        self.assertFalse(Shelf.objects.filter(user=self.user, name="One more").exists())

    def test_shelf_rename(self):
        shelf = Shelf.objects.create(user=self.user, name="Old name")
        response = self.client.post(
            reverse("library:shelf_edit", kwargs={"pk": shelf.pk}),
            {"name": "New name"},
        )
        self.assertRedirects(response, reverse("library:shelf_detail", kwargs={"pk": shelf.pk}))
        shelf.refresh_from_db()
        self.assertEqual(shelf.name, "New name")

    def test_shelf_delete(self):
        shelf = Shelf.objects.create(user=self.user, name="Temporary")
        response = self.client.post(
            reverse("library:shelf_delete", kwargs={"pk": shelf.pk})
        )
        self.assertRedirects(response, reverse("library:dashboard"))
        self.assertFalse(Shelf.objects.filter(pk=shelf.pk).exists())

    def test_default_shelf_cannot_be_deleted(self):
        shelf = get_default_shelf(self.user)
        response = self.client.post(
            reverse("library:shelf_delete", kwargs={"pk": shelf.pk})
        )
        self.assertRedirects(response, reverse("library:shelf_detail", kwargs={"pk": shelf.pk}))
        self.assertTrue(Shelf.objects.filter(pk=shelf.pk).exists())

    def test_other_users_shelf_is_not_visible(self):
        shelf = Shelf.objects.create(user=self.other, name="Private")
        response = self.client.get(
            reverse("library:shelf_detail", kwargs={"pk": shelf.pk})
        )
        self.assertEqual(response.status_code, 404)

    def test_other_users_shelf_cannot_be_edited_or_deleted(self):
        shelf = Shelf.objects.create(user=self.other, name="Private")
        response = self.client.post(
            reverse("library:shelf_edit", kwargs={"pk": shelf.pk}),
            {"name": "Hijacked"},
        )
        self.assertEqual(response.status_code, 404)
        response = self.client.post(
            reverse("library:shelf_delete", kwargs={"pk": shelf.pk})
        )
        self.assertEqual(response.status_code, 404)
        shelf.refresh_from_db()
        self.assertEqual(shelf.name, "Private")

    def test_add_book_to_named_shelf(self):
        shelf = Shelf.objects.create(user=self.user, name="Want to read")
        response = self.client.post(
            reverse("library:shelf_add_to", kwargs={"pk": shelf.pk}),
            {"book_id": self.book.pk},
        )
        self.assertRedirects(response, self.book.get_absolute_url())
        item = ShelfItem.objects.get(shelf=shelf, book=self.book)
        self.assertEqual(item.position, 1)

    def test_add_book_without_shelf_uses_default(self):
        response = self.client.post(
            reverse("library:shelf_add"), {"book_id": self.book.pk}
        )
        self.assertRedirects(response, self.book.get_absolute_url())
        default = Shelf.objects.get(user=self.user, is_default=True)
        self.assertTrue(default.items.filter(book=self.book).exists())

    def test_adding_same_book_twice_is_idempotent(self):
        shelf = Shelf.objects.create(user=self.user, name="Want to read")
        url = reverse("library:shelf_add_to", kwargs={"pk": shelf.pk})
        self.client.post(url, {"book_id": self.book.pk})
        self.client.post(url, {"book_id": self.book.pk})
        self.assertEqual(ShelfItem.objects.filter(shelf=shelf, book=self.book).count(), 1)

    def test_cannot_add_to_another_users_shelf(self):
        shelf = Shelf.objects.create(user=self.other, name="Private")
        response = self.client.post(
            reverse("library:shelf_add_to", kwargs={"pk": shelf.pk}),
            {"book_id": self.book.pk},
        )
        self.assertEqual(response.status_code, 404)
        self.assertFalse(ShelfItem.objects.filter(shelf=shelf).exists())

    def test_get_cannot_add_book(self):
        shelf = Shelf.objects.create(user=self.user, name="Want to read")
        response = self.client.get(
            reverse("library:shelf_add_to", kwargs={"pk": shelf.pk})
        )
        self.assertEqual(response.status_code, 405)

    def test_remove_book_from_shelf(self):
        shelf = Shelf.objects.create(user=self.user, name="Want to read")
        item = ShelfItem.objects.create(shelf=shelf, book=self.book, position=1)
        response = self.client.post(
            reverse("library:shelf_remove", kwargs={"pk": item.pk})
        )
        self.assertRedirects(response, reverse("library:shelf_detail", kwargs={"pk": shelf.pk}))
        self.assertFalse(ShelfItem.objects.filter(pk=item.pk).exists())

    def test_cannot_remove_item_from_another_users_shelf(self):
        shelf = Shelf.objects.create(user=self.other, name="Private")
        item = ShelfItem.objects.create(shelf=shelf, book=self.book, position=1)
        response = self.client.post(
            reverse("library:shelf_remove", kwargs={"pk": item.pk})
        )
        self.assertEqual(response.status_code, 404)
        self.assertTrue(ShelfItem.objects.filter(pk=item.pk).exists())

    def test_reorder_updates_positions(self):
        shelf = Shelf.objects.create(user=self.user, name="Ordered")
        second_book = make_book(title="Second Book")
        third_book = make_book(title="Third Book")
        items = [
            ShelfItem.objects.create(shelf=shelf, book=book, position=index)
            for index, book in enumerate([self.book, second_book, third_book], start=1)
        ]
        order = [items[2].pk, items[0].pk, items[1].pk]
        response = self.client.post(
            reverse("library:shelf_reorder", kwargs={"pk": shelf.pk}),
            data=json.dumps({"order": order}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"saved": True, "count": 3})
        positions = {
            item.pk: item.position for item in ShelfItem.objects.filter(shelf=shelf)
        }
        self.assertEqual(positions[items[2].pk], 1)
        self.assertEqual(positions[items[0].pk], 2)
        self.assertEqual(positions[items[1].pk], 3)

    def test_reorder_rejects_missing_items(self):
        shelf = Shelf.objects.create(user=self.user, name="Ordered")
        second_book = make_book(title="Second Book")
        first = ShelfItem.objects.create(shelf=shelf, book=self.book, position=1)
        ShelfItem.objects.create(shelf=shelf, book=second_book, position=2)
        response = self.client.post(
            reverse("library:shelf_reorder", kwargs={"pk": shelf.pk}),
            data=json.dumps({"order": [first.pk]}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())

    def test_reorder_rejects_foreign_items(self):
        shelf = Shelf.objects.create(user=self.user, name="Ordered")
        item = ShelfItem.objects.create(shelf=shelf, book=self.book, position=1)
        other_shelf = Shelf.objects.create(user=self.other, name="Private")
        foreign = ShelfItem.objects.create(
            shelf=other_shelf, book=make_book(title="Foreign"), position=1
        )
        response = self.client.post(
            reverse("library:shelf_reorder", kwargs={"pk": shelf.pk}),
            data=json.dumps({"order": [item.pk, foreign.pk]}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_reorder_rejects_malformed_payload(self):
        shelf = Shelf.objects.create(user=self.user, name="Ordered")
        ShelfItem.objects.create(shelf=shelf, book=self.book, position=1)
        for payload in ["not json", json.dumps({"order": "nope"}), json.dumps({"order": ["1"]})]:
            response = self.client.post(
                reverse("library:shelf_reorder", kwargs={"pk": shelf.pk}),
                data=payload,
                content_type="application/json",
            )
            self.assertEqual(response.status_code, 400, payload)

    def test_cannot_reorder_another_users_shelf(self):
        shelf = Shelf.objects.create(user=self.other, name="Private")
        item = ShelfItem.objects.create(shelf=shelf, book=self.book, position=1)
        response = self.client.post(
            reverse("library:shelf_reorder", kwargs={"pk": shelf.pk}),
            data=json.dumps({"order": [item.pk]}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class ProgressApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="reader", password="secret12345")
        self.other = User.objects.create_user(username="other", password="secret12345")
        self.book = make_book()

    def post_progress(self, payload, book_id=None):
        return self.client.post(
            reverse(
                "save_progress",
                kwargs={"book_id": book_id or self.book.pk},
            ),
            data=json.dumps(payload),
            content_type="application/json",
        )

    def test_progress_requires_login(self):
        response = self.post_progress({"locator": {"kind": "pdf", "page": 2}, "percent": 20})
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_progress_is_created_and_updated(self):
        self.client.force_login(self.user)
        response = self.post_progress(
            {"locator": {"kind": "pdf", "page": 2}, "percent": 20}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["saved"])
        progress = ReadingProgress.objects.get(user=self.user, book=self.book)
        self.assertEqual(progress.percent, 20)
        self.assertEqual(progress.locator, {"kind": "pdf", "page": 2})

        response = self.post_progress(
            {"locator": {"kind": "pdf", "page": 5}, "percent": 55.556}
        )
        self.assertEqual(response.status_code, 200)
        progress.refresh_from_db()
        self.assertEqual(progress.percent, 55.56)
        self.assertEqual(progress.locator, {"kind": "pdf", "page": 5})
        self.assertEqual(ReadingProgress.objects.filter(user=self.user).count(), 1)

    def test_progress_is_per_user(self):
        self.client.force_login(self.user)
        self.post_progress({"locator": {"kind": "txt", "ratio": 0.4}, "percent": 40})
        self.assertTrue(
            ReadingProgress.objects.filter(user=self.user, book=self.book).exists()
        )
        self.assertFalse(
            ReadingProgress.objects.filter(user=self.other, book=self.book).exists()
        )

    def test_progress_rejects_invalid_json(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("save_progress", kwargs={"book_id": self.book.pk}),
            data="not json",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_progress_rejects_percent_out_of_range(self):
        self.client.force_login(self.user)
        for percent in (-0.1, 100.1, "abc", None):
            response = self.post_progress({"locator": {}, "percent": percent})
            self.assertEqual(response.status_code, 400, percent)

    def test_progress_rejects_invalid_locator(self):
        self.client.force_login(self.user)
        for locator in ([], "cfi", 5, None):
            response = self.post_progress({"locator": locator, "percent": 10})
            self.assertEqual(response.status_code, 400, locator)

    def test_progress_rejects_oversized_locator(self):
        self.client.force_login(self.user)
        response = self.post_progress(
            {"locator": {"cfi": "x" * 5000}, "percent": 10}
        )
        self.assertEqual(response.status_code, 400)

    def test_progress_unknown_book_is_404(self):
        self.client.force_login(self.user)
        response = self.post_progress({"locator": {}, "percent": 10}, book_id=999999)
        self.assertEqual(response.status_code, 404)

    def test_get_progress_is_not_allowed(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("save_progress", kwargs={"book_id": self.book.pk})
        )
        self.assertEqual(response.status_code, 405)


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class ReaderResumeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="reader", password="secret12345")
        self.book = make_book()

    def reader_config(self):
        response = self.client.get(
            reverse("catalog:reader", kwargs={"slug": self.book.slug})
        )
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        marker = '<script id="reader-config" type="application/json">'
        start = html.index(marker) + len(marker)
        end = html.index("</script>", start)
        return json.loads(html[start:end])

    def test_guest_config_has_no_saved_progress(self):
        config = self.reader_config()
        self.assertFalse(config["isAuthenticated"])
        self.assertEqual(config["initialPercent"], 0)
        self.assertEqual(config["initialLocator"], {})

    def test_logged_in_config_exposes_saved_progress(self):
        ReadingProgress.objects.create(
            user=self.user,
            book=self.book,
            locator={"kind": "pdf", "page": 4},
            percent=42,
        )
        self.client.force_login(self.user)
        config = self.reader_config()
        self.assertTrue(config["isAuthenticated"])
        self.assertEqual(config["initialPercent"], 42)
        self.assertEqual(config["initialLocator"], {"kind": "pdf", "page": 4})
