from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from .facebook import analyze_facebook_lead
from .data_ai import process_text_data
import urllib.parse
import html2text
import re
import pandas as pd
import json
import csv
import requests
from urllib.parse import urlparse
import ssl
import socket
from bs4 import BeautifulSoup


# ========================================
# 1. WEBSITE SECURITY & SPEED SCANNER
# ========================================
def analyze_website_issues(website_url: str) -> str:
    if not website_url or website_url.strip() in ["", "None", "null", "FB Only"]:
        return "FB-only store — perfect for AI Chatbot + Auto-Order System"

    if not website_url.startswith(("http://", "https://")):
        website_url = "https://" + website_url

    issues = []
    start_time = time.time()
    try:
        response = requests.get(website_url, timeout=12, allow_redirects=True, verify=False)
        load_time = time.time() - start_time
        final_url = response.url
        content = response.text
        soup = BeautifulSoup(content, 'html.parser')
    except Exception as e:
        return f"Site unreachable: {str(e)[:80]}"

    # Speed
    if load_time > 5:
        issues.append(f"Load time: {load_time:.1f}s (slow — lose 40% mobile users)")
    elif load_time > 3:
        issues.append(f"Load time: {load_time:.1f}s (fixable)")

    # HTTPS
    parsed = urlparse(final_url)
    if parsed.scheme != "https":
        issues.append("No HTTPS — Google flags as 'Not Secure'")
    else:
        try:
            hostname = parsed.hostname
            ctx = ssl.create_default_context()
            with socket.create_connection((hostname, 443), timeout=5) as sock:
                with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    expiry = ssl.cert_time_to_seconds(cert['notAfter'])
                    days_left = (expiry - time.time()) // 86400
                    if days_left < 30:
                        issues.append(f"SSL expires in {int(days_left)} days")
        except:
            issues.append("SSL certificate error")

    # Security Headers
    headers = response.headers
    security_headers = {
        'Content-Security-Policy': 'Missing CSP',
        'X-Frame-Options': 'Clickjacking risk',
        'X-Content-Type-Options': 'MIME sniffing risk',
        'Referrer-Policy': 'Leaking referrers'
    }
    missing = [msg for h, msg in security_headers.items() if h not in headers]
    if missing:
        issues.append(f"Missing headers: {', '.join(missing[:2])}")

    # Mobile
    if 'viewport' not in content.lower():
        issues.append("No mobile viewport — broken on phones")

    # E-com
    if 'shopify' in content.lower():
        issues.append("Shopify — can secure & optimize")
    if 'add to cart' in content.lower() and 'checkout' not in content.lower():
        issues.append("Cart exists but no secure checkout")

    return " | ".join(issues[:4]) if issues else "Site is fast, secure, mobile-ready."


