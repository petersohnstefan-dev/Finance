import json
import os
import datetime
from typing import Dict, Any, List, Optional
import yfinance as yf
from src.db import PortfolioDB
from src.derivatives import DerivativeEngine

PORTFOLIO_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "portfolios.json")

from zoneinfo import ZoneInfo
BERLIN_TZ = ZoneInfo("Europe/Berlin")

def get_berlin_now() -> datetime.datetime:
    try:
        return datetime.datetime.now(BERLIN_TZ)
    except Exception:
        return datetime.datetime.utcnow() + datetime.timedelta(hours=2)

class PortfolioManager:
    """Manages 3 distinct paper trading portfolios (Short-Term, Medium-Term, Long-Term)."""

    def __init__(self, initial_capital_per_depot: float = 10000.0):
        self.initial_capital = initial_capital_per_depot
        self.db = PortfolioDB()
        self.data = self._load()

    def _get_seed_data(self) -> Dict[str, Any]:
        now_str = get_berlin_now().strftime("%Y-%m-%d %H:%M:%S")
        return {
            "created_at": now_str,
            "currency": "EUR",
            "portfolios": {
                "short_term": {
                    "name": "⚡ Kurzfristiges Trading-Depot (Tage–Wochen / Squeezes & Hebel)",
                    "strategy": "Aggressives Swing-Trading auf akute Ausbrüche, Short Squeezes & Krypto-Momentum via Hebel / Knock-Outs (Stop-Loss -7% / Take-Profit +20%).",
                    "initial_cash": self.initial_capital,
                    "cash": 4500.0,
                    "positions": {
                        "MRNA": {
                            "symbol": "MRNA", "name": "Moderna, Inc.", "shares": 15.0943,
                            "buy_price": 132.50, "current_price": 138.89, "buy_date": "2026-08-20 15:45",
                            "stop_loss": 123.23, "take_profit": 159.00,
                            "reason": "Akuter Biotech-Ausbruch & hoher Short Float (15.2%)",
                            "derivative_type": "STOCK", "last_updated": get_berlin_now().strftime("%H:%M:%S")
                        },
                        "RIVN": {
                            "symbol": "RIVN", "name": "Rivian Automotive, Inc.", "shares": 128.2051,
                            "buy_price": 15.60, "current_price": 16.60, "buy_date": "2026-08-21 16:20",
                            "stop_loss": 14.51, "take_profit": 18.72,
                            "reason": "Top Kurzfrist-Momentum (95/100) & CEO-Insiderkauf",
                            "derivative_type": "STOCK", "last_updated": get_berlin_now().strftime("%H:%M:%S")
                        },
                        "SOL-USD": {
                            "symbol": "SOL-USD", "name": "Solana USD", "shares": 15.9236,
                            "buy_price": 94.20, "current_price": 99.80, "buy_date": "2026-08-22 11:30",
                            "stop_loss": 87.61, "take_profit": 113.04,
                            "reason": "High-Beta Krypto-Momentum mit bullischem MACD-Setup",
                            "derivative_type": "STOCK", "last_updated": get_berlin_now().strftime("%H:%M:%S")
                        }
                    },
                    "history": [
                        {"type": "BUY", "symbol": "MRNA", "name": "Moderna, Inc.", "product_type": "STOCK", "shares": 15.0943, "price": 132.50, "total": 2000.0, "date": "2026-08-20 15:45", "reason": "Akuter Biotech-Ausbruch & hoher Short Float (15.2%)"},
                        {"type": "BUY", "symbol": "RIVN", "name": "Rivian Automotive, Inc.", "product_type": "STOCK", "shares": 128.2051, "price": 15.60, "total": 2000.0, "date": "2026-08-21 16:20", "reason": "Top Kurzfrist-Momentum (95/100) & CEO-Insiderkauf"},
                        {"type": "BUY", "symbol": "SOL-USD", "name": "Solana USD", "product_type": "STOCK", "shares": 15.9236, "price": 94.20, "total": 1500.0, "date": "2026-08-22 11:30", "reason": "High-Beta Krypto-Momentum mit bullischem MACD-Setup"}
                    ]
                },
                "medium_term": {
                    "name": "📈 Mittelfristiges Trend- & Growth-Depot (1–6 Monate / Swing)",
                    "strategy": "Mittelfristige Trendfolge auf führende Wachstumsaktien & KI-Leader über der 50-Tage-Linie (Trailing Stop-Loss -10% / Take-Profit +35%).",
                    "initial_cash": self.initial_capital,
                    "cash": 4000.0,
                    "positions": {
                        "PLTR": {
                            "symbol": "PLTR", "name": "Palantir Technologies Inc.", "shares": 12.3153,
                            "buy_price": 162.40, "current_price": 175.89, "buy_date": "2026-08-10 15:35",
                            "stop_loss": 158.30, "take_profit": 237.45,
                            "reason": "KI-Enterprise-Wachstum & Trendfolge über EMA 50",
                            "derivative_type": "STOCK", "last_updated": get_berlin_now().strftime("%H:%M:%S")
                        },
                        "DUOL": {
                            "symbol": "DUOL", "name": "Duolingo, Inc.", "shares": 14.4404,
                            "buy_price": 138.50, "current_price": 146.84, "buy_date": "2026-08-12 16:10",
                            "stop_loss": 132.16, "take_profit": 198.23,
                            "reason": "Stabiles Umsatzwachstum & Ausbruch über 200-Tage-Linie",
                            "derivative_type": "STOCK", "last_updated": get_berlin_now().strftime("%H:%M:%S")
                        },
                        "NVDA": {
                            "symbol": "NVDA", "name": "NVIDIA Corporation", "shares": 10.1937,
                            "buy_price": 196.20, "current_price": 208.48, "buy_date": "2026-08-14 17:45",
                            "stop_loss": 187.63, "take_profit": 281.45,
                            "reason": "KI-Hardware-Monopol & Nancy Pelosi Call-Optionen",
                            "derivative_type": "STOCK", "last_updated": get_berlin_now().strftime("%H:%M:%S")
                        }
                    },
                    "history": [
                        {"type": "BUY", "symbol": "PLTR", "name": "Palantir Technologies Inc.", "product_type": "STOCK", "shares": 12.3153, "price": 162.40, "total": 2000.0, "date": "2026-08-10 15:35", "reason": "KI-Enterprise-Wachstum & Trendfolge über EMA 50"},
                        {"type": "BUY", "symbol": "DUOL", "name": "Duolingo, Inc.", "product_type": "STOCK", "shares": 14.4404, "price": 138.50, "total": 2000.0, "date": "2026-08-12 16:10", "reason": "Stabiles Umsatzwachstum & Ausbruch über 200-Tage-Linie"},
                        {"type": "BUY", "symbol": "NVDA", "name": "NVIDIA Corporation", "product_type": "STOCK", "shares": 10.1937, "price": 196.20, "total": 2000.0, "date": "2026-08-14 17:45", "reason": "KI-Hardware-Monopol & Nancy Pelosi Call-Optionen"}
                    ]
                },
                "long_term": {
                    "name": "🏛️ Langfristiges Investment-Depot (Jahre / Quality, Gold & Moat)",
                    "strategy": "Klassisches Buy & Hold bei krisenfesten Burggraben-Unternehmen (ROE > 15%), Gold zur Absicherung, Bitcoin-Core und Bonus-Zertifikaten.",
                    "initial_cash": self.initial_capital,
                    "cash": 3000.0,
                    "positions": {
                        "SAP.DE": {
                            "symbol": "SAP.DE", "name": "SAP SE", "shares": 10.6838,
                            "buy_price": 187.20, "current_price": 185.92, "buy_date": "2026-08-01 10:15",
                            "stop_loss": None, "take_profit": None,
                            "reason": "Europäischer Software-Monopolist, ROE 18.3%, solide Bilanz",
                            "derivative_type": "STOCK", "last_updated": get_berlin_now().strftime("%H:%M:%S")
                        },
                        "MUV2.DE": {
                            "symbol": "MUV2.DE", "name": "Münchener Rück AG", "shares": 3.8565,
                            "buy_price": 518.60, "current_price": 518.60, "buy_date": "2026-08-01 10:15",
                            "stop_loss": None, "take_profit": None,
                            "reason": "Münchener Rück: KGV unter 10, exzellente Dividendenhistorie",
                            "derivative_type": "STOCK", "last_updated": get_berlin_now().strftime("%H:%M:%S")
                        },
                        "GC=F": {
                            "symbol": "GC=F", "name": "Gold Futures", "shares": 0.3186,
                            "buy_price": 4708.60, "current_price": 4692.70, "buy_date": "2026-08-01 10:15",
                            "stop_loss": None, "take_profit": None,
                            "reason": "Gold: Makro-Wertspeicher & Inflationsschutz im Bullenmarkt",
                            "derivative_type": "STOCK", "last_updated": get_berlin_now().strftime("%H:%M:%S")
                        },
                        "BTC-USD": {
                            "symbol": "BTC-USD", "name": "Bitcoin USD", "shares": 0.0191,
                            "buy_price": 78682.79, "current_price": 79228.74, "buy_date": "2026-08-01 10:15",
                            "stop_loss": None, "take_profit": None,
                            "reason": "Bitcoin: Digitales Gold & langfristiger Makrotrend über SMA200",
                            "derivative_type": "STOCK", "last_updated": get_berlin_now().strftime("%H:%M:%S")
                        }
                    },
                    "history": [
                        {"type": "BUY", "symbol": "SAP.DE", "name": "SAP SE", "product_type": "STOCK", "shares": 10.6838, "price": 187.20, "total": 2000.0, "date": "2026-08-01 10:15", "reason": "Europäischer Software-Monopolist, ROE 18.3%, solide Bilanz"},
                        {"type": "BUY", "symbol": "MUV2.DE", "name": "Münchener Rück AG", "product_type": "STOCK", "shares": 3.8565, "price": 518.60, "total": 2000.0, "date": "2026-08-01 10:15", "reason": "Münchener Rück: KGV unter 10, exzellente Dividendenhistorie"},
                        {"type": "BUY", "symbol": "GC=F", "name": "Gold Futures", "product_type": "STOCK", "shares": 0.3186, "price": 4708.60, "total": 1500.0, "date": "2026-08-01 10:15", "reason": "Gold: Makro-Wertspeicher & Inflationsschutz im Bullenmarkt"},
                        {"type": "BUY", "symbol": "BTC-USD", "name": "Bitcoin USD", "product_type": "STOCK", "shares": 0.0191, "price": 78682.79, "total": 1500.0, "date": "2026-08-01 10:15", "reason": "Bitcoin: Digitales Gold & langfristiger Makrotrend über SMA200"}
                    ]
                }
            }
        }

    def _load(self) -> Dict[str, Any]:
        """Loads existing portfolio state, ensuring all 3 depots have active positions."""
        if os.path.exists(PORTFOLIO_FILE):
            try:
                with open(PORTFOLIO_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if "portfolios" in data and "short_term" in data["portfolios"]:
                        # Ensure positions exist in medium_term
                        if not data["portfolios"].get("medium_term", {}).get("positions"):
                            seed = self._get_seed_data()
                            data["portfolios"]["medium_term"] = seed["portfolios"]["medium_term"]
                            self._save(data)
                        return data
            except Exception:
                pass

        seed_data = self._get_seed_data()
        self._save(seed_data)
        return seed_data

    def _save(self, data: Optional[Dict[str, Any]] = None):
        if data is None:
            data = self.data
        os.makedirs(os.path.dirname(PORTFOLIO_FILE), exist_ok=True)
        with open(PORTFOLIO_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def buy(self, depot_key: str, symbol: str, name: str, shares: float, price: float, 
            reason: str = "", stop_loss: Optional[float] = None, take_profit: Optional[float] = None,
            derivative_meta: Optional[Dict[str, Any]] = None) -> bool:
        """Executes a buy order and logs to SQLite + JSON."""
        depot = self.data["portfolios"].get(depot_key)
        if not depot:
            return False

        cost = shares * price
        if cost > depot["cash"]:
            shares = depot["cash"] / price
            cost = shares * price

        if shares <= 0 or cost <= 0:
            return False

        depot["cash"] -= cost
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

        pos_dict = {
            "symbol": symbol,
            "name": name,
            "shares": round(shares, 4),
            "buy_price": round(price, 2),
            "current_price": round(price, 2),
            "buy_date": now_str,
            "stop_loss": round(stop_loss, 2) if stop_loss else None,
            "take_profit": round(take_profit, 2) if take_profit else None,
            "reason": reason,
            "derivative_type": derivative_meta.get("type", "STOCK") if derivative_meta else "STOCK"
        }
        if derivative_meta:
            pos_dict.update(derivative_meta)

        depot["positions"][symbol] = pos_dict

        trade_record = {
            "type": "BUY",
            "symbol": symbol,
            "name": name,
            "product_type": pos_dict["derivative_type"],
            "shares": round(shares, 4),
            "price": round(price, 2),
            "total": round(cost, 2),
            "date": now_str,
            "reason": reason
        }
        depot["history"].append(trade_record)

        try:
            self.db.record_trade(depot_key, "BUY", symbol, name, shares, cost, price, reason=reason)
        except Exception:
            pass

        self._save()
        return True

    def sell(self, depot_key: str, symbol: str, price: float, reason: str = "") -> bool:
        """Sells an entire open position and records realized gain/loss."""
        depot = self.data["portfolios"].get(depot_key)
        if not depot or symbol not in depot["positions"]:
            return False

        pos = depot["positions"][symbol]
        shares = pos["shares"]
        revenue = shares * price
        pnl = (price - pos["buy_price"]) * shares
        pnl_pct = ((price - pos["buy_price"]) / pos["buy_price"]) * 100.0 if pos["buy_price"] > 0 else 0.0

        depot["cash"] += revenue
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

        trade_record = {
            "type": "SELL",
            "symbol": symbol,
            "name": pos["name"],
            "product_type": pos.get("derivative_type", "STOCK"),
            "shares": round(shares, 4),
            "buy_price": round(pos["buy_price"], 2),
            "sell_price": round(price, 2),
            "total": round(revenue, 2),
            "pnl": round(pnl, 2),
            "pnl_pct": round(pnl_pct, 2),
            "date": now_str,
            "reason": reason
        }
        depot["history"].append(trade_record)

        try:
            self.db.record_trade(depot_key, "SELL", symbol, pos["name"], shares, revenue, 
                                 pos["buy_price"], sell_price=price, pnl=pnl, pnl_pct=pnl_pct, reason=reason)
        except Exception:
            pass

        del depot["positions"][symbol]
        self._save()
        return True

    def update_live_prices(self):
        """Fetches fresh live tick prices for all positions across all 3 depots in parallel."""
        from src.realtime_scanner import RealTimeBreakoutScanner
        from concurrent.futures import ThreadPoolExecutor
        scanner = RealTimeBreakoutScanner()
        
        underlying_prices = {}
        all_symbols = set()
        
        for depot in self.data["portfolios"].values():
            for sym, pos in depot["positions"].items():
                und_sym = pos.get("underlying_symbol", sym)
                all_symbols.add(und_sym)

        def fetch_single(sym):
            try:
                px = scanner.get_live_tick(sym)
                return sym, px
            except Exception:
                return sym, None

        with ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(fetch_single, list(all_symbols)))

        for sym, px in results:
            if px and px > 0:
                underlying_prices[sym] = round(px, 2)

        now_str = get_berlin_now().strftime("%H:%M:%S")
        for depot in self.data["portfolios"].values():
            for sym, pos in list(depot["positions"].items()):
                und_sym = pos.get("underlying_symbol", sym)
                curr_und_p = underlying_prices.get(und_sym)
                if curr_und_p:
                    pos["last_updated"] = now_str
                    if pos.get("derivative_type") in ["KNOCKOUT", "FACTOR", "BONUS"]:
                        DerivativeEngine.update_derivative_price(pos, curr_und_p)
                    else:
                        pos["current_price"] = curr_und_p

        self._save()

    def get_depot_summary(self, depot_key: str) -> Dict[str, Any]:
        """Calculates total portfolio value, return, allocation, and open position P&L."""
        depot = self.data["portfolios"].get(depot_key, {})
        cash = depot.get("cash", self.initial_capital)
        init_cash = depot.get("initial_cash", self.initial_capital)

        positions_list = []
        invested_value = 0.0

        for sym, pos in depot.get("positions", {}).items():
            curr_p = pos.get("current_price", pos["buy_price"])
            buy_p = pos["buy_price"]
            shares = pos["shares"]
            pos_val = shares * curr_p
            pnl = (curr_p - buy_p) * shares
            pnl_pct = ((curr_p - buy_p) / buy_p * 100.0) if buy_p > 0 else 0.0

            invested_value += pos_val
            positions_list.append({
                "symbol": sym,
                "name": pos.get("name", sym),
                "product_type": pos.get("derivative_type", "STOCK"),
                "shares": shares,
                "buy_price": buy_p,
                "current_price": curr_p,
                "last_updated": pos.get("last_updated", "-"),
                "value": round(pos_val, 2),
                "pnl": round(pnl, 2),
                "pnl_pct": round(pnl_pct, 2),
                "stop_loss": pos.get("stop_loss"),
                "take_profit": pos.get("take_profit"),
                "distance_to_ko": pos.get("distance_to_ko_pct") or pos.get("distance_to_barrier_pct"),
                "leverage": pos.get("leverage"),
                "buy_date": pos.get("buy_date"),
                "reason": pos.get("reason", "")
            })

        total_value = cash + invested_value
        total_pnl = total_value - init_cash
        total_pnl_pct = (total_pnl / init_cash) * 100.0

        try:
            self.db.record_daily_snapshot(
                depot_key, total_value, cash, invested_value, total_pnl, total_pnl_pct, len(positions_list)
            )
        except Exception:
            pass

        return {
            "name": depot.get("name"),
            "strategy": depot.get("strategy"),
            "total_value": round(total_value, 2),
            "cash": round(cash, 2),
            "invested_value": round(invested_value, 2),
            "cash_ratio_pct": round((cash / total_value * 100.0) if total_value > 0 else 100.0, 1),
            "total_pnl": round(total_pnl, 2),
            "total_pnl_pct": round(total_pnl_pct, 2),
            "positions": positions_list,
            "history": list(reversed(depot.get("history", [])))
        }

    def auto_trade_check(self, scan_results: List[Dict[str, Any]]) -> List[str]:
        """Autonomous 3-Depot AI Trading Engine driven by Real-Time Ticks and Multi-Factor Intelligence."""
        actions_taken = []
        self.update_live_prices()

        from src.realtime_scanner import RealTimeBreakoutScanner
        rt_alerts = RealTimeBreakoutScanner.get_recent_alerts()

        # 1. Kurzfristiges Trading-Depot (Squeezes, Ausbrüche & Hebel)
        st_depot = self.data["portfolios"]["short_term"]
        for sym in list(st_depot["positions"].keys()):
            pos = st_depot["positions"][sym]
            curr_p = pos["current_price"]
            if pos.get("is_knocked_out"):
                self.sell("short_term", sym, 0.001, reason="❌ Knock-Out Barriere berührt (Totalverlust)")
                actions_taken.append(f"KNOCK-OUT {sym}")
                continue
            if pos.get("stop_loss") and curr_p <= pos["stop_loss"]:
                self.sell("short_term", sym, curr_p, reason="🚨 Stop-Loss ausgelöst (-7%) zur Verlustbegrenzung")
                actions_taken.append(f"VERKAUF {sym} (Stop-Loss)")
            elif pos.get("take_profit") and curr_p >= pos["take_profit"]:
                self.sell("short_term", sym, curr_p, reason="🎯 Take-Profit erreicht (+20%)")
                actions_taken.append(f"VERKAUF {sym} (Take-Profit)")

        if st_depot["cash"] >= 1500.0 and len(st_depot["positions"]) < 4:
            # Priority 1: Instant Real-Time Sub-Minute Alerts
            bought_from_realtime = False
            for alert in rt_alerts:
                sym = alert["symbol"]
                p = alert.get("trigger_price")
                if sym not in st_depot["positions"] and p and p > 0:
                    alloc = min(2000.0, st_depot["cash"] * 0.85)
                    shares = alloc / p
                    self.buy("short_term", sym, alert.get("name", sym), shares, p,
                             reason=f"⚡ Echtzeit-Intraday-Spike ({alert.get('change_1min_pct', 2.0):+.1f}% in <60s / {alert.get('urgency', 'Alarm')})",
                             stop_loss=p*0.93, take_profit=p*1.20)
                    actions_taken.append(f"KAUF {sym} (⚡ Echtzeit-Spike)")
                    bought_from_realtime = True
                    break

            # Priority 2: High-Ranked Universe Breakouts
            if not bought_from_realtime:
                candidates = sorted(scan_results, key=lambda x: (x.get("breakout_score", 0) + x.get("short_score", 0)), reverse=True)
                for cand in candidates:
                    sym = cand["symbol"]
                    p = cand.get("price")
                    if sym not in st_depot["positions"] and p and p > 0:
                        alloc = min(2000.0, st_depot["cash"] * 0.85)
                        if cand.get("breakout_score", 0) >= 45:
                            turbo = DerivativeEngine.create_turbo_knockout(sym, cand.get("name", sym), p, direction="LONG", target_leverage=3.5)
                            cert_price = turbo["cert_price"]
                            shares = alloc / cert_price
                            self.buy("short_term", turbo["wkn"], turbo["name"], shares, cert_price,
                                     reason=f"🚨 Akuter Ausbruchs-Alarm ({cand.get('breakout_score')}/100)",
                                     stop_loss=cert_price*0.85, take_profit=cert_price*1.40, derivative_meta=turbo)
                            actions_taken.append(f"KAUF {turbo['name']} für Kurzfrist-Depot")
                        else:
                            shares = alloc / p
                            self.buy("short_term", sym, cand.get("name", sym), shares, p,
                                     reason=f"Kurzfrist-Momentum ({cand.get('short_score')}/100)",
                                     stop_loss=p*0.93, take_profit=p*1.20)
                            actions_taken.append(f"KAUF {sym} für Kurzfrist-Depot")
                        break

        # 2. Mittelfristiges Trend- & Growth-Depot (1–6 Monate / Swing)
        mt_depot = self.data["portfolios"]["medium_term"]
        for sym in list(mt_depot["positions"].keys()):
            pos = mt_depot["positions"][sym]
            curr_p = pos["current_price"]
            if pos.get("stop_loss") and curr_p <= pos["stop_loss"]:
                self.sell("medium_term", sym, curr_p, reason="🚨 Trailing Stop-Loss ausgelöst (-10%)")
                actions_taken.append(f"VERKAUF {sym} (Mittelfrist-Stop)")
            elif pos.get("take_profit") and curr_p >= pos["take_profit"]:
                self.sell("medium_term", sym, curr_p, reason="🎯 Mittelfrist-Kursziel erreicht (+35%)")
                actions_taken.append(f"VERKAUF {sym} (Mittelfrist-Ziel)")

        if mt_depot["cash"] >= 1500.0 and len(mt_depot["positions"]) < 4:
            candidates = sorted(scan_results, key=lambda x: (x.get("short_score", 0) * 0.5 + x.get("long_score", 0) * 0.5), reverse=True)
            for cand in candidates:
                sym = cand["symbol"]
                p = cand.get("price")
                if sym not in mt_depot["positions"] and p and p > 0:
                    alloc = min(2000.0, mt_depot["cash"] * 0.85)
                    shares = alloc / p
                    self.buy("medium_term", sym, cand.get("name", sym), shares, p,
                             reason=f"📈 Starker mittelfristiger Trend & Wachstum (Gesamt: {cand.get('total_score')}/100)",
                             stop_loss=p*0.90, take_profit=p*1.35)
                    actions_taken.append(f"KAUF {sym} für Mittelfrist-Depot")
                    break

        # 3. Langfristiges Investment-Depot (Jahre / Quality & Moat)
        lt_depot = self.data["portfolios"]["long_term"]
        if lt_depot["cash"] >= 1500.0 and len(lt_depot["positions"]) < 4:
            candidates = sorted(scan_results, key=lambda x: x.get("long_score", 0), reverse=True)
            for cand in candidates:
                sym = cand["symbol"]
                p = cand.get("price")
                if sym not in lt_depot["positions"] and p and p > 0:
                    alloc = min(2000.0, lt_depot["cash"] * 0.85)
                    if cand.get("long_score", 0) >= 90:
                        bonus = DerivativeEngine.create_bonus_certificate(sym, cand.get("name", sym), p, barrier_pct=25.0, bonus_pct=14.0)
                        shares = alloc / p
                        self.buy("long_term", bonus["wkn"], bonus["name"], shares, p,
                                 reason=f"🛡️ Bonus-Zertifikat (-25% Puffer, +14% Bonus)",
                                 derivative_meta=bonus)
                        actions_taken.append(f"KAUF {bonus['name']} für Langfrist-Depot")
                    else:
                        shares = alloc / p
                        self.buy("long_term", sym, cand.get("name", sym), shares, p,
                                 reason=f"Qualitäts-Compounder ({cand.get('long_score')}/100)")
                        actions_taken.append(f"KAUF {sym} für Langfrist-Depot")
                    break

        return actions_taken
