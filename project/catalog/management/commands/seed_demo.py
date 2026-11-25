import io
import textwrap
from datetime import date
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from PIL import Image, ImageDraw, ImageFont

from catalog.models import Book, Category
from library.models import ReadingProgress, Shelf, ShelfItem
from library.services import get_default_shelf

User = get_user_model()

SEED_DIR = settings.BASE_DIR / "seed_data"

CATEGORIES = {
    "Fiction": {
        "description": "Novels and stories, from Victorian classics to modern adventures.",
        "color": (47, 93, 80),
    },
    "Philosophy": {
        "description": "Strategy, ethics, and ideas that reward slow reading.",
        "color": (138, 90, 43),
    },
    "Poetry": {
        "description": "Short forms, big feelings, and lines worth returning to.",
        "color": (91, 59, 94),
    },
    "History & Politics": {
        "description": "Documents and histories that shaped the world we read in.",
        "color": (51, 74, 107),
    },
}

BOOKS = [
    {
        "title": "Alice's Adventures in Wonderland",
        "author": "Lewis Carroll",
        "category": "Fiction",
        "isbn": "9780141439761",
        "publisher": "Macmillan",
        "published_date": date(1865, 11, 26),
        "language": "English",
        "page_count": 200,
        "description": (
            "Alice follows a waistcoated White Rabbit down a hole and finds a world where "
            "logic runs sideways. A playful, strange, and endlessly quotable classic."
        ),
        "file": "alice.epub",
        "download_count": 4,
    },
    {
        "title": "Pride and Prejudice",
        "author": "Jane Austen",
        "category": "Fiction",
        "isbn": "9780141439518",
        "publisher": "T. Egerton",
        "published_date": date(1813, 1, 28),
        "language": "English",
        "page_count": 432,
        "description": (
            "Elizabeth Bennet and Mr. Darcy begin as the worst possible match and become one "
            "of literature's most beloved couples. Sharp, funny, and quietly radical."
        ),
        "file": "pride-and-prejudice.epub",
        "download_count": 7,
    },
    {
        "title": "The Art of War",
        "author": "Sun Tzu",
        "category": "Philosophy",
        "isbn": "9781590302255",
        "publisher": "Luzac & Co.",
        "published_date": date(1910, 1, 1),
        "language": "English",
        "page_count": 68,
        "description": (
            "The classic treatise on strategy, adapted across centuries for conflict, business, "
            "and everyday decision-making. This edition uses Lionel Giles's translation."
        ),
        "file": "art-of-war.txt",
        "download_count": 12,
    },
    {
        "title": "The Raven",
        "author": "Edgar Allan Poe",
        "category": "Poetry",
        "isbn": "9780141439600",
        "publisher": "The American Review",
        "published_date": date(1845, 1, 29),
        "language": "English",
        "page_count": 12,
        "description": (
            "A grieving scholar is visited by a midnight raven whose single word becomes a "
            "refrain. Poe's most famous poem, in a short reading edition."
        ),
        "file": "the-raven.txt",
        "download_count": 3,
    },
    {
        "title": "The Declaration of Independence",
        "author": "The Continental Congress",
        "category": "History & Politics",
        "publisher": "Continental Congress",
        "published_date": date(1776, 7, 4),
        "language": "English",
        "page_count": 3,
        "description": (
            "The unanimous declaration of the thirteen united States of America, adopted on "
            "July 4, 1776. A three-page reading edition of the public-domain text."
        ),
        "file": "the-declaration-of-independence.pdf",
        "download_count": 2,
    },
]


def _font(size, bold=False):
    candidates = [
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/TTF/DejaVuSerif-Bold.ttf" if bold else "/usr/share/fonts/TTF/DejaVuSerif.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _gradient_cover(title, author, color):
    width, height = 600, 900
    image = Image.new("RGB", (width, height), color)
    draw = ImageDraw.Draw(image)

    dark = tuple(max(0, channel - 45) for channel in color)
    for y in range(height):
        ratio = y / height
        row = tuple(
            int(color[channel] * (1 - ratio) + dark[channel] * ratio)
            for channel in range(3)
        )
        draw.line([(0, y), (width, y)], fill=row)

    draw.rectangle([34, 34, width - 34, height - 34], outline=(255, 255, 255, 70), width=2)
    draw.rectangle([52, 52, width - 52, height - 52], outline=(255, 255, 255, 40), width=1)

    title_font = _font(46, bold=True)
    author_font = _font(23)
    small_font = _font(15)

    wrapped = textwrap.wrap(title, width=17)
    line_height = 54
    total_height = len(wrapped) * line_height
    start_y = (height - total_height) // 2 - 40
    for index, line in enumerate(wrapped):
        bbox = draw.textbbox((0, 0), line, font=title_font)
        x = (width - (bbox[2] - bbox[0])) / 2
        draw.text((x, start_y + index * line_height), line, font=title_font, fill=(255, 250, 240))

    author_text = author.upper()
    bbox = draw.textbbox((0, 0), author_text, font=author_font)
    draw.text(
        ((width - (bbox[2] - bbox[0])) / 2, start_y + total_height + 34),
        author_text,
        font=author_font,
        fill=(245, 232, 205),
    )

    footer = "LIBRA  ·  PUBLIC DOMAIN EDITION"
    bbox = draw.textbbox((0, 0), footer, font=small_font)
    draw.text(
        ((width - (bbox[2] - bbox[0])) / 2, height - 100),
        footer,
        font=small_font,
        fill=(255, 250, 240),
    )

    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=88, optimize=True)
    buffer.seek(0)
    return buffer


