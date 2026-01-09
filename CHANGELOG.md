# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/lang/en/).

## [2.0.2] - 2026-01-09

### 📚 Documentation
- **Man Page**: Added complete manual page (`docs/soplos-repo-selector.1`) with standard sections (NAME, SYNOPSIS, DESCRIPTION, OPTIONS, FILES, AUTHOR, COPYRIGHT, SEE ALSO).
- **Debian Copyright**: Added machine-readable copyright file (`debian/copyright`) following Debian 1.0 format with full GPL-3.0+ license block.
- **Packager Integration**: Updated `soplos-packager` to automatically include documentation in generated `.deb` packages.

## [2.0.1] - 2026-01-02

### � Major Improvements
- **Speed Test Service**: Complete rewrite with accurate, real-world measurements.
  - Real TCP latency measurement using socket connections (no more simulated ICMP).
  - Larger downloads (2-10MB) for accurate speed calculation over 3+ seconds.
  - Dynamic download size selection based on test file availability.
  - Increased parallelism from 3 to 6 workers for faster testing.
  - Improved country detection from mirror URLs.

### ✨ UI Enhancements
- **Dynamic Progress Bars**: Progress bars now animate in real-time during speed tests.
  - Shows "Measuring latency..." during TCP connection test.
  - Shows live download speed during bandwidth test.
  - Final display shows relative speed comparison with fastest mirror.
- **Live Updates**: Individual mirror rows update without rebuilding entire list.
- **Better Visual Feedback**: Status icons change based on connection quality.

### 🐛 Bug Fixes
- **Sources Generator**: Now detects real system state instead of using hardcoded defaults.
  - Distributions, components, and backports checkboxes reflect actual system configuration.
  - Only considers active (non-disabled) Debian repositories for detection.
- **Sources Generator**: Properly removes `debian-backports.sources` file when backports is disabled.
- **File Manager**: Fixed `UnboundLocalError` with `_` translation function caused by variable shadowing in tuple unpacking.
- Fixed speed test giving identical results regardless of geographic location.
- Fixed progress bars not animating during mirror tests.
- Improved error handling for unreachable mirrors.

### ✨ Improvements
- **System State Detection**: New `_detect_system_state()` method reads active repos from `/etc/apt/sources.list.d/`.
- **Desktop Detection**: Improved `_translate_desktop_name()` and `_translate_protocol_name()` methods with i18n support.

## [2.0.0] - 2025-12-10

### 🏗️ Architecture Rewrite
- Complete rewrite with modern, modular architecture for improved cross-desktop compatibility.
- Separation of concerns: Core, UI, Services, Utils layers.
- Professional project structure with focused, maintainable modules.

### 🔧 Universal Desktop Compatibility
- Smart desktop environment detection (GNOME, KDE, XFCE).
- GNOME 48+ full integration.
- KDE Plasma 6 native support.
- XFCE 4.20 optimization.
- Complete X11 and Wayland compatibility.

### 🌍 Internationalization Overhaul
- Migrated to GNU Gettext standard with .mo files.
- Support for 8 languages: ES, EN, FR, DE, PT, IT, RO, RU.
- Complete translation coverage across all UI elements.

### 🎨 Advanced Theming System
- CSS-based theming engine aligned with Soplos Welcome.
- Automatic dark/light theme detection.
- Modern UI with improved visual consistency.

### ✨ Enhanced Repository Management
- Improved repository addition, editing, and removal workflows.
- Better validation and error handling.
- Enhanced DEB822 format support.

### 🔑 GPG Key Management Improvements
- Streamlined GPG key import process.
- Enhanced key download functionality from URLs.
- Better key verification and management.

### Patch - 2025-12-13
- **Internationalization**: Completed and standardized translations for all supported languages (French, Italian, Portuguese, Romanian, Russian).
- **Localization**: Validated and compiled MO files for all 8 languages ensuring 100% coverage.

### Patch - 2025-12-12
- Fixed `Sources Generator` to preserve DEB822 block grouping and respect selected mirror.
- Integrated mirror speed test into the Sources Generator tab (no external windows).
- Fixed layout and selection bugs in the Repositories list tab.
- Added GPG tab improvements: fingerprint/expiry display, export and delete actions with safe validation.
- Replaced four screenshots (Welcome, Repositories, Sources Generator, GPG Keys).

### 🚀 Mirror Detection & Speed Testing
- Improved fastest mirror detection algorithm.
- Enhanced speed testing with better progress reporting.
- Optimized mirror selection based on geographical location.

### 📦 AppStream/DEP-11 Integration
- Updated metadata for better software center integration.
- Improved compatibility with Discover, GNOME Software, and other AppStream-compatible centers.
- Enhanced icon and screenshot references.

### 🛠️ Fixed
- Improved stability across different desktop environments.
- Better error handling and user feedback.
- Fixed theme detection issues in KDE Plasma.
- Resolved Wayland-specific compatibility issues.

## [1.0.7] - 2025-07-27

### 🎨 Changed
- **Application Icon**: Updated program icon to new design.

## [1.0.6] - 2025-07-16

### 🆕 Added
- **AppStream Icons**: Added program icons in 48x48, 64x64 and 128x128 for AppStream/DEP11 integration.

### ✨ Improved
- **Finalized Metainfo**: Metainfo file now fully complies with AppStream/DEP11 standard for maximum compatibility in software centers.

### 🔧 Technical
- **AppStream Compliance**: Final validation and correction of metainfo.xml and associated resources.

