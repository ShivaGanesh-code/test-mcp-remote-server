from fastmcp import FastMCP
import random
import json
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "expenses.db")
CATEGORIES_PATH = os.path.join(os.path.dirname(__file__), "categories.json")

mcp = FastMCP("Expense Tracker")

def init_db():  # Keep as sync for initialization
    try:
        with sqlite3.connect(DB_PATH) as c:
            #c.execute("PRAGMA journal_mode=WAL")
            c.execute("""
                CREATE TABLE IF NOT EXISTS expenses(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    amount REAL NOT NULL,
                    category TEXT NOT NULL,
                    subcategory TEXT DEFAULT '',
                    note TEXT DEFAULT ''
                )
            """)
            # Test write access
            c.execute("INSERT OR IGNORE INTO expenses(date, amount, category) VALUES ('2000-01-01', 0, 'test')")
            c.execute("DELETE FROM expenses WHERE category = 'test'")
            print("Database initialized successfully with write access")
    except Exception as e:
        print(f"Database initialization error: {e}")
        raise

# Initialize database synchronously at module load
init_db()


@mcp.tool()
def add_expense(date, amount, category, subcategory="", note=""):
    """Add a new expense entry to the database"""
    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute(
            "INSERT INTO expenses(date, amount, category, subcategory, note) VALUES(?,?,?,?,?)",
            (date, amount, category, subcategory, note)
        )
        return {"status": "ok", "id": cur.lastrowid}

@mcp.tool()
def list_expenses(start_date, end_date):
    """List expense entries within an inclusive date range"""
    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute(
            """SELECT id, date, amount, category, subcategory, note" \
            FROM expenses
            WHERE date BETWEEN ? AND ?
            ORDER BY id asc 
            """,
            (start_date, end_date)
        )
        cols = [d[0] for d in cur.description]

        return [dict(zip(cols, r)) for r in cur.fetchall()]
    

@mcp.tool()
def summarization(start_date, end_date, category=None):
    '''Summarize expenses by category within an inclusive date range'''
    with sqlite3.connect(DB_PATH) as c:
        query = (
            """
            SELECT category, SUM(amount) AS total_amount
            FROM expenses
            WHERE date BETWEEN ? AND ?
            """
        )
        params = [start_date, end_date]

        if category:
            query += " AND category = ?"
            params.append(category)
        
        query += " GROUP BY category ORDER BY category ASC"

        cur = c.execute(query, params)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]


@mcp.resource("expense://categories", mime_type="application/json")
def categories():
    """Read fresh each time so you can edit the file without restarting"""
    with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
        return f.read()
    
if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8000)