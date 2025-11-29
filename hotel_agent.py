from tools import search_hotels, compute_itinerary_centroid, compute_distance_km
from prompts import HOTEL_SYSTEM_PROMPT
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from dotenv import load_dotenv
import json
import os, re

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

llm = ChatOpenAI(
    model = "gpt-4o-mini",
    api_key = OPENAI_API_KEY
)

hotel_agent = create_agent(
    model = llm,
    tools = [search_hotels, compute_itinerary_centroid, compute_distance_km],
    system_prompt = HOTEL_SYSTEM_PROMPT
)

def extract_json(text: str):
    if not text:
        raise ValueError("Empty model output")

    # remove markdown fences
    text = text.strip()
    text = re.sub(r"```json", "", text)
    text = re.sub(r"```", "", text).strip()

    # extract JSON object
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        raise ValueError(f"No JSON object found in:\n{text[:200]}")
    
    json_text = match.group()
    return json.loads(json_text)


def recommend_hotels(trip_config, itinerary_json, verbose=False):
    """
    推荐酒店
    
    Args:
        trip_config: 旅行配置字典
        itinerary_json: 行程JSON字符串
        verbose: 是否返回详细的执行过程
    
    Returns:
        如果verbose=False: 返回提取的JSON结果
        如果verbose=True: 返回包含结果和执行过程的字典
    """
    trip_json = json.dumps(trip_config, ensure_ascii=True, indent = 2)

    user_message = {"messages":
    [
        {
            "role": "user",
            "content": (
                "Here is the trip config:\n"
                f"{trip_json}\n\n"
                "Here is the itinerary JSON from the planner agent:\n"
                f"{itinerary_json}\n\n"
                "Please give me some hotel recommendations "   
            )
        }
    ]
    }

    result = hotel_agent.invoke(user_message)
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
    "origin_city": "St. Louis",
    "destination_city": "Phoenix",
    "check_in_date": "2026-01-10",
    "check_out_date": "2026-01-15",
    "num_people": 1,
    "total_budget": 800,
}
    dummy_itinerary = """
    {
        "destination": "Phoenix",
        "days": [
            {
                "day_index": 1,
                "date": "DAY 1",
                "morning": [
                    {
                        "name": "Scottsdale Museum of Contemporary Art",
                        "lat": "33.4915997",
                        "lng": "-111.923191"
                    }
                ],
                "afternoon": [
                    {
                        "name": "Children's Museum of Phoenix",
                        "lat": "33.4504055",
                        "lng": "-112.0643623"
                    }
                ],
                "evening": [
                    {
                        "name": "Japanese Friendship Garden of Phoenix",
                        "lat": "33.4609597",
                        "lng": "-112.0765703"
                    }
                ]
            },
            {
                "day_index": 2,
                "date": "DAY 2",
                "morning": [
                    {
                        "name": "Heritage & Science Park",
                        "lat": "33.450207",
                        "lng": "-112.0659142"
                    }
                ],
                "afternoon": [
                    {
                        "name": "S'edav Va'aki Museum",
                        "lat": "33.4457435",
                        "lng": "-111.9846914"
                    }
                ],
                "evening": [
                    {
                        "name": "Hall of Flame Fire Museum",
                        "lat": "33.44735480000001",
                        "lng": "-111.9534253"
                    }
                ]
            },
            {
                "day_index": 3,
                "date": "DAY 3",
                "morning": [
                    {
                        "name": "Desert Botanical Garden",
                        "lat": "33.4616795",
                        "lng": "-111.944926"
                    }
                ],
                "afternoon": [
                    {
                        "name": "Encanto Park",
                        "lat": "33.4742548",
                        "lng": "-112.0891785"
                    }
                ],
                "evening": [
                    {
                        "name": "Phoenix Zoo",
                        "lat": "33.4500374",
                        "lng": "-111.9470063"
                    }
                ]
            }
        ]
    }
    """
    hotels = recommend_hotels(info, dummy_itinerary)
    print(json.dumps(hotels, ensure_ascii=False, indent=2))

