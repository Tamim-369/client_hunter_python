from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
from langchain_classic.prompts import ChatPromptTemplate
from langchain_classic.schema.output_parser import StrOutputParser
import re
from humanauto import chatDuckAIJson
import json
from ddgs import DDGS
from dotenv import load_dotenv
load_dotenv()

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

# get facebook page data
def getPageData(page_url:str):
    try:
        extracted_text = scrape_facebook_with_popup_close_and_scroll(
            url=page_url,
            scroll_duration=10
        )
        if extracted_text:
            print("\n[+] Extracted Text (first 1500 characters):\n")
            print(extracted_text[:1500] + "..." if len(extracted_text) > 1500 else extracted_text)
            return extracted_text
        else:
            print("Failed to extract content.")
            return ""
    except:
        return ""
    



def analyze_facebook_lead(url: str, advertiser_name: str = "") -> dict:
    text = getPageData(url)
    pagename = url.split("com/")[1].replace("/", "").strip()

    if not text or len(text.strip()) < 50 or pagename.isdigit():
        return {"probability": 0, "service": None, "reasoning": "Insufficient content"}

    text = text[:3000]

    # External research
    research_text = ""
    try:
        query = f"{advertiser_name or pagename} site:.com OR site:.bd OR site:.io OR facebook.com"
        with DDGS() as ddgs:
            results = [r.get("body", "") + " " + r.get("title", "") for r in ddgs.text(query, max_results=5)]
            research_text = "\n".join([r for r in results if len(r) > 50])
    except:
        research_text = ""

    combined_content = f"Facebook Page Content:\n{text}\n\nExternal Research Data:\n{research_text}"

    # Prompt template
    prompt = f"""You are an elite B2B sales analyst helping a small digital agency based in Bangladesh.  
The agency offers only these four services:  
1. AI automation / chatbot systems  
2. E-commerce website development and maintenance  
3. Security audits for websites and apps  
4. Securing and maintaining existing online stores  

Your job is to evaluate a business's Facebook page (and any available external data) and predict whether the owner is a high-potential lead—meaning they are likely to reply to a direct message or email and purchase a service soon.  

**Lead Quality Guidelines:**  
- ⬇️ **Reduce probability** if:  
  - The page belongs to a large corporation, celebrity, or verified account with 100K+ followers  
  - The page appears inactive, personal, or has <100 followers  
  - No contact info, website, or business details are visible  
- ⬆️ **Increase probability** if:  
  - It’s a local, active, professionally branded small or medium business  
  - Clear signs of digital presence (e.g., online store, contact form, recent posts)  

**Output Rules (STRICT):**  
- ALWAYS respond with a brief natural-language explanation **first**, then provide the JSON **strictly as a code block** using triple backticks (```json ... ```)  
- NEVER output JSON as plain text—it must be wrapped in a code block  
- The JSON must contain exactly these three keys: "Probability", "Service", and "Reasoning"  
- "Probability" must be an integer from 0 to 100  
- "Service" must be one of the four exact service names listed above  
- "Reasoning" must be 1–2 concise, realistic sentences  

Example of correct output:  
This business runs an active online clothing store with recent posts but lacks proper security headers. They’re likely to invest in maintenance and protection.  
```json
{
  "Probability": "78",
  "Service": "Securing and maintaining existing online stores",
  "Reasoning": "Active e-commerce store with visible contact info and recent updates, but shows signs of outdated security practices.",
}



```"""
    
    try:
        response = chatDuckAIJson(prompt)

        # Parse JSON robustly
        json_str = None
        try:
            json_str = re.search(r'\{.*\}', response, re.DOTALL).group(0)
            data = json.loads(json_str)
        except:
            match = re.search(
                r'"?Probability"?\s*[:=]\s*(\d+).*?"?Service"?\s*[:=]\s*["\']?([^"\n]+)["\']?.*?"?Reasoning"?\s*[:=]\s*["\']?(.+?)["\']?\s*$',
                response, re.DOTALL | re.IGNORECASE
            )
            if match:
                data = {
                    "Probability": int(match.group(1)),
                    "Service": match.group(2).strip(),
                    "Reasoning": match.group(3).strip()
                }
            else:
                data = {"Probability": 0, "Service": None, "Reasoning": "Parsing failed"}

        probability = int(data.get("Probability", data.get("probability", 0)))
        service = data.get("Service") or data.get("service")
        reasoning = data.get("Reasoning") or data.get("reasoning")
        
        return {
            "probability": min(100, max(0, probability)) or 0,
            "service": service or "",
            "reasoning": reasoning or ""
        }

    except Exception as e:
        return {"probability": 0, "service": None, "reasoning": f"Analysis failed: {str(e)}"}




