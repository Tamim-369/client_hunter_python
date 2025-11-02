import pyautogui
import time
import pandas as pd
import json
# print("Move your mouse to the desired location and click. The coordinates will be printed after 5 seconds.")
# time.sleep(5) # Give the user time to position the mouse

# x, y = pyautogui.position()
# print(f"You clicked at X: {x}, Y: {y}")
# time.sleep(5)
# pyautogui.click(867,634)
with open("extracted_ads.json", "r") as data:
    json_data = json.load(data)
    selected_fields = ['advertiser', 'advertiser_facebook_link', 'advertiser_website_link', 'contact', 'library_id']
    
    # Create DataFrame and rename columns to look better
    ads_df = pd.DataFrame(json_data['ads'])[selected_fields]
    ads_df.columns = ['Advertiser', 'Facebook Link', 'Website Link', 'Contact', 'Library ID']
    
    # Drop duplicates based on Advertiser column, keeping the first occurrence
    ads_df = ads_df.drop_duplicates(subset=['Advertiser'], keep='first')
    
    # Save to CSV with better formatting
    ads_df.to_csv('extracted_ads.csv', index=False)
