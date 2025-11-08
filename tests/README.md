# Test Suite for TutorNet-AI

This directory contains the unit tests for the TutorNet-AI project.

## Overview

- **Total Tests**: 66 passing tests ✅
- **Overall Coverage**: 55%
- **Modules with 100% Coverage**: function_tools

## Structure

- `conftest.py` - Shared pytest fixtures and test configuration
- `test_function_tools.py` - Tests for the function tool wrappers (11 tests, **100% coverage** ✅)
- `test_conversation.py` - Tests for the conversation API endpoints and helper functions (27 tests)
- `test_system_prompts.py` - Tests for system prompt generation (13 tests, **88% coverage**)
- `test_settings.py` - Tests for settings configuration (15 tests, **88% coverage**)

## Running Tests

### Run all tests
```bash
poetry run pytest tests/ -v
```

### Run with coverage
```bash
poetry run pytest tests/ --cov=src --cov-report=html
```

### Run specific test file
```bash
poetry run pytest tests/test_function_tools.py -v
```

### Run specific test class or method
```bash
poetry run pytest tests/test_function_tools.py::TestSearchTutorService -v
poetry run pytest tests/test_conversation.py::TestHelperFunctions::test_get_session_memory_new_session -v
```

## Test Coverage

Current test coverage focuses on:

### Function Tools (`test_function_tools.py`)
- ✅ Search tutor service (success and error cases)
- ✅ Search course service (success, empty results, errors)
- ✅ Get course by user ID
- ✅ Get course details (success and not found)
- ✅ Place order (success and failure)

### Conversation API (`test_conversation.py`)
- ✅ Request models validation
- ✅ Helper functions (LLM params, session memory, tool validation, error messages)
- ✅ Message preparation and context saving
- ✅ API endpoints (clear memory, get history)

## Fixtures

Available fixtures in `conftest.py`:
- `mock_settings` - Mocked settings configuration
- `mock_wrapper_config` - Authorization config for API calls
- `sample_conversation_request` - Sample conversation request data
- `mock_llm_response` - Mocked LLM response
- `mock_tool_response` - Mocked tool API response
- `mock_session_memory` - Mocked conversation memory
- `setup_test_env` - Environment setup for tests

## Coverage Report

After running tests with coverage, open `htmlcov/index.html` in your browser to view the detailed coverage report.

## Dependencies

Testing dependencies are managed through Poetry:
- pytest ^8.3.0
- pytest-asyncio ^0.24.0
- pytest-cov ^5.0.0
- pytest-mock ^3.14.0
- httpx ^0.28.1

## Adding New Tests

1. Create a new test file following the naming convention `test_*.py`
2. Import necessary fixtures from `conftest.py`
3. Use the `Test*` class naming convention for test classes
4. Use the `test_*` naming convention for test methods
5. Add appropriate docstrings explaining what each test verifies
6. Use mocking for external dependencies (HTTP requests, database calls, etc.)

## Best Practices

- **Isolate tests**: Each test should be independent and not rely on other tests
- **Use fixtures**: Leverage pytest fixtures for reusable test data and setup
- **Mock external calls**: Use `unittest.mock` to mock HTTP requests and external APIs
- **Clear assertions**: Use descriptive assertion messages
- **Test both success and failure**: Cover both happy paths and error scenarios
- **Keep tests fast**: Use mocking to avoid real API calls or database operations
