from dotenv import load_dotenv
from langchain_core.tools import tool
from serpapi import GoogleSearch
from datetime import datetime
from haversine import haversine, Unit
import requests
import os, re, time, random, json

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
SERP_KEY = os.getenv("SERPAPI_API_KEY")

@tool
def search_attractions(dest: str) -> dict:
    """
    Search popular attractions in a given destination city.

    Args:
        dest (str): Destination name or city, e.g. "Seattle", "Denver, CO".

    Returns: 
        dict: JSON format day-by-day itinerary

    """
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    categories = [
        "tourist attractions",
        "point of interest",
        "museums",
        "viewpoints",
        "historical sites",
        "landmarks",
        "establishments"
    ]

    excluded_categories = {
        "restaurant", "lodging"
    }
    results = []
    for c in categories:
        params = {"query": f"{c} in {dest}", "key": GOOGLE_API_KEY}
        data = requests.get(url, params=params).json()
        results.extend(data.get("results", []))

    # Get more attractions. Default amount of attractions in Google Places API is 20
    token = data.get("next_page_token")
    while token:
        time.sleep(2) 
        params = {"pagetoken": token, "key": GOOGLE_API_KEY}
        r = requests.get(url, params=params)
        next_data = r.json()
        results.extend(next_data.get("results", []))
        token = next_data.get("next_page_token")
    
    # Remove Duplicates
    seen, unique = set(), []
    for r in results:
        name = r.get("name")
        if name and name not in seen:
            seen.add(name)
            unique.append(r)

    random.shuffle(unique)

    attractions = []
    for a in unique:
        types = set(a.get("types", []))

        reviews = a.get("user_ratings_total", 0)
        if types & excluded_categories or reviews < 900:        # Filter out attractions that have reviews < 900
            continue

        attractions.append({
            "name": a.get("name"),
            "rating": a.get("rating"),
            "types": a.get("types",[]),
            "lat": a.get("geometry", {}).get("location", {}).get("lat"),
            "lng": a.get("geometry", {}).get("location", {}).get("lng"),            
            })
        
    return {"attractions": attractions}

# Can ignore this, just for testing
@tool
def cluster_attractions(attractions_json: str, threshold_km: float = 15.0, max_per_day: int = 4) -> dict:
    """
    Cluster attractions by proximity into day-sized groups.
    Input:
    - attractions_json: attractions in JSON format.

    Output:
    - JSON-serializable dict
    """
    try:
        data = json.loads(attractions_json) if isinstance(attractions_json, str) else attractions_json
    except Exception as e:
        raise ValueError(f"cluster_attractions: invalid JSON: {e}")

    attractions = data.get("attractions", [])
    n = len(attractions)
    used = [False] * n
    clusters = []
    day_idx = 1

    for i in range(n):
        if used[i]:
            continue
        ai = attractions[i]
        lat_i, lng_i = ai.get("lat"), ai.get("lng")
        if lat_i is None or lng_i is None:
            used[i] = True
            continue

        cluster = [ai]
        used[i] = True

        # greedy expand cluster
        for j in range(i + 1, n):
            if used[j] or len(cluster) >= max_per_day:
                continue
            aj = attractions[j]
            lat_j, lng_j = aj.get("lat"), aj.get("lng")
            if lat_j is None or lng_j is None:
                continue

            d = compute_distance_km.run(lat_i, lng_i, lat_j, lng_j)
            if d <= threshold_km:
                cluster.append(aj)
                used[j] = True

        clusters.append({
            "day_index": day_idx,
            "attractions": cluster,
        })
        day_idx += 1

    return {"clusters": clusters}



def parse_price(raw: str) -> float:
    """
    Convert string type price to float type

    Args:
        raw (str): Price in str type
    
    Returns:
        float: Price in float type
    """

    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    if isinstance(raw, str):
        m = re.findall(r"[\d\.]+", raw)
        if not m:
            return None
        return float(m[0])
    return None



