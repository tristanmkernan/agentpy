# Agentpy

A simple Python-based coding agent that uses Claude's API to help you edit and modify Python files through natural language conversations.

(Note from the human): this was created entirely by Claude, first via chat and then once bootstrapped self editing 🤖

## Features

- **Conversational Interface**: Chat with Claude about your code through a terminal interface
- **File Context**: Agent always has access to the current state of your target file
- **Tool Integration**: Claude can read files, write complete file updates, and generate random numbers
- **Conversation Memory**: Maintains context across the entire session
- **API Logging**: All API requests and responses are logged to JSON for debugging

## Requirements

- Python 3.6+
- Anthropic API key (configured via environment variable)
- No external dependencies (uses only Python standard library)

## Setup

1. Get an Anthropic API key from https://console.anthropic.com/
2. Set your API key as an environment variable:
   ```bash
   export ANTHROPIC_API_KEY="your-api-key-here"
   ```
   (Or use direnv/other environment management tools)

## Usage

```bash
python3 agent.py <filename> [-v|--verbose]
```

- `<filename>`: The Python file you want to work on (will be created if it doesn't exist)
- `-v` or `--verbose`: Enable verbose logging for debugging tool usage

### Example Session

```bash
$ python3 agent.py hello.py
Claude Coding Agent - Working on: hello.py
API logs will be saved to: hello.py.log.json
Enter your prompt (or 'quit' to exit):
> Create a simple hello world program

Claude: I'll create a simple hello world program for you.

[Tool executes: write_file]

> Add a function that takes a name parameter and greets that person

Claude: I'll modify the program to include a greeting function.

[Tool executes: write_file]

> quit
Goodbye!
```

## How It Works

1. **File Context**: The agent reads the current contents of your target file before each conversation
2. **Natural Language**: You describe what you want to change in plain English
3. **Complete Rewrites**: When Claude suggests changes, it rewrites the entire file (no partial updates)
4. **Tool Execution**: Claude can use tools to read other files, write to your target file, or generate random numbers

## Available Tools

- `write_file`: Write complete contents to the target file
- `read_file`: Read contents from any file
- `generate_random_number`: Generate random numbers (useful for testing)

## Files Created

- `<filename>`: Your target Python file
- `<filename>.log.json`: Complete API request/response log for debugging

## Rate Limiting

The agent includes built-in delays to respect Anthropic's API rate limits. If you encounter rate limit errors, the agent will wait between API calls.

## Limitations

- Single file focus (designed for simple Python programs)
- No syntax validation (relies on Claude's understanding)
- No version control integration
- Limited to tools defined in the agent

## Development

The agent is designed to be simple and hackable. You can:
- Add new tools by extending the `execute_tool` method
- Modify the system prompt in `get_messages_with_file_context`
- Adjust API parameters like model and token limits
- Extend logging and debugging capabilities

## Troubleshooting

- **Empty file writes**: Usually indicates Claude's response was truncated due to token limits
- **Rate limit errors**: The agent includes automatic delays, but you may need to wait if you hit limits
- **API errors**: Check the `.log.json` file for detailed request/response information
- **Tool failures**: Run with `-v` flag to see detailed tool execution logs
