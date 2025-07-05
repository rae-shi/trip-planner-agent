from agent.trip_agent import create_agent

if __name__ == "__main__":
    agent = create_agent()
    while True:
        user_input = input("User: ")
        if user_input.lower() in ["exit", "quit"]:
            break
        response = agent.run(user_input)
        print("Agent:", response)
