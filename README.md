# Velo Booster - Free Warzone AFK Bot

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.8%2B-brightgreen)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)
![License](https://img.shields.io/badge/license-MIT-green)

<div align="center">

[![Discord](https://img.shields.io/badge/Discord-%235865F2.svg?style=for-the-badge&logo=discord&logoColor=white)](https://discord.gg/velobooster)

**Contact:** ! dma | Discord ID: dmastream

**Join our community:** [discord.gg/cGN3ZWJVYe](https://discord.gg/cGN3ZWJVYe)

</div>

## 📋 Overview

Velo Booster is an automated bot designed for farming XP and Battle Pass progression in Call of Duty: Warzone
The bot works by:

- Automatically queuing for Plunder matches
- Navigating game menus using computer vision
- Performing random movements in-game to avoid AFK detection
- Monitoring game state and automatically requeuing after matches end (currently supported only for Battle.net.)
- Providing Discord webhook notifications for game events
- Offering a user-friendly GUI interface

> **Note:** This software is provided for educational purposes only. Use at your own risk and responsibility.

## ✨ Features

- **Fully Automated Operation**: Queue, play, and requeue without manual intervention
- **Computer Vision Technology**: Uses OpenCV to detect UI elements and game state
- **Discord Integration**: Real-time notifications about game status
- **Game Crash Recovery**: Watchdog feature that can restart the game if it crashes
- **Modern GUI Interface**: Easy-to-use interface with game statistics

## 🛠️ Setup

1. **Install Python 3.8+**
   - Download from [python.org](https://www.python.org/downloads/)
   - Ensure you check "Add Python to PATH" during installation

2. **Install Required Packages**
   ```bash
   python -m pip install pypiwin32 pillow opencv-python pyside6 requests
   ```

3. **Game Configuration**
   - Set Call of Duty: Modern Warfare/Warzone to **English language**
   - Configure the game to run in **Windowed mode**
   - Ensure the "Jump" button is bound to **SPACE**
   - If using the watchdog feature, set Battle.net launcher to English and keep it open

## 🚀 Usage

### GUI Mode (Recommended)

1. Start Call of Duty: Warzone
2. Run the bot with:
   ```bash
   python gui.py
   ```
3. Configure your Discord webhook URL (optional)
4. Click "Start" to begin the bot operation

### Command Line Mode

1. Start the game
2. Run the bot with options:
   ```bash
   python bot.py [options]
   ```

### Command Line Options

- `mode=<gamemode>`: Specify which game mode to queue for
  - Supported modes: `battle-royale-quads`, `battle-royale-duos`
- `fill=<on|off>`: Whether to fill your squad with random players

Example:
```bash
python bot.py mode=battle-royale-duos fill=off
```

## 📊 How It Works

1. The bot uses computer vision (OpenCV) to detect UI elements
2. It automatically navigates menus to queue for matches
3. Once in-game, it performs random movements to avoid AFK detection
4. After a match ends, it automatically requeues
5. Optional Discord notifications keep you updated on progress

## ⚠️ Disclaimer

This software is provided for **educational purposes only**. Using automation tools may violate the game's Terms of Service. The developers are not responsible for any consequences resulting from the use of this software.

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.
