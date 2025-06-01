import keyinput, time, win32gui, win32api, win32con, win32com.client, win32process, cv2, sys, ctypes
from PIL import ImageGrab
import numpy as np
import os, signal, threading
import re
import random

# The directory of this script
pwd = os.path.dirname(os.path.realpath(sys.argv[0])) + "\\"


def path(relpath: str) -> str:
    return pwd + relpath


# Exit on interrupt (this is a multithreaded program so do it ourselves)
def interrupt_handler(signum, frame):
    os._exit(1) # Kinda hacky but I couldn't care less about a clean exit


signal.signal(signal.SIGINT, interrupt_handler)


# The template inside the name of the window we are looking for
# Yes, this clusterfuck is the standard name 'Call of Duty® HQ',
# With lots of Zero Width Spaces (U+200B) inserted inbetween, big Infinity-Ward anti-cheat !
window_template = 'C\u200ba\u200bl\u200bl\u200b \u200bo\u200bf\u200b \u200b' \
                  'D\u200bu\u200bt\u200by\u200b®'

# The name of the "Start in safe mode" window,
# in english (feel free to modify into your mother tongue)
safe_mode_window_name = 'Run In Safe Mode?'

# The name of the "DEV ERROR" windows (usually related to DirectX errors),
# in english (feel free to modify into your mother tongue)
dev_error_window_name = 'Fatal Error'

# The name of the battle.net window
battle_net_window_name = 'Battle.net'

# The complete name of the window that contains this template
window_name = None

# Position of the modern warfare window
window_x = -1
window_y = -1
window_width = -1
window_height = -1

# Windows process related stuff
window_pid = -1
window_path = ""
window_found = False

# Path to the game's directory
game_directory_path = ""

# Launch options parsed as arguments in the "optionname" or "optioname=value" format
launch_options = {}

# Routine to kill a process, used when it gets frozen permanently
def killprocess(pid):
    try:
        os.kill(pid, signal.SIGTERM)
    except:
        print('Failed to kill process')


# Callback for windows enumeration
def getmwwindow(hwnd, extra):
    w_name = win32gui.GetWindowText(hwnd)

    if window_template not in w_name:
        return

    global window_name
    window_name = w_name

    global window_found
    window_found = True

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


# Keys to press to move around
keys = [keyinput.W, keyinput.D, keyinput.S, keyinput.A]

# When moving around, how long in seconds since the last keypress.
last_keypress_timestamp = time.time()

# Start with a 'random' duration of activity 5 seconds
random_duration = 5


# Function to move around ingame
def move_around():
    current_time = time.time()

    global last_keypress_timestamp
    global random_duration

    if (current_time - last_keypress_timestamp) > random_duration:
        # Pick one of the keys
        rand_key_index = random.randint(0, 3)

        # Hold it for a second
        keyinput.holdKey(keys[rand_key_index], 1.0)

        last_keypress_timestamp = time.time()

        # Re-generate a random number between 2 and 4 (seconds).
        # If the amount of seconds since last keypress is greater,
        # we press a random key for a tenth of a second.
        random_duration = random.uniform(2.0, 4.0)


# The delay for pressing space when dropping off the ship
space_press_delay = 10.0


# The delay for pressing esc when exiting the game
esc_press_delay = 2.0


# Function to press space
def press_space_delayed(x, y):
    # Wait for 10 seconds
    time.sleep(space_press_delay)
    keyinput.pressKey(keyinput.SPACE)
    time.sleep(0.05)
    keyinput.releaseKey(keyinput.SPACE)

def press_esc_delayed(x, y):
    time.sleep(esc_press_delay)
    keyinput.pressKey(keyinput.ESC)
    time.sleep(0.05)
    keyinput.releaseKey(keyinput.ESC)


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
battle_net_play_button = cv2.imread(path("UI/Platforms/Battle.net/battle_net_play_button.png"), cv2.IMREAD_GRAYSCALE)
battle_net_play_button_hovered = cv2.imread(path("UI/Platforms/Battle.net/battle_net_play_button_hovered.png"), cv2.IMREAD_GRAYSCALE)

