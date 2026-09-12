import sys

with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

start_idx = -1
for i, l in enumerate(lines):
    if 'with st.expander("📖 Glossar: Was bedeuten die wichtigsten Kennzahlen?"):' in l:
        start_idx = i
        break

if start_idx == -1:
    print("Could not find Glossar")
    sys.exit(1)

injection = """
        if is_breakout_mode:
            st.markdown("---")
            st.subheader("🕰️ Radar-Historie (Was wurde aus vergangenen Signalen?)")
            
            with st.expander("📊 Track-Record der Top-Signale der letzten Tage ansehen"):
                from src.db import PortfolioDB
                pdb = PortfolioDB()
                history_signals = pdb.get_recent_radar_signals(limit=30)
                
                if not history_signals:
                    st.info("Noch keine Radar-Historie vorhanden. Ab dem nächsten Scan werden hier die Verläufe der Top-Signale getrackt.")
                else:
                    st.write("Die folgende Tabelle zeigt die Performance der Top-Ausbruchs-Signale der vergangenen Scans ab dem Zeitpunkt ihrer Erkennung:")
                    
                    hist_data = []
                    unique_syms = list(set([s["symbol"] for s in history_signals]))
                    import yfinance as yf
                    live_prices = {}
                    try:
                        tickers = yf.Tickers(" ".join(unique_syms))
                        for sym in unique_syms:
                            info = tickers.tickers[sym].fast_info
                            if hasattr(info, 'last_price') and info.last_price is not None:
                                live_prices[sym] = info.last_price
                    except Exception:
                        pass
                        
                    for s in history_signals:
                        sym = s["symbol"]
                        sig_p = s["signal_price"]
                        curr_p = live_prices.get(sym, sig_p)
                        ret_pct = ((curr_p - sig_p) / sig_p * 100.0) if sig_p > 0 else 0.0
                        
                        hist_data.append({
                            "Datum": s["detected_at"],
                            "Ticker": sym,
                            "Name": s["name"],
                            "Signal-Kurs": f"{sig_p:.2f}",
                            "Aktueller Kurs": f"{curr_p:.2f}",
                            "Performance": ret_pct,
                            "Score": s.get("score", 0.0)
                        })
                    
                    import pandas as pd
                    df_hist = pd.DataFrame(hist_data)
                    df_hist["Performance (str)"] = df_hist["Performance"].apply(lambda x: f"{x:+.2f}%")
                    
                    def color_ret(val):
                        if isinstance(val, str) and "%" in val:
                            try:
                                num = float(val.replace("%", ""))
                                if num > 0: return "color: #34d399; font-weight: bold;"
                                elif num < 0: return "color: #f87171;"
                            except:
                                pass
                        return ""

                    st.dataframe(
                        df_hist[["Datum", "Ticker", "Name", "Score", "Signal-Kurs", "Aktueller Kurs", "Performance (str)"]].style.map(color_ret, subset=["Performance (str)"]),
                        use_container_width=True,
                        hide_index=True
                    )

"""

lines.insert(start_idx, injection)

with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
    
print("Injected history section")
