#!/usr/bin/env python3

import os
import sys
import json
import random
import urllib.request
import urllib.parse
import time
import traceback
import subprocess
from datetime import datetime

MAX_TOKENS = 1024 * 10
MODEL = "claude-sonnet-4-20250514"

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

        try:
            with open(self.log_file, 'w') as f:
                json.dump(self.api_logs, f, indent=2)
        except Exception as e:
            print(f"Failed to write log: {e}")

    def get_file_contents(self):
        """Get current contents of the target file"""
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return f"File {self.filename} does not exist yet."
        except Exception as e:
            return f"Error reading {self.filename}: {str(e)}"

    def get_messages_with_file_context(self):
        """Get conversation messages with current file contents prepended"""
        file_contents = self.get_file_contents()

        system_message = {
            "role": "user",
            "content": f"""You are working on the file: {self.filename}

Current file contents:
```python
{file_contents}
```

When you suggest changes to the code, please use the write_file tool to update the entire file contents. Always provide complete, working code - never partial updates or diffs. The file should be ready to run after your changes."""
        }

        # Return system message + conversation history
        return [system_message] + self.conversation

    def get_tools_definition(self):
        """Get the tools definition for the API"""
        return [
            {
                "name": "write_file",
                "description": f"Write complete contents to {self.filename}. Always provide the entire file content, not partial updates.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "content": {"type": "string", "description": "Complete file contents to write"}
                    },
                    "required": ["content"]
                }
            },
            {
                "name": "read_file",
                "description": "Read the contents of a file",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "filepath": {"type": "string", "description": "Path to the file to read"}
                    },
                    "required": ["filepath"]
                }
            },
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
            },
            {
                "name": "run_script",
                "description": "Run a Python script and return the output. If no script_path is provided, runs the file being edited.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "script_path": {"type": "string", "description": "Path to the Python script to run (optional, defaults to the file being edited)"},
                        "args": {"type": "array", "items": {"type": "string"}, "description": "Command line arguments to pass to the script (optional)"}
                    }
                }
            }
        ]

    def write_file(self, content):
        """Tool: Write complete contents to the target file"""
        try:
            # Debug: log what we're about to write
            self.log_tool(f"write_file called with content length: {len(content)}")
            if self.verbose:
                print(f"[DEBUG] First 100 chars of content: {repr(content[:100])}")

            with open(self.filename, 'w', encoding='utf-8') as f:
                f.write(content)
            self.log_tool(f"write_file({self.filename}) -> {len(content)} characters written")
            return f"Successfully wrote {len(content)} characters to {self.filename}"
        except Exception as e:
            error_msg = f"Error writing to {self.filename}: {str(e)}"
            self.log_tool(error_msg)
            return error_msg

    def read_file(self, filepath):
        """Tool: Read contents of a file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            self.log_tool(f"read_file({filepath}) -> {len(content)} characters")
            return content
        except FileNotFoundError:
            error_msg = f"File not found: {filepath}"
            self.log_tool(error_msg)
            return error_msg
        except Exception as e:
            error_msg = f"Error reading file {filepath}: {str(e)}"
            self.log_tool(error_msg)
            return error_msg

    def generate_random_number(self, min_val=1, max_val=100):
        """Tool: Generate a random number between min_val and max_val"""
        result = random.randint(min_val, max_val)
        self.log_tool(f"generate_random_number({min_val}, {max_val}) -> {result}")
        return result

    def run_script(self, script_path=None, args=None):
        """Tool: Run a Python script and return the output"""
        # Use the target file if no script_path provided
        if script_path is None:
            script_path = self.filename
        
        # Default to empty args if none provided
        if args is None:
            args = []
        
        self.log_tool(f"run_script({script_path}, {args}) -> Starting execution")
        
        # Check if the script file exists
        if not os.path.exists(script_path):
            error_msg = f"Script file not found: {script_path}"
            self.log_tool(error_msg)
            return error_msg
        
        try:
            # Build the command
            cmd = [sys.executable, script_path] + args
            
            # Run the script with a timeout to prevent hanging
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,  # 30 second timeout
                cwd=os.path.dirname(os.path.abspath(script_path)) or '.'
            )
            
            # Format the output
            output_parts = []
            
            if result.stdout:
                output_parts.append(f"STDOUT:\n{result.stdout}")
            
            if result.stderr:
                output_parts.append(f"STDERR:\n{result.stderr}")
            
            output_parts.append(f"EXIT CODE: {result.returncode}")
            
            if result.returncode == 0:
                status = "SUCCESS"
            else:
                status = "FAILED"
            
            output_parts.insert(0, f"EXECUTION {status}")
            
            final_output = "\n".join(output_parts)
            
            self.log_tool(f"run_script({script_path}) -> Exit code: {result.returncode}")
            return final_output
            
        except subprocess.TimeoutExpired:
            error_msg = f"Script execution timed out after 30 seconds: {script_path}"
            self.log_tool(error_msg)
            return error_msg
        except FileNotFoundError:
            error_msg = f"Python interpreter not found. Make sure Python is installed and accessible."
            self.log_tool(error_msg)
            return error_msg
        except Exception as e:
            error_msg = f"Error running script {script_path}: {str(e)}"
            self.log_tool(error_msg)
            return error_msg

    def execute_tool(self, tool_name, parameters):
        """Execute a tool and return the result"""
        self.log_tool(f"Executing tool: {tool_name} with params: {parameters}")

        # Debug: log parameter details
        if self.verbose:
            print(f"[DEBUG] Tool parameters type: {type(parameters)}")
            print(f"[DEBUG] Tool parameters keys: {list(parameters.keys()) if isinstance(parameters, dict) else 'Not a dict'}")

        if tool_name == "write_file":
            content = parameters.get("content", "")
            return self.write_file(content)
        elif tool_name == "read_file":
            filepath = parameters.get("filepath", "")
            return self.read_file(filepath)
        elif tool_name == "generate_random_number":
            min_val = parameters.get("min_val", 1)
            max_val = parameters.get("max_val", 100)
            return self.generate_random_number(min_val, max_val)
        elif tool_name == "run_script":
            script_path = parameters.get("script_path")
            args = parameters.get("args", [])
            return self.run_script(script_path, args)
        else:
            raise Exception(f"Unknown tool: {tool_name}")

    def call_claude(self, prompt):
        """Send prompt to Claude API with conversation history and tools"""

        time.sleep(3)  # rate limit protection

        try:
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if not api_key:
                raise Exception("ANTHROPIC_API_KEY environment variable not set")

            # Add user message to conversation
            self.conversation.append({"role": "user", "content": prompt})

            url = "https://api.anthropic.com/v1/messages"

            data = {
                "model": MODEL,
                "max_tokens": MAX_TOKENS,
                "messages": self.get_messages_with_file_context(),
                "tools": self.get_tools_definition()
            }

            headers = {
                "Content-Type": "application/json",
                "x-api-key": "[REDACTED]",
                "anthropic-version": "2023-06-01"
            }

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
                self.log_api_call(log_request, result, "main")

                if self.verbose:
                    print(f"[DEBUG] Response content blocks: {len(result['content'])}")

                # Extract text content and tool calls from the response
                text_content = []
                tool_calls = []

                for content_block in result["content"]:
                    if content_block["type"] == "text":
                        text_content.append(content_block["text"])
                    elif content_block["type"] == "tool_use":
                        tool_calls.append(content_block)

                # Add assistant message with full content to conversation
                self.conversation.append({"role": "assistant", "content": result["content"]})

                # Collect all response parts
                response_parts = []
                
                # Add text content if any
                if text_content:
                    combined_text = "\n".join(text_content).strip()
                    if combined_text:
                        response_parts.append(combined_text)

                # Execute tool calls if any
                if tool_calls:
                    self.log_tool(f"Claude requested {len(tool_calls)} tool(s)")
                    
                    # For now, execute only the first tool call to keep things simple
                    # TODO: Could be enhanced to handle multiple tool calls
                    tool_call = tool_calls[0]
                    if len(tool_calls) > 1:
                        self.log_tool(f"Warning: Multiple tool calls detected, executing only the first one")
                    
                    tool_result = self.execute_tool(tool_call["name"], tool_call["input"])

                    # Add tool result to conversation
                    self.conversation.append({
                        "role": "user",
                        "content": [{
                            "type": "tool_result",
                            "tool_use_id": tool_call["id"],
                            "content": str(tool_result)
                        }]
                    })

                    # Get Claude's follow-up response after tool execution
                    follow_up_response = self.call_claude_continue()
                    if follow_up_response.strip():
                        response_parts.append(follow_up_response)

                # Return combined response
                if response_parts:
                    return "\n\n".join(response_parts)
                else:
                    return "Tool execution completed."

        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            print(f"HTTP Error {e.code}: {e.reason}")
            print(f"Response body: {error_body}")
            raise Exception(f"API Error {e.code}: {error_body}")
        except Exception as e:
            print(f"Exception in call_claude: {type(e).__name__}: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            raise

    def call_claude_continue(self):
        """Continue conversation after tool use"""
        time.sleep(3)  # rate limit protection

        try:
            api_key = os.getenv('ANTHROPIC_API_KEY')
            url = "https://api.anthropic.com/v1/messages"

            data = {
                "model": MODEL,
                "max_tokens": MAX_TOKENS,
                "messages": self.get_messages_with_file_context()
            }

            headers = {
                "Content-Type": "application/json",
                "x-api-key": "[REDACTED]",
                "anthropic-version": "2023-06-01"
            }

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
                self.log_api_call(log_request, result, "continue")

                if not result["content"]:
                    if self.verbose:
                        print("[DEBUG] Empty content in continue response")
                    return "Tool execution completed."

                text_parts = []
                for content_block in result["content"]:
                    if content_block["type"] == "text":
                        text_parts.append(content_block["text"])

                assistant_response = "\n".join(text_parts) if text_parts else "Tool execution completed."
                self.conversation.append({"role": "assistant", "content": result["content"]})
                return assistant_response

        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            print(f"HTTP Error {e.code}: {e.reason}")
            print(f"Response body: {error_body}")
            raise Exception(f"API Error {e.code}: {error_body}")
        except Exception as e:
            print(f"Exception in call_claude_continue: {type(e).__name__}: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            raise

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