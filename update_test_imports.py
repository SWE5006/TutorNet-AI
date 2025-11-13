"""
Test Import Update Script

This script updates all test files to use the new refactored module structure.
Maps old private functions to new public functions in their respective modules.
"""

import re
from pathlib import Path

# Define import mappings
IMPORT_MAPPINGS = {
    # Models
    "ConversationRequest": "src.api.models",
    "SessionManagementRequest": "src.api.models",
    
    # LLM Factory
    "_get_llm_instance": ("get_llm_instance", "src.api.llm_factory"),
    "_create_qwen_openai_instance": ("create_qwen_openai_instance", "src.api.llm_factory"),
    "_create_openai_instance": ("create_openai_instance", "src.api.llm_factory"),
    
    # Memory Manager
    "_get_session_memory": ("get_session_memory", "src.api.memory_manager"),
    "_prepare_messages": ("prepare_messages", "src.api.memory_manager"),
    "_save_conversation_context": ("save_conversation_context", "src.api.memory_manager"),
    "memory_by_session": "src.api.conversation",  # Still in conversation.py
    
    # Utils
    "_validate_and_get_tools": ("validate_and_get_tools", "src.api.utils"),
    "_get_error_fallback_message": ("get_error_fallback_message", "src.api.utils"),
    
    # Agents
    "_create_react_agent": ("create_react_agent", "src.api.agents.react_agent"),
    "_create_reflection_graph": ("create_reflection_graph", "src.api.agents.reflection_graph"),
    "_reflect_on_response_with_agent": ("reflect_on_response_with_agent", "src.api.agents.reflection_graph"),
    "_extract_regeneration_instructions": ("extract_regeneration_instructions", "src.api.agents.reflection_graph"),
    "_create_agent_with_reflection_graph": ("create_agent_with_reflection_graph", "src.api.agents.combined_graph"),
    
    # Streaming Handlers
    "_create_agent_response_stream": ("create_agent_response_stream", "src.api.streaming_handlers"),
    "_create_regular_response_stream": ("create_regular_response_stream", "src.api.streaming_handlers"),
    "_handle_tool_conversation": ("handle_tool_conversation", "src.api.streaming_handlers"),
    "_handle_regular_conversation": ("handle_regular_conversation", "src.api.streaming_handlers"),
    "STREAMING_HEADERS": "src.api.streaming_handlers",
    
    # Constants (still in conversation.py - these were removed in refactoring)
    # "DEFAULT_TEMPERATURE": "src.api.conversation",
    # "REQUEST_TIMEOUT": "src.api.conversation",
    # "MAX_RETRIES": "src.api.conversation",
}

def update_test_file(filepath: Path):
    """Update imports in a single test file."""
    print(f"\nProcessing: {filepath.name}")
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    original_content = content
    changes_made = []
    
    # Replace function calls (remove underscore prefix)
    for old_name, mapping in IMPORT_MAPPINGS.items():
        if isinstance(mapping, tuple):
            new_name, new_module = mapping
            # Replace function calls
            if old_name in content:
                content = content.replace(old_name, new_name)
                changes_made.append(f"  - Renamed {old_name} -> {new_name}")
    
    if content != original_content:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"  ✅ Updated {len(changes_made)} references")
        for change in changes_made:
            print(change)
        return True
    else:
        print("  ⏭️  No changes needed")
        return False

def main():
    """Main execution."""
    tests_dir = Path(__file__).parent / "tests"
    
    test_files = [
        "test_conversation.py",
        "test_conversation_additional.py",
        "test_censorship_validation.py",
        "test_settings.py",
    ]
    
    print("=" * 60)
    print("Test Import Update Script")
    print("=" * 60)
    
    updated_count = 0
    for test_file in test_files:
        filepath = tests_dir / test_file
        if filepath.exists():
            if update_test_file(filepath):
                updated_count += 1
        else:
            print(f"\n⚠️  File not found: {test_file}")
    
    print("\n" + "=" * 60)
    print(f"Summary: Updated {updated_count}/{len(test_files)} files")
    print("=" * 60)
    print("\n✅ Script completed!")
    print("\nNext steps:")
    print("1. Run: pytest tests/ -v")
    print("2. Check for any import errors")
    print("3. Verify all 212 tests pass")

if __name__ == "__main__":
    main()
