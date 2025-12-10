"""
Welcome View (Tab 1).
Startup screen with logo and description.
"""

import os
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf

from core.i18n_manager import _
from config.constants import APP_NAME

class WelcomeView(Gtk.Box):
    """View for the Welcome tab."""
    
    def __init__(self, main_window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        self.main_window = main_window
        
        self._create_ui()
    
    def _create_ui(self):
        self.set_valign(Gtk.Align.CENTER)
        self.set_halign(Gtk.Align.CENTER)
        
        # Logo
        logo_path = os.path.join(os.path.dirname(__file__), '../../assets/icons/logo.png')
        if os.path.exists(logo_path):
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(logo_path, 128, 128, True)
                image = Gtk.Image.new_from_pixbuf(pixbuf)
            except Exception as e:
                print(f"Error loading logo: {e}")
                image = Gtk.Image.new_from_icon_name("system-software-install", Gtk.IconSize.DIALOG)
        else:
            image = Gtk.Image.new_from_icon_name("system-software-install", Gtk.IconSize.DIALOG)
            
        self.pack_start(image, False, False, 0)
        
        # Title
        title_label = Gtk.Label(label=_(APP_NAME))
        title_label.get_style_context().add_class('h1')
        title_label.set_use_markup(True)
        # Force larger font via markup if css class h1 isn't enough in base theme
        title_label.set_markup(f"<span size='xx-large' weight='bold'>{APP_NAME}</span>")
        self.pack_start(title_label, False, False, 10)
        
        # Description Box
        desc_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        desc_box.set_size_request(500, -1)
        
        desc_text = _(
            "Welcome to the Advanced Repository Manager for Soplos Linux.\n\n"
            "This tool allows you to:\n"
            "• Generate optimized repository sources for your Debian version.\n"
            "• Find and select the fastest download mirrors.\n"
            "• Manage third-party repositories and GPG keys.\n"
            "• Customize free and non-free software components."
        )
        
        desc_label = Gtk.Label(label=desc_text)
        desc_label.set_justify(Gtk.Justification.CENTER)
        desc_label.set_line_wrap(True) # Corrected method
        desc_label.get_style_context().add_class('welcome-text')
        
        desc_box.pack_start(desc_label, False, False, 0)
        self.pack_start(desc_box, False, False, 0)
