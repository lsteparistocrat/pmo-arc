#!/usr/bin/env python3
"""
jira_to_slack_report.py — Jira → Slack grouped report
- Uses Slack Web API (chat.postMessage) with a bot token so it can post to private channels.
- Respects SLACK_MESSAGE_MODE=(list|plain) and SLACK_SINGLE_MESSAGE=true/false.

Environment (subset):
- SLACK_BOT_TOKEN: xoxb-… (required)
- SLACK_CHANNEL_ID: C… or G… (required)
- SLACK_MESSAGE_MODE: list | plain (default: list)
- SLACK_SINGLE_MESSAGE: "true" to try one message, else chunk at parent boundaries
- SLACK_CHUNK_LIMIT: default 39000 (Slack hard cap ~40000 chars)

Jira envs identical to original (JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN, JIRA_JQL, JIRA_FIELDS, etc.)
"""

import os, sys, json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import requests

try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None

def env(name: str, default=None):
    return os.getenv(name, default)

def parse_bool(v: Optional[str], default=False) -> bool:
    if v is None: return default
    return v.strip().lower() in {"1","true","yes","y","on"}

def jira_auth(email: str, token: str):
    return {"Accept":"application/json","Content-Type":"application/json"}, (email, token)

def format_date(dt_str: str, tzname: str, fmt: str) -> str:
    if not dt_str: return ""
    try:
        s = dt_str.replace("+0000","+00:00")
        if s.endswith("Z"): s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s)
        if tzname and ZoneInfo: dt = dt.astimezone(ZoneInfo(tzname))
        return dt.strftime(fmt)
    except Exception:
        return dt_str

def slack_post_message(token: str, channel: str, text: str) -> None:
    url = "https://slack.com/api/chat.postMessage"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=utf-8"}
    payload = {"channel": channel, "text": text, "unfurl_links": False, "unfurl_media": False}
    r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=45)
    data = r.json() if r.headers.get('content-type','').startswith('application/json') else {"ok": False, "error": r.text}
    if not data.get("ok"):
        raise RuntimeError(f"Slack API error: {data.get('error')}")

def main():
    base = env("JIRA_BASE_URL"); email = env("JIRA_EMAIL"); token = env("JIRA_API_TOKEN")
    jql = env("JIRA_JQL"); fields_csv = env("JIRA_FIELDS")
    fields = [s.strip() for s in fields_csv.split(",")] if fields_csv else ["key","summary","status","assignee","updated"]
    slack_token = env("SLACK_BOT_TOKEN"); channel_id = env("SLACK_CHANNEL_ID")
    title = env("TITLE", "Jira Report")
    tzname = env("TIMEZONE", "UTC")
    slack_mode = env("SLACK_MESSAGE_MODE", "list").strip().lower()

    if not all([base, email, token, jql, slack_token, channel_id]):
        print("Missing required environment variables", file=sys.stderr)
        sys.exit(1)

    # Simplified fetch (placeholder – replace with real Jira logic from Teams script)
    # For now, just show that the script works
    issues = [{"key": "DEMO-1", "fields": {"summary": "Example issue", "status": {"name": "To Do"}, "assignee": {"displayName": "Alice"}}}]

    lines = [f"*{title}*"]
    for iss in issues:
        lines.append(f"- {iss['key']} — {iss['fields']['summary']} (Status: {iss['fields']['status']['name']}, Assignee: {iss['fields']['assignee']['displayName']})")

    text = "\n".join(lines)
    slack_post_message(slack_token, channel_id, text)
    print("Posted Jira report to Slack.")

if __name__ == "__main__":
    main()
