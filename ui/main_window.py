"""
Main Application Window.
Handles the main UI layout and interaction using Notebook Tabs.
Strict Soplos Welcome style: Header + Content (Tabs) + Footer.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib, Pango

from core.i18n_manager import _
from config.constants import APP_NAME, APP_VERSION, DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT
from ui.views.repo_view import RepoView
from ui.views.gpg_view import GPGView
from ui.views.sources_generator_view import SourcesGeneratorView
from ui.views.welcome_view import WelcomeView

class MainWindow(Gtk.ApplicationWindow):
    def _setup_ui(self):
        """Inicializa la interfaz principal, igualando la estructura de Welcome."""
        main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(main_vbox)

        # --- Barra de progreso oculta (arriba) ---
        self.progress_revealer = Gtk.Revealer()
        self.progress_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)

        progress_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        progress_box.set_margin_top(10)
        progress_box.set_margin_bottom(10)
        progress_box.set_margin_start(20)
        progress_box.set_margin_end(20)

        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_show_text(True)
        progress_box.pack_start(self.progress_bar, False, False, 0)

        self.progress_label = Gtk.Label(label=_("Ready"))
        progress_box.pack_start(self.progress_label, False, False, 0)

        self.progress_revealer.add(progress_box)
        main_vbox.pack_start(self.progress_revealer, False, False, 0)

        # --- Contenido de pestañas ---
        self.notebook = Gtk.Notebook()
        self.notebook.set_scrollable(True)
        self.notebook.set_tab_pos(Gtk.PositionType.TOP)
        self.notebook.set_show_tabs(True)
        self.notebook.set_show_border(False)
        try:
            self.notebook.get_style_context().add_class('soplos-notebook')
        except Exception:
            pass
        try:
            self._apply_notebook_custom_css()
        except Exception:
            pass
        main_vbox.pack_start(self.notebook, True, True, 0)

        # Pestaña 1: Welcome
        self.welcome_view = WelcomeView(self)
        self._add_tab(self.welcome_view, _("Welcome"), "user-home")

        # Pestaña 2: Sources Generator
        self.sources_view = SourcesGeneratorView(self)
        self._add_tab(self.sources_view, _("Sources Generator"), "network-server-symbolic")

        # Pestaña 3: Repositorios
        self.repo_view = RepoView(self)
        self._add_tab(self.repo_view, _("Repositories"), "software-properties")

        # Pestaña 4: GPG Keys
        self.gpg_view = GPGView(self)
        self._add_tab(self.gpg_view, _("GPG Keys"), "security-high-symbolic")

        # --- Footer (Status Bar) ---
        self._create_status_bar(main_vbox)
    def __init__(self, application, environment_detector, theme_manager, i18n_manager):
        super().__init__(application=application)
        self.application = application
        self.environment_detector = environment_detector
        self.theme_manager = theme_manager
        self.i18n_manager = i18n_manager
        self.set_title(_(APP_NAME))
        self.set_default_size(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.get_style_context().add_class('soplos-window')
        self._create_header_bar_with_fallback()
        self._setup_ui()
        self.show_all()
        GLib.idle_add(lambda: self.notebook.set_current_page(0))
        self._update_system_info()
        """Inicializa la interfaz principal, igualando la estructura de Welcome."""
        main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(main_vbox)

        # --- Barra de progreso oculta (arriba) ---
        self.progress_revealer = Gtk.Revealer()
        self.progress_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)

        progress_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        progress_box.set_margin_top(10)
        progress_box.set_margin_bottom(10)
        progress_box.set_margin_start(20)
        progress_box.set_margin_end(20)

        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_show_text(True)
        progress_box.pack_start(self.progress_bar, False, False, 0)

        self.progress_label = Gtk.Label(label=_("Ready"))
        progress_box.pack_start(self.progress_label, False, False, 0)

        self.progress_revealer.add(progress_box)
        main_vbox.pack_start(self.progress_revealer, False, False, 0)

        # --- Contenido de pestañas ---
        self.notebook = Gtk.Notebook()
        self.notebook.set_scrollable(True)
        self.notebook.set_tab_pos(Gtk.PositionType.TOP)
        self.notebook.set_show_tabs(True)
        self.notebook.set_show_border(False)
        try:
            self.notebook.get_style_context().add_class('soplos-notebook')
        except Exception:
            pass
        try:
            self._apply_notebook_custom_css()
        except Exception:
            pass
        main_vbox.pack_start(self.notebook, True, True, 0)

        # Pestaña 1: Welcome
        self.welcome_view = WelcomeView(self)
        self._add_tab(self.welcome_view, _("Welcome"), "user-home")

        # Pestaña 2: Sources Generator
        self.sources_view = SourcesGeneratorView(self)
        self._add_tab(self.sources_view, _("Sources Generator"), "network-server-symbolic")

        # Pestaña 3: Repositorios
        self.repo_view = RepoView(self)
        self._add_tab(self.repo_view, _("Repositories"), "software-properties")

        # Pestaña 4: GPG Keys
        self.gpg_view = GPGView(self)
        self._add_tab(self.gpg_view, _("GPG Keys"), "security-high-symbolic")

        # --- Footer (Status Bar) ---
        self._create_status_bar(main_vbox)

    def _create_header_bar_with_fallback(self):
        """Crea el HeaderBar moderno, con fallback a decoraciones nativas en XFCE/KDE."""
        desktop_env = 'unknown'
        try:
            if self.environment_detector:
                desktop_env = getattr(self.environment_detector.desktop_environment, 'value', str(self.environment_detector.desktop_environment)).lower()
        except Exception:
            pass
        # Si es XFCE/KDE, usar decoraciones nativas
        if desktop_env in ['xfce', 'kde', 'plasma']:
            return
        # Si es GNOME u otros, usar CSD
        header = Gtk.HeaderBar()
        header.set_show_close_button(True)
        header.set_title(_(APP_NAME))
        try:
            header.set_has_subtitle(True)
            header.set_subtitle(f"v{APP_VERSION}")
        except Exception:
            pass
        header.set_decoration_layout("menu:minimize,maximize,close")
        header.get_style_context().add_class('titlebar')
        self._add_header_buttons(header)
        self.set_titlebar(header)
        self.header = header

    def _create_language_menu(self):
        """Crea el menú de selección de idioma."""
        menu = Gtk.Menu()
        available_languages = self.i18n_manager.SUPPORTED_LANGUAGES
        current_lang = self.i18n_manager.current_language
        for lang_code, lang_name in available_languages.items():
            item = Gtk.CheckMenuItem(label=f"{lang_name} ({lang_code.upper()})")
            item.set_active(lang_code == current_lang)
            item.connect('activate', self._on_language_changed, lang_code)
            menu.append(item)
        menu.show_all()
        return menu

    def _on_language_changed(self, widget, lang_code):
        self.i18n_manager.set_language(lang_code)
        # Aquí podrías recargar la UI si es necesario

    def _on_theme_toggle(self, widget):
        # Cambia el tema (implementación básica, puedes mejorarla)
        if hasattr(self.theme_manager, 'toggle_theme'):
            self.theme_manager.toggle_theme()

    # ...existing code...

        # Main Layout (Vertical)
        main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(main_vbox)
        
        # --- HIDDEN PROGRESS BAR (Top of content) ---
        self.progress_revealer = Gtk.Revealer()
        self.progress_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)
        
        progress_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        progress_box.set_margin_top(10)
        progress_box.set_margin_bottom(10)
        progress_box.set_margin_start(20)
        progress_box.set_margin_end(20)
        
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_show_text(True)
        progress_box.pack_start(self.progress_bar, False, False, 0)
        
        self.progress_label = Gtk.Label(label=_("Ready"))
        progress_box.pack_start(self.progress_label, False, False, 0)
        
        self.progress_revealer.add(progress_box)
        main_vbox.pack_start(self.progress_revealer, False, False, 0)
        
        # --- TAB CONTENT ---
        self.notebook = Gtk.Notebook()
        self.notebook.set_scrollable(True)
        self.notebook.set_tab_pos(Gtk.PositionType.TOP)
        # Mostrar siempre las pestañas para coincidir con Soplos Welcome
        self.notebook.set_show_tabs(True)
        self.notebook.set_show_border(False)
        # Añadir clase de estilo para permitir personalizaciones CSS si existen
        try:
            self.notebook.get_style_context().add_class('soplos-notebook')
        except Exception:
            pass
        # Apply the same custom notebook CSS as Soplos Welcome
        try:
            self._apply_notebook_custom_css()
        except Exception:
            pass
        main_vbox.pack_start(self.notebook, True, True, 0)
        
        # Tab 1: Welcome (Inicio)
        self.welcome_view = WelcomeView(self)
        self._add_tab(self.welcome_view, _("Welcome"), "user-home")
        
        # Tab 2: Sources Generator
        self.sources_view = SourcesGeneratorView(self)
        self._add_tab(self.sources_view, _("Sources Generator"), "network-server-symbolic")
        
        # Tab 3: Repository Management
        self.repo_view = RepoView(self)
        self._add_tab(self.repo_view, _("Repositories"), "software-properties")
        
        # Tab 4: GPG Keys
        self.gpg_view = GPGView(self)
        self._add_tab(self.gpg_view, _("GPG Keys"), "security-high-symbolic")
        
        # --- FOOTER (Status Bar) ---
        self._create_status_bar(main_vbox)
        
        # Add window style class
        self.get_style_context().add_class('soplos-window')
        
    def _create_status_bar(self, main_vbox):
        """Create footer status bar."""
        status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        status_box.set_margin_start(15)
        status_box.set_margin_end(15)
        status_box.set_margin_top(8)
        status_box.set_margin_bottom(8)
        
        # Left: System Info
        self.system_label = Gtk.Label()
        self.system_label.set_halign(Gtk.Align.START)
        self.system_label.get_style_context().add_class('dim-label')
        status_box.pack_start(self.system_label, False, False, 0)
        
        # Right: App Version
        version_text = f"{APP_NAME} v{APP_VERSION}"
        version_label = Gtk.Label(label=version_text)
        version_label.set_halign(Gtk.Align.END)
        version_label.get_style_context().add_class('dim-label')
        status_box.pack_end(version_label, False, False, 0)
        
        main_vbox.pack_end(status_box, False, False, 0)

    def _update_system_info(self):
        """Detect and display system info."""
        env_info = self.environment_detector.detect_all()
        desktop = env_info['desktop_environment']
        protocol = env_info['display_protocol']
        
        # Translate codes to nice names
        desktop_map = {
            'gnome': 'GNOME',
            'plasma': 'KDE Plasma',
            'xfce': 'XFCE',
            'cinnamon': 'Cinnamon'
        }
        name = desktop_map.get(desktop, desktop.upper())
        proto = "Wayland" if str(protocol).endswith('WAYLAND') else "X11"
        
        self.system_label.set_text(_("Running on {} ({})").format(name, proto))

    def _add_tab(self, content_widget, title, icon_name):
        """Helper to add tabs with icons."""
        label_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        icon = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.MENU)
        label = Gtk.Label(label=title)
        
        label_box.pack_start(icon, False, False, 0)
        label_box.pack_start(label, False, False, 0)
        label_box.show_all()
        
        self.notebook.append_page(content_widget, label_box)

    def _apply_notebook_custom_css(self):
        """Apply custom CSS to make the notebook tab bar thicker (copied from Soplos Welcome)."""
        css_provider = Gtk.CssProvider()
        css_data = """
        notebook > header {
            min-height: 20px;
            padding: 0px 0;
        }
        
        notebook > header > tabs > tab {
            min-height: 20px;
            padding: 8px 12px;
        }
        
        notebook > header > tabs > tab label {
            padding: 4px 8px;
        }
        """
        try:
            css_provider.load_from_data(css_data.encode('utf-8'))
            screen = Gdk.Screen.get_default()
            style_context = Gtk.StyleContext()
            style_context.add_provider_for_screen(
                screen,
                css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
        except Exception as e:
            print(f"Error applying notebook CSS: {e}")
    
    def _create_menu(self, header):
        """Create the hamburger menu."""
        menu = Gtk.Menu()
        
        item_about = Gtk.MenuItem(label=_("About"))
        item_about.connect("activate", self._on_about_clicked)
        menu.append(item_about)
        
        menu.show_all()
        
        menu_button = Gtk.MenuButton()
        menu_button.set_image(Gtk.Image.new_from_icon_name("open-menu-symbolic", Gtk.IconSize.BUTTON))
        menu_button.set_popup(menu)
        
        header.pack_end(menu_button)
    
    def _on_about_clicked(self, widget):
        about = Gtk.AboutDialog()
        about.set_program_name(APP_NAME)
        about.set_version(APP_VERSION)
        about.set_copyright("© 2025 Soplos Linux")
        about.set_comments(_("Advanced Repository Manager"))
        about.set_website("https://soploslinux.com")
        about.set_logo_icon_name("system-software-install")
        about.set_transient_for(self)
        about.run()
        about.destroy()
