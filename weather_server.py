"""
Weather Data Dashboard - MCP Server

Provides a get_current_weather(location) tool.
The tool fetches current weather data from wttr.in.
"""

import json
from urllib.parse import quote
from urllib.request import Request, urlopen

from mcp.server.mcpserver import MCPServer


# Create MCP server
server = MCPServer("Weather Data Dashboard")


@server.tool()
def get_current_weather(location: str) -> str:
    """
    Get current weather information for a location.

    Args:
        location: City or location name.

    Returns:
        Current weather information as structured JSON text.
    """

    try:
        # Encode location for the URL
        encoded_location = quote(location)

        # wttr.in JSON API
        url = f"https://wttr.in/{encoded_location}?format=j1"

        request = Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        # Fetch weather data
        with urlopen(request, timeout=15) as response:
            data = json.loads(
                response.read().decode("utf-8")
            )

        # Current weather
        current = data["current_condition"][0]

        # Location information
        area = data.get("nearest_area", [{}])[0]

        area_name = area.get(
            "areaName",
            [{}]
        )[0].get("value", location)

        country = area.get(
            "country",
            [{}]
        )[0].get("value", "")
        
        # Create structured result
        result = {
            "location": f"{area_name}, {country}".strip(", "),
            "temperature_celsius": current.get("temp_C"),
            "feels_like_celsius": current.get("FeelsLikeC"),
            "condition": current.get(
                "weatherDesc",
                [{}]
            )[0].get("value"),
            "humidity_percent": current.get("humidity"),
            "wind_speed_kmph": current.get("windspeedKmph"),
            "wind_direction": current.get("winddir16Point"),
            "visibility_km": current.get("visibility"),
            "pressure_mb": current.get("pressure")
        }

        return json.dumps(
            result,
            indent=2
        )

    except Exception as e:

        return json.dumps(
            {
                "error": f"Could not fetch weather for {location}.",
                "details": str(e)
            },
            indent=2
        )


if __name__ == "__main__":
    server.run(transport="stdio")