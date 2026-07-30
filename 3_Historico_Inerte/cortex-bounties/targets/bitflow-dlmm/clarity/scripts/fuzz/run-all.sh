#!/bin/bash
cd "$(dirname "$0")/../.."

echo "🚀 Starting comprehensive fuzz test..."
echo "This will run 10,000 transactions and may take 10-30 minutes"
echo ""

source ~/.nvm/nvm.sh
nvm use 20

# Kill any existing test processes
pkill -f "vitest.*comprehensive" 2>/dev/null
sleep 2

# Run the test using dedicated fuzz command (routes through fuzz-args.sh)
npm run fuzz:comprehensive 2>&1 | tee fuzz-test-execution.log

echo ""
echo "✅ Test execution completed!"
echo ""
echo "📁 Checking results..."

if [ -d "fuzz-test-results" ]; then
    echo ""
    echo "📊 Latest Summary:"
    echo "=================="
    LATEST_SUMMARY=$(ls -t fuzz-test-results/*.md 2>/dev/null | head -1)
    if [ -n "$LATEST_SUMMARY" ]; then
        cat "$LATEST_SUMMARY"
    else
        echo "No summary file found yet"
    fi
    
    echo ""
    echo "📈 All result files:"
    ls -lh fuzz-test-results/
fi

echo ""
echo "📝 Full execution log: fuzz-test-execution.log"

