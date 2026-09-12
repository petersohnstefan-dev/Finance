import codecs
import re

with codecs.open('src/market_scanner.py', 'r', 'utf8') as f:
    content = f.read()

def replacer_eval(match):
    return match.group(0) + '''
            # Fetch and apply insider sentiment
            insider_data = fetcher.get_insider_sentiment()
            if insider_data['insider_score'] > 0:
                synth["total_score"] += insider_data['insider_score']
                breakout_res["breakout_score"] += insider_data['insider_score']
                if "triggers" not in breakout_res:
                    breakout_res["triggers"] = []
                breakout_res["triggers"].append({
                    "title": f"Insider Kauf (Wert: ${insider_data['recent_buy_value']:,.0f})",
                    "desc": f"Insgesamt {insider_data['recent_buys']} aktuelle Kaeufe von Insidern registriert."
                })'''

content = re.sub(r'breakout_res = self\.breakout_radar\.analyze_breakout_potential\(df_with_ind, fundamentals, mentions\)', replacer_eval, content)

def replacer_dict(match):
    return match.group(0) + '''
                "insider_score": insider_data.get("insider_score", 0),
                "recent_insider_buys": insider_data.get("recent_buys", 0),'''

content = re.sub(r'"sample_forum_posts": f_info\.get\("sample_titles", \[\]\),', replacer_dict, content)

with codecs.open('src/market_scanner.py', 'w', 'utf8') as f:
    f.write(content)
print("Patched market_scanner.py with regex!")
