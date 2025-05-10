# =====================================================================
# Imports and Dependencies
# =====================================================================
import keyinput, time, win32gui, win32api, win32con, win32com.client, win32process, cv2, sys, ctypes
from PIL import ImageGrab
import numpy as np
import os, signal, threading
import re
import random
import requests
import json
from datetime import datetime, timezone, timedelta

# =====================================================================
# Configuration and Global Variables
# =====================================================================
# The directory of this script
pwd = os.path.dirname(os.path.realpath(sys.argv[0])) + "\\"

# Discord webhook URL - Will be set by GUI from settings.json
DISCORD_WEBHOOK_URL = ""

# Game state tracking variables
searching_sent = False
in_game_sent = False
game_finished_sent = False

# GUI integration variables
game_count = 0
update_game_count_callback = None
selected_loadout = "Loadout 1"  # Always use Loadout 1
shutdown_requested = False
start_time = None

# Windows process related stuff
window_pid = -1
window_path = ""
window_found = False
window_name = ""
window_x = 0
window_y = 0
window_width = 0
window_height = 0

# Path to the game's directory
game_directory_path = ""

# Movement control variables
keys = [keyinput.W, keyinput.D, keyinput.S, keyinput.A]
last_keypress_timestamp = time.time()
random_duration = 5
movement_enabled = False
prev_state = False

# The delay for pressing space when dropping off the ship
space_press_delay = 10.0

# The previous image used in the watchdog
old_img = None

# Window template for finding the game window
# This is the standard name 'Call of Duty® HQ' with Zero Width Spaces (U+200B) inserted
window_template = 'C\u200ba\u200bl\u200bl\u200b \u200bo\u200bf\u200b \u200b' \
                  'D\u200bu\u200bt\u200by\u200b®'


# =====================================================================
# Helper Functions
# =====================================================================
def path(relpath: str) -> str:
    return pwd + relpath


# =====================================================================
# Discord Notification Functions
# =====================================================================
def send_discord_embed(title, description, color=0x00ff00):
    """
    Send a formatted Discord webhook notification with embed.
    
    Args:
        title (str): The title of the embed
        description (str): The description/content of the embed
        color (int): The color of the embed in hex format (default: green)
    """
    now = datetime.now(timezone.utc)
    
    # Add emoji based on title
    emoji = ""
    if "Started" in title:
        emoji = "🚀 "
        # Description is provided by the caller
    elif "Match Started" in title:
        emoji = "🎮 "
        # Description is provided by the caller
    elif "Searching" in title:
        emoji = "🔍 "
        # Description is provided by the caller
    elif "Game Finished" in title:
        emoji = "🏆 "
        # Description is provided by the caller
    
    # Create the embed with enhanced formatting
    embed = {
        "title": f"{emoji}{title}",
        "description": description,
        "color": color,
        "timestamp": now.isoformat(),
        "footer": {
            "text": "© Velo Booster 2025",
            "icon_url": "https://images-ext-1.discordapp.net/external/1oWqzHeQsqj99s5L_pc9EO-8OQ-fBoaP0SQcMUJTLXU/https/i.ibb.co/FkS55qGR/e50bb5a4e6d8a46acdc9499cef1fc564.jpg"
        }
    }
    
    # Always use the specified username and avatar URL for all webhook messages
    payload = {
        "username": "Velo Booster",
        "avatar_url": "https://i.ibb.co/YTNdPVN4/velo-pfp.jpg",
        "embeds": [embed]
    }
    
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        if response.status_code != 204:
            print(f"Failed to send Discord webhook: {response.text}")
    except Exception as e:
        print(f"Error sending Discord webhook: {e}")


