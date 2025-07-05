from agent.agent_graph import run_trip_planner

if __name__ == "__main__":
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            break
        response = run_trip_planner(user_input)
        print("Agent:", response)
