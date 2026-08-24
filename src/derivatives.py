"""Derivative Pricing and Instrument Modeling for Knock-Outs, Factor Certificates, and Bonus Certificates."""

from typing import Dict, Any, List, Optional
import datetime

class DerivativeEngine:
    """Generates and prices synthetic/real derivative structures for equities, cryptos, and commodities."""

    @staticmethod
    def create_turbo_knockout(underlying_symbol: str, underlying_name: str, current_price: float, 
                              direction: str = "LONG", target_leverage: float = 4.0, 
                              ratio: float = 0.1) -> Dict[str, Any]:
        """Creates a synthetic Turbo / Knock-Out Certificate with realistic pricing and leverage."""
        direction = direction.upper()
        if direction == "LONG":
            # Strike and KO Barrier below current price
            strike = current_price * (1.0 - (1.0 / target_leverage))
            ko_barrier = strike * 1.02  # Slight safety buffer above strike for barrier
            cert_price = max(0.01, (current_price - strike) * ratio)
            distance_to_ko_pct = ((current_price - ko_barrier) / current_price) * 100.0
            actual_leverage = (current_price / (cert_price / ratio)) if cert_price > 0 else 0
            wkn = f"KO{abs(hash(underlying_symbol + 'LONG')) % 899999 + 100000}"
            name = f"⚡ Turbo Bull {actual_leverage:.1f}x auf {underlying_name} (KO: {ko_barrier:.2f})"
        else:
            # Short: Strike and Barrier above current price
            strike = current_price * (1.0 + (1.0 / target_leverage))
            ko_barrier = strike * 0.98
            cert_price = max(0.01, (strike - current_price) * ratio)
            distance_to_ko_pct = ((ko_barrier - current_price) / current_price) * 100.0
            actual_leverage = (current_price / (cert_price / ratio)) if cert_price > 0 else 0
            wkn = f"KO{abs(hash(underlying_symbol + 'SHORT')) % 899999 + 100000}"
            name = f"🔻 Turbo Bear {actual_leverage:.1f}x auf {underlying_name} (KO: {ko_barrier:.2f})"

        return {
            "type": "KNOCKOUT",
            "wkn": wkn,
            "name": name,
            "underlying_symbol": underlying_symbol,
            "underlying_name": underlying_name,
            "direction": direction,
            "ratio": ratio,
            "strike": round(strike, 2),
            "knockout_barrier": round(ko_barrier, 2),
            "initial_underlying_price": round(current_price, 2),
            "current_underlying_price": round(current_price, 2),
            "cert_price": round(cert_price, 2),
            "leverage": round(actual_leverage, 1),
            "distance_to_ko_pct": round(distance_to_ko_pct, 1),
            "is_knocked_out": False
        }

    @staticmethod
    def create_factor_certificate(underlying_symbol: str, underlying_name: str, current_price: float, 
                                  factor: int = 3, direction: str = "LONG") -> Dict[str, Any]:
        """Creates a constant leverage Factor Certificate (e.g. 3x Long / 5x Long)."""
        wkn = f"FA{abs(hash(underlying_symbol + str(factor) + direction)) % 899999 + 100000}"
        name = f"🚀 Faktor {factor}x {direction} auf {underlying_name}"
        initial_cert_price = 10.00  # Standard normalized starting price

        return {
            "type": "FACTOR",
            "wkn": wkn,
            "name": name,
            "underlying_symbol": underlying_symbol,
            "underlying_name": underlying_name,
            "direction": direction.upper(),
            "factor": factor,
            "initial_underlying_price": round(current_price, 2),
            "current_underlying_price": round(current_price, 2),
            "cert_price": initial_cert_price,
            "leverage": float(factor)
        }

    @staticmethod
    def create_bonus_certificate(underlying_symbol: str, underlying_name: str, current_price: float, 
                                 barrier_pct: float = 25.0, bonus_pct: float = 12.0) -> Dict[str, Any]:
        """Creates a Capped Bonus Certificate for defensive side-yields even in flat/declining markets."""
        barrier = current_price * (1.0 - (barrier_pct / 100.0))
        bonus_level = current_price * (1.0 + (bonus_pct / 100.0))
        wkn = f"BN{abs(hash(underlying_symbol + 'BONUS')) % 899999 + 100000}"
        name = f"🛡️ Bonus-Zertifikat auf {underlying_name} (Barriere: -{barrier_pct:.0f}%, Bonus: +{bonus_pct:.0f}%)"

        return {
            "type": "BONUS",
            "wkn": wkn,
            "name": name,
            "underlying_symbol": underlying_symbol,
            "underlying_name": underlying_name,
            "barrier": round(barrier, 2),
            "bonus_level": round(bonus_level, 2),
            "cap": round(bonus_level, 2),
            "initial_underlying_price": round(current_price, 2),
            "current_underlying_price": round(current_price, 2),
            "cert_price": round(current_price, 2),
            "distance_to_barrier_pct": barrier_pct,
            "bonus_yield_pct": bonus_pct,
            "barrier_breached": False
        }

    @staticmethod
    def update_derivative_price(position: Dict[str, Any], current_underlying_price: float) -> Dict[str, Any]:
        """Updates live derivative pricing and checks barriers."""
        p_type = position.get("derivative_type")
        if not p_type:
            return position

        init_underlying = position.get("initial_underlying_price", current_underlying_price)
        ratio = position.get("ratio", 0.1)

        # 1. Knock-Out / Turbo
        if p_type == "KNOCKOUT":
            strike = position.get("strike", 0.0)
            ko_barrier = position.get("knockout_barrier", 0.0)
            direction = position.get("direction", "LONG")

            if direction == "LONG":
                if current_underlying_price <= ko_barrier:
                    position["current_price"] = 0.001
                    position["is_knocked_out"] = True
                    position["distance_to_ko_pct"] = 0.0
                else:
                    position["current_price"] = max(0.01, (current_underlying_price - strike) * ratio)
                    position["distance_to_ko_pct"] = round(((current_underlying_price - ko_barrier) / current_underlying_price) * 100.0, 1)
            else:
                if current_underlying_price >= ko_barrier:
                    position["current_price"] = 0.001
                    position["is_knocked_out"] = True
                    position["distance_to_ko_pct"] = 0.0
                else:
                    position["current_price"] = max(0.01, (strike - current_underlying_price) * ratio)
                    position["distance_to_ko_pct"] = round(((ko_barrier - current_underlying_price) / current_underlying_price) * 100.0, 1)

        # 2. Factor Certificate
        elif p_type == "FACTOR":
            factor = position.get("factor", 3)
            direction = position.get("direction", "LONG")
            if init_underlying > 0:
                underlying_return = (current_underlying_price - init_underlying) / init_underlying
                if direction == "SHORT":
                    underlying_return = -underlying_return
                cert_return = underlying_return * factor
                buy_p = position.get("buy_price", 10.0)
                position["current_price"] = max(0.01, round(buy_p * (1.0 + cert_return), 2))

        # 3. Bonus Certificate
        elif p_type == "BONUS":
            barrier = position.get("barrier", 0.0)
            bonus_level = position.get("bonus_level", 0.0)
            if current_underlying_price <= barrier:
                position["barrier_breached"] = True
                position["current_price"] = current_underlying_price
            else:
                # Trades at a premium reflecting bonus floor
                position["current_price"] = max(current_underlying_price, round(current_underlying_price * 1.04, 2))

        return position
