from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from utils import process_text_data, analyze_facebook_lead, proccess_leads
import html2text
import re
import pandas as pd
import json

# === Browser Setup ===
options = Options()
options.binary_location = "/usr/bin/chromium"
options.add_argument("--headless")          # Critical: avoids ad blocker
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1932,1180")
options.add_argument("--disable-extensions")

from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

def clean_image_urls(text: str) -> str:
    """
    Remove image markdown syntax with Facebook CDN URLs.
    Pattern: ![anything](https://scontent...anything)
    """
    # Remove lines or parts containing ![...](...) with scontent URLs
    cleaned_text = re.sub(r'!\[.*?\]\(https://scontent[^\)]*\)', '', text)
    return cleaned_text

try:
    # === Build & Visit URL ===
    query = "online store Dhaka" 
    url = (
        f"https://www.facebook.com/ads/library/"
        f"?active_status=active"
        f"&ad_type=all"
        f"&country=BD"
        f"&is_targeted_country=true"
        f"&media_type=all"
        f"&q={query}"
        f"&search_type=keyword_unordered"
        f"&impression_condition=HAS_IMPRESSIONS_LAST_7DAYS"
    )

    print(f"Visiting: {url}")
    driver.get(url)

    # === Wait for ad blocker warning to disappear (if any) ===
    try:
        WebDriverWait(driver, 8).until_not(
            EC.presence_of_element_located((By.XPATH, "//div[contains(text(), '关闭广告拦截工具')]"))
        )
        print("✅ Ad blocker warning gone.")
    except:
        print("⚠️ Warning: Ad blocker message may still be present.")
        # Still proceed — maybe it didn't appear

    # === Wait for first ad to load using your signal ===
    print("Waiting for first ad (looking for 'Library ID: ')...")
    WebDriverWait(driver, 25).until(
        EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Library ID: ')]"))
    )
    print("✅ First ad loaded!")

    # === Scroll to bottom to load more ===
    print("Scrolling to bottom to load more ads...")
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(4)  # Wait for lazy-loaded ads

    # Optional: scroll multiple times if needed
    # for _ in range(3):
    #     driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    #     time.sleep(2)

    fullText = html2text.html2text(driver.page_source)
    fullText = clean_image_urls(fullText)

    filename = f"meta_ads_{query.replace(' ', '_')}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(fullText)
    
    process_text_data(fullText, query)
    with open("extracted_ads.json", "r") as data:
        json_data = json.load(data)
        selected_fields = ['advertiser', 'advertiser_facebook_link', 'advertiser_website_link', 'contact', 'library_id']
        
        # Create DataFrame and rename columns to look better
        ads_df = pd.DataFrame(json_data['ads'])[selected_fields]
        ads_df.columns = ['Advertiser', 'Facebook Link', 'Website Link', 'Contact', 'Library ID']

        # Drop duplicates based on Advertiser column, keeping the first occurrence
        ads_df = ads_df.drop_duplicates(subset=['Advertiser'], keep='first')

        # Save to CSV
        ads_df.to_csv('extracted_ads.csv', index=False)
        proccess_leads(json_data['ads'])
    print("\n\n[+]: Successfully analyzed every facebook page and sorted according to probability and saved in Database\n\n")
finally:
    driver.quit()
    print("Browser closed.")