def send_shutdown_embed():
    """
    Send a shutdown notification to Discord with runtime statistics.
    """
    global game_count, start_time
    
    # Calculate runtime
    runtime_str = "Unknown"
    if start_time is not None:
        runtime = datetime.now() - start_time
        hours, remainder = divmod(runtime.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        runtime_str = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
    
    # Create a detailed description with statistics
    description = f"The bot has been stopped by the user.\n\n**Statistics:**\n• Games Played: **{game_count}**\n• Total Runtime: **{runtime_str}**"
    
    payload = {
        "username": "Velo Booster",
        "avatar_url": "https://i.ibb.co/YTNdPVN4/velo-pfp.jpg",
        "embeds": [{
            "title": "Velo Booster Stopped",
            "description": description,
            "color": 0x7f4fc3,  # Purple color
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "footer": {
                "text": "© Velo Booster 2025",
                "icon_url": "https://images-ext-1.discordapp.net/external/1oWqzHeQsqj99s5L_pc9EO-8OQ-fBoaP0SQcMUJTLXU/https/i.ibb.co/FkS55qGR/e50bb5a4e6d8a46acdc9499cef1fc564.jpg"
            }
        }]
    }
    
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        if response.status_code != 204:
            print(f"Failed to send Discord webhook: {response.text}")
    except Exception as e:
        print(f"Error sending Discord webhook: {e}")


def send_game_finished_screenshot():
    """
    Take a screenshot of the game and send it to Discord when a game finishes.
    """
    try:
        # Get window position and size
        if window_found:
            # Take a screenshot of only the game window
            img = screenshot(window_x, window_y, window_width, window_height)
            
            # Save the screenshot to a file
            screenshot_path = path("game_finished_screenshot.jpg")
            cv2.imwrite(screenshot_path, img)
            
            # Prepare the message
            now = datetime.now(timezone.utc)
            
            # Create the embed
            embed = {
                "title": "🏆 Mission Complete",
                "description": "Operation concluded. Velo Booster is ready for the next deployment.",
                "color": 0x9b75d0,  # Purple color
                "timestamp": now.isoformat(),
                "footer": {
                    "text": "© Velo Booster 2025",
                    "icon_url": "https://images-ext-1.discordapp.net/external/1oWqzHeQsqj99s5L_pc9EO-8OQ-fBoaP0SQcMUJTLXU/https/i.ibb.co/FkS55qGR/e50bb5a4e6d8a46acdc9499cef1fc564.jpg"
                }
            }
            
            # Get game stats if available
            global game_count
            
            # Add game stats to the embed
            embed["fields"] = [
                {
                    "name": "Games Played",
                    "value": str(game_count + 1),  # +1 because we increment after this function
                    "inline": True
                }
            ]
            
            # Calculate runtime if start_time is available
            if start_time is not None:
                runtime = datetime.now() - start_time
                hours, remainder = divmod(runtime.total_seconds(), 3600)
                minutes, seconds = divmod(remainder, 60)
                runtime_str = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
                
                embed["fields"].append({
                    "name": "Total Runtime",
                    "value": runtime_str,
                    "inline": True
                })
            
            # Send the file with the embed
            with open(screenshot_path, "rb") as f:
                files = {"file": ("screenshot.jpg", f, "image/jpeg")}
                
                # Always use the specified username and avatar URL
                webhook_data = {
                    "username": "Velo Booster",
                    "avatar_url": "https://i.ibb.co/YTNdPVN4/velo-pfp.jpg",
                    "embeds": [embed]
                }
                
                payload = {"payload_json": json.dumps(webhook_data)}
                
                response = requests.post(DISCORD_WEBHOOK_URL, files=files, data=payload)
                
                if response.status_code != 204 and response.status_code != 200:
                    print(f"Failed to send Discord webhook with screenshot: {response.text}")
        
    except Exception as e:
        print(f"Error sending game finished screenshot: {e}")


# =====================================================================
# Signal and Interrupt Handling
# =====================================================================
# Exit on interrupt (this is a multithreaded program so do it ourselves)
def interrupt_handler(signum, frame):
    global shutdown_requested
    shutdown_requested = True

# Register SIGINT handler only from the main thread to avoid errors when
# the module is imported inside a Qt worker thread.
if threading.current_thread() is threading.main_thread():
    signal.signal(signal.SIGINT, interrupt_handler)


# =====================================================================
# Window Management Functions
# =====================================================================
# Routine to kill a process, used when it gets frozen permanently
def killprocess(pid):
    """
    Kill a process by its PID.
    """
    try:
        os.kill(pid, signal.SIGTERM)
    except:
        print('Failed to kill process')


# Callback for windows enumeration
def getmwwindow(hwnd, extra):
    global window_name, window_found, window_pid, window_path, game_directory_path
    global window_x, window_y, window_width, window_height
    
    # Skip invisible windows
    if not win32gui.IsWindowVisible(hwnd):
        return
        
    w_name = win32gui.GetWindowText(hwnd)
    
    # Debug: Print all window names to help diagnose
    if w_name and len(w_name) > 3:  # Skip very short window names
        print(f"Found window: '{w_name}'")
    
    # Check if this is a COD or Battle.net window
    is_cod_window = False
    is_battlenet_window = False
    
    # Check for COD window with zero-width spaces (main template)
    if window_template in w_name:
        is_cod_window = True
        print(f"Found COD window with zero-width spaces: '{w_name}'")
    # Check for exact "Call of Duty"
    elif 'Call of Duty' == w_name:
        is_cod_window = True
        print(f"Found exact Call of Duty window: '{w_name}'")
    # Check if window name starts with "Call of Duty"
    elif w_name.startswith('Call of Duty'):
        is_cod_window = True
        print(f"Found window starting with Call of Duty: '{w_name}'")
    # Check for Battle.net
    elif 'Battle.net' == w_name:
        is_battlenet_window = True
        print(f"Found Battle.net window: '{w_name}'")
    
    # Skip if not a COD or Battle.net window
    if not is_cod_window and not is_battlenet_window:
        return
    
    # Prioritize COD windows over Battle.net
    if is_battlenet_window and window_found and window_name and 'Call of Duty' in window_name:
        print(f"Skipping Battle.net window because COD window already found: '{window_name}'")
        return
    
    window_name = w_name
    window_found = True
    
    print(f"Selected window: '{window_name}'")
    

    global window_pid
    global window_path
    global game_directory_path
    thread_id, window_pid = win32process.GetWindowThreadProcessId(hwnd)

    handle = win32api.OpenProcess(win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ, False, window_pid)
    window_path = win32process.GetModuleFileNameEx(handle, 0)
    game_directory_path = os.path.dirname(window_path)

    rect = win32gui.GetClientRect(hwnd)
    rect_with_borders = win32gui.GetWindowRect(hwnd)
    window_pos = win32gui.ClientToScreen(hwnd, (0, 0))
    global window_x
    global window_y
    global window_width
    global window_height
    window_x = window_pos[0]
    window_y = window_pos[1]
    window_width = rect[2]
    window_height = rect[3]

    # Get the size of borders
    window_width_with_borders = rect_with_borders[2] - rect_with_borders[0]
    window_height_with_borders = rect_with_borders[3] - rect_with_borders[1]

    total_border_width = window_width_with_borders - window_width
    total_border_height = window_height_with_borders - window_height
    # Horizontally, the border only comprises of the snapping border, which wraps the sides (and also the bottom)
    snapping_border_width = total_border_width / 2
    # But not the top of the top bar !
    top_bar_height = total_border_height - snapping_border_width

    # Check for whether or not the window has the right resolution
    if window_width != 1280 or window_height != 720:
        # If not, resize the window. Take into account the fact we are mixing coordinates with no borders
        # and coordinates with borders
        win32gui.SetWindowPos(hwnd,
                              0,
                              int(window_x - snapping_border_width),
                              int(window_y - top_bar_height),
                              int(1280 + total_border_width),
                              int(720 + total_border_height),
                              0)
        window_width = 1280
        window_width = 720


# =====================================================================
# Screenshot and Image Processing Functions
# =====================================================================
# Take a screenshot of the specified region
def screenshot(x, y, width, height):
    try:
        image = ImageGrab.grab(bbox=(x, y, x + width, y + height))
        image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        return image
    except Exception as e:
        print(f"Error taking screenshot: {e}")
        # Return a small blank image instead of None to avoid errors
        return np.zeros((10, 10, 3), dtype=np.uint8)


# Function to move around ingame
def move_around():
    if not movement_enabled:
        return
        
    current_time = time.time()

    global last_keypress_timestamp
    global random_duration

    if (current_time - last_keypress_timestamp) > random_duration:
        # Use only the keys that are defined in keyinput module
        movement_keys = [keyinput.W, keyinput.A, keyinput.S, keyinput.D]
        rand_key = random.choice(movement_keys)

        # Random duration for holding the key between 0.2 to 1.2 seconds
        hold_duration = random.uniform(0.2, 1.2)
        keyinput.holdKey(rand_key, hold_duration)

        # Update the timestamp
        last_keypress_timestamp = time.time()

        # Re-generate next action delay (more frequent and randomized)
        random_duration = random.uniform(0.5, 2.0)

        # Random chance to perform mouse actions
        mouse_chance = random.random()

        if mouse_chance < 0.6:
            x = random.randint(window_x + 100, window_x + window_width - 100)
            y = random.randint(window_y + 100, window_y + window_height - 100)
            win32api.SetCursorPos((x, y))

            if random.random() < 0.5:
                # Left click
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
                time.sleep(0.05)
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)
            else:
                # Right click
                win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, x, y, 0, 0)
                time.sleep(0.05)
                win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, x, y, 0, 0)

        # Occasionally move the mouse randomly
        if random.random() < 0.2:
            move_x = random.randint(window_x + 100, window_x + window_width - 100)
            move_y = random.randint(window_y + 100, window_y + window_height - 100)
            win32api.SetCursorPos((move_x, move_y))


