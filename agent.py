#!/usr/bin/env python3

import os
import sys
import json
import random
import urllib.request
import urllib.parse

class CodingAgent:
    def __init__(self, filename):
        self.conversation = []
        self.filename = filename

    def generate_random_number(self, min_val=1, max_val=100):
        """Tool: Generate a random number between min_val and max_val"""
        return random.randint(min_val, max_val)

    def execute_tool(self, tool_name, parameters):
        """Execute a tool and return the result"""
        if tool_name == "generate_random_number":
            min_val = parameters.get("min_val", 1)
            max_val = parameters.get("max_val", 100)
            return self.generate_random_number(min_val, max_val)
        else:
            raise Exception(f"Unknown tool: {tool_name}")

    def call_claude(self, prompt):
        """Send prompt to Claude API with conversation history and tools"""
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise Exception("ANTHROPIC_API_KEY environment variable not set")

        # Add user message to conversation
        self.conversation.append({"role": "user", "content": prompt})

        url = "https://api.anthropic.com/v1/messages"

        tools = [
            {
                "name": "generate_random_number",
                "description": "Generate a random number between min_val and max_val",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "min_val": {"type": "integer", "description": "Minimum value (default: 1)"},
                        "max_val": {"type": "integer", "description": "Maximum value (default: 100)"}
                    }
                }
            }
        ]

        data = {
            "model": "claude-3-sonnet-20240229",
            "max_tokens": 1024,
            "messages": self.conversation,
            "tools": tools
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

            # Handle tool use
            if result["content"][0]["type"] == "tool_use":
                tool_call = result["content"][0]
                tool_name = tool_call["name"]
                tool_params = tool_call["input"]
                tool_id = tool_call["id"]

                # Execute tool
                tool_result = self.execute_tool(tool_name, tool_params)

                # Add assistant message with tool use
                self.conversation.append({"role": "assistant", "content": result["content"]})

                # Add tool result
                self.conversation.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": str(tool_result)
                        }
                    ]
                })

                # Make another API call to get final response
                return self.call_claude_continue()
            else:
                assistant_response = result["content"][0]["text"]
                self.conversation.append({"role": "assistant", "content": assistant_response})
                return assistant_response

    def call_claude_continue(self):
        """Continue conversation after tool use"""
        api_key = os.getenv('ANTHROPIC_API_KEY')
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
