from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableLambda
from pydantic import BaseModel


from tools.tavily_tool import search_with_tavily
from planner.trip_planner import plan_itinerary


class TripPlannerState(BaseModel):
    user_input: str
    user_preferences: dict = {}
    conversation_history: list = []
    current_plan: dict = {}
    search_results: dict = {}
    output: str = None
    error_count: int = 0

def planner_node(state):
    query = state.user_input
    return {"output": plan_itinerary(query)}

def search_node(state):
    query = state.user_input
    return {"output": search_with_tavily(query)}

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
