import codecs

with codecs.open('src/data_fetcher.py', 'r', 'utf8') as f:
    content = f.read()

new_method = '''
    def get_insider_sentiment(self) -> Dict[str, Any]:
        """Fetch recent insider transactions and score them."""
        try:
            import math
            insiders = self.ticker.insider_transactions
            if insiders is None or insiders.empty:
                return {'insider_score': 0, 'recent_buys': 0, 'recent_sells': 0}
            
            buys = 0
            sells = 0
            buy_value = 0.0
            
            # Analyze recent trades
            for idx, row in insiders.head(10).iterrows():
                val = row.get('Value', 0)
                if math.isnan(val): val = 0
                txt = str(row.get('Text', '')).lower()
                shares = row.get('Shares', 0)
                
                # Exclude stock gifts which have value 0 or '0.00 per share'
                if val == 0 or '0.00 per share' in txt or 'gift' in txt or 'grant' in txt:
                    continue
                    
                if 'purchase' in txt or 'buy' in txt or 'purchase at price' in txt:
                    buys += 1
                    buy_value += float(val)
                elif 'sale' in txt or 'sell' in txt:
                    sells += 1
            
            # Score
            score = 0
            if buys > 0:
                score += 15 # Heavy boost for actual buys
            if buys >= 2:
                score += 10 # Extra boost for multiple buys
            
            return {
                'insider_score': score,
                'recent_buys': buys,
                'recent_sells': sells,
                'recent_buy_value': buy_value
            }
        except Exception:
            return {'insider_score': 0, 'recent_buys': 0, 'recent_sells': 0}
'''

content = content + new_method
with codecs.open('src/data_fetcher.py', 'w', 'utf8') as f:
    f.write(content)
print('Patched data_fetcher.py')
