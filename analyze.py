import argparse
import sys
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from src.data_fetcher import FinancialDataFetcher
from src.indicators import calculate_technical_indicators
from src.short_term_engine import ShortTermEngine
from src.long_term_engine import LongTermEngine
from src.synthesis import DecisionSynthesizer

console = Console()

def run_analysis(ticker_symbol: str):
    console.print(f"\n[bold cyan]=== Analyse gestartet für: {ticker_symbol.upper()} ===[/bold cyan]")
    
    try:
        fetcher = FinancialDataFetcher(ticker_symbol)
        df_prices = fetcher.get_historical_prices(period="1y")
        df_with_ind = calculate_technical_indicators(df_prices)
        fundamentals = fetcher.get_fundamentals()
        consensus = fetcher.get_analyst_consensus()
        sentiment = fetcher.get_social_sentiment()
    except Exception as e:
        console.print(f"[bold red]Fehler beim Laden:[/bold red] {e}")
        sys.exit(1)

    short_engine = ShortTermEngine()
    long_engine = LongTermEngine()
    synthesizer = DecisionSynthesizer()

    short_res = short_engine.evaluate(df_with_ind, sentiment)
    long_res = long_engine.evaluate(fundamentals, consensus)
    synth = synthesizer.synthesize(short_res, long_res, fundamentals, consensus)

    # 1. Header Overview
    curr = fundamentals.get('currency', 'USD')
    price = fundamentals.get('currentPrice', 0)
    company = fundamentals.get('shortName', ticker_symbol)
    
    console.print(Panel(
        f"[bold white]{company} ({ticker_symbol.upper()})[/bold white]\n"
        f"Kurs: [bold yellow]{price:.2f} {curr}[/bold yellow] | "
        f"Sektor: {fundamentals.get('sector')} | "
        f"Industrie: {fundamentals.get('industry')}",
        title="?? Unternehmensprofil",
        border_style="cyan"
    ))

    # 2. Decision Synthesis Banner
    color_map = {"green": "bold green", "blue": "bold blue", "orange": "bold yellow", "gray": "bold white", "red": "bold red"}
    console.print(Panel(
        f"[bold]{synth['action']}[/bold]\n\n"
        f"{synth['action_desc']}\n\n"
        f"Gesamt-Score: [bold cyan]{synth['total_score']}/100[/bold cyan] | "
        f"Kurzfristig: [magenta]{short_res['score']}/100[/magenta] | "
        f"Langfristig: [green]{long_res['score']}/100[/green]",
        title="?? KI-Entscheidungs-Synthese",
        border_style=color_map.get(synth['color'], "white")
    ))

    # 3. Tables for Tracks
    t_short = Table(title="? Schiene 1: Kurz- & Mittelfristige Signale (Momentum & Sentiment)")
    t_short.add_column("Typ", justify="center")
    t_short.add_column("Signal", style="bold")
    t_short.add_column("Beschreibung")
    for s in short_res['signals']:
        icon = "[green]??[/green]" if s['type'] == 'bullish' else ("[red]??[/red]" if s['type'] == 'bearish' else "[yellow]??[/yellow]")
        t_short.add_row(icon, s['title'], s['desc'])
    console.print(t_short)

    t_long = Table(title="??? Schiene 2: Langfristige Fundamentaldaten & Bewertung")
    t_long.add_column("Typ", justify="center")
    t_long.add_column("Kennzahl / Signal", style="bold")
    t_long.add_column("Beschreibung")
    for s in long_res['signals']:
        icon = "[green]??[/green]" if s['type'] == 'bullish' else ("[red]??[/red]" if s['type'] == 'bearish' else "[yellow]??[/yellow]")
        t_long.add_row(icon, s['title'], s['desc'])
    console.print(t_long)

    # 4. Analyst Target
    upside = consensus.get('upsideMeanPct')
    t_mean = consensus.get('targetMeanPrice')
    if t_mean:
        console.print(f"\n?? [bold]Analysten-Konsens:[/bold] Mittleres Kursziel: [bold]{t_mean:.2f} {curr}[/bold] (Potenzial: [bold green]{upside:+.1f}%[/bold green] | Analysten: {consensus.get('numberOfAnalystOpinions')})")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Stock Decision Support CLI")
    parser.add_argument("--ticker", "-t", type=str, default="SAP.DE", help="Stock ticker (e.g. NVDA, SAP.DE, AAPL)")
    args = parser.parse_args()
    run_analysis(args.ticker)
