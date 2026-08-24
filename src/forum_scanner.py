import re
import requests
from typing import Dict, Any, List
from collections import defaultdict
import datetime

class ForumSentimentHarvester:
    """Scans major investor forums (Reddit, StockTwits, etc.) to detect trending tickers and crowd sentiment."""

    SUBREDDITS = ["wallstreetbets", "stocks", "investing", "Finanzen", "pennystocks", "options"]
    
    BULLISH_KEYWORDS = {
        "call", "calls", "buy", "buying", "bought", "moon", "bull", "bullish", 
        "undervalued", "breakout", "gem", "long", "rally", "upgrade", "pump", "strong", "holding", "hold"
    }
    BEARISH_KEYWORDS = {
        "put", "puts", "sell", "selling", "sold", "bear", "bearish", "overvalued", 
        "drop", "dump", "crash", "short", "shorting", "downgrade", "bubble", "weak", "tanking"
    }

    COMMON_WORDS = {
        "A", "I", "AND", "OR", "THE", "FOR", "TO", "IN", "ON", "AT", "BY", "WITH",
        "ALL", "ARE", "AS", "BE", "BUT", "CAN", "DID", "DO", "GET", "HAS", "HAD",
        "HE", "HER", "HIM", "HIS", "HOW", "IF", "IS", "IT", "ITS", "MAY", "ME",
        "MY", "NO", "NOT", "NOW", "OFF", "ONE", "OUT", "SEE", "SO", "THEIR", "THEM",
        "THEN", "THERE", "THESE", "THEY", "THIS", "UP", "WAS", "WE", "WHAT", "WHEN",
        "WHO", "WILL", "YOU", "YOUR", "CEO", "CFO", "SEC", "FED", "GDP", "CPI", "USA",
        "DD", "YOLO", "FOMO", "ATH", "EOD", "ETF", "EV", "AI", "WSB", "RH", "P/E", "EPS", "USD", "EUR"
    }

    def __init__(self, target_tickers: List[str]):
        self.target_map = {}
        for t in target_tickers:
            clean = t.split(".")[0].upper()
            self.target_map[clean] = t.upper()
            self.target_map[t.upper()] = t.upper()

    def scan_reddit(self, limit_per_sub: int = 50) -> Dict[str, Dict[str, Any]]:
        """Scans recent hot and new posts from investor subreddits."""
        stats = defaultdict(lambda: {
            "mentions": 0,
            "bullish_count": 0,
            "bearish_count": 0,
            "subreddits": set(),
            "sample_titles": []
        })

        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) MarketResearch/2.0"}

        for sub in self.SUBREDDITS:
            for feed in ["hot", "new"]:
                url = f"https://www.reddit.com/r/{sub}/{feed}.json?limit={limit_per_sub}"
                try:
                    resp = requests.get(url, headers=headers, timeout=6)
                    if resp.status_code != 200:
                        continue
                    data = resp.json()
                    posts = (data.get("data") or {}).get("children", [])

                    for p in posts:
                        pdata = p.get("data", {})
                        title = pdata.get("title", "")
                        selftext = pdata.get("selftext", "")
                        full_text = f"{title} {selftext}"

                        # Match potential ticker tokens like , AAPL, etc.
                        tokens = set(re.findall(r'\b\True([A-Za-z]{2,6})\b', full_text))
                        text_words = set(re.findall(r'\b\w+\b', full_text.lower()))

                        bull_hits = len(text_words.intersection(self.BULLISH_KEYWORDS))
                        bear_hits = len(text_words.intersection(self.BEARISH_KEYWORDS))

                        for raw_tok in tokens:
                            tok = raw_tok.upper()
                            if tok in self.COMMON_WORDS:
                                continue
                            if tok in self.target_map:
                                full_sym = self.target_map[tok]
                                stats[full_sym]["mentions"] += 1
                                stats[full_sym]["bullish_count"] += (bull_hits + 1 if bull_hits >= bear_hits else 0)
                                stats[full_sym]["bearish_count"] += (bear_hits + 1 if bear_hits > bull_hits else 0)
                                stats[full_sym]["subreddits"].add(sub)
                                if len(stats[full_sym]["sample_titles"]) < 3 and title:
                                    stats[full_sym]["sample_titles"].append(f"[r/{sub}] {title[:90]}")
                except Exception:
                    continue

        results = {}
        for ticker, data in stats.items():
            tot = data["bullish_count"] + data["bearish_count"]
            sent_score = int((data["bullish_count"] / tot * 100)) if tot > 0 else 50
            results[ticker] = {
                "ticker": ticker,
                "mentions": data["mentions"],
                "forum_sentiment_score": sent_score,
                "subreddits": list(data["subreddits"]),
                "sample_titles": data["sample_titles"],
                "scanned_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            }
        return results
