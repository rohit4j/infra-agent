import subprocess
import shutil
import os
from langchain.agents import Tool
import logging
from dotenv import load_dotenv
import json

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class MongoDBTool:
    def __init__(self):
        """Initialize the MongoDB tool with mongosh path."""
        logger.info("Initializing MongoDB tool")
        
        # Ensure we have the full system PATH
        if os.name == 'nt':  # Windows
            paths = os.environ.get('PATH', '').split(';')
        else:  # Unix-like
            paths = os.environ.get('PATH', '').split(':')
            
        self.env = os.environ.copy()
        
        # Accumulate commands to maintain session context
        self._session_script = []

        # Locate 'mongosh'
        self.mongosh_path = shutil.which('mongosh', path=os.environ.get('PATH'))
        if not self.mongosh_path:
            logger.error("MongoDB Shell (mongosh) not found in PATH")
            raise RuntimeError(
                "MongoDB Shell (mongosh) not found in PATH. "
                "Please ensure MongoDB Shell is installed and added to your system PATH."
            )
        logger.info(f"mongosh found at: {self.mongosh_path}")
        
        # Handle paths with spaces
        if ' ' in self.mongosh_path:
            self.mongosh_path = f'"{self.mongosh_path}"'
            logger.debug(f"Adjusted mongosh path for spaces: {self.mongosh_path}")

        # MongoDB connection URI from environment
        self.mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://admin:adminpass@localhost:27017/')
        logger.info(f"Using MongoDB URI: {self.mongodb_uri}")

    def _convert_command(self, cmd: str) -> str:
        """
        Convert shell-style commands like:
          - 'use login_tracker;'
          - 'show collections;'
          - 'show dbs;'
        to valid JavaScript statements for mongosh.
        """
        # 1. Strip trailing semicolons/spaces
        stripped = cmd.strip().rstrip(';').strip().lower()

        # 2. Rewrite 'use <db>'
        if stripped.startswith('use '):
            # e.g. 'use my_db'
            parts = stripped.split(' ', 1)
            if len(parts) == 2:
                db_name = parts[1].strip()
                # Return both the db switch and a confirmation print
                return f'db = db.getSiblingDB("{db_name}"); print("Using database: " + db.getName());'
            return cmd if cmd.endswith(';') else f"{cmd};"

        # 3. Rewrite 'show dbs'
        if stripped == 'show dbs':
            return 'printjson(db.adminCommand({ listDatabases: 1 }));'

        # 4. Rewrite 'show collections' or 'show tables'
        if stripped in ('show collections', 'show tables'):
            return 'printjson(db.getCollectionNames());'

        # 5. Rewrite find() to use printjson for better output
        if '.find(' in stripped and not stripped.startswith('print'):
            return f'printjson({cmd});'

        # 6. If no special rewrites, just ensure the command ends with a semicolon
        return cmd if cmd.endswith(';') else f"{cmd};"

    def execute_command(self, commands: str) -> str:
        """Execute mongosh commands in a single session."""
        logger.info("=" * 80)
        logger.info("MONGODB COMMAND FROM LLM:")
        logger.info("-" * 40)
        logger.info(commands)
        logger.info("-" * 40)

        try:
            # Split incoming commands by ';' and filter out empty items
            incoming_commands = [c.strip() for c in commands.split(';') if c.strip()]

            # Convert each command to valid mongosh JavaScript
            converted_commands = [self._convert_command(c) for c in incoming_commands]
            
            # Join commands with semicolons
            js_commands = '; '.join(converted_commands)

            # Execute command
            result = subprocess.run(
                [self.mongosh_path, self.mongodb_uri, '--eval', js_commands],
                capture_output=True,
                text=True,
                check=True
            )
            
            output = result.stdout.strip()
            if not output:
                logger.warning("Command executed successfully but returned no output")
                return "No results found"
                
            logger.info("MONGODB RESPONSE TO LLM:")
            logger.info("-" * 40)
            logger.info(output)
            logger.info("-" * 40)
            logger.info("=" * 80)
            
            return output
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Error executing MongoDB command: {e.stderr}"
            logger.error(error_msg)
            logger.info("MONGODB ERROR RESPONSE TO LLM:")
            logger.info("-" * 40)
            logger.info(error_msg)
            logger.info("-" * 40)
            logger.info("=" * 80)
            return error_msg
        except Exception as e:
            error_msg = f"Unexpected error during command execution: {str(e)}"
            logger.error(error_msg)
            logger.info("MONGODB ERROR RESPONSE TO LLM:")
            logger.info("-" * 40)
            logger.info(error_msg)
            logger.info("-" * 40)
            logger.info("=" * 80)
            return error_msg


def get_mongo_tool() -> Tool:
    """Create and return a MongoDB Tool for use with LangGraph."""
    logger.info("Creating MongoDB Tool")
    try:
        tool_obj = MongoDBTool()
        mongo_tool = Tool(
            name="MongoDB Tool",
            func=tool_obj.execute_command,
            description=(
                "Execute MongoDB shell (mongosh) commands in a single, persistent session.\n\n"
                "IMPORTANT RULES:\n"
                "1. ALWAYS include 'use database_name;' before ANY query, even if you used it before\n"
                "2. Commands must be in sequence with semicolons, e.g.:\n"
                "   use login_tracker; db.users.find();\n"
                "3. Never assume database context is maintained between calls\n"
                "4. Each command's output will be paired with its input\n\n"
                "Examples of CORRECT command sequences:\n"
                "- 'use login_tracker; db.users.find();'\n"
                "- 'use mydatabase; show collections;'\n"
                "- 'show dbs;' (only for listing databases)\n\n"
                "Examples of INCORRECT command sequences:\n"
                "- 'db.users.find();' (missing database context)\n"
                "- 'show collections;' (missing database context)\n\n"
                "IF DB and COLLECTION NAME CONTEXT IS NOT AVAILABLE THEN ALWAYS FIRST CHECK ALL DBS and collections available before running any commands\n"
                "AND EVERY FRESH CALL TO THIS TOOL MUST INCLUDE 'use database_name;' BEFORE ANY QUERY"
            )
        )
        logger.info("Successfully created MongoDB Tool")
        return mongo_tool
    except Exception as e:
        logger.error(f"Failed to create MongoDB Tool: {str(e)}")
        raise
