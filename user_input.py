# user_input.py
"""
用户输入界面 - 允许用户自定义输入旅行配置信息
"""
import json
from pipeline import run_pipeline
from datetime import datetime


def get_user_input() -> dict:
    """
    获取用户输入的旅行配置信息
    
    Returns:
        dict: 包含旅行配置的字典
    """
    print("=" * 60)
    print("欢迎使用旅行规划系统！")
    print("=" * 60)
    print()
    
    # 获取出发城市
    origin_city = input("请输入出发城市 (例如: Seattle): ").strip()
    if not origin_city:
        raise ValueError("出发城市不能为空")
    
    # 获取目的地城市
    destination_city = input("请输入目的地城市 (例如: New York): ").strip()
    if not destination_city:
        raise ValueError("目的地城市不能为空")
    
    # 获取入住日期
    check_in_date = input("请输入入住日期 (格式: YYYY-MM-DD, 例如: 2026-01-10): ").strip()
    if not check_in_date:
        raise ValueError("入住日期不能为空")
    
    # 验证日期格式
    try:
        datetime.strptime(check_in_date, "%Y-%m-%d")
    except ValueError:
        raise ValueError(f"入住日期格式不正确，应为 YYYY-MM-DD，例如: 2026-01-10")
    
    # 获取退房日期
    check_out_date = input("请输入退房日期 (格式: YYYY-MM-DD, 例如: 2026-01-15): ").strip()
    if not check_out_date:
        raise ValueError("退房日期不能为空")
    
    # 验证日期格式
    try:
        datetime.strptime(check_out_date, "%Y-%m-%d")
    except ValueError:
        raise ValueError(f"退房日期格式不正确，应为 YYYY-MM-DD，例如: 2026-01-15")
    
    # 验证退房日期晚于入住日期
    check_in = datetime.strptime(check_in_date, "%Y-%m-%d")
    check_out = datetime.strptime(check_out_date, "%Y-%m-%d")
    if check_out <= check_in:
        raise ValueError("退房日期必须晚于入住日期")
    
    # 获取人数
    num_people_input = input("请输入旅行人数 (例如: 2): ").strip()
    if not num_people_input:
        raise ValueError("旅行人数不能为空")
    
    try:
        num_people = int(num_people_input)
        if num_people <= 0:
            raise ValueError("旅行人数必须大于0")
    except ValueError:
        raise ValueError(f"旅行人数必须是正整数，您输入的是: {num_people_input}")
    
    # 获取总预算
    total_budget_input = input("请输入总预算 (USD, 例如: 2000): ").strip()
    if not total_budget_input:
        raise ValueError("总预算不能为空")
    
    try:
        total_budget = float(total_budget_input)
        if total_budget <= 0:
            raise ValueError("总预算必须大于0")
    except ValueError:
        raise ValueError(f"总预算必须是数字，您输入的是: {total_budget_input}")
    
    # 构建配置字典
    trip_config = {
        "origin_city": origin_city,
        "destination_city": destination_city,
        "check_in_date": check_in_date,
        "check_out_date": check_out_date,
        "num_people": num_people,
        "total_budget": total_budget,
    }
    
    return trip_config


def display_execution_details(execution_log: list):
    """
    显示agent执行过程的详细信息
    
    Args:
        execution_log: 执行日志列表
    """
    print("\n" + "=" * 60)
    print("📊 Agent 执行过程详情")
    print("=" * 60)
    
    for agent_log in execution_log:
        agent_name = agent_log.get("agent", "unknown")
        print(f"\n【{agent_name.upper()}】")
        print("-" * 60)
        
        if "execution_steps" in agent_log:
            steps = agent_log["execution_steps"]
            print(f"总执行步骤数: {len(steps)}")
            print(f"工具调用次数: {agent_log.get('tool_calls_count', 0)}")
            print("\n执行步骤详情:")
            
            for step in steps:
                step_num = step.get("step", 0)
                step_type = step.get("type", "unknown")
                print(f"\n  步骤 {step_num} [{step_type}]:")
                
                # 显示工具调用
                if "tool_calls" in step and step["tool_calls"]:
                    for tool_call in step["tool_calls"]:
                        tool_name = tool_call.get("name", "unknown")
                        tool_args = tool_call.get("args", {})
                        print(f"    🔧 调用工具: {tool_name}")
                        if tool_args:
                            # 只显示关键参数，避免过长
                            args_preview = {}
                            for key, value in tool_args.items():
                                if isinstance(value, str) and len(value) > 50:
                                    args_preview[key] = value[:50] + "..."
                                else:
                                    args_preview[key] = value
                            print(f"       参数: {json.dumps(args_preview, ensure_ascii=False, indent=8)}")
                
                # 显示内容预览
                if "content_preview" in step:
                    print(f"    💭 思考过程: {step['content_preview']}")
                elif "content" in step and step["content"]:
                    content = step["content"]
                    if len(content) > 150:
                        print(f"    💭 思考过程: {content[:150]}...")
                    else:
                        print(f"    💭 思考过程: {content}")
        else:
            print("  执行完成（无详细步骤记录）")


