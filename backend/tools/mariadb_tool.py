import subprocess
import shutil
import os
from langchain.agents import Tool

class MariaDBTool:
    def __init__(self):
        """Initialize the MariaDB tool."""
        # Find mariadb executable
        self.mariadb_path = shutil.which('mariadb') or shutil.which('mysql')
        if not self.mariadb_path:
            raise RuntimeError("MariaDB/MySQL client not found in PATH. Please install MariaDB/MySQL client.")
        
        # Set environment for subprocess calls
        self.env = os.environ.copy()
        
        # Check if server is running
        try:
            result = subprocess.run([
                self.mariadb_path,
                '-h', '127.0.0.1',  # Use IP instead of localhost
                '-P', '3306',
                '-u', 'root',
                '-proot',
                '--protocol=TCP',
                '-e', 'SELECT 1'
            ], capture_output=True, text=True, check=True, env=self.env)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Cannot connect to MariaDB server: {e.stderr}")

    def execute_command(self, command: str) -> str:
        try:
            result = subprocess.run([
                self.mariadb_path,
                '-h', '127.0.0.1',  # Use IP instead of localhost
                '-P', '3306',
                '-u', 'root',
                '-proot',
                '--protocol=TCP',
                '-e', command
            ], capture_output=True, text=True, check=True, env=self.env)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            return f"Error executing MariaDB command: {e.stderr}"

def get_mariadb_tool() -> Tool:
    """Create and return a MariaDB Tool for use with LangGraph."""
    tool = MariaDBTool()
    return Tool(
        name="MariaDB Tool",
        func=tool.execute_command,
        description="Executes MariaDB CLI commands to manage MariaDB databases. Common commands: SHOW DATABASES, USE [db], SHOW TABLES, SELECT * FROM [table]"
    ) 