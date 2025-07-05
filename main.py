from agent.agent_graph import run_trip_planner
import sys
import time
import threading

def print_loading_animation(message, stop_event):
    """Print a loading animation with dots"""
    animation = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    i = 0
    while not stop_event.is_set():
        sys.stdout.write(f"\r{message} {animation[i % len(animation)]}")
        sys.stdout.flush()
        time.sleep(0.1)
        i += 1
    sys.stdout.write("\r" + " " * (len(message) + 2) + "\r")  # Clear the line
    sys.stdout.flush()

def print_progress(message):
    """Print a progress message"""
    print(f"\n[PROGRESS] {message}")

if __name__ == "__main__":
    print("Welcome to the Trip Planner Agent!")
    print("Enter your trip request and I'll create a detailed plan with real-time information.")
    print("Type 'exit' or 'quit' to end the session.\n")
    
    while True:
        user_input = input("Please enter your trip plan: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Thank you for using the Trip Planner! Goodbye!")
            break
        
        # Start loading animation
        stop_loading = threading.Event()
        loading_thread = threading.Thread(
            target=print_loading_animation, 
            args=("Agent is planning your trip", stop_loading)
        )
        loading_thread.start()
        
        try:
            response = run_trip_planner(user_input)
            stop_loading.set()
            loading_thread.join()
            
            print("\n" + "="*60)
            print("YOUR PERSONALIZED TRIP PLAN")
            print("="*60)
            print(response)
            print("="*60 + "\n")
            
        except Exception as e:
            stop_loading.set()
            loading_thread.join()
            print(f"\n[ERROR] {str(e)}")
            print("Please try again with a different request.\n")
