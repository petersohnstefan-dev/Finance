import json
import os
import datetime
from typing import Dict, Any, List, Optional
import yfinance as yf
from src.db import PortfolioDB
from src.derivatives import DerivativeEngine

PORTFOLIO_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "portfolios.json")

class PortfolioManager:
    """Manages multi-asset paper trading portfolios (Stocks, Crypto, Gold, Knock-Outs, Factor & Bonus Certificates)."""

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

        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        initial_data = {
            "created_at": now_str,
            "currency": "EUR",
            "portfolios": {
                "short_term": {
                    "name": "⚡ Kurz-/Mittelfristiges Trading-Depot (Momentum, Hebel & Squeeze)",
                    "strategy": "Aktives Swing-Trading auf Momentum, Ausbrüche & Squeezes via Aktien, Krypto, Knock-Out & Faktor-Zertifikate (Stop-Loss -7% / Take-Profit +20%).",
                    "initial_cash": self.initial_capital,
                    "cash": self.initial_capital,
                    "positions": {},
                    "history": []
                },
                "long_term": {
                    "name": "🏛️ Langfristiges Investment-Depot (Quality, Gold & Bonus-Zertifikate)",
                    "strategy": "Langfristiges Buy & Hold bei soliden Burggraben-Unternehmen (ROE > 15%), Gold, Bitcoin und Bonus-Zertifikaten mit Sicherheitspuffer.",
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
        """Fetches fresh live prices for underlying assets and recalculates derivative values."""
        underlying_prices = {}
        all_symbols = set()
        
        for depot in self.data["portfolios"].values():
            for sym, pos in depot["positions"].items():
                und_sym = pos.get("underlying_symbol", sym)
                all_symbols.add(und_sym)

        for sym in all_symbols:
            try:
                t = yf.Ticker(sym)
                hist = t.history(period="2d")
                if not hist.empty:
                    underlying_prices[sym] = round(hist['Close'].iloc[-1], 2)
            except Exception:
                pass

        for depot in self.data["portfolios"].values():
            for sym, pos in list(depot["positions"].items()):
                und_sym = pos.get("underlying_symbol", sym)
                curr_und_p = underlying_prices.get(und_sym)
                if curr_und_p:
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
        """Autonomous AI Trading Engine: manages stops, targets, breakouts, knockouts, and factor certificates."""
        actions_taken = []
        self.update_live_prices()

        # 1. Check Short-Term Trading Portfolio
        st_depot = self.data["portfolios"]["short_term"]
        for sym in list(st_depot["positions"].keys()):
            pos = st_depot["positions"][sym]
            curr_p = pos["current_price"]
            
            # Check Knockout event
            if pos.get("is_knocked_out"):
                self.sell("short_term", sym, 0.001, reason="❌ Knock-Out Barriere berührt (Totalverlust der Hebelposition)")
                actions_taken.append(f"KNOCK-OUT {sym}")
                continue

            # Stop Loss Check
            if pos.get("stop_loss") and curr_p <= pos["stop_loss"]:
                self.sell("short_term", sym, curr_p, reason="🚨 Stop-Loss ausgelöst zur Verlustbegrenzung")
                actions_taken.append(f"VERKAUF {sym} (Stop-Loss bei {curr_p:.2f} €)")
            # Take Profit Check
            elif pos.get("take_profit") and curr_p >= pos["take_profit"]:
                self.sell("short_term", sym, curr_p, reason="🎯 Take-Profit erreicht - Gewinnsicherung")
                actions_taken.append(f"VERKAUF {sym} (Take-Profit bei {curr_p:.2f} €)")

        # Buy top setups if cash is available
        if st_depot["cash"] >= 1200.0 and len(st_depot["positions"]) < 5:
            # Look for highest breakout / momentum scores
            candidates = sorted(scan_results, key=lambda x: (x.get("breakout_score", 0) + x.get("short_score", 0)), reverse=True)
            for cand in candidates:
                sym = cand["symbol"]
                p = cand.get("price")
                if sym not in st_depot["positions"] and p and p > 0:
                    alloc = min(1800.0, st_depot["cash"] * 0.9)
                    
                    # If high breakout score, use Turbo Knock-Out Bull (3.5x leverage)!
                    if cand.get("breakout_score", 0) >= 50:
                        turbo = DerivativeEngine.create_turbo_knockout(sym, cand.get("name", sym), p, direction="LONG", target_leverage=3.5)
                        cert_price = turbo["cert_price"]
                        shares = alloc / cert_price
                        sl = cert_price * 0.85  # -15% on certificate
                        tp = cert_price * 1.40  # +40% Take Profit
                        self.buy("short_term", turbo["wkn"], turbo["name"], shares, cert_price,
                                 reason=f"🚨 Akuter Ausbruchs-Alarm ({cand.get('breakout_score')}/100) - Hebel {turbo['leverage']}x",
                                 stop_loss=sl, take_profit=tp, derivative_meta=turbo)
                        actions_taken.append(f"KAUF {turbo['name']} ({shares:.1f} Stk.)")
                    else:
                        shares = alloc / p
                        sl = p * 0.93
                        tp = p * 1.20
                        self.buy("short_term", sym, cand.get("name", sym), shares, p,
                                 reason=f"Starkes Momentum & Trendfolge ({cand.get('short_score')}/100)",
                                 stop_loss=sl, take_profit=tp)
                        actions_taken.append(f"KAUF {sym} ({shares:.2f} Stk.)")
                    break

        # 2. Check Long-Term Investment Portfolio
        lt_depot = self.data["portfolios"]["long_term"]
        if lt_depot["cash"] >= 1200.0 and len(lt_depot["positions"]) < 5:
            candidates = sorted(scan_results, key=lambda x: x.get("long_score", 0), reverse=True)
            for cand in candidates:
                sym = cand["symbol"]
                p = cand.get("price")
                if sym not in lt_depot["positions"] and p and p > 0:
                    alloc = min(1800.0, lt_depot["cash"] * 0.9)
                    
                    # Option: Create Bonus Certificate for high quality stocks
                    if cand.get("long_score", 0) >= 90:
                        bonus = DerivativeEngine.create_bonus_certificate(sym, cand.get("name", sym), p, barrier_pct=25.0, bonus_pct=14.0)
                        shares = alloc / p
                        self.buy("long_term", bonus["wkn"], bonus["name"], shares, p,
                                 reason=f"🛡️ Bonus-Zertifikat mit 25% Sicherheitspuffer & +14% Bonuschance (Score {cand.get('long_score')}/100)",
                                 derivative_meta=bonus)
                        actions_taken.append(f"KAUF {bonus['name']}")
                    else:
                        shares = alloc / p
                        self.buy("long_term", sym, cand.get("name", sym), shares, p,
                                 reason=f"Qualitäts-Compounder ({cand.get('long_score')}/100)")
                        actions_taken.append(f"KAUF {sym} ({shares:.2f} Stk.)")
                    break

        return actions_taken