# The play button in the steam window
steam_play_button = cv2.imread(path("UI/Platforms/Steam/steam_play_button.png"), cv2.IMREAD_GRAYSCALE)
steam_play_button_hovered = cv2.imread(path("UI/Platforms/Steam/steam_play_button_hovered.png"), cv2.IMREAD_GRAYSCALE)

# The play button in the gamepass window
gamepass_play_button = cv2.imread(path("UI/Platforms/Gamepass/gamepass_play_button.png"), cv2.IMREAD_GRAYSCALE)
gamepass_play_button_hovered = cv2.imread(path("UI/Platforms/Gamepass/gamepass_play_button_hovered.png"), cv2.IMREAD_GRAYSCALE)



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
warzone_button = cv2.imread(path("UI/Misc/warzone_button.png"), cv2.IMREAD_GRAYSCALE)
warzone_button_hovered = cv2.imread(path("UI/Misc/warzone_button_hovered.png"), cv2.IMREAD_GRAYSCALE)

battle_royale_button = cv2.imread(path("UI/Gamemodes/BR/battle_royale_button.png"), cv2.IMREAD_GRAYSCALE)
battle_royale_button_hovered = cv2.imread(path("UI/Gamemodes/BR/battle_royale_button_hovered.png"), cv2.IMREAD_GRAYSCALE)
resurgence_button = cv2.imread(path("UI/Gamemodes/Resurgence/resurgence_button.png"), cv2.IMREAD_GRAYSCALE)
resurgence_button_hovered = cv2.imread(path("UI/Gamemodes/Resurgence/resurgence_button_hovered.png"), cv2.IMREAD_GRAYSCALE)
plunder_button = cv2.imread(path("UI/Gamemodes/Plunder/plunder_button.png"), cv2.IMREAD_GRAYSCALE)
plunder_button_hovered = cv2.imread(path("UI/Gamemodes/Plunder/plunder_button_hovered.png"), cv2.IMREAD_GRAYSCALE)

black_ops_button = cv2.imread(path("UI/Gamemodes/Multi/black_ops_button.png"), cv2.IMREAD_GRAYSCALE)
black_ops_button_hovered = cv2.imread(path("UI/Gamemodes/Multi/black_ops_button_hovered.png"), cv2.IMREAD_GRAYSCALE)
find_a_match_button_multi = cv2.imread(path("UI/Gamemodes/Multi/find_a_match_button.png"), cv2.IMREAD_GRAYSCALE)
find_a_match_button_multi_hovered = cv2.imread(path("UI/Gamemodes/Multi/find_a_match_button_hovered.png"), cv2.IMREAD_GRAYSCALE)
multiplayer_button = cv2.imread(path("UI/Gamemodes/Multi/multiplayer_button.png"), cv2.IMREAD_GRAYSCALE)
multiplayer_button_hovered = cv2.imread(path("UI/Gamemodes/Multi/multiplayer_button_hovered.png"), cv2.IMREAD_GRAYSCALE)
party_games_button = cv2.imread(path("UI/Gamemodes/Multi/party_games.png"), cv2.IMREAD_GRAYSCALE)
party_games_button_hovered = cv2.imread(path("UI/Gamemodes/Multi/party_games_hovered.png"), cv2.IMREAD_GRAYSCALE)
prop_hunt_button = cv2.imread(path("UI/Gamemodes/Multi/prop_hunt_button.png"), cv2.IMREAD_GRAYSCALE)
prop_hunt_button_hovered = cv2.imread(path("UI/Gamemodes/Multi/prop_hunt_button_hovered.png"), cv2.IMREAD_GRAYSCALE)
classified_button = cv2.imread(path("UI/Gamemodes/Multi/classified_button.png"), cv2.IMREAD_GRAYSCALE)
classified_button_hovered = cv2.imread(path("UI/Gamemodes/Multi/classified_button_hovered.png"), cv2.IMREAD_GRAYSCALE)
after_action_report_button = cv2.imread(path("UI/Gamemodes/Multi/after_action_report.png"), cv2.IMREAD_GRAYSCALE)
skip_dismiss = cv2.imread(path("UI/Gamemodes/Multi/skip_dismiss.png"), cv2.IMREAD_GRAYSCALE)
bug = cv2.imread(path("UI/Gamemodes/Multi/bug.png"), cv2.IMREAD_GRAYSCALE)


