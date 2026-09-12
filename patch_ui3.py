with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

start_idx = -1
end_idx = -1
for i, line in enumerate(lines):
    if line.startswith('elif app_mode == "🐋 Whale- & Insider-Radar":'):
        start_idx = i
    if line.startswith('elif app_mode == "🌐 Makro-Klima, Zentralbanken & News":'):
        end_idx = i

if start_idx != -1 and end_idx != -1:
    new_block = [
        'elif app_mode == "🐋 Whale- & Insider-Radar":\n',
        '    st.title("🐋 Live Whale- & Insider-Radar (100% Echte Daten via Yahoo Finance)")\n',
        '    st.markdown("Verfolge die **echten institutionellen Großaktionäre (Whales)** und die aktuellsten **Vorstands-Insiderkäufe** einer Watchlist aus Top-Tech & Krypto Aktien.")\n',
        '\n',
        '    tab_insiders, tab_whales = st.tabs([\n',
        '        "👔 Echte Insiderkäufe (SEC Form 4)",\n',
        '        "🏛️ Institutionelle Großaktionäre (Whales)"\n',
        '    ])\n',
        '    \n',
        '    from src.insider_whale_tracker import LiveInsiderWhaleTracker\n',
        '    \n',
        '    with tab_insiders:\n',
        '        st.subheader("👔 Jüngste Vorstands- & CEO-Insiderkäufe")\n',
        '        st.caption("Live-Daten der SEC Form 4 Meldungen für Top-Tickers (NVDA, TSLA, AAPL, PLTR, Krypto-Miner).")\n',
        '        with st.spinner("Lade Insider-Daten von Yahoo Finance..."):\n',
        '            df_insiders = LiveInsiderWhaleTracker.get_live_insider_transactions()\n',
        '            if not df_insiders.empty:\n',
        '                st.dataframe(df_insiders, use_container_width=True, hide_index=True)\n',
        '            else:\n',
        '                st.info("Keine aktuellen Insider-Daten gefunden.")\n',
        '                \n',
        '    with tab_whales:\n',
        '        st.subheader("🏛️ Die größten institutionellen Wal-Positionen")\n',
        '        st.caption("Die Top 2 Großaktionäre der wichtigsten Tech-Werte (BlackRock, Vanguard, etc.).")\n',
        '        with st.spinner("Lade Whale-Daten von Yahoo Finance..."):\n',
        '            df_whales = LiveInsiderWhaleTracker.get_live_whale_holders()\n',
        '            if not df_whales.empty:\n',
        '                st.dataframe(df_whales, use_container_width=True, hide_index=True)\n',
        '            else:\n',
        '                st.info("Keine aktuellen Whale-Daten gefunden.")\n',
        '\n'
    ]
    with open('app.py', 'w', encoding='utf-8') as f:
        f.writelines(lines[:start_idx] + new_block + lines[end_idx:])
    print('Replaced successfully!')
else:
    print('Could not find bounds.')
