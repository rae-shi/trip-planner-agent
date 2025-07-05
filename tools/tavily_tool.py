import requests
import os
from dotenv import load_dotenv

load_dotenv()

def search_with_tavily(query):
    API_KEY = os.getenv("TAVILY_API_KEY")
    if not API_KEY:
        return {"error": "TAVILY_API_KEY not found in environment variables"}
    
    url = "https://api.tavily.com/search"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    data = {
        "query": query,
        "include_answer": True,
        "search_depth": "advanced",
        "include_domains": [
            "*.gov", "*.org", "*.museum", "*.gallery",
            "*.theatre", "*.theater", "*.park", "*.zoo", "*.aquarium"
        ],
        "exclude_domains": [
            "tripadvisor.com", "yelp.com", "foursquare.com",
            "google.com", "facebook.com", "instagram.com",
            "twitter.com", "youtube.com", "wikipedia.org",
            "artsy-traveler.com", "whichmuseum.com", "ottawaembassy.com"
        ]
    }

    try:
        # Show a brief loading indicator for the search
        print("      [SEARCHING]...", end="", flush=True)
        
        res = requests.post(url, json=data, headers=headers)
        if res.status_code != 200:
            print(" [FAILED]")
            return {"error": f"Tavily API error: {res.status_code} - {res.text}"}

        response_data = res.json()
        print(" [DONE]")

        extracted_data = {
            "query": query,
            "answer": "",
            "content": "",
            "image": None
        }

        # Use the best result's content, without URL
        if response_data.get("results"):
            best_result = response_data["results"][0]
            extracted_data["content"] = best_result.get("content", "")

        # Use answer if provided
        if response_data.get("answer"):
            extracted_data["answer"] = response_data["answer"]
        else:
            extracted_data["answer"] = extracted_data["content"]

        # Optional image
        if response_data.get("images"):
            extracted_data["image"] = response_data["images"][0]

        return extracted_data

    except Exception as e:
        return {"error": f"Tavily search failed: {str(e)}"}
