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



from utils import analyze_facebook_lead
import json
import time
import pandas as pd
# results = []
# print("Loading json data")
# json_data = None
# with open("extracted_ads.json", "r") as data:
#      json_data = json.load(data)

# for ad in json_data["ads"]:
#         print(f"Analyzing: {ad['advertiser']}")

#         # Clean URL
#         fb_link = ad['advertiser_facebook_link']
#         pagename = fb_link.split("com/")[1].replace("/", "")
#         # Skip if no valid Facebook link
#         isNumber = pagename.isnumeric()
#         if not fb_link or "facebook.com" not in fb_link or isNumber:
#             lead_result = {"probability": 0, "service": None, "reasoning": "No valid Facebook link"}
#         else:
#             lead_result = analyze_facebook_lead(fb_link)
#             time.sleep(2)  # Be respectful to Groq + FB

#         # Clean reasoning text by removing unwanted characters
#         reasoning = lead_result['reasoning'].replace('"', '').replace('}\n', '').replace('```','\n').strip() if lead_result['reasoning'] else ''
        
#         # Combine original ad data + analysis
#         combined = {
#             "Advertiser": ad['advertiser'],
#             "Facebook Link": fb_link,
#             "Website Link": ad['advertiser_website_link'],
#             "Contact": ad['contact'],
#             "Library ID": ad['library_id'],
#             "Buy Probability (%)": lead_result['probability'],
#             "Recommended Service": lead_result['service'],
#             "Reasoning": reasoning
#         }
#         results.append(combined)
# # Create DataFrame
# df = pd.DataFrame(results)
# # sort by probability of conversion
# df = df.sort_values(by="Buy Probability (%)", ascending=False)

# # Save to CSV
# df.to_csv('analyzed_leads.csv', index=False, encoding='utf-8')
# print("Successfully analyzed every facebook page and sorted according to probability and saved in csv")