def display_result(result: dict, show_details: bool = False):
    """
    格式化显示结果
    
    Args:
        result: pipeline返回的结果字典
        show_details: 是否显示执行过程详情
    """
    print()
    print("=" * 60)
    print("📋 旅行规划结果")
    print("=" * 60)
    
    # 显示迭代信息
    if "iterations" in result:
        print(f"\n【迭代信息】")
        print(f"  总迭代次数: {result['iterations']}")
    
    # 显示验证结果
    if "check_result" in result:
        check_result = result["check_result"]
        print(f"\n【验证结果】")
        
        # 显示每个验证项的详细过程
        if "check_details" in check_result:
            print("  验证过程详情：")
            for detail in check_result["check_details"]:
                rule_name = detail.get("rule", "unknown")
                status = detail.get("status", "unknown")
                message = detail.get("message", "")
                
                # 规则名称映射
                rule_names = {
                    "json_format": "JSON格式验证",
                    "budget": "预算验证",
                    "attractions_count": "景点数验证",
                    "hotel_distance": "酒店距离验证",
                    "flight_completeness": "航班完整性验证"
                }
                rule_display = rule_names.get(rule_name, rule_name)
                
                if status == "passed":
                    print(f"    ✅ {rule_display}: {message}")
                else:
                    print(f"    ❌ {rule_display}: {message}")
        
        # 显示总体结果
        if check_result["passed"]:
            print(f"\n  ✅ 总体验证通过！所有限制条件都满足")
        else:
            print(f"\n  ❌ 总体验证失败，发现 {len(check_result['violations'])} 个问题：")
            for i, violation in enumerate(check_result["violations"], 1):
                print(f"    {i}. [{violation['rule']}] {violation['message']}")
        
        # 如果有多次迭代的验证结果
        if "all_check_results" in result:
            print(f"\n【所有迭代的验证结果】")
            for idx, cr in enumerate(result["all_check_results"], 1):
                status = "✅ 通过" if cr["passed"] else f"❌ 失败 ({len(cr['violations'])} 个问题)"
                print(f"  迭代 {idx}: {status}")
    
    # 如果有执行日志，先显示摘要
    if "execution_log" in result and show_details:
        print("\n【执行摘要】")
        for agent_log in result["execution_log"]:
            agent_name = agent_log.get("agent", "unknown")
            status = agent_log.get("status", "unknown")
            tool_calls = agent_log.get("tool_calls_count", 0)
            print(f"  {agent_name}: {status} (工具调用: {tool_calls}次)")
    
    # 显示最终结果
    print("\n【最终结果】")
    result_to_show = {k: v for k, v in result.items() 
                      if k not in ["execution_log", "check_result", "iterations", "all_check_results"]}
    print(json.dumps(result_to_show, ensure_ascii=False, indent=2))
    
    # 显示详细执行过程
    if "execution_log" in result and show_details:
        display_execution_details(result["execution_log"])


def main():
    """
    主函数：获取用户输入，运行pipeline，显示结果
    """
    try:
        # 获取用户输入
        trip_config = get_user_input()
        
        # 显示用户输入的配置
        print()
        print("=" * 60)
        print("您输入的配置信息：")
        print("=" * 60)
        print(json.dumps(trip_config, ensure_ascii=False, indent=2))
        print()
        
        # 确认是否继续
        confirm = input("确认以上信息无误？(y/n，默认y): ").strip().lower()
        if confirm and confirm != 'y' and confirm != 'yes':
            print("已取消，请重新运行程序。")
            return
        
        # 询问是否显示详细过程
        show_details = input("是否显示 Agent 执行过程详情？(y/n，默认n): ").strip().lower()
        show_details = show_details in ['y', 'yes']
        
        # 运行pipeline
        print()
        print("=" * 60)
        print("正在生成旅行规划，请稍候...")
        print("=" * 60)
        
        result = run_pipeline(trip_config, verbose=show_details)
        
        # 显示结果
        display_result(result, show_details=show_details)
        
    except KeyboardInterrupt:
        print("\n\n程序被用户中断。")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

