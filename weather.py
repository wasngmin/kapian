"""
Weather fetcher — gets Nanning weather from wttr.in.
"""

import urllib.request
import urllib.error
import json


def get_weather(city="Nanning"):
    """Fetch weather for a city. Returns {icon, text, city} dict."""
    try:
        url = f"https://wttr.in/{city}?format=j1"
        req = urllib.request.Request(url, headers={"User-Agent": "curl/8.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        current = data.get("current_condition", [{}])[0]
        cond = current.get("lang_zh", [{}])[0].get("value", "")
        temp_c = current.get("temp_C", "")

        # Try to get today's forecast for temp range
        forecast = data.get("weather", [{}])[0]
        t_min = forecast.get("mintempC", "")
        t_max = forecast.get("maxtempC", "")

        text_parts = []
        if t_max and t_min:
            text_parts.append(f"{t_max}°~{t_min}°")
        elif temp_c:
            text_parts.append(f"{temp_c}°")
        if cond:
            text_parts.append(cond)

        return {
            "icon": cond,
            "text": " ".join(text_parts) if text_parts else "暂无数据",
            "city": "南宁",
        }
    except Exception as e:
        print(f"Weather fetch failed: {e}")
        return {"icon": "多云", "text": "暂无天气数据", "city": "南宁"}