class Command(BaseCommand):
    help = "Create demo categories, books, users, and shelves. Safe to run more than once."

    def handle(self, *args, **options):
        if not SEED_DIR.exists():
            raise CommandError(f"Seed data folder not found: {SEED_DIR}")

        with transaction.atomic():
            admin, reader = self._create_users()
            categories = self._create_categories()
            books = self._create_books(categories, admin)
            self._create_reader_library(reader, books)

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Demo data is ready."))
        self.stdout.write(f"  Books:      {Book.objects.count()}")
        self.stdout.write(f"  Categories: {Category.objects.count()}")
        self.stdout.write("")
        self.stdout.write("Demo accounts (local development only):")
        self.stdout.write("  Staff:  admin / admin12345")
        self.stdout.write("  Reader: reader / reader12345")
        self.stdout.write("")
        self.stdout.write("Run the server with: .venv/bin/python manage.py runserver")

    def _create_users(self):
        admin, admin_created = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@example.com",
                "is_staff": True,
                "is_superuser": True,
                "first_name": "Library",
                "last_name": "Admin",
            },
        )
        if admin_created:
            admin.set_password("admin12345")
            admin.is_staff = True
            admin.is_superuser = True
            admin.save()
            self.stdout.write("  Created staff user: admin")
        else:
            self.stdout.write("  Staff user 'admin' already exists; password unchanged.")

        reader, reader_created = User.objects.get_or_create(
            username="reader",
            defaults={"email": "reader@example.com", "first_name": "Demo", "last_name": "Reader"},
        )
        if reader_created:
            reader.set_password("reader12345")
            reader.save()
            self.stdout.write("  Created reader user: reader")
        else:
            self.stdout.write("  Reader user 'reader' already exists; password unchanged.")

        return admin, reader

    def _create_categories(self):
        categories = {}
        for name, data in CATEGORIES.items():
            category, created = Category.objects.get_or_create(
                name=name,
                defaults={"description": data["description"]},
            )
            categories[name] = category
            if created:
                self.stdout.write(f"  Added category: {name}")
        return categories

    def _create_books(self, categories, admin):
        books = {}
        for data in BOOKS:
            file_name = data["file"]
            source = SEED_DIR / file_name
            if not source.exists():
                raise CommandError(f"Missing seed file: {source}")

            book, created = Book.objects.get_or_create(
                title=data["title"],
                author=data["author"],
                defaults={
                    "category": categories[data["category"]],
                    "isbn": data.get("isbn"),
                    "publisher": data.get("publisher", ""),
                    "published_date": data.get("published_date"),
                    "language": data.get("language", "English"),
                    "page_count": data.get("page_count"),
                    "description": data.get("description", ""),
                    "uploaded_by": admin,
                    "download_count": data.get("download_count", 0),
                },
            )
            if not created:
                self.stdout.write(f"  Book already exists: {book.title}")
                books[book.title] = book
                continue

            with source.open("rb") as handle:
                book.file = File(handle, name=file_name)
                book.save()

            cover = _gradient_cover(
                book.title,
                book.author,
                CATEGORIES[data["category"]]["color"],
            )
            book.cover = File(cover, name=f"{book.slug}-cover.jpg")
            book.save()

            books[book.title] = book
            self.stdout.write(f"  Added book: {book.title} ({book.file_type})")

        return books

    def _create_reader_library(self, reader, books):
        default_shelf = get_default_shelf(reader)
        weekend, _ = Shelf.objects.get_or_create(user=reader, name="Weekend reading")

        shelf_plan = {
            default_shelf: [
                "Alice's Adventures in Wonderland",
                "The Art of War",
            ],
            weekend: [
                "The Raven",
                "The Declaration of Independence",
            ],
        }
        for shelf, titles in shelf_plan.items():
            for position, title in enumerate(titles, start=1):
                book = books.get(title)
                if book is None:
                    continue
                ShelfItem.objects.get_or_create(
                    shelf=shelf,
                    book=book,
                    defaults={"position": position},
                )

        art_of_war = books.get("The Art of War")
        if art_of_war:
            ReadingProgress.objects.get_or_create(
                user=reader,
                book=art_of_war,
                defaults={"locator": {"kind": "txt", "ratio": 0.18}, "percent": 18},
            )
