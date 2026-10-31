"""
Generate a sample SQLite database (sample.db) with realistic data for testing
the SQL Generator app.
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "sample.db")


def create_sample_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # ── Departments ──
    c.execute("""
        CREATE TABLE IF NOT EXISTS departments (
            id          INTEGER PRIMARY KEY,
            name        TEXT    NOT NULL UNIQUE,
            budget      REAL    NOT NULL,
            location    TEXT
        )
    """)

    departments = [
        (1, "Engineering",  2500000, "San Francisco"),
        (2, "Marketing",    1200000, "New York"),
        (3, "Sales",         900000, "Chicago"),
        (4, "HR",            600000, "San Francisco"),
        (5, "Finance",       800000, "New York"),
        (6, "Design",        700000, "Los Angeles"),
    ]
    c.executemany("INSERT OR IGNORE INTO departments VALUES (?,?,?,?)", departments)

    # ── Employees ──
    c.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id              INTEGER PRIMARY KEY,
            first_name      TEXT    NOT NULL,
            last_name       TEXT    NOT NULL,
            email           TEXT    UNIQUE,
            department_id   INTEGER REFERENCES departments(id),
            title           TEXT,
            salary          REAL,
            hire_date       TEXT,
            is_active       INTEGER DEFAULT 1
        )
    """)

    employees = [
        (1,  "Alice",   "Chen",     "alice.chen@co.io",     1, "Senior Engineer",       145000, "2021-03-15", 1),
        (2,  "Bob",     "Smith",    "bob.smith@co.io",      1, "Staff Engineer",        175000, "2019-07-22", 1),
        (3,  "Carol",   "Davis",    "carol.davis@co.io",    2, "Marketing Manager",     110000, "2020-01-10", 1),
        (4,  "Dan",     "Lee",      "dan.lee@co.io",        3, "Sales Lead",            105000, "2022-06-01", 1),
        (5,  "Eve",     "Garcia",   "eve.garcia@co.io",     1, "Engineering Manager",   160000, "2018-11-30", 1),
        (6,  "Frank",   "Wilson",   "frank.wilson@co.io",   4, "HR Specialist",          85000, "2023-02-14", 1),
        (7,  "Grace",   "Nguyen",   "grace.nguyen@co.io",   5, "Financial Analyst",      95000, "2021-09-05", 1),
        (8,  "Hank",    "Miller",   "hank.miller@co.io",    6, "UI Designer",           100000, "2022-04-18", 1),
        (9,  "Ivy",     "Brown",    "ivy.brown@co.io",      1, "Junior Engineer",        95000, "2024-01-08", 1),
        (10, "Jake",    "Taylor",   "jake.taylor@co.io",    2, "Content Strategist",     90000, "2023-08-20", 1),
        (11, "Karen",   "Anderson", "karen.anderson@co.io", 3, "Account Executive",     100000, "2020-05-12", 0),
        (12, "Leo",     "Thomas",   "leo.thomas@co.io",     5, "Senior Accountant",     115000, "2019-12-01", 1),
        (13, "Mia",     "Jackson",  "mia.jackson@co.io",    6, "UX Researcher",          92000, "2023-06-15", 1),
        (14, "Noah",    "White",    "noah.white@co.io",     1, "DevOps Engineer",       135000, "2021-11-03", 1),
        (15, "Olivia",  "Harris",   "olivia.harris@co.io",  4, "HR Manager",            120000, "2017-08-25", 1),
    ]
    c.executemany("INSERT OR IGNORE INTO employees VALUES (?,?,?,?,?,?,?,?,?)", employees)

    # ── Projects ──
    c.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id              INTEGER PRIMARY KEY,
            name            TEXT    NOT NULL,
            department_id   INTEGER REFERENCES departments(id),
            lead_id         INTEGER REFERENCES employees(id),
            status          TEXT    CHECK(status IN ('active','completed','on_hold')),
            start_date      TEXT,
            end_date        TEXT,
            budget          REAL
        )
    """)

    projects = [
        (1, "Cloud Migration",    1, 5,  "active",    "2024-01-15", None,         500000),
        (2, "Brand Refresh",      2, 3,  "completed", "2023-06-01", "2024-03-30", 150000),
        (3, "CRM Overhaul",       3, 4,  "active",    "2024-04-01", None,         200000),
        (4, "Mobile App v2",      1, 2,  "active",    "2024-07-01", None,         350000),
        (5, "Compliance Audit",   5, 12, "on_hold",   "2024-09-01", None,          75000),
        (6, "Design System",      6, 8,  "active",    "2024-03-15", None,         120000),
    ]
    c.executemany("INSERT OR IGNORE INTO projects VALUES (?,?,?,?,?,?,?,?)", projects)

    conn.commit()
    conn.close()
    print(f"Sample database created at: {DB_PATH}")


if __name__ == "__main__":
    create_sample_db()
