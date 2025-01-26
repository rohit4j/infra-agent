[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

# Infrastructure ChatBot

An intelligent chatbot powered by LangChain and GPT-4 that helps manage various infrastructure components through natural language interactions.

## Table of Contents
- [Overview](#overview)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Setup Instructions](#setup-instructions)
  - [Windows](#windows)
  - [macOS](#macos)
  - [Linux](#linux)
- [Understanding Key Components](#understanding-key-components)
- [Available Tools](#available-tools)
- [Usage Guide](#usage-guide)
- [Troubleshooting](#troubleshooting)

## Overview

This project implements an AI-powered chatbot that can help manage various infrastructure components through natural language. It uses:
- LangChain for orchestrating the AI components
- GPT-4 for natural language understanding
- Various infrastructure tools (Kubernetes, databases, etc.)
- FastAPI for the backend API
- Streamlit for the user interface

## Project Structure

```
.
├── backend/
│   ├── main.py                 # FastAPI application entry point
│   ├── orchestration_agent.py  # Main agent logic using LangGraph
│   └── tools/                  # Infrastructure tool implementations
│       ├── aws_tool.py
│       ├── k8s_tool.py
│       ├── mongo_tool.py
│       └── ...
├── streamlit_app.py           # Streamlit UI implementation
├── requirements.txt           # Python dependencies
└── .env.example              # Example environment variables
```

## Prerequisites

Before setting up the project, you need:
1. Python 3.10 or higher
2. Git
3. Basic understanding of command line
4. Text editor (VS Code recommended)

## Setup Instructions

### Common Steps (All Operating Systems)

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd infra-chatbot
   ```

2. Create a Python virtual environment:
   ```bash
   python -m venv venv
   ```

3. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

4. Edit .env file with required credentials (will be provided separately)

### Windows

1. Activate virtual environment:
   ```powershell
   .\venv\Scripts\activate
   ```

2. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

3. Install required tools:
   - **Kubernetes**: Install [minikube](https://minikube.sigs.k8s.io/docs/start/)
   - **MongoDB**: Download and install [MongoDB Community Server](https://www.mongodb.com/try/download/community)
   - **MySQL**: Download and install [MySQL Community Server](https://dev.mysql.com/downloads/mysql/)
   - **Redis**: Download and install [Redis for Windows](https://github.com/microsoftarchive/redis/releases)
   - **RabbitMQ**: Download and install [RabbitMQ](https://www.rabbitmq.com/download.html)

### macOS

1. Activate virtual environment:
   ```bash
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Install required tools:
   ```bash
   # Install Homebrew if not already installed
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

   # Install tools
   brew install kubernetes-cli
   brew install mongodb-community
   brew install mysql
   brew install redis
   brew install rabbitmq
   ```

### Linux (Ubuntu/Debian)

1. Activate virtual environment:
   ```bash
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Install required tools:
   ```bash
   # Update package list
   sudo apt update

   # Install tools
   sudo apt install -y kubectl
   sudo apt install -y mongodb
   sudo apt install -y mysql-server
   sudo apt install -y redis-server
   sudo apt install -y rabbitmq-server
   ```

## Understanding Key Components

### 1. Orchestration Agent (backend/orchestration_agent.py)
- Core component that manages the interaction between user input and infrastructure tools
- Uses LangGraph for managing the conversation flow
- Implements ReAct pattern (Reason-Act-Observe) for tool usage
- Key classes:
  - `OrchestrationAgent`: Main class that initializes LLM and tools
  - `MessagesState`: Manages conversation state
  - `StateGraph`: Controls the flow between different states

### 2. Tools (backend/tools/)
Each tool file implements specific infrastructure operations:
- `aws_tool.py`: AWS operations (using your AWS account)
- `k8s_tool.py`: Kubernetes cluster management
- `mongo_tool.py`: MongoDB database operations
- etc.

### 3. FastAPI Backend (backend/main.py)
- Provides REST API endpoints
- Handles streaming responses
- Manages WebSocket connections for real-time updates

### 4. Streamlit Frontend (streamlit_app.py)
- User interface for interacting with the chatbot
- Displays conversation history
- Shows tool execution status

## Available Tools

1. **Kubernetes**
   - Manage clusters, pods, services
   - View logs and status
   - Deploy applications

2. **MongoDB**
   - Create/delete databases and collections
   - Query data
   - Manage indexes

3. **MySQL**
   - Database administration
   - Query execution
   - User management

4. **Redis**
   - Key-value operations
   - Cache management
   - Pub/sub functionality

5. **RabbitMQ**
   - Queue management
   - Message publishing/consuming
   - Exchange configuration

6. **AWS** (using provided account)
   - Will be configured with personal credentials
   - Access will be restricted to necessary services
   - No need to install AWS CLI locally

## Usage Guide

1. Start the backend:
   ```bash
   cd backend
   uvicorn main:app --reload
   ```

2. Start the frontend:
   ```bash
   streamlit run streamlit_app.py
   ```

3. Access the UI at http://localhost:8501

4. Example queries:
   - "Show me all running pods in the Kubernetes cluster"
   - "Create a new MongoDB database named 'testdb'"
   - "Check the status of MySQL server"
   - "List all Redis keys matching pattern 'user:*'"

## Troubleshooting

### Common Issues

1. **Tool Not Found Errors**
   - Ensure the tool is installed correctly
   - Check if it's available in system PATH
   - Try running the tool command directly in terminal

2. **Permission Issues**
   - Make sure you have necessary permissions for each tool
   - Some tools might need sudo/admin access
   - Check service status if tool seems unresponsive

3. **Environment Issues**
   - Verify .env file is properly configured
   - Ensure virtual environment is activated
   - Check Python version compatibility

### Getting Help

1. Check the logs in the terminal running the backend
2. Look for specific error messages in the UI
3. Contact team lead for AWS-related issues
4. Refer to individual tool documentation for specific tool issues

## Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

## Code of Conduct

This project follows the [Contributor Covenant](https://www.contributor-covenant.org/version/2/0/code_of_conduct/) Code of Conduct.

## Security

For security issues, please email security@yourdomain.com instead of using the issue tracker.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [LangChain](https://github.com/langchain-ai/langchain) for the LLM framework
- [FastAPI](https://fastapi.tiangolo.com/) for the backend framework
- [Streamlit](https://streamlit.io/) for the frontend framework
- All our [contributors](../../graphs/contributors)

---

For any additional questions or issues, please [open an issue](../../issues/new) or contact the maintainers. 