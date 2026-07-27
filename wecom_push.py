"""
WeCom webhook push — sends text (markdown) and image to group robot.
"""

import json
import base64
import hashlib
import urllib.request
import urllib.error


def push_image(image_path, webhook_url):
    with open(image_path, "rb") as f:
        img_data = f.read()

    size_mb = len(img_data) / (1024 * 1024)
    if size_mb > 2:
        print(f"WARNING: image {size_mb:.1f}MB > 2MB limit")

    payload = {
        "msgtype": "image",
        "image": {
            "base64": base64.b64encode(img_data).decode("utf-8"),
            "md5": hashlib.md5(img_data).hexdigest(),
        },
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(webhook_url, data=data,
                                 headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            if result.get("errcode") == 0:
                print("OK: image pushed")
                return True
            print(f"ERROR: {result}")
            return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False


def push_text(text, webhook_url):
    payload = {"msgtype": "markdown", "markdown": {"content": text}}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(webhook_url, data=data,
                                 headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            if result.get("errcode") == 0:
                print("OK: text pushed")
                return True
            print(f"ERROR: {result}")
            return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False


def build_greeting(config):
    """Build three-paragraph morning greeting from card config."""
    parts = []
    date_str = config.get("date", "")
    weather = config.get("weather", {})
    summary = config.get("summary", "")

    if date_str:
        parts.append(f"{date_str} 早安")
    if weather.get("text"):
        parts.append(f"今日天气：{weather.get('city', '南宁')} {weather['text']}")
    if summary:
        parts.append(summary)

    return "\n\n".join(parts)
