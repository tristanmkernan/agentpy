#!/usr/bin/env python3

def main():
    print("Simple Echo Agent")
    print("Enter your prompt (or 'quit' to exit):")

    while True:
        user_input = input("> ")

        if user_input.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break

        print(f"You said: {user_input}")

if __name__ == "__main__":
    main()
