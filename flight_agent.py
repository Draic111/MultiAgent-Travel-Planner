from tools import search_roundTrip_flights
from prompts import FLIGHT_SYSTEM_PROMPT
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from dotenv import load_dotenv
import json
import os, re

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

CITY_TO_IATA = {
    "St. Louis": "STL",
    "Phoenix": "PHX",
    "Seattle": "SEA",
    "New York": "JFK",   
    "Los Angeles": "LAX",
    "San Francisco": "SFO",
    "Chicago": "ORD", 
    "Dallas": "DFW",
    "Houston": "IAH",
    "Miami": "MIA",
    "Boston": "BOS",
}

llm = ChatOpenAI(
    model = "gpt-4o-mini",
    api_key = OPENAI_API_KEY
)


flight_agent = create_agent(
    model = llm,
    tools = [search_roundTrip_flights],
    system_prompt = FLIGHT_SYSTEM_PROMPT
)

def extract_json(text: str):
    text = text.strip()
    text = re.sub(r"```json", "", text)
    text = re.sub(r"```", "", text).strip()

    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        raise ValueError(f"No JSON object found in:\n{text[:200]}")
    json_text = match.group()
    return json.loads(json_text)


def recommend_flights(trip_config: dict, verbose=False) -> dict:
    """Call Flight Agent and get JSON format flight information.
    
    Args:
        trip_config (dict): User's original input in JSON format
        verbose: 是否返回详细的执行过程
    
    Returns:
        如果verbose=False: 返回提取的JSON结果
        如果verbose=True: 返回包含结果和执行过程的字典
    
    """

    origin_city = trip_config.get("origin_city")
    dest_city = trip_config.get("destination_city")
    origin_airport = CITY_TO_IATA.get(origin_city)
    dest_airport = CITY_TO_IATA.get(dest_city)

    # A new dictionary containing airport IATA code
    flight_input = {
        **trip_config,
        "origin_airport": origin_airport,
        "destination_airport": dest_airport,
    }

    info_json = json.dumps(flight_input, ensure_ascii=False, indent=2)
    user_message = {
        "messages": [
            {
                "role": "user",
                "content": info_json,
            }
        ]
    }
    result = flight_agent.invoke(user_message)
    final_message = result["messages"][-1]
    
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
                if len(content) > 200:
                    step_info["content_preview"] = content[:200] + "..."
                else:
                    step_info["content"] = content
            
            execution_steps.append(step_info)
        
        return {
            "result": extract_json(final_message.content),
            "execution_steps": execution_steps,
            "full_messages": result["messages"]
        }
    else:
        return extract_json(final_message.content)



if __name__ == "__main__":
    info = {
        "origin_city": "New York",
        "destination_city": "Seattle",
        "check_in_date": "2026-01-10",
        "check_out_date": "2026-01-15",
        "num_people": 2,
        "total_budget": 1000,
    }
    flights = recommend_flights(info)
    print(json.dumps(flights, ensure_ascii=False, indent=2))



# # Tested User input
# info = {
#     "origin_city": "JFK",
#     "destination_city": "SEA",
#     "check_in_date": "2026-01-10",
#     "check_out_date": "2026-01-15",
#     "num_people": 2,
#     "total_budget": 1000,
# }

# info_json = json.dumps(info, ensure_ascii=False, indent=2)

# flight_agent = create_agent(
#     model = llm,
#     tools = [search_roundTrip_flights],
#     system_prompt = FLIGHT_SYSTEM_PROMPT
# )

# user_message = {"messages":
#     [
#         {
#             "role": "user",
#             "content": f"{info_json}"
#         }
#     ]
# }

# result = flight_agent.invoke(user_message)
# final_result = result["messages"][-1]