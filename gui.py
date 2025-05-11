"""GUI launcher for Velo Booster – Warzone AFK bot.

Run:  python gui.py

Dependencies:  PySide6 (pip install pyside6)
"""

from __future__ import annotations

import sys
import json
import time
import ctypes
from pathlib import Path
from typing import Optional

import bot  # noqa: E402

from PySide6.QtCore import Qt, QTimer, QThread, Signal, QPoint, QPropertyAnimation
from PySide6.QtGui import QColor, QGuiApplication, QKeyEvent
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QPushButton,
    QLineEdit,
    QComboBox,
    QVBoxLayout,
    QHBoxLayout,
    QSpacerItem,
    QSizePolicy,
    QProgressBar,
    QMessageBox,
)

# -----------------------------------------------------------------------------
# Persistent settings helpers
# -----------------------------------------------------------------------------
SETTINGS_PATH = Path(__file__).with_name("settings.json")


def load_settings() -> dict:
    if SETTINGS_PATH.exists():
        try:
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_settings(data: dict) -> None:
    try:
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as exc:
        print("Failed to save settings:", exc)

# -----------------------------------------------------------------------------
# Loading screen – simple progress bar with fade out
# -----------------------------------------------------------------------------
class LoadingScreen(QWidget):
    finished = Signal()  # emitted when animation completes

    def __init__(self, duration_ms: int = 2000):
        super().__init__(None, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(360, 200)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.addStretch()

        title = QLabel("Velo Booster", self)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color:white;font-size:24px;font-weight:600;")
        layout.addWidget(title)
        layout.addSpacing(20)

        self._bar = QProgressBar(self)
        self._bar.setRange(0, 100)
        self._bar.setTextVisible(False)
        self._bar.setFixedHeight(8)
        self._bar.setStyleSheet(
            """QProgressBar{background:#333;border-radius:4px;}QProgressBar::chunk{background:#7f4fc3;border-radius:4px;}"""
        )
        layout.addWidget(self._bar)
        layout.addStretch()

        # Center on primary screen
        geo = QGuiApplication.primaryScreen().geometry()
        self.move(geo.center() - self.rect().center())

        self._step = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(int(duration_ms / 100))  # 100 ticks

        self._fade = QPropertyAnimation(self, b"windowOpacity", self)
        self._fade.setDuration(400)
        self._fade.setStartValue(1)
        self._fade.setEndValue(0)
        self._fade.finished.connect(self.finished)

    def _tick(self):
        self._step += 1
        self._bar.setValue(self._step)
        if self._step >= 100:
            self._timer.stop()
            self._fade.start()

# -----------------------------------------------------------------------------
# Thread wrapper around bot.main_loop
# -----------------------------------------------------------------------------
class BotThread(QThread):
    game_count_changed = Signal(int)
    stopped = Signal()

    def __init__(self, webhook_url: str):
        super().__init__()
        self.webhook_url = webhook_url.strip()

    def run(self):
        global bot  # use the existing module reference

        # patch webhook url if provided
        if self.webhook_url:
            bot.DISCORD_WEBHOOK_URL = self.webhook_url

        # callback for game count updates
        def _u():
            self.game_count_changed.emit(bot.get_game_count())

        bot.set_update_game_count_callback(_u)
        bot.set_shutdown_requested(False)
        
        # Record start time
        from datetime import datetime
        bot.start_time = datetime.now()
        
        # Send startup notification
        bot.send_discord_embed(
            "Velo Booster Started", 
            "The bot is now active and monitoring for game activity. Sit back and let Velo Booster handle the rest.", 
            0x7f4fc3
        )

        try:
            bot.main_loop()
        except Exception as exc:
            print("Bot crashed:", exc)
        finally:
            self.stopped.emit()

# -----------------------------------------------------------------------------
# Main GUI window
# -----------------------------------------------------------------------------
class MainWindow(QWidget):
    PRIMARY = "#7f4fc3"
    ACCENT = "#6639a6"
    LIGHT = "#9b75d0"

    def __init__(self):
        super().__init__(None, Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._dragPos: Optional[QPoint] = None

        self.bot_thread: Optional[BotThread] = None
        self.start_time: Optional[float] = None

        self._build_ui()
        self._load_settings()

        # runtime timer
        self._runtime_timer = QTimer(self)
        self._runtime_timer.timeout.connect(self._update_runtime)

    # --------------------------- UI construction
    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        container = QWidget(self)
        container.setObjectName("bg")
        outer.addWidget(container)

        container.setStyleSheet(
            """#bg{background:#1e1e1e;border-radius:12px;}"""
        )

        v = QVBoxLayout(container)
        v.setContentsMargins(24, 24, 24, 24)
        v.setSpacing(14)

        # ---- title bar
        bar = QHBoxLayout()
        lbl_title = QLabel("Velo Booster", self)
        lbl_title.setStyleSheet("color:white;font-size:18px;font-weight:600;")
        bar.addWidget(lbl_title)
        bar.addStretch()
        btn_close = QPushButton("✕", self)
        btn_close.setFixedSize(24, 24)
        btn_close.setStyleSheet(
            f"QPushButton{{background:transparent;color:white;border:none;}}"
            f"QPushButton:hover{{color:{self.LIGHT};}}"
        )
        btn_close.clicked.connect(self.close)
        bar.addWidget(btn_close)
        v.addLayout(bar)

        # ---- webhook url
        lbl_hook = QLabel("Discord Webhook URL", self)
        lbl_hook.setStyleSheet("color:white;")
        self.le_hook = QLineEdit(self)
        self.le_hook.setPlaceholderText("https://discord.com/api/webhooks/...")
        self.le_hook.setStyleSheet(
            f"QLineEdit{{background:#2b2b2b;color:#ddd;border:1px solid #444;padding:6px;border-radius:6px;}}"
            f"QLineEdit:focus{{border:1px solid {self.PRIMARY};}}"
        )
        v.addWidget(lbl_hook)
        v.addWidget(self.le_hook)

        # ---- loadout (future proof)
        lbl_load = QLabel("Loadout", self)
        lbl_load.setStyleSheet("color:white;")
        self.cb_load = QComboBox(self)
        self.cb_load.addItems(["Loadout 1"])
        self.cb_load.setStyleSheet(
            f"QComboBox{{background:#2b2b2b;color:#ddd;border:1px solid #444;border-radius:6px;padding:4px;}}"
            f"QComboBox:hover{{border:1px solid {self.PRIMARY};}}"
            f"QComboBox::drop-down{{border:none;}}"
        )
        v.addWidget(lbl_load)
        v.addWidget(self.cb_load)

        # ---- stats
        self.lbl_runtime = QLabel("Runtime: 00:00:00", self)
        self.lbl_runtime.setStyleSheet("color:white;")
        self.lbl_games = QLabel("Games Played: 0", self)
        self.lbl_games.setStyleSheet("color:white;")
        v.addWidget(self.lbl_runtime)
        v.addWidget(self.lbl_games)

        v.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # ---- start/stop button
        self.btn_toggle = QPushButton("Start", self)
        self.btn_toggle.setFixedHeight(42)
        self.btn_toggle.clicked.connect(self._toggle_bot)
        self.btn_toggle.setStyleSheet(
            f"QPushButton{{background:{self.PRIMARY};color:white;border:none;border-radius:8px;font-size:16px;}}"
            f"QPushButton:hover{{background:{self.LIGHT};}}"
        )
        v.addWidget(self.btn_toggle)

        # Footer label
        footer = QLabel("Made by Nox.", self)
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("color:#666;font-size:10px; margin-top:6px;")
        v.addWidget(footer)

        # --- hidden disclaimer (obfuscated)
        import base64 as _b64
        _d = _b64.b64decode("VGhpcyBzb2Z0d2FyZSBpcyBmcmVlLiBJZiB5b3UgYm91Z2h0IGl0IHlvdSBnb3Qgc2NhbW1lZC4=").decode()
        # store as a dynamic property, hidden from UI
        container.setProperty("_vd", _d)

        self.resize(400, 500)
        # center
        geo = QGuiApplication.primaryScreen().geometry()
        self.move(geo.center() - self.rect().center())

    # --------------------------- settings persistence
    def _load_settings(self):
        stg = load_settings()
        self.le_hook.setText(stg.get("webhook", ""))
        # future: loadout index if stored

    def _save_settings(self):
        save_settings({"webhook": self.le_hook.text().strip()})

    # --------------------------- interaction
    def _toggle_bot(self):
        if self.bot_thread and self.bot_thread.isRunning():
            # stop
            import bot
            bot.set_shutdown_requested(True)
            self.btn_toggle.setEnabled(False)
            return

        # start
        self.start_time = time.time()
        self._runtime_timer.start(1000)
        self.lbl_runtime.setText("Runtime: 00:00:00")
        self.btn_toggle.setText("Stop")

        webhook_url = self.le_hook.text().strip()
        self.bot_thread = BotThread(webhook_url)
        self.bot_thread.game_count_changed.connect(self._on_game_count)
        self.bot_thread.stopped.connect(self._on_bot_stopped)
        self.bot_thread.start()

    def _on_game_count(self, count: int):
        self.lbl_games.setText(f"Games Played: {count}")

    def _on_bot_stopped(self):
        self._runtime_timer.stop()
        self.btn_toggle.setEnabled(True)
        self.btn_toggle.setText("Start")

    def _update_runtime(self):
        if self.start_time is None:
            return
        sec = int(time.time() - self.start_time)
        h = sec // 3600
        m = (sec % 3600) // 60
        s = sec % 60
        self.lbl_runtime.setText(f"Runtime: {h:02d}:{m:02d}:{s:02d}")

    # --------------------------- window behaviour
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._dragPos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()
            e.accept()

    def mouseMoveEvent(self, e):
        if e.buttons() & Qt.LeftButton and self._dragPos is not None:
            self.move(e.globalPosition().toPoint() - self._dragPos)
            e.accept()

    def closeEvent(self, e):
        self._save_settings()
        if self.bot_thread and self.bot_thread.isRunning():
            import bot
            bot.set_shutdown_requested(True)
            self.bot_thread.wait(2000)
        e.accept()

    def keyPressEvent(self, e: QKeyEvent):
        # Right Shift toggle: scan code 54 on Windows
        if e.key() == Qt.Key_Shift and e.nativeScanCode() == 54:
            self._toggle_bot()
        super().keyPressEvent(e)

# -----------------------------------------------------------------------------
# Application entry point
# -----------------------------------------------------------------------------

def main():
    # Hide console window on Windows for cleaner UX
    try:
        whnd = ctypes.windll.kernel32.GetConsoleWindow()
        if whnd:
            ctypes.windll.user32.ShowWindow(whnd, 0)  # SW_HIDE
    except Exception:
        pass

    app = QApplication(sys.argv)

    # Show loading splash
    splash = LoadingScreen()
    splash.show()

    # Pre-create main window and keep a strong reference so it isn't
    # garbage-collected when the local function returns.
    main_window = MainWindow()

    def _show_main():
        splash.close()
        import base64 as _b64msg, PySide6.QtWidgets as _qtw
        _m = _b64msg.b64decode("VGhpcyBzb2Z0d2FyZSBpcyBmcmVlLiBJZiB5b3UgYm91Z2h0IGl0IHlvdSBnb3Qgc2NhbW1lZC4=").decode()
        _qtw.QMessageBox.information(None, "Note", _m)
        main_window.show()

    # When splash animation finishes, display the main GUI
    splash.finished.connect(_show_main)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
