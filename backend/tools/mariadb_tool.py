import subprocess
import shutil
import os
from langchain.agents import Tool

class MariaDBTool:
    def __init__(self):
        """Initialize the MariaDB tool with mariadb path."""
        # Ensure we have the full system PATH
        if os.name == 'nt':  # Windows
            paths = os.environ.get('PATH', '').split(';')
        else:  # Unix-like
            paths = os.environ.get('PATH', '').split(':')
            
        # Update environment for subprocess calls
        self.env = os.environ.copy()
        
        # Find mariadb in PATH
        self.mariadb_path = shutil.which('mariadb', path=os.environ.get('PATH'))
        if not self.mariadb_path:
            raise RuntimeError("MariaDB CLI not found in PATH. Please ensure MariaDB is installed and added to your system PATH.")
            
        # Handle paths with spaces for all platforms
        if ' ' in self.mariadb_path:
            self.mariadb_path = f'"{self.mariadb_path}"'

    def execute_command(self, command: str) -> str:
        """Execute a MariaDB command and return the output."""
        try:
            # Use list form to avoid shell injection and handle spaces in paths
            result = subprocess.run(
                [self.mariadb_path, '-e', command],
                capture_output=True,
                text=True,
                check=True,
                shell=False,  # Avoid shell to handle spaces better
                env=self.env  # Use the full environment
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            return f"Error executing MariaDB command: {e.stderr}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"

def get_mariadb_tool() -> Tool:
    """Create and return a MariaDB Tool for use with LangGraph."""
    tool = MariaDBTool()
    return Tool(
        name="MariaDB Tool",
        func=tool.execute_command,
        description="Executes MariaDB CLI commands to manage MariaDB databases. Common commands: SHOW DATABASES, USE [db], SHOW TABLES, SELECT * FROM [table]"
    ) 