#!/bin/bash
# PR Merger - Quick Examples
# Common use cases for managing and merging pull requests

echo "PR Merger Tool - Quick Examples"
echo "================================"
echo ""

echo "1. List all open PRs:"
echo "   ./scripts/pr-merger.sh list"
echo ""

echo "2. Check if a specific PR is ready to merge:"
echo "   ./scripts/pr-merger.sh check 88"
echo ""

echo "3. Merge a single PR:"
echo "   ./scripts/pr-merger.sh merge 88"
echo ""

echo "4. Batch merge multiple PRs:"
echo "   ./scripts/pr-merger.sh batch 84 86 87 88"
echo ""

echo "5. Auto-merge all ready PRs (with confirmation):"
echo "   ./scripts/pr-merger.sh auto"
echo ""

echo "6. Dry run - test what would happen:"
echo "   DRY_RUN=true ./scripts/pr-merger.sh auto"
echo ""

echo "7. Use different merge method:"
echo "   MERGE_METHOD=merge ./scripts/pr-merger.sh batch 88 89"
echo "   Options: squash (default), merge, rebase"
echo ""

echo "8. Show help:"
echo "   ./scripts/pr-merger.sh help"
echo ""

echo "Full documentation: PR_MERGER_GUIDE.md"
