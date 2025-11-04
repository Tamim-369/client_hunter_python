import re
import json
import pandas as pd 
import pyautogui
from humanauto  import execute_click_sequence, click_on_text, press, click, scroll, wait, write, run, say, wait_until_appears_image, click_on_image, get_copied_value, scroll_until_appears_image, copy_var_and_paste
garbege = """

United States

United States Minor Outlying Islands

Uruguay

US Virgin Islands

Uzbekistan

Vanuatu

Vatican City

Venezuela

Vietnam

Wallis and Futuna

Western Sahara

Yemen

Zambia

Zimbabwe

​

​

All ads

​

Select ad category

All ads

Issues, elections or politics

Search by keyword or advertiser

​

 __

​

[ Sign in](/)

Ad Library

[Ad Library report](/ads/library/report/?source=nav-panel)

[Ad Library API](/ads/library/api/?source=nav-panel)

[Branded content](/ads/library/branded_content/?source=fb-logo)

* * *

[System status](https://metastatus.com/ads-transparency)

Subscribe to email updates

[FAQ](/ads/library/?show_faq=true)

[About ads and data use](/ads/about/?entry_product=ad_library)

[Privacy](/privacy/center/?entry_point=privacy_basics_redirect)

[Terms](/policies/)

[Cookies](/policies/cookies/)

~87 results

These results include ads that match your **keyword search.**

Filters

**Active status** : Active ads

Remove

​

Launched in November 2025

* * *

​

Active

Library ID: 1907843143416638

Started running on 4 Nov 2025 · Total active time 2 hrs

Platforms

​

​

Open Drop-down

​

See ad details

* * *



[The Reading Cafe](https://www.facebook.com/readingcafe.bookstore/)

**Sponsored******

📚 𝗛𝗔𝗟𝗙 𝗣𝗥𝗜𝗖𝗘 𝗕𝗢𝗢𝗞 𝗦𝗔𝗟𝗘! 📚  
𝑭𝑳𝑨𝑻 50% 𝑫𝑰𝑺𝑪𝑶𝑼𝑵𝑻 𝑶𝑵 𝑨𝑳𝑳 𝑶𝑹𝑰𝑮𝑰𝑵𝑨𝑳 & 𝑰𝑴𝑷𝑶𝑹𝑻𝑬𝑫 𝑩𝑶𝑶𝑲𝑺! 🎉  
  
Dive into your next great read with our massive Half Price Sale — featuring
𝑭𝒊𝒄𝒕𝒊𝒐𝒏, 𝑵𝒐𝒏-𝑭𝒊𝒄𝒕𝒊𝒐𝒏, 𝑪𝒉𝒊𝒍𝒅𝒓𝒆𝒏’𝒔 𝑩𝒐𝒐𝒌𝒔, 𝑩𝒐𝒙 𝑺𝒆𝒕𝒔, 𝒓𝒆𝒇𝒆𝒓𝒆𝒏𝒄𝒆 𝒃𝒐𝒐𝒌𝒔 𝒂𝒏𝒅 𝑫𝒆𝒍𝒖𝒙𝒆
𝑬𝒅𝒊𝒕𝒊𝒐𝒏𝒔! ✨  
  
Whether you’re growing your personal library or gifting a fellow book lover,
now’s the perfect time to grab your favourites at unbeatable prices! 🛍️  
  
📍𝗩𝗶𝘀𝗶𝘁 𝗢𝘂𝗿 𝗢𝘂𝘁𝗹𝗲𝘁𝘀:  
  
📚 𝗦𝗰𝗶𝗲𝗻𝗰𝗲 𝗟𝗮𝗯 – 𝗗𝗵𝗮𝗻𝗺𝗼𝗻𝗱𝗶 𝗢𝘂𝘁𝗹𝗲𝘁  
2nd Floor, 32/1 Khan Plaza, Science Lab, Mirpur Road, Dhaka 1205  
📞 +880-1738-963-670  
🕙 Open: 10 AM – 8 PM  
  
📚 𝗠𝗶𝗿𝗽𝘂𝗿 𝗘𝗖𝗕 𝗢𝘂𝘁𝗹𝗲𝘁  
161/1-C Matikata, Dhaka Cantonment (Near ECB Chottor, Kalshi Main Road, BJ
Group)  
📞 +880-1738-963-670 / +880-1858-469-123 / +880-1933-620-392  
🕘 Open: 10 AM – 9 PM  
  
P.S. 🗓️ Offer valid till 30th November.  
💳 For card or bKash payments, a 2% chargcopied_texte will be added.  
  
🚚 Home Delivery Available All Over Bangladesh  
🌐 Order Online:
[www.thereadingcafebd.com](https://l.facebook.com/l.php?u=http%3A%2F%2Fwww.thereadingcafebd.com%2F&h=AT280lg6wuEpL4ps7JFy90vncsz5tLI3mAp_nlLULMdYHe2ZZzzzDpp3n8TqA6MN-
_u_jALaBVOGyvcPoZUoljMU1eiHM3O70SiljcEtoYwPHX24pwd5oLHwk33pagK1XSvSBd581VldiOwOKXCVFErx-n01pg)  
📩 Email: contact.readingcafe@gmail.com  
  
#BookSale #HalfPriceBooks #ReadingCafe #BookLovers #DhakaBookstore #Fiction
#NonFiction #ChildrensBooks #BoxSets #DeluxeEditions #Bookworm
#BangladeshReaders








































"""

