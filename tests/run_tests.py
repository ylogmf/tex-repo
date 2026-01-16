#!/usr/bin/env python3
"""
Run all tex-repo tests
Executes both unit tests and sample workflow tests
"""
import sys
import os
import subprocess
from pathlib import Path


def run_test_file(test_file, description):
    """Run a test file and report results"""
    print(f"\n{'='*60}")
    print(f"🧪 {description}")
    print('='*60)
    repo_root = Path(__file__).resolve().parent.parent
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{repo_root}{os.pathsep}{env.get('PYTHONPATH', '')}"
    
    try:
        result = subprocess.run([sys.executable, str(test_file)], 
                              capture_output=True, text=True, cwd=test_file.parent, env=env)
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        if result.returncode == 0:
            print(f"✅ {description} PASSED")
            return True
        else:
            print(f"❌ {description} FAILED (exit code: {result.returncode})")
            return False
            
    except Exception as e:
        print(f"❌ {description} FAILED with exception: {e}")
        return False


def main():
    """Run all tests"""
    print("🚀 Running all tex-repo tests...")
    
    # Get test directory
    test_dir = Path(__file__).parent
    
    # Find all test files
    test_files = [
        (test_dir / 'code' / 'test_enhancements.py', 'Enhancement Unit Tests'),
        (test_dir / 'sample' / 'test_sample_workflow.py', 'Complete Workflow Test'),
    ]
    
    results = []
    
    for test_file, description in test_files:
        if test_file.exists():
            success = run_test_file(test_file, description)
            results.append((description, success))
        else:
            print(f"⚠️  Test file not found: {test_file}")
            results.append((description, False))
    
    # Print summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print('='*60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for description, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status}: {description}")
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("💥 Some tests failed!")
        return 1


if __name__ == '__main__':
    sys.exit(main())
