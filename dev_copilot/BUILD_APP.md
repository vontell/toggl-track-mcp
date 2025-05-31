# Task: Build an MCP server for Toggl Track

This is a spec for a simple MCP server for Toggle Track. The goal of the MCP
server is to allow Claude and other MCP clients to read and write to Toggl
Track to have better management of time tracking. Ideally I'd like to be able
to ask things like.

"How much time did I spent last week on social activities?"
"Did I spend at least 5 hours on the X task?"
"Start a new time entry for task X on project Y"

# Resources

You will want to reference the Toggl Track API docs: https://engineering.toggl.com/docs/
You may need to search for the relevant pages in the docs.

For building the MCP server, you may want to reference the following docs in the @dev_copilot/docs/MCPs.txt file.
You can find the Python-specific docs in the @dev_copilot/docs/MCP_Python.md file.

## Specification

The server should be written in Python.

You should start with a task that simply returns the list of projects I have in Toggl Track.

You should update the README.md with the details about the implementation, how to run and try it, and any other relevant information.
Use that README.md as a file that you can reference later to continue your work.
