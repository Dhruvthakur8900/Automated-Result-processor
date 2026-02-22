# pylint: disable=all
"""main.py – Entry point. Assembles all mixins into ModernResultProcessor."""

import tkinter as tk
from config import APP_TITLE, APP_GEOMETRY, APP_MIN_SIZE, COLORS, PAGES_CONFIG
from gui_components import GUIComponentsMixin
from gui_pages      import GUIPagesMixin
from database       import DatabaseMixin
from logic          import LogicMixin
from reports        import ReportsMixin


class ModernResultProcessor(GUIComponentsMixin, GUIPagesMixin, DatabaseMixin, LogicMixin, ReportsMixin):

    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE); self.root.geometry(APP_GEOMETRY); self.root.minsize(*APP_MIN_SIZE)

        # Data state
        self.df = self.valid_df = self.error_df = self.pending_df = self.results_df = None
        self.db_connection = self.logged_in_user = self.db_config = None
        self.db_table_name = 'results'

        # UI refs (set during page rendering)
        self.sidebar = self.main_container = self.content_area = None
        self.nav_buttons = {}; self.sidebar_visible = False
        self.username_entry = self.password_entry = None
        self.db_host = self.db_port = self.db_user = self.db_pass = None
        self.db_name = self.db_table = self.db_status_label = None
        self.drop_zone = self.save_to_db_btn = self.upload_continue_btn = None
        self.file_info_label = self.upload_preview_frame = None
        self.continue_btn = self.fix_errors_btn = None
        self.validation_summary_frame = self.valid_tree = self.error_tree = self.validation_notebook = None
        self.fix_errors_tree = self.pending_tree = self.history_tree = None
        self.results_continue_btn = self.results_summary_frame = self.results_tree = None

        # Config
        self.colors       = COLORS
        self.pages_config = [dict(p) for p in PAGES_CONFIG]
        self.current_page = "login"

        self.init_database()
        self.setup_ui()


if __name__ == "__main__":
    root = tk.Tk()
    ModernResultProcessor(root)
    root.mainloop()