pages_to_test = [
    {
      "advertiser": "Dhaka Online Grocery Store",
      "advertiser_facebook_link": "https://www.facebook.com/dhakawholesalepricebd/",
      "advertiser_website_link": None,
      "library_id": "1869881600293572",
      "start_date": "2025-11-04",
      "active_time": "3 hrs",
      "content_preview": "🔥🔥 Offer Offer 🔥🔥  Buy one get one free  #follwers #everyonehighlightsfollowerseveryonehighlightsfollowerseveryone",
      "contact": None,
      "delivery_cost_inside": None,
      "delivery_cost_outside": None
    },
    {
      "advertiser": "The Reading Cafe",
      "advertiser_facebook_link": "https://www.facebook.com/readingcafe.bookstore/",
      "advertiser_website_link": None,
      "library_id": "1907843143416638",
      "start_date": "2025-11-04",
      "active_time": "7 hrs",
      "content_preview": "Remember: Your response MUST contain: 1. A brief analysis (max 5 lines) 2. JSON data ONLY inside a ```json code block",
      "contact": None,
      "delivery_cost_inside": None,
      "delivery_cost_outside": None
    },
    {
      "advertiser": "The Reading Cafe",
      "advertiser_facebook_link": "https://www.facebook.com/readingcafe.bookstore/",
      "advertiser_website_link": "http://www.thereadingcafebd.com/",
      "library_id": "1907843143416638",
      "start_date": "2025-11-04",
      "active_time": "7 hrs",
      "content_preview": "📚 𝗛𝗔𝗟𝗙 𝗣𝗥𝗜𝗖𝗘 𝗕𝗢𝗢𝗞 𝗦𝗔𝗟𝗘! 📚 𝑭𝑳𝑨𝑻 50% 𝑫𝑰𝑺𝑪𝑶𝑼𝑵𝑻 𝑶𝑵 𝑨𝑳𝑳 𝑶𝑹𝑰𝑮𝑰𝑵𝑨𝑳 & 𝑰𝑴𝑝𝑶𝑹𝑻𝑬𝑫 𝑩𝑶𝑶𝑲𝑺! 🎉 Dive into your next great read with our massive Half Price Sale — featuring 𝑭𝒊𝒄𝒕𝒊𝒐𝒏, 𝑵𝒐𝒏-𝑭𝒊𝒄𝒕𝒊𝒐𝒏, 𝑪𝒉𝒊𝒍𝒅𝒓𝒆𝒏’𝒔 𝑩𝒐𝒐𝒌𝒔...",
      "contact": "+880-1738-963-670",
      "delivery_cost_inside": "None",
      "delivery_cost_outside": "None"
    },
    {
      "advertiser": "The Reading Cafe",
      "advertiser_facebook_link": "https://www.facebook.com/readingcafe.bookstore/",
      "advertiser_website_link": "http://www.thereadingcafebd.com",
      "library_id": "1328297535102482",
      "start_date": "2025-11-04",
      "active_time": "7 hrs",
      "content_preview": "📚 𝗛𝗔𝗟𝗙 𝗣𝗥𝗜𝗖𝗘 𝗕𝗢𝗢𝗚𝗔 ✅ Dive into your next great read with our massive Half Price Sale — featuring 𝑭𝒊𝒄𝒕𝒊𝒐𝒏, 𝑵𝒐𝒏-𝑭𝒊𝒄𝒕𝒊𝒐𝒏, 𝑪𝒉𝒊𝒍𝒅𝒓𝒆𝒏’𝒔 𝑩𝒐𝒐𝒌𝒔, 𝑩𝒐𝒙 𝑺𝒆𝒕𝒔...",
      "contact": "+880-1738-963-670",
      "delivery_cost_inside": "2% charge for card/bKash payments",
      "delivery_cost_outside": "advance required"
    },
    {
      "advertiser": "And Or",
      "advertiser_facebook_link": "https://www.facebook.com/andor.readingcafe/",
      "advertiser_website_link": "http://www.thereadingcafebd.com/",
      "library_id": "24978811731813725",
      "start_date": "2025-11-04",
      "active_time": "7 hrs",
      "content_preview": "📚 𝗛𝗔𝗟𝗙 𝗣𝗥𝗜𝗖𝗘 𝗕𝗢𝗢𝗚 𝗦𝗔𝗟𝗘! 📚 𝑭𝑳𝑨𝑻 50% 𝑫𝑰𝑺𝑪𝑶𝑼𝑵𝑻 𝑶𝑵 𝑨𝑳𝑳 𝑶𝑹𝑰𝑮𝑰𝑵𝑨𝑳 & 𝑰𝑴𝑷𝑶𝑹𝑻𝑬𝑫 𝑩𝑶𝑶𝑲𝑺! 🎉 Dive into your next great read with our massive Half Price Sale — featuring... ",
      "contact": "+880-1738-963-670",
      "delivery_cost_inside": "Home Delivery Available All Over Bangladesh",
      "delivery_cost_outside": None
    },
    {
      "advertiser": "Time Machine BD",
      "advertiser_facebook_link": "https://www.facebook.com/timemachinetmbd/",
      "advertiser_website_link": None,
      "library_id": "2127259851350392",
      "start_date": "2025-11-04",
      "active_time": "9 hrs",
      "content_preview": "In-store: Up to 20% off exclusive deals. Online: Flat 10% off every order. Pre-order limited pieces before they’re gone...",
      "contact": None,
      "delivery_cost_inside": "COD Across Bangladesh",
      "delivery_cost_outside": None
    },
  
    {
      "advertiser": "Emptique",
      "advertiser_facebook_link": "https://www.facebook.com/emptique/",
      "advertiser_website_link": None,
      "library_id": "798603479612122",
      "start_date": "2025-11-02",
      "active_time": "Active",
      "content_preview": "𝐁𝐮𝐢𝐥𝐝 𝐭𝐫𝐮𝐬𝐭 𝐭𝐡𝐞 𝐬𝐢𝐦𝐩𝐥𝐞 𝐰𝐚𝐲 — 𝐥𝐞𝐭 𝐃𝐡𝐚𝐤𝐚’𝐬 𝐛𝐞𝐬𝐭 𝐫𝐞𝐬𝐭𝐚𝐮𝐫𝐚𝐧𝐭𝐬 𝐡𝐨𝐬𝐭 𝐲𝐨𝐮. Step inside Dhaka’s most elegant restaurants with 𝐄𝐦𝐩𝐭𝐢𝐪𝐮𝐞 — Bangladesh’s first platform...",
      "contact": "01814-231316",
      "delivery_cost_inside": None,
      "delivery_cost_outside": None
    },
    {
      "advertiser": "Tori : তরী",
      "advertiser_facebook_link": "https://www.facebook.com/toriclothing/",
      "advertiser_website_link": None,
      "library_id": "845133538461631",
      "start_date": "2025-11-02",
      "active_time": "Active",
      "content_preview": "🪡Premium Cotton 𝗞𝗔𝗘𝗜𝗔! 𝗘𝗜𝗗/𝟮𝟱\nSoft as a hug! Lightweight, breathable & all-day comfy. Crafted for comfort lovers! Grab yours & create magic! 𝗦𝘁𝗼𝗰𝗸 𝗹𝗶𝗺𝗶𝘁𝗲𝗱!",
      "contact": None,
      "delivery_cost_inside": None,
      "delivery_cost_outside": None
    },
    {
      "advertiser": "India Shopping BD",
      "advertiser_facebook_link": "https://www.facebook.com/IndiaShoppingBD/",
      "advertiser_website_link": None,
      "library_id": "1357083399453057",
      "start_date": "2025-10-31",
      "active_time": "Active",
      "content_preview": "Shop for you and your loved ones availing great deals. We are taking pre-orders from Malaysia and India. 🇧🇩🇲🇾🇮🇳 Delivery time is 10-20 days...",
      "contact": None,
      "delivery_cost_inside": None,
      "delivery_cost_outside": None
    },
    {
      "advertiser": "Printacy",
      "advertiser_facebook_link": "https://www.facebook.com/printacy/",
      "advertiser_website_link": None,
      "library_id": "790084117343465",
      "start_date": "2025-11-01",
      "active_time": "Active",
      "content_preview": "Premium Shopping Bags – যেখানে স্টাইল মিশে আছে ব্র্যান্ড আইডেন্টিটির সাথে! প্রতিটি ব্যাগ শুধু একটি প্যাকেজ নয় — এটা আপনার ব্র্যান্ডের চলমান বিজ্ঞাপন!",
      "contact": "01823549035",
      "delivery_cost_inside": None,
      "delivery_cost_outside": None
    }
  ]

results = []

print("[+] Starting batch Facebook lead analysis...\n")

for i, page in enumerate(pages_to_test, start=1):
    print(f"[{i}/{len(pages_to_test)}] Analyzing: {page['advertiser']} -> {page['advertiser_facebook_link']}")
    try:
        data = analyze_facebook_lead(page["advertiser_facebook_link"], page["advertiser"])
    except Exception as e:
        data = {"probability": 0, "service": None, "reasoning": f"Error: {str(e)}"}
    
    page_result = {
        "page_name": page["name"],
        "url": page["url"],
        **data
    }
    results.append(page_result)
    
    # Sleep a bit to avoid request limits or rate bans
    time.sleep(2)

# --- Save to JSON file ---
with open("output.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("\n✅ Analysis completed. Results saved to 'output.json'.")