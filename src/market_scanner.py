import json
import os
import sys
import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List, Optional

from src.universe import FULL_MARKET_UNIVERSE, CATEGORIZED_UNIVERSES
from src.forum_scanner import ForumSentimentHarvester
from src.data_fetcher import FinancialDataFetcher
from src.indicators import calculate_technical_indicators
from src.short_term_engine import ShortTermEngine
from src.long_term_engine import LongTermEngine
from src.synthesis import DecisionSynthesizer
from src.breakout_radar import BreakoutRadar

DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "market_scan_results.json")

class MarketScanner:
    """Scans and ranks across Stocks, Cryptocurrencies, Precious Metals, and Commodities."""

    def __init__(self, tickers: Optional[List[str]] = None):
        self.tickers = tickers or FULL_MARKET_UNIVERSE
        self.short_engine = ShortTermEngine()
        self.long_engine = LongTermEngine()
        self.synthesizer = DecisionSynthesizer()
        self.breakout_radar = BreakoutRadar()

    def _analyze_single_ticker(self, ticker: str, forum_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            fetcher = FinancialDataFetcher(ticker)
            prices_df = fetcher.get_historical_prices(period="1y")
            df_with_ind = calculate_technical_indicators(prices_df)
            fundamentals = fetcher.get_fundamentals()
            consensus = fetcher.get_analyst_consensus()
            social_sentiment = fetcher.get_social_sentiment()

            # Integrate forum sentiment
            clean_sym = ticker.split("-")[0].split(".")[0].split("=")[0].upper()
            f_info = forum_data.get(clean_sym) or forum_data.get(ticker.upper()) or {}
            mentions = f_info.get("mentions", 0)
            if mentions > 0:
                social_sentiment["forum_mentions"] = mentions
                social_sentiment["forum_sentiment"] = f_info.get("forum_sentiment_score", 50)
                social_sentiment["bullish_pct"] = (social_sentiment.get("bullish_pct", 50) + f_info.get("forum_sentiment_score", 50)) / 2.0
                social_sentiment["available"] = True

            short_res = self.short_engine.evaluate(df_with_ind, social_sentiment)
            long_res = self.long_engine.evaluate(fundamentals, consensus)
            synth = self.synthesizer.synthesize(short_res, long_res, fundamentals, consensus)
            breakout_res = self.breakout_radar.analyze_breakout_potential(df_with_ind, fundamentals, mentions)

            # Determine Asset Class & Region
            if "-USD" in ticker or "-EUR" in ticker:
                region = "🪙 Krypto"
                sector = "Kryptowährung"
            elif any(met in ticker for met in ["GC=F", "SI=F", "PL=F", "PA=F", "HG=F"]):
                region = "🥇 Edelmetalle"
                sector = "Edelmetall / Rohstoff"
            elif "=F" in ticker:
                region = "🛢️ Rohstoffe"
                sector = "Energie & Agrar"
            elif ".DE" in ticker:
                region = "Deutschland"
                sector = fundamentals.get("sector", "Aktie (DE)")
            elif any(ext in ticker for ext in [".PA", ".AS", ".SW", ".L", ".MC", ".MI"]):
                region = "Europa"
                sector = fundamentals.get("sector", "Aktie (EU)")
            else:
                region = "USA"
                sector = fundamentals.get("sector", "Aktie (US)")

            return {
                "symbol": ticker,
                "name": fundamentals.get("shortName", ticker),
                "region": region,
                "sector": sector,
                "industry": fundamentals.get("industry", "N/A"),
                "price": fundamentals.get("currentPrice") or (prices_df['Close'].iloc[-1] if not prices_df.empty else 0),
                "currency": fundamentals.get("currency", "USD"),
                "total_score": synth["total_score"],
                "short_score": short_res["score"],
                "long_score": long_res["score"],
                "breakout_score": breakout_res["breakout_score"],
                "breakout_status": breakout_res["status"],
                "breakout_triggers": [t["title"] for t in breakout_res.get("triggers", [])],
                "vol_ratio": breakout_res.get("vol_ratio", 1.0),
                "daily_return_pct": breakout_res.get("daily_return_pct", 0.0),
                "short_float": fundamentals.get("shortPercentOfFloat"),
                "short_ratio": fundamentals.get("shortRatio"),
                "squeeze_score": fundamentals.get("squeezeScore", 10.0),
                "action": synth["action"],
                "action_desc": synth["action_desc"],
                "color": synth["color"],
                "short_status": short_res["status"],
                "long_status": long_res["status"],
                "rsi": short_res.get("metrics", {}).get("rsi"),
                "pe": fundamentals.get("trailingPE"),
                "forward_pe": fundamentals.get("forwardPE"),
                "peg": fundamentals.get("pegRatio"),
                "roe": fundamentals.get("returnOnEquity"),
                "fcf_yield": fundamentals.get("fcfYield"),
                "dividend_yield": fundamentals.get("dividendYield"),
                "debt_to_equity": fundamentals.get("debtToEquity"),
                "upside_pct": consensus.get("upsideMeanPct"),
                "target_mean_price": consensus.get("targetMeanPrice"),
                "analyst_rec": consensus.get("recommendationMean"),
                "analyst_count": consensus.get("numberOfAnalystOpinions"),
                "forum_mentions": mentions,
                "forum_sentiment": f_info.get("forum_sentiment_score", 50) if mentions > 0 else None,
                "sample_forum_posts": f_info.get("sample_titles", []),
                "short_signals": [s["title"] for s in short_res.get("signals", [])],
                "long_signals": [s["title"] for s in long_res.get("signals", [])],
                "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception:
            return None

    def run_full_scan(self, max_workers: int = 12, progress_callback=None) -> List[Dict[str, Any]]:
        """Scans forums, then scans all assets (Stocks, Cryptos, Metals, Commodities)."""
        sys.stdout.write(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 1. Scanne Foren (Reddit r/wallstreetbets, r/CryptoCurrency, etc.)...\n")
        sys.stdout.flush()
        harvester = ForumSentimentHarvester(self.tickers)
        forum_data = harvester.scan_reddit(limit_per_sub=50)
        sys.stdout.write(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Foren-Scan fertig. Erwaehnungen fuer {len(forum_data)} Ticker erfasst.\n")
        sys.stdout.flush()

        sys.stdout.write(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 2. Starte Multi-Asset-Analyse fuer {len(self.tickers)} Assets (Aktien, Krypto, Rohstoffe)...\n")
        sys.stdout.flush()
        results = []
        completed = 0

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_ticker = {
                executor.submit(self._analyze_single_ticker, ticker, forum_data): ticker 
                for ticker in self.tickers
            }
            for future in as_completed(future_to_ticker):
                completed += 1
                try:
                    res = future.result()
                    if res:
                        results.append(res)
                except Exception:
                    pass
                if progress_callback:
                    progress_callback(completed, len(self.tickers))
                if completed % 25 == 0 or completed == len(self.tickers):
                    sys.stdout.write(f"  Fortschritt: {completed}/{len(self.tickers)} Assets verarbeitet...\n")
                    sys.stdout.flush()

        results.sort(key=lambda x: x["total_score"], reverse=True)

        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "scan_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "total_scanned": len(results),
                "data": results
            }, f, indent=2, ensure_ascii=False)

        sys.stdout.write(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Multi-Asset-Scan erfolgreich gespeichert ({len(results)} Assets).\n")
        sys.stdout.flush()
        return results

def load_cached_market_scan() -> Optional[Dict[str, Any]]:
    """Loads latest market scan results from disk."""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    return None

if __name__ == "__main__":
    scanner = MarketScanner()
    scanner.run_full_scan()
