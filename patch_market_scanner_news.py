import codecs

with codecs.open('src/market_scanner.py', 'r', 'utf8') as f:
    content = f.read()

old_code = '''            short_res = self.short_engine.evaluate(df_with_ind, social_sentiment)
            long_res = self.long_engine.evaluate(fundamentals, consensus)
            synth = self.synthesizer.synthesize(short_res, long_res, fundamentals, consensus)
            breakout_res = self.breakout_radar.analyze_breakout_potential(df_with_ind, fundamentals, mentions)'''

new_code = '''            short_res = self.short_engine.evaluate(df_with_ind, social_sentiment)
            long_res = self.long_engine.evaluate(fundamentals, consensus)
            synth = self.synthesizer.synthesize(short_res, long_res, fundamentals, consensus)
            
            # Fetch Live News Sentiment
            news_sentiment = fetcher.get_news_sentiment()
            
            breakout_res = self.breakout_radar.analyze_breakout_potential(df_with_ind, fundamentals, mentions, news_sentiment)'''

if 'news_sentiment = fetcher.get_news_sentiment()' not in content:
    content = content.replace(old_code, new_code)
    with codecs.open('src/market_scanner.py', 'w', 'utf8') as f:
        f.write(content)
    print("Patched market_scanner.py")
else:
    print("Already patched")
