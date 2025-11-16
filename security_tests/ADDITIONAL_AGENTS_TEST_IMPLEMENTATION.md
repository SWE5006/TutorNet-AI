# Additional AI Agents Test Implementation

## Overview

Implemented comprehensive security testing for three additional AI agents:
1. **Chatbot (Assistant)** - `test_chatbot.py`
2. **Content Optimizer** - `test_content_optimizer.py`
3. **Content Censorship** - `test_content_censorship.py`

---

## Test Files Created

### 1. `test_chatbot.py` - Chatbot (Assistant) Tests
- **Workflow**: `assistant`
- **Total Tests**: 80 test cases
- **Test Categories**:
  - Output Handling - XSS (5 tests)
  - Output Handling - SQL (5 tests)
  - Output Handling - Sensitive Data (5 tests)
  - Output Handling - Malicious Code (5 tests)
  - PII Detection - Email (5 tests)
  - PII Detection - Phone (5 tests)
  - PII Detection - NRIC (5 tests)
  - Prompt Injection - Direct (5 tests)
  - Prompt Injection - Indirect (5 tests)
  - Prompt Injection - Jailbreaking (5 tests)
  - Prompt Injection - Leakage (5 tests)
  - Prompt Injection - Override (5 tests)
  - Tool Security - Unauthorized (5 tests)
  - Tool Security - Input Validation (5 tests)
  - Tool Security - Permission Bypass (5 tests)
  - Tool Security - Execution Abuse (5 tests)

### 2. `test_content_optimizer.py` - Content Optimizer Tests
- **Workflow**: `content-optimizer`
- **Total Tests**: 15 test cases
- **Test Categories**:
  - Prompt Injection (5 tests)
  - Output Handling - XSS (1 test)
  - Output Handling - SQL (1 test)
  - Output Handling - Malicious Code (1 test)
  - Output Handling - HTML Handlers (1 test)
  - PII Detection - Email (1 test)
  - PII Detection - Phone (1 test)
  - PII Detection - NRIC (1 test)
  - Content Security - Profanity Bypass (1 test)
  - Content Security - Threat Preservation (1 test)
  - Content Security - Injection via Content (1 test)
  - Content Security - Malicious Input (1 test)

### 3. `test_content_censorship.py` - Content Censorship Tests
- **Workflow**: `censorship`
- **Total Tests**: 17 test cases
- **Test Categories**:
  - Prompt Injection (5 tests)
  - Output Handling - XSS (1 test)
  - Output Handling - SQL (1 test)
  - Output Handling - Malicious Code (1 test)
  - Output Handling - Sensitive Data (1 test)
  - PII Detection - Email (1 test)
  - PII Detection - Phone (1 test)
  - PII Detection - NRIC (1 test)
  - Content Safety - Political Content (1 test)
  - Content Safety - Threats (1 test)
  - Content Safety - Negative Feedback (1 test)
  - Content Safety - Injection via Content (1 test)
  - Content Safety - Image Validation (1 test)

---

## Integration

### Test Framework Updates
- Added `run_chatbot_tests()` method to `test_framework.py`
- Added `run_content_optimizer_tests()` method to `test_framework.py`
- Added `run_content_censorship_tests()` method to `test_framework.py`
- Updated `run_all_tests()` to include all three new test suites

### Test Execution
All tests are automatically included when running:
```bash
python security_tests/run_security_tests.py \
  --url http://localhost:8002/foundation/api/conversation/chat \
  --output test_results
```

---

## Test Case Details

### Chatbot Tests (80 tests)

#### Output Handling Tests
- **XSS**: Tests for `<script>`, `onclick`, `onerror`, `onload`, `<iframe>` patterns
- **SQL**: Tests for `SELECT`, `DROP TABLE`, `UNION SELECT`, `DELETE` patterns
- **Sensitive Data**: Tests for API keys, passwords, connection strings, tokens
- **Malicious Code**: Tests for `os.remove`, `rm -rf`, `eval()`, `exec()`, `subprocess`

#### PII Detection Tests
- **Email**: Tests masking of email addresses in various formats
- **Phone**: Tests masking of Singapore 8-digit phone numbers
- **NRIC/FIN**: Tests masking of Singapore NRIC/FIN numbers

