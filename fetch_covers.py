#!/usr/bin/env python3
"""
Fetches higher-resolution book cover art for the 30 Day Changes reading
queue. Tries Google Books first (usually sharper and larger than Open
Library's images), falls back to Open Library, and keeps whichever
result actually has more pixels. Both are official public APIs made
for exactly this kind of use -- no scraping, no copyright grey area.

Run this from anywhere on your Mac (needs normal internet access,
which is why it's a script for your own Terminal rather than
something Claude runs through the device bridge):

    python3 fetch_covers.py

Needs Pillow to compare image dimensions -- install it first if you
don't have it:

    pip3 install pillow

Safe to re-run -- it overwrites covers/ with whichever source wins
each time. Prints a short reason next to any book where Google Books
didn't win, so it's obvious whether it lost fairly (Open Library just
had the bigger image) or errored out (network/API issue worth flagging).
"""
import io
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request

try:
    from PIL import Image
    HAVE_PIL = True
except ImportError:
    HAVE_PIL = False
    print("NOTE: Pillow isn't installed (pip3 install pillow) -- can't compare")
    print("resolutions, so this will just keep whichever source responds last.\n")

BOOKS = [
    {"n": 1, "title": "The Subtle Art of Not Giving a F*ck", "author": "Mark Manson", "slug": "01-subtle-art"},
    {"n": 2, "title": "Can't Hurt Me", "author": "David Goggins", "slug": "02-cant-hurt-me"},
    {"n": 3, "title": "The Miracle Morning", "author": "Hal Elrod", "slug": "03-miracle-morning"},
    {"n": 4, "title": "Atomic Habits", "author": "James Clear", "slug": "04-atomic-habits"},
    {"n": 5, "title": "Rich Dad Poor Dad", "author": "Robert Kiyosaki", "slug": "05-rich-dad-poor-dad"},
    {"n": 6, "title": "Extreme Ownership", "author": "Jocko Willink", "slug": "06-extreme-ownership"},
    {"n": 7, "title": "The 4-Hour Workweek", "author": "Tim Ferriss", "slug": "07-4-hour-workweek"},
    {"n": 8, "title": "Ikigai", "author": "Hector Garcia", "slug": "08-ikigai"},
    {"n": 9, "title": "Deep Work", "author": "Cal Newport", "slug": "09-deep-work"},
    {"n": 10, "title": "The 5AM Club", "author": "Robin Sharma", "slug": "10-5am-club"},
    {"n": 11, "title": "The Obstacle Is the Way", "author": "Ryan Holiday", "slug": "11-obstacle-is-the-way"},
    {"n": 12, "title": "The Compound Effect", "author": "Darren Hardy", "slug": "12-compound-effect"},
    {"n": 13, "title": "The Power of Now", "author": "Eckhart Tolle", "slug": "13-power-of-now"},
    {"n": 14, "title": "The 7 Habits of Highly Effective People", "author": "Stephen Covey", "slug": "14-7-habits"},
    {"n": 15, "title": "Think and Grow Rich", "author": "Napoleon Hill", "slug": "15-think-and-grow-rich"},
    {"n": 16, "title": "Never Split the Difference", "author": "Chris Voss", "slug": "16-never-split-the-difference"},
    {"n": 17, "title": "Peak", "author": "Anders Ericsson", "slug": "17-peak"},
    {"n": 18, "title": "The Millionaire Fastlane", "author": "MJ DeMarco", "slug": "18-millionaire-fastlane"},
    {"n": 19, "title": "Outliers", "author": "Malcolm Gladwell", "slug": "19-outliers"},
    {"n": 20, "title": "The Psychology of Money", "author": "Morgan Housel", "slug": "20-psychology-of-money"},
]

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "covers")
os.makedirs(OUT_DIR, exist_ok=True)

UA = {"User-Agent": "30DayChanges-CoverFetcher/2.1 (personal project)"}


def fetch(url, timeout=15):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def pixel_size(data):
    if not HAVE_PIL:
        return None
    try:
        return Image.open(io.BytesIO(data)).size
    except Exception:
        return None


def area(size):
    return size[0] * size[1] if size else 0


