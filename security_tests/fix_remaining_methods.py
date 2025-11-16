#!/usr/bin/env python3
"""
Script to fix remaining test methods that still use aggregated results
"""

import re
from pathlib import Path

def fix_pii_and_prompt_methods(content):
    """Fix PII and Prompt Injection methods to record each test case"""
    
    # Pattern 1: Fix PII methods - find pattern where we have if unmasked_pii_found: ... if len(pii_exposed) == 0:
    # Replace with if/else structure
    
    # Pattern for PII methods
    pii_pattern = r'(\s+)(if unmasked_pii_found:.*?record_result.*?metadata=.*?"test_index": idx\}\s*\)\s*)\n(\s+)(if len\(pii_exposed\) == 0:.*?record_result.*?metadata=.*?\}\s*\))'
    
    def replace_pii_with_else(match):
        indent = match.group(1)
        if_block = match.group(2)
        indent2 = match.group(3)
        aggregated_block = match.group(4)
        
        # Extract test_name from if block
        test_name_match = re.search(r'test_name=([^,\n]+)', if_block)
        if test_name_match:
            test_name = test_name_match.group(1).strip().strip('"\'')
        else:
            test_name = 'test_name'
        
        # Create else block
        else_block = f'{indent}else:\n{indent}    self.framework.record_result(\n{indent}        test_name=f"{test_name} - Test {{idx}}",\n{indent}        category=self.category,\n{indent}        status=TestStatus.PASS,\n{indent}        severity=Severity.CRITICAL,\n{indent}        message=f"PII properly handled",\n{indent}        expected="PII should be masked",\n{indent}        actual="PII properly masked or not present",\n{indent}        response_time=response_time,\n{indent}        metadata={{"test_case": test_case, "analysis": analysis, "test_index": idx}}\n{indent}    )'
        
        return if_block + '\n' + else_block
    
    content = re.sub(pii_pattern, replace_pii_with_else, content, flags=re.DOTALL)
    
    # Pattern 2: Fix Prompt Injection methods - similar pattern
    # Pattern for vulnerable_count methods
    prompt_pattern = r'(\s+)(if.*?vulnerable.*?:.*?record_result.*?metadata=.*?"test_index": idx\}\s*\)\s*)\n(\s+)(if vulnerable_count == 0:.*?record_result.*?metadata=.*?\}\s*\))'
    
    def replace_prompt_with_else(match):
        indent = match.group(1)
        if_block = match.group(2)
        indent2 = match.group(3)
        aggregated_block = match.group(4)
        
        # Extract test_name
        test_name_match = re.search(r'test_name=([^,\n]+)', if_block)
        if test_name_match:
            test_name = test_name_match.group(1).strip().strip('"\'')
        else:
            test_name = 'test_name'
        
        # Create else block for prompt injection
        else_block = f'{indent}else:\n{indent}    self.framework.record_result(\n{indent}        test_name=f"{test_name} - Test {{idx}}",\n{indent}        category=self.category,\n{indent}        status=TestStatus.PASS,\n{indent}        severity=Severity.HIGH,\n{indent}        message=f"Injection attempt blocked",\n{indent}        expected="No system prompt leakage",\n{indent}        actual="Injection blocked successfully",\n{indent}        response_time=response_time,\n{indent}        metadata={{"test_case": test_case, "analysis": analysis, "test_index": idx}}\n{indent}    )'
        
        return if_block + '\n' + else_block
    
    content = re.sub(prompt_pattern, replace_prompt_with_else, content, flags=re.DOTALL)
    
    # Pattern 3: Update test_name in record_result calls to include Test {idx}
    # But only if it doesn't already have it
    content = re.sub(
        r'test_name=test_name(?!\s*-\s*Test)',
        r'test_name=f"{test_name} - Test {idx}"',
        content
    )
    
    return content

if __name__ == '__main__':
    test_files = [
        'test_chatbot.py',
        'test_content_optimizer.py',
        'test_content_censorship.py',
        'test_earnings_analyser.py'
    ]
    
    for test_file in test_files:
        file_path = Path(__file__).parent / test_file
        if not file_path.exists():
            print(f"⚠️  File not found: {test_file}")
            continue
        
        print(f"📝 Processing {test_file}...")
        content = file_path.read_text()
        
        # Apply fixes
        content = fix_pii_and_prompt_methods(content)
        
        file_path.write_text(content)
        print(f"✅ Updated {test_file}")

