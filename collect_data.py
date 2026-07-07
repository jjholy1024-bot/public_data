import os
import sys
import time
import json
import requests
import xml.etree.ElementTree as ET
from dotenv import load_dotenv

# Reconfigure stdout to use UTF-8 to prevent Windows console encoding errors
sys.stdout.reconfigure(encoding='utf-8')

# Load environment variables
load_dotenv(dotenv_path="D:\\public_data_pro\\.env")
SERVICE_KEY = os.getenv("PUBLIC_DATA_SERVICE_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Constants
GEMINI_MODEL = 'gemini-flash-lite-latest'

# Static lookup table for coordinates
COORDINATES_LOOKUP = {
    ("United States", "New York"): (40.7128, -74.0060),
    ("United States", "Washington D.C."): (38.9072, -77.0369),
    ("United States", "Washington"): (38.9072, -77.0369),
    ("United States", "Boston"): (42.3601, -71.0589),
    ("United States", "Chicago"): (41.8781, -87.6298),
    ("United States", "San Francisco"): (37.7749, -122.4194),
    ("Switzerland", "Geneva"): (46.2044, 6.1432),
    ("Switzerland", "Bern"): (46.9480, 7.4474),
    ("Austria", "Vienna"): (48.2082, 16.3738),
    ("France", "Paris"): (48.8566, 2.3522),
    ("Italy", "Rome"): (41.9028, 12.4964),
    ("Italy", "Turin"): (45.0703, 7.6869),
    ("Thailand", "Bangkok"): (13.7563, 100.5018),
    ("Kenya", "Nairobi"): (-1.2921, 36.8219),
    ("United Kingdom", "London"): (51.5074, -0.1278),
    ("Germany", "Bonn"): (50.7374, 7.0982),
    ("Germany", "Berlin"): (52.5200, 13.4050),
    ("Germany", "Munich"): (48.1351, 11.5820),
    ("Germany", "Frankfurt"): (50.1109, 8.6821),
    ("Canada", "Montreal"): (45.5017, -73.5673),
    ("Canada", "Ottawa"): (45.4215, -75.6972),
    ("Canada", "Toronto"): (43.6532, -79.3832),
    ("Philippines", "Manila"): (14.5995, 120.9842),
    ("Jordan", "Amman"): (31.9454, 35.9284),
    ("India", "New Delhi"): (28.6139, 77.2090),
    ("India", "Delhi"): (28.6139, 77.2090),
    ("India", "Mumbai"): (19.0760, 72.8777),
    ("Egypt", "Cairo"): (30.0444, 31.2357),
    ("China", "Beijing"): (39.9042, 116.4074),
    ("China", "Shanghai"): (31.2304, 121.4737),
    ("Japan", "Tokyo"): (35.6762, 139.6503),
    ("Belgium", "Brussels"): (50.8503, 4.3517),
    ("Netherlands", "The Hague"): (52.0705, 4.3007),
    ("Netherlands", "Amsterdam"): (52.3676, 4.9041),
    ("Denmark", "Copenhagen"): (55.6761, 12.5683),
    ("South Korea", "Seoul"): (37.5665, 126.9780),
    ("South Korea", "Incheon"): (37.4563, 126.7052),
    ("South Korea", "Busan"): (35.1796, 129.0756),
    ("South Korea", "Daejeon"): (36.3504, 127.3845),
    ("Indonesia", "Jakarta"): (-6.2088, 106.8456),
    ("Vietnam", "Hanoi"): (21.0285, 105.8542),
    ("Malaysia", "Kuala Lumpur"): (3.1390, 101.6869),
    ("Singapore", "Singapore"): (1.3521, 103.8198),
    ("Australia", "Canberra"): (-35.2809, 149.1300),
    ("Australia", "Sydney"): (-33.8688, 151.2093),
    ("New Zealand", "Wellington"): (-41.2865, 174.7762),
    ("Spain", "Madrid"): (40.4168, -3.7038),
    ("Spain", "Barcelona"): (41.3851, 2.1734),
    ("Sweden", "Stockholm"): (59.3293, 18.0686),
    ("Norway", "Oslo"): (59.9139, 10.7522),
    ("Finland", "Helsinki"): (60.1699, 24.9384),
    ("Senegal", "Dakar"): (14.7167, -17.4677),
    ("Ethiopia", "Addis Ababa"): (9.0300, 38.7400),
    ("Panama", "Panama City"): (8.9824, -79.5199),
    ("Chile", "Santiago"): (-33.4489, -70.6693),
    ("Peru", "Lima"): (-12.0464, -77.0428),
    ("Brazil", "Brasilia"): (-15.7975, -47.8919),
    ("Brazil", "Rio de Janeiro"): (-22.9068, -43.1729),
    ("South Africa", "Pretoria"): (-25.7479, 28.2293),
    ("South Africa", "Cape Town"): (-33.9249, 18.4241),
}

def get_coordinates(country, city, gemini_lat=0.0, gemini_lng=0.0):
    c_norm = country.strip().title()
    ct_norm = city.strip().title()

    # Exact match
    if (c_norm, ct_norm) in COORDINATES_LOOKUP:
        return COORDINATES_LOOKUP[(c_norm, ct_norm)]

    # Normalized country variations
    c_var = c_norm
    if c_var in ["United States Of America", "Usa", "U.S.A.", "U.S."]:
        c_var = "United States"
    elif c_var in ["Korea", "Korea, South", "Republic Of Korea", "South Korea", "대한민국", "한국"]:
        c_var = "South Korea"
    elif c_var in ["United Kingdom", "Uk", "U.K."]:
        c_var = "United Kingdom"

    if (c_var, ct_norm) in COORDINATES_LOOKUP:
        return COORDINATES_LOOKUP[(c_var, ct_norm)]

    # Fallback to matching country only
    for (lookup_c, lookup_ct), coords in COORDINATES_LOOKUP.items():
        if lookup_c == c_var:
            return coords

    # Fallback to Gemini's output
    try:
        return float(gemini_lat), float(gemini_lng)
    except:
        return 0.0, 0.0

def load_cache(filepath):
    cache = {}
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    cache[item["seq"]] = item
            print(f"Loaded {len(cache)} items from cache: {filepath}")
        except Exception as e:
            print(f"Error loading cache from {filepath}: {e}")
    return cache

def call_gemini_api(raw_title, raw_reg_date, raw_location, raw_organization, raw_content):
    if not GOOGLE_API_KEY:
        print("GOOGLE_API_KEY environment variable is not set. Cannot call Gemini API.")
        return None

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GOOGLE_API_KEY}"
    prompt = f"""You are an expert recruitment assistant specializing in international organizations.
Analyze the following job vacancy post and extract structured data.

[Job Title]
{raw_title}

[Registration Date]
{raw_reg_date}

[Country/City]
{raw_location}

[Organization]
{raw_organization}

[HTML Content]
{raw_content}

Your task is to return a JSON object with the following fields:
1. "cleaned_title": A clean, concise, professional job title in English. Do not include prefixes like [Domestic] or [Career] - those will be added programmatically.
2. "country": Normalized English name of the country where the job is located. If it is in South Korea, write "South Korea". If it is hybrid or remote, identify the head office country.
3. "city": Normalized English name of the city where the job is located (e.g. "New York", "Geneva", "Seoul").
4. "workType": The work type of the job. Must be one of: "On-site", "Hybrid", or "Remote". Infer this from the content.
5. "ai_keywords": A list of 4 to 6 relevant skill keywords or qualifications in English (e.g., ["Political Affairs", "Report Writing", "Fluent English"]).
6. "ai_summary": A concise 2-3 sentence Korean summary of the job description, key responsibilities, and qualifications. Clean all HTML tags.
7. "applyUrl": Extract the direct application URL or application email. Look for application instructions or links (e.g., Apply button link, UN careers link, recruitment portal link, or email address like recruit@...) inside the content or provided URLs. If it is an email, return it as "mailto:email@address.com". If no link is found, return "".
8. "lat": Latitude of the city/country (approximate).
9. "lng": Longitude of the city/country (approximate).

Return ONLY a valid JSON object matching this structure. Do not wrap in markdown code blocks or add any comments."""

    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }],
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }
    headers = {"Content-Type": "application/json"}

    # Retry logic
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            if response.status_code == 200:
                res_json = response.json()
                text_out = res_json.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()
                return json.loads(text_out)
            elif response.status_code in [429, 500, 502, 503, 504]:
                # Transient error or quota hit, backoff and retry
                wait_sec = (attempt + 1) * 15
                print(f"Transient error or rate limit hit ({response.status_code}): {response.text}. Waiting {wait_sec} seconds before retry...")
                time.sleep(wait_sec)
            else:
                print(f"Gemini API returned status code {response.status_code}: {response.text}")
                break
        except Exception as e:
            print(f"Exception during Gemini API call (attempt {attempt+1}): {e}")
            time.sleep(5)
    return None

