from langchain_ollama import ChatOllama
from langchain_classic.text_splitter import RecursiveCharacterTextSplitter
from langchain_classic.schema import HumanMessage
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

def process_large_ad_file(text: str, chunk_size: int = 3000, output_file: str = "extracted_ads.json", query: str = "minifan") -> int:
    """
    Process large Facebook Ad Library file containing multiple ads.
    Saves new ads incrementally to avoid data loss.
    Returns total number of new ads found.
    """
    # Split text into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=500,  # Higher overlap to avoid splitting ads
        length_function=len,
        separators=["\n\n* * *\n\n", "Library ID:", "\n\n\n", "\n\n", "\n", " "]
    )
    
    chunks = text_splitter.split_text(text)
    
    llm = ChatOllama(
        model="phi4-mini-reasoning",
        temperature=0.1,
    )
    
    total_new_ads = 0
    not_found_count = 0
    for i, chunk in enumerate(chunks):
        print(f"Processing chunk {i+1}/{len(chunks)}...")
        
        prompt = f"""
You are a data extraction AI specialized in parsing Facebook Ad Library data. 
Your task: extract EVERY valid Facebook ad from the provided text chunk.

### Rules (strictly enforced):
1. Only include ads that:
   - Contain a valid advertiser Facebook page link.
   - Are relevant to this query: "{query}".
2. If no valid, complete ads exist, return exactly: {{"ads": []}} — no text or commentary.
3. Never add, infer, or guess missing data. If a field is missing, use null.
4. The response MUST be valid JSON (parseable, no trailing commas).

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
{chunk}
"""

        try:
            response = llm.invoke([HumanMessage(content=prompt)])
            
            # Extract JSON from response (handles extra text)
            result = extract_json_from_response(response.content)
            
            if "ads" in result and result["ads"]:
                print(f"  ✓ Found {len(result['ads'])} ads in this chunk")
                
                # Save incrementally
                new_count = save_ads_incremental(result["ads"], output_file)
                total_new_ads += new_count
            else:
                print(f"  - No ads found in this chunk")
                # not_found_count+=1
                # if not_found_count > 20:
                #     return total_new_ads

            
        except Exception as e:
            print(f"  ✗ Error processing chunk {i+1}: {e}")
            continue
    
    return total_new_ads

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
        new_ads_count = process_large_ad_file(text_data, chunk_size=3000, output_file=output_file, query=query)
        
        print(f"{'='*60}")
        print(f"✓ Processing complete!")
        print(f"✓ New ads added: {new_ads_count}")
        
        # Print summary
        print_summary(output_file)
        
        return new_ads_count

