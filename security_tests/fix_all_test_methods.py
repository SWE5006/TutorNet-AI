#!/usr/bin/env python3
"""
Script to add else clauses for PASS results in all test methods
"""

import re
from pathlib import Path

def fix_remaining_methods(content):
    """Fix remaining methods that need else clauses"""
    
    # Pattern: Find blocks like:
    #   if issue_found:
    #       ... record_result FAIL ...
    #   
    #   if len(issues_detected) == 0:
    #       record_result PASS (aggregated)
    #
    # Replace with:
    #   if issue_found:
    #       ... record_result FAIL ...
    #   else:
    #       record_result PASS (individual)
    #   (remove the aggregated block)
    
    # More specific pattern for test_chatbot.py style
    pattern = r'(\s+)(if issue_found:.*?record_result.*?metadata=.*?"test_index": idx\}\s*\)\s*)\n(\s+)(if len\(issues_detected\) == 0:.*?record_result.*?metadata=.*?\}\s*\)\s*)'
    
    def replace_with_else(match):
        indent = match.group(1)
        if_block = match.group(2)
        indent2 = match.group(3)
        aggregated_block = match.group(4)
        
        # Extract test_name from the if block
        test_name_match = re.search(r'test_name=f?"([^"]+)"', if_block)
        if test_name_match:
            test_name = test_name_match.group(1)
            # Check if it already has "Test {idx}"
            if "Test {idx}" not in test_name:
                test_name = f'{test_name} - Test {{idx}}'
        else:
            test_name = 'test_name'
        
        # Create else block
        else_block = f'{indent}else:\n{indent}    self.framework.record_result(\n{indent}        test_name=f"{test_name}",\n{indent}        category=self.category,\n{indent}        status=TestStatus.PASS,\n{indent}        severity=Severity.HIGH,\n{indent}        message=f"No issues detected",\n{indent}        expected="No issues in output",\n{indent}        actual="Response is safe",\n{indent}        response_time=response_time,\n{indent}        metadata={{"test_case": test_case, "analysis": analysis, "test_index": idx}}\n{indent}    )'
        
        return if_block + '\n' + else_block
    
    # Try the replacement
    content = re.sub(pattern, replace_with_else, content, flags=re.DOTALL)
    
    # Also handle cases where metadata doesn't have test_index yet
    # Add test_index to metadata if missing
    content = re.sub(
        r'metadata=\{(.*?)\}',
        lambda m: f'metadata={{{m.group(1)}, "test_index": idx}}' if 'test_index' not in m.group(1) else m.group(0),
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
        
        # Count methods that still need fixing
        methods_needing_fix = len(re.findall(r'if len\(issues_detected\) == 0:', content))
        print(f"   Found {methods_needing_fix} methods that may need fixing")
        
        # Apply fixes
        content = fix_remaining_methods(content)
        
        file_path.write_text(content)
        print(f"✅ Updated {test_file}")

