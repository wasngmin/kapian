#!/usr/bin/env python3
"""
Daily real estate knowledge card - cloud runner.
Runs on GitHub Actions (or any cloud scheduler).

Idempotent: checks if today's card has already been pushed successfully.
If so, skips to avoid duplicate pushes from multiple cron triggers.
"""

import os
import sys
import datetime
import requests

# Add cloud dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from weather import get_weather
from content_bank import TOPICS, N
from card_gen import generate
from wecom_push import push_text, push_image, build_greeting

REPO = "wasngmin/kapian"


def already_pushed_today():
    """Check if there's already a successful run today (excluding this run)."""
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("No GITHUB_TOKEN, skipping idempotency check")
        return False

    today = datetime.date.today().isoformat()
    current_run_id = os.environ.get("GITHUB_RUN_ID", "")

    url = "https://api.github.com/repos/{}/actions/runs".format(REPO)
    params = {"per_page": 20}
    headers = {
        "Authorization": "token {}".format(token),
        "Accept": "application/vnd.github+json",
    }

    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        runs = resp.json().get("workflow_runs", [])
        for run in runs:
            if str(run.get("id")) == current_run_id:
                continue
            if run.get("conclusion") == "success" and run["created_at"].startswith(today):
                print("Found existing successful run today: {} ({})".format(run["id"], run["created_at"]))
                return True
    except Exception as e:
        print("Warning: could not check runs: {}".format(e))

    return False


def main():
    # Idempotency check - skip if already pushed today
    if already_pushed_today():
        print("SKIP: Today's card has already been pushed successfully.")
        return

    # Step 1. Date
    today = datetime.date.today()
    weekdays = ["一", "二", "三", "四", "五", "六", "日"]
    date_str = "{}年{}月{}日 周{}".format(
        today.year, today.month, today.day, weekdays[today.weekday()]
    )
    print("Date: " + date_str)

    # Step 2. Weather
    weather = get_weather("Nanning")
    print("Weather: " + weather["text"])

    # Step 3. Content selection (rotated by day-of-year)
    topic_index = (today.timetuple().tm_yday - 1) % N
    topic = dict(TOPICS[topic_index])
    topic["date"] = date_str
    topic["weather"] = weather
    topic["footer"] = "每日房产知识卡片"
    print("Topic [{}/{}]: {}".format(topic_index + 1, N, topic["title"]))

    # Step 4. Generate card
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    os.makedirs(output_dir, exist_ok=True)
    card_path = os.path.join(output_dir, "daily_card.png")

    generate(topic, card_path)
    print("Card saved: " + card_path)

    # Step 5. Push to WeCom
    webhook_url = os.environ.get("WECOM_WEBHOOK_URL", "")
    if not webhook_url:
        print("ERROR: WECOM_WEBHOOK_URL environment variable not set!")
        sys.exit(1)

    greeting = build_greeting(topic)
    print("Greeting://n" + greeting)

    ok_text = push_text(greeting, webhook_url)
    ok_img = push_image(card_path, webhook_url)

    if ok_text and ok_img:
        print("SUCCESS: Greeting + card pushed to WeCom.")
    else:
        print("Partial failure: text={}, image={}".format(ok_text, ok_img))
        sys.exit(1)


if __name__ == "__main__":
    main()