# The delay for pressing space when dropping off the ship
space_press_delay = 10.0


# Function to press space
def press_space_delayed(x, y):
    # Wait for 10 seconds
    time.sleep(space_press_delay)
    keyinput.pressKey(keyinput.SPACE)
    time.sleep(0.05)
    keyinput.releaseKey(keyinput.SPACE)


def press_down(x, y):
    keyinput.pressKey(keyinput.S)
    time.sleep(0.05)
    keyinput.releaseKey(keyinput.S)


def press_up(x, y):
    keyinput.pressKey(keyinput.W)
    time.sleep(0.05)
    keyinput.releaseKey(keyinput.W)


def press_up_five_times(x, y):
    for i in range(0, 5):
        press_up(x, y)
        time.sleep(1.0)


# Function to pause after clicking
def click_and_pause(x, y):
    keyinput.click(x, y)
    time.sleep(2.0)


# =====================================================================
# Screenshot and Image Processing Functions
# =====================================================================
# Take a screenshot of the specified region
def screenshot(x, y, width, height):
    try:
        image = ImageGrab.grab(bbox=(x, y, x + width, y + height))
        image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        return image
    except Exception as e:
        print(f"Error taking screenshot: {e}")
        # Return a small blank image instead of None to avoid errors
        return np.zeros((10, 10, 3), dtype=np.uint8)


