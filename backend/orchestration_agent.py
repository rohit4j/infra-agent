from typing import List
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import HumanMessage, SystemMessage
from tools.aws_tool import get_aws_tool
from tools.k8s_tool import get_k8s_tool
from tools.rabbitmq_tool import get_rabbitmq_tool
from tools.redis_tool import get_redis_tool
from tools.mongo_tool import get_mongo_tool
from tools.mysql_tool import get_mysql_tool
from tools.mariadb_tool import get_mariadb_tool
from tools.kong_gateway_tool import get_kong_tool
from tools.docker_tool import get_docker_tool
import os
import asyncio
import logging
from dotenv import load_dotenv
import subprocess
from langgraph.checkpoint.memory import MemorySaver

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OrchestrationAgent:
    def __init__(self):
        """Initialize the orchestration agent with LangGraph components."""
        logger.info("Initializing OrchestrationAgent")
        try:
            # Initialize LLM
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                logger.error("OPENAI_API_KEY not found in environment variables")
                raise ValueError("OPENAI_API_KEY not found in environment variables")
            
            # Initialize base LLM
            self.llm = ChatOpenAI(
                api_key=api_key,
                model="gpt-4o",
                temperature=0
            )
            logger.info("Successfully initialized OpenAI ChatLLM")
            
            # Initialize memory saver for conversation persistence
            self.memory = MemorySaver()
            
            # Initialize tools
            self.tools = self._initialize_tools()
            
            # Bind tools to LLM
            self.llm_with_tools = self.llm.bind_tools(
                self.tools,
                parallel_tool_calls=False
            )

            # Create the state graph with memory
            self.graph = self._create_state_graph()
            logger.info("Successfully initialized LangGraph state graph")

        except Exception as e:
            logger.error(f"Error during initialization: {str(e)}", exc_info=True)
            raise

    def _initialize_tools(self):
        """Initialize infrastructure tools."""
        logger.info("Initializing infrastructure tools")
        tools = []
        
        # Get the current process environment
        env = dict(os.environ)
        
        # Update PATH to include system paths
        try:
            if os.name == 'nt':  # Windows
                result = subprocess.run(
                    ['powershell', '-Command', '[Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")'],
                    capture_output=True,
                    text=True
                )
                if result.stdout.strip():
                    paths = result.stdout.strip().split(';') + env.get('PATH', '').split(';')
                    seen = set()
                    unique_paths = [p for p in paths if p and not (p in seen or seen.add(p))]
                    env['PATH'] = ';'.join(unique_paths)
                    logger.info("Successfully updated PATH with system environment")
        except Exception as e:
            logger.warning(f"Failed to get system PATH: {e}")

        # Update environment
        os.environ.update(env)
        
        tools_to_init = [
            ('Kubernetes', get_k8s_tool),
            ('AWS', get_aws_tool),
            ('RabbitMQ', get_rabbitmq_tool),
            ('Redis', get_redis_tool),
            ('MongoDB', get_mongo_tool),
            ('MySQL', get_mysql_tool),
            ('MariaDB', get_mariadb_tool),
             ('Docker', get_docker_tool),
            ('Kong Gateway', get_kong_tool)
        ]
        
        for tool_name, tool_func in tools_to_init:
            try:
                # Initialize tool with updated environment
                tool = tool_func()
                # Ensure function name follows pattern ^[a-zA-Z0-9_-]+$
                if hasattr(tool, 'name'):
                    tool.name = tool.name.replace(' ', '_')  # Replace spaces with underscores
                    # Remove any other special characters
                    tool.name = ''.join(c for c in tool.name if c.isalnum() or c in '_-')
                tools.append(tool)
                logger.info(f"Successfully initialized {tool_name} tool")
            except Exception as e:
                logger.warning(f"{tool_name}: Error during initialization - {str(e)}")

        return tools

    def _create_state_graph(self):
        """Create the LangGraph state graph."""
        # System message to guide the assistant
        sys_msg = SystemMessage(content="""You are an infrastructure management assistant that can help with various infrastructure tools.
        You can manage Kubernetes clusters, AWS resources, databases, and more. Be helpful and precise in your responses.""")

        # Assistant node that processes messages
        def assistant(state: MessagesState):
            messages = [sys_msg] + state["messages"]
            return {"messages": [self.llm_with_tools.invoke(messages)]}

        # Create graph
        builder = StateGraph(MessagesState)
        
        # Add nodes
        builder.add_node("assistant", assistant)
        builder.add_node("tools", ToolNode(self.tools))
        
        # Add edges
        builder.add_edge(START, "assistant")
        builder.add_conditional_edges(
            "assistant",
            tools_condition,
        )
        builder.add_edge("tools", "assistant")
        
        # Compile with memory
        return builder.compile(checkpointer=self.memory)

    async def process_query(self, query: str):
        """Process a user query using the LangGraph state graph."""
        logger.info(f"Processing query: {query}")
        try:
            # Create initial state with the query and use memory
            config = {"configurable": {"thread_id": "default"}}
            state = {"messages": [HumanMessage(content=query)]}
            result = await self.graph.ainvoke(state, config)
            
            # Get the final response
            final_message = result["messages"][-1]
            response = final_message.content
            
            # Yield response in chunks
            chunk_size = 100
            for i in range(0, len(response), chunk_size):
                chunk = response[i:i + chunk_size]
                yield chunk
                await asyncio.sleep(0.1)
                
        except Exception as e:
            error_msg = f"Error processing query: {str(e)}"
            logger.error(error_msg, exc_info=True)
            yield error_msg

# Create singleton instance
logger.info("Creating OrchestrationAgent singleton instance")
try:
    orchestration_agent = OrchestrationAgent()
    logger.info("Successfully created OrchestrationAgent singleton instance")
except Exception as e:
    logger.error("Failed to create OrchestrationAgent singleton instance", exc_info=True)
    raise 
