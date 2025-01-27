import subprocess
import json
import shutil
import os
from langchain.agents import Tool
import logging
from dotenv import load_dotenv
import shlex

# Configure logging with more detailed format
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
        logger.info("TOOL: Redis")
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

class RedisTool:
    def __init__(self):
        """Initialize the Redis tool with redis-cli path."""
        logger.info("Initializing Redis tool")
        try:
            load_dotenv()
            self.host = os.getenv('REDIS_HOST', 'localhost')
            self.port = os.getenv('REDIS_PORT', '6379')
            self.password = os.getenv('REDIS_PASSWORD', None)

            self.redis_cli_path = shutil.which('redis-cli', path=os.environ.get('PATH'))
            if not self.redis_cli_path:
                raise RuntimeError(
                    "Redis CLI not found in PATH. Please install Redis CLI using your system's package manager "
                    "(e.g., 'sudo apt install redis-tools' or 'brew install redis')."
                )
            if ' ' in self.redis_cli_path:
                self.redis_cli_path = f'"{self.redis_cli_path}"'
            logger.info(f"redis-cli executable found at: {self.redis_cli_path}")

            self.test_connection()
            logger.info("Redis tool initialization completed successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Redis tool: {str(e)}", exc_info=True)
            raise

    def test_connection(self):
        """Test the Redis connection."""
        try:
            output = self.execute_command("PING")
            if output != "PONG":
                logger.warning("Unexpected response from Redis: %s", output)
            else:
                logger.info("Redis connection test successful")
        except Exception as e:
            logger.error("Redis connection test failed: %s", str(e))
            raise

    @log_tool_interaction
    def execute_command(self, command: str) -> str:
        """Execute Redis command."""
        try:
            command_args = [self.redis_cli_path, "-h", self.host, "-p", self.port]
            if self.password:
                command_args.extend(["-a", self.password])

            command_args.extend(shlex.split(command))

            result = subprocess.run(
                command_args,
                capture_output=True,
                text=True,
                check=True,
                timeout=10  # Timeout in seconds
            )

            output = result.stdout.strip()
            return output if output else "Command executed successfully (no results to display)"
        except subprocess.TimeoutExpired:
            error_msg = "Error: Command execution timed out."
            logger.error(error_msg)
            return error_msg
        except subprocess.CalledProcessError as e:
            error_msg = f"Error executing Redis command: {e.stderr.strip()}"
            logger.error(error_msg)
            return error_msg
        except Exception as e:
            error_msg = f"Unexpected error during command execution: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return error_msg

def get_redis_tool() -> Tool:
    """Create and return a Redis Tool for use with LangGraph."""
    try:
        tool_obj = RedisTool()
        redis_tool = Tool(
            name="Redis Tool",
            func=tool_obj.execute_command,
            description=(
                "Execute Redis commands to interact with the Redis server.\n\n"
                "IMPORTANT RULES:\n"
                "1. Use proper Redis command syntax.\n"
                "2. Check key existence with EXISTS before operations.\n"
                "3. Use INFO for server status.\n\n"
                "Examples of PREFERRED commands:\n"
                "- 'INFO' (Check server status)\n"
                "- 'KEYS *' (List all keys)\n"
                "- 'GET mykey' (Retrieve a value)\n"
                "- 'SET mykey value' (Set a value)\n\n"
                "Examples of DISCOURAGED commands:\n"
                "- Improperly formatted commands.\n"
                "- Operations without checking key existence."
            )
        )
        return redis_tool
    except Exception as e:
        logger.error(f"Failed to create Redis Tool: {str(e)}", exc_info=True)
        raise
