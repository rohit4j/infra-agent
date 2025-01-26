import subprocess
import shutil
import os
from langchain.agents import Tool
import logging

# Configure logging
logger = logging.getLogger(__name__)

class MongoDBTool:
    def __init__(self):
        """Initialize the MongoDB tool with mongosh path."""
        logger.info("Initializing MongoDB tool")
        # Ensure we have the full system PATH
        if os.name == 'nt':  # Windows
            paths = os.environ.get('PATH', '').split(';')
        else:  # Unix-like
            paths = os.environ.get('PATH', '').split(':')
            
        # Update environment for subprocess calls
        self.env = os.environ.copy()
        
        # Find mongosh in PATH
        self.mongosh_path = shutil.which('mongosh', path=os.environ.get('PATH'))
        if not self.mongosh_path:
            logger.error("MongoDB Shell (mongosh) not found in PATH")
            raise RuntimeError("MongoDB Shell (mongosh) not found in PATH. Please ensure MongoDB Shell is installed and added to your system PATH.")
        logger.info(f"mongosh found at: {self.mongosh_path}")
            
        # Handle paths with spaces for all platforms
        if ' ' in self.mongosh_path:
            self.mongosh_path = f'"{self.mongosh_path}"'
            logger.debug(f"Adjusted mongosh path for spaces: {self.mongosh_path}")

    def execute_command(self, command: str) -> str:
        """Execute a mongosh command and return the output."""
        logger.info(f"Executing MongoDB command: {command}")
        try:
            # Use list form to avoid shell injection and handle spaces in paths
            result = subprocess.run(
                [self.mongosh_path, '--quiet', '--eval', command],
                capture_output=True,
                text=True,
                check=True,
                shell=False,  # Avoid shell to handle spaces better
                env=self.env  # Use the full environment
            )
            logger.info("MongoDB command executed successfully")
            logger.debug(f"Command output: {result.stdout.strip()}")
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            error_msg = f"Error executing mongosh command: {e.stderr}"
            logger.error(error_msg)
            return error_msg
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            return error_msg

def get_mongo_tool() -> Tool:
    """Create and return a MongoDB Tool for use with LangGraph."""
    logger.info("Creating MongoDB Tool")
    try:
        tool = MongoDBTool()
        mongo_tool = Tool(
            name="MongoDB Tool",
            func=tool.execute_command,
            description="Executes mongosh commands to manage MongoDB databases. Common commands: show dbs, use [db], show collections, db.[collection].find().The tool will execute any valid mongosh command and return the results"
        )
        logger.info("Successfully created MongoDB Tool")
        return mongo_tool
    except Exception as e:
        logger.error(f"Failed to create MongoDB Tool: {str(e)}")
        raise 