solos_button = cv2.imread(path("UI/Gamemodes/solos_button.png"), cv2.IMREAD_GRAYSCALE)
solos_button_hovered = cv2.imread(path("UI/Gamemodes/solos_button_hovered.png"), cv2.IMREAD_GRAYSCALE)
duos_button = cv2.imread(path("UI/Gamemodes/duos_button.png"), cv2.IMREAD_GRAYSCALE)
duos_button_hovered = cv2.imread(path("UI/Gamemodes/duos_button_hovered.png"), cv2.IMREAD_GRAYSCALE)
trios_button = cv2.imread(path("UI/Gamemodes/trios_button.png"), cv2.IMREAD_GRAYSCALE)
trios_button_hovered = cv2.imread(path("UI/Gamemodes/trios_button_hovered.png"), cv2.IMREAD_GRAYSCALE)
quads_button = cv2.imread(path("UI/Gamemodes/quads_button.png"), cv2.IMREAD_GRAYSCALE)
quads_button_hovered = cv2.imread(path("UI/Gamemodes/quads_button_hovered.png"), cv2.IMREAD_GRAYSCALE)

find_a_match_button = cv2.imread(path("UI/Misc/find_a_match_button.png"), cv2.IMREAD_GRAYSCALE)

loadout_button = cv2.imread(path("UI/Loadout/loadout1.png"), cv2.IMREAD_GRAYSCALE)


leave_match_button = cv2.imread(path("UI/Misc/leave_match_button.png"), cv2.IMREAD_GRAYSCALE)
leave_match_button_hovered = cv2.imread(path("UI/Misc/leave_match_button_hovered.png"), cv2.IMREAD_GRAYSCALE)
leave_match_alt_button = cv2.imread(path("UI/Misc/leave_match_alt_button.png"), cv2.IMREAD_GRAYSCALE)
leave_match_alt_button_hovered = cv2.imread(path("UI/Misc/leave_match_alt_button_hovered.png"), cv2.IMREAD_GRAYSCALE)

yes_button = cv2.imread(path("UI/Misc/yes_button.png"), cv2.IMREAD_GRAYSCALE)
yes_button_hovered = cv2.imread(path("UI/Misc/yes_button_hovered.png"), cv2.IMREAD_GRAYSCALE)

jump_prompt = cv2.imread(path("UI/Misc/jump_prompt.png"), cv2.IMREAD_GRAYSCALE)

dismiss_button = cv2.imread(path("UI/Misc/dismiss_button.png"), cv2.IMREAD_GRAYSCALE)
dismiss_button_hovered = cv2.imread(path("UI/Misc/dismiss_button_hovered.png"), cv2.IMREAD_GRAYSCALE)

exit_button = cv2.imread(path("UI/Misc/exit_button.png"), cv2.IMREAD_GRAYSCALE)
exit_button_hovered = cv2.imread(path("UI/Misc/exit_button_hovered.png"), cv2.IMREAD_GRAYSCALE)
skip_survey = cv2.imread(path("UI/Misc/skip_survey.png"), cv2.IMREAD_GRAYSCALE)
skip_survey_hovered = cv2.imread(path("UI/Misc/skip_survey_hovered.png"), cv2.IMREAD_GRAYSCALE)

quit_to_desktop = cv2.imread(path("UI/Misc/quit_to_desktop.png"), cv2.IMREAD_GRAYSCALE)
quit_to_desktop_hovered = cv2.imread(path("UI/Misc/quit_to_desktop_hovered.png"), cv2.IMREAD_GRAYSCALE)
no_crash = cv2.imread(path("UI/Misc/no_crash.png"), cv2.IMREAD_GRAYSCALE)
no_crash_hovered = cv2.imread(path("UI/Misc/no_crash_hovered.png"), cv2.IMREAD_GRAYSCALE)

menu_x  = cv2.imread(path("UI/Misc/menu_x.png"), cv2.IMREAD_GRAYSCALE)
menu_x1  = cv2.imread(path("UI/Misc/menu_x1.png"), cv2.IMREAD_GRAYSCALE)
menu_x2  = cv2.imread(path("UI/Misc/menu_x2.png"), cv2.IMREAD_GRAYSCALE)
menu_x3  = cv2.imread(path("UI/Misc/menu_x3.png"), cv2.IMREAD_GRAYSCALE)
menu_x4  = cv2.imread(path("UI/Misc/menu_x4.png"), cv2.IMREAD_GRAYSCALE)