def process_vacancies():
    # Paths for output JSON feeds
    os.makedirs("public/data", exist_ok=True)
    general_path = "public/data/general_jobs.json"
    internship_path = "public/data/internship_jobs.json"

    # Load cache
    general_cache = load_cache(general_path)
    internship_cache = load_cache(internship_path)

    # 1. Fetch General Vacancies
    print("Fetching Recent Vacancies...")
    general_url = 'http://apis.data.go.kr/1262000/IntrlInsttVacancyInfoService/getRecentVacancyInfoList'
    # Fetch top 100 rows to cover all active general vacancies (usually around 30)
    general_params = {'serviceKey': SERVICE_KEY, 'numOfRows': '100', 'pageNo': '1'}
    
    try:
        res = requests.get(general_url, params=general_params)
        root = ET.fromstring(res.content)
        general_items = root.findall('.//item')
        print(f"Retrieved {len(general_items)} general vacancy items from API.")
    except Exception as e:
        print(f"Error fetching General Vacancies: {e}")
        general_items = []

    # 2. Fetch Internship Vacancies
    print("Fetching Internship Vacancies...")
    internship_url = 'http://apis.data.go.kr/1262000/IntrlInsttVacancyInfoService/getInternshipVacancyInfoList'
    # Fetch top 50 items (sorted by regDt descending, so they are the most recent ones)
    internship_params = {'serviceKey': SERVICE_KEY, 'numOfRows': '50', 'pageNo': '1', 'title': '인턴십'}
    
    try:
        res = requests.get(internship_url, params=internship_params)
        root = ET.fromstring(res.content)
        internship_items = root.findall('.//item')
        print(f"Retrieved {len(internship_items)} internship vacancy items from API.")
    except Exception as e:
        print(f"Error fetching Internship Vacancies: {e}")
        internship_items = []

    # Process General Vacancies
    processed_general = []
    for idx, item in enumerate(general_items):
        seq = item.find('seq').text if item.find('seq') is not None else f"gen_{idx}"
        
        # Check cache
        if seq in general_cache:
            print(f"[{idx+1}/{len(general_items)}] General Vacancy {seq} found in cache. Reusing.")
            processed_general.append(general_cache[seq])
            continue
            
        print(f"[{idx+1}/{len(general_items)}] Processing General Vacancy {seq} with Gemini...")
        raw_title = item.find('positionName').text if item.find('positionName') is not None else ''
        raw_reg_date = item.find('regDate').text if item.find('regDate') is not None else ''
        raw_country = item.find('country').text if item.find('country') is not None else ''
        raw_city = item.find('city').text if item.find('city') is not None else ''
        raw_location = f"{raw_country}, {raw_city}"
        raw_org = item.find('international').text if item.find('international') is not None else ''
        raw_content = item.find('content').text if item.find('content') is not None else ''
        
        # Call Gemini
        # Slice content to 4000 chars for token efficiency
        result = call_gemini_api(raw_title, raw_reg_date, raw_location, raw_org, raw_content[:4000])
        
        if result:
            # Map coordinates
            lat, lng = get_coordinates(result.get("country", raw_country), result.get("city", raw_city), result.get("lat", 0.0), result.get("lng", 0.0))
            
            # Format prefix
            is_domestic = (result.get("country", "").lower().strip() in ["south korea", "korea", "대한민국", "한국"])
            loc_pref = "Domestic" if is_domestic else "Overseas"
            final_title = f"[{loc_pref}][Career] {result.get('cleaned_title', raw_title)}"
            
            # Application URL fallback
            apply_url = result.get("applyUrl", "")
            if not apply_url:
                apply_url = f"https://unrecruit.mofa.go.kr/vacancy/latest_vacancy_view.jsp?seq={seq}"
                
            job_data = {
                "seq": seq,
                "title": final_title,
                "country": result.get("country", raw_country),
                "city": result.get("city", raw_city),
                "lat": lat,
                "lng": lng,
                "regDt": raw_reg_date,
                "applyUrl": apply_url,
                "workType": result.get("workType", "On-site"),
                "ai_keywords": result.get("ai_keywords", []),
                "ai_summary": result.get("ai_summary", "")
            }
            processed_general.append(job_data)
            
            # Sleep to prevent rate limit
            time.sleep(4)
        else:
            print(f"Skipping General Vacancy {seq} due to Gemini API failure.")

    # Process Internship Vacancies
    processed_internship = []
    for idx, item in enumerate(internship_items):
        seq = item.find('seq').text if item.find('seq') is not None else f"intern_{idx}"
        
        # Check cache
        if seq in internship_cache:
            print(f"[{idx+1}/{len(internship_items)}] Internship Vacancy {seq} found in cache. Reusing.")
            processed_internship.append(internship_cache[seq])
            continue
            
        print(f"[{idx+1}/{len(internship_items)}] Processing Internship Vacancy {seq} with Gemini...")
        raw_title = item.find('title').text if item.find('title') is not None else ''
        raw_reg_date = item.find('regDt').text if item.find('regDt') is not None else ''
        raw_content = item.find('content').text if item.find('content') is not None else ''
        
        # LinkUrl4 and LinkTitle4 might contain application email or site
        link_url = item.find('linkUrl4').text if item.find('linkUrl4') is not None else ''
        link_title = item.find('linkTitle4').text if item.find('linkTitle4') is not None else ''
        
        extra_info = f"Provided Link: {link_title} - {link_url}"
        
        # Call Gemini
        result = call_gemini_api(raw_title, raw_reg_date, extra_info, "", raw_content[:4000])
        
        if result:
            # Map coordinates
            lat, lng = get_coordinates(result.get("country", ""), result.get("city", ""), result.get("lat", 0.0), result.get("lng", 0.0))
            
            # Format prefix
            is_domestic = (result.get("country", "").lower().strip() in ["south korea", "korea", "대한민국", "한국"])
            loc_pref = "Domestic" if is_domestic else "Overseas"
            final_title = f"[{loc_pref}][Internship] {result.get('cleaned_title', raw_title)}"
            
            # Application URL fallback
            apply_url = result.get("applyUrl", "")
            if not apply_url:
                if link_url and ("http" in link_url or "mailto" in link_url):
                    apply_url = link_url
                elif link_url and "@" in link_url:
                    apply_url = f"mailto:{link_url}"
                else:
                    apply_url = f"https://unrecruit.mofa.go.kr/new/community/notice_view.jsp?seq={seq}"
                    
            job_data = {
                "seq": seq,
                "title": final_title,
                "country": result.get("country", "South Korea"),
                "city": result.get("city", "Seoul"),
                "lat": lat,
                "lng": lng,
                "regDt": raw_reg_date,
                "applyUrl": apply_url,
                "workType": result.get("workType", "On-site"),
                "ai_keywords": result.get("ai_keywords", []),
                "ai_summary": result.get("ai_summary", "")
            }
            processed_internship.append(job_data)
            
            # Sleep to prevent rate limit
            time.sleep(4)
        else:
            print(f"Skipping Internship Vacancy {seq} due to Gemini API failure.")

    # Save to file
    try:
        with open(general_path, "w", encoding="utf-8") as f:
            json.dump(processed_general, f, ensure_ascii=False, indent=2)
        print(f"Successfully saved {len(processed_general)} general jobs to {general_path}")
    except Exception as e:
        print(f"Error saving general jobs to JSON: {e}")

    try:
        with open(internship_path, "w", encoding="utf-8") as f:
            json.dump(processed_internship, f, ensure_ascii=False, indent=2)
        print(f"Successfully saved {len(processed_internship)} internship jobs to {internship_path}")
    except Exception as e:
        print(f"Error saving internship jobs to JSON: {e}")

if __name__ == "__main__":
    process_vacancies()
