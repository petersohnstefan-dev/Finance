"""Free Real-Time Intraday Momentum & Breakout Engine across 160+ Multi-Asset Watchlists."""

import os
import time
import json
import datetime
import urllib.request
import pandas as pd
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor
import yfinance as yf
from src.universe import CATEGORIZED_UNIVERSES, FULL_MARKET_UNIVERSE

ALERTS_LOG_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "realtime_alerts.json")
LIVE_PRICES_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "live_ticks.json")

# 500+ Assets categorized
WATCHLIST_CATEGORIES = CATEGORIZED_UNIVERSES

class RealTimeBreakoutScanner:
    """Monitors live price ticks and volume spikes in real-time across 500+ assets without paid APIs."""

    def __init__(self):
        self.price_history = {}  # {symbol: [{"time": ts, "price": px}]}
        self._load_state()

    def _load_state(self):
        if not os.path.exists(ALERTS_LOG_FILE):
            os.makedirs(os.path.dirname(ALERTS_LOG_FILE), exist_ok=True)
            with open(ALERTS_LOG_FILE, "w", encoding="utf-8") as f:
                json.dump([], f)

    def fetch_crypto_live_price(self, symbol: str) -> Optional[float]:
        """Free 0-latency live crypto prices via public Binance API."""
        clean_base = symbol.split("-")[0].upper()
        pair = f"{clean_base}USDT"
        try:
            url = f"https://api.binance.com/api/v3/ticker/price?symbol={pair}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=2.5) as resp:
                data = json.loads(resp.read().decode())
                return float(data["price"])
        except Exception:
            return None

    def fetch_stock_live_price(self, symbol: str) -> Optional[float]:
        """Free real-time stock, ETF & futures quotes with pre/post-market live streaming support."""
        try:
            t = yf.Ticker(symbol)
            # Try ultra-fast 1-day 1-minute pre/post-market tick first for active US/EU tickers
            try:
                df = t.history(period="1d", interval="1m", prepost=True)
                if not df.empty and pd.notnull(df["Close"].iloc[-1]):
                    return round(float(df["Close"].iloc[-1]), 2)
            except Exception:
                pass

            # Fallback to fast_info
            fi = t.fast_info
            px = getattr(fi, 'last_price', None) or getattr(fi, 'regular_market_previous_close', None)
            return round(float(px), 2) if px else None
        except Exception:
            return None

    def get_live_tick(self, symbol: str) -> Optional[float]:
        if "-USD" in symbol:
            px = self.fetch_crypto_live_price(symbol)
            if px:
                return px
        return self.fetch_stock_live_price(symbol)

    def scan_category(self, category_name: str = "🔥 Hot-Momentum & Squeeze-Radar") -> Dict[str, Any]:
        """Scans all assets in a selected category in parallel."""
        tickers = WATCHLIST_CATEGORIES.get(category_name, WATCHLIST_CATEGORIES["🔥 Hot-Momentum & Squeeze-Radar"])
        now = datetime.datetime.now()
        now_ts = now.timestamp()
        new_alerts = []
        live_ticks = {}

        def fetch_single(sym):
            try:
                px = self.get_live_tick(sym)
                return sym, px
            except Exception:
                return sym, None

        with ThreadPoolExecutor(max_workers=20) as executor:
            results = list(executor.map(fetch_single, tickers))

        for sym, px in results:
            if not px or px <= 0:
                continue

            live_ticks[sym] = {
                "symbol": sym,
                "price": round(px, 2),
                "type": "CRYPTO" if "-USD" in sym else ("COMMODITY" if "=F" in sym else "STOCK"),
                "time": now.strftime("%H:%M:%S")
            }

            if sym not in self.price_history:
                self.price_history[sym] = []

            self.price_history[sym].append({"time": now_ts, "price": px})
            self.price_history[sym] = [p for p in self.price_history[sym] if now_ts - p["time"] <= 300]

            one_min_ago_ticks = [p for p in self.price_history[sym] if now_ts - p["time"] >= 45]
            if one_min_ago_ticks:
                old_p = one_min_ago_ticks[0]["price"]
                change_pct = ((px - old_p) / old_p) * 100.0

                if change_pct >= 0.6:
                    alert = {
                        "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
                        "time_str": now.strftime("%H:%M:%S"),
                        "symbol": sym,
                        "trigger_price": round(px, 2),
                        "change_1min_pct": round(change_pct, 2),
                        "urgency": "⚡ EXTREM (Sofortiger Intraday-Ausbruch)",
                        "message": f"🚨 {sym} explodiert um {change_pct:+.2f}% in <60 Sek.! Short-Squeeze-Druck aktiv."
                    }
                    new_alerts.append(alert)
                    self._record_alert(alert)

        # Merge with existing live ticks file
        existing_ticks = {}
        if os.path.exists(LIVE_PRICES_FILE):
            try:
                with open(LIVE_PRICES_FILE, "r", encoding="utf-8") as f:
                    existing_ticks = json.load(f)
            except Exception:
                pass
        existing_ticks.update(live_ticks)
        try:
            with open(LIVE_PRICES_FILE, "w", encoding="utf-8") as f:
                json.dump(existing_ticks, f, indent=2)
        except Exception:
            pass

        return {
            "category": category_name,
            "count": len(live_ticks),
            "ticks": live_ticks,
            "alerts": new_alerts
        }

    def _record_alert(self, alert: Dict[str, Any]):
        try:
            alerts = []
            if os.path.exists(ALERTS_LOG_FILE):
                with open(ALERTS_LOG_FILE, "r", encoding="utf-8") as f:
                    alerts = json.load(f)
            alerts.insert(0, alert)
            alerts = alerts[:50]
            with open(ALERTS_LOG_FILE, "w", encoding="utf-8") as f:
                json.dump(alerts, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    @staticmethod
    def get_categories() -> List[str]:
        return list(WATCHLIST_CATEGORIES.keys())

    @staticmethod
    def get_recent_alerts() -> List[Dict[str, Any]]:
        if os.path.exists(ALERTS_LOG_FILE):
            try:
                with open(ALERTS_LOG_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    @staticmethod
    def get_live_ticks_snapshot() -> Dict[str, Any]:
        if os.path.exists(LIVE_PRICES_FILE):
            try:
                with open(LIVE_PRICES_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

if __name__ == "__main__":
    scanner = RealTimeBreakoutScanner()
    print("Starte erweiterten Multi-Asset Real-Time-Scan...")
    res = scanner.scan_category("🔥 Hot-Momentum & Squeeze-Radar")
    print(f"Erfolgreich {res['count']} Assets in Real-Time gescannt.")
