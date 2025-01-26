import subprocess
import shutil
import os
from langchain.agents import Tool

class MySQLTool:
    def __init__(self):
        """Initialize the MySQL tool with mysql path."""
        # Find mysql in PATH
        self.mysql_path = shutil.which('mysql')
        if not self.mysql_path:
            raise RuntimeError("mysql not found in PATH")
        
        # Convert Windows path to raw string to handle spaces
        if os.name == 'nt':  # Windows
            self.mysql_path = f'"{self.mysql_path}"'

    def execute_command(self, command: str) -> str:
        """Execute a MySQL command and return the output."""
        try:
            # Use list form to avoid shell injection and handle spaces in paths
            if os.name == 'nt':  # Windows
                result = subprocess.run(
                    [self.mysql_path.strip('"'), '-e', command],
                    capture_output=True,
                    text=True,
                    check=True,
                    shell=False  # Avoid shell to handle spaces better
                )
            else:  # Unix-like
                result = subprocess.run(
                    [self.mysql_path, '-e', command],
                    capture_output=True,
                    text=True,
                    check=True,
                    shell=False
                )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            return f"Error executing MySQL command: {e.stderr}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"

def get_mysql_tool() -> Tool:
    """Create and return a MySQL Tool for use with LangGraph."""
    tool = MySQLTool()
    return Tool(
        name="MySQL Tool",
        func=tool.execute_command,
        description="Executes MySQL CLI commands to manage MySQL databases. Common commands: SHOW DATABASES, USE [db], SHOW TABLES, SELECT * FROM [table]. The tool will execute any valid MySQL CLI command and return the results"
    ) 