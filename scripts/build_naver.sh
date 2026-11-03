#!/usr/bin/env bash
set -euo pipefail
python3 -m pip install --quiet -r requirements.txt
python3 scripts/build.py
python3 scripts/verify_naver_images.py
