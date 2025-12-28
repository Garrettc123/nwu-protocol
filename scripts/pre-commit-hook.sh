#!/bin/bash

# Pre-commit hook for auto-repair
# Install with: cp scripts/pre-commit-hook.sh .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit

echo "🤖 Running pre-commit auto-repairs..."

# Fix formatting
npx prettier --write . 2>/dev/null || true

# Fix linting
npx eslint --fix . 2>/dev/null || true

# Python formatting
black . 2>/dev/null || true

# Stage all fixes
git add -A

echo "✅ Pre-commit checks complete"
exit 0
