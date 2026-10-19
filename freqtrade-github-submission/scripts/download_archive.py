"""Download official Binance monthly spot OHLCV archives, verify SHA256, save Freqtrade JSON.

No API credentials required. Timestamps are normalized to milliseconds (Binance
spot archives changed to microseconds in 2025). Missing/duplicate hours fail.
"""
import concurrent.futures
import csv
import hashlib
import io
import json
from pathlib import Path
import time
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "user_data" / "data" / "binance"
CACHE = ROOT / "evidence" / "archives"


def fetch(url):
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=60) as response:
                return response.read()
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2)


def month(job):
    symbol, year, number = job
    name = f"{symbol}-1h-{year}-{number:02d}.zip"
    url = f"https://data.binance.vision/data/spot/monthly/klines/{symbol}/1h/{name}"
    path = CACHE / name
    payload = path.read_bytes() if path.exists() else fetch(url)
    expected = fetch(url + ".CHECKSUM").decode().split()[0]
    actual = hashlib.sha256(payload).hexdigest()
    if actual != expected:
        raise ValueError(f"Checksum mismatch: {name}")
    path.write_bytes(payload)
    rows = []
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        for row in csv.reader(io.StringIO(archive.read(archive.namelist()[0]).decode())):
            stamp = int(row[0])
            if stamp > 10**14:
                stamp //= 1000
            rows.append([stamp, *map(float, row[1:6])])
    print(f"verified {name}: {len(rows)} candles", flush=True)
    return symbol, rows, {"url": url, "sha256": actual, "candles": len(rows)}


def main():
    DATA.mkdir(parents=True, exist_ok=True)
    CACHE.mkdir(parents=True, exist_ok=True)
    jobs = [(symbol, year, number) for symbol in ("BTCUSDT", "ETHUSDT")
            for year, number in [(2023, 12)] + [(y, m) for y in (2024, 2025) for m in range(1, 13)]]
    combined = {"BTCUSDT": [], "ETHUSDT": []}
    manifest = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        for symbol, rows, evidence in pool.map(month, jobs):
            combined[symbol].extend(rows)
            manifest.append(evidence)
    for symbol, rows in combined.items():
        rows.sort(key=lambda row: row[0])
        for previous, current in zip(rows, rows[1:]):
            if current[0] - previous[0] != 3_600_000:
                raise ValueError(f"Missing or duplicate hourly data: {symbol}: {previous[0]}")
        for row in rows:
            _, op, hi, lo, cl, vol = row
            if not (0 < lo <= min(op, cl) <= max(op, cl) <= hi and vol >= 0):
                raise ValueError(f"Invalid OHLCV: {row}")
        (DATA / f"{symbol[:-4]}_USDT-1h.json").write_text(json.dumps(rows), encoding="utf-8")
    (ROOT / "evidence" / "data_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