#### Prompt Injection Tests
- **Direct**: Direct attempts to reveal system prompt
- **Indirect**: Indirect attempts via context manipulation
- **Jailbreaking**: Attempts to bypass safety restrictions
- **Leakage**: Attempts to extract system prompt details
- **Override**: Attempts to override system instructions

#### Tool Security Tests
- **Unauthorized**: Attempts to access unauthorized tools
- **Input Validation**: Malicious input in tool parameters
- **Permission Bypass**: Attempts to bypass permission checks
- **Execution Abuse**: Rate limiting and abuse prevention

### Content Optimizer Tests (15 tests)

#### Prompt Injection
- Direct, indirect, jailbreaking, leakage, and override attempts

#### Output Handling
- XSS, SQL, malicious code, and HTML handler sanitization

#### PII Detection
- Email, phone, and NRIC/FIN masking in optimized content

#### Content Security
- Profanity bypass prevention
- Threat preservation prevention
- Injection via content prevention
- Malicious input sanitization

### Content Censorship Tests (17 tests)

#### Prompt Injection
- Direct, indirect, jailbreaking, leakage, and override attempts

#### Output Handling
- XSS, SQL, malicious code, and sensitive data sanitization

#### PII Detection
- Email, phone, and NRIC/FIN masking in review responses

#### Content Safety
- Political content detection
- Threat detection
- Negative feedback handling (should be allowed)
- Injection via content prevention
- Image validation

---

## Test Results Format

Each test category records:
- **Test Name**: Category and subcategory
- **Status**: PASS, FAIL, WARN, SKIP
- **Severity**: CRITICAL, HIGH, MEDIUM, LOW
- **Message**: Summary of test results
- **Expected**: Expected behavior
- **Actual**: Actual behavior observed
- **Response Time**: Time taken for test execution
- **Metadata**: Test case details and analysis

---

## Running Individual Test Suites

### Run Only Chatbot Tests
```python
import asyncio
from security_tests.test_framework import SecurityTestFramework, TestConfig
from security_tests.test_chatbot import ChatbotTests

async def main():
    config = TestConfig(
        ai_service_url="http://localhost:8002/foundation/api/conversation/chat",
        output_dir="./test_results"
    )
    
    async with SecurityTestFramework(config) as framework:
        tester = ChatbotTests(framework)
        await tester.run_all()

asyncio.run(main())
```

### Run Only Content Optimizer Tests
```python
from security_tests.test_content_optimizer import ContentOptimizerTests
# ... same pattern as above
```

### Run Only Content Censorship Tests
```python
from security_tests.test_content_censorship import ContentCensorshipTests
# ... same pattern as above
```

---

## Test Coverage Summary

| AI Agent | Workflow | Test Cases | Status |
|----------|----------|------------|--------|
| **Chatbot** | `assistant` | 80 | ✅ Implemented |
| **Content Optimizer** | `content-optimizer` | 15 | ✅ Implemented |
| **Content Censorship** | `censorship` | 17 | ✅ Implemented |
| **Earnings Analyser** | `earnings-analyser` | 20 | ✅ Implemented |
| **Total** | | **132** | ✅ Complete |

---

## OWASP LLM Top 10 Risk Mapping

| Test Category | OWASP Risk | Description |
|--------------|-----------|-------------|
| Prompt Injection | LLM01 | Prompt Injection |
| Output Handling | LLM02 | Insecure Output Handling |
| PII Detection | LLM03, LLM06 | Training Data Poisoning / Sensitive Information Disclosure |
| Tool Security | LLM07 | Insecure Plugin Design |
| Content Security | LLM02, LLM03 | Insecure Output Handling / Training Data Poisoning |

---

## Files Modified

1. **`security_tests/test_chatbot.py`**: New test file with 80 test cases
2. **`security_tests/test_content_optimizer.py`**: New test file with 15 test cases
3. **`security_tests/test_content_censorship.py`**: New test file with 17 test cases
4. **`security_tests/test_framework.py`**: Added three new test runner methods

---

## Next Steps

1. ✅ All three test suites implemented
2. ✅ Integrated into test framework
3. ✅ Ready for execution

**Status**: ✅ Complete and ready for production use

---

**Last Updated**: 2025-11-14  
**Maintainer**: TutorNet Security Team

