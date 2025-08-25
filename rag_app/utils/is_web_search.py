def should_use_web_search(query):
    """Determine if query should trigger web search"""
    web_indicators = [
        "latest",
        "recent",
        "current",
        "news",
        "today",
        "now",
        "what is happening",
        "updates",
        "breaking",
        "new",
        "search for",
        "find information about",
        "look up",
    ]
    query_lower = query.lower()
    return any(indicator in query_lower for indicator in web_indicators)
