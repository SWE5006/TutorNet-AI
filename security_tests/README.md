# 🔒 TutorNet AI Security Testing Framework

Comprehensive security testing framework for TutorNet 2.0 AI Agent system.

## 📋 Overview

This security testing framework implements comprehensive security tests based on **OWASP LLM Top 10** security risks and **NIST Cybersecurity Framework** best practices.

The framework is designed to run against **local AI services** running on `http://localhost:8002`.

## 🧪 Test Categories

### 1. Prompt Injection (5 tests)
- **Direct Prompt Injection**: Tests direct attempts to override system instructions
- **Indirect Prompt Injection**: Tests context-based injection attempts
- **Jailbreaking Attempts**: Tests jailbreaking techniques
- **System Prompt Leakage**: Tests attempts to extract system prompts
- **Instruction Override**: Tests attempts to override instructions

### 2. Output Handling (4 tests)
- **XSS Injection**: Tests for XSS vulnerabilities in output
- **SQL Injection**: Tests for SQL injection patterns in output
- **Sensitive Data Exposure**: Tests for sensitive data leakage
- **Malicious Code Output**: Tests for malicious code generation

### 3. PII Detection (4 tests)
- **Email Detection**: Tests email address handling
- **Phone Number Detection**: Tests phone number handling
- **Credit Card Detection**: Tests credit card number handling
- **SSN Detection**: Tests SSN handling

### 4. Tool Security (4 tests)
- **Unauthorized Tool Access**: Tests unauthorized tool access attempts
- **Input Validation**: Tests input validation for tool parameters
- **Tool Permission Bypass**: Tests permission bypass attempts
- **Tool Execution Abuse**: Tests tool execution abuse scenarios

### 5. Red Team Testing (4 phases)
- **Phase 1: Reconnaissance**: API discovery and system analysis
- **Phase 2: Vulnerability Assessment**: Prompt injection and PII extraction
- **Phase 3: Exploitation**: System prompt leakage and unauthorized tool execution
- **Phase 4: Reporting**: Vulnerability report with CVSS scores

## 🚀 Quick Start

### Prerequisites

```bash
# Ensure AI service is running locally
# Default: http://localhost:8002/foundation/api/conversation/chat

# Install dependencies
cd TutorNet-AI
poetry install

# Or with pip
pip install httpx fastapi
```

### Running Tests

#### Basic Usage (Local Service)

```bash
# Run all tests against local AI service (default)
python security_tests/run_security_tests.py
```

The default configuration connects to:
- **URL**: `http://localhost:8002/foundation/api/conversation/chat`
- **Output**: `./test_results/`

#### Advanced Usage

```bash
# Run with custom AI service URL (if different port)
python security_tests/run_security_tests.py \
    --url http://localhost:8002/foundation/api/conversation/chat

# Run with custom output directory
python security_tests/run_security_tests.py \
    --output ./my_test_results

# Run with authorization token (if required)
python security_tests/run_security_tests.py \
    --token "Bearer your-token-here"

# Run with specific workflow
python security_tests/run_security_tests.py \
    --workflow assistant

# Run quietly (less output)
python security_tests/run_security_tests.py --quiet
```

### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--url` | AI service URL | `http://localhost:8002/foundation/api/conversation/chat` |
| `--output` | Output directory for test results | `./test_results` |
| `--token` | Authorization token (optional) | `None` |
| `--workflow` | Workflow type | `general` |
| `--temperature` | LLM temperature | `0.7` |
| `--timeout` | Request timeout in seconds | `30` |
| `--quiet` | Run quietly (less verbose output) | `False` |

## 📊 Test Results

### Output Files

After running tests, you'll find:

1. **JSON Report**: `security_test_report_<timestamp>.json`
   - Complete test results in JSON format
   - Includes all test details, responses, and metadata
   - Suitable for automated processing

2. **Markdown Summary**: `security_test_summary_<timestamp>.md`
   - Human-readable summary report in English
   - Includes test statistics, results table, and vulnerability analysis
   - Suitable for documentation and review

### Report Structure

```json
{
  "timestamp": "2025-11-03T12:00:00",
  "config": {
    "ai_service_url": "http://localhost:8002/foundation/api/conversation/chat",
    "workflow": "general",
    "temperature": 0.7
  },
  "summary": {
    "total_tests": 17,
    "by_status": {
      "PASS": 15,
      "FAIL": 2
    },
    "by_category": {
      "Prompt Injection": 5,
      "Output Handling": 4,
      "PII Detection": 4,
      "Tool Security": 4
    },
    "by_severity": {
      "CRITICAL": 0,
      "HIGH": 2,
      "MEDIUM": 10,
      "LOW": 5
    },
    "pass_rate": "88.2%"
  },
  "results": [...]
}
```

### Markdown Report Contents

The Markdown report includes:
- Executive Summary with key metrics
- Test Results by Category
- Test Results by Status
- Test Results by Severity
- Detailed Test Results Table
- Vulnerability Analysis (for failed tests)
- Recommendations for remediation

## 🔧 Configuration

### Test Configuration

You can customize test behavior by modifying `TestConfig`:

```python
from security_tests.test_framework import TestConfig, SecurityTestFramework

config = TestConfig(
    ai_service_url="http://localhost:8002/foundation/api/conversation/chat",
    output_dir="./test_results",
    authorization_token="Bearer your-token",  # Optional
    workflow="assistant",
    temperature=0.7,
    timeout=30,
    verbose=True
)
```

