import json
import os
import time
import datetime
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
import yfinance as yf
from src.db import PortfolioDB
from src.derivatives import DerivativeEngine
from src.deep_intelligence import DeepIntelligenceHub
from src.wkn_mapping import get_wkn, get_wkn_display
from src.tribunal import AITribunalManager

PORTFOLIO_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "portfolios.json")

from zoneinfo import ZoneInfo
BERLIN_TZ = ZoneInfo("Europe/Berlin")

def get_berlin_now() -> datetime.datetime:
    try:
        return datetime.datetime.now(BERLIN_TZ)
    except Exception:
        return datetime.datetime.utcnow() + datetime.timedelta(hours=2)

ENTRY_DIAG_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "entry_diagnostics.json")


class PortfolioManager:
    """Manages 3 distinct paper trading portfolios (Short-Term, Medium-Term, Long-Term)."""

    def __init__(self, initial_capital_per_depot: float = 10000.0):
        self.initial_capital = initial_capital_per_depot
        self.db = PortfolioDB()
        self.deep_intel = DeepIntelligenceHub()
        self.tribunal = AITribunalManager()
        self._last_price_update = 0.0
        self._atr_cache: Dict[str, float] = {}
        self.data = self._load()
        self.strategy = self._load_strategy()

    def _tribunal_approved_buy(self, depot_id: str, sym: str, name: str, shares: float, price: float, reason: str, stop_loss: float, take_profit: float, derivative_meta=None) -> Tuple[bool, str]:
        # Cooldown check
        if "cooldowns" not in self.data:
            self.data["cooldowns"] = {}
            
        cooldown_key = f"{depot_id}_{sym}"
        now = get_berlin_now()
        
        if cooldown_key in self.data["cooldowns"]:
            try:
                cd_time = datetime.datetime.fromisoformat(self.data["cooldowns"][cooldown_key])
                if now < cd_time:
                    return False, f"VETO (Tribunal Cooldown aktiv bis {cd_time.strftime('%H:%M')})"
            except:
                pass

        candidate = {"symbol": sym, "name": name, "price": price, "reason": reason}
        depot = self.data["portfolios"][depot_id]

        # Hand the tribunal what was actually measured. It used to receive only the
        # scanner's headline string and consequently argued from the model's own
        # recollection of the ticker - the logs show it reasoning about a "Dark Pool"
        # figure that was a modulo artefact.
        underlying = (derivative_meta or {}).get("underlying_symbol", sym)
        try:
            intel = self.deep_intel.get_asset_360_intelligence(underlying)
        except Exception:
            intel = None
        scan_row = None
        try:
            scan_file = os.path.join(os.path.dirname(__file__), "..", "data",
                                     "market_scan_results.json")
            with open(scan_file, "r", encoding="utf-8") as fh:
                scan_row = next((r for r in json.load(fh).get("data", [])
                                 if r.get("symbol") == underlying), None)
        except Exception:
            scan_row = None

        evidence = self.tribunal.build_evidence(
            candidate, intel, depot_id, depot, scan_row=scan_row, stop_loss=stop_loss)

        action, judge_reasoning, debate_log = self.tribunal.decide_trade(
            depot_id, candidate, depot["cash"], evidence=evidence)
        
        if action == "BUY":
            full_reason = f"{reason} | ⚖️ Tribunal (BUY): {judge_reasoning}"
            self.buy(depot_id, sym, name, shares, price, reason=full_reason, stop_loss=stop_loss, take_profit=take_profit, derivative_meta=derivative_meta)
            # Remove cooldown if it existed
            if cooldown_key in self.data["cooldowns"]:
                del self.data["cooldowns"][cooldown_key]
                self._save()
            return True, full_reason
        else:
            # Set a 4-hour cooldown for this symbol to prevent API spam
            cd_expiry = now + datetime.timedelta(hours=4)
            self.data["cooldowns"][cooldown_key] = cd_expiry.isoformat()
            self._save()
            return False, f"VETO vom Tribunal: {judge_reasoning}"

    def _load_strategy(self) -> Dict[str, Any]:
        strat_file = os.path.join(os.path.dirname(__file__), "..", "data", "strategy.json")
        default_strat = {
            "daytrade_max_leverage": 10.0,
            "daytrade_stop_loss_pct": 0.15,
            "daytrade_max_risk_per_trade_pct": 0.02,
            "daytrade_min_risk_reward_ratio": 2.0,
            "daytrade_max_daily_loss_pct": 0.05,
            "daytrade_max_daily_trades": 5,
            "daytrade_max_correlated_positions": 2,
            "daytrade_eod_close_all": True,
            "daytrade_eod_time_hour": 21,
            "daytrade_min_entry_score": 65,
            "daytrade_max_candidates_scored": 8,
            "daytrade_trailing_breakeven_pct": 0.03,
            "daytrade_trailing_lock_pct": 0.05,
            "daytrade_trailing_aggressive_pct": 0.10,
            "daytrade_vix_defensive_threshold": 25.0,
            "daytrade_vix_pause_threshold": 35.0,
            "short_term_stop_loss_pct": 0.15,
            "short_term_stop_atr_mult": 2.5,
            "short_term_trail_atr_mult": 2.5,
            "short_term_breakeven_trigger_atr": 1.0,
            "short_term_stop_min_pct": 0.06,
            "short_term_stop_max_pct": 0.25,
            "short_term_max_risk_per_trade_pct": 0.015,
            "short_term_min_alpha_score": 55,
            "short_term_min_spike_pct": 1.5,
            "short_term_max_candidates_scored": 12,
            "carry_unwind_usdjpy_threshold": 145.0,
            "medium_term_hedge_vix_threshold": 28.0,
            "medium_term_hedge_exit_vix": 22.0,
            "medium_term_hedge_pct": 0.20,
            "medium_term_hedge_leverage": 3.0,
            "medium_term_hedge_symbol": "SPY",
            "long_term_min_score": 75,
            "long_term_max_positions": 6,
            "long_term_min_cash": 1500.0,
            "medium_term_min_score": 75,
            "medium_term_max_positions": 4,
            "min_data_quality_for_thesis_exit": 0.45
        }
        if os.path.exists(strat_file):
            try:
                with open(strat_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    default_strat.update(data)
            except:
                pass
        return default_strat

    def _get_market_regime(self) -> str:
        """Determines if the market is Risk-On (Bull) or Risk-Off (Bear) using SPY 200 SMA."""
        try:
            spy = yf.Ticker("SPY").history(period="1y")
            if len(spy) > 200:
                sma_200 = spy['Close'].rolling(window=200).mean().iloc[-1]
                current = spy['Close'].iloc[-1]
                if current < sma_200:
                    return "BEAR"
            return "BULL"
        except:
            return "BULL"

    def _calculate_volatility_factor(self, symbol: str) -> float:
        """Calculates a position sizing factor based on 30-day volatility (ATR equivalent)."""
        try:
            if "-USD" in symbol:
                return 0.5  # Fixed lower sizing for crypto
            if "KO" in symbol:
                return 0.4  # Knock-outs get smaller sizing
            hist = yf.Ticker(symbol).history(period="1mo")
            if len(hist) < 10:
                return 1.0
            daily_returns = hist['Close'].pct_change().dropna()
            vol = daily_returns.std() * (252 ** 0.5)  # Annualized volatility
            
            # Base benchmark is SPY ~15-20% vol.
            if vol < 0.10:
                return 1.5  # Very safe, larger size
            elif vol > 0.40:
                return 0.6  # High vol, smaller size
            elif vol > 0.60:
                return 0.3  # Extreme vol
            return 1.0
        except:
            return 1.0

    # ------------------------------------------------------------------
    # PROFESSIONAL DAYTRADING ENGINE — Helper Methods
    # ------------------------------------------------------------------

    def _get_vix(self) -> float:
        """Fetches the current VIX (CBOE Volatility Index) to gauge market fear."""
        try:
            vix = yf.Ticker("^VIX").history(period="1d")
            if not vix.empty:
                return float(vix['Close'].iloc[-1])
        except:
            pass
        return 18.0  # Default: normal market conditions

    def _get_trading_mode(self) -> str:
        """Determines trading mode based on VIX: NORMAL / DEFENSIVE / PAUSE."""
        vix = self._get_vix()
        pause_threshold = self.strategy.get("daytrade_vix_pause_threshold", 35.0)
        defensive_threshold = self.strategy.get("daytrade_vix_defensive_threshold", 25.0)
        if vix >= pause_threshold:
            return "PAUSE"       # No trading — market too chaotic
        elif vix >= defensive_threshold:
            return "DEFENSIVE"   # Half position size, only A+ setups
        return "NORMAL"

    def _get_sector(self, symbol: str) -> str:
        """Returns the sector/asset class for correlation checking."""
        # Fast lookup for known tickers
        SECTOR_MAP = {
            'NVDA': 'tech_chips', 'AMD': 'tech_chips', 'INTC': 'tech_chips', 'AVGO': 'tech_chips', 'SMCI': 'tech_chips',
            'AAPL': 'tech_mega', 'MSFT': 'tech_mega', 'GOOGL': 'tech_mega', 'META': 'tech_mega', 'AMZN': 'tech_mega',
            'TSLA': 'ev', 'RIVN': 'ev', 'NIO': 'ev', 'LCID': 'ev',
            'BTC-USD': 'crypto', 'ETH-USD': 'crypto', 'SOL-USD': 'crypto', 'DOGE-USD': 'crypto',
            'MRNA': 'biotech', 'BNTX': 'biotech', 'NVAX': 'biotech', 'VKTX': 'biotech', 'BEAM': 'biotech',
            'GC=F': 'commodities', '4GLD.DE': 'commodities', 'SI=F': 'commodities',
            'JPM': 'finance', 'GS': 'finance', 'BAC': 'finance',
        }
        if symbol in SECTOR_MAP:
            return SECTOR_MAP[symbol]
        if '-USD' in symbol:
            return 'crypto'
        if 'KO' in symbol and len(symbol) > 4:
            return 'derivative'  # KO-Zertifikate
        try:
            info = yf.Ticker(symbol).info
            return info.get('sector', 'unknown').lower().replace(' ', '_')
        except:
            return 'unknown'

    def _check_correlation(self, symbol: str, depot: Dict) -> bool:
        """Returns True if the position passes the correlation check (max N in same sector)."""
        max_correlated = self.strategy.get("daytrade_max_correlated_positions", 2)
        new_sector = self._get_sector(symbol)
        if new_sector in ('unknown', 'derivative'):
            return True  # Can't determine sector, allow
        same_sector_count = 0
        for s, p in depot.get("positions", {}).items():
            underlying = p.get("underlying_symbol", s)
            if self._get_sector(underlying) == new_sector:
                same_sector_count += 1
        return same_sector_count < max_correlated

    def _check_daily_loss_limit(self, depot_value: float) -> bool:
        """Returns True if the daily loss limit has NOT been reached (trading allowed)."""
        max_loss_pct = self.strategy.get("daytrade_max_daily_loss_pct", 0.05)
        max_loss = depot_value * max_loss_pct
        today_pnl = self.db.get_today_pnl("day_trading")
        return today_pnl > -max_loss  # True = can still trade

    def _check_daily_trade_count(self) -> bool:
        """Returns True if max daily trades not reached."""
        max_trades = self.strategy.get("daytrade_max_daily_trades", 5)
        today_count = self.db.get_today_trade_count("day_trading")
        return today_count < max_trades

    def _record_entry_diagnostic(self, depot_id: str, scores: List[float], threshold: float,
                                 entered: bool, blocked: str = "") -> None:
        """Per-day entry-gate telemetry. Without it the journal cannot tell 'no signal
        today' apart from 'the gate is set so high that nothing can ever pass it' -
        the exact failure that kept the daytrader idle for two trading days."""
        try:
            day = get_berlin_now().strftime("%Y-%m-%d")
            data = {}
            if os.path.exists(ENTRY_DIAG_FILE):
                with open(ENTRY_DIAG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)

            slot = data.setdefault(day, {}).setdefault(depot_id, {
                "runs": 0, "scored": 0, "entries": 0, "best_score": None,
                "above_threshold": 0, "threshold": threshold, "blocks": {}
            })
            slot["runs"] += 1
            slot["threshold"] = threshold
            slot["scored"] += len(scores)
            if scores:
                best = round(max(scores), 1)
                slot["best_score"] = best if slot["best_score"] is None else max(slot["best_score"], best)
                slot["above_threshold"] += sum(1 for s in scores if s >= threshold)
            if entered:
                slot["entries"] += 1
            if blocked:
                slot["blocks"][blocked] = slot["blocks"].get(blocked, 0) + 1

            # Keep the file small - the journal only ever looks back a week
            for old_day in sorted(data.keys())[:-14]:
                data.pop(old_day, None)

            os.makedirs(os.path.dirname(ENTRY_DIAG_FILE), exist_ok=True)
            with open(ENTRY_DIAG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass  # Telemetry must never break trading

    def _get_atr_pct(self, symbol: str) -> float:
        """14-day ATR as a fraction of price. Cached per instance because the bot
        re-runs every 5 minutes and every position would otherwise refetch."""
        if symbol in self._atr_cache:
            return self._atr_cache[symbol]
        atr_pct = 0.0
        try:
            hist = yf.Ticker(symbol).history(period="2mo")
            if len(hist) >= 15:
                atr = float(hist['High'].sub(hist['Low']).rolling(14).mean().iloc[-1])
                price = float(hist['Close'].iloc[-1])
                if price > 0 and atr > 0:
                    atr_pct = atr / price
        except Exception:
            pass
        self._atr_cache[symbol] = atr_pct
        return atr_pct

    def _position_atr_pct(self, sym: str, pos: Dict) -> float:
        """ATR% as it applies to the traded instrument. A knock-out moves with the
        underlying's ATR amplified by its leverage."""
        underlying = pos.get("underlying_symbol", sym)
        atr_pct = self._get_atr_pct(underlying)
        if atr_pct <= 0:
            return 0.0
        try:
            lev = max(float(pos.get("leverage", 1.0) or 1.0), 1.0)
        except (TypeError, ValueError):
            lev = 1.0
        return atr_pct * lev

    def _short_term_stop_pct(self, symbol: str) -> float:
        """Initial stop distance for the short-term depot, scaled to the symbol's own
        volatility instead of a flat percentage. short_term_stop_loss_pct is the
        fallback for symbols where no ATR can be read."""
        atr_pct = self._get_atr_pct(symbol)
        if atr_pct > 0:
            sl_pct = self.strategy.get("short_term_stop_atr_mult", 2.5) * atr_pct
        else:
            sl_pct = self.strategy.get("short_term_stop_loss_pct", 0.15)
        lo = self.strategy.get("short_term_stop_min_pct", 0.06)
        hi = self.strategy.get("short_term_stop_max_pct", 0.25)
        return min(max(sl_pct, lo), hi)

    def _choose_leverage(self, spike: float) -> float:
        """Maps an intraday spike to the certificate leverage. Shared by scoring and entry
        so the RRR estimate uses the same stop distance the trade will actually get."""
        max_lev = self.strategy.get("daytrade_max_leverage", 10.0)
        if spike >= 2.0:
            return min(10.0, max_lev)
        if spike >= 1.2:
            return min(7.0, max_lev)
        if spike >= 0.8:
            return min(5.0, max_lev)
        if spike >= 0.5:
            return min(3.0, max_lev)
        return 1.0  # Direct stock purchase for weak signals

    def _calculate_entry_quality(self, alert: Dict, sym: str) -> int:
        """Calculates a multi-factor entry quality score (0-100) for professional daytrading."""
        score = 0

        # 1. Volume Confirmation (25 points)
        vol_ratio = alert.get('vol_ratio', 1.0)
        if vol_ratio >= 3.0:
            score += 25
        elif vol_ratio >= 1.8:
            score += 15
        elif vol_ratio >= 1.2:
            score += 5

        # 2. Trend Conformity (20 points) — only trade WITH the trend
        try:
            hist = yf.Ticker(sym).history(period="3mo")
            if len(hist) >= 50:
                ema_50 = hist['Close'].ewm(span=50).mean().iloc[-1]
                price = hist['Close'].iloc[-1]
                direction = alert.get("direction", "LONG")
                if direction == "LONG" and price > ema_50:
                    score += 20  # Long in uptrend
                elif direction == "SHORT" and price < ema_50:
                    score += 20  # Short in downtrend
                elif direction == "LONG" and price > hist['Close'].ewm(span=20).mean().iloc[-1]:
                    score += 10  # At least above EMA20
        except:
            score += 5  # Benefit of the doubt

        # 3. Spike Strength (20 points) — stronger spike = higher conviction
        spike = alert.get('change_1min_pct', 0)
        if spike >= 2.0:
            score += 20
        elif spike >= 1.2:
            score += 15
        elif spike >= 0.8:
            score += 10
        elif spike >= 0.5:
            score += 5

        # 4. RRR Potential (20 points) — estimated from ATR
        try:
            hist = yf.Ticker(sym).history(period="1mo")
            if len(hist) >= 14:
                atr = hist['High'].sub(hist['Low']).rolling(14).mean().iloc[-1]
                price = alert.get("trigger_price", hist['Close'].iloc[-1])
                # sl_pct is the stop on the leveraged certificate. On the underlying
                # the same stop sits sl_pct/leverage away, which is what the ATR
                # reward has to be compared against.
                sl_pct = self.strategy.get("daytrade_stop_loss_pct", 0.15)
                lev = self._choose_leverage(alert.get('change_1min_pct', 0))
                risk = price * sl_pct / max(lev, 1.0)
                reward = atr * 2  # Expect 2x ATR move on breakout
                if risk > 0 and reward / risk >= 2.0:
                    score += 20
                elif risk > 0 and reward / risk >= 1.5:
                    score += 10
        except:
            pass

        # 5. Market Context (15 points) — VIX calm + no macro event
        trading_mode = self._get_trading_mode()
        if trading_mode == "NORMAL":
            score += 15
        elif trading_mode == "DEFENSIVE":
            score += 5
        # PAUSE mode: 0 points (but entry is blocked elsewhere anyway)

        return min(100, score)

    def _calculate_risk_based_position_size(self, depot_value: float, entry_price: float,
                                             stop_loss_pct: float, trading_mode: str,
                                             is_bearish: bool, regime: str) -> float:
        """Calculates position size based on max 2% risk per trade (Kelly-inspired)."""
        max_risk_pct = self.strategy.get("daytrade_max_risk_per_trade_pct", 0.02)
        risk_amount = depot_value * max_risk_pct  # e.g. 10000 * 0.02 = 200€

        # In DEFENSIVE mode: halve the risk
        if trading_mode == "DEFENSIVE":
            risk_amount *= 0.5

        # In BEAR market for LONG trades: halve again
        if regime == "BEAR" and not is_bearish:
            risk_amount *= 0.5

        # Position size = risk / stop-loss distance
        if stop_loss_pct > 0:
            position_size = risk_amount / stop_loss_pct
        else:
            position_size = risk_amount / 0.15  # Fallback

        return position_size

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

        # Dynamische Spread-Berechnung (Bid/Ask Simulation)
        is_crypto = "-USD" in symbol.upper()
        is_derivative = derivative_meta is not None or symbol.startswith("KO")
        
        if is_derivative:
            SPREAD_PCT = 0.015  # 1.5% Spread für Hebelprodukte (wg. Emittenten-Risiko/Aufschlag)
        elif is_crypto:
            SPREAD_PCT = 0.005  # 0.5% Spread für Krypto-Börsen
        else:
            SPREAD_PCT = 0.002  # 0.2% für reguläre Aktien

        effective_price = price * (1.0 + SPREAD_PCT)

        cost = shares * effective_price
        if cost > depot["cash"]:
            shares = depot["cash"] / effective_price
            cost = shares * effective_price

        if shares <= 0 or cost <= 0:
            return False

        depot["cash"] -= (cost + 1.00)
        now_str = get_berlin_now().strftime("%Y-%m-%d %H:%M")

        pos_dict = {
            "symbol": symbol,
            "name": name,
            "shares": round(shares, 4),
            "buy_price": round(effective_price, 4),
            "current_price": round(price, 4),  # Current market price is still mid
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
            fee = cost * SPREAD_PCT + 1.00; self.db.record_trade(depot_key, "BUY", symbol, name, shares, cost, price, reason=reason, fees=fee)
        except Exception:
            pass

        self._save()
        return True

    def sell(self, depot_key: str, symbol: str, price: float, reason: str = "", shares_to_sell: Optional[float] = None, fee: float = 1.00) -> bool:
        """Sells an entire or partial open position and records realized gain/loss."""
        depot = self.data["portfolios"].get(depot_key)
        if not depot or symbol not in depot["positions"]:
            return False

        pos = depot["positions"][symbol]
        total_shares = pos["shares"]
        
        if shares_to_sell is None or shares_to_sell >= total_shares:
            shares = total_shares
            is_partial = False
        else:
            shares = shares_to_sell
            is_partial = True
        
        # Dynamische Spread-Berechnung (Bid/Ask Simulation)
        is_crypto = "-USD" in symbol.upper()
        is_derivative = pos.get("derivative_meta") is not None or symbol.startswith("KO")
        
        if is_derivative:
            SPREAD_PCT = 0.015  # 1.5% 
        elif is_crypto:
            SPREAD_PCT = 0.005  # 0.5% 
        else:
            SPREAD_PCT = 0.002  # 0.2% 
            
        effective_price = price * (1.0 - SPREAD_PCT)
        
        revenue = shares * effective_price
        pnl = (effective_price - pos["buy_price"]) * shares
        pnl_pct = ((effective_price - pos["buy_price"]) / pos["buy_price"]) * 100.0 if pos["buy_price"] > 0 else 0.0

        depot["cash"] += (revenue - 1.00)
        now_str = get_berlin_now().strftime("%Y-%m-%d %H:%M")

        trade_record = {
            "type": "SELL",
            "symbol": symbol,
            "name": pos["name"],
            "product_type": pos.get("derivative_type", "STOCK"),
            "shares": round(shares, 4),
            "buy_price": round(pos["buy_price"], 4),
            "sell_price": round(effective_price, 4),
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

        if is_partial:
            pos["shares"] -= shares
            if "scaled_out" not in pos:
                pos["scaled_out"] = True
        else:
            del depot["positions"][symbol]
            
        self._save()
        return True

    def update_live_prices(self, force: bool = False):
        """Fetches live prices for all positions across all 3 depots in parallel and writes back (throttled)."""
        now = time.time()
        if not force and (now - self._last_price_update) < 20.0:
            return  # Skip redundant external API calls if updated within 20s
        self._last_price_update = now

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
                import yfinance as yf
                ticker = yf.Ticker(sym)
                
                # 1. Try history (works best on GitHub Actions)
                try:
                    df = ticker.history(period="1d")
                    if not df.empty:
                        return sym, float(df['Close'].iloc[-1])
                except:
                    pass
                    
                # 2. Try fast_info
                try:
                    px = ticker.fast_info.last_price
                    return sym, px
                except:
                    pass
                    
                # 3. Try info dictionary
                info = ticker.info or {}
                px = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose")
                if px:
                    return sym, float(px)
                    
                return sym, None
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
            wkn_code = get_wkn(sym)

            invested_value += pos_val
            positions_list.append({
                "wkn": wkn_code,
                "symbol": wkn_code,
                "ticker": sym,
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
                wkn_code = get_wkn(t_sym)
                merged_history.append({
                    "wkn": wkn_code,
                    "type": t_type,
                    "action": t_type,
                    "symbol": wkn_code,
                    "ticker": t_sym,
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

        # Realised trade statistics. A SELL carries the P&L of the position it
        # closed; partial sales (scaling out) each count as their own closed trade.
        closed = [t for t in merged_history
                  if str(t.get("type", "")).upper() == "SELL" and t.get("pnl") is not None]
        wins = [t for t in closed if float(t["pnl"]) > 0]
        losses = [t for t in closed if float(t["pnl"]) <= 0]
        gross_win = sum(float(t["pnl"]) for t in wins)
        gross_loss = abs(sum(float(t["pnl"]) for t in losses))
        trade_stats = {
            "closed_trades": len(closed),
            "wins": len(wins),
            "losses": len(losses),
            "win_rate_pct": round(len(wins) / len(closed) * 100.0, 1) if closed else None,
            "avg_win": round(gross_win / len(wins), 2) if wins else 0.0,
            "avg_loss": round(gross_loss / len(losses), 2) if losses else 0.0,
            "realized_pnl": round(gross_win - gross_loss, 2),
            # Profit factor: gross profit over gross loss. Above 1.0 the depot earns
            # more on its winners than it gives back on its losers.
            "profit_factor": (round(gross_win / gross_loss, 2) if gross_loss > 0
                              else (None if not wins else float("inf"))),
            "best_trade": max(closed, key=lambda t: float(t["pnl"])) if closed else None,
            "worst_trade": min(closed, key=lambda t: float(t["pnl"])) if closed else None,
        }

        prev_close = None
        try:
            prev_close = self.db.get_previous_daily_close(depot_key)
        except Exception:
            pass
        
        today_pnl = 0.0
        today_pnl_pct = 0.0
        if prev_close and prev_close > 0:
            today_pnl = total_value - prev_close
            today_pnl_pct = (today_pnl / prev_close) * 100.0

        return {
            "name": depot.get("name"),
            "strategy": depot.get("strategy"),
            "total_value": round(total_value, 2),
            "cash": round(cash, 2),
            "invested_value": round(invested_value, 2),
            "cash_ratio_pct": round((cash / total_value * 100.0) if total_value > 0 else 100.0, 1),
            "total_pnl": round(total_pnl, 2),
            "total_pnl_pct": round(total_pnl_pct, 2),
            "today_pnl": round(today_pnl, 2),
            "today_pnl_pct": round(today_pnl_pct, 2),
            "positions": positions_list,
            "history": merged_history,
            "trade_stats": trade_stats
        }

    def get_equity_curve(self, depot_key: str) -> pd.DataFrame:
        """Constructs an authentic historical equity curve dataframe tracking hourly depot development starting from 24.08.2026."""
        depot = self.data["portfolios"].get(depot_key, {})
        summary = self.get_depot_summary(depot_key)
        
        # Record current live hour snapshot
        curr_hour_str = get_berlin_now().strftime("%Y-%m-%d %H:00")
        self.db.record_hourly_snapshot(
            depot_id=depot_key,
            total_value=summary["total_value"],
            cash=summary["cash"],
            invested_value=summary["invested_value"],
            pnl=summary["total_pnl"],
            pnl_pct=summary["total_pnl_pct"],
            num_positions=len(summary["positions"]),
            snapshot_time=curr_hour_str
        )
        
        snapshots = self.db.get_hourly_snapshots(depot_key)
        rows = []
        if snapshots:
            for s in snapshots:
                rows.append({
                    "date": s["snapshot_time"],
                    "total_value": s["total_value"],
                    "cash": s["cash"],
                    "invested_value": s["invested_value"],
                    "pnl": s["pnl"],
                    "pnl_pct": s["pnl_pct"]
                })
        else:
            rows.append({
                "date": curr_hour_str,
                "total_value": summary["total_value"],
                "cash": summary["cash"],
                "invested_value": summary["invested_value"],
                "pnl": summary["total_pnl"],
                "pnl_pct": summary["total_pnl_pct"]
            })
                
        df = pd.DataFrame(rows)
        df["baseline"] = float(depot.get("initial_cash", 10000.0))
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
        # JPY carry-trade unwind guard. A sharp yen appreciation forces global
        # carry positions to be closed, which hits risk assets first. The metric
        # existed in commodities_forex_radar but nothing ever acted on it.
        carry_unwind, usdjpy = False, None
        try:
            fx = self.deep_intel.forex_engine.get_forex_overview()
            usdjpy = float(fx.get("rates", {}).get("USD/JPY", 154.0))
            carry_unwind = usdjpy < self.strategy.get("carry_unwind_usdjpy_threshold", 145.0)
        except Exception:
            carry_unwind = False
        if carry_unwind:
            actions_taken.append(f"🛑 Carry-Unwind-Schutz aktiv (USD/JPY {usdjpy:.1f}) — keine neuen Longs")

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

            # 1c. Trend-following exit: breakeven guard, then ATR chandelier trail.
            #     No profit target and no fixed ratchet - the old +8% -> +3% lock
            #     capped the upside at 3% while the downside ran to the full stop.
            #     Stops only ever ratchet up, never down.
            pos_atr_pct = self._position_atr_pct(sym, pos)
            if pos_atr_pct > 0:
                be_trigger = self.strategy.get("short_term_breakeven_trigger_atr", 1.0)
                trail_mult = self.strategy.get("short_term_trail_atr_mult", 2.5)

                # Once the trade has earned one ATR of room, it may no longer lose
                if gain_pct >= be_trigger * pos_atr_pct * 100.0:
                    be_sl = round(buy_p * 1.001, 2)
                    if not pos.get("stop_loss") or pos["stop_loss"] < be_sl:
                        pos["stop_loss"] = be_sl

                # Chandelier trail at the same ATR distance as the initial stop.
                # Never placed below entry, so it cannot turn a winner into a loser.
                trail_sl = round(peak_p * (1.0 - trail_mult * pos_atr_pct), 2)
                if trail_sl > buy_p and (not pos.get("stop_loss") or pos["stop_loss"] < trail_sl):
                    pos["stop_loss"] = trail_sl

            # Carry unwind: every position already in profit is pulled to breakeven
            # so a liquidity shock cannot turn a winner into a loser.
            if carry_unwind and curr_p > buy_p:
                be_sl = round(buy_p * 1.001, 2)
                if not pos.get("stop_loss") or pos["stop_loss"] < be_sl:
                    pos["stop_loss"] = be_sl

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

            # 1f. Laufendes Thesen-Audit (Thesis Invalidation / Momentum-Erosion)
            pos_intel = self.deep_intel.get_asset_360_intelligence(sym)
            pos_alpha = pos_intel.get("composite_alpha_score")
            flow = pos_intel.get("smart_money_flow", {})
            pos_pcr = flow.get("put_call_ratio")
            # Only act on a thesis break when enough of the score is actually backed
            # by data. Previously a missing alpha defaulted to 70 and a missing
            # put/call ratio to 0.8, so this exit silently never fired for German
            # stocks or crypto - it looked active and protected nothing.
            min_dq = self.strategy.get("min_data_quality_for_thesis_exit", 0.45)
            thesis_reliable = (pos_alpha is not None
                               and pos_intel.get("data_quality", 0) >= min_dq)
            if thesis_reliable and (pos_alpha < 42 or (pos_pcr is not None and pos_pcr > 1.35)):
                self.sell("short_term", sym, curr_p, 
                          reason=f"🚨 Thesen-Bruch: Momentum & Smart-Money erodiert (Alpha: {pos_alpha:.0f}/100, PCR: {pos_pcr if pos_pcr is not None else 'o. A.'}) ➔ Vorzeitiger Ausstieg")
                actions_taken.append(f"THESEN-AUSSTIEG {sym} (Alpha {pos_alpha:.0f}/100)")
                continue

        # 1g. Multi-Source Opportunity Check & Intelligent Capital Reallocation
        top_st_candidate = None
        best_score = 50

        # Both sources feed ONE scored list. Previously `if rt_alerts:` short-circuited
        # the whole block, so the depot bought the NEWEST realtime alert with no quality
        # bar at all, and the scored scan path below was effectively dead code.
        min_alpha = self.strategy.get("short_term_min_alpha_score", 55)
        min_spike = self.strategy.get("short_term_min_spike_pct", 1.5)
        max_cands = self.strategy.get("short_term_max_candidates_scored", 12)
        scan_by_sym = {c["symbol"]: c for c in scan_results}

        raw_candidates, seen = [], set()
        # Realtime alerts, strongest first. The scanner alerts from 0.5% because that is
        # a daytrade trigger; a multi-day swing entry needs a lot more than that.
        for a in sorted(rt_alerts, key=lambda x: x.get("change_1min_pct", 0), reverse=True):
            a_sym = a["symbol"]
            if a_sym in seen or not a.get("trigger_price"):
                continue
            if a.get("change_1min_pct", 0) < min_spike:
                continue
            seen.add(a_sym)
            raw_candidates.append(("realtime", a_sym, a))
        for c in scan_results[:10]:
            if c["symbol"] in seen:
                continue
            seen.add(c["symbol"])
            raw_candidates.append(("scan", c["symbol"], c))

        scored_candidates = []
        for source, c_sym, payload in raw_candidates[:max_cands]:
            intel = self.deep_intel.get_asset_360_intelligence(c_sym)
            alpha = intel.get("composite_alpha_score")
            if alpha is None:
                continue  # No data at all - never buy on a substituted constant
            # Identical blend for both sources. A symbol the scanner has no read on
            # gets a NEUTRAL 50, not a free pass - otherwise missing data would score
            # better than a measured weak breakout.
            breakout = scan_by_sym.get(c_sym, {}).get("breakout_score", 50)
            c_score = breakout * 0.4 + alpha * 0.6
            scored_candidates.append((c_score, source, c_sym, payload, intel))

        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        st_scores = [x[0] for x in scored_candidates]
        st_entered = False
        if scored_candidates and scored_candidates[0][0] >= min_alpha:
            best_score, source, c_sym, payload, intel = scored_candidates[0]
            flow = intel["smart_money_flow"]
            social = intel["social_sentiment"]
            if source == "realtime":
                pcr = flow.get("put_call_ratio")
                news_note = (f"News {social['nlp_sentiment_score']}/100"
                             if social.get("nlp_sentiment_score") is not None else "News o. A.")
                reason_str = (f"⚡ Echtzeit-Spike ({payload.get('change_1min_pct', 0):+.1f}%, "
                              f"Alpha {best_score:.0f}/100) | "
                              f"{'PCR ' + format(pcr, '.2f') if pcr is not None else 'keine Optionsdaten'} "
                              f"| {news_note}")
                c_price = payload.get("trigger_price")
            else:
                pcr = flow.get("put_call_ratio")
                reason_str = (f"🚨 Smart-Money Ausbruch (Alpha {best_score:.0f}/100) "
                              f"| {'PCR: ' + format(pcr, '.2f') if pcr is not None else 'keine Optionsdaten'} "
                              f"| {social.get('trending_theme', 'keine Meldungen')}")
                c_price = payload.get("price")
            top_st_candidate = {"symbol": c_sym, "name": payload.get("name", c_sym),
                                "price": c_price, "reason": reason_str,
                                "is_realtime": source == "realtime"}

        # If we have a great candidate but low cash, intelligently swap the most mature profitable or weakest dead-money position!
        if top_st_candidate and top_st_candidate["symbol"] not in st_depot["positions"]:
            if st_depot["cash"] < 1500.0 and len(st_depot["positions"]) >= 3:
                held_rankings = []
                for s, p in st_depot["positions"].items():
                    h_intel = self.deep_intel.get_asset_360_intelligence(s)
                    h_alpha = h_intel.get("composite_alpha_score")
                    h_gain = (p["current_price"] - p["buy_price"]) / p["buy_price"] * 100.0 if p["buy_price"] > 0 else 0.0
                    # A position whose alpha cannot be measured is not "dead money" -
                    # it is unmeasured. Ranking it as 70 would have swapped it out on
                    # the strength of a placeholder, so it is excluded instead.
                    if h_alpha is not None:
                        held_rankings.append((s, p, h_alpha, h_gain))
                
                # Check for profitable harvest first (>= 5%)
                prof_positions = sorted([x for x in held_rankings if x[3] >= 5.0], key=lambda x: x[3], reverse=True)
                if prof_positions:
                    swap_sym, swap_pos, swap_alpha, swap_gain = prof_positions[0]
                    self.sell("short_term", swap_sym, swap_pos["current_price"], 
                              reason=f"💡 Opportunitäts-Umschichtung: Gewinn bei +{swap_gain:.1f}% mitgenommen für neuen Ausbruch {top_st_candidate['symbol']}")
                    actions_taken.append(f"UMSCHICHTUNG: {swap_sym} (+{swap_gain:.1f}%) ➔ {top_st_candidate['symbol']}")
                else:
                    # Dead Money / Alpha-Spread Swap (Delta >= 25 Alpha points)
                    held_by_alpha = sorted(held_rankings, key=lambda x: x[2])
                    weakest_sym, weakest_pos, weakest_alpha, weakest_gain = held_by_alpha[0]
                    if (best_score - weakest_alpha) >= 25.0:
                        self.sell("short_term", weakest_sym, weakest_pos["current_price"],
                                  reason=f"💡 Opportunitäts-Tausch (Dead Money): Schwächeren Wert ({weakest_sym}, Alpha {weakest_alpha:.0f}) gegen Top-Ausbruch ({top_st_candidate['symbol']}, Alpha {best_score:.0f}) getauscht")
                        actions_taken.append(f"OPPORTUNITÄTS-TAUSCH: {weakest_sym} ➔ {top_st_candidate['symbol']}")

            # Execute Buy if cash available (Long or Short Turbo)
            if st_depot["cash"] >= 1500.0 and len(st_depot["positions"]) < 4:
                p = top_st_candidate["price"]
                sym = top_st_candidate["symbol"]
                if p and p > 0:
                    vol_factor = self._calculate_volatility_factor(sym)
                    regime = self._get_market_regime()
                    base_alloc = 2000.0
                    if regime == "BEAR":
                        base_alloc = 1200.0  # Reduce risk
                    
                    # Volatility-scaled stop. Widening the stop without touching the
                    # position size would silently raise the risk per trade, so the
                    # allocation is capped at a fixed risk budget instead.
                    sl_pct = self._short_term_stop_pct(sym)
                    depot_value = st_depot["cash"] + sum(
                        x["current_price"] * x["shares"] for x in st_depot["positions"].values())
                    risk_budget = depot_value * self.strategy.get("short_term_max_risk_per_trade_pct", 0.015)
                    risk_cap = risk_budget / sl_pct if sl_pct > 0 else base_alloc

                    alloc = min(base_alloc * vol_factor, risk_cap, st_depot["cash"] * 0.85)
                    is_bearish = top_st_candidate.get("direction") == "SHORT" or "Absturz" in top_st_candidate["reason"] or "Breakdown" in top_st_candidate["reason"]
                    if carry_unwind and not is_bearish:
                        # Shorts stay allowed - they profit from exactly this move
                        actions_taken.append(f"⏸️ Kurzfrist-Long {sym} pausiert (Carry-Unwind)")
                    elif is_bearish:
                        turbo = DerivativeEngine.create_turbo_knockout(sym, top_st_candidate["name"], p, direction="SHORT", target_leverage=3.5)
                        cert_price = turbo["cert_price"]
                        shares = alloc / cert_price
                        # Same underlying stop distance, expressed on the certificate
                        cert_sl_pct = min(sl_pct * max(turbo.get("leverage", 1.0), 1.0), 0.5)
                        approved, msg = self._tribunal_approved_buy("short_term", turbo["wkn"], turbo["name"], shares, cert_price,
                                 reason=f"🔻 Bearisher Short-Trade: {top_st_candidate['reason']}",
                                 stop_loss=cert_price*(1.0 - cert_sl_pct), take_profit=None, derivative_meta=turbo)
                        if approved:
                            st_entered = True
                            actions_taken.append(f"KAUF {turbo['name']} (🔻 Short-Hebel)")
                        else:
                            actions_taken.append(f"VETO (Short-Term): {turbo['name']} ({msg})")
                    else:
                        shares = alloc / p
                        approved, msg = self._tribunal_approved_buy("short_term", sym, top_st_candidate["name"], shares, p,
                                 reason=top_st_candidate["reason"],
                                 stop_loss=p*(1.0 - sl_pct), take_profit=None)  # ATR-scaled, then trailed
                        if approved:
                            st_entered = True
                            actions_taken.append(f"KAUF {sym} für Kurzfrist-Depot")
                        else:
                            actions_taken.append(f"VETO (Short-Term): {sym} ({msg})")

        if not st_entered:
            if not st_scores:
                st_block = "keine_kandidaten"
            elif st_scores[0] < min_alpha:
                st_block = "unter_min_alpha_score"
            elif st_depot["cash"] < 1500.0:
                st_block = "zu_wenig_cash"
            elif len(st_depot["positions"]) >= 4:
                st_block = "depot_voll"
            else:
                st_block = "tribunal_veto_oder_kein_preis"
        else:
            st_block = ""
        self._record_entry_diagnostic("short_term", st_scores, float(min_alpha),
                                      st_entered, st_block)

        # ----------------------------------------------------------------------
        # 2. MITTELFRISTIGES TREND- & GROWTH-DEPOT (1–6 Monate / Swing & Hedge)
        # ----------------------------------------------------------------------
        mt_depot = self.data["portfolios"]["medium_term"]

        # 2a. Makro-Absicherung: index short while the market is in risk-off stress.
        #     Opened outside the normal position budget and exempt from the trend
        #     exits below - a hedge is supposed to lose money when the book wins.
        hedge_on = self.strategy.get("medium_term_hedge_vix_threshold", 28.0)
        hedge_off = self.strategy.get("medium_term_hedge_exit_vix", 22.0)
        hedge_sym = self.strategy.get("medium_term_hedge_symbol", "SPY")
        vix_now = self._get_vix()
        open_hedges = [s for s, hp in mt_depot["positions"].items() if hp.get("is_macro_hedge")]

        if open_hedges and vix_now < hedge_off:
            for h_sym in open_hedges:
                hp = mt_depot["positions"][h_sym]
                self.sell("medium_term", h_sym, hp["current_price"],
                          reason=f"🛡️ Makro-Hedge aufgelöst (VIX {vix_now:.1f} < {hedge_off}) — Marktstress abgeklungen")
                actions_taken.append(f"HEDGE GESCHLOSSEN {h_sym} (VIX {vix_now:.1f})")
        elif not open_hedges and vix_now >= hedge_on:
            mt_invested = sum(hp["current_price"] * hp["shares"] for hp in mt_depot["positions"].values())
            hedge_alloc = min(mt_invested * self.strategy.get("medium_term_hedge_pct", 0.20),
                              mt_depot["cash"] * 0.5)
            if hedge_alloc >= 200.0:
                idx_price = 0.0
                try:
                    idx_hist = yf.Ticker(hedge_sym).history(period="1d")
                    if not idx_hist.empty:
                        idx_price = float(idx_hist["Close"].iloc[-1])
                except Exception:
                    idx_price = 0.0
                if idx_price > 0:
                    h_turbo = DerivativeEngine.create_turbo_knockout(
                        hedge_sym, f"{hedge_sym} Index", idx_price, direction="SHORT",
                        target_leverage=self.strategy.get("medium_term_hedge_leverage", 3.0))
                    h_turbo["is_macro_hedge"] = True
                    h_shares = hedge_alloc / h_turbo["cert_price"]
                    self.buy("medium_term", h_turbo["wkn"], h_turbo["name"], h_shares, h_turbo["cert_price"],
                             reason=f"🛡️ Makro-Absicherung: VIX {vix_now:.1f} ≥ {hedge_on} — {hedge_alloc:.0f}€ Buchwert gegen Korrektur gehedgt",
                             stop_loss=None, take_profit=None, derivative_meta=h_turbo)
                    actions_taken.append(f"HEDGE ERÖFFNET ({hedge_sym} Short {vix_now:.1f} VIX)")

        for sym in list(mt_depot["positions"].keys()):
            pos = mt_depot["positions"][sym]
            if pos.get("is_macro_hedge"):
                continue  # Exits handled by the VIX rule above, not by trend logic
            curr_p = pos["current_price"]
            buy_p = pos["buy_price"]
            gain_pct = ((curr_p - buy_p) / buy_p * 100.0) if buy_p > 0 else 0.0

            peak_p = max(pos.get("peak_price", buy_p), curr_p)
            pos["peak_price"] = peak_p

            # Trailing Profit Ratchet & Scaling Out
            if gain_pct >= 35.0 and not pos.get("scaled_out"):
                self.sell("medium_term", sym, curr_p, reason=f"💰 Scaling Out: +{gain_pct:.1f}% erreicht, 50% der Position gesichert", shares_to_sell=pos["shares"]/2.0)
                actions_taken.append(f"TEILVERKAUF {sym} (+{gain_pct:.1f}%)")

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

            # 2e. Laufendes Wachstums- & Trend-Audit (Thesen-Bruch)
            mt_pos_intel = self.deep_intel.get_asset_360_intelligence(sym)
            mt_alpha = mt_pos_intel.get("composite_alpha_score")
            mt_min_dq = self.strategy.get("min_data_quality_for_thesis_exit", 0.45)
            if (mt_alpha is not None
                    and mt_pos_intel.get("data_quality", 0) >= mt_min_dq
                    and mt_alpha < 45):
                self.sell("medium_term", sym, curr_p,
                          reason=f"⚠️ Thesen-Bruch: Mittelfristiges Wachstums-Rating unter 45 gefallen (Alpha: {mt_alpha:.0f}/100) ➔ Vorzeitiger Ausstieg")
                actions_taken.append(f"THESEN-AUSSTIEG {sym} (Alpha {mt_alpha:.0f}/100)")
                continue

        # Mittelfrist Opportunity & Dead-Money Check
        if scan_results:
            # Previously: pick max() by the short/long blend, then gate that ONE
            # candidate on total_score. The two metrics disagree, so the depot was
            # blocked by WAC.DE (blend 95.4 / total 69) while eleven other names
            # cleared the threshold and were never looked at.
            mt_min_score = self.strategy.get("medium_term_min_score", 75)
            mt_qualified = [c for c in scan_results
                            if c.get("total_score", 0) >= mt_min_score
                            and c["symbol"] not in mt_depot["positions"]
                            and c.get("price")]
            mt_qualified.sort(
                key=lambda x: (x.get("short_score", 0) * 0.4 + x.get("long_score", 0) * 0.6),
                reverse=True)
            top_mt_cand = mt_qualified[0] if mt_qualified else None
            if top_mt_cand is None:
                best_seen = max((c.get("total_score", 0) for c in scan_results), default=0)
                actions_taken.append(
                    f"⏸️ Mittelfrist wartet (bester Gesamt-Score {best_seen:.0f} < {mt_min_score})")
            if top_mt_cand is not None:
                cand_intel = self.deep_intel.get_asset_360_intelligence(top_mt_cand["symbol"])
                cand_alpha = cand_intel.get("composite_alpha_score")
                if cand_alpha is None:
                    cand_alpha = 0.0  # Unmeasurable candidate never wins a swap
                if mt_depot["cash"] < 1500.0 and len(mt_depot["positions"]) >= 3:
                    mt_rankings = []
                    for s, p in mt_depot["positions"].items():
                        m_intel = self.deep_intel.get_asset_360_intelligence(s)
                        m_alpha = m_intel.get("composite_alpha_score")
                        if m_alpha is None:
                            continue  # Unmeasured holding is not swap material
                        m_gain = (p["current_price"] - p["buy_price"])/p["buy_price"]*100.0 if p["buy_price"] > 0 else 0.0
                        mt_rankings.append((s, p, m_alpha, m_gain))
                    
                    mt_profs = sorted([x for x in mt_rankings if x[3] >= 8.0], key=lambda x: x[3], reverse=True)
                    if mt_profs:
                        s_sym, s_pos, s_alpha, s_gain = mt_profs[0]
                        self.sell("medium_term", s_sym, s_pos["current_price"],
                                  reason=f"💡 Opportunitäts-Umschichtung: Gewinn bei +{s_gain:.1f}% realisiert für neuen Growth-Leader {top_mt_cand['symbol']}")
                        actions_taken.append(f"UMSCHICHTUNG: {s_sym} (+{s_gain:.1f}%) ➔ {top_mt_cand['symbol']}")
                    else:
                        # Dead-Money Rotation (Delta >= 20 Alpha points)
                        mt_by_alpha = sorted(mt_rankings, key=lambda x: x[2])
                        w_sym, w_pos, w_alpha, w_gain = mt_by_alpha[0]
                        if (cand_alpha - w_alpha) >= 20.0:
                            self.sell("medium_term", w_sym, w_pos["current_price"],
                                      reason=f"💡 Opportunitäts-Tausch: Stagnierenden Titel ({w_sym}, Alpha {w_alpha:.0f}) gegen stärkeren Growth-Leader ({top_mt_cand['symbol']}, Alpha {cand_alpha:.0f}) getauscht")
                            actions_taken.append(f"OPPORTUNITÄTS-TAUSCH: {w_sym} ➔ {top_mt_cand['symbol']}")

                mt_core_count = sum(1 for hp in mt_depot["positions"].values()
                                    if not hp.get("is_macro_hedge"))
                if (mt_depot["cash"] >= 1500.0
                        and mt_core_count < self.strategy.get("medium_term_max_positions", 4)):
                    p = top_mt_cand.get("price")
                    sym = top_mt_cand["symbol"]
                    if p and p > 0:
                        vol_factor = self._calculate_volatility_factor(sym)
                        regime = self._get_market_regime()
                        base_alloc = 2000.0
                        if regime == "BEAR":
                            base_alloc = 1000.0  # Defensive in bear market
                        
                        alloc = min(base_alloc * vol_factor, mt_depot["cash"] * 0.85)
                        shares = alloc / p
                        c_news = cand_intel['social_sentiment'].get('nlp_sentiment_score')
                        reason_msg = (f"📈 Growth & Smart Money (Alpha: {cand_alpha:.0f}/100, "
                                      f"News: {c_news if c_news is not None else 'o. A.'}/100)")
                        approved, msg = self._tribunal_approved_buy("medium_term", sym, top_mt_cand.get("name", sym), shares, p,
                                 reason=reason_msg,
                                 stop_loss=p*0.90, take_profit=None)  # Dynamic trailing
                        if approved:
                            actions_taken.append(f"KAUF {sym} für Mittelfrist-Depot")
                        else:
                            actions_taken.append(f"VETO (Medium-Term): {sym} ({msg})")

        # ----------------------------------------------------------------------
        # 3. LANGFRISTIGES INVESTMENT-DEPOT (Jahre / Quality, Moat & Macro-Hedge)
        # ----------------------------------------------------------------------
        lt_depot = self.data["portfolios"]["long_term"]
        for sym in list(lt_depot["positions"].keys()):
            pos = lt_depot["positions"][sym]
            curr_p = pos["current_price"]
            buy_p = pos["buy_price"]
            lt_intel = self.deep_intel.get_asset_360_intelligence(sym)
            forensic = lt_intel.get("forensic_quality", {})
            q_score = forensic.get("quality_investing_score")
            # Only sell on a MEASURED deterioration. Gold and Bitcoin have no
            # balance sheet at all and would previously have been scored 80 by
            # default - close enough to the threshold to be one bad default away
            # from a forced sale.
            if q_score is not None and q_score < 45:
                self.sell("long_term", sym, curr_p,
                          reason=f"🚨 Qualitäts-Degradierung: Fundamental-Rating auf {q_score}/100 gefallen ➔ Burggraben-Austausch")
                actions_taken.append(f"QUALITÄTS-AUSSTIEG {sym}")
                continue
        # The depot was seeded with five holdings but limited to four, so it could
        # never buy again regardless of cash. Both bounds are configuration now.
        lt_max_pos = self.strategy.get("long_term_max_positions", 6)
        lt_min_cash = self.strategy.get("long_term_min_cash", 1500.0)
        if lt_depot["cash"] >= lt_min_cash and len(lt_depot["positions"]) < lt_max_pos and scan_results:
            candidates = sorted(scan_results, key=lambda x: x.get("long_score", 0), reverse=True)
            lt_min_score = self.strategy.get("long_term_min_score", 75)
            for cand in candidates:
                sym = cand["symbol"]
                p = cand.get("price")
                # There used to be NO minimum here: the depot bought the best
                # available candidate no matter how weak, so in a poor market it
                # was forced into the least bad name instead of holding cash.
                if cand.get("long_score", 0) < lt_min_score:
                    actions_taken.append(
                        f"⏸️ Langfrist wartet (bester Score {cand.get('long_score', 0):.0f} < {lt_min_score})")
                    break  # sorted descending - nothing below will qualify either
                if sym not in lt_depot["positions"] and p and p > 0:
                    vol_factor = self._calculate_volatility_factor(sym)
                    regime = self._get_market_regime()
                    base_alloc = 2000.0
                    if regime == "BEAR" and sym not in ["GC=F", "SHY", "TLT", "IEF", "LQD"]:
                        # Halve allocation to standard stocks in a bear market
                        base_alloc = 1000.0
                        
                    alloc = min(base_alloc * vol_factor, lt_depot["cash"] * 0.85)
                    cand_intel = self.deep_intel.get_asset_360_intelligence(sym)
                    forensic = cand_intel["forensic_quality"]
                    moat_reason = f"🏰 Burggraben & Bilanz-Audit: {forensic['moat_rating']} | Piotroski: {forensic['piotroski_f_score']}"
                    
                    if cand.get("long_score", 0) >= 90:
                        bonus = DerivativeEngine.create_bonus_certificate(sym, cand.get("name", sym), p, barrier_pct=25.0, bonus_pct=14.0)
                        shares = alloc / p
                        approved, msg = self._tribunal_approved_buy("long_term", bonus["wkn"], bonus["name"], shares, p,
                                 reason=f"🛡️ Bonus-Zertifikat (-25% Puffer, +14% Bonus) | {moat_reason}", stop_loss=0, take_profit=0,
                                 derivative_meta=bonus)
                        if approved:
                            actions_taken.append(f"KAUF {bonus['name']} für Langfrist-Depot")
                        else:
                            actions_taken.append(f"VETO (Long-Term): {bonus['name']} ({msg})")
                    else:
                        shares = alloc / p
                        approved, msg = self._tribunal_approved_buy("long_term", sym, cand.get("name", sym), shares, p,
                                 reason=moat_reason, stop_loss=0, take_profit=0)
                        if approved:
                            actions_taken.append(f"KAUF {sym} für Langfrist-Depot")
                        else:
                            actions_taken.append(f"VETO (Long-Term): {sym} ({msg})")
                    break

        # ======================================================================
        # 4. DAYTRADER DEPOT — Professional Risk-Managed Intraday System
        #    Principles: 2% max risk/trade, RRR ≥ 2:1, daily loss limit,
        #    correlation check, VIX-adaptive modes, multi-factor entry score
        # ======================================================================
        dt_depot = self.data["portfolios"].get("day_trading")
        if dt_depot:
            trading_mode = self._get_trading_mode()
            eod_hour = self.strategy.get("daytrade_eod_time_hour", 21)
            eod_close_all = self.strategy.get("daytrade_eod_close_all", True)
            hour = get_berlin_now().hour

            # --- EXIT LOGIC (always runs, even in PAUSE mode) ---
            for sym in list(dt_depot["positions"].keys()):
                pos = dt_depot["positions"][sym]
                curr_p = pos["current_price"]
                buy_p = pos["buy_price"]
                gain_pct = ((curr_p - buy_p) / buy_p * 100.0) if buy_p > 0 else 0.0

                peak_p = max(pos.get("peak_price", buy_p), curr_p)
                pos["peak_price"] = peak_p

                # 4a. Check Knock-Out Barrier
                if pos.get("is_knocked_out"):
                    self.sell("day_trading", sym, 0.001, reason="❌ Knock-Out Barriere berührt (Totalverlust)")
                    actions_taken.append(f"KNOCK-OUT {sym}")
                    continue

                # 4b. Professional Trailing Stop System (3 stages)
                breakeven_pct = self.strategy.get("daytrade_trailing_breakeven_pct", 0.03) * 100
                lock_pct = self.strategy.get("daytrade_trailing_lock_pct", 0.05) * 100
                aggressive_pct = self.strategy.get("daytrade_trailing_aggressive_pct", 0.10) * 100

                if gain_pct >= aggressive_pct:
                    # Stage 3: Trail 5% below peak (aggressive profit protection)
                    pos["stop_loss"] = max(pos.get("stop_loss", 0), round(peak_p * 0.95, 2))
                elif gain_pct >= lock_pct:
                    # Stage 2: Lock in +2% profit minimum
                    pos["stop_loss"] = max(pos.get("stop_loss", 0), round(buy_p * 1.02, 2))
                elif gain_pct >= breakeven_pct:
                    # Stage 1: Move stop to breakeven (no loss possible)
                    pos["stop_loss"] = max(pos.get("stop_loss", 0), round(buy_p * 1.001, 2))

                # 4c. Strict stop-loss execution
                if pos.get("stop_loss") and curr_p <= pos["stop_loss"]:
                    if curr_p >= buy_p:
                        self.sell("day_trading", sym, curr_p, reason=f"🎯 Trailing-Stop gesichert (+{gain_pct:.1f}%)")
                        actions_taken.append(f"VERKAUF {sym} (Trailing-Profit +{gain_pct:.1f}%)")
                    else:
                        self.sell("day_trading", sym, curr_p, reason=f"🚨 Stop-Loss Disziplin ({gain_pct:.1f}%) — Verlust akzeptiert")
                        actions_taken.append(f"VERKAUF {sym} (Stop-Loss {gain_pct:.1f}%)")
                    continue

                # 4d. EOD: Close ALL positions (kein Übernacht-Risiko!)
                if hour >= eod_hour and eod_close_all:
                    reason = f"🛡️ EOD Pflichtverkauf ({gain_pct:+.1f}%) — Kein Übernacht-Risiko"
                    self.sell("day_trading", sym, curr_p, reason=reason)
                    actions_taken.append(f"VERKAUF {sym} (EOD {gain_pct:+.1f}%)")
                    continue

            # --- ENTRY LOGIC (blocked in PAUSE mode) ---
            dt_scores, dt_entered, dt_block = [], False, ""
            dt_threshold = self.strategy.get("daytrade_min_entry_score", 65)

            # Gate 0: VIX-Pause — no new trades when market is too chaotic
            if trading_mode == "PAUSE":
                dt_block = "vix_pause"
                actions_taken.append("⏸️ Daytrader PAUSE (VIX ≥ 35 — Markt zu chaotisch)")

            # Gate 0b: No entries outside active trading hours (8:00 - EOD)
            elif hour < 8 or hour >= eod_hour:
                dt_block = "ausserhalb_handelszeit"  # Silent - no log spam

            # Gate 1: Check daily loss limit
            elif not self._check_daily_loss_limit(dt_depot.get("cash", 0) + sum(
                    p["current_price"] * p["shares"] for p in dt_depot.get("positions", {}).values())):
                dt_block = "tages_verlustlimit"
                actions_taken.append("🛑 Daytrader GESPERRT (Tages-Verlustlimit -5% erreicht)")

            # Gate 2: Check daily trade count
            elif not self._check_daily_trade_count():
                dt_block = "max_trades_pro_tag"
                actions_taken.append("🛑 Daytrader GESPERRT (Max. Trades pro Tag erreicht)")

            # Gate 3: Basic prerequisites
            elif dt_depot["cash"] >= 500.0 and len(dt_depot["positions"]) < 3 and rt_alerts:
                min_score = self.strategy.get("daytrade_min_entry_score", 65)
                # In DEFENSIVE mode, require higher score
                if trading_mode == "DEFENSIVE":
                    min_score = 80

                # Today's trades, fetched once instead of per candidate (Gate 5).
                today_str = get_berlin_now().strftime("%Y-%m-%d")
                try:
                    recent_trades = self.db.get_trades("day_trading")
                    if not recent_trades:
                        recent_trades = list(reversed(dt_depot.get("history", [])))
                except Exception:
                    recent_trades = []
                todays_trades = [t for t in recent_trades
                                 if (t.get("executed_at") or t.get("date", "")).startswith(today_str)]

                # Gates 4-7 are local and cheap, so pre-filter every pending alert
                # before spending yfinance calls on the quality score.
                candidates = []
                for alert in rt_alerts:
                    sym = alert["symbol"]
                    p = alert.get("trigger_price", 10.0)
                    if p <= 0:
                        continue

                    # Gate 4: No duplicate positions on same underlying
                    if any(existing_sym == sym or pos.get("underlying_symbol") == sym
                           for existing_sym, pos in dt_depot["positions"].items()):
                        continue

                    # Gate 5: No revenge trading (same symbol today)
                    if any(t.get("symbol", "") == sym or sym in t.get("name", "")
                           or sym in t.get("ticker", "") for t in todays_trades):
                        continue

                    # Gate 6: Alert freshness (< 15 min old)
                    alert_ts = alert.get("timestamp")
                    if alert_ts:
                        try:
                            atime = datetime.datetime.strptime(alert_ts, "%Y-%m-%d %H:%M:%S")
                            if (get_berlin_now().replace(tzinfo=None) - atime).total_seconds() > 900:
                                continue
                        except Exception:
                            pass

                    # Gate 7: Correlation check (max 2 in same sector)
                    if not self._check_correlation(sym, dt_depot):
                        continue

                    candidates.append(alert)

                # Gate 8: Score the strongest survivors and keep the best one.
                # Capped because every score costs two yfinance calls.
                max_scored = self.strategy.get("daytrade_max_candidates_scored", 8)
                candidates.sort(key=lambda a: a.get("change_1min_pct", 0), reverse=True)

                top_alert, entry_score = None, 0
                for alert in candidates[:max_scored]:
                    score = self._calculate_entry_quality(alert, alert["symbol"])
                    dt_scores.append(score)
                    if score > entry_score:
                        top_alert, entry_score = alert, score

                dt_threshold = min_score
                if not candidates:
                    dt_block = "keine_kandidaten_nach_gates"
                elif not (top_alert and entry_score >= min_score):
                    dt_block = "unter_min_entry_score"

                if top_alert and entry_score >= min_score:
                    sym = top_alert["symbol"]
                    p = top_alert.get("trigger_price", 10.0)
                    real_name = next((r.get("name", sym) for r in scan_results if r["symbol"] == sym), sym)
                    if real_name == sym:
                        try:
                            info = yf.Ticker(sym).info
                            real_name = info.get('shortName') or info.get('longName') or sym
                        except:
                            pass
                    name = top_alert.get("name") or real_name

                    is_bearish = top_alert.get("direction") == "SHORT"
                    dir_str = "SHORT" if is_bearish else "LONG"

                    # Conservative leverage scaling (max 10x, not 30x)
                    spike = top_alert.get('change_1min_pct', 0.5)
                    chosen_lev = self._choose_leverage(spike)

                    # Risk-based position sizing (max 2% risk per trade)
                    regime = self._get_market_regime()
                    sl_pct = self.strategy.get("daytrade_stop_loss_pct", 0.15)
                    depot_value = dt_depot.get("cash", 10000) + sum(
                        pos["current_price"] * pos["shares"] for pos in dt_depot.get("positions", {}).values()
                    )
                    alloc = self._calculate_risk_based_position_size(
                        depot_value, p, sl_pct, trading_mode, is_bearish, regime
                    )
                    alloc = min(alloc, dt_depot["cash"] * 0.9)  # Never exceed 90% of cash

                    if chosen_lev > 1.0:
                        turbo = DerivativeEngine.create_turbo_knockout(sym, name, p, direction=dir_str, target_leverage=chosen_lev)
                        cert_price = turbo["cert_price"]
                        shares = alloc / cert_price
                        reason_msg = f"⚡ Daytrade ({spike:+.1f}% Spike, Score {entry_score}/100) | {chosen_lev}x Hebel | Risiko {sl_pct*100:.0f}%"
                        sl_price = cert_price * (1.0 - sl_pct)

                        self.buy("day_trading", turbo["wkn"], turbo["name"], shares, cert_price,
                                 reason=reason_msg,
                                 stop_loss=sl_price, take_profit=None, derivative_meta=turbo)
                        dt_entered = True
                        actions_taken.append(f"KAUF {turbo['name']} ({chosen_lev}x {dir_str}, Score {entry_score})")
                    else:
                        # Direct stock purchase (no leverage for weak signals)
                        shares = alloc / p
                        reason_msg = f"⚡ Daytrade ({spike:+.1f}% Spike, Score {entry_score}/100) | 1x Aktie | Risiko {sl_pct*100:.0f}%"
                        sl_price = p * (1.0 - sl_pct)

                        self.buy("day_trading", sym, name, shares, p,
                                 reason=reason_msg,
                                 stop_loss=sl_price, take_profit=None)
                        dt_entered = True
                        actions_taken.append(f"KAUF {sym} (1x Direkt, Score {entry_score})")

            if not dt_entered and not dt_block:
                dt_block = "kein_cash_oder_slot_frei"
            self._record_entry_diagnostic("day_trading", dt_scores, float(dt_threshold),
                                          dt_entered, dt_block)

        self._save()

        # Record hourly snapshots after bot runs to keep equity curves updated
        try:
            curr_hour_str = get_berlin_now().strftime("%Y-%m-%d %H:00")
            for k in ["short_term", "medium_term", "long_term", "day_trading"]:
                sm = self.get_depot_summary(k)
                self.db.record_hourly_snapshot(
                    depot_id=k, total_value=sm["total_value"], cash=sm["cash"],
                    invested_value=sm["invested_value"], pnl=sm["total_pnl"],
                    pnl_pct=sm["total_pnl_pct"], num_positions=len(sm["positions"]),
                    snapshot_time=curr_hour_str
                )
        except Exception:
            pass

        return actions_taken
