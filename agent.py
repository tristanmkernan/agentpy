#!/usr/bin/env python3

import os
import sys
import json
import urllib.request
import urllib.parse

class CodingAgent:
    def __init__(self, filename):
        self.conversation = []
        self.filename = filename

    def call_claude(self, prompt):
        """Send prompt to Claude API with conversation history"""
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise Exception("ANTHROPIC_API_KEY environment variable not set")

        # Add user message to conversation
        self.conversation.append({"role": "user", "content": prompt})

        url = "https://api.anthropic.com/v1/messages"

        data = {
            "model": "claude-3-sonnet-20240229",
            "max_tokens": 1024,
            "messages": self.conversation
        }

        headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01"
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8'),
            headers=headers
        )

        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            assistant_response = result["content"][0]["text"]

            # Add assistant response to conversation
            self.conversation.append({"role": "assistant", "content": assistant_response})

            return assistant_response

    def run(self):
        print(f"Claude Coding Agent - Working on: {self.filename}")
        print("Enter your prompt (or 'quit' to exit):")

        while True:
            user_input = input("> ")

            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break

            try:
                response = self.call_claude(user_input)
                print(f"\nClaude: {response}\n")
            except Exception as e:
                print(f"Error: {e}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 agent.py <filename>")
        sys.exit(1)

    filename = sys.argv[1]
    agent = CodingAgent(filename)
    agent.run()

if __name__ == "__main__":
    main()
