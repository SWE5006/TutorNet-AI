#!/usr/bin/env python3
"""
Script to modify all test files to record each test case individually
instead of aggregating results by test method.
"""

import re
from pathlib import Path

def fix_test_method(content):
    """Fix a test method to record each test case"""
    
    # Pattern 1: Find "for test_case in test_cases:" and add enumerate
    content = re.sub(
        r'for\s+test_case\s+in\s+test_cases:',
        r'for idx, test_case in enumerate(test_cases, 1):',
        content
    )
    
    # Pattern 2: Find record_result calls that don't have test_index and add it
    # Also update test_name to include index
    def update_record_result(match):
        test_name_var = match.group(1) if match.group(1) else 'test_name'
        # Check if already has Test {idx}
        if 'Test {idx}' not in match.group(0):
            # Replace test_name=test_name with test_name=f"{test_name} - Test {idx}"
            result = match.group(0)
            result = re.sub(
                rf'test_name={test_name_var}',
                rf'test_name=f"{test_name_var} - Test {{idx}}"',
                result
            )
            # Add test_index to metadata if not present
            if 'test_index' not in result:
                result = re.sub(
                    r'metadata=\{(.*?)\}',
                    r'metadata={\1, "test_index": idx}',
                    result
                )
            return result
        return match.group(0)
    
    # Pattern 3: Find the final aggregated record_result and remove it, 
    # but add else clause for PASS cases
    # This is complex, so we'll handle it manually for each file
    
    return content

def add_else_clause_for_pass(content):
    """Add else clause to record PASS results for each test case"""
    
    # Pattern: Find record_result in if issue_found block, then find the closing if len(issues_detected) == 0 block
    # and add else clause before it
    
    # This is too complex for regex. Let's use a different approach:
    # Find patterns like:
    #   if issue_found:
    #       ... record_result FAIL ...
    #   
    #   if len(issues_detected) == 0:
    #       record_result PASS (aggregated)
    
    # Replace with:
    #   if issue_found:
    #       ... record_result FAIL ...
    #   else:
    #       record_result PASS (individual)
    
    # But we need to be careful about the structure. Let's do this manually per file.
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
        content = fix_test_method(content)
        
        # Note: The else clause addition needs to be done manually
        # as it requires understanding the specific structure of each method
        
        file_path.write_text(content)
        print(f"✅ Updated {test_file}")

