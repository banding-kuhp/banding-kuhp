#!/bin/bash
set -e
cd "$(dirname "$0")"
python3 teks.py
python3 urai_lama.py
python3 koreksi_lama.py | head -1
python3 urai_baru.py
python3 koreksi_baru.py
python3 urai_2026.py > /dev/null
python3 terapkan_2026.py
python3 peta.py
