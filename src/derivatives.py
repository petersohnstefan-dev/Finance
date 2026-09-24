"""Derivative Pricing and Instrument Modeling for Knock-Outs, Factor Certificates, and Bonus Certificates."""

from typing import Dict, Any, List, Optional
import datetime

import zlib


def _stable_id(seed: str) -> int:
    """Deterministische Kennnummer.

    hash() auf Strings ist pro Prozess zufaellig (PYTHONHASHSEED), also bekam
    dasselbe Instrument bei jedem Bot-Lauf eine neue WKN. Dadurch griff die
    Tribunal-Sperre nie und derselbe abgelehnte Kandidat wurde alle fuenf
    Minuten erneut verhandelt.
    """
    return zlib.crc32(seed.encode("utf-8")) % 899999 + 100000


# A certificate below this price cannot carry a meaningful stop: prices get rounded
# to the cent, so the stop collapses onto the purchase price and only the knock-out
# can still fire - which is a total loss.
MIN_CERT_PRICE = 0.50

#: Underlyings cheaper than this are not offered as turbos at all. Their quotes tick
#: in increments of whole percent, and leverage multiplies that noise directly.
MIN_UNDERLYING_PRICE = 1.0

#: Subscription ratios an issuer would realistically use.
_RATIO_STEPS = [0.001, 0.01, 0.1, 1.0, 10.0, 100.0, 1000.0]


def round_price(value):
    """Rounds to a precision the price can actually carry.

    round(x, 2) on a 1-cent certificate rounds a 10% stop back onto the entry
    price. That is how a stop-loss silently became inoperative on 17.09. and a
    knock-out took the entire position.
    """
    if value is None:
        return None
    a = abs(value)
    if a >= 100:
        return round(value, 2)
    if a >= 1:
        return round(value, 3)
    if a >= 0.01:
        return round(value, 5)
    return round(value, 8)


#: Target price band for a generated certificate. Real issuers keep turbos in
#: roughly this range, and it is where the spread stays economically sane: the
#: bid/ask on a cent-priced paper is a double-digit percentage of its value.
TARGET_CERT_PRICE = 2.0


def _pick_ratio(current_price: float, target_leverage: float) -> float:
    """Chooses the subscription ratio that puts the certificate in a tradable band.

    The ratio used to be fixed at 0.1 with a max(0.01, ...) floor catching the
    result. For a 0.03 USD underlying that floor multiplied the price by 23x, so
    a '7x' turbo was priced as a 0.3x one and its stop was meaningless.

    Aiming at TARGET_CERT_PRICE rather than 1.0 keeps the result clear of the
    cent range even when the coarse ratio steps round the wrong way: four of the
    18 daytrade purchases landed at exactly 0.01 and produced 52% of that depot's
    entire loss.
    """
    if current_price <= 0 or target_leverage <= 0:
        return 0.1
    # intrinsic value per unit is price/leverage; we want intrinsic * ratio ~ target
    intrinsic = current_price / target_leverage
    ideal = TARGET_CERT_PRICE / intrinsic if intrinsic > 0 else 1.0
    viable = [r for r in _RATIO_STEPS if intrinsic * r >= MIN_CERT_PRICE]
    return min(viable or _RATIO_STEPS, key=lambda r: abs((r / ideal) - 1.0))

class DerivativeEngine:
    """Generates and prices synthetic/real derivative structures for equities, cryptos, and commodities."""

    @staticmethod
    def create_turbo_knockout(underlying_symbol: str, underlying_name: str, current_price: float,
                              direction: str = "LONG", target_leverage: float = 4.0,
                              ratio: float = None) -> Dict[str, Any]:
        """Creates a synthetic Turbo / Knock-Out Certificate with realistic pricing and leverage.

        Always check `valid` before buying: a turbo that cannot be priced sensibly
        comes back with valid=False and a reason instead of a broken instrument.
        """
        direction = direction.upper()
        if not current_price or current_price < MIN_UNDERLYING_PRICE:
            return {
                "type": "KNOCKOUT", "valid": False,
                # Machine-readable, because the callers must react differently.
                # A cheap underlying rules out the direct purchase as well; a
                # certificate price below the minimum does not.
                "invalid_code": "underlying_too_cheap",
                "invalid_reason": (f"Basiswert {underlying_symbol} steht bei {current_price}; "
                                   f"unter {MIN_UNDERLYING_PRICE} ist kein Turbo mit "
                                   f"tragfaehigem Stop darstellbar"),
                "underlying_symbol": underlying_symbol, "underlying_name": underlying_name,
                "cert_price": None, "leverage": None,
            }

        if ratio is None:
            ratio = _pick_ratio(current_price, target_leverage)

        if direction == "LONG":
            # Strike and KO Barrier below current price
            strike = current_price * (1.0 - (1.0 / target_leverage))
            ko_barrier = strike * 1.02  # Slight safety buffer above strike for barrier
            cert_price = (current_price - strike) * ratio
            distance_to_ko_pct = ((current_price - ko_barrier) / current_price) * 100.0
            wkn = f"KO{_stable_id(underlying_symbol + 'LONG')}"
            label = "⚡ Turbo Bull"
        else:
            # Short: Strike and Barrier above current price
            strike = current_price * (1.0 + (1.0 / target_leverage))
            ko_barrier = strike * 0.98
            cert_price = (strike - current_price) * ratio
            distance_to_ko_pct = ((ko_barrier - current_price) / current_price) * 100.0
            wkn = f"KO{_stable_id(underlying_symbol + 'SHORT')}"
            label = "\U0001f53b Turbo Bear"

        if cert_price < MIN_CERT_PRICE:
            return {
                "type": "KNOCKOUT", "valid": False,
                "invalid_code": "cert_price_too_low",
                "invalid_reason": (f"Zertifikatspreis waere {cert_price:.4f} und damit unter "
                                   f"{MIN_CERT_PRICE} - kein belastbarer Stop moeglich"),
                "underlying_symbol": underlying_symbol, "underlying_name": underlying_name,
                "cert_price": None, "leverage": None,
            }

        cert_price = round_price(cert_price)
        actual_leverage = (current_price / (cert_price / ratio)) if cert_price > 0 else 0
        name = f"{label} {actual_leverage:.1f}x auf {underlying_name} (KO: {round_price(ko_barrier)})"

        return {
            "type": "KNOCKOUT",
            "valid": True,
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
        wkn = f"FA{_stable_id(underlying_symbol + str(factor) + direction)}"
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
        wkn = f"BN{_stable_id(underlying_symbol + 'BONUS')}"
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
