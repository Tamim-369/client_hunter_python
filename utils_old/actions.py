import pyautogui
import time

# Press any key
def press(*args):
    pyautogui.hotkey(*args)
# sleep for certain amount of time
def wait(seconds):
    time.sleep(float(seconds))
# write anything
def write(text, interval = 0.05):
    pyautogui.write(text, interval=interval)
# click somewhere
def click(*args):
    pyautogui.click(*args)
# move to a certain location
def move(*args):
    pyautogui.moveTo(*args)
# scroll for a certain amount of time
def scroll(*args):
    pyautogui.scroll(*args)