quit_match = cv2.imread(path("UI/Misc/quit_match.png"), cv2.IMREAD_GRAYSCALE)
quit_match_hovered = cv2.imread(path("UI/Misc/quit_match_hovered.png"), cv2.IMREAD_GRAYSCALE)
yes_quit_match = cv2.imread(path("UI/Misc/yes_quit_match.png"), cv2.IMREAD_GRAYSCALE)
yes_quit_match_hovered = cv2.imread(path("UI/Misc/yes_quit_match_hovered.png"), cv2.IMREAD_GRAYSCALE)
return_to_game = cv2.imread(path("UI/Misc/return_to_game.png"), cv2.IMREAD_GRAYSCALE)
return_to_game_hovered = cv2.imread(path("UI/Misc/return_to_game_hovered.png"), cv2.IMREAD_GRAYSCALE)



# Additional templates that may be added depending on what the user selects

# When queuing for the battle royale solos mode
battle_royale_solos_ui_elements = {"elements": [{"image" : battle_royale_button, "threshold" : 0.90, "callback" : keyinput.click},
                                                {"image": warzone_button, "threshold": 0.95, "callback" : keyinput.click},
                                                {"image": warzone_button_hovered, "threshold": 0.90, "callback" : keyinput.click},
                                                {"image" : battle_royale_button_hovered, "threshold" : 0.90, "callback" : keyinput.click},
                                                {"image" : solos_button, "threshold" : 0.90, "callback" : keyinput.click},
                                                {"image" : solos_button_hovered, "threshold" : 0.90, "callback" : keyinput.click}]}

# When queuing for the battle royale duos mode
battle_royale_duos_ui_elements = {"elements": [{"image" : battle_royale_button, "threshold" : 0.90, "callback" : keyinput.click},
                                               {"image": warzone_button, "threshold": 0.95, "callback" : keyinput.click},
                                            {"image": warzone_button_hovered, "threshold": 0.90, "callback" : keyinput.click},
                                               {"image" : battle_royale_button_hovered, "threshold" : 0.90, "callback" : keyinput.click},
                                               {"image" : duos_button, "threshold" : 0.90, "callback" : keyinput.click},
                                               {"image" : duos_button_hovered, "threshold" : 0.90, "callback" : keyinput.click}]}

# When queuing for the battle royale trios mode
battle_royale_trios_ui_elements = {"elements": [{"image" : battle_royale_button, "threshold" : 0.90, "callback" : keyinput.click},
                                                {"image": warzone_button, "threshold": 0.95, "callback" : keyinput.click},
                                                {"image": warzone_button_hovered, "threshold": 0.90, "callback" : keyinput.click},
                                                {"image" : battle_royale_button_hovered, "threshold" : 0.90, "callback" : keyinput.click},
                                                {"image" : trios_button, "threshold" : 0.90, "callback" : keyinput.click},
                                                {"image" : trios_button_hovered, "threshold" : 0.90, "callback" : keyinput.click}]}

# When queuing the battle royale quads mode
battle_royale_quads_ui_elements = {"elements": [{"image" : battle_royale_button, "threshold" : 0.90, "callback" : keyinput.click},
                                                {"image": warzone_button, "threshold": 0.95, "callback" : keyinput.click},
                                                {"image": warzone_button_hovered, "threshold": 0.90, "callback" : keyinput.click},
                                                {"image" : battle_royale_button_hovered, "threshold" : 0.90, "callback" : keyinput.click},
                                                {"image" : quads_button, "threshold" : 0.90, "callback" : keyinput.click},
                                                {"image" : quads_button_hovered, "threshold" : 0.90, "callback" : keyinput.click}]}

