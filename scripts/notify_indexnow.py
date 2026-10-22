#!/usr/bin/env python3
"""Notify Naver IndexNow about newly published/updated posts once Pages serves them.

Invoked by the GitHub Actions workflow only for content/posts changes.
Submission means notifying the engine, never guaranteed crawl or index.
"""
import json
import os
import pathlib
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
HOST = "skin-map.pages.dev"
BASE = "https://" + HOST
KEY = "d507d99d18a0029f9e6a7f92d608f0d7"
VERIFY = BASE + "/" + KEY + ".txt"

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "InfoWorld-IndexNow/1.0"})
    with urllib.request.urlopen(req, timeout=20) as res:
        return res.status, res.read()

def changed_paths():
    """Detect newly added/updated post JSON in the triggering commit."""
    before = os.getenv("BEFORE_SHA", "").strip()
    after = os.getenv("AFTER_SHA", "").strip() or "HEAD"
    commands = [
        ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", "--diff-filter=ACMRT", after, "--", "content/posts/"],
        ["git", "show", "--format=", "--name-only", "--diff-filter=ACMRT", after, "--", "content/posts/"],
    ]
    if before and before != "0" * 40 and before != after:
        commands.append(["git", "diff", "--name-only", "--diff-filter=ACMRT", before, after, "--", "content/posts/"])
    for command in commands:
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        if result.returncode:
            print("Git history check failed:", result.stderr.strip()[:240])
            continue
        paths = sorted({line.strip() for line in result.stdout.splitlines()
                        if line.strip().startswith("content/posts/") and line.strip().endswith(".json")})
        if paths:
            print(f"IndexNow candidate files: {len(paths)}")
            return paths
    print("IndexNow candidate files: 0")
    return []

def main():
    files = changed_paths()
    if not files:
        print("No changed article JSON files; skipping IndexNow.")
        return 0
    urls = []
    for name in files:
        file = ROOT / name
        if not file.is_file():
            continue
        try:
            post = json.loads(file.read_text(encoding="utf-8"))
        except (ValueError, UnicodeError) as exc:
            print("Skipping invalid JSON", name, exc)
            continue
        if post.get("status") != "published" or post.get("seo_approved") is not True:
            continue
        slug = str(post.get("slug") or "").strip()
        if not slug or "/" in slug or ".." in slug:
            continue
        url = BASE + "/blog/" + urllib.parse.quote(slug, safe="-") + "/"
        urls.append(url)
    if not urls:
        print("No new public SEO-approved URLs.")
        return 0
    # The action may run before Cloudflare Pages finishes building. Wait until
    # the ownership key and each article are publicly reachable.
    for attempt in range(18):
        try:
            _, key_body = get(VERIFY)
            if key_body.decode("utf-8").strip() != KEY:
                raise RuntimeError("IndexNow verification key not deployed")
            failed = []
            for url in urls:
                try:
                    status, body = get(url)
                    if status != 200 or b"<html" not in body[:500].lower():
                        failed.append(url)
                except (urllib.error.URLError, TimeoutError) as err:
                    failed.append(url)
            if not failed:
                break
            print(f"Pages not ready: {len(failed)} URL(s), attempt {attempt+1}/18")
        except Exception as err:
            print(f"Waiting for key/deployment: {err}")
        time.sleep(20)
    else:
        print("Cloudflare Pages not ready after retries, IndexNow skipped to avoid premature notification.")
        return 1
    # Batched Naver notification; IndexNow response 200/202 means accepted,
    # not indexed in search results.
    payload = json.dumps({"host": HOST, "key": KEY, "urlList": urls}).encode("utf-8")
    req = urllib.request.Request(
        "https://searchadvisor.naver.com/indexnow",
        data=payload,
        headers={"Content-Type": "application/json; charset=utf-8", "User-Agent": "InfoWorld-IndexNow/1.0"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as response:
            print(f"Naver IndexNow response HTTP {response.status}; submitted {len(urls)} URL(s)")
            return 0 if response.status in (200, 202) else 1
    except urllib.error.HTTPError as err:
        print(f"Naver IndexNow HTTP {err.code}: {err.read(500).decode('utf-8', 'replace')}")
    except urllib.error.URLError as err:
        print("Naver IndexNow request failed:", err)
    return 1

if __name__ == "__main__":
    sys.exit(main())
