import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = "data/subtotal.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS Users (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT    NOT NULL UNIQUE COLLATE NOCASE,
            password TEXT    NOT NULL
        );

        CREATE TABLE IF NOT EXISTS Subscriptions (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id       INTEGER NOT NULL,
            name          TEXT    NOT NULL,
            category      TEXT    NOT NULL DEFAULT 'Other',
            cost          REAL    NOT NULL,
            billing_cycle TEXT    NOT NULL DEFAULT 'Monthly',
            start_date    TEXT,
            notes         TEXT,
            FOREIGN KEY (user_id) REFERENCES Users(id)
        );
    """)
    conn.commit()

    # Safely add end_date if it doesn't exist yet (won't break existing databases)
    try:
        conn.execute("ALTER TABLE Subscriptions ADD COLUMN end_date TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass  # column already exists

    conn.close()


# ── Auth ──────────────────────────────────────────────────────────────────────

def register_user(username, password):
    if not username or not password:
        return False, "Username and password are required."
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO Users (username, password) VALUES (?, ?)",
            (username.strip(), generate_password_hash(password))
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return False, "Username already taken."
    conn.close()
    return True, None


def check_login(username, password):
    conn = get_db()
    user = conn.execute(
        "SELECT * FROM Users WHERE username = ? COLLATE NOCASE", (username,)
    ).fetchone()
    conn.close()
    if user and check_password_hash(user["password"], password):
        return dict(user)
    return None


# ── Subscriptions ─────────────────────────────────────────────────────────────

def get_subscriptions(user_id):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM Subscriptions WHERE user_id = ? ORDER BY name",
        (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_subscription(sub_id, user_id):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM Subscriptions WHERE id = ? AND user_id = ?",
        (sub_id, user_id)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def add_subscription(user_id, name, category, cost, billing_cycle,
                     start_date, end_date, notes):
    conn = get_db()
    conn.execute(
        """INSERT INTO Subscriptions
               (user_id, name, category, cost, billing_cycle, start_date, end_date, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (user_id, name.strip(), category, float(cost), billing_cycle,
         start_date.strip() or None,
         end_date.strip() or None,
         notes.strip() if notes else None)
    )
    conn.commit()
    conn.close()


def update_subscription(sub_id, user_id, name, category, cost, billing_cycle,
                         start_date, end_date, notes):
    conn = get_db()
    conn.execute(
        """UPDATE Subscriptions
           SET name=?, category=?, cost=?, billing_cycle=?,
               start_date=?, end_date=?, notes=?
           WHERE id=? AND user_id=?""",
        (name.strip(), category, float(cost), billing_cycle,
         start_date.strip() or None,
         end_date.strip() or None,
         notes.strip() if notes else None,
         sub_id, user_id)
    )
    conn.commit()
    conn.close()


def delete_subscription(sub_id, user_id):
    conn = get_db()
    conn.execute(
        "DELETE FROM Subscriptions WHERE id = ? AND user_id = ?",
        (sub_id, user_id)
    )
    conn.commit()
    conn.close()


# ── Calculations ──────────────────────────────────────────────────────────────

def to_monthly(cost, billing_cycle):
    cycle = billing_cycle.lower()
    if cycle == "weekly":
        return cost * 52 / 12
    elif cycle == "yearly":
        return cost / 12
    elif cycle == "quarterly":
        return cost / 3
    return cost  # monthly


def get_totals(user_id):
    subs = get_subscriptions(user_id)
    monthly = sum(to_monthly(s["cost"], s["billing_cycle"]) for s in subs)
    return {
        "monthly": round(monthly, 2),
        "yearly":  round(monthly * 12, 2),
        "count":   len(subs),
    }


def get_category_breakdown(user_id):
    subs = get_subscriptions(user_id)
    breakdown = {}
    for s in subs:
        cat = s["category"]
        breakdown[cat] = breakdown.get(cat, 0) + to_monthly(s["cost"], s["billing_cycle"])
    return {k: round(v, 2) for k, v in sorted(breakdown.items(), key=lambda x: -x[1])}
