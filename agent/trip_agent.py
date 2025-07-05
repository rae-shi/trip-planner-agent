from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, Tool
from langchain.memory import ConversationBufferMemory
from tools.tavily_tool import search_with_tavily
from planner.trip_planner import plan_itinerary
from dotenv import load_dotenv
import os

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def create_agent():
    llm = ChatOpenAI(model="gpt-4", temperature=0, api_key=OPENAI_API_KEY)
    tools = [
        Tool(name="WebSearch", func=search_with_tavily, description="Fetch real-time info from the web."),
        Tool(name="ItineraryPlanner", func=plan_itinerary, description="Generate structured trip plan.")
    ]
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    agent = initialize_agent(tools, llm, agent_type="zero-shot-react-description", memory=memory, verbose=True)
    return agent
