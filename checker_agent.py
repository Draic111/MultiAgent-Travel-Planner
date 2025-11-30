# checker_agent.py
"""
Checker Agent - Validates travel plan against constraints
"""
from tools import compute_distance_km, compute_itinerary_centroid
import json


def check_plan(itinerary: dict, hotels: dict, flights: dict, total_budget: float) -> dict:
    """
    Validates travel plan against constraints
    
    Args:
        itinerary: Itinerary planning result
        hotels: Hotel recommendation result
        flights: Flight recommendation result
        total_budget: Total budget
    
    Returns:
        dict: {
            "passed": bool,
            "violations": [{"rule": str, "message": str}]
        }
    """
    violations = []
    check_details = []  # Store detailed results for each validation item
    
    # 1. JSON Format Validation (basic check)
    try:
        # Check if required fields exist
        if not isinstance(itinerary, dict) or not isinstance(hotels, dict) or not isinstance(flights, dict):
            violations.append({
                "rule": "json_format",
                "message": "Invalid result format, missing required fields"
            })
            check_details.append({"rule": "json_format", "status": "failed", "message": "Invalid result format"})
            return {"passed": False, "violations": violations, "check_details": check_details}
        else:
            check_details.append({"rule": "json_format", "status": "passed", "message": "JSON format validation passed"})
    except Exception as e:
        violations.append({
            "rule": "json_format",
            "message": f"JSON format validation failed: {str(e)}"
        })
        check_details.append({"rule": "json_format", "status": "failed", "message": f"JSON format validation failed: {str(e)}"})
        return {"passed": False, "violations": violations, "check_details": check_details}
    
    # 2. Budget 验证
    try:
        # 计算航班总价
        flight_total = 0
        if flights.get("outbound") and flights.get("outbound").get("recommended_flights"):
            outbound_flights = flights["outbound"]["recommended_flights"]
            if outbound_flights:
                flight_total += outbound_flights[0].get("price", 0)
        
        if flights.get("return") and flights.get("return").get("recommended_flights"):
            return_flights = flights["return"]["recommended_flights"]
            if return_flights:
                flight_total += return_flights[0].get("price", 0)
        
        # 计算酒店总价（取平均值）
        hotel_total = 0
        if hotels.get("recommended_hotels") and len(hotels["recommended_hotels"]) > 0:
            hotel_prices = [hotel.get("total_price", 0) for hotel in hotels["recommended_hotels"]]
            hotel_total = sum(hotel_prices) / len(hotel_prices)  # 取平均值
        else:
            hotel_total = 0
        
        # 总开销 = 航班 + 酒店 + 50% 作为其他开销估算
        other_expenses = (flight_total + hotel_total) * 0.5
        total_cost = flight_total + hotel_total + other_expenses
        
        if total_cost > total_budget:
            violations.append({
                "rule": "budget",
                "message": f"Total cost ${total_cost:.2f} exceeds budget ${total_budget:.2f} (flights: ${flight_total:.2f}, hotels: ${hotel_total:.2f}, other expenses: ${other_expenses:.2f})"
            })
            check_details.append({
                "rule": "budget",
                "status": "failed",
                "message": f"Total cost ${total_cost:.2f} exceeds budget ${total_budget:.2f}"
            })
        else:
            check_details.append({
                "rule": "budget",
                "status": "passed",
                "message": f"Budget validation passed (total cost: ${total_cost:.2f}, budget: ${total_budget:.2f})"
            })
    except Exception as e:
        violations.append({
            "rule": "budget",
            "message": f"Budget validation failed: {str(e)}"
        })
        check_details.append({
            "rule": "budget",
            "status": "failed",
            "message": f"Budget validation failed: {str(e)}"
        })
    
    # 3. 每天景点数验证（>=1 且 <=5）
    try:
        days = itinerary.get("days", [])
        attractions_issues = []
        for day in days:
            day_index = day.get("day_index", 0)
            morning = day.get("morning", [])
            afternoon = day.get("afternoon", [])
            evening = day.get("evening", [])
            
            total_attractions = len(morning) + len(afternoon) + len(evening)
            
            if total_attractions < 1:
                violations.append({
                    "rule": "attractions_count",
                    "message": f"Day {day_index} has no attractions (minimum 1 required)"
                })
                attractions_issues.append(f"Day {day_index} has no attractions")
            elif total_attractions > 5:
                violations.append({
                    "rule": "attractions_count",
                    "message": f"Day {day_index} has {total_attractions} attractions (maximum 5 allowed)"
                })
                attractions_issues.append(f"Day {day_index} has {total_attractions} attractions (exceeds 5)")
        
        if attractions_issues:
            check_details.append({
                "rule": "attractions_count",
                "status": "failed",
                "message": "; ".join(attractions_issues)
            })
        else:
            check_details.append({
                "rule": "attractions_count",
                "status": "passed",
                "message": f"All {len(days)} days have attractions count within limit (1-5)"
            })
    except Exception as e:
        violations.append({
            "rule": "attractions_count",
            "message": f"Attractions count validation failed: {str(e)}"
        })
        check_details.append({
            "rule": "attractions_count",
            "status": "failed",
            "message": f"Attractions count validation failed: {str(e)}"
        })
    
    # 4. Hotel Distance Validation (all hotels within 15km of centroid)
    try:
        recommended_hotels = hotels.get("recommended_hotels", [])
        distance_issues = []
        for hotel in recommended_hotels:
            hotel_name = hotel.get("name", "Unknown Hotel")
            
            # 优先使用已计算的 distance_km（如果 hotel_agent 已计算）
            if "distance_km" in hotel and hotel["distance_km"] is not None:
                distance = hotel["distance_km"]
            else:
                # 如果没有，则重新计算
                hotel_lat = hotel.get("lat")
                hotel_lng = hotel.get("lng")
                
                if hotel_lat is None or hotel_lng is None:
                    violations.append({
                        "rule": "hotel_distance",
                        "message": f"Hotel '{hotel_name}' missing location information"
                    })
                    distance_issues.append(f"'{hotel_name}' missing location information")
                    continue
                
                # Calculate itinerary centroid
                itinerary_json = json.dumps(itinerary, ensure_ascii=True)
                centroid = compute_itinerary_centroid.invoke({"itinerary_json": itinerary_json})
                centroid_lat = centroid.get("lat_center")
                centroid_lng = centroid.get("lng_center")
                
                if centroid_lat is None or centroid_lng is None:
                    violations.append({
                        "rule": "hotel_distance",
                        "message": f"Cannot calculate itinerary centroid, unable to validate distance for hotel '{hotel_name}'"
                    })
                    distance_issues.append(f"Cannot calculate centroid")
                    continue
                
                distance = compute_distance_km.invoke({
                    "lat1": hotel_lat,
                    "lng1": hotel_lng,
                    "lat2": centroid_lat,
                    "lng2": centroid_lng
                })
            
            if distance >= 10:
                violations.append({
                    "rule": "hotel_distance",
                    "message": f"Hotel '{hotel_name}' is {distance:.2f} km from itinerary centroid, exceeds limit (10km)"
                })
                distance_issues.append(f"'{hotel_name}' distance {distance:.2f}km")
        
        if distance_issues:
            check_details.append({
                "rule": "hotel_distance",
                "status": "failed",
                "message": "; ".join(distance_issues)
            })
        else:
            check_details.append({
                "rule": "hotel_distance",
                "status": "passed",
                "message": f"All {len(recommended_hotels)} hotels are within 10km of centroid"
            })
    except Exception as e:
        violations.append({
            "rule": "hotel_distance",
            "message": f"Hotel distance validation failed: {str(e)}"
        })
        check_details.append({
            "rule": "hotel_distance",
            "status": "failed",
            "message": f"Hotel distance validation failed: {str(e)}"
        })
    
    # 5. Flight Completeness Validation
    try:
        has_outbound = flights.get("outbound") and flights["outbound"].get("recommended_flights")
        has_return = flights.get("return") and flights["return"].get("recommended_flights")
        
        flight_issues = []
        if not has_outbound:
            violations.append({
                "rule": "flight_completeness",
                "message": "Missing outbound flight recommendation"
            })
            flight_issues.append("Missing outbound flight")
        
        if not has_return:
            violations.append({
                "rule": "flight_completeness",
                "message": "Missing return flight recommendation"
            })
            flight_issues.append("Missing return flight")
        
        if flight_issues:
            check_details.append({
                "rule": "flight_completeness",
                "status": "failed",
                "message": "; ".join(flight_issues)
            })
        else:
            check_details.append({
                "rule": "flight_completeness",
                "status": "passed",
                "message": "Both outbound and return flights are recommended"
            })
    except Exception as e:
        violations.append({
            "rule": "flight_completeness",
            "message": f"Flight completeness validation failed: {str(e)}"
        })
        check_details.append({
            "rule": "flight_completeness",
            "status": "failed",
            "message": f"Flight completeness validation failed: {str(e)}"
        })
    
    return {
        "passed": len(violations) == 0,
        "violations": violations,
        "check_details": check_details
    }
