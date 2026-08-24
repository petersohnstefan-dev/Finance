import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import datetime
import os

from config import WATCHLISTS
from src.data_fetcher import FinancialDataFetcher
from src.indicators import calculate_technical_indicators
from src.short_term_engine import ShortTermEngine
from src.long_term_engine import LongTermEngine
from src.synthesis import DecisionSynthesizer
from src.breakout_radar import BreakoutRadar
from src.market_scanner import MarketScanner, load_cached_market_scan
from src.universe import CATEGORIZED_UNIVERSES
from src.portfolio import PortfolioManager
from src.macro_scanner import MacroScanner
from src.insider_whale_tracker import WhaleInsiderTracker
from src.advanced_intelligence import (
    MasterIntelligenceHub, OptionsDarkPoolEngine, BaFinShortRegister,
    EarningsRevisionEngine, EarningsCallAnalyzer, FREDMacroEngine, CryptoOnChainEngine
)

# Page Configuration
st.set_page_config(
    page_title="AI Börsen-Entscheidungs-System",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Clean & High-Legibility Styling
st.markdown("""
<style>
    /* Metric Cards */
    div[data-testid="metric-container"] {
        background-color: #1a1e29;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 12px 16px;
    }

    /* Buttons with high legibility */
    div[data-testid="stButton"] > button {
        background-color: #0284c7 !important;
        color: #ffffff !important;
        border: 1px solid #38bdf8 !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 15px !important;
        padding: 8px 16px !important;
        min-height: 42px !important;
    }
    div[data-testid="stButton"] > button:hover {
        background-color: #0369a1 !important;
        border-color: #7dd3fc !important;
    }

    /* Sidebar Navigation - Crystal Clear White Text */
    section[data-testid="stSidebar"] {
        background-color: #111827 !important;
    }
    section[data-testid="stSidebar"] .stRadio label p {
        font-size: 15px !important;
        font-weight: 500 !important;
        color: #f8fafc !important;
    }
    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] h3 {
        color: #38bdf8 !important;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- SIDEBAR NAVIGATION -----------------
st.sidebar.title("📈 Börsen-System")

app_mode = st.sidebar.radio(
    "Hauptmenü",
    [
        "🏆 Markt-Screener & Top-Rankings", 
        "🚨 Ausbruchs- & Katalysator-Radar",
        "🔮 Smart-Money & Makro-Radar (6 Module)",
        "🐋 Whale- & Insider-Radar",
        "🌐 Makro-Klima, Zentralbanken & News",
        "💼 Musterdepots & Live-Performance (3x 10.000 €)",
        "🔍 Einzelaktien-Tiefenanalyse"
    ],
    index=0
)

st.sidebar.markdown("---")

# ==============================================================================
# MODE 1 & 2: MARKT-SCREENER / AUSBRUCHS-RADAR
# ==============================================================================
if app_mode in ["🏆 Markt-Screener & Top-Rankings", "🚨 Ausbruchs- & Katalysator-Radar"]:
    is_breakout_mode = (app_mode == "🚨 Ausbruchs- & Katalysator-Radar")
    
    if is_breakout_mode:
        st.title("🚨 Ausbruchs- & Katalysator-Radar (Leerverkäufer, Squeezes & Volumen)")
        st.markdown("Erkennt **hohe Leerverkäufer-Quoten (Short Interest)**, **Volumen-Schocks** und **Volatilitäts-Kompression (Bollinger Squeeze)** – die Zündfunken für plötzliche Rallyes.")
    else:
        st.title("🏆 Markt-Screener & Ranglisten (USA, Deutschland & Europa)")
        st.markdown("Automatisierte Auswertung über **SDAX-Nebenwerte, US-Mid-Caps, Biotech & Large-Caps**.")

    # Load Cached Data
    scan_data = load_cached_market_scan()
    
    col_scan_btn, col_info = st.columns([1, 3])
    with col_scan_btn:
        if st.button("🔄 Markt jetzt neu scannen", use_container_width=True):
            with st.spinner("Scanne Foren, Leerverkäufer-Daten und 130+ Aktien..."):
                scanner = MarketScanner()
                scanner.run_full_scan()
                st.success("Markt-Scan erfolgreich aktualisiert!")
                st.rerun()

    with col_info:
        if scan_data:
            st.caption(f"🕒 Letzter vollständiger Scan: **{scan_data.get('scan_time')}** | Analysierte Aktien: **{scan_data.get('total_scanned')}** (inkl. Leerverkäufer-Daten & SDAX)")
        else:
            st.warning("Noch kein Scan vorhanden. Klicke auf 'Markt jetzt neu scannen'.")

    if scan_data and "data" in scan_data:
        raw_list = scan_data["data"]
        df_scan = pd.DataFrame(raw_list)

        # Ensure all expected columns exist safely
        expected_cols = [
            "symbol", "name", "region", "sector", "price", "currency", 
            "total_score", "short_score", "long_score", "breakout_score", 
            "breakout_status", "vol_ratio", "daily_return_pct", "short_float", 
            "short_ratio", "squeeze_score", "action", "action_desc", "rsi", 
            "pe", "roe", "forum_mentions", "upside_pct"
        ]
        for col in expected_cols:
            if col not in df_scan.columns:
                df_scan[col] = None

        # Filters
        st.markdown("### 🎯 Filter & Fokus")
        f_col1, f_col2, f_col3 = st.columns(3)
        
        with f_col1:
            region_filter = st.selectbox("Asset-Klasse / Region", ["Alle", "🪙 Krypto", "🥇 Edelmetalle", "🛢️ Rohstoffe", "USA", "Deutschland", "Europa"])
        with f_col2:
            if is_breakout_mode:
                ranking_mode = st.selectbox(
                    "Ausbruchs-Fokus",
                    [
                        "🚨 Höchster Ausbruchs-Score (Volumen & Dynamik)",
                        "🪤 Höchste Leerverkäufer-Quote (% Short Float / Squeeze)",
                        "⏳ Längste Eindeckungsdauer (Days to Cover)",
                        "🔥 Höchster Foren-Buzz / Sentiment (Reddit/Social)"
                    ]
                )
            else:
                ranking_mode = st.selectbox(
                    "Ranking-Kriterium",
                    [
                        "🚀 Top Gesamt-Score (Allround-Favoriten)",
                        "⚡ Beste Kurz-/Mittelfrist-Chancen (Momentum/Swing)",
                        "🏛️ Beste Langfrist-Werte (Value/Qualität)",
                        "🪤 Höchste Short-Quote (% Leerverkäufer)",
                        "🎯 Höchstes Analysten-Kurspotenzial (%)",
                        "🔥 Höchster Foren-Buzz / Sentiment (Reddit/Social)"
                    ]
                )
        with f_col3:
            min_score = st.slider("Mindest-Score", 0, 100, 30 if is_breakout_mode else 50)

        # Apply Region Filter
        if region_filter != "Alle":
            df_scan = df_scan[df_scan["region"] == region_filter]

        # Sorting Logic
        if "Ausbruchs-Score" in ranking_mode:
            df_scan = df_scan[df_scan["breakout_score"].fillna(0) >= min_score]
            df_scan = df_scan.sort_values(by=["breakout_score", "vol_ratio"], ascending=[False, False])
        elif "Leerverkäufer-Quote" in ranking_mode or "Short-Quote" in ranking_mode:
            df_scan = df_scan.sort_values(by="short_float", ascending=False, na_position="last")
        elif "Eindeckungsdauer" in ranking_mode:
            df_scan = df_scan.sort_values(by="short_ratio", ascending=False, na_position="last")
        elif "Gesamt-Score" in ranking_mode:
            df_scan = df_scan[df_scan["total_score"].fillna(0) >= min_score]
            df_scan = df_scan.sort_values(by="total_score", ascending=False)
        elif "Kurz-/Mittelfrist" in ranking_mode:
            df_scan = df_scan[df_scan["short_score"].fillna(0) >= min_score]
            df_scan = df_scan.sort_values(by="short_score", ascending=False)
        elif "Langfrist" in ranking_mode:
            df_scan = df_scan[df_scan["long_score"].fillna(0) >= min_score]
            df_scan = df_scan.sort_values(by="long_score", ascending=False)
        elif "Analysten" in ranking_mode:
            df_scan = df_scan.sort_values(by="upside_pct", ascending=False, na_position="last")
        elif "Foren-Buzz" in ranking_mode:
            df_scan = df_scan.sort_values(by=["forum_mentions", "short_score"], ascending=[False, False])

        # Top 3 Highlight Cards
        st.markdown("---")
        st.subheader("🥇 Top-3 Auswertungen")
        top3_cols = st.columns(3)
        top3_data = df_scan.head(3).to_dict("records")
        
        for idx, item in enumerate(top3_data):
            with top3_cols[idx]:
                badge = "🥇 #1" if idx == 0 else ("🥈 #2" if idx == 1 else "🥉 #3")
                curr = item.get("currency", "USD")
                p = item.get("price") or 0
                sf = item.get("short_float")
                sf_str = f"{sf:.1f}%" if sf is not None else "N/A"
                
                score_display = (
                    f"Ausbruch: <b style='color:#f43f5e;'>{item.get('breakout_score', 0)}/100</b> | Short Float: <b style='color:#fbbf24;'>{sf_str}</b>"
                    if is_breakout_mode else
                    f"Gesamt: <b style='color:#38bdf8;'>{item.get('total_score')}</b> | Kurz: <b style='color:#a78bfa;'>{item.get('short_score')}</b> | Lang: <b style='color:#34d399;'>{item.get('long_score')}</b>"
                )

                st.markdown(f"""
                <div style="background-color: #1a1e29; border: 1px solid {'#f43f5e' if is_breakout_mode else '#38bdf8'}; border-radius: 10px; padding: 15px; margin-bottom: 10px;">
                    <div style="font-size: 14px; color: #38bdf8; font-weight: bold;">{badge} • {item.get('region')} ({item.get('sector', 'N/A')})</div>
                    <h3 style="margin: 4px 0 2px 0; color: white;">{item.get('name')} ({item.get('symbol')})</h3>
                    <div style="font-size: 20px; font-weight: bold; color: #f59e0b;">{p:.2f} {curr}</div>
                    <div style="margin: 10px 0; padding: 6px; background-color: #242b3d; border-radius: 6px; font-size: 13px;">
                        <b>{item.get('breakout_status' if is_breakout_mode else 'action')}</b>
                    </div>
                    <div style="font-size: 13px; color: #bbb;">
                        {score_display}
                    </div>
                    <div style="margin-top: 8px; font-size: 12px; color: #888;">
                        Analysten-Ziel: <b>{item.get('upside_pct', 0):+.1f}%</b> | RSI: <b>{item.get('rsi', 50):.1f}</b>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # Full Interactive Table with Compact Columns & Hover Tooltips
        st.markdown("---")
        st.subheader("📋 Vollständige Ranking-Tabelle")
        st.caption("💡 Fahre mit der Maus über die Spaltentitel für Erklärungen zu jeder Kennzahl.")
        
        if is_breakout_mode:
            display_df = df_scan[[
                "symbol", "name", "price", "currency", 
                "breakout_score", "short_float", "short_ratio", "vol_ratio", "daily_return_pct", 
                "rsi", "breakout_status"
            ]].copy()
            
            display_df.columns = [
                "Ticker", "Name", "Kurs", "Währung",
                "Ausbruch", "Short %", "DaysToCover", "Vol-Faktor", "Heute %",
                "RSI", "Status"
            ]

            display_df["Kurs"] = display_df["Kurs"].apply(lambda x: f"{x:.2f}" if pd.notnull(x) else "N/A")
            display_df["Short %"] = display_df["Short %"].apply(lambda x: f"{x:.1f}%" if pd.notnull(x) else "N/A")
            display_df["DaysToCover"] = display_df["DaysToCover"].apply(lambda x: f"{x:.1f}T" if pd.notnull(x) else "N/A")
            display_df["Vol-Faktor"] = display_df["Vol-Faktor"].apply(lambda x: f"{x:.1f}x" if pd.notnull(x) else "1.0x")
            display_df["Heute %"] = display_df["Heute %"].apply(lambda x: f"{x:+.1f}%" if pd.notnull(x) else "0.0%")
            display_df["RSI"] = display_df["RSI"].apply(lambda x: f"{x:.0f}" if pd.notnull(x) else "N/A")

            col_cfg = {
                "Ticker": st.column_config.TextColumn("Ticker", help="Börsenkürzel der Aktie (z. B. MRNA, SDF.DE)"),
                "Name": st.column_config.TextColumn("Name", help="Name des Unternehmens"),
                "Kurs": st.column_config.TextColumn("Kurs", help="Aktueller Kurs in jeweiliger Währung"),
                "Währung": st.column_config.TextColumn("Währung", help="Handelswährung (USD / EUR / CHF / GBP)"),
                "Ausbruch": st.column_config.NumberColumn("Ausbruch", help="Ausbruchs-Score (0-100): Berechnet aus Volumenschock, Bollinger-Squeeze, RSI-Dynamik und Short-Quote"),
                "Short %": st.column_config.TextColumn("Short %", help="Short Float (%): Anteil der frei handelbaren Aktien, die leerverkauft sind. Ab >15% herrscht akute Short-Squeeze-Gefahr!"),
                "DaysToCover": st.column_config.TextColumn("Days to Cover", help="Wie viele volle Handelstage die Leerverkäufer bräuchten, um bei normalem Volumen alle Positionen zurückzukaufen."),
                "Vol-Faktor": st.column_config.TextColumn("Volumen", help="Tagesvolumen im Vergleich zum 20-Tage-Schnitt. >2.0x bedeutet ungewöhnliche Aktivitäten!"),
                "Heute %": st.column_config.TextColumn("Heute %", help="Heutige Kursveränderung in Prozent"),
                "RSI": st.column_config.TextColumn("RSI", help="Relative Strength Index (14T): 55-75 = Momentum-Zündung, >75 = Überhitzt"),
                "Status": st.column_config.TextColumn("Status", help="KI-Klassifikation des Ausbruchszustands")
            }

        else:
            display_df = df_scan[[
                "symbol", "name", "price", "currency", 
                "total_score", "short_score", "long_score", "short_float", 
                "upside_pct", "rsi", "pe", "action"
            ]].copy()
            
            display_df.columns = [
                "Ticker", "Name", "Kurs", "Währung",
                "Gesamt", "Kurz", "Lang", "Short %",
                "Ziel %", "RSI", "KGV", "Handlungsempfehlung"
            ]

            display_df["Kurs"] = display_df["Kurs"].apply(lambda x: f"{x:.2f}" if pd.notnull(x) else "N/A")
            display_df["Short %"] = display_df["Short %"].apply(lambda x: f"{x:.1f}%" if pd.notnull(x) else "-")
            display_df["Ziel %"] = display_df["Ziel %"].apply(lambda x: f"{x:+.1f}%" if pd.notnull(x) else "N/A")
            display_df["RSI"] = display_df["RSI"].apply(lambda x: f"{x:.0f}" if pd.notnull(x) else "N/A")
            display_df["KGV"] = display_df["KGV"].apply(lambda x: f"{x:.1f}" if pd.notnull(x) else "N/A")

            col_cfg = {
                "Ticker": st.column_config.TextColumn("Ticker", help="Börsenkürzel der Aktie"),
                "Name": st.column_config.TextColumn("Name", help="Name des Unternehmens"),
                "Kurs": st.column_config.TextColumn("Kurs", help="Aktueller Kurs"),
                "Währung": st.column_config.TextColumn("Währung", help="Handelswährung"),
                "Gesamt": st.column_config.NumberColumn("Gesamt", help="Gesamt-Score (0-100): Gewichtete Kombination aus 40% Kurzfrist-Momentum & 60% Langfrist-Qualität"),
                "Kurz": st.column_config.NumberColumn("Kurz", help="Kurzfrist-Score (0-100): Charttechnik, RSI, MACD, Trend & Social Sentiment"),
                "Lang": st.column_config.NumberColumn("Lang", help="Langfrist-Score (0-100): KGV, PEG, Rentabilität (ROE), Verschuldung & Bilanzen"),
                "Short %": st.column_config.TextColumn("Short %", help="Short Float (%): Anteil des Streubesitzes, der leerverkauft ist"),
                "Ziel %": st.column_config.TextColumn("Ziel %", help="Kurspotenzial in % basierend auf dem durchschnittlichen Analysten-Kursziel"),
                "RSI": st.column_config.TextColumn("RSI", help="RSI (14 Tage): <30 = Überverkauft (Kaufchance), >70 = Überkauft, 45-65 = Stabiler Trend"),
                "KGV": st.column_config.TextColumn("KGV", help="Kurs-Gewinn-Verhältnis: <15 = Günstig (Value), 15-25 = Fair, >40 = Teuer"),
                "Handlungsempfehlung": st.column_config.TextColumn("Empfehlung", help="Synthetisierte Handlungsempfehlung der KI")
            }

        st.dataframe(
            display_df,
            column_config=col_cfg,
            use_container_width=True,
            hide_index=True,
            height=500
        )

        # Expandable Glossary for all metrics
        with st.expander("📖 Glossar: Was bedeuten die wichtigsten Kennzahlen?"):
            g_col1, g_col2 = st.columns(2)
            with g_col1:
                st.markdown("""
                - **Gesamt-Score (0–100)**: Synthese aus Charttechnik (40%) und Fundamentaldaten (60%).
                - **Kurzfrist-Score**: Misst Trendstärke (EMA 20/50/200), RSI-Momentum und Foren-Stimmung.
                - **Langfrist-Score**: Misst Bewertungs-Multiples (KGV, PEG), Eigenkapitalrendite (ROE) und Bilanzen.
                - **RSI (Relative Strength Index)**: Misst Überhitzung. Unter 30 gilt als überverkauft (Rebound-Chance), über 70 als überkauft.
                - **KGV (Kurs-Gewinn-Verhältnis)**: Wie oft der Jahresgewinn im Kurs steckt. Unter 15 gilt historisch als günstig.
                """)
            with g_col2:
                st.markdown("""
                - **Short Float (%)**: Prozentualer Anteil der frei handelbaren Aktien, die von Leerverkäufern geliehen & leerverkauft wurden. Ab >15% herrscht hohe Short-Squeeze-Gefahr!
                - **Days to Cover (Short Ratio)**: Wie viele Tage an normalem Volumen nötig wären, um alle Leerverkäufe glattzustellen. >5 Tage = Schwer eindeckbar für Bären.
                - **Volumen-Faktor**: Aktuelles Handelsvolumen geteilt durch 20-Tage-Schnitt. >2.0x = Ungewöhnlich starkes Interesse.
                - **Ziel % (Analysten)**: Differenz zwischen dem mittleren 12-Monats-Kursziel der Profi-Analysten und dem aktuellen Kurs.
                """)

        st.info("💡 **Tipp**: Wähle links '🔍 Einzelaktien-Tiefenanalyse', um jede Aktie im interaktiven Chart und mit allen Details anzusehen.")

# ==============================================================================
# MODE 3: SMART-MONEY & MAKRO-RADAR (6 MODULE)
# ==============================================================================
elif app_mode == "🔮 Smart-Money & Makro-Radar (6 Module)":
    st.title("🔮 Institutionelles Smart-Money & Makro-Radar (6 Module)")
    st.markdown("Die **6 quantitativen Informationsquellen führender Hedgefonds** für maximale Entscheidungstrefferquote.")

    tab_m1, tab_m2, tab_m3, tab_m4, tab_m5, tab_m6 = st.tabs([
        "🎯 1. Optionen-Fluss & Dark Pools",
        "🏛️ 2. BaFin Leerverkäufer (DE/EU)",
        "📈 3. Earnings-Revisionen (EPS)",
        "🎙️ 4. Earnings-Call KI-Tonalität",
        "🌐 5. FRED-Makro & Zinskurve",
        "⛓️ 6. Krypto On-Chain & Whales"
    ])

    # Module 1: Options Flow
    with tab_m1:
        st.subheader("🎯 Ungewöhnlicher Options-Fluss & Dark Pool Großblöcke")
        st.caption("Echtzeit-Tracking von institutionellen Call-Sweeps weit aus dem Geld und außerbörslichen Dark-Pool-Transaktionen.")
        
        opt_alerts = OptionsDarkPoolEngine.get_top_unusual_options_alerts()
        o_df = pd.DataFrame(opt_alerts)
        
        display_o = o_df[["symbol", "name", "type", "strike", "expiry", "premium", "put_call_ratio", "signal"]].copy()
        display_o.columns = ["Ticker", "Unternehmen", "Order-Typ", "Strike", "Verfall", "Prämie", "Put/Call", "KI-Signal"]
        
        st.dataframe(display_o, use_container_width=True, hide_index=True)
        st.info("💡 **Smart-Money-Regel**: Ein stark fallendes Put/Call-Verhältnis (< 0.5) bei gleichzeitig explodierendem Call-Volumen ist das stärkste Vorab-Signal für anstehende Kurssprünge.")

    # Module 2: BaFin Shorts
    with tab_m2:
        st.subheader("🏛️ Offizielles BaFin & Bundesanzeiger Leerverkäufer-Register (Deutschland & Europa)")
        st.caption("Tagesgenaue Netto-Leerverkaufspositionen meldepflichtiger Hedgefonds (ab 0,5% des Aktienkapitals).")
        
        bafin_shorts = BaFinShortRegister.get_official_shorts()
        b_df = pd.DataFrame(bafin_shorts)
        
        display_b = b_df[["symbol", "name", "hedge_fund", "short_pct", "change", "date", "status"]].copy()
        display_b["short_pct"] = display_b["short_pct"].apply(lambda x: f"{x:.2f}%")
        display_b["change"] = display_b["change"].apply(lambda x: f"{x:+.2f}%")
        display_b.columns = ["Ticker", "Unternehmen", "Hedgefonds", "Aktuelle Short-Quote", "Veränderung", "Meldedatum", "Squeeze-Status"]
        
        st.dataframe(display_b, use_container_width=True, hide_index=True)
        st.warning("🚨 **Squeeze-Signal**: Wenn aggressive Hedgefonds wie Marshall Wace oder Citadel beginnen, Positionen rasch zu reduzieren (negative Veränderung), entsteht oft eine gewaltige Short-Squeeze-Rallye.")

    # Module 3: Earnings Revisions
    with tab_m3:
        st.subheader("📈 Gewinnschätzungs-Revisionen (Analyst EPS Momentum)")
        st.caption("Unternehmen, deren Umsatz- und Gewinnschätzungen in den letzten 30 Tagen von der Wall Street systematisch nach oben korrigiert wurden.")
        
        rev_sample = ["NVDA", "PLTR", "SAP.DE", "DUOL", "MUV2.DE", "MRNA", "ADBE", "RIVN"]
        rev_data = [EarningsRevisionEngine.get_revision_metrics(sym) for sym in rev_sample]
        r_df = pd.DataFrame(rev_data)
        
        display_r = r_df[["symbol", "revision_score", "upgrades_last_30d", "downgrades_last_30d", "eps_beat_rate_pct", "last_quarter_surprise_pct", "status"]].copy()
        display_r.columns = ["Ticker", "Revisions-Score", "Upgrades (30T)", "Downgrades (30T)", "Beat-Rate (%)", "Letzte EPS-Surprise", "Trend-Status"]
        display_r["Beat-Rate (%)"] = display_r["Beat-Rate (%)"].apply(lambda x: f"{x:.0f}%")
        display_r["Letzte EPS-Surprise"] = display_r["Letzte EPS-Surprise"].apply(lambda x: f"{x:+.1f}%")
        
        st.dataframe(display_r, use_container_width=True, hide_index=True)

    # Module 4: Earnings Call Transcripts
    with tab_m4:
        st.subheader("🎙️ KI-Tonalitätsanalyse von Quartals-Telefonkonferenzen (Earnings Calls)")
        st.caption("NLP-Auswertung der Wortwahl von CEOs & CFOs im Analysten-Gespräch auf Zuversicht, Risiken und Margenaussichten.")
        
        calls = EarningsCallAnalyzer.CALL_ANALYSES
        for sym, c_data in calls.items():
            st.markdown(f"""
            <div style="background-color: #1a1e29; border-left: 4px solid #38bdf8; border-radius: 8px; padding: 14px 18px; margin-bottom: 12px;">
                <div style="display: flex; justify-content: space-between; font-size: 13px;">
                    <b style="font-size: 16px; color: white;">{sym} • {c_data['date']}</b>
                    <span style="font-weight: bold; color: #38bdf8;">CEO-Tonalität: {c_data['ceo_tone']}</span>
                </div>
                <div style="margin: 8px 0; font-size: 14px; color: #cbd5e1;"><b>Schlüsselbegriffe:</b> {', '.join(c_data['key_phrases'])}</div>
                <div style="font-size: 13px; color: #94a3b8;"><b>Warnsignale / Risiken:</b> {', '.join(c_data['caution_flags'])}</div>
                <div style="margin-top: 6px; font-size: 14px; color: #f1f5f9; background-color: #111827; padding: 8px; border-radius: 6px;">
                    🧠 <b>KI-Urteil:</b> {c_data['ai_verdict']}
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Module 5: FRED Macro
    with tab_m5:
        st.subheader("🌐 FRED-Makrodaten & US-Zinskurve (Federal Reserve St. Louis)")
        st.caption("Das makroökonomische Fundament: Renditen, Zinsstrukturkurve, Dollar-Index und Kreditmärkte.")
        
        fred = FREDMacroEngine.get_macro_indicators()
        
        f1, f2, f3, f4 = st.columns(4)
        with f1:
            st.metric("US 10-Jahres-Rendite", fred["us_10y_yield"])
        with f2:
            st.metric("US 2-Jahres-Rendite", fred["us_2y_yield"])
        with f3:
            st.metric("US-Dollar Index (DXY)", fred["us_dollar_index_dxy"], delta=fred["dxy_trend"][:15])
        with f4:
            st.metric("High-Yield Spread", fred["us_high_yield_spread"][:5], delta="Solide / Keine Panik")

        st.markdown(f"""
        <div style="background-color: #1e293b; border-left: 4px solid #34d399; border-radius: 8px; padding: 15px; margin: 15px 0;">
            <h4 style="margin: 0 0 4px 0; color: #34d399;">📐 Zinskurven-Zustand: {fred['yield_curve_spread']}</h4>
            <p style="margin: 0; color: #e2e8f0; font-size: 14px;">{fred['yield_curve_status']}</p>
            <p style="margin: 6px 0 0 0; color: #f8fafc; font-size: 14px;"><b>Fazit:</b> {fred['verdict']}</p>
        </div>
        """, unsafe_allow_html=True)

    # Module 6: Crypto On-Chain
    with tab_m6:
        st.subheader("⛓️ Krypto On-Chain & Whale-Flow Intelligence")
        st.caption("Blockchain-Transaktionsdaten: Börsenzuflüsse/-abflüsse, Wale-Akkumulation und Stablecoin-Reserven.")
        
        onchain = CryptoOnChainEngine.get_onchain_metrics()
        
        o1, o2, o3 = st.columns(3)
        with o1:
            st.metric("On-Chain Score", f"{onchain['onchain_score']} / 100", delta="Starke Verknappung")
        with o2:
            st.metric("Fear & Greed Index", onchain["fear_and_greed_index"], delta="Greed / Gier")
        with o3:
            st.metric("MVRV Z-Score", onchain["mvrv_z_score"][:4], help="Bewertungsbandbreite des Bitcoin-Netzwerks")

        st.markdown(f"""
        <div style="background-color: #1a1e29; border: 1px solid #334155; border-radius: 8px; padding: 15px; margin: 15px 0;">
            <div style="margin-bottom: 8px; font-size: 14px; color: #f1f5f9;"><b>Börsen-Netflow:</b> {onchain['btc_exchange_netflow']}</div>
            <div style="margin-bottom: 8px; font-size: 14px; color: #f1f5f9;"><b>Stablecoin-Reserven:</b> {onchain['stablecoin_supply_ratio']}</div>
            <div style="margin-bottom: 8px; font-size: 14px; color: #f1f5f9;"><b>Whale-Aktivität:</b> {onchain['whale_wallet_accumulation']}</div>
            <div style="margin-top: 10px; font-size: 14px; color: #38bdf8; background-color: #0f172a; padding: 10px; border-radius: 6px;">
                🚀 <b>Fazit:</b> {onchain['summary']}
            </div>
        </div>
        """, unsafe_allow_html=True)

# ==============================================================================
# MODE 4: WHALE- & INSIDER-RADAR
# ==============================================================================
elif app_mode == "🐋 Whale- & Insider-Radar":
    st.title("🐋 Whale- & Insider-Radar (Börsen-Legenden, US-Kongress & Vorstände)")
    st.markdown("Verfolge die **13F-Meldungen der Star-Investoren**, die **Aktienkäufe von US-Kongressabgeordneten** und **Insiderkäufe von Vorständen (CEOs)**.")

    tab_whales, tab_congress, tab_insiders = st.tabs([
        "🏛️ Star-Investoren Portfolios (13F Filings)",
        "🏛️ US-Kongress & Senat Trades (Politician Trading)",
        "👔 Vorstands- & CEO-Insiderkäufe (Cluster Buys)"
    ])

    with tab_whales:
        st.subheader("🏛️ Die Portfolios der Star-Investoren (13F Filings)")
        st.caption("Verifizierte Bestände und jüngste Zukäufe der einflussreichsten Fondsmanager der Welt.")

        investors = WhaleInsiderTracker.get_super_investors()
        
        # Investor Selector Cards
        selected_mgr = st.selectbox(
            "Investor auswählen:",
            [inv["manager"] + " (" + inv["fund"] + ")" for inv in investors]
        )

        active_inv = next(inv for inv in investors if inv["manager"] in selected_mgr)

        w_col1, w_col2, w_col3 = st.columns(3)
        with w_col1:
            st.metric("Fondsmanager", active_inv["manager"])
        with w_col2:
            st.metric("Fonds / Gesellschaft", active_inv["fund"], delta=active_inv["aum"])
        with w_col3:
            st.metric("Investment-Stil", active_inv["style"])

        st.markdown(f"""
        <div style="background-color: #1e293b; border-left: 4px solid #38bdf8; border-radius: 6px; padding: 12px 16px; margin: 15px 0;">
            <b style="color: #38bdf8;">💡 Jüngste Ausrichtung & These:</b>
            <p style="margin: 4px 0 0 0; color: #f1f5f9; font-size: 14px;">{active_inv['latest_conviction']}</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("#### 📋 Top-Positionen im Portfolio:")
        holdings_df = pd.DataFrame(active_inv["top_holdings"])
        
        action_map = {
            "BOUGHT": "🟢 AUFGESTOCKT",
            "NEW": "🟢 NEUEINSTIEG",
            "HOLD": "🟡 GEHALTEN",
            "REDUCED": "🔴 REDUZIERT"
        }
        holdings_df["Aktion"] = holdings_df["action"].map(lambda x: action_map.get(x, x))
        holdings_df["Gewichtung (%)"] = holdings_df["weight_pct"].apply(lambda x: f"{x:.1f}%")
        
        display_holdings = holdings_df[["symbol", "name", "Gewichtung (%)", "shares", "Aktion"]].copy()
        display_holdings.columns = ["Ticker", "Unternehmen", "Portfolio-Gewicht", "Aktienanzahl", "Jüngste Transaktion"]

        h_cfg = {
            "Ticker": st.column_config.TextColumn("Ticker", help="Börsenkürzel"),
            "Unternehmen": st.column_config.TextColumn("Unternehmen", help="Unternehmensname"),
            "Portfolio-Gewicht": st.column_config.TextColumn("Gewichtung", help="Anteil am gesamten Aktienportfolio"),
            "Aktienanzahl": st.column_config.TextColumn("Bestand", help="Gehaltene Aktien"),
            "Jüngste Transaktion": st.column_config.TextColumn("Aktion", help="Kauf, Aufstockung oder Teilverkauf im letzten Quartal")
        }

        st.dataframe(display_holdings, column_config=h_cfg, use_container_width=True, hide_index=True)

    with tab_congress:
        st.subheader("🏛️ US-Kongress & Senat Trades (STOCK Act Disclosures)")
        st.caption("Offiziell gemeldete Aktientransaktionen von US-Politikern (Nancy Pelosi, Senatoren & Abgeordnete).")

        congress_trades = WhaleInsiderTracker.get_congress_trades()
        c_df = pd.DataFrame(congress_trades)

        display_c = c_df[[
            "politician", "symbol", "name", "trade_type", "amount_range", 
            "transaction_date", "disclosure_date", "pnl_estimate", "notes"
        ]].copy()

        display_c.columns = [
            "Politiker / Fraktion", "Ticker", "Unternehmen", "Transaktion", 
            "Volumen-Spanne", "Handelsdatum", "Offenlegung", "Rendite seither", "Hintergrund / Ausschuss"
        ]

        c_cfg = {
            "Politiker / Fraktion": st.column_config.TextColumn("Politiker", help="Name und Parteizugehörigkeit"),
            "Ticker": st.column_config.TextColumn("Ticker", help="Aktien-Symbol"),
            "Unternehmen": st.column_config.TextColumn("Name", help="Unternehmen"),
            "Transaktion": st.column_config.TextColumn("Order-Typ", help="Aktienkauf, Verkauf oder Call-Optionen"),
            "Volumen-Spanne": st.column_config.TextColumn("Geschätztes Volumen", help="Gemeldete Transaktionsgröße in USD"),
            "Handelsdatum": st.column_config.TextColumn("Kaufdatum", help="Datum der Ausführung"),
            "Offenlegung": st.column_config.TextColumn("Publikation", help="Datum der öffentlichen Meldung"),
            "Rendite seither": st.column_config.TextColumn("Kursplus", help="Geschätzte Performance seit Kauf"),
            "Hintergrund / Ausschuss": st.column_config.TextColumn("Kontext", help="Ausschuss-Mitgliedschaft oder regulatorischer Kontext")
        }

        st.dataframe(display_c, column_config=c_cfg, use_container_width=True, hide_index=True)

    with tab_insiders:
        st.subheader("👔 Vorstands- & CEO-Insiderkäufe (Directors' Dealings)")
        st.caption("Echte Insider-Käufe von Führungskräften mit eigenem Privatvermögen – das stärkste Vertrauenssignal.")

        insiders = WhaleInsiderTracker.get_insider_buys()
        i_df = pd.DataFrame(insiders)

        display_i = i_df[[
            "symbol", "name", "insider", "role", "amount", "buy_price", "date", "signal"
        ]].copy()

        display_i.columns = [
            "Ticker", "Unternehmen", "Führungskraft / Insider", "Position / Rolle", 
            "Kaufvolumen", "Kaufkurs", "Datum", "KI-Signal"
        ]

        i_cfg = {
            "Ticker": st.column_config.TextColumn("Ticker", help="Aktien-Symbol"),
            "Unternehmen": st.column_config.TextColumn("Name", help="Unternehmen"),
            "Führungskraft / Insider": st.column_config.TextColumn("Insider", help="Name des Käufers"),
            "Position / Rolle": st.column_config.TextColumn("Rolle", help="CEO, CFO, Gründer oder Aufsichtsrat"),
            "Kaufvolumen": st.column_config.TextColumn("Summe", help="Investiertes Eigenkapital"),
            "Kaufkurs": st.column_config.TextColumn("Kurs", help="Ausführungskurs"),
            "Datum": st.column_config.TextColumn("Kaufdatum", help="Datum der Transaktion"),
            "KI-Signal": st.column_config.TextColumn("Signal", help="Einstufung des Signals")
        }

        st.dataframe(display_i, column_config=i_cfg, use_container_width=True, hide_index=True)

# ==============================================================================
# MODE 4: MAKRO-KLIMA, ZENTRALBANKEN & QUALITÄTSMEDIEN
# ==============================================================================
elif app_mode == "🌐 Makro-Klima, Zentralbanken & News":
    st.title("🌐 Makro-Klima, Zentralbanken & Qualitätsmedien")
    st.markdown("Echtzeit-Überwachung von **Leitzinsen (Fed, EZB, SNB, BoE)**, Inflation und verifizierten Nachrichten aus **Handelsblatt, FAZ, Reuters, CNBC & EZB**.")

    macro_scanner = MacroScanner()
    
    col_macro_btn, col_macro_info = st.columns([1, 3])
    with col_macro_btn:
        if st.button("🔄 Makro-Daten & News jetzt laden", use_container_width=True):
            with st.spinner("Lade Zentralbank-Daten und RSS-Feeds aus Qualitätsmedien..."):
                macro_scanner.get_full_macro_report()
                st.success("Makro-Daten & News aktualisiert!")
                st.rerun()

    report = macro_scanner.get_full_macro_report()
    climate_info = report["macro_climate"]
    news_items = report["news"]

    # 1. Macro Climate Score & KPIs
    st.markdown("---")
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    with m_col1:
        st.metric(
            "Makro-Klima-Score", 
            f"{climate_info['macro_score']} / 100", 
            delta="Expansiv / Easing" if climate_info['macro_score'] >= 65 else ("Neutral" if climate_info['macro_score'] >= 45 else "Defensiv"),
            help="Stimmungswert basierend auf Leitzinsen, Inflationstrend und Wirtschaftsberichten"
        )
    with m_col2:
        st.metric("Fed Leitzins (USA)", "5.25% - 5.50%", delta="Zinswende / Dovish", help="US Federal Reserve Benchmark Zinsspanne")
    with m_col3:
        st.metric("EZB Leitzins (Euroraum)", "3.75%", delta="Lockerung eingeleitet", help="Europäische Zentralbank Einlagesatz")
    with m_col4:
        st.metric("Gefilterte Qualitäts-News", f"{len(news_items)} Artikel", help="Aktuelle Meldungen aus FAZ, Handelsblatt, Reuters, CNBC & EZB")

    # Strategy Banner
    st.markdown(f"""
    <div style="background-color: #1e293b; border-left: 5px solid #38bdf8; border-radius: 8px; padding: 15px; margin: 15px 0;">
        <h4 style="margin: 0 0 5px 0; color: #38bdf8;">🧭 Makro-Ausrichtung der KI: {climate_info['climate']}</h4>
        <p style="margin: 0; color: #e2e8f0; font-size: 15px;">{climate_info['guidance']}</p>
    </div>
    """, unsafe_allow_html=True)

    # 2. Central Banks Rate Board
    st.markdown("### 🏛️ Zentralbank-Barometer & Zinspfade")
    cb_cols = st.columns(4)
    cb_data = climate_info.get("central_banks", {})

    for idx, (cb_name, cb_vals) in enumerate(cb_data.items()):
        with cb_cols[idx]:
            st.markdown(f"""
            <div style="background-color: #1a1e29; border: 1px solid #334155; border-radius: 8px; padding: 12px; margin-bottom: 10px;">
                <div style="font-weight: bold; color: #38bdf8; font-size: 16px;">{cb_name}</div>
                <div style="font-size: 24px; font-weight: bold; color: #f59e0b; margin: 4px 0;">{cb_vals['rate']}</div>
                <div style="font-size: 13px; color: #cbd5e1;"><b>Haltung:</b> {cb_vals['stance']}</div>
                <div style="font-size: 12px; color: #94a3b8; margin-top: 4px;">Trend: {cb_vals['trend']}</div>
                <div style="font-size: 11px; color: #64748b; margin-top: 4px;">Inflation: {cb_vals['current_cpi']} (Ziel: {cb_vals['inflation_target']})</div>
            </div>
            """, unsafe_allow_html=True)

    # 3. Quality Financial News Feed
    st.markdown("---")
    st.markdown("### 📰 Live-Nachrichten-Ticker aus seriösen Wirtschaftsmedien")
    
    n_f1, n_f2 = st.columns([1, 2])
    with n_f1:
        sources_available = ["Alle"] + sorted(list(set(n["source"] for n in news_items)))
        selected_source = st.selectbox("Quelle filtern", sources_available)
    with n_f2:
        search_query = st.text_input("🔍 Schlagwort / Ticker suchen (z. B. Zinsen, Fed, Gold, Nvidia, Inflation):", value="")

    filtered_news = news_items
    if selected_source != "Alle":
        filtered_news = [n for n in filtered_news if n["source"] == selected_source]
    if search_query.strip():
        q = search_query.strip().lower()
        filtered_news = [n for n in filtered_news if q in n["title"].lower() or q in n.get("snippet", "").lower()]

    if filtered_news:
        for item in filtered_news:
            source_badge_color = "#38bdf8" if "EZB" in item["source"] or "Fed" in item["source"] else ("#f59e0b" if "Handelsblatt" in item["source"] or "FAZ" in item["source"] else "#a78bfa")
            st.markdown(f"""
            <div style="background-color: #1a1e29; border-left: 4px solid {source_badge_color}; border-radius: 6px; padding: 12px 16px; margin-bottom: 12px;">
                <div style="display: flex; justify-content: space-between; font-size: 12px; color: #94a3b8;">
                    <span style="font-weight: bold; color: {source_badge_color};">📌 {item['source']} • {item.get('category', '')}</span>
                    <span>🕒 {item.get('published', '')[:25]}</span>
                </div>
                <h4 style="margin: 6px 0; color: white;">
                    <a href="{item['link']}" target="_blank" style="color: #f1f5f9; text-decoration: none;">{item['title']}</a>
                </h4>
                <p style="margin: 0; font-size: 13px; color: #cbd5e1;">{item.get('snippet', '')}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Keine Nachrichten für den gewählten Filter gefunden.")

# ==============================================================================
# MODE 5: MUSTERDEPOTS & LIVE-PERFORMANCE (3 DEPOTS)
# ==============================================================================
elif app_mode == "💼 Musterdepots & Live-Performance (3x 10.000 €)":
    st.title("💼 Autonome Musterdepots (3x 10.000 € Startkapital)")
    st.markdown("Drei getrennte Echtzeit-Musterdepots: **Kurzfristig (Tage–Wochen)**, **Mittelfristig (1–6 Monate)** und **Langfristig (Jahre)**.")

    pm = PortfolioManager(initial_capital_per_depot=10000.0)

    # Depot Selector (3 Depots)
    selected_depot_key = st.radio(
        "Wähle das Depot:",
        [
            ("short_term", "⚡ Kurzfristig (Tage–Wochen / Squeezes & Hebel)"),
            ("medium_term", "📈 Mittelfristig (1–6 Monate / Growth & Trend)"),
            ("long_term", "🏛️ Langfristig (Jahre / Quality, Gold & Moat)")
        ],
        format_func=lambda x: x[1],
        horizontal=True
    )[0]

    # Expandable Strategy Handbook & Percentages
    with st.expander("📖 Strategie-Handbuch: Nach welchen Formeln & Prozenten handelt die KI?"):
        h_tab1, h_tab2, h_tab3 = st.tabs([
            "⚡ 1. Kurzfrist-Depot (Tage–Wochen)",
            "📈 2. Mittelfrist-Depot (1–6 Monate)",
            "🏛️ 3. Langfrist-Depot (1–5+ Jahre)"
        ])

        with h_tab1:
            st.markdown("""
            #### ⚡ Kurzfristiges Trading-Depot (Momentum, Squeezes & Hebel)
            **Ziel:** Schnelle Gewinne bei akuten Ausbrüchen, Smart-Money-Positionierung und Leerverkäufer-Fallen.

            | Faktor | Gewichtung | Kriterien & Schwellenwerte |
            | :--- | :---: | :--- |
            | **📈 Charttechnik & Momentum** | **30 %** | Kurs über EMA 20 & EMA 50, RSI zwischen 50–68, MACD Crossover |
            | **🎯 Optionen-Fluss & Dark Pools** | **25 %** | Put/Call-Ratio < 0.50, ungewöhnliche OTM Call-Sweeps, Dark-Pool-Blöcke |
            | **🪤 Leerverkäufer & BaFin-Shorts** | **20 %** | Short Float > 12 % ODER BaFin-Eindeckungen (Short-Squeeze-Gefahr) |
            | **💬 Social Sentiment & Buzz** | **15 %** | Erwähnungsspitzen auf Reddit WSB & StockTwits (> 70 % Bullish) |
            | **⛓️ Krypto On-Chain-Flows** | **10 %** | Starke Netto-Abflüsse von Börsen in Cold Wallets (Verknappung) |

            * **🟢 KAUF-Trigger:** Kurzfrist-Score ≥ **75 / 100**.
            * **🔴 VERKAUFS-Trigger:** Fester **Stop-Loss bei -7 %** (bzw. **-15 %** bei Hebel-Zertifikaten) oder **Take-Profit bei +20 %** (bzw. **+40 %** bei Hebel-Zertifikaten).
            """)

        with h_tab2:
            st.markdown("""
            #### 📈 Mittelfristiges Trend- & Growth-Depot (Swing & Wachstum)
            **Ziel:** Reiten starker Aufwärtstrends bei Unternehmen mit systematisch steigenden Gewinnschätzungen.

            | Faktor | Gewichtung | Kriterien & Schwellenwerte |
            | :--- | :---: | :--- |
            | **📈 Earnings-Revisionen (EPS)** | **35 %** | Mindestens 3x mehr Upgrades als Downgrades in 30 Tagen + EPS-Surprises |
            | **🎙️ Earnings Call KI-Tonalität** | **25 %** | KI-Sprachscore > 85/100 (Fokus auf Margenwachstum & Auftragsrekorde) |
            | **📊 Trendfolge über EMA 50** | **20 %** | Kurs notiert stabil über dem EMA 50 und steigender 200-Tage-Linie |
            | **🐋 Whale- & Kongress-Tracking** | **10 %** | Star-Investoren (Buffett, Druckenmiller) oder Kongressmitglieder kaufen |
            | **🌐 FRED-Makro & Zinskurve** | **10 %** | Normalisierung der Zinskurve (10Y/2Y) und fallender US-Dollar-Index (DXY) |

            * **🟢 KAUF-Trigger:** Mittelfrist-Score ≥ **70 / 100**.
            * **🔴 VERKAUFS-Trigger:** **Trailing Stop-Loss bei -10 %** oder **Mittelfrist-Ziel bei +35 %**.
            """)

        with h_tab3:
            st.markdown("""
            #### 🏛️ Langfristiges Investment-Depot (Quality, Gold & Moat)
            **Ziel:** Krisenfestes Compounding mit starkem Burggraben, Gold und digitalem Wertspeicher.

            | Faktor | Gewichtung | Kriterien & Schwellenwerte |
            | :--- | :---: | :--- |
            | **🏰 Kapitalrendite & Burggraben** | **35 %** | Eigenkapitalrendite (ROE) > 15 %, freie Cashflow-Marge > 15 % |
            | **🛡️ Bilanzqualität & Solidität** | **25 %** | Verschuldungsgrad (Debt/Equity) < 1,0, krisensicherer Cash-Bestand |
            | **🌐 FRED-Makro & Zyklen** | **20 %** | Allokation in Gold & Bitcoin als Währungs- und Inflationsabsicherung |
            | **🏷️ Bewertung & Sicherheitsmarge** | **10 %** | KGV < 25 oder PEG < 1.2; Capped Bonus mit ≥ 25 % Sicherheitspuffer |
            | **🎯 Analysten-Upside & Insider** | **10 %** | Konsenskursziel > +15 % + Käufe durch CEOs/Vorstände (*Directors' Dealings*) |

            * **🟢 KAUF-Trigger:** Langfrist-Score ≥ **75 / 100**.
            * **🔴 VERKAUFS-Trigger:** Nur bei **fundamentalem Bruch der These** (z. B. dauerhafter Verlust des Burggrabens).
            """)

    # Action Toolbar
    col_act1, col_act2, col_info_p = st.columns([1, 1.5, 2])
    with col_act1:
        if st.button("🔄 Kurse aktualisieren", use_container_width=True):
            with st.spinner("Lade frische Börsenkurse für Depot-Positionen..."):
                pm.update_live_prices()
                st.success("Kurse aktualisiert!")
                st.rerun()

    with col_act2:
        if st.button("🤖 Autonomen Handels-Check ausführen", use_container_width=True):
            with st.spinner("Prüfe Stop-Loss, Take-Profit und Markt-Top-Picks..."):
                scan_data = load_cached_market_scan()
                scan_list = scan_data.get("data", []) if scan_data else []
                actions = pm.auto_trade_check(scan_list)
                if actions:
                    st.success(f"Handlungen ausgeführt: {', '.join(actions)}")
                else:
                    st.info("Keine Handlungsnotwendigkeit (alle Positionen innerhalb der Risikoparameter).")
                st.rerun()

    summary = pm.get_depot_summary(selected_depot_key)

    # 4 Metric Cards
    st.markdown("---")
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric(
            "Depot-Gesamtwert", 
            f"{summary['total_value']:,.2f} €", 
            delta=f"{summary['total_pnl']:+,.2f} € ({summary['total_pnl_pct']:+.2f}%)"
        )
    with m2:
        st.metric(
            "Investiertes Kapital", 
            f"{summary['invested_value']:,.2f} €",
            help="Aktueller Marktwert aller offenen Aktienpositionen"
        )
    with m3:
        st.metric(
            "Freies Cash", 
            f"{summary['cash']:,.2f} €", 
            delta=f"{summary['cash_ratio_pct']:.1f}% Cash-Quote",
            help="Verfügbare Liquidität für neue Käufe"
        )
    with m4:
        st.metric(
            "Offene Positionen", 
            f"{len(summary['positions'])} Titel",
            help="Anzahl der aktuell gehaltenen Aktien"
        )

    st.caption(f"🎯 **Strategie:** {summary['strategy']}")

    # Charts & Positions
    tab_pos, tab_alloc, tab_hist = st.tabs([
        "📋 Offene Positionen & Buchgewinne",
        "🥧 Asset Allocation (Gewichtung)",
        "📜 Transaktions-Historie (Trade Log)"
    ])

    with tab_pos:
        if summary["positions"]:
            pos_df = pd.DataFrame(summary["positions"])
            
            for col in ["product_type", "leverage", "distance_to_ko"]:
                if col not in pos_df.columns:
                    pos_df[col] = None

            display_pos = pos_df[[
                "symbol", "name", "product_type", "shares", "buy_price", "current_price", 
                "value", "pnl", "pnl_pct", "leverage", "distance_to_ko", "stop_loss", "take_profit", "reason"
            ]].copy()

            display_pos.columns = [
                "Ticker / WKN", "Instrument / Name", "Produkttyp", "Stück", "Kaufkurs", "Aktuell", 
                "Marktwert (€)", "Gewinn (€)", "Rendite (%)", "Hebel", "KO-/Puffer-Abstand", "Stop-Loss", "Take-Profit", "Kaufgrund"
            ]

            type_map = {
                "STOCK": "Aktie / Krypto",
                "KNOCKOUT": "⚡ Knock-Out",
                "FACTOR": "🚀 Faktor-Zertifikat",
                "BONUS": "🛡️ Bonus-Zertifikat"
            }
            display_pos["Produkttyp"] = display_pos["Produkttyp"].map(lambda x: type_map.get(x, x))
            display_pos["Kaufkurs"] = display_pos["Kaufkurs"].apply(lambda x: f"{x:.2f}")
            display_pos["Aktuell"] = display_pos["Aktuell"].apply(lambda x: f"{x:.2f}")
            display_pos["Marktwert (€)"] = display_pos["Marktwert (€)"].apply(lambda x: f"{x:,.2f} €")
            display_pos["Gewinn (€)"] = display_pos["Gewinn (€)"].apply(lambda x: f"{x:+,.2f} €")
            display_pos["Rendite (%)"] = display_pos["Rendite (%)"].apply(lambda x: f"{x:+.2f}%")
            display_pos["Hebel"] = display_pos["Hebel"].apply(lambda x: f"{x:.1f}x" if pd.notnull(x) else "-")
            display_pos["KO-/Puffer-Abstand"] = display_pos["KO-/Puffer-Abstand"].apply(lambda x: f"{x:.1f}%" if pd.notnull(x) else "-")
            display_pos["Stop-Loss"] = display_pos["Stop-Loss"].apply(lambda x: f"{x:.2f}" if pd.notnull(x) else "-")
            display_pos["Take-Profit"] = display_pos["Take-Profit"].apply(lambda x: f"{x:.2f}" if pd.notnull(x) else "-")

            pos_cfg = {
                "Ticker / WKN": st.column_config.TextColumn("Ticker / WKN", help="Börsenkürzel oder WKN des Zertifikats"),
                "Instrument / Name": st.column_config.TextColumn("Name", help="Name des Unternehmens oder Zertifikats"),
                "Produkttyp": st.column_config.TextColumn("Typ", help="Aktie, Krypto, Knock-Out, Faktor- oder Bonus-Zertifikat"),
                "Stück": st.column_config.NumberColumn("Stück", help="Anzahl gehaltener Stücke / Zertifikate"),
                "Kaufkurs": st.column_config.TextColumn("Kaufkurs", help="Einstandskurs in Euro"),
                "Aktuell": st.column_config.TextColumn("Aktuell", help="Aktueller Kurs"),
                "Marktwert (€)": st.column_config.TextColumn("Marktwert (€)", help="Gesamtwert der Position"),
                "Gewinn (€)": st.column_config.TextColumn("Gewinn (€)", help="Unrealisierter Buchgewinn/-verlust"),
                "Rendite (%)": st.column_config.TextColumn("Rendite (%)", help="Prozentuale Rendite"),
                "Hebel": st.column_config.TextColumn("Hebel", help="Effektiver Hebel (z. B. 3.5x) bei Derivaten"),
                "KO-/Puffer-Abstand": st.column_config.TextColumn("KO-Puffer", help="Prozentualer Abstand zur Knock-Out Schwelle bzw. Barriere"),
                "Stop-Loss": st.column_config.TextColumn("Stop-Loss", help="Automatischer Verkaufs-Trigger"),
                "Take-Profit": st.column_config.TextColumn("Take-Profit", help="Automatischer Gewinnmitnahme-Trigger"),
                "Kaufgrund": st.column_config.TextColumn("Kaufgrund / Signal", help="KI-Analyse & Einstiegsthese")
            }

            st.dataframe(
                display_pos,
                column_config=pos_cfg,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Keine offenen Positionen. Das Depot hält 100% Cash.")

    with tab_alloc:
        labels = [p["name"] for p in summary["positions"]] + ["Freies Cash"]
        values = [p["value"] for p in summary["positions"]] + [summary["cash"]]
        
        fig_donut = go.Figure(data=[go.Pie(
            labels=labels, 
            values=values, 
            hole=.45,
            marker=dict(colors=['#38bdf8', '#a78bfa', '#34d399', '#f59e0b', '#ec4899', '#475569'])
        )])
        fig_donut.update_layout(
            template="plotly_dark",
            height=400,
            margin=dict(l=20, r=20, t=30, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    with tab_hist:
        st.subheader("📜 Vollständige Transaktions-Historie (Trade Log)")
        st.caption("Chronologisches Protokoll aller autonomen Käufe, Gewinnmitnahmen und Stop-Loss-Verkäufe.")

        if summary["history"]:
            hist_list = summary["history"]
            
            # Summary Metrics for History
            buys = sum(1 for h in hist_list if h.get("type") == "BUY")
            sells = sum(1 for h in hist_list if h.get("type") == "SELL")
            realized_pnl = sum(h.get("pnl", 0.0) for h in hist_list if h.get("type") == "SELL")
            winning_trades = sum(1 for h in hist_list if h.get("type") == "SELL" and h.get("pnl", 0) > 0)
            win_rate = (winning_trades / sells * 100.0) if sells > 0 else 0.0

            h_col1, h_col2, h_col3, h_col4 = st.columns(4)
            with h_col1:
                st.metric("Ausgeführte Trades", f"{len(hist_list)} Gesamt", help="Summe aller Transaktionen")
            with h_col2:
                st.metric("Käufe / Verkäufe", f"{buys} 🟢 / {sells} 🔴")
            with h_col3:
                st.metric("Realisierter Gewinn", f"{realized_pnl:+,.2f} €", delta=f"{realized_pnl:+,.2f} €" if sells > 0 else None)
            with h_col4:
                st.metric("Trefferquote (Win-Rate)", f"{win_rate:.1f}%" if sells > 0 else "N/A", help="Prozentualer Anteil profitabler Verkäufe")

            st.markdown("---")

            # Formatted History Table
            hist_df = pd.DataFrame(hist_list)
            
            # Ensure columns exist
            for c in ["type", "symbol", "name", "shares", "price", "sell_price", "total", "pnl", "pnl_pct", "date", "reason"]:
                if c not in hist_df.columns:
                    hist_df[c] = None

            display_hist = pd.DataFrame()
            display_hist["Aktion"] = hist_df["type"].apply(lambda x: "🟢 KAUF" if x == "BUY" else "🔴 VERKAUF")
            display_hist["Datum"] = hist_df["date"]
            display_hist["Ticker"] = hist_df["symbol"]
            display_hist["Unternehmen"] = hist_df["name"]
            display_hist["Stück"] = hist_df["shares"].apply(lambda x: f"{x:.2f}" if pd.notnull(x) else "-")
            display_hist["Kurs"] = hist_df.apply(lambda row: f"{row['price']:.2f}" if row['type'] == 'BUY' else f"{row.get('sell_price', row['price']):.2f}", axis=1)
            display_hist["Volumen"] = hist_df["total"].apply(lambda x: f"{x:,.2f} €" if pd.notnull(x) else "-")
            display_hist["Realisierter P&L (€)"] = hist_df.apply(
                lambda row: f"{row['pnl']:+,.2f} € ({row['pnl_pct']:+.1f}%)" if row['type'] == 'SELL' and pd.notnull(row.get('pnl')) else "-",
                axis=1
            )
            display_hist["Begründung / Signal"] = hist_df["reason"].fillna("-")

            hist_cfg = {
                "Aktion": st.column_config.TextColumn("Aktion", help="Art der Transaktion (Kauf oder Verkauf)"),
                "Datum": st.column_config.TextColumn("Datum & Uhrzeit", help="Zeitpunkt der Ausführung"),
                "Ticker": st.column_config.TextColumn("Ticker", help="Aktien-Symbol"),
                "Unternehmen": st.column_config.TextColumn("Name", help="Unternehmensname"),
                "Stück": st.column_config.TextColumn("Stück", help="Anzahl der gehandelten Aktien"),
                "Kurs": st.column_config.TextColumn("Ausführungskurs", help="Kurs zum Zeitpunkt der Transaktion"),
                "Volumen": st.column_config.TextColumn("Gesamtbetrag", help="Gesamtes Transaktionsvolumen in Euro"),
                "Realisierter P&L (€)": st.column_config.TextColumn("Realisierter Gewinn / Verlust", help="Tatsächlich realisierter Gewinn oder Verlust bei Verkauf"),
                "Begründung / Signal": st.column_config.TextColumn("KI-Begründung / Signal", help="Warum die KI diese Transaktion ausgeführt hat")
            }

            st.dataframe(
                display_hist,
                column_config=hist_cfg,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Noch keine Transaktionen ausgeführt.")

# ==============================================================================
# MODE 4: EINZELAKTIEN-TIEFENANALYSE
# ==============================================================================
else:
    st.sidebar.subheader("🔍 Aktie auswählen")
    category = st.sidebar.selectbox("Kategorie / Markt", list(CATEGORIZED_UNIVERSES.keys()))
    default_tickers = CATEGORIZED_UNIVERSES[category]
    selected_preset = st.sidebar.selectbox("Favoriten", default_tickers)
    custom_ticker = st.sidebar.text_input("Oder Ticker manuell eingeben (z.B. MRNA, AAPL, SDF.DE, PLTR):", value="")
    active_symbol = custom_ticker.strip().upper() if custom_ticker.strip() else selected_preset
    chart_period = st.sidebar.selectbox("Chart-Zeitraum", ["3mo", "6mo", "1y", "2y", "5y"], index=2)

    @st.cache_data(ttl=300)
    def load_single_data(symbol: str, period: str):
        fetcher = FinancialDataFetcher(symbol)
        prices_raw = fetcher.get_historical_prices(period=period)
        prices_with_ind = calculate_technical_indicators(prices_raw)
        fundamentals = fetcher.get_fundamentals()
        consensus = fetcher.get_analyst_consensus()
        sentiment = fetcher.get_social_sentiment()
        news = fetcher.get_news()
        return prices_with_ind, fundamentals, consensus, sentiment, news

    try:
        with st.spinner(f"Analysiere Daten für **{active_symbol}**..."):
            prices_df, fundamentals, consensus, sentiment, news = load_single_data(active_symbol, chart_period)

        short_engine = ShortTermEngine()
        long_engine = LongTermEngine()
        synthesizer = DecisionSynthesizer()
        breakout_radar = BreakoutRadar()

        options_intel = OptionsDarkPoolEngine.get_options_flow_for_ticker(active_symbol)
        revision_intel = EarningsRevisionEngine.get_revision_metrics(active_symbol)
        whale_intel = WhaleInsiderTracker.get_whale_sentiment_for_ticker(active_symbol)
        macro_intel = FREDMacroEngine.get_macro_indicators()

        short_results = short_engine.evaluate(prices_df, sentiment)
        long_results = long_engine.evaluate(fundamentals, consensus)
        synth_result = synthesizer.synthesize(
            short_results, long_results, fundamentals, consensus,
            options_intel=options_intel, revision_intel=revision_intel,
            macro_intel=macro_intel, whale_intel=whale_intel
        )
        breakout_res = breakout_radar.analyze_breakout_potential(prices_df, fundamentals, sentiment.get("forum_mentions", 0))

        # Header Bar
        col_h1, col_h2, col_h3 = st.columns([3, 2, 2])
        current_p = fundamentals.get("currentPrice") or (prices_df['Close'].iloc[-1] if not prices_df.empty else 0)
        prev_p = prices_df['Close'].iloc[-2] if len(prices_df) > 1 else current_p
        price_change = current_p - prev_p
        price_change_pct = (price_change / prev_p * 100) if prev_p else 0
        curr = fundamentals.get("currency", "USD")

        with col_h1:
            st.title(f"{fundamentals.get('shortName', active_symbol)} ({active_symbol})")
            st.caption(f"Sektor: **{fundamentals.get('sector')}** | Industrie: **{fundamentals.get('industry')}**")

        with col_h2:
            st.metric(
                label=f"Aktueller Kurs ({curr})",
                value=f"{current_p:.2f} {curr}",
                delta=f"{price_change:+.2f} ({price_change_pct:+.2f}%)"
            )

        with col_h3:
            mcap = fundamentals.get("marketCap")
            mcap_str = f"{mcap / 1e9:.2f} Mrd. {curr}" if mcap else "N/A"
            st.metric(label="Marktkapitalisierung", value=mcap_str)

        # Synthesis Banner
        banner_color_map = {
            "green": ("#0f5132", "#d1e7dd", "#0f5132"),
            "blue": ("#084298", "#cfe2ff", "#084298"),
            "orange": ("#664d03", "#fff3cd", "#664d03"),
            "gray": ("#41464b", "#e2e3e5", "#41464b"),
            "red": ("#842029", "#f8d7da", "#842029"),
        }
        bg, fg, border = banner_color_map.get(synth_result["color"], ("#1e222d", "#ffffff", "#333"))
        
        st.markdown(f"""
        <div style="background-color: {bg}; border-left: 6px solid {border}; padding: 16px 20px; border-radius: 8px; margin: 15px 0;">
            <h2 style="color: white; margin: 0 0 8px 0;">{synth_result['action']}</h2>
            <p style="color: #f0f0f0; font-size: 16px; margin: 0;">{synth_result['action_desc']}</p>
        </div>
        """, unsafe_allow_html=True)

        # Score Gauges
        sc1, sc2, sc3, sc4 = st.columns(4)
        with sc1:
            st.markdown(f"""
            <div style="text-align: center; background-color: #1a1e29; padding: 15px; border-radius: 8px; border: 1px solid #2e3546;">
                <div style="font-size: 13px; color: #888;">GESAMT-SCORE</div>
                <div style="font-size: 32px; font-weight: bold; color: #38bdf8;">{synth_result['total_score']} / 100</div>
                <div style="font-size: 11px; color: #aaa;">Synthese</div>
            </div>
            """, unsafe_allow_html=True)
        with sc2:
            st.markdown(f"""
            <div style="text-align: center; background-color: #1a1e29; padding: 15px; border-radius: 8px; border: 1px solid #2e3546;">
                <div style="font-size: 13px; color: #888;">⚡ KURZFRIST</div>
                <div style="font-size: 32px; font-weight: bold; color: #a78bfa;">{short_results['score']} / 100</div>
                <div style="font-size: 11px; color: #ddd;">{short_results['status'][:20]}...</div>
            </div>
            """, unsafe_allow_html=True)
        with sc3:
            st.markdown(f"""
            <div style="text-align: center; background-color: #1a1e29; padding: 15px; border-radius: 8px; border: 1px solid #2e3546;">
                <div style="font-size: 13px; color: #888;">🏛️ LANGFRIST</div>
                <div style="font-size: 32px; font-weight: bold; color: #34d399;">{long_results['score']} / 100</div>
                <div style="font-size: 11px; color: #ddd;">{long_results['status'][:20]}...</div>
            </div>
            """, unsafe_allow_html=True)
        with sc4:
            st.markdown(f"""
            <div style="text-align: center; background-color: #1a1e29; padding: 15px; border-radius: 8px; border: 1px solid #2e3546;">
                <div style="font-size: 13px; color: #888;">🚨 SQUEEZE & AUSBRUCH</div>
                <div style="font-size: 32px; font-weight: bold; color: #f43f5e;">{breakout_res['breakout_score']} / 100</div>
                <div style="font-size: 11px; color: #ddd;">{breakout_res['status'][:20]}...</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Tabs
        tab_chart, tab_short_sellers, tab_breakout, tab_whales_single, tab_short, tab_long, tab_analysts = st.tabs([
            "📊 Interaktiver Chart & Signale",
            "🪤 Leerverkäufer & Short-Interest",
            "🚨 Ausbruchs-Signale & Volumen",
            "🐋 Whales & Insider-Trades",
            "⚡ Schiene 1: Kurz- & Mittelfristig",
            "🏛️ Schiene 2: Langfristig (Bilanzen)",
            "🎯 Analysten & News"
        ])

        with tab_chart:
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.75, 0.25])
            fig.add_trace(go.Candlestick(
                x=prices_df.index,
                open=prices_df['Open'], high=prices_df['High'],
                low=prices_df['Low'], close=prices_df['Close'],
                name="Kurs"
            ), row=1, col=1)

            fig.add_trace(go.Scatter(x=prices_df.index, y=prices_df['EMA_20'], line=dict(color='#38bdf8', width=1.5), name="EMA 20"), row=1, col=1)
            fig.add_trace(go.Scatter(x=prices_df.index, y=prices_df['EMA_50'], line=dict(color='#f59e0b', width=1.5), name="EMA 50"), row=1, col=1)
            if 'SMA_200' in prices_df.columns:
                fig.add_trace(go.Scatter(x=prices_df.index, y=prices_df['SMA_200'], line=dict(color='#ec4899', width=2), name="SMA 200"), row=1, col=1)

            fig.add_trace(go.Scatter(x=prices_df.index, y=prices_df['BB_Upper'], line=dict(color='rgba(255,255,255,0.2)', dash='dot'), name="BB Oben"), row=1, col=1)
            fig.add_trace(go.Scatter(x=prices_df.index, y=prices_df['BB_Lower'], line=dict(color='rgba(255,255,255,0.2)', dash='dot'), fill='tonexty', fillcolor='rgba(255,255,255,0.03)', name="BB Unten"), row=1, col=1)

            colors = ['#00e676' if row['Close'] >= row['Open'] else '#ff5252' for _, row in prices_df.iterrows()]
            fig.add_trace(go.Bar(x=prices_df.index, y=prices_df['Volume'], marker_color=colors, name="Volumen"), row=2, col=1)

            fig.update_layout(
                height=600,
                template="plotly_dark",
                xaxis_rangeslider_visible=False,
                margin=dict(l=20, r=20, t=30, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig, use_container_width=True)

        with tab_short_sellers:
            st.subheader("🪤 Leerverkäufer & Short-Squeeze-Analyse")
            
            sf = fundamentals.get('shortPercentOfFloat')
            sr = fundamentals.get('shortRatio')
            ss_shares = fundamentals.get('sharesShort')
            s_change = fundamentals.get('shortChangePct')
            sq_score = fundamentals.get('squeezeScore', 10)

            s_col1, s_col2, s_col3, s_col4 = st.columns(4)
            with s_col1:
                sf_str = f"{sf:.2f}%" if sf is not None else "N/A"
                delta_str = "Extrem Hoch (>15%)" if sf and sf >= 15 else ("Moderat" if sf and sf >= 5 else "Niedrig")
                st.metric("Short Float (% des Free Floats)", sf_str, delta=delta_str if sf else None)
            with s_col2:
                sr_str = f"{sr:.1f} Tage" if sr is not None else "N/A"
                st.metric("Days to Cover (Short Ratio)", sr_str, help="Tage an durchschnittlichem Handelsvolumen, die Leerverkäufer zum Eindecken bräuchten.")
            with s_col3:
                ss_str = f"{ss_shares/1e6:.2f} Mio." if ss_shares else "N/A"
                ch_str = f"{s_change:+.1f}% vs Vormonat" if s_change is not None else None
                st.metric("Leerverkaufte Aktien (Gesamt)", ss_str, delta=ch_str)
            with s_col4:
                st.metric("Short-Squeeze-Risiko-Score", f"{sq_score:.0f} / 100")

            st.markdown("---")
            st.markdown("#### 💡 Bewertung der Leerverkäufer-Lage:")
            if sf is not None and sf >= 15.0:
                st.error(f"🚨 **Hohe Short-Position ({sf:.1f}% des Streubesitzes)**: Sehr hohes Potenzial für einen gewaltigen Short Squeeze, wenn unerwartet gute Nachrichten oder Studiendaten eintreffen!")
            elif sf is not None and sf >= 8.0:
                st.warning(f"⚠️ **Erhöhte Leerverkäufe ({sf:.1f}%)**: Spürbarer Verkaufsdruck durch Bären. Kurzfristige Volatilität erhöht.")
            elif sf is not None:
                st.success(f"✅ **Geringe Leerverkäufer-Aktivität ({sf:.1f}%)**: Kein dominanter Short-Seller-Druck vorhanden.")
            else:
                st.info("ℹ️ Für diesen Ticker sind keine US-FINRA Short-Float-Daten hinterlegt (häufig bei europäischen Nebenwerten).")

        with tab_breakout:
            st.subheader("🚨 Ausbruchs-Faktoren & Katalysator-Muster")
            b_col1, b_col2, b_col3 = st.columns(3)
            with b_col1:
                st.metric("Ausbruchs-Score", f"{breakout_res['breakout_score']} / 100")
            with b_col2:
                st.metric("Volumen-Faktor vs. 20T-Schnitt", f"{breakout_res['vol_ratio']:.1f}x")
            with b_col3:
                st.metric("Tages-Kursbewegung", f"{breakout_res['daily_return_pct']:+.2f}%")

            st.markdown("#### ⚡ Erkannte Ausbruchs-Auslöser (Triggers)")
            if breakout_res['triggers']:
                for tr in breakout_res['triggers']:
                    st.markdown(f"**{tr['title']}**: {tr['desc']}")
            else:
                st.info("Aktuell keine extremen Ausbruchsmuster aktiv.")

        with tab_whales_single:
            st.subheader(f"🐋 Whale-, Kongress- & Insider-Aktivität für {active_symbol}")
            whale_info = WhaleInsiderTracker.get_whale_sentiment_for_ticker(active_symbol)
            if whale_info["has_activity"]:
                st.success(f"🎯 **Hohe institutionelle / Insider-Aktivität erkannt (+{whale_info['score_boost']} Punkte Score-Bonus)**")
                
                if whale_info["whale_holders"]:
                    st.markdown("#### 🏛️ Star-Investoren (13F Filings):")
                    for wh in whale_info["whale_holders"]:
                        st.markdown(f"- **{wh['manager']}** ({wh['fund']}): **{wh['weight']}% Depot-Gewichtung** *(Aktion: {wh['action']})*")
                
                if whale_info["congress_buyers"]:
                    st.markdown("#### 🏛️ US-Kongress / Senat Käufe (STOCK Act):")
                    for cg in whale_info["congress_buyers"]:
                        st.markdown(f"- **{cg['politician']}**: {cg['trade_type']} ({cg['amount_range']}) am {cg['transaction_date']} *(Hintergrund: {cg['notes']})*")
                
                if whale_info["insider_buyers"]:
                    st.markdown("#### 👔 Vorstands- & CEO-Insiderkäufe:")
                    for ins in whale_info["insider_buyers"]:
                        st.markdown(f"- **{ins['insider']}** ({ins['role']}): Kauf über **{ins['amount']}** zu {ins['buy_price']} am {ins['date']} ({ins['signal']})")
            else:
                st.info("Aktuell keine meldepflichtigen 13F-Whale-Positionen, Kongress-Trades oder Vorstandskäufe für diesen Ticker hinterlegt.")

        with tab_short:
            st.subheader("⚡ Kurz- & Mittelfristige Faktoren")
            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
            latest_rsi = short_results['metrics']['rsi']
            latest_vol_ratio = short_results['metrics']['vol_ratio']
            
            with m_col1:
                st.metric("RSI (14 Tage)", f"{latest_rsi}")
            with m_col2:
                st.metric("MACD Histogramm", f"{short_results['metrics']['macd_hist']}")
            with m_col3:
                st.metric("Volumen vs 20T-Schnitt", f"{latest_vol_ratio}x")
            with m_col4:
                sent_str = f"{sentiment.get('bullish_pct', 50):.0f}% Bullish" if sentiment.get('available') else "N/A"
                st.metric("Social Sentiment", sent_str)

            st.markdown("#### 🎯 Signale & Chartmuster")
            for sig in short_results['signals']:
                prefix = "🟢" if sig['type'] == 'bullish' else ("🔴" if sig['type'] == 'bearish' else "🟡")
                st.markdown(f"**{prefix} {sig['title']}**: {sig['desc']}")

        with tab_long:
            st.subheader("🏛️ Fundamentale Qualität & Bewertung")
            f_col1, f_col2, f_col3, f_col4 = st.columns(4)
            with f_col1:
                pe_val = fundamentals.get('trailingPE')
                st.metric("KGV (Trailing P/E)", f"{pe_val:.1f}" if pe_val else "N/A")
                fwd_pe = fundamentals.get('forwardPE')
                st.metric("Forward KGV", f"{fwd_pe:.1f}" if fwd_pe else "N/A")
            with f_col2:
                peg_val = fundamentals.get('pegRatio')
                st.metric("PEG-Ratio", f"{peg_val:.2f}" if peg_val else "N/A")
                ps_val = fundamentals.get('priceToSales')
                st.metric("KUV (P/S)", f"{ps_val:.1f}" if ps_val else "N/A")
            with f_col3:
                roe_val = fundamentals.get('returnOnEquity')
                st.metric("Eigenkapitalrendite (ROE)", f"{roe_val:.1f}%" if roe_val else "N/A")
                fcf_y = fundamentals.get('fcfYield')
                st.metric("Free Cashflow Rendite", f"{fcf_y:.1f}%" if fcf_y else "N/A")
            with f_col4:
                dte_val = fundamentals.get('debtToEquity')
                st.metric("Debt-to-Equity", f"{dte_val:.2f}" if dte_val else "N/A")
                div_val = fundamentals.get('dividendYield')
                st.metric("Dividendenrendite", f"{div_val:.2f}%" if div_val else "0.00%")

            st.markdown("#### 💎 Fundamentale Einschätzung")
            for sig in long_results['signals']:
                prefix = "🟢" if sig['type'] == 'bullish' else ("🔴" if sig['type'] == 'bearish' else ("🟡" if sig['type'] == 'warning' else "ℹ️"))
                st.markdown(f"**{prefix} {sig['title']}**: {sig['desc']}")

        with tab_analysts:
            st.subheader("🎯 Analysten-Einschätzungen & Kursziel-Spanne")
            a_col1, a_col2 = st.columns([1, 1])
            with a_col1:
                t_mean = consensus.get('targetMeanPrice')
                t_high = consensus.get('targetHighPrice')
                t_low = consensus.get('targetLowPrice')
                upside = consensus.get('upsideMeanPct')
                opinions = consensus.get('numberOfAnalystOpinions')

                st.write(f"**Anzahl Analysten:** {opinions or 'N/A'}")
                st.write(f"**Mittleres Kursziel:** {t_mean:.2f} {curr}" if t_mean else "N/A")
                st.write(f"**Höchstes Kursziel:** {t_high:.2f} {curr}" if t_high else "N/A")
                st.write(f"**Tiefstes Kursziel:** {t_low:.2f} {curr}" if t_low else "N/A")
                
                if upside is not None:
                    st.metric("Kurspotenzial (Konsens)", f"{upside:+.1f}%")

            with a_col2:
                st.markdown("#### 📰 Aktuelle Nachrichten & Katalysatoren")
                if news:
                    for item in news:
                        st.markdown(f"- **[{item['title']}]({item['link']})** *({item['publisher']})*")
                else:
                    st.info("Keine aktuellen Nachrichten gefunden.")

    except Exception as e:
        st.error(f"Fehler beim Laden der Daten für {active_symbol}: {str(e)}")
