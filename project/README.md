# Libra

A small library management system built with Django and SQLite. Visitors can browse
the catalog, read books in the browser, and download files. Members get saved reading
progress and personal, reorderable shelves. Staff manage the catalog from a dedicated
web interface, while categories live in the Django admin.

This project was built for a web development course assignment. It focuses on complete
CRUD, server-side validation, clear error messages, and data that survives a restart.

---

## Features

### Public (no account required)

- Browse the catalog with search by title, author, or ISBN.
- Filter by category and sort by newest, title, author, or downloads.
- Paginated results.
- Book detail pages with metadata and related titles.
- Read PDF, EPUB, and TXT files in the built-in browser reader:
  - PDF.js for PDF navigation, page numbers, and zoom.
  - ePub.js for paginated EPUB reading and font-size controls.
  - Plain-text view with adjustable font size.
- Download any book.
- Light and dark theme, remembered in `localStorage`.

### Registered members

- Register and log in with a username and password. No email confirmation.
- A default shelf (`My Shelf`) is created automatically.
- Create, rename, and delete custom shelves (up to 20 per account).
- Add and remove books from shelves.
- Drag and drop shelf items to reorder them; the order is saved to the database.
- Reading progress is saved per account and per book:
  - PDF: current page.
  - EPUB: EPUB CFI location.
  - TXT: scroll ratio.
- "Continue reading" cards on the home page and dashboard.
- Progress cannot be read or changed by another account.

### Staff

- Staff dashboard with counts and a missing-file warning.
- Create, edit, and delete books through the web interface.
- Upload a book file and optional cover.
- Search the management list.
- Manage categories through the Django admin.
- Book records include fields reserved for future metadata imports.

### Validation and error handling

- Only `.pdf`, `.epub`, and `.txt` book files are accepted.
- Book uploads are limited to 50 MB per file, covers to 5 MB.
- PDF headers, EPUB archive structure/mimetype, and UTF-8 text encoding are checked,
  not just the filename extension.
- Covers must be valid JPG, PNG, or WebP images.
- ISBN-10 and ISBN-13 checksums are verified; duplicate ISBNs are rejected.
- Titles, authors, categories, and file uploads are required.
- Publication dates cannot be in the future; page counts must be positive.
- Shelf names are unique per user and cannot be blank.
- Reordering requires the exact set of items on that shelf.
- Missing files, missing pages, and permission errors show friendly pages or messages
  instead of stack traces.
- Guests are redirected to login when they try to use member features.
- Members who try to open staff pages receive a 403 page.

---

## Technology

| Layer | Choice |
| --- | --- |
| Backend | Django 6.1.3 |
| Database | SQLite |
| Images | Pillow 13.0.0 |
| Templates | Django templates + Bootstrap 5.3.9 |
| Icons | Bootstrap Icons 1.13.2 |
| PDF reader | PDF.js 6.5.438 |
| EPUB reader | ePub.js 0.3.93 + JSZip 3.10.2 |
| Drag and drop | SortableJS 1.15.7 |
| Python | 3.14 (only version installed in the development environment) |

All front-end libraries are vendored under `static/vendor/`. The app does not depend on
a CDN at runtime.

---

## Quick start

