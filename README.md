# Soplos Repo Selector

[![License: GPL-3.0+](https://img.shields.io/badge/License-GPL--3.0%2B-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Version](https://img.shields.io/badge/version-2.0.1-green.svg)]()

Soplos Repo Selector is a graphical APT repository manager designed specifically for Debian-based systems. It allows you to manage, optimize, and configure software repositories in a simple and intuitive way.

## Screenshots

Welcome view:

![Welcome](https://raw.githubusercontent.com/SoplosLinux/soplos-repo-selector/main/assets/screenshots/screenshot1.png)

Repositories tab (list and actions):

![Repositories](https://raw.githubusercontent.com/SoplosLinux/soplos-repo-selector/main/assets/screenshots/screenshot2.png)

Sources Generator (speed test integrated):

![Sources Generator](https://raw.githubusercontent.com/SoplosLinux/soplos-repo-selector/main/assets/screenshots/screenshot3.png)

GPG Keys tab:

![GPG Keys](https://raw.githubusercontent.com/SoplosLinux/soplos-repo-selector/main/assets/screenshots/screenshot4.png)

## 🆕 Version History

### 🆕 What's new in version 2.0.1
- Release date: January 2, 2026

#### Major Improvements
- **Speed Test Service**: Complete rewrite with accurate, real-world measurements.
  - Real TCP latency measurement using socket connections.
  - Larger downloads (2-10MB) for accurate speed calculation.
  - Increased parallelism from 3 to 6 workers for faster testing.
  - Improved country detection from mirror URLs.

#### UI Enhancements
- **Dynamic Progress Bars**: Progress bars now animate in real-time during speed tests.
  - Shows "Measuring latency..." during TCP connection test.
  - Shows live download speed during bandwidth test.
  - Final display shows relative speed comparison with fastest mirror.

#### Bug Fixes
- **Sources Generator**: Now detects real system state instead of using hardcoded defaults.
- **Sources Generator**: Properly removes `debian-backports.sources` file when backports is disabled.
- **File Manager**: Fixed `UnboundLocalError` with translation function caused by variable shadowing.
- Fixed speed test giving identical results regardless of geographic location.
- Fixed progress bars not animating during mirror tests.

#### Improvements
- New system state detection method that reads active repos from `/etc/apt/sources.list.d/`.
- Improved desktop/protocol detection with i18n support.

### 🆕 What's new in version 2.0.0
- Release date: December 10, 2025
- Patch: December 13, 2025 — translation finalization (see details below)

#### Patch (2025-12-13)
- Completed and standardized translations for all 8 supported languages.
- Validated and compiled localization files for full consistency.

#### Patch (2025-12-12)
- Fixed `Sources Generator` tab to preserve per-distribution DEB822 blocks and respect the selected mirror.
- Integrated the mirror speed test into the same Sources Generator tab (no external windows required).
- Fixed issues in the Repositories list tab (layout and selection bugs).
- Added GPG tab enhancements: fingerprint and expiry display, export and delete actions with safe validation.
- Replaced four screenshots with updated captures for the Welcome, Repositories, Sources Generator (speed test integrated) and GPG Keys tabs.

#### Original 2.0.0 highlights (December 10, 2025)
- Major refactor for multi-desktop compatibility and modern theming aligned with Soplos Welcome.
- Improved repository management, GPG key handling, mirror detection and speed testing.
- Updated AppStream/DEP-11 metadata for better software center integration.

### 🆕 What's new in version 1.0.7 (July 27, 2025)
- Application icon update

### 🆕 What's new in version 1.0.6 (July 16, 2025)
- Full AppStream/DEP11 standard compliance in metainfo
- Icons added in 48x48, 64x64 and 128x128 for software center integration

### 🆕 What's new in version 1.0.5 (July 14, 2025)
- Final metainfo corrections to ensure proper appearance in software centers like Discover, GNOME Software and other AppStream-compatible centers.

### 🆕 What's new in version 1.0.4 (July 13, 2025)
- Metainfo updates for better visibility and compatibility in Discover and AppStream.
- Screenshot reference corrections: consistent and real capture names.

### 🆕 What's new in version 1.0.3 (June 17, 2025)
- Improved specific GTK theme detection by reading KDE configuration.
- Better integration with XDG portal and Wayland compatibility.
- Compatibility with custom themes and respect for system configuration.
- Reduced loading time and memory usage.
- Fixed color issues and orange accent problems.

### 🆕 What's new in version 1.0.2 (January 15, 2025)
- Automatic system theme detection (KDE and GNOME).
- Improved Wayland support.
- Theme environment variables configured automatically.
- Interface improvements and startup performance.
- Better error handling and language detection.

### 🆕 What's new in version 1.0.1 (January 10, 2025)
- Full multi-language support (8 languages).
- GPG key management and repository speed testing.
- Predefined repositories and better error handling.

### 🆕 What's new in version 1.0.0 (January 5, 2025)
- Initial release of Soplos Repo Selector.
- Basic APT repository management and DEB822 format support.
- GTK 3 interface and Debian compatibility.

## Main Features

- **Complete repository management**: Add, edit, remove and enable/disable APT repositories
- **Multi-language support**: Interface available in 8 languages (ES, EN, FR, PT, DE, IT, RU, RO)
- **Automatic theme detection**: Support for light and dark themes
- **Fast repository search**: Automatically find the fastest mirrors
- **GPG key management**: Import, download and manage verification keys
- **Predefined repositories**: Quick access to popular repositories (Chrome, VSCode, Docker, OBS)
- **Wayland/X11 compatibility**: Works perfectly in both environments
- **Distribution templates**: Pre-configured settings for Debian Stable, Testing, Sid and Soplos

## Installation

### From DEB package (recommended)
```bash
sudo dpkg -i soplos-repo-selector_2.0.0_all.deb
sudo apt-get install -f  # Resolve dependencies if necessary
```

### From source code
```bash
git clone https://github.com/SoplosLinux/soplos-repo-selector
cd soplos-repo-selector
sudo python3 setup.py install
```

## Dependencies

- **Python 3.8+**
- **GTK 3.0+**
- **GObject Introspection**
- **Python packages**: `python3-gi`, `python3-apt`, `python3-psutil`
- **System**: `curl`, `wget`, `gnupg`, `pkexec`

## Basic Usage

### Launch the application
```bash
soplos-repo-selector
```

### Repository management
1. **Add repository**: "Add" button or Ctrl+N
2. **Edit repository**: Select and "Edit" or Ctrl+E
3. **Remove repository**: Select and "Remove" or Delete
4. **Apply changes**: "Apply" button or Ctrl+S

### Fast repository search
1. Click "Search Fastest Repositories"
2. Select country/region (optional)
3. Start speed test
4. Select desired repositories
5. Apply configuration

### GPG key management
1. Go to "GPG Keys" tab
2. Import from file or download from URL
3. View details and manage existing keys

## Advanced Configuration

### Configuration files
- **User configuration**: `~/.config/soplos-repo-selector/settings.json`
- **System repositories**: `/etc/apt/sources.list.d/`
- **GPG keys**: `/usr/share/keyrings/` and `/etc/apt/keyrings/`

### Environment variables
- `SOPLOS_REPO_SELECTOR_LANG`: Force specific language
- `GDK_BACKEND`: Graphics backend (wayland, x11)
- `GTK_THEME`: Specific GTK theme

## Development

### Project structure
```
soplos-repo-selector/
├── src/
│   └── soplos_repo_selector/
│       ├── __init__.py
│       ├── main.py
│       └── ui/
├── data/
│   ├── icons/
│   └── locale/
├── debian/
└── setup.py
```

## Links

- **Website**: https://soplos.org
- **Report issues**: https://github.com/SoplosLinux/soplos-repo-selector/issues
- **Help / Forums**: https://soplos.org/foros

## License

This project is licensed under GPL-3.0+.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues on GitHub.

## Credits

Developed and maintained by the Soplos Linux team.