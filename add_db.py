import sqlite3
c = sqlite3.connect('data/portfolio.db')
c.execute("""
INSERT OR IGNORE INTO depots (id, name, strategy, initial_cash, cash) 
VALUES ('day_trading', 'Daytrader Depot', 'Aggressives Intraday-Trading & Momentum (Hebelprodukte)', 10000.0, 10000.0)
""")
c.commit()
print('Done.')