def search_oneWay_flights(origin: str, dest: str, depart_date: str, num_people: int, budget):
    """
    Search one-way flights based on user's information

    Args:
        origin (str): Departure airport IATA code (e.g. "SEA", "JFK").
        dest (str): Arrival airport IATA code.
        depart_date (str): Departure date in "YYYY-MM-DD".
        num_people (int): Number of travelers
        budget: user's total budget
    
    Returns:
        dict: one way flights info in JSON

    """
    # Formulate departure and return date 
    depart_date = datetime.strptime(depart_date, "%Y-%m-%d").date()

    params = {
        "engine": "google_flights",
        "type": 2,
        "departure_id": origin,
        "arrival_id": dest,
        "outbound_date": depart_date,
        "adults": num_people,
        "api_key": SERP_KEY,
    }
    search = GoogleSearch(params)
    results = search.get_dict()

    flight_raw = (results.get("best_flights") or []) + (results.get("other_flights") or [])
    normalized = []

    for f in flight_raw:
        price_raw = f.get("price")
        price = parse_price(price_raw)
        # 如果价格缺失或无法解析，跳过该航班，避免类型错误
        if price is None:
            continue
        # if budget is not None and price > budget:
        #     continue
        total_price = price * num_people

        segments = f.get("flights", []) or []
        if not segments:
            continue

        dep_airport = segments[0].get("departure_airport") or {}
        arr_airport = segments[-1].get("arrival_airport") or {}

        # Airlines
        airlines = []
        for seg in segments:
            airline = seg.get("airline")
            if airline and airline not in airlines:
                airlines.append(airline)

        # Combine all info
        normalized.append({
            "price": total_price,
            "price_display": price_raw,
            "airlines": airlines,
            # in-flight duration
            "total_duration": f.get("total_duration"),
            "departure_airport": dep_airport.get("id"),
            "depart_time": dep_airport.get("time"),
            "arrival_airport": arr_airport.get("id"),
            "arrival_time": arr_airport.get("time"),
        })

    return normalized

# data = search_oneWay_flights("JFK", "SEA", "2025-12-10", 1, 106)
# print(json.dumps(data, indent=2, ensure_ascii=False))

@tool
def search_roundTrip_flights(origin: str, dest: str, depart_date: str, return_date: str, num_people: int, budget):
    """

    Search round trip flights based on user's information

    Args:
        origin (str): Departure airport IATA code (e.g. "SEA", "JFK").
        dest (str): Arrival airport IATA code.
        depart_date (str): Departure date in "YYYY-MM-DD".
        return_date (str): Return date in "YYYY-MM-DD".
        num_people (int): Number of travelers
        budget: user's total budget
    
    Returns:
        dict: Round trip flight information in JSON format

    """
    # Call one way flight search twice 
    outbound = search_oneWay_flights(origin, dest, depart_date, num_people, budget)
    inbound = search_oneWay_flights(dest, origin, return_date, num_people, budget)

    trips = []
    for o in outbound:
        for r in inbound:
            total_price = o["price"] + r["price"]
            if total_price <= budget:
                trips.append({
                    "total_price": total_price,
                    "outbound": o,
                    "return": r,
                })
    return trips

# data = search_roundTrip_flights("JFK", "SEA", "2025-12-10", "2025-12-15", 1, 500)
# print(json.dumps(data, indent=2, ensure_ascii=False))



