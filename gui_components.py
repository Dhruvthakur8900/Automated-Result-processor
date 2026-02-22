# pylint: disable=all
"""gui_components.py – Sidebar, navigation, and reusable widget factories."""

import tkinter as tk
from tkinter import ttk
from config import COLORS, PAGES_CONFIG


class GUIComponentsMixin:

    def setup_ui(self):
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.main_container = tk.Frame(self.root, bg=self.colors['bg'])
        self.main_container.grid(row=0, column=0, sticky='nsew')
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=0, minsize=250)
        self.main_container.grid_columnconfigure(1, weight=1)

        # Sidebar
        self.sidebar = tk.Frame(self.main_container, bg=self.colors['sidebar'], width=250)
        self.sidebar.grid(row=0, column=0, sticky='nsew')
        self.sidebar.grid_propagate(False)
        hdr = tk.Frame(self.sidebar, bg=self.colors['sidebar'])
        hdr.pack(fill='x', pady=30, padx=20)
        tk.Label(hdr, text="📊 Result Processor", font=('Segoe UI',18,'bold'),
                 bg=self.colors['sidebar'], fg='white').pack()
        tk.Label(hdr, text="Automated System", font=('Segoe UI',10),
                 bg=self.colors['sidebar'], fg='#95A5A6').pack()
        tk.Frame(self.sidebar, bg='#34495E', height=2).pack(fill='x', padx=20, pady=20)
        self.nav_buttons = {}
        self.create_navigation_menu()
        footer = tk.Frame(self.sidebar, bg=self.colors['sidebar'])
        footer.pack(side='bottom', fill='x', pady=20)
        tk.Label(footer, text="v1.0 • 2026", font=('Segoe UI',9),
                 bg=self.colors['sidebar'], fg='#7F8C8D').pack()

        # Content area
        self.content_area = tk.Frame(self.main_container, bg=self.colors['bg'])
        self.content_area.grid(row=0, column=1, sticky='nsew')
        self.sidebar_visible = False
        self.sidebar.grid_remove()
        self.show_page('login')

    def create_navigation_menu(self):
        for page in self.pages_config:
            frm = tk.Frame(self.sidebar, bg=self.colors['sidebar'])
            frm.pack(fill='x', padx=10, pady=3)
            locked = page['locked']
            btn = tk.Button(frm,
                text=f"  {page['icon']}  {page['title']}",
                font=('Segoe UI',11), bg=self.colors['sidebar'],
                fg='white' if not locked else '#7F8C8D',
                activebackground=self.colors['sidebar_hover'], activeforeground='white',
                relief='flat', anchor='w', padx=15, pady=12,
                cursor='hand2' if not locked else 'arrow',
                command=(lambda p=page['id'], lk=locked: self.navigate_to(p) if not lk else None),
                wraplength=210, justify='left')
            btn.pack(fill='x')
            if not locked:
                btn.bind('<Enter>', lambda e,b=btn: b.config(bg=self.colors['sidebar_hover']))
                btn.bind('<Leave>', lambda e,b=btn,pid=page['id']:
                         b.config(bg=self.colors['sidebar'] if self.current_page!=pid else self.colors['sidebar_active']))
            self.nav_buttons[page['id']] = btn
            if locked:
                tk.Label(btn, text="🔒", font=('Segoe UI',10),
                         bg=self.colors['sidebar'], fg='#7F8C8D').place(relx=0.92, rely=0.5, anchor='center')

    def unlock_page(self, page_id):
        for p in self.pages_config:
            if p['id'] == page_id:
                p['locked'] = False
                btn = self.nav_buttons[page_id]
                btn.config(fg='white', cursor='hand2',
                           command=lambda: self.navigate_to(page_id))  # pylint: disable=unnecessary-lambda
                for w in btn.winfo_children(): w.destroy()
                break

    def navigate_to(self, page_id):
        if page_id != 'login': self._ensure_sidebar_visible()
        for pid, btn in self.nav_buttons.items():
            if pid == page_id: btn.config(bg=self.colors['sidebar_active'])
            elif not any(p['locked'] for p in self.pages_config if p['id']==pid):
                btn.config(bg=self.colors['sidebar'])
        self.current_page = page_id
        self.show_page(page_id)

    def force_sidebar_visible(self):
        if self.current_page != 'login': self._ensure_sidebar_visible()

    def _ensure_sidebar_visible(self):
        if hasattr(self,'sidebar') and not self.sidebar_visible:
            self.sidebar.grid(row=0, column=0, sticky='nsew')
            self.sidebar_visible = True

    def show_page(self, page_id):
        if page_id != 'login':
            self._ensure_sidebar_visible()
            self.root.after(100, self.force_sidebar_visible)
        for w in self.content_area.winfo_children(): w.destroy()
        dispatch = {
            'login': self.show_login_page, 'database': self.show_database_page,
            'upload': self.show_upload_page, 'validate': self.show_validate_page,
            'fix_errors': self.show_fix_errors_page, 'results': self.show_results_page,
            'pending': self.show_pending_page, 'reports': self.show_reports_page,
        }
        if page_id in dispatch: dispatch[page_id]()

    # ── Widget factories ──────────────────────────────────────────────────
    def create_page_header(self, title, subtitle=""):
        for w in self.content_area.winfo_children(): w.destroy()
        hdr = tk.Frame(self.content_area, bg='white')
        hdr.pack(fill='x', padx=30, pady=(30,0))
        tk.Label(hdr, text=title, font=('Segoe UI',28,'bold'),
                 bg='white', fg=self.colors['text']).pack(anchor='w', pady=(20,5))
        if subtitle:
            tk.Label(hdr, text=subtitle, font=('Segoe UI',12),
                     bg='white', fg=self.colors['text_light']).pack(anchor='w', pady=(0,20))
        return hdr

    def create_card(self, parent, padx=30, pady=20):
        card = tk.Frame(parent, bg=self.colors['card'], relief='flat', bd=0)
        card.pack(fill='both', expand=True, padx=padx, pady=pady)
        return card

    def create_button(self, parent, text, command, style='primary', width=20):
        color = {'primary': self.colors['primary'], 'success': self.colors['success'],
                 'danger': self.colors['danger'], 'warning': self.colors['warning']}.get(style, self.colors['primary'])
        btn = tk.Button(parent, text=text, command=command, font=('Segoe UI',11,'bold'),
                        bg=color, fg='white', activebackground=color, activeforeground='white',
                        relief='flat', cursor='hand2', padx=25, pady=12, width=width)
        btn.bind('<Enter>', lambda e: btn.config(bg=self.adjust_color(color,-20)))
        btn.bind('<Leave>', lambda e: btn.config(bg=color))
        return btn

    def adjust_color(self, color, amount):
        c = color.lstrip('#')
        r,g,b = (int(c[i:i+2],16) for i in (0,2,4))
        return '#{:02x}{:02x}{:02x}'.format(
            max(0,min(255,r+amount)), max(0,min(255,g+amount)), max(0,min(255,b+amount)))

    def create_treeview(self, parent):
        frm = tk.Frame(parent); frm.pack(fill='both', expand=True, padx=10, pady=10)
        ys = tk.Scrollbar(frm); ys.pack(side='right', fill='y')
        xs = tk.Scrollbar(frm, orient='horizontal'); xs.pack(side='bottom', fill='x')
        tree = ttk.Treeview(frm, yscrollcommand=ys.set, xscrollcommand=xs.set, selectmode='browse')
        tree.pack(fill='both', expand=True)
        ys.config(command=tree.yview); xs.config(command=tree.xview)
        s = ttk.Style()
        s.configure("Treeview", rowheight=25, font=('Segoe UI',10))
        s.map('Treeview', background=[('selected','#3498DB')])
        tree.tag_configure('error',   background='#FFEBEE')
        tree.tag_configure('evenrow', background='#F5F5F5')
        tree.tag_configure('oddrow',  background='#FFFFFF')
        return tree

    def create_stat_box(self, parent, value, label, bg_color, value_color=None):
        box = tk.Frame(parent, bg=bg_color); box.pack(side='left', padx=20)
        tk.Label(box, text=str(value), font=('Segoe UI',24,'bold'),
                 bg=bg_color, fg=value_color or self.colors['primary']).pack()
        tk.Label(box, text=label, font=('Segoe UI',10),
                 bg=bg_color, fg=self.colors['text_light']).pack()
        return box

    def populate_treeview(self, tree, df):
        for item in tree.get_children(): tree.delete(item)
        if df is None or df.empty: return
        tree['columns'] = list(df.columns); tree['show'] = 'headings'
        for col in df.columns:
            tree.heading(col, text=col)
            tree.column(col, width=(400 if col=='Errors' else 150 if any(x in col.lower() for x in ('id','name')) else 120),
                        anchor=('w' if col in ('Errors',) or 'name' in col.lower() else 'center'))
        has_errors = 'Errors' in df.columns
        for idx, vals in enumerate(df.head(200).values.tolist()):
            tag = 'error' if has_errors else ('evenrow' if idx%2==0 else 'oddrow')
            tree.insert('', 'end', values=vals, tags=(tag,))
            if idx % 50 == 0: self.root.update_idletasks()
