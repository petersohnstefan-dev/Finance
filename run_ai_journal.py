import os
import sys

# Wir müssen sicherstellen, dass wir aus dem root Ordner laufen
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.ai_journal import AIJournalEngine

def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Fehler: GEMINI_API_KEY Umgebungsvariable nicht gesetzt.")
        print("Stelle sicher, dass der Key als GitHub Secret hinterlegt ist.")
        sys.exit(1)
        
    engine = AIJournalEngine(api_key)
    
    mode = "weekly" if len(sys.argv) > 1 and sys.argv[1] == "--weekly" else "daily"
    
    if mode == "daily":
        print("=" * 60)
        print("🧠 KI-Lerntagebuch — Tägliche Retrospektive")
        print("=" * 60)
        for depot in ["day_trading", "short_term"]:
            try:
                print(f"\n📊 Analysiere {depot}...")
                result = engine.generate_retrospective(depot_id=depot, mode="daily")
                print(f"  ✅ Erfolgreich generiert für: {depot}")
                print(f"  Win-Rate (gesamt): {result['win_rate']}%")
                if result.get('param_updates') and result['param_updates'] != '{}':
                    print(f"  🔧 Parameter-Updates: {result['param_updates']}")
            except Exception as e:
                print(f"  ❌ Fehler bei {depot}: {e}")
    else:
        print("=" * 60)
        print("🧠 KI-Lerntagebuch — Wöchentliche Retrospektive")
        print("=" * 60)
        for depot in ["medium_term", "long_term"]:
            try:
                print(f"\n📊 Analysiere {depot}...")
                result = engine.generate_retrospective(depot_id=depot, mode="weekly")
                print(f"  ✅ Erfolgreich generiert für: {depot}")
                print(f"  Win-Rate (gesamt): {result['win_rate']}%")
                if result.get('param_updates') and result['param_updates'] != '{}':
                    print(f"  🔧 Parameter-Updates: {result['param_updates']}")
            except Exception as e:
                print(f"  ❌ Fehler bei {depot}: {e}")

    print("\n" + "=" * 60)
    print("🏁 Fertig.")

if __name__ == "__main__":
    main()
