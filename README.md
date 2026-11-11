# Kimi Token Usage

<p align="center">
  <img src="assets/token_widget.png" width="160" alt="Kimi Token Usage icon">
</p>

A standalone Windows desktop pet that shows your Kimi Code token usage. A cute pixel-art cat walks along your taskbar at **35 FPS**, has a life of its own, and occasionally thinks about random AI facts.

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

## Your desktop companion

- Original pixel-art sprites with chunky outlines, curled tails, collars, and expressive poses.
- A four-legged walk cycle plays at **35 distinct frames per second** while walking.
- Choose **Luna** (white/silver), **Mochi** (ginger), **Smokey** (grey), or **Coco** (chocolate) from the right-click menu.
- The cat turns to face its walking direction and has separate walking, sitting, sleeping, and pickup poses.
- Hover over the cat to see your total AI token usage. The bubble disappears when you move the pointer away.
- Drag gently to pick the cat up; release to place it back on the taskbar.
- Click the cat to pet it, or double-click to refresh its token total.
- Right-click for appearance choices, snacks, games, sleep mode, taskbar walking, always-on-top, and refresh controls.
- Press **Escape** to close the app.

## Resource use

Walking and actions animate at 35 FPS. Resting and sleeping use much slower updates. Token usage refreshes in the background every 60 seconds instead of continuously reading session data. Pixel-art frames are tiny and loaded on demand, so no 3D engine or video player runs in the background.

The total includes regular input, cached input, cache creation, and output tokens across saved Kimi Code sessions.

## Privacy and requirements

- Windows 10 or 11, 64-bit.
- Kimi Code session data in `%USERPROFILE%\.kimi-code`, or a custom location set through `KIMI_CODE_HOME`.
- All usage data is read locally. The app does not send token or session data anywhere.
- Appearance and behavior preferences are stored locally in `token_widget.json` inside the Kimi Code data directory.

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

- `src/token_widget.py`: the animated desktop pet and its interactions.
- `src/token_usage.py`: local session discovery and token calculations.
- `assets/cats/`: original transparent pixel-art walk cycles and poses in both directions.
- `assets/`: the app icon.
- `installer/`: Windows installer and executable version metadata.