# Find a certain item in an image, returns the estimated position and associated threshold
def findItem(img, template):
    # Apply template Matching
    res = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)

    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

    w, h = template.shape[::-1]

    # Top left of the area
    top_left = max_loc
    # Buttom right of the area
    bottom_right = (top_left[0] + w, top_left[1] + h)

    # Zone to click if we do need
    middle_x = (top_left[0] + bottom_right[0]) / 2
    middle_y = (top_left[1] + bottom_right[1]) / 2

    return {'threshold' : max_val, 'x' : middle_x, 'y' : middle_y}


# Take a screenshot of the window
def screenshot(x, y, width, height):
    image = ImageGrab.grab(bbox = (x, y, x + width, y + height))
    image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    return image

# The previous image used in the watchdog
old_img = None

# The play button in the battle net window
battle_net_play_button = cv2.imread(path("Images/Battle.net/play_button.png"), cv2.IMREAD_GRAYSCALE)
battle_net_play_button_hovered = cv2.imread(path("Images/Battle.net/play_button_hovered.png"), cv2.IMREAD_GRAYSCALE)


# Check for the play button in the battle net window
def checkForBattleNetPlayButton() -> bool:
    # Try to find the window handle
    hwnd = win32gui.FindWindowEx(0, 0, 'Chrome_WidgetWin_0', battle_net_window_name)

    if hwnd == 0:
        return False

    rect = win32gui.GetClientRect(hwnd)
    window_pos = win32gui.ClientToScreen(hwnd, (0, 0))

    # Put it in foreground in case it is not and wait for a bit to ensure it is made visible
    # Workaround for foreground windows
    shell = win32com.client.Dispatch("WScript.Shell")
    shell.SendKeys('%')

    try:
        win32gui.SetForegroundWindow(hwnd)
    except:
        print('Error: SetForegroundWindow failed')

    time.sleep(1.0)

    # Screenshot the safe mode window
    battle_net_window_img = screenshot(window_pos[0], window_pos[1], rect[2], rect[3])

    # Convert it to grayscale for faster processing
    img = cv2.cvtColor(battle_net_window_img, cv2.COLOR_BGR2GRAY)

    # Try to find the "Play" button
    result = findItem(img, battle_net_play_button)

    # Click on it if was found
    if result['threshold'] > 0.90:
        keyinput.click(window_pos[0] + int(result['x']), window_pos[1] + int(result['y']))
        return True

    # Try to find the "Play" button if it is hovered
    result = findItem(img, battle_net_play_button_hovered)

    # Click on it if was found
    if result['threshold'] > 0.90:
        keyinput.click(window_pos[0] + int(result['x']), window_pos[1] + int(result['y']))
        return True

    return False

