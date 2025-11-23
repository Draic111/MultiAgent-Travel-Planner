# pipeline.py
import json

from planner_agent import generate_plan
from hotel_agent import recommend_hotels
from flight_agent import recommend_flights

def run_pipeline(trip_config: dict) -> dict:
    itinerary = generate_plan(trip_config)

    itinerary_json = json.dumps(itinerary, ensure_ascii=True, indent=2)
    hotels = recommend_hotels(trip_config, itinerary_json)
    flights = recommend_flights(trip_config)

    final = {
        "trip_config": trip_config,
        "itinerary": itinerary,
        "hotels": hotels,
        "flights": flights,
    }

    return final

if __name__ == "__main__":
    info = {
        "origin_city": "Seattle",
        "destination_city": "New York",
        "check_in_date": "2026-01-10",
        "check_out_date": "2026-01-15",
        "num_people": 2,
        "total_budget": 2000,
    }

    result = run_pipeline(info)
    print(json.dumps(result, ensure_ascii=False, indent=2))
