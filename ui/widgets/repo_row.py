"""
Repository Row Widget.
Display a single repository in the list.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, Pango

from core.i18n_manager import _

class RepoRow(Gtk.ListBoxRow):
    """Row widget representing a single repository."""
    
    def __init__(self, repo_data, on_toggle=None, on_edit=None, on_delete=None):
        super().__init__()
        self.repo_data = repo_data
        self.on_toggle = on_toggle
        self.on_edit = on_edit
        self.on_delete = on_delete
        
        self.set_activatable(False)
        self.set_selectable(False)
        
        self._create_ui()
    
    def _create_ui(self):
        """Create the row UI."""
        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        main_box.set_margin_top(8)
        main_box.set_margin_bottom(8)
        main_box.set_margin_start(12)
        main_box.set_margin_end(12)
        
        # Enable Switch
        self.switch = Gtk.Switch()
        self.switch.set_active(not self.repo_data.get('disabled', False))
        self.switch.set_valign(Gtk.Align.CENTER)
        self.switch.connect('state-set', self._on_switch_state_set)
        main_box.pack_start(self.switch, False, False, 0)
        
        # Info Box (URI and Distribution)
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        
        # URI
        uri_label = Gtk.Label(label=self.repo_data.get('uri', ''))
        uri_label.set_xalign(0)
        uri_label.get_style_context().add_class('repo-uri')
        uri_label.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
        info_box.pack_start(uri_label, True, True, 0)
        
        # Details (Type + Dist + Components)
        details_text = f"{self.repo_data.get('type', '')} {self.repo_data.get('distribution', '')} {self.repo_data.get('components', '')}"
        details_label = Gtk.Label(label=details_text)
        details_label.set_xalign(0)
        details_label.get_style_context().add_class('dim-label')
        details_label.set_attributes(Pango.AttrList.from_string("scale=0.9"))
        info_box.pack_start(details_label, True, True, 0)

        # Comment (if exists)
        if self.repo_data.get('comment'):
            comment_label = Gtk.Label(label=f"<i>{self.repo_data['comment']}</i>")
            comment_label.set_use_markup(True)
            comment_label.set_xalign(0)
            comment_label.set_attributes(Pango.AttrList.from_string("scale=0.85 foreground='#666666'"))
            info_box.pack_start(comment_label, False, False, 0)
        
        main_box.pack_start(info_box, True, True, 0)
        
        # Buttons Box
        buttons_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        
        # Edit Button
        edit_btn = Gtk.Button.new_from_icon_name("document-edit-symbolic", Gtk.IconSize.BUTTON)
        edit_btn.set_tooltip_text(_("Edit"))
        edit_btn.get_style_context().add_class('flat')
        edit_btn.connect('clicked', lambda b: self.on_edit(self.repo_data) if self.on_edit else None)
        buttons_box.pack_start(edit_btn, False, False, 0)
        
        # Delete Button
        delete_btn = Gtk.Button.new_from_icon_name("user-trash-symbolic", Gtk.IconSize.BUTTON)
        delete_btn.set_tooltip_text(_("Delete"))
        delete_btn.get_style_context().add_class('flat')
        delete_btn.get_style_context().add_class('destructive-action')
        delete_btn.connect('clicked', lambda b: self.on_delete(self.repo_data) if self.on_delete else None)
        buttons_box.pack_start(delete_btn, False, False, 0)
        
        main_box.pack_start(buttons_box, False, False, 0)
        
        self.add(main_box)
        self.show_all()
    
    def _on_switch_state_set(self, switch, state):
        """Handle switch toggle."""
        self.repo_data['disabled'] = not state
        if self.on_toggle:
            self.on_toggle(self.repo_data)
        return True # Prevent default handler which might toggle it back? No, standard GTK3 switch state-set needs return True to accept state?? usually return False for default.
        # Check docs: "True to stop the signal emission". 
        # Actually usually with state-set used for logic, we typically return False to let the switch animate.
        return False