@tool
def search_hotels(dest, check_in, check_out, num_people, budget):
    """
    Search Top-K hotels using SerpAPI

    Args:
        dest (str): Destination City
        check_in (str): check in date
        check_out (str): check out date
        num_adults (int): number of travelers
        budget: total budget for all travelers
    Returns: 
        list(dict): List of feasible accommodations in JSON format.
        Each hotel dict contains: name, price_per_night, price_per_night_num, 
        total_price_num, rating, reviews, class, lat, lng (latitude/longitude for distance calculation)
    """
    # Convert check_in and check_out date and calculate nights to stay
    check_in_date = datetime.strptime(check_in, "%Y-%m-%d").date()
    check_out_date = datetime.strptime(check_out, "%Y-%m-%d").date()
    nights = (check_out_date - check_in_date).days

    params = {
        "engine": "google_hotels",
        "q": dest,
        "check_in_date": check_in,
        "check_out_date": check_out,
        "adults": num_people,
        "currency": "USD",
        "api_key": SERP_KEY
    }
    search = GoogleSearch(params)
    results = search.get_dict()

    hotels = results.get("properties", [])

    output = []
    for h in hotels:
        price_in_num = parse_price(h.get("rate_per_night", {}).get("lowest"))

        if price_in_num is None:
            continue

        if price_in_num is not None:
            total_price_num = price_in_num * nights
        else:
            total_price_num = None

        if total_price_num <= budget:
            # Extract GPS coordinates if available
            gps_coords = h.get("gps_coordinates", {})
            lat = gps_coords.get("latitude") if gps_coords else None
            lng = gps_coords.get("longitude") if gps_coords else None
            
            output.append({
                "name": h.get("name"),
                "price_per_night": h.get("rate_per_night", {}).get("lowest"), # String Price（ex. "$118"）
                "price_per_night_num": price_in_num, # Numeric Price (ex. 118.0)
                "total_price_num": total_price_num,
                "rating": h.get("overall_rating"),
                "reviews": h.get("reviews"),
                "class": h.get("extracted_hotel_class"),
                "lat": lat,  # Latitude for distance calculation
                "lng": lng,  # Longitude for distance calculation
            })
    
    # 方案4: 限制只返回前10个酒店，减少处理时间
    return output[:10]


@tool
def compute_distance_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Compute great-circle distance between two points in kilometers.

    Args:
        lat1 (float): Latitude of the place1 in decimal degrees.
        lng1 (float): Longtitude of the place1 in decimal degrees.
        lat2 (float): Latitude of the place2 in decimal degrees.
        lng2 (float): Longtitude of the place2 in decimal degrees.

    Return:
        float: The distance between two places in kilometer.

    """
    p1 = (lat1, lng1)
    p2 = (lat2, lng2)
    km = haversine(p1, p2, unit=Unit.KILOMETERS)
    return km


@tool
def compute_itinerary_centroid(itinerary_json: str) -> dict:
    """
    Compute the centroid of all attractions in an itinerary.

    Args:
        itinerary_json (str): JSON format day-by-day itinerary plan generated by planner agent.

    Return:
        dict: The latitude and longtitude of the centroid based on each day's attractions
    """

    def clean_input(text: str):
        # Remove leading/trailing whitespace
        text = text.strip()

        # Case 1: If text looks like a JSON literal inside quotes:
        # e.g. "\"{\\n   \\\"days\\\": ... }\""
        if (text.startswith('"') and text.endswith('"')) or \
           (text.startswith("'") and text.endswith("'")):
            try:
                text = json.loads(text)   # Unescape to raw JSON text
            except:
                pass
        return text

    def extract_json(text: str):
        # strip markdown fences
        text = re.sub(r"```json|```", "", text).strip()

        # Extract first {...} block
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            raise ValueError(f"compute_itinerary_centroid: no JSON found in:\n{text[:200]}")
        json_text = match.group()

        # Remove trailing characters after final matching brace (e.g. "{}}" → "{}")
        # Count braces
        brace_count = 0
        correct_end = None
        for i, ch in enumerate(json_text):
            if ch == '{':
                brace_count += 1
            elif ch == '}':
                brace_count -= 1
                if brace_count == 0:
                    correct_end = i
                    break
        if correct_end is not None:
            json_text = json_text[:correct_end+1]

        return json.loads(json_text)

    # Pipeline 
    itinerary_json = clean_input(itinerary_json)
    itinerary = extract_json(itinerary_json)

    # Compute centroid
    lat_list = []
    lng_list = []

    for day in itinerary.get("days", []):
        for block in ["morning", "afternoon", "evening"]:
            for item in day.get(block, []):
                if "lat" in item and "lng" in item:
                    try:
                        lat_list.append(float(item["lat"]))
                        lng_list.append(float(item["lng"]))
                    except:
                        continue

    if not lat_list:
        return {"lat_center": None, "lng_center": None}

    return {
        "lat_center": sum(lat_list) / len(lat_list),
        "lng_center": sum(lng_list) / len(lng_list)
    }


#pprint(search_attractions("Seattle", 20))
#pprint(search_hotels("Seattle", "2026-01-10", "2026-01-15", 2, 20))