### Custom Test Execution

```python
import asyncio
from security_tests.test_framework import SecurityTestFramework, TestConfig

async def main():
    config = TestConfig(
        ai_service_url="http://localhost:8002/foundation/api/conversation/chat",
        verbose=True
    )
    
    async with SecurityTestFramework(config) as framework:
        # Run all tests
        await framework.run_all_tests()
        
        # Or run specific test categories
        await framework.run_prompt_injection_tests()
        await framework.run_output_handling_tests()
        await framework.run_pii_detection_tests()
        await framework.run_tool_security_tests()
        await framework.run_red_team_tests()

if __name__ == "__main__":
    asyncio.run(main())
```

## 📝 Test Status and Severity

### Test Status

- **PASS**: Test passed - no vulnerabilities detected
- **FAIL**: Test failed - vulnerabilities detected
- **WARN**: Test warning - potential issues detected
- **SKIP**: Test skipped - not applicable
- **ERROR**: Test error - execution error occurred

### Severity Levels

- **CRITICAL**: Critical vulnerabilities requiring immediate attention
- **HIGH**: High severity vulnerabilities requiring prompt attention
- **MEDIUM**: Medium severity vulnerabilities requiring attention
- **LOW**: Low severity issues or informational findings
- **INFO**: Informational findings

## 🛡️ Security Best Practices

### Before Running Tests

1. **Ensure AI service is running locally** on `localhost:8002`
2. **Use test environment** - don't run against production
3. **Review test prompts** - some tests may generate malicious content
4. **Monitor service logs** - watch for unexpected behavior
5. **Check network connectivity** - ensure localhost is accessible

### After Running Tests

1. **Review test results** carefully, especially the Markdown report
2. **Address vulnerabilities** based on severity (CRITICAL → HIGH → MEDIUM)
3. **Update security controls** as needed
4. **Re-run tests** after fixes to verify remediation
5. **Document findings** in security documentation

## 📚 Test Implementation Details

### Prompt Injection Tests

Tests attempt to:
- Override system instructions
- Extract system prompts
- Bypass safety controls
- Reveal internal configuration

**Expected Behavior**: All injection attempts should be blocked or ignored.

### Output Handling Tests

Tests verify:
- XSS sanitization
- SQL injection prevention
- Sensitive data handling
- Malicious code prevention

**Expected Behavior**: Outputs should be sanitized and safe.

### PII Detection Tests

Tests check:
- Email address handling
- Phone number handling
- Credit card number handling
- SSN handling

**Expected Behavior**: PII should be redacted or masked in outputs.

### Tool Security Tests

Tests validate:
- Tool access control
- Input validation
- Permission enforcement
- Execution abuse prevention

**Expected Behavior**: Unauthorized tools should be rejected, inputs validated.

### Red Team Tests

Simulates:
- Reconnaissance activities
- Vulnerability discovery
- Exploitation attempts
- Comprehensive reporting

**Expected Behavior**: Vulnerabilities should be detected and reported.

## 🐛 Troubleshooting

### Common Issues

1. **Connection Errors**
   ```
   Error: Connection refused
   ```
   - Check AI service is running: `curl http://localhost:8002/foundation/api/conversation/chat`
   - Verify URL is correct
   - Check firewall settings

2. **Timeout Errors**
   ```
   Error: Request timeout
   ```
   - Increase timeout value: `--timeout 60`
   - Check service performance
   - Verify service is responsive

3. **Authentication Errors**
   ```
   Error: 401 Unauthorized
   ```
   - Verify token is valid
   - Check token format: `Bearer <token>`
   - Ensure token has required permissions

4. **Localhost Not Resolving**
   ```
   Error: Cannot resolve localhost
   ```
   - Try `127.0.0.1` instead of `localhost`
   - Check `/etc/hosts` file
   - Verify network configuration

## 🔍 Example Test Run

```bash
$ python security_tests/run_security_tests.py

================================================================================
🔒 TutorNet AI Security Testing Framework
================================================================================

📋 Running Test Categories:
  1. Prompt Injection (5 tests)
  2. Output Handling (4 tests)
  3. PII Detection (4 tests)
  4. Tool Security (4 tests)
  5. Red Team Testing (4 phases)

🔍 Running Prompt Injection Tests...
✅ Completed Prompt Injection Tests

🔍 Running Output Handling Tests...
✅ Completed Output Handling Tests

🔍 Running PII Detection Tests...
✅ Completed PII Detection Tests

🔍 Running Tool Security Tests...
✅ Completed Tool Security Tests

🔍 Running Red Team Testing Tests...
✅ Completed Red Team Testing Tests

📊 Reports generated:
  - JSON: ./test_results/security_test_report_20251103_120000.json
  - Markdown: ./test_results/security_test_summary_20251103_120000.md

✅ Security Testing Complete!
```

## 📄 License

This security testing framework is part of the TutorNet 2.0 project.

## 🤝 Contributing

When adding new tests:

1. Follow existing test structure
2. Add appropriate test cases
3. Update this README
4. Include test metadata
5. Test your tests!

## 📞 Support

For issues or questions:
- Check test logs in output directory
- Review test results (JSON and Markdown)
- Consult security documentation
- Verify AI service is running correctly

---

**Last Updated**: 2025-11-03  
**Version**: 1.0.0  
**Default AI Service**: `http://localhost:8002/foundation/api/conversation/chat`
