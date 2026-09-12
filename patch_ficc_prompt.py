import sys

with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for i, l in enumerate(lines):
    new_lines.append(l)
    if 'sys_prompt +=' in l and 'pf_data' in l:
        new_lines.append("""
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
""")

with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print('Injected FICC data into chatbot prompt.')
