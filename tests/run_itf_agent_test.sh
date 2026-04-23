#!/bin/bash

# ITF Test Runner - Simple Wrapper

set -e

INPUT_DIR="/tests/test_output/async"
OUTPUT_DIR="./itf_test_reports"

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║      ITF FORM PROCESSING TEST RUNNER                       ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check if input directory exists
if [ ! -d "$INPUT_DIR" ]; then
    echo "❌ Error: Input directory not found: $INPUT_DIR"
    echo ""
    exit 1
fi

echo "📁 Input directory:  $INPUT_DIR"
echo "📁 Output directory: $OUTPUT_DIR"
echo ""

# Run the test runner
python test_itf_runner.py "$INPUT_DIR" -o "$OUTPUT_DIR"

exit_code=$?

echo ""
if [ $exit_code -eq 0 ]; then
    echo "✅ Test runner completed successfully"
    echo ""
    echo "📊 Results:"
    echo "   - Batch summary:   $OUTPUT_DIR/batch_summary.json"
    echo "   - Individual reports available in: $OUTPUT_DIR/"
    echo ""
    echo "📋 Check the log file for details:"
    echo "   tail -f itf_test_run.log"
else
    echo "❌ Test runner failed with exit code: $exit_code"
fi

echo ""
exit $exit_code
