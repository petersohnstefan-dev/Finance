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

            # Hourly Performance Snapshots (Starting 24.08.2026)

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS radar_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                detected_at TEXT NOT NULL,
                symbol TEXT NOT NULL,
                name TEXT NOT NULL,
                signal_price REAL NOT NULL,
                score REAL,
                theme TEXT
            );
            ''')
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS hourly_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                depot_id TEXT NOT NULL,
                snapshot_time TEXT NOT NULL,
                total_value REAL NOT NULL,
                cash REAL NOT NULL,
                invested_value REAL NOT NULL,
                pnl REAL NOT NULL,
                pnl_pct REAL NOT NULL,
                num_positions INTEGER NOT NULL,
                UNIQUE(snapshot_time, depot_id)
            );
            """)

            conn.commit()

    def record_trade(self, depot_id: str, trade_type: str, symbol: str, name: str, 
                     shares: float, total_amount: float, price: float, 
                     sell_price: Optional[float] = None, pnl: Optional[float] = None, 
                     pnl_pct: Optional[float] = None, reason: str = "",
                     executed_at: Optional[str] = None):
        now_str = executed_at or datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        buy_p = price if trade_type == "BUY" else price
        sell_p = sell_price if trade_type == "SELL" else None
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO trades (
                depot_id, trade_type, symbol, name, shares, buy_price, sell_price, 
                total_amount, pnl, pnl_pct, executed_at, reason
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                depot_id, trade_type, symbol, name, shares, 
                buy_p, sell_p,
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

    def get_previous_daily_close(self, depot_id: str) -> float:
        import datetime
        today_str = datetime.datetime.now().strftime("%Y-%m-%d")
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT total_value FROM daily_snapshots 
                WHERE depot_id = ? AND snapshot_date < ? 
                ORDER BY snapshot_date DESC LIMIT 1
            """, (depot_id, today_str))
            row = cursor.fetchone()
            if row:
                return row[0]
            return None


    def record_radar_signals(self, signals: list):
        import datetime
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        with self._get_conn() as conn:
            cursor = conn.cursor()
            for s in signals:
                cursor.execute('''
                    INSERT INTO radar_history (detected_at, symbol, name, signal_price, score, theme)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (now_str, s.get("symbol"), s.get("name", s.get("symbol")), s.get("price", 0.0), s.get("breakout_score", 0.0), s.get("theme", "")))
            conn.commit()

    def get_recent_radar_signals(self, limit=20):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT detected_at, symbol, name, signal_price, score, theme 
                FROM radar_history 
                ORDER BY detected_at DESC LIMIT ?
            ''', (limit,))
            rows = cursor.fetchall()
            res = []
            for r in rows:
                res.append({
                    "detected_at": r[0],
                    "symbol": r[1],
                    "name": r[2],
                    "signal_price": r[3],
                    "score": r[4],
                    "theme": r[5]
                })
            return res
    def get_snapshots(self, depot_id: str) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT snapshot_date, total_value, cash, invested_value, pnl, pnl_pct, num_positions
            FROM daily_snapshots
            WHERE depot_id = ?
            ORDER BY snapshot_date ASC
            """, (depot_id,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_trades(self, depot_id: str) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT id, depot_id, trade_type, symbol, name, shares, buy_price, sell_price, 
                   total_amount, pnl, pnl_pct, executed_at, reason
            FROM trades
            WHERE depot_id = ?
            ORDER BY id DESC
            """, (depot_id,))
            rows = cursor.fetchall()
            return [
                {
                    "id": r["id"],
                    "type": r["trade_type"],
                    "action": r["trade_type"],
                    "symbol": r["symbol"],
                    "name": r["name"],
                    "shares": r["shares"],
                    "price": r["buy_price"] if r["trade_type"] == "BUY" else r["sell_price"],
                    "buy_price": r["buy_price"],
                    "sell_price": r["sell_price"],
                    "total": r["total_amount"],
                    "pnl": r["pnl"],
                    "pnl_pct": r["pnl_pct"],
                    "date": r["executed_at"],
                    "reason": r["reason"]
                }
                for r in rows
            ]

    def record_hourly_snapshot(self, depot_id: str, total_value: float, cash: float, 
                               invested_value: float, pnl: float, pnl_pct: float, num_positions: int,
                               snapshot_time: Optional[str] = None):
        now_hour_str = snapshot_time or datetime.datetime.now().strftime("%Y-%m-%d %H:00")
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO hourly_snapshots (
                snapshot_time, depot_id, total_value, cash, invested_value, pnl, pnl_pct, num_positions
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(snapshot_time, depot_id) DO UPDATE SET
                total_value = excluded.total_value,
                cash = excluded.cash,
                invested_value = excluded.invested_value,
                pnl = excluded.pnl,
                pnl_pct = excluded.pnl_pct,
                num_positions = excluded.num_positions
            """, (now_hour_str, depot_id, total_value, cash, invested_value, pnl, pnl_pct, num_positions))
            conn.commit()

    def get_hourly_snapshots(self, depot_id: str) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT snapshot_time, total_value, cash, invested_value, pnl, pnl_pct, num_positions
            FROM hourly_snapshots
            WHERE depot_id = ?
            ORDER BY snapshot_time ASC
            """, (depot_id,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

