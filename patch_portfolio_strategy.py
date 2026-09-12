import sys
import re

with open('src/portfolio.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add strategy loading to PortfolioManager __init__
old_init = """    def __init__(self, initial_capital_per_depot: float = 10000.0):
        self.initial_capital = initial_capital_per_depot
        self.db = PortfolioDB()
        self.deep_intel = DeepIntelligenceHub()
        self._last_price_update = 0.0
        self.data = self._load()"""

new_init = """    def __init__(self, initial_capital_per_depot: float = 10000.0):
        self.initial_capital = initial_capital_per_depot
        self.db = PortfolioDB()
        self.deep_intel = DeepIntelligenceHub()
        self._last_price_update = 0.0
        self.data = self._load()
        self.strategy = self._load_strategy()

    def _load_strategy(self) -> Dict[str, Any]:
        strat_file = os.path.join(os.path.dirname(__file__), "..", "data", "strategy.json")
        default_strat = {
            "daytrade_max_leverage": 30.0,
            "daytrade_stop_loss_pct": 0.25,
            "short_term_trailing_start_pct": 8.0,
            "short_term_stop_loss_pct": 0.15
        }
        if os.path.exists(strat_file):
            try:
                with open(strat_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    default_strat.update(data)
            except:
                pass
        return default_strat"""

content = content.replace(old_init, new_init)

# 2. Patch short_term rules (using self.strategy["short_term_trailing_start_pct"])
old_st_trail = """            if gain_pct >= 8.0:
                # Ratchet Stop-Loss to Breakeven + 3%
                lock_sl = round(buy_p * 1.03, 2)
                if not pos.get("stop_loss") or pos["stop_loss"] < lock_sl:
                    pos["stop_loss"] = lock_sl
                    
            if gain_pct >= 18.0:"""

new_st_trail = """            trail_start = self.strategy.get("short_term_trailing_start_pct", 8.0)
            if gain_pct >= trail_start:
                # Ratchet Stop-Loss to Breakeven + 3%
                lock_sl = round(buy_p * 1.03, 2)
                if not pos.get("stop_loss") or pos["stop_loss"] < lock_sl:
                    pos["stop_loss"] = lock_sl
                    
            if gain_pct >= 18.0:"""

content = content.replace(old_st_trail, new_st_trail)


# 3. Patch daytrader stop loss
old_dt_buy = """                        sl_price = cert_price * 0.75 # 25% Stop-Loss auf das Derivat"""
new_dt_buy = """                        sl_pct = self.strategy.get("daytrade_stop_loss_pct", 0.25)
                        sl_price = cert_price * (1.0 - sl_pct) # Dynamischer Stop-Loss durch KI-Tagebuch"""
content = content.replace(old_dt_buy, new_dt_buy)

# 4. Patch daytrader max leverage limit
old_dt_lev = """                    if spike >= 2.0:
                        chosen_lev = 30.0
                    elif spike >= 1.2:
                        chosen_lev = 15.0
                    elif spike >= 0.8:
                        chosen_lev = 10.0
                    elif spike >= 0.5:
                        chosen_lev = 5.0
                    else:
                        chosen_lev = 2.0 # Minimum 2x Hebel für Daytrader"""

new_dt_lev = """                    max_lev = self.strategy.get("daytrade_max_leverage", 30.0)
                    if spike >= 2.0:
                        chosen_lev = min(30.0, max_lev)
                    elif spike >= 1.2:
                        chosen_lev = min(15.0, max_lev)
                    elif spike >= 0.8:
                        chosen_lev = min(10.0, max_lev)
                    elif spike >= 0.5:
                        chosen_lev = min(5.0, max_lev)
                    else:
                        chosen_lev = min(2.0, max_lev) # Minimum 2x Hebel für Daytrader"""

content = content.replace(old_dt_lev, new_dt_lev)

with open('src/portfolio.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched portfolio.py with strategy.json logic.")
