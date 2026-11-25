from django.urls import path

from . import views

app_name = "catalog"

urlpatterns = [
    path("", views.home, name="home"),
    path("books/", views.book_list, name="book_list"),
    path("books/<slug:slug>/", views.book_detail, name="book_detail"),
    path("books/<slug:slug>/read/", views.reader, name="reader"),
    path("books/<slug:slug>/file/", views.book_file, name="book_file"),
    path("books/<slug:slug>/download/", views.book_download, name="book_download"),
    path("manage/", views.manage_dashboard, name="manage_dashboard"),
    path("manage/books/", views.manage_book_list, name="manage_book_list"),
    path("manage/books/new/", views.manage_book_create, name="manage_book_create"),
    path("manage/books/<slug:slug>/edit/", views.manage_book_edit, name="manage_book_edit"),
    path("manage/books/<slug:slug>/delete/", views.manage_book_delete, name="manage_book_delete"),
]
