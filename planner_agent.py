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


def generate_plan(trip_config):
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

