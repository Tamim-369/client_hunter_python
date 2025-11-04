import pyautogui
import time
import os
import pyperclip
# Press any key
def press(*args):
    pyautogui.hotkey(*args)
# sleep for certain amount of time
def wait(seconds):
    time.sleep(float(seconds))
# write anything
def write(text, interval=0.05):
    """
    Types the given text using pyautogui, replacing newlines with two spaces.
    """
    # Replace newlines with two spaces
    text = text.replace("\n", "  ")
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
# execute operating system command
def run(*args):
    os.system(*args)
# say something
def say(text:str="No text in the argument"):
    os.system(f"espeak '{text}'")
# get the texts which were copied
def get_copied_value():
    return pyperclip.paste()
# copy and paste content from a variable
def copy_var_and_paste(var, delay=0.3):
    """
    Copies the text content of 'var' to clipboard and pastes it using Ctrl+V.
    """
    # Copy the text to clipboard
    pyperclip.copy(str(var))
    time.sleep(delay)  # small delay to ensure clipboard is ready
    
    # Paste it using Ctrl+V
    pyautogui.hotkey('ctrl', 'v')