# Watchdog running on another thread, makes sure the Apex process didn't crash or is not stucked
def processwatchdog():
    while True:
        # Check for the process being alive every 60 seconds
        time.sleep(60)

        global window_pid
        global window_path
        global window_found

        hwnd = 0

        # Try to find the window handle
        if window_name is not None:
            hwnd = win32gui.FindWindow(None, window_name)

        # Make sure the Window is still alive
        if hwnd == 0:
            window_found = False

            # Delete the 'lock file' that the game creates when it's active,
            # to make sure the safemode window doesn't pop up
            mw_lock_file = game_directory_path + "\\__cod"

            try:
                os.remove(mw_lock_file)
            except OSError: # File may not exist anymore
                pass

            # Check for the battle net window
            if checkForBattleNetPlayButton() is True:
                continue

            # In case the window name changed slightly (P100 Infinity Ward anti cheat technique), try to re-fetch it
            win32gui.EnumWindows(getmwwindow, None)

            # If it is still not found, wait again
            if window_found is False:
                continue

        # Refresh the window's position
        win32gui.EnumWindows(getmwwindow, None)

        # Grab its handle
        hwnd = win32gui.FindWindow(None, window_name)

        # Put it in foreground
        # Workaround for foreground windows
        shell = win32com.client.Dispatch("WScript.Shell")
        shell.SendKeys('%')
        win32gui.SetForegroundWindow(hwnd)

        global old_img

        # Capture the window in color
        color_img = screenshot(window_x, window_y, window_width, window_height)

        # Convert it to grayscale for faster processing
        img = cv2.cvtColor(color_img, cv2.COLOR_BGR2GRAY)

        if (old_img is not None):
            # Compare the current image to the old one,
            # if it didn't change within 60 seconds, the process is likely stuck
            result = findItem(img, old_img)

            # We deem the image as being the same if it matches over 99.999%
            if result['threshold'] > 0.99999:
                # Kill the process if it matches
                killprocess(window_pid)

        # Save the current image to compare it to the next one being read
        old_img = img


# Templates that we are looking for in the image
warzone_button = cv2.imread(path("Images/warzone_button.png"), cv2.IMREAD_GRAYSCALE)
warzone_button_hovered = cv2.imread(path("Images/warzone_button_hovered.png"), cv2.IMREAD_GRAYSCALE)

# Only load the plunder button images since we're only using plunder mode
plunder_button = cv2.imread(path("Images/plunder_button.png"), cv2.IMREAD_GRAYSCALE)
plunder_button_hovered = cv2.imread(path("Images/plunder_button_hovered.png"), cv2.IMREAD_GRAYSCALE)

find_a_match_button = cv2.imread(path("Images/find_a_match_button.png"), cv2.IMREAD_GRAYSCALE)

leave_match_button = cv2.imread(path("Images/leave_match_button.png"), cv2.IMREAD_GRAYSCALE)
leave_match_button_hovered = cv2.imread(path("Images/leave_match_button_hovered.png"), cv2.IMREAD_GRAYSCALE)
leave_match_alt_button = cv2.imread(path("Images/leave_match_alt_button.png"), cv2.IMREAD_GRAYSCALE)
leave_match_alt_button_hovered = cv2.imread(path("Images/leave_match_alt_button_hovered.png"), cv2.IMREAD_GRAYSCALE)

yes_button = cv2.imread(path("Images/yes_button.png"), cv2.IMREAD_GRAYSCALE)
yes_button_hovered = cv2.imread(path("Images/yes_button_hovered.png"), cv2.IMREAD_GRAYSCALE)

jump_prompt = cv2.imread(path("Images/jump_prompt.png"), cv2.IMREAD_GRAYSCALE)

dismiss_button = cv2.imread(path("Images/dismiss_button.png"), cv2.IMREAD_GRAYSCALE)
dismiss_button_hovered = cv2.imread(path("Images/dismiss_button_hovered.png"), cv2.IMREAD_GRAYSCALE)

after_action_report = cv2.imread(path("Images/after_action_report.png"), cv2.IMREAD_GRAYSCALE)

loadout1 = cv2.imread(path("Images/loadout1.png"), cv2.IMREAD_GRAYSCALE)

x1_button = cv2.imread(path("Images/x1.png"), cv2.IMREAD_GRAYSCALE)
x2_button = cv2.imread(path("Images/x2.png"), cv2.IMREAD_GRAYSCALE)
x3_button = cv2.imread(path("Images/x3.png"), cv2.IMREAD_GRAYSCALE)
x4_button = cv2.imread(path("Images/x4.png"), cv2.IMREAD_GRAYSCALE)

exit_button = cv2.imread(path("Images/exit.png"), cv2.IMREAD_GRAYSCALE)
quit_match_button = cv2.imread(path("Images/quit_match.png"), cv2.IMREAD_GRAYSCALE) 
yes_quit_match_button = cv2.imread(path("Images/yes_quit_match.png"), cv2.IMREAD_GRAYSCALE)
restart_button = cv2.imread(path("Images/restart.png"), cv2.IMREAD_GRAYSCALE)
restart_button_hovered = cv2.imread(path("Images/restart_hovered.png"), cv2.IMREAD_GRAYSCALE)
dev_error_ok_button = cv2.imread(path("Images/dev_error_ok.png"), cv2.IMREAD_GRAYSCALE)



