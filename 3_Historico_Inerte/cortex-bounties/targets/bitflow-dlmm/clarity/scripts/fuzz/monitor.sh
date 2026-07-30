#!/bin/bash
cd "$(dirname "$0")/../.."

echo "🚀 Starting fuzz test monitor..."
echo "Test is running in background. Monitoring progress..."

# Wait for test to start
sleep 5

# Monitor the log file
while true; do
    if [ -f "fuzz-test-run.log" ]; then
        # Show last 20 lines with progress
        tail -20 fuzz-test-run.log | grep -E "(Progress|📈|✅|FUZZ|Summary|Error|Invariant)" || tail -5 fuzz-test-run.log
    fi
    
    # Check if results directory has files
    if [ -d "fuzz-test-results" ]; then
        RESULT_COUNT=$(ls -1 fuzz-test-results/*.md 2>/dev/null | wc -l | tr -d ' ')
        if [ "$RESULT_COUNT" -gt 0 ]; then
            echo ""
            echo "✅ Results found! Latest summary:"
            echo "=================================="
            LATEST_SUMMARY=$(ls -t fuzz-test-results/*.md | head -1)
            cat "$LATEST_SUMMARY"
            echo ""
            echo "📁 All results in: fuzz-test-results/"
            break
        fi
    fi
    
    # Check if process is still running
    if ! pgrep -f "vitest.*comprehensive" > /dev/null; then
        echo ""
        echo "Test process completed. Final results:"
        if [ -d "fuzz-test-results" ]; then
            LATEST_SUMMARY=$(ls -t fuzz-test-results/*.md 2>/dev/null | head -1)
            if [ -n "$LATEST_SUMMARY" ]; then
                cat "$LATEST_SUMMARY"
            fi
        fi
        tail -50 fuzz-test-run.log
        break
    fi
    
    sleep 30
done

