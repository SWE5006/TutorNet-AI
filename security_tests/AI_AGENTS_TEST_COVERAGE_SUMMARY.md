# TutorNet AI Agents Security Test Coverage Summary

## Overview

TutorNet has **4 AI agents** designed for different purposes. This document summarizes each agent's functionality and security test coverage.

---

## AI Agents Summary

### 1. Chatbot (Assistant) - `assistant` ✅
- **Purpose:** Course discovery and tutor matching
- **Functionality:**
  - Search for tutors and courses
  - Get course details and variations
  - Place orders for course purchases
  - Guide users through the purchase workflow
- **Tools:** `search_tutor`, `search_course`, `get_course_by_userid`, `get_course_details`, `place_order`
- **Test Coverage:** ✅ **80 test cases** (Complete)
  - Prompt Injection: 5 test cases
  - Output Handling: 4 test cases
  - PII Detection: 3 test cases
  - Tool Security: 4 test cases
  - Red Team Testing: Multiple scenarios
- **Status:** Fully tested

### 2. Content Optimizer (Rewrite/Rephrase Helper) - `content-optimizer` ⚠️
- **Purpose:** Rewrite and refine user-generated activity posts
- **Functionality:**
  - Remove dirty words, threats, and offensive expressions
  - Preserve authentic emotions and negative feedback (if constructive)
  - Enhance readability, grammar, and structure
  - Maintain professionalism while keeping messages relatable
- **Tools:** None (text processing only)
- **Test Coverage:** ⚠️ **15 test cases** (Newly added)
  - Prompt Injection: 5 test cases (CO-1.1 to CO-1.5)
  - Output Handling: 4 test cases (CO-2.1 to CO-2.4)
  - PII Detection: 3 test cases (CO-3.1 to CO-3.3)
  - Content Filtering Security: 3 test cases (CO-4.1 to CO-4.3)
- **Status:** Test cases defined, ready for implementation

### 3. Content Censorship (Content Review) - `censorship` ⚠️
- **Purpose:** Review content (text + images) for safety and compliance
- **Functionality:**
  - Detect political content, threats, violence, explicit material
  - Allow honest negative feedback (if respectful)
  - Review both text and images
  - Return boolean validation result with explanation
- **Tools:** Image URL retrieval and analysis
- **Test Coverage:** ⚠️ **17 test cases** (Newly added)
  - Prompt Injection: 5 test cases (CS-1.1 to CS-1.5)
  - Output Handling: 4 test cases (CS-2.1 to CS-2.4)
  - PII Detection: 3 test cases (CS-3.1 to CS-3.3)
  - Content Review Security: 5 test cases (CS-4.1 to CS-4.5)
- **Status:** Test cases defined, ready for implementation

### 4. Earnings Analyser (Revenue Analyzer) - `earnings-analyser` ⚠️
- **Purpose:** Analyze performance data and provide revenue optimization strategies
- **Functionality:**
  - Process earnings data, revenue trends, course performance
  - Identify underlying trends and issues
  - Deliver 3-5 concrete, actionable strategies
  - Focus on revenue, retention, course quality, and growth
- **Tools:** None (data analysis only)
- **Special Note:** This workflow is **not directly interactive** - frontend automatically constructs structured prompts with analytics data. Users click "Refresh" but don't type messages.
- **Test Coverage:** ⚠️ **20 test cases** (Newly added)
  - Prompt Injection: 5 test cases (EA-1.1 to EA-1.5)
  - Output Handling: 4 test cases (EA-2.1 to EA-2.4)
  - PII Detection: 4 test cases (EA-3.1 to EA-3.4) - *Includes real-world data scenarios*
  - Data Analysis Security: 7 test cases (EA-4.1 to EA-4.7) - *Includes injection via data fields*
- **Status:** Test cases defined, ready for implementation
- **Testing Approach:** Simulate frontend-generated prompts with realistic structured data, test malicious data injection scenarios

---

## Test Coverage Summary

| AI Agent | Workflow | Test Cases | Status |
|----------|----------|------------|--------|
| **Chatbot** | `assistant` | 80 | ✅ Complete |
| **Content Optimizer** | `content-optimizer` | 15 | ⚠️ Defined |
| **Content Censorship** | `censorship` | 17 | ⚠️ Defined |
| **Earnings Analyser** | `earnings-analyser` | 20 | ⚠️ Defined |
| **Total** | | **132** | |

---

## Test Categories by Workflow

### Common Test Categories (All Workflows)
1. **Prompt Injection** (5 test cases per workflow)
   - Direct Injection
   - Indirect Injection
   - Jailbreaking Attempts
   - System Prompt Leakage
   - Instruction Override

