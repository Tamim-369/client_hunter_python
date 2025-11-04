
from langchain_classic.text_splitter import RecursiveCharacterTextSplitter
from langchain_classic.schema import HumanMessage
from humanauto import chatDuckAIJson
import time
from typing import List, Dict
import json
import re
import os
from dotenv import load_dotenv

load_dotenv()

def extract_json_from_response(text: str) -> dict:
    """
    Extract JSON from LLM response that may contain additional text.
    Looks for JSON between { and } brackets.
    """
    # Try to find JSON in code blocks first
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except:
            pass
    
    # Try to find any JSON object in the text
    # Find the first { and last }
    first_brace = text.find('{')
    last_brace = text.rfind('}')
    
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        json_str = text[first_brace:last_brace + 1]
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            # Try to find nested JSON if the first attempt fails
            # Look for the pattern {"ads": [...]}
            pattern = r'\{\s*"ads"\s*:\s*\[.*?\]\s*\}'
            match = re.search(pattern, text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except:
                    pass
    
    # If all else fails, return empty ads structure
    return {"ads": []}

def load_existing_ads(output_file: str) -> List[Dict]:
    """Load existing ads from file if it exists."""
    if os.path.exists(output_file):
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("ads", [])
        except Exception as e:
            print(f"Warning: Could not load existing file: {e}")
            return []
    return []

def get_existing_library_ids(ads: List[Dict]) -> set:
    """Get set of existing library IDs to avoid duplicates."""
    return {ad.get("library_id") for ad in ads if ad.get("library_id")}

def save_ads_incremental(new_ads: List[Dict], output_file: str = "extracted_ads.json"):
    """
    Append new ads to existing file, avoiding duplicates.
    Returns number of new ads added.
    """
    # Load existing ads
    existing_ads = load_existing_ads(output_file)
    existing_ids = get_existing_library_ids(existing_ads)
    
    # Filter out duplicates from new ads
    truly_new_ads = []
    for ad in new_ads:
        lib_id = ad.get("library_id")
        if lib_id and lib_id not in existing_ids:
            truly_new_ads.append(ad)
            existing_ids.add(lib_id)  # Add to set to avoid duplicates within new_ads
        elif not lib_id:
            # If no library_id, check if content is unique
            # You might want to add more sophisticated duplicate detection here
            truly_new_ads.append(ad)
    
    if truly_new_ads:
        # Add new ads to existing ones
        existing_ads.extend(truly_new_ads)
        
        # Save back to file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "total_ads": len(existing_ads),
                "ads": existing_ads
            }, f, indent=2, ensure_ascii=False)
        
        print(f"  ✓ Added {len(truly_new_ads)} new ads to {output_file}")
        return len(truly_new_ads)
    else:
        print(f"  - No new ads to add (all were duplicates)")
        return 0


def process_large_ad_file(text: str, query: str = "minifan", output_file: str = "ads.json") -> int:
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(chunk_size=3000, chunk_overlap=500)
    chunks = splitter.split_text(text)

    all_ads = []
    for i, chunk in enumerate(chunks):
        print(f"\nChunk {i+1}/{len(chunks)}")

        prompt = f"""
You are a Facebook Ad extractor. Return ONLY JSON.

Schema:
{{
  "ads": [ {{ "advertiser": "", "advertiser_facebook_link": "", "library_id": "" }} ]
}}

Extract ads relevant to "{query}" from:
{chunk}
"""

        result = chatDuckAIJson(prompt)
        ads = result.get("ads", [])
        
        if ads:
            print(f"  Found {len(ads)} ads")
            all_ads.extend(ads)
        else:
            print("  No ads")

        time.sleep(3)  # Be gentle with Duck.ai

    # Save
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({"ads": all_ads}, f, indent=2, ensure_ascii=False)

    print(f"\nDONE: {len(all_ads)} ads → {output_file}")
    return len(all_ads)

def print_summary(output_file: str = "extracted_ads.json"):
    """Print summary of all ads in the file."""
    ads = load_existing_ads(output_file)
    
    if ads:
        print(f"\n{'='*60}")
        print(f"SUMMARY")
        print(f"{'='*60}")
        print(f"Total unique ads in database: {len(ads)}")
        
        # Count ads by advertiser
        advertisers = {}
        for ad in ads:
            advertiser = ad.get("advertiser", "Unknown")
            advertisers[advertiser] = advertisers.get(advertiser, 0) + 1
        
        print(f"\nAds by advertiser:")
        for advertiser, count in sorted(advertisers.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  - {advertiser}: {count} ads")
        
        print(f"\nSample ad:")
        print(json.dumps(ads[0], indent=2, ensure_ascii=False)[:500] + "...")
    else:
        print("\nNo ads found in database yet.")
def process_text_data(text_data: str, query: str, output_file: str = "extracted_ads.json") -> int:
        """
        Process text data containing Facebook ads and extract information.
        Args:
            text_data: String containing the ad data
            output_file: Path to save extracted ads
        Returns:
            Number of new ads added
        """
        print(f"Processing text data of {len(text_data)} characters...")
        print(f"Output file: {output_file}")
        
        # Check existing ads
        existing_count = len(load_existing_ads(output_file))
        print(f"Existing ads in database: {existing_count}")
        
        print(f"{'='*60}")
        
        # Process the text data
        new_ads_count = process_large_ad_file(text_data, output_file=output_file, query=query)
        
        print(f"{'='*60}")
        print(f"✓ Processing complete!")
        print(f"✓ New ads added: {new_ads_count}")
        
        # Print summary
        print_summary(output_file)
        
        return new_ads_count

