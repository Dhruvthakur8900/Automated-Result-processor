# pylint: disable=all
"""gui_pages.py – All page renderers: login, database, upload, validate, fix errors, pending, results, reports, history."""

import hashlib, os, sqlite3, traceback
from datetime import datetime
import pandas as pd
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from config import SQLITE_DB_FILE


def _lbl(parent, text, font=None, bg=None, fg=None, **kw):
    return tk.Label(parent, text=text, font=font or ('Segoe UI',11),
                    bg=bg, fg=fg, **kw)


class GUIPagesMixin:

    # ── LOGIN ─────────────────────────────────────────────────────────────
    def show_login_page(self):
        self.create_page_header("Welcome Back", "Please login to continue")
        card = self.create_card(self.content_area)
        frm  = tk.Frame(card, bg=self.colors['card'])
        frm.place(relx=.5, rely=.5, anchor='center')
        for lbl, attr, kw in [("Username",'username_entry',{}), ("Password",'password_entry',{'show':'●'})]:
            _lbl(frm, lbl, bg=self.colors['card'], fg=self.colors['text']).pack(anchor='w', pady=(0,5))
            e = tk.Entry(frm, font=('Segoe UI',12), width=30, relief='solid', bd=1, **kw)
            e.pack(pady=(0,20)); setattr(self, attr, e)
        self.create_button(frm, "Login", self.handle_login, width=30).pack()
        self.password_entry.bind('<Return>', lambda _: self.handle_login())
        _lbl(frm, "Default: admin / admin123", ('Segoe UI',9),
             bg=self.colors['card'], fg=self.colors['text_light']).pack(pady=(20,0))

    def handle_login(self):
        u, p = self.username_entry.get().strip(), self.password_entry.get()
        if not u or not p: messagebox.showerror("Error","Enter username and password"); return
        h = hashlib.sha256(p.encode()).hexdigest()
        try:
            con = sqlite3.connect(SQLITE_DB_FILE); cur = con.cursor()
            cur.execute("SELECT user_id,username,role FROM users WHERE username=? AND password_hash=?", (u,h))
            user = cur.fetchone()
            ts   = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cur.execute("INSERT INTO login_logs(username,login_time,status,ip_address) VALUES(?,?,?,?)",
                        (u, ts, 'SUCCESS' if user else 'FAILED', 'localhost'))
            con.commit(); con.close()
            if user:
                self.logged_in_user = {'user_id':user[0],'username':user[1],'role':user[2],'login_time':datetime.now()}
                self.try_log_to_mysql(u,'SUCCESS')
                self._ensure_sidebar_visible()
                messagebox.showinfo("Success", f"Welcome, {u}!")
                self.unlock_page('database'); self.navigate_to('database')
            else:
                self.try_log_to_mysql(u,'FAILED')
                messagebox.showerror("Error","Invalid username or password")
        except Exception as e: messagebox.showerror("Error", str(e))

    # ── DATABASE SETUP ────────────────────────────────────────────────────
    def show_database_page(self):
        self.create_page_header("Database Setup","Configure MySQL connection (Optional)")
        card = self.create_card(self.content_area)
        info = tk.Frame(card, bg='#E3F2FD', relief='solid', bd=1)
        info.pack(fill='x', padx=50, pady=(20,30))
        _lbl(info, "ℹ️  Database is optional – skip to use SQLite only.",
             bg='#E3F2FD', fg=self.colors['text'], wraplength=700, justify='left').pack(padx=20, pady=15)
        frm = tk.Frame(card, bg=self.colors['card'])
        frm.pack(padx=50, pady=20, fill='both', expand=True)
        fields = [(0,0,"Host:",'db_host',"localhost",30),(0,2,"Port:",'db_port',"3306",15),
                  (1,0,"Username:",'db_user',"root",30),(1,2,"Password:",'db_pass',"",15),
                  (2,0,"Database:",'db_name',"student_results",30),(2,2,"Table:",'db_table',"results",15)]
        for row,col,lbl,attr,default,width in fields:
            _lbl(frm, lbl, bg=self.colors['card']).grid(row=row,column=col,sticky='e',pady=10,padx=(0 if col==0 else 20,20))
            e = tk.Entry(frm, font=('Segoe UI',11), width=width, show='●' if attr=='db_pass' else '')
            if default: e.insert(0, default)
            e.grid(row=row, column=col+1, pady=10, sticky='w'); setattr(self, attr, e)
        self.db_status_label = tk.Label(frm, text="", font=('Segoe UI',10), bg=self.colors['card'])
        self.db_status_label.grid(row=3, column=0, columnspan=4, pady=10)
        btn_row = tk.Frame(card, bg=self.colors['card']); btn_row.pack(pady=30)
        for txt,cmd,sty in [("Test Connection",self.test_db_connection,'primary'),
                             ("Save & Continue",self.save_db_and_continue,'success'),("Skip",self.skip_database,'warning')]:
            self.create_button(btn_row, txt, cmd, style=sty, width=18).pack(side='left', padx=10)

    # ── UPLOAD ────────────────────────────────────────────────────────────
    def show_upload_page(self):
        self.create_page_header("Upload Data","Upload your CSV or Excel file")
        card = self.create_card(self.content_area, pady=10)
        con  = tk.Frame(card, bg=self.colors['card']); con.pack(fill='x', padx=20, pady=10)

        self.drop_zone = tk.Frame(con, bg='#F8F9FA', relief='solid', bd=2,
                                  highlightbackground=self.colors['primary'], highlightthickness=2, height=180)
        self.drop_zone.pack(fill='x'); self.drop_zone.pack_propagate(False)
        for txt, font in [("📁",('Segoe UI',60)), ("Click to browse or drag & drop",('Segoe UI',12)),
                          ("Supported: CSV, XLSX, XLS",('Segoe UI',9))]:
            _lbl(self.drop_zone, txt, font, bg='#F8F9FA', fg=self.colors['primary' if '📁' in txt else 'text']).pack(pady=5)
        self.drop_zone.bind('<Button-1>', lambda _: self.browse_file())

        btn_row = tk.Frame(con, bg=self.colors['card']); btn_row.pack(pady=15)
        self.create_button(btn_row,"Browse Files",self.browse_file,width=20).pack(side='left',padx=5)
        self.save_to_db_btn = self.create_button(btn_row,"Save to DB",self.save_uploaded_to_database,'success',20)
        self.save_to_db_btn.pack(side='left',padx=5); self.save_to_db_btn.config(state='disabled')
        self.upload_continue_btn = self.create_button(btn_row,"Continue →",lambda:self.navigate_to('validate'),'warning',20)
        self.upload_continue_btn.pack(side='left',padx=5); self.upload_continue_btn.config(state='disabled')
        self.file_info_label = tk.Label(con,text="",font=('Segoe UI',11),bg=self.colors['card'],fg=self.colors['success'])
        self.file_info_label.pack(pady=5)
        self.upload_preview_frame = tk.Frame(card, bg=self.colors['card'])
        self.upload_preview_frame.pack(fill='both', expand=True, padx=20, pady=10)

    def browse_file(self):
        path = filedialog.askopenfilename(filetypes=[("CSV","*.csv"),("Excel","*.xlsx *.xls"),("All","*.*")])
        if not path: return
        try:
            self.df = pd.read_csv(path) if path.endswith('.csv') else pd.read_excel(path)
            self.file_info_label.config(text=f"✓ {os.path.basename(path)} ({len(self.df)} rows)")
            self.unlock_page('validate')
            if hasattr(self,'upload_continue_btn'): self.upload_continue_btn.config(state='normal')
            if hasattr(self,'save_to_db_btn') and self.db_connection and self.db_connection.is_connected():
                self.save_to_db_btn.config(state='normal'); self.auto_save_uploaded_data()
            self.show_file_preview()
        except Exception as e: messagebox.showerror("Error", str(e))

    def show_file_preview(self):
        if self.df is None or self.df.empty: return
        for w in self.upload_preview_frame.winfo_children(): w.destroy()
        try:   pdf = self.transform_to_student_rows(self.df)
        except: pdf = self.df.head(1000)
        hdr = tk.Frame(self.upload_preview_frame, bg='#E8F5E9', relief='solid', bd=1)
        hdr.pack(fill='x', pady=(10,0))
        _lbl(hdr, f"📄 Preview – {len(pdf):,} students", ('Segoe UI',12,'bold'),
             bg='#E8F5E9', fg=self.colors['success']).pack(pady=10)
        self._make_tree_frame(self.upload_preview_frame, pdf.head(100))

    def _make_tree_frame(self, parent, df):
        frm = tk.Frame(parent); frm.pack(fill='both', expand=True, pady=(5,0))
        ys  = tk.Scrollbar(frm); ys.pack(side='right',fill='y')
        xs  = tk.Scrollbar(frm,orient='horizontal'); xs.pack(side='bottom',fill='x')
        tree = ttk.Treeview(frm, yscrollcommand=ys.set, xscrollcommand=xs.set, selectmode='browse', height=18)
        tree.pack(fill='both', expand=True)
        ys.config(command=tree.yview); xs.config(command=tree.xview)
        tree['columns'] = list(df.columns); tree['show'] = 'headings'
        for col in df.columns: tree.heading(col,text=col); tree.column(col,width=120,anchor='center')
        tree.tag_configure('evenrow',background='#F5F5F5'); tree.tag_configure('oddrow',background='#FFFFFF')
        for i,v in enumerate(df.values.tolist()):
            tree.insert('','end',values=v,tags=('evenrow' if i%2==0 else 'oddrow',))
            if i%25==0: self.root.update_idletasks()

    # ── VALIDATE ──────────────────────────────────────────────────────────
    def show_validate_page(self):
        self.create_page_header("Validate Data","Review and validate uploaded data")
        if self.df is None:
            _lbl(self.create_card(self.content_area),"⚠️ No data – upload a file first.",
                 fg=self.colors['warning']).pack(pady=100); return
        card = self.create_card(self.content_area, pady=10)
        ctrl = tk.Frame(card, bg=self.colors['card']); ctrl.pack(fill='x',padx=20,pady=20)
        self.create_button(ctrl,"▶ Run Validation",self.run_validation,width=20).pack(side='left',padx=5)
        self.fix_errors_btn = self.create_button(ctrl,"🔧 Fix Errors →",lambda:self.navigate_to('fix_errors'),'warning',20)
        self.fix_errors_btn.pack(side='left',padx=5); self.fix_errors_btn.config(state='disabled')
        self.continue_btn = self.create_button(ctrl,"Continue to Results →",lambda:self.navigate_to('results'),'success',20)
        self.continue_btn.pack(side='left',padx=5); self.continue_btn.config(state='disabled')
        self.validation_summary_frame = tk.Frame(card, bg=self.colors['card'])
        self.validation_summary_frame.pack(fill='x',padx=20,pady=(0,10))
        nb = ttk.Notebook(card); nb.pack(fill='both',expand=True,padx=20,pady=(0,20))
        self.validation_notebook = nb
        for title, attr in [("✓ Valid Records",'valid_tree'),("✗ Error Records",'error_tree')]:
            frm = tk.Frame(nb, bg='white'); nb.add(frm,text=title)
            setattr(self, attr, self.create_treeview(frm))

    def show_validation_summary(self, valid_count, error_count):
        for w in self.validation_summary_frame.winfo_children(): w.destroy()
        bg   = '#E8F5E9' if error_count==0 else '#FFF3E0'
        card = tk.Frame(self.validation_summary_frame,bg=bg,relief='solid',bd=1,height=80)
        card.pack(fill='x'); card.pack_propagate(False)
        row  = tk.Frame(card,bg=bg); row.pack(expand=True)
        for txt,color,size in [
            ("✓ Complete  •  ", self.colors['success' if error_count==0 else 'warning'], 12),
            (f"{valid_count:,}", self.colors['success'], 16),
            (" Valid  |  ", self.colors['text_light'], 10),
            (f"{error_count:,}", self.colors['danger'], 16),
            (" Errors", self.colors['text_light'], 10)]:
            tk.Label(row,text=txt,font=('Segoe UI',size),bg=bg,fg=color).pack(side='left',padx=2)

    # ── FIX ERRORS ────────────────────────────────────────────────────────
    def show_fix_errors_page(self):
        self.create_page_header("Fix Errors","Correct error records and add late submissions")
        card = self.create_card(self.content_area, pady=10)
        if self.error_df is None or self.error_df.empty:
            _lbl(card,"✓ No errors to fix!",fg=self.colors['success']).pack(pady=100); return
        ctrl = tk.Frame(card, bg=self.colors['card']); ctrl.pack(fill='x',padx=20,pady=15)
        _lbl(ctrl,f"📝 {len(self.error_df)} errors",('Segoe UI',12,'bold'),
             bg=self.colors['card'],fg=self.colors['danger']).pack(side='left',padx=10)
        for txt,cmd,sty in [("🔄 Re-validate",self.revalidate_after_fixes,'warning'),
                             ("➕ Add Late",self.add_late_submission,'success'),
                             ("🔧 Fix Selected",self.fix_selected_error,'primary')]:
            self.create_button(ctrl,txt,cmd,style=sty,width=16).pack(side='right',padx=5)
        self.fix_errors_tree = self.create_treeview(card)
        self.populate_treeview(self.fix_errors_tree, self.error_df)
        self.fix_errors_tree.bind('<Double-Button-1>', lambda _: self.fix_selected_error())

    def fix_selected_error(self):
        if not hasattr(self,'fix_errors_tree'): return
        sel = self.fix_errors_tree.selection()
        if not sel: messagebox.showwarning("No Selection","Select a record to fix"); return
        self.show_edit_dialog(self.fix_errors_tree.item(sel[0],'values'), list(self.error_df.columns), sel[0])

    def show_edit_dialog(self, values, columns, tree_item):
        dlg = tk.Toplevel(self.root); dlg.title("Fix Error Record"); dlg.geometry("650x450")
        dlg.configure(bg=self.colors['bg'])
        tk.Frame(dlg,bg=self.colors['primary']).pack(fill='x')
        _lbl(dlg.winfo_children()[-1],"🔧 Edit Record",('Segoe UI',16,'bold'),
             bg=self.colors['primary'],fg='white').pack(pady=15)
        fc = tk.Frame(dlg,bg=self.colors['card'],height=300); fc.pack(fill='both',expand=True,padx=20,pady=10)
        fc.pack_propagate(False)
        cv = tk.Canvas(fc,bg=self.colors['card'],highlightthickness=0)
        sb = tk.Scrollbar(fc,orient="vertical",command=cv.yview); sf=tk.Frame(cv,bg=self.colors['card'])
        sf.bind("<Configure>",lambda _:cv.configure(scrollregion=cv.bbox("all")))
        cv.create_window((0,0),window=sf,anchor="nw",width=580); cv.configure(yscrollcommand=sb.set)
        cv.pack(side="left",fill="both",expand=True); sb.pack(side="right",fill="y")
        entries = {}
        for col,val in zip(columns,values):
            if col=='Errors': continue
            rf = tk.Frame(sf,bg=self.colors['card']); rf.pack(fill='x',pady=5,padx=10)
            _lbl(rf,f"{col}:",('Segoe UI',10,'bold'),bg=self.colors['card'],fg=self.colors['text'],width=20,anchor='w').pack(side='left')
            e = tk.Entry(rf,font=('Segoe UI',10),width=40); e.insert(0,str(val)); e.pack(side='left',padx=10)
            entries[col] = e
        br = tk.Frame(dlg,bg=self.colors['bg']); br.pack(fill='x',padx=20,pady=10)

        def save():
            try:
                data   = {c:entries[c].get() for c in columns if c!='Errors' and c in entries}
                sid_c  = next((c for c in columns if 'student' in c.lower() and 'id' in c.lower()),None)
                subj_c = next((c for c in columns if 'subject' in c.lower() and 'id' not in c.lower()),None)
                if not sid_c or not subj_c: messagebox.showerror("Error","Missing key columns"); return
                sid_v,subj_v = data.get(sid_c,''), data.get(subj_c,'')
                mask = ((self.error_df[sid_c].astype(str)==str(sid_v))&(self.error_df[subj_c].astype(str)==str(subj_v)))
                if not mask.any(): messagebox.showerror("Error","Record not found"); return
                idx    = self.error_df[mask].index[0]
                old_err= self.error_df.at[idx,'Errors'] if 'Errors' in self.error_df.columns else ''
                vals   = [data.get(c,'') if c!='Errors' else '' for c in columns]
                if not self.validate_single_record(vals, columns):
                    messagebox.showwarning("Invalid","Record still has errors"); return
                # Log changes
                sname = None
                for c in columns:
                    if c in self.error_df.columns and c!='Errors':
                        old_v = self.error_df.at[idx,c]; new_v = data.get(c,old_v)
                        if 'name' in c.lower(): sname = new_v
                        if str(old_v)!=str(new_v):
                            self.log_fixed_error(sid_v,sname or"Unknown",subj_v,c,old_v,new_v,old_err)
                # Move to valid_df
                self.error_df = self.error_df.drop(idx).reset_index(drop=True)
                new_row = {}
                for c in columns:
                    if c=='Errors' or c not in self.valid_df.columns: continue
                    v = data.get(c,''); dt = str(self.valid_df[c].dtype)
                    try: new_row[c] = (int(float(v)) if 'int' in dt else float(v) if 'float' in dt else str(v))
                    except: new_row[c] = v
                self.valid_df = pd.concat([self.valid_df,pd.DataFrame([new_row])],ignore_index=True)
                dlg.destroy()
                messagebox.showinfo("Saved",f"✓ Fixed!\nValid: {len(self.valid_df)}  Errors: {len(self.error_df)}")
                self.show_fix_errors_page()
            except Exception as e: traceback.print_exc(); messagebox.showerror("Error",str(e))

        self.create_button(br,"💾 Save",save,'success',15).pack(side='left',padx=10)
        self.create_button(br,"❌ Cancel",dlg.destroy,'danger',15).pack(side='left',padx=10)

    def add_late_submission(self):
        if self.valid_df is None or self.valid_df.empty:
            messagebox.showerror("Error","Upload data first"); return
        cols = [c for c in self.valid_df.columns if c!='Errors']
        dlg  = tk.Toplevel(self.root); dlg.title("Add Late Submission"); dlg.geometry("600x500")
        dlg.configure(bg=self.colors['bg'])
        tk.Frame(dlg,bg=self.colors['success']).pack(fill='x')
        _lbl(dlg.winfo_children()[-1],"➕ Add Late Submission",('Segoe UI',16,'bold'),bg=self.colors['success'],fg='white').pack(pady=15)
        cv = tk.Canvas(dlg,bg=self.colors['card']); sb=tk.Scrollbar(dlg,orient="vertical",command=cv.yview)
        sf = tk.Frame(cv,bg=self.colors['card'])
        sf.bind("<Configure>",lambda _:cv.configure(scrollregion=cv.bbox("all")))
        cv.create_window((0,0),window=sf,anchor="nw"); cv.configure(yscrollcommand=sb.set)
        cv.pack(side="left",fill="both",expand=True,padx=20,pady=20); sb.pack(side="right",fill="y")
        entries = {}
        for col in cols:
            rf = tk.Frame(sf,bg=self.colors['card']); rf.pack(fill='x',pady=8,padx=10)
            _lbl(rf,f"{col}:",('Segoe UI',10,'bold'),bg=self.colors['card'],fg=self.colors['text'],width=20,anchor='w').pack(side='left')
            e = tk.Entry(rf,font=('Segoe UI',10),width=40); e.pack(side='left',padx=10); entries[col]=e
        br = tk.Frame(dlg,bg=self.colors['card']); br.pack(fill='x',padx=20,pady=15)
        def save():
            rec = {c:entries[c].get() for c in cols}
            if self.validate_single_record([rec[c] for c in cols],cols):
                self.valid_df = pd.concat([self.valid_df,pd.DataFrame([rec])],ignore_index=True)
                messagebox.showinfo("Success","✓ Late submission added!"); dlg.destroy()
            else: messagebox.showerror("Invalid","Enter valid data for all fields")
        self.create_button(br,"💾 Add",save,'success',15).pack(side='left',padx=10)
        self.create_button(br,"❌ Cancel",dlg.destroy,'danger',15).pack(side='left',padx=10)

    def revalidate_after_fixes(self):
        if messagebox.askyesno("Refresh","Refresh Valid/Error tabs with fixes?"):
            self.navigate_to('validate')
            self.root.after(100, self.refresh_validation_display)

    def refresh_validation_display(self):
        self.root.config(cursor="wait")
        self.populate_treeview(self.valid_tree, self.valid_df)
        self.populate_treeview(self.error_tree, self.error_df)
        self.root.config(cursor="")
        self.show_validation_summary(len(self.valid_df), len(self.error_df))
        if hasattr(self,'validation_notebook'): self.validation_notebook.select(0)
        messagebox.showinfo("Refreshed",f"Valid: {len(self.valid_df)}  Errors: {len(self.error_df)}")

    # ── PENDING ───────────────────────────────────────────────────────────
    def show_pending_page(self):
        self.create_page_header("Pending Students","Students with incomplete subject marks")
        card = self.create_card(self.content_area, pady=10)
        info = tk.Frame(card,bg='#FFF3CD',relief='solid',bd=1); info.pack(fill='x',padx=20,pady=15)
        _lbl(info,"ℹ️  Pending students have some marks submitted but not all.",
             bg='#FFF3CD',fg='#856404',wraplength=900,justify='left').pack(padx=15,pady=12)
        stats = tk.Frame(card,bg=self.colors['card']); stats.pack(fill='x',padx=20,pady=10)
        has_pending = self.pending_df is not None and not self.pending_df.empty
        if has_pending:
            sid_c = next((c for c in self.pending_df.columns if 'student' in c.lower() and 'id' in c.lower()),None)
            uniq  = len(self.pending_df[sid_c].unique()) if sid_c else len(self.pending_df)
            _lbl(stats,f"⏳ {uniq} student(s) pending  •  {len(self.pending_df)} records",
                 ('Segoe UI',12,'bold'),bg=self.colors['card'],fg=self.colors['warning']).pack(side='left',padx=10)
        else:
            _lbl(stats,"✓ All students have complete marks!",('Segoe UI',12,'bold'),
                 bg=self.colors['card'],fg=self.colors['success']).pack(side='left',padx=10)
        br = tk.Frame(stats,bg=self.colors['card']); br.pack(side='right',padx=10)
        if has_pending:
            self.create_button(br,"📥 Export",self.export_pending_list,'primary',14).pack(side='left',padx=5)
        self.create_button(br,"Reports →",lambda:self.navigate_to('reports'),'success',14).pack(side='left',padx=5)
        if has_pending:
            self.pending_tree = self.create_treeview(card)
            self.populate_treeview(self.pending_tree, self.pending_df)
        else:
            ef = tk.Frame(card,bg='white',height=200); ef.pack(fill='both',expand=True,padx=20,pady=20)
            _lbl(ef,"🎉",('Segoe UI',48),bg='white').pack(pady=(40,10))
            _lbl(ef,"All Students Complete!",('Segoe UI',16,'bold'),bg='white',fg=self.colors['success']).pack()

    def export_pending_list(self):
        if self.pending_df is None or self.pending_df.empty: messagebox.showinfo("Info","No pending students"); return
        f = filedialog.asksaveasfilename(defaultextension=".xlsx",filetypes=[("Excel","*.xlsx")],initialfile="pending_students.xlsx")
        if f:
            try: self.pending_df.to_excel(f,index=False); messagebox.showinfo("Success",f"Exported to:\n{f}")
            except Exception as e: messagebox.showerror("Error",str(e))

    # ── RESULTS ───────────────────────────────────────────────────────────
    def show_results_page(self):
        self.create_page_header("Calculate Results","Process and grade student results")
        card = self.create_card(self.content_area)
        if self.valid_df is None or self.valid_df.empty:
            _lbl(card,"⚠️ No valid data – validate first.",fg=self.colors['warning']).pack(pady=100); return
        br = tk.Frame(card,bg=self.colors['card']); br.pack(fill='x',padx=20,pady=20)
        self.create_button(br,"📊 Calculate",self.calculate_results,'success',20).pack(side='left',padx=5)
        self.create_button(br,"⏳ Pending Students",lambda:self.navigate_to('pending'),'warning',20).pack(side='left',padx=5)
        self.results_continue_btn = self.create_button(br,"Continue to Reports →",lambda:self.navigate_to('reports'),width=20)
        self.results_continue_btn.pack(side='left',padx=5); self.results_continue_btn.config(state='disabled')
        self.results_summary_frame = tk.Frame(card,bg=self.colors['card'])
        self.results_summary_frame.pack(fill='x',padx=20,pady=(0,10))
        self.results_tree = self.create_treeview(card)

    def show_results_summary(self, total_count):
        for w in self.results_summary_frame.winfo_children(): w.destroy()
        if self.results_df is None or self.results_df.empty: return
        passed = len(self.results_df[self.results_df['Result']=='PASS'])
        failed = total_count-passed
        prate  = (passed/total_count*100) if total_count else 0
        card   = tk.Frame(self.results_summary_frame,bg='#E8F5E9',relief='solid',bd=1)
        card.pack(fill='x',pady=10)
        body = tk.Frame(card,bg=card['bg']); body.pack(pady=15)
        _lbl(body,"✓ Results Calculated Successfully",('Segoe UI',14,'bold'),
             bg=card['bg'],fg=self.colors['success']).pack()
        sr  = tk.Frame(body,bg=card['bg']); sr.pack(pady=10)
        sep = dict(font=('Segoe UI',24),bg=card['bg'],fg=self.colors['border'])
        self.create_stat_box(sr,str(total_count),"Total",card['bg'])
        tk.Label(sr,text="|",**sep).pack(side='left',padx=10)
        self.create_stat_box(sr,str(passed),"Passed",card['bg'],self.colors['success'])
        tk.Label(sr,text="|",**sep).pack(side='left',padx=10)
        self.create_stat_box(sr,str(failed),"Failed",card['bg'],self.colors['danger'] if failed else self.colors['text_light'])
        tk.Label(sr,text="|",**sep).pack(side='left',padx=10)
        self.create_stat_box(sr,f"{prate:.1f}%","Pass Rate",card['bg'])
        _lbl(body,"🎉 Click 'Continue to Reports' to generate reports",('Segoe UI',10),
             bg=card['bg'],fg=self.colors['success']).pack(pady=(10,0))

    # ── REPORTS ───────────────────────────────────────────────────────────
    def show_reports_page(self):
        self.create_page_header("Generate Reports","Create and export reports")
        card = self.create_card(self.content_area)
        if self.results_df is None or self.results_df.empty:
            _lbl(card,"⚠️ No results – calculate first.",fg=self.colors['warning']).pack(pady=100); return
        con = tk.Frame(card,bg=self.colors['card']); con.pack(expand=True)
        _lbl(con,"📄 Available Reports",('Segoe UI',18,'bold'),
             bg=self.colors['card'],fg=self.colors['text']).pack(pady=(20,30))
        for txt,desc,cmd,sty in [
            ("📊 Final Result Sheet (Excel)","Complete results for all students",self.export_results_excel,'primary'),
            ("📋 Individual Marksheets (PDF)","Generate PDF for each student",self.generate_individual_marksheets,'success'),
            ("📄 Summary Report","Overall statistics",self.generate_summary_report,'primary'),
            ("❌ Failed Students Report","List of failed students",self.generate_failed_report,'danger'),
            ("💾 Export All Reports","Generate all reports at once",self.export_all_reports,'warning')]:
            row = tk.Frame(con,bg=self.colors['card']); row.pack(pady=10)
            self.create_button(row,txt,cmd,style=sty,width=35).pack()
            _lbl(row,desc,('Segoe UI',9),bg=self.colors['card'],fg=self.colors['text_light']).pack(pady=(5,0))

    # ── FIXED HISTORY ─────────────────────────────────────────────────────
    def show_fixed_history_page(self):
        self.create_page_header("Fixed Errors History","Audit trail of corrections")
        card = self.create_card(self.content_area, pady=10)
        try:
            con = sqlite3.connect(SQLITE_DB_FILE); cur = con.cursor()
            cur.execute("SELECT fix_id,student_id,student_name,subject,field_name,"
                        "old_value,new_value,error_message,fixed_by,fixed_at FROM fixed_errors ORDER BY fixed_at DESC")
            fixes = cur.fetchall(); con.close()
            if not fixes:
                _lbl(card,"📋 No fixes recorded yet",fg=self.colors['text_light']).pack(pady=100); return
            sr = tk.Frame(card,bg=self.colors['card']); sr.pack(fill='x',padx=20,pady=15)
            _lbl(sr,f"📋 {len(fixes)} fixes",('Segoe UI',12,'bold'),bg=self.colors['card'],fg=self.colors['primary']).pack(side='left',padx=10)
            self.create_button(sr,"💾 Export to Excel",self.export_fixed_history,'success',18).pack(side='right',padx=10)
            frm = tk.Frame(card,bg=self.colors['card']); frm.pack(fill='both',expand=True,padx=20,pady=10)
            ys  = tk.Scrollbar(frm); ys.pack(side='right',fill='y')
            xs  = tk.Scrollbar(frm,orient='horizontal'); xs.pack(side='bottom',fill='x')
            self.history_tree = ttk.Treeview(frm,yscrollcommand=ys.set,xscrollcommand=xs.set,selectmode='browse',height=20)
            self.history_tree.pack(fill='both',expand=True)
            ys.config(command=self.history_tree.yview); xs.config(command=self.history_tree.xview)
            cols = ('Fix ID','Student ID','Name','Subject','Field','Old','New','Error','Fixed By','Date')
            self.history_tree['columns'] = cols; self.history_tree['show'] = 'headings'
            widths = {'Fix ID':60,'Student ID':100,'Name':150,'Subject':100,'Field':120,'Old':100,'New':100,'Error':250,'Fixed By':100,'Date':150}
            for c in cols: self.history_tree.heading(c,text=c); self.history_tree.column(c,width=widths.get(c,100))
            self.history_tree.tag_configure('evenrow',background='#F5F5F5')
            for i,fix in enumerate(fixes):
                self.history_tree.insert('','end',values=fix,tags=('evenrow' if i%2==0 else '',))
        except Exception as e: messagebox.showerror("Error",str(e))