## [1.0.5] - 2025-07-14

### ✨ Improved
- **Final Metainfo Corrections**: Metainfo file has been reviewed and finalized to ensure proper appearance in software centers like Discover, GNOME Software and other AppStream-compatible centers.

## [1.0.4] - 2025-07-13

### ✨ Improved
- **Metainfo Updates**: Improved visibility and compatibility in Discover and AppStream.
- **Screenshot Reference Corrections**: Screenshot names are now consistent and real.

## [1.0.3] - 2025-06-17

### 🆕 Added
- **Improved Specific GTK Theme Detection**: Directly reads KDE GTK configuration.
- **Respect for System Configuration**: Does not force specific themes unless necessary.
- **Better XDG Portal Integration**: Improved Wayland compatibility.

### ✨ Improved
- **Custom Theme Compatibility**: Now respects custom colors and accents.
- **KDE Theme Detection**: Searches for GTK theme configured in KDE instead of forcing Adwaita.
- **Startup Performance**: Reduced loading time and memory usage.
- **System Integration**: Better respect for user theme configuration.

### 🛠️ Fixed
- **Blue Color Issue**: Resolved forced Adwaita theme causing incorrect colors.
- **Orange Theme Compatibility**: Now correctly respects Soplos orange accents.
- **Theme Detection in KDE**: Improved reading of `~/.config/kdeglobals`.
- **GTK Configuration**: Avoids overwriting user theme configurations.

### 🔧 Technical
- **Refactored `detect_kde_theme()`**: Now searches for specific GTK configuration in KDE.
- **Theme Application Logic**: Only applies theme if a specific one is detected.
- **Better Error Handling**: Improved management of missing configuration files.
- **Documentation**: Updated documentation on theme compatibility.

## [1.0.2] - 2025-01-15

### 🆕 Added
- **Automatic System Theme Detection**: Support for light and dark themes in KDE and GNOME.
- **`detect_kde_theme()` Function**: Specific KDE theme detection by reading `~/.config/kdeglobals`.
- **Automatic `GTK_THEME` Configuration**: Automatically applied according to detected theme.
- **Improved Wayland Support**: Better integration with Wayland compositors.
- **Theme Environment Variables**: `GDK_BACKEND`, `GTK_USE_PORTAL` configured automatically.
- **Pre-Environment Configuration**: Theme detection before loading GTK.

### ✨ Improved
- **User Interface**: Better adaptation to dark themes with Soplos orange colors.
- **KDE Plasma Compatibility**: Precise detection of Breeze/Breeze-Dark color schemes.
- **Startup Performance**: Optimization in initial application loading.
- **Language Detection**: Improved automatic system language detection.
- **Error Handling**: Better error handling in theme detection.

### 🛠️ Fixed
- **Unwanted Blue Theme**: Resolved blue tones issue in dark theme.
- **Theme Inconsistencies**: Now correctly respects system theme.
- **Wayland Issues**: Better support and stability in Wayland environments.
- **Icon Configuration**: Improved icon loading in different themes.

### 🔧 Technical
- **Refactored `main.py`**: Reorganized initialization code.
- **New Detection Functions**: `detect_kde_theme()` and `configure_environment_theme()`.
- **Code Cleanup**: Removed redundant theme detection code.
- **Documentation**: Updated technical documentation on theme detection.

## [1.0.1] - 2025-01-10

### 🆕 Added
- **Complete Multi-Language Support**: 8 supported languages (ES, EN, FR, PT, DE, IT, RU, RO).
- **Automatic Language Detection**: Based on system configuration.
- **GPG Key Management**: Import, download and manage verification keys.
- **Fast Repository Search**: Speed test to find optimal mirrors.
- **Predefined Repositories**: Quick access to Chrome, VSCode, Docker, OBS Studio.

### ✨ Improved
- **User Interface**: More intuitive and responsive design.
- **Compatibility**: Better support for Wayland and X11.
- **Performance**: Optimization in repository loading.
- **Error Handling**: Improved error handling system.

### 🛠️ Fixed
- **Permission Issues**: Better handling of sudo/pkexec.
- **Repository Validation**: Improved syntax verification.
- **Stability**: Fixed occasional crashes.

## [1.0.0] - 2025-01-05

### 🎉 Initial Release
- **Initial Launch** of Soplos Repo Selector.
- **Basic Repository Management**: Add, edit, remove APT repositories.
- **DEB822 Format Support**: Compatibility with modern repository format.
- **GTK 3 Interface**: Native and responsive graphical interface.
- **Apply Changes**: Safe system to apply configurations.
- **Debian Compatibility**: Full support for Debian-based systems.

### Main Features
- Complete management of `/etc/apt/sources.list.d/`.
- Intuitive interface for novice and advanced users.
- Automatic repository syntax validation.
- Automatic configuration backup system.
- Integration with pkexec for administrative operations.

---

## Types of Changes

- **Added** for new features
- **Improved** for changes in existing functionality
- **Deprecated** for soon-to-be removed features
- **Removed** for removed features
- **Fixed** for bug fixes
- **Security** for vulnerabilities

## Author

Developed and maintained by Sergi Perich  
Website: https://soplos.org  
Contact: info@soploslinux.com

## Contributing

To report bugs or request features:
- **Issues**: https://github.com/SoplosLinux/soplos-repo-selector/issues
- **Email**: info@soploslinux.com

## Support

- **Documentation**: https://soplos.org
- **Community**: https://soplos.org/foros/
- **Support**: info@soploslinux.com