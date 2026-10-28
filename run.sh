#!/usr/bin/env bash
# Chay nhanh MiniStore SQLi CTF (ban rut gon) khong can Docker.
set -e
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
  echo "[*] Tao virtualenv..."
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q -r requirements.txt

export DB_PATH="$(pwd)/store.db"

echo "[*] Khoi tao CSDL..."
python3 init_db.py

echo "[*] Mo ung dung tai http://127.0.0.1:8080"
python3 app.py
