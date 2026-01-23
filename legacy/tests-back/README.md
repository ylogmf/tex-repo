# tex-repo Test Suite

This directory contains comprehensive tests for the tex-repo project enhancements.

## Test Structure

### `/tests/test_integration.py`
Integration tests that verify the complete tex-repo workflow:
- ✅ **Help Command**: Verifies CLI help functionality
- ✅ **Repository Initialization**: Tests interactive repo setup with metadata
- ✅ **Status Command**: Validates repository status reporting
- ✅ **Domain Creation**: Tests creation of research domains under stages
- ✅ **Paper Creation**: Verifies new paper generation with templates
- ✅ **Configuration**: Tests creation and management of .texrepo-config files
- ✅ **Error Handling**: Validates proper error reporting for invalid operations

### `/tests/code/`
Unit tests for specific code functionality:
- `test_text_init.py`: CLI text-based init, status sanity, and non-destructive guarantees.

### `/tests/sample/`  
Sample workflow tests and fixtures:
- `init_notes.txt`, `expected_section_1.tex`, `expected_init_tree.txt`: fixtures for text-based initialization.
- `test_sample_workflow.py`: creates a complete example repository.

## Running Tests

### Quick Integration Test
Run the main integration test that covers all primary functionality:

```bash
cd /Users/yanlinli/tools/tex-repo
python3 tests/test_integration.py
```

### All Tests
Run the comprehensive test runner:

```bash
cd /Users/yanlinli/tools/tex-repo  
python3 tests/run_tests.py
```

## Test Coverage

The integration tests verify all the enhancements made to tex-repo:

### ✅ Enhanced Error Messages
- Tests proper error reporting for invalid domains
- Validates helpful hints in error messages
- Confirms graceful failure modes

### ✅ Build System Caching  
- Paper creation templates work correctly
- Configuration system properly applied
- Directory structures follow tex-repo conventions

### ✅ Configuration Management
- `.texrepo-config` file creation and loading
- Custom paper settings (section count, document class, etc.)
- Build preferences and metadata options

### ✅ Metadata System
- Interactive repository initialization
- Identity.tex generation with author information
- Proper .paperrepo metadata storage

### ✅ CLI Enhancements
- All commands work as expected
- Help system provides useful information
- Status reporting shows repository health

## Test Results

Latest test run shows **100% pass rate** for all integration tests:

```
🎉 All integration tests passed!
```

The tests validate:
- Repository initialization with metadata
- Domain and paper creation workflows  
- Configuration file management
- Error condition handling
- CLI command functionality

## Test Environment

Tests run in isolated temporary directories and do not affect the main workspace. Each test creates its own clean environment to ensure reproducible results.

## Future Enhancements

- **Unit Tests**: Add focused tests for individual functions and modules
- **Build Tests**: Add LaTeX compilation tests (when LaTeX is available)
- **Performance Tests**: Validate caching system performance
- **Cross-platform Tests**: Ensure compatibility across different operating systems
