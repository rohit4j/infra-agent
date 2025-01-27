import os
import logging
import requests
from requests.auth import HTTPBasicAuth
from langchain.agents import Tool
from dotenv import load_dotenv

# Configure logging with detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('tools.log')
    ]
)

# Get logger for this module
logger = logging.getLogger(__name__)


def log_tool_interaction(func):
    """Decorator to log tool interactions with LLM."""

    def wrapper(*args, **kwargs):
        command = args[1] if len(args) > 1 else kwargs.get('command', '')
        logger.info("=" * 80)
        logger.info("TOOL: RabbitMQ")
        logger.info("INPUT FROM LLM:")
        logger.info("-" * 40)
        logger.info(f"Command: {command}")
        logger.info("-" * 40)
        try:
            result = func(*args, **kwargs)
            logger.info("OUTPUT TO LLM:")
            logger.info("-" * 40)
            logger.info(result)
            logger.info("-" * 40)
            logger.info("=" * 80)
            return result
        except Exception as e:
            logger.error("ERROR IN TOOL EXECUTION:")
            logger.error("-" * 40)
            logger.error(str(e))
            logger.error("-" * 40)
            logger.info("=" * 80)
            raise

    return wrapper


class RabbitMQTool:
    def __init__(self):
        """Initialize the RabbitMQ tool with RabbitMQ server credentials."""
        logger.info("Initializing RabbitMQ tool")
        try:
            load_dotenv()  # Load environment variables from .env file

            # Get RabbitMQ connection details from environment variables
            self.host = os.getenv('RMQ_HOST', 'localhost')
            self.port = os.getenv('RMQ_MANAGEMENT_PORT', '15672')
            self.username = os.getenv('RMQ_USERNAME', 'guest')
            self.password = os.getenv('RMQ_PASSWORD', 'guest')
            self.base_url = f"http://{self.host}:{self.port}/api"

            self.test_connection()
            logger.info("RabbitMQ tool initialization completed successfully")
        except Exception as e:
            logger.error(f"Failed to initialize RabbitMQ tool: {str(e)}", exc_info=True)
            raise

    def test_connection(self):
        """Test the RabbitMQ connection by checking the server health."""
        try:
            url = f"{self.base_url}/overview"
            response = requests.get(url, auth=HTTPBasicAuth(self.username, self.password))
            response.raise_for_status()
            logger.info(f"RabbitMQ connection test successful \nRMQ response{response.text.strip()}")
        except Exception as e:
            logger.error("RabbitMQ connection test failed: %s", str(e))
            raise

    @log_tool_interaction
    def execute_command(self, command: str) -> str:
        """Execute RabbitMQ command using the HTTP API, handle 404 error gracefully."""
        try:
            # Split the command into HTTP method and API path
            command_parts = command.split(' ', 1)
            if len(command_parts) != 2:
                raise ValueError(f"Invalid command format: {command}")

            method = command_parts[0].strip().upper()
            path_and_payload = command_parts[1].strip()

            # Extract the path (API endpoint)
            path_parts = path_and_payload.split(' ', 1)
            api_path = path_parts[0]  # e.g., /queues/%2F/test_queue
            payload = path_parts[1] if len(path_parts) > 1 else None  # Payload for PUT/POST requests

            # Construct the full API URL
            url = f"http://{self.host}:15672/{api_path}"

            # Prepare the request based on the HTTP method
            if method == 'GET':
                # For GET, no payload
                response = requests.get(url, auth=(self.username, self.password))
            elif method == 'PUT' or method == 'POST':
                # For PUT or POST, send the payload
                response = requests.put(url, data=payload, headers={'Content-Type': 'application/json'}, auth=(self.username, self.password))
            elif method == 'DELETE':
                # For DELETE, no payload
                response = requests.delete(url, auth=(self.username, self.password))
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            # Check if the response status is 404
            if response.status_code == 404:
                # Log the 404 error without escalating
                logger.warning(f"Resource not found for command: {command} (404 error).")
                return f"Resource not found for the command: {command}. Please check if the resource exists."

            # Check if the response is successful (status code 200)
            if response.status_code == 200:
                return response.text.strip()  # Return the response content

            # For other status codes, return the status message
            logger.error(f"Error executing RabbitMQ command: {response.status_code} - {response.text}")
            return f"Error executing command: {response.status_code} - {response.text}"

        except requests.exceptions.RequestException as e:
            # Handle exceptions related to the HTTP request
            logger.error(f"Request failed: {str(e)}")
            return f"Request failed: {str(e)}"
        except ValueError as ve:
            # Handle invalid command format errors
            logger.error(f"Invalid command format: {str(ve)}")
            return f"Invalid command format: {str(ve)}"
        except Exception as e:
            # Catch other unexpected exceptions
            logger.error(f"Unexpected error during command execution: {str(e)}")
            return f"Unexpected error: {str(e)}"

    def _make_http_request(self, method: str, url: str, data: str = None):
        """Helper to make an HTTP request to the RabbitMQ API."""
        headers = {"Content-Type": "application/json"}
        auth = HTTPBasicAuth(self.username, self.password)

        if method == "GET":
            return requests.get(url, auth=auth, headers=headers)
        elif method == "POST":
            return requests.post(url, auth=auth, headers=headers, data=data)
        elif method == "PUT":
            return requests.put(url, auth=auth, headers=headers, data=data)
        elif method == "DELETE":
            return requests.delete(url, auth=auth, headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")


def get_rabbitmq_tool() -> Tool:
    """Create and return a RabbitMQ Tool for use with LangGraph."""
    try:
        tool_obj = RabbitMQTool()
        rabbitmq_tool = Tool(
            name="RabbitMQ Tool",
            func=tool_obj.execute_command,
            description=(
                "You are an expert in managing RabbitMQ servers using the HTTP API. "
                "Map user queries to valid RabbitMQ API commands based on CloudAMQP API docs, and execute them safely.\n\n"
                "GUIDELINES:\n"
                "1. Map queries to RabbitMQ API commands.\n"
                "2. Ensure commands are safe and formatted correctly.\n"
                "3. Ask for clarification if needed.\n\n"
                "EXAMPLES:\n"
                "- Query: 'List queues' → Command: `GET /api/queues`\n"
                "- Query: 'Create queue test_queue' → Command: `PUT /api/queues/%2F/test_queue {\"durable\":true}`\n"
                "- Query: 'Delete queue test_queue' → Command: `DELETE /api/queues/%2F/test_queue`\n"
                "- Query: 'Get server status' → Command: `GET /api/overview`\n"
                "- Query: 'Check health status' → Command: `GET /api/health`\n\n"
                "OUTPUT:\n"
                "- Display command results or explain failure."
            )
        )
        return rabbitmq_tool
    except Exception as e:
        logger.error(f"Failed to create RabbitMQ Tool: {str(e)}", exc_info=True)
        raise
