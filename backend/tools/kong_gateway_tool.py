# kong_gateway_tool.py

import os
import subprocess
import shutil
import logging
from langchain.agents import Tool
import requests

class KongTool:
    def __init__(self, admin_url: str = "http://localhost:8001"):
        self.admin_url = admin_url.rstrip('/')
        self._verify_connection()

    def _verify_connection(self):
        try:
            response = requests.get(f"{self.admin_url}/")
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Cannot connect to Kong Admin API: {str(e)}")

    def execute_command(self, command: str) -> str:
        try:
            method, endpoint = command.split(maxsplit=1)
            url = f"{self.admin_url}/{endpoint.lstrip('/')}"
            
            response = requests.request(
                method=method.upper(),
                url=url,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return response.text
            
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Kong API request failed: {str(e)}")

def get_kong_tool() -> Tool:
    try:
        tool = KongTool()
        return Tool(
            name="Kong Gateway Tool",
            func=tool.execute_command,
            description="Manages Kong Gateway via Admin API. Commands: 'GET /services', 'GET /routes', 'GET /plugins'"
        )
    except ConnectionError as e:
        print(f"Warning: Kong Tool initialization failed - {str(e)}")
        raise ConnectionError(f"Warning: Kong Tool initialization failed - {str(e)}")
        # return None
# logger = logging.getLogger(__name__)

# class KongGatewayTool:
#     """
#     A super tool for interacting with a self-managed Kong Gateway via the `kong` CLI.
#     """

#     def __init__(self):
#         """Initialize the Kong tool by locating and validating the `kong` CLI."""
#         logger.info("Initializing Kong Gateway Tool")

#         # Find `kong` in the system PATH
#         self.kong_path = shutil.which('kong')
#         if not self.kong_path:
#             logger.error("kong CLI not found in PATH")
#             raise RuntimeError(
#                 "Kong CLI not found in PATH. Please ensure `kong` is installed and added to your system PATH."
#             )

#         logger.info(f"Kong CLI found at: {self.kong_path}")

#         # Optional: You could run a simple `kong version` check to verify the CLI is functional
#         try:
#             result = subprocess.run(
#                 [self.kong_path, "version"],
#                 capture_output=True,
#                 text=True,
#                 check=True
#             )
#             logger.info(f"Kong CLI version: {result.stdout.strip()}")
#         except subprocess.CalledProcessError as e:
#             logger.error(f"Error running 'kong version': {e.stderr}")
#             raise RuntimeError(f"Kong CLI not functioning properly: {e.stderr}")

#         # Additional config checks can be added here if needed

#     def execute_command(self, command: str) -> str:
#         """
#         Execute a `kong` CLI command and return the output.
#         Example commands:
#           - kong routes list
#           - kong services list
#           - kong consumers create --username user1
#         """
#         logger.info("=" * 80)
#         logger.info("KONG CLI COMMAND INPUT:")
#         logger.info("-" * 40)
#         logger.info(command)
#         logger.info("-" * 40)

#         try:
#             # Split the command into parts and remove 'kong' if present
#             cmd_parts = command.split()
#             if cmd_parts and cmd_parts[0].lower() == 'kong':
#                 cmd_parts = cmd_parts[1:]  # remove the 'kong' prefix

#             # Execute the command using the located kong CLI path
#             result = subprocess.run(
#                 [self.kong_path] + cmd_parts,
#                 capture_output=True,
#                 text=True,
#                 check=True
#             )

#             # Log output
#             logger.info("KONG CLI COMMAND OUTPUT:")
#             logger.info("-" * 40)
#             logger.info(result.stdout.strip())
#             logger.info("-" * 40)
#             logger.info("=" * 80)

#             return result.stdout.strip()

#         except subprocess.CalledProcessError as e:
#             error_msg = f"Error executing kong command: {e.stderr}"
#             logger.error("KONG CLI ERROR OUTPUT:")
#             logger.error("-" * 40)
#             logger.error(error_msg)
#             logger.error("-" * 40)
#             logger.info("=" * 80)
#             return error_msg
#         except Exception as e:
#             error_msg = f"Unexpected error: {str(e)}"
#             logger.error("KONG CLI ERROR OUTPUT:")
#             logger.error("-" * 40)
#             logger.error(error_msg)
#             logger.error("-" * 40)
#             logger.info("=" * 80)
#             return error_msg


# def get_kong_gateway_tool() -> Tool:
#     """
#     Create and return a Kong Gateway Tool for use with LangGraph or any other orchestration logic.
#     """
#     logger.info("Creating Kong Gateway Tool")
#     try:
#         tool = KongGatewayTool()
#         kong_tool = Tool(
#             name="Kong Gateway Tool",
#             func=tool.execute_command,
#             description=(
#                 "Executes `kong` CLI commands to manage a self-managed Kong Gateway installation. "
#                 "Examples: 'kong routes list', 'kong services list', 'kong consumers create --username user1'. "
#                 "Use this tool for any administrative or configuration tasks in Kong."
#             )
#         )
#         logger.info("Successfully created Kong Gateway Tool")
#         return kong_tool
#     except Exception as e:
#         logger.error(f"Failed to create Kong Gateway Tool: {str(e)}")
#         raise
