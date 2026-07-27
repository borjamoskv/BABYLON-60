#!/bin/bash
cd "$(dirname "$0")/../.."

echo "📊 FUZZ TEST RESULTS VIEWER"
echo "============================"
echo ""

# Check if test is running
if pgrep -f "vitest.*comprehensive" > /dev/null; then
    echo "⏳ Test is currently RUNNING..."
    echo ""
    echo "Recent progress from log:"
    tail -20 fuzz-test-execution.log 2>/dev/null | grep -E "(Progress|📈|Starting|Transaction)" | tail -5 || echo "   (checking log file...)"
    echo ""
    echo "To monitor live: tail -f fuzz-test-execution.log"
    echo ""
else
    echo "✅ Test is NOT running (completed or not started)"
    echo ""
fi

# Show results if they exist
if [ -d "fuzz-test-results" ] && [ "$(ls -A fuzz-test-results 2>/dev/null)" ]; then
    echo "📁 RESULTS FOUND:"
    echo "================="
    echo ""
    
    # Latest summary
    LATEST_SUMMARY=$(ls -t fuzz-test-results/*.md 2>/dev/null | head -1)
    if [ -n "$LATEST_SUMMARY" ]; then
        echo "📄 Latest Summary Report:"
        echo "-------------------------"
        cat "$LATEST_SUMMARY"
        echo ""
    fi
    
    # Latest JSON stats
    LATEST_JSON=$(ls -t fuzz-test-results/*.json 2>/dev/null | head -1)
    if [ -n "$LATEST_JSON" ]; then
        echo "📈 Quick Stats:"
        echo "--------------"
        cat "$LATEST_JSON" | python3 -m json.tool 2>/dev/null | grep -A 15 '"stats"' | head -20 || \
        cat "$LATEST_JSON" | grep -A 10 '"stats"' | head -15
        echo ""
    fi
    
    echo "📂 All result files:"
    ls -lh fuzz-test-results/ | tail -10
    echo ""
else
    echo "⚠️  No results found yet."
    echo "   Results will be saved to: fuzz-test-results/"
    echo ""
fi

echo "📝 Log files:"
echo "   - fuzz-test-execution.log (main execution log)"
echo "   - fuzz-test-nohup.log (nohup output)"
echo ""

