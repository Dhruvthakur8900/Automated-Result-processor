# pylint: disable=all
"""config.py – App constants, colours, page steps, and auto-installer."""

import sys, subprocess

# ── Auto-install missing packages ─────────────────────────────────────────
_PACKAGES = {
    "pandas":          "pandas",
    "mysql.connector": "mysql-connector-python",
    "openpyxl":        "openpyxl",
    "reportlab":       "reportlab",
}
for _imp, _pkg in _PACKAGES.items():
    try:
        __import__(_imp)
    except ImportError:
        print(f"[Setup] Installing {_pkg}…")
        ok = subprocess.call(
            [sys.executable, "-m", "pip", "install", _pkg, "-q"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0
        if not ok and _imp == "pandas":
            try:
                import tkinter as _tk, tkinter.messagebox as _mb
                _r = _tk.Tk(); _r.withdraw()
                _mb.showerror("Missing", f"Could not install '{_pkg}'.\nRun:  pip install {_pkg}")
                _r.destroy()
            except Exception: pass
            sys.exit(1)

# ── MySQL availability ────────────────────────────────────────────────────
try:
    import mysql.connector as _mc
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False

# ── App constants ─────────────────────────────────────────────────────────
APP_TITLE, APP_GEOMETRY, APP_MIN_SIZE = "Result Processing System", "1400x900", (1200, 700)
SQLITE_DB_FILE   = "result_processor.db"
DEFAULT_ADMIN    = ("admin", "admin123")
EXPECTED_SUBJECTS = 5

COLORS = {
    'sidebar': '#2C3E50', 'sidebar_active': '#34495E', 'sidebar_hover': '#3D566E',
    'primary': '#3498DB', 'success': '#27AE60', 'danger': '#E74C3C', 'warning': '#F39C12',
    'bg': '#ECF0F1', 'card': '#FFFFFF', 'text': '#2C3E50', 'text_light': '#7F8C8D', 'border': '#BDC3C7',
}

PAGES_CONFIG = [
    {'id': 'login',      'icon': '🔐', 'title': 'Login',             'locked': False},
    {'id': 'database',   'icon': '💾', 'title': 'Database Setup',    'locked': True},
    {'id': 'upload',     'icon': '📁', 'title': 'Upload Data',       'locked': True},
    {'id': 'validate',   'icon': '✓',  'title': 'Validate Data',     'locked': True},
    {'id': 'fix_errors', 'icon': '🔧', 'title': 'Fix Errors',        'locked': True},
    {'id': 'results',    'icon': '📊', 'title': 'Calculate Results', 'locked': True},
    {'id': 'pending',    'icon': '⏳', 'title': 'Pending Students',  'locked': True},
    {'id': 'reports',    'icon': '📄', 'title': 'Generate Reports',  'locked': True},
]
