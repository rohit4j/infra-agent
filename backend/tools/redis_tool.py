import subprocess
import json
import shutil
import os
from langchain.agents import Tool
import logging
from dotenv import load_dotenv

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
        # Extract the command from args (first argument after self)
        command = args[1] if len(args) > 1 else kwargs.get('command', '')
        
        # Log input
        logger.info("=" * 80)
        logger.info("TOOL: Redis")
        logger.info("INPUT FROM LLM:")
        logger.info("-" * 40)
        logger.info(f"Command: {command}")
        logger.info("-" * 40)
        
        # Execute the function
        try:
            result = func(*args, **kwargs)
            
            # Log output
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
            # Ensure we have the full system PATH
            if os.name == 'nt':  # Windows
                paths = os.environ.get('PATH', '').split(';')
                logger.debug(f"Windows PATH entries: {len(paths)} paths found")
            else:  # Unix-like
                paths = os.environ.get('PATH', '').split(':')
                logger.debug(f"Unix PATH entries: {len(paths)} paths found")
                
            self.env = os.environ.copy()
            logger.debug("Environment variables copied for subprocess execution")

            # Load environment variables
            load_dotenv()
            
            # Get Redis connection details from environment
            self.host = os.getenv('REDIS_HOST', 'localhost')
            self.port = os.getenv('REDIS_PORT', '6379')
            
            logger.info(f"Using Redis connection: {self.host}:{self.port}")

            # Locate 'redis-cli'
            self.redis_cli_path = shutil.which('redis-cli', path=os.environ.get('PATH'))
            if not self.redis_cli_path:
                logger.error("Redis CLI not found in PATH")
                raise RuntimeError(
                    "Redis CLI not found in PATH. "
                    "Please ensure Redis CLI is installed and added to your system PATH."
                )
            logger.info(f"redis-cli executable found at: {self.redis_cli_path}")
            
            # Handle paths with spaces
            if ' ' in self.redis_cli_path:
                self.redis_cli_path = f'"{self.redis_cli_path}"'
                logger.debug(f"Adjusted redis-cli path for spaces: {self.redis_cli_path}")
            
            logger.info("Redis tool initialization completed successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Redis tool: {str(e)}", exc_info=True)
            raise

    @log_tool_interaction
    def execute_command(self, command: str) -> str:
        """Execute Redis command."""
        logger.info(f"Received command to execute: {command}")
        
        try:
            # Execute command
            logger.info("Executing Redis command")
            result = subprocess.run(
                [
                    self.redis_cli_path,
                    "-h", self.host,
                    "-p", self.port,
                    command
                ],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Process output
            output = result.stdout.strip()
            if not output:
                logger.warning("Command executed successfully but returned no output")
                return "Command executed successfully (no results to display)"
                
            logger.info("Command execution completed successfully")
            logger.debug(f"Raw output: {output}")
            return output
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Error executing Redis command: {e.stderr}"
            logger.error(error_msg, exc_info=True)
            return error_msg
        except Exception as e:
            error_msg = f"Unexpected error during command execution: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return error_msg

def get_redis_tool() -> Tool:
    """Create and return a Redis Tool for use with LangGraph."""
    logger.info("Creating Redis Tool")
    try:
        tool_obj = RedisTool()
        redis_tool = Tool(
            name="Redis Tool",
            func=tool_obj.execute_command,
            description=(
                "Execute Redis commands to interact with the Redis server.\n\n"
                "IMPORTANT RULES:\n"
                "1. Use proper Redis command syntax\n"
                "2. Check key existence with EXISTS before operations\n"
                "3. Use INFO for server status\n\n"
                "Examples of CORRECT commands:\n"
                "- 'INFO'\n"
                "- 'KEYS *'\n"
                "- 'GET mykey'\n"
                "- 'SET mykey value'\n\n"
                "Examples of INCORRECT commands:\n"
                "- Commands without proper Redis syntax\n"
                "- Operations on keys without checking existence"
            )
        )
        logger.info("Successfully created Redis Tool")
        return redis_tool
    except Exception as e:
        logger.error(f"Failed to create Redis Tool: {str(e)}", exc_info=True)
        raise 