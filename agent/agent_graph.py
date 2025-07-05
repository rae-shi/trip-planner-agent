from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableLambda
from pydantic import BaseModel
import time
from dotenv import load_dotenv
from tools.tavily_tool import search_with_tavily
import os

load_dotenv()  # Load environment variables from .env file

llm = ChatOpenAI(model="gpt-4", temperature=0.7)

from tools.tavily_tool import search_with_tavily
from planner.trip_planner import plan_itinerary


class TripPlannerState(BaseModel):
    user_input: str
    user_preferences: dict = {}
    conversation_history: list = []
    current_plan: str = ""
    search_queries: list = []
    search_results: dict = {}
    final_output: str = ""
    output: str | None = None
    error_count: int = 0

def parse_daily_queries(content):
    daily_queries = {}
    for line in content.split('\n'):
        line = line.strip()
        if line.startswith('Day') and ':' in line:
            parts = line.split(':', 1)
            if len(parts) == 2:
                day = parts[0].strip()
                queries_str = parts[1].strip().strip('[]')
                queries = [q.strip().strip('"').strip("'") for q in queries_str.split(',') if q.strip()]
                daily_queries[day] = queries
    return daily_queries

def planner_node(state):
    try:
        print("[STEP 1/3] Creating your trip plan...")
        
        planning_prompt = f"""
        Create a detailed trip plan for: {state.user_input}

        Include:
        - Day-by-day itinerary
        - Specific attractions and places to visit
        - Recommended activities
        - Estimated costs
        - Best times to visit

        Format as a structured plan.
        """
        response = llm.invoke(planning_prompt)
        print("[SUCCESS] Trip plan created successfully!")
        return {"current_plan": response.content}
    except Exception as e:
        print(f"[ERROR] Planning error: {str(e)}")
        return {"error_count": state.error_count + 1, "output": f"Planning error: {str(e)}"}

def search_node(state):
    try:
        print("[STEP 2/3] Gathering real-time information...")
        
        daily_prompt = f"""
        Based on this trip plan: {state.current_plan}

        Generate 2-3 search queries for EACH DAY to get real-time information like:
        - Opening hours for attractions
        - Ticket prices and availability
        - Current weather conditions
        - Transportation options
        - Local events or activities

        Focus on official government, museum, and attraction websites. Be specific about the location and type of information needed. Format as:
        Day 1: [query1, query2, query3]
        Day 2: [query1, query2, query3]
        """
        daily_response = llm.invoke(daily_prompt)
        daily_queries = parse_daily_queries(daily_response.content)

        print(f"[SEARCH] Searching for real-time data across {sum(len(queries) for queries in daily_queries.values())} queries...")
        
        search_results = {}
        total_queries = sum(len(queries) for queries in daily_queries.values())
        current_query = 0
        
        for day, queries in daily_queries.items():
            day_results = {}
            for query in queries:
                current_query += 1
                print(f"   [QUERY {current_query}/{total_queries}] {query[:50]}...")
                
                result = search_with_tavily(query)
                day_results[query] = {
                    'info': result.get('answer', '') if isinstance(result, dict) else str(result),
                    'content': result.get('content', '') if isinstance(result, dict) else str(result),
                    'image': result.get('image', None) if isinstance(result, dict) else None
                }
                time.sleep(1)
            search_results[day] = day_results

        print("[SUCCESS] Real-time information gathered successfully!")
        return {"search_results": search_results}
    except Exception as e:
        print(f"[ERROR] Search error: {str(e)}")
        return {"error_count": state.error_count + 1, "output": f"Search error: {str(e)}"}

def final_synthesis_node(state):
    try:
        print("[STEP 3/3] Creating your final personalized plan...")
        
        synthesis_prompt = f"""
        You are a precise travel planner. Use the REAL data provided below to create specific, actionable recommendations.

        **Original Plan:**
        {state.current_plan}

        **Real-time Information (Use this EXACT data):**
        {state.search_results}

        **Your Task - Be SPECIFIC and ACTIONABLE:**
        1. **Weather Information:**
           - Use exact weather details if present
           - Recommend clothing accordingly

        2. **Attraction Information:**
           - Include opening hours and ticket prices if present
           - Mention image availability

        3. **Ticket Purchases:**
           - Provide the CORRECT official website URLs (do NOT use URLs from search results)
           - Generate from your own knowledge

        4. **Transportation:**
           - Include exact routes and times if found

        5. **Current Events:**
           - List events with details and prices if available

        **Format your response as:**
        Optimized Trip Plan, Real-time Insights, Practical Tips, Official Booking Links.
        """
        final_response = llm.invoke(synthesis_prompt)
        print("[SUCCESS] Final plan created successfully!")
        return {"final_output": final_response.content, "output": final_response.content}
    except Exception as e:
        print(f"[ERROR] Synthesis error: {str(e)}")
        return {"error_count": state.error_count + 1, "output": f"Synthesis error: {str(e)}"}

def run_trip_planner(user_input):
    builder = StateGraph(TripPlannerState)
    builder.add_node("PlanTrip", RunnableLambda(planner_node))
    builder.add_node("SearchInfo", RunnableLambda(search_node))
    builder.add_node("FinalSynthesis", RunnableLambda(final_synthesis_node))
    builder.set_entry_point("PlanTrip")
    builder.add_edge("PlanTrip", "SearchInfo")
    builder.add_edge("SearchInfo", "FinalSynthesis")
    builder.add_edge("FinalSynthesis", END)
    graph = builder.compile()
    
    print("\n[START] Starting Trip Planning Process...")
    result = graph.invoke({"user_input": user_input})
    print("\n[COMPLETE] Trip planning completed!")
    
    return result["output"]