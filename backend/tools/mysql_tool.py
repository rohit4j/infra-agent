import subprocess
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
        logger.info("TOOL: MySQL")
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

class MySQLTool:
    def __init__(self):
        """Initialize the MySQL tool with mysql path."""
        logger.info("Initializing MySQL tool")
        
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
            
            # Get MySQL connection details from environment
            self.host = os.getenv('MARIADB_HOST', 'localhost')
            self.port = os.getenv('MARIADB_PORT', '3306')
            self.user = os.getenv('MARIADB_USER', 'admin')
            self.password = os.getenv('MARIADB_PASSWORD', 'adminpass')
            self.database = os.getenv('MARIADB_DATABASE', 'testdb')
            
            logger.info(f"Using MySQL connection: {self.host}:{self.port}")

            # Locate 'mysql' client
            self.mysql_path = shutil.which('mysql', path=os.environ.get('PATH'))
            if not self.mysql_path:
                logger.error("MySQL client not found in PATH")
                raise RuntimeError(
                    "MySQL client not found in PATH. "
                    "Please ensure MySQL client is installed and added to your system PATH."
                )
            logger.info(f"mysql executable found at: {self.mysql_path}")
            
            # Handle paths with spaces
            if ' ' in self.mysql_path:
                self.mysql_path = f'"{self.mysql_path}"'
                logger.debug(f"Adjusted mysql path for spaces: {self.mysql_path}")
            
            logger.info("MySQL tool initialization completed successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize MySQL tool: {str(e)}", exc_info=True)
            raise

    @log_tool_interaction
    def execute_command(self, command: str) -> str:
        """Execute MySQL command."""
        logger.info(f"Received command to execute: {command}")
        
        try:
            # Execute command
            logger.info("Executing MySQL command")
            result = subprocess.run(
                [
                    self.mysql_path,
                    f"-h{self.host}",
                    f"-P{self.port}",
                    f"-u{self.user}",
                    f"-p{self.password}",
                    self.database,
                    "-e", command
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
            error_msg = f"Error executing MySQL command: {e.stderr}"
            logger.error(error_msg, exc_info=True)
            return error_msg
        except Exception as e:
            error_msg = f"Unexpected error during command execution: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return error_msg

def get_mysql_tool() -> Tool:
    """Create and return a MySQL Tool for use with LangGraph."""
    logger.info("Creating MySQL Tool")
    try:
        tool_obj = MySQLTool()
        mysql_tool = Tool(
            name="MySQL Tool",
            func=tool_obj.execute_command,
            description=(
                "Execute MySQL commands to interact with the database.\n\n"
                "IMPORTANT RULES:\n"
                "1. ALWAYS use proper SQL syntax\n"
                "2. Before querying tables, check their schema using 'DESCRIBE table_name;'\n"
                "3. If database context unknown, first use 'SHOW DATABASES;' then 'SHOW TABLES;'\n\n"
                "Examples of CORRECT commands:\n"
                "- 'SHOW DATABASES;'\n"
                "- 'SHOW TABLES;'\n"
                "- 'DESCRIBE users;'\n"
                "- 'SELECT * FROM users LIMIT 5;'\n\n"
                "Examples of INCORRECT commands:\n"
                "- Complex queries without checking schema\n"
                "- Commands without proper SQL syntax"
            )
        )
        logger.info("Successfully created MySQL Tool")
        return mysql_tool
    except Exception as e:
        logger.error(f"Failed to create MySQL Tool: {str(e)}", exc_info=True)
        raise 