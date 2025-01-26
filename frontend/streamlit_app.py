import streamlit as st
import httpx
import asyncio
from typing import AsyncGenerator
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
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

# Display conversation history
logger.debug("Displaying conversation history")
for message in st.session_state.conversation:
    if message['role'] == 'user':
        st.markdown(f"**You:** {message['content']}")
    else:
        st.markdown(f"**Assistant:** {message['content']}")

# Async function to handle streaming response
async def get_streaming_response(query: str) -> AsyncGenerator[str, None]:
    logger.info(f"Sending query to backend: {query}")
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
                logger.debug("Starting to receive response chunks")
                async for chunk in response.aiter_text():
                    logger.debug(f"Received chunk: {chunk[:50]}...")  # Log first 50 chars of chunk
                    yield chunk
            logger.info("Completed receiving response from backend")
        except httpx.TimeoutException:
            error_msg = "Error: Request timed out. Please try again."
            logger.error(error_msg)
            yield error_msg
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            yield error_msg

# User input
user_input = st.text_input("Enter your query:", key='input')

# Handle send button
if st.button("Send"):
    if user_input:
        logger.info(f"Processing user input: {user_input}")
        # Append user message
        st.session_state.conversation.append({'role': 'user', 'content': user_input})
        
        # Display assistant's response as it streams
        response_container = st.empty()
        
        # Create event loop for async operations
        logger.debug("Setting up async event loop")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Process streaming response
        async def process_response():
            logger.debug("Starting to process streaming response")
            full_response = ""
            async for chunk in get_streaming_response(user_input):
                full_response += chunk
                response_container.markdown(f"**Assistant:** {full_response}")
            logger.debug("Completed processing streaming response")
            return full_response

        try:
            # Run the async function
            logger.debug("Running async process_response")
            assistant_response = loop.run_until_complete(process_response())
            # Append assistant response to conversation history
            st.session_state.conversation.append({'role': 'assistant', 'content': assistant_response})
            logger.info("Successfully processed query and updated conversation history")
        except Exception as e:
            error_msg = f"An error occurred: {str(e)}"
            logger.error(error_msg, exc_info=True)
            st.error(error_msg)
        finally:
            logger.debug("Cleaning up async resources")
            loop.close()
            st.experimental_rerun() 