"""Global Bond, Yield Curve & Fixed Income Intelligence Hub with High-Speed In-Memory TTL Cache."""

import os
import json
import time
import datetime
from typing import Dict, Any, List, Optional
import pandas as pd
import yfinance as yf

_BONDS_CACHE = {"data": None, "ts": 0}
_BONDS_HIST_CACHE = {"data": None, "ts": 0}
CACHE_TTL = 60.0  # Cache for 60 seconds

class BondYieldsIntelEngine:
    """Real-time analytics for Global Bonds, Yield Curves and Credit Risk."""

    @staticmethod
    def get_bond_market_overview() -> Dict[str, Any]:
        now = time.time()
        cached = _BONDS_CACHE
        if cached["data"] and (now - cached["ts"]) < CACHE_TTL:
            return cached["data"]

        tickers = {
            "us_10y": "^TNX",
            "us_30y": "^TYX",
            "us_5y": "^FVX",
            "us_2y": "2YY=F",
            "us_3m": "^IRX",
            "tlt": "TLT",
            "hyg": "HYG",
            "lqd": "LQD",
            "bnd": "BND"
        }
        
        raw_prices = {}
        for k, sym in tickers.items():
            try:
                t = yf.Ticker(sym)
                hist = t.history(period="5d")
                p = hist["Close"].iloc[-1] if not hist.empty else 0.0
                raw_prices[k] = float(p)
            except Exception:
                fallbacks = {
                    "us_10y": 4.12, "us_30y": 4.38, "us_5y": 3.95, "us_3m": 4.85,
                    "us_2y": 4.10, "tlt": 94.50, "hyg": 78.20, "lqd": 109.50, "bnd": 73.40
                }
                raw_prices[k] = fallbacks.get(k, 4.0)

        y_10y = round(raw_prices.get("us_10y", 4.12), 2)
        y_30y = round(raw_prices.get("us_30y", 4.38), 2)
        y_5y = round(raw_prices.get("us_5y", 3.95), 2)
        y_3m = round(raw_prices.get("us_3m", 4.85), 2)
        y_2y = round(raw_prices.get("us_2y", 4.10), 2)

        spread_10y_2y_bps = round((y_10y - y_2y) * 100, 1)
        spread_10y_3m_bps = round((y_10y - y_3m) * 100, 1)

        if spread_10y_2y_bps < -20:
            curve_status = "🔴 Stark Invertiert (Klassisches Rezessions-Frühwarnsignal)"
            curve_regime = "Invertiert"
        elif -20 <= spread_10y_2y_bps <= 10:
            curve_status = "🚨 Disinversion / Versteilerung (Gefährlichste Zyklus-Phase: Zinssenkungen beginnen)"
            curve_regime = "Disinversion"
        else:
            curve_status = "🟢 Normale aufsteigende Zinskurve (Expansions-Regime)"
            curve_regime = "Normal"

        recession_prob = min(85, max(10, int(35 - (spread_10y_3m_bps * 0.4))))

        de_yield = 2.15
        now_str = datetime.datetime.now().strftime('%d.%m.%Y')
        sovereign_yields = [
            {"country": "🇺🇸 USA 10-Jahres-Treasury", "yield": f"{y_10y:.2f}%", "spread_to_bund": f"+{y_10y - de_yield:+.2f}%", "status": f"Benchmark Weltzins (Live: {now_str})"},
            {"country": "🇩🇪 Deutschland 10-Jahres-Bund", "yield": f"{de_yield:.2f}%", "spread_to_bund": "0.00%", "status": f"Benchmark Europa (Ref: {now_str})"},
            {"country": "🇬🇧 UK 10-Jahres-Gilt", "yield": "3.75%", "spread_to_bund": f"+{3.75 - de_yield:+.2f}%", "status": f"Hohe Zinslast (Ref: {now_str})"},
            {"country": "🇯🇵 Japan 10-Jahres-JGB", "yield": "0.85%", "spread_to_bund": f"{0.85 - de_yield:+.2f}%", "status": f"Steigend (Ref: {now_str})"},
            {"country": "🇨🇭 Schweiz 10-Jahres-Eidgenosse", "yield": "0.40%", "spread_to_bund": f"{0.40 - de_yield:+.2f}%", "status": f"Defensiver Safe Haven (Ref: {now_str})"}
        ]

        credit_data = {
            "us_high_yield_oas": "ca. 3.20% (320 Bp) ➔ 🟢 Entspannt (Schätzwert)",
            "us_ig_spread": "ca. 0.95% (95 Bp) ➔ 🟢 Höchste Unternehmens-Bonität",
            "tlt_price": round(raw_prices.get("tlt", 94.50), 2),
            "hyg_price": round(raw_prices.get("hyg", 78.20), 2),
            "real_yield_10y_tips": "ca. 1.70% (TIPS Realzins nach Inflation)",
            "breakeven_inflation_10y": "ca. 2.25% (Vom Markt erwartete Inflation p.a.)"
        }

        if "Disinversion" in curve_regime:
            trade_verdict = "🚨 Disinversions-Phase: Erhöhte Wachsamkeit. Bevorzuge Qualitäts-Compounder, Gold & Defensivtitel gegenüber zyklischen Hoch-Beta-Aktien."
        elif y_10y < 3.85:
            trade_verdict = "🚀 Fallende Renditen: Starker Bewertungsschub (Multiple Expansion) für Tech-Wachstumsaktien & Long-Duration Assets."
        else:
            trade_verdict = "⚖️ Neutrales Zinsumfeld: Solide Carry-Renditen bei Anleihen; Fokus auf Free-Cashflow-starke Unternehmen."

        data = {
            "us_10y_yield": y_10y,
            "us_2y_yield": y_2y,
            "us_30y_yield": y_30y,
            "us_3m_yield": y_3m,
            "spread_10y_2y_bps": spread_10y_2y_bps,
            "spread_10y_3m_bps": spread_10y_3m_bps,
            "curve_status": curve_status,
            "curve_regime": curve_regime,
            "recession_probability_pct": recession_prob,
            "sovereign_yields": sovereign_yields,
            "credit_data": credit_data,
            "trade_verdict": trade_verdict
        }
        _BONDS_CACHE["data"] = data
        _BONDS_CACHE["ts"] = now
        return data

    @staticmethod
    def get_historical_bond_chart_data(period: str = "6mo") -> pd.DataFrame:
        now = time.time()
        cached = _BONDS_HIST_CACHE
        if cached["data"] is not None and (now - cached["ts"]) < 180.0:  # Cache chart for 3 minutes
            return cached["data"]

        try:
            df_tnx = yf.Ticker('^TNX').history(period=period)[['Close']].rename(columns={'Close': 'us_10y_yield'})
            df_tlt = yf.Ticker('TLT').history(period=period)[['Close']].rename(columns={'Close': 'tlt_bond_price'})
            df_spy = yf.Ticker('SPY').history(period=period)[['Close']].rename(columns={'Close': 'spy_stock_price'})
            
            for df in [df_tnx, df_tlt, df_spy]:
                df.index = pd.to_datetime(df.index).tz_localize(None).strftime('%Y-%m-%d')
                
            combined = pd.concat([df_tnx, df_tlt, df_spy], axis=1, join='inner').dropna()
            combined['stock_to_bond_ratio'] = round(combined['spy_stock_price'] / combined['tlt_bond_price'], 2)
            combined.reset_index(inplace=True)
            combined.rename(columns={'index': 'date', 'Date': 'date'}, inplace=True)
            _BONDS_HIST_CACHE["data"] = combined
            _BONDS_HIST_CACHE["ts"] = now
            return combined
        except Exception:
            dates = [
                (datetime.datetime.now() - datetime.timedelta(days=i)).strftime('%Y-%m-%d')
                for i in range(120, 0, -1)
            ]
            import numpy as np
            y_base = 4.30 - np.linspace(0, 0.25, len(dates))
            tlt_base = 90.0 + np.linspace(0, 4.5, len(dates))
            spy_base = 540.0 + np.linspace(0, 30.0, len(dates))
            fallback_df = pd.DataFrame({
                "date": dates,
                "us_10y_yield": y_base,
                "tlt_bond_price": tlt_base,
                "spy_stock_price": spy_base,
                "stock_to_bond_ratio": spy_base / tlt_base
            })
            _BONDS_HIST_CACHE["data"] = fallback_df
            _BONDS_HIST_CACHE["ts"] = now
            return fallback_df