prompt = f"""
You are a data extraction AI specialized in parsing Facebook Ad Library data. 
Your task: extract EVERY valid Facebook ad from the provided text chunk.

### Rules (strictly enforced):
1. Only include ads that:
   - Contain a valid advertiser Facebook page link.
3. Never add, infer, or guess missing data. If a field is missing, use null.
4. The response MUST be valid JSON (parseable, no trailing commas) but you can explain why you have done what you have done.

### Required output schema:
{{
    "ads": [
        {{
            "advertiser": "Advertiser name",
            "advertiser_facebook_link": "https://facebook.com/...",
            "advertiser_website_link": "https://... or null",
            "library_id": "Library ID",
            "start_date": "YYYY-MM-DD",
            "active_time": "duration text (e.g., 'Active since 10 days')",
            "content_preview": "first 200 characters of ad text",
            "contact": "email or phone or null",
            "delivery_cost_inside": "price info or null",
            "delivery_cost_outside": "price info or null"
        }}
    ]
}}

### Extraction Notes:
- “content_preview” = first 200 visible characters of the ad’s content.
- Trim all whitespace and line breaks from extracted values.

### Input Text:
{garbege}
"""
def chatDuckAIJson(prompt:str):
    press("Win","9")
    wait(0.5)

    run("google-chrome --incognito")
    wait(0.5)
    write("duck.ai")
    press("Enter")
    wait(1)
    wait_until_appears_image("./assets/ocr/duckai_loaded.png")
    wait(0.5)
    click_on_image("./assets/ocr/duckai_agree.png")
    wait(0.5)
    click_on_image("./assets/ocr/duckai_chat.png")
    wait(0.5)
    copy_var_and_paste(prompt)
    wait(1)
    press("Enter")
    wait(0.5)
    press("Enter")
    wait(0.5)
    wait_until_appears_image("./assets/ocr/duckai_chat2.png")
    wait(0.5)
    click_on_image("./assets/ocr/duckai_random.png")
    wait(0.5)
    pyautogui.moveTo(960,540)
    wait(0.5)
    scroll_until_appears_image("./assets/ocr/duckai_copy_code.png")
    wait(0.5)
    click_on_image("./assets/ocr/duckai_copy_code.png")
    wait(2)
    copied_text = get_copied_value()
    print(copied_text)
    press("Alt", "F4")
    data = json.loads(copied_text)
    return data

data = chatDuckAIJson(prompt)







