from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableLambda
from pydantic import BaseModel
import time

# Initialize the LLM
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
    output: str | None = None
    error_count: int = 0

def planner_node(state):
    try:
        query = state.user_input
        plan = plan_itinerary(query)
        
        # Use LLM to generate intelligent search queries
        prompt = f"""
        Based on this trip plan: {plan}
        Generate ONLY 3-5 most important search queries to get real-time information like:
        - Opening hours
        - Ticket prices
        - Current events
        - Weather conditions
        - Transportation options
        
        Return only the search queries, one per line. MAXIMUM 5 queries.
        """
        response = llm.invoke(prompt)
        search_queries = [line.strip() for line in response.content.split('\n') if line.strip()][:5]  # Limit to 5
        return {"current_plan": plan, "search_queries": search_queries if search_queries else ["No search queries generated"] }
    except Exception as e:
        return {"error_count": state.error_count + 1, "output": f"Planning error: {str(e)}"}

def search_node(state):
    try:
        search_results = {}
        for i, query in enumerate(state.search_queries):
            result = search_with_tavily(query)
            search_results[query] = result
        
        # Add delay between requests to avoid rate limiting
        if i < len(state.search_queries) - 1:  # Don't delay after last request
            time.sleep(1)  # Wait 1 second between requests
        
        # Format the final output nicely
        final_output = f"""
        **Trip Plan:**
        {state.current_plan}
        
        **Real-time Information:**
        """
        for query, result in search_results.items():
            final_output += f"\n**{query}:**\n{result}\n"
        
        return {"search_results": search_results, "output": final_output if final_output else "No search results generated"}
    except Exception as e:
        return {"error_count": state.error_count + 1, "output": f"Search error: {str(e)}"}

def tool_orchestrator_node(state):
    plan = state.current_plan
    search_results = {}
    
    for place in plan.get('places', []):
        if place.get('needs_info'):
            search_query = f"{place['name']} opening hours ticket price"
            search_results[place['name']] = search_with_tavily(search_query)
    
    return {"search_results": search_results}

def run_trip_planner(user_input):
    builder = StateGraph(TripPlannerState)
    builder.add_node("PlanTrip", RunnableLambda(planner_node))
    builder.add_node("SearchInfo", RunnableLambda(search_node))

    builder.set_entry_point("PlanTrip")
    builder.add_edge("PlanTrip", "SearchInfo")
    builder.add_edge("SearchInfo", END)

    graph = builder.compile()
    result = graph.invoke({"user_input": user_input})
    return result["output"]