# ========================================
# 2. CONVERSION METRICS ESTIMATOR
# ========================================
def estimate_conversion_metrics(ad: dict, website_issues: str = "") -> dict:
    text = (ad.get('ad_text', '') + ad.get('page_bio', '') + ad.get('advertiser', '')).lower()
    metrics = {
        "Est. Daily Orders": "Unknown",
        "Ad Spend Intensity": "Low",
        "Cart Abandon Risk": "Low",
        "Est. Monthly Revenue": "Unknown",
        "DM Open Rate Prediction": "Low"
    }

    # Est. Daily Orders
    order_signals = len(re.findall(r'\border\b|\bঅর্ডার\b|\bকিনুন\b|\bকিনে\b', text))
    delivery_signals = len(re.findall(r'\bডেলিভারি\b|\bক্যাশ অন ডেলিভারি\b', text))
    total_signals = order_signals + delivery_signals

    if total_signals >= 5:
        metrics["Est. Daily Orders"] = "20–50/day"
    elif total_signals >= 3:
        metrics["Est. Daily Orders"] = "10–20/day"
    elif total_signals >= 1:
        metrics["Est. Daily Orders"] = "5–10/day"

    # Ad Spend Intensity
    urgency = len(re.findall(r'\bলিমিটেড\b|\bশেষ\b|\bতাড়াতাড়ি\b|\bআজই\b', text))
    repeat_ads = ad.get('ad_run_count_last_7d', 1)
    if repeat_ads >= 3 or urgency >= 2:
        metrics["Ad Spend Intensity"] = "High"
    elif repeat_ads >= 2:
        metrics["Ad Spend Intensity"] = "Medium"

    # Cart Abandon Risk
    risk_score = 0
    if "no https" in website_issues.lower():
        risk_score += 40
    if "load time" in website_issues.lower():
        load = [float(s) for s in website_issues.split() if s.replace('.', '').isdigit()]
        if load and load[0] > 4:
            risk_score += 30
    if "no mobile" in website_issues.lower():
        risk_score += 20

    if risk_score >= 60:
        metrics["Cart Abandon Risk"] = "High (50%+ loss)"
    elif risk_score >= 30:
        metrics["Cart Abandon Risk"] = "Medium (30% loss)"

    # Monthly Revenue
    orders = metrics["Est. Daily Orders"]
    if "20–50" in orders:
        metrics["Est. Monthly Revenue"] = "৳600K – ৳1.5M"
    elif "10–20" in orders:
        metrics["Est. Monthly Revenue"] = "৳300K – ৳600K"
    elif "5–10" in orders:
        metrics["Est. Monthly Revenue"] = "৳150K – ৳300K"
    else:
        metrics["Est. Monthly Revenue"] = "< ৳150K"

    # DM Open Rate
    followers = ad.get('page_followers', 0)
    has_contact = bool(ad.get('contact'))
    has_website = bool(ad.get('advertiser_website_link'))

    open_prob = 0
    if followers < 20_000: open_prob += 30
    if has_contact: open_prob += 25
    if has_website: open_prob += 15
    if any(x in text for x in ["ইনবক্স", "মেসেজ", "কল"]): open_prob += 20

    if open_prob >= 70:
        metrics["DM Open Rate Prediction"] = "High (70%+)"
    elif open_prob >= 50:
        metrics["DM Open Rate Prediction"] = "Medium (50%)"
    else:
        metrics["DM Open Rate Prediction"] = "Low (<30%)"

    return metrics


# ========================================
# 3. PITCH DRAFT + WHATSAPP LINK (SMART DEFAULTS)
# ========================================
def generate_pitch_and_link(row: dict) -> tuple:
    name = row["Advertiser"]
    issues = row["issues"]
    orders = row["Est. Daily Orders"]
    revenue = row["Est. Monthly Revenue"]
    contact = str(row["Contact"] or "").strip()
    website = row.get("Website Link", "")

    # SMART DEFAULTS
    if orders == "Unknown":
        orders_text = "৫–১৫ অর্ডার/দিন"
        revenue_text = "১–৩ লাখ/মাস"
    else:
        orders_text = orders
        revenue_text = revenue.replace("< ৳150K", "১.৫ লাখের নিচে")

    # Clean phone
    phone = re.sub(r'\D', '', contact)
    if phone.startswith('880'): phone = phone[3:]
    if phone.startswith('0'): phone = '880' + phone[1:]
    if not phone.startswith('880') or len(phone) != 13:
        phone = ""

    pitch = f"সালামু আলাইকুম, {name}!\n\n"

    # Dynamic Issues
    if "load time" in issues.lower():
        load = [s for s in issues.split() if s.replace('.', '').isdigit()]
        if load:
            pitch += f"আপনার সাইট {load[0]}s লোড → মোবাইলে ৪০% কাস্টমার হারাচ্ছেন\n"
    if "no https" in issues.lower():
        pitch += "সাইট 'Not Secure' দেখাচ্ছে → কাস্টমার ভরসা হারাচ্ছে\n"
    if "missing headers" in issues.lower():
        pitch += "হ্যাকাররা আপনার সাইটে ঢুকতে পারে — সিকিউরিটি হোল আছে\n"
    if "FB-only" in issues or not website or website == "FB Only":
        pitch += "আপনি FB-এ বিক্রি করছেন — কিন্তু অর্ডার ম্যানুয়াল? AI দিয়ে অটো করুন!\n"

    pitch += f"\nআপনার দোকানে ~{orders_text} ({revenue_text}) — আমরা ৭ দিনে:\n"
    pitch += "লোড টাইম ২ সেকেন্ডে নামাব\n"
    pitch += "হ্যাক প্রুফ + SSL + সিকিউরিটি ফিক্স\n"
    pitch += "৩০% বেশি সেল\n\n"
    pitch += "প্রথম অডিট ফ্রি। ১৫ মিনিট কল? [Your Calendly]"

    wa_link = f"https://wa.me/{phone}?text={urllib.parse.quote(pitch)}" if phone else ""

    return pitch.strip(), wa_link


