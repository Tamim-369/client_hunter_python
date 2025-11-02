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
    Analyzes scraped Facebook page text to predict:
    - Probability (0-100) of buying your service
    - Most likely service
    - Short reasoning
    """
    text = getPageData(url)
    if not text or len(text.strip()) < 50:
        return {"probability": 0, "service": None, "reasoning": "Insufficient or empty page content."}

    llm = ChatGroq(
        model="meta-llama/llama-4-maverick-17b-128e-instruct",
        temperature=0.1,
    )

    prompt_template = ChatPromptTemplate.from_messages([
        ("system", """
You are an expert B2B sales analyst specializing in web services for small businesses.
The user offers these services:
1. AI automation / automated bots (e.g., customer support bots, scraping bots)
2. Full e-commerce website development with ongoing maintenance
3. Security audits for websites/apps
4. Securing and maintaining existing e-commerce websites

Analyze the following Facebook page content. Then output EXACTLY in this JSON-like format:
Probability: [0-100]
Service: [one of the 4 service names above]
Reasoning: [1-2 sentence explanation]

Be realistic. If the page is personal, inactive, or unrelated to business/e-commerce/tech, assign low probability.
"""),
        ("human", f"Facebook page content:\n\n{text[:2000]}")  
    ])

    chain = prompt_template | llm | StrOutputParser()

    try:
        response = chain.invoke({})
        
        # Parse output
        prob_match = re.search(r"Probability:\s*(\d+)", response)
        service_match = re.search(r"Service:\s*([^\\n]+)", response)
        reason_match = re.search(r"Reasoning:\s*(.+)", response, re.DOTALL)

        probability = int(prob_match.group(1)) if prob_match else 0
        service = service_match.group(1).strip() if service_match else None
        reasoning = reason_match.group(1).strip() if reason_match else "Parsing failed."

        # Validate service name
        valid_services = {
            "AI automation / automated bots",
            "Full e-commerce website development with ongoing maintenance",
            "Security audits for websites/apps",
            "Securing and maintaining existing e-commerce websites"
        }
        if service not in valid_services:
            service = "Unknown"

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
    



