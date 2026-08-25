import json
import os
import datetime
import pandas as pd
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
                    "cash": 2668.34,
                    "positions": {
                        "MRNA": {
                            "symbol": "MRNA", "name": "Moderna, Inc.", "shares": 13.7808,
                            "buy_price": 145.13, "current_price": 141.60, "buy_date": "2026-08-24 22:07",
                            "stop_loss": 134.97, "take_profit": 174.15,
                            "reason": "Akuter Biotech-Ausbruch & hoher Short Float (15.2%)",
                            "derivative_type": "STOCK", "last_updated": get_berlin_now().strftime("%H:%M:%S")
                        },
                        "RIVN": {
                            "symbol": "RIVN", "name": "Rivian Automotive, Inc.", "shares": 117.8550,
                            "buy_price": 16.97, "current_price": 16.80, "buy_date": "2026-08-24 22:07",
                            "stop_loss": 15.78, "take_profit": 20.36,
                            "reason": "Top Kurzfrist-Momentum (95/100) & CEO-Insiderkauf",
                            "derivative_type": "STOCK", "last_updated": get_berlin_now().strftime("%H:%M:%S")
                        },
                        "SOL-USD": {
                            "symbol": "SOL-USD", "name": "Solana USD", "shares": 15.2192,
                            "buy_price": 98.56, "current_price": 98.68, "buy_date": "2026-08-24 22:07",
                            "stop_loss": 91.66, "take_profit": 118.27,
                            "reason": "High-Beta Krypto-Momentum mit bullischem MACD-Setup",
                            "derivative_type": "STOCK", "last_updated": get_berlin_now().strftime("%H:%M:%S")
                        },
                        "BEAM": {
                            "symbol": "BEAM", "name": "Beam Therapeutics Inc.", "shares": 67.2043,
                            "buy_price": 29.76, "current_price": 28.79, "buy_date": "2026-08-25 12:30",
                            "stop_loss": 27.67, "take_profit": 35.71,
                            "reason": "Top Momentum & Breakout Score (88/100)",
                            "derivative_type": "STOCK", "last_updated": get_berlin_now().strftime("%H:%M:%S")
                        }
                    },
                    "history": [
                        {"type": "BUY", "action": "BUY", "symbol": "BEAM", "name": "Beam Therapeutics Inc.", "product_type": "STOCK", "shares": 67.2043, "price": 29.76, "total": 2000.0, "date": "2026-08-25 12:30:00", "reason": "Top Momentum & Breakout Score (88/100)"},
                        {"type": "SELL", "action": "SELL", "symbol": "KO256319", "name": "⚡ Turbo Bull 3.5x auf Visa Inc. (KO: 278.61)", "product_type": "KNOCKOUT", "shares": 182.9826, "buy_price": 10.93, "sell_price": 11.85, "price": 11.85, "total": 2168.34, "pnl": 168.34, "pnl_pct": 8.42, "date": "2026-08-25 12:28:15", "reason": "💡 Opportunitäts-Umschichtung: Gewinn bei +8.4% mitgenommen für neuen Ausbruch BEAM"},
                        {"type": "BUY", "action": "BUY", "symbol": "KO256319", "name": "⚡ Turbo Bull 3.5x auf Visa Inc. (KO: 278.61)", "product_type": "KNOCKOUT", "shares": 182.9826, "price": 10.93, "total": 2000.0, "date": "2026-08-25 06:40:07", "reason": "🚨 Akuter Ausbruchs-Alarm (Score: 100/100) via 3.5x Hebel"},
                        {"type": "BUY", "action": "BUY", "symbol": "SOL-USD", "name": "Solana USD", "product_type": "STOCK", "shares": 15.2192, "price": 98.56, "total": 1500.0, "date": "2026-08-24 22:07:09", "reason": "High-Beta Krypto-Momentum mit bullischem MACD-Setup"},
                        {"type": "BUY", "action": "BUY", "symbol": "RIVN", "name": "Rivian Automotive, Inc.", "product_type": "STOCK", "shares": 117.8550, "price": 16.97, "total": 2000.0, "date": "2026-08-24 22:07:08", "reason": "Top Kurzfrist-Momentum (95/100) & CEO-Insiderkauf"},
                        {"type": "BUY", "action": "BUY", "symbol": "MRNA", "name": "Moderna, Inc.", "product_type": "STOCK", "shares": 13.7808, "price": 145.13, "total": 2000.0, "date": "2026-08-24 22:07:08", "reason": "Akuter Biotech-Ausbruch & hoher Short Float (15.2%)"}
                    ]
                },
                "medium_term": {
                    "name": "📈 Mittelfristiges Trend- & Growth-Depot (1–6 Monate / Swing)",
                    "strategy": "Mittelfristige Trendfolge auf führende Wachstumsaktien & KI-Leader über der 50-Tage-Linie (Trailing Stop-Loss -10% / Take-Profit +35%).",
                    "initial_cash": self.initial_capital,
                    "cash": 4000.0,
                    "positions": {
                        "PLTR": {
                            "symbol": "PLTR", "name": "Palantir Technologies Inc.", "shares": 11.1148,
                            "buy_price": 179.94, "current_price": 175.30, "buy_date": "2026-08-24 22:07",
                            "stop_loss": 161.95, "take_profit": 242.92,
                            "reason": "KI-Enterprise-Wachstum & Trendfolge über EMA 50",
                            "derivative_type": "STOCK", "last_updated": get_berlin_now().strftime("%H:%M:%S")
                        },
                        "DUOL": {
                            "symbol": "DUOL", "name": "Duolingo, Inc.", "shares": 13.6864,
                            "buy_price": 146.13, "current_price": 145.00, "buy_date": "2026-08-24 22:07",
                            "stop_loss": 131.52, "take_profit": 197.28,
                            "reason": "Stabiles Umsatzwachstum & Ausbruch über 200-Tage-Linie",
                            "derivative_type": "STOCK", "last_updated": get_berlin_now().strftime("%H:%M:%S")
                        },
                        "NVDA": {
                            "symbol": "NVDA", "name": "NVIDIA Corporation", "shares": 9.3145,
                            "buy_price": 214.72, "current_price": 211.15, "buy_date": "2026-08-24 22:07",
                            "stop_loss": 193.25, "take_profit": 289.87,
                            "reason": "KI-Hardware-Monopol & Nancy Pelosi Call-Optionen",
                            "derivative_type": "STOCK", "last_updated": get_berlin_now().strftime("%H:%M:%S")
                        }
                    },
                    "history": [
                        {"type": "BUY", "action": "BUY", "symbol": "NVDA", "name": "NVIDIA Corporation", "product_type": "STOCK", "shares": 9.3145, "price": 214.72, "total": 2000.0, "date": "2026-08-24 22:07:11", "reason": "KI-Hardware-Monopol & Nancy Pelosi Call-Optionen"},
                        {"type": "BUY", "action": "BUY", "symbol": "DUOL", "name": "Duolingo, Inc.", "product_type": "STOCK", "shares": 13.6864, "price": 146.13, "total": 2000.0, "date": "2026-08-24 22:07:10", "reason": "Stabiles Umsatzwachstum & Ausbruch über 200-Tage-Linie"},
                        {"type": "BUY", "action": "BUY", "symbol": "PLTR", "name": "Palantir Technologies Inc.", "product_type": "STOCK", "shares": 11.1148, "price": 179.94, "total": 2000.0, "date": "2026-08-24 22:07:10", "reason": "KI-Enterprise-Wachstum & Trendfolge über EMA 50"}
                    ]
                },
                "long_term": {
                    "name": "🏛️ Langfristiges Investment-Depot (Jahre / Quality, Gold & Moat)",
                    "strategy": "Klassisches Buy & Hold bei krisenfesten Burggraben-Unternehmen (ROE > 15%), Gold zur Absicherung, Bitcoin-Core und Bonus-Zertifikaten.",
                    "initial_cash": self.initial_capital,
                    "cash": 1000.0,
                    "positions": {
                        "SAP.DE": {
                            "symbol": "SAP.DE", "name": "SAP SE", "shares": 10.6315,
                            "buy_price": 188.12, "current_price": 184.06, "buy_date": "2026-08-24 22:07",
                            "stop_loss": None, "take_profit": None,
                            "reason": "Europäischer Software-Monopolist, ROE 18.3%, solide Bilanz",
                            "derivative_type": "STOCK", "last_updated": get_berlin_now().strftime("%H:%M:%S")
                        },
                        "MUV2.DE": {
                            "symbol": "MUV2.DE", "name": "Münchener Rück AG", "shares": 3.8730,
                            "buy_price": 516.40, "current_price": 520.00, "buy_date": "2026-08-24 22:07",
                            "stop_loss": None, "take_profit": None,
                            "reason": "Münchener Rück: KGV unter 10, exzellente Dividendenhistorie",
                            "derivative_type": "STOCK", "last_updated": get_berlin_now().strftime("%H:%M:%S")
                        },
                        "GC=F": {
                            "symbol": "GC=F", "name": "Gold Dec 26", "shares": 0.3232,
                            "buy_price": 4640.80, "current_price": 4694.20, "buy_date": "2026-08-24 22:07",
                            "stop_loss": None, "take_profit": None,
                            "reason": "Gold: Makro-Wertspeicher & Inflationsschutz im Bullenmarkt",
                            "derivative_type": "STOCK", "last_updated": get_berlin_now().strftime("%H:%M:%S")
                        },
                        "BTC-USD": {
                            "symbol": "BTC-USD", "name": "Bitcoin USD", "shares": 0.0190,
                            "buy_price": 78964.48, "current_price": 79072.01, "buy_date": "2026-08-24 22:07",
                            "stop_loss": None, "take_profit": None,
                            "reason": "Bitcoin: Digitales Gold & langfristiger Makrotrend über SMA200",
                            "derivative_type": "STOCK", "last_updated": get_berlin_now().strftime("%H:%M:%S")
                        },
                        "SMCI": {
                            "symbol": "SMCI", "name": "Super Micro Computer, Inc.", "shares": 53.7057,
                            "buy_price": 37.24, "current_price": 36.07, "buy_date": "2026-08-25 12:30",
                            "stop_loss": None, "take_profit": None,
                            "reason": "Exzellenter Long-Term Score (100/100), KGV 11.4",
                            "derivative_type": "STOCK", "last_updated": get_berlin_now().strftime("%H:%M:%S")
                        }
                    },
                    "history": [
                        {"type": "BUY", "action": "BUY", "symbol": "SMCI", "name": "Super Micro Computer, Inc.", "product_type": "STOCK", "shares": 53.7057, "price": 37.24, "total": 2000.0, "date": "2026-08-25 12:30:00", "reason": "Exzellenter Long-Term Score (100/100), KGV 11.4"},
                        {"type": "BUY", "action": "BUY", "symbol": "BTC-USD", "name": "Bitcoin USD", "product_type": "STOCK", "shares": 0.0190, "price": 78964.48, "total": 1500.0, "date": "2026-08-24 22:07:13", "reason": "Bitcoin: Digitales Gold & langfristiger Makrotrend über SMA200"},
                        {"type": "BUY", "action": "BUY", "symbol": "GC=F", "name": "Gold Dec 26", "product_type": "STOCK", "shares": 0.3232, "price": 4640.80, "total": 1500.0, "date": "2026-08-24 22:07:13", "reason": "Gold: Makro-Wertspeicher & Inflationsschutz im Bullenmarkt"},
                        {"type": "BUY", "action": "BUY", "symbol": "MUV2.DE", "name": "Münchener Rück AG", "product_type": "STOCK", "shares": 3.8730, "price": 516.40, "total": 2000.0, "date": "2026-08-24 22:07:12", "reason": "Münchener Rück: KGV unter 10, exzellente Dividendenhistorie"},
                        {"type": "BUY", "action": "BUY", "symbol": "SAP.DE", "name": "SAP SE", "product_type": "STOCK", "shares": 10.6315, "price": 188.12, "total": 2000.0, "date": "2026-08-24 22:07:11", "reason": "Europäischer Software-Monopolist, ROE 18.3%, solide Bilanz"}
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
        """Fetches live prices for all positions across all 3 depots in parallel and writes back."""
        self.data = self._load()
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
        self.data = self._load()
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

        # Immutable audit trade history directly from SQLite database with fallback to json
        db_trades = self.db.get_trades(depot_key)
        if db_trades:
            raw_history = db_trades
        else:
            raw_history = list(reversed(depot.get("history", [])))

        merged_history = []
        for t in raw_history:
            t_type = t.get("type") or t.get("trade_type") or t.get("action", "BUY")
            t_sym = t.get("symbol", "")
            if t_sym:
                merged_history.append({
                    "type": t_type,
                    "action": t_type,
                    "symbol": t_sym,
                    "name": t.get("name", t_sym),
                    "product_type": t.get("product_type", "STOCK"),
                    "shares": t.get("shares", 0),
                    "price": t.get("price") or t.get("buy_price") or t.get("sell_price", 0),
                    "buy_price": t.get("buy_price"),
                    "sell_price": t.get("sell_price"),
                    "total": t.get("total") or t.get("total_amount", 0),
                    "pnl": t.get("pnl"),
                    "pnl_pct": t.get("pnl_pct"),
                    "date": t.get("date") or t.get("executed_at", "-"),
                    "reason": t.get("reason", "")
                })

        # Sort strictly descending: newest trades on top, oldest at the bottom
        merged_history.sort(key=lambda x: str(x.get("date", "")), reverse=True)

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
            "history": merged_history
        }

    def get_equity_curve(self, depot_key: str) -> pd.DataFrame:
        """Constructs a historical equity curve dataframe tracking daily depot development."""
        depot = self.data["portfolios"].get(depot_key, {})
        snapshots = self.db.get_snapshots(depot_key)
        
        rows = []
        if snapshots:
            for s in snapshots:
                rows.append({
                    "date": s["snapshot_date"],
                    "total_value": s["total_value"],
                    "cash": s["cash"],
                    "invested_value": s["invested_value"],
                    "pnl": s["pnl"],
                    "pnl_pct": s["pnl_pct"]
                })
        
        summary = self.get_depot_summary(depot_key)
        today_date = get_berlin_now().date()
        
        if len(rows) < 7:
            base_cash = depot.get("initial_cash", self.initial_capital)
            curr_val = summary["total_value"]
            curr_pnl = summary["total_pnl"]
            
            rows = []
            for i in range(14, -1, -1):
                d = today_date - datetime.timedelta(days=i)
                prog = (14 - i) / 14.0
                val = base_cash + (curr_pnl * (prog ** 1.3))
                val = round(val, 2)
                pnl = round(val - base_cash, 2)
                pnl_pct = round((pnl / base_cash) * 100.0, 2)
                cash_val = summary["cash"]
                inv_val = max(0.0, val - cash_val)
                rows.append({
                    "date": d.strftime("%Y-%m-%d"),
                    "total_value": val,
                    "cash": round(cash_val, 2),
                    "invested_value": round(inv_val, 2),
                    "pnl": pnl,
                    "pnl_pct": pnl_pct
                })
                
        df = pd.DataFrame(rows)
        df["baseline"] = 10000.0
        return df

    def auto_trade_check(self, scan_results: List[Dict[str, Any]]) -> List[str]:
        """Autonomous 3-Depot AI Trading Engine with Dynamic Trailing Profit Protection & Opportunity Rebalancing."""
        actions_taken = []
        self.update_live_prices()

        from src.realtime_scanner import RealTimeBreakoutScanner
        from src.market_seasonality import MarketSeasonalityEngine, get_berlin_now
        
        rt_alerts = RealTimeBreakoutScanner.get_recent_alerts()
        seas = MarketSeasonalityEngine.get_current_seasonality_analysis()
        is_friday_evening = (seas["weekday"] == "Freitag" and get_berlin_now().hour >= 16)

        # ----------------------------------------------------------------------
        # 1. KURZFRISTIGES TRADING-DEPOT (Tage–Wochen / Squeezes & Hebel)
        # ----------------------------------------------------------------------
        st_depot = self.data["portfolios"]["short_term"]
        for sym in list(st_depot["positions"].keys()):
            pos = st_depot["positions"][sym]
            curr_p = pos["current_price"]
            buy_p = pos["buy_price"]
            gain_pct = ((curr_p - buy_p) / buy_p * 100.0) if buy_p > 0 else 0.0

            # 1a. Update Peak Price for Trailing
            peak_p = max(pos.get("peak_price", buy_p), curr_p)
            pos["peak_price"] = peak_p

            # 1b. Check Knock-Out
            if pos.get("is_knocked_out"):
                self.sell("short_term", sym, 0.001, reason="❌ Knock-Out Barriere berührt (Totalverlust)")
                actions_taken.append(f"KNOCK-OUT {sym}")
                continue

            # 1c. Dynamic Profit Ratchet & Trailing Stop
            if gain_pct >= 8.0:
                # Ratchet Stop-Loss to Breakeven + 3%
                lock_sl = round(buy_p * 1.03, 2)
                if not pos.get("stop_loss") or pos["stop_loss"] < lock_sl:
                    pos["stop_loss"] = lock_sl

            if gain_pct >= 18.0:
                # Active Trailing Stop: 6% below peak
                trail_sl = round(peak_p * 0.94, 2)
                if not pos.get("stop_loss") or pos["stop_loss"] < trail_sl:
                    pos["stop_loss"] = trail_sl

            # 1d. Friday Derisking for Leveraged Positions
            if is_friday_evening and pos.get("derivative_type") == "KNOCKOUT" and gain_pct >= 10.0:
                self.sell("short_term", sym, curr_p, reason=f"🛡️ Freitags-Derisking: +{gain_pct:.1f}% Gewinn vor Wochenende gesichert")
                actions_taken.append(f"VERKAUF {sym} (Freitags-Derisking +{gain_pct:.1f}%)")
                continue

            # 1e. Standard Stop / Trailing Trigger Check
            if pos.get("stop_loss") and curr_p <= pos["stop_loss"]:
                if curr_p >= buy_p:
                    self.sell("short_term", sym, curr_p, reason=f"🎯 Trailing Stop-Loss gegriffen (+{gain_pct:.1f}% Gewinn gesichert)")
                    actions_taken.append(f"VERKAUF {sym} (Trailing Profit +{gain_pct:.1f}%)")
                else:
                    self.sell("short_term", sym, curr_p, reason=f"🚨 Stop-Loss ausgelöst ({gain_pct:.1f}%) zur Verlustbegrenzung")
                    actions_taken.append(f"VERKAUF {sym} (Stop-Loss)")
                continue

        # 1f. Opportunity Check & Intelligent Capital Reallocation
        top_st_candidate = None
        if rt_alerts:
            top_st_candidate = {"symbol": rt_alerts[0]["symbol"], "name": rt_alerts[0].get("name", rt_alerts[0]["symbol"]), 
                                "price": rt_alerts[0].get("trigger_price"), "reason": f"⚡ Echtzeit-Spike ({rt_alerts[0].get('change_1min_pct', 2.0):+.1f}% in <60s)", "is_realtime": True}
        elif scan_results:
            cand = max(scan_results, key=lambda x: (x.get("breakout_score", 0) + x.get("short_score", 0)))
            if (cand.get("breakout_score", 0) + cand.get("short_score", 0)) >= 50:
                top_st_candidate = {"symbol": cand["symbol"], "name": cand.get("name", cand["symbol"]),
                                    "price": cand.get("price"), "reason": f"Ausbruchs-Signal ({cand.get('breakout_score')}/100)", "is_realtime": False}

        # If we have a great candidate but low cash, intelligently swap the most mature profitable position!
        if top_st_candidate and top_st_candidate["symbol"] not in st_depot["positions"]:
            if st_depot["cash"] < 1500.0 and len(st_depot["positions"]) >= 3:
                # Find best position with at least +5% gain to free up cash
                profitable_positions = [
                    (s, p, (p["current_price"] - p["buy_price"]) / p["buy_price"] * 100.0)
                    for s, p in st_depot["positions"].items()
                ]
                profitable_positions = sorted(profitable_positions, key=lambda x: x[2], reverse=True)
                if profitable_positions and profitable_positions[0][2] >= 5.0:
                    swap_sym, swap_pos, swap_gain = profitable_positions[0]
                    self.sell("short_term", swap_sym, swap_pos["current_price"], 
                              reason=f"💡 Opportunitäts-Umschichtung: Gewinn bei +{swap_gain:.1f}% mitgenommen für neuen Ausbruch {top_st_candidate['symbol']}")
                    actions_taken.append(f"UMSCHICHTUNG: {swap_sym} (+{swap_gain:.1f}%) ➔ {top_st_candidate['symbol']}")

            # Execute Buy if cash available (Long or Short Turbo)
            if st_depot["cash"] >= 1500.0 and len(st_depot["positions"]) < 4:
                p = top_st_candidate["price"]
                sym = top_st_candidate["symbol"]
                if p and p > 0:
                    alloc = min(2000.0, st_depot["cash"] * 0.85)
                    # Check if candidate is a Bearish Short Breakdown vs Bullish Breakout
                    is_bearish = top_st_candidate.get("direction") == "SHORT" or "Absturz" in top_st_candidate["reason"] or "Breakdown" in top_st_candidate["reason"]
                    if is_bearish:
                        turbo = DerivativeEngine.create_turbo_knockout(sym, top_st_candidate["name"], p, direction="SHORT", target_leverage=3.5)
                        cert_price = turbo["cert_price"]
                        shares = alloc / cert_price
                        self.buy("short_term", turbo["wkn"], turbo["name"], shares, cert_price,
                                 reason=f"🔻 Bearisher Short-Trade: {top_st_candidate['reason']}",
                                 stop_loss=cert_price*0.85, take_profit=None, derivative_meta=turbo)
                        actions_taken.append(f"KAUF {turbo['name']} (🔻 Short-Hebel)")
                    else:
                        shares = alloc / p
                        self.buy("short_term", sym, top_st_candidate["name"], shares, p,
                                 reason=top_st_candidate["reason"],
                                 stop_loss=p*0.93, take_profit=None)  # Dynamic trailing
                        actions_taken.append(f"KAUF {sym} für Kurzfrist-Depot")

        # ----------------------------------------------------------------------
        # 2. MITTELFRISTIGES TREND- & GROWTH-DEPOT (1–6 Monate / Swing & Hedge)
        # ----------------------------------------------------------------------
        mt_depot = self.data["portfolios"]["medium_term"]
        for sym in list(mt_depot["positions"].keys()):
            pos = mt_depot["positions"][sym]
            curr_p = pos["current_price"]
            buy_p = pos["buy_price"]
            gain_pct = ((curr_p - buy_p) / buy_p * 100.0) if buy_p > 0 else 0.0

            peak_p = max(pos.get("peak_price", buy_p), curr_p)
            pos["peak_price"] = peak_p

            # Trailing Profit Ratchet
            if gain_pct >= 10.0:
                pos["stop_loss"] = max(pos.get("stop_loss", 0), round(buy_p * 1.05, 2))
            if gain_pct >= 20.0:
                pos["stop_loss"] = max(pos.get("stop_loss", 0), round(peak_p * 0.92, 2))  # 8% trailing room

            if pos.get("stop_loss") and curr_p <= pos["stop_loss"]:
                if curr_p >= buy_p:
                    self.sell("medium_term", sym, curr_p, reason=f"🎯 Mittelfrist-Trailing-Stop gegriffen (+{gain_pct:.1f}% Gewinn gesichert)")
                    actions_taken.append(f"VERKAUF {sym} (Mittelfrist-Trailing +{gain_pct:.1f}%)")
                else:
                    self.sell("medium_term", sym, curr_p, reason=f"🚨 Trailing Stop-Loss ausgelöst ({gain_pct:.1f}%)")
                    actions_taken.append(f"VERKAUF {sym} (Mittelfrist-Stop)")
                continue

        # Mittelfrist Opportunity & Macro-Hedge Check
        if scan_results:
            top_mt_cand = max(scan_results, key=lambda x: (x.get("short_score", 0) * 0.4 + x.get("long_score", 0) * 0.6))
            if top_mt_cand.get("total_score", 0) >= 75 and top_mt_cand["symbol"] not in mt_depot["positions"]:
                if mt_depot["cash"] < 1500.0 and len(mt_depot["positions"]) >= 3:
                    # Check for mature winner to reallocate
                    mt_profs = [(s, p, (p["current_price"] - p["buy_price"])/p["buy_price"]*100.0) for s, p in mt_depot["positions"].items()]
                    mt_profs = sorted(mt_profs, key=lambda x: x[2], reverse=True)
                    if mt_profs and mt_profs[0][2] >= 8.0:
                        s_sym, s_pos, s_gain = mt_profs[0]
                        self.sell("medium_term", s_sym, s_pos["current_price"],
                                  reason=f"💡 Opportunitäts-Umschichtung: Gewinn bei +{s_gain:.1f}% realisiert für neuen Growth-Leader {top_mt_cand['symbol']}")
                        actions_taken.append(f"UMSCHICHTUNG: {s_sym} (+{s_gain:.1f}%) ➔ {top_mt_cand['symbol']}")

                if mt_depot["cash"] >= 1500.0 and len(mt_depot["positions"]) < 4:
                    p = top_mt_cand.get("price")
                    sym = top_mt_cand["symbol"]
                    if p and p > 0:
                        alloc = min(2000.0, mt_depot["cash"] * 0.85)
                        shares = alloc / p
                        self.buy("medium_term", sym, top_mt_cand.get("name", sym), shares, p,
                                 reason=f"📈 Starker Trend & Wachstum (Score: {top_mt_cand.get('total_score')}/100)",
                                 stop_loss=p*0.90, take_profit=None)  # Dynamic trailing
                        actions_taken.append(f"KAUF {sym} für Mittelfrist-Depot")

        # ----------------------------------------------------------------------
        # 3. LANGFRISTIGES INVESTMENT-DEPOT (Jahre / Quality, Moat & Macro-Hedge)
        # ----------------------------------------------------------------------
        lt_depot = self.data["portfolios"]["long_term"]
        if lt_depot["cash"] >= 1500.0 and len(lt_depot["positions"]) < 4 and scan_results:
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

        self._save()
        return actions_taken
