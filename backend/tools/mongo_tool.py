import subprocess
import shutil
import os
from langchain.agents import Tool
import logging
from dotenv import load_dotenv

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
        """
        Execute MongoDB commands in a single session with JavaScript:
          - commands are converted from shell style to JavaScript
          - outputs are separated by delimiters to pair each command with its output
        """
        logger.info(f"Received commands: {commands}")

        # Split incoming commands by ';' and filter out empty items
        incoming_commands = [c.strip() for c in commands.split(';') if c.strip()]

        # Convert each command to valid mongosh JavaScript
        converted_commands = [self._convert_command(c) for c in incoming_commands]

        # Build JavaScript with delimiters for just the new commands
        js_script = "\n".join([
            f"""
            print('### COMMAND_START ###');
            print('Command: {cmd}');
            try {{
                {cmd}
            }} catch (e) {{
                print('Error: ' + e);
            }}
            print('### COMMAND_END ###');
            """ for cmd in converted_commands
        ])

        try:
            logger.debug(f"Executing JavaScript in mongosh:\n{js_script}")
            result = subprocess.run(
                [self.mongosh_path, self.mongodb_uri, '--eval', js_script],
                capture_output=True,
                text=True,
                check=True
            )

            raw_output = result.stdout.strip()
            logger.debug(f"Raw mongosh output: {raw_output}")

            # Parse the raw output based on the delimiters
            outputs = []
            current_command = None
            current_output = []

            for line in raw_output.splitlines():
                if line.startswith('### COMMAND_START ###'):
                    # If we have a previous command, append its output first
                    if current_command:
                        outputs.append(f"{current_command}\nOutput:\n{''.join(current_output)}")
                    current_command = None
                    current_output = []
                elif line.startswith('Command:'):
                    current_command = line
                elif line.startswith('### COMMAND_END ###'):
                    continue
                else:
                    current_output.append(line + '\n')

            # Finalize last block
            if current_command:
                outputs.append(f"{current_command}\nOutput:\n{''.join(current_output)}")

            final_output = "\n\n".join(outputs)
            logger.info(f"Commands output: {final_output}")
            return final_output

        except subprocess.CalledProcessError as e:
            error_msg = f"Error: {e.stderr.strip() if e.stderr else str(e)}"
            logger.error(error_msg)
            return f"Error occurred during execution:\n{error_msg}"
        except Exception as e:
            error_msg = f"General Error: {str(e)}"
            logger.error(error_msg)
            return f"Error occurred during execution:\n{error_msg}"


def get_mongo_tool() -> Tool:
    """
    Create and return a MongoDB Tool for use with LangGraph.

    The tool:
      - Maintains session context using a single JavaScript block.
      - Converts old shell commands (use <db>, show dbs, show collections, etc.)
        into valid JavaScript for mongosh.
      - Instructs the LLM to write commands with semicolons, but it will handle
        rewriting them if needed.
    """
    logger.info("Creating MongoDB Tool")
    try:
        tool_obj = MongoDBTool()
        mongo_tool = Tool(
            name="MongoDB Tool",
            func=tool_obj.execute_command,
            description=(
                "Execute MongoDB shell (mongosh) commands in a single, persistent session.\n\n"
                "1. Provide a full chain of commands since the start.\n"
                "2. If you use old shell syntax, e.g. 'use mydb;' or 'show collections;', "
                "the tool automatically converts them.\n"
                "3. Always end each command with a semicolon.\n"
                "4. Each command's output will be paired with its input.\n\n"
                "Examples:\n"
                "- use my_database;\n"
                "- show dbs;\n"
                "- show collections;\n"
                "- db.users.find();\n"
            )
        )
        logger.info("Successfully created MongoDB Tool")
        return mongo_tool
    except Exception as e:
        logger.error(f"Failed to create MongoDB Tool: {str(e)}")
        raise
