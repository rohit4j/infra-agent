import subprocess
import json
import shutil
import os
from langchain.agents import Tool
import logging

logger = logging.getLogger(__name__)

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
        try:
            # Log the command being executed
            logger.info(f"Executing AWS command: {command}")
            logger.info(f"Using AWS CLI path: {self.aws_path}")
            
            # Split command into parts and remove 'aws' if present
            cmd_parts = command.split()
            if cmd_parts[0] == 'aws':
                cmd_parts = cmd_parts[1:]
            
            # Construct command list - this works consistently across all OS
            full_command = [self.aws_path] + cmd_parts
            logger.info(f"Full command: {full_command}")
            
            # Execute command
            result = subprocess.run(
                full_command,
                capture_output=True,
                text=True,
                check=True,
                shell=False,
                cwd=self.home
            )
            
            # Log the output
            logger.info(f"Command stdout: {result.stdout[:200]}...")
            
            # Return the output directly
            return result.stdout.strip()
            
        except subprocess.CalledProcessError as e:
            logger.error(f"AWS CLI error: {e.stderr}")
            return f"Error: AWS CLI command failed: {e.stderr}"
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return f"Error: Unexpected error occurred: {str(e)}"

def get_aws_tool() -> Tool:
    """Create and return an AWS Services Tool for use with LangChain."""
    logger.info("Creating AWS Services Tool")
    try:
        tool = AWSServicesTool()
        aws_tool = Tool(
            name="AWS Services Tool",
            func=tool.execute_command,
            description="""Use this tool to manage AWS services and resources. This tool executes AWS CLI commands.
            
            Common AWS CLI commands:
            - VPC commands:
              * aws ec2 describe-vpcs
              * aws ec2 describe-vpc-endpoints
            - EC2 commands:
              * aws ec2 describe-instances
              * aws ec2 describe-security-groups
            - S3 commands:
              * aws s3 ls
              * aws s3 ls s3://[bucket-name]
            - EKS commands:
              * aws eks list-clusters
              * aws eks describe-cluster --name [cluster-name]
            
            The tool will execute any valid AWS CLI command and return the results."""
        )
        logger.info("Successfully created AWS Services Tool")
        return aws_tool
    except Exception as e:
        logger.error(f"Failed to create AWS Services Tool: {str(e)}")
        raise 