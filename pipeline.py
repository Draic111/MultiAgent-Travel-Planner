# pipeline.py
import json

from planner_agent import generate_plan
from hotel_agent import recommend_hotels
from flight_agent import recommend_flights

def run_pipeline(trip_config: dict, verbose: bool = False) -> dict:
    """
    运行完整的旅行规划pipeline
    
    Args:
        trip_config: 旅行配置字典
        verbose: 是否返回详细的执行过程
    
    Returns:
        如果verbose=False: 返回最终结果
        如果verbose=True: 返回包含结果和执行过程的字典
    """
    execution_log = []
    
    # Step 1: Planner Agent
    if verbose:
        print("\n" + "="*60)
        print("🤖 [步骤 1/3] 调用 Planner Agent - 生成行程规划")
        print("="*60)
        print("正在搜索景点并规划行程...")
    
    planner_result = generate_plan(trip_config, verbose=verbose)
    
    if verbose:
        if isinstance(planner_result, dict) and "execution_steps" in planner_result:
            itinerary = planner_result["result"]
            execution_log.append({
                "agent": "planner_agent",
                "status": "completed",
                "execution_steps": planner_result["execution_steps"],
                "tool_calls_count": sum(
                    len(step.get("tool_calls", [])) 
                    for step in planner_result["execution_steps"]
                )
            })
            print(f"✅ Planner Agent 完成！")
            print(f"   - 执行步骤数: {len(planner_result['execution_steps'])}")
            print(f"   - 工具调用次数: {execution_log[-1]['tool_calls_count']}")
            print(f"   - 规划了 {len(itinerary.get('days', []))} 天的行程")
        else:
            itinerary = planner_result
            execution_log.append({
                "agent": "planner_agent",
                "status": "completed"
            })
            print(f"✅ Planner Agent 完成！规划了 {len(itinerary.get('days', []))} 天的行程")
    else:
        itinerary = planner_result
    
    itinerary_json = json.dumps(itinerary, ensure_ascii=True, indent=2)
    
    # Step 2: Hotel Agent
    if verbose:
        print("\n" + "="*60)
        print("🏨 [步骤 2/3] 调用 Hotel Agent - 推荐酒店")
        print("="*60)
        print("正在搜索酒店并计算最佳位置...")
    
    hotel_result = recommend_hotels(trip_config, itinerary_json, verbose=verbose)
    
    if verbose:
        if isinstance(hotel_result, dict) and "execution_steps" in hotel_result:
            hotels = hotel_result["result"]
            execution_log.append({
                "agent": "hotel_agent",
                "status": "completed",
                "execution_steps": hotel_result["execution_steps"],
                "tool_calls_count": sum(
                    len(step.get("tool_calls", [])) 
                    for step in hotel_result["execution_steps"]
                )
            })
            print(f"✅ Hotel Agent 完成！")
            print(f"   - 执行步骤数: {len(hotel_result['execution_steps'])}")
            print(f"   - 工具调用次数: {execution_log[-1]['tool_calls_count']}")
            print(f"   - 推荐了 {len(hotels.get('recommended_hotels', []))} 家酒店")
        else:
            hotels = hotel_result
            execution_log.append({
                "agent": "hotel_agent",
                "status": "completed"
            })
            print(f"✅ Hotel Agent 完成！推荐了 {len(hotels.get('recommended_hotels', []))} 家酒店")
    else:
        hotels = hotel_result
    
    # Step 3: Flight Agent
    if verbose:
        print("\n" + "="*60)
        print("✈️  [步骤 3/3] 调用 Flight Agent - 推荐航班")
        print("="*60)
        print("正在搜索往返航班...")
    
    flight_result = recommend_flights(trip_config, verbose=verbose)
    
    if verbose:
        if isinstance(flight_result, dict) and "execution_steps" in flight_result:
            flights = flight_result["result"]
            execution_log.append({
                "agent": "flight_agent",
                "status": "completed",
                "execution_steps": flight_result["execution_steps"],
                "tool_calls_count": sum(
                    len(step.get("tool_calls", [])) 
                    for step in flight_result["execution_steps"]
                )
            })
            print(f"✅ Flight Agent 完成！")
            print(f"   - 执行步骤数: {len(flight_result['execution_steps'])}")
            print(f"   - 工具调用次数: {execution_log[-1]['tool_calls_count']}")
        else:
            flights = flight_result
            execution_log.append({
                "agent": "flight_agent",
                "status": "completed"
            })
            print(f"✅ Flight Agent 完成！")
    else:
        flights = flight_result

    final = {
        "trip_config": trip_config,
        "itinerary": itinerary,
        "hotels": hotels,
        "flights": flights,
    }
    
    if verbose:
        final["execution_log"] = execution_log
        print("\n" + "="*60)
        print("🎉 所有 Agent 执行完成！")
        print("="*60)
    
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
