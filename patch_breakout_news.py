import codecs
import re

with codecs.open('src/breakout_radar.py', 'r', 'utf8') as f:
    content = f.read()

# Update signature
old_sig = 'def analyze_breakout_potential(self, df: pd.DataFrame, fundamentals: Dict[str, Any], forum_mentions: int = 0) -> Dict[str, Any]:'
new_sig = 'def analyze_breakout_potential(self, df: pd.DataFrame, fundamentals: Dict[str, Any], forum_mentions: int = 0, news_sentiment: Dict[str, Any] = None) -> Dict[str, Any]:'
content = content.replace(old_sig, new_sig)

# Add news evaluation logic
news_logic = '''
        # 7. Live-News & Earnings Sentiment
        if news_sentiment:
            n_score = news_sentiment.get("score", 0)
            if n_score > 0:
                score += min(20, n_score * 2)
                bulls = ", ".join(news_sentiment.get("bullish_keywords", []))
                triggers.append({
                    "type": "catalyst",
                    "title": f" Bullische Nachrichtenlage (+{n_score})",
                    "desc": f"Positive Signale in aktuellen News/Quartalszahlen. Keywords: {bulls}"
                })
            elif n_score < 0:
                score -= min(20, abs(n_score) * 2)
                bears = ", ".join(news_sentiment.get("bearish_keywords", []))
                triggers.append({
                    "type": "bearish_catalyst",
                    "title": f" Bearische Nachrichtenlage ({n_score})",
                    "desc": f"Negative Signale in aktuellen News. Keywords: {bears}"
                })

        final_score = min(100, round(score))
'''

if '# 7. Live-News' not in content:
    content = content.replace('        final_score = min(100, round(score))', news_logic)
    
with codecs.open('src/breakout_radar.py', 'w', 'utf8') as f:
    f.write(content)
print("Patched breakout_radar.py")
