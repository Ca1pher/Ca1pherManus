# app/langgraph_core/tools/common_tools.py

from langchain_core.tools import tool
from typing import Dict, Any


@tool
def calculator(expression: str) -> str:
    """
    Evaluates a mathematical expression and returns the result.
    Example: calculator("2 + 2") -> "4"
    This tool is useful for any mathematical calculations.
    """
    try:
        return str(eval(expression))
    except Exception as e:
        return f"Error evaluating expression: {e}"


@tool
def get_current_weather(location: str, unit: str = "celsius") -> Dict[str, Any]:
    """
    Fetches the current weather for a given location.
    The unit can be 'celsius' or 'fahrenheit'.
    This tool is useful when the user asks about the weather in a specific city or region.
    """
    print(f"--- Simulating weather API call for {location} in {unit} ---")
    weather_data = {
        "New York": {"celsius": 25, "fahrenheit": 77, "condition": "Sunny"},
        "London": {"celsius": 18, "fahrenheit": 64, "condition": "Cloudy"},
        "Tokyo": {"celsius": 28, "fahrenheit": 82, "condition": "Humid"},
        "Beijing": {"celsius": 30, "fahrenheit": 86, "condition": "Smoggy"}
    }

    if location in weather_data:
        data = weather_data[location]
        temp = data[unit]
        condition = data["condition"]
        return {"location": location, "temperature": temp, "unit": unit, "condition": condition}
    else:
        return {"error": f"Weather data for {location} not available."}


all_tools = [calculator, get_current_weather]
