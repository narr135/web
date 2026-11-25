from django.db import transaction
from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import Book


@receiver(post_delete, sender=Book)
def delete_book_files(sender, instance, **kwargs):
    storages_and_names = []
    if instance.file and instance.file.name:
        storages_and_names.append((instance.file.storage, instance.file.name))
    if instance.cover and instance.cover.name:
        storages_and_names.append((instance.cover.storage, instance.cover.name))

    def cleanup():
        for storage, name in storages_and_names:
            try:
                if storage.exists(name):
                    storage.delete(name)
            except OSError:
                pass

    transaction.on_commit(cleanup)
