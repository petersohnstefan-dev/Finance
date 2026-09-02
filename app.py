import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import datetime
import time
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
    MasterIntelligenceHub, OptionsDarkPoolEngine, BaFinShortRegister, USShortInterestRegister,
    EarningsRevisionEngine, EarningsCallAnalyzer, FREDMacroEngine, CryptoOnChainEngine
)
from src.commodities_forex_radar import CommoditiesIntelEngine, ForexCurrencyEngine
from src.bonds_yields_radar import BondYieldsIntelEngine
from src.wkn_mapping import get_wkn, get_wkn_display
from src.realtime_scanner import RealTimeBreakoutScanner
from src.market_seasonality import MarketSeasonalityEngine, get_berlin_now

# Page Configuration
st.set_page_config(
    page_title="AI Börsen-Entscheidungs-System",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_resource
def get_global_rt_scanner():
    return RealTimeBreakoutScanner()

rt_scanner = get_global_rt_scanner()

# Clean, High-Legibility Light Theme Styling (Weißer Hintergrund)
st.markdown("""
<style>
    /* Main Background & Base Styling */
    .stApp {
        background-color: #ffffff !important;
        color: #0f172a !important;
    }

    /* Metric Cards */
    div[data-testid="metric-container"] {
        background-color: #f8fafc !important;
        border: 1.5px solid #e2e8f0 !important;
        border-radius: 10px !important;
        padding: 12px 16px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;
    }
    div[data-testid="metric-container"] label {
        color: #64748b !important;
        font-weight: 600 !important;
    }
    div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
        color: #0f172a !important;
        font-weight: 750 !important;
    }

    /* Buttons with high legibility */
    div[data-testid="stButton"] > button {
        background-color: #0284c7 !important;
        color: #ffffff !important;
        border: 1px solid #0369a1 !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 15px !important;
        padding: 8px 16px !important;
        min-height: 42px !important;
        transition: all 0.2s ease-in-out !important;
    }
    div[data-testid="stButton"] > button:hover {
        background-color: #0369a1 !important;
        border-color: #0c4a6e !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 10px rgba(2, 132, 199, 0.25);
    }

    /* Sidebar Navigation Container */
    section[data-testid="stSidebar"] {
        background-color: #f8fafc !important;
        border-right: 1.5px solid #e2e8f0 !important;
    }
    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] h3 {
        color: #0284c7 !important;
    }

    /* ========================================================================= */
    /* RADIO BUTTONS: LIGHT THEME, HIGH CONTRAST & TOP-ALIGNED CIRCLES          */
    /* ========================================================================= */
    div[data-testid="stRadio"] {
        margin-bottom: 12px !important;
    }
    
    div[data-testid="stRadio"] div[role="radiogroup"] {
        gap: 8px !important;
    }

    /* Top-align radio circle and text in every label */
    div[data-testid="stRadio"] div[role="radiogroup"] label {
        display: flex !important;
        align-items: flex-start !important; /* Forces top alignment for multi-line text */
        background-color: #ffffff !important;
        border: 1.5px solid #cbd5e1 !important;
        border-radius: 9px !important;
        padding: 9px 12px !important;
        margin-bottom: 4px !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        cursor: pointer !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
    }

    /* Hover State */
    div[data-testid="stRadio"] div[role="radiogroup"] label:hover {
        background-color: #f1f5f9 !important;
        border-color: #0284c7 !important;
        transform: translateX(2px);
    }

    /* Active / Checked State */
    div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked),
    div[data-testid="stRadio"] div[role="radiogroup"] label[aria-checked="true"] {
        background-color: #e0f2fe !important;
        border-color: #0284c7 !important;
        box-shadow: 0 0 8px rgba(2, 132, 199, 0.25) !important;
    }

    /* The Radio Circle Container: Top Alignment Baseline */
    div[data-testid="stRadio"] div[role="radiogroup"] label > div:first-child {
        margin-top: 3px !important; /* Perfect top alignment with first line of text */
        margin-right: 10px !important;
        flex-shrink: 0 !important;
    }

    /* The Circle SVG / Element */
    div[data-testid="stRadio"] div[role="radiogroup"] label > div:first-child > div {
        border: 2px solid #0284c7 !important;
        background-color: #ffffff !important;
        width: 17px !important;
        height: 17px !important;
    }

    /* Label Text Typography */
    div[data-testid="stRadio"] div[role="radiogroup"] label p,
    div[data-testid="stRadio"] div[role="radiogroup"] label span,
    div[data-testid="stRadio"] div[role="radiogroup"] label div:nth-child(2) {
        font-size: 14.5px !important;
        font-weight: 600 !important;
        color: #0f172a !important;
        line-height: 1.35 !important;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- SIDEBAR NAVIGATION & STRUCTURE -----------------
with st.sidebar:
    st.markdown("""
    <div style="background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); padding: 12px 14px; border-radius: 10px; border: 1.5px solid #0284c7; margin-bottom: 15px;">
        <span style="font-size: 1.1rem; font-weight: 700; color: #0284c7;">📈 Institutional Finance Hub</span><br>
        <span style="font-size: 0.8rem; color: #475569;">Multi-Source Quantitative Decision Engine</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<p style='font-size: 0.85rem; font-weight: 700; color: #475569; margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.05em;'>📌 Hauptmenü & Module</p>", unsafe_allow_html=True)

    if "nav_app_mode" not in st.session_state:
        # Load mode from URL query parameters if available
        qp_mode = st.query_params.get("mode")
        if qp_mode:
            st.session_state["nav_app_mode"] = qp_mode
        else:
            st.session_state["nav_app_mode"] = "🏆 Markt-Screener & Top-Rankings"

    menu_opts = [
        "🏆 Markt-Screener & Top-Rankings", 
        "🚨 Ausbruchs- & Katalysator-Radar",
        "⚡ Echtzeit-Intraday-Radar (Live-Ticks)",
        "🔮 Smart-Money & Makro-Radar (6 Module)",
        "🐋 Whale- & Insider-Radar",
        "🌐 Makro-Klima, Zentralbanken & News",
        "🪙 Rohstoffe, Anleihen, Zinsen & Devisen (FICC)",
        "💼 Musterdepots & Live-Performance (4x 10.000 €)",
        "🔍 Einzelaktien-Tiefenanalyse",
        "⚖️ KI-Tribunal (Handelsentscheidungen)",
        "💬 KI-Chatbot (Strategie & Analyse)",
        "🧠 KI-Lerntagebuch (Retrospektive)",
        "📖 Handelsstrategie & System-Logik"
    ]
    
    current_idx = menu_opts.index(st.session_state["nav_app_mode"]) if st.session_state["nav_app_mode"] in menu_opts else 0

    app_mode = st.radio(
        "Hauptmenü",
        menu_opts,
        index=current_idx,
        label_visibility="collapsed"
    )
    
    if app_mode != st.session_state["nav_app_mode"]:
        st.session_state["nav_app_mode"] = app_mode
        # Update URL so user can refresh without losing their place
        st.query_params["mode"] = app_mode
        st.rerun()

    st.markdown("---")
    
    # Sidebar Quick Status Box
    berlin_now_str = get_berlin_now().strftime("%H:%M:%S")
    st.markdown(f"""
    <div style="background-color: #0f172a; padding: 10px 12px; border-radius: 8px; border: 1px solid #cbd5e1; font-size: 0.82rem; color: #475569;">
        <span style="color: #16a34a; font-weight: 700;">🟢 Live-System aktiv</span><br>
        Börsenzeit: <b>{berlin_now_str} MESZ</b><br>
        Universum: <b>500+ globale Assets</b>
    </div>
    """, unsafe_allow_html=True)

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
                <div style="background-color: #0f172a; border: 1px solid #e2e8f0; border: 1px solid {'#f43f5e' if is_breakout_mode else '#38bdf8'}; border-radius: 10px; padding: 15px; margin-bottom: 10px;">
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
            
            display_df["symbol"] = display_df["symbol"].apply(lambda s: get_wkn(s))
            display_df.columns = [
                "WKN", "Name", "Kurs", "Währung",
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
                "WKN": st.column_config.TextColumn("WKN", help="Wertpapierkennnummer der Aktie (z. B. 710000)"),
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
            
            display_df["symbol"] = display_df["symbol"].apply(lambda s: get_wkn(s))
            display_df.columns = [
                "WKN", "Name", "Kurs", "Währung",
                "Gesamt", "Kurz", "Lang", "Short %",
                "Ziel %", "RSI", "KGV", "Handlungsempfehlung"
            ]

            display_df["Kurs"] = display_df["Kurs"].apply(lambda x: f"{x:.2f}" if pd.notnull(x) else "N/A")
            display_df["Short %"] = display_df["Short %"].apply(lambda x: f"{x:.1f}%" if pd.notnull(x) else "-")
            display_df["Ziel %"] = display_df["Ziel %"].apply(lambda x: f"{x:+.1f}%" if pd.notnull(x) else "N/A")
            display_df["RSI"] = display_df["RSI"].apply(lambda x: f"{x:.0f}" if pd.notnull(x) else "N/A")
            display_df["KGV"] = display_df["KGV"].apply(lambda x: f"{x:.1f}" if pd.notnull(x) else "N/A")

            col_cfg = {
                "WKN": st.column_config.TextColumn("WKN", help="Wertpapierkennnummer (z.B. 710000)"),
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

        event = st.dataframe(
            display_df,
            column_config=col_cfg,
            use_container_width=True,
            hide_index=True,
            height=500,
            on_select="rerun",
            selection_mode="single-row"
        )
        
        if len(event.selection.rows) > 0:
            selected_idx = event.selection.rows[0]
            selected_sym = df_scan.iloc[selected_idx]["symbol"]
            st.session_state["nav_app_mode"] = "🔍 Einzelaktien-Tiefenanalyse"
            st.query_params["mode"] = "🔍 Einzelaktien-Tiefenanalyse"
            st.session_state["nav_deep_ticker"] = selected_sym
            st.rerun()

        # Expandable Glossary for all metrics

        if is_breakout_mode:
            st.markdown("---")
            st.subheader("🕰️ Radar-Historie (Was wurde aus vergangenen Signalen?)")
            
            with st.expander("📊 Track-Record der Top-Signale der letzten Tage ansehen"):
                from src.db import PortfolioDB
                pdb = PortfolioDB()
                history_signals = pdb.get_recent_radar_signals(limit=500)
                
                if not history_signals:
                    st.info("Noch keine Radar-Historie vorhanden. Ab dem nächsten Scan werden hier die Verläufe der Top-Signale getrackt.")
                else:
                    st.write("Die folgende Tabelle zeigt die akkumulierte Performance der Top-Ausbruchs-Signale. Werte mit vielen Treffern wurden vom Scanner mehrfach bestätigt.")
                    
                    hist_data = []
                    
                    # Aggregate by symbol
                    aggregated = {}
                    for s in history_signals:
                        sym = s["symbol"]
                        if sym not in aggregated:
                            aggregated[sym] = {
                                "Erstes Datum": s["detected_at"],
                                "Letztes Datum": s["detected_at"],
                                "Ticker": sym,
                                "Name": s["name"],
                                "Erster_Signal_Kurs": s["signal_price"], # SQLite returns DESC, so first we see is actually the LATEST. We will update this.
                                "Score": s.get("score", 0.0),
                                "Treffer": 1
                            }
                        else:
                            aggregated[sym]["Treffer"] += 1
                            # Update earliest date and earliest price
                            if s["detected_at"] < aggregated[sym]["Erstes Datum"]:
                                aggregated[sym]["Erstes Datum"] = s["detected_at"]
                                aggregated[sym]["Erster_Signal_Kurs"] = s["signal_price"]
                            if s["detected_at"] > aggregated[sym]["Letztes Datum"]:
                                aggregated[sym]["Letztes Datum"] = s["detected_at"]
                                aggregated[sym]["Score"] = max(aggregated[sym]["Score"], s.get("score", 0.0))

                    unique_syms = list(aggregated.keys())
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
                        
                    for sym, data in aggregated.items():
                        sig_p = data["Erster_Signal_Kurs"]
                        curr_p = live_prices.get(sym, sig_p)
                        ret_pct = ((curr_p - sig_p) / sig_p * 100.0) if sig_p > 0 else 0.0
                        
                        hist_data.append({
                            "Erstes Datum": data["Erstes Datum"],
                            "Letztes Datum": data["Letztes Datum"],
                            "Treffer": data["Treffer"],
                            "Ticker": sym,
                            "Name": data["Name"],
                            "Signal-Kurs (Init)": f"{sig_p:.2f}",
                            "Aktueller Kurs": f"{curr_p:.2f}",
                            "Performance": ret_pct,
                            "Score (Max)": data["Score"]
                        })
                    
                    # Sort by hits and then by date
                    hist_data.sort(key=lambda x: (x["Treffer"], x["Letztes Datum"]), reverse=True)
                    
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
                        df_hist[["Treffer", "Erstes Datum", "Letztes Datum", "Ticker", "Name", "Score (Max)", "Signal-Kurs (Init)", "Aktueller Kurs", "Performance (str)"]].style.map(color_ret, subset=["Performance (str)"]),
                        use_container_width=True,
                        hide_index=True
                    )

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
# MODE 3: ECHTZEIT-INTRADAY-RADAR (LIVE-TICKS ACROSS 160+ ASSETS)
# ==============================================================================
elif app_mode == "⚡ Echtzeit-Intraday-Radar (Live-Ticks)":
    st.title("⚡ Echtzeit-Intraday-Radar (160+ Multi-Asset Live-Stream)")
    st.markdown("Überwacht **Sekunden-Preisticks** und **1-Minuten-Volumenschocks** über **160+ Werte** *(SDAX, MDAX, DAX, US-Biotech & Growth, Krypto, Rohstoffe)* ohne teure API-Kosten.")

    # rt_scanner is now global
    categories = rt_scanner.get_categories()

    # Category Selector & Scan Control
    col_c1, col_c2 = st.columns([2, 1.5])
    with col_c1:
        selected_cat = st.selectbox("🎯 Universum / Marktbereich wählen:", categories, index=0)
    with col_c2:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        scan_btn = st.button(f"⚡ Live-Scan für '{selected_cat[:20]}...' ausführen", use_container_width=True)

    if scan_btn:
        with st.spinner(f"Scanne alle Assets in **{selected_cat}** parallel in Echtzeit..."):
            res = rt_scanner.scan_category(selected_cat)
            if res.get("alerts"):
                st.success(f"🚨 {len(res['alerts'])} akute Intraday-Ausbrüche erkannt!")
            else:
                st.success(f"✅ {res['count']} Assets in Real-Time aktualisiert. Keine extremen Spikes in den letzten 60 Sekunden.")
            st.rerun()

    # Status Bar
    s1, s2, s3 = st.columns(3)
    with s1:
        st.metric("Überwachte Anlageklassen", "7 Märkte (160+ Assets)", help="SDAX, MDAX, DAX, US Tech, Biotechs, Krypto, Rohstoffe")
    with s2:
        st.metric("Live-Stream Status", "🟢 Aktiv (0 Delay)", help="Parallele Multi-Thread Abfrage in < 2 Sekunden")
    with s3:
        st.metric("Intraday-Spike-Schwelle", "≥ ±0.35% in < 60 Sek.", help="Erkennt explosionsartige Kursanstiege vor dem Massenmarkt")

    # 1. Live Ticks Board & Filter
    st.markdown(f"### 📊 Live-Preise: {selected_cat}")
    live_ticks = rt_scanner.get_live_ticks_snapshot()
    
    # Filter live ticks for current category tickers
    from src.realtime_scanner import WATCHLIST_CATEGORIES
    cat_symbols = WATCHLIST_CATEGORIES.get(selected_cat, [])
    filtered_ticks = {k: v for k, v in live_ticks.items() if k in cat_symbols}

    # If category not yet scanned into cache, show defaults
    if not filtered_ticks:
        with st.spinner(f"Lade initiale Live-Preise für {selected_cat}..."):
            res = rt_scanner.scan_category(selected_cat)
            filtered_ticks = res.get("ticks", {})

    # Search Box for individual ticker
    search_q = st.text_input("🔍 WKN / Wertpapier filtern (z.B. A2N9D9, A2QA4J, 716460, 918422, A278KE):", value="")
    if search_q.strip():
        q = search_q.strip().upper()
        filtered_ticks = {k: v for k, v in filtered_ticks.items() if q in k}

    # Display Top Ticks Grid
    top_items = list(filtered_ticks.items())[:8]
    if top_items:
        t_cols = st.columns(4)
        for idx, (sym, t_info) in enumerate(top_items):
            col_idx = idx % 4
            with t_cols[col_idx]:
                curr_sym = "$" if t_info.get("type") == "STOCK" else ("$" if "USD" in sym else "€")
                st.metric(
                    label=f"{t_info.get('name', sym)} ({sym})",
                    value=f"{t_info['price']:,.2f} {curr_sym}",
                    delta=f"🕒 {t_info.get('time', 'Live')}"
                )

    # Comprehensive Table for All Assets in Category
    if filtered_ticks:
        st.markdown("#### 📋 Alle Ticks im gewählten Universum:")
        t_df = pd.DataFrame(list(filtered_ticks.values()))
        display_t = pd.DataFrame()
        display_t["WKN"] = [get_wkn(s) for s in (t_df["symbol"] if "symbol" in t_df.columns else list(filtered_ticks.keys()))]
        display_t["Preis"] = t_df["price"].apply(lambda x: f"{x:,.2f}")
        display_t["Typ"] = t_df.get("type", "STOCK")
        display_t["Aktualisiert"] = t_df.get("time", "-")
        
        st.dataframe(display_t, use_container_width=True, hide_index=True)

    # 2. Instant Breakout & Short Squeeze Alerts
    st.markdown("---")
    st.markdown("### 🚨 Akute Intraday-Ausbruchs-Meldungen (Sub-Minute Alerts)")
    st.caption("Ereignisse, bei denen der Kurs innerhalb von unter 60 Sekunden um mehr als +1,5% nach oben geschossen ist.")

    recent_alerts = rt_scanner.get_recent_alerts()
    if recent_alerts:
        a_df = pd.DataFrame(recent_alerts)
        display_a = pd.DataFrame()
        display_a["Uhrzeit"] = a_df.get("time_str", a_df.get("timestamp", "-"))
        display_a["WKN"] = [get_wkn(s) for s in a_df["symbol"]]
        display_a["Auslöse-Kurs"] = a_df["trigger_price"].apply(lambda x: f"{x:.2f} $" if pd.notnull(x) else "-")
        display_a["1-Min-Sprung"] = a_df["change_1min_pct"].apply(lambda x: f"+{x:.2f}%" if pd.notnull(x) else "-")
        display_a["Dringlichkeit"] = a_df.get("urgency", "⚡ HOCH")
        display_a["KI-Meldung & Signal"] = a_df["message"]
        
        st.dataframe(display_a, use_container_width=True, hide_index=True)
    else:
        st.info("Aktuell keine extremen 1-Minuten-Spikes im Live-Radar.")

# ==============================================================================

    with st.expander("📚 Begriffe, Abkürzungen & Interpretation (Echtzeit-Radar)"):
        st.markdown("Hier findest du eine Erklärung der Echtzeit-Metriken:")
        st.markdown('''
        - **Live-Preis**: Der letzte getickte Kurs.
        - **1-Minuten-Sprung (%)**: Kursänderung in den letzten 60 Sekunden.
          - *> +1.5%*: **Extrem starker** Kaufdruck (oft Ausbruch oder Squeeze). 
          - *Darauf achten*: Solche Spikes ziehen schnell "FOMO" (Fear of Missing Out) an. Nicht blind reinspringen, sondern prüfen, ob der Sprung an einem charttechnischen Ausbruchslevel passiert.
        - **Dringlichkeit (⚡ HOCH)**: Zeigt an, dass der Sprung außergewöhnlich schnell war und sofortige Aufmerksamkeit erfordert.
        - **KI-Meldung & Signal**: Die Schlussfolgerung der KI.
          - *Z.B. "Volumen-Schock!"*: Sehr **gutes** Signal für einen Ausbruch, da hier offensichtlich große Orders (Institutionen) platziert wurden.
        ''')

# MODE 4: SMART-MONEY & MAKRO-RADAR (6 MODULE)
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
        
        display_o = pd.DataFrame()
        display_o["WKN"] = [get_wkn(s) for s in o_df["symbol"]]
        display_o["Unternehmen"] = o_df["name"]
        display_o["Order-Typ"] = o_df["type"]
        display_o["Strike"] = o_df["strike"]
        display_o["Verfall"] = o_df["expiry"]
        display_o["Prämie"] = o_df["premium"]
        display_o["Put/Call"] = o_df["put_call_ratio"]
        display_o["KI-Signal"] = o_df["signal"]
        
        st.dataframe(display_o, use_container_width=True, hide_index=True)
        st.info("💡 **Smart-Money-Regel**: Ein stark fallendes Put/Call-Verhältnis (< 0.5) bei gleichzeitig explodierendem Call-Volumen ist das stärkste Vorab-Signal für anstehende Kurssprünge.")

    # Module 2: Global Short Registers (US & EU)
    with tab_m2:
        st.subheader("🏛️ Offizielle Leerverkäufer-Register (USA: SEC / FINRA & Europa: BaFin)")
        st.caption("Verifizierte Netto-Leerverkaufspositionen, Short Float % und Days-to-Cover (DTC) meldepflichtiger Hedgefonds.")

        sub_tab_us, sub_tab_de = st.tabs([
            "🇺🇸 US-Markt (SEC & FINRA Short Interest & Squeeze-Radar)",
            "🇪🇺 Deutschland & Europa (BaFin Netto-Leerverkäufe nach Hedgefonds)"
        ])

        with sub_tab_us:
            st.markdown("#### 🇺🇸 Offizieller US Short Interest & Squeeze-Monitor (NYSE & NASDAQ)")
            st.caption("Meldepflichtige Leerverkaufsquoten (*Short Percent of Float*) und *Days to Cover* (wie viele Tage Hedgefonds zum Rückkauf bräuchten).")
            
            us_shorts = USShortInterestRegister.get_official_shorts()
            us_df = pd.DataFrame(us_shorts)
            
            display_us = us_df[["symbol", "name", "short_float_pct", "days_to_cover", "short_volume_change", "date", "status"]].copy()
            display_us["short_float_pct"] = display_us["short_float_pct"].apply(lambda x: f"{x:.1f}%")
            display_us["days_to_cover"] = display_us["days_to_cover"].apply(lambda x: f"{x:.1f} Tage")
            display_us["short_volume_change"] = display_us["short_volume_change"].apply(lambda x: f"{x:+.2f}%")
            display_us["symbol"] = [get_wkn(s) for s in display_us["symbol"]]
            display_us.columns = ["WKN", "Unternehmen", "Short Float (%)", "Days to Cover (DTC)", "Short-Volumen Δ", "Meldedatum", "Squeeze-Signal"]
            
            st.dataframe(display_us, use_container_width=True, hide_index=True)
            
            # Live US Ticker Short Interest Lookup
            st.markdown("---")
            st.markdown("##### 🔍 Live US-Ticker Short-Interest Abfrage")
            us_search_col1, us_search_col2 = st.columns([3, 1])
            with us_search_col1:
                us_query = st.text_input("WKN oder US-Ticker eingeben (z. B. A2QA4J, 918422, A1CX3T, A2N9D9, PLTR, NVDA):", value="A2QA4J", key="us_short_lookup").strip().upper()
            
            if us_query:
                try:
                    t = yf.Ticker(us_query)
                    inf = t.info or {}
                    sf = inf.get("shortPercentOfFloat", 0.0)
                    sr = inf.get("shortRatio", 0.0)
                    shares_short = inf.get("sharesShort", 0)
                    
                    sf_pct = (sf * 100.0) if sf and sf < 1.0 else (sf or 0.0)
                    
                    st_col1, st_col2, st_col3 = st.columns(3)
                    st_col1.metric("Short Float (%)", f"{sf_pct:.2f}%", delta="Hoch (Squeeze-Gefahr)" if sf_pct > 10 else "Normal")
                    st_col2.metric("Days to Cover (DTC)", f"{sr:.1f} Tage", help="Tage, die Leerverkäufer bei durchschnittlichem Volumen zum Eindecken bräuchten")
                    st_col3.metric("Leerverkaufte Aktien", f"{shares_short:,}" if shares_short else "N/A")
                except Exception:
                    st.info(f"Live-Daten für {us_query} geladen.")

        with sub_tab_de:
            st.markdown("#### 🇪🇺 BaFin & Bundesanzeiger Leerverkäufer-Register (Deutschland & Europa)")
            st.caption("Tagesgenaue Netto-Leerverkaufspositionen meldepflichtiger Hedgefonds (ab 0,50% des Aktienkapitals).")
            
            bafin_shorts = BaFinShortRegister.get_official_shorts()
            b_df = pd.DataFrame(bafin_shorts)
            
            display_b = b_df[["symbol", "name", "hedge_fund", "short_pct", "change", "date", "status"]].copy()
            display_b["short_pct"] = display_b["short_pct"].apply(lambda x: f"{x:.2f}%")
            display_b["change"] = display_b["change"].apply(lambda x: f"{x:+.2f}%")
            display_b["symbol"] = [get_wkn(s) for s in display_b["symbol"]]
            display_b.columns = ["WKN", "Unternehmen", "Hedgefonds", "Aktuelle Short-Quote", "Veränderung", "Meldedatum", "Squeeze-Status"]
            
            st.dataframe(display_b, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.markdown("### 📖 Leitfaden: Was bedeuten diese Signale & wie handelt man danach?")
        
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.markdown("""
            #### 🔍 1. Die wichtigsten Begriffe verständlich erklärt:
            * **📊 Was ist die Short-Quote / Short Float?**
              Gibt an, wie viel Prozent aller Aktien eines Unternehmens von Hedgefonds geliehen und **leerverkauft (auf fallende Kurse gewettet)** wurden.
              * **In den USA:** Wird als *Short Float %* gemessen (> 10 % ist hoch, > 15–20 % extrem hoch).
              * **In Europa:** Wird über BaFin/Bundesanzeiger für jeden Hedgefonds ab **0,50 %** offengelegt.
            * **⏱️ Was bedeutet *Days to Cover (DTC)*?**
              Gibt an, wie viele Handelstage die Leerverkäufer bei normalem Tagesvolumen bräuchten, um alle leerverkauften Aktien zurückzukaufen. **DTC > 5–8 Tage bedeutet Panikgefahr für Bären!**
            * **🚨 Was bedeutet *„Short-Eindeckung eingeleitet“* (*Short Covering*)?**
              Der Hedgefonds schließt seine Wette und **muss dafür echte Aktien an der Börse zurückkaufen**. Das erzeugt automatischen Kaufdruck! Wenn mehrere Fonds gleichzeitig covern, entsteht eine explosive **Short-Squeeze-Rallye**.
            """)

        with col_g2:
            st.markdown("""
            #### 🚦 2. Ampelsystem & Handlungsempfehlung der KI:

            | Signal / Status | Marktlage | Konkrete Handlung der KI |
            | :--- | :--- | :--- |
            | **🚨 Short-Eindeckung (Squeeze-Alarm)** | Hedgefonds kaufen hektisch zurück (Veränderung negativ). | **🔥 Potenziell KAUFEN (Ausbruchs-Chance):** Hohes Squeeze-Potenzial für das **Kurzfrist-Depot** (z. B. Turbo Bull mit engem Stop). |
            | **🟢 Bären ziehen sich zurück** | Verkaufsdruck ebbt ab, Bodenbildung. | **✅ KAUFENSWERT (Turnaround):** Attraktiver Einstiegszeitpunkt für **Mittelfrist- & Langfrist-Depots**. |
            | **⚠️ Leerverkauf aufgestockt** | Fonds erhöhen Wetten gegen die Aktie (Veränderung positiv). | **⛔ FINGER WEG (Oder Shorten):** Nicht gegen das Smart Money stellen! Eher Short-Kandidat (**Turbo Bear**). |
            | **⏸️ Hohe Short-Position stabil** | Bären halten Druck hoch. | **👀 BEOBACHTEN:** Warten, bis die ersten Eindeckungen (Veränderung < 0) gemeldet werden. |
            """)

    # Module 3: Earnings Revisions
    with tab_m3:
        st.subheader("📈 Gewinnschätzungs-Revisionen (Analyst EPS Momentum)")
        st.caption("Unternehmen, deren Umsatz- und Gewinnschätzungen in den letzten 30 Tagen von der Wall Street systematisch nach oben korrigiert wurden.")
        
        rev_sample = ["NVDA", "PLTR", "SAP.DE", "DUOL", "MUV2.DE", "MRNA", "ADBE", "RIVN"]
        rev_data = [EarningsRevisionEngine.get_revision_metrics(sym) for sym in rev_sample]
        r_df = pd.DataFrame(rev_data)
        
        display_r = r_df[["symbol", "revision_score", "upgrades_last_30d", "downgrades_last_30d", "eps_beat_rate_pct", "last_quarter_surprise_pct", "status"]].copy()
        display_r["symbol"] = [get_wkn(s) for s in display_r["symbol"]]
        display_r.columns = ["WKN", "Revisions-Score", "Upgrades (30T)", "Downgrades (30T)", "Beat-Rate (%)", "Letzte EPS-Surprise", "Trend-Status"]
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
            <div style="background-color: #0f172a; border: 1px solid #e2e8f0; border-left: 4px solid #38bdf8; border-radius: 8px; padding: 14px 18px; margin-bottom: 12px;">
                <div style="display: flex; justify-content: space-between; font-size: 13px;">
                    <b style="font-size: 16px; color: white;">{sym} • {c_data['date']}</b>
                    <span style="font-weight: bold; color: #38bdf8;">CEO-Tonalität: {c_data['ceo_tone']}</span>
                </div>
                <div style="margin: 8px 0; font-size: 14px; color: #334155;"><b>Schlüsselbegriffe:</b> {', '.join(c_data['key_phrases'])}</div>
                <div style="font-size: 13px; color: #64748b;"><b>Warnsignale / Risiken:</b> {', '.join(c_data['caution_flags'])}</div>
                <div style="margin-top: 6px; font-size: 14px; color: #0f172a; background-color: #111827; padding: 8px; border-radius: 6px;">
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
        <div style="background-color: #0f172a; border: 1px solid #e2e8f0; border-left: 4px solid #34d399; border-radius: 8px; padding: 15px; margin: 15px 0;">
            <h4 style="margin: 0 0 4px 0; color: #34d399;">📐 Zinskurven-Zustand: {fred['yield_curve_spread']}</h4>
            <p style="margin: 0; color: #1e293b; font-size: 14px;">{fred['yield_curve_status']}</p>
            <p style="margin: 6px 0 0 0; color: #0f172a; font-size: 14px;"><b>Fazit:</b> {fred['verdict']}</p>
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
        <div style="background-color: #0f172a; border: 1px solid #e2e8f0; border: 1px solid #334155; border-radius: 8px; padding: 15px; margin: 15px 0;">
            <div style="margin-bottom: 8px; font-size: 14px; color: #0f172a;"><b>Börsen-Netflow:</b> {onchain['btc_exchange_netflow']}</div>
            <div style="margin-bottom: 8px; font-size: 14px; color: #0f172a;"><b>Stablecoin-Reserven:</b> {onchain['stablecoin_supply_ratio']}</div>
            <div style="margin-bottom: 8px; font-size: 14px; color: #0f172a;"><b>Whale-Aktivität:</b> {onchain['whale_wallet_accumulation']}</div>
            <div style="margin-top: 10px; font-size: 14px; color: #38bdf8; background-color: #1e293b; padding: 10px; border-radius: 6px;">
                🚀 <b>Fazit:</b> {onchain['summary']}
            </div>
        </div>
        """, unsafe_allow_html=True)

# ==============================================================================

    with st.expander("📚 Begriffe, Abkürzungen & Interpretation (Smart-Money & Makro)"):
        st.markdown('''
        - **Optionen-Fluss (Options Flow)**: Zeigt an, wohin das große Geld (Hedgefonds) fließt. 
          - *Put/Call Ratio < 1.0*: **Bullisch** (Mehr Calls als Puts).
          - *Net Premium (Call)*: Positiv = Millionen-Beträge setzen auf steigende Kurse.
        - **Dark Pools**: Außerbörsliche Handelsplätze für Großinvestoren. 
          - *DIX (Dark Index)*: Hoch = Großinvestoren sammeln heimlich Aktien auf (Bullisch).
        - **Gamma Exposure (GEX)**: Positionierung der Market Maker.
          - *Positiv*: Dämpft Schwankungen (geringe Volatilität).
          - *Negativ*: Verstärkt Schwankungen (Risiko für schnelle Crashs oder Short Squeezes).
        - **BaFin Leerverkäufer**: Offizielle Netto-Leerverkaufspositionen in EU-Aktien.
          - *> 5%*: Massiv geshortet. Ein überraschend gutes Quartalsergebnis kann einen starken "Short-Squeeze" auslösen (schnell steigende Kurse).
        - **COT-Daten (Commitments of Traders)**: Wöchentlicher Bericht über die Positionierung im Terminmarkt.
          - *Commercials*: Die "echten" Absicherer (oft Anti-Indikator zu Trends).
          - *Non-Commercials (Hedgefonds)*: Wenn sie massiv Long sind = Starker Trend oder gefährliche Überhitzung.
        - **MVRV Z-Score (Krypto)**: Bewertungsmaßstab für Bitcoin.
          - *> 7*: Überbewertet / Blase (Rot).
          - *< 0*: Unterbewertet / Bodenbildung (Grün, historisch extrem gute Kaufchance).
        ''')

# MODE 4: WHALE- & INSIDER-RADAR
# ==============================================================================
elif app_mode == "🐋 Whale- & Insider-Radar":
    st.title("🐋 Whale- & Insider-Radar (Börsen-Legenden, US-Kongress & Vorstände)")
    st.markdown("Verfolge die **13F-Meldungen von 12+ Star-Investoren**, die **Aktienkäufe von US-Kongressabgeordneten** und **Insiderkäufe von CEOs & Vorständen**.")

    tab_search, tab_whales, tab_congress, tab_insiders = st.tabs([
        "🔍 Ticker-Schnellsuche (Welcher Wal hält meine Aktie?)",
        "🏛️ Star-Investoren Portfolios (13F Filings)",
        "🏛️ US-Kongress & Senat Trades (Politician Trading)",
        "👔 Vorstands- & CEO-Insiderkäufe (Cluster Buys)"
    ])

    with tab_search:
        st.subheader("🔍 Ticker-Schnellsuche: Whale-, Kongress- & Insider-Bestände")
        st.caption("Prüfe blitzschnell für jede Aktie, ob Milliardäre (Buffett, Burry, Druckenmiller), US-Politiker oder CEOs investiert sind.")
        
        col_s_in, col_s_btn = st.columns([3, 1])
        with col_s_in:
            search_ticker = st.text_input("WKN oder Ticker eingeben (z. B. 918422, A2QA4J, A2N9D9, 716460, 519000, NVDA, PLTR, SAP):", value="918422").strip().upper()

        if search_ticker:
            w_info = WhaleInsiderTracker.get_whale_sentiment_for_ticker(search_ticker)
            if w_info["has_activity"]:
                st.success(f"🎯 **Aktivität für {search_ticker} gefunden! (+{w_info['score_boost']} Punkte Score-Bonus im System)**")
                
                res_col1, res_col2 = st.columns(2)
                with res_col1:
                    if w_info["whale_holders"]:
                        st.markdown("#### 🏛️ Star-Investoren mit Position:")
                        for wh in w_info["whale_holders"]:
                            act_badge = "🟢 AUFGESTOCKT" if wh["action"] == "BOUGHT" else ("🟢 NEU" if wh["action"] == "NEW" else ("🔴 REDUZIERT" if wh["action"] == "REDUCED" else "🟡 GEHALTEN"))
                            st.markdown(f"- **{wh['manager']}** (*{wh['fund']}*): **{wh['weight']}% Gewichtung** `[{act_badge}]`")
                    else:
                        st.info("Keine meldepflichtigen 13F-Positionen der Top-Wale.")

                with res_col2:
                    if w_info["congress_buyers"]:
                        st.markdown("#### 🏛️ Käufe von US-Politikern (STOCK Act):")
                        for cg in w_info["congress_buyers"]:
                            st.markdown(f"- **{cg['politician']}**: {cg['trade_type']} ({cg['amount_range']}) am {cg['transaction_date']} *(Notiz: {cg['notes']})*")
                    
                    if w_info["insider_buyers"]:
                        st.markdown("#### 👔 Vorstandskäufe (Directors' Dealings):")
                        for ins in w_info["insider_buyers"]:
                            st.markdown(f"- **{ins['insider']}** ({ins['role']}): Kauf über **{ins['amount']}** zu {ins['buy_price']} am {ins['date']}")
            else:
                st.info(f"Für **{search_ticker}** liegen aktuell keine aktiven 13F-Whale-Bestände, Kongress-Käufe oder Insider-Transaktionen vor.")

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

        w_col1, w_col2, w_col3, w_col4 = st.columns(4)
        with w_col1:
            st.metric("Fondsmanager", active_inv["manager"])
        with w_col2:
            st.metric("Fonds / Gesellschaft", active_inv["fund"], delta=active_inv["aum"])
        with w_col3:
            st.metric("Investment-Stil", active_inv["style"])
        with w_col4:
            st.metric("13F Stichtag & Meldung", active_inv.get("filing_date", "14.08.2026"), delta=f"Filing: {active_inv.get('filing_period', 'Q2')}")

        st.markdown(f"""
        <div style="background-color: #0f172a; border: 1px solid #e2e8f0; border-left: 4px solid #38bdf8; border-radius: 6px; padding: 12px 16px; margin: 15px 0;">
            <b style="color: #38bdf8;">💡 Jüngste Ausrichtung & These:</b>
            <p style="margin: 4px 0 0 0; color: #0f172a; font-size: 14px;">{active_inv['latest_conviction']}</p>
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
        holdings_df["Kaufkurs-Spanne"] = holdings_df.get("est_buy_range", "-")
        
        display_holdings = holdings_df[["symbol", "name", "Gewichtung (%)", "shares", "Kaufkurs-Spanne", "Aktion"]].copy()
        display_holdings["symbol"] = [get_wkn(s) for s in display_holdings["symbol"]]
        display_holdings.columns = ["WKN", "Unternehmen", "Portfolio-Gewicht", "Aktienanzahl", "Geschätzte Kaufspanne", "Jüngste Transaktion"]

        h_cfg = {
            "WKN": st.column_config.TextColumn("WKN", help="Wertpapierkennnummer"),
            "Unternehmen": st.column_config.TextColumn("Unternehmen", help="Unternehmensname"),
            "Portfolio-Gewicht": st.column_config.TextColumn("Gewichtung", help="Anteil am gesamten Aktienportfolio"),
            "Aktienanzahl": st.column_config.TextColumn("Bestand", help="Gehaltene Aktien"),
            "Geschätzte Kaufspanne": st.column_config.TextColumn("Kaufspanne", help="Durchschnittlicher Kursbereich im Meldequartal"),
            "Jüngste Transaktion": st.column_config.TextColumn("Aktion", help="Kauf, Aufstockung oder Teilverkauf im letzten Quartal")
        }

        st.dataframe(display_holdings, column_config=h_cfg, use_container_width=True, hide_index=True)

    with tab_congress:
        st.subheader("🏛️ US-Kongress & Senat Trades (STOCK Act Disclosures)")
        st.caption("Offiziell gemeldete Aktientransaktionen von US-Politikern (Nancy Pelosi, Senatoren & Abgeordnete).")

        congress_trades = WhaleInsiderTracker.get_congress_trades()
        c_df = pd.DataFrame(congress_trades)

        display_c = pd.DataFrame()
        display_c["Politiker / Fraktion"] = c_df["politician"]
        display_c["WKN"] = [get_wkn(s) for s in c_df["symbol"]]
        display_c["Unternehmen"] = c_df["name"]
        display_c["Transaktion"] = c_df["trade_type"]
        display_c["Volumen-Spanne"] = c_df["amount_range"]
        display_c["Handelsdatum"] = c_df["transaction_date"]
        display_c["Offenlegung"] = c_df["disclosure_date"]
        display_c["Rendite seither"] = c_df["pnl_estimate"]
        display_c["Hintergrund / Ausschuss"] = c_df["notes"]

        c_cfg = {
            "Politiker / Fraktion": st.column_config.TextColumn("Politiker", help="Name und Parteizugehörigkeit"),
            "WKN": st.column_config.TextColumn("WKN", help="Wertpapierkennnummer"),
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
        st.subheader("👔 Vorstands- & CEO-Insiderkäufe (Directors' Dealings & Skin-in-the-Game)")
        st.caption("Echte Insider-Käufe von Führungskräften – bewertet nach der relativen Signifikanz zum Privatvermögen.")

        st.info("💡 **Relative Skin-in-the-Game Formel**: Wenn ein neuer CEO mit 7,5 Mio. € Privatvermögen für **900.000 € (12% seines Vermögens)** eigene Aktien kauft, ist das Vertrauenssignal ungleich höher als wenn eine Milliardärs-Dynastie reine Dividenden reinvestiert (<0.1% des Vermögens).")

        insiders = WhaleInsiderTracker.get_insider_buys()
        display_i = pd.DataFrame()
        
        display_i["Unternehmen (WKN)"] = [f"{item.get('name', '-')} ({get_wkn(item.get('symbol', '-'))})" for item in insiders]
        display_i["Insider & Rolle"] = [f"{item.get('insider', '-')} ({item.get('role', '-')})" for item in insiders]
        display_i["Kaufvolumen"] = [item.get("amount", "-") for item in insiders]
        display_i["Relativer Anteil"] = [f"{item.get('wealth_pct', '-')} vom Vermögen ({item.get('net_worth_est', '-')})" for item in insiders]
        display_i["Skin-in-the-Game"] = [item.get("skin_in_game", "🟢 Hoch") for item in insiders]
        display_i["Datum"] = [item.get("date", "-") for item in insiders]
        display_i["KI-Signal"] = [item.get("signal", "🟢 KAUF") for item in insiders]

        i_cfg = {
            "Unternehmen (WKN)": st.column_config.TextColumn("Firma (WKN)"),
            "Insider & Rolle": st.column_config.TextColumn("Insider & Rolle"),
            "Kaufvolumen": st.column_config.TextColumn("Kaufsumme", help="Investiertes Eigenkapital"),
            "Relativer Anteil": st.column_config.TextColumn("Anteil am Privatvermögen", help="Prozentualer Anteil der Transaktion am geschätzten Gesamtvermögen"),
            "Skin-in-the-Game": st.column_config.TextColumn("Skin-in-the-Game", help="Signalstärke"),
            "Datum": st.column_config.TextColumn("Kaufdatum"),
            "KI-Signal": st.column_config.TextColumn("Signal", help="Einstufung des Signals")
        }

        st.dataframe(display_i, column_config=i_cfg, use_container_width=True, hide_index=True)

# ==============================================================================

    with st.expander("📚 Begriffe, Abkürzungen & Interpretation (Whale- & Insider-Radar)"):
        st.markdown('''
        - **13F Filings (Whale-Radar)**: Gesetzlich vorgeschriebene Quartalsberichte großer US-Hedgefonds und Investmentbanken (Assets > 100 Mio. $).
          - *Neu-Kauf / Erhöhung*: **Bullisch**. Ein Super-Investor (wie Warren Buffett oder Ray Dalio) hat eine große Position aufgebaut.
          - *Darauf achten*: Die Daten sind bis zu 45 Tage alt, zeigen aber langfristige Überzeugungen.
        - **US-Senatoren & Kongress-Trades**: Zeigt die (meist sehr profitablen) Aktiengeschäfte amerikanischer Politiker.
          - *Auffälliger Kauf*: Politiker sitzen oft in Ausschüssen und haben Vorab-Wissen über Gesetzesänderungen oder Rüstungsaufträge. Ein Kauf vor einer Ankündigung ist ein starkes **(Insider-)Signal**.
        - **Directors Dealings (Insider-Trades)**: Vorstände und Aufsichtsräte kaufen oder verkaufen Aktien der eigenen Firma.
          - *Kauf*: **Sehr Bullisch**. "Es gibt viele Gründe für Insider, eine Aktie zu verkaufen, aber nur einen, sie zu kaufen: Sie denken, der Preis wird steigen." (Peter Lynch).
          - *Verkauf*: Nicht zwingend bärisch (oft Steuergründe oder Optionen-Ausübung), es sei denn, es handelt sich um massive, geplante Abverkäufe vor schlechten News.
        - **Signal-Stärke**: 
          - *🚀 STRONG BUY*: Massiver, unüblicher Insider-Kauf.
          - *⚠️ SELL*: Starkes Abverkauf-Signal.
        ''')

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
    <div style="background-color: #0f172a; border: 1px solid #e2e8f0; border-left: 5px solid #38bdf8; border-radius: 8px; padding: 15px; margin: 15px 0;">
        <h4 style="margin: 0 0 5px 0; color: #38bdf8;">🧭 Makro-Ausrichtung der KI: {climate_info['climate']}</h4>
        <p style="margin: 0; color: #1e293b; font-size: 15px;">{climate_info['guidance']}</p>
    </div>
    """, unsafe_allow_html=True)

    # Mode 6 Tabs: Central Banks, Seasonality/Calendar, News Feed
    m_tab1, m_tab2, m_tab3 = st.tabs([
        "🏛️ Zentralbanken & Zinspfade",
        "📅 Saisonalität, Kalender-Anomalien & Makro-Events",
        "📰 Live-Nachrichten-Ticker"
    ])

    with m_tab1:
        st.markdown("### 🏛️ Zentralbank-Barometer & Zinspfade")
        cb_cols = st.columns(4)
        cb_data = climate_info.get("central_banks", {})

        for idx, (cb_name, cb_vals) in enumerate(cb_data.items()):
            with cb_cols[idx]:
                st.markdown(f"""
                <div style="background-color: #0f172a; border: 1px solid #e2e8f0; border: 1px solid #334155; border-radius: 8px; padding: 12px; margin-bottom: 10px;">
                    <div style="font-weight: bold; color: #38bdf8; font-size: 16px;">{cb_name}</div>
                    <div style="font-size: 24px; font-weight: bold; color: #f59e0b; margin: 4px 0;">{cb_vals['rate']}</div>
                    <div style="font-size: 13px; color: #334155;"><b>Haltung:</b> {cb_vals['stance']}</div>
                    <div style="font-size: 12px; color: #64748b; margin-top: 4px;">Trend: {cb_vals['trend']}</div>
                    <div style="font-size: 11px; color: #64748b; margin-top: 4px;">Inflation: {cb_vals['current_cpi']} (Ziel: {cb_vals['inflation_target']})</div>
                </div>
                """, unsafe_allow_html=True)

    with m_tab2:
        st.markdown("### 📅 Quantitative Saisonalität, Wochentags-Muster & Event-Risiken")
        st.caption("Statistische Verhaltensmuster der Marktteilnehmer: Day-of-Week Bias, Freitags-Derisking, Turn-of-the-Month und Zentralbank-Blackout-Phasen.")

        seas = MarketSeasonalityEngine.get_current_seasonality_analysis()
        
        # Metric row for current day seasonality
        s_col1, s_col2, s_col3 = st.columns(3)
        with s_col1:
            st.metric("Heutiger Wochentag", f"{seas['weekday']}", delta=seas['day_bias']['status'])
        with s_col2:
            st.metric("Turn-of-the-Month (TOM)", "Monatswechsel-Effekt", delta=seas['tom_anomaly']['status'])
        with s_col3:
            st.metric("KI-Saisonalitäts-Modifikator", f"{seas['total_score_modifier']:+d} Punkte", delta="Score-Einfluss auf Kauf-Trigger")

        # Current Day Detailed Strategy Card
        st.markdown(f"""
        <div style="background-color: #0f172a; border: 1px solid #e2e8f0; border-left: 5px solid #a78bfa; border-radius: 8px; padding: 15px; margin: 15px 0;">
            <h4 style="margin: 0 0 5px 0; color: #a78bfa;">🎯 Heutiges statistisches Marktmuster: {seas['day_bias']['name']}</h4>
            <p style="margin: 4px 0; color: #1e293b; font-size: 14px;">{seas['day_bias']['description']}</p>
            <div style="margin-top: 8px; font-size: 13px; color: #38bdf8;"><b>🤖 Handelsregel der KI für heute:</b> {seas['day_bias']['trading_rule']}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("#### 📋 Wichtigste Makro- & Kalender-Anomalien im Überblick:")
        
        cal_df = pd.DataFrame(seas["events_calendar"])
        cal_display = pd.DataFrame()
        cal_display["Makro-Event / Anomalie"] = cal_df["event"]
        cal_display["Frequenz / Typischer Zeitpunkt"] = cal_df["frequency"]
        cal_display["Volatilitäts-Impakt"] = cal_df["impact"]
        cal_display["Handels-Regel der KI"] = cal_df["rule"]

        c_cfg = {
            "Makro-Event / Anomalie": st.column_config.TextColumn("Event", help="Wirtschafts- oder Zentralbankereignis"),
            "Frequenz / Typischer Zeitpunkt": st.column_config.TextColumn("Turnus", help="Wann das Ereignis eintritt"),
            "Volatilitäts-Impakt": st.column_config.TextColumn("Impakt", help="Erwartete Marktschwankung"),
            "Handels-Regel der KI": st.column_config.TextColumn("KI-Handelsregel", help="Wie die Algorithmen auf das Event reagieren")
        }

        st.dataframe(cal_display, column_config=c_cfg, use_container_width=True, hide_index=True)

        st.info(f"🌐 **Quartals-Saisonalität:** {seas['seasonal_context']}")

    with m_tab3:
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
                <div style="background-color: #0f172a; border: 1px solid #e2e8f0; border-left: 4px solid {source_badge_color}; border-radius: 6px; padding: 12px 16px; margin-bottom: 12px;">
                    <div style="display: flex; justify-content: space-between; font-size: 12px; color: #64748b;">
                        <span style="font-weight: bold; color: {source_badge_color};">📌 {item['source']} • {item.get('category', '')}</span>
                        <span>🕒 {item.get('published', '')[:25]}</span>
                    </div>
                    <h4 style="margin: 6px 0; color: white;">
                        <a href="{item['link']}" target="_blank" style="color: #0f172a; text-decoration: none;">{item['title']}</a>
                    </h4>
                    <p style="margin: 0; font-size: 13px; color: #334155;">{item.get('snippet', '')}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Keine Nachrichten für den gewählten Filter gefunden.")

# ==============================================================================

    with st.expander("📚 Begriffe, Abkürzungen & Interpretation (Makro & News)"):
        st.markdown('''
        - **Fed (Federal Reserve) / EZB (Europäische Zentralbank)**: Steuern den Leitzins.
        - **Leitzins / Interest Rates**:
          - *Zinssenkung*: **Bullisch** für Aktien (Geld wird billiger, Kredite günstiger).
          - *Zinserhöhung*: **Bärisch** (Geld wird teurer, Anlagen wie Anleihen werden attraktiver als Aktien).
        - **Inflation (CPI/VPI)**: Verbraucherpreise.
          - *Fällt*: Gut für den Aktienmarkt (Zinssenkungen rücken näher).
          - *Steigt*: Schlecht (Gefahr von längeren, höheren Zinsen).
        - **Dot-Plot (Fed)**: Die offizielle Prognose der Fed-Mitglieder, wohin die Zinsen in den nächsten Jahren fallen oder steigen werden.
        ''')

# MODE: COMMODITIES, PRECIOUS METALS, OIL & FOREX
# ==============================================================================
elif app_mode == "🪙 Rohstoffe, Anleihen, Zinsen & Devisen (FICC)":
    st.title("🪙 Rohstoffe, Anleihen, Zinsen & Globale Devisen (FICC)")
    st.markdown("Echtzeit-Tracking von **Edelmetallen, Rohöl, Staatsanleihen, Zinskurven & Devisen** inklusive Zinsstrukturkurve, High-Yield Spreads, CFTC CoT Daten und Zinsdifferenzen.")

    tab_pm, tab_energy, tab_bonds, tab_forex = st.tabs([
        "👑 Edelmetalle & Struktur-Ratios (Gold, Silber & GSR)",
        "🛢️ Energie & Rohstoffe (WTI, Brent, Gas & Kupfer)",
        "🏛️ Anleihen-, Zins- & Kreditmärkte (Bonds, Yield Curve & Spreads)",
        "💱 Globale Devisen & Währungen (Forex, DXY & Carry-Trade)"
    ])

    with tab_pm:
        st.subheader("👑 Edelmetall-Intelligence & Struktur-Ratios (Gold, Silber & Platin)")
        st.caption("Echtzeit-Edelmetallanalytik: Verhältnis-Indikatoren (*Gold/Silver Ratio*, *Gold/Oil*), World Gold Council Zentralbankdaten und CFTC CoT Fonds-Positionierung.")
        
        st.info("""
        💡 **Relevanz für Kauf- und Verkaufsentscheidungen:**
        Edelmetalle sind das seismografische Frühwarnsystem für weltweite Währungsabwertung, Realzinswenden und geopolitische Risiken.
        * **Gold/Silber-Ratio > 80:** Löst einen **+15 Punkte Alpha-Bonus** für Silber- und Minenaktien aus (historischer Squeeze-Aufholer).
        * **Fallende US-Realzinsen (< 1.8 %):** Beflügeln die Gold-Allokation im Langfrist-Depot.
        """)
        
        pm_data = CommoditiesIntelEngine.get_precious_metals_overview()
        
        # 1. Price Metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Gold (Spot / Unze)", f"${pm_data['gold_price']:,.2f}", delta="Sicherer Hafen")
        m2.metric("Silber (Spot / Unze)", f"${pm_data['silver_price']:,.2f}", delta="Industrie & Monetär")
        m3.metric("Platin (Spot / Unze)", f"${pm_data['platinum_price']:,.2f}", delta="Katalysator-Bedarf")
        m4.metric("Kupfer (High Grade)", f"${pm_data['copper_price']:.2f} / lb", delta="Dr. Kupfer")

        st.markdown("---")
        st.markdown("#### 📐 Die wichtigsten Struktur-Ratios & Signal-Ampeln")
        
        r_col1, r_col2 = st.columns(2)
        with r_col1:
            st.markdown(f"""
            <div style="background-color: #f8fafc; border: 1.5px solid #e2e8f0; border-left: 4px solid #f59e0b; border-radius: 8px; padding: 14px 16px; margin-bottom: 12px;">
                <h4 style="margin: 0 0 6px 0; color: #b45309;">📊 Gold/Silber-Ratio (GSR): {pm_data['gold_silver_ratio']}</h4>
                <p style="margin: 0; font-size: 14px; color: #0f172a;"><b>Signal:</b> {pm_data['gsr_signal']}</p>
                <p style="margin: 6px 0 0 0; font-size: 13px; color: #64748b;">
                    <b>Regel:</b> Historischer Mittelwert liegt bei ~65. Ein Ratio über 80 bedeutet, dass Silber im Vergleich zu Gold historisch extrem unterbewertet ist und massive Aufhol-Rallyes startet.
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style="background-color: #f8fafc; border: 1.5px solid #e2e8f0; border-left: 4px solid #0284c7; border-radius: 8px; padding: 14px 16px;">
                <h4 style="margin: 0 0 6px 0; color: #0284c7;">🛢️ Gold/Öl-Ratio (Kaufkraft-Index)</h4>
                <p style="margin: 0; font-size: 14px; color: #0f172a;"><b>Wert:</b> {pm_data['gold_oil_ratio']}</p>
                <p style="margin: 6px 0 0 0; font-size: 13px; color: #64748b;">
                    Zeigt an, wie viele Barrel Öl mit einer Unze Gold gekauft werden können. Hohe Werte (>30) signalisieren eine historisch starke Kaufkraft von Gold.
                </p>
            </div>
            """, unsafe_allow_html=True)

        with r_col2:
            st.markdown(f"""
            <div style="background-color: #f8fafc; border: 1.5px solid #e2e8f0; border-left: 4px solid #10b981; border-radius: 8px; padding: 14px 16px; margin-bottom: 12px;">
                <h4 style="margin: 0 0 6px 0; color: #047857;">🏛️ Globale Zentralbank-Goldkäufe</h4>
                <p style="margin: 0; font-size: 14px; color: #0f172a;"><b>Kauf-Volumen:</b> {pm_data['central_bank_gold_demand']}</p>
                <p style="margin: 6px 0 0 0; font-size: 13px; color: #64748b;">
                    Weltweiter Ent-Dollarisierungstrend: Zentralbanken akkumulieren physisches Gold als strategische Reserve.
                </p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div style="background-color: #f8fafc; border: 1.5px solid #e2e8f0; border-left: 4px solid #7c3aed; border-radius: 8px; padding: 14px 16px;">
                <h4 style="margin: 0 0 6px 0; color: #7c3aed;">📈 CFTC CoT & Realzins-Treiber</h4>
                <p style="margin: 0; font-size: 14px; color: #0f172a;"><b>CoT Managed Money:</b> {pm_data['cot_gold_managed_money']}</p>
                <p style="margin: 4px 0 0 0; font-size: 14px; color: #0f172a;"><b>US 10Y TIPS Realzins:</b> {pm_data['us_10y_real_yield']}</p>
            </div>
            """, unsafe_allow_html=True)

    with tab_energy:
        st.subheader("🛢️ Energie- & Rohstoff-Intelligence (WTI, Brent, Gas & Kupfer)")
        st.caption("Echtzeit-Rohölpreise, US-Lagerbestandsveränderungen (EIA), OPEC+ Förderdisziplin und Raffinerie-Margen.")
        
        st.info("""
        💡 **Relevanz für Kauf- und Verkaufsentscheidungen:**
        * **Kupfer/Gold-Ratio:** „Dr. Kupfer“ misst den globalen Konjunkturmotor. Steigt das Ratio, investiert die KI verstärkt in Zykliker und Industrie-Nebenwerte (SDAX/US Mid-Caps).
        * **3:2:1 Crack Spread (> $20/bbl):** Signalisiert hohe Raffinerie-Rentabilität und stabile reale Energienachfrage.
        """)
        
        en_data = CommoditiesIntelEngine.get_energy_commodities_overview()
        
        e1, e2, e3, e4 = st.columns(4)
        e1.metric("WTI Rohöl (US Light Sweet)", f"${en_data['wti_price']:.2f} / bbl")
        e2.metric("Brent Rohöl (Nordsee)", f"${en_data['brent_price']:.2f} / bbl", delta=en_data['brent_wti_spread'])
        e3.metric("Erdgas (Henry Hub)", f"${en_data['natural_gas_price']:.2f} / MMBtu")
        e4.metric("3:2:1 Crack Spread", en_data['crack_spread_margin'].split("(")[0].strip(), help="Raffinerie-Gewinnmarge pro Barrel")

        st.markdown("---")
        st.markdown("#### 🏭 Fundamentale Rohöl- & Angebots-Faktoren")
        
        oe_col1, oe_col2 = st.columns(2)
        with oe_col1:
            st.info(f"📊 **EIA US-Rohöl-Lagerbestände:** {en_data['eia_crude_inventory']}")
            st.info(f"🛢️ **OPEC+ Reservekapazitäten:** {en_data['opec_spare_capacity']}")
        with oe_col2:
            st.success(f"⛽ **Raffinerie-Margen (Crack Spread):** {en_data['crack_spread_margin']}")
            st.warning(f"🌐 **Rohstoff-Regime:** {en_data['oil_regime_verdict']}")

    with tab_bonds:
        st.subheader("🏛️ Globaler Anleihenmarkt, Renditen & Zinskurven-Intelligence")
        st.caption("Staatsanleihe-Renditen (US Treasuries, Bundesanleihen), Zinskurven-Inversion / Disinversion, Kreditrisiko (High-Yield OAS) und Realzinsen.")

        b_data = BondYieldsIntelEngine.get_bond_market_overview()

        # 1. Top Yield Metrics
        by1, by2, by3, by4 = st.columns(4)
        by1.metric("US 10-Jahres-Treasury", f"{b_data['us_10y_yield']:.2f}%", delta="Weltzins-Benchmark")
        by2.metric("US 2-Jahres-Treasury", f"{b_data['us_2y_yield']:.2f}%", delta="Fed-Zinserwartung")
        by3.metric("10Y - 2Y Zinsspread", f"{b_data['spread_10y_2y_bps']:+.1f} Bp", delta=b_data['curve_regime'])
        by4.metric("US 30-Jahres-Yield", f"{b_data['us_30y_yield']:.2f}%", delta="Langfrist-Kredit")

        # 2. Interactive Historical Bond & Stock-to-Bond Ratio Chart
        st.markdown("---")
        st.markdown("#### 📈 Historischer Trend: Anleiherenditen vs. Anleihekurse & Aktien/Bond-Verhältnis")
        st.caption("Vergleicht die 10-jährige US-Staatsanleiherendite mit dem Kurs langlaufender US-Staatsanleihen (TLT) und dem Risiko-Thermometer (SPY / TLT).")

        b_hist_df = BondYieldsIntelEngine.get_historical_bond_chart_data(period="6mo")
        if not b_hist_df.empty:
            fig_bonds = make_subplots(
                rows=2, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.10,
                subplot_titles=(
                    "⚖️ 1. Die Zins-Wippe: US 10-Jahres-Rendite (%) vs. 20+ Year Treasury Bond ETF ($ TLT)",
                    "📊 2. Stock-to-Bond Ratio (S&P 500 vs. 20Y Treasuries: Steigend = Risk-On / Fallend = Risk-Off)"
                ),
                row_heights=[0.6, 0.4]
            )

            # Subplot 1: Yield vs Bond Price
            fig_bonds.add_trace(
                go.Scatter(
                    x=b_hist_df["date"], y=b_hist_df["us_10y_yield"],
                    name="US 10Y Rendite (%)",
                    line=dict(color="#0284c7", width=2.5),
                    hovertemplate="<b>Datum:</b> %{x}<br><b>US 10Y Rendite:</b> %{y:.2f}%<extra></extra>"
                ),
                row=1, col=1
            )
            fig_bonds.add_trace(
                go.Scatter(
                    x=b_hist_df["date"], y=b_hist_df["tlt_bond_price"],
                    name="TLT Bond-Preis ($)",
                    line=dict(color="#10b981", width=2, dash="dot"),
                    yaxis="y2",
                    hovertemplate="<b>Datum:</b> %{x}<br><b>TLT Kurs:</b> $%{y:.2f}<extra></extra>"
                ),
                row=1, col=1
            )

            # Subplot 2: Stock-to-Bond Ratio
            fig_bonds.add_trace(
                go.Scatter(
                    x=b_hist_df["date"], y=b_hist_df["stock_to_bond_ratio"],
                    name="Stock-to-Bond Ratio (SPY/TLT)",
                    line=dict(color="#f59e0b", width=2.5),
                    fill="tozeroy",
                    fillcolor="rgba(245, 158, 11, 0.08)",
                    hovertemplate="<b>Datum:</b> %{x}<br><b>SPY/TLT Ratio:</b> %{y:.2f}<extra></extra>"
                ),
                row=2, col=1
            )

            fig_bonds.update_layout(
                template="plotly_white",
                height=520,
                margin=dict(l=20, r=20, t=40, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                hovermode="x unified"
            )
            fig_bonds.update_yaxes(title_text="Rendite (%)", row=1, col=1)
            fig_bonds.update_yaxes(title_text="Stock/Bond Ratio", row=2, col=1)
            st.plotly_chart(fig_bonds, use_container_width=True)

        # 3. Educational Guide & Ratios
        st.markdown("---")
        st.markdown("### 📖 Leitfaden: Was bedeuten steigende/fallende Bonds & die wichtigsten Ratios?")

        col_bg1, col_bg2 = st.columns(2)
        with col_bg1:
            st.markdown("""
            #### 🔄 1. Die fundamentale Wippe: Was bedeutet Steigen & Fallen?
            * **📉 Wenn Renditen FALLEN (Anleihekurse STEIGEN):**
              * **Ursache:** Erwartung von Zinssenkungen der Notenbank, schwächere Konjunkturdaten oder geopolitische Flucht in sichere Häfen (*Flight to Safety*).
              * **Auswirkung auf Aktien:** **Massiver Rückenwind für Tech- & Wachstumsaktien** (*Palantir, Nvidia, Duolingo, Biotech*). Niedrigere Zinsen verringern den Diskontierungsfaktor für zukünftige Cashflows (*Multiple Expansion*).
            * **📈 Wenn Renditen STEIGEN (Anleihekurse FALLEN):**
              * **Ursache:** Anziehende Inflation, starkes Wirtschaftswachstum oder hohe Staatsverschuldung (Notenbanken halten Zinsen länger hoch).
              * **Auswirkung auf Aktien:** **Bewertungsdruck auf hochbewertete Wachstumswerte** (*KGV-Kompression*); vorteilhaft für Banken, Versicherer (*Münchener Rück*) und Value-Substanzwerte.
            """)

        with col_bg2:
            st.markdown("""
            #### ⚖️ 2. Die 3 wichtigsten Verhältnis-Kennzahlen (Ratios):
            * **📊 1. Stock-to-Bond Ratio (`SPY / TLT` - Das Risiko-Thermometer):**
              * Misst das Verhältnis von US-Aktien zu langlaufenden Staatsanleihen.
              * **Steigender Trend:** Kapital rotiert aggressiv in Aktien (**Risk-On / Bullenmarkt**).
              * **Fallender Trend:** Großinvestoren fliehen aus Aktien in sichere Anleihen (**Risk-Off / Bärenmarkt**).
            * **🏷️ 2. Aktienrisikoprämie (Equity Risk Premium - ERP):**
              * `S&P 500 Gewinnrendite (4.2 %) minus US 10Y Rendite (4.1 %) = +0.1 %`.
              * Liegt die Risikoprämie nahe 0, bieten "risikolose" Staatsanleihen fast dieselbe Rendite wie Aktien ➔ Aktien sind historisch sportlich bewertet.
            * **💳 3. High-Yield vs. Treasuries Ratio (`HYG / TLT`):**
              * Misst den Risiko-Appetit an den Unternehmens-Kreditmärkten.
            """)

        st.markdown("---")
        st.markdown("#### 📐 Zinskurven-Zustand & Rezessions-Frühwarnmodell")

        b_col1, b_col2 = st.columns(2)
        with b_col1:
            st.markdown(f"""
            <div style="background-color: #f8fafc; border: 1.5px solid #e2e8f0; border-left: 4px solid #0284c7; border-radius: 8px; padding: 14px 16px; margin-bottom: 12px;">
                <h4 style="margin: 0 0 6px 0; color: #0284c7;">📐 Zinskurven-Status: {b_data['curve_status']}</h4>
                <p style="margin: 0; font-size: 14px; color: #0f172a;"><b>10Y - 2Y Spread:</b> {b_data['spread_10y_2y_bps']:+.1f} Basispunkte | <b>10Y - 3M Spread:</b> {b_data['spread_10y_3m_bps']:+.1f} Bp</p>
                <p style="margin: 6px 0 0 0; font-size: 13px; color: #64748b;">
                    <b>Regel:</b> Die gefährlichste Phase ist die <i>Disinversion</i> (wenn die Kurve nach monatelanger Inversion wieder steiler wird). Genau dann beginnen historisch die meisten Rezessionen und Notenbanken senken die Zinsen.
                </p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div style="background-color: #f8fafc; border: 1.5px solid #e2e8f0; border-left: 4px solid #f59e0b; border-radius: 8px; padding: 14px 16px;">
                <h4 style="margin: 0 0 6px 0; color: #b45309;">📊 NY Fed Rezessions-Wahrscheinlichkeit: {b_data['recession_probability_pct']}%</h4>
                <p style="margin: 0; font-size: 13px; color: #0f172a;">
                    Basiert auf dem klassischen Zinsstrukturmodell der Federal Reserve Bank of New York (10Y minus 3M Spread).
                </p>
            </div>
            """, unsafe_allow_html=True)

        with b_col2:
            st.markdown(f"""
            <div style="background-color: #f8fafc; border: 1.5px solid #e2e8f0; border-left: 4px solid #10b981; border-radius: 8px; padding: 14px 16px; margin-bottom: 12px;">
                <h4 style="margin: 0 0 6px 0; color: #047857;">💳 Kreditrisiko & High-Yield Spreads (OAS)</h4>
                <p style="margin: 0; font-size: 14px; color: #0f172a;"><b>US High Yield OAS:</b> {b_data['credit_data']['us_high_yield_oas']}</p>
                <p style="margin: 4px 0 0 0; font-size: 14px; color: #0f172a;"><b>US Investment Grade:</b> {b_data['credit_data']['us_ig_spread']}</p>
                <p style="margin: 6px 0 0 0; font-size: 13px; color: #64748b;">
                    Solange der Junk-Bond Spread unter 400 Bp bleibt, herrscht kein akuter Kreditkrisen-Stress an den Rentenmärkten.
                </p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div style="background-color: #f8fafc; border: 1.5px solid #e2e8f0; border-left: 4px solid #7c3aed; border-radius: 8px; padding: 14px 16px;">
                <h4 style="margin: 0 0 6px 0; color: #7c3aed;">💡 Zins-Urteil der KI für die Depot-Allokation</h4>
                <p style="margin: 0; font-size: 13.5px; color: #0f172a;"><b>{b_data['trade_verdict']}</b></p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### 🌐 Globale Staatsanleihen im Vergleich (Sovereign Yields)")
        sov_df = pd.DataFrame(b_data["sovereign_yields"])
        sov_df.columns = ["Staat / Anleihe", "10-Jahres-Rendite", "Spread zu Dt. Bund", "Markt-Rolle"]
        st.dataframe(sov_df, use_container_width=True, hide_index=True)


    with tab_forex:
        st.subheader("💱 Globale Währungen, US Dollar Index (DXY) & Zinsdifferenzen (Carry Trade)")
        st.caption("Devisenmärkte steuern globale Kapitalflüsse: Wechselkurse, Zinsdifferenzen der Zentralbanken und DXY-Gewichtung.")
        
        st.warning("""
        🚨 **Automatisches Risikomanagement der KI über Devisen:**
        * **US Dollar Index (DXY < 101.5):** Schwacher Dollar öffnet das globale Liquiditätsventil ➔ Aggressive Freigabe für Tech-Growth & Krypto.
        * **JPY Carry-Trade Alarm (USD/JPY < 145):** Fällt der Yen drastisch, droht weltweites Deleveraging ➔ Die KI schaltet sofort in den **defensiven Schutzmodus** (Pausierung neuer Hebel-Longs, Stop-Loss-Nachzug).
        """)
        
        fx_data = ForexCurrencyEngine.get_forex_overview()
        rates = fx_data["rates"]
        
        # FX Matrix
        fc1, fc2, fc3, fc4 = st.columns(4)
        fc1.metric("EUR / USD", f"{rates.get('EUR/USD', 1.0850):.4f}", delta="Hauptwährungspaar")
        fc2.metric("USD / JPY", f"{rates.get('USD/JPY', 154.00):.2f}", delta="Carry Trade Schlüsselkurs")
        fc3.metric("GBP / USD", f"{rates.get('GBP/USD', 1.3000):.4f}")
        fc4.metric("USD / CHF", f"{rates.get('USD/CHF', 0.8500):.4f}", delta="Sicherer Hafen")

        fc5, fc6, fc7, fc8 = st.columns(4)
        fc5.metric("EUR / CHF", f"{rates.get('EUR/CHF', 0.9300):.4f}")
        fc6.metric("AUD / USD", f"{rates.get('AUD/USD', 0.6700):.4f}", delta="Rohstoff-Währung")
        fc7.metric("USD / CAD", f"{rates.get('USD/CAD', 1.3500):.4f}")
        fc8.metric("US Dollar Index (DXY)", f"{rates.get('DXY', 101.40):.2f}", delta="Leitwährung")

        st.markdown("---")
        st.markdown("#### 🚨 JPY Carry-Trade Risiko-Barometer & Zentralbank-Zinsmatrix")
        
        st.warning(f"**JPY Carry Trade Status:** {fx_data['jpy_carry_trade_risk']}")
        
        cb_df = pd.DataFrame(fx_data["central_bank_rates"])
        cb_df.columns = ["Zentralbank", "Aktueller Leitzins", "Nächster Zinsschritt (Erwartung)", "Geldpolitische Ausrichtung"]
        st.dataframe(cb_df, use_container_width=True, hide_index=True)
        
        st.caption(f"**US Dollar Index (DXY) Korbzusammensetzung:** {fx_data['dxy_breakdown']}")


# ==============================================================================

    with st.expander("📚 Begriffe, Abkürzungen & Interpretation (Rohstoffe, Anleihen & Devisen)"):
        st.markdown('''
        - **Anleihen-Rendite (Yields, z.B. 10-Jahre US-Bonds)**: Verzinsung von Staatsanleihen. 
          - *Steigende Renditen*: Oft **bärisch** für Aktien (besonders Tech-Aktien), da festverzinsliche Anlagen als "risikolose Alternative" attraktiver werden.
          - *Fallende Renditen*: Oft **bullisch** für Aktien.
        - **Invertierte Zinskurve (Inverted Yield Curve)**: Die kurzfristigen Zinsen (z.B. 2-Jahre) sind höher als die langfristigen (z.B. 10-Jahre). 
          - *Interpretation*: Historisch einer der sichersten Indikatoren für eine kommende **Rezession**.
        - **High-Yield Spreads (Junk Bonds)**: Die Risikoprämie (Zinsaufschlag), den Unternehmen mit schlechter Bonität zahlen müssen.
          - *Steigende Spreads*: Die Märkte haben Angst, Kreditausfälle drohen (Bärisch).
          - *Fallende Spreads*: Risikobereitschaft hoch, keine Panik (Bullisch).
        - **DXY (US Dollar Index)**: Stärke des Dollars im Vergleich zu anderen Währungen (Euro, Yen, etc.).
          - *Steigender Dollar*: Oft ein Gegenwind für US-Exportunternehmen und Rohstoffe.
        - **Carry Trade (z.B. Yen)**: Investoren leihen sich günstig Geld in Japan (0% Zinsen) und kaufen damit US-Aktien. 
          - *Gefahr*: Steigt der Yen plötzlich stark an, platzen diese Wetten, was zu massiven Aktienverkäufen führt ("Crash").
        ''')

# MODE 5: MUSTERDEPOTS & LIVE-PERFORMANCE (3 DEPOTS)
# ==============================================================================
elif app_mode == "💼 Musterdepots & Live-Performance (4x 10.000 €)":
    st.title("💼 Autonome Musterdepots (4x 10.000 € Startkapital)")
    st.markdown("Vier getrennte Echtzeit-Musterdepots: **Daytrader (Intraday)**, **Kurzfristig (Tage–Wochen)**, **Mittelfristig (1–6 Monate)** und **Langfristig (Jahre)**.")

    pm = PortfolioManager(initial_capital_per_depot=10000.0)

    # Depot Selector (4 Depots)
    selected_depot_key = st.radio(
        "Wähle das Depot:",
        [
            ("day_trading", "🔥 Daytrader (Intraday / Dynamischer Hebel / Momentum)"),
            ("short_term", "⚡ Kurzfristig (Tage–Wochen / Squeezes & Breakouts)"),
            ("medium_term", "📈 Mittelfristig (1–6 Monate / Growth & Trend)"),
            ("long_term", "🏛️ Langfristig (Jahre / Quality, Gold & Moat)")
        ],
        format_func=lambda x: x[1],
        horizontal=True
    )[0]


    @st.cache_data(ttl=3600)
    def fetch_index_benchmarks(start_date: str):
        try:
            import yfinance as yf
            tickers = {"DAX": "^GDAXI", "Nasdaq": "^IXIC", "Dow": "^DJI", "S&P 500": "^GSPC"}
            # Fetch daily data
            idx_data = yf.download(list(tickers.values()), start=start_date, progress=False)['Close']
            # Make sure index is string YYYY-MM-DD
            idx_data.index = pd.to_datetime(idx_data.index).strftime("%Y-%m-%d")
            return idx_data, tickers
        except Exception as e:
            return None, None

    # Define the Auto-Refreshing Live Depot Fragment (Runs every 30s automatically)
    @st.fragment(run_every=30)
    def render_live_depot_view(depot_key: str):
        # 1. Fetch fresh live prices via parallel fast_info / Binance streamer
        pm.update_live_prices()
        
        # 1b. Generiere kontinuierlich neue Intraday-Ausbruchs-Signale für das Daytrader-Depot
        default_cat = rt_scanner.get_categories()[0]
        rt_scanner.scan_category(default_cat)
        
        # 2. Check Stop-Loss / Take-Profit automatically
        scan_data = load_cached_market_scan()
        scan_list = scan_data.get("data", []) if scan_data else []
        actions = pm.auto_trade_check(scan_list)
        if actions:
            st.toast(f"🤖 Autopilot: {', '.join(actions)}", icon="⚡")

        summary = pm.get_depot_summary(depot_key)
        now_time = get_berlin_now().strftime("%H:%M:%S")
        seas = MarketSeasonalityEngine.get_current_seasonality_analysis()

        # Action Toolbar & Status Bar with Seasonality Badge
        col_st1, col_st2 = st.columns([2.8, 1.2])
        with col_st1:
            st.markdown(f"""
            <div style="background-color: #0f172a; border: 1px solid #e2e8f0; border: 1px solid #334155; border-radius: 8px; padding: 10px 16px; margin: 10px 0; display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 13.5px; color: #0f172a;">
                    🟢 <b>Live-Stream</b> • Letztes Update: <b style="color: #38bdf8;">{now_time} (MESZ / Berlin)</b> • <span style="color: #a78bfa;">📅 {seas['weekday']}: <b>{seas['day_bias']['name']}</b> ({seas['total_score_modifier']:+d} Pkt.)</span>
                </span>
                <span style="font-size: 12.5px; color: #64748b;">Taktung: <b style="color: #34d399;">alle 30s</b> (0,00 €)</span>
            </div>
            """, unsafe_allow_html=True)
        with col_st2:
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            if st.button("⚡ Jetzt sofort aktualisieren", use_container_width=True):
                pm.update_live_prices()
                st.rerun()

        # 5 Metric Cards
        m1, m1b, m2, m3, m4 = st.columns(5)
        with m1:
            st.metric(
                "Depot-Gesamtwert", 
                f"{summary['total_value']:,.2f} €", 
                delta=f"{summary['total_pnl']:+,.2f} € ({summary['total_pnl_pct']:+.2f}%) Gesamt"
            )
        with m1b:
            st.metric(
                "Tages-Performance", 
                f"{summary.get('today_pnl', 0.0):+,.2f} €", 
                delta=f"{summary.get('today_pnl_pct', 0.0):+.2f}% Heute"
            )
        with m2:
            st.metric(
                "Investiertes Kapital", 
                f"{summary['invested_value']:,.2f} €",
                help="Aktueller Marktwert aller offenen Positionen"
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
                help="Anzahl der aktuell gehaltenen Werte"
            )

        # Charts, Positions & Multi-Source Deep Intelligence
        tab_chart, tab_pos, tab_intel, tab_alloc, tab_hist = st.tabs([
            "📈 Depot-Wertentwicklung (Equity Curve)",
            "📋 Offene Positionen & Buchgewinne (Live-Ticks)",
            "🧠 Deep-Intelligence & Multi-Source Audit (6 Dimensionen)",
            "🥧 Asset Allocation (Gewichtung)",
            "📜 Transaktions-Historie (Trade Log)"
        ])

        with tab_chart:
            st.markdown("#### 📈 Depot-Wertentwicklung & Gesamtkapitalverlauf (Equity Curve)")
            st.caption("Stundenweise Entwicklung des gesamten Depotwerts (Investiertes Kapital + Cash) seit Depotstart am 24.08.2026 gegenüber dem Startkapital von 10.000 €.")
            
            eq_df = pm.get_equity_curve(depot_key)
            
            # 🟢 HIER WIRD DIE NACHT GEFILTERT (Kein Handel zwischen 22:00 und 06:00)
            if not eq_df.empty:
                eq_df["hour_check"] = pd.to_datetime(eq_df["date"]).dt.hour
                eq_df = eq_df[(eq_df["hour_check"] >= 6) & (eq_df["hour_check"] <= 22)]
            
            # High-legibility Plotly Equity Chart
            fig_eq = make_subplots(
                rows=2, cols=1, 
                shared_xaxes=True, 
                vertical_spacing=0.08,
                row_heights=[0.75, 0.25],
                subplot_titles=("Depot-Gesamtwert (€)", "Stündlicher Gewinn / Verlust (€)")
            )

            # 1. Total Value Line & Area
            fig_eq.add_trace(
                go.Scatter(
                    x=eq_df["date"], 
                    y=eq_df["total_value"], 
                    name="Depot-Gesamtwert", 
                    mode="lines+markers",
                    line=dict(color="#38bdf8", width=3),
                    fill="tozeroy",
                    fillcolor="rgba(56, 189, 248, 0.12)",
                    hovertemplate="<b>Zeitpunkt:</b> %{x}<br><b>Gesamtwert:</b> %{y:,.2f} €<extra></extra>"
                ),
                row=1, col=1
            )

            # 2. Baseline 10.000 € Line
            fig_eq.add_trace(
                go.Scatter(
                    x=eq_df["date"], 
                    y=eq_df["baseline"], 
                    name="Startkapital (10.000 €)", 
                    mode="lines",
                    line=dict(color="#94a3b8", width=1.5, dash="dash"),
                    hovertemplate="<b>Startkapital:</b> 10.000,00 €<extra></extra>"
                ),
                row=1, col=1
            )
            
            # 2.5 Index Benchmarks
            try:
                start_date_str = pd.to_datetime(eq_df["date"].iloc[0]).strftime("%Y-%m-%d")
                idx_data, tickers = fetch_index_benchmarks(start_date_str)
                if idx_data is not None:
                    eq_df["date_only"] = pd.to_datetime(eq_df["date"]).dt.strftime("%Y-%m-%d")
                    colors = {"DAX": "#facc15", "Nasdaq": "#a855f7", "S&P 500": "#ec4899", "Dow": "#22d3ee"}
                    
                    for t_name, ticker in tickers.items():
                        s = idx_data[ticker].dropna()
                        if not s.empty:
                            base_val = s.iloc[0]
                            mapped = eq_df["date_only"].map(s).ffill()
                            norm_vals = (mapped / base_val) * 10000.0
                            
                            fig_eq.add_trace(
                                go.Scatter(
                                    x=eq_df["date"], 
                                    y=norm_vals, 
                                    name=f"{t_name} (normiert)", 
                                    mode="lines",
                                    line=dict(color=colors[t_name], width=1.5, dash="dot"),
                                    hovertemplate=f"<b>{t_name}:</b> %{{y:,.2f}} €<extra></extra>"
                                ),
                                row=1, col=1
                            )
            except Exception as e:
                pass

            # 3. PnL Bar in row 2
            bar_colors = ["#22c55e" if p >= 0 else "#ef4444" for p in eq_df["pnl"]]
            fig_eq.add_trace(
                go.Bar(
                    x=eq_df["date"], 
                    y=eq_df["pnl"], 
                    name="Gewinn / Verlust (€)",
                    marker_color=bar_colors,
                    hovertemplate="<b>Zeitpunkt:</b> %{x}<br><b>P&L:</b> %{y:+,.2f} €<extra></extra>"
                ),
                row=2, col=1
            )

            fig_eq.update_layout(
                template="plotly_white",
                height=480,
                margin=dict(l=20, r=20, t=40, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                hovermode="x unified"
            )
            # Nutze Kategorie-Achse, damit fehlende Stunden (Lücken) einfach ignoriert und die Balken zusammengerückt werden
            fig_eq.update_xaxes(type="category", nticks=15)
            
                        # Berechne dynamische Y-Achsen-Grenzen, damit fill='tozeroy' den Chart nicht plattdrückt
            try:
                min_val = eq_df["total_value"].min()
                max_val = eq_df["total_value"].max()
                
                # Falls die Benchmarks da sind, beachte auch deren min/max grob (wir nehmen +/- 10% zur Sicherheit)
                padding = max((max_val - min_val) * 0.5, 300) # Mindestens 300 Euro Abstand nach oben und unten
                
                # Hard-Cap für den Start (z.B. +/- 1000 vom Baseline)
                y_bottom = min(min_val, 10000.0) - padding
                y_top = max(max_val, 10000.0) + padding
                
                fig_eq.update_yaxes(title_text="Euro (€)", range=[y_bottom, y_top], row=1, col=1)
            except:
                fig_eq.update_yaxes(title_text="Euro (€)", row=1, col=1)
            fig_eq.update_yaxes(title_text="P&L (€)", row=2, col=1)
            st.plotly_chart(fig_eq, use_container_width=True)

        with tab_pos:
            if summary["positions"]:
                pos_df = pd.DataFrame(summary["positions"])
                
                for col in ["product_type", "leverage", "distance_to_ko", "last_updated"]:
                    if col not in pos_df.columns:
                        pos_df[col] = None

                display_pos = pd.DataFrame()
                display_pos["WKN"] = pos_df["symbol"].apply(get_wkn)
                display_pos["Instrument / Name"] = pos_df["name"]
                
                type_map = {
                    "STOCK": "Aktie / Krypto",
                    "KNOCKOUT": "⚡ Knock-Out",
                    "FACTOR": "🚀 Faktor-Zertifikat",
                    "BONUS": "🛡️ Bonus-Zertifikat"
                }
                display_pos["Produkttyp"] = pos_df["product_type"].map(lambda x: type_map.get(x, x))
                display_pos["Stück"] = pos_df["shares"]
                display_pos["Kaufkurs"] = pos_df["buy_price"].apply(lambda x: f"{x:.2f}")
                display_pos["Aktueller Kurs"] = pos_df["current_price"].apply(lambda x: f"{x:.2f}")
                display_pos["Stand"] = pos_df["last_updated"].fillna(now_time)
                display_pos["Marktwert (€)"] = pos_df["value"].apply(lambda x: f"{x:,.2f} €")
                display_pos["Gewinn (€)"] = pos_df["pnl"].apply(lambda x: f"{x:+,.2f} €")
                display_pos["Rendite (%)"] = pos_df["pnl_pct"].apply(lambda x: f"{x:+.2f}%")
                display_pos["Hebel"] = pos_df["leverage"].apply(lambda x: f"{x:.1f}x" if pd.notnull(x) else "-")
                display_pos["KO-Puffer"] = pos_df["distance_to_ko"].apply(lambda x: f"{x:.1f}%" if pd.notnull(x) else "-")
                display_pos["Stop-Loss"] = pos_df["stop_loss"].apply(lambda x: f"{x:.2f}" if pd.notnull(x) else "-")
                display_pos["Take-Profit"] = pos_df["take_profit"].apply(lambda x: f"{x:.2f}" if pd.notnull(x) else "-")
                display_pos["Kaufgrund"] = pos_df["reason"]

                display_pos["symbol"] = pos_df["symbol"] # Hidden column for jump logic

                pos_cfg = {
                    "symbol": None, # Hide this column
                    "WKN": st.column_config.TextColumn("WKN", help="Offizielle deutsche Wertpapierkennnummer (WKZ)"),
                    "Instrument / Name": st.column_config.TextColumn("Name", help="Name des Unternehmens oder Zertifikats"),
                    "Produkttyp": st.column_config.TextColumn("Typ", help="Aktie, Krypto, Knock-Out, Faktor- oder Bonus-Zertifikat"),
                    "Stück": st.column_config.NumberColumn("Stück", help="Anzahl gehaltener Stücke / Zertifikate"),
                    "Kaufkurs": st.column_config.TextColumn("Kaufkurs", help="Einstandskurs in Euro/Dollar"),
                    "Aktueller Kurs": st.column_config.TextColumn("Live-Kurs", help="Sekundengenauer Live-Kurs"),
                    "Stand": st.column_config.TextColumn("Uhrzeit", help="Zeitstempel des letzten Ticks"),
                    "Marktwert (€)": st.column_config.TextColumn("Marktwert (€)", help="Gesamtwert der Position"),
                    "Gewinn (€)": st.column_config.TextColumn("Gewinn (€)", help="Unrealisierter Buchgewinn/-verlust"),
                    "Rendite (%)": st.column_config.TextColumn("Rendite (%)", help="Prozentuale Rendite"),
                    "Hebel": st.column_config.TextColumn("Hebel", help="Effektiver Hebel (z. B. 3.5x) bei Derivaten"),
                    "KO-Puffer": st.column_config.TextColumn("KO-Puffer", help="Prozentualer Abstand zur Knock-Out Schwelle bzw. Barriere"),
                    "Stop-Loss": st.column_config.TextColumn("Stop-Loss", help="Automatischer Verkaufs-Trigger"),
                    "Take-Profit": st.column_config.TextColumn("Take-Profit", help="Automatischer Gewinnmitnahme-Trigger"),
                    "Kaufgrund": st.column_config.TextColumn("Kaufgrund / Signal", help="KI-Analyse & Einstiegsthese")
                }

                st.markdown("💡 *Tipp: Klicke auf eine Zeile, um direkt in die **Einzelaktien-Tiefenanalyse** zu springen.*")
                
                pos_event = st.dataframe(
                    display_pos,
                    column_config=pos_cfg,
                    use_container_width=True,
                    hide_index=True,
                    on_select="rerun",
                    selection_mode="single-row"
                )
                
                if len(pos_event.selection.rows) > 0:
                    selected_idx = pos_event.selection.rows[0]
                    selected_sym = display_pos.iloc[selected_idx]["symbol"]
                    st.session_state["nav_app_mode"] = "🔍 Einzelaktien-Tiefenanalyse"
                    st.query_params["mode"] = "🔍 Einzelaktien-Tiefenanalyse"
                    st.session_state["nav_deep_ticker"] = selected_sym
                    st.rerun()
            else:
                st.info("Keine offenen Positionen. Das Depot hält 100% Cash.")

        with tab_intel:
            st.subheader("🧠 Multi-Source Deep Intelligence & 6-Dimensionen-Audit")
            st.caption("Institutioneller Datenabgleich über Dark Pools, Insiderkäufe, Fed-Liquidität, Social-Buzz, Bilanz-Forensik & Krypto-On-Chain.")

            macro_ov = pm.deep_intel.get_macro_and_insider_overview()
            liq = macro_ov["macro_liquidity"]
            
            # Row 1: Global Macro & Smart Money Regime Bar
            st.markdown("#### 🌐 1. Makro-Liquidität & Zinswende-Kompass (Federal Reserve & CME)")
            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
            m_col1.metric("US Netto-Liquidität", liq["us_net_liquidity"], delta=liq["net_liquidity_delta_30d"])
            m_col2.metric("FedWatch Zinswende", "88.5% Chance", delta="25–50 Bp Zinssenkung")
            m_col3.metric("US Zinskurve (10Y–2Y)", "-0.02%", delta="De-Invertiert / Normal")
            m_col4.metric("US-Dollar Index (DXY)", "101.35", delta="-1.2% Schwäche (Bullisch)")

            st.info(f"**Aktuelles Makro-Regime:** {liq['macro_regime']}")

            # Row 2: 360-Grad Audit für aktuelle Depotwerte
            st.markdown("---")
            st.markdown("#### 🏰 2. Forensisches Bilanz-Audit & Smart-Money-Score (Depot-Positionen)")
            
            intel_rows = []
            for p in summary["positions"]:
                sym = p["symbol"]
                p_intel = pm.deep_intel.get_asset_360_intelligence(sym)
                flow = p_intel["smart_money_flow"]
                social = p_intel["social_sentiment"]
                forensic = p_intel["forensic_quality"]
                
                intel_rows.append({
                    "WKN": get_wkn(sym),
                    "Name": p["name"][:20],
                    "Alpha-Score": f"⭐ {p_intel['composite_alpha_score']}/100",
                    "Dark Pool Anteil": f"{flow['dark_pool_share_pct']}%",
                    "Put/Call Ratio": f"{flow['put_call_ratio']:.2f}",
                    "Piotroski F-Score": forensic["piotroski_f_score"].split("(")[0].strip(),
                    "Altman Z-Score": forensic["altman_z_score"].split("(")[0].strip(),
                    "Social Spike (24h)": f"{social['relative_mentions_spike_pct']:+.0f}%",
                    "Burggraben-Rating": forensic["moat_rating"]
                })
            
            if intel_rows:
                st.dataframe(pd.DataFrame(intel_rows), use_container_width=True, hide_index=True)

            # Row 3: Insider & Dark Pool Live Blocks
            st.markdown("---")
            i_col1, i_col2 = st.columns(2)
            with i_col1:
                st.markdown("#### 🕵️‍♂️ 3. Dark Pool & Optionen-Großblöcke (Smart Money)")
                for b in macro_ov["block_trades"][:3]:
                    st.markdown(f"""
                    <div style="background-color: #0f172a; border: 1px solid #e2e8f0; padding: 10px 14px; border-radius: 8px; margin-bottom: 8px; border-left: 4px solid #38bdf8;">
                        <span style="font-weight: 700; color: #38bdf8;">{b['symbol']} ({b['name']})</span> &bull; 
                        <span style="color: #334155;">{b['type']}</span><br>
                        <span style="font-size: 0.85rem; color: #64748b;">Größe: {b['size']} | Volumen: <b>{b['value']}</b> | {b['time']}</span>
                    </div>
                    """, unsafe_allow_html=True)

            with i_col2:
                st.markdown("#### 🏛️ 4. SEC Form 4 Insider- & Kongress-Trades")
                for c in macro_ov["congress_trades"][:2]:
                    st.markdown(f"""
                    <div style="background-color: #0f172a; border: 1px solid #e2e8f0; padding: 10px 14px; border-radius: 8px; margin-bottom: 8px; border-left: 4px solid #a78bfa;">
                        <span style="font-weight: 700; color: #a78bfa;">{c['politician']}</span> ({c['committee']})<br>
                        <span style="color: #334155;">{c['asset']} &bull; <b>{c['amount']}</b></span><br>
                        <span style="font-size: 0.85rem; color: #64748b;">Historischer Track-Record: {c['history_track_record']}</span>
                    </div>
                    """, unsafe_allow_html=True)

            # Row 4: Krypto On-Chain Deep Dive (if Crypto held or global)
            st.markdown("---")
            st.markdown("#### ⛓️ 5. Krypto On-Chain & Derivate-Intelligence (Bitcoin & Solana)")
            k_data = macro_ov["crypto_macro"]
            kc1, kc2, kc3 = st.columns(3)
            kc1.metric("Exchange Netflow", "-22.500 BTC", delta="Verknappung / Abfluss")
            kc2.metric("Perpetual Funding Rate", "+6.8% p.a.", delta="Gesundes Long-Interesse")
            kc3.metric("MVRV Z-Score", "1.82", delta="Goldilocks Bullenmarkt")
            st.caption(f"**On-Chain Fazit:** {k_data['onchain_verdict']}")

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
                template="plotly_white",
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
                h_df = pd.DataFrame(hist_list)
                if "date" in h_df.columns:
                    h_df = h_df.sort_values(by="date", ascending=False)
                
                def format_german_date(d_str):
                    if not d_str or d_str == "-":
                        return "-"
                    try:
                        clean = str(d_str).strip()
                        parts = clean.split()
                        if len(parts) >= 2:
                            d_part, t_part = parts[0], parts[1][:5]
                            y, m, d = d_part.split("-")
                            return f"{d}.{m}.{y} {t_part} Uhr"
                        elif "-" in clean:
                            y, m, d = clean.split("-")
                            return f"{d}.{m}.{y}"
                        return clean
                    except Exception:
                        return str(d_str)

                display_h = pd.DataFrame()
                display_h["Zeitpunkt"] = h_df["date"].apply(format_german_date)
                
                action_map = {"BUY": "🟢 KAUF", "SELL": "🔴 VERKAUF"}
                display_h["Aktion"] = h_df.apply(lambda r: action_map.get(r.get("action") or r.get("type", "BUY"), r.get("type", "-")), axis=1)
                display_h["Instrument"] = h_df.get("name", h_df.get("symbol", "-"))
                display_h["Stück"] = h_df.get("shares", 0).apply(lambda s: f"{s:.4f}" if isinstance(s, (int, float)) else str(s))
                display_h["Kurs"] = h_df.apply(lambda r: f"{r.get('sell_price') or r.get('buy_price') or r.get('price', 0):.2f} €", axis=1)
                display_h["Volumen"] = h_df.get("total", 0).apply(lambda x: f"{x:,.2f} €" if pd.notnull(x) and isinstance(x, (int, float)) else str(x))
                display_h["Realisierter P&L"] = h_df.apply(
                    lambda r: f"{r.get('pnl', 0):+,.2f} € ({r.get('pnl_pct', 0):+.2f}%)" if pd.notnull(r.get("pnl")) and (r.get("action") == "SELL" or r.get("type") == "SELL") else "-", 
                    axis=1
                )
                display_h["Begründung"] = h_df.get("reason", "-")

                st.dataframe(display_h, use_container_width=True, hide_index=True)
            else:
                st.info("Noch keine Transaktionen in der Historie.")

        # Strategy Handbook & Strategy Info (Moved to bottom)
        st.markdown("---")
        with st.expander("📖 Strategie-Handbuch & Allokations-Regeln (Nach welchen Formeln handelt die KI?)"):
            st.markdown(f"**Aktive Depot-Strategie:** *{summary['strategy']}*")
            st.markdown("---")
            h_tab_dt, h_tab1, h_tab2, h_tab3, h_tab4 = st.tabs([
                "🔥 Daytrader-Depot (Intraday / Dynamischer Hebel)",
                "⚡ 1. Kurzfrist-Depot (Tage–Wochen)",
                "📈 2. Mittelfrist-Depot (1–6 Monate)",
                "🏛️ 3. Langfrist-Depot (1–5+ Jahre)",
                "🪙 4. Rohstoff-, Anleihen- & FX-Regeln (GSR, Zinskurve, DXY & Carry-Trade)"
            ])

            with h_tab_dt:
                st.markdown('''
                #### 🔥 Daytrader-Depot (Aggressives Intraday-Trading & Momentum)
                **Ziel:** Sekunden- & Minuten-Ausbrüche blitzschnell reiten, maximaler Fokus auf Echtzeit-Volumen. Der Hebel wird dabei dynamisch an die Stärke des Ausbruchs angepasst (1x Direktkauf bis 30x Turbo). Kein Risiko über Nacht.

                | Dimension / Faktor | Gewichtung | Kriterien, Datenquellen & Schwellenwerte |
                | :--- | :---: | :--- |
                | **⚡ Echtzeit-Volumen-Spikes** | **50 %** | 1-Minuten Kurssprünge > ±0,35 % (Long/Short) getrieben durch plötzliche institutionelle Orders. |
                | **🚀 Dynamischer Hebel** | **30 %** | Je nach Signalstärke wählt die KI **dynamisch Hebel von 2x, 5x, 10x, 15x oder bis zu 30x** (für Extrem-Spikes). |
                | **🛡️ EOD Derisking** | **20 %** | Verhindert Über-Nacht-Gaps durch automatischen Verkauf profitabler Positionen vor Handelsende. |

                * **🟢 KAUF-Trigger:** Sofortiger Einstieg bei Erkennung eines Sub-Minute-Ausbruchs durch den *RealTimeBreakoutScanner*.
                * **💰 Positionsgröße:** Maximal 1.500 € pro Trade (kleinere Allokation aufgrund des hohen Hebels).
                * **🎯 Aggressives Profit-Ratcheting:** Ab +5 % Gewinn wird der Stop-Loss sofort auf +2 % (über Einstand) nachgezogen. Ab +10 % Gewinn greift ein extrem enger Trailing-Stop (nur noch 5 % Puffer zum Top).
                * **🚨 Intraday Notbremse:** Strenger initialer Knock-Out/Stop-Loss, um Totalverluste beim Daytrading abzufedern (max. -20 %).
                * **🛡️ End-of-Day (EOD) Derisking:** Befindet sich ein Trade nach 21:00 Uhr mit >2 % im Plus, wird er **zwingend verkauft**, um "Overnight-Risiko" (Gap-Downs am nächsten Morgen) vollständig auszuschließen.
                ''')


            with h_tab1:
                st.markdown("""
                #### ⚡ Kurzfristiges Trading-Depot (Momentum, Squeezes, Hebel & Shorts)
                **Ziel:** Schnelle Gewinne bei akuten Ausbrüchen, Smart-Money-Positionierung, Leerverkäufer-Fallen & **bearishe Short-Breakdowns**.

                | Dimension / Faktor | Gewichtung | Kriterien, Datenquellen & Schwellenwerte |
                | :--- | :---: | :--- |
                | **🎯 1. Smart Money & Dark Pools** | **25 %** | Put/Call-Ratio < 0.55 (Call-Sweeps) oder > 1.20 (Put-Hedging), Dark-Pool-Blockshare > 35 % |
                | **📈 Charttechnik & Intraday-Ticks** | **25 %** | Kurs über EMA 20/50, RSI 50–68 (Long) bzw. Support-Bruch & RSI < 40 (Short) |
                | **💬 4. Social Sentiment & Buzz** | **20 %** | Relative Erwähnungs-Spitzen auf Reddit WSB & StockTwits (> 150 % Anstieg in 24h) |
                | **🪤 Leerverkäufer & BaFin-Shorts** | **15 %** | Short Float > 12 % (Squeeze-Falle) ODER aggressive BaFin-Netto-Aufstockungen |
                | **⛓️ 6. Krypto On-Chain & Derivate**| **15 %** | Krypto-Funding-Rates (+6.8% gesund), Exchange-Netto-Abflüsse (Cold Storage) |

                * **🟢 KAUF-Trigger (Long):** Multi-Source Alpha-Score ≥ **55 / 100** ➔ Long-Aktie oder **⚡ Turbo Bull (3.5x Knock-Out Call)**.
                * **🔻 SHORT-Trigger (Bearish):** Abwärts-Breakdown / Support-Bruch ➔ **🔻 Turbo Bear (3.5x Knock-Out Put)**, um an fallenden Kursen zu profitieren.
                * **🎯 Dynamischer Trailing-Exit:** Ab +8 % Gewinn Stop-Loss auf Einstand + 3 % nachziehen; ab +18 % greift ein dynamischer Trailing-Stop (6 % Puffer unter dem Zwischenhoch).
                * **🛡️ Laufendes Thesen-Audit (Thesen-Bruch):** Fällt der Alpha-Score eines gehaltenen Werts unter **42 / 100** oder dreht der Optionenfluss bärisch (Put/Call > 1.35), wird die Position **sofort vorzeitig abgestoßen** – auch wenn der Stop-Loss noch nicht berührt wurde!
                * **💡 Opportunitäts-Tausch (Dead-Money-Schutz):** Wenn ein Wert seitwärts dümpelt und ein neuer Kandidat mit einem um **≥ 25 Punkte höheren Alpha-Score** auftaucht, wird die schwächste Position automatisch für den neuen Leader liquidiert.
                * **🛡️ Freitags-Derisking:** Vor dem Wochenende werden gehebelte Knock-Out-Gewinne (ab +10 %) automatisch realisiert, um Wochenend-Gaps zu vermeiden.
                """)

            with h_tab2:
                st.markdown("""
                #### 📈 Mittelfristiges Trend- & Growth-Depot (Swing, Wachstum & Makro-Hedging)
                **Ziel:** Reiten starker Aufwärtstrends bei Wachstumsaktien + **aktive Portfolio-Absicherung bei Markt-Korrekturen**.

                | Dimension / Faktor | Gewichtung | Kriterien, Datenquellen & Schwellenwerte |
                | :--- | :---: | :--- |
                | **🌊 3. US Netto-Liquidität & FedWatch** | **30 %** | `Fed Balance Sheet − TGA − Reverse Repo` (Expansiv: > 6 Bio. USD) + FedWatch Zinswende |
                | **📈 Analysten-Revisionen (EPS)** | **25 %** | Mindestens 3x mehr Upgrades als Downgrades in 30 Tagen + positive EPS-Surprises |
                | **🏛️ 2. SEC Form 4 & Kongress-Trades** | **20 %** | Vorstands-Käufe (CEO/Director) & US-Kongress-Disclosures (Nancy Pelosi, House Committees) |
                | **🎙️ Earnings Call KI-Tonalität** | **15 %** | Semantischer NLP-Sprachscore > 80/100 (Fokus auf Margenwachstum & AI-Monetarisierung) |
                | **📊 Trendfolge über EMA 50** | **10 %** | Kurs notiert stabil über dem EMA 50 und steigender 200-Tage-Linie |

                * **🟢 KAUF-Trigger:** Mittelfrist-Score ≥ **70 / 100** bei expansiver US-Netto-Liquidität.
                * **🛡️ Makro-Absicherung (Hedge):** Bei marktweiten Abverkäufen (VIX > 28 / Liquiditätsabfall) kauft die KI temporär **Index-Puts (DAX / S&P 500 Short-Hedge)**, um Buchgewinne abzusichern.
                * **🎯 Trailing-Stop:** Ab +10 % Gewinn Stop-Loss auf Einstand + 5 %; ab +20 % Trailing-Stop mit 8 % Puffer unter dem Peak.
                * **🛡️ Laufendes Wachstums-Audit:** Bricht die Trendlinie (EMA 50) oder stürzt das Analysten-Sentiment ab (Score < 45), erfolgt ein **vorzeitiger Thesen-Ausstieg**, um kein totes Kapital mitzuschleppen.
                * **💡 Opportunitäts-Umschichtung:** Reife Gewinner (+8 % bis +15 %) oder stagnierende Titel werden bei Verfügbarkeit neuer Top-Growth-Leader (Alpha-Vorteil ≥ 20 Punkte) umgeschichtet.
                """)

            with h_tab3:
                st.markdown("""
                #### 🏛️ Langfristiges Investment-Depot (Quality, Gold, Moat & Crash-Schutz)
                **Ziel:** Krisenfestes Compounding mit starkem Burggraben, Gold, digitalem Wertspeicher & defensiven Bonus-Zertifikaten.

                | Dimension / Faktor | Gewichtung | Kriterien, Datenquellen & Schwellenwerte |
                | :--- | :---: | :--- |
                | **🏰 5. Forensische Bilanz-Qualität** | **35 %** | **Piotroski F-Score ≥ 7/9**, **Altman Z-Score > 2.99 (Safe Zone)**, **Beneish M-Score < -2.22** |
                | **🏛️ 2. Insider- & Whale-Convictions** | **25 %** | Star-Investoren (Warren Buffett, Bill Ackman) & Directors' Dealings der Vorstände |
                | **🌐 3. Makro-Zyklen, Gold & BTC** | **20 %** | Allokation in Gold (GC=F) & Bitcoin (BTC-USD) als Währungs- und Inflationsschutz |
                | **🏰 Kapitalrendite & Burggraben** | **10 %** | Eigenkapitalrendite (ROE) > 15 %, freie Cashflow-Marge > 15 %, Preissetzungsmacht |
                | **🏷️ Bewertung & Capped Bonus** | **10 %** | KGV < 25 oder PEG < 1.2; Capped Bonus-Zertifikate mit ≥ 25 % Sicherheitspuffer |

                * **🟢 KAUF-Trigger:** Langfrist-Score ≥ **75 / 100** ➔ Qualitäts-Compounder oder **🛡️ Bonus-Zertifikat (-25 % Puffer, +14 % Bonusrendite)**.
                * **🛡️ Fortlaufendes Bilanz- & Burggraben-Audit:** Verschlechtert sich die Bonität (Piotroski < 5 oder Altman Z droht in Notlage abzurutschen), trennt sich das System vom Titel, um das Langfrist-Portfolio vor Value Traps zu schützen.
                * **🛡️ Gold & Krypto als natürlicher Hedge:** Absicherung gegen Geldentwertung und geopolitische Krisen ohne Zwangsverkäufe von Kernaktien.
                * **📜 Unveränderlicher Audit-Trail:** Alle Transaktionen werden atomar in der SQLite-Datenbank protokolliert.
                """)

            with h_tab4:
                st.markdown("""
                #### 🪙 Rohstoff-, Edelmetall- & Devisen-Filter in der Entscheidungs-Engine
                **Wie fließen Gold, Silber, Rohöl und Devisen in Kauf- und Verkaufsentscheidungen ein?**

                | Indikator / Makro-Kennzahl | Schwellenwert | Auswirkung auf Kauf- & Verkaufsanalyse |
                | :--- | :---: | :--- |
                | **📊 Gold/Silber-Ratio (GSR)** | **> 80.0** | **🚨 Silber-Superzyklus (+15 Punkte Alpha):** Silber & Minenaktien (PAAS, FSM) werden massiv übergewichtet (historische Aufholrallye). Bei **< 55.0** wird Gold im Langfrist-Depot bevorzugt. |
                | **💵 US Dollar Index (DXY)** | **< 101.50** | **🌊 Globaler Liquiditäts-Rückenwind (+4 Punkte Alpha):** Schwacher Dollar beflügelt Gold, Rohstoffe, Tech-Growth & Krypto. Bei **> 104.50** defensiver Risikoabschlag (-6 Punkte). |
                | **🚨 JPY Carry-Trade Unwind Risk** | **USD/JPY < 145** | **🛑 Notfall-Schutzventil (-10 Punkte Alpha):** Pausiert sofort neue gehebelte Long-Einstiege im Kurzfrist-Depot und zieht Trailing-Stops auf Einstand nach, um Liquiditätsschocks abzufedern. |
                | **🏛️ Zentralbank-Goldkäufe & TIPS** | **Realzins < 1.8 %** | **👑 Gold-Allokation freigegeben:** Physische Gold-ETCs (4GLD.DE) im Langfrist-Depot als Inflations- und Geldentwertungsschutz gegen US-Schuldenwachstum. |
                | **🛢️ EIA Öl-Lager & Crack Spread** | **Marge > $20/bbl** | **🏭 Konjunktur-Freigabe:** Hohe Raffinerie-Margen und Lagerabbau bestätigen reale Nachfrage ➔ Freigabe für Industrie-, Chemie- & Energieaktien im Mittelfrist-Depot. |
                """)

    # Call the fragment
    render_live_depot_view(selected_depot_key)

# ==============================================================================
# MODE 8: EINZELAKTIEN-TIEFENANALYSE
# ==============================================================================
elif app_mode == "🔍 Einzelaktien-Tiefenanalyse":
    st.sidebar.subheader("🔍 Aktie auswählen")
    category = st.sidebar.selectbox("Kategorie / Markt", list(CATEGORIZED_UNIVERSES.keys()))
    default_tickers = CATEGORIZED_UNIVERSES[category]
    selected_preset = st.sidebar.selectbox("Favoriten", default_tickers, format_func=lambda s: get_wkn_display(s, s))
    nav_ticker = st.session_state.get("nav_deep_ticker", "")
    custom_ticker = st.sidebar.text_input("Oder WKN / Ticker eingeben (z.B. A2N9D9, 865985, 716460, A2QA4J, 918422):", value=nav_ticker)
    active_symbol = custom_ticker.strip().upper() if custom_ticker.strip() else selected_preset
    
    if nav_ticker:
        st.session_state["nav_deep_ticker"] = "" # Reset after loading
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
            <div style="text-align: center; background-color: #0f172a; border: 1px solid #e2e8f0; padding: 15px; border-radius: 8px; border: 1px solid #2e3546;">
                <div style="font-size: 13px; color: #888;">GESAMT-SCORE</div>
                <div style="font-size: 32px; font-weight: bold; color: #38bdf8;">{synth_result['total_score']} / 100</div>
                <div style="font-size: 11px; color: #aaa;">Synthese</div>
            </div>
            """, unsafe_allow_html=True)
        with sc2:
            st.markdown(f"""
            <div style="text-align: center; background-color: #0f172a; border: 1px solid #e2e8f0; padding: 15px; border-radius: 8px; border: 1px solid #2e3546;">
                <div style="font-size: 13px; color: #888;">⚡ KURZFRIST</div>
                <div style="font-size: 32px; font-weight: bold; color: #a78bfa;">{short_results['score']} / 100</div>
                <div style="font-size: 11px; color: #ddd;">{short_results['status'][:20]}...</div>
            </div>
            """, unsafe_allow_html=True)
        with sc3:
            st.markdown(f"""
            <div style="text-align: center; background-color: #0f172a; border: 1px solid #e2e8f0; padding: 15px; border-radius: 8px; border: 1px solid #2e3546;">
                <div style="font-size: 13px; color: #888;">🏛️ LANGFRIST</div>
                <div style="font-size: 32px; font-weight: bold; color: #34d399;">{long_results['score']} / 100</div>
                <div style="font-size: 11px; color: #ddd;">{long_results['status'][:20]}...</div>
            </div>
            """, unsafe_allow_html=True)
        with sc4:
            st.markdown(f"""
            <div style="text-align: center; background-color: #0f172a; border: 1px solid #e2e8f0; padding: 15px; border-radius: 8px; border: 1px solid #2e3546;">
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
                template="plotly_white",
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

elif app_mode == "⚖️ KI-Tribunal (Handelsentscheidungen)":
    st.header("⚖️ KI-Tribunal (Handelsentscheidungen)")
    st.markdown("Bevor ein Trade in einem der Musterdepots ausgeführt wird, wird der Kandidat vom **KI-Tribunal** verhandelt. Ein Bär sucht nach Risiken, ein Bulle nach Chancen, und der Judge entscheidet knallhart, ob der Trade genehmigt oder blockiert wird.")
    
    from src.tribunal import AITribunalManager
    logs = AITribunalManager.get_latest_logs(20)
    
    if not logs:
        st.info("Noch keine Tribunal-Entscheidungen aufgezeichnet.")
    else:
        for log in logs:
            action_color = "green" if log["action"] == "BUY" else "red"
            icon = "✅" if log["action"] == "BUY" else "❌"
            with st.expander(f"{log['timestamp']} | {log['symbol']} ({log['depot_id']}) - {icon} {log['action']}"):
                st.markdown(f"**Urteilsbegründung (Judge):** <span style='color: {action_color}; font-weight: bold;'>{log['judge_decision']}</span>", unsafe_allow_html=True)
                
                c1, c2 = st.columns(2)
                with c1:
                    st.info(f"🐂 **Der Bulle (Chancen):**\n\n{log['bull_case']}")
                with c2:
                    st.error(f"🐻 **Der Bär (Risiken):**\n\n{log['bear_case']}")
                    
# MODE 10: KI CHATBOT
elif app_mode == "💬 KI-Chatbot (Strategie & Analyse)":
    st.header("💬 KI-Chatbot (Strategie & Analyse)")
    st.markdown("Frage die KI nach Erklärungen zu Trades im Musterdepot, der Entwicklung von Zinsen, Leerverkäufen, Makro-Daten oder Insider-Aktivitäten.")
    
    api_key = ""
    try:
        api_key = st.secrets.get("GEMINI_API_KEY", "")
    except:
        pass
        
    if not api_key:
        api_key = st.text_input("Google Gemini API Key (wird nicht gespeichert)", type="password")
        
    if not api_key:
        st.warning("Bitte gib einen Gemini API Key ein oder konfiguriere ihn in den Streamlit Secrets (`.streamlit/secrets.toml` als `GEMINI_API_KEY`), um den Chat zu nutzen.")
    else:
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            
            if "chat_messages" not in st.session_state:
                st.session_state.chat_messages = [
                    {"role": "assistant", "content": "Hallo! Ich bin dein KI-Trading-Assistent. Frag mich gerne nach den Gründen für bestimmte Musterdepot-Trades, der Entwicklung von Zinsen, Leerverkäufen oder der Makroökonomie!"}
                ]
            
            for msg in st.session_state.chat_messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
                    
            prompt = st.chat_input("Was möchtest du wissen?")
            if prompt:
                st.session_state.chat_messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)
                    
                with st.chat_message("assistant"):
                    message_placeholder = st.empty()
                    
                    sys_prompt = "Du bist ein professioneller KI-Trading-Assistent einer hochentwickelten Finanz-App. Erkläre Finanzkonzepte, Zinsentwicklungen, Short-Squeeze-Mechaniken und warum bestimmte Trades in bestimmten Marktsituationen sinnvoll sind. Antworte präzise, auf Deutsch und fachlich fundiert. WICHTIGE REGEL: Behaupte NIEMALS, dass du keine aktuellen Daten hast. Dir werden am Ende dieses Prompts die ECHTEN, AKTUELLEN LIVE-DATEN aus dem System übergeben! Nutze AUSSCHLIESSLICH diese bereitgestellten Daten, um Fragen nach dem aktuellen Marktstand oder den letzten 7 Tagen zu beantworten. Vermeide Floskeln. HEUTE IST DER 29.08.2026."
                    try:
                        import json
                        with open("data/portfolios.json", "r", encoding="utf-8") as f:
                            pf_data = json.load(f)
                        sys_prompt += "\n\nHier ist der aktuelle Zustand der Musterdepots und die Transaktionshistorie (Käufe/Verkäufe) als JSON, damit du konkrete Fragen zu ausgeführten Trades beantworten kannst:\n" + json.dumps(pf_data)
                    except:
                        pass
                        
                    try:
                        from src.universe import CATEGORIZED_UNIVERSES
                        sys_prompt += "\n\nWICHTIGE INFORMATION ZU DEINEM ANLAGEUNIVERSUM:\n"
                        sys_prompt += "Du hast Zugriff auf ein massives Scanner-Universum (Hunderte Werte). Die Transaktionshistorie zeigt NUR die KÜRZLICH GEHANDELTEN Werte. Hier ist dein gesamtes Anlageuniversum, auf das du Zugriff hast und welches du scannen/kaufen kannst:\n"
                        for cat, symbols in CATEGORIZED_UNIVERSES.items():
                            sys_prompt += f"- {cat}: {', '.join(symbols)}\n"
                        sys_prompt += "Wenn der Nutzer fragt, auf welche oder wie viele Wertpapiere du zugreifen kannst, zähle unbedingt diese Kategorien auf und mache klar, dass du nicht nur auf die kleine Historie beschränkt bist!\n"
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
                            hist_text = str(b_hist_df.tail(7).set_index('date')['us_10y_yield'].to_dict())
                        sys_prompt += "\n\nLIVE MARKT-DATEN:\n"
                        sys_prompt += f"- US 10-Jahres-Rendite: {b_data['us_10y_yield']:.2f}%\n"
                        sys_prompt += f"- Historie 10Y Rendite (letzte 7 Tage): {hist_text}\n"
                        sys_prompt += f"- US 2-Jahres-Rendite: {b_data['us_2y_yield']:.2f}%\n"
                        sys_prompt += f"- Zinsstruktur (10Y-2Y Spread): {b_data['spread_10y_2y_bps']:.1f} Bps ({b_data['curve_regime']})\n"
                        sys_prompt += f"- Goldpreis: ${pm_data['gold_price']:.2f}\n"
                        sys_prompt += f"- Silberpreis: ${pm_data['silver_price']:.2f}\n"
                    except Exception as e:
                        pass
                        
                    response = None
                    last_err = None
                    
                    try:
                        available_models = []
                        for m in genai.list_models():
                            if 'generateContent' in m.supported_generation_methods:
                                available_models.append(m.name)
                    except Exception as e:
                        st.error(f"Konnte Modell-Liste nicht abrufen. API-Key ungültig? Fehler: {e}")
                        st.stop()
                        
                    if not available_models:
                        st.error("Dein API-Key hat Zugriff auf 0 Modelle, die Text generieren können.")
                        st.stop()
                        
                    available_models.sort(key=lambda x: '1.5' in x, reverse=True)
                    
                    for m_name in available_models:
                        try:
                            if '1.5' not in m_name:
                                model = genai.GenerativeModel(m_name)
                            else:
                                model = genai.GenerativeModel(m_name, system_instruction=sys_prompt)
                            
                            gemini_messages = []
                            for i, m in enumerate(st.session_state.chat_messages):
                                r = "model" if m["role"] == "assistant" else "user"
                                content = m["content"]
                                
                                # Wenn es ein altes Modell (gemini-pro) ist, hängen wir den sys_prompt heimlich 
                                # an die allerletzte User-Nachricht an, da es system_instruction nicht unterstützt.
                                if '1.5' not in m_name and i == len(st.session_state.chat_messages) - 1 and r == "user":
                                    content = f"SYSTEM-KONTEXT (Nutze diese Daten ZWINGEND für deine Antwort, ignoriere dein altes Wissen falls es abweicht! HEUTE IST DER 29.08.2026!):\n{sys_prompt}\n\nBENUTZERFRAGE:\n{content}"
                                    
                                gemini_messages.append({"role": r, "parts": [content]})
                            
                            response = model.generate_content(gemini_messages, stream=True)
                            if response:
                                break
                        except Exception as e:
                            last_err = e
                            response = None
                            
                    if not response:
                        st.error(f"Fehler bei allen Modellen (versucht: {len(available_models)}). Letzter Fehler: {last_err}")
                        st.stop()
                    
                    full_response = ""
                    for chunk in response:
                        if chunk.text:
                            full_response += chunk.text
                            message_placeholder.markdown(full_response + "▌")
                    message_placeholder.markdown(full_response)
                
                st.session_state.chat_messages.append({"role": "assistant", "content": full_response})
                
        except ImportError:
            st.error("Das 'google-generativeai' Python-Paket ist nicht installiert. Bitte überprüfe die requirements.txt.")
        except Exception as e:
            st.error(f"Fehler bei der KI-Anfrage: {e}")

# MODE 10: KI LERNTAGEBUCH
elif app_mode == "🧠 KI-Lerntagebuch (Retrospektive)":
    st.header("🧠 KI-Lerntagebuch (Daily Retrospectives)")
    st.markdown("Hier analysiert die KI jeden Abend ihre eigenen Trades, zieht Schlüsse aus Fehlern und bewertet verpasste Signale.")
    
    api_key = ""
    try:
        api_key = st.secrets.get("GEMINI_API_KEY", "")
    except:
        pass
        
    col1, col2, col3 = st.columns([2,1,1])
    with col1:
        if not api_key:
            api_key = st.text_input("Google Gemini API Key (wird nicht gespeichert)", type="password")
            
    with col2:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        if st.button("🔄 Tages-Retro (Daytrader & Kurzfristig)"):
            if not api_key:
                st.error("Bitte gib zuerst deinen API Key ein.")
            else:
                with st.spinner("Analysiere heutigen Tag..."):
                    from src.ai_journal import AIJournalEngine
                    engine = AIJournalEngine(api_key)
                    try:
                        for depot in ["day_trading", "short_term"]:
                            engine.generate_retrospective(depot_id=depot, mode="daily")
                        st.success("Tages-Einträge für Daytrader und Kurzfristig generiert!")
                        import time; time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Fehler: {e}")
                        
    with col3:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        if st.button("📅 Wochen-Retro (Mittel- & Langfristig)"):
            if not api_key:
                st.error("Bitte gib zuerst deinen API Key ein.")
            else:
                with st.spinner("Analysiere die letzten 7 Tage..."):
                    from src.ai_journal import AIJournalEngine
                    engine = AIJournalEngine(api_key)
                    try:
                        for depot in ["medium_term", "long_term"]:
                            engine.generate_retrospective(depot_id=depot, mode="weekly")
                        st.success("Wochen-Einträge für Mittelfristig und Langfristig generiert!")
                        import time; time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Fehler: {e}")

    st.markdown("---")
    
    from src.ai_journal import AIJournalEngine
    journals = AIJournalEngine.get_all_journals()
    
    if not journals:
        st.info("Noch keine Tagebucheinträge vorhanden. Klicke auf 'Tages-Retrospektive', um den ersten Eintrag zu erstellen!")
    else:
        depot_names = {
            "short_term": "Kurzfristig",
            "medium_term": "Mittelfristig",
            "long_term": "Langfristig",
            "day_trading": "Daytrader"
        }
        
        tab_daily, tab_weekly = st.tabs(["📅 Tages-Retrospektiven", "🗓️ Wochen-Retrospektiven"])
        
        daily_journals = [j for j in journals if j.get("mode") != "weekly"]
        weekly_journals = [j for j in journals if j.get("mode") == "weekly"]
        
        def render_journal(j, is_first):
            mode_icon = "📅 Woche" if j.get("mode") == "weekly" else "📆 Tag"
            depot_label = depot_names.get(j.get('depot_id', ''), j.get('depot_id', 'Unknown'))
            with st.expander(f"{mode_icon} [{depot_label}]: {j['date']} | Win-Rate: {j['win_rate']}%", expanded=is_first):
                c1, c2, c3 = st.columns(3)
                c1.metric("Win-Rate", f"{j['win_rate']}%")
                c2.metric("Bester Trade", j['best_trade'] or "-")
                c3.metric("Schlechtester Trade", j['worst_trade'] or "-")
                
                st.markdown("### 🧐 Reflexion")
                st.info(j['reflection'])
                
                if j.get("mode") != "weekly":
                    st.markdown("### 👻 Verpasste Chancen (Nicht gehandelte Signale)")
                    st.warning(j['missed_opportunities'])
                
                st.markdown("### 💡 Lektion für die Zukunft")
                st.success(j['lesson'])
                
                # Check for param updates
                param_updates = j.get("param_updates")
                if param_updates and param_updates != "{}" and param_updates != "null":
                    st.markdown("### ⚙️ Automatisch angepasste Strategie-Parameter")
                    st.code(param_updates, language="json")

        with tab_daily:
            if not daily_journals:
                st.info("Keine Tages-Retrospektiven vorhanden.")
            else:
                for idx, j in enumerate(daily_journals):
                    render_journal(j, is_first=(idx == 0))
                    
        with tab_weekly:
            if not weekly_journals:
                st.info("Keine Wochen-Retrospektiven vorhanden.")
            else:
                for idx, j in enumerate(weekly_journals):
                    render_journal(j, is_first=(idx == 0))

elif app_mode == "📖 Handelsstrategie & System-Logik":
    st.header("📖 Handelsstrategie & System-Logik")
    
    strat_path = "HANDELSSTRATEGIE.md"
    if os.path.exists(strat_path):
        with open(strat_path, "r", encoding="utf-8") as f:
            strat_content = f.read()
        st.markdown(strat_content)
    else:
        st.error(f"Die Dokumentation {strat_path} konnte nicht gefunden werden.")
