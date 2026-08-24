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

# Page Configuration
st.set_page_config(
    page_title="AI Börsen-Entscheidungs-System",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .metric-card {
        background-color: #1e222d;
        border-radius: 10px;
        padding: 15px;
        border: 1px solid #2e3546;
        margin-bottom: 10px;
    }
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
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
        "💼 Musterdepots & Live-Performance (2x 10.000 €)",
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
# MODE 3: MUSTERDEPOTS & LIVE-PERFORMANCE
# ==============================================================================
elif app_mode == "💼 Musterdepots & Live-Performance (2x 10.000 €)":
    st.title("💼 Autonome Musterdepots (2x 10.000 € Startkapital)")
    st.markdown("Zwei getrennte Echtzeit-Musterdepots: Eines für **aktives Kurz-/Mittelfrist-Trading** und eines für **langfristiges Qualitäts-Investing**.")

    pm = PortfolioManager(initial_capital_per_depot=10000.0)

    # Depot Selector
    selected_depot_key = st.radio(
        "Wähle das Depot:",
        [
            ("short_term", "⚡ Kurz-/Mittelfristiges Trading-Depot (Momentum & Squeeze)"),
            ("long_term", "🏛️ Langfristiges Investment-Depot (Quality & Value)")
        ],
        format_func=lambda x: x[1],
        horizontal=True
    )[0]

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

        short_results = short_engine.evaluate(prices_df, sentiment)
        long_results = long_engine.evaluate(fundamentals, consensus)
        synth_result = synthesizer.synthesize(short_results, long_results, fundamentals, consensus)
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
        tab_chart, tab_short_sellers, tab_breakout, tab_short, tab_long, tab_analysts = st.tabs([
            "📊 Interaktiver Chart & Signale",
            "🪤 Leerverkäufer & Short-Interest",
            "🚨 Ausbruchs-Signale & Volumen",
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
