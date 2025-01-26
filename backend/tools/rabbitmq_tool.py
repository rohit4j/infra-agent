import subprocess
import shutil
import os
from langchain.agents import Tool

class RabbitMQTool:
    def __init__(self):
        """Initialize the RabbitMQ tool with rabbitmqctl path."""
        # Find rabbitmqctl in PATH
        self.rabbitmqctl_path = shutil.which('rabbitmqctl')
        if not self.rabbitmqctl_path:
            raise RuntimeError("rabbitmqctl not found in PATH")
        
        # Convert Windows path to raw string to handle spaces
        if os.name == 'nt':  # Windows
            self.rabbitmqctl_path = f'"{self.rabbitmqctl_path}"'

    def execute_command(self, command: str) -> str:
        """Execute a rabbitmqctl command and return the output."""
        try:
            # Use list form to avoid shell injection and handle spaces in paths
            cmd_parts = command.split()
            if os.name == 'nt':  # Windows
                result = subprocess.run(
                    [self.rabbitmqctl_path.strip('"')] + cmd_parts,
                    capture_output=True,
                    text=True,
                    check=True,
                    shell=False  # Avoid shell to handle spaces better
                )
            else:  # Unix-like
                result = subprocess.run(
                    [self.rabbitmqctl_path] + cmd_parts,
                    capture_output=True,
                    text=True,
                    check=True,
                    shell=False
                )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            return f"Error executing rabbitmqctl command: {e.stderr}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"

def get_rabbitmq_tool() -> Tool:
    """Create and return a RabbitMQ Tool for use with LangGraph."""
    tool = RabbitMQTool()
    return Tool(
        name="RabbitMQ Tool",
        func=tool.execute_command,
        description="Executes rabbitmqctl commands to manage RabbitMQ servers. Common commands: list_queues, list_exchanges, list_bindings, list_connections"
    ) 