From the `project/` directory:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py seed_demo
.venv/bin/python manage.py runserver
```

Open <http://127.0.0.1:8000/>.

`seed_demo` is safe to run more than once. It creates categories, five public-domain
books, generated covers, two demo accounts, two shelves, and one saved reading position.
Existing accounts keep their current passwords.

### Demo accounts

| Role | Username | Password |
| --- | --- | --- |
| Staff / superuser | `admin` | `admin12345` |
| Member | `reader` | `reader12345` |

These credentials are for local development only.

### Useful commands

```bash
.venv/bin/python manage.py check
.venv/bin/python manage.py test
.venv/bin/python manage.py makemigrations --check --dry-run
.venv/bin/python manage.py collectstatic
```

---

## URLs

| URL | Purpose |
| --- | --- |
| `/` | Home page |
| `/books/` | Catalog, search, filters, pagination |
| `/books/<slug>/` | Book detail |
| `/books/<slug>/read/` | In-browser reader |
| `/books/<slug>/file/` | Inline file for the reader |
| `/books/<slug>/download/` | Download and increment the counter |
| `/accounts/register/` | Create an account |
| `/accounts/login/` | Log in |
| `/accounts/logout/` | Log out (POST) |
| `/library/` | Member dashboard |
| `/library/shelves/new/` | Create a shelf |
| `/library/shelves/<id>/` | Shelf detail and drag/drop ordering |
| `/library/shelves/<id>/edit/` | Rename a shelf |
| `/library/shelves/<id>/delete/` | Delete a shelf |
| `/api/books/<id>/progress/` | JSON progress save endpoint |
| `/manage/` | Staff dashboard |
| `/manage/books/` | Staff book list |
| `/manage/books/new/` | Add a book |
| `/manage/books/<slug>/edit/` | Edit a book |
| `/manage/books/<slug>/delete/` | Delete a book |
| `/admin/` | Django admin, including categories |

---

## Project structure

```
project/
├── config/                 # Settings, root URLs, WSGI/ASGI
├── catalog/                # Books, categories, reader, staff CRUD
│   ├── management/commands/seed_demo.py
│   ├── migrations/
│   ├── admin.py
│   ├── decorators.py       # staff_required
│   ├── forms.py            # BookForm and validation
│   ├── models.py           # Category, Book
│   ├── signals.py          # File cleanup on delete
│   ├── tests.py
│   ├── urls.py
│   ├── validators.py       # ISBN, file, EPUB, cover checks
│   └── views.py
├── library/                # Member accounts, shelves, progress
│   ├── migrations/
│   ├── forms.py
│   ├── models.py           # Shelf, ShelfItem, ReadingProgress
│   ├── services.py         # Default-shelf helper
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── templates/              # Base layout, auth, errors, partials
├── static/
│   ├── css/app.css
│   ├── css/reader.css
│   ├── js/theme.js
│   ├── js/reader.js
│   ├── js/shelves.js
│   └── vendor/             # Bootstrap, icons, PDF.js, ePub.js, ...
├── catalog/templates/      # Catalog, reader, staff pages
├── library/templates/      # Dashboard, shelf pages
├── seed_data/              # Public-domain sample books
├── media/                  # Uploaded files (gitignored)
├── db.sqlite3              # Local database (gitignored)
├── requirements.txt
└── manage.py
```

`media/`, `db.sqlite3`, and `.venv/` are intentionally ignored by git. Recreate them
with `migrate` and `seed_demo`.

---

## Data model

There are five related tables, satisfying the "at least two related tables" requirement.

### `catalog.Category`

- `name`, `slug`, `description`, `created_at`.
- One category has many books.
- Deletion is protected while books still reference the category.
- Managed in the Django admin.

### `catalog.Book`

- Bibliographic fields: title, subtitle, author (free text), category, ISBN, publisher,
  publication date, language, page count, description.
- File fields: uploaded file, original filename, detected type, size, SHA-256, download
  counter, optional cover image or remote cover URL.
- `uploaded_by` links to the staff account.
- Reserved metadata fields: `metadata_source`, `metadata_updated_at`, `external_ids`,
  and `raw_metadata` (JSON).
- Slugs are generated automatically and kept unique.
- Deleting a book removes its stored file and cover after the transaction commits.

### `library.Shelf`

- Belongs to one user; one user has many shelves.
- Unique name per user; one shelf per user is marked as the default.
- Deleting a shelf deletes its items but not the books themselves.

### `library.ShelfItem`

- Join table between a shelf and a book.
- Unique per shelf/book pair.
- `position` stores the user's manual order.

### `library.ReadingProgress`

- One row per user/book pair.
- `locator` is JSON:
  - PDF: `{"kind": "pdf", "page": 12}`
  - EPUB: `{"kind": "epub", "cfi": "epubcfi(...)"}`
  - TXT: `{"kind": "txt", "ratio": 0.42}`
- `percent` is a float from 0 to 100.
- `updated_at` drives "Continue reading" ordering.

Reading progress is intentionally separate from shelves so a book can be on several
shelves while keeping a single position per account.

---

## Validation summary

Server-side validation is the source of truth. Browser-side `accept` attributes are only
a convenience.

| Input | Rule |
| --- | --- |
| Book file extension | `.pdf`, `.epub`, `.txt` |
| Book file size | ≤ 50 MB |
| PDF content | Must contain a `%PDF-` header |
| EPUB content | Valid ZIP with `mimetype` and `META-INF/container.xml`; mimetype must be `application/epub+zip` |
| TXT content | UTF-8, no NUL bytes |
| Cover | JPG, PNG, or WebP; valid image; ≤ 5 MB |
| ISBN | Optional; ISBN-10/13 checksum; unique |
| Published date | Cannot be in the future |
| Page count | At least 1 if provided |
| Shelf name | Non-blank, unique per user |
| Progress percent | Number from 0 to 100 |
| Progress locator | JSON object, at most 12 keys and 4 KB |
| Reorder payload | Exact set of item IDs on the shelf |

Files are stored under `media/books/` and `media/covers/` with UUID names, so duplicate
filenames cannot overwrite each other.

---

## Reader behaviour

- `static/js/reader.js` is an ES module.
- PDF.js is loaded dynamically as a module, with its worker served by Django as
  `text/javascript`. Standard PDF fonts are served locally.
- PDF pages are rendered to a canvas at device pixel ratio, with zoom from 50% to 250%.
- EPUB rendering uses ePub.js with generated locations for percentage calculation.
  Reader styles follow the site light/dark theme.
- TXT files are fetched as text and rendered with `white-space: pre-wrap`.
- Progress is saved with a debounced `POST` to the progress API. The request includes
  the CSRF token and uses `keepalive` for page exits.
- Guests can read everything but see a banner explaining that progress is not saved.
- Saved positions are restored from the book's `ReadingProgress` record when a member
  reopens the reader.

The reader degrades to an error panel with a download link if a file cannot be opened.

---

## Future metadata integration

The schema is ready for an importer without a migration:

1. Add a service that queries Google Books, Open Library, or another provider by ISBN.
2. Store the provider name in `metadata_source`, the response in `raw_metadata`, and
   provider IDs in `external_ids`.
3. Update `metadata_updated_at` and copy selected fields onto the book.
4. Optionally add a management command or staff action that calls the service.

`cover_url` already allows a remote cover when no local image is uploaded. The catalog
templates use the local cover first and fall back to `cover_url`.

No metadata provider is called in this version; the project works fully offline.

---

## Tests

The test suite covers models, validation, permissions, CRUD, files, search, shelves,
reordering, progress, and reader configuration.

```bash
.venv/bin/python manage.py test
```

Current result: **69 tests, all passing**.

Test media is written to a temporary directory, so the local `media/` folder is not
modified by the suite.

---

## Requirement mapping

| Requirement | Where it is satisfied |
| --- | --- |
| Python + Django + SQLite | `config/settings.py`, `db.sqlite3` |
| Separate virtual environment | `.venv/` in the project root |
| Library management topic | Catalog, shelves, reading progress, staff management |
| Upload books | Staff create/edit forms with `BookForm` |
| Download books | `/books/<slug>/download/` and download counters |
| PDF / EPUB / TXT only | `catalog/validators.py` |
| File and cover size limits | Settings plus validators |
| In-browser reader | PDF.js, ePub.js, and plain-text renderer |
| Guest browsing and reading | Public catalog, detail, reader, download views |
| Saved reading progress | `ReadingProgress` plus the JSON API |
| Custom shelves, per account | `Shelf` and `ShelfItem` with ownership checks |
| Drag/drop shelf ordering | SortableJS plus transactional reorder endpoint |
| Free-text author on books | `Book.author`; no Author account or table |
| Categories as a related table | `Category` foreign key, managed in the admin |
| Search, filters, pagination | `catalog.views.book_list` |
| At least two related tables | Five tables with foreign keys and unique constraints |
| CRUD through the web UI | Staff book CRUD, member shelf CRUD, account registration |
| Server-side validation | Forms, model validators, and API checks |
| Understandable errors | Form messages, 403/404/500 pages, reader error panel |
| Data persistence | SQLite plus files in `media/`; survives restart |
| Bootstrap 5 + icons | Vendored under `static/vendor/` |
| Prepared for future metadata | Reserved JSON/URL fields and importer notes |

---

## Seed content

The sample files in `seed_data/` are public-domain works:

- *Alice's Adventures in Wonderland* — Lewis Carroll, EPUB from Standard Ebooks.
- *Pride and Prejudice* — Jane Austen, EPUB from Standard Ebooks.
- *The Art of War* — Sun Tzu, Lionel Giles translation, plain text from Project Gutenberg.
- *The Raven* — Edgar Allan Poe, plain text from Project Gutenberg.
- *The Declaration of Independence* — PDF generated from the public-domain text.

Covers are generated locally by the seed command and are not copied from any store.

---

## Notes and limitations

- This is a local course project. `DEBUG` defaults to on and `SECRET_KEY` has a
  development fallback. Set `DJANGO_DEBUG=0`, `DJANGO_SECRET_KEY`, and
  `DJANGO_ALLOWED_HOSTS` before any real deployment.
- SQLite is used as required. No production web server, HTTPS, or object storage is
  configured.
- Files are stored on the local filesystem under `media/`.
- There is no email verification, password reset, borrowing, purchasing, or review
  system, by design.
- Uploaded EPUBs are rendered in a sandboxed iframe with scripted content disabled.
- The admin remains available for categories and low-level maintenance; day-to-day
  book management is done in the staff interface at `/manage/`.
