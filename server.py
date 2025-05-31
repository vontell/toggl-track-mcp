#!/usr/bin/env python3
"""
Toggl Track MCP Server

An MCP server for interacting with Toggl Track API.
Provides tools for time tracking management.
"""

import os
import base64
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import aiohttp
import asyncio
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts import base

# Load environment variables from .env file
load_dotenv()

# Create the MCP server
mcp = FastMCP("Toggl Track")

# Toggl Track API configuration
TOGGL_API_BASE = "https://api.track.toggl.com/api/v9"


class TogglClient:
    """Client for interacting with Toggl Track API"""
    
    def __init__(self, api_token: str):
        self.api_token = api_token
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        # Encode the API token with base64 for Basic auth
        # Toggl API requires format: api_token:api_token
        auth_string = f"{self.api_token}:api_token"
        encoded_auth = base64.b64encode(auth_string.encode()).decode()
        
        self.session = aiohttp.ClientSession(
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Basic {encoded_auth}"
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_projects(self) -> List[Dict[str, Any]]:
        """Get all projects for the authenticated user"""
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")
        
        url = f"{TOGGL_API_BASE}/me/projects"
        async with self.session.get(url) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                raise Exception(f"Failed to get projects: {response.status} - {error_text}")
    
    async def get_workspaces(self) -> List[Dict[str, Any]]:
        """Get all workspaces for the authenticated user"""
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")
        
        url = f"{TOGGL_API_BASE}/workspaces"
        async with self.session.get(url) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                raise Exception(f"Failed to get workspaces: {response.status} - {error_text}")
    
    async def get_time_entries(self, start_date: Optional[str] = None, end_date: Optional[str] = None, 
                              project_ids: Optional[List[int]] = None) -> List[Dict[str, Any]]:
        """Get time entries for the authenticated user with optional filters
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format  
            project_ids: List of project IDs to filter by
        """
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")
        
        url = f"{TOGGL_API_BASE}/me/time_entries"
        params = {}
        
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
            
        async with self.session.get(url, params=params) as response:
            if response.status == 200:
                entries = await response.json()
                
                # Filter by project IDs if specified
                if project_ids:
                    entries = [entry for entry in entries if entry.get("project_id") in project_ids]
                
                return entries
            else:
                error_text = await response.text()
                raise Exception(f"Failed to get time entries: {response.status} - {error_text}")
    
    async def get_current_time_entry(self) -> Optional[Dict[str, Any]]:
        """Get the currently running time entry"""
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")
        
        url = f"{TOGGL_API_BASE}/me/time_entries/current"
        async with self.session.get(url) as response:
            if response.status == 200:
                result = await response.json()
                return result
            elif response.status == 404:
                return None  # No running entry
            else:
                error_text = await response.text()
                raise Exception(f"Failed to get current time entry: {response.status} - {error_text}")
    
    async def start_timer(self, workspace_id: int, description: str, project_id: Optional[int] = None) -> Dict[str, Any]:
        """Start a new timer
        
        Args:
            workspace_id: ID of the workspace
            description: Description for the time entry
            project_id: Optional project ID to assign the time entry to
        """
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")
        
        # Create time entry data
        now = datetime.utcnow().isoformat() + "Z"
        data = {
            "created_with": "Toggl Track MCP Server",
            "description": description,
            "workspace_id": workspace_id,
            "duration": -1,  # -1 indicates running timer
            "start": now,
            "stop": None,
            "tags": [],
            "billable": False
        }
        
        if project_id:
            data["project_id"] = project_id
        
        url = f"{TOGGL_API_BASE}/workspaces/{workspace_id}/time_entries"
        async with self.session.post(url, json=data) as response:
            if response.status in [200, 201]:
                return await response.json()
            else:
                error_text = await response.text()
                raise Exception(f"Failed to start timer: {response.status} - {error_text}")
    
    async def stop_timer(self, workspace_id: int, time_entry_id: int) -> Dict[str, Any]:
        """Stop a running timer
        
        Args:
            workspace_id: ID of the workspace
            time_entry_id: ID of the time entry to stop
        """
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")
        
        url = f"{TOGGL_API_BASE}/workspaces/{workspace_id}/time_entries/{time_entry_id}/stop"
        async with self.session.patch(url) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                raise Exception(f"Failed to stop timer: {response.status} - {error_text}")
    
    async def get_tasks(self, workspace_id: int, project_id: int) -> List[Dict[str, Any]]:
        """Get all tasks for a project
        
        Args:
            workspace_id: ID of the workspace
            project_id: ID of the project
        """
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")
        
        url = f"{TOGGL_API_BASE}/workspaces/{workspace_id}/projects/{project_id}/tasks"
        async with self.session.get(url) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                raise Exception(f"Failed to get tasks: {response.status} - {error_text}")
    
    async def create_task(self, workspace_id: int, project_id: int, name: str, 
                         estimated_seconds: Optional[int] = None, active: bool = True) -> Dict[str, Any]:
        """Create a new task for a project
        
        Args:
            workspace_id: ID of the workspace
            project_id: ID of the project
            name: Name of the task
            estimated_seconds: Estimated time in seconds (optional)
            active: Whether the task is active (default: True)
        """
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")
        
        data = {
            "name": name,
            "active": active
        }
        
        if estimated_seconds is not None:
            data["estimated_seconds"] = estimated_seconds
        
        url = f"{TOGGL_API_BASE}/workspaces/{workspace_id}/projects/{project_id}/tasks"
        async with self.session.post(url, json=data) as response:
            if response.status in [200, 201]:
                return await response.json()
            else:
                error_text = await response.text()
                raise Exception(f"Failed to create task: {response.status} - {error_text}")


def get_api_token() -> str:
    """Get Toggl API token from environment variable"""
    token = os.getenv("TOGGL_API_TOKEN")
    if not token:
        raise ValueError(
            "TOGGL_API_TOKEN environment variable is required. "
            "Get your API token from your Toggl Track profile settings."
        )
    return token


@mcp.tool()
async def get_projects() -> str:
    """
    Get all projects from Toggl Track.
    
    Returns a formatted list of projects with their details.
    """
    try:
        api_token = get_api_token()
        
        async with TogglClient(api_token) as client:
            projects = await client.get_projects()
            
            if not projects:
                return "No projects found in your Toggl Track account."
            
            # Format the projects for display
            result = "Your Toggl Track Projects:\n\n"
            for project in projects:
                name = project.get("name", "Unnamed Project")
                workspace_id = project.get("workspace_id", "Unknown")
                color = project.get("color", "No color")
                is_private = project.get("is_private", False)
                client_name = project.get("client", {}).get("name", "No client") if project.get("client") else "No client"
                
                result += f"• **{name}**\n"
                result += f"  - Workspace ID: {workspace_id}\n"
                result += f"  - Client: {client_name}\n"
                result += f"  - Color: {color}\n"
                result += f"  - Private: {'Yes' if is_private else 'No'}\n\n"
            
            return result
            
    except ValueError as e:
        return f"Configuration error: {str(e)}"
    except Exception as e:
        return f"Error fetching projects: {str(e)}"


@mcp.tool()
async def get_workspaces() -> str:
    """
    Get all workspaces from Toggl Track.
    
    Returns a formatted list of workspaces with their details.
    """
    try:
        api_token = get_api_token()
        
        async with TogglClient(api_token) as client:
            workspaces = await client.get_workspaces()
            
            if not workspaces:
                return "No workspaces found in your Toggl Track account."
            
            # Format the workspaces for display
            result = "Your Toggl Track Workspaces:\n\n"
            for workspace in workspaces:
                name = workspace.get("name", "Unnamed Workspace")
                workspace_id = workspace.get("id", "Unknown")
                
                result += f"• **{name}** (ID: {workspace_id})\n"
            
            return result
            
    except ValueError as e:
        return f"Configuration error: {str(e)}"
    except Exception as e:
        return f"Error fetching workspaces: {str(e)}"


@mcp.tool()
async def get_time_entries(start_date: str = "", end_date: str = "", project_name: str = "") -> str:
    """
    Get time entries from Toggl Track with optional filtering.
    
    Args:
        start_date: Start date in YYYY-MM-DD format (optional, defaults to last 7 days)
        end_date: End date in YYYY-MM-DD format (optional, defaults to today)
        project_name: Project name to filter by (optional)
    
    Returns a detailed list of time entries with descriptions and durations.
    """
    try:
        api_token = get_api_token()
        
        # Set default date range if not provided
        if not start_date and not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        elif not start_date:
            start_date = (datetime.strptime(end_date, "%Y-%m-%d") - timedelta(days=7)).strftime("%Y-%m-%d")
        elif not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        async with TogglClient(api_token) as client:
            # Get projects first to match project names to IDs
            projects = await client.get_projects()
            project_map = {p.get("name", ""): p.get("id") for p in projects}
            
            # Filter by project if specified
            project_ids = None
            if project_name:
                project_id = project_map.get(project_name)
                if project_id:
                    project_ids = [project_id]
                else:
                    return f"Project '{project_name}' not found. Available projects: {', '.join(project_map.keys())}"
            
            # Get time entries
            entries = await client.get_time_entries(start_date, end_date, project_ids)
            
            if not entries:
                date_range = f"from {start_date} to {end_date}"
                if project_name:
                    date_range += f" for project '{project_name}'"
                return f"No time entries found {date_range}."
            
            # Format the entries for display
            result = f"Time Entries ({start_date} to {end_date}):\n\n"
            
            # Group entries by date
            entries_by_date = {}
            for entry in entries:
                start_time = entry.get("start", "")
                date = start_time[:10] if start_time else "Unknown date"
                if date not in entries_by_date:
                    entries_by_date[date] = []
                entries_by_date[date].append(entry)
            
            # Sort dates
            for date in sorted(entries_by_date.keys()):
                result += f"**{date}**\n"
                daily_total = 0
                
                for entry in entries_by_date[date]:
                    description = entry.get("description", "No description")
                    duration = entry.get("duration", 0)
                    
                    # Convert duration from seconds to hours and minutes
                    if duration > 0:
                        hours = duration // 3600
                        minutes = (duration % 3600) // 60
                        duration_str = f"{hours}h {minutes}m"
                        daily_total += duration
                    else:
                        duration_str = "Running"
                    
                    # Get project name
                    project_id = entry.get("project_id")
                    project_name_display = "No project"
                    for project in projects:
                        if project.get("id") == project_id:
                            project_name_display = project.get("name", "Unknown project")
                            break
                    
                    start_time = entry.get("start", "")[:16].replace("T", " ") if entry.get("start") else ""
                    
                    result += f"  • {start_time} | {project_name_display} | {description} | {duration_str}\n"
                
                # Daily total
                if daily_total > 0:
                    total_hours = daily_total // 3600
                    total_minutes = (daily_total % 3600) // 60
                    result += f"  **Daily Total: {total_hours}h {total_minutes}m**\n"
                
                result += "\n"
            
            return result
            
    except ValueError as e:
        return f"Configuration error: {str(e)}"
    except Exception as e:
        return f"Error fetching time entries: {str(e)}"


@mcp.tool()
async def get_time_summary(start_date: str = "", end_date: str = "", project_name: str = "") -> str:
    """
    Get a summary of time worked with totals by project.
    
    Args:
        start_date: Start date in YYYY-MM-DD format (optional, defaults to last 7 days)
        end_date: End date in YYYY-MM-DD format (optional, defaults to today) 
        project_name: Project name to filter by (optional)
    
    Returns an aggregated summary of time worked by project.
    """
    try:
        api_token = get_api_token()
        
        # Set default date range if not provided
        if not start_date and not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        elif not start_date:
            start_date = (datetime.strptime(end_date, "%Y-%m-%d") - timedelta(days=7)).strftime("%Y-%m-%d")
        elif not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        async with TogglClient(api_token) as client:
            # Get projects first
            projects = await client.get_projects()
            project_map = {p.get("id"): p.get("name", "Unknown") for p in projects}
            
            # Filter by project if specified
            project_ids = None
            if project_name:
                project_id_match = None
                for p in projects:
                    if p.get("name") == project_name:
                        project_id_match = p.get("id")
                        break
                        
                if project_id_match:
                    project_ids = [project_id_match]
                else:
                    return f"Project '{project_name}' not found. Available projects: {', '.join([p.get('name', '') for p in projects])}"
            
            # Get time entries
            entries = await client.get_time_entries(start_date, end_date, project_ids)
            
            if not entries:
                date_range = f"from {start_date} to {end_date}"
                if project_name:
                    date_range += f" for project '{project_name}'"
                return f"No time entries found {date_range}."
            
            # Aggregate by project
            project_totals = {}
            grand_total = 0
            
            for entry in entries:
                project_id = entry.get("project_id")
                duration = entry.get("duration", 0)
                
                if duration > 0:  # Only count completed entries
                    project_name_display = project_map.get(project_id, "No project")
                    
                    if project_name_display not in project_totals:
                        project_totals[project_name_display] = 0
                    
                    project_totals[project_name_display] += duration
                    grand_total += duration
            
            # Format the summary
            result = f"Time Summary ({start_date} to {end_date}):\n\n"
            
            # Sort projects by time spent (descending)
            sorted_projects = sorted(project_totals.items(), key=lambda x: x[1], reverse=True)
            
            for project_name_display, total_seconds in sorted_projects:
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                percentage = (total_seconds / grand_total * 100) if grand_total > 0 else 0
                
                result += f"• **{project_name_display}**: {hours}h {minutes}m ({percentage:.1f}%)\n"
            
            # Grand total
            total_hours = grand_total // 3600
            total_minutes = (grand_total % 3600) // 60
            result += f"\n**Total Time: {total_hours}h {total_minutes}m**\n"
            
            return result
            
    except ValueError as e:
        return f"Configuration error: {str(e)}"
    except Exception as e:
        return f"Error generating time summary: {str(e)}"


@mcp.tool()
async def get_current_timer() -> str:
    """
    Get information about the currently running timer, if any.
    
    Returns details about the active time entry or indicates no timer is running.
    """
    try:
        api_token = get_api_token()
        
        async with TogglClient(api_token) as client:
            current_entry = await client.get_current_time_entry()
            
            if not current_entry:
                return "No timer is currently running."
            
            description = current_entry.get("description", "No description")
            start_time = current_entry.get("start", "")
            
            # Get project name
            project_id = current_entry.get("project_id")
            project_name = "No project"
            
            if project_id:
                projects = await client.get_projects()
                for project in projects:
                    if project.get("id") == project_id:
                        project_name = project.get("name", "Unknown project")
                        break
            
            # Calculate duration
            if start_time:
                start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                now = datetime.now(start_dt.tzinfo)
                duration = now - start_dt
                
                hours = int(duration.total_seconds() // 3600)
                minutes = int((duration.total_seconds() % 3600) // 60)
                duration_str = f"{hours}h {minutes}m"
            else:
                duration_str = "Unknown duration"
            
            result = f"**Currently Running Timer:**\n\n"
            result += f"• **Project**: {project_name}\n"
            result += f"• **Description**: {description}\n"
            result += f"• **Duration**: {duration_str}\n"
            result += f"• **Started**: {start_time[:16].replace('T', ' ') if start_time else 'Unknown'}\n"
            
            return result
            
    except ValueError as e:
        return f"Configuration error: {str(e)}"
    except Exception as e:
        return f"Error fetching current timer: {str(e)}"


@mcp.tool()
async def start_timer(description: str, project_name: str = "") -> str:
    """
    Start a new timer in Toggl Track.
    
    Args:
        description: Description for the time entry
        project_name: Name of the project to assign the timer to (optional)
    
    Returns confirmation of timer start with details.
    """
    try:
        api_token = get_api_token()
        
        async with TogglClient(api_token) as client:
            # Get workspaces to find the primary one
            workspaces = await client.get_workspaces()
            if not workspaces:
                return "No workspaces found. Cannot start timer."
            
            # Use the first workspace (most users have one)
            workspace_id = workspaces[0].get("id")
            workspace_name = workspaces[0].get("name", "Unknown")
            
            # Get project ID if project name specified
            project_id = None
            if project_name:
                projects = await client.get_projects()
                for project in projects:
                    if project.get("name") == project_name:
                        project_id = project.get("id")
                        break
                
                if not project_id:
                    available_projects = [p.get("name", "") for p in projects]
                    return f"Project '{project_name}' not found. Available projects: {', '.join(available_projects)}"
            
            # Start the timer
            result = await client.start_timer(workspace_id, description, project_id)
            
            # Format response
            timer_id = result.get("id")
            start_time = result.get("start", "")[:16].replace("T", " ") if result.get("start") else ""
            
            response = f"**Timer Started Successfully!**\n\n"
            response += f"• **Description**: {description}\n"
            response += f"• **Project**: {project_name if project_name else 'No project'}\n"
            response += f"• **Workspace**: {workspace_name}\n"
            response += f"• **Started**: {start_time}\n"
            response += f"• **Timer ID**: {timer_id}\n"
            
            return response
            
    except ValueError as e:
        return f"Configuration error: {str(e)}"
    except Exception as e:
        return f"Error starting timer: {str(e)}"


@mcp.tool()
async def stop_current_timer() -> str:
    """
    Stop the currently running timer in Toggl Track.
    
    Returns confirmation of timer stop with duration details.
    """
    try:
        api_token = get_api_token()
        
        async with TogglClient(api_token) as client:
            # Get current running timer
            current_entry = await client.get_current_time_entry()
            
            if not current_entry:
                return "No timer is currently running."
            
            # Get workspace info
            workspaces = await client.get_workspaces()
            workspace_id = None
            workspace_name = "Unknown"
            
            entry_workspace_id = current_entry.get("workspace_id")
            for workspace in workspaces:
                if workspace.get("id") == entry_workspace_id:
                    workspace_id = entry_workspace_id
                    workspace_name = workspace.get("name", "Unknown")
                    break
            
            if not workspace_id:
                return "Could not determine workspace for current timer."
            
            # Stop the timer
            time_entry_id = current_entry.get("id")
            result = await client.stop_timer(workspace_id, time_entry_id)
            
            # Calculate duration
            description = current_entry.get("description", "No description")
            start_time = current_entry.get("start", "")
            stop_time = result.get("stop", "")
            duration = result.get("duration", 0)
            
            if duration > 0:
                hours = duration // 3600
                minutes = (duration % 3600) // 60
                duration_str = f"{hours}h {minutes}m"
            else:
                duration_str = "Unknown duration"
            
            # Get project name
            project_id = current_entry.get("project_id")
            project_name = "No project"
            if project_id:
                projects = await client.get_projects()
                for project in projects:
                    if project.get("id") == project_id:
                        project_name = project.get("name", "Unknown project")
                        break
            
            response = f"**Timer Stopped Successfully!**\n\n"
            response += f"• **Description**: {description}\n"
            response += f"• **Project**: {project_name}\n"
            response += f"• **Duration**: {duration_str}\n"
            response += f"• **Started**: {start_time[:16].replace('T', ' ') if start_time else 'Unknown'}\n"
            response += f"• **Stopped**: {stop_time[:16].replace('T', ' ') if stop_time else 'Unknown'}\n"
            
            return response
            
    except ValueError as e:
        return f"Configuration error: {str(e)}"
    except Exception as e:
        return f"Error stopping timer: {str(e)}"


@mcp.tool()
async def search_time_entries(query: str, start_date: str = "", end_date: str = "") -> str:
    """
    Search time entries by description text with optional date filtering.
    
    Args:
        query: Text to search for in entry descriptions (case-insensitive)
        start_date: Start date in YYYY-MM-DD format (optional, defaults to last 30 days)
        end_date: End date in YYYY-MM-DD format (optional, defaults to today)
    
    Returns time entries matching the search query.
    """
    try:
        api_token = get_api_token()
        
        # Set default date range if not provided (last 30 days for search)
        if not start_date and not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        elif not start_date:
            start_date = (datetime.strptime(end_date, "%Y-%m-%d") - timedelta(days=30)).strftime("%Y-%m-%d")
        elif not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        async with TogglClient(api_token) as client:
            # Get projects for display names
            projects = await client.get_projects()
            project_map = {p.get("id"): p.get("name", "Unknown") for p in projects}
            
            # Get time entries
            entries = await client.get_time_entries(start_date, end_date)
            
            if not entries:
                return f"No time entries found from {start_date} to {end_date}."
            
            # Filter entries by description query (case-insensitive)
            matching_entries = []
            query_lower = query.lower()
            
            for entry in entries:
                description = entry.get("description", "").lower()
                if query_lower in description:
                    matching_entries.append(entry)
            
            if not matching_entries:
                return f"No time entries found matching '{query}' from {start_date} to {end_date}."
            
            # Format the matching entries
            result = f"Time Entries matching '{query}' ({start_date} to {end_date}):\n\n"
            
            # Group entries by date
            entries_by_date = {}
            for entry in matching_entries:
                start_time = entry.get("start", "")
                date = start_time[:10] if start_time else "Unknown date"
                if date not in entries_by_date:
                    entries_by_date[date] = []
                entries_by_date[date].append(entry)
            
            total_matching_time = 0
            
            # Sort dates and display
            for date in sorted(entries_by_date.keys()):
                result += f"**{date}**\n"
                daily_total = 0
                
                for entry in entries_by_date[date]:
                    description = entry.get("description", "No description")
                    duration = entry.get("duration", 0)
                    
                    # Convert duration from seconds to hours and minutes
                    if duration > 0:
                        hours = duration // 3600
                        minutes = (duration % 3600) // 60
                        duration_str = f"{hours}h {minutes}m"
                        daily_total += duration
                        total_matching_time += duration
                    else:
                        duration_str = "Running"
                    
                    # Get project name
                    project_id = entry.get("project_id")
                    project_name = project_map.get(project_id, "No project")
                    
                    start_time = entry.get("start", "")[:16].replace("T", " ") if entry.get("start") else ""
                    
                    result += f"  • {start_time} | {project_name} | {description} | {duration_str}\n"
                
                # Daily total for matching entries
                if daily_total > 0:
                    daily_hours = daily_total // 3600
                    daily_minutes = (daily_total % 3600) // 60
                    result += f"  **Daily Total: {daily_hours}h {daily_minutes}m**\n"
                
                result += "\n"
            
            # Overall total for matching entries
            if total_matching_time > 0:
                total_hours = total_matching_time // 3600
                total_minutes = (total_matching_time % 3600) // 60
                result += f"**Total Time for '{query}': {total_hours}h {total_minutes}m**\n"
            
            return result
            
    except ValueError as e:
        return f"Configuration error: {str(e)}"
    except Exception as e:
        return f"Error searching time entries: {str(e)}"


@mcp.tool()
async def get_time_entries_fixed(start_date: str = "", end_date: str = "", project_name: str = "") -> str:
    """
    Get time entries from Toggl Track with improved date handling.
    
    Args:
        start_date: Start date in YYYY-MM-DD format (optional, defaults to last 7 days)
        end_date: End date in YYYY-MM-DD format (optional, defaults to today)
        project_name: Project name to filter by (optional)
    
    Returns a detailed list of time entries with descriptions and durations.
    This version handles single-day queries better than get_time_entries.
    """
    try:
        api_token = get_api_token()
        
        # Set default date range if not provided
        if not start_date and not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        elif not start_date:
            start_date = (datetime.strptime(end_date, "%Y-%m-%d") - timedelta(days=7)).strftime("%Y-%m-%d")
        elif not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        # Store original dates for display
        original_start = start_date
        original_end = end_date
        
        # Handle single-day queries by expanding the range for API call
        if start_date == end_date:
            # Query a wider range and filter results later
            api_start_date = (datetime.strptime(start_date, "%Y-%m-%d") - timedelta(days=2)).strftime("%Y-%m-%d")
            api_end_date = (datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=2)).strftime("%Y-%m-%d")
            single_day_filter = start_date
        else:
            api_start_date = start_date
            api_end_date = end_date
            single_day_filter = None
        
        async with TogglClient(api_token) as client:
            # Get projects first to match project names to IDs
            projects = await client.get_projects()
            project_map = {p.get("name", ""): p.get("id") for p in projects}
            
            # Filter by project if specified
            project_ids = None
            if project_name:
                project_id = project_map.get(project_name)
                if project_id:
                    project_ids = [project_id]
                else:
                    return f"Project '{project_name}' not found. Available projects: {', '.join(project_map.keys())}"
            
            # Get time entries using potentially expanded date range
            entries = await client.get_time_entries(api_start_date, api_end_date, project_ids)
            
            # Filter to the requested date range
            if single_day_filter:
                entries = [entry for entry in entries if entry.get("start", "")[:10] == single_day_filter]
            elif original_start != api_start_date or original_end != api_end_date:
                # Filter to original date range if we expanded it
                entries = [entry for entry in entries 
                          if original_start <= entry.get("start", "")[:10] <= original_end]
            
            if not entries:
                date_range = f"from {original_start} to {original_end}"
                if project_name:
                    date_range += f" for project '{project_name}'"
                return f"No time entries found {date_range}."
            
            # Format the entries for display
            result = f"Time Entries ({original_start} to {original_end}):\n\n"
            
            # Group entries by date
            entries_by_date = {}
            for entry in entries:
                start_time = entry.get("start", "")
                date = start_time[:10] if start_time else "Unknown date"
                if date not in entries_by_date:
                    entries_by_date[date] = []
                entries_by_date[date].append(entry)
            
            # Sort dates
            for date in sorted(entries_by_date.keys()):
                result += f"**{date}**\n"
                daily_total = 0
                
                for entry in entries_by_date[date]:
                    description = entry.get("description", "No description")
                    duration = entry.get("duration", 0)
                    
                    # Convert duration from seconds to hours and minutes
                    if duration > 0:
                        hours = duration // 3600
                        minutes = (duration % 3600) // 60
                        duration_str = f"{hours}h {minutes}m"
                        daily_total += duration
                    else:
                        duration_str = "Running"
                    
                    # Get project name
                    project_id = entry.get("project_id")
                    project_name_display = "No project"
                    for project in projects:
                        if project.get("id") == project_id:
                            project_name_display = project.get("name", "Unknown project")
                            break
                    
                    start_time = entry.get("start", "")[:16].replace("T", " ") if entry.get("start") else ""
                    
                    result += f"  • {start_time} | {project_name_display} | {description} | {duration_str}\n"
                
                # Daily total
                if daily_total > 0:
                    total_hours = daily_total // 3600
                    total_minutes = (daily_total % 3600) // 60
                    result += f"  **Daily Total: {total_hours}h {total_minutes}m**\n"
                
                result += "\n"
            
            return result
            
    except ValueError as e:
        return f"Configuration error: {str(e)}"
    except Exception as e:
        return f"Error fetching time entries: {str(e)}"


@mcp.tool()
async def get_project_tasks(project_name: str) -> str:
    """
    Get all tasks for a specific project.
    
    Args:
        project_name: Name of the project to get tasks for
    
    Returns list of tasks with their details.
    """
    try:
        api_token = get_api_token()
        
        async with TogglClient(api_token) as client:
            # Get workspaces and projects
            workspaces = await client.get_workspaces()
            projects = await client.get_projects()
            
            if not workspaces:
                return "No workspaces found."
            
            # Find the project
            project_id = None
            project_found = None
            for project in projects:
                if project.get("name") == project_name:
                    project_id = project.get("id")
                    project_found = project
                    break
            
            if not project_id:
                available_projects = [p.get("name", "") for p in projects]
                return f"Project '{project_name}' not found. Available projects: {', '.join(available_projects)}"
            
            # Get workspace ID for the project
            workspace_id = project_found.get("workspace_id")
            if not workspace_id:
                return f"Could not determine workspace for project '{project_name}'."
            
            # Get tasks for the project
            tasks = await client.get_tasks(workspace_id, project_id)
            
            if not tasks:
                return f"No tasks found for project '{project_name}'."
            
            # Format the tasks
            result = f"Tasks for project '{project_name}':\n\n"
            
            for task in tasks:
                name = task.get("name", "Unnamed Task")
                task_id = task.get("id", "Unknown")
                active = task.get("active", True)
                estimated_seconds = task.get("estimated_seconds")
                
                status = "Active" if active else "Inactive"
                
                result += f"• **{name}** (ID: {task_id})\n"
                result += f"  - Status: {status}\n"
                
                if estimated_seconds:
                    hours = estimated_seconds // 3600
                    minutes = (estimated_seconds % 3600) // 60
                    result += f"  - Estimated: {hours}h {minutes}m\n"
                
                result += "\n"
            
            return result
            
    except ValueError as e:
        return f"Configuration error: {str(e)}"
    except Exception as e:
        return f"Error fetching tasks: {str(e)}"


@mcp.tool()
async def create_project_task(project_name: str, task_name: str, estimated_hours: float = 0) -> str:
    """
    Create a new task for a specific project.
    
    Args:
        project_name: Name of the project to create the task in
        task_name: Name of the new task
        estimated_hours: Estimated hours for the task (optional)
    
    Returns confirmation of task creation.
    """
    try:
        api_token = get_api_token()
        
        async with TogglClient(api_token) as client:
            # Get workspaces and projects
            workspaces = await client.get_workspaces()
            projects = await client.get_projects()
            
            if not workspaces:
                return "No workspaces found."
            
            # Find the project
            project_id = None
            project_found = None
            for project in projects:
                if project.get("name") == project_name:
                    project_id = project.get("id")
                    project_found = project
                    break
            
            if not project_id:
                available_projects = [p.get("name", "") for p in projects]
                return f"Project '{project_name}' not found. Available projects: {', '.join(available_projects)}"
            
            # Get workspace ID for the project
            workspace_id = project_found.get("workspace_id")
            if not workspace_id:
                return f"Could not determine workspace for project '{project_name}'."
            
            # Convert estimated hours to seconds
            estimated_seconds = None
            if estimated_hours > 0:
                estimated_seconds = int(estimated_hours * 3600)
            
            # Create the task
            result = await client.create_task(workspace_id, project_id, task_name, estimated_seconds)
            
            # Format response
            task_id = result.get("id")
            active = result.get("active", True)
            status = "Active" if active else "Inactive"
            
            response = f"**Task Created Successfully!**\n\n"
            response += f"• **Task Name**: {task_name}\n"
            response += f"• **Project**: {project_name}\n"
            response += f"• **Task ID**: {task_id}\n"
            response += f"• **Status**: {status}\n"
            
            if estimated_hours > 0:
                response += f"• **Estimated Time**: {estimated_hours}h\n"
            
            return response
            
    except ValueError as e:
        return f"Configuration error: {str(e)}"
    except Exception as e:
        return f"Error creating task: {str(e)}"


@mcp.tool()
async def get_all_tasks() -> str:
    """
    Get all tasks across all projects in the workspace.
    
    Returns a comprehensive list of all tasks organized by project.
    """
    try:
        api_token = get_api_token()
        
        async with TogglClient(api_token) as client:
            # Get workspaces and projects
            workspaces = await client.get_workspaces()
            projects = await client.get_projects()
            
            if not workspaces:
                return "No workspaces found."
            
            if not projects:
                return "No projects found."
            
            # Group projects by workspace for organization
            workspace_map = {ws.get("id"): ws.get("name", "Unknown") for ws in workspaces}
            
            result = "All Tasks Across Projects:\n\n"
            total_tasks = 0
            
            for project in projects:
                project_name = project.get("name", "Unnamed Project")
                project_id = project.get("id")
                workspace_id = project.get("workspace_id")
                
                if not project_id or not workspace_id:
                    continue
                
                try:
                    # Get tasks for this project
                    tasks = await client.get_tasks(workspace_id, project_id)
                    
                    if tasks:
                        # Add project header
                        result += f"**{project_name}** ({workspace_map.get(workspace_id, 'Unknown Workspace')})\n"
                        
                        for task in tasks:
                            name = task.get("name", "Unnamed Task")
                            task_id = task.get("id", "Unknown")
                            active = task.get("active", True)
                            estimated_seconds = task.get("estimated_seconds")
                            
                            status = "Active" if active else "Inactive"
                            
                            result += f"  • **{name}** (ID: {task_id})\n"
                            result += f"    - Status: {status}\n"
                            
                            if estimated_seconds:
                                hours = estimated_seconds // 3600
                                minutes = (estimated_seconds % 3600) // 60
                                result += f"    - Estimated: {hours}h {minutes}m\n"
                            
                            total_tasks += 1
                        
                        result += "\n"
                        
                except Exception as e:
                    # Skip projects that can't be accessed (might not have tasks enabled)
                    continue
            
            if total_tasks == 0:
                return "No tasks found across any projects."
            
            result += f"**Total Tasks Found: {total_tasks}**\n"
            
            return result
            
    except ValueError as e:
        return f"Configuration error: {str(e)}"
    except Exception as e:
        return f"Error fetching all tasks: {str(e)}"


@mcp.prompt()
def start_time_tracking(project_name: str, description: str = "") -> str:
    """Generate a prompt to start time tracking for a project"""
    prompt = f"I want to start tracking time for the project '{project_name}'"
    if description:
        prompt += f" with the description '{description}'"
    prompt += ". Please help me start a new time entry using my Toggl Track account."
    return prompt


@mcp.prompt()
def weekly_time_report() -> str:
    """Generate a prompt to request a weekly time report"""
    return "Please generate a weekly time report showing my time entries, total hours worked, and project breakdown for this week using my Toggl Track data."


@mcp.prompt()
def project_time_analysis(project_name: str) -> list[base.Message]:
    """Generate a structured conversation for project time analysis"""
    return [
        base.UserMessage(f"I need to analyze my time tracking for the project '{project_name}'"),
        base.AssistantMessage("I'll help you analyze your time tracking data. Let me first get your projects and recent time entries for this project."),
        base.UserMessage("Please show me the total hours, daily breakdown, and any patterns in my work schedule for this project.")
    ]


@mcp.prompt()
def optimize_workflow() -> str:
    """Generate a prompt for workflow optimization based on time tracking data"""
    return "Based on my Toggl Track time tracking data, please analyze my work patterns and suggest ways to optimize my workflow and improve productivity."


@mcp.prompt()
def project_overview() -> str:
    """Generate a prompt to get an overview of all projects"""
    return "Please show me all my Toggl Track projects and workspaces, organized in a clear format with project details and current status."


@mcp.prompt()
def detailed_time_report(start_date: str, end_date: str = "", project_name: str = "") -> str:
    """Generate a prompt to get detailed time entries for analysis"""
    prompt = f"Please show me detailed time entries from {start_date}"
    if end_date:
        prompt += f" to {end_date}"
    if project_name:
        prompt += f" for project '{project_name}'"
    prompt += ". Include descriptions, durations, and daily breakdowns."
    return prompt


@mcp.prompt()
def time_summary_report(days: str = "7", project_name: str = "") -> str:
    """Generate a prompt to get a time summary with project totals"""
    prompt = f"Please give me a time summary for the last {days} days"
    if project_name:
        prompt += f" for project '{project_name}'"
    prompt += ". Show total hours by project with percentages."
    return prompt


@mcp.prompt()
def productivity_analysis(period: str = "week") -> list[base.Message]:
    """Generate a structured conversation for productivity analysis"""
    return [
        base.UserMessage(f"I want to analyze my productivity for this {period}"),
        base.AssistantMessage("I'll help you analyze your productivity patterns. Let me get your time tracking data and current timer status."),
        base.UserMessage("Please show me my time distribution, most productive periods, and suggest improvements.")
    ]


@mcp.prompt()
def current_status_check() -> str:
    """Generate a prompt to check current timer and recent activity"""
    return "Please check my current timer status and show me what I've been working on today."


@mcp.prompt()
def project_deep_dive(project_name: str, days: str = "30") -> str:
    """Generate a prompt for in-depth project analysis"""
    return f"Please provide a detailed analysis of my work on '{project_name}' over the last {days} days. Include time patterns, task descriptions, and productivity insights."


@mcp.prompt()
def search_by_description(query: str, days: str = "30") -> str:
    """Generate a prompt to search time entries by description"""
    return f"Please search my time entries for '{query}' over the last {days} days and show me the total time spent on related activities."


@mcp.prompt()
def quick_start_timer(description: str, project_name: str = "") -> str:
    """Generate a prompt to quickly start a timer"""
    prompt = f"Please start a timer with description '{description}'"
    if project_name:
        prompt += f" for project '{project_name}'"
    prompt += ". Confirm when the timer has started."
    return prompt


@mcp.prompt()
def stop_and_start_new(new_description: str, project_name: str = "") -> str:
    """Generate a prompt to stop current timer and start a new one"""
    prompt = f"Please stop my current timer and start a new one with description '{new_description}'"
    if project_name:
        prompt += f" for project '{project_name}'"
    prompt += ". Show me the duration of the stopped timer and confirm the new timer has started."
    return prompt


@mcp.prompt()
def timer_status_and_control() -> str:
    """Generate a prompt to check timer status and offer controls"""
    return "Please check my current timer status. If I have a timer running, show me the details and ask if I want to stop it. If no timer is running, ask if I want to start one."


@mcp.prompt()
def work_session_timer(project_name: str, duration: str = "1 hour") -> str:
    """Generate a prompt to start a focused work session timer"""
    return f"I want to start a focused {duration} work session on '{project_name}'. Please start a timer and remind me to take breaks."


@mcp.prompt()
def view_project_tasks(project_name: str) -> str:
    """Generate a prompt to view all tasks for a project"""
    return f"Please show me all tasks for the project '{project_name}' with their current status and estimated time."


@mcp.prompt()
def create_new_task(project_name: str, task_name: str, estimated_hours: str = "") -> str:
    """Generate a prompt to create a new task"""
    prompt = f"Please create a new task called '{task_name}' for project '{project_name}'"
    if estimated_hours:
        prompt += f" with an estimated time of {estimated_hours} hours"
    prompt += ". Confirm when the task has been created."
    return prompt


@mcp.prompt()
def task_planning_session(project_name: str) -> str:
    """Generate a prompt for planning tasks for a project"""
    return f"I want to plan out tasks for the project '{project_name}'. Please show me existing tasks and help me create new ones based on the project requirements."


@mcp.prompt()
def project_task_overview() -> str:
    """Generate a prompt for a comprehensive task overview across projects"""
    return "Please give me an overview of tasks across all my projects. Show me which projects have tasks, what needs attention, and help me prioritize my work."


@mcp.prompt()
def list_all_tasks() -> str:
    """Generate a prompt to list all tasks across all projects"""
    return "Please show me all tasks across all my projects, organized by project. Include task status and estimated time for each task."


if __name__ == "__main__":
    # This allows the server to be run directly for testing
    print("Running server...")
    mcp.run()