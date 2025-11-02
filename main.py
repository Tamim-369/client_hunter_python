from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from utils import process_text_data
import urllib.parse
import html2text
import re
# === Browser Setup ===
options = Options()
options.binary_location = "/usr/bin/chromium"
options.add_argument("--headless")          # Critical: avoids ad blocker
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")
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
    query = "gym equipment"  # or loop through multiple queries
    url = (
        f"https://www.facebook.com/ads/library/"
        f"?active_status=active"
        f"&ad_type=all"
        f"&country=BD"
        f"&is_targeted_country=true"          # ← changed to TRUE
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
    print(f"✅ Saved to {filename}")

finally:
    driver.quit()
    print("Browser closed.")