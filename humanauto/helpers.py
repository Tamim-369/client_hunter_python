import pyautogui
import pytesseract
from PIL import Image
import json
import re
import math
import time
import psutil, time
from humanauto import *
from typing import Any, Dict, List, Optional

import pyperclip

def get_text_boxes(screenshot, min_conf=50):
    """
    Extract all text boxes with confidence >= min_conf (0-100).
    Returns list of dicts: {'text': str, 'x': int, 'y': int, 'w': int, 'h': int, 'conf': int}
    """
    data = pytesseract.image_to_data(screenshot, output_type=pytesseract.Output.DICT)
    boxes = []
    n_boxes = len(data['text'])
    for i in range(n_boxes):
        conf = int(data['conf'][i])
        text = data['text'][i].strip()
        if conf >= min_conf and text:
            boxes.append({
                'text': text,
                'x': data['left'][i],
                'y': data['top'][i],
                'w': data['width'][i],
                'h': data['height'][i],
                'conf': conf
            })
    return boxes

def find_closest_match(target_text, boxes, last_pos):
    """
    Find the box whose text best matches target_text (case-insensitive substring),
    and among matches, return the one closest to last_pos (x, y).
    """
    candidates = []
    target_lower = target_text.lower()

    for box in boxes:
        if target_lower in box['text'].lower():
            center_x = box['x'] + box['w'] // 2
            center_y = box['y'] + box['h'] // 2
            dist = math.hypot(center_x - last_pos[0], center_y - last_pos[1])
            candidates.append((dist, center_x, center_y, box))

    if not candidates:
        return None

    # Sort by distance (closest first)
    candidates.sort(key=lambda x: x[0])
    _, click_x, click_y, matched_box = candidates[0]
    return click_x, click_y, matched_box