2. **Output Handling** (4 test cases per workflow)
   - XSS Injection in Output
   - SQL Injection in Output
   - Sensitive Data Disclosure
   - Malicious Code Output

3. **PII Detection** (3 test cases per workflow)
   - Email Leakage
   - Phone Leakage
   - NRIC/FIN Leakage

### Workflow-Specific Test Categories

#### Chatbot (Assistant)
- **Tool Security** (4 test cases)
  - Unauthorized Tool Access
  - Malicious Tool Input
  - Tool Permission Bypass
  - Tool Execution Abuse

#### Content Optimizer
- **Content Filtering Security** (3 test cases)
  - Dirty Words Bypass Attempt
  - Threat Preservation Attempt
  - Injection via Content
  - Malicious Content in Input

#### Content Censorship
- **Content Review Security** (5 test cases)
  - Political Content Detection
  - Threat Detection
  - Negative Feedback (Allowed)
  - Injection via Review Request
  - Image URL Validation

#### Earnings Analyser
- **Data Analysis Security** (7 test cases)
  - Injection via Course Title
  - Injection via Student Name
  - XSS in Analytics Data
  - SQL Injection in Data Fields
  - Data Exfiltration Request
  - Malicious Code in Revenue Data
  - System Prompt Leakage via Data

---

## OWASP LLM Top 10 Risk Mapping

| OWASP Risk | Description | Test Coverage |
|------------|-------------|---------------|
| **LLM01: Prompt Injection** | Direct and indirect prompt injection attacks | ✅ All 4 workflows (5 tests each) |
| **LLM02: Insecure Output Handling** | XSS, SQL injection, malicious code in outputs | ✅ All 4 workflows (4 tests each) |
| **LLM03: Training Data Poisoning** | PII leakage and data exposure | ✅ All 4 workflows (3 tests each) |
| **LLM04: Model Denial of Service** | Rate limiting and abuse prevention | ✅ All 4 workflows (covered) |
| **LLM05: Supply Chain Vulnerabilities** | Content review and validation | ✅ Censorship workflow (5 tests) |
| **LLM06: Sensitive Information Disclosure** | Financial and personal data protection | ✅ Earnings Analyser (5 tests) |
| **LLM07: Insecure Plugin Design** | Tool security and access control | ✅ Chatbot workflow (4 tests) |
| **LLM08: Excessive Agency** | Content filtering and moderation | ✅ Content Optimizer (3 tests) |
| **LLM09: Overreliance** | Red team testing and adversarial scenarios | ✅ All workflows (covered) |
| **LLM10: Model Theft** | System prompt leakage prevention | ✅ All workflows (covered) |

---

## Test Implementation Status

### ✅ Completed
- **Chatbot (assistant):** 80 test cases fully implemented and tested

### ⚠️ Defined (Ready for Implementation)
- **Content Optimizer:** 15 test cases defined in `SECURITY_TEST_PAYLOADS_ADDITIONAL_WORKFLOWS.md`
- **Content Censorship:** 17 test cases defined in `SECURITY_TEST_PAYLOADS_ADDITIONAL_WORKFLOWS.md`
- **Earnings Analyser:** 20 test cases defined in `SECURITY_TEST_PAYLOADS_ADDITIONAL_WORKFLOWS.md`
  - *Note: Includes real-world data injection scenarios for non-interactive workflow*

### 📋 Next Steps
1. Implement test cases for Content Optimizer workflow
2. Implement test cases for Content Censorship workflow
3. Implement test cases for Earnings Analyser workflow
4. Integrate all test cases into automated test suite
5. Run comprehensive security test suite across all workflows

---

## Session ID Format by Workflow

| Workflow | Session ID Format | Example |
|----------|------------------|---------|
| `assistant` | `chat_{user_id}_{timestamp}` | `chat_123_1699123456789` |
| `content-optimizer` | `rewrite_{user_id}_{timestamp}` | `rewrite_123_1699123456789` |
| `censorship` | `review_{user_id}_{timestamp}` | `review_123_1699123456789` |
| `earnings-analyser` | `suggestions_{user_id}_{timestamp}` | `suggestions_123_1699123456789` |

---

## API Endpoint

All workflows use the same endpoint:
```
POST /foundation/api/conversation/chat
```

Request format:
```json
{
  "message": "test message",
  "session_id": "workflow_specific_session_id",
  "workflow": "assistant|content-optimizer|censorship|earnings-analyser",
  "temperature": 0.7,
  "tool_names": [] // Only for assistant workflow
}
```

---

**Last Updated:** 2025-11-12  
**Maintainer:** TutorNet Security Team  
**Documentation:** 
- Main test payloads: `SECURITY_TEST_PAYLOADS.md`
- Additional workflows: `SECURITY_TEST_PAYLOADS_ADDITIONAL_WORKFLOWS.md`

