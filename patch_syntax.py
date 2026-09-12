import sys

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_block = """                    try:
                        import json
                        with open("data/portfolios.json", "r", encoding="utf-8") as f:
                            pf_data = json.load(f)
                        sys_prompt += "\\n\\nHier ist der aktuelle Zustand der Musterdepots und die Transaktionshistorie (Käufe/Verkäufe) als JSON, damit du konkrete Fragen zu ausgeführten Trades beantworten kannst:\\n" + json.dumps(pf_data)

                    try:
                        from src.bonds_yields_radar import BondYieldsIntelEngine
                        from src.commodities_forex_radar import CommoditiesIntelEngine
                        b_data = BondYieldsIntelEngine.get_bond_market_overview()
                        pm_data = CommoditiesIntelEngine.get_precious_metals_overview()
                        b_hist_df = BondYieldsIntelEngine.get_historical_bond_chart_data(period="1mo")
                        hist_text = "Keine Daten"
                        if not b_hist_df.empty:
                            hist_text = str(b_hist_df.tail(7)['us_10y_yield'].to_dict())
                        sys_prompt += "\\n\\nLIVE MARKT-DATEN:\\n"
                        sys_prompt += f"- US 10-Jahres-Rendite: {b_data['us_10y_yield']:.2f}%\\n"
                        sys_prompt += f"- Historie 10Y Rendite (letzte 7 Tage): {hist_text}\\n"
                        sys_prompt += f"- US 2-Jahres-Rendite: {b_data['us_2y_yield']:.2f}%\\n"
                        sys_prompt += f"- Zinsstruktur (10Y-2Y Spread): {b_data['spread_10y_2y_bps']:.1f} Bps ({b_data['curve_regime']})\\n"
                        sys_prompt += f"- Goldpreis: ${pm_data['gold_price']:.2f}\\n"
                        sys_prompt += f"- Silberpreis: ${pm_data['silver_price']:.2f}\\n"
                    except Exception as e:
                        pass
                    except:
                        pass"""

new_block = """                    try:
                        import json
                        with open("data/portfolios.json", "r", encoding="utf-8") as f:
                            pf_data = json.load(f)
                        sys_prompt += "\\n\\nHier ist der aktuelle Zustand der Musterdepots und die Transaktionshistorie (Käufe/Verkäufe) als JSON, damit du konkrete Fragen zu ausgeführten Trades beantworten kannst:\\n" + json.dumps(pf_data)
                    except:
                        pass

                    try:
                        from src.bonds_yields_radar import BondYieldsIntelEngine
                        from src.commodities_forex_radar import CommoditiesIntelEngine
                        b_data = BondYieldsIntelEngine.get_bond_market_overview()
                        pm_data = CommoditiesIntelEngine.get_precious_metals_overview()
                        b_hist_df = BondYieldsIntelEngine.get_historical_bond_chart_data(period="1mo")
                        hist_text = "Keine Daten"
                        if not b_hist_df.empty:
                            hist_text = str(b_hist_df.tail(7)['us_10y_yield'].to_dict())
                        sys_prompt += "\\n\\nLIVE MARKT-DATEN:\\n"
                        sys_prompt += f"- US 10-Jahres-Rendite: {b_data['us_10y_yield']:.2f}%\\n"
                        sys_prompt += f"- Historie 10Y Rendite (letzte 7 Tage): {hist_text}\\n"
                        sys_prompt += f"- US 2-Jahres-Rendite: {b_data['us_2y_yield']:.2f}%\\n"
                        sys_prompt += f"- Zinsstruktur (10Y-2Y Spread): {b_data['spread_10y_2y_bps']:.1f} Bps ({b_data['curve_regime']})\\n"
                        sys_prompt += f"- Goldpreis: ${pm_data['gold_price']:.2f}\\n"
                        sys_prompt += f"- Silberpreis: ${pm_data['silver_price']:.2f}\\n"
                    except Exception as e:
                        pass"""

content = content.replace(old_block, new_block)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched app.py try/except syntax error.")
