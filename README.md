# TutorNet-AI

**Intelligent AI Agent Platform for TutorNet**

An advanced conversational AI system built with FastAPI, LangChain, and LangGraph, featuring sophisticated agent capabilities, quality validation, and comprehensive observability.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [Testing](#testing)
- [Configuration](#configuration)
- [Development](#development)
- [Technology Stack](#technology-stack)

---

## 🎯 Overview

TutorNet-AI is a production-ready agentic AI platform designed to provide intelligent, context-aware conversations with integrated tool usage, response quality validation, and comprehensive tracing. The system leverages state-of-the-art LLM capabilities while ensuring response quality through a sophisticated reflection agent architecture.

### Project Highlights

- **Test Coverage**: 91% overall coverage with 302 passing tests
- **Architecture**: Modular, scalable design with clear separation of concerns
- **Quality Assurance**: Automated reflection agent for response validation and improvement
- **Observability**: Integrated Langfuse tracing for monitoring and debugging
- **Production-Ready**: Comprehensive error handling, logging, and security features

---

## ✨ Key Features

### 🤖 Intelligent Agent System

- **ReAct Agent**: Tool-calling agent with reasoning and action capabilities
- **Reflection Agent**: Automated response quality validation and improvement
- **Multi-workflow Support**: Specialized prompts for different use cases (assistant, translator, censorship)
- **Session Management**: Persistent conversation memory with context preservation

### 🛠️ Tool Integration

- **Dynamic Tool Selection**: Validates and loads tools based on request
- **Course Search**: Find educational courses through external APIs
- **Tutor Search**: Discover available tutors
- **Extensible**: Easy to add new tools through standardized interface

### 📊 Quality & Observability

- **Reflection Loop**: Validates responses for hallucinations, errors, and quality issues
- **Langfuse Integration**: Comprehensive tracing and observability
- **Error Handling**: Structured error responses with detailed logging
- **Rate Limiting**: Configurable rate limiting for API protection

### 💬 Conversation Modes

1. **Chat Endpoint** (\`/api/conversation/chat\`): Non-streaming responses with full reflection support
2. **Streaming Endpoint** (\`/api/conversation\`): Server-sent events for real-time responses
3. **Memory Management**: Clear sessions and retrieve conversation history

---

## 🏗️ Architecture

### Core Components

\`\`\`
┌─────────────────────────────────────────────────────────────┐
│                        FastAPI Application                   │
├─────────────────────────────────────────────────────────────┤
│  API Layer                                                   │
│  ├── Conversation Endpoints (chat, streaming, management)   │
│  ├── Request/Response Models                                │
│  └── Error Handling Middleware                              │
├─────────────────────────────────────────────────────────────┤
│  Core Layer                                                  │
│  ├── LLM Factory (OpenAI, Qwen support)                    │
│  ├── Memory Manager (Session-based conversation history)   │
│  ├── Tool Registry (Dynamic tool loading)                  │
│  └── System Prompts (Workflow-specific templates)          │
├─────────────────────────────────────────────────────────────┤
│  Agent Layer                                                 │
│  ├── ReAct Agent (Tool-calling with LangGraph)             │
│  ├── Reflection Graph (Quality validation & improvement)   │
│  └── State Management                                       │
├─────────────────────────────────────────────────────────────┤
│  Utilities                                                   │
│  ├── Langfuse Config (Tracing & observability)             │
│  ├── Error Handling (Structured exception handling)        │
│  ├── Logging Config (Security & application logs)          │
│  └── Settings (Environment-based configuration)            │
└─────────────────────────────────────────────────────────────┘
\`\`\`

### Reflection Agent Flow

\`\`\`
User Query → LLM Response → Validation Node
                              ├── APPROVED → Return Response
                              ├── REJECT → Regeneration Node → New Response
                              └── Auto-Approve Errors → Return Error Message
\`\`\`

---

## �� Project Structure

\`\`\`
TutorNet-AI/
├── src/
│   ├── api/
│   │   └── conversation.py          # API endpoints for conversations
│   ├── core/
│   │   ├── function_tools.py        # Tool definitions and registry
│   │   ├── logging_config.py        # Logging configuration
│   │   ├── router.py                # API router setup
│   │   └── utils/
│   │       ├── agents/
│   │       │   ├── react_agent.py   # ReAct agent implementation
│   │       │   └── reflection_graph.py  # Reflection agent graph
│   │       ├── api_utils.py         # API utility functions
│   │       ├── error_handling.py    # Error handlers and middleware
│   │       ├── langfuse_config.py   # Langfuse tracing setup
│   │       ├── llm_factory.py       # LLM instance creation
│   │       ├── memory_manager.py    # Session memory management
│   │       ├── models.py            # Pydantic models
│   │       ├── settings.py          # Configuration settings
│   │       ├── streaming_handlers.py # SSE streaming handlers
│   │       └── system_prompts.py    # System prompt templates
│   └── main.py                      # FastAPI application entry
├── tests/
│   ├── conftest.py                  # Pytest fixtures
│   ├── test_conversation.py         # Conversation tests
│   ├── test_conversation_endpoints.py # Endpoint integration tests
│   ├── test_reflection_graph.py     # Reflection agent tests
│   └── [additional test files]
├── pyproject.toml                   # Project dependencies & config
└── README.md                        # This file
\`\`\`

---

## 🚀 Installation

### Prerequisites

- Python 3.13 or higher
- pip or poetry for dependency management
- OpenAI API key (or compatible LLM provider)

### Setup

1. **Clone the repository**

   \`\`\`bash
   git clone https://github.com/SWE5006/TutorNet-AI.git
   cd TutorNet-AI
   \`\`\`

2. **Create virtual environment**

   \`\`\`bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   \`\`\`

3. **Install dependencies**

   \`\`\`bash
   pip install -e .
   # or using poetry
   poetry install
   \`\`\`

4. **Configure environment variables**

   \`\`\`bash
   cp .env.example .env
   # Edit .env with your configuration
   \`\`\`

   Required variables:
   \`\`\`env
   OPENAI_API_KEY=your_openai_api_key
   OPENAI_MODEL_NAME=gpt-4-turbo-preview
   LANGFUSE_ENABLE=true
   LANGFUSE_PUBLIC_KEY=your_public_key
   LANGFUSE_SECRET_KEY=your_secret_key
   \`\`\`

---

## 💻 Usage

### Development Server

\`\`\`bash
# Using uvicorn directly
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Or using the VS Code task
# Run Task: "Start TutorNet-AI Development Server"
\`\`\`

### Production Deployment

\`\`\`bash
# Using gunicorn with uvicorn workers
gunicorn src.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Using Docker (if Dockerfile is available)
docker build -t tutornet-ai .
docker run -p 8000:8000 --env-file .env tutornet-ai
\`\`\`

### Quick Test

\`\`\`bash
curl -X POST "http://localhost:8000/foundation/api/conversation/chat" \\
  -H "Content-Type: application/json" \\
  -d '{
    "session_id": "test-session",
    "message": "Hello, how can you help me?",
    "workflow": "assistant",
    "temperature": 0.7
  }'
\`\`\`

---

## 🔌 API Endpoints

### Base URL: \`/foundation/api/conversation\`

#### 1. Chat (Non-Streaming)

\`\`\`http
POST /chat
Content-Type: application/json

{
  "session_id": "unique-session-id",
  "message": "Your question here",
  "workflow": "assistant",
  "temperature": 0.7,
  "tool_names": ["search_courses"],
  "reflection": true
}
\`\`\`

**Response:**
\`\`\`json
{
  "session_id": "unique-session-id",
  "message": "Your question here",
  "response": "AI response here",
  "workflow": "assistant",
  "temperature": 0.7,
  "tool_names": ["search_courses"],
  "reflection": {
    "improved": true,
    "original_response": "...",
    "improved_response": "...",
    "reflection_notes": "..."
  }
}
\`\`\`

#### 2. Conversation (Streaming)

\`\`\`http
POST /
Content-Type: application/json

{
  "session_id": "unique-session-id",
  "message": "Your question here",
  "workflow": "assistant"
}
\`\`\`

**Response:** Server-Sent Events (SSE) stream

#### 3. Clear Memory

\`\`\`http
POST /clear_memory
Content-Type: application/json

{
  "session_id": "session-to-clear"
}
\`\`\`

#### 4. Get History

\`\`\`http
POST /get_history
Content-Type: application/json

{
  "session_id": "session-id"
}
\`\`\`

**Response:**
\`\`\`json
{
  "session_id": "session-id",
  "history": "Human: Hello\\nAI: Hi there!..."
}
\`\`\`

---

## 🧪 Testing

### Run All Tests

\`\`\`bash
# Run all tests with coverage
pytest tests/ --cov=src --cov-report=html --cov-report=term

# Run specific test file
pytest tests/test_conversation_endpoints.py -v

# Run with coverage report
pytest tests/ --cov=src --cov-report=term-missing
\`\`\`

### Test Coverage

Current test coverage: **91%**

- \`conversation.py\`: 98% (126 statements, 2 missing)
- \`reflection_graph.py\`: 97% (100 statements, 3 missing)
- \`function_tools.py\`: 100%
- \`memory_manager.py\`: 100%
- \`api_utils.py\`: 100%
- \`llm_factory.py\`: 100%
- \`langfuse_config.py\`: 100%

**Total: 302 passing tests, 9 skipped**

### Code Quality

\`\`\`bash
# Format code
black src/

# Check code quality
flake8 src/

# Type checking (if configured)
mypy src/
\`\`\`

---

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| \`OPENAI_API_KEY\` | OpenAI API key | - | Yes |
| \`OPENAI_MODEL_NAME\` | Model to use | \`gpt-4-turbo-preview\` | No |
| \`QWEN_ENABLE\` | Enable Qwen models | \`false\` | No |
| \`LANGFUSE_ENABLE\` | Enable Langfuse tracing | \`false\` | No |
| \`LANGFUSE_PUBLIC_KEY\` | Langfuse public key | - | If enabled |
| \`LANGFUSE_SECRET_KEY\` | Langfuse secret key | - | If enabled |
| \`LOG_LEVEL\` | Logging level | \`INFO\` | No |
| \`CORS_ORIGINS\` | Allowed CORS origins | \`http://localhost:3000\` | No |

### Workflow Types

- **\`assistant\`**: General-purpose helpful assistant
- **\`translator\`**: Language translation tasks
- **\`censorship\`**: Content moderation with visual analysis
- **\`chat\`**: Default conversational mode

---

## 🛠️ Development

### VS Code Tasks

The project includes pre-configured VS Code tasks:

- **Start TutorNet-AI Development Server**: Run the FastAPI server
- **Install Dependencies**: Install project dependencies
- **Check Code Quality**: Run flake8 linting
- **Format Code**: Format code with black

### Adding New Tools

1. Define the tool in \`src/core/function_tools.py\`:

\`\`\`python
@tool
def my_new_tool(param: str) -> str:
    """Tool description for the LLM."""
    # Implementation
    return result

# Register the tool
available_tools["my_new_tool"] = my_new_tool
\`\`\`

2. Add tests in \`tests/test_function_tools.py\`

### Adding New Workflows

1. Add system prompt in \`src/core/utils/system_prompts.py\`:

\`\`\`python
WORKFLOW_PROMPTS["my_workflow"] = """
Your specialized system prompt here...
"""
\`\`\`

---

## 🔧 Technology Stack

### Core Framework
- **FastAPI**: Modern, high-performance web framework
- **Uvicorn**: ASGI server for async Python
- **Pydantic**: Data validation using Python type hints

### AI & LLM
- **LangChain**: LLM application framework
- **LangGraph**: Graph-based agent orchestration
- **OpenAI**: GPT models for conversation
- **Qwen**: Alternative LLM support

### Observability & Monitoring
- **Langfuse**: LLM tracing and observability
- **Python Logging**: Structured logging with security filters

### Testing & Quality
- **pytest**: Testing framework
- **pytest-cov**: Coverage reporting
- **pytest-asyncio**: Async test support
- **pytest-mock**: Mocking utilities
- **black**: Code formatting
- **flake8**: Code linting

### Storage & State
- **LangChain Memory**: Conversation history management
- **In-memory Sessions**: Fast session-based state

---

## 📊 Performance & Metrics

- **Response Time**: < 2s for non-streaming, real-time for streaming
- **Reflection Overhead**: ~500ms for quality validation
- **Test Suite Execution**: < 2s for 302 tests
- **Memory Footprint**: Minimal with efficient session management

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (\`git checkout -b feat/amazing-feature\`)
3. Commit your changes (\`git commit -m 'feat: add amazing feature'\`)
4. Push to the branch (\`git push origin feat/amazing-feature\`)
5. Open a Pull Request

### Commit Convention

Follow conventional commits:
- \`feat:\` New features
- \`fix:\` Bug fixes
- \`docs:\` Documentation changes
- \`test:\` Test additions or modifications
- \`refactor:\` Code refactoring
- \`chore:\` Maintenance tasks

---

## 📝 License

This project is part of the SWE5007 Capstone Project at Singapore Institute of Technology.

---

## 👥 Authors

- **Project Team**: SWE5006/TutorNet-AI
- **Course**: SWE5007 Capstone & Internship Project for SE32
- **Institution**: Singapore Institute of Technology

---

## 📞 Support

For issues, questions, or contributions, please:
- Open an issue on GitHub
- Contact the development team
- Refer to the documentation in \`/docs\` (if available)

---

**Built with ❤️ for TutorNet**
