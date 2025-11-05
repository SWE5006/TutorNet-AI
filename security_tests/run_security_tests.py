#!/usr/bin/env python3
"""
AI Security Testing Runner
Run all security tests for TutorNet AI service

Usage:
    python run_security_tests.py [--url <ai_service_url>] [--output <output_dir>] [--verbose]

Example:
    python run_security_tests.py --url http://localhost:8002/foundation/api/conversation/chat --output ./test_results
"""

import asyncio
import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from security_tests.test_framework import SecurityTestFramework, TestConfig


async def main():
    """Main entry point for security tests"""
    parser = argparse.ArgumentParser(
        description="Run AI Security Tests for TutorNet 2.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default settings
  python run_security_tests.py

  # Run with custom AI service URL
  python run_security_tests.py --url http://localhost:8002/foundation/api/conversation/chat

  # Run with custom output directory
  python run_security_tests.py --output ./my_test_results

  # Run with authorization token
  python run_security_tests.py --token "Bearer your-token-here"

  # Run quietly (less output)
  python run_security_tests.py --quiet
        """
    )
    
    parser.add_argument(
        "--url",
        type=str,
        default="http://localhost:8002/foundation/api/conversation/chat",
        help="AI service URL (default: http://localhost:8002/foundation/api/conversation/chat)"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default="./test_results",
        help="Output directory for test results (default: ./test_results)"
    )
    
    parser.add_argument(
        "--token",
        type=str,
        default=None,
        help="Authorization token (optional)"
    )
    
    parser.add_argument(
        "--workflow",
        type=str,
        default="general",
        help="Workflow type (default: general)"
    )
    
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.7,
        help="LLM temperature (default: 0.7)"
    )
    
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Request timeout in seconds (default: 30)"
    )
    
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Run quietly (less verbose output)"
    )
    
    args = parser.parse_args()
    
    # Create test configuration
    config = TestConfig(
        ai_service_url=args.url,
        output_dir=args.output,
        authorization_token=args.token,
        workflow=args.workflow,
        temperature=args.temperature,
        timeout=args.timeout,
        verbose=not args.quiet
    )
    
    # Run tests
    async with SecurityTestFramework(config) as framework:
        await framework.run_all_tests()
    
    print("\n" + "="*80)
    print("✅ Security Testing Complete!")
    print("="*80)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error running tests: {e}")
        sys.exit(1)

