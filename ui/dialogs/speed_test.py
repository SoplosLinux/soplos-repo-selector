"""
Speed Test Dialog.
"""

import gi
import threading
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Pango

from core.i18n_manager import _
from services.speed_test_service import RepoSpeedTester

class SpeedTestDialog(Gtk.Dialog):
    """Dialog to test mirror speeds."""
    
    def __init__(self, parent):
        super().__init__(title=_("Find Fastest Mirrors"), transient_for=parent)
        self.set_default_size(600, 400)
        self.add_button(_("Close"), Gtk.ResponseType.CANCEL)
        self.select_btn = self.add_button(_("Select Best"), Gtk.ResponseType.OK)
        self.select_btn.set_sensitive(False)
        
        self.tester = RepoSpeedTester()
        self.results = []
        
        self._create_ui()
        self.show_all()
        
        # Start test automatically
        self.start_test()
    
    def _create_ui(self):
        box = self.get_content_area()
        box.set_spacing(10)
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        box.set_margin_start(10)
        box.set_margin_end(10)
        
        # Progress info
        self.status_label = Gtk.Label(label=_("Initializing speed test..."))
        box.pack_start(self.status_label, False, False, 0)
        
        self.progress_bar = Gtk.ProgressBar()
        box.pack_start(self.progress_bar, False, False, 0)
        
        # Results List
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)
        
        self.list_box = Gtk.ListBox()
        self.list_box.set_selection_mode(Gtk.SelectionMode.SINGLE)
        scrolled.add(self.list_box)
        
        box.pack_start(scrolled, True, True, 0)
    
    def start_test(self):
        self.status_label.set_text(_("Testing mirrors... This may take a moment."))
        self.progress_bar.pulse()
        
        # Threaded test
        thread = threading.Thread(target=self._run_test)
        thread.daemon = True
        thread.start()
        
        # Pulse timer
        self.pulse_timer = GLib.timeout_add(100, self._pulse_progress)
    
    def _pulse_progress(self):
        self.progress_bar.pulse()
        return True
    
    def _run_test(self):
        results = self.tester.test_mirrors_parallel(callback=None)
        GLib.idle_add(self._on_test_finished, results)
    
    def _on_test_finished(self, results):
        GLib.source_remove(self.pulse_timer)
        self.progress_bar.set_fraction(1.0)
        self.status_label.set_text(_("Test completed."))
        self.select_btn.set_sensitive(True)
        self.results = results
        
        for result in results:
            row = Gtk.ListBoxRow()
            grid = Gtk.Grid()
            grid.set_column_spacing(10)
            grid.set_margin_top(5)
            grid.set_margin_bottom(5)
            grid.set_margin_start(5)
            grid.set_margin_end(5)
            
            # Icon based on speed
            icon_name = "network-cellular-signal-good-symbolic" # default
            speed = result.get('speed_mbps', 0)
            if speed > 2.0: icon_name = "network-cellular-signal-excellent-symbolic"
            elif speed < 0.5: icon_name = "network-cellular-signal-weak-symbolic"
            
            icon = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.BUTTON)
            grid.attach(icon, 0, 0, 1, 2)
            
            url_label = Gtk.Label(label=result['url'])
            url_label.set_xalign(0)
            url_label.get_style_context().add_class('bold')
            grid.attach(url_label, 1, 0, 1, 1)
            
            info = f"{result['country']} - {speed:.2f} MB/s ({result.get('latency_ms', 0):.0f} ms)"
            info_label = Gtk.Label(label=info)
            info_label.set_xalign(0)
            info_label.get_style_context().add_class('dim-label')
            grid.attach(info_label, 1, 1, 1, 1)
            
            row.add(grid)
            self.list_box.add(row)
            
        self.list_box.show_all()
        
        # Select first item
        row = self.list_box.get_row_at_index(0)
        if row:
            self.list_box.select_row(row)

    def get_selected_mirror(self):
        row = self.list_box.get_selected_row()
        if row:
            idx = row.get_index()
            if 0 <= idx < len(self.results):
                return self.results[idx]
        return None
