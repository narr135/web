import codecs
import re
import zipfile
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from PIL import Image

ALLOWED_BOOK_EXTENSIONS = {".pdf", ".epub", ".txt"}
ALLOWED_COVER_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def _reset(file_obj):
    try:
        file_obj.seek(0)
    except (AttributeError, OSError):
        pass


def _readable_size(file_obj):
    try:
        return file_obj.size
    except (AttributeError, OSError):
        return 0


def normalize_isbn(value):
    """Strip separators, validate the checksum, and return the normalized ISBN."""
    cleaned = re.sub(r"[\s-]", "", value or "").upper()
    if not cleaned:
        return ""

    if len(cleaned) == 10:
        if not re.fullmatch(r"\d{9}[\dX]", cleaned):
            raise ValidationError("An ISBN-10 must contain 9 digits and a final digit or X.")
        total = sum((10 - index) * (10 if char == "X" else int(char)) for index, char in enumerate(cleaned))
        if total % 11 != 0:
            raise ValidationError("This ISBN-10 checksum is not valid.")
    elif len(cleaned) == 13:
        if not cleaned.isdigit():
            raise ValidationError("An ISBN-13 must contain digits only.")
        total = sum(
            (1 if index % 2 == 0 else 3) * int(char)
            for index, char in enumerate(cleaned)
        )
        if total % 10 != 0:
            raise ValidationError("This ISBN-13 checksum is not valid.")
    else:
        raise ValidationError("Enter a valid 10- or 13-digit ISBN.")

    return cleaned


def validate_isbn(value):
    """Model-level wrapper around normalize_isbn for admin and other ModelForms."""
    normalize_isbn(value)


def validate_book_file(file_obj):
    """Validate extension, size, and magic bytes for uploaded book files."""
    suffix = Path(file_obj.name).suffix.lower()
    if suffix not in ALLOWED_BOOK_EXTENSIONS:
        raise ValidationError("Upload a PDF, EPUB, or TXT file.")

    maximum = getattr(settings, "MAX_BOOK_UPLOAD_BYTES", 50 * 1024 * 1024)
    if _readable_size(file_obj) > maximum:
        raise ValidationError(f"Book files must be smaller than {maximum // (1024 * 1024)} MB.")

    try:
        if suffix == ".pdf":
            header = file_obj.read(1024)
            if b"%PDF-" not in header:
                raise ValidationError("This file does not look like a valid PDF.")
        elif suffix == ".epub":
            try:
                with zipfile.ZipFile(file_obj) as archive:
                    names = set(archive.namelist())
                    if "mimetype" not in names or "META-INF/container.xml" not in names:
                        raise ValidationError("This file does not look like a valid EPUB archive.")
                    if archive.read("mimetype").strip() != b"application/epub+zip":
                        raise ValidationError("The EPUB archive has an invalid mimetype.")
            except zipfile.BadZipFile as exc:
                raise ValidationError("The EPUB archive is damaged or unreadable.") from exc
        elif suffix == ".txt":
            decoder = codecs.getincrementaldecoder("utf-8-sig")()
            try:
                while chunk := file_obj.read(1024 * 1024):
                    if b"\x00" in chunk:
                        raise ValidationError("This text file contains binary data.")
                    decoder.decode(chunk)
                decoder.decode(b"", final=True)
            except UnicodeDecodeError as exc:
                raise ValidationError("Text files must be saved as UTF-8.") from exc
    finally:
        _reset(file_obj)


def validate_cover_image(file_obj):
    suffix = Path(file_obj.name).suffix.lower()
    if suffix not in ALLOWED_COVER_EXTENSIONS:
        raise ValidationError("Covers must be JPG, PNG, or WebP images.")

    maximum = getattr(settings, "MAX_COVER_UPLOAD_BYTES", 5 * 1024 * 1024)
    if _readable_size(file_obj) > maximum:
        raise ValidationError(f"Covers must be smaller than {maximum // (1024 * 1024)} MB.")

    try:
        with Image.open(file_obj) as image:
            image.verify()
    except Exception as exc:  # Pillow raises several exception types
        raise ValidationError("This file is not a valid image.") from exc
    finally:
        _reset(file_obj)


@deconstructible
class BookFileValidator:
    def __call__(self, file_obj):
        validate_book_file(file_obj)


@deconstructible
class CoverImageValidator:
    def __call__(self, file_obj):
        validate_cover_image(file_obj)