# Additional templates that may be added depending on what the user selects

# When queuing the plunder mode
plunder_ui_elements = {"elements": [{"image" : plunder_button, "threshold" : 0.90, "callback" : keyinput.click},
                                    {"image" : find_a_match_button, "threshold" : 0.90, "callback" : keyinput.click},
                                    {"image" : plunder_button_hovered, "threshold" : 0.90, "callback" : keyinput.click},
                                    {"image" : warzone_button, "threshold": 0.95, "callback" : keyinput.click},
                                    {"image" : warzone_button_hovered, "threshold": 0.90, "callback" : keyinput.click},
                                    {"image" : find_a_match_button, "threshold": 0.95, "callback": keyinput.click},
                                    {"image" : leave_match_button, "threshold": 0.90, "callback": keyinput.click},
                                    {"image" : leave_match_button_hovered, "threshold": 0.95, "callback": keyinput.click},
                                    {"image" : leave_match_alt_button, "threshold": 0.90, "callback": keyinput.click},
                                    {"image" : leave_match_alt_button_hovered, "threshold": 0.95, "callback": keyinput.click},
                                    {"image" : yes_button, "threshold": 0.95, "callback": keyinput.click},
                                    {"image" : yes_button_hovered, "threshold": 0.95, "callback": keyinput.click},
                                    {"image" : jump_prompt, "threshold": 0.95, "callback": press_space_delayed},
                                    {"image" : dismiss_button, "threshold": 0.90, "callback": keyinput.click},
                                    {"image" : dismiss_button_hovered, "threshold": 0.95, "callback": keyinput.click},
                                    {"image" : battle_net_play_button, "threshold" : 0.90, "callback" : keyinput.click},
                                    {"image" : after_action_report, "threshold" : 0.90, "callback" : keyinput.click},
                                    {"image" : x1_button, "threshold" : 0.90, "callback" : keyinput.click},
                                    {"image" : x2_button, "threshold" : 0.90, "callback" : keyinput.click},
                                    {"image" : x3_button, "threshold" : 0.90, "callback" : keyinput.click},
                                    {"image" : x4_button, "threshold" : 0.90, "callback" : keyinput.click},
                                    {"image" : exit_button, "threshold" : 0.90, "callback" : keyinput.click},
                                    {"image" : quit_match_button, "threshold" : 0.90, "callback" : keyinput.click},
                                    {"image" : yes_quit_match_button, "threshold" : 0.90, "callback" : keyinput.click},
                                    {"image" : restart_button, "threshold" : 0.90, "callback" : keyinput.click},
                                    {"image" : restart_button_hovered, "threshold" : 0.90, "callback" : keyinput.click},
                                    {"image" : dev_error_ok_button, "threshold" : 0.90, "callback" : keyinput.click},
                                    {"image" : loadout1, "threshold" : 0.90, "callback" : keyinput.click}]}

# Function to reduce space press delay for certain modes
def reduce_space_press_delay():
    global space_press_delay
    space_press_delay = 5.0


optional_ui_elements = {"plunder" : plunder_ui_elements}


ui_elements = [{"image": warzone_button, "threshold": 0.95, "callback" : keyinput.click},
               {"image": warzone_button_hovered, "threshold": 0.90, "callback" : keyinput.click},
               {"image": find_a_match_button, "threshold": 0.95, "callback": keyinput.click},
               {"image": leave_match_button, "threshold": 0.90, "callback": keyinput.click},
               {"image": leave_match_button_hovered, "threshold": 0.95, "callback": keyinput.click},
               {"image": leave_match_alt_button, "threshold": 0.90, "callback": keyinput.click},
               {"image": leave_match_alt_button_hovered, "threshold": 0.95, "callback": keyinput.click},
               {"image": yes_button, "threshold": 0.95, "callback": keyinput.click},
               {"image": yes_button_hovered, "threshold": 0.95, "callback": keyinput.click},
               {"image": jump_prompt, "threshold": 0.95, "callback": press_space_delayed},
               {"image": dismiss_button, "threshold": 0.90, "callback": keyinput.click},
               {"image": dismiss_button_hovered, "threshold": 0.95, "callback": keyinput.click}]


available_launch_options = []  # No launch options needed since we only use plunder mode


# Always use plunder mode
print("Using plunder mode")
for ui_element in optional_ui_elements["plunder"]["elements"]:
    ui_elements.insert(0, ui_element)
