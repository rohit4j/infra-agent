import logging
import subprocess
import shutil
import os
from langchain.agents import Tool
from typing import List, Optional

# Configure logging
logger = logging.getLogger(__name__)

class K8sTool:
    def __init__(self):
        """Initialize the K8s tool with kubectl path."""
        logger.info("Initializing K8s tool")
        # Find kubectl in PATH
        self.kubectl_path = shutil.which('kubectl')
        if not self.kubectl_path:
            logger.error("kubectl not found in PATH")
            raise RuntimeError("kubectl not found in PATH")
        logger.info(f"kubectl found at: {self.kubectl_path}")
        
        # Convert Windows path to raw string to handle spaces
        if os.name == 'nt':  # Windows
            self.kubectl_path = f'"{self.kubectl_path}"'
            logger.debug(f"Windows path adjusted to: {self.kubectl_path}")

    def execute_command(self, command: str) -> str:
        """Execute a kubectl command and return the output."""
        logger.info("=" * 80)
        logger.info("KUBECTL COMMAND INPUT:")
        logger.info("-" * 40)
        logger.info(command)
        logger.info("-" * 40)
        
        try:
            # Use list form to avoid shell injection and handle spaces in paths
            cmd_parts = command.split()
            if os.name == 'nt':  # Windows
                logger.debug(f"Executing on Windows with command parts: {cmd_parts}")
                result = subprocess.run(
                    [self.kubectl_path.strip('"')] + cmd_parts,
                    capture_output=True,
                    text=True,
                    check=True,
                    shell=False  # Avoid shell to handle spaces better
                )
            else:  # Unix-like
                logger.debug(f"Executing on Unix with command parts: {cmd_parts}")
                result = subprocess.run(
                    [self.kubectl_path] + cmd_parts,
                    capture_output=True,
                    text=True,
                    check=True,
                    shell=False
                )
            
            logger.info("KUBECTL COMMAND OUTPUT:")
            logger.info("-" * 40)
            logger.info(result.stdout.strip())
            logger.info("-" * 40)
            logger.info("=" * 80)
            
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            error_msg = f"Error executing kubectl command: {e.stderr}"
            logger.error("KUBECTL ERROR OUTPUT:")
            logger.error("-" * 40)
            logger.error(error_msg)
            logger.error("-" * 40)
            logger.info("=" * 80)
            return error_msg
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error("KUBECTL ERROR OUTPUT:")
            logger.error("-" * 40)
            logger.error(error_msg)
            logger.error("-" * 40)
            logger.info("=" * 80)
            return error_msg

def run_kubectl_command(command: List[str]) -> str:
    """Execute kubectl command and return output."""
    try:
        logger.info("=" * 80)
        logger.info("KUBECTL COMMAND INPUT:")
        logger.info("-" * 40)
        logger.info(' '.join(command))
        logger.info("-" * 40)
        
        result = subprocess.run(
            ['kubectl'] + command,
            capture_output=True,
            text=True,
            check=True
        )
        
        logger.info("KUBECTL COMMAND OUTPUT:")
        logger.info("-" * 40)
        logger.info(result.stdout)
        logger.info("-" * 40)
        logger.info("=" * 80)
        
        return result.stdout
    except subprocess.CalledProcessError as e:
        error_msg = f"kubectl command failed: {e.stderr}"
        logger.error("KUBECTL ERROR OUTPUT:")
        logger.error("-" * 40)
        logger.error(error_msg)
        logger.error("-" * 40)
        logger.info("=" * 80)
        return f"Error: {error_msg}"
    except Exception as e:
        error_msg = f"Unexpected error running kubectl: {str(e)}"
        logger.error("KUBECTL ERROR OUTPUT:")
        logger.error("-" * 40)
        logger.error(error_msg)
        logger.error("-" * 40)
        logger.info("=" * 80)
        return f"Error: {error_msg}"

def get_k8s_tool() -> Tool:
    """Create and return a Kubernetes Tool for use with LangGraph."""
    logger.info("Creating Kubernetes Tool")
    try:
        tool = K8sTool()
        k8s_tool = Tool(
            name="Kubernetes Tool",
            func=tool.execute_command,
            description="Executes kubectl commands to manage Kubernetes clusters. IT can run any kubectl command. Examples commands: get nodes, get pods, get services, describe pod [name], get deployments"
        )
        logger.info("Successfully created Kubernetes Tool")
        return k8s_tool
    except Exception as e:
        logger.error(f"Failed to create Kubernetes Tool: {str(e)}")
        raise 