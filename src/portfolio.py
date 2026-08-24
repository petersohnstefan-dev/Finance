import json
import os
import datetime
from typing import Dict, Any, List, Optional
import yfinance as yf
from src.db import PortfolioDB

PORTFOLIO_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "portfolios.json")

class PortfolioManager:
    """Manages virtual paper trading portfolios with persistent dual-storage (SQLite + JSON)."""

    def __init__(self, initial_capital_per_depot: float = 10000.0):
        self.initial_capital = initial_capital_per_depot
        self.db = PortfolioDB()
        self.data = self._load()

    def _load(self) -> Dict[str, Any]:
        """Loads existing portfolio state without resetting."""
        if os.path.exists(PORTFOLIO_FILE):
            try:
                with open(PORTFOLIO_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if "portfolios" in data and "short_term" in data["portfolios"]:
                        return data
            except Exception:
                pass

        # Default fallback only if file is completely missing
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        initial_data = {
            "created_at": now_str,
            "currency": "EUR",
            "portfolios": {
                "short_term": {
                    "name": "⚡ Kurz-/Mittelfristiges Trading-Depot (Momentum & Squeeze)",
                    "strategy": "Aktives Swing-Trading, Momentum-Ausbrüche, Squeeze-Setups mit Stop-Loss (-7%) und Take-Profit (+20%).",
                    "initial_cash": self.initial_capital,
                    "cash": self.initial_capital,
                    "positions": {},
                    "history": []
                },
                "long_term": {
                    "name": "🏛️ Langfristiges Investment-Depot (Quality & Value)",
                    "strategy": "Kauf solider Qualitätsunternehmen mit starkem Burggraben (ROE > 15%), gesunder Bilanz und Gold/Krypto-Core.",
                    "initial_cash": self.initial_capital,
                    "cash": self.initial_capital,
                    "positions": {},
                    "history": []
                }
            }
        }
        self._save(initial_data)
        return initial_data

    def _save(self, data: Optional[Dict[str, Any]] = None):
        if data is None:
            data = self.data
        os.makedirs(os.path.dirname(PORTFOLIO_FILE), exist_ok=True)
        with open(PORTFOLIO_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def buy(self, depot_key: str, symbol: str, name: str, shares: float, price: float, 
            reason: str = "", stop_loss: Optional[float] = None, take_profit: Optional[float] = None) -> bool:
        """Executes a buy order in the specified portfolio and logs to SQLite + JSON."""
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

        if symbol in depot["positions"]:
            pos = depot["positions"][symbol]
            total_shares = pos["shares"] + shares
            avg_price = ((pos["shares"] * pos["buy_price"]) + cost) / total_shares
            pos["shares"] = round(total_shares, 4)
            pos["buy_price"] = round(avg_price, 2)
            pos["current_price"] = round(price, 2)
        else:
            depot["positions"][symbol] = {
                "symbol": symbol,
                "name": name,
                "shares": round(shares, 4),
                "buy_price": round(price, 2),
                "current_price": round(price, 2),
                "buy_date": now_str,
                "stop_loss": round(stop_loss, 2) if stop_loss else None,
                "take_profit": round(take_profit, 2) if take_profit else None,
                "reason": reason
            }

        trade_record = {
            "type": "BUY",
            "symbol": symbol,
            "name": name,
            "shares": round(shares, 4),
            "price": round(price, 2),
            "total": round(cost, 2),
            "date": now_str,
            "reason": reason
        }
        depot["history"].append(trade_record)

        # Mirror to SQLite
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
        pnl_pct = ((price - pos["buy_price"]) / pos["buy_price"]) * 100.0

        depot["cash"] += revenue
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

        trade_record = {
            "type": "SELL",
            "symbol": symbol,
            "name": pos["name"],
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

        # Mirror to SQLite
        try:
            self.db.record_trade(depot_key, "SELL", symbol, pos["name"], shares, revenue, 
                                 pos["buy_price"], sell_price=price, pnl=pnl, pnl_pct=pnl_pct, reason=reason)
        except Exception:
            pass

        del depot["positions"][symbol]
        self._save()
        return True

    def update_live_prices(self):
        """Fetches fresh live market prices for all open positions."""
        all_symbols = set()
        for depot in self.data["portfolios"].values():
            all_symbols.update(depot["positions"].keys())

        if not all_symbols:
            return

        for sym in all_symbols:
            try:
                t = yf.Ticker(sym)
                hist = t.history(period="2d")
                if not hist.empty:
                    curr_p = hist['Close'].iloc[-1]
                    for depot in self.data["portfolios"].values():
                        if sym in depot["positions"]:
                            depot["positions"][sym]["current_price"] = round(curr_p, 2)
            except Exception:
                pass
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
                "shares": shares,
                "buy_price": buy_p,
                "current_price": curr_p,
                "value": round(pos_val, 2),
                "pnl": round(pnl, 2),
                "pnl_pct": round(pnl_pct, 2),
                "stop_loss": pos.get("stop_loss"),
                "take_profit": pos.get("take_profit"),
                "buy_date": pos.get("buy_date"),
                "reason": pos.get("reason", "")
            })

        total_value = cash + invested_value
        total_pnl = total_value - init_cash
        total_pnl_pct = (total_pnl / init_cash) * 100.0

        # Record daily snapshot to SQLite
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
        """Continuous automated trader: checks stop loss, take profit, and opens positions only if cash available."""
        actions_taken = []
        self.update_live_prices()

        # 1. Check Short-Term Trading Portfolio
        st_depot = self.data["portfolios"]["short_term"]
        for sym in list(st_depot["positions"].keys()):
            pos = st_depot["positions"][sym]
            curr_p = pos["current_price"]
            # Stop Loss Check
            if pos.get("stop_loss") and curr_p <= pos["stop_loss"]:
                self.sell("short_term", sym, curr_p, reason="🚨 Stop-Loss ausgelöst (-7%) zur Verlustbegrenzung")
                actions_taken.append(f"VERKAUF {sym} (Stop-Loss bei {curr_p:.2f} €)")
            # Take Profit Check
            elif pos.get("take_profit") and curr_p >= pos["take_profit"]:
                self.sell("short_term", sym, curr_p, reason="🎯 Take-Profit erreicht (+20%) - Gewinnsicherung")
                actions_taken.append(f"VERKAUF {sym} (Take-Profit bei {curr_p:.2f} €)")

        # Only buy if free cash >= 1500 EUR and fewer than 5 positions
        if st_depot["cash"] >= 1500.0 and len(st_depot["positions"]) < 5:
            candidates = sorted(scan_results, key=lambda x: (x.get("short_score", 0) + x.get("breakout_score", 0)), reverse=True)
            for cand in candidates:
                sym = cand["symbol"]
                p = cand.get("price")
                if sym not in st_depot["positions"] and p and p > 0:
                    alloc = min(1800.0, st_depot["cash"] * 0.9)
                    shares = alloc / p
                    sl = p * 0.93  # -7% Stop Loss
                    tp = p * 1.20  # +20% Take Profit
                    self.buy("short_term", sym, cand.get("name", sym), shares, p, 
                             reason=f"Top Momentum & Breakout Score ({cand.get('short_score')}/100)",
                             stop_loss=sl, take_profit=tp)
                    actions_taken.append(f"KAUF {sym} ({shares:.2f} Stk. zu {p:.2f} €)")
                    break

        # 2. Check Long-Term Investment Portfolio
        lt_depot = self.data["portfolios"]["long_term"]
        if lt_depot["cash"] >= 1500.0 and len(lt_depot["positions"]) < 5:
            candidates = sorted(scan_results, key=lambda x: x.get("long_score", 0), reverse=True)
            for cand in candidates:
                sym = cand["symbol"]
                p = cand.get("price")
                if sym not in lt_depot["positions"] and p and p > 0:
                    alloc = min(1800.0, lt_depot["cash"] * 0.9)
                    shares = alloc / p
                    self.buy("long_term", sym, cand.get("name", sym), shares, p, 
                             reason=f"Exzellenter Long-Term Score ({cand.get('long_score')}/100)")
                    actions_taken.append(f"KAUF {sym} ({shares:.2f} Stk. zu {p:.2f} € für Langfrist-Depot)")
                    break

        return actions_taken
