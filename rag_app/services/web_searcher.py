import json
import requests
from datetime import datetime
import hashlib
from rag_app.config import SERPAPI_KEY

WEB_CACHE_PATH = "web_search_cache.json"

# Load web search cache
try:
    with open(WEB_CACHE_PATH, "r") as f:
        web_cache = json.load(f)
except FileNotFoundError:
    web_cache = {}


class WebSearcher:
    """Handle web search operations"""

    def __init__(self):
        self.serpapi_key = SERPAPI_KEY

    def search_serpapi(self, query, num_results=5):
        """Search using SerpAPI (Google Search)"""
        if not self.serpapi_key:
            return []

        params = {
            "q": query,
            "api_key": self.serpapi_key,
            "num": num_results,
            "engine": "google",
        }

        try:
            response = requests.get("https://serpapi.com/search", params=params)
            results = response.json()

            search_results = []
            for result in results.get("organic_results", []):
                search_results.append(
                    {
                        "title": result.get("title", ""),
                        "url": result.get("link", ""),
                        "snippet": result.get("snippet", ""),
                        "source": "serpapi",
                    }
                )
            return search_results
        except Exception as e:
            print(f"SerpAPI search error: {e}")
            return []

    def search(self, query, num_results=5):
        """Primary search method - tries SerpAPI first, then DuckDuckGo"""
        # Check cache first
        cache_key = hashlib.md5(f"{query}_{num_results}".encode()).hexdigest()
        if cache_key in web_cache:
            cached_result = web_cache[cache_key]
            if (
                datetime.now() - datetime.fromisoformat(cached_result["timestamp"])
            ).days < 1:
                return cached_result["results"]

        # Try SerpAPI first
        results = self.search_serpapi(query, num_results)

        # Cache results
        web_cache[cache_key] = {
            "results": results,
            "timestamp": datetime.now().isoformat(),
        }
        self._save_cache()

        return results

    def _save_cache(self):
        """Save web search cache to file"""
        try:
            with open(WEB_CACHE_PATH, "w") as f:
                json.dump(web_cache, f, indent=2)
        except Exception as e:
            print(f"Error saving web cache: {e}")
