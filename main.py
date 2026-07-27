#!/usr/bin/env python3
"""
Daily real estate knowledge card — cloud runner.
Runs on GitHub Actions (or any cloud scheduler).

Workflow:
  1. Get today's date + weekday
  2. Fetch Nanning weather
  3. Select topic from content bank (rotated daily)
  4. Generate card image
  5. Push greeting + card to WeCom group
"""

import os
import sys
import datetime
import json

# Add cloud dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from weather import get_weather
from content_bank import TOPICS, N
from card_gen import generate
from wecom_push import push_text, push_image, build_greeting


def main():
    # ── 1. Date ──────────────────────────────────────────────
    today = datetime.date.today()
    weekdays = ["一", "二", "三", "四", "五", "六", "日"]
    date_str = f"{today.year}年{today.month}月{today.day}日 周{weekdays[today.weekday()]}"
    print(f"Date: {date_str}")

    # ── 2. Weather ───────────────────────────────────────────
    weather = get_weather("Nanning")
    print(f"Weather: {weather['text']}")

    # ── 3. Content selection (rotated by day-of-year) ────────
    topic_index = (today.timetuple().tm_yday - 1) % N
    topic = dict(TOPICS[topic_index])  # copy
    topic["date"] = date_str
    topic["weather"] = weather
    topic["footer"] = "每日房产知识卡片"
    print(f"Topic [{topic_index+1}/{N}]: {topic['title']}")

    # ── 4. Generate card ─────────────────────────────────────
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    os.makedirs(output_dir, exist_ok=True)
    card_path = os.path.join(output_dir, "daily_card.png")

    generate(topic, card_path)
    print(f"Card saved: {card_path}")

    # ── 5. Push to WeCom ─────────────────────────────────────
    webhook_url = os.environ.get("WECOM_WEBHOOK_URL", "")
    if not webhook_url:
        print("ERROR: WECOM_WEBHOOK_URL environment variable not set!")
        sys.exit(1)

    greeting = build_greeting(topic)
    print(f"Greeting:\n{greeting}")

    ok_text = push_text(greeting, webhook_url)
    ok_img = push_image(card_path, webhook_url)

    if ok_text and ok_img:
        print("SUCCESS: Greeting + card pushed to WeCom.")
    else:
        print(f"Partial failure: text={ok_text}, image={ok_img}")
        sys.exit(1)


if __name__ == "__main__":
    main()
