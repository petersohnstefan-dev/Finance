import os
import re
import time
import requests
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict
import datetime

# Reddit blocks the anonymous www.reddit.com/*.json endpoints from most IPs and
# returns 403; old.reddit.com answers 200 but with an HTML interstitial, not JSON.
# The OAuth API still works and is free, so credentials - when present - are the
# only path that actually returns posts.
REDDIT_TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
REDDIT_API_BASE = "https://oauth.reddit.com"
REDDIT_USER_AGENT = os.environ.get(
    "REDDIT_USER_AGENT", "finance-dashboard/1.0 (autonomous market scanner)")

_token_cache: Dict[str, Any] = {"token": None, "expires_at": 0.0}


def reddit_credentials() -> Tuple[Optional[str], Optional[str]]:
    return os.environ.get("REDDIT_CLIENT_ID"), os.environ.get("REDDIT_CLIENT_SECRET")


def get_reddit_token() -> Optional[str]:
    """App-only OAuth token, cached until shortly before it expires."""
    client_id, client_secret = reddit_credentials()
    if not client_id or not client_secret:
        return None
    if _token_cache["token"] and time.time() < _token_cache["expires_at"]:
        return _token_cache["token"]
    try:
        resp = requests.post(
            REDDIT_TOKEN_URL,
            auth=(client_id, client_secret),
            data={"grant_type": "client_credentials"},
            headers={"User-Agent": REDDIT_USER_AGENT},
            timeout=8,
        )
        if resp.status_code != 200:
            print(f"[forum_scanner] Reddit-Token abgelehnt: HTTP {resp.status_code}")
            return None
        payload = resp.json()
        token = payload.get("access_token")
        if not token:
            return None
        _token_cache["token"] = token
        _token_cache["expires_at"] = time.time() + float(payload.get("expires_in", 3600)) - 60
        return token
    except Exception as exc:
        print(f"[forum_scanner] Reddit-Token fehlgeschlagen: {type(exc).__name__}")
        return None


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
        self.last_error: Optional[str] = None
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

        token = get_reddit_token()
        if not token:
            # Without a token every request is a guaranteed 403. Say so once
            # instead of burning eight timeouts per scan and silently reporting
            # zero mentions for every ticker, which is what used to happen.
            has_creds = all(reddit_credentials())
            self.last_error = (
                "Reddit-Zugangsdaten vorhanden, aber abgelehnt - Client-ID/Secret pruefen"
                if has_creds else
                "Keine Reddit-Zugangsdaten (REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET) "
                "- Forum-Sentiment inaktiv")
            print(f"[forum_scanner] {self.last_error}")
            return {}

        headers = {"User-Agent": REDDIT_USER_AGENT, "Authorization": f"bearer {token}"}
        fetched_any = False

        for sub in self.SUBREDDITS:
            for feed in ["hot", "new"]:
                url = f"{REDDIT_API_BASE}/r/{sub}/{feed}?limit={limit_per_sub}"
                try:
                    resp = requests.get(url, headers=headers, timeout=8)
                    if resp.status_code != 200:
                        print(f"[forum_scanner] r/{sub}/{feed}: HTTP {resp.status_code}")
                        continue
                    data = resp.json()
                    posts = (data.get("data") or {}).get("children", [])
                    if posts:
                        fetched_any = True

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

        if not fetched_any:
            self.last_error = "Reddit lieferte keine Posts (Token gültig, aber alle Feeds leer)"
            print(f"[forum_scanner] {self.last_error}")

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
