# Kimi Token Usage

<p align="center">
  <img src="assets/token_widget.png" width="160" alt="Kimi Token Usage icon">
</p>

A small, standalone Windows desktop widget that shows your total Kimi Code token usage. The purple companion refreshes automatically, follows your mouse with its eyes, and can be dragged anywhere on your screen.

## Download

**[Download Kimi Token Usage for Windows](https://github.com/Cyberkillr013/kimi-token-usage/releases/latest/download/KimiTokenUsage-Setup.exe)**

No Python installation is required.

## Install

1. Download `KimiTokenUsage-Setup.exe` and double-click it.
2. Choose an install location and select your options:
   - **Install app** is required and always selected.
   - **Open Kimi Token Usage when Windows starts** is selected by default.
   - **Put a shortcut on my Desktop** is optional.
3. Finish the installer, then open **Kimi Token Usage** from your Desktop or Start menu.

The app installs only for the current Windows user and does not require administrator access. It can be uninstalled from **Settings > Apps > Installed apps**.

## Using the widget

- Drag the widget to move it.
- Click the companion to pet it.
- Double-click the companion to refresh immediately.
- Right-click anywhere in the widget to open its menu, including snacks, games, sleep mode, always-on-top, and refresh controls.
- Press **Escape** to close it.

Usage refreshes every 15 seconds. The total includes regular input, cached input, cache creation, and output tokens across saved Kimi Code sessions.

## Privacy and requirements

- Windows 10 or 11, 64-bit.
- Kimi Code session data in `%USERPROFILE%\.kimi-code`, or a custom location set through `KIMI_CODE_HOME`.
- All usage data is read locally. The app does not send token or session data anywhere.

## Build from source

Install Python 3.12, Git, and Inno Setup 6. Then run:

```powershell
git clone https://github.com/Cyberkillr013/kimi-token-usage.git
cd kimi-token-usage
.\build.ps1
```

The build creates:

- `dist\KimiTokenUsage.exe`: the standalone app.
- `release\KimiTokenUsage-Setup.exe`: the Windows installer.

To install Inno Setup with Windows Package Manager:

```powershell
winget install --id JRSoftware.InnoSetup --exact
```

## Source layout

- `src/token_widget.py`: the desktop widget.
- `src/token_usage.py`: local session discovery and token calculations.
- `assets/`: the app icon.
- `installer/`: Windows installer and executable version metadata.
