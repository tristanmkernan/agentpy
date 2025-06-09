#!/usr/bin/env python3

import os
import sys
import json
import random
import urllib.request
import urllib.parse
from datetime import datetime

class CodingAgent:
    def __init__(self, filename, verbose=False):
        self.conversation = []
        self.filename = filename
        self.verbose = verbose
        self.log_file = f"{filename}.log.json"
        self.api_logs = []

    def log_tool(self, message):
        """Log tool-related activity"""
        if self.verbose:
            print(f"[TOOL] {message}")

    def log_api_call(self, request_data, response_data, call_type="main"):
        """Log API request and response to JSON file"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "call_type": call_type,
            "request": request_data,
            "response": response_data
        }
        self.api_logs.append(log_entry)

        # Write to file immediately
        try:
            with open(self.log_file, 'w') as f:
                json.dump(self.api_logs, f, indent=2)
        except Exception as e:
            print(f"Failed to write log: {e}")

    def generate_random_number(self, min_val=1, max_val=100):
        """Tool: Generate a random number between min_val and max_val"""
        result = random.randint(min_val, max_val)
        self.log_tool(f"generate_random_number({min_val}, {max_val}) -> {result}")
        return result

    def execute_tool(self, tool_name, parameters):
        """Execute a tool and return the result"""
        self.log_tool(f"Executing tool: {tool_name} with params: {parameters}")

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
            "x-api-key": "[REDACTED]",  # For logging
            "anthropic-version": "2023-06-01"
        }

        # Prepare request for logging (without real API key)
        log_request = {
            "url": url,
            "headers": headers,
            "data": data
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8'),
            headers={**headers, "x-api-key": api_key}  # Use real key for actual request
        )

        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))

            # Log this API call
            self.log_api_call(log_request, result, "main")

            if self.verbose:
                print(f"[DEBUG] Response type: {result['content'][0]['type']}")

            # Look for tool use in any content block
            tool_calls = []
            text_content = []

            for content_block in result["content"]:
                if content_block["type"] == "text":
                    text_content.append(content_block["text"])
                elif content_block["type"] == "tool_use":
                    tool_calls.append(content_block)

            # Add assistant message with full content
            self.conversation.append({"role": "assistant", "content": result["content"]})

            if tool_calls:
                self.log_tool(f"Claude requested {len(tool_calls)} tool(s)")

                # Execute all tool calls and collect results
                tool_results = []
                for tool_call in tool_calls:
                    tool_result = self.execute_tool(tool_call["name"], tool_call["input"])
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_call["id"],
                        "content": str(tool_result)
                    })

                # Add tool results
                self.conversation.append({"role": "user", "content": tool_results})

                # Continue conversation
                return self.call_claude_continue()
            else:
                # Just text response
                return "\n".join(text_content)

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
            "x-api-key": "[REDACTED]",
            "anthropic-version": "2023-06-01"
        }

        # Prepare request for logging
        log_request = {
            "url": url,
            "headers": headers,
            "data": data
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8'),
            headers={**headers, "x-api-key": api_key}
        )

        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))

            # Log this API call
            self.log_api_call(log_request, result, "continue")

            # Handle empty content array
            if not result["content"]:
                if self.verbose:
                    print("[DEBUG] Empty content in continue response")
                return "Tool execution completed."

            # Extract text from content blocks
            text_parts = []
            for content_block in result["content"]:
                if content_block["type"] == "text":
                    text_parts.append(content_block["text"])

            assistant_response = "\n".join(text_parts) if text_parts else "Tool execution completed."
            self.conversation.append({"role": "assistant", "content": result["content"]})
            return assistant_response

    def run(self):
        print(f"Claude Coding Agent - Working on: {self.filename}")
        print(f"API logs will be saved to: {self.log_file}")
        if self.verbose:
            print("Verbose mode enabled - tool logging active")
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
    if len(sys.argv) < 2:
        print("Usage: python3 agent.py <filename> [-v|--verbose]")
        sys.exit(1)

    filename = sys.argv[1]
    verbose = len(sys.argv) > 2 and sys.argv[2] in ['-v', '--verbose']

    agent = CodingAgent(filename, verbose)
    agent.run()

if __name__ == "__main__":
    main()