def execute_click_sequence(steps_json):
    """
    Execute a sequence of clicks based on JSON input.
    steps_json: str or dict containing list of {"text": "...", "sleep": N}
    """
    if isinstance(steps_json, str):
        steps = json.loads(steps_json)
    else:
        steps = steps_json

    # Start from screen center if no prior click
    screen_w, screen_h = pyautogui.size()
    last_click_pos = (screen_w // 2, screen_h // 2)

    for step in steps:
        target_text = step['text']
        sleep_time = step.get('sleep', 0)

        print(f"\n🔍 Looking for text: '{target_text}'")

        # Take full screenshot
        screenshot = pyautogui.screenshot()

        # Get all text boxes with confidence >= 50%
        boxes = get_text_boxes(screenshot, min_conf=50)

        if not boxes:
            print("⚠️ No text detected on screen.")
            time.sleep(sleep_time)
            continue

        # Find closest match to target_text near last_click_pos
        result = find_closest_match(target_text, boxes, last_click_pos)

        if result:
            click_x, click_y, matched_box = result
            print(f"✅ Clicking '{matched_box['text']}' at ({click_x}, {click_y}) [conf: {matched_box['conf']}%]")
            pyautogui.click(click_x, click_y)
            last_click_pos = (click_x, click_y)
        else:
            print(f"❌ Text '{target_text}' not found (even with low confidence).")

        if sleep_time > 0:
            print(f"😴 Sleeping for {sleep_time} second(s)...")
            time.sleep(sleep_time)



def click_on_text(target_text, min_conf=40, sleep_after=0, last_pos=None):
    """
    Capture the screen, find text closest to target_text using OCR,
    and click on it automatically.

    Args:
        target_text (str): The text to search for on screen.
        min_conf (int): Minimum OCR confidence threshold (default 50).
        sleep_after (float): Seconds to sleep after clicking.
        last_pos (tuple): Optional (x, y) last click position to prioritize nearby matches.

    Returns:
        dict or None: Returns info about clicked text box if found, else None.
    """
    screen_w, screen_h = pyautogui.size()
    if last_pos is None:
        last_pos = (screen_w // 2, screen_h // 2)

    print(f"\n🎯 Searching for '{target_text}'...")

    screenshot = pyautogui.screenshot()
    boxes = get_text_boxes(screenshot, min_conf=min_conf)

    if not boxes:
        print("⚠️ No text detected on screen.")
        return None

    result = find_closest_match(target_text, boxes, last_pos)

    if result:
        click_x, click_y, matched_box = result
        print(f"✅ Found '{matched_box['text']}' at ({click_x}, {click_y}) [conf: {matched_box['conf']}%]")
        pyautogui.click(click_x, click_y)
        if sleep_after > 0:
            print(f"😴 Sleeping {sleep_after}s after click...")
            time.sleep(sleep_after)
        return matched_box
    else:
        print(f"❌ Could not find '{target_text}' on screen.")
        return None
def wait_until_appears_text(target_text, timeout=30, min_conf=50, interval=0.5, region=None, fast=True):
    """
    Wait until target_text appears on the screen (OCR-based detection, optimized).

    Args:
        target_text (str): The text to wait for.
        timeout (int): Max seconds to wait before giving up (default 30).
        min_conf (int): Minimum confidence threshold for OCR.
        interval (float): Seconds between checks.
        region (tuple): Optional (x, y, width, height) for faster region scanning.
        fast (bool): If True, converts to grayscale for speed.

    Returns:
        dict or None: The matched text box dict if found, else None.
    """
    start_time = time.time()
    last_hash = None

    print(f"⏳ Waiting for '{target_text}' to appear (timeout {timeout}s)...")

    while True:
        screenshot = pyautogui.screenshot(region=region)
        if fast:
            screenshot = screenshot.convert("L")  # Grayscale for faster OCR

        # Hash image to skip identical frames
        current_hash = hash(screenshot.tobytes())
        if current_hash == last_hash:
            time.sleep(interval)
            continue
        last_hash = current_hash

        boxes = get_text_boxes(screenshot, min_conf=min_conf)
        if boxes:
            result = find_closest_match(target_text, boxes, (0, 0))
            if result:
                click_x, click_y, matched_box = result
                print(f"✅ '{matched_box['text']}' appeared at ({click_x}, {click_y}) [conf: {matched_box['conf']}%]")
                return matched_box

        if time.time() - start_time > timeout:
            print(f"❌ Timeout: '{target_text}' not found within {timeout}s.")
            return None

        time.sleep(interval)


def wait_until_appears_image(image_path, timeout=30, confidence=0.8, interval=0.5):
    """
    Wait until a specific image appears on the screen.
    
    Args:
        image_path (str): Path to the reference image (e.g. "agree.png")
        timeout (float): Maximum seconds to wait before giving up.
        confidence (float): Matching accuracy (0.8 = 80%)
        interval (float): Seconds between each check.
    
    Returns:
        (x, y) center coordinates if found, or None if not found.
    """
    start_time = time.time()
    print(f"⏳ Waiting for image '{image_path}' to appear (timeout {timeout}s)...")
    while True:
        try:
            location = pyautogui.locateCenterOnScreen(image_path, confidence=confidence)
            if location:
                print(f"✅ Image '{image_path}' appeared at {location}")
                return location
        except pyautogui.ImageNotFoundException:
            pass
        if time.time() - start_time > timeout:
            print(f"❌ Timeout: Image '{image_path}' not found within {timeout}s.")
            return None
        time.sleep(interval)




def click_on_image(image_path, timeout=30, confidence=0.8, move_duration=0.3):
    """
    Waits for an image to appear on screen and clicks it once found.
    - Smoothly moves mouse to image before clicking
    - Handles ImageNotFoundException and other exceptions safely
    - Returns True if clicked successfully, False otherwise
    """
    start_time = time.time()
    print(f"🖼️ Waiting for image '{image_path}' to appear (timeout: {timeout}s)...")

    while True:
        try:
            location = pyautogui.locateCenterOnScreen(image_path, confidence=confidence)
            if location:
                print(f"✅ Image '{image_path}' found at {location}, moving and clicking...")
                pyautogui.moveTo(location.x, location.y, duration=move_duration)
                pyautogui.click()
                print(f"🖱️ Clicked on '{image_path}' successfully!")
                return True
        except pyautogui.ImageNotFoundException:
            pass
        except Exception as e:
            print(f"⚠️ Error while clicking '{image_path}': {e}")

        if time.time() - start_time > timeout:
            print(f"❌ Timeout: Image '{image_path}' not found within {timeout}s.")
            return False

        time.sleep(0.5)



def scroll_until_appears_image(image_path, timeout=30, confidence=0.8, interval=2, scroll_amount=-10):
    """
    Scrolls the screen until a specific image appears or timeout is reached.
    
    Args:
        image_path (str): Path to the reference image (e.g. "agree.png")
        timeout (float): Max seconds to wait before giving up.
        confidence (float): Matching accuracy (0.8 = 80%)
        interval (float): Seconds between scroll checks.
        scroll_amount (int): Scroll amount (negative = down, positive = up)
    
    Returns:
        (x, y): center coordinates if found, or None if not found.
    """
    start_time = time.time()
    print(f"⏳ Scrolling until '{image_path}' appears (timeout {timeout}s)...")

    while True:
        try:
            location = pyautogui.locateCenterOnScreen(image_path, confidence=confidence)
            if location:
                print(f"✅ Image '{image_path}' found at {location}")
                return location
        except pyautogui.ImageNotFoundException:
            pass
        
        # Timeout check
        if time.time() - start_time > timeout:
            print(f"❌ Timeout: '{image_path}' not found within {timeout}s.")
            return None
        
        # Scroll down and wait a bit
        pyautogui.scroll(scroll_amount)
        time.sleep(interval)

def chatDuckAIJson(prompt:str):
    press("Win","9")
    wait(0.5)

    run("google-chrome --incognito")
    wait(0.5)
    write("https://duckduckgo.com/?q=DuckDuckGo+AI+Chat&ia=chat&duckai=1", interval=0.01)
    press("Enter")
    wait(1)
    wait_until_appears_image("./assets/ocr/duckai_loaded.png")
    wait(0.5)
    click_on_image("./assets/ocr/duckai_agree.png")
    wait(0.5)
    click_on_image("./assets/ocr/duckai_chat.png")
    wait(0.5)
    copy_var_and_paste(prompt)
    wait(1)
    press("Enter")
    wait(0.5)
    press("Enter")
    wait(0.5)
    wait_until_appears_image("./assets/ocr/duckai_chat2.png")
    wait(0.5)
    click_on_image("./assets/ocr/duckai_random.png")
    wait(0.5)
    pyautogui.moveTo(960,540)
    wait(0.5)
    press("Ctrl", "f")
    wait(0.5)
    write("copy code")
    wait(0.5)
    wait_until_appears_image("./assets/ocr/duckai_copy_code2.png")
    wait(0.5)
    click_on_image("./assets/ocr/duckai_copy_code2.png")
    wait(2)
    copied_text = get_copied_value()
    print(copied_text)
    press("Alt", "F4")
    data = json.loads(copied_text)
    return data