# When queuing for the resurgence solos mode
resurgence_solos_ui_elements = {"elements": [{"image" : resurgence_button, "threshold" : 0.90, "callback" : keyinput.click},
                                             {"image": warzone_button, "threshold": 0.95, "callback" : keyinput.click},
                                             {"image": warzone_button_hovered, "threshold": 0.90, "callback" : keyinput.click},
                                             {"image" : resurgence_button_hovered, "threshold" : 0.90, "callback" : keyinput.click},
                                             {"image" : solos_button, "threshold" : 0.90, "callback" : keyinput.click},
                                             {"image" : solos_button_hovered, "threshold" : 0.90, "callback" : keyinput.click}]}

# When queuing for the resurgence duos mode
resurgence_duos_ui_elements = {"elements": [{"image" : resurgence_button, "threshold" : 0.90, "callback" : keyinput.click},
                                            {"image": warzone_button, "threshold": 0.95, "callback" : keyinput.click},
                                            {"image": warzone_button_hovered, "threshold": 0.90, "callback" : keyinput.click},
                                            {"image" : resurgence_button_hovered, "threshold" : 0.90, "callback" : keyinput.click},
                                            {"image" : duos_button, "threshold" : 0.90, "callback" : keyinput.click},
                                            {"image" : duos_button_hovered, "threshold" : 0.90, "callback" : keyinput.click}]}

# When queuing for the resurgence trios mode
resurgence_trios_ui_elements = {"elements": [{"image" : resurgence_button, "threshold" : 0.90, "callback" : keyinput.click},
                                             {"image": warzone_button, "threshold": 0.95, "callback" : keyinput.click},
                                             {"image": warzone_button_hovered, "threshold": 0.90, "callback" : keyinput.click},
                                             {"image" : resurgence_button_hovered, "threshold" : 0.90, "callback" : keyinput.click},
                                             {"image" : trios_button, "threshold" : 0.90, "callback" : keyinput.click},
                                             {"image" : trios_button_hovered, "threshold" : 0.90, "callback" : keyinput.click}]}

# When queuing the resurgence quads mode
resurgence_quads_ui_elements = {"elements": [{"image" : resurgence_button, "threshold" : 0.90, "callback" : keyinput.click},
                                             {"image": warzone_button, "threshold": 0.95, "callback" : keyinput.click},
                                             {"image": warzone_button_hovered, "threshold": 0.90, "callback" : keyinput.click},       
                                             {"image" : resurgence_button_hovered, "threshold" : 0.90, "callback" : keyinput.click},
                                             {"image" : quads_button, "threshold" : 0.90, "callback" : keyinput.click},
                                             {"image" : quads_button_hovered, "threshold" : 0.90, "callback" : keyinput.click}]}

# When queuing the plunder mode
plunder_ui_elements = {"elements": [{"image" : plunder_button, "threshold" : 0.90, "callback" : keyinput.click},
                                    {"image": warzone_button, "threshold": 0.95, "callback" : keyinput.click},
                                    {"image": warzone_button_hovered, "threshold": 0.90, "callback" : keyinput.click},
                                    {"image" : plunder_button_hovered, "threshold" : 0.90, "callback" : keyinput.click}]}

# When queuing the prop hunt mode
prop_hunt_ui_elements = {"elements": [{"image" : black_ops_button, "threshold" : 0.90, "callback" : keyinput.click},
                                      {"image" : black_ops_button_hovered, "threshold" : 0.90, "callback" : keyinput.click},
                                      {"image" : find_a_match_button_multi, "threshold" : 0.90, "callback" : keyinput.click},
                                      {"image" : find_a_match_button_multi_hovered, "threshold" : 0.90, "callback" : keyinput.click},
                                      {"image" : multiplayer_button, "threshold" : 0.90, "callback" : keyinput.click},
                                      {"image" : multiplayer_button_hovered, "threshold" : 0.90, "callback" : keyinput.click},
                                      {"image" : party_games_button, "threshold" : 0.90, "callback" : keyinput.click},
                                      {"image" : party_games_button_hovered, "threshold" : 0.90, "callback" : keyinput.click},
                                      {"image" : prop_hunt_button, "threshold" : 0.90, "callback" : keyinput.click},
                                      {"image" : prop_hunt_button_hovered, "threshold" : 0.90, "callback" : keyinput.click},
                                      {"image" : classified_button, "threshold" : 0.90, "callback" : keyinput.click},
                                      {"image" : classified_button_hovered, "threshold" : 0.90, "callback" : keyinput.click},
                                      {"image" : after_action_report_button, "threshold" : 0.90, "callback" : press_esc_delayed},
                                      {"image" : bug, "threshold" : 0.90, "callback" : press_esc_delayed},
                                      {"image" : skip_dismiss, "threshold" : 0.90, "callback" : press_esc_delayed}]}

