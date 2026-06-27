#!/usr/bin/env sh
set -eu
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
