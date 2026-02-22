# pylint: disable=all
"""logic.py – Validation, result calculation, and pending student detection."""

import threading, traceback
import pandas as pd
from tkinter import messagebox
from config import EXPECTED_SUBJECTS


class LogicMixin:

    def transform_to_student_rows(self, df):
        """Pivot row-per-subject → row-per-student. Returns original df if columns not found."""
        sid=sname=subj=marks=None
        for c in df.columns:
            cl=c.lower()
            if 'student' in cl and 'id' in cl:   sid=c
            elif 'student' in cl and 'name' in cl: sname=c
            elif 'subject' in cl and 'id' not in cl: subj=c
            elif 'marks' in cl and 'obtain' in cl: marks=c
        if not (sid and subj and marks): return df
        pivot = df.pivot_table(index=sid, columns=subj, values=marks, aggfunc='first').reset_index()
        if sname:
            names = df.groupby(sid)[sname].first()
            pivot = pivot.merge(names, on=sid, how='left')
            cols  = [sid, sname] + [c for c in pivot.columns if c not in (sid, sname)]
            pivot = pivot[cols]
        return pivot

    def run_validation(self):
        if self.df is None: messagebox.showerror("Error","No data"); return
        self.root.config(cursor="wait"); self.root.update_idletasks()
        def worker():
            try:
                self.perform_validation_fast()
                self.root.after(0, self.on_validation_complete)
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
                self.root.after(0, lambda: self.root.config(cursor=""))
        threading.Thread(target=worker, daemon=True).start()

    def perform_validation_fast(self):
        # Column detection
        col_map = {c.lower().strip().replace(' ','').replace('_','').replace('-',''): c for c in self.df.columns}
        sid   = next((col_map[p] for p in ['studentid','studentnumber','id','rollnumber','enrollment'] if p in col_map), None)
        sname = next((col_map[p] for p in ['studentname','name','fullname','student'] if p in col_map), None)
        roll  = next((col_map[p] for p in ['rollno','rollnumber','roll','enrollmentno'] if p in col_map and col_map[p]!=sid), sid)
        missing = [l for l,v in [("Student ID",sid),("Student Name",sname),("Roll No",roll)] if not v]
        if missing: raise Exception(f"Missing columns: {', '.join(missing)}")  # pylint: disable=broad-exception-raised

        marks_cols = [c for c in self.df.columns if 'marks' in c.lower() and 'max' not in c.lower()
                      and c not in (sid, sname, roll)]
        err = pd.Series(False, index=self.df.index)
        msg = pd.Series('',    index=self.df.index)

        for col, lbl in [(sid,"Missing Student ID; "),(sname,"Missing Student Name; "),(roll,"Missing Roll No; ")]:
            m = self.df[col].isna(); err |= m; msg[m] += lbl

        for mc in marks_cols:
            mn  = pd.to_numeric(self.df[mc], errors='coerce')
            base = mc.lower().replace('marks','').replace('_','').replace(' ','').strip()
            maxc = next((c for c in self.df.columns if base in c.lower().replace('_','').replace(' ','') and 'max' in c.lower()), None)
            maxv = pd.to_numeric(self.df[maxc], errors='coerce').fillna(100) if maxc else 100
            miss = mn.isna(); neg = (mn<0)&~mn.isna(); over = (mn>maxv)&~mn.isna()
            err |= miss|neg|over
            msg[miss] += f"Missing {mc}; "; msg[neg] += f"Negative {mc}; "; msg[over] += f"Exceeds max {mc}; "

        self.valid_df = self.df[~err].copy()
        self.error_df = self.df[err].copy()
        if not self.error_df.empty: self.error_df['Errors'] = msg[err].str.rstrip('; ')
        self.detect_pending_students()

    def on_validation_complete(self):
        self._ensure_sidebar_visible()
        self.show_validation_summary(len(self.valid_df), len(self.error_df))
        self.root.config(cursor="wait"); self.root.update()
        self.populate_treeview(self.valid_tree, self.valid_df)
        self.populate_treeview(self.error_tree, self.error_df)
        self.root.config(cursor=""); self.root.update()
        if len(self.valid_df) > 0:
            self.unlock_page('results')
            if hasattr(self,'continue_btn'): self.continue_btn.config(state='normal')
        if len(self.error_df) > 0:
            self.unlock_page('fix_errors')
            if hasattr(self,'fix_errors_btn'): self.fix_errors_btn.config(state='normal')
        if self.db_connection and self.db_connection.is_connected():
            self.auto_save_validation_results()
            if len(self.error_df) > 0: self.save_error_logs_to_database()

    def validate_single_record(self, values, columns):
        try:
            for col, val in zip(columns, values):
                if 'marks' in col.lower() and 'max' not in col.lower():
                    m = float(val)
                    if m < 0 or m > 100: return False
            return True
        except (ValueError, TypeError): return False

    def detect_pending_students(self):
        try:
            if self.valid_df is None or self.valid_df.empty:
                self.pending_df = self.df.copy() if self.df is not None and not self.df.empty else pd.DataFrame()
                if not self.pending_df.empty: self.pending_df['Status'] = 'All subjects have errors'
                return
            sid_col  = next((c for c in self.valid_df.columns if 'student' in c.lower() and 'id' in c.lower()), None)
            sid_col  = sid_col or next((c for c in self.valid_df.columns if c.lower() in ('id','studentid')), None)
            subj_col = next((c for c in (self.df.columns if self.df is not None else []) if 'subject' in c.lower()), None)
            if not sid_col: self.pending_df = pd.DataFrame(); return

            counts      = self.valid_df.groupby(sid_col).size()
            pending_ids = counts[counts < EXPECTED_SUBJECTS].index.tolist()
            if self.df is not None and sid_col in self.df.columns:
                pending_ids += [s for s in self.df[sid_col].unique() if s not in counts.index]

            if not pending_ids: self.pending_df = pd.DataFrame(); return

            exp_subjs = (['Maths','Physics','Chemistry','English','Computer'] if not subj_col else
                         self.df[subj_col].value_counts().nlargest(EXPECTED_SUBJECTS).index.tolist())
            valid_subjs_map = {
                sid: (self.valid_df[self.valid_df[sid_col]==sid][subj_col].tolist()
                      if subj_col and subj_col in self.valid_df.columns else [])
                for sid in pending_ids}

            records = []
            for sid in pending_ids:
                missing = [s for s in exp_subjs if s not in valid_subjs_map.get(sid,[])]
                sinfo   = self.df[self.df[sid_col]==sid].iloc[0] if self.df is not None and sid_col in self.df.columns else None
                for subj in missing:
                    if (self.error_df is not None and not self.error_df.empty
                            and subj_col and subj_col in self.error_df.columns and sid_col in self.error_df.columns):
                        er = self.error_df[(self.error_df[sid_col]==sid)&(self.error_df[subj_col]==subj)]
                        if not er.empty:
                            row = er.copy(); row['Status'] = f"Pending – {er.get('Errors',['Invalid']).iloc[0]}"
                            records.append(row); continue
                    if sinfo is not None:
                        records.append(pd.DataFrame([{sid_col: sid, 'student_name': sinfo.get('student_name',f'Student_{sid}'),
                            subj_col: subj, 'marks_obtained': 'NOT SUBMITTED', 'max_marks': 100,
                            'Status': 'Pending – Not submitted', 'Errors': 'Not submitted'}]))
            self.pending_df = pd.concat(records, ignore_index=True) if records else pd.DataFrame()
        except Exception as e:
            print(f"[Logic] pending detection error: {e}"); traceback.print_exc()
            self.pending_df = pd.DataFrame()

    def calculate_results(self):
        if self.valid_df is None or self.valid_df.empty:
            messagebox.showerror("Error","No valid data"); return
        try:
            self.root.config(cursor="wait"); self.root.update()
            sid=sname=subj=marks=None
            for c in self.valid_df.columns:
                cl=c.lower()
                if 'student' in cl and 'id' in cl:    sid=c
                elif 'student' in cl and 'name' in cl: sname=c
                elif 'subject' in cl:                  subj=c
                elif 'marks' in cl and 'obtain' in cl: marks=c
            if not (sid and subj and marks):
                messagebox.showerror("Error","Could not find required columns"); self.root.config(cursor=""); return

            counts   = self.valid_df.groupby(sid).size()
            complete = counts[counts >= EXPECTED_SUBJECTS].index.tolist()
            if not complete:
                messagebox.showwarning("No Complete Students", f"No students have all {EXPECTED_SUBJECTS} subjects.")
                self.root.config(cursor=""); return

            df = self.valid_df[self.valid_df[sid].isin(complete)].copy()
            df[marks] = pd.to_numeric(df[marks], errors='coerce')
            pivot = df.pivot_table(index=sid, columns=subj, values=marks, aggfunc='first').reset_index()
            if sname:
                pivot = pivot.merge(df.groupby(sid)[sname].first(), on=sid, how='left')

            subj_cols = [c for c in pivot.columns if c not in (sid, sname)]
            pivot['Total']      = pivot[subj_cols].sum(axis=1)
            pivot['Percentage'] = (pivot['Total'] / (len(subj_cols)*100) * 100).round(2)
            pct = pivot['Percentage']
            pivot['Grade'] = pd.cut(pct, bins=[-1,40,50,60,70,80,90,101],
                                    labels=['F','D','C','B','A','A+','A+'], right=True)
            # Fix grade – pd.cut might give duplicates for A+; recalc simply
            pivot['Grade'] = 'F'
            pivot.loc[pct>=90,'Grade']='A+'; pivot.loc[(pct>=80)&(pct<90),'Grade']='A'
            pivot.loc[(pct>=70)&(pct<80),'Grade']='B'; pivot.loc[(pct>=60)&(pct<70),'Grade']='C'
            pivot.loc[(pct>=50)&(pct<60),'Grade']='D'
            pivot['Result'] = (pct>=40).map({True:'PASS',False:'FAIL'})

            final_cols = [sid] + ([sname] if sname else []) + subj_cols + ['Total','Percentage','Grade','Result']
            self.results_df = pivot[final_cols].copy()
            self.populate_treeview(self.results_tree, self.results_df.head(1000))
            self.show_results_summary(len(self.results_df))
            self.detect_pending_students()
            self.unlock_page('pending'); self.unlock_page('reports')
            if hasattr(self,'results_continue_btn'): self.results_continue_btn.config(state='normal')
            if self.db_connection and self.db_connection.is_connected(): self.auto_save_results()
            self._ensure_sidebar_visible(); self.root.config(cursor="")
            messagebox.showinfo("Success", f"✓ Results calculated!\n{len(self.results_df):,} students ready for export.")
        except Exception as e:
            self.root.config(cursor=""); messagebox.showerror("Error", str(e))
