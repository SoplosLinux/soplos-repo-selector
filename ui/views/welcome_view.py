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
    """View for the Welcome tab.

    This view now mirrors the layout used in `soplos-welcome`: logo, title,
    description, a framed "features" area and a row of action buttons.
    """

    def __init__(self, main_window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        self.main_window = main_window

        # Margins to make it look similar to Soplos Welcome
        self.set_margin_left(20)
        self.set_margin_right(20)
        self.set_margin_top(10)
        self.set_margin_bottom(10)

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
        title_label = Gtk.Label()
        title_label.set_markup(f"<span size='xx-large' weight='bold'>{APP_NAME}</span>")
        title_label.get_style_context().add_class('h1')
        title_label.set_halign(Gtk.Align.CENTER)
        self.pack_start(title_label, False, False, 10)

        # Description Box
        desc_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        desc_box.set_size_request(540, -1)

        desc_text = _(
            "Welcome to the Advanced Repository Manager for Soplos Linux.\n\n"
            "This application will help you get started configuring repositories and mirrors for your system."
        )

        desc_label = Gtk.Label(label=desc_text)
        desc_label.set_justify(Gtk.Justification.CENTER)
        desc_label.set_line_wrap(True)
        desc_label.get_style_context().add_class('welcome-text')
        desc_box.pack_start(desc_label, False, False, 0)
        self.pack_start(desc_box, False, False, 0)

        # Features frame (like Soplos Welcome)
        features_frame = Gtk.Frame()
        features_frame.set_label(_("Use the tabs above to:"))
        # Centrar el texto de la etiqueta del frame como en Soplos Welcome
        try:
            features_frame.set_label_align(0.5, 0.5)
        except Exception:
            pass
        features_frame.set_margin_left(15)
        features_frame.set_margin_right(15)

        grid = Gtk.Grid()
        grid.set_column_spacing(24)
        grid.set_row_spacing(8)
        grid.set_margin_left(20)
        grid.set_margin_right(20)
        grid.set_margin_top(8)
        grid.set_margin_bottom(8)
        grid.set_halign(Gtk.Align.CENTER)

        features = [
            (_("• Generate optimized repository sources"), "network-server-symbolic"),
            (_("• Find fastest download mirrors"), "network-transmit-receive"),
            (_("• Manage repositories and GPG keys"), "security-high-symbolic"),
            (_("• Customize free / non-free components"), "preferences-desktop-theme")
        ]

        for i, (text, icon_name) in enumerate(features):
            try:
                icon = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.LARGE_TOOLBAR)
            except Exception:
                icon = Gtk.Image.new_from_icon_name("preferences-system", Gtk.IconSize.LARGE_TOOLBAR)
            icon.set_halign(Gtk.Align.CENTER)
            icon.set_valign(Gtk.Align.CENTER)
            grid.attach(icon, 0, i, 1, 1)

            label = Gtk.Label(label=text)
            label.set_halign(Gtk.Align.START)
            label.set_valign(Gtk.Align.CENTER)
            label.set_margin_left(8)
            grid.attach(label, 1, i, 1, 1)

        features_frame.add(grid)
        self.pack_start(features_frame, False, False, 8)

        # No action buttons here — UI kept minimal like Soplos Welcome.

    def _open_url(self, url):
        try:
            import webbrowser
            webbrowser.open(url)
        except Exception as e:
            print(f"Error opening URL {url}: {e}")

    def _on_get_started_clicked(self, button):
        # Try to switch the main notebook to page 1 (Sources Generator)
        try:
            if hasattr(self.main_window, 'notebook'):
                self.main_window.notebook.set_current_page(1)
        except Exception as e:
            print(f"Error switching to Sources tab: {e}")