if "callback" in optional_ui_elements["plunder"]:
    optional_ui_elements["plunder"]["callback"]()

# ui_elements.insert(0, {"image": continue_button, "threshold": 0.95, "callback": keyinput.click})
# ui_elements.insert(0, {"image": continue_button_hovered, "threshold": 0.95, "callback": keyinput.click})
# ui_elements.insert(0, {"image": exit_button, "threshold": 0.95, "callback": keyinput.click})
# ui_elements.insert(0, {"image": exit_button_hovered, "threshold": 0.95, "callback": keyinput.click})

# No launch options to process since we only use plunder mode


# Set ourselves as DPI aware, or else we won't get proper pixel coordinates if scaling is not 100%
errorCode = ctypes.windll.shcore.SetProcessDpiAwareness(2)

# =====================================================================
# GUI Integration Functions
# =====================================================================
def set_update_game_count_callback(callback):
    """
    Set the callback function for updating the game count in the GUI.
    """
    global update_game_count_callback
    update_game_count_callback = callback


def set_selected_loadout(loadout):
    """
    Set the selected loadout for the bot.
    """
    global selected_loadout
    selected_loadout = loadout
    print(f"Selected loadout: {loadout}")


def get_game_count():
    """
    Get the current game count.
    """
    global game_count
    return game_count


def set_shutdown_requested(value):
    """
    Set the shutdown requested flag.
    """
    global shutdown_requested
    shutdown_requested = value
    print(f"Shutdown requested: {value}")
    if value:
        send_shutdown_embed()


# The following startup routine should run only when bot.py is executed
# directly, not when it is imported by the GUI. This prevents unwanted
# attempts to interact with Battle.net during GUI import.
if __name__ == "__main__":
    print("Warzone bot starting in 5 seconds, bring Warzone window in focus...")
    time.sleep(5)

    win32gui.EnumWindows(getmwwindow, None)

    # If the window hasn't been found, try to launch it through Battle.net
    if window_found == False:
        print("No Warzone window found, attempting to launch through Battle.net...")
        # Try to find and click the Battle.net play button
        if checkForBattleNetPlayButton():
            print("Clicked Battle.net play button, waiting for game to start...")
            # Wait for the game to start
            for attempt in range(30):  # Try for 30 * 5 = 150 seconds
                time.sleep(5)
                win32gui.EnumWindows(getmwwindow, None)
                if window_found:
                    print("Warzone window found!")
                    break
                # Try clicking the play button again every 30 seconds
                if attempt % 6 == 5:
                    checkForBattleNetPlayButton()
        
        # If we still haven't found the window, exit
        if not window_found:
            print("Failed to find Warzone window after launching. Exiting.")
            sys.exit(1)
    else:
        print("Could not find Battle.net play button. Exiting.")
        sys.exit(1)

