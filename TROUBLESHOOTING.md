# Troubleshooting Guide: LangChain with OpenAI Integration

## Core Issues Encountered

### 1. OpenAI Version Conflict
The first error we hit was:
```
module 'openai' has no attribute 'error'
```
This happened because newer versions of OpenAI (v1.0+) changed their error handling structure. The solution was to use OpenAI v0.28.1 which is compatible with older LangChain versions.

### 2. LangChain Agent Method Error
We then encountered:
```
'AgentExecutor' object has no attribute 'invoke'
```
This occurred because we were using `agent.invoke()` when the correct method in this version is `agent.run()`. The agent methods changed between LangChain versions.

### Working Solution

#### 1. Package Versions
Use these exact versions in requirements.txt:
```
langchain==0.0.284
openai==0.28.1
python-dotenv==1.0.0
```

#### 2. Agent Initialization and Usage
```python
# Correct agent initialization
self.agent = initialize_agent(
    tools=self.tools,
    llm=self.llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    max_iterations=5,
    handle_parsing_errors=True
)

# Correct way to use the agent
result = self.agent.run(query)  # Use run() instead of invoke()
```

### Common Pitfalls to Avoid

1. **Version Mismatches:**
   - Don't mix OpenAI v1.0+ with older LangChain versions
   - Stick to OpenAI v0.28.1 with LangChain v0.0.284

2. **Method Calls:**
   - Use `agent.run()` instead of `agent.invoke()`
   - Don't try to pass complex dictionaries to `run()`, just pass the query string

3. **Environment Setup:**
   - Always load environment variables at the start:
     ```python
     from dotenv import load_dotenv
     load_dotenv()
     ```
   - Verify OPENAI_API_KEY is properly loaded before initializing LangChain

### Quick Debug Checklist
1. Check package versions match exactly
2. Ensure you're using `run()` not `invoke()`
3. Verify environment variables are loaded
4. Check agent initialization parameters

### Additional Notes
- If upgrading to newer versions, be aware that both the OpenAI API and LangChain methods will change significantly
- The older versions (OpenAI 0.28.1, LangChain 0.0.284) are more stable for this specific setup
- When debugging, enable verbose mode in agent initialization to see what's happening 