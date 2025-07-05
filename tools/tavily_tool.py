import requests

def search_with_tavily(query):
    API_KEY = "YOUR_TAVILY_API_KEY"
    url = "https://api.tavily.com/search"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    data = {
        "query": query,
        "include_answer": True,
        "search_depth": "advanced"
    }
    try:
        res = requests.post(url, json=data, headers=headers)
        res.raise_for_status()
        return res.json().get("answer", "No answer found.")
    except Exception as e:
        return f"Tavily search failed: {str(e)}"
