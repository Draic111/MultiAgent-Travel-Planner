# pipeline.py
import json

from planner_agent import generate_plan
from hotel_agent import recommend_hotels
from flight_agent import recommend_flights
from checker_agent import check_plan
from formatter_agent import format_trip, generate_attraction_descriptions

def run_pipeline(trip_config: dict, verbose: bool = False) -> dict:
    """
    运行完整的旅行规划pipeline，包含checker验证和迭代
    
    Args:
        trip_config: 旅行配置字典
        verbose: 是否返回详细的执行过程
    
    Returns:
        如果verbose=False: 返回最终结果
        如果verbose=True: 返回包含结果和执行过程的字典
    """
    max_iterations = 2
    iteration = 0
    check_results = []
    iteration_logs = []  # 保存每次迭代的 execution_log 和 check_result
    
    while iteration < max_iterations:
        iteration += 1
        execution_log = []  # 每次迭代重置
        if verbose:
            print(f"\n{'='*60}")
            print(f"🔄 迭代 {iteration}/{max_iterations}")
            print(f"{'='*60}")
        
        # Step 1: Planner Agent
        if verbose:
            print("\n" + "="*60)
            print(" [步骤 1/5] 调用 Planner Agent - 生成行程规划")
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
            print(" [步骤 2/5] 调用 Hotel Agent - 推荐酒店")
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
            print("  [步骤 3/5] 调用 Flight Agent - 推荐航班")
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
        
        # Step 4: Checker Agent - 验证结果
        if verbose:
            print("\n" + "="*60)
            print("✅ [步骤 4/5] 调用 Checker Agent - 验证计划")
            print("="*60)
            print("正在验证计划是否符合限制条件...")
        
        check_result = check_plan(
            itinerary=itinerary,
            hotels=hotels,
            flights=flights,
            total_budget=trip_config["total_budget"]
        )
        check_results.append(check_result)
        
        # 将 checker 作为第四个 agent 添加到 execution_log
        execution_log.append({
            "agent": "checker_agent",
            "status": "completed",
            "check_result": check_result
        })
        
        if verbose:
            if check_result["passed"]:
                print("✅ Checker 验证通过！")
            else:
                print(f"❌ Checker 验证失败，发现 {len(check_result['violations'])} 个问题：")
                for violation in check_result["violations"]:
                    print(f"   - [{violation['rule']}] {violation['message']}")
        
        # Step 5: Formatter Agent - 生成景点描述和自然语言摘要
        if verbose:
            print("\n" + "="*60)
            print(" [步骤 5/5] 调用 Formatter Agent - 生成自然语言摘要与景点描述")
            print("="*60)
            print("正在为景点生成简短描述并输出用户可读摘要...")
        
        # Generate LLM descriptions for attractions and inject into itinerary
        try:
            pipeline_result_for_formatter = {
                "trip_config": trip_config,
                "itinerary": itinerary,
                "hotels": hotels,
                "flights": flights,
            }
            
            descriptions_verbose = generate_attraction_descriptions(
                pipeline_result_for_formatter, 
                verbose=verbose
            )
            
            if verbose and isinstance(descriptions_verbose, dict) and "descriptions" in descriptions_verbose:
                descriptions = descriptions_verbose.get("descriptions", {})
                execution_log.append({
                    "agent": "formatter_agent",
                    "status": "completed",
                    "execution_steps": descriptions_verbose.get("execution_steps", []),
                })
            elif not verbose:
                descriptions = descriptions_verbose
            else:
                descriptions = {}
            
            # Inject descriptions into itinerary items
            for day in itinerary.get("days", []):
                for block in ["morning", "afternoon", "evening"]:
                    for it in day.get(block, []) or []:
                        if isinstance(it, dict) and it.get("name"):
                            it["description"] = descriptions.get(it.get("name"), it.get("description", ""))
            
            # Generate full human-readable summary
            summary_text = format_trip(pipeline_result_for_formatter, verbose=verbose)
            
            if verbose:
                print("✅ Formatter Agent 完成！生成了用户可读摘要和景点描述")
        except Exception as e:
            summary_text = None
            if verbose:
                print(f"⚠️ Formatter Agent 失败: {e}")
                execution_log.append({
                    "agent": "formatter_agent",
                    "status": "failed",
                    "error": str(e)
                })
        
        # 保存本次迭代的日志
        iteration_logs.append({
            "iteration": iteration,
            "execution_log": execution_log.copy(),
            "check_result": check_result
        })
        
        # 如果验证通过，返回结果
        if check_result["passed"]:
            final = {
                "trip_config": trip_config,
                "itinerary": itinerary,
                "hotels": hotels,
                "flights": flights,
                "check_result": check_result,
                "iterations": iteration,
                "summary_text": summary_text,
            }
            
            if verbose:
                final["iteration_logs"] = iteration_logs
                final["execution_log"] = execution_log  # 保留最后一次的用于兼容
                print("\n" + "="*60)
                print("🎉 所有 Agent 执行完成，验证通过！")
                print("="*60)
            
            return final
        
        # 如果验证失败且还有迭代次数，继续循环
        if iteration < max_iterations:
            if verbose:
                print(f"\n⚠️  验证失败，开始第 {iteration + 1} 次迭代...")
        else:
            # 达到最大迭代次数，返回失败的结果
            if verbose:
                print(f"\n⚠️  已达到最大迭代次数 ({max_iterations})，返回当前结果")
            
            final = {
                "trip_config": trip_config,
                "itinerary": itinerary,
                "hotels": hotels,
                "flights": flights,
                "check_result": check_result,
                "iterations": iteration,
                "all_check_results": check_results,
                "summary_text": summary_text if 'summary_text' in locals() else None,
            }
            
            if verbose:
                final["iteration_logs"] = iteration_logs
                final["execution_log"] = execution_log  # 保留最后一次的用于兼容
                print("\n" + "="*60)
                print("⚠️  所有 Agent 执行完成，但验证未通过")
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
