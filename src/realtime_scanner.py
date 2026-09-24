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

from src.paths import data_file

ALERTS_LOG_FILE = data_file("realtime_alerts.json")
LIVE_PRICES_FILE = data_file("live_ticks.json")
#: A candle older than this is not a live price. Fifteen minutes is generous
#: next to the five-minute polling interval, and still rules out the after-hours
#: prints that produced phantom spikes.
MAX_CANDLE_AGE_MIN = 15.0

#: The window the spike is supposed to measure, and how far the real gap between
#: the two candles may deviate from it before the reading is discarded.
SPIKE_WINDOW_MIN = 5.0
MIN_WINDOW_SPAN_MIN = 2.0
MAX_WINDOW_SPAN_MIN = 12.0

#: Baseline for the volume ratio: the twenty minutes before the move, and the
#: fewest candles that still make an average worth comparing against.
BASELINE_WINDOW_MIN = 20.0
MIN_BASELINE_CANDLES = 8


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
        """Fetches 5-minute price history and detects spikes statelessly (perfect for GH Actions).

        Candles are selected by TIMESTAMP, not by position. The older code took
        Close[-1] against Close[-5] and called the difference a five-minute move,
        which is only true while the market trades every minute. It does not:

          23.09. 21:57  45.08   <- Close[-5], regular session
          23.09. 22:00  45.05   <- regular close
          23.09. 22:51  48.67   <- after hours, thin
          23.09. 23:15  48.67   <- Close[-1]

        Those two candles are 78 minutes apart, and the drift between them was
        reported as "+8.0% in 5 minutes". The bot bought a 3x turbo on it at 09:42
        the next morning - when the underlying had not traded for ten hours - and
        the position lost 23.6% the moment it was revalued against the real market.
        A stop cannot protect a position whose entry price never existed.
        """
        now = get_berlin_now()
        is_crypto = "-USD" in symbol

        try:
            # 1. Fetch live ticks using 1m interval
            t = yf.Ticker(symbol)
            df = t.history(period="1d", interval="1m", prepost=True)

            if df.empty or len(df) < 5:
                return None

            idx = df.index
            try:
                jetzt = (pd.Timestamp.now(tz=idx.tz) if getattr(idx, "tz", None)
                         else pd.Timestamp.now())
            except Exception:
                return None

            # Gate A: the newest candle must be recent. An old one means the
            # market is closed or the name barely trades - in both cases there is
            # no live price to act on, whatever the numbers look like.
            alter_min = (jetzt - idx[-1]).total_seconds() / 60.0
            if alter_min > MAX_CANDLE_AGE_MIN:
                return None

            # Gate B: the reference candle is picked by time, and the window it
            # actually spans has to resemble the window we claim to measure.
            ziel = idx[-1] - pd.Timedelta(minutes=SPIKE_WINDOW_MIN)
            pos = int(idx.get_indexer([ziel], method="nearest")[0])
            if pos < 0 or pos >= len(idx) - 1:
                return None
            spanne_min = (idx[-1] - idx[pos]).total_seconds() / 60.0
            if not (MIN_WINDOW_SPAN_MIN <= spanne_min <= MAX_WINDOW_SPAN_MIN):
                return None

            current_price = float(df["Close"].iloc[-1])
            five_mins_ago_price = float(df["Close"].iloc[pos])

            if five_mins_ago_price <= 0:
                return None

            change_pct = ((current_price - five_mins_ago_price) / five_mins_ago_price) * 100.0
            
            # Threshold: > 0.5% in 5 minutes for stocks, > 1.0% for crypto
            threshold = 1.0 if is_crypto else 0.5
            
            if abs(change_pct) >= threshold:
                direction = "LONG" if change_pct > 0 else "SHORT"
                msg = f"🚨 {symbol} explodiert um {change_pct:+.2f}% in 5 Min.! Momentum aktiv." if direction == "LONG" else f"🚨 {symbol} stürzt um {change_pct:+.2f}% in 5 Min. ab! Panik-Verkauf aktiv."
                
                # Volume confirmation: the volume during the move against the
                # twenty minutes before it. Both windows are cut by TIMESTAMP for
                # the same reason the price window is: iloc[-25:-5] assumed
                # twenty consecutive minutes of trading, so right after an open -
                # or across a session break - the "preceding twenty minutes"
                # could reach back into the previous day. That is how a quiet
                # name collects a volume ratio it never earned.
                vol_ratio = None
                try:
                    if "Volume" in df.columns:
                        ref_ts = idx[pos]
                        im_spike = idx > ref_ts
                        im_basis = ((idx > ref_ts - pd.Timedelta(minutes=BASELINE_WINDOW_MIN))
                                    & (idx <= ref_ts))
                        spike_v = df["Volume"][im_spike]
                        basis_v = df["Volume"][im_basis]
                        basis_idx = idx[im_basis]
                        # A ratio needs a real baseline: enough candles, and a
                        # stretch of time that actually resembles twenty minutes.
                        genug = (len(spike_v) >= 2
                                 and len(basis_v) >= MIN_BASELINE_CANDLES)
                        if genug:
                            basis_spanne = (basis_idx[-1] - basis_idx[0]).total_seconds() / 60.0
                            genug = basis_spanne <= BASELINE_WINDOW_MIN * 1.5
                        if genug:
                            base_vol = float(basis_v.mean())
                            spike_vol = float(spike_v.mean())
                            # Right after the open the preceding minutes are nearly
                            # empty, which produced ratios of 300-490x for German
                            # listings - every one of them then collected full marks
                            # on the volume factor while the absolute turnover was
                            # negligible.
                            if base_vol >= 50 and spike_vol > 0:
                                vol_ratio = round(min(spike_vol / base_vol, 10.0), 2)
                except Exception:
                    vol_ratio = None

                return {
                    "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
                    "time_str": now.strftime("%H:%M:%S"),
                    # Age of the underlying market data, not of the alert. Gate 6
                    # in portfolio.py checks the latter and was happy with a fresh
                    # alert built on ten-hour-old candles.
                    "data_age_min": round(alter_min, 1),
                    "window_span_min": round(spanne_min, 1),
                    "symbol": symbol,
                    "direction": direction,
                    "trigger_price": round(current_price, 2),
                    "change_1min_pct": round(abs(change_pct), 2),  # Used for leverage calc
                    "vol_ratio": vol_ratio,  # Used by the daytrade entry score
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
                if (get_berlin_now().replace(tzinfo=None) - last_time).total_seconds() < 1800:
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
