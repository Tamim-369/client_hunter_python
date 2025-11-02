import pyautogui
import pytesseract
from PIL import Image
import json
import math
import time
from utils_old import *

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
