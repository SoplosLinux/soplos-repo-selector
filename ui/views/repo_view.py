"""
Repository List View.
Displays and manages the list of repositories.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

from core.i18n_manager import _
from services.repo_manager import get_repo_manager
from ui.widgets.repo_row import RepoRow
from ui.dialogs.repo_edit import RepoEditDialog
from ui.dialogs.speed_test import SpeedTestDialog

class RepoView(Gtk.Box):
    """View for managing repositories."""
    
    def __init__(self, main_window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.main_window = main_window
        self.repo_manager = get_repo_manager()
        self.repos = []
        
        self._create_ui()
        self.refresh_repos()
    
    def _create_ui(self):
        """Create view UI."""
        self.set_margin_top(10)
        self.set_margin_bottom(10)
        self.set_margin_start(10)
        self.set_margin_end(10)
        
        # Toolbar / Action Bar
        action_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        
        add_btn = Gtk.Button(label=_("Add Repository"))
        image = Gtk.Image.new_from_icon_name("list-add-symbolic", Gtk.IconSize.BUTTON)
        add_btn.set_image(image)
        add_btn.connect("clicked", self._on_add_clicked)
        action_bar.pack_start(add_btn, False, False, 0)
        
        refresh_btn = Gtk.Button.new_from_icon_name("view-refresh-symbolic", Gtk.IconSize.BUTTON)
        refresh_btn.set_tooltip_text(_("Refresh"))
        refresh_btn.connect("clicked", lambda b: self.refresh_repos())
        action_bar.pack_start(refresh_btn, False, False, 0)
        
        sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        action_bar.pack_start(sep, False, False, 6)
        
        speed_btn = Gtk.Button(label=_("Find Fastest Mirrors"))
        speed_btn.set_tooltip_text(_("Test mirrors speed and select the fastest ones"))
        speed_btn.connect("clicked", self._on_speed_test_clicked)
        action_bar.pack_start(speed_btn, False, False, 0)
        
        # Spacer
        action_bar.pack_start(Gtk.Label(), True, True, 0)
        
        # Apply button (initially insensitive)
        self.apply_btn = Gtk.Button(label=_("Apply Changes"))
        self.apply_btn.get_style_context().add_class('suggested-action')
        self.apply_btn.set_sensitive(False)
        self.apply_btn.connect("clicked", self._on_apply_clicked)
        action_bar.pack_start(self.apply_btn, False, False, 0)
        
        self.pack_start(action_bar, False, False, 0)
        
        # List container with scroll
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)
        
        # Frame for visual grouping
        frame = Gtk.Frame()
        frame.get_style_context().add_class('view')
        
        self.list_box = Gtk.ListBox()
        self.list_box.set_selection_mode(Gtk.SelectionMode.NONE)
        
        self.list_box.set_placeholder(self._create_placeholder())
        
        frame.add(self.list_box)
        scrolled.add(frame)
        self.pack_start(scrolled, True, True, 0)
        
    def _create_placeholder(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_valign(Gtk.Align.CENTER)
        box.set_halign(Gtk.Align.CENTER)
        
        icon = Gtk.Image.new_from_icon_name("software-properties", Gtk.IconSize.DIALOG)
        icon.set_pixel_size(64)
        box.pack_start(icon, False, False, 0)
        
        label = Gtk.Label(label=_("No repositories found"))
        label.get_style_context().add_class('dim-label')
        box.pack_start(label, False, False, 0)
        
        box.show_all()
        return box

    def refresh_repos(self):
        """Reload repos from disk."""
        for row in self.list_box.get_children():
            self.list_box.remove(row)
        
        self.repos = self.repo_manager.get_all_repos(use_cache=False)
        
        for repo in self.repos:
            row = RepoRow(
                repo,
                on_toggle=self._on_repo_changed,
                on_edit=self._on_edit_repo,
                on_delete=self._on_delete_repo
            )
            self.list_box.add(row)
        
        self.list_box.show_all()
        self.apply_btn.set_sensitive(False)

    def _on_repo_changed(self, repo_data):
        self.apply_btn.set_sensitive(True)
    
    def _on_edit_repo(self, repo_data):
        dialog = RepoEditDialog(self.main_window, repo_data)
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            new_data = dialog.get_repo_data()
            dialog.destroy()
            
            # Update data in place
            repo_data.update(new_data)
            self.refresh_ui_from_data()
            self._on_repo_changed(repo_data)
        else:
            dialog.destroy()
    
    def _on_delete_repo(self, repo_data):
        dialog = Gtk.MessageDialog(
            transient_for=self.main_window,
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.OK_CANCEL,
            text=_("Delete Repository?")
        )
        dialog.format_secondary_text(
            _("Are you sure you want to delete this repository?\n\n{}").format(repo_data['uri'])
        )
        response = dialog.run()
        dialog.destroy()
        
        if response == Gtk.ResponseType.OK:
            self.repos.remove(repo_data)
            self.refresh_ui_from_data()
            self._on_repo_changed(None)
    
    def _on_add_clicked(self, btn):
        dialog = RepoEditDialog(self.main_window)
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            new_repo = dialog.get_repo_data()
            dialog.destroy()
            self.repos.append(new_repo)
            self.refresh_ui_from_data()
            self._on_repo_changed(None)
        else:
            dialog.destroy()
        
    def _on_speed_test_clicked(self, btn):
        dialog = SpeedTestDialog(self.main_window)
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            best_mirror = dialog.get_selected_mirror()
            dialog.destroy()
            
            if best_mirror:
                # Ask user if they want to replace existing main repos with this mirror?
                # Or just add it? Usually we replace.
                # Logic to replace main repo is complex.
                # For now, let's just show a message or add it as new.
                
                # Simple implementation: Add as new repo
                new_repo = {
                    'type': 'deb',
                    'uri': best_mirror['url'],
                    'distribution': 'stable', # How to guess?
                    'components': 'main contrib non-free',
                    'comment': f"Fastest mirror selected: {best_mirror['speed_mbps']:.2f} MB/s",
                    'file': None # Will be auto determined
                }
                self.repos.append(new_repo)
                self.refresh_ui_from_data()
                self._on_repo_changed(None)
        else:
            dialog.destroy()
        
    def _on_apply_clicked(self, btn):
        self.apply_btn.set_sensitive(False)
        
        if self.repo_manager.save_repos(self.repos):
            dialog = Gtk.MessageDialog(
                transient_for=self.main_window,
                flags=0,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text=_("Changes Applied")
            )
            dialog.format_secondary_text(_("Repositories have been updated successfully."))
            dialog.run()
            dialog.destroy()
        else:
            dialog = Gtk.MessageDialog(
                transient_for=self.main_window,
                flags=0,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text=_("Error Saving")
            )
            dialog.format_secondary_text(_("Could not save repositories. Check logs for details."))
            dialog.run()
            dialog.destroy()
            self.apply_btn.set_sensitive(True)
            
    def refresh_ui_from_data(self):
        """Redraw list from self.repos."""
        for row in self.list_box.get_children():
            self.list_box.remove(row)
        
        for repo in self.repos:
            row = RepoRow(repo, self._on_repo_changed, self._on_edit_repo, self._on_delete_repo)
            self.list_box.add(row)
        self.list_box.show_all()
