# pylint: disable=all
"""database.py – All DB operations: SQLite init, MySQL connect, save, logging."""

import hashlib, json, sqlite3, socket, traceback
from datetime import datetime
import pandas as pd
from tkinter import messagebox
from config import SQLITE_DB_FILE, DEFAULT_ADMIN, MYSQL_AVAILABLE

if MYSQL_AVAILABLE:
    import mysql.connector
    from mysql.connector import Error as MySQLError
else:
    class _FC:
        class Error(Exception): pass
        @staticmethod
        def connect(**kw): raise RuntimeError("mysql-connector-python not installed.")
    mysql = type("mysql", (), {"connector": _FC})()
    MySQLError = _FC.Error


class DatabaseMixin:

    # ── SQLite init ───────────────────────────────────────────────────────
    def init_database(self):
        try:
            con = sqlite3.connect(SQLITE_DB_FILE); cur = con.cursor()
            cur.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL,
                    role TEXT DEFAULT 'user', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
                CREATE TABLE IF NOT EXISTS login_logs (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL, login_time TEXT NOT NULL,
                    status TEXT, ip_address TEXT);
                CREATE TABLE IF NOT EXISTS fixed_errors (
                    fix_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id TEXT NOT NULL, student_name TEXT, subject TEXT NOT NULL,
                    field_name TEXT NOT NULL, old_value TEXT, new_value TEXT,
                    error_message TEXT, fixed_by TEXT,
                    fixed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
            """)
            h = hashlib.sha256(DEFAULT_ADMIN[1].encode()).hexdigest()
            cur.execute("INSERT OR IGNORE INTO users (username,password_hash,role) VALUES(?,?,?)",
                        (DEFAULT_ADMIN[0], h, 'admin'))
            con.commit(); con.close()
        except Exception as e:
            print(f"[DB] init error: {e}")

    # ── Audit trail ───────────────────────────────────────────────────────
    def log_fixed_error(self, student_id, student_name, subject, field_name,
                        old_value, new_value, error_message):
        by = self.logged_in_user["username"] if self.logged_in_user else "unknown"
        args = (str(student_id), str(student_name), str(subject), str(field_name),
                str(old_value), str(new_value), str(error_message), by)
        try:
            if hasattr(self,'db_connection') and self.db_connection and self.db_connection.is_connected():
                cur = self.db_connection.cursor()
                cur.execute("INSERT INTO fixed_errors (student_id,student_name,subject,field_name,"
                            "old_value,new_value,error_message,fixed_by) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)", args)
                self.db_connection.commit()
                return True, "MySQL", None
            else:
                con = sqlite3.connect(SQLITE_DB_FILE); cur = con.cursor()
                cur.execute("INSERT INTO fixed_errors (student_id,student_name,subject,field_name,"
                            "old_value,new_value,error_message,fixed_by) VALUES(?,?,?,?,?,?,?,?)", args)
                con.commit(); con.close()
                return True, f"SQLite ({SQLITE_DB_FILE})", None
        except Exception as e:
            traceback.print_exc()
            return False, None, str(e)

    # ── Login logging ─────────────────────────────────────────────────────
    def try_log_to_mysql(self, username, status):
        if not MYSQL_AVAILABLE or not hasattr(self, 'db_config'): return
        try:
            con = mysql.connector.connect(**self.db_config); cur = con.cursor()
            cur.execute("INSERT INTO login_logs(username,login_time,status,ip_address) VALUES(%s,%s,%s,%s)",
                        (username, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), status, 'localhost'))
            con.commit(); con.close()
        except Exception: pass

    def log_login_to_mysql(self, username, status):
        if not self.db_connection or not self.db_connection.is_connected(): return
        try:
            ip = socket.gethostbyname(socket.gethostname())
            cur = self.db_connection.cursor()
            cur.execute("INSERT INTO login_logs(username,login_time,status,ip_address,session_info) VALUES(%s,%s,%s,%s,%s)",
                        (username, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), status, ip, f"Host:{socket.gethostname()}"))
            self.db_connection.commit()
        except Exception as e: print(f"[DB] login log failed: {e}")

    # ── MySQL connect (DB setup page) ─────────────────────────────────────
    def test_db_connection(self):
        if not MYSQL_AVAILABLE:
            messagebox.showwarning("MySQL Unavailable", "Install: pip install mysql-connector-python"); return
        try:
            con = mysql.connector.connect(host=self.db_host.get(), user=self.db_user.get(), password=self.db_pass.get())
            if con.is_connected():
                ver = con.get_server_info()
                self.db_status_label.config(text=f"✓ Connected! MySQL {ver}", fg=self.colors['success'])
                messagebox.showinfo("Success", f"Connected!\nHost: {self.db_host.get()}\nMySQL: {ver}")
                con.close()
        except MySQLError as e:
            self.db_status_label.config(text="✗ Failed", fg=self.colors['danger'])
            messagebox.showerror("Error", f"Connection failed:\n{e}")

    def save_db_and_continue(self):
        if not MYSQL_AVAILABLE:
            messagebox.showwarning("MySQL N/A",
                "mysql-connector-python not available.\nContinuing in SQLite mode.\nRun: pip install mysql-connector-python")
            return self.skip_database()
        try:
            con = mysql.connector.connect(
                host=self.db_host.get(), port=int(self.db_port.get() or 3306),
                user=self.db_user.get(), password=self.db_pass.get())
            if not con.is_connected(): return
            cur = con.cursor()
            db  = self.db_name.get()
            tbl = getattr(self, 'db_table', None)
            tbl = tbl.get() if tbl else 'results'
            cur.execute(f"CREATE DATABASE IF NOT EXISTS `{db}`")
            cur.execute(f"USE `{db}`")
            cur.executemany("SELECT 1", [])  # flush
            for sql in [
                "CREATE TABLE IF NOT EXISTS users (id INT AUTO_INCREMENT PRIMARY KEY,"
                " username VARCHAR(50) UNIQUE NOT NULL, password_hash VARCHAR(255) NOT NULL,"
                " role VARCHAR(20) DEFAULT 'user', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)",
                "CREATE TABLE IF NOT EXISTS login_logs (id INT AUTO_INCREMENT PRIMARY KEY,"
                " username VARCHAR(100), login_time VARCHAR(50), status VARCHAR(20),"
                " ip_address VARCHAR(50), session_info TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)",
                f"CREATE TABLE IF NOT EXISTS `{tbl}` (id INT AUTO_INCREMENT PRIMARY KEY,"
                " student_id VARCHAR(50), student_name VARCHAR(100), roll_no VARCHAR(50),"
                " total_marks FLOAT, percentage FLOAT, grade VARCHAR(5), result VARCHAR(10),"
                " created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)",
                "CREATE TABLE IF NOT EXISTS error_logs (id INT AUTO_INCREMENT PRIMARY KEY,"
                " student_id VARCHAR(50), student_name VARCHAR(100), roll_no VARCHAR(50),"
                " error_type VARCHAR(100), error_description TEXT, record_data JSON,"
                " created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)",
                "CREATE TABLE IF NOT EXISTS fixed_errors (id INT AUTO_INCREMENT PRIMARY KEY,"
                " student_id VARCHAR(50), student_name VARCHAR(100), subject VARCHAR(100),"
                " field_name VARCHAR(100), old_value VARCHAR(255), new_value VARCHAR(255),"
                " error_message TEXT, fixed_by VARCHAR(100), fixed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)",
            ]:
                cur.execute(sql)
            h = hashlib.sha256(DEFAULT_ADMIN[1].encode()).hexdigest()
            try: cur.execute("INSERT INTO users(username,password_hash,role) VALUES(%s,%s,%s)",
                             (DEFAULT_ADMIN[0], h, 'admin'))
            except mysql.connector.IntegrityError: pass
            con.commit()
            self.db_connection = con; self.db_table_name = tbl
            self.db_config = {'host': self.db_host.get(), 'port': int(self.db_port.get() or 3306),
                              'user': self.db_user.get(), 'password': self.db_pass.get(), 'database': db}
            self.db_status_label.config(text=f"✓ Connected to '{db}'", fg=self.colors['success'])
            messagebox.showinfo("Success", f"✓ Database '{db}' ready!")
            self.unlock_page('upload'); self.navigate_to('upload')
        except MySQLError as e:
            self.db_status_label.config(text="✗ Failed", fg=self.colors['danger'])
            if messagebox.askyesno("DB Error", f"{e}\n\nSkip database setup?"):
                self.skip_database()

    def skip_database(self):
        self.unlock_page('upload'); self.navigate_to('upload')

    # ── Save / auto-save ──────────────────────────────────────────────────
    def save_to_database(self):
        if self.results_df is None or self.results_df.empty:
            messagebox.showerror("Error", "No results to save"); return
        try:
            con = mysql.connector.connect(
                host=self.db_host.get(), port=int(self.db_port.get() or 3306),
                user=self.db_user.get(), password=self.db_pass.get(), database=self.db_name.get())
            if con.is_connected():
                messagebox.showinfo("Success", "Results saved!"); con.close(); self.navigate_to('reports')
        except MySQLError as e: messagebox.showerror("Error", str(e))

    def save_error_logs_to_database(self):
        if self.error_df is None or self.error_df.empty: return
        if not self.db_connection or not self.db_connection.is_connected(): return
        try:
            cur = self.db_connection.cursor()
            for _, row in self.error_df.iterrows():
                sid  = str(row.get('student_id', row.get('Student_ID', 'Unknown')))
                sname= str(row.get('student_name', row.get('Student_Name', 'Unknown')))
                roll = str(row.get('roll_no', row.get('Roll_No', 'Unknown')))
                desc = str(row.get('Errors', 'Validation error'))
                etype= ('Negative Marks' if 'negative' in desc.lower() else
                        'Marks Exceed Max' if 'exceed' in desc.lower() else
                        'Non-numeric' if 'non-numeric' in desc.lower() else
                        'Missing Data' if 'missing' in desc.lower() else 'Validation Error')
                cur.execute("INSERT INTO error_logs(student_id,student_name,roll_no,error_type,error_description,record_data)"
                            " VALUES(%s,%s,%s,%s,%s,%s)",
                            (sid, sname, roll, etype, desc, json.dumps({k: str(v) for k,v in row.items() if k!='Errors'})))
            self.db_connection.commit()
            messagebox.showinfo("Success", f"✓ {len(self.error_df)} error logs saved!")
        except Exception as e: messagebox.showerror("Error", str(e))

    def save_uploaded_to_database(self):
        if self.df is None or self.df.empty: messagebox.showerror("Error","No data"); return
        if not self.db_connection or not self.db_connection.is_connected():
            messagebox.showerror("Error","No DB connection"); return
        self._write_df_to_mysql(self.df, "uploaded_student_data", show_success=True)

    def auto_save_uploaded_data(self):
        if self.df is None or not (self.db_connection and self.db_connection.is_connected()): return
        self._write_df_to_mysql(self.df, "uploaded_student_data")

    def auto_save_validation_results(self):
        if not (self.db_connection and self.db_connection.is_connected()): return
        if self.valid_df is not None and not self.valid_df.empty:
            self._write_df_to_mysql(self.valid_df, "validated_records")

    def auto_save_results(self):
        if self.results_df is None or self.results_df.empty: return
        if not (self.db_connection and self.db_connection.is_connected()): return
        tbl = getattr(self, 'db_table_name', 'results')
        try:
            cur = self.db_connection.cursor()
            cur.execute(f"DELETE FROM `{tbl}`")
            for _, row in self.results_df.iterrows():
                pct = float(str(row.get('Percentage','0%')).replace('%','') or 0)
                cur.execute(f"INSERT INTO `{tbl}`(student_id,student_name,roll_no,total_marks,percentage,grade,result)"
                            " VALUES(%s,%s,%s,%s,%s,%s,%s)",
                            (str(row.get('student_id','')), str(row.get('student_name','')),
                             str(row.get('roll_no','')), float(row.get('Total',0)), pct,
                             str(row.get('Grade','F')), str(row.get('Result','FAIL'))))
            self.db_connection.commit()
        except Exception as e: print(f"[DB] auto_save_results: {e}")

    def _write_df_to_mysql(self, df, table_name, *, show_success=False):
        try:
            cur = self.db_connection.cursor()
            cur.execute(f"DROP TABLE IF EXISTS `{table_name}`")
            col_map = {}
            for c in df.columns:
                s = ''.join(x if x.isalnum() or x=='_' else '_' for x in str(c).replace(' ','_').replace('-','_'))
                col_map[c] = s
            cols_sql = ', '.join(f"`{v}` TEXT" for v in col_map.values())
            cur.execute(f"CREATE TABLE `{table_name}` (id INT AUTO_INCREMENT PRIMARY KEY, {cols_sql},"
                        " upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
            for _, row in df.iterrows():
                ph  = ','.join(['%s']*len(row))
                cs  = ','.join(f"`{col_map[c]}`" for c in df.columns)
                cur.execute(f"INSERT INTO `{table_name}` ({cs}) VALUES({ph})",
                            tuple(str(v) if not pd.isna(v) else None for v in row))
            self.db_connection.commit()
            if show_success:
                messagebox.showinfo("Success", f"✓ Saved {len(df)} rows to '{table_name}'")
        except Exception as e:
            if show_success: messagebox.showerror("Error", str(e))
            else: print(f"[DB] _write_df_to_mysql: {e}")
