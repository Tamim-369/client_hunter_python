# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from bs4 import BeautifulSoup
# import time

# def scrape_facebook_with_popup_close_and_scroll(url, scroll_duration=10):
#     chrome_options = Options()
#     chrome_options.add_argument("--headless")
#     chrome_options.add_argument("--no-sandbox")
#     chrome_options.add_argument("--disable-dev-shm-usage")
#     chrome_options.add_argument("--disable-gpu")
#     chrome_options.add_argument("--window-size=1920,1080")
#     chrome_options.add_argument(
#         "user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
#     )
#     # Optional: if using Chromium on Debian
#     # chrome_options.binary_location = "/usr/bin/chromium"

#     driver = webdriver.Chrome(options=chrome_options)
#     try:
#         print(f"[+] Loading page: {url}")
#         driver.get(url)

#         # Wait for body to appear
#         WebDriverWait(driver, 10).until(
#             EC.presence_of_element_located((By.TAG_NAME, "body"))
#         )

#         # Try to find and click any close button (case-insensitive aria-label)
#         try:
#             close_button = driver.find_element(
#                 By.XPATH,
#                 '//div[@aria-label="Close" or @aria-label="close"] | '
#                 '//button[@aria-label="Close" or @aria-label="close"] | '
#                 '//*[@aria-label="Close" or @aria-label="close"]'
#             )
#             if close_button.is_displayed() and close_button.is_enabled():
#                 print("[+] Found and clicking 'Close' element...")
#                 close_button.click()
#                 time.sleep(1)  # brief pause after click
#         except Exception as e:
#             print("[-] No 'Close' popup found or failed to click:", str(e))

#         # Scroll down for `scroll_duration` seconds
#         print(f"[+] Scrolling for {scroll_duration} seconds to load content...")
#         start_time = time.time()
#         while time.time() - start_time < scroll_duration:
#             driver.execute_script("window.scrollBy(0, 1000);")
#             time.sleep(0.2)  # small delay between scrolls

#         # Get body HTML after scrolling
#         body_element = driver.find_element(By.TAG_NAME, "body")
#         body_html = body_element.get_attribute("outerHTML")

#         # Parse with BeautifulSoup and clean
#         soup = BeautifulSoup(body_html, "html.parser")
#         for tag in soup(["script", "style", "svg", "noscript", "header", "footer", "nav", "aside"]):
#             tag.decompose()

#         text = soup.get_text(separator=" ", strip=True)
#         return text

#     except Exception as e:
#         print(f"[!] Error during scraping: {e}")
#         return None
#     finally:
#         driver.quit()

# # === Usage ===
# if __name__ == "__main__":
#     # Replace with a PUBLIC Facebook Page URL
#     page_url = "https://www.facebook.com/Ghorerbazarbd.comm"

#     extracted_text = scrape_facebook_with_popup_close_and_scroll(
#         url=page_url,
#         scroll_duration=10
#     )

#     if extracted_text:
#         print("\n[+] Extracted Text (first 1500 characters):\n")
#         print(extracted_text[:1500] + "..." if len(extracted_text) > 1500 else extracted_text)
#     else:
#         print("Failed to extract content.")



from utils.facebook import analyze_facebook_lead
import json
import time
import pandas as pd
results = []
print("Loading json data")
json_data = None
with open("extracted_ads.json", "r") as data:
     json_data = json.load(data)

for ad in json_data["ads"]:
        print(f"Analyzing: {ad['advertiser']}")

        # Clean URL
        fb_link = ad['advertiser_facebook_link']
        pagename = fb_link.split("com/")[1].replace("/", "")
        # Skip if no valid Facebook link
        isNumber = pagename.isnumeric()
        if not fb_link or "facebook.com" not in fb_link or isNumber:
            lead_result = {"probability": 0, "service": None, "reasoning": "No valid Facebook link"}
        else:
            lead_result = analyze_facebook_lead(fb_link)
            time.sleep(2)  # Be respectful to Groq + FB

        # Clean reasoning text by removing unwanted characters
        reasoning = lead_result['reasoning'].replace('"', '').replace('}\n', '').replace('```','\n').strip() if lead_result['reasoning'] else ''
        
        # Combine original ad data + analysis
        combined = {
            "Advertiser": ad['advertiser'],
            "Facebook Link": fb_link,
            "Website Link": ad['advertiser_website_link'],
            "Contact": ad['contact'],
            "Library ID": ad['library_id'],
            "Buy Probability (%)": lead_result['probability'],
            "Recommended Service": lead_result['service'],
            "Reasoning": reasoning
        }
        results.append(combined)
# Create DataFrame
df = pd.DataFrame(results)
# sort by probability of conversion
df = df.sort_values(by="Buy Probability (%)", ascending=False)

# Save to CSV
df.to_csv('analyzed_leads.csv', index=False, encoding='utf-8')
print("Successfully analyzed every facebook page and sorted according to probability and saved in csv")