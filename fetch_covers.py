#!/usr/bin/env python3
"""
Fetches real book cover art from Open Library (a free, purpose-built
API for exactly this — no scraping, no copyright grey area) for the
30 Day Changes reading queue, and saves them into a `covers/` folder
next to index.html.

Run this from anywhere on your Mac (needs normal internet access,
which is why it's a script for your own Terminal rather than
something Claude runs through the device bridge):

    python3 fetch_covers.py

It's safe to re-run — it'll just overwrite the same files.
"""
import json
import os
import time
import urllib.parse
import urllib.request

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

misses = []

for b in BOOKS:
    q = urllib.parse.urlencode({
        "title": b["title"],
        "author": b["author"],
        "limit": 1,
        "fields": "cover_i,title",
    })
    url = f"https://openlibrary.org/search.json?{q}"
    dest = os.path.join(OUT_DIR, f"{b['slug']}.jpg")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "30DayChanges-CoverFetcher/1.0 (personal project)"})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.load(r)
        docs = data.get("docs", [])
        cover_i = docs[0].get("cover_i") if docs else None
        if cover_i:
            img_url = f"https://covers.openlibrary.org/b/id/{cover_i}-L.jpg"
            img_req = urllib.request.Request(img_url, headers={"User-Agent": "30DayChanges-CoverFetcher/1.0 (personal project)"})
            with urllib.request.urlopen(img_req, timeout=15) as r, open(dest, "wb") as f:
                f.write(r.read())
            print(f"OK    #{b['n']:>2}  {b['title']}")
        else:
            print(f"MISS  #{b['n']:>2}  {b['title']}  (no cover found on Open Library)")
            misses.append(b["title"])
    except Exception as e:
        print(f"ERR   #{b['n']:>2}  {b['title']}  ({e})")
        misses.append(b["title"])
    time.sleep(0.4)

print("\nDone. Covers saved to:", OUT_DIR)
if misses:
    print("\nNo automatic match found for:")
    for t in misses:
        print(" -", t)
    print("\nThese can be added manually later, or we'll fall back to a placeholder for them.")
