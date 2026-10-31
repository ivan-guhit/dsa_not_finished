import os
import sqlite3
from datetime import date, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "inventory.db")
COLUMNS = ("sku", "name", "category", "price", "quantity", "expiry")


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _conn() as c:
        c.execute(
            """CREATE TABLE IF NOT EXISTS products (
                sku TEXT PRIMARY KEY, name TEXT NOT NULL, category TEXT NOT NULL,
                price REAL NOT NULL, quantity INTEGER NOT NULL, expiry TEXT)"""
        )
        c.execute(
            """CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT, sku TEXT NOT NULL, name TEXT NOT NULL,
                quantity INTEGER NOT NULL, unit_price REAL NOT NULL, total REAL NOT NULL,
                sold_at TEXT NOT NULL)"""
        )
        if c.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 0:
            today = date.today()
            seed = [
                ("NDL-001", "Lucky Me Pancit Canton", "Noodles", 16.0, 40, 120),
                ("NDL-002", "NIssin Cup Noodles", "Noodles", 9.5, 25, 90),
                ("CND-001", "San Marino Tuna", "Canned Goods", 38.0, 18, 400),
                ("CND-002", "Ligo Sardines", "Canned Goods", 24.0, 30, 300),
                ("DRK-001", "Coke", "Drinks", 15.0, 48, 60),
                ("DRK-002", "Milo", "Drinks", 8.0, 60, 150),
                ("SNK-001", "Piattos yung kulay Blue", "Snacks", 20.0, 22, 45),
                ("SNK-002", "Skyflakes Pack", "Snacks", 7.0, 35, 8),
                ("DAI-001", "Alaska", "Dairy", 12.0, 14, 3),
                ("EGG-001", "Eggs", "Fresh", 11.0, 90, 5),
                ("BRD-001", "Pandesal ni Jezar", "Fresh", 25.0, 10, -1),
                ("CON-001", "Papa Kitsup", "Condiments", 22.0, 16, 500),
                ("CON-002", "Silver Swan Soy Sauce", "Condiments", 21.0, 12, 450),
                ("HOM-001", "Safeguard", "Household", 42.0, 9, None),
                ("HOM-002", "Tide Bar", "Household", 6.5, 70, None),
            ]
            for sku, name, cat, price, qty, days in seed:
                exp = (today + timedelta(days=days)).isoformat() if days is not None else None
                c.execute("INSERT INTO products VALUES (?,?,?,?,?,?)", (sku, name, cat, price, qty, exp))


def fetch_all():
    with _conn() as c:
        return [dict(r) for r in c.execute("SELECT * FROM products")]


def insert(p):
    with _conn() as c:
        c.execute("INSERT INTO products VALUES (?,?,?,?,?,?)", tuple(p[k] for k in COLUMNS))


def update(p):
    with _conn() as c:
        c.execute(
            "UPDATE products SET name=?, category=?, price=?, quantity=?, expiry=? WHERE sku=?",
            (p["name"], p["category"], p["price"], p["quantity"], p["expiry"], p["sku"]),
        )


def delete(sku):
    with _conn() as c:
        c.execute("DELETE FROM products WHERE sku=?", (sku,))


def fetch_sales():
    with _conn() as c:
        return [dict(r) for r in c.execute("SELECT * FROM sales ORDER BY id")]


def record_sale(sku, new_quantity, sale):
    with _conn() as c:
        c.execute("UPDATE products SET quantity=? WHERE sku=?", (new_quantity, sku))
        cur = c.execute(
            "INSERT INTO sales (sku, name, quantity, unit_price, total, sold_at) VALUES (?,?,?,?,?,?)",
            (sale["sku"], sale["name"], sale["quantity"], sale["unit_price"], sale["total"], sale["sold_at"]),
        )
        return cur.lastrowid


def void_sale(sale_id, sku, restored_quantity):
    with _conn() as c:
        if restored_quantity is not None:
            c.execute("UPDATE products SET quantity=? WHERE sku=?", (restored_quantity, sku))
        c.execute("DELETE FROM sales WHERE id=?", (sale_id,))
