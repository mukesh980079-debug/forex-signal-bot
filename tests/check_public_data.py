import requests

BASE = "https://fapi.binance.com"
checks = [
    ("/fapi/v1/klines", {"symbol":"BTCUSDT","interval":"5m","limit":3}),
    ("/fapi/v1/openInterest", {"symbol":"BTCUSDT"}),
    ("/fapi/v1/premiumIndex", {"symbol":"BTCUSDT"}),
]
for path, params in checks:
    response = requests.get(BASE + path, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()
    assert data, f"Empty response from {path}"
    if path.endswith("klines"):
        assert len(data) >= 2 and len(data[0]) >= 6, "Unexpected candle response"
        print(f"PASS {path}: received {len(data)} candles")
    elif path.endswith("openInterest"):
        assert "openInterest" in data, "Missing openInterest field"
        print(f"PASS {path}: open interest field received")
    else:
        assert "lastFundingRate" in data, "Missing funding field"
        print(f"PASS {path}: funding field received")
print("All public Binance Futures data checks passed.")
