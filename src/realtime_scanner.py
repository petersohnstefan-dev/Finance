import os
import time
import datetime
from zoneinfo import ZoneInfo
BERLIN_TZ = ZoneInfo("Europe/Berlin")
def get_berlin_now() -> datetime.datetime:
    try:
        return datetime.datetime.now(BERLIN_TZ)
    except Exception:
        return datetime.datetime.utcnow() + datetime.timedelta(hours=2)
import json
import urllib.request
import pandas as pd
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor
import yfinance as yf
from src.universe import FULL_MARKET_UNIVERSE

ALERTS_LOG_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "realtime_alerts.json")
LIVE_PRICES_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "live_ticks.json")

class RealTimeBreakoutScanner:
    """Monitors live price ticks and volume spikes in real-time across 500+ assets statelessly."""

    def __init__(self):
        self._load_state()

    def _load_state(self):
        if not os.path.exists(ALERTS_LOG_FILE):
            os.makedirs(os.path.dirname(ALERTS_LOG_FILE), exist_ok=True)
            with open(ALERTS_LOG_FILE, "w", encoding="utf-8") as f:
                json.dump([], f)

    def fetch_stateless_spike(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetches 5-minute price history and detects spikes statelessly (perfect for GH Actions)."""
        now = get_berlin_now()
        is_crypto = "-USD" in symbol
        
        try:
            # 1. Fetch live ticks using 1m interval
            t = yf.Ticker(symbol)
            df = t.history(period="1d", interval="1m", prepost=True)
            
            if df.empty or len(df) < 5:
                return None
                
            current_price = float(df["Close"].iloc[-1])
            five_mins_ago_price = float(df["Close"].iloc[-5])
            
            if five_mins_ago_price <= 0:
                return None
                
            change_pct = ((current_price - five_mins_ago_price) / five_mins_ago_price) * 100.0
            
            # Threshold: > 0.5% in 5 minutes for stocks, > 1.0% for crypto
            threshold = 1.0 if is_crypto else 0.5
            
            if abs(change_pct) >= threshold:
                direction = "LONG" if change_pct > 0 else "SHORT"
                msg = f"🚨 {symbol} explodiert um {change_pct:+.2f}% in 5 Min.! Momentum aktiv." if direction == "LONG" else f"🚨 {symbol} stürzt um {change_pct:+.2f}% in 5 Min. ab! Panik-Verkauf aktiv."
                
                return {
                    "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
                    "time_str": now.strftime("%H:%M:%S"),
                    "symbol": symbol,
                    "direction": direction,
                    "trigger_price": round(current_price, 2),
                    "change_1min_pct": round(abs(change_pct), 2),  # Used for leverage calc
                    "urgency": "⚡ EXTREM (Sofortiger Intraday-Ausbruch)",
                    "message": msg
                }
            return None
        except Exception:
            return None

    def scan_all_stateless(self) -> Dict[str, Any]:
        """Scans ALL 500+ assets in FULL_MARKET_UNIVERSE."""
        tickers = FULL_MARKET_UNIVERSE
        now = get_berlin_now()
        new_alerts = []
        
        def fetch_single(sym):
            try:
                return self.fetch_stateless_spike(sym)
            except Exception:
                return None

        with ThreadPoolExecutor(max_workers=30) as executor:
            results = list(executor.map(fetch_single, tickers))

        for res in results:
            if res:
                new_alerts.append(res)
                self._record_alert(res)

        return {
            "count": len(tickers),
            "alerts": new_alerts
        }

    def _record_alert(self, alert: Dict[str, Any]):
        try:
            alerts = []
            if os.path.exists(ALERTS_LOG_FILE):
                with open(ALERTS_LOG_FILE, "r", encoding="utf-8") as f:
                    alerts = json.load(f)
            
            # Prevent duplicate alerts for same symbol within 30 minutes
            recent = [a for a in alerts if a["symbol"] == alert["symbol"]]
            if recent:
                last_time = datetime.datetime.strptime(recent[0]["timestamp"], "%Y-%m-%d %H:%M:%S")
                if (datetime.datetime.now() - last_time).total_seconds() < 1800:
                    return

            alerts.insert(0, alert)
            alerts = alerts[:50]
            with open(ALERTS_LOG_FILE, "w", encoding="utf-8") as f:
                json.dump(alerts, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    @staticmethod
    def get_recent_alerts() -> List[Dict[str, Any]]:
        if os.path.exists(ALERTS_LOG_FILE):
            try:
                with open(ALERTS_LOG_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

if __name__ == "__main__":
    scanner = RealTimeBreakoutScanner()
    print("Starte ZUSTANDSLOSEN Multi-Asset Real-Time-Scan fr GitHub Actions...")
    res = scanner.scan_all_stateless()
    print(f"Erfolgreich {res['count']} Assets in Real-Time gescannt. {len(res['alerts'])} neue Alarme.")