def google_books_search(query):
    """One search attempt against Google Books. Returns (items, reason)."""
    q = urllib.parse.urlencode({"q": query, "maxResults": 5})
    url = f"https://www.googleapis.com/books/v1/volumes?{q}"
    try:
        raw = fetch(url)
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}"
    except urllib.error.URLError as e:
        return None, f"network error ({e.reason})"
    except Exception as e:
        return None, f"error ({e})"
    try:
        data = json.loads(raw)
    except Exception:
        return None, "bad JSON response"
    return data.get("items", []) or [], None


def google_books_cover(title, author):
    """Returns (img_bytes, size, debug_reason). debug_reason is None on success."""
    # First try a strict field-scoped search, then fall back to a plain one --
    # some titles (accented authors, punctuation like "F*ck") don't match well
    # with intitle:/inauthor: operators.
    clean_title = re.sub(r"[^\w\s]", " ", title)
    attempts = [
        f"intitle:{title} inauthor:{author}",
        f"{clean_title} {author}",
    ]

    last_reason = "no results"
    for query in attempts:
        items, reason = google_books_search(query)
        if reason:
            last_reason = reason
            continue
        if not items:
            last_reason = "no results"
            continue

        for item in items:
            links = item.get("volumeInfo", {}).get("imageLinks", {})
            base = (links.get("extraLarge") or links.get("large") or links.get("medium")
                    or links.get("small") or links.get("thumbnail") or links.get("smallThumbnail"))
            if not base:
                continue
            # Search results default to a small thumbnail, but bumping zoom
            # and dropping the curl-page effect unlocks a much bigger image
            big_url = re.sub(r"zoom=\d", "zoom=3", base)
            big_url = big_url.replace("&edge=curl", "").replace("http://", "https://")
            try:
                img = fetch(big_url)
            except Exception as e:
                last_reason = f"image download failed ({e})"
                continue
            size = pixel_size(img)
            if HAVE_PIL and area(size) <= 40 * 40:
                last_reason = "image too small/corrupt"
                continue
            return img, size, None

        last_reason = "matched but no cover image listed"

    return None, None, last_reason


def open_library_cover(title, author):
    q = urllib.parse.urlencode({"title": title, "author": author, "limit": 1, "fields": "cover_i,title"})
    url = f"https://openlibrary.org/search.json?{q}"
    try:
        data = json.loads(fetch(url))
    except Exception:
        return None
    docs = data.get("docs", [])
    cover_i = docs[0].get("cover_i") if docs else None
    if not cover_i:
        return None
    img_url = f"https://covers.openlibrary.org/b/id/{cover_i}-L.jpg"
    try:
        img = fetch(img_url)
        return img, pixel_size(img)
    except Exception:
        return None


misses = []

for b in BOOKS:
    dest = os.path.join(OUT_DIR, f"{b['slug']}.jpg")
    candidates = []

    gb_img, gb_size, gb_reason = google_books_cover(b["title"], b["author"])
    if gb_img:
        candidates.append(("Google Books", gb_img, gb_size))
    time.sleep(0.3)

    o = open_library_cover(b["title"], b["author"])
    if o:
        candidates.append(("Open Library", o[0], o[1]))
    time.sleep(0.3)

    if not candidates:
        print(f"MISS  #{b['n']:>2}  {b['title']}  (no cover found on either source; Google: {gb_reason})")
        misses.append(b["title"])
        continue

    if HAVE_PIL:
        candidates.sort(key=lambda c: area(c[2]), reverse=True)
    source, img, size = candidates[0]

    with open(dest, "wb") as f:
        f.write(img)

    dims = f"{size[0]}x{size[1]}" if size else "?"
    note = "" if source == "Google Books" or not gb_reason else f"  [Google: {gb_reason}]"
    print(f"OK    #{b['n']:>2}  {b['title']:<45} {dims:>10}  ({source}){note}")

print("\nDone. Covers saved to:", OUT_DIR)
if misses:
    print("\nNo automatic match found for:")
    for t in misses:
        print(" -", t)
    print("\nThese can be added manually later, or we'll fall back to a placeholder for them.")
