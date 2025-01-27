import streamlit as st
import httpx
import asyncio
from typing import AsyncGenerator
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('llm_interactions.log')
    ]
)
logger = logging.getLogger(__name__)

# Set the Streamlit page configuration
logger.info("Initializing Streamlit application")
st.set_page_config(page_title="Infrastructure Chat Assistant", layout="wide")

st.title("🚀 Infrastructure Chat Assistant")

# Initialize conversation history
if 'conversation' not in st.session_state:
    logger.info("Initializing new conversation history")
    st.session_state.conversation = []

# Initialize input key for resetting
if 'input_key' not in st.session_state:
    st.session_state.input_key = 0

# Function to increment key and clear input
def clear_input():
    logger.debug("Clearing input by incrementing input key")
    st.session_state.input_key += 1

# Display conversation history
logger.debug("Displaying conversation history")
for message in st.session_state.conversation:
    if message['role'] == 'user':
        st.markdown(
    f"""
    <div style="display: flex; justify-content: flex-end;">
        <div style="background-color: #e6f3ff; padding: 10px; border-radius: 10px; max-width: 70%;">
            <b>You:</b> {message['content']}
        </div>
    </div>
    """, 
    unsafe_allow_html=True
)
    else:
        st.markdown(f"**Assistant:** {message['content']}")

# Async function to handle streaming response
async def get_streaming_response(query: str) -> AsyncGenerator[str, None]:
    """Handle streaming response from backend LLM."""
    # Log the input query in a structured way
    logger.info("LLM Input Parameters:")
    logger.info("-" * 50)
    logger.info(f"Query: {query}")
    logger.info("-" * 50)

    # Configure longer timeouts
    timeout = httpx.Timeout(30.0, connect=60.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            logger.debug("Initiating streaming request to backend")
            async with client.stream("POST", "http://localhost:8000/process_query", json={"query": query}) as response:
                if response.status_code != 200:
                    error_msg = f"Error: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    yield error_msg
                    return

                logger.info("LLM Output Stream:")
                logger.info("-" * 50)
                full_response = ""
                async for chunk in response.aiter_text():
                    full_response += chunk
                    yield chunk
                
                # Log the complete response at the end
                logger.info("Complete LLM Response:")
                logger.info(full_response)
                logger.info("-" * 50)

            logger.info("Completed LLM interaction")

        except httpx.TimeoutException:
            error_msg = "Error: Request timed out. Please try again."
            logger.error(f"LLM Interaction Error: {error_msg}")
            yield error_msg
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            logger.error(f"LLM Interaction Error: {error_msg}", exc_info=True)
            yield error_msg

# Process streaming response
async def process_response(user_input: str, response_container: st.empty):
    """Process the streaming response from LLM."""
    logger.info("Starting new LLM interaction")
    logger.info("=" * 80)
    
    full_response = ""
    async for chunk in get_streaming_response(user_input):
        full_response += chunk
        response_container.markdown(f"**Assistant:** {full_response}")
    
    logger.info("LLM interaction completed")
    logger.info("=" * 80)
    return full_response

# Create a form for input
with st.form(key="query_form", clear_on_submit=True):
    # User input with dynamic key for clearing
    user_input = st.text_input("Enter your query (press Enter or click Send):", key=f"input_{st.session_state.input_key}")
    submit_button = st.form_submit_button("Send")

    # Handle form submission (works for both Enter and Send button)
    if submit_button and user_input:
        logger.info("Processing new user query")
        logger.info("=" * 80)
        
        # Append and immediately display user message
        st.session_state.conversation.append({'role': 'user', 'content': user_input})
        st.markdown(f"**You:** {user_input}")
        
        # Show loading indicator
        with st.spinner('Assistant is thinking...'):
            response_container = st.empty()
            
            # Create event loop for async operations
            logger.debug("Setting up async event loop")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                # Run the async function
                assistant_response = loop.run_until_complete(process_response(user_input, response_container))
                # Append assistant response to conversation history
                st.session_state.conversation.append({'role': 'assistant', 'content': assistant_response})
                logger.info("Query processing completed successfully")
            except Exception as e:
                error_msg = f"An error occurred: {str(e)}"
                logger.error(error_msg, exc_info=True)
                st.error(error_msg)
            finally:
                logger.debug("Cleaning up async resources")
                loop.close()
                clear_input()
                try:
                    st.rerun()
                except AttributeError:
                    st.experimental_rerun()