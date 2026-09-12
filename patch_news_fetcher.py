import codecs
import re

with codecs.open('src/data_fetcher.py', 'r', 'utf8') as f:
    content = f.read()

news_method = '''
    def get_news_sentiment(self) -> Dict[str, Any]:
        """Analyzes recent news headlines for bullish/bearish catalysts."""
        sentiment_data = {
            "score": 0,
            "bullish_keywords": [],
            "bearish_keywords": [],
            "recent_headlines": []
        }
        try:
            news = self.ticker.news
            if not news:
                return sentiment_data
                
            import re
            BULLISH = [r'\\bbeat', r'\\braise', r'\\bupgrade', r'\\brecord', r'\\bsurge', r'\\bjump', r'\\bsoar', r'\\bprofit', r'\\bbuy', r'\\bpartner', r'\\bgrowth', r'\\bdividend', r'\\bexpansion', r'\\bdemand']
            BEARISH = [r'\\bmiss', r'\\bcut', r'\\bdowngrade', r'\\bplunge', r'\\bslump', r'\\bdrop', r'\\bfall\\b', r'\\bloss', r'\\bsell', r'\\blawsuit', r'\\binvestigat', r'\\bwarn', r'\\bmissed', r'\\btank', r'\\bcrash']
            
            score = 0
            b_found = set()
            bear_found = set()
            headlines = []
            
            for n in news[:5]:
                c = n.get('content') or {}
                title = c.get('title', '')
                summary = c.get('summary', '')
                if title:
                    headlines.append(title)
                
                text = (title + ' ' + summary).lower()
                
                for b in BULLISH:
                    if re.search(b, text):
                        b_found.add(b.replace('\\\\b', ''))
                        score += 2
                for b in BEARISH:
                    if re.search(b, text):
                        bear_found.add(b.replace('\\\\b', ''))
                        score -= 3
                        
            sentiment_data["score"] = score
            sentiment_data["bullish_keywords"] = list(b_found)
            sentiment_data["bearish_keywords"] = list(bear_found)
            sentiment_data["recent_headlines"] = headlines
            
        except Exception as e:
            pass
            
        return sentiment_data
'''

if 'def get_news_sentiment' not in content:
    # Insert it before get_insider_sentiment
    content = content.replace('    def get_insider_sentiment(self) -> Dict[str, Any]:', news_method + '\n    def get_insider_sentiment(self) -> Dict[str, Any]:')
    
    with codecs.open('src/data_fetcher.py', 'w', 'utf8') as f:
        f.write(content)
    print("Added get_news_sentiment to data_fetcher.py")
else:
    print("Method already exists")