# ========================================
# 4. MAIN PROCESSOR — FULLY UPGRADED
# ========================================
def proccess_leads(ads_array: any):
    results = []
    print("Analyzing every Facebook page and sorting according to probability")

    for ad in ads_array:
        print(f"Analyzing: {ad.get('advertiser', 'Unknown')}")

        # --- SAFELY EXTRACT ---
        fb_link = str(ad.get('advertiser_facebook_link') or "").strip()
        website_raw = ad.get('advertiser_website_link')
        website = ""

        if website_raw and isinstance(website_raw, str):
            website = website_raw.strip()
            if website.lower() in ["none", "null", ""] or not website:
                website = ""
            elif not website.startswith(("http://", "https://")):
                website = "https://" + website

        # Extract pagename safely
        pagename = ""
        if fb_link and "facebook.com" in fb_link:
            try:
                pagename = fb_link.split("facebook.com/")[1].split("?")[0].split("#")[0].rstrip("/")
            except:
                pagename = ""

        isNumber = pagename.isdigit() if pagename else True

        # Analyze FB page
        if not fb_link or not pagename or isNumber:
            lead_result = {"probability": 0, "service": None, "reasoning": "No valid Facebook link"}
        else:
            lead_result = analyze_facebook_lead(fb_link, ad.get("advertiser", "unknown"))
            time.sleep(2)

        reasoning = (lead_result.get('reasoning', '') or "").replace('"', '').replace('}\n', '').replace('```', '\n').replace("json", "").replace("{", "").strip()

        # Website scan
        issues = ""
        service = lead_result.get('service', '') or ""
        if "security" in service.lower() or "maintaining" in service.lower() or "audit" in service.lower():
            if website:
                print(f"   → Scanning website: {website}")
                issues = analyze_website_issues(website)
                time.sleep(1)
            else:
                issues = "FB-only store — perfect for AI Chatbot + Auto-Order System"

        # Conversion metrics
        metrics = estimate_conversion_metrics(ad, issues)

        # Contact
        contact = str(ad.get('contact') or "").strip()

        # Build row
        temp_row = {
            "Advertiser": ad.get('advertiser', 'Unknown'),
            "Facebook Link": fb_link,
            "Website Link": website or "FB Only",
            "Contact": contact,
            "Library ID": ad.get('library_id', '') or "",
            "Buy Probability (%)": lead_result.get('probability', 0),
            "Recommended Service": service,
            "Reasoning": reasoning,
            "issues": issues or "FB-only store — AI automation ready",
            **metrics
        }

        pitch, wa_link = generate_pitch_and_link(temp_row)
        temp_row["Pitch Draft (Bangla)"] = pitch
        temp_row["WhatsApp DM Link"] = wa_link

        if pagename and not isNumber:
            results.append(temp_row)

    # Create DataFrame
    df = pd.DataFrame(results)
    if not df.empty:
        df = df.sort_values(by="Buy Probability (%)", ascending=False)

    # Save to CSV
    df.to_csv('analyzed_leads.csv', index=False, encoding='utf-8', quoting=csv.QUOTE_ALL, escapechar='\\')
    print(f"\nDone! {len(df)} leads saved to 'analyzed_leads.csv'")

    # AUTO-PRINT TOP 5 HIGH-DM LEADS
    high_dm = df[
        (df["Buy Probability (%)"] >= 65) &
        (df["DM Open Rate Prediction"].str.contains("High|Medium", na=False)) &
        (df["Contact"] != "")
    ].head(5)

    if not high_dm.empty:
        print("\nTOP 5 LEADS — OPEN IN BROWSER NOW:")
        for _, row in high_dm.iterrows():
            if row["WhatsApp DM Link"]:
                print(row["WhatsApp DM Link"])

    return df