# =====================================================================
# Main Bot Logic
# =====================================================================
def main_loop():
    global movement_enabled, prev_state, searching_sent, in_game_sent, game_finished_sent, shutdown_requested, start_time
    
    # Initialize start time if not already set (when called from GUI)
    if start_time is None:
        start_time = datetime.now()
        print(f"Start time initialized: {start_time}")
    
    print("Starting main loop...")
    print(f"Looking for game windows...")
    
    # List all visible windows for debugging
    print("Listing all visible windows for debugging:")
    def list_all_windows(hwnd, extra):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title and len(title) > 3:  # Skip very short window names
                print(f"Window: '{title}' (hwnd: {hwnd})")
    win32gui.EnumWindows(list_all_windows, None)
    
    # Try to find the game window before starting
    print("\nLooking for Call of Duty or Battle.net window...")
    win32gui.EnumWindows(getmwwindow, None)
    
    if window_found:
        print(f"Found game window: {window_name}")
    else:
        print("Game window not found initially, will continue searching...")

    while not shutdown_requested:
        # If the window died, try to relaunch the game through Battle.net
        if window_found is False:
            print("Warzone window not found, attempting to find it...")
            # Try to find all potential windows
            win32gui.EnumWindows(getmwwindow, None)
            
            if not window_found:
                print("Still couldn't find game window, trying Battle.net...")
                if checkForBattleNetPlayButton():
                    print("Clicked Battle.net play button, waiting for game to restart...")
                    # Wait for the game to start
                    time.sleep(5.0)
                    # Try to find the window again
                    win32gui.EnumWindows(getmwwindow, None)
                else:
                    print("Could not find Battle.net play button. Will try again in 5 seconds...")
                    time.sleep(5.0)
            # Continue the main loop to keep trying
            continue

        # Capture the window in color
        color_img = screenshot(window_x, window_y, window_width, window_height)
        # Convert it to grayscale for faster processing
        img = cv2.cvtColor(color_img, cv2.COLOR_BGR2GRAY)

        found_UI_element = False
    
        # Check for loadout presence (in-game) to enable movement
        loadout_found = False
        
        # Only check for loadout1 since that's the only one we support
        img_check = loadout1
        result = findItem(img, img_check)
        if result['threshold'] > 0.90:
            movement_enabled = True
            loadout_found = True
            
            # Print a message when movement is first enabled
            if movement_enabled != prev_state and movement_enabled:
                print("Loadout screen detected. Movement enabled.")
                
                # Send Discord notification when entering a game (only once per game)
                if not in_game_sent:
                    # Select the appropriate loadout based on settings
                    global selected_loadout, loadout_cycle_index, game_count
                    
                    # Always use Loadout 1
                    current_loadout = loadout1
                    
                    # Send Discord notification
                    send_discord_embed(
                        "Match Started",
                        "Connected to a lobby. Velo Booster is now in-game and actively monitoring your progress.\nGood luck, Operator! 🍀",
                        color=0x4f2c80
                    )
                    in_game_sent = True
                    searching_sent = False  # reset for future cycles
                    game_finished_sent = False  # reset for future cycles
                
            prev_state = movement_enabled
        
        # Check for find-a-match presence (searching) to disable movement
        if not loadout_found:
            # Check for UI elements that indicate we're not in-game with named elements
            non_game_ui = [
                {"image": find_a_match_button, "name": "find_a_match"},
                {"image": warzone_button, "name": "warzone"},
                {"image": warzone_button_hovered, "name": "warzone_hovered"},
                {"image": leave_match_button, "name": "leave_match"},
                {"image": leave_match_button_hovered, "name": "leave_match_hovered"},
                {"image": dismiss_button, "name": "dismiss"},
                {"image": dismiss_button_hovered, "name": "dismiss_hovered"},
                {"image": exit_button, "name": "exit"},
                {"image": quit_match_button, "name": "quit_match"},
                {"image": yes_quit_match_button, "name": "yes_quit_match"},
                {"image": restart_button, "name": "restart"},
                {"image": restart_button_hovered, "name": "restart_hovered"}
            ]
            
            for ui_item in non_game_ui:
                result = findItem(img, ui_item["image"])
                if result['threshold'] > 0.90:
                    movement_enabled = False
                    
                    # Print a message when movement is first disabled
                    if movement_enabled != prev_state and not movement_enabled:
                        print("Not in-game. Movement disabled.")
                    
                    # Check specifically for find-a-match button (searching for game)
                    if ui_item["name"] == "find_a_match" and not searching_sent:
                        send_discord_embed(
                            "Searching for Match",
                            "Queueing up... Searching the battlefield for the next mission.\nVelo Booster is on standby and ready to deploy.",
                            color=0x6639a6
                        )
                        searching_sent = True
                        in_game_sent = False  # reset for future cycles
                    
                    # Check specifically for dismiss button (game finished)
                    if (ui_item["name"] == "dismiss" or ui_item["name"] == "dismiss_hovered") and not game_finished_sent:
                        # Wait 10 seconds before taking the screenshot to ensure XP screen is fully visible
                        print("Game finished detected - waiting 10 seconds before taking screenshot...")
                        time.sleep(10.0)
                        
                        # Take the screenshot after waiting
                        send_game_finished_screenshot()
                        game_finished_sent = True
                        
                        # Increment game count and update UI if callback is set
                        global game_count, update_game_count_callback
                        game_count += 1
                        if update_game_count_callback:
                            update_game_count_callback()
                        
                    prev_state = movement_enabled
                    break

        # Try to find any of the templates
        for ui_element in ui_elements:
            result = findItem(img, ui_element['image'])

            if result['threshold'] > ui_element['threshold']:
                found_UI_element = True
                ui_element['callback'](window_x + int(result['x']), window_y + int(result['y']))
                break

        # If no UI element got found, move around is the default behavior
        if found_UI_element is False:
            move_around()

        # Sleep for a second
        time.sleep(1.0)

# =====================================================================
# Main Entry Point
# =====================================================================
if __name__ == "__main__":
    # Record start time
    start_time = datetime.now()
    
    # Send initial startup notification
    send_discord_embed(
        "Velo Booster Online", 
        "Velo Booster is now live and scanning for game activity.\nSit back, relax, and let automation take the wheel. 🎮💤", 
        0x7f4fc3
    )

    # Start the main loop
    main_loop()
