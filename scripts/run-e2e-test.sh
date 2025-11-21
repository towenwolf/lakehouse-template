#!/bin/bash
# Run the end-to-end lakehouse test
# This script runs the minimal tracer bullet test

set -e

echo "========================================"
echo "Lakehouse End-to-End Test"
echo "========================================"
echo ""

# Check Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed or not in PATH"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo "Using Python $PYTHON_VERSION"
echo ""

# Run the test
echo "Running end-to-end test..."
echo ""

python3 tests/test_end_to_end.py

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo "========================================"
    echo "End-to-End Test: SUCCESS ✓"
    echo "========================================"
    echo ""
    echo "Next steps:"
    echo "1. Review the test code in tests/test_end_to_end.py"
    echo "2. Explore the simple pipeline in pipelines/simple_pipeline.py"
    echo "3. Check out docs/END_TO_END_TEST.md for more details"
    echo "4. Run the pipeline directly: python3 pipelines/simple_pipeline.py"
    exit 0
else
    echo ""
    echo "========================================"
    echo "End-to-End Test: FAILED ✗"
    echo "========================================"
    exit 1
fi
