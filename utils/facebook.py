from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
from langchain_classic.prompts import ChatPromptTemplate
from langchain_classic.schema.output_parser import StrOutputParser
from langchain_groq import ChatGroq 
import re
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
    """
    Deeply analyzes a Facebook lead using both on-page content and external research
    to predict:
      - Probability (0–100) of buying your service
      - Most likely service
      - Short reasoning
    """

    # --- Step 1: Get base Facebook content
    text = getPageData(url)
    pagename = url.split("com/")[1].replace("/", "").strip()

    if not text or len(text.strip()) < 50 or pagename.isdigit():
        return {
            "probability": 0,
            "service": None,
            "reasoning": "Insufficient or empty page content."
        }

    text = text[:3000]  # allow slightly more content for context

    # --- Step 2: External research with DuckDuckGo
    research_text = ""
    try:
        query = f"{advertiser_name or pagename} site:.com OR site:.bd OR site:.io OR facebook.com"
        with DDGS() as ddgs:
            results = [r.get("body", "") + " " + r.get("title", "") for r in ddgs.text(query, max_results=5)]
            research_text = "\n".join([r for r in results if len(r) > 50])
    except Exception:
        research_text = ""

    if len(research_text) < 50:
        research_text = "No strong external data found; analyze only Facebook content."

    combined_content = f"Facebook Page Content:\n{text}\n\nExternal Research Data:\n{research_text}"

    # --- Step 3: Smart prompt
    prompt_template = ChatPromptTemplate.from_messages([
    ("system", """You are an elite B2B sales analyst helping a small digital agency.
The agency sells:
1. AI automation / chatbot systems
2. E-commerce website development and maintenance
3. Security audits for websites and apps
4. Securing and maintaining existing online stores

The agency owner only wants leads who will likely REPLY to his DM/email — not massive corporations or inactive shops.
If the page seems too large (corporate, celebrity, verified, 100K+ followers), reduce probability.
If it seems too small (no contact info, personal account, <100 followers), reduce probability.
If it's a local business, active, and professionally branded, increase probability.

Your task:
Analyze both the Facebook page and any external data to predict:
- Probability (0–100) of this lead replying and buying one of the services soon
- The exact service that fits best
- A short, realistic reasoning (1-2 sentences max)

Return STRICT JSON:
{{
  "Probability": <number between 0-100>,
  "Service": "<exact service name>",
  "Reasoning": "<1-2 sentences>"
}}
"""),
    ("human", "{content}")
])

    # --- Step 4: Run the model
    llm = ChatGroq(
        model="openai/gpt-oss-120b",
        temperature=0.1,
    )

    chain = prompt_template | llm | StrOutputParser()

    try:
        response = chain.invoke({"content": combined_content})

        # --- Step 5: Parse JSON robustly
        json_str = None
        try:
            json_str = re.search(r'\{.*\}', response, re.DOTALL).group(0)
            data = json.loads(json_str)
        except Exception:
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
                data = {"Probability": 0, "Service": None, "Reasoning": "Parsing failed."}

        probability = int(data.get("Probability", data.get("probability", 0)))
        service = data.get("Service") or data.get("service")
        reasoning = data.get("Reasoning") or data.get("reasoning")

        return {
            "probability": min(100, max(0, probability)),
            "service": service,
            "reasoning": reasoning
        }

    except Exception as e:
        return {
            "probability": 0,
            "service": None,
            "reasoning": f"Analysis failed: {str(e)}"
        }
