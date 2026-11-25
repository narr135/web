from django.urls import path

from . import views

app_name = "library"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("shelves/new/", views.shelf_create, name="shelf_create"),
    path("shelves/<int:pk>/", views.shelf_detail, name="shelf_detail"),
    path("shelves/<int:pk>/edit/", views.shelf_edit, name="shelf_edit"),
    path("shelves/<int:pk>/delete/", views.shelf_delete, name="shelf_delete"),
    path("shelves/<int:pk>/add/", views.shelf_add_book, name="shelf_add_to"),
    path("add-book/", views.shelf_add_book, name="shelf_add"),
    path("items/<int:pk>/remove/", views.shelf_remove_book, name="shelf_remove"),
    path("shelves/<int:pk>/reorder/", views.shelf_reorder, name="shelf_reorder"),
]
