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
        logger.info("TOOL: AWS CLI")
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

class AWSServicesTool:
    def __init__(self):
        """Initialize the AWS tool with aws cli path."""
        logger.info("Initializing AWS Services Tool")
        # Find aws cli in PATH
        self.aws_path = shutil.which('aws')
        if not self.aws_path:
            logger.error("AWS CLI not found in PATH")
            raise RuntimeError("AWS CLI not found in PATH. Please ensure AWS CLI is installed and added to your system PATH.")
            
        # Check AWS configuration
        try:
            # Get user's home directory and AWS directory
            self.env = os.environ.copy()
            self.home = os.path.expanduser('~')
            self.aws_dir = os.path.join(self.home, '.aws')
            
            # Log the actual AWS directory for debugging
            logger.info(f"Using AWS directory: {self.aws_dir}")
            logger.info(f"AWS CLI path: {self.aws_path}")
            
            # Test AWS configuration by running a simple command
            result = subprocess.run(
                [self.aws_path, "configure", "list"],
                capture_output=True,
                text=True,
                check=True,
                cwd=self.home
            )
            logger.info(f"AWS configure output: {result.stdout}")
            
            if "access_key" not in result.stdout.lower():
                logger.error("AWS CLI is not configured with access key")
                raise RuntimeError("AWS CLI is not configured. Please run 'aws configure' to set up your credentials.")
        except subprocess.CalledProcessError as e:
            logger.error(f"AWS CLI error: {e.stderr}")
            raise RuntimeError(f"AWS CLI is not properly configured: {e.stderr}")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise

    def execute_command(self, command: str) -> str:
        """Execute an AWS CLI command and return the output."""
        logger.info("=" * 80)
        logger.info("AWS CLI COMMAND INPUT:")
        logger.info("-" * 40)
        logger.info(command)
        logger.info("-" * 40)
        
        try:
            # Split the command into parts and remove 'aws' if present
            cmd_parts = command.split()
            if cmd_parts[0].lower() == 'aws':
                cmd_parts = cmd_parts[1:]  # Remove the 'aws' prefix
            
            # Execute command
            result = subprocess.run(
                [self.aws_path] + cmd_parts,
                capture_output=True,
                text=True,
                check=True,
                cwd=self.home
            )
            
            # Log and return the output
            logger.info("AWS CLI COMMAND OUTPUT:")
            logger.info("-" * 40)
            logger.info(result.stdout.strip())
            logger.info("-" * 40)
            logger.info("=" * 80)
            
            return result.stdout.strip()
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Error executing AWS CLI command: {e.stderr}"
            logger.error("AWS CLI ERROR OUTPUT:")
            logger.error("-" * 40)
            logger.error(error_msg)
            logger.error("-" * 40)
            logger.info("=" * 80)
            return error_msg
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error("AWS CLI ERROR OUTPUT:")
            logger.error("-" * 40)
            logger.error(error_msg)
            logger.error("-" * 40)
            logger.info("=" * 80)
            return error_msg

def get_aws_tool() -> Tool:
    """Create and return an AWS CLI Tool for use with LangGraph."""
    logger.info("Creating AWS Services Tool")
    try:
        tool = AWSServicesTool()
        aws_tool = Tool(
            name="AWS CLI Tool",
            func=tool.execute_command,
            description="Executes AWS CLI commands to manage AWS services. Common commands: aws ec2 describe-instances, aws s3 ls, aws lambda list-functions. The tool will execute any valid AWS CLI command and return the results"
        )
        logger.info("Successfully created AWS Services Tool")
        return aws_tool
    except Exception as e:
        logger.error(f"Failed to create AWS Services Tool: {str(e)}")
        raise 