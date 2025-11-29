from tools import search_attractions, compute_distance_km
from prompts import PLANNER_SYSTEM_PROMPT
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from pprint import pprint
from dotenv import load_dotenv
import json
import os
import re


load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

llm = ChatOpenAI(
    model = "gpt-4o-mini",
    api_key= OPENAI_API_KEY
)

planner_agent = create_agent(
    model = llm,
    tools = [search_attractions, compute_distance_km],
    system_prompt = PLANNER_SYSTEM_PROMPT,
)

def _extract_json(text: str):
    text = text.strip()
    text = re.sub(r"```json", "", text)
    text = re.sub(r"```", "", text).strip()

    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        raise ValueError(f"No JSON object found in:\n{text[:200]}")
    json_text = match.group()
    return json.loads(json_text)


def generate_plan(trip_config, verbose=False):
    """
    生成旅行计划
    
    Args:
        trip_config: 旅行配置字典
        verbose: 是否返回详细的执行过程
    
    Returns:
        如果verbose=False: 返回提取的JSON结果
        如果verbose=True: 返回包含结果和执行过程的字典
    """
    info_json = json.dumps(trip_config, ensure_ascii=True, indent = 2)    
    user_message = {
        "messages": [
            {
                "role": "user",
                "content": info_json,
            }
        ]
    }
    result = planner_agent.invoke(user_message)
    final_result = result["messages"][-1]
    
    if verbose:
        # 提取执行过程
        execution_steps = []
        for i, msg in enumerate(result["messages"]):
            step_info = {
                "step": i + 1,
                "type": getattr(msg, "type", "unknown"),
                "role": getattr(msg, "type", "unknown"),
            }
            
            # 如果是AI消息且有工具调用
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                step_info["tool_calls"] = []
                for tool_call in msg.tool_calls:
                    # 处理不同的tool_call格式
                    if isinstance(tool_call, dict):
                        tool_name = tool_call.get("name", tool_call.get("function", {}).get("name", "unknown"))
                        tool_args = tool_call.get("args", tool_call.get("function", {}).get("arguments", {}))
                        # 如果args是字符串，尝试解析为JSON
                        if isinstance(tool_args, str):
                            try:
                                tool_args = json.loads(tool_args)
                            except:
                                pass
                    else:
                        tool_name = getattr(tool_call, "name", "unknown")
                        tool_args = getattr(tool_call, "args", {})
                    
                    step_info["tool_calls"].append({
                        "name": tool_name,
                        "args": tool_args,
                    })
            
            # 如果有内容
            if hasattr(msg, "content") and msg.content:
                content = msg.content
                # 只显示前200个字符，避免过长
                if len(content) > 200:
                    step_info["content_preview"] = content[:200] + "..."
                else:
                    step_info["content"] = content
            
            execution_steps.append(step_info)
        
        return {
            "result": _extract_json(final_result.content),
            "execution_steps": execution_steps,
            "full_messages": result["messages"]
        }
    else:
        return _extract_json(final_result.content)


if __name__ == "__main__":
    # Test Case
    info = {
        "origin_city": "New York City",
        "destination_city": "Los Angeles",
        "check_in_date": "2026-01-10",
        "check_out_date": "2026-01-15",
        "num_people": 1,
        "total_budget": 2000,
    }
    itinerary = generate_plan(info)
    print(json.dumps(itinerary, ensure_ascii=False, indent=2))
    

# user_message = {"messages":
#     [
#         {
#             "role": "user",
#             "content": f"{info_json}"
#         }
#     ]
# }

# result = planner_agent.invoke(user_message)
# final_result = result["messages"][-1]

# print(final_result.content)

# for i, m in enumerate(result["messages"]):
#     print("==== MESSAGE", i, "====")
#     print("type:", getattr(m, "type", None)) 
#     # 如果是 AI 且有 tool_calls
#     if hasattr(m, "tool_calls") and m.tool_calls:
#         print("tool_calls:", m.tool_calls)
#     print("content:", m.content)
#     print()

