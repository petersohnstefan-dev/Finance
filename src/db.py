import sqlite3
import os
import json
import datetime
from typing import Dict, Any, List, Optional

DB_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "portfolio.db")

class PortfolioDB:
    """Enterprise-grade SQLite database for persistent trade logging and daily portfolio tracking."""

    def __init__(self, db_path: str = DB_FILE):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            
            # Depots Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS depots (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                strategy TEXT,
                initial_cash REAL NOT NULL,
                cash REAL NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)

            # Open Positions Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                depot_id TEXT NOT NULL,
                symbol TEXT NOT NULL,
                name TEXT NOT NULL,
                shares REAL NOT NULL,
                buy_price REAL NOT NULL,
                current_price REAL NOT NULL,
                buy_date TEXT NOT NULL,
                stop_loss REAL,
                take_profit REAL,
                reason TEXT,
                UNIQUE(depot_id, symbol),
                FOREIGN KEY (depot_id) REFERENCES depots(id)
            );
            """)

            # Trade History Log (Immutable append-only ledger)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                depot_id TEXT NOT NULL,
                trade_type TEXT NOT NULL, -- 'BUY' or 'SELL'
                symbol TEXT NOT NULL,
                name TEXT NOT NULL,
                shares REAL NOT NULL,
                buy_price REAL,
                sell_price REAL,
                total_amount REAL NOT NULL,
                pnl REAL,
                pnl_pct REAL,
                executed_at TEXT NOT NULL,
                reason TEXT,
                FOREIGN KEY (depot_id) REFERENCES depots(id)
            );
            """)

            # Daily Performance Snapshots
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_date TEXT NOT NULL,
                depot_id TEXT NOT NULL,
                total_value REAL NOT NULL,
                cash REAL NOT NULL,
                invested_value REAL NOT NULL,
                pnl REAL NOT NULL,
                pnl_pct REAL NOT NULL,
                num_positions INTEGER NOT NULL,
                UNIQUE(snapshot_date, depot_id)
            );
            """)

            conn.commit()

    def record_trade(self, depot_id: str, trade_type: str, symbol: str, name: str, 
                     shares: float, total_amount: float, price: float, 
                     sell_price: Optional[float] = None, pnl: Optional[float] = None, 
                     pnl_pct: Optional[float] = None, reason: str = ""):
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO trades (
                depot_id, trade_type, symbol, name, shares, buy_price, sell_price, 
                total_amount, pnl, pnl_pct, executed_at, reason
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                depot_id, trade_type, symbol, name, shares, 
                price if trade_type == "BUY" else None,
                sell_price if trade_type == "SELL" else None,
                total_amount, pnl, pnl_pct, now_str, reason
            ))
            conn.commit()

    def record_daily_snapshot(self, depot_id: str, total_value: float, cash: float, 
                              invested_value: float, pnl: float, pnl_pct: float, num_positions: int):
        today_str = datetime.datetime.now().strftime("%Y-%m-%d")
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO daily_snapshots (
                snapshot_date, depot_id, total_value, cash, invested_value, pnl, pnl_pct, num_positions
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(snapshot_date, depot_id) DO UPDATE SET
                total_value = excluded.total_value,
                cash = excluded.cash,
                invested_value = excluded.invested_value,
                pnl = excluded.pnl,
                pnl_pct = excluded.pnl_pct,
                num_positions = excluded.num_positions
            """, (today_str, depot_id, total_value, cash, invested_value, pnl, pnl_pct, num_positions))
            conn.commit()
