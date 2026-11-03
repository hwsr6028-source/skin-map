#!/usr/bin/env python3
"""Mark CMS trash dates and purge only items older than 72 hours.

Runs via GitHub Actions. Live and draft posts are never deleted.
Restore by changing status from trash to published/draft before expiration.
"""
import datetime, json, pathlib, subprocess
ROOT = pathlib.Path(__file__).resolve().parents[1]
POSTS = ROOT / "content" / "posts"
NOW = datetime.datetime.now(datetime.timezone.utc)
changed = []
deleted = []
for path in sorted(POSTS.glob("*.json")):
    try:
        post = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        print("Skip unreadable:", path.name, exc)
        continue
    if post.get("status") != "trash":
        if post.get("deleted_at"):
            post.pop("deleted_at", None)
            path.write_text(json.dumps(post, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            changed.append(path.name)
        continue
    deleted_at = post.get("deleted_at")
    if not deleted_at:
        post["deleted_at"] = NOW.isoformat(timespec="seconds").replace("+00:00", "Z")
        path.write_text(json.dumps(post, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        changed.append(path.name)
        continue
    try:
        stamp = datetime.datetime.fromisoformat(str(deleted_at).replace("Z", "+00:00"))
        if stamp.tzinfo is None:
            print("Skip ambiguous deletion date:", path.name)
            continue
    except (ValueError, TypeError):
        print("Skip invalid deletion date:", path.name)
        continue
    if NOW - stamp >= datetime.timedelta(hours=72):
        path.unlink()
        deleted.append(path.name)
print("Timestamped:", changed, "Purged:", deleted)
