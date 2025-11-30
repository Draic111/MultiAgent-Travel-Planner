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
    # 方案1: 预计算中心点，避免 Agent 多次调用
    centroid = compute_itinerary_centroid.invoke({"itinerary_json": itinerary_json})
    centroid_lat = centroid.get("lat_center")
    centroid_lng = centroid.get("lng_center")
    
    trip_json = json.dumps(trip_config, ensure_ascii=True, indent = 2)
    
    # 将中心点信息加入用户消息，让 Agent 直接使用
    centroid_info = ""
    if centroid_lat is not None and centroid_lng is not None:
        centroid_info = f"\n\nIMPORTANT: The itinerary centroid (center point) has been pre-calculated:\n"
        centroid_info += f"Centroid Latitude: {centroid_lat}\n"
        centroid_info += f"Centroid Longitude: {centroid_lng}\n"
        centroid_info += "You can use these coordinates directly with compute_distance_km tool. "
        centroid_info += "DO NOT call compute_itinerary_centroid tool again - it's already calculated."

    user_message = {"messages":
    [
        {
            "role": "user",
            "content": (
                "Here is the trip config:\n"
                f"{trip_json}\n\n"
                "Here is the itinerary JSON from the planner agent:\n"
                f"{itinerary_json}\n"
                f"{centroid_info}\n"
                "Please give me some hotel recommendations."
            )
        }
    ]
    }

    result = hotel_agent.invoke(user_message)
    final_message = result["messages"][-1]
    
    # 从 Agent 的消息历史中提取 search_hotels 工具的原始返回结果
    search_hotels_raw_result = None
    for msg in result["messages"]:
        # 查找工具调用的返回结果
        # LangChain 中工具返回通常在 ToolMessage 中
        if hasattr(msg, "name") and msg.name == "search_hotels":
            try:
                content = getattr(msg, "content", None)
                if content:
                    if isinstance(content, str):
                        # 尝试解析 JSON
                        try:
                            search_hotels_raw_result = json.loads(content)
                        except:
                            # 如果不是 JSON，可能是列表的字符串表示
                            search_hotels_raw_result = content
                    elif isinstance(content, list):
                        search_hotels_raw_result = content
                    if search_hotels_raw_result:
                        break
            except:
                pass
    
    # 如果从消息中找不到，手动调用一次 search_hotels 获取原始结果
    # 这样可以确保获取到包含 lat/lng 的完整数据
    if search_hotels_raw_result is None or not isinstance(search_hotels_raw_result, list):
        try:
            search_hotels_raw_result = search_hotels.invoke({
                "dest": trip_config["destination_city"],
                "check_in": trip_config["check_in_date"],
                "check_out": trip_config["check_out_date"],
                "num_people": trip_config["num_people"],
                "budget": trip_config["total_budget"]
            })
        except Exception as e:
            if verbose:
                print(f"警告: 无法获取 search_hotels 原始结果: {e}")
            search_hotels_raw_result = []
    
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
        
        hotel_data = extract_json(final_message.content)
    else:
        hotel_data = extract_json(final_message.content)
    
    # 计算每个酒店到中心点的距离并添加到结果中
    # 通过名称匹配从原始工具结果中获取 lat/lng
    if hotel_data.get("recommended_hotels") and search_hotels_raw_result and centroid_lat is not None and centroid_lng is not None:
        # 创建名称到原始酒店数据的映射（用于匹配）
        raw_hotels_map = {}
        for raw_hotel in search_hotels_raw_result:
            hotel_name = raw_hotel.get("name", "").strip().lower()
            if hotel_name:
                raw_hotels_map[hotel_name] = raw_hotel
        
        for hotel in hotel_data["recommended_hotels"]:
            hotel_name = hotel.get("name", "").strip()
            hotel_name_lower = hotel_name.lower()
            
            # 尝试精确匹配
            matched_raw_hotel = raw_hotels_map.get(hotel_name_lower)
            
            # 如果精确匹配失败，尝试模糊匹配（去除标点、空格等）
            if not matched_raw_hotel:
                for raw_name, raw_hotel in raw_hotels_map.items():
                    # 简单的模糊匹配：去除常见标点和空格后比较
                    normalized_raw = re.sub(r'[^\w]', '', raw_name)
                    normalized_hotel = re.sub(r'[^\w]', '', hotel_name_lower)
                    if normalized_raw == normalized_hotel:
                        matched_raw_hotel = raw_hotel
                        break
            
            if matched_raw_hotel:
                hotel_lat = matched_raw_hotel.get("lat")
                hotel_lng = matched_raw_hotel.get("lng")
                if hotel_lat is not None and hotel_lng is not None:
                    try:
                        distance = compute_distance_km.invoke({
                            "lat1": hotel_lat,
                            "lng1": hotel_lng,
                            "lat2": centroid_lat,
                            "lng2": centroid_lng
                        })
                        hotel["distance_km"] = round(distance, 2)
                    except Exception as e:
                        if verbose:
                            print(f"警告: 计算酒店 '{hotel_name}' 距离失败: {e}")
                        hotel["distance_km"] = None
                else:
                    if verbose:
                        print(f"警告: 酒店 '{hotel_name}' 在原始结果中缺少位置信息")
                    hotel["distance_km"] = None
            else:
                if verbose:
                    print(f"警告: 无法在原始结果中找到酒店 '{hotel_name}' 的匹配项")
                hotel["distance_km"] = None
    
    if verbose:
        return {
            "result": hotel_data,
            "execution_steps": execution_steps,
            "full_messages": result["messages"]
        }
    else:
        return hotel_data



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