# When queuing for the resurgence quads mode
def reduce_space_press_delay():
    global space_press_delay
    space_press_delay = 5.0


optional_ui_elements = {"battle-royale-quads" : battle_royale_quads_ui_elements,
                        "battle-royale-trios" : battle_royale_trios_ui_elements,
                        "battle-royale-duos" : battle_royale_duos_ui_elements,
                        "battle-royale-solos" : battle_royale_solos_ui_elements,
                        "resurgence-quads" : resurgence_quads_ui_elements,
                        "resurgence-trios" : resurgence_trios_ui_elements,
                        "resurgence-duos" : resurgence_duos_ui_elements,
                        "resurgence-solos" : resurgence_solos_ui_elements,
                        "plunder" : plunder_ui_elements,
                        "prop-hunt" : prop_hunt_ui_elements}


ui_elements = [{"image": menu_x, "threshold": 0.90, "callback": press_esc_delayed},
               {"image": menu_x1, "threshold": 0.90, "callback": press_esc_delayed},
               {"image": menu_x2, "threshold": 0.90, "callback": press_esc_delayed},
               {"image": menu_x3, "threshold": 0.90, "callback": press_esc_delayed},
               {"image": menu_x4, "threshold": 0.90, "callback": press_esc_delayed},
               {"image": find_a_match_button, "threshold": 0.95, "callback": keyinput.click},
               {"image": leave_match_button, "threshold": 0.90, "callback": keyinput.click},
               {"image": leave_match_button_hovered, "threshold": 0.95, "callback": keyinput.click},
               {"image": leave_match_alt_button, "threshold": 0.90, "callback": keyinput.click},
               {"image": leave_match_alt_button_hovered, "threshold": 0.95, "callback": keyinput.click},
               {"image": return_to_game, "threshold": 0.90, "callback": keyinput.click},
               {"image": return_to_game_hovered, "threshold": 0.95, "callback": keyinput.click},
               {"image": yes_button, "threshold": 0.95, "callback": keyinput.click},
               {"image": yes_button_hovered, "threshold": 0.95, "callback": keyinput.click},
               {"image": jump_prompt, "threshold": 0.95, "callback": press_space_delayed},
               {"image": exit_button, "threshold": 0.80, "callback": keyinput.click},
               {"image": exit_button_hovered, "threshold": 0.85, "callback": keyinput.click},
               {"image": dismiss_button, "threshold": 0.90, "callback": press_esc_delayed},
               {"image": loadout_button, "threshold": 0.90, "callback": keyinput.click},
               {"image": quit_match, "threshold": 0.90, "callback": keyinput.click},
               {"image": quit_match_hovered, "threshold": 0.90, "callback": keyinput.click},
               {"image": yes_quit_match, "threshold": 0.90, "callback": keyinput.click},
               {"image": yes_quit_match_hovered, "threshold": 0.90, "callback": keyinput.click},
               {"image": battle_net_play_button, "threshold": 0.90, "callback": keyinput.click},
               {"image": battle_net_play_button_hovered, "threshold": 0.90, "callback": keyinput.click},
               {"image": steam_play_button, "threshold": 0.90, "callback": keyinput.click},
               {"image": steam_play_button_hovered, "threshold": 0.90, "callback": keyinput.click},
               {"image": gamepass_play_button, "threshold": 0.90, "callback": keyinput.click},
               {"image": gamepass_play_button_hovered, "threshold": 0.90, "callback": keyinput.click},
               {"image": quit_to_desktop, "threshold": 0.90, "callback": keyinput.click},
               {"image": quit_to_desktop_hovered, "threshold": 0.90, "callback": keyinput.click},
               {"image": skip_survey, "threshold": 0.90, "callback": keyinput.click},
               {"image": skip_survey_hovered, "threshold": 0.90, "callback": keyinput.click},
               {"image": no_crash, "threshold": 0.90, "callback": keyinput.click},
               {"image": no_crash_hovered, "threshold": 0.90, "callback": keyinput.click},
               {"image": dismiss_button_hovered, "threshold": 0.95, "callback": keyinput.click}]


