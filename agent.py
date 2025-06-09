#!/usr/bin/env python3

import os
import json
import urllib.request
import urllib.parse

def call_claude(prompt):
    """Send prompt to Claude API and return response"""
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        raise Exception("ANTHROPIC_API_KEY environment variable not set")

    url = "https://api.anthropic.com/v1/messages"

    data = {
        "model": "claude-3-sonnet-20240229",
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": prompt}]
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
        return result["content"][0]["text"]

def main():
    print("Claude Coding Agent")
    print("Enter your prompt (or 'quit' to exit):")

    while True:
        user_input = input("> ")

        if user_input.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break

        try:
            response = call_claude(user_input)
            print(f"\nClaude: {response}\n")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
