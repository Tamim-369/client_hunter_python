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
    


def analyze_facebook_lead(url: str) -> dict:
    """
    Efficiently analyzes a Facebook page's content to predict:
      - Probability (0–100) of buying your service
      - Most likely service
      - Short reasoning
    """

    # --- Step 1: Get text content efficiently
    text = getPageData(url)
    if not text or len(text.strip()) < 50:
        return {
            "probability": 0,
            "service": None,
            "reasoning": "Insufficient or empty page content."
        }

    # Limit input size to reduce token cost and latency
    text = text[:2000]

    # --- Step 2: Create the prompt once (cached globally if reused)
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", """You are a B2B sales analyst. The user offers:
1. AI automation / automated bots
2. E-commerce website development + maintenance
3. Security audits for websites/apps
4. Securing + maintaining existing e-commerce sites

Analyze the Facebook page content and respond in **strict JSON**:
{
  "Probability": <0-100>,
  "Service": "<exact service name>",
  "Reasoning": "<1-2 sentences>"
}

Be realistic — personal or inactive pages = low probability."""),
        ("human", "{content}")
    ])

    # --- Step 3: Use the model
    llm = ChatGroq(
        model="meta-llama/llama-4-maverick-17b-128e-instruct",
        temperature=0.1,
    )

    chain = prompt_template | llm | StrOutputParser()

    # --- Step 4: Execute
    try:
        response = chain.invoke({"content": text})

        # --- Step 5: Parse JSON-like output robustly
        match = re.search(
            r'"?Probability"?\s*[:=]\s*(\d+).*?"?Service"?\s*[:=]\s*["\']?([^"\n]+)["\']?.*?"?Reasoning"?\s*[:=]\s*["\']?(.+?)["\']?\s*$', 
            response, 
            re.DOTALL | re.IGNORECASE
        )

        if match:
            probability = int(match.group(1))
            service = match.group(2).strip()
            reasoning = match.group(3).strip()
        else:
            # fallback in case parsing fails
            probability, service, reasoning = 0, None, "Parsing failed."

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



