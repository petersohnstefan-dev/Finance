"""Automated Scheduler for periodic Forum & Market Scans."""
import time
import datetime
from src.market_scanner import MarketScanner

def run_scheduled_scanner(interval_hours: int = 4):
    print(f"=== Börsen & Foren Scanner-Service gestartet ===")
    print(f"Intervall: Alle {interval_hours} Stunden")
    
    scanner = MarketScanner()
    while True:
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n[{now_str}] Starte automatischen Scan-Durchlauf...")
        try:
            results = scanner.run_full_scan()
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Scan beendet: {len(results)} Aktien aktualisiert.")
        except Exception as e:
            print(f"Fehler im Scan-Durchlauf: {e}")
            
        print(f"Warte {interval_hours} Stunden bis zum nächsten Scan...")
        time.sleep(interval_hours * 3600)

if __name__ == "__main__":
    run_scheduled_scanner(interval_hours=4)
