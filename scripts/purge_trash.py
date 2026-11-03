#!/usr/bin/env python3
"""Immediately remove all old trash posts, preserving only deleted slugs.

Published and draft posts are never modified or deleted. This is an idempotent
migration for the previous 72-hour trash system.
"""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
POSTS=ROOT/"content"/"posts"
DELETED=ROOT/"content"/"deleted-slugs.json"
if DELETED.exists():
    previous=json.loads(DELETED.read_text(encoding="utf-8"))
    if not isinstance(previous,list):
        raise RuntimeError("Deleted-slug registry must be a JSON array")
    slugs=set(x for x in previous if isinstance(x,str))
else:
    slugs=set()
removed=[]
unreadable=[]
for path in sorted(POSTS.glob("*.json")):
    try:
        post=json.loads(path.read_text(encoding="utf-8"))
    except (ValueError,OSError) as exc:
        unreadable.append((path.name,str(exc)))
        continue
    if post.get("status")!="trash":
        continue
    slugs.add(path.stem)
    path.unlink()
    removed.append(path.name)
DELETED.parent.mkdir(parents=True,exist_ok=True)
DELETED.write_text(json.dumps(sorted(slugs),ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("Permanently deleted",len(removed),"trash articles; retained",len(slugs),"blocked slugs")
for item in removed: print("DELETED",item)
for name,error in unreadable:print("UNREADABLE (NOT deleted)",name,error)
