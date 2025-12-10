"""
GPG Keys View.
Displays and manages GPG keys.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

from core.i18n_manager import _
from services.gpg_manager import get_gpg_manager

class GPGView(Gtk.Box):
    """View for managing GPG keys."""
    
    def __init__(self, main_window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.main_window = main_window
        self.gpg_manager = get_gpg_manager()
        self.keys = []
        
        self._create_ui()
        self.refresh_keys()
    
    def _create_ui(self):
        """Create view UI."""
        self.set_margin_top(10)
        self.set_margin_bottom(10)
        self.set_margin_start(10)
        self.set_margin_end(10)
        
        # Toolbar
        action_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        
        import_btn = Gtk.Button(label=_("Import Key"))
        image = Gtk.Image.new_from_icon_name("document-import-symbolic", Gtk.IconSize.BUTTON)
        import_btn.set_image(image)
        import_btn.connect("clicked", self._on_import_clicked)
        action_bar.pack_start(import_btn, False, False, 0)
        
        refresh_btn = Gtk.Button.new_from_icon_name("view-refresh-symbolic", Gtk.IconSize.BUTTON)
        refresh_btn.set_tooltip_text(_("Refresh"))
        refresh_btn.connect("clicked", lambda b: self.refresh_keys())
        action_bar.pack_start(refresh_btn, False, False, 0)
        
        self.pack_start(action_bar, False, False, 0)
        
        # List container
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)
        
        frame = Gtk.Frame()
        frame.get_style_context().add_class('view')
        
        self.list_box = Gtk.ListBox()
        self.list_box.set_selection_mode(Gtk.SelectionMode.NONE)
        frame.add(self.list_box)
        scrolled.add(frame)
        self.pack_start(scrolled, True, True, 0)
        
    def refresh_keys(self):
        for row in self.list_box.get_children():
            self.list_box.remove(row)
            
        self.keys = self.gpg_manager.get_all_keys()
        
        if not self.keys:
            # Show placeholder
            pass
            
        for key in self.keys:
            row = Gtk.ListBoxRow()
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            box.set_margin_top(8)
            box.set_margin_bottom(8)
            box.set_margin_start(12)
            box.set_margin_end(12)
            
            icon = Gtk.Image.new_from_icon_name("application-certificate-symbolic", Gtk.IconSize.LARGE_TOOLBAR)
            icon.set_opacity(0.6)
            box.pack_start(icon, False, False, 0)
            
            info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            name_label = Gtk.Label(label=key['name'])
            name_label.set_xalign(0)
            name_label.get_style_context().add_class('bold')
            info_box.pack_start(name_label, True, True, 0)
            
            desc_label = Gtk.Label(label=key['description'])
            desc_label.set_xalign(0)
            desc_label.get_style_context().add_class('dim-label')
            info_box.pack_start(desc_label, True, True, 0)
            
            box.pack_start(info_box, True, True, 0)
            
            row.add(box)
            self.list_box.add(row)
            
        self.list_box.show_all()
    
    def _on_import_clicked(self, btn):
        dialog = Gtk.FileChooserDialog(
            title=_("Import GPG Key"),
            parent=self.main_window,
            action=Gtk.FileChooserAction.OPEN,
        )
        dialog.add_buttons(
            _("Cancel"), Gtk.ResponseType.CANCEL,
            _("Import"), Gtk.ResponseType.ACCEPT
        )
        
        filter_gpg = Gtk.FileFilter()
        filter_gpg.set_name("GPG Keys")
        filter_gpg.add_pattern("*.gpg")
        filter_gpg.add_pattern("*.asc")
        filter_gpg.add_pattern("*.pgp")
        dialog.add_filter(filter_gpg)
        
        response = dialog.run()
        if response == Gtk.ResponseType.ACCEPT:
            filename = dialog.get_filename()
            dialog.destroy()
            
            success, msg = self.gpg_manager.import_key_from_file(filename)
            if success:
                self.refresh_keys()
                # Show toast/message?
            else:
                md = Gtk.MessageDialog(
                    parent=self.main_window,
                    flags=0,
                    message_type=Gtk.MessageType.ERROR,
                    buttons=Gtk.ButtonsType.OK,
                    text=_("Import Error")
                )
                md.format_secondary_text(msg)
                md.run()
                md.destroy()
        else:
            dialog.destroy()