available_launch_options = [{'name' : 'mode=<mode_name>', 'description' : 'gamemode to queue for'}]


# Parse launch options if any
if len(sys.argv) > 1:
    # Regex used to parse options
    arg_regex_template = '(.*)=(.*)'
    arg_regex = re.compile(arg_regex_template)

    for argv in sys.argv[1:]:
        match = arg_regex.match(argv)
        if match is not None:
            launch_options[match.group(1)] = match.group(2)
        else:
            launch_options[argv] = None


if 'mode' in launch_options:
    mode = launch_options.pop('mode', None)
    if mode in optional_ui_elements:
        print(f"Selected gamemode: {mode}")
        for ui_element in optional_ui_elements[mode]["elements"]:
            ui_elements.insert(0, ui_element)
        if "callback" in optional_ui_elements[mode]:
            optional_ui_elements[mode]["callback"]()
    else:
        print(f"Unknown gamemode: '{mode}', exiting.")
        sys.exit(1)
else:
    print("No gamemode specified, defaulting to 'battle-royale-quads'")
    for ui_element in optional_ui_elements["battle-royale-quads"]["elements"]:
        ui_elements.insert(0, ui_element)
    if "callback" in optional_ui_elements["battle-royale-quads"]:
        optional_ui_elements["battle-royale-quads"]["callback"]()

# ui_elements.insert(0, {"image": continue_button, "threshold": 0.95, "callback": keyinput.click})
# ui_elements.insert(0, {"image": continue_button_hovered, "threshold": 0.95, "callback": keyinput.click})
# ui_elements.insert(0, {"image": exit_button, "threshold": 0.95, "callback": keyinput.click})
# ui_elements.insert(0, {"image": exit_button_hovered, "threshold": 0.95, "callback": keyinput.click})

# Print leftover launch options as unknown
for unknown_launch_option in launch_options:
    print(f"Unknown launch option: '{unknown_launch_option}'")

if launch_options:
    print("List of options:")
    for available_launch_option in available_launch_options:
        print(f"- {available_launch_option['name']} : {available_launch_option['description']}")
    sys.exit(1)


# Set ourselves as DPI aware, or else we won't get proper pixel coordinates if scaling is not 100%
errorCode = ctypes.windll.shcore.SetProcessDpiAwareness(2)

os.system("cls")
print("\n")
# Purple color ANSI code for #7A52B2
PURPLE = "\033[38;2;122;82;178m"
RESET = "\033[0m"

print(f"{PURPLE}██╗   ██╗███████╗██╗      ██████╗ {RESET}")
print(f"{PURPLE}██║   ██║██╔════╝██║     ██╔═══██╗{RESET}")
print(f"{PURPLE}██║   ██║█████╗  ██║     ██║   ██║{RESET}")
print(f"{PURPLE}╚██╗ ██╔╝██╔══╝  ██║     ██║   ██║{RESET}")
print(f"{PURPLE} ╚████╔╝ ███████╗███████╗╚██████╔╝{RESET}")
print(f"{PURPLE}  ╚═══╝  ╚══════╝╚══════╝ ╚═════╝ {RESET}")
print("\nStarting in 5 seconds, bring the Warzone window in focus...")
time.sleep(5)

win32gui.EnumWindows(getmwwindow, None)

# If the window hasn't been found, exit
if window_found == False:
    print("No Warzone window found")
    time.sleep(3)
    sys.exit(1)

# Start the watchdog thread
watchdogthread = threading.Thread(target = processwatchdog)
watchdogthread.start()

while True:
    # If the window died, stop running analysis for a moment */
    if window_found is False:
        time.sleep(5)
        continue

    # Capture the window in color
    color_img = screenshot(window_x, window_y, window_width, window_height)
    # Convert it to grayscale for faster processing
    img = cv2.cvtColor(color_img, cv2.COLOR_BGR2GRAY)

    found_UI_element = False

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
