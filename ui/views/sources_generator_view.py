"""
Sources Generator View.
Tab 1: Select Distribution, Components, and Mirror to generate sources.
"""

import gi
import threading
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

from core.i18n_manager import _
from services.speed_test_service import RepoSpeedTester
from services.repo_manager import get_repo_manager


class SourcesGeneratorView(Gtk.Box):
    """View for generating main APT sources."""
    
    # Known distributions to detect
    KNOWN_DISTROS = ['trixie', 'forky', 'testing', 'sid', 'unstable', 'experimental']
    # Known components to detect
    KNOWN_COMPONENTS = ['main', 'contrib', 'non-free', 'non-free-firmware']
    
    def __init__(self, main_window):
        # Reduce overall spacing to compact vertical gaps
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.main_window = main_window
        self.repo_manager = get_repo_manager()
        self.tester = RepoSpeedTester()
        self.speed_results = []
        # Track row widgets to update progress bars when max speed changes
        self.row_widgets = {}
        self.max_speed_seen = 1.0
        
        # Detect current system state instead of hardcoding defaults
        self.selected_distros, self.backports_enabled, self.selected_components = self._detect_system_state()
        
        self._create_ui()
    
    def _detect_system_state(self):
        """
        Detect the current system state by reading active repositories.
        Only considers MAIN repos (not -updates, -security, etc.) to determine
        which distributions are actually enabled.
        Returns: (selected_distros: set, backports_enabled: bool, selected_components: dict)
        """
        selected_distros = set()
        backports_enabled = False
        selected_components = {comp: False for comp in self.KNOWN_COMPONENTS}
        
        # Suffixes that indicate derivative repos (not main distro selection)
        DERIVATIVE_SUFFIXES = ['-updates', '-security', '-proposed', '-backports']
        
        try:
            # Get all repos from system (force fresh read, no cache)
            repos = self.repo_manager.get_all_repos(use_cache=False)
            
            for repo in repos:
                # Skip disabled repos
                if repo.get('disabled', False):
                    continue
                
                distribution = repo.get('distribution', '').lower()
                components = repo.get('components', '').lower()
                uri = repo.get('uri', '').lower()
                
                # Only consider Debian repos (skip third-party repos)
                if not any(d in uri for d in ['debian.org', 'deb.debian.org', 'security.debian.org']):
                    continue
                
                # Detect backports (just flag, don't add base distro from here)
                if '-backports' in distribution:
                    backports_enabled = True
                    continue
                
                # Skip -updates, -security, -proposed (they follow main distro)
                if any(suffix in distribution for suffix in DERIVATIVE_SUFFIXES):
                    continue
                
                # Only detect MAIN distribution repos (exact match)
                if distribution in self.KNOWN_DISTROS:
                    selected_distros.add(distribution)
                    
                    # Only count components from main repos
                    for comp in self.KNOWN_COMPONENTS:
                        if comp in components:
                            selected_components[comp] = True
        
        except Exception as e:
            print(f"Error detecting system state: {e}")
            # Return empty defaults on error - user starts fresh
        
        return selected_distros, backports_enabled, selected_components
    
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

        # Arrange Distribution and Components side-by-side in two columns
        # Slightly tighter columns spacing to reclaim vertical space
        top_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        top_box.set_homogeneous(False)

        # Let frames expand to share available vertical space and reduce left-alignment
        dist_frame.set_hexpand(True)
        dist_frame.set_vexpand(True)
        comp_frame.set_hexpand(True)
        comp_frame.set_vexpand(True)

        top_box.pack_start(dist_frame, True, True, 0)
        top_box.pack_start(comp_frame, True, True, 0)

        self.pack_start(top_box, False, False, 0)
        
        # 3. Mirror Selection
        mirror_frame = Gtk.Frame(label=_("3. Select Mirror"))
        # Compact mirror area margins so more vertical room is available
        mirror_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        mirror_box.set_margin_top(6)
        mirror_box.set_margin_bottom(6)
        mirror_box.set_margin_start(8)
        mirror_box.set_margin_end(8)
        # Make mirror_frame expand to fill the same width as top frames
        try:
            mirror_frame.set_hexpand(True)
            mirror_frame.set_halign(Gtk.Align.FILL)
        except Exception:
            pass
        
        self.selected_mirror_url = "http://deb.debian.org/debian"
        self.mirror_label = Gtk.Label(label=_("Current: {} (Global CDN)").format(self.selected_mirror_url))
        self.mirror_label.set_xalign(0)
        mirror_box.pack_start(self.mirror_label, False, False, 0)
        
        # Note: the speed test trigger button is placed with the action buttons
        # (created later) so the central mirror area remains free for results.
        # Inline results list (updates as mirrors are tested)
        self.status_label = Gtk.Label(label="")
        self.status_label.set_xalign(0)
        mirror_box.pack_start(self.status_label, False, False, 0)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)
        # Ensure results list has a reasonable visible height so rows are readable
        try:
            scrolled.set_min_content_height(240)
        except Exception:
            pass
        self.list_box = Gtk.ListBox()
        self.list_box.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.list_box.connect('row-activated', self._on_result_selected)
        scrolled.add(self.list_box)

        # Put the scrolled results inside the same mirror box so the frame
        # containing the mirror label and the results shares the same width
        mirror_box.pack_start(scrolled, True, True, 6)
        mirror_frame.add(mirror_box)
        # Make the mirror frame expand to fill available width (so it matches results)
        self.pack_start(mirror_frame, True, True, 0)
        
        # Action Buttons
        actions_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        actions_box.set_halign(Gtk.Align.END)
        
        speed_btn = Gtk.Button(label=_("Find Fastest Mirror"))
        speed_icon = Gtk.Image.new_from_icon_name("network-wireless-symbolic", Gtk.IconSize.BUTTON)
        speed_btn.set_image(speed_icon)
        speed_btn.connect("clicked", self._on_speed_test_clicked)
        actions_box.pack_start(speed_btn, False, False, 0)

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
        
    def _run_speed_test(self, trigger_button):
        """Run the speed test service and update UI via callbacks."""
        try:
            results = self.tester.test_mirrors_parallel(callback=self._speed_result_callback)
            GLib.idle_add(self._on_speed_test_finished, results, trigger_button)
        except Exception as e:
            print(f"Speed test error: {e}")
            GLib.idle_add(self._on_speed_test_finished, [], trigger_button)

    def _speed_result_callback(self, result: dict):
        # Called from worker thread for each mirror; schedule UI update
        GLib.idle_add(self._on_single_result, result)

    def _on_single_result(self, result: dict):
        """Update UI for a single mirror result - with dynamic progress bars."""
        try:
            url = result.get('url', '')
            status = result.get('status', '')
            progress = result.get('progress', 0.0)
            speed = float(result.get('speed_mbps', 0) or 0.0)
            latency = float(result.get('latency_ms', 0) or 0.0)
            country = result.get('country', _("Unknown"))
            
            # Update max speed seen
            if speed > self.max_speed_seen:
                self.max_speed_seen = speed
            
            # Check if row already exists for this URL
            existing_row = self.row_widgets.get(url)
            
            if existing_row:
                # Update existing row's progress bar and labels
                widgets = existing_row
                
                # Update progress bar
                if status in ['success', 'error', 'timeout', 'connection_failed', 'no_valid_files']:
                    # Final state - show speed comparison
                    if self.max_speed_seen > 0 and speed > 0:
                        frac = min(1.0, speed / self.max_speed_seen)
                    else:
                        frac = 0.0
                    widgets['progress'].set_fraction(frac)
                    widgets['progress'].set_text(f"{speed:.2f} MB/s")
                else:
                    # In-progress - show download progress
                    widgets['progress'].set_fraction(progress)
                    if status == 'measuring_latency':
                        widgets['progress'].set_text(_("Measuring latency..."))
                    elif status == 'downloading':
                        widgets['progress'].set_text(f"{speed:.1f} MB/s...")
                    else:
                        widgets['progress'].set_text(_("Starting..."))
                
                # Update info label
                if status == 'success':
                    info_text = f"{country} - {speed:.2f} MB/s ({int(latency)} ms)"
                    widgets['info'].set_text(info_text)
                    widgets['icon'].set_from_icon_name(
                        "network-cellular-signal-excellent-symbolic" if speed > 5 else 
                        "network-cellular-signal-good-symbolic" if speed > 1 else
                        "network-cellular-signal-weak-symbolic",
                        Gtk.IconSize.SMALL_TOOLBAR
                    )
                elif status in ['error', 'timeout', 'connection_failed', 'no_valid_files']:
                    widgets['info'].set_text(f"{country} - {_('Failed')}")
                    widgets['icon'].set_from_icon_name("network-cellular-signal-none-symbolic", Gtk.IconSize.SMALL_TOOLBAR)
                else:
                    widgets['info'].set_text(f"{country} - {_('Testing...')}")
                
                # Update stored result
                self.speed_results = [r if r.get('url') != url else result for r in self.speed_results]
                if not any(r.get('url') == url for r in self.speed_results):
                    self.speed_results.append(result)
                    
            else:
                # Create new row
                row = Gtk.ListBoxRow()
                row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
                row_box.set_margin_top(4)
                row_box.set_margin_bottom(4)
                row_box.set_margin_start(8)
                row_box.set_margin_end(8)
                
                # Status icon
                icon = Gtk.Image.new_from_icon_name("network-cellular-acquiring-symbolic", Gtk.IconSize.SMALL_TOOLBAR)
                row_box.pack_start(icon, False, False, 0)
                
                # Info box (URL + details)
                vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
                
                url_label = Gtk.Label(label=url)
                url_label.set_xalign(0)
                url_label.set_ellipsize(2)  # PANGO_ELLIPSIZE_MIDDLE
                url_label.get_style_context().add_class('bold')
                vbox.pack_start(url_label, False, False, 0)
                
                info_label = Gtk.Label(label=f"{country} - {_('Starting...')}")
                info_label.set_xalign(0)
                info_label.get_style_context().add_class('dim-label')
                vbox.pack_start(info_label, False, False, 0)
                
                row_box.pack_start(vbox, True, True, 0)
                
                # Progress bar (shows download progress, then speed comparison)
                progress_bar = Gtk.ProgressBar()
                progress_bar.set_fraction(progress)
                progress_bar.set_show_text(True)
                progress_bar.set_text(_("Starting..."))
                progress_bar.set_size_request(120, -1)
                row_box.pack_start(progress_bar, False, False, 0)
                
                row.add(row_box)
                self.list_box.add(row)
                row.show_all()
                
                # Store widget references for updates
                self.row_widgets[url] = {
                    'row': row,
                    'icon': icon,
                    'url': url_label,
                    'info': info_label,
                    'progress': progress_bar
                }
                
                # Add to results
                self.speed_results.append(result)
            
            # Update main window progress
            total = len(self.tester.mirrors)
            completed = sum(1 for r in self.speed_results if r.get('status') in ['success', 'error', 'timeout', 'connection_failed', 'no_valid_files'])
            try:
                self.main_window.show_progress(
                    _("Testing mirrors ({}/{})...").format(completed, total),
                    completed / total if total > 0 else 0
                )
            except Exception:
                pass
                
        except Exception as e:
            print(f"Error updating result: {e}")

    def _on_speed_test_finished(self, results, trigger_button):
        """Finalize speed test - reorder rows by speed and update UI."""
        try:
            self.main_window.hide_progress()
        except Exception:
            pass

        try:
            trigger_button.set_sensitive(True)
        except Exception:
            pass

        # Sort results: successful first, by speed desc
        success = [r for r in self.speed_results if r.get('status') == 'success']
        failed = [r for r in self.speed_results if r.get('status') != 'success']
        success.sort(key=lambda x: float(x.get('speed_mbps', 0) or 0.0), reverse=True)
        ordered = success + failed
        
        # Rebuild the list in sorted order with final progress bars
        for child in self.list_box.get_children():
            self.list_box.remove(child)
        self.row_widgets.clear()
        
        # Find max speed for relative comparison
        max_speed = max((float(r.get('speed_mbps', 0) or 0) for r in ordered), default=0)
        
        for result in ordered:
            url = result.get('url', '')
            speed = float(result.get('speed_mbps', 0) or 0.0)
            latency = int(result.get('latency_ms', 0) or 0)
            country = result.get('country', _("Unknown"))
            status = result.get('status', '')
            
            row = Gtk.ListBoxRow()
            row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            row_box.set_margin_top(4)
            row_box.set_margin_bottom(4)
            row_box.set_margin_start(8)
            row_box.set_margin_end(8)
            
            # Status icon based on speed
            if status == 'success':
                if speed > 5:
                    icon_name = "network-cellular-signal-excellent-symbolic"
                elif speed > 1:
                    icon_name = "network-cellular-signal-good-symbolic"
                else:
                    icon_name = "network-cellular-signal-weak-symbolic"
            else:
                icon_name = "network-cellular-signal-none-symbolic"
            
            icon = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.SMALL_TOOLBAR)
            row_box.pack_start(icon, False, False, 0)
            
            # Info box
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            
            url_label = Gtk.Label(label=url)
            url_label.set_xalign(0)
            url_label.set_ellipsize(2)
            url_label.get_style_context().add_class('bold')
            vbox.pack_start(url_label, False, False, 0)
            
            if status == 'success':
                info_text = f"{country} - {speed:.2f} MB/s ({latency} ms)"
            else:
                info_text = f"{country} - {_('Failed')}"
            
            info_label = Gtk.Label(label=info_text)
            info_label.set_xalign(0)
            info_label.get_style_context().add_class('dim-label')
            vbox.pack_start(info_label, False, False, 0)
            
            row_box.pack_start(vbox, True, True, 0)
            
            # Progress bar showing relative speed
            progress_bar = Gtk.ProgressBar()
            if max_speed > 0 and speed > 0:
                frac = min(1.0, speed / max_speed)
            else:
                frac = 0.0
            progress_bar.set_fraction(frac)
            progress_bar.set_show_text(True)
            progress_bar.set_text(f"{speed:.2f} MB/s" if status == 'success' else _("Failed"))
            progress_bar.set_size_request(120, -1)
            row_box.pack_start(progress_bar, False, False, 0)
            
            row.add(row_box)
            self.list_box.add(row)
        
        self.list_box.show_all()
        self.speed_results = ordered
        
        # Select best mirror
        if ordered:
            row = self.list_box.get_row_at_index(0)
            if row:
                self.list_box.select_row(row)
            best = ordered[0]
            if best.get('status') == 'success':
                self.selected_mirror_url = best.get('url', self.selected_mirror_url)
                self.mirror_label.set_text(_("Current: {url} ({country}, {speed:.2f} MB/s)").format(
                    url=best.get('url', ''),
                    country=best.get('country', ''),
                    speed=float(best.get('speed_mbps', 0) or 0)
                ))

    def _on_result_selected(self, listbox, row):
        try:
            idx = row.get_index()
            if 0 <= idx < len(self.speed_results):
                sel = self.speed_results[idx]
                self.selected_mirror_url = sel.get('url', self.selected_mirror_url)
                self.mirror_label.set_text(_("Current: {url} ({country}, {speed:.2f} MB/s)").format(
                    url=sel.get('url',''), country=sel.get('country',''), speed=float(sel.get('speed_mbps',0) or 0)
                ))
        except Exception:
            pass
    def _on_speed_test_clicked(self, btn):
        # Disable button while testing
        btn.set_sensitive(False)

        # Reveal footer progress and initialize
        try:
            self.main_window.show_progress(_("Testing mirrors... This may take a moment."), None)
        except Exception:
            pass

        # Clear previous results and row widget references
        for child in self.list_box.get_children():
            self.list_box.remove(child)
        self.speed_results = []
        self.row_widgets = {}
        self.max_speed_seen = 0.0

        # Run tests in background thread
        thread = threading.Thread(target=self._run_speed_test, args=(btn,))
        thread.daemon = True
        thread.start()
            
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

        # If backports is disabled, remove the backports file if it exists
        if not self.backports_enabled:
            self._remove_debian_file('debian-backports.sources')

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

    def _remove_debian_file(self, filename):
        """Remove a Debian sources file if it exists (requires pkexec for /etc)."""
        import subprocess
        import os
        
        file_path = f'/etc/apt/sources.list.d/{filename}'
        if os.path.exists(file_path):
            try:
                # Try direct removal first (in case user has write access)
                os.unlink(file_path)
                print(f"Removed {file_path}")
            except PermissionError:
                # Use pkexec to remove
                try:
                    result = subprocess.run(
                        ['pkexec', 'rm', '-f', file_path],
                        capture_output=True, text=True
                    )
                    if result.returncode == 0:
                        print(f"Removed {file_path} (via pkexec)")
                    else:
                        print(f"Failed to remove {file_path}: {result.stderr}")
                except Exception as e:
                    print(f"Error removing {file_path}: {e}")
            except Exception as e:
                print(f"Error removing {file_path}: {e}")

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
