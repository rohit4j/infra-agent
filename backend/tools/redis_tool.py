import subprocess
import json
import shutil
import os
from langchain.agents import Tool

class RedisTool:
    def __init__(self):
        """Initialize the Redis tool with redis-cli path."""
        # Find redis-cli in PATH
        self.redis_cli_path = shutil.which('redis-cli')
        if not self.redis_cli_path:
            raise RuntimeError("redis-cli not found in PATH")
        
        # Convert Windows path to raw string to handle spaces
        if os.name == 'nt':  # Windows
            self.redis_cli_path = f'"{self.redis_cli_path}"'

    def execute_command(self, command: str) -> str:
        """Execute a redis-cli command and return the output."""
        try:
            # Use list form to avoid shell injection and handle spaces in paths
            cmd_parts = command.split()
            if os.name == 'nt':  # Windows
                result = subprocess.run(
                    [self.redis_cli_path.strip('"')] + cmd_parts,
                    capture_output=True,
                    text=True,
                    check=True,
                    shell=False  # Avoid shell to handle spaces better
                )
            else:  # Unix-like
                result = subprocess.run(
                    [self.redis_cli_path] + cmd_parts,
                    capture_output=True,
                    text=True,
                    check=True,
                    shell=False
                )
            # Attempt to parse JSON output if applicable
            try:
                json_output = json.loads(result.stdout)
                return json.dumps(json_output, indent=2)
            except json.JSONDecodeError:
                return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            return f"Error executing redis-cli command: {e.stderr}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"

def get_redis_tool() -> Tool:
    """Create and return a Redis Tool for use with LangGraph."""
    tool = RedisTool()
    return Tool(
        name="Redis Tool",
        func=tool.execute_command,
        description="Executes redis-cli commands to manage Redis servers. Common commands: info, keys *, get [key], set [key] [value], monitor"
    ) 