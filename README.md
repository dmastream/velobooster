# Velo Booster - Free Warzone AFK Bot

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.8%2B-brightgreen)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)
![License](https://img.shields.io/badge/license-MIT-green)

<div align="center">

[![Velo Booster](https://img.shields.io/badge/Velo_Booster-%237f4fc3.svg?style=for-the-badge&logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAGMAAABhBAMAAAAw3QKtAAAAAXNSR0IB2cksfwAAAAlwSFlzAAAOxAAADsQBlSsOGwAAABhQTFRFAAAATU1NiIiIw8PD4eHh////paWla2trMZP9ogAAAAh0Uk5TAID////////P6vTwAAADdElEQVR4nL2YO2/bMBDHST+HprCRQlNaxHDh3SigpUsNBFrjp7au/gj6Hv4GzRrHTbunaLOnLbJniJA1Dap27cPlQw8eeZTopf8hsWX9dLwjebwTJTuLWi73+527l6sdkNqc/90+fuOMSIIxeyeuSNAlD1+T/ee97efYDfFG5Ercukz+nDshdEEenWTmsk/lSBTXTtOPtfl244C0xsptg+H9ZTWyTJS7MDMG0j7+%2B1b56o0MMwbijW6uwRMMMzpCF9otg6EeNB1pTr59Ahdqc31udMTvXSTwyjKR82pD6rPf74h%2BSbOrIcYjmYIO9A4idAEiLNWcwDhDRIuwlB5niISIESPOAKnPzBUlLoM4A8Q//KBFWCroqkFRkcZUC2fxg2pGRUKiTyNqRkGaE2MaUTMFwvavzQjc0QUSxRZPpBm6NhCwf00pOzpH/B4y8YXYjn66gkhzgk58oSh++AgQ5ru5hKHyQNPsGSW+Z0NLIyAR5ju+VFRlEZDIMin1PTMjY0qlkQrfpaJYmKHSpIMRHiPhDSWW7Yub4UHjiL65rarNeVw54h+WLRVVy+8bgdCFddHrakzZyCjf2k7Oc9EFc4Fyp84cCebDs3OOLH+sq+9NFd1uOBLsubrCnblIKBvfr/fOSH12FVOWP5295zMjEeRst4kubq6pAJ0REt5fcmQHK3xIVNjaEeG2nJHW+GDFEeclxuflbOfZjwXivXJd+2yN9U/lSnYOmVgpfIuFlTksU2PKns4RsdeclO1KybqofcyDK5JSiFWdiLwRf7ZAZLKpVJq8BGIWUBYjRbZk6dLBTFaYSCQ/CMoEMz9a3Gqqz9I0THOjWHmvKj9Ms7OyMc2OQou8URai/EQOuhUncl5I0OJa6bnv9/KFWFQXg2HJ0HLfAVIaAb+H1TBlEQB1n1qPBR2bGVBww6rPYgYW3KC2DDp4wQCrepcKtjUGaQvWyfhBOxgeqH0sRBpTZAmkFYIFISGyCfSqXkOwLR1uyzqLtH4AMloavUsyc5rRN+mIEefWuKoXM3ois/AykOYENitm4YV0ryDOLt0r7ImwRsBEQE6LYvNURPp9JafVZ0i3gSAscaRbjQ0LOa2wdxdRLJnaURfLOugbEr+3fbIm+y8Iwc6q0vcw2LCsb3uOuvwfngos75Tar3+S7Zdb9DcLUqb/g/wDrNxbcQI4pDoAAAAASUVORK5CYII=&logoColor=white)](https://discord.gg/cGN3ZWJVYe)

**Contact:** ! dma | Discord ID: dmastream

**Join our community:** [discord.gg/cGN3ZWJVYe](https://discord.gg/cGN3ZWJVYe)

</div>

## 📋 Overview

Velo Booster is an automated bot designed for farming XP and Battle Pass progression in Call of Duty: Modern Warfare 2 (2022) and Warzone 2.0. The bot works by:

- Automatically queuing for Battle Royale matches
- Navigating game menus using computer vision
- Performing random movements in-game to avoid AFK detection
- Monitoring game state and automatically requeuing after matches end
- Providing Discord webhook notifications for game events
- Offering a user-friendly GUI interface

> **Note:** This software is provided for educational purposes only. Use at your own risk and responsibility.

## ✨ Features

- **Fully Automated Operation**: Queue, play, and requeue without manual intervention
- **Computer Vision Technology**: Uses OpenCV to detect UI elements and game state
- **Discord Integration**: Real-time notifications about game status
- **Game Crash Recovery**: Watchdog feature that can restart the game if it crashes
- **Modern GUI Interface**: Easy-to-use interface with game statistics
- **Multiple Game Mode Support**: Configure for different Battle Royale variants

## 🛠️ Setup

### Automatic Setup (Recommended)

1. **Run the Automatic Installer**
   - Simply run `setup.bat` by double-clicking it
   - The script will automatically install Python and all required packages
   - Follow any on-screen prompts

### Manual Setup

1. **Install Python 3.8+**
   - Download from [python.org](https://www.python.org/downloads/)
   - Ensure you check "Add Python to PATH" during installation

2. **Install Required Packages**
   ```bash
   python -m pip install -r requirements.txt
   ```
   Or install packages individually:
   ```bash
   python -m pip install pypiwin32 pillow opencv-python pyside6 requests numpy
   ```

3. **Game Configuration**
   - Set Call of Duty: Modern Warfare/Warzone to **English language**
   - Configure the game to run in **Windowed mode**
   - Ensure the "Jump" button is bound to **SPACE**
   - If using the watchdog feature, set Battle.net launcher to English and keep it open

## 🚀 Usage

### GUI Mode (Recommended)

1. Start Call of Duty: Warzone
2. **Run the bot by double-clicking `run_bot.bat`**
   - This will automatically start the GUI application
   - Alternatively, you can run it manually with: `python gui.py`
3. Configure your Discord webhook URL (optional)
4. Click "Start" to begin the bot operation

## 📊 How It Works

1. The bot uses computer vision (OpenCV) to detect UI elements
2. It automatically navigates menus to queue for matches
3. Once in-game, it performs random movements to avoid AFK detection
4. After a match ends, it automatically requeues
5. Optional Discord notifications keep you updated on progress

## ⚠️ Disclaimer

-# Velo Booster is a free, open-source project intended for **educational and entertainment purposes only**. Use at your own risk. We are not responsible for any bans, account issues, or other consequences that may arise from using this software.

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.
