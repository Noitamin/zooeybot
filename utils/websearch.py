"""Bounded Tavily basic search, using the existing requests dependency."""

from urllib.parse import urlsplit

import requests

from utils.settings import TAVILY_API_KEY


class SearchError(Exception):
    """An error safe to show in Discord."""


def search_web(query):
    if not TAVILY_API_KEY:
        raise SearchError("Web search isn't configured. Set TAVILY_API_KEY in .env and restart the bot.")
    try:
        response = requests.post(
            "https://api.tavily.com/search",
            headers={"Authorization": f"Bearer {TAVILY_API_KEY}"},
            json={
                "query": query,
                "search_depth": "basic",
                "auto_parameters": False,
                "max_results": 5,
                "include_answer": False,
                "include_raw_content": False,
            },
            timeout=(5, 25),
        )
        if response.status_code == 401:
            raise SearchError("The Tavily API key is invalid. Ask the bot owner to check it.")
        if response.status_code in (429, 432, 433):
            raise SearchError("Web search has reached its rate or usage limit. Try again later.")
        response.raise_for_status()
        data = response.json()
        results = []
        for item in data["results"][:5]:
            url = item.get("url", "")
            parsed = urlsplit(url)
            if parsed.scheme not in ("http", "https") or not parsed.netloc:
                continue
            if len(url) > 1500 or any(char.isspace() or char in "<>" for char in url):
                continue
            results.append({
                "title": str(item.get("title", ""))[:200],
                "url": url,
                "content": str(item.get("content", ""))[:2000],
            })
        return results
    except requests.Timeout:
        raise SearchError("Web search timed out. Try again shortly.") from None
    except (requests.RequestException, ValueError, KeyError, TypeError, AttributeError):
        raise SearchError("Web search is unavailable right now. Try again later.") from None
