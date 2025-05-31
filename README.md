# Toggl Track MCP Server

A Model Context Protocol (MCP) server for Toggl Track time tracking integration. This server allows Claude and other MCP clients to interact with your Toggl Track account to manage projects and time entries.

## Features

- **Get Projects**: Retrieve all projects from your Toggl Track account
- **Get Workspaces**: List all workspaces associated with your account
- **Get Time Entries**: Detailed time entries with filtering by date range and project
- **Time Summary**: Aggregated time reports by project with percentages
- **Current Timer**: Check what's currently running and elapsed time
- **Smart Prompts**: Pre-built conversation starters for common time tracking queries
- Secure API token authentication
- Formatted, readable output for LLM consumption

## Quick Start

### 1. Installation

Create a virtual environment (recommended):

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: venv\Scripts\activate
```

Install the required dependencies:

```bash
pip install -r requirements.txt
```

### 2. Configuration

Get your Toggl Track API token:

1. Go to your [Toggl Track profile settings](https://track.toggl.com/profile)
2. Copy your API token from the "API Token" section

Set your API token as an environment variable:

```bash
export TOGGL_API_TOKEN="your_api_token_here"
```

Or create a `.env` file (copy from `.env.example`):

```bash
cp .env.example .env
# Edit .env file with your API token
```

### 3. Running the Server

#### Development Mode (with MCP Inspector)

```bash
mcp dev server.py
```

This opens the MCP Inspector for testing your server interactively.

#### Install in Claude Desktop

```bash
mcp install server.py
```

#### Direct Execution

```bash
python server.py
```

## Available Tools

### `get_projects`

Retrieves all projects from your Toggl Track account with details including:

- Project name
- Workspace ID
- Associated client
- Color coding
- Privacy settings

### `get_workspaces`

Lists all workspaces associated with your Toggl Track account with:

- Workspace name
- Workspace ID

### `get_time_entries`

Get detailed time entries with optional filtering:

- **start_date**: Filter by start date (YYYY-MM-DD format, defaults to 7 days ago)
- **end_date**: Filter by end date (YYYY-MM-DD format, defaults to today)
- **project_name**: Filter by specific project name
- Shows entries grouped by date with descriptions, durations, and daily totals

### `get_time_summary`

Get aggregated time summary by project:

- **start_date**: Start date for summary (defaults to 7 days ago)
- **end_date**: End date for summary (defaults to today)
- **project_name**: Focus on specific project (optional)
- Shows total hours by project with percentages and grand total

### `get_current_timer`

Check currently running timer:

- Shows active project and description
- Displays elapsed time and start time
- Returns "No timer running" if nothing is active

## Example Prompts

The server includes pre-built prompts for common scenarios:

- **detailed_time_report**: Get detailed breakdown of time entries
- **time_summary_report**: Get aggregated time summary by project
- **productivity_analysis**: Analyze work patterns and productivity
- **current_status_check**: Check current timer and today's activity
- **project_deep_dive**: In-depth analysis of specific project work

## Example Usage

Once installed in Claude Desktop, you can ask:

- "What projects do I have in Toggl Track?"
- "Show me my Toggl workspaces"
- "List all my time tracking projects"
- "Show me my time entries for the last week"
- "What did I work on yesterday?"
- "Give me a time summary for project X"
- "How much time did I spend on each project this month?"
- "What's my current timer status?"

## API Reference

This server uses the [Toggl Track API v9](https://developers.track.toggl.com/docs/). Key endpoints used:

- `GET /api/v9/me/projects` - Get user projects
- `GET /api/v9/workspaces` - Get user workspaces

## Development

### Project Structure

```
toggl-track-mcp/
├── server.py              # Main MCP server implementation
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variable template
└── README.md             # This file
```

### Adding New Features

To extend this server with additional Toggl Track functionality:

1. Add new methods to the `TogglClient` class
2. Create new `@mcp.tool()` decorated functions
3. Handle authentication and error cases
4. Update this README with the new capabilities

## Authentication

This server uses Toggl Track's API token authentication method. The token should be provided via the `TOGGL_API_TOKEN` environment variable.

**Security Note**: Never commit your API token to version control. Always use environment variables or secure configuration management.

## Error Handling

The server includes comprehensive error handling for:

- Missing API token configuration
- Network connectivity issues
- API authentication failures
- Malformed API responses

## Rate Limiting

Toggl Track API has rate limiting (approximately 1 request per second). The server respects these limits and provides appropriate error messages if limits are exceeded.

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is open source and available under standard terms.
