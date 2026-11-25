from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Shelf(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="shelves",
    )
    name = models.CharField(max_length=100)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_default", "name"]
        constraints = [
            models.UniqueConstraint(fields=["user", "name"], name="unique_shelf_name_per_user"),
        ]

    def __str__(self):
        return f"{self.name} ({self.user.get_username()})"

    @property
    def item_count(self):
        return self.items.count()


class ShelfItem(models.Model):
    shelf = models.ForeignKey(Shelf, on_delete=models.CASCADE, related_name="items")
    book = models.ForeignKey(
        "catalog.Book",
        on_delete=models.CASCADE,
        related_name="shelf_items",
    )
    position = models.PositiveIntegerField(default=0)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["position", "id"]
        constraints = [
            models.UniqueConstraint(fields=["shelf", "book"], name="unique_book_per_shelf"),
        ]

    def __str__(self):
        return f"{self.book.title} on {self.shelf.name}"


class ReadingProgress(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reading_progress",
    )
    book = models.ForeignKey(
        "catalog.Book",
        on_delete=models.CASCADE,
        related_name="reading_progress",
    )
    locator = models.JSONField(default=dict, blank=True)
    percent = models.FloatField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-updated_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "book"], name="unique_progress_per_user_book"),
        ]

    def __str__(self):
        return f"{self.user.get_username()} — {self.book.title} ({self.percent:.0f}%)"

    @property
    def is_finished(self):
        return self.percent >= 99.0
