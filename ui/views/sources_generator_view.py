"""
Sources Generator View.
Tab 1: Select Distribution, Components, and Mirror to generate sources.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

from core.i18n_manager import _
from services.speed_test_service import RepoSpeedTester
from services.repo_manager import get_repo_manager
from ui.dialogs.speed_test import SpeedTestDialog

class SourcesGeneratorView(Gtk.Box):
    """View for generating main APT sources."""
    
    def __init__(self, main_window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        self.main_window = main_window
        self.repo_manager = get_repo_manager()
        
        # Defaults - Soplos Hybrid Mode (Trixie + Testing)
        # Using a set for selected distros to handle multi-selection
        self.selected_distros = {'trixie', 'testing'}
        self.backports_enabled = True # User asked for Backports checkbox
        
        self.selected_components = {
            "main": True,
            "contrib": True,
            "non-free": True,
            "non-free-firmware": True
        }
        
        self._create_ui()
    
    def _create_ui(self):
        self.set_margin_top(20)
        self.set_margin_bottom(20)
        self.set_margin_start(20)
        self.set_margin_end(20)
        
        # 1. Distribution Selection (Multi-select Checkboxes)
        dist_frame = Gtk.Frame(label=_("1. Select Debian Distribution(s)"))
        dist_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        dist_box.set_margin_top(10)
        dist_box.set_margin_bottom(10)
        dist_box.set_margin_start(10)
        dist_box.set_margin_end(10)
        
        # Requested list: Trixie, Forky, Testing, Backports, Sid, Unstable
        # Note: Backports is special, it applies to others.
        
        self.dist_checks = {}
        distributions = [
            ("trixie", _("Debian 13 (Trixie)")),
            ("forky", _("Debian 14 (Forky)")),
            ("testing", _("Testing")),
            ("sid", _("Sid")),
            ("unstable", _("Unstable")),
            ("experimental", _("Experimental"))
        ]
        
        for id, name in distributions:
            chk = Gtk.CheckButton(label=name)
            chk.set_active(id in self.selected_distros)
            chk.connect("toggled", self._on_dist_toggled, id)
            self.dist_checks[id] = chk
            dist_box.pack_start(chk, False, False, 0)
            
        # Backports Checkbox (Separate because it's a modifier)
        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        dist_box.pack_start(sep, False, False, 5)
        
        self.backports_check = Gtk.CheckButton(label=_("Include Backports"))
        self.backports_check.set_active(self.backports_enabled)
        self.backports_check.connect("toggled", self._on_backports_toggled)
        dist_box.pack_start(self.backports_check, False, False, 0)
            
        dist_frame.add(dist_box)
        self.pack_start(dist_frame, False, False, 0)
        
        # 2. Components Selection
        comp_frame = Gtk.Frame(label=_("2. Select Components"))
        comp_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        comp_box.set_margin_top(10)
        comp_box.set_margin_bottom(10)
        comp_box.set_margin_start(10)
        comp_box.set_margin_end(10)
        
        self.comp_checks = {}
        components = [
            ("main", _("Main (Free Software)")),
            ("contrib", _("Contrib (Drivers/Packages relying on non-free)")),
            ("non-free", _("Non-Free (Proprietary software)")),
            ("non-free-firmware", _("Non-Free Firmware (Hardware support)"))
        ]
        
        for id, name in components:
            chk = Gtk.CheckButton(label=name)
            chk.set_active(self.selected_components.get(id, False))
            chk.connect("toggled", self._on_comp_toggled, id)
            self.comp_checks[id] = chk
            comp_box.pack_start(chk, False, False, 0)
            
        comp_frame.add(comp_box)
        self.pack_start(comp_frame, False, False, 0)
        
        # 3. Mirror Selection
        mirror_frame = Gtk.Frame(label=_("3. Select Mirror"))
        mirror_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        mirror_box.set_margin_top(10)
        mirror_box.set_margin_bottom(10)
        mirror_box.set_margin_start(10)
        mirror_box.set_margin_end(10)
        
        self.mirror_label = Gtk.Label(label=_("Current: http://deb.debian.org/debian (Global CDN)"))
        self.mirror_label.set_xalign(0)
        mirror_box.pack_start(self.mirror_label, False, False, 0)
        self.selected_mirror_url = "http://deb.debian.org/debian"
        
        speed_btn = Gtk.Button(label=_("Find Fastest Mirror"))
        icon = Gtk.Image.new_from_icon_name("network-wireless-symbolic", Gtk.IconSize.BUTTON)
        speed_btn.set_image(icon)
        speed_btn.connect("clicked", self._on_speed_test_clicked)
        mirror_box.pack_start(speed_btn, False, False, 0)
        
        mirror_frame.add(mirror_box)
        self.pack_start(mirror_frame, False, False, 0)
        
        # Action Buttons
        actions_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        actions_box.set_halign(Gtk.Align.END)
        
        apply_btn = Gtk.Button(label=_("Generate Source List"))
        apply_btn.get_style_context().add_class('suggested-action')
        apply_btn.connect("clicked", self._on_generate_clicked)
        actions_box.pack_start(apply_btn, False, False, 0)
        
        self.pack_start(actions_box, False, False, 0)
        
    def _on_dist_toggled(self, button, dist_id):
        if button.get_active():
            self.selected_distros.add(dist_id)
        else:
            self.selected_distros.discard(dist_id)
            
    def _on_backports_toggled(self, button):
        self.backports_enabled = button.get_active()
            
    def _on_comp_toggled(self, button, comp_id):
        self.selected_components[comp_id] = button.get_active()
        
    def _on_speed_test_clicked(self, btn):
        dialog = SpeedTestDialog(self.main_window)
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            best = dialog.get_selected_mirror()
            dialog.destroy()
            if best:
                self.selected_mirror_url = best['url']
                self.mirror_label.set_text(_("Current: {} ({}, {:.2f} MB/s)").format(
                    best['url'], best['country'], best['speed_mbps']
                ))
        else:
            dialog.destroy()
            
    def _on_generate_clicked(self, btn):
        if not self.selected_distros:
            self._show_msg(Gtk.MessageType.WARNING, _("Warning"), _("Please select at least one distribution."))
            return

        comps_list = [k for k, v in self.selected_components.items() if v]
        comps_str = " ".join(comps_list)
        
        repos = []
        keyring = '/usr/share/keyrings/debian-archive-keyring.gpg'
        
        # Generate entries for each selected distro
        for distro in self.selected_distros:
            # Main Repo
            repos.append(self._make_repo(distro, comps_str, keyring, 'debian.sources'))
            
            # Skip Updates/Security for Unstable/Sid/Experimental?
            # Generally:
            # Sid/Unstable/Experimental DO NOT have -updates or -security (in the traditional sense)
            # Trixie/Testing/Forky DO have them.
            
            is_unstable_type = distro in ['sid', 'unstable', 'experimental']
            
            if not is_unstable_type:
                # -updates
                repos.append(self._make_repo(f"{distro}-updates", comps_str, keyring, 'debian.sources'))
                
                # -proposed-updates (Often useful for Testing, maybe not default? Let's include if it's Testing)
                if distro == 'testing':
                     repos.append(self._make_repo(f"{distro}-proposed-updates", comps_str, keyring, 'debian.sources'))
                
                # Security
                sec_uri = 'https://security.debian.org/debian-security/'
                # Note: Testing uses 'testing-security' (or stable-security format).
                # Trixie uses 'trixie-security'.
                sec_distro = f"{distro}-security"
                repos.append(self._make_repo(sec_distro, comps_str, keyring, 'debian-security.sources', sec_uri))
                
                # Backports (If enabled globally)
                if self.backports_enabled:
                    repos.append(self._make_repo(f"{distro}-backports", comps_str, keyring, 'debian-backports.sources'))

        success = self.repo_manager.save_repos(repos)
        
        if success:
             self._show_msg(Gtk.MessageType.INFO, _("Sources Generated"), 
                            _("Your sources have been updated successfully."))
        else:
             self._show_msg(Gtk.MessageType.ERROR, _("Error"), 
                            _("Could not save sources files. Check permissions."))

    def _make_repo(self, suite, components, signed_by, filename, uri=None):
        """Helper to create repo dict."""
        if not uri:
            uri = self.selected_mirror_url
            
        return {
            'type': 'deb',
            'uri': uri,
            'distribution': suite,
            'components': components,
            'signed_by': signed_by,
            'file': f'/etc/apt/sources.list.d/{filename}',
            'format': 'deb822'
        }

    def _show_msg(self, msg_type, title, text):
        dialog = Gtk.MessageDialog(
            transient_for=self.main_window,
            flags=0,
            message_type=msg_type,
            buttons=Gtk.ButtonsType.OK,
            text=title
        )
        dialog.format_secondary_text(text)
        dialog.run()
        dialog.destroy()
