"""
Repository Edit Dialog.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from core.i18n_manager import _

class RepoEditDialog(Gtk.Dialog):
    """Dialog to add or edit a repository."""
    
    def __init__(self, parent, repo_data=None):
        title = _("Edit Repository") if repo_data else _("Add Repository")
        super().__init__(title=title, transient_for=parent, flags=0)
        self.add_buttons(
            _("Cancel"), Gtk.ResponseType.CANCEL,
            _("Save"), Gtk.ResponseType.OK
        )
        
        self.repo_data = repo_data or {}
        self.set_default_size(450, -1)
        
        self._create_ui()
        self.show_all()
    
    def _create_ui(self):
        box = self.get_content_area()
        box.set_spacing(10)
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        box.set_margin_start(10)
        box.set_margin_end(10)
        
        # Grid layout
        grid = Gtk.Grid()
        grid.set_column_spacing(10)
        grid.set_row_spacing(10)
        box.add(grid)
        
        # Type
        grid.attach(Gtk.Label(label=_("Type:")), 0, 0, 1, 1)
        self.type_combo = Gtk.ComboBoxText()
        self.type_combo.append("deb", "Binary (deb)")
        self.type_combo.append("deb-src", "Source (deb-src)")
        
        current_type = self.repo_data.get('type', 'deb')
        self.type_combo.set_active_id(current_type)
        grid.attach(self.type_combo, 1, 0, 1, 1)
        
        # URI
        grid.attach(Gtk.Label(label=_("URI:")), 0, 1, 1, 1)
        self.uri_entry = Gtk.Entry()
        self.uri_entry.set_text(self.repo_data.get('uri', 'http://'))
        grid.attach(self.uri_entry, 1, 1, 1, 1)
        
        # Distribution
        grid.attach(Gtk.Label(label=_("Distribution:")), 0, 2, 1, 1)
        self.dist_entry = Gtk.Entry()
        self.dist_entry.set_text(self.repo_data.get('distribution', ''))
        grid.attach(self.dist_entry, 1, 2, 1, 1)
        
        # Components
        grid.attach(Gtk.Label(label=_("Components:")), 0, 3, 1, 1)
        self.comp_entry = Gtk.Entry()
        self.comp_entry.set_text(self.repo_data.get('components', 'main'))
        grid.attach(self.comp_entry, 1, 3, 1, 1)
        
        # Signed-By (Advanced)
        grid.attach(Gtk.Label(label=_("Signed By (Key):")), 0, 4, 1, 1)
        self.key_entry = Gtk.Entry()
        self.key_entry.set_placeholder_text(_("Optional (key path or fingerprint)"))
        self.key_entry.set_text(self.repo_data.get('signed_by', ''))
        grid.attach(self.key_entry, 1, 4, 1, 1)
        
        # Comment
        grid.attach(Gtk.Label(label=_("Comment:")), 0, 5, 1, 1)
        self.comment_entry = Gtk.Entry()
        self.comment_entry.set_text(self.repo_data.get('comment', ''))
        grid.attach(self.comment_entry, 1, 5, 1, 1)
        
    def get_repo_data(self):
        """Returns the modified repo data."""
        return {
            'type': self.type_combo.get_active_id(),
            'uri': self.uri_entry.get_text().strip(),
            'distribution': self.dist_entry.get_text().strip(),
            'components': self.comp_entry.get_text().strip(),
            'signed_by': self.key_entry.get_text().strip(),
            'comment': self.comment_entry.get_text().strip(),
            # Preserve existing fields
            'disabled': self.repo_data.get('disabled', False),
            'file': self.repo_data.get('file'),
            'format': self.repo_data.get('format', 'legacy')
        }
