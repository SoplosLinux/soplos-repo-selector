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

            # Details column (fingerprint, expiry)
            details = self.gpg_manager.get_key_details(key['path']) or {}
            details_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            fpr = details.get('fingerprint') or ''
            expiry = details.get('expiry') or ''
            fpr_label = Gtk.Label(label=fpr)
            fpr_label.set_xalign(0)
            fpr_label.get_style_context().add_class('dim-label')
            details_box.pack_start(fpr_label, True, True, 0)

            expiry_label = Gtk.Label(label=expiry)
            expiry_label.set_xalign(0)
            expiry_label.get_style_context().add_class('dim-label')
            details_box.pack_start(expiry_label, True, True, 0)

            box.pack_start(details_box, False, False, 0)

            # Actions column (Export / Delete)
            action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            export_btn = Gtk.Button(label=_("Exportar"))
            export_btn.connect('clicked', self._on_export_clicked, key)
            action_box.pack_start(export_btn, False, False, 0)

            delete_btn = Gtk.Button(label=_("Borrar"))
            # attach a small state to manage confirm-once behavior
            delete_btn._confirm_state = False
            delete_btn.connect('clicked', self._on_delete_clicked, key, delete_btn)
            action_box.pack_start(delete_btn, False, False, 0)

            box.pack_start(action_box, False, False, 0)
            
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

    def _on_export_clicked(self, btn, key):
        dialog = Gtk.FileChooserDialog(
            title=_("Export Key"),
            parent=self.main_window,
            action=Gtk.FileChooserAction.SAVE,
        )
        dialog.add_buttons(
            _("Cancel"), Gtk.ResponseType.CANCEL,
            _("Save"), Gtk.ResponseType.ACCEPT
        )
        dialog.set_do_overwrite_confirmation(True)

        response = dialog.run()
        if response == Gtk.ResponseType.ACCEPT:
            dst = dialog.get_filename()
            dialog.destroy()
            success, msg = self.gpg_manager.export_key(key['path'], dst)
            if success:
                self.refresh_keys()
            else:
                md = Gtk.MessageDialog(
                    parent=self.main_window,
                    flags=0,
                    message_type=Gtk.MessageType.ERROR,
                    buttons=Gtk.ButtonsType.OK,
                    text=_("Export Error")
                )
                md.format_secondary_text(msg)
                md.run()
                md.destroy()
        else:
            dialog.destroy()

    def _on_delete_clicked(self, btn, key, delete_btn):
        # Two-step inline confirmation: first click arms the button, second click deletes.
        if not getattr(delete_btn, '_confirm_state', False):
            delete_btn.set_label(_('Confirmar borrar'))
            delete_btn._confirm_state = True

            def reset_label():
                try:
                    delete_btn.set_label(_('Borrar'))
                    delete_btn._confirm_state = False
                except Exception:
                    pass
                return False

            # reset after 5 seconds if no confirmation
            GLib.timeout_add_seconds(5, reset_label)
            return

        # Proceed to delete
        success, msg = self.gpg_manager.delete_key(key['path'], force=False)
        if success:
            self.refresh_keys()
        else:
            md = Gtk.MessageDialog(
                parent=self.main_window,
                flags=0,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text=_('Delete Error')
            )
            md.format_secondary_text(msg)
            md.run()
            md.destroy()
