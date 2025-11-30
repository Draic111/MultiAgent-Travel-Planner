from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from dotenv import load_dotenv
import json
import os


load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


FORMAT_SYSTEM_PROMPT = """You are a travel assistant whose job is to convert machine-readable pipeline outputs (JSON) into clear, concise, and friendly natural-language summaries for end users.

Instructions:
- Read the provided JSON which contains `trip_config`, `itinerary`, `hotels`, and `flights`.
- Produce a human-friendly travel summary organized with these sections:
  1) Short Overview (destination, dates, travelers, budget)
  2) Day-by-day itinerary (brief bullets per day: morning/afternoon/evening activities)
  3) Hotel recommendations (top picks with one-line reasons and total price)
  4) Flight recommendations (outbound/return highlights and prices)
  5) Quick tips (transport, timing, budget notes)

Output requirements:
- Return plain text (no surrounding JSON or code fences).
- Keep the language natural and suitable for a user-facing message.
- If any field is missing from the input, mention it politely and continue with available info.
"""


llm = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=OPENAI_API_KEY
)


formatter_agent = create_agent(
    model=llm,
    tools=[],
    system_prompt=FORMAT_SYSTEM_PROMPT,
)


def format_trip(pipeline_result: dict, verbose: bool = False):
    """Convert the pipeline JSON result into natural language.

    Args:
        pipeline_result: dict containing keys: `trip_config`, `itinerary`, `hotels`, `flights`.
        verbose: if True, return agent execution details in addition to the text.

    Returns:
        If verbose=False: a plain text string with the user-facing summary.
        If verbose=True: a dict {"text": <str>, "execution_steps": ..., "full_messages": ...}
    """

    info_json = json.dumps(pipeline_result, ensure_ascii=False, indent=2)

    user_message = {
        "messages": [
            {
                "role": "user",
                "content": (
                    "Please convert the following pipeline output into a clear, user-facing travel summary in plain text.\n\n"
                    + info_json
                ),
            }
        ]
    }

    result = formatter_agent.invoke(user_message)
    final_message = result["messages"][-1]
    text = getattr(final_message, "content", "")

    if verbose:
        # Build a light execution trace similar to other agents
        execution_steps = []
        for i, msg in enumerate(result["messages"]):
            step_info = {
                "step": i + 1,
                "type": getattr(msg, "type", "unknown"),
                "role": getattr(msg, "type", "unknown"),
            }
            if hasattr(msg, "content") and msg.content:
                content = msg.content
                if len(content) > 200:
                    step_info["content_preview"] = content[:200] + "..."
                else:
                    step_info["content"] = content
            execution_steps.append(step_info)

        return {
            "text": text,
            "execution_steps": execution_steps,
            "full_messages": result["messages"],
        }

    return text


def generate_attraction_descriptions(pipeline_result: dict, verbose: bool = False):
    """Generate short natural-language descriptions for every attraction in the itinerary.

    Returns either a dict mapping attraction name -> description, or if verbose=True,
    returns a dict with keys `descriptions`, `execution_steps`, `full_messages`.
    """

    # Collect unique attraction names and minimal context
    itinerary = pipeline_result.get("itinerary", {}) or {}
    days = itinerary.get("days", [])
    attractions = []
    for day in days:
        for block in ["morning", "afternoon", "evening"]:
            for item in day.get(block, []) or []:
                name = item.get("name") if isinstance(item, dict) else None
                if name and name not in attractions:
                    attractions.append(name)

    # Prepare prompt asking the model to return JSON mapping
    payload = {
        "attractions": attractions,
        "trip_config": pipeline_result.get("trip_config", {})
    }

    info_json = json.dumps(payload, ensure_ascii=False, indent=2)
    user_message = {
        "messages": [
            {
                "role": "user",
                "content": (
                    "Please generate a concise (1-2 sentence) natural-language description for each attraction listed below. "
                    "Return a single JSON object that maps attraction names to their descriptions. Do not include any other text.\n\n"
                    + info_json
                ),
            }
        ]
    }

    result = formatter_agent.invoke(user_message)
    final_message = result["messages"][-1]
    content = getattr(final_message, "content", "")

    # Extract JSON object from model output
    try:
        # Strip markdown fences if present
        text = content.strip()
        if text.startswith("```"):
            # remove code fences
            text = text.replace("```json", "").replace("```", "").strip()

        # Find first {...} block
        import re
        m = re.search(r"\{[\s\S]*\}", text)
        if not m:
            raise ValueError("No JSON object found in model output")
        json_text = m.group()
        descriptions = json.loads(json_text)
    except Exception as e:
        # fallback: empty descriptions
        descriptions = {name: "" for name in attractions}

    if verbose:
        execution_steps = []
        for i, msg in enumerate(result["messages"]):
            step_info = {"step": i + 1, "type": getattr(msg, "type", "unknown")}
            if hasattr(msg, "content") and msg.content:
                content_preview = msg.content
                step_info["content_preview"] = content_preview if len(content_preview) < 300 else content_preview[:300] + "..."
            execution_steps.append(step_info)

        return {"descriptions": descriptions, "execution_steps": execution_steps, "full_messages": result["messages"]}

    return descriptions


if __name__ == "__main__":
    # small local test using a minimal fake pipeline result
    sample = {
        "trip_config": {
            "origin_city": "New York City",
            "destination_city": "Los Angeles",
            "check_in_date": "2026-01-10",
            "check_out_date": "2026-01-15",
            "num_people": 1,
            "total_budget": 2000,
        },
        "itinerary": {
            "destination": "Los Angeles",
            "days": [
                {"day_index": 1, "date": "DAY 1", "morning": [{"name": "Griffith Observatory"}], "afternoon": [{"name": "Hollywood Walk of Fame"}], "evening": [{"name": "Santa Monica Pier"}]},
                {"day_index": 2, "date": "DAY 2", "morning": [{"name": "The Getty Center"}], "afternoon": [], "evening": []},
            ],
        },
        "hotels": {
            "destination": "Los Angeles",
            "nights": 5,
            "hotel_budget_per_night": 120.0,
            "recommended_hotels": [
                {"name": "Cozy LA Inn", "price_per_night": 115.0, "total_price": 575.0, "rating": 4.2, "reason": "Close to beaches and attractions"}
            ]
        },
        "flights": {
            "outbound": {"destination": "LAX", "recommended_flights": [{"airline": "Delta", "price": 250, "departure_time": "08:00", "arrival_time": "11:00"}]},
            "return": {"destination": "JFK", "recommended_flights": [{"airline": "Delta", "price": 260, "departure_time": "18:00", "arrival_time": "02:00"}]}
        }
    }

    print(format_trip(sample))

