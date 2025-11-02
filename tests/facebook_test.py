from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time

def scrape_facebook_with_popup_close_and_scroll(url, scroll_duration=10):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    )
    # Optional: if using Chromium on Debian
    # chrome_options.binary_location = "/usr/bin/chromium"

    driver = webdriver.Chrome(options=chrome_options)
    try:
        print(f"[+] Loading page: {url}")
        driver.get(url)

        # Wait for body to appear
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # Try to find and click any close button (case-insensitive aria-label)
        try:
            close_button = driver.find_element(
                By.XPATH,
                '//div[@aria-label="Close" or @aria-label="close"] | '
                '//button[@aria-label="Close" or @aria-label="close"] | '
                '//*[@aria-label="Close" or @aria-label="close"]'
            )
            if close_button.is_displayed() and close_button.is_enabled():
                print("[+] Found and clicking 'Close' element...")
                close_button.click()
                time.sleep(1)  # brief pause after click
        except Exception as e:
            print("[-] No 'Close' popup found or failed to click:", str(e))

        # Scroll down for `scroll_duration` seconds
        print(f"[+] Scrolling for {scroll_duration} seconds to load content...")
        start_time = time.time()
        while time.time() - start_time < scroll_duration:
            driver.execute_script("window.scrollBy(0, 1000);")
            time.sleep(0.2)  # small delay between scrolls

        # Get body HTML after scrolling
        body_element = driver.find_element(By.TAG_NAME, "body")
        body_html = body_element.get_attribute("outerHTML")

        # Parse with BeautifulSoup and clean
        soup = BeautifulSoup(body_html, "html.parser")
        for tag in soup(["script", "style", "svg", "noscript", "header", "footer", "nav", "aside"]):
            tag.decompose()

        text = soup.get_text(separator=" ", strip=True)
        return text

    except Exception as e:
        print(f"[!] Error during scraping: {e}")
        return None
    finally:
        driver.quit()

# === Usage ===
if __name__ == "__main__":
    # Replace with a PUBLIC Facebook Page URL
    page_url = "https://www.facebook.com/Ghorerbazarbd.comm"

    extracted_text = scrape_facebook_with_popup_close_and_scroll(
        url=page_url,
        scroll_duration=10
    )

    if extracted_text:
        print("\n[+] Extracted Text (first 1500 characters):\n")
        print(extracted_text[:1500] + "..." if len(extracted_text) > 1500 else extracted_text)
    else:
        print("Failed to extract content.")