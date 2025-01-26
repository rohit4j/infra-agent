import subprocess
import shutil
import os
from langchain.agents import Tool

class KongGatewayTool:
    def __init__(self):
        """Initialize the Kong Gateway tool with kong path."""
        # Find kong in PATH
        self.kong_path = shutil.which('kong')
        if not self.kong_path:
            raise RuntimeError("kong not found in PATH")
        
        # Convert Windows path to raw string to handle spaces
        if os.name == 'nt':  # Windows
            self.kong_path = f'"{self.kong_path}"'

    def execute_command(self, command: str) -> str:
        """Execute a Kong Gateway command and return the output."""
        try:
            # Use list form to avoid shell injection and handle spaces in paths
            cmd_parts = command.split()
            if os.name == 'nt':  # Windows
                result = subprocess.run(
                    [self.kong_path.strip('"')] + cmd_parts,
                    capture_output=True,
                    text=True,
                    check=True,
                    shell=False  # Avoid shell to handle spaces better
                )
            else:  # Unix-like
                result = subprocess.run(
                    [self.kong_path] + cmd_parts,
                    capture_output=True,
                    text=True,
                    check=True,
                    shell=False
                )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            return f"Error executing Kong CLI command: {e.stderr}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"

def get_kong_gateway_tool() -> Tool:
    """Create and return a Kong Gateway Tool for use with LangGraph."""
    tool = KongGatewayTool()
    return Tool(
        name="Kong Gateway Tool",
        func=tool.execute_command,
        description="Executes Kong CLI commands to manage Kong Gateway. Common commands: status, health, config, migrations, services list, routes list"
    ) 