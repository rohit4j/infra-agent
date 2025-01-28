from langchain.agents import Tool
import subprocess
from typing import Optional

class DockerTool:
    def execute_command(self, command: str) -> str:
        """Execute Docker commands and return output."""
        try:
            cmd = ['docker'] + command.split()
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            raise ConnectionError(f"Docker command failed: {e.stderr}")

def get_docker_tool() -> Tool:
    tool = DockerTool()
    return Tool(
        name="Docker Tool",
        func=tool.execute_command,
        description="Executes Docker commands. Examples: 'ps', 'logs mariadb', 'inspect mariadb'"
    )