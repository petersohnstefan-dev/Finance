import yfinance as yf
import pandas as pd
import requests
from typing import Dict, Any, Optional

class FinancialDataFetcher:
    """Fetches market data, fundamentals, short interest, analyst ratings, and news."""

    def __init__(self, ticker_symbol: str):
        self.raw_ticker = ticker_symbol.strip().upper()
        self.ticker = yf.Ticker(self.raw_ticker)

    def get_historical_prices(self, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
        """Fetch historical OHLCV price data."""
        df = self.ticker.history(period=period, interval=interval)
        if df.empty:
            raise ValueError(f"Keine Kursdaten für Ticker '{self.raw_ticker}' gefunden. Bitte Symbol prüfen.")
        return df

    @staticmethod
    def _normalize_percent(val: Optional[float]) -> Optional[float]:
        """Normalizes percentage to 0.0 - 100.0 scale."""
        if val is None:
            return None
        return val * 100.0 if abs(val) <= 1.0 else val

    def get_fundamentals(self) -> Dict[str, Any]:
        """Fetch key fundamental data, valuation, and short interest metrics."""
        info = self.ticker.info or {}
        
        current_price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose")
        
        free_cashflow = info.get("freeCashflow")
        market_cap = info.get("marketCap")
        fcf_yield = None
        if free_cashflow and market_cap and market_cap > 0:
            fcf_yield = (free_cashflow / market_cap) * 100.0

        raw_div = info.get("dividendYield")
        div_yield_pct = self._normalize_percent(raw_div)
        roe_pct = self._normalize_percent(info.get("returnOnEquity"))
        pm_pct = self._normalize_percent(info.get("profitMargins"))
        gm_pct = self._normalize_percent(info.get("grossMargins"))
        om_pct = self._normalize_percent(info.get("operatingMargins"))

        dte = info.get("debtToEquity")
        if dte is not None and dte > 10.0:
            dte = dte / 100.0

        # Short Interest Metrics
        short_float = self._normalize_percent(info.get("shortPercentOfFloat"))
        short_ratio = info.get("shortRatio")  # Days to cover
        shares_short = info.get("sharesShort")
        shares_short_prior = info.get("sharesShortPriorMonth")
        short_shares_out = self._normalize_percent(info.get("sharesPercentSharesOut"))
        
        short_change_pct = None
        if shares_short and shares_short_prior and shares_short_prior > 0:
            short_change_pct = ((shares_short - shares_short_prior) / shares_short_prior) * 100.0

        # Calculate Short Squeeze Potential Score (0 - 100)
        squeeze_score = 10.0
        if short_float is not None:
            if short_float >= 25.0:
                squeeze_score += 45.0
            elif short_float >= 15.0:
                squeeze_score += 30.0
            elif short_float >= 8.0:
                squeeze_score += 15.0
        
        if short_ratio is not None:
            if short_ratio >= 8.0:
                squeeze_score += 35.0
            elif short_ratio >= 5.0:
                squeeze_score += 20.0
            elif short_ratio >= 3.0:
                squeeze_score += 10.0

        if short_change_pct and short_change_pct > 10.0:
            squeeze_score += 10.0

        squeeze_score = min(100.0, squeeze_score)

        fundamentals = {
            "symbol": self.raw_ticker,
            "shortName": info.get("shortName") or info.get("longName") or self.raw_ticker,
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "currency": info.get("currency", "USD"),
            "currentPrice": current_price,
            "marketCap": market_cap,
            "trailingPE": info.get("trailingPE"),
            "forwardPE": info.get("forwardPE"),
            "pegRatio": info.get("pegRatio"),
            "priceToBook": info.get("priceToBook"),
            "priceToSales": info.get("priceToSalesTrailing12Months"),
            "enterpriseToEbitda": info.get("enterpriseToEbitda"),
            "profitMargins": pm_pct,
            "operatingMargins": om_pct,
            "grossMargins": gm_pct,
            "returnOnEquity": roe_pct,
            "returnOnAssets": self._normalize_percent(info.get("returnOnAssets")),
            "debtToEquity": dte,
            "currentRatio": info.get("currentRatio"),
            "quickRatio": info.get("quickRatio"),
            "freeCashflow": free_cashflow,
            "fcfYield": fcf_yield,
            "dividendYield": div_yield_pct,
            "payoutRatio": self._normalize_percent(info.get("payoutRatio")),
            "beta": info.get("beta"),
            "fiftyTwoWeekHigh": info.get("fiftyTwoWeekHigh"),
            "fiftyTwoWeekLow": info.get("fiftyTwoWeekLow"),
            "fiftyDayAverage": info.get("fiftyDayAverage"),
            "twoHundredDayAverage": info.get("twoHundredDayAverage"),
            "revenueGrowth": self._normalize_percent(info.get("revenueGrowth")),
            "earningsGrowth": self._normalize_percent(info.get("earningsGrowth")),
            
            # Short Data
            "shortPercentOfFloat": short_float,
            "shortRatio": short_ratio,
            "sharesShort": shares_short,
            "sharesShortPriorMonth": shares_short_prior,
            "shortChangePct": short_change_pct,
            "shortPercentSharesOut": short_shares_out,
            "squeezeScore": round(squeeze_score, 1)
        }
        return fundamentals

    def get_analyst_consensus(self) -> Dict[str, Any]:
        """Fetch analyst recommendations, price targets and upside potential."""
        info = self.ticker.info or {}
        current_price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose") or 0.0

        target_mean = info.get("targetMeanPrice")
        target_high = info.get("targetHighPrice")
        target_low = info.get("targetLowPrice")
        target_median = info.get("targetMedianPrice")

        upside_mean_pct = None
        if target_mean and current_price and current_price > 0:
            upside_mean_pct = ((target_mean - current_price) / current_price) * 100.0

        consensus = {
            "targetMeanPrice": target_mean,
            "targetHighPrice": target_high,
            "targetLowPrice": target_low,
            "targetMedianPrice": target_median,
            "upsideMeanPct": upside_mean_pct,
            "recommendationKey": info.get("recommendationKey", "none"),
            "recommendationMean": info.get("recommendationMean"),
            "numberOfAnalystOpinions": info.get("numberOfAnalystOpinions")
        }
        return consensus

    def get_news(self, limit: int = 6) -> list:
        """Fetch recent news headlines and links."""
        try:
            news = self.ticker.news or []
            cleaned_news = []
            for item in news[:limit]:
                content = item.get("content") if isinstance(item.get("content"), dict) else item
                title = content.get("title") or item.get("title")
                publisher = (content.get("provider") or {}).get("displayName") if isinstance(content.get("provider"), dict) else item.get("publisher", "")
                link = (content.get("canonicalUrl") or {}).get("url") if isinstance(content.get("canonicalUrl"), dict) else item.get("link", "")
                pub_date = content.get("pubDate") or item.get("providerPublishTime")

                if title:
                    cleaned_news.append({
                        "title": title,
                        "publisher": publisher,
                        "link": link,
                        "published": pub_date
                    })
            return cleaned_news
        except Exception:
            return []

    def get_social_sentiment(self) -> Dict[str, Any]:
        """Fetch social sentiment indicators from StockTwits or fallback."""
        symbol = self.raw_ticker.split(".")[0]
        url = f"https://api.stocktwits.com/api/2/streams/symbol/{symbol}.json"
        try:
            resp = requests.get(url, timeout=4, headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code == 200:
                data = resp.json()
                messages = data.get("messages", [])
                bullish = 0
                bearish = 0
                for msg in messages:
                    sentiment = (msg.get("entities") or {}).get("sentiment") or {}
                    basic = sentiment.get("basic")
                    if basic == "Bullish":
                        bullish += 1
                    elif basic == "Bearish":
                        bearish += 1
                total = bullish + bearish
                bull_ratio = (bullish / total * 100.0) if total > 0 else 50.0
                return {
                    "available": True,
                    "bullish_count": bullish,
                    "bearish_count": bearish,
                    "bullish_pct": bull_ratio,
                    "total_analyzed_messages": len(messages)
                }
        except Exception:
            pass
        return {"available": False, "bullish_pct": 50.0, "reason": "No direct feed or EU ticker"}
